---
audit-type: req-coverage-plan
requirement: UI-NFR-019
title: Kiosk-Modus
type: ui-nfr
spec_path: spec/ui-nfr/UI-NFR-019_Kiosk-Modus.md
coverage_score: n/a
status: idee
priority: none
effort: S
created: 2026-04-30
audit_run: 340e527c
---

# Ausfuehrungsplan: UI-NFR-019 Kiosk-Modus

## Kontext
- **Spec**: `spec/ui-nfr/UI-NFR-019_Kiosk-Modus.md`
- **Coverage**: n/a
- **Status**: Idee
- **Aufwand-Schaetzung**: S (0 Pflicht-Artefakte fehlen)

## Erwartete Artefakte

### Dimension: frontend (n/a)

| Rolle | Pfad | Kind | Optional | Status | Evidenz / Begruendung |
|---|---|---|---|---|---|
| kiosk_page | `src/frontend/src/**/Kiosk*.tsx` | glob | ja | n/a |  |
| touch_mode | `src/frontend/src/**/TouchMode*.tsx` | glob | ja | n/a |  |

### Dimension: drift (n/a)

| Rolle | Pfad | Kind | Optional | Status | Evidenz / Begruendung |
|---|---|---|---|---|---|
| marker_clean | `(memory_status_field)` | drift | nein | n/a | _(Begruendung: kein memory_status_field gepflegt)_ |
| cross_refs_intact | `(cross_refs)` | drift | ja | n/a | _(Begruendung: keine Cross-References deklariert)_ |
| spec_version_present | `spec/ui-nfr/UI-NFR-019_Kiosk-Modus.md` | drift | ja | n/a | _(Begruendung: Keine Versionsangabe in der Spec extrahierbar (optional, nice-to-have))_ |

## Aufgaben (priorisiert, abarbeitbar)

_Keine Pflicht-Artefakte fehlen. Coverage-Defizit liegt nur in optionalen Artefakten oder Drift-Findings._

## Empfohlene Skill-Sequenz
1. Aufgaben in obiger Reihenfolge abarbeiten (jeweils kleinster sinnvoller Commit)
2. `/req-coverage-audit UI-NFR-019` zur Verifikation nach jedem groesseren Block
3. Bei Coverage-Erreichen 100 % wird der Plan beim naechsten Full-Audit automatisch geloescht (git log bewahrt History)
