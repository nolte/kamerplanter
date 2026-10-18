"""REQ-053 WP 3.1 (GP-FR-060) — the layout fields of a planting-run entry survive the service paths.

The fields are plain optional data on the entry; what can go wrong is a path that drops them: the PATCH
merge (``ENTRY_UPDATABLE_FIELDS``), an explicit ``null`` that must clear one, a merged value outside its
range, and the clone of a run's configuration.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import LayoutStrategy, RowDirection
from app.domain.models.planting_run import PlantingRunEntry
from tests.unit.domain.services.test_planting_run_entry_species_scope import OWN, _entry, _Repo, _run, _service


def _layout_entry() -> PlantingRunEntry:
    return PlantingRunEntry(
        species_key="sp_own",
        quantity=4,
        id_prefix="TOM",
        spacing_cm=60,
        row_spacing_cm=80,
        layout_strategy=LayoutStrategy.ROWS,
        row_direction=RowDirection.ALONG_LENGTH,
        edge_margin_along_cm=30,
        edge_margin_across_cm=40,
        row_assignment=[0, 2],
    )


def test_a_patch_applies_the_layout_fields_and_keeps_the_rest() -> None:
    repo = _Repo()
    service = _service(repo)
    run = service.create_run(_run(), [_layout_entry()], tenant_key=OWN)

    updated = service.update_entry(
        run.key,
        "e1",
        {"row_spacing_cm": 100, "layout_strategy": "triangular", "depth_cm": 5, "depth_kind": "sowing"},
        tenant_key=OWN,
    )

    assert (updated.row_spacing_cm, updated.layout_strategy, updated.depth_cm) == (
        100,
        LayoutStrategy.TRIANGULAR,
        5,
    )
    assert (updated.spacing_cm, updated.row_assignment, updated.edge_margin_along_cm) == (60, [0, 2], 30)


def test_an_explicit_null_clears_a_layout_field() -> None:
    repo = _Repo()
    service = _service(repo)
    run = service.create_run(_run(), [_layout_entry()], tenant_key=OWN)

    updated = service.update_entry(
        run.key, "e1", {"row_assignment": None, "edge_margin_along_cm": None}, tenant_key=OWN
    )

    assert (updated.row_assignment, updated.edge_margin_along_cm, updated.row_spacing_cm) == (None, None, 80)


@pytest.mark.parametrize("patch", [{"row_spacing_cm": 4}, {"spacing_cm": 1600}, {"row_assignment": [1, 1]}])
def test_a_merged_value_outside_its_range_is_refused(patch: dict) -> None:
    repo = _Repo()
    service = _service(repo)
    run = service.create_run(_run(), [_layout_entry()], tenant_key=OWN)

    with pytest.raises(PydanticValidationError):
        service.update_entry(run.key, "e1", patch, tenant_key=OWN)


def test_a_plain_entry_stays_plain() -> None:
    repo = _Repo()
    service = _service(repo)
    run = service.create_run(_run(), [_entry("sp_own")], tenant_key=OWN)

    updated = service.update_entry(run.key, "e1", {"quantity": 2}, tenant_key=OWN)

    assert updated.layout_strategy is None and updated.row_spacing_cm is None
