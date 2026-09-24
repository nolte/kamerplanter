"""REQ-025 Art. 15 — read side of the declared personal-data inventory.

The Art. 15 disclosure walks :attr:`DataExportEngine.USER_DATA_MANIFEST`. This
interface is how a source from that manifest turns into rows: the caller hands
over the *declared* source and never names a collection itself, so the manifest
stays the single reader (#1622) and the executing path cannot drift from it.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from app.common.types import UserKey
from app.domain.models.privacy import DataSourceDefinition


class IPersonalDataRepository(ABC):
    """Reads the documents one manifest source declares for a user."""

    @abstractmethod
    def collect_for_user(
        self,
        source: DataSourceDefinition,
        user_key: UserKey,
        tenant_keys: Sequence[str],
    ) -> list[dict[str, Any]]:
        """Return the declared ``source.fields`` of every document of *user_key*.

        ``tenant_keys`` are the subject's own tenants. A ``tenant_scoped``
        source is restricted to them, so a document in a tenant the subject is
        not a member of can never reach their disclosure — whoever wrote the
        user-reference field (#1662 SCR-001). A source with a
        ``disclosure_gap`` must be refused, not answered with ``[]``.

        Three shapes, all declared by the source itself:

        * ``edge_collection`` set — traverse that edge from the user vertex.
        * ``filter_field == "_key"`` — the user document itself.
        * ``filter_field`` ``_from`` / ``_to`` — the rows of an edge collection
          whose endpoint is the user vertex ``users/<key>`` (#1719): the edge
          itself is the data, not the vertex at its other end.
        * any other ``filter_field`` — documents carrying the user reference.

        Returns an empty list when the user has no data in that source. A
        source the repository cannot resolve raises rather than returning
        ``[]``: an empty list is indistinguishable from "no data", which is how
        an Art. 15 disclosure silently under-delivers.
        """
