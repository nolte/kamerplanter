---
id: F-29
title: Bodenwasser-Bilanz im Gießbedarf
status: draft
roadmap_item: R-27
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@5d01b6c4
  findings:
    - kind: drift
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:465
      resolution: proceed
      evidence: "REQ-037 §7 holds the acceptance criteria; formula and FAO rule live in §3.1 (:296-311) and §3.3 (:335-381) — acceptance-1 now names §3.1/§3.3/§7; the docstring of irrigation_tasks.py:1 carries the same wrong reference and is fixed with it."
    - kind: drift
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:483
      resolution: proceed
      evidence: "The existing AC 'net_demand 9, water_holding_capacity 6 → capped 6' pins a per-application cap; acceptance-1 rewrites it together with the bucket."
    - kind: drift
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:362
      resolution: proceed
      evidence: "REQ-037 §3.3 sources capacity from the REQ-019 substrate and REQ-053 GP-FR-113 (:1012) uses usable capacity × volume for planters/raised beds/tents — added as tier 1 of acceptance-4 (operator decision D6)."
    - kind: drift
      target: spec/req/REQ-053_Grafische-Garten-Beetplanung.md:2372
      resolution: proceed
      evidence: "§32.6 item 11 (quantity-less 'rainfall' events do not enter the balance) vs. GP-FR-113 (:1012) — acceptance-6 settles it: only measured quantities enter."
    - kind: drift
      target: project/requirements/measured-rain-soil-water-balance.md:51
      resolution: proceed
      evidence: "A 6-h freshness per day would drop yesterday's final total the next morning; operator decision D2: completed days use the day's last value, the 6-h rule applies to the current day only (agent proposed revisit-after agrobiology review)."
    - kind: drift
      target: src/backend/app/domain/services/irrigation_zone_service.py:451
      resolution: proceed
      evidence: "Zone status (GP-FR-113) and the WateringService ET volume (watering_service.py:468-475) consume net_demand_mm / recommended_volume_liters — acceptance-7 pins their behaviour under the bucket."
    - kind: prior-art
      target: src/backend/app/domain/calculators/evapotranspiration_calculator.py:238
      resolution: proceed
      evidence: "calculate_water_balance already takes water_holding_capacity_mm (cap semantics :270-271) and the rule of thumb (:38-41); irrigation_tasks.py:146 passes None — the seam to replace."
    - kind: prior-art
      target: src/backend/app/domain/models/site.py:290
      resolution: proceed
      evidence: "soil_texture-derived values stay null until R-008 (E-10, REQ-053:2286) — the texture tier yields nothing today; no built-in default capacity (E-10)."
    - kind: prior-art
      target: src/backend/app/domain/models/irrigation_demand.py:26
      resolution: proceed
      evidence: "The record has weather_source but no per-day provenance or capacity tier; irrigation_demands is part of tenant export/erasure — new fields travel with them (acceptance-3/4)."
    - kind: overlap
      target: F-13
      resolution: proceed
      evidence: "F-13 recomputes irrigation after every fetch (up to 4×/day) with an upsert per (site, run, day) (irrigation_tasks.py:150-170) — acceptance-5 requires the bucket to start from yesterday's end state."
---

## Description

Der Gießbedarf ist heute eine Tagesbilanz ohne Gedächtnis: ETc des Tages
minus vorhergesagter Niederschlag, pauschal um eine FAO-Faustregel gekürzt
(`irrigation_tasks.py:145`). Regen von gestern zählt heute nicht mehr.

Nach dieser Änderung führt Kamerplanter je Run eine mehrtägige
Bodenwasser-Bilanz nach FAO-56: Niederschlag füllt den Wurzelraum-Speicher bis
zu seiner Kapazität, der Überschuss geht verloren, ETc zehrt ihn auf. Für den
laufenden Tag gilt ein höchstens 6 Stunden alter Messwert (F-28), für
abgeschlossene Tage der letzte Messwert des Tages, sonst jeweils die Prognose.
Die Speicherfähigkeit kommt bei Kübeln, Hochbeeten und Zelten aus Substrat und
Volumen, bei Beeten aus der belegten Bodenart, sonst aus einem Standardwert des
Standorts; fehlt alles, rechnet Kamerplanter wie heute mit der FAO-Faustregel,
ergänzt um den gemessenen Regen der letzten 24 Stunden. Modell und Parameter
werden vor der Implementierung agrarbiologisch geprüft.

## Acceptance criteria

- [ ] **acceptance-1** Das Bilanzmodell und seine Parameter sind von `agrobiology-requirements-reviewer` geprüft und in REQ-037 §3.1/§3.3 beschrieben, bevor Code entsteht; die Faustregel bleibt dort nur als Rückfall ohne Kapazität, und das Akzeptanzkriterium zur Deckelung (§7, :483) ist neu gefasst.
- [ ] **acceptance-2** Regen über die Speicherkapazität hinaus senkt den Bedarf späterer Tage nicht; Regen darunter senkt ihn, bis ETc ihn aufgezehrt hat.
- [ ] **acceptance-3** Für den laufenden Tag rechnet die Bilanz mit einem Messwert, der höchstens 6 Stunden alt ist, für abgeschlossene Tage mit dem letzten Messwert des Tages, sonst mit der Prognose; der Bedarfsdatensatz trägt die Herkunft je Tag.
- [ ] **acceptance-4** Die Kapazität folgt der Kette Substrat × Volumen (Kübel, Hochbeet, Zelt; REQ-037 §3.3, REQ-053 GP-FR-113) → belegte Bodenart (R-008, E-10) → Standardwert des Standorts → Rückfall auf die Tagesbilanz mit Faustregel und gemessenem 24-h-Regen; der Bedarfsdatensatz nennt die verwendete Stufe. Kamerplanter liefert keinen eingebauten Kapazitätswert.
- [ ] **acceptance-5** Mehrere Neuberechnungen am selben Tag (F-13) starten vom Endstand des Vortags und zehren den Speicher nicht mehrfach auf.
- [ ] **acceptance-6** Nur gemessene Niederschlagsmengen gehen in die Bilanz ein; ein `rainfall`-Pflegeereignis ohne Menge nicht (REQ-053 §32.6 Pkt. 11 und GP-FR-113 sind angeglichen).
- [ ] **acceptance-7** Ein Standort ohne Messwert und ohne Kapazität rechnet wie heute (Regression unverändert); Zonenstatus und ET-Gießmenge folgen dem neuen Bedarf nachvollziehbar.
- [ ] **acceptance-8** Die Leitung kann den Standardwert der Speicherkapazität am Standort setzen und löschen.

## Test hooks

- **acceptance-1** — spec diff of REQ-037 + recorded agrobiology review — pending
- **acceptance-2** — calculator unit tests over a multi-day series (fill, overflow, depletion) — pending
- **acceptance-3** — unit tests: current-day fresh/stale, completed day last value, forecast only; provenance on the record — pending
- **acceptance-4** — unit tests per capacity tier — pending
- **acceptance-5** — unit test: two recomputations on one day give the same result — pending
- **acceptance-6** — unit test: quantity-less rainfall event ignored; spec diff of REQ-053 — pending
- **acceptance-7** — regression test pinning today's single-day result; zone-status and watering-volume tests — pending
- **acceptance-8** — API test (lead only) + vitest on the site form — pending

## Consistency notes

**Wrong section reference (proceed).** Established: REQ-037 §7 is the
acceptance criteria; formula and FAO rule are §3.1 (`:296-311`) and §3.3
(`:335-381`). The requirement artifact (R9) and `irrigation_tasks.py:1` carried
the same misreference.

**Capacity semantics and chain (proceed, D6).** Established: today
`water_holding_capacity_mm` caps a single application (`:270-271`, REQ-037
AC `:483`); the bucket redefines it, so the AC is rewritten in the same change.
REQ-037 §3.3 and REQ-053 GP-FR-113 already source capacity from substrate ×
volume for containers — that tier leads the chain. E-10 forbids a built-in
default; the lead-set site value is allowed.

**Freshness (proceed, D2).** The reviewer showed that a per-day 6-h rule would
drop yesterday's measured total the next morning; the operator decided that
completed days use the day's last value and the 6-h rule applies to the
current day only.

**Overlap with F-13 (proceed).** F-13 recomputes after every fetch; the demand
is upserted per (site, run, day). The bucket must be a function of yesterday's
end state plus today's inputs, so repeated runs are idempotent (acceptance-5).

**Downstream consumers (proceed).** Zone status (`irrigation_zone_service.py:451`)
and the ET watering volume (`watering_service.py:468-475`) read the demand;
acceptance-7 pins them.

## Risks

- Until R-008 sources soil-texture values, beds without substrate/volume work only with a lead-set default.

## References

- Issue #3002, roadmap item R-27, REQ-037 §3.1/§3.3/§7, REQ-053 GP-FR-113
- `project/requirements/measured-rain-soil-water-balance.md` (R3, R4, R5, R9)
