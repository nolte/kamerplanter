"""A task may only bind to an entity the caller's tenant owns (SEC-I01, #1102).

`POST /t/{tenant_slug}/tasks` stamped the task with the caller's `tenant_key` but
never checked the caller-supplied `entity_key`/`entity_type`. The repository then
wrote a `has_task` edge to whatever key arrived — an unvalidated cross-boundary
reference plus a graph edge into a foreign tenant's document.

Two things here are worth more than the happy path.

**`location` is anchored on its site, not on its own field.** `Location` *has* a
`tenant_key`, and nothing ever writes it: the create path is
`Location(**body.model_dump())` and `LocationCreate` carries no such field, so
every stored row holds `""`. A guard that checked `location.tenant_key ==
caller` would therefore reject **every** location-bound task while looking
exactly like a correct security fix. `test_a_location_is_anchored_on_its_site`
and its own-tenant sibling are the pair that catches that.

**The unknown-type arm fails closed.** The verified set is derived from
`ENTITY_TYPE_TO_COLLECTION` — the same map that decides whether an edge is
written at all — so the two cannot drift. If a fifth type is added there without
an anchor here, an edge would be written to an entity nobody checked; the guard
raises instead, and a test drives that branch rather than excluding it from
coverage.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango import task_repository
from app.domain.services.task_entity_guard import TaskEntityGuard

_MINE = "tenant_acme"
_THEIRS = "tenant_other"


class _TenantScopedService:
    """Answers 404 for a foreign row, exactly as the real services do."""

    def __init__(self, owner: str = _MINE) -> None:
        self._owner = owner
        self.calls: list[tuple[str, str]] = []

    def _resolve(self, key: str, tenant_key: str, name: str):
        self.calls.append((key, tenant_key))
        if tenant_key and self._owner != tenant_key:
            raise NotFoundError(name, key)
        return SimpleNamespace(key=key, tenant_key=self._owner)

    def get_plant(self, key, *, tenant_key=""):
        return self._resolve(key, tenant_key, "PlantInstance")

    def get_run(self, key, *, tenant_key=""):
        return self._resolve(key, tenant_key, "PlantingRun")

    def get_tank(self, key, *, tenant_key=""):
        return self._resolve(key, tenant_key, "Tank")


class _SiteService:
    """Locations resolve unscoped; the *site* carries the tenancy (see module docstring)."""

    def __init__(self, site_owner: str = _MINE) -> None:
        self._site_owner = site_owner
        self.site_lookups: list[tuple[str, str]] = []

    def get_location(self, key):
        # Deliberately mirrors reality: no tenant argument, and tenant_key is ""
        # on every stored row.
        return SimpleNamespace(key=key, site_key="site_1", tenant_key="")

    def get_site(self, key, *, tenant_key=""):
        self.site_lookups.append((key, tenant_key))
        if tenant_key and self._site_owner != tenant_key:
            raise NotFoundError("Site", key)
        return SimpleNamespace(key=key, tenant_key=self._site_owner)


def _guard(*, owner: str = _MINE, site_owner: str = _MINE) -> TaskEntityGuard:
    return TaskEntityGuard(
        _TenantScopedService(owner),
        _TenantScopedService(owner),
        _TenantScopedService(owner),
        _SiteService(site_owner),
    )


# ── A foreign entity is refused, and refused as 404 ───────────────────────────


@pytest.mark.parametrize("entity_type", ["plant_instance", "planting_run", "tank"])
def test_a_foreign_entity_is_refused(entity_type: str) -> None:
    guard = _guard(owner=_THEIRS)

    with pytest.raises(NotFoundError):
        guard.verify(entity_type, "e1", tenant_key=_MINE)


def test_a_location_in_a_foreign_site_is_refused() -> None:
    guard = _guard(site_owner=_THEIRS)

    with pytest.raises(NotFoundError):
        guard.verify("location", "loc_1", tenant_key=_MINE)


# ── The caller's own entities still bind ──────────────────────────────────────


@pytest.mark.parametrize("entity_type", ["plant_instance", "planting_run", "tank"])
def test_an_own_entity_is_accepted(entity_type: str) -> None:
    """The half that stops this from being a blanket refusal."""
    _guard().verify(entity_type, "e1", tenant_key=_MINE)


def test_a_location_is_anchored_on_its_site() -> None:
    """The trap: `Location.tenant_key` is dead, so the site is the only real anchor.

    Anchoring on the field would 404 every location-bound task — an
    over-rejecting guard indistinguishable from a working one until a user files
    a bug. The assertion is on *where* the check happened, not just that it
    passed.
    """
    sites = _SiteService()
    guard = TaskEntityGuard(_TenantScopedService(), _TenantScopedService(), _TenantScopedService(), sites)

    guard.verify("location", "loc_1", tenant_key=_MINE)

    assert sites.site_lookups == [("site_1", _MINE)], "the tenancy check must land on the parent site"


# ── What the guard deliberately lets through ──────────────────────────────────


@pytest.mark.parametrize(
    ("entity_type", "entity_key"),
    [(None, None), ("plant_instance", None), (None, "e1"), ("plant_instance", "")],
)
def test_an_unbound_task_is_untouched(entity_type, entity_key) -> None:
    _guard(owner=_THEIRS).verify(entity_type, entity_key, tenant_key=_MINE)


@pytest.mark.parametrize("entity_type", ["generic", "plant", "actuator", "species"])
def test_a_type_that_writes_no_edge_is_untouched(entity_type: str) -> None:
    """Only types in `ENTITY_TYPE_TO_COLLECTION` produce a dereferenceable edge.

    All four of these occur in the tree today. Rejecting them would break
    producers over a cross-boundary reference that is never created.
    """
    assert entity_type not in task_repository.ENTITY_TYPE_TO_COLLECTION

    _guard(owner=_THEIRS).verify(entity_type, "e1", tenant_key=_MINE)


def test_the_system_context_is_ungated() -> None:
    """Celery care-reminder generation and seeds mint their own bindings, unscoped."""
    _guard(owner=_THEIRS).verify("plant_instance", "e1", tenant_key="")


# ── Drift: a new edge-writing type must not slip through unverified ───────────


def test_a_new_edge_writing_type_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Add a fifth entry to the map and the guard must refuse, not shrug.

    This is the branch that keeps the two sets honest. Without it, someone
    extending `ENTITY_TYPE_TO_COLLECTION` gets an edge written to an entity no
    anchor was ever written for — silently, and in the permissive direction.
    """
    monkeypatch.setitem(task_repository.ENTITY_TYPE_TO_COLLECTION, "greenhouse", "greenhouses")

    with pytest.raises(NotFoundError):
        _guard().verify("greenhouse", "gh_1", tenant_key=_MINE)
