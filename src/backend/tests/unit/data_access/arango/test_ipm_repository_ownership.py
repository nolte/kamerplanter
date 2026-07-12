"""Per-write-path tenant-ownership tests for ArangoIpmRepository (#517).

Solitary unit tests (MagicMock ``StandardDatabase``). Each write path that
persists a caller-supplied plant-instance reference must reject a missing or
foreign key with :class:`NotFoundError` (→ 404, no cross-tenant oracle) and must
NOT persist anything in that case.
"""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.domain.models.ipm import Inspection, TreatmentApplication


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoIpmRepository(mock_db)


def _own_plant(db):
    db.collection.return_value.get.return_value = {"_key": "plant_1", "tenant_key": "tenant_anna"}


def _foreign_plant(db):
    db.collection.return_value.get.return_value = {"_key": "plant_1", "tenant_key": "tenant_bob"}


def _missing_plant(db):
    db.collection.return_value.get.return_value = None


class TestCreateInspection:
    def test_same_tenant_succeeds(self, repo, mock_db):
        _own_plant(mock_db)
        mock_db.collection.return_value.insert.return_value = {
            "new": {"_key": "insp_1", "tenant_key": "tenant_anna", "plant_key": "plant_1"}
        }
        result = repo.create_inspection(Inspection(tenant_key="tenant_anna", plant_key="plant_1"))
        assert result.key == "insp_1"

    def test_foreign_plant_raises_404_and_persists_nothing(self, repo, mock_db):
        _foreign_plant(mock_db)
        with pytest.raises(NotFoundError):
            repo.create_inspection(Inspection(tenant_key="tenant_anna", plant_key="plant_1"))
        mock_db.collection.return_value.insert.assert_not_called()

    def test_missing_plant_raises_404(self, repo, mock_db):
        _missing_plant(mock_db)
        with pytest.raises(NotFoundError):
            repo.create_inspection(Inspection(tenant_key="tenant_anna", plant_key="plant_1"))
        mock_db.collection.return_value.insert.assert_not_called()


class TestCreateTreatmentApplication:
    def test_same_tenant_succeeds(self, repo, mock_db):
        _own_plant(mock_db)
        mock_db.collection.return_value.insert.return_value = {
            "new": {"_key": "ta_1", "tenant_key": "tenant_anna", "plant_key": "plant_1", "treatment_key": "tr_1"}
        }
        result = repo.create_treatment_application(
            TreatmentApplication(tenant_key="tenant_anna", plant_key="plant_1", treatment_key="tr_1")
        )
        assert result.key == "ta_1"

    def test_foreign_plant_raises_404_and_persists_nothing(self, repo, mock_db):
        _foreign_plant(mock_db)
        with pytest.raises(NotFoundError):
            repo.create_treatment_application(
                TreatmentApplication(tenant_key="tenant_anna", plant_key="plant_1", treatment_key="tr_1")
            )
        mock_db.collection.return_value.insert.assert_not_called()

    def test_missing_plant_raises_404(self, repo, mock_db):
        _missing_plant(mock_db)
        with pytest.raises(NotFoundError):
            repo.create_treatment_application(
                TreatmentApplication(tenant_key="tenant_anna", plant_key="plant_1", treatment_key="tr_1")
            )
        mock_db.collection.return_value.insert.assert_not_called()
