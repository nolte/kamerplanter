#!/usr/bin/env python3
"""Sync the shared kp_errortracking module into the service copies.

Same shape as ``src/libs/kp_vectordb/sync.py``: the module lives once here
(source of truth) and is copied verbatim into each service's
``app/observability/`` package, because the three Python services are separate
Docker build contexts with their own dependency sets.

The stake is higher than for the vectordb copies: the copied module carries the
PII-scrubbing rules, and a service whose copy has drifted scrubs less than its
siblings while looking identical from the outside. A per-service guard test
(``test_error_tracking_sync_guard.py``) fails the build on any drift.

Usage::

    python src/libs/kp_errortracking/sync.py           # write the copies
    python src/libs/kp_errortracking/sync.py --check   # verify, non-zero exit on drift
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Only the module itself is shared; each service keeps its own ``__init__.py``
# so its package namespace stays its own.
SHARED_MODULES = ("error_tracking.py",)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_DIR = _REPO_ROOT / "src" / "libs" / "kp_errortracking" / "kp_errortracking"
_TARGET_DIRS = (
    _REPO_ROOT / "src" / "backend" / "app" / "observability",
    _REPO_ROOT / "src" / "knowledge-service" / "app" / "observability",
    _REPO_ROOT / "src" / "inference-service" / "app" / "observability",
)


def _diverging(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return source.read_bytes() != target.read_bytes()


def check() -> list[str]:
    """Return a list of human-readable drift descriptions (empty == in sync)."""
    drift: list[str] = []
    for target_dir in _TARGET_DIRS:
        for module in SHARED_MODULES:
            source = _SOURCE_DIR / module
            target = target_dir / module
            if _diverging(source, target):
                drift.append(f"{target.relative_to(_REPO_ROOT)} differs from source {module}")
    return drift


def write() -> list[str]:
    """Copy the shared modules into every service. Returns the changed paths."""
    changed: list[str] = []
    for target_dir in _TARGET_DIRS:
        target_dir.mkdir(parents=True, exist_ok=True)
        for module in SHARED_MODULES:
            source = _SOURCE_DIR / module
            target = target_dir / module
            if _diverging(source, target):
                target.write_bytes(source.read_bytes())
                changed.append(str(target.relative_to(_REPO_ROOT)))
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the copies instead of writing them (CI guard)",
    )
    args = parser.parse_args()

    if args.check:
        drift = check()
        if drift:
            print("kp_errortracking copies have drifted:", file=sys.stderr)
            for entry in drift:
                print(f"  - {entry}", file=sys.stderr)
            print(
                "Edit src/libs/kp_errortracking/kp_errortracking/ and run `python src/libs/kp_errortracking/sync.py`.",
                file=sys.stderr,
            )
            return 1
        print("kp_errortracking copies are in sync.")
        return 0

    changed = write()
    if changed:
        for entry in changed:
            print(f"updated {entry}")
    else:
        print("kp_errortracking copies were already in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
