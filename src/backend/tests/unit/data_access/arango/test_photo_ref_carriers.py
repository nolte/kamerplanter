"""#1393 — ``PHOTO_REF_COLLECTIONS`` covers every model that can reference an attachment.

`ArangoAttachmentRepository.find_orphaned_task_photos` returns rows that
`cleanup_orphaned_task_photos` then **deletes**. It decides "nothing references
this" by looking in the collections named in ``PHOTO_REF_COLLECTIONS``, so a
carrier missing from that tuple is a photo destroyed while something still points
at it.

The tuple is hand-maintained — the mapping from a Pydantic model to its ArangoDB
collection is not declared anywhere a test can read mechanically — so the failure
mode is a *seventh* model gaining ``photo_refs`` and nobody thinking of this file.
This test is what makes that a red lane instead of a silent widening of what the
sweep may delete.

It compares model names, not collections, for the same reason: the model is where
the field is declared, and declaring it is the act that creates the hazard.
"""

from __future__ import annotations

import ast
import pathlib

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import PHOTO_REF_COLLECTIONS

_MODELS_ROOT = pathlib.Path(__file__).resolve().parents[4] / "app" / "domain" / "models"

#: Which collection each ``photo_refs``-carrying model is stored in.
#:
#: Maintained beside the tuple it explains: when this test fails because a model
#: gained the field, the fix is to decide the model's collection here **and** add it
#: to ``PHOTO_REF_COLLECTIONS`` — the two halves of the same decision, so neither
#: can be done alone.
_MODEL_TO_COLLECTION: dict[str, str] = {
    "Task": col.TASKS,
    "PlantInstance": col.PLANT_INSTANCES,
    "PlantDiaryEntry": col.PLANT_DIARY_ENTRIES,
    "HarvestObservation": col.HARVEST_OBSERVATIONS,
    "Inspection": col.INSPECTIONS,
    "StorageObservation": col.STORAGE_OBSERVATIONS,
}


def _models_declaring_photo_refs() -> set[str]:
    """Every class in ``app/domain/models`` with a ``photo_refs`` annotation.

    Read from the AST rather than by importing and inspecting: a class attribute
    with no default would not survive ``model_fields`` inspection uniformly across
    plain ``BaseModel`` and its subclasses here, and a grep would match the field
    named in a docstring — this repository has several such comments, and a sweep
    reporting prose as a finding is a failure mode it has paid for before.
    """
    found: set[str] = set()
    for path in sorted(_MODELS_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id == "photo_refs"
                ):
                    found.add(node.name)
    return found


def test_every_model_carrying_photo_refs_is_mapped():
    """A new carrier fails here, naming itself, before it can cost a photo."""
    unmapped = sorted(_models_declaring_photo_refs() - set(_MODEL_TO_COLLECTION))

    assert not unmapped, (
        "these models declare `photo_refs` and are not mapped to a collection:\n  "
        + "\n  ".join(unmapped)
        + "\n\nAdd each to _MODEL_TO_COLLECTION AND to PHOTO_REF_COLLECTIONS in "
        "app/data_access/arango/attachment_repository.py — the orphan sweep deletes "
        "what none of those collections references (#1393)."
    )


def test_no_mapping_outlives_its_model():
    """The other direction, so the map cannot grow into a list of dead names."""
    stale = sorted(set(_MODEL_TO_COLLECTION) - _models_declaring_photo_refs())

    assert not stale, (
        "these are mapped but no longer declare `photo_refs`; drop them from the map "
        "and consider dropping the collection from PHOTO_REF_COLLECTIONS:\n  " + "\n  ".join(stale)
    )


def test_the_sweep_looks_in_every_mapped_collection():
    """The load-bearing assertion: the map and the tuple the query uses agree.

    Split from the two above on purpose. Those keep the *map* honest against the
    models; this one keeps the *query* honest against the map, and they fail for
    different reasons — a model added to the map but not to the tuple is exactly the
    half-finished edit that leaves the sweep deleting referenced photos.
    """
    missing = sorted(set(_MODEL_TO_COLLECTION.values()) - set(PHOTO_REF_COLLECTIONS))

    assert not missing, (
        "the orphan sweep does not look in these collections, so a photo referenced "
        "from one of them would be deleted:\n  " + "\n  ".join(missing)
    )


def test_the_tuple_has_no_collection_nothing_maps_to():
    """An entry nothing maps to is either a typo or a carrier that lost its field."""
    unexplained = sorted(set(PHOTO_REF_COLLECTIONS) - set(_MODEL_TO_COLLECTION.values()))

    assert not unexplained, "PHOTO_REF_COLLECTIONS names collections no mapped model uses:\n  " + "\n  ".join(
        unexplained
    )


def test_the_set_is_not_empty():
    """A map emptied by a careless edit would make all four assertions above vacuous."""
    assert len(_MODEL_TO_COLLECTION) >= 6
    assert len(PHOTO_REF_COLLECTIONS) >= 6
