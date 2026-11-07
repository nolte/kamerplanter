"""#2709 — what ``collection.get`` answers for a key a client can send, and what ``get_document`` makes of it.

Measured against a real ArangoDB, because the whole point is a server answer no double can predict: the
driver reads 1202 as ``None``, but the dot keys come back as ``DocumentGetError`` 1203 and a key naming
another collection as ``DocumentParseError``. The raw measurement is pinned next to the helper's answer, so a
server or driver release that changes the former shows up here rather than as a 500 in production.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from arango.exceptions import DocumentGetError, DocumentParseError

from app.data_access.arango.document_reads import get_document
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("document_reads")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection("locations").insert({"_key": "bed_1", "name": "Bed"})
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.mark.parametrize("key", ["a b", "x!%", "%zz", "ä", "x" * 300])
def test_a_malformed_key_the_server_answers_1202_for_is_none_either_way(database, key: str) -> None:
    locations = database.collection("locations")

    assert locations.get(key) is None
    assert get_document(locations, key) is None


@pytest.mark.parametrize("key", ["", ".", ".."])
def test_a_dot_key_raises_1203_raw_and_is_absent_through_the_helper(database, key: str) -> None:
    locations = database.collection("locations")

    with pytest.raises(DocumentGetError) as raised:
        locations.get(key)

    assert raised.value.error_code == 1203
    assert get_document(locations, key) is None


def test_a_key_naming_another_collection_is_absent(database) -> None:
    locations = database.collection("locations")

    with pytest.raises(DocumentParseError):
        locations.get("plants/bed_1")
    assert get_document(locations, "plants/bed_1") is None


def test_an_existing_document_is_read(database) -> None:
    """The positive control: the helper is no reader that answers ``None`` for everything."""
    document = get_document(database.collection("locations"), "bed_1")

    assert document is not None
    assert document["name"] == "Bed"


def test_a_missing_collection_still_raises(database) -> None:
    """1203 is also a missing collection; the helper refuses the dot keys up front and does not swallow it."""
    with pytest.raises(DocumentGetError) as raised:
        get_document(database.collection("no_such_collection"), "bed_1")

    assert raised.value.error_code == 1203
