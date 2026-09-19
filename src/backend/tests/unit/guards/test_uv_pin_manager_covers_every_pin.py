"""#1464 — every `[tool.uv].required-version` pin is READ by the custom manager.

**The defect this is written against, and it was introduced by the change that
added this file's subject.** ``renovate.json5`` carries a custom regex manager
whose ``managerFilePatterns`` enumerates the ``pyproject.toml`` files it ages the
uv pin in. When #1464 gave ``src/libs/kp_vectordb`` and
``src/libs/kp_errortracking`` a lock, it gave them a
``required-version = "==0.12.15"`` too — and did not widen that list. The
resulting failure is not "a pin ages": it is the ``uv toolchain`` pull request
moving FIVE pins, leaving two at the old version, and
``test_library_lock_hash_verification.py``'s
``test_the_libraries_pin_the_same_uv_as_the_backend`` then reddening the required
``Write-route and tree guards`` lane — a red gate produced by Renovate doing
exactly what it was configured to do. The review of that pull request caught it;
nothing in the tree would have.

**Why a guard and not a corrected list.** The list was correct on the day it was
written and wrong two pull requests later, which is the whole failure class: an
enumeration maintained by whoever remembers it. The pin count in the
``uv toolchain`` comment block is the same shape and was ALREADY stale before
#1464 — it claimed seven ``setup-uv`` steps against ten on develop. A count in a
comment ages silently; this property does not.

**The property.** Every ``pyproject.toml`` in the checkout that declares
``[tool.uv].required-version`` is matched by at least one
``managerFilePatterns`` entry of the custom manager that reads that key — and
nothing in that list points at a file which does not exist, which is the other
direction and equally a defect (a pattern nobody notices has stopped matching).

**Why the config is read TEXTUALLY and not parsed.** ``renovate.json5`` is JSON5
— comments, single quotes, trailing commas, unquoted keys — and no JSON5 parser
is in the backend's locked dependency set. Adding one for a guard would put a
dependency into the required lane's install for the sake of reading one array,
so the manager block is located and its regex literals extracted instead. Every
step of that extraction is asserted rather than trusted: the block must be
found, the pattern list must be non-empty, and it must contain the backend pin
that has been in it since #1383. A silently empty extraction would make the
sweep vacuously green, which is the failure mode this repository pays for most
often. Traces to #1464 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from tests.support.renovate_config import array_value, strip_comments
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_CONFIG = _REPO_ROOT / "renovate.json5"

#: Directories the pyproject sweep never descends into — build and environment
#: artefacts, not source. A virtualenv holds other projects' pyproject.toml by
#: the hundred and every one of them would be a phantom finding.
_EXCLUDED = frozenset({".git", ".venv", ".venv-docs", "node_modules", "site-packages", "__pycache__"})

#: The key whose readers this file is about.
_PIN_KEY = "required-version"

#: A Renovate `managerFilePatterns` regex literal: `'/^some/path\\.toml$/'`.
#: Only the slash-delimited REGEX form is read, because that is the form this
#: repository uses; a bare glob would not be matched by this and the
#: "every pattern points at a real file" assertion below turns that into a red
#: test rather than a quietly shrunken sweep.
_PATTERN_LITERAL = re.compile(r"'/(?P<body>\^[^']+\$)/'")


def python_trees_with_a_uv_pin() -> list[str]:
    """Every ``pyproject.toml`` in the checkout that declares the uv pin, sorted."""
    found = []
    for pyproject in _REPO_ROOT.rglob("pyproject.toml"):
        relative = pyproject.relative_to(_REPO_ROOT)
        if _EXCLUDED.intersection(relative.parts):
            continue
        table = tomllib.loads(pyproject.read_text()).get("tool", {}).get("uv", {})
        if _PIN_KEY in table:
            found.append(relative.as_posix())
    return sorted(found)


# `strip_comments` and `array_value` used to live here. They moved to
# `tests.support.renovate_config` when #1543's guard needed the same two readers:
# a second copy of a reader whose failure mode is "silently returns nothing" is
# how one copy gets fixed while the other keeps lying. The reasons they are
# written the way they are moved with them.


def _custom_managers_section(text: str) -> str:
    """The ``customManagers:`` array, textually. Raises rather than returning ''."""
    start = text.find("customManagers:")
    assert start != -1, (
        "renovate.json5 has no `customManagers:` key. Either the uv pin is no longer aged by a custom "
        "manager — in which case this guard needs rewriting against whatever reads it now — or the file "
        "moved. Silently reading nothing is the one outcome this must not have."
    )
    return text[start:]


def pin_reading_patterns(text: str) -> list[str]:
    """The ``managerFilePatterns`` regexes of the custom manager(s) reading the pin.

    A block qualifies when one of its ``matchStrings`` PATTERNS names
    :data:`_PIN_KEY` — not when its prose does. The blocks are split on
    ``customType:`` so a second custom manager's file list cannot leak in and
    make an uncovered pin look covered.
    """
    blocks = strip_comments(_custom_managers_section(text)).split("customType:")
    patterns: list[str] = []
    for block in blocks[1:]:
        match_strings = array_value(block, "matchStrings")
        if match_strings is None or _PIN_KEY not in match_strings:
            continue
        file_list = array_value(block, "managerFilePatterns") or ""
        patterns.extend(
            # `\\.` in the JSON5 source is an escaped backslash: the string
            # Renovate receives carries a single one. Reading the raw file means
            # undoing that, or `\\.` would be "backslash then any character".
            literal.group("body").replace("\\\\", "\\")
            for literal in _PATTERN_LITERAL.finditer(file_list)
        )
    return patterns


def uncovered_pins(trees: list[str], patterns: list[str]) -> list[str]:
    """Trees carrying the pin that no pattern matches."""
    compiled = [re.compile(pattern) for pattern in patterns]
    return [tree for tree in trees if not any(regex.search(tree) for regex in compiled)]


class TestTheManagerReadsEveryPin:
    """The property, over the real tree and the real config."""

    def test_every_pinned_pyproject_is_matched_by_a_pattern(self) -> None:
        trees = python_trees_with_a_uv_pin()
        patterns = pin_reading_patterns(_CONFIG.read_text())
        uncovered = uncovered_pins(trees, patterns)

        assert uncovered == [], (
            "These pyproject.toml declare [tool.uv].required-version and the custom manager in "
            f"renovate.json5 does not read them: {uncovered}\n\n"
            "The next `uv toolchain` pull request will move every OTHER pin and leave these behind. That "
            "is not a stale pin — it is a RED required lane: "
            "test_library_lock_hash_verification.py::TestEveryLibraryPinsTheSameUv holds every pin equal to "
            "the backend's, so Renovate's own pull request would fail the gate. Add the path to "
            "`managerFilePatterns` of the custom manager whose matchStrings read `required-version`."
        )

    def test_every_pattern_still_points_at_a_file_that_exists(self) -> None:
        """The other direction: a pattern that stopped matching is invisible too."""
        trees = python_trees_with_a_uv_pin()
        unused = [
            pattern
            for pattern in pin_reading_patterns(_CONFIG.read_text())
            if not any(re.compile(pattern).search(tree) for tree in trees)
        ]

        assert unused == [], (
            f"These `managerFilePatterns` entries match no pyproject.toml carrying the pin: {unused}. "
            "Either the file was moved or renamed and the pattern was left behind, or the pin was removed "
            "from it. Renovate reports neither — an unmatched pattern is silent."
        )

    def test_the_two_shared_libraries_are_covered(self) -> None:
        """The named regression, asserted on its own so the failure names it (#1464)."""
        patterns = pin_reading_patterns(_CONFIG.read_text())
        for library in ("src/libs/kp_vectordb/pyproject.toml", "src/libs/kp_errortracking/pyproject.toml"):
            assert uncovered_pins([library], patterns) == [], library


class TestTheExtractionIsNotVacuous:
    """Every step of reading a JSON5 file textually, asserted instead of trusted."""

    def test_the_sweep_finds_the_pins_the_repository_has(self) -> None:
        trees = python_trees_with_a_uv_pin()
        assert len(trees) >= 7, f"only {trees} carry the pin — has the sweep stopped reading pyproject.toml?"
        assert "src/backend/pyproject.toml" in trees, "the backend pin is the one that has existed since #1383"

    def test_the_pattern_list_is_not_empty(self) -> None:
        patterns = pin_reading_patterns(_CONFIG.read_text())
        assert patterns, (
            "no `managerFilePatterns` regex was extracted from renovate.json5, so the sweep above compared "
            "every pin against nothing and passed. That is a defect in the MEASURING TOOL."
        )
        assert any("src/backend" in pattern for pattern in patterns), (
            f"the extracted patterns {patterns} do not include the backend pyproject, which has been in "
            "that list since #1383 — the extraction is reading the wrong block."
        )

    def test_a_second_custom_manager_does_not_lend_its_file_list(self) -> None:
        """Scoping matters: another manager's paths must not cover a pin."""
        text = _CONFIG.read_text()
        patterns = pin_reading_patterns(text)
        assert not any("renovate-pins" in pattern for pattern in patterns), (
            f"{patterns} includes a path belonging to the `.github/renovate-pins.yaml` manager, so blocks "
            "are being merged and an uncovered pin could look covered."
        )

    def test_the_json5_double_backslash_is_undone(self) -> None:
        """`\\\\.` in the source is one backslash to Renovate; reading it raw must agree."""
        patterns = pin_reading_patterns(_CONFIG.read_text())
        backend = next(pattern for pattern in patterns if "src/backend" in pattern)
        assert backend == r"^src/backend/pyproject\.toml$", backend
        # The escaped dot must be a literal dot, not "any character": otherwise a
        # file named `pyprojectXtoml` would match and a real one might not.
        assert re.compile(backend).search("src/backend/pyproject.toml")
        assert not re.compile(backend).search("src/backend/pyprojectXtoml")


class TestTheSweepCanGoRed:
    """Otherwise the green above certifies nothing (the 2026-08-15 class)."""

    _MINIMAL = """
customManagers: [
  {
    customType: 'regex',
    managerFilePatterns: [
      '/^src/backend/pyproject\\\\.toml$/',
    ],
    matchStrings: [
      'required-version = "==(?<currentValue>[0-9][^"]*)"',
    ],
  },
]
"""

    def test_a_pin_outside_the_pattern_list_is_a_finding(self) -> None:
        patterns = pin_reading_patterns(self._MINIMAL)

        assert uncovered_pins(["src/backend/pyproject.toml", "src/libs/kp_vectordb/pyproject.toml"], patterns) == [
            "src/libs/kp_vectordb/pyproject.toml"
        ]

    def test_a_covered_pin_is_not_a_finding(self) -> None:
        assert uncovered_pins(["src/backend/pyproject.toml"], pin_reading_patterns(self._MINIMAL)) == []

    def test_a_manager_whose_comment_alone_names_the_pin_contributes_nothing(self) -> None:
        """The defect this file had in its first draft, pinned down (#1464 review).

        `.github/workflows/**` is the real pattern that leaked: the workflow-pin
        manager explains in a comment that `[tool.uv].required-version` replaced
        the `uv==` literal it used to match. Prose is not configuration.
        """
        prose = """
customManagers: [
  {
    customType: 'regex',
    managerFilePatterns: [
      '/^\\.github/workflows/[^/]+\\.ya?ml$/',
    ],
    matchStrings: [
      // `uv` was an alternative here until #1383 — required-version replaced it.
      "'(?<depName>pip-audit)==(?<currentValue>[0-9][^']*)'",
    ],
  },
]
"""

        assert pin_reading_patterns(prose) == []

    def test_the_real_config_does_not_lend_the_workflow_pattern(self) -> None:
        """The same thing, over the file that actually configures Renovate."""
        patterns = pin_reading_patterns(_CONFIG.read_text())

        assert not any("workflows" in pattern for pattern in patterns), (
            f"{patterns} includes the workflow pattern of the `run:`-pin manager. Its matchStrings do not "
            "read `required-version`; only a comment there mentions it."
        )

    def test_the_array_reader_does_not_depend_on_key_order(self) -> None:
        """`matchStrings` before `managerFilePatterns` must read the same."""
        reordered = """
customManagers: [
  {
    customType: 'regex',
    matchStrings: [
      'required-version = "==(?<currentValue>[0-9][^"]*)"',
    ],
    managerFilePatterns: [
      '/^src/backend/pyproject\\.toml$/',
    ],
  },
]
"""

        assert pin_reading_patterns(reordered) == [r"^src/backend/pyproject\.toml$"]

    def test_a_manager_that_does_not_read_the_pin_contributes_nothing(self) -> None:
        """The scoping rule, exercised rather than asserted in prose."""
        other = self._MINIMAL.replace(
            'required-version = "==(?<currentValue>[0-9][^"]*)"', "image: (?<currentValue>.+)"
        )

        assert pin_reading_patterns(other) == []

    def test_a_config_without_custom_managers_raises_instead_of_passing(self) -> None:
        """An unreadable config is an undetermined run, never a clean one."""
        with pytest.raises(AssertionError, match="no `customManagers:` key"):
            pin_reading_patterns("{ packageRules: [] }")
