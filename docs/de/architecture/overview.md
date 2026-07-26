# Architektur-Überblick

Kamerplanter ist eine agrotech-orientierte Plattform für das Pflanzenwachstums-Management. Die Architektur ist auf Erweiterbarkeit, Datensicherheit und klare Verantwortlichkeitstrennung ausgelegt. Dieses Dokument beschreibt das Gesamtbild — die Detailseiten gehen auf die einzelnen Schichten ein.

---

## 5-Schichten-Architektur (NFR-001)

Das System folgt einer strikten 5-Schichten-Architektur. Jede Schicht kennt nur die direkt darunter liegende — überspringende Aufrufe sind nicht erlaubt. Das Frontend greift **niemals** direkt auf die Datenbank zu.

<!-- diagram-source: user-described — strict 5-layer architecture (NFR-001): presentation -> API -> business logic -> data access -> persistence -->
```mermaid
flowchart TB
    subgraph "Layer 1 — Presentation"
        Web["Web App (React 19 + MUI 9)"]
        Mobile["Mobile App (Flutter — planned)"]
    end

    subgraph "Layer 2 — API"
        GW["Traefik Ingress"]
        API["FastAPI Backend<br/>/api/v1/..."]
    end

    subgraph "Layer 3 — Business Logic"
        SVC["Services<br/>(orchestration)"]
        ENG["Engines<br/>(pure domain logic)"]
    end

    subgraph "Layer 4 — Data Access"
        REPO["Repositories<br/>(python-arango)"]
        EXT["External Adapters<br/>(GBIF, Perenual)"]
    end

    subgraph "Layer 5 — Persistence"
        ARANGO[("ArangoDB<br/>Documents + Graph")]
        TSDB[("TimescaleDB<br/>Time-series data")]
        VALKEY[("Valkey<br/>Cache + Broker")]
    end

    Web -- HTTPS --> GW
    Mobile -- HTTPS --> GW
    GW --> API
    API --> SVC
    SVC --> ENG
    SVC --> REPO
    REPO --> ARANGO
    REPO -.-> TSDB
    API --> VALKEY
    EXT --> ARANGO
```

## Laufzeitkomponenten

| Komponente | Technologie | Aufgabe |
|-----------|------------|---------|
| Web-App | React 19, TypeScript 6, MUI 9 | Benutzeroberfläche |
| Backend API | Python 3.14+, FastAPI >= 0.115 | REST-Endpunkte, JWT-Auth, OpenAPI |
| Celery Worker | Celery >= 5.4 | Hintergrundaufgaben (Anreicherung, Erinnerungen) |
| Celery Beat | Celery Beat | Zeitgesteuerte Aufgaben (täglich, stündlich) |
| ArangoDB | ArangoDB 3.11+ | Primäre Datenbank — Dokumente und Graph |
| TimescaleDB | TimescaleDB 2.13+ | Sensordaten (Zeitreihen, optional) |
| Valkey | Valkey 8 (Redis-kompatibel) | Celery-Broker + Cache |
| Traefik | Traefik Ingress | TLS-Terminierung, Routing |

## Deployment-Varianten

### Kubernetes (Produktion)

Container-Images aus `ghcr.io/nolte/kamerplanter-{backend,frontend}`, deployt via Helm-Chart auf Basis der [bjw-s common library](https://bjw-s-helm-charts.pages.dev/docs/common-library/). Der Chart liegt unter `helm/kamerplanter/`.

### Docker Compose (einfacher Start)

Für schnelle lokale Instanzen ohne Kubernetes. Alle Dienste in einer `docker-compose.yml` — ideal für Demos und Evaluierung.

### Skaffold + Kind (Entwicklung)

Der primäre Entwicklungsworkflow. Skaffold übernimmt Image-Building, Hot-Reload via Datei-Sync und Deployment in einen lokalen Kind-Cluster. Kein manuelles `kubectl apply` nötig.

## Authentifizierung & Multi-Tenancy

Kamerplanter unterstützt mehrere Betriebsmodi:

- **Full-Modus**: Vollständige Auth mit JWT-Tokens (15 min Ablauf), HttpOnly-Cookie für Refresh-Token (30 Tage). Lokale Accounts (bcrypt) und federated Login (OIDC). Multi-Tenant-Routing unter `/api/v1/t/{tenant_slug}/`.
- **Light-Modus** (REQ-027): Für lokale Einzelinstallationen ohne Auth-Overhead. Ein Platform-Tenant wird automatisch erstellt.

## Betriebsmodi-Schalter

Der Modus wird über die Umgebungsvariable `KAMERPLANTER_MODE` gesteuert:

```
KAMERPLANTER_MODE=light   # Anonymer Zugang, kein Login
KAMERPLANTER_MODE=full    # Vollständige Auth (Standard)
```

## Externe Integrationen

<!-- diagram-source: user-described — external integrations: enrichment (GBIF, Perenual) and Home Assistant (sensors, weather) -->
```mermaid
flowchart LR
    subgraph "Kamerplanter"
        ENR["Enrichment Engine"]
        HA["HA Integration<br/>(custom component)"]
    end

    subgraph "External services"
        GBIF["GBIF API<br/>Plant taxonomy"]
        PER["Perenual API<br/>Care data"]
        HASS["Home Assistant<br/>Sensors / actuators"]
        DWD["DWD / Open-Meteo<br/>Weather data"]
    end

    ENR --> GBIF
    ENR --> PER
    HA <--> HASS
    HASS --> DWD
```

## Siehe auch

- [Backend-Architektur](backend.md) — Schichtenaufbau, Engines, Celery
- [Frontend-Architektur](frontend.md) — React, Redux, Routing
- [Datenbankarchitektur](database.md) — ArangoDB-Graph, Polyglot Persistence
- [Infrastruktur](infrastructure.md) — Kubernetes, Helm, Skaffold, CI/CD
