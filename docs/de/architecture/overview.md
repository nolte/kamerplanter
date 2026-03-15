# Architektur-Überblick

Kamerplanter folgt einer strikten 5-Schichten-Architektur (NFR-001). Das Frontend kommuniziert ausschließlich über die REST-API mit dem Backend — direkter Datenbankzugriff vom Frontend ist nicht erlaubt.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Schichten

| Schicht | Technologie | Beschreibung |
|---------|------------|-------------|
| Präsentation | React 19, MUI 7 | UI, Redux State, react-router-dom v7 |
| API | FastAPI >= 0.115 | REST-Endpunkte, JWT-Auth, OpenAPI |
| Business Logic | Python Services + Engines | Domain-Logik, Berechnungen |
| Data Access | python-arango, Repositories | Abstraktion über Datenbankzugriff |
| Persistenz | ArangoDB, TimescaleDB, Redis | Speicherung |
