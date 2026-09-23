# Group pre-analysis: 2026-09-23-settings-yml-truth

> Run-scoped artifact; removed fix-forward before the bundle merges.

## Scope of this analysis

**Research question:** Warum erscheint das deklarierte Label nicht, und was fehlt der `strict`-Begründung?

**The group's single logical change, in one sentence:** `.github/settings.yml` describes the repository state it actually produces — the declared label becomes applicable and the `strict` rationale records its slot cost.

**Out of scope:** Merge-Queue / `strict` abschalten (Operator-Entscheidung #1584: nicht jetzt).

**Tier:** 2 — ein Repository, Konfiguration.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1632 | infra | shared touch surface | `.github/settings.yml` `labels:` block |
| #1584 | infra | shared touch surface | `.github/settings.yml` `strict` comment (:96-110) |

**Dependency ordering:** unabhängig.

**Shared touch surface:** `.github/settings.yml`.

## Measured premises

| Claim | Messung | Ergebnis |
|---|---|---|
| #1632: Label fehlt | `gh api repos/nolte/kamerplanter/labels --paginate --jq '.[].description|length'` max 77; kein `security-scan` | bestätigt |
| #1632 Ursache (neu) | YAML-Länge der Beschreibung: `193`; `gh label create zz-len-probe --description <101×x>` → `description is too long (maximum is 100 characters)` | **Ursache gemessen**: Beschreibung > 100 Zeichen, App-Sync scheitert für dieses Label |
| #1584 AK1 | Nachmessung 2026-09-20 im Issue: 27/40/23 % cancelled | erfüllt; Rest = Doku (Operator-Entscheidung) |

## Mode decision

**Mode:** A — zwei Kommentare/Werte in einer Datei, nichts entfernbar-riskant.

## Structural finding

**Cluster shape:** neither — gemeinsame Datei, keine gemeinsame Ursache.

**Process finding:** Ein deklarativer Settings-Block wird nicht gegen die API-Grenzen geprüft; der Fehler ist nur im App-Log sichtbar. **Preventive change:** Unit-Test, der jede deklarierte Label-Beschreibung auf ≤ 100 Zeichen prüft.

## Completeness matrix

| Member | Source/Config | Tests | Spec | Docs |
|---|---|---|---|---|
| #1632 | Beschreibung ≤ 100 Zeichen; Aufruf-Hinweis in den YAML-Kommentar; check: Test unten | `src/backend/tests/unit/guards/test_settings_labels_fit_api.py` rot-zuerst; check: pytest | not applicable — kein Spec regelt das Label | not applicable — interne Triage-Markierung |
| #1584 | `strict`-Kommentar um Slot-Kosten + Wiederöffnungsbedingung; check: `pre-commit run --files .github/settings.yml` | not applicable — Kommentar | not applicable | not applicable |

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #1632 | no matching specialist — orchestrator (config + guard test) | `pytest tests/unit/guards/test_settings_labels_fit_api.py` vor der Änderung | `1 failed, 1 passed in 0.37s` |
| #1632/#1584 | orchestrator | `pytest test_settings_labels_fit_api.py test_required_contexts_are_unfiltered.py` nach der Änderung | `32 passed in 3.36s`; Beschreibung jetzt 67 Zeichen, `strict: True` unverändert |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| — | local adaptation | `test_lane_filters_cover_measured_inputs.py::test_no_manifest_is_older_than_its_job` rot, **vorbestehend**: `backend-guards--integration.yaml` veraltet gegen `backend-guards.yml` (nicht von diesem Branch berührt); Guard ist advisory; gehört zu #1683. |
