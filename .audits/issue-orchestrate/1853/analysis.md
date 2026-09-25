# Pre-analysis — #1853 global dashboard summary returns any tenant's dashboard

- Issue: https://github.com/nolte/kamerplanter/issues/1853 (author: repository owner, trusted)
- Classification: `security` — authorization bypass (IDOR on tenant key); secondary: `bug`
- Route: implement directly (one outcome, one PR strand, no roadmap item)
- Requirements gate: operator override — the issue carries four testable acceptance criteria; the operator approved the strand-X plan with full autonomy up to an open, green PR (2026-09-25).

## Cause verification (established)

- `src/backend/app/api/v1/dashboard/router.py` (develop 8229e4f06): router `dependencies=[Depends(get_current_user)]` only; `get_dashboard_summary(tenant_key: str = Query(""))` → `service.get_summary(tenant_key)`. Confirmed.
- Mounted unconditionally: `src/backend/app/api/v1/router.py:179`. Confirmed.
- Red test through the deployed app: `GET /api/v1/dashboard/summary?tenant_key=tenant_b` by a non-member → **200** with tenant B's data.
- No consumer: `git grep "dashboard/summary"` → only the tenant router docstring; frontend `api/endpoints/dashboard.ts` uses `/t/{slug}/dashboard/{widgets/catalog,aggregated}`; kamerplanter-ha `api.py` has no dashboard summary call; no reach probe names it.

## Scope

In: remove the global route; route test through the real resolver chain; class guard over the assembled app.
Out: anything else the sweep finds → separate issue.

## Work packages

| id | problem | acceptance | files | specialist |
|----|---------|------------|-------|------------|
| WP1 | remove global summary route | 404 for any caller, absent from OpenAPI | `app/api/v1/dashboard/router.py`, `app/api/v1/router.py` | generalist (strand-X agent; single-file deletion) |
| WP2 | route test | non-member of B gets 403 on `/t/club-b/…`, service never called; positive control 200 | `tests/api/test_dashboard_summary_tenant_isolation.py` | generalist |
| WP3 | class guard | every route with a tenant selector depends on a resolver / platform-admin gate; raw reads allowlisted with reason | `tests/unit/guards/test_tenant_selector_routes_depend_on_a_resolver.py` | generalist |
| WP4 | security review | `nolte-engineering:code-security-reviewer` | — | code-security-reviewer |

Ordering: WP3, WP2 (red) → WP1 → WP4.

## Class sweep (develop 8229e4f06)

Predicate: leaf `APIRoute` of `app.main.app` (walked through `original_router`) whose dependant tree has a path/query/header/cookie/body parameter, or Pydantic body field (recursive), whose name or alias matches `tenant([_-]?(key|id|slug))?$` (case-insensitive), and that depends on none of `get_current_tenant`, `get_active_tenant_key`, `get_active_tenant_context`, `require_platform_admin`.
Result: 585 selector routes, **1** unresolved (`GET /api/v1/dashboard/summary`). Raw-read AST scan over `app/api/`: 2 hits, both non-request selectors (allowlisted with reason).

## Risks

- Breaking API change: route removed (no known consumer). Listed in Risk / rollout notes.
