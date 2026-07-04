#!/usr/bin/env python3
"""Sync the shared kp_vectordb infrastructure into the service copies.

Variant B of code-review AP-18c / INF-D1: the byte-identical pgvector
connection pool + migration runner live once here (source of truth) and are
copied verbatim into each service's ``app/vectordb/`` package. The Docker build
contexts stay per-service (unchanged, low risk); this script deduplicates the
*maintenance* and a CI guard (``test_vectordb_sync_guard.py`` in each service)
fails the build if a copy ever drifts from the source.

Usage::

    python src/libs/kp_vectordb/sync.py          # write the copies
    python src/libs/kp_vectordb/sync.py --check   # verify, non-zero exit on drift
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Modules that are byte-identical across the shared package and every service
# copy. Everything else (repositories, __init__, migrations/) stays per-service.
SHARED_MODULES = ("config.py", "connection.py", "schema.py")

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_DIR = _REPO_ROOT / "src" / "libs" / "kp_vectordb" / "kp_vectordb"
_TARGET_DIRS = (
    _REPO_ROOT / "src" / "knowledge-service" / "app" / "vectordb",
    _REPO_ROOT / "src" / "inference-service" / "app" / "vectordb",
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
        help="verify the copies are in sync; exit non-zero on drift instead of writing",
    )
    args = parser.parse_args()

    if args.check:
        drift = check()
        if drift:
            print("kp_vectordb copies are OUT OF SYNC:")
            for line in drift:
                print(f"  - {line}")
            print("Run: python src/libs/kp_vectordb/sync.py")
            return 1
        print("kp_vectordb copies are in sync.")
        return 0

    changed = write()
    if changed:
        print("Updated kp_vectordb copies:")
        for line in changed:
            print(f"  - {line}")
    else:
        print("kp_vectordb copies already in sync — nothing to do.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
