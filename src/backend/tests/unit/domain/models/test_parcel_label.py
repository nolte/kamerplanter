"""GP-FR-176 (#2759): the parcel label of a location - one line, at most 40 characters, blank is none."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.models.garden_plan import LocationFieldsPatch, LocationPatch
from app.domain.models.garden_plan_export import ExportLocation
from app.domain.models.parcel_label import PARCEL_LABEL_MAX_CHARS
from app.domain.models.site import Location


def _location(**fields: object) -> Location:
    return Location(name="Beet 1", area_m2=1.0, **fields)


class TestTheStoredValue:
    def test_absent_is_none(self) -> None:
        assert _location().parcel_label is None

    def test_surrounding_whitespace_is_stripped(self) -> None:
        assert _location(parcel_label="  Parzelle 12 ").parcel_label == "Parzelle 12"

    @pytest.mark.parametrize("blank", ["", "   ", "　"])
    def test_a_blank_text_is_no_label(self, blank: str) -> None:
        assert _location(parcel_label=blank).parcel_label is None

    def test_the_longest_label_is_taken_one_more_is_refused(self) -> None:
        assert _location(parcel_label="x" * PARCEL_LABEL_MAX_CHARS).parcel_label == "x" * PARCEL_LABEL_MAX_CHARS
        with pytest.raises(ValidationError, match="at most 40 characters"):
            _location(parcel_label="x" * (PARCEL_LABEL_MAX_CHARS + 1))

    @pytest.mark.parametrize("text", ["A\n17", "A\t17", "A‮71", "A B", "A\x0017"])
    def test_a_line_break_a_control_or_a_bidi_character_is_refused(self, text: str) -> None:
        with pytest.raises(ValidationError, match="one line of text"):
            _location(parcel_label=text)

    def test_a_number_is_refused_not_coerced(self) -> None:
        with pytest.raises(ValidationError):
            _location(parcel_label=17)


class TestTheWriteBodies:
    def test_the_patch_takes_null_to_clear(self) -> None:
        patch = LocationPatch.model_validate({"parcel_label": None})
        assert "parcel_label" in patch.model_fields_set and patch.parcel_label is None

    def test_the_patch_and_the_plan_batch_hold_the_same_rule(self) -> None:
        for body in (LocationPatch, LocationFieldsPatch):
            assert body.model_validate({"parcel_label": " A-17 "}).parcel_label == "A-17"
            with pytest.raises(ValidationError):
                body.model_validate({"parcel_label": "A\n17"})

    def test_the_plan_file_carries_it_and_a_file_without_it_reads(self) -> None:
        exported = ExportLocation.model_validate(_location(_key="b1", parcel_label="A-17"))
        assert exported.parcel_label == "A-17"
        legacy = ExportLocation.model_validate({"key": "b1", "name": "Beet 1", "location_type_key": "bed"})
        assert legacy.parcel_label is None
