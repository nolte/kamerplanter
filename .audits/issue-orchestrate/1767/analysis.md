# Pre-analysis — issue #1767

- Issue: #1767 "erasure: remaining GDPR gaps from the #1761/#1766 reviews" (author `nolte`, trusted — repository owner)
- Classification: `bug` (secondary `security`) — erasure/retention entry points report or record success that is not proven by what they removed.
- Requirements gate: **operator override** (operator authorisation 2026-09-24/25, full autonomy). The issue states defect + acceptance precisely; no elicitation artefact.
- Base: stacked on #1766 head `ffd4c2ae2` (open, automerge) — same erasure code; rebase onto develop when it lands.

## Claim verification (file:line, measured on `ffd4c2ae2`)

| Item | Verdict | Evidence |
|---|---|---|
| GDPR-004 admin delete discards report | **established** | `app/api/v1/admin/platform/router.py:287` `run_async(privacy_service.erase_account(key))` — report discarded, no `unreached` gate, no `ErasureRequest` record |
| GDPR-004 unverified cleanup discards report | **established** | `app/tasks/auth_tasks.py:57` same call; only a counter in the task result |
| SEC-003 race on admin delete | **established (cause re-measured)** | admin path does not deactivate/revoke before Phase 0 (`router.py:275-287` vs self-service `privacy_service.py:533-545`) → an active session can upload between the storage phases and the ArangoDB plan; no claim on the request → two concurrent DELETEs, or DELETE vs the daily beat (`_finalize_erasure` marks `in_progress` unconditionally, `privacy_service.py:1316`), run the erasure twice concurrently |
| GDPR-005 export expiry order | **established** | `data_export_repository.py:85-90` flips `status='expired'` first; `privacy_service.py:1836-1848` on delete failure `continue`s; the next run filters `status=='completed'` → the bundle is never retried. With no storage adapter wired the file is silently kept too |
| GDPR-003 tenant cascade | **established** | `tenant_service.py:254-268` removes only assignments/invitations/memberships/tenant record after the storage/vector purge; every other `tenant_key` collection survives |
| GDPR-006 / SEC-007 dedup ownership | **established** | `attachment_service.py:146-156` returns the existing attachment (tenant-wide sha256 dedup) → the second uploader has no own record; `created_by` stays the first uploader |
| Legacy pest-prototype residue | **established (per #1766 body)**, unmeasured on a live index | rows keyed by a deleted contribution carry no user key; tenant deletion reaches them (`tenant_service.py:313-320`) |
| Dev config `PEST_DETECTION_ENABLED` | **established** | `helm/kamerplanter/values-dev.yaml:78` backend only; worker env (`:215-250`) lacks it; `pest_image_tasks.py:98,146` no-op without it |

## Route decision

Issue spans more than one coherent PR strand (tenant domain-data inventory and per-user dedup ownership are each a data-model change). Per the route rule: **split**.

- This strand (PR): GDPR-004 + SEC-003 (same entry points), GDPR-005 (export retention), dev config (one line).
- Split issues: GDPR-003 (tenant domain-data erasure inventory), GDPR-006+SEC-007 (per-user ownership of deduplicated content), legacy pest-prototype residue (orphan sweep).
- DPO questions: stay open on #1767 (not implementable).

## Work packages

| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| WP1 | admin + unverified deletion run without persisted proof or unreached gate; no claim | both paths create/reuse an `ErasureRequest` (with `origin`), deactivate + revoke first, run through the same `_finalize_erasure` (unreached gate, `partially_completed` + backoff, beat retries); atomic claim refuses a concurrent run (409); config error refused before anything (503) | `privacy_service.py`, `erasure_repository.py` (+interface), `models/privacy.py`, `admin/platform/router.py`, `auth_tasks.py`, exceptions | generalist (pattern-following, see #1766) | — |
| WP2 | export expiry flips status before the delete | status `expired` written only after the bundle is gone; a failed delete is retried next run; unwired storage holds loud | `privacy_service.py`, `data_export_repository.py` (+interface), `retention_tasks.py` | generalist | — |
| WP3 | dev worker lacks `PEST_DETECTION_ENABLED` | worker env carries it | `helm/kamerplanter/values-dev.yaml` | generalist | — |
| WP4 | docs | privacy/admin docs state persisted admin erasure + retry | `docs/{de,en}/…` | `mkdocs-documentation` | WP1, WP2 |

Reviews: `nolte-engineering:gdpr-data-protection-reviewer`, `nolte-engineering:code-security-reviewer`, `/code-review medium`.

## Results

- Split: #1769 (GDPR-003), #1770 (GDPR-006 + SEC-007), #1771 (legacy pest prototypes); review follow-ups #1772 (R-06 purge, R-02 threshold), #1773 (plaintext keys in logs).
- WP1/WP2/WP3 implemented by the orchestrating generalist (no dispatch: pattern-following on #1761/#1766); WP4 `mkdocs-documentation`.
- Red-first: every new unit test run against the pre-change service/router/task (`cp` swap) — red for the asserted reason; green after.
- Reviews: `gdpr-data-protection-reviewer` (2 W, 4 S), `code-security-reviewer` (1 W, 4 S) — dispositions in the PR body.
