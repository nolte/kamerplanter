# Pre-analysis — #1844 auth: light mode lets any caller set the system account's first password

- Classification: `security`. Requirements gate: operator override (autonomous strand B). Route: implement directly.
- Cause (established): `seed_light_mode.py` inserts `system-user` with `password_hash: None`; `LightAuthProvider.resolve_user` ignores the header; `StepUpVerifier.verify` returns `no_local_password` for a hash-less account; red route test on develop: 200 "Password changed".
- Decision: refuse (403) via request-time `refuse_in_light_mode`, like erasure.
- WP1 refusal on password route; WP2 invitations (review SEC-001); WP3 guard over the light-mode surface; WP4 docs/REQ-027/FAQ. Specialist: generalist (orchestrator), reviewed by code-security-reviewer.
- Out of scope, filed: #1855.
