"""REQ-010 P2 recognition — promote/demote a user pest image into the index.

Exercises the pure logic of ``_index_promoted`` / ``_retract_promoted`` against
patched DI providers, so no broker / inference service / object storage / DB is
needed. The Celery wrappers are thin best-effort shells over these helpers.

Coverage:
* feature flag off ⇒ clean no-op, nothing fetched, no client call;
* label resolved via the pest's ``detection_slug`` → ``PestTaxon.slug``;
* a pest *without* ``detection_slug`` ⇒ no-op (no recognition class);
* an unknown contribution ⇒ no-op;
* upsert is called with ``source="user_contributed"`` + contribution provenance,
  and the EXIF-stripped bytes from the attachment stream;
* retract deactivates via the provenance-matched prototype;
* the task wrapper swallows unexpected failures into a warning (admin flow safe).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import app.tasks.pest_image_tasks as task_mod
from app.common.enums import AttachmentCategory, PestImageStatus
from app.common.exceptions import NotFoundError
from app.domain.models.attachment import Attachment
from app.domain.models.ipm import Pest
from app.domain.models.pest_image import PestImageContribution

CONTRIB = "pic1"
TENANT = "tenant_anna"
PEST = "pest_spider_mite"
ATT = "att1"


def _contribution() -> PestImageContribution:
    return PestImageContribution(
        _key=CONTRIB,
        tenant_key=TENANT,
        pest_key=PEST,
        attachment_id=ATT,
        contributed_by="user_anna",
        status=PestImageStatus.PROMOTED,
        created_at=datetime.now(UTC),
    )


def _attachment() -> Attachment:
    return Attachment(
        _key=ATT,
        tenant_key=TENANT,
        mime_type="image/jpeg",
        byte_size=10,
        sha256="x" * 64,
        original_filename="mite.jpg",
        created_by="user_anna",
        category=AttachmentCategory.PEST_REFERENCE,
        storage_key=f"{TENANT}/{ATT}",
        created_at=datetime.now(UTC),
    )


def _pest(detection_slug: str | None) -> Pest:
    return Pest(
        _key=PEST,
        scientific_name="Tetranychus urticae",
        common_name="Spider Mites",
        detection_slug=detection_slug,
    )


def _wire(
    monkeypatch,
    *,
    enabled: bool = True,
    contribution: PestImageContribution | None = _contribution(),
    pest: Pest | None = None,
    pest_missing: bool = False,
    detection_slug: str | None = "spider_mite",
):
    settings = MagicMock()
    settings.pest_detection_enabled = enabled
    monkeypatch.setattr(task_mod, "settings", settings)

    repo = MagicMock()
    repo.get_by_key.return_value = contribution
    monkeypatch.setattr(task_mod, "get_pest_image_repo", lambda: repo)

    ipm = MagicMock()
    if pest_missing:
        ipm.get_pest.side_effect = NotFoundError("Pest", PEST)
    else:
        ipm.get_pest.return_value = pest if pest is not None else _pest(detection_slug)
    monkeypatch.setattr(task_mod, "get_ipm_service", lambda: ipm)

    attachment_service = MagicMock()
    attachment_service.get_attachment.return_value = _attachment()

    async def _open_stream(_attachment):
        async def _gen():
            yield b"clean-jpeg-bytes"

        return _gen()

    attachment_service.open_stream = _open_stream
    monkeypatch.setattr(task_mod, "get_attachment_service", lambda: attachment_service)

    client = MagicMock()
    client.upsert_prototype.return_value = {"status": "ok"}
    client.retract_prototype.return_value = 1
    monkeypatch.setattr(task_mod, "get_pest_inference_client", lambda: client)

    return repo, ipm, attachment_service, client


class TestIndexPromoted:
    def test_feature_off_is_noop_without_any_lookup(self, monkeypatch):
        repo, _ipm, attachments, client = _wire(monkeypatch, enabled=False)

        outcome = task_mod._index_promoted(CONTRIB)

        assert outcome == {"status": "noop", "reason": "pest_detection_disabled"}
        repo.get_by_key.assert_not_called()
        client.upsert_prototype.assert_not_called()

    def test_unknown_contribution_is_noop(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, contribution=None)

        outcome = task_mod._index_promoted(CONTRIB)

        assert outcome["status"] == "noop"
        assert outcome["reason"] == "contribution_not_found"
        client.upsert_prototype.assert_not_called()

    def test_no_detection_slug_is_noop(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, detection_slug=None)

        outcome = task_mod._index_promoted(CONTRIB)

        assert outcome["status"] == "noop"
        assert outcome["reason"] == "no_detection_slug"
        client.upsert_prototype.assert_not_called()

    def test_unknown_slug_is_noop(self, monkeypatch):
        # A detection_slug that maps to no PestTaxon cannot be a recognition class.
        _repo, _ipm, _att, client = _wire(monkeypatch, detection_slug="not_a_real_taxon")

        outcome = task_mod._index_promoted(CONTRIB)

        assert outcome["status"] == "noop"
        assert outcome["reason"] == "no_detection_slug"
        client.upsert_prototype.assert_not_called()

    def test_missing_pest_is_noop(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, pest_missing=True)

        outcome = task_mod._index_promoted(CONTRIB)

        assert outcome["status"] == "noop"
        assert outcome["reason"] == "no_detection_slug"
        client.upsert_prototype.assert_not_called()

    def test_upserts_user_contributed_prototype_with_provenance(self, monkeypatch):
        _repo, _ipm, attachments, client = _wire(monkeypatch, detection_slug="spider_mite")

        outcome = task_mod._index_promoted(CONTRIB)

        assert outcome == {"status": "indexed", "label": "spider_mite", "contribution_key": CONTRIB}
        # Bytes resolved against the owning tenant.
        attachments.get_attachment.assert_called_once_with(ATT, TENANT)
        client.upsert_prototype.assert_called_once()
        args, kwargs = client.upsert_prototype.call_args
        # The EXIF-stripped bytes from the attachment stream are sent.
        assert args[0] == b"clean-jpeg-bytes"
        # Label is the detection_slug → taxon slug; category from the taxon.
        assert kwargs["label"] == "spider_mite"
        assert kwargs["category"] == "pest"
        # Provenance: user-contributed + contribution key + owning tenant.
        assert kwargs["source"] == task_mod.USER_CONTRIBUTED_SOURCE
        assert kwargs["source_record_id"] == CONTRIB
        assert TENANT in kwargs["source_url"]
        assert CONTRIB in kwargs["source_url"]


class TestRetractPromoted:
    def test_feature_off_is_noop(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, enabled=False)

        outcome = task_mod._retract_promoted(CONTRIB)

        assert outcome == {"status": "noop", "reason": "pest_detection_disabled"}
        client.retract_prototype.assert_not_called()

    def test_no_detection_slug_is_noop(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, detection_slug=None)

        outcome = task_mod._retract_promoted(CONTRIB)

        assert outcome["status"] == "noop"
        client.retract_prototype.assert_not_called()

    def test_deactivates_provenance_matched_prototype(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, detection_slug="spider_mite")

        outcome = task_mod._retract_promoted(CONTRIB)

        assert outcome == {"status": "retracted", "label": "spider_mite", "deactivated": 1}
        client.retract_prototype.assert_called_once_with(
            label="spider_mite",
            source=task_mod.USER_CONTRIBUTED_SOURCE,
            source_record_id=CONTRIB,
        )


class TestTaskWrapper:
    def test_index_task_swallows_unexpected_error(self, monkeypatch):
        _repo, _ipm, _att, client = _wire(monkeypatch, detection_slug="spider_mite")
        client.upsert_prototype.side_effect = ValueError("boom")

        # Call the underlying function (bind=True → pass a dummy self).
        outcome = task_mod.index_promoted_pest_image_task.run(CONTRIB)

        assert outcome["status"] == "error"
        assert outcome["reason"] == "ValueError"

    def test_index_task_returns_outcome_on_success(self, monkeypatch):
        _wire(monkeypatch, detection_slug="spider_mite")

        outcome = task_mod.index_promoted_pest_image_task.run(CONTRIB)

        assert outcome["status"] == "indexed"
        assert outcome["label"] == "spider_mite"

    def test_retract_task_returns_outcome_on_success(self, monkeypatch):
        _wire(monkeypatch, detection_slug="spider_mite")

        outcome = task_mod.retract_promoted_pest_image_task.run(CONTRIB)

        assert outcome["status"] == "retracted"
