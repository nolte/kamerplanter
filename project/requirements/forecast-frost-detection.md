# Requirements — Proactive weather-forecast frost detection (Issue #392)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back /
authoritative user answer.
-->

## Bounded context

- **What:** Add a **proactive** frost early-warning to the existing **reactive**
  frost path. A grower is warned *before* a frost night, not once the air
  temperature has already fallen. Built **on top of the already-merged REQ-046
  weather infrastructure (#403, `cbf4808b8`)** — not a from-scratch adapter
  build. This branch (`feat/forecast-frost-detection`, base `062fd57f2`/#402) is
  **rebased onto develop** to consume #403's `WeatherForecast` model,
  `IWeatherForecastRepository`, resolver, adapters, per-site config, and the
  Celery fetch task.
- **For whom:** Outdoor growers (the frost path is outdoor per REQ-005 hybrid
  sensorics); the Home Assistant coordinator (reads the endpoint); the tenant's
  Celery scheduler (fetch + evaluation).
- **Explicitly out of scope:** building weather adapters / a provider registry /
  a coordinate model / request-time caching (all delivered by #403); hourly
  forecast granularity (the shared `WeatherForecast` is **daily** min/max);
  owning the REQ-046 weather-source configuration UI (only *filling* its
  placeholder `WeatherForecastWidget`); reworking the reactive path
  (`evaluate_frost_warning` stays byte-for-byte unchanged).

**Foundation verified in code (self-consistency `k = 2`: read both the #403 diff
and the on-disk reactive path):**

- `WeatherForecast` (`domain/models/weather.py`, #403) — **daily** record:
  `site_key`, `forecast_date`, `temp_min_c | None`, `temp_max_c | None`,
  `source`, `data_kind="forecast"`, `fetched_at`. Collection `weather_forecasts`.
- `IWeatherForecastRepository.find_by_site(site_key, tenant_key) -> list[WeatherForecast]`
  (#403) — the read seam for the frost logic.
- `fetch_weather_forecasts` Celery task (#403) upserts daily forecasts per
  enabled site; guarded by the `settings.weather_enabled` kill-switch (default
  off); skips sites without `Site.gps_coordinates`.
- Coordinates live on `Site.gps_coordinates` (`domain/models/site.py:97`);
  `Location.site_key` (`:61`) resolves a location to its site. `Location` has no
  geo field — **no new field/migration needed**.
- Reactive path unchanged: `evaluate_frost_warning(temperature_celsius,
  threshold_celsius=3.0) -> bool | None` (`domain/engines/frost_warning_engine.py`),
  `sensor_service.get_location_frost_warning`, `GET /{key}/frost-warning ->
  FrostWarningResponse` (`api/v1/locations/`).
- Active delivery uses the N-003 notification system (`notification_service` +
  `notification_channel_registry`: in-app, PWA/VAPID, e-mail, Apprise, HA), not
  the Care-Reminder path.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question
  budget = `8` (spec defaults; unchanged).
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` — every required dimension `≥ τ_high` with an
  authoritative user answer or code-verified evidence; no remaining candidate
  question has positive net EVPI (the residual unknowns are low-EVPI
  implementation details, listed as open risks).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | interpretation (resolved) | Turn 1 (scope = read-path + notification), Turn 2 (horizon/threshold), Turn 3 (channel/dedup), Turn 4 (frontend) — all authoritative answers |
| `non_functional` | yes | 0.82 | interpretation | Graceful-degradation + idempotency patterns verified in #403 Celery task & reactive `None`-return; Turn 3 dedup answer |
| `constraints` | yes | 0.88 | interpretation (resolved) | Code inspection: consume #403 infra, 5-layer arch, **daily** granularity, `weather_enabled` kill-switch |
| `domain_objects` | yes | 0.90 | interpretation (resolved) | `k=2` read of `weather.py`, `weather_forecast_repository.py`, `site.py`, reactive engine |
| `actors` | yes | 0.85 | interpretation | Endpoint docstring (HA coordinator), #403 Celery task (scheduler), REQ-024 tenant isolation |
| `acceptance_criteria` | yes | 0.82 | interpretation (resolved) | Turns 1–4 answers → testable ACs below |
| `edge_cases` | yes | 0.80 | interpretation | Enumerated from #403 graceful patterns (no gps / disabled / empty / partial / tenant-mismatch) + Turn 3 dedup |
| `scope_boundaries` | yes | 0.82 | specification (resolved) | Turn 1 (notification in), Turn 4 (fill widget + read endpoint in; REQ-046 config UI out) |

## Requirements

<!-- EARS/CNL form, tagged confirmed/assumed, with traceability. -->

- **R1** — WHEN the persisted daily forecast for a location's site contains any
  record within the horizon whose `temp_min_c` is at or below the forecast frost
  threshold, the frost service SHALL report `forecast_frost_warning = true`
  together with the expected frost `forecast_min_temperature`,
  `forecast_expected_date`, and `forecast_source`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue #392
    ("evaluate the forecast horizon … raise an early warning"); Turn 2.
- **R2** — The forecast horizon SHALL be configurable via
  `settings.frost_forecast_horizon_days` with a default of **2** days (today +
  next day, ≈ the 24–48 h in Issue #392); the engine SHALL receive
  `horizon_days` as a parameter.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Turn 2
    ("Konfigurierbar, Default 2 Tage").
- **R3** — The forecast frost threshold SHALL be a **separate**
  `settings.frost_forecast_threshold_celsius`, independent of the reactive
  `settings.frost_warning_threshold_celsius` (3.0 °C).
  - _dimension_: `functional`/`constraints` · _status_: `confirmed` · _source_:
    Turn 2 ("Eigener Forecast-Threshold").
- **R4** — The forecast evaluation SHALL be a **pure** engine function (e.g.
  `evaluate_forecast_frost_warning(forecasts, threshold_celsius, horizon_days,
  today) -> {predicted: bool | None, min_temp, expected_date, source}`); the
  existing `evaluate_frost_warning` reactive function SHALL remain **unchanged**.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan design
    decision; NFR-001 5-layer; verified reactive engine.
- **R5** — WHEN no usable forecast is available for a location — no
  `Site.gps_coordinates`, `settings.weather_enabled` is off, the
  `weather_forecasts` collection has no in-horizon record, or every in-horizon
  record has `temp_min_c = None` — the service SHALL set the forecast fields to
  `null`/`unknown`, leave the reactive `frost_warning` untouched, and SHALL NOT
  raise a 500.
  - _dimension_: `edge_cases`/`non_functional` · _status_: `confirmed` ·
    _source_: Issue #392 ("Graceful degradation … never a 500"); reactive
    `None`-return convention.
- **R6** — The frost service SHALL expose the forecast result as **additive**
  fields on the existing `FrostWarningResponse`
  (`forecast_frost_warning: bool | None`, `forecast_min_temperature: float |
  None`, `forecast_expected_date: date | None`, `forecast_source: str | None`);
  the existing `frost_warning` field SHALL keep its reactive meaning so the HA
  coordinator does not break.
  - _dimension_: `functional`/`scope_boundaries` · _status_: `confirmed` ·
    _source_: plan (additive, HA-compat); Turn 4.
- **R7** — The system SHALL provide a **forecast-read endpoint** that the
  frontend `WeatherForecastWidget` consumes to render weather forecast plus a
  frost early-warning badge (next frost date + min temperature), filling the
  REQ-046 placeholder widget.
  - _dimension_: `functional`/`scope_boundaries` · _status_: `confirmed` ·
    _source_: Turn 4 ("Platzhalter-WeatherForecastWidget füllen"); #403 widget
    comment noting the missing forecast-read endpoint.
- **R8** — WHEN the scheduled weather fetch persists a daily forecast that
  contains an in-horizon frost for a site, the system SHALL emit **one** N-003
  notification (via `notification_service` → channel registry, respecting user
  notification preferences) announcing the expected frost date, location, and
  minimum temperature.
  - _dimension_: `functional`/`actors` · _status_: `confirmed` · _source_:
    Turn 1 ("Read-Path + aktive Notification"); Turn 3 ("Notification-System
    N-003").
- **R9** — The frost notification SHALL be **idempotent per `(site_key, expected
  frost forecast_date)`**: repeated fetches for the same frost event SHALL NOT
  re-notify; a new notification is emitted only for a new or earlier frost date.
  - _dimension_: `non_functional`/`edge_cases` · _status_: `confirmed` ·
    _source_: Turn 3 ("Einmal pro Standort + Frost-Datum").
- **R10** — All forecast reads and notifications SHALL respect tenant isolation
  (`find_by_site(site_key, tenant_key)`; site↔config tenant match per #403
  SEC-002).
  - _dimension_: `non_functional`/`actors` · _status_: `confirmed` · _source_:
    REQ-024; #403 Celery `weather_fetch_tenant_mismatch` guard.
- **R11** — WHEN the additive response contract is extended (R6), the
  `kamerplanter-ha` custom integration SHALL be checked and, if needed, synced
  (`ha-integration-sync`) so the HA coordinator surfaces the forecast field
  without breaking on the unchanged reactive field.
  - _dimension_: `scope_boundaries`/`actors` · _status_: `assumed` · _source_:
    plan Q4; HA-integration deploy convention. Confirm during implementation.

## Acceptance Criteria

- [ ] Branch rebased onto develop; #403 weather infrastructure present; suite
      green.
- [ ] Pure engine: in-horizon `temp_min_c ≤ frost_forecast_threshold_celsius`
      → `predicted=true` + earliest such date + its min temp + source; no
      in-horizon frost → `predicted=false`; empty / all-`None` forecast →
      `predicted=None`. Horizon boundary (day `horizon_days` inclusive, day
      `horizon_days+1` excluded) covered by tests.
- [ ] Service combines reactive (unchanged) + forecast (additive); no gps /
      `weather_enabled` off / empty repo → forecast fields `None`, reactive
      unchanged, **no 500** (regression test).
- [ ] `FrostWarningResponse` carries the four additive fields; reactive
      `frost_warning` unchanged; endpoint test asserts both paths.
- [ ] Forecast-read endpoint returns the widget payload; `WeatherForecastWidget`
      renders forecast + frost badge (vitest).
- [ ] Frost notification emitted exactly once per `(site_key, frost_date)` across
      repeated fetches; respects notification preferences; tenant-scoped.
- [ ] Real-flow verification (`/verify`/`run`): a site with coordinates + a
      simulated in-horizon frost forecast → `forecast_frost_warning=true` +
      date; without a source → clean fallback, reactive intact.
- [ ] Full quality gate green (ruff/format/pytest; eslint/tsc/vitest for the
      touched frontend); PR to `develop`.

## Surviving assumptions / open risks

- **R11 (`assumed`) — HA sync:** whether the `kamerplanter-ha` coordinator must
  be extended for the new forecast field is not yet verified against that repo;
  confirm during implementation. *(scope_boundaries residual)*
- **Notification wiring depth:** the exact `notification_service` producer seam
  (does a new notification "type"/template need registering, mirroring how
  winter reminders were wired in #360) is verified only at the interface level;
  the producer call site is an implementation detail. *(edge_cases residual,
  `c_d`=0.80)*
- **Idempotency store:** R9's dedup needs a persisted marker keyed on
  `(site_key, forecast_date)` (a small collection, a field on the forecast
  record, or a notification-history lookup). The mechanism is an implementation
  choice made under green tests; the *behaviour* (once per site+date) is
  confirmed.
- **Past/rolling dates:** the engine must ignore `forecast_date < today`; treated
  as an obvious implementation guard (low EVPI), not separately elicited.
- **Threshold/horizon defaults** (`frost_forecast_threshold_celsius`,
  `frost_forecast_horizon_days=2`) are engineering defaults, overridable per
  deployment; the separate-threshold decision is confirmed, its *numeric* value
  is a default to calibrate.
