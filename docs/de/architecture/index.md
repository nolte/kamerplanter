# Architektur

Kamerplanter folgt einer strikten 5-Schichten-Architektur und nutzt polyglotte Persistenz.

## Architekturüberblick

```mermaid
graph TB
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
        ArangoDB[("ArangoDB\n(Dokumente + Graph)")]
        Redis[("Redis\n(Cache + Queue)")]
        TimescaleDB[("TimescaleDB\n(Zeitreihen)")]
    end

    Web --> Traefik
    Traefik --> FastAPI
    FastAPI --> Services
    Services --> Engines
    Services --> ArangoDB
    Services --> Redis
    Services --> TimescaleDB
```

## In diesem Abschnitt

- [Überblick](overview.md) — Schichtenmodell und Designprinzipien
- [Backend](backend.md) — FastAPI, Celery, Domain-Modelle
- [Frontend](frontend.md) — React, Redux, MUI
- [Datenbank](database.md) — ArangoDB Collections und Graph-Schema
- [Infrastruktur](infrastructure.md) — Kubernetes, Helm, Netzwerk
