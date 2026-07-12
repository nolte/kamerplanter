"""REQ-033 — MCP audit + idempotency repository tests.

The ArangoDB boundary is doubled with a small fake capturing AQL bind_vars and
insert payloads, so the parametrised-query contract (no f-strings) and the
scoping filters are asserted without a live database.
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.data_access.arango.mcp_repository import (
    ArangoMcpAuditRepository,
    ArangoMcpIdempotencyRepository,
)
from app.domain.models.mcp import McpAuditLog, McpIdempotencyRecord


class _FakeCursor(list):
    pass


class _FakeAql:
    def __init__(self, rows) -> None:
        self.rows = rows
        self.calls: list = []

    def execute(self, query, bind_vars):
        self.calls.append((query, bind_vars))
        return _FakeCursor(self.rows)


class _FakeCollection:
    def __init__(self) -> None:
        self.inserted: list = []

    def insert(self, doc, overwrite=False):
        self.inserted.append((doc, overwrite))
        return {"_key": doc.get("_key", "generated")}


class _FakeDb:
    def __init__(self, rows=None) -> None:
        self.aql = _FakeAql(rows or [])
        self._collection = _FakeCollection()

    def collection(self, name):
        return self._collection


def _audit_entry(**overrides) -> McpAuditLog:
    base = dict(
        service_account_key="sa-1",
        tenant_key="home",
        tool_name="list_species",
        input_hash="abc",
        status="ok",
    )
    base.update(overrides)
    return McpAuditLog(**base)


def test_audit_record_inserts_document_with_created_at():
    db = _FakeDb()
    repo = ArangoMcpAuditRepository(db)
    repo.record(_audit_entry())
    doc, _overwrite = db._collection.inserted[0]
    assert doc["service_account_key"] == "sa-1"
    assert doc["created_at"]  # backfilled when absent
    assert "_key" not in doc


def test_audit_list_scopes_by_service_account():
    row = {
        "tool_name": "list_species",
        "tenant_key": "home",
        "status": "ok",
        "output_size_bytes": 5,
        "duration_ms": 1,
        "error_class": None,
        "created_at": None,
    }
    db = _FakeDb(rows=[row])
    repo = ArangoMcpAuditRepository(db)
    entries = repo.list_for_service_account("sa-1", limit=10)
    assert len(entries) == 1
    _query, bind = db.aql.calls[0]
    assert bind["sa_key"] == "sa-1"
    assert bind["limit"] == 10
    assert bind["@collection"] == col.MCP_AUDIT_LOG


def test_audit_list_for_user_accounts_empty_shortcircuits():
    db = _FakeDb()
    repo = ArangoMcpAuditRepository(db)
    assert repo.list_for_user_accounts([]) == []
    assert db.aql.calls == []  # no query issued


def test_idempotency_get_returns_none_when_absent():
    db = _FakeDb(rows=[])
    repo = ArangoMcpIdempotencyRepository(db)
    assert repo.get("sa-1", "create_site", "k-1") is None
    _query, bind = db.aql.calls[0]
    assert bind["idem"] == "k-1"


def test_idempotency_store_uses_deterministic_key_and_overwrite():
    db = _FakeDb()
    repo = ArangoMcpIdempotencyRepository(db)
    record = McpIdempotencyRecord(
        service_account_key="sa-1",
        tool_name="create_site",
        idempotency_key="k-1",
        input_hash="h",
        result_payload={"summary": "ok"},
    )
    repo.store(record)
    doc, overwrite = db._collection.inserted[0]
    assert overwrite is True
    assert doc["_key"] == ArangoMcpIdempotencyRepository._doc_key("sa-1", "create_site", "k-1")
    assert record.expires_at is not None  # TTL stamped


def test_idempotency_delete_expired_returns_count():
    db = _FakeDb(rows=[7])
    repo = ArangoMcpIdempotencyRepository(db)
    assert repo.delete_expired() == 7
