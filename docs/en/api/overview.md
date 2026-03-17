# API Overview

The Kamerplanter API is a REST API built on [FastAPI](https://fastapi.tiangolo.com/). All endpoints return JSON and follow standard HTTP conventions. An interactive Swagger UI is available at `/api/v1/docs`.

---

## Base URL

```
http://localhost:8000/api/v1
```

In production environments, the API is exposed through Traefik as the ingress controller under the configured domain.

## Interactive Documentation

| URL | Content |
|-----|---------|
| `/api/v1/docs` | Swagger UI — try all endpoints interactively |
| `/api/v1/redoc` | ReDoc — readable reference documentation |
| `/api/v1/openapi.json` | OpenAPI schema (JSON) — for code generation |

---

## Deployment Modes

The API behaviour depends on the configured deployment mode. The current mode is exposed by the mode endpoint:

```http
GET /api/v1/mode
```

```json
{
  "mode": "full",
  "features": {
    "auth": true,
    "multi_tenant": true,
    "privacy_consent": true
  }
}
```

### `full` (Default)

Full operation with authentication, multi-tenancy, and GDPR features. All auth endpoints are active. Every request must be authenticated (except `health`, `mode`, and public OAuth callbacks).

### `light`

Enabled via `KAMERPLANTER_MODE=light`. No login required — all endpoints are accessible without authentication. Suitable for local single-user installations without multi-tenant requirements. The auth routers (`/auth/...`) are disabled in this mode.

!!! warning "Light mode is not for multi-user production"
    In light mode there is no access control. Only use this mode for isolated local instances.

---

## URL Structure

The API distinguishes between **global resources** and **tenant-scoped resources**.

### Global Resources

Master data such as plant species, botanical families, and IPM reference data is global — it does not belong to any single tenant.

```
GET  /api/v1/species/
GET  /api/v1/species/{key}
GET  /api/v1/botanical-families/
GET  /api/v1/cultivars/
GET  /api/v1/ipm/pests/
GET  /api/v1/starter-kits/
```

### Tenant-Scoped Resources

All user-specific data (plants, runs, sensors, tanks, etc.) belongs to a tenant and is addressed via the tenant slug in the URL:

```
/api/v1/t/{tenant_slug}/...
```

Examples:

```
GET  /api/v1/t/my-garden/plant-instances/
POST /api/v1/t/my-garden/planting-runs/
GET  /api/v1/t/my-garden/tanks/
GET  /api/v1/t/my-garden/tasks/
```

The tenant slug is automatically generated from the username at registration (personal tenant). For community gardens a separate tenant can be created.

### Health Endpoints

Health endpoints require no authentication and are intended for Kubernetes liveness and readiness probes:

```
GET /api/v1/health/live    → {"status": "alive"}
GET /api/v1/health/ready   → {"status": "ready", "database": true}
GET /api/health            → {"status": "healthy", "version": "...", "mode": "..."}
```

---

## Endpoint Groups

The following table lists all available router groups. In full mode, `auth`, `oidc-providers`, and `platform-admin` routes are additionally active.

| Group | Path Prefix | Description | REQ |
|-------|------------|-------------|-----|
| Authentication | `/auth` | Login, registration, tokens, OAuth (full mode only) | REQ-023 |
| Users | `/users` | Own profile, change password | REQ-023 |
| Tenants | `/tenants` | Tenant CRUD, memberships | REQ-024 |
| Tenant Scope | `/t/{slug}/...` | All tenant-scoped resources | REQ-024 |
| Botanical Families | `/botanical-families` | Plant family master data | REQ-001 |
| Species | `/species` | Plant species master data | REQ-001 |
| Cultivars | `/cultivars` | Cultivar variants | REQ-001 |
| Locations | `/sites`, `/locations`, `/slots` | Location and slot hierarchy | REQ-002 |
| Substrates | `/substrates` | Substrate types and batches | REQ-019 |
| Plant Instances | `/plant-instances` | Individual plant tracking | REQ-001 |
| Phase Control | `/phases`, `/growth-phases` | Growth phases and transitions | REQ-003 |
| Planting Runs | `/planting-runs` | Batch management | REQ-013 |
| Tanks | `/tanks` | Tank states and fills | REQ-014 |
| Fertilizers | `/fertilizers` | Fertilizer master data | REQ-004 |
| Nutrient Plans | `/nutrient-plans` | EC-based nutrition plans | REQ-004 |
| Watering Events | `/watering-events` | Irrigation log | REQ-004 |
| IPM | `/ipm` | Pest and disease management | REQ-010 |
| Harvest | `/harvest` | Harvest documentation and pre-harvest interval gate | REQ-007 |
| Tasks | `/tasks` | Task planning and workflows | REQ-006 |
| Care Reminders | `/care-reminders` | Automated care schedules | REQ-022 |
| Calendar | `/calendar` | iCal feeds and calendar events | REQ-015 |
| Onboarding | `/onboarding` | Setup wizard | REQ-020 |
| Starter Kits | `/starter-kits` | Preconfigured packages | REQ-020 |
| User Preferences | `/user-preferences` | Experience level, language | REQ-021 |
| Calculations | `/calculations` | EC/VPD calculations | REQ-004 |
| Enrichment | `/enrichment` | GBIF/Perenual data enrichment | REQ-011 |
| Import | `/imports` | CSV import for master data | REQ-012 |
| Companion Planting | `/companion-planting` | Mixed cultivation recommendations | REQ-028 |
| Crop Rotation | `/crop-rotation` | Rotation validation | REQ-002 |
| Health | `/health` | Liveness and readiness | — |

---

## Request and Response Format

All request bodies and responses use `application/json`. An explicit `Content-Type: application/json` header is required for POST/PUT/PATCH requests.

### Pagination

List endpoints support `skip` and `limit` as query parameters:

```http
GET /api/v1/species/?skip=0&limit=50
```

Defaults: `skip=0`, `limit=100` (varies by endpoint).

### Date Format

All dates and timestamps follow ISO 8601 in UTC:

```
2026-03-17T10:30:00Z
```

---

## Rate Limiting

Sensitive endpoints are rate-limited to prevent abuse:

| Endpoint Group | Default Limit |
|---------------|--------------|
| Auth endpoints (`/auth/login`, `/auth/register`) | 20 requests/minute per IP |
| General API endpoints | 100 requests/minute |

When exceeded, the API responds with HTTP `429 Too Many Requests`.

---

## CORS Configuration

Allowed origins are configured via the `CORS_ORIGINS` environment variable as a comma-separated list:

```bash
CORS_ORIGINS=https://app.kamerplanter.example.com,https://admin.kamerplanter.example.com
```

By default, `http://localhost:3000` and `http://localhost:5173` (Vite dev server) are allowed.

---

## Security Headers

Every API response includes the following security headers:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Strict-Transport-Security` | Active (only outside debug mode) |

---

## See Also

- [Authentication](authentication.md) — Token workflow and API keys
- [Error Handling](error-handling.md) — Error structure and error codes
- [Local Development Setup](../development/local-setup.md) — Running the backend locally
