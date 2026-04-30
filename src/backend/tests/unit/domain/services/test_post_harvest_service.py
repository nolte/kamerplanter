"""REQ-008 Post-Harvest scaffold tests."""

import pytest

from app.domain.services.post_harvest_service import PostHarvestService


class TestPostHarvestServiceScaffold:
    def test_list_for_batch_raises_until_follow_up(self):
        svc = PostHarvestService()
        with pytest.raises(NotImplementedError, match="pending follow-up"):
            svc.list_for_batch("batch-1")

    def test_advance_stage_raises_until_follow_up(self):
        svc = PostHarvestService()
        with pytest.raises(NotImplementedError, match="pending follow-up"):
            svc.advance_stage("ph-1", "curing")


class TestPostHarvestModel:
    def test_default_stage_is_drying(self):
        from app.domain.models.post_harvest import PostHarvestBatch

        b = PostHarvestBatch(harvest_batch_key="hb-1")
        assert b.stage == "drying"
