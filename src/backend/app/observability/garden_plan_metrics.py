"""Prometheus metrics of the garden plan (REQ-053 GP-NFR-061, NFR-007).

Registered on the API process's own registry (``app.observability.metrics.REGISTRY``), so they
are served by the same listener as the HTTP metrics and nowhere else.

**What is never a label.** A tenant, a site or a person: the series set would grow with the
installation and publish it to anyone who can scrape. ``size`` is a bucket of the plan's
object count (small / medium / large, §25.1), not the count itself.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from app.observability.metrics import REGISTRY

#: §25.1 size classes by locations + garden objects: "groß" is the 500-object quota.
SIZE_SMALL_MAX = 50
SIZE_MEDIUM_MAX = 200

GARDEN_PLAN_BATCH_DURATION = Histogram(
    "garden_plan_batch_duration_seconds",
    "Duration of an applied garden-plan batch, validation and transaction (GP-NFR-061).",
    registry=REGISTRY,
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
GARDEN_PLAN_CONFLICTS = Counter(
    "garden_plan_conflicts_total",
    "Garden-plan batches refused with plan.revision_conflict (GP-NFR-061).",
    registry=REGISTRY,
)
GARDEN_PLAN_SIZE_OBJECTS = Gauge(
    "garden_plan_size_objects",
    "Locations plus garden objects of the plan last read or written, by size class (GP-NFR-061).",
    ("size",),
    registry=REGISTRY,
)


def size_class(object_count: int) -> str:
    """The §25.1 bucket of a plan with *object_count* locations and garden objects."""
    if object_count <= SIZE_SMALL_MAX:
        return "small"
    if object_count <= SIZE_MEDIUM_MAX:
        return "medium"
    return "large"


def observe_plan_size(object_count: int) -> None:
    """Record the object count of the plan just handled under its size class (the last value per class)."""
    GARDEN_PLAN_SIZE_OBJECTS.labels(size=size_class(object_count)).set(object_count)


def record_conflict() -> None:
    """Count one batch refused with ``plan.revision_conflict``."""
    GARDEN_PLAN_CONFLICTS.inc()


def observe_batch_duration(seconds: float) -> None:
    """Record the duration of one applied batch."""
    GARDEN_PLAN_BATCH_DURATION.observe(seconds)
