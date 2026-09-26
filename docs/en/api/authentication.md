# Authentication

Kamerplanter supports two authentication methods: **local accounts** (email + password) and **federated accounts** (OAuth 2.0 / OpenID Connect (OIDC) via Google, GitHub, Apple, or generic providers). For machine-to-machine (M2M) integrations (Home Assistant, CI/CD), **API keys** are available.

!!! note "Light Mode"
    In light mode (`KAMERPLANTER_MODE=light`), authentication is not required. All auth endpoints under `/auth/...` are disabled in this mode. This section applies to full mode only.

---

## Token Model

| Token | Validity | Transport | Renewal |
|-------|---------|-----------|---------|
| Access Token (JWT) | 15 minutes | `Authorization: Bearer <token>` | Via refresh token |
| Refresh Token | 30 days | HttpOnly cookie `kp_refresh` | Rotation on every renewal |

The **access token** is a signed JSON Web Token (JWT) using the HMAC-SHA256 (HS256) algorithm. It contains the user ID and expires after 15 minutes. It should be kept in application memory — never in localStorage.

The **refresh token** is set as an HttpOnly cookie. It is not readable by JavaScript, protecting against Cross-Site Scripting (XSS) attacks. On every call to `/auth/refresh`, the token is rotated — the old token is invalidated and a new one issued.

---

## Registration

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "grower@example.com",
  "password": "secure-password-2026",
  "display_name": "Alex Grower"
}
```

**Password requirements:** At least 10 characters, maximum 128 characters.

**Response (201 Created):**

```json
{
  "key": "usr_abc123",
  "email": "grower@example.com",
  "display_name": "Alex Grower",
  "email_verified": false,
  "is_active": true,
  "avatar_url": null,
  "locale": "de",
  "timezone": "Europe/Berlin",
  "last_login_at": null,
  "created_at": "2026-03-17T10:00:00Z"
}
```

After registration, a personal tenant is automatically created. If email verification is active (`REQUIRE_EMAIL_VERIFICATION=true`), the email address must be confirmed before the first login.

### Email Verification

```http
POST /api/v1/auth/verify-email
Content-Type: application/json

{
  "token": "<token-from-email>"
}
```

---

## Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "grower@example.com",
  "password": "secure-password-2026",
  "remember_me": false
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

The server simultaneously sets the HttpOnly cookie `kp_refresh`. The value of `expires_in` is in seconds (900 = 15 minutes).

**`remember_me: true`** extends the refresh cookie lifetime to 30 days. Otherwise the cookie is a session cookie (expires when the browser is closed).

### Demo Account

A preconfigured demo account is available in development and testing environments:

```json
{
  "email": "demo@kamerplanter.local",
  "password": "demo-passwort-2024"
}
```

!!! warning "Production environment"
    The demo account and demo data must not be active in production environments. Remove the seed step from the deployment configuration.

---

## Using the Access Token

Every API request requiring authentication needs the access token as a Bearer token in the `Authorization` header:

```http
GET /api/v1/t/my-garden/plant-instances/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Renewing the Token

The access token expires after 15 minutes. To renew it, the refresh cookie is sent automatically (the browser includes the cookie for requests to `/api/v1/auth`):

```http
POST /api/v1/auth/refresh
X-CSRF-Token: <csrf-token>
```

!!! note "CSRF Protection"
    Token-mutating endpoints (`/refresh`, `/logout`, `/logout-all`) require the `X-CSRF-Token` header. The Cross-Site Request Forgery (CSRF) token is set as a regular cookie `kp_csrf` and is readable by JavaScript. It is renewed on login and refresh.

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

The old refresh token becomes invalid. The new refresh cookie is set automatically.

---

## Logout

### Sign out current browser session

```http
POST /api/v1/auth/logout
X-CSRF-Token: <csrf-token>
```

Invalidates the current refresh token and deletes the cookie.

### Sign out all sessions

```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access-token>
X-CSRF-Token: <csrf-token>
```

Invalidates all refresh tokens for the user across all devices.

---

## Password Reset

### Request a reset email

```http
POST /api/v1/auth/password-reset/request
Content-Type: application/json

{
  "email": "grower@example.com"
}
```

For security reasons, this endpoint always returns the same success response regardless of whether the email address exists.

### Set a new password

```http
POST /api/v1/auth/password-reset/confirm
Content-Type: application/json

{
  "token": "<token-from-email>",
  "new_password": "new-password-2026"
}
```

---

## Changing Your Password (Signed In)

```http
POST /api/v1/users/me/password
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "current_password": "old-password-2026",
  "new_password": "new-password-2026"
}
```

`current_password` may be omitted only when the account has **no** local password yet (an SSO-only account setting one for the first time) — in that case, confirm instead with a fresh sign-in at the linked provider (next section) or, only if all of its providers cannot do that (GitHub, Apple), with the confirmation code from the section after that. If a local password already exists, it must be supplied correctly — it is a step-up (see below). On success, all of the user's active sessions are terminated.

A request authenticated with an API key is refused with `403 Forbidden` — an API key cannot change its own account's password.

In light mode (`KAMERPLANTER_MODE=light`) the route answers `403 Forbidden`. The instance's single account is used by every request without sign-in, so a password set there would prove nothing about who set it — and it would become a working sign-in once the instance switches to full mode.

---

## Signing In Again to Confirm (OIDC)

An account without a local password has no secret of its own to answer the step-up confirmations two sections down. If at least one of its linked sign-in providers is an **OpenID Connect provider** (Google or a generic OIDC provider with the `openid` scope), it confirms instead with a **fresh** sign-in at exactly that provider — this is the normal case. Only an account whose linked providers are all unable to do that (exclusively GitHub and/or Apple, see the boundary below) falls back to the emailed code.

```http
POST /api/v1/users/me/step-up/oidc
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "action": "account_erasure"
}
```

`action` names the act to confirm, same as for the code, and `target` its target, same as there (required for the targeted actions, see below). The optional `provider_key` (a linked provider's key from `GET /users/me/providers`) picks a specific provider when several OIDC-capable ones are linked; without it, the route takes the first matching one. The optional `client_nonce` (32 hex characters the client generates at random) comes back unchanged beside the token or the error — so the page that started the sign-in recognises its own result and discards a planted one.

**Response (200 OK):**

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=kamerplanter&response_type=code&prompt=login&max_age=0&state=…&nonce=…&code_challenge_method=S256"
}
```

Open `authorization_url` in the browser — the same login request as a normal sign-in, plus `prompt=login` and `max_age=0`: the provider must authenticate the person again (no silent answer from its own session) and report when it did. The provider then redirects to this server's existing callback, which signs nobody in and redirects straight on to `{frontend-url}/auth/step-up/callback`:

- Success: `#step_up_token=<token>&action=<action>&client_nonce=<nonce>` in the URL **fragment** (never the query — a fragment reaches no server, no proxy, and no `Referer` header)
- Error: `?error=step_up_failed` (general), `?error=step_up_stale` (the sign-in was older than five minutes — retry), or `?error=step_up_cancelled` (denied at the provider)

The backend checks the ID token: `iss` is the expected issuer, `aud`/`azp` is this instance, `nonce` matches the request, `exp` has not passed, `sub` is a linked sign-in of **this** account made through **exactly this** provider configuration (the link records configuration and issuer; `iss` must match it), and `auth_time` is a finite number at most five minutes old (30 seconds' clock tolerance). An older link without a recorded configuration counts as re-authenticable only when exactly one enabled, capable configuration of its type exists — otherwise the account confirms with the emailed code. It does **not** check a JWKS signature: the ID token comes straight from the provider's token endpoint over TLS (the fresh sign-in is only offered for an `https` token endpoint), in an exchange this server authenticated with its own client secret — exactly the case OIDC Core 3.1.3.7 item 6 allows TLS protection to stand in for the signature check.

The returned `step_up_token` is valid for five minutes, applies to exactly the requested action (and, for a targeted action, exactly the named target), is spent by the first action that presents it, and is otherwise used like the emailed code: as `step_up_token` in the confirmation body of the respective action (see the table below).

`403 Forbidden` for a request authenticated with an API key, a service account, or a light-mode installation. `422 Unprocessable Entity`: `STEP_UP_PASSWORD_REQUIRED` when the account has a local password (it confirms with that); `STEP_UP_REAUTH_UNAVAILABLE` when none of its linked providers (or the one named by `provider_key`) supports a fresh sign-in — it then confirms with the emailed code —; a validation error when `action` is missing/unknown or `client_nonce` is malformed. `429 Too Many Requests` (`STEP_UP_LOCKED`) while the step-up is locked.

!!! info "Operator requirement"
    The linked identity provider must support `prompt=login`/`max_age` and the `auth_time` claim (Google and most generic OIDC providers do) and serve its token endpoint over `https`. The re-authentication's callback URL is built from `APP_BASE_URL` (`{APP_BASE_URL}/api/v1/auth/oauth/{slug}/callback`), never from the request's Host header — set `APP_BASE_URL` to the public address and register exactly this callback URL with the provider.

---

## Requesting a Confirmation Code by Email (fallback for GitHub/Apple)

**Boundary.** GitHub is plain OAuth2 and issues no ID token — so there is no sign-in time for the previous section to check. Apple does issue an ID token, but without `auth_time`. An account whose linked sign-in methods are **exclusively** GitHub and/or Apple therefore cannot be freshly re-authenticated and confirms instead with a one-time code mailed to its own address — the same proof a password reset relies on. An account with at least one OIDC-capable provider always uses the previous section; the route below refuses it the code (see below).

```http
POST /api/v1/users/me/step-up-code
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "action": "account_erasure"
}
```

`action` names what the code is to confirm — one of the actions in the table below (`account_erasure`, `admin_account_erasure`, `tenant_deletion`, `password_change`, `email_change`, `api_key_creation`, `device_pairing`, `provider_unlink`, `admin_account_update`, `oidc_provider_change`). The code confirms **only** that one action — a code requested for a password change is refused for an erasure attempt, without being spent by the mismatch. The mailed message names the action in plain text, never the target.

**The act's target (`target`).** When the act acts on something other than your own account, `target` names it — otherwise the route answers `422`; for an act on your own account a `target` is `422` as well: <!-- #1884 -->

| Action | `target` |
|---|---|
| `admin_account_update`, `admin_account_erasure` | the other account's key |
| `tenant_deletion` | the tenant's key |
| `provider_unlink` | the provider link's key from `GET /users/me/providers` |
| `oidc_provider_change` | the OIDC configuration's key; `new:<slug>` when creating one |

The code and the `step_up_token` then hold for that target only: a code requested for account A is refused for account B, without being spent. The route checks the target when it issues the factor — it must exist and you must be allowed to act on it (`403` if not; `404` if it doesn't exist; `409` if the slug of a new OIDC configuration is taken).

**Response (202 Accepted):**

```json
{
  "expires_at": "2026-09-25T18:40:00Z",
  "expires_in": 600
}
```

The code is eight digits, valid for ten minutes, and spent by the first action that presents it; a new request replaces a still-valid code with a fresh one — with two exceptions: an **unspent** code younger than 60 seconds is not replaced (otherwise a request would void the code the person is currently typing), and at most **5 codes per account and hour** are sent. It is mailed only to the account's own address — never returned in this response or anywhere else.

`403 Forbidden` for a request authenticated with an API key, a service account, or a light-mode installation (there is no personal account to confirm anything there). `422 Unprocessable Entity`: `STEP_UP_PASSWORD_REQUIRED` when the account already has a local password — it confirms with that, not with a code —; `STEP_UP_REAUTH_REQUIRED` **when at least one of the account's linked providers is OIDC-capable** (see above — the route then says to use the previous section); a validation error when `action` is missing or not one of the values above. `429 Too Many Requests` (`STEP_UP_LOCKED`, `details[0].retry_after_minutes`) while the account's step-up is locked, a still-valid code is younger than 60 seconds, or the hourly code budget is spent.

`503 Service Unavailable` (`STEP_UP_CODE_UNDELIVERABLE`) when the code cannot be delivered by email — for example because the instance has no mail delivery configured, or the mail server reports a failure. Nothing is issued in that case: the code is withdrawn and its budget given back, so neither the 60-second wait nor the hourly budget blocks the next attempt once the operator fixes delivery.

---

## Step-up Confirmation for Irreversible Account Actions and Sign-In Credentials

Ten actions require re-confirmation by the signed-in person, in addition to a valid access token — since version 1.19 this also covers issuing or removing sign-in credentials and a platform admin raising another account's trust: <!-- #1847, #1857 -->

| Action | Route(s) | Typed-back target (body field) | Password / Fresh sign-in / Code |
|---|---|---|---|
| Delete own account (GDPR Art. 17) | `DELETE /users/me`, `POST /privacy/erasure` | own email (`confirm_email`) | own password, if a local one exists — otherwise a `step_up_token` from a fresh sign-in, or, only for GitHub/Apple-only accounts, the emailed code (`step_up_code`) |
| Delete another account (platform admin) | `DELETE /admin/platform/users/{key}` | target's email (`confirm_email`) | the admin's own, otherwise their `step_up_token` or code |
| Delete a tenant | `DELETE /tenants/{slug}`, `DELETE /admin/platform/tenants/{key}` | slug (`confirm_slug`) | own password, otherwise a `step_up_token` or code |
| Change email address | `POST /privacy/email-change` | — | own password, otherwise a `step_up_token` or code |
| Change password | `POST /users/me/password` | — | current (`current_password`) — setting the **first** password on an account without one runs through a `step_up_token` or code instead |
| Issue an API key | `POST /auth/api-keys` | — | own password, otherwise a `step_up_token` or code. **Light Mode:** no step-up — the instance has only the one system account |
| Pair a device by QR code | `POST /auth/device-pairing` | — | own password, otherwise a `step_up_token` or code |
| Remove a sign-in method (provider link) | `DELETE /users/me/providers/{provider_key}` | — | own password, otherwise a `step_up_token` or code |
| Raise another account's trust (platform admin) | `PATCH /admin/platform/users/{key}`, only when `email_verified` or `is_active` flips from `false` to `true` | — | the admin's own, otherwise their `step_up_token` or code |
| Create, change or delete an OIDC provider (platform admin) | `POST /admin/oidc-providers`, `PUT`/`DELETE /admin/oidc-providers/{key}` — not for a `PUT` that only changes `display_name` or `icon_url` (switching it on or off needs it) | — | the admin's own, otherwise their `step_up_token` or code |

!!! info "No automatic revocation of API keys"
    Changing your password, resetting it, and `POST /auth/logout-all` revoke the account's refresh tokens — **not** its API keys. A key represents a deliberately set-up machine integration (Home Assistant, an MCP client); silently invalidating it on every password change would break those integrations without warning. Since this version, a key can only be minted behind this step-up — no longer from a merely stolen session or from another key. Keys are listed under `GET /auth/api-keys` with their creation and last-used timestamps, and each can be revoked individually via `DELETE /auth/api-keys/{key_id}`. <!-- #1847 -->

A request authenticated with an API key, or one coming from a service account, cannot trigger any of these ten actions — including issuing another API key or a pairing code (see the check order below).

Example body for account erasure (local account):

```json
{
  "confirm_email": "gartner@example.com",
  "password": "current-password-2026"
}
```

Example body after a fresh sign-in (OIDC-capable account):

```json
{
  "confirm_email": "gartner@example.com",
  "step_up_token": "AqX7…"
}
```

Example body for an account signed in exclusively through GitHub/Apple:

```json
{
  "confirm_email": "gartner@example.com",
  "step_up_code": "48213907"
}
```

**Check order:**

1. A request authenticated with an API key or coming from a service account is refused with `403 Forbidden` — before anything is checked or counted.
2. If the confirmation is locked (see below), the route immediately answers `429 Too Many Requests` without checking the secret.
3. If the typed-back target doesn't match (email case-insensitively, slug exactly), the route answers `422 Unprocessable Entity`. A wrong echo does **not** count as a failed attempt. Changing the email and changing the password have no target to type back.
4. If the affected account has a local password, the password field must be correct, otherwise `401 Unauthorized`. Otherwise — if the body carries a `step_up_token`, the route checks that (confirming nothing or expired: `401 Unauthorized`). Without `step_up_token`: if the account has an OIDC-capable linked provider, the route answers `401 Unauthorized` with the error code `STEP_UP_REAUTH_REQUIRED` — a hint to sign in again first. Otherwise (GitHub/Apple only), the route checks `step_up_code` instead; missing it answers `401 Unauthorized` with `STEP_UP_CODE_REQUIRED`.

**Throttling:** After 5 wrong confirmations (password, code, or an invalid/expired fresh sign-in) for the same account-and-client-address combination, the system locks further confirmations for **15 minutes**; repeated failures double the wait time up to **4 hours**. An additional account-wide cap of 15 failed attempts applies across any number of client addresses. All nine actions — and requesting a code or a fresh sign-in — share the same failed-attempt budget per account; a successful step-up clears it.

A locked confirmation responds with the error code `STEP_UP_LOCKED`:

```json
{
  "error_code": "STEP_UP_LOCKED",
  "message": "Too many failed confirmations. Try again in 15 minutes.",
  "details": [
    {
      "field": "password",
      "reason": "Too many failed confirmations.",
      "code": "STEP_UP_LOCKED",
      "retry_after_minutes": 15
    }
  ]
}
```

!!! note "The login lockout is unaffected"
    This lock only applies to the five confirmations above and has no effect on `POST /auth/login`. Anyone who locks one of these confirmations — for example, someone with a stolen session — can still sign in normally, end sessions in the **Sessions** tab, and reset the password by email.

!!! info "For operators: two different requirements"
    An account with an OIDC-capable provider (Google, generic OIDC) confirms via the fresh sign-in — that provider needs to support `prompt=login`/`max_age` and `auth_time` (see above), not SMTP. Only an account whose linked providers are exclusively GitHub and/or Apple needs the emailed code, and with it working mail delivery: if the instance runs the console email adapter without debug mode — the production default with no email delivery configured (SMTP or Resend) — the code is never delivered, and such an account then cannot delete itself, delete a tenant, set a first local password, or change its email address. See [Environment Variables](../reference/environment-variables.md#email) for configuration details.

---

## OAuth 2.0 / OIDC (Federated Login)

!!! note "Stub implementation"
    The OAuth/OIDC integration is implemented as a stub. The endpoints exist but do not yet perform a complete authorization code exchange. A full implementation is planned for a future sprint.

### Query available providers

```http
GET /api/v1/auth/oauth/providers
```

**Response:**

```json
[
  {
    "slug": "google",
    "display_name": "Google",
    "icon_url": "https://..."
  }
]
```

### Initiate the OAuth flow

```http
GET /api/v1/auth/oauth/{slug}
```

The server responds with a `302` redirect to the provider's authorization URL. After a successful login at the provider, the user is redirected back to the callback endpoint.

```
GET /api/v1/auth/oauth/{slug}/callback?code=...&state=...
```

The server sets the cookies and redirects to the frontend:

```
{frontend_url}/auth/callback?access_token=...&expires_in=900
```

---

## API Keys (M2M Integration)

API keys enable machine-to-machine (M2M) access without interactive login — for example for Home Assistant, Grafana, or CI/CD pipelines.

### Create an API key

```http
POST /api/v1/auth/api-keys
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "label": "Home Assistant Integration",
  "tenant_scope": "my-garden",
  "current_password": "current-password-2026"
}
```

`tenant_scope` is optional and accepts either the tenant's slug or its key when creating the key. Either way, you must be an active member of the named tenant — otherwise the route answers `403 Forbidden` ("tenant_scope must name a tenant you are an active member of."), with the same message for an unknown tenant and for one you don't belong to.

!!! info "Issuing a key is a step-up"
    Instead of `current_password` you can send `step_up_token` (after a fresh sign-in, see [Signing In Again to Confirm](#signing-in-again-to-confirm-oidc)) or `step_up_code` (after [Requesting a Confirmation Code](#requesting-a-confirmation-code-by-email-fallback-for-githubapple)) — the same rules as in the [step-up table](#step-up-confirmation-for-irreversible-account-actions-and-sign-in-credentials) above. A request authenticated with an API key answers `403 Forbidden` before any password is even checked — a key cannot mint another key. **In Light Mode**, this route issues the instance's one MCP key without a step-up. <!-- #1847 -->

**Response (201 Created):**

```json
{
  "key": "apk_xyz789",
  "label": "Home Assistant Integration",
  "raw_key": "kp_sk_abc...xyz",
  "key_prefix": "kp_sk_abc",
  "tenant_scope": "t-a1b2c3d4",
  "created_at": "2026-03-17T10:00:00Z"
}
```

What is stored and returned is always the tenant's **key**, never the slug you entered at creation. That means renaming the tenant later (a new slug) leaves the scope unaffected, and deleting the tenant deletes the key along with it.

!!! danger "Raw key visible only once"
    The `raw_key` field is only shown at creation and will not be returned again. Store the key immediately in a secure location.

### Use an API key

```http
GET /api/v1/t/my-garden/plant-instances/
Authorization: Bearer kp_sk_abc...xyz
```

The API key is used in the same `Authorization` header as a JWT.

A key created with `tenant_scope` acts only in that tenant. On every route under `/api/v1/t/{slug}/` and on every route that reads the `X-Active-Tenant` header, another tenant answers `403 Forbidden` — even if the key's owner is a member there — with the same response as a tenant the owner does not belong to. Without the header, a scoped key falls back to your personal tenant only if that is its scope; otherwise it sees the shared catalogue only. The match is always against the stored tenant key (see above).

### IP allowlist and rate limit per key

An API key can also carry a CIDR allowlist and its own per-minute request limit. Both restrictions apply identically to the REST API and to the [MCP server](mcp-server.md) — there is **one** shared budget per key, not a separate count per surface.

- If the client address is outside the allowlist or cannot be resolved, the API answers `401 Unauthorized` ("Client IP is not permitted for this API key.") — the same message the MCP server gives for this case.
- If the per-minute budget is spent, the API answers `429 Too Many Requests`. The same response applies if the counter store itself is unreachable — a counter-store outage is never treated as "no limit".

### Account-level routes and a scoped key

A key created with `tenant_scope` is restricted to exactly one tenant. On routes that resolve no tenant — your own account data (`PATCH`/`DELETE /users/me`, password, sessions, linked providers), the [privacy endpoints](../user-guide/privacy.md), managing API keys themselves, device pairing, `POST /auth/logout-all`, or creating/joining a new tenant — it therefore answers `403 Forbidden` ("This API key is restricted to one tenant and cannot act on the account."). It gives the same answer on the few routes under `/t/{slug}/` that change your **account-wide** settings despite the tenant in the path: notification settings and Web Push subscriptions, user preferences, the onboarding state, and removing a favourite. They apply to all your tenants, not only the scoped one. Still admitted: `GET /users/me` (your own identity lookup), `GET /tenants` (lists only the scoped tenant), and every other route that resolves a tenant (`/t/{slug}/`, `X-Active-Tenant`) — the scope still binds there. A key without `tenant_scope` is unaffected by this restriction.

### List API keys

```http
GET /api/v1/auth/api-keys
Authorization: Bearer <access-token>
```

The response lists all keys for the user without the `raw_key` value.

### Revoke an API key

```http
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: Bearer <access-token>
```

---

## Device Pairing (QR Code)

For native mobile apps (e.g. the upcoming Flutter app), Kamerplanter offers QR-code pairing: an already signed-in user displays a QR code in the web frontend, scans it with the app, and receives its own token pair — without ever typing a password on the mobile device. <!-- REQ-023 -->

The flow has three steps: a signed-in client requests a pairing code (1), the app reads the QR code and exchanges it for a token pair (2), and because native clients have no cookie jar, the app renews its access token through a dedicated, cookie-less transport (3).

### Requesting a pairing code

```http
POST /api/v1/auth/device-pairing
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "current_password": "current-password-2026"
}
```

!!! info "Requesting a code is a step-up"
    As with issuing an API key, you can send `step_up_token` or `step_up_code` instead of `current_password` (see the [step-up table](#step-up-confirmation-for-irreversible-account-actions-and-sign-in-credentials) above). A request authenticated with an API key answers `403 Forbidden` — a key cannot mint itself a full session this way. <!-- #1847 -->

**Response (201 Created):**

```json
{
  "payload_version": 1,
  "server_url": "https://garten.example.org",
  "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3",
  "expires_at": "2026-08-11T14:32:41Z",
  "expires_in": 90
}
```

`server_url` comes from the instance's configured base URL — not from the incoming request's URL, which would be unreachable from outside behind a reverse proxy. `expires_in` is already the remaining validity in seconds and stays consistent with `expires_at`.

### QR payload

The QR code the app scans encodes exactly these three fields as JSON:

```json
{
  "v": 1,
  "url": "https://garten.example.org",
  "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3"
}
```

The `v` field (equal to `payload_version`) exists for forward compatibility: a future app version can refuse a payload version it does not recognize instead of misinterpreting it.

!!! note "Light mode: instance discovery as an app-link URL"
    In light mode (`KAMERPLANTER_MODE=light`) there are no accounts and the pairing endpoints answer `404`. The web frontend still shows a QR code there — but **not** a JSON payload: a **plain app-link URL** without a pairing code, pointing at a fixed deep-link path on the instance the browser reached:

    ```text
    https://garten.example.org/connect?v=1
    ```

    The value is a **plain URL string**, not a JSON blob. That is the decisive change over #1118 P12: a phone's system camera does not recognize a JSON string as something openable, whereas it does recognize an `https` URL as a link. The URL is produced entirely in the frontend from `window.location.origin` (the address the user actually reaches the instance through), carries no credential, calls no endpoint and signs nobody in — it is pure instance discovery. The `v=1` query field shares the same version space as the pairing payload's `v`, so the app can refuse a version it does not recognize.

#### App-recognition contract for the discovery link

The discovery link is deliberately an **unverified deep link**. The future Kamerplanter Android app declares an `intent-filter` with a **wildcard host** (`android:host="*"`) on the fixed path `/connect`, so it catches `https://<any-instance>/connect`:

```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="*" android:pathPrefix="/connect" />
</intent-filter>
```

- **Why not verified App Links?** Auto-verified Android App Links bind, via `assetlinks.json`, to **fixed domains declared in the manifest**. Kamerplanter is self-hosted, though — every instance has its own domain, unknown in advance. Auto-verification across arbitrary self-hosted domains is therefore **not feasible**. The contract is consequently an **unverified** deep link with a wildcard host: Android shows an app-chooser when the link is opened (or opens the app directly once the user has set it as the default).
- **Browser fallback:** if the app is not installed, the system camera opens the URL in the browser. The `/connect` path renders a minimal landing page there ("Open in the Kamerplanter app" / "Continue in the browser"), so the link never dead-ends in a 404. The page lives outside the auth guard and the mode switch, so it works in **both** light and full mode.
- **The pairing QR stays deliberately opaque:** the login/pairing QR (`{"v","url","code"}`, above) remains **opaque JSON and in-app-scan-only**. It is deliberately **not** turned into a deep link, because its `code` is a one-time credential: as a system-camera-openable link it could be intercepted and routed to a foreign app. Only the credential-free discovery link may be a publicly recognizable URL.

### Redeeming a pairing code

```http
POST /api/v1/auth/device-pairing/redeem
Content-Type: application/json

{
  "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3",
  "device_name": "Pixel 8 (Greenhouse)"
}
```

This endpoint is **public** — the app has no credential of its own yet at this point; the scanned code is the proof.

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "hZ3JvdzogcmVmcmVzaCB0b2tlbiBmb3IgYSBwYWlyZWQgZGV2aWNl"
}
```

!!! note "Refresh token in the JSON body"
    Unlike the browser login flow (see [Token Model](#token-model)), pairing redemption returns the refresh token in the JSON response body and sets **no** cookie. This is deliberate: native clients have no cookie jar and must receive the token themselves in order to store it securely (e.g. in the Android Keystore).

`device_name` is optional, up to 64 characters, and — when supplied — appears as a label in the [session list](../user-guide/account.md#viewing-and-ending-active-sessions).

### Renewing the access token (native clients)

Because a paired device has no cookie jar, `POST /api/v1/auth/refresh` accepts an optional JSON body in addition to the cookie-based flow:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "hZ3JvdzogcmVmcmVzaCB0b2tlbiBmb3IgYSBwYWlyZWQgZGV2aWNl"
}
```

**Response (200 OK):** identical in shape to the `/device-pairing/redeem` response — `{access_token, token_type, expires_in, refresh_token}` with the rotated refresh token in the body.

When the body is present and carries a refresh token:

- The `X-CSRF-Token` header is **not** required (no cookie is being spent, so there is nothing for CSRF protection to guard).
- **No** cookie is set.
- The rotated refresh token comes back in the JSON body.

If the `refresh_token` field is absent, `null`, or the whole body is empty, the classic cookie path — including the CSRF check — applies instead. If both a body token and a cookie are present, the body wins; the cookie is ignored in that case rather than used as a fallback.

!!! warning "`Content-Type: application/json` is required"
    A non-empty body that is not valid JSON is rejected with `422 Unprocessable Entity`. Native clients must set the `Content-Type: application/json` header.

Rotation is cross-transport: a refresh token rotated via either the body or the cookie invalidates the previous token on **both** transports — there is one rotation, not separate bookkeeping per transport.

### Ending a paired device's session

!!! warning "Native clients cannot use `/auth/logout`"
    `POST /api/v1/auth/logout` checks for the CSRF cookie and answers `403 Forbidden` without it. A paired device never had that cookie in the first place and therefore cannot sign out through it.

A paired device ends its session through the regular session management instead:

```http
DELETE /api/v1/users/me/sessions/{key}
Authorization: Bearer <access-token>
```

Alternatively, it is enough to discard the stored refresh token on the device — the session then simply expires after 30 days without ever having been actively revoked.

### Error responses

| Status | Meaning |
|--------|---------|
| `401 Unauthorized` | "Invalid or expired pairing code." — applies equally to an unknown, an already-redeemed, and an expired code. There is deliberately **no** distinguishable response, so a request cannot be used as an oracle for a code's state. |
| `423 Locked` | The source address is locked out after too many failed redemption attempts; the response states the remaining lockout duration in minutes. The most recently used code is **not** consumed by this — the same QR code can be redeemed again once the lockout ends, as long as its own (short) validity period has not yet expired. |
| `429 Too Many Requests` | The rate limit for the redemption endpoint has been exceeded. |

### Security notes

!!! danger "Never show the pairing code as plain text next to the QR code"
    Display the pairing code only as a QR code, never additionally as readable text on the same screen — otherwise a single glance over your shoulder is enough to impersonate the paired device. Also, only ever scan a QR code you just generated yourself — a QR code from someone else, or an older one, may already be redeemed, expired, or tampered with.

    The pairing code is short-lived (60–120 seconds, configurable) and redeemable only once. It is **not** a password and not a long-lived token — its only purpose is to issue a regular token pair a single time.

---

## Roles and Permissions

Users can be members of multiple tenants and hold a different role in each tenant.

| Role | Description |
|------|-------------|
| `viewer` | Read access to all tenant resources |
| `grower` | Read and write access to plants, runs, and tasks |
| `admin` | Full access including member management and settings |

The role is checked automatically when accessing tenant-scoped endpoints. Endpoints with elevated requirements document their minimum required role in the Swagger UI.

### Platform Admin

The platform admin has access to the platform-wide administration area under `/api/v1/admin/`. This role is controlled via membership in the `platform` tenant with the `admin` role.

---

## Login Protection

After multiple failed login attempts, the account is temporarily locked. The API then responds with `423 Locked` and indicates the remaining lockout duration:

```json
{
  "error_code": "ACCOUNT_LOCKED",
  "message": "Account temporarily locked. Try again in 15 minutes.",
  "details": [
    {
      "field": "account",
      "reason": "Too many failed login attempts. Locked for 15 minutes.",
      "code": "ACCOUNT_LOCKED"
    }
  ]
}
```

---

## Environment Variables (Authentication)

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-...` | Signing key for JWTs — generate in production with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm (HS256 = HMAC-SHA256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token validity in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token validity in days |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Enforce email verification before first login |
| `KAMERPLANTER_MODE` | `full` | `light` disables all authentication |
| `FERNET_KEY` | — | Encryption key for OIDC provider secrets |

---

## See Also

- [API Overview](overview.md) — URL structure and deployment modes
- [Error Handling](error-handling.md) — Auth-specific error codes
