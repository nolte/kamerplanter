"""#2107 (MT-010) — a parent-scoped model declares no ``tenant_key`` of its own.

``Location.tenant_key`` and ``Slot.tenant_key`` existed and were never written:
every document held ``""``. A field that is always empty is worse than no field —
``""`` is the hybrid-catalogue marker for *global*, so every check that trusted
it either refused the caller's own row (#706, #1397: a guard comparing it with the
tenant) or would have admitted every tenant's row (a check reading ``""`` as
global, the ``HARVEST_OBSERVATIONS`` shape). The fields were removed; the tenant
of a location or slot is its site's.

**The rule**: every collection that
``test_tenant_scoped_reads_are_derived.PARENT_CHAINS`` declares as tenant-scoped
*through a parent* maps to models without a ``tenant_key`` field. A new child
collection that copies the field "for later" fails here rather than shipping a
second never-written owner.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from app.data_access.arango import collections as col
from tests.support.execution_guards import find_project_root
from tests.unit.guards.test_tenant_scoped_reads_are_derived import PARENT_CHAINS, Inventory, build_inventory

_APP = find_project_root(Path(__file__)) / "app"


@cache
def _inventory() -> Inventory:
    return build_inventory(_APP)


def _parent_scoped_models_with_a_tenant(inventory: Inventory, collections: set[str]) -> list[str]:
    return sorted(
        f"{collection}: {model}"
        for collection in collections
        for module, model in inventory.collection_models.get(collection, set())
        if "tenant_key" in inventory.fields_by_model[(module, model)]
    )


def test_no_parent_scoped_model_declares_a_tenant_of_its_own() -> None:
    offenders = _parent_scoped_models_with_a_tenant(_inventory(), set(PARENT_CHAINS))
    assert offenders == [], (
        "These collections are tenant-scoped through a parent (PARENT_CHAINS) but their model declares a "
        "tenant_key no write path fills. Drop the field and resolve the owner through the parent (#2107)."
    )


def test_every_parent_scoped_collection_resolves_to_a_model() -> None:
    """Anti-vacuity: a collection with no placed model would pass the rule above by having nothing to check."""
    inventory = _inventory()
    unplaced = sorted(c for c in PARENT_CHAINS if not inventory.collection_models.get(c))
    assert unplaced == []
    assert {col.LOCATIONS, col.SLOTS, col.HARVEST_OBSERVATIONS, col.SENSORS} <= set(PARENT_CHAINS)


def test_the_rule_names_a_tenant_carrying_model_and_passes_a_parent_scoped_one() -> None:
    """Self-test on the same expression: ``sites`` (own tenant) is named, ``locations`` is not."""
    assert _parent_scoped_models_with_a_tenant(_inventory(), {col.SITES, col.LOCATIONS}) == ["sites: Site"]
