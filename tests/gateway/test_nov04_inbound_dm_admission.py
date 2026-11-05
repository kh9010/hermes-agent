"""kMini inbound contract: an allowlisted WhatsApp DM reaches an agent turn on 0.22.

The 2026-11-04 cutover verified only OUTBOUND (cron probes + delivery). This pins the inbound
half with the kMini config shape: ``whatsapp:`` sets no ``dm_policy`` (so the adapter default,
``pairing``, applies), ``WHATSAPP_ALLOWED_USERS`` holds a phone number, the sender arrives as a
``<lid>@lid`` resolved through the bridge's lid-mapping files, ``unauthorized_dm_behavior: ignore``
and a group allowlist (R1). The event goes through the REAL adapter intake (bridge payload ->
``_build_message_event`` -> text batch -> ``handle_message``) and the REAL runner handler
(authorization, routing) up to the agent-turn entry point; only the turn body is replaced.
"""
import asyncio
import json

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from hermes_constants import get_hermes_home

PHONE = "15550001234"
LID = "88123456789012"
STRANGER_LID = "99000000000001"
GROUP = "120363001234567890@g.us"


def _bridge_dm(sender_lid: str, body: str) -> dict:
    """The shape bridge.js queues on /messages for a 1:1 text."""
    jid = f"{sender_lid}@lid"
    return {"messageId": f"3EB0{sender_lid[-6:]}", "chatId": jid, "senderId": jid, "senderName": "probe",
            "chatName": "probe", "isGroup": False, "body": body, "hasMedia": False, "mediaType": "",
            "mime": "", "fileName": "", "mediaUrls": [], "mentionedIds": [], "quotedMessageId": "",
            "quotedParticipant": "", "quotedRemoteJid": "", "quotedText": "", "hasQuotedMessage": False,
            "botIds": [], "timestamp": 0}


@pytest.fixture
def kmini_runner(monkeypatch):
    from gateway.run import GatewayRunner
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_ALLOWED_USERS", PHONE)
    monkeypatch.setenv("WHATSAPP_GROUP_ALLOW_FROM", GROUP)
    for name in ("GATEWAY_ALLOWED_USERS", "GATEWAY_ALLOW_ALL_USERS", "WHATSAPP_ALLOW_ALL_USERS",
                 "WHATSAPP_DM_POLICY"):
        monkeypatch.delenv(name, raising=False)
    session = get_hermes_home() / "whatsapp" / "session"
    session.mkdir(parents=True, exist_ok=True)
    (session / f"lid-mapping-{PHONE}.json").write_text(json.dumps(LID), encoding="utf-8")
    (session / f"lid-mapping-{LID}_reverse.json").write_text(json.dumps(PHONE), encoding="utf-8")
    pconfig = PlatformConfig(enabled=True, extra={
        "unauthorized_dm_behavior": "ignore", "group_policy": "allowlist", "group_allow_from": GROUP,
        "require_mention": True, "text_batch_delay_seconds": 0})
    runner = GatewayRunner(GatewayConfig(platforms={Platform.WHATSAPP: pconfig}))
    from plugins.platforms.whatsapp.adapter import WhatsAppAdapter
    adapter = WhatsAppAdapter(pconfig)
    adapter.gateway_runner = runner  # what runner._create_adapter does once the registry is loaded
    runner._wire_adapter_handlers(adapter)
    runner.adapters[Platform.WHATSAPP] = adapter
    turns = []

    async def _turn(event, source, _quick_key, run_generation):  # the agent turn entry point
        turns.append((event, source))
        return None

    runner._handle_message_with_agent = _turn
    return runner, adapter, turns


async def _deliver(adapter, payload, turns, wait_s=5.0):
    event = await adapter._build_message_event(payload)
    assert event is not None, "adapter intake dropped the bridge payload"
    adapter._enqueue_text_event(event)
    deadline = asyncio.get_running_loop().time() + wait_s
    while not turns and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_allowlisted_whatsapp_dm_reaches_an_agent_turn(kmini_runner):
    runner, adapter, turns = kmini_runner
    assert adapter._dm_policy == "pairing"  # kMini sets none: the 0.22 default is what runs live
    await _deliver(adapter, _bridge_dm(LID, "hello from the inbound contract"), turns)
    assert len(turns) == 1, "an allowlisted DM never reached an agent turn"
    event, source = turns[0]
    assert event.text == "hello from the inbound contract"
    assert source.platform == Platform.WHATSAPP and source.chat_type == "dm"
    assert source.user_id == f"{LID}@lid"


@pytest.mark.asyncio
async def test_stranger_dm_is_ignored_not_turned(kmini_runner):
    runner, adapter, turns = kmini_runner
    await _deliver(adapter, _bridge_dm(STRANGER_LID, "hi"), turns, wait_s=1.0)
    assert turns == []
