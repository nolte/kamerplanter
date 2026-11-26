---
id: F-18
title: Wissenstabelle Bodengefahren mit Belegstatus
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
    - kind: drift
      target: spec/req/REQ-054_Automatische-Anbauplanung.md:146
      resolution: proceed
      evidence: "§5.2 fixes soil_hazards[] with affected_families[] and a single soil_persistence_years; AP-ACC-022 (:527), TC-REQ-054.md:472 and H-10 (:203) build on it — all updated (acceptance-1)."
    - kind: drift
      target: spec/req/REQ-003_Phasensteuerung.md:1878
      resolution: proceed
      evidence: "REQ-003 E5 owns the termination_cause enum (no bolting) — added to acceptance-1."
    - kind: prior-art
      target: spec/analysis/agrobiology-soil-hazards-research-2888.md:299
      resolution: proceed
      evidence: "§6.1 is keyed by the eight REQ-054 hazards, §6.2 by pathogen incl. Fusarium f. sp. rows (:322-326); operator decision: key by hazard, no Fusarium hazards for now."
    - kind: prior-art
      target: src/backend/app/migrations/seed_data/ipm.yaml:511
      resolution: proceed
      evidence: "IPM catalogue holds Meloidogyne (:511), Plasmodiophora (:1657), Verticillium dahliae (:1667), Sclerotinia (:1755); Species has family_key and genus (species.py:366-367) for host levels; operator decision: table as seed YAML next to ipm.yaml."
    - kind: prior-art
      target: src/backend/app/config/constants.py:13
      resolution: proceed
      evidence: "MAX_ROTATION_WINDOW_YEARS=8 with the note that longer blocks belong to soil_hazards (REQ-054 H-10) — consistent."
---

## Description

Ob ein Beet nach einem Befall mit Kohlhernie, Weißfäule oder Nematoden wieder
für dieselben Pflanzen taugt, hängt von Fachwerten ab: wie lange der Erreger
im Boden überdauert, wie lange man pausieren sollte und welche Pflanzen er
befällt. Diese Werte sind recherchiert, aber unterschiedlich gut belegt, und
die Specs beschreiben das zugehörige Fachmodell noch nicht.

Diese Änderung zieht zuerst die Specs nach und legt dann eine Wissenstabelle
der acht Bodengefahren an — mit Anbaupause, maximaler Überdauerung und
Wirtspflanzen auf Familien-, Gattungs- oder Artebene, jeder Wert mit seinem
Belegstatus. Nur dreifach belegte Werte dürfen später eine Zeitangabe in
einer Warnung tragen. Nachrecherchierte Werte (#3005) werden als Daten
ergänzt, ohne dass sich Code ändert.

## Acceptance criteria

- [x] **acceptance-1** Vor jeder Codeänderung beschreiben REQ-053 §11.3/§16, REQ-054 §5.2/§6 H-10 samt AP-ACC-022, TC-REQ-054 und REQ-003 E5 die Ursachenklasse, `bolting`, die Saison als Anbaufenster, die zwei Zeitfelder, die weichen Gefahren und die Wirtsebenen.
- [x] **acceptance-2** Die Wissenstabelle hält je Bodengefahr Anbaupause, maximale Überdauerung und Wirte (Familie, Gattung oder Art), jeden Wert mit Belegstatus.
- [x] **acceptance-3** Die Startwerte aus der Recherche sind mit ihrem Status geladen; nur 3/3-belegte Werte gelten als nutzbar für Zeitangaben.
- [x] **acceptance-4** Ein nachrecherchierter Wert wird allein durch eine Datenänderung wirksam.

## Test hooks

- **acceptance-1** — spec diff review (REQ-003, REQ-053, REQ-054, TC-REQ-054) before the first code commit — commit `docs(spec): specify the soil-hazard knowledge table before code` precedes the first code commit; REQ-003 E5 v2.23, REQ-053 §11.3/§11.3a/§16 (GP-FR-131/137/193) v1.55, REQ-054 §3/§5.2/§5.2a/§5.5/§6 H-10/H-11/§7.2/AP-API-012/AP-ACC-022/028 v1.4, TC-REQ-054 v1.3 (TC-054-013, TC-054-029); `tests/unit/guards/test_spec_literal_discriminators_match_models.py` green — proven 2026-11-27
- **acceptance-2** — schema validation of the seed YAML (`seed YAML matches the schema` hook) — `seed-schema-conformance` hook over `src/backend/app/migrations/seed_data/soil_hazards.yaml`; `tests/unit/migrations/test_soil_hazards_seed.py` (schema refuses a value without evidence, a 3/3 claim with two sources, a host without level, `affected_families`; host taxa known to the seed catalogue at all three levels) — proven 2026-11-27
- **acceptance-3** — unit test: loader exposes durations only for 3/3 values — `tests/unit/data_access/knowledge/test_soil_hazard_knowledge_source.py::TestShippedStartValues` (start values and status per hazard, usable durations only for `evidenced`); invariants in `tests/unit/domain/models/test_soil_hazard_knowledge.py` — proven 2026-11-27
- **acceptance-4** — unit test: changing a value's status in the fixture changes the resolved duration without code change — `tests/unit/data_access/knowledge/test_soil_hazard_knowledge_source.py::TestDataChangeAlone` (status raised → usable, lowered → withdrawn, new value takes effect, a 3/3 claim without three sources is refused) — proven 2026-11-27

## Consistency notes

**REQ-054 data model (drift, proceed).** Established:
`REQ-054_Automatische-Anbauplanung.md:146` fixes `soil_hazards[]` with
`affected_families[]` and a single `soil_persistence_years`; AP-ACC-022
(`:527`), `TC-REQ-054.md:472` and H-10 (`:203`) build on it. They are updated
in acceptance-1.

**termination_cause owner (drift, proceed).** Established: REQ-003 E5
(`REQ-003_Phasensteuerung.md:1878`) owns the enum without `bolting`; added to
acceptance-1.

**Keying (decision).** Established: research §6.1 is keyed by the eight
REQ-054 hazards, §6.2 by pathogen with *Fusarium* rows
(`agrobiology-soil-hazards-research-2888.md:299-329`). Operator decision
2026-11-17: key by hazard; *Fusarium* formae speciales are not hazards for now
(mostly 1/3).

**Storage (decision).** Established: the IPM seed (`ipm.yaml:511,1657,1667,1755`)
holds four of the pathogens; `Species` carries `family_key` and `genus`
(`species.py:366-367`) for the host levels. Operator decision 2026-11-17: the
table lives as seed YAML next to `ipm.yaml`.

**Rotation window constant (prior-art, proceed).** Established:
`constants.py:13-15` already says longer blocks belong to `soil_hazards`.

## Risks

- Most block durations are below 3/3 today; until #3005 delivers, most warnings carry no time statement.

## References

- Issue #2888, roadmap item R-20, research follow-up #3005
- `project/requirements/soil-hazards-replant.md` (R5, R11, R12, R20)
- `spec/analysis/agrobiology-soil-hazards-research-2888.md`
