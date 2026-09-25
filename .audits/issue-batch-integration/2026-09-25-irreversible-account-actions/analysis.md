# Group pre-analysis: 2026-09-25-irreversible-account-actions

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Which irreversible account actions still run without a step-up
re-authentication, which password step-ups run without any throttle, and can one shared
step-up verifier close both without letting the throttle become a victim-lockout tool?

**The group's single logical change, in one sentence:** Every irreversible account action
(account self-deletion, platform-admin user deletion, tenant deletion) and every password
step-up goes through one shared, throttled step-up verifier enforced in the service layer.

**Out of scope:**
- #1815 — real re-authentication for federated accounts (OIDC `prompt=login`); federated
  accounts keep the typed-echo confirmation #1791/#394 chose.
- #1817 — API key `tenant_scope` on REST.
- #1829 / #1788 (personal-tenant erasure on account erasure) and #1770 (attachment dedup
  ownership) — coordinated by merge-update, not pulled in.
- Any other finding → new issue.

**Tier:** 3 — the group changes a published contract (request bodies on `DELETE
/users/me`, `DELETE /admin/platform/users/{key}`, `POST /privacy/erasure`, new 429 code).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1816 | security | dependency chain (provides the shared verifier the other two consume) + thematic coupling | password re-checks without throttle: `tenant_service.py:487`, `privacy_service.py:530`, `auth_service.py:787`; only `/auth/*` carries a limiter (`auth/router.py:183…587`) |
| #1813 | security | thematic coupling (same class: irreversible erasure without step-up) + shared touch surface (`privacy_service.py`) | `users/router.py:110-117` → `UserService.delete_account` (`user_service.py:103-127`) — no step-up, and it only tombstones the user document: no erasure record, no data erased |
| #1814 | security | thematic coupling + shared touch surface (`privacy_service.py`, verifier) | `admin/platform/router.py:267-307` → `erase_account_now(key, origin="platform_admin")`, gate `require_platform_admin` only |

**Dependency ordering:** #1816 (verifier + throttle store) → #1813 → #1814. #1813 and
#1814 are independent of each other but both consume #1816's verifier.

**Shared touch surface:** `app/domain/services/privacy_service.py`, the new
`app/domain/services/step_up_service.py`, `app/common/dependencies.py`,
`app/common/exceptions.py`, frontend `components/` step-up dialog, i18n `pages.json` (DE/EN),
REQ-023/REQ-025 spec, docs.

## Mode decision

**Mode:** A — single strand.

**Reason:** No member is removable on its own: #1813 and #1814 are built on #1816's
verifier, and every member's acceptance is clear. Mode B's removability criterion does not
hold.

## Structural finding

**Cluster shape:** class cluster — "an irreversible act or a password re-check reachable
from a session without the protections the login path has".

**Root cause or defect class:** the step-up was implemented per call site
(`PrivacyService.request_erasure`, `TenantService._verify_tenant_deletion_step_up`,
`AuthService.change_password`) — three hand-written copies of "if password_hash: verify",
none throttled, and two erasure routes that never got a copy. Opt-in-at-the-call-site
drift between siblings (memory: "Guard opt-in am Aufrufort → Drift zwischen Geschwistern").

**Process finding:** none new — the class is the known "guard opt-in at the call site"
pattern; its preventive change is the guard below, delivered in this group.

**Preventive change:** one `StepUpVerifier`; a guard test (AST) that no `verify_password`
call exists outside `AuthService.login_local` / `_reject_unknown_account` and the verifier;
keyword-only no-default step-up arguments on every erasure entry point.

**Recurrence fed to the portfolio loop:** class already recorded (sweeps 08-22, #1791);
no new count.

## Design (the load-bearing decisions)

1. **One verifier** `StepUpVerifier.verify(requester, *, echo_matches, password,
   authenticated_with_api_key, client_ip)` in `app/domain/services/step_up_service.py`.
   Order: service account / API-key request → 403; step-up lockout → 429
   `STEP_UP_LOCKED`; echo mismatch → 422 (not counted: nothing secret was tested);
   local account + missing/wrong password → 401 and counted; federated-only account →
   echo is the confirmation (#394/#1791, real re-auth #1815). Success clears the counters.
2. **Throttle store**: the repository's existing mechanism — `LoginThrottleEngine`
   (5 failures → 15 min, doubling to 240 min) over a Valkey store with in-process
   fallback (shape of `device_pairing_throttle.py`, #1118), own key prefix
   `kp:auth:stepup:throttle:`.
3. **Buckets**: (account, client IP) at the login threshold, plus an account-wide ceiling
   (higher threshold) that bounds IP rotation. Both lock **step-ups only**, never login.
4. **Lockout-abuse reasoning**: only a caller holding the victim's own session can
   produce a failure against the victim's counter (the password tested is always the
   requester's own; API keys are refused before counting). Deliberately *not* coupled to
   the login lockout (#1816's suggestion): coupling would let a session thief lock the
   owner out of sign-in — the very step the owner needs to revoke the thief's session —
   and reading the login lockout would let an unauthenticated outsider (who can already
   lock any known address at `/auth/login`) block the owner's step-ups too. The residual:
   a session thief can hold the account-wide step-up bucket locked; the owner can still
   sign in, revoke sessions and reset the password by mail.
5. **#1813 decision**: `DELETE /users/me` is neither a hard delete nor the Art. 17
   request — it tombstones the user document and leaves every personal record in place,
   with no erasure record. It is re-pointed onto the Art. 17 pipeline
   (`PrivacyService.request_erasure`, 90-day grace) with the same step-up body as
   `/privacy/erasure`; `UserService.delete_account` is removed.
6. **Echo for every account** on all three actions (tenant: slug; self: own e-mail; admin
   user delete: target's e-mail), password additionally for local accounts — the #1823
   shape, one rule everywhere.
7. **#1814**: `PrivacyService.erase_account_by_admin(target, *, requester,
   authenticated_with_api_key, confirmation, client_ip)` — keyword-only, no defaults;
   refuses self-deletion, re-proves the platform-lead membership, runs the verifier, then
   `erase_account_now`; the erasure record carries `step_up` and `requested_by_subject`.

## Completeness matrix

| Member | Source (backend) | Source (frontend) | Tests | Spec | Docs | Config / generated |
|---|---|---|---|---|---|---|
| #1816 | `step_up_service.py` (new), throttle store (new, Valkey + fallback), `StepUpLockedError`, `tenant_service.py` / `privacy_service.py` / `auth_service.py` call through it, `dependencies.py` wiring; check: guards lane | lockout message (429 `STEP_UP_LOCKED`) in every step-up dialog, i18n DE/EN; check: vitest | unit: verifier + store; route: lockout through real routes (N failures → 429, login unaffected), guard: no `verify_password` outside login + verifier; check: `pytest tests/unit/api tests/unit/guards` | REQ-023 (step-up throttle §), version row; check: `pre-commit` on spec | DE/EN security/account docs; check: `mkdocs build --strict` warning count | `settings.py` not applicable — thresholds reuse `LoginThrottleEngine`; openapi generated at build (never checked in) |
| #1813 | `users/router.py` DELETE /me → `request_erasure` with step-up body, `UserService.delete_account` removed, `ErasureCreateRequest.confirm_email`; check: route tests | `AccountSettingsPage` + `PrivacySettingsPage` use the shared step-up dialog (echo + fail-closed password); check: vitest red-first | route tests: grower/API key/service account/federated/local missing+wrong password; check: pytest | REQ-023 API table row `DELETE /users/me`, REQ-025 erasure body; check: pre-commit | privacy/account user guide DE/EN | not applicable — no config |
| #1814 | `admin/platform/router.py` delete_user body + `erase_account_by_admin`; erasure record audit fields; check: route tests | `AdminEditUserPage` step-up dialog; check: vitest red-first | route tests: platform admin with/without step-up, API key, non-admin, self; nothing erased on refusal; check: pytest | REQ-023/REQ-024 admin API table; check: pre-commit | admin docs DE/EN | `scripts/reach` act for admin user delete if one exists; check: grep |

## Risks

- API break: three routes gain a required body; external scripts break (listed for
  release notes).
- #1829 edits `privacy_service.py`/`models/privacy.py` concurrently → merge conflicts;
  resolved by merge-update.
- Throttle store per-request construction must use a process-wide fallback, or the
  guard is inert (the `DEFAULT_*` lesson from #1118).

## Open questions for the operator

- None blocking; operator pre-approved all gates (2026-09-25).

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #1816 | local adaptation | Issue suggests counting step-up failures into the login lockout; operator directive requires a lockout that cannot be used to lock out a victim — separate step-up buckets, login untouched (reasoning above). |
