"""The three sibling plant seeders match cultivars against the global catalogue only (SEC-002, #1090).

``seed_data.seed_cultivars`` was made ownership-aware in C-1
(``test_seed_data_cultivar_ownership.py``). Its three siblings —
``seed_plant_info``, ``seed_plant_info_extended`` and ``seed_adventskalender`` —
were not: each built its skip-set over **every** cultivar of the species::

    existing_names = {c.name for c in species_repo.get_cultivars(sp_key)}

so a *tenant-owned* row named like a YAML entry made the seeder skip that entry.
The consequence is the SEC-002 finding of the C-7 security review: a
tenant-controlled string decides what the **shared** catalogue contains. A tenant
who creates a cultivar called ``Genovese`` suppresses the global ``Genovese`` for
*every* tenant, on every future boot — a cross-tenant denial of catalogue content
from an ordinary, permitted write.

These are behavioural tests, not structural ones: each seeder is driven end to
end over a minimal in-memory YAML and a fake repository set, so a fix that lands
in a shared helper but is not actually *called* by a seeder still fails here.

Red-first (measured 2026-08-10, before the fix): all three
``…_still_seeds_the_global_entry`` tests failed with ``created == []`` — the
global entry was silently dropped for every tenant.

Delimitation: the ownership rule itself (which rows are the seed-match universe)
is pinned once on the shared helper in ``test_cultivar_seed.py``; the upsert-style
sibling ``seed_data.seed_cultivars`` keeps its own module
(``test_seed_data_cultivar_ownership.py``). This module pins only that each of the
three *skip-if-exists* seeders routes its match through that rule.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.domain.models.species import Cultivar, Species

_SPECIES_NAME = "Ocimum basilicum"
_SPECIES_KEY = "sp_basil"
_CULTIVAR_NAME = "Genovese"

_YAML_CULTIVARS: dict[str, list[dict[str, Any]]] = {
    _SPECIES_NAME: [{"name": _CULTIVAR_NAME, "breeder": "Seed Co", "patent_status": "none"}]
}


# ── fake repository set: only what a cultivar-only seed run touches ──────────


class _FakeFamilyRepo:
    def get_by_name(self, name: str) -> None:
        return None


class _FakeSpeciesRepo:
    """Species/cultivar reads and the cultivar create the seeders' §5 block uses."""

    def __init__(self, cultivars: list[Cultivar]) -> None:
        self._cultivars = list(cultivars)
        self.created: list[Cultivar] = []
        self.updated: list[tuple[str, Cultivar]] = []

    def get_by_scientific_name(self, scientific_name: str) -> Species | None:
        if scientific_name != _SPECIES_NAME:
            return None
        return Species(_key=_SPECIES_KEY, scientific_name=_SPECIES_NAME)

    def get_cultivars(self, species_key: str) -> list[Cultivar]:
        return [c for c in self._cultivars if c.species_key == species_key]

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.created.append(cultivar)
        self._cultivars.append(cultivar)
        return cultivar

    def update_cultivar(self, key: str, cultivar: Cultivar) -> Cultivar:
        self.updated.append((key, cultivar))
        return cultivar

    def update(self, key: str, species: Species) -> Species:
        return species

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        return species.model_copy(update={"key": _SPECIES_KEY})


class _FakeIpmRepo:
    def get_all_pests(self, offset: int, limit: int) -> tuple[list[Any], int]:
        return [], 0

    def get_all_diseases(self, offset: int, limit: int) -> tuple[list[Any], int]:
        return [], 0

    def get_all_treatments(self, offset: int, limit: int) -> tuple[list[Any], int]:
        return [], 0


class _UnusedRepo:
    """Any call on this repo is a test-design error, not a silent no-op."""

    def __getattr__(self, name: str):
        raise AssertionError(f"A cultivar-only seed run must not touch {name!r} on this repository.")


def _install_repos(monkeypatch: pytest.MonkeyPatch, module: Any, species_repo: _FakeSpeciesRepo) -> None:
    monkeypatch.setattr(module, "get_family_repo", _FakeFamilyRepo)
    monkeypatch.setattr(module, "get_species_repo", lambda: species_repo)
    monkeypatch.setattr(module, "get_lifecycle_repo", _UnusedRepo)
    monkeypatch.setattr(module, "get_graph_repo", _UnusedRepo)
    monkeypatch.setattr(module, "get_ipm_repo", _FakeIpmRepo)


def _tenant_owned() -> Cultivar:
    return Cultivar(
        _key="cv_tenant",
        name=_CULTIVAR_NAME,
        species_key=_SPECIES_KEY,
        tenant_key="tenant_42",
        breeder="The tenant",
    )


def _global_row() -> Cultivar:
    return Cultivar(_key="cv_global", name=_CULTIVAR_NAME, species_key=_SPECIES_KEY, tenant_key="")


# ── the three seed runners, each reduced to its cultivar block ───────────────


def _run_plant_info(monkeypatch: pytest.MonkeyPatch, stored: list[Cultivar]) -> _FakeSpeciesRepo:
    from app.migrations import seed_plant_info

    repo = _FakeSpeciesRepo(stored)
    _install_repos(monkeypatch, seed_plant_info, repo)
    monkeypatch.setattr(seed_plant_info, "_load_yaml", lambda: {"cultivars": _YAML_CULTIVARS})
    # The loader consults species.yaml for lifecycle overrides; nothing to override here.
    monkeypatch.setattr(seed_plant_info, "load_yaml", lambda _filename: {})
    seed_plant_info.run_seed_plant_info()
    return repo


def _run_plant_info_extended(monkeypatch: pytest.MonkeyPatch, stored: list[Cultivar]) -> _FakeSpeciesRepo:
    from app.migrations import seed_plant_info_extended

    repo = _FakeSpeciesRepo(stored)
    _install_repos(monkeypatch, seed_plant_info_extended, repo)
    monkeypatch.setattr(
        seed_plant_info_extended,
        "load_yaml",
        lambda filename: {} if filename == "species.yaml" else {"cultivars": _YAML_CULTIVARS},
    )
    seed_plant_info_extended._seed_yaml_file("plant_info_test.yaml")
    return repo


def _run_adventskalender(monkeypatch: pytest.MonkeyPatch, stored: list[Cultivar]) -> _FakeSpeciesRepo:
    from app.migrations import seed_adventskalender

    repo = _FakeSpeciesRepo(stored)
    _install_repos(monkeypatch, seed_adventskalender, repo)
    monkeypatch.setattr(
        seed_adventskalender,
        "_load_data",
        # This seeder resolves species keys only from its own new_species/enrichment
        # blocks, so the species under test has to be declared there.
        lambda: {"new_species": [{"scientific_name": _SPECIES_NAME}], "cultivars": _YAML_CULTIVARS},
    )
    seed_adventskalender.run_seed_adventskalender()
    return repo


_SEEDERS = pytest.mark.parametrize(
    "run_seeder",
    [
        pytest.param(_run_plant_info, id="seed_plant_info"),
        pytest.param(_run_plant_info_extended, id="seed_plant_info_extended"),
        pytest.param(_run_adventskalender, id="seed_adventskalender"),
    ],
)


# ── the SEC-002 case, per seeder ─────────────────────────────────────────────


@_SEEDERS
def test_a_tenant_owned_row_does_not_suppress_the_global_seed_entry(monkeypatch, run_seeder):
    # SEC-002: the shared catalogue must not be decided by a tenant-chosen name.
    repo = run_seeder(monkeypatch, [_tenant_owned()])

    created_names = [c.name for c in repo.created]
    assert created_names == [_CULTIVAR_NAME], (
        "A tenant-owned cultivar of the same name suppressed the global seed entry — "
        "one tenant's ordinary write removed catalogue content from every tenant (SEC-002, #1090)."
    )
    assert repo.created[0].tenant_key == "", "the seed path must stay a global write path"


@_SEEDERS
def test_the_tenant_owned_row_itself_is_never_written_to(monkeypatch, run_seeder):
    # These seeders are skip-if-exists, never upsert: the tenant's record must come
    # out of the run byte-for-byte unchanged, not merely un-reassigned.
    repo = run_seeder(monkeypatch, [_tenant_owned()])

    assert repo.updated == []


@_SEEDERS
def test_an_existing_global_row_is_still_skipped(monkeypatch, run_seeder):
    # The idempotence the skip-set exists for is unchanged: a global row of the same
    # name means no second copy on the next boot.
    repo = run_seeder(monkeypatch, [_global_row()])

    assert repo.created == []
    assert repo.updated == []


@_SEEDERS
def test_a_legacy_row_without_an_owner_is_still_skipped(monkeypatch, run_seeder):
    # Rows written before #1090 carry no tenant_key attribute at all; the model
    # default makes them global (exactly the v0038 cutover rule), so the skip must
    # still fire and the first boot after the cutover must not duplicate the catalogue.
    legacy = Cultivar(_key="cv_legacy", name=_CULTIVAR_NAME, species_key=_SPECIES_KEY)
    repo = run_seeder(monkeypatch, [legacy])

    assert repo.created == []


@_SEEDERS
def test_an_empty_catalogue_seeds_the_entry(monkeypatch, run_seeder):
    # Control: without the ownership question the seeders behave as before, so the
    # assertions above measure the owner filter and not a broken harness.
    repo = run_seeder(monkeypatch, [])

    assert [c.name for c in repo.created] == [_CULTIVAR_NAME]
