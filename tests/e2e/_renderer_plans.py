"""Self-provisioning of the large plans the renderer measurement draws (REQ-053 WP 9.6, D-01, GP-NFR-033/034).

Two plans, both arranged through the application's own API (`test-pyramid-foundation` §"Arrangement-Treue"):

* **"large"** - the plant-state worst case of the renderer benchmark (``renderer.benchmark.test.ts``,
  ``statedPlan``): 250 beds of 1.2 x 2 m on a 25 x 10 grid (2 m x 3 m pitch), 20 point slots per bed on a
  0.3 x 0.35 m grid, and a plant on every slot - 5 000 plants. That is the load the issue names ("250 Beete x 20
  Pflanzen"); it is larger than the §25.1 table row "groß" (150 beds, 2 000 plants) and equals its stress limit
  in plants (GP-NFR-073).
* **"synthetic 3 000"** - 30 beds of 3 x 3 m with 100 planted slots each (10 x 10 at 0.3 m), laid out so that the
  whole plan fits the desktop canvas at a zoom where every plant marker is drawn: 30 beds + 3 000 plants = 3 030
  visible objects (D-01's threshold). Garden objects cannot carry the count: beds and objects share the quota of
  500 per site (GP-NFR-017). On a 390 px phone the fit is far below the marker LOD: there the case shows beds and
  clusters, and the report says so.

HOW, AND WHY THIS PATH
----------------------
The structure goes in through **one** ``POST /sites/{key}/plan/import`` (``mode = replace``, GP-API-005): the
backup file is the server's own export of the freshly provisioned site (``GET /plan/export``), extended by the
beds and slots - the import validates it like any file a user restores (quotas GP-NFR-017, containment, slot
ids). The plan batch (GP-API-003) cannot carry it: it has no slot operation, and 500 operations per batch.
250 beds x 20 slots through ``POST /locations/{key}/slots/batch`` would be 250 more requests for nothing.

The plants go in the way the planting dialog puts them: per bed one planned run with a ``free`` entry of 20
(``POST /planting-runs``) and ``create-plants`` with ``assign_to_slots`` (GP-API-023), which puts the plants on
the bed's free slots. That is 500 requests for 250 beds (60 for the synthetic plan) - the expensive half of the arrangement (expected one
to three minutes on the E2E stack), run on a small thread pool (``E2E_RENDERER_SEED_WORKERS``, default 4). There
is no faster *supported* path: the import carries no plants (a backup holds structure, GP-FR-141), and the
benchmark's own fixture (``seed_large_garden`` in ``test_garden_plan_repository.py``) writes the collections
directly, which this suite does not do for state the API can produce.

Every refusal raises with the response body, and the arrangement is read back (``GET /plan``) and counted
before a test may measure on it: a plan that is not what it claims fails here, never as a frame time.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from ._garden_plan_helpers import (
    ProvisionedGarden,
    _api,
    _require,
    export_plan_json,
    provision_garden,
    rect,
    run_payload,
    species,
    unique_tag,
)
from ._journey_helpers import _api_request

#: The plan import may take a while for 5 000 slots; the default socket timeout of the helpers is 15 s.
IMPORT_TIMEOUT_S = 180
#: ``GET /plan`` of the large class (5 000 plants) is a large answer (GP-NFR-031).
READ_TIMEOUT_S = 60
SEED_WORKERS = int(os.environ.get("E2E_RENDERER_SEED_WORKERS", "4"))
TOMATO = "Solanum lycopersicum"


@dataclass(frozen=True)
class GridPlan:
    """Beds of one size on a regular grid, each with the same point slots (bed frame, metres)."""

    name: str
    columns: int
    rows: int
    bed_width_m: float
    bed_length_m: float
    pitch_x_m: float
    pitch_y_m: float
    slots: tuple[tuple[float, float], ...]
    planted: bool
    margin_m: float = 0.5
    #: A plant-free strip along the bed's right edge (x from ``bed_width_m - drag_strip_m``): the drag handle
    #: of the measurement, where the press hits the bed and no plant marker. ``0`` = press the bed's centre.
    drag_strip_m: float = 0.0

    @property
    def beds(self) -> int:
        return self.columns * self.rows

    @property
    def slot_count(self) -> int:
        return self.beds * len(self.slots)

    @property
    def plant_count(self) -> int:
        return self.slot_count if self.planted else 0

    def bed_origin(self, index: int) -> tuple[float, float]:
        return (
            round(self.margin_m + (index % self.columns) * self.pitch_x_m, 3),
            round(self.margin_m + (index // self.columns) * self.pitch_y_m, 3),
        )

    def boundary(self) -> dict:
        width = self.margin_m * 2 + (self.columns - 1) * self.pitch_x_m + self.bed_width_m
        length = self.margin_m * 2 + (self.rows - 1) * self.pitch_y_m + self.bed_length_m
        return rect(0, 0, round(width, 3), round(length, 3))

    def bed_name(self, index: int) -> str:
        return f"Beet {index + 1:03d}"


#: renderer.benchmark.test.ts ``statedPlan``: 250 x 20, 0.3 m across, 0.35 m along.
LARGE = GridPlan(
    name="large",
    columns=25,
    rows=10,
    bed_width_m=1.2,
    bed_length_m=2.0,
    pitch_x_m=2.0,
    pitch_y_m=3.0,
    slots=tuple(
        (round(0.15 + (k % 4) * 0.3, 3), round(0.2 + (k // 4) * 0.35, 3)) for k in range(20)
    ),
    planted=True,
)

#: 30 beds + 30 x 100 plants = 3 030 visible objects, 0.3 m apart on 3.3 x 3 m beds (the right 0.3 m strip is
#: plant-free, the drag handle) with 0.2 m gaps: the plan (21.8 x 16.8 m) is as dense as the marker LOD allows, so the desktop fit (~40 px/m on a 1080 px high window)
#: draws every plant on its own from a canvas width of ~800 px on (markers need >= 10 px, i.e. >= 33.4 px/m).
#: Planted, not empty: the first run (2026-11-08) showed an empty bed below that zoom draws nothing at all.
SYNTHETIC_3000 = GridPlan(
    name="synthetic_3000",
    columns=6,
    rows=5,
    bed_width_m=3.3,
    bed_length_m=3.0,
    pitch_x_m=3.5,
    pitch_y_m=3.2,
    slots=tuple(
        (round(0.15 + c * 0.3, 3), round(0.15 + r * 0.3, 3)) for r in range(10) for c in range(10)
    ),
    planted=True,
    drag_strip_m=0.3,
)


@dataclass(frozen=True)
class MeasuredPlan:
    """A provisioned plan and what the server holds for it (read back, counted)."""

    spec: GridPlan
    garden: ProvisionedGarden
    stored_beds: int
    stored_slots: int
    stored_plants: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "case": self.spec.name,
            "beds": self.stored_beds,
            "slots": self.stored_slots,
            "plants": self.stored_plants,
            "site_key": self.garden.site_key,
        }


def _import_document(base_url: str, seed: dict, site_key: str, spec: GridPlan) -> dict:
    """The server's own backup of the empty site, with the grid's beds and slots added."""
    document = export_plan_json(base_url, seed, site_key)
    tag = unique_tag().upper()
    locations: list[dict] = []
    slots: list[dict] = []
    for index in range(spec.beds):
        x, y = spec.bed_origin(index)
        bed_key = f"b{index}"
        locations.append(
            {
                "key": bed_key,
                "name": spec.bed_name(index),
                "location_type_key": "raised_bed",
                "geometry": rect(x, y, spec.bed_width_m, spec.bed_length_m),
                "area_m2": round(spec.bed_width_m * spec.bed_length_m, 4),
            }
        )
        for n, (sx, sy) in enumerate(spec.slots, start=1):
            slots.append(
                {
                    "key": f"{bed_key}s{n}",
                    # The model's format rule (upper case, LOCATION_POSITION) and unique per run.
                    "slot_id": f"R{tag}_{index:03d}_{n:02d}",
                    "location_key": bed_key,
                    "slot_role": "position",
                    "capacity_plants": 1,
                    "geometry": {"kind": "point", "origin": [float(sx), float(sy)]},
                    "sequence": n,
                }
            )
    document["locations"] = locations
    document["slots"] = slots
    document["garden_objects"] = []
    document["zones"] = []
    return document


def _import(base_url: str, seed: dict, garden: ProvisionedGarden, document: dict) -> dict:
    api, token = _api(base_url, seed)
    status, report = _api_request(
        f"{api}/sites/{garden.site_key}/plan/import",
        "POST",
        token,
        {
            "mode": "replace",
            "dry_run": False,
            "force": False,
            "confirm_site_name": garden.site_name,
            "target": "same_site",
            "document": document,
        },
        timeout=IMPORT_TIMEOUT_S,
    )
    _require(status, report, (200,), f"POST /sites/{garden.site_key}/plan/import (renderer plan)")
    if not report.get("applied"):
        raise AssertionError(
            f"Self-provisioning failed: the plan import was not applied: {report!r}"
        )
    return report


def _plant_bed(base_url: str, seed: dict, bed_key: str, species_key: str, quantity: int) -> int:
    """One planned run of *quantity* on *bed_key*, its plants put on the bed's free slots; the slots taken."""
    api, token = _api(base_url, seed)
    status, run = _api_request(
        f"{api}/planting-runs",
        "POST",
        token,
        run_payload(
            bed_key=bed_key,
            species_key=species_key,
            id_prefix="TOM",
            quantity=quantity,
            name=f"E2E-GP-render-{unique_tag()}",
            entry={"spacing_cm": 30.0, "layout_strategy": "free"},
        ),
    )
    _require(status, run, (201,), f"POST /planting-runs (bed {bed_key})")
    status, result = _api_request(
        f"{api}/planting-runs/{run['key']}/create-plants",
        "POST",
        token,
        {"assign_to_slots": True},
        timeout=60,
    )
    _require(status, result, (200, 201), f"POST /planting-runs/{run['key']}/create-plants")
    assigned = int(result.get("slots_assigned") or 0)
    if int(result.get("created_count") or 0) != quantity or assigned != quantity:
        raise AssertionError(
            f"Self-provisioning failed: bed {bed_key!r} should hold {quantity} plants on {quantity} slots, "
            f"create-plants answered {result!r}"
        )
    return assigned


def _read_plan(base_url: str, seed: dict, site_key: str) -> dict:
    api, token = _api(base_url, seed)
    status, body = _api_request(
        f"{api}/sites/{site_key}/plan", "GET", token, timeout=READ_TIMEOUT_S
    )
    _require(status, body, (200,), f"GET /sites/{site_key}/plan (renderer plan)")
    return body


def _count(items: Iterable[dict], predicate) -> int:
    return sum(1 for item in items if predicate(item))


def provision_grid_plan(base_url: str, seed: dict, spec: GridPlan) -> MeasuredPlan:
    """Create a site with *spec*'s plan through the API and return it once the server holds all of it."""
    garden = provision_garden(
        base_url, seed, purpose=f"render-{spec.name}", boundary=spec.boundary()
    )
    _import(base_url, seed, garden, _import_document(base_url, seed, garden.site_key, spec))

    plan = _read_plan(base_url, seed, garden.site_key)
    names = {spec.bed_name(index) for index in range(spec.beds)}
    for location in plan.get("locations") or []:
        if location.get("name") in names:
            garden.beds[location["name"]] = location["key"]
    if len(garden.beds) != spec.beds:
        raise AssertionError(
            f"Self-provisioning failed: the imported plan holds {len(garden.beds)} of the {spec.beds} beds"
        )

    if spec.planted:
        tomato = species(base_url, seed, TOMATO)
        # Warm the token cache once, so the worker threads do not log in concurrently (full mode).
        _api(base_url, seed)
        with ThreadPoolExecutor(max_workers=max(1, SEED_WORKERS)) as pool:
            taken = list(
                pool.map(
                    lambda key: _plant_bed(base_url, seed, key, tomato["key"], len(spec.slots)),
                    sorted(garden.beds.values()),
                )
            )
        if sum(taken) != spec.plant_count:
            raise AssertionError(
                f"Self-provisioning failed: {sum(taken)} of {spec.plant_count} plants stand on a slot"
            )
        plan = _read_plan(base_url, seed, garden.site_key)

    bed_keys = set(garden.beds.values())
    slots = [slot for slot in plan.get("slots") or [] if slot.get("location_key") in bed_keys]
    slot_keys = {slot.get("key") for slot in slots}
    plants = plan.get("plants") or []
    measured = MeasuredPlan(
        spec=spec,
        garden=garden,
        stored_beds=len(bed_keys),
        stored_slots=len(slots),
        stored_plants=_count(plants, lambda plant: plant.get("slot_key") in slot_keys),
    )
    if (measured.stored_slots, measured.stored_plants) != (spec.slot_count, spec.plant_count):
        raise AssertionError(
            f"Self-provisioning failed: the stored plan of {spec.name!r} holds {measured.stored_slots} slots "
            f"and {measured.stored_plants} plants on them, expected {spec.slot_count} and {spec.plant_count}"
        )
    return measured


__all__ = ["LARGE", "SYNTHETIC_3000", "GridPlan", "MeasuredPlan", "provision_grid_plan"]
