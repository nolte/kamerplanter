"""The run-type rule refuses as a caller error, and ``preview_run`` writes nothing (#2775).

``PlantingRunEngine.validate_run_type_constraints`` raises a bare ``ValueError``. No REST
handler maps one, so ``POST /planting-runs`` with a monoculture of two entries answered 500
and the MCP tool would have answered ``internal.contract_mismatch``. The service types it as
a ``ValidationError`` (422) on every path that applies the rule.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.api.v1.planting_runs.schemas import PlantingRunCreate
from app.common.enums import PlantingRunType
from app.common.exceptions import ValidationError
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.planting_run_service import PlantingRunService
from tests.unit.domain.services.test_planting_run_location_ownership import OWN, FakeRunRepo, FakeSiteRepo


def _service(repo: FakeRunRepo) -> PlantingRunService:
    return PlantingRunService(
        repo,
        MagicMock(),
        engine=PlantingRunEngine(),
        site_repo=FakeSiteRepo(),
        species_resolver=lambda key, *, tenant_key: None,
    )


def _run() -> PlantingRun:
    return PlantingRun(name="Beet A", run_type=PlantingRunType.MONOCULTURE, location_key="loc_own")


def _entry(prefix: str = "AB", quantity: int = 3) -> PlantingRunEntry:
    return PlantingRunEntry(species_key="sp_own", quantity=quantity, id_prefix=prefix)


def test_a_monoculture_with_two_entries_is_a_validation_error_and_nothing_is_stored():
    repo = FakeRunRepo()

    with pytest.raises(ValidationError, match="exactly one entry"):
        _service(repo).create_run(_run(), [_entry("AB"), _entry("CD")], tenant_key=OWN)

    assert repo.store == {} and repo.entries == []


def test_preview_run_reports_what_create_run_would_store_and_writes_nothing():
    repo = FakeRunRepo()

    run, entries, layout_slots = _service(repo).preview_run(_run(), [_entry(quantity=6)], tenant_key=OWN)

    assert (run.tenant_key, run.planned_quantity, len(entries), layout_slots) == (OWN, 6, 1, 0)
    assert repo.store == {} and repo.entries == []


def test_preview_run_refuses_what_create_run_refuses():
    repo = FakeRunRepo()

    with pytest.raises(ValidationError):
        _service(repo).preview_run(_run(), [_entry("AB"), _entry("CD")], tenant_key=OWN)

    assert repo.store == {}


def test_the_rest_body_refuses_a_clone_run_without_its_mother_plant():
    """``PlantingRun`` refuses it on construction inside the route (500); the body refuses it first (422)."""
    with pytest.raises(PydanticValidationError, match="source_plant_key"):
        PlantingRunCreate(name="Klone", run_type="clone")

    assert PlantingRunCreate(name="Klone", run_type="clone", source_plant_key="plant_1").run_type == "clone"
