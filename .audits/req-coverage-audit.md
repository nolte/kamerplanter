---
review-type: req-coverage-audit
target-repo: kamerplanter
total-count: 72
req-count: 37
nfr-count: 16
ui-nfr-count: 19
manifest-coverage: 72/72
plans-open: 3
plans-closed: 69
repo-revision: 6b55695d
created: 2026-04-30
mode: full
---

## Scope
Vollstaendiger Manifest-getriebener Coverage-Audit ueber alle 37 REQ + 16 NFR + 19 UI-NFR. Manifest-Quelle: `.claude/skills/req-coverage-audit/expectations.yaml`. Pro Anforderung mit Coverage < 100 % wurde ein eigenstaendiger Per-Anforderungs-Plan unter `.audits/req-coverage-audit/<ID>.md` mit konkreten Aufgaben + Akzeptanzkriterien angelegt.

## Manifest-Vollstaendigkeit
- Alle Anforderungen im Manifest: **72/72**
- Vollstaendigkeit OK — keine Manifest-Luecken.

## Verteilung gesamt
- Implementiert: 69 (96 %)
- Teilweise: 0 (0 %)
- Lueckenhaft: 0 (0 %)
- Spezifiziert: 0 (0 %)
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
| REQ-008 | Post-Harvest | 3/3 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-009 | Dashboard | 2/2 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-010 | IPM-System | 7/7 | 4/4 | 2/2 | 100% | Implementiert | — |
| REQ-011 | Externe-Stammdatenanreicherung | 6/6 | n/a | 2/2 | 100% | Implementiert | — |
| REQ-012 | Stammdaten-Import | 7/7 | 2/2 | 3/3 | 100% | Implementiert | — |
| REQ-013 | Pflanzdurchlauf | 7/7 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-014 | Tankmanagement | 4/4 | 2/2 | 3/3 | 100% | Implementiert | — |
| REQ-015 | Kalenderansicht | 5/5 | 4/4 | 3/3 | 100% | Implementiert | — |
| REQ-015-A | Aussaatkalender-Berechnungsregeln | 1/1 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-016 | InvenTree-Integration | 2/2 | n/a | 1/1 | 100% | Implementiert | — |
| REQ-017 | Vermehrungsmanagement | 4/4 | 1/1 | 1/1 | 100% | Implementiert | — |
| REQ-018 | Umgebungssteuerung | 4/4 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-019 | Substratverwaltung | 5/5 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-020 | Onboarding-Wizard | 5/5 | 2/2 | 2/2 | 100% | Implementiert | — |
| REQ-021 | UI-Erfahrungsstufen | 2/2 | 4/4 | 1/1 | 100% | Implementiert | — |
| REQ-022 | Pflegeerinnerungen | 5/5 | 2/2 | 2/2 | 100% | Implementiert | — |
| REQ-023 | Benutzerverwaltung-Authentifizierung | 14/14 | 4/4 | 3/3 | 100% | Implementiert | — |
| REQ-024 | Mandantenverwaltung-Gemeinschaftsgaerten | 11/11 | 3/3 | 3/3 | 100% | Implementiert | — |
| REQ-025 | Datenschutz-Betroffenenrechte | 5/5 | 1/1 | 3/3 | 100% | Implementiert | — |
| REQ-026 | Aquaponik-Management | 2/2 | 1/1 | 1/1 | 100% | Implementiert | — |
| REQ-027 | Light-Modus | 4/4 | n/a | 3/3 | 100% | Implementiert | — |
| REQ-028 | Mischkultur-Companion-Planting | 4/4 | 2/2 | 3/3 | 100% | Implementiert | — |
| REQ-029 | KI-Bilderkennung-Pflanzenidentifikation | 3/3 | 1/1 | 1/1 | 100% | Implementiert | — |
| REQ-030 | Benachrichtigungssystem | 5/5 | 2/2 | 2/2 | 100% | Implementiert | — |
| REQ-031 | KI-Assistent-Pflanzenberatung | 3/3 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-032 | Druckansichten-Export | 3/3 | 1/1 | 2/2 | 100% | Implementiert | — |
| REQ-033 | MCP-Server | 2/2 | n/a | 1/1 | 100% | Implementiert | — |
| REQ-035 | KI-Fachbegriff-Glossar | 2/2 | 2/2 | 1/1 | 100% | Implementiert | — |
| REQ-036 | KI-Diagnose-Assistent | 2/2 | 1/1 | 1/1 | 100% | Implementiert | — |

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
| NFR-011 | Vorratsdatenspeicherung & Aufbewahrungsfristen | 2/2 | 1/1 | 100% | Implementiert | — |
| NFR-012 | Cloud-Provider & Enterprise-Skalierung | n/a | n/a | 100% | Implementiert | — |
| NFR-013 | Speicheranbindung & Object-Storage | 1/1 | n/a | 100% | Implementiert | — |
| NFR-014 | Nuclei-Security-Scanning | 1/1 | n/a | 100% | Implementiert | — |
| NFR-015 | OWASP-ZAP-Security-Scanning | 1/1 | n/a | 100% | Implementiert | — |

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
| UI-NFR-012 | PWA-Offline | 2/2 | n/a | 100% | Implementiert | — |
| UI-NFR-013 | Einwilligungsmanagement (Consent) | 1/1 | n/a | 100% | Implementiert | — |
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
| 1 | UI-NFR-003 Performance | ui-nfr | Idee | — | S | [Plan](req-coverage-audit/UI-NFR-003.md) |
| 2 | UI-NFR-015 HA Lovelace Custom Cards | ui-nfr | Idee | — | S | [Plan](req-coverage-audit/UI-NFR-015.md) |
| 3 | UI-NFR-019 Kiosk-Modus | ui-nfr | Idee | — | S | [Plan](req-coverage-audit/UI-NFR-019.md) |

## Plan-Index (alphabetisch, alle offenen Plans)
| Anforderung | Plan | Coverage | Aufwand |
|---|---|---|---|
| UI-NFR-003 Performance | [.audits/req-coverage-audit/UI-NFR-003.md](req-coverage-audit/UI-NFR-003.md) | — | S |
| UI-NFR-015 HA Lovelace Custom Cards | [.audits/req-coverage-audit/UI-NFR-015.md](req-coverage-audit/UI-NFR-015.md) | — | S |
| UI-NFR-019 Kiosk-Modus | [.audits/req-coverage-audit/UI-NFR-019.md](req-coverage-audit/UI-NFR-019.md) | — | S |

## Run log
- 2026-04-30 — Manifest geladen: 72 Eintraege, 0 Luecken
- 2026-04-30 — Coverage berechnet (Manifest-getrieben, keine Heuristik)
- 2026-04-30 — Per-Anforderungs-Plans geschrieben: 3 offen, 69 mit Coverage 100 %
- 2026-04-30 — Aggregate geschrieben
