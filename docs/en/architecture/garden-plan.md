# Garden Plan: Geometry and Interfaces

This page describes how the garden plan is built technically: the coordinate system and shapes, the batch contract used for saving, the backup format and the way to plant state and irrigation zones. It is written for developers and operators. How you use the plan is described in the [Garden Plan user guide](../user-guide/garden-plan.md).

!!! info "Source of truth"
    The limits and error codes below come from the code (`src/backend/app/domain/models/geometry.py`, `garden_plan.py`, `garden_plan_import.py`, `garden_plan_export.py`). The routes with examples are in the [API Reference](../reference/api-reference.md#garden-plan-pdf-svg-json-backup). <!-- REQ-053 §20-§22 -->

---

## Geometry model

### Coordinate system

Every stored geometry is given in **metres**, rounded to 0.001 m (a millimetre). Pixels arise only when converting from the model to the view and are never stored. The x axis points right, the y axis points up, and angles run **counter-clockwise**. The north direction of the plan (`north_angle_deg`) is the exception: it is a compass azimuth, clockwise, where 0 means "north is +y".

There are two frames of reference:

| Frame | Applies to | Coordinate range |
|-------|-----------|------------------|
| **Plan frame** | Garden boundary (`plan.boundary`), geometry of locations (`Location`) and garden objects | 0 to 1000 m per axis |
| **Bed frame** | Geometry of a planting place (`Slot`) | −1000 to 1000 m per axis |

The origin of the bed frame is the anchor point of the bed: the centre for a round bed, the first vertex for a polygon. That is why the coordinates of a planting place can legitimately be negative. The range −1000 to 1000 m in the bed frame is a placeholder until the specification decides; it is in the code as stated.

### Shapes (`kind`)

| `kind` | Fields | Notes |
|--------|--------|-------|
| `rect` | `origin`, `width_m`, `length_m`, `rotation_deg` | `origin` is the lower left corner before rotation; the rotation pivots about `origin` |
| `circle` | `origin`, `radius_m` | `origin` is the centre; no rotation |
| `polygon` | `points` (3 to 200), `rotation_deg` | The first point is the anchor; the editor stores polygons with rotation 0 |
| `polyline` | `points` (2 to 200), `width_m` | Open line (fence, wall, path axis); no rotation |
| `point` | `origin` | A position (planting place, point object); no rotation |

`rect`, `circle` and `polygon` enclose an area and carry the server-computed `area_m2`. A `rotation_deg` on a circle, line or point is an error (unknown field).

### Value ranges (rule V-01)

- Dimensions (`width_m`, `length_m`, `radius_m`, `width_m` of the line): 0.01 to 1000 m.
- Coordinates: see the table above, depending on the frame.
- `rotation_deg`: from 0 (inclusive) to below 360. An input value that rounds to 360.000 becomes 0.
- Vertices: polygon 3 to 200, line 2 to 200.
- The server applies the rule with the error code `geometry.invalid`. For a vertex outside the range the entry also carries `point_index` (counted from 0).
- Rule V-02 (a polygon must not cross itself) sits one layer up in the `geometry_calculator`: a self-intersecting polygon is parsed and refused by the service with its own error code.

### Rounding

Length, coordinate and angle are rounded to three decimals, **halves away from zero**, on the exact binary value (`Decimal(value).quantize(0.001, ROUND_HALF_UP)`). In JavaScript this corresponds to `Number(value.toFixed(3))`. Python's built-in `round` would round ties to even and differ on exactly representable halves such as 2.0625. `-0.0` becomes `0.0`.

---

## Batch contract

`POST /api/v1/t/{slug}/sites/{key}/plan/batch` applies a list of plan operations **atomically**: either all are accepted or none. The editor collects its changes locally and sends them in one batch when saving.

### Request

```json
{
  "expected_revision": 42,
  "operations": [
    { "op": "create_location", "temp_key": "tmp1",
      "data": { "name": "Bed 6", "location_type_key": "bed",
                "geometry": { "kind": "rect", "origin": [4, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0 } } },
    { "op": "delete", "entity": "garden_object", "key": "go_old" }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `expected_revision` | The `plan_revision` at which the client loaded its state (optimistic lock). Integer ≥ 0 |
| `operations` | 1 to 500 operations from the closed list below |

The operations are a closed list:

| `op` | Effect |
|------|--------|
| `create_location` | Creates a location (a bed, an area) with geometry; `temp_key` names it within the batch |
| `create_garden_object` | Creates a garden object (`object_type`, geometry, `props`) |
| `update_geometry` | Sets the geometry of `entity` (`location` or `garden_object`) with `key` |
| `update_fields` | Changes fields; for a location also `site_conditions.sun_profile` (only the keys sent) |
| `delete` | Deletes `entity` with `key` including descendants; **lead role only** |
| `set_boundary` | Sets the garden boundary, `north_angle_deg`, `default_grid_m` (greater than 0 up to 10 m) and `adjacency_factor` |
| `set_locked` | Locks or unlocks an object |
| `set_z_order` | Sets the drawing order (−10000 to 10000) |

### Temporary keys

An object you create in the batch gets a `temp_key` (1 to 40 characters from letters, digits, `_` and `-`). Later operations of the same batch and `parent_location_key` may use it as a key. The response contains `key_map` (`temp_key` to assigned key). A `temp_key` is valid only within the request.

### Response

`200` with `plan_revision` (the new revision), `key_map`, `updated` and `deleted` (lists of keys) and `derived` per key (`area_m2`, `bbox` as `[minX, minY, maxX, maxY]`). Every successful batch raises the revision by one. Planting places live in the bed frame and change **outside** the plan revision, through routes of their own.

### Order of checks and error codes

The server checks in this order and stops at the first error. Nothing is written.

0. Role at the route: a viewer fails at the route (permission to change locations) with a general `403` – before the `404` and before the size checks.
1. The site belongs to the tenant (otherwise `404`).
2. Size of the request: more than `MAX_OPERATIONS` = 500 operations gives `422 batch.too_many_operations`. A body above 1 MiB is rejected by the server before routing with `413 REQUEST_BODY_TOO_LARGE`. The `MAX_BATCH_BODY_BYTES` = 2 MiB check (`422 batch.too_complex`) measures the re-serialised operations of a body that is already under 1 MiB; over HTTP it practically never triggers.
3. References: an unknown or foreign key gives `422 reference.not_found` (absent and foreign look the same).
4. Role per operation: `delete` requires the lead role, everything else at least grower. A violation (a grower whose batch contains a `delete`) discards the whole batch with `403 batch.operation_forbidden` and `op_index`.
5. Shape: Pydantic checks each operation (`422 VALIDATION_ERROR`). More than `MAX_BATCH_POINTS` = 20,000 polygon and polyline points together gives `422 batch.too_complex`.
6. Domain rules: `422 VALIDATION_ERROR`, with `code`, `op_index` and where applicable `point_index` in `details[]`. Codes include `geometry.invalid`, `geometry.outside_parent`, `bed.overlap`, `boundary.shrinks_below_objects`, `plan.quota_exceeded`. At most 50 findings per response. If checking and transaction take longer than `BATCH_TIME_BUDGET_SECONDS` = 10 s, the batch ends with `422 batch.too_complex`.
7. Revision: `409 plan.revision_conflict` with `current_revision`, the display name of the last editor (`changed_by`) and `changed_at`; never with an account key.

In addition the server refuses to delete a bed with `409 location.has_active_plants` while plants stand on it.

Per site at most `MAX_PLAN_OBJECTS_PER_SITE` = 500 locations and garden objects together, `MAX_PLAN_ZONES` = 500 irrigation zones and `MAX_SLOTS_PER_SITE` = 8,000 planting places are allowed. Exceeding one gives `422 plan.quota_exceeded` or `irrigation_zone.quota_exceeded`. Saving is limited per account by `RATE_LIMIT_PLAN_BATCH` (default 10 per minute), see [Environment Variables](../reference/environment-variables.md).

`POST …/plan/place-template` places a single bed from a template through the same path (one transaction, one revision). `PUT …/plan/boundary` creates the plan on the first call and raises the revision afterwards.

---

## Backup: export and import

### Export

`GET …/plan/export` returns a JSON file with `schema_version: "1"`: plan settings, locations with geometry and soil profile, garden objects, planting places and irrigation zones. It deliberately holds no plants, tasks, care events, photos or attachments, no account references and no `tenant_key`; a new field appears only if it is added to the export model on purpose. The underlay is not part of it.

With `scope` you choose `site` (everything), `selection` (exactly the beds or objects named in `keys`, objects as `object:<key>`) or `subtree` (the beds with everything below them); `keys` has at most 100 entries. A partial file is the same schema, only smaller: without plan settings and with `null` for references that leave the file.

### Import

`POST …/plan/import` (lead role only) checks or writes a backup:

- `mode`: `replace` replaces the plan of the site, `merge` adds. `dry_run` writes nothing and answers with the report. `replace` requires `confirm_site_name`. `force` lifts only the condition that no bed carries an active plant (`409 import.not_empty`); those beds then stay.
- `target`: `same_site`, `other_site` or `other_tenant`. `offset_m` (`[dx, dy]`, at most ±1000 m) applies to `merge` only.
- **Keys** of the file are never kept; all objects get new keys, references are rewritten through a key table. Links to Home Assistant entities and actuators are never imported.
- **Limits:** file at most 5 MiB (`413`, plus an envelope of 64 KiB), at most 10 levels of locations below each other (`import.too_deep`), time budget 30 s, report with at most 50 findings (the counters stay exact). The import budget is one shared counter per tenant (`RATE_LIMIT_PLAN_IMPORT`, default 3 per minute).
- **Quotas:** the same ceilings as when saving (`plan.quota_exceeded`).

### Additive keys and versions

`schema_version` is `"1"`. New fields are added **additively** only; a known entry ignores unknown fields. A file with an unknown key at the top level comes from a newer version and is refused with `422 import.unknown_keys`; a missing or unsupported `schema_version` gives `import.schema_version_missing` or `import.schema_version_unsupported`. The frost exposure of a bed (`frost_exposed`) is part of the file; if it is missing, the import derives it from the frost risk.

### Snapshots

A `replace` import first writes the overwritten plan as `import_snapshot` into the change log. A site keeps at most `MAX_SNAPSHOTS_PER_SITE` = 20 snapshots; a new one removes the oldest in the same transaction. Retention follows the change log (365 days, `RETENTION_GARDEN_PLAN_AUDIT_RETENTION_DAYS`). `GET …/plan/snapshots` lists counters only, never the plan; `POST …/plan/snapshots/{audit_key}/restore` restores a state and first writes the current one as a snapshot itself. Both routes are for the lead role only.

---

## State, zones and further routes

Pointers only; paths and fields are in the [API Reference](../reference/api-reference.md) and in the OpenAPI description of the backend.

| Purpose | Route | Role |
|---------|-------|------|
| Plant state of a bed | `GET /locations/{key}/plant-states` | all members |
| Irrigation zones of a site | `GET`/`POST /sites/{key}/irrigation-zones`, `GET`/`PATCH`/`DELETE /irrigation-zones/{key}` | read all, change grower, delete lead |
| Replace the beds of a zone | `PUT /irrigation-zones/{key}/locations` | grower |
| State of a zone | `GET /irrigation-zones/{key}/status` | all members |
| Watering round | `POST /irrigation-zones/{key}/log-watering` | grower |
| Bed templates | `GET`/`POST /bed-templates`, `PATCH`/`DELETE /bed-templates/{key}` | read all, create grower, delete lead |
| Underlay | `PUT`/`DELETE /sites/{key}/plan/underlay` | grower |
| Change log | `GET /sites/{key}/plan/audit` | all members |
| New season | `POST /sites/{key}/plan/new-season` | lead |
| PDF and SVG | `GET /print/garden-plan/{site_key}`, `GET /sites/{key}/plan/render.svg` | all members |

The technical coupling of a zone (`actuator_key`, flow from a Home Assistant entity) may be written only by an account with the `technical` admin scope.

## Print views (reference)

The garden plan to scale is the "visual floor plan" of the location overview. How a user prints it is described under [Export the plan and restore a backup](../user-guide/garden-plan.md#plan-export-import) and in [Print Views & Export](../user-guide/print-export.md). The print view specification points to the routes above for this floor plan.

## See Also

- [User guide: Garden Plan](../user-guide/garden-plan.md)
- [API Reference](../reference/api-reference.md#garden-plan-pdf-svg-json-backup)
- [Environment Variables](../reference/environment-variables.md)
- [Backend Architecture](backend.md)
