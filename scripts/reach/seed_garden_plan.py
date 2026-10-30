#!/usr/bin/env python3
"""Build one small garden plan through the API, for the plan read-model reach probe (#2448).

The environment half of the ``endpoint-sites-plan-read-model-answers`` probe
(REQ-053 GP-API-001, ``GET /api/v1/t/{slug}/sites/{key}/plan``). It makes the
data the read model has to return exist, along the routes a gardener's client
uses — never by writing documents directly, so the plan the probe reads is one
the production write paths produced:

1. a fresh account is registered (``POST /api/v1/auth/register``) and signs in;
   its personal tenant, of which it is the lead, is the plan's tenant;
2. an outdoor site (``POST /sites``), its garden boundary (``PUT
   /sites/{key}/plan/boundary``), one bed and one compost heap in one plan batch
   (``POST /sites/{key}/plan/batch``);
3. three plants of a seeded global species in the bed, with their slots, in one
   field-mode quick planting (``POST /locations/{key}/quick-planting``);
4. one open task on the bed (``POST /tasks``, ``entity_type = location``);
5. one irrigation zone holding the bed (``POST /sites/{key}/irrigation-zones``,
   ``PUT /irrigation-zones/{key}/locations``).

Every step that is not answered as documented stops the build with an error:
the runner then reports the probe *not probed*, never *not reached*. The build
says nothing about the read model; ``observe_garden_plan.py`` reads it.

The record — the account's credentials, the tenant slug and the site key — goes
to ``.reach/subjects/garden-plan.json`` (``.reach/`` is ignored by git; the
password is a throw-away one of the throw-away stack). ``stack.py down`` removes
it with the rest of the run state.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import ReachError, http_json, log, reach_dir, read_stack  # noqa: E402

#: The record ``observe_garden_plan.py`` reads, under ``.reach/subjects/``.
RECORD_NAME = "garden-plan"
#: Names the build gives the plan's objects; the probe's expected set repeats them.
SITE_NAME = "reach-garden"
BED_NAME = "reach-bed"
COMPOST_LABEL = "reach-compost"
TASK_NAME = "reach-weeding"
ZONE_NAME = "reach-zone"
#: The global species the plants are of. Tomato carries a seeded lifecycle, so the
#: quick planting starts each plant in a phase (GP-API-001 lists ``phase_key``).
SPECIES_SCIENTIFIC_NAME = "Solanum lycopersicum"
#: How many plants the bed gets, and their spacing in and between rows; three fit the 2.0 x 1.0 m bed at
#: 40 cm with the default margins, so each plant gets its own slot (pinned by the unit test).
PLANT_COUNT = 3
SPACING_CM = 40
#: Page size of the species lookup; the global catalogue holds a few hundred species.
SPECIES_PAGE = 1000


def record_file() -> Path:
    return reach_dir() / "subjects" / f"{RECORD_NAME}.json"


def read_record() -> dict[str, Any]:
    path = record_file()
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:garden-plan` first")
    return json.loads(path.read_text(encoding="utf-8"))


# ── Request bodies (pure; pinned against the API's own models by the unit test) ──


def _rect(origin: tuple[float, float], width_m: float, length_m: float) -> dict[str, Any]:
    return {"kind": "rect", "origin": list(origin), "width_m": width_m, "length_m": length_m, "rotation_deg": 0}


def site_body() -> dict[str, Any]:
    return {"name": SITE_NAME, "type": "outdoor"}


def boundary_body() -> dict[str, Any]:
    """A 10 x 10 m garden, north up (GP-API-002)."""
    return {"boundary": _rect((0.0, 0.0), 10.0, 10.0), "north_angle_deg": 0}


def batch_body(expected_revision: int) -> dict[str, Any]:
    """One bed and one compost heap inside the boundary, in one batch (GP-API-003)."""
    return {
        "expected_revision": expected_revision,
        "operations": [
            {
                "op": "create_location",
                "temp_key": "bed",
                "data": {"name": BED_NAME, "location_type_key": "bed", "geometry": _rect((1.0, 1.0), 2.0, 1.0)},
            },
            {
                "op": "create_garden_object",
                "temp_key": "compost",
                "data": {"object_type": "compost", "label": COMPOST_LABEL, "geometry": _rect((7.0, 7.0), 1.0, 1.0)},
            },
        ],
    }


def quick_planting_body(species_key: str) -> dict[str, Any]:
    """Three plants on a grid, each on its own slot (GP-API-017)."""
    return {
        "species_key": species_key,
        "quantity": PLANT_COUNT,
        "layout_strategy": "grid",
        "spacing_cm": SPACING_CM,
        "row_spacing_cm": SPACING_CM,
    }


def task_body(bed_key: str) -> dict[str, Any]:
    """One open task bound to the bed (GP-FR-080); the plan counts it (GP-API-001)."""
    return {"name": TASK_NAME, "category": "maintenance", "entity_type": "location", "entity_key": bed_key}


def zone_body() -> dict[str, Any]:
    return {"name": ZONE_NAME, "irrigation_type": "drip"}


def zone_locations_body(bed_key: str) -> dict[str, Any]:
    return {"location_keys": [bed_key]}


def species_key_of(listing: object, scientific_name: str = SPECIES_SCIENTIFIC_NAME) -> str:
    """The key of the species called *scientific_name* in a ``GET /species`` page."""
    items = listing.get("items") if isinstance(listing, dict) else None
    if not isinstance(items, list):
        raise ReachError(f"GET /species answered no item list: {str(listing)[:200]}")
    for item in items:
        if isinstance(item, dict) and item.get("scientific_name") == scientific_name and item.get("key"):
            return str(item["key"])
    raise ReachError(f"the global catalogue holds no species {scientific_name!r}")


def personal_slug_of(listing: object) -> str:
    """The slug of the only tenant a fresh account belongs to (its personal tenant)."""
    rows = listing if isinstance(listing, list) else []
    slugs = [str(row["slug"]) for row in rows if isinstance(row, dict) and row.get("slug")]
    if len(slugs) != 1:
        raise ReachError(f"a fresh account should belong to exactly one tenant, GET /tenants listed {slugs}")
    return slugs[0]


# ── The build ────────────────────────────────────────────────────────────────


def _expect(answer: tuple[int, Any], status: int, what: str) -> Any:
    code, body = answer
    if code != status:
        raise ReachError(f"{what} answered {code} (expected {status}): {str(body)[:500]}")
    return body


def _key(body: object, what: str) -> str:
    if not isinstance(body, dict) or not body.get("key"):
        raise ReachError(f"{what} answered no key: {str(body)[:300]}")
    return str(body["key"])


def sign_in(api: str, email: str, password: str) -> dict[str, str]:
    body = _expect(
        http_json(
            "POST",
            f"{api}/api/v1/auth/login",
            body={"email": email, "password": password, "refresh_token_in_body": True},
        ),
        200,
        "POST /auth/login",
    )
    if not isinstance(body, dict) or "access_token" not in body:
        raise ReachError(f"POST /auth/login answered no access token: {str(body)[:300]}")
    return {"Authorization": f"Bearer {body['access_token']}"}


def build(api: str) -> dict[str, Any]:
    email = f"reach-gardener-{secrets.token_hex(4)}@example.com"
    password = secrets.token_urlsafe(18)
    _expect(
        http_json(
            "POST",
            f"{api}/api/v1/auth/register",
            body={"email": email, "password": password, "display_name": "Reach Gardener"},
        ),
        201,
        "POST /auth/register",
    )
    headers = sign_in(api, email, password)
    slug = personal_slug_of(_expect(http_json("GET", f"{api}/api/v1/tenants", headers=headers), 200, "GET /tenants"))
    base = f"{api}/api/v1/t/{slug}"

    def call(method: str, path: str, status: int, body: object | None = None) -> Any:
        return _expect(http_json(method, f"{base}{path}", body=body, headers=headers), status, f"{method} {path}")

    site_key = _key(call("POST", "/sites", 201, site_body()), "POST /sites")
    boundary = call("PUT", f"/sites/{site_key}/plan/boundary", 200, boundary_body())
    revision = boundary.get("plan_revision") if isinstance(boundary, dict) else None
    if not isinstance(revision, int):
        raise ReachError(f"PUT /plan/boundary answered no plan_revision: {str(boundary)[:300]}")
    batch = call("POST", f"/sites/{site_key}/plan/batch", 200, batch_body(revision))
    key_map = batch.get("key_map") if isinstance(batch, dict) else None
    if not isinstance(key_map, dict) or not key_map.get("bed") or not key_map.get("compost"):
        raise ReachError(f"POST /plan/batch answered no key for the bed and the compost heap: {str(batch)[:300]}")
    bed_key = str(key_map["bed"])

    species = _expect(
        http_json("GET", f"{api}/api/v1/species?limit={SPECIES_PAGE}", headers=headers), 200, "GET /species"
    )
    planted = call("POST", f"/locations/{bed_key}/quick-planting", 201, quick_planting_body(species_key_of(species)))
    if not isinstance(planted, dict) or len(planted.get("plant_keys") or []) != PLANT_COUNT:
        raise ReachError(f"POST /quick-planting did not plant {PLANT_COUNT}: {str(planted)[:300]}")
    call("POST", "/tasks", 201, task_body(bed_key))
    zone_key = _key(call("POST", f"/sites/{site_key}/irrigation-zones", 201, zone_body()), "POST /irrigation-zones")
    call("PUT", f"/irrigation-zones/{zone_key}/locations", 200, zone_locations_body(bed_key))

    return {"email": email, "password": password, "tenant_slug": slug, "site_key": site_key}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    try:
        record = build(read_stack()["api_url"])
    except ReachError as exc:
        print(f"reach garden plan: {exc}", file=sys.stderr)
        return 1
    path = record_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(f"built a garden plan on site {record['site_key']!r} in tenant {record['tenant_slug']!r} -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
