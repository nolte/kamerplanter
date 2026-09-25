# Pre-analysis #1772 — R-06 purge never enforced, R-02 threshold drift

Group: 2026-09-25-privacy-retention-hygiene (Mode A). Class: **bug** (secondary docs). Route: implement directly (bounded, one strand).
Requirements gate: operator override (2026-09-24/25 full autonomy) — requirement = issue acceptance + NFR-011 R-02/R-06/§4/AK-11/AK-13, REQ-023 AK-17, REQ-025 AK-10.

## Cause verification (established)
- R-06: `grep -rn "erasure_requests\|ERASURE_REQUESTS" src/backend/app | grep -i "remove\|delete\|purge"` → no remove path; only `collections.py:2218-2221` index defs and `v0054` read. `ErasureStep(... "requested_erasure" edge, user_field="_from")` (erasure_engine.py:408) removes the user's edges at erasure, the record itself stays forever. Confirmed.
- "other R-06 audit rows": `PSEUDONYMIZE_AUDIT_COLLECTIONS` = `erasure_requests` + `mcp_audit_log`; `mcp_audit_log` already has its own window (`settings.mcp_audit_retention_days=90`, beat `mcp.cleanup_expired_audit_log`) under REQ-033 — not R-06. **Refines the issue:** R-06 covers `erasure_requests` only.
- R-02: `auth_tasks.py:51` `timedelta(hours=72)`; spec: NFR-011 R-02 "7 Tage", §4 `UNVERIFIED_ACCOUNT_DAYS: int = 7`, AK-11; REQ-023 l.1109 + AK-17 "7 Tagen"; docs 7 d. **Decision: 7 days canonical (spec wins), code aligns.**

## Work packages
| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| P1 | R-02 literal | `settings.retention_unverified_account_days` (default 7, ge=1; env `RETENTION_UNVERIFIED_ACCOUNT_DAYS`), task cutoff = now − setting; red-first unit test pins default 7 and cutoff | settings.py, auth_tasks.py, tests/unit/tasks | nolte-engineering:fullstack-developer | – |
| P2 | R-06 purge | `settings.retention_erasure_audit_retention_years` (default 1, ge=1 floor; env `RETENTION_ERASURE_AUDIT_RETENTION_YEARS`); repo `delete_completed_before(cutoff_iso)` removes only `completed` rows with `completed_at < cutoff` + their `requested_erasure` edges; `PrivacyService.purge_expired_erasure_records(now)`; Celery `retention.purge_expired_erasure_records` daily beat; red-first unit through task→service; integration against ArangoDB (old completed purged; young completed, partially_completed, scheduled, in_progress kept) | erasure_repository(+interface), privacy_service.py, retention_tasks.py, tasks/__init__.py, dependencies.py, tests | nolte-engineering:fullstack-developer | P1 (settings file) |
| P3 | Art. 13 policy | `get_privacy_policy` lists unverified accounts (R-02) and erasure records (R-06) from the same settings; R-04→R-03 label for IP | privacy_service.py | same | P2 |
| P4 | docs | data-retention DE/EN R-02/R-06 accurate, purge task named | docs | mkdocs-documentation | P1-P3 |

## Open question
DPO: proof retention of `unverified_cleanup` records — spec year implemented for all origins; flagged (#1767 Q4).
