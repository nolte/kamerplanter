# Architektur-Überblick

Kamerplanter ist eine agrotech-orientierte Plattform für das Pflanzenwachstums-Management. Die Architektur ist auf Erweiterbarkeit, Datensicherheit und klare Verantwortlichkeitstrennung ausgelegt. Dieses Dokument beschreibt das Gesamtbild — die Detailseiten gehen auf die einzelnen Schichten ein.

---

## 5-Schichten-Architektur (NFR-001)

Das System folgt einer strikten 5-Schichten-Architektur. Jede Schicht kennt nur die direkt darunter liegende — überspringende Aufrufe sind nicht erlaubt. Das Frontend greift **niemals** direkt auf die Datenbank zu.

```mermaid
graph TB
    subgraph "Schicht 1 — Präsentation"
        Web["Web App (React 19 + MUI 7)"]
        Mobile["Mobile App (Flutter — geplant)"]
    end

    subgraph "Schicht 2 — API"
        GW["Traefik Ingress"]
        API["FastAPI Backend\n/api/v1/..."]
    end

    subgraph "Schicht 3 — Business Logic"
        SVC["Services\n(Orchestrierung)"]
        ENG["Engines\n(reine Domänenlogik)"]
    end

    subgraph "Schicht 4 — Data Access"
        REPO["Repositories\n(python-arango)"]
        EXT["External Adapters\n(GBIF, Perenual)"]
    end

    subgraph "Schicht 5 — Persistenz"
        ARANGO[("ArangoDB\nDokumente + Graph")]
        TSDB[("TimescaleDB\nZeitreihendaten")]
        VALKEY[("Valkey\nCache + Broker")]
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
| Web-App | React 19, TypeScript 5.9, MUI 7 | Benutzeroberfläche |
| Backend API | Python 3.14+, FastAPI >= 0.115 | REST-Endpunkte, JWT-Auth, OpenAPI |
| Celery Worker | Celery >= 5.4 | Hintergrundaufgaben (Anreicherung, Erinnerungen) |
| Celery Beat | Celery Beat | Zeitgesteuerte Aufgaben (täglich, stündlich) |
| ArangoDB | ArangoDB 3.11+ | Primäre Datenbank — Dokumente und Graph |
| TimescaleDB | TimescaleDB 2.13+ | Sensordaten (Zeitreihen, künftig) |
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

```mermaid
graph LR
    subgraph "Kamerplanter"
        ENR["Enrichment Engine"]
        HA["HA-Integration\n(Custom Component)"]
    end

    subgraph "Externe Dienste"
        GBIF["GBIF API\nPflanzentaxonomie"]
        PER["Perenual API\nPflegedaten"]
        HASS["Home Assistant\nSensorik / Aktoren"]
        DWD["DWD / Open-Meteo\nWetterdaten"]
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
