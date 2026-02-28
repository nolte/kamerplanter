# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

Kamerplanter is an **agricultural technology system** for plant lifecycle management (cannabis, vegetables, herbs). The repository contains both **specification documents** (German) and a **working implementation** (English source code, NFR-003).

Documentation is written in **German**; source code must be in **English only** (NFR-003).

## Repository Structure

- `spec/` — Specification documents
  - `spec/req/` — 25 functional requirements (REQ-001 through REQ-025)
  - `spec/nfr/` — 11 non-functional requirements (NFR-001 through NFR-011)
  - `spec/stack.md` — Complete technology stack specification
- `src/backend/` — Python/FastAPI backend (implemented)
- `src/frontend/` — React/TypeScript frontend (implemented)

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

## Key Architectural Decisions

These constraints are documented across multiple files and must be respected when implementing:

1. **Strict 5-layer architecture** (NFR-001): Presentation → API → Business Logic → Data Access → Persistence. Frontend CANNOT access databases directly; all communication goes through REST API.

2. **Polyglot persistence**: ArangoDB (primary — documents + graph queries for species relationships, companion planting), TimescaleDB (time-series sensor data with automatic downsampling), Redis (cache + Celery broker).

3. **Hybrid sensor data model** (REQ-005): Four data sources with fallback chain — automatic (IoT/MQTT) → semi-automatic (Home Assistant REST API) → weather API (DWD/OpenWeatherMap/Open-Meteo for outdoor) → manual entry. Data provenance is always tracked.

4. **Plant phase state machine** (REQ-003): Germination → Seedling → Vegetative → Flowering → Harvest. Transitions can be time-based or event-triggered. Each phase has distinct VPD targets, photoperiod settings, and NPK profiles. Perennial mode with seasonal cycles.

5. **Fertilizer mixing order matters** (REQ-004): CalMag before sulfates to prevent precipitation. EC-net = target EC minus base water EC. Pydantic models enforce mixing sequence validation. Organic outdoor fertilization with area-based dosing (g/m², L/m²) and soil analysis integration.

6. **Genetic lineage graph** (REQ-017): `descended_from` edges track parent-child relationships across generations. Supports clones, seed crosses, grafting, division. Graft compatibility checked at genus/family level.

7. **Actuator control loop** (REQ-018): Closes the sensor→actuator loop. Home Assistant/MQTT/manual protocols. Rule-based control with hysteresis. Priority system: manual override > safety rules > sensor rules > schedules. Graceful degradation to fallback tasks on HA outage.

8. **Dual authentication** (REQ-023): Local accounts (email + bcrypt password) and federated accounts (Google, GitHub, Apple + generic OIDC providers via Authlib). JWT access tokens (15 min) + refresh tokens (30 days, HttpOnly cookie, rotation). Supersedes NFR-001 §6.1.

9. **Multi-tenancy with tenant-scoped roles** (REQ-024): Tenant is the isolation container — all resources belong to exactly one tenant. Users can be members of multiple tenants with different roles per tenant (admin/grower/viewer). URL-based routing: `/api/v1/t/{tenant_slug}/...` for tenant-scoped endpoints. Global resources (species, cultivars, IPM data) remain at `/api/v1/...`. Personal tenant auto-created at registration.

10. **DSGVO by Design** (REQ-025, NFR-011): All personal data has defined retention periods enforced by Celery. DSGVO subject rights (Art. 15–21) as self-service API at `/api/v1/privacy/`. IP addresses anonymized after 7 days. Sensor data downsampled in 3 stages (90d raw → 2y hourly → 5y daily). Consent-checking middleware for optional processing. Harvest/treatment data anonymized (not deleted) when retention laws (CanG, PflSchG) apply.

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14+, FastAPI >= 0.115, Celery >= 5.4, Authlib (JWT/OAuth2/OIDC) |
| Frontend | React 19, TypeScript 5.9, Redux Toolkit, MUI 7, Vite 6, react-router-dom v7 |
| Mobile | Flutter 3.16+ (not yet implemented) |
| Primary DB | ArangoDB 3.11+ (multi-model) |
| Time-Series DB | TimescaleDB 2.13+ |
| Cache/Queue | Redis 7.2+ |
| Orchestration | Kubernetes 1.28+, Helm, Traefik |
| Code Quality | Ruff (Python); ESLint (TypeScript) |
| Testing | pytest + pytest-asyncio (backend); vitest (frontend) |
| CI/CD | GitHub Actions |

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
