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
from app.data_access.arango.attachment_repository import (
    ATTACHMENT_REF_FIELDS,
    PHOTO_REF_COLLECTIONS,
)

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
    # ``rglob``, not ``glob``: there are no subpackages under ``models/`` today, so
    # the two behave alike — and the first model added in one would have gained
    # ``photo_refs`` without turning this lane red, which is the single failure mode
    # this file exists to prevent.
    found: set[str] = set()
    for path in sorted(_MODELS_ROOT.rglob("*.py")):
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


# ── Every field shaped like an attachment reference, not just ``photo_refs`` ──
#
# The sweep originally checked ``photo_refs`` alone, and review pointed out that the
# principle behind it ("a destructive query may not rest on a category assumption")
# was being applied to one field name. Three others hold attachment ids, and a
# scan for the *shape* is what stops a fourth appearing unnoticed.

#: Fields that look like an attachment reference and are not one. Each names why,
#: so the list cannot quietly grow into "everything the scan complained about".
_NOT_AN_ATTACHMENT_REFERENCE: dict[str, str] = {
    "Task.source_run_ref": "points at a PlantingRun, not an attachment",
    "Task.external_ref": "an external system's identifier (InvenTree et al.), not a document key",
    "WeatherSourcePublicConfig.api_key_ref": "names a secret in the key store, not an attachment",
    # Holds real attachment ids, and still adds no reference the sweep does not
    # already see: ``PlantDiaryService`` refuses an analysis whose
    # ``analyzed_photo_ids`` are not a subset of the entry's own ``photo_refs``
    # (``plant_diary_service.py`` — "contains ids that are not attached to this
    # entry"), and ``plant_diary_entries`` is a scanned carrier. Adding it to
    # ``ATTACHMENT_REF_FIELDS`` would cost a tenth collection pass to learn nothing.
    #
    # This is the field the widened detector found and the old ``*_ref`` naming rule
    # could not — it is why the rule was widened rather than merely documented.
    "DiaryAnalysis.analyzed_photo_ids": (
        "validated to be a subset of the entry's photo_refs, which is already scanned"
    ),
}

#: Fields the sweep resolves through ``ATTACHMENT_REF_FIELDS`` rather than through
#: ``photo_refs``.
_RESOLVED_BY_FIELD_TUPLE = {
    "PlantInstance.cover_photo_ref",
    "PestImageContribution.attachment_id",
    "Pest.reference_image_refs",
}


#: Word stems that make a field name *about* an attachment.
#:
#: The detector below used to accept only ``*_ref`` / ``*_refs`` / ``attachment_id``,
#: which is a guess about naming rather than about meaning — and this file is the only
#: mechanical protection standing in front of a query that **deletes** attachments.
#: A field called ``gallery_ids``, ``photo_id``, ``cover_image`` or ``media_keys``
#: would have held attachment ids while every test here stayed green, and the sweep
#: would have deleted around it. That is the "the measuring tool has the gap, not the
#: guard" class this PR already paid four review rounds for.
_MEDIA_TOKENS: tuple[str, ...] = (
    "photo",
    "image",
    "picture",
    "media",
    "attachment",
    "thumbnail",
    "gallery",
)

#: Suffixes that make such a field a *reference* rather than a value.
#:
#: Required alongside a media token, because the token alone is far too coarse in this
#: domain: measured, it also matches ``photoperiod_type``, ``photosynthesis_temp_opt_c``
#: and ``biofilter_media_ssa_m2_per_m3`` — 27 fields, almost all of them physics. With
#: the suffix the detector grows by exactly one field over the old rule, and that one
#: is a real carrier the old rule could not see.
_REFERENCE_SUFFIXES: tuple[str, ...] = ("_id", "_ids", "_ref", "_refs", "_key", "_keys")


def _reference_shaped_fields() -> set[str]:
    """``<Class>.<field>`` for every annotation that reads like an attachment ref."""
    found: set[str] = set()
    for path in sorted(_MODELS_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if not (isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)):
                    continue
                name = statement.target.id
                lowered = name.lower()
                by_suffix = name.endswith(("_ref", "_refs")) or name == "attachment_id"
                by_meaning = any(token in lowered for token in _MEDIA_TOKENS) and name.endswith(_REFERENCE_SUFFIXES)
                if by_suffix or by_meaning:
                    found.add(f"{node.name}.{name}")
    return found


def test_the_detector_sees_a_field_the_old_naming_rule_would_have_missed():
    """The detector's own falsification, because a detector cannot test itself.

    Every other assertion in this file consumes ``_reference_shaped_fields()``. If it
    silently stopped matching, they would all pass over an empty set — the failure
    mode this whole file exists to prevent, one layer up. So: a name that carries no
    ``_ref`` suffix and is nonetheless an attachment reference must be found.
    """
    found = _reference_shaped_fields()
    assert "DiaryAnalysis.analyzed_photo_ids" in found, (
        "the detector stopped recognising media-shaped id fields; every assertion in "
        "this file now passes over a smaller set than it thinks"
    )
    assert "PlantInstance.cover_photo_ref" in found, "the original suffix rule was lost"
    # The coarse half must stay bounded: a bare media token matches physics terms like
    # ``photoperiod_type``. Measured, the token-only rule found 36 fields to this one's 13.
    assert "PhaseSequence.photoperiod_type" not in found
    assert "AquaponicSystem.biofilter_media_ssa_m2_per_m3" not in found


def test_every_reference_shaped_field_is_accounted_for():
    """A new ``*_ref`` field fails here until someone says which kind it is.

    Three answers are allowed: it is ``photo_refs`` on a mapped carrier, it is in
    ``ATTACHMENT_REF_FIELDS``, or it is listed above as not an attachment reference
    *with a reason*. Anything else is a field the sweep might be deleting around.
    """
    photo_ref_fields = {f"{model}.photo_refs" for model in _MODEL_TO_COLLECTION}
    accounted = photo_ref_fields | _RESOLVED_BY_FIELD_TUPLE | set(_NOT_AN_ATTACHMENT_REFERENCE)

    unaccounted = sorted(_reference_shaped_fields() - accounted)

    assert not unaccounted, (
        "these fields look like attachment references and nothing says what they are:\n  "
        + "\n  ".join(unaccounted)
        + "\n\nEither add the field to ATTACHMENT_REF_FIELDS (so the orphan sweep stops "
        "deleting what it references) or list it in _NOT_AN_ATTACHMENT_REFERENCE with a "
        "reason (#1393)."
    )


def test_the_field_tuple_and_the_expectation_agree():
    """The tuple the query uses matches what this file claims it covers."""
    declared = {field for _collection, field in ATTACHMENT_REF_FIELDS}
    expected = {name.split(".", 1)[1] for name in _RESOLVED_BY_FIELD_TUPLE}

    assert declared == expected, (
        f"ATTACHMENT_REF_FIELDS covers {sorted(declared)} while this file expects "
        f"{sorted(expected)} — one of the two was edited alone"
    )


def test_no_exclusion_outlives_its_field():
    """An excuse for a field that no longer exists is an excuse nobody is checking."""
    stale = sorted(set(_NOT_AN_ATTACHMENT_REFERENCE) - _reference_shaped_fields())

    assert not stale, "these are excused but no longer exist:\n  " + "\n  ".join(stale)


def test_the_scan_actually_finds_something():
    """The control: a scan matching nothing would pass all three tests above."""
    found = _reference_shaped_fields()

    assert len(found) >= 10, f"the reference-shaped scan found only {len(found)} fields"
    assert "Task.photo_refs" in found
