# Version 01 — behavior requirements and disposition

Decision owner: Kahran, 2026-10-07. Candidate only; no deployment authority.

## Fixed identities and scope

- Worktree: `/Users/kahransingh/Dev/hermes-agent-oct07-upgrade`.
- Branch: `kahran-oct07-hermes-upgrade`.
- Old live commit: `130c0a8f7aa40fc407eea99656d7c3bce8ba4222`.
- Old upstream base / merge-base with release: `d63f996a757f6255fc1454239616ab4b4435e0f5`.
- Candidate release HEAD: `f97608f178d1ffeca59860195ab7da295f7c8e5f` (requested v2026.9.24 / v0.21.5).
- No commits, staging, pushes, merges, deployment, live configuration writes, live gateway/cron starts, or outbound messages authorized.
- Tests: isolated HOME and HERMES_HOME, empty inherited environment, macOS sandbox denying network and live Hermes home access. Synthetic identities only. Candidate-local `.venv`; no live environment installs.

## Required behaviors

### R1 — allowlisted family groups independent of DM sender allowlist

Old commits: `c7aef3e9e4`, `7b2cd84bbd`.

Upstream **partially covers** this. `scripts/whatsapp-bridge/allowlist.js::matchesInboundWhatsAppGroup` and bridge intake now gate groups by group JID/policy, not every participant's DM identity. Its existing Node regression passes. No bridge patch needed.

The release's Python authorization still denied an allowed group's participant when the restrictive DM sender list was populated. Candidate `gateway/authz_mixin.py` grants a WhatsApp group only when adapter delegation is permitted, the receiving profile's adapter declares its own policy, its actual group policy is `allowlist`, and its actual `_is_group_allowed` returns true. Open/disabled/pairing policies do not get this new grant. DMs/unlisted groups do not inherit it. Adapter mention/reply intake gating remains unchanged.

Evidence: `red.log`; gateway compatibility tests; upstream authorization/profile-scope suites; `bridge.log`.

### R2 — device-qualified LID replies match the same account

Old commit: `9d374d4bba`.

Upstream **partially covers** this: standard `123:7@lid` normalization already exists. Historical `123@7@lid` still failed. Candidate shared WhatsApp normalizer canonicalizes that strictly numeric LID form. Unlike the old permissive numeric-prefix fallback, it does not equate phone and LID namespaces or different accounts. Reverse quote/device direction is tested. No debug logging or metadata dump restored.

Evidence: `red.log`; both gateway compatibility test files, including namespace/malformed-ID negatives.

### R3 — per-conversation display overrides

Old commit: `82da021cf7`.

Upstream **does not cover** `display.chats`. Candidate restores first-non-None chat → platform → legacy tool-progress override → global → platform default → global default/fallback precedence. False is an explicit setting; null inherits. Numeric chat IDs are string-keyed; malformed mappings inherit rather than crash. Global `display.streaming` remains CLI-only as upstream intends; chat/platform streaming may override the gateway's top-level streaming config.

The chat scope is carried through turn display settings and TurnContext, tool progress and its explicit provenance, interim messages, thinking, reasoning output/style, streaming, cleanup, live status, long-running notifications, busy acknowledgments and turn-bound diagnostic renderers. Mattermost still requires an explicit platform OR chat opt-in. Old global/platform users are unchanged. Tests cover real A→B→A config-home loads and the receiving adapter's profile identity.

Not a promise that every new upstream platform-owned UI consults `display.chats`: slash-command reporting, API-server-owned filtering and some lifecycle notification producers remain outside the shared turn resolver; these were not part of the old local port. Deployment review should inspect any newly enabled surface before relying on chat-level suppression there.

### R4 — lean prompt and narrow skill lookup triggers

Old commit: `27a221ce5f`.

Upstream **does not cover** the ordinary-session narrow-skill rule; it again said to load even partially relevant skills. Candidate requires clearly applicable procedural skills before specialist work, exempts casual/tangential matches, and explicitly retains mandatory/domain-safety prerequisites. Skill indexing, caching, availability filtering and repair guidance remain upstream implementations.

Four repeated guidance blocks shrink from 6,163 to 4,864 characters in aggregate; these are character counts, not token or latency claims. Action, verification, prerequisite, literal-preservation and external-write checks remain. Upstream one-shot-specific skills policy is unchanged and covered by its regression suite. Model-selection, provider, fallback and reasoning-default code are untouched.

Evidence: prompt contract tests, `prompt-metrics.json`, `release-guidance.json`, broader prompt/skill suites.

### R5 — preserve Astra defaults

Read-only live observation: model default `gpt-6-astra`, provider `openai-codex`. No model/config/runtime default edits. Synthetic real config loads verify those values survive A→B→A scope changes. The candidate does not embed live credentials or copy live config.

## Withdrawn behavior: inferred family addressing

Old commit `b53933bc0f` is deliberately **not ported**. Its classifier, adapter integration, config wiring, docs and 619-line test file are archived separately under `old-local/`; see `WITHDRAWN.md`.

Kahran withdrew responding without a reply on Oct 7. Candidate adds no free-response group, semantic addressing, mention regex or model-based group routing. Existing explicit mentions/replies and upstream command handling remain. Ordinary text such as “Who is in this photo?” or “Hermes can you tell us?” without an actual mention/reply remains silent in the regression tests.

## Live config observation (read-only, not a copied config)

`live-gate-sanitized.json`: one group allowlist entry, expected family group present; `group_policy: allowlist`, `require_mention: true`; no config free-response chats or mention patterns; `local_address_classifier` absent; one chat display override. This establishes the intended YAML gate. Runtime in-memory/environment overrides were not interrogated and no live traffic was exercised.

## Archive completeness

`source-inventory.json` enumerates 16 changed paths and six non-merge local commits. `old-local/combined.patch` includes the full old-base→old-live net delta, including tests and documentation; six per-commit patches preserve intermediate intent; `old-local/files/` contains exact final old-live bytes for all 16 paths. Hashes are in `snapshot-sha256.json`. No blind cherry-picks.

## Release breadth, not a whole-release certification

The ancestry spans 15,157 upstream commits and a no-rename net diff of 11,516 files: 1,438,244 added lines and 1,088,677 deleted lines. `upstream-breadth.json` breaks this down. The gateway now splits runner/turn/busy/notification code; authorization and config use receiving-profile scope; WhatsApp intake/bridge handling and prompt/skill paths have evolved. Candidate changes adapt behaviors to these interfaces rather than transplanting the old monolithic runner or its tests.

Focused and selected broader suites are meaningful but not exhaustive release CI. No real model request, live bridge handshake, channel send, cron delivery, desktop build, or migration rehearsal was performed.
