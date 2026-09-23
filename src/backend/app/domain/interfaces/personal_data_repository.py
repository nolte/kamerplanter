"""REQ-025 Art. 15 — read side of the declared personal-data inventory.

The Art. 15 disclosure walks :attr:`DataExportEngine.USER_DATA_MANIFEST`. This
interface is how a source from that manifest turns into rows: the caller hands
over the *declared* source and never names a collection itself, so the manifest
stays the single reader (#1622) and the executing path cannot drift from it.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.common.types import UserKey
from app.domain.models.privacy import DataSourceDefinition


class IPersonalDataRepository(ABC):
    """Reads the documents one manifest source declares for a user."""

    @abstractmethod
    def collect_for_user(self, source: DataSourceDefinition, user_key: UserKey) -> list[dict[str, Any]]:
        """Return the declared ``source.fields`` of every document of *user_key*.

        Three shapes, all declared by the source itself:

        * ``edge_collection`` set — traverse that edge from the user vertex.
        * ``filter_field == "_key"`` — the user document itself.
        * any other ``filter_field`` — documents carrying the user reference.

        Returns an empty list when the user has no data in that source. A
        source the repository cannot resolve raises rather than returning
        ``[]``: an empty list is indistinguishable from "no data", which is how
        an Art. 15 disclosure silently under-delivers.
        """
