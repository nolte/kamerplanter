# API Reference

!!! note "Auto-generated"
    This page will be automatically generated from Google-style docstrings via `mkdocstrings`.

For interactive API docs with a running backend:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Print & Export (REQ-032)

All print endpoints are located under the tenant-scoped path `/api/v1/t/{slug}/print/` and require a valid JWT token. Access rights mirror the permissions of the underlying data (REQ-024 RBAC) — anyone who may read a nutrient plan may also print it.

**Common query parameters (all endpoints):**

| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| `locale` | string | `de` | `de`, `en` |
| `format` | string | `pdf` | `pdf`, `csv` (tabular templates only) |

### Nutrient Plan PDF

Exports a complete nutrient plan as a PDF including the phase table, mixing instructions, water configuration, and CalMag / flushing notes.

```
GET /api/v1/t/{slug}/print/nutrient-plan/{plan_key}
```

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `slug` | Tenant slug |
| `plan_key` | ArangoDB key of the NutrientPlan document |

**Response:** `application/pdf` with `Content-Disposition: attachment; filename="nutrient-plan-{plan_key}.pdf"`

**Example:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/my-garden/print/nutrient-plan/nutrient_plans/42?locale=en" \
  -H "Authorization: Bearer <token>" \
  --output nutrient-plan.pdf
```

---

### Care Checklist PDF

Exports all due care tasks for a given date as a checklist with tick boxes, grouped by urgency (overdue, due today, coming up).

```
GET /api/v1/t/{slug}/print/care-checklist
```

**Query parameters (in addition to `locale` and `format`):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | string (ISO 8601) | Today's date | Reference date for due tasks, e.g. `2026-04-01` |

**Response:** `application/pdf` with `Content-Disposition: attachment; filename="care-checklist-{date}.pdf"`

**Example:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/my-garden/print/care-checklist?date=2026-04-15&locale=en" \
  -H "Authorization: Bearer <token>" \
  --output care-checklist.pdf
```

---

### Plant Info Cards / Label PDF

Prints compact info cards with a QR code for one or more plant instances. The QR code contains the deep-link URL to the respective plant in the app.

```
GET /api/v1/t/{slug}/print/plant-labels
```

**Query parameters (in addition to `locale`):**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plant_keys` | string | Yes | — | Comma-separated ArangoDB keys of the plant instances (at least 1) |
| `fields` | string | No | `name,scientific_name,planted_date` | Comma-separated fields to show on the card |
| `layout` | string | No | `grid_2x4` | `single` (A6), `grid_2x4` (8 per A4), `grid_3x3` (9 per A4) |
| `qr_size_mm` | integer | No | `25` | QR code side length in mm (min: 20, max: 60) |

**Possible values for `fields`:**

`name`, `scientific_name`, `family`, `planted_date`, `current_phase`, `location`, `cultivar`, `note`

The QR code is always included and cannot be deselected via `fields`.

**Response:** `application/pdf` with `Content-Disposition: attachment; filename="plant-labels.pdf"`

**Example — 8 cards per A4 page with plant name, scientific name and planting date:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/my-garden/print/plant-labels\
?plant_keys=plant_instances/101,plant_instances/102,plant_instances/103\
&fields=name,scientific_name,planted_date,location\
&layout=grid_2x4\
&qr_size_mm=25\
&locale=en" \
  -H "Authorization: Bearer <token>" \
  --output labels.pdf
```

**Error codes:**

| HTTP status | Meaning |
|-------------|---------|
| `400` | Invalid parameters (e.g. unknown `layout` value, `qr_size_mm` out of range) |
| `401` | Not authenticated |
| `403` | No permission for this tenant or resource |
| `404` | Plan key or plant instance key not found |
| `422` | Required parameter missing (e.g. `plant_keys` for `/plant-labels`) |

---

### Bed history and care log (REQ-053)

Read endpoints of the bed history. All need a valid JWT and are open to every member of the tenant; a bed or entry of another tenant answers like a missing one with `404`.

```
GET    /api/v1/t/{slug}/locations/{key}/history                       # care entries + planting events
GET    /api/v1/t/{slug}/locations/{key}/rotation                      # timeline per year (family, nutrient demand, role)
POST   /api/v1/t/{slug}/locations/{key}/history/backfill              # fill in an earlier year (grower and above)
DELETE /api/v1/t/{slug}/locations/{key}/history/backfill/{event_key}  # take a backfilled year back
GET    /api/v1/t/{slug}/care-events                                   # care log of the whole tenant
```

**`GET …/history`** returns the stored care entries of the bed and the planting events **derived** from plants and runs in one list, newest first. Every item carries `kind` (`care_event`, `plant_planted`, `plant_removed`, `run_started`, `run_completed`), `at` and `category` (`planting` or `removal` for planting events). For `care_event` the whole entry is in `care_event`. Here as in `GET /care-events`, a care entry lists the readable names of its plants in `plant_names` (`plant_name`, else `instance_id`, in the order of `plant_keys`; a deleted plant is missing), so the list needs no request per row. `summary` stays the stored text; the app words a position correction itself, with the plant's name.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `category` | – | Only this category (`422` for an unknown one) |
| `plant_key` | – | Only entries that name this plant (runs drop out) |
| `from`, `to` | – | Period, inclusive; `to` before `from` is `422`. An instant without a time zone is read as UTC |
| `performed_by` | – | Account key of a member. Role `viewer`/`grower`: only your own account (`403` otherwise); `lead` and the `management` scope: any member. The `_anonymized` marker cannot be filtered (`422`). Planting events have no performer and drop out |
| `include_corrections` | `false` | Also replaced entries and `position_corrected` |
| `offset`, `limit` | `0`, `50` | Page; `limit` at most 200 |

**`GET …/rotation`** returns for each year the families that stood in the bed (`family_key`, `family_name`, `nutrient_demand`, `plan_role`, `source` = `plant` or `backfill`). `years` defaults to `max(rotation pause of the families involved, 5)`, at most 10 (`422` above).

**`POST …/history/backfill`** takes `{year, season?, species_key?, family_key?, plan_role}`. `year` lies between the current year minus 10 and minus 1 (`422 backfill.year_out_of_range`). A species names its family; a differing `family_key` is `422 backfill.family_mismatch`. Only a fallow year (`plan_role: fallow`) needs no family. The server writes the care entry itself; a client cannot set the `trigger`.

**`GET /care-events`** is the care log of the whole tenant with the same filters plus `location_key` and `include_superseded`. Without a period, bed or plant filter it shows the last 90 days.

---

### Create a mixed culture in one step (REQ-053)

`POST /api/v1/t/{slug}/planting-runs/mixed-culture` creates one run per species of a mixed culture on the same bed, all in one step (role `grower` or higher). Each item of `runs[]` carries in `entry.row_assignment` the rows (counted from 0) its species takes. Every row belongs to exactly one species: when the rows of two items overlap, the API answers `422` before anything is stored. Only items with a row layout (`grid`, `rows`, `triangular`) and a `row_assignment` take part; an area (`zone`), free positions (`free`) and items without a layout take no rows. The error names the pairs in `details[0].conflicts` as `{"runs": [i, j], "rows": [...], "rows_total": n}` (positions in `runs[]`, the shared rows in ascending order and their count), at most 20 pairs with at most 50 rows each; `details[0].pairs_total` gives the number of all pairs, and `details[0].truncated` is `true` when anything was cut. `details[0].field` points at the later item of the first pair.

!!! note "Limit of the check"
    The row index refers to the row grid of its own item (`row_spacing_cm`, `row_direction`, edge margins). When two items use different grids, their plants can stand at the same spot although the index sets are disjoint. The planting dialog lays all species out on one shared grid; when you call the API directly, send the same row settings for every item.

**Error codes:**

| HTTP status | Code | Meaning |
|-------------|------|---------|
| `403` | `FORBIDDEN` | Role `viewer` |
| `404` | `ENTITY_NOT_FOUND` | Bed not found (or not in this tenant) |
| `422` | `layout.row_assignment_overlap` | Two items with a row layout claim the same row index (assuming the same grid, see above) |
| `422` | `layout.spacing_required`, `layout.too_many_positions`, `plan.quota_exceeded` | The layout of one species cannot be computed or exceeds a limit |
| `422` | `VALIDATION_ERROR` with `reference.not_found` | A species or cultivar does not exist or belongs to another tenant |

---

### Switch the crop rotation check per bed (REQ-053)

`PATCH /api/v1/t/{slug}/locations/{key}` (role `grower` or higher) takes two fields for the crop rotation check that `POST …/locations/{key}/validate-planting` and `GET …/locations/{key}/rotation` evaluate:

| Field | Values | Meaning |
|-------|--------|---------|
| `rotation_enabled` | `true`, `false`, `null` | `true` switches the check on for this bed, also for pots (`planter`), tents (`tent`) and shelves (`shelf`), where it is otherwise off. `false` switches it off. `null` (default) follows the location type |
| `rotation_exempt` | `true`, `false` | Permanent crop (asparagus, berry shrubs): the check is off whatever `rotation_enabled` says. `null` is not allowed |

When the check is off, both routes answer `rotation_applicable: false` with the reason in `not_applicable_reason`: `rotation.not_applicable.rotation_exempt`, `rotation.not_applicable.disabled` (switched off for the bed) or `rotation.not_applicable.container` (pot, tent, shelf without a switch). Both fields are also part of the garden plan's JSON backup; an older file without them gives a bed that is not exempt and follows its location type. In the file both must be JSON booleans (`"yes"` or `1` gives `validation.invalid`), and the import refuses a bed with both set to `true` with `import.rotation_exempt_and_enabled`.

The switch also governs the check per plant place: when the check is off for a bed, `POST …/plant-instances` with a `slot_key` and `POST …/planting-runs/{key}/create-plants` no longer refuse a planting in that bed with `ROTATION_VIOLATION`, and `POST …/plant-instances/slots/{slot_key}/validate-planting` reports it as valid.

**Error codes:**

| HTTP status | Code | Meaning |
|-------------|------|---------|
| `403` | `FORBIDDEN` | Role `viewer` |
| `404` | `ENTITY_NOT_FOUND` | Bed not found (or not in this tenant) |
| `422` | `patch.rotation_exempt_and_enabled` | After the change both `rotation_exempt` and `rotation_enabled` would be `true`; to exempt a switched-on bed, send `rotation_enabled: null` with it |
| `422` | `VALIDATION_ERROR` | `rotation_exempt: null` or a value that is not a boolean |

---

### Garden Plan (PDF, SVG, JSON backup)

Three exports of one site's garden plan (REQ-053). All three need a valid JWT and are open to every member of the tenant. A site of another tenant answers `404`, like an absent one. Each route allows `RATE_LIMIT_PLAN_EXPORT` requests per account (default 10 a minute) and `RATE_LIMIT_PLAN_EXPORT_TENANT` per tenant (default 30 a minute); above that the API answers `429` with `Retry-After`.

```
GET /api/v1/t/{slug}/print/garden-plan/{site_key}        # PDF
GET /api/v1/t/{slug}/sites/{key}/plan/render.svg         # SVG download
GET /api/v1/t/{slug}/sites/{key}/plan/export             # JSON backup
```

**Partial export of the JSON backup** (GP-FR-172): `scope` is `site` (default), `selection` (exactly the beds named in `keys`; a garden object as `object:<key>`) or `subtree` (the named beds with everything below them). `keys` is a comma-separated list of at most 100, not allowed with `site`. A partial file has no plan settings, holds only the zones of its beds, and references that leave the file are `null`. A key the site does not hold is `404`; `422` for missing, too many or invalid keys (`export.keys_required`, `export.too_many_keys`, `export.keys_not_allowed`, `export.object_key_in_subtree`).

**Query parameters of the PDF and the SVG:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `scale` | `auto` | `auto` or one of `1:20`, `1:25`, `1:50`, `1:75`, `1:100`, `1:125`, `1:150`, `1:200`, `1:250`, `1:300`, `1:400`, `1:500`. `auto` takes the finest scale at which the plan fits the page |
| `paper` | `a4` | `a4` or `a3` |
| `orientation` | `landscape` | `landscape` or `portrait` |
| `layers` | `beds,objects,plants,labels` | Comma-separated: `grid`, `beds`, `objects`, `slots`, `plants`, `labels`. Boundary, scale bar, north arrow and legend are always drawn |
| `locale` | `de` | `de` or `en` |
| `color` | `#2e7d32` | Accent colour of the garden boundary, `#rrggbb` (send the `#` as `%23`) |
| `bed_list` | `false` | PDF only: add a second page with the bed list (name, area, status, sun) |

The response carries `X-Plan-Scale` (for example `1:50`). `X-Plan-Suggested-Paper: a3` appears when A4 would need a scale coarser than 1:200.

The PDF contains no member names, assignments, notes or coordinates. The SVG uses millimetres in its `viewBox` (1 m = 1,000 units) and is delivered as an attachment with `X-Content-Type-Options: nosniff` and `Content-Security-Policy: default-src 'none'` (the SVG carries no `style` element or attribute). The JSON backup carries `schema_version: "1"` with the plan settings, locations, slots and garden objects, but no plants, tasks, events or account references.

**Error codes:**

| HTTP status | Code | Meaning |
|-------------|------|---------|
| `404` | `ENTITY_NOT_FOUND` | Site not found (or not in this tenant) |
| `422` | `plan.empty` | The plan has no boundary and nothing placed on it |
| `422` | `plan.does_not_fit` | PDF only: the fixed `scale` does not fit the paper; choose a coarser scale or A3 |
| `422` | `VALIDATION_ERROR` | A query value outside the lists above |

---

### Garden Plan import (JSON backup)

Restores a plan from the JSON backup above (REQ-053). **Only a lead** may import; a grower or viewer gets `403` before the file is read. A site of another tenant answers `404`. The route allows `RATE_LIMIT_PLAN_IMPORT` requests per tenant (default 3 a minute) and a body of up to 5 MB.

```
POST /api/v1/t/{slug}/sites/{key}/plan/import
```

```json
{
  "mode": "replace",
  "dry_run": true,
  "force": false,
  "confirm_site_name": null,
  "document": { "schema_version": "1", "...": "the file from GET …/plan/export" }
}
```

| Field | Description |
|-------|-------------|
| `mode` | `replace` swaps the site's locations and garden objects for the file's and writes the state it overwrites to the change log first (a snapshot); `merge` only adds |
| `dry_run` | `true` checks the file and answers the report; nothing is written |
| `force` | Lifts only the condition that no bed holds an active plant. Those beds, and the locations above them, then stay |
| `confirm_site_name` | `replace` (not a dry run) needs the exact name of the site |
| `target` | `same_site` (default), `other_site` or `other_tenant`: where the file goes. Keys are always new. For the last two, a reference that is not in the file is never resolved against the site (`null` and `dropped_references[]` with reason `outside_file`/`not_found`). `other_tenant` needs the lead role in the target account; nothing is read from another account |
| `offset_m` | `merge` only: `[dx, dy]` in metres (finite, at most ±1000), added to every shape of the file; `replace` answers `422` `import.offset_requires_merge`, an invalid value `422` |
| `document` | The backup file |

The answer is the same report for a dry run and an applied import: `would_create`, `would_update` and `would_delete` (counts of `locations`, `garden_objects`, `slots`, `plan_settings`), `kept_locations`, `dropped_references[]` (`entity`, `key`, `field`, `reason`), `errors[]` (`field`, `code`, `key`), `applied`, `plan_revision`, `snapshot_written`. A dry run lists geometry and limit violations in `errors[]` with status `200`; an applied import with errors answers `422`.

Keys of the file are never kept: every location, garden object and slot gets a new key. A reference that leaves the file is resolved against the target site only, otherwise it is set to empty and reported in `dropped_references[]`. Links to Home Assistant entities and actuators are never imported.

The frost exposure of a bed (`frost_exposed` in `locations[]`) is part of the file and is taken over as it stands there; `null` means "inherit from the site type". If the field is missing (a file from an older version), the import derives it from `site_conditions.microclimate.frost_risk`: `high` becomes `true`, `low` becomes `false`, everything else inherits.

**Error codes:**

| HTTP status | Code | Meaning |
|-------------|------|---------|
| `403` | `import.forbidden` | Not a lead |
| `404` | `ENTITY_NOT_FOUND` | Site not found (or not in this tenant) |
| `409` | `import.not_empty` | `replace` while a bed holds an active plant; remove the plants or send `force` |
| `409` | `plan.revision_conflict` | Someone saved the plan while the import ran |
| `413` | `REQUEST_BODY_TOO_LARGE` | More than 5 MB |
| `422` | `import.schema_version_missing`, `import.schema_version_unsupported` | The file is no backup of a version this installation reads |
| `422` | `import.unknown_keys` | The file holds top-level parts this version does not know (a newer file) |
| `422` | `import.site_name_mismatch` | `replace` without the exact site name |
| `422` | `import.offset_invalid`, `import.offset_requires_merge` | `offset_m` is not finite or beyond ±1000 m / belongs to `merge` only |
| `422` | `plan.quota_exceeded`, `import.too_deep`, `import.parent_cycle`, `import.duplicate_key`, `import.duplicate_slot_id`, `geometry.invalid`, `geometry.outside_parent`, `bed.overlap`, `slot.outside_bed` | The file breaks a limit or a geometry rule |
| `422` | `import.rotation_exempt_and_enabled` | A bed of the file is a permanent crop (`rotation_exempt: true`) and has `rotation_enabled: true` as well; `details[].field` names `locations[i].rotation_enabled` |
| `429` | | Import budget of the tenant used up; `Retry-After` names the wait |

---

### Garden Plan save: geometry errors

`PUT /api/v1/t/{slug}/sites/{key}/plan/boundary` (the boundary) and `POST …/plan/batch` (a batch of operations) refuse a shape that breaks a geometry rule with `422` `VALIDATION_ERROR` (REQ-053). On the boundary route, a vertex or origin outside the plan's coordinate range (0 to 1000 m) carries `code: "geometry.invalid"`; for a polygon or polyline vertex the entry also carries `point_index`, the position of the first such vertex in `points` (counted from 0). The other shape rules there (dimensions, vertex count, rotation) answer with the generic `code: "value_error"`. In a batch, every geometry defect carries `code: "geometry.invalid"` with `op_index` naming the operation and, for a vertex, `point_index`. Slots and bed templates are saved on their own endpoints in the bed's frame (−1000 to 1000 m) and report an out-of-range vertex the same way.

---

### Earlier states of the plan (snapshots)

A `replace` import writes the plan it overwrites to the change log as an `import_snapshot` (kept as long as the log, one year; a site keeps at most its 20 newest snapshots, and a `replace` or restore that writes a 21st removes the oldest). Both routes are **lead only**; a site of another tenant answers `404`, and so does a snapshot of another site or tenant.

```
GET  /api/v1/t/{slug}/sites/{key}/plan/snapshots                        # list, newest first, paged (limit/offset)
POST /api/v1/t/{slug}/sites/{key}/plan/snapshots/{audit_key}/restore    # { "dry_run": true, "force": false, "confirm_site_name": null }
```

The list names, per snapshot, `audit_key`, `revision`, `at`, `summary`, `changed_by_name` and the number of locations, garden objects, slots and zones, never the plan itself. The restore is a `replace` with the stored plan (same checks and same report as the import; `confirm_site_name` is required unless `dry_run`); the plan it overwrites is saved as a snapshot of its own first. Zones of the site that the snapshot does not name are retired. `409` `import.not_empty` while a bed holds an active plant (`force` lifts that). A `merge` import creates no snapshot.

---

### List Available Templates

Returns a list of all registered print templates.

```
GET /api/v1/print/templates
```

This endpoint is not tenant-scoped and only requires a valid authentication token.

**Example response:**

```json
[
  {
    "type": "nutrient_plan",
    "label_de": "Nährstoffplan",
    "label_en": "Nutrient Plan",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  },
  {
    "type": "care_checklist",
    "label_de": "Pflege-Checkliste",
    "label_en": "Care Checklist",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  },
  {
    "type": "plant_label",
    "label_de": "Pflanzen-Infokarte",
    "label_en": "Plant Info Card",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  }
]
```

---

---

## Browser Push / PWA Notifications

All three endpoints are located under the tenant-scoped path `/api/v1/t/{tenant_slug}/notifications/pwa/` and require a valid JWT token.

### Retrieve the VAPID Public Key

Returns the instance's VAPID public key. The browser requires this key to create a push subscription.

```
GET /api/v1/t/{tenant_slug}/notifications/pwa/vapid-public-key
```

**Response (200):**

```json
{
  "vapid_public_key": "BNm..."
}
```

If no VAPID key pair is configured, the endpoint responds with `503 Service Unavailable`.

---

### Register a Push Subscription

Registers the current device for browser push notifications. The subscription data is provided by the browser after calling `PushManager.subscribe()`.

```
POST /api/v1/t/{tenant_slug}/notifications/pwa/subscribe
```

**Request body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

**Response:** `201 Created` on success, `409 Conflict` if the subscription for this device is already registered.

---

### Deregister a Push Subscription

Removes the subscription for the current device. After this, no browser push notifications will be sent to that device.

```
POST /api/v1/t/{tenant_slug}/notifications/pwa/unsubscribe
```

**Request body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:** `204 No Content` on success, `404 Not Found` if the subscription was not found.

---

### See Also

- [Print Views & Export — User Guide](../user-guide/print-export.md)
- [Fertilization Logic](../user-guide/fertilization.md)
- [Care Reminders](../user-guide/care-reminders.md)
- [Environment Variables — Browser Push (VAPID)](environment-variables.md#browser-push-pwa-vapid)

---

## Site Weather Forecast & Frost Early-Warning <!-- REQ-046 / Issue #392 -->

Both endpoints live under the tenant-specific path `/api/v1/t/{tenant_slug}/` and require a valid JWT token. There is no separate role restriction — any active tenant member (including the **Viewer** role) may read. Both endpoints are **graceful**: if no weather source is configured, no GPS coordinates are stored for the site, or the weather forecast feature is disabled by the operator (`WEATHER_ENABLED=false`), they return empty/`null` forecast fields instead of an error.

### Retrieve a Site's Daily Weather Forecast

Returns the in-horizon daily forecasts for a site (from the [weather source infrastructure](../user-guide/weather-sources.md)) plus the aggregated proactive frost early-warning summary. Backs the "Weather forecast" dashboard widget.

```
GET /api/v1/t/{tenant_slug}/sites/{site_key}/weather-forecast
```

**Response (200):** `SiteWeatherForecastResponse`

```json
{
  "site_key": "sites/42",
  "forecasts": [
    {
      "forecast_date": "2026-07-07",
      "temp_min_c": -1.5,
      "temp_max_c": 6.0,
      "precipitation_mm": 0.0,
      "wind_speed_kmh": 10.0,
      "humidity_percent": 80.0,
      "weather_code": "clear",
      "source": "open-meteo",
      "data_kind": "forecast"
    }
  ],
  "forecast_frost_warning": true,
  "forecast_min_temperature": -1.5,
  "forecast_expected_date": "2026-07-07",
  "forecast_source": "open-meteo"
}
```

| Field | Type | Meaning |
|------|-----|----------|
| `forecasts` | list | Daily forecasts within the configured forecast horizon (default: today + 1 day), each with a provenance label (`source`, `data_kind`) |
| `forecast_frost_warning` | boolean \| null | `true` when at least one day in the horizon reaches a minimum temperature at or below the forecast frost threshold; `null` when no usable forecast is available |
| `forecast_min_temperature` | number \| null | Minimum temperature of the earliest expected frost day |
| `forecast_expected_date` | string \| null | Date of the earliest expected frost day |
| `forecast_source` | string \| null | Weather source that this frost day comes from |

### Additional Fields on a Location's Frost Warning (`Location`)

The existing reactive frost warning now additionally returns the proactive forecast for the site that this location belongs to. The reactive `frost_warning` field is unchanged, so the Home Assistant coordinator stays compatible.

```
GET /api/v1/t/{tenant_slug}/locations/{key}/frost-warning
```

**Response (200):** `FrostWarningResponse` — in addition to the existing fields (`location_key`, `frost_warning`, `temperature_celsius`, `threshold_celsius`, `source`, `entity_id`):

| Field | Type | Meaning |
|------|-----|----------|
| `forecast_frost_warning` | boolean \| null | Proactive forecast for the associated site (additive, see above) |
| `forecast_min_temperature` | number \| null | Expected minimum temperature of the earliest frost day |
| `forecast_expected_date` | string \| null | Date of the earliest expected frost day |
| `forecast_source` | string \| null | Provenance of the underlying forecast |

### See Also

- [Dashboard: Weather Forecast and Frost Early-Warning — User Guide](../user-guide/dashboard.md#weather-forecast-and-frost-early-warning)
- [Notifications: Frost Early-Warning — User Guide](../user-guide/notifications.md#frost-early-warning)
- [Weather Sources per Location — User Guide](../user-guide/weather-sources.md)
- [Environment Variables — Weather Forecast & Frost Early-Warning](environment-variables.md#weather-forecast-frost-early-warning)

---

## Live Sensor Readings of a Location, Site or Tank <!-- REQ-005 / Issue #977 -->

Reads the current states of every Home Assistant sensor attached to the element — storing nothing in the process. The endpoints live under the tenant-specific path `/api/v1/t/{tenant_slug}/` and require a valid JWT token; any active tenant member (including the **Viewer** role) may read.

```
GET /api/v1/t/{tenant_slug}/locations/{key}/sensors/live
GET /api/v1/t/{tenant_slug}/sites/{key}/sensors/live
GET /api/v1/t/{tenant_slug}/tanks/{key}/states/live
```

**Response (200):** `LiveStateResponse`

```json
{
  "readings": {
    "884210": {
      "sensor_key": "884210",
      "sensor_name": "Tent front",
      "metric_type": "temperature_celsius",
      "value": 21.4,
      "last_changed": "2026-08-06T05:12:44Z",
      "last_updated": "2026-08-06T05:12:44Z",
      "last_reported": "2026-08-06T06:03:01Z",
      "entity_id": "sensor.tent_front_temperature",
      "unit": "°C"
    },
    "884211": {
      "sensor_key": "884211",
      "sensor_name": "Tent back",
      "metric_type": "temperature_celsius",
      "value": 23.9,
      "last_changed": "2026-08-06T06:01:10Z",
      "last_updated": "2026-08-06T06:01:10Z",
      "last_reported": "2026-08-06T06:04:55Z",
      "entity_id": "sensor.tent_back_temperature",
      "unit": "°C"
    }
  },
  "values": {
    "temperature_celsius": {
      "sensor_key": "884211",
      "sensor_name": "Tent back",
      "metric_type": "temperature_celsius",
      "value": 23.9,
      "last_changed": "2026-08-06T06:01:10Z",
      "last_updated": "2026-08-06T06:01:10Z",
      "last_reported": "2026-08-06T06:04:55Z",
      "entity_id": "sensor.tent_back_temperature",
      "unit": "°C",
      "sensor_count": 2,
      "superseded_sensor_keys": ["884210"]
    }
  },
  "errors": [],
  "source": "ha_live"
}
```

| Field | Type | Meaning |
|------|-----|----------|
| `readings` | object | **The complete answer**, keyed by sensor key. One entry per sensor that answered — two sensors reporting the same metric are two entries |
| `values` | object | **Derived** single-value view, keyed by metric type. Never more complete than `readings` |
| `errors` | list | One entry per entity that could not be read (`entity_id`, `error`) |
| `source` | string | `ha_live`, or `unavailable` when Home Assistant is not configured at all |
| `message` | string \| null | Explanation for `source: "unavailable"` |

**Fields of a `readings` entry:**

| Field | Type | Meaning |
|------|-----|----------|
| `sensor_key` | string \| null | Document key of the sensor — the key the entry is filed under |
| `sensor_name` | string \| null | Display name of the sensor |
| `metric_type` | string \| null | What the sensor measures, verbatim as configured on the sensor |
| `value` | number | The current reading |
| `last_changed` / `last_updated` / `last_reported` | string \| null | Timestamps from Home Assistant. `last_reported` (Home Assistant 2024.6 and newer) is the most reliable one: it moves on every report, `last_changed` only when the value changes |
| `entity_id` | string \| null | The Home Assistant entity the value came from |
| `unit` | string \| null | Unit of the reading |

**Additional fields of a `values` entry:**

| Field | Type | Meaning |
|------|-----|----------|
| `sensor_count` | integer | How many sensors answered this metric. `1` means nothing was left out |
| `superseded_sensor_keys` | list | Keys of the readings this view does **not** show — look them up in `readings` |

### Selection Rule of the Single-Value View

When several sensors measure the same quantity, `values` shows **the freshest reading**. The measurement instant is read in the order `last_reported` → `last_updated` → `last_changed`; a reading without any timestamp ranks last, and ties are broken by the smaller sensor key. The view is therefore independent of the order the sensors arrive in from the database.

Anyone who needs a different answer reads `readings` and decides for themselves. The frost warning does exactly that: it evaluates **the coldest** air temperature of the location, because a warning reporting the warm edge of the tent would be silent at the cold end.

!!! info "API only / operator configuration: `values` is derived, not authoritative"
    Existing integrations reading `values` keep working unchanged — the map keeps its key and its field names. It is explicitly a summary, though: as long as `sensor_count` is greater than `1` there is more to see, and `readings` shows it. <!-- Issue #977 -->

---

## Site Climate Normals (NASA POWER) <!-- REQ-041 -->

Returns a site's long-term monthly climate normals for the "Climate at the Site" section of the site detail page. The endpoint lives under the tenant-specific path `/api/v1/t/{tenant_slug}/` and requires a valid JWT token; any active tenant member (including the **Viewer** role) may read. Site ownership is verified server-side (404 unknown / 403 foreign). The endpoint is **graceful**: if no climate normals exist yet for an owned site (background fetch not yet run), it returns an empty `normals` list instead of an error.

### Retrieve a Site's Climate Normals

```
GET /api/v1/t/{tenant_slug}/sites/{site_key}/climate-normals
```

**Response (200):** `SiteClimateResponse`

```json
{
  "site_key": "sites/42",
  "normals": [
    {
      "source": "nasa-power",
      "attribution": "Klima- und Strahlungsdaten: NASA POWER (power.larc.nasa.gov)",
      "period_start_year": 1991,
      "period_end_year": 2020,
      "monthly_temp_min_c": [-3.1, -2.6, 0.4, 3.8, 8.2, 11.4, 13.1, 12.8, 9.6, 5.7, 1.3, -1.9],
      "monthly_temp_max_c": [2.4, 3.9, 8.1, 13.2, 18.0, 21.3, 23.6, 23.2, 18.9, 13.1, 7.0, 3.2],
      "monthly_temp_avg_c": [-0.4, 0.6, 4.2, 8.5, 13.1, 16.4, 18.4, 18.0, 14.2, 9.4, 4.1, 0.6],
      "monthly_precip_mm": [42.0, 33.0, 40.0, 37.0, 55.0, 68.0, 62.0, 58.0, 45.0, 39.0, 48.0, 47.0],
      "monthly_solar_mj_m2": [4.1, 7.2, 11.5, 16.3, 19.8, 21.0, 20.4, 17.6, 12.5, 7.4, 4.0, 3.1],
      "coldest_month_min_c": -3.1,
      "annual_temp_avg_c": 8.9,
      "annual_precip_mm": 574.0,
      "fetched_at": "2026-07-01T03:12:00Z"
    }
  ]
}
```

| Field | Type | Meaning |
|------|-----|----------|
| `normals` | list | One entry per contributing source; currently only `nasa-power`. Empty as long as the monthly background fetch hasn't run yet for this site. |
| `source` | string | Provenance identifier of the entry (`nasa-power`) |
| `attribution` | string | The source's license/attribution notice (mandatory CC-BY notice), meant for display directly next to the data |
| `period_start_year` / `period_end_year` | number \| null | Reference period of the climate normal (e.g. `1991`–`2020`) |
| `monthly_temp_min_c` / `monthly_temp_max_c` / `monthly_temp_avg_c` | list[12] | Monthly minimum, maximum, and average temperature, index 0 = January |
| `monthly_precip_mm` | list[12] | Monthly precipitation in mm |
| `monthly_solar_mj_m2` | list[12] | Monthly solar radiation in MJ/m² |
| `coldest_month_min_c` | number \| null | Minimum of the coldest month — an input for the [automatic hardiness-zone derivation](#hardiness-zones-usda) |
| `annual_temp_avg_c` / `annual_precip_mm` | number \| null | Annual average / annual total |
| `fetched_at` | datetime | Time this record was last fetched from the source |

!!! info "API only: triggering climate normals manually"
    There is no dedicated endpoint to manually trigger the fetch for a single site. Population runs exclusively via the monthly Celery task `app.tasks.climate_tasks.fetch_climate_normals` (operator configuration, see [Environment Variables — Climate Normals](environment-variables.md#climate-normals-nasa-power)). <!-- REQ-041 -->

### See Also

- [Climate at the Site — User Guide](../user-guide/weather-sources.md#climate-at-the-site)
- [Environment Variables — Climate Normals (NASA POWER)](environment-variables.md#climate-normals-nasa-power)

---

## Hardiness Zones (USDA) <!-- REQ-039 --> {#hardiness-zones-usda}

Automatic derivation of a site's USDA hardiness zone from its [climate normals](#site-climate-normals-nasa-power) (coldest monthly mean minimum temperature), following the license-free USDA zone schema (26 half-zones `1a`–`13b`, no proprietary USDA/PHZM/PRISM map data). Replaces the free-text `Site.climate_zone` field for the traffic-light comparison, which is kept for compatibility and automatically synced. Feeds the [hardiness traffic light](../user-guide/overwintering.md) for perennial plants. <!-- REQ-039 -->

The global catalog is reference data (like botanical families) and lives without a tenant prefix under `/api/v1/hardiness-zones`; per-site derivation and read access are tenant-scoped under `/api/v1/t/{tenant_slug}/sites/{site_key}/`. All endpoints require a valid JWT token.

### Listing the Global Zone Catalog

```
GET /api/v1/hardiness-zones
```

**Response (200):** A list of `HardinessZoneResponse`, coldest zone first.

```json
[
  {
    "zone": "7a",
    "zone_number": 7,
    "subzone": "a",
    "temp_min_c": -17.7,
    "temp_max_c": -15.0,
    "temp_min_f": 0.0,
    "temp_max_f": 5.0,
    "description_de": "Mild-gemäßigtes Klima weiter Tieflandregionen. Günstige Zone für die Freilandkultur der meisten winterharten Stauden und Gehölze.",
    "representative_regions_de": ["Norddeutsches Tiefland", "Wiener Becken", "Genferseeregion"],
    "typical_last_frost_md": "05-08",
    "typical_first_frost_md": "10-20"
  }
]
```

Only the DACH-relevant zones `5a`–`9a` carry curated German descriptions and example regions; all other zones across the worldwide `1a`–`13b` spectrum have a generic description with no `representative_regions_de`.

### Retrieving a Single Zone

```
GET /api/v1/hardiness-zones/{zone}
```

**Path parameter:** `zone` — the zone label in `<number><a|b>` format, e.g. `7a`.

**Error codes:** `404` when `zone` isn't a valid label in the catalog.

### Reading a Site's Hardiness Zone

```
GET /api/v1/t/{tenant_slug}/sites/{site_key}/hardiness
```

Any active tenant member (including the **Viewer** role) may read. Site ownership is verified server-side (404 for an unknown/foreign site).

**Response (200):** `SiteHardinessResponse`

```json
{
  "site_key": "sites/42",
  "hardiness_zone": "7a",
  "hardiness_zone_source": "derived_gps",
  "hardiness_zone_resolved_at": "2026-07-01T05:00:00Z",
  "mean_annual_minimum_c": -17.2,
  "last_frost_date_avg": "2026-05-08",
  "first_frost_date_avg": "2026-10-20",
  "zone": { "zone": "7a", "...": "full catalog entry, as above" }
}
```

`hardiness_zone_source` ∈ `manual` (never overwritten automatically), `derived_gps` (derived from climate normals). The values `derived_postal` and `frostline_us` are reserved for future, not-yet-implemented derivation paths.

### Re-Deriving a Site's Hardiness Zone

```
POST /api/v1/t/{tenant_slug}/sites/{site_key}/resolve-hardiness-zone
```

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force` | boolean | `false` | When `true`, discards an already **manually** set zone as well and re-derives it from the climate normals. |

Without `force=true`, a manually set zone (`hardiness_zone_source: manual`) is left untouched — the endpoint then returns the existing zone unchanged. It also pre-fills the site's frost reference dates (`last_frost_date_avg`, `first_frost_date_avg`) from the derived zone's catalog entry, when not already set. A regular `PUT` call on the site with `hardiness_zone` set in the request body instead marks the zone directly as `manual`.

**Response (200):** `SiteHardinessResponse` (see above).

**Error codes:**

| HTTP status | Meaning |
|-------------|---------|
| `404` | Site not found or doesn't belong to the tenant |
| `422` | No climate normals with a usable minimum temperature exist yet for the site (`VALIDATION_ERROR`) — [climate normals](#site-climate-normals-nasa-power) must be fetched for the site first |

!!! info "API only: hardiness-zone operation"
    Neither a button to trigger an immediate re-derivation nor a display of the derived zone with its provenance are wired into the site form of the web interface yet. Independent of that, the automatic derivation already runs fully automatically in the background via a quarterly Celery task (see [Environment Variables — Hardiness Zones](environment-variables.md#hardiness-zones-usda)); the endpoint documented here is for triggering an immediate manual re-derivation. <!-- REQ-039 -->

### See Also

- [Climate Zones & Hardiness — User Guide](../guides/climate-zones.md)
- [Overwintering — User Guide](../user-guide/overwintering.md)
- [Site Climate Normals (NASA POWER)](#site-climate-normals-nasa-power)
- [Environment Variables — Hardiness Zones](environment-variables.md#hardiness-zones-usda)

---

## Plant Instances: Removal with Ending Type & Survival Statistics

All endpoints are located under the tenant-scoped path `/api/v1/t/{tenant_slug}/plant-instances/` and require a valid JWT token. <!-- REQ-003 E5/G1 -->

### Remove a Plant (with Optional Ending Classification)

Removes a plant instance. The request body is optional and backward compatible: an empty body (or no body at all) matches the previous plain removal without classification.

```
POST /api/v1/t/{tenant_slug}/plant-instances/{key}/remove
```

**Request body (optional):**

```json
{
  "termination_type": "died",
  "termination_cause": "pest"
}
```

| Field | Type | Required | Values |
|------|-----|---------|-------|
| `termination_type` | string \| null | No | `harvested`, `senesced`, `died`, `cancelled` |
| `termination_cause` | string \| null | No — only valid together with `termination_type: "died"` | `disease`, `pest`, `frost`, `heat`, `drought`, `waterlogging`, `neglect`, `mechanical`, `unknown` |

**Behaviour:**

- Without a body, or with `termination_type: null`: plain removal, as before these fields were introduced — `removed_on` is set, no further classification.
- With `termination_type: "died"`: the current growth phase is **frozen** via the phase-transition engine (the open phase-history entry is closed without triggering a senescence transition), and `termination_cause` is recorded for the loss-cause analysis.
- For any `termination_type` value: open tasks and care reminders for the plant are removed from the queue; completed/skipped tasks remain as history.

**Response (200):** `PlantResponse` — now additionally includes the `termination_type` and `termination_cause` fields (both `null` when not classified).

**Error codes:**

| HTTP status | Meaning |
|-------------|----------|
| `404` | Plant instance not found or does not belong to the tenant |
| `422` | `termination_cause` set but `termination_type` is not `died` (`VALIDATION_ERROR`) |

**Example — loss due to pest infestation:**

```bash
curl -X POST \
  "https://api.example.com/api/v1/t/my-garden/plant-instances/plant_instances/101/remove" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"termination_type": "died", "termination_cause": "pest"}'
```

### Get Survival Statistics

Returns a tenant-wide analysis of all plant instances: survival rate, breakdown by ending type, by growth phase (unplanned losses only), and by loss cause.

```
GET /api/v1/t/{tenant_slug}/plant-instances/survival-stats
```

**Response (200):**

```json
{
  "total": 42,
  "terminated": 18,
  "active": 24,
  "died": 3,
  "survived": 39,
  "survival_rate": 0.9286,
  "by_termination_type": [
    { "termination_type": "harvested", "count": 12 },
    { "termination_type": "died", "count": 3 },
    { "termination_type": "cancelled", "count": 2 },
    { "termination_type": "senesced", "count": 1 }
  ],
  "by_termination_cause": [
    { "termination_cause": "pest", "count": 2 },
    { "termination_cause": "frost", "count": 1 }
  ],
  "loss_by_phase": [
    { "phase_name": "seedling", "count": 2 },
    { "phase_name": "vegetative", "count": 1 }
  ]
}
```

`survived` counts every plant that was **not** an unplanned loss — harvested, naturally senesced, cancelled and still-active plants all count as survived; only `termination_type: "died"` counts as a loss. `loss_by_phase` is aggregated by the resolved phase **name** (not the phase key), so the same canonical phase across different species is summed together, and sorted in descending order by count.

!!! note "Route ordering"
    `/survival-stats` is declared **before** `/{key}` in the router so the literal path is not accidentally captured as a plant key.

### See Also

- [Growth Phases — User Guide: Removing a Plant](../user-guide/growth-phases.md#pflanze-entfernen)
- [Growth Phases — User Guide: Survival Rate and Loss-Cause Analysis](../user-guide/growth-phases.md#ueberlebensrate-verlustursachen)

---

## Plant Instances: Pup Ancestry (`mother_key`)

When a monocarpic mother plant automatically transitions into its final flowering phase, Kamerplanter automatically creates a new plant instance (the pup) and links it to the mother plant. <!-- REQ-003 D10 / REQ-017 -->

### Additional Field in the Plant Instance Response

```
GET /api/v1/t/{tenant_slug}/plant-instances/{key}
```

`PlantResponse` now additionally includes:

| Field | Type | Meaning |
|------|-----|----------|
| `mother_key` | string \| null | Key of the mother plant this instance descended from as a pup. `null` for directly created plants. |

The authoritative ancestry relationship is additionally stored as a `descended_from` graph edge (pup → mother); `mother_key` mirrors it for cheap frontend access without requiring a graph-traversal query.

### Trigger and Behaviour

- The automatic pup spawn is triggered as soon as a plant species configured as monocarpic (`flowering_strategy: "monocarpic"`) automatically transitions into one of its terminal reproductive phases (flowering, fruiting, or ripening).
- Exactly one new plant instance is created; re-evaluating the same transition does **not** create a second pup (idempotent — guarded by the existence of an inbound `descended_from` edge on the mother).
- The pup inherits `tenant_key`, `species_key`, `cultivar_key`, and the mother's location, **but no slot** (`slot_key: null`) — the mother plant keeps its slot while it senesces. Its `planted_on` is set to the transition date.
- In addition to the edge, a `PropagationEvent` with `method: "clone"` is persisted (mother → pup).

!!! note "No dedicated endpoint, no manual trigger"
    The pup spawn is a side effect of the automatic phase transition (see [Growth Phases — Automatic Phase Transitions](../user-guide/growth-phases.md#automatic-phase-transitions)) and has **no** dedicated REST endpoint for manual triggering or for querying propagation history. The full propagation API (ancestry traversal, listing propagation events per plant) remains REQ-017 follow-up work. <!-- REQ-017 -->

### See Also

- [Growth Phases — User Guide: Monocarpic Plants](../user-guide/growth-phases.md#monokarpische-pflanzen)
- [Propagation Management — User Guide](../user-guide/propagation.md#automatische-kindel-fortfuehrung)
- [Database Schema — Plant Instance Graph](database-schema.md#plant-instance-graph)
- [Error Handling](../api/error-handling.md)

---

## Lifecycle Configuration: Derived Field `grown_as_annual`

Botanically perennial species that are cultivated in practice like annuals (the classic example: the tomato) get a derived, read-only flag in the lifecycle response. <!-- REQ-001 / REQ-003 -->

### Additional Field in the Lifecycle Response

```
GET /api/v1/species/{species_key}/lifecycle
```

`LifecycleResponse` additionally includes:

| Field | Type | Meaning |
|------|-----|----------|
| `grown_as_annual` | boolean | `true` when `cultivation_cycle_type == "annual"` while `cycle_type != "annual"` — i.e. the species is cultivated as an annual in practice even though it is not botanically annual. |

!!! note "Derived, not persisted, not a request field"
    `grown_as_annual` is a server-computed response field (`computed_field`): it is re-derived from `cycle_type` and `cultivation_cycle_type` on every request, is never independently stored in the database, and cannot be set via `POST`/`PUT` — a value sent in the request body is ignored.

### See Also

- [Growth Phases — User Guide: Botanical Life Cycle vs. Cultivation Cycle Type](../user-guide/growth-phases.md#botanischer-lebenszyklus-vs-anbau-zyklustyp)

---

## Season & Overwintering Automation

These endpoints read the automatically computed season state of a site and the automatically materialised overwintering profile of a plant. Both are derived without user interaction as soon as a plant is assigned to a frost-exposed location — by default, a location on an outdoor, greenhouse, or balcony site (`OVERWINTERING_SITE_TYPES`), or a location with a manual frost-exposure override on a site of another type (see [Setting Frost Exposure for a Location](../user-guide/locations-substrates.md#setting-frost-exposure-for-a-location)) — on plant creation, on a site change, and additionally as a safety net from the daily season evaluation run — see [Season Automation](../user-guide/season-automation.md) and [Overwintering](../user-guide/overwintering.md) in the user guide. <!-- REQ-047 -->

All endpoints are under the tenant-scoped path `/api/v1/t/{tenant_slug}/` and require a valid JWT token.

### Read a Site's Season State

```
GET /api/v1/t/{tenant_slug}/sites/{site_key}/season-state
```

**Response (200):**

```json
{
  "site_key": "sites/12",
  "season_state_id": "season-4f2a9c1b3d0e",
  "phase": "pre_winter",
  "trigger_tier": "live",
  "trigger_reason_i18n_key": "pages.season.trigger.frostForecast",
  "season_year": 2026,
  "entered_phase_at": "2026-10-18T06:30:00Z",
  "last_min_temp_c": 3.5,
  "forecast_first_frost_date": "2026-10-24",
  "estimated_first_frost_md": "10-20",
  "estimated_last_frost_md": "04-15",
  "evaluated_at": "2026-10-19T06:30:00Z"
}
```

`phase` ∈ `growing`, `pre_winter`, `winter_dormancy`, `pre_spring`. `trigger_tier` ∈ `live`, `climatological`, `calendar` — which cascade tier (see [Season Automation](../user-guide/season-automation.md#where-the-assessment-comes-from-the-three-data-sources)) currently determines the state.

If no season state exists yet for the site, the endpoint evaluates it lazily and persists the result instead of returning `404`.

**Error Codes:**

| HTTP Status | Meaning |
|-------------|---------|
| `404` | Site not found or does not belong to the tenant |
| `409` | Site has no frost exposure: neither is its type `outdoor`, `greenhouse`, or `balcony`, nor is at least one of its locations manually marked frost-exposed — only frost-exposed sites run a season state |

### Season Overview Across All Sites

```
GET /api/v1/t/{tenant_slug}/season/overview
```

Returns `{"states": [ ... ]}` with one `SeasonStateResponse` object (see above) per frost-exposed site of the tenant — that is, sites of type outdoor, greenhouse, or balcony, plus sites of other types with at least one location manually marked frost-exposed. Feeds the "Winter Protection" dashboard widget (see [Personalizing the Dashboard](../user-guide/dashboard-personalization.md)).

### Read a Plant's Overwintering Profile

```
GET /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering
```

**Response (200):** the `OverwinteringProfile` object, including `auto_generated`, `user_overridden`, `derived_path` (`A` = in-situ, `B` = relocated) and `materialized_at`.

**Error Codes:** `404` if the plant has no (materialised) profile — e.g. because it is winter-hardy, is not at a frost-exposed site, or has not yet transitioned into "winter approaching".

### Read a Plant's Overwintering Status

```
GET /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/status
```

Additive, read-only companion to `GET .../overwintering`: always returns `200`, even without a profile at all — useful for the plant detail page to distinguish "winter-hardy", "protection needed, plan pending", and "site not frost-exposed" without abusing the profile endpoint's 404 case for that.

**Response (200):** `PlantOverwinteringStatus` object:

```json
{
  "has_profile": false,
  "hardiness_light": "yellow",
  "will_materialize": true,
  "site_overwinterable": true
}
```

| Field | Meaning |
|-------|---------|
| `has_profile` | Whether an overwintering profile is already materialised. |
| `hardiness_light` | Winter-hardiness rating (`green`, `yellow`, `red`), or `null` if it cannot be determined (e.g. missing species or site assignment). |
| `will_materialize` | Whether a profile is (still) auto-created — `true` only when `site_overwinterable` is true and the rating is not `green`. |
| `site_overwinterable` | Whether the site type is frost-exposed at all (`outdoor`, `greenhouse`, `balcony`). `false` for indoor, windowsill, grow-tent, or an unresolvable site. |

**Error Codes:** none — the endpoint always responds with `200`, even for a foreign or unresolvable plant (protects against a cross-tenant existence oracle via the 404 difference).

### Override an Overwintering Profile

```
PATCH /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering
```

Sets individual fields of the profile and marks it `user_overridden: true`. From then on the automation only fills in missing fields, without overwriting values you've already set.

**Error Codes:**

| HTTP Status | Meaning |
|-------------|---------|
| `404` | Plant or profile not found, or does not belong to the tenant |
| `422` | Invalid value, or the chosen protection measure contradicts the winter-hardiness rating (D5 invariant — e.g. "dig up & store" on a winter-hardy rating) |

### Reset an Overwintering Profile to Automatic

```
POST /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/reset
```

Resets `user_overridden` to `false` and re-materialises the profile fully from the species profile and the site's winter-hardiness rating.

**Error Codes:** `404` if the plant or profile is not found or does not belong to the tenant.

### See Also

- [Season Automation — User Guide](../user-guide/season-automation.md)
- [Overwintering — User Guide](../user-guide/overwintering.md)
- [Environment Variables — Season & Overwintering Automation](environment-variables.md#season-overwintering-automation)
- [Error Handling](../api/error-handling.md)

---

## Plant Identification: Reference Image Contribution (Self-Hosted Recognition)

When creating a plant from a photo identification, a user can optionally contribute the identification photo as a training reference for the self-hosted DINOv2 recognition (see [Assigning the Photo to the New Plant — User Guide](../user-guide/plant-identification.md#assigning-the-photo-to-the-new-plant)). <!-- Issue #447 -->

```
POST /api/v1/t/{tenant_slug}/identification/reference
```

Requires a valid JWT token and at least the tenant role **grower**. Only available when self-hosted DINOv2 recognition is active (`INFERENCE_SERVICE_ENABLED=true`) — the external Pl@ntNet path has no local reference index.

**Request Body:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `image` | file | Yes | JPEG or PNG image, maximum `IDENTIFICATION_MAX_IMAGE_SIZE_MB` |
| `species_key` | string | Yes | Resolved species key the reference image is attached to |

!!! note "No `scientific_name` field"
    The endpoint does **not** expect a `scientific_name` form field. The scientific name is derived server-side from the `species_key` record; any value sent alongside it is ignored.

**Response (202 Accepted):** `ReferenceContributionResponse`

```json
{
  "accepted": true,
  "pending_review": true,
  "species_key": "species/123",
  "dim": 768
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `accepted` | boolean | Whether the contribution was accepted and indexed |
| `pending_review` | boolean | `true` while the contribution is **quarantined** (`is_active=false`) and does not yet affect other users' active recognition. Becomes `false` only after a platform admin approves it. |
| `species_key` | string | The species key the reference image was attached to |
| `dim` | integer \| null | Dimensionality of the computed embedding vector |

**Error Codes:**

| HTTP Status | Meaning |
|-------------|---------|
| `403` | Active tenant role below **grower** (e.g. **viewer**) |
| `403` | The `reference_contribution` consent is missing or was revoked (`CONSENT_REQUIRED`) |
| `404` | `species_key` does not reference a known species |
| `409` | Self-hosted recognition is not enabled (`INFERENCE_SERVICE_ENABLED=false`) |
| `409` | Contributions are disabled in Light mode (REQ-034 §4.1) |
| `413` | Image exceeds `IDENTIFICATION_MAX_IMAGE_SIZE_MB` |
| `415` | `Content-Type` is neither `image/jpeg` nor `image/png` |
| `422` | Image cannot be decoded (corrupt or not a valid image format) |
| `429` | Daily contribution quota (`REFERENCE_CONTRIBUTION_RATE_LIMIT_PER_USER_DAY`) exhausted |

!!! note "Security model (quarantine, provenance, dedup)"
    Every contribution is stored with `source="user_contributed"`, `is_active=false`, and the contributing user and tenant as provenance — it therefore does not affect other tenants' recognition until a platform admin has reviewed it. The dedup key (`source_record_id`) is derived from the tenant, the contributing user, and the SHA-256 hash of the normalized image: re-submitting the same photo updates your own row instead of creating another one. If a different person contributes the same image — even across tenants — they get their own row as of issue #1770; before that, a plain image hash as the key made such a contribution land on the first contributor's row, so that person's erasure also removed the other person's contribution, and the second person's own erasure never reached it. The original image itself is never persisted — only the embedding.

### See Also

- [Identify a Plant by Photo — User Guide: Assigning the Photo to the New Plant](../user-guide/plant-identification.md#assigning-the-photo-to-the-new-plant)
- [Curating Reference Images — User Guide](../user-guide/reference-image-curation.md)
- [Environment Variables — Photo Identification](environment-variables.md#photo-identification-req-029)
- [Error Handling](../api/error-handling.md)

---

## AI Assistant <!-- REQ-031 --> {#ki-assistent}

!!! note "Partially available"
    The endpoints documented here are implemented and active. Of the full specification scope (including background tip-card generation, a tenant-settings endpoint, and provider management via API), only the endpoints listed below have been implemented so far — see the notes in each section.

Every endpoint responds with `404 Not Found` when the platform operator has disabled AI features instance-wide (`AI_FEATURES_ENABLED=false`) — the AI API then effectively doesn't exist. Details on the three-stage toggle: [AI Assistant — User Guide](../user-guide/ai-assistant.md#how-the-ai-assistant-is-structured-three-stage-toggle).

### Knowledge question in Light Mode

!!! warning "Light Mode only"
    `/api/v1/public/ai/ask` and `/api/v1/public/ai/health` exist only with `KAMERPLANTER_MODE=light`. In full mode both paths answer `404`; the knowledge question there is `POST /api/v1/t/{tenant_slug}/ai/knowledge/ask` (see [Tenant-scoped endpoints](#tenant-scoped-endpoints)).

The routes require a signed-in principal (`get_current_user`); in Light Mode that is always the system user without a login, so the Light Mode UI needs no sign-in. IP rate-limited (`AI_PUBLIC_RATE_LIMIT_PER_MIN`, default 10/minute). **No** tenant or plant context is passed to the knowledge base.

```
POST /api/v1/public/ai/ask
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `question` | string | Yes | 3–2000 characters |
| `language` | `de` \| `en` | No | Default: `de` |

**Response (200):** `AiResponseSchema`

```json
{
  "answer_text": "VPD (vapor pressure deficit) describes the difference ...",
  "sources": [
    { "source_key": "vpd-basics", "source_type": "guide", "title": "VPD basics", "score": 0.87, "language": "de" }
  ],
  "language": "de",
  "language_mismatch_warning": false,
  "uses_tenant_data": false,
  "uses_cloud_provider": false,
  "confidence": "high",
  "fallback_species": null,
  "cultivar_hint": null,
  "model_name": "gemma3:12b",
  "provider_type": "ollama",
  "kb_version": "ks-1.4.2-idx-20260420",
  "generated_at": "2026-07-11T10:15:00Z"
}
```

`confidence` is one of `high` | `medium` | `low` | `none` (ADR-002 — drops when the question references a tenant-owned species/cultivar that isn't in the knowledge base).

```
GET /api/v1/public/ai/health
```

**Response (200):** `{ "healthy": true }`

### Tenant-scoped endpoints

The following endpoints live under `/api/v1/t/{tenant_slug}/ai/` and require a valid JWT token plus an active tenant membership. Reads (`GET`) and creating or deleting one's own conversations are open to every member; refreshing, dismissing or marking tips as acted on, `/explain` and sending a message require at least the grower role (`grower`).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ai/tips?context_type=&context_key=&language=` | Tip cards for a context (cache-first) |
| `POST` | `/ai/tips/refresh?context_type=&context_key=&language=` | Force-regenerate tip cards (cache miss) |
| `POST` | `/ai/tips/{tip_key}/dismiss` | Dismiss a tip |
| `POST` | `/ai/tips/{tip_key}/acted-on` | Mark a tip as acted on |
| `GET` | `/ai/daily-tip?language=` | A single tip of the day (may be `null`) |
| `POST` | `/ai/daily-tip/dismiss` | Dismiss today's daily tip |
| `POST` | `/ai/explain` | "Why?" explanation for a concrete item |
| `GET` | `/ai/conversations` | List conversations |
| `POST` | `/ai/conversations` | Start a new conversation |
| `POST` | `/ai/conversations/{conversation_key}/messages` | Send a message — answer streams back as SSE |
| `DELETE` | `/ai/conversations/{conversation_key}` | Delete a conversation immediately (GDPR Art. 17) |
| `GET` | `/ai/providers` | List available providers (read-only) |
| `POST` | `/ai/knowledge/ask` | Free-form knowledge question (grower and up); consent `ai_knowledge_question`, with plant values in `context` also `ai_tenant_data_access`. Response `{ answer, question_type, model, usage, sources[], provider_type, uses_cloud_provider }` — the cloud label comes from the platform's system default provider, because the Knowledge Service answers with its own model. When that model is a cloud model, the route additionally requires `ai_cloud_processing` and the garden's `ai_allow_cloud_providers` (otherwise `403 AI_DISABLED_FOR_TENANT`); the garden's own provider does not count here |

!!! info "API only / operator configuration: enabling for a tenant"
    Every one of these endpoints additionally requires `tenant.settings.ai_features_enabled=true` — there is currently neither a UI nor a dedicated `GET`/`PUT` endpoint for this; the field can only be set directly on the tenant document. Without this, every tenant-scoped endpoint responds with `403` and `{ "detail": "ai.disabled_for_tenant" }` (error code `AI_DISABLED_FOR_TENANT`).

`POST /ai/explain` expects the following request body:

| Field | Type | Description |
|-------|------|-------------|
| `subject_type` | `task` \| `reminder` \| `phase_transition` \| `feeding_event` | Type of the item to explain |
| `subject_key` | string | Key of the item |
| `question_template_id` | string | ID of the curated question template |
| `language` | `de` \| `en` | Optional, default: `de` |

`POST /ai/conversations/{conversation_key}/messages` returns the answer as `text/event-stream` (SSE) with the event types `token` (a single answer token), `done` (the final `AiResponseSchema` as JSON), and `error`.

**Error Codes (all tenant-scoped endpoints):**

| HTTP Status | Error Code | Meaning |
|-------------|-----------|---------|
| `404` | — | AI features disabled instance-wide (stage 1) |
| `403` | `AI_DISABLED_FOR_TENANT` | AI features disabled for this tenant (stage 2) |
| `403` | `CONSENT_REQUIRED` | Required consent missing (stage 3; the missing purpose is named machine-readably in `details[0].purpose`: `ai_knowledge_question`, `ai_tenant_data_access` or `ai_cloud_processing`) |

### Global endpoints (platform admin)

```
GET /api/v1/ai/knowledge-service/health
```

Requires platform admin rights. Only mounted in full mode (`KAMERPLANTER_MODE=full`). Returns `{ "healthy": true|false }`.

### See Also

- [AI Assistant — User Guide](../user-guide/ai-assistant.md)
- [Privacy & GDPR — User Guide](../user-guide/privacy.md)
- [Environment Variables — AI Assistant](environment-variables.md#ki-assistent)
- [Error Handling](../api/error-handling.md)

---

## CV Disease Diagnosis <!-- REQ-038 -->

Photo-based **condition diagnosis** (disease, nutrient deficiency, and — as a secondary category — pest) from a leaf photo, distinct from species identification ([Plant Identification](#plant-identification-reference-image-contribution-self-hosted-recognition)) and from the dedicated [Pest Detection](../user-guide/pest-detection.md): this diagnosis answers "what is wrong with the plant?", not "which species/pest is this?". Recognition runs self-hosted in the inference service; the uploaded photo is stripped of EXIF metadata server-side and is **never persisted** — only a SHA-256 fingerprint is kept (`image_deleted_at` is set on every response).

All endpoints live under the tenant-scoped path `/api/v1/t/{tenant_slug}/cv-diagnosis/` and require a valid JWT token. Read endpoints (`/status`, `/history`) need no special tenant role; write endpoints (`/diagnose`, `/diagnose/{request_key}/confirm`) require at least the **grower** role.

!!! danger "Always a hypothesis — never an automatic treatment"
    Every response carries a never-empty `disclaimer` field. A CV diagnosis **never** automatically triggers a treatment and does **not** bypass any pre-harvest interval gate (see [Integrated Pest Management (IPM)](../user-guide/pest-management.md)) — `POST .../confirm` creates at most an IPM inspection **suggestion** that you review and confirm yourself.

### Check Availability

```
GET /api/v1/t/{tenant_slug}/cv-diagnosis/status
```

**Response (200):** `CvDiagnosisStatusResponse`

```json
{
  "available": false,
  "feature_enabled": false,
  "adapter_key": "local_cv_diagnosis",
  "phenotype_available": false,
  "class_count": 0
}
```

| Field | Type | Meaning |
|------|-----|----------|
| `available` | boolean | Whether the feature can be used (`feature_enabled` **and** a loaded classifier model). Drives whether a future photo-diagnosis button is shown in the frontend. |
| `feature_enabled` | boolean | Operator switch (`CV_DIAGNOSIS_ENABLED`), independent of whether a model is already loaded. |
| `adapter_key` | string | Identifier of the active adapter. Currently only `local_cv_diagnosis` (self-hosted, no image data leaves the instance). |
| `phenotype_available` | boolean | Whether the PlantCV phenotype pipeline is available in the inference service. |
| `class_count` | integer | Number of disease/deficiency/pest classes supported by the loaded classifier. |

### Run a Photo Diagnosis

```
POST /api/v1/t/{tenant_slug}/cv-diagnosis/diagnose
```

Requires at least the tenant role **grower** — the **viewer** role receives `403`. Consent `plant_diagnosis` is required in **Full mode** and is enforced server-side (`403 CONSENT_REQUIRED` without a granted consent); in [Light mode](../user-guide/light-mode.md) the server-side check is skipped, since no consent subsystem exists there (see [Privacy & GDPR](../user-guide/privacy.md)).

**Request Body:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `image` | file | Yes | JPEG or PNG image, maximum `CV_DIAGNOSIS_MAX_IMAGE_SIZE_MB` (default 5 MB) |
| `plant_key` | string | No | Plant instance the diagnosis is attached to |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `phenotype` | boolean | `false` | Also compute PlantCV phenotype metrics (leaf area, green index, discolored/necrotic area ratio) — only effective when `phenotype_available == true` |

**Response (200):** `CvDiagnosisResponse`

```json
{
  "key": "plant_diagnosis_requests/abc123",
  "plant_instance_key": "plant_instances/101",
  "inspection_key": null,
  "classifications": [
    {
      "label": "septoria_leaf_spot",
      "category": "disease",
      "scientific_name": null,
      "probability": 0.74,
      "highlight": false,
      "matched_disease_key": "diseases/septoria",
      "matched_pest_key": null,
      "matched_symptom_slug": null
    }
  ],
  "phenotype": null,
  "model_meta": {
    "model_name": "kamerplanter-leaf-disease-v1",
    "training_base": "imagenet-dinov2-backbone",
    "fine_tuned_on": ["plantdoc-ccby4"],
    "onnx_checksum": "sha256:...",
    "model_version": "20260601",
    "class_count": 17
  },
  "adapter_key": "local_cv_diagnosis",
  "is_confident": false,
  "disclaimer": "Only a hypothesis of the image recognition — not a confirmed diagnosis. Please verify professionally before treating; get a second opinion if unsure.",
  "confirmed_labels": [],
  "image_hash": "sha256:9f86d0...",
  "image_deleted_at": "2026-07-11T14:30:02Z",
  "created_at": "2026-07-11T14:30:00Z"
}
```

| Field | Meaning |
|------|----------|
| `classifications[].category` | `disease`, `deficiency`, `pest`, or `healthy` (no abnormality detected) |
| `classifications[].probability` | Confidence 0.0–1.0. Hits below the display floor (`CV_CLASSIFIER_CONFIDENCE_SHOW`) are dropped and never appear in the list. |
| `classifications[].highlight` | `true` at or above the highlight threshold (`CV_CLASSIFIER_CONFIDENCE_HIGHLIGHT`) — a UI emphasis hint only, **never** an auto-accept |
| `classifications[].matched_disease_key` / `matched_pest_key` | Key matched against the IPM stammdaten ([Integrated Pest Management](../user-guide/pest-management.md)), only set for `category` `disease` or `pest` |
| `classifications[].matched_symptom_slug` | Only set for `category == "deficiency"` — REQ-010 has no dedicated deficiency stammdaten collection (yet), so matching runs via symptom slugs instead |
| `is_confident` | `true` when at least one actionable hit (`disease`/`deficiency`/`pest`) is highlighted. Does **not** mean "confirmed" — it's a UI classification only |
| `model_meta` | Model card / provenance: `fine_tuned_on` lists the training source (`plantdoc-ccby4` — CC BY 4.0; **PlantVillage is not used**, see [License Notices](#license-notices-req-038)) |
| `image_hash` / `image_deleted_at` | Evidence that **no** original image is stored — only the fingerprint is retained |

**Error Codes:**

| HTTP Status | Meaning |
|-------------|---------|
| `403` | Active tenant role below **grower**, or consent `plant_diagnosis` missing (Full mode) |
| `413` | Image exceeds `CV_DIAGNOSIS_MAX_IMAGE_SIZE_MB` or the internal decompression-bomb pixel limit |
| `415` | `Content-Type` is neither `image/jpeg` nor `image/png` |
| `422` | Image cannot be decoded (corrupt or not a valid image format) |
| `503` | The self-hosted classifier is not enabled or not reachable (`CV_DIAGNOSIS_ENABLED=false` or no loaded model) |

### Confirm a Diagnosis into an IPM Inspection Suggestion

```
POST /api/v1/t/{tenant_slug}/cv-diagnosis/diagnose/{request_key}/confirm
```

Requires at least the tenant role **grower**. Creates an [IPM inspection](../user-guide/pest-management.md) as a **suggestion** from the confirmed classes — **never** an automatic treatment; the pre-harvest interval gate always stays active.

**Request Body:**

```json
{
  "plant_key": "plant_instances/101",
  "confirmed_labels": ["septoria_leaf_spot"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `plant_key` | string | Yes | Plant instance the created inspection is attached to |
| `confirmed_labels` | list[string] | No | Class labels to confirm; defaults to the highlighted (`highlight == true`) classes when omitted |

**Response (201):** `ConfirmDiagnosisResponse`

```json
{
  "inspection_key": "inspections/42",
  "detected_disease_keys": ["diseases/septoria"],
  "detected_pest_keys": [],
  "confirmed_labels": ["septoria_leaf_spot"]
}
```

**Error Codes:**

| HTTP Status | Meaning |
|-------------|---------|
| `403` | Active tenant role below **grower** |
| `404` | `request_key` unknown or does not belong to the tenant (cross-tenant access fails indistinguishably — no existence oracle) |

### Retrieve Diagnosis History

```
GET /api/v1/t/{tenant_slug}/cv-diagnosis/history
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | `20` | Maximum number of entries (1–100) |

**Response (200):** List of `CvDiagnosisResponse` (see above), sorted by creation date descending, scoped to the signed-in user's own diagnoses within the current tenant.

### License Notices {#license-notices-req-038}

The classifier is fine-tuned on the **PlantDoc** dataset (CC BY 4.0, attribution required) plus curated own-data field images; the phenotype pipeline uses **PlantCV** (MPL-2.0, used unmodified as a library). **PlantVillage is not used** (license unclear). Full attribution text: [`NOTICE.md`](https://github.com/nolte/kamerplanter/blob/main/NOTICE.md#cv-disease-diagnosis-req-038).

### See Also

- [My Plant Looks Sick — Symptom Diagnosis](../user-guide/plant-health-troubleshooting.md)
- [Pest Detection by Photo](../user-guide/pest-detection.md)
- [Integrated Pest Management (IPM)](../user-guide/pest-management.md)
- [Privacy & GDPR — AI Disease Diagnosis](../user-guide/privacy.md#ai-disease-diagnosis-plant_diagnosis)
- [Environment Variables — CV Disease Diagnosis](environment-variables.md#cv-disease-diagnosis-req-038)

---

## Aquaponics <!-- REQ-026 -->

Aquaponics introduces fish-plant closed-loop systems: fish stock, water tests with automatically calculated free ammonia, biofilter cycling detection, feeding, and nutrient supplementation. The frontend currently covers only part of the API (creating/listing systems, recording a water test, reading cycling progress and water quality) — see [Aquaponics — User Guide: For Technical Users / Self-Hosters](../user-guide/aquaponics.md#for-technical-users-self-hosters) for the full, still UI-less remainder of the API.

**Tenant-scoped** under `/api/v1/t/{tenant_slug}/aquaponics/` (28 endpoints, write calls require at least the **grower** role, deleting a system requires **admin**):

| Resource Group | Endpoints (Selection) |
|-----------------|------------------------|
| Systems | `GET`/`POST /systems`, `GET`/`PATCH`/`DELETE /systems/{key}`, `POST /systems/{key}/cycling-status` |
| Fish stock | `GET`/`POST /systems/{key}/fish-stocks`, `PATCH`/`DELETE /systems/{key}/fish-stocks/{stock_key}`, `POST .../mortality`, `GET .../biomass-history`, `GET .../mortality-rate` |
| Water tests & nitrogen cycle | `GET`/`POST /systems/{key}/water-tests`, `GET /systems/{key}/water-quality-status`, `GET /systems/{key}/nitrogen-cycle-chart`, `GET /systems/{key}/cycling-progress` |
| Feeding | `GET`/`POST /systems/{key}/feeding-events`, `GET /systems/{key}/feeding-recommendation`, `GET /systems/{key}/fcr-analysis` |
| Supplementation & deficiencies | `GET`/`POST /systems/{key}/supplementation`, `GET /systems/{key}/deficiency-check` |
| Safety & health | `GET /systems/{key}/safety-status`, `GET /systems/{key}/alerts`, `GET /systems/{key}/fish-health` |

**Global** (not tenant-scoped, no write access needed) under `/api/v1/fish-species/`:

| Endpoint | Description |
|----------|-------------|
| `GET /fish-species` | All 8 seed fish species with temperature zones and species-specific limits |
| `GET /fish-species/by-temperature-zone/{zone}` | Fish species filtered by temperature zone (`coldwater`, `temperate`, `warmwater`) |
| `GET /fish-species/{species_key}` | A single fish species |
| `GET /fish-species/{species_key}/compatible-plants` | Fish-plant compatibility via graph edges (temperature and nutrient match) |

### See Also

- [Aquaponics — User Guide](../user-guide/aquaponics.md)
- [Tank Management — User Guide](../user-guide/tanks.md)
- [Error Handling](../api/error-handling.md)

---

## Post-Harvest

All endpoints live under the tenant-scoped path `/api/v1/t/{tenant_slug}/post-harvest/` and require a valid JWT token. Read endpoints accept any active membership; write endpoints require at least the **grower** role; deleting a batch is **admin**-only. <!-- REQ-008 -->

| Method & Path | Description | Minimum role |
|---------------|-------------|--------------|
| `GET /post-harvest` | List the tenant's batches (optionally filtered by `harvest_batch`) | any membership |
| `POST /post-harvest/start-drying` | Take a harvest batch into post-harvest processing (stage "drying") | grower |
| `GET /post-harvest/{key}` | Batch details incl. the latest drying measurement and open mold-alert count | any membership |
| `POST /post-harvest/{key}/advance` | Advance the batch to the next stage (forward, one step) | grower |
| `POST /post-harvest/{key}/drying-progress` | Record a weight measurement (optionally also water activity, CO₂, snap-test result) | grower |
| `GET /post-harvest/{key}/drying-progress` | List all drying measurements of the batch | any membership |
| `POST /post-harvest/{key}/observations` | Record an environmental observation (may auto-raise a mold alert) | grower |
| `GET /post-harvest/{key}/observations` | List all environmental observations of the batch | any membership |
| `GET /post-harvest/{key}/mold-alerts` | List the batch's mold alerts | any membership |
| `DELETE /post-harvest/{key}` | Delete a batch | admin |

**Stage state machine:** `drying → curing → stored → released` — forward only, one step per call. The `drying → curing` transition additionally requires `dryness_progress_percent >= 95`.

**Error codes:**

| HTTP status | Meaning |
|-------------|---------|
| `403` | Active tenant role below the required minimum role |
| `404` | Batch not found or does not belong to the tenant |
| `422` | Invalid stage transition (backward, skip, or drying progress < 95% on `drying → curing`), or `current_weight_g` exceeds the batch's start weight |

### Example — Start drying

```bash
curl -X POST \
  "https://api.example.com/api/v1/t/mein-garten/post-harvest/start-drying" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "harvest_batch_key": "harvest_batches/42",
    "species_type": "flower",
    "drying_method": "hang_dry",
    "target_moisture_percent": 10
  }'
```

### See Also

- [Post-Harvest — User Guide](../user-guide/post-harvest.md)
- [Harvest — User Guide](../user-guide/harvest.md)
- [Error Handling](../api/error-handling.md)

---

## Environment Control & Actuators <!-- REQ-018 --> {#environment-control-actuators}

All endpoints live under the tenant-scoped path `/api/v1/t/{tenant_slug}/` and require a valid JWT token. Read calls accept any active membership; write calls (create, command, override, rules, schedules, emergency stop) require at least the **grower** role; deleting an actuator requires **admin**. The UI currently covers only part of the API (creating/listing/deleting an actuator, direct on/off command, emergency stop with the `fire_alarm` scenario) — see [Environment Control & Actuators — User Guide: For Technical Users / Self-Hosters](../user-guide/actuator-control.md#for-technical-users-self-hosters) for the full, still UI-less remainder of the API (schedules, rules, phase-linked profiles, envelope configuration).

| Resource group | Endpoints (selection) |
|-----------------|------------------------|
| Actuators | `GET`/`POST /locations/{location_key}/actuators`, `GET /actuators`, `GET`/`PUT`/`DELETE /actuators/{key}` |
| Command & override | `POST /actuators/{key}/command`, `POST`/`DELETE /actuators/{key}/override`, `GET /actuators/{key}/state` |
| Schedules | `GET`/`POST /actuators/{key}/schedules`, `PUT`/`DELETE /actuators/{key}/schedules/{schedule_key}`, `POST .../toggle` |
| Rules | `GET`/`POST /actuators/{key}/rules`, `GET /rules`, `PUT`/`DELETE /actuators/{key}/rules/{rule_key}`, `POST .../toggle`, `POST /rules/{rule_key}/test` |
| Control log | `GET /actuators/{key}/events`, `GET /actuators/{key}/events/stats`, `GET /locations/{location_key}/control-events`, `GET /locations/{location_key}/control-status`, `GET /locations/{location_key}/energy` |
| Phase-linked profiles | `GET`/`POST /phase-control-profiles`, `GET`/`PUT`/`DELETE /phase-control-profiles/{key}`, `POST .../apply` |
| Emergency stop | `POST /emergency-stop` |

### Safety guarantees

**Value envelope:** every command, rule hit, schedule hit and override passes through the same backend chokepoint. A numeric value for an actuator without a configured `min_value`/`max_value` is refused (`422` for a direct command or override; the affected actuator is skipped and logged for the automatic control loop). If an envelope is configured, every value is automatically clamped into `[min_value, max_value]` — non-finite values (`NaN`/`Infinity`) are likewise never passed through unchanged.

**Time-limited override:** `POST /actuators/{key}/override` requires `expires_at` as a mandatory field. An `expires_at` that already lies in the past is rejected with `422` — there is no implicit default duration.

```json
POST /api/v1/t/my-garden/actuators/act_42/override
{
  "expires_at": "2026-07-11T10:00:00Z",
  "override_state": "on",
  "reason": "Manual ventilation before the weekend"
}
```

**Response (422) when `expires_at` has already passed:**

```json
{
  "error_id": "err_...",
  "error_code": "VALIDATION_ERROR",
  "message": "Manual override expires_at must be in the future.",
  "details": [],
  "timestamp": "2026-07-11T09:00:00.000000+00:00",
  "path": "/api/v1/t/my-garden/actuators/act_42/override",
  "method": "POST"
}
```

**Emergency stop — per-actuator fault tolerance:** `POST /emergency-stop` handles every affected actuator in isolation. If switching a single actuator fails (e.g. Home Assistant unreachable), the call is not aborted — the response lists successfully switched (`stopped`, `forced_on`) and failed (`failed`) actuator keys separately:

```json
{
  "scenario": "fire_alarm",
  "stopped": ["act_1", "act_3"],
  "forced_on": [],
  "failed": ["act_2"]
}
```

### See Also

- [Environment Control & Actuators — User Guide](../user-guide/actuator-control.md)
- [Sensors — User Guide](../user-guide/sensors.md)
- [Environment Variables — Environment Control & Actuators](environment-variables.md#environment-control-actuators-req-018)
- [Error Handling](../api/error-handling.md)

---

## Phase Definitions: Plants & Species per Phase <!-- FIX-01 -->

Two thin, read-only endpoints feed the two additional lists on the phase-definition detail page: which of your own plants are currently in a phase, and which species traverse that phase in the global catalog.

### List Species for a Phase Definition (Global)

Returns all species from the global catalog whose phase sequence includes the given phase definition. No tenant prefix — reference data like botanical families or the hardiness-zone catalog.

```
GET /api/v1/phase-definitions/{key}/species
```

Requires a valid JWT token; no separate role restriction.

**Path parameter:** `key` — the phase definition's key.

**Response (200):** a list of `PhaseDefinitionSpeciesResponse`. Empty if no species traverses this phase (no `404`).

```json
[
  {
    "key": "species/123",
    "scientific_name": "Solanum lycopersicum",
    "common_names": ["Tomate", "Tomato"],
    "typical_duration_days": 30,
    "illustration": "phases/flowering.svg"
  }
]
```

| Field | Type | Meaning |
|------|-----|----------|
| `key` | string | The species' key |
| `scientific_name` | string | Scientific (binomial) name |
| `common_names` | list[string] | Common names |
| `typical_duration_days` | integer | This phase's typical duration for the species — the species-specific override (`override_duration_days`) from the phase-sequence entry when set, otherwise the phase definition's default |
| `illustration` | string | The phase definition's own illustration path (no per-species illustration yet) |

If a species is linked to the same phase definition through more than one phase sequence, it appears only once (de-duplicated by species key); a species-specific override, where set, takes precedence over the definition's default.

### List the Tenant's Active Plant Instances in a Phase Definition

Returns the calling tenant's **active** plant instances whose current phase resolves to the given phase definition. Tenant-scoped (SEC-001) — an empty tenant context is rejected server-side rather than returning another tenant's data.

```
GET /api/v1/t/{tenant_slug}/plant-instances/by-phase-definition/{phase_definition_key}
```

Requires a valid JWT token and an active tenant membership; any role may read.

**Response (200):** `PlantInstancesInPhaseResponse`. `items` is empty if none of the tenant's active plants are in this phase (no `404`).

```json
{
  "total": 2,
  "items": [
    {
      "key": "plant_instances/101",
      "instance_id": "T3-01",
      "plant_name": "Balcony Tomato",
      "species_key": "species/123",
      "species_scientific_name": "Solanum lycopersicum",
      "species_common_names": ["Tomato"],
      "location_key": "locations/5",
      "location_name": "South Balcony",
      "slot_key": "slots/12",
      "slot_label": "Row 2, Pot 3",
      "current_phase_key": "phase_sequence_entries/456",
      "current_phase_started_at": "2026-06-20T08:00:00Z"
    }
  ]
}
```

| Field | Type | Meaning |
|------|-----|----------|
| `total` | integer | Total number of plant instances returned |
| `items[].current_phase_key` | string \| null | Raw value of `PlantInstance.current_phase_key` — usually a `PhaseSequenceEntry` key; for older records it may still be a legacy `GrowthPhase` key |
| `items[].current_phase_started_at` | datetime \| null | Timestamp of the last phase transition — the basis for the "days in phase" count computed client-side on the detail page |

"Active" means `removed_on == null` — removed plants (see [Growth Phases — User Guide: Removing a Plant](../user-guide/growth-phases.md#pflanze-entfernen)) do not appear here. A plant is matched to the phase definition via its current phase-sequence assignment (`PhaseSequenceEntry.phase_definition_key`); for legacy data without a phase sequence, a fallback via the shared canonical phase name of a legacy `GrowthPhase` additionally applies.

!!! note "No `days_in_phase` field in the response"
    Days in phase are deliberately **not** returned by the backend; the UI derives them from `current_phase_started_at` instead, so the value stays current without a re-fetch.

**Route order:** `/by-phase-definition/{phase_definition_key}` is declared **before** `/{key}` in the router so the literal path is not accidentally captured as a plant key (the same pattern used for `/survival-stats` above).

### See Also

- [Growth Phases — User Guide: Phase Definition Detail View](../user-guide/growth-phases.md#phasendefinition-detailansicht)
- [Master Data: Plant Species — User Guide](../user-guide/plant-management.md)
- [Error Handling](../api/error-handling.md)

---

## Plans and quotas of a tenant <!-- REQ-056 §7 / Issue #2142 --> {#plaene-und-kontingente}

Every tenant points at exactly one plan with `plan_key`. A plan sets a limit per quota or leaves it empty (`null` = the server setting). The seeded plan `standard` leaves everything empty and is the plan of every tenant nothing else is assigned to. The responses of `GET /api/v1/tenants/{slug}` and `GET /api/v1/admin/platform/tenants` additionally carry `plan_key`.

| Quota (`dimension`) | Server setting when `null` | `0` means | Refusal |
|---|---|---|---|
| `members` | `TENANT_MAX_MEMBERS_CEILING` (never above it) | — (at least `1`) | `422 MEMBER_LIMIT_REACHED` |
| `service_accounts` | `TENANT_MAX_SERVICE_ACCOUNTS` | — (at least `1`) | `422 SERVICE_ACCOUNT_LIMIT_REACHED` |
| `storage_mb` | `STORAGE_TENANT_QUOTA_MB` | unlimited | `409 STORAGE_QUOTA_EXCEEDED` |
| `photos_per_instance` | `STORAGE_MAX_PHOTOS_PER_INSTANCE` | unlimited | `409 PHOTO_QUOTA_EXCEEDED` |
| `ai_calls_per_user_day` | `AI_BUDGET_USER_CALLS_PER_DAY` | budget off | `429 AI_BUDGET_EXCEEDED` |
| `ai_calls_per_tenant_day` | `AI_BUDGET_TENANT_CALLS_PER_DAY` | budget off | `429 AI_BUDGET_EXCEEDED` |
| `ai_tokens_per_tenant_day` | `AI_BUDGET_TENANT_TOKENS_PER_DAY` | budget off | `429 AI_BUDGET_EXCEEDED` |

!!! warning "`0` means unlimited, not \"nothing allowed\""
    For `storage_mb` and `photos_per_instance`, `0` lifts the limit entirely; for the three AI budgets, `0` switches the budget off — again no limit. A plan therefore cannot set these dimensions to "none at all". The plan response lists such dimensions in the field `unlimited`, and the security audit marks a change to `0` as `to_unlimited`.

Every quota has an upper bound (e.g. `storage_mb` at most 10,000,000, `ai_tokens_per_tenant_day` at most 10¹²); above it the API answers `422`. The effective member limit is `min(max_members, plan.members ?? ceiling, TENANT_MAX_MEMBERS_CEILING)`. The platform tenant always follows the server settings and takes no plan (`422`). A tenant whose plan document is missing or corrupt falls back to the default plan, then to the server setting, never to "unlimited"; a corrupt plan is also left out of the plan listing.

### Read a tenant's plan and usage

`GET /api/v1/tenants/{slug}/entitlements` — every member. `ai_calls_per_user_day.used` is your own usage; `service_accounts` and `ai_tokens_per_tenant_day` are listed for a lead only. `limit: null` = unlimited, `used: null` = counted per plant or not readable right now.

```json
{
  "plan": {"key": "standard", "name": "Standard"},
  "limits": [
    {"dimension": "members", "limit": 50, "used": 12},
    {"dimension": "storage_mb", "limit": 2048, "used": 731},
    {"dimension": "photos_per_instance", "limit": 50, "used": null},
    {"dimension": "ai_calls_per_user_day", "limit": 50, "used": 3},
    {"dimension": "ai_calls_per_tenant_day", "limit": 500, "used": 41}
  ]
}
```

### Manage plans (platform admin)

| Method | Path | Effect |
|---|---|---|
| `GET` | `/api/v1/admin/platform/plans` | every plan with `tenant_count` |
| `POST` | `/api/v1/admin/platform/plans` | create a plan (`201`; `409` for a taken `key`; `422` out of range or `members` above the ceiling) |
| `PATCH` | `/api/v1/admin/platform/plans/{plan_key}` | change name, description, single quotas (`name: null` is `422`); `is_default: true` makes it the default of new tenants |
| `DELETE` | `/api/v1/admin/platform/plans/{plan_key}` | delete (`204`); `409 RESOURCE_IN_USE` while a tenant uses it or it is the default |
| `PATCH` | `/api/v1/admin/platform/tenants/{key}` with `plan_key` | assign a plan (`422` for an unknown plan, a tenant being erased or the platform tenant; `409 WRITE_CONFLICT` when the plan is deleted at the same moment) |
| `GET` | `/api/v1/admin/platform/tenants/{key}` | the tenant with `entitlements` over every quota |

`key` matches `^[a-z][a-z0-9_-]{1,39}$` and is immutable. None of these actions asks for a password confirmation; each writes a security-audit entry (`plan_created`, `plan_changed` with `changed_fields` and — for quotas — `limit_changes` with old and new value, `plan_deleted`, `tenant_plan_changed` with `old_plan_key` and `plan_key`). Light mode has none of these routes.

### Exporting and importing a tenant <!-- REQ-056 §8 / Issue #2138 --> {#mandanten-export-import}

Steps, archive content and refusals are described in the runbook [Exporting and importing a tenant](../deployment/tenant-export-import.md). All routes exist in full mode only; none accepts an API key or a service account (`403`).

| Method | Path | Who | Effect |
|---|---|---|---|
| `POST` | `/api/v1/tenants/{slug}/exports` | lead ∧ management + confirmation (`tenant_export`) | request an export (`202`); in `active` and `pending_deletion`. `409 EXPORT_ALREADY_RUNNING` while one runs; `429` from the `TENANT_EXPORTS_PER_DAY`+1st in 24 h; an unknown slug and a missing permission are the same `403` |
| `GET` | `/api/v1/tenants/{slug}/exports` | lead ∧ management | own exports, newest first (paginated) |
| `GET` | `/api/v1/tenants/{slug}/exports/{export_key}/download` | whoever requested it | the archive as ZIP; `404` after expiry (`RETENTION_EXPORT_FILE_RETENTION_HOURS`) |
| `POST` | `/api/v1/admin/platform/tenants/{key}/exports` | platform admin + confirmation | export in every state but `deleted` |
| `GET` | `/api/v1/admin/platform/tenants/{key}/exports` (`…/{export_key}/download`) | platform admin | own exports or the archive |
| `POST` | `/api/v1/admin/platform/tenant-imports` | platform admin + confirmation (`tenant_import`, target `archive:<the first 32 hex digits of the file's SHA-256>`, checked before the file is read) | the archive as `multipart/form-data` (`archive`, optional `member_mapping` as JSON `{"<old user_key>": {"email": "…", "role": "lead\|grower\|viewer", "admin_scopes": […]}}`, `plan_key`, confirmation fields); `202`, `verified` says whether this installation signed the archive. Refused before any write with `422` and the codes `IMPORT_FORMAT_UNSUPPORTED`, `IMPORT_CHECKSUM_MISMATCH`, `IMPORT_UNDECLARED_REFERENCE`, `IMPORT_MISSING_CATALOG_ENTRIES` (listed in `details`), `IMPORT_MEMBER_NOT_FOUND`; `413` above `TENANT_IMPORT_MAX_UPLOAD_MB` |
| `GET` | `/api/v1/admin/platform/tenant-imports/{import_key}` | platform admin | state and report (`report`: count per collection), `target_tenant_key`, `verified` |

The body carries the confirmation as for a deletion (`current_password`, `step_up_code` or `step_up_token`). An export request (`status`: `pending` → `running` → `completed` / `failed` with `failure_reason` `too_large`, `internal_error`, `storage_unavailable`, `tenant_not_exportable` → `expired`) names its size (`size_bytes`), rows per archive part (`counts`) and `expires_at`. Security log: `tenant_export_requested`, `tenant_export_downloaded` (every download), `tenant_import_requested`, `tenant_imported`. An imported tenant is in the state `importing` until its last row is written and reachable for nobody.

### Organizations per account

`POST /api/v1/tenants` refuses once the account owns `TENANT_MAX_ORGANIZATIONS_PER_USER` organizations (counted in every state but `deleted`): `422 ORGANIZATION_LIMIT_REACHED` (until now `422 VALIDATION_ERROR`). This is a limit of the account, not a plan quota.
