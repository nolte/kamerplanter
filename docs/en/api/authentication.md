# Authentication

Kamerplanter supports two authentication methods: **local accounts** (email + password) and **federated accounts** (OAuth 2.0 / OIDC via Google, GitHub, Apple, or generic providers). For machine-to-machine integrations (Home Assistant, CI/CD), **API keys** are available.

!!! note "Light Mode"
    In light mode (`KAMERPLANTER_MODE=light`), authentication is not required. All auth endpoints under `/auth/...` are disabled in this mode. This section applies to full mode only.

---

## Token Model

| Token | Validity | Transport | Renewal |
|-------|---------|-----------|---------|
| Access Token (JWT) | 15 minutes | `Authorization: Bearer <token>` | Via refresh token |
| Refresh Token | 30 days | HttpOnly cookie `kp_refresh` | Rotation on every renewal |

The **access token** is a signed JWT (HS256). It contains the user ID and expires after 15 minutes. It should be kept in application memory — never in localStorage.

The **refresh token** is set as an HttpOnly cookie. It is not readable by JavaScript, protecting against XSS attacks. On every call to `/auth/refresh`, the token is rotated — the old token is invalidated and a new one issued.

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
    Token-mutating endpoints (`/refresh`, `/logout`, `/logout-all`) require the `X-CSRF-Token` header. The CSRF token is set as a regular cookie `kp_csrf` and is readable by JavaScript. It is renewed on login and refresh.

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

API keys enable machine access without interactive login — for example for Home Assistant, Grafana, or CI/CD pipelines.

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
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token validity in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token validity in days |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Enforce email verification before first login |
| `KAMERPLANTER_MODE` | `full` | `light` disables all authentication |
| `FERNET_KEY` | — | Encryption key for OIDC provider secrets |

---

## See Also

- [API Overview](overview.md) — URL structure and deployment modes
- [Error Handling](error-handling.md) — Auth-specific error codes
