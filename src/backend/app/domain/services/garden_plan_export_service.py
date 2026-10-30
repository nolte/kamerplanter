"""Export of a garden plan: JSON backup, SVG and PDF (REQ-053 §23, GP-API-004/006/007, GP-NFR-052).

Every public method resolves the site **inside the method** through the tenant anchor
(``location_ownership.require_owned_site``, §22.3 T-04) and takes ``*, tenant_key: str`` without a default, so
a site of another tenant answers exactly like an absent one (404) before any document of it is read. The
read model itself comes from :class:`GardenPlanService`, which anchors again; the double walk costs one
document and keeps this class correct if it is ever handed a different collaborator.

**What a PDF carries (SR-024).** The plan, its scale bar, north arrow and legend, a title block (garden name,
date, revision, scale, paper) and, on request, a bed list (name, area, status, sun exposure). Never member
names, assignments, notes, GPS coordinates, ``*_by`` fields or photos. The SVG is embedded as a ``data:``
image, so the template needs neither ``|safe`` nor any URL, and the print engine's fetcher
(``RestrictedURLFetcher``: ``data:`` and the template tree only) sees nothing it could be talked into
fetching (GP-NFR-052 (a), (f)).

**The underlay (GP-FR-033, WP 7.14)** is the one image from an attachment: only when the caller asks for it
(``underlay=True`` on the PDF route; the JSON export and the SVG never carry it), read from the tenant's *own*
``garden_plan_underlay`` attachment, re-encoded and shrunk, and laid under the plan figure as a ``data:`` URI.
The fetcher still sees nothing but ``data:``.

**Plant states and phase colours (GP-UX-005/059/060, #2489).** Below
:data:`~app.domain.engines.plan_svg_engine.PLANT_COUNTER_THRESHOLD` plants the SVG and the PDF draw each plant with
its phase colour, lifecycle ring and most urgent badge. The states come from the plant-state repository, bed by bed
of the already owned site and in bounded pages, and are assembled by
:func:`~app.domain.calculators.plant_state_inputs.visual_state_of` — the same function behind
``GET /locations/{key}/plant-states``, so paper and screen agree. Phase names are read once per distinct phase key
from the growth-phase repository; a key that is no growth phase (a phase-sequence entry) takes the name the
plant-state read joined in — the bed view's rule, so a plant has the same colour on screen and on paper. From the
threshold on nothing is read: each bed prints its counter (GP-NFR-038).
"""

from __future__ import annotations

import asyncio
import base64
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import structlog
from pydantic import BaseModel

from app.common.enums import AttachmentCategory
from app.common.exceptions import NotFoundError, PlanError
from app.common.types import SiteKey
from app.domain.calculators.plant_state_calculator import PlantVisualState
from app.domain.calculators.plant_state_inputs import visual_state_of
from app.domain.engines.plan_svg_engine import (
    PDF_HEADER_MM,
    PLANT_COUNTER_THRESHOLD,
    PlanPaper,
    PlanSvg,
    PlanSvgLayer,
    PlanSvgOptions,
    PlantStateMarks,
    page_size_mm,
    render_plan_svg,
)
from app.domain.engines.plan_underlay_engine import (
    UnderlayImage,
    UnderlayImageError,
    UnderlayPlacement,
    place_underlay,
    prepare_image,
)
from app.domain.engines.print_engine import PrintEngine
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, PlantStateSource
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import GardenPlanView
from app.domain.models.garden_plan_export import (
    MAX_EXPORT_KEYS,
    OBJECT_KEY_PREFIX,
    ExportGardenObject,
    ExportLocation,
    ExportPlanSettings,
    ExportScope,
    ExportSite,
    ExportSlot,
    ExportZone,
    GardenPlanExport,
)
from app.domain.models.site import Location, Site
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.location_ownership import require_owned_site
from app.domain.services.plant_state_inputs import frost_risk_of

logger = structlog.get_logger(__name__)

_TEMPLATE = "garden_plan.html"
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9_-]")
#: Plants per plant-state read; a bed needs at most ``PLANT_COUNTER_THRESHOLD / page`` reads (+1 to see the end).
STATE_PAGE_SIZE = 200
_MAX_STATE_PAGES = PLANT_COUNTER_THRESHOLD // STATE_PAGE_SIZE + 1


def _export_error(code: str, message: str) -> PlanError:
    return PlanError(code, message, status_code=422, field="keys")


def _validated[TModel: BaseModel](model: type[TModel], source: object) -> TModel:
    return model.model_validate(source)


def _cut_parent(item: ExportLocation | ExportGardenObject, kept: set[str]) -> None:
    """A parent that is not in the file is no reference of the file: ``null`` (the item becomes a root)."""
    if item.parent_location_key not in kept:
        item.parent_location_key = None


def _zone_of_file(row: dict[str, Any], object_keys: set[str]) -> ExportZone:
    """A zone of a partial file; its water source stays only when that garden object is in the file as well."""
    zone = ExportZone(**row)
    if zone.water_source_key not in object_keys:
        zone.water_source_key = None
    return zone


def _is_object_key(key: str) -> bool:
    return key.startswith(OBJECT_KEY_PREFIX)


def _object_name(key: str) -> str:
    return key.removeprefix(OBJECT_KEY_PREFIX)


def _chosen(
    scope: ExportScope, keys: Sequence[str], locations: Sequence[Location], garden_objects: Sequence[GardenObject]
) -> tuple[set[str], set[str]]:
    """The location keys and garden-object keys a partial export holds; 404 for a key the site does not hold."""
    if not keys:
        raise _export_error("export.keys_required", "keys names the beds or objects to export.")
    if len(keys) > MAX_EXPORT_KEYS:
        raise _export_error("export.too_many_keys", f"keys names at most {MAX_EXPORT_KEYS} entries.")
    held_locations = {loc.key for loc in locations if loc.key}
    held_objects = {obj.key for obj in garden_objects if obj.key}
    wanted_objects = {_object_name(key) for key in keys if _is_object_key(key)}
    wanted_locations = {key for key in keys if not _is_object_key(key)}
    if wanted_objects and scope == "subtree":
        raise _export_error("export.object_key_in_subtree", "A subtree is named by locations.")
    for missing in sorted(wanted_locations - held_locations)[:1]:
        raise NotFoundError("Location", missing)
    for missing in sorted(wanted_objects - held_objects)[:1]:
        raise NotFoundError("GardenObject", missing)
    if scope == "selection":
        return wanted_locations, wanted_objects
    below = set(wanted_locations)
    grew = True
    while grew:
        more = {loc.key for loc in locations if loc.key and loc.parent_location_key in below} - below
        grew = bool(more)
        below |= more
    return below, {obj.key for obj in garden_objects if obj.key and obj.parent_location_key in below}


@dataclass(frozen=True)
class PlanPdf:
    content: bytes
    scale: int
    paper: PlanPaper
    suggest_a3: bool
    filename: str


def safe_filename_part(key: str) -> str:
    """A key as a file-name fragment: keys are system-made, but a header is no place to trust that."""
    return _SAFE_FILENAME.sub("_", key)[:64] or "plan"


class GardenPlanExportService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        plan_service: GardenPlanService,
        print_engine: PrintEngine | None = None,
        attachment_service: AttachmentService | None = None,
        plant_state_repo: IPlantStateRepository | None = None,
        phase_repo: IPhaseRepository | None = None,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._plans = plan_service
        self._print = print_engine or PrintEngine()
        #: ``None`` = a caller that never prints the underlay.
        self._attachments = attachment_service
        #: ``None`` = plants are printed as the uniform symbol (no states, no phase colours).
        self._plant_states = plant_state_repo
        self._phases = phase_repo

    def _owned_site(self, site_key: SiteKey, *, tenant_key: str) -> Site:
        return require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)

    # ── GP-API-004: the JSON backup ───────────────────────────────────────────

    def export_json(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        scope: ExportScope = "site",
        keys: Sequence[str] = (),
    ) -> GardenPlanExport:
        """The structure of the site's plan; no plant, task, event or account reference (GP-FR-140).

        ``scope`` (GP-FR-172): ``site`` is the whole plan; ``selection`` is exactly the named locations (and, with
        the ``object:`` prefix, garden objects); ``subtree`` is the named locations with everything below them. A
        partial file carries no plan settings, only the slots of its beds, only the zones its beds name, and every
        reference that leaves it (a parent, a zone's water source) as ``null`` - it is a file that stands on its own.
        A key the site does not hold answers 404, exactly like a key of another tenant.
        """
        site = self._owned_site(site_key, tenant_key=tenant_key)
        data = self._plan.load_read_model(site_key, tenant_key=tenant_key, include_plants=False, include_tasks=False)
        zone_rows = self._plans.zone_rows(site_key, tenant_key=tenant_key)
        slots = [slot for slot in data.slots if slot.key and slot.archived_at is None]
        exported_at = datetime.now(UTC)
        header = ExportSite(name=site.name, type=site.type)
        if scope == "site":
            if keys:
                raise _export_error("export.keys_not_allowed", "keys belongs to scope selection or subtree.")
            return GardenPlanExport(
                exported_at=exported_at,
                site=header,
                plan=_validated(ExportPlanSettings, site.plan) if site.plan is not None else None,
                locations=[_validated(ExportLocation, location) for location in data.locations],
                slots=[_validated(ExportSlot, slot) for slot in slots],
                garden_objects=[_validated(ExportGardenObject, obj) for obj in data.garden_objects],
                zones=[ExportZone(**row) for row in zone_rows],
            )
        location_keys, object_keys = _chosen(scope, keys, data.locations, data.garden_objects)
        locations = [_validated(ExportLocation, loc) for loc in data.locations if loc.key in location_keys]
        objects = [_validated(ExportGardenObject, obj) for obj in data.garden_objects if obj.key in object_keys]
        for location in locations:
            _cut_parent(location, location_keys)
        for garden_object in objects:
            _cut_parent(garden_object, location_keys)
        named_zones = {location.irrigation_zone_key for location in locations if location.irrigation_zone_key}
        return GardenPlanExport(
            exported_at=exported_at,
            site=header,
            plan=None,
            locations=locations,
            slots=[_validated(ExportSlot, slot) for slot in slots if slot.location_key in location_keys],
            garden_objects=objects,
            zones=[_zone_of_file(row, object_keys) for row in zone_rows if row["key"] in named_zones],
        )

    # ── GP-API-006: the SVG ───────────────────────────────────────────────────

    def render_svg(
        self, site_key: SiteKey, *, tenant_key: str, options: PlanSvgOptions, now: datetime | None = None
    ) -> PlanSvg:
        view = self._view(site_key, tenant_key=tenant_key, options=options)
        marks = self._plant_marks(view, tenant_key=tenant_key, options=options, now=now)
        return render_plan_svg(view, options, marks)

    # ── GP-API-007: the PDF ───────────────────────────────────────────────────

    async def load_underlay(self, site_key: SiteKey, *, tenant_key: str) -> UnderlayImage | None:
        """The site's underlay picture, read from the tenant's own attachment and prepared for the page.

        ``None`` when the site has none, the attachment is gone or the stored bytes are no image: the plan is
        then printed without it rather than refused.
        """
        site = self._owned_site(site_key, tenant_key=tenant_key)
        if site.plan is None or site.plan.underlay is None or self._attachments is None:
            return None
        try:
            attachment = self._attachments.get_attachment(site.plan.underlay.attachment_key, tenant_key)
            if attachment.category != AttachmentCategory.GARDEN_PLAN_UNDERLAY:
                return None
            chunks = [chunk async for chunk in await self._attachments.open_stream(attachment)]
            # Decoding up to 40 MPx is CPU work: off the event loop.
            return await asyncio.to_thread(prepare_image, b"".join(chunks))
        except NotFoundError, OSError, UnderlayImageError:
            logger.warning("garden_plan.underlay_unavailable", site_key=site_key)
            return None

    def render_pdf(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        options: PlanSvgOptions,
        bed_list: bool = False,
        underlay: UnderlayImage | None = None,
        now: datetime | None = None,
    ) -> PlanPdf:
        """A scaled plan on one page (plus the bed list when asked). 422 ``plan.does_not_fit`` when it cannot."""
        started = perf_counter()
        pdf_options = replace(options, header_mm=PDF_HEADER_MM)
        view = self._view(site_key, tenant_key=tenant_key, options=pdf_options)
        marks = self._plant_marks(view, tenant_key=tenant_key, options=pdf_options, now=now)
        rendered = render_plan_svg(view, pdf_options, marks)
        if not rendered.fits:
            raise PlanError(
                "plan.does_not_fit",
                "The plan does not fit the page at this scale; choose a larger paper or a coarser scale.",
                status_code=422,
                field="scale",
                scale=f"1:{rendered.scale}",
                paper=pdf_options.paper.value,
            )
        page_w, page_h = page_size_mm(pdf_options.paper, pdf_options.orientation)
        placement = self._underlay_placement(site_key, tenant_key=tenant_key, image=underlay, rendered=rendered)
        context = {
            "title": view.site_name,
            "site_name": view.site_name,
            "generated_date": datetime.now(UTC).strftime("%d.%m.%Y" if options.locale == "de" else "%Y-%m-%d"),
            "plan_revision": view.plan_revision,
            "scale_label": f"1:{rendered.scale}",
            "paper_label": f"{pdf_options.paper.value.upper()} {pdf_options.orientation.value}",
            "page_size": f"{pdf_options.paper.value.upper()} {pdf_options.orientation.value}",
            "page_width_mm": page_w,
            "page_height_mm": page_h,
            "suggest_a3": rendered.suggest_a3,
            "svg_data_uri": "data:image/svg+xml;base64,"
            + base64.b64encode(rendered.svg.encode("utf-8")).decode("ascii"),
            "plan_width_mm": rendered.width_mm,
            "plan_height_mm": rendered.height_mm,
            "underlay": placement,
            "beds": self._bed_rows(view, options.locale) if bed_list else [],
            "show_bed_list": bed_list,
        }
        content = self._print.render_pdf(_TEMPLATE, context, options.locale)
        logger.info(
            "garden_plan.pdf_rendered",
            scale=rendered.scale,
            paper=pdf_options.paper.value,
            beds=len(view.locations),
            plants=len(view.plants),
            stated_plants=len(marks.states) if marks is not None else 0,
            seconds=round(perf_counter() - started, 3),
        )
        return PlanPdf(
            content=content,
            scale=rendered.scale,
            paper=pdf_options.paper,
            suggest_a3=rendered.suggest_a3,
            filename=f"garden-plan-{safe_filename_part(site_key)}.pdf",
        )

    # ── Plant states for the print (#2489) ────────────────────────────────────

    def _plant_marks(
        self, view: GardenPlanView, *, tenant_key: str, options: PlanSvgOptions, now: datetime | None = None
    ) -> PlantStateMarks | None:
        """The visual state of every plant of ``view`` and the names of their phases, for the SVG writer.

        ``view`` is the read model of a site this service has already resolved through the tenant anchor; its beds
        are therefore the tenant's, and every plant-state read still filters on ``tenant_key``. ``None`` when the
        plants layer is off, when there is no plant-state source, or from the counter threshold on (nothing is read).
        """
        if (
            self._plant_states is None
            or PlanSvgLayer.PLANTS not in options.layers
            or not view.plants
            or len(view.plants) >= PLANT_COUNTER_THRESHOLD
        ):
            return None
        moment = now if now is not None else datetime.now(UTC)
        wanted = {plant.key for plant in view.plants}
        slot_beds = {slot.key: slot.location_key for slot in view.slots}
        bed_keys = {plant.location_key or slot_beds.get(plant.slot_key or "") for plant in view.plants}
        beds = sorted((loc for loc in view.locations if loc.key and loc.key in bed_keys), key=lambda loc: loc.key or "")
        states: dict[str, PlantVisualState] = {}
        row_names: dict[str, str] = {}
        for bed in beds:
            if bed.key is None:
                continue
            frost_risk = frost_risk_of(bed)
            for row in self._standing_plants(bed.key, tenant_key=tenant_key, now=moment):
                if row.plant_key in wanted:
                    states[row.plant_key] = visual_state_of(row, frost_risk=frost_risk, now=moment)
                    if row.phase_key and row.phase_name and row.phase_name.strip():
                        row_names.setdefault(row.phase_key, row.phase_name)
        phase_names = self._phase_names(
            {state.phase_key for state in states.values() if state.phase_key}, fallback=row_names
        )
        logger.info(
            "garden_plan.plant_states_resolved",
            site_key=view.site_key,
            beds=len(beds),
            plants=len(states),
            phases=len(phase_names),
        )
        return PlantStateMarks(states=states, phase_names=phase_names)

    def _standing_plants(self, bed_key: str, *, tenant_key: str, now: datetime) -> list[PlantStateSource]:
        """Every standing plant of the bed in pages of :data:`STATE_PAGE_SIZE`, at most :data:`_MAX_STATE_PAGES`."""
        if self._plant_states is None:
            return []
        rows: list[PlantStateSource] = []
        for page in range(_MAX_STATE_PAGES):
            window = self._plant_states.list_bed_plants(
                bed_key, tenant_key=tenant_key, now=now, offset=page * STATE_PAGE_SIZE, limit=STATE_PAGE_SIZE
            )
            rows.extend(window)
            if len(window) < STATE_PAGE_SIZE:
                break
        return rows

    def _phase_names(self, phase_keys: set[str], *, fallback: Mapping[str, str]) -> dict[str, str]:
        """``phase key → name``: the growth-phase name where the key is a growth phase (one read per distinct key),
        else the name the plant-state read joined in (``fallback``) — a phase-sequence entry key is no growth phase.

        The rule of the bed view (``BedPlanTab``): the plant-states answer names the phase, the fetched growth-phase
        name wins where there is one. So a plant prints in the colour it has on screen."""
        names: dict[str, str] = {}
        for key in sorted(phase_keys):
            phase = self._phases.get_phase_by_key(key) if self._phases is not None else None
            if phase is not None and phase.name:
                names[key] = phase.name
            elif key in fallback:
                names[key] = fallback[key]
        return names

    # ── helpers ───────────────────────────────────────────────────────────────

    def _underlay_placement(
        self, site_key: SiteKey, *, tenant_key: str, image: UnderlayImage | None, rendered: PlanSvg
    ) -> UnderlayPlacement | None:
        if image is None or rendered.frame is None:
            return None
        site = self._owned_site(site_key, tenant_key=tenant_key)
        if site.plan is None or site.plan.underlay is None:
            return None
        return place_underlay(site.plan.underlay, image, rendered.frame)

    def _view(self, site_key: SiteKey, *, tenant_key: str, options: PlanSvgOptions) -> GardenPlanView:
        self._owned_site(site_key, tenant_key=tenant_key)
        include = frozenset({"plants"}) if PlanSvgLayer.PLANTS in options.layers else frozenset()
        return self._plans.get_plan(site_key, tenant_key=tenant_key, include=include)

    def _bed_rows(self, view: GardenPlanView, locale: str) -> list[dict[str, str]]:
        """Name, area, status and sun exposure of every placed *bed* — no rooms or areas, no notes, no assignments
        (SR-024). Whether a location is a bed is the ``is_bed`` flag of its type."""
        is_bed = self._plan.bed_type_flags(sorted({loc.location_type_key for loc in view.locations}))
        rows = []
        for location in sorted(view.locations, key=lambda loc: loc.name.casefold()):
            if location.geometry is None or not is_bed.get(location.location_type_key, False):
                continue
            rows.append(
                {
                    "name": location.name,
                    "area": f"{location.area_m2:.1f}".replace(".", ",")
                    if locale == "de"
                    else f"{location.area_m2:.1f}",
                    "status": location.bed_status.value,
                    "sun": location.sun_exposure.value,
                }
            )
        return rows
