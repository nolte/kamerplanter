"""Seed consistency for the M6 nitrogen split (REQ-053 GP-FR-139, GP-ACC-049, #2325).

A fresh install runs v0096 on an empty volume, so a legacy ``nitrogen_fixer`` species
only carries ``nitrogen_fixing: true`` if the seed says so — otherwise a fresh install
and an upgraded one end with different data. The model rule (no fixer that is a heavy
feeder) is pinned here against the seeds too, because a seed violating it would make
every later read of that species raise.
"""

from pathlib import Path

import pytest
import yaml

SEED_DIR = Path(__file__).resolve().parents[3] / "app" / "migrations" / "seed_data"


def _species_entries() -> list[tuple[str, dict]]:
    entries: list[tuple[str, dict]] = []
    for path in sorted(SEED_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        for key in ("species", "new_species"):
            for entry in data.get(key) or []:
                if isinstance(entry, dict):
                    entries.append((f"{path.name}:{entry.get('scientific_name')}", entry))
        for name, fields in (data.get("species_enrichment") or {}).items():
            if isinstance(fields, dict):
                entries.append((f"{path.name}:enrichment:{name}", fields))
    return entries


@pytest.mark.parametrize(("where", "entry"), _species_entries())
def test_a_legacy_nitrogen_fixer_is_flagged_and_not_a_heavy_feeder(where: str, entry: dict) -> None:
    if entry.get("nutrient_demand_level") != "nitrogen_fixer":
        pytest.skip("not a legacy nitrogen fixer")
    assert entry.get("nitrogen_fixing") is True, f"{where}: legacy nitrogen_fixer without nitrogen_fixing: true"
    assert entry.get("nutrient_demand") != "heavy_feeder", f"{where}: nitrogen fixer must not be a heavy feeder"


def test_the_seeds_contain_legacy_nitrogen_fixers() -> None:
    """Guard against the parametrised test above going vacuous (loader finds no species)."""
    assert sum(1 for _, e in _species_entries() if e.get("nutrient_demand_level") == "nitrogen_fixer") >= 9
