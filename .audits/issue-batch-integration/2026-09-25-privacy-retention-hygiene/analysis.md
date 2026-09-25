# Group pre-analysis: 2026-09-25-privacy-retention-hygiene

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. Never on the default branch, never in `.gitignore`.

## Scope of this analysis

**Research question:** Do #1772 and #1773 share one change — personal identifiers of a data
subject outliving the retention NFR-011 declares for them — and what exactly has to change so
the declared periods (R-02, R-06) are enforced and the privacy/auth/retention log lines stop
carrying the plaintext identifier?

**The group's single logical change, in one sentence:** Personal identifiers of a data subject
no longer outlive the retention NFR-011 declares for them — erasure records are purged after
R-06, unverified accounts follow the spec's R-02 period from one setting, and the
privacy/auth/retention log lines carry a salted subject reference instead of the account key or
address.

**Out of scope:**
- Log lines outside the privacy/auth/retention/storage surface that name a subject
  (notification_service, email adapters, tenant_service, migrations, pest/diary services …) —
  listed in the class sweep, filed as a follow-up issue, not repaired here.
- The rest of the `RETENTION_*` env-var block in `docs/*/guides/data-retention.md` and the
  "master task" diagram, which describe settings/tasks the code does not have (pre-existing
  NFR-018 §1 drift) — follow-up issue; only the R-02/R-06 rows become true here.
- Changing the export bundle's storage-key shape (`privacy/exports/<user_key>/…`): the stored
  path lives 72 h (R-05); only the log line outlives it.
- DPO decisions (#1767 questions 1–5).

**Tier:** 2 — one repository, no published contract (no API/schema change; two new settings
with spec-given env names).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1772 | bug (secondary: docs) | thematic coupling (NFR-011 retention of personal data) + shared touch surface | no REMOVE on `erasure_requests` anywhere in `src/backend/app` (grep, only v0054 read + index defs); `auth_tasks.py:51` `timedelta(hours=72)` vs NFR-011 R-02 / REQ-023 §AK-17 "7 Tage" |
| #1773 | bug (secondary: security/privacy) | thematic coupling + shared touch surface | `privacy_service.py:1139/1198/1208` `user_key=export.user_key`; `:481-483` `old_email`/`new_email`; `auth_service.py:375` `email=email`; `s3_adapter.py:266`, `local_fs_adapter.py:277` `key=` with `privacy/exports/<user_key>/…` (`data_export_engine.py:683`) |

**Dependency ordering:** independent; implemented #1772 → #1773 on one strand because both
edit `privacy_service.py` and `dependencies.py` (sequential on one tree).

**Shared touch surface:** `src/backend/app/domain/services/privacy_service.py`,
`src/backend/app/common/dependencies.py`, `src/backend/app/config/settings.py`,
`docs/{de,en}/guides/data-retention.md`.

## Mode decision

**Mode:** A — single strand.

**Reason:** neither member has uncertain acceptance or an outstanding external review that
could reject it; the open DPO question (#1767 Q4) does not block #1772 — the spec's stated
period is implemented and the question flagged. Overlapping touch surface favours one strand.

## Structural finding

**Cluster shape:** class cluster.

**Root cause or defect class:** *a retention rule declared in NFR-011 with no mechanical
enforcement behind it* — R-06 names a period no task applies; R-02's period lives as a literal
in the task instead of one setting; and log lines (a store with no retention rule of its own)
receive the plaintext identifier the erasure pipeline pseudonymises everywhere else (#1700
applied the rule to the erasure lines only, the sibling lines in the same service were left).

**Process finding:** the #1700 fix repaired sites (the erasure log lines) without a class guard,
so the same file kept 19 plaintext `user_key=` log kwargs. Preventive change is this group's AST
guard. No new process issue: the defect-class-guards spec (G1/G3) already requires the guard; the
miss was not applying it in #1700.

**Preventive change:** `tests/unit/guards/test_privacy_logs_carry_no_plaintext_subject.py` —
enumerates every structlog call in the privacy/auth/retention/storage modules and refuses a
kwarg that names or passes an account key or address.

**Recurrence fed to the portfolio loop:** "site fix without class guard" — recurring in MEMORY
(#948 sibling drift, #1402); no new count here beyond the note.

## Completeness matrix

| Member | Source | Spec | Tests | Docs | Config / Helm | Generated index |
|---|---|---|---|---|---|---|
| #1772 | `settings.py` two settings (`retention_unverified_account_days=7`, `retention_erasure_audit_retention_years=1`, floors); `auth_tasks.cleanup_unverified_accounts` reads setting; `erasure_repository.delete_completed_before`; `PrivacyService.purge_expired_erasure_records`; `retention_tasks.purge_expired_erasure_records` + beat entry; privacy policy lists R-02/R-06 (and fixes R-04→R-03 label); check: unit + integration tests below | not applicable — spec is canonical and already says 7 d / 1 y; no spec text changes (env names follow NFR-011 §4) | red-first unit: task cutoff from setting, purge task through service, setting floors; integration: repo purge against ArangoDB; check: `pytest tests/unit/... tests/integration/...` | `docs/{de,en}/guides/data-retention.md` R-02/R-06 rows + purge task + env vars that now exist; `docs/*/reference/environment-variables.md`; check: `mkdocs build --strict` | not applicable — defaults carry the spec periods; no Helm value needed (checked `helm/` for PRIVACY_* — none set) | not applicable — no generated catalog covers settings |
| #1773 | `ErasureEngine.log_subject` (salted tombstone, `anon_unavailable` fallback); privacy_service/data_subject_service/auth_service/user_service/storage adapters use it or `email_digest`; storage adapters log `loggable_storage_key(key)`; check: unit tests per listed line | not applicable — REQ-025/NFR-011 already demand it (#1700 rule) | red-first unit per listed line (capture structlog, assert plaintext absent); AST class guard red-first against develop; check: guards lane | `data-retention.md` note on log pseudonymisation; check: mkdocs build | `dependencies.py` wires `tombstone_salt` into AuthService/UserService; check: unit | not applicable |

## Risks

- R-02 7 d replaces 72 h: unverified accounts now live ~4 days longer — spec wins (CLAUDE.md), but it is a behaviour change to call out.
- Deleting audit rows is irreversible: purge only `status == completed` with `completed_at` older than the period; open/partial requests never selected.
- Log correlation: dev/e2e without salt get `anon_unavailable`; e2e compose sets the salt.
- Lane-input records may flag new reads (#1747: in-filter reads are notes).

## Open questions for the operator

- DPO (#1767 Q4 / #1772 AK-2): proof retention of an `unverified_cleanup` erasure — spec's R-06 year implemented for every origin; open.

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|

## Deviations

| Member | Kind | What changed |
|---|---|---|
