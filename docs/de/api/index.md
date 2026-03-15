# API-Dokumentation

Die Kamerplanter REST-API folgt OpenAPI 3.0. Alle Endpunkte sind unter `/api/v1/` verfügbar. Mandanten-spezifische Endpunkte verwenden `/api/v1/t/{tenant_slug}/`.

## Interaktive API-Docs (mit laufendem Backend)

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## In diesem Abschnitt

- [Überblick](overview.md) — Basis-URL, Paginierung, Fehlerformat
- [Authentifizierung](authentication.md) — JWT, OAuth2/OIDC
- [Fehlerbehandlung](error-handling.md) — HTTP-Statuscodes, Error-Schema
