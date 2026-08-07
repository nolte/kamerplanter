"""REQ-050 §4 — the five diary AI-analysis tools (REQ-033 §2.2a).

This module *is* the interface to the separate ``kamerplanter-goose`` repository:
a recipe is written against REQ-050 §4 alone, without ever reading this file, so
every ``data`` key below is a published contract rather than an implementation
detail. Renaming one is a breaking change for a repository that cannot be
grepped from here.

The five tools, and the order an agent uses them in (§3):

1. :class:`ListPendingDiaryAnalyses` — the work queue. Carries **no** free text
   and **no** images (§7.3, AK-04): the queue is not yet a transmission of
   content; content flows only once an entry is claimed and fetched on purpose.
2. :class:`ClaimDiaryAnalysis` — take one entry exclusively (lease + CAS).
3. :class:`GetDiaryEntry` — the entry, its plant context and any previously
   stored analysis, **without** image data (§4.3), so an agent can read the text
   without spending its token budget on photos it may not need.
4. :class:`GetDiaryEntryPhotos` — the photos as MCP image content blocks.
5. :class:`SubmitDiaryAnalysis` — write the result back and end the claim.

Two further tools share the module but **not** the contract; both belong to
REQ-033 §2.1/§2.2 and are irrelevant to the analysis recipe:

* :class:`AddPlantDiaryEntry` lets an agent *document* an observation rather
  than analyse one (REQ-050 §9, O-04 — decided yes). It touches none of the
  analysis fields, and writing an entry does not enqueue it: marking is a user
  action (REQ-050 §1.3), so an agent cannot create work for itself.
* :class:`ListDiaryEntries` browses what has been recorded — the read path the
  other five never offered, since the queue shows only marked entries and
  ``get_diary_entry`` needs a key one already holds.

**No state machine lives here.** Claiming, the lease, the compare-and-set and the
server-side disclaimer all belong to :mod:`app.domain.services.plant_diary_service`;
these tools are the typed, tenant-bound surface over it. The domain errors already
carry the published contract codes (``conflict.already_claimed`` …) **and** their
``details`` object, and the transport copies both by attribute rather than by
class (``_tool_error_result`` in ``app/api/v1/mcp/router.py``) — so they fly
straight to the recipe and nothing is re-wrapped or translated on the way out.
"""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, date, datetime
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from app.common.datetimes import ensure_aware_utc, now_utc
from app.common.enums import DiaryAnalysisState, DiaryEntryType, McpPermission
from app.common.exceptions import DiaryAnalysisValidationError, KamerplanterError, NotFoundError
from app.config.settings import settings
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_MIME_TYPE, can_render, metadata_keys
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter
from app.domain.models.mcp import McpToolResponse
from app.domain.models.plant_diary_entry import DiaryAnalysis, PlantDiaryEntry
from app.domain.services.plant_diary_service import (
    ANALYSIS_DISCLAIMER,
    DEFAULT_LEASE_SECONDS,
    derive_lease_token,
    effective_analysis_state,
)
from app.mcp_server.base import (
    McpToolError,
    TenantToolInput,
    ToolBase,
    WriteToolBase,
    WriteToolInput,
    image_content_index,
    mcp_tool,
)
from app.mcp_server.context import ToolContext

logger = structlog.get_logger()

#: The two renditions §4.4 lets an agent ask for. 128 px exists (NFR-013 §8.2)
#: but is deliberately not offered: it is a grid avatar, useless for a leaf
#: diagnosis, and offering it would invite a recipe to "save tokens" into an
#: unusable answer.
DELIVERABLE_RENDITION_SIZES: tuple[int, ...] = (512, 1280)

#: Default rendition (§4.4). 1280 px is enough for a leaf diagnosis and a
#: fraction of the cost of an original.
DEFAULT_RENDITION_SIZE = 1280

#: ``pending`` status for a rendition that does not exist *yet* (§4.4, AK-09).
#: Generation is kicked off and the agent may retry later.
PHOTO_STATUS_THUMBNAIL_PENDING = "thumbnail_pending"

#: ``pending`` status for a photo that will *never* render — the attachment
#: record is gone, or its type is not renderable. See :class:`GetDiaryEntryPhotos`
#: for why this is not reported as ``thumbnail_pending``.
PHOTO_STATUS_UNAVAILABLE = "unavailable"

#: ``photos`` status of a rendition that actually travelled in the response.
PHOTO_STATUS_DELIVERED = "delivered"


# ── Contract plumbing ─────────────────────────────────────────────────────────
def _iso_z(value: datetime | str | None) -> str | None:
    """Render a timestamp as ISO-8601 UTC with a ``Z`` suffix, or ``None``.

    §4.0 pins the spelling: "Zeitangaben sind durchgängig ISO-8601 in UTC mit
    Z-Suffix". Python's own ``isoformat()`` writes ``+00:00``, which is the same
    instant but not the same string — and a recipe that string-compares or
    regex-matches timestamps would see a contract violation. Formatting happens
    here rather than being left to the JSON encoder, which knows nothing about
    this requirement.
    """

    moment = ensure_aware_utc(value)
    if moment is None:
        return None
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _iso_date(value: date | datetime | str | None) -> str | None:
    """Render a calendar date (``planted_on``) as ``YYYY-MM-DD``, or ``None``."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _base64_length(raw_bytes: int) -> int:
    """Base-64 size of ``raw_bytes`` bytes, without encoding them twice.

    The §4.4 ceiling is measured on the **encoded** payload, because that is what
    travels and what a model's context pays for. Computing it arithmetically
    keeps the guard cheap enough to run before anything is encoded.
    """

    return 4 * ((raw_bytes + 2) // 3)


def _max_image_payload_bytes() -> int:
    """The configured Base-64 payload ceiling of one photo call (§4.4).

    No clamping and no "off" switch (SEC-008). This used to read
    ``max(int(...), 0)`` while the guard returned early on a non-positive
    ceiling, which made ``MCP_MAX_IMAGE_PAYLOAD_MB=0`` mean *unlimited* — the
    opposite of what an operator who sets zero wants. The bound now lives on the
    setting (``ge=1``), so an instance configured that way refuses to start
    rather than quietly serving without a ceiling.
    """

    return int(settings.mcp_max_image_payload_mb) * 1024 * 1024


def _dispatch_thumbnail_generation(attachment_id: str, tenant_key: str) -> None:
    """Kick off the missing rendition and never fail the read for it (AK-09).

    Mirrors the lazy regeneration of ``GET /attachments/{id}/thumbnails/{size}``.
    A broker outage must not turn a successful photo read into an error: the
    photo is already reported as ``thumbnail_pending``, and the worst case of a
    lost trigger is that the agent's retry re-issues it.
    """

    try:
        from app.tasks.storage_tasks import generate_thumbnails

        generate_thumbnails.delay(attachment_id, tenant_key)
    except Exception as exc:  # noqa: BLE001 — a dispatch failure is not a read failure
        logger.warning(
            "diary_photo_thumbnail_dispatch_failed",
            attachment_id=attachment_id,
            tenant_key=tenant_key,
            reason=type(exc).__name__,
        )


async def _collect(stream: AsyncIterator[bytes]) -> bytes:
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)


# ── Plant context resolution ──────────────────────────────────────────────────
def _load_plant(ctx: ToolContext, plant_key: str) -> Any | None:
    """Load the entry's plant inside the acting tenant, or ``None``.

    A diary entry whose plant has been removed must still be readable — the entry
    is the unit of analysis, the plant only its context. Failing the whole call
    over a dangling reference would take a perfectly analysable entry out of
    circulation.
    """

    if not plant_key:
        return None
    try:
        return ctx.plant_service.get_plant(plant_key, tenant_key=ctx.tenant_key)
    except KamerplanterError:
        return None


def _species_name(ctx: ToolContext, species_key: str | None, cache: dict[str, str | None]) -> str | None:
    """Resolve a species' scientific name, memoised across one call."""

    if not species_key:
        return None
    if species_key not in cache:
        try:
            cache[species_key] = getattr(ctx.species_service.get_species(species_key), "scientific_name", None)
        except KamerplanterError:
            cache[species_key] = None
    return cache[species_key]


def _cultivar_name(ctx: ToolContext, cultivar_key: str | None) -> str | None:
    if not cultivar_key:
        return None
    try:
        return getattr(ctx.species_service.get_cultivar(cultivar_key), "name", None)
    except KamerplanterError:
        return None


def _location_name(ctx: ToolContext, location_key: str | None) -> str | None:
    if not location_key:
        return None
    try:
        return getattr(ctx.site_service.get_location(location_key, ctx.tenant_key), "name", None)
    except KamerplanterError:
        return None


def _current_phase_name(ctx: ToolContext, plant: Any) -> str | None:
    """Human-readable name of the plant's current phase, or ``None``.

    §4.3 wants the phase *name* ("flowering"), not the key. Resolution spans two
    key-spaces (PhaseSequenceEntry and the legacy GrowthPhase), which
    ``PhaseService.get_current_phase`` already reconciles — reimplementing that
    here would be a third reading of the same data.
    """

    if not getattr(plant, "current_phase_key", None):
        return None
    try:
        current = ctx.phase_service.get_current_phase(plant.key)
    except KamerplanterError, AttributeError, RuntimeError:
        return plant.current_phase_key
    return current.get("phase") or plant.current_phase_key


def _plant_context(ctx: ToolContext, entry: PlantDiaryEntry) -> dict[str, Any]:
    """The ``plant`` object of §4.3 — every key always present.

    "Felder des ``plant``-Objekts, die am Datensatz fehlen, kommen als ``null``,
    nicht als ausgelassener Schlüssel" (§4.3). That also covers the case where the
    plant cannot be resolved at all: the shape stays identical, the values go
    ``null``. A recipe therefore never has to distinguish "key absent" from "value
    unknown".
    """

    plant = _load_plant(ctx, entry.plant_key)
    if plant is None:
        return {
            "plant_key": entry.plant_key or None,
            "plant_name": None,
            "instance_id": None,
            "species_key": None,
            "species_name": None,
            "cultivar_key": None,
            "cultivar_name": None,
            "current_phase": None,
            "phase_started_at": None,
            "location_name": None,
            "planted_on": None,
        }
    return {
        "plant_key": plant.key or entry.plant_key,
        "plant_name": plant.plant_name,
        "instance_id": plant.instance_id,
        "species_key": plant.species_key,
        "species_name": _species_name(ctx, plant.species_key, {}),
        # The key next to the name: ``get_cultivar`` takes a key, and the name
        # alone left an agent holding a label it could not look anything up with.
        # Same reason ``species_key`` sits beside ``species_name``.
        "cultivar_key": plant.cultivar_key,
        "cultivar_name": _cultivar_name(ctx, plant.cultivar_key),
        "current_phase": _current_phase_name(ctx, plant),
        "phase_started_at": _iso_z(plant.current_phase_started_at),
        "location_name": _location_name(ctx, plant.location_key),
        "planted_on": _iso_date(plant.planted_on),
    }


# ── §4.1 list_pending_diary_analyses ──────────────────────────────────────────
@mcp_tool(name="list_pending_diary_analyses", permission=McpPermission.READ)
class ListPendingDiaryAnalyses(ToolBase):
    """List diary entries waiting for AI analysis — no free text, no images."""

    class Input(TenantToolInput):
        # No ``le=100`` here on purpose: the ceiling lives in
        # ``PlantDiaryService.list_pending_analyses`` (MAX_PENDING_LIMIT) and is
        # raised as ``validation.error`` with ``details.field = "limit"``.
        # Duplicating it in the schema would mean two places to change and a
        # generic pydantic message instead of the contract's.
        limit: int = Field(
            default=20,
            description="Maximum number of entries to return (1-100). Above 100 the call fails with validation.error.",
        )
        include_stale: bool = Field(
            default=True,
            description="Also list entries whose analysis lease has expired and that are claimable again.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entries, total = ctx.plant_diary_service.list_pending_analyses(
            ctx.tenant_key,
            limit=args.limit,
            include_stale=args.include_stale,
        )

        species_cache: dict[str, str | None] = {}
        plant_cache: dict[str, Any | None] = {}
        items: list[dict[str, Any]] = []
        # Order is the repository's (``SORT doc.analysis_requested_at ASC``,
        # AK-04) and is passed through untouched — re-sorting here would put a
        # second, silently diverging opinion on the queue's order.
        for entry in entries:
            plant = plant_cache.get(entry.plant_key, ...)
            if plant is ...:
                plant = _load_plant(ctx, entry.plant_key)
                plant_cache[entry.plant_key] = plant
            items.append(
                {
                    "entry_key": entry.key,
                    "plant_key": entry.plant_key or None,
                    "plant_name": getattr(plant, "plant_name", None),
                    "species_name": _species_name(ctx, getattr(plant, "species_key", None), species_cache),
                    "entry_type": str(entry.entry_type),
                    "title": entry.title,
                    "created_at": _iso_z(entry.created_at),
                    "requested_at": _iso_z(entry.analysis_requested_at),
                    "photo_count": len(entry.photo_refs),
                    # The *effective* state (§2.5.2): an entry whose lease ran out
                    # is claimable again, and reporting the stored "in_progress"
                    # would tell the agent not to touch the very entry the queue
                    # just handed it.
                    "analysis_state": str(effective_analysis_state(entry)),
                }
            )

        # No ``text``, no ``photo_refs``, no image content — §7.3 / AK-04.
        return self._response(
            summary=f"{total} diary entries are waiting for analysis ({len(items)} returned).",
            data={"entries": items, "total": total},
            links=[ctx.ui_link("/diary")],
        )


# ── §4.2 claim_diary_analysis ─────────────────────────────────────────────────
@mcp_tool(name="claim_diary_analysis", permission=McpPermission.WRITE)
class ClaimDiaryAnalysis(WriteToolBase):
    """Claim a diary entry exclusively for analysis (lease + compare-and-set)."""

    class Input(WriteToolInput):
        entry_key: str = Field(description="Key of the diary entry to claim.")
        worker_id: str = Field(
            description="Free-form identifier of the claiming agent; stored as analysis_claimed_by.",
        )
        lease_seconds: int = Field(
            default=DEFAULT_LEASE_SECONDS,
            description="How long the claim is held (max 3600). Above that the call fails with validation.error.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        _require_claim_arguments(args.worker_id, args.lease_seconds)
        entry = ctx.plant_diary_service.get_entry_for_tenant(args.entry_key, ctx.tenant_key)
        return self._response(
            summary=(
                f"Would claim diary entry '{args.entry_key}' for '{args.worker_id.strip()}' "
                f"({args.lease_seconds}s lease, {len(entry.photo_refs)} photos)."
            ),
            data={
                "entry_key": entry.key,
                "photo_count": len(entry.photo_refs),
                "lease_seconds": args.lease_seconds,
                # No lease_token: nothing was claimed, and handing out a token
                # for a claim that did not happen would let a recipe submit
                # against an entry it does not hold.
                "analysis_state": str(effective_analysis_state(entry)),
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        claim = ctx.plant_diary_service.claim_analysis(
            args.entry_key,
            tenant_key=ctx.tenant_key,
            worker_id=args.worker_id,
            lease_seconds=args.lease_seconds,
        )
        return self._response(
            summary=f"Claimed diary entry '{claim.entry_key}' ({claim.photo_count} photos).",
            data={
                "entry_key": claim.entry_key,
                "lease_token": claim.lease_token,
                "lease_expires_at": _iso_z(claim.lease_expires_at),
                "photo_count": claim.photo_count,
            },
            links=[ctx.ui_link("/diary")],
        )


def _require_claim_arguments(worker_id: str, lease_seconds: int) -> None:
    """Apply §4.2's argument rules on the dry-run path.

    ``claim_analysis`` enforces the same rules before it writes, so the real call
    needs nothing here. A dry run never reaches the service, though, and a
    preview that answers "would claim" for an empty ``worker_id`` promises a call
    that will fail. The bounds come from the domain constants, so this stays an
    application of the rule and not a second copy of it.
    """

    from app.domain.services.plant_diary_service import MAX_LEASE_SECONDS, MAX_WORKER_ID_LENGTH

    worker = (worker_id or "").strip()
    if not worker:
        raise DiaryAnalysisValidationError("worker_id must not be empty.", field="worker_id")
    if len(worker) > MAX_WORKER_ID_LENGTH:
        raise DiaryAnalysisValidationError(
            f"worker_id must not exceed {MAX_WORKER_ID_LENGTH} characters.",
            field="worker_id",
        )
    if lease_seconds < 1 or lease_seconds > MAX_LEASE_SECONDS:
        raise DiaryAnalysisValidationError(
            f"lease_seconds must be between 1 and {MAX_LEASE_SECONDS}.",
            field="lease_seconds",
        )


# ── §4.3 get_diary_entry ──────────────────────────────────────────────────────
@mcp_tool(name="get_diary_entry", permission=McpPermission.READ)
class GetDiaryEntry(ToolBase):
    """Return one diary entry with its plant context — without image data.

    It also carries the **previously persisted** ``analysis`` / ``analysis_error``
    (§4.3): a repeat analysis (AK-21) reaches the earlier finding through no other
    tool, and an agent that cannot see it re-analyses blind.
    """

    class Input(TenantToolInput):
        entry_key: str = Field(description="Key of the diary entry to read.")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # A foreign or unknown entry raises NotFoundError, never a permission
        # error — otherwise the tool would confirm the existence of another
        # tenant's records (§4.0, AK-12).
        entry = ctx.plant_diary_service.get_entry_for_tenant(args.entry_key, ctx.tenant_key)

        data = {
            "entry_key": entry.key,
            "entry_type": str(entry.entry_type),
            "title": entry.title,
            "text": entry.text,
            "tags": list(entry.tags),
            # §4.3 types this as an open object. An entry without measurements
            # answers with an empty object rather than null, so a recipe can
            # iterate it unconditionally.
            "measurements": dict(entry.measurements or {}),
            "photo_refs": list(entry.photo_refs),
            "created_at": _iso_z(entry.created_at),
            # The bare ``user_key`` as stored — §4.3 shows no ``user/`` prefix,
            # because inventing a collection-qualified document id here would
            # promise a handle that exists nowhere in the data.
            "created_by": entry.created_by or None,
            "analysis_state": str(effective_analysis_state(entry)),
            # The previous result, in the §4.5 wire shape. Without it an agent
            # that picks up an already analysed entry (AK-21) could reach the
            # prior finding through *none* of the five tools: it would see
            # ``analysis_state: "completed"`` and re-analyse blind. ``None`` when
            # nothing has been recorded — a stable key, never an omitted one.
            "analysis": _analysis_payload(entry.analysis) if entry.analysis is not None else None,
            "analysis_error": entry.analysis_error,
            "plant": _plant_context(ctx, entry),
        }
        title = entry.title or (entry.text[:60] if entry.text else entry.key)
        return self._response(
            summary=f"Diary entry '{title}' ({entry.entry_type}, {len(entry.photo_refs)} photos).",
            data=data,
            links=[ctx.ui_link(f"/plants/{entry.plant_key}#diary")],
        )


# ── §4.4 get_diary_entry_photos ───────────────────────────────────────────────
@mcp_tool(name="get_diary_entry_photos", permission=McpPermission.READ)
class GetDiaryEntryPhotos(ToolBase):
    """Return a diary entry's photos as MCP image content blocks (WebP renditions).

    Three behaviours are load-bearing and each of them exists because the obvious
    alternative is worse:

    * **Renditions only, never the original** (§4.4, AK-07). An original may be
      25 MB and carries EXIF — GPS position and device identity — which the
      renditions provably do not (NFR-013 §8.2). The permission to hand a photo
      to a third-party model rests entirely on that property, so this path has no
      fallback to the original key: a missing rendition is reported, never
      substituted.
    * **Never silently truncated** (§4.4, AK-08). Over the payload ceiling the
      call fails with ``payload.too_large`` and names the photos and a rendition
      that would fit. A shortened success would let an agent conclude from four
      of six photos and never learn it had missed two.
    * **A missing rendition is not an error** (§4.4, AK-09). The photo moves to
      ``pending``, generation is kicked off, and the remaining photos are
      delivered. Failing hard would block an entry with four ready photos and one
      missing thumbnail entirely.
    """

    class Input(TenantToolInput):
        entry_key: str = Field(description="Key of the diary entry whose photos to fetch.")
        photo_ids: list[str] | None = Field(
            default=None,
            description="Attachment ids to fetch; omit for all photos of the entry.",
        )
        size: int = Field(
            default=DEFAULT_RENDITION_SIZE,
            description="Rendition edge size to deliver: 512 or 1280. Anything else fails with validation.error.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entry = ctx.plant_diary_service.get_entry_for_tenant(args.entry_key, ctx.tenant_key)
        if args.size not in DELIVERABLE_RENDITION_SIZES:
            raise DiaryAnalysisValidationError(
                f"size must be one of {list(DELIVERABLE_RENDITION_SIZES)}.",
                field="size",
            )
        requested = _select_photo_ids(entry, args.photo_ids)

        # The ceiling is handed *into* the loading loop rather than applied to
        # its result (SEC-004). Measuring afterwards bounded what left the
        # process, not what it did: the loop had already fetched and held every
        # rendition by then.
        ceiling = _max_image_payload_bytes()
        delivered, pending, payload_bytes = await _load_renditions(ctx, requested, args.size, ceiling=ceiling)
        if payload_bytes > ceiling:
            await _raise_payload_too_large(
                ctx,
                requested,
                size=args.size,
                ceiling=ceiling,
                measured=payload_bytes,
            )

        photos = [
            {
                "photo_id": photo_id,
                "status": PHOTO_STATUS_DELIVERED,
                # The index into the *content* array, not into ``photos`` — the
                # leading summary block already occupies index 0, and a further
                # text block later must not silently shift the mapping (§4.4).
                "content_index": image_content_index(position),
                "byte_size": len(raw),
            }
            for position, (photo_id, raw) in enumerate(delivered)
        ]
        summary = _photo_summary(len(photos), len(requested), args.size)
        return self._image_response(
            summary,
            images=[(raw, THUMBNAIL_MIME_TYPE) for _photo_id, raw in delivered],
            data={
                "entry_key": entry.key,
                "size": args.size,
                "photos": photos,
                "pending": pending,
            },
            links=[ctx.ui_link(f"/plants/{entry.plant_key}#diary")],
        )


def _photo_summary(delivered: int, requested: int, size: int) -> str:
    if requested == 0:
        return "This diary entry has no photos attached."
    if delivered == requested:
        return f"{delivered} of {requested} photos delivered ({size} px)."
    return f"{delivered} of {requested} photos delivered ({size} px); the rest are not available yet."


def _select_photo_ids(entry: PlantDiaryEntry, requested: Sequence[str] | None) -> list[str]:
    """Resolve the requested selection against the entry's own photos (§4.4).

    An id that does not hang on this entry is ``validation.error`` and not a
    silent omission: a recipe passing the wrong id would otherwise get a
    successful, empty answer and conclude the entry has no photo.

    **Repeats are collapsed (SEC-004).** The check used to be membership only,
    which said nothing about *how often* an id appeared: ``photo_ids:
    ["<valid-id>"] * 2000`` passed it and made the loader fetch the same
    rendition two thousand times. Deduplication also gives the selection its
    bound for free — every element must be one of the entry's own references,
    and an entry carries at most five (REQ-013 §2.3) — so the work of one call
    is bounded by the document rather than by the request body.

    The first occurrence keeps the caller's position: that order is the order the
    image content blocks travel in, and ``content_index`` refers to it.
    """

    if requested is None:
        return list(dict.fromkeys(entry.photo_refs))
    unknown = [photo_id for photo_id in requested if photo_id not in entry.photo_refs]
    if unknown:
        raise DiaryAnalysisValidationError(
            f"photo_ids contains ids that are not attached to this entry: {', '.join(unknown)}.",
            field="photo_ids",
        )
    return list(dict.fromkeys(requested))


async def _load_renditions(
    ctx: ToolContext,
    photo_ids: Sequence[str],
    size: int,
    *,
    ceiling: int,
) -> tuple[list[tuple[str, bytes]], list[dict[str, str]], int]:
    """Load one rendition per photo, sorting the misses into ``pending``.

    Never touches ``storage_key`` — only ``open_thumbnail_stream``, which reads
    the ``{ulid}_t{size}.webp`` object. There is deliberately no ``except
    NotFoundError: read the original`` branch anywhere in this module: that
    fallback would be invisible in the response and would ship EXIF-bearing
    originals to a language model (AK-07).

    **The payload budget is carried along and the loop stops the moment it is
    exceeded** (SEC-004). Summing afterwards limited what left the process, not
    what it assembled: every rendition of the selection was already fetched and
    held in memory before the ceiling had a say. Stopping early does not weaken
    AK-08 — the call still ends in ``payload.too_large`` and never in a
    shortened success — it only stops paying for bytes that were never going to
    travel. Returns the running total so the caller can decide without summing
    a second time.

    Renditions are also held against :func:`metadata_keys` before they are
    handed on; see :func:`_is_metadata_free`.
    """

    attachments = ctx.attachment_service
    delivered: list[tuple[str, bytes]] = []
    pending: list[dict[str, str]] = []
    payload_bytes = 0

    for photo_id in photo_ids:
        try:
            attachment = attachments.get_attachment(photo_id, ctx.tenant_key)
        except NotFoundError:
            # The attachment record is gone (or belongs elsewhere): no rendition
            # will ever appear, so promising ``thumbnail_pending`` would send the
            # agent into an endless retry loop.
            pending.append({"photo_id": photo_id, "status": PHOTO_STATUS_UNAVAILABLE})
            continue

        if not can_render(attachment.mime_type):
            pending.append({"photo_id": photo_id, "status": PHOTO_STATUS_UNAVAILABLE})
            continue

        try:
            raw = await _collect(await attachments.open_thumbnail_stream(attachment, size))
        except NotFoundError:
            # AK-09: not an error. Kick off generation and keep going — the other
            # photos of this entry are still perfectly analysable.
            pending.append({"photo_id": photo_id, "status": PHOTO_STATUS_THUMBNAIL_PENDING})
            _dispatch_thumbnail_generation(photo_id, ctx.tenant_key)
            continue

        if not _is_metadata_free(photo_id, raw):
            pending.append({"photo_id": photo_id, "status": PHOTO_STATUS_THUMBNAIL_PENDING})
            _dispatch_thumbnail_generation(photo_id, ctx.tenant_key)
            continue

        delivered.append((photo_id, raw))
        payload_bytes += _base64_length(len(raw))
        if payload_bytes > ceiling:
            # Nothing further is loaded: the answer is already decided.
            break

    return delivered, pending, payload_bytes


def _is_metadata_free(photo_id: str, raw: bytes) -> bool:
    """Assert on the delivery path that a rendition carries no EXIF/XMP/ICC.

    **This is a boundary assertion, not a fix for a demonstrated leak.** Every
    rendition this codebase has ever produced is metadata-free: the current
    generator enforces it in three layers and *fails closed*, and the
    pre-hardening generator produced clean WebP too, because Pillow's WebP
    encoder sources ``exif``/``xmp``/``icc_profile`` exclusively from the
    arguments of ``save()`` and never from the decoded image's ``info`` dict
    (``PIL/WebPImagePlugin._save``) — measured on the pinned Pillow 12.3.0
    against JPEG, PNG and WebP sources carrying EXIF, GPS, XMP and an ICC
    profile.

    It is asserted here anyway because this is the point where bytes leave the
    trust boundary (REQ-050 §4.4, §7.3: "die Zulässigkeit der Herausgabe hängt
    an der Rendition"), and objects in the bucket are not written *only* by this
    code — a restore, an operator copy or a future second producer is outside
    the generator's fail-closed guarantee. :func:`metadata_keys` documents itself
    as usable by exactly such callers, and it parses the container header only
    (no pixel decode): ~0.4 ms per rendition, against a storage round-trip that
    costs orders of magnitude more.

    A loaded rendition that fails is treated like a missing one — reported as
    ``thumbnail_pending`` and regenerated — never delivered. That is the same
    trade-off NFR-013 §8.2 already makes at generation time: §4.4 handles a
    missing rendition gracefully, while a rendition with GPS in it would reach a
    third-party model unnoticed.
    """

    leaked = metadata_keys(raw)
    if not leaked:
        return True
    logger.error(
        "diary_photo_rendition_metadata_leak",
        photo_id=photo_id,
        leaked_blocks=leaked,
        detail="Refused to deliver a rendition that still carries image metadata; regeneration dispatched.",
    )
    return False


async def _raise_payload_too_large(
    ctx: ToolContext,
    requested: Sequence[str],
    *,
    size: int,
    ceiling: int,
    measured: int,
) -> None:
    """Refuse an over-sized answer instead of shortening it (§4.4, AK-08).

    ``details.suggested_size`` names "die Rendition, mit der der Abruf passen
    würde" — so it is *measured*, not guessed: the smaller renditions are loaded
    and summed before one of them is recommended. Recommending 512 px on the
    assumption that it is small enough would send an agent into a second call
    that fails exactly like the first.

    ``details.photo_ids`` is the **requested selection**, not the subset that
    happened to be loaded before the budget ran out. It answers "which images did
    this call concern", which is stable and is what the agent has to change; the
    loaded subset would vary with the order the ceiling was crossed in and would
    under-report the call. ``payload_bytes`` is correspondingly the sum measured
    at the point the ceiling was crossed — a lower bound on the full selection,
    which is all that is needed to justify the refusal. Neither key is named by
    §4.4 beyond ``photo_ids`` and ``suggested_size``.
    """

    photo_ids = list(requested)
    suggested = await _largest_fitting_size(ctx, photo_ids, below=size, ceiling=ceiling)
    hint = (
        f" Retry with size={suggested}."
        if suggested is not None
        else " No offered rendition fits; request fewer photos per call."
    )
    raise McpToolError(
        "payload.too_large",
        (
            f"The {size} px renditions of {len(photo_ids)} photos exceed the {ceiling} byte "
            f"Base-64 ceiling (measured {measured} bytes before the read was stopped).{hint}"
        ),
        details={
            "photo_ids": photo_ids,
            # Present even when nothing fits — §4.0 wants a stable structure, so
            # the key carries an explicit null rather than disappearing.
            "suggested_size": suggested,
            "payload_bytes": measured,
            "max_payload_bytes": ceiling,
        },
    )


async def _largest_fitting_size(
    ctx: ToolContext,
    photo_ids: Sequence[str],
    *,
    below: int,
    ceiling: int,
) -> int | None:
    """The largest offered rendition below ``below`` whose payload fits, or ``None``."""

    attachments = ctx.attachment_service
    for candidate in sorted((s for s in DELIVERABLE_RENDITION_SIZES if s < below), reverse=True):
        total = 0
        fits = True
        for photo_id in photo_ids:
            try:
                attachment = attachments.get_attachment(photo_id, ctx.tenant_key)
                raw = await _collect(await attachments.open_thumbnail_stream(attachment, candidate))
            except NotFoundError:
                # A rendition that is missing costs nothing on the retry — it
                # would land in ``pending`` there, exactly as it would here.
                continue
            total += _base64_length(len(raw))
            if total > ceiling:
                fits = False
                break
        if fits:
            return candidate
    return None


# ── §4.5 submit_diary_analysis ────────────────────────────────────────────────
class DiaryFindingInput(BaseModel):
    """One finding an agent submits (§4.5).

    Deliberately unbounded here: ``label``/``rationale`` lengths and the
    ``confidence`` range are enforced by the domain model ``DiaryFinding``
    (REQ-050 §5), which is the single definition of "too long". Repeating the
    bounds in this schema would create a second one that drifts.
    """

    label: str
    confidence: float
    rationale: str


@mcp_tool(name="submit_diary_analysis", permission=McpPermission.WRITE)
class SubmitDiaryAnalysis(WriteToolBase):
    """Write an analysis result back to a claimed diary entry and end the claim."""

    class Input(WriteToolInput):
        entry_key: str = Field(description="Key of the claimed diary entry.")
        lease_token: str = Field(description="Lease token returned by claim_diary_analysis.")
        status: Literal["completed", "failed"] = Field(description="Outcome of the analysis.")
        summary: str | None = Field(
            default=None,
            description="One to three sentences, max 2000 characters. Required when status is 'completed'.",
        )
        findings: list[DiaryFindingInput] | None = Field(
            default=None,
            description="Up to 10 findings, each with label, confidence (0.0-1.0) and rationale.",
        )
        recommended_actions: list[str] | None = Field(
            default=None,
            description="Up to 10 concrete actions.",
        )
        analyzed_photo_ids: list[str] | None = Field(
            default=None,
            description="Up to 5 ids of the photos that actually went into the analysis.",
        )
        model: str = Field(default="", description="Model used, max 200 characters.")
        recipe_version: str = Field(default="", description="Version of the agent recipe, max 50 characters.")
        error: str | None = Field(
            default=None,
            description="Failure cause. Required when status is 'failed'.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entry = ctx.plant_diary_service.get_entry_for_tenant(args.entry_key, ctx.tenant_key)
        _require_live_claim(entry, args.lease_token)
        _require_submittable_payload(entry, args)
        return self._response(
            summary=f"Would record a '{args.status}' analysis for diary entry '{args.entry_key}'.",
            data={
                "entry_key": entry.key,
                "analysis_state": args.status,
                # The disclaimer is shown here too, so a dry run reveals that it
                # is the server's text and not the agent's (§4.5, AK-11).
                "disclaimer": ANALYSIS_DISCLAIMER,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        updated = ctx.plant_diary_service.submit_analysis(
            args.entry_key,
            tenant_key=ctx.tenant_key,
            lease_token=args.lease_token,
            status=args.status,
            summary=args.summary,
            findings=[finding.model_dump() for finding in (args.findings or [])],
            recommended_actions=list(args.recommended_actions or []),
            analyzed_photo_ids=list(args.analyzed_photo_ids or []),
            model=args.model,
            recipe_version=args.recipe_version,
            error=args.error,
        )

        data: dict[str, Any] = {
            "entry_key": updated.key,
            "analysis_state": str(updated.analysis_state),
        }
        if updated.analysis is not None and args.status == "completed":
            # Mirror back what was *persisted*, including the server-set
            # disclaimer (§4.5) — the agent should see what actually stands on
            # the entry, not an echo of what it sent.
            data["analysis"] = _analysis_payload(updated.analysis)
        else:
            data["analysis_error"] = updated.analysis_error
        return self._response(
            summary=f"Recorded a '{updated.analysis_state}' analysis for diary entry '{updated.key}'.",
            data=data,
            links=[ctx.ui_link(f"/plants/{updated.plant_key}#diary")],
        )


class DiaryMeasurementsInput(BaseModel):
    """The recognised quantities of ``measurements``, with the rest still open.

    **The problem this solves.** ``measurements`` was an open object —
    ``additionalProperties: true``, no declared properties — documented only by
    the example ``{'height_cm': 42, 'ph': 6.3}``. An agent reading the published
    ``inputSchema`` could learn neither the unit nor the spelling of any
    quantity, so a consuming spec had to *discard* ambiguous values. A number a
    reader must throw away is worse than no number.

    **The decision: declare the recognised keys, keep the object open.**
    ``extra="allow"`` means the JSON schema still carries
    ``additionalProperties: true``, so nothing that was writable before stops
    being writable. What changes is that the quantities a recipe is expected to
    reason over now appear in the schema **with their unit in the key name** and
    with the physical bounds that make a typo detectable.

    **Backward compatibility was the constraint that shaped the key set.** This
    module's own header warns that every published key is a contract for a
    repository that cannot be grepped from here, and the same is true in the
    other direction: entries already in the wild were written through the web
    UI's free-form key/value editor and through the REST schema whose example is
    ``{"height_cm": 84, "leaf_count": 22}``. So:

    * ``ph``, ``height_cm`` and ``leaf_count`` are declared **under the spelling
      that is already in the data**. Renaming them to a tidier form would have
      split every plant's history across two key sets — the read tools return
      ``measurements`` verbatim and cannot migrate what is stored.
    * ``ec_ms_cm``, ``temperature_c`` and ``humidity_percent`` are new: no
      established spelling existed for them in diary data, so the unit-bearing
      name used elsewhere in the codebase (``TankStateCreate.ec_ms_cm``) is
      adopted rather than inventing a third one.
    * Nothing is made **required**, and nothing outside this list is rejected.

    **Why only the MCP surface and not the REST request schema.** The two have
    genuinely different consumers. The REST path serves the UI's free-form editor,
    where a human types a label of their choosing; constraining it would break
    that editor for every key it does not know. The MCP path serves an agent that
    reads a JSON schema and has nobody to ask. Declaring the recognised set for
    the reader that needs it, while leaving the store open for the reader that
    does not, is the whole point of a typed surface over an open record.
    """

    model_config = {"extra": "allow"}

    ec_ms_cm: float | None = Field(
        default=None,
        ge=0,
        description="Electrical conductivity in mS/cm. Say in the text whether this is tank or runoff.",
    )
    ph: float | None = Field(default=None, ge=0, le=14, description="pH value, 0-14.")
    temperature_c: float | None = Field(default=None, description="Temperature in degrees Celsius.")
    humidity_percent: float | None = Field(default=None, ge=0, le=100, description="Relative humidity in percent.")
    height_cm: float | None = Field(default=None, ge=0, description="Plant height in centimetres.")
    leaf_count: int | None = Field(default=None, ge=0, description="Number of leaves counted.")


@mcp_tool(name="add_plant_diary_entry", permission=McpPermission.WRITE)
class AddPlantDiaryEntry(WriteToolBase):
    """Record a diary entry (observation, problem, measurement) for a plant."""

    class Input(WriteToolInput):
        plant_key: str = Field(description="Key of the plant instance the entry belongs to.")
        entry_type: DiaryEntryType = Field(
            default=DiaryEntryType.OBSERVATION,
            description="Kind of entry. Defaults to 'observation'.",
        )
        title: str | None = Field(default=None, max_length=200, description="Optional headline, max 200 characters.")
        text: str = Field(min_length=1, max_length=5000, description="The entry itself, 1 to 5000 characters.")
        tags: list[str] = Field(default_factory=list, description="Free-form tags.")
        measurements: DiaryMeasurementsInput | None = Field(
            default=None,
            description=(
                "Optional measured values. The recognised quantities carry their unit in the key "
                "(ec_ms_cm, ph, temperature_c, humidity_percent, height_cm, leaf_count); any further "
                "key is accepted unchanged. For a dose with EC and pH use record_feeding_event instead — "
                "it stores amount, EC, pH and the tank reference in fields a reader can rely on."
            ),
        )

        # The two length bounds are repeated from ``PlantDiaryEntry``, which is
        # where they actually bind. Declaring them here as well is what puts them
        # into the published ``inputSchema``: a recipe that only reads the schema
        # would otherwise discover them by being rejected. The REST request
        # schema repeats them for the same reason.

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-001: resolve + ownership-check the plant against the caller's
        # tenant before anything else, exactly as ConfirmCareTask does. A foreign
        # or missing key yields the project's 404 contract, never a 403.
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would add a '{args.entry_type}' diary entry to plant '{plant.key}'.",
            data={
                "plant_key": plant.key,
                "entry_type": str(args.entry_type),
                "title": args.title,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-001: same tenant-ownership gate as preview() before the write.
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        entry = PlantDiaryEntry(
            tenant_key=ctx.tenant_key,
            created_by=ctx.principal.account_key,
            entry_type=args.entry_type,
            title=args.title,
            text=args.text,
            tags=list(args.tags),
            # ``exclude_none`` so an unset recognised key is *absent* rather than
            # stored as an explicit null. Padding every entry with six nulls would
            # change what the read tools return for entries that measured nothing,
            # and ``{"ph": null}`` reads as "measured, result unknown" — which is
            # not what an omitted field means.
            measurements=args.measurements.model_dump(exclude_none=True) if args.measurements is not None else None,
        )
        # No ``run_key``: the entry hangs off the plant, so it surfaces in a run's
        # aggregation as soon as the plant belongs to one. Passing a run here
        # would refuse the standalone plant, which is the common case.
        created = ctx.plant_diary_service.create_entry(plant.key, entry, actor_role=ctx.role)
        return self._response(
            summary=f"Added a '{created.entry_type}' diary entry to plant '{plant.key}'.",
            data={
                "entry_key": created.key,
                "plant_key": created.plant_key,
                "entry_type": str(created.entry_type),
                "title": created.title,
                "created_at": _iso_z(created.created_at),
                # Stated rather than implied: writing an entry does not enqueue
                # it for analysis. Marking is a user action (§1.3) and there is
                # no tool for it — an agent that expects otherwise would poll
                # list_pending_diary_analyses forever.
                "analysis_state": str(created.analysis_state),
            },
            links=[
                ctx.api_link(f"/plant-instances/{created.plant_key}/diary"),
                ctx.ui_link("/tagebuch"),
            ],
        )


@mcp_tool(name="list_diary_entries", permission=McpPermission.READ)
class ListDiaryEntries(ToolBase):
    """Browse diary entries of the garden — by plant, type, tag or date range.

    The palette could reach a diary entry two ways before this: the analysis
    queue (marked entries only) and ``get_diary_entry`` (one key you already
    hold). Neither answers "what has been recorded about this plant", which is
    what a supply-history reading is built on.

    Two things this deliberately does **not** carry:

    * **No ``text``.** The row stops at title, tags and measurements; the free
      text needs ``get_diary_entry``. Same line ``list_pending_diary_analyses``
      draws (§7.3): a browsable list is a different exposure of observer prose
      than a single deliberate read, and nothing in the process specs needs the
      body to *select* an entry.
    * **No free-text search.** ``entry_type`` and ``tag`` select structurally.
      A search that matched against text this tool then refuses to return would
      be a half-open door — the REST overview keeps it for the UI, which does
      show the text.

    **Newest first, always.** The rows come back sorted by ``created_at``
    descending, with ``_key`` as the tiebreaker so paging cannot show one entry
    on two pages and another on none. This is part of the contract rather than
    an accident of the query: REQ-050's evidence ladder rates a measurement by
    how recent it is, so a recipe that reads the first row is entitled to the
    latest one. The order is the repository's and is passed through untouched —
    re-sorting here would be a second, silently diverging opinion on it.
    """

    class Input(TenantToolInput):
        plant_key: str | None = Field(default=None, description="Restrict to one plant instance.")
        species_key: str | None = Field(default=None, description="Restrict to plants of one species.")
        entry_type: DiaryEntryType | None = Field(
            default=None,
            description="Restrict to one kind of entry, e.g. 'measurement' for recorded values.",
        )
        tag: str | None = Field(default=None, description="Restrict to entries carrying this tag (case-insensitive).")
        analysis_state: list[DiaryAnalysisState] | None = Field(
            default=None,
            description="Restrict to these analysis states. Omit for every state.",
        )
        created_from: date | None = Field(default=None, description="Only entries created on or after this UTC day.")
        created_to: date | None = Field(default=None, description="Only entries created on or before this UTC day.")
        limit: int = Field(default=20, ge=1, le=100, description="Maximum number of entries to return.")
        offset: int = Field(default=0, ge=0, description="Number of entries to skip.")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entries, total = ctx.plant_diary_service.list_overview(
            ctx.tenant_key,
            DiaryOverviewFilter(
                analysis_states=tuple(args.analysis_state or ()),
                plant_key=args.plant_key,
                species_key=args.species_key,
                entry_type=args.entry_type,
                tag=args.tag,
                created_from=args.created_from,
                created_to=args.created_to,
            ),
            offset=args.offset,
            limit=args.limit,
        )

        # Labels are resolved per row, deduplicated per call. Worst case is a
        # page whose entries all sit on different plants: ``limit`` plant reads
        # plus up to ``limit`` species reads. That is the same bound the REST
        # overview carries, and it is bounded by ``limit`` rather than by the
        # tenant's diary — but this tool's ceiling is 100 where the analysis
        # queue's is 20, so the worst case here is five times theirs. Resolving
        # in the query instead would move the join into the repository, which is
        # a change to the shared read path, not to this tool.
        species_cache: dict[str, str | None] = {}
        plant_cache: dict[str, Any | None] = {}
        items: list[dict[str, Any]] = []
        for entry in entries:
            plant = plant_cache.get(entry.plant_key, ...)
            if plant is ...:
                plant = _load_plant(ctx, entry.plant_key)
                plant_cache[entry.plant_key] = plant
            items.append(
                {
                    "entry_key": entry.key,
                    "plant_key": entry.plant_key or None,
                    "plant_name": getattr(plant, "plant_name", None),
                    "species_name": _species_name(ctx, getattr(plant, "species_key", None), species_cache),
                    "entry_type": str(entry.entry_type),
                    "title": entry.title,
                    "tags": list(entry.tags),
                    # The reason this tool exists. REQ-050's evidence ladder puts a
                    # recorded EC or pH above every inferred signal, and a row
                    # without them would force one get_diary_entry per entry just
                    # to find out whether it carries any.
                    "measurements": dict(entry.measurements or {}),
                    "created_at": _iso_z(entry.created_at),
                    "photo_count": len(entry.photo_refs),
                    "analysis_state": str(effective_analysis_state(entry)),
                }
            )

        return self._response(
            summary=f"{len(items)} diary entries returned (of {total} matching).",
            data={"entries": items, "total": total, "offset": args.offset},
            links=[ctx.api_link("/diary"), ctx.ui_link("/tagebuch")],
        )


def _analysis_payload(analysis: DiaryAnalysis) -> dict[str, Any]:
    """The persisted result in the §4.5 wire shape."""

    return {
        "summary": analysis.summary,
        "findings": [
            {"label": f.label, "confidence": f.confidence, "rationale": f.rationale} for f in analysis.findings
        ],
        "recommended_actions": list(analysis.recommended_actions),
        "analyzed_photo_ids": list(analysis.analyzed_photo_ids),
        "model": analysis.model,
        "recipe_version": analysis.recipe_version,
        "analyzed_at": _iso_z(analysis.analyzed_at),
        "disclaimer": analysis.disclaimer,
    }


def _require_live_claim(entry: PlantDiaryEntry, lease_token: str) -> None:
    """Dry-run counterpart of the state + lease gate in ``submit_analysis`` (§4.5).

    Uses the very same exported ``derive_lease_token`` the service uses, so a
    preview cannot approve a token the real call would reject.
    """

    from app.common.enums import DiaryAnalysisState
    from app.common.exceptions import DiaryAnalysisLeaseExpiredError, DiaryAnalysisNotClaimedError
    from app.domain.services.plant_diary_service import lease_expired

    key = entry.key or ""
    if entry.analysis_state != DiaryAnalysisState.IN_PROGRESS:
        raise DiaryAnalysisNotClaimedError(key, str(entry.analysis_state))
    if lease_expired(entry):
        raise DiaryAnalysisLeaseExpiredError(key)
    expected = derive_lease_token(
        entry_key=key,
        claimed_by=entry.analysis_claimed_by or "",
        claimed_at=entry.analysis_claimed_at,
        lease_expires_at=entry.analysis_lease_expires_at,
    )
    if not hmac.compare_digest(expected, lease_token or ""):
        raise DiaryAnalysisLeaseExpiredError(key)


def _require_submittable_payload(entry: PlantDiaryEntry, args: Any) -> None:
    """Dry-run counterpart of the §4.5 payload validation (AK-22).

    Runs the payload through the *same* domain model the service persists, so the
    length limits and the confidence range have exactly one definition. Only the
    two rules the model cannot express — the mandatory summary/error and the
    "photo must hang on this entry" check — are applied explicitly.
    """

    from app.domain.services.plant_diary_service import MAX_ERROR_LENGTH, MAX_RECOMMENDED_ACTION_LENGTH

    if args.status == "failed":
        text = (args.error or "").strip()
        if not text:
            raise DiaryAnalysisValidationError("error is required when status is 'failed'.", field="error")
        if len(text) > MAX_ERROR_LENGTH:
            raise DiaryAnalysisValidationError(
                f"error must not exceed {MAX_ERROR_LENGTH} characters.",
                field="error",
            )
        return

    summary = (args.summary or "").strip()
    if not summary:
        raise DiaryAnalysisValidationError("summary is required when status is 'completed'.", field="summary")

    photo_ids = list(args.analyzed_photo_ids or [])
    unknown = [photo_id for photo_id in photo_ids if photo_id not in entry.photo_refs]
    if unknown:
        raise DiaryAnalysisValidationError(
            f"analyzed_photo_ids contains ids that are not attached to this entry: {', '.join(unknown)}.",
            field="analyzed_photo_ids",
        )

    actions = list(args.recommended_actions or [])
    for action in actions:
        if len(action) > MAX_RECOMMENDED_ACTION_LENGTH:
            raise DiaryAnalysisValidationError(
                f"recommended_actions entries must not exceed {MAX_RECOMMENDED_ACTION_LENGTH} characters.",
                field="recommended_actions",
            )

    try:
        DiaryAnalysis(
            summary=summary,
            findings=[finding.model_dump() for finding in (args.findings or [])],
            recommended_actions=actions,
            analyzed_photo_ids=photo_ids,
            model=args.model,
            recipe_version=args.recipe_version,
            analyzed_at=now_utc(),
            disclaimer=ANALYSIS_DISCLAIMER,
        )
    except PydanticValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ())) or "analysis"
        raise DiaryAnalysisValidationError(f"{location}: {first.get('msg', 'invalid value')}") from exc


__all__ = [
    "DEFAULT_RENDITION_SIZE",
    "DELIVERABLE_RENDITION_SIZES",
    "PHOTO_STATUS_DELIVERED",
    "PHOTO_STATUS_THUMBNAIL_PENDING",
    "PHOTO_STATUS_UNAVAILABLE",
    "AddPlantDiaryEntry",
    "ClaimDiaryAnalysis",
    "DiaryFindingInput",
    "DiaryMeasurementsInput",
    "GetDiaryEntry",
    "GetDiaryEntryPhotos",
    "ListDiaryEntries",
    "ListPendingDiaryAnalyses",
    "SubmitDiaryAnalysis",
]
