# `zap-setup/`

External tooling for the OWASP ZAP DAST workflow (NFR-015). Speaks to the Kamerplanter backend exclusively over the public REST API. **Not** part of the production backend image.

## Files

| File | Purpose |
|---|---|
| `test-identities.yaml` | Tenant + user + membership definitions for cross-tenant scans (NFR-015 §3.1). |
| `seed-test-identities.sh` | Idempotent bash seeder: registers users, creates tenants, invites members through the public API. Phase 1. |
| `seed-cross-tenant.sh` | Per-run setup that logs in each test identity, creates demo resources in tenant α, and exposes the resulting tokens to the ZAP context. Added in Phase 3. |

## Usage

```bash
export KP_API_BASE="https://staging.kamerplanter.example"
export KP_ZAP_PWD_TENANT_A_ADMIN="$(op read op://staging/zap-tenant-a-admin/password)"
export KP_ZAP_PWD_TENANT_A_VIEWER="$(op read op://staging/zap-tenant-a-viewer/password)"
export KP_ZAP_PWD_TENANT_B_ADMIN="$(op read op://staging/zap-tenant-b-admin/password)"

./seed-test-identities.sh
```

The script:

1. Registers every user from `test-identities.yaml` via `POST /api/v1/auth/register`. Already-existing accounts are reported but not treated as failures.
2. For each tenant, logs in as the configured owner and creates the tenant via `POST /api/v1/tenants/`. Existing tenants are reused.
3. Invites every additional member via `POST /api/v1/tenants/{slug}/invitations/email`, then accepts the invitation as the invitee via `POST /api/v1/tenants/invitations/accept`.

Repeated runs are no-ops as long as backend state is consistent.

## Domain choice — why `@zap.kamerplanter.example`

RFC 2606 reserves `.test` and `.example` as special-use top-level domains for documentation and testing. The Pydantic `email-validator` library rejects email addresses ending in `.test`, but accepts `.example`. To keep both Pydantic validation green **and** retain the “these accounts are obviously test fixtures” signal, every ZAP identity uses the subdomain `zap.kamerplanter.example`. The pre-deploy check (NFR-015 §3.1) blocks any production DB snapshot whose `users` collection contains an entry ending in `@zap.kamerplanter.example`.

## Safety rails

- The script never reads or writes the database directly; if the public API enforces a constraint, the seeder enforces it transitively.
- Passwords are sourced from environment variables; the literal string `from-env-required` aborts the run with exit 2.
- The script is idempotent and ships no destructive operations — there is no `delete-test-identities.sh` counterpart by design. Cleanup of staging environments is owned by the staging-namespace lifecycle (rebuild from scratch), not by this tooling.
