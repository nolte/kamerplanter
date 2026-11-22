"""The combined history of a bed: care events and planting events in one list (REQ-053 GP-FR-102, GP-API-038; WP 4.5).

* :meth:`BedHistoryService.list_history` — ``GET /locations/{key}/history``: the stored care events of the bed and
  the planting events **derived** from its plants and runs (planted, removed, run started, run completed), newest
  first, one page cut from the merged order (50 by default).

Read-only. The method takes ``*, tenant_key: str`` without a default; the bed is resolved through
:mod:`~app.domain.services.location_ownership` (a bed has no ``tenant_key`` of its own, #2107), so a foreign and an
absent bed answer the same 404. The ``performed_by`` filter follows the care log's rule (E-16, SR-020): the caller's
own account always, another member for a lead or a ``management`` scope. A person filter leaves the derived events
out — they have no performer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.common.enums import AdminScope, TenantRole
from app.domain.interfaces.bed_history_repository import (
    BedHistoryFilter,
    BedHistoryRow,
    IBedHistoryRepository,
    PlantingEvent,
)
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.care_event import CareEventView
from app.domain.services.care_event_service import check_performed_by_filter, view_of_row
from app.domain.services.location_ownership import resolve_owned_location


@dataclass(frozen=True)
class BedHistoryItem:
    """One line of the history: a care event view, or a derived planting event."""

    care: CareEventView | None = None
    planting: PlantingEvent | None = None


class BedHistoryService:
    def __init__(self, site_repo: ISiteRepository, history_repo: IBedHistoryRepository) -> None:
        self._sites = site_repo
        self._history = history_repo

    def list_history(
        self,
        location_key: str,
        criteria: BedHistoryFilter,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        admin_scopes: Sequence[AdminScope] = (),
        offset: int,
        limit: int,
    ) -> list[BedHistoryItem]:
        """One page of the bed's history, newest first (GP-API-038)."""
        check_performed_by_filter(criteria.performed_by, user_key=user_key, role=role, admin_scopes=admin_scopes)
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        rows: list[BedHistoryRow] = self._history.list_history(
            location.key or location_key, criteria, tenant_key=tenant_key, offset=offset, limit=limit
        )
        return [
            BedHistoryItem(care=view_of_row(row.care, user_key))
            if row.care is not None
            else BedHistoryItem(planting=row.planting)
            for row in rows
        ]
