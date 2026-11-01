"""#2538 — the one merge rule of ``Location.site_conditions``, shared by ``PATCH /locations`` and the plan batch.

Both bodies are driven through the same function: the PATCH body (every part) and the batch body (sun profile
only). A rule that drifted between the two paths would show here as one body merging differently from the other.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.engines.site_conditions_merge import merge_site_conditions, sent_fields, sent_site_parts
from app.domain.models.garden_plan import PlanSiteConditionsPatch, SiteConditionsPatch
from app.domain.models.site import SiteConditions

_STORED = SiteConditions(
    sun_profile={"sun_window": "morning", "direct_sun_hours_summer": 6.0, "foliage_shade_in_summer": True},
    microclimate={"frost_risk": "high", "cold_air_pocket": True},
    wind_exposure="exposed",
    access_sides=["N", "S"],
)


@pytest.mark.parametrize("body", [SiteConditionsPatch, PlanSiteConditionsPatch])
def test_a_sent_sun_key_changes_that_key_and_nothing_else(body) -> None:
    merged = merge_site_conditions(_STORED, body(sun_profile={"sun_window": "afternoon"}))

    assert merged.sun_profile.sun_window == "afternoon"
    assert (merged.sun_profile.direct_sun_hours_summer, merged.sun_profile.foliage_shade_in_summer) == (6.0, True)
    assert (merged.microclimate.frost_risk, merged.microclimate.cold_air_pocket) == ("high", True)
    assert merged.wind_exposure == "exposed" and [side.value for side in merged.access_sides] == ["N", "S"]


@pytest.mark.parametrize("body", [SiteConditionsPatch, PlanSiteConditionsPatch])
def test_a_sent_null_clears_the_hours_only(body) -> None:
    merged = merge_site_conditions(_STORED, body(sun_profile={"direct_sun_hours_summer": None}))

    assert merged.sun_profile.direct_sun_hours_summer is None
    assert merged.sun_profile.sun_window == "morning"


def test_nothing_stored_merges_onto_the_unknown_defaults() -> None:
    merged = merge_site_conditions(None, PlanSiteConditionsPatch(sun_profile={"foliage_shade_in_summer": True}))

    assert merged.sun_profile.foliage_shade_in_summer is True
    assert (merged.sun_profile.sun_window, merged.microclimate.frost_risk) == ("unknown", "unknown")


def test_a_flat_part_and_a_list_are_replaced_whole() -> None:
    merged = merge_site_conditions(_STORED, SiteConditionsPatch(wind_exposure="sheltered", access_sides=["E"]))

    assert merged.wind_exposure == "sheltered" and [side.value for side in merged.access_sides] == ["E"]
    assert merged.sun_profile == _STORED.sun_profile  # an untouched nested part is the stored one


def test_the_stored_value_is_not_changed_in_place() -> None:
    before = _STORED.model_dump()
    merge_site_conditions(_STORED, PlanSiteConditionsPatch(sun_profile={"sun_window": "all_day"}))
    assert _STORED.model_dump() == before


def test_the_merged_value_is_validated_against_the_stored_model() -> None:
    """The result is a ``SiteConditions``: a bound of the stored model holds even for a looser request body."""
    loose = SiteConditionsPatch.model_construct(
        sun_profile=SiteConditionsPatch.model_fields["sun_profile"].annotation.model_construct(
            _fields_set={"direct_sun_hours_summer"}, direct_sun_hours_summer=30.0
        ),
        _fields_set={"sun_profile"},
    )
    with pytest.raises(ValidationError):
        merge_site_conditions(_STORED, loose)


def test_sent_fields_lists_only_what_the_body_set() -> None:
    body = PlanSiteConditionsPatch(sun_profile={"sun_window": "mixed"})
    assert set(sent_fields(body)) == {"sun_profile"}
    assert sent_fields(body.sun_profile) == {"sun_window": "mixed"}


# ── #2569: what PATCH /locations writes - the sent parts, not the whole merged value ─────────────────────────


def _written(sent: SiteConditionsPatch) -> dict:
    return sent_site_parts(merge_site_conditions(_STORED, sent).model_dump(mode="json"), sent)


def test_the_write_carries_only_the_sent_nested_keys() -> None:
    written = _written(SiteConditionsPatch(microclimate={"frost_risk": "low"}))

    assert written == {"microclimate": {"frost_risk": "low"}}  # no sun profile a concurrent batch could lose


def test_a_cleared_key_is_written_as_none_so_the_store_removes_it() -> None:
    written = _written(SiteConditionsPatch(sun_profile={"direct_sun_hours_summer": None}, slope_deg=None))

    assert written == {"sun_profile": {"direct_sun_hours_summer": None}, "slope_deg": None}


def test_flat_parts_and_lists_are_written_json_shaped_from_the_merged_value() -> None:
    written = _written(SiteConditionsPatch(wind_exposure="sheltered", access_sides=["E"]))

    assert written == {"wind_exposure": "sheltered", "access_sides": ["E"]}


def test_an_empty_nested_part_writes_an_empty_object() -> None:
    assert _written(SiteConditionsPatch.model_validate({"sun_profile": {}})) == {"sun_profile": {}}
