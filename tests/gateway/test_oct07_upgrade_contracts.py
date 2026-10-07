"""Local compatibility contracts; synthetic identities, no live adapters started."""
from unittest.mock import MagicMock

import pytest

from gateway.config import GatewayConfig, Platform
from gateway.display_config import resolve_display_setting, resolve_tool_progress
from gateway.session import SessionSource
from tests.gateway.test_whatsapp_group_gating import _make_adapter, _group_message


@pytest.mark.parametrize('bot_id', ['123:7@lid', '123@7@lid', '123@lid'])
def test_reply_matches_device_identity_but_not_other_account(bot_id):
    adapter = _make_adapter(require_mention=True, group_policy='allowlist',
                            group_allow_from=['120363001234567890@g.us'])
    assert adapter._should_process_message(_group_message(botIds=[bot_id], quotedParticipant='123@lid'))
    assert not adapter._should_process_message(_group_message(botIds=[bot_id], quotedParticipant='124@lid'))
    assert not adapter._should_process_message(_group_message('Hermes, lovely photo', botIds=[bot_id]))


def test_allowlisted_group_independent_of_dm_sender_allowlist(monkeypatch):
    from gateway.run import GatewayRunner
    monkeypatch.setenv('WHATSAPP_ALLOWED_USERS', '999')
    monkeypatch.delenv('GATEWAY_ALLOWED_USERS', raising=False)
    adapter = _make_adapter(require_mention=True, group_policy='allowlist',
                            group_allow_from=['120363001234567890@g.us'],
                            dm_policy='allowlist', allow_from=['999'])
    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(platforms={Platform.WHATSAPP: adapter.config})
    runner.adapters = {Platform.WHATSAPP: adapter}
    runner.pairing_store = MagicMock()
    runner.pairing_store.is_approved.return_value = False
    source = SessionSource(platform=Platform.WHATSAPP, chat_id='120363001234567890@g.us',
                           chat_type='group', user_id='888')
    assert runner._is_user_authorized(source)
    assert not runner._is_user_authorized(source, allow_adapter_delegation=False)
    for policy in ('open', 'disabled', 'pairing'):
        adapter._group_policy = policy
        assert not runner._is_user_authorized(source)
    adapter._group_policy = 'allowlist'
    adapter._group_allow_from = set()
    assert not runner._is_user_authorized(source)
    adapter._group_allow_from = {'120363001234567890@g.us'}
    source.chat_id = 'unlisted@g.us'
    assert not runner._is_user_authorized(source)
    source.chat_type = 'dm'
    source.chat_id = '888'
    assert not runner._is_user_authorized(source)


@pytest.mark.parametrize('setting,value', [('tool_progress', 'off'), ('thinking_progress', False),
    ('interim_assistant_messages', False), ('show_reasoning', False), ('streaming', False)])
def test_chat_override_precedes_platform_without_affecting_dm(setting, value):
    config = {'display': {'platforms': {'whatsapp': {setting: True}},
                          'chats': {'family@g.us': {setting: value}}}}
    expected = 'off' if setting == 'tool_progress' else value
    assert resolve_display_setting(config, 'whatsapp', setting, chat_id='family@g.us') == expected
    assert resolve_display_setting(config, 'whatsapp', setting, chat_id='owner@lid') != expected


def test_numeric_yaml_chat_keys_match_string_chat_ids():
    """Unquoted numeric keys load from YAML as ints; Discord/Telegram chat ids arrive as strings."""
    from gateway.run import _has_platform_display_override
    config = {'display': {'tool_progress': 'all', 'chats': {123456789: {'tool_progress': False}}}}
    assert resolve_tool_progress(config, 'discord', 'all', chat_id='123456789') == ('off', True)
    assert resolve_display_setting(config, 'discord', 'tool_progress', chat_id='123456789') == 'off'
    assert _has_platform_display_override(config, 'discord', 'tool_progress', chat_id='123456789') is True
    assert _has_platform_display_override(config, 'discord', 'tool_progress', chat_id='987') is False


def test_chat_tool_progress_false_is_explicit_and_null_inherits():
    config = {'display': {'tool_progress': 'all', 'chats': {'family': {'tool_progress': False}}}}
    assert resolve_tool_progress(config, 'whatsapp', 'all', chat_id='family') == ('off', True)
    config['display']['chats']['family']['tool_progress'] = None
    assert resolve_tool_progress(config, 'whatsapp', chat_id='family') == ('all', True)


def test_actual_turn_display_consumers_use_chat_scope(monkeypatch):
    from gateway.run import GatewayRunner
    config = {'display': {'tool_progress': 'all', 'thinking_progress': True,
              'interim_assistant_messages': True, 'chats': {'family': {
              'tool_progress': 'off', 'thinking_progress': False, 'interim_assistant_messages': False}}}}
    monkeypatch.setattr('gateway.run._load_gateway_config', lambda: config)
    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig()
    runner.adapters = {}
    monkeypatch.setattr(runner, '_resolve_turn_toolsets', lambda *a: ([], []))
    family = runner._run_agent_display_settings(SessionSource(platform=Platform.WHATSAPP, chat_id='family'))
    dm = runner._run_agent_display_settings(SessionSource(platform=Platform.WHATSAPP, chat_id='owner'))
    assert family.progress_mode == 'off'
    assert family.interim_assistant_messages_enabled is False
    assert family._thinking_enabled is False
    assert dm.progress_mode == 'all'
    assert dm.interim_assistant_messages_enabled is True


@pytest.mark.parametrize('quoted', ['', '124@7@lid', '123@s.whatsapp.net', '123@x@lid'])
def test_reply_normalization_does_not_merge_accounts_or_namespaces(quoted):
    adapter = _make_adapter(require_mention=True, group_policy='open')
    assert not adapter._message_is_reply_to_bot({'botIds': ['123@7@lid'], 'quotedParticipant': quoted})


def test_real_config_homes_a_b_a_preserve_astra_and_chat_settings(tmp_path, monkeypatch):
    import yaml
    from gateway.run import _load_gateway_config
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    homes = [tmp_path / 'a', tmp_path / 'b']
    for home, value in zip(homes, ('off', 'all')):
        home.mkdir()
        (home / 'config.yaml').write_text(yaml.safe_dump({
            'model': {'default': 'gpt-6-astra', 'provider': 'openai-codex'},
            'display': {'chats': {'family': {'tool_progress': value}}}}))
    for home, expected in ((homes[0], 'off'), (homes[1], 'all'), (homes[0], 'off')):
        monkeypatch.setenv('HERMES_HOME', str(home))
        token = set_hermes_home_override(home)
        try:
            cfg = _load_gateway_config()
        finally:
            reset_hermes_home_override(token)
        assert cfg['model'] == {'default': 'gpt-6-astra', 'provider': 'openai-codex'}
        assert resolve_tool_progress(cfg, 'whatsapp', chat_id='family') == (expected, True)


def test_auth_uses_receiving_profile_not_default_group_grant(monkeypatch):
    from gateway.run import GatewayRunner
    import weakref
    monkeypatch.setenv('WHATSAPP_ALLOWED_USERS', '999')
    primary = _make_adapter(group_policy='allowlist', group_allow_from=['family@g.us'])
    secondary = _make_adapter(group_policy='allowlist', group_allow_from=['other@g.us'])
    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig()
    runner.adapters = {Platform.WHATSAPP: primary}
    runner._profile_adapters = {'secondary': {Platform.WHATSAPP: secondary}}
    runner.pairing_store = MagicMock()
    runner.pairing_store.is_approved.return_value = False
    source = SessionSource(platform=Platform.WHATSAPP, chat_id='family@g.us', chat_type='group', user_id='888')
    for adapter, expected in ((primary, True), (secondary, False), (primary, True)):
        setattr(source, '_transport_adapter_ref', weakref.ref(adapter))
        assert runner._is_user_authorized(source) is expected
