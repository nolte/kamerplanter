"""Unit tests for the shared domain-to-response mapper (AP-18a / DUP-B4)."""

from pydantic import BaseModel

from app.api.mapping import to_response


class _Domain(BaseModel):
    key: str | None = None
    name: str = ""
    secret: str = ""  # deliberately absent from the response schema


class _Resp(BaseModel):
    key: str
    name: str


def test_key_defaults_to_empty_string_when_absent():
    result = to_response(_Domain(name="topping"), _Resp)
    assert result.key == ""
    assert result.name == "topping"


def test_existing_key_passes_through():
    result = to_response(_Domain(key="a1", name="topping"), _Resp)
    assert result.key == "a1"


def test_unknown_domain_fields_are_filtered_out():
    result = to_response(_Domain(name="topping", secret="hidden"), _Resp)
    assert not hasattr(result, "secret")
    assert result.name == "topping"


def test_overrides_win_over_dumped_values():
    class _RespWithComputed(BaseModel):
        key: str
        name: str
        computed: str = ""

    result = to_response(_Domain(name="topping"), _RespWithComputed, computed="value", name="override")
    assert result.computed == "value"
    assert result.name == "override"


def test_matches_legacy_idiom_for_real_schema():
    from app.api.v1.activities.schemas import ActivityResponse
    from app.domain.models.activity import Activity

    activity = Activity(name="Topping")
    legacy = ActivityResponse(key=activity.key or "", **activity.model_dump(exclude={"key"}))
    mapped = to_response(activity, ActivityResponse)
    assert mapped.model_dump() == legacy.model_dump()
