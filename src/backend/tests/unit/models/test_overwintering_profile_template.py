"""Unit tests for the species-level OverwinteringProfileTemplate model (REQ-022)."""

import pytest
from pydantic import ValidationError

from app.common.enums import HardinessRating, TuberStatus, WinterAction
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate


def _base(**overrides):
    data = {
        "species_scientific_name": "Aechmea fasciata",
        "hardiness_rating": HardinessRating.FROST_FREE,
        "winter_action": WinterAction.MOVE_INDOORS,
        "winter_action_month": 9,
    }
    data.update(overrides)
    return data


class TestOverwinteringProfileTemplate:
    def test_minimal_valid(self):
        tpl = OverwinteringProfileTemplate.model_validate(_base())
        assert tpl.species_scientific_name == "Aechmea fasciata"
        assert tpl.source == "steckbrief"
        assert tpl.species_key is None

    def test_key_alias_roundtrips(self):
        tpl = OverwinteringProfileTemplate.model_validate({**_base(), "_key": "aechmea_fasciata"})
        assert tpl.key == "aechmea_fasciata"
        assert tpl.model_dump(by_alias=True)["_key"] == "aechmea_fasciata"

    def test_month_is_optional(self):
        """A ``none`` action on a fully hardy species has no meaningful month."""
        tpl = OverwinteringProfileTemplate.model_validate(
            _base(hardiness_rating=HardinessRating.HARDY, winter_action=WinterAction.NONE, winter_action_month=None)
        )
        assert tpl.winter_action_month is None

    def test_month_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            OverwinteringProfileTemplate.model_validate(_base(winter_action_month=13))

    def test_tuber_status_requires_dig_and_store(self):
        with pytest.raises(ValidationError, match="tuber_status"):
            OverwinteringProfileTemplate.model_validate(
                _base(tuber_status=TuberStatus.STORED)  # rating is frost_free, not dig_and_store
            )

    def test_tuber_status_allowed_for_dig_and_store(self):
        tpl = OverwinteringProfileTemplate.model_validate(
            _base(
                hardiness_rating=HardinessRating.DIG_AND_STORE,
                winter_action=WinterAction.DIG_STORE,
                winter_action_month=10,
                tuber_status=TuberStatus.STORED,
            )
        )
        assert tpl.tuber_status == TuberStatus.STORED

    def test_temp_min_above_max_rejected(self):
        with pytest.raises(ValidationError, match="winter_quarter_temp_min"):
            OverwinteringProfileTemplate.model_validate(_base(winter_quarter_temp_min=20, winter_quarter_temp_max=10))

    def test_temp_equal_bounds_allowed(self):
        tpl = OverwinteringProfileTemplate.model_validate(_base(winter_quarter_temp_min=15, winter_quarter_temp_max=15))
        assert tpl.winter_quarter_temp_min == tpl.winter_quarter_temp_max == 15
