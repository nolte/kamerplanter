"""Every field the frontend's ``Species`` type reads is a field ``SpeciesResponse`` serves.

The defect class: a species field sits on the domain model and in the seeds, the client type declares it and a
component reads it, but ``SpeciesResponse`` does not list it - ``to_response`` drops it silently and the feature
built on it is inert. Seen three times: ``light_requirement``/``shade_tolerance``/``row_spacing_cm`` (WP 3.9,
#2399), ``waterlogging_tolerance`` (GP-FR-161 hint never shown) and ``toxicity`` (REQ-001 warning badge never
shown since #465), the last two found by the REQ-053 wave-8 E2E run (#2674).

The guard enumerates the class, not the sites: it reads the ``export interface Species`` block of
``src/frontend/src/api/types.ts`` and requires each declared key in ``SpeciesResponse.model_fields``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.api.v1.species.schemas import SpeciesResponse
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_TYPES = _REPO_ROOT / "src" / "frontend" / "src" / "api" / "types.ts"
_FIELD = re.compile(r"^  (\w+)\??:")


def _client_species_keys() -> list[str]:
    lines = _TYPES.read_text(encoding="utf-8").splitlines()
    start = lines.index("export interface Species {")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("}"))
    return [match.group(1) for line in lines[start + 1 : end] if (match := _FIELD.match(line))]


def test_the_client_type_is_read_from_the_real_interface() -> None:
    keys = _client_species_keys()

    # Falsifies a reader that silently finds nothing (wrong path, renamed interface, changed indentation).
    assert len(keys) > 40, keys
    assert {"scientific_name", "light_requirement", "toxicity"} <= set(keys)


def test_every_client_species_field_is_served_by_the_response() -> None:
    missing = sorted(set(_client_species_keys()) - set(SpeciesResponse.model_fields))

    assert missing == [], (
        f"src/frontend/src/api/types.ts `Species` declares {missing}, but SpeciesResponse does not serve them, "
        "so the client always reads undefined. Add them to app/api/v1/species/schemas.py SpeciesResponse "
        "(or drop them from the client type if nothing reads them)."
    )
