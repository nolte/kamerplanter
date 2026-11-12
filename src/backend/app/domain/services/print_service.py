"""Print service for generating PDF exports of nutrient plans, care checklists, plant and bed labels."""

from datetime import UTC, datetime
from urllib.parse import quote, urlencode

import structlog

from app.common.exceptions import NotFoundError
from app.common.log_privacy import log_tenant
from app.common.tenant_guard import verify_tenant_ownership
from app.data_access.arango.base_repository import get_all_pages
from app.domain.engines.print_engine import PrintEngine, format_decimal
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.care_reminder import CareDashboardEntry
from app.domain.models.location_type import LocationType
from app.domain.models.site import Location, Site
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.location_ownership import find_owned_location, require_owned_site
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.species_visibility import readable_species

logger = structlog.get_logger(__name__)

#: Default QR edge length of a bed label (GP-FR-052): larger than a pot card's 25 mm, because a bed label is read from
#: standing height. REQ-032 §2.7 sets 20 mm as the floor for reliable scanning.
LOCATION_LABEL_QR_DEFAULT_MM = 40


def location_label_url(app_base_url: str, *, site_key: str, location_key: str, is_bed: bool) -> str:
    """The URL a bed label's QR code carries (REQ-053 GP-UX-028, GP-NFR-053).

    A bed opens in field mode of its site's plan with the bed's sheet open:
    ``{base}/standorte/sites/{site}/plan?mode=field&bed={key}``. Any other location opens its own page,
    ``{base}/standorte/locations/{key}`` - field mode lists beds only. The path is the app's own route, with no token
    and no tenant: who scans it without a session signs in first and is brought back to it (UI-NFR-014 R-009), and
    a non-member gets the 404 of the site (SR-023). Keys are percent-encoded, so a key can never add a path segment or
    a parameter.
    """
    base = app_base_url.rstrip("/")
    if is_bed:
        query = urlencode({"mode": "field", "bed": location_key})
        return f"{base}/standorte/sites/{quote(site_key, safe='')}/plan?{query}"
    return f"{base}/standorte/locations/{quote(location_key, safe='')}"


class PrintService:
    """Generates printable PDF documents for nutrient plans and care checklists."""

    def __init__(
        self,
        nutrient_plan_service: NutrientPlanService,
        care_reminder_service: CareReminderService,
        fertilizer_repo: IFertilizerRepository,
        plant_repo: IPlantInstanceRepository,
        species_repo: ISpeciesRepository,
        print_engine: PrintEngine | None = None,
        site_repo: ISiteRepository | None = None,
        app_base_url: str = "http://localhost:5173",
        location_type_repo: ILocationTypeRepository | None = None,
    ) -> None:
        self._nutrient_plan_service = nutrient_plan_service
        self._care_reminder_service = care_reminder_service
        self._fert_repo = fertilizer_repo
        self._plant_repo = plant_repo
        self._species_repo = species_repo
        self._print_engine = print_engine or PrintEngine()
        self._site_repo = site_repo
        self._app_base_url = app_base_url
        self._location_type_repo = location_type_repo

    def generate_nutrient_plan_pdf(
        self,
        plan_key: str,
        tenant_key: str,
        locale: str = "de",
    ) -> bytes:
        """Generate a PDF document for a nutrient plan.

        Args:
            plan_key: Key of the nutrient plan.
            tenant_key: Tenant key for access control.
            locale: Locale for labels ('de' or 'en').

        Returns:
            PDF file content as bytes.

        Raises:
            NotFoundError: If the plan does not exist.
        """
        plan = self._nutrient_plan_service.get_plan(plan_key, tenant_key=tenant_key)
        entries = self._nutrient_plan_service.get_phase_entries(plan_key, tenant_key=tenant_key)

        # Build phase data with resolved fertilizer names
        phases_data: list[dict] = []
        for entry in sorted(entries, key=lambda e: e.sequence_order):
            channels_data: list[dict] = []
            for channel in entry.delivery_channels:
                dosages_data: list[dict] = []
                for dosage in sorted(channel.fertilizer_dosages, key=lambda d: d.mixing_order):
                    fert = self._fert_repo.get_by_key(dosage.fertilizer_key)
                    dosages_data.append(
                        {
                            "product_name": fert.product_name if fert else dosage.fertilizer_key,
                            "ml_per_liter": dosage.ml_per_liter,
                            "optional": dosage.optional,
                            "mixing_order": dosage.mixing_order,
                        }
                    )

                channels_data.append(
                    {
                        "channel_id": channel.channel_id,
                        "label": channel.label,
                        "application_method": channel.application_method.value,
                        "target_ec_ms": channel.target_ec_ms,
                        "target_ph": channel.target_ph,
                        "dosages": dosages_data,
                    }
                )

            phases_data.append(
                {
                    "phase_name": entry.phase_name.value,
                    "week_start": entry.week_start,
                    "week_end": entry.week_end,
                    "target_ec_ms": entry.target_ec_ms,
                    "npk_ratio": list(entry.npk_ratio),
                    "calcium_ppm": entry.calcium_ppm,
                    "magnesium_ppm": entry.magnesium_ppm,
                    "sulfur_ppm": entry.sulfur_ppm,
                    "notes": entry.notes,
                    "channels": channels_data,
                }
            )

        # Build water config info
        water_config = None
        if plan.water_mix_ratio_ro_percent is not None:
            water_config = {
                "ro_percent": plan.water_mix_ratio_ro_percent,
                "base_ec_note": None,
            }

        # Collect flushing/calmag notes from phase entries
        flushing_notes = None
        calmag_notes = None
        for entry in entries:
            if entry.phase_name.value == "flushing" and entry.notes:
                flushing_notes = entry.notes
            if entry.notes and "calmag" in entry.notes.lower():
                calmag_notes = entry.notes

        context = {
            "plan_name": plan.name,
            "description": plan.description,
            "author": plan.author,
            "substrate_type": plan.recommended_substrate_type.value if plan.recommended_substrate_type else None,
            "generated_date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),
            "phases": phases_data,
            "water_config": water_config,
            "flushing_notes": flushing_notes,
            "calmag_notes": calmag_notes,
        }

        logger.info(
            "print_service.generate_nutrient_plan_pdf",
            plan_key=plan_key,
            tenant=log_tenant(tenant_key),
            phase_count=len(phases_data),
        )

        return self._print_engine.render_pdf("nutrient_plan.html", context, locale)

    def generate_care_checklist_pdf(
        self,
        tenant_key: str,
        date: str | None = None,
        locale: str = "de",
    ) -> bytes:
        """Generate a PDF care checklist for all plants in a tenant.

        Args:
            tenant_key: Tenant key for scoping plants.
            date: Optional ISO date string to filter entries.
            locale: Locale for labels ('de' or 'en').

        Returns:
            PDF file content as bytes.
        """
        # Load all plant instances for the tenant
        plants = get_all_pages(self._plant_repo, tenant_key=tenant_key)  # every plant, not the first 500 (#2015)

        # Resolve species names via species_repo (cache to avoid repeated lookups)
        species_cache: dict[str, str] = {}

        # Build plant_data dicts for care reminder service
        plant_data: list[dict] = []
        for plant in plants:
            species_name = None
            if plant.species_key:
                if plant.species_key not in species_cache:
                    species = readable_species(self._species_repo, plant.species_key, tenant_key)
                    species_cache[plant.species_key] = (
                        species.common_names[0] if species and species.common_names else ""
                    )
                species_name = species_cache[plant.species_key] or None

            plant_data.append(
                {
                    "plant_key": plant.key or "",
                    "plant_name": plant.plant_name or plant.instance_id or "",
                    "species_name": species_name,
                    "current_phase": None,
                    "has_nutrient_plan": False,
                }
            )

        # Get care dashboard entries
        entries = self._care_reminder_service.get_care_dashboard(plant_data, hemisphere="north", tenant_key=tenant_key)

        # Filter by date if provided
        if date:
            entries = [e for e in entries if e.due_date and e.due_date.startswith(date)]

        # Group by urgency
        urgency_order = ["overdue", "due_today", "upcoming"]
        urgency_groups: list[dict] = []
        for urgency in urgency_order:
            group_entries = [e for e in entries if e.urgency == urgency]
            if group_entries:
                urgency_groups.append(
                    {
                        "urgency": urgency,
                        "label": self._get_urgency_label(urgency, locale),
                        "entries": [self._entry_to_dict(e) for e in group_entries],
                    }
                )

        context = {
            "generated_date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),
            "target_date": date,
            "entries": [self._entry_to_dict(e) for e in entries],
            "urgency_groups": urgency_groups,
        }

        logger.info(
            "print_service.generate_care_checklist_pdf",
            tenant=log_tenant(tenant_key),
            date=date,
            entry_count=len(entries),
        )

        return self._print_engine.render_pdf("care_checklist.html", context, locale)

    def generate_plant_labels_pdf(
        self,
        tenant_key: str,
        tenant_slug: str,
        plant_keys: list[str],
        fields: list[str],
        layout: str = "grid_2x4",
        qr_size_mm: int = 25,
        locale: str = "de",
    ) -> bytes:
        """Generate a PDF with plant info cards / labels including QR codes.

        Args:
            tenant_key: Tenant key for scoping plants.
            tenant_slug: Tenant slug for constructing QR code URLs.
            plant_keys: List of PlantInstance keys to include.
            fields: List of field names to display on each card.
            layout: Card layout — 'single', 'grid_2x4', or 'grid_3x3'.
            qr_size_mm: QR code size in millimeters.
            locale: Locale for labels ('de' or 'en').

        Returns:
            PDF file content as bytes.

        Raises:
            NotFoundError: If a plant instance does not exist.
        """

        # Caches to avoid repeated lookups
        species_cache: dict[str, dict] = {}
        cultivar_cache: dict[str, str] = {}
        location_cache: dict[str, str] = {}

        cards: list[dict] = []

        for plant_key in plant_keys:
            plant = self._plant_repo.get_or_raise(plant_key)
            # A foreign plant answers like an absent one: its name, species and location must not reach the PDF.
            verify_tenant_ownership(plant, tenant_key, "PlantInstance")

            # Resolve species data
            species_data: dict = {}
            if plant.species_key:
                if plant.species_key not in species_cache:
                    species = readable_species(self._species_repo, plant.species_key, tenant_key)
                    if species:
                        species_data = {
                            "scientific_name": species.scientific_name,
                            "common_name": (species.common_names[0] if species.common_names else ""),
                            "family_key": species.family_key,
                        }
                    else:
                        species_data = {}
                    species_cache[plant.species_key] = species_data
                species_data = species_cache[plant.species_key]

            # Resolve cultivar name
            cultivar_name = ""
            if plant.cultivar_key:
                if plant.cultivar_key not in cultivar_cache:
                    cultivar = self._species_repo.get_cultivar_by_key(plant.cultivar_key)
                    cultivar_cache[plant.cultivar_key] = cultivar.name if cultivar else ""
                cultivar_name = cultivar_cache[plant.cultivar_key]

            # Resolve location name
            location_name = ""
            if plant.location_key and self._site_repo:
                if plant.location_key not in location_cache:
                    # Anchored on the location's site (#1397): a dangling or foreign location prints no name.
                    location = find_owned_location(self._site_repo, plant.location_key, tenant_key)
                    location_cache[plant.location_key] = location.name if location else ""
                location_name = location_cache[plant.location_key]

            # Resolve current phase name
            phase_name = ""
            if plant.current_phase_key:
                phase_name = self._plant_repo.resolve_phase_name(plant.current_phase_key)

            # Build display name
            display_name = plant.plant_name or plant.instance_id or ""

            # Generate QR code
            qr_url = f"{self._app_base_url}/t/{tenant_slug}/plants/{plant_key}"
            qr_data_uri = PrintEngine.generate_qr_code_base64(qr_url, qr_size_mm)

            cards.append(
                {
                    "name": display_name,
                    "scientific_name": species_data.get("scientific_name", ""),
                    "family": "",  # family_key would need separate resolution
                    "cultivar": cultivar_name,
                    "planted_date": (
                        plant.planted_on.strftime("%d.%m.%Y")
                        if locale == "de"
                        else plant.planted_on.strftime("%Y-%m-%d")
                    ),
                    "current_phase": phase_name,
                    "location": location_name,
                    "note": "",
                    "qr_data_uri": qr_data_uri,
                }
            )

        context = {
            "cards": cards,
            "fields": fields,
            "layout": layout,
            "qr_size_mm": qr_size_mm,
            "generated_date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),
        }

        logger.info(
            "print_service.generate_plant_labels_pdf",
            tenant=log_tenant(tenant_key),
            plant_count=len(cards),
            layout=layout,
            fields=fields,
        )

        return self._print_engine.render_pdf("plant_label.html", context, locale)

    def generate_location_label_pdf(
        self,
        location_key: str,
        *,
        tenant_key: str,
        qr_size_mm: int = LOCATION_LABEL_QR_DEFAULT_MM,
        locale: str = "de",
    ) -> bytes:
        """A printable label of a bed with a QR code that opens it in field mode (REQ-053 GP-FR-052, GP-UX-028).

        The label names the bed, its site, its type and - while it has one - its area. The QR code carries
        :func:`location_label_url`: field mode of the site's plan with the bed's sheet open for a bed (type with
        ``is_bed``), the location page for any other location.

        Ownership is anchored on the location's site (``location_ownership``, #1397): an absent location, one
        without a site and one under a foreign site all raise the same ``NotFoundError``.

        Args:
            location_key: Key of the bed (or other location).
            tenant_key: The caller's tenant; the location's site must belong to it.
            qr_size_mm: QR code edge length in millimetres.
            locale: Locale of the printed labels ('de' or 'en').

        Returns:
            PDF file content as bytes.

        Raises:
            NotFoundError: If the location does not exist or does not belong to the tenant.
        """
        location, site = self._owned_location_and_site(location_key, tenant_key=tenant_key)
        location_type = self._location_type(location.location_type_key)
        is_bed = location_type is not None and location_type.is_bed
        qr_url = location_label_url(
            self._app_base_url, site_key=site.key or location.site_key, location_key=location_key, is_bed=is_bed
        )
        label = {
            "name": location.name,
            "site_name": site.name,
            "type_name": self._location_type_name(location_type, location.location_type_key, locale),
            # A location without an area says nothing rather than "0 m²" (as the bed head, GP-FR-047).
            "area": format_decimal(location.area_m2, locale) if location.area_m2 > 0 else "",
            "qr_url": qr_url,
            "qr_data_uri": PrintEngine.generate_qr_code_base64(qr_url, qr_size_mm),
            "title_key": "location_label_title" if is_bed else "location_label_title_location",
            "hint_key": "location_label_scan_hint" if is_bed else "location_label_scan_hint_location",
            "qr_alt_key": "location_label_qr_alt" if is_bed else "location_label_qr_alt_location",
        }
        context = {
            "label": label,
            "qr_size_mm": qr_size_mm,
            "title": location.name,
            "generated_date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),
        }

        logger.info(
            "print_service.generate_location_label_pdf",
            tenant=log_tenant(tenant_key),
            location_key=location_key,
            is_bed=is_bed,
            qr_size_mm=qr_size_mm,
        )

        return self._print_engine.render_pdf("location_label.html", context, locale)

    def _owned_location_and_site(self, location_key: str, *, tenant_key: str) -> tuple[Location, Site]:
        """The location and its site, both owned by ``tenant_key``; ``NotFoundError`` otherwise.

        The same walk as :func:`resolve_owned_location`, kept here because the label needs the site too and must
        not read it twice. Without a site repository there is nothing to anchor on, so the answer is a refusal.
        """
        if self._site_repo is None or not location_key:
            raise NotFoundError("Location", location_key)
        location = self._site_repo.get_location_by_key(location_key)
        if location is None:
            raise NotFoundError("Location", location_key)
        site = require_owned_site(self._site_repo, location.site_key, tenant_key, "Location", location_key)
        return location, site

    def _location_type(self, location_type_key: str) -> LocationType | None:
        """The location type, or ``None`` when it is unset, unknown or no type repository is wired."""
        if not location_type_key or self._location_type_repo is None:
            return None
        return self._location_type_repo.get_by_key(location_type_key)

    @staticmethod
    def _location_type_name(location_type: LocationType | None, location_type_key: str, locale: str) -> str:
        """The type's display name in ``locale`` (English name when there is one), else the raw key."""
        if location_type is None:
            return location_type_key
        if locale == "en" and location_type.name_en:
            return location_type.name_en
        return location_type.name

    @staticmethod
    def _entry_to_dict(entry: CareDashboardEntry) -> dict:
        """Convert a CareDashboardEntry to a template-friendly dict."""
        return {
            "plant_key": entry.plant_key,
            "plant_name": entry.plant_name,
            "species_name": entry.species_name,
            "reminder_type": entry.reminder_type.value,
            "urgency": entry.urgency,
            "due_date": entry.due_date,
            "location": None,
        }

    @staticmethod
    def _get_urgency_label(urgency: str, locale: str) -> str:
        """Get localized urgency group label."""
        labels = {
            "de": {
                "overdue": "\u00dcberf\u00e4llig",
                "due_today": "Heute f\u00e4llig",
                "upcoming": "Demn\u00e4chst",
            },
            "en": {
                "overdue": "Overdue",
                "due_today": "Due today",
                "upcoming": "Upcoming",
            },
        }
        return labels.get(locale, labels["de"]).get(urgency, urgency)
