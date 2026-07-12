"""Unit tests for ArangoPlantDiagnosisRepository (REQ-038).

Solitary unit tests: the injected ``StandardDatabase`` is doubled with MagicMock.
Assertions target the tenant filter guards, the emitted AQL bind_vars and the
provenance edges. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import DiagnosisCategory
from app.data_access.arango import collections as col
from app.data_access.arango.plant_diagnosis_repository import ArangoPlantDiagnosisRepository
from app.domain.interfaces.cv_diagnosis_adapter import DiseaseClassification
from app.domain.models.plant_diagnosis_request import PlantDiagnosisRequest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPlantDiagnosisRepository(mock_db)


def _request(**overrides) -> PlantDiagnosisRequest:
    base = {
        "tenant_key": "tenant_anna",
        "user_key": "user_anna",
        "image_hash": "sha256:abc",
    }
    base.update(overrides)
    return PlantDiagnosisRequest(**base)


class TestTenantGuards:
    def test_get_rejects_empty_tenant_key(self, repo):
        with pytest.raises(ValueError, match="tenant"):
            repo.get("diag_1", "")

    def test_list_for_user_rejects_empty_tenant_key(self, repo):
        with pytest.raises(ValueError, match="tenant"):
            repo.list_for_user("", "user_anna")

    def test_mark_confirmed_rejects_empty_tenant_key(self, repo):
        with pytest.raises(ValueError, match="tenant"):
            repo.mark_confirmed("diag_1", "", confirmed_labels=["x"])

    def test_get_foreign_tenant_returns_none(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = {
            "_key": "diag_1",
            "tenant_key": "tenant_bob",  # different tenant
            "user_key": "u",
            "image_hash": "sha256:x",
        }
        assert repo.get("diag_1", "tenant_anna") is None


class TestListForUser:
    def test_emits_tenant_and_user_bind_vars(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        repo.list_for_user("tenant_anna", "user_anna", limit=5)
        _, kwargs = mock_db.aql.execute.call_args
        bind = kwargs["bind_vars"]
        assert bind["tenant_key"] == "tenant_anna"
        assert bind["user_key"] == "user_anna"
        assert bind["limit"] == 5


class TestCreateEdges:
    def test_create_wires_plant_and_found_edges(self, repo, mock_db):
        coll = mock_db.collection.return_value
        # #517 — the create path now verifies the plant instance's tenant
        # ownership; stub the lookup to return an own-tenant plant.
        coll.get.return_value = {"_key": "plant_1", "tenant_key": "tenant_anna"}
        coll.insert.return_value = {
            "new": {"_key": "diag_1", "tenant_key": "tenant_anna", "user_key": "u", "image_hash": "sha256:x"}
        }
        request = _request(
            plant_instance_key="plant_1",
            classifications=[
                DiseaseClassification(
                    label="tomato_early_blight",
                    category=DiagnosisCategory.DISEASE,
                    probability=0.9,
                    matched_disease_key="disease_early_blight",
                ),
                DiseaseClassification(
                    label="nitrogen_deficiency",
                    category=DiagnosisCategory.DEFICIENCY,
                    probability=0.2,
                ),  # no matched key → no edge
            ],
        )
        repo.create(request)

        edge_targets = [c.args[0].get("_to") for c in coll.insert.call_args_list if "_to" in c.args[0]]
        assert f"{col.PLANT_INSTANCES}/plant_1" in edge_targets
        assert f"{col.DISEASES}/disease_early_blight" in edge_targets
        # the unmatched deficiency produced no found-edge
        assert not any(t.startswith(f"{col.PESTS}/") for t in edge_targets)


class TestCreateOwnershipGuard:
    """#517 — the caller-supplied plant instance must be own-tenant (fail-closed 404)."""

    def test_foreign_plant_instance_raises_404_and_persists_nothing(self, repo, mock_db):
        from app.common.exceptions import NotFoundError

        coll = mock_db.collection.return_value
        coll.get.return_value = {"_key": "plant_1", "tenant_key": "tenant_bob"}
        with pytest.raises(NotFoundError):
            repo.create(_request(plant_instance_key="plant_1"))
        coll.insert.assert_not_called()

    def test_missing_plant_instance_raises_404(self, repo, mock_db):
        from app.common.exceptions import NotFoundError

        coll = mock_db.collection.return_value
        coll.get.return_value = None
        with pytest.raises(NotFoundError):
            repo.create(_request(plant_instance_key="plant_1"))
        coll.insert.assert_not_called()

    def test_foreign_harvest_observation_raises_404(self, repo, mock_db):
        from app.common.exceptions import NotFoundError

        coll = mock_db.collection.return_value
        coll.get.return_value = {"_key": "obs_1", "tenant_key": "tenant_bob"}
        with pytest.raises(NotFoundError):
            repo.create(_request(harvest_observation_key="obs_1"))
        coll.insert.assert_not_called()
