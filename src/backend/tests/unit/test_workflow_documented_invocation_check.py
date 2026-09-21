"""Tests for ``scripts/check_workflow_documented_invocation.py``.

**What is under test.** The detection logic, driven against *constructed*
workflow files in ``tmp_path`` — never against the real ``.github/workflows``.
A test asserting "the tree has 40 checked sites" would go red on the next
legitimate workflow edit and prove nothing about the rule.

**Why the red cases come first.** The check this file covers exists because of
#1607, where two workflow headers documented an invocation (`label a pull
request ``security-scan``') that the configuration did not carry and nobody
could perform. A guard against that class which has never been watched fail is
itself an instance of the class. Each of the three shapes therefore gets a
constructed workflow that MUST make the check go red, plus the near-miss that
must stay green.

Traces to #1607 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_workflow_documented_invocation")


@pytest.fixture
def build_workflows(tmp_path: Path) -> Callable[..., Path]:
    """Write workflow files into a ``workflows/`` directory and return it."""

    def _build(**files: str) -> Path:
        root = tmp_path / "workflows"
        root.mkdir(exist_ok=True)
        for name, content in files.items():
            (root / f"{name}.yml").write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return root

    return _build


def _rules(root: Path) -> list[str]:
    return sorted(finding.rule for finding in checker.collect(root))


# Written flush-left on purpose: the helper runs `textwrap.dedent`, and a header
# comment spliced in at column 0 would otherwise destroy the common indent and
# hand the parser a broken file — a fixture defect that looks like a finding.
DISPATCH_WITH_INPUT = """\
name: Scan
on:
  workflow_dispatch:
    inputs:
      pull_request:
        required: false
        type: string
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ inputs.pull_request }}"
"""


class TestItCanFail:
    """Each shape, constructed broken, and the check going red on it."""

    def test_an_undeclared_input_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """GitHub renders it empty rather than erroring — accepted, ignored."""
        root = build_workflows(
            scan="""
            name: Scan
            on:
              workflow_dispatch:
            jobs:
              scan:
                runs-on: ubuntu-latest
                steps:
                  - run: echo "${{ inputs.pull_request }}"
            """
        )
        assert _rules(root) == ["undeclared-input"]

    def test_a_declared_input_nothing_reads_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """The Run-workflow dialog is prose too: it invites a value and drops it."""
        root = build_workflows(
            scan="""
            name: Scan
            on:
              workflow_dispatch:
                inputs:
                  pull_request:
                    required: false
                    type: string
            jobs:
              scan:
                runs-on: ubuntu-latest
                steps:
                  - run: echo hello
            """
        )
        assert _rules(root) == ["unread-input"]

    def test_a_documented_invocation_naming_a_missing_workflow_is_caught(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """#1607 exactly: the header names a path that does not exist."""
        root = build_workflows(
            scan="""
            # Run it with:
            #     gh workflow run nowhere.yml --ref develop
            name: Scan
            on: [push]
            jobs:
              scan:
                runs-on: ubuntu-latest
                steps:
                  - run: echo hello
            """
        )
        assert _rules(root) == ["documented-invocation"]

    def test_a_documented_invocation_of_a_non_dispatchable_workflow_is_caught(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """The file exists; `gh workflow run` against it still fails."""
        root = build_workflows(
            caller="""
            #     gh workflow run target.yml --ref develop
            name: Caller
            on: [push]
            jobs:
              a:
                runs-on: ubuntu-latest
                steps:
                  - run: echo hello
            """,
            target="""
            name: Target
            on: [push]
            jobs:
              b:
                runs-on: ubuntu-latest
                steps:
                  - run: echo hello
            """,
        )
        assert _rules(root) == ["documented-invocation"]

    def test_a_documented_field_the_target_does_not_declare_is_caught(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """The instruction passes `-f` for an input that does not exist."""
        root = build_workflows(
            scan=DISPATCH_WITH_INPUT.replace(
                "name: Scan",
                "#     gh workflow run scan.yml --ref develop -f pr_number=<number>\nname: Scan",
                1,
            )
        )
        assert _rules(root) == ["documented-invocation"]

    def test_a_backslash_continued_example_is_read_as_one_instruction(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """The real headers wrap the example; a line-at-a-time reader misses the `-f`."""
        root = build_workflows(
            scan=DISPATCH_WITH_INPUT.replace(
                "name: Scan",
                "#     gh workflow run scan.yml --ref develop \\\n#       -f pr_number=<number>\nname: Scan",
                1,
            )
        )
        assert _rules(root) == ["documented-invocation"]

    def test_the_broken_workflow_makes_the_process_exit_non_zero(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        root = build_workflows(
            scan="""
            name: Scan
            on:
              workflow_dispatch:
            jobs:
              scan:
                runs-on: ubuntu-latest
                steps:
                  - run: echo "${{ inputs.pull_request }}"
            """
        )
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_FINDINGS
        assert "undeclared-input" in capsys.readouterr().err


class TestItStaysGreen:
    """The near-misses. A guard that fires on correct configuration is noise."""

    def test_a_wired_dispatch_input_passes(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(scan=DISPATCH_WITH_INPUT)
        assert _rules(root) == []

    def test_a_correct_documented_invocation_passes(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            scan=DISPATCH_WITH_INPUT.replace(
                "name: Scan",
                "#     gh workflow run scan.yml --ref develop \\\n#       -f pull_request=<number>\nname: Scan",
                1,
            )
        )
        assert _rules(root) == []

    def test_a_bare_inputs_word_in_shell_text_is_not_an_expression(self, build_workflows: Callable[..., Path]) -> None:
        """`inputs.pull_request` only counts inside `${{ }}` — prose is not wiring."""
        root = build_workflows(
            scan="""
            name: Scan
            on: [push]
            jobs:
              scan:
                runs-on: ubuntu-latest
                steps:
                  - run: echo "see inputs.pull_request in the docs"
            """
        )
        assert _rules(root) == []

    def test_a_workflow_call_input_counts_as_declared(self, build_workflows: Callable[..., Path]) -> None:
        """A reusable workflow declares its inputs under `workflow_call`."""
        root = build_workflows(
            reusable="""
            name: Reusable
            on:
              workflow_call:
                inputs:
                  node:
                    required: true
                    type: string
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - run: echo "${{ inputs.node }}"
            """
        )
        assert _rules(root) == []


class TestTheGuardIsNotVacuous:
    """It has to be looking at something, or green means nothing (NFR-018 §2)."""

    def test_the_survey_names_every_checked_site(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(scan=DISPATCH_WITH_INPUT)
        sites = checker.survey(root)
        assert any("declared input `pull_request`" in site for site in sites)
        assert any("reads `inputs.pull_request`" in site for site in sites)
