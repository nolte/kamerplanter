# Architektur

Kamerplanter folgt einer strikten 5-Schichten-Architektur und nutzt polyglotte Persistenz.

## Architekturüberblick

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

## In diesem Abschnitt

- [Überblick](overview.md) — Schichtenmodell und Designprinzipien
- [Backend](backend.md) — FastAPI, Celery, Domain-Modelle
- [Frontend](frontend.md) — React, Redux, MUI
- [Datenbank](database.md) — ArangoDB Collections und Graph-Schema
- [Infrastruktur](infrastructure.md) — Kubernetes, Helm, Netzwerk
