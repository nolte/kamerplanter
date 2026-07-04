import pytest
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import HardinessRating, TuberStatus, WinterAction
from app.domain.models.overwintering_profile import OverwinteringProfile


def _base(**overrides) -> dict:
    data = {
        "plant_key": "p1",
        "hardiness_rating": HardinessRating.DIG_AND_STORE,
        "winter_action": WinterAction.DIG_STORE,
        "winter_action_month": 10,
    }
    data.update(overrides)
    return data


class TestTuberStatusValidator:
    def test_tuber_status_allowed_for_dig_and_store(self) -> None:
        profile = OverwinteringProfile(**_base(tuber_status=TuberStatus.STORED))
        assert profile.tuber_status == TuberStatus.STORED

    def test_tuber_status_rejected_for_other_ratings(self) -> None:
        with pytest.raises(PydanticValidationError, match="tuber_status"):
            OverwinteringProfile(
                **_base(
                    hardiness_rating=HardinessRating.HARDY,
                    winter_action=WinterAction.NONE,
                    tuber_status=TuberStatus.STORED,
                )
            )

    def test_tuber_status_none_is_always_valid(self) -> None:
        profile = OverwinteringProfile(**_base(hardiness_rating=HardinessRating.HARDY, winter_action=WinterAction.NONE))
        assert profile.tuber_status is None

    def test_key_alias_round_trip(self) -> None:
        profile = OverwinteringProfile(_key="ow1", **_base())
        assert profile.key == "ow1"
        dumped = profile.model_dump(by_alias=True)
        assert dumped["_key"] == "ow1"

    def test_month_bounds_enforced(self) -> None:
        with pytest.raises(PydanticValidationError):
            OverwinteringProfile(**_base(winter_action_month=13))
