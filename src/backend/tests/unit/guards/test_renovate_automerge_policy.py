"""NFR-009 §3.4 — every Renovate pull request is merged by Renovate once EVERY check is green.

**The decision this holds** (operator, 2026-09-24): Renovate pull requests merge
into ``develop`` on their own for every group and update type, majors
included, and "green" means every check run on the head commit — not only the
required contexts. The previous policy (exactly one rule with
``automerge: true``, three rules writing ``automerge: false`` out) is history in
``renovate.json5`` and in NFR-009.

**Why each assertion, and why at the level it sits:**

* ``automerge: true`` at the top level and in NO ``packageRules`` entry. A rule
  that sets ``automerge`` overrides the top level for its match; a single
  ``automerge: false`` left behind silently re-creates a manual-merge island.
  The old config had three — the red-first run of this file against it is the
  proof the check can fail.
* ``platformAutomerge: false``. With the default ``true`` GitHub's native
  auto-merge merges on the REQUIRED contexts only; Renovate's own merge reads
  every check run on the head (``getBranchStatus`` in Renovate's GitHub
  platform module), which is what "all checks green" means here.
* ``automergeType: 'pr'``, ``automergeStrategy: 'squash'`` (the repository
  allows squash only; Renovate stops automerging on an unsupported strategy),
  ``rebaseWhen: 'behind-base-branch'`` (Renovate keeps its own branches current
  under ``strict: true``; nobody ``update-branch``es a ``renovate/`` branch).
* ``ignoreTests`` unset or ``false`` — ``true`` would merge without waiting for
  any check.
* No ``automerge`` label and no ``branchPrefix``: the label would hand the pull
  request to the second merger (``automerge.yaml``, required checks only), and
  that workflow recognises Renovate by the default ``renovate/`` prefix.
* ``automerge.yaml`` skips ``renovate/`` heads and gives their runs a
  run-scoped concurrency group. Its per-PR ``cancel-in-progress`` group left a
  ``cancelled`` check run on 13 of the last 25 Renovate heads (2026-09-24), and
  Renovate treats ``cancelled`` as pending — it would never have merged them.

``renovate.json5`` is read through ``tests.support.renovate_config.load`` — a
parse of the file into the object Renovate reads, not a grep over its text, so
a key is judged by WHERE it sits. The workflow is read as YAML for the same
reason; its ``${{ }}`` expressions are GitHub's to evaluate and are asserted as
text, which is the residual this guard does not close.

Traces to NFR-009 §3.4 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.renovate_config import json5_to_json, load
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_CONFIG = _REPO_ROOT / "renovate.json5"
_AUTOMERGE_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "automerge.yaml"

_RENOVATE_HEAD = "startsWith(github.event.pull_request.head.ref, 'renovate/')"


def _config() -> dict[str, Any]:
    return load(_CONFIG.read_text(encoding="utf-8"))


def _rules() -> list[dict[str, Any]]:
    rules = _config().get("packageRules")
    assert isinstance(rules, list) and rules, (
        f"no packageRules parsed from {_CONFIG} — the reader broke, not the config; "
        "an empty list would make every per-rule assertion below vacuous"
    )
    return rules


def _workflow() -> dict[str, Any]:
    loaded = yaml.safe_load(_AUTOMERGE_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), f"{_AUTOMERGE_WORKFLOW} did not parse to a mapping"
    return loaded


class TestRenovateMergesEverythingItself:
    """The top-level keys that make Renovate the merger, for every update."""

    def test_automerge_is_on_at_the_top_level(self) -> None:
        assert _config().get("automerge") is True

    def test_no_package_rule_sets_automerge(self) -> None:
        offenders = [
            rule.get("groupName") or rule.get("description") or rule.get("matchPackageNames") or rule
            for rule in _rules()
            if "automerge" in rule
        ]
        assert not offenders, (
            "a packageRules entry sets `automerge`, overriding the top-level policy for its match "
            f"(NFR-009 §3.4): {offenders}"
        )

    def test_renovate_merges_instead_of_the_platform(self) -> None:
        assert _config().get("platformAutomerge") is False, (
            "platformAutomerge must be false: GitHub's native auto-merge waits for the REQUIRED "
            "contexts only, the policy is every check green"
        )

    def test_no_package_rule_sets_platform_automerge(self) -> None:
        assert not [rule for rule in _rules() if "platformAutomerge" in rule]

    def test_the_merge_goes_through_a_pull_request(self) -> None:
        assert _config().get("automergeType") == "pr"

    def test_the_merge_strategy_is_the_one_the_repository_allows(self) -> None:
        assert _config().get("automergeStrategy") == "squash"

    def test_renovate_keeps_its_own_branches_current(self) -> None:
        assert _config().get("rebaseWhen") == "behind-base-branch"
        assert not [rule for rule in _rules() if "rebaseWhen" in rule]

    def test_checks_are_never_ignored(self) -> None:
        config = _config()
        assert config.get("ignoreTests", False) is False
        assert not [rule for rule in _rules() if rule.get("ignoreTests")]

    def test_no_rule_hands_the_pull_request_to_the_label_merger(self) -> None:
        carriers = [_config(), *_rules()]
        labelled = [c for c in carriers for key in ("labels", "addLabels") if "automerge" in c.get(key, [])]
        assert not labelled, "the `automerge` label would make automerge.yaml a second merger"

    def test_the_branch_prefix_the_workflow_keys_on_is_renovates_default(self) -> None:
        assert "branchPrefix" not in _config(), (
            "automerge.yaml recognises Renovate pull requests by the default `renovate/` prefix"
        )


class TestTheLabelMergerStaysOutOfRenovatesWay:
    """``automerge.yaml`` neither merges nor leaves a ``cancelled`` run on a Renovate head."""

    def test_the_job_skips_renovate_branches(self) -> None:
        condition = str(_workflow()["jobs"]["automerge"].get("if", ""))
        assert f"!{_RENOVATE_HEAD}" in condition, f"jobs.automerge.if must exclude Renovate heads, found {condition!r}"

    def test_renovate_runs_are_never_cancelled_by_a_sibling(self) -> None:
        group = str(_workflow()["concurrency"]["group"])
        assert _RENOVATE_HEAD in group and "github.run_id" in group, (
            "a Renovate pull request's runs must each get their own concurrency group; a shared "
            f"cancel-in-progress group leaves `cancelled` check runs Renovate reads as pending: {group!r}"
        )
        renovate_branch = group.split(_RENOVATE_HEAD, 1)[1].split("||", 1)[0]
        assert "github.run_id" in renovate_branch, (
            f"github.run_id must be the key chosen FOR Renovate heads, not a later fallback: {group!r}"
        )


class TestTheReader:
    """The JSON5 reader returns the object, not a text-shaped approximation of it."""

    def test_a_key_inside_a_rule_is_not_read_as_top_level(self) -> None:
        text = "{\n  packageRules: [\n    {\n      automerge: false,\n    },\n  ],\n}\n"
        config = load(text)
        assert "automerge" not in config
        assert config["packageRules"] == [{"automerge": False}]

    def test_a_comment_naming_the_key_contributes_nothing(self) -> None:
        text = "{\n  // automerge: false,\n  automerge: true,\n}\n"
        assert load(text) == {"automerge": True}

    def test_slashes_inside_strings_survive(self) -> None:
        text = "{\n  a: 'https://x/y', b: '/^\\\\.github/x$/', // trailing\n}\n"
        assert load(text) == {"a": "https://x/y", "b": "/^\\.github/x$/"}

    def test_trailing_commas_are_dropped_even_before_a_comment(self) -> None:
        assert json.loads(json5_to_json("[1, // c\n]")) == [1]

    def test_the_real_config_parses_into_the_rules_it_has(self) -> None:
        groups = [rule.get("groupName") for rule in _rules()]
        assert "application dependencies" in groups and "uv toolchain" in groups
