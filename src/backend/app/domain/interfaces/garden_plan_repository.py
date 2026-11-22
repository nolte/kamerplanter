from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app.common.types import SiteKey
from app.domain.models.bed_list_export import BedAssignee, LocationTypeName
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    BedCounters,
    PlanAuditEntry,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlanSnapshotEntry,
    PlantShortInfo,
    SlotBatchOutcome,
    SlotBatchWrite,
    SlotRuleBasis,
    SlotSpeciesHint,
    TaskCounter,
)
from app.domain.models.site import Location, SiteUnderlay, Slot
from app.domain.models.tent_hint import PlantPhotoperiod

#: Plants one photoperiod read considers (W-016.6). A tent holds a few dozen at most; the bound keeps a mis-typed
#: location of thousands of plants from turning a summary into a scan.
MAX_PHOTOPERIOD_PLANTS = 500
#: Area location types one read returns (REQ-053 §9.5). The seed has a dozen; the bound keeps the master-data read
#: of every plan request bounded.
MAX_AREA_TYPES = 500


@dataclass
class PlanReadData:
    """The documents behind ``GET /sites/{key}/plan``, read in one pass (GP-NFR-002)."""

    locations: list[Location] = field(default_factory=list)
    garden_objects: list[GardenObject] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)
    plants: list[PlantShortInfo] = field(default_factory=list)
    task_counters: dict[str, TaskCounter] = field(default_factory=dict)
    #: Open tasks per garden object (compost, water source, storage; REQ-053 R-7.2), keyed by the object key.
    object_task_counters: dict[str, TaskCounter] = field(default_factory=dict)
    #: Newest watering per bed (care event or ``watering_events``, within a year), keyed by location key; filled
    #: together with the task counters (REQ-053 GP-UX-006, WP 7.3). A bed never watered is absent.
    last_watered: dict[str, datetime] = field(default_factory=dict)
    #: Display name of the account that last changed the plan structure; ``None`` when unknown or erased.
    plan_updated_by_name: str | None = None
    #: Per slot key, the first day a live run of the tenant reserves the slot in a window that has not ended
    #: (``run_planned_at``, GP-FR-065/074); filled with the plants (``include=plants``). An unreserved slot is absent.
    slot_planned_from: dict[str, date] = field(default_factory=dict)


@dataclass(frozen=True)
class SoilProfileEdit:
    """A ``soil_profile`` sent with ``PATCH /locations`` (#2706); the repository writes it through the derivation.

    ``profile`` is the body's profile as JSON (``None`` stores ``null``). ``check_last_analysis_at`` says the body
    carried ``last_analysis_at``; then ``expected_last_analysis_at`` must equal the stored one (409 otherwise).
    """

    tenant_key: str
    profile: dict[str, Any] | None
    check_last_analysis_at: bool = False
    expected_last_analysis_at: datetime | None = None


class IGardenPlanRepository(ABC):
    """Persistence of the garden plan beyond the single documents (REQ-053 §21.1, §21.3).

    Locations and garden objects carry no ``tenant_key`` (E-01, #2107): every read here
    takes the tenant keyword-only without a default and joins the site inside the query,
    so a foreign site answers with nothing instead of with its rows (§22.3 T-04).
    """

    @abstractmethod
    def load_structure(self, site_key: SiteKey, *, tenant_key: str) -> tuple[list[Location], list[GardenObject]]:
        """Every location and garden object of a site of ``tenant_key`` (the batch's working-copy basis)."""

    @abstractmethod
    def load_read_model(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        include_plants: bool,
        include_tasks: bool,
        skip_unreadable_slots: bool = True,
        as_of: date | None = None,
    ) -> PlanReadData:
        """The documents of the plan read model; slots of archived runs are left out.

        ``as_of`` (GP-API-001, #2901) changes the plants only: those of ``tenant_key`` that stood in the beds on
        that day (``planted_on <= as_of < removed_on``, an open ``removed_on`` counts as standing), without a
        ``phase_key``. ``None`` reads the plants standing now. Structure, slots and task counters stay current.

        A stored slot that fails :class:`Slot` validation (a legacy row) is logged and left out, so one such row
        does not turn the displayed plan into an error (#2709). A reader that hands the slots on - the export,
        whose file a replace import restores from - passes ``skip_unreadable_slots=False`` and gets the 409
        ``StoredDocumentInvalidError`` instead of a silently shorter file.
        """

    @abstractmethod
    def load_active_slots(
        self,
        site_key: SiteKey,
        location_keys: list[str],
        *,
        tenant_key: str,
        include_archived: bool = False,
        slot_keys: list[str] | None = None,
    ) -> list[Slot]:
        """Slots (``archived_at`` null, or all with ``include_archived``) of the named locations (V-04, V-06, V-20).

        The locations must belong to the tenant's site; a key of another site or tenant yields nothing. With
        *slot_keys* only those slots among them are read (the companion overlay reads just the slots in pairs).
        A stored slot that fails :class:`Slot` validation raises the 409 ``StoredDocumentInvalidError`` (#2709):
        the write paths read their siblings here (taken slot ids, sequence, quota, overlap), and a row left out
        would let them hand out a duplicate id or pass a cap.
        """

    @abstractmethod
    def load_slot_species_hints(self, location_key: str, *, tenant_key: str) -> list[SlotSpeciesHint]:
        """The species of the active plants and of the live run reservations in a bed's slots (GP-FR-130).

        Empty when the bed does not belong to the tenant's site. Several rows may name one slot. Only species the
        tenant may read (own ∪ global ∪ granted) are answered: a stored key is no proof of access, so an invisible
        species is left out rather than named (#2709). A row that fails validation is logged and left out.
        """

    @abstractmethod
    def bed_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        """``location_type_key`` → ``is_bed`` for the keys that resolve; an unknown key is absent."""

    @abstractmethod
    def layout_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        """``location_type_key`` → ``supports_layout`` (W-016.1) for the keys that resolve; an unknown key is absent.

        A type flagged ``is_bed`` reads ``True`` even where a stored document lacks ``supports_layout`` (the model's
        rule, ``LocationType._a_bed_supports_a_layout``).
        """

    @abstractmethod
    def area_type_keys(self) -> list[str]:
        """The keys of every location type the plan draws as an **area** (REQ-053 §9.5, GP-UX-071), sorted.

        An area type is neither ``is_bed`` nor ``supports_layout``: garden, terrace, balcony, greenhouse, room and
        the like. Tent and shelf (``supports_layout``) are planting spots, not areas. Location types are global master
        data; at most :data:`MAX_AREA_TYPES` keys are read.
        """

    @abstractmethod
    def bed_type_keys(self) -> list[str]:
        """The keys of every location type flagged ``is_bed`` (REQ-053 V-05), sorted.

        The editor checks V-05 (``bed.overlap``) live with them (operator decision of 2026-11-14 on #2759, question
        14): two beds of one parent may not overlap. Every bed type, not only those on the plan, so a bed drawn with a
        type the plan does not hold yet is checked too. Global master data; at most :data:`MAX_AREA_TYPES` keys.
        """

    @abstractmethod
    def load_location_photoperiods(self, location_key: str, *, tenant_key: str) -> list[PlantPhotoperiod]:
        """The tenant's standing plants in the location with the photoperiod their current phase asks for (W-016.6).

        A plant stands in the location by its ``location_key`` or, without one, by its slot's (the plan's rule). The
        photoperiod is the ``photoperiod_hours`` of the requirement profile of the plant's current phase (REQ-003):
        a legacy growth phase directly (its key is the plant's ``current_phase_key`` - the id wins); a phase-sequence
        entry through the growth phase of the same name in the species' lifecycle, only when exactly one has that
        name. Two, none, or no profile - ``None``, never a guess or a default (E-10). With the hours comes the
        profile's ``photoperiod_source`` as stored (#2857; ``None`` when the profile has none or a value this code does
        not know) - which hours the rule may judge is the engine's decision. Each plant carries its phase's
        machine name (``phase_code``) and its display name. At most :data:`MAX_PHOTOPERIOD_PLANTS` plants, ordered
        by key; the caller resolved the location under the tenant first.
        """

    @abstractmethod
    def count_active_plants(self, location_keys: list[str], *, tenant_key: str) -> int:
        """Plants of ``tenant_key`` with ``removed_on = null`` standing in any of the locations (V-09)."""

    @abstractmethod
    def locations_with_active_plants(self, location_keys: list[str], *, tenant_key: str) -> set[str]:
        """The locations among ``location_keys`` in which a plant of ``tenant_key`` with ``removed_on = null`` stands.

        The import's "empty bed" condition (GP-API-005) and the set it must keep with ``force`` (V-09).
        """

    @abstractmethod
    def apply_plan_batch(self, write: PlanBatchWrite) -> PlanBatchOutcome:
        """Write the set in one transaction, after re-checking the revision inside it (GP-NFR-013).

        A ``write.snapshot`` is stored as an ``import_snapshot`` row; in the same transaction the site's oldest
        ``import_snapshot`` rows beyond ``MAX_SNAPSHOTS_PER_SITE`` are removed (GP-NFR-055, #2542). No other audit
        row is touched by that.

        Raises:
            PlanRevisionConflictError: the stored ``plan_revision`` is not the one expected.
            NotFoundError: the site is gone or not the tenant's.
        """

    @abstractmethod
    def list_audit(self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int) -> list[PlanAuditEntry]:
        """The site's plan change log, newest first."""

    @abstractmethod
    def list_import_snapshots(
        self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int
    ) -> list[PlanSnapshotEntry]:
        """The ``import_snapshot`` rows of the site (plans a ``replace`` overwrote), newest first, no payload."""

    @abstractmethod
    def load_import_snapshot(self, site_key: SiteKey, audit_key: str, *, tenant_key: str) -> dict[str, Any] | None:
        """The stored plan of one ``import_snapshot`` row of this site and tenant, or ``None`` (absent or foreign)."""

    @abstractmethod
    def purge_audit_before(self, cutoff: datetime, *, batch: int) -> int:
        """Hard-delete up to ``batch`` audit rows with ``at`` before ``cutoff`` (NFR-011 R-26); the number removed."""

    # ── Single resources (WP 1.9, GP-API-010…015, GP-API-018) ─────────────────

    @abstractmethod
    def load_bed_counters(self, location_keys: list[str], *, tenant_key: str) -> dict[str, BedCounters]:
        """Plant, task and care counters for the named locations (which the caller took from an owned site).

        A location without any of them is absent from the result.
        """

    # ── The bed list as a download (WP 8.25, GP-FR-145/175) ───────────────────

    @abstractmethod
    def location_type_names(self, location_type_keys: list[str]) -> dict[str, LocationTypeName]:
        """``location_type_key`` → its names (DE/EN) for the keys that resolve; location types are global."""

    @abstractmethod
    def irrigation_zone_names(self, site_key: SiteKey, *, tenant_key: str) -> dict[str, str]:
        """``irrigation_zone_key`` → name of every zone of the tenant's site; a foreign site yields nothing."""

    @abstractmethod
    def location_assignees(self, location_keys: list[str], *, tenant_key: str) -> list[BedAssignee]:
        """The active members of ``tenant_key`` the named locations are assigned to (``location_assignments``).

        The caller took the keys from an owned site. An assignment of another tenant, of an ended membership or of
        a membership that is gone is left out.
        """

    @abstractmethod
    def count_active_slots(self, site_key: SiteKey, *, tenant_key: str) -> int:
        """Slots (``archived_at`` null) in all locations of the tenant's site — the GP-NFR-017 quota counts these."""

    @abstractmethod
    def update_location_fields(
        self, location_key: str, fields: dict[str, Any], *, soil: SoilProfileEdit | None = None
    ) -> None:
        """Write *only* ``fields`` (``None`` removes a stored value) — outside the plan revision (GP-API-010).

        The caller has resolved the location under the tenant through ``location_ownership``; the repository
        does not know the tenant (a location carries none, E-01). A change of ``irrigation_zone_key`` moves the
        bed's ``zone_covers`` edge in the same transaction (REQ-053 WP 7.1); the caller has resolved the zone
        to one of the bed's site.

        ``site_conditions`` is the exception to "a column is replaced whole" (#2569): its value holds only the
        parts the PATCH sent (a nested part only its sent keys) and is merged into the stored value, a ``None``
        inside it removing that key; ``site_conditions: None`` clears the whole value. A part the plan batch
        wrote after the caller's read (``sun_profile``, #2538) is therefore kept.

        ``soil`` (#2706) writes the bed's ``soil_profile`` in the **same** transaction: the precondition on
        ``last_analysis_at`` (409 ``soil_profile.stale``), the hand entries of the edited measured fields, the other
        soil fields as sent, then the one derivation every soil-analysis write runs - so a concurrent derivation of
        the bed collides (409 ``WRITE_CONFLICT``) instead of being overwritten.
        """

    @abstractmethod
    def set_site_underlay(
        self, site_key: SiteKey, *, tenant_key: str, underlay: SiteUnderlay | None
    ) -> tuple[bool, str | None]:
        """Replace (or, with ``None``, remove) the underlay of the tenant's site plan - outside the plan revision.

        The picture is presentation, not structure (GP-NFR-007 counts structure), so neither the revision nor the
        audit log moves. Returns ``(written, previous_attachment_key)``: ``written`` is false when the site is
        another tenant's, absent or has no plan; ``previous_attachment_key`` is the picture the write replaced.

        A new underlay's attachment record (the tenant's, category ``garden_plan_underlay``) is written in the same
        transaction (#2545), so a concurrent ``IAttachmentRepository.remove_if_unreferenced`` of it conflicts instead
        of leaving the plan naming a deleted picture; a record already gone raises 422 ``reference.not_found``
        (``PlanValidationError``), a concurrent writer ``WriteConflictError``.
        """

    @abstractmethod
    def load_slot_rule_basis(
        self,
        site_key: SiteKey,
        location_keys: list[str],
        *,
        tenant_key: str,
        include_archived: bool = False,
    ) -> SlotRuleBasis:
        """The beds, their slots and each bed's ``slot_rules_revision`` — what V-04/V-06 are checked against (#2773).

        One query, so one snapshot: the revision belongs to exactly the frame and the slots returned. A writer that
        validated against them hands the revision to its transaction, which compares and raises it before it
        writes (``slot_rules_fence.take_slot_rules``). Ownership as :meth:`load_active_slots`: a bed of another
        site or tenant is absent from all three parts. A stored slot that fails :class:`Slot` validation raises the
        409 ``StoredDocumentInvalidError``.
        """

    @abstractmethod
    def update_slot_fields(
        self, slot_key: str, fields: dict[str, Any], *, read: Slot, slot_rules: tuple[str, int] | None
    ) -> None:
        """Write *only* ``fields`` of a slot, nested objects replaced whole (a geometry may change its kind).

        The caller has resolved the slot under the tenant through ``location_ownership``.

        ``read`` is the slot the change was validated against (#2727); the write is conditional on it: it lands
        only while the stored ``slot_role``, ``capacity_plants`` and geometry kind — the columns the slot model
        validates against each other — are still those of ``read``; otherwise
        :class:`~app.common.exceptions.WriteConflictError` (409) and nothing is written. Without it a second
        ``PATCH`` drawing an unplaced zone's polygon between the read and this write could meet a role changed
        to ``row`` here and store a slot neither PATCH validated.

        ``slot_rules`` is ``(bed key, slot_rules_revision)`` of the basis V-04/V-06 were checked against, or
        ``None`` when the change ran no bed-level rule (capacity only). With it the write and the bed's fence are one
        transaction: a slot or frame write of the bed since the basis was read is a ``WriteConflictError`` (#2773).
        """

    @abstractmethod
    def irrigation_zone_site_key(self, zone_key: str, *, tenant_key: str) -> str | None:
        """``site_key`` of the tenant's irrigation zone ``zone_key``; ``None`` when absent or another tenant's."""

    @abstractmethod
    def substrate_visible(self, substrate_key: str, *, tenant_key: str) -> bool:
        """Whether the substrate is a catalogue one (no tenant) or the tenant's own (GP-NFR-058)."""

    @abstractmethod
    def reserved_among(self, candidates: list[str], *, tenant_key: str) -> set[str]:
        """The slots among ``candidates`` that a planting run of the tenant has reserved (``run_planned_at``, V-08)."""

    @abstractmethod
    def replace_slots(self, write: SlotBatchWrite) -> SlotBatchOutcome:
        """Delete the unoccupied slots named, insert the new ones and their ``has_slot`` edges — one transaction.

        Raises:
            DuplicateError: a ``slot_id`` of the location is taken (V-20, the unique index).
            WriteConflictError: a slot to delete became occupied or reserved after the service read it, or the bed's
                slots or frame changed since ``write.slot_rules_revision`` was read (#2773).
        """
