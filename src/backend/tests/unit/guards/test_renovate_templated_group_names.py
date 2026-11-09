"""A Renovate rule whose ``groupName`` is a template carries a ``groupSlug`` template too.

**The defect this holds** (PR #2555, #2627, #2810): the ArangoDB digest bump of
the service container in ``backend-guards.yml`` opened the branch
``renovate/if-(equals-updatetype-"major")depname-imageelsethird-party-imagesif``
instead of joining ``renovate/third-party-images`` — the CI lane and the
compose stack then pinned different ArangoDB digests (#1432).

**Why:** Renovate compiles ``groupName`` only in its branch-name step. When an
earlier rule already set a ``groupSlug`` for the dependency, Renovate's package
rule merge (``lib/util/package-rules/index.ts``) derives the new rule's slug by
slugifying the RAW ``groupName`` — template braces stripped, never compiled.
The shared preset ``gh-plumbing//renovate-configs/common`` sets
``groupSlug: 'digests'`` on github-actions digest updates, and the github-actions
manager extracts workflow service images, so exactly those updates hit it. An
explicit ``groupSlug`` is compiled (``branch-name.ts``), so a templated
``groupName`` needs a templated ``groupSlug`` beside it.

Traces to NFR-009 §3.4 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.support.renovate_config import load
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)


def _rules_missing_a_slug(config: dict[str, Any]) -> list[str]:
    return [
        rule["groupName"]
        for rule in config.get("packageRules", [])
        if "{{" in str(rule.get("groupName") or "") and "{{" not in str(rule.get("groupSlug") or "")
    ]


def test_every_templated_group_name_has_a_templated_group_slug() -> None:
    config = load((_REPO_ROOT / "renovate.json5").read_text(encoding="utf-8"))
    assert _rules_missing_a_slug(config) == []


def test_the_check_reports_a_templated_name_without_a_slug() -> None:
    config = {"packageRules": [{"groupName": "{{depName}} image"}, {"groupName": "plain"}]}
    assert _rules_missing_a_slug(config) == ["{{depName}} image"]
