# Group pre-analysis: 2026-09-26-step-up-target-binding

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges.

## Scope of this analysis

**Research question:** Does a step-up factor (mailed code, OIDC re-auth token) obtained
for act X on target A confirm act X on target B, and which admin acts that steer
identity federation pass no step-up at all?

**The group's single logical change, in one sentence:** Every step-up confirmation is
bound to the exact act *and target* it was obtained for, and OIDC provider
configuration changes join the set of acts that require one.

**Out of scope:** an admin UI for OIDC providers (none exists in the frontend; follow-up
issue); issuer binding of the federated login lookup (#1869); `POST
/admin/oidc-providers/{key}/test` (re-reads discovery from the already step-upped issuer).

**Tier:** 3 — changes the published API contract of `POST /users/me/step-up-code`,
`POST /users/me/step-up/oidc` and the OIDC provider admin routes.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1884 | security | shared touch surface | `app/domain/services/step_up_service.py:246` `_code_digest(key, user_key, action, code)` — no target |
| #1883 | security | thematic coupling + shared touch surface | `app/api/v1/admin/oidc_providers/router.py` create/update/delete depend on `require_platform_admin` only; the new act must be target-bound (#1884) |

**Dependency ordering:** #1884 (target binding in the verifier) before #1883 (new act uses it).

**Shared touch surface:** `step_up_service.py` (`StepUpAction`, `CODE_PURPOSES`,
`verify`/`issue_*`), `api/v1/users/schemas.py` (issuing request bodies), frontend
`utils/stepUpReauth.ts`, `StepUpConfirmDialog`.

## Mode decision

**Mode:** A — single strand. **Reason:** #1883 depends on #1884's verifier signature;
neither is likely to be removed independently.

## Structural finding

**Cluster shape:** class cluster — "a guard's decision input is narrower than the
act it guards": the verifier knows who and which act, not on what.

**Preventive change:** `verify(..., target=...)` keyword-only without default plus a
`TARGETED_ACTIONS` set; guard test asserts every targeted act passes a non-None target
and every call site passes `target`.

## Design decisions (escalated to main before implementation)

| # | Question | Answer |
|---|---|---|
| D1 | target identity per act | user key (admin_account_update/erasure), tenant key, provider-link key, OIDC config key or `new:<slug>`; own-account acts unbound; email_change unbound |
| D2 | where the target comes from | client names it; server validates existence + authorization at issuance (403 before 404) |
| D3 | strictness | strict: 422 without target for targeted acts; breaking for non-frontend clients |
| D4 | mail text | no target in the mail |
| D5 | #1883 step-up class | full StepUpVerifier (password / OIDC re-auth / code), same budget; lockout edge documented |
| D6 | #1883 free fields | first: display_name, icon_url, enabled true→false; corrected after review SEC-001 (escalated): only display_name, icon_url — `enabled` needs the step-up both ways |
| D7 | #1883 UI AC | API-only; missing UI filed as #1906 |

## Completeness matrix

| Member | backend | frontend | spec/docs | guards |
|---|---|---|---|---|
| #1884 | digest + verify/issue/admit bound to target, StepUpTargetAuthorizer; check: `pytest tests/unit/domain/services/test_step_up_target_binding.py` | pending token/resume bound to target, dialogs pass `stepUpTarget`; check: `vitest run src/test/utils/stepUpReauth.test.ts ...` | REQ-023 §3.9 v1.20, docs/{de,en}/api/authentication.md; check: review | `tests/unit/guards/test_step_up_targets_are_bound.py` |
| #1883 | OidcProviderAdminService + step-up; partial writes (SEC-002/003); check: `pytest tests/unit/api/test_oidc_provider_step_up.py tests/api/test_admin_oidc_provider_*.py` | not applicable — no OIDC admin UI exists (#1906) | REQ-023 §3.9 + endpoint table, docs/{de,en}/user-guide/admin.md | credential-change guard extended to `_oidc_config_repo` writes |

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #1884 cause | no matching specialist — generalist | scratch script on origin/develop e12868385: token issued for admin_account_update, verified with no target | `token for A accepted for B: oidc_reauth` |
| #1883 cause | generalist | read `api/v1/admin/oidc_providers/router.py` on develop | create/update/delete depend on `require_platform_admin` only; writes via repo in router |
| both | generalist | `pytest tests/unit -q` | `13064 passed, 1 skipped, 6 deselected` |
| both | generalist | guards lane | `2593 passed, 64 deselected` |
| both | generalist | `pytest tests/api -q` | `1688 passed, 1 failed` → fixed (`test_light_mode_password_change_api.py`, 5 passed) |
| both | generalist | integration reach tests (erasure) | `33 passed` |
| frontend | generalist | `tsc --noEmit`, `vitest run` | clean; `4487 passed` (before the prettier revert, rerun pending) |
| review | nolte-engineering:code-security-reviewer | read-only review | SEC-001 (escalated, fixed per operator: Option A, red-first), SEC-002/003 + O-2 fixed red-first, O-1 filed as #1909 (out of scope per operator) |
