# Pre-analysis #1773 — plaintext account keys / addresses in privacy log lines

Group: 2026-09-25-privacy-retention-hygiene (Mode A). Class: **bug** (secondary security/privacy). Route: implement directly.
Requirements gate: operator override — requirement = issue acceptance + #1700 rule (erasure logs carry `subject=` salted hash) + NFR-011 (logs have no retention rule).

## Cause verification (established)
Prototype AST scan (scratchpad scan.py) over the guarded surface, before any change:
privacy_service.py 19 kwargs (incl. :1139/:1198/:1208 `user_key=export.user_key`, :481-483 `old_email`/`new_email`), auth_service.py 10 (incl. :375 `user_registered email=`), data_subject_service.py 6, user_service.py 1; storage adapters `storage_delete_object key=` (s3_adapter.py:266, local_fs_adapter.py:277) with key `privacy/exports/<user_key>/<export_key>.json` (data_export_engine.py:683). Confirmed; the issue's list is a subset of the class.
Repo-wide the same scan finds ~86 kwargs in 21 files — the remainder outside privacy/auth/retention/storage is out of scope (follow-up issue).

## Work packages
| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| P1 | one helper | `ErasureEngine.log_subject(user_key, salt)` = salted tombstone hash, `anon_unavailable` on missing/short salt; `PrivacyService._erasure_log_subject` delegates | erasure_engine.py, privacy_service.py | nolte-engineering:fullstack-developer | – |
| P2 | privacy lines | every `user_key=` → `subject=`; emails → `*_email_sha256=email_digest(...)`; unit test per issue-listed line captures logs, asserts plaintext absent (red first) | privacy_service.py, data_subject_service.py, user_service.py | same | P1 |
| P3 | auth lines | same for auth_service (salt injected via dependencies) | auth_service.py, dependencies.py | same | P1 |
| P4 | storage | adapters log a redacted key (user segment of `privacy/exports/` masked) | storage adapters (+ helper) | same | – |
| P5 | class guard | AST guard over the module set, refusing kwarg names/values naming an account key or address; red-first against develop; docstring names spellings it cannot see | tests/unit/guards/ | same | P2-P4 |
