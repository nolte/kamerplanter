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
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/backend/app/tasks/weather_tasks.py:233
      resolution: revisit-after Betreiberentscheidung "Wo und wie oft wird die Roh-Entität gelesen" (nach der Messung der Entität)
      evidence: "Die REQ-046-Bindung wird nur in resolve_daily beim Abruf gelesen (Intervall >= 6 h); der Adapter liest einen Momentanwert (adapter :133-136, get_state) und HaClient hat keine History-Methode (ha_client.py :90-178). Eine Tagessumme aus Stunden-/Momentanwerten ist so nicht bildbar."
    - kind: prior-art
      target: src/backend/app/tasks/sensor_ingestion_tasks.py:12
      resolution: revisit-after dieselbe Entscheidung
      evidence: "ingest_ha_readings liest alle 5 min jede Sensor-Entität mit Freigabe-Prüfung nach TimescaleDB (Beat tasks/__init__.py:628-632, nur bei timescaledb_enabled); Sensor.site_key bindet an den Standort (models/sensor.py:16). Zweiter vorhandener Bindungsweg neben weather_source_configs."
    - kind: drift
      target: src/backend/app/tasks/irrigation_tasks.py:80
      resolution: revisit-after Edit acceptance-3 (Auswahl je Feld)
      evidence: "forecast.temp_min_c is None -> skipped; ein Regen-only-observed-Datensatz neben der Prognose kann als exact[0] gewählt werden, dann entsteht für den Standort gar kein Bedarf."
    - kind: drift
      target: src/backend/app/domain/services/sensor_service.py:461
      resolution: revisit-after Edit (neues Kriterium zu den übrigen Lesern)
      evidence: "get_site_weather_forecast gibt jeden Datensatz im Horizont aus; mit observed + forecast am selben Tag zeigt das WeatherForecastWidget zwei Zeilen. Weitere Leser: frost_forecast.py:44, season_signal_resolver.py:113, environment_snapshot_service.py:488."
    - kind: drift
      target: src/backend/app/domain/engines/tenant_export_engine.py:430
      resolution: revisit-after Edit acceptance-5
      evidence: "REDACTED_FIELDS['weather_source_configs'] = ('sources.config.api_key_ref',) - die HA-Entitäts-IDs des sensor_mapping reisen heute im Mandanten-Export mit; 'weiterhin weglassen' trifft nicht zu."
    - kind: drift
      target: src/backend/app/data_access/external/home_assistant_weather_adapter.py:131
      resolution: revisit-after Edit acceptance-2
      evidence: "logger.warning('ha_weather_invalid_sensor_id', entity_id=entity_id) (auch :88) - 'die Entitäts-ID erscheint in keinem Log' gilt heute nicht."
    - kind: drift
      target: project/features/site-rain-sensor.md:69
      resolution: revisit-after Edit acceptance-1/-2/-3/-4
      evidence: "acceptance-1 'ein späterer Messwert ersetzt den früheren' und Risiko A1 widersprechen der Entscheidung :117 (Summe selbst bilden); acceptance-3 verweist auf die 'Frischeregel von F-29', obwohl F-28 zuerst kommt und die 6 h fest sind (:118)."
    - kind: drift
      target: src/backend/app/common/enums.py:482
      resolution: revisit-after Edit (Standorttypen)
      evidence: "WEATHER_RELEVANT_SITE_TYPES = {OUTDOOR, GREENHOUSE, BALCONY}; das Feature nennt nur Outdoor und Gewächshaus."
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

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`. Triggers: merges since 2026-11-17 (#3097 F-13, #3131/#3134/#3143 F-8, #3149, #3151/#3154) and the operator decisions of 2026-11-27. The frontmatter holds the eight findings of this run; the nine findings of 2026-11-17 (`feature-consistency-reviewer@5d01b6c4`) are listed below with their fate. No test was run. Line references into this file are those of `cc8531492`, before this section was added. The reviewer codes a contradiction as `drift`, "adjust" as `revisit-after <edit>` and "block" as `revisit-after <decision>`; the resolutions are proposals, the operator decides. The canonical feature spec (`spec/project/feature/`, `spec/.spec-config.yml`) is not in the repository; the run followed the task, not the spec. The report's verdict: **blocked** on one operator decision, see the German section below.

**Findings of 2026-11-17 — fate.**

1. `home_assistant_weather_adapter.py:127` (duplication, proceed, D1) — still true (`_from_sensor_mapping` `:127`, record `:147-163`). The resolution "proceed, extend the binding" no longer carries, see N1.
2. `irrigation_tasks.py:174` (drift, proceed) — moved to `:175-182` (`return exact[0]` `:181`). Still true, aggravated by N3.
3. `weather/tenant_router.py:148` (drift, proceed) — still true (LEAD at `:148` and `:236`; `technical` only on the listings `:250`/`:263`).
4. `REQ-005:1846` (drift, proceed) — moved to `:1847`. Still true; code: `ha_entity_grant_service.py:110-113`.
5. Adapter `:138`, UTC day (drift, proceed) — still true (`:138-146`, `forecast_date=today_utc()` `:150`). The decision of 2026-11-27 demands the local day boundary; `Site.timezone` exists (`site.py:813`, default `"UTC"`).
6. `weather_forecast_repository.py:20` (prior-art, proceed) — still true. The upsert on (site, date, source) **replaces**; for a sum that is the wrong semantics (N1).
7. `irrigation_zone_service.py:376` (prior-art, proceed) — still true (`_resolve_coupling` `:364-400`). The weather path has no such check: `weather_source_service.py` contains no `device_class`.
8. `garden_plan_import.py:31` (prior-art, proceed) — true for the plan, but it does not support acceptance-5: `ALWAYS_DROPPED_FIELDS` names only `flow_rate_ha_entity_id`, `actuator_key`, `flow_rate_source` (see the export finding below).
9. Overlap F-13 (proceed) — still true; F-13 is `done` (#3097), interval minimum and default 6 h (REQ-046 §3.6a `:392`).

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
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
```

**New findings.**

- **N1 — the summing rule against D1 (drift, core; `weather_tasks.py:233`).** The REQ-046 binding is read only in `resolve_daily` at the fetch (interval ≥ 6 h); the adapter reads a momentary value (`:133-136`, `get_state`) and `HaClient` has no history method (`ha_client.py:90-178`). A daily sum from hourly or momentary values cannot be built this way. Bindings live in two places: `weather_source_configs.sources[].config.sensor_mapping.precipitation_entity` (REQ-046 mode B; set by `PUT /t/{slug}/sites/{key}/weather-source`, LEAD, grant check `_require_granted_ha_entities` at `weather_source_service.py:263-271`, read at the fetch), and `Sensor` with `site_key` and `ha_entity_id` (REQ-005; 5-minute ingest into TimescaleDB, `metric_type` free text). D1 chose the first. Which one carries depends on the kind of raw entity, which is still to be measured: a monotonically rising counter (daily sum = difference; coarse sampling works, but the day boundary smears by the sampling interval), "rain in the last hour" (needs hourly sampling), or a rate in mm/h (needs integration over dense sampling). Without the decision F-28 cannot be designed.
- **Second existing binding path (prior-art, `sensor_ingestion_tasks.py:12`).** `ingest_ha_readings` reads every sensor entity every 5 min with the grant check into TimescaleDB (beat `tasks/__init__.py:628-632`, only with `timescaledb_enabled`); `Sensor.site_key` binds to the site (`models/sensor.py:16`). Same decision.
- **N3 — selection per field (drift, `irrigation_tasks.py:80`).** `forecast.temp_min_c is None` → skipped; a rain-only observed record beside the forecast can be picked as `exact[0]`, and then the site gets no demand at all. Rain comes from `observed`, temperature/humidity/wind for ET₀ still from the forecast; acceptance-3 pins only "the measured value". `find_by_site` also returns every record ever stored (no filter on the active source); after a source change old records of the same day are present.
- **Other readers of `weather_forecasts` (drift, `sensor_service.py:461`).** `get_site_weather_forecast` returns every record in the horizon; with observed + forecast on the same day the `WeatherForecastWidget` shows two rows. Further readers: `frost_forecast.py:44`, `season_signal_resolver.py:113`, `environment_snapshot_service.py:488`. A new criterion is needed.
- **Tenant export carries the entity id (drift, `tenant_export_engine.py:430`).** `REDACTED_FIELDS['weather_source_configs'] = ('sources.config.api_key_ref',)` — the HA entity ids of the `sensor_mapping` travel in the tenant export today; "keeps leaving them out" (acceptance-5) is not true.
- **The entity id is logged (drift, adapter `:131`).** `logger.warning('ha_weather_invalid_sensor_id', entity_id=entity_id)` (also `:88`) — "the entity id appears in no log" (acceptance-2) does not hold today.
- **Criteria against the decision of 2026-11-27 (drift, this file `:69`).** acceptance-1 ("a later reading replaces the earlier") and risk A1 contradict the decision at `:117` (build the sum yourself); acceptance-3 refers to the "freshness rule of F-29" although F-28 comes first and the 6 h are fixed (`:118`). The circular reference to F-29 has to go.
- **Site types (drift, `enums.py:482`).** `WEATHER_RELEVANT_SITE_TYPES = {OUTDOOR, GREENHOUSE, BALCONY}`; the feature names only outdoor and greenhouse.

**Further discussion.**

- **N2 — `device_class`.** `device_class: precipitation` fits a sum or counter sensor; a rate entity would presumably carry `precipitation_intensity` (Home Assistant knowledge, not evidenced in the repository). Fix it only after the measurement. The flow-sensor pattern (first `device_class`, then the grant in light mode) is the template but has to be rebuilt in the weather path.
- **Freshness and fetch interval.** With an interval of exactly 6 h plus 5 min tolerance a reading written at the fetch is borderline old at the next run; with an interval above 6 h (up to 168 h) it is almost always stale. An own, denser read cadence dissolves this — one more argument for deciding N1.
- **Docs.** `docs/{de,en}/user-guide/weather-services.md` and `weather-sources.md` both exist; acceptance-6 names only the first. Check which one describes the HA sensor mapping.

**Already implemented:** binding, grant check (422 / light admit), LEAD gate, `technical` on the listings, `data_kind="observed"`, idempotent upsert, `WeatherProvenanceBadge`, the UI field `precipitation_entity` (`WeatherSourceAddDialog.tsx:52`). **New:** measurement beside forecast, summing, local day boundary, `device_class` check, selection rule.

**Cross-feature (R-27).**

- Order: the roadmap (`project/roadmap.md:436-439`, D4) fixes F-28, F-29, F-31, F-30. Hard dependencies by the code: F-28 → F-29 (reading and provenance per day), F-29 → F-30 (demand threshold, look-ahead), F-29 → F-31 (store level, following days). F-31 is no technical precondition for F-30 (F-30 acceptance-6 refers to F-24, not F-31); D4 stays defensible because the read endpoint makes the chain visible.
- Common gaps of the four files: the site-type set (balcony is in the code, in none of the files); rain exposure under glass and roof; the mapping site rain → run demand → plant reminder; the look-ahead over following days; the trigger chain after the fetch; and the decisions of 2026-11-27 stood only in this file (F-29 and F-30 gained their sections in this change).
- Stale line references: REQ-037 throughout +1 (the v1.3 line of 2026-11-22), REQ-005 +1, REQ-053 +24/+26, `care_reminder_service.py:1626` → `:1784`, `irrigation_tasks.py` +1.
- Spec follow-up that stands in no criterion: REQ-037 §3.3 and DoD (`:347`, `:509`) name only outdoor/greenhouse; REQ-037 §3.3 `:383` calls `care_reminder_service.apply_irrigation_demand()`, which does not exist; REQ-005 G-010 is described as existing but is not built; REQ-046 §3.5 "the first successful source wins" (`:379`) contradicts the coexistence.
- Health of the run: 26 criteria checked (F-28: 6, F-29: 8, F-30: 7, F-31: 5). Deferred: F-30 acceptance-7 (zone round) read only against the model, not the service; the documentation content of F-28 acceptance-6 and F-30 acceptance-6 not read. Surfaces without a hit: REQ-018 (no rain reference), REQ-045 (no site or water reference).

**Issue #3002 (read 2026-11-27; the reviewer could not and used `project/requirements/measured-rain-soil-water-balance.md` instead).** The issue body (split out of #2934) is narrower than the feature set: its three acceptance criteria — measured value with documented precedence over the forecast, provenance visible on the demand record, REQ-037 describes the sensor source — are covered by F-28 and F-29; the deferral of reminders (F-30) and the widget (F-31) come from the requirements interview, not from the issue. Its operator comment (dated 2026-11-27 in the text) agrees with the sections of the files: the Netatmo gauge exposes no daily sum, so F-28 needs a summing rule over hourly/momentary readings with the local-day boundary; the agrobiology review is done by the agent and confirmed by the operator (F-29 acceptance-1); the 6-hour freshness is fixed and ADR-008 is no precondition. It decides none of the open points: it does not say where and how often the raw entity is read, and "the postponement uses the existing care scheduling" does not choose between the two existing mechanisms (retiming or a new occurrence) nor settle the scope for watering-plan tasks. Two points of the issue are not covered by any feature as written: the open design point "source precedence per the REQ-005 fallback chain (sensor/MQTT → Home Assistant → weather API)" — D1 binds through REQ-046 mode B and no feature treats an automatic/MQTT rain sensor, unless the open decision picks the REQ-005 sensor path — and the "agrobiology review of the effective-precipitation rule for measured values", which appears only as parameter 5 of the F-29 review list, not in a criterion. A label differs: the requirement artefact (`:69-70`) calls the reuse of the care scheduling A2 and the fixed 6-hour freshness A3; the section "Betreiberentscheidungen 2026-11-27" below records the freshness as "A2 bestätigt".

**Edits required before `ready`** (the report's verdict for F-28, translated): blocked on the decision where and how often the raw entity is read. After it:

1. acceptance-1: sum instead of replace.
2. acceptance-2: `device_class` after the measurement; the log statement against adapter `:88`/`:131`.
3. acceptance-3: selection per field, name the 6 h directly, no reference to F-29.
4. acceptance-4: local day through `Site.timezone`.
5. acceptance-5: the tenant export does not redact the entity id today.
6. A new criterion on the other readers of `weather_forecasts`.
7. Site types.
8. Delete risk A1.

## Risks

- Assumption A1: the Netatmo integration in HA exposes a daily cumulative rain sensor; a gauge with only hourly values needs a summation rule.

## References

- Issue #3002, roadmap item R-27, REQ-046 §3.5 / mode B
- `project/requirements/measured-rain-soil-water-balance.md` (R1, R2)

## Betreiberentscheidungen 2026-11-27

- **Annahme A1 trifft nicht zu.** Der Regenmesser (Netatmo) liefert in Home Assistant **keine Tagessumme**. F-28 braucht deshalb eine Summierregel: Aus den gelieferten Stunden- oder Momentanwerten wird die Tagessumme bis zur lokalen Tagesgrenze selbst gebildet. Vor dem Entwurf ist zu messen, welche Entität und welche Auflösung tatsächlich ankommt.
- A2 bestätigt: Die Frische von 6 Stunden ist fest und nicht einstellbar.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

F-28 ist auf diese Entscheidung blockiert. Sie fällt, **nachdem gemessen ist**, was die Netatmo-Entität liefert (Art und Auflösung): ein steigender Zähler erlaubt grobes Abtasten (Tagessumme = Differenz, die Tagesgrenze verschmiert um das Abtastintervall), „Regen der letzten Stunde“ braucht stündliches Abtasten, eine Rate in mm/h braucht dichtes Abtasten und Integration.

- **Wo und wie oft wird die Roh-Entität gelesen?** Heute liest die REQ-046-Bindung die Entität nur beim Wetterabruf (`weather_tasks.py:233`, Intervall mindestens 6 h) als Momentanwert (`home_assistant_weather_adapter.py:133-136`); `HaClient` kennt keine History-Abfrage (`ha_client.py:90-178`), und der Upsert je (Standort, Tag, Quelle) ersetzt den früheren Wert (`weather_forecast_repository.py:20`). Eine Tagessumme entsteht so nicht.
  - **Eigener Lesetakt an der REQ-046-Bindung:** Ein eigener Beat nur für die HA-Entität (lokal, kein Kontingentproblem); die Bindung und D1 vom 2026-11-17 bleiben.
  - **HA-History-API:** Eine neue Methode im `HaClient`; die Summe wird beim Abruf aus der Historie gebildet, ohne eigenen Takt.
  - **REQ-005-Sensor mit TimescaleDB:** Nutzt den vorhandenen 5-Minuten-Ingest (`sensor_ingestion_tasks.py:12`, Beat `tasks/__init__.py:628-632`) und ein Aggregat; hängt an `timescaledb_enabled` (Light-Modus zu klären) und ist ein zweiter Bindungsweg neben D1.
  - **Summe in Home Assistant bilden (Helfer):** D1 bleibt unverändert, Kamerplanter liest weiter einen Tageswert; die Summierregel liegt dann beim Betreiber in Home Assistant.
- **Danach festzuschreiben: `device_class`.** `precipitation` passt zu Summe oder Zähler, eine Raten-Entität trägt vermutlich `precipitation_intensity` (nicht im Repo belegt). Der Wetterpfad prüft `device_class` heute gar nicht (`weather_source_service.py`).
- **Rangfolge der Regenquellen (aus Issue #3002, in keinem Kriterium).** Das Issue nennt die Fallback-Kette aus REQ-005 (eigener Sensor/MQTT → Home Assistant → Wetterdienst → Handeingabe). Die Entscheidung D1 vom 2026-11-17 bindet den Regen nur über die Home-Assistant-Zuordnung von REQ-046; ein MQTT-Regensensor nach REQ-005 hat keinen Weg in die Bilanz.
  - **Nur Home Assistant (heutiger Entwurf):** F-28 bleibt klein; ein MQTT-Regensensor wird nicht ausgewertet. Das Issue wird in diesem Punkt angepasst.
  - **Volle Kette nach REQ-005:** F-28 muss beide Bindungswege lesen und eine Rangfolge festlegen; das hängt an der Entscheidung, wo die Roh-Entität gelesen wird.
