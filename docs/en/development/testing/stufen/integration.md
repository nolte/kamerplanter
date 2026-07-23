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

Integration tests are **automatically skipped** when no database is reachable (`@pytest.mark.skipif(not ARANGO_AVAILABLE, …)`) — so the suite stays green even without a DB.

```bash
# Start ArangoDB (e.g. via Docker Compose)
docker-compose up -d arangodb

# Integration tests only
cd src/backend && pytest tests/integration/ -v
```

Details in the [testing concept → Integration Tests](../index.md#integration-tests).

## Conventions

- Integration tests may change the state of the test database — they clean up after themselves or use isolated collections.
- In CI they run with a provided ArangoDB; locally without a DB they are cleanly skipped rather than failing.
