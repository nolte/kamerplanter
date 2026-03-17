# Anforderungs-Widerspruchsanalyse

**Erstellt:** 2026-03-17
**Analysierte Dokumente:** 30 REQ-Dateien, 11 NFR-Dateien, 18 UI-NFR-Dateien (gesamt: 59)
**Gefundene Anforderungen:** ~110 funktionale Anforderungen (FA), ~85 non-funktionale Anforderungen (NFA)
**Widersprueche gesamt:** 18

---

## Executive Summary

Die Anforderungslandschaft von Kamerplanter ist insgesamt konsistent strukturiert und zeigt ausgereiftes Requirements Engineering. Die kritischsten Spannungen betreffen das Zusammenspiel des Light-Modus (REQ-027) mit DSGVO-Compliance-Anforderungen (REQ-025, UI-NFR-013), die Offline-Faehigkeit (UI-NFR-012) gegenueber dem Multi-Device-Echtzeit-Anspruch sowie die Retention-Matrix (NFR-011), die mit dem DSGVO-Loeschrecht (Art. 17) in einem unaufgeloesten Grundkonflikt steht. Fuenf weitere Widersprueche betreffen technische Inkompatibilitaeten zwischen Performance- und Sicherheitsanforderungen.

---

## Anforderungs-Index

### Funktionale Anforderungen (Auswahl der in Widerspruechsn relevanten)

| ID | Dokument | Bereich | Kurztext |
|----|----------|---------|----------|
| FA-001 | REQ-025 §1 | DSGVO | Nutzer kann Account und alle Daten loeschen lassen (Art. 17) |
| FA-002 | REQ-025 §1 | DSGVO | Erntedaten werden bei Loeschantrag anonymisiert (nicht geloescht) — CanG/PflSchG |
| FA-003 | REQ-027 §1 | Light-Modus | Light-Modus deaktiviert Auth, Tenants und DSGVO-Consent |
| FA-004 | REQ-027 §1.1 Szenario 2 | Light-Modus | Mehrere Geraete im LAN teilen denselben System-User |
| FA-005 | REQ-023 §1 | Auth | Refresh-Token mit 30 Tagen Laufzeit (persistent) |
| FA-006 | REQ-023 v1.2 | Auth | IP-Adressen werden nach 7 Tagen anonymisiert |
| FA-007 | REQ-004 §1 | Duengung | Silizium-Zusaetze werden als Erstes in den Tank gegeben |
| FA-008 | REQ-004 §1 | Duengung | CalMag wird vor Base-A und Base-B eingemischt |
| FA-009 | REQ-004 §1 | Duengung | Foliar-Anwendung in Bluetephase ab Woche 2 wird per Soft-Warnung blockiert |
| FA-010 | REQ-004 §1 | Duengung | IPM-Notfallbehandlungen sind von der Foliar-Warnung ausgenommen |
| FA-011 | REQ-007 §1 | Ernte | Karenzzeit-Gate blockiert Ernte bei noch laufenden IPM-Behandlungen |
| FA-012 | REQ-011 §1 | Anreicherung | Externe Stammdatenanreicherung benoetigt Einwilligung (optional) |
| FA-013 | REQ-021 §1 | UI-Modus | Backend liefert immer alle Daten; Filter ausschliesslich im Frontend |
| FA-014 | REQ-023 §1 | Auth | Access-Token TTL betraegt 15 Minuten |
| FA-015 | REQ-024 §1 | Multi-Tenant | Alle Ressourcen gehoeren zu genau einem Tenant |
| FA-016 | REQ-027 §1.1 | Light-Modus | System-User wird fuer alle Aktionen ohne Authentifizierung verwendet |
| FA-017 | REQ-020 §1 | Onboarding | Onboarding laeuft auch im Light-Modus ohne Login-Schritt |
| FA-018 | REQ-005 §1 | Sensorik | Automatische Sensor-Fallback-Kette: HA -> MQTT -> Wetter-API -> Manuell |
| FA-019 | REQ-018 §1 | Aktorik | Phasengebundene Aktoren-Profile werden bei Phasenwechsel automatisch angepasst |
| FA-020 | REQ-003 §1 | Phasen | Keine Rueckwaerts-Transitionen erlaubt |
| FA-021 | REQ-022 §1 | Pflege | Giesserinnerungen werden bei >5mm Regen-Vorhersage unterdrueckt (REQ-005-Integration) |
| FA-022 | REQ-013 §1 | Durchlauf | Mischkultur-Runs erlauben mehrere Arten pro Durchlauf |
| FA-023 | REQ-001 §2 | Stammdaten | Tenant kann Species-Zugaenge ausblenden (hidden-Flag) |
| FA-024 | REQ-028 §1 | Mischkultur | Companion-Planting-Empfehlungen basieren auf Graph-Edges |

### Non-Funktionale Anforderungen (Auswahl der in Widerspruechsn relevanten)

| ID | Dokument | Kategorie | Kurztext | Messbar? |
|----|----------|-----------|----------|----------|
| NFA-001 | NFR-007 §2.2 | Performance | API-Latenz P50 < 200ms | Ja |
| NFA-002 | NFR-007 §2.2 | Performance | API-Latenz P95 < 500ms | Ja |
| NFA-003 | NFR-007 §2.2 | Verfuegbarkeit | Uptime >= 99,5 % | Ja |
| NFA-004 | NFR-007 §4.3 | Resilience | Alle Netzwerkaufrufe haben explizite Timeouts | Ja |
| NFA-005 | NFR-008 §2.1 | Testing | Unit-Test-Coverage >= 80 % | Ja |
| NFA-006 | NFR-003 §1 | Code-Qualitaet | Gesamter Source Code auf Englisch | Ja |
| NFA-007 | NFR-011 §2.1 | DSGVO | Soft-Deleted Accounts nach 90 Tagen Hard-Delete | Ja |
| NFA-008 | NFR-011 §2.3 | DSGVO/Gesetz | Erntedaten mind. 5 Jahre aufbewahren (CanG) | Ja |
| NFA-009 | NFR-011 §2.1 | DSGVO | IP-Adressen nach 7 Tagen anonymisiert | Ja |
| NFA-010 | NFR-011 §2.2 | DSGVO | Sensordaten-Rohdaten nach 90 Tagen geloescht/aggregiert | Ja |
| NFA-011 | UI-NFR-003 §2.1 | Performance | First Contentful Paint < 1,5 Sekunden | Ja |
| NFA-012 | UI-NFR-003 §2.1 | Performance | Interaction to Next Paint (INP) < 200ms | Ja |
| NFA-013 | UI-NFR-012 §2 | Offline | PWA muss offline-faehig sein; Daten werden offline erfasst und spaeter synchronisiert | Ja |
| NFA-014 | UI-NFR-012 §3 | Offline | Offline-Konflikte werden automatisch zusammengefuehrt (Last-Write-Wins) | Ja |
| NFA-015 | UI-NFR-013 §3.1 | Consent | Consent-Banner erscheint beim ersten Besuch (Full-Modus) | Ja |
| NFA-016 | UI-NFR-013 §3.1 | Consent | App bleibt ohne Einwilligung voll funktionsfaehig | Ja |
| NFA-017 | UI-NFR-002 §2.1 | Barrierefreiheit | WCAG 2.1 Level AA | Ja |
| NFA-018 | NFR-001 §6 | Sicherheit | JWT Access-Token TTL 15 Minuten (Abweichung von NFR-001 §6.1 explizit dokumentiert) | Ja |
| NFA-019 | NFR-001 §5 | Sicherheit | Alle sensiblen Daten muessen verschluesselt gespeichert werden | Nein (kein konkretes Algorithmus-Ziel) |
| NFA-020 | NFR-007 §4.6 | Rate Limiting | Per-Client 100 Req/min; Service Accounts ebenfalls (REQ-023 v1.7) | Ja |
| NFA-021 | NFR-011 §2.1 R-04 | DSGVO | Consent-Records 3 Jahre nach Widerruf behalten (Nachweispflicht) | Ja |
| NFA-022 | REQ-025 §1 | DSGVO | Widerruf einer Einwilligung muss sofort wirksam sein | Nein (kein Zeitlimit angegeben) |
| NFA-023 | UI-NFR-001 §2.3 | Layout | Kein festes maxWidth auf dem Content-Container | Ja |
| NFA-024 | NFR-002 §1 | Infrastruktur | Kubernetes als verpflichtende Produktionsplattform | Ja |
| NFA-025 | NFR-007 §4.5 | Resilience | Redis-Ausfall degradiert zu direkten DB-Abfragen statt Totalausfall | Ja |

---

## Kritische Widersprueche

### W-001: DSGVO-Loeschrecht vs. Gesetzliche Aufbewahrungspflicht (Wertkonflikt)

**Typ:** Impliziter Widerspruch (rechtlich unvermeidbar, aber Umgang nicht vollstaendig definiert)
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `FA-001` in `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` §1: "Nutzer kann vollstaendige Loeschung seines Accounts und aller zugehoerigen Daten beantragen"
- `FA-002` in `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` §1 Szenario 3: "Erntedaten/Behandlungen: User-Referenz anonymisiert, Daten bleiben (CanG/PflSchG)"
- `NFA-008` in `spec/nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md` §2.3 R-16: "Erntedaten mind. 5 Jahre, Behandlungsanwendungen mind. 3 Jahre"

**Konflikt:** REQ-025 formuliert als User Story das "Recht auf vollstaendige Loeschung". NFR-011 definiert einen Loeschvorgang, der fuer gesetzlich geschuetzte Daten nur Anonymisierung (keine Loeschung) vorsieht. Das ist rechtlich korrekt (Art. 17 Abs. 3 lit. b DSGVO), aber die UI-seitige Kommunikation an den Nutzer ist ungeklaert. Der Nutzer erhaelt eine "Bestaetigung der Loeschung", obwohl anonymisierte Erntedaten technisch weiterhin existieren.

**Auswirkung:** Irreführende Nutzerkommunikation — der Nutzer glaubt, alle Daten seien geloescht, obwohl anonymisierte Chargen weiterhin in `harvest_batches` und `treatment_applications` bestehen. Potentiell unzureichende Erfullung der Transparenzpflicht (Art. 5 Abs. 1 lit. a DSGVO).

**Loesungsoptionen:**
1. **Transparente Kommunikation:** UI-Text bei Loeschanfrage explizit klarstellen: "Ihr Account und personenbezogene Daten werden geloescht. Erntedokumentation und IPM-Behandlungsnachweise, die gesetzlichen Aufbewahrungsfristen unterliegen (CanG, PflSchG), werden anonymisiert — d.h. ohne Personenbezug aufbewahrt." REQ-025 und UI-NFR-013 entsprechend erganzen.
2. **Datenschutzerklaerung-Ergaenzung:** Im Datenschutzdialog (REQ-025) explizite Sektion "Gesetzliche Aufbewahrungspflichten" einfuegen, die vor der Loeschanfrage auf diesen Umstand hinweist.
3. **Loeschbestaetigung aufteilen:** API-Response `/api/v1/privacy/deletion-requests` unterscheidet zwischen `fully_deleted_categories` und `anonymized_categories` und gibt beide Listen in der Bestaetigung aus.

---

### W-002: Light-Modus deaktiviert DSGVO-Consent — Fehlende Abgrenzung fuer Mehrgeraete-Szenario

**Typ:** Direkter Widerspruch
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `FA-003` in `spec/req/REQ-027_Light-Modus.md` §1: "Light-Modus deaktiviert Auth, Tenants und DSGVO-Consent-Banner"
- `FA-004` in `spec/req/REQ-027_Light-Modus.md` §1.1 Szenario 2: "Mehrere Geraete im LAN — alle Aktionen werden dem System-User zugeordnet"
- `NFA-015` in `spec/ui-nfr/UI-NFR-013_Einwilligungsmanagement-Consent.md` §3.1 CB-001: "Beim ersten Besuch eines neuen Nutzers MUSS ein Consent-Banner angezeigt werden"
- `NFA-019` in `spec/nfr/NFR-001_Separation-of-Concerns.md` §5: "Alle sensiblen Daten verschluesselt"

**Konflikt:** REQ-027 gibt explizit an, dass im Light-Modus kein Consent-Banner erscheint ("kein Consent-Banner"). UI-NFR-013 stellt als MUSS-Anforderung auf, dass beim ersten Besuch *eines neuen Nutzers* ein Consent-Banner erscheint. Im LAN-Familiennutzungs-Szenario (Szenario 2 in REQ-027) greifen mehrere verschiedene Personen ohne eigenen Account zu — die DSGVO definiert diese als unterschiedliche betroffene Personen. Ob fuer Light-Modus-Deployments ueberhaupt eine DSGVO-Pflicht gilt (Haushaltsausnahme Art. 2 Abs. 2 lit. c DSGVO), ist in den Anforderungen nicht erwaehnt oder abgegrenzt.

**Auswirkung:** Wenn das Deployment das Heimnetzwerk verlaesst (z.B. VPN-Zugriff, Cloud-Hosting im Light-Modus), entstehen DSGVO-Compliance-Luecken. Es fehlt eine klare Trennlinie, wann der Light-Modus rechtlich zulaessig ist.

**Loesungsoptionen:**
1. **Ausnahmedefinition in REQ-027 erganzen:** Explizit auf die Haushaltsausnahme (DSGVO Art. 2 Abs. 2 lit. c) Bezug nehmen und den Light-Modus auf Deployments im privaten Haushalt beschraenken. Deployment-Doku muss dies klarstellen.
2. **Vereinfachtes Consent im Light-Modus:** Statt vollstaendigem Consent-Banner ein einfaches First-Use-Modal "Diese Instanz laeuft ohne Accountsystem. Alle Aktionen werden lokal gespeichert. Sentry (optional): [Ja/Nein]" — minimal, aber rechtlich abgesicherter.
3. **Light-Modus auf localhost erzwingen:** Konfiguration prueft, ob das System von localhost/127.0.0.1 oder einer RFC-1918-Adresse zugegriffen wird; ausserhalb dieser Grenzen wird automatisch in den Full-Modus gewechselt.

---

### W-003: Offline-Faehigkeit (PWA) vs. Echtzeit-Sensorik und Aktoren-Steuerung

**Typ:** Impliziter Widerspruch (CAP-Theorem-Variante)
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `NFA-013` in `spec/ui-nfr/UI-NFR-012_PWA-Offline.md` §2: "PWA muss offline-faehig sein; Beobachtungen koennen ohne Verbindung erfasst werden"
- `NFA-014` in `spec/ui-nfr/UI-NFR-012_PWA-Offline.md` §3: "Offline-Konflikte werden per Last-Write-Wins zusammengefuehrt"
- `FA-018` in `spec/req/REQ-005_Hybrid-Sensorik.md` §1: "Automatische Fallback-Kette mit Echtzeit-Daten von Home Assistant"
- `FA-019` in `spec/req/REQ-018_Umgebungssteuerung.md` §1: "Phasengebundene Aktoren-Profile werden bei Phasenwechsel automatisch angepasst"
- `FA-011` in `spec/req/REQ-007_Erntemanagement.md`: "Karenzzeit-Gate blockiert Ernte bei laufenden IPM-Behandlungen"

**Konflikt:** UI-NFR-012 spezifiziert, dass kritische Aktionen (Aufgaben abhaken, Beobachtungen erfassen, Pflanzenzustand aendern) offline ausgefuehrt werden koennen. Gleichzeitig erfordern mehrere FAs serverseitige Validierungen, die ohne Netzwerkverbindung nicht durchfuehrbar sind:
- Das Karenzzeit-Gate (FA-011) muss IPM-Behandlungsdaten aus dem Server pruefe — offline nicht moeglich.
- Phasengebundene Aktoren (FA-019) werden serverseitig ausgeloest — ein Offline-Phasenwechsel kann den Aktor nicht steuern.
- Last-Write-Wins (NFA-014) bei Konflikten ist fuer Safety-kritische Daten (Behandlungsanwendungen, Karenzzeiten) ungeeignet: Wenn ein Nutzer offline eine Ernte anlegt (und so das Karenzzeit-Gate umgeht), entsteht ein Datenproblem.

**Auswirkung:** Bei Offline-Phasenuebergaengen koennen Safety-Checks (Karenzzeit, HST-Validierung) umgangen werden. Last-Write-Wins ist fuer Ernte- und Behandlungsdaten potentiell gefaehrlich.

**Loesungsoptionen:**
1. **Offline-Schutzbereich definieren:** UI-NFR-012 muss eine Liste von "offline-erlaubten Aktionen" und "nur-online-Aktionen" definieren. Karenzzeit-Gate, Phasenuebergang mit Aktoren-Trigger und Ernteerstellung sind Only-Online.
2. **Optimistic-Locking mit Konflikt-Eskalation:** Statt Last-Write-Wins fuer Safety-relevante Entitaeten eine Konflikt-Eskalation implementieren — bei Konflikten an diesen Daten wird dem Nutzer manuell zur Auflosung aufgefordert.
3. **Offline-Modus-Kennung in Events:** Jedes offline erstellte Event erhaelt ein Flag `created_offline: true` und wird nach Sync server-seitig gegen alle Safety-Gates nochmal validiert. Bei Verletzung wird das Event zurueckgewiesen und der Nutzer informiert.

---

## Hohe Widersprueche

### W-004: NFR-001 JWT-Skizze vs. REQ-023 — Library und Token-TTL-Konflikt (teilweise aufgeloest, Rest offen)

**Typ:** Direkter Widerspruch (teilweise selbst-deklariert aufgeloest)
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `NFA-018` in `spec/nfr/NFR-001_Separation-of-Concerns.md` §6.1: "JWT mit `python-jose`, Access Token 1 Stunde TTL"
- `FA-014` in `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` §1: "Access-Token TTL 15 Minuten, Authlib statt python-jose"

**Konflikt:** REQ-023 loest den Widerspruch per Changelog-Eintrag auf (REQ-023 "ersetzt NFR-001 §6.1") und listet die Abweichungen in einer Tabelle. Problematisch ist jedoch, dass NFR-001 v2.2 das Dokument weiterhin unveraendert vorhaelt — §6.1 referenziert `python-jose` und 1h-TTL. Ein Entwickler, der zuerst NFR-001 liest, erhaelt widerspruchliche Vorgaben. Das NFR-001-Dokument selbst wurde nicht aktualisiert.

**Auswirkung:** Neues Entwickler-Onboarding kann NFR-001 als autoritativer lesen und falsche Implementierungsentscheidungen treffen. Technische Schulden durch zwei widerspruchliche autoritaere Quellen.

**Loesungsoptionen:**
1. **NFR-001 §6.1 aktualisieren:** Querverweise auf REQ-023 einfuegen, den python-jose-Abschnitt mit "DEPRECATED — siehe REQ-023 v1.1" markieren und Token-TTL auf 15 Minuten anpassen.
2. **Single Source of Truth erzwingen:** In der Anforderungs-Governance festlegen, dass Auth-Parameter ausschliesslich in REQ-023 definiert werden; NFR-001 §6.1 auf einen Hinweis kuerzen.

---

### W-005: Performance-Anforderungen vs. Ende-zu-Ende-Verschluesselung und kryptographische Signaturen

**Typ:** Impliziter Widerspruch (technisch schwer vereinbar)
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `NFA-001` in `spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md` §2.2: "API-Latenz P50 < 200ms"
- `NFA-002` in `spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md` §2.2: "API-Latenz P95 < 500ms"
- `NFA-019` in `spec/nfr/NFR-001_Separation-of-Concerns.md` §5: "Alle sensiblen Daten verschluesselt"
- `NFA-012` in `spec/ui-nfr/UI-NFR-003_Performance.md` §2.1: "INP < 200ms"
- `FA-007` in `spec/req/REQ-004_Duenge-Logik.md` §1: "CalMag-Korrektur-Berechnung aus Wasserquelle bei jeder Anfrage"

**Konflikt:** NFR-001 §5 verlangt, dass "alle sensiblen Daten verschluesselt" werden, ohne den Begriff "sensibel" zu definieren oder einen konkreten Verschluesselungsalgorithmus vorzuschreiben (NFA-019 ist nicht messbar). Wenn dies als "alle ArangoDB-Felder mit sensiblen Werten werden transparent verschluesselt" interpretiert wird, ist das mit den Latenz-SLOs (NFA-001/002) kaum vereinbar, weil per-field encryption jeden Lese-/Schreibvorgang verzoegert. REQ-004s berechnungsintensive EC-Budget-Kalkulation und die WaterMixCalculator-Calls koennen die P50-Grenze ueberschreiten.

**Auswirkung:** Unklare Verschluesselungsanforderungen fuehren zu Interpretationsspielraum, der entweder zu Performance-Problemen (zu viel Verschluesselung) oder zu Sicherheitsluecken (zu wenig) fuehrt.

**Loesungsoptionen:**
1. **NFR-001 §5 praezisieren:** "Sensibel" auf konkrete Felder eingrenzen: Passworter (bcrypt), API-Keys (SHA-256 Hash), HA-Tokens (AES-256-GCM). Datenbankdaten-at-rest werden per ArangoDB-eigener Verschluesselung geschuetzt — kein per-field-encryption.
2. **Performance-Budget fuer rechenintensive Endpoints:** Fuer REQ-004 Berechnungs-Endpoints (EC-Budget, WaterMixCalculator) separates P95-Budget von 1000ms definieren — nicht das generische 500ms-Ziel.
3. **Caching fuer repetitive Berechnungen:** REQ-004-Berechnungen (die auf unveraenderten Stammdaten basieren) koennen gecachet werden (Redis), um Latenz-SLOs einzuhalten.

---

### W-006: Rate-Limiting fuer Service Accounts vs. Home-Assistant-Integration

**Typ:** Priorisierungs-Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `NFA-020` in `spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md` §4.6: "Per-Client 100 Requests/Minute"
- `FA-005` / REQ-023 v1.4: "Service Accounts fuer Home Assistant, API-Key-only, Rate Limit 1000 req/min"
- `FA-018` in `spec/req/REQ-005_Hybrid-Sensorik.md`: "Home Assistant liefert Echtzeit-Sensor-Daten"

**Konflikt:** NFR-007 §4.6 setzt ein Rate-Limit von 100 Requests/Minute pro Client. REQ-023 v1.4 gibt an, dass M2M-API-Keys (fuer Service Accounts wie Home Assistant) ein Rate-Limit von 1000 req/min haben. Bei intensiver Sensor-Erfassung durch Home Assistant (z.B. alle 30 Sekunden mehrere Sensoren bei mehreren Sites) koennen selbst 1000 req/min unter Last nicht ausreichen. Zudem ist unklar, ob das globale Limit (1000 req/min, NFR-007 §4.6 "Global alle Clients") bei vielen HA-Instanzen gegenuber dem per-Client-Limit priorisiert wird.

**Auswirkung:** Sensordaten koennen durch Rate-Limiting verlorengehen, was die Kernfunktionalitaet von REQ-005 beeintraechtigt.

**Loesungsoptionen:**
1. **Burst-Mode fuer Service Accounts:** Fuer `account_type: 'service'` ein separates Rate-Limit definieren (z.B. 10.000 req/min), das vom Per-Client-Limit getrennt ist.
2. **Batch-Sensor-Endpoint:** REQ-005 einen `/batch-observations`-Endpoint hinzufuegen, der mehrere Sensor-Datenpunkte in einem einzigen Request verarbeitet — reduziert Request-Anzahl erheblich.
3. **Rate-Limit-Hierarchie in NFR-007 formalisieren:** Globales Limit, Per-Client-Human-Limit und Per-Client-Service-Limit explizit als drei separate Ebenen definieren.

---

### W-007: Offline-Phasenwechsel und servieseitige Phasenvalidierung

**Typ:** Impliziter Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `NFA-013` in `spec/ui-nfr/UI-NFR-012_PWA-Offline.md`: "Offline erfasste Daten automatisch synchronisiert"
- `FA-020` in `spec/req/REQ-003_Phasensteuerung.md`: "Keine Rueckwaerts-Transitionen erlaubt (serverseitige Validierung)"
- REQ-006 §1: "HST-Validierung: Topping in Bluetephase verboten (serverseitig)"

**Konflikt:** UI-NFR-012 erlaubt das Erfassen von Beobachtungen und Aktionen offline. REQ-003 implementiert die Phasenvalidierung (keine Rueckwaerts-Transitionen) serverseitig. Wenn ein Nutzer offline einen Phasenwechsel durchfuehrt und dann einen weiteren offline-Phasenwechsel zurueck zur vorherigen Phase, entstehen nach der Synchronisation zwei widerspruchliche Transitionen. Die Last-Write-Wins-Strategie (NFA-014) wuerde den zweiten Wechsel anwenden — damit wird eine eigentlich verbotene Rueckwaerts-Transition durchgefuehrt.

**Auswirkung:** Ungueltiger Phasenstatus nach Offline-Synchronisation koennte falsche Pflegeerinnerungen, falsche Aktoren-Steuerung und ungultige HST-Validierungen ausloesen.

**Loesungsoptionen:**
1. **Phasenwechsel als Offline-verbotene Aktion klassifizieren (bevorzugt):** In UI-NFR-012 Phasenwechsel als "requires-connectivity"-Aktion markieren. Das Frontend zeigt eine Meldung "Phasenwechsel erfordert Netzwerkverbindung".
2. **Serverseitige Conflict-Resolution fuer Phasen:** Bei Sync wird serverseitig die Phasen-Timeline validiert; ungueltige Transitionen werden abgelehnt und der Nutzer zur manuellen Auflosung aufgefordert.

---

### W-008: DSGVO-Consent-Banner vs. Light-Modus-Vereinfachung

**Typ:** Direkter Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `NFA-015` in `spec/ui-nfr/UI-NFR-013_Einwilligungsmanagement-Consent.md` §3.1: "Consent-Banner beim ersten Besuch MUSS erscheinen"
- `NFA-016` in `spec/ui-nfr/UI-NFR-013_Einwilligungsmanagement-Consent.md` §3.1 CB-005: "App bleibt ohne Einwilligung voll funktionsfaehig"
- `FA-016` in `spec/req/REQ-027_Light-Modus.md` §1.1: "Kein Consent-Banner im Light-Modus"
- `FA-012` in `spec/req/REQ-011_Externe-Stammdatenanreicherung.md`: "Stammdaten-Anreicherung benoetigt Einwilligung"

**Konflikt:** UI-NFR-013 CB-001 stellt als MUSS-Anforderung auf, dass der Consent-Banner bei jedem neuen Nutzer erscheint. REQ-027 deaktiviert dies fuer den Light-Modus explizit. Die Stammdaten-Anreicherung (REQ-011) ist eine opt-in-Funktion, die laut UI-NFR-013 §3.2 CK-003 Einwilligung erfordert. Im Light-Modus koennte die Anreicherung also ohne Einwilligung laufen — ein DSGVO-Problem, wenn der Light-Modus nicht als Haushalts-Deployment gilt.

**Auswirkung:** Im Light-Modus wird Anreicherung moeglicherweise ohne Einwilligung durchgefuehrt. Wenn REQ-011-Anreicherung im Light-Modus aktiviert ist, ist die Rechtsgrundlage unklar.

**Loesungsoptionen:**
1. **REQ-027 erganzen:** Im Light-Modus wird REQ-011-Anreicherung standardmaessig deaktiviert. Aktivierbar nur ueber explizite Konfigurationsoption `ENABLE_ENRICHMENT_LIGHTMODE=true`.
2. **Minimal-Consent im Light-Modus:** Ein einmaliges Opt-in-Modal beim ersten Start (kein Banner, nur ein Dialog "Moechten Sie automatische Pflanzendaten-Anreicherung aktivieren?") wuerde die rechtliche Grundlage schaffen.

---

## Mittlere Widersprueche

### W-009: Sensordaten-Retention vs. Pflanzenpflege-Historienverfolgung

**Typ:** Zeitlicher Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `NFA-010` in `spec/nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md` §2.2 R-14: "Sensor-Rohdaten nach 90 Tagen aggregiert (Stundenmittel)"
- `FA-018` in `spec/req/REQ-005_Hybrid-Sensorik.md`: "Historische Datenanalyse fuer Plausibilitaetspruefung"
- REQ-003 §2: "VPD-Verlauf und Klimadaten sind Basis fuer Phasenempfehlungen"

**Konflikt:** NFR-011 loescht Sensor-Rohdaten nach 90 Tagen. REQ-003 und REQ-005 verlangen historische Sensordaten fuer Plausibilitaetspruefungen und Phasenanalyse. Bei mehrzyklischen Outdoor-Pflanzen oder mehrjaehrigen Perennials (Obstbaeume, Stauden) liegen relevante Vergleichszyklen mehr als 90 Tage zurueck. Stundenmittel (Stufe 2) sind fuer bestimmte Analysen unzureichend (z.B. kurzzeitige Temperaturspitzen die Pflanzenreaktionen auslosten).

**Auswirkung:** Qualitaetsverlust bei der Phasenanalyse und Pflegeoptimierung fuer mehrjaehrige Pflanzen. Historische Abweichungs-Analysen ("Warum gab es Frost-Schaden im letzten Maerz?") werden nach 90 Tagen unmoglich.

**Loesungsoptionen:**
1. **Differenzierte Retention per Sensortyp:** Klimatische Extremwerte (Frost-Ereignisse, Hitzewellen — erkannt durch Schwellwerte) als Events in ArangoDB dauerhaft archivieren, unabhaengig von der Timeseries-Aggregierung.
2. **Retention-Ausnahme fuer Phase-Transition-Snapshots:** Beim Phasenwechsel werden relevante Sensordaten des letzten Zyklus als `PhaseSummary`-Dokument archiviert (nicht loeschpflichtig, da kein Personenbezug).
3. **Laengere Rohdaten-Retention konfigurierbar:** `SENSOR_RAW_RETENTION_DAYS` (Standard 90) koennte auf 180 Tage fuer Perennial-Anlagen erhoehen.

---

### W-010: Stammdaten-Scoping (REQ-001 v4.0) vs. Companion-Planting-Graph (REQ-028)

**Typ:** Scope-Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `FA-023` in `spec/req/REQ-001_Stammdatenverwaltung.md` §2 v4.0: "Tenant kann Species-Zugaenge ausblenden (`hidden: true` in TenantSpeciesConfig)"
- `FA-024` in `spec/req/REQ-028_Mischkultur-Companion-Planting.md`: "Companion-Planting-Empfehlungen basieren auf `compatible_with`/`incompatible_with` Graph-Edges zwischen Species"
- `FA-022` in `spec/req/REQ-013_Pflanzdurchlauf.md` §1: "Mischkultur-Runs erlauben mehrere Arten pro Durchlauf"

**Konflikt:** REQ-001 v4.0 erlaubt es Tenants, bestimmte Species aus ihrer Sicht auszublenden (`hidden: true`). REQ-028 berechnet Companion-Planting-Empfehlungen ueber alle `compatible_with`-Kanten des Graphen. Wenn eine Species, die als idealer Begleiter einer anderen Species gilt, vom Tenant ausgeblendet wurde, erscheint sie nicht in der Companion-Planting-Empfehlung — obwohl sie botanisch relevant und die Kante vorhanden waere. Die `hidden`-Logik in REQ-001 ist auf Tenant-UI-Filterung ausgerichtet, aber es ist unklar, ob sie auch auf Graph-Traversal-Ergebnisse wirkt.

**Auswirkung:** Inkonsistente oder unvollstaendige Companion-Planting-Empfehlungen bei Tenants mit angepasstem Stammdaten-Scope.

**Loesungsoptionen:**
1. **Klare Abgrenzung in REQ-028:** "Companion-Planting-Empfehlungen traversieren alle globalen Species-Kanten, unabhaengig von TenantSpeciesConfig.hidden. Die Empfehlungen zeigen jedoch nur Species an, fuer die der Tenant `tenant_has_access` besitzt." — so ist die Graph-Intaktitiheit gewahrt, aber die Darstellung ist tenant-gefiltert.
2. **Warnung in REQ-001 erganzen:** `hidden: true` filtert nur die direkte Listenansicht; Graph-Traversals (Companion-Planting, Fruchtfolge) verwenden weiterhin alle verbundenen Species.

---

### W-011: Erfahrungsstufen-UI (REQ-021) vs. Vollstaendige CRUD-Anforderung (NFR-010)

**Typ:** Qualitaets-Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `FA-013` in `spec/req/REQ-021_UI-Erfahrungsstufen.md` §1: "Im Einsteiger-Modus werden ausgeblendete Felder mit Defaults befuellt; keine Information geht verloren"
- REQ-021 §3.1: "Im Einsteiger-Modus sind Species-Felder wie `allelopathy_score`, `root_type`, `critical_day_length_hours` ausgeblendet"
- NFR-010 §2.1: "Jede Entitaet MUSS vollstaendige CRUD-UI unterstuetzen"

**Konflikt:** NFR-010 fordert, dass jede Entitaet vollstaendige Pflegemasken hat. REQ-021 blendet im Einsteiger-Modus Felder aus und befuellt sie mit Defaults. Wenn ein Einsteiger eine Species anlegt, werden kritische Felder (z.B. `frost_sensitivity`, `nutrient_demand_level`) mit Defaults gesetzt, die moeglicherweise falsch sind — und der Einsteiger sieht keine Moeglichkeit, diese zu korrigieren, ohne den Modus zu wechseln. NFR-010 verlangt "Bearbeiten"-Funktion fuer alle Felder — im Einsteiger-Modus sind aber manche Felder im Edit-Dialog nicht sichtbar.

**Auswirkung:** Daten koennen mit falschen Defaults in der Datenbank landen und ohne Modusswechsel nicht korrigiert werden. NFR-010 und REQ-021 haben unterschiedliche Interpretationen von "Pflegetiefe".

**Loesungsoptionen:**
1. **"Mehr anzeigen" explizit fuer kritische Felder hervorheben:** Wenn Defaults gesetzt wurden, erscheint nach dem Speichern ein Hinweis "X Felder wurden automatisch gesetzt. Klicken Sie hier, um diese anzupassen." — Low-Friction-Weg, Defaults zu korrigieren.
2. **Defaults mit Vertrauensstufe versehen:** Felder die per Auto-Fill gesetzt wurden, werden mit einem kleinen "automatisch" -Badge in der Detailansicht markiert — auch im Einsteiger-Modus sichtbar.
3. **NFR-010 erganzen:** "Vollstaendige CRUD" bedeutet, dass alle Felder editierbar sind, entweder direkt oder ueber den "Mehr anzeigen"-Toggle (REQ-021). Diese Kombination gilt als NFR-010-konform.

---

### W-012: Nutrient-Plan-Gantt-Visualisierung vs. UI-NFR-003 Performance

**Typ:** Qualitaets-Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- REQ-004 §1 (Gantt-Diagramm): "Interaktives Gantt-Diagramm mit Hover-Tooltips, horizontalem Scrolling bei >16 Wochen, Balken pro Duenger und Phase"
- `NFA-011` in `spec/ui-nfr/UI-NFR-003_Performance.md` §2.1: "FCP < 1,5s"
- `NFA-012` in `spec/ui-nfr/UI-NFR-003_Performance.md` §2.1: "INP < 200ms"
- UI-NFR-003 §2.3 R-012: "Schwere Komponenten (Charts) sollen per Dynamic Import lazily geladen werden (SOLL)"

**Konflikt:** Ein komplexes Gantt-Diagramm (12-20 Wochen, 8-15 Dünger-Zeilen, Phasenhintergruende, Hover-Tooltips) ist eine schwere Komponente. Bei mehreren gleichzeitig geladenen Nährstoffplaenen (NutrientPlanDetailPage) und ohne expliziten Lazy-Load-Befehl in REQ-004 koennte die INP-Grenze von 200ms ueberschritten werden. REQ-004 beschreibt die Visualisierung sehr detailliert, ohne Lazy Loading zu erwaehnen. UI-NFR-003 R-012 ist ein SOLL (nicht MUSS).

**Auswirkung:** Performance-Degradierung auf Low-End-Geraeten bei komplexen Nährstoffplaenen. FCP-Ziel koennte nicht eingehalten werden, wenn das Gantt initial gerendert wird.

**Loesungsoptionen:**
1. **REQ-004 Gantt-Abschnitt erganzen:** Gantt wird per Dynamic Import lazily geladen; initialer Tab zeigt die Text-Listenansicht. Umschalten auf Gantt-Ansicht loest den Load aus.
2. **Virtualisierung:** Gantt-Balken ausserhalb des Viewports werden nicht gerendert (Intersection Observer). Standard fuer lange Timelines.

---

### W-013: Giessdienst-Rotation (REQ-024) vs. DSGVO-Loeschrecht (REQ-025)

**Typ:** Zeitlicher Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- REQ-024 §1.2 v1.2 (Giessdienst-Rotation): "DutyRotation-Nodes: wer hatte wann Dienst — vollstaendige Historie"
- REQ-025 §1: "Recht auf Loeschung — alle personenbezogenen Daten des Nutzers werden geloescht"
- NFR-011 §2.1 R-01: "User-Accounts nach 90 Tagen Hard-Delete"

**Konflikt:** DutyRotation-Eintraege enthalten Personenbezug (User-Referenz auf Mitglieder). Wenn ein Mitglied seinen Account loescht, muss die User-Referenz aus der Rotationshistorie entfernt werden. Ob die Rotationshistorie selbst behalten (mit anonymisiertem User-Verweis) oder mitgeloescht werden soll, ist nicht spezifiziert. Dies ist eine Luecke in der Retention-Matrix (NFR-011) — DutyRotation-Collection fehlt.

**Auswirkung:** DSGVO-Loeschanfragen koennen DutyRotation-Eintraege nicht vollstaendig bereinigen, weil kein Retention-Verhalten definiert ist.

**Loesungsoptionen:**
1. **NFR-011 Retention-Matrix erganzen:** DutyRotation-Eintraege mit geloeschtem User werden anonymisiert (User-Referenz auf NULL gesetzt, Dienst-Zeitraum bleibt). Kein Hard-Delete notwendig, da kein Personenbezug nach Anonymisierung.
2. **REQ-024 erganzen:** Expliziter Hinweis, dass DutyRotation bei Loeschanfrage anonymisiert wird (analog Ernte-/Behandlungsdaten in REQ-025).

---

### W-014: Feedback-System (REQ-006 Aufgabenbewertungen) vs. NFR-011 Retention

**Typ:** Zeitlicher Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- REQ-006 §1 "Vollstaendige Einzelaufgaben-Pflege": "Bewertungen nach Abschluss: `difficulty_rating`, `quality_rating` — System lernt durchschnittliche Schwierigkeitsgrade"
- NFR-011 §2.1: Retention-Matrix deckt Aufgaben-Bewertungen nicht ab

**Konflikt:** REQ-006 spezifiziert ein Lern-System fuer Aufgabenbewertungen. Diese Bewertungen sind an User-IDs geknuepft und damit personenbezogen. Die NFR-011 Retention-Matrix erwaehnt Tasks-Collection nicht. Wenn ein User geloescht wird, ist unklar, was mit seinen Bewertungen passiert. Aggregierte Lern-Daten (Durchschnittsschwierigkeit pro Template) koennten dem Tenant erhalten bleiben — User-bezogene Einzel-Bewertungen muessen aber bei Loeschung bereinigt werden.

**Auswirkung:** Potenzieller Datenleck von Bewertungsdaten nach Account-Loeschung.

**Loesungsoptionen:**
1. **NFR-011 erganzen:** `tasks` und `workflow_executions` Collections in die Retention-Matrix aufnehmen. Beim Hard-Delete eines Users: User-Referenz auf NULL setzen, Bewertungen beibehalten (keine PII mehr nach Anonymisierung).
2. **REQ-006 erganzen:** Expliziter DSGVO-Hinweis "Bewertungen werden bei Kontoloeschung anonymisiert (Personenbezug entfernt, Aggregat-Daten bleiben)".

---

## Niedrige Widersprueche und redaktionelle Inkonsistenzen

### W-015: NFR-003 spezifiziert mypy, aber REQ-Dokumente beschreiben Python-3.14-Typannotationen inkonsistent

**Typ:** Redaktionelle Inkonsistenz
**Schweregrad:** NIEDRIG

- NFR-003 §4.1 erwaehnt `mypy` als verpflichtenden Type-Checker.
- CLAUDE.md nennt Python 3.14+ und "Pydantic v2, `type` keyword for aliases (not TypeAlias)".
- REQ-Dokumente (z.B. REQ-001) verwenden `Optional[str]` und `list[str]` gemischt — ersteres ist Python 3.9+ kompatibel, letzteres ist der neue Stil ab Python 3.10+. Bei Python 3.14 sollte konsistent der neue Stil (`str | None` statt `Optional[str]`) verwendet werden.

**Loesungsvorschlag:** NFR-003 um ein Kapitel "Python-Versions-spezifischer Stil" erganzen, das den bevorzugten Stil fuer Type Annotations bei Python 3.10+ definiert.

---

### W-016: Misch-Reihenfolge in REQ-004 — Silizium vor CalMag vs. Herstellerempfehlungen

**Typ:** Fachlicher Selbst-Widerspruch
**Schweregrad:** NIEDRIG

- REQ-004 §1 Liste: "1. Wasser, 2. Silizium (zuerst!), 3. CalMag, 4. Base A, 5. Base B..."
- REQ-004 §1 Hinweis: "Die Zuordnung A/B variiert je nach Hersteller. Die tatsaechliche Reihenfolge wird ueber das `mixing_priority`-Feld des Fertilizer-Modells gesteuert."

**Konflikt:** Die fest codierte Liste im Text widerspricht dem Hinweis, dass die Reihenfolge durch das Modell gesteuert wird. Ein Entwickler liest die Liste als normative Vorgabe; ein anderer liest den Hinweis als "das ist konfigurierbar". Die Liste sollte als Beispiel deklariert werden, nicht als Fest-Reihenfolge.

**Loesungsvorschlag:** Ueberschrift der Liste aendern von impliziter Fest-Reihenfolge zu "Empfohlene Standardreihenfolge (ueberschreibbar per `mixing_priority`)".

---

### W-017: Wasser-Defaults-Kaskade in REQ-004 vs. REQ-014 — Doppeldefinition

**Typ:** Scope-Widerspruch
**Schweregrad:** NIEDRIG

- REQ-004 §1 (CalMag-Korrektur aus Wasserquelle): Beschreibt WaterMixCalculator, der EC_mix aus Tap/RO-Verhaeltnis berechnet.
- REQ-014 §1 (Wasserquellen-Defaults-Kaskade): Beschreibt eine 4-stufige Kaskade fuer TankFillEvent-Felder.
- REQ-004-A §1: Formalisiert die Berechnungspipeline.

**Konflikt:** Drei Dokumente beschreiben teilweise dieselbe WaterMixCalculator-Logik mit leicht abweichenden Details. REQ-004 erwaehnt den `WaterMixCalculator` als Engine-Klasse. REQ-014 beschreibt dieselbe Kaskade auf Event-Ebene. REQ-004-A formalisiert die Mathematik. Es ist unklar, wo die Single Source of Truth liegt.

**Loesungsvorschlag:** REQ-004-A explizit als "Single Source of Truth fuer EC-Budget-Mathematik" kennzeichnen. REQ-004 und REQ-014 verweisen auf REQ-004-A statt eigene Berechnungsbeschreibungen vorzuhalten.

---

### W-018: Technische Dokumentationssprache vs. Anforderungsdokument-Sprache

**Typ:** Redaktionelle Inkonsistenz
**Schweregrad:** NIEDRIG

- NFR-003 §1: "Der gesamte Source Code MUSS auf Englisch verfasst werden."
- Anforderungsdokumente (spec/**/*.md): Vollstaendig auf Deutsch verfasst.
- CLAUDE.md: "Documentation is written in German; source code must be in English only (NFR-003)."

**Konflikt:** NFR-003 gilt explizit nur fuer Source Code, nicht fuer Dokumentation. CLAUDE.md bestaetigt das. Kein eigentlicher Widerspruch, aber Klarstellungsbedarf: NFR-003 sollte explizit erwaehnen, dass Spezifikationsdokumente von der Englisch-Pflicht ausgenommen sind, um Fehlinterpretation zu verhindern.

**Loesungsvorschlag:** NFR-003 §1 um einen Satz erganzen: "Ausgenommen von der Englisch-Pflicht sind Spezifikationsdokumente (spec/**/*.md) und Nutzer-facing Dokumentation, die auf Deutsch verfasst werden."

---

## Nicht messbare NFAs mit Handlungsbedarf

Folgende non-funktionale Anforderungen sind nicht praezise genug formuliert und sollten praeziisiert werden:

| ID | Dokument | Text | Empfehlung |
|----|----------|------|------------|
| NFA-019 | NFR-001 §5 | "Alle sensiblen Daten muessen verschluesselt gespeichert werden" | Konkrete Felder definieren: Passwoerter (bcrypt), API-Keys (SHA-256 Hash gespeichert), HA-Token (AES-256-GCM), Rest: Datenbankebene-Verschluesselung |
| NFA-022 | REQ-025 §1 | "Widerruf muss sofort wirksam sein" | Konkrete SLA: "Widerruf propagiert innerhalb von max. 5 Sekunden an alle aktiven Sitzungen" oder "Widerruf gilt ab naechstem API-Request" |
| REQ-025 §1 | REQ-025 | "Art. 15 DSGVO — Auskunft in angemessener Zeit" | Konkrete Frist: DSGVO Art. 12 Abs. 3 gibt 1 Monat vor — diesen Wert als SLA einpflegen |

---

## Fehlende Anforderungen (Luecken)

Folgende Bereiche sind in den Dokumenten nicht abgedeckt oder unvollstaendig:

1. **Notification-Delivery-Kanal (N-003):** REQ-022 generiert Pflegeerinnerungen als Celery-Tasks, aber der Zustellkanal (E-Mail, Push, In-App) ist nicht spezifiziert. MEMORY.md erwaehnt dies als bekannte Luecke.

2. **KI/Bilderkennung (N-001):** Photo-basierte Pflanzenerkennung fehlt komplett — als zukuenftige Anforderung bekannt (MEMORY.md), aber noch kein REQ-Dokument vorhanden.

3. **DutyRotation in NFR-011-Retention-Matrix:** REQ-024 v1.2 fuegt DutyRotation hinzu, aber NFR-011 §2.1 erwaehnt diese Collection nicht. Personenbezug ist vorhanden.

4. **BulletinPost und SharedShoppingList (REQ-024 v1.2):** Diese Collections enthalten User-Referenzen — keine Retention-Regel in NFR-011.

5. **REQ-016 InvenTree-Integration:** Als "optional" markiert, aber kein Hinweis auf Fallback-Verhalten wenn InvenTree nicht verfuegbar ist (Impact auf Tank-/Lagerbestandsdaten).

6. **TimescaleDB-Deployment im Light-Modus:** REQ-027 beschreibt den Light-Modus fuer lokale Deployments, aber REQ-005/NFR-011 setzen TimescaleDB voraus. Ob TimescaleDB in einer Light-Mode-docker-compose Pflicht oder Optional ist, fehlt.

---

## Aufloesungsstatus

Alle 18 Widersprueche wurden am 2026-03-17 in den betroffenen Anforderungsdokumenten aufgeloest:

| ID | Schwere | Status | Geaenderte Dokumente | Massnahme |
|----|---------|--------|---------------------|-----------|
| W-001 | KRITISCH | AUFGELOEST | REQ-025 | User Story, Loesch-Tab und Abnahmekriterien praezisiert: transparente Unterscheidung `fully_deleted` vs. `anonymized` |
| W-002 | KRITISCH | AUFGELOEST | REQ-027, UI-NFR-013 | DSGVO-Haushaltsausnahme (Art. 2 Abs. 2 lit. c) explizit referenziert; externe Anreicherung im Light-Modus standardmaessig deaktiviert; CB-001 um Light-Modus-Ausnahme ergaenzt |
| W-003 | KRITISCH | AUFGELOEST | UI-NFR-012 | Neuer Abschnitt 3.3a "Offline-Schutzbereich": Phasenwechsel, Ernteerstellung, Aktoren-Trigger, Behandlungsanwendungen als Requires-Connectivity klassifiziert (R-020a bis R-020f) |
| W-004 | HOCH | BEREITS GELOEST | NFR-001 | §6.1 war bereits als "ABGELOEST" markiert mit Verweis auf REQ-023 |
| W-005 | HOCH | AUFGELOEST | NFR-001 | Neue Verschluesselungs-Scope-Tabelle in §5.2: bcrypt (Passwoerter), SHA-256 (API-Keys), AES-256-GCM (HA-Tokens), Encryption-at-Rest (ArangoDB RocksDB) |
| W-006 | HOCH | AUFGELOEST | NFR-007 | Rate-Limiting-Hierarchie: Human (100/min), Service Account (1.000/min), Batch (10.000/min); Batch-Sensor-Endpoint empfohlen |
| W-007 | HOCH | AUFGELOEST | UI-NFR-012 | Durch W-003 mitabgedeckt (R-020a: Phasenwechsel als Requires-Connectivity) |
| W-008 | HOCH | AUFGELOEST | UI-NFR-013 | CB-001 um Light-Modus-Ausnahme ergaenzt (Haushaltsausnahme + deaktivierte Anreicherung) |
| W-009 | MITTEL | AUFGELOEST | NFR-011 | ClimateEvent-Archivierung fuer Extremwerte (kein Personenbezug); konfigurierbare Rohdaten-Retention |
| W-010 | MITTEL | AUFGELOEST | REQ-028 | Klarstellung: Graph-Traversal traversiert alle Edges unabhaengig von `hidden`; Ergebnisse gefiltert nach `tenant_has_access` |
| W-011 | MITTEL | AUFGELOEST | NFR-010 | Klarstellung: REQ-021 "Mehr anzeigen"-Toggle erfuellt NFR-010 CRUD-Pflicht; "Automatisch gesetzt"-Badge empfohlen |
| W-012 | MITTEL | AUFGELOEST | REQ-004 | Gantt-Diagramm: Dynamic Import (React.lazy) Pflicht; Intersection Observer fuer Virtualisierung |
| W-013 | MITTEL | AUFGELOEST | NFR-011 | DutyRotation (R-19) in Retention-Matrix aufgenommen: Anonymisierung bei User-Loeschung |
| W-014 | MITTEL | AUFGELOEST | NFR-011 | Task-Bewertungen (R-22) und BulletinPost/SharedShoppingList (R-20, R-21) in Retention-Matrix aufgenommen |
| W-015 | NIEDRIG | AUFGELOEST | NFR-003 | Python 3.14+ Type Annotation Style explizit definiert: `str | None`, `list[str]`, `type`-Statement |
| W-016 | NIEDRIG | AUFGELOEST | REQ-004 | Misch-Reihenfolge als "Empfohlene Standard-Reihenfolge (ueberschreibbar per mixing_priority)" gekennzeichnet |
| W-017 | NIEDRIG | AUFGELOEST | REQ-004 | REQ-004 explizit als Single Source of Truth fuer EC-Budget-Mathematik und WaterMixCalculator markiert |
| W-018 | NIEDRIG | AUFGELOEST | NFR-003 | Klarstellung: Englisch-Pflicht gilt nur fuer Source Code; Spezifikationen und Nutzer-Doku sind Deutsch |

---

*Analyse erstellt am 2026-03-17. Alle Widersprueche aufgeloest am 2026-03-17.*
