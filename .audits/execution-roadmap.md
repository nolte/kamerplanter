---
audit-type: execution-roadmap
target-repo: kamerplanter
based-on: .audits/req-coverage-audit.md
plans-considered: 32
repo-revision: c18e03dc
created: 2026-04-27
iteration: 2
---

# Strategische Umsetzungs-Roadmap

Strategische Priorisierung der **32 offenen Per-Anforderungs-Plans** aus
`.audits/req-coverage-audit.md`. Im Gegensatz zur algorithmischen Roadmap im Aggregate
(Score-basiert) bewertet dieses Dokument zusaetzlich Risiko / Compliance, Drift in Produktion,
Cross-Reference-Abhaengigkeiten, Geschaeftswert (Now vs. Future) und Quick-Win-Faktor.

**Iteration 2 (2026-04-27):** Drift-Detection im Skill aktiviert. 6 neue Drift-Plans
(REQ-013, 014, 015, 022, 023, 024) die vorher 100 % File-Coverage zeigten aber im MEMORY als
Drift markiert waren, erscheinen jetzt korrekt im Plan-Index. NFR-012 wurde geschlossen
(alle Artefakte optional + kein Drift-Marker = 100 % Score). Die zuvor als „nicht im
Plan-Index" notierten Drifts sind jetzt automatisch erkannt und actionable.

## Bewertungsmatrix (alle 32 Plans)

Spalten: Risiko (R), Abhaengigkeit (A), Aufwand (E), Quick-Win (Q),
Roadmap-Markierung in MEMORY (F=Future explizit, N=Now), Bucket A–F.

| ID | Coverage | R | A | E | Q | F | Bucket |
|---|---|---|---|---|---|---|---|
| **REQ-025** Datenschutz/DSGVO | 26 % | hoch | NFR-011, REQ-024, UI-NFR-013 | L | nein | N | A1 |
| **NFR-011** Retention-Policy | 50 % | hoch | REQ-025 | M | mittel | N | A1 |
| **UI-NFR-013** Consent | 0 % | hoch | REQ-025 | M | mittel | N | A1 |
| **REQ-027** Light-Modus | 72 % | mittel | REQ-023, REQ-024, REQ-025 | M | hoch | N | A2 |
| **REQ-023** Auth (Service Accounts) | 88 % | mittel | REQ-024, REQ-027 | L | hoch | N | A2 |
| **REQ-024** Tenant (RBAC Matrix) | 88 % | mittel | REQ-023, REQ-027 | L | hoch | N | A2 |
| **REQ-013** PlantingRun (Backend v2.0 → v2.3) | 88 % | mittel | REQ-001, REQ-022 | M | hoch | N | B1 |
| **REQ-022** Pflegeerinnerungen (v2.3 → v2.5) | 88 % | mittel | REQ-013 | M | hoch | N | B1 |
| ~~**REQ-014** Tankmanagement (v1.4 → v1.6)~~ ✅ | 100 % | gering | REQ-004 | S | sehr hoch | N | **done** |
| ~~**REQ-015** Kalenderansicht (v1.1 → v1.6)~~ ✅ | 100 % | gering | — | M | hoch | N | **done** |
| REQ-005 Hybrid-Sensorik | 89 % | gering | — | S | **sehr hoch** | N | B2 |
| REQ-007 Erntemanagement | 83 % | gering | REQ-008 | S | **sehr hoch** | N | B2 |
| REQ-028 Mischkultur | 89 % | gering | REQ-001, REQ-002 | S | **sehr hoch** | N | B2 |
| REQ-030 Benachrichtigung | 83 % | gering | REQ-022 | S | **sehr hoch** | N | B2 |
| REQ-032 Druckansichten | 83 % | gering | UI-NFR-016 | M | hoch | N | B2 |
| UI-NFR-002 Barrierefreiheit | 50 % | gering | — | S | hoch | N | B2 |
| REQ-009 Dashboard | 67 % | mittel | REQ-021/22/24/27 | M | mittel | N | C |
| **NFR-013** Object-Storage | 0 % | mittel | REQ-025, NFR-011 | M | mittel | N | C |
| **UI-NFR-012** PWA-Offline | 0 % | mittel | — | M | mittel | N | C |
| REQ-018 Umgebungssteuerung | 31 % | mittel | REQ-005 | L | gering | N | D |
| REQ-017 Vermehrungsmanagement | 12 % | gering | REQ-001, REQ-013 | L | gering | N | D |
| REQ-008 Post-Harvest | 12 % | gering | REQ-007 | L | gering | N | D |
| REQ-016 InvenTree (optional) | 0 % | gering | — | M | gering | N | D |
| REQ-026 Aquaponik | 12 % | gering | REQ-005, REQ-018 | L | gering | N | D |
| REQ-029 KI-Bilderkennung | 12 % | gering | REQ-001 | L | gering | **F** | E |
| REQ-031 KI-Assistent | 26 % | gering | REQ-029, 035, 036 | L | gering | **F** | E |
| REQ-033 MCP-Server | 12 % | gering | REQ-031 | M | gering | **F** | E |
| REQ-035 KI-Glossar | 26 % | gering | REQ-031, UI-NFR-011 | L | gering | **F** | E |
| REQ-036 KI-Diagnose | 12 % | gering | REQ-010, 029, 031 | L | gering | **F** | E |
| UI-NFR-003 Performance | n/a | gering | — | S | hoch | N | F |
| UI-NFR-015 HA Lovelace | n/a | gering | — | S | hoch | N | F |
| UI-NFR-019 Kiosk-Modus | n/a | gering | — | S | hoch | N | F |

**Buckets:**

- **A1 — Compliance-Sofort** — DSGVO/Rechtsrisiko bei EU-Produktivnutzung
- **A2 — Auth/Tenant/Light-Modus-Trio** — drei eng gekoppelte Anforderungen, die zusammen das
  Multi-Tenant-Berechtigungsmodell + Light-Modus-Auslieferung freischalten
- **B1 — Drift-Sync produktive Module (NEU in Iter 2)** — Backend hinkt der Spec hinterher,
  reine Synchronisations-Arbeit, keine neuen Architekturentscheidungen
- **B2 — Quick Wins** — Coverage 50–89 %, Restaufwand klein (meist nur 1 E2E-Test), Statusaufstieg
  gross
- **C — Strategische Backend-/UI-Slices** — neue Bausteine die andere Module aktivieren
- **D — Geschaeftliche Slices** — komplette neue Features, niedriger Druck
- **E — Future / KI-Familie** — explizit als „Future" in MEMORY markiert, ML-Pipeline-Setup noetig
- **F — Polish (Idee-Status)** — kleinere Themen, on-demand bei konkretem Trigger

## Empfohlene Sprint-Sequenz

### Sprint 1A — Compliance (1 Woche)

**Ziel:** EU-Auslieferungsfaehigkeit. DSGVO-Risiko geschlossen.

| # | Plan | Aufwand | Akzeptanz |
|---|---|---|---|
| 1 | [REQ-025 Datenschutz/DSGVO](req-coverage-audit/REQ-025.md) | L | 14 Privacy-Endpunkte unter `/api/v1/privacy/` + Privacy-Page |
| 2 | [NFR-011 Retention-Policy aktivieren](req-coverage-audit/NFR-011.md) | M | Celery-Task laeuft taeglich, IP-Anonymisierung nach 7 Tagen |
| 3 | [UI-NFR-013 Consent-Komponente](req-coverage-audit/UI-NFR-013.md) | M | Cookie-/Tracking-Consent UI + Backend-ConsentRecord |

**Aufwand:** L + 2×M ≈ **1 Personenwoche Backend + ½ Woche Frontend**.

### Sprint 1B — Auth/Tenant/Light-Modus-Trio (1.5 Wochen)

**Ziel:** Drei stark gekoppelte Anforderungen gemeinsam abschliessen — Service Accounts (REQ-023
v1.10) brauchen Light-Modus-Tenant-Kontext (REQ-027), und beide brauchen die granulare
Permission-Matrix (REQ-024 v1.4). Einzeln implementieren wuerde Refactoring nach sich ziehen.

| # | Plan | Aufwand | Was fehlt konkret |
|---|---|---|---|
| 4 | [REQ-024 RBAC Permission-Matrix](req-coverage-audit/REQ-024.md) | M | `app/core/permissions.py` mit `require_permission()` Dependency, Permission-Enum |
| 5 | [REQ-023 Service Accounts](req-coverage-audit/REQ-023.md) | L | `account_type: 'service'`, ServiceAccountEngine, 15 API-Endpunkte, IP-Allowlist |
| 6 | [REQ-027 Light-Modus Platform-Tenant + Mode-Switch](req-coverage-audit/REQ-027.md) | M | Bidirektionaler Mode-Switch + Auto-Assign + Platform-Tenant |

**Aufwand:** M + L + M ≈ **1.5 Personenwochen Backend + ½ Woche Frontend (Permission-Gating in UI)**.

### Sprint 2 — Drift-Sync produktive Module (1 Woche)

**Ziel:** Backend-Code mit jeweils aktueller Spec-Version synchronisieren. Reine Sync-Arbeit
ohne neue Architektur, aber wichtig damit die "Implementiert"-Module tatsaechlich der Spec
entsprechen.

| # | Plan | Aufwand | Was nachzuziehen ist |
|---|---|---|---|
| 7 | ~~REQ-014 Tankmanagement v1.6~~ ✅ **done** | S | Wasserquellen-Kaskade + `_ms`-Suffix implementiert (`tank_service.py:242`), Fable-5-Review 2026-07 verifiziert (GAP-B17) |
| 8 | ~~REQ-015 Kalenderansicht v1.6~~ ✅ **done** | M | Light-Modus iCal-Token (`calendar/tenant_router.py:38`) + CF-005 `expires_at`/410 (`calendar_service.py:308-316`) implementiert, Fable-5-Review 2026-07 verifiziert (GAP-B17) |
| 9 | [REQ-013 PlantingRun v2.3](req-coverage-audit/REQ-013.md) | M | CareProfile-Snapshot beim Run-Start (v2.0 → v2.3) |
| 10 | [REQ-022 Pflegeerinnerungen v2.5](req-coverage-audit/REQ-022.md) | M | Run-Owned CareProfile mit Snapshot-Mechanik (v2.3 → v2.5) |

**Aufwand:** S + 3×M ≈ **1 Personenwoche Backend**. Pro Plan: Spec lesen → Diff zu Backend
identifizieren → Felder/Edges nachziehen → MEMORY aktualisieren.

### Sprint 3 — Quick Wins (3–5 Tage)

**Ziel:** Maximale Statusaufstiege bei minimalem Restaufwand. Alle Plans sind primaer
„fehlt nur 1–2 Test-Files / 1 Frontend-Page".

| # | Plan | Aufwand | Was fehlt konkret |
|---|---|---|---|
| 11 | [REQ-005 Hybrid-Sensorik](req-coverage-audit/REQ-005.md) | S | E2E-Test `tests/e2e/test_req005_*.py` |
| 12 | [REQ-007 Erntemanagement](req-coverage-audit/REQ-007.md) | S | E2E-Test (Karenz-Gate-Szenario) |
| 13 | [REQ-028 Mischkultur](req-coverage-audit/REQ-028.md) | S | E2E-Test |
| 14 | [REQ-030 Benachrichtigung](req-coverage-audit/REQ-030.md) | S | E2E-Test |
| 15 | [UI-NFR-002 Barrierefreiheit](req-coverage-audit/UI-NFR-002.md) | S | a11y-Test ergaenzen (Page-Coverage) |
| 16 | [REQ-032 Druckansichten](req-coverage-audit/REQ-032.md) | M | Frontend-PrintPage-Komponente |

**Aufwand:** 5×S + 1×M ≈ **3 Tage Tests + 1 Tag Frontend**.

### Sprint 4 — Strategische Bausteine (1.5 Wochen)

**Ziel:** Module aktivieren, die andere Anforderungen freischalten oder eine zentrale
Funktionalitaet komplettieren.

| # | Plan | Aufwand | Geschaeftsnutzen |
|---|---|---|---|
| 17 | [REQ-009 Dashboard Backend-Aggregations-Service](req-coverage-audit/REQ-009.md) | M | Dashboard-Performance, kein ad-hoc-Aggregation mehr |
| 18 | [NFR-013 Object-Storage S3-Adapter](req-coverage-audit/NFR-013.md) | M | Voraussetzung fuer File-Uploads (Bilder, Reports) |
| 19 | [UI-NFR-012 PWA-Offline](req-coverage-audit/UI-NFR-012.md) | M | Mobile-Nutzung im Garten ohne Netz |

**Aufwand:** 3×M ≈ **1.5 Wochen**.

### Sprint 5+ — Geschaeftliche Slices (jeweils eigener Sprint)

**Ziel:** Neue Features, jeweils komplette Module. Eigenstaendige Sprints — nicht parallel.

Reihenfolge **nach Abhaengigkeit + Cross-Reference**:

| # | Plan | Aufwand | Vorbedingung |
|---|---|---|---|
| 20 | [REQ-018 Umgebungssteuerung](req-coverage-audit/REQ-018.md) | L | REQ-005 Hybrid-Sensorik (Sprint 3 erledigt) |
| 21 | [REQ-008 Post-Harvest](req-coverage-audit/REQ-008.md) | L | REQ-007 (Sprint 3 erledigt) — nur wenn aktiver Cannabis-Use-Case |
| 22 | [REQ-017 Vermehrungsmanagement](req-coverage-audit/REQ-017.md) | L | REQ-001 (100 %), REQ-013 (Sprint 2 erledigt) |
| 23 | [REQ-016 InvenTree](req-coverage-audit/REQ-016.md) | M | Spec markiert als optional — nur on-demand |
| 24 | [REQ-026 Aquaponik](req-coverage-audit/REQ-026.md) | L | REQ-018 (siehe #20) — niedrige Geschaeftspriorit. |

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

**Empfehlung:** Erst nach Sprint 1–4 anpacken. Erfordert ML-Inference-Infrastruktur (GPU/CPU,
Embedding-Service, ggf. eigene Modelle).

### Polish-Items (on-demand)

| Plan | Aufwand | Trigger |
|---|---|---|
| [UI-NFR-003 Performance](req-coverage-audit/UI-NFR-003.md) | S | Wenn Lighthouse-Audit / Performance-Beschwerden |
| [UI-NFR-015 HA Lovelace](req-coverage-audit/UI-NFR-015.md) | S | Wenn HA-Integration ausgebaut wird |
| [UI-NFR-019 Kiosk-Modus](req-coverage-audit/UI-NFR-019.md) | S | Wenn echter Kiosk-Use-Case auftritt |

**Hinweis:** NFR-012 Cloud-Skalierung wurde in Iter 2 geschlossen — alle Manifest-Artefakte
optional + kein Drift-Marker. Wenn Cloud-Deploy ansteht, Manifest-Eintraege auf
`optional: false` setzen, dann erscheint NFR-012 wieder im Plan-Index.

## Status-Prognose

Bei Umsetzung der Sprints 1A–4:

| Status | Heute | nach 1A | nach 1B | nach 2 | nach 3 | nach 4 |
|---|---|---|---|---|---|---|
| Implementiert | 40 (57 %) | 43 (61 %) | 46 (66 %) | 50 (71 %) | **56 (80 %)** | **59 (84 %)** |
| Teilweise | 11 | 10 | 7 | 3 | 1 | 1 |
| Lueckenhaft | 7 | 5 | 5 | 5 | 5 | 4 |
| Spezifiziert | 9 | 9 | 9 | 9 | 5 | 3 |
| Idee | 3 | 3 | 3 | 3 | 3 | 3 |

→ **84 % Implementierungsgrad in 5–7 Wochen Aufwand**, ohne KI-Familie und ohne Geschaefts-
Slices Sprint 5+.

## Abhaengigkeitsgraph (vereinfacht)

```
Sprint 1A:
  REQ-025 ──┬─ NFR-011 (Retention)
            └─ UI-NFR-013 (Consent)

Sprint 1B (eng gekoppelt):
  REQ-024 (RBAC) ──┐
  REQ-023 (Service Accounts) ──┼── REQ-027 (Light-Modus mit Service Accounts)
                                └── (alle drei brauchen sich gegenseitig)

Sprint 2 (Drift-Sync):
  REQ-013 (Pflanzdurchlauf v2.3) ── REQ-022 (Pflegeerinnerungen v2.5 nutzt CareProfile-Snapshot)
  REQ-014 (Tankmanagement v1.6) ── eigenstaendig
  REQ-015 (Kalender v1.6) ── eigenstaendig

Sprint 5+ (Geschaeftlich):
  REQ-018 ── REQ-005 (Sensoren vor Aktoren)
  REQ-026 ── REQ-018, REQ-005 (Aquaponik braucht beides)
  REQ-008 ── REQ-007
  REQ-017 ── REQ-001, REQ-013

Future (KI):
  REQ-031 ── REQ-029
  REQ-033 ── REQ-031
  REQ-035 ── REQ-031, UI-NFR-011
  REQ-036 ── REQ-010, REQ-029, REQ-031
```

## Empfohlene unmittelbare naechste Schritte

1. **Diese Roadmap reviewen und freigeben** — Sprint-Schnitt + Reihenfolge bestaetigen
2. **Sprint 1A starten** mit `/implement REQ-025` (Backend-Slice DSGVO-Privacy)
3. **Sprint 2 (Drift-Sync) parallel** als Backend-Sync-Aufgaben einplanen — niedrige
   Architekturkomplexitaet, gute Aufgabe waehrend Sprint 1A/1B Frontend-Anteile laufen
4. **Quick Wins (Sprint 3) als Aufgaben fuer Test-Engineering** parallel einplanen
5. **Nach jedem Sprint:** `python3 .claude/skills/req-coverage-audit/run_audit.py` zur
   Verifikation — geschlossene Plans verschwinden automatisch, Plan-Index schrumpft, Drift-
   Markierungen in MEMORY.md zur Aktualisierung mit-bedenken (sonst bleiben Drift-Findings
   bestehen, auch wenn Code synchron ist)

## Aenderungen gegenueber Iteration 1

| Aspekt | Iter 1 | Iter 2 |
|---|---|---|
| Plans im Index | 27 | **32** (+5: Drift-Plans REQ-013/14/15/22/23/24, -1: NFR-012 closed) |
| Sprint-Struktur | 4 Sprints + Future + Polish | 5 Sprints (1A/1B/2/3/4) + Future + Polish |
| Sprint 1 | Compliance + Auth (alles in einem Sprint) | A1 Compliance / A2 Auth-Trio (sauberer Schnitt) |
| Drift-Sync | nicht im Plan-Index, nur in „Wichtige Drift" notiert | **eigener Sprint 2** mit 4 actionable Plans |
| 80 %-Marke | nach Sprint 3 | nach Sprint 3 (gleicher Endpunkt, mehr Detailarbeit unterwegs) |
| 84 %-Marke | nicht erreicht | nach Sprint 4 |
