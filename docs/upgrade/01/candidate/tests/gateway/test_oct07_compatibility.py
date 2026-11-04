"""Version 01 compatibility contracts: pure/mocked, no transports started."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.display_config import resolve_display_setting, resolve_tool_progress
from gateway.session import SessionSource
from tests.gateway.test_whatsapp_group_gating import _make_adapter, _group_message


@pytest.mark.parametrize('bot,quote', [
    ('123:4@lid', '123@lid'), ('123@4@lid', '123@lid'),
    ('123@lid', '123@4@lid'), ('123:4@s.whatsapp.net', '123@s.whatsapp.net'),
])
def test_reply_device_suffix_matches(bot, quote):
    adapter = _make_adapter(require_mention=True, group_policy='allowlist',
                            group_allow_from=['120363001234567890@g.us'])
    assert adapter._should_process_message(_group_message(botIds=[bot], quotedParticipant=quote))
    assert not adapter._should_process_message(_group_message(botIds=[bot], quotedParticipant='999@lid'))


def test_family_group_never_infers_unsolicited_addressing():
    adapter = _make_adapter(require_mention=True, group_policy='allowlist',
                            group_allow_from=['120363001234567890@g.us'])
    for text in ['Who is in this photo?', 'Hermes can you tell us?', 'Thanks!', 'What year was this?']:
        assert not adapter._should_process_message(_group_message(text))
    assert adapter._should_process_message(_group_message(mentionedIds=['15551230000@lid']))
    assert not adapter._should_process_message(_group_message(chatId='other@g.us', quotedParticipant='15551230000@lid'))


def test_group_authorization_independent_of_dm_allowlist(monkeypatch):
    from gateway.run import GatewayRunner
    monkeypatch.setenv('WHATSAPP_ALLOWED_USERS', '11111111111')
    monkeypatch.setenv('GATEWAY_ALLOWED_USERS', '11111111111')
    adapter = _make_adapter(require_mention=True, dm_policy='allowlist', allow_from=['11111111111'],
                            group_policy='allowlist', group_allow_from=['120363001234567890@g.us'])
    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(platforms={Platform.WHATSAPP: adapter.config})
    runner.adapters = {Platform.WHATSAPP: adapter}
    runner.pairing_store = MagicMock()
    runner.pairing_store.is_approved.return_value = False
    source = SessionSource(platform=Platform.WHATSAPP, chat_type='group',
                           chat_id='120363001234567890@g.us', user_id='22222222222')
    assert runner._is_user_authorized(source)
    source.chat_id = 'other@g.us'
    assert not runner._is_user_authorized(source)
    source.chat_type = 'dm'
    source.chat_id = '22222222222'
    assert not runner._is_user_authorized(source)


@pytest.fixture
def chat_config():
    return {'display': {'tool_progress': 'all', 'show_reasoning': True,
                        'platforms': {'whatsapp': {'tool_progress': 'new', 'thinking_progress': True,
                                                  'interim_assistant_messages': True}},
                        'chats': {'family@g.us': {'tool_progress': 'off', 'thinking_progress': False,
                                                 'interim_assistant_messages': False, 'show_reasoning': False}}}}


def test_chat_precedence_and_explicit_progress(chat_config):
    assert resolve_display_setting(chat_config, 'whatsapp', 'tool_progress', chat_id='family@g.us') == 'off'
    assert resolve_display_setting(chat_config, 'whatsapp', 'show_reasoning', chat_id='family@g.us') is False
    assert resolve_tool_progress(chat_config, 'whatsapp', 'all', chat_id='family@g.us') == ('off', True)
    assert resolve_display_setting(chat_config, 'whatsapp', 'tool_progress', chat_id='dm') == 'new'
    chat_config['display']['chats']['family@g.us']['tool_progress'] = None
    assert resolve_display_setting(chat_config, 'whatsapp', 'tool_progress', chat_id='family@g.us') == 'new'


@pytest.mark.parametrize('chats', [None, [], 'invalid', {'family@g.us': []}, {'family@g.us': 'invalid'}])
def test_malformed_chat_overrides_inherit(chats):
    config = {'display': {'tool_progress': 'all', 'chats': chats}}
    assert resolve_display_setting(config, 'whatsapp', 'tool_progress', chat_id='family@g.us') == 'all'


def test_chat_display_reaches_turn_consumers(monkeypatch, chat_config):
    from gateway.run import GatewayRunner, _resolve_gateway_display_bool
    monkeypatch.setattr('gateway.run._load_gateway_config', lambda: chat_config)
    runner = object.__new__(GatewayRunner)
    runner.adapters = {}
    runner._resolve_turn_toolsets = lambda *args: ([], [])
    source = SessionSource(platform=Platform.WHATSAPP, chat_id='family@g.us', chat_type='group')
    disp = runner._run_agent_display_settings(source)
    assert disp.progress_mode == 'off'
    assert disp.tool_progress_enabled is False
    assert disp.interim_assistant_messages_enabled is False
    assert disp._display_surface_mode('thinking_progress') == 'off'
    assert _resolve_gateway_display_bool(chat_config, 'whatsapp', 'show_reasoning', chat_id=source.chat_id) is False
    source.chat_id = 'dm'
    dm = runner._run_agent_display_settings(source)
    assert dm.tool_progress_enabled is True
    assert dm.interim_assistant_messages_enabled is True
