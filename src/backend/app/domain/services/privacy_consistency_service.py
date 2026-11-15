"""The daily privacy consistency check, minimal form (spec/privacy PRIV-206, DEC-28; E04).

Counts tombstone-shaped values (both generations) in every account-reference cell of the erasure
inventory that is **not** on the tombstone allowlist (:meth:`ErasureEngine.tombstone_watch_fields`).
Such a value is a defect — a copy of a pseudonym into a field that should hold a live key or the
marker — and it is reported, never corrected: the one correction is migration v0109 (spec/privacy/09
§3). Read-only; signals are one structlog event, a warning when anything was found, and the gauge
``privacy_undeclared_tombstones{cell}``. No endpoint, no operations listing — those are E15.

The cells and the pattern are read live from the inventory and from ``app.domain.models.privacy`` on
every run, so a rule added to the inventory is watched from the next run on; the counting AQL is the
one migration v0109 runs with its frozen arguments (:mod:`app.data_access.arango.tombstone_census`).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import structlog

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.tombstone_census import ITombstoneCensus
from app.domain.models.privacy import TOMBSTONE_REGEX
from app.observability.privacy_metrics import record_undeclared_tombstones

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PrivacyConsistencyReport:
    """What one run counted, per ``<collection>.<field>`` cell (zero included)."""

    undeclared_tombstones: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.undeclared_tombstones.values())

    @property
    def findings(self) -> dict[str, int]:
        """Only the cells that hold a tombstone."""
        return {cell: count for cell, count in self.undeclared_tombstones.items() if count}


class PrivacyConsistencyService:
    def __init__(self, census: ITombstoneCensus) -> None:
        self._census = census

    def run(self) -> PrivacyConsistencyReport:
        """Count the undeclared tombstones of the installation; set the gauge and log the result."""
        started = time.monotonic()
        counts = self._census.count_tombstones(ErasureEngine.tombstone_watch_fields(), TOMBSTONE_REGEX)
        report = PrivacyConsistencyReport(undeclared_tombstones=dict(counts))
        record_undeclared_tombstones(report.undeclared_tombstones)
        logger.info(
            "privacy_consistency.completed",
            duration_seconds=round(time.monotonic() - started, 3),
            cells=len(report.undeclared_tombstones),
            undeclared_tombstones=report.total,
        )
        if report.total:
            logger.warning("privacy_consistency.undeclared_tombstones", findings=report.findings, total=report.total)
        return report
