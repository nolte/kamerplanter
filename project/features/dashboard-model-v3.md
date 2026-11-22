---
id: F-22
title: Dashboard-Modell v3 pro Nutzer und Mandant
status: draft
roadmap_item: R-21
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@a38d18746
  findings:
    - kind: drift
      target: src/backend/app/api/v1/user_preferences/tenant_router.py:4
      resolution: proceed
      evidence: "Docstring 'Preferences are user-global (not per-tenant)' contradicts REQ-045 §2:65-69 and DoD :554; acceptance-1 aligns the code with the spec."
    - kind: drift
      target: src/backend/app/domain/services/user_preference_service.py:91
      resolution: proceed
      evidence: "get_preferences is write-free since #1461; operator decision: lazy migration derives on read and materialises on first write."
    - kind: drift
      target: src/backend/app/migrations/versions/v0031_dedup_user_singletons_unique_index.py:1
      resolution: proceed
      evidence: "user_preferences has a unique user_key index (collections.py:2648) and REQ-045 §2:65 says 'no new collections'; operator decision: new collection dashboards (tenant_key + user_key)."
    - kind: drift
      target: spec/req/REQ-045_Individualisierbares-Dashboard.md:610
      resolution: proceed
      evidence: "Scenario 5 / DoD :560 fix HTTP 200 with unknown keys dropped and scenario 3 :596 'not rendered'; _sanitize_layout (user_preference_service.py:18-40) drops them on save; operator decision: keep, hide in read mode, placeholder in edit mode, 422 for invalid config of known widgets."
    - kind: drift
      target: src/backend/app/domain/models/user_preference.py:98
      resolution: proceed
      evidence: "dashboard_layout=null means 'level default, not materialised' and follows level changes (REQ-045 §3.5:366); operator decision: null stays null."
    - kind: overlap
      target: F-24
      resolution: proceed
      evidence: "F-24 acceptance-6 adds plant_grid to the beginner default (today EXPERT: dashboard_widget_catalog.py:88, dashboardWidgetCatalog.ts:157-162), changing the visible dashboard of users without a stored layout."
    - kind: prior-art
      target: src/frontend/src/config/dashboardWidgetCatalog.ts:109
      resolution: proceed
      evidence: "Drift: quick_actions h 4 vs 2 (py:52), care_reminders module tasks vs care (py:54), winter_protection overwintering vs care (py:63), requiresSmartHome FE only (ts:130), CONFIG_SCHEMA FE only (WidgetConfigDialog.tsx:20-23); contract test checks only the key set (test_dashboard_widgets_contract.py:39-50); src/frontend/src/contracts/dashboard-widgets.json can carry the shared catalog."
    - kind: prior-art
      target: src/frontend/src/store/slices/userPreferencesSlice.ts:120
      resolution: proceed
      evidence: "migrateLocalDashboardLayout and dashboardLayoutStorage.ts exist (light → full); acceptance-5 extends them to v3."
    - kind: drift
      target: src/backend/app/domain/engines/tenant_erasure_engine.py:303
      resolution: proceed
      evidence: "user_preferences is account-scoped; a tenant-bound collection must pass test_tenant_erasure_inventory_is_complete.py and is derived into the tenant export (tenant_export_engine.py:660) unless EXCLUDED; GDPR export lists dashboard_layout (data_export_engine.py:1128); operator decision: acceptance-7."
    - kind: drift
      target: spec/req/REQ-045_Individualisierbares-Dashboard.md:486
      resolution: proceed
      evidence: "REQ-045 §4 allows writing from grower while PATCH only requires require_account_principal (tenant_router.py:33); operator decision: every member incl. viewers manages own dashboards, API keys stay excluded."
---

## Description

Heute hat jeder Nutzer genau ein Dashboard-Layout, das in allen Gärten
(Mandanten) gleich ist, obwohl Spec und Nutzerdoku „pro Mandant“ versprechen.
Widget-Einstellungen prüft nur die Oberfläche, und Frontend und Backend
führen den Widget-Katalog leicht unterschiedlich.

Dieses Feature legt das Fundament für mehrere Dashboards: Jedes Dashboard
gehört einem Nutzer in einem Mandanten, besteht aus Ansichten mit eigenen
Widgets und Layouts und wird serverseitig in einer eigenen Ablage gespeichert.
Beim ersten Aufruf erscheint das bisherige Layout unverändert als erstes
Dashboard. Ein gemeinsamer Katalog beschreibt jedes Widget samt
Einstellungsschema; Server und Oberfläche prüfen dagegen. Ein Widget, das es
nicht mehr gibt oder dessen Modul ausgeblendet ist, geht nicht verloren,
sondern lässt sich im Bearbeitungsmodus sehen und entfernen. Dashboards sind
privat: Sie verlassen den Mandanten nicht im Archiv, verschwinden mit dem
Ende der Mitgliedschaft und gehören zur eigenen Datenauskunft.

## Acceptance criteria

- [ ] **acceptance-1** Dashboards gehören einem Nutzer in einem Mandanten; jedes Mitglied (auch mit Leserechten) verwaltet seine eigenen, und niemand sonst kann sie lesen oder ändern.
- [ ] **acceptance-2** Beim ersten Aufruf in einem Mandanten erscheint das bisherige Layout unverändert als erstes Dashboard mit einer Ansicht; ein nie angepasstes Layout folgt weiter der Erfahrungsstufe.
- [ ] **acceptance-3** Ein gemeinsamer Katalog legt für jedes Widget Größen, Modul-Bindung und Einstellungsschema fest; ungültige Einstellungen eines bekannten Widgets lehnt der Server mit 422 ab, und Frontend und Backend weichen nicht mehr voneinander ab.
- [ ] **acceptance-4** Ein unbekanntes oder modul-ausgeblendetes Widget bleibt beim Speichern erhalten, ist in der normalen Ansicht unsichtbar und erscheint im Bearbeitungsmodus als Platzhalter „nicht verfügbar“ mit „Entfernen“.
- [ ] **acceptance-5** Im light-Modus ohne Anmeldung gilt dasselbe Modell lokal und wird nach der Registrierung übernommen.
- [ ] **acceptance-6** REQ-045 (v2: mehrere Dashboards, Mandantenbezug, Einstellungsschema, Szenarien 3/5, Rollen) und REQ-009 beschreiben das neue Verhalten.
- [ ] **acceptance-7** Dashboards sind nicht Teil des Mandanten-Archivs, werden mit dem Mandanten und mit dem Ende der Mitgliedschaft gelöscht und erscheinen in der Datenauskunft des Nutzers.

## Test hooks

- **acceptance-1** — router tests: owner 200; other user same/other tenant 404; viewer can write own; API key refused — pending
- **acceptance-2** — service tests: GET derives without write; first PATCH materialises; `null` layout follows level change — pending
- **acceptance-3** — contract test on the shared catalog (sizes, modules, schema) FE == BE; 422 for invalid config — pending
- **acceptance-4** — service + vitest: unknown key kept, hidden in read mode, placeholder in edit mode — pending
- **acceptance-5** — `userPreferencesSlice` migration test extended to v3 — pending
- **acceptance-6** — spec diff review — pending
- **acceptance-7** — `test_tenant_erasure_inventory_is_complete.py` classification, membership-end cascade test, GDPR export test — pending

## Consistency notes

**Per-tenant scope (drift, proceed).** Established: the router docstring
(`user_preferences/tenant_router.py:4-5`) states user-global preferences,
against REQ-045 §2 (`:65-69`) and DoD (`:554`). Acceptance-1 aligns the code
with the spec.

**Write-free reads (drift, proceed).** Established:
`user_preference_service.py:91` is write-free since #1461. Operator decision
2026-11-17: lazy migration — derive on read, materialise on first write
(acceptance-2).

**Storage (drift, proceed).** Established: `user_preferences` has a unique
`user_key` index (`v0031`, `collections.py:2648`) and REQ-045 §2 (`:65`) says
"no new collections". Operator decision 2026-11-17: new collection
`dashboards` with `tenant_key` + `user_key`; REQ-045 amended (acceptance-6).

**Unknown widgets (drift, proceed).** Established: REQ-045 scenario 5 / DoD
(`:610`, `:560`) and scenario 3 (`:596`) drop or hide unknown keys, and
`_sanitize_layout` (`user_preference_service.py:18-40`) deletes them on save.
Operator decision 2026-11-17: kept, hidden in read mode, placeholder in edit
mode; 422 only for invalid config of known widgets (acceptance-3/4).

**Null layout (drift, proceed).** Established: `dashboard_layout = null`
means the level default and follows level changes (`user_preference.py:98`,
REQ-045 §3.5 `:366`). Operator decision 2026-11-17: `null` stays `null`.

**Overlap with F-24 (proceed).** Established: F-24 adds `plant_grid` to the
beginner default (today expert: `dashboard_widget_catalog.py:88`,
`dashboardWidgetCatalog.ts:157-162`), so users without a stored layout see a
changed dashboard. Rationale for `proceed`: this is an intended change of the
level default owned by F-24; acceptance-2's "unchanged" applies to stored
layouts only (operator decision 2026-11-17). The two features stay separate
because the default content is widget scope, the model is storage scope.

**Catalog drift (prior-art, proceed).** Established: sizes and module gates
differ (`dashboardWidgetCatalog.ts:109,130` vs. `dashboard_widget_catalog.py:52,54,63`),
the config schema exists only in the frontend
(`WidgetConfigDialog.tsx:20-23`) and the contract test checks only the key
set (`test_dashboard_widgets_contract.py:39-50`).
`src/frontend/src/contracts/dashboard-widgets.json` can carry the shared
catalog.

**Light-mode storage (prior-art, proceed).** Established:
`migrateLocalDashboardLayout` (`userPreferencesSlice.ts:120`) and
`dashboardLayoutStorage.ts` exist and are extended (acceptance-5).

**Erasure and export (drift, proceed).** Established: `user_preferences` is
account-scoped (`tenant_erasure_engine.py:303`); a tenant-bound collection
must pass `test_tenant_erasure_inventory_is_complete.py` and is derived into
the tenant export (`tenant_export_engine.py:660`) unless excluded; the GDPR
export lists `dashboard_layout` (`data_export_engine.py:1128`). Operator
decision 2026-11-17: excluded from the archive, deleted with the tenant and on
membership end, included in the GDPR export (acceptance-7). The membership-end
cascade is unestablished and verified in the implementation.

**Roles (drift, proceed).** Established: REQ-045 §4 (`:486`) allows writing
from grower while the PATCH only requires an account principal
(`tenant_router.py:33`). Operator decision 2026-11-17: every member including
viewers manages own dashboards; API keys stay excluded.

## Risks

- A user in several tenants gets the old layout copied into each; later edits diverge per tenant (intended).
- Keeping unknown widget instances lets stale entries accumulate; the edit-mode placeholder is the cleanup path.

## References

- Epic #2502, roadmap item R-21
- `project/requirements/multi-dashboard.md` (R1, R2, R8, R9, R16–R23)
