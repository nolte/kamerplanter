"""Tests for the dedicated substrate catalog seeder (REQ-019).

Covers, without touching a real database:

* ``substrates.yaml`` loads and every entry validates against ``Substrate``
  (in particular the composition-fractions-sum-to-1.0 invariant);
* ``run_seed_substrates()`` inserts the catalog into an empty collection;
* the seeder is idempotent — a second run inserts nothing;
* the seed is registered in the seed registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml

import app.migrations
from app.domain.models.substrate import Substrate
from app.migrations.seed_substrates import run_seed_substrates

_YAML = Path(app.migrations.__file__).parent / "seed_data" / "substrates.yaml"


def _raw_entries() -> list[dict[str, Any]]:
    data = yaml.safe_load(_YAML.read_text(encoding="utf-8")) or {}
    return data["substrates"]


class _FakeSubstrateRepo:
    """Minimal in-memory stand-in for the substrate repository."""

    def __init__(self) -> None:
        self.stored: list[Substrate] = []

    def get_global_substrates(self) -> list[Substrate]:
        """Global rows only, as the real read filters them (``tenant_key`` empty, #2027)."""
        return [s for s in self.stored if not s.tenant_key]

    def create_substrate(self, substrate: Substrate) -> Substrate:
        self.stored.append(substrate)
        return substrate


# ── YAML / model validation ───────────────────────────────────────────────


def test_yaml_loads_and_is_non_empty() -> None:
    entries = _raw_entries()
    assert len(entries) > 0, "substrates.yaml must contain seed records"


def test_every_entry_validates_against_model() -> None:
    errors: list[str] = []
    for entry in _raw_entries():
        try:
            Substrate.model_validate(entry)
        except Exception as exc:  # noqa: BLE001
            name = entry.get("name_de") or entry.get("brand") or entry.get("type")
            errors.append(f"{name}: {str(exc).splitlines()[0]}")
    assert not errors, "model validation errors:\n" + "\n".join(errors)


def test_composition_fractions_sum_to_one() -> None:
    for entry in _raw_entries():
        composition = entry.get("composition") or {}
        if not composition:
            continue
        total = sum(composition.values())
        name = entry.get("name_de") or entry.get("brand") or entry.get("type")
        assert abs(total - 1.0) <= 0.01, f"{name}: composition sums to {total:.4f}, expected 1.0 (±0.01)"


# ── Seeder behaviour ──────────────────────────────────────────────────────


def test_run_seed_substrates_populates_empty_collection() -> None:
    repo = _FakeSubstrateRepo()
    with patch("app.migrations.seed_substrates.get_substrate_repo", return_value=repo):
        run_seed_substrates()

    assert len(repo.stored) == len(_raw_entries())
    # spot check a well-known record survived model round-trip
    names = {s.name_de for s in repo.stored}
    assert "Universalerde" in names


def test_run_seed_substrates_is_idempotent() -> None:
    repo = _FakeSubstrateRepo()
    with patch("app.migrations.seed_substrates.get_substrate_repo", return_value=repo):
        run_seed_substrates()
        count_after_first = len(repo.stored)
        run_seed_substrates()
        count_after_second = len(repo.stored)

    assert count_after_first == len(_raw_entries())
    assert count_after_second == count_after_first, "second run must not duplicate substrates"


def test_a_tenant_mix_with_a_seed_identity_does_not_count_as_the_seed() -> None:
    """#2027: only a global row stands for a seed; the real-DB proof is
    ``tests/integration/test_seed_catalogue_loaders_ownership.py``."""
    first = Substrate.model_validate(_raw_entries()[0])
    repo = _FakeSubstrateRepo()
    repo.stored.append(first.model_copy(update={"tenant_key": "t-grower"}))
    with patch("app.migrations.seed_substrates.get_substrate_repo", return_value=repo):
        run_seed_substrates()

    same_identity = [s for s in repo.stored if (s.type, s.name_de) == (first.type, first.name_de)]
    assert sorted(s.tenant_key for s in same_identity) == ["", "t-grower"]


# ── Registry wiring ───────────────────────────────────────────────────────


def test_seed_registered_in_registry() -> None:
    from app.migrations.seeds.registry import _build_jobs

    job_names = {job.name for job in _build_jobs()}
    assert "substrates" in job_names


def test_seed_module_imports() -> None:
    assert callable(run_seed_substrates)
