"""API-tier fixtures.

Carries the same datastore guard as the unit tier (#978). The tier builds the
real FastAPI app, but it drives it through ``dependency_overrides`` against
fakes — so a connection here means an override is missing, which is a wiring bug
of exactly the kind the guard exists to name. Measured before switching it on:
of 682 api+contracts tests, none reached ArangoDB or TimescaleDB and two reached
the Celery broker.
"""

import pytest

from tests.support import db_guard


@pytest.fixture(autouse=True)
def block_datastore_access(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any real datastore connection from an API test fail immediately."""
    db_guard.install_unless_marked(request, monkeypatch, tier="api")
