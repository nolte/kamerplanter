# REQ-046 Umsetzungsplan — Folge-PRs (Adapter → Resolver → API → Frontend → Doku)

> Begleitdokument zu `plan.md`. Der **Adapter-Fundament-PR ist erledigt** (ABC,
> Registry, Modelle, Collections/Edges, tenant-scoped Repos, `Site.weather_source_priority`,
> 27 Tests). Dieses Dokument plant die **verbleibende** Arbeit bis zum vollen
> REQ-046-Funktionsumfang, verankert an konkreten Codestellen aus der Recherche.
> SSOT der Anforderung bleibt `spec/req/REQ-046_Wetterdienst-Datenquellen.md` (15 AC).

## 0. Ausgangslage (was das Fundament schon liefert)

Die Folge-PRs docken hieran an — **nicht neu erfinden**:

| Baustein | Ort |
|---|---|
| `WeatherAdapter`-ABC (`fetch_daily` async, `fetch_climate_normals`→None, `health_check`→NotImplementedError) | `app/domain/interfaces/weather_adapter.py` |
| `WeatherAdapterRegistry` (`@register` speichert **Klasse**, `get`/`all`/`public_sources`/`clear`) | `app/domain/services/weather_adapter_registry.py` |
| Modelle `WeatherForecast` (+`data_kind`/`is_current_conditions`/`solar_radiation_mj_m2`), `ClimateNormal` (minimal), `WeatherSourceConfig` + `WeatherSourceEntry`/`WeatherSourcePublicConfig`(`api_key_ref`)/`WeatherSourceHaConfig`/`HaSensorMapping` | `app/domain/models/weather.py` |
| Repos (tenant-scoped, `has_forecast`/`has_weather_source_config`-Edges beim Insert) | `app/data_access/arango/weather_{forecast,source_config}_repository.py` |
| DI-Provider `get_weather_forecast_repo()` / `get_weather_source_config_repo()` | `app/common/dependencies.py` |
| Collections/Edges/Indizes | `app/data_access/arango/collections.py` |

---

## 1. Zu bestätigende Design-Entscheidungen (BLOCKING vor Impl.)

D1/D3/D4 sind vom Nutzer **bestätigt** (2026-07-05). D2/D5/D6 folgen der Empfehlung
(unkritisch), bleiben aber im jeweiligen PR final zu ziehen.

- **D1 — Secret-Storage `api_key_ref` ✅ ENTSCHIEDEN: Inline-Ciphertext.** Kein „secret
  store by ref". Das etablierte Muster (OIDC, `oidc_providers/router.py:64`) speichert den
  **Ciphertext inline** in einem `*_encrypted`-Feld via `EncryptionEngine.encrypt()`.
  → `WeatherSourcePublicConfig.api_key_ref` hält den Fernet-**Ciphertext** direkt (bzw. Feld
  in `api_key_encrypted` umbenennen) — kein separater Store. Entschlüsseln nur im
  Service/Adapter zur Fetch-Zeit (`EncryptionEngine.decrypt()`), API gibt nur maskiert zurück. **AC-8.**
- **D2 — Async-httpx-Client:** Kein zentraler DI-Client vorhanden. `WeatherAdapter`
  ist async. → **Empfehlung:** HA-Client-Stil übernehmen — pro Call
  `async with httpx.AsyncClient(timeout=self._timeout) as client:` (`ha_client.py:26`).
  Registry hält Klassen; der Resolver/Task instanziiert Adapter mit ihren Deps.
  Kein neuer globaler Client-Provider (vermeidet Lifecycle-Komplexität).
- **D3 — Prioritätsliste-UI (DnD) ✅ ENTSCHIEDEN: Hoch/Runter-IconButtons.**
  `react-grid-layout` (einzige DnD-Lib) ist für 1D zu schwer (Bundle-Budget UI-NFR-003,
  `DashboardEditGrid.tsx:8` einziger statischer Importeur). → MVP mit **Hoch/Runter-IconButtons**
  (bestehendes Tabellen-Icon-Muster), kein neues DnD. Echte Drag-Reihenfolge als
  spätere Kür (dnd-kit) — bewusste separate Dependency-Entscheidung.
- **D4 — Modul-Gating ✅ ENTSCHIEDEN: kein Modul-Gate.** Kein `weather`-`ModuleKey`
  (`moduleCatalog.ts:15`), Wetter ist laut REQ-005-Invariante **keine** Smart-Home-Funktion.
  → Der Wetterquelle-Abschnitt erscheint für Sites mit `type ∈ {outdoor, greenhouse}`
  **und** gesetzten GPS (Filter neu, `SiteDetailPage` hat ihn noch nicht). Nur die
  **HA-Quellen-Option** wird bei fehlendem HA-Token deaktiviert.
- **D5 — Default-Quelle & Auto-Provisioning:** Spec §5 `WEATHER_DEFAULT_PUBLIC_SOURCE`
  (Default `open-meteo`). → **Empfehlung:** Resolver fällt bei **fehlender** Config auf
  die Default-Public-Quelle zurück (kein Zwangs-Seed nötig); optional legt der
  PUT-Endpunkt beim ersten Speichern die Config an. So ist PR-2 ohne UI testbar. **AC-9.**
- **D6 — Auth-Guard:** `require_permission`/Permission-Matrix ist laut Docstring
  (`core/permissions.py:196`) noch nicht flächendeckend verdrahtet. → **Empfehlung:**
  Reads `Depends(get_current_tenant)`, Writes `Depends(require_tenant_role(TenantRole.GROWER))`
  (`app/common/auth.py:40,89`). Optionaler `ResourceType.WEATHER_SOURCE`-Eintrag als Kür.

---

## 2. PR-Schnitt & Reihenfolge

```
PR-2  Öffentliche Adapter + Resolver + Celery        (Backend, kein UI/API)      ← D2, D5
PR-3  HA-Wetteradapter + HA-Client-Erweiterung        (Backend)                   ← D2
PR-4  API-Endpunkte + Fernet-Secret-Handling          (Backend)                   ← D1, D6
PR-5  Frontend-Konfigurator + Dashboard-Widget        (Frontend) + 3-Agent-Kette  ← D3, D4
PR-6  Doku (MkDocs) + NOTICE-Attribution + Security-Review
```

Jeder PR forkt von `develop` (Feedback), grün durch `static`-Gate, danach automerge.
PR-2/3/4 sind rein backend und unabhängig reviewbar; PR-5 setzt PR-4 (Endpunkte) voraus.

---

## 3. PR-2 — Öffentliche Adapter + Resolver + Celery

**Ziel:** Für eine Outdoor-/Greenhouse-Site mit GPS werden real Tageswerte gezogen
und als `:WeatherForecast` geschrieben; Prioritäts-/Fallback-Kette funktioniert.
**Deckt:** AC-2, AC-6, AC-9 (öffentlich), AC-13, AC-15 (Attribution-Konstanten).

### Neue Dateien
- `app/data_access/external/open_meteo_weather_adapter.py` — `OpenMeteoWeatherAdapter`
  (`source_name="open-meteo"`, `kind="public"`, kein Key). Nach REQ-046 §3.3: `daily=`-Params,
  `wind_speed_unit=kmh`, `timezone=auto`, `forecast_days=7`; `_map()`→`WeatherForecast(source=..., data_kind="forecast")`.
  Per-Call `async with httpx.AsyncClient` (D2). Base-URL aus Settings (überschreibbar).
- `app/data_access/external/dwd_weather_adapter.py` — `DwdWeatherAdapter`
  (`source_name="dwd"`, kein Key) über Brightsky-JSON (`api.brightsky.dev`, WMO-Codes vorhanden),
  Attribution DWD GeoNutzV.
- `app/data_access/external/openweathermap_weather_adapter.py` — `OpenWeatherMapWeatherAdapter`
  (`source_name="openweathermap"`, `requires_api_key=True`). Key wird zur Fetch-Zeit aus
  `config.api_key_ref` via `EncryptionEngine.decrypt()` gelesen (D1) — **nie** aus Klartext-Config.
- `app/domain/services/weather_source_resolver.py` — `WeatherSourceResolver` nach §3.5:
  läuft `cfg.sources` (enabled, priorisiert) durch, `Registry.get(entry.source_name)` →
  Adapter mit passenden Deps bauen, `fetch_daily(lat, lon, config=entry.config)`, erste
  nicht-leere Antwort gewinnt; fängt `(httpx.HTTPError, httpx.TimeoutException)` → nächste Quelle.
  Fehlt Config → Default-Public-Quelle (D5). Gibt `[]` wenn keine Quelle liefert.
- `app/tasks/weather_tasks.py` — `fetch_weather_forecasts` (Celery). Muster:
  `sensor_ingestion_tasks.py:17-38` — `get_weather_source_config_repo()`/`get_weather_forecast_repo()`
  aus `app.common.dependencies` **im Task-Body** (kein `Depends`); cross-tenant über
  `weather_source_configs` iterieren (`repo._db.aql.execute`), pro Site Resolver aufrufen,
  Ergebnisse `upsert_daily`. `@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)`.

### Änderungen
- `app/tasks/__init__.py` — `"app.tasks.weather_tasks"` in `conf.update(include=[...])`
  (:11-29); Beat-Eintrag `"weather-fetch-daily": {"task": "...fetch_weather_forecasts", "schedule": crontab(hour=6, minute=0)}` (:35-130).
  Kill-Switch-Muster (:134): `if settings.weather_enabled: conf.beat_schedule["weather-fetch-daily"] = {...}`.
- `app/config/settings.py` — nach HA-Block (:177): `weather_enabled: bool = False`,
  `weather_default_public_source: str = "open-meteo"`, `open_meteo_base_url`, `dwd_base_url`,
  `openweathermap_base_url`, `openweathermap_enabled`/`dwd_enabled`/`open_meteo_enabled: bool`,
  `weather_fetch_timeout_s: int = 20`, `weather_max_rps_per_provider: float = 1.0` (§5).
- `app/main.py` bzw. Adapter-Import-Seite — sicherstellen, dass die drei Adapter-Module
  **importiert** werden, damit `@WeatherAdapterRegistry.register` greift (analog wie
  `local_pest_adapters`/`plantnet` registriert werden — Import-Ort prüfen).
- Attribution-Konstanten (`DWD GeoNutzV`, `Open-Meteo CC-BY-4.0`, `OWM`) zentral als Modul-Konstante
  (Verbrauch in UI/NOTICE später).

### Tests
- Adapter-`_map()` gegen ge-mockte Provider-JSON-Fixtures (`temp_min/max`, `precipitation`,
  `wind_gust`, WMO-Code korrekt gemappt; `-999`/`null`→`None`).
- Resolver: (a) erste Quelle liefert → gewinnt; (b) erste 5xx/Timeout → Fallback auf zweite;
  (c) alle leer → `[]`; (d) keine Config → Default-Quelle. Registry mit Dummy-Adaptern + `clear()`.
- Task: cross-tenant-Iteration schreibt korrekt `source`/`data_kind`; `weather_enabled=False` → no-op.

### Risiken
- ruff-Falle: `except (httpx.HTTPError, httpx.TimeoutException) as exc:` — **immer mit `as exc`**
  (Projekt-Feedback: `ruff format` zerlegt `as`-lose Tuple-except zu SyntaxError).
- Rate-Limit/Timeout je Provider respektieren (`weather_max_rps_per_provider`).

---

## 4. PR-3 — HA-Wetteradapter + HA-Client-Erweiterung

**Ziel:** Home Assistant als Wetterquelle in beiden Modi. **Deckt:** AC-3, AC-4, AC-10, AC-12.

### Neue Dateien
- `app/data_access/external/home_assistant_weather_adapter.py` — `HomeAssistantWeatherAdapter`
  (`source_name="ha_weather"`, `kind="home_assistant"`, `requires_api_key=False`) nach §3.4.
  Konstruktor nimmt `HomeAssistantClient`. `_from_weather_entity()` (Modus A) liest
  `attributes.forecast[]` → Tages-`WeatherForecast(data_kind="forecast")`;
  `_from_sensor_mapping()` (Modus B) liest gemappte `sensor.*` → **ein** Ist-Datensatz
  `is_current_conditions=True, data_kind="observed"`, ungemappte/`unavailable`→`None`.

### Änderungen
- `app/data_access/external/ha_client.py` — **zwei neue Methoden** (Lücke, s. Recherche):
  - `list_weather_entities() -> list[dict]` — `GET /api/states`, Filter `weather.` (bestehendes
    `list_sensor_entities():77` filtert hart `sensor.` — nicht wiederverwendbar).
  - `get_state_attributes(entity_id) -> dict | None` — roher `attributes`-Block, **ohne** die
    numerische Kollaps-Logik von `get_state():99` (die `attributes.forecast` verwerfen würde).
  SSRF-Guard/`validate_ha_url` bleibt unangetastet (AC-12). Keine neue Ziel-URL.
- `WeatherSourceResolver` (aus PR-2) — HA-Zweig ergänzen: baut `HomeAssistantWeatherAdapter`
  mit `get_ha_client()` (`dependencies.py:764`); `get_ha_client()==None` → Quelle „nicht verfügbar",
  Fallback auf nächste (Degradation, nie harter Fehler — REQ-005-Invariante). **AC-9.**
- **`source`-Provenance `ha_weather`:** In REQ-005 ist `SourceType` ein Literal; im Code ist
  `WeatherForecast.source` ein freier `str` — der Adapter schreibt schlicht `"ha_weather"`.
  Kein Enum-Refactor nötig. (Falls ein zentrales Quality-Score-Mapping existiert:
  `ha_weather=0.9` ergänzen, §2.3.)
- **Warn-Ausschluss (AC-10):** HA-Ist-Werte (`is_current_conditions=True`) dürfen **keine**
  Frost-/Regen-/Sturm-Frühwarnung auslösen — der (spätere REQ-005-)Warn-Pfad muss auf
  `is_current_conditions=False` filtern. Hier als Guard im Task/Warn-Konsumenten dokumentieren.

### Tests
- Modus A: gemockte `weather.*`-`attributes.forecast[]` → N Tages-Records, korrektes Feld-Mapping,
  `condition`→WMO.
- Modus B: gemappte `sensor.*` → genau 1 Ist-Datensatz; `unavailable`/`unknown`/ungemappt→`None`;
  `data_kind="observed"`, `is_current_conditions=True`.
- Resolver-Degradation: `get_ha_client()==None` → nächste Quelle.

---

## 5. PR-4 — API-Endpunkte + Fernet-Secret-Handling

**Ziel:** UI-fähige tenant-scoped Endpunkte inkl. Verbindungstest & sicherem Key-Storage.
**Deckt:** AC-1 (Registry sichtbar), AC-5 (Backend), AC-7, AC-8, AC-11.

### Neue Dateien
- `app/api/v1/tenant_scoped/weather/tenant_router.py` — `router = APIRouter(prefix="/sites/{site_key}/weather-source", tags=["weather"])`
  (Muster `tasks/tenant_router.py:43`; kein `/t`-Prefix, kommt vom Parent). Endpunkte (§4.3):
  | Methode & Pfad | Guard | Zweck |
  |---|---|---|
  | `GET  /sites/{site_key}/weather-source` | `get_current_tenant` | Config lesen |
  | `PUT  /sites/{site_key}/weather-source` | `require_tenant_role(GROWER)` | Config speichern (§4.1) |
  | `GET  /weather-sources/available` | `get_current_tenant` | Registry-Quellen + HA-Token-Status |
  | `POST /sites/{site_key}/weather-sources/test` | `require_tenant_role(GROWER)` | health_check + Werte-Vorschau (ungespeichert) |
  | `GET  /ha/weather-entities` | `get_current_tenant` | HA `weather.*` (Modus A) |
  | `GET  /ha/sensor-entities` | `get_current_tenant` | HA `sensor.*` (Modus B, `list_sensor_entities`) |
  Idiom: `ctx: TenantContext = Depends(get_current_tenant)` → `tenant_key=ctx.tenant_key`
  an Repo/Service; beim Schreiben `WeatherSourceConfig(**body, tenant_key=ctx.tenant_key)`.
- `app/domain/services/weather_source_service.py` (optional, wenn Router-Logik wächst):
  kapselt Fernet-Encrypt beim PUT, Maskierung beim GET, Site-Ownership-Check, `health_check`-Dispatch.

### Änderungen
- `app/api/v1/tenant_scoped/router.py` — `tenant_weather_router` via `include_router` mounten (:53-84).
- **Fernet (D1, AC-8):** Beim PUT den Klartext-OWM-Key `encryption.encrypt(...)` (Provider
  `get_encryption_engine()`, `dependencies.py:482`), Ciphertext in `api_key_ref` ablegen;
  Klartext **nie** persistieren. GET maskiert (`"••••"`, nie Klartext). Vorbild `oidc_providers/router.py:64,105`.
- **Tenant-Isolation (AC-11):** `upsert` wirft bereits bei leerem/abweichendem `tenant_key`
  (Fundament). Router prüft zusätzlich, dass `site_key` zur Tenant-Site gehört (Site-Repo-Read
  mit `tenant_key`); fremde Site → 403/422. Cross-Tenant-Edges ausgeschlossen.
- **Verbindungstest (AC-7):** `test`-Endpunkt baut Adapter aus dem **Request-Body** (ungespeichert),
  ruft `health_check(config=...)` + eine `fetch_daily`-Vorschau; verständlicher Fehler statt 500;
  speichert nichts. `health_check` in den 4 Adaptern konkret implementieren (Default ist `NotImplementedError`).
- **Pydantic-422-Falle** (Projekt-Erfahrung): rohe `pydantic.ValidationError` im Router-Body →
  500 statt 422, wenn Handler nur `RequestValidationError` fängt. Request-Schemas als FastAPI-Body-Modelle,
  nicht manuelles `Model(**body)` in try/except ohne Mapping.

### Tests
- Endpunkt-Tests (tenant-scoped Fixture): PUT→GET round-trip; OWM-Key wird verschlüsselt gespeichert
  und maskiert zurückgegeben (nie Klartext, AC-8); fremde Site → 403 (AC-11); `available` listet
  Registry-Public-Quellen + HA nur mit Token; `test` gültig→Vorschau, ungültig→verständlicher Fehler (AC-7).

---

## 6. PR-5 — Frontend-Konfigurator + Dashboard-Widget

**Ziel:** Nutzer wählt/konfiguriert Wetterquellen je Standort. **Deckt:** AC-5, AC-14, AC-10 (UI-Badges).
Mobile-First, beschreibende Texte + Fachbegriff-Erklärungen (Feedback). Danach 3-Agent-Kette.

### Neue Dateien
- `src/frontend/src/api/endpoints/weatherSources.ts` — analog `sites.ts:19`, **`tenantClient`**
  (Interceptor setzt `/t/{slug}` automatisch, `client.ts:60`): `getWeatherSource(siteKey)`,
  `putWeatherSource(siteKey, cfg)`, `getAvailableSources()`, `testSource(siteKey, entry)`,
  `listHaWeatherEntities()`, `listHaSensorEntities()`. Typen in `api/types.ts`.
- `src/frontend/src/pages/standorte/WeatherSourceSection.tsx` — eigenständige Section
  (Muster `LocationTreeSection`/`SiteRunsSection`, nur `siteKey`-Prop, lädt selbst; kein Redux-Slice
  nötig — wie die Sensoren-Sektion mit lokalem `useState`, `SiteDetailPage.tsx:63`). Enthält:
  - Prioritätsliste mit **Hoch/Runter-IconButtons** (D3), `kind`-Badge, Enable-Toggle, Zahnrad, Entfernen.
  - „Quelle hinzufügen"-Dialog mit **Zwei-Wege-Umschaltung** (Kern-UX §4.1): Öffentlicher Dienst
    (Provider-Select; OWM→maskiertes Key-Feld) **vs.** Home Assistant (Modus A `weather.*`-Autocomplete /
    Modus B Feld-für-Feld `sensor.*`-Picker). HA-Optionen **deaktiviert mit Hinweis** ohne HA-Token
    (Fallback-Muster `SensorCreateDialog.tsx:103` — leere Entity-Liste → deaktivieren/ausblenden;
    ein echtes `ha_token_set`-Flag fehlt, ggf. via `available`-Endpunkt liefern).
  - „Quelle testen"-Button → `testSource` → Erreichbarkeit + Werte-Vorschau vor dem Speichern (AC-7).
- `src/frontend/src/components/dashboard/widgets/WeatherForecastWidget.tsx` — bespoke Widget
  (Platzhalter existiert: `dashboardWidgetCatalog.ts:104` `weather_forecast`, `hasConfig=true`;
  `widgetRegistry.ts:33` fällt auf `GenericWidget` zurück → hier `lazy(() => import('./widgets/WeatherForecastWidget'))`
  eintragen, Muster `QuickActionsWidget`). Zeigt Tageswerte + **Quellen-Badge** (`source`) +
  `Ist-Wert`/`Reanalyse`-Label aus `data_kind`/`is_current_conditions` (AC-10) + „Fallback aktiv"-Hinweis.

### Änderungen
- `src/frontend/src/pages/standorte/SiteDetailPage.tsx` — `<WeatherSourceSection siteKey={key} />`
  einhängen (nahe :295), **konditional** auf `current.type ∈ {outdoor, greenhouse}` && `current.gps_coordinates`
  (Filter neu bauen, `current` verfügbar :60; Typen `types.ts:487-502`). (D4 — kein Modul-Gate.)
- i18n: **beide** `src/frontend/src/i18n/locales/{de,en}/translation.json` an gleicher Stelle:
  `pages.weatherSource.*`, `enums.weatherSource.*` (Quellen), `enums.weatherSourceKind.*`
  (`public`/`home_assistant`), `enums.haWeatherMode.*` (`weather_entity`/`sensor_mapping`),
  `dashboard.widgets.weather_forecast.*`. DE = Default/Fallback (AC-14). Single namespace `translation`.
- Custom Hooks mit Objekt/Array-Return via `useMemo` stabilisieren (Projektkonvention).

### 3-Agent-Kette nach Impl. (Pflicht-Feedback)
`frontend-usability-optimizer`/UI-Review → `unit-test-runner` (vitest) → `mkdocs-documentation`.

---

## 7. PR-6 — Doku + NOTICE + Security-Review

- **NOTICE / Attribution (AC-15):** DWD GeoNutzV, Open-Meteo CC-BY-4.0, OWM-Bedingungen,
  NASA POWER (REQ-041) in NOTICE-Datei + UI-Wetterabschnitt.
- **MkDocs (DOCS.md-Konventionen, du-Anrede, REQ-IDs nur in HTML-Kommentaren):**
  Nutzer-Guide „Wetterquelle je Standort einrichten" (öffentlich vs. HA, Verbindungstest);
  technische Referenz (Datenmodell/Collections, Registry-Ownership REQ-041/039 registrieren hier).
- **`code-security-reviewer`** auf `weather_source_config_repository.py`,
  `weather_forecast_repository.py`, den neuen tenant-Router und das Fernet-Handling
  (Tenant-Isolation, parametrisierte AQL, kein Key-Leak).
- **DSGVO (REQ-025):** öffentliche Adapter übermitteln nur GPS; OWM/US-Dienste als
  Drittland-Übermittlung im Verarbeitungsverzeichnis führen; HA spricht nur die eigene Instanz.

---

## 8. Querschnitts-Invarianten (aus CLAUDE.md + Specs)

- Source code **English only** (NFR-003); Doku/Spec DE; i18n DE-Default + EN.
- 5-Layer (NFR-001): API → Service → Engine/Adapter → Repository → ArangoDB.
- HA **strikt optional** — alle Wetterfunktionen mit rein öffentlichen Diensten nutzbar,
  Fallback-Degradation nie harter Fehler; Wetter ≠ „Smart-Home-Funktion" (unabhängig `smart_home_enabled`).
- SSRF: `validate_ha_url` unangetastet; öffentliche Adapter nur fest verdrahtete Provider-URLs.
- Multi-Tenancy: alle Reads/Writes `tenant_key`-gefiltert; Cross-Tenant-Edges verboten.
- `ruff`-Falle: Multi-Exception-`except` immer mit `as exc`.
- Provenance immer tracken (`source`, `data_kind`, `is_current_conditions`).

## 9. Akzeptanzkriterien → PR-Zuordnung

| AC | Thema | PR |
|----|-------|----|
| AC-1 | Registry als SSOT (NASA POWER registriert hier) | Fundament + PR-4 (sichtbar via `available`); REQ-041-Adapter = eigener Follow-up |
| AC-2 | Öffentliche Adapter schreiben `:WeatherForecast` | PR-2 |
| AC-3 / AC-4 | HA Modus A / Modus B | PR-3 |
| AC-5 | Nutzerwahl öffentlich vs. HA in UI | PR-4 (Backend) + PR-5 (UI) |
| AC-6 | Priorität & Fallback | PR-2 (Resolver) + PR-3 (HA im Resolver) |
| AC-7 | Verbindungstest | PR-4 + PR-5 |
| AC-8 | Secret-Sicherheit (Fernet) | PR-4 (D1) |
| AC-9 | HA optional / voll öffentlich nutzbar | PR-2 (Default) + PR-3 (Degradation) |
| AC-10 | Provenance & Warn-Ausschluss + UI-Badges | PR-3 (Guard) + PR-5 (Badges) |
| AC-11 | Tenant-Isolation | Fundament + PR-4 |
| AC-12 | SSRF | PR-3 |
| AC-13 | Migration/additiv | Fundament (erledigt) |
| AC-14 | i18n DE/EN | PR-5 |
| AC-15 | Attribution NOTICE + UI | PR-2 (Konstanten) + PR-6 |

## 10. Offene / abhängige Punkte außerhalb REQ-046-Kern

- **REQ-041** `NasaPowerWeatherAdapter` + volles `:ClimateNormal`-Schema registrieren sich in
  der Foundation-Registry — eigener REQ-041-PR, nicht Teil dieser REQ-046-Kette.
- **REQ-039** `OpenMeteoClimateNormalAdapter` registriert analog — REQ-039-PR.
- **REQ-005-Warn-Pfad** (`check_frost_warnings`/`adjust_watering_reminders`) ist im Code noch
  gar nicht implementiert; REQ-046 liefert die Datenquelle, der Warn-Konsument bleibt REQ-005.
  AC-10 (kein Frühwarn-Trigger für Ist-Werte) ist erst mit dem REQ-005-Warn-Pfad voll prüfbar.
