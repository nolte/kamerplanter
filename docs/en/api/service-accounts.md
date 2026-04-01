# Service Accounts & API Keys

!!! warning "Not yet implemented"
    Service Accounts are specified (REQ-023 v1.7) but **not yet implemented**. This page describes the planned behavior. The endpoints documented here are not yet available.

Service Accounts enable machine-to-machine (M2M) communication between external systems
and the Kamerplanter API — without using personal user credentials. Typical use cases
are Home Assistant, Grafana, CI/CD pipelines, and automated monitoring systems.

---

## Concept

Service Accounts are independent, non-interactive accounts of type `account_type: 'service'`.
Unlike human accounts (`account_type: 'human'`), the following applies:

- No password, no SSO login
- Authentication exclusively via API key (Bearer token)
- No interactive login possible
- Configurable rate limits and IP restrictions per account

### Tenant-scoped vs. Platform-scoped

| Type | Created by | Access | Example |
|------|-----------|--------|---------|
| **Tenant-scoped** | Tenant admin | Only resources within the own tenant | Home Assistant, Grafana per tenant |
| **Platform-scoped** | KA Admin (Platform Admin) | Global and cross-tenant data | Backup system, enrichment pipeline |

---

## Prerequisites

- Tenant admin role in the relevant tenant (for tenant-scoped accounts)
- Platform admin role (for platform-scoped accounts)

---

## Creating a Service Account

### Tenant-scoped Service Account

```bash
curl -X POST "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Home Assistant Tent 1",
    "description": "Delivers sensor data and controls light/ventilation for tent 1",
    "rate_limit_rpm": 500,
    "allowed_ip_ranges": ["192.168.1.0/24"]
  }'
```

**Response (201 Created):**

```json
{
  "_key": "sa_abc123",
  "display_name": "Home Assistant Tent 1",
  "account_type": "service",
  "status": "active",
  "api_key": "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "rate_limit_rpm": 500,
  "allowed_ip_ranges": ["192.168.1.0/24"],
  "created_at": "2026-03-28T10:00:00Z"
}
```

!!! warning "API key visible only once"
    The `api_key` value is only returned in plain text at creation time.
    Afterwards, the system only stores the SHA-256 hash. Write down the key immediately
    in a secure location (e.g., a secret manager).

### Platform-scoped Service Account

```bash
curl -X POST "https://api.kamerplanter.example.com/api/v1/service-accounts/" \
  -H "Authorization: Bearer {platform_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Backup Pipeline",
    "description": "Nightly data backup for all tenants",
    "rate_limit_rpm": 200
  }'
```

---

## Using the API Key

Send the API key as an `Authorization: Bearer` header with every request:

=== "curl"

    ```bash
    curl -X GET "https://api.kamerplanter.example.com/api/v1/t/my-garden/plants/" \
      -H "Authorization: Bearer kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ```

=== "Python (httpx)"

    ```python
    import httpx

    API_KEY = "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    BASE_URL = "https://api.kamerplanter.example.com"

    client = httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
    )

    response = client.get("/api/v1/t/my-garden/plants/")
    response.raise_for_status()
    plants = response.json()
    ```

=== "Python (requests)"

    ```python
    import requests

    API_KEY = "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    BASE_URL = "https://api.kamerplanter.example.com"

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {API_KEY}"

    response = session.get(f"{BASE_URL}/api/v1/t/my-garden/plants/")
    response.raise_for_status()
    plants = response.json()
    ```

!!! note "Key format"
    All API keys carry the prefix `kp_`. The backend recognizes this prefix and routes
    the request into the API key authentication path (instead of JWT validation).

---

## Key Rotation

### Manual Rotation

Generate a new key and revoke the old one. Rotation is recommended regularly
(every 90 days) or after suspected compromise.

```bash
# Generate a new key (the old one remains active for now)
curl -X POST "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}/rotate-key" \
  -H "Authorization: Bearer {access_token}"
```

**Response:**

```json
{
  "new_api_key": "kp_live_yyyyyyyyyyyyyyyyyyyyyyyy",
  "old_key_revoked_at": "2026-03-28T11:00:00Z"
}
```

!!! tip "Rotation workflow"
    1. Generate new key via `rotate-key`
    2. Enter the new key in the external application (Home Assistant, CI/CD)
    3. Test the connection with the new key
    4. The old key is automatically invalid after the rotation request

### Suspending a Service Account

```bash
curl -X PATCH "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"status": "suspended"}'
```

---

## Configuring the IP Allowlist

Restrict access to specific IP ranges (CIDR notation):

```bash
curl -X PATCH "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_ip_ranges": [
      "192.168.1.0/24",
      "10.0.0.0/8"
    ]
  }'
```

Requests from non-allowed IPs receive a `403 Forbidden` response.

!!! tip "No restriction"
    Set `allowed_ip_ranges` to `null` or omit the field to allow access from all IP
    ranges (default for new service accounts).

---

## Rate Limits

Each service account has a configurable rate limit in requests per minute (RPM).

| Value | Meaning |
|-------|---------|
| `null` | Global default (1000 RPM) |
| `500` | 500 requests per minute |
| `100` | Restrictive access for external partners |

When exceeded, the API responds with `429 Too Many Requests` and the header
`Retry-After: <seconds>`.

---

## Permissions

Service accounts are subject to the same permission matrix as human users.
A tenant-scoped service account with a viewer role can only read tenant resources;
a service account with a grower role can also write.

The role is set at creation:

```bash
curl -X POST ".../service-accounts/" \
  -d '{
    "display_name": "Grafana Read-Only",
    "role": "viewer"
  }'
```

Available roles: `admin`, `grower`, `viewer` (identical to human members).

---

## Practical Example: Setting Up Home Assistant

This example shows the complete setup process for a Home Assistant integration.

### Step 1: Create the service account

```python
import httpx

# Log in with your personal account (tenant admin)
auth = httpx.post(
    "https://api.kamerplanter.example.com/api/v1/auth/login",
    json={"email": "admin@my-garden.com", "password": "..."},
)
token = auth.json()["access_token"]

# Create a service account for Home Assistant
sa = httpx.post(
    "https://api.kamerplanter.example.com/api/v1/t/my-garden/service-accounts/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "display_name": "Home Assistant",
        "description": "Sensor ingestion and actuator control",
        "role": "grower",
        "rate_limit_rpm": 1000,
        "allowed_ip_ranges": ["192.168.1.100/32"],  # HA host only
    },
)
sa.raise_for_status()
api_key = sa.json()["api_key"]
print(f"API Key (save this now!): {api_key}")
```

### Step 2: Enter the API key in Home Assistant

Enter the key in the Home Assistant Kamerplanter integration
(Settings → Integrations → Kamerplanter):

```yaml
# configuration.yaml (example for REST sensor)
sensor:
  - platform: rest
    name: "Kamerplanter Sensor Push"
    resource: "https://api.kamerplanter.example.com/api/v1/t/my-garden/observations/"
    method: POST
    headers:
      Authorization: "Bearer kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      Content-Type: "application/json"
```

### Step 3: Test the connection

```bash
curl -X GET "https://api.kamerplanter.example.com/api/v1/t/my-garden/service-accounts/me" \
  -H "Authorization: Bearer kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Expected response: Service account details (name, role, last activity).

---

## Listing and Managing Service Accounts

```bash
# List all service accounts for a tenant
curl "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/" \
  -H "Authorization: Bearer {access_token}"

# Retrieve a single service account
curl "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}"

# Delete a service account
curl -X DELETE "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}"
```

---

## Frequently Asked Questions

??? question "Can a service account have multiple API keys simultaneously?"
    No. There is exactly one active API key per service account. A rotation immediately
    invalidates the old key and issues a new one. Plan the rotation so that you can
    enter the new key in the target application before revoking the old one.

??? question "What happens with a compromised API key?"
    Immediately suspend the service account via `status: suspended` and then rotate
    the key. Check the activity logs (`last_active_at`) for suspicious requests.

??? question "How does a service account differ from a regular API key (v1.4)?"
    Service accounts (v1.7) are fully-fledged entities with their own record,
    description, role, and configuration. Simple API keys (v1.4 under `api_keys`) are
    more lightweight but without role assignment and IP restriction.

??? question "Can service accounts access multiple tenants?"
    Tenant-scoped service accounts are restricted to exactly one tenant.
    For cross-tenant access, a platform-scoped service account must be created
    (requires platform admin role).

## See also

- [Authentication](authentication.md)
- [Error Handling](error-handling.md)
- [Environment Variables](../reference/environment-variables.md)
