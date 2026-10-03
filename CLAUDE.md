# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

Kamerplanter is an **agricultural technology system** for plant lifecycle management (cannabis, vegetables, herbs). The repository contains both **specification documents** (German) and a **working implementation** (English source code, NFR-003).

Documentation is written in **German**; source code must be in **English only** (NFR-003).

Agents authored under `.claude/agents/` (`distribution: project`) MAY author the `description` value and the system-prompt body in German, matching the project's documentation language. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`, `tags`) remain English per `agent-management.Structure`. This authorization is the project-language exception referenced by `agent-management.Structure` and `agent-review.Checks-derived-from-agent-management`.

## Repository Structure

- `spec/` — Specification documents
  - `spec/req/` — Functional requirements (REQ-001 through REQ-032)
  - `spec/nfr/` — Non-functional requirements (NFR-001 through NFR-015)
  - `spec/ui-nfr/` — UI non-functional requirements
  - `spec/stack.md` — Complete technology stack specification
  - `spec/style-guides/` — Code style guides (Backend, Frontend, Helm, HA)
  - `spec/knowledge/` — Plant & domain knowledge base
    - `spec/knowledge/rag/` — RAG-optimized YAML chunks (8 categories)
    - `spec/knowledge/plants/` — Plant info documents (210 species)
    - `spec/knowledge/products/` — Fertilizer product data
    - `spec/knowledge/nutrient-plans/` — Nutrient plan documents
  - `spec/rag-eval/` — RAG benchmark questions & topic synonyms
  - `spec/design/` — KAMI graphic prompts
  - `spec/analysis/` — Review & analysis reports
  - `spec/target-audiences/` — Target audience personas
  - `spec/e2e-testcases/` — E2E test case specifications
- `src/backend/` — Python/FastAPI backend (implemented)
- `src/frontend/` — React/TypeScript frontend (implemented)

## Crash recovery & parallel working copies

Session transcripts persist under `~/.claude/projects/<encoded-cwd>/`; resume with `task resume`, `claude --continue` or `claude --resume <id>`. Run long work as a top-level session in a worktree created by `task worktree:add -- feat/<branch>`, never under `.claude/worktrees/` (the `guard-nested-worktree` hook rejects commits there). Worktree-isolated subagents and `Workflow` runs are not recoverable via `claude --resume`. Details: `.claude/reference/claude-md-offload.md`.

## Claude Code plugin adoption

Generic delivery capabilities come from the `nolte-shared` + `nolte-engineering` plugins, never from local copies in `.claude/`; only domain assets (Steckbrief, agrobiology, HA, RAG) stay local. Launch with `task claude` (extra args are forwarded). Rules (no copies, verify before remove) and the full adoption notes: `.claude/reference/claude-md-offload.md`.

## Requirements Overview

The REQ index lives in `spec/req/` (one file per requirement, `REQ-<NNN>_<Title>.md`; list with `ls spec/req`). NFRs: `spec/nfr/`.

## Verbindliche Style Guides

All code MUST follow the style guides in `spec/style-guides/`:

- **Backend (Python/FastAPI):** `spec/style-guides/BACKEND.md` — 5-layer architecture, naming conventions, Pydantic patterns, Service/Engine/Repository patterns, error handling, enums, logging, Celery tasks, tests, docstrings, typing, imports
- **Frontend (React/TypeScript/MUI):** `spec/style-guides/FRONTEND.md` — component patterns, props typing, Redux Toolkit, custom hooks (useMemo obligation), MUI styling, routing, i18n, API layer, form patterns, tests, accessibility
- **Helm/Kubernetes:** `spec/style-guides/HELM.md` — bjw-s/common chart, values.yaml conventions, security patterns, NetworkPolicies, health checks, persistence, Skaffold integration
- **Documentation (MkDocs Material, DE/EN):** `spec/style-guides/DOCS.md` — DE-canonical/EN-mirror pairing, informal "du" voice, admonition conventions (`!!! warning "Noch nicht implementiert"` etc.), REQ-ID visibility rule, end-user/technical audience separation, generated fact tables

These style guides take precedence over general best practices. When existing code conflicts with a style guide, the style guide wins for new code.

## Key Architectural Decisions

These constraints are documented across multiple files and must be respected when implementing:

1. **Strict 5-layer architecture** (NFR-001): Presentation → API → Business Logic → Data Access → Persistence. Frontend CANNOT access databases directly; all communication goes through REST API.

2. **Polyglot persistence**: ArangoDB (primary — documents + graph queries for species relationships, companion planting), TimescaleDB (time-series sensor data with automatic downsampling), Redis (cache + Celery broker).

3. **Hybrid sensor data model** (REQ-005): Four data sources with fallback chain — automatic (IoT/MQTT) → semi-automatic (Home Assistant REST API) → weather API (DWD/OpenWeatherMap/Open-Meteo for outdoor) → manual entry. Data provenance is always tracked.

4. **Plant phase state machine** (REQ-003): Germination → Seedling → Vegetative → Flowering → Harvest. Transitions can be time-based or event-triggered. Each phase has distinct VPD targets, photoperiod settings, and NPK profiles. Perennial mode with seasonal cycles.

5. **Fertilizer mixing order matters** (REQ-004): Mixing sequence is controlled by the `mixing_priority` field on the Fertilizer model — not by hard-coded rules. Default ordering follows the convention "Silicon → CalMag → Base A → Base B → Acids" (CalMag-before-sulfates prevents precipitation), but is fully configurable per fertilizer. EC-net = target EC minus base water EC. Pydantic models enforce that `mixing_priority` is set; the actual sequence emerges from sorting all selected fertilizers by `mixing_priority`. Organic outdoor fertilization with area-based dosing (g/m², L/m²) and soil analysis integration. <!-- W-013 -->

6. **Genetic lineage graph** (REQ-017): `descended_from` edges track parent-child relationships across generations. Supports clones, seed crosses, grafting, division. Graft compatibility checked at genus/family level.

7. **Actuator control loop** (REQ-018): Closes the sensor→actuator loop. Home Assistant/MQTT/manual protocols. Rule-based control with hysteresis. Priority system: manual override > safety rules > sensor rules > schedules. Graceful degradation to fallback tasks on HA outage.

8. **Dual authentication + Service Accounts** (REQ-023): Local accounts (email + bcrypt password) and federated accounts (Google, GitHub, Apple + generic OIDC providers via Authlib). JWT access tokens (15 min) + refresh tokens (30 days, HttpOnly cookie, rotation). Service Accounts (`account_type: 'service'`) for M2M integration (Home Assistant, Grafana, CI/CD) — API-key-only, no interactive login, with IP allowlist and per-account rate limits. Supersedes NFR-001 §6.1.

9. **Multi-tenancy with RBAC Permission Matrix** (REQ-024): Tenant is the isolation container — all resources belong to exactly one tenant. Users can be members of multiple tenants with different roles per tenant (viewer/grower/lead). Assignment-based write control for locations. Platform roles: admin (full KA-Admin) and viewer (read-only admin panel). URL-based routing: `/api/v1/t/{tenant_slug}/...` for tenant-scoped endpoints. Global resources (species, cultivars, IPM data) remain at `/api/v1/...`. Personal tenant auto-created at registration.

    **Enforcement (2026-08-08):** the write gate is wired (#1042) via `require_permission` / `require_tenant_role` / `require_admin_scope` in `src/backend/app/common/auth.py`; delete is lead-only, reads stay open to every member. Full status: `.claude/reference/claude-md-offload.md`.

10. **DSGVO by Design** (REQ-025, NFR-011): All personal data has defined retention periods enforced by Celery. DSGVO subject rights (Art. 15–21) as self-service API at `/api/v1/privacy/`. IP addresses anonymized after 7 days. Sensor data downsampled in 3 stages (90d raw → 2y hourly → 5y daily). Consent-checking middleware for optional processing. Harvest/treatment data anonymized (not deleted) when retention laws (CanG, PflSchG) apply.

11. **Two-tier DAST security testing** (NFR-014, NFR-015): Two complementary scanners are specified. **Nuclei** (NFR-014) provides broad, fast template-based scanning per PR and nightly — covering exposures, misconfigurations, default-logins, CVEs and project-specific custom templates (security-headers, CORS, JWT-leak, source-map, tenant-leak); it uploads SARIF to GitHub Code Scanning. **OWASP ZAP** (NFR-015) is specified for deep behaviour-based scanning: Baseline + API scan per PR, Full-Scan with AjaxSpider and authenticated cross-tenant negative tests nightly. NFR-009 covers dependency CVEs *before* deployment, NFR-014/015 cover the deployed app.

    **Enforcement (2026-08-01):** the Nuclei and ZAP lanes run but are **advisory**, not required checks on `develop`; verify with `gh api repos/nolte/kamerplanter/branches/develop/protection --jq '.required_status_checks.contexts'`. Full status: `.claude/reference/claude-md-offload.md`.

## Tech Stack Summary

Full stack: `spec/stack.md`. Versions: `src/frontend/package.json`, `src/backend/pyproject.toml` — verify there before reasoning about library-specific behaviour.
Backend Python/FastAPI/Celery (ArangoDB, TimescaleDB, Valkey); frontend React 19 + **MUI 9** (not 7: `Drawer` role per variant, `Select` opens on `mousedown` only, click-away guard) — a stale "MUI 7" entry once misled E2E investigations.

## Domain Concepts

- **GDD** — Growing Degree Days: accumulated heat units tracking plant maturity
- **VPD** — Vapor Pressure Deficit: key environmental metric (0.8–1.5 kPa vegetative, 0.8–1.2 kPa flowering)
- **PPFD** — Photosynthetic Photon Flux Density: light intensity measurement
- **EC** — Electrical Conductivity: nutrient solution concentration
- **IPM** — Integrated Pest Management: 3-tier approach (prevention → monitoring → intervention)
- **Karenz period** — mandatory waiting time between chemical treatment and harvest
- **Lineage** — genetic ancestry graph (clone chains, seed crosses, grafts)
- **Hysteresis** — on/off threshold separation preventing actuator oscillation
- **Tenant** — isolation container for multi-user: personal garden, community garden, or commercial operation. All resources scoped to exactly one tenant.
- **Membership** — user-to-tenant relationship with role (admin/grower/viewer). One user can have different roles in different tenants.
- **Retention Policy** — defined data lifecycle per category (NFR-011). Celery master task enforces deletion/anonymization daily. Configurable via environment variables with legal minimum floors.
- **Consent Record** — tracked per user and processing purpose. Required consents (core functionality) cannot be revoked. Optional consents (Sentry, HIBP, enrichment) gate feature access via middleware.
- **DSFA** — Datenschutz-Folgenabschätzung (Data Protection Impact Assessment): required for sensor data that may reveal personal presence patterns (CO2, motion, manual overrides).
- **Fruchtfolge** — Crop rotation: 4-year cycle (Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung) tracked per bed location via CropRotationPlan nodes.
- **Mischkultur** — Companion planting: graph-based compatibility engine recommending beneficial plant combinations for outdoor beds.
- **Sukzession** — Succession sowing: staggered plantings at intervals to extend harvest window, tracked via SuccessionPlan nodes.
- **Winterhärte-Ampel** — Winter hardiness traffic light: 3-tier rating (green=hardy, yellow=needs protection, red=must overwinter indoors) based on frost_sensitivity + climate_zone.
- **Phänologie** — Phenological indicators: natural events (Forsythienblüte, Holunderblüte, Apfelblüte) used as task triggers instead of fixed calendar dates.
- **Überwinterung** — Overwintering management: OverwinteringProfile nodes tracking protection methods, storage conditions, and spring uncovering schedules for perennial and frost-tender plants.
