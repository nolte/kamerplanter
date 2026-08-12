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
  "tenant_scope": "my-garden"
}
```

**Response (201 Created):**

```json
{
  "key": "apk_xyz789",
  "label": "Home Assistant Integration",
  "raw_key": "kp_sk_abc...xyz",
  "key_prefix": "kp_sk_abc",
  "tenant_scope": "my-garden",
  "created_at": "2026-03-17T10:00:00Z"
}
```

!!! danger "Raw key visible only once"
    The `raw_key` field is only shown at creation and will not be returned again. Store the key immediately in a secure location.

### Use an API key

```http
GET /api/v1/t/my-garden/plant-instances/
Authorization: Bearer kp_sk_abc...xyz
```

The API key is used in the same `Authorization` header as a JWT.

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
```

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

!!! note "Light mode: instance discovery only (URL only)"
    In light mode (`KAMERPLANTER_MODE=light`) there are no accounts and the pairing endpoints answer `404`. The web frontend still shows a QR code there — but a **URL-only variant without a pairing code**, carrying only the instance's address:

    ```json
    {
      "v": 1,
      "url": "https://garten.example.org"
    }
    ```

    The `code` field is deliberately absent here; the payload shares the same `v` version space, so an app tells the two cases apart purely by the presence or absence of `code`: "point this app at this instance" (no `code`) versus "sign this device in" (`code` present). The URL variant is produced entirely in the frontend (from the instance address the browser reached), carries no credential, calls no endpoint and signs nobody in — it is pure instance discovery.

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
