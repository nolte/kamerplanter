"""Unit tests for the shared tenant-ownership guard (#517).

Solitary unit tests: the ``StandardDatabase`` is doubled with MagicMock. The
guard must fail **closed** with :class:`NotFoundError` (→ HTTP 404, never a
403-with-detail) on a missing, foreign or off-allowlist reference so a foreign
key's existence is never disclosed (no cross-tenant oracle, SEC-B4).
"""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.tenant_ownership import (
    OWNERSHIP_VERIFIABLE_COLLECTIONS,
    verify_entities_ownership,
    verify_entity_ownership,
)


@pytest.fixture
def db():
    return MagicMock()


def _returns(db, doc):
    db.collection.return_value.get.return_value = doc


class TestVerifyEntityOwnership:
    def test_same_tenant_passes(self, db):
        _returns(db, {"_key": "plant_1", "tenant_key": "tenant_anna"})
        verify_entity_ownership(db, col.PLANT_INSTANCES, "plant_1", "tenant_anna")
        db.collection.assert_called_with(col.PLANT_INSTANCES)

    def test_global_catalog_row_passes(self, db):
        # Globally-seeded rows (empty tenant_key) stay referenceable, mirroring
        # the hybrid-catalog read visibility.
        _returns(db, {"_key": "fert_1", "tenant_key": ""})
        verify_entity_ownership(db, col.FERTILIZERS, "fert_1", "tenant_anna")

    def test_missing_document_raises_404(self, db):
        _returns(db, None)
        with pytest.raises(NotFoundError):
            verify_entity_ownership(db, col.PLANT_INSTANCES, "ghost", "tenant_anna")

    def test_foreign_tenant_raises_404(self, db):
        _returns(db, {"_key": "plant_1", "tenant_key": "tenant_bob"})
        with pytest.raises(NotFoundError):
            verify_entity_ownership(db, col.PLANT_INSTANCES, "plant_1", "tenant_anna")

    def test_off_allowlist_collection_raises_without_db_hit(self, db):
        # Never dial an off-allowlist collection handle (defense in depth).
        with pytest.raises(NotFoundError):
            verify_entity_ownership(db, "users", "user_1", "tenant_anna")
        db.collection.assert_not_called()

    def test_empty_tenant_key_raises_value_error(self, db):
        with pytest.raises(ValueError, match="tenant"):
            verify_entity_ownership(db, col.PLANT_INSTANCES, "plant_1", "")

    def test_entity_name_flows_into_error(self, db):
        _returns(db, None)
        with pytest.raises(NotFoundError, match="PlantInstance"):
            verify_entity_ownership(db, col.PLANT_INSTANCES, "ghost", "tenant_anna", entity_name="PlantInstance")

    def test_missing_tenant_key_field_treated_as_global(self, db):
        # A document without a tenant_key field (legacy/global) is treated as
        # empty → referenceable.
        _returns(db, {"_key": "plant_1"})
        verify_entity_ownership(db, col.PLANT_INSTANCES, "plant_1", "tenant_anna")

    def test_allowlist_membership(self):
        assert col.PLANT_INSTANCES in OWNERSHIP_VERIFIABLE_COLLECTIONS
        assert col.PLANTING_RUNS in OWNERSHIP_VERIFIABLE_COLLECTIONS
        assert col.HARVEST_OBSERVATIONS in OWNERSHIP_VERIFIABLE_COLLECTIONS
        assert "users" not in OWNERSHIP_VERIFIABLE_COLLECTIONS


class TestVerifyEntitiesOwnership:
    def test_all_owned_passes(self, db):
        _returns(db, {"_key": "k", "tenant_key": "tenant_anna"})
        verify_entities_ownership(db, col.PLANT_INSTANCES, ["a", "b"], "tenant_anna")

    def test_one_foreign_raises(self, db):
        def _get(key):
            return {"_key": key, "tenant_key": "tenant_bob" if key == "b" else "tenant_anna"}

        db.collection.return_value.get.side_effect = _get
        with pytest.raises(NotFoundError):
            verify_entities_ownership(db, col.PLANT_INSTANCES, ["a", "b"], "tenant_anna")

    def test_falsy_and_duplicate_keys_skipped(self, db):
        _returns(db, {"_key": "a", "tenant_key": "tenant_anna"})
        verify_entities_ownership(db, col.PLANT_INSTANCES, ["a", "", None, "a"], "tenant_anna")
        # Only the single distinct, truthy key triggers a lookup.
        assert db.collection.return_value.get.call_count == 1
