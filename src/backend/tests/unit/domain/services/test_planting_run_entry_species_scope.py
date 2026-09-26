"""A planting-run entry names only a species the run's tenant may read — #1871 B11.

``species_key`` of an entry came from the create-run body, the add-entry body
and the PATCH body and was stored as given, with an edge to the species; the
species then reached every plant ``create_plants`` built from the entry. The
entry's species is now resolved under the run's tenant — global, own or
granted (#1092) — on all three paths, before anything is stored.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunType
from app.common.exceptions import NotFoundError
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.planting_run_service import PlantingRunService
from tests.unit.domain.services.test_planting_run_location_ownership import FakeRunRepo, FakeSiteRepo

OWN = "tenant_own"
_READABLE = {"sp_global", "sp_own", "sp_granted"}


def _species(key: str, *, tenant_key: str) -> None:
    if key not in _READABLE:
        raise NotFoundError("Species", key)


class _Repo(FakeRunRepo):
    def __init__(self) -> None:
        super().__init__()
        self.entry_writes: list[str] = []

    def verify_entry_references(self, entry) -> None:
        return None

    def create_entry(self, entry):
        self.entry_writes.append(entry.species_key)
        stored = entry.model_copy(update={"key": f"e{len(self.entry_writes)}"})
        self.entries.append(stored)
        return stored

    def get_entry_or_raise(self, key):
        for e in self.entries:
            if e.key == key:
                return e
        raise NotFoundError("PlantingRunEntry", key)

    def update_entry(self, key, entry):
        self.entry_writes.append(entry.species_key)
        return entry


def _service(repo: _Repo) -> PlantingRunService:
    engine = MagicMock()
    engine.validate_run_type_constraints.return_value = None
    return PlantingRunService(repo, MagicMock(), engine=engine, site_repo=FakeSiteRepo(), species_resolver=_species)


def _run() -> PlantingRun:
    return PlantingRun(tenant_key=OWN, name="Salat", run_type=PlantingRunType.MONOCULTURE)


def _entry(species: str) -> PlantingRunEntry:
    return PlantingRunEntry(species_key=species, quantity=1, id_prefix="AB")


@pytest.mark.parametrize("species", ["sp_foreign", "no-such-species"])
def test_a_new_run_with_an_unreadable_species_is_refused_before_anything_is_stored(species: str) -> None:
    repo = _Repo()

    with pytest.raises(NotFoundError):
        _service(repo).create_run(_run(), [_entry("sp_own"), _entry(species)])

    assert repo.store == {} and repo.entry_writes == []


def test_adding_and_patching_an_entry_resolve_the_species() -> None:
    repo = _Repo()
    service = _service(repo)
    run = service.create_run(_run(), [_entry("sp_own")])

    with pytest.raises(NotFoundError):
        service.add_entry(run.key, _entry("sp_foreign"))
    with pytest.raises(NotFoundError):
        service.update_entry(run.key, "e1", {"species_key": "sp_foreign"}, tenant_key=OWN)

    assert repo.entry_writes == ["sp_own"]


def test_readable_species_are_accepted_on_every_path() -> None:
    repo = _Repo()
    service = _service(repo)
    run = service.create_run(_run(), [_entry("sp_global")])

    service.add_entry(run.key, _entry("sp_granted"))
    service.update_entry(run.key, "e1", {"species_key": "sp_own"}, tenant_key=OWN)

    assert repo.entry_writes == ["sp_global", "sp_granted", "sp_own"]


def test_without_a_species_resolver_an_entry_is_refused() -> None:
    repo = _Repo()
    engine = MagicMock()

    with pytest.raises(NotFoundError):
        PlantingRunService(repo, MagicMock(), engine=engine, site_repo=FakeSiteRepo()).create_run(
            _run(), [_entry("sp_own")]
        )
