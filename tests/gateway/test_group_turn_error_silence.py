"""A group chat that suppresses warnings must never see a turn-error notice.

Regression: ``display.chats.<group>.suppress_warning_notifications: true`` was set for a
family WhatsApp group, yet a ``RuntimeStoreError`` posted "Sorry, I encountered an error
(RuntimeStoreError). permission_denied ..." into it, because the adapter's policy check
dropped ``chat_id`` and only saw the platform default.
"""

import asyncio

import pytest

from gateway import warning_notifications
from gateway.config import HomeChannel, Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, SendResult
from gateway.platforms.event import MessageEvent, MessageType
from gateway.session import SessionSource

GROUP = "111-222@g.us"
DM = "333@lid"
HOME = "444@lid"


def _config(**group_overrides):
    chats = {GROUP: {"suppress_warning_notifications": True, **group_overrides}}
    # Same shape as a real config.yaml: display.chats.<chat_id>.<setting>
    return {"display": {"chats": chats}}


class _Adapter(BasePlatformAdapter):
    def __init__(self, home: "str | None" = HOME):
        pc = PlatformConfig(enabled=True, token="t")
        if home:
            pc.home_channel = HomeChannel(platform=Platform.WHATSAPP, chat_id=home, name="Home")
        super().__init__(pc, Platform.WHATSAPP)
        self.sent = []

    async def connect(self, is_reconnect: bool = False):
        return True

    async def disconnect(self):
        pass

    async def send(self, chat_id, content, reply_to=None, metadata=None, **kwargs) -> SendResult:
        self.sent.append((chat_id, content))
        return SendResult(success=True, message_id="m1")

    async def get_chat_info(self, chat_id):
        return {"id": chat_id, "type": "group"}


def _event(chat_id, chat_type):
    src = SessionSource(platform=Platform.WHATSAPP, chat_id=chat_id, chat_type=chat_type,
                        user_id="u1", chat_name="Family")
    return MessageEvent(text="the halibut", source=src, message_type=MessageType.TEXT)


@pytest.fixture
def policy(monkeypatch):
    holder = {"cfg": _config()}
    monkeypatch.setattr(warning_notifications, "effective_user_config", lambda: holder["cfg"])
    return holder


def _fail(adapter, event):
    err = RuntimeError("permission_denied")
    asyncio.run(adapter._notify_turn_error(event, err))


def test_policy_check_now_sees_the_chat_override(policy):
    adapter = _Adapter()
    assert adapter.warning_notifications_enabled(Platform.WHATSAPP, chat_id=GROUP) is False
    assert adapter.warning_notifications_enabled(Platform.WHATSAPP, chat_id=DM) is True


def test_suppressed_group_gets_nothing_and_home_gets_the_detail(policy):
    adapter = _Adapter()
    _fail(adapter, _event(GROUP, "group"))
    assert [c for c, _ in adapter.sent] == [HOME]
    assert "permission_denied" in adapter.sent[0][1]
    assert "Family" in adapter.sent[0][1]


def test_suppressed_group_with_no_home_channel_is_simply_silent(policy):
    adapter = _Adapter(home=None)
    _fail(adapter, _event(GROUP, "group"))
    assert adapter.sent == []


def test_group_that_did_not_opt_out_keeps_the_notice(policy):
    policy["cfg"] = {}
    adapter = _Adapter()
    _fail(adapter, _event(GROUP, "group"))
    assert [c for c, _ in adapter.sent] == [GROUP]


def test_dm_behaviour_is_unchanged(policy):
    adapter = _Adapter()
    _fail(adapter, _event(DM, "dm"))
    assert [c for c, _ in adapter.sent] == [DM]
    assert "permission_denied" in adapter.sent[0][1]


def test_bare_group_id_is_not_presented_as_a_name(policy):
    adapter = _Adapter()
    event = _event(GROUP, "group")
    event.source.chat_name = "111-222"
    _fail(adapter, event)
    assert [c for c, _ in adapter.sent] == [HOME]
    text = adapter.sent[0][1]
    assert "a group chat" in text and "111-222" not in text.split("Technical detail")[0]
