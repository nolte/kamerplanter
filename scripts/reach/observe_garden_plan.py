#!/usr/bin/env python3
"""Read the built garden plan through ``GET /sites/{key}/plan`` and print what it holds, one fact per line (#2448).

Observation step of the ``endpoint-sites-plan-read-model-answers`` reach probe
(REQ-053 GP-API-001: the whole plan of a site — site plan, locations with
geometry, garden objects, slots, plant short info ``{key, instance_id,
species_key, phase_key, slot_key}``, task counters per location, zones — in one
request). ``seed_garden_plan.py`` built the plan along the write routes; this
step signs in as the same account and asks the read model, with its default
``include`` (all parts), what it answers. It prints the facts of the response
body, never a verdict:

* ``plan/boundary=<kind>`` — the site plan's boundary;
* ``location/<name>/geometry=<kind>`` — per location;
* ``garden-object/<type>/<label>/geometry=<kind>`` — per garden object;
* ``slots/<location name>=<n>`` — slots carrying a plan geometry, per location;
* ``plants/<location name>=<n>`` — plants per location (through their slot);
* ``plant-field/<field>=<n>`` — for each field of the declared short info, how
  many plants carry a non-empty value;
* ``open-tasks/<location name>=<n>`` — the location's open-task counter, when it
  is not zero;
* ``zone/<name>=<location names>`` — per zone, the locations it holds.

A response other than 200 is printed as ``http-status=<code>``, and a 200 whose
body holds none of these parts as ``plan/empty``: the endpoint under audit
answered, and what it answered is the observation — never silence, which the
runner would read as *not probed*. A failed sign-in
is the environment's failure and exits 1 (the runner reports *not probed*).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import ReachError, http_json, read_stack  # noqa: E402
from seed_garden_plan import read_record, sign_in  # noqa: E402

#: The plant short info GP-API-001 declares.
PLANT_FIELDS = ("key", "instance_id", "species_key", "phase_key", "slot_key")


def _rows(body: dict[str, Any], part: str) -> list[dict[str, Any]]:
    rows = body.get(part)
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _kind(geometry: object) -> str:
    return str(geometry.get("kind")) if isinstance(geometry, dict) and geometry.get("kind") else "none"


def plan_facts(body: object) -> list[str]:
    """The facts of one ``GET /plan`` answer, sorted and without duplicates."""
    if not isinstance(body, dict):
        return []
    facts: set[str] = set()
    plan = body.get("plan")
    if isinstance(plan, dict) and plan.get("boundary") is not None:
        facts.add(f"plan/boundary={_kind(plan['boundary'])}")

    names: dict[str, str] = {}
    for location in _rows(body, "locations"):
        name = str(location.get("name") or location.get("key") or "?")
        names[str(location.get("key"))] = name
        facts.add(f"location/{name}/geometry={_kind(location.get('geometry'))}")
        open_tasks = location.get("open_task_count")
        if isinstance(open_tasks, int) and open_tasks:
            facts.add(f"open-tasks/{name}={open_tasks}")

    for obj in _rows(body, "garden_objects"):
        label = obj.get("label") or obj.get("key") or "?"
        facts.add(f"garden-object/{obj.get('object_type')}/{label}/geometry={_kind(obj.get('geometry'))}")

    slot_location: dict[str, str] = {}
    slots_per_location: Counter[str] = Counter()
    for slot in _rows(body, "slots"):
        location = names.get(str(slot.get("location_key")), str(slot.get("location_key")))
        slot_location[str(slot.get("key"))] = location
        if slot.get("plan_geometry") is not None:
            slots_per_location[location] += 1
    facts.update(f"slots/{location}={count}" for location, count in slots_per_location.items())

    plants = _rows(body, "plants")
    plants_per_location: Counter[str] = Counter()
    for plant in plants:
        location_key = plant.get("location_key")
        location = (
            slot_location.get(str(plant.get("slot_key")))
            if plant.get("slot_key")
            else names.get(str(location_key), str(location_key))
        )
        plants_per_location[location or "?"] += 1
    facts.update(f"plants/{location}={count}" for location, count in plants_per_location.items())
    for field in PLANT_FIELDS:
        carried = sum(1 for plant in plants if plant.get(field) not in (None, ""))
        if plants:
            facts.add(f"plant-field/{field}={carried}")

    for zone in _rows(body, "zones"):
        members = sorted(names.get(str(key), str(key)) for key in zone.get("location_keys") or [])
        facts.add(f"zone/{zone.get('name')}={','.join(members)}")
    return sorted(facts)


def observe() -> list[str]:
    stack = read_stack()
    record = read_record()
    api = stack["api_url"]
    headers = sign_in(api, record["email"], record["password"])
    status, body = http_json(
        "GET", f"{api}/api/v1/t/{record['tenant_slug']}/sites/{record['site_key']}/plan", headers=headers
    )
    if status != 200:
        return [f"http-status={status}"]
    return plan_facts(body) or ["plan/empty"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    try:
        lines = observe()
    except ReachError as exc:
        print(f"observe garden plan: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
