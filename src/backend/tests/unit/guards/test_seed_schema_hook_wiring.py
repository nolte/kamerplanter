"""Guard the seed-schema hook against a return to a per-file opt-in list (#1406).

**What this refuses.** ``.pre-commit-config.yaml`` used to carry twelve
``check-jsonschema`` hooks over the seed directory — eleven naming a single file
by an anchored regex, one globbing ``plant_info*.yaml``. They reached 20 of the
36 seed files, while the conformance test (converted by #1030/#1435 to derive its
corpus from each file's ``$schema`` directive) reached all 32 declaring ones. The
two enforcement paths over the same rule therefore covered different files, and a
newly added seed file was checked by the test and by no hook at all.

Removing the list is a one-off; keeping it removed is what this module does. It
asserts two things against the real config:

* **the collecting hook exists** and its ``files:`` pattern matches *every* seed
  YAML in the tree — derived by running the pattern over the directory, not by
  comparing the regex to a literal, so a pattern that is textually different but
  still complete passes and one that silently narrows does not;
* **no hook selects an individual seed file.** Any pattern that matches at least
  one seed YAML but not all of them is the opt-in shape coming back, whatever the
  hook is called.

Traces to issue #1406 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

#: The hook that must carry the whole seed directory.
COLLECTING_HOOK_ID = "seed-schema-conformance"

#: Seed directory, relative to the checkout root.
SEED_DIR = Path("src/backend/app/migrations/seed_data")


def _find_repo_root(start: Path) -> Path:
    """Walk up from *start* to the checkout root, identified by its markers.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``scripts/``.

    Raises:
        RuntimeError: If no ancestor carries both markers.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise RuntimeError(f"no checkout root above {start} (looked for Taskfile.yaml + scripts/)")


_ROOT = _find_repo_root(Path(__file__).resolve())
_CONFIG = _ROOT / ".pre-commit-config.yaml"


def _hooks() -> list[dict]:
    """Return every hook entry in ``.pre-commit-config.yaml``, flattened across repos."""
    config = yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))
    return [hook for repo in config["repos"] for hook in repo.get("hooks", [])]


def _seed_yaml_paths() -> list[str]:
    """Return every seed YAML as a repo-root-relative POSIX path."""
    paths = sorted((_ROOT / SEED_DIR).glob("*.y*ml"))
    assert paths, f"no seed YAML found under {SEED_DIR} — the guard would be vacuous"
    return [p.relative_to(_ROOT).as_posix() for p in paths]


def _matches(pattern: str, paths: list[str]) -> list[str]:
    """Return the subset of *paths* the pre-commit ``files:`` *pattern* selects."""
    compiled = re.compile(pattern)
    return [p for p in paths if compiled.search(p)]


class TestTheCollectingHookCarriesTheWholeDirectory:
    """The hook that replaced the twelve per-file ones must reach every seed file."""

    def test_the_hook_exists_and_runs_the_shared_script(self) -> None:
        """The hook is wired and points at the script the conformance test imports."""
        hooks = [h for h in _hooks() if h.get("id") == COLLECTING_HOOK_ID]
        assert len(hooks) == 1, (
            f"expected exactly one '{COLLECTING_HOOK_ID}' hook in .pre-commit-config.yaml, found {len(hooks)}"
        )
        entry = hooks[0].get("entry", "")
        assert "scripts/check_seed_schema.py" in entry, (
            f"'{COLLECTING_HOOK_ID}' must run scripts/check_seed_schema.py — the module whose "
            f"NO_SCHEMA_DECLARED / SCHEMA_DEBT_CEILING registers the conformance test imports. Found: {entry!r}"
        )
        assert (_ROOT / "scripts" / "check_seed_schema.py").is_file()

    def test_its_pattern_selects_every_seed_file(self) -> None:
        """Derived coverage: run the configured pattern over the real directory."""
        hook = next(h for h in _hooks() if h.get("id") == COLLECTING_HOOK_ID)
        pattern = hook.get("files")
        assert pattern, f"'{COLLECTING_HOOK_ID}' carries no files: pattern — it would run on nothing"
        paths = _seed_yaml_paths()
        missed = sorted(set(paths) - set(_matches(pattern, paths)))
        assert not missed, (
            f"'{COLLECTING_HOOK_ID}' files: {pattern!r} does not select these seed files — "
            "the hook layer would again be narrower than the conformance test:\n" + "\n".join(missed)
        )

    def test_it_does_not_reach_outside_the_seed_directory(self) -> None:
        """A pattern broad enough to catch siblings would validate unrelated YAML."""
        hook = next(h for h in _hooks() if h.get("id") == COLLECTING_HOOK_ID)
        compiled = re.compile(hook["files"])
        outsiders = [
            ".pre-commit-config.yaml",
            "src/backend/app/migrations/seed_data/schemas/species.schema.yaml",
            "helm/kamerplanter/values.yaml",
        ]
        caught = [p for p in outsiders if compiled.search(p)]
        assert not caught, f"files: {hook['files']!r} also selects non-seed files: {caught}"


class TestTheOptInListStaysGone:
    """No hook may select a proper subset of the seed directory."""

    def test_no_hook_names_individual_seed_files(self) -> None:
        """Partial coverage of the seed tree is the fail-open shape #1406 removed."""
        paths = _seed_yaml_paths()
        offenders: list[str] = []
        for hook in _hooks():
            pattern = hook.get("files")
            if not pattern:
                continue
            matched = _matches(pattern, paths)
            if matched and len(matched) < len(paths):
                offenders.append(
                    f"{hook.get('id', '<no id>')} ({hook.get('name', '')}): files: {pattern!r} "
                    f"selects {len(matched)} of {len(paths)} seed files"
                )
        assert not offenders, (
            "Hooks select only part of the seed directory. Seed-schema enforcement is "
            "directory-wide (#1406) — extend scripts/check_seed_schema.py's registers instead "
            "of narrowing a files: pattern:\n" + "\n".join(offenders)
        )


class TestTheGuardCanFail:
    """Negative controls: the two assertions above must reject the shapes they name.

    A guard nobody has watched fail is a guard nobody knows works — and both
    assertions are regex-over-tree comparisons, which are exactly the kind that
    silently pass when the pattern stops matching anything.
    """

    @pytest.mark.parametrize(
        "pattern",
        [
            r"^src/backend/app/migrations/seed_data/species\.yaml$",
            r"^src/backend/app/migrations/seed_data/plant_info.*\.yaml$",
        ],
    )
    def test_a_per_file_pattern_is_detected_as_partial(self, pattern: str) -> None:
        """The two retired shapes — one named file, one name-glob — both count as partial."""
        paths = _seed_yaml_paths()
        matched = _matches(pattern, paths)
        assert matched, f"{pattern!r} matches nothing — the detection below would be vacuous"
        assert len(matched) < len(paths), f"{pattern!r} unexpectedly covers the whole tree"

    def test_the_configured_pattern_is_the_one_shape_that_passes(self) -> None:
        """The live pattern covers everything, so it is not flagged as partial."""
        hook = next(h for h in _hooks() if h.get("id") == COLLECTING_HOOK_ID)
        paths = _seed_yaml_paths()
        assert len(_matches(hook["files"], paths)) == len(paths)
