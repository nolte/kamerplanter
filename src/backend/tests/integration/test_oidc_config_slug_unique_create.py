"""#1987 — the second of two creations of one slug fails in ``create``, which is what serialises them.

``OidcProviderAdminService.create_provider`` checks ``get_by_slug`` (not atomic) and then creates the
configuration; the unique index on ``slug`` is the only thing that makes two concurrent creations
fail one of them. The service now creates FIRST — switched off — and purges the slug's orphan links
only afterwards, so the loser never touches a link. That order is only as good as this contract:
the driver raises on the unique violation and the repository turns it into ``DuplicateError``.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.exceptions import DuplicateError
from app.data_access.arango import collections as col
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.domain.models.oidc_config import OidcProviderConfig
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1987 a unique index is a server contract; no double may answer it"),
]

_DB_NAME = run_database_name("oidc_slug_unique_create")


@pytest.fixture
def repo():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    db = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.OIDC_PROVIDER_CONFIGS)
    # The index ``ensure_collections`` creates (app/data_access/arango/collections.py).
    db.collection(col.OIDC_PROVIDER_CONFIGS).add_persistent_index(fields=["slug"], unique=True)
    try:
        yield ArangoOidcConfigRepository(db)
    finally:
        system.delete_database(_DB_NAME)


def _config(issuer: str) -> OidcProviderConfig:
    return OidcProviderConfig(slug="corp", display_name="Corp", issuer_url=issuer, client_id="c")


def test_the_second_creation_of_a_slug_raises_duplicate_and_the_first_survives(
    repo: ArangoOidcConfigRepository,
) -> None:
    first = repo.create(_config("https://first.example"))

    with pytest.raises(DuplicateError):
        repo.create(_config("https://second.example"))

    survivors = repo.list_all()
    assert [c.key for c in survivors] == [first.key]
    assert survivors[0].issuer_url == "https://first.example"
