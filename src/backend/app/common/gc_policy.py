"""The process's garbage-collection policy: the start-up heap is frozen out of the collector (#2526).

A full (generation-2) collection walks every tracked container of the process. After start-up that is
some 300 000 objects - imported modules, the FastAPI app and its routes, pydantic schemas, seeded caches -
that live as long as the process and that no collection will ever free. Every few requests a request's
own allocations trigger such a collection; on ``GET /sites/{key}/plan`` of the "large" class it was most
of the gap between the median (~150 ms) and the p95 (~260 ms, GP-NFR-030: 300 ms) on a developer machine,
and the reason the shared CI runner, ~1.5x slower, could not certify the target.

``gc.freeze()`` moves everything alive at that moment into the permanent generation, which the collector
skips; collections then walk only what was allocated since. The cost is that a frozen object that later
becomes cyclic garbage is not reclaimed - acceptable for the start-up heap, which is not garbage by
construction. ``gc.collect()`` first, so nothing already unreachable is frozen with it.

Measured 2026-11-07, 40 runs of the large class: p95 262 ms default, 175 ms frozen, 158 ms with the
collector off.
"""

from __future__ import annotations

import gc

import structlog

logger = structlog.get_logger(__name__)


def freeze_startup_heap() -> int:
    """Collect, then freeze every object alive now out of future collections; the number frozen."""
    gc.collect()
    gc.freeze()
    frozen = gc.get_freeze_count()
    logger.info("gc.startup_heap_frozen", objects=frozen)
    return frozen
