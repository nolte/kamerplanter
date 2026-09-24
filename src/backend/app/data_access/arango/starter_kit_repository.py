"""The ``starter_kits`` collection (REQ-020)."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository


class ArangoStarterKitRepository(BaseArangoRepository):
    """Persistence for the seeded starter kits the onboarding wizard offers.

    A class of its own so :class:`~app.domain.services.starter_kit_service.StarterKitService`
    is handed a repository instead of building one from a ``StandardDatabase``
    it would otherwise have to hold (#1638). Raw mode is kept (FR-002 A3): the
    service wraps each returned ``dict`` into
    :class:`~app.domain.models.starter_kit.StarterKit` itself, exactly as it did
    when it constructed the bare ``BaseArangoRepository`` in its own ``__init__``.
    """

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.STARTER_KITS, raw=True)
