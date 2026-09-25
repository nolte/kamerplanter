"""pytest plugin the lane-inputs recorder loads to attribute reads to test modules (#1749).

``scripts/ci/lane_inputs.py record`` runs an invocation under ``strace -ff -ttt``
and, for a pytest invocation, loads this plugin (``PYTHONPATH`` + ``-p
lane_inputs_markers`` in ``PYTEST_ADDOPTS``). Before pytest collects a test
module and before it runs a test, the plugin OPENS a marker file whose name
says which module is active::

    <marker dir>/collect~<quoted module path>
    <marker dir>/run~<quoted module path>
    <marker dir>/none~

and, once a test's call phase has actually executed (not skipped), ::

    <marker dir>/ran~<quoted module path>

which is what puts the module on the manifest's ``test_modules``: a module whose
tests were all skipped did not judge anything in that lane.

The open is a syscall like every read, with a timestamp, so the recorder can
put each read of the whole process tree — the pytest process, its threads and
every subprocess a test spawned — on the same timeline and attribute it to the
module active at that moment. A marker is a syscall rather than a log line
because the trace is the only record whose clock the reads share.

Module paths are repo-relative (``LANE_INPUTS_REPO_ROOT``). A test outside the
checkout (a nested pytest session over a temporary directory) sets no marker,
and a marker is restored, not cleared, when it ends — so an in-process
``pytester`` run keeps its reads on the test that started it. Only the process
that first loads the plugin emits markers (``LANE_INPUTS_MARKER_PID``): a pytest
subprocess of a test inherits the environment, and its markers would otherwise
re-attribute the outer test's reads.

Standard library plus pytest. Does nothing unless ``LANE_INPUTS_MARKERS`` is set.
"""

from __future__ import annotations

import os
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

import pytest

MARKERS_ENV = "LANE_INPUTS_MARKERS"
REPO_ROOT_ENV = "LANE_INPUTS_REPO_ROOT"
OWNER_ENV = "LANE_INPUTS_MARKER_PID"

_stack: list[str] = []


def _enabled() -> bool:
    directory = os.environ.get(MARKERS_ENV)
    if not directory:
        return False
    owner = os.environ.setdefault(OWNER_ENV, str(os.getpid()))
    return owner == str(os.getpid())


def _module(path: Path | None) -> str | None:
    root = os.environ.get(REPO_ROOT_ENV)
    if path is None or not root:
        return None
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return None


def _mark(name: str) -> None:
    directory = os.environ[MARKERS_ENV]
    fd = os.open(os.path.join(directory, name), os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC, 0o600)
    os.close(fd)


@contextmanager
def _active(kind: str, module: str | None) -> Iterator[None]:
    if module is None or not _enabled():
        yield
        return
    name = f"{kind}~{quote(module, safe='')}"
    _stack.append(name)
    _mark(name)
    try:
        yield
    finally:
        _stack.pop()
        _mark(_stack[-1] if _stack else "none~")


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(collector: pytest.Collector) -> Generator[None, object, object]:
    module = _module(collector.path) if isinstance(collector, pytest.Module) else None
    with _active("collect", module):
        return (yield)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    # The active marker, not the report's path: the report is about the item
    # `pytest_runtest_protocol` below just marked, and that marker is the one
    # spelling of its module the recorder already reads.
    # `skipped` covers a `pytest.skip()` inside the test body, which still reports a call phase.
    if report.when != "call" or report.skipped or not _stack or not _stack[-1].startswith("run~") or not _enabled():
        return
    _mark("ran~" + _stack[-1].removeprefix("run~"))


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, object, object]:
    with _active("run", _module(item.path)):
        return (yield)
