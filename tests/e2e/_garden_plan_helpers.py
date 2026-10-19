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
(`test-pyramid-foundation` §"Arrangement-Treue", `test-falsifiability` T9):

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

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

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
    """A garden object to create (path, tree, ...)."""

    label: str
    object_type: str
    geometry: dict


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
        operations.append(
            {
                "op": "create_garden_object",
                "temp_key": f"obj{index}",
                "data": {
                    "object_type": obj.object_type,
                    "label": obj.label,
                    "geometry": obj.geometry,
                },
            }
        )
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


def tenant_get(base_url: str, seed: dict, path: str) -> object:
    """``GET`` a tenant-scoped *path* (``/locations/...``); loud on anything but 200."""
    api, token = _api(base_url, seed)
    status, body = _api_request(f"{api}{path}", "GET", token)
    _require(status, body, (200,), f"GET {path}")
    return body


def _tenant_post(base_url: str, seed: dict, path: str, data: dict, expected=(200, 201)) -> dict:
    api, token = _api(base_url, seed)
    status, body = _api_request(f"{api}{path}", "POST", token, data)
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
    from datetime import timedelta

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
