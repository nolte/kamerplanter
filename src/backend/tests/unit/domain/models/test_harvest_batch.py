"""Tests for the HarvestBatch model's batch_id normalisation (#740).

``batch_id`` is an optional user-facing lot label. A unique+sparse ArangoDB index
enforces uniqueness only for real values, so every blank input MUST persist as
``None`` — otherwise a second unlabelled batch collides on ``""``.
"""

from app.common.enums import HarvestType
from app.domain.models.harvest import HarvestBatch


class TestHarvestBatchIdNormalization:
    def test_empty_string_becomes_none(self):
        batch = HarvestBatch(batch_id="")
        assert batch.batch_id is None

    def test_whitespace_only_becomes_none(self):
        batch = HarvestBatch(batch_id="   ")
        assert batch.batch_id is None

    def test_default_is_none(self):
        batch = HarvestBatch()
        assert batch.batch_id is None

    def test_explicit_none_stays_none(self):
        batch = HarvestBatch(batch_id=None)
        assert batch.batch_id is None

    def test_real_value_is_preserved(self):
        batch = HarvestBatch(batch_id="LOT-42", harvest_type=HarvestType.FINAL)
        assert batch.batch_id == "LOT-42"

    def test_real_value_is_not_stripped(self):
        # Only fully-blank inputs collapse to None; internal/edge whitespace of a
        # real label is left to the caller (no silent trimming of meaningful ids).
        batch = HarvestBatch(batch_id=" LOT 7 ")
        assert batch.batch_id == " LOT 7 "
