"""Prometheus metric of the privacy consistency check (spec/privacy PRIV-206, DEC-28).

Registered on the process's registry (``app.observability.metrics.REGISTRY``) like the garden-plan
metrics. The label is a fixed ``<collection>.<field>`` cell name out of the erasure inventory — never a
tenant, a row or a value — so the series set is bounded by the inventory and says nothing about anyone.
"""

from __future__ import annotations

from collections.abc import Mapping

from prometheus_client import Gauge

from app.observability.metrics import REGISTRY

PRIVACY_UNDECLARED_TOMBSTONES = Gauge(
    "privacy_undeclared_tombstones",
    "Rows holding an erased-account tombstone in an account-reference field outside the tombstone allowlist, "
    "by cell, as the last privacy.consistency run counted them (spec/privacy PRIV-206). Alert on > 0.",
    ("cell",),
    registry=REGISTRY,
)


def record_undeclared_tombstones(counts: Mapping[str, int]) -> None:
    """Set the gauge for every counted cell — zero included, so a corrected cell drops back to 0."""
    for cell, count in counts.items():
        PRIVACY_UNDECLARED_TOMBSTONES.labels(cell=cell).set(count)
