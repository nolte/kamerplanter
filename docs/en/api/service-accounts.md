# Service Accounts & API Keys

!!! info "API only / operator configuration"
    You set up service accounts and the restrictions of an API key through the REST API; there is no screen for it yet. <!-- REQ-023 §5b, Issue #2137 -->

A **service account** is an account for a machine instead of a person — Home Assistant, Grafana,
a CI/CD pipeline. It belongs to exactly one garden (tenant), never signs in with a password and
works with API keys only. No integration has to run on your personal key, and you can take its
access away at any time without touching your own.

---

## What makes a service account

- **No password, no sign-in, no session.** A login with its address is refused.
- **Exactly one garden.** It is created as a member with the role **viewer** or **grower** — never as a lead, without administrative scopes. The member administration does not raise it to lead either (`403`).
- **Its API keys work in this garden only.** Every key is bound to the garden: a call in another garden answers `403`, and so does every account-level route.
- **It founds no garden and accepts no invitation** (`403`).
- **It takes a seat** of the garden's member limit.
- Its address is random and undeliverable (`sa-…@service.example.com`); it receives no email.

---

## Prerequisites

- You are a **lead** in the garden **and** hold the technical administrative scope (`technical`). Both are read from your stored membership.
- You confirm every change with your own password (step-up). Without a local password you request a code or sign in again — action `service_account_change`, target: the garden's key when creating, `<garden-key>|<service-account-key>` when rotating and removing.
- A request that is itself authenticated with an API key may do none of this (`403`).
- Light mode has no service accounts (`403`).

---

## Create a service account

```bash
curl -X POST "https://kamerplanter.example.com/api/v1/t/my-garden/service-accounts" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Home Assistant",
    "role": "grower",
    "ip_allowlist": ["192.168.1.0/24"],
    "rate_limit_per_minute": 600,
    "expires_at": "2027-04-01T00:00:00+02:00",
    "current_password": "<your current password>"
  }'
```

**Response (`201 Created`):**

```json
{
  "key": "8f3c…",
  "display_name": "Home Assistant",
  "role": "grower",
  "membership_key": "51a0…",
  "api_key": {
    "key": "a7d2…",
    "label": "Home Assistant",
    "raw_key": "kp_…",
    "key_prefix": "kp_Xy1aB",
    "tenant_scope": "<key of my-garden>",
    "created_at": "2026-10-05T10:00:00Z",
    "ip_allowlist": ["192.168.1.0/24"],
    "rate_limit_per_minute": 600,
    "expires_at": "2027-03-31T22:00:00Z"
  }
}
```

!!! warning "You see the key once"
    `raw_key` is only in this response (and in the response of a rotation). Only its hash is
    stored. Put it into the integration or a secret manager right away.

**Refusals before your password is asked for:**

| Response | When |
|---|---|
| `403` | You are not a lead with `technical`, the request comes from an API key, or light mode |
| `422` | Role other than `viewer`/`grower`, or one of the key restrictions is unusable (see below) |
| `422 SERVICE_ACCOUNT_LIMIT_REACHED` | The garden already holds as many active service accounts as `TENANT_MAX_SERVICE_ACCOUNTS` allows (default 20) |
| `422 MEMBER_LIMIT_REACHED` | The garden's member limit is reached |

After that: `401` without or with a wrong password, `429 STEP_UP_LOCKED` after too many failures.

---

## The restrictions of an API key

`POST /api/v1/auth/api-keys`, which issues a key for your own account, takes the same three
fields. They apply to the REST API and to the MCP server alike.

| Field | Allowed | Effect |
|---|---|---|
| `ip_allowlist` | At most 32 ranges in CIDR notation; a single address is stored as `/32` or `/128`. No host bits set (`10.0.0.5/8` is refused), nothing wider than `/8` (IPv4) or `/32` (IPv6). Empty or omitted: no restriction | A call from another address answers `401` |
| `rate_limit_per_minute` | 1–10000 | Beyond it `429`; REST and MCP count together |
| `expires_at` | With a timezone, in the future, at most 730 days ahead | After it every call answers `401` |

`GET /api/v1/auth/api-keys` shows the three values for your own keys.

---

## List service accounts

```bash
curl "https://kamerplanter.example.com/api/v1/t/my-garden/service-accounts" \
  -H "Authorization: Bearer {access_token}"
```

The list names every active service account with its role and its keys in this garden —
metadata only (prefix, restrictions, last use, revoked or not), never the key itself.

---

## Rotate a key

```bash
curl -X POST "https://kamerplanter.example.com/api/v1/t/my-garden/service-accounts/{sa_key}/rotate-key" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"overlap_minutes": 30, "current_password": "<your current password>"}'
```

- The new key keeps the **IP allowlist and rate limit** of the newest previous key. You may give it a new expiry with `expires_at`.
- `overlap_minutes` (0–1440, default **0**): with `0` the previous keys are revoked **at once** — the right value when a key got into the wrong hands. With a value above 0 they keep working for that many minutes so you can switch the integration without a gap; after that every call refuses them.
- The response holds the new key (`api_key.raw_key`, this once only), `previous_keys_end_at` (the end of the overlap window, or `null`) and `replaced_key_count`.

!!! tip "Switching without downtime"
    1. Rotate with `overlap_minutes` (e.g. 30).
    2. Put the new key into Home Assistant or the pipeline.
    3. Test. After the window only the new key works.

---

## Remove a service account

```bash
curl -X DELETE "https://kamerplanter.example.com/api/v1/t/my-garden/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "<your current password>"}'
```

Every key of the service account in this garden is revoked at once, its membership ends (tasks
assigned to it lose the assignment), and the account is deactivated. What it wrote keeps it as
the author.

Creating, rotating and removing are recorded in the security audit log, which platform admins
can read.

---

## Use the key

```bash
curl "https://kamerplanter.example.com/api/v1/t/my-garden/sites" \
  -H "Authorization: Bearer kp_…"
```

The key acts with the service account's role in the garden — a `viewer` only reads, a `grower`
may also write, but delete nothing.

---

## What is still missing

!!! warning "Not yet implemented"
    The following will come later: editing a service account, suspending and reactivating it;
    platform-level service accounts for several gardens; a screen in the garden settings. <!-- REQ-023 §5b.0 -->

---

## Frequently asked questions

??? question "Can a service account have several keys?"
    During an overlap window after a rotation, yes — afterwards only the new one works. A
    rotation with `overlap_minutes: 0` never leaves two valid keys.

??? question "What do I do with a compromised key?"
    Rotate with `overlap_minutes: 0` — the old key stops working that moment. If you no longer need
    the integration, remove the service account.

??? question "How does it differ from my own API key?"
    Your own key acts as you, in all your gardens (or the one you restrict it to), with your role.
    A service account is a member of its own with at most grower rights in exactly one garden —
    removing it leaves your access untouched.

## See also

- [Authentication](authentication.md)
- [Error handling](error-handling.md)
- [Environment variables](../reference/environment-variables.md)
- [MCP server](mcp-server.md)
