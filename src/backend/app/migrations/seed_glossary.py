"""REQ-035 §4.2 — seed the curated glossary term skeleton.

Loads ``seed_data/glossary_terms.yaml`` into the ``glossary_terms`` collection
(idempotent upsert by ``_key``). Glossary terms are global reference data, not
tenant-scoped (§6). Runs at backend start via the seed registry, mirroring the
other reference-data seeds.

The RAG answer text is *not* seeded — it is produced on demand by the Knowledge
Service and cached in ``glossary_term_cache`` (§4.1). This seed only maintains
the editorial metadata + fallback text.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from app.common.dependencies import get_db
from app.data_access.arango import collections as col
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

#: Editorial fields that are refreshed on every seed run (idempotent upsert). The
#: ``created_at`` timestamp is preserved on update; ``updated_at`` is bumped.
_MANAGED_FIELDS = (
    "slug",
    "labels",
    "long_labels",
    "aliases",
    "category",
    "default_expertise_level",
    "applicable_phases",
    "related_term_slugs",
    "fallback_text",
    "rag_query_template",
    "is_active",
)


def _upsert_term(collection: Any, raw: dict[str, Any], now: str) -> bool:
    """Insert or update one term by ``_key``. Returns True when data changed."""
    key = raw["_key"]
    payload = {field: raw[field] for field in _MANAGED_FIELDS if field in raw}
    payload.setdefault("is_active", True)

    existing = collection.get(key)
    if existing is None:
        collection.insert({"_key": key, **payload, "created_at": now, "updated_at": now})
        return True

    # Only write when a managed field actually differs, so re-runs stay no-ops.
    if all(existing.get(field) == value for field, value in payload.items()):
        return False
    collection.update({"_key": key, **payload, "updated_at": now})
    return True


def run_seed_glossary() -> None:
    """Seed / refresh the curated glossary terms (idempotent)."""
    db = get_db()
    data = load_yaml("glossary_terms.yaml")
    terms: list[dict[str, Any]] = data.get("glossary_terms", [])
    collection = db.collection(col.GLOSSARY_TERMS)
    now = datetime.now(UTC).isoformat()

    changed = sum(1 for raw in terms if _upsert_term(collection, raw, now))
    logger.info("seed_glossary_complete", total=len(terms), changed=changed)


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_glossary()
