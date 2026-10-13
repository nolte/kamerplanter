"""Tests for ``scripts/check_untrusted_checkout_permissions.py``.

**What is under test.** The detection logic, driven against *constructed*
workflow files in ``tmp_path`` — never against the real ``.github/workflows``.
An assertion about the live tree ("29 sites") would go red on the next
legitimate workflow edit and would prove nothing about the rule.

**Why the red cases come first, and why there is one per spelling.** The check
exists because of #1614, where two security workflows checked out
``refs/pull/<n>/merge`` in a job holding ``issues: write``. The dangerous part
of that finding was never the two files — it was that the same construction
can be written four other ways, and a sweep that matches only the literal
spelling reports a clean tree while three of them stand. Each spelling
therefore gets a constructed workflow that MUST make the check go red:

* the permission inherited from the workflow level rather than declared on the job;
* the ``ref:`` built from an expression rather than written as a literal;
* the composite action that checks out on the job's behalf;
* the ``pull_request_target`` trigger, where the checkout needs no ``ref:`` at all;
* the ``run:`` block that fetches the pull request itself;
* no ``permissions:`` block anywhere, so the repository default decides.

And the near-misses that must stay green, including the one that matters most
for #1456: a *comment* may neither raise a finding nor satisfy one.

Traces to #1614 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_untrusted_checkout_permissions")

WRITE_RULE = "untrusted-checkout-write-permission"
CREDENTIAL_RULE = "untrusted-checkout-persists-credentials"


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


def _messages(root: Path) -> str:
    return "\n".join(finding.message for finding in checker.collect(root))


class TestItCanFail:
    """Each spelling of the class, constructed, and the check going red on it."""

    def test_the_literal_shape_from_the_issue(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            scan="""
            name: Scan
            on:
              push:
                branches: [develop]
              workflow_dispatch:
                inputs:
                  pull_request:
                    type: string
            permissions:
              contents: read
            jobs:
              scan:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  issues: write
                steps:
                  - uses: actions/checkout@v7
                    with:
                      ref: refs/pull/7/merge
            """
        )
        assert _rules(root) == [CREDENTIAL_RULE, WRITE_RULE]

    def test_a_permission_inherited_from_the_workflow_level(self, build_workflows: Callable[..., Path]) -> None:
        """The job declares no `permissions:` — the write comes from above it."""
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request:
            permissions:
              contents: read
              checks: write
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v7
            """
        )
        assert _rules(root) == [WRITE_RULE]
        assert "`checks: write`" in _messages(root)

    def test_a_ref_built_from_an_expression(self, build_workflows: Callable[..., Path]) -> None:
        """`format(...)` renders the marker; a literal-only matcher misses it."""
        root = build_workflows(
            scan="""
            name: Scan
            on:
              workflow_dispatch:
                inputs:
                  pull_request:
                    type: string
            jobs:
              scan:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  issues: write
                steps:
                  - uses: actions/checkout@v7
                    with:
                      ref: ${{ github.event.inputs.pull_request && format('refs/pull/{0}/merge', github.event.inputs.pull_request) || '' }}
                      persist-credentials: false
            """  # noqa: E501
        )
        assert _rules(root) == [WRITE_RULE]

    def test_a_composite_action_that_checks_out_on_the_jobs_behalf(
        self, build_workflows: Callable[..., Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        action_dir = tmp_path / ".github" / "actions" / "prepare"
        action_dir.mkdir(parents=True)
        (action_dir / "action.yml").write_text(
            textwrap.dedent(
                """
                name: Prepare
                runs:
                  using: composite
                  steps:
                    - uses: actions/checkout@v7
                """
            ).lstrip(),
            encoding="utf-8",
        )
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request:
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  packages: write
                steps:
                  - uses: ./.github/actions/prepare
            """
        )
        assert _rules(root) == [WRITE_RULE]

    def test_pull_request_target_needs_no_ref_at_all(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request_target:
                types: [opened]
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  pull-requests: write
                steps:
                  - uses: actions/checkout@v7
            """
        )
        assert _rules(root) == [WRITE_RULE]

    def test_a_run_block_that_fetches_the_pull_request(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            lane="""
            name: Lane
            on:
              workflow_dispatch:
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  issues: write
                steps:
                  - run: gh pr checkout "$PR"
            """
        )
        assert _rules(root) == [WRITE_RULE]

    def test_no_permissions_block_anywhere(self, build_workflows: Callable[..., Path]) -> None:
        """The repository default decides, and this tree cannot see what it is."""
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request:
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v7
            """
        )
        assert _rules(root) == [WRITE_RULE]
        assert "repository's default token scope" in _messages(root)

    def test_write_all_is_a_write_scope(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request:
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions: write-all
                steps:
                  - uses: actions/checkout@v7
            """
        )
        assert _rules(root) == [WRITE_RULE]


class TestItStaysGreenOnTheNearMisses:
    """Constructions that resemble the class without being it."""

    def test_a_trusted_checkout_may_hold_a_write_scope(self, build_workflows: Callable[..., Path]) -> None:
        """A push-only lane checks out the code that was already merged."""
        root = build_workflows(
            publish="""
            name: Publish
            on:
              push:
                branches: [develop]
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  packages: write
                steps:
                  - uses: actions/checkout@v7
            """
        )
        assert _rules(root) == []

    def test_the_repaired_shape(self, build_workflows: Callable[..., Path]) -> None:
        """Explicit pull-request ref, credential dropped, write moved out."""
        root = build_workflows(
            scan="""
            name: Scan
            on:
              push:
                branches: [develop]
              workflow_dispatch:
                inputs:
                  pull_request:
                    type: string
            permissions:
              contents: read
            jobs:
              scan:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                outputs:
                  label: ${{ steps.target.outputs.label }}
                steps:
                  - uses: actions/checkout@v7
                    with:
                      ref: ${{ github.event.inputs.pull_request && format('refs/pull/{0}/merge', github.event.inputs.pull_request) || '' }}
                      persist-credentials: false
              report:
                needs: scan
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  issues: write
                steps:
                  - uses: actions/download-artifact@v8
            """  # noqa: E501
        )
        assert _rules(root) == []

    def test_a_shell_comment_does_not_raise_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """#1456, the false-positive direction.

        This job has no checkout at all. Its only mention of ``gh pr checkout``
        is a shell COMMENT — and the job holds ``issues: write``, so reading
        the ``run:`` block as raw text would make it a site and raise a
        finding about a tree that never exists.
        """
        root = build_workflows(
            lane="""
            name: Lane
            on:
              workflow_dispatch:
            jobs:
              note:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  issues: write
                steps:
                  - run: |
                      # gh pr checkout "$PR" would be wrong here; this lane has no tree.
                      echo "reporting only"
            """
        )
        assert checker.survey(root) == []
        assert _rules(root) == []

    def test_a_yaml_comment_does_not_satisfy_the_credential_rule(self, build_workflows: Callable[..., Path]) -> None:
        """#1456, the false-negative direction.

        The checkout really does resolve a pull-request ref and really does
        persist its credential. A comment spelled exactly as the key the check
        looks for may not make that finding go away.
        """
        root = build_workflows(
            lane="""
            name: Lane
            on:
              workflow_dispatch:
                inputs:
                  pull_request:
                    type: string
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                steps:
                  - uses: actions/checkout@v7
                    with:
                      # persist-credentials: false
                      ref: refs/pull/9/merge
            """
        )
        assert _rules(root) == [CREDENTIAL_RULE]

    def test_a_job_without_any_checkout_is_not_a_site(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request:
            jobs:
              label:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  issues: write
                steps:
                  - run: echo "no tree here"
            """
        )
        assert _rules(root) == []
        assert checker.survey(root) == []


class TestTheRatchet:
    """The exception list is data, and it is enumerated rather than assumed."""

    def test_an_entry_silences_exactly_its_own_scope(
        self, build_workflows: Callable[..., Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(checker.KNOWN_EXCEPTIONS, ("lane.yml", "build", "checks"), "measured elsewhere")
        root = build_workflows(
            lane="""
            name: Lane
            on:
              pull_request:
            jobs:
              build:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  checks: write
                  issues: write
                steps:
                  - uses: actions/checkout@v7
            """
        )
        assert _rules(root) == [WRITE_RULE]
        assert "`issues: write`" in _messages(root)
        assert "`checks: write`" not in _messages(root)

    def test_every_recorded_exception_names_a_site_that_still_exists(self) -> None:
        """A stale entry is a silenced rule nobody can see any more."""
        scan_root = checker.REPO_ROOT / checker.DEFAULT_SCAN_ROOT
        if not scan_root.is_dir():  # pragma: no cover - outside a full checkout
            pytest.skip("no .github/workflows in this checkout")
        live = {(site.workflow, site.job, scope) for site in checker.survey(scan_root) for scope in site.write_scopes}
        stale = sorted(key for key in checker.KNOWN_EXCEPTIONS if key not in live)
        assert stale == [], f"KNOWN_EXCEPTIONS entries with no matching site: {stale}"


class TestTheSurveyIsNotVacuous:
    """A green run has to be distinguishable from a run that looked at nothing."""

    def test_the_real_tree_has_sites(self) -> None:
        scan_root = checker.REPO_ROOT / checker.DEFAULT_SCAN_ROOT
        if not scan_root.is_dir():  # pragma: no cover - outside a full checkout
            pytest.skip("no .github/workflows in this checkout")
        sites = checker.survey(scan_root)
        assert len(sites) > 10
        assert any(c.explicit_ref for site in sites for c in site.checkouts)
