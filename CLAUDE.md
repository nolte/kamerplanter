# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

Kamerplanter is an **agricultural technology system** for plant lifecycle management (cannabis, vegetables, herbs). The repository contains both **specification documents** (German) and a **working implementation** (English source code, NFR-003).

Documentation is written in **German**; source code must be in **English only** (NFR-003).

## Repository Structure

- `spec/` — Specification documents
  - `spec/req/` — 18 functional requirements (REQ-001 through REQ-018)
  - `spec/nfr/` — 10 non-functional requirements (NFR-001 through NFR-010)
  - `spec/stack.md` — Complete technology stack specification
- `src/backend/` — Python/FastAPI backend (implemented)
- `src/frontend/` — React/TypeScript frontend (implemented)

## Requirements Overview

| REQ | Title | Category |
|-----|-------|----------|
| REQ-001 | Stammdatenverwaltung | Stammdaten |
| REQ-002 | Standort & Substrat | Standorte |
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

## Key Architectural Decisions

These constraints are documented across multiple files and must be respected when implementing:

1. **Strict 5-layer architecture** (NFR-001): Presentation → API → Business Logic → Data Access → Persistence. Frontend CANNOT access databases directly; all communication goes through REST API.

2. **Polyglot persistence**: ArangoDB (primary — documents + graph queries for species relationships, companion planting), TimescaleDB (time-series sensor data with automatic downsampling), Redis (cache + Celery broker).

3. **Hybrid sensor data model** (REQ-005): Three data sources with fallback chain — automatic (IoT/MQTT) → semi-automatic (Home Assistant REST API) → manual entry. Data provenance is always tracked.

4. **Plant phase state machine** (REQ-003): Germination → Seedling → Vegetative → Flowering → Harvest. Transitions can be time-based or event-triggered. Each phase has distinct VPD targets, photoperiod settings, and NPK profiles. Perennial mode with seasonal cycles.

5. **Fertilizer mixing order matters** (REQ-004): CalMag before sulfates to prevent precipitation. EC-net = target EC minus base water EC. Pydantic models enforce mixing sequence validation.

6. **Genetic lineage graph** (REQ-017): `descended_from` edges track parent-child relationships across generations. Supports clones, seed crosses, grafting, division. Graft compatibility checked at genus/family level.

7. **Actuator control loop** (REQ-018): Closes the sensor→actuator loop. Home Assistant/MQTT/manual protocols. Rule-based control with hysteresis. Priority system: manual override > safety rules > sensor rules > schedules. Graceful degradation to fallback tasks on HA outage.

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, Celery |
| Frontend | React 18, TypeScript, Redux Toolkit, MUI, Vite |
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
- **VPD** — Vapor Pressure Deficit: key environmental metric (0.8–1.5 kPa vegetative, 0.4–0.8 kPa flowering)
- **PPFD** — Photosynthetic Photon Flux Density: light intensity measurement
- **EC** — Electrical Conductivity: nutrient solution concentration
- **IPM** — Integrated Pest Management: 3-tier approach (prevention → monitoring → intervention)
- **Karenz period** — mandatory waiting time between chemical treatment and harvest
- **Lineage** — genetic ancestry graph (clone chains, seed crosses, grafts)
- **Hysteresis** — on/off threshold separation preventing actuator oscillation
