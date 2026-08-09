"""The #948 owned-reference guard on the **update** path (#1090 C-9).

Solitary unit tests on the mechanism itself, with a test-local model and
repository so the contract is pinned independently of any one domain. The
``StandardDatabase`` is the owned I/O boundary and is doubled.

``BaseArangoRepository.create`` has verified declared foreign references since
#948, but ``update`` never did — which left the guard bypassable in two requests:
write the row with a harmless reference, then ``PUT`` the foreign key onto it.
The guard added for #1090 closes that, and does so only for a reference the update
actually **re-points**. Both halves are load-bearing and both are pinned here:

* a re-point at another tenant's row fails closed with 404 and writes nothing;
* an untouched reference is never dialled — otherwise a row whose target has since
  been deleted (a dangling key: an integrity defect, not a disclosure route) would
  become permanently uneditable, and every internal full-model rewrite would pay a
  lookup for a value nobody supplied.
"""

from __future__ import annotations

from typing import Any

import pytest
import structlog.testing
from pydantic import BaseModel, Field

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository

TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
GLOBAL_PLANT = "plant-global"
FOREIGN_PLANT = "plant-b1"

PLANTS: dict[str, dict[str, Any]] = {
    OWN_PLANT: {"_key": OWN_PLANT, "tenant_key": TENANT_KEY},
    GLOBAL_PLANT: {"_key": GLOBAL_PLANT, "tenant_key": ""},
    FOREIGN_PLANT: {"_key": FOREIGN_PLANT, "tenant_key": FOREIGN_TENANT_KEY},
}


class Widget(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str
    plant_key: str | None = None

    model_config = {"populate_by_name": True}


class BasketWidget(Widget):
    plant_keys: list[str] = Field(default_factory=list)


class GuardedRepo(BaseArangoRepository[Widget]):
    _model_cls = Widget
    _owned_reference_fields = {"plant_key": col.PLANT_INSTANCES}
    _verify_references_on_update = True


class UnguardedRepo(BaseArangoRepository[Widget]):
    """Same declaration, opted out — the default every other repository keeps."""

    _model_cls = Widget
    _owned_reference_fields = {"plant_key": col.PLANT_INSTANCES}


class BasketRepo(BaseArangoRepository[BasketWidget]):
    _model_cls = BasketWidget
    _owned_reference_fields = {"plant_keys": col.PLANT_INSTANCES}
    _verify_references_on_update = True


class _Collection:
    """Minimal collection double recording reads and writes."""

    def __init__(self, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self.docs = docs or {}
        self.reads: list[str] = []
        self.updates: list[dict[str, Any]] = []

    def get(self, key: str) -> dict[str, Any] | None:
        self.reads.append(key)
        return self.docs.get(key)

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.updates.append(data)
        stored = {**self.docs.get(data["_key"], {}), **data}
        self.docs[data["_key"]] = stored
        return {"new": stored}


class _Db:
    def __init__(self, widgets: _Collection, plants: _Collection) -> None:
        self._collections = {"widgets": widgets, col.PLANT_INSTANCES: plants}

    def collection(self, name: str) -> _Collection:
        return self._collections[name]


def _stored(plant_key: str | None = OWN_PLANT, **extra: Any) -> dict[str, Any]:
    return {"_key": "w1", "tenant_key": TENANT_KEY, "name": "Hammer", "plant_key": plant_key, **extra}


@pytest.fixture
def widgets() -> _Collection:
    return _Collection({"w1": _stored()})


@pytest.fixture
def plants() -> _Collection:
    return _Collection({key: dict(doc) for key, doc in PLANTS.items()})


@pytest.fixture
def repo(widgets, plants) -> GuardedRepo:
    return GuardedRepo(_Db(widgets, plants), "widgets")


def _widget(plant_key: str | None, tenant_key: str = TENANT_KEY) -> Widget:
    return Widget(key="w1", tenant_key=tenant_key, name="Hammer", plant_key=plant_key)


class TestARepointedReference:
    def test_a_foreign_target_fails_closed_and_writes_nothing(self, repo, widgets):
        with pytest.raises(NotFoundError):
            repo.update("w1", _widget(FOREIGN_PLANT))

        assert widgets.updates == []
        assert widgets.docs["w1"]["plant_key"] == OWN_PLANT

    def test_an_unknown_target_looks_exactly_the_same(self, repo):
        """No oracle: 'owned elsewhere' and 'does not exist' are one answer."""
        with pytest.raises(NotFoundError):
            repo.update("w1", _widget("no-such-plant"))

    @pytest.mark.parametrize("target", [GLOBAL_PLANT, OWN_PLANT])
    def test_a_bindable_target_is_written(self, repo, widgets, target):
        repo.update("w1", _widget(target))

        assert widgets.docs["w1"]["plant_key"] == target

    def test_clearing_the_reference_is_allowed_and_dials_nothing(self, repo, plants):
        """Dropping a reference is a change, but there is no new target to verify."""
        repo.update("w1", _widget(None))

        assert plants.reads == []


class TestAnUntouchedReference:
    def test_is_never_dialled(self, repo, plants):
        repo.update("w1", _widget(OWN_PLANT))

        assert plants.reads == []

    def test_survives_the_deletion_of_its_target(self, repo, plants, widgets):
        """A dangling reference must not make the row uneditable."""
        del plants.docs[OWN_PLANT]

        repo.update("w1", Widget(key="w1", tenant_key=TENANT_KEY, name="Renamed", plant_key=OWN_PLANT))

        assert widgets.docs["w1"]["name"] == "Renamed"

    def test_a_reordered_key_list_is_not_a_repoint(self, plants):
        widgets = _Collection({"w1": _stored(plant_key=None, plant_keys=[OWN_PLANT, GLOBAL_PLANT])})
        repo = BasketRepo(_Db(widgets, plants), "widgets")

        repo.update(
            "w1",
            BasketWidget(key="w1", tenant_key=TENANT_KEY, name="Hammer", plant_keys=[GLOBAL_PLANT, OWN_PLANT]),
        )

        assert plants.reads == []


class TestTheGuardsBoundaries:
    def test_it_is_off_unless_the_repository_opts_in(self, widgets, plants):
        """The default every other repository keeps: create-only verification."""
        repo = UnguardedRepo(_Db(widgets, plants), "widgets")

        repo.update("w1", _widget(FOREIGN_PLANT))

        assert widgets.docs["w1"]["plant_key"] == FOREIGN_PLANT
        assert plants.reads == []

    def test_an_absent_document_is_left_to_the_update_itself(self, plants):
        """Nothing is written, so there is nothing to verify — and no target read."""
        widgets = _Collection()
        repo = GuardedRepo(_Db(widgets, plants), "widgets")

        repo.update("w1", _widget(FOREIGN_PLANT))

        assert plants.reads == []

    def test_a_tenantless_row_says_out_loud_that_it_skipped_the_check(self, repo):
        """Fail-open here mirrors ``create``'s: unreachable from a router, never silent."""
        with structlog.testing.capture_logs() as logs:
            repo.update("w1", _widget(FOREIGN_PLANT, tenant_key=""))

        skipped = [entry for entry in logs if entry["event"] == "owned_reference_check_skipped_tenantless_row"]
        assert skipped and skipped[0]["fields"] == ["plant_key"]

    def test_only_the_changed_field_is_named_in_the_skip_log(self, plants):
        """The subset, not the whole declaration — the log describes what was skipped."""
        widgets = _Collection({"w1": _stored(plant_key=None, plant_keys=[])})
        repo = BasketRepo(_Db(widgets, plants), "widgets")

        with structlog.testing.capture_logs() as logs:
            repo.update(
                "w1",
                BasketWidget(key="w1", tenant_key="", name="Hammer", plant_keys=[FOREIGN_PLANT]),
            )

        skipped = [entry for entry in logs if entry["event"] == "owned_reference_check_skipped_tenantless_row"]
        assert skipped and skipped[0]["fields"] == ["plant_keys"]
