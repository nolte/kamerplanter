"""The call-graph detector types what loop targets, `with` and late attributes say (#2039).

`_write_call_graph.CallGraph` resolves a call by the TYPE of its receiver and, for
a write-vocabulary name on an untyped receiver, falls back to every definition of
that name. Three spellings of a receiver whose type is written down were read as
untyped, so each of those calls was counted as an unresolved receiver and a write
behind it was linked by guess instead of by type:

* a **tuple-unpacking loop target** — ``for repo, svc in pairs``,
  ``for i, repo in enumerate(repos)``, ``for name, repo in by_name.items()``;
* a ``with … as x`` binding — a ``@contextmanager`` function annotated
  ``Iterator[X]``, an annotated ``__enter__``;
* a ``self.X`` assigned in a method other than ``__init__``.

Every ``run_*`` handler below fails against the detector before this change —
measured by restoring that file, not assumed. The ``control_*`` handlers hold the
line the other way, which matters more: the detector feeds the write-route gate
sweep, and a type it invents makes that sweep certify a gate over a call it never
saw. A tuple annotation whose arity is not written (``tuple[X, ...]``), a starred
target, a context manager whose ``__enter__`` is not annotated and a factory
function (not a constructor) assigned to ``self.X`` all stay UNTYPED and keep the
name fallback.

**Module-level ``logger = structlog.get_logger()``** — listed in #2039 as a
spelling the detector missed — is not one: ``test_the_split_sees_external_and_untyped_receivers_apart``
in ``test_write_route_gates.py`` pins ``external_logger`` as an external receiver,
and the issue text was stale on that item.
"""

import pathlib

import pytest

from tests.unit.api._write_call_graph import CallGraph

_TREE = {
    "data_access/invented_repository.py": """
class InventedRepository:
    def __init__(self, collection) -> None:
        self.collection = collection

    def write(self, data: dict) -> None:
        self.collection.insert(data)
""",
    "data_access/inert_service.py": """
class InertService:
    def write(self, data: dict) -> None:
        return None

    def close(self) -> None:
        return None
""",
    "domain/bindings.py": """
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Self

import httpx

from app.data_access.inert_service import InertService
from app.data_access.invented_repository import InventedRepository


@contextmanager
def open_repo() -> Iterator[InventedRepository]:
    yield InventedRepository(None)


@asynccontextmanager
async def open_repo_async() -> AsyncIterator[InventedRepository]:
    yield InventedRepository(None)


def make_repo():
    return InventedRepository(None)


class SelfReturning:
    def __enter__(self) -> Self:
        return self

    def write(self, data: dict) -> None:
        InventedRepository(None).write(data)


class Plain:
    def __enter__(self):
        return self


class Late:
    def __init__(self, repo: InventedRepository | None = None) -> None:
        self._seed = repo
        self._shared = InertService()
        self._factory_made = None
        self._explicit: InertService = InertService()

    def connect(self) -> None:
        self._conn = InventedRepository(None)
        self._factory_made = make_repo()
        self._explicit = InventedRepository(None)

    def attach(self, repo: InventedRepository) -> None:
        self._late = repo
        self._shared = repo

    def open_repo(self) -> Iterator[InventedRepository]:
        yield InventedRepository(None)

    def run_connected(self) -> None:
        self._conn.write({})

    def run_attached(self) -> None:
        self._late.write({})

    def run_union_keeps_both(self) -> None:
        self._shared.write({})

    def control_factory_made(self) -> None:
        self._factory_made.write({})

    def control_explicit_not_widened(self) -> None:
        self._explicit.write({})


def pairs_of() -> list[tuple[InventedRepository, InertService]]:
    return []


def run_tuple_loop(pairs: list[tuple[InventedRepository, InertService]]):
    for repo, svc in pairs:
        repo.write({})


def run_tuple_loop_second_position(pairs: list[tuple[InertService, InventedRepository]]):
    for svc, repo in pairs:
        repo.write({})


def run_enumerate_loop(repos: list[InventedRepository]):
    for index, repo in enumerate(repos):
        repo.write({})


def run_zip_loop(repos: list[InventedRepository], services: list[InertService]):
    for repo, svc in zip(repos, services):
        repo.write({})


def run_items_loop(by_name: dict[str, InventedRepository]):
    for name, repo in by_name.items():
        repo.write({})


def run_nested_target(pairs: list[tuple[InventedRepository, InertService]]):
    for index, (repo, svc) in enumerate(pairs):
        repo.write({})


def run_comprehension(pairs: list[tuple[InventedRepository, InertService]]):
    return [repo.write({}) for repo, svc in pairs]


def run_call_iterable():
    for repo, svc in pairs_of():
        repo.write({})


def run_context_manager_function():
    with open_repo() as repo:
        repo.write({})


async def run_async_context_manager_function():
    async with open_repo_async() as repo:
        repo.write({})


def run_annotated_enter():
    with SelfReturning() as manager:
        manager.write({})


def inert_through_position(pairs: list[tuple[InertService, InventedRepository]]):
    for svc, repo in pairs:
        svc.write({})
        svc.close()


def control_variadic_tuple(pairs: list[tuple[InventedRepository, ...]]):
    for repo, other in pairs:
        repo.write({})


def control_arity_mismatch(pairs: list[tuple[InventedRepository, InertService, int]]):
    for repo, svc in pairs:
        repo.write({})


def control_starred_target(pairs: list[tuple[InventedRepository, InertService]]):
    for repo, *rest in pairs:
        repo.write({})


def control_unparameterised(pairs: list):
    for repo, svc in pairs:
        repo.write({})


def control_unannotated_enter():
    with Plain() as manager:
        manager.write({})


def control_untyped_manager(opener):
    with opener() as repo:
        repo.write({})


def external_with_binding(url: str):
    with httpx.Client() as client:
        client.get(url)


def external_unpacked_value(settings: dict[str, str]):
    for key, value in settings.items():
        value.lower()
""",
}

_WRITE = "app.data_access.invented_repository::InventedRepository.write"


@pytest.fixture(scope="module")
def graph(tmp_path_factory: pytest.TempPathFactory) -> CallGraph:
    root = tmp_path_factory.mktemp("bindings")
    for relative, source in _TREE.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    built = CallGraph()
    built.parse_tree(pathlib.Path(root))
    built.link()
    return built


def _typed_callees(graph: CallGraph, qualname: str) -> set[str]:
    caller = graph.by_id[f"app.domain.bindings::{qualname}"]
    return {callee.id for callee in caller.callees if (caller.id, callee.id) not in graph.fallback_edges}


def _fell_back(graph: CallGraph, qualname: str) -> bool:
    caller = graph.by_id[f"app.domain.bindings::{qualname}"]
    return any(edge[0] == caller.id for edge in graph.fallback_edges)


class TestTheReceiverIsTypedByWhatIsWrittenDown:
    @pytest.mark.parametrize(
        "qualname",
        [
            "run_tuple_loop",
            "run_tuple_loop_second_position",
            "run_enumerate_loop",
            "run_zip_loop",
            "run_items_loop",
            "run_nested_target",
            "run_comprehension",
            "run_call_iterable",
            "run_context_manager_function",
            "run_async_context_manager_function",
            "Late.run_connected",
            "Late.run_attached",
        ],
    )
    def test_the_write_resolves_by_type_and_not_by_name(self, graph: CallGraph, qualname: str) -> None:
        caller = graph.by_id[f"app.domain.bindings::{qualname}"]

        written = {callee for callee in _typed_callees(graph, qualname) if callee.endswith(".write")}
        assert written == {_WRITE}, (
            f"{qualname}: callees={sorted(c.id for c in caller.callees)}, unresolved={caller.unresolved}"
        )
        assert "write" not in caller.unresolved
        assert not _fell_back(graph, qualname), f"{qualname}: still linked by the name fallback"

    def test_an_annotated_enter_returning_self_types_the_binding(self, graph: CallGraph) -> None:
        assert _typed_callees(graph, "run_annotated_enter") == {"app.domain.bindings::SelfReturning.write"}

    def test_an_attribute_assigned_in_two_methods_is_the_union_of_them(self, graph: CallGraph) -> None:
        """`self._shared` is an `InertService` in `__init__` and an `InventedRepository` in `attach`.

        The first assignment winning would keep only the inert one and hide the
        write behind the second — the under-approximation this guard cannot afford.
        """
        assert _typed_callees(graph, "Late.run_union_keeps_both") == {
            _WRITE,
            "app.data_access.inert_service::InertService.write",
        }

    def test_a_position_is_not_the_whole_tuple(self, graph: CallGraph) -> None:
        """The wrong-resolution refusal: `svc` is an `InertService`, never the `InventedRepository`.

        Typing every name of the target with every element of the tuple would
        link `svc.write()` to the repository's `write` and certify a write that
        the position's own type does not perform.
        """
        assert _typed_callees(graph, "inert_through_position") == {
            "app.data_access.inert_service::InertService.write",
            "app.data_access.inert_service::InertService.close",
        }
        assert graph.by_id["app.domain.bindings::inert_through_position"].id not in graph.writers()
        assert graph.by_id["app.domain.bindings::run_tuple_loop"].id in graph.writers()


class TestWhatTheSourceDoesNotSayStaysUntyped:
    @pytest.mark.parametrize(
        "qualname",
        [
            "control_variadic_tuple",
            "control_arity_mismatch",
            "control_starred_target",
            "control_unparameterised",
            "control_unannotated_enter",
            "control_untyped_manager",
            "Late.control_factory_made",
        ],
    )
    def test_the_call_keeps_the_name_fallback(self, graph: CallGraph, qualname: str) -> None:
        caller = graph.by_id[f"app.domain.bindings::{qualname}"]

        assert _typed_callees(graph, qualname) == set(), f"{qualname} was resolved by a type nothing wrote down"
        assert "write" in caller.unresolved, f"{qualname}: {caller.unresolved}"
        assert _fell_back(graph, qualname), f"{qualname}: an untyped write-vocabulary call lost its fallback"

    def test_an_explicit_annotation_is_not_widened_by_a_later_assignment(self, graph: CallGraph) -> None:
        """`self._explicit: InertService` is what the author wrote; a later assignment does not widen it."""
        assert _typed_callees(graph, "Late.control_explicit_not_widened") == {
            "app.data_access.inert_service::InertService.write"
        }


class TestTheUnresolvedSplitFollowsTheBinding:
    @pytest.mark.parametrize("qualname", ["external_with_binding", "external_unpacked_value"])
    def test_a_binding_from_outside_the_tree_is_an_external_receiver(self, graph: CallGraph, qualname: str) -> None:
        caller = graph.by_id[f"app.domain.bindings::{qualname}"]
        external = [
            call
            for call in caller._call_nodes
            if hasattr(call.func, "attr")
            and call.func.attr in {"get", "lower"}
            and graph._is_external_receiver(call.func.value, caller)
        ]

        assert len(external) == 1, f"{qualname} is still counted as a genuine annotation gap"
