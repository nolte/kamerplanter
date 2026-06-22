"""REQ-010 — PestImageContribution model invariants.

Focus: the ``is_active`` curation field is backward compatible — a document
written before the field existed (no ``is_active`` key) must deserialize as
*active* so an existing contribution stays visible after the migration.
"""

from __future__ import annotations

from app.common.enums import PestImageStatus
from app.domain.models.pest_image import PestImageContribution


def _base_doc() -> dict:
    return {
        "_key": "pic1",
        "tenant_key": "t1",
        "pest_key": "p1",
        "attachment_id": "att1",
        "contributed_by": "u1",
    }


def test_is_active_defaults_to_true_for_legacy_doc():
    # No ``is_active`` key (pre-curation document) → treated as active.
    contribution = PestImageContribution(**_base_doc())
    assert contribution.is_active is True
    assert contribution.status == PestImageStatus.PRIVATE


def test_is_active_false_round_trips():
    doc = {**_base_doc(), "is_active": False}
    contribution = PestImageContribution(**doc)
    assert contribution.is_active is False


def test_is_active_serializes():
    contribution = PestImageContribution(**_base_doc())
    dumped = contribution.model_dump()
    assert dumped["is_active"] is True
