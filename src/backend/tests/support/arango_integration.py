"""The one ArangoDB connection contract of the integration tier (#1432).

Until 2026-09-16 thirteen modules under ``tests/integration/`` each carried their
**own** copy of the same probe::

    ARANGO_AVAILABLE = False
    try:
        _probe = ArangoClient(hosts="http://localhost:8529")
        _probe.db("_system", username="root", password="rootpassword").version()
        ARANGO_AVAILABLE = True
    except Exception:
        pass
    pytestmark = pytest.mark.skipif(not ARANGO_AVAILABLE, reason="...")

Three consequences, all measured: the address was a literal in every copy, so no
runner could point the tier anywhere else; the probe ran at *import* time once
per module (~170 s of connection retries for a full skipped run); and a run
without a database reported ``7 passed, 136 skipped`` with exit code 0 — a tier
that tested almost nothing while looking green (NFR-018 §1).

This module holds the address, and the single probe. The semantics of a missing
database live in ``tests/integration/conftest.py``: **in CI it is a failure, not
a skip.**

The environment variable names are ``Settings``' own (``env_prefix: ""`` in
``app/config/settings.py``), deliberately: several modules build a real
``Settings(arangodb_database=...)`` and connect through ``ArangoConnection``,
while others open an ``ArangoClient`` directly. Reading the same names here is
what keeps those two routes pointed at the same server when CI moves it.
"""

from __future__ import annotations

import os
from functools import cache

#: Defaults mirror ``Settings`` and ``docker-compose.yml`` — a developer who ran
#: `task dev:core` needs no environment at all.
ARANGO_HOST = os.environ.get("ARANGODB_HOST", "localhost")
ARANGO_PORT = os.environ.get("ARANGODB_PORT", "8529")
ARANGO_USERNAME = os.environ.get("ARANGODB_USERNAME", "root")
ARANGO_PASSWORD = os.environ.get("ARANGODB_PASSWORD", "rootpassword")

#: ``http://host:port`` — what every module passes to ``ArangoClient(hosts=...)``.
ARANGO_URL = f"http://{ARANGO_HOST}:{ARANGO_PORT}"

#: The database every probe authenticates against; never written to.
SYSTEM_DATABASE = "_system"


def connection_address() -> str:
    """Render the address and user the tier connects as, for a failure message."""
    return f"{ARANGO_URL} (database {SYSTEM_DATABASE!r}, user {ARANGO_USERNAME!r})"


@cache
def probe_failure() -> str | None:
    """Return why ArangoDB is unreachable, or ``None`` when it answered.

    Cached: the session fixture asks once, and a second caller (a module-scoped
    fixture, a helper) must not pay the retry timeout again. The exception text
    is carried into the message because "not available" alone cannot distinguish
    "nothing listening" from "wrong password" — the second is the failure mode a
    CI service container actually produces.

    Returns:
        A human-readable reason, or ``None`` if the server answered ``_api/version``.
    """
    try:
        from arango import ArangoClient
    except ImportError as exc:  # pragma: no cover - the lock installs python-arango
        return f"python-arango is not installed in this environment: {exc}"

    client = ArangoClient(hosts=ARANGO_URL)
    try:
        client.db(SYSTEM_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD).version()
    except Exception as exc:  # noqa: BLE001 - any failure means "this tier cannot run"
        return f"{type(exc).__name__}: {exc}"
    finally:
        client.close()
    return None
