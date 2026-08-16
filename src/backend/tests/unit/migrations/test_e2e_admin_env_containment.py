"""`E2E_PLATFORM_ADMIN_*` must exist in exactly one file (#1155).

The seed these variables drive creates an account with full platform-admin
rights. Its module docstring argues that two gates make that acceptable, and
`test_seed_e2e_platform_admin.py` proves the gates hold. This file guards the
third thing, which neither of those can see: **where the variables are allowed
to appear at all.**

The realistic accident is not someone deliberately provisioning an admin. It is
a Helm values file, a deployment manifest or a second compose file that gets
these keys by being copied from the one place they legitimately live. The
`cookie_secure` gate would still refuse — but a configuration that carries an
admin credential around is worth catching before it depends on a runtime check
nobody remembers.

Scoped to configuration and deployment files. Documentation and tests may name
the variables freely; explaining a mechanism is not configuring it.
"""

from __future__ import annotations

import pathlib
import re

import pytest

# tests/unit/migrations/<file> → tests → unit is [1], tests [2], backend [3],
# src [4], repository root [5].
_ROOT = pathlib.Path(__file__).resolve().parents[5]

#: The one file that may set them, relative to the repository root.
_ALLOWED = "docker-compose.e2e.yml"

#: Where a stray copy would actually be dangerous: anything that configures a
#: running deployment. Globs rather than a full-tree walk, so the guard says
#: what it covers instead of quietly depending on what happens to be on disk.
_CONFIG_GLOBS = (
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "helm/**/*.yaml",
    "helm/**/*.yml",
    "k8s/**/*.yaml",
    "deploy/**/*.yaml",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "src/backend/.env*",
    ".env*",
)

_VAR = re.compile(r"E2E_PLATFORM_ADMIN_(EMAIL|PASSWORD)")


def _config_files() -> list[pathlib.Path]:
    seen: dict[pathlib.Path, None] = {}
    for glob in _CONFIG_GLOBS:
        for path in _ROOT.glob(glob):
            if path.is_file():
                seen[path] = None
    return sorted(seen)


def test_the_scan_reaches_the_file_that_is_allowed_to_set_them() -> None:
    """Loud when it finds nothing.

    Every assertion below is a no-op over an empty file list — a moved compose
    file or a changed repository root would leave this guard reporting green
    while looking at nothing at all.
    """
    files = _config_files()
    assert files, f"no configuration files matched under {_ROOT}"

    allowed = _ROOT / _ALLOWED
    assert allowed in files, f"{_ALLOWED} is not in the scanned set — the guard cannot be trusted"
    assert _VAR.search(allowed.read_text("utf-8")), (
        f"{_ALLOWED} no longer sets E2E_PLATFORM_ADMIN_*. Either the E2E admin seed was "
        "removed — in which case delete this guard and the seed together — or the "
        "variables moved somewhere this guard does not look."
    )


@pytest.mark.parametrize("path", _config_files(), ids=lambda p: str(p.relative_to(_ROOT)))
def test_no_other_configuration_file_sets_the_e2e_admin_credentials(path: pathlib.Path) -> None:
    """One file, one purpose, one blast radius."""
    relative = path.relative_to(_ROOT).as_posix()
    if relative == _ALLOWED:
        pytest.skip("the file that is allowed to set them")

    hits = sorted({m.group(0) for m in _VAR.finditer(path.read_text("utf-8"))})

    assert hits == [], (
        f"{relative} sets {hits}. These variables seed an account with full "
        f"platform-admin rights and belong in {_ALLOWED} alone.\n\n"
        "The seed still refuses unless `cookie_secure` is off, so this is not "
        "automatically an exploit — but a deployment file carrying an admin "
        "credential should not be relying on a runtime check to stay harmless."
    )
