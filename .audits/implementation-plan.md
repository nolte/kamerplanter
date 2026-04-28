---
audit-type: implementation-plan
target-repo: kamerplanter
based-on: .audits/req-coverage-audit.md, .audits/execution-roadmap.md, .audits/phase-0-drift-findings.md
plans-considered: 32
created: 2026-04-28
updated: 2026-04-28 (Phase 0 abgeschlossen, Sprint 1B reklassifiziert)
status: phase-0-done
---

# Implementierungsplan — Abarbeitung der 32 offenen Plans

Operationalisierung der `execution-roadmap.md`. Die Roadmap sortiert Plans
strategisch in 5 Sprints + Future + Polish; dieser Plan macht sie ausführbar:
PR-Schnitt, Skill-Sequenz pro Plan, Verifikations-Cadence, Tracking-Mechanik.

## Bestandsaufnahme

- **32 offene Per-Anforderungs-Plans** unter `.audits/req-coverage-audit/` (24 REQ + 2 NFR + 6 UI-NFR)
- Drei Plan-Typen je nach Aufgabengröße:
  - **Drift-only** (1 Aufgabe): MEMORY-Update bzw. Code-Sync — z. B. REQ-014 (88 % → 100 % wenn Drift-Marker aufgelöst)
  - **Quick-Win** (1 Aufgabe): meist 1× E2E-Test fehlt — z. B. REQ-005 (92 % → 100 %)
  - **Slice** (5–10 Aufgaben): volles Backend+Frontend+Tests — z. B. REQ-025 (26 % → 100 %, 8 Aufgaben)

## Reihenfolge — 3 Korrekturen gegenüber `execution-roadmap.md`

Die Roadmap startet mit Sprint 1A (Compliance). Inhaltlich richtig, aber zwei pragmatische Verschiebungen lohnen sich:

1. **Sprint 2 (Drift-Sync) vorziehen** als Phase 0 vor 1A.
   Begründung: 6 der 32 Plans (REQ-013/14/15/22/23/24) sind nur als „Drift" markiert.
   Wenn der Code synchron ist, sind das reine MEMORY.md-Updates → 5–10 Min pro Plan.
   Wenn nicht, sehen wir das früh und re-priorisieren.
2. **Sprint 3 (Quick Wins) parallel zu Sprint 1A** laufen lassen.
   Skills sind disjunkt (`/test-extract` + `selenium-test-generator` vs. `fullstack-developer`) — kein Konflikt.
3. **Sprint 5+ und Future** bleiben in der Roadmap zurückgestellt — keine Änderung.

## Ausführungs-Phasen

### Phase 0 — Drift-Truthing — ABGESCHLOSSEN (2026-04-28)

| Plan | Hypothese | Befund | Aktion |
|---|---|---|---|
| REQ-013 (v2.0 → v2.3) | Backend hinkt | DRIFT konfirmiert | Slice in Sprint 1B (2 PRs) |
| REQ-014 (v1.4 → v1.6) | Backend hinkt | DRIFT (oberflächlich, WateringEvent) | Mini-Sync-PR (~3h) |
| REQ-015 (v1.1 → v1.6) | Backend hinkt | TEILWEISE — iCal/Feed-Drift | Mini-Sync-PR + Follow-Ups |
| REQ-022 (v2.3 → v2.5) | Backend hinkt | DRIFT konfirmiert (umfangreich) | Slice in Sprint 1B |
| REQ-023 (v1.10 Service Accounts) | Service Accounts fehlen | bestätigt | Slice in Sprint 1B (Auth-Trio Schritt 2) |
| REQ-024 (v1.4 RBAC) | RBAC fehlt | bestätigt | Slice in Sprint 1B (Auth-Trio Schritt 1) |

**Ergebnis**: **0 Plans auf 100 %**, **6 Plans reklassifiziert nach Sprint 1B**.
Index bleibt bei 32 (statt vermuteter 28). Detail-Befunde:
[`phase-0-drift-findings.md`](phase-0-drift-findings.md).

**Output**: `expectations.yaml` `memory_status_field`-Strings präzisiert,
MEMORY.md Drift-Hinweise präzisiert (REQ-013/14/15/22 jeweils mit konkreter
Item-Liste), Sprint 1B in Phase 2 erweitert.

### Phase 1 — Compliance (Sprint 1A) parallel zu Quick Wins (Sprint 3) — 1.5 Wochen

| Track | Anforderung | PR-Titel | Skill / Agent |
|---|---|---|---|
| A | REQ-025 Datenschutz | `feat(privacy): implement REQ-025 (DSGVO subject rights)` | `/implement REQ-025` |
| A | NFR-011 Retention | `feat(privacy): activate retention policy NFR-011` | `/implement NFR-011` |
| A | UI-NFR-013 Consent | `feat(privacy): consent component UI-NFR-013` | `frontend-usability-optimizer` |
| B | REQ-005 E2E | `test(e2e): add REQ-005 hybrid sensor E2E` | `selenium-test-generator` |
| B | REQ-007 E2E | `test(e2e): add REQ-007 harvest E2E (Karenz-Gate)` | `selenium-test-generator` |
| B | REQ-028 E2E | `test(e2e): add REQ-028 mischkultur E2E` | `selenium-test-generator` |
| B | REQ-030 E2E | `test(e2e): add REQ-030 notification E2E` | `selenium-test-generator` |
| B | UI-NFR-002 a11y | `test(e2e): a11y page coverage UI-NFR-002` | `selenium-test-generator` |
| B | REQ-032 PrintPage | `feat(frontend): print page component REQ-032` | `frontend-usability-optimizer` |

**3 + 6 = 9 PRs**. Track A seriell (Cross-Refs), Track B parallel.

### Phase 2 — Sprint 1B (Auth-Trio + Drift-Sync-Slices) — 2.5–3 Wochen

Auth-Trio seriell (Foundation-Reihenfolge), Drift-Sync-Slices parallel ab Tag 1.

**Track Auth (seriell)**:
1. **REQ-024 RBAC Permission-Matrix** (`feat(auth): RBAC permission matrix REQ-024`) — Foundation, blockiert 23, 27
2. **REQ-023 Service Accounts** (`feat(auth): service accounts REQ-023`)
3. **REQ-027 Light-Modus** (`feat(auth): light-mode platform-tenant REQ-027`)

**Track Drift-Sync (parallel zu Auth, gestartet Tag 1)**:

| # | Anforderung | PR-Titel | Scope | Dauer |
|---|---|---|---|---|
| 4 | REQ-014 WateringEvent | `refactor(watering): align watering-event field names with spec v1.6 REQ-014` | Mini-Sync (Renames) | 3h |
| 5 | REQ-015 iCal/Feed | `feat(calendar): VALARM, expires_at, PRIORITY/STATUS, HTTP 410 REQ-015` | Mini-Sync | ~75 min |
| 6 | REQ-013/022 Detach-Snapshot ⊕ Run-Owned-Care | `feat(planting-run,care): detach snapshots + run-membership-guard REQ-013 REQ-022 W-010` | Slice (gekoppelt) | M |
| 7 | REQ-022 Outdoor + Überwinterung | `feat(care): overwintering profile + outdoor presets REQ-022 v2.5` | Slice | L |
| 8 | REQ-013 SuccessionPlan | `feat(planting-run): succession-plan model + endpoints REQ-013` | Slice (kann nach Sprint 2 verschoben) | L |

**Auth-Trio + 5 Drift-Slices = 8 PRs in Sprint 1B**. Ohne SuccessionPlan
(verschoben) = 7 PRs in Sprint 1B.

**Kopplung beachten**: REQ-013 Detach-CareProfile-Snapshot (W-010) und
REQ-022 Run-Owned-CareProfile gehören in einen gemeinsamen PR (#6) — sonst
inkonsistente Datenmodell-Mitte.

### Phase 3 — Strategische Bausteine (Sprint 4) — 1.5 Wochen

| Plan | PR-Titel | Skill / Agent |
|---|---|---|
| REQ-009 Dashboard-Aggregation | `feat(dashboard): aggregation service REQ-009` | `fullstack-developer` |
| NFR-013 Object-Storage | `feat(infra): S3 storage adapter NFR-013` | `fullstack-developer` |
| UI-NFR-012 PWA-Offline | `feat(frontend): PWA offline UI-NFR-012` | `frontend-usability-optimizer` |

**3 PRs**.

### Phase 4 — Geschäftliche Slices (Sprint 5+, on-demand)

REQ-018, REQ-008, REQ-017, REQ-016 (optional), REQ-026 — nur bei konkretem Use-Case-Trigger.

### Phase 5 — KI-Familie (Future, Quartalsplanung)

REQ-029 → REQ-031 → REQ-035 → REQ-036 → REQ-033 — nur nach Phase 1–3 + ML-Infra-Setup.

### Polish — UI-NFR-003/015/019 on-demand bei Trigger

## Cadence pro PR

1. **Branch erstellen** von `develop`: `<type>/<scope>-<id>-<slug>` (Conventional-Commits-Prefix matcht Branch-Type)
2. **Implementieren** mit empfohlenem Skill/Agent
3. **Verifizieren lokal**: `python3 .claude/skills/req-coverage-audit/run_audit.py <ID>` — Coverage muss 100 % erreichen
4. **PR erstellen** via `/nolte-shared:pull-request-create`
5. **Review** via `/review` Skill
6. **Mergen** via `/nolte-shared:pull-request-merge --wait` (sobald `claude-shared#26` gemerged ist; sonst manueller Re-Run nach grüner CI)
7. **Plan auto-gelöscht** beim nächsten globalen `run_audit.py` (kein manueller Cleanup pro Plan)

## Tracking + Sprint-Closing

- **Pro Sprint**: globaler `python3 .claude/skills/req-coverage-audit/run_audit.py` ohne Args → schreibt neuen `.audits/req-coverage-audit.md` + Plan-Index
- **Status-Prognose** (aus Roadmap, plus Phase 0 ergänzt):

| Status | Heute | nach Phase 0 (revidiert) | nach Phase 1 | nach Phase 2 | nach Phase 3 |
|---|---|---|---|---|---|
| Implementiert | 40 (57 %) | 40 (57 %) | 46 (66 %) | 53 (76 %) | 56 (80 %) |
| Plans offen | 32 | 32 | 26 | 16 | 13 |

→ **80 % Implementierungsgrad in 6–8 Wochen** ohne KI-Familie und ohne Sprint 5+.

Die Phase-0-Revision (alle 6 Plans bleiben offen statt 4 schließen) verlängert
den Gesamtplan um ~1 Woche, da Sprint 1B nun 7–8 PRs statt 3 enthält. Quick-Wins
in Track Drift-Sync (REQ-014/15) bleiben aber kleinformatig parallel laufbar.

## Risiken

1. ~~**Drift-Truthing kann eskalieren**~~ — **eingetreten**: Alle 6 Plans
   bleiben offen, alle 6 wurden als Sprint-1B-Slices reklassifiziert.
   Sprint 1B von 3 PRs auf 7–8 PRs erweitert, Gesamtaufwand +1 Woche.
2. **REQ-025 ist groß** (8 Aufgaben, 14 Endpunkte): `/implement REQ-025` als
   Single-Skill könnte zu groß sein — eventuell aufteilen in 2 PRs
   (Backend + Frontend separat).
3. **REQ-024 vs. REQ-023 Reihenfolge**: `require_permission()` aus REQ-024
   wird in REQ-023 gebraucht — Reihenfolge in Sprint 1B wird strikt
   eingehalten (24 → 23 → 27).
4. **Kopplung REQ-013 ⊕ REQ-022 W-010**: Detach-CareProfile-Snapshot (REQ-013)
   und Run-Owned-CareProfile (REQ-022) müssen in einem PR ko-implementiert
   werden, sonst inkonsistente Datenmodell-Mitte. Bei strikter
   Per-Plan-PR-Strategie aufpassen.
5. **REQ-014 Renames** brechen Frontend-Konsumenten: `plant_keys` →
   `slot_keys` und `target_ec` → `target_ec_ms` benötigen entweder
   Dual-Support-Window oder Frontend-Update im selben PR.

## Abhängigkeitsgraph (kritischer Pfad)

```
Phase 0 (Drift-Truthing) — DONE
  Alle 6 Plans → Sprint 1B reklassifiziert

Phase 1 (Compliance + Quick Wins)
  Track A: REQ-025 ──┬─ NFR-011 (Retention)
                    └─ UI-NFR-013 (Consent)
  Track B: 6 Quick Wins parallel

Phase 2 (Sprint 1B — Auth-Trio + Drift-Sync-Slices)
  Auth seriell: REQ-024 (RBAC) → REQ-023 (Service Accounts) → REQ-027 (Light)
  Drift-Sync (parallel): REQ-014 (Mini), REQ-015 (Mini)
  Gekoppelt: REQ-013 Detach + REQ-022 W-010 (gemeinsamer PR)
  REQ-022 Outdoor-Slice (eigenständig)
  REQ-013 SuccessionPlan (optional, Sprint 2)

Phase 3 (Strategische Bausteine)
  REQ-009 + NFR-013 + UI-NFR-012 unabhängig
```

## Empfohlener Start

**Phase 0 abgeschlossen (2026-04-28)**. Detail-Befunde:
[`phase-0-drift-findings.md`](phase-0-drift-findings.md).

**Nächster Start**: **Phase 1** (Compliance-Track A: REQ-025 + NFR-011 + UI-NFR-013)
parallel zu **Phase 1 Track B** (6 Quick-Win-E2E-Tests). Die zwei kleinsten
Drift-Sync-PRs aus Sprint 1B (REQ-014 WateringEvent, REQ-015 iCal/Feed) können
zusätzlich als Side-Track ausgeführt werden, da sie disjunkte Skills brauchen.

## Status

- 2026-04-28: Initialer Plan-Entwurf verfasst.
- 2026-04-28: Phase 0 abgeschlossen — alle 6 Drift-Truthing-Plans als Slices
  reklassifiziert; Sprint 1B von 3 PRs auf 7–8 PRs erweitert.

Wird mit jedem Sprint-Closing aktualisiert (Audit-Re-Run schiebt abgearbeitete
Plans aus dem Index, dieser Plan zeigt nur Phase-Fortschritt + Risiken).
