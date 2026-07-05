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

    def get_all_substrates(self, offset: int = 0, limit: int = 50) -> tuple[list[Substrate], int]:
        window = self.stored[offset : offset + limit]
        return window, len(self.stored)

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


# ── Registry wiring ───────────────────────────────────────────────────────


def test_seed_registered_in_registry() -> None:
    from app.migrations.seeds.registry import _build_jobs

    job_names = {job.name for job in _build_jobs()}
    assert "substrates" in job_names


def test_seed_module_imports() -> None:
    assert callable(run_seed_substrates)
