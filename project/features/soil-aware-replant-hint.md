---
id: F-21
title: Bodengefahren im Nachpflanz-Hinweis
status: draft
roadmap_item: R-20
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
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

- [ ] **acceptance-1** Ist die gewählte Pflanze Wirt einer Bodengefahr des Beets, zeigt der Pflanzdialog innerhalb der belegten Anbaupause eine überstimmbare Warnung mit Zeitangabe, danach bis zur maximalen Überdauerung einen Hinweis; Pflanzen wird nie verhindert — auch nicht auf Beeten mit ausgeschalteter Fruchtfolge.
- [ ] **acceptance-2** Ist keine Anbaupause belegt, warnt der Dialog ohne Zeitangabe — bis zum Ende der belegten Überdauerung, falls diese belegt ist, sonst unbefristet.
- [ ] **acceptance-3** Wurzelgallenälchen und Sklerotinia ergeben nur einen Hinweis.
- [ ] **acceptance-4** Eine Nachpflanzung innerhalb des Anbaufensters der ersetzten Pflanze (Pflanzdatum + Kulturdauer der Art, sonst Kalenderjahr) zählt die ersetzte Pflanze nicht als Vorkultur; bei mehrjährigen Kulturen gilt nur das Ausfalljahr.
- [ ] **acceptance-5** Nach dem Datum „Substrat erneuert“ gibt es keine Bodenwarnung.
- [ ] **acceptance-6** Fruchtfolgeprüfung und Pflanzdialog zeigen dasselbe Ergebnis; Fruchtfolge-Warnungen aus Vorjahren bleiben unverändert.
- [ ] **acceptance-7** Der Hinweis nach einem Ausfall folgt der Ursachenklasse: Blattschädling keiner, Blattkrankheit „Reste entfernen, nicht kompostieren“, unbestätigte bodenbürtige Ursache eine überstimmbare Warnung.

## Test hooks

- **acceptance-1** — unit tests of `validate_planting_in_location` with a hazard inside/after the block, on a `rotation_exempt` bed — pending
- **acceptance-2** — unit test: hazard without evidenced duration (and clubroot: survival only) — pending
- **acceptance-3** — unit test: `root_knot_nematode`/`sclerotinia` → INFO — pending
- **acceptance-4** — unit tests: autumn garlic replaced in March; missing `days_to_maturity`; perennial — pending
- **acceptance-5** — unit test with `substrate_replaced_on` before the planting — pending
- **acceptance-6** — E2E TC-053-111 extended (dialog vs. validator) + previous-year regression — pending
- **acceptance-7** — unit tests per cause class — pending

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
calendar-year rule.

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

**Planner contradiction (drift, revisit-after the REQ-054 planner).**
Established: H-10 (`REQ-054:203`) blocks hard; this feature only warns (D-09).
Deliberate; reconciled when the planner is built.

## Risks

- Hosts resolved at genus/species level need `genus`/species keys on the planted species; species without them fall back to family matching.

## References

- Issue #2888, roadmap item R-20; after F-18, F-19 and F-20
- `project/requirements/soil-hazards-replant.md` (R6–R9, R14–R18)
