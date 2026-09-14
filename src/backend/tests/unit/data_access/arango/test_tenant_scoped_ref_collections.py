"""#1393 — the tenant narrowing may only name collections that carry ``tenant_key``.

``unreferenced_among`` decides which attachments get **deleted**, and it now narrows
its reference scan to the caller's tenant so it stops reading the whole installation
from inside an interactive request.

The narrowing is emitted as ``FILTER d.tenant_key == @ref_tenant_key``. ArangoDB is
schemaless, so on a collection whose documents have no such field that compares
``null`` against the tenant key, matches nothing, and the collection contributes **no
references at all** — it stops protecting every photo it alone protects. There is no
error, no empty result, no failing request: the delete route simply starts answering
"safe to delete" for photos that collection still links.

That makes membership of ``TENANT_SCOPED_REF_COLLECTIONS`` load-bearing in the
destructive direction, and it is exactly the kind of fact a reader adds by eye — the
field is present on most models, so "this one probably has it too" is right four times
out of five. This file reads it off the models instead.

The companion check is in ``test_photo_ref_carriers.py``, which pins the carrier lists
themselves. Together they mean a new carrier, a new reference field, or a wrong guess
about tenant scoping fails a fast lane rather than silently widening what may be
deleted.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.data_access.arango import attachment_repository as repo

_MODELS_ROOT = Path(repo.__file__).resolve().parents[2] / "domain" / "models"

#: Model class → collection, for every collection either reference list names.
#:
#: Spelled out rather than derived, because deriving it from the same constants the
#: production code uses is how a guard ends up agreeing with the bug it is meant to
#: catch. A model renamed out from under this mapping fails the completeness check
#: below rather than quietly dropping a collection from the sweep.
_MODEL_FOR_COLLECTION: dict[str, str] = {
    "tasks": "Task",
    "plant_instances": "PlantInstance",
    "plant_diary_entries": "PlantDiaryEntry",
    "harvest_observations": "HarvestObservation",
    "inspections": "Inspection",
    "storage_observations": "StorageObservation",
    "pest_image_contributions": "PestImageContribution",
    "pests": "Pest",
}


def _declares_tenant_key(class_name: str) -> bool | None:
    """Does this model declare a ``tenant_key`` field? ``None`` if not found at all."""
    for path in sorted(_MODELS_ROOT.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return any(
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id == "tenant_key"
                    for statement in node.body
                )
    return None


def _scanned_collections() -> set[str]:
    extra = {collection for collection, _field in repo.ATTACHMENT_REF_FIELDS}
    return set(repo.PHOTO_REF_COLLECTIONS) | extra


def test_every_scanned_collection_has_a_known_model():
    """The mapping above must stay complete, or the real check silently shrinks.

    Without this, adding a carrier and forgetting to map it here would leave it
    unchecked — and an unchecked collection is precisely one nobody has confirmed
    carries ``tenant_key``.
    """
    unmapped = _scanned_collections() - set(_MODEL_FOR_COLLECTION)
    assert not unmapped, (
        f"Collections scanned for attachment references but not mapped to a model here: "
        f"{sorted(unmapped)}. Add the mapping so the tenant-scoping check covers them."
    )
    missing_models = sorted(name for name in _MODEL_FOR_COLLECTION.values() if _declares_tenant_key(name) is None)
    assert not missing_models, (
        f"Model classes named here but not found under {_MODELS_ROOT}: {missing_models}. "
        "A renamed model would otherwise make this file check nothing."
    )


@pytest.mark.parametrize("collection", sorted(_MODEL_FOR_COLLECTION))
def test_tenant_scoped_ref_collections_match_the_models(collection: str):
    declared = collection in repo.TENANT_SCOPED_REF_COLLECTIONS
    actual = _declares_tenant_key(_MODEL_FOR_COLLECTION[collection])
    if declared and not actual:
        pytest.fail(
            f"{collection!r} is in TENANT_SCOPED_REF_COLLECTIONS but "
            f"{_MODEL_FOR_COLLECTION[collection]} declares no tenant_key. The delete route "
            f"emits FILTER d.tenant_key == @ref_tenant_key for it, which matches nothing, "
            f"so {collection!r} now protects no photo at all — attachments it still "
            f"references become deletable (#1393)."
        )
    if actual and not declared:
        pytest.fail(
            f"{_MODEL_FOR_COLLECTION[collection]} declares tenant_key but {collection!r} is not "
            f"in TENANT_SCOPED_REF_COLLECTIONS, so the interactive delete route still scans it "
            f"across every tenant. Safe, but it is the cost the narrowing exists to remove — "
            f"add it, or record here why this collection must stay installation-wide."
        )


def test_the_nightly_sweep_is_not_narrowed():
    """The installation-wide sweep must keep reading every tenant's references.

    It has no tenant to narrow to. If the narrowing ever leaked into its prelude the
    bind parameter would be missing and the query would fail loudly — but a *default*
    of ``tenant_scoped=True`` plus a stray bind would make it quietly sweep one
    tenant's references against every tenant's photos, which deletes other tenants'
    data. Asserted on the generated AQL, because that is what the database runs.
    """
    sweep_aql = repo.ArangoAttachmentRepository._aql_referenced_prelude(
        repo.ArangoAttachmentRepository.__new__(repo.ArangoAttachmentRepository)
    )
    assert "@ref_tenant_key" not in sweep_aql

    scoped_aql = repo.ArangoAttachmentRepository._aql_referenced_prelude(
        repo.ArangoAttachmentRepository.__new__(repo.ArangoAttachmentRepository), tenant_scoped=True
    )
    # Counted per *scan site*, not per collection: ``plant_instances`` is read twice
    # (once for ``photo_refs``, once for ``cover_photo_ref``) and both reads need the
    # filter. Expecting one per collection was wrong and, had it been asserted the
    # other way round, would have passed with one of those two reads unnarrowed.
    sites = [
        collection
        for collection in list(repo.PHOTO_REF_COLLECTIONS)
        + [collection for collection, _field in repo.ATTACHMENT_REF_FIELDS]
        if collection in repo.TENANT_SCOPED_REF_COLLECTIONS
    ]
    assert scoped_aql.count("@ref_tenant_key") == len(sites), (
        f"Expected the tenant filter on all {len(sites)} tenant-scoped scan sites "
        f"({sorted(set(sites))}), found {scoped_aql.count('@ref_tenant_key')}."
    )
