"""#2623 — ``ArangoSiteRepository.update_location`` leaves the ``untouched`` columns out of the write.

The payload handed to ArangoDB is the contract: a column it does not name keeps the value stored at write time
(ArangoDB's update), so a stale copy the caller read cannot revert a newer write. The frost mirror is the one
``site_conditions`` sub-path. The behaviour against a real ArangoDB (the race itself) is measured in
``tests/integration/test_location_put_leaves_plan_columns.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import FrostRisk
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Location
from app.domain.services.site_service import LOCATION_FIELDS_KEPT_ON_EDIT

_STORED = {
    "_key": "loc-1",
    "name": "Bed",
    "site_key": "site-1",
    "area_m2": 2.0,
    "geometry": {"kind": "rect", "origin": [1, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0},
    "site_conditions": {"sun_profile": {"sun_window": "afternoon"}},
}


@pytest.fixture
def db() -> MagicMock:
    database = MagicMock()
    database.collection.return_value.update.return_value = {"new": dict(_STORED)}
    return database


def _payload(db: MagicMock) -> dict:
    return db.collection.return_value.update.call_args.args[0]


def _location(**overrides) -> Location:
    return Location(**{"name": "Bed (renamed)", "site_key": "site-1", "area_m2": 2.0, **overrides})


def test_the_untouched_columns_are_not_in_the_written_document(db: MagicMock) -> None:
    location = _location(geometry=_STORED["geometry"], site_conditions={"sun_profile": {"sun_window": "morning"}})

    ArangoSiteRepository(db).update_location("loc-1", location, untouched=(*LOCATION_FIELDS_KEPT_ON_EDIT, "area_m2"))

    payload = _payload(db)
    assert set(payload) & {*LOCATION_FIELDS_KEPT_ON_EDIT, "area_m2"} == set()
    assert payload["name"] == "Bed (renamed)" and payload["_key"] == "loc-1"
    # the body's columns keep the full-replace null semantics (#714)
    assert payload["frost_exposed"] is None
    assert db.collection.return_value.update.call_args.kwargs["keep_none"] is False


def test_without_untouched_columns_the_whole_model_is_written(db: MagicMock) -> None:
    ArangoSiteRepository(db).update_location("loc-1", _location(), untouched=())

    assert {"site_conditions", "geometry", "area_m2", "z_order"} <= set(_payload(db))


def test_the_frost_mirror_is_the_one_site_conditions_sub_path(db: MagicMock) -> None:
    ArangoSiteRepository(db).update_location(
        "loc-1", _location(), untouched=LOCATION_FIELDS_KEPT_ON_EDIT, frost_risk=FrostRisk.HIGH
    )

    assert _payload(db)["site_conditions"] == {"microclimate": {"frost_risk": "high"}}
    # merged into the stored object (ArangoDB's default mergeObjects), never replacing it
    assert db.collection.return_value.update.call_args.kwargs.get("merge", True) is True


def test_the_answer_is_the_stored_document(db: MagicMock) -> None:
    returned = ArangoSiteRepository(db).update_location("loc-1", _location(), untouched=LOCATION_FIELDS_KEPT_ON_EDIT)

    assert returned.site_conditions is not None
    assert returned.site_conditions.sun_profile.sun_window == "afternoon"


def test_a_misspelt_untouched_name_is_refused_before_the_write(db: MagicMock) -> None:
    with pytest.raises(AttributeError, match="sun_profil"):
        ArangoSiteRepository(db).update_location("loc-1", _location(), untouched=("sun_profil",))

    db.collection.return_value.update.assert_not_called()
