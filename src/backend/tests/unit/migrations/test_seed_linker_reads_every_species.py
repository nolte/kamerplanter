"""The seed phase-sequence linker binds every species, not the first 1000 (#2015).

:func:`app.migrations.seed_data.link_indoor_species_to_phase_sequence` read
``species_repo.get_all(0, 1000)`` once. ``tenant_key=None`` is the whole catalogue —
the ~230 global seeds plus every tenant's own species, which a CSV import grows
without bound — so a species past row 1000 (``_key`` order) was never bound and
its plants started with ``current_phase_key: null``.

The test drives the real linker with a species repository double that pages like
``ArangoSpeciesRepository.get_all`` (``offset``/``limit`` honoured, ``_key`` order,
full ``total``, no ``all_tenants`` argument) and asserts on the edges it inserts.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.migrations import seed_data
from app.migrations.perennial_binding import INDOOR_DEFAULT_SEQUENCE


class _SpeciesRepo:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = sorted(rows, key=lambda r: r.key)

    def get_all(self, offset=0, limit=50, *, tenant_key=None):
        assert tenant_key is None, "the linker reads the whole catalogue"
        if limit < 1 or offset < 0:
            raise ValueError("bad paging window")
        return list(self.rows[offset : offset + limit]), len(self.rows)


def test_species_past_the_old_1000_window_is_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    species = [
        SimpleNamespace(
            key=f"sp{i:05d}",
            scientific_name=f"Genus species{i:05d}",
            photosynthesis_type=None,
            growth_habit=None,
        )
        for i in range(1001)
    ]
    ps_repo = MagicMock()
    ps_repo.get_all_sequences.return_value = ([SimpleNamespace(name=INDOOR_DEFAULT_SEQUENCE, key="idk")], 1)
    lifecycle_repo = MagicMock()
    lifecycle_repo.get_lifecycle_by_species.return_value = None
    edge_col = MagicMock()
    db = MagicMock()
    db.aql.execute.return_value = []  # no species is bound yet
    db.collection.return_value = edge_col

    monkeypatch.setattr(seed_data, "get_phase_sequence_repo", lambda: ps_repo)
    monkeypatch.setattr(seed_data, "get_species_repo", lambda: _SpeciesRepo(species))
    monkeypatch.setattr(seed_data, "get_lifecycle_repo", lambda: lifecycle_repo)
    monkeypatch.setattr(seed_data, "get_db", lambda: db)

    seed_data.link_indoor_species_to_phase_sequence()

    bound = [c.args[0]["_from"] for c in edge_col.insert.call_args_list]
    assert bound == [f"species/{s.key}" for s in species]
