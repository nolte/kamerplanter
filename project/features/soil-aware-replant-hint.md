---
id: F-21
title: Bodengefahren im Nachpflanz-Hinweis
status: done
roadmap_item: R-20
sprint: 4
created: 2026-11-17
ended: 2026-11-27
verifies_sprint_value: acceptance-1
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@a38d18746
  findings:
    - kind: prior-art
      target: src/backend/app/domain/engines/crop_rotation_validator.py:639
      resolution: proceed
      evidence: "validate_planting_in_location (:639-709) produces the findings; HintsPanel.tsx:99-117 renders backend codes; PlantingDialog.tsx:203,411-434 already has 'plant anyway' with a reason."
    - kind: drift
      target: src/backend/app/domain/engines/crop_rotation_validator.py:180
      resolution: proceed
      evidence: "not_applicable_reason returns before any check for rotation_exempt, rotation_enabled=False and planter/tent/shelf (:180-195, :677-681); operator decision: the hazard check bypasses the rotation gate, containers carry no hazard."
    - kind: drift
      target: spec/req/REQ-053_Grafische-Garten-Beetplanung.md:822
      resolution: revisit-after F-18 acceptance-1 (spec update)
      evidence: "§11.3 and GP-FR-131 (:1162) fix 'current calendar year (UTC)'; code checks removed_on.year == today.year (:587) and end.year - 1 (:616); changed only after the spec update."
    - kind: drift
      target: src/backend/app/domain/models/plant_instance.py:24
      resolution: proceed
      evidence: "PlantInstance has only planted_on/removed_on; operator decision: expected end = planted_on + species days_to_maturity (species.py:150), else calendar-year rule."
    - kind: drift
      target: src/backend/app/domain/models/site.py:263
      resolution: proceed
      evidence: "SoilProfile (:263-293) has no substrate_replaced_on; operator decision: add it."
    - kind: drift
      target: spec/analysis/agrobiology-soil-hazards-research-2888.md:286
      resolution: proceed
      evidence: "§5 sets hints per class while crop_rotation_validator.py:255 warns on every disease/pest; operator decision: covered by acceptance-7."
    - kind: prior-art
      target: spec/analysis/agrobiology-soil-hazards-research-2888.md:303
      resolution: proceed
      evidence: "clubroot: block duration 2/3, survival 3/3; operator decision: warning without time statement until max survival, then nothing (acceptance-2)."
    - kind: drift
      target: spec/req/REQ-054_Automatische-Anbauplanung.md:203
      resolution: revisit-after REQ-054 planner implementation
      evidence: "H-10 blocks the bed hard while F-21 only warns (D-09); deliberate, reconciled when the planner is built."
---

## Description

Wer einen ausgefallenen Platz nachbepflanzt oder ein Beet neu belegt, sieht
heute einen Fruchtfolge-Hinweis, der nur nach grober Ursache unterscheidet.
Ein bekannter Bodenerreger im Beet spielt keine Rolle, und „dieselbe Saison“
heißt schlicht „dasselbe Kalenderjahr“ — ein im März ersetzter
Herbstknoblauch zählt so fälschlich als Vorkultur.

Nach dieser Änderung warnt der Pflanzdialog gezielt, wenn die gewählte
Pflanze ein Wirt einer Bodengefahr des Beets ist: innerhalb der belegten
Anbaupause mit Zeitangabe, ohne belegte Dauer mit einer Warnung ohne Zeitangabe,
danach nur noch mit einem Hinweis. Man kann immer „trotzdem pflanzen“ und
eine Begründung angeben. Wurzelgallenälchen und Sklerotinia ergeben nur einen
Hinweis, weil sie fast alles befallen. Frisches Substrat hebt die Warnung auf;
„dieselbe Saison“ richtet sich nach dem Anbaufenster der ersetzten Pflanze,
und der Hinweis folgt der Ursachenklasse des Ausfalls.

## Acceptance criteria

- [x] **acceptance-1** Ist die gewählte Pflanze Wirt einer Bodengefahr des Beets, zeigt der Pflanzdialog innerhalb der belegten Anbaupause eine überstimmbare Warnung mit Zeitangabe, danach bis zur maximalen Überdauerung einen Hinweis; Pflanzen wird nie verhindert — auch nicht auf Beeten mit ausgeschalteter Fruchtfolge.
- [x] **acceptance-2** Ist keine Anbaupause belegt, warnt der Dialog ohne Zeitangabe — bis zum Ende der belegten Überdauerung, falls diese belegt ist, sonst unbefristet.
- [x] **acceptance-3** Wurzelgallenälchen und Sklerotinia ergeben nur einen Hinweis.
- [x] **acceptance-4** Eine Nachpflanzung innerhalb des Anbaufensters der ersetzten Pflanze (Pflanzdatum + Kulturdauer der Art, sonst Kalenderjahr) zählt die ersetzte Pflanze nicht als Vorkultur; bei mehrjährigen Kulturen gilt nur das Ausfalljahr.
- [x] **acceptance-5** Nach dem Datum „Substrat erneuert“ gibt es keine Bodenwarnung.
- [x] **acceptance-6** Fruchtfolgeprüfung und Pflanzdialog zeigen dasselbe Ergebnis; Fruchtfolge-Warnungen aus Vorjahren bleiben unverändert.
- [x] **acceptance-7** Der Hinweis nach einem Ausfall folgt der Ursachenklasse: Blattschädling keiner, Blattkrankheit „Reste entfernen, nicht kompostieren“, unbestätigte bodenbürtige Ursache eine überstimmbare Warnung.

## Test hooks

- **acceptance-1** — `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestNoEvidencedPause::test_a_tenants_own_species_without_a_genus_still_hits_a_genus_host` and the engine's `TestTheFinestHostLevel` (genus from the scientific name, only an evidenced non-host lifts a host - review 2026-11-28, falsified); `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestAHostOfTheBedsSoilHazard` (warning with `hazard_until` inside the pause, hint after it, nothing after the survival, `rotation_exempt` and switched-off beds still warn, planter/tent/shelf/container and hydroponics never, no table no finding), `src/backend/tests/unit/domain/engines/test_soil_hazard_planting_engine.py::TestAHostInsideAndAfterThePause` / `TestTheFinestHostLevel`, vitest `src/frontend/src/features/gardenPlanner/planting/PlantingDialog.soilHazards.test.tsx` ("warns inside the pause …", "shows the hazard on a bed whose rotation check is off …") — falsified 2026-11-27 (rotation gate, vessels, pause stage, end after the survival)
- **acceptance-2** — `src/backend/tests/unit/domain/engines/test_soil_hazard_planting_engine.py::TestNoEvidencedPause` (white rot, juglone without an end, clubroot survival-only by a data change), `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestNoEvidencedPause`, vitest "warns without a time statement" — falsified 2026-11-27
- **acceptance-3** — `src/backend/tests/unit/domain/engines/test_soil_hazard_planting_engine.py::TestSoftHazardsAndUncertainHosts`, `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestSoftHazards` (`root_knot_nematode`/`sclerotinia` → `soil_hazard.soft` INFO; host below 3/3 → `soil_hazard.uncertain_host`, operator decision P4), vitest "gives a hint for a soft hazard …" — falsified 2026-11-27
- **acceptance-4** — `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestTheCultivationWindow` (autumn garlic replaced in March; no cultivar = calendar year; replant after the window counts; a perennial that stood past its window leaves out only the year of its loss; the timeline unchanged) — falsified 2026-11-27 (whole-plant skip, window end, perennial rule)
- **acceptance-5** — `src/backend/tests/unit/domain/engines/test_soil_hazard_planting_engine.py::TestFreshSubstrate`, `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestFreshSubstrate` (also the residual soil-borne warning, a future day refused), `src/backend/tests/api/test_replant_soil_hazards_api.py::TestFreshSubstrateOnTheWire` (PATCH round trip, 422 for a day after today), vitest `src/frontend/src/features/gardenPlanner/bed/SoilProfileForm.test.tsx` / `soilForm.test.ts` — falsified 2026-11-27
- **acceptance-6** — browser: `tests/e2e/test_req053_wave10_domain.py::test_tc_053_111_soil_hazard_in_the_dialog_is_the_planting_checks_answer` (TC-053-111 part 2, TC-REQ-053 v1.28: clubroot bed, broccoli; every hint line's code/strength/stage in order and the block's strength equal the `validate-planting` answer; year, host family and "Trotzdem pflanzen" shown) - collected and self-tested locally, **the browser run itself is pending the E2E stack (CI nightly)**; `src/backend/tests/api/test_replant_soil_hazards_api.py::TestOneSourceForTheDialogAndTheCheck` (the wire answer equals the validator finding for finding, also with the rotation off), `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestTheRotationAroundIt` (previous-year finding unchanged next to a hazard), vitest "one source of truth" (the dialog follows the server's strength, one request per species; `data-code`/`data-severity`/`data-hazard-stage` on each line); production wiring `src/backend/tests/unit/common/test_bed_rotation_validator_wiring.py` - falsified 2026-11-27/28 (router filter, factory without `soil_hazards=`, line attributes)
- **acceptance-7** — `src/backend/tests/unit/domain/engines/test_crop_rotation_validator_soil_hazards.py::TestTheResidualHintFollowsTheCauseClass` (abiotic/mechanical/pest_foliar none, disease_foliar INFO, unconfirmed soil-borne WARNING, unknown INFO, confirmed pathogen on the bed speaks through its hazard, not taken over keeps the warning, legacy without class unchanged), vitest "the residual hint follows the cause class"; the history row carries the class: `src/backend/tests/integration/test_rotation_history.py::TestPlantings::test_a_row_carries_the_cause_class_and_the_cultivar_of_a_loss` (needs ArangoDB, runs in CI) — falsified 2026-11-27

## Consistency notes

**Validator and dialog prior art (proceed).** Established:
`validate_planting_in_location` (`crop_rotation_validator.py:639-709`)
produces the findings that `HintsPanel.tsx:99-117` renders, and
`PlantingDialog.tsx:203,411-434` already offers "plant anyway" with a reason.
Acceptance-6 holds as long as hazard findings originate in the validator.

**Rotation gate (decision).** Established: `not_applicable_reason`
(`crop_rotation_validator.py:180-195,677-681`) returns early for
`rotation_exempt`, disabled rotation and containers. Operator decision
2026-11-17: the hazard check bypasses the rotation gate; containers carry no
hazard (F-20).

**Calendar-year rule (drift, revisit-after F-18).** Established: REQ-053
§11.3 and GP-FR-131 (`:822,1162`) fix the calendar year, implemented at
`crop_rotation_validator.py:587,616`. Changed only after the F-18 spec update;
TC-053-111 stays valid for plants without a window.

**Window end (decision).** Established: `PlantInstance` carries only
`planted_on`/`removed_on` (`plant_instance.py:24-25`). Operator decision
2026-11-17: `planted_on + days_to_maturity` (`species.py:150`), else the
calendar-year rule. Built 2026-11-27: `species.py:150` is `Cultivar.days_to_maturity`
- `Species` has no culture duration - so the window reads the replaced plant's
cultivar (REQ-053 v1.59 §11.3a Nr. 3). "Perennial" is a plant that stood past
its window, not the botanical cycle (garlic is `perennial` in the lifecycle seed).

**Fresh substrate (decision).** Established: `SoilProfile`
(`site.py:263-293`) has no replacement date. Operator decision 2026-11-17: add
`substrate_replaced_on`.

**Class-based hint (decision).** Established: research §5 (`:286-287`) sets
per-class hints while `crop_rotation_validator.py:255` warns on every disease
or pest. Operator decision 2026-11-17: acceptance-7.

**Partial evidence (decision).** Established: clubroot has a 2/3 block
duration and 3/3 survival (`research:303`). Operator decision 2026-11-17:
warning without time statement until the survival end, then nothing
(acceptance-2).

**Operator decisions P1-P7 (2026-11-27).** Applied as decided in
`soil-hazard-knowledge.md`: a lower-bound survival ends the hint (P3), a host
below 3/3 only hints (P4), no evidenced survival keeps the finding open until
the lead removes the hazard (P5); P1, P2, P6, P7 keep the table unchanged.

**Planner contradiction (drift, revisit-after the REQ-054 planner).**
Established: H-10 (`REQ-054:203`) blocks hard; this feature only warns (D-09).
Deliberate; reconciled when the planner is built.

## Risks

- **Single-plant dialog asks for no reason.** The plan tool "Pflanze setzen" (`PlantSlotDialog.tsx:163-164, 309-316`) shows the soil-hazard findings through `HintsPanel` with `overridable={false}`: a `WARNING` is shown, but planting one plant needs no reason and stores none. This is the dialog's existing pattern for every rotation warning (GP-UX-071: a single plant has no "Trotzdem pflanzen" path on the server, which refuses only `CRITICAL` findings); the bed's planting dialog keeps the overridable warning with a reason. Decided not to change in F-21.
- Hosts resolved at genus/species level need `genus`/species keys on the planted species; species without them fall back to family matching.

## Operator questions from the review 2026-11-28 (decided 2026-11-28)

- **S3 — May a grower silence a soil hazard through "Substrat erneuert am"?** Removing a soil hazard is lead-only (F-20), but `soil_profile.substrate_replaced_on` is written with the soil profile (`PATCH /locations/{key}`, role grower). Scenario: clubroot confirmed 2025-07-01 on bed B1; a grower sets "Substrat erneuert am" to today without replacing the soil - every warning for cabbage on B1 disappears, the hazard entry stays and still shows in the bed's Soil tab. Options: keep (it states a fact the grower owns) / lead-only for this field / log the change in the care log or plan audit / show the lifted hazards as "aufgehoben durch Substraterneuerung am …" in the dialog.
  - **Entschieden 2026-11-28 (D-S3):** Gärtner setzen das Feld weiter (Rollen-Gate unverändert); Setzen, Ändern und Löschen des Datums schreibt einen Eintrag ins Plan-Änderungsprotokoll `garden_plan_audit` in derselben Transaktion wie die Änderung (wer, wann, welcher Standort, altes und neues Datum, kein Freitext), nur bei echter Änderung. REQ-053 v1.61 §11.3a Nr. 7, §20.13 SR-011.
- **S4 — Does a long cultivation window hide a perennial standing time?** The window is `planted_on + Cultivar.days_to_maturity`, and `days_to_maturity` allows up to 1095 days. Scenario: asparagus cultivar with `days_to_maturity = 1095`, planted 2024-04-01, died 2026-05-01, replanted 2026-06-01: the replant lies inside the window, so the plant counts as a previous crop in no year - 2024 and 2025 vanish from this check although it stood there for two seasons. Options: keep / cap the window at one season (e.g. 365 days) / treat a window longer than a year as "perennial" (calendar-year rule).
  - **Entschieden 2026-11-28 (D-S4):** Die ersetzte Pflanze wird nur dann ganz ausgelassen, wenn sie höchstens eine Saison stand — Pflanzung im selben oder im vorigen Kalenderjahr des Ausfalls (UTC). Stand sie länger, zählen ihre früheren Jahre als Vorkultur; nur das Ausfalljahr bleibt ausgenommen. Umgesetzt als „im selben oder vorigen Kalenderjahr **und** höchstens 365 Tage“, weil das Beispiel der Entscheidung (1000 Tage, gepflanzt 2024-04, ausgefallen 2025-09 → 2024 zählt) sonst nicht hielte. REQ-053 v1.61 §11.3a Nr. 3.

## References

- Issue #2888, roadmap item R-20; after F-18, F-19 and F-20
- `project/requirements/soil-hazards-replant.md` (R6–R9, R14–R18)
