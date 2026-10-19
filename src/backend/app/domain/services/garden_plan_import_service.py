"""Import of a garden plan: ``POST /sites/{key}/plan/import`` (REQ-053 GP-API-005, GP-FR-141/170/172, GP-NFR-051).

The file is the JSON backup of :mod:`app.domain.models.garden_plan_export`. This service turns it back into a
plan, and — the part that makes it safe to offer — treats the file as **untrusted input**: it was edited, it came
from another installation, or somebody built it to reach what the caller must not.

**Check order (SR-013, §22.1).** (1) authentication and the lead gate — the route; (2) tenant anchor: the site of
the path, a foreign one is a 404 before the file is read; (3) the caller's role (lead only, SR-010); (4) the
document: ``schema_version``, top-level keys, Pydantic; (5) references and limits; (6) the same geometry rules
as a batch; (7) the revision check, inside the transaction. A ``dry_run`` runs (1)-(6) and writes nothing.

**Keys are never taken from the file** (GP-NFR-051). Every location, garden object and slot is inserted under a
key the database assigns; the keys of the file only wire the file's own references together (a slot names its
bed, an object its parent area) through an import-local map. A reference that leaves the file is resolved against
the target site only, or dropped and reported (``dropped_references``): a key of another tenant is simply not
resolvable here, so it can be neither claimed nor probed.

**``replace``.** Writes the state it overwrites into ``garden_plan_audit`` first, in the same transaction
(SR-011), then deletes the site's locations and garden objects and inserts the file's. A bed with an active plant
is never deleted (V-09): without ``force`` the import refuses (409 ``import.not_empty``); with ``force`` those
beds, and the locations above them, stay and the file's structure is added next to them. ``force`` lifts that
condition and nothing else. ``merge`` only adds.

**Logs carry no user text** (GP-NFR-060): site key, mode, counts, durations and error codes.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import structlog
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from app.common.enums import TenantRole
from app.common.exceptions import PlanError, PlanValidationError
from app.common.types import SiteKey
from app.domain.calculators.geometry_calculator import area_m2, validate_geometry
from app.domain.engines.frost_exposure_resolver import frost_exposed_from_risk
from app.domain.engines.garden_plan_engine import (
    ERROR_SLOT_OUTSIDE_BED,
    ERROR_SLOT_OVERLAP,
    overlapping_zones,
    slots_outside_bed,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    MAX_PLAN_OBJECTS_PER_SITE,
    MAX_SLOTS_PER_BATCH,
    MAX_SLOTS_PER_SITE,
    PlanBatchWrite,
)
from app.domain.models.garden_plan_export import (
    ExportGardenObject,
    ExportLocation,
    ExportSlot,
    GardenPlanExport,
)
from app.domain.models.garden_plan_import import (
    ALWAYS_DROPPED_FIELDS,
    IMPORT_TIME_BUDGET_SECONDS,
    MAX_IMPORT_NESTING,
    MAX_REPORTED,
    SUPPORTED_SCHEMA_VERSIONS,
    DroppedReference,
    ImportCounts,
    ImportFinding,
    ImportMode,
    PlanImportReport,
)
from app.domain.models.site import Location, SitePlan, Slot
from app.domain.services.adjacency_service import AdjacencyDispatch, request_adjacency_recompute
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.location_ownership import require_owned_site
from app.domain.services.site_service import place_in_tree

logger = structlog.get_logger()

ERROR_NOT_EMPTY = "import.not_empty"
ERROR_DUPLICATE_KEY = "import.duplicate_key"
ERROR_PARENT_CYCLE = "import.parent_cycle"
ERROR_TOO_DEEP = "import.too_deep"
ERROR_DUPLICATE_SLOT_ID = "import.duplicate_slot_id"
ERROR_QUOTA = "plan.quota_exceeded"
_GEOMETRY_FIELDS = frozenset({"geometry", "boundary", "origin", "points", "width_m", "length_m", "radius_m"})
#: How much of a file's own key an error may echo back.
_KEY_ECHO = 64
_TEMP_PREFIX = "imp_"

_LOCATION = "location"
_OBJECT = "garden_object"
_SLOT = "slot"


@dataclass
class _Prepared:
    """Everything the import decided before a byte is written."""

    findings: list[ImportFinding] = field(default_factory=list)
    dropped: list[DroppedReference] = field(default_factory=list)
    locations: dict[str, Location] = field(default_factory=dict)
    objects: dict[str, GardenObject] = field(default_factory=dict)
    #: temp key → the file's key, to report an error against the file.
    file_key: dict[str, str] = field(default_factory=dict)
    imported_locations: list[str] = field(default_factory=list)
    imported_objects: list[str] = field(default_factory=list)
    slots: list[tuple[str, Slot]] = field(default_factory=list)
    delete_locations: list[str] = field(default_factory=list)
    delete_objects: list[str] = field(default_factory=list)
    deleted_slot_count: int = 0
    deleted_names: dict[str, str] = field(default_factory=dict)
    kept: int = 0
    boundary: Any = None
    boundary_changed: bool = False
    settings_written: bool = False
    snapshot_wanted: bool = False

    def add_finding(self, finding: ImportFinding) -> None:
        self.findings.append(finding)

    def add_findings(self, findings: Iterable[ImportFinding]) -> None:
        self.findings.extend(findings)

    def drop(self, reference: DroppedReference) -> None:
        self.dropped.append(reference)

    def add_slot(self, location: str, slot: Slot) -> None:
        self.slots.append((location, slot))


def _copied[TModel: BaseModel](model: TModel) -> TModel:
    return model.model_copy(deep=True)


def _dumped(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _is_temp(key: str) -> bool:
    return key.startswith(_TEMP_PREFIX)


def _value(mapping: dict[str, Any], name: str) -> Any:
    return mapping.get(name)


def _errors_of(error: PydanticValidationError) -> list[ErrorDetails]:
    return error.errors()


def _echo(key: object) -> str | None:
    return key[:_KEY_ECHO] if isinstance(key, str) else None


def _path(loc: tuple[int | str, ...]) -> str:
    out = ""
    for part in loc:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out or "document"


class GardenPlanImportService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        plan_service: GardenPlanService,
        export_service: GardenPlanExportService,
        *,
        dispatch_adjacency: AdjacencyDispatch | None = None,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._plans = plan_service
        self._export = export_service
        self._dispatch_adjacency = dispatch_adjacency

    # ── the entry ─────────────────────────────────────────────────────────────

    def import_plan(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        mode: ImportMode,
        dry_run: bool,
        force: bool,
        confirm_site_name: str | None,
        document: dict[str, Any],
    ) -> PlanImportReport:
        """Check the file and, unless ``dry_run``, write it. See the module docstring for the order."""
        started = perf_counter()
        site = require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)  # (2) tenant anchor
        if not MembershipEngine.can_delete_resource(role):  # (3) lead only: a replace deletes (SR-010)
            raise PlanError(
                "import.forbidden", "Only a lead may import a garden plan.", status_code=403, field="request"
            )
        parsed = self._read_document(document)  # (4)
        if mode == "replace" and not dry_run and (confirm_site_name or "").strip() != site.name.strip():
            raise PlanError(
                "import.site_name_mismatch",
                "Type the name of the site to confirm that its plan is replaced.",
                status_code=422,
                field="confirm_site_name",
            )

        revision = site.plan.plan_revision if site.plan is not None else 0
        prepared = self._prepare(
            site_key,
            site_plan=site.plan,
            parsed=parsed,
            raw=document,
            tenant_key=tenant_key,
            user_key=user_key,
            mode=mode,
            force=force,
        )
        report = self._report(prepared, mode=mode, dry_run=dry_run)
        if dry_run:
            logger.info("garden_plan.import_checked", site_key=site_key, mode=mode, errors=report.errors_total)
            return report
        if any(finding.code == ERROR_NOT_EMPTY for finding in prepared.findings):
            raise PlanError(
                ERROR_NOT_EMPTY,
                "Beds with active plants stand in this plan; remove the plants or import with force.",
                status_code=409,
                field="mode",
            )
        if prepared.findings:
            logger.warning(
                "garden_plan.import_refused",
                site_key=site_key,
                mode=mode,
                codes=sorted({finding.code for finding in prepared.findings}),
            )
            raise PlanValidationError(
                [
                    (None, finding.field, finding.code, {"key": finding.key} if finding.key else {})
                    for finding in prepared.findings[:MAX_REPORTED]
                ]
            )

        write = self._build_write(
            site_key,
            tenant_key=tenant_key,
            user_key=user_key,
            revision=revision,
            mode=mode,
            prepared=prepared,
            parsed=parsed,
            started=started,
        )
        outcome = self._plan.apply_plan_batch(write)
        for temp_key in {temp for temp, _ in write.slot_inserts}:
            request_adjacency_recompute(self._dispatch_adjacency, outcome.key_map.get(temp_key, ""))
        logger.info(
            "garden_plan.import_applied",
            site_key=site_key,
            mode=mode,
            revision=outcome.plan_revision,
            locations=len(write.location_inserts),
            garden_objects=len(write.object_inserts),
            slots=len(write.slot_inserts),
            deleted=len(write.location_deletes) + len(write.object_deletes),
            duration_ms=round((perf_counter() - started) * 1000),
        )
        report.applied = True
        report.plan_revision = outcome.plan_revision
        report.snapshot_written = write.snapshot is not None
        return report

    # ── (4) the document ──────────────────────────────────────────────────────

    @staticmethod
    def _read_document(document: dict[str, Any]) -> GardenPlanExport:
        """``schema_version``, the top-level keys and the shape — refused as a whole, before any lookup."""
        version = document.get("schema_version")
        if version is None:
            raise PlanError(
                "import.schema_version_missing",
                "The file has no schema_version; it is not a garden-plan backup.",
                status_code=422,
                field="schema_version",
            )
        if version not in SUPPORTED_SCHEMA_VERSIONS:
            raise PlanError(
                "import.schema_version_unsupported",
                "This file has a schema version this installation cannot read.",
                status_code=422,
                field="schema_version",
                supported=list(SUPPORTED_SCHEMA_VERSIONS),
                got=str(version)[:16],
            )
        unknown = sorted(set(document) - set(GardenPlanExport.model_fields))
        if unknown:
            # A newer file within schema_version "1" may carry parts this version cannot place (zones, template
            # references, WP 7.x). Silently skipping them would restore a plan that quietly lacks half of itself.
            raise PlanError(
                "import.unknown_keys",
                "The file holds parts this version does not know; update Kamerplanter or export again.",
                status_code=422,
                field="document",
                keys=[name[:_KEY_ECHO] for name in unknown[:10]],
            )
        try:
            return GardenPlanExport.model_validate(document)
        except PydanticValidationError as exc:
            findings = [_finding_of(error, document) for error in _errors_of(exc)]
            raise PlanValidationError(
                [
                    (None, finding.field, finding.code, {"key": finding.key} if finding.key else {})
                    for finding in findings[:MAX_REPORTED]
                ]
            ) from None

    # ── (5), (6) references, limits, geometry ─────────────────────────────────

    def _prepare(
        self,
        site_key: str,
        *,
        site_plan: SitePlan | None,
        parsed: GardenPlanExport,
        raw: dict[str, Any],
        tenant_key: str,
        user_key: str,
        mode: ImportMode,
        force: bool,
    ) -> _Prepared:
        prepared = _Prepared()
        existing_locations, existing_objects = self._plan.load_structure(site_key, tenant_key=tenant_key)
        stored = {loc.key: loc for loc in existing_locations if loc.key}
        self._plan_the_existing(
            prepared, stored, existing_objects, site_key, tenant_key=tenant_key, mode=mode, force=force
        )
        index_of = self._index_locations(prepared, parsed.locations)
        flags = self._plan.bed_type_flags(sorted({loc.location_type_key for loc in parsed.locations}))
        zone_cache: dict[str, str | None] = {}
        substrate_cache: dict[str, bool] = {}

        for position in self._parents_first(prepared, parsed.locations, index_of):
            self._add_location(
                prepared,
                parsed.locations[position],
                position,
                site_key=site_key,
                tenant_key=tenant_key,
                index_of=index_of,
                flags=flags,
                zone_cache=zone_cache,
                substrate_cache=substrate_cache,
            )
        for position, item in enumerate(parsed.garden_objects):
            self._add_object(prepared, item, position, site_key=site_key, user_key=user_key, index_of=index_of)
        self._add_slots(prepared, parsed.slots)
        self._mark_always_dropped(prepared, raw)
        self._check_quotas(prepared, site_key, tenant_key=tenant_key, mode=mode)
        self._check_settings(prepared, site_plan, parsed, mode)
        self._check_geometry(prepared, site_key, tenant_key=tenant_key)
        return prepared

    def _plan_the_existing(
        self,
        prepared: _Prepared,
        stored: dict[str, Location],
        existing_objects: list[GardenObject],
        site_key: str,
        *,
        tenant_key: str,
        mode: ImportMode,
        force: bool,
    ) -> None:
        """What stays and what goes of the plan that is there now."""
        if mode == "merge":
            prepared.locations = {key: _copied(loc) for key, loc in stored.items()}
            prepared.objects = {obj.key: _copied(obj) for obj in existing_objects if obj.key}
            return
        planted = self._plan.locations_with_active_plants(sorted(stored), tenant_key=tenant_key)
        if planted and not force:
            prepared.add_finding(ImportFinding(field="mode", code=ERROR_NOT_EMPTY))
        keep: set[str] = set()
        for key in planted:  # V-09: a bed with a plant stays, and so does everything above it
            current: str | None = key
            while current and current in stored and current not in keep:
                keep.add(current)
                current = stored[current].parent_location_key
        prepared.kept = len(keep)
        prepared.locations = {key: _copied(stored[key]) for key in keep}
        prepared.delete_locations = sorted(set(stored) - keep)
        prepared.deleted_names = {key: stored[key].name for key in prepared.delete_locations}
        prepared.delete_objects = sorted(obj.key for obj in existing_objects if obj.key)
        if prepared.delete_locations:
            prepared.deleted_slot_count = len(
                self._plan.load_active_slots(site_key, prepared.delete_locations, tenant_key=tenant_key)
            )
        prepared.snapshot_wanted = True

    @staticmethod
    def _index_locations(prepared: _Prepared, locations: list[ExportLocation]) -> dict[str, int]:
        index_of: dict[str, int] = {}
        for position, item in enumerate(locations):
            if item.key in index_of:
                prepared.add_finding(
                    ImportFinding(field=f"locations[{position}].key", code=ERROR_DUPLICATE_KEY, key=_echo(item.key))
                )
                continue
            index_of[item.key] = position
        return index_of

    @staticmethod
    def _parents_first(prepared: _Prepared, locations: list[ExportLocation], index_of: dict[str, int]) -> list[int]:
        """File positions ordered so a location follows its parent; a parent cycle is reported and cut."""
        order: list[int] = []
        state: dict[int, int] = {}  # 1 on the way down, 2 done
        for start in range(len(locations)):
            if state.get(start) == 2 or index_of.get(locations[start].key) != start:
                continue
            chain: list[int] = []
            current: int | None = start
            while current is not None and state.get(current) is None:
                state[current] = 1
                chain.append(current)
                parent = locations[current].parent_location_key
                current = index_of.get(parent) if parent is not None else None
            if current is not None and state.get(current) == 1:
                prepared.add_finding(
                    ImportFinding(
                        field=f"locations[{current}].parent_location_key",
                        code=ERROR_PARENT_CYCLE,
                        key=_echo(locations[current].key),
                    )
                )
            for position in reversed(chain):
                state[position] = 2
                order.append(position)
        return order

    def _add_location(
        self,
        prepared: _Prepared,
        item: ExportLocation,
        position: int,
        *,
        site_key: str,
        tenant_key: str,
        index_of: dict[str, int],
        flags: dict[str, bool],
        zone_cache: dict[str, str | None],
        substrate_cache: dict[str, bool],
    ) -> None:
        temp = f"imp_loc_{position}"
        parent_key = self._resolve_parent(prepared, item, index_of)
        parent = prepared.locations.get(parent_key) if parent_key else None

        type_key = item.location_type_key
        if type_key and type_key not in flags:
            prepared.drop(
                DroppedReference(entity=_LOCATION, key=item.key, field="location_type_key", reason="not_found")
            )
            type_key = ""
        zone_key = item.irrigation_zone_key
        if zone_key:
            if zone_key not in zone_cache:
                zone_cache[zone_key] = self._plan.irrigation_zone_site_key(zone_key, tenant_key=tenant_key)
            zone_site = zone_cache[zone_key]
            if zone_site != site_key:
                reason = "not_found" if zone_site is None else "not_in_site"
                prepared.drop(
                    DroppedReference(entity=_LOCATION, key=item.key, field="irrigation_zone_key", reason=reason)
                )
                zone_key = None
        soil = _copied(item.soil_profile) if item.soil_profile is not None else None
        site_conditions = _copied(item.site_conditions) if item.site_conditions is not None else None
        if soil is not None and soil.substrate_key:
            if soil.substrate_key not in substrate_cache:
                substrate_cache[soil.substrate_key] = self._plan.substrate_visible(
                    soil.substrate_key, tenant_key=tenant_key
                )
            if not substrate_cache[soil.substrate_key]:
                prepared.drop(
                    DroppedReference(
                        entity=_LOCATION, key=item.key, field="soil_profile.substrate_key", reason="not_found"
                    )
                )
                soil.substrate_key = None

        fields: dict[str, Any] = {
            "name": item.name,
            "site_key": site_key,
            "parent_location_key": parent_key,
            "location_type_key": type_key,
            "description": item.description,
            "notes": item.notes,
            "geometry": item.geometry,
            "area_m2": item.area_m2 if item.geometry is None else 0.0,
            "height_m": item.height_m,
            "bed_status": item.bed_status,
            "sun_exposure": item.sun_exposure,
            "soil_profile": soil,
            "site_conditions": site_conditions,
            # The file carries no ``frost_exposed``; the winter readers still read it (WP 3.9), so it follows the risk.
            "frost_exposed": frost_exposed_from_risk(site_conditions.microclimate.frost_risk)
            if site_conditions is not None
            else None,
            "irrigation_zone_key": zone_key,
            "locked": item.locked,
            "z_order": item.z_order,
        }
        if item.pitch_m is not None:
            fields["pitch_m"] = item.pitch_m
        try:
            location = Location(**fields)
        except PydanticValidationError as exc:
            prepared.add_findings(
                ImportFinding(field=f"locations[{position}].{_path(e['loc'])}", code=_code_of(e), key=_echo(item.key))
                for e in _errors_of(exc)
            )
            return
        place_in_tree(location, parent)
        if location.depth >= MAX_IMPORT_NESTING:
            prepared.add_finding(
                ImportFinding(
                    field=f"locations[{position}].parent_location_key", code=ERROR_TOO_DEEP, key=_echo(item.key)
                )
            )
        prepared.locations[temp] = location
        prepared.imported_locations.append(temp)
        prepared.file_key[temp] = item.key

    @staticmethod
    def _resolve_parent(
        prepared: _Prepared, item: ExportLocation | ExportGardenObject, index_of: dict[str, int]
    ) -> str | None:
        """The key a parent reference of the file becomes in the working set.

        A parent in the file is that location's temporary key. One that is not is looked up among the locations
        that **stay** in the target site (``merge``: all of them; ``replace``: the planted beds and their
        ancestors) - a key of another site or tenant is not among them and is dropped, reported, set to ``null``.
        """
        parent = item.parent_location_key
        if parent is None:
            return None
        position = index_of.get(parent)
        if position is not None:
            # A parent that could not be built has a finding already; here it is simply absent.
            temp = f"imp_loc_{position}"
            return temp if temp in prepared.locations else None
        if parent in prepared.locations and not _is_temp(parent):
            return parent
        entity = _LOCATION if isinstance(item, ExportLocation) else _OBJECT
        prepared.drop(DroppedReference(entity=entity, key=item.key, field="parent_location_key", reason="not_found"))
        return None

    def _add_object(
        self,
        prepared: _Prepared,
        item: ExportGardenObject,
        position: int,
        *,
        site_key: str,
        user_key: str,
        index_of: dict[str, int],
    ) -> None:
        temp = f"imp_obj_{position}"
        parent_key = self._resolve_parent(prepared, item, index_of)
        try:
            garden_object = GardenObject(
                site_key=site_key,
                parent_location_key=parent_key,
                object_type=item.object_type,
                label=item.label,
                geometry=item.geometry,
                props=item.props.model_dump(mode="python"),
                off_site=item.off_site,
                locked=item.locked,
                z_order=item.z_order,
                notes=item.notes,
                created_by=user_key,
            )
        except PydanticValidationError as exc:
            prepared.add_findings(
                ImportFinding(
                    field=f"garden_objects[{position}].{_path(e['loc'])}", code=_code_of(e), key=_echo(item.key)
                )
                for e in _errors_of(exc)
            )
            return
        prepared.objects[temp] = garden_object
        prepared.imported_objects.append(temp)
        prepared.file_key[temp] = item.key

    def _add_slots(self, prepared: _Prepared, slots: list[ExportSlot]) -> None:
        by_file_key = {prepared.file_key[temp]: temp for temp in prepared.imported_locations}
        seen: set[tuple[str, str]] = set()
        for position, item in enumerate(slots):
            bed = by_file_key.get(item.location_key)
            if bed is None:
                prepared.drop(DroppedReference(entity=_SLOT, key=item.key, field="location_key", reason="not_found"))
                continue
            if (bed, item.slot_id) in seen:
                prepared.add_finding(
                    ImportFinding(field=f"slots[{position}].slot_id", code=ERROR_DUPLICATE_SLOT_ID, key=_echo(item.key))
                )
                continue
            seen.add((bed, item.slot_id))
            try:
                slot = Slot(
                    slot_id=item.slot_id,
                    location_key=bed,
                    slot_role=item.slot_role,
                    capacity_plants=item.capacity_plants,
                    geometry=item.geometry,
                    row_index=item.row_index,
                    sequence=item.sequence,
                    geometry_source=item.geometry_source,
                    container_volume_l=item.container_volume_l,
                    planned_spacing_cm=item.planned_spacing_cm,
                )
            except PydanticValidationError as exc:
                prepared.add_findings(
                    ImportFinding(field=f"slots[{position}].{_path(e['loc'])}", code=_code_of(e), key=_echo(item.key))
                    for e in _errors_of(exc)
                )
                continue
            prepared.add_slot(bed, slot)
            prepared.file_key[f"imp_slot_{len(prepared.slots) - 1}"] = item.key

    @staticmethod
    def _mark_always_dropped(prepared: _Prepared, raw: dict[str, Any]) -> None:
        """GP-FR-141: a coupling to a Home Assistant entity or an actuator is never carried over; say so."""
        for list_name, entity in (("locations", _LOCATION), ("garden_objects", _OBJECT)):
            items = raw.get(list_name)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                for name in ALWAYS_DROPPED_FIELDS:
                    if _value(item, name) is not None:
                        key = _echo(_value(item, "key")) or ""
                        prepared.drop(DroppedReference(entity=entity, key=key, field=name, reason="always_dropped"))

    def _check_quotas(self, prepared: _Prepared, site_key: str, *, tenant_key: str, mode: ImportMode) -> None:
        """GP-NFR-017: ≤ 500 locations and garden objects per site, ≤ 8 000 slots, ≤ 2 000 per bed."""
        total = len(prepared.locations) + len(prepared.objects)
        if total > MAX_PLAN_OBJECTS_PER_SITE:
            prepared.add_finding(ImportFinding(field="locations", code=ERROR_QUOTA))
        per_bed: dict[str, int] = {}
        for bed, _ in prepared.slots:
            per_bed[bed] = per_bed.get(bed, 0) + 1
        for bed, count in per_bed.items():
            if count > MAX_SLOTS_PER_BATCH:
                prepared.add_finding(
                    ImportFinding(field="slots", code=ERROR_QUOTA, key=_echo(prepared.file_key.get(bed)))
                )
        if mode == "merge":
            standing = self._plan.count_active_slots(site_key, tenant_key=tenant_key)
        else:
            kept = [key for key in prepared.locations if not _is_temp(key)]
            standing = len(self._plan.load_active_slots(site_key, kept, tenant_key=tenant_key)) if kept else 0
        if standing + len(prepared.slots) > MAX_SLOTS_PER_SITE:
            prepared.add_finding(ImportFinding(field="slots", code=ERROR_QUOTA))

    @staticmethod
    def _check_settings(
        prepared: _Prepared, site_plan: SitePlan | None, parsed: GardenPlanExport, mode: ImportMode
    ) -> None:
        """The plan settings of the file replace the site's (``replace``) or fill a site that has none (``merge``)."""
        current = site_plan.boundary if site_plan is not None else None
        prepared.boundary = current
        document = parsed.plan
        if document is None:
            return
        takes = mode == "replace" or site_plan is None
        if not takes:
            return
        try:
            candidate = SitePlan(
                boundary=document.boundary,
                north_angle_deg=document.north_angle_deg,
                default_grid_m=document.default_grid_m,
                adjacency_factor=document.adjacency_factor,
            )
        except PydanticValidationError as exc:
            prepared.add_findings(
                ImportFinding(field=f"plan.{_path(e['loc'])}", code=_code_of(e)) for e in _errors_of(exc)
            )
            return
        if candidate.boundary is not None:
            for code in validate_geometry(candidate.boundary):
                prepared.add_finding(ImportFinding(field="plan.boundary", code=code))
            prepared.boundary = candidate.boundary
            prepared.boundary_changed = True
        prepared.settings_written = True

    def _check_geometry(self, prepared: _Prepared, site_key: str, *, tenant_key: str) -> None:
        """V-01…V-06, V-19 on the plan the import would leave, by the engine a batch uses."""
        findings = self._plans.check_imported_structure(
            site_key,
            tenant_key=tenant_key,
            locations=prepared.locations,
            objects=prepared.objects,
            imported_locations=prepared.imported_locations,
            imported_objects=prepared.imported_objects,
            boundary=prepared.boundary,
            boundary_changed=prepared.boundary_changed,
        )
        for index, name, code, extra in findings:
            if index is None:
                prepared.add_finding(ImportFinding(field="plan.boundary", code=code))
                continue
            if index < len(prepared.imported_locations):
                temp = prepared.imported_locations[index]
                path = f"locations[{temp.removeprefix('imp_loc_')}].{name}"
            else:
                temp = prepared.imported_objects[index - len(prepared.imported_locations)]
                path = f"garden_objects[{temp.removeprefix('imp_obj_')}].{name}"
            other = _value(extra, "key")
            prepared.add_finding(ImportFinding(field=path, code=code, key=_echo(prepared.file_key.get(temp) or other)))
        self._check_slot_geometry(prepared)

    @staticmethod
    def _check_slot_geometry(prepared: _Prepared) -> None:
        """V-04 and V-06 for the imported slots: inside their bed, zones not overlapping."""
        by_bed: dict[str, list[tuple[str, Any]]] = {}
        for number, (bed, slot) in enumerate(prepared.slots):
            if slot.geometry is not None:
                by_bed.setdefault(bed, []).append((f"imp_slot_{number}", slot.geometry))
        for bed, placed in by_bed.items():
            bed_geometry = prepared.locations[bed].geometry
            if bed_geometry is not None:
                for temp in slots_outside_bed(bed_geometry, placed):
                    prepared.add_finding(
                        ImportFinding(
                            field="slots", code=ERROR_SLOT_OUTSIDE_BED, key=_echo(prepared.file_key.get(temp))
                        )
                    )
            for first, _second in overlapping_zones(placed):
                prepared.add_finding(
                    ImportFinding(field="slots", code=ERROR_SLOT_OVERLAP, key=_echo(prepared.file_key.get(first)))
                )

    # ── the answer and the write ──────────────────────────────────────────────

    @staticmethod
    def _report(prepared: _Prepared, *, mode: str, dry_run: bool) -> PlanImportReport:
        return PlanImportReport(
            mode=mode,
            dry_run=dry_run,
            would_create=ImportCounts(
                locations=len(prepared.imported_locations),
                garden_objects=len(prepared.imported_objects),
                slots=len(prepared.slots),
            ),
            would_update=ImportCounts(plan_settings=1 if prepared.settings_written else 0),
            would_delete=ImportCounts(
                locations=len(prepared.delete_locations),
                garden_objects=len(prepared.delete_objects),
                slots=prepared.deleted_slot_count,
            ),
            kept_locations=prepared.kept,
            dropped_references=prepared.dropped[:MAX_REPORTED],
            dropped_references_total=len(prepared.dropped),
            errors=prepared.findings[:MAX_REPORTED],
            errors_total=len(prepared.findings),
        )

    def _build_write(
        self,
        site_key: str,
        *,
        tenant_key: str,
        user_key: str,
        revision: int,
        mode: ImportMode,
        prepared: _Prepared,
        parsed: GardenPlanExport,
        started: float,
    ) -> PlanBatchWrite:
        inserts = sorted(
            prepared.imported_locations,
            key=lambda temp: (prepared.locations[temp].depth, prepared.imported_locations.index(temp)),
        )
        audit: list[dict[str, str]] = []
        for key in prepared.delete_locations:
            audit.append(
                {"op": "import_delete", "entity": _LOCATION, "key": key, "summary": prepared.deleted_names[key][:200]}
            )
        for key in prepared.delete_objects:
            audit.append({"op": "import_delete", "entity": _OBJECT, "key": key, "summary": ""})
        summary = (
            f"{len(prepared.imported_locations)} locations, {len(prepared.imported_objects)} objects, "
            f"{len(prepared.slots)} slots"
        )
        audit.append({"op": f"import_{mode}", "entity": "site", "key": site_key, "summary": summary})
        snapshot: dict[str, Any] | None = None
        if prepared.snapshot_wanted:
            backup = self._export.export_json(site_key, tenant_key=tenant_key)
            snapshot = _dumped(backup)
        plan = parsed.plan if prepared.settings_written else None
        return PlanBatchWrite(
            site_key=site_key,
            tenant_key=tenant_key,
            editor_key=user_key,
            expected_revision=revision,
            basis_revision=revision,
            location_inserts=[(temp, prepared.locations[temp]) for temp in inserts],
            location_deletes=prepared.delete_locations,
            object_inserts=[(temp, prepared.objects[temp]) for temp in prepared.imported_objects],
            object_deletes=prepared.delete_objects,
            boundary=prepared.boundary if prepared.boundary_changed else None,
            north_angle_deg=plan.north_angle_deg if plan is not None else None,
            default_grid_m=plan.default_grid_m if plan is not None else None,
            adjacency_factor=plan.adjacency_factor if plan is not None else None,
            total_area_m2=area_m2(prepared.boundary) if prepared.boundary_changed else None,
            audit=audit,
            slot_inserts=prepared.slots,
            snapshot=snapshot,
            snapshot_summary=f"state before the replace import (revision {revision})",
            time_budget_seconds=max(IMPORT_TIME_BUDGET_SECONDS - (perf_counter() - started), 1.0),
        )


def _code_of(error: Any) -> str:
    parts = {str(part) for part in error["loc"]}
    return "geometry.invalid" if parts & _GEOMETRY_FIELDS else "validation.invalid"


def _finding_of(error: Any, document: dict[str, Any]) -> ImportFinding:
    loc = tuple(error["loc"])
    key: str | None = None
    if len(loc) >= 2 and isinstance(loc[1], int) and isinstance(loc[0], str):
        items = document.get(loc[0])
        if isinstance(items, list) and loc[1] < len(items) and isinstance(items[loc[1]], dict):
            key = _echo(items[loc[1]].get("key"))
    return ImportFinding(field=_path(loc), code=_code_of(error), key=key)


__all__ = ["ERROR_NOT_EMPTY", "GardenPlanImportService"]
