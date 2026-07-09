# Requirements — Forecast-frost follow-ups (#404 deferred review findings, Issue #409)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (methodology spec shipped in claude-shared).
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Resolve the five consciously-deferred efficiency & delivery-edge-case
  findings from the #404 pre-merge review of the proactive weather-forecast frost
  warning (introduced by #404, squash `4200b003c`). Backend-only.
- **For whom:** Home Assistant integration (F1 poll hot path), notification
  recipients who join mid-event (F3) or are in quiet hours (F4), and the task-run
  metrics consumer (F5); the growing `notifications` collection (F2).
- **Out of scope:** The reactive HA frost path's behaviour beyond the F1 field
  removal and the F4 type addition; the frontend; the Home Assistant integration
  code itself (a separate repo — F1 requires a follow-up `ha-integration-sync`,
  tracked as a consequence below, not delivered in this PR); any new roadmap item.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `4`
  <!-- spec defaults; four high-EVPI decision questions spent (F1 approach, F3 top-up,
       F4 quiet-hours, F5 metric semantics). F2 carried no open decision. -->
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` (all four deferred design decisions resolved by operator; no positive-EVPI question remains)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.9 | specification | Operator answers on F1/F3/F4/F5 + teach-back; F2 fix stated in issue |
| `non_functional` | yes | 0.85 | interpretation | Efficiency intent explicit in issue (hot-path reads, unindexed scan) |
| `constraints` | yes | 0.85 | interpretation | Migration framework (v0006/v0008 pattern) for F2 index; HA integration is a separate repo (F1 consequence) |
| `domain_objects` | yes | 0.9 | interpretation | Code-verified: `Notification.group_key`, `WeatherForecast`, `Site`, `frost_forecast_warning` type, `_QUIET_HOURS_BYPASS_TYPES` |
| `actors` | yes | 0.9 | interpretation | HA poll (F1), recipients (F3/F4), task-run summary (F5) |
| `acceptance_criteria` | yes | 0.85 | specification | Per-finding, derived from issue + answers; teach-back confirmed |
| `edge_cases` | yes | 0.8 | interpretation | F3 itself is a mid-event-join edge case; F2 migration idempotency; F1 HA breaking-change |
| `scope_boundaries` | yes | 0.9 | specification | Backend-only; HA-integration sync deferred to separate repo; issue explicitly scopes the 5 findings |

## Requirements

- **R1 (F1)** — The per-location frost-warning response
  (`sensor_service.get_location_frost_warning`, backing
  `binary_sensor.kp_{location}_frost_warning`) SHALL NOT perform the site-level
  forecast read; the forecast fields SHALL be removed from the per-location
  response so a site with N locations no longer triggers N identical site-level
  forecast reads on the HA poll hot path. HA reads the frost forecast per-site via
  `GET /sites/{site_key}/weather-forecast`.
  - _dimension_: `functional`/`non_functional` · _status_: `confirmed` · _source_: operator answer "Forecast-Felder aus per-Location droppen" + teach-back
- **R1a (F1 consequence)** — Because R1 removes fields the HA integration currently
  reads per-location, the Home Assistant integration (separate repo) MUST be
  re-synced to read the per-site endpoint. This is a tracked follow-up
  (`ha-integration-sync`), NOT delivered in this PR; the PR notes it as a rollout
  dependency.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: teach-back (out-of-scope boundary)
- **R2 (F2)** — The frost dedup guard SHALL test group-key existence without
  materialising every matching notification: expose `exists_by_group_key`
  (`... LIMIT 1 RETURN 1` or `COLLECT WITH COUNT`) and use it in place of
  `find_by_group_key` for the truthiness check, backed by a persistent index on
  `group_key` created via a versioned, idempotent migration (v0006/v0008 pattern).
  - _dimension_: `functional`/`non_functional` · _status_: `confirmed` · _source_: issue F2 (no open decision)
- **R3 (F3)** — WHEN a tenant member becomes eligible after the first daily
  forecast run but before the frost date, the system SHALL still deliver the
  already-announced warning to that member: track notified recipients per
  `(site_key, forecast_date)` event and, on later runs, top up only the
  newly-eligible members (no duplicate send to already-notified members).
  - _dimension_: `functional`/`edge_cases` · _status_: `confirmed` · _source_: operator answer "Per-recipient-Tracking + Top-up" + teach-back
- **R4 (F4)** — The proactive `frost_forecast_warning` type SHALL bypass quiet
  hours (added to `_QUIET_HOURS_BYPASS_TYPES`), consistent with the reactive
  `weather.frost` type, so a high-urgency forecast is not held until the
  quiet-hours flush.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: operator answer "Ja, Quiet-Hours bypassen" + teach-back
- **R5 (F5)** — `send_frost_forecast_notifications` SHALL increment
  `users_notified` only for a genuinely delivered/accepted `send_notification`
  result; deduped, queued-during-quiet-hours, no-channels, and failed sends SHALL
  NOT count. The task-run summary metric reflects users actually reached.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: operator answer "Nur echt zugestellt/akzeptiert" + teach-back

## Surviving assumptions / open risks

- **A1 (assumed):** `GET /sites/{site_key}/weather-forecast` already exists and
  returns the per-site frost summary the removed per-location fields carried (the
  issue names it as the intended read path). Verify during implementation.
- **A2 (assumed):** Per-recipient top-up (R3) can reuse the existing notification /
  group_key model with an added per-recipient marker; whether it needs a schema
  field or a separate tracking record is an implementation choice left to the plan
  author, provided the "no duplicate send" invariant holds.
- **Risk (R1a):** Removing the per-location forecast fields is a breaking change
  for the current HA integration until it is re-synced to the per-site endpoint;
  the two must ship close together to avoid a gap in HA frost visibility.
