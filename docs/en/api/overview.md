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

### Getting the OpenAPI schema

There are three ways to get the OpenAPI document — which one fits depends on who needs it and what for:

| Path | Audience | Source |
|------|----------|--------|
| Generate locally from the code | Developers with a local checkout | `task openapi:export` — reproducibly writes the document to `src/backend/openapi.json`, no running database or backend required (gitignored — it is a build artifact and is never checked in) |
| CI workflow artifact | People with access to the GitHub Actions runs | Re-exported on every backend change and linted with [Spectral](https://github.com/stoplightio/spectral) — artifact `openapi` on the corresponding `api-docs` lane run, under "Artifacts" |
| Release asset | External consumers without a checkout, e.g. for client code generation | `https://github.com/nolte/kamerplanter/releases/latest/download/openapi.json` — the recommended path |

Every published release attaches the current OpenAPI document under the stable, version-less name `openapi.json`. This naming is a deliberate choice: it is the only way the permanent link `releases/latest/download/openapi.json` keeps working and always resolves to the most recently published version.

To pin to a specific version instead, download the asset from the [releases overview](https://github.com/nolte/kamerplanter/releases) of the desired tag — releases published before this asset was introduced do not include it.

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
```

---

## Endpoint Groups

The following table lists all available router groups. In full mode, `auth`, `oidc-providers`, and `platform-admin` routes are additionally active.

### Global Endpoints

| Group | Path Prefix | Description | REQ |
|-------|------------|-------------|-----|
| Authentication | `/auth` | Login, registration, tokens, OAuth (full mode only) | REQ-023 |
| Users | `/users` | Own profile, password, sessions | REQ-023 |
| Tenants | `/tenants` | Tenant CRUD, memberships, invitations | REQ-024 |
| Botanical Families | `/botanical-families` | Plant family master data | REQ-001 |
| Species | `/species` | Plant species master data | REQ-001 |
| Cultivars | `/species/{key}/cultivars` | Cultivar variants (nested under species) | REQ-001 |
| Lifecycle Configs | `/species/{key}/lifecycle` | Lifecycle configurations per species | REQ-003 |
| Growth Phases | `/growth-phases` | Global phase definitions | REQ-003 |
| Plant Phases | `/plant-instances/{key}/phases` | Phase transitions for individual plants | REQ-003 |
| Profiles | `/profiles` | Requirement and nutrient profiles | REQ-004 |
| Location Types | `/location-types` | Location type master data | REQ-002 |
| Substrates | `/substrates` | Substrate types and batches | REQ-019 |
| Enrichment | `/enrichment` | GBIF/Perenual data enrichment | REQ-011 |
| Family Relationships | `/family-relationships` | Pest risks and compatibility per plant family | REQ-001 |
| Companion Planting | `/companion-planting` | Mixed cultivation recommendations | REQ-028 |
| Crop Rotation | `/crop-rotation` | Rotation validation | REQ-002 |
| IPM (global) | `/ipm` | Pests, diseases, treatments — master data | REQ-010 |
| Calculations | `/calculations` | EC/VPD/sun position calculations, vernalization, slot capacity | REQ-004 |
| Care Reminders | `/care-reminders` | Automated care schedules | REQ-022 |
| Starter Kits | `/starter-kits` | Preconfigured packages | REQ-020 |
| Import | `/import` | CSV import for master data | REQ-012 |
| Activities | `/activities` | Activity definitions (watering, fertilizing, etc.) | REQ-006 |
| Activity Plans | `/activity-plans` | Activity plan generation and application | REQ-006 |
| Knowledge Base | `/knowledge` | RAG-based search and AI answers (optional) | — |
| MCP Server | `/mcp` | Tool interface for external LLM clients (service-account auth, opt-in) | REQ-033 |
| Observations | `/observations` | TimescaleDB status | REQ-005 |
| Health | `/health` | Liveness and readiness | — |
| Mode | `/mode` | Current deployment mode (full/light) | REQ-027 |

### Tenant-Scoped Endpoints (`/t/{slug}/...`)

| Group | Path Prefix | Description | REQ |
|-------|------------|-------------|-----|
| Sites | `/sites` | Site CRUD, location hierarchy, sensors | REQ-002 |
| Locations | `/locations` | Areas and sub-locations | REQ-002 |
| Slots | `/slots` | Slot management within locations | REQ-002 |
| Plant Instances | `/plant-instances` | Individual plant tracking | REQ-001 |
| Planting Runs | `/planting-runs` | Batch management, phases, diary | REQ-013 |
| Tanks | `/tanks` | Tank states, fills, maintenance, sensors | REQ-014 |
| Fertilizers | `/fertilizers` | Fertilizers, stocks, incompatibilities | REQ-004 |
| Nutrient Plans | `/nutrient-plans` | EC-based nutrition plans, channels, dosages | REQ-004 |
| Feeding Events | `/feeding-events` | Fertilization event documentation | REQ-004 |
| Watering Events | `/watering-events` | Irrigation log with confirmation | REQ-004 |
| Watering Logs | `/watering-logs` | Detailed irrigation protocol | REQ-004 |
| IPM (tenant) | `/ipm` | Tenant-specific inspections and treatments | REQ-010 |
| Harvest | `/harvest` | Harvest documentation and pre-harvest interval gate | REQ-007 |
| Tasks | `/tasks` | Task planning, workflows, queue | REQ-006 |
| Calendar | `/calendar` | iCal feeds, sowing calendar, season overview | REQ-015 |
| Onboarding | `/onboarding` | Setup wizard | REQ-020 |
| Starter Kits | `/starter-kits` | Kit application for tenants | REQ-020 |
| User Preferences | `/user-preferences` | Experience level, language | REQ-021 |
| Favorites | `/favorites` | Plant favorites and nutrient plan matching | — |
| Nutrient Calculations | `/nutrient-calculations` | Mixing protocol, flushing, runoff, mixing safety, water mix, EC budget | REQ-004 |
| Notifications | `/notifications` | Notifications, preferences, test delivery | REQ-022 |
| Observations | `/observations` | Sensor data CRUD (TimescaleDB) | REQ-005 |
| Print Views | `/print` | PDF export for nutrient plans, care lists, plant labels | REQ-032 |

### Admin Endpoints

| Group | Path Prefix | Description | REQ |
|-------|------------|-------------|-----|
| Platform Admin | `/admin/platform` | Statistics, tenant and user management | REQ-024 |
| OIDC Providers | `/admin/oidc-providers` | Federated authentication providers | REQ-023 |
| Settings | `/admin/settings` | Home Assistant configuration, plant identification (masked) | REQ-018 / REQ-029 |
| Plant Identification Settings | `/admin/settings/plant-identification` | Manage Pl@ntNet API key (set, test, remove) | REQ-029 |

The plant identification settings endpoints are exclusively accessible to users with the platform role **admin**. The key is never returned in plain text in any response.

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/admin/settings` | Platform settings including `plant_identification` (key source + masked flag) |
| `PUT` | `/admin/settings/plant-identification` | Save Pl@ntNet API key (replaces any existing database entry) |
| `POST` | `/admin/settings/plant-identification/test` | Test the key against Pl@ntNet — returns validity status and remaining daily quota |
| `DELETE` | `/admin/settings/plant-identification` | Remove the stored key from the database |

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
- [Service Accounts](service-accounts.md) — M2M access (planned, not yet implemented)
- [MCP Server](mcp-server.md) — external LLM clients as a Kamerplanter tool
- [Local Development Setup](../development/local-setup.md) — Running the backend locally
