"""A deny-list ``dorny/paths-filter`` needs ``predicate-quantifier: every`` (#1577).

THE DEFECT THIS IS WRITTEN AGAINST, PAID FOR ONCE ALREADY.

``dorny/paths-filter`` ORs a filter's patterns together by default
(``predicate-quantifier: some``). Under that default a filter written as a DENY
LIST — a leading ``'**'`` followed by ``'!…'`` exclusions — is permanently true:
``'**'`` matches every file on its own, and the negations subtract nothing
because the OR is already satisfied. The filter reads like a selection and is
not one. PR #795 changed only ``.github/settings.yml`` and still ran the full
E2E smoke suite for exactly this reason; ``e2e-smoke.yml`` carries the story in
a comment beside the option.

Two properties keep such a filter honest, and this file is the absence check for
both, because a comment is not a mechanism (NFR-018 §1):

1. **The quantifier is declared.** Any ``paths-filter`` step with a negated
   pattern anywhere in its filter set must set ``predicate-quantifier: 'every'``.
   Deleting the line is valid YAML, runs, and is wrong only later.

2. **A deny list stays a deny list.** Under ``every`` a file must satisfy ALL of
   a filter's patterns, so adding a *positive* pattern to a deny-list filter
   narrows it by intersection rather than widening it — ``'**'`` AND ``'src/**'``
   AND every negation is a strictly smaller set than the author of the new line
   intended.

THE SECOND RULE IS NOT A STYLE RULE. It is what stops the FIRST rule's remedy
from becoming a gate switch, and that is the sharpest thing in this file.
``backend-guards.yml``'s ``integration`` filter is a pure ALLOW list — four
positive patterns, no negation, quantifier deliberately absent because ``some``
is the intended reading there. Add one exclusion to it and rule 1 fires and
demands ``every``. Obey that message literally and ``every`` is applied to a list
with no leading ``'**'``: a file would have to be under ``src/backend/**`` AND be
``Taskfile.yaml`` AND be this workflow, which nothing is. The filter becomes
permanently FALSE, and the REQUIRED ``Integration tests (ArangoDB)`` context
skips green on every pull request in the repository. That is the worst fail-open
this repository can reach, and it would be the literal execution of this file's
own error message. Rule 2 rejects the mixed list first, so the message a reader
gets is "split it into two filters and OR them in the job condition", which is
what ``e2e-smoke.yml``'s ``e2e_infra`` filter already demonstrates.

DELIBERATELY MATCHER-FREE. This says nothing about *which* paths a filter should
exclude; reimplementing picomatch here would mean the test reaches the rule over
a different code path than production does, which is the vacuity class this
repository has paid for repeatedly. Whether a concrete diff runs or skips a lane
is proven by running it — the counter-proofs in #1577's pull request — and this
file guards only the structural properties that make such a run meaningful.

WHY THE SWEEP IS PROVEN TO GO RED, AND PROVEN NOT TO BE VACUOUS.
``TestTheSweepCanGoRed`` plants a violating workflow tree per rule and asserts
the checker reports it, each paired with the compliant variant so the fix the
message asks for is proven to clear the check rather than assumed to.
``TestTheRealTreeIsActuallyMeasured`` closes the other hole: "the sweep found
steps" is not "the sweep parsed anything". If the ``filters:`` spelling ever
changes — the input renamed, the block scalar replaced, the patterns moved into
a composite action's own input — the step list stays non-empty, every filter
parses to ``{}``, no filter has a negation, both rules find zero offenders and
both tests pass while measuring nothing.

Traces to #1577 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, NamedTuple

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found; this guard reads .github/ and cannot run without it")

_DOT_GITHUB = _REPO_ROOT / ".github"

#: Substring rather than the full ``dorny/paths-filter@<sha>`` spelling on
#: purpose. The repository pins actions by digest, so the version lives in a
#: trailing comment and never in the ``uses:`` value; and a fork, a re-published
#: copy or a mirror of the same action carries the same defect while failing an
#: equality test against the upstream owner. Name a spelling of the same thing
#: this misses and it belongs here: a composite action wrapping the filter is
#: why ``actions/`` is swept alongside ``workflows/``, and why that sweep uses
#: ``rglob`` — a composite action nested a directory deeper is still one.
_PATHS_FILTER = "paths-filter@"

#: The value ``predicate-quantifier`` must carry. YAML reads ``every`` and
#: ``'every'`` as the same string, so both spellings satisfy this.
_EVERY = "every"

#: A digest-shaped placeholder for the planted trees below. Never resolved — the
#: sweep matches on the action's name, and a real digest here would age.
_FAKE_SHA = "0" * 40


class Step(NamedTuple):
    """One ``paths-filter`` step: where it lives, its inputs, its parsed filters."""

    path: Path
    inputs: dict[str, Any]
    filters: dict[str, list[str]]


def _yaml_files(dot_github: Path) -> list[Path]:
    """Every workflow and composite-action definition under *dot_github*."""
    files = sorted(p for p in (dot_github / "workflows").glob("*.y*ml") if p.is_file())
    files += sorted(p for p in (dot_github / "actions").rglob("action.y*ml") if p.is_file())
    return files


def _steps(document: Any) -> list[dict[str, Any]]:
    """Every step of every job, plus a composite action's own ``runs.steps``."""
    found: list[dict[str, Any]] = []
    if not isinstance(document, dict):
        return found
    jobs = document.get("jobs")
    if isinstance(jobs, dict):
        for job in jobs.values():
            steps = job.get("steps") if isinstance(job, dict) else None
            if isinstance(steps, list):
                found += [step for step in steps if isinstance(step, dict)]
    runs = document.get("runs")
    if isinstance(runs, dict) and isinstance(runs.get("steps"), list):
        found += [step for step in runs["steps"] if isinstance(step, dict)]
    return found


def _filter_patterns(raw: Any) -> dict[str, list[str]]:
    """``filter name -> its patterns``, for every spelling the action accepts.

    The action takes the ``filters`` input either as a YAML document in a block
    scalar (the spelling used here) or as an inline mapping, and each filter's
    value may be a single pattern, a list of patterns, or a list of objects
    carrying the pattern under ``path``. All four are normalised, so a rewrite
    into another one of them cannot walk out of this guard's sight.
    """
    document = yaml.safe_load(raw) if isinstance(raw, str) else raw
    if not isinstance(document, dict):
        return {}
    normalised: dict[str, list[str]] = {}
    for name, value in document.items():
        entries = value if isinstance(value, list) else [value]
        patterns: list[str] = []
        for entry in entries:
            if isinstance(entry, dict):
                entry = entry.get("path")
            if isinstance(entry, str):
                patterns.append(entry)
        normalised[str(name)] = patterns
    return normalised


def collect(dot_github: Path) -> list[Step]:
    """Every ``dorny/paths-filter`` step under *dot_github*, with its filters parsed."""
    collected: list[Step] = []
    for path in _yaml_files(dot_github):
        document = yaml.safe_load(path.read_text())
        for step in _steps(document):
            uses = step.get("uses")
            if not isinstance(uses, str) or _PATHS_FILTER not in uses:
                continue
            inputs = step.get("with") if isinstance(step.get("with"), dict) else {}
            collected.append(Step(path, inputs, _filter_patterns(inputs.get("filters"))))
    return collected


def deny_list_filters(steps: list[Step]) -> list[tuple[Step, str, list[str]]]:
    """Filters carrying at least one negated pattern — the ones the rules are about."""
    return [
        (step, name, patterns)
        for step in steps
        for name, patterns in step.filters.items()
        if any(pattern.startswith("!") for pattern in patterns)
    ]


def missing_quantifier(steps: list[Step]) -> list[str]:
    """Deny-list filters whose step does not declare ``predicate-quantifier: every``."""
    return [
        f"{step.path.name}: filter {name!r} has exclusions but the step declares "
        f"predicate-quantifier={step.inputs.get('predicate-quantifier')!r}"
        for step, name, _patterns in deny_list_filters(steps)
        if str(step.inputs.get("predicate-quantifier", "")) != _EVERY
    ]


def mixed_deny_list(steps: list[Step]) -> list[str]:
    """Deny-list filters carrying a positive pattern after their first entry."""
    offenders = []
    for step, name, patterns in deny_list_filters(steps):
        extra_positives = [pattern for pattern in patterns[1:] if not pattern.startswith("!")]
        if extra_positives:
            offenders.append(
                f"{step.path.name}: filter {name!r} mixes exclusions with the positive "
                f"pattern(s) {extra_positives} after its first entry"
            )
    return offenders


_QUANTIFIER_REMEDY = (
    "A dorny/paths-filter filter written as a deny list is permanently TRUE under the "
    "default quantifier `some`, because the leading '**' matches every file on its own "
    "and the '!' entries are ORed in rather than subtracted. Set "
    "`predicate-quantifier: 'every'` on the step"
)

_MIXED_REMEDY = (
    "Under `predicate-quantifier: every` a file must match ALL of a filter's patterns, "
    "so a positive pattern added beside exclusions INTERSECTS rather than re-includes — "
    "the filter silently matches less than before and the lane it gates stops running on "
    "changes that do affect it. Give the addition its own filter and OR the two in the "
    "job condition, the way e2e-smoke.yml's `e2e_infra` filter does"
)


@pytest.fixture(scope="module")
def real_steps() -> list[Step]:
    steps = collect(_DOT_GITHUB)
    assert steps, (
        "no dorny/paths-filter step found in .github/ — either the relevance "
        "filters were removed, or the sweep stopped recognising them. Both make "
        "every assertion below vacuously true, so this is a failure, not a pass."
    )
    return steps


class TestTheRealTree:
    """The two rules, over this repository's own ``.github/``."""

    def test_deny_list_filters_declare_the_every_quantifier(self, real_steps: list[Step]) -> None:
        offenders = missing_quantifier(real_steps)
        assert not offenders, _QUANTIFIER_REMEDY + ":\n  " + "\n  ".join(offenders)

    def test_deny_list_filters_carry_no_positive_pattern_after_the_first(self, real_steps: list[Step]) -> None:
        offenders = mixed_deny_list(real_steps)
        assert not offenders, _MIXED_REMEDY + ":\n  " + "\n  ".join(offenders)


class TestTheRealTreeIsActuallyMeasured:
    """ "The sweep found steps" is not "the sweep parsed anything"."""

    def test_every_swept_step_yields_at_least_one_pattern(self, real_steps: list[Step]) -> None:
        """A step whose filters parse to nothing satisfies both rules vacuously.

        This is the hole a ``filters``-spelling change would open: rename the
        input, replace the block scalar, move the patterns into a composite
        action's own input, and the step list stays non-empty while every filter
        is ``{}``. No filter then has a negation, ``deny_list_filters`` returns
        ``[]``, and both rules above report zero offenders over a sweep that
        measured nothing.
        """
        silent = [
            f"{step.path.name}: a paths-filter step whose `filters:` parsed to "
            f"{step.filters!r} (inputs present: {sorted(step.inputs)})"
            for step in real_steps
            if not any(step.filters.values())
        ]
        assert not silent, (
            "A dorny/paths-filter step was found but no pattern could be read out of it. "
            "Either the step really carries no filter, or `_filter_patterns` no longer "
            "understands the spelling in use — and in the second case every other "
            "assertion in this file is vacuously green. Teach `_filter_patterns` the new "
            "spelling:\n  " + "\n  ".join(silent)
        )

    def test_the_real_tree_has_at_least_one_deny_list_to_measure(self, real_steps: list[Step]) -> None:
        """Rule 1 is about deny lists; with none present it asserts over an empty set."""
        assert deny_list_filters(real_steps), (
            "no filter in .github/ carries a negated pattern, so "
            "test_deny_list_filters_declare_the_every_quantifier asserts over an empty "
            "population. If the deny-list filters were genuinely retired, retire this "
            "file with them rather than leaving a green check that measures nothing "
            "(NFR-018 §1)."
        )


def _plant(dot_github: Path, name: str, body: str, *, subdir: str = "workflows") -> None:
    """Write a workflow (or composite action) into a constructed ``.github/`` tree."""
    target = dot_github / subdir / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(body).lstrip())


def _workflow(*, quantifier: str | None, patterns: list[str]) -> str:
    quantifier_line = f"          predicate-quantifier: '{quantifier}'\n" if quantifier else ""
    pattern_lines = "".join(f"              - '{pattern}'\n" for pattern in patterns)
    return (
        "name: planted\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  changes:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - uses: dorny/paths-filter@{_FAKE_SHA} # v4.0.3\n"
        "        with:\n" + quantifier_line + "          filters: |\n"
        "            runtime:\n" + pattern_lines
    )


class TestTheSweepCanGoRed:
    """Each rule is planted against, and paired with the variant that clears it.

    A constructed ``.github/`` rather than a mutation of the real one: a test
    that edits the tree it runs in cannot be run twice and cannot run beside its
    siblings. The production predicates — ``collect``, ``missing_quantifier``,
    ``mixed_deny_list`` — are the ones called here, so the planted cases reach
    the rule over the same code path ``TestTheRealTree`` does.
    """

    @pytest.fixture
    def tree(self, tmp_path: Path) -> Path:
        return tmp_path / ".github"

    def test_a_deny_list_without_the_quantifier_is_reported(self, tree: Path) -> None:
        _plant(tree, "offender.yml", _workflow(quantifier=None, patterns=["**", "!docs/**"]))
        steps = collect(tree)
        assert len(steps) == 1, "the planted workflow was not swept — the fixture, not the rule, is broken"
        assert missing_quantifier(steps) == [
            "offender.yml: filter 'runtime' has exclusions but the step declares predicate-quantifier=None"
        ]

    def test_the_same_deny_list_with_the_quantifier_is_not(self, tree: Path) -> None:
        _plant(tree, "compliant.yml", _workflow(quantifier="every", patterns=["**", "!docs/**"]))
        assert missing_quantifier(collect(tree)) == []

    def test_a_positive_pattern_beside_exclusions_is_reported(self, tree: Path) -> None:
        _plant(tree, "offender.yml", _workflow(quantifier="every", patterns=["**", "!docs/**", "src/**"]))
        assert mixed_deny_list(collect(tree)) == [
            "offender.yml: filter 'runtime' mixes exclusions with the positive pattern(s) "
            "['src/**'] after its first entry"
        ]

    def test_the_same_list_without_that_pattern_is_not(self, tree: Path) -> None:
        _plant(tree, "compliant.yml", _workflow(quantifier="every", patterns=["**", "!docs/**"]))
        assert mixed_deny_list(collect(tree)) == []

    def test_a_pure_allow_list_is_left_alone_by_both_rules(self, tree: Path) -> None:
        """The ``backend-guards.yml`` shape: positive patterns only, no quantifier.

        Neither rule may fire here. If rule 1 did, its own remedy would apply
        ``every`` to a list with no leading ``'**'`` and make the filter
        permanently false — the gate-switch path in this file's header.
        """
        _plant(tree, "allow.yml", _workflow(quantifier=None, patterns=["src/backend/**", "Taskfile.yaml"]))
        steps = collect(tree)
        assert len(steps) == 1
        assert missing_quantifier(steps) == []
        assert mixed_deny_list(steps) == []

    def test_a_nested_composite_action_is_swept(self, tree: Path) -> None:
        """``actions/`` is walked with ``rglob``, not one level of ``glob``."""
        _plant(
            tree,
            "action.yml",
            "name: planted\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n"
            f"    - uses: dorny/paths-filter@{_FAKE_SHA} # v4.0.3\n"
            "      with:\n"
            "        filters: |\n"
            "          runtime:\n"
            "            - '**'\n"
            "            - '!docs/**'\n",
            subdir="actions/outer/inner",
        )
        steps = collect(tree)
        assert len(steps) == 1, "a composite action nested two levels deep was not swept"
        assert missing_quantifier(steps) == [
            "action.yml: filter 'runtime' has exclusions but the step declares predicate-quantifier=None"
        ]

    def test_a_step_whose_filters_cannot_be_parsed_is_reported_as_silent(self, tree: Path) -> None:
        """The anti-vacuity rule, planted: the step is found, no pattern is read.

        This is the spelling change ``TestTheRealTreeIsActuallyMeasured`` exists
        for — here the ``filters`` input has been renamed, which is a change a
        future action version could plausibly make. Both rules stay silent, which
        is precisely why silence is not enough on its own.
        """
        _plant(
            tree,
            "renamed-input.yml",
            "name: planted\n"
            "on:\n"
            "  pull_request:\n"
            "jobs:\n"
            "  changes:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            f"      - uses: dorny/paths-filter@{_FAKE_SHA} # v4.0.3\n"
            "        with:\n"
            "          patterns: |\n"
            "            runtime:\n"
            "              - '**'\n"
            "              - '!docs/**'\n",
        )
        steps = collect(tree)
        assert len(steps) == 1, "the step must still be FOUND — that is what makes the hole invisible"
        assert missing_quantifier(steps) == [], "and both rules must be silent, which is the defect"
        assert mixed_deny_list(steps) == []
        assert [step for step in steps if not any(step.filters.values())], (
            "the silent-step detector missed a step whose filters parsed to nothing"
        )
