# Issue #1750 — pre-analysis

- **Issue:** #1750 "compose: ArangoDB, Valkey, pgvector, Ollama, backend and frontend publish on all interfaces" (author: nolte — trusted, repository owner)
- **Classification:** `security` (secondary: `infra`). Rationale: host ports of data stores (ArangoDB, Valkey, Postgres) and unauthenticated services (Ollama, light-mode app) are published on every interface.
- **Requirements gate:** operator override (2026-09-24/25, full autonomy) — the issue carries three explicit acceptance criteria and the operator brief sharpens them; no elicitation run.
- **Route:** implement directly — one outcome, one PR strand, no roadmap item.

## Measured state (develop 47771d74d)

Inventory by YAML parse of every tracked compose file (established: `grep -n -A2 ports: docker-compose*.yml`):

| File | Service | Entry | Bound? |
|---|---|---|---|
| docker-compose.yml | arangodb | `8529:8529` | no |
| docker-compose.yml | valkey | `6379:6379` | no |
| docker-compose.yml | vectordb | `5433:5432` | no |
| docker-compose.yml | ollama | `11434:11434` | no |
| docker-compose.yml | timescaledb | `5432:5432` | no |
| docker-compose.yml | reranker-service | `127.0.0.1:8081:8081` | yes (#1739) |
| docker-compose.yml | backend | `8000:8000` | no |
| docker-compose.yml | frontend | `8080:8080` | no |
| docker-compose.release.yml | arangodb, vectordb, ollama, timescaledb, backend, frontend | same shapes | no |
| docker-compose.reach.yml | arangodb, backend-full | `127.0.0.1::8529`, `127.0.0.1::8000` | yes |
| docker-compose.security.override.yml | backend, frontend | `127.0.0.1:…` | yes |
| docker-compose.e2e.yml / .e2e.ci.yml | — | no `ports:` | n/a |

Divergences from the issue text: the issue does not list TimescaleDB (5432) nor `docker-compose.release.yml`, which is the file end users run (docs "Permanent operation") and ships `KAMERPLANTER_MODE: light` (no authentication). #1739's guard (`test_ml_sidecar_limits.py::TestComposeRuntime`) does **not** assert the reranker's `127.0.0.1` bind — it checks read_only/cap_drop/user only (established: `grep -n 8081 test_ml_sidecar_limits.py` → no hit).

Sibling spellings outside compose files: `docker compose run --publish 8080:80` (.taskfiles/mcp.yaml:158), `docker run -p 8529:8529` copy-paste commands in integration-test docstrings, conftest skip message, testing docs, docker/*/README.md, spec NFR examples; GitHub-hosted-runner publishes in backend-guards.yml (`services.arangodb.ports`) and lane-inputs.yml.

## Work packages

| ID | Problem | AC | Files | Specialist |
|---|---|---|---|---|
| WP1 | guard over every host-port publish | red on develop, green after; fails closed on unparseable spellings; named allow-list keyed explicitly | src/backend/tests/unit/guards/test_published_ports_bind_loopback.py | generalist (strand agent) |
| WP2 | bind compose ports to loopback; front doors opt-in via `KAMERPLANTER_BIND_ADDRESS` | guard green; e2e smoke unaffected | docker-compose.yml, docker-compose.release.yml, .env.example | generalist |
| WP3 | sibling CLI publishes + docs | guard green; docs describe opt-in | .taskfiles, tests docstrings, docs/de+en | generalist |

Order: WP1 → WP2 → WP3. Verify: guards lane, code-security-reviewer, /code-review medium.
