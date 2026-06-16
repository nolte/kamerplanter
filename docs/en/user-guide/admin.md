# Platform Admin Area

The platform admin area is exclusively accessible to users with the platform role **admin**. It enables platform-wide management of all tenants and users — independent of the tenant-scoped tenant-admin role.

---

## Prerequisites

- Platform role **admin** (distinct from the tenant-admin role)
- Access via `/admin/platform` (in full mode)

!!! warning "Do not confuse with tenant-admin"
    The platform-admin role is a **platform-wide** special role. It grants access to data across all tenants. The tenant-admin role, by contrast, is limited to a single tenant and is assigned via **Settings > Tenants > Members**.

---

## Distinction: Platform-Admin vs. Tenant-Admin

| Function | Platform Admin | Tenant Admin |
|---------|---------------|-------------|
| Manage all tenants | Yes | No |
| Platform-wide user management | Yes | No |
| View tenant statistics | Yes | No |
| Configure OIDC providers | Yes | No |
| Manage own tenant's members | Yes | Yes |
| Tenant locations and plant data | Yes | Yes |

---

## Tenant Management

In the **Admin > Tenants** section you can:

- View all platform tenants (name, slug, member count, creation date)
- Deactivate or delete individual tenants
- View tenant quotas and limits
- Manage a tenant's members on their behalf

!!! danger "Deleting a tenant is irreversible"
    Deleting a tenant removes all associated data (plants, runs, logs). This action cannot be undone. Create a data export for the affected tenant beforehand.

---

## User Management

In the **Admin > Users** section you can:

- View all user accounts on the platform
- Lock or deactivate user accounts
- Assign platform roles (`admin`, `viewer`)
- Trigger password resets for users
- Process GDPR requests (data deletion, data access)

!!! note "GDPR requests"
    Data subject rights under GDPR Art. 15–21 are available to users via the self-service API at `/api/v1/privacy/`. As a platform admin, you can view and process requests in the admin area. See [Privacy (GDPR)](privacy.md) for details.

---

## Statistics

The **Admin > Statistics** section provides an overview of:

- Number of active tenants and users
- Active planting runs platform-wide
- Celery task queue status
- Storage usage (ArangoDB, TimescaleDB, Redis)

---

## OIDC Providers

Under **Admin > OIDC Providers** you configure federated authentication providers (e.g. Google, GitHub, corporate OIDC instances). These settings apply platform-wide to all tenants.

See [Authentication](../api/authentication.md) for details.

---

## Enabling Plant Photo Identification

[Photo identification](plant-identification.md) is an optional feature that requires API credentials from a third-party service. As long as no key is configured, the backend reports `available: false` and the entire camera/upload UI remains hidden for all users.

The Pl@ntNet API key is an **instance-wide setting** — a single key applies to all users of the instance. The free tier allows 500 identifications per day across the entire instance.

!!! note "Platform admin required"
    Only users with the platform role **admin** can manage the API key. The setting applies platform-wide.

### Step 1: Obtain a free Pl@ntNet key

1. Open [my.plantnet.org](https://my.plantnet.org) in a browser
2. Create an account or sign in
3. Navigate to **Account** > **API key**
4. Copy the displayed API key

!!! warning "Non-commercial use only"
    The Pl@ntNet free tier is explicitly licensed for non-commercial use. For commercial instances review the terms of use at [my.plantnet.org](https://my.plantnet.org).

### Step 2: Enter the key via the Admin UI (recommended)

This is the **preferred method** — no pod restart required, no file changes, takes effect immediately.

1. Sign in as a platform admin
2. Open **Account Settings** (click your profile picture in the top right)
3. Select the **Integrations** tab
4. Scroll to the **Plant Identification** section
5. Enter the copied API key in the **Pl@ntNet API Key** field
6. Click **Save**

The key is stored in masked form — it is never visible in plain text in API responses or logs. The field indicates whether the key is sourced from the database (UI entry), from an environment variable, or is not set at all.

**Optional: Test the key immediately**

After saving, click **Test Connection**. The backend sends a test request to Pl@ntNet and reports whether the key is valid and how many requests remain for today.

**Optional: Remove the key**

Click **Remove** to delete the database-stored key. If no environment variable is set either, photo identification is deactivated immediately.

---

### Alternative: Set the key as an environment variable

The environment variable `PLANTNET_API_KEY` remains fully supported — it is suitable for automated deployments, GitOps workflows, or when UI access is not used.

!!! warning "Priority: UI value takes precedence"
    If a key is stored in the database via the Admin UI, it **overrides the `PLANTNET_API_KEY` environment variable**. A key set via the UI takes effect immediately without a pod restart. The environment variable is only used when no database entry exists.

=== "Production / Kubernetes"

    Create a Kubernetes Secret and load it into the backend via `envFrom`. **Never** commit the key in plain text in `values.yaml`.

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PLANTNET_API_KEY="your-api-key" \
      --namespace kamerplanter
    ```

    Reference the secret in Helm values:

    ```yaml
    # helm/kamerplanter/values.yaml (excerpt)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

    After the next rollout the backend automatically reads the key from the secret environment variable.

=== "Local dev (kind / Skaffold)"

    For quick testing without a Kubernetes Secret: add the variable directly to the `env:` block of the backend container in `helm/kamerplanter/values.yaml`. **Do not commit.**

    ```yaml
    # helm/kamerplanter/values.yaml (local only, do not commit)
    backend:
      env:
        PLANTNET_API_KEY: "your-api-key"
    ```

    Skaffold redeploys the change automatically.

=== "Docker Compose"

    Add the key to the `.env` file in the repository root:

    ```bash
    # .env (do not commit)
    PLANTNET_API_KEY=your-api-key
    ```

    Restart the stack:

    ```bash
    docker compose up -d
    ```

### Step 3: Verify activation via API

Call the status endpoint:

```bash
curl -s http://localhost:8000/api/v1/recognition/status | python3 -m json.tool
```

Expected response when the key is correctly set:

```json
{
  "available": true,
  "adapter": "plantnet",
  "daily_limit": 500,
  "remaining_today": 498
}
```

After successful configuration, the camera/upload function and the **Add by Photo** button in the species overview appear automatically in the UI. Users see the consent dialog the first time they use the feature — from that point on it is fully functional.

### Optional fine-tuning

The following variables do not usually need to be changed. They have sensible default values. A full description is available in the [Environment Variables reference](../reference/environment-variables.md#photo-identification-req-029):

| Variable | Default | Purpose |
|----------|---------|---------|
| `IDENTIFICATION_PRIMARY_ADAPTER` | `plantnet` | Preferred adapter (extensible) |
| `IDENTIFICATION_CONFIDENCE_AUTO_ACCEPT` | `0.85` | Threshold for "very certain" highlighting |
| `IDENTIFICATION_CONFIDENCE_MIN_SHOW` | `0.10` | Minimum confidence required to show a result |
| `IDENTIFICATION_MAX_IMAGE_SIZE_MB` | `10` | Maximum image size in megabytes |
| `IDENTIFICATION_RATE_LIMIT_PER_USER_DAY` | `0` | Max requests per user per day (`0` = adapter limit) |

### Privacy note

Photos are **not** stored on the Kamerplanter server — they are transmitted to Pl@ntNet (CIRAD/INRIA, France/EU) for analysis only and discarded immediately afterwards. EXIF metadata (GPS, camera model) is stripped before transmission. Each user must consent to image transfer once. Full details: [Privacy (GDPR) — Photo Identification](privacy.md#photo-identification-plant_identification).

---

## Frequently Asked Questions

??? question "Who can assign the platform-admin role?"
    The platform-admin role can only be assigned by an existing platform admin — directly via the API or in the admin area. During initial setup, the first registered user is automatically configured as platform admin.

??? question "Can a platform admin view tenant data?"
    Yes. Platform admins have read access to all tenant-scoped data. This permission should be restricted to trusted individuals and accompanied by an audit log (REQ-024).

??? question "Is there a viewer role for the admin area?"
    Yes. The platform role `viewer` grants read access to all admin statistics and tenant overviews, but no write permissions.

??? question "Where exactly in the UI do I find the Pl@ntNet key setting?"
    Open **Account Settings** (click your profile picture in the top right) → **Integrations** tab → **Plant Identification** section. There you can enter, test, and remove the key. The setting is only visible to users with the platform role **admin**.

??? question "Can I also set the key as an environment variable instead of using the UI?"
    Yes. The environment variable `PLANTNET_API_KEY` remains fully supported and is suitable for GitOps workflows or automated deployments. Important: a key stored in the database via the Admin UI takes **precedence** over the environment variable and takes effect immediately without a pod restart.

??? question "What happens when the daily limit is exhausted?"
    The backend reports `remaining_today: 0`. The UI shows the message "Daily identification limit reached. Available again tomorrow." The limit resets daily at midnight UTC. All other features remain fully available.

??? question "Can I use a different recognition service instead of Pl@ntNet?"
    Currently Pl@ntNet is the only implemented adapter (`IDENTIFICATION_PRIMARY_ADAPTER=plantnet`). A phase-2 extension for local offline recognition (without a third-party service) is planned.

---

## See Also

- [Tenants & Gardens](tenants.md) — Tenant management as tenant-admin (REQ-024)
- [Privacy (GDPR)](privacy.md) — Data subject rights and GDPR compliance
- [Authentication](../api/authentication.md) — JWT, OAuth2/OIDC, service accounts
- [Identify Plant by Photo](plant-identification.md) — End-user guide
- [Environment Variables](../reference/environment-variables.md) — Full variable reference
