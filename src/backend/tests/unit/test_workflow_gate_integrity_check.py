"""Tests for the NFR-018 workflow linter (``scripts/check_workflow_gate_integrity.py``).

**What is under test.** The detection logic, driven against *constructed*
workflow files written into ``tmp_path`` — never against the real
``.github/workflows``. A test asserting "the tree has 19 justified sites" would
go red on the next legitimate workflow edit and teach nobody anything.

**The deliberately-broken workflow.** :class:`TestItCanFail` writes each of the
three shapes and asserts the check goes red and names it. A gate nobody has
watched fail is a gate nobody knows works — which is the entire subject of
NFR-018, and this is the gate the spec says in §8 it does not have.

**The third shape is the subtle one.** A job under ``always()`` that reads
``needs.<x>.outputs`` without ``needs.<x>.result`` reports **Success** when its
dependency failed, because every output is then empty, every step is skipped, and
a job of skipped steps is green. :class:`TestNeedsOutputs` pins both halves: the
override makes it a finding, the plain dependency does not (GitHub's own skip
semantics already protect that shape, and flagging it would put a marker on
every ``needs:`` in the repository).

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded by path. It is not a
backend test in subject; it is one in placement, because this is the tier that
runs.

Traces to the 2026-08-08 issue-pattern audit, measure P5.4 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_workflow_gate_integrity")


@pytest.fixture
def build_workflows(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing workflow files into a ``workflows/`` directory."""

    def _build(**files: str) -> Path:
        root = tmp_path / "workflows"
        root.mkdir(exist_ok=True)
        for name, content in files.items():
            (root / f"{name}.yml").write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return root

    return _build


def _kinds(root: Path) -> list[str]:
    """The kind of every *counted* finding, sorted."""
    return sorted(finding.kind for finding in checker.collect(root) if not finding.justified)


class TestItCanFail:
    """The three deliberately-broken shapes, and the check going red on them."""

    def test_a_swallowed_exit_code_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """`skaffold render … || true` discarded a real failure for months."""
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ./scripts/verify.sh || true
            """
        )
        assert _kinds(root) == ["swallowed_exit"]

    def test_continue_on_error_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """A step that cannot turn its check red is not measuring anything."""
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - name: Verify
                    continue-on-error: true
                    run: ./scripts/verify.sh
            """
        )
        assert _kinds(root) == ["continue_on_error"]

    def test_the_broken_workflow_makes_the_process_exit_non_zero(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ./scripts/verify.sh || true
            """
        )
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "NFR-018" in out
        assert checker.JUSTIFICATION_MARKER in out

    def test_a_clean_workflow_is_green(self, build_workflows: Callable[..., Path]) -> None:
        """The fix the message asks for actually clears the check."""
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ./scripts/verify.sh
            """
        )
        assert _kinds(root) == []
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_OK


class TestPrecisionGuards:
    """What the check refuses to report, so it does not get switched off."""

    def test_a_comment_mentioning_the_pattern_is_not_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """``skaffold-verify.yml`` explains in its header that it REMOVED `|| true`.

        A checker that read its own subject matter out of prose would report the
        two places this repository documents the fix — and be switched off by
        the first person who read the report.
        """
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            # Removing `|| true` revealed that this step had never worked.
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  # `|| true` used to hide the failure here.
                  - run: ./scripts/verify.sh
            """
        )
        assert _kinds(root) == []

    def test_continue_on_error_false_is_not_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """Writing the default out loud is the opposite of the defect."""
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - continue-on-error: false
                    run: ./scripts/verify.sh
            """
        )
        assert _kinds(root) == []


class TestNeedsOutputs:
    """The false green a failed dependency produces — and when it cannot happen."""

    _FILTER_JOB = """
    name: CI
    on: [pull_request]
    jobs:
      changes:
        runs-on: ubuntu-latest
        outputs:
          frontend: ${{ steps.filter.outputs.frontend }}
        steps:
          - id: filter
            run: echo frontend=true >> "$GITHUB_OUTPUT"
      build:
        needs: changes
        %s
        runs-on: ubuntu-latest
        steps:
          - run: npm run build
    """

    def test_always_plus_outputs_without_result_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """The frontend.yml trap: `changes` fails, every step skips, job is green."""
        root = build_workflows(ci=self._FILTER_JOB % "if: always() && needs.changes.outputs.frontend == 'true'")
        assert _kinds(root) == ["unguarded_needs_output"]

    def test_naming_the_result_clears_it(self, build_workflows: Callable[..., Path]) -> None:
        """The guard `coverage` in frontend.yml already carried."""
        root = build_workflows(
            ci=self._FILTER_JOB
            % ("if: always() && (needs.changes.result != 'success' || needs.changes.outputs.frontend == 'true')")
        )
        assert _kinds(root) == []

    def test_the_wildcard_result_form_clears_it(self, build_workflows: Callable[..., Path]) -> None:
        """`!contains(needs.*.result, 'failure')` — what docker-publish's publishers use."""
        root = build_workflows(
            ci=self._FILTER_JOB
            % ("if: always() && !contains(needs.*.result, 'failure') && needs.changes.outputs.frontend == 'true'")
        )
        assert _kinds(root) == []

    def test_without_an_override_the_shape_is_safe(self, build_workflows: Callable[..., Path]) -> None:
        """GitHub skips a dependent job when its dependency fails.

        Reporting this shape would put a marker on nearly every `needs:` in the
        repository while naming no defect — the exact reach/precision trade the
        script's docstring refuses.
        """
        root = build_workflows(ci=self._FILTER_JOB % "if: needs.changes.outputs.frontend == 'true'")
        assert _kinds(root) == []

    def test_the_finding_names_the_job_and_the_dependency(self, build_workflows: Callable[..., Path]) -> None:
        """The message has to point at the job, not merely at a file."""
        root = build_workflows(ci=self._FILTER_JOB % "if: always() && needs.changes.outputs.frontend == 'true'")
        finding = checker.collect(root)[0]
        assert "build" in finding.detail
        assert "needs.changes.outputs" in finding.detail
        assert finding.line > 1


class TestJustification:
    """The per-site escape hatch, and why a bare marker is not one."""

    def _with_reason(self, reason: str) -> str:
        return f"""
        name: Gate
        on: [push]
        jobs:
          check:
            runs-on: ubuntu-latest
            steps:
              - run: |
                  hits=$(grep -c foo bar || true)  {reason}
        """

    def test_a_reason_on_the_line_exempts_it(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(gate=self._with_reason("# gate-integrity-ok: grep -c exits 1 on a zero count"))
        assert _kinds(root) == []

    def test_a_reason_in_the_comment_block_above_exempts_it(self, build_workflows: Callable[..., Path]) -> None:
        """This repository explains its jobs in a paragraph, not on one line."""
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              # The job below is a reporter, not a measurement.
              # gate-integrity-ok: the suite's verdict is the step before this one
              check:
                if: always() && needs.changes.outputs.frontend == 'true'
                needs: changes
                runs-on: ubuntu-latest
                steps:
                  - run: echo hi
              changes:
                runs-on: ubuntu-latest
                outputs:
                  frontend: ${{ steps.f.outputs.frontend }}
                steps:
                  - id: f
                    run: echo frontend=true >> "$GITHUB_OUTPUT"
            """
        )
        assert _kinds(root) == []

    def test_a_bare_marker_is_not_an_exemption(self, build_workflows: Callable[..., Path]) -> None:
        """The point of the hatch is the reason, not the token."""
        root = build_workflows(gate=self._with_reason("# gate-integrity-ok:"))
        assert _kinds(root) == ["swallowed_exit"]

    def test_a_too_short_reason_is_not_an_exemption(self, build_workflows: Callable[..., Path]) -> None:
        """``# gate-integrity-ok: ok`` explains nothing a reviewer can argue with."""
        root = build_workflows(gate=self._with_reason("# gate-integrity-ok: ok"))
        assert _kinds(root) == ["swallowed_exit"]

    def test_the_report_names_every_justified_site(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An exemption stays visible; a silent one is indistinguishable from a fix."""
        root = build_workflows(gate=self._with_reason("# gate-integrity-ok: grep -c exits 1 on a zero count"))
        assert checker.main(["--scan-root", str(root), "--list"]) == checker.EXIT_OK
        assert "grep -c exits 1 on a zero count" in capsys.readouterr().out


class TestProcessContract:
    """Exit codes and the machine-readable output."""

    def test_json_reports_both_buckets(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = build_workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ./a.sh || true
                  - name: Report
                    # gate-integrity-ok: a reporter, the verdict is the step above
                    continue-on-error: true
                    run: ./report.sh
            """
        )
        assert checker.main(["--scan-root", str(root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert [entry["kind"] for entry in payload["unjustified"]] == ["swallowed_exit"]
        assert [entry["kind"] for entry in payload["justified"]] == ["continue_on_error"]

    def test_a_missing_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check that cannot run must not report success — the #814 failure mode."""
        assert checker.main(["--scan-root", str(tmp_path / "nowhere")]) == checker.EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err

    def test_an_empty_directory_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scanning nothing and reporting clean is the shape this whole file is about.

        A path typo, a renamed directory, a checkout that failed — every one of
        them ends here, and every one of them must be loud.
        """
        empty = tmp_path / "empty"
        empty.mkdir()
        assert checker.main(["--scan-root", str(empty)]) == checker.EXIT_USAGE
        assert "no workflow files" in capsys.readouterr().err

    def test_unparseable_yaml_is_a_usage_error_not_a_pass(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = build_workflows(broken="jobs:\n  - [unclosed\n")
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_USAGE
        assert "cannot parse" in capsys.readouterr().err


class TestTheRealTree:
    """What the pre-commit hook asserts, asserted here too."""

    def test_every_swallowed_verdict_in_the_workflows_carries_a_reason(self) -> None:
        assert checker.main([]) == checker.EXIT_OK
