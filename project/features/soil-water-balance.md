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
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: project/features/soil-water-balance.md:80
      resolution: revisit-after agrarbiologisches Review + Betreiberbestätigung (Zufluss durch Gießen)
      evidence: "'Nur gemessene Niederschlagsmengen gehen in die Bilanz ein' - kein Kriterium nennt das Gießen als Zufluss; ohne ihn wächst das Defizit trotz Gießen unbegrenzt."
    - kind: drift
      target: src/backend/app/tasks/irrigation_tasks.py:63
      resolution: revisit-after agrarbiologisches Review (Regenexposition je Standorttyp)
      evidence: "find_site_docs_by_types(WEATHER_RELEVANT_SITE_TYPES) rechnet Gewächshaus und Balkon mit und zieht dort Niederschlag ab (:146); gemessener Regen füllt den Speicher unter Glas oder Dach nicht."
    - kind: drift
      target: src/backend/app/tasks/irrigation_tasks.py:156
      resolution: revisit-after Edit (Kriterium zur Vorausrechnung)
      evidence: "demand_date=today - es entsteht nur der heutige Datensatz; REQ-037 §3.3 (:352) sieht horizon_days=3 vor. F-30 ('erster Tag mit Bedarf') und F-31 ('die nächsten Tage') brauchen Folgetage, F-29 fordert sie nicht."
    - kind: drift
      target: src/backend/app/domain/models/site.py:645
      resolution: revisit-after agrarbiologisches Review (Ausschluss erdloser Kultur)
      evidence: "Location.irrigation_system kennt hydro/nft/ebb_flow/mist (enums.py:498-504), SubstrateType kennt hydro_solution/none/clay_pebbles/rockwool (:507-521); der Task schließt nichts davon aus."
    - kind: prior-art
      target: src/backend/app/domain/models/substrate.py:92
      resolution: proceed
      evidence: "water_holding_capacity_percent, water_retention (:39), air_porosity_percent (:51), bulk_density_g_per_l (:96), volume_liters (:146); SoilProfile.substrate_key (site.py:281), Location.height_m (:662) und area_m2 - die Bausteine der Stufe 'Substrat x Volumen'."
    - kind: prior-art
      target: src/backend/app/domain/services/watering_service.py:479
      resolution: proceed
      evidence: "Die Bodenfeuchte-Sensor-Übersteuerung wirkt nach der ET-Übersteuerung auf dieselbe Gießmenge - eine zweite, gemessene Feuchtequelle neben dem gerechneten Speicher."
    - kind: prior-art
      target: src/backend/app/domain/models/site.py:277
      resolution: proceed
      evidence: "SoilProfile hat drainage, site_water_regime, conditions[waterlogged/compacted] (enums.py:2329-2355), stone_content_class (:292); soil_hazards (F-20, :709) sind Schaderreger-Einträge ohne Wasserhaushalt-Bezug - keine Überschneidung."
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

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`; same run, triggers and caveats as recorded in `site-rain-sensor.md` (no test run; resolutions are proposals; line references into this file are those of `cc8531492`). The frontmatter holds the seven findings of this run; the ten findings of 2026-11-17 (`feature-consistency-reviewer@5d01b6c4`) are listed with their fate. The report's verdict: **blocked** on the agrobiology review plus operator confirmation, see the German section below.

**Findings of 2026-11-17 — fate.**

1. `REQ-037:465` (drift, proceed) — moved: §7 `:466`, §3.1 `:218` (formula `:297-312`), §3.3 `:336-387`. `irrigation_tasks.py:1` still carries "REQ-037 §7". Still true.
2. `REQ-037:483` (drift, proceed) — moved to `:483-486` (scenario 4). Still true.
3. `REQ-037:362`, `REQ-053:1012` (drift, proceed) — moved to `REQ-037:363` and `REQ-053:1036`. Still true.
4. `REQ-053:2372` (drift, proceed) — moved to `:2398` (located by match only, not read in full).
5. `project/requirements/measured-rain-soil-water-balance.md:51` (drift, proceed) — still true.
6. `irrigation_zone_service.py:451`, `watering_service.py:468-475` (drift, proceed) — still true (`:451-454`; `:468-477`).
7. Calculator `:238`, `irrigation_tasks.py:146` (prior-art, proceed) — calculator unchanged (`:238`, cap `:270-271`, rule of thumb `:38-41`); the task moved to `:147`. The description of this file names `:145`; the calculation is now at `:143-149`.
8. `site.py:290` (prior-art, proceed) — still true (`:290-291`).
9. `irrigation_demand.py:26` (prior-art, proceed) — still true.
10. Overlap F-13, `irrigation_tasks.py:150-170` (proceed) — moved to `:151-171`. Still true; REQ-037 v1.3 (`:20`, `:387`) now names up to five runs per day.

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
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
```

**New findings.**

- **Watering as inflow (drift, this file `:80`).** "Nur gemessene Niederschlagsmengen gehen in die Bilanz ein" — no criterion names watering as an inflow; without it the deficit grows without bound despite watering. acceptance-6 is worded against quantity-less `rainfall` events and, read literally, excludes watering. Available would be `watering_logs` (`volume_liters`) and `care_events` with a quantity; many confirmations carry none. The review has to fix what a confirmation without a quantity does.
- **Rain exposure per site type (drift, `irrigation_tasks.py:63`).** `find_site_docs_by_types(WEATHER_RELEVANT_SITE_TYPES)` includes greenhouse and balcony and subtracts precipitation there (`:146`); measured rain does not fill the store under glass or a roof. The error exists today for the forecast; with measured rain and deferral (F-30) it takes effect: a tomato in the greenhouse would no longer be reminded because of rain. `Location.frost_exposed` (`:654`) is a pattern for a per-location override; there is no rain counterpart.
- **Look-ahead over the forecast horizon (drift, `irrigation_tasks.py:156`).** `demand_date=today` — only today's record is written; REQ-037 §3.3 (`:352`) foresees `horizon_days=3`. F-30 ("first day with demand") and F-31 ("the next days") need following days, F-29 does not require them. A criterion is missing.
- **Soilless culture is not excluded (drift, `site.py:645`).** `Location.irrigation_system` knows hydro/nft/ebb_flow/mist (`enums.py:498-504`), `SubstrateType` knows hydro_solution/none/clay_pebbles/rockwool (`:507-521`); the task excludes none of them.
- **Building blocks of the tier "substrate × volume" (prior-art, proceed, `substrate.py:92`).** `water_holding_capacity_percent`, `water_retention` (`:39`), `air_porosity_percent` (`:51`), `bulk_density_g_per_l` (`:96`), `volume_liters` (`:146`); `SoilProfile.substrate_key` (`site.py:281`), `Location.height_m` (`:662`) and `area_m2`.
- **Second, measured moisture source (prior-art, proceed, `watering_service.py:479`).** The soil-moisture sensor override acts after the ET override on the same watering volume — a measured source beside the computed store.
- **No overlap with soil hazards (prior-art, proceed, `site.py:277`).** `SoilProfile` has `drainage`, `site_water_regime`, `conditions[waterlogged/compacted]` (`enums.py:2329-2355`), `stone_content_class` (`:292`); `soil_hazards` (F-20, `:709`) are pathogen entries without a water-balance relation.

**Further discussion.**

- **Tier "evidenced soil type".** It yields nothing today (R-008, E-10) and is testable only as "yields no value". In practice substrate × volume and the site default remain.
- **Testability.** acceptance-7 "nachvollziehbar" is not a checkable result; name expected values for zone status and ET watering volume. acceptance-1 is a process gate and should contain the operator confirmation (decision of 2026-11-27: the agent reviews, the operator confirms; the criterion names only the agent).
- The 6-hour freshness is fixed (2026-11-27) and not part of the review.

**Cross-feature.** F-28 → F-29 (reading and provenance per day); F-30 and F-31 depend on F-29 (demand threshold, look-ahead, store level, following days). The order, the common gaps, the stale line references, the spec follow-up outside any criterion and the comparison with issue #3002 are in `site-rain-sensor.md`. The issue's point "agrobiology review of the effective-precipitation rule for measured values" is parameter 5 of the list below.

**Edits required before `ready`** (the report's verdict for F-29, translated): blocked on the agrobiology review of the 15 parameters by the agent and the operator's confirmation; watering as inflow, rain exposure of greenhouse/balcony, the demand threshold and the exclusion of soilless culture must be settled. After it:

1. Add the section "Betreiberentscheidungen 2026-11-27" (done in this change).
2. Add a criterion on the look-ahead.
3. Sharpen acceptance-6 and acceptance-7.
4. Update the line references.

## Risks

- Until R-008 sources soil-texture values, beds without substrate/volume work only with a lead-set default.

## References

- Issue #3002, roadmap item R-27, REQ-037 §3.1/§3.3/§7, REQ-053 GP-FR-113
- `project/requirements/measured-rain-soil-water-balance.md` (R3, R4, R5, R9)

## Betreiberentscheidungen 2026-11-27

- Das agrarbiologische Review macht ein Agent; der Betreiber bestätigt die Parameter.
- Die Datenfrische von 6 Stunden ist fest.
- ADR-008 ist keine Vorbedingung.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

F-29 ist auf das agrarbiologische Review der folgenden 15 Parameter und die Bestätigung des Betreibers blockiert. Die 6-h-Frische gehört nicht dazu (fest).

**Zuerst zu klären (vier Punkte):**

- **Gießen als Zufluss (Parameter 7).** Heute sagt acceptance-6 „nur gemessene Niederschlagsmengen gehen in die Bilanz ein“; kein Kriterium nennt das Gießen. Mengen lägen in `watering_logs` (`volume_liters`) und `care_events`; viele Bestätigungen tragen keine.
  - **Gießen füllt den Speicher:** Das Defizit sinkt nach dem Gießen; festzulegen ist, was eine Bestätigung ohne Menge bewirkt.
  - **Gießen zählt nicht:** Das Defizit wächst trotz Gießen unbegrenzt.
- **Regenexposition von Gewächshaus und Balkon (Parameter 9).** Heute rechnet der Task Gewächshaus und Balkon mit und zieht dort Niederschlag ab (`irrigation_tasks.py:63`, `:146`); ein Regen-Pendant zu `Location.frost_exposed` (`site.py:654`) gibt es nicht.
  - **Regen zählt dort nicht (je Standorttyp oder je Ort überschreibbar):** Gemessener Regen füllt den Speicher unter Glas und Dach nicht; die Tomate im Gewächshaus wird weiter erinnert.
  - **So lassen:** Mit F-30 verschiebt gemessener Regen auch Erinnerungen für Pflanzen, die keinen Regen abbekommen.
- **Bedarfsschwelle (Parameter 4).** Ab welcher Entleerung gilt „Bedarf“ — heute gibt es keinen Speicher, nur die Tagesbilanz (`evapotranspiration_calculator.py:238`).
  - **Jedes Defizit ist Bedarf:** F-30 holt eine verschobene Erinnerung am ersten Tag mit Defizit zurück.
  - **Erst ab einem Anteil der Kapazität:** Die Erinnerung bleibt länger verschoben; der Anteil ist festzulegen.
- **Ausschluss erdloser Kultur (Parameter 10).** Heute schließt der Task weder `irrigation_system` hydro/nft/ebb_flow/mist (`enums.py:498-504`) noch die Substrattypen hydro_solution/none/clay_pebbles/rockwool (`:507-521`) aus (`site.py:645`).
  - **Ausschließen:** Für diese Standorte entsteht keine Bodenwasser-Bilanz.
  - **Mitrechnen:** Die Bilanz rechnet einen Bodenspeicher, den es dort nicht gibt.

**Alle 15 Parameter des Reviews:**

1. Wurzelraumtiefe je Kultur/Phase für die Umrechnung von Volumenanteil in mm.
2. Bedeutung von `water_holding_capacity_percent` (Gesamtkapazität oder pflanzenverfügbar) und die Umrechnung über Volumen und Fläche in mm.
3. Pflanzenverfügbares Wasser je `soil_texture` (R-008; bis dahin null).
4. Bedarfsschwelle: ab welcher Entleerung „Bedarf“ gilt (jedes Defizit oder erst ab einem Anteil). Sie bestimmt F-30s „ersten Tag mit Bedarf“.
5. Effektiver Niederschlag im Speichermodell: Bleibt die 5-mm/80-%-Regel (`evapotranspiration_calculator.py:38-41`) neben dem Überlauf bestehen? Gefahr des doppelten Abzugs.
6. Anfangsfüllstand (erster Tag, neuer Run, Datenlücke) und Verhalten nach Lücken.
7. Zufluss durch Gießen, mit und ohne Menge.
8. Untergrenze und Deckel der Empfehlung (Defizit höchstens Kapazität; ersetzt Szenario 4).
9. Regenexposition je Standorttyp/Ort (Gewächshaus, Balkon, Zelt).
10. Ausschluss erdloser Systeme und Substrate.
11. Einfluss von Drainage, Wasserregime, Staunässe, Steingehalt, Mulch — berücksichtigen oder ausdrücklich nicht.
12. Standardwert des Standorts: Einheit, zulässiger Bereich, ein Wert für alle Beete; Hilfetext ohne eingebaute Werte (E-10).
13. Rückfall „Faustregel + gemessener 24-h-Regen“: Die 24 h überlappen Vortag und heute; Doppelzählung mit der Tagesprognose.
14. Prognosehorizont der Vorausrechnung und wie vorhergesagter Regen künftige Tage füllt.
15. Schwelle „starke Abweichung“ zwischen Messung und Prognose (F-31 acceptance-4).
