"""The writes of a bed's ``soil_hazards`` (REQ-054 §5.2, AP-API-012, #2888 F-20).

Each write is **one transaction** that re-reads the bed under its site's tenant (a ``Location`` carries no
``tenant_key``, #2107 - the site is the anchor), applies the change to that snapshot and writes the list back only if
it changed. Two concurrent writes to the same bed therefore never lose one another: the second one to commit conflicts
(``WriteConflictError``, 409) instead of overwriting the list it did not read.

The change itself is the caller's (``bed_soil_hazard_engine``), so the rule "one entry per hazard, the later
confirmation wins" lives in one place. The outcome is a status: which refusal it becomes is the service's decision.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from app.domain.models.bed_soil_hazard import BedSoilHazard

#: What one write did. ``written`` and ``unchanged`` carry the bed's entries after the write.
type SoilHazardWriteStatus = Literal["written", "unchanged", "location_not_found"]

#: The change of one write: the stored entries in, the entries to store out.
type SoilHazardChange = Callable[[tuple[BedSoilHazard, ...]], tuple[BedSoilHazard, ...]]


@dataclass(frozen=True)
class SoilHazardWrite:
    status: SoilHazardWriteStatus
    entries: tuple[BedSoilHazard, ...] = ()


class IBedSoilHazardRepository(ABC):
    @abstractmethod
    def change_soil_hazards(self, location_key: str, *, tenant_key: str, change: SoilHazardChange) -> SoilHazardWrite:
        """Apply ``change`` to the stored entries of the tenant's bed ``location_key`` in one transaction.

        ``location_not_found`` for an absent bed and for a bed under another tenant's site alike; ``unchanged``
        when ``change`` returns the stored entries (nothing is written then).
        """
