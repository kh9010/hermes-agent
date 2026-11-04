# Version 02 — reviewed candidate

Built on Version 01 (sealed, `docs/upgrade/01/`) on 2026-10-07 by the MacBook Claude session finishing the upgrade. Same release HEAD; same nine runtime files plus one more test file.

## Independent review of 01 (Opus, read-only, mutation-tested)

Verdict MERGE-SAFE. R1 grant path traced from adapter `build_source` through `_chat_scoped_grant`: stranger DMs, unlisted groups, open/disabled/pairing policies and plugin injection all denied. R2 regex anchored, digits only, mention/reply matching only. R3 `functools.partial` keyword override is safe; false honoured, null inherits. 833 upstream tests from auth/WhatsApp/Discord/display/warning/reasoning/streaming/busy suites: 12 failures, all reproduced on clean release bytes.

Mutations that went red on 01: R1 grant removed (3), allowlist check dropped (1), R2 regex reverted (3), chat lookup removed (10), partial binding removed (2), "Casual conversation" sentence removed (1).

## Fixed in 02

1. **Medium — numeric YAML chat keys.** `display.chats` lookups used `chats.get(str(chat_id))`; an unquoted Discord/Telegram id loads as an int and never matched, so the override was silently ignored. `gateway/display_config.py` gains `chat_display_override()` (string-compares keys); `gateway/run.py::_has_platform_display_override` uses it. Test `test_numeric_yaml_chat_keys_match_string_chat_ids` fails on 01, passes on 02.
2. **Medium — three untested sites.** Pinned: chat-level `show_reasoning: false` through the real `_hmwa_prepend_reasoning` (`run_turn.py`); chat-level warning suppression through the real `TurnRunner._status_callback_sync` → `render_notification` (`run_turn_runner.py`); the exact sentence "This does not waive explicit skill-loading requirements or domain safety prerequisites." Each test was run with the hunk removed (red) and restored (green); see `focused.log` for the green run.

## Noted, not changed (design as Kahran decided it)

- Every participant of the one allowlisted family group is a full principal; the bridge passes `/`-commands through without a mention, so a family member could run `/model` or `/stop`. This is what R1 restores; an owner-only command tier would be a new feature.
- A secondary profile without its own adapter borrows the primary's adapters and therefore its group grant (release design; a secondary with its own adapter is denied, tested).

## Local plugin compatibility (outside this repo)

`hermes plugins compat` on 0.21.5 refused `privacy-logging` (imported the removed `hermes_logging.rotating_file_handlers`). Fixed in `kh9010/hermes-kmini` PR #80 (reads `_queued_file_handlers`, fails closed, 29 tests). `compat.log` here is the clean run with all three kMini plugins enabled. `day-header` and `hanuman-capture` were clean.

## Config migration rehearsal (v33 → v46, on a copy)

No keys added or removed. Two value changes: `display.background_process_notifications` `all` → `concise` (kept), and `connections` toolset inserted into `platform_toolsets.whatsapp` (removed at cutover to keep the WhatsApp toolset identical). Harmless warnings for unused `teams`/`google_chat` platform entries.
