"""Tests for the #1222 chart-version gate (``scripts/check_chart_develop_version.py``).

**What is under test.** The detection logic, driven against *constructed*
``Chart.yaml`` files written into ``tmp_path`` — never against the real
``helm/``. A test asserting "the tree is clean" would be inverted by the very
commit that repairs the tree, and a test asserting "the tree is broken" would be
inverted by the commit after that; neither teaches anyone what the rule is.

**The two falsification directions, both pinned here.** :class:`TestTheIncident`
carries them:

1. The exact pre-fix ``helm/kamerplanter/Chart.yaml`` — ``version: 0.2.0``, the
   tree that on 2026-08-18 republished ``charts/kamerplanter:0.2.0`` five days
   after release ``v0.2.0`` had published it — MUST be a finding naming
   ``version 0.2.0``.
2. ``version: 0.3.0`` MUST *also* be a finding. A checker that merely forbade the
   literal ``0.2.0`` would pass ``0.3.0`` and reintroduce the defect at the very
   next release: the rule is "not a releasable version", not "not 0.2.0".

Both are stated as tests rather than left to the PR body, because a checker that
only ever agrees with the repaired tree certifies nothing.

:class:`TestTheMarkerMustOpenTheComment` carries a third direction, found in
review (F-5): a comment block that *explains* the escape hatch — the natural
thing to write above ``version:`` — must not *be* the escape hatch. The reviewer's
reproduction is :data:`PROSE_EXPLAINING_THE_HATCH`, held verbatim, and it exited 0
on a releasable ``0.2.0`` while reporting "1 justified site(s)". The class asserts
both directions, because anchoring the marker must not amount to removing it.

**The pre-fix file is reproduced verbatim, not read from the tree.** It is a
module constant here. Reading it from ``helm/`` would make the test follow the
repair and stop testing anything; reading it from a git object would make a unit
test depend on the checkout's history depth, which is the same
shallow-vs-full asymmetry that got the strong rule rejected in the first place.
It also carries the real chart's ``dependencies:`` block, whose three nested
``version:`` keys are exactly what a naive anchor would latch onto.

**What the real tree is NOT asserted here, and why.** The sibling
``test_workflow_gate_integrity_check.py`` ends with a ``TestTheRealTree`` class
re-asserting what its pre-commit hook already asserts. This file deliberately has
no such class: at the moment it was written the real tree was still broken —
that is the point, the guard was authored before the fix so it could be *seen*
failing against the genuine defect — and a test pinning that state would have to
be inverted by the commit that repairs it. The real tree is gated by the
``chart-develop-version`` pre-commit hook, which runs in the required
``static / Static CI Tests`` lane on every push to every branch.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded by path. It is not a
backend test in subject; it is one in placement, because this is the tier that
runs.

Traces to issue #1222 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_chart_develop_version")

#: ``git show 17aae5f58:helm/kamerplanter/Chart.yaml`` — the exact tree that
#: produced the measured overwrite of ``charts/kamerplanter:0.2.0``. Held as a
#: constant so it stays the pre-fix shape after the tree is repaired.
PRE_FIX_CHART = """
apiVersion: v2
name: kamerplanter
description: Kamerplanter plant lifecycle management system
type: application
version: 0.2.0
appVersion: "1.0.0"
dependencies:
  - name: common
    repository: https://bjw-s-labs.github.io/helm-charts/
    version: 5.0.1
  - name: valkey
    repository: oci://ghcr.io/valkey-io/valkey-helm
    version: 0.10.0
    condition: valkey.enabled
  - name: ollama
    repository: https://otwld.github.io/ollama-helm/
    version: 1.62.0
    condition: ollama.enabled
"""


#: The reviewer's reproduction of finding F-5, verbatim. A comment block that
#: *explains* the escape hatch — the natural thing to write directly above
#: ``version:`` — while stating that this chart is **not** exempt. Under the
#: substring search this file was reported as "1 justified site(s)" and exited 0
#: with a plainly releasable ``version: 0.2.0``.
PROSE_EXPLAINING_THE_HATCH = """
apiVersion: v2
name: probe
description: probe chart
type: application
# The develop tree carries a -dev pre-release so a merge cannot republish a
# released chart version. If a chart legitimately reaches the registry some
# other way, the escape hatch is `# chart-develop-version-ok: <reason>` written
# on the version line or in this block. That is documentation of the mechanism,
# not a claim that this chart is exempt.
version: 0.2.0
appVersion: "1.0.0"
"""


def chart(version: str) -> str:
    """The real chart's shape carrying *version* as its top-level version.

    Derived from :data:`PRE_FIX_CHART` by substitution rather than written fresh,
    so every case keeps the ``dependencies:`` block and its three nested
    ``version:`` keys.
    """
    return PRE_FIX_CHART.replace("version: 0.2.0", f"version: {version}", 1)


@pytest.fixture
def build_charts(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing ``<name>/Chart.yaml`` files into a helm root.

    Keyword names become chart directory names, with ``_`` read as ``-`` so a
    hyphenated chart name is expressible as a Python keyword.
    """

    def _build(**charts: str) -> Path:
        root = tmp_path / "helm"
        root.mkdir(exist_ok=True)
        for name, content in charts.items():
            directory = root / name.replace("_", "-")
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "Chart.yaml").write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return root

    return _build


def _findings(root: Path) -> list[Any]:
    """Every finding under a constructed helm root, justified or not."""
    return checker.collect(checker.discover(root))


def _kinds(root: Path) -> list[str]:
    """The kind of every *counted* finding, sorted."""
    return sorted(finding.kind for finding in _findings(root) if not finding.justified)


def _details(root: Path) -> list[str]:
    """The detail text of every *counted* finding."""
    return [finding.detail for finding in _findings(root) if not finding.justified]


class TestItCanFail:
    """The broken shape, and the check going red on it."""

    def test_a_releasable_version_is_caught(self, build_charts: Callable[..., Path]) -> None:
        """A version with no pre-release is the defect in its simplest form."""
        root = build_charts(kamerplanter=chart("0.2.0"))
        assert _kinds(root) == ["chart_version_releasable"]

    def test_the_broken_chart_makes_the_process_exit_non_zero(
        self, build_charts: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        root = build_charts(kamerplanter=chart("0.2.0"))
        assert checker.main(["--helm-root", str(root)]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "#1222" in out
        assert checker.JUSTIFICATION_MARKER in out

    def test_the_finding_names_the_file_and_the_version(self, build_charts: Callable[..., Path]) -> None:
        """A verdict alone does not tell anyone which chart to open, or what is wrong."""
        root = build_charts(kamerplanter=chart("0.2.0"), other_chart=chart("0.9.0-dev"))
        findings = _findings(root)
        assert len(findings) == 1
        assert findings[0].relative().endswith("kamerplanter/Chart.yaml")
        assert "version 0.2.0" in findings[0].detail

    def test_the_finding_points_at_the_top_level_version_key(self, build_charts: Callable[..., Path]) -> None:
        """Line 5 of the real chart — not one of the three dependency versions.

        The anchor is where the escape-hatch comment must go, so an anchor on a
        ``dependencies:`` entry would put the hatch on somebody else's version.
        """
        root = build_charts(kamerplanter=chart("0.2.0"))
        assert [finding.line for finding in _findings(root)] == [5]

    def test_a_dev_version_is_green(self, build_charts: Callable[..., Path]) -> None:
        """The fix the message asks for actually clears the check."""
        root = build_charts(kamerplanter=chart("0.3.0-dev"))
        assert _kinds(root) == []
        assert checker.main(["--helm-root", str(root)]) == checker.EXIT_OK


class TestTheIncident:
    """The two falsification directions #1222 requires, as tests.

    The first says the checker detects the real, measured defect. The second says
    it detects the *class* of defect rather than one literal string — without it,
    a checker that forbade only ``0.2.0`` would pass this suite and reintroduce
    the incident at the next release.
    """

    def test_the_pre_fix_chart_yaml_is_a_finding(self, build_charts: Callable[..., Path]) -> None:
        """``17aae5f58``'s ``Chart.yaml`` — the tree that overwrote the release tag."""
        root = build_charts(kamerplanter=PRE_FIX_CHART)
        assert _kinds(root) == ["chart_version_releasable"]

    def test_the_finding_says_0_2_0_carries_no_dev_pre_release(self, build_charts: Callable[..., Path]) -> None:
        """The message must name the value and the missing channel, not just fail."""
        root = build_charts(kamerplanter=PRE_FIX_CHART)
        (detail,) = _details(root)
        assert "version 0.2.0" in detail
        assert "no pre-release" in detail
        assert "'dev'" in detail

    def test_a_different_release_shaped_version_is_also_a_finding(self, build_charts: Callable[..., Path]) -> None:
        """0.3.0 is not published today — and is still forbidden.

        This is the direction that separates "not a releasable version" from
        "not the literal 0.2.0". A checker blind to it would go green the moment
        somebody hand-bumped the develop tree, which is exactly how the next
        release version would get overwritten.
        """
        root = build_charts(kamerplanter=chart("0.3.0"))
        assert _kinds(root) == ["chart_version_releasable"]
        assert "version 0.3.0" in _details(root)[0]

    def test_the_pre_fix_chart_exits_non_zero_through_the_cli(self, build_charts: Callable[..., Path]) -> None:
        """The acceptance criterion is about the *process*, via ``--chart``."""
        root = build_charts(kamerplanter=PRE_FIX_CHART)
        argv = ["--chart", str(root / "kamerplanter" / "Chart.yaml")]
        assert checker.main(argv) == checker.EXIT_DEFECTS

    def test_the_repaired_chart_clears_it(self, build_charts: Callable[..., Path]) -> None:
        """Both directions, because a checker that only agrees with the fix proves nothing."""
        root = build_charts(kamerplanter=chart("0.3.0-dev"))
        assert _kinds(root) == []


class TestTheChannelIdentifier:
    """Which pre-releases count as the develop channel, and which do not."""

    def test_a_release_candidate_is_not_the_develop_channel(self, build_charts: Callable[..., Path]) -> None:
        """An ``-rc1`` tag is a release, so a develop tree carrying it can collide."""
        root = build_charts(kamerplanter=chart("0.3.0-rc1"))
        assert _kinds(root) == ["chart_version_wrong_channel"]

    def test_a_dotted_dev_identifier_is_the_develop_channel(self, build_charts: Callable[..., Path]) -> None:
        """Only the FIRST identifier is reserved, so ``dev.4`` is fine."""
        root = build_charts(kamerplanter=chart("0.3.0-dev.4"))
        assert _kinds(root) == []

    def test_a_prefix_of_dev_is_not_enough(self, build_charts: Callable[..., Path]) -> None:
        """``development`` starts with ``dev`` and is a word a release could carry.

        A ``startswith`` test would admit it, and P3's release-side rejection is
        written against the exact identifier — the two must agree or the guard's
        premise does not hold.
        """
        root = build_charts(kamerplanter=chart("0.3.0-development"))
        assert _kinds(root) == ["chart_version_wrong_channel"]

    def test_the_comparison_is_case_sensitive(self, build_charts: Callable[..., Path]) -> None:
        """SemVer pre-release identifiers are case-sensitive; so is this rule."""
        root = build_charts(kamerplanter=chart("0.3.0-DEV"))
        assert _kinds(root) == ["chart_version_wrong_channel"]

    def test_a_hyphenated_dev_identifier_is_a_different_identifier(self, build_charts: Callable[..., Path]) -> None:
        """``dev-1`` is one identifier, not ``dev`` followed by anything."""
        root = build_charts(kamerplanter=chart("0.3.0-dev-1"))
        assert _kinds(root) == ["chart_version_wrong_channel"]

    def test_the_wrong_channel_finding_names_the_identifier_it_found(self, build_charts: Callable[..., Path]) -> None:
        """A verdict of 'wrong' without saying what was read is one nobody can act on."""
        root = build_charts(kamerplanter=chart("0.3.0-rc1"))
        (detail,) = _details(root)
        assert "'rc1'" in detail
        assert "'dev'" in detail


class TestSemverStrictness:
    """The first half of the rule: it must parse as SemVer 2.0.0."""

    def test_a_leading_v_is_not_semver(self, build_charts: Callable[..., Path]) -> None:
        """Helm's own parser is lenient about ``v0.3.0``; SemVer 2.0.0 is not.

        Accepting it would leave a value whose relationship to ``${REF_NAME#v}``
        — the release version — this rule cannot reason about.
        """
        root = build_charts(kamerplanter=chart("v0.3.0-dev"))
        assert _kinds(root) == ["chart_version_not_semver"]

    def test_a_two_segment_version_is_not_semver(self, build_charts: Callable[..., Path]) -> None:
        """``version: 1.0`` also parses out of YAML as a float, not a string."""
        root = build_charts(kamerplanter=chart("1.0"))
        assert _kinds(root) == ["chart_version_not_semver"]

    def test_a_missing_patch_with_a_dev_suffix_is_not_semver(self, build_charts: Callable[..., Path]) -> None:
        """Carrying ``dev`` does not excuse a malformed core version."""
        root = build_charts(kamerplanter=chart("0.3-dev"))
        assert _kinds(root) == ["chart_version_not_semver"]

    def test_a_leading_zero_segment_is_not_semver(self, build_charts: Callable[..., Path]) -> None:
        """``01`` is forbidden by the grammar, and quoting keeps YAML out of it."""
        root = build_charts(kamerplanter=chart('"0.01.0-dev"'))
        assert _kinds(root) == ["chart_version_not_semver"]

    def test_build_metadata_is_allowed(self, build_charts: Callable[..., Path]) -> None:
        """``+meta`` is part of SemVer 2.0.0 and does not move the channel."""
        root = build_charts(kamerplanter=chart("0.3.0-dev+build.7"))
        assert _kinds(root) == []

    def test_the_not_semver_finding_names_the_value(self, build_charts: Callable[..., Path]) -> None:
        """The value as spelled, so the reader can see the typo."""
        root = build_charts(kamerplanter=chart("v0.3.0-dev"))
        assert "version v0.3.0-dev" in _details(root)[0]


class TestAMissingVersion:
    """A chart that declares no version at all is a finding, not a pass."""

    def test_no_version_key_is_a_finding(self, build_charts: Callable[..., Path]) -> None:
        """``helm package`` would fail on it, and reporting clean hides that."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            type: application
            appVersion: "1.0.0"
            """
        )
        assert _kinds(root) == ["chart_version_missing"]

    def test_an_empty_version_is_a_finding(self, build_charts: Callable[..., Path]) -> None:
        """``version:`` with nothing after it parses as null, not as a version."""
        root = build_charts(kamerplanter=chart(""))
        assert _kinds(root) == ["chart_version_missing"]

    def test_the_missing_finding_still_has_an_anchor(self, build_charts: Callable[..., Path]) -> None:
        """It must land on a real line, or the escape hatch has nowhere to go."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            """
        )
        assert [finding.line for finding in _findings(root)] == [1]


class TestScanScope:
    """Which files the default scan reaches — and which it deliberately does not."""

    def test_every_top_level_chart_is_scanned(self, build_charts: Callable[..., Path]) -> None:
        """One clean chart must not exculpate a broken sibling."""
        root = build_charts(alpha=chart("0.1.0-dev"), beta=chart("0.2.0"), gamma=chart("0.4.0"))
        assert _kinds(root) == ["chart_version_releasable", "chart_version_releasable"]

    def test_a_fetched_dependency_chart_is_not_scanned(self, build_charts: Callable[..., Path]) -> None:
        """``helm/<chart>/charts/<dep>/Chart.yaml`` holds somebody else's version.

        Those are never published from this repository, and demanding a ``dev``
        pre-release of them would make the gate unpassable the moment
        ``helm dependency build`` ran.
        """
        root = build_charts(kamerplanter=chart("0.3.0-dev"))
        vendored = root / "kamerplanter" / "charts" / "common"
        vendored.mkdir(parents=True)
        (vendored / "Chart.yaml").write_text("apiVersion: v2\nname: common\nversion: 5.0.1\n", encoding="utf-8")
        assert _kinds(root) == []
        assert checker.main(["--helm-root", str(root)]) == checker.EXIT_OK


class TestJustification:
    """The escape hatch, and the two ways of not qualifying for it."""

    def test_a_reason_in_the_comment_block_above_the_key_exempts_it(self, build_charts: Callable[..., Path]) -> None:
        """Where a chart already explains its version choice."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            # chart-develop-version-ok: never published from this repository
            version: 0.2.0
            """
        )
        assert _kinds(root) == []
        assert [finding.justified for finding in _findings(root)] == [True]

    def test_a_reason_on_the_version_line_exempts_it(self, build_charts: Callable[..., Path]) -> None:
        """The trailing form, for a one-line answer."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            version: 0.2.0  # chart-develop-version-ok: never published from this repository
            """
        )
        assert _kinds(root) == []

    def test_a_bare_marker_is_not_an_exemption(self, build_charts: Callable[..., Path]) -> None:
        """Otherwise the hatch is a silencer."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            version: 0.2.0  # chart-develop-version-ok:
            """
        )
        assert _kinds(root) == ["chart_version_releasable"]

    def test_a_too_short_reason_is_not_an_exemption(self, build_charts: Callable[..., Path]) -> None:
        """One word is not a justification."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            version: 0.2.0  # chart-develop-version-ok: ok
            """
        )
        assert _kinds(root) == ["chart_version_releasable"]

    def test_the_report_names_every_justified_chart(
        self, build_charts: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``--list`` is what makes standing exemptions countable."""
        root = build_charts(
            kamerplanter="""
            apiVersion: v2
            name: kamerplanter
            version: 0.2.0  # chart-develop-version-ok: never published from this repository
            """
        )
        assert checker.main(["--helm-root", str(root), "--list"]) == checker.EXIT_OK
        assert "never published from this repository" in capsys.readouterr().out


class TestTheMarkerMustOpenTheComment:
    """Finding F-5: prose *about* the hatch is not a use of the hatch.

    The exemption is recognised only where a comment begins — the trailing
    comment on the ``version:`` line, or the head of a comment line above it.
    A substring search over the block admitted any sentence that merely named
    the marker, and the block above ``version:`` is precisely where a chart
    explains the mechanism. Both directions live here: the prose must not exempt,
    and a genuine marker must still exempt, including when it sits in the same
    block as the prose.
    """

    def test_prose_explaining_the_hatch_does_not_exempt_a_releasable_version(
        self, build_charts: Callable[..., Path]
    ) -> None:
        """The reviewer's reproduction, verbatim: releasable, and reported so."""
        root = build_charts(probe=PROSE_EXPLAINING_THE_HATCH)
        assert _kinds(root) == ["chart_version_releasable"]
        assert [finding.justified for finding in _findings(root)] == [False]

    def test_the_prose_fixture_exits_non_zero(
        self, build_charts: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """It exited 0 announcing "1 justified site(s)" — the shape NFR-018 §2 forbids."""
        root = build_charts(probe=PROSE_EXPLAINING_THE_HATCH)
        assert checker.main(["--helm-root", str(root), "--list"]) == checker.EXIT_DEFECTS
        assert "justified site(s)" not in capsys.readouterr().out

    def test_a_marker_quoted_mid_sentence_in_a_comment_is_not_an_exemption(
        self, build_charts: Callable[..., Path]
    ) -> None:
        """The minimal form of the same defect, on a single comment line.

        Quoted *with* its ``#``, exactly as one writes it in prose — which is
        what made the substring search match.
        """
        root = build_charts(
            probe="""
            apiVersion: v2
            name: probe
            # the hatch is spelled `# chart-develop-version-ok: <reason>` on the version line
            version: 0.2.0
            """
        )
        assert _kinds(root) == ["chart_version_releasable"]

    def test_a_marker_behind_another_trailing_comment_is_not_an_exemption(
        self, build_charts: Callable[..., Path]
    ) -> None:
        """On the ``version:`` line the marker must BE the comment, not be in it."""
        root = build_charts(
            probe="""
            apiVersion: v2
            name: probe
            version: 0.2.0  # pinned by hand # chart-develop-version-ok: never published here
            """
        )
        assert _kinds(root) == ["chart_version_releasable"]

    def test_a_genuine_marker_line_inside_the_prose_block_still_exempts(
        self, build_charts: Callable[..., Path]
    ) -> None:
        """The hatch is anchored, not removed — the other direction of F-5.

        Same block, same prose, plus one line that actually opens with the
        marker. A "fix" that dropped the block form would go green on the four
        tests above and silently take the escape hatch away.
        """
        root = build_charts(
            probe=PROSE_EXPLAINING_THE_HATCH.replace(
                "version: 0.2.0",
                "# chart-develop-version-ok: vendored, never published from this repository\nversion: 0.2.0",
                1,
            )
        )
        assert _kinds(root) == []
        assert [finding.justification for finding in _findings(root)] == [
            "vendored, never published from this repository"
        ]

    def test_a_genuine_marker_on_the_version_line_still_exempts_under_the_prose(
        self, build_charts: Callable[..., Path]
    ) -> None:
        """The trailing form, with the explanatory block left in place above it."""
        root = build_charts(
            probe=PROSE_EXPLAINING_THE_HATCH.replace(
                "version: 0.2.0",
                "version: 0.2.0  # chart-develop-version-ok: vendored, never published here",
                1,
            )
        )
        assert _kinds(root) == []
        assert checker.main(["--helm-root", str(root)]) == checker.EXIT_OK

    def test_a_double_hash_comment_still_exempts(self, build_charts: Callable[..., Path]) -> None:
        """``##`` is a comment style, not a different marker."""
        root = build_charts(
            probe="""
            apiVersion: v2
            name: probe
            ## chart-develop-version-ok: vendored, never published from this repository
            version: 0.2.0
            """
        )
        assert _kinds(root) == []

    def test_the_displayed_marker_is_derived_from_the_matched_key(self) -> None:
        """The report shows one spelling and the matcher uses another — unless derived."""
        assert checker.JUSTIFICATION_MARKER.endswith(checker.JUSTIFICATION_KEY)
        assert checker.JUSTIFICATION_MARKER.startswith("#")


class TestProcessContract:
    """Exit codes and machine-readable output — what CI and pre-commit read."""

    def test_json_reports_both_buckets(
        self, build_charts: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A justified site stays visible; it is exempt, not invisible."""
        root = build_charts(
            broken=chart("0.2.0"),
            excused="""
            apiVersion: v2
            name: excused
            version: 0.4.0  # chart-develop-version-ok: never published from this repository
            """,
        )
        assert checker.main(["--helm-root", str(root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert payload["charts"] == 2
        assert [entry["kind"] for entry in payload["unjustified"]] == ["chart_version_releasable"]
        assert [entry["reason"] for entry in payload["justified"]] == ["never published from this repository"]

    def test_a_clean_tree_exits_zero_in_json_mode(
        self, build_charts: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The green path must be green in both output modes."""
        root = build_charts(kamerplanter=chart("0.3.0-dev"))
        assert checker.main(["--helm-root", str(root), "--json"]) == checker.EXIT_OK
        assert json.loads(capsys.readouterr().out)["unjustified"] == []

    def test_a_missing_helm_root_is_a_usage_error_not_a_pass(self, tmp_path: Path) -> None:
        """A renamed directory must not read as "no charts, all fine"."""
        assert checker.main(["--helm-root", str(tmp_path / "absent")]) == checker.EXIT_USAGE

    def test_an_empty_helm_root_is_a_usage_error_not_a_pass(self, tmp_path: Path) -> None:
        """Scanning nothing and reporting clean is the shape NFR-018 §2 forbids."""
        (tmp_path / "helm").mkdir()
        assert checker.main(["--helm-root", str(tmp_path / "helm")]) == checker.EXIT_USAGE

    def test_a_named_chart_that_does_not_exist_is_a_usage_error(self, tmp_path: Path) -> None:
        """``--chart <typo>`` must not silently check nothing and exit 0."""
        assert checker.main(["--chart", str(tmp_path / "nope" / "Chart.yaml")]) == checker.EXIT_USAGE

    def test_unparseable_yaml_is_a_usage_error_not_a_pass(self, build_charts: Callable[..., Path]) -> None:
        """A chart the checker cannot read has not been checked."""
        root = build_charts(kamerplanter="apiVersion: v2\nname: [unclosed\n")
        assert checker.main(["--helm-root", str(root)]) == checker.EXIT_USAGE

    def test_chart_and_helm_root_are_mutually_exclusive(self, build_charts: Callable[..., Path]) -> None:
        """Two scan definitions at once means one of them was silently ignored."""
        root = build_charts(kamerplanter=chart("0.3.0-dev"))
        with pytest.raises(SystemExit) as excinfo:
            checker.main(["--helm-root", str(root), "--chart", str(root / "kamerplanter" / "Chart.yaml")])
        assert excinfo.value.code == checker.EXIT_USAGE
