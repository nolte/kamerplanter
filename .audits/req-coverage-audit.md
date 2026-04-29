---
review-type: req-coverage-audit
target-repo: kamerplanter
total-count: 72
req-count: 37
nfr-count: 16
ui-nfr-count: 19
manifest-coverage: 72/72
plans-open: 28
plans-closed: 44
repo-revision: 91d527be
created: 2026-04-29
mode: full
---

## Scope
Vollstaendiger Manifest-getriebener Coverage-Audit ueber alle 37 REQ + 16 NFR + 19 UI-NFR. Manifest-Quelle: `.claude/skills/req-coverage-audit/expectations.yaml`. Pro Anforderung mit Coverage < 100 % wurde ein eigenstaendiger Per-Anforderungs-Plan unter `.audits/req-coverage-audit/<ID>.md` mit konkreten Aufgaben + Akzeptanzkriterien angelegt.

## Manifest-Vollstaendigkeit
- Alle Anforderungen im Manifest: **72/72**
- Vollstaendigkeit OK — keine Manifest-Luecken.

## Verteilung gesamt
- Implementiert: 44 (61 %)
- Teilweise: 9 (12 %)
- Lueckenhaft: 8 (11 %)
- Spezifiziert: 8 (11 %)
- Idee: 3 (4 %)

## Coverage-Uebersicht: REQ — Funktional

| ID | Titel | Backend | Frontend | Tests | Score | Status | Plan |
|---|---|---|---|---|---|---|---|
| REQ-001 | Stammdatenverwaltung | 6/6 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-002 | Standortverwaltung | 5/5 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-003 | Phasensteuerung | 5/5 | 2/2 | 2/2 | 100% | Implementiert | — |
| REQ-004 | Duenge-Logik | 11/11 | 5/5 | 3/3 | 100% | Implementiert | — |
| REQ-004-A | EC-Budget-Kalkulation | 1/1 | n/a | 1/1 | 100% | Implementiert | — |
| REQ-005 | Hybrid-Sensorik | 6/6 | 2/2 | 3/3 | 100% | Implementiert | — |
| REQ-006 | Aufgabenplanung | 5/5 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-007 | Erntemanagement | 4/4 | 3/3 | 2/2 | 100% | Implementiert | — |
| REQ-008 | Post-Harvest | 0/3 | 0/1 | 0/2 | 12% | Spezifiziert | [Plan](req-coverage-audit/REQ-008.md) |
| REQ-009 | Dashboard | 0/2 | 1/1 | 2/2 | 75% | Teilweise | [Plan](req-coverage-audit/REQ-009.md) |
| REQ-010 | IPM-System | 7/7 | 4/4 | 2/2 | 100% | Implementiert | — |
| REQ-011 | Externe-Stammdatenanreicherung | 6/6 | n/a | 2/2 | 100% | Implementiert | — |
| REQ-012 | Stammdaten-Import | 7/7 | 2/2 | 3/3 | 100% | Implementiert | — |
| REQ-013 | Pflanzdurchlauf | 7/7 | 3/3 | 3/3 | 88% | Teilweise | [Plan](req-coverage-audit/REQ-013.md) |
| REQ-014 | Tankmanagement | 4/4 | 2/2 | 3/3 | 88% | Teilweise | [Plan](req-coverage-audit/REQ-014.md) |
| REQ-015 | Kalenderansicht | 5/5 | 4/4 | 3/3 | 88% | Teilweise | [Plan](req-coverage-audit/REQ-015.md) |
| REQ-015-A | Aussaatkalender-Berechnungsregeln | 1/1 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-016 | InvenTree-Integration | 0/2 | n/a | 0/1 | 0% | Spezifiziert | [Plan](req-coverage-audit/REQ-016.md) |
| REQ-017 | Vermehrungsmanagement | 0/4 | 0/1 | 0/1 | 12% | Spezifiziert | [Plan](req-coverage-audit/REQ-017.md) |
| REQ-018 | Umgebungssteuerung | 1/4 | 0/1 | 1/2 | 31% | Lueckenhaft | [Plan](req-coverage-audit/REQ-018.md) |
| REQ-019 | Substratverwaltung | 5/5 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-020 | Onboarding-Wizard | 5/5 | 2/2 | 2/2 | 100% | Implementiert | — |
| REQ-021 | UI-Erfahrungsstufen | 2/2 | 4/4 | 1/1 | 100% | Implementiert | — |
| REQ-022 | Pflegeerinnerungen | 5/5 | 2/2 | 2/2 | 88% | Teilweise | [Plan](req-coverage-audit/REQ-022.md) |
| REQ-023 | Benutzerverwaltung-Authentifizierung | 14/14 | 4/4 | 3/3 | 88% | Teilweise | [Plan](req-coverage-audit/REQ-023.md) |
| REQ-024 | Mandantenverwaltung-Gemeinschaftsgaerten | 10/10 | 3/3 | 3/3 | 88% | Teilweise | [Plan](req-coverage-audit/REQ-024.md) |
| REQ-025 | Datenschutz-Betroffenenrechte | 5/5 | 0/1 | 2/3 | 54% | Lueckenhaft | [Plan](req-coverage-audit/REQ-025.md) |
| REQ-026 | Aquaponik-Management | 0/2 | 0/1 | 0/1 | 12% | Spezifiziert | [Plan](req-coverage-audit/REQ-026.md) |
| REQ-027 | Light-Modus | 4/4 | n/a | 2/3 | 72% | Teilweise | [Plan](req-coverage-audit/REQ-027.md) |
| REQ-028 | Mischkultur-Companion-Planting | 4/4 | 2/2 | 3/3 | 100% | Implementiert | — |
| REQ-029 | KI-Bilderkennung-Pflanzenidentifikation | 0/3 | 0/1 | 0/1 | 25% | Spezifiziert | [Plan](req-coverage-audit/REQ-029.md) |
| REQ-030 | Benachrichtigungssystem | 5/5 | 2/2 | 2/2 | 100% | Implementiert | — |
| REQ-031 | KI-Assistent-Pflanzenberatung | 1/3 | 0/1 | 1/2 | 46% | Lueckenhaft | [Plan](req-coverage-audit/REQ-031.md) |
| REQ-032 | Druckansichten-Export | 3/3 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-033 | MCP-Server | 0/2 | n/a | 0/1 | 33% | Lueckenhaft | [Plan](req-coverage-audit/REQ-033.md) |
| REQ-035 | KI-Fachbegriff-Glossar | 0/2 | 1/2 | 0/1 | 38% | Lueckenhaft | [Plan](req-coverage-audit/REQ-035.md) |
| REQ-036 | KI-Diagnose-Assistent | 0/2 | 0/1 | 0/1 | 25% | Spezifiziert | [Plan](req-coverage-audit/REQ-036.md) |

## Coverage-Uebersicht: NFR — Cross-cutting

| ID | Titel | Artefakte | Validierung | Score | Status | Plan |
|---|---|---|---|---|---|---|
| NFR-001 | Separation of Concerns | 6/6 | n/a | 100% | Implementiert | — |
| NFR-002 | Kubernetes-Plattform | 3/3 | 1/1 | 100% | Implementiert | — |
| NFR-003 | Code-Standard Linting (English-only) | 3/3 | 2/2 | 100% | Implementiert | — |
| NFR-004 | Lokale Entwicklungsumgebung mit Skaffold | 1/1 | n/a | 100% | Implementiert | — |
| NFR-005 | Technische Dokumentation (MkDocs) | 4/4 | 1/1 | 100% | Implementiert | — |
| NFR-006 | API-Fehlerbehandlung mit Tracking-ID | n/a | 1/1 | 100% | Implementiert | — |
| NFR-007 | Betriebsstabilitaet & Monitoring | 2/2 | n/a | 100% | Implementiert | — |
| NFR-008 | Teststrategie & Testprotokoll | 3/3 | 1/1 | 100% | Implementiert | — |
| NFR-008a | E2E-Selenium-Teststandard | 3/3 | 1/1 | 100% | Implementiert | — |
| NFR-009 | Dependency-Management | 4/4 | n/a | 100% | Implementiert | — |
| NFR-010 | UI-Pflegemasken & Listenansichten | 3/3 | 1/1 | 100% | Implementiert | — |
| NFR-011 | Vorratsdatenspeicherung & Aufbewahrungsfristen | 1/2 | 1/1 | 67% | Teilweise | [Plan](req-coverage-audit/NFR-011.md) |
| NFR-012 | Cloud-Provider & Enterprise-Skalierung | n/a | n/a | 100% | Implementiert | — |
| NFR-013 | Speicheranbindung & Object-Storage | 0/1 | n/a | 50% | Lueckenhaft | [Plan](req-coverage-audit/NFR-013.md) |
| NFR-014 | Nuclei-Security-Scanning | 0/1 | n/a | 50% | Lueckenhaft | [Plan](req-coverage-audit/NFR-014.md) |
| NFR-015 | OWASP-ZAP-Security-Scanning | 0/1 | n/a | 50% | Lueckenhaft | [Plan](req-coverage-audit/NFR-015.md) |

## Coverage-Uebersicht: UI-NFR — Frontend

| ID | Titel | Artefakte | Validierung | Score | Status | Plan |
|---|---|---|---|---|---|---|
| UI-NFR-001 | Responsive Design | 1/1 | n/a | 100% | Implementiert | — |
| UI-NFR-002 | Barrierefreiheit | 1/1 | 1/1 | 100% | Implementiert | — |
| UI-NFR-003 | Performance | n/a | n/a | — | Idee | [Plan](req-coverage-audit/UI-NFR-003.md) |
| UI-NFR-004 | Feedback (Loading/Error/Empty States) | 3/3 | 2/2 | 100% | Implementiert | — |
| UI-NFR-005 | Navigation | 1/1 | n/a | 100% | Implementiert | — |
| UI-NFR-006 | Design-System | 2/2 | n/a | 100% | Implementiert | — |
| UI-NFR-007 | Internationalisierung | 3/3 | 1/1 | 100% | Implementiert | — |
| UI-NFR-008 | Formulare | 4/4 | 1/1 | 100% | Implementiert | — |
| UI-NFR-009 | Visual Identity & Brand Design | 1/1 | n/a | 100% | Implementiert | — |
| UI-NFR-010 | Tabellen & Datenansichten | 1/1 | 1/1 | 100% | Implementiert | — |
| UI-NFR-011 | Fachbegriff-Erklaerungen | 1/1 | 1/1 | 100% | Implementiert | — |
| UI-NFR-012 | PWA-Offline | 0/1 | n/a | 0% | Spezifiziert | [Plan](req-coverage-audit/UI-NFR-012.md) |
| UI-NFR-013 | Einwilligungsmanagement (Consent) | 0/1 | n/a | 0% | Spezifiziert | [Plan](req-coverage-audit/UI-NFR-013.md) |
| UI-NFR-014 | Auth-Initialisierung & Seitenreload | 1/1 | n/a | 100% | Implementiert | — |
| UI-NFR-015 | HA Lovelace Custom Cards | n/a | n/a | — | Idee | [Plan](req-coverage-audit/UI-NFR-015.md) |
| UI-NFR-016 | Phasen-Zyklus-Visualisierungen | 3/3 | n/a | 100% | Implementiert | — |
| UI-NFR-017 | Seitenlayout & Seitenueberschriften | 1/1 | 1/1 | 100% | Implementiert | — |
| UI-NFR-018 | Herkunftskennzeichnung Stammdaten | 1/1 | 1/1 | 100% | Implementiert | — |
| UI-NFR-019 | Kiosk-Modus | n/a | n/a | — | Idee | [Plan](req-coverage-audit/UI-NFR-019.md) |

## Roadmap (priorisierter Ausfuehrungsplan)
Sortiert nach Prioritaet (blocker > warning > info) und Coverage-Score (aufsteigend):

| # | Anforderung | Typ | Status | Score | Aufwand | Plan |
|---|---|---|---|---|---|---|
| 1 | REQ-016 InvenTree-Integration | req | Spezifiziert | 0% | L | [Plan](req-coverage-audit/REQ-016.md) |
| 2 | UI-NFR-012 PWA-Offline | ui-nfr | Spezifiziert | 0% | M | [Plan](req-coverage-audit/UI-NFR-012.md) |
| 3 | UI-NFR-013 Einwilligungsmanagement (Consent) | ui-nfr | Spezifiziert | 0% | M | [Plan](req-coverage-audit/UI-NFR-013.md) |
| 4 | REQ-008 Post-Harvest | req | Spezifiziert | 12% | L | [Plan](req-coverage-audit/REQ-008.md) |
| 5 | REQ-017 Vermehrungsmanagement | req | Spezifiziert | 12% | L | [Plan](req-coverage-audit/REQ-017.md) |
| 6 | REQ-026 Aquaponik-Management | req | Spezifiziert | 12% | L | [Plan](req-coverage-audit/REQ-026.md) |
| 7 | REQ-029 KI-Bilderkennung-Pflanzenidentifikation | req | Spezifiziert | 25% | L | [Plan](req-coverage-audit/REQ-029.md) |
| 8 | REQ-036 KI-Diagnose-Assistent | req | Spezifiziert | 25% | L | [Plan](req-coverage-audit/REQ-036.md) |
| 9 | REQ-018 Umgebungssteuerung | req | Lueckenhaft | 31% | L | [Plan](req-coverage-audit/REQ-018.md) |
| 10 | REQ-033 MCP-Server | req | Lueckenhaft | 33% | M | [Plan](req-coverage-audit/REQ-033.md) |
| 11 | REQ-035 KI-Fachbegriff-Glossar | req | Lueckenhaft | 38% | L | [Plan](req-coverage-audit/REQ-035.md) |
| 12 | REQ-031 KI-Assistent-Pflanzenberatung | req | Lueckenhaft | 46% | L | [Plan](req-coverage-audit/REQ-031.md) |
| 13 | NFR-013 Speicheranbindung & Object-Storage | nfr | Lueckenhaft | 50% | M | [Plan](req-coverage-audit/NFR-013.md) |
| 14 | NFR-014 Nuclei-Security-Scanning | nfr | Lueckenhaft | 50% | M | [Plan](req-coverage-audit/NFR-014.md) |
| 15 | NFR-015 OWASP-ZAP-Security-Scanning | nfr | Lueckenhaft | 50% | M | [Plan](req-coverage-audit/NFR-015.md) |
| 16 | REQ-025 Datenschutz-Betroffenenrechte | req | Lueckenhaft | 54% | M | [Plan](req-coverage-audit/REQ-025.md) |
| 17 | NFR-011 Vorratsdatenspeicherung & Aufbewahrungsfristen | nfr | Teilweise | 67% | M | [Plan](req-coverage-audit/NFR-011.md) |
| 18 | REQ-027 Light-Modus | req | Teilweise | 72% | M | [Plan](req-coverage-audit/REQ-027.md) |
| 19 | REQ-009 Dashboard | req | Teilweise | 75% | M | [Plan](req-coverage-audit/REQ-009.md) |
| 20 | REQ-013 Pflanzdurchlauf | req | Teilweise | 88% | M | [Plan](req-coverage-audit/REQ-013.md) |
| 21 | REQ-014 Tankmanagement | req | Teilweise | 88% | M | [Plan](req-coverage-audit/REQ-014.md) |
| 22 | REQ-015 Kalenderansicht | req | Teilweise | 88% | M | [Plan](req-coverage-audit/REQ-015.md) |
| 23 | REQ-022 Pflegeerinnerungen | req | Teilweise | 88% | M | [Plan](req-coverage-audit/REQ-022.md) |
| 24 | REQ-023 Benutzerverwaltung-Authentifizierung | req | Teilweise | 88% | M | [Plan](req-coverage-audit/REQ-023.md) |
| 25 | REQ-024 Mandantenverwaltung-Gemeinschaftsgaerten | req | Teilweise | 88% | M | [Plan](req-coverage-audit/REQ-024.md) |
| 26 | UI-NFR-003 Performance | ui-nfr | Idee | — | S | [Plan](req-coverage-audit/UI-NFR-003.md) |
| 27 | UI-NFR-015 HA Lovelace Custom Cards | ui-nfr | Idee | — | S | [Plan](req-coverage-audit/UI-NFR-015.md) |
| 28 | UI-NFR-019 Kiosk-Modus | ui-nfr | Idee | — | S | [Plan](req-coverage-audit/UI-NFR-019.md) |

## Plan-Index (alphabetisch, alle offenen Plans)
| Anforderung | Plan | Coverage | Aufwand |
|---|---|---|---|
| NFR-011 Vorratsdatenspeicherung & Aufbewahrungsfristen | [.audits/req-coverage-audit/NFR-011.md](req-coverage-audit/NFR-011.md) | 67% | M |
| NFR-013 Speicheranbindung & Object-Storage | [.audits/req-coverage-audit/NFR-013.md](req-coverage-audit/NFR-013.md) | 50% | M |
| NFR-014 Nuclei-Security-Scanning | [.audits/req-coverage-audit/NFR-014.md](req-coverage-audit/NFR-014.md) | 50% | M |
| NFR-015 OWASP-ZAP-Security-Scanning | [.audits/req-coverage-audit/NFR-015.md](req-coverage-audit/NFR-015.md) | 50% | M |
| REQ-008 Post-Harvest | [.audits/req-coverage-audit/REQ-008.md](req-coverage-audit/REQ-008.md) | 12% | L |
| REQ-009 Dashboard | [.audits/req-coverage-audit/REQ-009.md](req-coverage-audit/REQ-009.md) | 75% | M |
| REQ-013 Pflanzdurchlauf | [.audits/req-coverage-audit/REQ-013.md](req-coverage-audit/REQ-013.md) | 88% | M |
| REQ-014 Tankmanagement | [.audits/req-coverage-audit/REQ-014.md](req-coverage-audit/REQ-014.md) | 88% | M |
| REQ-015 Kalenderansicht | [.audits/req-coverage-audit/REQ-015.md](req-coverage-audit/REQ-015.md) | 88% | M |
| REQ-016 InvenTree-Integration | [.audits/req-coverage-audit/REQ-016.md](req-coverage-audit/REQ-016.md) | 0% | L |
| REQ-017 Vermehrungsmanagement | [.audits/req-coverage-audit/REQ-017.md](req-coverage-audit/REQ-017.md) | 12% | L |
| REQ-018 Umgebungssteuerung | [.audits/req-coverage-audit/REQ-018.md](req-coverage-audit/REQ-018.md) | 31% | L |
| REQ-022 Pflegeerinnerungen | [.audits/req-coverage-audit/REQ-022.md](req-coverage-audit/REQ-022.md) | 88% | M |
| REQ-023 Benutzerverwaltung-Authentifizierung | [.audits/req-coverage-audit/REQ-023.md](req-coverage-audit/REQ-023.md) | 88% | M |
| REQ-024 Mandantenverwaltung-Gemeinschaftsgaerten | [.audits/req-coverage-audit/REQ-024.md](req-coverage-audit/REQ-024.md) | 88% | M |
| REQ-025 Datenschutz-Betroffenenrechte | [.audits/req-coverage-audit/REQ-025.md](req-coverage-audit/REQ-025.md) | 54% | M |
| REQ-026 Aquaponik-Management | [.audits/req-coverage-audit/REQ-026.md](req-coverage-audit/REQ-026.md) | 12% | L |
| REQ-027 Light-Modus | [.audits/req-coverage-audit/REQ-027.md](req-coverage-audit/REQ-027.md) | 72% | M |
| REQ-029 KI-Bilderkennung-Pflanzenidentifikation | [.audits/req-coverage-audit/REQ-029.md](req-coverage-audit/REQ-029.md) | 25% | L |
| REQ-031 KI-Assistent-Pflanzenberatung | [.audits/req-coverage-audit/REQ-031.md](req-coverage-audit/REQ-031.md) | 46% | L |
| REQ-033 MCP-Server | [.audits/req-coverage-audit/REQ-033.md](req-coverage-audit/REQ-033.md) | 33% | M |
| REQ-035 KI-Fachbegriff-Glossar | [.audits/req-coverage-audit/REQ-035.md](req-coverage-audit/REQ-035.md) | 38% | L |
| REQ-036 KI-Diagnose-Assistent | [.audits/req-coverage-audit/REQ-036.md](req-coverage-audit/REQ-036.md) | 25% | L |
| UI-NFR-003 Performance | [.audits/req-coverage-audit/UI-NFR-003.md](req-coverage-audit/UI-NFR-003.md) | — | S |
| UI-NFR-012 PWA-Offline | [.audits/req-coverage-audit/UI-NFR-012.md](req-coverage-audit/UI-NFR-012.md) | 0% | M |
| UI-NFR-013 Einwilligungsmanagement (Consent) | [.audits/req-coverage-audit/UI-NFR-013.md](req-coverage-audit/UI-NFR-013.md) | 0% | M |
| UI-NFR-015 HA Lovelace Custom Cards | [.audits/req-coverage-audit/UI-NFR-015.md](req-coverage-audit/UI-NFR-015.md) | — | S |
| UI-NFR-019 Kiosk-Modus | [.audits/req-coverage-audit/UI-NFR-019.md](req-coverage-audit/UI-NFR-019.md) | — | S |

## Run log
- 2026-04-29 — Manifest geladen: 72 Eintraege, 0 Luecken
- 2026-04-29 — Coverage berechnet (Manifest-getrieben, keine Heuristik)
- 2026-04-29 — Per-Anforderungs-Plans geschrieben: 28 offen, 44 mit Coverage 100 %
- 2026-04-29 — Aggregate geschrieben
