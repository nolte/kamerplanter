# Requirements — Weather fetch interval and manual fetch (#2934)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Interview conducted 2026-11-17 with the operator (German); artifact in English.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** a configurable, global weather fetch interval in hours, a manual "fetch now" action with result feedback, display of the last successful fetch, unambiguous wording of the timeout field, and the matching updates of REQ-046 and REQ-037.
- **For whom:** platform admins (the weather admin endpoints are gated `require_platform_admin`, `api/v1/admin/weather_providers/router.py:68,78,114`); the UI lives in the Installation group of the settings page (F-11, R-17).
- **Out of scope:** new weather sources; frost and irrigation logic beyond their timing coupling to the fetch; sub-6-hour intervals; per-tenant or per-site weather settings and per-site manual fetch; sensor-measured precipitation in the irrigation demand (separate issue).
- _source_: Q1 "ja", Q2 "A", Q5 "ja, das passt".

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8` (6 used)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (final teach-back Q6 confirmed)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.9 | specification (resolved) | Q2 global trigger, Q3/Q4 chaining, Q6 teach-back |
| `non_functional` | yes | 0.8 | specification | Q6: no restart on change, 10-min manual cooldown |
| `constraints` | yes | 0.9 | specification (resolved) | Q4 "6h ist das minimum", platform-admin gate measured |
| `domain_objects` | yes | 0.85 | interpretation | `fetch_interval_hours`, last-fetch record, Q6 |
| `actors` | yes | 0.85 | interpretation | Q2 "A"; gate corrected to platform admin in Q6 |
| `acceptance_criteria` | yes | 0.85 | specification | issue AC + Q6 teach-back |
| `edge_cases` | yes | 0.8 | specification | Q6: concurrent run, cooldown, sub-minimum value |
| `scope_boundaries` | yes | 0.9 | specification (resolved) | Q1, Q5 sensor precipitation split out |

Self-consistency (k=2) diverged on the manual trigger scope (global vs. per site → Q2), on the meaning of "4 mal am Tag" (default vs. minimum → Q4) and on the irrigation slot (daily vs. per fetch → Q4); each resolved by a decision answer.

## Requirements

- **R1** — The weather settings SHALL hold a global `fetch_interval_hours` (minimum 6, default 6), layered like `fetch_timeout_s` (DB value over env default) and edited in the "Abruf-Einstellungen" card.
  - _dimension_: `functional`, `constraints` · _status_: `confirmed` · _source_: Q4 "6h ist das minimum", Q5 default, Q6
- **R2** — WHEN a value below 6 is submitted, the API SHALL reject it with 422 and the UI SHALL prevent it.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q6
- **R3** — The scheduler SHALL run an hourly due-check and start a fetch WHEN at least `fetch_interval_hours` have passed since the last successful fetch; a changed interval SHALL take effect without restart or redeploy.
  - _dimension_: `functional`, `non_functional` · _status_: `confirmed` · _source_: Q3, Q4, Q6
- **R4** — WHEN a fetch (scheduled or manual) completes successfully, the system SHALL run the frost early-warning evaluation and the irrigation demand computation; their fixed daily beat slots SHALL be removed.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q3 "frostwarnung immer nach dem abruf", Q5 "der bewässerungsbedarf muss jedesmal ermittelt werden"
- **R5** — A platform admin SHALL be able to start a fetch for all configured sites from the Installation group; the manual fetch counts as a regular fetch and restarts the interval.
  - _dimension_: `functional`, `actors` · _status_: `confirmed` · _source_: Q2 "A", Q6
- **R6** — WHILE a fetch is running, or within 10 minutes after the previous manual fetch, a manual fetch SHALL be refused with a message naming when it is possible again.
  - _dimension_: `edge_cases`, `non_functional` · _status_: `confirmed` · _source_: Q6 "das passt!"
- **R7** — The manual fetch SHALL report its result (success/failure, timestamp, number of sites).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue, Q6
- **R8** — The card SHALL show time and result of the last successful fetch and the next scheduled fetch.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue AC, Q6
- **R9** — Label and helper text of the timeout field SHALL state unambiguously (DE + EN) that it is the time limit per request, not the fetch frequency.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: issue, Q6
- **R10** — REQ-046 (interval, manual fetch, chaining) and REQ-037 (irrigation demand after every fetch instead of daily) SHALL be updated.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: issue AC, Q6
- **R11** — The UI part SHALL follow F-11 (Installation group); the backend part is independent of it.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q6
- **R12** — A fetch SHALL count as successful WHEN it ends without a runtime error and wrote at least one site (or no site is configured); only a successful fetch restarts the interval and triggers R4; after a failed fetch the next hourly due-check retries. The status SHALL carry the number of sites with errors.
  - _dimension_: `edge_cases`, `domain_objects` · _status_: `confirmed` · _source_: revisit 2026-11-17 decision 1 "ja"
- **R13** — The season evaluation (`season-evaluate-states-daily`) SHALL keep its daily slot and read the latest stored forecast; its coupling to the 06:00 fetch is removed from code comments and REQ-047.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: revisit decision 2
- **R14** — The manual fetch SHALL be asynchronous (202 + status polling); a refusal SHALL answer 409 while a fetch runs and 429 with `Retry-After` during the 10-minute cooldown (NFR-006, NFR-007); the "fetch running" lock SHALL be held by the fetch task itself.
  - _dimension_: `non_functional`, `edge_cases` · _status_: `confirmed` · _source_: revisit decisions 3+4
- **R15** — The last-fetch status SHALL be stored in a dedicated status document written only by the fetch task (not the `SystemSettings` singleton).
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: revisit decision 5
- **R16** — The due-check SHALL live in `fetch_weather_forecasts` itself (hourly beat, early return when not due); the frost and irrigation beats are removed and the tenant-beat classification (`tenant_gate.py`) and its guard tests updated; REQ-005 §121, REQ-047 §411 and REQ-056 (beat classification), `notifications.md:189` (DE+EN) and the env var `WEATHER_FETCH_INTERVAL_HOURS` in `environment-variables.md` (DE+EN) SHALL be updated.
  - _dimension_: `constraints`, `acceptance_criteria` · _status_: `confirmed` · _source_: revisit decisions 6+7

## Surviving assumptions / open risks

- **Sensor precipitation** in the irrigation demand (REQ-037/REQ-005 fallback chain) is split into its own issue; until then the 4×/day recomputation uses forecast precipitation only (`irrigation_tasks.py:145`).
- **Frost idempotency:** the frost evaluation is idempotent per `(site_key, expected frost date)` (`frost_forecast_tasks.py:7`), so per-fetch runs do not duplicate warnings — established. The irrigation demand upserts per `(site, run, day)` — established from the task docstring.
- **Revisit 2026-11-17:** the consistency check of F-13/F-14 found the undefined "successful fetch", the season-evaluation coupling, the beat-guard tests and further 06:00 spec anchors; the operator accepted all seven recommendations (R12–R16).
- **Scheduled time anchor:** with the hourly due-check the fetch times drift from today's fixed 06:00; accepted implicitly with R3. `assumed`.
