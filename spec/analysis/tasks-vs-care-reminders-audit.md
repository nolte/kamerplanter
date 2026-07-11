# Tasks vs. Care Reminders — Model / Layer Duplication & Reuse Audit

> Findings report for [Issue #489](https://github.com/nolte/kamerplanter/issues/489).
> **Analysis only** — this document prescribes and performs no refactor; any code
> consolidation is a follow-up gated by these findings and the existing requirements.
> Date: 2026-07-11. Scope grounded in `develop` (`361fb50b6`).

## Executive summary

- **At the persistence level there is exactly one actionable-reminder concept: the
  `Task`.** A "care reminder" is a `Task` with `category == "care_reminder"`. There is
  **no** `CareReminder` document and **no** `care_reminders` collection. The
  care-specific collections (`care_profiles`, `care_confirmations`) store
  *configuration and event history*, not reminders. This **matches** the spec: REQ-022
  mandates exactly this and explicitly forbids a parallel reminder store.
- **The dashboard double-counts.** `open_tasks_today` and `overdue_tasks` apply **no
  category filter**, so they include care-reminder tasks; `care_reminders_due` counts
  those same tasks (`due_date <= today`). Every open care-reminder task due today or
  earlier is counted in two tiles at once, rendered side by side with no
  deduplication. The spec is **silent** on this — it is an unspecified gap, not a spec
  contradiction.
- **The real duplication is behavioural, not structural.** The data model is shared
  and spec-correct; what is duplicated is *logic*: care-reminder idempotency/dedup is
  reimplemented **five** times, "due/overdue" is defined **four** independent ways,
  recurrence is hand-rolled instead of reusing the Task recurrence engine, and
  `Task(...)` builders + instruction strings are copied between the service and the
  Celery producer.
- **Highest-value, lowest-risk fix:** exclude `category == "care_reminder"` from the
  two generic task counters (or agree an explicit "care reminders count only in their
  own tile" rule) to remove the double-count, and collapse the repeated dedup/due
  logic onto a single shared helper. Both stay strictly within REQ-006/REQ-022/REQ-009.

---

## 1. Data model — one concept or two?

**Verdict: one persisted concept (`Task`), plus care-owned *config/event* records — not a second reminder store.**

- A care reminder's persisted, tenant-scoped, due-dated form **is** a `Task` with
  `category = TaskCategory.CARE_REMINDER` (`app/common/enums.py:757`). The care
  repository states this in its own docstring
  (`app/data_access/arango/care_reminder_repository.py:77-83`): *"Care reminders are
  not stored as standalone documents … Their persisted, tenant-scoped, due-dated form
  is a care-reminder `Task` (`category == care_reminder`)."*
- Care reminders are created via the **task** repository:
  `Task(... category=TaskCategory.CARE_REMINDER ...)` then
  `self._task_repo.create_task(task)` (`app/domain/services/care_reminder_service.py:558`,
  `:566`, `:695`, `:703`).
- There is **no** `CareReminder` / `CareReminderTemplate` / `CareReminderPreset`
  Pydantic model and **no** `care_reminders` collection. Presets are Python dict
  constants in the engine (`FAMILY_CARE_MAP` at
  `app/domain/engines/care_reminder_engine.py:293`; `CARE_STYLE_PRESETS` at `:58`).

### Collections map

| Collection (`collections.py`) | Stores | Written / read by |
|---|---|---|
| `TASKS` (`:62`, `"tasks"`) | actionable items **incl.** care reminders (`category="care_reminder"`) | written+read by `ArangoTaskRepository`; **also read** by `ArangoCareReminderRepository.count_due_on` (`care_reminder_repository.py:110`) |
| `CARE_PROFILES` (`:81`) | `CareProfile` — per-plant care config/intervals/learned intervals (no `tenant_key`, no `due_date`) | `ArangoCareReminderRepository` |
| `CARE_CONFIRMATIONS` (`:82`) | `CareConfirmation` — confirm/snooze/skip event log | `ArangoCareReminderRepository` |

`CareDashboardEntry` (`app/domain/models/care_reminder.py:68-77`) is a **transient
view model** (no `_key`, never persisted).

### Field overlap vs. divergence

The two persisted stores model **different concerns**, so overlap is minimal.
`Task` (`app/domain/models/task.py:104-153`) carries execution/scheduling/workflow
fields (`due_date`, `status`, `priority`, `recurrence_rule`, `checklist`, `timer_*`,
workflow keys); `CareProfile` (`app/domain/models/care_reminder.py:9-47`) carries
*configuration* (`watering_interval_days`, `adaptive_learning_enabled`,
`*_interval_learned`, `winter_watering_multiplier`, `dormancy_*`, `care_style`) and
notably has **no `tenant_key` and no `due_date`**.

One notable modelling gap: `reminder_type` (a `ReminderType` enum,
`enums.py:887-902`) is persisted on `CareConfirmation` and `CareDashboardEntry`, but
**not** on the care-reminder `Task` — it is only encoded into the task `name` suffix
(`care_reminder_service.py:538,543`). At the `Task` level the reminder type is not a
first-class, queryable field (category is always the single value `CARE_REMINDER`).

---

## 2. Layer-by-layer duplication

The model is shared; the **logic** around it is duplicated. Map (task-side vs.
care-side, with `file:line`):

| Behaviour | Task-side (generic) | Care-side (reimplemented) |
|---|---|---|
| **Care-task dedup / idempotency** | `task_service._deduplicate_care_tasks` (`task_service.py:700-734`), applied at read in `get_task_queue`/`get_overdue_tasks` (`:679`,`:738`) | **4 inline copies:** `care_reminder_service.py:274-286`, `:540-551`, `:646-660`, and Celery `care_tasks.py:151-166` — all sharing the same `category==CARE_REMINDER AND name endswith "— {rt}" AND (open OR completed-today)` predicate |
| **Due / overdue determination** | `task_repository.get_overdue_tasks` (`task_repository.py:420-426`, `due_date < now`) | **3 independent definitions:** engine `calculate_urgency` (`care_reminder_engine.py:349-361`), AQL `count_due_on` (`care_reminder_repository.py:100-101`, `LEFT(due_date,10) <= today`), notification `notification_tasks.py:281-283` (`due_dt < today_start`) |
| **Recurrence / next occurrence** | `_create_next_recurring_task` + `_compute_next_recurrence` (`task_service.py:373-450`, iCal RRULE via `dateutil`) — driven by `Task.recurrence_rule` | Hand-rolled: `ensure_next_watering_task` (`care_reminder_service.py:626-703`) computes next due via `engine.calculate_due_date` and creates a fresh Task — **does not** use `recurrence_rule`; the two recurrence engines never meet |
| **`Task(...)` construction** | `instantiate_workflow` (`task_service.py:228-250`), `clone_task` (`:477-497`), `_create_next_recurring_task` (`:387-414`) | Duplicated builders: `care_reminder_service.py:555-565`, `:692-702`, and inline in Celery `care_tasks.py:186-197` |
| **Per-type instruction text** | — | Duplicated: module fn `care_reminder_instruction` (`care_reminder_service.py:41-54`) **and** inline dict `rt_instructions` (`care_tasks.py:172-184`) — same strings |
| **Interval selection (learned vs. base)** | — | `care_reminder_service._get_current_interval` (`:705-710`) duplicates engine `_get_interval_days` (`care_reminder_engine.py:679-693`) |
| **Tenant-scoped, orphan-guarded due query over `tasks`** | `count_open_due_on` / `count_overdue` reuse shared `_OPEN_STATUSES` (`task_repository.py:737`) + `_ORPHAN_GUARD` (`:742-748`) | `count_due_on` (`care_reminder_repository.py:93-116`) **re-inlines** the same status list and orphan guard over the same `tasks` collection instead of reusing the task-repo constants |

**Already shared (good reuse):**

- Care reminders reuse the **`Task` model** and **`ITaskRepository`** directly; the
  service holds `self._task_repo` and never owns a reminder collection.
- The **task-completion → care-confirmation bridge** lives once at the router
  (`app/api/v1/tasks/tenant_router.py:501-542`, `:553-575`): completing/skipping a
  `category=="care_reminder"` task calls back into the care service to log a
  `CareConfirmation` and schedule the next reminder.
- The **engine is pure and single-sourced** for scheduling math
  (`care_reminder_engine.py`, "no I/O"), reused by the service, the Celery producer,
  and the router.

**The core coupling signal:** `care_reminder_repository.count_due_on` has read
knowledge of the `tasks` schema/collection and duplicates the task-repo's due-count
query; the care service holds *both* `ICareReminderRepository` and `ITaskRepository`
and writes reminders through the task repo. The care stack is a *layer on top of*
tasks (as REQ-022 intends), but it reimplements task-side helpers instead of
delegating to them.

---

## 3. Dashboard counts — overlap / double counting

**Verdict: YES, the counts double-count care-reminder tasks. Proven from the filters.**

`DashboardService` declares three fields (`dashboard_service.py:48-51`) and delegates
predicates to repositories:

| Count | Method | Filter | Categories |
|---|---|---|---|
| `open_tasks_today` | `count_open_due_on` (`task_repository.py:750-778`) | `tenant` AND `status IN [pending,in_progress]` AND `due_date != null` AND `LEFT(due_date,10) == today` AND orphan-guard | **all** (no category filter) |
| `overdue_tasks` | `count_overdue` (`task_repository.py:780-802`) | same but `LEFT(due_date,10) < today` | **all** (no category filter) |
| `care_reminders_due` | `count_due_on` (`care_reminder_repository.py:73-118`) | `tenant` AND **`category == care_reminder`** AND `status IN [pending,in_progress]` AND `due_date != null` AND `LEFT(due_date,10) <= today` AND orphan-guard | **only** `care_reminder` |

The task-count queries contain **no** `FILTER doc.category != @care_category`
anywhere in `task_repository.py`. `care_reminders_due` uses `<= today`, spanning both
`== today` and `< today`, over the identical `tasks` collection with the identical
open-status set. Therefore:

- care-reminder task, `due_date == today` → counted in **`open_tasks_today`** *and*
  **`care_reminders_due`**;
- care-reminder task, `due_date < today` → counted in **`overdue_tasks`** *and*
  **`care_reminders_due`**.

Both slices are surfaced to the same page simultaneously
(`app/api/v1/dashboard/tenant_router.py:93-104`), and the frontend renders
`tasks_today` (`open_tasks_today` + `overdue_tasks`) next to `care_reminders`
(`care_reminders_due`) with **no client-side reconciliation**
(`GenericWidget.tsx:300-328`; catalog entries `dashboardWidgetCatalog.ts:103-104`,
both in `BEGINNER_WIDGETS`).

**What each count is *meant* to represent** (from labels + spec): `tasks_today` =
"Aufgaben heute" (all due/overdue work); `care_reminders` = "Pflegeerinnerungen"
(the beginner-friendly care slice). The intent is a *simplified view* of the same
work, not a disjoint set — but the numbers read as if additive, which is the
confusion the issue reports.

**Extra nuance — two divergent "care" surfaces:** the `care_reminders_due` **count**
reads care-reminder *Tasks*, whereas the `/care-reminders/dashboard` **list**
endpoint (`app/api/v1/care_reminders/tenant_router.py:12-24`) is **live-computed**
from active plants + `CareProfile`s (`care_reminder_service.py:406-421`) and never
reads tasks. The tile count and the care dashboard list can therefore disagree.

---

## 4. Requirements reconciliation (REQ-006, REQ-022, REQ-009, NFR-001)

| Observed implementation trait | Spec position | Verdict |
|---|---|---|
| Care reminder = `Task` with `category='care_reminder'` | REQ-022 §Beschreibung (l.49): *"spezialisierte Vereinfachungsschicht auf dem bestehenden Task-System … kein paralleler Reminder-Store, keine Datenbank-Duplizierung"*; REQ-006 `TaskCategory` enum includes `care_reminder` | **Matches spec** |
| Dedicated `CareReminderEngine` + `care_profiles`/`care_confirmations` collections | REQ-022 §Abgrenzung zu TaskTemplate (l.204) mandates a dedicated engine; §2 mandates the care-owned config/event collections | **Matches spec** (required, not a deviation) |
| Separate `care_reminders` dashboard widget beside `tasks_today` | REQ-009 §1.4 (l.148) **promotes** care reminders to their own `care_reminders` widget on purpose; both in beginner default set (§1.6) | **Matches spec** — the split UI is intended |
| Three separate care-reminder-flavoured counts, and generic task counts include care reminders | REQ-009 defines `tasks_overdue`/`tasks_today`/`tasks_this_week` task counters and **one** `care_reminders` widget; it defines **no** care-reminder count fields and **never** addresses task/care double-counting | **Spec silent** → the double-count is an **unspecified gap**, not a contradiction |
| Parallel service/repository *reminder store* | REQ-022 l.49 forbids a parallel reminder store | **No contradiction** — the implementation shares the `tasks` collection (see §1); only *logic* is duplicated, not the store |

**NFR-001 (5-layer):** shared business rules (generation, due-date/urgency,
recurrence, guards) belong in **Layer 3** (Domain Services / Calculation Engines /
Rule Engines, NFR-001 §2.1 l.81-86); shared persistence access belongs in **Layer 4**
via the Repository Pattern. Because tasks and care reminders share the `tasks`
collection, the task repository is the natural single access point — which is exactly
where the duplication in §2 should collapse.

**Care-reminder-only behaviour the spec genuinely requires** (so any consolidation
must preserve it, not erase it): Care-Style presets (8 indoor + outdoor), adaptive
scheduling (±1 day steps, ±30 % cap), seasonal winter multiplier, fertilizing guard,
12 reminder types, `FAMILY_CARE_MAP` fallback, one-tap confirm/snooze/skip event log,
winter-hardiness gating (Invariante D5). These live correctly in the care
engine/service; the reuse opportunity is in the *plumbing* (dedup, due-banding,
recurrence, task construction), not this domain logic.

---

## 5. Improvement & reuse recommendations (prioritized)

All options stay within REQ-006 / REQ-022 / REQ-009 and preserve the required
care-specific behaviour. Ordered by value ÷ risk. **Each is a follow-up; this issue
performs none of them.**

### P1 — Remove the dashboard double-count (low risk, high clarity gain)

The confusion in the issue ("7 overdue tasks" next to "7 care reminders due") is the
double-count. Two spec-compatible options:

- **(a) Exclude `category == "care_reminder"` from `count_open_due_on` and
  `count_overdue`** (`task_repository.py:759-802`), so `tasks_today` means
  *non-care* work and `care_reminders` owns the care slice → the two tiles become
  disjoint and additive-safe. Recommended.
- **(b) Keep the counts as-is but relabel/annotate** so the UI states the care tile
  is a subset of tasks (e.g. "davon Pflege: N"). Cheaper, but leaves overlapping raw
  numbers.

Either needs a decision recorded against REQ-009 (which is silent today). **(a)** is
the cleaner reconciliation. *Touches:* `task_repository.py`, count tests, possibly a
one-line REQ-009 clarification.

*Trade-off:* option (a) changes what `tasks_today`/`overdue_tasks` have historically
counted — verify no other consumer relies on the old "includes care reminders"
semantics before changing it.

### P2 — Single source for care-task dedup/idempotency (medium risk, removes 5-way drift)

Collapse the four inline dedup scans (`care_reminder_service.py:274-286`, `:540-551`,
`:646-660`; `care_tasks.py:151-166`) and the read-time safety net
(`task_service._deduplicate_care_tasks`) onto **one** shared helper (Layer 3/4), e.g.
a `find_open_care_task(entity_key, reminder_type, tenant_key)` on the task repository.
This also fixes the **tenant-scoping asymmetry**: today the dedup scans use
`find_by_field("entity_key", …)` which is **tenant-blind** (`base_repository.py:384-394`)
while the created task is stamped with `plant.tenant_key` — a shared, tenant-aware
lookup removes that latent cross-tenant interference.

*Trade-off:* central helper must keep the "completed today counts as satisfied"
recency rule; regression-test all three service paths + the Celery path.

### P3 — Reuse the Task recurrence engine instead of hand-rolled next-task creation (medium risk)

`ensure_next_watering_task` (`care_reminder_service.py:626-703`) reimplements
recurrence imperatively. Where a care reminder's cadence is a fixed interval, express
it via `Task.recurrence_rule` and let `task_service._create_next_recurring_task`
(`task_service.py:373-415`) generate the next occurrence — one recurrence engine
instead of two. Adaptive/seasonal intervals that can't be expressed as a static RRULE
stay in the care engine (the engine remains the interval authority).

*Trade-off:* adaptive learning mutates the interval between occurrences, which a
static RRULE can't capture — scope this to the fixed-interval reminder types only, or
have the care engine rewrite the rule on confirmation.

### P4 — De-duplicate task construction + instruction strings (low risk, cleanup)

Factor the duplicated `Task(...)` builders and the two copies of the per-type
instruction text (`care_reminder_service.care_reminder_instruction` vs.
`care_tasks.py:172-184`) into one factory (e.g. `build_care_reminder_task`). Pure
DRY; no behaviour change. Also lets the daily Celery path and the service path never
drift.

### P5 — Consider promoting `reminder_type` to a first-class Task field (low priority)

Today reminder type is only in the task `name` suffix + always-`CARE_REMINDER`
category. A queryable `reminder_type` field would let dedup/queries filter precisely
instead of string-matching the name. Larger surface (model + migration); defer unless
P2 needs it.

### Explicitly out of scope / not recommended

- Merging the care engine into task_service, or removing the `care_reminders`
  widget — both contradict REQ-022/REQ-009 (dedicated engine + dedicated widget are
  *required*).
- Introducing a separate reminder store — forbidden by REQ-022 l.49.

---

## Prioritized recommendation (one line)

**Do P1 first** (remove the dashboard double-count, the user-visible symptom), then
**P2** (single tenant-aware care-task dedup helper, which also closes the
tenant-blind dedup gap); P3–P5 are DRY/consistency follow-ups. None require any spec
change beyond a one-line REQ-009 clarification of what the two count tiles mean.

## Suggested follow-up issues

1. `fix(dashboard): exclude care reminders from generic task counts (REQ-009 clarify)` — P1
2. `refactor(care): single tenant-aware care-task dedup helper` — P2 (note: closes a latent cross-tenant dedup gap)
3. `refactor(care): reuse Task recurrence engine for fixed-interval reminders` — P3
4. `chore(care): DRY care-reminder Task builder + instruction strings` — P4
