"""Load a repository-root ``scripts/*.py`` gate into the backend test suite.

The source-tree gates (``scripts/check_layer_imports.py``,
``scripts/check_tenant_body_field.py``,
``scripts/check_workflow_gate_integrity.py``, …) deliberately live outside the
backend package: they run in the required ``static`` lane on a bare runner with
none of this project's dependencies installed, so they must not be importable
only as ``app.something``. Their tests, however, belong in ``tests/unit/`` —
``pytest tests/unit/`` is a CI gate, so a backend change that trips one of them
goes red in the backend suite too, not only in pre-commit.

That leaves loading them by path. This module is the one implementation of that.
``test_schema_example_ratchet.py`` and ``test_boundary_validation_check.py``
predate it and carry their own copies; they are left alone rather than
refactored from a change that is about something else.

Usage::

    from tests.support.repo_scripts import load_repo_script

    checker = load_repo_script("check_layer_imports")
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index breaks silently
    the moment the test file moves, which has bitten this repository before.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``scripts/``, or None.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    return None


def load_repo_script(stem: str) -> ModuleType:
    """Execute ``scripts/<stem>.py`` and return it as a module.

    Registration in ``sys.modules`` happens **before** ``exec_module`` because
    these scripts define ``@dataclass`` types, and ``dataclass`` resolves its own
    module through ``sys.modules`` while the module body is still running.

    Skips the whole calling module — rather than erroring — when the script is
    unreachable, which happens only outside a full checkout.

    Args:
        stem: File name of the script without the ``.py`` suffix.

    Returns:
        The executed module.
    """
    repo_root = find_repo_root(Path(__file__).resolve())
    if repo_root is None:  # pragma: no cover — only outside a full checkout
        pytest.skip(
            "checkout root not found (no ancestor holds both Taskfile.yaml and scripts/); "
            f"scripts/{stem}.py is unreachable from here",
            allow_module_level=True,
        )

    path = repo_root / "scripts" / f"{stem}.py"
    if not path.is_file():  # pragma: no cover — only on a partial checkout
        pytest.skip(f"{path} does not exist", allow_module_level=True)

    spec = importlib.util.spec_from_file_location(f"_repo_script_{stem}", path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"_repo_script_{stem}"] = module
    spec.loader.exec_module(module)
    return module
