# Unit-Tests

Unit-Tests prüfen eine **einzelne Funktion oder Klasse in Isolation** — ohne Datenbank, Netzwerk oder Browser. Sie sind die Basis der [Testpyramide](index.md): am zahlreichsten, am schnellsten, am präzisesten in der Fehlermeldung.

## Was diese Stufe prüft

- **Backend-Fachlogik:** reine Berechnungen und Engine-Regeln (VPD nach Tetens, GDD-Akkumulation, EC-Budget), Adapter-Logik (GBIF-/Perenual-Anreicherung).
- **Frontend-Logik ohne DOM:** Redux-Slices (Reducer, Actions) und Custom Hooks, die als reine Funktionen testbar sind.

## Getestete Bereiche im Überblick

| Bereich | Getestete Elemente | Umfang |
|---------|--------------------|--------|
| Domain-Logik (Backend) | VPD-/GDD-/EC-Berechnung, Phasen-Engine, Karenz-Gate, Companion/Fruchtfolge | umfangreich |
| Repositories (Backend) | ArangoDB-Zugriffe, Graph-Queries | umfangreich |
| Migrationen | Schema-Migrations-Framework | umfangreich |
| Celery-Tasks | Hintergrund-Jobs, Retention/Anonymisierung | mittel |
| Adapter | Wetter (DWD/Open-Meteo/OWM/NASA), GBIF, Perenual, PlantNet, Home Assistant, Notifications | mittel |
| Frontend | Redux-Slices, Custom Hooks | mittel |

## Werkzeug & Ort

| | Backend | Frontend |
|---|---|---|
| Werkzeug | pytest (`asyncio_mode = "auto"`) | vitest |
| Ort | `src/backend/tests/unit/` | `src/frontend/src/test/store/`, `…/hooks/` |
| Abhängigkeiten | keine externen | keine (kein Provider-Wrapper nötig) |

## Ausführen

```bash
# Backend
cd src/backend && pytest tests/unit/ -v

# Frontend
cd src/frontend && npm test
```

Die vollständigen Voraussetzungen und Muster stehen im [Testkonzept → Backend-Tests](../index.md#backend-tests-pytest) bzw. [→ Frontend-Tests](../index.md#frontend-tests-vitest).

## Konventionen

- Engine-Tests instanziieren die Klasse direkt und mocken **keine** Repositories.
- Service-Tests mocken das Repository (`AsyncMock(spec=…)`).
- Redux-Slice-Tests laufen ganz ohne React — Reducer als reine Funktion aufrufen.
- Jedes neue Feature braucht mindestens einen Unit-Test für seine Business-Logik.
