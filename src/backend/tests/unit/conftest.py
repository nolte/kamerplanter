"""Unit-tier fixtures.

Carries the datastore guard from #978: no unit test may open a real ArangoDB,
TimescaleDB or Valkey connection. See ``tests/support/db_guard.py`` for why the
failure mode is worth a guard rather than a per-test patch.
"""

import pytest

from tests.support import db_guard


@pytest.fixture(autouse=True)
def block_datastore_access(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any real datastore connection from a unit test fail immediately."""
    db_guard.install_unless_marked(request, monkeypatch, tier="unit")
