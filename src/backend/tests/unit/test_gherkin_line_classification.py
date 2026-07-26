"""Regression tests for the shared Gherkin line classifier (``tests/e2e/_gherkin.py``).

**The defect being locked down.** ``tests/e2e/conftest.py::_collect_feature_tags``
used to match every source line of a ``.feature`` against a tag regex with no
docstring awareness. A Gherkin docstring line consisting solely of ``@token``
items — ordinary prose such as ``@example`` — was therefore read as a tag,
rejected by the conftest typo guard and raised as ``pytest.UsageError`` from
``pytest_configure``. That is not one failing test but a **collection abort**:
exit 2, with all ~720 E2E tests never running. A one-line prose change in a
``.feature`` could take the whole suite down.

**Why the tests live here and not under ``tests/e2e/``.** ``tests/e2e/`` runs
only through ``scripts/run-e2e.sh`` (Docker plus the full stack), so a test
placed there would never execute in the ordinary gate. ``pytest tests/unit/``
from ``src/backend`` is a PR-gating CI check, so the regression is nailed down
where it is actually run. The price is that ``tests/e2e/_gherkin.py`` sits
outside the backend package and has to be loaded **by path**, which is what
``scripts/check_bdd_traceability.py::_load_module_by_path`` already does.

**What is exercised, and what stands in for what.** ``_collect_feature_tags``
itself cannot be imported here: ``tests/e2e/conftest.py`` imports Selenium at
module scope, and adding Selenium to the backend unit suite would violate the
tier's no-outside-world rule for the sake of a three-line wrapper. The tests
below therefore drive ``iter_tags`` / ``iter_lines`` — the path
``_collect_feature_tags`` now delegates to **entirely**: its whole body is a
``glob`` over ``features/**/*.feature`` plus ``iter_tags(file.read_text())``, so
every tag-versus-non-tag decision is made in the module under test here.
:class:`TestSharedClassifierBoundary` guards that delegation so the substitution
cannot quietly stop being true.

The traceability check's own feature parsing
(``scripts/check_bdd_traceability.py::parse_feature_file``) is covered directly:
that script is standard-library only and loadable by the same path mechanism.

**Known dead branch, deliberately uncovered.** ``GherkinLine.tags`` filters
tokens with ``len(token) > 1``, which is unreachable through ``iter_lines``:
``TAG_LINE``'s ``@\\S+`` never classifies a bare ``@`` line as a tag in the first
place. It is defensive code inherited from the original parser; chasing coverage
on it would mean constructing a ``GherkinLine`` by hand and asserting an
implementation detail.

Traces to issue #771 (no TC-ID: the E2E test harness is not a requirement).
"""

from __future__ import annotations

import importlib.util
import re
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest

# ── Loading the modules under test by path ───────────────────────────────────


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index silently breaks
    the moment the test file moves, which has bitten this repository before.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``tests/e2e``, or None.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "tests" / "e2e").is_dir():
            return candidate
    return None


def _load_module_by_path(module_name: str, path: Path) -> ModuleType:
    """Execute the module at *path* under *module_name* and return it.

    Mirrors ``scripts/check_bdd_traceability.py::_load_module_by_path``. The
    registration in ``sys.modules`` must happen **before** ``exec_module``:
    ``_gherkin`` uses ``@dataclass(frozen=True, slots=True)``, and ``slots=True``
    rebuilds the class and resolves ``sys.modules[cls.__module__]`` while the
    module body is still running.

    Args:
        module_name: Private name to register under; must not collide with the
            name the module carries when the E2E suite imports it normally.
        path: The ``.py`` file to execute.

    Returns:
        The executed module.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip(
        "checkout root not found (no ancestor holds both Taskfile.yaml and tests/e2e); "
        "tests/e2e/_gherkin.py is unreachable from here",
        allow_module_level=True,
    )

_GHERKIN_PATH = _REPO_ROOT / "tests" / "e2e" / "_gherkin.py"
_TRACEABILITY_PATH = _REPO_ROOT / "scripts" / "check_bdd_traceability.py"
_E2E_CONFTEST_PATH = _REPO_ROOT / "tests" / "e2e" / "conftest.py"

for _required in (_GHERKIN_PATH, _TRACEABILITY_PATH, _E2E_CONFTEST_PATH):
    if not _required.is_file():  # pragma: no cover — only in a partial checkout
        pytest.skip(f"{_required} does not exist in this checkout", allow_module_level=True)

gherkin = _load_module_by_path("_kamerplanter_gherkin_under_test", _GHERKIN_PATH)
traceability = _load_module_by_path("_kamerplanter_bdd_traceability_under_test", _TRACEABILITY_PATH)

_TC_PATTERN = traceability.load_tc_id_pattern()

# ── Feature-source helpers ───────────────────────────────────────────────────


def _feature(source: str) -> str:
    """Return an inline ``.feature`` source, dedented and without its leading blank line."""
    return textwrap.dedent(source).lstrip("\n")


def _write_feature(tmp_path: Path, source: str, name: str = "sample.feature") -> Path:
    """Write an inline ``.feature`` source into *tmp_path* and return its path."""
    feature_file = tmp_path / name
    feature_file.write_text(_feature(source), encoding="utf-8")
    return feature_file


def _tag_names(source: str) -> list[str]:
    """Return every tag name ``iter_tags`` reports, in source order."""
    return [name for _lineno, name in gherkin.iter_tags(source)]


def _kind_of(source: str, line_number: int) -> object:
    """Return the classification of the 1-based *line_number* of *source*."""
    return next(line.kind for line in gherkin.iter_lines(source) if line.number == line_number)


def _line_number_of(source: str, needle: str) -> int:
    """Return the 1-based number of the first line whose stripped text starts with *needle*."""
    for number, raw in enumerate(source.splitlines(), start=1):
        if raw.strip().startswith(needle):
            return number
    raise AssertionError(f"no line starting with {needle!r} in the feature source")


class TestDocstringPayloadIsNotATag:
    """The regression itself: nothing inside a Gherkin docstring is a tag."""

    def test_tag_only_docstring_line_is_not_reported_as_a_tag(self, tmp_path: Path) -> None:
        feature_file = _write_feature(
            tmp_path,
            '''
            Feature: Watering log

              @req004 @TC-004-092
              Scenario: A logged watering shows up in every view
                Given the plant detail page is open
                When the grower logs a watering
                Then the rendered template is
                  """
                  @example
                  """
            ''',
        )

        names = _tag_names(feature_file.read_text(encoding="utf-8"))

        assert "example" not in names
        assert names == ["req004", "TC-004-092"]

    def test_tag_block_inside_a_docstring_is_not_reported_as_tags(self, tmp_path: Path) -> None:
        feature_file = _write_feature(
            tmp_path,
            '''
            Feature: Watering log

              @TC-004-092
              Scenario: The docstring documents the tag syntax
                Then the help text is
                  """
                  @smoke @req004 @watering
                  """
            ''',
        )

        names = _tag_names(feature_file.read_text(encoding="utf-8"))

        assert names == ["TC-004-092"]

    def test_docstring_payload_is_classified_as_docstring_not_as_content(self) -> None:
        source = _feature(
            '''
            Feature: Watering log
              Scenario: The payload is opaque
                Then the response body is
                  """
                  # not a comment
                  Scenario: not a keyword
                  @not-a-tag
                  """
            '''
        )

        kinds = {line.number: line.kind for line in gherkin.iter_lines(source) if line.number >= 5}

        assert set(kinds.values()) == {gherkin.GherkinLineKind.DOCSTRING}


class TestRealTagLinesAreReported:
    """The counter-direction: genuine tag lines must survive the docstring state."""

    def test_tags_at_every_gherkin_level_are_reported(self) -> None:
        source = _feature(
            """
            @req004
            Feature: Fertiliser dosing

              @watering
              Rule: The net EC excludes the base water

                @smoke @TC-004-092
                Scenario Outline: The net EC is the target minus the base water
                  Given a base water EC of <base>
                  Then the net EC is <net>

                  @TC-004-101
                  Examples: metric
                    | base | net |
                    | 0.4  | 1.1 |
            """
        )

        names = _tag_names(source)

        assert names == ["req004", "watering", "smoke", "TC-004-092", "TC-004-101"]

    def test_several_tags_on_one_line_are_all_reported_in_order(self) -> None:
        source = _feature(
            """
            @req004 @watering @TC-004-092
            Feature: Watering log
            """
        )

        assert _tag_names(source) == ["req004", "watering", "TC-004-092"]

    @pytest.mark.parametrize(
        ("tag_line", "case"),
        [
            ("@smoke", "no surrounding whitespace"),
            ("  @smoke", "leading spaces"),
            ("\t@smoke", "leading tab"),
            ("@smoke  ", "trailing spaces"),
            ("   @smoke\t", "leading spaces and a trailing tab"),
            ("  @smoke \t @req004  ", "whitespace around two tags"),
        ],
    )
    def test_whitespace_around_a_tag_line_does_not_hide_the_tag(self, tag_line: str, case: str) -> None:
        source = f"Feature: Watering log\n{tag_line}\nScenario: A watering is logged\n"

        assert "smoke" in _tag_names(source), case

    def test_an_at_sign_inside_step_text_is_not_reported_as_a_tag(self) -> None:
        source = _feature(
            """
            Feature: Watering log
              Scenario: A grower signs in
                Given the user @admin signs in
            """
        )

        assert _tag_names(source) == []

    def test_the_tag_line_number_is_reported_for_diagnostics(self) -> None:
        source = _feature(
            """
            Feature: Watering log

              @TC-004-092
              Scenario: A watering is logged
            """
        )

        assert list(gherkin.iter_tags(source)) == [(3, "TC-004-092")]


class TestUnknownTagsStillSurface:
    """The typo guard must keep its input: an unknown tag outside a docstring is a tag."""

    def test_a_misspelled_tag_outside_a_docstring_is_still_reported(self, tmp_path: Path) -> None:
        feature_file = _write_feature(
            tmp_path,
            """
            Feature: Watering log

              @smoek
              Scenario: A watering is logged
            """,
        )

        reported = list(gherkin.iter_tags(feature_file.read_text(encoding="utf-8")))

        assert reported == [(3, "smoek")]

    def test_an_unknown_tag_after_a_closed_docstring_is_still_reported(self) -> None:
        source = _feature(
            '''
            Feature: Watering log

              Scenario: The docstring is closed again
                Then the payload is
                  """
                  @example
                  """

              @smoek
              Scenario: A watering is logged
            '''
        )

        assert _tag_names(source) == ["smoek"]


class TestDocstringDelimiters:
    """Both fences, their asymmetry, the closing line, and the unterminated case."""

    def test_a_triple_quote_docstring_is_not_closed_by_a_backtick_fence(self) -> None:
        source = _feature(
            '''
            Feature: Watering log
              Scenario: The payload embeds a code fence
                Then the response body is
                  """
                  ```
                  @example
                  ```
                  """
            '''
        )

        assert _tag_names(source) == []

    def test_a_backtick_docstring_is_not_closed_by_a_triple_quote_fence(self) -> None:
        source = _feature(
            '''
            Feature: Watering log
              Scenario: The payload embeds a Python docstring
                Then the response body is
                  ```
                  """
                  @example
                  """
                  ```
            '''
        )

        assert _tag_names(source) == []

    @pytest.mark.parametrize("fence", ['"""', "```"])
    def test_the_closing_fence_line_itself_counts_as_docstring(self, fence: str) -> None:
        source = _feature(
            f"""
            Feature: Watering log
              Scenario: The payload is opaque
                Then the response body is
                  {fence}
                  irrelevant
                  {fence}
                And the watering is stored
            """
        )
        closing_line = _line_number_of(source, "irrelevant") + 1

        assert _kind_of(source, closing_line) is gherkin.GherkinLineKind.DOCSTRING
        assert _kind_of(source, closing_line + 1) is gherkin.GherkinLineKind.CONTENT

    @pytest.mark.parametrize("fence", ['"""', "```"])
    def test_a_docstring_left_open_at_end_of_file_yields_no_tags_and_no_error(self, fence: str) -> None:
        source = _feature(
            f"""
            Feature: Watering log

              @TC-004-092
              Scenario: The author forgot the closing fence
                Then the response body is
                  {fence}
                  @example
            """
        )

        assert _tag_names(source) == ["TC-004-092"]

    @pytest.mark.parametrize("fence", ['"""', "```"])
    def test_every_line_after_an_unterminated_fence_is_docstring(self, fence: str) -> None:
        source = _feature(
            f"""
            Feature: Watering log
              Scenario: The author forgot the closing fence
                Then the response body is
                  {fence}
                  Scenario: still payload
                  @example
            """
        )
        opening_line = _line_number_of(source, fence)

        trailing = [line for line in gherkin.iter_lines(source) if line.number >= opening_line]

        assert [line.kind for line in trailing] == [gherkin.GherkinLineKind.DOCSTRING] * 3

    def test_an_empty_feature_file_classifies_to_nothing(self) -> None:
        assert list(gherkin.iter_lines("")) == []
        assert _tag_names("") == []


class TestTraceabilityFeatureParsing:
    """``check_bdd_traceability.py::parse_feature_file`` on the same edge cases.

    The script is standard-library only and loadable by path, so the two
    findings it produces — orphan tag and untagged scenario — are exercised
    end-to-end on a ``tmp_path`` feature instead of only at the classifier level.
    """

    def test_a_tc_tag_inside_a_docstring_does_not_become_an_orphan_finding(self, tmp_path: Path) -> None:
        feature_file = _write_feature(
            tmp_path,
            '''
            Feature: Watering log

              @TC-004-092
              Scenario: A logged watering shows up in every view
                Then the response body is
                  """
                  Superseded, this case used to be @TC-004-999
                  @TC-004-998
                  Scenario: the payload documents a scenario
                  """
            ''',
        )

        scenarios = traceability.parse_feature_file(feature_file, _TC_PATTERN)

        assert len(scenarios) == 1
        assert scenarios[0].tc_ids == ("TC-004-092",)
        assert scenarios[0].tags == ("TC-004-092",)

    def test_examples_tags_are_attributed_to_the_enclosing_scenario_outline(self, tmp_path: Path) -> None:
        source = """
            @req004
            Feature: Fertiliser dosing

              @TC-004-092
              Scenario Outline: The net EC is the target minus the base water
                Given a base water EC of <base>
                Then the net EC is <net>

                @TC-004-101
                Examples: metric
                  | base | net |
                  | 0.4  | 1.1 |
            """
        feature_file = _write_feature(tmp_path, source)
        outline_line = _line_number_of(_feature(source), "Scenario Outline:")

        scenarios = traceability.parse_feature_file(feature_file, _TC_PATTERN)

        assert len(scenarios) == 1
        assert scenarios[0].line == outline_line
        assert scenarios[0].tc_ids == ("TC-004-092", "TC-004-101")

    def test_an_unterminated_docstring_does_not_break_the_traceability_parse(self, tmp_path: Path) -> None:
        feature_file = _write_feature(
            tmp_path,
            '''
            Feature: Watering log

              @TC-004-092
              Scenario: The author forgot the closing fence
                Then the response body is
                  """
                  @TC-004-999
                  Scenario: still payload
            ''',
        )

        scenarios = traceability.parse_feature_file(feature_file, _TC_PATTERN)

        assert [scenario.tc_ids for scenario in scenarios] == [("TC-004-092",)]

    def test_a_scenario_without_any_tag_reports_no_tc_id(self, tmp_path: Path) -> None:
        feature_file = _write_feature(
            tmp_path,
            """
            Feature: Watering log

              Scenario: Nobody declared a test case for this
                Then the watering is stored
            """,
        )

        scenarios = traceability.parse_feature_file(feature_file, _TC_PATTERN)

        assert [scenario.tc_ids for scenario in scenarios] == [()]


class TestSharedClassifierBoundary:
    """The two properties that let this module stand in for the E2E collection path."""

    def test_the_classifier_pulls_in_no_selenium_dependency(self) -> None:
        selenium_modules = [name for name in sys.modules if name.split(".")[0] == "selenium"]

        assert selenium_modules == []

    def test_the_e2e_conftest_delegates_tag_collection_to_the_shared_classifier(self) -> None:
        """Guard the substitution this module relies on.

        ``_collect_feature_tags`` cannot be exercised here without importing
        Selenium, so its equivalence with ``iter_tags`` is asserted at the source
        level: the conftest must import ``iter_tags`` and must not carry a
        second, docstring-blind tag regex of its own. Without this guard the
        tests above could keep passing while the conftest quietly grew a private
        parser again — which is exactly how the defect arose.
        """
        source = _E2E_CONFTEST_PATH.read_text(encoding="utf-8")

        assert re.search(r"^from \._gherkin import [^\n]*\biter_tags\b", source, re.MULTILINE)
        assert r"@\S+" not in source
