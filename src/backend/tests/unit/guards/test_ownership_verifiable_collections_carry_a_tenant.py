"""#2107 (MT-010) — a collection is ownership-verifiable only if its documents carry a tenant.

:func:`~app.data_access.arango.tenant_ownership.verify_entity_ownership` reads
``doc.get("tenant_key", "") or ""`` and admits ``""`` as the global catalogue arm.
For a collection whose model has **no** ``tenant_key`` every document reads as
``""`` — so the guard does not merely do nothing, it *admits every tenant's row*
as if it were a global seed. ``HARVEST_OBSERVATIONS`` sat on the allowlist in
exactly that state (``HarvestObservation`` is tenant-resolved through its plant);
it was inert only because no application path sets
``PlantDiagnosisRequest.harvest_observation_key``.

The rule: every collection on
:data:`~app.data_access.arango.tenant_ownership.OWNERSHIP_VERIFIABLE_COLLECTIONS`
maps (through :data:`~app.data_access.arango.collection_entity_names.COLLECTION_ENTITY_MODELS`)
to a model that declares ``tenant_key``. A collection that is tenant-resolved
through a parent needs a parent-anchored check, not this one.
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.data_access.arango.collection_entity_names import COLLECTION_ENTITY_MODELS
from app.data_access.arango.tenant_ownership import OWNERSHIP_VERIFIABLE_COLLECTIONS


def _without_a_tenant(collections: frozenset[str] | set[str]) -> list[str]:
    """Allowlisted collections whose model does not declare ``tenant_key`` (or has no model at all)."""
    return sorted(
        name
        for name in collections
        if name not in COLLECTION_ENTITY_MODELS or "tenant_key" not in COLLECTION_ENTITY_MODELS[name].model_fields
    )


def test_every_ownership_verifiable_collection_carries_a_tenant() -> None:
    assert _without_a_tenant(OWNERSHIP_VERIFIABLE_COLLECTIONS) == [], (
        "These collections are on OWNERSHIP_VERIFIABLE_COLLECTIONS but their model has no tenant_key, "
        "so verify_entity_ownership reads every document as a global row and admits it for any tenant. "
        "Anchor the check on the parent instead (#2107)."
    )


def test_the_rule_sees_a_parent_scoped_collection_and_passes_an_owned_one() -> None:
    """Self-test on the same expression: a known parent-scoped collection is named, an owned one is not."""
    assert _without_a_tenant({col.HARVEST_OBSERVATIONS, col.BOTANICAL_FAMILIES, col.PLANT_INSTANCES, "unmapped"}) == [
        col.BOTANICAL_FAMILIES,
        col.HARVEST_OBSERVATIONS,
        "unmapped",
    ]


def test_the_allowlist_is_not_vacuous() -> None:
    assert {col.PLANT_INSTANCES, col.PLANTING_RUNS, col.FERTILIZERS, col.CULTIVARS} <= OWNERSHIP_VERIFIABLE_COLLECTIONS
