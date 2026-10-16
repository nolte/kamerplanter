"""REQ-053 GP-FR-040 / §9.2a (#2325): the bed flags on ``LocationType`` and the full-replace body.

* ``is_bed`` implies ``supports_layout`` — on create, on edit and on a stored row read
  back, so no path can store a bed without a layout;
* ``PUT /location-types/{key}`` rebuilds the model from ``LocationTypeUpdate``; a body
  that predates the flags is refused (422), never silently reset to "not a bed" — the
  ``is_system`` defect class the service documents.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.location_types.schemas import LocationTypeCreate, LocationTypeUpdate
from app.domain.models.location_type import LocationType


class TestABedSupportsALayout:
    def test_defaults_are_false(self) -> None:
        lt = LocationType(name="Regal")

        assert (lt.is_bed, lt.supports_layout) == (False, False)

    def test_is_bed_forces_supports_layout(self) -> None:
        lt = LocationType(name="Hochbeet", is_bed=True, supports_layout=False)

        assert lt.supports_layout is True

    def test_a_layout_without_a_bed_is_allowed(self) -> None:
        lt = LocationType(name="Zelt", supports_layout=True)

        assert (lt.is_bed, lt.supports_layout) == (False, True)

    def test_a_stored_row_with_a_bed_but_no_layout_reads_with_the_layout(self) -> None:
        lt = LocationType.model_validate({"_key": "terrassenbeet", "name": "Terrassenbeet", "is_bed": True})

        assert lt.supports_layout is True
        assert lt.model_dump()["supports_layout"] is True, "the next write persists the invariant"


class TestTheFullReplaceBodyCarriesTheFlags:
    def test_create_defaults_both_flags_to_false(self) -> None:
        body = LocationTypeCreate(name="Hügelbeet")

        assert (body.is_bed, body.supports_layout) == (False, False)

    def test_update_without_the_flags_is_refused(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            LocationTypeUpdate(name="Beet")

        missing = {error["loc"][0] for error in excinfo.value.errors() if error["type"] == "missing"}
        assert missing == {"is_bed", "supports_layout"}

    def test_update_with_the_flags_rebuilds_a_consistent_model(self) -> None:
        body = LocationTypeUpdate(name="Beet", is_bed=True, supports_layout=False)

        lt = LocationType(**body.model_dump())

        assert (lt.is_bed, lt.supports_layout) == (True, True)
