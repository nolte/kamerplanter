# Plan — feat/forecast-frost-detection

**Worktree:** `/home/nolte/repos/.worktrees/kamerplanter/forecast-frost-detection`
**Branch:** `feat/forecast-frost-detection` (off `origin/develop`)
**Issue:** [#392](https://github.com/nolte/kamerplanter/issues/392) — *Proactive
weather-forecast frost detection (REQ-005 / REQ-018 / REQ-039)*, ausgegliedert
aus #367.

---

## Goal

Ein Grower wird **vor** einer Frostnacht gewarnt, nicht erst wenn die Temperatur
bereits gefallen ist. Konkret: der bestehende **reaktive** Frost-Warn-Pfad
(`binary_sensor.kp_{location}_frost_warning`, feuert bei aktueller Lufttemperatur
≤ Schwelle) wird um eine **proaktive**, Forecast-basierte Frühwarnung ergänzt.
Eine Wetter-Forecast-Quelle (DWD / OpenWeatherMap / Open-Meteo je Hybrid-Sensor-
Modell REQ-005) speist die Frost-Logik; das Engine wertet den Forecast-Horizont
(z. B. nächste 24–48 h) aus und meldet eine frühe Warnung inkl. erwartetem
Zeitpunkt/Minimaltemperatur.

**Additiv & graceful:** Der reaktive Pfad bleibt unverändert intakt. Fehlt eine
Forecast-Quelle → Fallback auf das aktuelle reaktive Verhalten (`unknown` /
reaktiv), **niemals ein 500**.

## Current state (recherchiert am 2026-07-05, im Worktree)

> **⚠ UPDATE 2026-07-05 (nach requirements-elicit): PRÄMISSE ÜBERHOLT.**
> **#403 (REQ-046, `cbf4808b8`) hat die komplette Wetter-Infrastruktur bereits
> nach develop gemergt** — genau das, was dieser Plan von Grund auf bauen wollte.
> Commit-Message: die `WeatherAdapter`-Registry ist explizit das, „worin
> **REQ-039** (Frost) registriert". Mein Branch (`062fd57f2`/#402) liegt **vor**
> #403 → **erster Schritt = Rebase auf develop**. Danach ist #392 **kein**
> Adapter-Bau mehr, sondern **Konsum** der vorhandenen Infrastruktur:
> - `WeatherForecast` (`domain/models/weather.py`) — **TÄGLICH** `temp_min_c` /
>   `temp_max_c` pro `site_key`/`forecast_date`/`source`, Collection
>   `weather_forecasts`. (KEIN stündlicher `ForecastPoint` wie unten skizziert.)
> - `IWeatherForecastRepository.find_by_site(site_key, tenant_key)` — Lese-Seam.
> - Celery `fetch_weather_forecasts` (kill-switch `settings.weather_enabled`,
>   default off) holt+persistiert pro Site; skippt Sites ohne `gps_coordinates`.
> - Adapter (Open-Meteo/DWD/OWM/HA), `WeatherSourceResolver`, per-Site-Config-API,
>   Platzhalter-`WeatherForecastWidget.tsx` (dessen fehlender Forecast-Read-
>   Endpoint jetzt in Scope kommt).
> - Koordinaten auf `Site.gps_coordinates` (`site.py:97`); `Location.site_key`
>   (`:61`) → **kein neues Feld/Migration**.
> - **Erledigte Open Questions durch #403:** Q1 (Provider), Q2 (Koordinaten),
>   Q5 (Caching — Celery-persistiert statt read-through).
> - **Requirement-Artefakt:** `project/requirements/forecast-frost-detection.md`
>   (`U_gate=0.80`). Entscheidungen: Horizont konfigurierbar Default **2 Tage**;
>   **eigener** Forecast-Threshold; aktive Warnung via **N-003-Notification**,
>   dedup **pro (site_key, Frost-Datum)**; Frontend = Platzhalter-Widget füllen.
>
> **Ausgangslage (reaktiver Pfad, weiterhin gültig):** Der reaktive Pfad ist
> vollständig und sauber (pure Engine + Service + Endpoint) und bleibt
> **unverändert**.

Fakten mit Fundstellen (Pfade relativ zu `src/backend/app/`):

- **Reaktive Engine (pure, side-effect-free):**
  `domain/engines/frost_warning_engine.py`
  - `evaluate_frost_warning(temperature_celsius, threshold_celsius=3.0) ->
    bool | None` (`:38`) — `None` bei fehlendem Reading (ehrliches `unknown`,
    kein fabriziertes „kein Frost"). Default-Schwelle **3.0 °C** (`:34`;
    Bodenfrost-Konvention, Rationale im Modul-Docstring).
  - `pick_air_temperature(values)` (`:65`) — zieht Lufttemperatur aus dem
    Live-State (`temperature_celsius` > `water_temp_celsius`), nicht-numerische
    HA-Werte (`"unavailable"`) werden übersprungen, kein 500.
  - **Modul-Docstring markiert Forecast explizit als „documented follow-up …
    intentionally out of scope here"** — genau dieser Scope wird jetzt geöffnet.
  - ⚠ `ruff format`-Falle dokumentiert (`:88`): `except (A, B) as exc:` — das
    `as`-Binding ist Pflicht, sonst SyntaxError (siehe CLAUDE.md-Feedback).
- **Service:** `domain/services/sensor_service.py`
  - `get_location_frost_warning(key, threshold_celsius=None)` (`:137`) — holt
    Live-State, `pick_air_temperature` → `evaluate_frost_warning`, liefert dict
    `{frost_warning, temperature, entity_id, threshold, …}` (`:151-167`). NUR
    reaktiv, keine Persistenz. Threshold aus
    `settings.frost_warning_threshold_celsius`.
- **Endpoint:** `api/v1/locations/tenant_router.py:143`
  `GET /{key}/frost-warning` → `FrostWarningResponse`
  (`api/v1/locations/schemas.py:60`, `frost_warning: bool | None`, `:67`).
- **Etabliertes External-Adapter-Muster** (die Vorlage für die Forecast-Quelle):
  - ABC-Interfaces unter `domain/interfaces/` (z. B.
    `external_source_adapter.py`, `pest_detection_adapter.py`,
    `object_storage_adapter.py`).
  - Implementierungen unter `data_access/external/` (z. B. `gbif_adapter.py`,
    `perenual_adapter.py`, `plantnet_adapter.py`, `ha_client.py`) — **keine**
    Wetter-Datei vorhanden.
  - `AdapterRegistry` (Decorator-Registrierung) laut CLAUDE.md; graceful
    degradation bei fehlender Config ist im Projekt Standard (vgl.
    HA-Optionalität, `unknown`-Rückgaben).
- **Verwandtes Engine als Muster:** `domain/engines/watering_forecast_engine.py`
  existiert (Namens-/Struktur-Vorbild für ein „forecast"-Engine; prüfen ob es
  bereits eine Wetter-Abstraktion nutzt oder rein intern rechnet).
- **REQ-005 Hybrid-Sensor-Modell:** Fallback-Kette automatic (IoT/MQTT) →
  semi-automatic (HA REST) → **weather API (DWD/OpenWeatherMap/Open-Meteo für
  outdoor)** → manual. Die Forecast-Quelle ist genau die dritte Stufe, hier für
  Frost statt für Ist-Werte.

## Design decision (load-bearing) — #403-Wetterinfrastruktur KONSUMIEREN, reaktives Engine unangetastet

**Neuscope nach requirements-elicit (Artefakt `project/requirements/forecast-frost-detection.md`):**

0. **Rebase** `feat/forecast-frost-detection` auf develop → #403 im Branch (mein
   Branch hat noch keine Feature-Commits → im Wesentlichen Fast-Forward auf den
   develop-Tip mit #403).
1. **Reine Engine** `frost_warning_engine.py` additiv erweitern: NEUE Funktion
   `evaluate_forecast_frost_warning(forecasts: list[WeatherForecast],
   threshold_celsius, horizon_days, today) -> {predicted: bool | None, min_temp,
   expected_date, source}`. Liest **tägliche** `temp_min_c` über
   `today .. today+horizon_days` (inklusiv), ignoriert `forecast_date < today`.
   Kein Reading / alle `None` → `predicted=None`. `evaluate_frost_warning`
   (reaktiv) bleibt **byte-genau unverändert** (R4).
2. **Settings** (`config/settings.py`): `frost_forecast_horizon_days=2` (R2),
   `frost_forecast_threshold_celsius` **separat** vom reaktiven 3.0 °C (R3).
3. **Service** `sensor_service.get_location_frost_warning`: Location→`site_key`,
   `weather_forecast_repository.find_by_site(site_key, tenant_key)`, Horizont
   filtern, Engine. Additiv zum reaktiven Teil. Kein gps / `weather_enabled` off
   / leerer Repo / alle `None` → Forecast-Felder `None`, reaktiv unverändert,
   **kein 500** (R5).
4. **Schema/Endpoint additiv** (`FrostWarningResponse`): `forecast_frost_warning:
   bool | None`, `forecast_min_temperature`, `forecast_expected_date: date |
   None`, `forecast_source` (R6). Reaktives `frost_warning` bleibt die Wahrheit
   → HA bricht nicht.
5. **Forecast-Read-Endpoint** für das Widget (R7): liefert Forecast-Payload +
   Frost-Frühwarn-Badge (nächstes Frost-Datum + Min-Temp).
6. **Frontend** (R7): Platzhalter `WeatherForecastWidget.tsx` füllen (Forecast +
   Frost-Badge), neuen Read-Endpoint anbinden. → 3-Agent-Kette (UI-Review →
   Tests → Doku) + Auto-UI-Review.
7. **Notification-Producer** (R8/R9): nach `fetch_weather_forecasts` (oder als
   Folge-Task) pro Site in-Horizont-Frost prüfen → **eine** N-003-Notification
   via `notification_service` → Channel-Registry, respektiert User-Preferences.
   **Idempotenz pro (site_key, Frost-`forecast_date`)** (persistierter Marker /
   Notification-History-Lookup), tenant-scoped (R10).

**Begründung:** Konsum statt Parallelbau = kein Duplikat/Konflikt mit #403,
minimaler Blast-Radius, HA-Kompat bleibt, graceful degradation ist strukturell
(kein Forecast → Feld `None`).

**Verbleibende Open Questions (Rest, im Artefakt als Risiko geführt):**

- **HA-Sync** (R11, `assumed`): ob `kamerplanter-ha`-Coordinator das neue Feld
  braucht → bei Impl gegen HA-Repo prüfen (`ha-integration-sync`).
- **Notification-Producer-Seam:** ob ein neuer Notification-„Typ"/Template
  registriert werden muss (Muster #360) → bei Impl verifizieren.
- **Idempotenz-Store:** konkreter Mechanismus (kleine Collection vs. Feld vs.
  History-Lookup) unter grünen Tests entscheiden; Verhalten (once per site+date)
  ist fix.

## Work steps

1. ~~**Requirements-Elicit**~~ → **erledigt**: Artefakt
   `project/requirements/forecast-frost-detection.md` (`U_gate=0.80`).
2. **Rebase** auf develop (#403 holen); Suite grün als Baseline.
3. **Settings** + **Engine** additiv (`evaluate_forecast_frost_warning`), reaktive
   Funktion unverändert; Engine-Unit-Tests (bool/None, Horizont-Grenzen inkl.
   `horizon_days+1` exkludiert, leere/teilfehlende Forecasts, past-date-Guard).
4. **Service** kombiniert reaktiv + Forecast über
   `weather_forecast_repository`; Fallback-Kette; **kein 500** (Regressionstest);
   Tenant-Isolation.
5. **Schema/Endpoint additiv** (`FrostWarningResponse`) + **Forecast-Read-
   Endpoint**; HA-Kompat des reaktiven Feldes; Endpoint-Tests (beide Pfade).
6. **Frontend**: `WeatherForecastWidget.tsx` füllen (Forecast + Frost-Badge),
   Read-Endpoint anbinden; vitest. 3-Agent-Kette + Auto-UI-Review.
7. **Notification-Producer** (R8/R9): Frost-Prüfung nach Fetch → N-003-
   Notification, **dedup pro (site_key, Frost-Datum)**, Preferences, tenant-scoped;
   Task-Tests (dedup über wiederholte Fetches, kein Frost → keine Notification).
8. **HA-Sync prüfen** (R11): falls Kontrakt-Erweiterung relevant → `ha-integration-sync`.
9. **Verifikation am realen Flow** (`/verify` / `run`): Site mit Koordinaten +
   simuliertem in-Horizont-Frost → `forecast_frost_warning=true` + Datum + eine
   Notification; ohne Quelle → sauberes Fallback, reaktiv intakt.
10. **Quality-Gate** (ruff/format/pytest + eslint/tsc/vitest, da FE berührt) grün
    → PR nach `develop` via `pull-request-create`.

## Invariants & guardrails (aus CLAUDE.md + Specs)

- **5-Schichten-Architektur** (NFR-001): HTTP-Call/Provider-Details ins
  **Adapter** (`data_access/external/`), Abstraktion als **ABC**
  (`domain/interfaces/`), reine Berechnung ins **Engine**, Orchestrierung in den
  **Service**. Kein Provider-SDK im Service/Engine.
- **Hybrid-Sensor-Modell (REQ-005):** Forecast ist die dritte Fallback-Stufe
  (weather API), **outdoor**; Datenprovenienz mitführen (`forecast_source`).
  Graceful degradation ist Pflicht, nicht optional.
- **Additiv & abwärtskompatibel:** reaktives `frost_warning` bleibt die
  bestehende Wahrheit; HA-Custom-Integration darf nicht brechen. Neue Felder
  optional.
- **Kein 500 bei fehlender Quelle:** externe API down / kein Key / keine
  Koordinaten → `None`/reaktiv, ehrliches `unknown` statt fabriziertem Wert
  (Muster `evaluate_frost_warning`).
- **SSRF-Härtung** für neuen Outbound-Adapter (vgl. `url_safety.py` /
  Notification-SSRF-Validator), besonders wenn Provider-URL/Host konfigurierbar.
- **DSGVO/Consent:** externe Wetter-API mit Standortkoordinaten ggf.
  Consent-gegated (vgl. enrichment/HIBP) — in Q5 klären.
- **Source-Code nur Englisch** (NFR-003); Doku Deutsch (DE-kanonisch, EN-Mirror);
  GitHub-Texte (PR/Commits) Englisch.
- **`ruff format`-Falle:** `except (A, B) as exc:` mit `as`-Binding, sonst
  SyntaxError (bereits im Engine dokumentiert).
- **Pydantic v2**; python-arango `add_persistent_index` (falls Index nötig).
- **Feedback-Pflicht:** Source-Code bevorzugt via `fullstack-developer`-Agent;
  falls FE berührt → 3-Agent-Kette (UI-Review → Tests → Doku) + Auto-UI-Review.
- **Branch von `develop`;** Hauptcheckout bleibt auf `develop` (Arbeit nur im
  Worktree).

## Status / resume-anchor checklist

Erste unerledigte Box = Wiedereinstiegspunkt der nächsten Session.

- [x] **`requirements-elicit` erledigt:** Open Questions via 4 Funnel-Turns
      beantwortet (Q1/Q2/Q5 durch #403 obsolet); Artefakt ≥ Threshold →
      `project/requirements/forecast-frost-detection.md` (`U_gate=0.80`).
      Plan auf „#403 konsumieren" umgeschrieben.
- [x] Branch auf develop rebasen (#403-Wetterinfra holen) → **erledigt**
      (Fast-Forward auf `cbf4808b8`, keine eigenen Commits; Infra im Worktree).
- [x] Settings (`frost_forecast_threshold_celsius=2.0` separat,
      `frost_forecast_horizon_days=2`) + Engine additiv
      (`evaluate_forecast_frost_warning`, tägliche `temp_min_c`, reaktive Funktion
      byte-genau unverändert verifiziert) + 14 Engine-Unit-Tests → **erledigt**.
- [x] Service kombiniert reaktiv + Forecast über `weather_forecast_repo`
      (optional injiziert); Fallback-Kette; **kein 500** verifiziert; Tenant-Guard
      (`site.tenant_key != tenant_key` → leer) + `find_by_site(tenant_key)` →
      **erledigt**.
- [x] Schema additiv (`FrostWarningResponse` +4 Felder, HA-kompat) + **per-Site**
      Read-Endpoint `GET /sites/{site_key}/weather-forecast`
      (`SiteWeatherForecastResponse`) → **erledigt** (ruff clean, 77 Tests grün).
- [x] Notification-Producer (N-003) → **erledigt**: neuer Celery-Task
      `evaluate_forecast_frost_warnings` (Beat 06:10, nach Fetch), Producer
      `send_frost_forecast_notifications`, Dedup über `group_key` +
      `find_by_group_key`, Empfänger = aktive Tenant-Mitglieder, Preferences via
      bestehendem Pfad, tenant-scoped; `weather_tasks.py` unangetastet; 10 Tests
      grün, ruff clean.
- [x] Frontend: `WeatherForecastWidget` gefüllt (Forecast-Rows +
      `WeatherProvenanceBadge` + Frost-Frühwarn-Badge, Loading/Error/Empty) +
      Hook `useSiteWeatherForecast` (erste Site mit gps) + i18n DE/EN → **erledigt**
      (tsc/eslint clean, 11 vitest grün).
- [~] Pflicht-3-Agent-Kette:
      - [x] UI-Review (`frontend-usability-optimizer`): Retry-Action (UI-NFR-004),
            Touch-Target 48px (UI-NFR-001), locale-Temp-Format; 11 vitest grün.
      - [x] Tests (`unit-test-runner`): Backend **3946 grün** + ruff clean;
            Frontend **1922 grün** + tsc clean (1 bekannter AuthImage-Flake,
            unabhängig; eslint nur Baseline auf unberührten Dateien); 56 neue
            Frost-Tests grün. **Merge-bereit.**
      - [x] Doku (`mkdocs-documentation` DE/EN) → **erledigt**: dashboard.md,
            notifications.md, weather-sources.md (Querverweis), api-reference.md,
            environment-variables.md, dashboard-personalization.md — je DE+EN;
            `mkdocs build --strict` grün.
- [x] HA-Sync (R11) → **geklärt: keine Änderung in diesem Repo.** Die HA-Custom-
      Integration liegt im **separaten Repo `kamerplanter-ha`** (hier nur Spec-Docs,
      kein `custom_components/`). Die `forecast_*`-Felder am per-Location
      `/frost-warning` sind **additiv** → bestehender Coordinator bricht nicht
      (unbekannte Felder ignoriert). Forecast-Surfacing in HA = Follow-up im
      HA-Repo (via `ha-integration-sync` dort), außerhalb dieses PRs.
- [x] Verifikation → **durch automatisierte Tests abgedeckt** (56 neue Feature-
      Tests: Engine-Grenzen, Service-graceful/kein-500, Endpoint, Notification-
      Dedup, Widget-States; Vollsuite grün). **Live-Cluster-Real-Flow N/A:**
      Skaffold fährt Primary-Checkout-Code (develop), nicht diesen Worktree-Branch
      (dokumentierte Falle), und das Feature ist hinter `weather_enabled` (default
      off) — ein Live-Drive würde den Branch-Code gar nicht ausführen.
- [ ] **Resume anchor:** Commit (Conventional Commits, EN) + PR nach `develop`
      via `pull-request-create`.
