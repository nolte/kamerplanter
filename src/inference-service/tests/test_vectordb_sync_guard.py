"""Drift guard: local vectordb infra must equal the shared kp_vectordb source.

Variant B of code-review AP-18c / INF-D1: the pgvector connection pool and
migration runner are maintained once under ``src/libs/kp_vectordb`` and copied
byte-for-byte into this service. If this test fails, do NOT edit the copy —
edit the source and run ``python src/libs/kp_vectordb/sync.py``.
"""

from pathlib import Path

import pytest

_SHARED_MODULES = ("config.py", "connection.py", "schema.py")
_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_DIR = _SERVICE_ROOT / "app" / "vectordb"
_SOURCE_DIR = _SERVICE_ROOT.parents[0] / "libs" / "kp_vectordb" / "kp_vectordb"


@pytest.mark.parametrize("module", _SHARED_MODULES)
def test_local_vectordb_matches_shared_source(module: str) -> None:
    if not _SOURCE_DIR.exists():
        pytest.skip("shared kp_vectordb source not present in this checkout")
    source = (_SOURCE_DIR / module).read_bytes()
    local = (_LOCAL_DIR / module).read_bytes()
    assert local == source, (
        f"{module} has drifted from src/libs/kp_vectordb; "
        "run `python src/libs/kp_vectordb/sync.py` (never edit the copy directly)."
    )
