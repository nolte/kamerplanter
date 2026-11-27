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

- **acceptance-1** — spec diff review (REQ-003, REQ-053, REQ-054, TC-REQ-054) before the first code commit — commit `docs(spec): specify the soil-hazard knowledge table before code` precedes the first code commit; REQ-003 E5 v2.23, REQ-053 §11.3/§11.3a/§16 (GP-FR-131/137/193) v1.55, REQ-054 §3/§5.2/§5.2a/§5.5/§6 H-10/H-11/§7.2/AP-API-012/AP-ACC-022/028 v1.4, TC-REQ-054 v1.3 (TC-054-013, TC-054-029); `tests/unit/guards/test_spec_literal_discriminators_match_models.py` does **not** cover the new `termination_cause` literal (two-line literal, attached to the wrong model heading, `TerminationCause` has no `bolting`) — the enum, i18n and the literal match are F-19's — proven 2026-11-27
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

## Offene Betreiberentscheidungen

Aus den Reviews von F-18 (2026-11-27). Die Daten in `src/backend/app/migrations/seed_data/soil_hazards.yaml` folgen heute der jeweils als „heute“ genannten Antwort; Spec-Stellen, die eine Antwort vorwegnehmen, sind in REQ-054 (H-10, §5.2a, AP-ACC-022, AP-ACC-028), REQ-053 §11.3a und TC-054-029 als vorläufig markiert. F-20/F-21 zitieren diese Punkte. Jede Antwort ist eine reine Datenänderung (F-18 acceptance-4), außer wo „Code“ steht.

- **P1 — Bleibt ein Wert 3/3, wenn drei unabhängige Quellen ihn tragen und eine vierte widerspricht?** Betroffen: `sclerotinia` Pause 5 (Review PMC8417578: 2–3 bzw. 1–4 J.), `verticillium` Überdauerung 10 (LfL 2017: „nicht sehr lange“).
  - „ja“ (heute): beide bleiben `evidenced`; Sklerotinia-Hinweis mit Pause 5 J., Verticillium-Warnung mit 4 J., Restrisiko bis 10 J.
  - „nein“: beide werden `contradictory`, keine Dauer; Sklerotinia-Hinweis ohne Zeitangabe und (nach P5) unbefristet, Verticillium-Warnung mit 4 J., danach Hinweis (nach P5) unbefristet.
- **P2 — Gilt die Kohlhernie-Lesart überall: Nennen alle Quellen unterschiedliche Maxima, ist das kleinste gemeinsame Minimum `lower_bound` 3/3?**
  - „ja, überall“: `cyst_nematode` Überdauerung 5 `evidenced`/`lower_bound` (5–6, bis 10, > 12 J.); `sclerotinia` Überdauerung 4 `evidenced`/`lower_bound` (bis 10, ≥ 5, bis 4 J. — Manitoba „up to four“ müsste als Untergrenze gelesen werden, sonst bleibt es offen); `root_knot_nematode` bleibt leer (nur eine Quelle mit Zahl). Restrisiko-Hinweise enden dann dort (siehe P3).
  - „nein, Einzelfallurteil“ (heute): `clubroot` 15, `white_rot` 15, `pea_root_rot` 10, `verticillium` 10 sind `lower_bound` 3/3; `cyst_nematode` bleibt `contradictory` und leer (Recherche §7.2 „keine belegte Einzelzahl“), `sclerotinia` 10 bleibt 2/3. Die Ungleichbehandlung ist bewusst stehen gelassen, bis entschieden ist.
- **P3 — Darf eine Überdauerungs-Untergrenze den Restrisiko-Hinweis beenden?** Alle nutzbaren Überdauerungen sind `lower_bound` („mindestens“).
  - „ja“ (heute vorläufig, REQ-053 §11.3a Nr. 6 „danach nichts“, AP-ACC-022 „bis 2037“): Hinweis endet bei `confirmed_at + max_survival_years` (Kohlhernie 15, Weißfäule 15, Erbsen-Komplex 10, Verticillium 10 J.).
  - „nein“: Hinweis bleibt nach der Untergrenze unbefristet; `max_survival_years` wird dann nur noch angezeigt („mindestens 15 J.“). Code: die Stufe „danach nichts“ entfällt in F-21.
- **P4 — Zählen Wirte unter 3/3?** Betroffen: `sclerotinia` alle acht Familien (2/3), `verticillium` Solanaceae, Rosaceae, Cucurbitaceae, Asteraceae, *Beta vulgaris* (2/3), `root_knot_nematode` *Allium* (1/3), `juglone` Purdue-Restliste (1/3).
  - „ja, voll“: Sperre/Warnung wie bei 3/3-Wirten — Tomate, Erdbeere, Gurke, Salat auf einem Verticillium-Beet werden gewarnt.
  - „nur Hinweis und `pest_risk`“ (heute vorläufig in AP-ACC-028): keine Warnung, nur Hinweis bzw. Planer-Strafe; Verticillium warnt dann nur Kohl, Minze, Spinat.
  - „gar nicht“: Sklerotinia meldet für keine Pflanze (alle Wirte 2/3), Verticillium nur Kohl, Minze, Spinat; Juglon nur die vier Solanaceae-Arten.
- **P5 — Ist „unbefristet“ der Rückfall, wo keine Überdauerung belegt ist?** Betroffen: `juglone`, `root_knot_nematode`, `sclerotinia`, `cyst_nematode` (nach der Pause).
  - „ja“ (heute vorläufig, REQ-054 §5.2a, H-10, REQ-053 §11.3a): Warnung bzw. Hinweis bleibt, bis jemand die Bodengefahr am Beet entfernt (Leitung, F-20).
  - „nein, Ende nach der Pause“: ohne belegte Überdauerung endet die Meldung mit der Pause; ohne belegte Pause und ohne Überdauerung (Juglon, Wurzelgallenälchen) meldet die Gefahr gar keine Dauer — die Spec braucht dann eine feste Ersatzdauer oder „nur einmal beim Eintragen“. Code: F-21.
- **P6 — Wie ist Manitoba „crop rotation of 5 years between susceptible crops“ zu lesen?** (Sklerotinia-Pause)
  - „Pause 5 J.“ (heute; „between susceptible crops“ = Zeit zwischen zwei Wirten): 5 liegt in allen drei Angaben, `evidenced`/`range`.
  - „Rotation 5 J. = Pause 4 J.“ (strenge Regel N − 1 wie bei AGES): 5 liegt nicht mehr in allen drei Angaben → `insufficient` (2/3) oder Planungswert 4 (AGES 3–5, Manitoba 4, PNW 3–8) als neuer 3/3-Wert.
- **P7 (optional) — Zählen allgemeine Quellen („nearly all temperate vegetables“, „sehr großer Wirtspflanzenkreis“) als Beleg für eine Familienliste?** Heute zählen sie für die acht `root_knot_nematode`-Familien (3/3, zusammen mit der UC-IPM-Kulturtabelle), nicht aber für *Allium* (1/3, nur JKI-Flyer). Die Asymmetrie steht in den Notizen der YAML.
  - „ja“: *Allium* wird 3/3.
  - „nein“: die acht Familien stützt nur noch die UC-IPM-Kulturtabelle (sie nennt Kulturen aller acht, bei Rosaceae nur die Erdbeere) → je Familie 1/3, wie *Allium*; `root_knot_nematode` bleibt `soft`, die Wirkung hängt dann an P4.

## Risks

- Most block durations are below 3/3 today; until #3005 delivers, most warnings carry no time statement.

## References

- Issue #2888, roadmap item R-20, research follow-up #3005
- `project/requirements/soil-hazards-replant.md` (R5, R11, R12, R20)
- `spec/analysis/agrobiology-soil-hazards-research-2888.md`
