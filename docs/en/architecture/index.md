# Architecture

Kamerplanter follows a strict 5-layer architecture with polyglot persistence.

## Architecture overview

<!-- diagram-source: user-described — high-level 5-layer architecture: client -> API -> business logic -> polyglot persistence -->
```mermaid
flowchart TB
    subgraph "Client Layer"
        Web["Web App (React 19)"]
    end

    subgraph "API Layer"
        FastAPI["FastAPI Backend"]
        Traefik["Traefik Ingress"]
    end

    subgraph "Business Logic"
        Services["Domain Services"]
        Engines["Domain Engines"]
    end

    subgraph "Data Layer"
        ArangoDB[("ArangoDB<br/>Documents + Graph")]
        Valkey[("Valkey<br/>Cache + Broker")]
        TimescaleDB[("TimescaleDB<br/>Time-series")]
    end

    Web --> Traefik
    Traefik --> FastAPI
    FastAPI --> Services
    Services --> Engines
    Services --> ArangoDB
    Services --> Valkey
    Services --> TimescaleDB
```

## In This Section

- [Overview](overview.md) — Layer model and design principles
- [Backend](backend.md) — FastAPI, Celery, domain models
- [Frontend](frontend.md) — React, Redux, MUI
- [Database](database.md) — ArangoDB collections and graph schema
- [Infrastructure](infrastructure.md) — Kubernetes, Helm, networking
