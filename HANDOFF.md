# Handoff: Hermes 0.21.5 → 0.22.7 (version 03), after the 0.19.1 → 0.21.5 upgrade and the Claude-subscription switch
Last updated: 2026-11-04. Version 03.

## Current goal
Replace the live fork on kMini (0.21.5 + versions 01/02, fork `main` 71cdc44862) with upstream v0.22.7 carrying the same four local behaviors, in an attended cutover. Kahran merges this branch's PR after the cutover.

## Where things stand
- Version 03 is branch `kahran-nov04-hermes-022` (PR to fork `main`; history joined with `git merge -s ours fork/main` as in October, so the PR applies cleanly). Built and tested in a separate clone, `~/Dev/hermes-candidate-0.22.x`; the live checkout was not touched.
- **Not deployed.** Runbook: hermes-kmini `bin/nov04-cutover.sh` (its PR, same branch name), rehearsed end to end against a sandbox HOME by `bin/nov04-cutover-rehearsal.sh`. Live launch path and conventions stay owned by `~/Dev/hermes-kmini` (`DEPLOY.md`, `config/README.md`, `plugins/privacy-logging/INSTALL.md`). Point there; do not restate.
- What 03 is and why: `docs/upgrade/03/REQUIREMENTS.md` (release choice against open upstream issues, behaviors carried, what changed underneath).

## Versions
- **01 Quiet family gateway** (2026-10-07) — four behavior ports on release 0.21.5; inferred family addressing withdrawn. Evidence `docs/upgrade/01/`.
- **02 Reviewed candidate** (2026-10-07) — Opus review fixes; deployed that evening. Evidence `docs/upgrade/02/`.
- **03 0.22.7 candidate** (2026-11-04) — R1–R4 carried onto v0.22.7 (R3's chat-scope threading re-applied by hand where upstream split the turn code); R5 (Astra) retired with the Claude switch. Evidence `docs/upgrade/03/`.

## Rules that came out of this work
- Kahran, 2026-10-07: work by behavior, not blind cherry-pick; isolated test homes, no live credentials or channels in tests. 03 measured first: the requirement tests on pristine v0.22.7 are 26 red of 35, so every behavior is still needed.
- Tests are watched red before green; 03's mutation log names the two hunks no test pins (M7, M8) rather than claiming them.
- Python follows the release: 0.22's lockfile is 3.14-only. Use uv-managed CPython, never Homebrew's, so a brew upgrade cannot break the gateway venv.
- The venv is rebuilt from the lockfile plus the extras this install uses (`messaging voice edge-tts exa google bedrock`); compare against the old venv before starting, and stop on anything missing beyond the recorded backports.
- The config step refuses any change it was not rehearsed to make (`hermes-kmini/bin/hermes_022_config_step.py`).
- Earlier: config migration v33→v46 inserted `connections` into the WhatsApp toolset and was undone; privacy-logging installs before its `.pth`.

## Verification
From the candidate root (`venv` = 0.22.7 lockfile on CPython 3.14 + the three kMini plugins + Hindsight client):

```sh
env -i PATH=/usr/bin:/bin HOME=$(mktemp -d) HERMES_HOME=/tmp/none venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/gateway/test_oct07_compatibility.py tests/gateway/test_oct07_upgrade_contracts.py \
  tests/agent/test_oct07_prompt_contracts.py tests/gateway/test_oct07_chat_scope_propagation.py \
  tests/gateway/test_display_config.py tests/gateway/test_config_driven_access_policy.py \
  tests/gateway/test_whatsapp_group_gating.py tests/gateway/test_nov04_inbound_dm_admission.py
# 115 passed

env -i PATH=/opt/homebrew/bin:/usr/bin:/bin HOME="$(mktemp -d)" /opt/homebrew/bin/node verify.mjs
```

Expected (`VERIFY.txt` holds the last real run): one PASS line per rail/integrity/archive/requirements/01/02/03 check, then `STATUS deployment: …`. Exit 0 means the evidence contract is intact; `STATUS` says whether 03 is deployed.

## Known limits
- Upstream CI was not run whole (its jobs assume 96 cores). Run here: `tests/gateway`, `tests/cron`, `tests/plugins` under an isolated home; every failure was re-run on pristine v0.22.7 bytes (`docs/upgrade/03/broad-*.log`, `broad-differential.txt`).
- `display.chats` is honored by the turn-bound resolver and the call sites listed in 01's REQUIREMENTS; new 0.22 surfaces (webapp, group rooms) do not consult it. kMini uses none of them.
- Live `teams` / `google_chat` platform-toolset entries are harmless leftovers; `feishu` shows a stale "connected" in `gateway_state.json` with no config behind it.

## Deployment
- **2026-10-07** (0.21.5, attended): `hermes-kmini/bin/oct07-cutover.sh`; model moved to Claude Opus 5.5 via `claude-subscription-directsdk-experimental` 0.3.2; crons on `claude-haiku-5-5`; fallbacks Codex `gpt-6-sol` → DeepSeek. Rollback artifacts retired after Kahran called it good.
- **03**: pending, attended. Run `bin/nov04-cutover.sh preflight`, then `cutover`, then `probe-delivery`, then `probe-inbound` (the cutover is done only when it reports inbound + reply on both platforms); `plugin-update` (DirectSDK 0.3.2 → 0.3.4) is a separate, optional step. Record the result here and set version 03's status in `versions.json`.
- **2026-11-04 attempt** (rolled back): 0.22.7 ran 23:07:20-23:11:45Z; cron probes and outbound delivery passed. It was rolled back as "dropping inbound", but no inbound reached it: raw.db (Kahran's WhatsApp account) and a sweep of every guild channel/thread show his first messages at 23:12:23Z (WhatsApp) and 23:12:26Z (Discord), after 0.21.5 was back (23:11:56Z), and 0.21.5 answered both. The same 0.22.7 build with this config admitted a synthetic DM from his real sender id end-to-end in an isolated home (fake bridge, fake LLM). Not a code defect; the runbook simply never checked inbound. `tests/gateway/test_nov04_inbound_dm_admission.py` now pins the inbound half (kMini config shape, real adapter intake + runner handler to the turn entry; red under four mutations: DM intake reject, runner deny, batch flush no-dispatch, runner admit-all), and the runbook's `probe-inbound` gates the next cutover on real inbound.
