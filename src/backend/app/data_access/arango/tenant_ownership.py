"""Shared tenant-ownership guard for caller-supplied foreign entity keys (#517).

Create/link write paths across the codebase persist foreign document keys that
the caller supplies — ``plant_instance_key`` / ``plant_key``,
``planting_run_key``, ``harvest_observation_key``, InvenTree ``entity_key`` and
similar. Reads are strictly tenant-scoped, so a dangling or foreign key that was
written into an *own-tenant* record cannot be read back across the boundary
today; this is therefore **not** an active cross-tenant leak. It is, however, a
latent data-integrity gap and a defense-in-depth weakness: the day any code path
traverses one of these references *backwards* without a tenant filter, an
unverified foreign key becomes a real leak (SEC-B4).

This module lifts the reference implementation
:meth:`ArangoInvenTreeRepository.verify_linkable_entity` (PR #513) into a single,
reusable guard so every domain performs the **same** existence +
tenant-ownership + allowlist check instead of re-implementing it. On any
violation the guard fails **closed** with :class:`NotFoundError` (→ HTTP 404),
never a ``403``-with-detail — so the existence of a foreign key is never
disclosed (no cross-tenant oracle).

Globally-seeded catalog rows (empty ``tenant_key`` — e.g. the shared fertilizer
catalog) stay referenceable, mirroring the hybrid-catalog read visibility.
"""

from __future__ import annotations

from collections.abc import Iterable

from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col

#: Allowlist of collections whose documents may be ownership-verified as a
#: caller-supplied foreign reference on a write path. Constraining the handle set
#: is a defense-in-depth guard: the verifier must never dial an arbitrary,
#: caller-influenced collection name (mirrors
#: :class:`~app.common.enums.LinkableEntityCollection` for the InvenTree case and
#: extends it with the plant-lifecycle references used by IPM / pest-detection /
#: CV-diagnosis write paths).
OWNERSHIP_VERIFIABLE_COLLECTIONS: frozenset[str] = frozenset(
    {
        col.PLANT_INSTANCES,
        col.PLANTING_RUNS,
        col.HARVEST_OBSERVATIONS,
        col.FERTILIZERS,
        col.TANKS,
        col.EQUIPMENT,
    }
)


def verify_entity_ownership(
    db: StandardDatabase,
    collection: str,
    key: str,
    tenant_key: str,
    *,
    entity_name: str | None = None,
) -> None:
    """Fail closed (404) unless ``collection/key`` exists and is visible to ``tenant_key``.

    Use on **write** paths that persist a caller-supplied foreign reference. An
    entity that does not exist, or that belongs to a *different* tenant, must
    never be linked — otherwise a caller could point a record/edge at a foreign
    or dangling key (graph pollution / latent cross-tenant leak, SEC-B4).

    Args:
        db: The ArangoDB handle (the repository's ``self._db``).
        collection: The collection the reference targets. Must be in
            :data:`OWNERSHIP_VERIFIABLE_COLLECTIONS` (defense-in-depth).
        key: The caller-supplied document key to verify.
        tenant_key: The caller's tenant. Must be non-empty (a scoped write
            without a tenant cannot be ownership-verified — SEC-B4).
        entity_name: Optional human-readable name for the raised
            :class:`NotFoundError` (defaults to ``collection``).

    Raises:
        ValueError: ``tenant_key`` is empty (programming/scoping error, mirrors
            :meth:`BaseArangoRepository._require_tenant_key`).
        NotFoundError: the collection is off-allowlist, the document is absent,
            or it belongs to another tenant — all mapped to HTTP 404 so a
            foreign key's existence is never disclosed (no oracle).
    """
    if not tenant_key:
        raise ValueError(
            "verify_entity_ownership is tenant-scoped and requires a non-empty tenant_key (SEC-B4 tenant isolation)."
        )
    name = entity_name or collection
    if collection not in OWNERSHIP_VERIFIABLE_COLLECTIONS:
        # Never dial an off-allowlist collection handle.
        raise NotFoundError(name, key)
    doc = db.collection(collection).get(key)
    if doc is None:
        raise NotFoundError(name, key)
    doc_tenant = doc.get("tenant_key", "") or ""
    if doc_tenant not in ("", tenant_key):
        raise NotFoundError(name, key)


def verify_entities_ownership(
    db: StandardDatabase,
    collection: str,
    keys: Iterable[str],
    tenant_key: str,
    *,
    entity_name: str | None = None,
) -> None:
    """Batch variant of :func:`verify_entity_ownership`.

    Verifies every distinct, non-empty key in ``keys`` (order-preserving dedup),
    failing closed on the first violation. Empty/falsy keys are skipped — there
    is nothing to verify — so callers may pass an optional-key list directly.
    """
    seen: set[str] = set()
    for key in keys:
        if not key or key in seen:
            continue
        seen.add(key)
        verify_entity_ownership(db, collection, key, tenant_key, entity_name=entity_name)
