# Plan: Wetterdienst-Datenquellen-Integration (REQ-046)

Branch: `feat/weather-service-integration`
Slug: `weather-service-integration`
Worktree: `~/repos/.worktrees/kamerplanter/weather-service-integration`

## Goal

Der Nutzer kann pro Freiland-/Gewächshaus-Standort **selbst wählen und in der UI
konfigurieren**, woher Wetterdaten stammen: entweder ein **öffentlicher
Wetterdienst** (DWD / OpenWeatherMap / Open-Meteo) oder **Sensoren aus seiner
Home-Assistant-Installation** (native `weather.*`-Entität ODER einzeln gemappte
`sensor.*`-Entitäten). Mehrere Quellen sind priorisierbar (Fallback-Kette).

Erster und aktuell einziger Deliverable dieses Schrittes: das **Anforderungs-
dokument `spec/req/REQ-046_Wetterdienst-Datenquellen.md`** als verbindliche
Implementierungsgrundlage. Die eigentliche Backend-/Frontend-Implementierung
ist Folgearbeit (eigene Work-Steps unten, aber nach dem Dokument).

## Current state (recherchiert)

- **Spezifiziert, aber NICHT im Code umgesetzt:** REQ-005 §"Wetter-Integration
  (Freiland)" definiert `source='weather_api'`, `:WeatherForecast` /
  `weather_forecasts`, `has_forecast`-Edge, Celery `fetch_weather_forecasts`,
  Frost-/Regen-Warnungen, Quality-Score `weather_api=0.7`. Adapter selbst nur als
  AC "mindestens ein Adapter" gefordert — kein Wetter-Code in `src/backend/app/`.
- **REQ-041 (NASA POWER)** hat `WeatherAdapter`-ABC, `WeatherAdapterRegistry`,
  `Site.weather_source_priority`, `data_kind`, `solar_radiation_mj_m2`,
  `:ClimateNormal` und eine Quellen-Prioritäts-UI (§4) **auf Papier** vorweg-
  genommen — ebenfalls nichts davon im Code.
- **REQ-039 (Winterhärte)** nutzt dasselbe Adapter-Muster (`HardinessZoneSource-
  Adapter`, `OpenMeteoClimateNormalAdapter`), teilt DWD/Open-Meteo-Quellen +
  Attributionspflichten (DWD GeoNutzV, Open-Meteo CC-BY-4.0).
- **REQ-037 (ET)** konsumiert `weather_forecasts` + `solar_radiation_mj_m2`.
- **Vorhandene Bausteine (Blaupause):**
  - `domain/interfaces/external_source_adapter.py::ExternalSourceAdapter` (ABC)
  - `domain/services/adapter_registry.py::AdapterRegistry` (`@register`-Dekorator)
  - Priorisierende Registry-Vorlagen: `identification_registry.py`,
    `pest_detection_registry.py` (`PRIMARY_ADAPTER` + "nur konfigurierte").
  - `data_access/external/ha_client.py::HomeAssistantClient` mit
    `list_sensor_entities()`, `get_state(entity_id)`, SSRF-Guard `validate_ha_url`.
  - `domain/models/site.py::Site` (`type`, `gps_coordinates`, `climate_zone` —
    KEIN `weather_source_priority`).
  - `domain/models/observation.py::SensorReading.source` (freier String, nicht
    das REQ-005-Literal-Enum).
- **Frontend:** keine Wetter-/Datenquellen-UI. `SiteDetailPage.tsx` kennt nur
  `climate_zone`-String. HA-Config existiert nur als Publish-Richtung
  (`HaPublishSettingsTab.tsx`) + Sensor-Anlage (`SensorCreateDialog.tsx` mit
  `ha_entity_id`). Dashboard-Widget `weather_forecast` ist reiner Platzhalter.
- Höchste vergebene REQ-Nummer: **045** → neue Nummer **046**.

## Load-bearing design decision

**REQ-046 wird die konsolidierte SSOT der Wetter-Datenquellen-Schicht.** Es
besitzt die `WeatherAdapter`-ABC, `WeatherAdapterRegistry`,
`Site.weather_source_priority` und die konkreten Adapter DWD / OpenWeatherMap /
Open-Meteo **sowie** den neuen `HomeAssistantWeatherAdapter` und die
Konfigurations-UI. REQ-041 (NASA POWER) und REQ-039 (Winterhärte) registrieren
ihre Spezial-Adapter nur in dieser Registry. REQ-005 bleibt SSOT für Sensorik +
Basis-Datenmodell `:WeatherForecast`.

**HA-als-Wetterquelle: beide Varianten** — (A) native HA `weather.*`-Entität
(liefert `forecast[]`+`current`) und (B) Mapping einzelner `sensor.*`-Entitäten
auf die Wetterfelder.

### Beim Schreiben geklärte / offene Fragen

- [x] Neues REQ-046 statt Inline-Ausbau von REQ-005 (Dokumentgröße + REQ-041-Präzedenz).
- [x] Ownership der Registry/Priorität → REQ-046 (User bestätigt "Fundament konsolidieren").
- [x] HA-Quelle → beide Varianten (User bestätigt "Beides").
- [ ] **Vor Backend-Impl. bestätigen:** Übernimmt REQ-046 die Felder
  `data_kind` / `solar_radiation_mj_m2` in `:WeatherForecast` selbst, oder bleiben
  sie REQ-041? (Vorschlag: Felder in REQ-046 additiv am Modell dokumentieren,
  Befüllung bleibt quellenspezifisch je Adapter.)
- [ ] **Vor UI-Impl. bestätigen:** Wird die Quellen-Konfiguration pro Standort
  ODER pro Standort+Parameter granular? (Vorschlag: pro Standort, mit optionalem
  Per-Parameter-Override als AC-Kann.)
- [ ] Sicherer OWM-API-Key-Store: Fernet-Pattern wie bestehende Secrets bestätigen.

## Work steps (ordered)

1. REQ-046-Dokument schreiben (dieser Schritt — der eigentliche Auftrag).
2. `spec/req/README.md` Integrations-Abschnitt um REQ-046 ergänzen.
3. Rück-Querverweise in REQ-005 §Wetter + REQ-041 (Registry-Ownership) + REQ-039.
4. (Folge-PR) Backend: `WeatherAdapter`-ABC + `WeatherAdapterRegistry`,
   `:WeatherForecast`-Modell/Repo, `Site.weather_source_priority`.
5. (Folge-PR) Adapter DWD / OpenWeatherMap / Open-Meteo + `HomeAssistantWeather-
   Adapter` (nutzt `ha_client`), Celery `fetch_weather_forecasts`.
6. (Folge-PR) Frontend: "Klima/Wetter am Standort"-Tab in `SiteDetailPage`,
   Quellen-Prioritätsliste + HA-Entity-Picker, Verbindungstest, i18n.
7. Nach jeder Impl.-Welle: 3-Agent-Kette (UI-Review → Tests → Doku) gem. Feedback.

## Invariants / guardrails (aus CLAUDE.md + Specs)

- Source code English only (NFR-003); Doku/Spec Deutsch; i18n DE-Default + EN.
- 5-Layer-Architektur (NFR-001): API → Service → Engine → Repository → ArangoDB.
- Adapter-Muster: ABC in `domain/interfaces/`, Impl in `data_access/external/`,
  Registrierung via Registry-Dekorator (wie `AdapterRegistry`).
- SSRF-Schutz für HA-URL (`validate_ha_url`) und Wetter-API-URLs verbindlich.
- HA-Abhängigkeit MUSS optional bleiben; öffentliche Dienste ohne HA nutzbar,
  Fallback bis auf `manual`. Wetter gilt NICHT als "Smart-Home-Funktion"
  (unabhängig von `smart_home_enabled`, REQ-005).
- Attributionspflichten: DWD GeoNutzV, Open-Meteo CC-BY-4.0 → NOTICE.
- Provenance immer tracken (`source`-Enum um `ha_weather` erweitern).
- Multi-Tenancy: `weather_source_config` tenant-scoped, Cross-Tenant-Edges prüfen.
- Custom Hooks mit Objekt/Array-Return via `useMemo` stabilisieren.
- Mobile-First; beschreibende Texte + Fachbegriff-Erklärungen in der UI.

## Ausführlicher Umsetzungsplan der Folge-PRs

Siehe **`implementation-plan.md`** (Begleitdokument): PR-Schnitt PR-2..PR-6
(öffentliche Adapter+Resolver+Celery → HA-Adapter → API+Fernet → Frontend →
Doku/Security), je mit konkreten Datei:Zeile-Ankern, Tests, AC-Zuordnung und
6 zu bestätigenden Design-Entscheidungen (D1 Secret-Storage, D2 async-httpx,
D3 DnD, D4 Modul-Gating, D5 Default-Quelle, D6 Auth-Guard).

## Status / resume anchor

- [x] Worktree angelegt, Recherche abgeschlossen, Design-Entscheidungen geklärt.
- [x] REQ-046-Dokument geschrieben (`spec/req/REQ-046_Wetterdienst-Datenquellen.md`).
- [x] README (`spec/req/README.md`) + Rück-Querverweise in REQ-005/041/039 ergänzt (Registry-Ownership nach REQ-046 umgehängt).
- [x] Backend-Adapter-Fundament implementiert: `WeatherAdapter`-ABC + `WeatherAdapterRegistry` (speichert Klasse, §3.2), `domain/models/weather.py` (`WeatherForecast` inkl. `data_kind`/`is_current_conditions`, minimal `ClimateNormal`, `WeatherSourceConfig` + eingebettete Konfig-Modelle), Collections/Edges (`weather_forecasts`/`weather_source_configs`/`has_forecast`/`has_weather_source_config`) + Indizes, `Site.weather_source_priority`, tenant-scoped Repos (Interface + Arango) + DI-Verdrahtung, 27 neue Unit-Tests. Verifiziert: ruff clean, 311 Tests grün. `has_forecast`/`has_weather_source_config`-Edges werden beim Insert geschrieben (kein Follow-up).
- [x] **Welle 1 (PR-2+PR-3):** Adapter open-meteo/dwd/openweathermap/ha_weather + HA-Client-Erweiterung (`list_weather_entities`/`get_state_attributes`) + `WeatherSourceResolver` + Celery `fetch_weather_forecasts` (Kill-Switch `weather_enabled`) + 10 Settings + `WEATHER_ATTRIBUTIONS`. Verifiziert: ruff clean, Registry {dwd,ha_weather,open-meteo,openweathermap}, 189 Tests grün.
- [x] **Welle 2 (PR-4):** 6 tenant-scoped Endpunkte (§4.3) + Fernet-Inline-Ciphertext (D1) + Verbindungstest (ungespeicherter Body) + Site-Ownership-Guard + Maskierung. Verifiziert: ruff clean, 6 Routen registriert, 26 Tests grün.
- [x] **Welle 3 (PR-5):** Frontend-Konfigurator (Zwei-Wege-Dialog, HA-Picker, Hoch/Runter-Priorität D3, „Quelle testen", `WeatherProvenanceBadge`, Widget-Platzhalter), kein Modul-Gate (D4), i18n DE+EN. Verifiziert: tsc grün, 13 Tests grün.
- [x] **Welle 4 — UI-Review** (`frontend-usability-optimizer`): Touch-Targets 48px, LoadingSkeleton, Tooltips für data_kind/Priorität, Sensor-Mapping in 3 Gruppen, Empty-States, GPS-fehlt-Hinweis. tsc/eslint/13 Tests grün.
- [x] **Welle 4 — Security-Review** (`code-security-reviewer`): 1 Critical **SEC-001** (OWM-Key leakt via httpx-Fehlerstring) → **behoben** (Redaction im Adapter, deckt Log/Response/Health) + Härtungen SEC-002 (Task-Tenant-Reverify), SEC-003 (HA-entity_id-Guard Adapter+Schema), SEC-004 (max_length). 3 neue Regressionstests. SEC-005 = bewusstes Design (globale HA-Instanz). Verifiziert: 246 Wetter-Tests grün.
- [x] **Welle 4 — NOTICE** (`NOTICE.md`, AC-15) + UI-Attribution (i18n `pages.weatherSource.attribution`) vorhanden.
- [x] **Welle 4 — Voll-Suite Merge-Gate:** Backend **3846 passed** / 1 skipped, Frontend **1916 passed** (194 Dateien). Keine Regression.
- [x] **Welle 4 — MkDocs-Doku** (`mkdocs-documentation`): neue Seite `user-guide/weather-sources.md` (DE+EN), Nav eingehängt, Drift in `sensors.md` korrigiert, `mkdocs build --strict` exit 0.
- [ ] **← NÄCHSTER SCHRITT:** PR nach develop (pull-request-create) — wartet auf Nutzer-Freigabe.
