# Withdrawn — inferred family addressing

Kahran, 2026-10-07: responding to family-group messages without a reply was withdrawn. Do not restore the classifier as part of this upgrade.

Historical implementation: `b53933bc0f2abbd43a17dfa8ee9657ad15e5601f`.

It introduced `local_address_classifier`, a loopback Ollama classifier receiving bounded message text; adapter-side async gating; config propagation; documentation and a 619-line regression file. It was designed to allow selected semantically addressed messages without an explicit reply or mention.

All historical implementation/test bytes remain under `old-local/files/`, with the complete individual patch at `old-local/b53933bc0f.patch`. They are evidence only, not importable candidate runtime wiring. The new release's runtime contains no `gateway/platforms/whatsapp_local_address.py`, and this candidate does not add one or enable equivalent behavior.

The read-only YAML observation found no `local_address_classifier` entry, `require_mention: true`, and the family group in an allowlist. No free-response setting was added, and no classifier/model calls were made. Runtime/environment overrides and live traffic are outside this verification.

Regression tests explicitly reject ordinary family questions and a textual “Hermes” address without a true mention/reply. Explicit bot replies, actual mentions and upstream command handling retain their existing paths. There is no new unsolicited response path.
