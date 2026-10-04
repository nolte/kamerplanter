"""#1793 — the erasure knows every continuous aggregate the migrations create.

``_purge_aggregates`` deletes from a closed list of aggregates. A migration that
adds another (``sensor_weekly``) would leave that aggregate's buckets of a
deleted tenant behind while every test stayed green, so the list is measured
against the migrations: each ``CREATE MATERIALIZED VIEW ... timescaledb.continuous``
must be named in ``AGGREGATE_VIEWS``.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.data_access.timescale import observation_repository
from app.data_access.timescale.observation_repository import AGGREGATE_VIEWS

_MIGRATIONS = Path(observation_repository.__file__).parent / "migrations"
_CAGG = re.compile(
    r"CREATE\s+MATERIALIZED\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>\w+)\s+WITH\s*\(\s*timescaledb\.continuous",
    re.IGNORECASE,
)


def test_every_continuous_aggregate_of_the_migrations_is_erased() -> None:
    created = {m.group("name") for path in sorted(_MIGRATIONS.glob("*.sql")) for m in _CAGG.finditer(path.read_text())}

    assert created, "the pattern found no continuous aggregate: it no longer reads the migrations"
    assert created == set(AGGREGATE_VIEWS), (
        "A continuous aggregate was added or renamed in a migration; deletion of a tenant/sensor must "
        "purge its buckets too (add it to AGGREGATE_VIEWS in observation_repository.py)."
    )
