"""Pin per-chat display scope propagation at two turn-consumer call sites (synthetic, no adapters)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from gateway.config import GatewayConfig, Platform
from gateway.session import SessionSource


def test_reasoning_prefix_honors_chat_level_show_reasoning_false(monkeypatch):
    """run_turn._hmwa_prepend_reasoning must pass chat_id so a chat can hide reasoning."""
    from gateway.run import GatewayRunner
    config = {'display': {'show_reasoning': True, 'chats': {'family': {'show_reasoning': False}}}}
    monkeypatch.setattr('gateway.run._load_gateway_config', lambda: config)
    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig()
    result = {'last_reasoning': 'secret thoughts'}
    family = SessionSource(platform=Platform.WHATSAPP, chat_id='family')
    owner = SessionSource(platform=Platform.WHATSAPP, chat_id='owner')
    assert runner._hmwa_prepend_reasoning(result, 'answer', family, False) == 'answer'
    assert 'secret thoughts' in runner._hmwa_prepend_reasoning(result, 'answer', owner, False)


def test_status_warning_notification_honors_chat_level_suppression(monkeypatch):
    """TurnRunner._status_callback_sync must pass chat_id to render_notification (real policy, mocked sink)."""
    from gateway.run_turn_runner import TurnRunner
    sent = MagicMock(return_value=None)
    monkeypatch.setattr('gateway.run._send_or_update_status_coro', sent)
    monkeypatch.setattr(TurnRunner, '_schedule', lambda self, coro, msg, loop=None: None)
    config = {'display': {'suppress_warning_notifications': False,
                          'chats': {'family': {'suppress_warning_notifications': True}}}}

    def deliver(chat_id):
        sent.reset_mock()
        ctx = SimpleNamespace(
            mute_notification_reply=False, source=SessionSource(platform=Platform.WHATSAPP, chat_id=chat_id),
            user_config=config, _status_adapter=object(), _run_still_current=lambda: True,
            _status_chat_id=chat_id, _status_thread_metadata=None, _cleanup_progress=False)
        TurnRunner(MagicMock(), ctx)._status_callback_sync('warn', 'careful now')
        return sent.called

    assert deliver('family') is False
    assert deliver('owner') is True
