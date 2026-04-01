"""Print service for generating PDF exports of nutrient plans, care checklists, and plant labels."""

from datetime import UTC, datetime

import structlog

from app.domain.engines.print_engine import PrintEngine
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.care_reminder import CareDashboardEntry
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.nutrient_plan_service import NutrientPlanService

logger = structlog.get_logger(__name__)


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
    ) -> None:
        self._nutrient_plan_service = nutrient_plan_service
        self._care_reminder_service = care_reminder_service
        self._fert_repo = fertilizer_repo
        self._plant_repo = plant_repo
        self._species_repo = species_repo
        self._print_engine = print_engine or PrintEngine()
        self._site_repo = site_repo
        self._app_base_url = app_base_url

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
        entries = self._nutrient_plan_service.get_phase_entries(plan_key)

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
            tenant_key=tenant_key,
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
        plants, _total = self._plant_repo.get_all(
            offset=0,
            limit=500,
            tenant_key=tenant_key,
        )

        # Resolve species names via species_repo (cache to avoid repeated lookups)
        species_cache: dict[str, str] = {}

        # Build plant_data dicts for care reminder service
        plant_data: list[dict] = []
        for plant in plants:
            species_name = None
            if plant.species_key:
                if plant.species_key not in species_cache:
                    species = self._species_repo.get_by_key(plant.species_key)
                    species_cache[plant.species_key] = (
                        species.common_names[0] if species and species.common_names else ""
                    )
                species_name = species_cache[plant.species_key] or None

            plant_data.append(
                {
                    "plant_key": plant.key or "",
                    "plant_name": plant.plant_name or plant.instance_id or "",
                    "species_name": species_name,
                    "botanical_family": None,
                    "current_phase": None,
                    "has_nutrient_plan": False,
                }
            )

        # Get care dashboard entries
        entries = self._care_reminder_service.get_care_dashboard(plant_data, hemisphere="north")

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
            tenant_key=tenant_key,
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
        from app.common.exceptions import NotFoundError

        # Caches to avoid repeated lookups
        species_cache: dict[str, dict] = {}
        cultivar_cache: dict[str, str] = {}
        location_cache: dict[str, str] = {}

        cards: list[dict] = []

        for plant_key in plant_keys:
            plant = self._plant_repo.get_by_key(plant_key)
            if plant is None:
                raise NotFoundError("PlantInstance", plant_key)

            # Resolve species data
            species_data: dict = {}
            if plant.species_key:
                if plant.species_key not in species_cache:
                    species = self._species_repo.get_by_key(plant.species_key)
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
                    location = self._site_repo.get_location_by_key(plant.location_key)
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
            tenant_key=tenant_key,
            plant_count=len(cards),
            layout=layout,
            fields=fields,
        )

        return self._print_engine.render_pdf("plant_label.html", context, locale)

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
