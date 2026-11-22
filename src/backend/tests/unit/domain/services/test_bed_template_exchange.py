"""REQ-053 WP 9.9 (#2749) - the pieces of the template exchange the routes cannot isolate (GP-FR-173, GP-API-071).

* the version window: the current ``schema_version`` and exactly one before it, even when the migration chain could
  reach further back (GP-API-071 "die aktuelle und eine Vorgängerversion");
* the nesting bound of the file (GP-FR-141 / SR-018: ten levels), walked without recursion;
* the proposed name after a 409;
* the export builds the file field by field: a field added to ``BedTemplate`` does not reach it.
"""

from __future__ import annotations

import typing

import pytest

from app.common.exceptions import PlanError
from app.domain.models import bed_template_exchange
from app.domain.models.bed_template import BedTemplate
from app.domain.models.bed_template_exchange import MAX_NESTING, SCHEMA_VERSION, BedTemplateExchange
from app.domain.services import bed_template_service
from app.domain.services.bed_template_service import _migrated, _nesting_depth, name_candidates


def _lift(target: str):
    def step(document: dict) -> dict:
        return {**document, "schema_version": target}

    return step


class TestTheVersionWindow:
    def test_the_models_literal_is_the_current_version(self) -> None:
        """The model validates after migration: its literal must be :data:`SCHEMA_VERSION`, nothing else."""
        annotation = BedTemplateExchange.model_fields["schema_version"].annotation
        assert typing.get_args(annotation) == (SCHEMA_VERSION,)

    def test_the_current_version_passes_unchanged(self) -> None:
        document = {"schema_version": SCHEMA_VERSION, "name": "Bed"}

        assert _migrated(document) == (document, False)

    def test_one_predecessor_is_lifted_and_an_older_one_refused(self, monkeypatch) -> None:
        """With "3" current and steps from "1" and "2" registered, "2" is read and "1" is not - although the chain
        reaches it. Falsified by widening ``KEPT_PREDECESSORS`` to 2: "1" is then accepted."""
        monkeypatch.setattr(bed_template_service, "SCHEMA_VERSION", "3")
        monkeypatch.setattr(bed_template_service, "MIGRATORS", {"1": _lift("2"), "2": _lift("3")})

        lifted, migrated = _migrated({"schema_version": "2", "name": "Bed"})
        assert (lifted["schema_version"], migrated) == ("3", True)

        with pytest.raises(PlanError) as refused:
            _migrated({"schema_version": "1", "name": "Bed"})
        assert refused.value.details[0]["code"] == "bed_template.schema_version_unsupported"

    def test_a_failing_step_is_a_422_not_a_500(self, monkeypatch) -> None:
        def broken(document: dict) -> dict:
            raise KeyError("geometry")

        monkeypatch.setattr(bed_template_service, "SCHEMA_VERSION", "2")
        monkeypatch.setattr(bed_template_service, "MIGRATORS", {"1": broken})

        with pytest.raises(PlanError) as refused:
            _migrated({"schema_version": "1"})
        assert (refused.value.status_code, refused.value.details[0]["code"]) == (
            422,
            "bed_template.schema_version_unsupported",
        )

    def test_no_step_is_registered_while_one_is_the_only_version(self) -> None:
        assert (SCHEMA_VERSION, dict(bed_template_exchange.MIGRATORS)) == ("1", {})


class TestTheNesting:
    @pytest.mark.parametrize(("value", "depth"), [(1, 0), ({}, 1), ([[1]], 2), ({"a": [{"b": []}]}, 4)])
    def test_the_depth_is_counted_per_container(self, value, depth: int) -> None:
        assert _nesting_depth(value) == depth

    def test_a_deep_value_stops_the_walk_past_the_bound(self) -> None:
        deep: object = []
        for _ in range(50_000):
            deep = [deep]

        assert _nesting_depth(deep) == MAX_NESTING + 1


class TestTheProposedName:
    def test_the_candidates_count_on_from_two(self) -> None:
        assert name_candidates("Herb bed", count=3) == ["Herb bed", "Herb bed (2)", "Herb bed (3)", "Herb bed (4)"]

    def test_a_number_of_the_name_is_replaced_not_stacked(self) -> None:
        assert name_candidates("Herb bed (2)", count=2) == ["Herb bed (2)", "Herb bed (3)"]

    def test_a_long_name_is_shortened_to_stay_a_valid_name(self) -> None:
        candidates = name_candidates("x" * 200, count=150)

        assert all(len(candidate) <= 200 for candidate in candidates)
        assert candidates[-1].endswith(" (151)")


class TestTheExportFile:
    def test_a_field_of_the_stored_template_beyond_the_file_does_not_reach_it(self) -> None:
        template = BedTemplate(
            _key="tpl",
            tenant_key="ten",
            created_by="u_author",
            name="Bed",
            location_type_key="bed",
            default_geometry={"kind": "circle", "origin": [0, 0], "radius_m": 0.5},
            recurring_task_templates=["task_1"],
        )

        dumped = BedTemplateExchange.of(template).model_dump()

        assert set(dumped) == {
            "format",
            "schema_version",
            "name",
            "location_type_key",
            "default_geometry",
            "height_m",
            "default_layout",
            "soil_profile_defaults",
        }
