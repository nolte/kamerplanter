from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    DiaryAnalysisState,
    DiaryEntryType,
    DiaryEnvironmentOrigin,
    DiaryEnvironmentStatus,
)
from app.domain.models.plant_diary_entry import DiaryAnalysis, PlantDiaryEntry
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_diary_service import PlantDiaryService, effective_analysis_state

# REQ-013 §2.3 — five photos per entry. The bound is repeated on the domain
# model (``PlantDiaryEntry.photo_refs``), which is where it actually binds: these
# schemas only cover the two HTTP routes, and REQ-050 §4.4 turns each reference
# into an image block for an external model. ``photo_refs`` is otherwise
# *unvalidated* input — the identity, tenant, category and authorship of every
# referenced attachment are checked server-side in
# :meth:`~app.domain.services.plant_diary_service.PlantDiaryService.create_entry`
# (SEC-003), not here: a schema cannot look a document up.
MAX_PHOTO_REFS = 5


class DiaryEnvironmentReadingResponse(BaseModel):
    """REQ-013 §2.3a — one machine-read value of the entry's environment snapshot.

    Read-only in every direction: it appears in responses and in nothing a client
    may send. See :class:`~app.domain.models.plant_diary_entry.DiaryEnvironmentReading`
    for why this is a list of provenance-carrying records instead of more keys in
    ``measurements``.
    """

    metric_type: str
    value: float
    unit: str | None
    #: REQ-005 §2 provenance (``ha_auto``, ``mqtt_auto``, ``manual``, …), or the
    #: weather adapter's own source name for an ``origin: weather`` reading.
    source: str
    #: When the reading was **measured** — regularly older than ``created_at``.
    measured_at: datetime
    sensor_key: str | None
    origin: DiaryEnvironmentOrigin


class DiaryEntryCreateRequest(BaseModel):
    entry_type: DiaryEntryType
    title: str | None = Field(default=None, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    photo_refs: list[str] = Field(default_factory=list, max_length=MAX_PHOTO_REFS)
    tags: list[str] = Field(default_factory=list)
    measurements: dict | None = None
    #: REQ-013 §2.3a — the author's opt-out from the environment snapshot.
    #:
    #: This says whether the server should **look**, never what it should store.
    #: The readings themselves are resolved from the plant's own location and are
    #: absent from this schema on purpose: a value the client can write is a value
    #: the client can invent, and this one is meant to be evidence. Opting out
    #: stores an empty snapshot flagged ``opted_out``, which is a different
    #: statement from "nothing covers this plant".
    capture_environment: bool = True


class DiaryEntryUpdateRequest(BaseModel):
    entry_type: DiaryEntryType | None = None
    title: str | None = Field(default=None, max_length=200)
    text: str | None = Field(default=None, min_length=1, max_length=5000)
    photo_refs: list[str] | None = Field(default=None, max_length=MAX_PHOTO_REFS)
    tags: list[str] | None = None
    measurements: dict | None = None


# REQ-050: the analysis fields are deliberately absent from both request schemas
# above. Every state transition of the analysis state machine (§2.2) has its own
# guarded endpoint/tool — marking, claiming with a CAS lease, submitting a result.
# Letting the generic entry update carry `analysis_state` would give any writer a
# way to jump the machine (claim without a lease, fake a `completed`) past the
# permission and lease checks that make the transitions safe.


class DiaryEntryResponse(BaseModel):
    key: str
    plant_key: str
    entry_type: DiaryEntryType
    title: str | None
    text: str
    photo_refs: list[str]
    tags: list[str]
    measurements: dict | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    # REQ-013 §2.3a — read-only projection of the environment snapshot. Defaults
    # mirror the domain model, so an entry stored before this feature serialises
    # as "nothing was attempted" instead of failing the response model.
    #
    #: The machine-read conditions at the moment the entry was created. Strictly
    #: separate from ``measurements`` above: that dict is the grower's own,
    #: free-form and unprovenanced, and merging the two would destroy the only
    #: thing that makes either readable as evidence a year later.
    environment: list[DiaryEnvironmentReadingResponse] = Field(default_factory=list)
    environment_captured_at: datetime | None = None
    #: What an empty ``environment`` *means* — see
    #: :class:`~app.common.enums.DiaryEnvironmentStatus`. Without it a client
    #: cannot tell "no sensor covers this plant" from "the capture failed".
    environment_status: DiaryEnvironmentStatus = DiaryEnvironmentStatus.NOT_ATTEMPTED

    # REQ-050 §5 — read-only projection of the analysis state machine and its
    # result. Defaults mirror the domain model so an entry stored before REQ-050
    # serialises as "not marked" instead of failing the response model (AK-26).

    #: The state the entry is **actually** in, not the one that happens to be
    #: stored: an entry whose agent lease has run out reads as ``requested``,
    #: because it is back in the work queue and every agent may pick it up
    #: (§2.2, AK-06). The correction is
    #: :func:`~app.domain.services.plant_diary_service.effective_analysis_state`
    #: — the same function the overview row uses, so the two views of one entry
    #: cannot disagree.
    #:
    #: The *stored* value is deliberately **not** published a second time. It
    #: stays derivable from the lease fields below, which are projected raw: a
    #: ``requested`` entry that still names an ``analysis_claimed_by`` with an
    #: ``analysis_lease_expires_at`` in the past is exactly the crashed-agent
    #: case. A second state field would be a second projection of one truth —
    #: which is the defect this pair of fields exists to close.
    analysis_state: DiaryAnalysisState = DiaryAnalysisState.NONE
    analysis_requested_at: datetime | None = None
    analysis_requested_by: str | None = None
    analysis_claimed_at: datetime | None = None
    analysis_claimed_by: str | None = None
    analysis_lease_expires_at: datetime | None = None
    analysis: DiaryAnalysis | None = None
    analysis_error: str | None = None

    #: §7.2 evaluated **server-side** for the user of *this* request (AK-18a).
    #:
    #: A display aid, never an authorisation: the marking endpoints re-evaluate
    #: the identical rule and refuse an entry whose flag said ``false``,
    #: whatever the client believed. It is per-user and per-entry — the same
    #: document answers ``true`` for its author and ``false`` for another
    #: grower — so it is required here rather than defaulted; a default would
    #: be the one value that is wrong for half the callers.
    can_request_analysis: bool

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "8271634",
                    "plant_key": "5512099",
                    "entry_type": "problem",
                    "title": "Braune Flecken unten",
                    "text": "Seit dem Umtopfen hängen die unteren Blätter, Substrat riecht sauer.",
                    "photo_refs": ["01HQ8X9V3J7P5K2N4M6T8R0S2W", "01HQ8X9V3J7P5K2N4M6T8R0S2X"],
                    "tags": ["blatt", "substrat"],
                    "measurements": {"height_cm": 84, "leaf_count": 22},
                    "created_by": "4471023",
                    "created_at": "2026-08-03T18:22:11Z",
                    "updated_at": "2026-08-03T18:22:11Z",
                    "environment": [
                        {
                            "metric_type": "temperature_celsius",
                            "value": 31.2,
                            "unit": "°C",
                            "source": "ha_auto",
                            "measured_at": "2026-08-03T18:21:44Z",
                            "sensor_key": "7710455",
                            "origin": "location",
                        },
                        {
                            "metric_type": "humidity_percent",
                            "value": 28.0,
                            "unit": "%",
                            "source": "ha_auto",
                            "measured_at": "2026-08-03T18:21:44Z",
                            "sensor_key": "7710456",
                            "origin": "location",
                        },
                    ],
                    "environment_captured_at": "2026-08-03T18:22:11Z",
                    "environment_status": "captured",
                    "analysis_state": "completed",
                    "analysis_requested_at": "2026-08-04T07:05:00Z",
                    "analysis_requested_by": "4471023",
                    "analysis_claimed_at": "2026-08-04T07:10:00Z",
                    "analysis_claimed_by": "goose-laptop",
                    "analysis_lease_expires_at": "2026-08-04T07:25:00Z",
                    "analysis": {
                        "summary": "Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
                        "findings": [
                            {
                                "label": "Staunässe / Wurzelstress",
                                "confidence": 0.72,
                                "rationale": (
                                    "Saurer Substratgeruch und hängende untere Blätter kurz nach dem Umtopfen."
                                ),
                            }
                        ],
                        "recommended_actions": ["Substrat abtrocknen lassen", "Drainage prüfen"],
                        "analyzed_photo_ids": ["01HQ8X9V3J7P5K2N4M6T8R0S2W", "01HQ8X9V3J7P5K2N4M6T8R0S2X"],
                        "model": "claude-opus-5",
                        "recipe_version": "1.0.0",
                        "analyzed_at": "2026-08-04T07:14:52Z",
                        "disclaimer": (
                            "Diese Einschätzung stammt von einem Sprachmodell, ist eine Hypothese "
                            "und ersetzt keine fachliche Prüfung."
                        ),
                    },
                    "analysis_error": None,
                    "can_request_analysis": True,
                }
            ]
        }
    )


class RunDiaryEntryResponse(BaseModel):
    plant_key: str
    plant_id: str
    plant_name: str | None
    diary_entry: DiaryEntryResponse


def diary_entry_response(entry: PlantDiaryEntry, *, can_request_analysis: bool) -> DiaryEntryResponse:
    """Project a domain entry onto its API response.

    Shared by the run-scoped and the standalone (REQ-013 §4.7) diary routers so
    the two paths cannot drift apart in what they expose — an entry read through
    ``/planting-runs/…`` and the same entry read through ``/plant-instances/…``
    must be the same document, field for field.

    **The state is the displayed one.** ``analysis_state`` goes through
    :func:`~app.domain.services.plant_diary_service.effective_analysis_state`,
    the same function the tenant-wide overview uses. Projecting the stored value
    here was a real divergence: an entry whose agent had crashed showed "wird
    analysiert" on the plant's diary tab and "wartet auf Analyse" in the
    overview — one truth, two answers, and the tab's was the false one, because
    the entry was demonstrably not being analysed but sitting in the work queue
    (AK-06).

    Reading never writes: the stored ``in_progress`` stays until the next write
    touches the entry (``PlantDiaryService._release_expired_lease``), and the
    work queue finds stale entries on its own.

    ``can_request_analysis`` is keyword-only and has **no default** on purpose.
    It is a per-user verdict, so there is no value that is right for every
    caller; forcing every construction site to name it is what stops a listing
    from shipping one blanket answer for every row. Use
    :func:`diary_entry_response_for_caller` unless a test constructs the
    projection directly.
    """
    return DiaryEntryResponse(
        key=entry.key or "",
        plant_key=entry.plant_key,
        entry_type=entry.entry_type,
        title=entry.title,
        text=entry.text,
        photo_refs=entry.photo_refs,
        tags=entry.tags,
        measurements=entry.measurements,
        created_by=entry.created_by,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        # REQ-013 §2.3a — read-only; captured on create and never re-derived.
        environment=[DiaryEnvironmentReadingResponse(**r.model_dump()) for r in entry.environment],
        environment_captured_at=entry.environment_captured_at,
        environment_status=entry.environment_status,
        # REQ-050 §5 — read-only; transitions never run through the entry CRUD.
        analysis_state=effective_analysis_state(entry),
        analysis_requested_at=entry.analysis_requested_at,
        analysis_requested_by=entry.analysis_requested_by,
        analysis_claimed_at=entry.analysis_claimed_at,
        analysis_claimed_by=entry.analysis_claimed_by,
        analysis_lease_expires_at=entry.analysis_lease_expires_at,
        analysis=entry.analysis,
        analysis_error=entry.analysis_error,
        can_request_analysis=can_request_analysis,
    )


def diary_entry_response_for_caller(
    entry: PlantDiaryEntry,
    *,
    diary_service: PlantDiaryService,
    ctx: TenantContext,
) -> DiaryEntryResponse:
    """Project ``entry`` for the user behind *this* request.

    The single entry point of every diary endpoint on both prefixes. It exists
    so the §7.2 verdict is evaluated where the entry is projected instead of
    being an argument a caller might forget, mis-hoist out of a loop, or fill
    with a constant.

    The rule itself is not reimplemented here: it is
    :meth:`PlantDiaryService.evaluate_request_permission` — the same call the
    overview row makes (``api/v1/diary/tenant_router.py``) and the same one the
    marking endpoint enforces (AK-18a).
    """
    permission = diary_service.evaluate_request_permission(entry, user_key=ctx.user_key, role=ctx.role)
    return diary_entry_response(entry, can_request_analysis=permission.allowed)
