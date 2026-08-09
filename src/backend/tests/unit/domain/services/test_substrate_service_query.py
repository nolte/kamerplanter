"""#1099 defect 5 — the substrate list ``query`` reaches the repository.

``GET /api/v1/substrates`` took only offset/limit, so the documented
case-insensitive name/brand filter was dropped on the floor and every query
answered "no such substrate" — the wrong answer that lets an agent seed a
duplicate. These tests pin the service → repository wiring that carries the
term through; the AQL itself lives in the repository and is exercised against a
real ArangoDB in the integration layer.
"""

from __future__ import annotations

from app.domain.models.substrate import Substrate
from app.domain.services.substrate_service import SubstrateService


class _RecordingRepo:
    """Records exactly what ``list_substrates`` forwards to ``get_all_substrates``."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, int, str | None]] = []

    def get_all_substrates(self, offset: int = 0, limit: int = 50, query: str | None = None):
        self.calls.append((offset, limit, query))
        return [Substrate(_key="s1", brand="BioBizz", name_de="BioBizz Light·Mix")], 1


def test_list_substrates_forwards_the_query_to_the_repository():
    repo = _RecordingRepo()
    service = SubstrateService(repo)

    items, total = service.list_substrates(offset=0, limit=25, query="biobizz")

    assert repo.calls == [(0, 25, "biobizz")], "the query must reach the repository, not be dropped"
    assert total == 1
    assert items[0].name_de == "BioBizz Light·Mix"


def test_list_substrates_without_a_query_forwards_none():
    repo = _RecordingRepo()
    service = SubstrateService(repo)

    service.list_substrates(offset=10, limit=50)

    assert repo.calls == [(10, 50, None)]
