"""Every label declared in ``.github/settings.yml`` fits the GitHub labels API (#1632).

The Settings app syncs the ``labels:`` block through the REST labels endpoint,
which rejects a description longer than 100 characters. The rejection lands in
the app's log only: the declaration looks merged, the label never appears. The
``security-scan`` label sat undeclared-in-effect for that reason with a
193-character description.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from tests.support.repo_scripts import find_repo_root

_SETTINGS = find_repo_root(Path(__file__).resolve()) / ".github" / "settings.yml"

# Limits of POST /repos/{owner}/{repo}/labels, measured 2026-09-23:
# `gh label create probe --description <101 chars>` →
# "description is too long (maximum is 100 characters)".
_MAX_DESCRIPTION = 100
_MAX_NAME = 50


def _declared_labels() -> list[dict[str, str]]:
    settings = yaml.safe_load(_SETTINGS.read_text(encoding="utf-8"))
    return list(settings.get("labels") or [])


def test_the_settings_file_declares_labels() -> None:
    # Anti-vacuity: an empty or renamed block would make the check below pass on nothing.
    assert _declared_labels(), f"{_SETTINGS} declares no labels; the size check below would pass vacuously"


def test_every_declared_label_fits_the_labels_api() -> None:
    too_long = [
        f"{label['name']}: description {len(label.get('description', ''))} > {_MAX_DESCRIPTION}"
        for label in _declared_labels()
        if len(label.get("description", "")) > _MAX_DESCRIPTION
    ] + [
        f"{label['name']}: name {len(label['name'])} > {_MAX_NAME}"
        for label in _declared_labels()
        if len(label["name"]) > _MAX_NAME
    ]
    assert not too_long, "the Settings app cannot create these labels: " + "; ".join(too_long)
