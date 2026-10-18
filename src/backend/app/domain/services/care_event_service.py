"""The care log: create, correct, cancel and redact the events of a bed (REQ-053 §13, WP 4.1, #2400).

**The stable interface** other work packages build on — WP 3.2 (clearing), WP 3.4 (backfill), WP 4.3 (task
completion) and the consistency job of wave 8:

* :meth:`create` — a validated event is stored. ``origin=None`` is a *client* (HTTP): ``trigger`` is
  ``manual`` / ``observation``, the server-only categories are refused. A server caller passes a
  :class:`~app.domain.models.care_event.CareEventOrigin` (``trigger``, ``task_key``, ``source_ref``, the
  backfill window) — the fields no request body can carry (SR-009).
* :meth:`build_event` — the same validation and the same stored shape, *without* persisting: a caller that
  must write the event inside its own transaction (the atomic task completion, GP-FR-083) calls it, opens
  the transaction and writes with :func:`~app.data_access.arango.care_event_repository.write_care_event`.
* :meth:`supersede` — a correction as a new entry that keeps the predecessor readable (GP-FR-101).
* :meth:`void` — a cancellation; the lead any time, the author within ten minutes with ``reason = undo``.
* :meth:`redact` — the lead replaces the free texts of a whole supersede chain and deletes its photos (GP-FR-109).

**Ownership is resolved here, never in the router** (T-01…T-04, #2107). Every public method takes
``*, tenant_key: str`` without a default; the bed is resolved through
:mod:`~app.domain.services.location_ownership` and every other key of the request (plants, photos, product,
the member the care was done for) is resolved under the tenant before anything is written (GP-NFR-058). The
bed and the path key answer 404 when foreign or absent, a reference in the body answers 422
``reference.not_found`` for both alike.

**The performer comes from the token** (GP-NFR-054): ``performed_by_user_key`` and ``created_by`` are the
caller's ``user_key``; a supersede keeps the predecessor's performer and records the corrector as ``created_by``.

**Logs carry no user text** (GP-NFR-060): keys, counts, codes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.care_event_repository import (
    CareEventFilter,
    CareEventRow,
    ICareEventRepository,
)
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.care_event import (
    FUTURE_TOLERANCE_MINUTES,
    MAX_AGE_DAYS,
    SERVER_ONLY_CATEGORIES,
    UNDO_WINDOW_MINUTES,
    CareEvent,
    CareEventCorrection,
    CareEventInput,
    CareEventOrigin,
    CareEventView,
    display_performer,
)
from app.domain.models.site import Location
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.location_ownership import resolve_owned_location
from app.observability.garden_plan_metrics import record_care_event_created

logger = structlog.get_logger()

#: ``reason`` of an author's own cancellation inside the undo window (GP-API-037, GP-FR-149).
UNDO_REASON = "undo"
#: GP-FR-107: the tenant-wide history shows the last 90 days unless the caller says otherwise.
DEFAULT_HISTORY_DAYS = 90

ERROR_REFERENCE_NOT_FOUND = "reference.not_found"
ERROR_PERFORMED_IN_FUTURE = "care_event.performed_in_future"
ERROR_TOO_OLD = "care_event.too_old"
ERROR_IMMUTABLE = "care_event.immutable"
ERROR_SEQUENCE = "care_event.sequence"
ERROR_SERVER_ONLY = "care_event.category_server_only"


def _not_found(field: str) -> PlanValidationError:
    """422 ``reference.not_found`` — one text for a missing and for another tenant's key (GP-NFR-058)."""
    return PlanValidationError([(None, field, ERROR_REFERENCE_NOT_FOUND, {})])


def _subtree(locations: list[Location], root_key: str) -> list[str]:
    """``root_key`` and every location below it, by ``parent_location_key`` (a site holds a few hundred at most)."""
    children: dict[str, list[str]] = {}
    for location in locations:
        if location.key and location.parent_location_key:
            children.setdefault(location.parent_location_key, []).append(location.key)
    found = [root_key]
    for key in found:  # grows while iterating: a breadth-first walk
        found.extend(child for child in children.get(key, []) if child not in found)
    return found


class CareEventService:
    def __init__(
        self,
        repo: ICareEventRepository,
        site_repo: ISiteRepository,
        membership_repo: IMembershipRepository,
        fertilizer_repo: IFertilizerRepository,
        attachment_repo: IAttachmentRepository,
        attachment_service: AttachmentService,
    ) -> None:
        self._repo = repo
        self._sites = site_repo
        self._memberships = membership_repo
        self._fertilizers = fertilizer_repo
        self._attachment_repo = attachment_repo
        self._attachments = attachment_service

    # ── Roles ────────────────────────────────────────────────────────────────

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _require_lead(role: TenantRole) -> None:
        if not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Requires lead role.")

    # ── Validation ───────────────────────────────────────────────────────────

    @staticmethod
    def _check_performed_at(performed_at: datetime, *, max_age_days: int) -> None:
        """V-11: at most five minutes ahead, at most ``max_age_days`` back."""
        now = datetime.now(UTC)
        if performed_at > now + timedelta(minutes=FUTURE_TOLERANCE_MINUTES):
            raise PlanError(
                ERROR_PERFORMED_IN_FUTURE,
                "performed_at lies in the future.",
                status_code=422,
                field="performed_at",
            )
        if performed_at < now - timedelta(days=max_age_days):
            raise PlanError(
                ERROR_TOO_OLD,
                f"performed_at lies more than {max_age_days} days back.",
                status_code=422,
                field="performed_at",
                max_age_days=max_age_days,
            )

    def _check_plants(self, plant_keys: list[str], location: Location, *, tenant_key: str) -> None:
        """``plant_keys`` ⊆ the tenant's plants standing in the bed's subtree (GP-NFR-058)."""
        if not plant_keys:
            return
        subtree = _subtree(self._sites.get_locations_by_site(location.site_key), location.key or "")
        found = self._repo.plants_in_locations(plant_keys, subtree, tenant_key=tenant_key)
        if found != set(plant_keys):
            raise _not_found("plant_keys")

    def _check_product(self, product_key: str | None, *, tenant_key: str) -> None:
        if product_key is None:
            return
        if product_key not in self._fertilizers.list_visible_keys([product_key], tenant_key=tenant_key):
            raise _not_found("product_ref")

    def _check_performed_for(self, user_key: str | None, *, tenant_key: str) -> None:
        if user_key is None:
            return
        membership = self._memberships.get_by_user_and_tenant(user_key, tenant_key)
        if membership is None or not membership.is_active:
            raise _not_found("performed_for_user_key")

    def _check_photos(
        self, photo_refs: list[str], already_attached: list[str], *, tenant_key: str, user_key: str
    ) -> None:
        """A photo is the tenant's attachment that the caller uploaded or that the corrected entry already carries."""
        for ref in photo_refs:
            if ref in already_attached:
                continue
            attachment = self._attachment_repo.get(ref, tenant_key)
            if attachment is None or attachment.created_by != user_key:
                raise _not_found("photo_refs")

    @staticmethod
    def _quantity_total(
        data: CareEventInput | CareEventCorrection, location: Location
    ) -> tuple[float | None, str | None]:
        """Area doses (``l_per_m2``, ``g_per_m2``) become a total for the bed: ``quantity × area_m2`` (GP-FR-088)."""
        if data.quantity is None or data.unit not in ("l_per_m2", "g_per_m2") or location.area_m2 <= 0:
            return None, None
        return round(data.quantity * location.area_m2, 3), "l" if data.unit == "l_per_m2" else "g"

    def _validated_fields(
        self,
        data: CareEventInput | CareEventCorrection,
        location: Location,
        *,
        tenant_key: str,
        user_key: str,
        already_photos: list[str],
        max_age_days: int,
    ) -> dict[str, object]:
        """Every reference resolved under the tenant, V-11 applied; the stored descriptive columns of the event."""
        self._check_plants(data.plant_keys, location, tenant_key=tenant_key)
        self._check_product(data.product_ref.key if data.product_ref else None, tenant_key=tenant_key)
        self._check_performed_for(data.performed_for_user_key, tenant_key=tenant_key)
        self._check_photos(data.photo_refs, already_photos, tenant_key=tenant_key, user_key=user_key)
        self._check_performed_at(data.performed_at, max_age_days=max_age_days)
        total, total_unit = self._quantity_total(data, location)
        return {
            "plant_keys": list(data.plant_keys),
            "category": data.category,
            "summary": data.summary,
            "performed_at": data.performed_at,
            "performed_for_user_key": data.performed_for_user_key,
            "performed_by_label": data.performed_by_label,
            "reason": data.reason,
            "product_ref": data.product_ref.model_dump(mode="json") if data.product_ref else None,
            "product_label": data.product_label,
            "quantity": data.quantity,
            "unit": data.unit,
            "quantity_total": total,
            "quantity_total_unit": total_unit,
            "material": data.material,
            "measurements": [m.model_dump(mode="json") for m in data.measurements] if data.measurements else None,
            "observed_outcome": data.observed_outcome,
            "outcome_rating": data.outcome_rating,
            "photo_refs": list(data.photo_refs),
        }

    # ── Views ────────────────────────────────────────────────────────────────

    @staticmethod
    def _view(row: CareEventRow, viewer_user_key: str, chain_keys: list[str] | None = None) -> CareEventView:
        event = row.event
        return CareEventView(
            event=event,
            performed_by=display_performer(
                event.performed_by_user_key, row.performed_by_name, event.performed_by_label
            ),
            performed_for=(
                display_performer(event.performed_for_user_key, row.performed_for_name)
                if event.performed_for_user_key
                else None
            ),
            created_by_me=event.created_by is not None and event.created_by == viewer_user_key,
            chain_keys=chain_keys or [],
        )

    def _stored_view(self, key: str, *, tenant_key: str, user_key: str) -> CareEventView:
        row = self._repo.get_row(key, tenant_key=tenant_key)
        if row is None:  # written a moment ago in this request; only a concurrent erasure removes it
            raise NotFoundError("CareEvent", key)
        return self._view(row, user_key)

    # ── Reads ────────────────────────────────────────────────────────────────

    def get(self, key: str, *, tenant_key: str, user_key: str) -> CareEventView:
        """One event with its supersede chain (GP-API-035); absent and foreign answer 404 alike."""
        row = self._repo.get_row(key, tenant_key=tenant_key)
        if row is None:
            raise NotFoundError("CareEvent", key)
        chain = [event.key or "" for event in self._repo.chain(key, tenant_key=tenant_key)]
        return self._view(row, user_key, chain)

    def list_window(
        self,
        criteria: CareEventFilter,
        *,
        tenant_key: str,
        user_key: str,
        offset: int,
        limit: int,
    ) -> list[CareEventView]:
        """The tenant's care log, newest first (GP-API-034, GP-FR-107); the last 90 days when no range is given."""
        if criteria.location_key:
            resolve_owned_location(self._sites, criteria.location_key, tenant_key)
        if criteria.performed_from is None and criteria.performed_to is None:
            criteria = CareEventFilter(
                location_key=criteria.location_key,
                plant_key=criteria.plant_key,
                category=criteria.category,
                performed_from=datetime.now(UTC) - timedelta(days=DEFAULT_HISTORY_DAYS),
                performed_to=None,
                performed_by=criteria.performed_by,
                include_superseded=criteria.include_superseded,
            )
        rows = self._repo.list_events(criteria, tenant_key=tenant_key, offset=offset, limit=limit)
        return [self._view(row, user_key) for row in rows]

    # ── Create ───────────────────────────────────────────────────────────────

    def build_event(
        self,
        data: CareEventInput,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        origin: CareEventOrigin | None = None,
    ) -> CareEvent:
        """Validate ``data`` and return the event as it would be stored — nothing is written.

        For a caller that writes inside its own transaction (see the module docstring). Raises exactly what
        :meth:`create` raises.
        """
        self._require_editor(role)
        if origin is None and data.category in SERVER_ONLY_CATEGORIES:
            raise PlanError(
                ERROR_SERVER_ONLY,
                f"The category '{data.category}' is written by the server only.",
                status_code=422,
                field="category",
            )
        location = resolve_owned_location(self._sites, data.location_key, tenant_key)
        fields = self._validated_fields(
            data,
            location,
            tenant_key=tenant_key,
            user_key=user_key,
            already_photos=[],
            max_age_days=origin.max_age_days if origin else MAX_AGE_DAYS,
        )
        return CareEvent(
            tenant_key=tenant_key,
            site_key=location.site_key,
            location_key=location.key or data.location_key,
            performed_by_user_key=user_key,
            trigger=origin.trigger if origin else data.trigger,
            task_key=origin.task_key if origin else None,
            source_ref=origin.source_ref if origin else None,
            created_by=user_key,
            **fields,
        )

    def create(
        self,
        data: CareEventInput,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        origin: CareEventOrigin | None = None,
    ) -> CareEventView:
        """Store a care event (GP-API-033); the performer is the caller (GP-NFR-054)."""
        event = self.build_event(data, tenant_key=tenant_key, user_key=user_key, role=role, origin=origin)
        stored = self._repo.insert(event, tenant_key=tenant_key)
        self._record_created(stored)
        return self._stored_view(stored.key or "", tenant_key=tenant_key, user_key=user_key)

    @staticmethod
    def _record_created(event: CareEvent) -> None:
        record_care_event_created(event.category)
        logger.info(
            "care_event.created",
            event_key=event.key,
            location_key=event.location_key,
            category=event.category,
            trigger=event.trigger,
            plant_count=len(event.plant_keys),
            supersedes_key=event.supersedes_key,
        )

    # ── Supersede ────────────────────────────────────────────────────────────

    def supersede(
        self,
        key: str,
        data: CareEventCorrection,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
    ) -> CareEventView:
        """Correct an entry: a new one that supersedes it, the old one stays readable (GP-API-036, GP-FR-101).

        The author corrects their own entry, the lead any. The corrected entry keeps the predecessor's performer,
        ``trigger`` and ``task_key``; the corrector is ``created_by``. A corrected ``performed_at`` is held to
        V-11 like a new one.
        """
        self._require_editor(role)
        predecessor = self._repo.get(key, tenant_key=tenant_key)
        if predecessor is None:
            raise NotFoundError("CareEvent", key)
        if predecessor.created_by != user_key and not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Only the author or a lead may correct this entry.")
        if predecessor.redacted_at is not None:
            raise PlanError(
                ERROR_IMMUTABLE, "A redacted entry cannot be corrected.", status_code=422, field="care_event"
            )
        if predecessor.superseded_by_key or predecessor.voided_at:
            raise PlanError(
                ERROR_SEQUENCE,
                "The care event is superseded or voided already; correct the newest entry of its chain.",
                status_code=422,
                field="supersedes_key",
            )
        location = resolve_owned_location(self._sites, predecessor.location_key, tenant_key)
        fields = self._validated_fields(
            data,
            location,
            tenant_key=tenant_key,
            user_key=user_key,
            already_photos=predecessor.photo_refs,
            max_age_days=3650 if predecessor.trigger == "backfill" else MAX_AGE_DAYS,
        )
        event = CareEvent(
            tenant_key=tenant_key,
            site_key=predecessor.site_key,
            location_key=predecessor.location_key,
            performed_by_user_key=predecessor.performed_by_user_key,
            trigger=predecessor.trigger,
            task_key=predecessor.task_key,
            supersedes_key=predecessor.key,
            created_by=user_key,
            **fields,
        )
        stored = self._repo.supersede(key, event, tenant_key=tenant_key)
        self._record_created(stored)
        return self._stored_view(stored.key or "", tenant_key=tenant_key, user_key=user_key)

    # ── Void ─────────────────────────────────────────────────────────────────

    def void(self, key: str, *, reason: str, tenant_key: str, user_key: str, role: TenantRole) -> CareEventView:
        """Cancel an entry (GP-API-037): ``voided_at`` / ``voided_by`` / ``void_reason``, nothing else changes.

        The lead may cancel any entry. A grower may take back their *own* entry within ten minutes of
        ``created_at`` with ``reason = "undo"`` (the field-mode snackbar, GP-FR-149) and nothing else.
        """
        self._require_editor(role)
        event = self._repo.get(key, tenant_key=tenant_key)
        if event is None:
            raise NotFoundError("CareEvent", key)
        if not MembershipEngine.can_delete_resource(role):
            within_window = event.created_at is not None and datetime.now(UTC) - event.created_at <= timedelta(
                minutes=UNDO_WINDOW_MINUTES
            )
            if not (event.created_by == user_key and reason == UNDO_REASON and within_window):
                raise ForbiddenError("Only a lead may cancel this entry; you may undo your own within ten minutes.")
        voided = self._repo.void(key, tenant_key=tenant_key, voided_by=user_key, reason=reason, at=datetime.now(UTC))
        logger.info("care_event.voided", event_key=voided.key, category=voided.category, undo=reason == UNDO_REASON)
        return self._stored_view(key, tenant_key=tenant_key, user_key=user_key)

    # ── Redact ───────────────────────────────────────────────────────────────

    async def redact(self, key: str, *, reason: str, tenant_key: str, user_key: str, role: TenantRole) -> CareEventView:
        """Replace the free texts of the entry and its whole supersede chain by ``[redacted]`` (GP-API-041).

        Lead only. The photos are detached in the same transaction as the redaction and the audit row
        (``garden_plan_audit``, ``op = redact``); the stored objects are deleted afterwards unless another
        carrier still references them (GP-FR-109, Art. 16/17).
        """
        self._require_lead(role)
        if self._repo.get(key, tenant_key=tenant_key) is None:
            raise NotFoundError("CareEvent", key)
        redacted, detached = self._repo.redact(
            key, tenant_key=tenant_key, redacted_by=user_key, reason=reason, at=datetime.now(UTC)
        )
        deleted = 0
        for attachment_id in detached:
            if await self._attachments.delete_if_unreferenced(attachment_id, tenant_key):
                deleted += 1
        logger.info("care_event.redacted", event_key=key, chain_length=len(redacted), photos_deleted=deleted)
        return self._stored_view(key, tenant_key=tenant_key, user_key=user_key)
