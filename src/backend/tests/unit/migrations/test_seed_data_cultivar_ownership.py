"""The plant-info seed run never writes over a tenant-owned cultivar (#1090 P2).

``seed_data.seed_cultivars`` upserts the YAML cultivar catalogue **matched by
name**, per species. Before #1090 a cultivar had no owner, so "the row named
``Genovese`` under ``Ocimum basilicum``" was unambiguous. With tenant ownership it
no longer is: a tenant may create their own ``Genovese``, and on the next boot the
seed run would find *that* row by name and rewrite it from the YAML entry —
replacing the tenant's breeder/traits/notes and (before the repository guard)
reassigning the row to the global catalogue.

Two independent layers now stop this, and each is pinned separately:

* the **repository** refuses to rewrite ``tenant_key`` on any update
  (``tests/unit/data_access/arango/test_cultivar_repository_ownership.py``), which
  saves the *owner* but not the tenant's *field values*;
* the **seed loader**, tested here, only ever matches against the global catalogue,
  so a tenant-owned row is never the target of a seed write at all — and the global
  seed entry it was shadowing gets created rather than silently skipped.

The fake repository below deliberately implements the *pre-#1090* full-replace
semantics (it stores exactly the model it is handed). That keeps this test honest:
it fails unless ``seed_cultivars`` itself is ownership-aware, and cannot be
accidentally satisfied by the repository-level guard.
"""

from __future__ import annotations

from app.domain.models.species import Cultivar
from app.migrations.seed_data import seed_cultivars

_SPECIES_KEY_MAP = {"Ocimum basilicum": "sp_basil"}
_YAML = {"Ocimum basilicum": [{"name": "Genovese", "breeder": "Seed Co", "patent_status": "none"}]}


class _FakeSpeciesRepo:
    """In-memory cultivar store with plain full-replace update semantics."""

    def __init__(self, cultivars: list[Cultivar]) -> None:
        self._by_key = {c.key or "": c for c in cultivars}
        self.created: list[Cultivar] = []
        self.updated: list[tuple[str, Cultivar]] = []

    def get_cultivars(self, species_key: str) -> list[Cultivar]:
        return [c for c in self._by_key.values() if c.species_key == species_key]

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.created.append(cultivar)
        return cultivar

    def update_cultivar(self, key: str, cultivar: Cultivar) -> Cultivar:
        self.updated.append((key, cultivar))
        self._by_key[key] = cultivar
        return cultivar


def _owned(key: str, tenant_key: str, name: str = "Genovese") -> Cultivar:
    return Cultivar(_key=key, name=name, species_key="sp_basil", tenant_key=tenant_key, breeder="The tenant")


def test_a_same_named_tenant_cultivar_is_not_the_seed_upsert_target():
    # The core P2 case: the tenant's row must not be touched at all.
    repo = _FakeSpeciesRepo([_owned("cv_tenant", "tenant_42")])

    seed_cultivars(repo, _YAML, _SPECIES_KEY_MAP)

    assert repo.updated == [], "the seed run rewrote a tenant-owned cultivar it matched by name"


def test_the_global_seed_entry_is_created_alongside_the_tenant_row():
    # Not writing over the tenant's row must not mean losing the seed entry: the
    # global catalogue still owes every tenant a 'Genovese'.
    repo = _FakeSpeciesRepo([_owned("cv_tenant", "tenant_42")])

    seed_cultivars(repo, _YAML, _SPECIES_KEY_MAP)

    assert len(repo.created) == 1
    assert repo.created[0].name == "Genovese"
    assert repo.created[0].tenant_key == "", "the seed path must stay a global write path"


def test_an_existing_global_cultivar_is_still_upserted():
    # The ordinary idempotent re-seed is unchanged: a global row of the same name is
    # updated in place, not duplicated on every boot.
    repo = _FakeSpeciesRepo([_owned("cv_global", "")])

    seed_cultivars(repo, _YAML, _SPECIES_KEY_MAP)

    assert repo.created == []
    assert [key for key, _cv in repo.updated] == ["cv_global"]
    assert repo.updated[0][1].breeder == "Seed Co"


def test_a_legacy_row_without_an_owner_is_still_upserted():
    # Rows written before #1090 carry no tenant_key; the model default makes them
    # global, so the pre-existing upsert must keep finding them (no duplicate wave
    # on the first boot after the cutover).
    repo = _FakeSpeciesRepo([Cultivar(_key="cv_legacy", name="Genovese", species_key="sp_basil")])

    seed_cultivars(repo, _YAML, _SPECIES_KEY_MAP)

    assert repo.created == []
    assert [key for key, _cv in repo.updated] == ["cv_legacy"]


def test_a_foreign_species_entry_is_skipped():
    # Unchanged guard: a YAML species that never resolved to a key writes nothing.
    repo = _FakeSpeciesRepo([])

    seed_cultivars(repo, _YAML, {})

    assert repo.created == []
    assert repo.updated == []
