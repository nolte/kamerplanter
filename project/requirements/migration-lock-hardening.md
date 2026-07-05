# Requirements — Migration Advisory-Lock Hardening (Issue #375)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (authoritative source at
claude-shared/spec/project/requirements-elicitation/en.md).
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

- **Issue:** https://github.com/nolte/kamerplanter/issues/375 (follow-up to #374, versioned migration framework)
- **Branch / worktree:** `fix/375-migration-lock-hardening`
- **Plan:** `.resume/375-migration-lock-hardening/plan.md`
- **Governing spec:** NFR-016 / ADR-005 (versioned migration framework, invariants M-1…M-8)

## Bounded context

- **What:** Harden the cross-replica advisory lock in the versioned migration framework
  (`app/migrations/framework/`) so multi-replica startup stays correct when a migration runs
  **longer than `LOCK_TTL_SECONDS` (300 s)**. Close the four pre-merge review findings from #374:
  (1) the lock carries no owner/fencing token; (2) the replica that loses the lock race continues
  startup with no barrier, serving traffic against un-migrated data; (3) `v0004_backfill_tenant_key`
  is recorded applied even on a no-tenant no-op, so orphaned legacy docs are never backfilled later;
  (4) checksum drift detection hashes only `up()`, missing edits to `down()` or class helpers.
- **For whom:** Operators running **multi-replica** production deployments of the backend. This is
  net-hardening — `develop` had no lock at all before #374 and single-replica boots are already safe;
  none of the four findings block single-replica operation.
- **Explicitly out of scope:** No schema, API, or frontend changes. Migration framework only
  (`framework/tracking.py`, `framework/runner.py`, `framework/base.py`,
  `versions/v0004_backfill_tenant_key.py`, `backfill_tenant_key.py`, framework tests). The
  single-runner guarantee (M-8) MUST NOT be weakened to satisfy the losing-replica barrier.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `5`
  (spec defaults; unchanged — the requirement arrived code-grounded with four concrete findings and
  file:line references, so the default risk posture applies. The only genuine specification
  uncertainty lived in the five design questions Q1–Q5, all resolved authoritatively).
- `U_gate = min_d c_d` over required dimensions = **0.88**
- Termination: `saturation` (every required dimension ≥ `τ_high`; Q1/Q3/Q5 were withheld as
  individual turns — low EVPI, clear best answers — and folded into one confirmation, while Q2 and
  Q4, the load-bearing trade-offs, were forced as explicit decisions).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Four findings enumerated verbatim from the issue + grounded against `tracking.py:109-142`, `runner.py:165-177`, `base.py:52-60`, `v0004`; teach-back of the four fixes accepted |
| `non_functional` | yes | 0.88 | interpretation | Invariants confirmed (M-1 linear, M-3 idempotent, M-4 fatal, M-7 immutable-applied, M-8 single-runner never weakened; EN source per NFR-003; bound AQL params) |
| `constraints` | yes | 0.90 | interpretation | Multi-replica + `LOCK_TTL_SECONDS=300` + python-arango CAS (`_rev`) semantics grounded against driver exceptions (`DocumentReplaceError`/`DocumentRevisionError`/`DocumentDeleteError`) |
| `domain_objects` | yes | 0.90 | interpretation | `schema_migrations` `__lock__` doc, owner uuid, `MigrationReport`, `applied_versions`/head set enumerated from source |
| `actors` | yes | 0.90 | interpretation | Winning runner, losing replica(s), stale-takeover replica, startup path (`run_pending_migrations`), CLI — all identified from code |
| `acceptance_criteria` | yes | 0.85 | specification→resolved | Per-finding done-conditions confirmed; backend gate (ruff + pytest migrations/smoke) is the verifier |
| `edge_cases` | yes | 0.88 | specification→resolved | Q2 (long-migration barrier timeout), Q4 (light-mode-with-orphans no-tenant), stale-takeover CAS race, get→delete window — decided authoritatively |
| `scope_boundaries` | yes | 0.90 | specification→resolved | Authoritative answer: migration framework only; no schema/API/frontend; M-8 never weakened |

_Self-consistency (`k≥2`) evidence event:_ two independent sketches of the losing-replica barrier
(Q2) **diverged** — sketch A (bounded wait-loop polling `applied_versions ⊇ head`, raise on timeout)
vs. sketch B (fail-fast readiness, rely on orchestrator restart backoff). The divergence is the
ambiguity signal; it was resolved to the wait-loop by authoritative answer, with the fail-fast
behaviour retained only as the timeout escape hatch.

## Requirements

<!-- EARS/CNL form; tagged confirmed/assumed with traceability. -->

- **R1 (finding 1 — owner token)** — WHEN `acquire_lock` is called, the framework SHALL generate a
  per-runner owner uuid, store it in the `__lock__` document, and return it to the caller.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue #375 §1 + Q1 (return owner as plain string)

- **R2 (finding 1 — stale takeover is atomic)** — WHEN a runner observes a stale lock (older than
  `LOCK_TTL_SECONDS`), the framework SHALL take it over with a revision-checked `replace` so that if
  another replica took the same stale lock first, the revision mismatch raises and is surfaced as
  `MigrationLockError` (lock held) rather than two runners migrating concurrently.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: issue #375 §1 (two-replica stale race) + M-8

- **R3 (finding 1 — fenced release)** — WHEN `release_lock(db, owner)` is called, the framework SHALL
  delete the lock only when the stored owner matches `owner` and the revision is unchanged since it
  was read; a foreign or superseded lock SHALL be left intact, and a delete/replace race SHALL be
  swallowed rather than crash startup.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue #375 §1 (slow runner deletes new owner's lock) + Q1

- **R4 (finding 2 — losing-replica barrier)** — WHEN `run_pending_migrations` catches
  `MigrationLockError`, the framework SHALL block startup and re-attempt `upgrade` at a bounded
  interval until it succeeds (the winner released the lock), and only then complete startup.
  Re-running `upgrade` — rather than polling for a fixed head — is the barrier because it is
  idempotent (M-3) and correctly leaves a legitimately-pending migration pending: a former loser
  that acquires the lock re-evaluates preconditions and behaves exactly like the winner.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue #375 §2 + Q2 (bounded wait) + pre-merge review of PR #386 (see risk note below)

- **R5 (finding 2 — barrier timeout fails readiness)** — WHEN the barrier of R4 exceeds its timeout
  (derived from `LOCK_TTL_SECONDS` plus margin) without the lock being released, the framework SHALL
  raise `MigrationBarrierTimeoutError` so startup/readiness fails and the orchestrator retries,
  rather than serve traffic against un-migrated data.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: issue #375 §2 + Q2 timeout escape hatch

- **R6 (finding 3 — v0004 no-op stays pending)** — WHEN `v0004_backfill_tenant_key` runs and no
  default tenant is resolvable **while orphaned tenant-scoped docs still exist**, the migration SHALL
  report a precondition-unmet result and the runner SHALL NOT record it applied (nor any later
  migration), so a subsequent boot with a resolvable tenant retries it. A genuine no-op (no tenant
  **and** no orphans) SHALL still be recorded applied.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue #375 §3 + Q4 (leave pending, don't record; no hard fail)

- **R7 (finding 4 — whole-class checksum)** — WHEN a migration's checksum is computed, the framework
  SHALL hash the whole migration **class** source (capturing `up`, `down`, and class-level helpers),
  not `up()` alone.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue #375 §4 + Q5 (whole class, not module)

- **R8 (invariant — single-runner preserved)** — The barrier of R4/R5 SHALL NOT weaken the M-8
  single-runner guarantee: exactly one runner holds the lock and applies migrations at any instant;
  a losing replica that later acquires the released lock becomes the (still single) runner.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan invariants + Q2

- **R9 (deploy note — checksum-format change)** — WHEN the R7 change first ships, every
  already-applied migration will show one-time checksum drift (M-7 logs a warning only, non-fatal);
  this SHALL be called out in the PR.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan D4 + Q5

## Surviving assumptions / open risks

- **Blocking startup sleep (R4).** The startup path is synchronous today; the barrier adds a bounded
  blocking retry. Assumed acceptable (confirmed via Q2). Residual: a genuinely stuck winner makes
  losing replicas wait up to the timeout before failing readiness — mitigated by the R5 escape hatch.
- **Barrier design corrected in pre-merge review (PR #386).** The first implementation polled
  `applied_versions ⊇ head`; a review pass caught that in the R6 no-tenant edge the winner leaves
  v0004+ pending and never reaches head, so losing replicas would wait the full timeout and
  crash-loop. The retry-`upgrade` barrier (R4) closes this and additionally reclaims a stale lock
  from a *crashed* winner (the poll design did not), since `acquire_lock` takes over a stale lock.
- **Light-mode-with-orphans leaves v0004+ pending (R6).** Not recording v0004 leaves it and every
  later migration pending until a boot with a resolvable tenant (required to preserve M-1 linear
  history). Assumed acceptable for this rare edge (confirmed via Q4); self-heals on the next
  tenant-bearing boot. Below `τ_high` risk: none of the migrations after v0004 apply in that window.
- **Barrier timeout constant** (`LOCK_TTL_SECONDS × 2`, poll 2 s) is an engineering default, not a
  measured value; revisit if real long-migration deploys show it too tight or too loose.
</content>
