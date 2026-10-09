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
- **Die Anfrage-Adresse** ist das Routenmuster, nie der aufgerufene Pfad: Ereignis-URL und Transaktionsname lauten `/api/v1/t/{tenant_slug}/attachments/{key}/…`, nicht der Pfad mit Mandanten-Kürzel und Download-Token (das Token *ist* die Berechtigung). Hat das Framework kein Muster geliefert (404, Fehler vor dem Routing), reduziert das Backend den Pfad wie in seinen Zugriffsprotokollen auf feste Routen-Segmente. Methode, Host und Statuscode bleiben.
- **Query-Parameter** behalten nur ihren Namen, jeder Wert wird geschwärzt — auch die Roh-Query ausgehender Anfragen in Breadcrumbs (`http.query`). **Kontextfelder** werden anhand ihres *Namens* geschwärzt (`token`, `password`, `email`, `secret`, …), auch in verschachtelten Strukturen. Der Schlüssel bleibt sichtbar, der Wert nicht — so ist beim Auswerten erkennbar, dass an dieser Stelle ein Geheimnis lag.
- **Lokale Variablen im Stacktrace** werden nicht übertragen. Der Name einer Variablen verrät nicht, was sie enthält — `url` oder `html` in einem Mail-Adapter enthalten den Passwort-Reset-Link. Ein Ereignis zeigt deshalb Dateien, Funktionen und Zeilen, aber keine Laufzeitwerte.
- **Fehlertexte und Protokollmeldungen** durchlaufen in Backend und Celery-Worker dieselbe Bereinigung wie die Protokollzeilen: Eine Fehlermeldung aus der Anwendungslogik erscheint nur als Fehlercode, E-Mail-Adressen werden zu Digests, Query-Strings und Zugangsdaten in URLs (auch im Pfad, etwa ein Telegram-Bot-Token) zu `<redacted>`. Das gilt auch für Breadcrumbs. Die beiden Nebendienste (inference-service, knowledge-service) wenden eine einfachere Bereinigung an, die nur Formen erkennt: Zugangsdaten und Query-Strings in URLs, ein Token im Pfad nach Art von Telegram, E-Mail-Adressen (als `<email>`). Freitext wie eine Suchfrage hat keine Form und bleibt dort nicht verborgen. Unbehandelte Tracebacks, die diese Dienste nach stderr schreiben, durchlaufen dieselbe Bereinigung; Schlüssel von Wörterbüchern, Tags und Kontexte eines Ereignisses werden wie Werte bereinigt.
- **Vom Nutzer** sendet das Backend nur Pseudonyme und nur mit dessen Einwilligung `error_tracking` (Datenschutz-Einstellungen): `user.id` ist die Konto-Referenz `sub_…`, `user.tenant` die Mandanten-Referenz `ten_…` der Anfrage — dieselben Werte wie in den Logzeilen, nie die Schlüssel. Ohne Einwilligung, oder wenn sie nicht gelesen werden kann, geht das Ereignis ohne Nutzer-Block. Sie machen einen Vorgang bearbeitbar und einem Mandanten zuordenbar; Name, E-Mail und IP-Adresse tun das nicht. Was das SDK oder eine Integration selbst in den Nutzer-Block schreibt, wird verworfen. Ereignisse des Celery-Workers und der Nebendienste tragen keinen Nutzer-Block.
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
| Frontend | Nicht abgefangene Fehler, abgewiesene Promises, und jeder Render-Fehler, den eine Fehlergrenze auffängt — erst, wenn die Person im Browser der Fehleranalyse zugestimmt hat (siehe unten) |

Die Fehlergrenzen des Frontends melden ausdrücklich mit: Eine Grenze, die eine Ersatzdarstellung zeigt, hat den Fehler aus Sicht aller globalen Handler zum Verschwinden gebracht — der Nutzer sieht eine aufgeräumte Karte, und niemand erfährt, dass das Widget kaputt ist.

## Einwilligung im Frontend

Im Browser reicht die DSN allein nicht: Das Frontend lädt und startet sein SDK erst, wenn die Person der **Fehleranalyse** (`error_tracking`) zugestimmt hat. Solange sie nicht entschieden oder abgelehnt hat, lädt der Browser das SDK-Bündel nicht herunter, und kein Fehlerbericht verlässt ihn.

- **Wo gefragt wird:** Ist eine DSN gesetzt, erscheint beim ersten Besuch unten ein Einwilligungs-Banner mit „Alle akzeptieren", „Nur Notwendige" und „Einstellungen" — auch schon auf der Anmeldeseite. Ohne DSN erscheint kein Banner, denn dann gibt es im Browser nichts, dem man zustimmen könnte.
- **Light-Modus:** Hier erscheint kein Banner (Haushaltsausnahme der DSGVO). Damit gibt es auch keine Zustimmung, und das Frontend meldet im Light-Modus keine Fehler — das Backend schon.
- **Widerruf:** Unter **Datenschutz → Einwilligungen** steht der Schalter „Fehleranalyse erlauben". Ausschalten beendet das Melden sofort und ohne Neuladen, auch in anderen offenen Tabs desselben Browsers. Einschalten startet es ebenso.
- **Pro Browser:** Die Entscheidung liegt im `localStorage` des Browsers (`kamerplanter:consent:v1`) und gilt nur dort. Sie wird noch nicht mit der serverseitigen Einwilligung abgeglichen, die das Backend für den Nutzer-Block liest; das ist ein offener Folgeschritt.

Für dich als Betreiber heißt das: Nach dem Setzen der DSN kommen Frontend-Fehler nur von Personen an, die zugestimmt haben. Ein ruhiger Frontend-Bereich im Tracker kann also auch „niemand hat zugestimmt" bedeuten.

## Nachprüfen, dass es funktioniert

Es gibt keinen Testknopf. Der belastbare Weg:

1. Setze `SENTRY_DSN` und starte die Container neu.
2. Backend: In den Logs steht `error_tracking: enabled for backend (environment=…, release=…)`.
3. Frontend: Öffne die Anwendung in einem privaten Fenster. Es erscheint das Einwilligungs-Banner — fehlt es, war die DSN nicht in `runtime-config.js`. Klicke „Alle akzeptieren": Erst jetzt erscheint im Netzwerk-Tab des Browsers ein zusätzliches JavaScript-Bündel, das nachgeladene SDK.
4. Provoziere einen Fehler und sieh nach, ob er im Tracker ankommt. Kommt er nicht an, prüfe zuerst die NetworkPolicy (Backend) beziehungsweise die Content-Security-Policy (Frontend, sichtbar als CSP-Verstoß in der Browser-Konsole).
