# ADR-009: Versioned Database Migration Framework

**Status:** Accepted
**Date:** 2026-07-04
**Deciders:** Kamerplanter Development Team

## Context

Database seeds and one-off data migrations used to live as a loose collection of functions in `app/migrations/`, called individually, hard-coded, and unordered during application startup (`app/main.py`) — roughly 18 calls in sequence, all of which re-ran on **every** start. This left several gaps:

- No **tracking** of which migration had already run against a given database
- No **error isolation** — a single failing migration took down the entire startup
- No **declared order** — execution order lived implicitly in the call sequence
- No **shared conventions** for report format and `--dry-run`
- No **versioning/rollback concept** to show which database state is currently applied

These gaps caused two consecutive backend startup crashes on 2026-07-04: first on an enum value (`harvest`) retired since Issue #306, for which no data migration existed; then on a blocked Home Assistant endpoint. In both cases a single step took down the whole startup.

**Constraints:** ArangoDB, the primary database, is schemaless and AQL-based ([ADR-001](001-arangodb-multi-model.md)) — an Alembic-/SQL-style migration framework does not fit. The existing pattern of "idempotent YAML seed jobs on every startup" (docs/adr/005, [YAML-based Seed Jobs at Startup](005-yaml-seed-jobs-startup.md)) remains valid and is cleanly separated from one-off migrations, not replaced. Multiple backend replicas in production must not trigger duplicate or concurrent migration execution.

## Decision

We introduce a **versioned, tracked migration framework** and draw a clear conceptual line between **migrations** (one-off, versioned) and **seeds** (idempotent, always running):

| | Migration | Seed |
|---|---|---|
| Purpose | One-off transformation of existing data/structure | Loading/upserting reference data |
| Execution | Exactly once per database (tracked) | On every startup (idempotent) |
| Error policy | **Fatal** — startup aborts | Non-fatal — startup continues |

**Core building blocks:**

- **Tracking collection `schema_migrations`** — one document per applied version, holding the version number, name, a checksum of the `up()` source, timestamp, and duration. If the checksum of an already-applied migration drifts, a warning is logged — applied migrations are treated as immutable; corrections ship as a **new** migration.
- **Concurrency lock** — prevents multiple backend replicas starting at the same time from applying the same migration twice.
- **Strictly linear version history** — migrations are sequentially numbered (`v0001`, `v0002`, …); gaps before the current head are an error, and out-of-order application is not allowed.
- **Migration protocol** with `up()`/`down()`: rollback is supported where it makes sense; non-reversible data transformations declare that honestly (`reversible = False`) instead of faking a reversal.
- **Baseline migration `v0001`** marks the database state prior to the framework's introduction; the five existing migrations were wrapped as `v0002`–`v0006`.
- **Startup order:** all pending migrations run first (fatal on error), then the seed registry (isolated, non-fatal for reference data).

### Database migrations — CLI reference

A CLI entry point exists for controlled operational use and for scaffolding new migrations:

```bash
python -m app.migrations upgrade      # apply all pending migrations
python -m app.migrations downgrade    # roll back to a target version (reversible migrations only)
python -m app.migrations current      # show the highest applied version
python -m app.migrations history      # list all applied migrations with timestamps
python -m app.migrations create <slug> # scaffold a new vNNNN_<slug>.py from a template
```

`upgrade` and `downgrade` support `--dry-run` to compute the plan without writing anything — a prerequisite for controlled production execution. This CLI does not change the public HTTP API; it is a pure ops/developer tool.

Migrations currently still run inside the FastAPI `lifespan` on startup (protected by the concurrency lock). The medium-term target is to run them instead as a dedicated Kubernetes Job / Helm `pre-upgrade` hook, so app replicas never migrate themselves — the CLI entry point is already the foundation for that.

### Rejected alternatives

| Option | Why rejected |
|---|---|
| Lightweight registry without versioning | Does not satisfy the need for a rollback-capable, reproducible history |
| Conventions/documentation only, no framework code | Does not fix the real startup crashes (missing error isolation, no tracking) |
| Existing SQL tool (Alembic/yoyo) | Tied to SQLAlchemy/SQL DDL — does not fit schemaless, AQL-based ArangoDB |
| Migrations exclusively as an external job, never at startup | Adopted as the target state, but not as an immediate break — the startup path with the lock remains in place as an interim solution |

## Consequences

### Positive

- A failing reference-data seed no longer takes down the startup.
- One-off migrations run exactly once, tracked, and in a defined order.
- The database state is inspectable at any time via `current`/`history`.
- Replica races on parallel pod startup are excluded by the lock.
- New migrations follow a single, tested pattern (`create <slug>` scaffolding).

### Negative

- Additional framework complexity and a new `schema_migrations` collection.
- Migration authors must follow the versioning and idempotency rules.
- Most data transformations remain effectively irreversible — rollback is not a cure-all, but an honestly declared exception.

### Follow-ups

- Move migrations into a dedicated Kubernetes Job/Helm hook rather than running them in the app pod lifespan, as a medium-term step.
- Any removal or renaming of a persisted enum value or field must ship a data migration in the same change (a direct lesson from Issue #306).

## References

- Canonical decision: `spec/decisions/ADR-005-versioned-migration-framework.md` *(note: this uses its own numbering under `spec/decisions/`, independent of the `docs/adr/` count here — this page is the published version of Canonical ADR-005, under the next free number, `009`)*
- Normative requirement: `spec/nfr/NFR-016_Datenbank-Migrationsstrategie.md`
- [ADR-001](001-arangodb-multi-model.md) — ArangoDB as a schemaless primary database
- docs/adr/005 — [YAML-based Seed Jobs at Startup](005-yaml-seed-jobs-startup.md) (the separate seed pattern)
- Issue #306 — retirement of the `harvest` phase (triggering incident)
