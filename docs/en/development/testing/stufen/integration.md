# Integration Tests

Integration tests verify the **interplay of several building blocks with real external dependencies** — above all data access against a running ArangoDB and the behavior of the API layer. They sit in the middle of the [test pyramid](index.md): fewer than unit tests, but more realistic.

## What this level verifies

- **Repository and database access:** that queries, indexes, and the graph (`kamerplanter_graph`) work as expected against a real ArangoDB instance.
- **API layer:** error handling and status codes of the FastAPI endpoints.

## Tested areas at a glance

| Area | Tested elements | Extent |
|------|-----------------|--------|
| API layer (routers) | REST endpoints per domain — dashboard, nutrient, weather, privacy, recognition, tenants, locations, and many more | extensive |
| Database integration | ArangoDB setup, graph, multi-year season cycle | focused |
| Tenant isolation | propagation/lineage across tenant boundaries | focused |

## Tooling & location

| | Value |
|---|---|
| Tooling | pytest |
| Location | `src/backend/tests/integration/`, `src/backend/tests/api/` |
| Dependency | a running ArangoDB instance |

## Running

This level needs a database, and a missing one is **not** passed over in silence: in CI the run fails and names the address it tried, locally it skips with the same reason — and because the target declares the skip floor `--max-skipped 0`, even that skip is red.

```bash
# Start ArangoDB (the dev stack or a throwaway container)
task dev:core
# or:
docker run -d --rm --name kp-it-arango -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12

# Integration tests only — the same invocation CI runs
task test:backend:integration
```

Details in the [testing concept → Integration Tests](../index.md#integration-tests).

## Conventions

- Integration tests may change the state of the test database — they clean up after themselves or use isolated collections.
- In CI they run against an ArangoDB service container; without a database the run there fails deliberately instead of reporting green.
- The connection is checked **once**, centrally (`tests/integration/conftest.py`, session fixture `arango_db`); a module attaches to it with `pytestmark = pytest.mark.usefixtures("arango_db")` and brings no probe of its own.
- No module hard-codes the address: `ARANGODB_HOST` / `ARANGODB_PORT` / `ARANGODB_USERNAME` / `ARANGODB_PASSWORD` point the level at any server.
