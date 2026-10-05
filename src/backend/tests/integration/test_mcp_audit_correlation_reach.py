"""The MCP audit row's correlation fields reach the database and the Art. 15 export (#2130).

Unit tests prove the logger builds the row; only a real server proves the row
the repository *stores* carries the four references, that the privacy
self-service projection still reads a row that has them (#1145: a projection
stricter than its writer answers 500), and that the export manifest's walk
returns them to the subject.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.common.enums import McpToolStatus
from app.data_access.arango import collections as col
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository
from app.data_access.arango.personal_data_repository import ArangoPersonalDataRepository
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.models.mcp import McpAuditLog
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("mcp_audit_correlation")

pytestmark = pytest.mark.usefixtures("arango_db")

_ACCOUNT = "sa-2130-reach"
_REFERENCES = {
    "api_key_ref": "key_0123456789abcdef",
    "client_ip_ref": "198.51.100.0",
    "request_id": "5f0c2e8a-1d4b-4c55-9a39-2b8e7f1c0d42",
    "entity_keys": {"plant_key": ["plant-17"], "fertilizer_keys": ["fert-1", "fert-2"]},
}


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    database.create_collection(col.MCP_AUDIT_LOG)
    yield database
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def stored(db) -> str:
    entry = McpAuditLog(
        service_account_key=_ACCOUNT,
        tenant_key="t-2130",
        tool_name="get_plant",
        input_hash="0" * 64,
        status=McpToolStatus.OK,
        created_at=datetime.now(UTC),
        **_REFERENCES,
    )
    return ArangoMcpAuditRepository(db).record(entry)


def test_the_stored_row_carries_the_four_references(db, stored: str) -> None:
    document = db.collection(col.MCP_AUDIT_LOG).get(stored)

    assert {key: document[key] for key in _REFERENCES} == _REFERENCES


def test_the_self_service_projection_still_reads_the_row(db, stored: str) -> None:
    [entry] = ArangoMcpAuditRepository(db).list_for_service_account(_ACCOUNT)

    assert entry.tool_name == "get_plant"


def test_the_art_15_walk_returns_the_references(db, stored: str) -> None:
    [source] = [s for s in DataExportEngine.USER_DATA_MANIFEST if s.collection == col.MCP_AUDIT_LOG]

    [row] = ArangoPersonalDataRepository(db).collect_for_user(source, _ACCOUNT, ["t-2130"])

    assert {key: row[key] for key in _REFERENCES} == _REFERENCES
