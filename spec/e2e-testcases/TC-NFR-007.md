---
req_id: NFR-007
title: Betriebsstabilitaet & Monitoring — SLIs/SLOs, Alerting, Incident Response, Resilience
category: Betrieb / Observability
test_count: 42
coverage_areas:
  - Health-Check-Endpunkte (GET /health/live, GET /health/ready)
  - Readiness-Probe-Verhalten im Browser (503-Fehlerseite, Retry-After)
  - Graceful Degradation (Redis-Ausfall, Sensor-Service-Ausfall, TimescaleDB-Ausfall)
  - Circuit-Breaker-sichtbare UI-Auswirkungen (503 mit Service-Hinweis)
  - Rate-Limiting-Feedback (Retry-After-Meldung im Browser)
  - Smoke-Tests nach Deployment (API-Erreichbarkeit, Botanische-Familien-Endpunkt)
  - Metrics-Endpunkt-Erreichbarkeit (/metrics, prometheus-Scraping)
  - SLO-Statuspage-Anzeige (Operational/Degraded/Outage je Komponente)
  - Liveness- vs. Readiness-Unterschied im Nutzer-sichtbaren Verhalten
  - Stale-Data-Markierung im Dashboard bei Sensor-Service-Ausfall
  - Fehlermeldung bei vollstaendig nicht erreichbarer API
  - Frontend-Erreichbarkeit (HTTP 200 auf Root-URL)
generated: 2026-03-21
version: "1.0"
---

# TC-NFR-007: Betriebsstabilitaet & Monitoring

Dieses Dokument enthaelt End-to-End-Testfaelle aus **NFR-007 Betriebsstabilitaet & Monitoring v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in den Testschritten selbst. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale).

**Wichtiger Hinweis zur Testkategorie**: NFR-007 ist eine infrastrukturnahe NFR (SLIs/SLOs, Prometheus-Alerting, Circuit Breaker, Kubernetes-Probes). Ein Grossteil der Anforderungen ist aus dem Browser **nicht direkt beobachtbar** — diese Testfaelle pruefen ausschliesslich die **nutzer-sichtbaren Auswirkungen** von Betriebszustaenden:
- Was sieht der Nutzer, wenn die API nicht erreichbar ist?
- Was sieht der Nutzer, wenn das System degradiert laeuft?
- Welche Meldung erscheint bei Rate-Limiting?
- Sind die Health-Check-Endpunkte korrekt implementiert und liefern die richtigen Antwortinhalte?

Testfaelle, die Infrastrukturzustaende erfordern (Prometheus-Alerts, PagerDuty, Grafana-Dashboards, Kubernetes-Probes), sind als **[Infra-Test]** markiert und koennen nicht in einem Standard-Browser-E2E-Testlauf ausgefuehrt werden — sie erfordern eine dedizierte Betriebsumgebung mit vollem Monitoring-Stack.

---

## 1. Health-Check-Endpunkte

*Abdeckung: NFR-007 §6.1, §6.2 — Synthetic Monitoring, externe Health-Checks*

Die Health-Check-Endpunkte sind technische Endpunkte, die direkt im Browser aufrufbar sind. Ein Tester oder Monitoring-Tool kann sie wie eine normale URL besuchen und das Ergebnis pruefenn.

---

### TC-NFR007-001: Liveness-Endpunkt liefert "alive"-Status

**Requirement**: NFR-007 §6.1 — Externe Health-Checks (`GET /health/live`)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Backend-Anwendung laeuft und ist erreichbar
- Kein spezieller Systemzustand erforderlich

**Testschritte**:
1. Nutzer (oder externer Prober) oeffnet im Browser die URL `https://api.kamerplanter.example.com/health/live`

**Erwartete Ergebnisse**:
- Die Seite laedt erfolgreich (kein Fehlerbild, keine Browser-Fehlermeldung "ERR_CONNECTION_REFUSED")
- Der Inhalt der Antwort ist ein JSON-Objekt mit dem Feld `"status": "alive"`
- Die Antwort erscheint sofort (unter 5 Sekunden gemaess Timeout-Vorgabe §6.1)

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, health-check, liveness, synthetic-monitoring, §6.1]

---

### TC-NFR007-002: Readiness-Endpunkt liefert "ready"-Status wenn Datenbank verbunden

**Requirement**: NFR-007 §6.1 — Externe Health-Checks (`GET /health/ready`), §2.1 SLI Verfuegbarkeit
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Backend laeuft und ist erreichbar
- ArangoDB ist verbunden und antwortet

**Testschritte**:
1. Nutzer oeffnet im Browser die URL `https://api.kamerplanter.example.com/health/ready`

**Erwartete Ergebnisse**:
- Die Seite laedt erfolgreich
- Der Inhalt ist ein JSON-Objekt mit `"status": "ready"` und `"database": true`
- Die Antwort erscheint innerhalb von 10 Sekunden (gemaess Timeout-Vorgabe §6.1)

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, health-check, readiness, arangodb, sli-verfuegbarkeit, §6.1]

---

### TC-NFR007-003: Readiness-Endpunkt signalisiert Nicht-Bereitschaft bei Datenbankausfall

**Requirement**: NFR-007 §6.1 — Readiness-Probe, §4.5 Graceful Degradation
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Backend laeuft
- ArangoDB ist **nicht** erreichbar (z.B. Container gestoppt, Verbindung unterbrochen)

**Testschritte**:
1. Nutzer oeffnet im Browser die URL `https://api.kamerplanter.example.com/health/ready`

**Erwartete Ergebnisse**:
- Die Seite laedt (kein Connection-Refused-Fehler — das Backend laeuft noch)
- Der Inhalt zeigt `"status": "not_ready"` und `"database": false`
- Die HTTP-Antwort signalisiert einen Nicht-OK-Status (der Browser zeigt ggf. einen Fehlerhintergrund, aber der JSON-Body ist sichtbar)

**Nachbedingungen**:
- Kubernetes-Liveness-Probe wird den Pod nicht neu starten (nur Readiness scheitert)
- Der Pod wird aus dem Service-Endpoint-Pool entfernt bis Readiness wiederhergestellt ist

**Tags**: [nfr-007, health-check, readiness, arangodb-ausfall, graceful-degradation, §6.1, §4.5]

---

### TC-NFR007-004: Liveness-Endpunkt antwortet auch wenn Datenbank nicht erreichbar ist

**Requirement**: NFR-007 §6.1 — Unterschied Liveness vs. Readiness
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Backend-Prozess laeuft
- ArangoDB ist nicht erreichbar

**Testschritte**:
1. Nutzer oeffnet im Browser `https://api.kamerplanter.example.com/health/live`

**Erwartete Ergebnisse**:
- Die Antwort ist `"status": "alive"` (das Backend selbst lebt noch)
- Kein Connection-Refused-Fehler erscheint
- Der Liveness-Check ist unabhaengig vom Datenbankstatus

**Nachbedingungen**:
- Kubernetes erkennt den Pod als "lebendig" und startet ihn nicht neu
- Nur die Readiness-Probe (TC-NFR007-003) scheitert

**Tags**: [nfr-007, health-check, liveness-vs-readiness, §6.1]

---

### TC-NFR007-005: API-Smoke-Check liefert gueltige Daten ueber botanische Familien

**Requirement**: NFR-007 §6.1 — API Smoke Check, §6.2 Smoke-Tests nach Deployment
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Backend und ArangoDB laufen
- Seed-Daten sind eingespielt (mindestens eine botanische Familie vorhanden)

**Testschritte**:
1. Nutzer oeffnet im Browser `https://api.kamerplanter.example.com/api/v1/botanical-families?limit=1`

**Erwartete Ergebnisse**:
- Die Seite laedt erfolgreich
- Die Antwort enthaelt ein JSON-Objekt mit einem `items`-Array, das mindestens einen Eintrag enthaelt
- Der Eintrag hat die Felder `_key`, `name` und `created_at` (oder vergleichbare Pflichtfelder)
- Die Antwort erscheint innerhalb von 10 Sekunden

**Nachbedingungen**:
- Kein Systemzustand veraendert (Leseoperation)

**Tags**: [nfr-007, smoke-test, botanical-families, deployment-validation, §6.1, §6.2]

---

### TC-NFR007-006: Metrics-Endpunkt ist erreichbar und enthaelt http_requests_total

**Requirement**: NFR-007 §6.2 — Smoke-Tests nach Deployment (Metrics-Check), §2.1 SLI-Metriken
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Backend laeuft mit aktiviertem Prometheus-Metrics-Exporter
- Mindestens ein HTTP-Request wurde verarbeitet (damit der Counter nicht leer ist)

**Testschritte**:
1. Nutzer oeffnet im Browser `https://api.kamerplanter.example.com/metrics`

**Erwartete Ergebnisse**:
- Die Seite laedt erfolgreich (kein 404, kein 403)
- Der Inhalt ist im Prometheus-Textformat (Zeilen mit `# HELP`, `# TYPE` und Metrikwerten)
- Die Metrik `http_requests_total` ist im Inhalt enthalten
- Die Metrik `circuit_breaker_state` ist vorhanden (gemaess §4.1 Circuit-Breaker-Gauge)
- Die Metrik `connection_pool_active_connections` ist vorhanden (gemaess §4.4 Bulkhead)
- Die Metrik `service_degraded` ist vorhanden (gemaess §4.5 Graceful-Degradation-Gauge)

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, metrics, prometheus, smoke-test, circuit-breaker, §6.2, §2.1, §4.1, §4.4, §4.5]

---

### TC-NFR007-007: Frontend-Root-URL liefert HTTP-200 (Erreichbarkeit)

**Requirement**: NFR-007 §6.1 — Frontend Erreichbarkeit (`GET /`, HTTP 200)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Frontend-Container laeuft und ist erreichbar (Vite-Build deployed)
- Ingress/Traefik ist korrekt konfiguriert

**Testschritte**:
1. Nutzer oeffnet im Browser `https://app.kamerplanter.example.com/`

**Erwartete Ergebnisse**:
- Die Seite laedt ohne Fehlermeldung
- Der Browser zeigt das Kamerplanter-Frontend (Login-Seite oder Dashboard, je nach Auth-Status)
- Kein "502 Bad Gateway", kein "503 Service Unavailable", kein "ERR_CONNECTION_REFUSED" erscheint
- Die Seite laedt innerhalb von 10 Sekunden

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, frontend-erreichbarkeit, smoke-test, §6.1]

---

## 2. Rate-Limiting und nutzerseitige Rueckmeldung

*Abdeckung: NFR-007 §4.6 — Rate Limiting, Retry-After-Header*

---

### TC-NFR007-008: Rate-Limit-Meldung erscheint nach zu vielen Requests (Human-Client)

**Requirement**: NFR-007 §4.6 — Rate Limiting, Retry-After-Header (Human: 100 Requests/Minute)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- In den letzten 60 Sekunden wurden mehr als 100 Requests von derselben IP-Adresse gesendet (durch schnelles Navigieren oder ein Testskript)

**Testschritte**:
1. Nutzer navigiert schnell durch verschiedene Seiten (z.B. Artenliste, Pflanzenfamilien, Standorte) und loest dabei mehr als 100 API-Requests in einer Minute aus
2. Nutzer versucht einen weiteren Seitenaufruf oder eine weitere Aktion (z.B. Klick auf "Erstellen")

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint im Browser (Snackbar oder Fehlerseite)
- Die Meldung informiert den Nutzer, dass zu viele Anfragen gesendet wurden
- Die Meldung enthaelt einen Hinweis, wie lange der Nutzer warten soll (Retry-After-Information, z.B. "Bitte warten Sie X Sekunden")
- Der Nutzer wird nicht ausgeloggt
- Nach Ablauf der Wartezeit funktionieren neue Requests wieder normal

**Nachbedingungen**:
- Rate-Limit-Zaehler wird nach dem Zeitfenster zurueckgesetzt

**Tags**: [nfr-007, rate-limiting, retry-after, fehlermeldung, human-client, §4.6]

---

### TC-NFR007-009: Schreiboperationen haben strengeres Rate-Limit (20 Requests/Minute)

**Requirement**: NFR-007 §4.6 — Per Endpunkt Schreiboperationen: 20 Requests/Minute (Human)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt mit Schreibrechten
- Testtenant mit Seed-Daten vorhanden

**Testschritte**:
1. Nutzer oeffnet das Formular zum Erstellen einer botanischen Familie
2. Nutzer klickt mehr als 20-mal in einer Minute auf "Erstellen" (mit gueltigen oder ungueltigen Daten — der Zaehler laeuft auch bei Validierungsfehlern)
3. Nutzer versucht die 21. Erstellaktion

**Erwartete Ergebnisse**:
- Ab dem 21. Versuch erscheint eine Fehlermeldung (Snackbar oder Modal)
- Die Meldung informiert ueber das Rate-Limit fuer Schreiboperationen
- Der Retry-After-Wert ist in der Meldung oder dem Response-Header sichtbar
- Leseoperationen (z.B. Artenliste laden) funktionieren weiterhin ohne Einschraenkung

**Nachbedingungen**:
- Kein Datenverlust bei gueltigen Requests vor dem Limit

**Tags**: [nfr-007, rate-limiting, schreiboperationen, §4.6]

---

## 3. Graceful Degradation — sichtbare UI-Auswirkungen

*Abdeckung: NFR-007 §4.5 — Graceful Degradation-Tabelle*

Diese Testfaelle erfordern eine Testumgebung, in der einzelne Dienste kontrolliert gestoppt werden koennen. Sie sind als **[Infra-Test]** markiert, da die Vorbedingungen nicht im Standard-Browser hergestellt werden koennen.

---

### TC-NFR007-010: Redis-Ausfall — Nutzer kann weiterhin Daten lesen (Cache-Bypass) [Infra-Test]

**Requirement**: NFR-007 §4.5 — Graceful Degradation: Redis-Ausfall → Cache-Bypass
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Redis-Dienst wurde gestoppt (z.B. `kubectl scale deployment redis --replicas=0`)
- ArangoDB laeuft normal

**Testschritte**:
1. Nutzer navigiert zur Artenliste (`/stammdaten/arten`)
2. Nutzer gibt einen Suchbegriff in das Suchfeld ein
3. Nutzer klickt auf eine Art, um die Detailseite zu oeffnen
4. Nutzer navigiert zur Standortliste (`/standorte`)

**Erwartete Ergebnisse**:
- Alle Seiten laden erfolgreich — kein "Service nicht verfuegbar"-Fehler erscheint
- Die Artenliste zeigt korrekte Daten (direkt aus ArangoDB, ohne Cache)
- Die Suche funktioniert (ggf. minimal langsamer, aber ohne Fehlermeldung)
- Die Detailseite zeigt alle erwarteten Felder
- Kein unendlich ladender Spinner erscheint

**Nachbedingungen**:
- `service_degraded{component="redis"}` Metrik zeigt Wert 1 (pruefbar ueber /metrics)
- Celery-Tasks koennen nicht ausgefuehrt werden (Celery-Broker ist ausgefallen)

**Siehe auch**: TC-NFR007-011 (Celery-Fallback bei Redis-Ausfall)

**Tags**: [nfr-007, graceful-degradation, redis-ausfall, cache-bypass, infra-test, §4.5]

---

### TC-NFR007-011: Redis-Ausfall — kritische Phase-Transitions laufen synchron als Fallback [Infra-Test]

**Requirement**: NFR-007 §4.5 — Graceful Degradation: Celery Worker → synchrone Fallback-Verarbeitung fuer kritische Tasks
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt als Grower
- Redis-Dienst gestoppt (Celery-Broker nicht erreichbar)
- Mindestens eine aktive Pflanzinstanz in der Keimungsphase vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Pflanzinstanz in der Keimungsphase
2. Nutzer klickt auf "Naechste Phase" (Phase-Uebergang zu Saemling)
3. Nutzer wartet auf die Systemantwort

**Erwartete Ergebnisse**:
- Der Phasenuebergang wird ausgefuehrt (kein endloser Ladezustand)
- Die Detailseite zeigt die neue Phase "Saemling" nach dem Uebergang
- Ggf. erscheint eine Hinweismeldung, dass die Verarbeitung im eingeschraenkten Modus laeuft ("Service voruebergehend eingeschraenkt — Basisfunktionen verfuegbar")
- Der Nutzer kann weiterarbeiten (kein Totalausfall)

**Nachbedingungen**:
- Die Phase ist korrekt gespeichert (in ArangoDB, nicht via Celery-Queue)

**Tags**: [nfr-007, graceful-degradation, redis-ausfall, celery-fallback, phase-transition, infra-test, §4.5]

---

### TC-NFR007-012: TimescaleDB-Ausfall — Dashboard zeigt "Daten verzoeGert"-Hinweis [Infra-Test]

**Requirement**: NFR-007 §4.5 — Graceful Degradation: TimescaleDB → Dashboards zeigen "Daten verzoegert"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- TimescaleDB ist nicht erreichbar (z.B. gestoppt)
- ArangoDB und Redis laufen normal

**Testschritte**:
1. Nutzer navigiert zum Dashboard (`/dashboard`)
2. Nutzer betrachtet die Sensor-Widgets und Zeitreihen-Diagramme

**Erwartete Ergebnisse**:
- Das Dashboard laedt (kein Totalausfall der Seite)
- Widgets, die TimescaleDB-Daten benoetigen (Sensorgraphen, VPD-Kurven), zeigen einen deutlichen Hinweis: z.B. "Sensordaten verzoegert" oder "Daten nicht verfuegbar"
- Widgets, die keine Zeitreihendaten benoetigen (Pflanzenanzahl, Status-Uebersicht), zeigen korrekte Daten aus ArangoDB
- Kein unendlich ladender Spinner erscheint ohne Rueckmeldung

**Nachbedingungen**:
- `service_degraded{component="timescaledb"}` Metrik zeigt Wert 1

**Tags**: [nfr-007, graceful-degradation, timescaledb-ausfall, dashboard, daten-verzoegert, infra-test, §4.5]

---

### TC-NFR007-013: Externer Sensor-Service ausgefallen — letzte bekannte Werte mit Stale-Markierung [Infra-Test]

**Requirement**: NFR-007 §4.5 — Graceful Degradation: externer Sensor-Service → letzte bekannte Werte, Stale-Markierung im UI
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Home Assistant oder externer Sensor-Service ist nicht erreichbar
- Zuvor wurden Sensordaten erfolgreich empfangen und gecacht (letzte bekannte Werte vorhanden)

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Pflanzinstanz mit Sensordaten
2. Nutzer betrachtet die Sensor-Anzeige (Temperatur, Luftfeuchtigkeit, VPD)

**Erwartete Ergebnisse**:
- Die Sensor-Anzeige zeigt die zuletzt empfangenen Werte (nicht "--" oder leer)
- Neben den Werten erscheint eine visuelle Markierung, die auf veraltete Daten hinweist (z.B. ein Warnsymbol, grauer Text, Tooltip "Letzte bekannte Werte — Sensor nicht erreichbar")
- Die Meldung enthalt den Zeitpunkt des letzten gueltigen Messwerts
- Der Nutzer kann die Seite weiterhin nutzen (keine Fehlermeldung, die weitere Aktionen blockiert)

**Nachbedingungen**:
- `service_degraded{component="sensor_service"}` Metrik zeigt Wert 1

**Tags**: [nfr-007, graceful-degradation, sensor-ausfall, stale-data, home-assistant, infra-test, §4.5]

---

### TC-NFR007-014: Circuit Breaker geoeffnet — API liefert sofort 503 statt zu blockieren [Infra-Test]

**Requirement**: NFR-007 §4.1 — Circuit Breaker: OPEN-Zustand → sofortiger 503 mit Retry-After
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- ArangoDB ist so konfiguriert, dass alle Requests fehlschlagen (z.B. Netzwerkpartition)
- Nach 5 Fehlern hat der Circuit Breaker den OPEN-Zustand erreicht

**Testschritte**:
1. Nutzer versucht, die Artenliste aufzurufen (`/stammdaten/arten`)
2. Nutzer wartet auf die Systemantwort

**Erwartete Ergebnisse**:
- Die Fehlermeldung erscheint **sofort** (kein langes Warten auf Timeouts)
- Eine Meldung wie "Service voruebergehend nicht verfuegbar" oder "Service vorueber&gehend eingeschraenkt" erscheint
- Die Meldung enthaelt einen Hinweis, wann der Nutzer es erneut versuchen soll (Retry-After-Information)
- Der Browser haengt nicht und der Nutzer kann andere Seitenteile weiter nutzen
- Nach 30 Sekunden (Circuit-Breaker-Timeout) geht das System in den HALF-OPEN-Zustand — ein erneuter Versuch des Nutzers wird durchgelassen

**Nachbedingungen**:
- `circuit_breaker_state{dependency="arangodb"}` Metrik zeigt Wert 2 (open)

**Tags**: [nfr-007, circuit-breaker, open-state, 503, retry-after, infra-test, §4.1]

---

### TC-NFR007-015: Circuit Breaker HALF-OPEN — System erholt sich nach 30 Sekunden [Infra-Test]

**Requirement**: NFR-007 §4.1 — Circuit Breaker: Zustandsuebergang OPEN → HALF-OPEN → CLOSED
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Circuit Breaker befindet sich im OPEN-Zustand (Voraussetzung: TC-NFR007-014)
- 30 Sekunden sind seit dem letzten Fehler vergangen
- ArangoDB ist wieder erreichbar (Stoerung behoben)

**Testschritte**:
1. Nutzer wartet 30 Sekunden nach dem letzten Fehler
2. Nutzer klickt auf "Erneut versuchen" oder laedt die Seite neu
3. Nutzer beobachtet das Verhalten ueber 3 Probe-Requests (3 Requests muessen erfolgreich sein, um den Circuit zu schliessen)

**Erwartete Ergebnisse**:
- Nach 30 Sekunden wird der erste Probe-Request durchgelassen (HALF-OPEN-Zustand)
- Wenn die Probe erfolgreich ist, laedt die naechste Seite normal
- Nach 3 erfolgreichen Requests normalisiert sich das Systemverhalten vollstaendig
- Keine Fehlermeldungen mehr erscheinen
- Die Liste zeigt wieder aktuelle Daten

**Nachbedingungen**:
- `circuit_breaker_state{dependency="arangodb"}` Metrik zeigt Wert 0 (closed)

**Tags**: [nfr-007, circuit-breaker, half-open, recovery, infra-test, §4.1]

---

## 4. API-Nicht-Erreichbarkeit und Frontend-Fehlerverhalten

*Abdeckung: NFR-007 §1.3 — Nutzer-sichtbares Verhalten bei Totalausfall*

---

### TC-NFR007-016: Vollstaendiger API-Ausfall — Nutzer sieht klare Fehlermeldung statt Endlos-Spinner

**Requirement**: NFR-007 §1.3 (Business Case: Nutzerperspektive), §4.1 Circuit Breaker Nutzer-Story
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt oder versucht die App zu nutzen
- Backend-API ist vollstaendig nicht erreichbar (z.B. alle Pods ausgefallen)

**Testschritte**:
1. Nutzer oeffnet die Kamerplanter-App im Browser
2. Nutzer navigiert zu einer datenbankgestuetzten Seite (z.B. Artenliste)
3. Nutzer wartet auf eine Systemantwort

**Erwartete Ergebnisse**:
- Kein endlos ladender Spinner erscheint ohne Rueckmeldung
- Nach maximal 30 Sekunden (globaler Timeout) erscheint eine Fehlermeldung
- Die Meldung ist nutzerfreundlich (keine technischen Stack-Traces, keine HTTP-Statuscode-Zahlen sichtbar)
- Die Meldung enthaelt einen Hinweis, es spaeter erneut zu versuchen
- Die Navigation (Sidebar, Header) bleibt nutzbar

**Nachbedingungen**:
- Fehlerzustand bleibt bis zur Wiederherstellung der API bestehen

**Tags**: [nfr-007, totalausfall, fehlermeldung, timeout, endlos-spinner, §1.3, §4.3]

---

### TC-NFR007-017: Netzwerkfehler-Snackbar erscheint bei unterbrochener Verbindung

**Requirement**: NFR-007 §4.3 — Timeouts (kein Netzwerkaufruf ohne Timeout), NFR-006 Error-Response-Schema
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt und befindet sich auf der Artenliste
- Netzwerkverbindung wird unterbrochen (Entwickler-Tools → Offline) oder API-Timeout wird simuliert

**Testschritte**:
1. Nutzer befindet sich auf der Artenliste und die Liste wurde erfolgreich geladen
2. Netzwerkverbindung wird unterbrochen (z.B. WLAN ausschalten oder Entwickler-Tools "Offline"-Modus)
3. Nutzer klickt auf "Erstellen", um eine neue Art anzulegen
4. Nutzer fuellt das Formular aus und klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (Snackbar oder Inline-Fehlermeldung): "Netzwerkfehler..." oder "Verbindung fehlgeschlagen"
- Das Formular bleibt geoeffnet mit den eingegebenen Daten (kein Datenverlust)
- Der Nutzer kann den Speichern-Vorgang wiederholen, sobald die Verbindung wiederhergestellt ist
- Kein unbehandelter JavaScript-Fehler erscheint in der UI

**Nachbedingungen**:
- Formular-Daten erhalten bis zum erfolgreichen Speichern oder Abbrechen

**Tags**: [nfr-007, netzwerkfehler, timeout, snackbar, formular-datenverlust, §4.3]

---

## 5. Smoke-Test-Validierung nach Deployment

*Abdeckung: NFR-007 §6.2 — Smoke-Tests nach Deployment*

---

### TC-NFR007-018: Smoke-Test-Sequenz nach Production-Deployment

**Requirement**: NFR-007 §6.2 — Smoke-Tests nach Deployment (Health + API + Metrics)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Ein neues Backend-Image wurde in Production deployed
- Der Post-Deploy-Smoke-Test-Job (Kubernetes Helm Hook) wird ausgefuehrt

**Testschritte**:
1. Deployment-Pipeline deployt das neue Backend-Image via Helm
2. Helm-Hook startet den `post-deploy-smoke-test`-Job
3. Der Job fuehrt folgende Checks durch (sichtbar in Kubernetes-Logs oder CI-Pipeline-Output):
   - Schritt 1: `GET /health/ready` gibt "ready" zurueck
   - Schritt 2: `GET /api/v1/botanical-families?limit=1` gibt eine Liste mit >= 1 Eintrag zurueck
   - Schritt 3: `GET /metrics` enthaelt die Metrik `http_requests_total`
4. Deployment-Pipeline zeigt "Smoke Tests: PASSED"

**Erwartete Ergebnisse**:
- Alle drei Smoke-Checks sind erfolgreich
- Die Pipeline zeigt "All smoke tests passed"
- Das Deployment wird als abgeschlossen markiert
- Kein Rollback wird ausgeloest

**Nachbedingungen**:
- Neues Image laeuft stabil in Production

**Tags**: [nfr-007, smoke-test, deployment, helm-hook, §6.2]

---

### TC-NFR007-019: Fehlgeschlagener Smoke-Test loest automatisches Rollback aus [Infra-Test]

**Requirement**: NFR-007 §6.2 — Fehlgeschlagene Smoke-Tests loesen automatisches Rollback aus (Helm `--atomic`)
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Ein neues Backend-Image wird deployed, das einen Fehler enthaelt (z.B. /health/ready antwortet mit "not_ready")
- Helm ist mit `--atomic` Flag konfiguriert

**Testschritte**:
1. Fehlerhaftes Backend-Image wird via Helm deployed
2. Post-Deploy-Smoke-Test-Job startet
3. Der `GET /health/ready`-Check schlaegt fehl (Antwort nicht "ready")
4. Helm erkennt den fehlgeschlagenen Hook

**Erwartete Ergebnisse**:
- Der Smoke-Test-Job loggt: "Smoke Test FAILED: Health Check"
- Helm startet automatisch einen Rollback auf die vorherige funktionierende Version
- Die CI/CD-Pipeline zeigt einen Fehler und den Rollback-Status
- Nach dem Rollback ist die vorherige Version wieder aktiv und `/health/ready` antwortet mit "ready"

**Nachbedingungen**:
- Production laeuft weiterhin auf der stabilen vorherigen Version
- Kein Nutzer erlebt einen Ausfall (Rollback erfolgt vor Traffic-Umleitung)

**Tags**: [nfr-007, smoke-test, rollback, helm-atomic, fehlschlag, §6.2]

---

## 6. SLO-Verfuegbarkeit und Statuspage

*Abdeckung: NFR-007 §5.5 — Statuspage, §2.2 SLO-Definitionen*

---

### TC-NFR007-020: Statuspage zeigt "Operational" wenn alle Komponenten gesund sind [Infra-Test]

**Requirement**: NFR-007 §5.5 — Statuspage (oeffentlich, Komponenten-Status)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Statuspage ist deployed und erreichbar (z.B. via Atlassian Statuspage oder Cachet)
- Alle Komponenten (API, Frontend, Sensordaten, Hintergrundverarbeitung) laufen normal
- Kein aktiver Critical-Alert

**Testschritte**:
1. Nutzer (auch ohne Login) oeffnet die Statuspage-URL

**Erwartete Ergebnisse**:
- Die Statuspage zeigt alle vier Komponenten: "API", "Web-Frontend", "Sensordaten-Erfassung", "Hintergrund-Verarbeitung"
- Alle Komponenten zeigen den Status "Operational" (gruenes Symbol)
- Kein aktives Incident wird angezeigt

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, statuspage, operational, oeffentlich, §5.5]

---

### TC-NFR007-021: Statuspage wechselt automatisch auf "Degraded" bei aktivem Warning-Alert [Infra-Test]

**Requirement**: NFR-007 §5.5 — Statuspage wird automatisch ueber Prometheus-Alerts aktualisiert
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Statuspage ist konfiguriert mit automatischer Prometheus-Alert-Aktualisierung
- Ein Warning-Alert (z.B. `ElevatedErrorRate` oder `HighLatencyP95`) ist aktiv

**Testschritte**:
1. Prometheus erkennt eine erhoeHte Error Rate (> 1% fuer mehr als 10 Minuten)
2. Alert `ElevatedErrorRate` wird ausgeloest
3. Alertmanager aktualisiert die Statuspage via API

**Erwartete Ergebnisse**:
- Die Statuspage wechselt den API-Status von "Operational" auf "Degraded"
- Eine Incident-Meldung erscheint auf der Statuspage mit dem Zeitpunkt des Beginns
- Nutzer, die die Statuspage besuchen, sehen den degradierten Zustand

**Nachbedingungen**:
- Wenn der Alert sich aufloest, wechselt die Statuspage zurueck auf "Operational"

**Tags**: [nfr-007, statuspage, degraded, alert-aktualisierung, §5.5]

---

### TC-NFR007-022: Statuspage zeigt "Outage" bei aktivem Critical-Alert (z.B. AvailabilityBelowSLO) [Infra-Test]

**Requirement**: NFR-007 §5.5 — Statuspage-Status "Outage", §3.2 AvailabilityBelowSLO Critical Alert
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Statuspage ist konfiguriert
- 30-Tage-Verfuegbarkeit ist unter 99,5% gefallen (SLO-Verletzung)
- Critical Alert `AvailabilityBelowSLO` ist aktiv (seit mind. 5 Minuten)

**Testschritte**:
1. Prometheus erkennt `slo:availability:ratio_30d < 0.995`
2. Alert wird nach 5-Minuten-for-Klausel ausgeloest
3. Alertmanager aktualisiert Statuspage

**Erwartete Ergebnisse**:
- Statuspage wechselt API-Status auf "Outage"
- Incident wird mit Schweregrad und Zeitpunkt angezeigt
- Nutzer sehen die Outage-Information ohne Login

**Nachbedingungen**:
- Incident bleibt aktiv bis Alert sich aufloest und Statuspage-Update erfolgt

**Tags**: [nfr-007, statuspage, outage, slo-verletzung, critical-alert, §5.5, §3.2]

---

## 7. Alerting-Verhalten (beobachtbar aus Operations-Perspektive)

*Abdeckung: NFR-007 §3.1 — Alerting-Schweregrade, §3.2 PrometheusRule-Definitionen*

Diese Testfaelle erfordern Zugriff auf Alertmanager, Prometheus-UI und Slack/PagerDuty. Sie sind als **[Infra-Test]** markiert.

---

### TC-NFR007-023: Critical-Alert loest PagerDuty-Benachrichtigung aus [Infra-Test]

**Requirement**: NFR-007 §3.1 — Critical: PagerDuty/OpsGenie + Slack #incidents, §3.4 Eskalation L1
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Alertmanager ist konfiguriert mit PagerDuty Service Key und Slack Webhook
- Prometheus laeuft mit den AlertingRules aus §3.2

**Testschritte**:
1. Engineer loest manuell einen Test-Alert aus (z.B. `amtool alert add alertname=TestCritical severity=critical`)
2. Alertmanager verarbeitet den Alert (Routing-Regel: severity=critical → receiver "critical")
3. On-Call-Engineer ueberprueft PagerDuty und den Slack-Kanal #incidents

**Erwartete Ergebnisse**:
- PagerDuty zeigt eine neue Incident-Meldung mit Severity "critical" innerhalb von 1 Minute
- Slack-Kanal #incidents zeigt eine Nachricht mit dem Alert-Titel und der Summary
- Die Nachricht enthaelt die `runbook_url` (Link zu einem Runbook)
- Reaktionszeit bis zum Acknowledge durch On-Call: ≤ 15 Minuten

**Nachbedingungen**:
- Test-Alert wird manuell aufgeloest (`amtool silence` oder `amtool alert expire`)

**Tags**: [nfr-007, alerting, critical, pagerduty, slack-incidents, eskalation, infra-test, §3.1, §3.4]

---

### TC-NFR007-024: Warning-Alert wird an Slack #alerts und E-Mail geroutet [Infra-Test]

**Requirement**: NFR-007 §3.1 — Warning: Slack #alerts + E-Mail, §3.3 Alertmanager-Konfiguration
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Alertmanager konfiguriert mit Slack Webhook und E-Mail-Empfaenger `oncall@kamerplanter.example.com`

**Testschritte**:
1. Engineer loest Test-Warning-Alert aus (`amtool alert add alertname=TestWarning severity=warning`)
2. Alertmanager verarbeitet den Alert (Routing: severity=warning → receiver "warning")
3. Engineer prueft Slack #alerts und Postfach `oncall@kamerplanter.example.com`

**Erwartete Ergebnisse**:
- Slack-Kanal #alerts zeigt eine Nachricht mit dem Warning-Titel
- E-Mail-Benachrichtigung geht an `oncall@kamerplanter.example.com`
- Der Alert erscheint NICHT im Kanal #incidents (korrektes Routing)
- `runbook_url` ist in der Nachricht enthalten

**Nachbedingungen**:
- Test-Alert aufgeloest

**Tags**: [nfr-007, alerting, warning, slack-alerts, email, routing, infra-test, §3.1, §3.3]

---

### TC-NFR007-025: Inhibition-Rule — Warning wird unterdrueckt wenn Critical fuer gleichen Service aktiv [Infra-Test]

**Requirement**: NFR-007 §3.3 Alertmanager-Konfiguration, §3.5 Alert-Fatigue-Praevention (Inhibition)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Alertmanager mit Inhibition-Rules konfiguriert
- Ein Critical-Alert (`HighErrorRate`) ist aktiv fuer den Backend-Service

**Testschritte**:
1. Critical-Alert `HighErrorRate` ist aktiv (Error Rate > 5% seit 5 Minuten)
2. Gleichzeitig wird `ElevatedErrorRate` (Warning, Error Rate > 1%) ausgeloest
3. Engineer prueft Alertmanager-UI auf aktive und inhibited Alerts

**Erwartete Ergebnisse**:
- `HighErrorRate` (Critical) ist aktiv und loest PagerDuty + Slack #incidents aus
- `ElevatedErrorRate` (Warning) wird in Alertmanager-UI als "inhibited" angezeigt
- Kein separater Warning erscheint in Slack #alerts (Inhibition greift korrekt)
- Nach Aufloesen des Critical-Alerts erscheint ggf. der Warning-Alert (falls noch aktiv)

**Nachbedingungen**:
- Alert-Fatigue wurde verhindert (nur 1 Benachrichtigung statt 2)

**Tags**: [nfr-007, alerting, inhibition, alert-fatigue, critical-vs-warning, infra-test, §3.3, §3.5]

---

### TC-NFR007-026: Jeder Alert hat eine runbook_url-Annotation [Infra-Test]

**Requirement**: NFR-007 §3.6 — Runbook-Pflicht: jeder Alert enthaelt runbook_url
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- PrometheusRules aus §3.2 sind deployt

**Testschritte**:
1. Engineer oeffnet Prometheus-UI → Alert-Regeln-Uebersicht
2. Engineer prueft alle definierten Alerts auf vorhandene Annotationen

**Erwartete Ergebnisse**:
- Alle Alerts (`AvailabilityBelowSLO`, `HighErrorRate`, `ElevatedErrorRate`, `HighLatencyP95`, `HighLatencyP99`, `HighCPUUsage`, `HighMemoryUsage`, `ArangoDBDown`, `RedisDown`, `ErrorBudgetLow`, `ErrorBudgetExhausted`, `DiskFillingUp`) haben eine `runbook_url`-Annotation
- Alle `runbook_url`-Werte sind nicht leer und zeigen auf existierende Runbook-Seiten
- Die Runbook-URLs folgen dem Schema `https://wiki.internal/runbooks/{runbook-name}`

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, alerting, runbook-pflicht, annotation, §3.6]

---

## 8. Error-Budget und SLO-Metriken

*Abdeckung: NFR-007 §2.4 — Error Budgets, §2.5 SLO-Recording-Rules*

---

### TC-NFR007-027: SLO-Recording-Rules liefern Werte in Prometheus [Infra-Test]

**Requirement**: NFR-007 §2.5 — SLO-Prometheus-Recording-Rules
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Prometheus mit PrometheusRule `slo-recording-rules` aus §2.5 deployt
- Mindestens 5 Minuten Betrieb nach dem Deployment

**Testschritte**:
1. Engineer oeffnet Prometheus-UI → Expression-Browser
2. Engineer gibt folgende Abfragen ein und klickt "Execute":
   - `slo:availability:ratio_30d`
   - `slo:error_rate:ratio_5m`
   - `slo:latency_p95:seconds_5m`
   - `slo:latency_p99:seconds_5m`
   - `slo:error_budget:remaining_ratio`

**Erwartete Ergebnisse**:
- Alle fuenf Metriken liefern numerische Werte (keine leeren Ergebnisse)
- `slo:availability:ratio_30d` zeigt einen Wert zwischen 0 und 1 (z.B. 0.999)
- `slo:error_rate:ratio_5m` zeigt einen Wert < 0.01 (unter SLO-Ziel) bei normalem Betrieb
- `slo:latency_p95:seconds_5m` zeigt einen Wert < 0.5 (unter SLO-Ziel) bei normalem Betrieb
- `slo:error_budget:remaining_ratio` zeigt einen Wert zwischen 0 und 1

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, slo, recording-rules, prometheus, error-budget, §2.5]

---

### TC-NFR007-028: ErrorBudgetLow-Alert bei weniger als 25% verbleibendem Budget [Infra-Test]

**Requirement**: NFR-007 §3.2 — Alert `ErrorBudgetLow` (< 25% verbleibend), §2.4 Error-Budget-Regeln
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- SLO-Recording-Rules aktiv
- `slo:error_budget:remaining_ratio` ist kleiner als 0.25 (Simulation durch kuenstlich erhoehte Error Rate)

**Testschritte**:
1. Engineer simuliert eine hohe Error Rate, die das Error Budget auf unter 25% sinken laesst
2. Prometheus evaluiert `ErrorBudgetLow`-Alert: `slo:error_budget:remaining_ratio < 0.25` fuer 5 Minuten
3. Engineer prueft Alertmanager auf neuen Warning-Alert

**Erwartete Ergebnisse**:
- Alert `ErrorBudgetLow` erscheint als aktiver Warning in Alertmanager nach 5 Minuten
- Slack #alerts erhaelt eine Nachricht: "Error Budget unter 25% (XX% verbleibend)"
- Die Meldung enthaelt die `runbook_url` zum Error-Budget-Runbook
- Kein PagerDuty-Alert (Severity ist Warning, nicht Critical)

**Nachbedingungen**:
- Feature-Freeze-Empfehlung wird dokumentiert (§2.4 Error-Budget-Regeln: 75–100% verbraucht = Feature Freeze)

**Tags**: [nfr-007, error-budget, errorbudgetlow, warning, §2.4, §3.2, infra-test]

---

### TC-NFR007-029: ErrorBudgetExhausted-Alert bei vollstaendig verbrauchtem Budget [Infra-Test]

**Requirement**: NFR-007 §3.2 — Alert `ErrorBudgetExhausted` (≤ 0%), §2.4 Error Budget: Deployment-Stop
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- `slo:error_budget:remaining_ratio` ist <= 0

**Testschritte**:
1. `slo:error_budget:remaining_ratio` sinkt auf oder unter 0
2. Prometheus evaluiert `ErrorBudgetExhausted`-Alert fuer 5 Minuten
3. Engineer prueft Alertmanager und Benachrichtigungskanaele

**Erwartete Ergebnisse**:
- Alert `ErrorBudgetExhausted` erscheint als aktiver Critical-Alert
- PagerDuty und Slack #incidents erhalten Benachrichtigungen
- Die Meldung lautet: "Error Budget aufgebraucht — Deployment-Stop erforderlich"
- Die `runbook_url` zeigt auf `/runbooks/error-budget-exhausted`

**Nachbedingungen**:
- Deployment-Prozess wird gestoppt bis das Budget regeneriert (manueller Eingriff erforderlich)

**Tags**: [nfr-007, error-budget, exhausted, deployment-stop, critical, infra-test, §2.4, §3.2]

---

## 9. Kapazitaetswarnungen und Ressourcen-Metriken

*Abdeckung: NFR-007 §7.2 — Kapazitaetswarnungen, §3.2 Resource-Rules*

---

### TC-NFR007-030: HighCPUUsage-Alert bei mehr als 80% CPU-Last fuer 15 Minuten [Infra-Test]

**Requirement**: NFR-007 §3.2 — Alert `HighCPUUsage` (> 80%, 15 Minuten), §7.2 Kapazitaetswarnungen (Warning: > 70%)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Prometheus mit Resource-AlertingRules deployt
- Backend-Container-CPU-Limit ist konfiguriert (kube_pod_container_resource_limits)

**Testschritte**:
1. Backend wird mit synthetischer Last beaufschlagt (z.B. Lasttests mit k6), so dass CPU > 80% fuer 15 Minuten
2. Prometheus evaluiert `HighCPUUsage`-Bedingung
3. Engineer prueft Alertmanager nach 15 Minuten sustained Last

**Erwartete Ergebnisse**:
- Alert `HighCPUUsage` erscheint als Warning in Alertmanager
- Slack #alerts erhaelt: "Backend CPU > 80% seit 15 Minuten"
- Die `runbook_url` zeigt auf `/runbooks/high-cpu`
- Kein PagerDuty-Alert (Severity ist Warning)

**Nachbedingungen**:
- Last-Test beendet; Alert loest sich auf sobald CPU unter 80% faellt

**Tags**: [nfr-007, kapazitaet, cpu, high-cpu-usage, §3.2, §7.2, infra-test]

---

### TC-NFR007-031: ArangoDBDown-Alert nach 1 Minute Ausfall [Infra-Test]

**Requirement**: NFR-007 §3.2 — Alert `ArangoDBDown` (probe_success == 0, fuer 1 Minute)
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- ArangoDB-Probe (`job="arangodb-probe"`) ist konfiguriert im Blackbox Exporter
- ArangoDB wird gestoppt

**Testschritte**:
1. ArangoDB-Container wird gestoppt (`kubectl scale statefulset arangodb --replicas=0`)
2. Blackbox Exporter erkennt, dass `probe_success{job="arangodb-probe"}` == 0
3. Prometheus evaluiert Alert nach 1 Minute

**Erwartete Ergebnisse**:
- Alert `ArangoDBDown` erscheint als Critical in Alertmanager
- PagerDuty und Slack #incidents erhalten Benachrichtigungen innerhalb von 2 Minuten nach dem Stopp
- Die Summary lautet: "ArangoDB nicht erreichbar"
- Die `runbook_url` zeigt auf `/runbooks/arangodb-down`

**Nachbedingungen**:
- ArangoDB wieder gestartet; Alert loest sich auf (resolve_timeout 5m)

**Tags**: [nfr-007, arangodb-down, dependency-alert, critical, §3.2, infra-test]

---

### TC-NFR007-032: RedisDown-Alert nach 1 Minute Ausfall [Infra-Test]

**Requirement**: NFR-007 §3.2 — Alert `RedisDown` (probe_success == 0, fuer 1 Minute)
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Redis-Probe (`job="redis-probe"`) konfiguriert
- Redis wird gestoppt

**Testschritte**:
1. Redis-Container wird gestoppt
2. `probe_success{job="redis-probe"}` wechselt auf 0
3. Prometheus evaluiert Alert nach 1 Minute

**Erwartete Ergebnisse**:
- Alert `RedisDown` erscheint als Critical in Alertmanager
- PagerDuty und Slack #incidents werden benachrichtigt
- Summary: "Redis nicht erreichbar"
- `runbook_url`: `/runbooks/redis-down`

**Nachbedingungen**:
- Redis gestartet; Alert loest sich auf

**Tags**: [nfr-007, redis-down, dependency-alert, critical, §3.2, infra-test]

---

### TC-NFR007-033: DiskFillingUp-Alert bei prognostiziertem Volllaufen in < 7 Tagen [Infra-Test]

**Requirement**: NFR-007 §7.3 — Trend-Analyse, Alert `DiskFillingUp` (predict_linear)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- `predict_linear`-Rule fuer Disk deployt
- PVC-Disk-Fuellrate ist hoch genug, dass `predict_linear` < 7 Tage prognostiziert

**Testschritte**:
1. PVC wird kuenstlich gefuellt (z.B. durch grosse Log-Dateien oder Testdaten)
2. `predict_linear(kubelet_volume_stats_available_bytes[7d], 7*24*3600) < 0` wird wahr
3. Alert `DiskFillingUp` wird nach 1 Stunde ausgeloest

**Erwartete Ergebnisse**:
- Alert erscheint als Warning: "PVC wird voraussichtlich in < 7 Tagen voll"
- Slack #alerts erhaelt die Benachrichtigung
- `runbook_url`: `/runbooks/disk-filling-up`

**Nachbedingungen**:
- Disk bereinigen; Alert loest sich auf

**Tags**: [nfr-007, disk-filling-up, predict-linear, kapazitaetsplanung, §7.3, infra-test]

---

## 10. Bulkhead — Connection-Pool-Metriken

*Abdeckung: NFR-007 §4.4 — Bulkhead-Pattern, §6.2 Smoke-Tests (Metrics)*

---

### TC-NFR007-034: Connection-Pool-Metriken sind in /metrics sichtbar

**Requirement**: NFR-007 §4.4 — Bulkhead: connection_pool_active_connections und connection_pool_max_connections Prometheus-Gauge
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Backend laeuft mit aktivem Connection-Pool fuer ArangoDB, Redis und HTTP-Client

**Testschritte**:
1. Nutzer (oder Prober) oeffnet `https://api.kamerplanter.example.com/metrics`
2. Seite wird geladen

**Erwartete Ergebnisse**:
- Metrik `connection_pool_active_connections` mit Labels `pool_name="arangodb"`, `pool_name="redis"`, `pool_name="http_client"` ist vorhanden
- Metrik `connection_pool_max_connections` mit denselben Labels ist vorhanden
- ArangoDB-Pool-Maximum zeigt Wert 20 (`connection_pool_max_connections{pool_name="arangodb"} 20`)
- Redis-Pool-Maximum zeigt Wert 10 (`connection_pool_max_connections{pool_name="redis"} 10`)
- HTTP-Client-Pool-Maximum zeigt Wert 10 (`connection_pool_max_connections{pool_name="http_client"} 10`)
- Aktive Verbindungen liegen im normalen Betrieb unter dem Maximum

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, bulkhead, connection-pool, prometheus-metrics, §4.4]

---

### TC-NFR007-035: Circuit-Breaker-Zustand ist in /metrics sichtbar (0=closed, 1=half_open, 2=open)

**Requirement**: NFR-007 §4.1 — Circuit Breaker: circuit_breaker_state Prometheus-Gauge
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Backend laeuft mit implementiertem Circuit Breaker fuer ArangoDB, Redis und externe APIs
- Circuit Breaker befindet sich im Normalzustand (CLOSED)

**Testschritte**:
1. Nutzer oeffnet `https://api.kamerplanter.example.com/metrics`
2. Nutzer sucht nach der Metrik `circuit_breaker_state`

**Erwartete Ergebnisse**:
- Metrik `circuit_breaker_state` ist vorhanden
- Labels enthalten mindestens: `dependency="arangodb"`, `dependency="redis"`, `dependency="external_api"`
- Im Normalzustand zeigen alle Werte 0 (closed)
- Wertebereich: 0 (closed), 1 (half_open), 2 (open)

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, circuit-breaker, prometheus-gauge, metrics, §4.1]

---

## 11. Retry-Policy und Timeout-Verhalten (nutzerseitig sichtbar)

*Abdeckung: NFR-007 §4.2 — Retry-Policies, §4.3 — Timeouts*

---

### TC-NFR007-036: Kurzer Verbindungsausfall wird durch Retry transparent behoben

**Requirement**: NFR-007 §4.2 — Retry mit Exponential Backoff: max_retries=3, base_delay=0.5s
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- ArangoDB erleidet einen kurzfristigen Verbindungsunterbruch (< 2 Sekunden), der nach dem 2. Retry behoben ist

**Testschritte**:
1. Nutzer navigiert zur Artenliste
2. Waehrend des Ladens gibt es einen kurzen Verbindungsausfall (2 Retries erforderlich)
3. Nutzer wartet auf das Ergebnis

**Erwartete Ergebnisse**:
- Die Artenliste laedt erfolgreich (kein Fehler sichtbar)
- Kein Fehler-Snackbar erscheint (der Retry war transparent)
- Die Ladezeit kann geringfuegig laenger sein (bis zu ~2 Sekunden durch Retry-Delays)
- Der Nutzer bemerkt keinen Fehler

**Nachbedingungen**:
- Kein Systemzustand veraendert

**Tags**: [nfr-007, retry, exponential-backoff, transparenter-retry, §4.2]

---

### TC-NFR007-037: Nach 3 fehlgeschlagenen Retries erscheint eine Fehlermeldung

**Requirement**: NFR-007 §4.2 — Nach Erschoepfung der Retries (max_retries=3) wird Fehler weitergegeben
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- ArangoDB ist dauerhaft nicht erreichbar (alle 3 Retries schlagen fehl)

**Testschritte**:
1. Nutzer navigiert zur Artenliste
2. Alle 3 Retry-Versuche schlagen fehl (nach insgesamt ca. 3-4 Sekunden — base_delay * (2^0 + 2^1 + 2^2) = 3.5s + Jitter)
3. Nutzer betrachtet das Ergebnis

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Serverfehler..." oder "Service voruebergehend nicht verfuegbar"
- Die Fehlermeldung erscheint nach ca. 3-5 Sekunden (Retry-Delay-Summe + Jitter)
- Kein endloser Ladezustand ohne Feedback
- Der Nutzer kann es manuell erneut versuchen (Reload-Schaltflaeche oder Neuladen der Seite)

**Nachbedingungen**:
- Fehlerzustand bleibt bis zur Wiederherstellung der Verbindung bestehen

**Tags**: [nfr-007, retry, exhausted, fehlermeldung, §4.2]

---

### TC-NFR007-038: Request-Timeout nach 15 Sekunden fuer ArangoDB-Anfragen

**Requirement**: NFR-007 §4.3 — Timeouts: ArangoDB Gesamt-Timeout 15s
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- ArangoDB antwortet extrem langsam (z.B. durch Overload) — Request haengt nach > 15 Sekunden

**Testschritte**:
1. Nutzer klickt auf eine datenintensive Operation (z.B. komplexe Suche oder Listenaufruf)
2. ArangoDB antwortet nach 16 Sekunden immer noch nicht
3. Nutzer beobachtet, was passiert

**Erwartete Ergebnisse**:
- Nach maximal 15 Sekunden erscheint eine Timeout-Fehlermeldung
- Die Meldung lautet sinngemaeß: "Anfrage hat zu lange gedauert" oder "Zeitlimit ueberschritten"
- Das System haengt nicht laenger als 15 Sekunden
- Kein endloser Ladezustand nach dem Timeout

**Nachbedingungen**:
- Fehlerzustand wird nach Benutzer-Aktion (Retry oder Navigation) aufgeloest

**Tags**: [nfr-007, timeout, arangodb, 15-sekunden, fehlermeldung, §4.3]

---

## 12. Canary Deployment und Traffic-Verteilung

*Abdeckung: NFR-007 §6.3 — Canary Deployments (SOLL)*

---

### TC-NFR007-039: Canary Deployment — Rollback bei > 10% Degradation gegenueber Baseline [Infra-Test]

**Requirement**: NFR-007 §6.3 — Canary: Automatisches Rollback bei Verschlechterung > 10% gegenueber Baseline (SOLL)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Canary-Deployment-Mechanismus (Flagger oder Argo Rollouts) ist konfiguriert
- Eine neue Canary-Version wird deployed, die erhoehte Error Rate hat

**Testschritte**:
1. Neue Canary-Version wird deployed (initial 10% Traffic)
2. Canary hat eine Error Rate, die > 10% schlechter als die Baseline ist
3. Flagger/Argo Rollouts analysiert die Metriken

**Erwartete Ergebnisse**:
- Canary wird automatisch gestoppt und Rollback auf Baseline ausgefuehrt
- 100% Traffic wird wieder auf die stabile Baseline-Version geleitet
- Kein Nutzer erlebt dauerhaft Fehler durch die fehlerhafte Canary-Version
- CI/CD-Pipeline zeigt den Rollback-Status

**Nachbedingungen**:
- Prod laeuft wieder vollstaendig auf der Baseline-Version

**Tags**: [nfr-007, canary, rollback, flagger, §6.3, infra-test]

---

## 13. Incident-Management-Prozess

*Abdeckung: NFR-007 §5.1 — Incident-Schweregrade, §5.3 Incident-Lifecycle, §5.4 Post-Mortem-Pflicht*

---

### TC-NFR007-040: SEV-1-Incident wird innerhalb von 15 Minuten acknowledged [Infra-Test]

**Requirement**: NFR-007 §5.2 — Reaktionszeit SEV-1: ≤ 15 Minuten (Geschaeftszeiten), §3.4 Eskalation L1
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- On-Call-Rotation eingerichtet und aktiv
- PagerDuty/OpsGenie konfiguriert
- Simulierter SEV-1-Incident (API liefert nur 503)

**Testschritte**:
1. SEV-1-Incident wird ausgeloest (z.B. `ArangoDBDown` Critical Alert)
2. PagerDuty sendet Alert an On-Call-Engineer
3. On-Call-Engineer bestaetig den Alert (Acknowledge)
4. Reaktionszeit wird gemessen (Alert-Zeitstempel bis Acknowledge-Zeitstempel)

**Erwartete Ergebnisse**:
- Acknowledge erfolgt innerhalb von 15 Minuten waehrend Geschaeftszeiten
- Acknowledge erfolgt innerhalb von 30 Minuten ausserhalb Geschaeftszeiten
- Incident-Status wechselt von "Triggered" auf "Acknowledged" in PagerDuty

**Nachbedingungen**:
- Incident-Lifecycle setzt sich fort (Diagnose → Behebung → Closed)

**Tags**: [nfr-007, incident, sev1, reaktionszeit, acknowledge, §5.2, infra-test]

---

### TC-NFR007-041: Post-Mortem wird fuer SEV-2-Incident innerhalb von 5 Arbeitstagen erstellt [Infra-Test]

**Requirement**: NFR-007 §5.4 — Post-Mortem-Pflicht fuer Incidents ab SEV-2 innerhalb 5 Arbeitstage
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Ein SEV-2-Incident wurde abgeschlossen (Status "Closed")
- Post-Mortem-Template ist vorhanden

**Testschritte**:
1. SEV-2-Incident wird geschlossen
2. Zustaendiger Engineer erstellt Post-Mortem innerhalb von 5 Arbeitstagen
3. Post-Mortem enthaelt alle Pflichtbestandteile gemaess §5.4

**Erwartete Ergebnisse**:
- Post-Mortem enthaelt: Zusammenfassung, Timeline, Ursachenanalyse (5-Why), Auswirkung, Action Items, Lessons Learned
- Post-Mortem-Ton ist blameless (Fokus auf Systemverbesserung)
- Action Items haben Verantwortliche und Fristen
- Post-Mortem wird im Wiki/Dokumentationssystem veroeff entlicht

**Nachbedingungen**:
- Action Items werden verfolgt und umgesetzt

**Tags**: [nfr-007, post-mortem, sev2, incident-management, §5.4, infra-test]

---

### TC-NFR007-042: Wartungsfenster wird als Silence in Alertmanager eingetragen [Infra-Test]

**Requirement**: NFR-007 §3.5 — Alert-Fatigue-Praevention: geplante Wartungsfenster als Silence
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Alertmanager laeuft
- Ein geplantes Wartungsfenster ist bekannt (z.B. 03:00–05:00 Uhr)

**Testschritte**:
1. Engineer erstellt eine Silence in Alertmanager-UI: Zeitraum 03:00–05:00, alle Labels `namespace="agrotech-prod"`
2. Waehrend des Wartungsfensters wird eine geplante Aktion durchgefuehrt (z.B. Datenbankupdate)
3. Alerts werden ausgeloest (z.B. `ArangoDBDown` waehrend des Updates)

**Erwartete Ergebnisse**:
- Waehrend des Wartungsfensters werden keine Benachrichtigungen an PagerDuty oder Slack gesendet
- Nach Ende des Wartungsfensters (05:00) werden Alerts wieder normal geroutet
- Die Silence ist in Alertmanager-UI als aktiv sichtbar

**Nachbedingungen**:
- Silence verfaellt automatisch nach dem konfigurierten Endzeitpunkt

**Tags**: [nfr-007, silence, alertmanager, wartungsfenster, slo-ausschluss, §3.5, infra-test]

---

## Abdeckungsmatrix

| NFR-007-Abschnitt | Titel | Testfall-IDs |
|---|---|---|
| §2.1 SLI-Definitionen | Verfuegbarkeit, Latenz, Error Rate, Throughput | TC-NFR007-001, TC-NFR007-002, TC-NFR007-027 |
| §2.2 SLO-Definitionen | Verfuegbarkeit ≥ 99.5%, P95 < 500ms | TC-NFR007-027, TC-NFR007-022 |
| §2.4 Error Budgets | Budget-Regeln, Feature Freeze, Deployment-Stop | TC-NFR007-028, TC-NFR007-029 |
| §2.5 SLO-Recording-Rules | Prometheus-Recording-Rules | TC-NFR007-027 |
| §3.1 Alerting-Schweregrade | Critical/Warning/Info Routing | TC-NFR007-023, TC-NFR007-024 |
| §3.2 PrometheusRule-Definitionen | Alle Alerting-Regeln | TC-NFR007-023, TC-NFR007-024, TC-NFR007-025, TC-NFR007-028, TC-NFR007-029, TC-NFR007-030, TC-NFR007-031, TC-NFR007-032 |
| §3.3 Alertmanager-Konfiguration | Routing, Inhibition | TC-NFR007-023, TC-NFR007-024, TC-NFR007-025, TC-NFR007-042 |
| §3.4 Eskalationsstufen | L1–L4, Reaktionszeiten | TC-NFR007-023, TC-NFR007-040 |
| §3.5 Alert-Fatigue-Praevention | Inhibition, Silencing | TC-NFR007-025, TC-NFR007-042 |
| §3.6 Runbook-Pflicht | runbook_url-Annotation | TC-NFR007-026 |
| §4.1 Circuit Breaker | CLOSED/OPEN/HALF-OPEN, Prometheus-Gauge | TC-NFR007-014, TC-NFR007-015, TC-NFR007-035 |
| §4.2 Retry-Policies | Exponential Backoff, max_retries=3 | TC-NFR007-036, TC-NFR007-037 |
| §4.3 Timeouts | ArangoDB 15s, Redis 7s, extern 20s | TC-NFR007-017, TC-NFR007-038 |
| §4.4 Bulkhead-Pattern | Connection-Pool-Metriken | TC-NFR007-006, TC-NFR007-034 |
| §4.5 Graceful Degradation | Redis, TimescaleDB, Sensor, Celery | TC-NFR007-010, TC-NFR007-011, TC-NFR007-012, TC-NFR007-013 |
| §4.6 Rate Limiting | Retry-After, Human/Service-Limits | TC-NFR007-008, TC-NFR007-009 |
| §5.1 Incident-Schweregrade | SEV-1 bis SEV-4 | TC-NFR007-040, TC-NFR007-041 |
| §5.2 Reaktionszeiten | SEV-1 ≤ 15 Minuten | TC-NFR007-040 |
| §5.4 Post-Mortem-Pflicht | SEV-2, 5 Arbeitstage, blameless | TC-NFR007-041 |
| §5.5 Statuspage | Operational/Degraded/Outage | TC-NFR007-020, TC-NFR007-021, TC-NFR007-022 |
| §6.1 Externe Health-Checks | /health/live, /health/ready, API Smoke | TC-NFR007-001, TC-NFR007-002, TC-NFR007-003, TC-NFR007-004, TC-NFR007-005, TC-NFR007-007 |
| §6.2 Smoke-Tests nach Deployment | Health + API + Metrics, Rollback | TC-NFR007-006, TC-NFR007-018, TC-NFR007-019 |
| §6.3 Canary Deployments | Automatisches Rollback bei Degradation | TC-NFR007-039 |
| §7.2 Kapazitaetswarnungen | CPU, Memory, Disk, ArangoDB-Connections | TC-NFR007-030, TC-NFR007-031, TC-NFR007-032 |
| §7.3 Trend-Analyse | predict_linear, DiskFillingUp | TC-NFR007-033 |

## Testtyp-Verteilung

| Kategorie | Anzahl | IDs |
|---|---|---|
| Standard-E2E (Browser/HTTP-Client) | 12 | TC-NFR007-001 bis TC-NFR007-009, TC-NFR007-016, TC-NFR007-017, TC-NFR007-034, TC-NFR007-035 |
| **[Infra-Test]** (erfordert Monitoring-Stack) | 30 | alle uebrigen Testfaelle |

**Hinweis fuer Test-Planung**: Die Standard-E2E-Tests koennen in jeder Umgebung mit laufendem Backend ausgefuehrt werden (inkl. lokaler Entwicklungsumgebung via Skaffold). Die **[Infra-Test]**-Testfaelle erfordern einen vollstaendigen Kubernetes-Cluster mit Prometheus, Alertmanager, Grafana und optionalem Statuspage-Setup.
