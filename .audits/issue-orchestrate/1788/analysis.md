---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: "1788"
classification: bug
secondary-classes: [security]
route: direct
status: approved
created: 2026-09-25
---

# Issue Orchestration — Pre-analysis #1788

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1788 — erasure: an erased account's personal tenant keeps its domain data forever
- **Labels**: bug, backend
- **Linked items**: #1769 / PR #1797 (`0d7276476`, tenant-erasure inventory), PR #1776 (account-erasure proof/retry), #1791 (parallel strand: who may delete a tenant), #1811 (probe re-anchoring)
- **Prior art checked**: no open PR references #1788 (`gh pr list --search 1788`).
- **Trust**: issue author `nolte` (repository owner) — trusted. No comments.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: security (GDPR Art. 5(1)(e) / Art. 17)
- **Rationale**: an erasure path leaves data it is obliged to remove.
- **Asserted cause verified**: confirmed.
  - `src/backend/app/domain/engines/erasure_engine.py:308-312` — `tenants` is an `AnonymizationRule` (owner → `_anonymized`, personal name/slug renamed); the tenant is kept.
  - Callers of `delete_tenant`/`run_tenant_erasure`/`resume_tenant_erasures` (grep over `src/backend/app`): `api/v1/admin/platform/router.py:251`, `api/v1/tenants/router.py:113`, `tasks/tenant_tasks.py:28`, the service itself — none in `privacy_service.py`.
  - Personal tenant identity: `tenant_service.py:119-147` (`tenant_type=PERSONAL`, `owner_user_key=user_key`, `max_members=1`, the owner's LEAD membership); lookup `tenant_repository.py:55-56` `list_by_owner`.
  - Other members possible: `accept_invitation` (`tenant_service.py:944-990`) never checks `max_members` or `tenant_type`; `max_members` is patchable (`api/v1/tenants/schemas.py:25`); REQ-049 AK-19 requires that a personal tenant can take another member (P3, no special case).
  - After the account plan commits, `owner_user_key` is `_anonymized` — the personal tenant can no longer be found by owner, so its key must be resolved and persisted **before** the account plan runs.
  - Proofs: account erasure → `erasure_requests` (`ErasureRequest`, `_finalize_erasure`, `completed` only without unreached steps); tenant erasure → `tenant_erasure_records` (`TenantErasureRecord`, keyed per tenant, `completed` only without residue, own beat retry). Today unrelated.
  - Spec on a personal tenant with other members at account erasure: silent (REQ-024, REQ-025 §3.1.3, NFR-011, REQ-049 searched).

## Scope

- **In scope**: account erasure (`PrivacyService.erase_account` / `_finalize_erasure`, all three origins) erases the subject's personal tenant(s) through `TenantService.delete_tenant(origin="account_erasure")` when the subject is the only active member; request records per tenant what happened; config hold, fail-loud, retry; spec record in REQ-025/NFR-011; unit (red-first) + integration (ArangoDB) tests; reach probe for the personal tenant; docs (data-retention guide DE/EN).
- **Out of scope**: who may delete a tenant (#1791); organisation tenants the subject is alone in (P3 question → new issue); transfer of a shared personal tenant (spec question → new issue).

## Route

- **Decision**: direct — one outcome, one PR strand, no roadmap item.

## Work packages

### P1 — account erasure runs the tenant-erasure inventory on the personal tenant
- **Acceptance**: sole-member personal tenant → `delete_tenant(origin="account_erasure")` before the account ArangoDB plan; request records `personal_tenants` outcomes (erased / retained_other_members / absent) with the tenant-erasure record key; request `completed` only when every personal tenant is erased-completed or retained with reason; tenant-erasure misconfiguration holds the account erasure before any change; failure → `partially_completed` + backoff, retry resumes the tenant record; keys persisted before the run so a retry after the tenant document is gone still proves it.
- **Touched**: `privacy_service.py`, `models/privacy.py`, `models/tenant_erasure.py` (origin), `tenant_service.py` (two public read accessors only), `membership_repository` (active member keys), `dependencies.py`.
- **Specialist**: no dispatch — orchestrating generalist (precedent #1761/#1776/#1797: one author over the claim/finalise invariants; `fullstack-developer` is the only candidate).

### P2 — tests: red-first unit through `_finalize_erasure`/`erase_account_now`; integration against ArangoDB
### P3 — reach: seed option for a personal tenant of the subject; new T2 probe (admin user delete leaves no row of the sole-member personal tenant); privacy-subject seed gets a second member so the existing account-erasure probes keep measuring the account plan in a retained (shared) tenant — `nolte-engineering:capability-reach-audit`
### P4 — spec REQ-025/NFR-011 decision record; docs data-retention (DE/EN) — `mkdocs-documentation`
### P5 — reviews: `nolte-engineering:gdpr-data-protection-reviewer`, `nolte-engineering:code-security-reviewer`, `/code-review medium`

## Dependency ordering

P1 → P2 → P3 → P4 → P5

## Risks

- Existing account-erasure reach probes change their observation if the seeded subject's tenant becomes erasable → mitigated by a second member in the seed (P3).
- Concurrency with the tenant beat on the same record → `WriteConflictError`, recorded as a failed attempt, retried.
- #1791 edits `tenant_service.py` in parallel → change there limited to appended read accessors.

## Open questions

- Personal tenant with other members: spec silent → retain (as today), record reason, file spec issue (operator rule).
