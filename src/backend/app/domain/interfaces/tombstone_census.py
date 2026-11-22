"""Read side of the privacy consistency check (spec/privacy PRIV-206, DEC-28)."""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class ITombstoneCensus(ABC):
    """Counts tombstone-shaped values in account-reference fields; never reads or returns a value."""

    @abstractmethod
    def count_tombstones(self, fields: Sequence[tuple[str, str]], pattern: str) -> dict[str, int]:
        """``{"<collection>.<field>": count}`` of rows whose *field* matches *pattern*, for every given cell.

        Cross-tenant on purpose: the census walks the installation and reports per cell, never per row,
        tenant or person. A collection the database does not have counts as ``0``.
        """
