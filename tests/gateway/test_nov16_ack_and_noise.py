"""kMini, 2026-11-16: a receipt ack on WhatsApp, and three notices Kahran never acts on.

1. WhatsApp DM gets 👀 before the turn and ✅/❌ after it (off by default; groups never).
2. ``<platform>: unauthorized_owner_notice: false`` keeps the "Dropped a message from unrecognized
   user" ping out of the home channel; the WARNING log line stays.
3. The "shutting down, your task will be interrupted" notice honours ``display.chats`` per-chat
   ``suppress_warning_notifications`` (it did not pass ``chat_id``, so a restart mid-turn in the
   family group would post there).
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from gateway.config import HomeChannel, Platform, PlatformConfig
from gateway.pairing import PairingStore
from gateway.platforms.event import MessageEvent, MessageType, ProcessingOutcome
from gateway.run import GatewayRunner
from gateway.session import SessionSource, build_session_key
from tests.gateway.restart_test_helpers import make_restart_runner, make_restart_source


# ── 1. WhatsApp reactions ───────────────────────────────────────────────────────────────────────

class _Resp:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _wa_adapter(extra):
    from plugins.platforms.whatsapp.adapter import WhatsAppAdapter
    adapter = WhatsAppAdapter(PlatformConfig(enabled=True, extra=extra))
    calls = []

    def _bridge_req(method, path, timeout, **kwargs):
        calls.append((method, path, kwargs.get("json")))
        return _Resp()

    async def _available():
        return None

    adapter._http_session = object()
    adapter._bridge_req = _bridge_req
    adapter._bridge_unavailable = _available
    return adapter, calls


def _wa_event(chat_type="dm", chat_id="96723401760947@lid"):
    key = {"remoteJid": chat_id, "id": "3EB0IN", "participant": "1425@lid", "fromMe": False}
    source = SessionSource(platform=Platform.WHATSAPP, chat_id=chat_id, chat_type=chat_type, user_id="1425@lid")
    return MessageEvent(text="hi", message_type=MessageType.TEXT, source=source,
                        raw_message={"messageId": "3EB0IN", "readReceiptKey": key}, message_id="3EB0IN")


@pytest.mark.asyncio
async def test_whatsapp_dm_gets_eyes_then_done_when_enabled():
    adapter, calls = _wa_adapter({"reactions": True})
    event = _wa_event()
    await adapter.on_processing_start(event)
    await adapter.on_processing_complete(event, ProcessingOutcome.SUCCESS)
    assert [(c[1], c[2]["emoji"]) for c in calls] == [("react", "👀"), ("react", "✅")]
    assert calls[0][2]["key"]["id"] == "3EB0IN"


@pytest.mark.asyncio
async def test_whatsapp_failure_and_cancel_outcomes():
    adapter, calls = _wa_adapter({"reactions": "true"})
    await adapter.on_processing_complete(_wa_event(), ProcessingOutcome.FAILURE)
    await adapter.on_processing_complete(_wa_event(), ProcessingOutcome.CANCELLED)
    assert [c[2]["emoji"] for c in calls] == ["❌", ""]


@pytest.mark.asyncio
async def test_whatsapp_reactions_off_by_default_and_never_in_groups():
    adapter, calls = _wa_adapter({})
    await adapter.on_processing_start(_wa_event())
    group_adapter, group_calls = _wa_adapter({"reactions": True})
    await group_adapter.on_processing_start(_wa_event("group", "14252693038-1407863591@g.us"))
    assert calls == [] and group_calls == []


def test_whatsapp_reactions_key_reaches_extra_from_root_yaml(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "whatsapp:\n  reactions: true\n  unauthorized_owner_notice: false\n  gateway_restart_notification: false\n")
    with patch("gateway.config.get_hermes_home", return_value=tmp_path), \
            patch.dict("os.environ", {"WHATSAPP_ENABLED": "true"}, clear=False):
        from gateway.config import load_gateway_config
        wa = load_gateway_config().platforms[Platform.WHATSAPP]
    assert wa.extra.get("reactions") is True
    assert wa.extra.get("unauthorized_owner_notice") is False
    assert wa.gateway_restart_notification is False


# ── 2. Unknown-sender owner notice off switch ───────────────────────────────────────────────────

def _ignored_dm_runner(tmp_path, monkeypatch, extra):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    runner, adapter = make_restart_runner()
    runner.pairing_store = PairingStore()
    runner.pairing_stores = {}
    cfg = runner.config.platforms[Platform.TELEGRAM]
    cfg.home_channel = HomeChannel(platform=Platform.TELEGRAM, chat_id="home-1", name="Ops")
    cfg.extra.update(extra)
    runner._hm_report_ignored_dm = GatewayRunner._hm_report_ignored_dm.__get__(runner, GatewayRunner)
    return runner, adapter


@pytest.mark.asyncio
async def test_owner_notice_off_keeps_home_channel_quiet_but_logs(tmp_path, monkeypatch, caplog):
    runner, adapter = _ignored_dm_runner(tmp_path, monkeypatch, {"unauthorized_owner_notice": False})
    stranger = SessionSource(platform=Platform.TELEGRAM, chat_id="dm-777", user_id="777", user_name="Eve", chat_type="dm")
    with caplog.at_level(logging.WARNING, logger="gateway.run"):
        await runner._hm_report_ignored_dm(stranger)
    assert adapter.sent_calls == []
    assert any("Unauthorized user (ignored)" in r.getMessage() and "777" in r.getMessage() for r in caplog.records)


@pytest.mark.asyncio
async def test_owner_notice_default_still_on(tmp_path, monkeypatch):
    runner, adapter = _ignored_dm_runner(tmp_path, monkeypatch, {})
    stranger = SessionSource(platform=Platform.TELEGRAM, chat_id="dm-778", user_id="778", chat_type="dm")
    await runner._hm_report_ignored_dm(stranger)
    assert [c[0] for c in adapter.sent_calls] == ["home-1"]


# ── 3. Shutdown notice honours the per-chat (family group) suppression ──────────────────────────

@pytest.mark.asyncio
async def test_shutdown_notice_skips_a_group_that_suppresses_warnings():
    runner, adapter = make_restart_runner()
    group = make_restart_source(chat_id="family-group", chat_type="group")
    key = build_session_key(group)
    runner._running_agents = {key: MagicMock()}
    runner._cache_session_source(key, group)
    user_config = {"display": {"chats": {"family-group": {"suppress_warning_notifications": True}}}}
    with patch("gateway.warning_notifications.effective_user_config", return_value=user_config):
        await runner._notify_active_sessions_of_shutdown()
    assert "family-group" not in [c[0] for c in adapter.sent_calls]


@pytest.mark.asyncio
async def test_shutdown_notice_still_reaches_an_unsuppressed_chat():
    runner, adapter = make_restart_runner()
    dm = make_restart_source(chat_id="kahran-dm")
    key = build_session_key(dm)
    runner._running_agents = {key: MagicMock()}
    runner._cache_session_source(key, dm)
    user_config = {"display": {"chats": {"family-group": {"suppress_warning_notifications": True}}}}
    with patch("gateway.warning_notifications.effective_user_config", return_value=user_config):
        await runner._notify_active_sessions_of_shutdown()
    assert "kahran-dm" in [c[0] for c in adapter.sent_calls]
