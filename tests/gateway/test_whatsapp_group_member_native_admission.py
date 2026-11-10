"""A member of an allowlisted WhatsApp group must pass native admission.

Regression (2026-11-05 and 2026-11-10, a family group on kMini): ``group_policy: allowlist`` +
``group_allow_from: [<group JID>]`` admits every member at intake, but the durable admission
re-check in ``session_envelope._validate_native`` called ``_is_user_authorized_for_source`` with
``allow_adapter_delegation=False``. That skips the WhatsApp group-JID grant, so the verdict
fell to ``WHATSAPP_ALLOWED_USERS`` (the owner only), and every other member's reply was refused
as ``permission_denied`` / ``user_not_authorized`` after intake had accepted it.
"""

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.event import MessageEvent, MessageType
from gateway.run import GatewayRunner
from gateway.session import SessionSource
from gateway.session_envelope import snapshot_native
from hermes_state_runtime import RuntimeStoreError

GROUP = "120363000000000001@g.us"
OTHER_GROUP = "120363000000000002@g.us"
OWNER = "15550000001"
MEMBER = "999000000000001@lid"


def _runner(tmp_path, monkeypatch):
    from plugins.platforms.whatsapp.adapter import WhatsAppAdapter

    for key in ("GATEWAY_ALLOWED_USERS", "GATEWAY_ALLOW_ALL_USERS", "WHATSAPP_ALLOW_ALL_USERS",
                "WHATSAPP_GROUP_ALLOWED_USERS", "WHATSAPP_GROUP_ALLOW_FROM"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("WHATSAPP_ALLOWED_USERS", OWNER)
    runner = GatewayRunner(GatewayConfig(sessions_dir=tmp_path / "sessions"))
    adapter = WhatsAppAdapter(PlatformConfig(enabled=True, extra={
        "group_policy": "allowlist", "group_allow_from": [GROUP], "require_mention": True}))
    runner.adapters = {Platform.WHATSAPP: adapter}
    return runner


def _event(chat_id, user_id, chat_type="group"):
    source = SessionSource(platform=Platform.WHATSAPP, chat_id=chat_id, chat_type=chat_type,
                           user_id=user_id, user_name="Member")
    return MessageEvent(text="The halibut", message_type=MessageType.TEXT, message_id="m1",
                        source=source)


def test_member_of_allowlisted_group_is_admitted(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    snapshot = snapshot_native(runner, _event(GROUP, MEMBER))
    assert snapshot["native_text_v1"]["source"]["user_id"] == MEMBER


def test_member_in_a_group_that_is_not_allowlisted_is_still_refused(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    with pytest.raises(RuntimeStoreError, match="permission_denied"):
        snapshot_native(runner, _event(OTHER_GROUP, MEMBER))


def test_member_dm_is_still_refused(tmp_path, monkeypatch):
    runner = _runner(tmp_path, monkeypatch)
    with pytest.raises(RuntimeStoreError, match="permission_denied"):
        snapshot_native(runner, _event(MEMBER, MEMBER, chat_type="dm"))
