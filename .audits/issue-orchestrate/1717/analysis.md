---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: "1717"
classification: infra
secondary-classes: []
route: direct
status: approved
created: "2026-09-24"
---

# Issue Orchestration — Pre-analysis (#1717, Restumfang)

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1717 — E2E compose workers lack the tombstone salt and the API's storage, so export and erasure cannot run there
- **URL**: https://github.com/nolte/kamerplanter/issues/1717
- **Labels**: none
- **Linked items**: #1723 (compose/overlay, gemergt `a950d4cec`), #1721 (REQ-025 v1.10, `89fc264f9`), #1715 (Probe-Set), #1680
- **Prior art checked**: `gh pr list --search 1717` → nur #1723 (merged) und #1721 (merged); kein offener PR.

## Classification

- **Primary class**: infra
- **Rationale**: Test-/Audit-Infrastruktur (Reach-Probe-Set und T2-Stack), kein Produktcode, kein CI-Workflow.
- **Asserted cause verified**: confirmed —
  - Worker-Workarounds entfallen: `docker-compose.e2e.yml:373` (`ERASURE_TOMBSTONE_SALT` auf `celery-worker-full`), `:379` (`object-storage-full:/data`); `docker-compose.reach.yml` enthält nur Ports, Query-Tracking und das Volume-Backing.
  - Probes stale: `reach_audit.py --repo .` (ohne T2) an HEAD `00a58808028b` meldet 4 Probes `declaration changed since derivation … last changed in 89fc264f9169` (REQ-025 und `data_export_engine.py`).

## Scope

- **In scope**: Re-Derive der Probes zu den Deklarationen `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` und `src/backend/app/domain/engines/data_export_engine.py` über `capability-reach-audit derive` (Scanner-Entwürfe, Gate), Neuschreiben von `_not-constructible.yml`, danach `reach_audit.py --include-t2` auf dem Reach-Stack ohne Workarounds.
- **Out of scope**: neue Probes über andere Deklarationen, Schemaänderungen, Produktcode, Anpassen von Erwartungen an Beobachtungen.

## Route

- **Decision**: direct
- **Rationale**: ein Ergebnis, ein PR-Strang, kein Roadmap-Eintrag.

## Work packages

### P1 — Re-Derive der stale Probes

- **Problem statement**: #1721 hat REQ-025 §3.1 von einer Inventar-Abschrift auf Regeln + Code-Verweise umgestellt und `data_export_engine.py` erweitert; die vier Probes und zwei Manifest-Einträge sind stale.
- **Acceptance criteria**: Runner meldet für keine Probe mehr `declaration changed since derivation`; neue Probes tragen `derived_from` ≥ `89fc264f9`.
- **Touched files / artifacts**: `project/reach-probes/*.yml`
- **Specialist**: nolte-engineering:capability-reach-audit (Skill) → nolte-engineering:capability-reach-scanner (Agent)
- **Depends on**: none

### P2 — T2-Lauf ohne Workarounds

- **Problem statement**: Abnahme #1717: `task reach:stack:up` + `reach_audit.py --include-t2` klassifiziert die Export-/Löschprobes `reached`.
- **Acceptance criteria**: Report unter `.audits/capability-reach/` mit Klassen der Export-/Löschprobes; Abweichungen werden roh berichtet, nicht angepasst.
- **Touched files / artifacts**: `.audits/capability-reach/2026-09-24.md` (vom Runner geschrieben)
- **Specialist**: bundled runner `reach_audit.py`
- **Depends on**: P1

## Dependency ordering

P1 → P2

## Risks

- Scanner kann für die Requirement-Deklaration nach #1721 keine zählbare Erwartung mehr ableiten → `not_constructible`; wird als Ergebnis berichtet.

## Open questions

none (Gates vom Betreiber vorab freigegeben, Parent-Session 2026-09-24)

## Dispatch log
