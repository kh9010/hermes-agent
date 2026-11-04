# Version 01 — review and future deployment gates

## Candidate review

- Behavior port, not a cherry-pick: upstream bridge intake retained unchanged; new Python authorization uses receiving-profile adapter checks; the release's split turn/runner/busy paths carry chat scope.
- Security: no blanket group-policy grant; disallowed groups, stranger DMs, open/disabled/pairing policies and disabled adapter delegation remain denied in the new authorization regression. Secondary-profile adapters cannot borrow the primary group grant. LID normalization preserves namespaces.
- Privacy: withdrawn semantic addressing is archive-only. No inference model, new group allowlist, free-response path or extra mention pattern is enabled. Source-level runtime model/provider/default selectors remain unchanged.
- Display: chat false values remain explicit (including Slack native progress provenance), null inherits, and platform/global behavior remains. Chat scope is bound into the per-turn resolver rather than stored globally. Upstream profile-secret scope is retained.
- Prompt: wording reduced, not tool/default configuration. Required procedural skills and execution-safety obligations retain regression coverage. Upstream one-shot footprint remains unchanged.
- Diagnostics extension uses the same chat resolver for turn-owned notifications. It does not claim all platform/lifecycle-specific surfaces have been ported. See REQUIREMENTS R3 limitations.
- Review method: source diff inspection; before/after behavioral tests; upstream related suites; release-byte differential diagnosis. No independent human/security audit or full-release CI certification claimed.

## Remaining verification limits

Nine test failures under the chosen hard isolation reproduce with release module bytes:

1. Six tests traverse from a temporary directory to ancestors, assuming there is no surrounding Git checkout/AGENTS file. User scope requires scratch paths inside this worktree, so the repository root is visible. One mock agent also lacks a diagnostic method when that unexpectedly found large AGENTS file causes truncation. These are harness/location-sensitive outcomes, not demonstrated production faults.
2. Three tests bind local sockets (bridge PID lookup and API-server reasoning tests). The macOS sandbox denies all network, including bind. Restrictions were not relaxed to make tests pass.

The original broader attempt also exposed missing messaging extras and a newly written test that changed only HERMES_HOME instead of the release's context-local override. Messaging extras were installed only in candidate `.venv`; the synthetic A/B/A test now uses the real scope override. Original failed output is retained rather than erased.

No live endpoints or credentials were used. No model/bridge/gateway/cron/channel integration run occurred. Six skipped tests in the final broad run remain reported by the upstream runner. The full release, optional connectors, desktop/web builds, packaging and data migrations still need their own CI/rehearsal.

## Deployment steps — review only, DO NOT execute from this handoff

1. Obtain separate approval for review/commit/PR and later deployment. This worktree is deliberately uncommitted; do not treat release HEAD as the candidate's commit.
2. Resolve/re-run the nine isolation-limited tests on disposable CI with approved scratch outside the checkout and network isolation permitting only its own mock listeners. Run full release CI plus packaging and relevant optional connector suites. Inspect newly enabled display surfaces before depending on chat suppression there.
3. Inventory the actual live launch path, service definitions, Python/Node environments, bridge session location, cron ownership, plugins/skills and config schema **read-only**. This task did not establish a deployment target or edit these.
4. Before any live action, enumerate and verify a restorable backup of configuration, credentials/session material, databases, cron state, plugins/skills and old executable environment. Rehearse migrations on protected copies; do not expose real credentials to tests. Review schema downgrade/rollback compatibility rather than assuming Git rollback is enough.
5. Build an independent release environment from reviewed lockfiles. Preserve Astra (`gpt-6-astra`, `openai-codex`), explicit family group allowlist/reply gate and existing display.chats. Do not restore `local_address_classifier` or add permissive group behavior. Review bridge dependency/runtime changes and required migration prompts.
6. With deployment explicitly approved, pause the applicable service/scheduler paths once, avoid duplicate gateway/bridge ownership and cron deliveries, and switch only the approved runtime. No generic restart/update command is provided because ownership/backup/migration details are not yet verified.
7. Validate restart-free settings and transport health first. Any real test message or cron delivery needs its own permission. Confirm intended group silence as well as explicitly addressed replies. Verify model/provider selection and quiet family rendering.
8. If validation fails, stop the candidate service and restore the verified old environment/state using the rehearsed migration-aware rollback. Keep old credentials/session backup protected. Only after acceptance may the old environment be retired and the committed release registered on the version rail.

## Wrong turns preserved

- Background shell lacked `uv` on PATH; absolute `/Users/kahransingh/.hermes/bin/uv` succeeded. The requested `/opt/homebrew/bin/python3.11` did not exist; `uv sync` selected available CPython 3.11.15 and created candidate `.venv`. No live pip/environment install. Scope caveat: this first dependency preparation used uv's default shared download/build cache outside the worktree (two downloaded wheels and the editable build). Later installation explicitly used `.upgrade-uv-cache` inside the worktree. Shared cache was not deleted because pre-existing contents must be preserved; the known-new local cache was removed.
- A shell glob matched no test file; replaced with explicit Python discovery that fails on empty selections.
- Initial prompt-length regression tried reading Git through a sandbox that intentionally blocks the live Git common directory. Replaced that test dependency with a release-guidance snapshot.
- Initial YAML group-count probe counted characters in a scalar; corrected to parse the allowlist. Final sanitized evidence records one entry; no group identifiers or credentials are dumped.
- Final broad run was repeated with `-rfs` rather than `-rs` to retain failed node IDs as well as skips. Counts are per run, not summed across repeated/overlapping suites.
