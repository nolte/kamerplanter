# Debugging

Diese Seite beschreibt, wie das Backend und das Frontend in der lokalen Entwicklungsumgebung debuggt werden. Alle Methoden setzen ein laufendes Skaffold-Setup voraus (siehe [Lokales Setup](local-setup.md)).

---

## Backend-Debugging mit debugpy

Das Backend-Container-Image enthält [debugpy](https://github.com/microsoft/debugpy) — den Python-Debugger, den VS Code, PyCharm und andere IDEs für Remote-Debugging verwenden.

### Debug-Modus starten

```bash
skaffold debug --port-forward
```

Das `debug`-Profil in `skaffold.yaml` setzt `DEBUGPY_ENABLED=true` als Docker-Build-Argument. Der Container startet daraufhin debugpy und wartet optional auf eine Verbindung.

Debugpy lauscht auf Port `5678`. Skaffold leitet diesen Port nicht automatisch weiter — das muss manuell eingerichtet werden:

```bash
kubectl port-forward deployment/kamerplanter-backend 5678:5678
```

### VS Code — launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Kamerplanter Backend (Remote)",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/src/backend",
          "remoteRoot": "/app"
        }
      ],
      "justMyCode": true
    }
  ]
}
```

### PyCharm — Remote-Debug-Konfiguration

1. Menü: `Run` → `Edit Configurations` → `+` → `Python Debug Server`
2. Host: `localhost`, Port: `5678`
3. Path Mappings: `src/backend/app` → `/app/app`
4. Konfiguration starten, dann `skaffold debug --port-forward` ausführen

### Breakpoints und Log-Ausgabe

Der Backend-Server läuft mit uvicorn im `--reload`-Modus. Strukturierte Logs werden über [structlog](https://www.structlog.org/) ausgegeben:

```python
import structlog

log = structlog.get_logger()

async def create_species(data: CreateSpeciesRequest) -> Species:
    log.info("creating_species", scientific_name=data.scientific_name)
    # Breakpoint hier setzen
    result = await self.repo.create(data)
    log.info("species_created", key=result.key)
    return result
```

### Pod-Logs einsehen

Ohne Debugger reichen oft die Logs aus:

```bash
# Backend-Logs (letzte 100 Zeilen, dann live folgen)
kubectl logs -l app=kamerplanter-backend --tail=100 -f

# Celery-Worker-Logs
kubectl logs -l app=kamerplanter-worker --tail=100 -f

# Nur Fehler
kubectl logs -l app=kamerplanter-backend --tail=200 | grep '"level":"error"'
```

---

## Frontend-Debugging

### Browser DevTools

Die meisten Frontend-Probleme lassen sich mit den Browser-Entwicklerwerkzeugen lösen:

- **Konsole** (`F12` → Console): JavaScript-Fehler, unbehandelte Promise-Rejections, i18n-Warnungen zu fehlenden Schlüsseln
- **Netzwerk** (`F12` → Network): API-Anfragen, HTTP-Status-Codes, Request/Response-Bodies
- **Redux DevTools**: Redux-Zustandsänderungen nachverfolgen (Erweiterung für Chrome/Firefox erforderlich)

### React Developer Tools

Die [React DevTools](https://react.dev/learn/react-developer-tools) Browser-Erweiterung ermöglicht:
- Komponenten-Baum inspizieren
- Props und State einzelner Komponenten einsehen
- Re-Render-Profiler für Performance-Analyse

### Vite-Quellkarten

Im Entwicklungsmodus (Vite Dev Server, Port `5173`) sind Quellkarten aktiv. Haltepunkte können direkt in TypeScript-Dateien im Browser-Debugger gesetzt werden.

### Häufige Frontend-Probleme

??? question "API-Anfragen schlagen mit 401 fehl"
    Der JWT-Token ist abgelaufen oder der `kp_active_tenant_slug`-Eintrag in `localStorage` fehlt. Im Browser-DevTools unter `Application → Local Storage` prüfen:
    - `kp_active_tenant_slug` muss auf einen gültigen Tenant-Slug gesetzt sein (z. B. `demo`)
    - Den Login-Flow erneut durchlaufen oder den Token manuell löschen und neu anmelden

??? question "i18n-Schlüssel werden als Rohtext angezeigt"
    Fehlende Übersetzungsschlüssel werden in der Konsole als Warnung ausgegeben: `i18next: key "pages.myPage.missingKey" for language "de" not found`. Den Schlüssel in `src/i18n/locales/de/translation.json` und `en/translation.json` ergänzen.

??? question "Redux-State wird nicht aktualisiert"
    Mit Redux DevTools die dispatched Actions und die State-Änderungen prüfen. Häufige Ursachen: falsche Slice-Action exportiert, Immer-Mutation vergessen, `createSelector`-Memo-Problem (unstabile Referenz aus einem Custom Hook ohne `useMemo`).

??? question "MSW-Mocks greifen im Browser nicht"
    Der Mock Service Worker ist nur für Tests aktiv. Im Entwicklungsmodus treffen Anfragen den echten Backend-Proxy unter `/api`. Falls die Backend-API nicht erreichbar ist, den Port-Forward von Skaffold prüfen.

---

## ArangoDB Web-UI

Die ArangoDB-Weboberfläche ist unter [http://localhost:8529](http://localhost:8529) erreichbar:

| Feld | Wert |
|------|------|
| Benutzer | `root` |
| Passwort | `rootpassword` |
| Datenbank | `kamerplanter` |

Nützliche AQL-Abfragen für die Fehlersuche:

```aql
// Alle Pflanzenarten anzeigen
FOR s IN species RETURN s

// Verbindungen eines Mandanten prüfen
FOR v, e IN 1..1 OUTBOUND 'tenants/demo' GRAPH 'kamerplanter_graph'
  RETURN { vertex: v._id, edge: e._from }

// Letzte 10 Aufgaben
FOR t IN tasks
  SORT t.created_at DESC
  LIMIT 10
  RETURN t
```

---

## Celery-Aufgaben debuggen

Für Hintergrundaufgaben (Celery Beat + Worker) sind separate Logs vorhanden:

```bash
# Celery-Worker
kubectl logs -l app=kamerplanter-worker -f

# Celery-Beat (Scheduler)
kubectl logs -l app=kamerplanter-beat -f
```

Eine Aufgabe manuell auslösen (direkter Python-Aufruf im Backend-Pod):

```bash
kubectl exec -it deployment/kamerplanter-backend -- python -c "
from app.tasks.care_reminders import generate_due_care_reminders
result = generate_due_care_reminders.delay()
print('Task ID:', result.id)
"
```

---

## Health-Endpunkte

Das Backend stellt zwei Health-Endpunkte bereit, die auch für manuelle Diagnosen nützlich sind:

```bash
# Liveness (läuft der Prozess?)
curl http://localhost:8000/api/v1/health/live

# Readiness (ist die Datenbank erreichbar?)
curl http://localhost:8000/api/v1/health/ready
```

Erwartete Antwort (beide): `{"status": "ok"}` mit HTTP 200.

---

## Häufige Fehlerszenarien

??? question "Backend-Pod in CrashLoopBackOff"
    1. Logs abrufen: `kubectl logs <pod-name> --previous`
    2. Häufige Ursachen: Pydantic-Validierungsfehler beim Start, fehlende Umgebungsvariable, ArangoDB noch nicht bereit
    3. ArangoDB-Verbindung direkt testen: `kubectl exec -it deployment/kamerplanter-backend -- python -c "from app.data_access.arango.connection import ArangoConnection; from app.config.settings import Settings; c = ArangoConnection(Settings()); c.connect(); print('OK')"`

??? question "Seed-Daten wurden nicht angelegt"
    Die Migration läuft als Init-Container. Logs einsehen:
    ```bash
    kubectl logs <backend-pod-name> -c init-seed
    ```

??? question "Frontend zeigt leere Seite ohne Fehlermeldung"
    Browser-Konsole auf JavaScript-Fehler prüfen. Typische Ursache: eine Redux-Aktion wird mit einem `undefined`-Payload dispatched, was zu einem Reducer-Fehler führt.

## Siehe auch

- [Lokales Setup](local-setup.md)
- [Testen](testing.md)
- [Code-Standards](code-standards.md)
