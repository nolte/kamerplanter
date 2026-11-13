"""Self-provisioning for the REQ-053 garden plan editor tests (WP 2.9, TC-053-0xx).

Every editor test arranges its **own** site with its own plan, so no test reads
or mutates a plan another test (or another xdist worker) touches
(`e2e-test-stability` §A). The site name carries a UUID-derived suffix, which is
unique across parallel workers and across repeated runs against the same
persistent database.

WHY THE API, AND WHICH ONE
--------------------------
The arrangement goes through the application's own REST API — the same routes
the editor itself calls — never through a direct database write
(`test-pyramid-foundation` §"Arrangement-Treue", `test-falsifiability` T9) -
with two named exceptions, both going through :func:`_arango_document_write`
and each explaining its divergence in its own docstring:

* :func:`mark_task_suggested` - the suggestion flag of a task has no route and
  no producer yet (REQ-053 E-02);
* :func:`store_frost_forecast` - a weather forecast is written only by the
  weather fetch task, and the E2E stack has no outbound weather source.

The routes used otherwise:

* ``POST /sites`` creates the site;
* ``PUT /sites/{key}/plan/boundary`` creates the plan with its boundary and grid
  (GP-API-002) — the editor of WP 2.1-2.8 has no boundary tool and does not
  mount on a plan without content, so this precondition cannot be drawn;
* ``POST /sites/{key}/plan/batch`` creates beds and garden objects (GP-API-003),
  exactly the operation the editor's save sends;
* ``POST /locations/{key}/slots/batch`` creates planting positions (GP-API-015) —
  the editor cannot create slots yet, and the "tent with 9 slots from M1"
  precondition of TC-053-014 is migration data in production.

Every refusal raises with the response body: a failed arrangement is a loud
failure, never a skip (`e2e-test-stability` §A).

RATE LIMIT
----------
``plan/batch`` (and ``plan/boundary``) are limited per user
(``RATE_LIMIT_PLAN_BATCH``, production default ``10/minute``). Light mode runs
every request as one user, so the arrangement uses exactly one batch per site.
A ``429`` is reported as what it is instead of as a broken editor.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from ._journey_helpers import _api_request

#: Snap grid of every provisioned plan (TC-REQ-053 test data: "Raster 10 cm").
GRID_M = 0.1


def unique_tag() -> str:
    """A collision-free suffix: UUID-derived, unique across workers and runs."""
    return uuid.uuid4().hex[:10]


def rect(x: float, y: float, width: float, length: float, rotation: float = 0.0) -> dict:
    """A rect geometry in the plan frame (``origin`` = lower-left corner, y up, metres).

    Floats on purpose: the backend's geometry model uses ``StrictFloat``.
    """
    return {
        "kind": "rect",
        "origin": [float(x), float(y)],
        "width_m": float(width),
        "length_m": float(length),
        "rotation_deg": float(rotation),
    }


def polyline(points: list[tuple[float, float]], width: float) -> dict:
    """A polyline geometry (a path); a polyline carries no rotation (V-01)."""
    return {
        "kind": "polyline",
        "points": [[float(x), float(y)] for x, y in points],
        "width_m": float(width),
    }


def circle(x: float, y: float, radius: float) -> dict:
    """A circle geometry (a tree crown); ``origin`` is the centre."""
    return {"kind": "circle", "origin": [float(x), float(y)], "radius_m": float(radius)}


@dataclass(frozen=True)
class BedSpec:
    """A bed (or tent) to create; ``slots`` are bed-frame points (origin = bed corner)."""

    name: str
    geometry: dict
    location_type_key: str = "raised_bed"
    slots: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class ObjectSpec:
    """A garden object to create (path, tree, window, lamp, ...).

    ``props`` are the type's own properties where the model requires some (a lamp's ``kind`` and ``height_m``);
    ``off_site`` marks scenery outside the boundary (§9.5, exempt from containment). Both go into the same
    ``create_garden_object`` operation the editor's save sends.
    """

    label: str
    object_type: str
    geometry: dict
    props: dict | None = None
    off_site: bool = False


@dataclass
class ProvisionedGarden:
    """What a test needs to drive the plan it arranged."""

    site_key: str
    site_name: str
    revision: int
    beds: dict[str, str] = field(default_factory=dict)
    objects: dict[str, str] = field(default_factory=dict)
    slots: dict[str, list[str]] = field(default_factory=dict)

    def bed_key(self, name: str) -> str:
        if name not in self.beds:
            raise AssertionError(f"no provisioned bed named {name!r}; have {sorted(self.beds)}")
        return self.beds[name]


def _api(base_url: str, seed: dict) -> tuple[str, str | None]:
    from .conftest import _fresh_access_token

    token = _fresh_access_token(seed, base_url)
    slug = seed.get("tenant_slug", "mein-garten")
    return f"{base_url.rstrip('/')}/api/v1/t/{slug}", token


def _require(status: int, body: object, expected: tuple[int, ...], what: str) -> None:
    if status in expected:
        return
    hint = ""
    if status == 429:
        hint = (
            " (429: the per-user plan rate limit RATE_LIMIT_PLAN_BATCH was exhausted —"
            " a harness budget problem, not an editor defect)"
        )
    raise AssertionError(
        f"Self-provisioning failed: {what} answered status={status}{hint}, body={body!r}"
    )


def provision_garden(
    base_url: str,
    seed: dict,
    *,
    purpose: str,
    site_type: str = "outdoor",
    boundary: dict | None = None,
    beds: tuple[BedSpec, ...] = (),
    objects: tuple[ObjectSpec, ...] = (),
) -> ProvisionedGarden:
    """Create a site with a plan (boundary, grid 10 cm, north 0°), beds, objects and slots."""
    api, token = _api(base_url, seed)
    tag = unique_tag()
    name = f"E2E-GP-{purpose}-{tag}"

    status, site = _api_request(
        f"{api}/sites",
        "POST",
        token,
        {"name": name, "type": site_type, "timezone": "Europe/Berlin"},
    )
    _require(status, site, (201,), f"POST /sites ({name})")
    site_key = site["key"]

    status, body = _api_request(
        f"{api}/sites/{site_key}/plan/boundary",
        "PUT",
        token,
        {
            "boundary": boundary or rect(0, 0, 10, 10),
            "north_angle_deg": 0.0,
            "default_grid_m": GRID_M,
        },
    )
    _require(status, body, (200,), f"PUT /sites/{site_key}/plan/boundary")
    revision = int(body["plan_revision"])

    garden = ProvisionedGarden(site_key=site_key, site_name=name, revision=revision)
    operations: list[dict] = []
    for index, bed in enumerate(beds):
        operations.append(
            {
                "op": "create_location",
                "temp_key": f"bed{index}",
                "data": {
                    "name": bed.name,
                    "location_type_key": bed.location_type_key,
                    "geometry": bed.geometry,
                },
            }
        )
    for index, obj in enumerate(objects):
        data: dict = {
            "object_type": obj.object_type,
            "label": obj.label,
            "geometry": obj.geometry,
        }
        if obj.props is not None:
            data["props"] = obj.props
        if obj.off_site:
            data["off_site"] = True
        operations.append({"op": "create_garden_object", "temp_key": f"obj{index}", "data": data})
    if operations:
        status, result = _api_request(
            f"{api}/sites/{site_key}/plan/batch",
            "POST",
            token,
            {"expected_revision": revision, "operations": operations},
        )
        _require(status, result, (200,), f"POST /sites/{site_key}/plan/batch")
        key_map = result.get("key_map") or {}
        garden.revision = int(result["plan_revision"])
        for index, bed in enumerate(beds):
            garden.beds[bed.name] = _mapped(key_map, f"bed{index}", bed.name)
        for index, obj in enumerate(objects):
            garden.objects[obj.label] = _mapped(key_map, f"obj{index}", obj.label)

    for bed_index, bed in enumerate(beds):
        if not bed.slots:
            continue
        bed_key = garden.beds[bed.name]
        slots = [
            {
                # The model's own format rule (upper case, `LOCATION_POSITION`), and
                # unique per run: a slot id must never collide with one of another
                # test's sites, whatever scope V-20 checks it in.
                "slot_id": f"S{tag.upper()}_{bed_index}_{n:02d}",
                "geometry": {"kind": "point", "origin": [float(x), float(y)]},
            }
            for n, (x, y) in enumerate(bed.slots, start=1)
        ]
        status, result = _api_request(
            f"{api}/locations/{bed_key}/slots/batch",
            "POST",
            token,
            {"mode": "append", "slots": slots},
        )
        _require(status, result, (200, 201), f"POST /locations/{bed_key}/slots/batch")
        created = list(result.get("created_keys") or [])
        if len(created) != len(slots):
            raise AssertionError(
                f"Self-provisioning failed: asked for {len(slots)} slots in {bed.name!r}, "
                f"the server created {len(created)}: {result!r}"
            )
        garden.slots[bed.name] = created
    return garden


def create_site(base_url: str, seed: dict, *, purpose: str, site_type: str) -> tuple[str, str]:
    """A site **without** a plan (no boundary, no bed, no object): ``(key, name)``.

    The state a freshly created site is in - ``POST /sites`` is all the site form sends - so the plan route shows its
    empty state (GP-UX-049; indoor GP-FR-182).
    """
    api, token = _api(base_url, seed)
    name = f"E2E-GP-{purpose}-{unique_tag()}"
    status, site = _api_request(
        f"{api}/sites",
        "POST",
        token,
        {"name": name, "type": site_type, "timezone": "Europe/Berlin"},
    )
    _require(status, site, (201,), f"POST /sites ({name})")
    return site["key"], name


def stored_object(plan: dict, key: str) -> dict:
    """The stored garden object *key* of a plan read (GP-API-001); loud when the plan has none of that key."""
    for obj in plan.get("garden_objects") or []:
        if obj.get("key") == key:
            return obj
    keys = [obj.get("key") for obj in plan.get("garden_objects") or []]
    raise AssertionError(f"garden object {key!r} is not in the stored plan; objects={keys}")


def _mapped(key_map: dict, temp_key: str, name: str) -> str:
    if temp_key not in key_map:
        raise AssertionError(
            f"Self-provisioning failed: the batch answer has no key for {name!r} "
            f"(temp key {temp_key!r}); key_map={key_map!r}"
        )
    return key_map[temp_key]


def read_plan(base_url: str, seed: dict, site_key: str) -> dict:
    """The stored plan (GP-API-001) — the durable, server-side read-back of a save."""
    api, token = _api(base_url, seed)
    status, body = _api_request(f"{api}/sites/{site_key}/plan", "GET", token)
    _require(status, body, (200,), f"GET /sites/{site_key}/plan")
    return body


def bed_rect(width: float, length: float) -> dict:
    """A bed of *width* x *length* metres in the middle of the 10 x 10 m garden."""
    return rect(5.0 - width / 2, 5.0 - length / 2, width, length)


# ── Planting (wave 3: WP 3.2 / 3.6 / 3.7) ────────────────────────────────────
#
# The planting tests arrange runs, slots, plants, tasks and a previous year
# through the same routes the planting dialog, the run page and the history tab
# call (`test-pyramid-foundation` §"Arrangement-Treue"):
#
# * ``GET /species`` (global catalogue) resolves a seeded species by its
#   scientific name — the tests never create a species, the catalogue is seed;
# * ``POST /locations/{key}/slots/batch`` + ``POST /planting-runs`` +
#   ``POST /planting-runs/{key}/plan-slots`` + ``POST …/create-plants`` put a
#   plant on an exact bed-frame position — the dialog's own "freely placed"
#   path (GP-API-015/021/023);
# * ``POST /locations/{key}/history/backfill`` records "what stood here last
#   year" (GP-API-042), the precondition of the crop-rotation hint;
# * ``POST /tasks`` hangs an overdue task on a plant (REQ-006).

#: Species resolved per (base URL, scientific name): the catalogue is seed data
#: and does not change during a run.
_SPECIES_CACHE: dict[tuple[str, str], dict] = {}


def _global_api(base_url: str, seed: dict) -> tuple[str, str | None]:
    from .conftest import _fresh_access_token

    return f"{base_url.rstrip('/')}/api/v1", _fresh_access_token(seed, base_url)


def _is_seed(item: dict) -> bool:
    """A global catalogue entry: ``tenant_key == ""`` where the answer carries it, else ``origin`` ``system``."""
    if "tenant_key" in item:
        return item["tenant_key"] in ("", None)
    return item.get("origin", "system") in ("system", "enrichment")


def species(base_url: str, seed: dict, scientific_name: str) -> dict:
    """The seeded species *scientific_name* (exact match, seed entry preferred); loud when it is missing."""
    cached = _SPECIES_CACHE.get((base_url, scientific_name))
    if cached is not None:
        return cached
    api, token = _global_api(base_url, seed)
    status, body = _api_request(f"{api}/species?limit=1000", "GET", token)
    _require(status, body, (200,), "GET /species")
    # The list is the seed catalogue *plus* the caller's own species (F-5): a tenant species of the same
    # scientific name must not shadow the seed entry, so a seed entry always wins over a tenant one.
    for item in body.get("items") or []:
        key = (base_url, item.get("scientific_name", ""))
        if key not in _SPECIES_CACHE or (_is_seed(item) and not _is_seed(_SPECIES_CACHE[key])):
            _SPECIES_CACHE[key] = item
    found = _SPECIES_CACHE.get((base_url, scientific_name))
    if found is None:
        raise AssertionError(
            f"Self-provisioning failed: the species catalogue has no {scientific_name!r} "
            f"(seed data `species.yaml`); {len(body.get('items') or [])} species listed"
        )
    return found


def tenant_get(base_url: str, seed: dict, path: str, *, timeout: float = 15) -> object:
    """``GET`` a tenant-scoped *path* (``/locations/...``); loud on anything but 200."""
    api, token = _api(base_url, seed)
    status, body = _api_request(f"{api}{path}", "GET", token, timeout=timeout)
    _require(status, body, (200,), f"GET {path}")
    return body


def _tenant_post(
    base_url: str, seed: dict, path: str, data: dict, expected=(200, 201), *, timeout: float = 15
) -> dict:
    api, token = _api(base_url, seed)
    status, body = _api_request(f"{api}{path}", "POST", token, data, timeout=timeout)
    _require(status, body, expected, f"POST {path}")
    return body


def utc_today() -> date:
    """Today as the backend counts it (UTC calendar day), not the test runner's local day."""
    return datetime.now(UTC).date()


def run_payload(
    *,
    bed_key: str,
    species_key: str,
    id_prefix: str,
    quantity: int,
    entry: dict,
    name: str,
) -> dict:
    """A planned monoculture run on *bed_key*, as the planting dialog sends it (`runPayload`)."""
    today = utc_today().isoformat()
    return {
        "name": name,
        "run_type": "monoculture",
        "location_key": bed_key,
        "planned_start_date": today,
        "planned_from": today,
        "plan_role": "main_crop",
        "source": "manual",
        "entries": [
            {"species_key": species_key, "quantity": quantity, "id_prefix": id_prefix, **entry}
        ],
    }


def planned_run_with_layout(
    base_url: str,
    seed: dict,
    *,
    bed_key: str,
    species_key: str,
    id_prefix: str,
    quantity: int,
    spacing_cm: float,
    row_spacing_cm: float,
) -> str:
    """A planned run whose rows layout the server lays out and reserves on the bed (GP-FR-064/065)."""
    run = _tenant_post(
        base_url,
        seed,
        "/planting-runs",
        run_payload(
            bed_key=bed_key,
            species_key=species_key,
            id_prefix=id_prefix,
            quantity=quantity,
            name=f"E2E-GP-run-{unique_tag()}",
            entry={
                "spacing_cm": float(spacing_cm),
                "row_spacing_cm": float(row_spacing_cm),
                "layout_strategy": "rows",
                "row_direction": "along_length",
            },
        ),
        expected=(201,),
    )
    return run["key"]


def create_plants(base_url: str, seed: dict, run_key: str) -> list[str]:
    """``create-plants`` onto the run's reserved slots (GP-API-023); the new plant keys."""
    result = _tenant_post(
        base_url, seed, f"/planting-runs/{run_key}/create-plants", {"assign_to_slots": True}
    )
    keys = list(result.get("plant_keys") or [])
    if not keys:
        raise AssertionError(f"Self-provisioning failed: create-plants made no plant: {result!r}")
    return keys


def plantings(base_url: str, seed: dict, bed_key: str, state: str) -> list[dict]:
    """``GET /locations/{key}/plantings?state=`` (GP-API-024): what the planting tab lists."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/plantings?state={state}&limit=200")
    if not isinstance(body, list):
        raise AssertionError(f"plantings of {bed_key!r} is not a list: {body!r}")
    return body


def bed_slots(base_url: str, seed: dict, bed_key: str) -> list[dict]:
    """The live (unarchived) slots of a bed, bed frame."""
    body = tenant_get(base_url, seed, f"/slots?location_key={bed_key}")
    if not isinstance(body, list):
        raise AssertionError(f"slots of {bed_key!r} is not a list: {body!r}")
    return [slot for slot in body if not slot.get("archived_at")]


def runs_of_bed(base_url: str, seed: dict, bed_key: str) -> list[dict]:
    body = tenant_get(base_url, seed, f"/planting-runs?location_key={bed_key}&limit=200")
    if not isinstance(body, list):
        raise AssertionError(f"runs of {bed_key!r} is not a list: {body!r}")
    return body


@dataclass(frozen=True)
class PlantedBed:
    """Plants a test put on exact positions: ``plant_by_slot`` maps slot key -> plant key."""

    run_key: str
    point_slots: tuple[str, ...]
    zone_slots: tuple[str, ...]
    plant_by_slot: dict[str, str]

    def plant_on(self, slot_key: str) -> str:
        if slot_key not in self.plant_by_slot:
            raise AssertionError(f"no plant stands on slot {slot_key!r}: {self.plant_by_slot!r}")
        return self.plant_by_slot[slot_key]


def plant_on_positions(
    base_url: str,
    seed: dict,
    *,
    bed_key: str,
    species_key: str,
    id_prefix: str,
    points: tuple[tuple[float, float], ...] = (),
    zones: tuple[tuple[tuple[float, float], ...], ...] = (),
) -> PlantedBed:
    """Put one plant on each bed-frame *point* and in each *zone* polygon.

    The dialog's "freely placed" path end to end: the slots first, then a
    planned run with a ``free`` entry (the server lays nothing out for it), the
    reservation of exactly those slots, and ``create-plants`` onto them.
    """
    tag = unique_tag().upper()
    items: list[dict] = [
        {
            "slot_id": f"S{tag}_P{n:02d}",
            "slot_role": "position",
            "geometry": {"kind": "point", "origin": [float(x), float(y)]},
            "capacity_plants": 1,
            "sequence": n,
        }
        for n, (x, y) in enumerate(points, start=1)
    ]
    items += [
        {
            "slot_id": f"S{tag}_Z{n:02d}",
            "slot_role": "zone",
            "geometry": {"kind": "polygon", "points": [[float(x), float(y)] for x, y in zone]},
            "capacity_plants": 1,
            "sequence": len(points) + n,
        }
        for n, zone in enumerate(zones, start=1)
    ]
    created = _tenant_post(
        base_url, seed, f"/locations/{bed_key}/slots/batch", {"mode": "append", "slots": items}
    )
    slot_keys = list(created.get("created_keys") or [])
    if len(slot_keys) != len(items):
        raise AssertionError(
            f"Self-provisioning failed: asked for {len(items)} slots, got {created!r}"
        )
    run = _tenant_post(
        base_url,
        seed,
        "/planting-runs",
        run_payload(
            bed_key=bed_key,
            species_key=species_key,
            id_prefix=id_prefix,
            quantity=len(items),
            name=f"E2E-GP-run-{unique_tag()}",
            entry={"spacing_cm": 30.0, "layout_strategy": "free"},
        ),
        expected=(201,),
    )
    run_key = run["key"]
    entries = tenant_get(base_url, seed, f"/planting-runs/{run_key}/entries")
    if not isinstance(entries, list) or len(entries) != 1:
        raise AssertionError(f"Self-provisioning failed: run {run_key!r} has entries {entries!r}")
    _tenant_post(
        base_url,
        seed,
        f"/planting-runs/{run_key}/plan-slots",
        {"entry_key": entries[0]["key"], "slot_keys": slot_keys},
    )
    result = _tenant_post(
        base_url, seed, f"/planting-runs/{run_key}/create-plants", {"assign_to_slots": True}
    )
    if int(result.get("created_count") or 0) != len(items):
        raise AssertionError(
            f"Self-provisioning failed: create-plants made {result!r} for {len(items)} slots"
        )
    active = plantings(base_url, seed, bed_key, "active")
    by_slot = {item["slot_key"]: item["plant_key"] for item in active if item.get("slot_key")}
    missing = [key for key in slot_keys if key not in by_slot]
    if missing:
        raise AssertionError(
            f"Self-provisioning failed: no plant on slots {missing}; active plantings {active!r}"
        )
    return PlantedBed(
        run_key=run_key,
        point_slots=tuple(slot_keys[: len(points)]),
        zone_slots=tuple(slot_keys[len(points) :]),
        plant_by_slot={key: by_slot[key] for key in slot_keys},
    )


def backfill_last_year(base_url: str, seed: dict, bed_key: str, species_key: str) -> int:
    """Record that *species_key* stood in the bed last year (GP-API-042); return that year."""
    year = utc_today().year - 1
    _tenant_post(
        base_url,
        seed,
        f"/locations/{bed_key}/history/backfill",
        {"year": year, "species_key": species_key, "plan_role": "main_crop"},
    )
    return year


def overdue_task(base_url: str, seed: dict, plant_key: str, name: str, days_ago: int) -> str:
    """An open task on *plant_key* that fell due *days_ago* days ago (overdue = due before today, UTC)."""
    due = (datetime.now(UTC) - timedelta(days=days_ago)).replace(hour=9, minute=0, second=0)
    task = _tenant_post(
        base_url,
        seed,
        "/tasks",
        {
            "name": name,
            "category": "observation",
            "priority": "medium",
            "entity_type": "plant_instance",
            "entity_key": plant_key,
            "due_date": due.isoformat(),
        },
        expected=(201,),
    )
    return task["key"]


def stored_origin(plan: dict, location_key: str) -> tuple[float, float]:
    """The stored ``origin`` of a location's geometry; fails loudly when it is not there."""
    for location in plan.get("locations") or []:
        if location.get("key") == location_key:
            geometry = location.get("geometry") or {}
            origin = geometry.get("origin")
            if origin is None:
                raise AssertionError(
                    f"location {location_key!r} has no stored origin: {location!r}"
                )
            return float(origin[0]), float(origin[1])
    keys = [loc.get("key") for loc in plan.get("locations") or []]
    raise AssertionError(f"location {location_key!r} is not in the stored plan; locations={keys}")


# ── Care events: the log lines of wave 4 (WP 4.1-4.5) ───────────────────────


def tenant_request(
    base_url: str, seed: dict, method: str, path: str, data: dict | None = None
) -> tuple[int, object]:
    """Any tenant-scoped call; the status and body, for a test that asserts a refusal."""
    api, token = _api(base_url, seed)
    return _api_request(f"{api}{path}", method, token, data)


def utc_stamp(moment: datetime) -> str:
    """``2026-10-20T08:30:00Z`` - a query-safe instant (a ``+00:00`` offset would lose its ``+`` in a URL)."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_care_event(
    base_url: str,
    seed: dict,
    *,
    bed_key: str,
    category: str,
    summary: str,
    days_ago: float = 0.0,
    **fields: object,
) -> dict:
    """``POST /care-events`` (GP-API-033): a care line without a task, *days_ago* days back (at most 365)."""
    performed_at = datetime.now(UTC) - timedelta(days=days_ago, minutes=1)
    return _tenant_post(
        base_url,
        seed,
        "/care-events",
        {
            "location_key": bed_key,
            "category": category,
            "summary": summary,
            "performed_at": utc_stamp(performed_at),
            **fields,
        },
        expected=(201,),
    )


def care_events(
    base_url: str,
    seed: dict,
    bed_key: str,
    *,
    include_superseded: bool = False,
    category: str | None = None,
) -> list[dict]:
    """``GET /care-events`` of one bed over the last 400 days (the default window is 90), newest first."""
    query = (
        f"location_key={bed_key}&limit=200"
        f"&from={utc_stamp(datetime.now(UTC) - timedelta(days=400))}"
        f"&include_superseded={'true' if include_superseded else 'false'}"
    )
    if category:
        query += f"&category={category}"
    body = tenant_get(base_url, seed, f"/care-events?{query}")
    if not isinstance(body, list):
        raise AssertionError(f"care events of {bed_key!r} is not a list: {body!r}")
    return body


def supersede_care_event(base_url: str, seed: dict, event_key: str, correction: dict) -> dict:
    """``POST /care-events/{key}/supersede`` (GP-API-036): the corrected entry, created beside the original."""
    return _tenant_post(
        base_url, seed, f"/care-events/{event_key}/supersede", correction, expected=(201,)
    )


def redact_care_event(base_url: str, seed: dict, event_key: str, reason: str) -> dict:
    """``POST /care-events/{key}/redact`` (GP-API-041): the free texts of the entry and its chain."""
    return _tenant_post(base_url, seed, f"/care-events/{event_key}/redact", {"reason": reason})


def create_bed_task(
    base_url: str, seed: dict, *, bed_key: str, name: str, category: str, days_ahead: int = 0
) -> str:
    """An open task on the bed itself (``entity_type = location``), due *days_ahead* days from today."""
    due = (datetime.now(UTC) + timedelta(days=days_ahead)).replace(hour=23, minute=0, second=0)
    task = _tenant_post(
        base_url,
        seed,
        "/tasks",
        {
            "name": name,
            "category": category,
            "priority": "medium",
            "entity_type": "location",
            "entity_key": bed_key,
            "due_date": due.isoformat(),
        },
        expected=(201,),
    )
    return task["key"]


def task_state(base_url: str, seed: dict, task_key: str) -> dict:
    """``GET /tasks/{key}``: the task as the server holds it."""
    body = tenant_get(base_url, seed, f"/tasks/{task_key}")
    if not isinstance(body, dict):
        raise AssertionError(f"task {task_key!r} is not an object: {body!r}")
    return body


# ── Wave 7: irrigation zones and the concurrent writer (WP 7.25) ────────────
#
# The zone tests arrange zones through the routes the zone panel itself calls
# (GP-API-050/051): ``POST /sites/{key}/irrigation-zones`` creates the zone,
# ``PUT /irrigation-zones/{key}/locations`` assigns its beds. The "someone else
# saved meanwhile" precondition of the auto-save case is one ``plan/batch`` with
# the revision the editor holds - exactly what a second editor's save sends.


def create_zone(
    base_url: str,
    seed: dict,
    *,
    site_key: str,
    name: str,
    bed_keys: tuple[str, ...],
    irrigation_type: str = "manual",
    color: str = "#1565C0",
) -> dict:
    """A zone on *site_key* covering *bed_keys* (GP-API-050 + 051); the zone as the server answers it."""
    zone = _tenant_post(
        base_url,
        seed,
        f"/sites/{site_key}/irrigation-zones",
        {"name": name, "irrigation_type": irrigation_type, "color": color},
        expected=(201,),
    )
    status, body = tenant_request(
        base_url,
        seed,
        "PUT",
        f"/irrigation-zones/{zone['key']}/locations",
        {"location_keys": list(bed_keys)},
    )
    _require(status, body, (200,), f"PUT /irrigation-zones/{zone['key']}/locations")
    if not isinstance(body, dict) or sorted(body.get("location_keys") or []) != sorted(bed_keys):
        raise AssertionError(
            f"Self-provisioning failed: zone {zone['key']!r} should cover {sorted(bed_keys)}, "
            f"the server answered {body!r}"
        )
    return body


def zones_of_site(base_url: str, seed: dict, site_key: str) -> list[dict]:
    """``GET /sites/{key}/irrigation-zones`` (GP-API-050): the stored zones of the site."""
    body = tenant_get(base_url, seed, f"/sites/{site_key}/irrigation-zones")
    if not isinstance(body, list):
        raise AssertionError(f"zones of site {site_key!r} is not a list: {body!r}")
    return body


def move_location_via_api(
    base_url: str,
    seed: dict,
    *,
    site_key: str,
    expected_revision: int,
    location_key: str,
    geometry: dict,
) -> int:
    """Save a new geometry for *location_key* as a second editor would (GP-API-003); the new revision."""
    api, token = _api(base_url, seed)
    status, body = _api_request(
        f"{api}/sites/{site_key}/plan/batch",
        "POST",
        token,
        {
            "expected_revision": expected_revision,
            "operations": [
                {
                    "op": "update_geometry",
                    "entity": "location",
                    "key": location_key,
                    "geometry": geometry,
                }
            ],
        },
    )
    _require(status, body, (200,), f"POST /sites/{site_key}/plan/batch (concurrent writer)")
    return int(body["plan_revision"])


def stored_location(plan: dict, name: str) -> dict:
    """The stored location named *name*; fails loudly when there is none or more than one."""
    found = [loc for loc in plan.get("locations") or [] if loc.get("name") == name]
    if len(found) != 1:
        names = [loc.get("name") for loc in plan.get("locations") or []]
        raise AssertionError(
            f"expected exactly one stored location {name!r}, found {len(found)}: {names}"
        )
    return found[0]


def days_since_utc(instant: str) -> int:
    """Whole UTC calendar days from *instant* (ISO 8601) to today - the day rule of the last-watered layer."""
    moment = datetime.fromisoformat(instant.replace("Z", "+00:00")).astimezone(UTC)
    return (utc_today() - moment.date()).days


# ── Wave 7 part B: season, partial export, snapshots, sun profile (WP 7.26) ──
#
# The arrangements go through the routes the product itself calls:
#
# * ``POST /locations/{key}/clear`` (GP-API-019) is the only path that ends a run's slots (``archived_at``),
#   which is what "new season from the previous year" copies from - the "Beet räumen" action has no browser
#   surface yet, so the API is the arrangement, not a shortcut past a UI;
# * ``GET /sites/{key}/plan/export`` (GP-API-004) is exactly the request the export dialog downloads, with the
#   same ``scope`` / ``keys`` query (``exportParams``);
# * ``POST /sites/{key}/plan/import`` (GP-API-005) with ``mode = replace`` writes the snapshot a restore needs;
# * ``PATCH /locations/{key}`` with ``site_conditions.sun_profile`` is what the bed dialog and the field-mode
#   sun chips send (``patchSun``).


def clear_bed(base_url: str, seed: dict, bed_key: str, termination_type: str = "harvested") -> dict:
    """End every plant and run of *bed_key* (GP-API-019); its slots become history (``archived_at`` = now)."""
    body = _tenant_post(
        base_url, seed, f"/locations/{bed_key}/clear", {"termination_type": termination_type}
    )
    if int(body.get("slots_archived") or 0) == 0:
        raise AssertionError(
            f"Self-provisioning failed: clearing {bed_key!r} archived no slot: {body!r}"
        )
    return body


def export_plan_json(
    base_url: str, seed: dict, site_key: str, *, scope: str = "site", keys: tuple[str, ...] = ()
) -> dict:
    """The JSON backup exactly as the export dialog requests it (GP-API-004, ``exportParams``)."""
    query = "" if scope == "site" else f"?scope={scope}&keys={','.join(keys)}"
    body = tenant_get(base_url, seed, f"/sites/{site_key}/plan/export{query}")
    if not isinstance(body, dict) or "schema_version" not in body:
        raise AssertionError(f"the plan export of {site_key!r} is not a backup: {body!r}")
    return body


def replace_plan_with(
    base_url: str,
    seed: dict,
    *,
    site_key: str,
    site_name: str,
    document: dict,
    timeout: float = 15,
) -> dict:
    """Write *document* over the site's plan (``mode = replace``, GP-API-005); the server keeps a snapshot.

    *timeout* (seconds) is raised only for a large file (the renderer plans of WP 9.6)."""
    report = _tenant_post(
        base_url,
        seed,
        f"/sites/{site_key}/plan/import",
        {
            "mode": "replace",
            "dry_run": False,
            "force": False,
            "confirm_site_name": site_name,
            "target": "same_site",
            "document": document,
        },
        timeout=timeout,
    )
    if not report.get("applied") or not report.get("snapshot_written"):
        raise AssertionError(
            f"Self-provisioning failed: the replace import of {site_key!r} was not applied with a "
            f"snapshot: {report!r}"
        )
    return report


def plan_snapshots(base_url: str, seed: dict, site_key: str) -> list[dict]:
    """``GET /sites/{key}/plan/snapshots`` (GP-FR-148): the earlier states of the plan, newest first."""
    body = tenant_get(base_url, seed, f"/sites/{site_key}/plan/snapshots")
    if not isinstance(body, list):
        raise AssertionError(f"snapshots of {site_key!r} is not a list: {body!r}")
    return body


def add_bed_via_batch(
    base_url: str, seed: dict, *, site_key: str, name: str, geometry: dict
) -> str:
    """One more bed through the editor's own save (GP-API-003, ``create_location``); its new key."""
    revision = int(read_plan(base_url, seed, site_key)["plan_revision"])
    api, token = _api(base_url, seed)
    status, body = _api_request(
        f"{api}/sites/{site_key}/plan/batch",
        "POST",
        token,
        {
            "expected_revision": revision,
            "operations": [
                {
                    "op": "create_location",
                    "temp_key": "extra",
                    "data": {"name": name, "location_type_key": "raised_bed", "geometry": geometry},
                }
            ],
        },
    )
    _require(status, body, (200,), f"POST /sites/{site_key}/plan/batch (add {name!r})")
    return _mapped(body.get("key_map") or {}, "extra", name)


def set_sun_window(base_url: str, seed: dict, bed_key: str, window: str) -> dict:
    """Store the bed's sun window as the bed dialog does (``PATCH /locations/{key}``, merged per key)."""
    status, body = tenant_request(
        base_url,
        seed,
        "PATCH",
        f"/locations/{bed_key}",
        {"site_conditions": {"sun_profile": {"sun_window": window}}},
    )
    _require(status, body, (200,), f"PATCH /locations/{bed_key} (sun window)")
    return body


def sun_profile(base_url: str, seed: dict, bed_key: str) -> dict:
    """The stored ``site_conditions.sun_profile`` of a bed (``{}`` when none is stored)."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}")
    if not isinstance(body, dict) or body.get("key") != bed_key:
        raise AssertionError(f"GET /locations/{bed_key} answered no location: {body!r}")
    return dict((body.get("site_conditions") or {}).get("sun_profile") or {})


def rotation_years(base_url: str, seed: dict, bed_key: str) -> dict[int, list[dict]]:
    """``GET /locations/{key}/rotation`` (GP-API-039): the plantings of the bed per calendar year."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/rotation")
    if not isinstance(body, dict) or not isinstance(body.get("timeline"), list):
        raise AssertionError(f"the rotation timeline of {bed_key!r} has no timeline: {body!r}")
    return {int(entry["year"]): list(entry.get("plantings") or []) for entry in body["timeline"]}


# ── Wave 8 part A: soil, area dose, rotation matrix, suggestions (WP 8.30) ──
#
# Arranged through the routes the bed view itself calls - ``POST /care-events`` for a soil analysis or a care line,
# ``POST /fertilizers`` for a catalogue product with a data-sheet rate, ``POST /locations/{key}/history/backfill`` for
# a past year, ``PATCH /locations/{key}`` for the rotation switch - with ONE named exception: the suggestion flag of a
# task (:func:`mark_task_suggested`), which no route writes.


def record_soil_analysis(
    base_url: str,
    seed: dict,
    *,
    bed_key: str,
    measurements: list[dict],
    days_ago: float = 0.0,
    summary: str = "Bodenanalyse (E2E)",
) -> dict:
    """``POST /care-events`` with ``category = soil_analysis`` - the body the "Bodenanalyse erfassen" dialog sends."""
    return log_care_event(
        base_url,
        seed,
        bed_key=bed_key,
        category="soil_analysis",
        summary=summary,
        days_ago=days_ago,
        measurements=measurements,
    )


def soil_analyses(base_url: str, seed: dict, bed_key: str) -> dict:
    """``GET /locations/{key}/soil-analyses``: the series per parameter and method, the method changes, the liming hint."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/soil-analyses")
    if not isinstance(body, dict) or not isinstance(body.get("series"), list):
        raise AssertionError(f"the soil analyses of {bed_key!r} carry no series: {body!r}")
    return body


def soil_series(analyses: dict, parameter: str) -> dict[str, list[float]]:
    """``{method: [value, ...]}`` of one parameter, oldest first (the server's order)."""
    return {
        entry["method"]: [float(point["value"]) for point in entry["points"]]
        for entry in analyses["series"]
        if entry["parameter"] == parameter
    }


def stored_soil_profile(base_url: str, seed: dict, bed_key: str, *, required: bool = True) -> dict:
    """The stored ``soil_profile`` of a bed.

    ``required`` (the default) is loud when the bed has none - the reader after a write. ``required=False`` answers
    ``{}`` for a bed without profile - the precondition read of a fresh bed. Either way an answer that is no
    location of *bed_key* is loud.
    """
    body = tenant_get(base_url, seed, f"/locations/{bed_key}")
    if not isinstance(body, dict) or body.get("key") != bed_key:
        raise AssertionError(f"GET /locations/{bed_key} answered no location: {body!r}")
    profile = body.get("soil_profile")
    if isinstance(profile, dict):
        return profile
    if required or profile is not None:
        raise AssertionError(f"the bed {bed_key!r} has no stored soil profile: {profile!r}")
    return {}


def bed_summary(base_url: str, seed: dict, bed_key: str) -> dict:
    """``GET /locations/{key}/summary`` (GP-API-012): what the bed head renders, ``nutrient_hint`` included."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/summary")
    if not isinstance(body, dict) or body.get("key") != bed_key:
        raise AssertionError(f"the summary of {bed_key!r} is no bed summary: {body!r}")
    return body


def create_fertilizer(
    base_url: str,
    seed: dict,
    *,
    name: str,
    rate_g_per_m2: float | None = None,
    rate_l_per_m2: float | None = None,
    npk: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> dict:
    """A tenant catalogue product with a data-sheet area rate (REQ-004 W-013), as the fertilizer form creates it."""
    data: dict = {
        "product_name": name,
        "fertilizer_type": "organic",
        "is_organic": True,
        "tank_safe": False,
        "npk_ratio": [float(value) for value in npk],
    }
    if rate_g_per_m2 is not None:
        data["application_rate_g_per_m2"] = float(rate_g_per_m2)
    if rate_l_per_m2 is not None:
        data["application_rate_l_per_m2"] = float(rate_l_per_m2)
    return _tenant_post(base_url, seed, "/fertilizers", data, expected=(201,))


def create_bed_without_area(base_url: str, seed: dict, *, site_key: str, name: str) -> str:
    """A legacy bed without geometry (``area_m2 = 0``, TC-053-011): the per-m² dose units are blocked for it."""
    body = _tenant_post(
        base_url,
        seed,
        "/locations",
        {"name": name, "site_key": site_key, "location_type_key": "raised_bed", "area_m2": 0.0},
        expected=(201,),
    )
    return body["key"]


def backfill_year(
    base_url: str,
    seed: dict,
    bed_key: str,
    year: int,
    *,
    species_key: str | None = None,
    family_key: str | None = None,
    season: str | None = None,
) -> int:
    """Record what stood in the bed in *year* (GP-API-042, main crop): a species or a family.

    *season* (``spring`` / ``main`` / ``autumn``) dates the entry to that season's middle; two entries of one year
    with ``spring`` and ``main`` are a pre-crop and its main crop as the product records them.
    """
    data: dict = {"year": year, "plan_role": "main_crop"}
    if season:
        data["season"] = season
    if species_key:
        data["species_key"] = species_key
    if family_key:
        data["family_key"] = family_key
    _tenant_post(base_url, seed, f"/locations/{bed_key}/history/backfill", data)
    return year


_FAMILY_CACHE: dict[tuple[str, str], str] = {}


def botanical_family_key(base_url: str, seed: dict, name: str) -> str:
    """The key of the seeded botanical family *name* (``Cucurbitaceae``); loud when the catalogue lacks it."""
    cached = _FAMILY_CACHE.get((base_url, name))
    if cached is not None:
        return cached
    api, token = _global_api(base_url, seed)
    status, body = _api_request(f"{api}/botanical-families?offset=0&limit=200", "GET", token)
    _require(status, body, (200,), "GET /botanical-families")
    items = body if isinstance(body, list) else (body.get("items") or [])
    for item in items:
        _FAMILY_CACHE[(base_url, item.get("name", ""))] = item["key"]
    if (base_url, name) not in _FAMILY_CACHE:
        raise AssertionError(
            f"Self-provisioning failed: the botanical family catalogue has no {name!r}; "
            f"{len(items)} families listed"
        )
    return _FAMILY_CACHE[(base_url, name)]


def rotation_matrix(base_url: str, seed: dict, site_key: str) -> dict:
    """``GET /sites/{key}/rotation-matrix`` (GP-FR-135): beds x years as the matrix page reads it."""
    body = tenant_get(base_url, seed, f"/sites/{site_key}/rotation-matrix")
    if not isinstance(body, dict) or not isinstance(body.get("beds"), list):
        raise AssertionError(f"the rotation matrix of {site_key!r} has no beds: {body!r}")
    return body


def succession_recommendation(base_url: str, seed: dict, bed_key: str) -> dict:
    """``GET /locations/{key}/succession-recommendation`` (GP-FR-133)."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/succession-recommendation")
    if not isinstance(body, dict) or "status" not in body:
        raise AssertionError(
            f"the succession recommendation of {bed_key!r} has no status: {body!r}"
        )
    return body


def patch_location(base_url: str, seed: dict, bed_key: str, data: dict) -> dict:
    """``PATCH /locations/{key}`` with *data*; loud on anything but 200."""
    status, body = tenant_request(base_url, seed, "PATCH", f"/locations/{bed_key}", data)
    _require(status, body, (200,), f"PATCH /locations/{bed_key} ({sorted(data)})")
    return body


def tenant_location(base_url: str, seed: dict, bed_key: str) -> dict:
    body = tenant_get(base_url, seed, f"/locations/{bed_key}")
    if not isinstance(body, dict) or body.get("key") != bed_key:
        raise AssertionError(f"GET /locations/{bed_key} answered no location: {body!r}")
    return body


#: The E2E stack's ArangoDB as the compose file runs it (``docker-compose.e2e.yml``: service ``arangodb``, root
#: password ``e2e-test-password``, database ``kamerplanter_e2e`` for the light and ``kamerplanter_e2e_full`` for the
#: full app stack). Every value can be overridden for a stack that runs elsewhere.
_ARANGO_URL = os.environ.get("E2E_ARANGO_URL", "http://arangodb:8529")
_ARANGO_USER = os.environ.get("E2E_ARANGO_USER", "root")
_ARANGO_PASSWORD = os.environ.get("E2E_ARANGO_PASSWORD", "e2e-test-password")
_ARANGO_DB = {"light": "kamerplanter_e2e", "full": "kamerplanter_e2e_full"}


def _arango_document_write(
    app_mode: str, method: str, path: str, document: dict, *, what: str, reason_no_route: str
) -> None:
    """One document write on the backend's ArangoDB (``/_db/<db>/_api/document/<path>``); loud on every failure.

    The single place the two named direct writes go through. *what* names the arranged state in the failure
    message, *reason_no_route* says why there is no API route for it.
    """
    if app_mode not in _ARANGO_DB:
        raise AssertionError(f"{what}: unknown app mode {app_mode!r}")
    database = os.environ.get("E2E_ARANGO_DB", _ARANGO_DB[app_mode])
    url = f"{_ARANGO_URL.rstrip('/')}/_db/{database}/_api/document/{path}"
    credentials = base64.b64encode(f"{_ARANGO_USER}:{_ARANGO_PASSWORD}".encode()).decode()
    request = urllib.request.Request(
        url,
        data=json.dumps(document).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Basic {credentials}"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        raise AssertionError(
            f"Self-provisioning failed: ArangoDB refused {what} ({database}): {exc.code} {exc.read()[:300]!r}"
        ) from exc
    except urllib.error.URLError as exc:
        raise AssertionError(
            f"Self-provisioning failed: ArangoDB at {_ARANGO_URL} is not reachable from the test runner "
            f"({exc.reason}). {reason_no_route}; set E2E_ARANGO_URL / E2E_ARANGO_DB / E2E_ARANGO_PASSWORD when the "
            "stack does not run from docker-compose.e2e.yml."
        ) from exc
    if status not in (200, 201, 202):
        raise AssertionError(f"Self-provisioning failed: ArangoDB answered {status} for {what}")


def mark_task_suggested(app_mode: str, task_key: str, reason: str) -> None:
    """Turn an open task into a system suggestion (``suggested = true`` + ``suggestion_reason``).

    **Divergence from the running system, named (`test-pyramid-foundation` §"Arrangement fidelity", T9).** No route
    and no producer writes ``suggested = true`` yet (REQ-053 E-02: the producer belongs to the ADR-008 propagation
    strand; ``TaskCreate`` has no such field). The task itself is created through ``POST /tasks``, so every
    attribute the creation path enforces - tenant, entity link, edge, ``care_dedup_key`` - is the system's own; this
    write only sets the two fields the ``Task`` model declares for a proposal (``app/domain/models/task.py``,
    migration v0095) on that document. The state is reachable by the model; only its producer is missing.

    A direct ``PATCH`` on ArangoDB's document API - the database the backend under test uses. Loud when the database
    cannot be reached or refuses the write: a missing suggestion must never read as "the section is hidden".
    """
    _arango_document_write(
        app_mode,
        "PATCH",
        f"tasks/{task_key}",
        {"suggested": True, "suggestion_reason": reason},
        what=f"the suggestion flag on task {task_key}",
        reason_no_route="The suggestion flag has no API route",
    )


# ── Wave 8 part B: companion layer, site features, photos, CSV, frost reason (WP 8.31) ──
#
# Arranged through the routes the product itself calls - ``PUT /slots/{a}/adjacent/{b}`` is the "mark as
# neighbours" action of the slot neighbourhood (SR-021), ``PATCH /locations/{key}`` with ``site_conditions`` /
# ``soil_profile`` is what the site-conditions dialog and the field-mode chips send, ``POST /tenants/{slug}/assignments``
# is the assignment the tenant settings write - with ONE named exception: a stored weather forecast
# (:func:`store_frost_forecast`), which only the weather fetch task writes.


def mark_neighbours(base_url: str, seed: dict, slot_a: str, slot_b: str) -> None:
    """``PUT /slots/{a}/adjacent/{b}`` (manual neighbourhood, both directions); loud on anything but 204.

    The manual edge, not the derived one: the derivation runs out of band (a Celery task after a slot change), so a
    test that waited for it would wait on a worker; a manual edge is the user's own path and is never removed by the
    geometry.
    """
    status, body = tenant_request(base_url, seed, "PUT", f"/slots/{slot_a}/adjacent/{slot_b}")
    _require(status, body, (204,), f"PUT /slots/{slot_a}/adjacent/{slot_b}")


def companion_edges(base_url: str, seed: dict, bed_key: str) -> list[dict]:
    """``GET /locations/{key}/companion-edges`` (GP-FR-134): the judged neighbour pairs the layer draws."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/companion-edges")
    if not isinstance(body, dict) or not isinstance(body.get("edges"), list):
        raise AssertionError(f"the companion edges of {bed_key!r} carry no edge list: {body!r}")
    return body["edges"]


def edge_between(edges: list[dict], slot_a: str, slot_b: str) -> dict:
    """The judged pair of *slot_a* and *slot_b* (either order); loud when the server answers none."""
    for edge in edges:
        if {edge["slot_a"]["slot_key"], edge["slot_b"]["slot_key"]} == {slot_a, slot_b}:
            return edge
    pairs = [(e["slot_a"]["slot_key"], e["slot_b"]["slot_key"], e["status"]) for e in edges]
    raise AssertionError(
        f"no companion edge between {slot_a!r} and {slot_b!r}; the server judged {pairs}"
    )


def site_conditions(base_url: str, seed: dict, bed_key: str) -> dict:
    """The stored ``site_conditions`` of a bed (``{}`` when none are stored)."""
    return dict(tenant_location(base_url, seed, bed_key).get("site_conditions") or {})


def bed_photos(base_url: str, seed: dict, bed_key: str) -> dict:
    """``GET /locations/{key}/photos`` (GP-FR-051): the gallery as the photos tab reads it."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/photos")
    if not isinstance(body, dict) or not isinstance(body.get("photos"), list):
        raise AssertionError(f"the photo gallery of {bed_key!r} has no photo list: {body!r}")
    return body


def plant_photos(base_url: str, seed: dict, plant_key: str) -> list[dict]:
    """``GET /plant-instances/{key}/photos`` (REQ-034): the gallery of one plant."""
    body = tenant_get(base_url, seed, f"/plant-instances/{plant_key}/photos")
    if not isinstance(body, dict) or not isinstance(body.get("photos"), list):
        raise AssertionError(
            f"the photo gallery of plant {plant_key!r} has no photo list: {body!r}"
        )
    return body["photos"]


def _tenants_api(base_url: str, seed: dict) -> tuple[str, str | None]:
    from .conftest import _fresh_access_token

    slug = seed.get("tenant_slug", "mein-garten")
    return f"{base_url.rstrip('/')}/api/v1/tenants/{slug}", _fresh_access_token(seed, base_url)


def acting_member(base_url: str, seed: dict) -> dict:
    """The acting account's membership in the test tenant (``key``, ``display_name``); loud when it has none.

    ``GET /users/me`` names the account, ``GET /tenants/{slug}/members`` its membership - the two reads the tenant
    settings page makes.
    """
    api, token = _global_api(base_url, seed)
    status, me = _api_request(f"{api}/users/me", "GET", token)
    _require(status, me, (200,), "GET /users/me")
    tenants, token = _tenants_api(base_url, seed)
    status, members = _api_request(f"{tenants}/members?offset=0&limit=200", "GET", token)
    _require(status, members, (200,), "GET /tenants/{slug}/members")
    mine = [m for m in members if isinstance(m, dict) and m.get("user_key") == me.get("key")]
    if len(mine) != 1 or not (mine[0].get("display_name") or "").strip():
        raise AssertionError(
            f"Self-provisioning failed: the acting account {me.get('key')!r} should have exactly one membership "
            f"with a display name in the test tenant; members: {members!r}"
        )
    return mine[0]


def assign_bed(base_url: str, seed: dict, *, membership_key: str, bed_key: str) -> dict:
    """``POST /tenants/{slug}/assignments`` (REQ-049 §3.5): *bed_key* becomes the member's responsibility."""
    tenants, token = _tenants_api(base_url, seed)
    status, body = _api_request(
        f"{tenants}/assignments",
        "POST",
        token,
        {"membership_key": membership_key, "location_key": bed_key, "can_edit": True},
    )
    _require(status, body, (201,), f"POST /tenants/{{slug}}/assignments ({bed_key})")
    return body


def tenant_key_of(base_url: str, seed: dict) -> str:
    """The document key of the test tenant (``GET /tenants/{slug}``)."""
    tenants, token = _tenants_api(base_url, seed)
    status, body = _api_request(tenants, "GET", token)
    _require(status, body, (200,), "GET /tenants/{slug}")
    if not body.get("key"):
        raise AssertionError(f"GET /tenants/{{slug}} answered no key: {body!r}")
    return str(body["key"])


def plant_states(base_url: str, seed: dict, bed_key: str) -> dict[str, list[str]]:
    """``GET /locations/{key}/plant-states``: plant key -> the attention reasons, highest priority first."""
    body = tenant_get(base_url, seed, f"/locations/{bed_key}/plant-states")
    if not isinstance(body, list):
        raise AssertionError(f"the plant states of {bed_key!r} are not a list: {body!r}")
    return {
        row["plant_key"]: [item["reason"] for item in row.get("attention") or []] for row in body
    }


def store_frost_forecast(
    app_mode: str, *, tenant_key: str, site_key: str, temp_min_c: float = -3.0
) -> None:
    """Store one daily forecast for *site_key* for today (UTC) with a night minimum of *temp_min_c*.

    **Divergence from the running system, named (`test-pyramid-foundation` §"Arrangement fidelity", T9).** A
    forecast is written only by the weather fetch task (Open-Meteo / DWD / Home Assistant through
    ``WeatherForecastRepository.upsert_daily``); the E2E stack has neither an outbound weather source nor a route that
    stores a forecast. This write is the document that path stores - every field of ``WeatherForecast``
    (``app/domain/models/weather.py``) with the values a fetched forecast carries (``data_kind = forecast``,
    ``source``, ``fetched_at``), scoped to the tenant and the site - in the ``weather_forecasts`` collection the plant
    state reads by ``site_key`` and ``tenant_key`` (``find_by_site``). Not written: the ``has_forecast`` graph edge,
    which no reader of the frost verdict follows. The state is the one a fetch produces; only the producer is missing.

    Loud when the database cannot be reached or refuses the write: a missing forecast must never read as "no frost".
    """
    # One instant for both: "today" and the fetch time must not straddle midnight UTC.
    now = datetime.now(UTC)
    document = {
        "tenant_key": tenant_key,
        "site_key": site_key,
        "forecast_date": now.date().isoformat(),
        "temp_min_c": float(temp_min_c),
        "temp_max_c": float(temp_min_c) + 9.0,
        "source": "open_meteo",
        "fetched_at": now.isoformat(),
        "data_kind": "forecast",
        "is_current_conditions": False,
    }
    _arango_document_write(
        app_mode,
        "POST",
        "weather_forecasts",
        document,
        what=f"the forecast for site {site_key}",
        reason_no_route="A forecast has no API route",
    )


# ── Wave 10 part B: sown/thinned/failed slots, phases, object tasks, feeding (WP 10.14) ──
#
# The domain cases of wave 10 arrange their preconditions through the routes the product's own dialogs and pages
# call - no direct database write:
#
# * ``POST /locations/{key}/slots/batch`` + ``POST /planting-runs`` + ``POST …/plan-slots`` reserve a ``row`` slot for a
#   planned run (GP-API-015/021), the state the planting dialog leaves behind before direct sowing; the run entry's
#   ``thinning_to_cm`` is the run's own field (``EntryCreate``), filled from the species data or left empty (E-10);
# * ``POST /plant-instances/{key}/remove`` with ``termination_type = died`` records a failed plant (REQ-003 E5), the
#   way the plant page's "Entfernen" dialog does;
# * ``POST /plant-instances`` with ``current_phase_key`` creates a plant in a given phase, as the plant form does;
#   the phase and its photoperiod come from the species' lifecycle (``GET /species/{key}/lifecycle``,
#   ``GET /growth-phases``, ``GET /profiles/requirements/{phase}``) - the test never invents a photoperiod.


def lower_bound_cm(value: object) -> float | None:
    """The leading number of a species distance (``"5--8"`` -> 5.0, ``"7,5"`` -> 7.5); ``None`` without one.

    The rule of the planting dialog's prefill (``plantingLogic.ts::parseLowerBound``): the Steckbrief value a grower
    starts from. A non-positive or missing value is no value - never replaced by a default (E-10).
    """
    if isinstance(value, int | float):
        return float(value) if value > 0 else None
    if not isinstance(value, str):
        return None
    head = value.strip()
    digits = ""
    for char in head:
        if char.isdigit() or (char in ".," and digits and "." not in digits):
            digits += "." if char == "," else char
            continue
        break
    try:
        parsed = float(digits.rstrip("."))
    except ValueError:
        return None
    return parsed if parsed > 0 else None


@dataclass(frozen=True)
class ReservedRow:
    """A ``row`` slot of a bed reserved by a planned run (not sown yet): what the planting tab lists as "Geplant"."""

    slot_key: str
    slot_id: str
    run_key: str
    entry_key: str


def reserved_row(
    base_url: str,
    seed: dict,
    *,
    bed_key: str,
    species_key: str,
    id_prefix: str,
    points: tuple[tuple[float, float], ...],
    thinning_to_cm: float | None,
) -> ReservedRow:
    """A ``row`` slot along *points* (bed frame, metres) reserved by a planned monoculture run of *species_key*.

    *thinning_to_cm* is the run entry's spacing after thinning - the caller passes the species' value or ``None``
    (then the thinning dialog must ask for it, E-10). Loud on every refusal and on a reservation that did not land.
    """
    tag = unique_tag().upper()
    slot_id = f"S{tag}_R01"
    created = _tenant_post(
        base_url,
        seed,
        f"/locations/{bed_key}/slots/batch",
        {
            "mode": "append",
            "slots": [
                {
                    "slot_id": slot_id,
                    "slot_role": "row",
                    "geometry": {
                        "kind": "polyline",
                        "points": [[float(x), float(y)] for x, y in points],
                        "width_m": 0.05,
                    },
                    "capacity_plants": 1,
                    "sequence": 1,
                }
            ],
        },
    )
    slot_keys = list(created.get("created_keys") or [])
    if len(slot_keys) != 1:
        raise AssertionError(f"Self-provisioning failed: asked for one row slot, got {created!r}")
    entry: dict = {"layout_strategy": "free"}
    if thinning_to_cm is not None:
        entry["thinning_to_cm"] = float(thinning_to_cm)
    run = _tenant_post(
        base_url,
        seed,
        "/planting-runs",
        run_payload(
            bed_key=bed_key,
            species_key=species_key,
            id_prefix=id_prefix,
            quantity=1,
            name=f"E2E-GP-run-{unique_tag()}",
            entry=entry,
        ),
        expected=(201,),
    )
    run_key = run["key"]
    entries = tenant_get(base_url, seed, f"/planting-runs/{run_key}/entries")
    if not isinstance(entries, list) or len(entries) != 1:
        raise AssertionError(f"Self-provisioning failed: run {run_key!r} has entries {entries!r}")
    stored_spacing = entries[0].get("thinning_to_cm")
    if stored_spacing != (None if thinning_to_cm is None else float(thinning_to_cm)):
        raise AssertionError(
            f"Self-provisioning failed: the run entry stores thinning_to_cm={stored_spacing!r}, "
            f"asked for {thinning_to_cm!r}"
        )
    _tenant_post(
        base_url,
        seed,
        f"/planting-runs/{run_key}/plan-slots",
        {"entry_key": entries[0]["key"], "slot_keys": slot_keys},
    )
    planned = [
        item
        for item in plantings(base_url, seed, bed_key, "planned")
        if item.get("slot_key") == slot_keys[0]
    ]
    if len(planned) != 1 or planned[0].get("sown_at"):
        raise AssertionError(
            f"Self-provisioning failed: the row {slot_keys[0]!r} should be planned and not sown: {planned!r}"
        )
    return ReservedRow(
        slot_key=slot_keys[0], slot_id=slot_id, run_key=run_key, entry_key=entries[0]["key"]
    )


def thinning_plan(base_url: str, seed: dict, slot_key: str) -> dict:
    """``GET /slots/{key}/thinning``: the server's spacing, measure and suggested count of a sown slot."""
    body = tenant_get(base_url, seed, f"/slots/{slot_key}/thinning")
    if not isinstance(body, dict):
        raise AssertionError(f"the thinning plan of {slot_key!r} is not an object: {body!r}")
    return body


def stored_slot(base_url: str, seed: dict, bed_key: str, slot_key: str) -> dict:
    """The live slot *slot_key* of *bed_key* as the server holds it; loud when it is not listed."""
    for slot in bed_slots(base_url, seed, bed_key):
        if slot.get("key") == slot_key:
            return slot
    raise AssertionError(f"slot {slot_key!r} is not a live slot of bed {bed_key!r}")


def remove_plant(
    base_url: str,
    seed: dict,
    plant_key: str,
    termination_type: str,
    termination_cause: str | None = None,
) -> dict:
    """``POST /plant-instances/{key}/remove`` with *termination_type* (``died``, ``senesced``, ...), REQ-003 E5.

    *termination_cause* (``disease``, ``pest``, ``frost``, ...) is only valid with ``died``.
    """
    body: dict[str, str] = {"termination_type": termination_type}
    if termination_cause is not None:
        body["termination_cause"] = termination_cause
    removed = _tenant_post(base_url, seed, f"/plant-instances/{plant_key}/remove", body)
    if (
        removed.get("termination_type") != termination_type
        or not removed.get("removed_on")
        or (termination_cause is not None and removed.get("termination_cause") != termination_cause)
    ):
        raise AssertionError(
            f"Self-provisioning failed: plant {plant_key!r} is not recorded as {termination_type}: {removed!r}"
        )
    return removed


def sow_slot(base_url: str, seed: dict, slot_key: str, sown_at: date) -> dict:
    """``PUT /slots/{key}/sowing``: record the direct sowing of a reserved row or zone (what the sowing dialog sends)."""
    status, body = tenant_request(
        base_url, seed, "PUT", f"/slots/{slot_key}/sowing", {"sown_at": sown_at.isoformat()}
    )
    _require(status, body, (200,), f"PUT /slots/{slot_key}/sowing")
    if not isinstance(body, dict) or body.get("sown_at") != sown_at.isoformat():
        raise AssertionError(f"Self-provisioning failed: slot {slot_key!r} is not sown: {body!r}")
    return body


@dataclass(frozen=True)
class PhasePhotoperiod:
    """One entry of a species' phase sequence with the photoperiod of its phase profile (REQ-003).

    ``key`` is the sequence entry - what a plant's ``current_phase_key`` holds; ``name`` the phase definition's
    machine name, by which the entry is bridged to the growth phase whose requirement profile carries the photoperiod.
    ``display_name`` / ``display_name_de`` are the phase definition's English and German names from the catalogue.
    """

    key: str
    name: str
    photoperiod_hours: float
    display_name: str = ""
    display_name_de: str = ""


def phase_photoperiods(base_url: str, seed: dict, species_key: str) -> list[PhasePhotoperiod]:
    """The phase-sequence entries of *species_key* with the ``photoperiod_hours`` of their phase profile.

    Read from the global catalogue along the path the tent hint reads (``load_location_photoperiods``): the sequence
    entry's phase definition name, the growth phase of exactly that name in the species' lifecycle, its requirement
    profile. An entry with no or two matching growth phases, or without a photoperiod, is left out - never given a
    default (E-10).
    """
    api, token = _global_api(base_url, seed)
    status, sequence = _api_request(f"{api}/species/{species_key}/phase-sequence", "GET", token)
    _require(status, sequence, (200,), f"GET /species/{species_key}/phase-sequence")
    status, lifecycle = _api_request(f"{api}/species/{species_key}/lifecycle", "GET", token)
    _require(status, lifecycle, (200,), f"GET /species/{species_key}/lifecycle")
    status, phases = _api_request(
        f"{api}/growth-phases?lifecycle_key={lifecycle['key']}", "GET", token
    )
    _require(status, phases, (200,), f"GET /growth-phases?lifecycle_key={lifecycle['key']}")
    by_name: dict[str, list[dict]] = {}
    for phase in phases:
        by_name.setdefault(str(phase["name"]), []).append(phase)
    found: list[PhasePhotoperiod] = []
    for entry in (sequence or {}).get("entries") or []:
        definition = entry.get("phase_definition") or {}
        name = str(definition.get("name") or "")
        matches = by_name.get(name) or []
        if len(matches) != 1:
            continue
        status, profile = _api_request(
            f"{api}/profiles/requirements/{matches[0]['key']}", "GET", token
        )
        if status == 404:
            continue
        _require(status, profile, (200,), f"GET /profiles/requirements/{matches[0]['key']}")
        hours = profile.get("photoperiod_hours")
        if hours is None:
            continue
        found.append(
            PhasePhotoperiod(
                key=str(entry["key"]),
                name=name,
                photoperiod_hours=float(hours),
                display_name=str(definition.get("display_name") or ""),
                display_name_de=str(definition.get("display_name_de") or ""),
            )
        )
    return found


#: The fields ``PUT /profiles/requirements/{key}`` takes (``RequirementProfileCreate``); the rest is the server's.
_REQUIREMENT_PROFILE_BODY_FIELDS = (
    "phase_key",
    "light_ppfd_target",
    "photoperiod_hours",
    "light_spectrum",
    "temperature_day_c",
    "temperature_night_c",
    "humidity_day_percent",
    "humidity_night_percent",
    "vpd_target_kpa",
    "co2_ppm",
    "irrigation_frequency_days",
    "irrigation_volume_ml_per_plant",
)


def _platform_admin_api(base_url: str, seed: dict) -> tuple[str, str | None]:
    """The API base and a token of the platform admin: the catalogue's phase profiles are theirs to edit (#1120).

    Light mode has no login (the sole operator is the platform admin, REQ-027): ``None``. Full mode logs in as the
    seeded platform-admin account (``seed_e2e_platform_admin.py``), never as the demo user.
    """
    from .conftest import PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD, _fresh_access_token

    api = f"{base_url.rstrip('/')}/api/v1"
    if not seed.get("access_token"):
        return api, None
    admin_seed = {
        "access_token": seed["access_token"],
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASSWORD,
    }
    return api, _fresh_access_token(admin_seed, base_url)


def enter_phase_photoperiods(
    base_url: str, seed: dict, species_key: str, phase_names: set[str]
) -> None:
    """Save the requirement profile of each named growth phase of *species_key* unchanged, as the profile editor does.

    A person who saves the profile states its light hours: the server stores them as ``sourced`` (#2857), the only
    origin the tent hint judges. The values stay as the catalogue holds them. Loud when a phase is missing or the
    answer does not carry ``photoperiod_source = sourced``.
    """
    api, token = _platform_admin_api(base_url, seed)
    status, lifecycle = _api_request(f"{api}/species/{species_key}/lifecycle", "GET", token)
    _require(status, lifecycle, (200,), f"GET /species/{species_key}/lifecycle")
    status, phases = _api_request(
        f"{api}/growth-phases?lifecycle_key={lifecycle['key']}", "GET", token
    )
    _require(status, phases, (200,), f"GET /growth-phases?lifecycle_key={lifecycle['key']}")
    keys = {
        str(phase["name"]): str(phase["key"])
        for phase in phases
        if str(phase["name"]) in phase_names
    }
    if set(keys) != phase_names:
        raise AssertionError(
            f"Self-provisioning failed: growth phases {sorted(phase_names - set(keys))} not found"
        )
    for name, phase_key in sorted(keys.items()):
        status, profile = _api_request(f"{api}/profiles/requirements/{phase_key}", "GET", token)
        _require(status, profile, (200,), f"GET /profiles/requirements/{phase_key}")
        body = {
            field_name: profile[field_name]
            for field_name in _REQUIREMENT_PROFILE_BODY_FIELDS
            if field_name in profile
        }
        status, saved = _api_request(
            f"{api}/profiles/requirements/{profile['key']}", "PUT", token, body
        )
        _require(status, saved, (200,), f"PUT /profiles/requirements/{profile['key']}")
        if not isinstance(saved, dict) or saved.get("photoperiod_source") != "sourced":
            raise AssertionError(
                f"Self-provisioning failed: the {name!r} profile is not sourced: {saved!r}"
            )


def create_plant_in_phase(
    base_url: str,
    seed: dict,
    *,
    site_key: str,
    location_key: str,
    species_key: str,
    phase_key: str,
    name: str,
) -> str:
    """``POST /plant-instances``: a plant standing in *location_key* whose current phase is *phase_key*."""
    plant = _tenant_post(
        base_url,
        seed,
        "/plant-instances",
        {
            "instance_id": f"E2E-{unique_tag().upper()}",
            "species_key": species_key,
            "site_key": site_key,
            "location_key": location_key,
            "plant_name": name,
            "planted_on": utc_today().isoformat(),
            "current_phase_key": phase_key,
        },
        expected=(201,),
    )
    if plant.get("current_phase_key") != phase_key or plant.get("location_key") != location_key:
        raise AssertionError(
            f"Self-provisioning failed: plant {name!r} should stand in {location_key!r} in phase "
            f"{phase_key!r}: {plant!r}"
        )
    return plant["key"]


def object_tasks(base_url: str, seed: dict, object_key: str) -> list[dict]:
    """``GET /tasks`` of the garden object *object_key* (``entity_type = garden_object``), every status."""
    body = tenant_get(
        base_url,
        seed,
        f"/tasks?entity_type=garden_object&entity_key={object_key}&limit=100",
    )
    if not isinstance(body, list):
        raise AssertionError(f"the tasks of object {object_key!r} are not a list: {body!r}")
    return body


def plant_feeding_events(base_url: str, seed: dict, plant_key: str) -> list[dict]:
    """``GET /feeding-events/plant/{key}``: every feeding event that names the plant."""
    body = tenant_get(base_url, seed, f"/feeding-events/plant/{plant_key}")
    if not isinstance(body, list):
        raise AssertionError(f"the feeding events of {plant_key!r} are not a list: {body!r}")
    return body
