"""In-memory stand-in for :class:`IReferenceContributionMarker` (#1753).

Mirrors the Arango implementation's contract: the first ``record`` sets the
timestamp, every later one keeps it; ``fail_reads`` / ``fail_writes`` make the
read or the write raise like an unreachable database does.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.interfaces.reference_contribution_marker import IReferenceContributionMarker


class FakeContributionMarker(IReferenceContributionMarker):
    def __init__(self, since: datetime | None = None) -> None:
        self.since = since
        self.fail_reads = False
        self.fail_writes = False
        self.writes = 0

    def record_reference_contributions(self, now: datetime) -> None:
        if self.fail_writes:
            raise ConnectionError("arangodb unreachable")
        self.writes += 1
        if self.since is None:
            self.since = now

    def reference_contributions_since(self) -> datetime | None:
        if self.fail_reads:
            raise ConnectionError("arangodb unreachable")
        return self.since
