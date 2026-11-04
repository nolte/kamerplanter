"""Read side of the care-event consistency job (REQ-053 GP-FR-105; WP 8.2, #2645)."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from typing import Any


class ICareEventGapReader(ABC):
    """The domain-event documents of a source that may lack a care event, with their references resolved."""

    @abstractmethod
    def candidates(self, source: str, since: datetime) -> Iterator[dict[str, Any]]:
        """Rows ``{doc, refs, own_location_key, locations, present}`` for every ``source`` document performed at or
        after ``since``, sorted by key. ``present`` says a care event with this ``source_ref`` exists already.

        Cross-tenant on purpose: the job walks the installation, and decides per row which tenant it may write into.
        """
