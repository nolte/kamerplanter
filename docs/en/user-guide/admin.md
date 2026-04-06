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

## Frequently Asked Questions

??? question "Who can assign the platform-admin role?"
    The platform-admin role can only be assigned by an existing platform admin — directly via the API or in the admin area. During initial setup, the first registered user is automatically configured as platform admin.

??? question "Can a platform admin view tenant data?"
    Yes. Platform admins have read access to all tenant-scoped data. This permission should be restricted to trusted individuals and accompanied by an audit log (REQ-024).

??? question "Is there a viewer role for the admin area?"
    Yes. The platform role `viewer` grants read access to all admin statistics and tenant overviews, but no write permissions.

---

## See Also

- [Tenants & Gardens](tenants.md) — Tenant management as tenant-admin (REQ-024)
- [Privacy (GDPR)](privacy.md) — Data subject rights and GDPR compliance
- [Authentication](../api/authentication.md) — JWT, OAuth2/OIDC, service accounts
