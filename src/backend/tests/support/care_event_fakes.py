"""In-memory doubles of the care-event service's collaborators (REQ-053 WP 4.1, #2400).

``FakeCareEventRepo`` holds the documents the way ``ArangoCareEventRepository`` does — tenant-filtered reads,
the supersede / void sequence rules inside the write — and records what was handed to it, so a test asserts both
what the service decided and that a refusal wrote nothing. The rest are the narrow reads the service resolves
references through. Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.common.exceptions import NotFoundError, PlanError
from app.domain.interfaces.care_event_repository import (
    AnonymizedBatch,
    CareEventFilter,
    CareEventRow,
    ICareEventRepository,
)
from app.domain.models.attachment import Attachment
from app.domain.models.care_event import (
    FREE_TEXT_FIELDS,
    REDACTED,
    CareEvent,
)
from app.domain.models.membership import Membership
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT, USER

NAMES = {USER: "Sabine", "u_tom": "Tom", "u_lead": "Lena"}


class FakeCareEventRepo(ICareEventRepository):
    def __init__(self) -> None:
        self.events: dict[str, CareEvent] = {}
        #: ``plant_key`` → (tenant, location) of the plants that exist.
        self.plants: dict[str, tuple[str, str]] = {}
        self.inserted: list[CareEvent] = []
        self.audit: list[dict] = []
        self.photos_held: dict[str, list[str]] = {}
        self._next = 0

    def _store(self, event: CareEvent) -> CareEvent:
        self._next += 1
        stored = event.model_copy(update={"key": f"ce_{self._next}", "created_at": datetime.now(UTC)})
        self.events[stored.key or ""] = stored
        return stored

    # reads ---------------------------------------------------------------
    def get(self, key, *, tenant_key):
        event = self.events.get(key)
        return event if event is not None and event.tenant_key == tenant_key else None

    def get_row(self, key, *, tenant_key):
        event = self.get(key, tenant_key=tenant_key)
        if event is None:
            return None
        return CareEventRow(
            event=event,
            performed_by_name=NAMES.get(event.performed_by_user_key or ""),
            performed_for_name=NAMES.get(event.performed_for_user_key or ""),
        )

    def chain(self, key, *, tenant_key):
        event = self.get(key, tenant_key=tenant_key)
        if event is None:
            return []
        older: list[CareEvent] = []
        cursor = event
        while cursor.supersedes_key and (previous := self.get(cursor.supersedes_key, tenant_key=tenant_key)):
            older.append(previous)
            cursor = previous
        newer: list[CareEvent] = []
        cursor = event
        while cursor.superseded_by_key and (following := self.get(cursor.superseded_by_key, tenant_key=tenant_key)):
            newer.append(following)
            cursor = following
        return [*reversed(older), event, *newer]

    def list_events(self, criteria: CareEventFilter, *, tenant_key, offset, limit):
        rows = []
        for event in sorted(self.events.values(), key=lambda e: e.performed_at, reverse=True):
            if event.tenant_key != tenant_key:
                continue
            if criteria.location_key and event.location_key != criteria.location_key:
                continue
            if criteria.plant_key and criteria.plant_key not in event.plant_keys:
                continue
            if criteria.category and event.category != criteria.category:
                continue
            if criteria.performed_by and event.performed_by_user_key != criteria.performed_by:
                continue
            if not criteria.include_superseded and event.superseded_by_key:
                continue
            if criteria.performed_from and event.performed_at < criteria.performed_from:
                continue
            if criteria.performed_to and event.performed_at > criteria.performed_to:
                continue
            rows.append(self.get_row(event.key or "", tenant_key=tenant_key))
        return rows[offset : offset + limit]

    def plants_in_locations(self, plant_keys, location_keys, *, tenant_key):
        return {
            key
            for key in plant_keys
            if key in self.plants and self.plants[key][0] == tenant_key and self.plants[key][1] in location_keys
        }

    # writes --------------------------------------------------------------
    def insert(self, event, *, tenant_key):
        assert event.tenant_key == tenant_key
        self.inserted.append(event)
        return self._store(event)

    @staticmethod
    def _refuse_if_closed(event: CareEvent) -> None:
        if event.superseded_by_key or event.voided_at:
            raise PlanError("care_event.sequence", "closed", status_code=422, field="supersedes_key")

    def supersede(self, predecessor_key, event, *, tenant_key):
        old = self.get(predecessor_key, tenant_key=tenant_key)
        if old is None:
            raise NotFoundError("CareEvent", predecessor_key)
        self._refuse_if_closed(old)
        self.inserted.append(event)
        stored = self._store(event)
        self.events[predecessor_key] = old.model_copy(update={"superseded_by_key": stored.key})
        return stored

    def void(self, key, *, tenant_key, voided_by, reason, at):
        event = self.get(key, tenant_key=tenant_key)
        if event is None:
            raise NotFoundError("CareEvent", key)
        self._refuse_if_closed(event)
        voided = event.model_copy(update={"voided_at": at, "voided_by": voided_by, "void_reason": reason})
        self.events[key] = voided
        return voided

    def redact(self, key, *, tenant_key, redacted_by, reason, at):
        chain = self.chain(key, tenant_key=tenant_key)
        if not chain:
            raise NotFoundError("CareEvent", key)
        detached: list[str] = []
        redacted = []
        for event in chain:
            detached.extend(event.photo_refs)
            patch = {
                name: REDACTED for name in FREE_TEXT_FIELDS if getattr(event, name) is not None or name == "summary"
            }
            updated = event.model_copy(
                update={
                    **patch,
                    "photo_refs": [],
                    "redacted_at": at,
                    "redacted_by": redacted_by,
                    "redaction_reason": reason,
                }
            )
            self.events[event.key or ""] = updated
            redacted.append(updated)
        self.audit.append({"op": "redact", "entity": "care_event", "key": key, "user_key": redacted_by})
        return redacted, list(dict.fromkeys(detached))

    def anonymize_expired(self, *, cutoff, pflschg_cutoff, now, batch):  # pragma: no cover - the sweep has its own test
        return AnonymizedBatch()


class FakeMemberships:
    def __init__(self) -> None:
        self.members = {(USER, TENANT), ("u_tom", TENANT), ("u_lead", TENANT), ("u_foreign", OTHER_TENANT)}
        self.inactive: set[tuple[str, str]] = set()

    def get_by_user_and_tenant(self, user_key, tenant_key):
        if (user_key, tenant_key) not in self.members:
            return None
        return Membership(
            user_key=user_key,
            tenant_key=tenant_key,
            role="grower",
            is_active=(user_key, tenant_key) not in self.inactive,
        )


class FakeFertilizers:
    def __init__(self) -> None:
        #: key → owning tenant ("" = global catalogue).
        self.owners = {"fert_global": "", "fert_own": TENANT, "fert_foreign": OTHER_TENANT}

    def list_visible_keys(self, keys, *, tenant_key):
        return {key for key in keys if key in self.owners and self.owners[key] in ("", tenant_key)}


class FakeAttachmentRepo:
    def __init__(self) -> None:
        self.rows: dict[str, Attachment] = {}

    def add(self, key: str, *, tenant_key: str = TENANT, created_by: str = USER) -> None:
        self.rows[key] = Attachment(
            _key=key,
            tenant_key=tenant_key,
            mime_type="image/jpeg",
            byte_size=10,
            sha256="0" * 64,
            original_filename="p.jpg",
            created_by=created_by,
            category="plant",
            storage_key=f"t/{tenant_key}/plant/{key}.jpg",
        )

    def get(self, key, tenant_key):
        row = self.rows.get(key)
        return row if row is not None and row.tenant_key == tenant_key else None


class FakeAttachmentService:
    """Records the deletes the redaction asks for; a photo another carrier holds is kept."""

    def __init__(self) -> None:
        self.deleted: list[tuple[str, str]] = []
        self.still_referenced: set[str] = set()

    async def delete_if_unreferenced(self, attachment_id, tenant_key):
        if attachment_id in self.still_referenced:
            return False
        self.deleted.append((tenant_key, attachment_id))
        return True
