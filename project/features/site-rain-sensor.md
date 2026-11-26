---
id: F-28
title: Gemessener Regen neben der Prognose
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
    - kind: duplication
      target: src/backend/app/data_access/external/home_assistant_weather_adapter.py:127
      resolution: proceed
      evidence: "REQ-046 mode B already binds HaSensorMapping.precipitation_entity per site and writes data_kind='observed' (:147-162); operator decision D1 2026-11-17: extend this binding instead of a second one (agent proposed revisit-after operator decision)."
    - kind: drift
      target: src/backend/app/tasks/irrigation_tasks.py:174
      resolution: proceed
      evidence: "_pick_forecast returns exact[0] when an observed and a forecast record share the day — acceptance-3 makes the choice explicit."
    - kind: drift
      target: src/backend/app/api/v1/tenant_scoped/weather/tenant_router.py:148
      resolution: proceed
      evidence: "The per-site weather source is LEAD-only (REQ-049 §2.10, #2181); D1 keeps it — the 'technical' scope only for entity listings (REQ-005:1842), not a second gate."
    - kind: drift
      target: spec/req/REQ-005_Hybrid-Sensorik.md:1846
      resolution: proceed
      evidence: "Light mode grants the entity on bind instead of 422 — acceptance-2 states both cases."
    - kind: drift
      target: src/backend/app/data_access/external/home_assistant_weather_adapter.py:138
      resolution: proceed
      evidence: "weather_forecasts days are UTC (§12a, #858) while an HA 'rain today' counter resets at local midnight — acceptance-4 fixes the day boundary."
    - kind: prior-art
      target: src/backend/app/data_access/arango/weather_forecast_repository.py:20
      resolution: proceed
      evidence: "upsert_daily is idempotent on (site_key, forecast_date, source) — the same-day overwrite of acceptance-1 reuses it."
    - kind: prior-art
      target: src/backend/app/domain/services/irrigation_zone_service.py:376
      resolution: proceed
      evidence: "GP-FR-114 flow-entity bind (grant check, light-mode admit, device_class check, entity id never logged) is the template; device_class 'precipitation' is checked in acceptance-2."
    - kind: prior-art
      target: src/backend/app/domain/models/garden_plan_import.py:31
      resolution: proceed
      evidence: "HA entity ids are always dropped from plan export/import; acceptance-5 keeps that for the rain entity."
    - kind: overlap
      target: F-13
      resolution: proceed
      evidence: "F-13 moves the fetch to an interval >= 6 h; measured rain arriving via the fetch can be older than 6 h on the current day — see Consistency notes."
---

## Description

Ein Regenmesser (z. B. Netatmo über Home Assistant) lässt sich heute schon als
Wetterquelle eines Standorts binden (REQ-046 Modus B, `precipitation_entity`).
Der Wetter-Resolver nimmt aber pro Lauf nur eine Quelle: Ein HA-Mapping
verdrängt die öffentliche Prognose, und gibt es für einen Tag beide Datensätze,
greift der Gießbedarf zufällig einen davon.

Nach dieser Änderung speichert Kamerplanter den gemessenen Regen **neben** der
Prognose: Die öffentliche Quelle liefert weiter die Vorhersage, die gebundene
HA-Entität den gemessenen Tageswert mit Herkunft. Der Gießbedarf wählt je Tag
eindeutig zwischen gemessen und vorhergesagt. Die Rollen bleiben wie heute: Die
Leitung setzt die Wetterquelle des Standorts, das Auflisten von HA-Entitäten
braucht die Admin-Zuständigkeit `technical`.

## Acceptance criteria

- [ ] **acceptance-1** Ist an einem Outdoor- oder Gewächshaus-Standort eine HA-Niederschlags-Entität gebunden und eine öffentliche Prognosequelle aktiv, liegen für einen Tag beide Datensätze vor (`observed` und `forecast`); ein späterer Messwert desselben Tages ersetzt den früheren.
- [ ] **acceptance-2** Das Binden folgt den bestehenden Regeln: nur Leitung (REQ-049 §2.10), nur freigegebene Entitäten (sonst 422; im Light-Modus wird die Entität beim Binden freigegeben, REQ-005 §4c), nur `device_class: precipitation`; die Entitäts-ID erscheint in keinem Log.
- [ ] **acceptance-3** Für einen Tag mit `observed`- und `forecast`-Datensatz liefert die Auswahl für den Gießbedarf deterministisch den Messwert, sofern er die Frischeregel von F-29 erfüllt, sonst die Prognose.
- [ ] **acceptance-4** Die Tagesgrenze des gemessenen Werts ist festgelegt und dokumentiert (lokaler Tag des Standorts gegenüber UTC-Tagen der Prognose, §12a / #858).
- [ ] **acceptance-5** Ist HA nicht erreichbar oder liefert die Entität keinen Zahlwert, wird kein Messwert geschrieben; die Prognose wird unverändert geholt. Plan- und Mandanten-Export lassen die Entitäts-ID weiterhin weg.
- [ ] **acceptance-6** REQ-046 (Messwert neben Prognose) ist nachgezogen; die Nutzerdoku `weather-services.md` (DE + EN) beschreibt den Regenmesser neben der Prognose.

## Test hooks

- **acceptance-1** — repository/integration test: observed + forecast per (site, day), same-day overwrite — pending
- **acceptance-2** — API tests: non-lead 403, ungranted 422, light-mode admit, wrong device_class 422, no entity id in logs — pending
- **acceptance-3** — unit tests of the day selection (fresh observed, stale observed, forecast only) — pending
- **acceptance-4** — unit test around local midnight vs. UTC — pending
- **acceptance-5** — unit test: HA error / non-numeric state → no observed record, forecast still written — pending
- **acceptance-6** — spec diff review + `mkdocs build --strict` — pending

## Consistency notes

**Duplication with REQ-046 mode B (proceed, operator decision D1 2026-11-17).**
Established: the site-level HA precipitation binding exists
(`home_assistant_weather_adapter.py:127`, `HaSensorMapping.precipitation_entity`,
`weather.py:114`) and REQ-046:386/477 name it as the measured-rain feed for
REQ-022/037. Missing is coexistence with a public forecast: the resolver takes
one source per run (REQ-046 §3.5). F-28 is therefore narrowed to that extension;
no second binding. The reviewer proposed `revisit-after operator decision`; the
operator chose "extend REQ-046".

**Role (proceed, D1).** The weather source stays LEAD-only
(`tenant_router.py:148`, REQ-049 §2.10); `technical` gates the entity listings
only (REQ-005:1842). The interview answer "technical binds" (requirement R1) is
corrected accordingly.

**Overlap with F-13 (proceed).** F-13 moves the fetch to an interval of at least
6 h. Measured rain on the current day can then be older than the 6-h freshness of
F-29; F-29 applies the freshness rule to the current day only (D2) and reads a
completed day's final value, so the interval does not starve the balance.

## Risks

- Assumption A1: the Netatmo integration in HA exposes a daily cumulative rain sensor; a gauge with only hourly values needs a summation rule.

## References

- Issue #3002, roadmap item R-27, REQ-046 §3.5 / mode B
- `project/requirements/measured-rain-soil-water-balance.md` (R1, R2)

## Betreiberentscheidungen 2026-11-27

- **Annahme A1 trifft nicht zu.** Der Regenmesser (Netatmo) liefert in Home Assistant **keine Tagessumme**. F-28 braucht deshalb eine Summierregel: Aus den gelieferten Stunden- oder Momentanwerten wird die Tagessumme bis zur lokalen Tagesgrenze selbst gebildet. Vor dem Entwurf ist zu messen, welche Entität und welche Auflösung tatsächlich ankommt.
- A2 bestätigt: Die Frische von 6 Stunden ist fest und nicht einstellbar.
