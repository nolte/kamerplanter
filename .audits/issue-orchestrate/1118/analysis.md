---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 1118
classification: feature-request
secondary-classes: [security]
route: direct
status: draft
created: 2026-08-11
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on the run's feature branch, then removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1118 — feat(auth): QR-code device pairing for mobile app login (one-time code)
- **URL**: https://github.com/nolte/kamerplanter/issues/1118
- **Labels**: enhancement, feat, security, backend, frontend
- **Linked items**: none (no comments, no linked issues/PRs; `gh pr list --search 1118` returns only the unrelated dependency PR #74)
- **Prior art checked**: no existing pairing/device-code implementation (`grep -i pair` across `src/backend/app`, `src/frontend/src`, REQ-023 finds nothing relevant); no `project/features/` entry and no roadmap item for device pairing; `qrcode.react@^4.2.0` is already a frontend dependency and already used in `src/frontend/src/pages/pflanzen/PlantTagDialog.tsx`; `settings.app_base_url` already exists as the "base URL for QR codes" SSOT (REQ-032).

## Audit trail — operator decisions carried into this plan

- **Requirements gate**: explicit **operator override**. No `project/requirements/` artifact exists for this issue and none is to be created; the issue body is accepted as the elicited requirement. Recorded here because the hard rule "never plan against unstated requirements" otherwise blocks planning without a grounded requirement artifact.
- **Classification**: `feature-request` (primary), `security` (secondary) — decided by the operator.
- **Route**: direct implementation, single PR strand — decided by the operator.
- **Scope**: backend issuance + redemption + TTL store + rate limiting + audit events; web frontend "Connect mobile device" dialog with QR rendering and expiry countdown/refresh; QR payload contract documented for the future Flutter app. **The Flutter app itself is out of scope** — decided by the operator.
- **Decomposition approval** (2026-08-11): the 11-package plan below is approved for dispatch. Open questions 1–3 resolved by the operator: **P6 = optional JSON body on the existing `POST /auth/refresh`** (single rotation implementation, cookie path byte-identical); **P5 = client-supplied, length-capped `device_name`**; **P11 stays in this strand**. Question 4 (Nuclei brute-force template follow-up issue) is deferred to PR time.
- **Dispatch mode**: packages run strictly sequentially despite the DAG's permitted fan-out — P1/P2 share `common/dependencies.py`, P4/P5/P6 share `auth/schemas.py`, P5/P7 share `AccountSettingsPage.tsx`, and the recorded portfolio lesson forbids concurrent writing agents on a shared tree.

## Detected repository context

Derived from this worktree, not assumed:

| Aspect | Finding |
|--------|---------|
| Backend | Python 3.14 / FastAPI, strict 5-layer (`api/v1` → `domain/services` → `domain/engines` → `data_access` → ArangoDB), enforced by `scripts/check_layer_imports.py` (NFR-001) |
| Auth surface | `src/backend/app/api/v1/auth/router.py` (449 lines): register/login/refresh/logout/logout-all/password-reset/OAuth/api-keys/service-accounts |
| Auth service | `src/backend/app/domain/services/auth_service.py` (980 lines), `_create_tokens()` is the single token-pair factory (line 930) |
| Session surface | `AuthService.list_sessions` / `revoke_session` (lines 558/573) → `GET|DELETE /api/v1/users/me/sessions[/{key}]` in `src/backend/app/api/v1/users/router.py` (lines 101/113) |
| One-time-state pattern | `src/backend/app/data_access/external/redis_oauth_state.py` — TTL `set(..., ex=)` + pipelined `get`+`delete` (atomic single use) |
| Throttle/lockout pattern | `src/backend/app/domain/engines/login_throttle_engine.py` (pure) + `src/backend/app/data_access/external/unknown_account_store.py` (Redis tier + bounded in-process fallback so the guard is **never inert**) |
| Per-IP rate limiting | `slowapi` `Limiter(key_func=get_remote_address)` in the auth router; `settings.rate_limit_auth = "20/minute"` |
| Mode gating | `src/backend/app/api/v1/router.py` lines 113–125: `api_keys_router` is mounted in **both** modes, the rest of `auth_router` only in **full** mode (REQ-027) |
| Public-endpoint marking | `main.py` `_openapi_postprocessed()` stamps `security: []` on operations with no security dependency; `scripts/security/zap_auth_bypass.py::is_protected` skips those |
| Static gates (required `static` lane) | `scripts/check_schema_examples.py` (new/changed schemas need an OpenAPI example; ratchet must not grow), `check_boundary_validation.py`, `check_layer_imports.py`, `check_tenant_body_field.py`, `check_workflow_gate_integrity.py` |
| Frontend | React 19 + TS 6 + **MUI 9** + RTK; `qrcode.react` present; account surface `src/frontend/src/pages/auth/AccountSettingsPage.tsx` with a `sessions` tab that exists **only in full mode** (lines 196–212); API client `src/frontend/src/api/endpoints/auth.ts`; i18n `pages.auth.*` in `src/frontend/src/i18n/locales/{de,en}/pages.json` |
| Tests | backend `src/backend/tests/{unit,api,integration,contracts}` (pytest); frontend `src/frontend/src/test/**` (vitest); E2E `tests/e2e/test_req023_*.py` (Selenium, Docker-only) with test cases specified as `TC-023-NNN` in `spec/e2e-testcases/TC-REQ-023.md` |
| Docs | MkDocs Material, DE canonical + EN mirror: `docs/de/api/authentication.md` + `docs/en/api/authentication.md`, both in `mkdocs.yml` nav |
| Style guides (binding) | `spec/style-guides/BACKEND.md`, `spec/style-guides/FRONTEND.md`, `spec/style-guides/DOCS.md` |

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: security
- **Rationale**: a new capability assembled from existing REQ-023 auth machinery; the `security` label drives the `code-security-reviewer` + `security-review` verify chain at PR time (an unauthenticated redemption endpoint that mints a full token pair is new attack surface).

## Scope

- **In scope**:
  - Backend: pairing-code issuance (authenticated) and redemption (public) endpoints, Redis-backed single-use TTL store, per-IP rate limit **and** lockout on redemption, structured audit events on create/redeem/failed-redeem.
  - Backend: a non-cookie refresh transport so the token pair handed to a native client is actually rotatable (see §Refutations R3).
  - Backend: optional device metadata on the refresh-token record so a paired device is distinguishable in — and revocable from — the existing session list.
  - Frontend: "Connect mobile device" dialog in the account settings *sessions* tab, QR rendering via `qrcode.react`, expiry countdown + refresh, DE/EN i18n.
  - Contract documentation: QR payload schema + redemption/refresh contract in `docs/{de,en}/api/authentication.md`, and the corresponding REQ-023 spec delta.
- **Out of scope**:
  - The Flutter/Android app (scanner + redemption client) — operator decision; this strand only defines the contract it will build against.
  - A **persisted** (ArangoDB) general auth audit log — see §Refutations R1; REQ-023 defers it explicitly ("Service Account Audit-Log → zukünftig, **nach allgemeinem Audit-Log**").
  - New DAST assets — see §Refutations R4: the ZAP API scan is OpenAPI-driven and picks the new routes up automatically. A dedicated brute-force Nuclei template is recorded as a follow-up candidate, not a package.
  - 2FA/WebAuthn, any change to the browser login flow's cookie semantics.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome ("pair a device by scanning a QR code"), one PR strand, no new roadmap item; every package below states a testable acceptance criterion, so nothing routes to the formal `roadmap → feature → sprint` pipeline. Operator-confirmed.
- **Pipeline hand-off**: n/a

## Refutations of the dispatch-brief hypothesis

The hypothesis — *"deliverable as one PR strand on the existing auth service without a new token class or DB collection beyond a Redis-backed store (plus possibly an audit/event trail)"* — is **confirmed in its core and refuted in three specifics**. Each refutation shaped a package.

**R0 — CONFIRMED (no new token class, no new collection for the code).**
`AuthService._create_tokens()` (auth_service.py:930) is the single factory for the REQ-023 pair and already persists a `RefreshToken` document, which `list_sessions` reads. A redemption that calls it therefore yields the standard pair *and* an automatically visible/revocable session with **zero** new token type. The pairing code itself fits `RedisOAuthStateStore`'s shape exactly (TTL + atomic get-and-delete).

**R1 — REFUTED: "audit log" must not become a new ArangoDB collection.**
Evidence: (a) there is **no** general audit collection — `collections.py` has only the domain-specific `AI_AUDIT_LOG`, `MCP_AUDIT_LOG`, `TASK_AUDIT_ENTRIES`; (b) REQ-023 §"Nicht in Scope" states the service-account audit log comes "zukünftig, **nach allgemeinem Audit-Log**", i.e. the general one is a deliberate future item, so introducing it here is scope creep against the spec; (c) NFR-011 IP anonymisation is implemented in `src/backend/app/tasks/auth_tasks.py::anonymize_old_ips`, and that sweep is hard-coded to the `refresh_tokens` collection — a new collection holding `source IP` would be an **unswept DSGVO liability** on day one. → The issue's "audit log entry (who, when, source IP)" is planned as **structlog structured events**, exactly how every other auth event in this codebase is recorded (`user_registered`, `login_unknown_account_attempt`). Packages P3 and P4 carry this as an acceptance criterion.

**R2 — REFUTED: session visibility of "device name/type" *does* require a persisted-model change.**
`RefreshToken` (models/auth.py:36) and `SessionInfo` (:82) carry only `user_agent`/`ip_address`. The issue's step 5 asks for device metadata "for later session management". ArangoDB is schemaless so no migration is needed, but the change is real and reaches the session API schema and the frontend session list. → Isolated as **P5** so it can be dropped without unpicking the rest.

**R3 — REFUTED, and this is the load-bearing one: without a non-cookie refresh path the whole feature is inert.**
`POST /api/v1/auth/refresh` takes the refresh token **exclusively** from the HttpOnly cookie (`get_refresh_token_from_cookie`, common/auth.py:56) and enforces the CSRF double-submit (`verify_csrf`, auth/csrf.py:34 — cookie value must equal the `X-CSRF-Token` header). A native app that stores the raw refresh token in the Android Keystore has no browser cookie jar and no way to obtain the `csrf_token` cookie other than replaying what the redeem response happened to set. Delivered as-is, the pairing flow would mint a token pair that can never be rotated — the "implemented but inert" failure class this repository has been bitten by repeatedly. → **P6** adds a body-borne refresh transport (CSRF is a defence against *ambient* credentials; a token supplied in the request body is not ambient), with the cookie path left byte-for-byte unchanged and still CSRF-verified. This also forces the redeem response to return the raw refresh token **in the JSON body**, a documented deviation from the web flow's cookie-only transport, and is why P4/P6 must reach the security reviewers.

**R4 — Checked, no package needed: DAST coverage is automatic.**
`security-zap-postmerge.yml` feeds `zap-api-scan.py` from the live `/api/v1/openapi.json`, so the new routes are scanned as soon as they exist. `scripts/security/zap_auth_bypass.py::is_protected` reads the OpenAPI `security` field, and `main.py::_openapi_postprocessed` stamps deliberately-public operations with `security: []` — so the intentionally unauthenticated redeem endpoint will **not** be reported as an auth bypass, and no suppression entry in `tests/security/nuclei-suppressions.yaml` is required. What ZAP cannot verify is the *behavioural* lockout; that is covered by P8's adversarial API tests. Follow-up candidate (separate issue, not this strand): a `kamerplanter-device-pairing-bruteforce.yaml` Nuclei template.

## Work packages

### P1 — Redis-backed one-time pairing-code store

- **Problem statement**: the pairing code needs a store that guarantees single use and expiry without touching ArangoDB.
- **Acceptance criteria**:
  - A `DevicePairingCodeStore` persists `{user_key, issued_at}` under `sha256(code)` with `ex=<ttl>`; the raw code is never a Redis key or value (mirrors the pseudonymisation convention of `unknown_account_store` and `RefreshToken.token_hash`).
  - Unit test: `consume()` returns the payload on the first call and `None` on every subsequent call for the same code (atomic get-and-delete, pipelined like `RedisOAuthStateStore.get_and_delete`).
  - Unit test: TTL is passed through to Redis; `settings.device_pairing_ttl_seconds` defaults to `90` and is validated `ge=60, le=120` (the issue's 60–120 s window is enforced by the settings model, not by a comment).
  - Unit test: an unknown/expired code yields `None`, never an exception that leaks whether the code ever existed.
  - `scripts/check_layer_imports.py` stays green (module lives in `data_access/external/`, interface in `domain/interfaces/`).
- **Touched files / artifacts**: `src/backend/app/data_access/external/redis_device_pairing.py` (new), `src/backend/app/domain/interfaces/device_pairing_store.py` (new), `src/backend/app/config/settings.py`, `src/backend/app/common/dependencies.py`, `src/backend/tests/unit/data_access/test_redis_device_pairing.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### P2 — Per-IP redemption throttle with lockout

- **Problem statement**: the redemption endpoint is unauthenticated; a per-IP rate limit alone does not produce the lockout the issue requires.
- **Acceptance criteria**:
  - A `DevicePairingThrottleStore` counts failed redemptions per source IP in Redis and **degrades to a bounded in-process map** on a Redis error rather than fail-open — the explicit design of `unknown_account_store.py`, so the guard can never be silently inert.
  - The lockout decision reuses the pure `LoginThrottleEngine` (`check_allowed` / `calculate_lockout` / `get_lockout_minutes`); no second threshold constant is introduced.
  - Unit test: after the engine's threshold of failed redemptions from one IP, the next attempt is refused **before** the code store is consulted (assert the store mock records zero calls) — proving the guard is not merely decorative.
  - Unit test: a *successful* redemption clears that IP's counter.
  - Unit test: counters are per-IP, so one attacker cannot lock out an unrelated IP.
- **Touched files / artifacts**: `src/backend/app/data_access/external/device_pairing_throttle.py` (new), `src/backend/app/domain/interfaces/device_pairing_throttle.py` (new), `src/backend/app/common/dependencies.py`, `src/backend/tests/unit/data_access/test_device_pairing_throttle.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none (parallel with P1)

### P3 — `AuthService` pairing create/redeem + audit events

- **Problem statement**: the domain logic that mints a pairing code and exchanges it for the standard REQ-023 token pair, without a new token class.
- **Acceptance criteria**:
  - `create_device_pairing(user_key)` returns `(code, expires_at)` with the code from `secrets.token_urlsafe(32)` (≥ 256 bit); unit test asserts the code is drawn from `secrets` (patched) and that 1 000 draws are unique and contain no monotonic component.
  - `redeem_device_pairing(code, user_agent, ip_address, device_name)` calls the **existing** `_create_tokens()`; unit test asserts the returned pair is shape-identical to a `login_local` pair and that **no** new token type/claim is introduced.
  - Unit test (REQ-024): the redeemed session resolves the *same* tenant memberships as a normal login for that user — nothing added, nothing dropped.
  - Unit test: a second redemption of the same code raises the same generic error as an unknown code (no oracle distinguishing "used" from "never existed"); an expired code likewise.
  - Unit test: the code is bound to its issuing user — redemption never consults caller-supplied identity.
  - Audit (R1): `device_pairing_created`, `device_pairing_redeemed`, `device_pairing_redeem_failed` structlog events carry `user_key`, `ip_address`, timestamp, and at most an 8-char code prefix; unit test asserts the **full code never appears in any emitted log record**.
  - Unit test: on a locked-out IP, `redeem_device_pairing` raises `AccountLockedError` (423) with remaining minutes, mirroring `login_local`.
- **Touched files / artifacts**: `src/backend/app/domain/services/auth_service.py`, `src/backend/app/domain/models/auth.py` (pairing DTOs), `src/backend/tests/unit/domain/services/test_auth_service_device_pairing.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P1, P2

### P4 — API surface: issuance + redemption endpoints

- **Problem statement**: expose the flow as two endpoints with the right authentication posture, rate limits and mode gating.
- **Acceptance criteria**:
  - `POST /api/v1/auth/device-pairing` (authenticated, `get_current_user`) returns `{payload_version, server_url, code, expires_at, expires_in}` where `server_url` comes from `settings.app_base_url` — the setting that already exists for QR codes (REQ-032) — and **never** from `request.base_url` (which behind Traefik/K8s yields an unreachable in-cluster URL). Test asserts the setting is the source.
  - `POST /api/v1/auth/device-pairing/redeem` is **public** and returns `{access_token, token_type, expires_in, refresh_token}`; test asserts the generated OpenAPI marks it `security: []` (so `zap_auth_bypass.py` classifies it correctly) and that the response carries **no** password, API key or any credential other than the two tokens.
  - Both endpoints are mounted on `auth_router`, **not** `api_keys_router`: a light-mode instance answers **404** on both. Test mirrors `src/backend/tests/api/test_api_key_router_mounting.py`.
  - Both endpoints carry a `@limiter.limit(...)`; the redemption limit is a dedicated `settings.rate_limit_device_pairing_redeem` (default `"10/minute"`, deliberately below `rate_limit_auth`). Test asserts a 429 past the limit.
  - The issuance endpoint requires no CSRF header (Bearer-authenticated, matching `create_api_key`); the redemption endpoint requires none either (no ambient credential). Test asserts a valid request without `X-CSRF-Token` succeeds on both.
  - New request/response schemas carry OpenAPI examples; `python3 scripts/check_schema_examples.py` and `python3 scripts/check_boundary_validation.py` stay green (no ratchet growth).
- **Touched files / artifacts**: `src/backend/app/api/v1/auth/router.py`, `src/backend/app/api/v1/auth/schemas.py`, `src/backend/app/config/settings.py`, `src/backend/tests/api/test_auth_device_pairing_api.py` (new), `src/backend/tests/api/test_device_pairing_router_mounting.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P3

### P5 — Device metadata on sessions (visibility + revocability)

- **Problem statement**: a paired phone must be distinguishable from a browser session in the existing session list, and revocable there.
- **Acceptance criteria**:
  - `RefreshToken` gains an optional `device_name: str | None` (length-capped, e.g. ≤ 64, validated at the boundary → 422, never 500); `_create_tokens()` accepts and stores it; `SessionInfo` and the API `SessionResponse` surface it.
  - Test: a session created **before** this change (document without the field) still deserialises and renders — backwards compatibility asserted rather than assumed.
  - Test: `GET /api/v1/users/me/sessions` lists the paired device with its name and the app's user-agent; `DELETE /api/v1/users/me/sessions/{key}` revokes it, and a subsequent refresh with that token fails with 401.
  - Frontend: `SessionInfo` type + session list row show the device name when present and fall back to the user-agent when absent; vitest test covers both.
- **Touched files / artifacts**: `src/backend/app/domain/models/auth.py`, `src/backend/app/domain/services/auth_service.py`, `src/backend/app/api/v1/auth/schemas.py`, `src/frontend/src/api/types.ts`, `src/frontend/src/pages/auth/AccountSettingsPage.tsx`, `src/backend/tests/api/test_sessions_device_name.py` (new), `src/frontend/src/test/pages/AccountSettingsSessions.test.tsx` (new)
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P4

### P6 — Non-cookie refresh transport for paired devices (R3)

- **Problem statement**: the token pair a native client receives is unusable beyond 15 minutes unless it can rotate the refresh token without a browser cookie jar and without the CSRF double-submit.
- **Acceptance criteria**:
  - `POST /api/v1/auth/refresh` accepts an **optional** JSON body `{"refresh_token": "..."}`. When present: the cookie is not required, `verify_csrf` is **not** invoked, no `kp_refresh` cookie is set on the response, and the raw rotated refresh token is returned in the body.
  - Regression test (the security-critical one): the **cookie** path is unchanged — a cookie-borne refresh with a missing or mismatched `X-CSRF-Token` is still rejected with 403.
  - Test: a request that supplies *both* a cookie and a body token does not let the body path bypass CSRF for the cookie credential (explicit, asserted precedence rule — recommended: body wins and the cookie is ignored entirely, so no ambient credential is ever spent without CSRF).
  - Test: rotation semantics are identical on both paths — the old token is revoked, the new one works once, the replayed old one fails with 401.
  - Test: the body path preserves `is_persistent` from the stored token, like the cookie path.
- **Touched files / artifacts**: `src/backend/app/api/v1/auth/router.py`, `src/backend/app/api/v1/auth/schemas.py`, `src/backend/app/common/auth.py`, `src/backend/tests/api/test_auth_refresh_body_transport.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer` (mandatory `nolte-engineering:code-security-reviewer` pass before PR — this package touches the CSRF boundary)
- **Depends on**: P4

### P7 — Frontend "Connect mobile device" dialog

- **Problem statement**: the logged-in user needs a place to produce the QR code, see it expire, and refresh it.
- **Acceptance criteria**:
  - A "Connect mobile device" action in the account settings **sessions** tab (which already exists only in full mode, so light mode is gated by construction) opens a dialog rendering `<QRCodeSVG value={payload}/>`.
  - The payload is the documented JSON contract `{"v":1,"url":<server_url>,"code":<code>}`; vitest asserts the rendered `value` prop contains the code **and** that the code does not appear anywhere in the dialog's visible text (`queryByText(code)` is null) — the issue's anti-shoulder-surfing requirement, tested rather than asserted in prose.
  - A countdown shows the remaining seconds; at zero the QR is replaced by an "expired" state with a refresh action; vitest drives this with fake timers.
  - The refresh action re-requests a code and replaces the QR; the previous code is not re-rendered.
  - Closing the dialog discards the code from component state (no code retained in Redux or `localStorage`); vitest asserts the store is untouched.
  - i18n keys added under `pages.auth.*` in **both** `de` and `en`; no hard-coded user-facing string.
- **Touched files / artifacts**: `src/frontend/src/pages/auth/ConnectDeviceDialog.tsx` (new), `src/frontend/src/pages/auth/AccountSettingsPage.tsx`, `src/frontend/src/api/endpoints/auth.ts`, `src/frontend/src/api/types.ts`, `src/frontend/src/i18n/locales/{de,en}/pages.json`, `src/frontend/src/test/pages/ConnectDeviceDialog.test.tsx` (new)
- **Specialist**: `nolte-engineering:fullstack-developer` (verify chain: `nolte-engineering:frontend-code-reviewer`, `kamerplanter:frontend-design-reviewer`)
- **Depends on**: P4

### P8 — Adversarial API tests for the pairing surface

- **Problem statement**: the security properties the issue states are behavioural; ZAP and the unit suites do not prove them end-to-end at the HTTP boundary.
- **Acceptance criteria** — one failing-first API test per property, all green afterwards:
  - Replay: redeeming a consumed code returns the same generic 4xx as an unknown code, and no second token pair is issued.
  - Expiry: a code redeemed after `device_pairing_ttl_seconds` fails; the test manipulates the store/clock, not `sleep`.
  - Brute force: N+1 failed redemptions from one IP produce a 423 lockout, and the (N+2)-th *valid* code is also refused while locked.
  - Rate limit: exceeding `rate_limit_device_pairing_redeem` returns 429.
  - Light mode: both endpoints answer 404 when `KAMERPLANTER_MODE=light`.
  - Tenant integrity (REQ-024): the access token from a redemption carries exactly the issuing user's memberships; a request to another tenant's scope with it is refused.
  - Log hygiene: with structlog captured, no emitted record contains the full pairing code or the raw refresh token.
- **Touched files / artifacts**: `src/backend/tests/api/test_auth_device_pairing_security.py` (new)
- **Specialist**: `nolte-engineering:integration-test-generator` (review pass: `nolte-engineering:integration-test-reviewer`)
- **Depends on**: P4, P6

### P9 — QR payload contract documentation (DE canonical + EN mirror)

- **Problem statement**: the future Flutter app must be able to build against a written contract; the issue names this as a deliverable.
- **Acceptance criteria**:
  - A new "Gerätekopplung (QR-Code)" section in `docs/de/api/authentication.md` with the mirrored EN section in `docs/en/api/authentication.md`, following `spec/style-guides/DOCS.md` (informal "du", admonition conventions, DE canonical).
  - Documents: the payload JSON schema incl. the `v` version field, TTL and single-use semantics, the issuance request/response, the redemption request/response **including that the refresh token arrives in the body**, the body-borne refresh call from P6, and the security notes (never scan a code you did not just generate; the code is not a password).
  - `mkdocs build --strict` passes locally; no nav change required (section within an existing page).
  - Every documented request/response matches the shipped OpenAPI (verified against `/api/v1/openapi.json`), so the page cannot be stale on the day it lands.
- **Touched files / artifacts**: `docs/de/api/authentication.md`, `docs/en/api/authentication.md`
- **Specialist**: `kamerplanter:mkdocs-documentation`
- **Depends on**: P4, P6

### P10 — REQ-023 spec delta

- **Problem statement**: `spec/` is the SSOT; a new auth flow that only exists in code will be reported as drift by the next `spec-drift-audit`.
- **Acceptance criteria**:
  - REQ-023 gains a device-pairing subsection under §3 (service/API) and §4 (frontend) describing: the Redis-only one-time code (no new node, no new collection), the TTL bounds, the lockout reuse of `LoginThrottleEngine`, the token pair being the *existing* one, and the body-borne refresh transport for native clients.
  - The changelog table at the top of REQ-023 gains a version row referencing #1118.
  - The "Nicht in Scope" list is extended with an explicit line that device pairing introduces **no** persisted audit log (R1), so the deferral of the general audit log stays coherent.
  - `task check` stays green; the spec text asserts nothing the implementation does not do (no aspirational tense — the NFR-018 §1 failure class).
- **Touched files / artifacts**: `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md`
- **Specialist**: `nolte-shared:spec` skill (fallback: `general-purpose` — the `spec` skill has previously failed to resolve at runtime in this repository)
- **Depends on**: P4, P6

### P11 — E2E coverage of the pairing dialog

- **Problem statement**: the browser half of the flow has no end-to-end proof that the dialog reaches a real backend and renders a real code.
- **Acceptance criteria**:
  - New `TC-023-NNN` entries in `spec/e2e-testcases/TC-REQ-023.md` (existing numbering scheme, next free ids) covering: open the dialog from the sessions tab, a QR image appears, a countdown is visible, refresh yields a new QR.
  - A Selenium test in `tests/e2e/test_req023_device_pairing.py` implementing them, with the TC id in the docstring so the `req<NNN>` conftest selector picks it up.
  - The test asserts on the rendered `<svg>` and the countdown text, **not** on a fixed `sleep`; it must fail if the dialog renders an empty QR.
- **Touched files / artifacts**: `spec/e2e-testcases/TC-REQ-023.md`, `tests/e2e/test_req023_device_pairing.py` (new)
- **Specialist**: `nolte-engineering:e2e-test-generator` (review pass: `nolte-engineering:e2e-test-reviewer`)
- **Depends on**: P7

## Dependency ordering

```
P1 ┐
   ├─→ P3 ─→ P4 ─┬─→ P5
P2 ┘             ├─→ P6 ─┬─→ P8
                 │       ├─→ P9
                 │       └─→ P10
                 └─→ P7 ─→ P11
```

Dispatch order: `P1 ∥ P2` → `P3` → `P4` → `P5 ∥ P6 ∥ P7` → `P8 ∥ P9 ∥ P10 ∥ P11`.
Shared-file constraint: P4, P5 and P6 all touch `src/backend/app/api/v1/auth/schemas.py`, and P5 and P7 both touch `AccountSettingsPage.tsx` — per the recorded lesson on parallel writing agents on a shared tree, run those sequentially rather than concurrently even though the DAG permits fan-out.

## Risks

| Risk | Mitigation |
|------|-----------|
| **CSRF regression via P6** — relaxing CSRF for a body-borne token could be over-applied to the cookie path. | Explicit regression test that the cookie path still 403s without a matching header; `code-security-reviewer` **and** the `security-review` chain are mandatory before PR (the `security` label). |
| **Refresh token in a JSON response body** deviates from the web flow's cookie-only transport (AP-7 FE-S1). | Confined to the redeem + body-refresh endpoints, documented in P9/P10, reviewed by `code-security-reviewer`; the browser flow keeps the HttpOnly cookie unchanged. |
| **Guard implemented but inert** — the repository's most expensive recurring class (lockout that never fires, throttle that fails open). | P2 mandates the Redis-plus-in-process-fallback shape and a test asserting the code store is *not* consulted once locked; P8 re-proves it at the HTTP boundary. |
| **QR payload points at an unreachable URL** when derived from `request.base_url` behind Traefik. | P4 pins the source to `settings.app_base_url` with a test. |
| **`check_schema_examples.py` ratchet growth** blocks the required `static` lane. | P4/P5/P6 acceptance criteria require examples on every new schema; run `task precommit` (not `task lint`) before pushing. |
| **i18n gaps** in the new dialog. | `nolte-engineering:i18n-completeness-checker` in the verify chain; DE+EN keys are a P7 acceptance criterion. |
| **Parallel `issue-orchestrate` collision** on this repo. | Checked: no open PR references #1118. Re-check `gh pr list --search` before dispatch. |
| **DAST false positive** on the intentionally public redeem endpoint. | Verified not to arise (R4): `security: []` stamping + `zap_auth_bypass.is_protected`. Re-verify on the nightly lane after merge rather than pre-suppressing. |

## Open questions

1. **P6 transport shape (recommended default given, decision welcome).** Extending the existing `POST /auth/refresh` with an optional body is proposed because it keeps one rotation implementation. The alternative is a dedicated `POST /auth/device/refresh`, which keeps the browser endpoint literally untouched at the cost of a second code path. If the operator prefers the dedicated endpoint, only P6's touched files change; the DAG is unaffected.
2. **Device name provenance (P5).** The proposal is a client-supplied, length-capped `device_name` in the redemption request. If the operator would rather derive it solely from the user-agent (no client-controlled string persisted at all), P5 shrinks to a display-only change and its schema/boundary criteria drop.
3. **P11 (E2E) inclusion.** The E2E lane is nightly and Docker-only, and this strand is already large. If the operator wants the PR narrow, P11 can be split into a follow-up issue without weakening any other package's acceptance criteria — P7's vitest coverage stands on its own.
4. **Nuclei brute-force template** — recorded as an out-of-scope follow-up candidate (R4). Confirm whether an issue should be opened for it at PR time.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports. -->

- **P1+P2** → `nolte-engineering:fullstack-developer` → **done**, commit `f6d8c893a`, 50 unit tests green (red-first proven by mutation). Deviations (accepted): tests live under `tests/unit/data_access/external/` (repo convention); class names follow `Redis{X}Store`/`Memory{X}Store`/`I{X}` convention (`RedisDevicePairingCodeStore`, `RedisDevicePairingThrottleStore`, `MemoryDevicePairingThrottleStore`); the code store deliberately has **no** in-process fallback (a per-replica fallback would make codes redeemable only on the issuing replica behind the LB) — `consume` fails closed, `issue` fails loud. `LoginThrottleEngine` fits per-IP keys unchanged. The P2 criterion "locked-out IP is refused before the code store is consulted" is **delegated to P3** (`test_locked_out_ip_never_reaches_the_code_store`) because the composition only exists in `AuthService.redeem_device_pairing`; store-level precondition is proven. Store emits `device_pairing_code_issued`/`device_pairing_code_not_redeemable` with `code_sha256[:16]`, never a raw-code prefix.
- **P3** → `nolte-engineering:fullstack-developer` → **done**, commit `aed26b457`, 36 new unit tests (red-first proven by 5 mutations; a vacuous claim-comparison test was caught and rewritten against the raw JWT payload segment). Signatures for P4: `create_device_pairing(user_key, ip_address=None) -> tuple[str, datetime]`; `redeem_device_pairing(code, user_agent=None, ip_address=None, device_name=None) -> tuple[TokenPair, str, bool]` (same shape as `login_local`). Errors: `AccountLockedError`→423, `InvalidTokenError("pairing code")`→401 single generic answer, `UnauthorizedError`→401 inactive account, `ValidationError`→422 (device_name >64 or store unconfigured). Events: `device_pairing_created`/`device_pairing_redeemed`/`device_pairing_redeem_failed(reason)` with `code_sha256[:16]` digest (D2). Deviations accepted: no pairing DTOs (D1, P4 derives `expires_in` from `expires_at`); `dependencies.py` wired into `get_auth_service()` (D3); code store optional→422, throttle never optional (D4); `is_persistent=True` on redemption like `complete_oauth` (D7); missing IP throttles into shared "unknown" bucket (D8). `device_name` validated but NOT yet persisted — P5 must flip `test_the_label_is_not_persisted_yet`. An absence test pins that the redeem signature carries no identity parameter.
- **P4** → `nolte-engineering:fullstack-developer` → **done**, commit `49f3dbbdf`, 31 new API tests (985 total green), 12 mutations red; two initially-green mutations led to sharpened tests (layer-distinguishing 422 assertion via `details[].field == "body.device_name"`). Routes: `POST /auth/device-pairing` → **201** (Bearer, `rate_limit_auth`), `POST /auth/device-pairing/redeem` → 200 (public, `security: []`, `rate_limit_device_pairing_redeem` "10/minute"). Schemas: `DevicePairingCreateResponse{payload_version,server_url,code,expires_at,expires_in}`, `DevicePairingRedeemRequest{code,device_name?}` (no identity field — pinned), `TokenPairResponse{access_token,token_type,expires_in,refresh_token}` (named generically for P6 reuse), `DEVICE_NAME_MAX_LENGTH=64` (P5 must import, not re-literal). Deviations accepted: **D1 security-relevant** — `resolve_client_ip(request)` instead of `request.client.host` so the throttle bucket isn't the Traefik proxy IP (otherwise 5 bad codes lock pairing globally); cost: left-appendable `X-Forwarded-For` can bypass the throttle (bounded by 256-bit code in 90 s TTL) — **flagged for security review**; slowapi rate limiter stays proxy-blind (pre-existing). D3: issuance answers 201 (P7 must check 201). D5: FastAPI 0.139 no longer flattens `include_router` — route-counting via `app.routes` is dead in this repo; mounting test reads `auth_module.router.routes` directly. For P6: reuse `TokenPairResponse`; the pre-existing unused `RefreshRequest` schema lacks an OpenAPI example — must add one (ratchet headroom only 2). For P5: `SessionResponse` also lacks an example — add one when touching it. QR payload for P7: `{"v": payload_version, "url": server_url, "code": code}`; `expires_in` is already remaining seconds.
- **P5** → `nolte-engineering:fullstack-developer` → **done**, commit `13549f6fe` (10 files, +936/−63). Backend 996 api + 6962 unit green; frontend 3805 vitest green, coverage over all thresholds; 8 mutations red (one initially-green frontend mutation fixed by reordering the fixture). Key catch beyond the plan: **token rotation would have silently dropped `device_name` after the first refresh** — `refresh_tokens` now carries it, pinned by unit+API tests. Deviations accepted: `DEVICE_NAME_MAX_LENGTH` moved to `app/domain/models/auth.py` (domain may not import from API layer; schemas re-exports so P4's import path still works); `RefreshToken.device_name` deliberately without model-level max_length (a long stored value must not 500 the session list; capping sits on both write boundaries); session-list column header fixed + aria-label on revoke. Example-ratchet headroom now **3** (SessionResponse got an example). Test-ID hooks for P11: `session-row/-device/-user-agent/-revoke-<key>`. Flagged for security review: client-supplied persisted free text rendered in the owner's session list (React escapes; data flow to check). Pre-existing, out of strand: HA-test timeout under full-coverage parallel load (`AccountSettingsPageFlows.test.tsx:256`) — follow-up-issue candidate.
- **P6** → `nolte-engineering:fullstack-developer` → **done**, commit `b5553f812`, 26 new API tests (1029 api green), 8 mutations killed. Precedence rule implemented: **body wins entirely** — non-empty body token ⇒ no `verify_csrf`, no Set-Cookie, rotated token in body, cookie ignored; invalid body token ⇒ 401 and the cookie is NOT spent (proven); `null`/absent body ⇒ cookie path incl. CSRF unchanged; `""` ⇒ 422. Mechanics refutation: `Depends(get_refresh_token_from_cookie)` would 401 before the body is seen — cookie declared inline via `Annotated[str | None, Cookie(...)]`, same helper called in-handler, `common/auth.py` untouched. `RefreshRequest` reused with constraints (cap 512) + example (ratchet headroom 3→4). `response_model=TokenPairResponse | TokenResponse` — union order is load-bearing, pinned by tests. Measured behavior delta: non-empty non-JSON body now 422 (was ignored); no known client affected. Findings recorded: **native clients cannot use `/auth/logout`** (verify_csrf → 403 without CSRF cookie) — intentional, documented in docstring, P9 must state revocation happens via `DELETE /users/me/sessions/{key}`; **`/auth/refresh` carries no rate limit** — follow-up-issue candidate. P10 must qualify REQ-023's double-submit table: CSRF on `/auth/refresh` applies to the cookie path only. P8 attack surface: cookie+body combinations, foreign user's body token with own valid cookie, log hygiene of raw refresh token on the body path, non-JSON fuzz ⇒ 422.
- **P7** → `nolte-engineering:fullstack-developer` → **done**, commit `432d8d418`. 16 vitest cases (QRCodeSVG wrapped not stubbed, so QR assertions can't pass on a fake); full suite 390 files / 3819 tests green at 4 workers, coverage over all thresholds, `ConnectDeviceDialog.tsx` at 98/94/100/100. Six mutation classes killed; two close/refresh state-reset guards are honestly documented as not DOM-observable (memory-lifetime hygiene, commented instead of a pretend test). Deviations accepted: `useCountdownTimer` NOT reused (beeps at zero; reset closes over construction-time total) — 6-line effect instead; refresh only in expired state; `fireEvent` in fake-timer tests (userEvent deadlocks against frozen clock). Trap recorded: `QRCodeSVG` renders two paths, the first is the constant background square — "QR changed" helpers must require ≥2 paths. data-testids for P11: `connect-device-button`, `connect-device-dialog`, `connect-device-close`, `loading-skeleton`, `device-pairing-qr`, `device-pairing-countdown`, `device-pairing-expired`, `device-pairing-refresh`, `device-pairing-error`. Dialog closes → session list reloads so a freshly paired device appears. UI flow for P9 delivered. Open (out of strand): `pages.auth.*` DE strings mix Sie/du — separate sweep candidate.
- **P8** → `nolte-engineering:integration-test-generator` → **done**, commit `c86c0423f`, 16 tests / 8 properties (1038 api green), 13 mutations killed, no production code changed. All eight security properties hold. **F-1 (real, measured defect — availability):** the redemption rate limit is proxy-blind — slowapi's limiter uses `get_remote_address` while the throttle uses `resolve_client_ip`, so behind Traefik all callers share one limiter bucket; 10 failed attempts from one address return 429 to a *different* address (measured with a throwaway probe). At `rate_limit_device_pairing_redeem = "10/minute"` an attacker can DoS device pairing globally for a minute with 10 requests, and the `settings.py` comment wrongly claims per-IP ("household behind NAT"). NOT frozen as expected behavior — **follow-up-issue candidate** (change limiter `key_func` to `resolve_client_ip`, assess jointly with the known X-Forwarded-For spoofability). F-2 (not a defect): tenant memberships resolve per-request (tested), `is_platform_admin` is a token claim refreshed on rotation — pre-existing REQ-023 behavior identical to browser login. For P9: `/auth/refresh` non-empty non-JSON body ⇒ 422 without spending the cookie (native clients must send `Content-Type: application/json`); redeem returns exactly `{access_token,token_type,expires_in,refresh_token}`, sets no cookie, yields exactly one revocable session; 401 generic / 423 with minutes (code NOT consumed) / 429. For P10: document what holds — lockout per source-IP, rate-limit global (F-1), lockout→store order, per-request authorization (paired device loses tenant access immediately on membership removal); no aspirational rate-limit wording while F-1 is open.
- **P9** → `kamerplanter:mkdocs-documentation` → **done**, commit `81f221a58` (+130 lines each in `docs/{de,en}/api/authentication.md`). New "Gerätekopplung (QR-Code)" section, `mkdocs build --strict` exit 0, DE/EN 1:1 heading mirror, verified against actual router/schemas/service source (no contradictions). Rate limit worded only as "rate limit exceeded" (no per-IP claim, per F-1). Links to existing session-management user-guide page rather than duplicating.
