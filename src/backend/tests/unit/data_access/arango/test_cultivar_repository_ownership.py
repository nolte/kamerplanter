"""``ArangoSpeciesRepository.update_cultivar`` never rewrites the owning tenant (#1090 P2).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary,
doubled with MagicMock. No real ArangoDB connection.

**Why this guard sits in the repository.** ``update_cultivar`` is not reached only
through :class:`SpeciesService` (which preserves ownership itself). The plant-info
seed run calls it **repository-direct** and **name-matched**
(``migrations/seed_data.py``): for every cultivar in the YAML catalogue it looks up
an existing row with the same ``name`` and rewrites it from a freshly built
``Cultivar``. That YAML-built model carries the model default ``tenant_key == ""``,
and the base repository's update is a full model dump — an empty string is not
``None``, so it is written. A tenant-owned cultivar that happens to share its name
with a seeded one would therefore be silently reassigned to the *global* catalogue
on the next boot: ownership erased, the row now visible to and editable by every
tenant, with no request and no log line saying so.

Preserving the stored owner here makes the invariant hold for **every** writer,
including future repository-direct ones, instead of only for the two call sites that
exist today.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.models.species import Cultivar


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoSpeciesRepository(mock_db)


def _stored(tenant_key: str) -> dict:
    return {
        "_key": "cv_1",
        "name": "Genovese",
        "species_key": "sp_1",
        "tenant_key": tenant_key,
        "origin": "tenant",
    }


def _arrange(mock_db, stored: dict | None) -> MagicMock:
    """Point the doubled collection at ``stored`` and echo the write back."""
    collection = mock_db.collection.return_value
    collection.get.return_value = stored
    collection.update.side_effect = lambda doc, **_kwargs: {"new": {**(stored or {}), **doc}}
    return collection


def _written_tenant_key(collection: MagicMock) -> str | None:
    return collection.update.call_args.args[0].get("tenant_key")


class TestUpdateCultivarPreservesOwnership:
    def test_a_global_replacement_cannot_erase_a_tenant_owner(self, repo, mock_db):
        # The seed-shaped write: a YAML-built cultivar with the default global
        # tenant_key, aimed at a row a tenant owns.
        collection = _arrange(mock_db, _stored("tenant_42"))

        updated = repo.update_cultivar("cv_1", Cultivar(name="Genovese", species_key="sp_1"))

        assert _written_tenant_key(collection) == "tenant_42"
        assert updated.tenant_key == "tenant_42"

    def test_a_foreign_tenant_key_cannot_be_written_over_an_owner(self, repo, mock_db):
        # Ownership is not merely defaulted-away: an explicit *other* tenant on the
        # incoming model must not be able to reassign the row either.
        collection = _arrange(mock_db, _stored("tenant_42"))

        repo.update_cultivar("cv_1", Cultivar(name="Genovese", species_key="sp_1", tenant_key="tenant_99"))

        assert _written_tenant_key(collection) == "tenant_42"

    def test_a_global_row_stays_global(self, repo, mock_db):
        # The other direction: an update must not accidentally *grant* ownership of a
        # global seed row to whoever happens to write it.
        collection = _arrange(mock_db, _stored(""))

        repo.update_cultivar("cv_1", Cultivar(name="Genovese", species_key="sp_1", tenant_key="tenant_42"))

        assert _written_tenant_key(collection) == ""

    def test_a_legacy_row_without_the_attribute_stays_unowned(self, repo, mock_db):
        # Rows written before #1090 carry no tenant_key at all; the cutover keeps them
        # global. Reading one back must not crash and must not mint an owner.
        legacy = {"_key": "cv_1", "name": "Genovese", "species_key": "sp_1"}
        collection = _arrange(mock_db, legacy)

        repo.update_cultivar("cv_1", Cultivar(name="Genovese", species_key="sp_1", tenant_key="tenant_42"))

        assert _written_tenant_key(collection) == ""

    def test_a_missing_document_still_reaches_the_write(self, repo, mock_db):
        # No stored row to preserve from: the guard must not swallow the update and
        # hide the repository's own not-found handling.
        collection = _arrange(mock_db, None)
        collection.update.side_effect = lambda doc, **_kwargs: {"new": {**doc, "_key": "cv_1"}}

        repo.update_cultivar("cv_1", Cultivar(name="Genovese", species_key="sp_1"))

        assert collection.update.called
