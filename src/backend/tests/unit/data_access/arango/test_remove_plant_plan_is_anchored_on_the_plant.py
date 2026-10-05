"""#2107 — detaching a plant from its plan verifies the plant in the repository.

``DELETE /t/{slug}/plant-instances/{key}/nutrient-plan`` checked the plant in the
router and then called an unscoped ``remove_plant_plan(key)`` that deleted every
``follows_plan`` edge of whatever plant key it was given — check-then-act. The
repository now takes ``*, tenant_key`` and verifies the plant first.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository


def _repo(plant: dict | None) -> tuple[ArangoNutrientPlanRepository, MagicMock]:
    db = MagicMock()
    db.collection.return_value.get.return_value = plant
    return ArangoNutrientPlanRepository(db), db


@pytest.mark.parametrize("plant", [None, {"_key": "p1", "tenant_key": "t-b"}])
def test_a_foreign_or_unknown_plant_is_not_found_and_no_edge_is_removed(plant) -> None:
    repo, db = _repo(plant)
    with pytest.raises(NotFoundError):
        repo.remove_plant_plan("p1", tenant_key="t-a")
    db.aql.execute.assert_not_called()


def test_an_own_plant_loses_its_plan_edges() -> None:
    repo, db = _repo({"_key": "p1", "tenant_key": "t-a"})
    assert repo.remove_plant_plan("p1", tenant_key="t-a") is True
    db.collection.assert_any_call(col.PLANT_INSTANCES)
    assert db.aql.execute.called
