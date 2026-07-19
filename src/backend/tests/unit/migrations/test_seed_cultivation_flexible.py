"""Tests for the ADR-006 E6 ``cultivation_flexible`` seed pass (#615).

The pass reads the ``cultivation_flexible: true`` entries from
``species.yaml/lifecycle_overrides`` and applies them onto the persisted
``Species.cultivation_flexible`` field. These DB-less tests exercise the loader
against the real YAML and the runner against a fake repository — asserting the
documented facultative cohort is picked up and the update is idempotent.
"""

from __future__ import annotations

from app.domain.models.species import Species
from app.migrations.seed_cultivation_flexible import (
    _load_flexible_species,
    run_seed_cultivation_flexible,
)


class _FakeSpeciesRepo:
    """Records single-field updates keyed by scientific_name."""

    def __init__(self, species: list[Species]) -> None:
        self._by_name = {s.scientific_name: s for s in species}
        self.updates: list[tuple[str, str, object]] = []

    def get_by_scientific_name(self, name: str) -> Species | None:
        return self._by_name.get(name)

    def update_field(self, key: str, field: str, value: object) -> None:
        self.updates.append((key, field, value))
        # Reflect the write so a re-run sees the updated state (idempotency).
        for sp in self._by_name.values():
            if sp.key == key:
                setattr(sp, field, value)


def test_loader_returns_documented_cohort():
    flexible = _load_flexible_species()
    assert "Solanum lycopersicum" in flexible
    assert "Fragaria x ananassa" in flexible
    assert "Ocimum basilicum" in flexible
    # Strict annuals are not flexible.
    assert "Solanum tuberosum" not in flexible
    assert "Tropaeolum majus" not in flexible


def test_runner_sets_flag_for_existing_species(monkeypatch):
    tomato = Species(_key="sp-1", scientific_name="Solanum lycopersicum")
    lettuce = Species(_key="sp-2", scientific_name="Lactuca sativa")
    repo = _FakeSpeciesRepo([tomato, lettuce])
    monkeypatch.setattr("app.migrations.seed_cultivation_flexible.get_species_repo", lambda: repo)
    monkeypatch.setattr(
        "app.migrations.seed_cultivation_flexible._load_flexible_species",
        lambda: {"Solanum lycopersicum"},
    )

    run_seed_cultivation_flexible()

    assert ("sp-1", "cultivation_flexible", True) in repo.updates
    # A non-flexible species is never touched.
    assert all(key != "sp-2" for key, _, _ in repo.updates)


def test_runner_is_idempotent(monkeypatch):
    tomato = Species(_key="sp-1", scientific_name="Solanum lycopersicum", cultivation_flexible=True)
    repo = _FakeSpeciesRepo([tomato])
    monkeypatch.setattr("app.migrations.seed_cultivation_flexible.get_species_repo", lambda: repo)
    monkeypatch.setattr(
        "app.migrations.seed_cultivation_flexible._load_flexible_species",
        lambda: {"Solanum lycopersicum"},
    )

    run_seed_cultivation_flexible()

    # Already flagged → no write.
    assert repo.updates == []


def test_runner_tolerates_missing_species(monkeypatch):
    repo = _FakeSpeciesRepo([])
    monkeypatch.setattr("app.migrations.seed_cultivation_flexible.get_species_repo", lambda: repo)
    monkeypatch.setattr(
        "app.migrations.seed_cultivation_flexible._load_flexible_species",
        lambda: {"Nonexistent species"},
    )

    run_seed_cultivation_flexible()  # must not raise

    assert repo.updates == []
