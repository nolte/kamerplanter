# Unreleased

Changes not yet published in a release.

## Added

### Backend

- **REQ-001** Master data management: Botanical families, species, cultivars, lifecycles (ArangoDB)
- **REQ-002** Site management: Sites, locations (recursive hierarchy), slots, location types
- **REQ-003** Phase control: Phase state machine (germination → harvest), GDD/VPD/photoperiod calculation
- **REQ-004** Fertilization logic: Fertilizers, nutrient plans, dosages, mixing safety, flushing, runoff, EC budget, water source/CalMag correction
- **REQ-006** Task planning: Workflow templates, tasks, queue, dependencies, HST validator
- **REQ-007** Harvest management: Harvest indicators, observations, batches, quality assessment, pre-harvest interval gate
- **REQ-010** IPM system: Pests, diseases, treatments, inspections, resistance manager
- **REQ-011** External master data enrichment: GBIF + Perenual adapters, enrichment engine, Celery tasks
- **REQ-012** Master data import: CSV upload, validation, preview, confirmation
- **REQ-013** Planting runs: PlantingRun, batch operations, state machine
- **REQ-014** Tank management: Tanks, tank states, fills, maintenance, sensors
- **REQ-015** Calendar view: iCal feeds, aggregation, token-based access
- **REQ-019** Substrate management: Extended substrate types, lifecycle manager, reuse
- **REQ-020** Onboarding wizard: 5-step assistant, 9 starter kits, experience levels
- **REQ-022** Care reminders: 9 care profiles, FAMILY_CARE_MAP, adaptive intervals, Celery task
- **REQ-023** Authentication: Local accounts (bcrypt), JWT (authlib), refresh token rotation
- **REQ-024** Multi-tenancy: Tenant isolation, memberships, invitations, RBAC
- **REQ-028** Companion planting: Graph-based compatibility
- **REQ-031** AI assistant: RAG-based knowledge base, LLM adapters (Anthropic/Ollama/OpenAI-compatible), hybrid search

### Frontend

- All REQ-001 through REQ-024 frontend pages implemented
- **REQ-020** Onboarding wizard (5-step MUI Stepper)
- **REQ-021** UI experience levels: Field configuration, navigation tiering, ExperienceLevelSwitcher
- **REQ-022** Care dashboard with urgency grouping
- Light/dark theme with localStorage persistence
- i18n German/English (react-i18next)

### Infrastructure

- MkDocs documentation infrastructure with Material Theme and DE/EN i18n (NFR-005)
- ADR-001 through ADR-006: Architecture decisions documented
- Skaffold-based development workflow with Kubernetes/Helm
- pgvector + embedding service for RAG pipeline
- Knowledge container for YAML-based knowledge base
- GitHub Actions CI/CD (Docker lint/build, Skaffold verify)

## In Development

- REQ-025 (Privacy/GDPR): GDPR Art. 15–21 data subject rights — specified, not implemented
- REQ-027 (Light mode): Anonymous access for local instances — specified, not implemented
- OAuth/OIDC: Full implementation (engine currently stubbed)
- TimescaleDB integration: Repository and migrations in place, feature-flag controlled
