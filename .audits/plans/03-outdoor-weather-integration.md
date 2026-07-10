---
plan-type: implementation-plan
title: Outdoor-Wetter-Integration & CV-Diagnose (NASA POWER, ET₀, Winterhärtezonen, CV-Krankheitsdiagnose)
epic: outdoor-weather-integration
covers: [REQ-041, REQ-037, REQ-039, REQ-038, REQ-040]
source-audit: .audits/awesome-agriculture-integration-plan.md
status: ready
created: 2026-07-10
verified-against: develop
parallelizable: partial (REQ-041 blockt Welle 1; 037‖039 danach; 038 unabhängig)
specialist: fullstack-developer
---

## Ziel

Dieser Plan überführt fünf awesome-agriculture-inspirierte Outdoor-/CV-Requirements von ihrem
aktuellen Seam-Zustand in produktive Integrationen. Die tragenden Nahtstellen stehen bereits auf
`develop` (aus REQ-046 #403/#405 für die Wetter-Datenquellen-Schicht und aus #360 für die
Winterhärte-Ampel), aber die eigentlichen externen Anbindungen und Berechnungs-Engines fehlen:

- **REQ-041 (NASA POWER)** liefert global verfügbare Klimanormale (`climate_normals`) und gemessene
  Solarstrahlung (`solar_radiation_mj_m2`) — beides ist die Datenbasis für REQ-037 (ET₀-PM-Pfad) und
  REQ-039 (Zonen-Resolver). **Harter Blocker der Welle 1.**
- **REQ-037 (Evapotranspiration/Bewässerung)** baut auf REQ-041 auf und schließt den inerten
  ET-Override-Seam im `watering_service.py`.
- **REQ-039 (Winterhärtezonen DACH)** ergänzt die bereits fertige Ampel um einen automatischen
  Zonen-Resolver aus Klimanormalen.
- **REQ-038 (CV-Diagnose)** ist eine eigenständige ML-Initiative (Krankheits-/Mangelbilder), komplett
  entkoppelt von der Wetterschiene — jederzeit parallel startbar.
- **REQ-040 (Enrichment OpenFarm-Dump)** ist bewusst zurückgestellt, optional, niedrigste Priorität.

## Ist-Stand (verifiziert 2026-07-10)

### REQ-041 — NASA POWER: OPEN, Seams vorhanden

Verdikt: **Seams stehen, konkrete Integration fehlt.**

Evidenz (Read verifiziert):
- `app/domain/models/weather.py`: `WeatherForecast.solar_radiation_mj_m2: float | None` (Z.59),
  `data_kind: WeatherDataKind` mit Literal `"reanalysis"` (Z.22/55), `ClimateNormal` als „minimal
  foundation model" (Z.64-82) mit `monthly_temp_min_c` und `coldest_month_min_c` — Docstring nennt
  REQ-041 explizit als Owner der Vollversion.
- `app/domain/interfaces/weather_adapter.py`: ABC `WeatherAdapter` mit `fetch_daily(...)` (abstrakt)
  und `fetch_climate_normals(...)` (default `return None`; nur REQ-041/REQ-039 überschreiben). ABC
  nennt „DWD / OpenWeatherMap / Open-Meteo / NASA POWER" bereits im Docstring.
- `app/domain/services/weather_adapter_registry.py`: `WeatherAdapterRegistry` speichert Adapter-
  **Klassen** (nicht Instanzen, wegen Konstruktor-DI); Docstring nennt `NasaPowerWeatherAdapter` als
  künftigen Registranten.
- `app/data_access/external/registration.py`: zentrale Registrierungsliste (`register_external_adapters`),
  aktuell dwd/open-meteo/openweathermap/home_assistant. **Kein** `nasa_power_weather_adapter`-Import.
- `app/data_access/external/weather_attributions.py`: `WEATHER_ATTRIBUTIONS`-Dict — **kein**
  `"nasa-power"`-Eintrag.
- `app/tasks/weather_tasks.py::fetch_weather_forecasts` + `app/tasks/frost_forecast_tasks.py`
  (Frostwarnung) existieren. **Kein** `fetch_climate_normals`-Task, keine `climate_normals`-Collection.

Fehlt: konkreter `NasaPowerWeatherAdapter(WeatherAdapter)` gegen `power.larc.nasa.gov` (keyless),
Parameter-Mapping, `climate_normals`-Collection + Repository + Edge `has_climate_normal`, Celery-Task
`fetch_climate_normals`, Throttling/Caching (0.5°-Zellen, TTL 180d, HTTP 429-Backoff),
CC-BY-4.0-Attribution, Frontend-Klimanormal-Anzeige, Guard-Ausschluss `data_kind="reanalysis"` in der
Frostwarnung, Registrierung in `registration.py`.

### REQ-037 — ET₀/Bewässerung: OPEN, inerter Seam

Verdikt: **Konsumentenseite fertig, Produzentenseite (ET-Calculator) fehlt komplett.**

Evidenz:
- `app/domain/services/watering_service.py::suggest_volume` (Z.225-352): Parameter
  `et_net_demand_ml: float | None = None`; Docstring Z.239-242 „inert until the REQ-037 follow-up
  wires a real ET calculator in; the hook is exercised by tests so it does not rot". Override wird via
  `_apply_volume_override(..., source="evapotranspiration_demand", allow_zero=True)` (Z.330-337)
  angewandt — ET-0-Bedarf bedeutet „nicht gießen", nicht 10 ml. WHC-Deckelung über
  `substrate.water_holding_capacity_percent` (Z.284) vorhanden.

Fehlt: `EvapotranspirationCalculator` (FAO-56 Penman-Monteith + Hargreaves-Fallback),
`crop_coefficient_kc` an GrowthPhase/Species + `KC_DEFAULTS`-Tabelle + `resolve_kc`-Kaskade,
Collection `irrigation_demands` + Edges, Celery-Task `compute_irrigation_demand` (nach Wetter-Update),
Frontend-Wasserbilanz, Kc-Pflege im Expertenmodus, REQ-022-Verdrahtung (adaptiver
`watering_interval_days`), Scope-Guard NUR `outdoor`/`greenhouse`. Dependency `aquacropeto` (BSD-3).

### REQ-039 — Winterhärtezonen DACH: PARTIAL

Verdikt: **Ampel + D5-Invariante fertig (#360); Zonen-Ableitung fehlt.**

Evidenz:
- `app/domain/engines/winter_hardiness_engine.py`: `evaluate_winter_hardiness(...)` (Z.72),
  `parse_zone` (Z.46), `_zone_delta` (Z.63), `derive_winter_path` (Z.101),
  `validate_d5_invariant` (Z.106), `map_frost_sensitivity` (Z.37) — vollständig, in
  `overwintering_profile_service.py` verdrahtet.
- `app/domain/models/site.py::Site.climate_zone: str = ""` (Z.98) — manuelles Freitext-Feld.
  **Kein** `hardiness_zone`, `hardiness_zone_source`, `mean_annual_minimum_c`, `postal_code`.

Fehlt: `HardinessZoneResolver` (Zone aus `mean_annual_minimum_c` / Klimanormalen — hängt an REQ-041),
Referenz-Collection `hardiness_zones` (USDA 1a–13b, 26 Einträge) + Edge `located_in_zone`,
automatische `site.hardiness_zone`-Befüllung, `OpenMeteoClimateNormalAdapter` (bzw. Konsum der
REQ-041-`climate_normals`), Frost-Defaults (`typical_last_frost_md`/`typical_first_frost_md`) →
REQ-015-A, `refresh_site_hardiness_zones`-Beat, `seed_hardiness_zones`-Job, API-Endpunkte,
Frontend-Badge + „Zone automatisch ermitteln". Datenbasis: DWD Open Data (GeoNutzV) / Open-Meteo
(CC-BY-4.0). Der optionale `FrostlineUsAdapter` (US-only) ist **nicht** Teil des DACH-Default-Flows.

### REQ-038 — CV-Diagnose: OPEN, unabhängig

Verdikt: **Eigenständige ML-Initiative; nichts vorhanden außer wiederverwendbarer Infra.**

Evidenz:
- `src/inference-service/app/main.py`: `/embed`, `/embed/batch`, `/match`, `/reference/*` (REQ-029)
  + `/pest/detect`, `/pest/reference/*`, `/pest/coverage`, `/pest/status` (REQ-044, frozen-DINOv2
  Few-Shot). **Kein** `/classify/disease`, `/disease`, `/diagnosis`, `/deficiency`.
- Abgrenzung: REQ-044 deckt Foto→Schädling via Few-Shot; REQ-038 verlangt einen ONNX-**Krankheits**-
  klassifikator (PlantDoc CC-BY-4.0) + PlantCV-Phänotyp-Pipeline (MPL-2.0) — eigenständig offen für
  Krankheiten/Mangelbilder.

Fehlt: ONNX-Krankheits-Endpunkt `/classify/disease` im inference-service, PlantCV-`PhenotypeEngine`,
Collection `plant_diagnosis_requests` + 4 Edge-Collections (`cv_diagnosed_for`, `cv_diagnosis_found`,
`cv_attached_to_inspection`, `cv_phenotype_of`), Consent `plant_diagnosis` + EXIF-Strip
(wiederverwendbar aus REQ-029), Confidence-Gates + „nur Hypothese"-Disclaimer, Frontend-Diagnose-Flow.
Fachliche Lücke: REQ-010 hat keine `deficiency`-Collection → `matched_*_key = null` für Mangel,
Matching über REQ-036-Symptom-Slugs. Lizenz: nur PlantDoc CC-BY-4.0 + Eigendaten (PlantVillage
fallengelassen, G1); PlantCV MPL-2.0 unverändert (nicht patchen).

### REQ-040 — Enrichment OpenFarm: OPEN, optional/zurückgestellt

Verdikt: **Bewusst zurückgestellt; Architektur-Rahmen (REQ-011) vorhanden.**

Evidenz: `ExternalSourceAdapter`-ABC + `AdapterRegistry` + `EnrichmentEngine` mit GBIF/Perenual
(`gbif_adapter.py`, `perenual_adapter.py`) vorhanden. Fehlt: einmaliger `OpenFarmDumpImporter`
(CC0-Dump, kein Live-Adapter, G3), `CompanionImportService` (Edges nur aus Dump). Growstuff nur
Mapping-Idee (G2, kein Wertimport wegen CC-BY-SA/REQ-032-Kollision). Niedrigste Prio.

## Arbeitspakete

### WP-1 — REQ-041: NASA POWER Adapter + Klimanormale (BLOCKER Welle 1)

**Problem:** Die Wetter-Datenquellen-Schicht (REQ-046) nennt `NasaPowerWeatherAdapter` in Registry-
und ABC-Docstrings, aber es gibt keine konkrete Implementierung, keine `climate_normals`-Collection und
keinen Klimanormal-Task. Ohne diese fehlt REQ-037 der Solarstrahlungs-Eingang für den präzisen
PM-Pfad und REQ-039 der Klimanormal-Eingang für den Zonen-Resolver.

**Umzusetzen:**
- `NasaPowerWeatherAdapter(WeatherAdapter)` in `app/data_access/external/nasa_power_weather_adapter.py`
  mit `source_name = "nasa-power"`, `kind = "public"`, `requires_api_key = False`. Basis-URL
  `https://power.larc.nasa.gov/api/temporal` (env `NASA_POWER_BASE_URL`, überschreibbar).
- `fetch_daily(...)` gegen `/daily/point` mit `community=AG`, Parametern
  `T2M_MIN,T2M_MAX,PRECTOTCORR,WS2M,RH2M,ALLSKY_SFC_SW_DWN`; rückblickend (`DATA_LATENCY_DAYS=7`,
  `days_back` aus `NASA_POWER_DAILY_DAYS_BACK=14`). Mapping: `WS2M` m/s → km/h (×3.6),
  `ALLSKY_SFC_SW_DWN` → `solar_radiation_mj_m2`, POWER-Fehlwert `-999` → `None`, `weather_code=None`,
  `wind_gust_kmh=None`, `data_kind="reanalysis"`.
- `fetch_climate_normals(...)` gegen `/climatology/point` (`T2M,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN`),
  mappt 12 Monatswerte je Parameter auf `ClimateNormal`; `coldest_month_min_c = min(monthly_temp_min_c)`.
- `ClimateNormal`-Modell auf die Vollversion erweitern (additiv, REQ-041 §2.2): `climate_normal_id`,
  `period_start_year`/`period_end_year`, `monthly_temp_avg_c`, `monthly_precip_mm`, `monthly_solar_mj_m2`,
  `annual_temp_avg_c`, `annual_precip_mm` — bestehende Felder (`monthly_temp_min_c`,
  `coldest_month_min_c`) unverändert lassen (REQ-046-Kompatibilität).
- Migration: Doc-Collection `climate_normals` + Edge `has_climate_normal` (sites → climate_normals) im
  `kamerplanter_graph` idempotent anlegen (versioniertes Migrations-Framework `python -m app.migrations`).
- Repository `ClimateNormalRepository` (CRUD + Upsert je `(site_key, source)`, TTL-Prüfung).
- Celery-Task `fetch_climate_normals` (monatlicher Beat, 1. des Monats 04:00 + on-demand bei Anlage
  einer Outdoor-/Greenhouse-Site mit GPS). Idempotent: Re-Fetch nur nach Ablauf `NASA_POWER_CLIMATE_TTL_DAYS=180`.
- `fetch_weather_forecasts` erweitern: NASA POWER nur ziehen wenn priorisiert/Fallback; POWER-Records
  mit `data_kind="reanalysis"` schreiben. Upsert auf `(site_key, forecast_date, source="nasa-power")`
  — keine Re-Fetches bereits geladener Tage.
- Guard: `frost_forecast_tasks` / `check_frost_warnings` MÜSSEN Records mit `data_kind="reanalysis"`
  ignorieren (nur `"forecast"` triggert Frühwarnungen).
- Throttle: max. `NASA_POWER_MAX_RPS=1.0`; HTTP 429/5xx → exponentielles Backoff, Site überspringen
  (Retry beim nächsten Beat), Lauf bricht nicht ab.
- Registrierung: Import in `register_external_adapters` (`registration.py`).
- Attribution: `"nasa-power": "Klima-/Strahlungsdaten: NASA POWER (power.larc.nasa.gov)"` in
  `WEATHER_ATTRIBUTIONS`.
- Frontend: Standort-Detail-Tab „Klima am Standort" (12-Monats-Diagramm aus `ClimateNormal`),
  Quellen-Badge `nasa-power` mit `Reanalyse`-Label vs. Vorhersage; Solarstrahlung im Tagesdetail;
  Attributions-Hinweis. i18n DE/EN unter `pages.siteDetail.climate.*` / `enums.weatherSource.*`.

**Betroffene Dateien:**
- NEU `app/data_access/external/nasa_power_weather_adapter.py`
- NEU `app/data_access/repositories/climate_normal_repository.py` (Ort analog bestehender Repos)
- `app/domain/models/weather.py` (ClimateNormal-Erweiterung)
- `app/data_access/external/registration.py`, `app/data_access/external/weather_attributions.py`
- `app/tasks/weather_tasks.py`, `app/tasks/frost_forecast_tasks.py`, `app/tasks/__init__.py` (Beat)
- `app/migrations/` (neue Migration climate_normals + has_climate_normal)
- Frontend: Site-Detail-Page + Wetter-Widget (Badge/Reanalyse-Label), neue Klima-Komponente, i18n
- Tests: `tests/` Adapter-Mapping (m/s, -999), Climate-Normal-Mapping, Task-Caching, Guard-Test

**Akzeptanzkriterien (testbar):**
- Für eine Outdoor-Site mit GPS schreibt `fetch_weather_forecasts` POWER-Tageswerte mit
  `source="nasa-power"`, `data_kind="reanalysis"`, gefülltem `solar_radiation_mj_m2`.
- `WS2M` wird korrekt m/s→km/h (×3.6) gemappt; `-999` → `None`.
- `fetch_climate_normals` erzeugt je Site genau einen `ClimateNormal` (12 Werte je Parameter,
  `coldest_month_min_c == min(monthly_temp_min_c)`), verknüpft via `has_climate_normal`.
- Bereits geladene `(site_key, forecast_date, "nasa-power")` werden nicht erneut abgerufen;
  `ClimateNormal` erst nach TTL neu geholt.
- Bei Quellen-Priorität `["dwd","open-meteo","nasa-power"]` wird POWER nur als Fallback gezogen.
- POWER-Records lösen **keine** Frost-/Regen-/Sturmwarnung aus.
- HTTP 429/5xx/Timeout → Lauf bricht nicht ab, betroffene Site übersprungen, Bestandsdaten bleiben.
- Adapter funktioniert ohne API-Key/Secret.
- Frontend zeigt Attributions-Hinweis + unterscheidbares `nasa-power`/`Reanalyse`-Badge; i18n DE/EN.
- Migration legt Collection/Edge idempotent an; additive Felder brechen Altdaten nicht.

**Spezialist:** fullstack-developer
**Aufwand:** M
**Abhängigkeiten:** REQ-046 (Registry/ABC — vorhanden), REQ-005 (WeatherForecast/Tasks — vorhanden),
REQ-002 (Site.gps_coordinates — vorhanden). **Keine** Upstream-WP-Abhängigkeit → als erstes starten.
**Lizenz-Gate:** NASA POWER frei nutzbar (de facto CC-BY-4.0/US-gemeinfrei), **Zitationsbitte** →
Attribution im „Klima am Standort"-Abschnitt + NOTICE. Kein Code aus `agroclimatology` (Ruby/MIT)
übernehmen — nur Konzept.

### WP-2 — REQ-037: Evapotranspiration-Calculator + Bewässerungsbilanz (Welle 1, nach WP-1)

**Problem:** `watering_service.suggest_volume` besitzt den ET-Override-Seam `et_net_demand_ml`, der
inert ist („inert until the REQ-037 follow-up wires a real ET calculator in"). Es fehlt der Produzent:
eine physikalisch fundierte ET₀→ETc→Netto-Bedarf-Berechnung und deren tägliche Materialisierung.

**Umzusetzen:**
- pip-Dependency `aquacropeto` (Import `aquacrop_eto`) in `pyproject.toml`; **Python-3.14-Kompatibilität
  verifizieren** (letztes Release 2022). Falls inkompatibel: Source vendored einbinden, Copyright-Notice
  „Mark Richards" (BSD-3-Clause) erhalten.
- `EvapotranspirationCalculator` in neuem `app/domain/calculators/evapotranspiration_calculator.py`
  (reine Berechnung, keine I/O): `calculate_et0(...)` → FAO-56 Penman-Monteith wenn Feuchte+Wind
  vorhanden (Strahlung gemessen `solar_radiation_mj_m2` aus WP-1 oder aus Temperaturhub geschätzt),
  sonst Hargreaves-Fallback; `calculate_water_balance(...)` → ETc, effektiver Niederschlag
  (FAO-Faustregel ×0.8 bei >5 mm), Netto-Bedarf, WHC-Deckelung, Volumen (1 mm = 1 L/m²).
- Kc-Felder: `GrowthPhase.crop_coefficient_kc: float | None` (0.1–1.5) + `kc_source`,
  `Species.default_crop_coefficient_kc`; `KC_DEFAULTS`-Tabelle je `plant_type` (Initial/Mid/Late);
  `resolve_kc`-Kaskade (Phase → Species → Tabelle → Global-Default 0.8) in Service-Schicht.
- Collection `irrigation_demands` + `IrrigationDemand`-Modell (et0_mm, kc_used, etc_mm,
  effective_precipitation_mm, net_demand_mm, net_demand_mm_capped, recommended_volume_liters,
  et_method, method_reason, quality, weather_source, computed_at); Edges `has_irrigation_demand`
  (sites→) und `demand_for_run` (planting_runs→). Migration idempotent.
- Celery-Task `compute_irrigation_demand` (Beat 06:15, 15 Min nach `fetch_weather_forecasts`):
  läuft NUR für `Site.type ∈ {outdoor, greenhouse}` mit GPS; iteriert Forecasts × aktive Runs;
  ruft `resolve_kc` + `substrate_service.water_holding_capacity_mm`; upsertet `IrrigationDemand`;
  triggert `care_reminder_service.apply_irrigation_demand()`.
- REQ-022-Verdrahtung: `CareReminderEngine` konsumiert `IrrigationDemand` — `net_demand_mm_capped == 0`
  → Gieß-Erinnerung unterdrücken; hoher Bedarf → vorziehen + Volumen-Hinweis; Indoor unverändert
  intervallbasiert. Den ET-Override auch an `watering_service.suggest_volume(et_net_demand_ml=...)`
  durchreichen (der bestehende Seam).
- Frontend: Wasserbilanz-Widget (Standort-Detail + Pflege-Dashboard: ET₀/ETc/eff. Niederschlag/
  Netto-Bedarf mm+L, Methoden-Qualität als Chip high/medium/low); Kc-Feld hinter
  `ExpertiseFieldWrapper` (Stufe expert) in GrowthPhase-/Species-Dialog. i18n `pages.irrigation.*`.

**Betroffene Dateien:**
- NEU `app/domain/calculators/evapotranspiration_calculator.py`
- NEU `app/domain/models/irrigation_demand.py`, `app/data_access/repositories/irrigation_demand_repository.py`
- `app/domain/models/` GrowthPhase/Species (Kc-Felder), `app/domain/services/` (resolve_kc, KC_DEFAULTS)
- `app/domain/services/watering_service.py` (ET-Override-Konsum), CareReminder-Engine/Service (REQ-022)
- `app/tasks/__init__.py` (Beat) + neuer Task-Modul `app/tasks/irrigation_tasks.py`
- `app/migrations/` (irrigation_demands + Edges), `pyproject.toml` (aquacropeto)
- Frontend: Site-Detail + Pflege-Dashboard-Widget, Kc-Feld, i18n
- Tests: 7 AC-Szenarien (PM, Hargreaves-Fallback, Regen deckt Bedarf, WHC-Deckelung, Kc-Kaskade,
  Indoor-Skip, Volumen)

**Akzeptanzkriterien (testbar):** die 7 REQ-037-Szenarien (§7):
- Vollständige Wetterdaten → `et_method="fao56_penman_monteith"`, `quality="high"`, positives `etc_mm`.
- Nur Tmin/Tmax → `et_method="hargreaves"`, `quality="medium"`, keine Exception.
- ETc 3.5 mm + Regen 12 mm → `net_demand_mm < 0`, `net_demand_mm_capped == 0`, Erinnerung unterdrückt.
- net_demand 9 mm + WHC 6 mm → `net_demand_mm_capped == 6`.
- GrowthPhase-Kc 1.1 schlägt Tabellen-Default (`kc_used == 1.1`).
- Indoor-Site → **kein** `IrrigationDemand`, Intervall-Logik bleibt.
- net_demand_capped 4 mm × 5 m² → `recommended_volume_liters == 20.0`.

**Spezialist:** fullstack-developer
**Aufwand:** S–M
**Abhängigkeiten:** **WP-1 (REQ-041)** für den PM-Pfad (`solar_radiation_mj_m2`) — Hargreaves-Fallback
funktioniert schon ohne, der präzise PM-Pfad braucht Strahlung. REQ-019 (`water_holding_capacity_percent`
— vorhanden), REQ-022 (CareReminderEngine — vorhanden), REQ-002/013 (Site/PlantingRun — vorhanden).
**Lizenz-Gate:** `aquacropeto` BSD-3-Clause (permissiv, MIT-kompatibel) — bei Vendoring
Copyright-Notice erhalten. 🔴 **`pyTSEB` (GPL-3.0) ist tabu** — kein Import (Outbound-Inkompatibilität).

### WP-3 — REQ-039: HardinessZoneResolver + Zonen-Referenz (Welle 1, nach WP-1, ‖ WP-2)

**Problem:** Die Winterhärte-Ampel (`evaluate_winter_hardiness`, #360) ist fertig, bezieht die
Standortzone aber aus dem manuellen Freitext-Feld `Site.climate_zone`. Es fehlt die automatische
Ableitung der Zone aus Klimanormalen und die kanonische USDA-Zonen-Referenz.

**Umzusetzen:**
- Referenz-Collection `hardiness_zones` (nicht tenant-scoped, analog `BotanicalFamily`): USDA 1a–13b
  (26 Einträge), `_key = zone` (z.B. `"7a"`); Felder `zone_number`, `subzone`, `temp_min_c`/`temp_max_c`
  (+`_f`), `description_de`, `representative_regions_de`, `typical_last_frost_md`/`typical_first_frost_md`.
  DACH-Zonen (6a–8b) mit gepflegten DE-Beschreibungen + Frost-Richtwerten. UNIQUE-Index auf `[zone]`.
- Seed-Job `seed_hardiness_zones` (dediziertes YAML `hardiness_zones.yaml` + eigener SeedJob-Eintrag,
  Muster wie Substrat-Seeds #398).
- `Site`-Erweiterung (additiv, non-breaking): `hardiness_zone: str | None` (Format `^\d{1,2}[a-b]$`),
  `hardiness_zone_source: Literal["manual","derived_gps","derived_postal","frostline_us"]`
  (Default `"manual"`), `hardiness_zone_resolved_at`, `mean_annual_minimum_c`, `postal_code`.
  Migration übernimmt bestehendes `climate_zone` als Initialwert; Field-Validator hält beide synchron.
- Edge `located_in_zone` (Site→HardinessZone), Properties `resolved_at`/`source`, Index auf `[_from]`.
- Engine `HardinessZoneResolver` (`app/domain/engines/hardiness_zone_resolver.py`):
  `classify_from_minimum(mean_annual_minimum_c, zones)` mit Rand-Clamping (<1a / >13b);
  `derive_from_climate_normals(...)`. Konsumiert `ClimateNormal` aus WP-1 (`monthly_temp_min_c` bzw.
  `coldest_month_min_c`) ODER einen `OpenMeteoClimateNormalAdapter` (historische Tagesminima
  1991–2020, `HARDINESS_NORMAL_PERIOD_START/END`).
- Service `HardinessZoneService.resolve_for_site(...)`: Adapter-Auswahl (US-Schnellpfad `postal_code`
  optional → sonst Klimanormal-Pfad), Zone klassifizieren, `Site` updaten, `located_in_zone`
  UPSERTen. `hardiness_zone_source == "manual"` wird vom Refresh **nie** überschrieben.
- Optionaler `FrostlineUsAdapter` (nur US, Laufzeit-Call gegen `phzmapi.org/{zip}.json`, `None` für
  Nicht-US); **NICHT** Teil des DACH-Default-Flows, standardmäßig deaktiviert.
- Celery-Tasks: `refresh_site_hardiness_zones` (vierteljährlicher Beat, nur Sites ohne manuelle
  Override), `seed_hardiness_zones` (einmalig).
- Frost-Defaults: `typical_last_frost_md`/`typical_first_frost_md` befüllen REQ-015-A-Frosttermine
  (`Site.last_frost_date_avg`/`first_frost_date_avg`/`eisheilige_date`), solange weder manuell noch
  per Wetter-API gesetzt.
- API: `GET /api/v1/hardiness-zones`, `/{zone}` (global); tenant-scoped
  `POST .../sites/{site_key}/resolve-hardiness-zone`, `GET .../sites/{site_key}/hardiness`,
  `GET .../plants/{plant_key}/hardiness-check` (Ampel + Zonendifferenz-Begründung).
- Ampel-Verdrahtung: `evaluate_winter_hardiness` (bereits vorhanden) nutzt nun `Site.hardiness_zone`
  statt Freitext-`climate_zone`; die `hardy`-Kurzschluss-Regel bleibt.
- Frontend: Site-Formular-Button „Zone automatisch ermitteln" (aktiv bei GPS/PLZ),
  `HardinessZoneBadge` (Chip + Tooltip aus `description_de`), Inline-Warnung bei nicht-winterharter
  Art im Pflanzen-Anlage-Dialog. i18n `pages.hardiness.*`, `enums.hardinessZoneSource.*`.

**Betroffene Dateien:**
- NEU `app/domain/engines/hardiness_zone_resolver.py`, `app/domain/services/hardiness_zone_service.py`
- NEU `app/data_access/external/open_meteo_climate_normal_adapter.py` (oder Konsum WP-1-climate_normals)
- NEU Seed `hardiness_zones.yaml` + SeedJob, `app/domain/models/hardiness_zone.py`
- `app/domain/models/site.py` (hardiness_zone-Felder + Validator)
- `app/api/` neue Router (hardiness-zones global + tenant-scoped)
- `app/domain/engines/winter_hardiness_engine.py`-Konsumenten (Site.hardiness_zone statt climate_zone)
- `app/tasks/__init__.py` (Beats), `app/migrations/` (Collection/Edge/Site-Felder)
- Frontend: Site-Formular, Badge, Pflanzen-Dialog-Warnung, i18n
- Tests: Resolver-Klassifikation (+Clamping), Ampel-Konsistenz, Adapter-Fallback, Manual-Override-Schutz

**Akzeptanzkriterien (testbar):**
- `hardiness_zones` geseedet 1a–13b; DACH-Zonen mit `description_de` + Frost-Richtwerten.
- `classify_from_minimum` ordnet mittleren Jahres-Tiefstwert korrekt zu (inkl. Rand-Clamping).
- `POST .../resolve-hardiness-zone` leitet für DACH-GPS-Site die Zone aus Klimanormalen ab,
  persistiert `hardiness_zone`/`mean_annual_minimum_c`/`source="derived_gps"` + `located_in_zone`.
- Manuell gesetztes `hardiness_zone` (`source="manual"`) wird vom Refresh nicht überschrieben.
- `evaluate_winter_hardiness`: (Art min 8a, Standort 7a, tender) → `red`; (hardy, Standort ≥ Art) →
  `green`; Differenz ≤ 1 → `yellow`.
- `hardiness-check`-Endpunkt liefert Ampel + Zonendifferenz; `hardy`-Arten erzeugen keine Winterschutz-
  Erinnerungen.
- Frost-Defaults (REQ-015-A) aus Zonen-Richtwerten vorbefüllt, wenn nichts anderes gesetzt.
- Migration: `climate_zone`↔`hardiness_zone` synchron; Sites ohne GPS funktionieren unverändert.

**Spezialist:** fullstack-developer
**Aufwand:** M (Ampel + D5 bereits fertig)
**Abhängigkeiten:** **WP-1 (REQ-041)** für `climate_normals` (bzw. eigener
`OpenMeteoClimateNormalAdapter`). REQ-001 (`Species.hardiness_zones`/`frost_sensitivity` — vorhanden),
REQ-002 (Geo-Index — vorhanden), REQ-046 (Registry — vorhanden). **Disjunkt zu WP-2** (nur lesender
Zugriff auf climate_normals) → parallel zu WP-2 nach WP-1.
**Lizenz-Gate:** USDA-Zonen-**Schema** lizenzfrei (einziges eingechecktes Material). 🔴 **KEINE
USDA/PHZM/PRISM-Zonen-Daten einchecken** (proprietär, OSU/PRISM-Terms). DWD (GeoNutzV: „Datenbasis:
Deutscher Wetterdienst") + Open-Meteo (CC-BY-4.0: „Weather data by Open-Meteo.com") in NOTICE;
frostline-**Code** (MIT) nur falls Parser-Muster übernommen → NOTICE.

### WP-4 — REQ-038: CV-Krankheitsdiagnose (Welle 2, komplett unabhängig)

**Problem:** Der inference-service kann Arten (REQ-029) und Schädlinge (REQ-044, Few-Shot) erkennen,
aber keine **Krankheits-/Mangelbilder** klassifizieren. REQ-038 verlangt einen eigenständigen
ONNX-PlantDoc-Krankheitsklassifikator + PlantCV-Phänotyp-Pipeline mit IPM-Mapping und strengem
„nur Hypothese"-Disclaimer.

**Umzusetzen:**
- inference-service: neuer Endpunkt `POST /classify/disease` (multipart image → classifications +
  model-meta + dim). ONNX-Krankheitsklassifikator (Transfer Learning: ImageNet/DINOv2-Backbone →
  Fine-Tuning auf PlantDoc CC-BY-4.0 + kuratierte Realdaten; CPU-Baseline). Kein neuer Microservice —
  Endpunkt neben `/pest/*`. Modellkarte (`training_base`, `fine_tuned_on`, `onnx_checksum`,
  `model_version`) verbindlich; PlantVillage **nicht** gelistet.
- `PhenotypeEngine` (PlantCV MPL-2.0, lazy import): Segmentierung → Metriken (leaf_area_px,
  green_index, discolored_area_ratio, necrotic_area_ratio, solidity, hue_circular_mean_deg,
  plantcv_version). Reine Messung, keine Diagnose. PlantCV-Quelldateien **nicht patchen**.
- Backend: `CvDiagnosisAdapter` (registriert in bestehender `IdentificationAdapterRegistry`, REQ-029),
  `CvDiagnosisEngine` (Orchestrierung Klassifikator + Phänotyp, IPM-Matching gegen `diseases`/`pests`
  aus REQ-010, Confidence-Gates `CONFIDENCE_SHOW=0.10`/`CONFIDENCE_HIGHLIGHT=0.75` — kein Auto-Accept).
- Collection `plant_diagnosis_requests` (classifications[], phenotype_metrics, model_meta, disclaimer,
  image_hash, image_deleted_at) + 4 Edge-Collections: `cv_diagnosed_for` (→plant_instances/
  planting_runs), `cv_diagnosis_found` (→diseases/pests, Felder confidence/rank/category/confirmed),
  `cv_attached_to_inspection` (→inspections), `cv_phenotype_of` (→harvest_observations). Migration.
- Consent `plant_diagnosis` (analog `plant_identification`, REQ-029/025) + EXIF-Strip (REQ-029 §5.4
  wiederverwenden). Bilddaten **nicht** persistiert (`image_deleted_at` gesetzt); Retention NFR-011.
- REST (tenant-scoped, `/api/v1/t/{tenant_slug}/cv-diagnosis/*`): `/status`, `POST /diagnose`
  (Consent-Pflicht, JPEG/PNG ≤5 MB), `POST /diagnose/{key}/confirm` (nur Vorschlag, Karenz-Gate bleibt),
  `GET /history`. Antwort trägt **immer** nicht-leeren `disclaimer`.
- Optionaler Celery-Task `run_cv_diagnosis` (Latenztoleranz für schwere ONNX/PlantCV-Inferenz).
- Settings (opt-in Default): `cv_diagnosis_enabled=False`, `cv_classifier_model_path`,
  `cv_phenotype_enabled=True`, Confidence-Schwellen, `inference_service_url` (wiederverwendet).
- Frontend: `CvDiagnosisDialog` (Erfassung aus `PlantIdentificationDialog` wiederverwenden),
  Disclaimer-Banner (immer sichtbar), Verdachtsliste Top-3 mit Konfidenz+Kategorie-Chip+IPM-Match,
  Bestätigen-Button, Phänotyp-Panel (nur Intermediate/Expert, REQ-021). Integration in IPM-Inspektion
  (REQ-010), REQ-036-Assistent (Symptom-Slug-Vorbelegung), PlantInstance-Detail (Historie +
  Phänotyp-Verlauf, REQ-007), Pflege-Dashboard-Quick-Action. i18n `pages.cvDiagnosis.*`.
- Fachliche Lücke: `category=="deficiency"` → `matched_disease_key`/`matched_pest_key = null`;
  Matching über REQ-036-Symptom-Slugs (keine neue `deficiencies`-Collection in v1).

**Betroffene Dateien:**
- NEU `src/inference-service/app/disease_classifier.py` + Endpunkt in `main.py` + `schemas.py`
- NEU `app/domain/engines/phenotype_engine.py`, `app/domain/interfaces/cv_diagnosis_adapter.py`,
  `app/domain/engines/cv_diagnosis_engine.py`, `app/data_access/external/cv_diagnosis_adapter_impl.py`
- NEU `app/api/` cv-diagnosis-Router, `app/domain/models/plant_diagnosis_request.py`, Repository
- `app/migrations/` (plant_diagnosis_requests + 4 Edges), Settings, Consent-Registry (`plant_diagnosis`)
- `src/inference-service/` Dependencies (`plantcv`, onnxruntime — Container-Größe beachten)
- Frontend: CvDiagnosisDialog + Integrationen (IPM/REQ-036/PlantInstance/Dashboard), i18n
- Tests: 5 REQ-038-Szenarien (IPM-Match, Mangel, Domänen-Gap/niedrige Konfidenz, Phänotyp-Verlauf,
  Feature deaktiviert) + Disclaimer-nie-leer-Test

**Akzeptanzkriterien (testbar):**
- `CvDiagnosisAdapter` in `IdentificationAdapterRegistry` registriert; ohne Modell/Feature meldet
  `/status` „nicht verfügbar", App bleibt funktionsfähig.
- Disease-Klassifikator als ONNX-Endpunkt im bestehenden inference-service (kein neuer Microservice);
  Fotos verlassen die Instanz im Self-Hosted-Pfad nicht.
- `PhenotypeEngine` liefert ≥ leaf_area, green_index, discolored/necrotic-Ratio + `plantcv_version`.
- Erkannte Krankheiten/Schädlinge via `cv_diagnosis_found`-Edges gegen `diseases`/`pests` gemappt;
  nicht gematchte Treffer bleiben mit `matched_*_key == null`.
- Bestätigung → IPM-Treatment-**Vorschlag**, nie Auto-Anlage, Karenz-Gate unberührt.
- Jede API-Antwort/UI-Anzeige trägt nicht-leeren Disclaimer (automatisierter Test).
- `< CONFIDENCE_SHOW` verworfen; `> CONFIDENCE_HIGHLIGHT` nur Hervorhebung.
- `/diagnose` erfordert Consent `plant_diagnosis`; EXIF entfernt; `image_deleted_at` gesetzt.
- Phänotyp-Metriken pro Pflanze als Zeitreihe abfragbar (REQ-007-Brücke).
- `model_meta` dokumentiert Provenienz; PlantVillage **nicht** gelistet.

**Spezialist:** fullstack-developer (+ ML-Modell-Build als separates Vorarbeits-Artefakt, analog
REQ-044-DINOv2-Prod)
**Aufwand:** L (eigenständige ML-Initiative)
**Abhängigkeiten:** **KEINE** zu WP-1/2/3 → jederzeit parallel startbar. Wiederverwendet REQ-029
(Adapter-Interface, EXIF, PlantIdentificationDialog), REQ-010 (diseases/pests), REQ-036 (Symptom-Slugs),
REQ-007 (harvest_observations), REQ-025 (Consent).
**Lizenz-Gate:** 🔴 PlantVillage **nicht verwenden** (Lizenz ungeklärt, G1). PlantDoc CC-BY-4.0
(Attribution, kommerziell + Modell-Weitergabe erlaubt) → NOTICE. PlantCV MPL-2.0 (Datei-Copyleft):
**unverändert als Library**, keine Quelldatei patchen; MPL-2.0-Notice mitliefern. DINOv2-Backbone
Apache-2.0 (LICENSE vor Produktivnahme verifizieren).

### WP-5 — REQ-040: OpenFarm-CC0-Dump-Enrichment (Welle 3, optional, niedrigste Prio)

**Problem:** Zwei bekannte Companion-/Anbauzeitraum-Lücken lassen sich optional aus einem CC0-Dump
schließen. Bewusst zurückgestellt: OpenFarm-Server tot (nur statischer Dump), Growstuff CC-BY-SA
(kollidiert mit REQ-032-Export), Audit-Lücken großteils geschlossen, GBIF+Perenual bereits produktiv.

**Umzusetzen:**
- `OpenFarmDumpImporter` (liest lokale CC0-Dump-JSON-Fixture, **kein** Netzwerk-Abruf) →
  `ExternalSpeciesData` mit Field-Mapping (binomial_name→scientific_name, sun_requirements→PPFD-
  Heuristik, days_to_maturity, companions).
- `CompanionImportService`: erzeugt REQ-028-`compatible_with`-Edges (bidirectional, score 0.6,
  effect_type general, source „openfarm") nur für beidseitig auflösbare Partner; nicht auflösbar →
  `skipped` (kein Species-Anlegen). Kuratierte höher bewertete Edges nicht herabstufen.
- `external_sources`-Eintrag nur `openfarm` (CC0, `import_mode="static_dump"`, `is_active=false`,
  `maintenance_status="archived"`); Per-Feld-Lizenz-Tracking `license="CC0-1.0"`,
  `attribution_required=false`. Confidence-Kette REQ-011 (leer→0.9, belegt→0.7, Prio 6).
- Manuell dispatchter Task `enrichment.import_openfarm_dump` (kein Beat). Consent-Gate „enrichment".
- **Kein** Growstuff-Adapter/-Eintrag/-Import (G2) — nur Mapping-Referenztabelle in der Doku.
- Frontend: OpenFarm-CC0-Badge + Companion-Herkunftstag; Admin-Button „CC0-Dump importieren"
  (additiv zur REQ-011-Enrichment-Admin). i18n DE/EN. Kein Growstuff-/CC-BY-SA-Badge.

**Betroffene Dateien:**
- NEU `app/adapters/openfarm_dump_importer.py`, `app/domain/services/companion_import_service.py`
- Task-Modul enrichment, `external_sources`-Seed (openfarm), Frontend-Enrichment-Admin, i18n
- Tests: Importer mit gemockter Dump-Fixture; Companion-Import (auflösbar/skip/Schutz bestehender Edges)

**Akzeptanzkriterien (testbar):**
- `OpenFarmDumpImporter` liest lokalen CC0-Dump (kein Netzwerk), Field-Mapping korrekt.
- Kein Growstuff-Adapter/-Eintrag/-Wert in der DB.
- Kein Live-Adapter/Beat; Import einmalig manuell.
- `external_sources` nur `openfarm` (static_dump, archived, inaktiv); Per-Feld CC0-Tracking.
- Companion-Edges nur beidseitig auflösbar; nicht auflösbar → skipped; kuratierte Edges nicht
  herabgestuft; Idempotenz per Checksum/Upsert.
- Fehlende/korrupte Dump-Datei bricht nur den Import ab; Bestandsdaten unberührt.
- Consent „enrichment" fehlt → keine Anwendung pro Tenant.

**Spezialist:** fullstack-developer
**Aufwand:** S–M
**Abhängigkeiten:** REQ-011 (external_sources/mappings/sync_runs — vorhanden), REQ-028
(compatible_with/incompatible_with — vorhanden), REQ-001, REQ-025. **Keine** zu WP-1..4.
**Lizenz-Gate:** OpenFarm-Daten CC0 (keine Attribution). 🔴 **Growstuff (CC-BY-SA 3.0) NICHT
mergen/importieren** — würde ShareAlike auf die abgeleitete Sammlung und jeden REQ-032-Export ziehen;
nur Mapping-Vorlage. Kein CC-BY-SA-Material in der Auslieferung.

## Reihenfolge & Parallelisierung

Abhängigkeitsgraph:

```
                 ┌──────────────────────────────────────────┐
   Welle 1       │  WP-1  REQ-041 NASA POWER  (BLOCKER)      │
                 │  liefert climate_normals + solar_radiation│
                 └───────────────┬──────────────────────────┘
                                 │ (climate_normals, solar_radiation_mj_m2)
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
        ┌─────────────────┐            ┌────────────────────┐
        │ WP-2 REQ-037    │  ‖ parallel│ WP-3 REQ-039       │
        │ ET₀/Bewässerung │  (disjunkt,│ Winterhärtezonen   │
        │ (PM braucht     │   nur lesend│ (Resolver braucht  │
        │  Strahlung)     │   climate_ │  climate_normals)  │
        └─────────────────┘   normals) └────────────────────┘

   Welle 2 (jederzeit, komplett unabhängig — eigener inference-service + Collections)
        ┌────────────────────────────────────────────────┐
        │ WP-4  REQ-038 CV-Krankheitsdiagnose             │
        └────────────────────────────────────────────────┘

   Welle 3 (optional, niedrigste Prio, unabhängig)
        ┌────────────────────────────────────────────────┐
        │ WP-5  REQ-040 OpenFarm-CC0-Dump-Enrichment      │
        └────────────────────────────────────────────────┘
```

- **WP-1 (REQ-041) ist harter Blocker der Welle 1:** Es liefert `climate_normals` (REQ-039-Resolver)
  UND `solar_radiation_mj_m2` (REQ-037-PM-Pfad). Muss zuerst gemergt sein.
- **WP-2 ‖ WP-3** danach parallel: disjunkte Domänen (Bewässerung vs. Winterhärte), beide nur lesend
  auf `climate_normals`/`WeatherForecast`. Bei geteiltem Working-Tree sequenziell committen oder je
  Agent `isolation: worktree` (Projekt-Konvention: schreibende Agenten auf geteiltem Tree seriell).
- **WP-4 (REQ-038)** ist vollständig entkoppelt (eigener inference-service-Endpunkt + eigene
  Collections) → kann parallel zu Welle 1 gestartet werden; braucht zusätzlich ein ML-Modell-Build-
  Artefakt (analog REQ-044-DINOv2-Prod), das als Vorarbeit läuft.
- **WP-5 (REQ-040)** separat, optional, zuletzt.

Empfohlene Merge-Reihenfolge: WP-1 → (WP-2, WP-3) → WP-4 → WP-5. WP-4 darf früher starten, aber nach
WP-1 mergen ist unkritisch (keine Kopplung).

## Definition of Done

- [ ] Alle WP-Akzeptanzkriterien als Tests grün (Backend pytest, Frontend vitest).
- [ ] `ruff` / `ESLint` / `TypeScript` clean (`static`-Check grün — einziger required Check).
- [ ] Alle Migrationen idempotent über `python -m app.migrations`; additive Modell-Felder brechen
      Altdaten nicht (Defaults greifen); Enum-/Feld-Retirement vermieden (kein Startup-Crash auf
      Alt-Volumes).
- [ ] Celery-Beats registriert (`fetch_climate_normals` monatlich, `compute_irrigation_demand` 06:15,
      `refresh_site_hardiness_zones` vierteljährlich) und in `app/tasks/__init__.py` verdrahtet.
- [ ] i18n DE/EN vollständig für alle neuen UI-Strings (DE Default/Fallback).
- [ ] Custom Hooks, die Objekte/Arrays zurückgeben, mit `useMemo` stabilisiert (Projekt-Konvention).
- [ ] Alle CC-BY-Attributionen (NASA POWER, Open-Meteo, DWD, PlantDoc) + MPL-2.0-Notice (PlantCV) in
      `THIRD_PARTY_LICENSES`/NOTICE geführt.
- [ ] 3-Agent-Kette nach Implementierung je WP (UI-Review → Tests → Doku); Auto-UI-Review nach
      Frontend-Änderungen.
- [ ] Pre-Merge-Review je PR (Muster: Cross-Tenant-Lecks, fail-open-Guards, TZ/off-by-one, i18n-
      Umkehrungen — die typischen Merge-Review-Finder dieses Projekts).
- [ ] Docs-Update (Fact-Tables, REQ-Cross-Refs) gemäß `spec/style-guides/DOCS.md`.

## Lizenz- & Risiko-Hinweise

Grundlage: `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

**Erlaubt (permissiv / Attribution-Pflicht):**
- `aquacropeto` **BSD-3-Clause** (REQ-037) — MIT-kompatibel; bei Vendoring Copyright-Notice
  „Mark Richards" erhalten.
- NASA POWER (REQ-041) — frei nutzbar (de facto CC-BY-4.0/US-gemeinfrei), **Zitationsbitte** →
  Attribution Pflicht.
- Open-Meteo **CC-BY-4.0** (REQ-039/041) — „Weather data by Open-Meteo.com".
- DWD Open Data **GeoNutzV** (REQ-039) — „Datenbasis: Deutscher Wetterdienst".
- PlantDoc **CC-BY-4.0** (REQ-038) — Attribution; kommerziell + Modell-Weitergabe ohne ShareAlike.
- PlantCV **MPL-2.0** (REQ-038) — nur als Library nutzen, **keine Quelldatei patchen**, Notice
  mitliefern.
- OpenFarm-Dump **CC0** (REQ-040) — keine Auflagen.
- frostline-**Code** MIT (REQ-039) — nur falls Parser-Muster übernommen → NOTICE.

**🔴 Verboten / tabu:**
- **`pyTSEB` (GPL-3.0-or-later)** — kein Import (Outbound-Inkompatibilität mit MIT); nur eigenständiger
  Nachbau ODER strikt prozessgetrennter Microservice.
- **USDA/PHZM/PRISM-Zonen-Daten** (proprietär, OSU/PRISM-Terms) — **nicht** ins MIT-Repo einchecken;
  nur das lizenzfreie USDA-Zonen-**Schema** + selbst abgeleitete Werte.
- **PlantVillage** (Lizenz ungeklärt, Repo ohne LICENSE, CC-BY-SA↔CC0 widersprüchlich) — **nicht**
  als Trainingsquelle (G1); zusätzlich Lab→Feld-Gap (99,35 % Lab → 31,4 % Feld).
- **Growstuff (CC-BY-SA 3.0)** — kein Wertimport/Merge (G2); ShareAlike würde jeden REQ-032-Export
  binden. Nur Mapping-Vorlage.

**Attribution-Pflicht (NOTICE + UI):** NASA POWER, Open-Meteo, DWD, PlantDoc — die jeweiligen
Attributionsstrings gehören in `THIRD_PARTY_LICENSES`/NOTICE und (Wetter) in die zentrale
`weather_attributions.py` bzw. den „Klima am Standort"-UI-Abschnitt.

**Weitere Risiken:**
- `aquacropeto` letztes Release 2022 → **Python-3.14-Kompatibilität vor Produktiveinsatz prüfen**,
  sonst vendored.
- inference-service-Container: `plantcv` bringt OpenCV/NumPy/Matplotlib mit → Image-Größe beachten;
  ONNX-Modell via Volume/Init-Container (nicht ins Image backen), Tag-Pin statt `:latest`
  (Muster inference-service-Pin-Falle).
- DSGVO (REQ-025): NASA POWER/ET₀ verarbeiten keine Personendaten (nur GPS-Standortbezug, bereits von
  REQ-002 abgedeckt). REQ-038 verarbeitet Nutzerfotos → Consent `plant_diagnosis` + EXIF-Strip +
  keine Bild-Persistenz (`image_deleted_at`).
- Cross-Tenant: `climate_normals`/`irrigation_demands`/`plant_diagnosis_requests` erben Tenant-Scope
  über `site_key`/`tenant_key`; Resolver-/Diagnose-Endpunkte strikt tenant-filtern (kein fail-open —
  wiederkehrender Merge-Review-Befund in diesem Projekt).
