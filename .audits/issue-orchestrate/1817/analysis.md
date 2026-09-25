# Pre-analysis — #1817 auth: an API key's tenant_scope is not enforced on the REST API

- Classification: `security` (secondary: `bug`) — a credential restriction is not enforced on one of two surfaces.
- Requirements gate: operator override (autonomous strand B, security wave); acceptance criteria in the issue are testable as written.
- Route: implement directly (one outcome, one PR strand).

## Cause verification (established)

- `AuthService.authenticate_api_key` (src/backend/app/domain/services/auth_service.py:1120-1137 on 9cacdb752) returns the owning `User`; `tenant_scope` is never read on that path.
- `grep -rn tenant_scope src/backend/app` → the only enforcement is `McpAuthenticator._resolve_memberships` (app/mcp_server/auth.py:177-178).
- Red run on develop code: 7 of 15 new tests fail (resolver + real-HTTP route tests), the scoped key reaches `/t/club-b/…` with 200.

## Work packages

| id | problem | acceptance | files | specialist |
|----|---------|------------|-------|------------|
| WP1 | carry the key's scope with the principal | `authenticate_api_key` returns a principal whose scope is set only there; not loadable from a document | models/user.py, services/auth_service.py | generalist (orchestrator) |
| WP2 | enforce in `_membership_for_slug` + personal fallback | 403 same body as non-member; path and header agree | common/auth.py | generalist |
| WP3 | one scope predicate for REST and MCP | `api_key_scope_admits` used by both | models/auth.py, mcp_server/auth.py | generalist |
| WP4 | tests + funnel guard | red on develop, green after | tests/unit/common, tests/api, tests/unit/guards | generalist |

Out of scope (filed): #1850, #1851, #1852, #1853; scope escape via minting routes commented on #1847.
