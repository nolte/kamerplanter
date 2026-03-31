# ADR-005: YAML-based Seed Jobs at Application Startup

**Status:** Accepted
**Date:** 2026-03-17
**Deciders:** Kamerplanter Development Team

## Context

Kamerplanter requires extensive master data (botanical families, species, cultivars, fertilizers, nutrient plans, starter kits, workflows, IPM data, activities, etc.) that must be consistently present in the database on first start and on every update. The following decisions had to be made:

1. **Data format**: In which format are seed data maintained?
2. **Execution timing**: When and how are seed jobs executed?
3. **Idempotency**: How is it ensured that repeated seeding does not create duplicates?
4. **Enrichment process**: How are new master data added and existing data extended?

## Decision

### Declarative YAML Files as Single Source of Truth

All seed data is stored as YAML files in `src/backend/app/migrations/seed_data/`. YAML was chosen because it is human-readable, diff-friendly (Git), and well-suited for hierarchical data. Each domain has its own file (e.g., `species.yaml`, `plagron.yaml`, `starter_kits.yaml`).

### Startup Seeding in FastAPI Lifespan

Seed jobs are executed at application startup in the FastAPI lifespan hook (`main.py`) — not as a separate CLI command or migration step. The execution order is fixed:

1. `ensure_collections()` — Create collections and graph
2. `seed_location_types()` — Location types
3. `run_seed()` — Core master data (families, species, cultivars, IPM, workflows)
4. `run_seed_starter_kits()` — Onboarding starter kits
5. `run_seed_adventskalender()` — Seasonal kits
6. `run_seed_plant_info()` / `run_seed_plant_info_extended()` — Extended plant data
7. `run_seed_plagron()` / `run_seed_gardol()` — Product-specific fertilization plans
8. `run_seed_nutrient_plans_outdoor()` — Outdoor nutrient plans
9. `run_seed_activities()` — Activity definitions
10. `run_seed_lifecycles_outdoor()` — Outdoor lifecycles
11. Conditional: `run_seed_light_mode()` — Only when `KAMERPLANTER_MODE=light`

### Idempotency via Lookup-before-Create

Each seed job checks whether a record already exists (by `scientific_name`, `kit_id`, `product_name`, etc.) before creating it. Four patterns are used:

- **Lookup + Create/Update**: Existence check by unique field, then insert or selective update of defined fields
- **Selective Field Update**: Only predefined `seed_update_fields` are overwritten — user-defined changes to other fields are preserved
- **Backfill Missing**: Count existing entries, add missing ones (e.g., nutrient plan phases)
- **Exception-based**: Try/catch for graph edges that throw an error on duplicate

### Reference Resolution via Intermediate Maps

YAML files use human-readable names (`scientific_name`, `product_name`). During seeding, intermediate maps are built (`name -> _key`) that subsequent steps use to resolve references (e.g., `species_names` in starter kits -> `species_keys`).

## Enrichment Process for Seed Data

The process for adding or extending master data follows a fixed schema:

### 1. Edit or Create YAML File

New data is added to the appropriate YAML file in `seed_data/`. For new domains, a new file is created. The structure follows the Pydantic models in `domain/models/`.

### 2. Extend Pydantic Model (if needed)

If new fields are required, the Pydantic model in `domain/models/` is extended. Pydantic v2 automatically handles coercion from YAML strings to enums, lists, etc.

### 3. Adapt Seed Function

The corresponding seed function in `migrations/seed_*.py` is extended:

- Add new fields to `seed_update_fields` (so existing records get updated)
- Add new reference resolutions (if the new field references other entities)
- `yaml_loader.load_yaml()` uses the same mechanism

### 4. Observe Startup Order

When a new seed file is created, it must be hooked into `main.py` in the correct order — dependencies (e.g., species before starter kits) determine the position.

### 5. Enrichment via Agents

For initial creation and extension of plant data, the `plant-info-document-generator` agent is available. It researches botanical data and produces structured documents that are then transferred into the YAML files.

### 6. Testing

A restart of the application automatically triggers all seed jobs. Structured logging (`structlog`) records every action (created/updated/skipped) with identifiers.

## Rationale

### Why YAML and not SQL Migrations, JSON, or CSV?

- **SQL Migrations** (Alembic-style) are not suitable for ArangoDB as a document database
- **JSON** is less readable and harder to diff than YAML for deeply nested structures
- **CSV** cannot represent hierarchical data (nested phases, dosage lists)
- **YAML** is the natural compromise: machine-readable, human-readable, Git-diff-friendly

### Why Startup and not Separate Migrations?

- **Simplicity**: No separate migration command needed, no forgotten step during deployment
- **Always consistent**: Every startup guarantees complete master data
- **Idempotency**: Repeated execution is safe — no state tracking (no migration table) needed
- **Kubernetes-ready**: Pods can restart at any time; seed jobs are part of the startup lifecycle

### Why no Transaction Rollback?

- ArangoDB transactions across many collections are complex and limited
- Partial seeding is acceptable: idempotency ensures that a restart fills in the rest
- Startup blocks on errors anyway — an incomplete seed leads to a pod restart

## Consequences

### Positive

- Master data is versioned and reviewable (Git)
- Simple onboarding process: `git pull` + restart = current data
- Clear separation: YAML = data, Python = orchestration
- Extensible: new seed file + hook into `main.py` is sufficient
- Observable: structured logging shows exactly what was seeded

### Negative

- Startup time increases with growing data volume (currently ~2-3s, acceptable)
- No atomic rollback on partial failure (compensated by idempotency)
- Order of seed jobs must be maintained manually (dependency graph is implicit)
- `seed_update_fields` must be manually extended for new fields — otherwise existing records are not updated
