# Fehler-Tracking (optional)

Ohne Fehler-Tracking erfährst du von einem Laufzeitfehler nur, wenn jemand die Container-Logs öffnet, weiß wonach er sucht und den Fehlerhergang aus verstreuten Zeilen rekonstruiert. Ein Fehler-Tracker dreht das um: die Anwendung meldet jeden nicht abgefangenen Fehler mitsamt Stacktrace, Anfrage-Kontext, Release und Umgebung, gruppiert wiederkehrende Ereignisse zu einem Vorgang und meldet sich, wenn ein bereits behobener Fehler in einem späteren Release zurückkehrt.

Kamerplanter ist dafür **vorbereitet, aber standardmäßig aus**. Ohne konfigurierte DSN passiert exakt nichts: Das Python-SDK wird nie initialisiert, und das Frontend lädt sein SDK-Bündel nicht einmal herunter. Du musst also nichts abschalten, wenn du keinen Tracker betreibst.

!!! warning "Noch nicht implementiert"
    Diese Seite beschreibt die **Anwendungsseite**. Das Bereitstellen und Betreiben einer GlitchTip-Instanz ist nicht Teil dieses Projekts und noch nicht dokumentiert.

---

## Was du brauchst

Einen Tracker, der das Sentry-Protokoll spricht. Die Referenz ist [GlitchTip](https://glitchtip.com/) (quelloffen, selbst hostbar), aber nichts im Code bindet daran — Sentry selbst oder ein kompatibler Tracker funktioniert genauso. Ein Wechsel ist eine Änderung der DSN, keine Code-Änderung.

## Einschalten

Alle vier Werte kommen aus der Umgebung, in Docker Compose aus deiner `.env`:

```bash
SENTRY_DSN=https://<public-key>@glitchtip.example.org/1
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=v1.4.2
SENTRY_SAMPLE_RATE=1.0
```

Die DSN enthält nur einen öffentlichen Ingest-Schlüssel, kein Geheimnis — sie darf im Frontend landen, denn genau dort wird sie gebraucht.

Unter Kubernetes setzt du dieselben Werte in den Helm-Values. Sie stehen bei `backend`, `celery-worker`, `celery-beat`, `inference-service` und — zweimal — beim `frontend`: einmal im Init-Container, der `runtime-config.js` schreibt, und einmal am nginx-Container, der daraus die Content-Security-Policy anpasst.

!!! danger "NetworkPolicy: ein selbst gehosteter Tracker ist zunächst nicht erreichbar"
    Die Egress-Regel des Backends erlaubt ausgehende Verbindungen ins Internet, **schließt die privaten Adressbereiche aber ausdrücklich aus** (RFC 1918, plus der Link-Local-Bereich). Läuft dein Tracker im selben Cluster oder im LAN, brauchst du eine zusätzliche Egress-Regel für ihn. Ohne sie werden die Ereignisse verworfen, ohne dass irgendwo eine Fehlermeldung erscheint — das SDK meldet eine blockierte Verbindung nicht. Das Einschalten sind also zwei Änderungen, nicht eine.

---

## Die Umgebungen

Der Wert von `SENTRY_ENVIRONMENT` stammt aus einem **festen Vokabular**. Alarmregeln filtern auf genau diese Zeichenketten, und sie muss über alle Komponenten hinweg dieselbe sein:

| Wert | Wofür |
|------|-------|
| `development` | Lokale Entwicklung. Standard, wenn nichts gesetzt ist. Aus dieser Umgebung darf nie jemand alarmiert werden. |
| `e2e` | Die End-to-End-Testläufe. Absichtlich provozierte Fehler gehören hierher und nicht in den Alarmkanal. |
| `staging` | Die Vorabumgebung. Ein neuer Vorgang hier ist ein Freigabe-Kriterium für das Release-Kandidaten. |
| `production` | Der Echtbetrieb. Nur hier wird alarmiert. |

Ein Tippfehler (`producton`) verhindert die Initialisierung **nicht** — die Anwendung protokolliert eine Warnung und meldet trotzdem. Das ist Absicht: Ein stiller Verzicht sähe von außen genauso aus wie eine gesunde, ruhige Instanz, während ein fremder Wert in der Umgebungs-Liste des Trackers sofort auffällt.

## Die Release-Kennung

`SENTRY_RELEASE` sollte das Image-Tag oder der Commit-SHA sein. Ohne sie kann der Tracker nicht sagen, welches Deployment einen Fehler eingeführt hat, und er kann eine **Regression** — ein als behoben markierter Fehler, der wiederkehrt — nicht von einem neuen Fehler unterscheiden. Genau diese Unterscheidung ist der Punkt, an dem ein Fehler-Tracker mehr wird als eine Fehlerliste.

Ist nichts gesetzt, meldet jede Komponente einen groben Ersatzwert (`kamerplanter-backend@1.0.0`, im Frontend `kamerplanter-frontend@dev`). Der ist absichtlich erkennbar unbrauchbar.

## Die Abtastrate

`SENTRY_SAMPLE_RATE=1.0` — also **jedes** Ereignis wird gemeldet.

Das ist eine bewusste Entscheidung und keine Voreinstellung, die niemand angefasst hat: Bei dem Aufkommen, das eine Kamerplanter-Instanz erzeugt, ist eine Stichprobe nur ein Weg, den einen Fehler zu verpassen, der einmal am Tag auftritt. Sobald das Ereignisaufkommen spürbar wird — insbesondere bei einem gehosteten Tarif mit Kontingent — ist die Rate neu zu bewerten und hier zu vermerken. Ein unlesbarer Wert fällt auf `1.0` zurück und protokolliert das.

---

## Was nicht übertragen wird

Fehlerereignisse können personenbezogene Daten enthalten, deshalb wird an der SDK-Grenze gefiltert, bevor irgendetwas den Prozess verlässt:

- **Anfrage-Inhalte und Cookies** werden vollständig verworfen. Ein Request-Body ist die dichteste Quelle personenbezogener Daten, die diese Anwendung hat — Pflanzennotizen, Erntedaten, Einladungen.
- **Header** folgen einer Positivliste (`Content-Type`, `User-Agent` und wenige weitere). Ein Header, den ein künftiger Proxy hinzufügt, wird also zurückgehalten, statt so lange zu lecken, bis jemand daran denkt, ihn zu sperren.
- **Query-Parameter, lokale Variablen im Stacktrace und Kontextfelder** werden anhand ihres *Namens* geschwärzt (`token`, `password`, `email`, `secret`, …). Der Schlüssel bleibt sichtbar, der Wert nicht — so ist beim Auswerten erkennbar, dass an dieser Stelle ein Geheimnis lag.
- **Vom Nutzer** bleiben nur `id` und Mandant übrig. Sie machen einen Vorgang bearbeitbar; Name, E-Mail und IP-Adresse tun das nicht.
- **Eingabe-Breadcrumbs** (`ui.input`) werden im Browser komplett verworfen.

Die Regeln laufen in **jeder** Umgebung, auch lokal. Ein Filter, der erst zur Produktivsetzung eingeschaltet wird, ist ein ungetesteter Filter.

## Was der Tracker nicht ist

Kein Log-Ziel. Dort landen ausschließlich Fehler und bewusst gemeldete Ereignisse; INFO- und DEBUG-Meldungen bleiben in der Log-Pipeline. Alles andere zerstört die Gruppierung und das Ereignis-Kontingent.

---

## Was gemeldet wird

| Komponente | Was das SDK übernimmt |
|------------|----------------------|
| Backend (FastAPI) | Nicht abgefangene Ausnahmen in jeder Anfrage, plus Fehler beim Start |
| Celery Worker und Beat | Fehlgeschlagene Hintergrundaufgaben — die unsichtbarste Fehlerart überhaupt, weil niemand auf eine Antwort wartet |
| Inference- und Knowledge-Service | Dasselbe, jeweils mit eigenem `component`-Tag |
| Frontend | Nicht abgefangene Fehler, abgewiesene Promises, und jeder Render-Fehler, den eine Fehlergrenze auffängt |

Die Fehlergrenzen des Frontends melden ausdrücklich mit: Eine Grenze, die eine Ersatzdarstellung zeigt, hat den Fehler aus Sicht aller globalen Handler zum Verschwinden gebracht — der Nutzer sieht eine aufgeräumte Karte, und niemand erfährt, dass das Widget kaputt ist.

## Nachprüfen, dass es funktioniert

Es gibt keinen Testknopf. Der belastbare Weg:

1. Setze `SENTRY_DSN` und starte die Container neu.
2. Backend: In den Logs steht `error_tracking: enabled for backend (environment=…, release=…)`.
3. Frontend: Im Netzwerk-Tab des Browsers erscheint ein zusätzliches JavaScript-Bündel — das ist das nachgeladene SDK. Erscheint es nicht, war die DSN nicht in `runtime-config.js`.
4. Provoziere einen Fehler und sieh nach, ob er im Tracker ankommt. Kommt er nicht an, prüfe zuerst die NetworkPolicy (Backend) beziehungsweise die Content-Security-Policy (Frontend, sichtbar als CSP-Verstoß in der Browser-Konsole).
