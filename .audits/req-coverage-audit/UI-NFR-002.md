---
audit-type: req-coverage-plan
requirement: UI-NFR-002
title: Barrierefreiheit
type: ui-nfr
spec_path: spec/ui-nfr/UI-NFR-002_Barrierefreiheit.md
coverage_score: 50%
status: lueckenhaft
priority: warning
effort: M
created: 2026-04-27
audit_run: 1546aab6
---

# Ausfuehrungsplan: UI-NFR-002 Barrierefreiheit

## Kontext
- **Spec**: `spec/ui-nfr/UI-NFR-002_Barrierefreiheit.md`
- **Coverage**: 50%
- **Status**: Lueckenhaft
- **Aufwand-Schaetzung**: M (1 Pflicht-Artefakte fehlen)

## Erwartete Artefakte

### Dimension: frontend (1/1)

| Rolle | Pfad | Kind | Optional | Status | Evidenz / Begruendung |
|---|---|---|---|---|---|
| aria_landmark | `src/frontend/src/**/PageTitle.tsx` | glob | ja | OK | src/frontend/src/components/layout/PageTitle.tsx |

### Dimension: tests (0/1)

| Rolle | Pfad | Kind | Optional | Status | Evidenz / Begruendung |
|---|---|---|---|---|---|
| a11y_test | `src/frontend/src/test/accessibility.test.tsx` | file | nein | FEHLT |  |

### Dimension: drift (n/a)

| Rolle | Pfad | Kind | Optional | Status | Evidenz / Begruendung |
|---|---|---|---|---|---|
| marker_clean | `(memory_status_field)` | drift | nein | n/a | _(Begruendung: kein memory_status_field gepflegt)_ |
| cross_refs_intact | `(cross_refs)` | drift | ja | n/a | _(Begruendung: keine Cross-References deklariert)_ |
| spec_version_present | `spec/ui-nfr/UI-NFR-002_Barrierefreiheit.md` | drift | ja | n/a | _(Begruendung: Keine Versionsangabe in der Spec extrahierbar (optional, nice-to-have))_ |

## Aufgaben (priorisiert, abarbeitbar)

### Aufgabe 1 — a11y_test anlegen [S]
- **Zu tun**: Testdatei anlegen fuer a11y_test
- **Pfad**: `src/frontend/src/test/accessibility.test.tsx` (file)
- **Spec-Referenz**: `spec/ui-nfr/UI-NFR-002_Barrierefreiheit.md` — Sektion zu a11y_test
- **Begruendung**: Spec-Vorgabe
- **Akzeptanzkriterium**: Datei existiert + 1 Smoke-Test (falls Code) bzw. Glob matched (falls Pattern)
- **Empfohlener Agent**: `frontend-usability-optimizer`

## Empfohlene Skill-Sequenz
1. Aufgaben in obiger Reihenfolge abarbeiten (jeweils kleinster sinnvoller Commit)
2. `/req-coverage-audit UI-NFR-002` zur Verifikation nach jedem groesseren Block
3. Bei Coverage-Erreichen 100 % wird der Plan beim naechsten Full-Audit automatisch geloescht (git log bewahrt History)
