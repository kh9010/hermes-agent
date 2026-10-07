# Handoff: Hermes upgrade 0.19.1 → 0.21.5, then Claude subscription as the model
Last updated: 2026-10-07. Version 02.

## Current goal
Replace the live fork on kMini (old base + six local commits) with release v2026.9.24 / 0.21.5 carrying the four required behaviors, then move the main model from `gpt-6-astra` / `openai-codex` to Kahran's Claude Max subscription through the `claude-subscription-directsdk` plugin (Hermes ≥ 0.21.4, Claude Code ≥ 2.1.284). The plugin drives the stock `claude` CLI; Hermes keeps tools, approvals and compaction.

## Where things stand
- Version 02 is this branch's commit; PR to fork `main`. History is joined with `git merge -s ours fork/main` so the PR applies cleanly: the old local commits stay in history and their exact bytes are archived under `docs/upgrade/01/old-local/`.
- Deployed 2026-10-07 ~17:00 EDT: live `~/.hermes/hermes-agent` is fork `main` 11d8be67da, main model is Claude Opus 5.5 through the subscription plugin, memory daemon healthy. Record under "Deployment".
- Live launch path and conventions are owned by `~/Dev/hermes-kmini` (`DEPLOY.md`, `config/README.md`, `plugins/privacy-logging/INSTALL.md`). Point there; do not restate.

## Versions
- **01 Quiet family gateway** — Hermes-built candidate on the release: R1 group auth independent of the DM allowlist, R2 strict legacy LID reply matching, R3 per-conversation display overrides, R4 lean prompt with narrow skill triggers, R5 Astra preserved; inferred family addressing deliberately withdrawn. Evidence sealed in `docs/upgrade/01/` (`REQUIREMENTS.md`, `REVIEW.md`, `WITHDRAWN.md`, logs, old-local archive).
- **02 Reviewed candidate** — independent Opus review of 01 (MERGE-SAFE, mutation-tested) plus its fixes: `display.chats` numeric YAML keys now match string chat ids (`chat_display_override()`); three previously unpinned behaviors have tests. `docs/upgrade/02/REVIEW.md` has the findings, including two accepted-by-design notes (group members can run slash commands; secondary profiles borrow adapters).

## Rules that came out of this work
- Kahran, 2026-10-07: work by behavior, not blind cherry-pick; keep Astra as the recorded gate for 01; keep inferred family addressing out; isolated test homes, no live credentials or channels in tests.
- Kahran, 2026-10-07 14:19 (Discord): do the upgrade now; snapshot the requirements and re-implement them properly on the new version. 14:16: "Yes go ahead" on the Claude-subscription route.
- privacy-logging must be 0.21-compatible before cutover (`hermes plugins compat` clean) — fixed in hermes-kmini PR #80. Install the package before its `.pth` or every interpreter start prints `ModuleNotFoundError`.
- Config migration v33→v46 inserts the `connections` toolset into `platform_toolsets.whatsapp` and flips `display.background_process_notifications` to `concise`; the WhatsApp toolset is kept identical (remove `connections`), the notification change is kept.
- Tests are watched red before green (every 02 test was run with its hunk removed).

## Verification
From the candidate root (`.venv` = release deps + the three kMini plugins):

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/gateway/test_oct07_compatibility.py tests/gateway/test_oct07_upgrade_contracts.py \
  tests/agent/test_oct07_prompt_contracts.py tests/gateway/test_oct07_chat_scope_propagation.py \
  tests/gateway/test_display_config.py tests/gateway/test_config_driven_access_policy.py \
  tests/gateway/test_whatsapp_group_gating.py
# 111 passed  (run under env -i with a throwaway HOME/HERMES_HOME; see docs/upgrade/02/run_02.py)

env -i PATH=/opt/homebrew/bin:/usr/bin:/bin HOME="$PWD/.verify-empty-home" \
  HERMES_HOME="$PWD/.verify-empty-home/.hermes" /opt/homebrew/bin/node verify.mjs
```

Expected (`VERIFY.txt` holds the last real run):

```text
PASS rail: versions 01-02 on release f97608f178; latest "Reviewed candidate" (…)
PASS integrity: 01 and 02 evidence sealed read-only; 9 runtime + 4 test files match 02
PASS archive: 6 old local commits; 16 changed paths including tests
PASS requirements: explicit family group + reply gate recorded; inferred addressing absent
PASS differential (01): 122-file run; all 9 failures reproduced with release bytes; 19 bridge tests
PASS focused evidence (02): 111 Python tests; kMini plugins compat clean; Ruff clean; git diff --check
STATUS deployment: …
```

Checker exit 0 means the candidate/evidence contract is intact; `STATUS` says whether it is deployed.

## Known limits
- Nine upstream tests fail only under the hard sandbox (six assume no ancestor Git checkout, three bind sockets); all nine reproduce on clean release bytes. Full upstream CI was not run on the fork (no runners for its 96-core jobs).
- Live `teams` / `google_chat` platform entries produce "unknown toolset" warnings at config load; harmless, those platforms are unused.

## Deployment (2026-10-07, attended, Kahran present)

Run by `~/Dev/hermes-kmini/bin/oct07-cutover.sh` (hermes-kmini PR #81 holds the final script). What is live:

- Live checkout fast-forwarded to fork `main` 11d8be67da; venv rebuilt from the release lockfile (`uv sync --frozen --extra dev --extra messaging`, CPython 3.11.15) with the three kMini plugins; old venv kept at `venv.old-20261007-pre-upgrade`. Bridge `npm ci` (body-parser 1.20.8).
- Config migrated v33 → v46 (backup `config-baks-archive/config.yaml.bak-20261007-pre-oct07-upgrade`); `connections` dropped from the WhatsApp toolset so it stays `[cronjob, hanuman_capture, hermes-whatsapp]`; `background_process_notifications` now `concise` (upstream default, kept).
- `claude-subscription-directsdk-experimental` 0.3.2 installed from the catalog and **enabled** (the installer leaves it disabled). `model: {provider: claude-subscription-directsdk-experimental, default: opus}`; `providers.<it>.stale_timeout_seconds: 900`. Claude Code on kMini updated 2.1.258 → 2.1.293.
- Fallbacks (Kahran, 17:xx): `openai-codex / gpt-6-sol` then `deepseek / deepseek-v4-flash`; the local qwen fallback is gone. Cron jobs stay on `openai-codex / gpt-5.6-luna`; auxiliary stays DeepSeek.
- Memory: on 0.21 Hindsight is a catalog plugin whose daemon runs as `uvx hindsight-api@0.10.2`; the gateway plist PATH now includes `~/.hermes/bin` (hermes-kmini PR #81), uvx cache pre-warmed. Daemon healthy on :9177, real recall seen on the probe turn.

Proof: three scheduler-side probe jobs (local delivery, no chat message) answered `PROBE OK`; `session_model_usage` records them as `opus` on `claude-subscription-directsdk-experimental`, one API call each, cache writes 28k → 12.7k tokens. SSH sessions on kMini cannot see the keychain login, so `claude auth status` over SSH reads logged-out; probe through the gateway, never the CLI.

Rollback (if a real conversation misbehaves): `bin/oct07-cutover.sh rollback` restores the old venv, commit 130c0a8f7a, the pre-upgrade config and plist, and parks the plugin. Do not restore databases. Retire `venv.old-*`, the config/plist backups and `~/Dev/hermes-upgrade-evidence-oct07/` (530 MB bundle) once a week of real use is clean.

Known after cutover: `teams`/`google_chat` config warnings (unused platforms); the first Hindsight start after a cache wipe downloads ~480 MB.
