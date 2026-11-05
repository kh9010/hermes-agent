# Version 03 — 0.22.7 candidate: behaviors carried, what changed underneath

Decision owner: Kahran. Candidate only; the cutover is attended (hermes-kmini `bin/nov04-cutover.sh`).

## Fixed identities

- Release: upstream `v0.22.7` = `b200f5bc60` (2026-11-03, stable, not a canary). Newest 0.22 tag; v0.22.6/.7 are rollups with no per-PR notes (full notes ship with v0.23.0).
- Branch `kahran-nov04-hermes-022`, built at `~/Dev/hermes-candidate-0.22.x` (separate clone; the live checkout was never touched).
- Live before: fork `main` `71cdc44862` (0.21.5 + versions 01/02).

## Why v0.22.7 and not an earlier 0.22

Open upstream issues were read on 2026-11-04 for the three surfaces that matter here. None is a showstopper for this install:

| Issue | Surface | Why it does not block |
|---|---|---|
| #147655 keychain unreadable → DirectSDK "Not logged in" | macOS + DirectSDK | Only when the plist is loaded in `user/<uid>`; the runbook bootstraps `gui/501` and asserts it in preflight and after start. |
| #139807 cron + DirectSDK `unexpected 'command'` | cron + DirectSDK | Root-caused upstream to a gateway serving stale modules after an in-place plugin update; the runbook starts a fresh process and its second probe exercises exactly the cron-default path. |
| #146509 cron → WhatsApp `deliver: origin` silently not sent (0.22.2) | cron + WhatsApp | Live crons use explicit `whatsapp:<lid>` / `discord:<id>` targets, not `origin`; `probe-delivery` checks the phone, not the log. |
| #142779 `session.resume` refuses DirectSDK chats (`process://` base_url) | Desktop/TUI resume | The messaging gateway does not resume through that path; no Desktop on kMini. Fix PR #143812 still open. |
| #144642 / #142988 plugin deps invisible / wiped by `hermes update` | Hindsight | Image/PM installs. This is a git install, never `hermes update`; the runbook installs the Hindsight client into the venv explicitly. |

## Behaviors (from versions 01/02)

All four are still absent upstream: on pristine v0.22.7 bytes the 35 requirement tests give `26 failed, 9 passed` (`requirements-pristine.log`); on the candidate `35 passed`.

- **R1** allowlisted WhatsApp group independent of the DM sender list — carried (authz_mixin; conflict resolved onto upstream's new `_group_chat_env()`).
- **R2** `<user>@<device>@lid` reply normalization — carried (auto-merged).
- **R3** `display.chats` per-conversation overrides — carried. Upstream split the turn code into `run_turn_persistence.py` / `run_turn_progress.py` / `run_turn_runner.py`; each chat-scope call site was re-applied by hand where it moved, plus the new local-notice renderer.
- **R4** lean prompt / narrow skill triggers — carried (auto-merged).
- **R5** keep Astra defaults — **retired**: the main model has been Claude Opus 5.5 on the subscription plugin since 2026-10-07. The A→B→A config-home test now pins the live Claude provider instead.
- Inferred family addressing stays withdrawn.

Mutation (`mutation.log`): six of the re-ported hunks turn their test red when reverted. Two do not and are recorded, not hidden: M7 (`diagnostic_turn_muted` chat scope, unpinned since 0.21) and M8 (gateway proxy-mode stream consumer; kMini does not use proxy mode — the live stream path goes through the turn-bound resolver M3 pins).

## Test drift only

- 0.22 on Python 3.14 ships ruamel.yaml, not PyYAML: the A→B→A test writes YAML text.
- `TurnRunner` consults the session authority at construction: the bare runner gets `session_authorities=None`.
- 0.22's ruff config flags B010 in an 02 test: `setattr` → attribute assignment.

## What changed underneath (runbook consequences)

- **Python 3.11 → 3.14.** 0.22.7's `uv.lock` supports only `>=3.14`. The venv uses uv-managed CPython 3.14 (not Homebrew's, so a brew upgrade cannot break it). The kMini launcher pinned `(3, 11)` and would have exited 78 under launchd: hermes-kmini bumps it to `(3, 14)` with a test.
- `dev` moved from an extra to a dependency group (`--group dev`).
- The live venv carried runtime packages the lockfile sync does not install (voice-note STT, edge-tts, Exa, Google API client, boto3, PyYAML). The runbook adds the matching extras; only `importlib-metadata`, `pytz`, `zipp` (3.11-era backports) are allowed to be missing.
- Config schema v46 → v52: on a copy of the live config the migration changes only the stamp (`config-step-diff.txt` also shows the coordinator-requested retirement of the deleted `qwen3.6:27b`).
- `hermes plugins compat` is gone; `hermes plugins doctor <id>` replaces it.
- Hindsight was already a catalog plugin on 0.21.5 (1.2.1 in `~/.hermes/plugins/hindsight`); 0.22's left-core migration only fires when the provider is missing, so it is a no-op here. Profile identity is unchanged (`default` → `hermes-default-*` banks); the candidate venv's client read 10,411 memories from the live daemon (read-only).
- state.db: 0.22 adds four tables (`runtime_epoch`, `session_admissions`, `worker_executions`, `worker_receipts`) and removes none; 0.21.5 opened, read and wrote the migrated copy. Rollback keeps the database.
- WhatsApp bridge: Baileys 7.0.0-rc13 on both sides, same session dir — no re-pair expected.
