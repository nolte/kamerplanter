"""The declared cultivar guards on propagation and succession are *live* (SEC-006, #1112).

`SuccessionPlan.cultivar_key` and `PropagationEvent.cultivar_key` arrive from the
request body and were written unverified, so either could reference a foreign
tenant's cultivar. Both models carry their own `tenant_key`, so the #948
declaration works — which is exactly why it needs proving rather than assuming.

**Why these tests drive the real repositories.** The declaration is one line, and
a one-line declaration is precisely the shape that ships inert in this codebase:
`BaseArangoRepository._verify_owned_references` deliberately skips a row with no
`tenant_key`, so on `PlantingRunEntry` (surface 1 of #1112, *not* fixed here) the
same line would look identical and do nothing. A test against a test-local model
would pin the mechanism — which `test_owned_reference_update_guard.py` already
does — and say nothing about whether these two repositories actually got it. So
the subjects here are `ArangoSuccessionPlanRepository` and the propagation events
repository themselves, and the only double is the database.

Three cases per repository, and the middle one is the reason the first is not
enough: a guard that refused *every* reference would pass the foreign case while
making the feature unusable.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from app.common.enums import PropagationMethod
from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.succession_plan_repository import ArangoSuccessionPlanRepository
from app.data_access.repositories.propagation_repository import PropagationRepository
from app.domain.models.propagation import PropagationEvent
from app.domain.models.succession_plan import SuccessionPlan

_MINE = "tenant-a"
_THEIRS = "tenant-b"

_OWN_CULTIVAR = "cv-own"
_GLOBAL_CULTIVAR = "cv-global"
_FOREIGN_CULTIVAR = "cv-foreign"

_CULTIVARS: dict[str, dict[str, Any]] = {
    _OWN_CULTIVAR: {"_key": _OWN_CULTIVAR, "tenant_key": _MINE},
    _GLOBAL_CULTIVAR: {"_key": _GLOBAL_CULTIVAR, "tenant_key": ""},
    _FOREIGN_CULTIVAR: {"_key": _FOREIGN_CULTIVAR, "tenant_key": _THEIRS},
}


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self.docs = docs or {}
        self.inserts: list[dict[str, Any]] = []
        self.updates: list[dict[str, Any]] = []

    def get(self, key: str) -> dict[str, Any] | None:
        return self.docs.get(key)

    def insert(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.inserts.append(data)
        key = data.get("_key") or f"new-{len(self.inserts)}"
        stored = {**data, "_key": key}
        self.docs[key] = stored
        return {"new": stored, "_key": key}

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.updates.append(data)
        stored = {**self.docs.get(data["_key"], {}), **data}
        self.docs[data["_key"]] = stored
        return {"new": stored}

    @property
    def writes(self) -> int:
        return len(self.inserts) + len(self.updates)


class _Db:
    def __init__(self, collections: dict[str, _Collection]) -> None:
        self._collections = collections

    def collection(self, name: str) -> _Collection:
        return self._collections.setdefault(name, _Collection())


@pytest.fixture
def cultivars() -> _Collection:
    return _Collection({key: dict(doc) for key, doc in _CULTIVARS.items()})


# ── SuccessionPlan ───────────────────────────────────────────────────────────


@pytest.fixture
def succession(cultivars):
    rows = _Collection()
    repo = ArangoSuccessionPlanRepository(_Db({col.SUCCESSION_PLANS: rows, col.CULTIVARS: cultivars}))
    return repo, rows


def _plan(cultivar_key: str) -> SuccessionPlan:
    return SuccessionPlan(
        tenant_key=_MINE,
        name="Radish waves",
        species_key="sp-radish",
        cultivar_key=cultivar_key,
        interval_days=14,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 6, 1),
        plants_per_batch=20,
    )


def test_a_succession_plan_cannot_reference_a_foreign_cultivar(succession):
    repo, rows = succession

    with pytest.raises(NotFoundError):
        repo.create(_plan(_FOREIGN_CULTIVAR))

    assert rows.writes == 0, "the refusal must land before the row is written"


@pytest.mark.parametrize("cultivar_key", [_OWN_CULTIVAR, _GLOBAL_CULTIVAR])
def test_a_succession_plan_may_reference_its_own_or_a_global_cultivar(succession, cultivar_key):
    """The hybrid catalogue: a tenant's own row *and* the shared seed row bind.

    Without this, a guard that refused everything would satisfy the test above and
    make succession planning impossible against the seed catalogue every tenant uses.
    """
    repo, rows = succession

    repo.create(_plan(cultivar_key))

    assert rows.writes == 1


def test_a_succession_plan_cannot_be_re_pointed_at_a_foreign_cultivar(succession):
    """The update half — the two-request bypass #1090 C-9 closed on the mechanism.

    Create with a harmless key, then PUT the foreign one. Verified only because
    ``_verify_references_on_update`` is opted in on this repository; the guard's
    default is create-only.
    """
    repo, rows = succession
    created = repo.create(_plan(_OWN_CULTIVAR))
    before = rows.writes

    with pytest.raises(NotFoundError):
        repo.update(created.key or "", _plan(_FOREIGN_CULTIVAR))

    assert rows.writes == before


# ── PropagationEvent ─────────────────────────────────────────────────────────


@pytest.fixture
def propagation(cultivars):
    rows = _Collection()
    repo = PropagationRepository(_Db({col.PROPAGATION_EVENTS: rows, col.CULTIVARS: cultivars}))
    return repo, rows


def _event(cultivar_key: str) -> PropagationEvent:
    return PropagationEvent(tenant_key=_MINE, method=PropagationMethod.CUTTING, cultivar_key=cultivar_key)


def test_a_propagation_event_cannot_reference_a_foreign_cultivar(propagation):
    repo, rows = propagation

    with pytest.raises(NotFoundError):
        repo.create_event(_event(_FOREIGN_CULTIVAR))

    assert rows.writes == 0


@pytest.mark.parametrize("cultivar_key", [_OWN_CULTIVAR, _GLOBAL_CULTIVAR])
def test_a_propagation_event_may_reference_its_own_or_a_global_cultivar(propagation, cultivar_key):
    repo, rows = propagation

    repo.create_event(_event(cultivar_key))

    assert rows.writes == 1


def test_a_propagation_event_cannot_be_re_pointed_at_a_foreign_cultivar(propagation):
    repo, rows = propagation
    created = repo.create_event(_event(_OWN_CULTIVAR))
    before = rows.writes

    with pytest.raises(NotFoundError):
        repo.update_event(created.key or "", _event(_FOREIGN_CULTIVAR))

    assert rows.writes == before


# ── The declarations themselves, so a silent removal is loud ─────────────────


def test_both_repositories_still_declare_the_guard():
    """A behavioural test can be satisfied by an unrelated refusal path.

    Pinning the declaration as well means removing it fails *here*, naming the
    cause, instead of somewhere downstream with a message about a missing row.
    """
    for repo_cls in (ArangoSuccessionPlanRepository, _propagation_events_cls()):
        assert repo_cls._owned_reference_fields == {"cultivar_key": col.CULTIVARS}
        assert repo_cls._verify_references_on_update is True


def _propagation_events_cls() -> type:
    from app.data_access.repositories.propagation_repository import _PropagationEventRepository

    return _PropagationEventRepository
