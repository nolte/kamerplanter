"""Per-write-path tenant-ownership tests for ArangoPestDetectionRepository (#517).

Solitary unit tests (MagicMock ``StandardDatabase``). The ``create`` path binds
a detection to a caller-supplied plant instance or planting run; a missing or
foreign reference must fail closed with :class:`NotFoundError` (→ 404) before any
document or edge is persisted.
"""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango.pest_detection_repository import ArangoPestDetectionRepository
from app.domain.models.pest_detection import PestDetection


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPestDetectionRepository(mock_db)


class TestCreateOwnership:
    def test_same_tenant_plant_succeeds(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = {"_key": "plant_1", "tenant_key": "tenant_anna"}
        mock_db.collection.return_value.insert.return_value = {
            "new": {"_key": "det_1", "tenant_key": "tenant_anna", "plant_instance_key": "plant_1"}
        }
        result = repo.create(PestDetection(tenant_key="tenant_anna", plant_instance_key="plant_1"))
        assert result.key == "det_1"

    def test_foreign_plant_raises_404_and_persists_nothing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = {"_key": "plant_1", "tenant_key": "tenant_bob"}
        with pytest.raises(NotFoundError):
            repo.create(PestDetection(tenant_key="tenant_anna", plant_instance_key="plant_1"))
        mock_db.collection.return_value.insert.assert_not_called()

    def test_missing_plant_raises_404(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        with pytest.raises(NotFoundError):
            repo.create(PestDetection(tenant_key="tenant_anna", plant_instance_key="plant_1"))
        mock_db.collection.return_value.insert.assert_not_called()

    def test_foreign_planting_run_raises_404(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = {"_key": "run_1", "tenant_key": "tenant_bob"}
        with pytest.raises(NotFoundError):
            repo.create(PestDetection(tenant_key="tenant_anna", planting_run_key="run_1"))
        mock_db.collection.return_value.insert.assert_not_called()

    def test_plant_agnostic_detection_needs_no_ownership_check(self, repo, mock_db):
        # The plant-agnostic entry point (no plant/run binding) persists without
        # an ownership lookup.
        mock_db.collection.return_value.insert.return_value = {"new": {"_key": "det_2", "tenant_key": "tenant_anna"}}
        result = repo.create(PestDetection(tenant_key="tenant_anna"))
        assert result.key == "det_2"
        mock_db.collection.return_value.get.assert_not_called()
