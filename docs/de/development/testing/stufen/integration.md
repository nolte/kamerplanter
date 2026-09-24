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

Diese Stufe braucht eine Datenbank, und das Fehlen einer solchen wird **nicht** weggeschwiegen: In CI scheitert der Lauf mit der versuchten Verbindungsadresse, lokal wird mit demselben Grund übersprungen — und weil das Target den Skip-Floor `--max-skipped 0` deklariert, ist auch dieser Skip rot.

```bash
# ArangoDB starten (Dev-Stack oder ein Wegwerf-Container)
task dev:core
# oder:
docker run -d --rm --name kp-it-arango -p 127.0.0.1:8529:8529 \
  -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12

# Nur Integrationstests — dieselbe Invocation wie in CI
task test:backend:integration
```

Details im [Testkonzept → Integrationstests](../index.md#integrationstests).

## Konventionen

- Integrationstests dürfen den Zustand der Testdatenbank verändern — sie räumen nach sich auf oder nutzen isolierte Collections.
- In CI laufen sie gegen einen ArangoDB-Service-Container; ohne Datenbank scheitert der Lauf dort bewusst, statt grün zu melden.
- Die Verbindung wird **einmal** zentral geprüft (`tests/integration/conftest.py`, Session-Fixture `arango_db`); ein Modul hängt sich mit `pytestmark = pytest.mark.usefixtures("arango_db")` daran und bringt keine eigene Probe mit.
- Die Adresse steht in keinem Modul fest: `ARANGODB_HOST` / `ARANGODB_PORT` / `ARANGODB_USERNAME` / `ARANGODB_PASSWORD` zeigen die Stufe auf einen beliebigen Server.
