"""Integration tests requiring a running ArangoDB instance.

Run with: pytest tests/integration/ -v
Requires: docker compose up arangodb
"""

import pytest

ARANGO_AVAILABLE = False
try:
    from arango import ArangoClient

    client = ArangoClient(hosts="http://localhost:8529")
    client.db("_system", username="root", password="rootpassword").version()
    ARANGO_AVAILABLE = True
    client.close()
except Exception:
    pass


@pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available")
class TestArangoSetup:
    def test_collections_created(self):
        from app.config.settings import Settings
        from app.data_access.arango.collections import DOCUMENT_COLLECTIONS, EDGE_COLLECTIONS, ensure_collections
        from app.data_access.arango.connection import ArangoConnection

        settings = Settings(arangodb_database="kamerplanter_test")
        conn = ArangoConnection(settings)
        db = conn.connect()

        ensure_collections(db)

        for col_name in DOCUMENT_COLLECTIONS:
            assert db.has_collection(col_name), f"Missing collection: {col_name}"

        for col_name in EDGE_COLLECTIONS:
            assert db.has_collection(col_name), f"Missing edge collection: {col_name}"

        assert db.has_graph("kamerplanter_graph")

        # Cleanup
        db_sys = ArangoClient(hosts="http://localhost:8529").db("_system", username="root", password="rootpassword")
        if db_sys.has_database("kamerplanter_test"):
            db_sys.delete_database("kamerplanter_test")
        conn.close()
