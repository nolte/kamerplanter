# Group 2026-09-25-api-key-rest-controls

- Members: #1850, #1851, #1852 (all repository-owner authored, trusted)
- Tier: 2 (one repository, backend + docs; no cross-repo contract, the HA integration only reads)
- One-sentence change: **every restriction an API key carries (network, rate, tenant scope) binds on every REST route the key reaches, and the tenant scope names one tenant by its stable key.**
- Admission: thematic coupling + shared touch surface (`app/domain/services/auth_service.py::authenticate_api_key`, `app/mcp_server/auth.py`, `app/domain/models/auth.py::api_key_scope_admits`, `app/common/auth.py`); dependency chain #1852 → #1851 (the scope the no-tenant routes decide on must be canonical first).
- Cluster: class cluster — "a key restriction read on one of the two key-accepting surfaces only" (#1817 was the first instance).
- Mode: A (single strand). No member is removable without leaving the class half-closed.
- Operator: approved strand-X plan with full autonomy up to an open, green PR (2026-09-25); breaking changes allowed, listed in Risk / rollout notes.

## Cause verification (develop 8229e4f06)

| member | asserted cause | measurement | result |
|---|---|---|---|
| #1850 | REST path checks revoked/expiry/active only | `AuthService.authenticate_api_key` (auth_service.py:1120-1139) reads neither `ip_allowlist` nor `rate_limit_per_minute`; `grep -rn "ip_allowlist\|rate_limit_per_minute" app` outside `mcp_server/` hits model, export, docstrings only | established |
| #1851 | ~221 routes resolve no tenant | route walk: 798 routes = 577 tenant-resolving + 103 platform-admin + 87 `get_current_user` only + 31 anonymous (103+87+31 = 221) | established |
| #1852 | scope stored as typed; erasure matches key only | `create_api_key` stores `tenant_scope` verbatim (auth_service.py:1060-1079); erasure `doc[@tenant_field] == @tenant_key` with `tenant_field="tenant_scope"` (tenant_erasure_executor.py:111, tenant_erasure_engine.py:215) | established |

## Ordering

#1852 (canonical key scope, key-only predicate, migration) → #1850 (one shared control function on both surfaces) → #1851 (decision per no-tenant route class + guard).

## Completeness matrix

| member | backend code | migration | tests (red-first) | guard | docs DE/EN + REQ-023 | frontend | HA integration |
|---|---|---|---|---|---|---|---|
| #1852 | resolve scope at creation → tenant key; predicate key-only | v0063 canonicalise slug scopes (member → key, else revoke) | create refuses unknown/foreign; erasure removes slug-created key; migration unit test | predicate signature (key only) | authentication.md: scope stored as key | n/a — UI never sends a scope (`AccountSettingsPage.tsx:558`) | n/a — does not create keys |
| #1850 | `enforce_api_key_controls` shared by `authenticate_api_key` and `McpAuthenticator`; client IP threaded from `get_current_user` | n/a | REST route test through `FullAuthProvider`: 401 outside allowlist, 429 over limit | one site reads `ip_allowlist`/limiter; every api-key `get_by_hash` caller enforces | authentication.md | n/a | behaviour change only for keys with allowlist/limit |
| #1851 | `refuse_tenant_scoped_api_key` on account/privacy/credential routes; `/tenants` list narrowed; direct `is_platform_admin` readers honour scope | n/a | scoped key 403 on account routes, 200 on catalogue, `/tenants` narrowed | every no-tenant authenticated route classified | REQ-023 decision table + authentication.md | n/a | HA reads `/users/me` and `/tenants/` → both stay admitted |

## Out of scope

- #1847 (minting routes without step-up) — the scoped-key refusal here covers `POST /auth/api-keys` and device pairing for *scoped* keys only; step-up stays #1847.
- #1864 (assign-slot cross-tenant write, filed from this sweep).
