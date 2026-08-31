"""Tests for the fifth shape of ``scripts/check_workflow_gate_integrity.py`` (#1313).

**The invariant under test.** Every repo-relative path a path-filtered workflow
references in its *executable* body must be covered by that workflow's ``paths:``
filter — or carry a written reason why not. When the two drift apart the result
is always the same: **the one change most able to break a check is the one change
that never runs it**, and the breakage surfaces later, on ``develop`` or in a
nightly, where nobody can attribute it.

**Its own file, unlike shapes 1–4.** Those share
``test_workflow_gate_integrity_check.py``, one class each. This shape needs
something they do not: a *constructed source tree*, because coverage is decided
against paths that exist. Every test here therefore builds a workflow directory
**and** a checkout for it to reference, and the fixture pair would sit awkwardly
in a file whose other classes never need it.

**Red first, and by construction.** Every positive case here writes a workflow
that violates the invariant and asserts the checker reports it; every one is
paired with the compliant variant, so the fix the message asks for is proven to
clear the check rather than assumed to. The real-tree counter-proof — reverting
each of the four production fixes and watching the checker go red on the actual
``.github/workflows`` — was run by hand before this file was written and is
recorded in the pull request; a test cannot hold it, because it would have to
mutate the tree it runs in.

Traces to #1313 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_workflow_gate_integrity")


@pytest.fixture
def tree(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper that materialises a checkout for references to resolve in.

    Coverage is only asked about paths that exist, so a test that forgets to
    create the file it references would pass vacuously — the exact shape this
    whole checker is about. Every test below creates what it references.
    """

    def _build(*paths: str) -> Path:
        root = tmp_path / "tree"
        root.mkdir(exist_ok=True)
        for entry in paths:
            target = root / entry
            if entry.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("", encoding="utf-8")
        return root

    return _build


@pytest.fixture
def workflows(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing workflow files into a ``workflows/`` directory."""

    def _build(**files: str) -> Path:
        root = tmp_path / "workflows"
        root.mkdir(exist_ok=True)
        for name, content in files.items():
            (root / f"{name}.yml").write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return root

    return _build


def _findings(root: Path, tree_root: Path) -> list[checker.Finding]:
    """Every *counted* path-coverage finding, in file order."""
    return [
        finding
        for finding in checker.collect(root, tree_root)
        if finding.kind == "uncovered_path_reference" and not finding.justified
    ]


def _references(root: Path, tree_root: Path) -> list[str]:
    """The referenced path of every counted finding."""
    return [finding.detail.split("'")[1] for finding in _findings(root, tree_root)]


_PIN_LANE = """
name: Nuclei templates
on:
  pull_request:
    branches: [develop]
    paths:
%s
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: yq e '.nuclei_templates_version' .github/renovate-pins.yaml
"""


class TestTheIssueShape:
    """#1302, reintroduced on purpose, and then repaired."""

    def test_reintroducing_1302_turns_the_check_red(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """The exact defect: the lane reads the pins file, its filter excludes it.

        #1280 changed only `.github/renovate-pins.yaml`, ran no nuclei check at
        all, merged green — and the nightly scan then failed to start for two
        nights. This is that workflow reduced to the two lines that matter.
        """
        root = workflows(nuclei=_PIN_LANE % "      - 'tests/security/nuclei-templates/**'")
        checkout = tree("tests/security/nuclei-templates/", ".github/renovate-pins.yaml")
        assert _references(root, checkout) == [".github/renovate-pins.yaml"]

    def test_adding_the_path_to_the_filter_clears_it(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Option 1 of #1302 — the fix the message asks for has to work."""
        root = workflows(
            nuclei=_PIN_LANE % ("      - 'tests/security/nuclei-templates/**'\n      - '.github/renovate-pins.yaml'")
        )
        checkout = tree("tests/security/nuclei-templates/", ".github/renovate-pins.yaml")
        assert _references(root, checkout) == []

    def test_the_script_a_delivery_lane_runs_is_caught(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """`docker-publish.yml` runs the script that computes the published version.

        `scripts/**` was absent from its `push` filter, so a change to
        `determine_chart_version.sh` never ran the workflow that publishes what
        it computes. This instance was not reported anywhere before #1313.
        """
        root = workflows(
            publish="""
            name: Publish
            on:
              push:
                branches: [develop]
                paths:
                  - 'src/backend/**'
                  - 'helm/**'
            jobs:
              publish:
                runs-on: ubuntu-latest
                steps:
                  - run: scripts/ci/determine_chart_version.sh
            """
        )
        checkout = tree("src/backend/app/main.py", "helm/chart/values.yaml", "scripts/ci/determine_chart_version.sh")
        assert _references(root, checkout) == ["scripts/ci/determine_chart_version.sh"]

    def test_the_process_exits_non_zero_and_says_what_to_do(
        self,
        workflows: Callable[..., Path],
        tree: Callable[..., Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        root = workflows(nuclei=_PIN_LANE % "      - 'tests/security/nuclei-templates/**'")
        checkout = tree("tests/security/nuclei-templates/", ".github/renovate-pins.yaml")
        code = checker.main(["--scan-root", str(root), "--tree-root", str(checkout)])
        assert code == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert ".github/renovate-pins.yaml" in out
        assert "paths:" in out
        assert "#1313" in out


class TestWhatCountsAsAReference:
    """Literal paths in executable lines — and nothing else."""

    def test_a_path_named_only_in_a_comment_is_not_a_reference(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Measured: leaving comments in raised 11 candidates against 4 real ones.

        This repository argues about paths in prose at length — headers that
        explain why a filter is narrow, notes about sibling lanes, links to
        specs. A checker that read its subject matter out of prose would be
        switched off by the first person who read the report.
        """
        root = workflows(
            gate="""
            name: Gate
            # Deliberately does NOT watch scripts/ci/publish_release_asset.sh —
            # see the header of docs/security/nuclei-triage.md for why.
            on:
              push:
                paths:
                  - 'src/backend/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                # spec/nfr/NFR-014_Nuclei-Security-Scanning.md §3.2 explains this.
                steps:
                  - run: echo hi
            """
        )
        checkout = tree(
            "src/backend/app/main.py",
            "scripts/ci/publish_release_asset.sh",
            "docs/security/nuclei-triage.md",
            "spec/nfr/NFR-014_Nuclei-Security-Scanning.md",
        )
        assert _references(root, checkout) == []

    def test_a_path_that_does_not_exist_is_not_a_reference(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Existence is the precision device, and it is doing real work here.

        `results.sarif` is written by the run, not read from the checkout;
        `ghcr.io/nolte/kamerplanter-backend` is an image; `actions/checkout` is
        an action reference. None of them is a file this workflow reads, and
        none of them exists in the tree — which is how they are told apart from
        one without a shell parser.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/backend/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
                  - run: scanner -o results/scan.sarif
                  - run: docker pull ghcr.io/nolte/kamerplanter-backend:latest
            """
        )
        checkout = tree("src/backend/app/main.py")
        assert _references(root, checkout) == []

    def test_a_leading_dot_slash_is_the_same_reference(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """`./scripts/run-e2e.sh` and `scripts/run-e2e.sh` are one path.

        Without this normalisation the checker reported four covered references
        as uncovered on the real tree — every one of them a filter entry that
        already existed, which is the false-positive class that gets a required
        gate switched off.
        """
        covered = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'scripts/run-e2e.sh'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ./scripts/run-e2e.sh
            """
        )
        checkout = tree("scripts/run-e2e.sh")
        assert _references(covered, checkout) == []

    def test_a_single_segment_name_is_not_a_reference(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """`docker`, `helm` and `spec` are directories AND ordinary words.

        Accepting one-segment candidates would make `run: docker build .` a
        reference to the `docker/` directory. The rule is at least two
        `/`-separated segments, and the cost is stated in the docstring: a
        top-level `Taskfile.yaml` reference is invisible.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/backend/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: docker build helm
            """
        )
        checkout = tree("docker/backend/Dockerfile", "helm/chart/Chart.yaml", "src/backend/app.py")
        assert _references(root, checkout) == []

    def test_the_trigger_block_itself_is_not_a_reference(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """A `paths:` entry is the filter, not something the workflow reads.

        Without this the checker read `!scripts/ci/**` as a *reference* to the
        very directory that entry removes from the trigger, and reported the
        exclusion as its own violation — the first false positive this shape
        produced, caught by the negation test below.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                branches: [develop]
                paths:
                  - 'src/backend/**'
                  - '!src/backend/docs/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: echo hi
            """
        )
        checkout = tree("src/backend/app.py", "src/backend/docs/index.md")
        assert _references(root, checkout) == []

    def test_a_paths_filter_action_inside_jobs_is_a_reference(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """A `dorny/paths-filter` fan-out is the workflow reasoning about paths.

        This is how `docker-publish.yml`'s side-service drift surfaced: the
        fan-out has selected on `src/inference-service/**` since those build
        jobs were added, while the trigger never listed it — so a develop push
        touching only that tree published nothing. Commit 5a67d9776 (2026-07-04)
        changed exactly `src/knowledge-service/app/service.py` and the GitHub
        API reports zero `docker-publish.yml` runs for that SHA.
        """
        root = workflows(
            publish="""
            name: Publish
            on:
              push:
                branches: [develop]
                paths:
                  - 'src/backend/**'
            jobs:
              changes:
                runs-on: ubuntu-latest
                steps:
                  - uses: dorny/paths-filter@v3
                    with:
                      filters: |
                        backend:
                          - 'src/backend/**'
                        inference-service:
                          - 'src/inference-service/**'
            """
        )
        checkout = tree("src/backend/app.py", "src/inference-service/Dockerfile")
        assert _references(root, checkout) == ["src/inference-service"]

    def test_a_workflow_without_a_paths_filter_is_out_of_scope(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """No filter, no drift: it already runs on every change.

        Reporting these would put a finding on every unfiltered workflow in the
        repository while naming no defect.
        """
        root = workflows(
            gate="""
            name: Gate
            on: [push]
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: scripts/ci/determine_chart_version.sh
            """
        )
        checkout = tree("scripts/ci/determine_chart_version.sh")
        assert _references(root, checkout) == []

    def test_an_unfiltered_schedule_leg_does_not_exempt_a_filtered_workflow(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """`schedule` and `workflow_dispatch` fire regardless of the diff.

        `security-nuclei-templates.yml` carries both, and both were running
        while #1302 was open — which is precisely why they do not count: neither
        puts the change that breaks a check in front of that check.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              pull_request:
                paths:
                  - 'tests/security/nuclei-templates/**'
              schedule:
                - cron: '17 1 * * *'
              workflow_dispatch:
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: yq e '.nuclei_version' .github/renovate-pins.yaml
            """
        )
        checkout = tree("tests/security/nuclei-templates/", ".github/renovate-pins.yaml")
        assert _references(root, checkout) == [".github/renovate-pins.yaml"]


class TestWhatCountsAsCovered:
    """GitHub's filter-glob semantics, including the cases that bite."""

    def _lane(self, pattern: str, reference: str) -> str:
        return f"""
        name: Gate
        on:
          push:
            paths:
              - '{pattern}'
        jobs:
          check:
            runs-on: ubuntu-latest
            steps:
              - run: cat {reference}
        """

    @pytest.mark.parametrize(
        ("pattern", "reference"),
        [
            ("src/backend/**", "src/backend/app/main.py"),
            ("src/backend/**", "src/backend/app.py"),
            ("scripts/ci/determine_chart_version.sh", "scripts/ci/determine_chart_version.sh"),
            ("src/*/Dockerfile", "src/backend/Dockerfile"),
            ("src/backend/Dockerfile*", "src/backend/Dockerfile.dev"),
            ("tests/security/zap-**", "tests/security/zap-rules/base.conf"),
            ("src/backend/app/mai?.py", "src/backend/app/main.py"),
        ],
    )
    def test_covered_patterns(
        self,
        pattern: str,
        reference: str,
        workflows: Callable[..., Path],
        tree: Callable[..., Path],
    ) -> None:
        root = workflows(gate=self._lane(pattern, reference))
        assert _references(root, tree(reference)) == []

    @pytest.mark.parametrize(
        ("pattern", "reference"),
        [
            # `*` stops at a separator — the difference between `src/*` and
            # `src/**`, and the reason a naive fnmatch translation over-covers.
            ("src/*", "src/backend/app.py"),
            # A literal dot is a literal dot. `re.escape` rather than a naive
            # fnmatch translation: unescaped, the `.` in `renovate-pins.yaml`
            # becomes "any character" and the entry would also cover
            # `renovate-pinsXyaml`, silently widening every filter in the repo.
            ("src/backend/app.py", "src/backend/appXpy"),
            ("src/backend/app_main.py", "src/backend/app.main.py"),
            ("scripts/ci/**", ".github/renovate-pins.yaml"),
            # A sibling prefix is not a prefix: `src/back` must not cover
            # `src/backend/...`.
            ("src/back/**", "src/backend/app.py"),
        ],
    )
    def test_uncovered_patterns(
        self,
        pattern: str,
        reference: str,
        workflows: Callable[..., Path],
        tree: Callable[..., Path],
    ) -> None:
        root = workflows(gate=self._lane(pattern, reference))
        assert _references(root, tree(reference)) == [reference]

    def test_a_directory_is_covered_by_a_filter_reaching_into_it(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """`context: src/inference-service` against `src/inference-service/**`.

        A directory never appears in a diff, so `src/inference-service/**` does
        not match the directory name itself — but any change *inside* it fires
        the workflow, which is the property being asserted.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/inference-service/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - uses: docker/build-push-action@v7
                    with:
                      context: src/inference-service
            """
        )
        checkout = tree("src/inference-service/Dockerfile")
        assert _references(root, checkout) == []

    def test_partial_coverage_of_a_directory_counts(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """`src/backend/app/**` against a reference to `src/backend`.

        Not every change under `src/backend` fires the lane, so this is
        genuinely incomplete — and it is still not what this shape reports. The
        finding is "no trigger path reaches here at all"; grading completeness
        would report entries that do fire and need a reason nobody can honestly
        write.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/backend/app/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ls src/backend
            """
        )
        checkout = tree("src/backend/app/main.py", "src/backend/tests/test_main.py")
        assert _references(root, checkout) == []

    def test_a_directory_reachable_from_no_entry_is_a_finding(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """The negative half of the two tests above, so neither is vacuous."""
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/backend/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: ls src/inference-service
            """
        )
        checkout = tree("src/backend/app.py", "src/inference-service/Dockerfile")
        assert _references(root, checkout) == ["src/inference-service"]

    def test_the_union_across_triggers_is_what_counts(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """A narrower `push` filter beside a wider `pull_request` one is not a finding.

        `security-nuclei-templates.yml` is exactly this: its `push` leg watches
        only the template directory while its `pull_request` leg also watches
        the validator hook and the pins file. Grading each trigger separately
        would report three "findings" naming no defect. Whether the *right lane*
        fires is #1302's deeper half and needs a different judgement.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              pull_request:
                paths:
                  - 'tests/security/nuclei-templates/**'
                  - '.github/renovate-pins.yaml'
              push:
                branches: [develop]
                paths:
                  - 'tests/security/nuclei-templates/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: yq e '.nuclei_version' .github/renovate-pins.yaml
            """
        )
        checkout = tree("tests/security/nuclei-templates/", ".github/renovate-pins.yaml")
        assert _references(root, checkout) == []

    def test_a_negated_entry_takes_coverage_away_again(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """GitHub lets the LAST matching entry decide, so `!` subtracts.

        `src/backend/**` admits `src/backend/generated/api.ts`; the exclusion
        after it takes that back, and a change there does not run the workflow —
        so the reference is uncovered even though a positive entry matches it.

        Merely *skipping* `!` entries would look equivalent and is not: the
        leading `!` escapes into the regex and could never match anything, which
        made the skipping line unobservable. A guard nobody can watch fail is
        exactly what this checker exists to refuse.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/backend/**'
                  - '!src/backend/generated/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: cat src/backend/generated/api.ts
            """
        )
        checkout = tree("src/backend/app.py", "src/backend/generated/api.ts")
        assert _references(root, checkout) == ["src/backend/generated/api.ts"]

    def test_a_positive_entry_after_a_negation_wins(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Order, not precedence: the same two entries the other way round cover it."""
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - '!src/backend/generated/**'
                  - 'src/backend/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: cat src/backend/generated/api.ts
            """
        )
        checkout = tree("src/backend/app.py", "src/backend/generated/api.ts")
        assert _references(root, checkout) == []

    def test_a_negation_on_one_trigger_does_not_reach_another(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Per-trigger grouping: ordering is only meaningful inside one list.

        The `push` lane watches the pins file; the `pull_request` lane
        deliberately does not. Flattening both into one ordered list would let
        the pull-request exclusion — evaluated last — cancel the push entry, and
        report a reference the push lane genuinely watches.
        """
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                branches: [develop]
                paths:
                  - 'tests/security/nuclei-templates/**'
                  - '.github/renovate-pins.yaml'
              pull_request:
                paths:
                  - 'tests/security/nuclei-templates/**'
                  - '!.github/renovate-pins.yaml'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: yq e '.nuclei_version' .github/renovate-pins.yaml
            """
        )
        checkout = tree("tests/security/nuclei-templates/", ".github/renovate-pins.yaml")
        assert _references(root, checkout) == []


class TestTheEscapeHatch:
    """Some references genuinely should not widen a trigger — with a reason."""

    _QUOTING_LANE = """
    name: Report
    on:
      push:
        paths:
          - 'src/backend/**'
    %s
    jobs:
      report:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/github-script@v8
            with:
              script: |
                await github.rest.issues.create({
                  body: [
                    'Follow `docs/security/nuclei-triage.md`, then open a fix-forward PR.',
                  ].join('\\n'),
                });
    """

    def test_without_a_reason_the_quoted_path_is_a_finding(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Start red: the hatch has to be shown to change something."""
        root = workflows(gate=self._QUOTING_LANE % "")
        checkout = tree("src/backend/app.py", "docs/security/nuclei-triage.md")
        assert _references(root, checkout) == ["docs/security/nuclei-triage.md"]

    def test_a_reason_naming_the_path_exempts_it(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """The real placement: beside the `paths:` filter it declines to widen.

        The reference sits inside a JavaScript string array, where a trailing
        `#` is a syntax error rather than a comment — so the shared
        "on the line, or the block above it" placements are physically
        unreachable. Naming the path is what keeps this from being a file-wide
        silencer.
        """
        marker = (
            "    # gate-integrity-ok: docs/security/nuclei-triage.md is quoted in the\n"
            "    # body of the issue this lane opens, never read by a step; widening\n"
            "    # the trigger would run the whole scan on a documentation edit."
        )
        root = workflows(gate=self._QUOTING_LANE % marker)
        checkout = tree("src/backend/app.py", "docs/security/nuclei-triage.md")
        assert _references(root, checkout) == []

    def test_a_reason_that_does_not_name_the_path_exempts_nothing(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """Otherwise one marker anywhere would silence every reference in the file."""
        marker = (
            "    # gate-integrity-ok: this lane deliberately keeps a narrow trigger,\n"
            "    # because a full scan costs nineteen minutes."
        )
        root = workflows(gate=self._QUOTING_LANE % marker)
        checkout = tree("src/backend/app.py", "docs/security/nuclei-triage.md")
        assert _references(root, checkout) == ["docs/security/nuclei-triage.md"]

    def test_a_bare_marker_is_not_an_exemption(self, workflows: Callable[..., Path], tree: Callable[..., Path]) -> None:
        """The point of the hatch is the reason, not the token.

        A marker whose entire reason is the path name is under the shared
        minimum length, so it cannot be used to wave a path through.
        """
        root = workflows(gate=self._QUOTING_LANE % "    # gate-integrity-ok: docs")
        checkout = tree("src/backend/app.py", "docs/security/nuclei-triage.md")
        assert _references(root, checkout) == ["docs/security/nuclei-triage.md"]

    def test_a_reason_on_the_referencing_line_exempts_it(
        self, workflows: Callable[..., Path], tree: Callable[..., Path]
    ) -> None:
        """The shared placement still works where the syntax allows a `#`."""
        root = workflows(
            gate="""
            name: Gate
            on:
              push:
                paths:
                  - 'src/backend/**'
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - run: cat docs/security/nuclei-triage.md  # gate-integrity-ok: printed as a hint, never gating
            """
        )
        checkout = tree("src/backend/app.py", "docs/security/nuclei-triage.md")
        assert _references(root, checkout) == []

    def test_an_exempted_reference_stays_visible_in_the_report(
        self,
        workflows: Callable[..., Path],
        tree: Callable[..., Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A silent exemption is indistinguishable from a fix — the whole subject."""
        marker = (
            "    # gate-integrity-ok: docs/security/nuclei-triage.md is quoted in an\n"
            "    # issue body, never read by a step."
        )
        root = workflows(gate=self._QUOTING_LANE % marker)
        checkout = tree("src/backend/app.py", "docs/security/nuclei-triage.md")
        code = checker.main(["--scan-root", str(root), "--tree-root", str(checkout), "--list"])
        assert code == checker.EXIT_OK
        assert "docs/security/nuclei-triage.md is quoted" in capsys.readouterr().out


class TestTheRealTree:
    """What the pre-commit hook asserts, asserted here too.

    The default tree root is this checkout, so this runs the fifth shape over
    the real `.github/workflows` — the same measurement the required `static`
    lane makes.
    """

    def test_every_referenced_path_is_covered_or_explained(self) -> None:
        assert checker.main([]) == checker.EXIT_OK
