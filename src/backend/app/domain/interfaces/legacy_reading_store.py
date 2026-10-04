"""The slice of the readings store the pre-#2076 cleanup needs (#2077).

Kept apart from ``IObservationRepository`` on purpose: nothing but an operator-run
maintenance command may call ``purge_legacy_series``, and a method on the shared
interface would put it one autocomplete away from request code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LegacySeriesCounts:
    """Rows per table: the raw hypertable and the hourly/daily continuous aggregates."""

    raw: int = 0
    hourly: int = 0
    daily: int = 0

    @property
    def total(self) -> int:
        return self.raw + self.hourly + self.daily

    def __add__(self, other: LegacySeriesCounts) -> LegacySeriesCounts:
        return LegacySeriesCounts(self.raw + other.raw, self.hourly + other.hourly, self.daily + other.daily)


class ILegacyReadingStore(ABC):
    """Rows stored under ``tenant_key = ''`` (the Home Assistant poll before #2076), grouped by sensor."""

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def legacy_series(self) -> dict[str, LegacySeriesCounts]:
        """Row counts per sensor key over every table, for rows with an empty tenant key. Reads only."""

    @abstractmethod
    def purge_legacy_series(self, sensor_key: str) -> LegacySeriesCounts:
        """Delete one sensor's rows with an empty tenant key from every table; return the counts removed.

        Never touches a row with a non-empty tenant key. The caller has decided that
        the sensor is gone; the store only enforces its own bounds (a non-empty
        sensor key, bounded transactions).
        """
