"""A write handed to ``asyncio.to_thread`` is still a write on the request path (#2545 review LOW-1).

``asyncio.to_thread(fn, ...)`` runs ``fn`` in a worker thread of this process and awaits it. The call itself
resolves to nothing in the app tree (the function belongs to the standard library), so without an edge to its
first argument the detector loses every repository write a service moves off the event loop — the write-route
gate sweep and the keyed-write guard would then certify a method as read-only that writes.
"""

import pathlib

import pytest

from tests.unit.api._write_call_graph import CallGraph

_TREE = {
    "data_access/threaded_repository.py": """
class ThreadedRepository:
    def __init__(self, collection) -> None:
        self.collection = collection

    def remove(self, key: str) -> None:
        self.collection.delete(key)

    def read(self, key: str) -> dict:
        return {"key": key}
""",
    "domain/threaded_service.py": """
import asyncio

from app.data_access.threaded_repository import ThreadedRepository


class ThreadedService:
    def __init__(self, repo: ThreadedRepository) -> None:
        self._repo = repo

    async def remove_in_a_thread(self, key: str) -> None:
        await asyncio.to_thread(self._repo.remove, key)

    async def read_in_a_thread(self, key: str) -> dict:
        return await asyncio.to_thread(self._repo.read, key)
""",
}


@pytest.fixture(scope="module")
def graph(tmp_path_factory: pytest.TempPathFactory) -> CallGraph:
    root = tmp_path_factory.mktemp("to_thread")
    for relative, source in _TREE.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    built = CallGraph()
    built.parse_tree(pathlib.Path(root))
    built.link()
    return built


def test_a_repository_write_passed_to_to_thread_makes_the_caller_a_writer(graph: CallGraph) -> None:
    caller = graph.by_id["app.domain.threaded_service::ThreadedService.remove_in_a_thread"]

    assert "app.data_access.threaded_repository::ThreadedRepository.remove" in {c.id for c in caller.callees}
    assert "app.domain.threaded_service::ThreadedService.remove_in_a_thread" in graph.writers()


def test_a_read_passed_to_to_thread_does_not(graph: CallGraph) -> None:
    assert "app.domain.threaded_service::ThreadedService.read_in_a_thread" not in graph.writers()
