from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from app.common.enums import DiaryAnalysisState, DiaryEntryType
from app.domain.models.plant_diary_entry import PlantDiaryEntry

#: Sort fields of the tenant-wide overview (REQ-050 §2.5.2). Always descending —
#: the requirement offers no ascending variant, and a list of observations is
#: read newest-first.
type DiaryOverviewSort = Literal["created_at", "analyzed_at"]


@dataclass(frozen=True, slots=True)
class DiaryOverviewFilter:
    """Every filter the tenant-wide diary overview accepts (REQ-050 §2.5.2).

    **Why one object instead of nine keyword arguments.** All of these are
    answered by a *single* AQL query, and they only make sense together: the
    ``total`` of the response is the number of documents that satisfy all of them
    at once. Handing them down individually invites the failure this type exists
    to prevent — one filter applied in the repository, the next one applied by the
    caller after paging, and a ``total`` that counts rows the caller then throws
    away.

    ``analysis_states`` names the **displayed** state (see
    :func:`~app.domain.services.plant_diary_service.effective_analysis_state`),
    not the stored one. An entry whose analysis lease has run out is stored as
    ``in_progress`` but is back in the work queue and displays as ``requested``;
    a "nur wartend" filter that asked the database for the stored value alone
    would hide exactly the entries a crashed agent left behind. An empty tuple
    means "no state filter" — every state is admitted.

    ``created_from`` / ``created_to`` are inclusive calendar days in UTC, matching
    the ``from`` / ``to`` query parameters of §2.5.2.
    """

    analysis_states: tuple[DiaryAnalysisState | str, ...] = ()
    plant_key: str | None = None
    species_key: str | None = None
    entry_type: DiaryEntryType | str | None = None
    tag: str | None = None
    created_from: date | None = None
    created_to: date | None = None
    search: str | None = None
    sort: DiaryOverviewSort = "created_at"


class IPlantDiaryRepository(ABC):
    """Interface for plant diary entry persistence."""

    @abstractmethod
    def create(self, entry: PlantDiaryEntry) -> PlantDiaryEntry: ...

    @abstractmethod
    def get_by_key(self, key: str) -> PlantDiaryEntry | None: ...

    @abstractmethod
    def get_or_raise(self, key: str) -> PlantDiaryEntry: ...

    @abstractmethod
    def update(self, key: str, entry: PlantDiaryEntry) -> PlantDiaryEntry: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict[str, Any]) -> PlantDiaryEntry: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def get_by_plant(
        self,
        plant_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """One plant's diary entries inside ``tenant_key``, newest first (SEC-002).

        ``tenant_key`` is **required and keyword-only**, and an empty value is
        rejected rather than read as "every tenant". This read enters the graph
        through the ``has_diary_entry`` edge of a key that comes from the URL;
        without the predicate, pairing an own run with a foreign ``plant_key``
        returned another tenant's entries in full. The isolation belongs here,
        not in the two endpoints that call it — one of them did not check.
        """

    @abstractmethod
    def get_by_run(
        self,
        run_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """Diary entries of a run's non-detached plants inside ``tenant_key``.

        Same edge-anchored shape and the same requirement as
        :meth:`get_by_plant`; see there.
        """

    # ── REQ-050 AI analysis ──────────────────────────────────────────────────

    @abstractmethod
    def get_with_revision(self, key: str) -> tuple[PlantDiaryEntry, str] | None:
        """Load an entry together with its storage revision (REQ-050 §2.2).

        The revision is the fencing token of the claim: it is read here and
        handed back to :meth:`update_fields_checked`, which refuses the write if
        anything changed in between. The domain model deliberately does not
        carry ``_rev`` — it is storage metadata, not domain state — so it
        travels as a separate value.

        Returns ``None`` when the entry does not exist.
        """

    @abstractmethod
    def update_fields_checked(
        self, key: str, fields: dict[str, Any], *, expected_rev: str
    ) -> tuple[PlantDiaryEntry, str]:
        """Partial update guarded by a compare-and-set on ``expected_rev``.

        Raises :class:`~app.common.exceptions.DiaryAnalysisConcurrentUpdateError`
        when the stored revision no longer matches — the second claimant of a
        contested entry must fail, never overwrite (REQ-050 §2.2, AK-05).
        ``None`` values in ``fields`` are *written* (``keep_none``), which is the
        only way to clear a lease: the full-model path dumps with
        ``exclude_none=True`` and would silently leave the old holder in place.

        Returns the updated entry together with its **new** revision, so a
        caller writing twice in sequence can fence the second write without a
        re-read.
        """

    @abstractmethod
    def list_pending_analyses(
        self,
        tenant_key: str,
        *,
        limit: int = 20,
        include_stale: bool = True,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """Return the analysis work queue of one tenant (REQ-050 §4.1).

        Oldest ``analysis_requested_at`` first. ``include_stale`` additionally
        yields entries whose lease has run out, so a crashed agent cannot pin an
        entry forever (AK-06). The returned ``total`` counts every waiting entry,
        independent of ``limit``.
        """

    @abstractmethod
    def list_overview(
        self,
        tenant_key: str,
        filters: DiaryOverviewFilter | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """One page of the tenant-wide diary overview (REQ-050 §2.5.2).

        **Every** filter of :class:`DiaryOverviewFilter` is answered by the
        storage layer, and ``total`` is the real number of matches across all
        pages — not the length of the returned page and not the size of some
        scanned window. That is the contract: an answer that silently covers only
        part of the tenant's entries is worse than an error, because it looks
        complete.

        Filtering for the state ``none`` also matches entries written before
        REQ-050, which carry no ``analysis_state`` attribute at all (AK-26), and
        filtering for ``requested`` also matches an entry whose analysis lease has
        run out even though it is stored as ``in_progress`` (AK-06).

        ``now`` overrides the moment the lease expiry is measured against; it
        exists for tests and defaults to the current time.
        """
