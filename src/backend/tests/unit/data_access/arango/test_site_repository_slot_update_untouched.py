"""#2639 — ``ArangoSiteRepository.update_slot`` leaves the ``untouched`` columns out of the write.

The payload handed to ArangoDB is the contract: a column it does not name keeps the value stored at write time
(ArangoDB's update), so the stale copy ``PUT /slots`` read cannot revert a newer ``PATCH /slots`` or occupation
write, and a stale point ``geometry`` is never object-merged into a newer polygon. The race itself is measured
against a real ArangoDB in ``tests/integration/test_garden_resource_repository.py``
(``TestPutLeavesTheSlotColumnsAsStored``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Slot
from app.domain.services.site_service import SLOT_COLUMNS_A_PUT_LEAVES

_STORED = {
    "_key": "slot-1",
    "slot_id": "BED_S1",
    "location_key": "loc-1",
    "capacity_plants": 1,
    "currently_occupied": True,
    "slot_role": "zone",
    "geometry": {"kind": "polygon", "points": [[0, 0], [1, 0], [1, 1]], "rotation_deg": 0},
}


@pytest.fixture
def db() -> MagicMock:
    database = MagicMock()
    database.collection.return_value.update.return_value = {"new": dict(_STORED)}
    return database


def _payload(db: MagicMock) -> dict:
    return db.collection.return_value.update.call_args.args[0]


def _slot(**overrides) -> Slot:
    """The model ``PUT /slots`` hands in: the body's columns plus the stale kept copy of the rest."""
    return Slot(
        **{
            "slot_id": "BED_S1_NEW",
            "location_key": "loc-1",
            "capacity_plants": 2,
            "currently_occupied": False,
            "geometry": {"kind": "point", "origin": [0.5, 0.5]},
            "geometry_source": "editor",
            **overrides,
        }
    )


def test_the_untouched_columns_are_not_in_the_written_document(db: MagicMock) -> None:
    ArangoSiteRepository(db).update_slot("slot-1", _slot(), untouched=SLOT_COLUMNS_A_PUT_LEAVES)

    payload = _payload(db)
    assert set(payload) & set(SLOT_COLUMNS_A_PUT_LEAVES) == set()
    assert (payload["_key"], payload["slot_id"], payload["capacity_plants"]) == ("slot-1", "BED_S1_NEW", 2)


def test_without_untouched_columns_the_whole_model_is_written(db: MagicMock) -> None:
    """The occupation writers pass none: their flag is the column they own."""
    ArangoSiteRepository(db).update_slot("slot-1", _slot())

    assert {"currently_occupied", "geometry", "slot_role", "geometry_source"} <= set(_payload(db))


def test_the_answer_is_the_stored_document(db: MagicMock) -> None:
    returned = ArangoSiteRepository(db).update_slot("slot-1", _slot(), untouched=SLOT_COLUMNS_A_PUT_LEAVES)

    assert returned.currently_occupied is True and returned.slot_role == "zone"
    assert returned.geometry is not None and returned.geometry.kind == "polygon"


def test_a_misspelt_untouched_name_is_refused_before_the_write(db: MagicMock) -> None:
    with pytest.raises(AttributeError, match="occupied"):
        ArangoSiteRepository(db).update_slot("slot-1", _slot(), untouched=("occupied",))

    db.collection.return_value.update.assert_not_called()
