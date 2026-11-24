---
id: F-13
title: Intervallgesteuerter Wetterabruf mit manuellem Start
status: done
roadmap_item: R-18
sprint: 3
created: 2026-11-17
ended: 2026-11-23
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@6b9b769c6
  findings:
    - kind: drift
      target: src/backend/app/tasks/tenant_gate.py:70
      resolution: proceed
      evidence: "frost (:70) and irrigation (:72) are in TENANT_WRITING_BEATS; removing their beats fails test_beats_skip_inactive_tenants.py:114 and :129 (count == 55); both tasks still check ActiveTenants themselves (frost_forecast_tasks.py:44,51)."
    - kind: drift
      target: src/backend/tests/unit/guards/test_every_task_is_scheduled_or_dispatched.py:178
      resolution: proceed
      evidence: "MT-051 guard asserts fetch_weather_forecasts == 'scheduled'; kept green by placing the due-check inside the fetch task (operator decision 6)."
    - kind: drift
      target: src/backend/app/tasks/__init__.py:684
      resolution: proceed
      evidence: "season-evaluate-states-daily (06:30) is documented as 'after the weather fetch' (:684, season_tasks.py:7, REQ-047:411); operator decision 2: slot stays daily, coupling removed."
    - kind: drift
      target: spec/req/REQ-005_Hybrid-Sensorik.md:121
      resolution: proceed
      evidence: "REQ-005:121 fixes 06:00, REQ-047:411 ~06:30, REQ-037:337,386,508 06:00/06:15; all updated (acceptance-7)."
    - kind: drift
      target: src/backend/app/tasks/weather_tasks.py:99
      resolution: proceed
      evidence: "Task returns 'ok' even when every site errored (:89-100); max_retries=3 (:20) never used; operator decision 1 defines success (acceptance-3)."
    - kind: drift
      target: spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md:722
      resolution: proceed
      evidence: "NFR-007:722 MUST Retry-After on rate-limit responses; NFR-006:250/252 define 409 CONFLICT / 429 RATE_LIMITED; operator decision 4 adopts them."
    - kind: prior-art
      target: src/backend/app/data_access/external/step_up_code_store.py:199
      resolution: proceed
      evidence: "Redis SET NX EX + ttl() (:199-201) and rendition_dispatch_claims.py:89 — reusable for the running lock and the cooldown."
    - kind: prior-art
      target: src/backend/app/tasks/climate_tasks.py:108
      resolution: proceed
      evidence: "_is_fresh(fetched_at, now, ttl) (:108-117) — TTL guard pattern for the hourly due-check."
    - kind: prior-art
      target: src/backend/app/domain/services/weather_settings_service.py:174
      resolution: proceed
      evidence: "fetch_timeout_s layering (:174-176, :224-225; schemas.py:53 ge=1,le=120) is the template for fetch_interval_hours (ge=6); no WEATHER_FETCH_INTERVAL_HOURS env var yet (settings.py:587-596)."
    - kind: prior-art
      target: src/backend/app/api/v1/admin/pests/router.py:116
      resolution: proceed
      evidence: "Platform-admin manual triggers dispatch async with 202 + task_id (pests :116-122, recognition :106); operator decision 3 follows it."
    - kind: prior-art
      target: src/backend/app/tasks/frost_forecast_tasks.py:7
      resolution: proceed
      evidence: "Frost idempotent per (site_key, expected frost date); irrigation upserts per site/run/day (irrigation_tasks.py:9,170) — chaining 4x/day duplicates nothing."
---

## Description

Wetterdaten werden heute fest einmal am Tag um 06:00 abgerufen; danach
laufen Frost-Frühwarnung und Bewässerungsbedarf zu festen Uhrzeiten. Der
Plattform-Admin kann weder die Häufigkeit ändern noch einen Abruf von Hand
anstoßen, und ein Abruf gilt auch dann als erfolgreich, wenn jeder Standort
fehlschlug.

Nach dieser Änderung legt der Plattform-Admin ein Abrufintervall in Stunden
fest (mindestens und standardmäßig 6 h). Das System prüft stündlich, ob ein
Abruf fällig ist, und übernimmt ein geändertes Intervall ohne Neustart. Nach
jedem erfolgreichen Abruf werden Frost-Frühwarnung und Bewässerungsbedarf
sofort neu berechnet. Ein manueller Abruf läuft im Hintergrund über alle
Standorte; parallele Läufe und zu dichte Wiederholungen werden mit klarer
Rückmeldung abgelehnt. Ein Status gibt Auskunft über den letzten
erfolgreichen und den nächsten geplanten Abruf.

## Acceptance criteria

- [x] **acceptance-1** Ein Plattform-Admin stellt das Abrufintervall in Stunden ein (mindestens und standardmäßig 6 h); kleinere Werte werden mit 422 abgelehnt, und ein geänderter Wert greift ohne Neustart.
- [x] **acceptance-2** Ein Abruf startet automatisch, sobald seit dem letzten erfolgreichen Abruf das Intervall vergangen ist; nach einem fehlgeschlagenen Abruf versucht es die nächste stündliche Prüfung erneut.
- [x] **acceptance-3** Ein Abruf gilt als erfolgreich, wenn er ohne Laufzeitfehler endet und mindestens einen Standort geschrieben hat (oder kein Standort konfiguriert ist); nur dann werden Frost-Frühwarnung und Bewässerungsbedarf neu berechnet.
- [x] **acceptance-4** Ein Plattform-Admin startet einen manuellen Abruf über alle Standorte; die Antwort kommt sofort (202), Ergebnis (Erfolg/Fehler, Zeitpunkt, Standorte, Standorte mit Fehler) steht danach im Status; ein erfolgreicher manueller Abruf startet das Intervall neu.
- [x] **acceptance-5** Ein manueller Abruf wird mit 409 abgelehnt, solange ein Abruf läuft, und mit 429 samt `Retry-After`, solange seit dem letzten manuellen Abruf keine 10 Minuten vergangen sind.
- [x] **acceptance-6** Der Status nennt Zeitpunkt und Ergebnis des letzten erfolgreichen Abrufs sowie den nächsten geplanten Abruf.
- [x] **acceptance-7** REQ-046, REQ-037, REQ-005, REQ-047 und REQ-056 sowie die Referenz der Umgebungsvariablen beschreiben Intervall, manuellen Abruf und die Kopplung von Frost und Bewässerung an jeden Abruf.

## Test hooks

- **acceptance-1** — `src/backend/tests/unit/` service + router tests for `fetch_interval_hours` (ge=6, DB over env) — passing — `tests/unit/domain/services/test_weather_settings_service.py::TestFetchInterval`, `tests/api/test_admin_weather_providers.py::test_put_rejects_an_interval_below_six_hours_with_422` (merged in #3097)
- **acceptance-2** — unit test of the due-check in `fetch_weather_forecasts` (not due → early return; failed last run → retried) — passing — `tests/unit/tasks/test_weather_tasks.py::TestDueCheck` (#3097)
- **acceptance-3** — unit test of the success definition (all sites failed → failure, no chaining; ≥1 written → success + frost/irrigation dispatched) — passing — `tests/unit/tasks/test_weather_tasks.py::TestSuccessDefinition`, `test_followups_queue_frost_and_irrigation` (#3097)
- **acceptance-4** — router test: 202 for platform admin, 403 otherwise; status reflects the run — passing — `tests/api/test_admin_weather_providers.py::test_manual_fetch_is_queued_with_202`, `test_manual_fetch_requires_platform_admin_full_mode`, `test_manual_fetch_is_queued_for_a_platform_lead_through_the_real_gating` (#3097)
- **acceptance-5** — router test: 409 with held lock, 429 + `Retry-After` within cooldown — passing — `test_manual_fetch_is_refused_with_409_while_a_fetch_runs`, `test_manual_fetch_is_refused_with_429_and_retry_after_within_the_cooldown` (#3097)
- **acceptance-6** — status endpoint test against the dedicated status document — passing — `test_fetch_status_reflects_the_recorded_runs`, `tests/integration/test_weather_fetch_status_repository.py` (#3097)
- **acceptance-7** — `mkdocs build --strict` + review of the spec diffs — passing — spec diffs (REQ-046/005/037/047/056) reviewed in the two security-review rounds of #3097; `mkdocs build --strict` on develop a958541c6 (2026-11-23): no link or nav warning — its only 45 warnings are the git-revision-date plugin on the locally generated, git-ignored catalog pages (docs/*/skills, agents, tags)

## Consistency notes

**Tenant-beat classification (drift, proceed).** Established:
`tenant_gate.py:70,72` lists frost and irrigation in `TENANT_WRITING_BEATS`;
removing their beats fails `test_beats_skip_inactive_tenants.py:114,129`.
Both tasks keep their own `ActiveTenants` check
(`frost_forecast_tasks.py:44,51`), so tenant isolation is preserved; the
classification and guard tests are updated in the same change (REQ-056 AK-07).

**MT-051 guard (drift, proceed).** Established:
`test_every_task_is_scheduled_or_dispatched.py:178` and
`test_beats_skip_inactive_tenants.py:125` require `fetch_weather_forecasts` in
the beat schedule. Operator decision 2026-11-17: the due-check lives inside
the fetch task (hourly beat, early return), so both stay valid.

**Season evaluation (drift, proceed).** Established:
`tasks/__init__.py:684`, `season_tasks.py:7` and `REQ-047:411` anchor the
06:30 season evaluation to the 06:00 fetch. Operator decision 2026-11-17: it
keeps its daily slot and reads the latest stored forecast; the anchoring text
is removed.

**Spec anchors on 06:00 (drift, proceed).** Established: `REQ-005:121`,
`REQ-047:411`, `REQ-037:337,386,508` fix the old schedule; all are updated
(acceptance-7).

**Undefined success (drift, proceed).** Established:
`weather_tasks.py:89-100` reports `ok` even when every site errored and never
uses its `max_retries`. Operator decision 2026-11-17 defines success
(acceptance-3).

**Refusal status codes (drift, proceed).** Established: `NFR-007:722`
mandates `Retry-After` on rate-limit responses; `NFR-006:250,252` define 409
and 429. Adopted in acceptance-5. The "running" lock is held by the fetch task
itself, so a scheduled run in progress also blocks a manual one — an
inference, unestablished until implemented.

**Reusable building blocks (prior-art, proceed).** Established: Redis
`SET NX EX` + `ttl()` (`step_up_code_store.py:199-201`,
`rendition_dispatch_claims.py:89`) for lock and cooldown; `_is_fresh`
(`climate_tasks.py:108-117`) for the due-check; the `fetch_timeout_s`
layering (`weather_settings_service.py:174-176,224-225`) for the interval;
async admin triggers with 202 (`admin/pests/router.py:116-122`).

**Status storage (decision).** Operator decision 2026-11-17: a dedicated
status document written only by the fetch task, avoiding a read-modify-write
race with admin PUTs on the `SystemSettings` singleton
(`weather_settings_service.py:209-234`); the race itself is unestablished
(not measured).

**Idempotency (prior-art, proceed).** Established: frost is idempotent per
`(site_key, expected frost date)` (`frost_forecast_tasks.py:7`), irrigation
upserts per site/run/day (`irrigation_tasks.py:9,170`).

## Risks

- Fetch times no longer sit at 06:00; users who relied on a morning frost warning get it after whichever fetch first sees the frost.
- Up to four fetches per day raise OpenWeatherMap key usage fourfold; the 6 h minimum bounds it.
- The hourly beat tick adds 24 cheap task runs per day.

## References

- Issue #2934, roadmap item R-18; split-out #3002 (sensor precipitation)
- `project/requirements/weather-fetch-interval.md`
