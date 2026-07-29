"""Deterministic pick for per-user singleton documents (auto-create race guard).

Some collections hold at most one document per ``user_key`` (user preferences,
onboarding state). Their services auto-create the singleton on the first cold
read, which races under concurrent load: two simultaneous reads both find the
collection empty and both insert, minting duplicate singletons. The unique
index on ``user_key`` (bootstrap + migration ``v0031``) closes the race at the
storage layer, but legacy volumes may still carry duplicates until the dedup
migration runs. Until then, an unordered ``find_by_field`` scan would return the
duplicates in a non-deterministic order, so ``docs[0]`` would flap between
requests and preferences/state would appear to change randomly.

:func:`pick_singleton` makes the read deterministic: it always returns the
document with the lexicographically smallest ``_key`` and warns once so the
duplicate is visible in the logs until the migration removes it.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


def pick_singleton(docs: list[dict[str, Any]], *, collection: str, user_key: str) -> dict[str, Any]:
    """Return the canonical document from a per-user singleton scan.

    Precondition: ``docs`` is non-empty. When it holds more than one document
    (a legacy duplicate-singleton group), the one with the smallest ``_key`` is
    returned so every request converges on the same record, and a
    ``duplicate_singleton_docs`` warning is logged.
    """
    if len(docs) > 1:
        keys = sorted(str(doc.get("_key", "")) for doc in docs)
        logger.warning(
            "duplicate_singleton_docs",
            collection=collection,
            user_key=user_key,
            count=len(docs),
            keys=keys,
        )
        winner_key = keys[0]
        return next(doc for doc in docs if str(doc.get("_key", "")) == winner_key)
    return docs[0]
