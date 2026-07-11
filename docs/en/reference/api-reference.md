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

## Season & Overwintering Automation

These endpoints read the automatically computed season state of a site and the automatically materialised overwintering profile of a plant. Both are derived without user interaction as soon as a plant is assigned to an outdoor, greenhouse, or balcony site (`OVERWINTERING_SITE_TYPES`) — on plant creation, on a site change, and additionally as a safety net from the daily season evaluation run — see [Season Automation](../user-guide/season-automation.md) and [Overwintering](../user-guide/overwintering.md) in the user guide. <!-- REQ-047 -->

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
| `409` | Site is not of type `outdoor`, `greenhouse`, or `balcony` — only these frost-exposed site types run a season state |

### Season Overview Across All Sites

```
GET /api/v1/t/{tenant_slug}/season/overview
```

Returns `{"states": [ ... ]}` with one `SeasonStateResponse` object (see above) per outdoor, greenhouse, or balcony site of the tenant. Feeds the "Winter Protection" dashboard widget (see [Personalizing the Dashboard](../user-guide/dashboard-personalization.md)).

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
| `404` | `species_key` does not reference a known species |
| `409` | Self-hosted recognition is not enabled (`INFERENCE_SERVICE_ENABLED=false`) |
| `413` | Image exceeds `IDENTIFICATION_MAX_IMAGE_SIZE_MB` |
| `415` | `Content-Type` is neither `image/jpeg` nor `image/png` |
| `422` | Image cannot be decoded (corrupt or not a valid image format) |
| `429` | Daily contribution quota (`REFERENCE_CONTRIBUTION_RATE_LIMIT_PER_USER_DAY`) exhausted |

!!! note "Security model (quarantine, provenance, dedup)"
    Every contribution is stored with `source="user_contributed"`, `is_active=false`, and the contributing user and tenant as provenance — it therefore does not affect other tenants' recognition until a platform admin has reviewed it. Re-submitting the same photo (SHA-256 hash of the normalized image) updates the existing row instead of creating another one. The original image itself is never persisted — only the embedding.

### See Also

- [Identify a Plant by Photo — User Guide: Assigning the Photo to the New Plant](../user-guide/plant-identification.md#assigning-the-photo-to-the-new-plant)
- [Curating Reference Images — User Guide](../user-guide/reference-image-curation.md)
- [Environment Variables — Photo Identification](environment-variables.md#photo-identification-req-029)
- [Error Handling](../api/error-handling.md)

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
