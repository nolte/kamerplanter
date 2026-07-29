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

A notebook crash, terminal close, or session expiry does **not** destroy
in-flight work — Claude Code persists every top-level session transcript under
`~/.claude/projects/<encoded-cwd>/`. To get back to an interrupted run:

```bash
task resume          # list this working copy's resumable sessions, newest first
claude --continue    # resume the most recent
claude --resume <id> # resume a specific one
```

Two things are **not** recoverable with `claude --resume`, which is why long or
autonomous work must be a top-level session:

- **Dispatched worktree-isolated subagents** — their transcript lives under the
  parent session, not as a standalone session.
- **`Workflow` runs** — resumable only via `Workflow({resumeFromRunId})` from
  inside the parent session; never via `claude --resume`.

A real loss happened this way: the `nfr-lektorat` Workflow run on 2026-06-11
executed inside a worktree nested under `.claude/worktrees/`, whose top-level
transcript was gone after the crash. (Its output had already been merged via
PR #166, so nothing was actually lost that time — but the session was not
resumable.)

**Rule:** run long feature work as a top-level session inside a worktree created
under the centralised worktree root, never from a harness worktree under
`.claude/worktrees/`:

```bash
# from the primary checkout:
task worktree:add -- feat/<branch>        # creates it off origin/develop
cd ${NOLTE_WORKTREE_ROOT:-~/repos/.worktrees}/kamerplanter/<slug>
claude                                     # a top-level, --resume-able session
```

The `guard-nested-worktree` pre-commit hook enforces this by rejecting any
commit made from a worktree under `.claude/worktrees/`.

## Claude Code plugin adoption

kamerplanter is migrating its generic delivery / software-engineering
capabilities to the shared **`nolte-shared`** + **`nolte-engineering`** portfolio
plugins, keeping only its **domain-specialised** assets (plant-profile /
"Steckbrief" capture, agrobiology, horticulture/lifecycle, Home-Assistant
integration, RAG/knowledge) under `.claude/`. Generic capabilities (test-case
extraction, E2E generation, quality gate, PR flow, spec/roadmap tooling, …) come
from the plugins, not from local copies.

**Launch Claude Code with the plugins loaded:**

```bash
task claude                 # → claude --plugin-dir <claude-shared> --plugin-dir <…>/plugins/nolte-engineering
task claude -- --resume     # extra args are forwarded
```

The plugins are consumed from a **local checkout of `nolte/claude-shared`** via
`--plugin-dir` (a runtime launch flag — it does **not** appear in
`.claude/settings.json` / `enabledPlugins`). The target resolves the checkout at
`~/repos/github/claude-shared`; override with the `NOLTE_CLAUDE_SHARED`
environment variable if yours lives elsewhere. `nolte-media` is intentionally
**not** loaded (kamerplanter's image-domain `gemini-graphic-prompt-generator`
stays local for now).

**Rules for this adoption:**

- **No copies (DRY):** never copy a plugin-owned skill/agent into `.claude/`.
  Adoption is by plugin consumption; retiring a local asset means *removing* it,
  not re-vendoring it.
- **Verify before remove:** delete a local asset only after its plugin pendant is
  confirmed present at runtime **and** behaviour parity is checked on a real input.
- **Domain assets stay local.** Only genuine plant/HA/agrobiology/RAG assets have
  no portfolio pendant; leave them untouched.

## Requirements Overview

| REQ | Title | Category |
|-----|-------|----------|
| REQ-001 | Stammdatenverwaltung | Stammdaten |
| REQ-002 | Standortverwaltung | Standorte |
| REQ-003 | Phasensteuerung | Wachstumslogik |
| REQ-004 | Dünge-Logik | Bewässerung & Düngung |
| REQ-005 | Hybrid-Sensorik | Monitoring |
| REQ-006 | Aufgabenplanung | Workflow |
| REQ-007 | Erntemanagement | Ernte |
| REQ-008 | Post-Harvest | Nacherntebehandlung |
| REQ-009 | Dashboard | Visualisierung |
| REQ-010 | IPM-System | Pflanzenschutz |
| REQ-011 | Externe Stammdatenanreicherung | Integration |
| REQ-012 | Stammdaten-Import | Import |
| REQ-013 | Pflanzdurchlauf | Gruppenmanagement |
| REQ-014 | Tankmanagement | Bewässerung & Düngung |
| REQ-015 | Kalenderansicht | Visualisierung |
| REQ-016 | InvenTree-Integration (optional) | Integration |
| REQ-017 | Vermehrungsmanagement | Pflanzenvermehrung |
| REQ-018 | Umgebungssteuerung & Aktorik | Automatisierung |
| REQ-019 | Substratverwaltung | Infrastruktur |
| REQ-020 | Onboarding-Wizard | Benutzerführung |
| REQ-021 | UI-Erfahrungsstufen | Benutzerführung |
| REQ-022 | Pflegeerinnerungen | Pflege & Erinnerungen |
| REQ-023 | Benutzerverwaltung & Authentifizierung | Plattform & Sicherheit |
| REQ-024 | Mandantenverwaltung & Gemeinschaftsgärten | Plattform & Kollaboration |
| REQ-025 | Datenschutz & Betroffenenrechte (DSGVO) | Plattform & Datenschutz |
| REQ-027 | Light-Modus (Anonymer Zugang) | Plattform & Deployment |
| REQ-028 | Mischkultur & Companion Planting | Pflanzenplanung |
| REQ-032 | Druckansichten & Export | Ausgabe & Dokumentation |

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

9. **Multi-tenancy with RBAC Permission Matrix** (REQ-024): Tenant is the isolation container — all resources belong to exactly one tenant. Users can be members of multiple tenants with different roles per tenant (admin/grower/viewer). Granular Permission Matrix defines CRUD rights per resource type and role. Assignment-based write control for locations. Platform roles: admin (full KA-Admin) and viewer (read-only admin panel). `require_permission()` FastAPI dependency. URL-based routing: `/api/v1/t/{tenant_slug}/...` for tenant-scoped endpoints. Global resources (species, cultivars, IPM data) remain at `/api/v1/...`. Personal tenant auto-created at registration.

10. **DSGVO by Design** (REQ-025, NFR-011): All personal data has defined retention periods enforced by Celery. DSGVO subject rights (Art. 15–21) as self-service API at `/api/v1/privacy/`. IP addresses anonymized after 7 days. Sensor data downsampled in 3 stages (90d raw → 2y hourly → 5y daily). Consent-checking middleware for optional processing. Harvest/treatment data anonymized (not deleted) when retention laws (CanG, PflSchG) apply.

11. **Two-tier DAST security testing** (NFR-014, NFR-015): Two complementary scanners run in CI. **Nuclei** (NFR-014) provides broad, fast template-based scanning per PR (< 15 min) and nightly — covering exposures, misconfigurations, default-logins, CVEs and project-specific custom templates (security-headers, CORS, JWT-leak, source-map, tenant-leak). **OWASP ZAP** (NFR-015) provides deep verhaltensbasierte scanning: Baseline + API-Scan per PR, Full-Scan with AjaxSpider and authenticated cross-tenant negative tests nightly (≤ 6 h). Both upload SARIF to GitHub Code Scanning. High/Critical findings block PR merge; cross-tenant findings always block. NFR-009 covers dependency CVEs *before* deployment, NFR-014/015 cover the deployed app.

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14+, FastAPI >= 0.115, Celery >= 5.4, Authlib (JWT/OAuth2/OIDC) |
| Frontend | React 19, TypeScript 6, Redux Toolkit, MUI 9, Vite 8, react-router-dom v7 |
| Mobile | Flutter 3.16+ (not yet implemented) |
| Primary DB | ArangoDB 3.11+ (multi-model) |
| Time-Series DB | TimescaleDB 2.13+ |
| Cache/Queue | Valkey 8.0+ (Redis-Wire-Protokoll-kompatibel; `redis-py` als Client) |
| Orchestration | Kubernetes 1.28+, Helm, Traefik |
| Code Quality | Ruff (Python); ESLint (TypeScript) |
| Testing | pytest + pytest-asyncio (backend); vitest (frontend) |
| CI/CD | GitHub Actions |

> **This table is a summary, not the source of truth.** Verify a frontend version
> against `src/frontend/package.json` and a backend one against
> `src/backend/pyproject.toml` before reasoning about library-specific behaviour.
> The frontend runs **MUI 9**, whose DOM/interaction details differ materially
> from MUI 7 (role assignment per `Drawer` variant, `Select` opening on
> `mousedown` only, the click-away guard) — an earlier stale "MUI 7" entry here
> misled several E2E investigations.

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
