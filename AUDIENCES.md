# Audiences — Kamerplanter

<!--
Produced following spec/project/audience-identification/. Audiences are derived
from the repository's README (the user types and concerns it names explicitly),
not invented. Do not add audiences without first declaring the bounded context.
-->

## Bounded context

Kamerplanter is a self-hosted, multi-tenant plant lifecycle management system
(Python/FastAPI backend, React frontend, a RAG knowledge service, ArangoDB +
PostgreSQL/pgvector + TimescaleDB + Redis, deployed via Docker / Kubernetes /
Helm / Skaffold) covering seed-to-harvest grow management plus a Home Assistant
integration.

**Inside the boundary**

- The backend, frontend, and knowledge service under `src/`
- The deployment stack (`docker-compose*.yml`, `helm/`, `skaffold.yaml`)
- The Home-Assistant-facing API contract consumed by `kamerplanter-ha`
- The data adapters (GBIF, Perenual, CSV/iCal)

**Outside the boundary**

- The `kamerplanter-ha` custom integration itself (separate repo; consumes this API)
- External botanical data providers and LLM backends (integrated, not owned)
- The operator's own hardware / cluster

## Audiences

Each entry: label, relationship category, interaction surface, expectation,
documentation `track` (`user-docs` or `developer-docs` per
spec/project/docs-audience-tracks/), `confirmed`/`assumed`, criticality.

### Direct consumers

- **Home grower / hobby gardener / houseplant owner** — _category_: direct-consumer ·
  _surface_: the web UI, adaptive care reminders, the knowledge assistant ·
  _expects_: guidance scaled to skill level (beginner/intermediate/expert),
  reliable season- and hemisphere-aware reminders, accurate plant and nutrient
  data · _track_: `user-docs` · _status_: `assumed` · _criticality_: primary

- **Community-garden administrator** — _category_: direct-consumer ·
  _surface_: the web UI with role-based access (admin/grower/viewer), shared
  gardens, the invitation system ·
  _expects_: tenant isolation, role management, shared-responsibility workflows ·
  _track_: `user-docs` · _status_: `assumed` · _criticality_: primary

### Operators

- **Self-hoster** — _category_: operator ·
  _surface_: Docker Compose / Kubernetes / Helm / Skaffold, `.env` configuration,
  the multi-service data stack (ArangoDB, PostgreSQL/pgvector, TimescaleDB, Redis) ·
  _expects_: reproducible deploy, an upgrade path, backup and retention controls,
  resource guidance · _track_: `developer-docs` · _status_: `assumed` ·
  _criticality_: primary

- **Home Assistant integrator** — _category_: operator ·
  _surface_: the Home-Assistant-facing API for sensor-data import and actuator
  control (consumed by `kamerplanter-ha`) ·
  _expects_: a stable API contract for sensors and actuators ·
  _track_: `developer-docs` · _status_: `assumed` · _criticality_: secondary

### Contributors / maintainers

- **Maintainer (`nolte`)** — _category_: contributor ·
  _surface_: the monorepo (backend / frontend / knowledge service), CI, the
  specs under `spec/` · _expects_: green CI and spec-grounded changes ·
  _track_: `developer-docs` · _status_: `assumed` · _criticality_: primary

- **Claude Code as co-author** — _category_: contributor ·
  _surface_: `CLAUDE.md`, `.claude/`, `spec/`, the Taskfile ·
  _expects_: deterministic task targets and readable conventions ·
  _track_: `developer-docs` · _status_: `assumed` · _criticality_: secondary

### Governing parties

- **GDPR / data-protection** — _category_: governing ·
  _surface_: personal-data handling, retention policies, the self-hosted-private
  design · _expects_: lawful processing, retention enforcement, data-subject
  rights · _track_: `developer-docs` · _status_: `assumed` · _criticality_: secondary

### Indirect audiences

- **External botanical / data providers (GBIF, Perenual)** — _category_: indirect ·
  _surface_: the enrichment adapters that call their APIs ·
  _expects_ (without knowing): correct API usage, attribution, rate-limit respect ·
  _track_: `developer-docs` · _status_: `assumed` · _criticality_: peripheral

## Revisit triggers

Re-run `audience-identify revisit` when any of the following changes:

- A hosted / SaaS offering is introduced (the self-hosted-only assumption breaks).
- A new external integration surface appears (a public API, a second smart-home
  platform, a mobile app).
- A regulated data class enters scope beyond today's personal-data handling.
- An external contributor pattern emerges (guest contributors, plugins).
