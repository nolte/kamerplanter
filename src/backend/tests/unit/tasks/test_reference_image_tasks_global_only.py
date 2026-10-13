"""#2173 — the reference-image acquisition indexes only the global species catalogue.

The DINOv2 reference index is one shared pgvector table: ``/match`` answers every
tenant from it. A tenant's own species indexed there would be returned — key and
scientific name — to every other tenant's identification. The fan-out task
therefore reads the catalogue global-only.

The species repository double models the documented ``get_all`` contract of
``ArangoSpeciesRepository`` (``tenant_key=None`` is the unscoped whole-catalogue
read; a string is own ∪ global, so ``""`` collapses to global-only — pinned on the
real AQL in ``test_species_repository_tenant_scope.py``) rather than whatever the
task happens to pass, so a task that drops back to the unscoped read goes red here.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domain.models.species import Species
from app.tasks import reference_image_tasks as mod


class _CatalogueDouble:
    """Hybrid species catalogue: global seeds (``""``) plus tenant-owned rows."""

    def __init__(self, species: list[Species]) -> None:
        self._species = species
        self.calls: list[str | None] = []

    def get_all(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None) -> tuple[list[Species], int]:
        self.calls.append(tenant_key)
        if tenant_key is None:
            visible = list(self._species)
        else:
            visible = [s for s in self._species if s.tenant_key in ("", tenant_key)]
        return visible[offset : offset + limit], len(visible)


@pytest.fixture
def dispatched(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    task = MagicMock()
    monkeypatch.setattr(mod.acquire_reference_images_task, "delay", task)
    return task


def _install(monkeypatch: pytest.MonkeyPatch, species: list[Species]) -> _CatalogueDouble:
    repo = _CatalogueDouble(species)
    monkeypatch.setattr(mod, "get_species_repo", lambda: repo)
    return repo


def test_tenant_owned_species_is_never_dispatched_for_indexing(monkeypatch, dispatched):
    _install(
        monkeypatch,
        [
            Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
            Species(_key="sp_private_b", scientific_name="Secretus privatus", tenant_key="tenant_b"),
        ],
    )

    out = mod.acquire_all_reference_images_task.run(batch_size=10)

    dispatched_keys = [call.args[0] for call in dispatched.call_args_list]
    assert "sp_private_b" not in dispatched_keys
    assert dispatched_keys == ["sp_global"]
    assert out == {"dispatched": 1}


def test_every_global_species_is_still_dispatched_across_pages(monkeypatch, dispatched):
    globals_ = [Species(_key=f"sp_g{i}", scientific_name=f"Genus species{i}", tenant_key="") for i in range(5)]
    private = [Species(_key=f"sp_t{i}", scientific_name=f"Privatus sp{i}", tenant_key="tenant_a") for i in range(3)]
    _install(monkeypatch, globals_ + private)

    out = mod.acquire_all_reference_images_task.run(batch_size=2)

    assert [call.args[0] for call in dispatched.call_args_list] == [s.key for s in globals_]
    assert out == {"dispatched": 5}
