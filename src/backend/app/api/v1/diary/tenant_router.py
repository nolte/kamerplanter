"""REQ-050 §2.5.2 — the tenant-wide diary overview.

``GET /api/v1/t/{tenant_slug}/diary`` lists the diary entries of **all** the
tenant's plants in one chronologically descending view. REQ-013 only ever knew
an aggregation per *planting run*; a plant without a run appears in none of
them, which is precisely the plant REQ-050 §2.5.1 puts a diary tab on.

Three properties of this endpoint are load-bearing and easy to lose:

* **The row is slim.** ``analysis_summary`` yes, ``findings`` and
  ``recommended_actions`` never (AK-18) — see :mod:`.schemas`.
* **``can_request_analysis`` is computed here, server-side** (AK-18a), from the
  same :meth:`PlantDiaryService.evaluate_request_permission` the marking
  endpoint enforces. It is an aid for rendering the button, not the
  authorisation: a marking attempt on a ``false`` row is still refused by the
  service.
* **The state filter matches pre-REQ-050 entries.** Those documents carry no
  ``analysis_state`` attribute at all, and a missing attribute is ``null`` in
  AQL — never equal to ``"none"``. The repository's ``analysis_state_bind_values``
  expands the filter accordingly (AK-26); this router must not bypass it by
  filtering states itself before the query.

**No filter is applied in this module.** Every parameter of §2.5.2 travels into
:class:`~app.domain.interfaces.plant_diary_repository.DiaryOverviewFilter` and is
answered by one AQL query, which is also what makes ``total`` the real number of
matches. Re-applying any of them here would narrow the page the repository
already selected, so the response would be shorter than its own ``total``; a
predecessor of this endpoint read a bounded window and filtered it in Python,
which additionally cut off every tenant above the window without saying so in the
response.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.diary.schemas import EXCERPT_MAX_LENGTH, DiaryOverviewItem, DiaryOverviewResponse
from app.common.auth import get_current_tenant
from app.common.datetimes import now_utc
from app.common.dependencies import get_plant_diary_service, get_plant_instance_service
from app.common.enums import DiaryAnalysisState, DiaryEntryType
from app.common.exceptions import NotFoundError
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter
from app.domain.models.plant_diary_entry import PlantDiaryEntry
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_diary_service import (
    PlantDiaryService,
    effective_analysis_state,
    lease_expired,
)
from app.domain.services.plant_instance_service import PlantInstanceService

router = APIRouter(prefix="/diary", tags=["diary"])


class _PlantContext:
    """Per-request cache for the plant/species labels of the overview rows.

    Diary entries cluster on few plants, so resolving each entry's plant
    individually would re-read the same document dozens of times per page. The
    cache also has to be negative: a plant that was deleted while its entries
    survive must not be looked up once per row.
    """

    def __init__(self, plant_service: PlantInstanceService, tenant_key: str) -> None:
        self._service = plant_service
        self._tenant_key = tenant_key
        self._plants: dict[str, PlantInstance | None] = {}
        self._species: dict[str, str | None] = {}

    def plant(self, plant_key: str) -> PlantInstance | None:
        if plant_key not in self._plants:
            try:
                self._plants[plant_key] = self._service.get_plant(plant_key, tenant_key=self._tenant_key)
            except NotFoundError:
                # Either gone, or owned by another tenant. Both are "no label" —
                # the entry itself was already restricted to this tenant by the
                # repository query, so this is never a way in.
                self._plants[plant_key] = None
        return self._plants[plant_key]

    def species_name(self, species_key: str) -> str | None:
        if species_key not in self._species:
            species = self._service.resolve_species(species_key)
            name: str | None = None
            if species is not None:
                name = species.scientific_name or (species.common_names[0] if species.common_names else None)
            self._species[species_key] = name
        return self._species[species_key]


def _excerpt(entry: PlantDiaryEntry) -> str:
    """The first characters of the free text, cut server-side (§2.5.2)."""
    return (entry.text or "")[:EXCERPT_MAX_LENGTH]


@router.get("", response_model=DiaryOverviewResponse)
def list_tenant_diary(
    analysis_state: Annotated[
        list[DiaryAnalysisState] | None,
        Query(description="Filter by analysis state; repeat the parameter to allow several."),
    ] = None,
    plant_key: Annotated[str | None, Query(description="Filter by plant instance.")] = None,
    species_key: Annotated[str | None, Query(description="Filter by the species of the plant instance.")] = None,
    entry_type: Annotated[DiaryEntryType | None, Query(description="Filter by diary entry type.")] = None,
    tag: Annotated[str | None, Query(description="Filter by a tag on the entry (case-insensitive).")] = None,
    date_from: Annotated[
        date | None,
        Query(alias="from", description="Only entries created on or after this date (UTC)."),
    ] = None,
    date_to: Annotated[
        date | None,
        Query(alias="to", description="Only entries created on or before this date (UTC)."),
    ] = None,
    q: Annotated[str | None, Query(description="Free-text search over title and text.")] = None,
    sort: Annotated[
        Literal["created_at", "analyzed_at"],
        Query(description="Sort field; always descending."),
    ] = "created_at",
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of rows to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of rows to skip.")] = 0,
    ctx: TenantContext = Depends(get_current_tenant),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
) -> DiaryOverviewResponse:
    """List the diary entries of all the tenant's plants (REQ-050 §2.5.2).

    Strictly scoped to ``tenant_key`` — the shared-garden case shows other
    members' entries (they are the same tenant), never another tenant's. An
    empty result is not an error (``items: []``, ``total: 0``), and every absent
    value is rendered as ``null`` rather than an omitted key, so the row shape is
    identical across the page.

    ``total`` counts every match across all pages, and nothing here caps or
    post-filters the result: filtering, sorting and paging are one AQL statement,
    so a tenant with 50 000 entries gets an answer of the same shape and the same
    honesty as one with 50. The only per-row work left in this module is
    resolving the plant/species labels of the rows actually returned, which is
    bounded by ``limit`` and cached per request.
    """
    entries, total = diary_service.list_overview(
        ctx.tenant_key,
        DiaryOverviewFilter(
            analysis_states=tuple(analysis_state or ()),
            plant_key=plant_key,
            species_key=species_key,
            entry_type=entry_type,
            tag=tag,
            created_from=date_from,
            created_to=date_to,
            search=q,
            sort=sort,
        ),
        offset=offset,
        limit=limit,
    )

    context = _PlantContext(plant_service, ctx.tenant_key)
    # One instant for the whole page: every lease on it is judged against the
    # same clock, so two rows cannot disagree about whether "now" is past a
    # deadline, and a single row's state and its claim timestamp cannot be
    # decided a few microseconds apart.
    now = now_utc()
    items = [_overview_item(entry, context, diary_service, ctx, now) for entry in entries]
    return DiaryOverviewResponse(items=items, total=total, limit=limit, offset=offset)


def _overview_item(
    entry: PlantDiaryEntry,
    context: _PlantContext,
    diary_service: PlantDiaryService,
    ctx: TenantContext,
    now: datetime,
) -> DiaryOverviewItem:
    """Build one row, resolving the plant labels and the §7.2 verdict.

    **The row's timestamps follow the displayed state, not the stored one.**
    ``analysis_state`` is corrected by ``effective_analysis_state``, so an entry
    whose agent lease has run out reads as ``requested``; for exactly that row
    ``analysis_claimed_at`` is suppressed to ``null``, because a beginning of
    analysis next to "wartet auf Analyse" would be a contradiction the reader
    cannot resolve — the slim row carries neither ``analysis_claimed_by`` nor
    ``analysis_lease_expires_at``, which are what make the crashed-agent case
    legible on the single-entry read. Every other state keeps its value: on
    ``in_progress`` it is the live lease §2.5.2 asks to show, on
    ``completed``/``failed`` the claim of the run whose outcome the row shows.
    A re-marked entry has none, because ``request_analysis`` clears the claim
    fields when it puts the entry back to ``requested``.

    ``now`` is passed in rather than read twice here: the state and the
    timestamp are two questions about the same lease, and answering them from
    two clock readings could produce the one combination that must never leave
    this function — ``requested`` *with* a claim timestamp.
    """
    plant = context.plant(entry.plant_key)
    permission = diary_service.evaluate_request_permission(entry, user_key=ctx.user_key, role=ctx.role)
    return DiaryOverviewItem(
        key=entry.key or "",
        created_at=entry.created_at,
        entry_type=entry.entry_type,
        title=entry.title,
        excerpt=_excerpt(entry),
        tags=entry.tags,
        plant_key=entry.plant_key,
        plant_name=plant.plant_name if plant else None,
        instance_id=plant.instance_id if plant else "",
        species_name=context.species_name(plant.species_key) if plant else None,
        photo_count=len(entry.photo_refs),
        preview_photo_id=entry.photo_refs[0] if entry.photo_refs else None,
        analysis_state=effective_analysis_state(entry, now),
        # AK-18 — the summary and nothing else of the result.
        analysis_summary=entry.analysis.summary if entry.analysis else None,
        analysis_error=entry.analysis_error,
        # §2.5.2 — the moment of claiming, dropped exactly where the displayed
        # state contradicts it (see the docstring).
        analysis_claimed_at=None if lease_expired(entry, now) else entry.analysis_claimed_at,
        analyzed_at=entry.analysis.analyzed_at if entry.analysis else None,
        can_request_analysis=permission.allowed,
    )
