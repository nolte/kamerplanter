"""Seed Kamerplanter resources for the Nuclei OpenAPI surface scan.

Nuclei's OpenAPI input mode walks every path in the spec and tries to
build a concrete URL. Path parameters with no resolved value cause
nuclei to either skip the request (with ``-skip-format-validation``) or
abort entirely (without it). The Kamerplanter API places nearly every
business endpoint under ``/api/v1/t/{tenant_slug}/...`` and adds a
second layer of resource keys (``{species_key}``, ``{location_key}``,
``{run_key}`` etc.), so the unresolved set is large.

This script logs in as the seeded demo user, ensures one resource of
each commonly referenced kind exists in the running stack, and writes a
``required_openapi_params.yaml`` file that nuclei consumes to substitute
those keys.

It targets the public REST API only; no backend Python module is
imported, so the script is safe to run from any CI runner that can reach
the stack.

Spec: spec/nfr/NFR-014_Nuclei-Security-Scanning.md §4.3
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib import error, request
from urllib.parse import urljoin

BASE = os.environ.get("KP_API_BASE", "http://127.0.0.1:8000")
# Fixture user is created on demand via the public /auth/register
# endpoint. We do not rely on `seed_auth.py` because it is a standalone
# CLI helper, not part of the FastAPI lifespan, so the demo user does
# not exist after a vanilla `docker compose up`.
EMAIL = os.environ.get("KP_FIXTURE_EMAIL", "nuclei-fixture@kamerplanter.example")
PASSWORD = os.environ.get("KP_FIXTURE_PASSWORD", "nuclei-fixture-pwd-2026")
DISPLAY_NAME = os.environ.get("KP_FIXTURE_DISPLAY_NAME", "Nuclei Fixture")
OUT_PARAMS = Path(os.environ.get("KP_FIXTURES_PARAMS_OUT", "required_openapi_params.yaml"))
OUT_JSON = Path(os.environ.get("KP_FIXTURES_JSON_OUT", "nuclei-openapi-fixtures.json"))


def call(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict | list:
    url = urljoin(BASE, path)
    data = json.dumps(body).encode() if body is not None else None
    headers: dict[str, str] = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=15) as resp:
            payload = resp.read()
            return json.loads(payload) if payload else {}
    except error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        print(f"::error::{method} {path} -> HTTP {exc.code}: {body_text}", file=sys.stderr)
        raise


def first_key(items: list[dict]) -> str | None:
    if not items:
        return None
    return items[0].get("_key") or items[0].get("key")


def register_or_login() -> str:
    """Idempotent: register the fixture user if it does not exist, then log in."""
    try:
        call(
            "POST",
            "/api/v1/auth/register",
            body={"email": EMAIL, "password": PASSWORD, "display_name": DISPLAY_NAME},
        )
        print(f"register: created {EMAIL}")
    except error.HTTPError as exc:
        if exc.code in (400, 409):
            print(f"register: {EMAIL} already exists (HTTP {exc.code}) — continuing")
        else:
            raise

    tokens = call("POST", "/api/v1/auth/login", body={"email": EMAIL, "password": PASSWORD})
    assert isinstance(tokens, dict)
    return tokens["access_token"]


def main() -> int:
    print(f"target: {BASE}")

    token = register_or_login()
    print("login: ok")

    # 2. Tenant slug — first non-platform membership the demo user has.
    tenants = call("GET", "/api/v1/tenants/", token=token)
    assert isinstance(tenants, list)
    candidates = [t for t in tenants if not t.get("is_platform") and t.get("slug")]
    if not candidates:
        print("::error::No non-platform tenant found for demo user", file=sys.stderr)
        return 1
    tenant_slug = candidates[0]["slug"]
    print(f"tenant_slug: {tenant_slug}")

    # 3. Species — seeded; take the first.
    species_list = call("GET", "/api/v1/species/", token=token)
    items = species_list["items"] if isinstance(species_list, dict) else species_list
    species_key = first_key(items)
    print(f"species_key: {species_key}")

    # 4. Cultivar — for that species.
    cultivar_key: str | None = None
    if species_key:
        cultivars = call("GET", f"/api/v1/cultivars?species_key={species_key}", token=token)
        cultivar_key = first_key(cultivars if isinstance(cultivars, list) else [])
    print(f"cultivar_key: {cultivar_key}")

    # 5. Location-Type — system-seeded.
    loc_types = call("GET", "/api/v1/location-types", token=token)
    location_type_key = first_key(loc_types if isinstance(loc_types, list) else [])
    print(f"location_type_key: {location_type_key}")

    # 6. Site — tenant-scoped. Reuse if exists, else create.
    sites = call("GET", f"/api/v1/t/{tenant_slug}/sites", token=token)
    site_key = first_key(sites if isinstance(sites, list) else [])
    if not site_key:
        created = call(
            "POST",
            f"/api/v1/t/{tenant_slug}/sites",
            token=token,
            body={"name": "Nuclei Fixture Site"},
        )
        assert isinstance(created, dict)
        site_key = created.get("_key") or created.get("key")
    print(f"site_key: {site_key}")

    # 7. Location — tenant-scoped, depends on site + location-type.
    locations = call("GET", f"/api/v1/t/{tenant_slug}/locations", token=token)
    location_key = first_key(locations if isinstance(locations, list) else [])
    if not location_key:
        created = call(
            "POST",
            f"/api/v1/t/{tenant_slug}/locations",
            token=token,
            body={
                "name": "Nuclei Fixture Location",
                "site_key": site_key,
                "location_type_key": location_type_key or "",
                "area_m2": 1.0,
            },
        )
        assert isinstance(created, dict)
        location_key = created.get("_key") or created.get("key")
    print(f"location_key: {location_key}")

    # 8. PlantingRun — tenant-scoped.
    runs = call("GET", f"/api/v1/t/{tenant_slug}/runs", token=token)
    run_key = first_key(runs if isinstance(runs, list) else [])
    if not run_key:
        created = call(
            "POST",
            f"/api/v1/t/{tenant_slug}/runs",
            token=token,
            body={
                "name": "Nuclei Fixture Run",
                "run_type": "veg",
                "location_key": location_key,
            },
        )
        assert isinstance(created, dict)
        run_key = created.get("_key") or created.get("key")
    print(f"run_key: {run_key}")

    fixtures = {
        "tenant_slug": tenant_slug,
        "species_key": species_key,
        "cultivar_key": cultivar_key,
        "location_type_key": location_type_key,
        "site_key": site_key,
        "location_key": location_key,
        "run_key": run_key,
        # Convenience aliases — many endpoints use {key} as the path param
        # name with the same semantic as one of the above. nuclei resolves
        # by exact path-param name, so we expose every alias the API uses.
        "key": run_key,
        "tenant_key": tenant_slug,
    }

    OUT_JSON.write_text(json.dumps(fixtures, indent=2, default=str))

    # nuclei reads required_openapi_params as a YAML map of param-name to
    # concrete value. We hand-render the YAML to avoid pulling pyyaml in
    # for two dozen lines of output.
    yaml_lines = [
        f'{k}: "{v}"' for k, v in fixtures.items() if v is not None
    ]
    OUT_PARAMS.write_text("\n".join(yaml_lines) + "\n")

    print("\nfixtures:")
    print(json.dumps(fixtures, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
