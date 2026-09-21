"""#1480 — a ``transformers`` bump must not buy itself a 2024 ONNX exporter.

**The measurement this file makes permanent.** ``docker/reranker-service``
locks ``transformers`` at 4.57.6, which Trivy reports with three HIGH CVEs
(CVE-2026-9856, CVE-2026-4372, CVE-2026-5241) and one MEDIUM (CVE-2026-1839),
all fixed in the 5.x line. The obvious remedy — widen
``[project].dependencies`` to ``transformers>=5.10,<6`` and relock — *resolves*.
It does not fail, and that is the trap. Measured 2026-09-20 with the pinned
toolchain (``uv==0.12.17``)::

    Updated optimum v2.1.0 -> v1.17.1
    Removed optimum-onnx v0.1.0
    Updated transformers v4.57.6 -> v5.17.0

``optimum-onnx`` — the package that carries the ONNX exporter since optimum's
2.x split — declares ``transformers>=4.36,<4.58`` in **every** release it has
published (0.0.1 … 0.1.0, checked against the PyPI metadata on 2026-09-20). So
the only way a resolver can satisfy ``transformers>=5`` next to
``optimum[onnxruntime]`` is to walk ``optimum`` back to 1.17.1, released
2024-02-18, whose ``transformers[sentencepiece]>=4.26.0`` has no ceiling at all.
The lock then looks healthy, Trivy goes quiet, and the export stage dies five
seconds into a twenty-minute image build::

    File "/opt/venv/.../optimum/utils/input_generators.py", line 23, in <module>
        from transformers.utils import is_tf_available, is_torch_available
    ImportError: cannot import name 'is_tf_available' from 'transformers.utils'

**Why a guard and not just the failing build.** The build catches it — but only
the build, only for the one image that has a ``build-*`` job, and only after a
runner slot and a model download. A silent two-year downgrade of a build-time
toolchain is the kind of thing that should be legible in the diff review of the
lock, which is where this assertion speaks. NFR-018 §1: a rule that only a
twenty-minute job can express is a rule most changes never meet.

**Deliberately narrow.** This says nothing about which ``transformers`` version
is right — that is the resolver's job, and #1480 stays open precisely because no
answer exists yet that is both CVE-free and exportable. It says only that a tree
which asks for ``optimum`` gets the generation of ``optimum`` that still has an
exporter in it. When ``optimum-onnx`` lifts its ceiling, the bump this file
blocks nothing about becomes possible and this guard stays true.

**Stated as a class, not as a file list.** Every ``pyproject.toml`` in the
checkout that names ``optimum`` is checked, so the sibling image
(``docker/embedding-service``, which resolves the identical open
``transformers>=4.46.0`` to 5.17.0 because it has no exporter beside it) is
covered the day it grows one. Traces to #1480 (no TC-ID: a dependency gate is
not a user-facing case).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

# optimum 2.0.0 is the release that split the ONNX exporter out into
# `optimum-onnx`. Everything below it is the pre-split line, whose newest member
# (1.17.1) predates transformers 5 by nearly two years. The floor is the split,
# not a specific patch level: Renovate may move 2.x freely.
_OPTIMUM_FLOOR = Version("2.0.0")

# The extras under which optimum pulls its exporter in. Requesting one of them
# and NOT getting `optimum-onnx` in the lock is the same defect wearing a
# different resolution: optimum 1.x carried `optimum.onnxruntime` in its own
# distribution, so the import line in the Dockerfile still parses.
_ONNX_EXTRAS = frozenset({"onnx", "onnxruntime", "onnxruntime-gpu"})

# Directories that hold third-party trees rather than this repository's own.
_SKIPPED_DIRS = frozenset({".git", ".venv", "node_modules", ".mypy_cache", ".ruff_cache"})


def _project_files() -> list[Path]:
    """Every ``pyproject.toml`` belonging to this checkout."""
    found = [
        path
        for path in _REPO_ROOT.rglob("pyproject.toml")
        if not _SKIPPED_DIRS.intersection(path.relative_to(_REPO_ROOT).parts)
    ]
    assert found, f"no pyproject.toml under {_REPO_ROOT} — the sweep would be vacuously green"
    return sorted(found)


def _declared_requirements(document: dict[str, object]) -> list[Requirement]:
    """``[project].dependencies`` plus every PEP 735 group, as requirements.

    Both halves matter and for opposite reasons: the runtime dependency list is
    what ships, and the ``build`` group is where ``optimum[onnxruntime]`` sits in
    the tree this guard was written for — a group uv resolves into the *same*
    lock as the runtime, which is the whole mechanism behind the downgrade.
    """
    raw: list[str] = []

    project = document.get("project")
    if isinstance(project, dict):
        raw.extend(entry for entry in project.get("dependencies", []) if isinstance(entry, str))

    groups = document.get("dependency-groups")
    if isinstance(groups, dict):
        for members in groups.values():
            if isinstance(members, list):
                raw.extend(entry for entry in members if isinstance(entry, str))

    requirements: list[Requirement] = []
    for entry in raw:
        try:
            requirements.append(Requirement(entry))
        except Exception:  # pragma: no cover — a malformed pin is another gate's business
            continue
    return requirements


def _locked_versions(lock_path: Path) -> dict[str, Version]:
    """``{canonical name: version}`` for every package pinned in *lock_path*."""
    document = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    locked: dict[str, Version] = {}
    for package in document.get("package", []):
        name = package.get("name")
        version = package.get("version")
        if isinstance(name, str) and isinstance(version, str):
            locked[canonicalize_name(name)] = Version(version)
    return locked


class _ExportTree:
    """A checkout tree that asks for ``optimum``, with its lock beside it."""

    def __init__(self, project_file: Path, requirement: Requirement) -> None:
        self.project_file = project_file
        self.requirement = requirement
        self.lock_file = project_file.with_name("uv.lock")

    @property
    def label(self) -> str:
        return str(self.project_file.relative_to(_REPO_ROOT))

    @property
    def wants_onnx_exporter(self) -> bool:
        return bool(_ONNX_EXTRAS.intersection(self.requirement.extras))


def _export_trees() -> list[_ExportTree]:
    trees: list[_ExportTree] = []
    for project_file in _project_files():
        document = tomllib.loads(project_file.read_text(encoding="utf-8"))
        for requirement in _declared_requirements(document):
            if canonicalize_name(requirement.name) == "optimum":
                trees.append(_ExportTree(project_file, requirement))
    return trees


_EXPORT_TREES = _export_trees()


class TestOptimumStaysOnThePostSplitLine:
    """The falsifier for the #1480 downgrade path."""

    def test_at_least_one_tree_declares_optimum(self) -> None:
        """Without this, every assertion below is vacuously true.

        The guard is written as a class over the checkout, so its non-vacuity is
        a fact about the checkout and has to be asserted, not assumed. If the
        reranker ever stops exporting through optimum, this is the line that
        says so — and the day it fires is the day to delete this module rather
        than to silence it.
        """
        assert _EXPORT_TREES, (
            "no pyproject.toml in the checkout declares `optimum` — "
            "either the ONNX export moved to another toolchain (delete this guard) "
            "or the sweep stopped finding it (fix the sweep)"
        )

    @pytest.mark.parametrize("tree", _EXPORT_TREES, ids=lambda tree: tree.label)
    def test_lock_exists_beside_the_project(self, tree: _ExportTree) -> None:
        """A tree without a lock cannot be checked, so it must not exist (NFR-009 §2.3)."""
        assert tree.lock_file.is_file(), (
            f"{tree.label} declares `optimum` but has no uv.lock beside it; "
            "an unhashed export toolchain is exactly what #1374 removed"
        )

    @pytest.mark.parametrize("tree", _EXPORT_TREES, ids=lambda tree: tree.label)
    def test_locked_optimum_is_not_the_pre_split_line(self, tree: _ExportTree) -> None:
        """optimum < 2.0 in the lock means a resolver backtracked to reach it.

        Nothing in this repository asks for optimum 1.x. The only way it lands in
        a lock is as the price a resolver paid for some other constraint — in
        #1480, for ``transformers>=5``. That price is a 2024 exporter against a
        2026 ``transformers``, and it does not run.
        """
        locked = _locked_versions(tree.lock_file)
        optimum = locked.get("optimum")
        assert optimum is not None, f"{tree.label} declares `optimum` but {tree.lock_file.name} pins no such package"
        assert optimum >= _OPTIMUM_FLOOR, (
            f"{tree.label}: optimum is locked at {optimum}, below the {_OPTIMUM_FLOOR} "
            "post-split floor. A resolver reached it by backtracking, almost certainly to "
            f"satisfy transformers {locked.get('transformers')} — and optimum 1.x imports "
            "`is_tf_available` from `transformers.utils`, which transformers 5 removed. "
            "The export stage of docker/reranker-service/Dockerfile dies on that import. "
            "See #1480: no optimum-onnx release accepts transformers >= 4.58 yet."
        )

    @pytest.mark.parametrize(
        "tree",
        [tree for tree in _EXPORT_TREES if tree.wants_onnx_exporter],
        ids=lambda tree: tree.label,
    )
    def test_onnx_extra_really_pulls_the_exporter_package(self, tree: _ExportTree) -> None:
        """``optimum[onnxruntime]`` must land ``optimum-onnx`` in the lock.

        The version floor above and this presence check are two spellings of the
        same requirement, and each catches a resolution the other misses: a lock
        could carry optimum 2.x with the extra dropped (no exporter, floor still
        green), or optimum 1.x with the exporter fused into the main
        distribution (extra satisfied, floor red).
        """
        locked = _locked_versions(tree.lock_file)
        assert "optimum-onnx" in locked, (
            f"{tree.label} asks for optimum{sorted(tree.requirement.extras)} but "
            f"{tree.lock_file.name} pins no `optimum-onnx`. Since optimum 2.0 that package "
            "*is* the ONNX exporter; a lock without it either dropped the extra or fell back "
            "to the pre-split line (#1480)."
        )
