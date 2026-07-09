---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 409
classification: refactor
secondary-classes: [bug]
route: direct
status: approved
created: 2026-07-09
---

# Issue Orchestration — Pre-analysis

<!-- Prose in the issue's language (English); machine-readable fields in English. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #409 — Follow-ups from #404 pre-merge review: forecast-frost efficiency & delivery edge cases
- **URL**: https://github.com/nolte/kamerplanter/issues/409
- **Labels**: enhancement, backend
- **Linked items**: #404 (introducing PR, squash `4200b003c`), #392 (proactive forecast frost, closed by #404)
- **Prior art checked**: `project/requirements/forecast-frost-followups.md` (confirmed requirement artifact, `U_gate = 0.85`, R1–R5 + R1a all `confirmed`); #404 fix-forward findings (already merged, distinct set); no open PR addresses these five findings. Grounded in `src/backend/app/domain/services/{sensor_service,notification_service}.py`, `src/backend/app/domain/engines/notification_engine.py`, `src/backend/app/data_access/arango/notification_repository.py`, `src/backend/app/tasks/frost_forecast_tasks.py`, migrations `versions/v0006`–`v0008`.

## Classification

- **Primary class**: refactor
- **Secondary class(es)**: bug
- **Rationale**: F1/F2 are efficiency refactors (hot-path read reduction, unindexed-scan removal); F5 (over-counting metric) and F3 (mid-event-join miss) are behavioural bugs; F4 is a small consistency fix. No new capability → refactor primary, bug secondary.

## Scope

- **In scope**: All five deferred #404 findings, backend-only, as one PR strand — R1 (drop per-location forecast fields), R2 (`exists_by_group_key` + persistent `group_key` index via versioned migration), R3 (per-recipient top-up), R4 (quiet-hours bypass for `frost_forecast_warning`), R5 (delivered-only `users_notified`).
- **Out of scope**: The Home Assistant integration code (separate repo). R1 removes fields the HA integration reads per-location; re-syncing HA to the per-site `GET /sites/{site_key}/weather-forecast` endpoint (**R1a**) is a tracked follow-up (`ha-integration-sync`), NOT delivered here — the PR body notes it as a rollout dependency. The frontend, the REQ-046 `fetch_weather_forecasts` task, and the reactive frost path (beyond the F1 field removal and the F4 type addition) are untouched. No new roadmap item.

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (harden the #404 forecast-frost feature), a single backend PR strand, no new/retargeted roadmap item. Requirements already elicited to `U_gate = 0.85` with all decisions confirmed → direct implementation, no pipeline hand-off.
- **Pipeline hand-off**: n/a

## Verified code anchors

- **F1**: `sensor_service.get_location_frost_warning` (`src/backend/app/domain/services/sensor_service.py:152`) calls `self._forecast_frost_summary(site_key, tenant_key)` (`:190`) and returns four `forecast_*` fields (`:199–202`). Router `src/backend/app/api/v1/locations/tenant_router.py:143` (`GET /{key}/frost-warning`) maps into `FrostWarningResponse` (`src/backend/app/api/v1/locations/schemas.py:59`, fields `:77–80`). Per-site read path confirmed to exist: `GET /sites/{site_key}/weather-forecast` → `get_site_weather_forecast` (`tenant_scoped/weather/tenant_router.py:147`, `sensor_service.py:205`) — **A1 verified**.
- **F2**: `notification_repository.find_by_group_key` (`src/backend/app/data_access/arango/notification_repository.py:164`, interface `domain/interfaces/notification_repository.py:52`) runs `FOR doc … FILTER doc.group_key == @group_key … RETURN doc` with no `LIMIT` and maps every doc. Bootstrap indexes for `notifications` are in `data_access/arango/collections.py:1456–1459` — `group_key` is **not** among them. Migration pattern: `versions/v0006`/`v0008` (`Migration` base, `up(db, *, dry_run)`, `MigrationReport`); next free version = **v0009**.
- **F3**: dedup guard `send_frost_forecast_notifications` (`src/backend/app/domain/services/notification_service.py:191`) treats a non-empty `find_by_group_key` as "whole group already notified → return `deduplicated`". `Notification` carries `user_key` (`domain/models/notification.py:29`) and `group_key` (`:37`), so already-notified recipients are already derivable per group. Producer builds `user_keys` from active members in `tasks/frost_forecast_tasks.py:91–92`.
- **F4**: `_QUIET_HOURS_BYPASS_TYPES = frozenset({"sensor.alert", "weather.frost"})` (`domain/engines/notification_engine.py:27`), consulted by `_ignores_quiet_hours` (`:355`). Proactive type literal is `"frost_forecast_warning"` (`notification_service.py:218`).
- **F5**: `send_frost_forecast_notifications` does `users_notified += 1` unconditionally per recipient (`notification_service.py:225`), ignoring the `send_notification`→`engine.notify` result whose `status` ∈ {`delivered`, `failed`, `deduplicated`, `queued_quiet_hours`, `no_channels`} (`notification_engine.py:92–159`); only `delivered` (channels_sent non-empty) is a genuine reach. The task rolls this up via `emit.get("users_notified")` (`frost_forecast_tasks.py:106`).

## Work packages

### P1 — Persistent index on `notifications.group_key` (bootstrap + versioned migration)

- **Problem statement**: The `group_key` dedup read has no supporting index; a growing `notifications` collection is full-scanned per frost-predicted site per day.
- **Acceptance criteria**: (1) `ensure_collections`/bootstrap in `collections.py` adds a non-unique persistent index on `notifications.group_key` (fresh DBs). (2) A new `v0009` migration idempotently creates the same index on existing volumes: re-run reports `changed == 0`, `dry_run` writes nothing, follows the `Migration`/`MigrationReport` contract of v0006/v0008. (3) Unit test asserts the migration is idempotent and that the index exists after `up`.
- **Touched files / artifacts**: `src/backend/app/data_access/arango/collections.py` (~`:1456`); `src/backend/app/migrations/versions/v0009_notification_group_key_index.py` (new); migration registration/index; `src/backend/tests/unit/data_access/arango/test_notification_repository.py` and/or a new migration test.
- **Specialist**: `fullstack-developer` (backend; honour the versioned migration-framework pattern — `Migration` base, idempotent `up`, `dry_run` support).
- **Depends on**: none.

### P2 — `exists_by_group_key` repo primitive (R2)

- **Problem statement**: The dedup truthiness check materialises and maps every matching notification just to test existence.
- **Acceptance criteria**: (1) `exists_by_group_key(group_key, tenant_key) -> bool` added to the notification repository interface and ArangoDB impl using `… LIMIT 1 RETURN 1` (or `COLLECT WITH COUNT`), returning without mapping full docs. (2) The frost dedup guard's boolean use of `find_by_group_key` is replaced by `exists_by_group_key` (subject to the R3 coordination note — see Risks). (3) Repo unit tests cover present/absent group and tenant-scoping (a foreign `tenant_key` returns `False`).
- **Touched files / artifacts**: `src/backend/app/domain/interfaces/notification_repository.py`, `src/backend/app/data_access/arango/notification_repository.py`, `src/backend/tests/unit/data_access/arango/test_notification_repository.py`.
- **Specialist**: `fullstack-developer`.
- **Depends on**: P1 (index backs the efficient read).

### P3 — Remove forecast fields from the per-location frost-warning path (R1)

- **Problem statement**: Every location poll triggers a site-level forecast read; N locations on a site → N identical reads on the HA hot path.
- **Acceptance criteria**: (1) `get_location_frost_warning` no longer calls `_forecast_frost_summary` and no longer returns `forecast_frost_warning`/`forecast_min_temperature`/`forecast_expected_date`/`forecast_source`; the reactive `frost_warning` behaviour is unchanged. (2) `FrostWarningResponse` drops the four `forecast_*` fields; the router docstring is updated to point HA at the per-site endpoint. (3) Existing `test_sensor_service.py` and `test_location_frost_warning_router.py` cases asserting the removed fields are updated/removed; a test asserts no site/forecast repo call is made on the per-location path.
- **Touched files / artifacts**: `src/backend/app/domain/services/sensor_service.py` (`:152`, drop `:190`,`:199–202`; `_forecast_frost_summary` may become dead if unused elsewhere — verify and remove if so), `src/backend/app/api/v1/locations/schemas.py` (`:77–80`), `src/backend/app/api/v1/locations/tenant_router.py` (`:143` docstring), `src/backend/tests/unit/domain/services/test_sensor_service.py`, `src/backend/tests/api/test_location_frost_warning_router.py`.
- **Specialist**: `fullstack-developer`.
- **Depends on**: none.

### P4 — `frost_forecast_warning` bypasses quiet hours (R4)

- **Problem statement**: The HIGH-urgency proactive `frost_forecast_warning` can be held until the quiet-hours flush, unlike the reactive `weather.frost`.
- **Acceptance criteria**: (1) `"frost_forecast_warning"` added to `_QUIET_HOURS_BYPASS_TYPES`. (2) An engine unit test proves a `frost_forecast_warning` during quiet hours is delivered immediately (not `queued_quiet_hours`).
- **Touched files / artifacts**: `src/backend/app/domain/engines/notification_engine.py` (`:27`), `src/backend/tests/unit/domain/engines/` (notification engine test).
- **Specialist**: `fullstack-developer`.
- **Depends on**: none.

### P5 — `users_notified` counts only delivered sends (R5)

- **Problem statement**: `users_notified` increments per recipient regardless of the `send_notification` result, so the task-run summary over-reports reach.
- **Acceptance criteria**: (1) In `send_frost_forecast_notifications` the counter increments only when the `send_notification`→`engine.notify` result is a genuine delivery (`status == "delivered"`); `deduplicated`, `queued_quiet_hours`, `no_channels`, `failed` do NOT count. (2) Unit tests cover a mix of statuses and assert the count equals the number of `delivered` results; the `frost_forecast_tasks` roll-up (`notified`) reflects it.
- **Touched files / artifacts**: `src/backend/app/domain/services/notification_service.py` (`:213–234`), `src/backend/tests/unit/domain/services/test_notification_service.py`, `src/backend/tests/unit/tasks/test_frost_forecast_tasks.py`.
- **Specialist**: `fullstack-developer`.
- **Depends on**: none. (Edits the same send loop as P6 — sequence before P6; see Risks.)

### P6 — Per-recipient top-up for mid-event joiners (R3)

- **Problem statement**: Group-wide dedup skips a member who becomes eligible after the first daily run but before the frost date; they never receive the already-announced warning.
- **Acceptance criteria**: (1) An index-backed repo read returns the set of `user_key`s already notified for a `(group_key, tenant_key)` (projected, not full-doc materialisation). (2) `send_frost_forecast_notifications` sends only to `user_keys` NOT already in that set (top-up); already-notified members get no duplicate. (3) When all supplied recipients are already notified, no send occurs and the delivered count is 0. (4) The R5 delivered-only counting (P5) is preserved for the topped-up recipients. (5) Unit tests: first run notifies all; a later run with one new member notifies only the new member; a later run with no new member sends nothing.
- **Touched files / artifacts**: `src/backend/app/domain/interfaces/notification_repository.py`, `src/backend/app/data_access/arango/notification_repository.py` (new projected-user-keys read), `src/backend/app/domain/services/notification_service.py` (`:187–234` dedup+send loop), `src/backend/tests/unit/domain/services/test_notification_service.py`, `src/backend/tests/unit/data_access/arango/test_notification_repository.py`.
- **Specialist**: `fullstack-developer`.
- **Depends on**: P1 (index), P2 (repo primitive family / coordinated dedup semantics), P5 (delivered-only send loop already in place).

## Dependency ordering

```
P1 → P2 → P6
P5 → P6
P3            (independent)
P4            (independent)
```

Suggested dispatch order: P1, then {P2, P3, P4, P5} (P3/P4/P5 parallelisable, P2 after P1), then P6 last. Because P2/P5/P6 all mutate `notification_service.py` / `notification_repository.py`, dispatch them sequentially (not in parallel on the shared tree) per the "schreibende Agenten auf geteiltem Tree sequenziell" convention.

## Risks

- **R2 ↔ R3 interaction (design coordination).** R2 adds a boolean `exists_by_group_key`, but R3 replaces the frost path's group-level truthiness check with a per-recipient set query — so after P6 the frost producer no longer uses `exists_by_group_key`. Mitigation: keep `exists_by_group_key` as the general-purpose primitive R2 mandates (useful for pure group-once producers), implement P6's recipient-set read as the index-backed efficient read, and have both share the P1 `group_key` index. Flag for the implementing specialist so P2 and P6 are co-designed, not contradictory.
- **R1a breaking change (rollout).** Removing the per-location `forecast_*` fields (P3) breaks the current HA integration until it is re-synced to `GET /sites/{site_key}/weather-forecast`. Mitigation: PR body MUST record the `ha-integration-sync` follow-up as a rollout dependency; the two must ship close together to avoid an HA frost-visibility gap.
- **Migration on existing volumes (P1).** An index-adding migration must be idempotent and not lock/re-scan destructively. Mitigation: follow v0006/v0008 idempotency (re-run `changed == 0`, `dry_run` no-op); Arango persistent-index creation is idempotent by field-set.
- **Shared-file write conflicts.** P2/P5/P6 edit overlapping files. Mitigation: sequential dispatch per the DAG; do not run these packages in parallel on the shared worktree.
- **No security-sensitive surface added.** Tenant-scoping is preserved in all repo reads (existing `tenant_key` filters); no new auth path. A `code-security-reviewer` pass is not required beyond the standard pre-merge review, but the tenant-scoping of the new projected read (P6) should be verified in review.

## Open questions

- **Q1 (P6 storage shape, A2).** Per-recipient top-up can reuse the existing `Notification.user_key`+`group_key` rows (derive the already-notified set from persisted notifications) rather than a new tracking record. Confirm the implementer should derive the set from existing notification rows (preferred — no schema change) unless a persisted notification is not always written for a delivered send. Verify that `send_notification` persists a row for every counted delivery so the derived set stays accurate across runs.
- **Q2 (P3 dead-code).** After P3, confirm `_forecast_frost_summary` has no remaining caller; if so it should be removed (kept only if `get_site_weather_forecast` or another path still needs it — current read shows `get_site_weather_forecast` uses `_load_site_forecasts` directly, so `_forecast_frost_summary` likely becomes dead).

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports. -->

2026-07-09 P1–P6 dispatched to `fullstack-developer` (single coordinated agent, DAG order) — approved by operator.
