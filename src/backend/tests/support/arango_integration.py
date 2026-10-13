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

It also holds the tier's **database naming** (#1661). Until 2026-09-23 every
module bootstrapped a database by a *fixed* name (``kamerplanter_merge_mode_null_test``,
``kp_test_slot_edge_cleanup``, …) — 21 of the tier's 22 modules — and dropped it
on setup and teardown. Two sessions on one server, which is the normal working
mode of this repository (parallel worktrees, ``task worktree:add``), therefore
dropped each other's database mid-test: measured as ``[HTTP 404][ERR 1228]
database not found`` errors that looked exactly like defects in the change
under review. Worse, and constructed deliberately rather than merely feared:
because a database handle is a *name* and not an identity, a session whose
database was re-created and re-seeded by its neighbour reads the neighbour's
rows and can pass an assertion its own code should have failed (a false green).
:func:`run_database_name` closes both by scoping every name to the session.

The environment variable names are ``Settings``' own (``env_prefix: ""`` in
``app/config/settings.py``), deliberately: several modules build a real
``Settings(arangodb_database=...)`` and connect through ``ArangoConnection``,
while others open an ``ArangoClient`` directly. Reading the same names here is
what keeps those two routes pointed at the same server when CI moves it.
"""

from __future__ import annotations

import os
import re
import secrets
import time
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


# ── run-scoped database names (#1661) ─────────────────────────────────────────

#: Prefix of every database this tier creates. The namespace is what lets the
#: sweeps below act on *only* what this helper made: the seeded demo database
#: (``kamerplanter``), the E2E stacks (``kamerplanter_e2e*``) and any database a
#: hand-written script left behind do not start with it and are never touched.
RUN_DATABASE_PREFIX = "kp_it_"

#: What a module may pass as the ``base`` of its database name. Short and
#: lower-case, so the full name stays inside ArangoDB's 64-character limit for
#: traditional names once the prefix and the run token are added.
_BASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,37}$")

#: Every name :func:`run_database_name` produces: prefix, base, ``__``, the
#: session's start as epoch seconds, ``_``, six hex digits of entropy.
RUN_DATABASE_PATTERN = re.compile(
    rf"^{re.escape(RUN_DATABASE_PREFIX)}(?P<base>[a-z][a-z0-9_]*)__(?P<started>\d{{10}})_(?P<entropy>[0-9a-f]{{6}})$"
)

#: A run-scoped database older than this is treated as an orphan of a session
#: that never reached its teardown (a killed process, a lost terminal). The tier
#: takes ~3.5 minutes serially and is bounded by CI at minutes, not hours; a
#: developer pausing a session under a debugger for six hours is the one case
#: this would misjudge, and the sweep names what it dropped so that is visible.
STALE_AFTER_SECONDS = 6 * 60 * 60


@cache
def run_token() -> str:
    """One token per **process**, computed on first use and never inherited.

    ``<epoch seconds>_<6 hex>``: the timestamp is what lets a leftover be
    recognised as stale without a registry, the entropy is what makes two
    sessions started in the same second — or on two machines against one server
    — distinct. Deliberately *not* read from the environment: a token a child
    process inherited would put a child pytest session (``test_integration_tier_gate``
    spawns them) into its parent's namespace, which is the collision this exists
    to remove. A child that creates databases gets its own token and its own
    session-end sweep.
    """
    return f"{int(time.time()):010d}_{secrets.token_hex(3)}"


def run_database_name(base: str) -> str:
    """The database a module of this tier should create, scoped to this session.

    Args:
        base: A short, lower-case identifier for the module — what the fixed name
            used to say after ``kamerplanter_`` / ``kp_test_``, without the
            trailing ``_test``.

    Returns:
        ``kp_it_<base>__<token>``; stable within one process, distinct across
        processes, and matched by :data:`RUN_DATABASE_PATTERN` so the sweeps in
        ``tests/integration/conftest.py`` can find it again.

    Raises:
        ValueError: for a base the pattern refuses — a name that would exceed
            ArangoDB's limit or fall outside the namespace the sweeps recognise.
    """
    if not _BASE_PATTERN.match(base):
        raise ValueError(
            f"test database base {base!r} must match {_BASE_PATTERN.pattern} — "
            "lower-case, starting with a letter, at most 38 characters"
        )
    return f"{RUN_DATABASE_PREFIX}{base}__{run_token()}"


def is_run_database(name: str) -> bool:
    """Whether *name* was produced by :func:`run_database_name` in some session."""
    return RUN_DATABASE_PATTERN.match(name) is not None


def belongs_to_this_run(name: str) -> bool:
    """Whether *name* was produced by :func:`run_database_name` in **this** process."""
    return is_run_database(name) and name.endswith(f"__{run_token()}")


def is_stale_run_database(name: str, *, now: float | None = None) -> bool:
    """Whether *name* is a run-scoped database from a session older than the threshold.

    Args:
        name: A database name as ``_system`` lists it.
        now: The current time as epoch seconds; defaults to ``time.time()`` and is
            a parameter so the boundary can be tested without waiting six hours.
    """
    match = RUN_DATABASE_PATTERN.match(name)
    if match is None:
        return False
    started = int(match.group("started"))
    current = time.time() if now is None else now
    return current - started > STALE_AFTER_SECONDS
