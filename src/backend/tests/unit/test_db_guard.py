"""The datastore guard is provably active (#978).

A guard nobody exercises is indistinguishable from a guard that silently stopped
working — the ``conftest.py`` could be renamed, a provider could start bypassing
``get_db()``, a future pytest could change fixture ordering. These tests open the
connections on purpose and pin both the failure and its message.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.connection import ArangoConnection
from tests.support.db_guard import ALLOW_MARKER, TierDatabaseAccessError, install_unless_marked


class TestArangoIsBlocked:
    def test_get_db_raises_immediately(self):
        from app.common.dependencies import get_db

        with pytest.raises(TierDatabaseAccessError) as excinfo:
            get_db()

        message = str(excinfo.value)
        assert "unit tier" in message
        assert "ArangoDB" in message
        assert "#978" in message

    def test_the_message_names_the_provider_chain(self):
        """The point of the message: tell an author which wiring reached a repository."""
        from app.common.dependencies import get_species_repo

        with pytest.raises(TierDatabaseAccessError) as excinfo:
            get_species_repo()

        message = str(excinfo.value)
        assert "app/common/dependencies.py" in message
        assert "get_species_repo" in message
        assert "tests/unit/test_db_guard.py" in message
        assert "test_the_message_names_the_provider_chain" in message

    def test_a_swallowing_except_exception_cannot_hide_it(self):
        """Why the guard raises a ``BaseException``.

        Production swallows ``Exception`` around optional lookups — see
        ``CropRotationValidator.validate_planting``, which wraps its
        ``get_family_repo()`` call in ``except Exception: pass``. A guard those
        handlers can catch would report green in exactly the code that needs it.
        """
        from app.common.dependencies import get_db

        def swallow_everything() -> str:
            try:
                get_db()
            except Exception:  # noqa: BLE001 — the point of the test
                return "swallowed"
            return "connected"

        with pytest.raises(TierDatabaseAccessError):
            swallow_everything()


class TestOtherDatastoresAreBlocked:
    def test_a_redis_command_raises(self):
        from app.common.dependencies import _get_redis_client

        # Constructing the client is lazy and must stay allowed; the socket only
        # opens on the first command, which is where the guard sits.
        client = _get_redis_client()

        with pytest.raises(TierDatabaseAccessError) as excinfo:
            client.ping()

        assert "Redis/Valkey" in str(excinfo.value)

    def test_the_timescale_pool_raises(self):
        from app.config.settings import settings
        from app.data_access.timescale.connection import TimescaleConnection

        with pytest.raises(TierDatabaseAccessError) as excinfo:
            TimescaleConnection(settings).connect()

        assert "TimescaleDB" in str(excinfo.value)


class TestOptOut:
    @pytest.mark.allow_db_connection("verifies the opt-out itself; opens no connection")
    def test_the_marker_leaves_the_connection_unpatched(self):
        # Asserted on the class attribute rather than by connecting: this test
        # proves the opt-out reaches the guard, not that a database exists.
        assert ArangoConnection.connect.__qualname__ == "ArangoConnection.connect"

    def test_the_marker_requires_a_reason(self):
        """An unjustified exception is a silent bypass, which is what we replaced."""
        node = SimpleNamespace(
            get_closest_marker=lambda name: SimpleNamespace(args=()) if name == ALLOW_MARKER else None,
            nodeid="tests/unit/example.py::test_example",
        )

        with pytest.raises(pytest.UsageError, match="requires a reason"):
            install_unless_marked(SimpleNamespace(node=node), MagicMock(), tier="unit")
