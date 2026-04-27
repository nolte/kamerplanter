---
audit-type: execution-roadmap
target-repo: kamerplanter
based-on: .audits/req-coverage-audit.md
plans-considered: 27
repo-revision: 2a08b17b
created: 2026-04-27
---

# Strategische Umsetzungs-Roadmap

Strategische Priorisierung der **27 offenen Per-Anforderungs-Plans** aus
`.audits/req-coverage-audit.md`. Im Gegensatz zur algorithmischen Roadmap im Aggregate
(Score-basiert) bewertet dieses Dokument zusaetzlich:

- **Risiko/Compliance** (DSGVO, Sicherheit, Multi-Tenant, Auslieferungs-Blocker)
- **Drift in Produktion** (Spec voraus, Code hinterher — Sync vs Neu-Implementierung)
- **Abhaengigkeiten** (Cross-References — was blockiert was?)
- **Geschaeftswert** (produktrelevant vs. explizit "Future" markiert in MEMORY)
- **Aufwand** (S/M/L/XL aus Manifest-Coverage)
- **Quick-Win-Faktor** (geringer Restaufwand fuer hohen Statusaufstieg)

## Bewertungsmatrix (alle 27 Plans)

Spalten: Risiko (R), Abhaengigkeit (A), Aufwand (E), Quick-Win (Q),
Roadmap-Markierung in MEMORY (F=Future explizit, N=Now), Bucket A–F.

| ID | Coverage | R | A | E | Q | F | Bucket |
|---|---|---|---|---|---|---|---|
| **REQ-025** Datenschutz/DSGVO | 18 % | hoch | NFR-011, REQ-024, UI-NFR-013 | L | nein | N | A |
| **NFR-011** Retention-Policy | 50 % | hoch | REQ-025 | M | mittel | N | A |
| **UI-NFR-013** Consent | 0 % | hoch | REQ-025 | M | mittel | N | A |
| **REQ-027** Light-Modus | 83 % | mittel | REQ-023, REQ-024, REQ-025 | M | hoch | N | A |
| REQ-005 Hybrid-Sensorik | 89 % | gering | — | M | **sehr hoch** | N | B |
| REQ-007 Erntemanagement | 83 % | gering | REQ-008 | M | **sehr hoch** | N | B |
| REQ-028 Mischkultur | 89 % | gering | REQ-001, REQ-002 | M | **sehr hoch** | N | B |
| REQ-030 Benachrichtigung | 83 % | gering | REQ-022 | M | **sehr hoch** | N | B |
| REQ-032 Druckansichten | 83 % | gering | UI-NFR-016 | M | hoch | N | B |
| UI-NFR-002 Barrierefreiheit | 50 % | gering | — | M | hoch | N | B |
| REQ-009 Dashboard | 67 % | mittel | REQ-021/22/24/27 | M | mittel | N | C |
| **NFR-013** Object-Storage | 0 % | mittel | REQ-025, NFR-011 | M | mittel | N | C |
| **UI-NFR-012** PWA-Offline | 0 % | mittel | — | M | mittel | N | C |
| REQ-018 Umgebungssteuerung | 25 % | mittel | REQ-005 | L | gering | N | D |
| REQ-017 Vermehrungsmanagement | 0 % | gering | REQ-001, REQ-013 | L | gering | N | D |
| REQ-008 Post-Harvest | 0 % | gering | REQ-007 | L | gering | N | D |
| REQ-016 InvenTree (optional) | 0 % | gering | — | M | gering | N | D |
| REQ-026 Aquaponik | 0 % | gering | REQ-005, REQ-018 | L | gering | N | D |
| REQ-029 KI-Bilderkennung | 0 % | gering | REQ-001 | L | gering | **F** | E |
| REQ-031 KI-Assistent | 28 % | gering | REQ-029, 035, 036 | L | gering | **F** | E |
| REQ-033 MCP-Server | 0 % | gering | REQ-031 | M | gering | **F** | E |
| REQ-035 KI-Glossar | 17 % | gering | REQ-031, UI-NFR-011 | L | gering | **F** | E |
| REQ-036 KI-Diagnose | 0 % | gering | REQ-010, 029, 031 | L | gering | **F** | E |
| NFR-012 Cloud-Skalierung | n/a | gering | NFR-002 | S | hoch | N | F |
| UI-NFR-003 Performance | n/a | gering | — | S | hoch | N | F |
| UI-NFR-015 HA Lovelace | n/a | gering | — | S | hoch | N | F |
| UI-NFR-019 Kiosk-Modus | n/a | gering | — | S | hoch | N | F |

**Buckets:**

- **A — Sofort (Compliance/Auslieferungs-Blocker)** — Rechtsrisiko ODER blockiert Produktiv-Deployment
- **B — Quick Wins** — Coverage 50–89 %, Restaufwand klein, Statusaufstieg gross
- **C — Strategische Backend-/UI-Slices** — neue Bausteine die andere Module aktivieren
- **D — Geschaeftliche Slices** — komplette neue Features, niedriger Druck
- **E — Future / KI-Familie** — explizit als "Future" in MEMORY markiert, ML-Pipeline-Setup noetig
- **F — Polish (Idee-Status)** — kleinere Themen, on-demand bei konkretem Trigger

## Empfohlene Sprint-Sequenz

### Sprint 1 — Compliance & Auslieferungsfaehigkeit (1–2 Wochen)

**Ziel:** Repository ist produktiv-auslieferungsfaehig in der EU. DSGVO-Risiko geschlossen,
Light-Modus deployment-bereit.

| # | Plan | Aufwand | Akzeptanz |
|---|---|---|---|
| 1 | [REQ-025 Datenschutz/DSGVO](req-coverage-audit/REQ-025.md) | L | 14 Privacy-Endpunkte unter `/api/v1/privacy/` + Privacy-Page |
| 2 | [NFR-011 Retention-Policy aktivieren](req-coverage-audit/NFR-011.md) | M | Celery-Task laeuft taeglich, IP-Anonymisierung nach 7 Tagen |
| 3 | [UI-NFR-013 Consent-Komponente](req-coverage-audit/UI-NFR-013.md) | M | Cookie-/Tracking-Consent UI + Backend-ConsentRecord |
| 4 | [REQ-027 Light-Modus Platform-Tenant + Mode-Switch](req-coverage-audit/REQ-027.md) | M | Bidirektionaler Mode-Switch + Auto-Assign |

**Kombinierter Aufwand:** L + 3×M ≈ **2 Personenwochen Backend + 1 Woche Frontend**.

**Output:** REQ-025/027/NFR-011/UI-NFR-013 alle auf 100 %, **5 Anforderungen abgehakt**,
Compliance-Risiko adressiert.

### Sprint 2 — Quick Wins (3–5 Tage)

**Ziel:** Maximale Statusaufstiege bei minimalem Restaufwand. Alle Plans sind primaer
"fehlt nur 1–2 Test-Files / 1 Frontend-Page".

| # | Plan | Aufwand | Was fehlt konkret |
|---|---|---|---|
| 5 | [REQ-005 Hybrid-Sensorik](req-coverage-audit/REQ-005.md) | S | E2E-Test `tests/e2e/test_req005_*.py` |
| 6 | [REQ-007 Erntemanagement](req-coverage-audit/REQ-007.md) | S | E2E-Test (Karenz-Gate-Szenario) |
| 7 | [REQ-028 Mischkultur](req-coverage-audit/REQ-028.md) | S | E2E-Test |
| 8 | [REQ-030 Benachrichtigung](req-coverage-audit/REQ-030.md) | S | E2E-Test |
| 9 | [UI-NFR-002 Barrierefreiheit](req-coverage-audit/UI-NFR-002.md) | S | a11y-Test ergaenzen (Page-Coverage) |
| 10 | [REQ-032 Druckansichten](req-coverage-audit/REQ-032.md) | M | Frontend-PrintPage-Komponente |

**Kombinierter Aufwand:** 5×S + 1×M ≈ **3 Tage Tests + 1 Tag Frontend**.

**Output:** **6 weitere Anforderungen auf 100 %**, Status-Verteilung springt von 43 → **49
Implementiert (von 70)**, Coverage-Score gesamt steigt deutlich.

### Sprint 3 — Strategische Bausteine (1–2 Wochen)

**Ziel:** Module aktivieren, die andere Anforderungen freischalten oder eine zentrale
Funktionalitaet komplettieren.

| # | Plan | Aufwand | Geschaeftsnutzen |
|---|---|---|---|
| 11 | [REQ-009 Dashboard Backend-Aggregations-Service](req-coverage-audit/REQ-009.md) | M | Dashboard-Performance, kein ad-hoc-Aggregation mehr |
| 12 | [NFR-013 Object-Storage S3-Adapter](req-coverage-audit/NFR-013.md) | M | Voraussetzung fuer File-Uploads (Bilder, Reports) |
| 13 | [UI-NFR-012 PWA-Offline](req-coverage-audit/UI-NFR-012.md) | M | Mobile-Nutzung im Garten ohne Netz |

**Kombinierter Aufwand:** 3×M ≈ **1.5 Wochen**.

**Output:** Mobile-tauglich, Dashboard-performant, Datei-Uploads als Foundation fuer REQ-029.

### Sprint 4+ — Geschaeftliche Slices (jeweils eigener Sprint)

**Ziel:** Neue Features, jeweils komplette Module. Eigenstaendige Sprints — nicht parallel.

Reihenfolge **nach Abhaengigkeit + Cross-Reference**:

| # | Plan | Aufwand | Vorbedingung |
|---|---|---|---|
| 14 | [REQ-018 Umgebungssteuerung](req-coverage-audit/REQ-018.md) | L | REQ-005 Hybrid-Sensorik (Sprint 2 erledigt) |
| 15 | [REQ-008 Post-Harvest](req-coverage-audit/REQ-008.md) | L | REQ-007 (Sprint 2 erledigt) — nur wenn aktiver Cannabis-Use-Case |
| 16 | [REQ-017 Vermehrungsmanagement](req-coverage-audit/REQ-017.md) | L | REQ-001, REQ-013 (beide bereits 100 %) |
| 17 | [REQ-016 InvenTree](req-coverage-audit/REQ-016.md) | M | Spec markiert als optional — nur on-demand |
| 18 | [REQ-026 Aquaponik](req-coverage-audit/REQ-026.md) | L | REQ-018 (siehe #14) — niedrige Geschaeftspriorit. |

### Sprint Future — KI-Familie (Quartalsplanung)

**Ziel:** ML-Pipeline + AI-Features als Block-Investment. Reihenfolge wegen
Foundation-Charakter von REQ-029:

| # | Plan | Aufwand | Reihenfolge-Begruendung |
|---|---|---|---|
| F1 | [REQ-029 KI-Bilderkennung](req-coverage-audit/REQ-029.md) | L | Foundation — andere KI-Features bauen darauf |
| F2 | [REQ-031 KI-Assistent Pflanzenberatung](req-coverage-audit/REQ-031.md) | L | KnowledgeServiceClient existiert bereits |
| F3 | [REQ-035 KI-Glossar](req-coverage-audit/REQ-035.md) | L | HelpTooltip-Komponente existiert |
| F4 | [REQ-036 KI-Diagnose](req-coverage-audit/REQ-036.md) | L | nutzt REQ-010 IPM + REQ-029 + REQ-031 |
| F5 | [REQ-033 MCP-Server](req-coverage-audit/REQ-033.md) | M | Externes Interface fuer alle KI-Features |

**Empfehlung:** Erst nach Sprint 1+2+3 anpacken. Erfordert ML-Inference-Infrastruktur (GPU/CPU,
Embedding-Service, ggf. eigene Modelle).

### Polish-Items (on-demand)

| Plan | Aufwand | Trigger |
|---|---|---|
| [NFR-012 Cloud-Skalierung](req-coverage-audit/NFR-012.md) | S | Wenn Cloud-Deploy ansteht |
| [UI-NFR-003 Performance](req-coverage-audit/UI-NFR-003.md) | S | Wenn Lighthouse-Audit / Performance-Beschwerden |
| [UI-NFR-015 HA Lovelace](req-coverage-audit/UI-NFR-015.md) | S | Wenn HA-Integration ausgebaut wird |
| [UI-NFR-019 Kiosk-Modus](req-coverage-audit/UI-NFR-019.md) | S | Wenn echter Kiosk-Use-Case auftritt |

## Status-Prognose

Bei Umsetzung der Sprints 1+2+3:

| Status | Heute | nach Sprint 1 | nach Sprint 2 | nach Sprint 3 |
|---|---|---|---|---|
| Implementiert | 43 (61 %) | 47 (67 %) | **53 (76 %)** | **56 (80 %)** |
| Teilweise | 7 | 6 | 1 | 1 |
| Lueckenhaft | 2 | 0 | 0 | 0 |
| Spezifiziert | 14 | 13 | 12 | 9 |
| Idee | 4 | 4 | 4 | 4 |

→ **80 % Implementierungsgrad in 3–5 Wochen Aufwand**, ohne KI-Familie.

## Abhaengigkeitsgraph (vereinfacht)

```
REQ-025 ──┬─ NFR-011 (Retention)
          ├─ UI-NFR-013 (Consent)
          └─ REQ-024 v1.4 RBAC (laut MEMORY drift, nicht im Plan-Index)

REQ-027 ──┬─ REQ-023 v1.10 Service Accounts (laut MEMORY drift)
          ├─ REQ-024
          └─ REQ-025

REQ-018 ── REQ-005 (Sensoren vor Aktoren)
REQ-026 ── REQ-018, REQ-005 (Aquaponik braucht beides)
REQ-008 ── REQ-007
REQ-017 ── REQ-001, REQ-013

REQ-031 ── REQ-029
REQ-033 ── REQ-031
REQ-035 ── REQ-031, UI-NFR-011
REQ-036 ── REQ-010, REQ-029, REQ-031
```

**Wichtige Drift, die NICHT im Plan-Index erscheint** (weil Coverage 100 % aber Spec-Version
voraus laut MEMORY): REQ-013 v2.3 vs Backend v2.0, REQ-022 v2.5 vs MEMORY v2.3, REQ-014 v1.6
vs MEMORY v1.4, REQ-015 v1.6 vs MEMORY v1.1, REQ-023 v1.10 vs MEMORY v1.7, REQ-024 v1.4
RBAC nicht impl. Diese Drift wird vom Manifest-Audit derzeit nicht erkannt (Manifest prueft
nur Datei-Existenz, nicht Versionsabgleich). **Vorschlag:** Drift-Detection als Schritt 2d-2
ergaenzen — REQ-Version aus Spec lesen, gegen MEMORY.md vergleichen.

## Empfohlene unmittelbare naechste Schritte

1. **Diese Roadmap reviewen und freigeben** — Sprint-Schnitt + Reihenfolge bestaetigen
2. **Sprint 1 starten** mit `/implement REQ-025` (Backend-Slice DSGVO-Privacy)
3. **Quick Wins (Sprint 2) parallel** als Aufgaben fuer Test-Engineering einplanen
4. **Drift-Erkennung im Skill nachziehen** — REQ-Version vs MEMORY-Version programmatisch
5. **Nach jedem Sprint:** `python3 .claude/skills/req-coverage-audit/run_audit.py` zur
   Verifikation — geschlossene Plans verschwinden automatisch, Plan-Index schrumpft
