---
id: F-20
title: Bodengefahren am Beet
status: in_progress
roadmap_item: R-20
sprint: 4
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@a38d18746
  findings:
    - kind: prior-art
      target: src/backend/app/api/v1/locations/tenant_router.py:291
      resolution: proceed
      evidence: "Location routes use require_permission(LOCATION, UPDATE) (grower+) and DELETE (lead only) (:291-413); resolve_owned_location (location_ownership.py:77) checks the tenant via the site; soil-analyses (:1027) is a sub-resource pattern."
    - kind: drift
      target: spec/req/REQ-054_Automatische-Anbauplanung.md:441
      resolution: proceed
      evidence: "AP-API-012 defines only POST|DELETE /locations/{key}/soil-hazards; the hazards are read with the location (acceptance-1), stated in the spec update."
    - kind: drift
      target: src/frontend/src/pages/pflanzen/TerminationDialog.tsx:68
      resolution: proceed
      evidence: "No pathogen/confirmed/source at a loss today; operator decision: captured in F-19, promotion offer here."
    - kind: prior-art
      target: src/backend/app/common/enums.py:390
      resolution: proceed
      evidence: "Hydroponics is encoded several times (irrigation_system HYDRO/NFT/EBB_FLOW :393-396, SubstrateType.HYDRO_SOLUTION :413, substrate_type_override, DWC/NFT :1693); operator decision: Location.irrigation_system is authoritative."
    - kind: drift
      target: src/backend/app/domain/models/garden_plan_export.py:86
      resolution: proceed
      evidence: "Bed export carries soil_profile/rotation flags (:86-106) but no soil_hazards; operator decision: include in plan export/import and tenant export."
    - kind: drift
      target: spec/req/REQ-054_Automatische-Anbauplanung.md:146
      resolution: proceed
      evidence: "§5.2 puts affected_families on the bed entry; operator decision: the entry references the hazard key and hosts resolve from the knowledge table (F-18)."
---

## Description

Ein bestätigter Befall mit einem dauerhaften Bodenerreger betrifft ein Beet
über Jahre — unabhängig davon, welche Pflanze gerade darin steht. Heute kann
man das nirgends festhalten.

Nach dieser Änderung zeigt jedes Beet seine Bodengefahren: welcher Erreger,
welche Pflanzen er gefährdet, seit wann und wer ihn bestätigt hat. Gärtner
können eine Gefahr eintragen, nur die Leitung kann sie wieder entfernen.
Wird eine eingegangene Pflanze mit benanntem, bestätigtem Bodenerreger
erfasst, bietet die App an, die Gefahr für das Beet zu übernehmen; ein
unbestätigter Verdacht erzeugt nie einen Eintrag. Bei Hydrokultur entsteht
statt einer Bodengefahr der Hinweis, das System zu reinigen. Bodengefahren
reisen mit Gartenplan- und Mandanten-Export.

## Acceptance criteria

- [x] **acceptance-1** Ein Beet zeigt seine Bodengefahren mit Erreger, gefährdeten Pflanzen, Bestätigungsdatum und Quelle.
- [x] **acceptance-2** Gärtner tragen eine Bodengefahr ein, nur die Leitung entfernt sie (API und Oberfläche); Gefäße (Kübel, Zelt, Regal) haben keine Bodengefahren.
- [x] **acceptance-3** Nach dem Erfassen eines bestätigten bodenbürtigen Ausfalls mit Erreger aus der Liste bietet die App die Übernahme ins Beet an; ein unbestätigter Ausfall erzeugt nie einen Eintrag.
- [x] **acceptance-4** Ein bodenbürtiger Ausfall an einem Hydrokultur-Standort erzeugt keine Bodengefahr, sondern den Hinweis „System reinigen und desinfizieren“.
- [x] **acceptance-5** Bodengefahren eines fremden Mandanten sind weder lesbar noch änderbar.
- [x] **acceptance-6** Bodengefahren sind Teil von Export und Import des Gartenplans und des Mandanten-Exports.

## Test hooks

- **acceptance-1** — `src/backend/tests/api/test_bed_soil_hazards_api.py::TestABedShowsItsSoilHazards` (GET location and bed summary carry `soil_hazards[]` with hosts resolved from the table; the stored entry holds the key only), `src/backend/tests/unit/domain/engines/test_bed_soil_hazard_engine.py::TestTheTableResolvesTheHosts`, `src/frontend/src/features/gardenPlanner/bed/BedView.test.tsx` ("shows each hazard with its pathogen, …") — green
- **acceptance-2** — `src/backend/tests/api/test_bed_soil_hazards_api.py::TestGrowersAddOnlyTheLeadRemoves` (grower POST 201, viewer 403, grower DELETE 403, lead DELETE 204, planter/tent/shelf 422 `soil_hazard.container`), `src/backend/tests/unit/domain/engines/test_bed_soil_hazard_engine.py::TestWhereASoilHazardMayStand`, `src/backend/tests/integration/test_bed_soil_hazard_repository.py::TestAnEditKeepsThem`, UI: `src/frontend/src/features/gardenPlanner/bed/BedView.test.tsx` (viewer/grower/lead, vessels and hydroponics) — green
- **acceptance-3** — `src/backend/tests/api/test_bed_soil_hazards_api.py::TestTheOfferAfterALoss` (offer in the remove answer, nothing written until `plant_key` is posted, unconfirmed and juglone refused by the service), `src/backend/tests/unit/domain/engines/test_bed_soil_hazard_engine.py::TestALossBecomesAnEntryOnlyWhenConfirmed` / `TestWhatALossProposes`, `src/backend/tests/integration/test_bed_soil_hazard_repository.py::TestTheServiceOverTheRealRepositories`, vitest `src/frontend/src/features/gardenPlanner/bed/SoilHazardFollowUpDialog.test.tsx` and `src/frontend/src/test/pages/PlantInstanceDetailPageRemove.test.tsx` — green
- **acceptance-4** — `src/backend/tests/api/test_bed_soil_hazards_api.py::TestHydroponics` (`irrigation_system = nft`: `clean_system`, no entry, manual entry 422), `src/backend/tests/unit/domain/engines/test_bed_soil_hazard_engine.py` (hydro, nft, ebb_flow; also unconfirmed and in a tent) — green
- **acceptance-5** — `src/backend/tests/api/test_bed_soil_hazards_api.py::TestAnotherTenantsHazards` (read, summary, record, take-over, remove: same 404 as an unknown bed; a foreign plant key at an own bed), `src/backend/tests/integration/test_garden_plan_tenant_isolation.py` (cases `record_soil_hazard`, `take_over_soil_hazard`, `remove_soil_hazard`, `get_location`; real `resolve_owned_location` against ArangoDB, falsified by the unscoped stub), `src/backend/tests/integration/test_bed_soil_hazard_repository.py` (foreign and absent bed, concurrent write) — green
- **acceptance-6** — `src/backend/tests/unit/domain/services/test_garden_plan_import_service.py::TestSoilHazardsInTheBackup2888` (plan export/import roundtrip, old file, unknown key refused, vessel/non-bed dropped with `no_soil`, foreign site refused), `src/backend/tests/integration/test_tenant_export_roundtrip.py::test_roundtrip_export_import_export_differs_only_in_keys` (tenant archive), `src/backend/tests/unit/domain/models/test_garden_plan_export.py` (Art. 15 manifest lists the field) — green

## Consistency notes

**Route and ownership prior art (proceed).** Established: location routes use
`require_permission(LOCATION, UPDATE/DELETE)` (`tenant_router.py:291-413`),
`resolve_owned_location` checks the tenant through the site
(`location_ownership.py:77`), and soil analyses (`:1027`) are the sub-resource
pattern. AP-API-012 (`REQ-054:441`) is implemented with these.

**Read path (drift, proceed).** Established: AP-API-012 defines only POST and
DELETE. The hazards are read with the location document (acceptance-1); the
spec update in F-18 states it.

**Pathogen capture (decision).** Established: `TerminationDialog.tsx:68-74`
has no pathogen/confirmed/source. Operator decision 2026-11-17: F-19 captures
them, F-20 offers the promotion.

**Hydroponics signal (decision).** Established: hydroponics is encoded in
several places (`enums.py:393-396,413,1693`, `plant_instance.py:78`). Operator
decision 2026-11-17: `Location.irrigation_system ∈ {HYDRO, NFT, EBB_FLOW}` is
authoritative.

**Host snapshot vs. reference (decision).** Established: REQ-054 §5.2
(`:146`) stores `affected_families` on the entry. Operator decision
2026-11-17: the entry references the hazard key; hosts resolve from the F-18
table, so later research applies to existing findings.

**Knowledge-table caller (handover from F-18).** `YamlSoilHazardKnowledgeSource` has no production caller yet and loads the table lazily, once per instance; wiring it (DI factory, one instance per process, behaviour on a corrupt file) is F-20's. Consumers display and evaluate only `evidence.status`, never "{sources}/3": with empty `years`, `sources` counts the sources that state any figure at all, not support for a value. Open operator decisions P1–P7 are listed in `soil-hazard-knowledge.md`.

**Export (decision).** Established: `garden_plan_export.py:86-106` carries
the soil profile but no hazards. Operator decision 2026-11-17: hazards travel
with plan export/import and the tenant export (R-19).

## Risks

- Containers are excluded by type; a raised bed filled with bought soil still counts as a bed — `substrate_replaced_on` (F-21) covers it.

## References

- Issue #2888, roadmap item R-20; after F-18, parallel to F-19
- `project/requirements/soil-hazards-replant.md` (R3, R4, R9, R12, R14, R16, R19)
