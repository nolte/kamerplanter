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
fetching (GP-NFR-052 (a), (f)). Images from attachments are not embedded yet — the only consumer would be the
background layer of GP-FR-033 — and when they are, they enter here as ``data:`` URIs read from the tenant's own
attachments.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from time import perf_counter

import structlog

from app.common.exceptions import PlanError
from app.common.types import SiteKey
from app.domain.engines.plan_svg_engine import (
    PDF_HEADER_MM,
    PlanPaper,
    PlanSvg,
    PlanSvgLayer,
    PlanSvgOptions,
    page_size_mm,
    render_plan_svg,
)
from app.domain.engines.print_engine import PrintEngine
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.garden_plan import GardenPlanView
from app.domain.models.garden_plan_export import (
    ExportGardenObject,
    ExportLocation,
    ExportPlanSettings,
    ExportSite,
    ExportSlot,
    ExportZone,
    GardenPlanExport,
)
from app.domain.models.site import Site
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.location_ownership import require_owned_site

logger = structlog.get_logger(__name__)

_TEMPLATE = "garden_plan.html"
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9_-]")


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
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._plans = plan_service
        self._print = print_engine or PrintEngine()

    def _owned_site(self, site_key: SiteKey, *, tenant_key: str) -> Site:
        return require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)

    # ── GP-API-004: the JSON backup ───────────────────────────────────────────

    def export_json(self, site_key: SiteKey, *, tenant_key: str) -> GardenPlanExport:
        """The structure of the site's plan; no plant, task, event or account reference (GP-FR-140)."""
        site = self._owned_site(site_key, tenant_key=tenant_key)
        data = self._plan.load_read_model(site_key, tenant_key=tenant_key, include_plants=False, include_tasks=False)
        plan = site.plan
        return GardenPlanExport(
            exported_at=datetime.now(UTC),
            site=ExportSite(name=site.name, type=site.type),
            plan=ExportPlanSettings.model_validate(plan) if plan is not None else None,
            locations=[ExportLocation.model_validate(location) for location in data.locations],
            slots=[ExportSlot.model_validate(slot) for slot in data.slots if slot.key and slot.archived_at is None],
            garden_objects=[ExportGardenObject.model_validate(obj) for obj in data.garden_objects],
            zones=[ExportZone(**row) for row in self._plans.zone_rows(site_key, tenant_key=tenant_key)],
        )

    # ── GP-API-006: the SVG ───────────────────────────────────────────────────

    def render_svg(self, site_key: SiteKey, *, tenant_key: str, options: PlanSvgOptions) -> PlanSvg:
        view = self._view(site_key, tenant_key=tenant_key, options=options)
        return render_plan_svg(view, options)

    # ── GP-API-007: the PDF ───────────────────────────────────────────────────

    def render_pdf(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        options: PlanSvgOptions,
        bed_list: bool = False,
    ) -> PlanPdf:
        """A scaled plan on one page (plus the bed list when asked). 422 ``plan.does_not_fit`` when it cannot."""
        started = perf_counter()
        pdf_options = replace(options, header_mm=PDF_HEADER_MM)
        view = self._view(site_key, tenant_key=tenant_key, options=pdf_options)
        rendered = render_plan_svg(view, pdf_options)
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
            seconds=round(perf_counter() - started, 3),
        )
        return PlanPdf(
            content=content,
            scale=rendered.scale,
            paper=pdf_options.paper,
            suggest_a3=rendered.suggest_a3,
            filename=f"garden-plan-{safe_filename_part(site_key)}.pdf",
        )

    # ── helpers ───────────────────────────────────────────────────────────────

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
