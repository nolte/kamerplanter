# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a **specification-only repository** containing comprehensive requirements and architecture documentation for the Kamerplanter project — an agricultural technology system for plant lifecycle management (cannabis, vegetables, herbs). There is no source code, no build system, and no runnable application here. All documents describe a system to be built.

Documentation is written in **German**; source code (when implemented) must be in **English only** (NFR-003).

## Repository Structure

- `stack.md` — Complete technology stack specification (Python/FastAPI backend, React/TypeScript frontend, Flutter mobile, ArangoDB + TimescaleDB + Redis)
- `fachanforderungen/` — 10 functional requirements documents (REQ-001 through REQ-010)
- `nfr/` — 3 non-functional requirements (architecture separation, Kubernetes deployment, code quality)

## Key Architectural Decisions

These constraints are documented across multiple files and must be respected when implementing:

1. **Strict 5-layer architecture** (NFR-001): Presentation → API → Business Logic → Data Access → Persistence. Frontend CANNOT access databases directly; all communication goes through REST API.

2. **Polyglot persistence**: ArangoDB (primary — documents + graph queries for species relationships, companion planting), TimescaleDB (time-series sensor data with automatic downsampling), Redis (cache + Celery broker).

3. **Hybrid sensor data model** (REQ-005): Three data sources with fallback chain — automatic (IoT/MQTT) → semi-automatic (Home Assistant REST API) → manual entry. Data provenance is always tracked.

4. **Plant phase state machine** (REQ-003): Germination → Seedling → Vegetative → Flowering → Harvest. Transitions can be time-based or event-triggered. Each phase has distinct VPD targets, photoperiod settings, and NPK profiles.

5. **Fertilizer mixing order matters** (REQ-004): CalMag before sulfates to prevent precipitation. EC-net = target EC minus base water EC. Pydantic models enforce mixing sequence validation.

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, Celery |
| Frontend | React 18, TypeScript, Redux Toolkit, MUI, Vite |
| Mobile | Flutter 3.16+ |
| Primary DB | ArangoDB 3.11+ (multi-model) |
| Time-Series DB | TimescaleDB 2.13+ |
| Cache/Queue | Redis 7.2+ |
| Orchestration | Kubernetes 1.28+, Helm, Traefik |
| Code Quality | Ruff, Black, mypy (Python); ESLint (TypeScript) |
| Testing | pytest + pytest-asyncio (backend); vitest (frontend) |
| CI/CD | GitHub Actions |

## Domain Concepts

- **GDD** — Growing Degree Days: accumulated heat units tracking plant maturity
- **VPD** — Vapor Pressure Deficit: key environmental metric (0.8–1.5 kPa vegetative, 0.4–0.8 kPa flowering)
- **PPFD** — Photosynthetic Photon Flux Density: light intensity measurement
- **EC** — Electrical Conductivity: nutrient solution concentration
- **IPM** — Integrated Pest Management: 3-tier approach (prevention → monitoring → intervention)
- **Karency period** — mandatory waiting time between chemical treatment and harvest
