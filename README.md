# Kamerplanter

Kamerplanter is a plant lifecycle management system for indoor and outdoor growing — covering everything from seed to harvest. It supports vegetables, herbs, houseplants, and ornamentals with features like nutrient planning, phase tracking, sensor integration, and care reminders.

**This project started as a vibe coding experiment** — built almost entirely through conversational AI prompting with Claude Code. The specifications, architecture, domain models, backend, frontend, Helm charts, and tests were all developed in this style. What began as an exploration of AI-assisted development grew into a fully functional agricultural management platform.

## Features

- **Plant Master Data** — Species, cultivars, botanical families with companion planting and crop rotation graphs
- **Growth Phase Tracking** — State machine (Germination > Seedling > Vegetative > Flowering > Harvest) with GDD, VPD, and photoperiod targets
- **Nutrient Planning** — Fertilizer mixing with EC budgets, mixing order safety, flush protocols, and runoff analysis
- **Tank Management** — Water source configuration (tap/RO/mixed), tank state tracking, and automated dosage calculation
- **Planting Runs** — Batch management for plant groups with lifecycle tracking
- **Care Reminders** — Adaptive watering/feeding schedules with 9 care presets, seasonal awareness, and learning from confirmations
- **Task & Workflow Engine** — Template-based task generation with dependency resolution
- **IPM (Pest Management)** — Integrated pest/disease tracking with Karenz safety intervals blocking harvest
- **Harvest Management** — Quality scoring, yield metrics, and harvest readiness indicators
- **Calendar** — Aggregated view of tasks, phases, and events with iCal export (RFC 5545)
- **Sowing Calendar** — Frost-date-aware planting windows for outdoor growing
- **Onboarding Wizard** — 5-step setup with 9 starter kits for quick start
- **Experience Levels** — UI adapts complexity (beginner/intermediate/expert)
- **Multi-Tenancy** — Personal gardens, community gardens, and commercial operations with role-based access
- **Authentication** — Local accounts + OAuth2/OIDC federation (Google, GitHub, Apple)
- **i18n** — German and English, with German as default

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.14+, FastAPI, Celery, Authlib |
| Frontend | React 19, TypeScript 5.9, MUI 7, Redux Toolkit, Vite 6 |
| Primary DB | ArangoDB 3.11+ (documents + graph) |
| Time-Series DB | TimescaleDB 2.13+ (planned) |
| Cache / Queue | Redis 7.2+ |
| Orchestration | Kubernetes, Helm, Skaffold |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose — for the simple setup
- [Skaffold](https://skaffold.dev/) + a local Kubernetes cluster (e.g. minikube, k3s, Docker Desktop) — for the full dev workflow
- Node.js 25+ (managed via [asdf](https://asdf-vm.com/)) — for frontend development
- Python 3.14+ — for backend development

## Quick Start (Docker Compose)

The fastest way to get everything running:

```bash
docker compose up --build
```

This starts:
- **ArangoDB** on `localhost:8529` (root / `rootpassword`)
- **Redis** on `localhost:6379`
- **Backend API** on `localhost:8000`
- **Frontend** on `localhost:8080`

The backend auto-creates the database, collections, and seeds demo data on first startup.

**Demo login:** `demo@kamerplanter.local` / `demo-passwort-2024`

## Development Setup (Skaffold + Kubernetes)

Skaffold is the primary development tool — it handles building, deploying, and hot-reloading:

```bash
# Full stack (manual trigger — rebuild only when you press 'r')
skaffold dev --trigger=manual --port-forward

# Backend only
skaffold dev --trigger=manual --port-forward -p backend-only

# Frontend only
skaffold dev --trigger=manual --port-forward -p frontend-only

# With debugpy enabled
skaffold debug --port-forward
```

Port forwards are configured automatically:

| Service | Local Port |
|---------|-----------|
| Frontend | 3000 |
| Backend API | 8000 |
| ArangoDB UI | 8529 |
| Home Assistant | 8123 |

## Running Tests

```bash
# Backend (pytest)
cd src/backend
pip install -r requirements-dev.txt
pytest

# Frontend (vitest)
cd src/frontend
npm install
npm test
```

## Project Structure

```
kamerplanter/
  spec/               # Specifications (German)
    req/              # 25 functional requirements (REQ-001 to REQ-027)
    nfr/              # 11 non-functional requirements
    stack.md          # Technology stack specification
  src/
    backend/          # Python/FastAPI backend
      app/
        api/v1/       # REST API routers
        domain/       # Business logic (models, engines, services)
        data_access/  # Repository implementations (ArangoDB)
        migrations/   # Seed data and schema migrations
        tasks/        # Celery background tasks
      tests/          # pytest test suite
    frontend/         # React/TypeScript frontend
      src/
        api/          # API client and types
        pages/        # Feature pages
        components/   # Shared components
        store/        # Redux slices
        i18n/         # Translations (de/en)
  helm/               # Helm charts (backend, frontend, ArangoDB)
  deploy/             # Kubernetes manifests
  docker-compose.yml  # Simple local setup
  skaffold.yaml       # Dev workflow orchestration
```

## Architecture

The system follows a strict 5-layer architecture:

```
Frontend (React) --> REST API (FastAPI) --> Services --> Engines --> Repositories --> ArangoDB
```

- **Engines** contain pure business logic (nutrient calculations, phase transitions, VPD formulas)
- **Services** orchestrate engines and repositories
- **Repositories** abstract database access behind interfaces
- ArangoDB serves as a multi-model database — documents for entities, graphs for relationships (companion planting, genetic lineage, crop rotation)

## API Documentation

With the backend running, interactive API docs are available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

This project is not yet licensed. All rights reserved.
