# Handoff: Hermes upgrade 0.19.1 → 0.21.5, then Claude subscription as the model
Last updated: 2026-10-07. Version 02.

## Current goal
Replace the live fork on kMini (old base + six local commits) with release v2026.9.24 / 0.21.5 carrying the four required behaviors, then move the main model from `gpt-6-astra` / `openai-codex` to Kahran's Claude Max subscription through the `claude-subscription-directsdk` plugin (Hermes ≥ 0.21.4, Claude Code ≥ 2.1.284). The plugin drives the stock `claude` CLI; Hermes keeps tools, approvals and compaction.

## Where things stand
- Version 02 is this branch's commit; PR to fork `main`. History is joined with `git merge -s ours fork/main` so the PR applies cleanly: the old local commits stay in history and their exact bytes are archived under `docs/upgrade/01/old-local/`.
- Deployment: see "Deployment" below once run; until then live stays on 130c0a8f7a with Astra.
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

## Deployment
Pending at this version; the cutover record goes here.
