---
id: F-19
title: Ursachenklasse am Ausfall
status: ready
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
      target: src/backend/app/common/enums.py:326
      resolution: proceed
      evidence: "TerminationCause (9 values, no bolting, :326-338); phase_transition_engine.py:253-291 sets the cause only on died; TerminationDialog.tsx:23,68-74 requires a cause on died."
    - kind: drift
      target: src/backend/app/domain/engines/crop_rotation_validator.py:60
      resolution: proceed
      evidence: "ABIOTIC_TERMINATION_CAUSES (:60-69) lacks bolting; an unknown value falls into the INFO branch (:262-265) — bolting is added (acceptance-3)."
    - kind: prior-art
      target: src/backend/app/domain/models/phase.py:138
      resolution: proceed
      evidence: "REQ-003 E6 models premature bolting as vegetative→bolting with is_premature (phase_transition_engine.py:115); operator decision: pre-fill bolting from it."
    - kind: drift
      target: src/frontend/src/features/gardenPlanner/bed/BedClearDialog.tsx:35
      resolution: proceed
      evidence: "Clearing a bed ends all plants with one termination_type (also died) without cause (:88); operator decision: stays unclassified."
    - kind: prior-art
      target: src/backend/app/domain/models/survival_stats.py:25
      resolution: proceed
      evidence: "TerminationCauseCount / SurvivalStatsPanel.tsx count by cause — bolting labels covered by acceptance-6."
---

## Description

Wer heute eine eingegangene Pflanze erfasst, wählt eine grobe Ursache wie
„Krankheit“ oder „Schädling“. Ob der Erreger im Boden sitzt und das Beet
gefährdet oder nur die Blätter befiel, bleibt offen; Schossen lässt sich gar
nicht als Ursache angeben.

Nach dieser Änderung fragt der Ausfall-Dialog nach, wo die Ursache saß.
Abiotische Ursachen wie Frost oder Trockenheit sind vorbelegt; bei Krankheit
oder Schädling wählt der Gärtner zwischen Blatt und Boden. Bei Hitze,
Trockenheit, Staunässe und bei unbekannter Ursache an welkeanfälligen
Familien fragt die App, ob die Pflanze trotz feuchter Erde welkte oder die
Wurzeln braun waren. Bei einem bodenbürtigen Ausfall kann er den Erreger
benennen und festhalten, ob und von wem er bestätigt wurde. „Schossen“ ist
eine neue Ursache und wird vorgeschlagen, wenn die Pflanze vorzeitig in die
Schoss-Phase ging.

## Acceptance criteria

- [ ] **acceptance-1** Beim Erfassen einer eingegangenen Pflanze wird die Ursachenklasse abgeleitet oder abgefragt: abiotische Ursachen vorbelegt, bei Krankheit oder Schädling Pflichtauswahl Blatt/Boden.
- [ ] **acceptance-2** Bei Hitze, Trockenheit, Staunässe und bei „unbekannt“ an welkeanfälligen Familien erscheint die Welke-Rückfrage, die zu „bodenbürtige Krankheit“ führen kann.
- [ ] **acceptance-3** Es gibt die Ursache „Schossen“; sie gilt als abiotisch, löst beim Nachpflanzen keinen Hinweis aus und ist vorbelegt, wenn die Pflanze vorzeitig in die Schoss-Phase ging.
- [ ] **acceptance-4** Bei einem bodenbürtigen Ausfall kann der Gärtner einen Erreger aus der Liste der Bodengefahren wählen und festhalten, ob und von wem er bestätigt wurde.
- [ ] **acceptance-5** Pflanzen ohne Ursachenklasse — Altdaten und über „Beet räumen“ beendete — verhalten sich wie bisher.
- [ ] **acceptance-6** Alle neuen Beschriftungen gibt es in DE und EN, auch in der Überlebensstatistik.

## Test hooks

- **acceptance-1** — backend unit test of the pre-fill table (research §5) + vitest on `TerminationDialog` — pending
- **acceptance-2** — vitest: wilt follow-up shown for the listed causes/families — pending
- **acceptance-3** — unit test: `bolting` in `ABIOTIC_TERMINATION_CAUSES`, no replant hint; pre-fill from `is_premature` bolting phase — pending
- **acceptance-4** — service test: pathogen limited to the hazard list; `confirmed`/`source` persisted — pending
- **acceptance-5** — regression: TC-053-111 unchanged for plants without class; `BedClearDialog` path unchanged — pending
- **acceptance-6** — i18n completeness check — pending

## Consistency notes

**Termination prior art (proceed).** Established: `TerminationCause`
(`enums.py:326-338`), the cause set only on `died`
(`phase_transition_engine.py:253-291`) and the mandatory cause in
`TerminationDialog.tsx:23,68-74` are where the class attaches.

**bolting in the abiotic set (drift, proceed).** Established:
`ABIOTIC_TERMINATION_CAUSES` (`crop_rotation_validator.py:60-69`) lacks
`bolting`; an unknown value falls into the INFO branch (`:262-265`) and would
raise a wrong hint. Covered by acceptance-3.

**Premature bolting phase (decision).** Established: REQ-003 E6 models it
(`phase.py:138`, `phase_transition_engine.py:115`). Operator decision
2026-11-17: pre-fill `bolting` from it.

**Bulk clear (decision).** Established: `BedClearDialog.tsx:35,88` ends all
plants with one type and no cause. Operator decision 2026-11-17: stays
unclassified (acceptance-5).

**Pathogen capture ownership (decision).** Operator decision 2026-11-17:
pathogen, `confirmed` and `source` are captured here (acceptance-4); the
promotion into the bed is F-20.

**Statistics (prior-art, proceed).** Established: `survival_stats.py:25` and
`SurvivalStatsPanel.tsx` count by cause; the new labels are covered by
acceptance-6.

## Risks

- A mandatory foliar/soil choice adds a click to every disease/pest loss; users unsure of the location pick "unknown" via the soil follow-up.

## References

- Issue #2888, roadmap item R-20; after F-18 (spec first)
- `project/requirements/soil-hazards-replant.md` (R1, R2, R13)
