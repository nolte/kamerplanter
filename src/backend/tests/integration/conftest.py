"""The integration tier's execution contract: no database, no green run (#1432).

This tier is the only place where the repository and AQL layer is measured
against a **real** ArangoDB. Before this file existed it could not be gated:
each module self-skipped when the server was missing, so on a runner the tier
would have reported green having executed almost nothing — the failure class
NFR-018 §1 names ("a check that cannot fail must not exist").

The rule here, in one sentence: **in CI a missing database is a failure; only on
a developer machine may it be a skip.**

``CI`` is the discriminator. GitHub Actions sets it to ``true`` in every job
(so does GitLab, Circle and Travis), and nothing local sets it — a contributor
without a database still gets a skip with the address in the reason, and
``--max-skipped 0`` in ``task test:backend:integration`` (#1434) makes even that
skip a red run rather than a quiet one. Two levels, on purpose: the skip keeps
`pytest tests/` usable without docker, the floor keeps "usable" from turning
into "unmeasured".

Modules attach to the gate with ``pytest.mark.usefixtures("arango_db")`` at
module level rather than by autouse: ``test_perennial_cycle_loop.py`` drives
real engines against in-memory repositories and needs no server, and an autouse
fixture would have gated it too.

The same session fixture owns the tier's **database hygiene** (#1661). Every
module names its database through ``run_database_name(...)``, which scopes the
name to this process, so two sessions on one server no longer drop each other's
database mid-test. A name that is unique per run has one cost a fixed name did
not: nothing re-uses it, so a session that dies before its teardown leaves its
database behind for good. The fixture therefore drops, at session start, every
run-scoped database whose token says it is older than
``STALE_AFTER_SECONDS`` — and at session end, every database that carries
*this* session's token, which covers a module whose own teardown never ran.
Both sweeps act only on names ``RUN_DATABASE_PATTERN`` matches; the seeded demo
database and anything a script created by hand are outside that namespace.
"""

from __future__ import annotations

import os

import pytest

from tests.support.arango_integration import (
    ARANGO_PASSWORD,
    ARANGO_URL,
    ARANGO_USERNAME,
    STALE_AFTER_SECONDS,
    SYSTEM_DATABASE,
    belongs_to_this_run,
    connection_address,
    is_stale_run_database,
    probe_failure,
)


def _running_in_ci() -> bool:
    """Whether this session runs on a build agent rather than a developer machine.

    Any non-empty ``CI`` counts: GitHub Actions sets ``"true"``, some agents set
    ``"1"``. Read at call time, not at import, so a test can drive both branches.
    """
    return bool(os.environ.get("CI", "").strip())


def _unavailable_message(reason: str) -> str:
    """Explain a missing database with the address that was tried."""
    return (
        f"ArangoDB did not answer at {connection_address()}: {reason}\n"
        "The integration tier measures the repository and AQL layer against a real "
        "server; without one it measures nothing.\n"
        "Start one with the digest the dev stack and the CI lane share:\n"
        "    docker run -d --rm --name kp-it-arango -p 8529:8529 "
        "-e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12\n"
        "or run the dev stack (`task dev:core`). Point the tier elsewhere with "
        "ARANGODB_HOST / ARANGODB_PORT / ARANGODB_USERNAME / ARANGODB_PASSWORD."
    )


@pytest.fixture(scope="session")
def arango_db(request: pytest.FixtureRequest):
    """The tier's single connection check, plus the ``_system`` database handle.

    Session-scoped so the probe runs **once** per run instead of once per module
    at import time, and so the verdict cannot differ between two modules of the
    same session.

    Yields:
        The ``_system`` ``StandardDatabase``. Modules that create and drop their
        own test database can use it directly; those that open their own client
        still depend on this fixture for the gate. Before yielding, stale
        run-scoped databases of earlier sessions are dropped; after the last
        test, whatever this session created and did not drop itself is.

    Raises:
        Failed: in CI, when the server is unreachable — deliberately a failure
            and not a skip, because a skipped test reports like a passed one.
    """
    reason = probe_failure()
    if reason is not None:
        message = _unavailable_message(reason)
        if _running_in_ci():
            pytest.fail(message, pytrace=False)
        pytest.skip(message)

    from arango import ArangoClient

    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db(SYSTEM_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        _report(
            request, "stale run-scoped database from an earlier session", drop_databases(system, is_stale_run_database)
        )
        yield system
        _report(request, "database this session left behind", drop_databases(system, belongs_to_this_run))
    finally:
        client.close()


def drop_databases(system, select) -> list[str]:
    """Drop every database of ``system`` that ``select`` accepts; return their names.

    The predicate is the whole safety argument: both callers pass one that only
    ever accepts names ``run_database_name`` produced, so a database outside
    that namespace cannot be reached from here whatever the server holds.
    """
    dropped = []
    for name in sorted(system.databases()):
        if select(name):
            system.delete_database(name, ignore_missing=True)
            dropped.append(name)
    return dropped


def _report(request: pytest.FixtureRequest, what: str, names: list[str]) -> None:
    """Name what a sweep dropped in the terminal, so a leak is seen and not just fixed."""
    if not names:
        return
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:  # pragma: no cover - only absent under -p no:terminal
        return
    reporter.write_line("")
    reporter.write_line(
        f"#1661: dropped {len(names)} {what}{'s' if len(names) != 1 else ''} "
        f"(older than {STALE_AFTER_SECONDS // 3600} h counts as stale): " + ", ".join(names),
        yellow=True,
    )
