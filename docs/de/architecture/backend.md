# Backend-Architektur

Das Backend ist in Python 3.14+ mit FastAPI implementiert und folgt einer Domain-Driven-Design-Struktur.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Verzeichnisstruktur

```
src/backend/app/
├── api/v1/          # FastAPI Router (Endpunkte)
├── domain/
│   ├── models/      # Pydantic v2 Datenmodelle
│   ├── engines/     # Pure Business Logic
│   ├── services/    # Orchestrierung (Services + Engines)
│   └── interfaces/  # Repository-Interfaces (ABCs)
├── data_access/
│   └── arango/      # ArangoDB Repository-Implementierungen
├── migrations/      # Seed-Daten
└── tasks/           # Celery Background-Tasks
```
