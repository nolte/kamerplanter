"""Every branch entry in ``.github/settings.yml`` names all four protection keys (#3042).

GitHub's "Update branch protection" endpoint requires ``required_status_checks``,
``enforce_admins``, ``required_pull_request_reviews`` and ``restrictions`` in one
request. The Probot Settings App sends the ``protection`` mapping as declared, so
an entry that leaves one key out is rejected as a whole, and the App reports
nothing: the labels and repository settings of the same sync still apply, and
the protection that was live before simply stays.

Until nolte/gh-plumbing#496 the shared commons this file extends supplied the
missing key through a branch entry of their own. They declare none any more, so
this file has to be complete by itself. A key whose value is ``null`` counts as
present; that is how "no requirement" is spelled for this endpoint.
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

_REQUIRED_KEYS = frozenset(
    {"required_status_checks", "enforce_admins", "required_pull_request_reviews", "restrictions"}
)


def _branch_entries() -> list[dict[str, Any]]:
    settings = yaml.safe_load((_REPO_ROOT / ".github" / "settings.yml").read_text(encoding="utf-8"))
    return settings.get("branches") or []


def test_settings_declare_a_protected_branch() -> None:
    """The guard below would pass on an empty list, so the list is pinned first."""
    assert [entry["name"] for entry in _branch_entries() if entry.get("protection")] == ["develop"]


@pytest.mark.parametrize("entry", _branch_entries(), ids=lambda entry: entry["name"])
def test_protection_names_every_key_the_api_requires(entry: dict[str, Any]) -> None:
    protection = entry.get("protection")
    if protection is None:
        pytest.skip("entry removes protection; the endpoint takes no body then")
    missing = sorted(_REQUIRED_KEYS - protection.keys())
    assert not missing, (
        f"branch {entry['name']!r} in .github/settings.yml lacks {missing}; GitHub rejects the "
        "whole protection update without them and the Settings App does not report it. "
        "Write the key with `null` when no requirement is meant."
    )
