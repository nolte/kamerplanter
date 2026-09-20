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
   intended. On a filter that decides whether a test suite runs, narrowing is the
   fail-open direction: fewer changes classified as relevant, fewer runs, a gate
   that goes green over work it never looked at. ``e2e-smoke.yml`` already
   documents the workaround — a second filter, ORed in the job condition — so
   the rule here costs nothing that is not already written down.

DELIBERATELY MATCHER-FREE. This says nothing about *which* paths a filter should
exclude; reimplementing picomatch here would mean the test reaches the rule over
a different code path than production does, which is the vacuity class this
repository has paid for repeatedly. Whether a concrete diff runs or skips a lane
is proven by running it — the counter-proofs in #1577's pull request — and this
file guards only the two structural properties that make such a run meaningful.

Traces to #1577 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found; this guard reads .github/ and cannot run without it")

_WORKFLOW_DIR = _REPO_ROOT / ".github" / "workflows"
_ACTIONS_DIR = _REPO_ROOT / ".github" / "actions"

#: Substring rather than the full ``dorny/paths-filter@<sha>`` spelling on
#: purpose. The repository pins actions by digest, so the version lives in a
#: trailing comment and never in the ``uses:`` value; and a fork, a re-published
#: copy or a mirror of the same action carries the same defect while failing an
#: equality test against the upstream owner. Name a spelling of the same thing
#: this misses and it belongs here: a composite action wrapping the filter is
#: why ``.github/actions/`` is swept alongside ``.github/workflows/``.
_PATHS_FILTER = "paths-filter@"

#: The value ``predicate-quantifier`` must carry. YAML reads ``every`` and
#: ``'every'`` as the same string, so both spellings satisfy this.
_EVERY = "every"


def _yaml_files() -> list[Path]:
    """Every workflow and composite-action definition in ``.github/``."""
    files = sorted(p for p in _WORKFLOW_DIR.glob("*.y*ml") if p.is_file())
    files += sorted(p for p in _ACTIONS_DIR.glob("*/action.y*ml") if p.is_file())
    assert files, f"no workflow files under {_WORKFLOW_DIR} — the sweep would be vacuously green"
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


def _paths_filter_steps() -> list[tuple[Path, dict[str, Any], dict[str, list[str]]]]:
    collected = []
    for path in _yaml_files():
        document = yaml.safe_load(path.read_text())
        for step in _steps(document):
            uses = step.get("uses")
            if not isinstance(uses, str) or _PATHS_FILTER not in uses:
                continue
            inputs = step.get("with") if isinstance(step.get("with"), dict) else {}
            collected.append((path, inputs, _filter_patterns(inputs.get("filters"))))
    return collected


@pytest.fixture(scope="module")
def paths_filter_steps() -> list[tuple[Path, dict[str, Any], dict[str, list[str]]]]:
    steps = _paths_filter_steps()
    assert steps, (
        "no dorny/paths-filter step found in .github/ — either the relevance "
        "filters were removed, or the sweep stopped recognising them. Both make "
        "every assertion below vacuously true, so this is a failure, not a pass."
    )
    return steps


def _deny_list_filters(
    steps: list[tuple[Path, dict[str, Any], dict[str, list[str]]]],
) -> list[tuple[Path, dict[str, Any], str, list[str]]]:
    """Filters carrying at least one negated pattern — the ones the rule is about."""
    return [
        (path, inputs, name, patterns)
        for path, inputs, filters in steps
        for name, patterns in filters.items()
        if any(pattern.startswith("!") for pattern in patterns)
    ]


def test_deny_list_filters_declare_the_every_quantifier(paths_filter_steps) -> None:
    """A negated pattern without ``predicate-quantifier: every`` subtracts nothing."""
    offenders = [
        f"{path.relative_to(_REPO_ROOT)}: filter {name!r} has exclusions but the step "
        f"declares predicate-quantifier={inputs.get('predicate-quantifier')!r}"
        for path, inputs, name, patterns in _deny_list_filters(paths_filter_steps)
        if str(inputs.get("predicate-quantifier", "")) != _EVERY
    ]
    assert not offenders, (
        "A dorny/paths-filter filter written as a deny list is permanently TRUE "
        "under the default quantifier `some`, because the leading '**' matches "
        "every file on its own and the '!' entries are ORed in rather than "
        "subtracted. Set `predicate-quantifier: 'every'` on the step:\n  " + "\n  ".join(offenders)
    )


def test_deny_list_filters_carry_no_positive_pattern_after_the_first(paths_filter_steps) -> None:
    """Under ``every``, a positive pattern added to a deny list narrows it silently."""
    offenders = []
    for path, _inputs, name, patterns in _deny_list_filters(paths_filter_steps):
        extra_positives = [pattern for pattern in patterns[1:] if not pattern.startswith("!")]
        if extra_positives:
            offenders.append(
                f"{path.relative_to(_REPO_ROOT)}: filter {name!r} mixes exclusions with "
                f"the positive pattern(s) {extra_positives} after its first entry"
            )
    assert not offenders, (
        "Under `predicate-quantifier: every` a file must match ALL of a filter's "
        "patterns, so a positive pattern added beside exclusions INTERSECTS "
        "rather than re-includes — the filter silently matches less than before "
        "and the lane it gates stops running on changes that do affect it. Give "
        "the addition its own filter and OR the two in the job condition, the "
        "way e2e-smoke.yml's `e2e_infra` filter does:\n  " + "\n  ".join(offenders)
    )
