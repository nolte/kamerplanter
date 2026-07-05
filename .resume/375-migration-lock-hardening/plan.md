# Plan — Issue #375: Harden the migration advisory lock

**Branch:** `fix/375-migration-lock-hardening`
**Worktree:** `~/repos/.worktrees/kamerplanter/375-migration-lock-hardening`
**Issue:** https://github.com/nolte/kamerplanter/issues/375 (follow-up to #374, versioned migration framework)

## Goal

Make the advisory lock in the versioned migration framework safe under
multi-replica startup where a migration can run longer than `LOCK_TTL_SECONDS`
(300 s). Close all four review findings from the #374 pre-merge review:

1. Lock carries no owner / fencing token (`framework/tracking.py:109-142`).
2. Losing replica continues startup without a barrier (`framework/runner.py:165-177`).
3. `v0004_backfill_tenant_key` is recorded as applied even on a no-op when no
   default tenant is resolvable (`versions/v0004_backfill_tenant_key.py:41-71`).
4. Checksum drift detection hashes only `up()` (`framework/base.py:52-60`).

None block single-replica operation; this is net-hardening. Scope is the
migration framework only — no schema, no API, no frontend.

## Current state (researched)

- `acquire_lock` inserts `{_key: "__lock__", acquired_at: <iso>}`; on insert
  clash it reads the existing doc, and if `_is_stale` (older than TTL) does a
  blind `col.replace()`. `release_lock` does a blind `col.delete()`. Neither
  checks who owns the lock → the three race sub-bugs in finding 1.
- `run_pending_migrations` catches `MigrationLockError`, logs
  `migrations_locked_by_other_runner_skipping`, returns `[]` → startup proceeds
  against un-migrated data (finding 2).
- `backfill_tenant_key(db)` returns `{"total_updated": 0, "warnings": 0}` both
  when there was genuinely nothing to backfill AND when
  `_resolve_default_tenant` returned `None` (logs `.error` then returns). The
  v0004 `up()` can't currently distinguish the two, so the runner records it
  applied either way (finding 3).
- `Migration.checksum()` hashes `inspect.getsource(type(self).up)` only —
  edits to `down()` or module-level helpers are invisible to M-7 (finding 4).
- Tests: `tests/unit/migrations/framework/` with a dict-backed `FakeCollection`
  / `FakeDatabase` in `conftest.py`; lock tests in `test_lock.py`, runner tests
  in `test_runner.py`. `FakeCollection` supports insert/get/has/delete/replace/all.

## Design decision (load-bearing) — OPEN QUESTIONS to confirm before coding

### D1 — Owner token + fencing (finding 1)
Store a `owner` uuid in the lock doc. `acquire_lock` generates a uuid, writes it
into the doc, and returns it (or a small handle). Stale-takeover `replace()`
only overwrites a lock whose `_is_stale`; `release_lock(db, owner)` only
`delete()`s when the stored owner matches ours. Wrap the replace/delete
races (`DocumentReplaceError`, `DocumentDeleteError`, missing doc) as
`MigrationLockError` / graceful skip instead of crashing.
- **OPEN Q1:** `release_lock` signature changes from `(db)` to `(db, owner)`.
  Runner's `finally: release_lock(db)` and downgrade path must thread the owner
  through. Confirm: return the owner string from `acquire_lock` and pass it to
  `release_lock`, vs. return a small `LockHandle` dataclass. → lean: return the
  owner **string** (minimal surface, matches current return of the lock doc).

### D2 — Losing-replica barrier (finding 2)
When `run_pending_migrations` catches `MigrationLockError`, don't return `[]`
immediately. Poll `tracking.current(db)` / `applied_versions` against the head
version of the discovered migration set until they match (winner finished), with
a bounded timeout and sleep interval; on timeout, raise (fail readiness) rather
than serve un-migrated data.
- **OPEN Q2:** wait-and-recheck loop vs. fail-fast readiness. Recommendation:
  **bounded wait loop** (interval ~2 s, timeout derived from `LOCK_TTL_SECONDS`
  plus margin), then raise on timeout. Confirm timeout budget + whether the
  startup path can tolerate a blocking sleep (it is synchronous today).
- **OPEN Q3:** how to compare "reached head" — the losing replica knows the full
  migration list (`MigrationRunner._migrations`); head = max version. Barrier
  succeeds when `tracking.applied_versions` ⊇ that set. Confirm.

### D3 — v0004 no-op recording (finding 3)
Make `backfill_tenant_key` signal "no tenant resolved" distinctly (e.g. a
`resolved_tenant: bool` / sentinel in stats), and in v0004 `up()` raise (so the
migration is NOT recorded applied) when no tenant was resolvable AND orphaned
docs exist — so a later boot with a tenant retries it.
- **OPEN Q4:** raising aborts startup (M-4 fatal). Is that acceptable for the
  light-mode-with-orphans edge, or should it record `status="skipped"` and stay
  pending? Recommendation: return a report that the runner treats as
  **not-applied** (leave pending) rather than hard-fail, so normal boots are
  unaffected. Confirm the mechanism (runner needs to skip `tracking.record` when
  a migration reports it did no work *because* a precondition was unmet).

### D4 — Whole-module checksum (finding 4)
Change `checksum()` to hash the whole migration module source
(`inspect.getsource(inspect.getmodule(type(self)))`) or the whole class, not
just `up`. This is a **checksum-format change** → every already-applied
migration will show drift on first boot after deploy (M-7 logs a warning only,
non-fatal), which is acceptable but must be called out in the PR.
- **OPEN Q5:** hash whole module vs. whole class. Recommendation: whole class
  (`inspect.getsource(type(self))`) — captures `up`, `down`, and class-level
  helpers without pulling in unrelated module churn. Confirm.

## Work steps

1. D1: owner token in `tracking.acquire_lock` / `release_lock` + race→`MigrationLockError`.
2. D1 tests: stale-takeover-with-wrong-owner, release-only-own, replace-race → skip.
3. D2: barrier in `run_pending_migrations` (bounded wait or fail readiness).
4. D2 tests: losing replica waits then returns once head reached; timeout raises.
5. D3: distinct "no tenant resolved" signal + runner leaves v0004 pending.
6. D3 tests: no-op-without-tenant stays pending; normal backfill records applied.
7. D4: whole-class checksum + adjust any checksum-format assertions in tests.
8. Full backend gate: `ruff`, `pytest` (migrations suite + smoke), fix drift.
9. Update MEMORY note + open PR to develop via `pull-request-create`.

## Invariants / guardrails (from CLAUDE.md + NFR-016 / ADR-005)

- Source code English only (NFR-003); docs German.
- Backend style guide: 5-layer, structlog, bound AQL params (no interpolation).
- M-3 idempotent, M-4 fatal-on-failure, M-5 dry-run writes nothing,
  M-6 honest reversibility, M-7 immutable-applied (checksum), M-8 single-runner lock.
- Never weaken the single-runner guarantee to fix the barrier.
- Commit only from the worktree (feature branch); primary checkout stays on develop.
- Co-Authored-By trailer on commits; English PR/commit text.

## Status / resume-anchor checklist (next session resumes at first unchecked)

- [x] Requirement captured via `/nolte-shared:requirements-elicit`; OPEN Q1–Q5 resolved
      → `project/requirements/migration-lock-hardening.md` (U_gate 0.88). Q1=owner string,
        Q2=bounded wait-loop, Q3=applied⊇head, Q4=leave-pending-don't-record, Q5=whole-class.
- [x] D1 implemented (owner token + race handling) in `tracking.py`
      → `acquire_lock` returns owner uuid; stale takeover is `_rev`-checked CAS;
        `release_lock(db, owner)` owner+rev fenced; races → `MigrationLockError`/swallowed.
        Fake gained `_rev`/CAS semantics.
- [x] D1 tests green → `test_lock.py` rewritten (owner token, CAS race, fenced release).
- [x] D2 implemented (losing-replica barrier) in `runner.py`
      → `_await_head` polls `applied_versions ⊇ head`; timeout → `MigrationBarrierTimeoutError`
        (new). `BARRIER_TIMEOUT_SECONDS = LOCK_TTL*2`, poll 2s.
- [x] D2 tests green → wait-until-head, poll-count, timeout-raises.
- [x] D3 implemented (v0004 no-op stays pending)
      → `backfill_tenant_key` signals `tenant_resolved`; v0004 `up()` returns
        `precondition_unmet=True` when no tenant + orphans; runner leaves it + successors
        pending (M-1). New `MigrationReport.precondition_unmet` field.
- [x] D3 tests green → unmet-stays-pending, retry-records-applied.
- [x] D4 implemented (whole-class checksum) → `base.py` hashes `inspect.getsource(type(self))`.
- [x] Full backend gate green → ruff check + format clean; `pytest tests/unit` 3189 passed
      (162 migration tests incl. new lock/barrier/precondition).
- [ ] PR opened to develop (`pull-request-create`), links #375
