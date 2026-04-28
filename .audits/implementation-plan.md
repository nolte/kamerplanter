---
audit-type: implementation-plan
target-repo: kamerplanter
based-on: .audits/req-coverage-audit.md, .audits/execution-roadmap.md
plans-considered: 32
created: 2026-04-28
status: draft
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

### Phase 0 — Drift-Truthing (1–2 Tage)

| Plan | Vermutung | Aktion |
|---|---|---|
| REQ-013 (v2.0 → v2.3) | Backend hinkt | Spec-Diff lesen, Code prüfen, MEMORY-Update oder Sync-PR |
| REQ-014 (v1.4 → v1.6) | Backend hinkt | dito |
| REQ-015 (v1.1 → v1.6) | Backend hinkt | dito |
| REQ-022 (v2.3 → v2.5) | Backend hinkt | dito |
| REQ-023 (v1.10 Service Accounts) | Service Accounts fehlen | reklassifizieren als Slice → Sprint 1B |
| REQ-024 (v1.4 RBAC) | RBAC fehlt | reklassifizieren als Slice → Sprint 1B |

**Ergebnis**: 4 Plans potentiell auf 100 %, 2 reklassifiziert nach 1B. Index schrumpft auf ~28.

**1 Mini-PR**: `chore(audit): drift-truthing for sprint-2 plans`

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

### Phase 2 — Auth-Trio (Sprint 1B) — 1.5 Wochen

Eng gekoppelt, **muss seriell** in dieser Reihenfolge:

1. **REQ-024 RBAC Permission-Matrix** (`feat(auth): RBAC permission matrix REQ-024`) — Voraussetzung für 23, 27
2. **REQ-023 Service Accounts** (`feat(auth): service accounts REQ-023`)
3. **REQ-027 Light-Modus** (`feat(auth): light-mode platform-tenant REQ-027`)

**3 PRs**.

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

| Status | Heute | nach Phase 0 | nach Phase 1 | nach Phase 2 | nach Phase 3 |
|---|---|---|---|---|---|
| Implementiert | 40 (57 %) | 44 (63 %) | 50 (71 %) | 53 (76 %) | 56 (80 %) |
| Plans offen | 32 | 28 | 19 | 16 | 13 |

→ **80 % Implementierungsgrad in 5–7 Wochen** ohne KI-Familie und ohne Sprint 5+.

## Risiken

1. **Drift-Truthing kann eskalieren**: Wenn Backend 4× hinterherhinkt, sind das 4× echte Slice-PRs statt MEMORY-Updates → Phase 0 dehnt sich auf 1–2 Wochen.
2. **REQ-025 ist groß** (8 Aufgaben, 14 Endpunkte): `/implement REQ-025` als Single-Skill könnte zu groß sein — eventuell aufteilen in 2 PRs (Backend + Frontend separat).
3. **REQ-024 vs. REQ-023 Reihenfolge**: `require_permission()` aus REQ-024 wird in REQ-023 gebraucht — falls REQ-023 zuerst, gibt es Refactoring-Schulden.
4. **Sprint 2 Drift-Reklassifikation** kann REQ-023/REQ-024 in Sprint 1B aufblähen, wenn der MEMORY-Status konkrete Code-Lücken aufdeckt.

## Abhängigkeitsgraph (kritischer Pfad)

```
Phase 0 (Drift-Truthing)
  ├── REQ-013/14/15/22 → MEMORY-Update wahrscheinlich
  └── REQ-023/24 → Reklassifikation in Phase 2

Phase 1 (Compliance + Quick Wins)
  Track A: REQ-025 ──┬─ NFR-011 (Retention)
                    └─ UI-NFR-013 (Consent)
  Track B: 6 Quick Wins parallel

Phase 2 (Auth-Trio, seriell)
  REQ-024 (RBAC) ──→ REQ-023 (Service Accounts) ──→ REQ-027 (Light-Modus)

Phase 3 (Strategische Bausteine)
  REQ-009 + NFR-013 + UI-NFR-012 unabhängig
```

## Empfohlener Start

**Phase 0 jetzt** — Drift-Truthing für REQ-013/14/15/22 parallel via 4 Subagents (jeder liest Spec + Code, meldet "synchron / nicht synchron"). REQ-023/24 reklassifiziert nach Phase 2. Aufwand: 1 Sitzung, ein PR mit MEMORY-Updates oder Sync-Code.

## Status

Initialer Plan-Entwurf. Wird mit jedem Sprint-Closing aktualisiert (Audit-Re-Run schiebt
abgearbeitete Plans aus dem Index, dieser Plan zeigt nur Phase-Fortschritt + Risiken).
