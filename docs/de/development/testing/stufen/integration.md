# Integrationstests

Integrationstests prüfen das **Zusammenspiel mehrerer Bausteine mit echten externen Abhängigkeiten** — vor allem den Datenzugriff gegen eine laufende ArangoDB und das Verhalten der API-Schicht. Sie sitzen in der Mitte der [Testpyramide](index.md): weniger als Unit-Tests, dafür realistischer.

## Was diese Stufe prüft

- **Repository- und Datenbank-Zugriff:** dass Queries, Indizes und der Graph (`kamerplanter_graph`) gegen eine echte ArangoDB-Instanz wie erwartet arbeiten.
- **API-Schicht:** Fehlerbehandlung und Statuscodes der FastAPI-Endpunkte.

## Getestete Bereiche im Überblick

| Bereich | Getestete Elemente | Umfang |
|---------|--------------------|--------|
| API-Schicht (Router) | REST-Endpunkte je Domäne — Dashboard, Nährlösung, Wetter, Datenschutz, Erkennung, Mandanten, Standorte u. v. m. | umfangreich |
| Datenbank-Integration | ArangoDB-Setup, Graph, mehrjähriger Saison-Zyklus | fokussiert |
| Tenant-Isolation | Vermehrung/Lineage über Mandantengrenzen | fokussiert |

## Werkzeug & Ort

| | Wert |
|---|---|
| Werkzeug | pytest |
| Ort | `src/backend/tests/integration/`, `src/backend/tests/api/` |
| Abhängigkeit | laufende ArangoDB-Instanz |

## Ausführen

Integrationstests werden **automatisch übersprungen**, wenn keine Datenbank erreichbar ist (`@pytest.mark.skipif(not ARANGO_AVAILABLE, …)`) — so bleibt die Suite auch ohne DB grün.

```bash
# ArangoDB starten (z. B. via Docker Compose)
docker-compose up -d arangodb

# Nur Integrationstests
cd src/backend && pytest tests/integration/ -v
```

Details im [Testkonzept → Integrationstests](../index.md#integrationstests).

## Konventionen

- Integrationstests dürfen den Zustand der Testdatenbank verändern — sie räumen nach sich auf oder nutzen isolierte Collections.
- In CI laufen sie mit bereitgestellter ArangoDB; lokal ohne DB werden sie sauber übersprungen statt zu scheitern.
