"""Session-level guards that make a backend test tier prove it actually ran (#1434).

Two ways a green backend run can mean nothing, both measured on this repository:

**The wrong interpreter.** ``pytest`` resolved off ``PATH`` is whichever
interpreter happens to be first. Its package set is not the hash-verified one
``uv sync --locked --extra dev`` installs, and — worse in a worktree — another
checkout's editable install can answer ``import app``, so the run measures a
*different tree* than the one being edited. Both shapes were measured on
2026-09-16: the system interpreter turned 32 cases of the attachment/storage tier
into setup errors, and the primary checkout's virtual environment imported
``app`` from ``~/repos/github/kamerplanter`` while the working directory was a
worktree.

**Skips counting as passes.** ``pytest`` reports a skipped test in the exit code
exactly like a passed one. A tier whose self-skip probe stops finding its
dependency shrinks silently; nothing in the run says how many cases were meant to
execute. :func:`skip_floor_violation` turns the expected skip count into a
declared, per-tier contract (``--max-skipped N``) and names the reasons in the
failure, so that raising the number is a visible decision rather than a reflex.

The functions here are pure: they take the interpreter facts and the skip
reasons as arguments rather than reading ``sys`` or the session. That is what
lets ``tests/unit/guards/test_execution_guards.py`` drive them with a faked
``sys.prefix`` and a faked ``app.__file__``. ``tests/conftest.py`` supplies the
real values.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

#: The file whose presence marks the root of the tree under test. The backend
#: package root (``src/backend``) carries it, next to ``app/`` — so the upward
#: search from this module lands on exactly the tree whose ``app`` must answer
#: ``import app``. Deliberately a search and not ``parents[N]``: a hard-coded
#: level count breaks the moment a file moves, and it breaks by pointing at a
#: plausible wrong directory rather than by raising.
PROJECT_MARKER = "pyproject.toml"

#: How the suite is meant to be started. Quoted verbatim in both failures,
#: because a guard that only says "wrong" makes the reader guess.
_REMEDY = (
    "Run the suite from this checkout's own environment:\n"
    "    cd src/backend\n"
    "    uv sync --locked --extra dev      # or: task deps:sync\n"
    "    .venv/bin/python -m pytest <tier>\n"
    "`uv run --locked python -m pytest <tier>` is equivalent — measured on "
    "2026-09-16, it points sys.prefix at this project's .venv."
)


def find_project_root(start: Path) -> Path:
    """Return the nearest directory at or above *start* that holds ``pyproject.toml``.

    Raises:
        RuntimeError: if no such directory exists up to the filesystem root. That
            is unreachable from an installed checkout and is reported rather than
            defaulted, because every caller here uses the result as the boundary
            of "this tree" — a guessed boundary would make the guard pass on the
            wrong tree.
    """
    resolved = Path(start).resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / PROJECT_MARKER).is_file():
            return candidate
    raise RuntimeError(
        f"no {PROJECT_MARKER} at or above {resolved} — the interpreter guard cannot "
        "determine which checkout this test session belongs to."
    )


def interpreter_violation(
    *,
    app_file: str | Path,
    project_root: str | Path,
    prefix: str,
    base_prefix: str,
    executable: str | Path,
) -> str | None:
    """Describe why this interpreter must not run the suite, or ``None`` if it may.

    Args:
        app_file: ``app.__file__`` of the imported application package.
        project_root: the checkout the session belongs to (see :func:`find_project_root`).
        prefix: ``sys.prefix``.
        base_prefix: ``sys.base_prefix``.
        executable: ``sys.executable``, echoed so the reader knows what ran.

    Returns:
        A multi-line, self-explaining message naming both paths and the
        expectation, or ``None`` when the interpreter is acceptable.

    The venv test is ``sys.prefix != sys.base_prefix``, not ``VIRTUAL_ENV``:
    ``uv run --locked`` never exports ``VIRTUAL_ENV`` and a guard keyed on that
    variable would reject the project's own locked runner.
    """
    resolved_app = Path(app_file).resolve()
    root = Path(project_root).resolve()
    problems: list[str] = []

    if not resolved_app.is_relative_to(root):
        problems.append(
            "`import app` resolved to a DIFFERENT checkout than the tests being run.\n"
            f"    app imported from : {resolved_app}\n"
            f"    tests expect below: {root}\n"
            "    Another checkout's editable install is answering the import, so this\n"
            "    session would measure that tree and report on this one."
        )

    if Path(prefix).resolve() == Path(base_prefix).resolve():
        problems.append(
            "the interpreter is not a virtual environment, so its packages are not\n"
            "    the hash-verified set the lock installs.\n"
            f"    sys.prefix      : {prefix}\n"
            f"    sys.base_prefix : {base_prefix}\n"
            "    Expected these to differ (any project virtual environment)."
        )

    if not problems:
        return None

    numbered = "\n\n".join(f"  {index}. {problem}" for index, problem in enumerate(problems, start=1))
    return (
        f"This pytest session is running on the wrong interpreter (#1434).\n\n"
        f"  sys.executable    : {Path(executable)}\n\n"
        f"{numbered}\n\n"
        f"{_REMEDY}"
    )


def skip_floor_violation(*, max_skipped: int, reasons: Sequence[str]) -> str | None:
    """Describe a run that skipped more tests than its tier declares, or ``None``.

    Args:
        max_skipped: the tier's declared skip count, from ``--max-skipped``.
        reasons: one entry per skipped test, already rendered as ``-rs`` renders
            it (``path:lineno: reason``). Order is irrelevant; identical entries
            are grouped with a count, as ``-rs`` does.

    Returns:
        A message carrying the two counts and every distinct reason, or ``None``
        when the run is at or below the floor.

    Every reason is listed, not just the surplus: which of the skips is the new
    one is not knowable from the count, and a message that withheld the reasons
    would leave raising the declared number as the only available response.
    """
    if len(reasons) <= max_skipped:
        return None

    grouped = Counter(reasons)
    listing = "\n".join(f"  SKIPPED [{count}] {reason}" for reason, count in sorted(grouped.items()))
    return (
        f"This run skipped {len(reasons)} tests; the tier declares at most {max_skipped} "
        f"(--max-skipped {max_skipped}).\n"
        "A skipped test reports like a passed one, so a tier that quietly stopped "
        "executing would otherwise be green (#1434).\n\n"
        f"{listing}\n\n"
        "If a skip above is new and justified, raise the number where the tier declares "
        "it (.taskfiles/backend.yaml) in the same change that introduces it — that keeps "
        "the skip a visible decision. If it is not justified, the tier stopped running "
        "something it is meant to run."
    )
