from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any

import structlog

from app.common.datetimes import today_utc
from app.common.enums import PlanRole, PlantingRunStatus, PlantingRunType, TenantRole
from app.common.exceptions import (
    ForbiddenError,
    InvalidRunStateError,
    NotFoundError,
    PlanError,
    PlanValidationError,
    ValidationError,
)
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import PlantID, PlantingRunKey
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.engines.slot_reservation_engine import LIVE_RUN_STATUSES
from app.domain.engines.watering_schedule_engine import WateringScheduleEngine
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_reservation_repository import IPlantingReservationRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_reservation import (
    QUICK_PLANTING_MAX_QUANTITY,
    MixedRunDraft,
    MixedRunSlot,
    MixedRunsWrite,
    MixedRunWrite,
    QuickPlantedPlant,
    QuickPlantingInput,
    QuickPlantingResult,
    QuickPlantWrite,
)
from app.domain.models.planting_run import SOURCE_FIELD_MODE, PlantingRun, PlantingRunEntry
from app.domain.models.site import Location, Slot
from app.domain.services.location_ownership import resolve_owned_location, resolve_owned_slot
from app.domain.services.planting_reservation_service import FreePlacement, PlantingReservationService

logger = structlog.get_logger()


class PlantingRunService:
    def __init__(
        self,
        run_repo: IPlantingRunRepository,
        plant_repo: IPlantInstanceRepository,
        engine: PlantingRunEngine,
        watering_schedule_engine: WateringScheduleEngine | None = None,
        nutrient_plan_repo=None,
        watering_repo=None,
        phase_repo: IPhaseRepository | None = None,
        site_repo: ISiteRepository | None = None,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
        care_profile_bootstrap: Callable[[Any], None] | None = None,
        rotation_validator: CropRotationValidator | None = None,
        companion_engine: CompanionPlantingEngine | None = None,
        substrate_batch_resolver: Callable[..., Any] | None = None,
        species_resolver: Callable[..., Any] | None = None,
        reservations: PlantingReservationService | None = None,
        reservation_repo: IPlantingReservationRepository | None = None,
    ) -> None:
        self._repo = run_repo
        # REQ-053 WP 3.2 — slot reservation (layout at create, planned slots at create-plants, quick planting).
        # Optional so a solitary run test can omit them; unwired, the service behaves as before WP 3.2.
        self._reservations = reservations
        self._reservation_repo = reservation_repo
        # ``SubstrateService.get_batch``-shaped: ``resolver(key, tenant_key=...)``
        # answers the batch or raises 404 for one that is not the tenant's (#1868).
        self._substrate_batch_resolver = substrate_batch_resolver
        # ``SpeciesService.get_species``-shaped: ``resolver(key, tenant_key=...)``
        # answers a species the tenant may read — global, own, granted — or 404
        # (#1871 B11). Without it an entry is refused.
        self._species_resolver = species_resolver
        self._plant_repo = plant_repo
        self._engine = engine
        self._schedule_engine = watering_schedule_engine or WateringScheduleEngine()
        self._nutrient_plan_repo = nutrient_plan_repo
        self._watering_repo = watering_repo
        self._phase_repo = phase_repo
        self._site_repo = site_repo
        self._phase_seq_repo = phase_seq_repo
        self._care_profile_bootstrap = care_profile_bootstrap
        # REQ-028/REQ-013 — the batch-creation path runs the same rotation +
        # companion checks as the single-plant path (PlantInstanceService).
        # Optional so solitary run tests can omit them; when unwired the checks
        # are skipped exactly as ``skip_validation`` does on a single plant.
        self._rotation = rotation_validator
        self._companion = companion_engine

    def _resolve_initial_phase(self, species_key: str) -> tuple[str, str]:
        """Resolve (phase_key, phase_name) for initial phase assignment.

        Tries PhaseSequence first, falls back to LifecycleConfig.
        Returns ("", "") if no phase data found.
        """
        # Try PhaseSequence first
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_species(species_key)
            if seq:
                entries = self._phase_seq_repo.get_entries_for_sequence(seq.key or "")
                if entries:
                    first = min(entries, key=lambda e: e.sequence_order)
                    defn = self._phase_seq_repo.get_definition_by_key(first.phase_definition_key)
                    name = defn.name if defn else ""
                    return first.key or "", name

        # Fallback to LifecycleConfig
        if self._phase_repo:
            lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
            if lifecycle:
                growth_phases = self._phase_repo.get_phases_by_lifecycle(lifecycle.key)
                if growth_phases:
                    first = min(growth_phases, key=lambda gp: gp.sequence_order)
                    return first.key or "", first.name

        return "", ""

    # ── Run CRUD ──────────────────────────────────────────────────────

    def list_runs(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str = "",
    ) -> tuple[list[PlantingRun], int]:
        return self._repo.get_all(offset, limit, filters, tenant_key=tenant_key)

    def list_runs_window(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict[str, Any] | None = None,
        *,
        tenant_key: str,
    ) -> list[PlantingRun]:
        """One page of the tenant's runs without the count query (MT-035, #2131).

        ``tenant_key`` is required here: an empty value is refused by the
        repository's tenant-scope guard instead of widening the page.
        """
        return self._repo.get_runs_window(offset, limit, filters, tenant_key=tenant_key)

    def get_run(self, key: PlantingRunKey, tenant_key: str = "") -> PlantingRun:
        run = self._repo.get_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(run, tenant_key, "PlantingRun")
        return run

    def _owned_run(self, key: PlantingRunKey, *, tenant_key: str) -> PlantingRun:
        """The run ``key`` of ``tenant_key``, or 404 — the load every write starts with (#2107).

        The write methods used to reload the run with :meth:`get_run` and **no**
        tenant, relying on the router having called ``get_run(key, tenant_key=…)``
        first (check-then-act, the #948 sibling-drift class). The predicate now
        lives here, unconditionally: :func:`verify_tenant_ownership` answers a
        foreign run and an empty caller tenant alike with ``NotFoundError``.
        """
        run = self._repo.get_or_raise(key)
        verify_tenant_ownership(run, tenant_key, "PlantingRun")
        return run

    def create_run(
        self,
        run: PlantingRun,
        entries: list[PlantingRunEntry] | None = None,
        *,
        tenant_key: str,
    ) -> PlantingRun:
        """Create a run owned by ``tenant_key`` (#2107).

        The run is stamped with the tenant here rather than trusted from the
        caller, and a ``clone_from_run_key`` template must be the tenant's own.
        An empty tenant is refused: every reference check below skips a run
        without one, so creating such a run would store unchecked references.
        """
        if not tenant_key:
            raise ValueError("create_run is tenant-scoped and requires a non-empty tenant_key (#2107).")
        run.tenant_key = tenant_key
        run.status = PlantingRunStatus.PLANNED
        if run.clone_from_run_key:
            entries = self._apply_clone_config(run, entries)
        # After the clone config, not before it. `_apply_clone_config` verifies the
        # *template's* tenant and then copies `template.location_key` onto this run
        # (`:138`) — and that stored key is not verified by anything, because rows
        # written before #1372 were deliberately not migrated. Checking first left
        # the clone path resolving a key nobody had looked at: clone a legacy run of
        # your own tenant that points at a foreign location, and the new run
        # inherits it. Here the check sees whichever key the run ends up with.
        self._require_owned_location(run)
        # After the clone config for the same reason as the location: the check
        # sees whichever key the run ends up with, inherited or supplied (#1868).
        self._require_owned_substrate_batch(run)
        self._require_owned_source_plant(run)
        self._require_readable_nutrient_plan(run)
        # Entries carry the run's tenant so their owned references (a
        # ``cultivar_key``) are checked — and checked before the run is stored,
        # so a foreign reference refuses the whole create rather than leaving a
        # run with a partial set of entries behind (#1871 B12, #1874 review).
        for entry in entries or []:
            entry.tenant_key = run.tenant_key
            self._require_readable_species(entry.species_key, run.tenant_key)
            self._repo.verify_entry_references(entry)
        self._require_green_manure_species(run, entries or [])
        total_qty = 0
        if entries:
            self._engine.validate_run_type_constraints(
                run.run_type,
                entries,
                run.source_plant_key,
            )
            total_qty = sum(e.quantity for e in entries)
        run.planned_quantity = total_qty
        # The reservation window starts with the run (GP-FR-065: ``planned_from`` = ``planned_start_date``).
        if run.planned_from is None:
            run.planned_from = run.planned_start_date
        # The layout of a bed with geometry is computed *before* the run is stored (GP-API-020): a refusal —
        # no spacing, too many positions, a zone overlap, the slot quota — leaves nothing behind.
        location, prepared = self._prepare_layout(run, entries or [])
        created = self._repo.create(run)
        stored_entries: list[PlantingRunEntry] = []
        if entries and created.key:
            for entry in entries:
                entry.run_key = created.key
                stored_entries.append(self._repo.create_entry(entry))
        if prepared is not None and location is not None and created.key:
            try:
                assert self._reservations is not None  # noqa: S101 — set by _prepare_layout's condition
                self._reservations.place_layout(location, created, stored_entries, prepared, tenant_key=tenant_key)
            except Exception:
                # The run and its entries are already stored; the slots are the all-or-nothing part. Take the run
                # back so a failed layout does not leave a planned run without its positions.
                self._repo.delete(created.key)
                raise
        return created

    def create_mixed_culture(
        self,
        location_key: str,
        drafts: list[MixedRunDraft],
        *,
        tenant_key: str,
        role: TenantRole,
    ) -> list[PlantingRun]:
        """Create the per-species runs of a mixed culture on one bed in **one** transaction (REQ-013 §2, #2463).

        A mixed culture is separate monoculture runs per species; the bed's layout is computed for all of them
        together (one id sequence, one quota and overlap check) and the runs, entries, layout slots and
        reservations are written in one database transaction. Every check runs before the write, so a refusal
        — or a failed write — leaves **nothing** behind and the caller never has to take a run back (which
        needs the lead role).
        """
        if not tenant_key:
            raise ValueError("create_mixed_culture is tenant-scoped and requires a non-empty tenant_key (#2463).")
        if self._site_repo is None or self._reservations is None:
            raise NotFoundError("Location", location_key)
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        location = resolve_owned_location(self._site_repo, location_key, tenant_key)
        for draft in drafts:
            self._stamp_mixed_draft(draft, location_key, tenant_key)
        entries = [draft.entry for draft in drafts]
        free = [
            FreePlacement(
                entry_index=index,
                points=draft.free_points,
                spacing_cm=draft.entry.spacing_cm,
                container_volume_l=draft.container_volume_l,
            )
            for index, draft in enumerate(drafts)
            if draft.free_points
        ]
        prepared = self._reservations.prepare_layout(location, entries, tenant_key=tenant_key, free=free)
        if free and prepared is None:
            # Points need a bed with a frame to lie in; "no layout" would silently drop them.
            raise PlanValidationError([(None, "runs", "geometry.invalid", {})])
        reserved = prepared.slots if prepared is not None else []
        writes = [
            MixedRunWrite(
                run=draft.run,
                entry=draft.entry,
                planned_from=draft.run.planned_from or today_utc(),
                planned_until=draft.run.planned_until,
                slots=[
                    MixedRunSlot(slot=item.slot, sequence=item.sequence)
                    for item in reserved
                    if item.entry_index == index
                ],
            )
            for index, draft in enumerate(drafts)
        ]
        outcome = self._reservations.place_mixed_runs(
            MixedRunsWrite(location_key=location_key, runs=writes), tenant_key=tenant_key
        )
        logger.info(
            "planting_run.mixed_culture_created",
            location_key=location_key,
            runs=len(outcome.run_keys),
            slots=len(outcome.created_slot_keys),
        )
        return [self._repo.get_or_raise(run_key) for run_key in outcome.run_keys]

    def _stamp_mixed_draft(self, draft: MixedRunDraft, location_key: str, tenant_key: str) -> None:
        """The run and entry of one species as the transaction stores them, after the reference checks.

        Everything that can refuse a single run refuses here, before any layout is computed or anything is
        written: the tenant is the caller's (never the body's), the species is readable, the cultivar is the
        tenant's, a green-manure run has suited species and the entry fits a monoculture run.
        """
        run, entry = draft.run, draft.entry
        run.tenant_key = tenant_key
        run.status = PlantingRunStatus.PLANNED
        run.run_type = PlantingRunType.MONOCULTURE
        run.location_key = location_key
        run.planned_quantity = entry.quantity
        run.planned_from = run.planned_from or run.planned_start_date
        entry.tenant_key = tenant_key
        # A key of the body is a reference: foreign and absent alike are 422 ``reference.not_found`` (GP-NFR-058).
        try:
            self._require_readable_species(entry.species_key, tenant_key)
        except NotFoundError:
            raise PlanValidationError([(None, "entry.species_key", "reference.not_found", {})]) from None
        try:
            self._repo.verify_entry_references(entry)
        except NotFoundError:
            raise PlanValidationError([(None, "entry.cultivar_key", "reference.not_found", {})]) from None
        self._require_green_manure_species(run, [entry])
        self._engine.validate_run_type_constraints(run.run_type, [entry], None)

    def _prepare_layout(self, run: PlantingRun, entries: list[PlantingRunEntry]):  # type: ignore[no-untyped-def]
        """``(bed, prepared slots)`` for a run on a bed with geometry whose entries plan a layout, else nothing."""
        if self._reservations is None or self._site_repo is None or not run.location_key or not entries:
            return None, None
        location = resolve_owned_location(self._site_repo, run.location_key, run.tenant_key)
        prepared = self._reservations.prepare_layout(location, entries, tenant_key=run.tenant_key)
        return (location, prepared) if prepared is not None else (None, None)

    def _require_green_manure_species(self, run: PlantingRun, entries: list[PlantingRunEntry]) -> None:
        """``plan_role = green_manure`` needs ``Species.green_manure_suitable`` on every entry (REQ-013, GP-FR-138)."""
        if run.plan_role is not PlanRole.GREEN_MANURE or not run.tenant_key or self._species_resolver is None:
            return
        for entry in entries:
            species = self._species_resolver(entry.species_key, tenant_key=run.tenant_key)
            if not getattr(species, "green_manure_suitable", False):
                raise PlanError(
                    "run.species_not_green_manure",
                    "A green-manure run needs species that are suited as green manure.",
                    status_code=422,
                    field="plan_role",
                    species_key=entry.species_key,
                )

    def _apply_clone_config(
        self,
        run: PlantingRun,
        entries: list[PlantingRunEntry] | None,
    ) -> list[PlantingRunEntry] | None:
        """Copy a template run's configuration into ``run`` (REQ-013 §2, Z.160).

        For succession/annual-repeat, ``clone_from_run_key`` references an
        existing run whose *configuration* (species/cultivar composition,
        nutrient plan, location, substrate batch, lifecycle config) is reused —
        but never its PlantInstances. Only fields the caller left unset are
        filled, so an explicit override on the new run always wins.
        """
        template = self._repo.get_or_raise(run.clone_from_run_key)
        verify_tenant_ownership(template, run.tenant_key, "PlantingRun")

        if run.location_key is None:
            run.location_key = template.location_key
        if run.substrate_batch_key is None:
            run.substrate_batch_key = template.substrate_batch_key
        if run.lifecycle_config_key is None:
            run.lifecycle_config_key = template.lifecycle_config_key
        if run.nutrient_plan_key is None:
            run.nutrient_plan_key = template.nutrient_plan_key

        # Copy the species composition only when the caller supplied none —
        # config (Entries) is copied, the template's plants are not.
        if entries is None:
            entries = [
                PlantingRunEntry(
                    species_key=e.species_key,
                    cultivar_key=e.cultivar_key,
                    quantity=e.quantity,
                    id_prefix=e.id_prefix,
                    spacing_cm=e.spacing_cm,
                    row_spacing_cm=e.row_spacing_cm,
                    row_direction=e.row_direction,
                    edge_margin_along_cm=e.edge_margin_along_cm,
                    edge_margin_across_cm=e.edge_margin_across_cm,
                    depth_cm=e.depth_cm,
                    depth_kind=e.depth_kind,
                    sowing_spacing_cm=e.sowing_spacing_cm,
                    thinning_to_cm=e.thinning_to_cm,
                    layout_strategy=e.layout_strategy,
                    placement_hint=e.placement_hint,
                    row_assignment=e.row_assignment,
                    notes=e.notes,
                )
                for e in self._repo.get_entries(run.clone_from_run_key)
            ]
        return entries

    def _require_owned_location(self, run: PlantingRun) -> None:
        """Refuse a ``location_key`` that is not under the run's own tenant (#1372).

        Nothing verified this, and everything downstream reads the location
        **unscoped**: ``create_plants`` asks ``get_existing_ids_at_location`` and
        ``_get_available_slots`` for the foreign location's plants and slots, writes
        each batch instance with ``self._plant_repo.create`` — bypassing
        :meth:`PlantInstanceService.create_plant` and therefore the #1349 resolution
        entirely — and then sets ``currently_occupied`` on the other tenant's slot.

        The rotation and companion guards do not catch it: they read the slot's
        neighbourhood tenant-scoped, so a foreign slot yields no findings and
        **passes**. The reference has to be refused before it is interpreted, which
        is the same ordering #1349 records for the single-plant path.

        Anchored on the parent site, never on ``Location.tenant_key`` (#1397): that
        field is persisted empty, and a guard written against it refuses every
        location — the over-rejecting failure #1352 measured.

        Skipped for a run with no tenant (seeds, migrations, light mode) and for a
        run with no location, matching the rest of this service.
        """
        self._require_owned_location_key(run.location_key, run.tenant_key)

    def _require_owned_location_key(self, location_key: str | None, tenant_key: str) -> None:
        """The same rule, applied to a value rather than to a built run.

        ``update_run`` needs it before it assigns, and ``create_run`` after it has
        a run — one predicate either way, so the two entry points cannot drift.
        """
        self._owned_location(location_key, tenant_key)

    def _owned_location(self, location_key: str | None, tenant_key: str) -> Location | None:
        """:meth:`_require_owned_location_key` that hands back the resolved location (one scoped read).

        ``None`` where the rule is skipped (no tenant, no location): there is then no anchor to read through.
        """
        if not tenant_key or not location_key:
            return None
        # Fail closed without the anchor (#1876 review, SEC-004): a tenant request
        # whose location cannot be resolved is refused, not stored.
        if self._site_repo is None:
            raise NotFoundError("Location", location_key)
        return resolve_owned_location(self._site_repo, location_key, tenant_key)

    def _require_owned_source_plant(self, run: PlantingRun) -> None:
        """Refuse a ``source_plant_key`` that is not a plant of the run's tenant (#1872 C1).

        A clone run names its mother plant; the key was only required to be
        present and was stored and echoed as given. Unknown and foreign answer
        the same 404. Skipped for a run with no tenant (seeds, migrations).
        """
        if not run.source_plant_key or not run.tenant_key:
            return
        plant = self._plant_repo.get_by_key(run.source_plant_key)
        if plant is None or plant.tenant_key != run.tenant_key:
            raise NotFoundError("PlantInstance", run.source_plant_key)

    def _require_readable_nutrient_plan(self, run: PlantingRun) -> None:
        """Refuse a ``nutrient_plan_key`` the run's tenant may not read (#2107 review, S3).

        The create body cannot carry the key; it arrives only through
        :meth:`_apply_clone_config`, copied from a template run that may predate
        #950 and name another tenant's plan. Read access, like
        :meth:`assign_nutrient_plan` — global plans stay usable (#324). Without a
        wired plan repository a plan reference is refused, not stored unchecked.
        """
        if not run.nutrient_plan_key:
            return
        if self._nutrient_plan_repo is None:
            raise NotFoundError("NutrientPlan", run.nutrient_plan_key)
        self._readable_plan_or_raise(run.nutrient_plan_key, run.tenant_key)

    def _require_readable_species(self, species_key: str, tenant_key: str) -> None:
        """Refuse an entry species the tenant may not read (#1871 B11).

        An entry's ``species_key`` came from request bodies and was stored with
        an edge to the species, then copied onto every plant ``create_plants``
        built from it. Skipped for a run with no tenant (seeds, migrations).
        """
        if not tenant_key:
            return
        if self._species_resolver is None:
            raise NotFoundError("Species", species_key)
        self._species_resolver(species_key, tenant_key=tenant_key)

    def _species_is_readable(self, species_key: str, tenant_key: str) -> bool:
        """Whether an entry's *stored* species is one the run's tenant may read (#1963).

        The read-side twin of :meth:`_require_readable_species`: that one refuses a
        species on the way in, this one is asked about rows that are already stored,
        where a legacy entry (written before #1876) may still name another tenant's
        private species — v0067 dropped its edge, not its field. A run with no tenant
        (seeds, migrations) is not judged, matching the write side.
        """
        if not tenant_key:
            return True
        try:
            self._require_readable_species(species_key, tenant_key)
        except NotFoundError:
            return False
        return True

    def _require_owned_substrate_batch(self, run: PlantingRun) -> None:
        """Refuse a ``substrate_batch_key`` that is not the run's tenant's (#1868).

        The key came from the request body or a cloned template and was stored
        as given; the repository then wrote a ``run_uses_substrate`` edge to the
        batch it named — any tenant's. A batch has exactly one owner (#1195), so
        it is resolved strictly under the run's tenant. Without a wired resolver
        a batch reference is refused, never waved through.

        Skipped for a run with no tenant (seeds, migrations, light mode) and for
        a run with no batch, like the location rule.
        """
        if not run.tenant_key or not run.substrate_batch_key:
            return
        if self._substrate_batch_resolver is None:
            raise NotFoundError("SubstrateBatch", run.substrate_batch_key)
        self._substrate_batch_resolver(run.substrate_batch_key, tenant_key=run.tenant_key)

    def update_run(self, key: PlantingRunKey, data: dict, *, tenant_key: str) -> PlantingRun:
        run = self._owned_run(key, tenant_key=tenant_key)
        old_location_key = run.location_key
        allowed_fields = {"name", "notes", "planned_start_date", "location_key"}
        # Resolved from the incoming value, before the model is touched (#1372).
        # Checking the mutated ``run`` instead would be correct against the
        # repository — which deserialises a fresh model per read — and would leave
        # the caller's in-memory run carrying a key that was refused. Refusing the
        # value itself has no such seam.
        if "location_key" in data:
            self._require_owned_location_key(data["location_key"], run.tenant_key)
        self._require_reservation_unmoved(run, data)
        old_start = run.planned_start_date
        for field, value in data.items():
            if field in allowed_fields:
                setattr(run, field, value)
        self._follow_start_date(run, old_start)
        updated = self._repo.update(key, run)

        # When location changes on an active run, reassign plants to new slots
        new_location_key = updated.location_key
        if old_location_key != new_location_key and updated.status in (
            PlantingRunStatus.ACTIVE,
            PlantingRunStatus.HARVESTING,
        ):
            self._reassign_plant_slots(key, new_location_key, tenant_key=tenant_key)

        return updated

    def _require_reservation_unmoved(self, run: PlantingRun, data: dict[str, Any]) -> None:
        """A run with reservations keeps its start date and its bed: the edges carry both (GP-FR-065).

        V-08 judged the window and the slots belong to one bed; moving either would leave the edges stating
        something the run no longer has. Release the reservation (``DELETE …/plan-slots/{slot}``) and plan again.
        """
        if self._reservation_repo is None or not run.key:
            return
        moves_start = "planned_start_date" in data and data["planned_start_date"] != run.planned_start_date
        moves_bed = "location_key" in data and data["location_key"] != run.location_key
        if not (moves_start or moves_bed):
            return
        if self._reservation_repo.reservations_of_run(run.key, tenant_key=run.tenant_key):
            code, field = (
                ("run.reserved_window_fixed", "planned_start_date")
                if moves_start
                else ("run.reserved_bed_fixed", "location_key")
            )
            raise PlanError(
                code,
                "The run reserves slots of its bed for its start date; release them before moving either.",
                status_code=422,
                field=field,
            )

    @staticmethod
    def _follow_start_date(run: PlantingRun, old_start: date | None) -> None:
        """``planned_from`` is the start date unless it was set apart (GP-FR-065): it follows a moved start."""
        if run.planned_start_date == old_start or run.planned_from not in (None, old_start):
            return
        if run.planned_until and run.planned_start_date and run.planned_until < run.planned_start_date:
            raise PlanError(
                "run.window_reversed",
                "The start date must not lie after the end of the reservation window.",
                status_code=422,
                field="planned_start_date",
            )
        run.planned_from = run.planned_start_date

    def delete_run(self, key: PlantingRunKey, *, tenant_key: str) -> bool:
        run = self._owned_run(key, tenant_key=tenant_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("delete", run.status.value)
        # The reservations go with the run, and so do the layout slots only it used (GP-FR-066).
        if self._reservation_repo is not None:
            self._reservation_repo.drop_run_reservations(key, remove_layout_slots=True)
        return self._repo.delete(key)

    # ── Entry management ──────────────────────────────────────────────

    def list_entries(self, run_key: PlantingRunKey) -> list[PlantingRunEntry]:
        self.get_run(run_key)
        return self._repo.get_entries(run_key)

    def add_entry(self, run_key: PlantingRunKey, entry: PlantingRunEntry, *, tenant_key: str) -> PlantingRunEntry:
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("add_entry", run.status.value)
        entry.run_key = run_key
        # The entry inherits the run's tenant (SEC-004, #1112). Not for access —
        # ``_owned_run`` above resolved the run tenant-scoped — but so the
        # repository's owned-reference guard has a tenant to compare a
        # body-supplied `cultivar_key` against. Without it the guard is skipped.
        entry.tenant_key = run.tenant_key
        self._require_readable_species(entry.species_key, run.tenant_key)
        created = self._repo.create_entry(entry)
        # Update planned_quantity
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return created

    ENTRY_UPDATABLE_FIELDS = {
        "species_key",
        "cultivar_key",
        "quantity",
        "id_prefix",
        "spacing_cm",
        "row_spacing_cm",
        "row_direction",
        "edge_margin_along_cm",
        "edge_margin_across_cm",
        "depth_cm",
        "depth_kind",
        "sowing_spacing_cm",
        "thinning_to_cm",
        "layout_strategy",
        "placement_hint",
        "row_assignment",
        "notes",
    }
    ENTRY_REQUIRED_FIELDS = {"species_key", "quantity", "id_prefix"}

    def update_entry(
        self,
        run_key: PlantingRunKey,
        entry_key: str,
        data: dict,
        *,
        tenant_key: str,
    ) -> PlantingRunEntry:
        """Partially update a run entry (REQ-013).

        Only keys present in ``data`` are applied; required fields
        (``species_key``, ``quantity``, ``id_prefix``) must not be nulled. The
        merged entry is re-validated against the model so field constraints
        (``quantity >= 1``, ``id_prefix`` pattern) keep applying.
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("update_entry", run.status.value)
        existing = self._entry_of_run(run_key, entry_key)

        patch = {k: v for k, v in data.items() if k in self.ENTRY_UPDATABLE_FIELDS}
        nulled_required = self.ENTRY_REQUIRED_FIELDS & {k for k, v in patch.items() if v is None}
        if nulled_required:
            raise ValidationError(f"Fields cannot be null: {', '.join(sorted(nulled_required))}")

        merged = PlantingRunEntry.model_validate({**existing.model_dump(by_alias=False), **patch})
        # Re-stamp from the run rather than trusting the stored value: a row
        # predating the v0042 backfill carries "", and an update is exactly the
        # moment its `cultivar_key` can be re-pointed at a foreign cultivar. A
        # merged entry that kept the empty tenant would skip the guard on the one
        # path that needs it most.
        merged.tenant_key = run.tenant_key
        if "species_key" in patch:
            self._require_readable_species(merged.species_key, run.tenant_key)
        updated = self._repo.update_entry(entry_key, merged)
        # Update planned_quantity
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return updated

    def delete_entry(self, run_key: PlantingRunKey, entry_key: str, *, tenant_key: str) -> bool:
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("delete_entry", run.status.value)
        self._entry_of_run(run_key, entry_key)
        result = self._repo.delete_entry(entry_key)
        # Update planned_quantity
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return result

    def _entry_of_run(self, run_key: PlantingRunKey, entry_key: str) -> PlantingRunEntry:
        """The entry ``entry_key`` **of run** ``run_key``, or 404 (#1867).

        An entry is addressed through its run, and the run is what the caller's
        tenant was checked against. Loading the entry by its key alone let a
        member of one tenant edit or delete any tenant's entry through a run of
        their own. A foreign and an unknown entry answer the same.
        """
        entry = self._repo.get_entry_or_raise(entry_key)
        if entry.run_key != run_key:
            raise NotFoundError("PlantingRunEntry", entry_key)
        return entry

    # ── Batch operations ──────────────────────────────────────────────

    def _validate_batch_planting(self, plant_specs: list[dict], available_slots: list, tenant_key: str) -> None:
        """Run rotation + companion checks for every slot-assigned batch plant.

        Mirrors ``PlantInstanceService.create_plant``: each instance that will
        receive a slot is validated against crop-rotation history and companion
        compatibility at that slot; instances without a slot (overflow beyond the
        available slots) are skipped, matching the single-plant ``if plant.slot_key``
        guard. No-op when the engines are unwired.

        ``tenant_key`` is the run's own — both engines read the slot's history and
        neighbourhood, which are tenant-scoped since #927.

        A run with no tenant **refuses to plant** rather than planting unchecked
        (#952). This branch used to ``return`` on an empty ``tenant_key``, which
        skipped crop-rotation and companion-planting validation altogether: a
        fail-*open* on a business rule, in a codebase whose tenant handling is
        otherwise fail-closed, and a silent divergence from the single-plant path
        — ``PlantInstanceService.create_plant`` has no such guard and raises out
        of ``_require_tenant_key`` on the same data. The two now agree that a
        tenantless run is a defect to surface, not a validation to drop; the
        error names the cause instead of surfacing as a bare ``ValueError`` from
        two layers down. Runs are stamped on create and backfilled by
        ``v0004_backfill_tenant_key``, so this is unreachable in normal operation.
        """
        if self._rotation is None or self._companion is None:
            return
        if not tenant_key:
            raise ValidationError(
                "This planting run carries no tenant, so its crop-rotation and companion-planting "
                "checks cannot be run against the slot's history. Planting is refused rather than "
                "performed unvalidated."
            )
        for i, spec in enumerate(plant_specs):
            slot = available_slots[i] if i < len(available_slots) else None
            slot_key = slot.key if slot is not None else None
            if not slot_key:
                continue
            self._rotation.validate_or_raise(slot_key, spec["species_key"], tenant_key=tenant_key)
            self._companion.check_or_raise(spec["species_key"], slot_key, tenant_key=tenant_key)

    def create_plants(
        self,
        run_key: PlantingRunKey,
        *,
        tenant_key: str,
        assign_to_slots: bool = True,
        planted_on: date | None = None,
    ) -> dict:
        """Batch-create PlantInstances from run entries.

        ``assign_to_slots`` (REQ-053 GP-FR-066, GP-API-023) places the plants first on the slots the run reserved
        (``run_planned_at``), per entry in ``sequence`` order, and only then on free slots of the bed as before;
        ``False`` creates the plants without a slot. Reserved slots that stay unused stay reserved until the run
        ends or the grower releases them. ``planted_on`` defaults to today (UTC).
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("create_plants", run.status.value)
        # The stored location is re-resolved under the tenant before its slots are
        # read or occupied (#2107 review, W2): create/update check the key on the
        # way in, but a run written before #1372 may still name a foreign one.
        bed = self._owned_location(run.location_key, tenant_key)

        entries = self._repo.get_entries(run_key)
        if not entries:
            raise ValueError("Run has no entries.")
        # The stored species of every entry is resolved under the run's tenant before the
        # phase data is read through it or a plant is stamped with it: an entry written
        # before #1876 can still name another tenant's species (#1963).
        for entry in entries:
            self._require_readable_species(entry.species_key, run.tenant_key)

        self._engine.validate_run_type_constraints(
            run.run_type,
            entries,
            run.source_plant_key,
        )

        location_key = run.location_key or "LOC"
        existing_ids = set()
        if run.location_key:
            existing_ids = self._repo.get_existing_ids_at_location(run.location_key)

        plant_specs = self._engine.generate_plant_ids(location_key, entries, existing_ids)

        # Resolve the slot of every plant: reserved slots first (per entry, in ``sequence`` order), then free ones
        available_slots = self._slots_for_specs(run, plant_specs, assign_to_slots=assign_to_slots)

        # Rotation + companion checks — mirror the single-plant path
        # (PlantInstanceService.create_plant). Only slot-assigned instances are
        # validated; overflow plants beyond the available slots have slot_key=None
        # and skip the checks exactly as a single plant with slot_key=None would.
        # Validated up-front so a conflict raises before any PlantInstance is
        # written (no partial batch left behind on failure).
        self._validate_batch_planting(plant_specs, available_slots, run.tenant_key)

        # Resolve initial phase per species — prefer PhaseSequence, fallback to LifecycleConfig
        initial_phases: dict[str, tuple[str, str]] = {}  # species_key -> (phase_key, phase_name)
        for entry in entries:
            if entry.species_key not in initial_phases:
                pk, pn = self._resolve_initial_phase(entry.species_key)
                if pk:
                    initial_phases[entry.species_key] = (pk, pn)

        now = datetime.now(UTC)
        # The plants stand in the run's location and carry it, with its garden, exactly as the field-mode path
        # (`quick_plant`) stamps them: every bed read finds a bed's plants by `location_key` - the plant states
        # (`GET /locations/{key}/plant-states`), the plant check of a care event (`position_corrected`, GP-FR-068),
        # the bed plan. Without it a plant created here stood on its slot but was invisible to all of them.
        # `bed` is the location resolved under the tenant above (ownership and object in one read).

        # Resolve initial phase for the run (from first entry's species)
        phase_key = ""
        phase_name = "seedling"
        if entries:
            pk, pn = initial_phases.get(entries[0].species_key, ("", "seedling"))
            phase_key = pk
            phase_name = pn

        created_plants = []
        occupied_slot_keys: set[str] = set()
        for i, spec in enumerate(plant_specs):
            slot = available_slots[i]
            slot_key = slot.key if slot is not None else None
            species_phase_key, _ = initial_phases.get(spec["species_key"], ("", ""))
            plant = PlantInstance(
                # The run's own tenant (#951). Batch-created instances were built
                # without one although ``run.tenant_key`` was right here, so they
                # persisted with the model default ``""`` — invisible to every
                # tenant-scoped plant read, and the reason ``get_slot_for_plant``
                # had to note this path as the one that does not stamp.
                tenant_key=run.tenant_key,
                instance_id=spec["instance_id"],
                species_key=spec["species_key"],
                cultivar_key=spec.get("cultivar_key"),
                slot_key=slot_key,
                site_key=bed.site_key if bed is not None else None,
                location_key=run.location_key,
                # UTC, like ``now`` two lines down: both stamp the same event and
                # the reports that subtract them must not straddle two clocks.
                planted_on=planted_on or today_utc(),
                current_phase_key=species_phase_key or None,
                current_phase_started_at=now,
            )
            created = self._plant_repo.create(plant)
            # REQ-022 — every plant this run creates gets its care profile, exactly as
            # a plant created through `PlantInstanceService.create_plant` does. This
            # path writes straight to the repository (the bypass documented in
            # `plant_instance_service`'s module docstring since #1349), so the
            # bootstrap added in #1422 round 3 did not reach it: a run of forty plants
            # produced forty plants that would never have received a care reminder.
            #
            # Best-effort per plant: one profile that could not be written must not
            # abort a batch the user already committed to.
            if self._care_profile_bootstrap is not None and created.key:
                try:
                    self._care_profile_bootstrap(created)
                except Exception:  # noqa: BLE001
                    logger.error("care_profile_bootstrap_failed", plant_key=created.key, exc_info=True)
            if created.key:
                self._repo.link_run_to_plant(run_key, created.key)
                # Create initial phase history per plant
                if self._phase_repo and species_phase_key:
                    _, sp_name = initial_phases[spec["species_key"]]
                    hist = PhaseHistory(
                        plant_instance_key=created.key,
                        phase_key=species_phase_key,
                        phase_name=sp_name,
                        entered_at=now,
                        transition_reason="initial",
                    )
                    self._phase_repo.create_phase_history(hist)
            # Mark slot as occupied (once: a row or a zone takes several plants)
            if slot is not None and slot_key and self._site_repo and slot_key not in occupied_slot_keys:
                slot.currently_occupied = True
                self._site_repo.update_slot(slot_key, slot)
                occupied_slot_keys.add(slot_key)
            created_plants.append(created)

        # Transition to active and set run-level phase
        run.actual_quantity = len(created_plants)
        run.status = PlantingRunStatus.ACTIVE
        run.started_at = now
        run.current_phase_key = phase_key or None
        run.current_phase_started_at = now
        self._repo.update(run_key, run)

        # Create phase history on the run as well
        if self._phase_repo and phase_key:
            history = PhaseHistory(
                plant_instance_key=run_key,
                phase_key=phase_key,
                phase_name=phase_name,
                entered_at=now,
                transition_reason="initial",
            )
            self._phase_repo.create_phase_history(history)

        return {
            "run_key": run_key,
            "created_count": len(created_plants),
            "plant_keys": [p.key for p in created_plants if p.key],
            "instance_ids": [p.instance_id for p in created_plants],
            "slots_assigned": sum(1 for slot in available_slots if slot is not None),
            # The slot of each plant that got one, in the order of ``plant_keys`` (GP-FR-066).
            "assigned_slots": [slot.key for slot in available_slots if slot is not None and slot.key],
        }

    # ── Quick planting (GP-API-017, GP-UX-027) ───────────────────────

    def quick_plant(
        self,
        location_key: str,
        *,
        tenant_key: str,
        role: TenantRole,
        request: QuickPlantingInput,
    ) -> QuickPlantingResult:
        """*I planted n of this species here*: run, entry, slots and plants in **one** transaction (GP-API-017).

        For the field mode, where a two-step "plan, then create plants" is no option. The run is ``active``
        straight away with ``source = field_mode``. On a bed with geometry and a ``spacing_cm`` the plants stand
        on a computed layout (grid, rows or triangular); without either, or beyond what the bed holds, they are
        recorded in the bed without a position and a warning says so. Rotation and companion hints belong to
        the planting dialog (WP 3.6) — what was planted in the field is recorded, not refused.
        """
        if self._site_repo is None or self._reservation_repo is None:
            raise NotFoundError("Location", location_key)
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        if request.quantity > QUICK_PLANTING_MAX_QUANTITY:
            raise PlanError(
                "plan.quota_exceeded",
                f"A quick planting holds at most {QUICK_PLANTING_MAX_QUANTITY} plants.",
                status_code=422,
                limit=QUICK_PLANTING_MAX_QUANTITY,
                current=request.quantity,
            )
        location = resolve_owned_location(self._site_repo, location_key, tenant_key)
        # A key of the body is a reference: foreign and absent alike are 422 ``reference.not_found`` (GP-NFR-058).
        try:
            species = self._readable_species(request.species_key, tenant_key)
        except NotFoundError:
            raise PlanValidationError([(None, "species_key", "reference.not_found", {})]) from None
        planted_on = request.planted_on or today_utc()
        now = datetime.now(UTC)

        entry = PlantingRunEntry(
            tenant_key=tenant_key,
            species_key=request.species_key,
            cultivar_key=request.cultivar_key,
            quantity=request.quantity,
            id_prefix=request.id_prefix or self._id_prefix_of(species),
            spacing_cm=request.spacing_cm,
            row_spacing_cm=request.row_spacing_cm,
            row_direction=request.row_direction,
            layout_strategy=request.layout_strategy,
            notes=request.notes,
        )
        try:
            self._repo.verify_entry_references(entry)
        except NotFoundError:
            raise PlanValidationError([(None, "cultivar_key", "reference.not_found", {})]) from None
        run = PlantingRun(
            tenant_key=tenant_key,
            name=request.name or f"Quick planting {planted_on.isoformat()}",
            run_type=PlantingRunType.MONOCULTURE,
            status=PlantingRunStatus.ACTIVE,
            planned_quantity=request.quantity,
            actual_quantity=request.quantity,
            location_key=location_key,
            planned_start_date=planted_on,
            planned_from=planted_on,
            started_at=now,
            plan_role=request.plan_role,
            rotation_override_reason=request.rotation_override_reason,
            source=SOURCE_FIELD_MODE,
            notes=request.notes,
        )
        self._require_green_manure_species(run, [entry])

        slots, warnings = self._quick_layout(location, entry, request, tenant_key=tenant_key)
        existing_ids = self._repo.get_existing_ids_at_location(location_key)
        specs = self._engine.generate_plant_ids(location_key, [entry], existing_ids)
        phase_key, phase_name = self._resolve_initial_phase(request.species_key)
        plants = [
            QuickPlantedPlant(
                plant=PlantInstance(
                    tenant_key=tenant_key,
                    instance_id=spec["instance_id"],
                    species_key=spec["species_key"],
                    cultivar_key=spec.get("cultivar_key"),
                    site_key=location.site_key,
                    location_key=location_key,
                    planted_on=planted_on,
                    current_phase_key=phase_key or None,
                    current_phase_started_at=now,
                ),
                slot_index=index if index < len(slots) else None,
                history=self._history_of(phase_key, phase_name, now),
            )
            for index, spec in enumerate(specs)
        ]
        run.current_phase_key = phase_key or None
        run.current_phase_started_at = now
        outcome = self._reservation_repo.quick_plant(
            QuickPlantWrite(
                location_key=location_key,
                run=run,
                entry=entry,
                slots=slots[: len(plants)],
                plants=plants,
                run_history=self._history_of(phase_key, phase_name, now),
            )
        )
        # REQ-022 — every plant gets its care profile, best-effort per plant (as ``create_plants`` does).
        if self._care_profile_bootstrap is not None:
            for item, plant_key in zip(plants, outcome.plant_keys, strict=True):
                try:
                    self._care_profile_bootstrap(item.plant.model_copy(update={"key": plant_key}))
                except Exception:  # noqa: BLE001
                    logger.error("care_profile_bootstrap_failed", plant_key=plant_key, exc_info=True)
        logger.info(
            "planting_run.quick_planted",
            run_key=outcome.run_key,
            location_key=location_key,
            plants=len(outcome.plant_keys),
            slots=len(outcome.created_slot_keys),
        )
        return QuickPlantingResult(
            run_key=outcome.run_key,
            entry_key=outcome.entry_key,
            created_slot_keys=outcome.created_slot_keys,
            plant_keys=outcome.plant_keys,
            instance_ids=[p.plant.instance_id for p in plants],
            warnings=warnings,
        )

    def _readable_species(self, species_key: str, tenant_key: str) -> Any:
        """The species the tenant may read, or 404 (#1871 B11)."""
        if self._species_resolver is None:
            raise NotFoundError("Species", species_key)
        return self._species_resolver(species_key, tenant_key=tenant_key)

    @staticmethod
    def _id_prefix_of(species: Any) -> str:
        """Three capitals from the scientific name (``Solanum lycopersicum`` -> ``SOL``); ``PLT`` without one."""
        letters = "".join(ch for ch in str(getattr(species, "scientific_name", "") or "").upper() if "A" <= ch <= "Z")
        return letters[:3] if len(letters) >= 2 else "PLT"

    @staticmethod
    def _history_of(phase_key: str, phase_name: str, now: datetime) -> PhaseHistory | None:
        if not phase_key:
            return None
        return PhaseHistory(phase_key=phase_key, phase_name=phase_name, entered_at=now, transition_reason="initial")

    def _quick_layout(
        self, location: Any, entry: PlantingRunEntry, request: QuickPlantingInput, *, tenant_key: str
    ) -> tuple[list[Slot], list[str]]:
        """The slots of a quick planting and the warnings: a layout when the bed and the request allow one."""
        if request.layout_strategy is None or request.spacing_cm is None or self._reservations is None:
            return [], []
        if location.geometry is None:
            return [], ["layout.bed_without_geometry"]
        prepared = self._reservations.prepare_layout(location, [entry], tenant_key=tenant_key)
        if prepared is None:
            return [], []
        slots = [item.slot for item in prepared.slots][: request.quantity]
        warnings = [w.code for w in prepared.warnings]
        if len(slots) < request.quantity:
            warnings.append("layout.capacity_exceeded")
        for slot in slots:
            slot.currently_occupied = True
        return slots, warnings

    def adopt_plants(self, run_key: PlantingRunKey, plant_keys: list[str], *, tenant_key: str) -> dict:
        """Adopt existing standalone PlantInstances into the run.

        ``tenant_key`` is keyword-only and has no default (#1973): the plant is
        loaded by key through the unscoped ``get_by_key``, and the write that follows
        (``link_run_to_plant`` + the run's phase) is aimed at it, so the predicate
        sits here on the plant rather than on the run alone. A plant of another
        tenant is answered exactly like an unknown key ("Plant not found", no
        existence oracle) and nothing is linked. An empty ``tenant_key`` owns
        nothing and is refused, not read as "skip the check".

        Validates:
        - Run must belong to the tenant
        - Run must be planned or active
        - Each plant must not be in another active run
        - Each plant must not be removed
        - Species must match the run's entry
        """
        if not tenant_key:
            raise NotFoundError("PlantingRun", run_key)
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status not in (PlantingRunStatus.PLANNED, PlantingRunStatus.ACTIVE):
            raise InvalidRunStateError("adopt_plants", run.status.value)

        entries = self._repo.get_entries(run_key)
        allowed_species = {e.species_key for e in entries}

        adopted: list[str] = []
        skipped: list[dict] = []

        # Deduplicated: a repeated key would be linked and counted twice.
        for pk in dict.fromkeys(plant_keys):
            plant = self._plant_repo.get_by_key(pk)
            if plant is None or plant.tenant_key != tenant_key:
                skipped.append({"plant_key": pk, "reason": "Plant not found"})
                continue
            if plant.removed_on is not None:
                skipped.append({"plant_key": pk, "reason": "Plant is removed"})
                continue
            if allowed_species and plant.species_key not in allowed_species:
                skipped.append({"plant_key": pk, "reason": f"Species {plant.species_key} does not match run entry"})
                continue

            # Check not in another active run
            existing_runs = self._repo.get_runs_for_plant(pk)
            in_active_run = any(
                r.status in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING) for r in existing_runs
            )
            if in_active_run:
                skipped.append({"plant_key": pk, "reason": "Already in an active run"})
                continue

            # Link plant to run (plant keeps its current phase)
            self._repo.link_run_to_plant(run_key, pk)

            adopted.append(pk)

        # Update quantities
        if adopted:
            run.actual_quantity = (run.actual_quantity or 0) + len(adopted)
            # If run was planned and now has plants, transition to active
            if run.status == PlantingRunStatus.PLANNED:
                now = datetime.now(UTC)
                run.status = PlantingRunStatus.ACTIVE
                run.started_at = now
            # Set initial run phase from first adopted plant if run has none
            if not run.current_phase_key:
                first_plant = self._plant_repo.get_by_key(adopted[0])
                if first_plant and first_plant.current_phase_key:
                    run.current_phase_key = first_plant.current_phase_key
                    run.current_phase_started_at = first_plant.current_phase_started_at or datetime.now(UTC)
            self._repo.update(run_key, run)

        return {
            "run_key": run_key,
            "adopted_count": len(adopted),
            "adopted_keys": adopted,
            "skipped": skipped,
            "run_status": run.status.value,
            "run_phase": run.current_phase_key,
        }

    # ── Slot helpers ────────────────────────────────────────────────────

    def _get_available_slots(self, location_key: str | None) -> list:
        """Return unoccupied slots at the given location, sorted by slot_id."""
        if not location_key or not self._site_repo:
            return []
        slots = self._site_repo.get_slots_by_location(location_key)
        # Archived slots are the history of a cleared bed (GP-FR-055): never a place to plant again.
        return sorted(
            [s for s in slots if not s.currently_occupied and s.key and s.archived_at is None],
            key=lambda s: s.slot_id,
        )

    def _slots_for_specs(
        self, run: PlantingRun, plant_specs: list[dict[str, Any]], *, assign_to_slots: bool
    ) -> list[Slot | None]:
        """The slot of each plant spec, in spec order (``None`` = no slot) — REQ-053 GP-FR-066.

        The run's reserved slots come first, per entry in ``sequence`` order; a row or zone slot takes up to its
        ``capacity_plants`` plants, a position one. Once an entry's reservation is used up its plants fall back
        to the free slots of the bed, which never include a slot any live run (this one for another entry too)
        has reserved.
        """
        if not assign_to_slots:
            return [None] * len(plant_specs)
        # The bed is read once; the reservations are asked for once per question (this run's, anyone's, the plants).
        bed_slots = (
            self._site_repo.get_slots_by_location(run.location_key) if self._site_repo and run.location_key else []
        )
        reserved = self._reserved_slots_by_entry(run, bed_slots)
        reserved_anywhere = self._live_reserved_slot_keys(run, bed_slots)
        free = sorted(
            (
                slot
                for slot in bed_slots
                if slot.key
                and not slot.currently_occupied
                and slot.archived_at is None
                and slot.key not in reserved_anywhere
            ),
            key=lambda slot: slot.slot_id,
        )
        used: dict[str, int] = {}
        free_cursor = 0
        slots: list[Slot | None] = []
        for spec in plant_specs:
            queue = reserved.get(spec.get("entry_key") or "", [])
            chosen: Slot | None = None
            while queue and chosen is None:
                head = queue[0]
                if used.get(head.key or "", 0) < (head.capacity_plants if head.slot_role.value != "position" else 1):
                    chosen = head
                else:
                    queue.pop(0)
            if chosen is None:
                while free_cursor < len(free) and (free[free_cursor].key or "") in used:
                    free_cursor += 1
                if free_cursor < len(free):
                    chosen = free[free_cursor]
                    free_cursor += 1
            if chosen is not None:
                used[chosen.key or ""] = used.get(chosen.key or "", 0) + 1
            slots.append(chosen)
        return slots

    def _reserved_slots_by_entry(self, run: PlantingRun, bed_slots: list[Slot]) -> dict[str, list[Slot]]:
        """The run's reserved slots per entry in ``sequence`` order; archived or foreign-bed slots are dropped."""
        if self._reservation_repo is None or not run.key or not run.location_key:
            return {}
        by_entry: dict[str, list[Slot]] = {}
        reservations = self._reservation_repo.reservations_of_run(run.key, tenant_key=run.tenant_key)
        # A position slot that still holds an earlier run's plant (a follow-up crop planned for later) is skipped.
        standing = {
            plant.slot_key
            for plant in self._reservation_repo.active_plants_in(
                [r.slot_key for r in reservations], tenant_key=run.tenant_key
            )
            if plant.run_key != run.key
        }
        by_key = {slot.key: slot for slot in bed_slots if slot.key}
        for reservation in sorted(reservations, key=lambda r: (r.entry_key, r.sequence)):
            slot = by_key.get(reservation.slot_key)
            if slot is None or slot.archived_at is not None:
                continue  # gone, archived, or never a slot of this bed
            if slot.slot_role.value == "position" and slot.key in standing:
                continue
            by_entry.setdefault(reservation.entry_key, []).append(slot)
        return by_entry

    def _live_reserved_slot_keys(self, run: PlantingRun, bed_slots: list[Slot]) -> set[str]:
        """Slots of the run's bed that a live run — any, this one included — has reserved (the fallback keeps off)."""
        if self._reservation_repo is None:
            return set()
        slot_keys = [s.key for s in bed_slots if s.key]
        return {
            r.slot_key
            for r in self._reservation_repo.reservations_for(slot_keys, tenant_key=run.tenant_key)
            if r.run_status in LIVE_RUN_STATUSES
        }

    def _owned_run_plant_rows(self, run_key: PlantingRunKey, tenant_key: str) -> list[dict[str, Any]]:
        """The run's attached plant rows whose plant belongs to ``tenant_key`` (#2107 review SEC-001).

        ``get_run_plants`` follows ``run_contains`` edges, which are stored data,
        not proof of ownership: a legacy edge can point at another tenant's plant.
        Every row is re-resolved through the plant repository and kept only when
        that plant is the caller's; an empty tenant keeps nothing.
        """
        rows: list[dict[str, Any]] = []
        for row in self._repo.get_run_plants(run_key, include_detached=False):
            plant_key = row.get("_key") or row.get("key", "")
            plant = self._plant_repo.get_by_key(plant_key) if plant_key else None
            if plant is not None and tenant_key and plant.tenant_key == tenant_key:
                rows.append(row)
        return rows

    def _reassign_plant_slots(
        self,
        run_key: PlantingRunKey,
        new_location_key: str | None,
        *,
        tenant_key: str,
    ) -> None:
        """Clear the run's slot assignments and assign the new location's slots.

        Both sides are re-checked under ``tenant_key`` at action time (#2107
        review, W2). A legacy run can point at a foreign location, and its
        plants at foreign slots: the release clears the plant's own
        ``slot_key`` but frees only a slot the tenant owns, and the new
        location is resolved before one of its slots is occupied.
        """
        if not self._site_repo:
            return
        new_location = self._owned_location(new_location_key, tenant_key)

        # Only the tenant's own plants are moved: a legacy run edge to another
        # tenant's plant is skipped, not re-slotted (#2107 review SEC-001 sweep).
        plants_raw = self._owned_run_plant_rows(run_key, tenant_key)

        # Release old slots
        for p in plants_raw:
            slot_key = p.get("slot_key")
            if slot_key:
                plant_key = p.get("_key") or p.get("key", "")
                plant = self._plant_repo.get_by_key(plant_key)
                if plant:
                    plant.slot_key = None
                    self._plant_repo.update(plant_key, plant)
                try:
                    slot, _location = resolve_owned_slot(self._site_repo, slot_key, tenant_key)
                except NotFoundError:
                    continue  # a foreign or vanished slot is not this tenant's to free
                slot.currently_occupied = False
                self._site_repo.update_slot(slot_key, slot)

        # Move every plant to the new location - its bed and garden, as `create_plants` stamps them (bed reads
        # find a bed's plants by `location_key`) - and onto the new location's available slots while they last.
        available_slots = self._get_available_slots(new_location_key)
        for i, p in enumerate(plants_raw):
            plant_key = p.get("_key") or p.get("key", "")
            plant = self._plant_repo.get_by_key(plant_key)
            if not plant:
                continue
            plant.location_key = new_location_key
            plant.site_key = new_location.site_key if new_location is not None else None
            target = available_slots[i] if i < len(available_slots) else None
            if target is not None and target.key:
                plant.slot_key = target.key
                target.currently_occupied = True
                self._site_repo.update_slot(target.key, target)
            self._plant_repo.update(plant_key, plant)

    def transition(
        self,
        run_key: PlantingRunKey,
        target_phase_key: str,
        target_phase_name: str = "",
        *,
        tenant_key: str,
    ) -> dict:
        """Run-level phase transition — all plants in the run share this phase.

        REQ-013 v2.0: The phase lives on the PlantingRun, not on individual
        PlantInstances. No per-plant exclude is possible.
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("transition", run.status.value)

        now = datetime.now(UTC)
        previous_phase = run.current_phase_key

        # Close open phase history on the run
        if self._phase_repo and previous_phase:
            self._phase_repo.close_open_phase_history_for_entity(run_key, now)

        # Update run-level phase
        run.current_phase_key = target_phase_key
        run.current_phase_started_at = now
        self._repo.update(run_key, run)

        # Create new phase history entry on the run
        if self._phase_repo:
            history = PhaseHistory(
                plant_instance_key=run_key,  # reused field for run_key
                phase_key=target_phase_key,
                phase_name=target_phase_name,
                entered_at=now,
                transition_reason="manual",
            )
            self._phase_repo.create_phase_history(history)

        return {
            "run_key": run_key,
            "previous_phase": previous_phase,
            "new_phase": target_phase_key,
            "new_phase_name": target_phase_name,
            "transitioned_at": now.isoformat(),
        }

    def batch_remove(
        self,
        run_key: PlantingRunKey,
        reason: str = "batch_remove",
        target_status: str | None = None,
        *,
        tenant_key: str,
    ) -> dict:
        """Remove all active plants from the run and transition to target status.

        If *target_status* is ``None`` the status is auto-determined:
        ``COMPLETED`` when the run is already in HARVESTING, ``CANCELLED``
        otherwise.
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_remove", run.status.value)

        # Resolve final status
        if target_status is not None:
            final = PlantingRunStatus(target_status)
            if final not in (PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED):
                raise InvalidRunStateError("batch_remove", target_status)
        else:
            final = (
                PlantingRunStatus.COMPLETED
                if run.status == PlantingRunStatus.HARVESTING
                else PlantingRunStatus.CANCELLED
            )

        # A legacy edge to another tenant's plant is skipped (#2107 review SEC-001 sweep).
        plants = self._owned_run_plant_rows(run_key, tenant_key)
        removed = []
        for plant in plants:
            plant_key = plant.get("_key", "")
            try:
                existing = self._plant_repo.get_by_key(plant_key)
                if existing and existing.removed_on is None:
                    existing.removed_on = today_utc()
                    self._plant_repo.update(plant_key, existing)
                    removed.append(plant_key)
            except Exception:
                pass

        run.status = final
        run.completed_at = datetime.now(UTC)
        self._repo.update(run_key, run)
        # A run that ended reserves nothing any more (GP-FR-066).
        if self._reservation_repo is not None:
            self._reservation_repo.drop_run_reservations(run_key, remove_layout_slots=False)

        return {
            "run_key": run_key,
            "removed_count": len(removed),
            "removed_keys": removed,
            "final_status": final.value,
        }

    # ── Phase summaries ─────────────────────────────────────────────

    def get_phase_summary(self, run_key: PlantingRunKey) -> dict:
        summaries = self._repo.get_batch_phase_summaries([run_key])
        return self._build_phase_summary(summaries.get(run_key, []))

    def get_batch_phase_summaries(self, run_keys: list[str]) -> dict[str, dict]:
        raw = self._repo.get_batch_phase_summaries(run_keys)
        return {k: self._build_phase_summary(v) for k, v in raw.items()}

    @staticmethod
    def _build_phase_summary(phases: list[dict]) -> dict:
        all_phases = {p["phase"]: p["cnt"] for p in phases if p.get("phase")}
        total = sum(all_phases.values())
        dominant_phase = None
        dominant_count = 0
        for phase, cnt in all_phases.items():
            if cnt > dominant_count:
                dominant_phase = phase
                dominant_count = cnt
        return {
            "dominant_phase": dominant_phase,
            "dominant_phase_count": dominant_count,
            "total_plant_count": total,
            "all_phases": all_phases,
        }

    # ── Phase timeline ─────────────────────────────────────────────────

    def _resolve_growth_phases_for_timeline(self, species_key: str) -> tuple[list, str | None, str | None]:
        """Resolve growth phases for timeline rendering.

        Tries PhaseSequence first, falls back to LifecycleConfig.
        Returns (growth_phase_dicts, lifecycle_or_sequence_key, cycle_type_value).
        Each dict has: key, name, display_name, description, sequence_order,
        typical_duration_days, allows_harvest.
        """
        # Try PhaseSequence first
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_species(species_key)
            if seq:
                entries = self._phase_seq_repo.get_entries_for_sequence(seq.key or "")
                if entries:
                    entries.sort(key=lambda e: e.sequence_order)
                    phases = []
                    for entry in entries:
                        defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                        phases.append(
                            {
                                "key": entry.key or "",
                                "name": defn.name if defn else "",
                                "display_name": (defn.display_name if defn else "") or (defn.name if defn else ""),
                                "description": defn.description if defn else "",
                                "sequence_order": entry.sequence_order,
                                "typical_duration_days": (
                                    entry.override_duration_days or (defn.typical_duration_days if defn else 14)
                                ),
                            }
                        )
                    cycle_val = seq.cycle_type.value if hasattr(seq.cycle_type, "value") else seq.cycle_type
                    return phases, seq.key, str(cycle_val)

        # Fallback to LifecycleConfig
        if self._phase_repo:
            lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
            if lifecycle and lifecycle.key:
                growth_phases = self._phase_repo.get_phases_by_lifecycle(lifecycle.key)
                growth_phases.sort(key=lambda gp: gp.sequence_order)
                if growth_phases:
                    phases = [
                        {
                            "key": gp.key or "",
                            "name": gp.name,
                            "display_name": gp.display_name or gp.name,
                            "description": gp.description or "",
                            "sequence_order": gp.sequence_order,
                            "typical_duration_days": gp.typical_duration_days,
                        }
                        for gp in growth_phases
                    ]
                    cycle_val = (
                        lifecycle.cycle_type.value if hasattr(lifecycle.cycle_type, "value") else lifecycle.cycle_type
                    )
                    return phases, lifecycle.key, str(cycle_val)

        return [], None, None

    def get_phase_timeline(self, run_key: PlantingRunKey) -> list[dict]:
        """Build per-species phase timeline with completed/current/projected phases."""
        run = self.get_run(run_key)
        if self._phase_repo is None and self._phase_seq_repo is None:
            return []

        entries = self._repo.get_entries(run_key)
        plants_raw = self._repo.get_run_plants(run_key, include_detached=False)

        # Group plants by species_key
        species_plants: dict[str, list[dict]] = {}
        for p in plants_raw:
            sk = p.get("species_key", "")
            species_plants.setdefault(sk, []).append(p)

        # Unique species from entries; fall back to plants when no entries exist
        species_keys = list({e.species_key for e in entries})
        if not species_keys:
            species_keys = list({sk for sk in species_plants if sk})

        timelines = []
        for species_key in species_keys:
            sp_plants = species_plants.get(species_key, [])
            if not sp_plants:
                continue
            # A stored species key is not proof the run's tenant may read it (#1963): a
            # legacy entry (and the plants stamped from it) can name another tenant's
            # private species, whose phases and name must not reach this timeline.
            if not self._species_is_readable(species_key, run.tenant_key):
                continue

            # Get phases — prefer PhaseSequence, fallback to LifecycleConfig
            phase_dicts, config_key, cycle_type_val = self._resolve_growth_phases_for_timeline(species_key)
            if not phase_dicts or config_key is None:
                continue

            # Pick representative plant (first one)
            rep_plant = sp_plants[0]
            rep_key = rep_plant.get("_key", "")
            rep_current_phase = rep_plant.get("current_phase", "")

            # Load phase history for representative plant
            history = self._phase_repo.get_phase_history(rep_key) if self._phase_repo else []
            history_by_phase: dict[str, dict] = {}
            for h in history:
                history_by_phase[h.phase_name] = {
                    "entered_at": h.entered_at,
                    "exited_at": h.exited_at,
                    "actual_duration_days": h.actual_duration_days,
                }

            # Build timeline entries
            now = datetime.now(UTC)
            phase_entries = []
            last_end: datetime | None = None
            for gp in phase_dicts:
                gp_name = gp["name"]
                gp_key = gp["key"]
                typical_days = gp["typical_duration_days"]
                h = history_by_phase.get(gp_name)
                exited = h.get("exited_at") if h else None
                exited_in_past = exited is not None and (exited if exited.tzinfo else exited.replace(tzinfo=UTC)) <= now
                if h and exited_in_past:
                    # Completed phase (exited_at is in the past)
                    phase_entries.append(
                        {
                            "phase_key": gp_key,
                            "phase_name": gp_name,
                            "display_name": gp.get("display_name", gp_name),
                            "description": gp.get("description", ""),
                            "sequence_order": gp["sequence_order"],
                            "typical_duration_days": typical_days,
                            "status": "completed",
                            "actual_entered_at": h["entered_at"],
                            "actual_exited_at": h["exited_at"],
                            "actual_duration_days": h.get("actual_duration_days"),
                            "projected_start": None,
                            "projected_end": None,
                        }
                    )
                    last_end = h["exited_at"]
                elif gp_name == rep_current_phase or (h and h.get("entered_at") and not exited_in_past):
                    # Current phase
                    entered = h["entered_at"] if h else None
                    if entered is None:
                        started_str = rep_plant.get("current_phase_started_at")
                        if started_str:
                            if isinstance(started_str, str):
                                entered = datetime.fromisoformat(started_str)
                            else:
                                entered = started_str
                    proj_end_dt = (
                        exited
                        if (exited and not exited_in_past)
                        else ((entered + timedelta(days=typical_days)) if entered else None)
                    )
                    phase_entries.append(
                        {
                            "phase_key": gp_key,
                            "phase_name": gp_name,
                            "display_name": gp.get("display_name", gp_name),
                            "description": gp.get("description", ""),
                            "sequence_order": gp["sequence_order"],
                            "typical_duration_days": typical_days,
                            "status": "current",
                            "actual_entered_at": entered,
                            "actual_exited_at": exited if (exited and not exited_in_past) else None,
                            "actual_duration_days": None,
                            "projected_start": None,
                            "projected_end": proj_end_dt,
                        }
                    )
                    if proj_end_dt:
                        last_end = proj_end_dt
                    elif entered:
                        last_end = entered + timedelta(days=typical_days)
                else:
                    # Projected phase (future)
                    proj_start = last_end
                    proj_end = (proj_start + timedelta(days=typical_days)) if proj_start else None
                    phase_entries.append(
                        {
                            "phase_key": gp_key,
                            "phase_name": gp_name,
                            "display_name": gp.get("display_name", gp_name),
                            "description": gp.get("description", ""),
                            "sequence_order": gp["sequence_order"],
                            "typical_duration_days": typical_days,
                            "status": "projected",
                            "actual_entered_at": None,
                            "actual_exited_at": None,
                            "actual_duration_days": None,
                            "projected_start": proj_start,
                            "projected_end": proj_end,
                        }
                    )
                    if proj_end:
                        last_end = proj_end

            timelines.append(
                {
                    "species_key": species_key,
                    "species_name": None,
                    "lifecycle_key": config_key,
                    "cycle_type": cycle_type_val,
                    "plant_count": len(sp_plants),
                    "phases": phase_entries,
                }
            )

        return timelines

    # ── Batch phase date editing ─────────────────────────────────────

    def batch_update_phase_dates(
        self,
        run_key: PlantingRunKey,
        phase_key: str,
        entered_at: datetime | None = None,
        exited_at: datetime | None = None,
        *,
        tenant_key: str,
    ) -> dict:
        """Update phase history dates for ALL plants in the run that have a matching phase_key."""
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_update_phase_dates", run.status.value)

        if self._phase_repo is None:
            raise ValueError("Phase repository not available")

        if entered_at is not None and exited_at is not None and entered_at >= exited_at:
            raise ValueError("entered_at must be before exited_at")

        # Phase history is the plant's: a legacy edge to another tenant's plant is
        # not followed (#2107 review SEC-001 sweep).
        plants_raw = self._owned_run_plant_rows(run_key, tenant_key)
        updated_count = 0
        skipped_count = 0

        for plant_data in plants_raw:
            plant_key = plant_data.get("_key", "")
            if not plant_key:
                skipped_count += 1
                continue

            history_entries = self._phase_repo.get_phase_history(plant_key)
            matched = None
            for h in history_entries:
                if h.phase_key == phase_key:
                    matched = h
                    break

            if matched is None or matched.key is None:
                skipped_count += 1
                continue

            if entered_at is not None:
                matched.entered_at = entered_at
            if exited_at is not None:
                matched.exited_at = exited_at

            # Recalculate duration
            if matched.exited_at is not None:
                delta = matched.exited_at - matched.entered_at
                matched.actual_duration_days = delta.days
            else:
                matched.actual_duration_days = None

            self._phase_repo.update_phase_history(matched.key, matched)

            # Update plant's current_phase_started_at if this is the open phase
            if matched.exited_at is None and entered_at is not None:
                plant = self._plant_repo.get_by_key(plant_key)
                if plant:
                    plant.current_phase_started_at = entered_at
                    self._plant_repo.update(plant_key, plant)

            updated_count += 1

        return {
            "run_key": run_key,
            "phase_key": phase_key,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
        }

    # ── Plant management ──────────────────────────────────────────────

    def get_plants(self, run_key: PlantingRunKey, include_detached: bool = False) -> list[dict]:
        self.get_run(run_key)
        return self._repo.get_run_plants(run_key, include_detached)

    def detach_plant(
        self,
        run_key: PlantingRunKey,
        plant_key: PlantID,
        reason: str,
        category: str = "other",
        *,
        tenant_key: str,
    ) -> dict:
        """Detach a plant from the run, making it standalone.

        REQ-013 v2.0: Copies the run's current phase to the plant so it
        can be managed independently after detach.

        REQ-013 v2.2 W-009 (treatment snapshot scaffold): the detach
        flow records which active run-treatments would be inherited by
        the standalone plant. The actual edge-copying lands when the
        treatment-application repo gains the ``inherited_from_run`` /
        ``inherited_at`` fields.

        REQ-013 v2.3 W-010 (care-profile snapshot scaffold): the detach
        flow records the run-care-profile reference. Run-owned care
        profiles land with REQ-022; until then the snapshot field is
        only populated when the run already has a CareProfile attached
        via the standalone-plant code path.
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        # The plant is resolved BEFORE the edge update (#2107 review, W1): unknown,
        # foreign and own-but-not-attached-to-this-run answer the same 404, so the
        # status code is no existence oracle and nothing is written for any of them.
        attached = {p.get("_key") for p in self._repo.get_run_plants(run_key, include_detached=False)}
        plant = self._plant_repo.get_by_key(plant_key) if plant_key in attached else None
        if plant is None or not tenant_key or plant.tenant_key != tenant_key:
            raise NotFoundError("PlantInstance", plant_key)
        self._repo.detach_plant(run_key, plant_key, reason)

        # Copy run's current phase to the standalone plant.
        #
        # #1619 — ``plant_key`` is a second caller-supplied key and the edge
        # update above silently no-ops for a plant that is not in the run, so
        # until this guard a grower could name a FOREIGN plant, reach this
        # branch and overwrite its ``current_phase_key`` /
        # ``current_phase_started_at`` and append a ``PhaseHistory`` row to it.
        # Verifying the run was never enough: the write below is aimed at the
        # plant, so the predicate belongs on the plant.
        copied_phase = None
        if run.current_phase_key:
            plant.current_phase_key = run.current_phase_key
            plant.current_phase_started_at = run.current_phase_started_at
            self._plant_repo.update(plant_key, plant)
            copied_phase = run.current_phase_key

            # Create a standalone phase history entry for the plant
            if self._phase_repo:
                history = PhaseHistory(
                    plant_instance_key=plant_key,
                    phase_key=run.current_phase_key,
                    phase_name="",
                    entered_at=run.current_phase_started_at or datetime.now(UTC),
                    transition_reason="detach_from_run",
                )
                self._phase_repo.create_phase_history(history)

        # W-009 / W-010 snapshot scaffolding — fields populated by the
        # follow-up that wires the treatment + care-profile repos.
        treatments_inherited: list[str] = []
        care_profile_snapshot: str | None = None

        return {
            "plant_key": plant_key,
            "detached_from_run": run_key,
            "copied_phase": copied_phase,
            "standalone": True,
            "treatments_inherited": treatments_inherited,
            "care_profile_snapshot": care_profile_snapshot,
        }

    def assert_plant_not_run_owned(self, plant_key: PlantID) -> None:
        """REQ-013 v2.1 W-003 — block direct phase changes on run-owned plants.

        REQ-003 §3 1a requires a 409 Conflict when a phase change is
        attempted directly on a plant that is currently part of an
        active PlantingRun. The phase service calls this guard before
        applying any transition.

        ``RunOwnedPlantError`` is raised so the API layer can map it to
        HTTP 409 ``phase.run_owned`` per spec.
        """
        runs = self._repo.get_runs_for_plant(plant_key)
        for run in runs:
            if getattr(run, "status", None) in ("planned", "active", "harvesting"):
                from app.common.exceptions import KamerplanterError

                raise KamerplanterError(
                    message=(
                        f"Plant '{plant_key}' belongs to active run '{run.key}' — "
                        "phase transitions must go through the run."
                    ),
                    error_code="phase.run_owned",
                    status_code=409,
                )

    def get_runs_for_plant(self, plant_key: PlantID) -> list[PlantingRun]:
        return self._repo.get_runs_for_plant(plant_key)

    # ── Nutrient plan assignment ───────────────────────────────────────

    def assign_nutrient_plan(
        self,
        run_key: PlantingRunKey,
        plan_key: str,
        assigned_by: str = "",
        *,
        tenant_key: str,
    ) -> dict:
        """Bind a run to a plan the caller's tenant may read (#950).

        The run side is verified here (``_owned_run``, #2107); the *plan* side was not
        checked anywhere, so the run's ``follows_plan`` edge could be pointed at
        another tenant's plan and read back through ``GET …/nutrient-plan``.
        Read access, not ownership — global system plans stay assignable (#324).
        """
        self._owned_run(run_key, tenant_key=tenant_key)
        # Fail closed without the plan repository (security review of #1872, S2):
        # the assignment used to be stored unchecked.
        if self._nutrient_plan_repo is None:
            raise NotFoundError("NutrientPlan", plan_key)
        self._readable_plan_or_raise(plan_key, tenant_key)
        return self._repo.assign_nutrient_plan(run_key, plan_key, assigned_by)

    def _readable_plan_or_raise(self, plan_key: str, tenant_key: str):  # type: ignore[no-untyped-def]
        """Resolve a plan through the repository's tenant read predicate (#950)."""
        if self._nutrient_plan_repo is None:
            return None
        return self._nutrient_plan_repo.get_readable_or_raise(plan_key, tenant_key=tenant_key)

    def get_nutrient_plan(self, run_key: PlantingRunKey, *, tenant_key: str) -> dict | None:
        """The plan assigned to a run, resolved through the tenant predicate (#950).

        This used to load the plan with a raw ``get_by_key`` and no tenant check
        at all — the most direct of the two routes #950 describes. A stored edge
        that points at a foreign plan (possible for rows written before #950)
        now answers "no plan" rather than handing the plan over.
        """
        self.get_run(run_key, tenant_key=tenant_key)
        plan_key = self._repo.get_run_nutrient_plan_key(run_key)
        if plan_key is None:
            return None
        if self._nutrient_plan_repo is not None:
            try:
                plan = self._readable_plan_or_raise(plan_key, tenant_key)
            except NotFoundError:
                return None
            if plan:
                return plan.model_dump(mode="json") if hasattr(plan, "model_dump") else plan
        return {"key": plan_key}

    def remove_nutrient_plan(self, run_key: PlantingRunKey, *, tenant_key: str) -> bool:
        self._owned_run(run_key, tenant_key=tenant_key)
        return self._repo.remove_nutrient_plan(run_key)

    def _build_channel_calendars(
        self,
        plan_key: str,
        run_key: PlantingRunKey,
        days_ahead: int,
        *,
        tenant_key: str,
    ) -> list[dict]:
        """Build per-channel watering calendars from phase entry schedules.

        Channels with the same channel_id across different phases are merged
        so that each physical channel appears only once with combined dates.

        ``tenant_key`` is forwarded to the watering repository, whose
        ``get_last_watering_date_for_run`` is tenant-scoped since #927.
        """
        if self._nutrient_plan_repo is None:
            return []
        phase_entries = self._nutrient_plan_repo.get_phase_entries(plan_key)
        # Projected against ``get_last_watering_date_for_run()``, which derives
        # its date from a stored UTC timestamp — so this anchor is UTC too.
        today = today_utc()

        merged: dict[str, dict] = {}
        for entry in phase_entries:
            for ch in entry.delivery_channels:
                if not ch.enabled or ch.schedule is None:
                    continue
                last_date = None
                if self._watering_repo is not None:
                    last_date = self._watering_repo.get_last_watering_date_for_run(run_key, tenant_key=tenant_key)
                ch_dates = self._schedule_engine.get_next_watering_dates(
                    ch.schedule,
                    today,
                    days_ahead,
                    last_date,
                )
                method = ch.application_method
                method_str = method.value if hasattr(method, "value") else str(method)
                phase = entry.phase_name
                phase_str = phase.value if hasattr(phase, "value") else str(phase)

                if ch.channel_id in merged:
                    date_set = set(merged[ch.channel_id]["dates"])
                    date_set.update(d.isoformat() for d in ch_dates)
                    merged[ch.channel_id]["dates"] = sorted(date_set)
                else:
                    merged[ch.channel_id] = {
                        "channel_id": ch.channel_id,
                        "label": ch.label or ch.channel_id,
                        "application_method": method_str,
                        "phase_name": phase_str,
                        "dates": sorted(d.isoformat() for d in ch_dates),
                        "times_per_day": ch.schedule.times_per_day,
                    }
        return list(merged.values())

    def get_watering_schedule(self, run_key: PlantingRunKey, days_ahead: int = 14, *, tenant_key: str) -> dict:
        """Get watering schedule calendar for the next N days.

        ``tenant_key`` is required and keyword-only: it scopes both the run
        lookup and the "last watered" probe the projection is anchored on
        (#927). The repository rejects the empty sentinel, so this method cannot
        be called tenant-blind.
        """
        self.get_run(run_key, tenant_key=tenant_key)
        plan_key = self._repo.get_run_nutrient_plan_key(run_key)
        if plan_key is None:
            return {"run_key": run_key, "has_schedule": False, "dates": []}

        plan = None
        if self._nutrient_plan_repo is not None:
            plan = self._nutrient_plan_repo.get_by_key(plan_key)

        has_plan_schedule = (
            plan is not None and hasattr(plan, "watering_schedule") and plan.watering_schedule is not None
        )

        channel_calendars = self._build_channel_calendars(plan_key, run_key, days_ahead, tenant_key=tenant_key)

        if not has_plan_schedule and not channel_calendars:
            return {"run_key": run_key, "has_schedule": False, "dates": []}

        # Plan-level dates (only when no channel-specific schedules override)
        plan_dates: list[str] = []
        if has_plan_schedule and not channel_calendars:
            last_watering_date = None
            if self._watering_repo is not None:
                last_watering_date = self._watering_repo.get_last_watering_date_for_run(
                    run_key,
                    tenant_key=tenant_key,
                )
            # Same UTC anchor as ``_build_channel_calendars`` — the two schedules
            # are rendered side by side and may not disagree about "today".
            today = today_utc()
            dates = self._schedule_engine.get_next_watering_dates(
                plan.watering_schedule,
                today,
                days_ahead,
                last_watering_date,
            )
            plan_dates = [d.isoformat() for d in dates]

        schedule_dump = None
        if has_plan_schedule:
            schedule_dump = plan.watering_schedule.model_dump(mode="json")

        plan_times_per_day = 1
        if has_plan_schedule:
            plan_times_per_day = plan.watering_schedule.times_per_day

        return {
            "run_key": run_key,
            "has_schedule": True,
            "plan_key": plan_key,
            "plan_name": plan.name if plan else "",
            "schedule": schedule_dump,
            "dates": plan_dates,
            "channel_calendars": channel_calendars,
            "times_per_day": plan_times_per_day,
        }
