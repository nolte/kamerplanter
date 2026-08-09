# Requirements — Species-Mandanten-Ownership (Issue #808, REQ-001 v4.0)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **Was:** `Species` erhält echte Mandanten-Ownership: ein `tenant_key`-Feld, auf
  jedem Schreibpfad gesetzt, plus ein tenant-bewusstes Leseverhalten auf der
  heute globalen Species-Route — so bleiben globale Seed-Arten für alle sichtbar,
  während tenant-eigene Arten nicht mehr an fremde Mandanten leaken. Umsetzung von
  REQ-001 v4.0 (`spec/req/REQ-001_Stammdatenverwaltung.md:68`) für Species.
- **Für wen:** Gemeinschaftsgarten-Mitglieder und -Verwalter (Outcome O-4,
  saubere Mandantentrennung); der globale Seed-Katalog bleibt für alle sichtbar.
- **Explizit ausserhalb (Folge-Requirements):**
  - **Cultivar** — REQ-001 v4.0 nennt Cultivar neben Species; operator-Entscheid
    „Species-only zuerst" verschiebt Cultivar in ein separates Folge-Requirement.
  - Die **`tenant_has_access`-Edge** (explizite Grants über Ownership hinaus, in
    REQ-001 v4.0 genannt, heute nirgends erzeugt) — zurückgestellt; die
    Cutover-Regel + Ownership-Prädikat liefern die Isolation ohne sie.
  - Der Frontend-**Origin-Filter** (#397, eigenes Requirement
    `species-origin-filter.md`).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `3` (2 verbraucht)
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` (`min_d c_d ≥ τ_high`; die beiden EVPI-tragenden Entscheidungen — Backfill-Policy und Scope-Grenze — sind teach-back-bestätigt, keine positive-EVPI-Frage verbleibt)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification | #808 Scope + Akzeptanzkriterien (Autor nolte, autoritativ); REQ-001 v4.0 |
| `non_functional` | yes | 0.9 | interpretation | #808 „beide Richtungen" + `TestSpeciesScopeConsistency` (#816); #324-Regressionsklasse |
| `constraints` | yes | 0.85 | interpretation | Code: `get_current_tenant` an `/t/{slug}/` gebunden (`auth.py:59`); #324-Prädikat 3–4× dupliziert; #780/REQ-049-Achse |
| `domain_objects` | yes | 0.9 | interpretation | `Species`, `tenant_key`, `origin` (DataOrigin), #324-Union-Prädikat, `tenant_has_access`-Edge |
| `actors` | yes | 0.85 | interpretation | Authentifizierter Aufrufer / Tenant-Mitglied (O-4); globaler System-Katalog (`tenant_key == ""`) |
| `acceptance_criteria` | yes | 0.85 | specification | #808 Akzeptanzkriterien-Checkliste (operator-authored) |
| `edge_cases` | yes | 0.85 | specification | **Teach-back bestätigt:** Cutover-Regel für Bestands-`origin:tenant`-Species (kein recoverable Owner) |
| `scope_boundaries` | yes | 0.85 | specification | **Teach-back bestätigt:** Species-only zuerst; Cultivar + `tenant_has_access`-Edge als Folge-Requirement |

## Requirements

<!-- EARS/CNL form, tagged confirmed/assumed, traced to the utterance/source. -->

- **R1** — Das `Species`-Modell SHALL ein `tenant_key`-Feld tragen (leer `""` = global/System, analog zum Hybrid-Katalog).
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: REQ-001 v4.0 + #808 „the field"
- **R2** — WHEN eine Species über einen interaktiven Create-Pfad angelegt wird, the system SHALL `tenant_key` aus dem authentifizierten Tenant-Kontext stempeln; System-/Seed-/Enrichment-/Import-Pfade SHALL `tenant_key == ""` (global) setzen.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #808 „written on every create path" + Backfill-Teach-back (nur neue Species binden an Tenant)
- **R3** — WHEN Species auf der globalen Route gelesen werden, the system SHALL das Mandanten-Union-Prädikat anwenden (`tenant_key == @caller_tenant OR tenant_key == "" OR tenant_key == null`), sodass globale und eigen-Tenant-Arten zurückkommen und fremd-Tenant-Arten ausgeschlossen sind.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #808 „another tenant's species do not leak" + #324-Union
- **R4** — Das Union-Prädikat SHALL ein einziger geteilter Helfer sein, extrahiert aus den 3–4 duplizierten Inline-Kopien (`fertilizer_repository.py:42`, `nutrient_plan_repository.py:45`, `task_repository.py:60`, `ai_repository`-Variante); keine vierte Kopie.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: #808 „one shared predicate, extracted from the three existing copies"
- **R5** — Das System SHALL einen Tenant-Auflösungs-Mechanismus für globale-aber-tenant-bewusste Routen bereitstellen (heute ist `get_current_tenant` strukturell an den `/t/{slug}/`-Path-Parameter gebunden), und dessen Entwurf SHALL dokumentiert werden.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #808 „Tenant resolution … is designed and documented"; die konkrete Mechanismus-Form ist Design (siehe A1)
- **R6** — Bestands-`origin:tenant`-Species SHALL kein `tenant_key` erhalten und per expliziter Cutover-Policy Teil des geteilten Katalogs bleiben; nur neu angelegte Species binden an einen Tenant. Ein Default-Tenant-Stamp SHALL NICHT angewandt werden.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: **Teach-back „Cutover-Regel (final)"**; Default-Stamp = #324-Regression verbatim
- **R7** — Das System SHALL globale Seed-Species für jeden Tenant sichtbar halten (kein #324-Failure-Mode) UND fremd-Tenant-Species nicht leaken; beide Richtungen SHALL getestet sein.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: #808 Akzeptanzkriterium „Both directions"
- **R8** — Species-Count und -Listing SHALL die Collection identisch einschränken; `TestSpeciesScopeConsistency` (#816) SHALL grün bleiben.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: #808 „Count and listing cannot diverge"; #816
- **R9** — Die Backfill-Entscheidung SHALL mit Begründung vor der Implementierung dokumentiert sein (erfüllt durch dieses Artefakt + R6).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: #808 Akzeptanzkriterium 1 + Teach-back

## Surviving assumptions / open risks

- **A1 (assumed):** Die konkrete Form des Tenant-Auflösungs-Mechanismus (R5) — z. B. optionaler Tenant-Kontext aus JWT/Membership vs. eine tenant-bewusste Variante der globalen Route vs. ein expliziter Kontext-Header — ist eine **Design-Entscheidung der Feature-Zerlegung/Implementierung**, nicht dieses Requirements. Sie sitzt auf der #780/REQ-049-Achse; das Requirement fixiert das Verhalten (R3), nicht den Mechanismus.
- **A2 (open risk):** Zwischenzustand-Inkonsistenz — mit Species gescoped, Cultivar aber nicht, bleiben **Cultivars global sichtbar**, bis das Cultivar-Folge-Requirement geliefert ist. Operator-akzeptiert mit der Wahl „Species-only zuerst".
- **A3 (assumed):** Es existiert genau ein interaktiver Create-Pfad für tenant-eigene Species (`app/api/v1/species/router.py:112`, `origin=DataOrigin.TENANT`); alle übrigen Pfade (import/seed/enrichment/`upsert_by_normalized_scientific_name`) sind global und stempeln `tenant_key == ""`. Aus #808-Operator-Kommentar; in der Implementierung zu verifizieren.
- **A4 (deferred, nicht Risiko):** Die `tenant_has_access`-Edge (REQ-001 v4.0) ist bewusst ausserhalb — explizite Grants über Ownership hinaus sind ein eigenes Folge-Requirement.
