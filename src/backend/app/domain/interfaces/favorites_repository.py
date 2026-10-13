from abc import ABC, abstractmethod


class IFavoritesRepository(ABC):
    """Persistence of the ``user_favorites`` edges and the reads favouriting needs (#1638).

    Favourites are raw edge documents (``_from`` = ``users/<key>``, ``_to`` =
    ``<catalogue>/<key>``); the service decides *which* catalogue a key resolves to
    and whether the caller may see it, and this interface only answers the
    questions it asks. The visibility decision itself stays in
    :class:`~app.domain.services.favorites_service.FavoritesService` so there is
    exactly one place that makes it (#1538).
    """

    # ── user_favorites edges ─────────────────────────────────────────

    @abstractmethod
    def find_edge(self, from_id: str, to_id: str) -> dict | None:
        """The favourite edge between two document ids, or ``None``."""
        ...

    @abstractmethod
    def promote_to_manual(self, edge_key: str) -> None:
        """Mark a cascade edge as manually favourited and clear ``cascade_from_key``."""
        ...

    @abstractmethod
    def insert_edge(self, edge_data: dict) -> dict:
        """Insert one favourite edge and return the stored document.

        A concurrent insert of the same ``_from``/``_to`` pair (HTTP 409 from the
        unique index) is not an error: the edge the other writer stored is
        returned instead. Any other failure propagates.
        """
        ...

    @abstractmethod
    def remove_edges_to_key(self, from_id: str, target_key: str) -> int:
        """Remove the caller's edges whose ``_to`` carries ``target_key``; return how many."""
        ...

    @abstractmethod
    def remove_cascade_edges(self, from_id: str, cascade_from_key: str) -> int:
        """Remove the caller's cascade-sourced edges created from one plan; return how many."""
        ...

    @abstractmethod
    def list_edges(self, from_id: str, target_type: str | None = None) -> list[dict]:
        """Every favourite edge of one user, optionally narrowed to one target collection."""
        ...

    # ── favourite-target resolution ──────────────────────────────────

    @abstractmethod
    def get_catalogue_row(self, collection_name: str, key: str) -> dict | None:
        """The row ``key`` in ``collection_name``, or ``None`` if there is none.

        A catalogue that does not exist at all answers ``None`` too (logged as a
        deployment defect). Every other datastore error propagates — a 404 that
        means "the database is down" would be a lie to the client (#1538).
        """
        ...

    @abstractmethod
    def is_granted(self, collection_name: str, key: str, tenant_key: str) -> bool:
        """Does an explicit ``tenant_has_access`` grant admit ``tenant_key`` to this row (#1092)?"""
        ...
