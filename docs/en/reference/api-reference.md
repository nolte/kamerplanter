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

### See Also

- [Print Views & Export — User Guide](../user-guide/print-export.md)
- [Fertilization Logic](../user-guide/fertilization.md)
- [Care Reminders](../user-guide/care-reminders.md)
