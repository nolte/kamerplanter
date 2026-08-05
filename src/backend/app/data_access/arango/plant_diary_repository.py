from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from arango.database import StandardDatabase
from arango.exceptions import DocumentRevisionError, DocumentUpdateError

from app.common.datetimes import now_utc
from app.common.enums import DiaryAnalysisState, DiaryEntryType
from app.common.exceptions import DiaryAnalysisConcurrentUpdateError, NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import _RESERVED_DOC_ATTRIBUTES, BaseArangoRepository
from app.data_access.arango.query_builder import escape_aql_like
from app.domain.interfaces.plant_diary_repository import (
    DiaryOverviewFilter,
    DiaryOverviewSort,
    IPlantDiaryRepository,
)
from app.domain.models.plant_diary_entry import PlantDiaryEntry

#: ArangoDB error code for "document not found" on a write.
_ERR_DOCUMENT_NOT_FOUND = 1202

#: Every state a document can be *stored* in. Used to recognise a state filter
#: that excludes nothing, so it can be dropped instead of turned into an ``IN``
#: over the full value range.
_ALL_STATES: frozenset[str] = frozenset(state.value for state in DiaryAnalysisState)


def analysis_state_bind_values(states: Sequence[DiaryAnalysisState | str]) -> list[str | None]:
    """Expand analysis states into the values an AQL ``IN`` filter must match.

    A diary entry written before REQ-050 carries **no** ``analysis_state``
    attribute, and in AQL a missing attribute is ``null`` — never equal to the
    string ``"none"``. A filter for ``none`` that does not also match ``null``
    therefore silently skips exactly the entries AK-26 promises to read as
    ``none``: the ones that existed before the feature.

    The expansion goes into the bound value list rather than into an
    ``OR doc.analysis_state == null`` clause on purpose. The persistent index is
    ``(tenant_key, analysis_state, analysis_requested_at)`` (migration ``v0033``)
    and the optimiser still serves ``IN`` from it as a set of ranges; an ``OR``
    on the same attribute breaks that and turns the read into a collection scan.
    """
    values: list[str | None] = []
    for state in states:
        value = DiaryAnalysisState(state).value
        if value not in values:
            values.append(value)
        if value == DiaryAnalysisState.NONE.value and None not in values:
            values.append(None)
    return values


def stored_states_for_display(states: Sequence[DiaryAnalysisState | str]) -> list[DiaryAnalysisState]:
    """Widen *displayed* analysis states to the *stored* ones that produce them.

    An entry whose analysis lease has run out sits in the database as
    ``in_progress`` but is back in the work queue and displays as ``requested``
    (:func:`~app.domain.services.plant_diary_service.effective_analysis_state`).
    A "nur wartend" filter that asked the index for ``requested`` alone would
    hide precisely the entries a crashed agent left behind — the ones a user
    filters for.

    The widening exists so the *index* can still pre-select: the persistent index
    is ``(tenant_key, analysis_state, analysis_requested_at)`` and only knows the
    stored value. The narrowing back to the displayed state is a follow-up
    predicate inside the same query (never a post-filter in the caller, which
    would make ``total`` a lie).
    """
    widened = {DiaryAnalysisState(state) for state in states}
    if DiaryAnalysisState.REQUESTED in widened:
        widened.add(DiaryAnalysisState.IN_PROGRESS)
    return sorted(widened, key=lambda state: state.value)


def _overview_sort_clause(sort: DiaryOverviewSort) -> str:
    """The ``SORT`` of the overview — always descending (§2.5.2).

    ``_key`` is the final tiebreaker on both variants. Without it two entries
    written in the same second have no defined order between two requests, and a
    row can appear on page 1 *and* page 2 while another appears on neither —
    paging that quietly loses rows.

    ``null`` is AQL's smallest value, so a descending sort puts the unanalysed
    entries last by itself: sorting by analysis time must not push an entry that
    has no analysis to the top.
    """
    if sort == "analyzed_at":
        return "SORT doc.analysis.analyzed_at DESC, doc.created_at DESC, doc._key DESC"
    return "SORT doc.created_at DESC, doc._key DESC"


def _day_bounds_ms(day: date, *, end_of_day: bool) -> int:
    """Epoch milliseconds of the start of ``day`` (or of the following day).

    The overview's ``from``/``to`` are inclusive calendar days in UTC, while
    ``created_at`` is a timestamp. Comparing them as strings would make the
    result depend on how the timestamp happens to be *spelled* (``…Z`` versus
    ``…+00:00``, offsets other than UTC), so both sides are reduced to a number
    and compared with ``DATE_TIMESTAMP`` in AQL instead.
    """
    moment = datetime.combine(day, time.min, tzinfo=UTC)
    if end_of_day:
        moment += timedelta(days=1)
    return int(moment.timestamp() * 1000)


class ArangoPlantDiaryRepository(BaseArangoRepository[PlantDiaryEntry], IPlantDiaryRepository):
    """ArangoDB implementation for plant diary entries."""

    _model_cls = PlantDiaryEntry

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.PLANT_DIARY_ENTRIES)

    # ── CRUD ─────────────────────────────────────────────────────────

    def create(self, entry: PlantDiaryEntry) -> PlantDiaryEntry:
        created = super().create(entry)

        # Create has_diary_entry edge: plant → diary entry
        if entry.plant_key:
            plant_id = f"{col.PLANT_INSTANCES}/{entry.plant_key}"
            entry_id = f"{col.PLANT_DIARY_ENTRIES}/{created.key}"
            self.create_edge(col.HAS_DIARY_ENTRY, plant_id, entry_id)

        return created

    def delete(self, key: str) -> bool:
        # Remove has_diary_entry edges pointing to this entry
        entry_id = f"{col.PLANT_DIARY_ENTRIES}/{key}"
        self.delete_edges(col.HAS_DIARY_ENTRY, entry_id, direction="inbound")
        return super().delete(key)

    # ── Queries ──────────────────────────────────────────────────────

    def get_by_plant(
        self,
        plant_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """One plant's diary entries **inside one tenant**, newest first (SEC-002).

        ``tenant_key`` is keyword-only and has no default on purpose. This read
        enters the graph through an edge — ``has_diary_entry`` outbound from
        ``plant_instances/{plant_key}`` — and the entry point is a key that
        arrives from the URL. Until SEC-002 it carried no tenant predicate at
        all: a member of tenant A who paired a run of their own with a foreign
        ``plant_key`` received the other tenant's complete entries, free text,
        photo references and (since REQ-050) analysis result included.

        Putting the filter here rather than in the endpoint is the whole point.
        A caller-side check is one line the next endpoint forgets — this one had
        two endpoints and only one of them checked. With the parameter required
        and the sentinel rejected, a read that does not name a tenant cannot be
        written at all, and the isolation is a property of the storage layer.

        The count runs the *same* predicate as the page: an edge whose target
        belongs to another tenant must not be counted either, otherwise ``total``
        reports rows the caller may never see — and leaks their number.
        """
        self._require_tenant_key(tenant_key, "get_by_plant")
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        bind_vars: dict[str, Any] = {"plant_id": plant_id, "tenant_key": tenant_key}

        # ``entry != null`` guards a dangling edge: DOCUMENT() answers null for a
        # deleted target, and ``null.tenant_key`` would be null too — filtering
        # on the tenant already excludes it, but naming it keeps the intent
        # readable and the count honest.
        body = (
            f"FOR e IN {col.HAS_DIARY_ENTRY} "
            "FILTER e._from == @plant_id "
            "LET entry = DOCUMENT(e._to) "
            "FILTER entry != null AND entry.tenant_key == @tenant_key "
        )

        count_cursor = self._db.aql.execute(f"{body}COLLECT WITH COUNT INTO cnt RETURN cnt", bind_vars=bind_vars)
        total = next(count_cursor, 0)

        cursor = self._db.aql.execute(
            f"{body}SORT entry.created_at DESC LIMIT @offset, @limit RETURN entry",
            bind_vars={**bind_vars, "offset": offset, "limit": limit},
        )
        entries = [PlantDiaryEntry(**self._from_doc(doc)) for doc in cursor]
        return entries, total

    def get_by_run(
        self,
        run_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """Diary entries of all non-detached plants of a run, inside one tenant.

        Returns a list of dicts with plant_key, plant_id (instance_id),
        plant_name and the diary_entry object.

        Same shape as :meth:`get_by_plant` and therefore the same treatment
        (SEC-002): the query enters through the ``run_contains`` edge of a
        caller-supplied run key and used to select entry documents without ever
        naming a tenant. The run itself *is* checked by the endpoint, so this is
        defence in depth rather than a demonstrated leak — but it is the same
        one line away from being one, and a mis-parented entry (an import, a
        plant moved between tenants) would ride along today.
        """
        self._require_tenant_key(tenant_key, "get_by_run")
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        bind_vars: dict[str, Any] = {"run_id": run_id, "tenant_key": tenant_key}

        body = (
            f"FOR rc IN {col.RUN_CONTAINS} "
            "FILTER rc._from == @run_id AND rc.detached_at == null "
            "LET plant = DOCUMENT(rc._to) "
            f"FOR de IN {col.HAS_DIARY_ENTRY} "
            "FILTER de._from == rc._to "
            "LET entry = DOCUMENT(de._to) "
            "FILTER entry != null AND entry.tenant_key == @tenant_key "
        )

        count_cursor = self._db.aql.execute(f"{body}COLLECT WITH COUNT INTO cnt RETURN cnt", bind_vars=bind_vars)
        total = next(count_cursor, 0)

        query = (
            f"{body}"
            "SORT entry.created_at DESC "
            "LIMIT @offset, @limit "
            "RETURN { "
            "  plant_key: plant._key, "
            "  plant_id: plant.instance_id, "
            "  plant_name: plant.name, "
            "  diary_entry: entry "
            "}"
        )
        cursor = self._db.aql.execute(query, bind_vars={**bind_vars, "offset": offset, "limit": limit})
        results = []
        for doc in cursor:
            entry_data = doc.get("diary_entry")
            if entry_data:
                entry_data = self._from_doc(entry_data)
                doc["diary_entry"] = PlantDiaryEntry(**entry_data).model_dump(by_alias=True, mode="json")
            results.append(doc)

        return results, total

    # ── REQ-050 AI analysis ──────────────────────────────────────────────────

    def get_with_revision(self, key: str) -> tuple[PlantDiaryEntry, str] | None:
        """Load an entry plus its ``_rev`` fencing token (REQ-050 §2.2)."""
        doc = self._get_doc(key)
        if doc is None:
            return None
        return PlantDiaryEntry(**doc), str(doc.get("_rev", ""))

    def update_fields_checked(
        self, key: str, fields: dict[str, Any], *, expected_rev: str
    ) -> tuple[PlantDiaryEntry, str]:
        """Partial update, guarded by a compare-and-set on ``expected_rev``.

        This is the whole point of the claim path (REQ-050 §2.2): two agents that
        read the same unclaimed entry must not both win. ArangoDB answers a
        ``_rev`` mismatch with HTTP 412, which python-arango raises as
        :class:`DocumentRevisionError` — the loser is turned into
        ``conflict.concurrent_update`` and retries, rather than quietly
        overwriting the winner's claim and paying for the model twice.

        Three storage flags carry meaning here and none of them is a default
        worth inheriting silently:

        * ``check_rev=True`` — the fencing itself.
        * ``keep_none=True`` — the only way to *clear* a lease. The full-model
          path (:meth:`update`) dumps with ``exclude_none=True``, so a ``None``
          never reaches the document and the previous holder's
          ``analysis_claimed_by`` would survive the reset.
        * ``merge=False`` — a nested object in the payload replaces the stored
          one wholesale. With ArangoDB's default the new ``analysis`` would be
          *merged* into the old one, and a re-analysis that reports fewer keys
          would inherit leftovers of the previous run. AK-21 requires the
          previous result to be overwritten completely.

        Returns the updated entry **and its new revision**, so a caller that
        performs two writes in a row (release a dead lease, then act) can fence
        the second one without re-reading the document.
        """
        data = {field: value for field, value in fields.items() if field not in _RESERVED_DOC_ATTRIBUTES}
        data["updated_at"] = self._now()
        payload = {**data, "_key": key, "_rev": expected_rev}
        try:
            result = self.collection.update(
                payload,
                return_new=True,
                keep_none=True,
                merge=False,
                check_rev=True,
            )
        except DocumentRevisionError as exc:
            raise DiaryAnalysisConcurrentUpdateError(key) from exc
        except DocumentUpdateError as exc:
            if exc.error_code == _ERR_DOCUMENT_NOT_FOUND:
                raise NotFoundError("PlantDiaryEntry", key) from exc
            raise
        new_doc = self._from_doc(result["new"])
        new_rev = str(new_doc.get("_rev") or result.get("_rev") or "")
        return PlantDiaryEntry(**new_doc), new_rev

    def list_pending_analyses(
        self,
        tenant_key: str,
        *,
        limit: int = 20,
        include_stale: bool = True,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """Return one tenant's analysis work queue, oldest request first (§4.1).

        ``tenant_key`` filters first and by equality, which is what lets the
        ``(tenant_key, analysis_state, analysis_requested_at)`` index serve both
        the filter and the sort. ``analysis_lease_expires_at`` is deliberately
        *not* part of that index — it only narrows the small ``in_progress``
        range — so the staleness test is applied as a follow-up predicate.

        ``total`` deliberately re-runs the same filter without ``limit``: an
        agent that fetches 20 of 137 waiting entries must be told there are 137,
        otherwise it stops after one round and the queue drains at 20 per run.
        """
        self._require_tenant_key(tenant_key, "list_pending_analyses")
        moment = (now or now_utc()).isoformat()

        states: list[str] = [DiaryAnalysisState.REQUESTED.value]
        bind_vars: dict[str, Any] = {"tenant_key": tenant_key}
        stale_clause = ""
        if include_stale:
            # A claimed entry re-enters the queue once its lease has run out
            # (AK-06). A claimed entry without any lease timestamp is broken and
            # is treated as expired as well — the alternative is an entry no
            # agent can ever pick up again.
            states.append(DiaryAnalysisState.IN_PROGRESS.value)
            stale_clause = (
                "FILTER doc.analysis_state == @requested_state "
                "OR doc.analysis_lease_expires_at == null "
                "OR doc.analysis_lease_expires_at <= @now "
            )
            bind_vars["requested_state"] = DiaryAnalysisState.REQUESTED.value
            bind_vars["now"] = moment
        bind_vars["states"] = states

        filter_clause = (
            f"FOR doc IN {col.PLANT_DIARY_ENTRIES} "
            "FILTER doc.tenant_key == @tenant_key "
            "FILTER doc.analysis_state IN @states "
            f"{stale_clause}"
        )

        count_cursor = self._db.aql.execute(
            f"{filter_clause}COLLECT WITH COUNT INTO cnt RETURN cnt",
            bind_vars=bind_vars,
        )
        total = next(count_cursor, 0)

        cursor = self._db.aql.execute(
            f"{filter_clause}SORT doc.analysis_requested_at ASC LIMIT @limit RETURN doc",
            bind_vars={**bind_vars, "limit": limit},
        )
        entries = [PlantDiaryEntry(**self._from_doc(doc)) for doc in cursor]
        return entries, total

    def list_overview(
        self,
        tenant_key: str,
        filters: DiaryOverviewFilter | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """One page of the tenant-wide diary overview (§2.5.2, AK-17, AK-18).

        **Everything §2.5.2 lists is answered here, in one query.** State, plant,
        species, entry type, tag, date range and free text all narrow the same
        ``FOR`` loop, so ``total`` — a second run of the identical filter block
        under ``COLLECT WITH COUNT`` — is the real number of matches across all
        pages. The alternative, reading a window into memory and filtering it in
        the caller, produces an answer that looks complete and is not: the tenant
        above the window silently sees only part of their diary.

        **The index is served by the first two predicates.** ``tenant_key`` is an
        equality on the leading attribute of
        ``(tenant_key, analysis_state, analysis_requested_at)``, and the state
        filter is an ``IN`` the optimiser turns into index ranges. Everything
        after that narrows the rows the index already produced; none of it is
        indexed, and none of it has to be — a tenant's diary is bounded by that
        tenant, not by the collection.

        Two subtleties that a naive translation of the parameter table gets
        wrong, both of which would fail *silently*:

        * The state filter names the **displayed** state. An entry with an
          expired lease is stored ``in_progress`` and displays as ``requested``;
          :func:`stored_states_for_display` widens the indexed pre-selection and
          the ``displayed_analysis_state`` predicate narrows it again — inside
          the query, so ``total`` stays honest.
        * A pre-REQ-050 document has **no** ``analysis_state`` attribute, which is
          ``null`` in AQL and never equal to ``"none"``
          (:func:`analysis_state_bind_values`, AK-26).
        """
        self._require_tenant_key(tenant_key, "list_overview")
        spec = filters or DiaryOverviewFilter()
        body, bind_vars = self._overview_body(tenant_key, spec, now=now)

        count_cursor = self._db.aql.execute(
            f"{body} COLLECT WITH COUNT INTO cnt RETURN cnt",
            bind_vars=bind_vars,
        )
        total = next(count_cursor, 0)

        cursor = self._db.aql.execute(
            f"{body} {_overview_sort_clause(spec.sort)} LIMIT @offset, @limit RETURN doc",
            bind_vars={**bind_vars, "offset": offset, "limit": limit},
        )
        entries = [PlantDiaryEntry(**self._from_doc(doc)) for doc in cursor]
        return entries, total

    def _overview_body(
        self,
        tenant_key: str,
        spec: DiaryOverviewFilter,
        *,
        now: datetime | None,
    ) -> tuple[str, dict[str, Any]]:
        """Assemble the shared ``FOR``/``FILTER`` block of the overview query.

        Count and page run the *same* string, which is the point: two hand-kept
        filter lists are two chances for ``total`` to describe a different set
        than ``items``.
        """
        bind_vars: dict[str, Any] = {"tenant_key": tenant_key}
        # Ordering inside this list is load-bearing for the index: tenant_key by
        # equality first, the analysis state second. See the method docstring.
        clauses: list[str] = [f"FOR doc IN {col.PLANT_DIARY_ENTRIES}", "FILTER doc.tenant_key == @tenant_key"]

        wanted = [DiaryAnalysisState(state) for state in dict.fromkeys(spec.analysis_states)]
        if wanted and {state.value for state in wanted} != _ALL_STATES:
            bind_vars["states"] = analysis_state_bind_values(stored_states_for_display(wanted))
            bind_vars["displayed_states"] = [state.value for state in wanted]
            bind_vars["in_progress_state"] = DiaryAnalysisState.IN_PROGRESS.value
            bind_vars["requested_state"] = DiaryAnalysisState.REQUESTED.value
            bind_vars["none_state"] = DiaryAnalysisState.NONE.value
            bind_vars["now"] = (now or now_utc()).isoformat()
            clauses.append("FILTER doc.analysis_state IN @states")
            clauses.append(
                "LET displayed_analysis_state = ("
                "doc.analysis_state == @in_progress_state "
                "AND (doc.analysis_lease_expires_at == null OR doc.analysis_lease_expires_at <= @now)"
                ") ? @requested_state : NOT_NULL(doc.analysis_state, @none_state)"
            )
            clauses.append("FILTER displayed_analysis_state IN @displayed_states")

        if spec.plant_key:
            bind_vars["plant_key"] = spec.plant_key
            clauses.append("FILTER doc.plant_key == @plant_key")

        if spec.entry_type:
            bind_vars["entry_type"] = DiaryEntryType(spec.entry_type).value
            clauses.append("FILTER doc.entry_type == @entry_type")

        if spec.tag:
            # Case-insensitive membership. ``NOT_NULL`` guards the entries that
            # carry no ``tags`` attribute at all — iterating ``null`` would raise
            # instead of simply not matching.
            bind_vars["tag"] = spec.tag.lower()
            clauses.append(
                "FILTER LENGTH(FOR entry_tag IN NOT_NULL(doc.tags, []) "
                "FILTER LOWER(entry_tag) == @tag LIMIT 1 RETURN 1) > 0"
            )

        if spec.created_from is not None:
            bind_vars["created_from"] = _day_bounds_ms(spec.created_from, end_of_day=False)
            clauses.append("FILTER doc.created_at != null AND DATE_TIMESTAMP(doc.created_at) >= @created_from")

        if spec.created_to is not None:
            # Exclusive upper bound at the start of the *next* day, so the whole
            # of ``to`` is included whatever time of day an entry carries.
            bind_vars["created_before"] = _day_bounds_ms(spec.created_to, end_of_day=True)
            clauses.append("FILTER doc.created_at != null AND DATE_TIMESTAMP(doc.created_at) < @created_before")

        if spec.search:
            # ``escape_aql_like`` is the repository-wide SSOT for this: without it
            # a term containing ``%`` matches everything and one containing ``_``
            # matches any single character — a search that quietly answers a
            # different question than the one asked.
            bind_vars["search"] = f"%{escape_aql_like(spec.search)}%"
            clauses.append(
                'FILTER LIKE(NOT_NULL(doc.title, ""), @search, true) OR LIKE(NOT_NULL(doc.text, ""), @search, true)'
            )

        if spec.species_key:
            # The species hangs on the plant, not on the entry, so this one needs
            # a join — in AQL, not in the caller: a join done after paging filters
            # a page instead of the result set. The plant is restricted to the
            # same tenant, mirroring the tenant-scoped lookup the row labels use.
            bind_vars["species_key"] = spec.species_key
            clauses.append(f'LET overview_plant = DOCUMENT("{col.PLANT_INSTANCES}", doc.plant_key)')
            clauses.append(
                "FILTER overview_plant != null "
                "AND overview_plant.tenant_key == @tenant_key "
                "AND overview_plant.species_key == @species_key"
            )

        return " ".join(clauses), bind_vars
