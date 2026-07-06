"""REQ-047 §2.1 — ArangoDB repository for ``:SeasonState`` records."""

from arango.database import StandardDatabase

from app.common.exceptions import DuplicateError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.season_state_repository import ISeasonStateRepository
from app.domain.models.season_state import SeasonState


class ArangoSeasonStateRepository(BaseArangoRepository[SeasonState], ISeasonStateRepository):
    """REQ-047 §2 — ``season_states`` repository (tenant-scoped, 1:1 per site)."""

    _model_cls = SeasonState
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SEASON_STATES)

    # ── Reads ──────────────────────────────────────────────────────────

    def get_by_site(self, site_key: str, tenant_key: str) -> SeasonState | None:
        return self.find_one_by_field(
            "site_key",
            site_key,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def list_for_tenant(self, tenant_key: str, offset: int = 0, limit: int = 200) -> tuple[list[SeasonState], int]:
        return super().get_all(offset, limit, tenant_key=tenant_key)

    # ── Writes ─────────────────────────────────────────────────────────

    def upsert(self, state: SeasonState) -> SeasonState:
        """Create or update the site's season state, wiring the edge on insert.

        Idempotent per ``(tenant_key, site_key)``: an existing state is updated in
        place; a fresh state is created and linked to its site via the 1:1
        ``has_season_state`` edge.
        """
        existing = self.get_by_site(state.site_key, state.tenant_key)
        if existing is not None and existing.key:
            return super().update(existing.key, state)

        try:
            created = super().create(state)
        except DuplicateError:
            # B3 — two parallel evaluations of a state-less site both reached the
            # insert; the unique ``(tenant_key, site_key)`` index rejected the
            # loser. Re-read the winner and update it in place instead of 500-ing
            # the second reader.
            winner = self.get_by_site(state.site_key, state.tenant_key)
            if winner is not None and winner.key:
                return super().update(winner.key, state)
            raise
        if state.site_key and created.key:
            from_id = f"{col.SITES}/{state.site_key}"
            to_id = f"{col.SEASON_STATES}/{created.key}"
            self.create_edge(col.HAS_SEASON_STATE, from_id, to_id)
        return created
