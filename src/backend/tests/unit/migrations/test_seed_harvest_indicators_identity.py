"""#1956 — the identity the harvest-indicator seed matches on, and where its job runs.

No database: the YAML and the registry are plain data. The behaviour over a real
server is ``tests/integration/test_seed_loader_idempotency.py``.
"""

from __future__ import annotations

from collections import Counter

from app.migrations.seed_harvest_indicators import load_harvest_indicator_entries
from app.migrations.seeds.registry import _build_jobs


def test_species_type_and_unit_identify_exactly_one_seed_entry() -> None:
    """``(species, indicator_type)`` alone would collapse six legitimate entries; adding the unit does not."""
    entries = load_harvest_indicator_entries()

    pairs = Counter((e["species_name"], e["indicator_type"]) for e in entries)
    identities = Counter((e["species_name"], e["indicator_type"], e["measurement_unit"]) for e in entries)

    assert any(n > 1 for n in pairs.values()), "the premise: (species, type) is not a key in this YAML"
    assert [k for k, n in identities.items() if n > 1] == []


def test_the_harvest_job_runs_after_every_species_seed() -> None:
    names = [job.name for job in _build_jobs()]

    assert names.index("harvest_indicators") > names.index("plant_info_extended")
    assert names.index("harvest_indicators") > names.index("core_data")
