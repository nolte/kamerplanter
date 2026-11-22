"""Tests for PrintService."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.common.enums import ApplicationMethod, PhaseName, ReminderType, SubstrateType
from app.common.exceptions import NotFoundError
from app.domain.models.care_reminder import CareDashboardEntry
from app.domain.models.location_type import LocationType
from app.domain.models.nutrient_plan import (
    DeliveryChannel,
    FertilizerDosage,
    NutrientPlan,
    NutrientPlanPhaseEntry,
)
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location, Site
from app.domain.services.print_service import LOCATION_LABEL_QR_DEFAULT_MM, PrintService, location_label_url
from tests.conftest import wire_get_or_raise


@pytest.fixture
def mock_nutrient_plan_service():
    return MagicMock()


@pytest.fixture
def mock_care_reminder_service():
    return MagicMock()


@pytest.fixture
def mock_fertilizer_repo():
    return MagicMock()


@pytest.fixture
def mock_plant_repo():
    return wire_get_or_raise(MagicMock(), "PlantInstance")


@pytest.fixture
def mock_species_repo():
    return MagicMock()


@pytest.fixture
def mock_print_engine():
    engine = MagicMock()
    engine.render_pdf.return_value = b"%PDF-1.7 mock content"
    return engine


@pytest.fixture
def mock_site_repo():
    return MagicMock()


@pytest.fixture
def service(
    mock_nutrient_plan_service,
    mock_care_reminder_service,
    mock_fertilizer_repo,
    mock_plant_repo,
    mock_species_repo,
    mock_print_engine,
    mock_site_repo,
):
    return PrintService(
        nutrient_plan_service=mock_nutrient_plan_service,
        care_reminder_service=mock_care_reminder_service,
        fertilizer_repo=mock_fertilizer_repo,
        plant_repo=mock_plant_repo,
        species_repo=mock_species_repo,
        print_engine=mock_print_engine,
        site_repo=mock_site_repo,
        app_base_url="https://app.example.com",
    )


def _make_plan(key: str = "plan1") -> NutrientPlan:
    return NutrientPlan(
        _key=key,
        tenant_key="t1",
        name="Test Nutrient Plan",
        description="A test plan",
        author="Test Author",
        recommended_substrate_type=SubstrateType.COCO,
        water_mix_ratio_ro_percent=50,
    )


def _make_phase_entry(plan_key: str = "plan1") -> NutrientPlanPhaseEntry:
    return NutrientPlanPhaseEntry(
        _key="entry1",
        plan_key=plan_key,
        phase_name=PhaseName.VEGETATIVE,
        sequence_order=1,
        week_start=1,
        week_end=4,
        target_ec_ms=1.2,
        npk_ratio=(3.0, 1.0, 3.0),
        calcium_ppm=120.0,
        magnesium_ppm=50.0,
        sulfur_ppm=30.0,
        delivery_channels=[
            DeliveryChannel(
                channel_id="main",
                label="Main Feed",
                application_method=ApplicationMethod.DRENCH,
                target_ec_ms=1.2,
                fertilizer_dosages=[
                    FertilizerDosage(
                        fertilizer_key="fert1",
                        ml_per_liter=2.0,
                        mixing_order=0,
                    ),
                    FertilizerDosage(
                        fertilizer_key="fert2",
                        ml_per_liter=1.5,
                        mixing_order=1,
                    ),
                ],
            ),
        ],
    )


class TestGenerateNutrientPlanPdf:
    def test_happy_path(
        self,
        service,
        mock_nutrient_plan_service,
        mock_fertilizer_repo,
        mock_print_engine,
    ):
        """Successfully generates a nutrient plan PDF."""
        plan = _make_plan()
        entry = _make_phase_entry()
        mock_nutrient_plan_service.get_plan.return_value = plan
        mock_nutrient_plan_service.get_phase_entries.return_value = [entry]

        fert1 = MagicMock()
        fert1.product_name = "Terra Grow"
        fert2 = MagicMock()
        fert2.product_name = "CalMag"
        mock_fertilizer_repo.get_by_key.side_effect = lambda k: {"fert1": fert1, "fert2": fert2}.get(k)

        result = service.generate_nutrient_plan_pdf("plan1", "t1", locale="de")

        assert result == b"%PDF-1.7 mock content"
        mock_print_engine.render_pdf.assert_called_once()
        call_args = mock_print_engine.render_pdf.call_args
        assert call_args[0][0] == "nutrient_plan.html"
        context = call_args[0][1]
        assert context["plan_name"] == "Test Nutrient Plan"
        assert context["author"] == "Test Author"
        assert len(context["phases"]) == 1
        assert len(context["phases"][0]["channels"]) == 1
        assert len(context["phases"][0]["channels"][0]["dosages"]) == 2

    def test_plan_not_found_raises(
        self,
        service,
        mock_nutrient_plan_service,
    ):
        """Raises NotFoundError when plan does not exist."""
        mock_nutrient_plan_service.get_plan.side_effect = NotFoundError("NutrientPlan", "missing")

        with pytest.raises(NotFoundError):
            service.generate_nutrient_plan_pdf("missing", "t1")

    def test_fertilizer_not_found_uses_key_as_name(
        self,
        service,
        mock_nutrient_plan_service,
        mock_fertilizer_repo,
        mock_print_engine,
    ):
        """Uses fertilizer key as product name when fertilizer not found."""
        plan = _make_plan()
        entry = _make_phase_entry()
        mock_nutrient_plan_service.get_plan.return_value = plan
        mock_nutrient_plan_service.get_phase_entries.return_value = [entry]
        mock_fertilizer_repo.get_by_key.return_value = None

        result = service.generate_nutrient_plan_pdf("plan1", "t1")

        assert result == b"%PDF-1.7 mock content"
        context = mock_print_engine.render_pdf.call_args[0][1]
        dosages = context["phases"][0]["channels"][0]["dosages"]
        assert dosages[0]["product_name"] == "fert1"

    def test_english_locale(
        self,
        service,
        mock_nutrient_plan_service,
        mock_fertilizer_repo,
        mock_print_engine,
    ):
        """Passes English locale to print engine."""
        plan = _make_plan()
        mock_nutrient_plan_service.get_plan.return_value = plan
        mock_nutrient_plan_service.get_phase_entries.return_value = []
        mock_fertilizer_repo.get_by_key.return_value = None

        service.generate_nutrient_plan_pdf("plan1", "t1", locale="en")

        assert mock_print_engine.render_pdf.call_args[0][2] == "en"

    def test_no_water_config(
        self,
        service,
        mock_nutrient_plan_service,
        mock_print_engine,
    ):
        """Plan without RO percent has no water config in context."""
        plan = NutrientPlan(
            _key="plan1",
            tenant_key="t1",
            name="Plan",
            water_mix_ratio_ro_percent=None,
        )
        mock_nutrient_plan_service.get_plan.return_value = plan
        mock_nutrient_plan_service.get_phase_entries.return_value = []

        service.generate_nutrient_plan_pdf("plan1", "t1")

        context = mock_print_engine.render_pdf.call_args[0][1]
        assert context["water_config"] is None


class TestGenerateCareChecklistPdf:
    def test_happy_path(
        self,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_care_reminder_service,
        mock_print_engine,
    ):
        """Successfully generates a care checklist PDF."""
        plant = MagicMock()
        plant.key = "p1"
        plant.plant_name = "My Tomato"
        plant.instance_id = "TOM-001"
        plant.species_key = "sp1"
        mock_plant_repo.get_all.return_value = ([plant], 1)

        species = MagicMock()
        species.common_names = ["Tomate"]
        mock_species_repo.get_by_key.return_value = species

        dashboard_entry = CareDashboardEntry(
            plant_key="p1",
            plant_name="My Tomato",
            species_name="Tomate",
            reminder_type=ReminderType.WATERING,
            urgency="due_today",
            due_date="2026-04-01",
            care_profile_key="cp1",
        )
        mock_care_reminder_service.get_care_dashboard.return_value = [dashboard_entry]

        result = service.generate_care_checklist_pdf("t1")

        assert result == b"%PDF-1.7 mock content"
        mock_print_engine.render_pdf.assert_called_once()
        context = mock_print_engine.render_pdf.call_args[0][1]
        assert len(context["urgency_groups"]) == 1
        assert context["urgency_groups"][0]["urgency"] == "due_today"

    def test_date_filter(
        self,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_care_reminder_service,
        mock_print_engine,
    ):
        """Filters entries by date when provided."""
        mock_plant_repo.get_all.return_value = ([], 0)
        mock_care_reminder_service.get_care_dashboard.return_value = [
            CareDashboardEntry(
                plant_key="p1",
                plant_name="Plant A",
                reminder_type=ReminderType.WATERING,
                urgency="due_today",
                due_date="2026-04-01",
                care_profile_key="cp1",
            ),
            CareDashboardEntry(
                plant_key="p2",
                plant_name="Plant B",
                reminder_type=ReminderType.FERTILIZING,
                urgency="upcoming",
                due_date="2026-04-05",
                care_profile_key="cp2",
            ),
        ]

        service.generate_care_checklist_pdf("t1", date="2026-04-01")

        context = mock_print_engine.render_pdf.call_args[0][1]
        # Only the entry matching the date should remain
        assert len(context["entries"]) == 1
        assert context["entries"][0]["due_date"] == "2026-04-01"

    def test_empty_plants(
        self,
        service,
        mock_plant_repo,
        mock_care_reminder_service,
        mock_print_engine,
    ):
        """Works when no plants exist for the tenant."""
        mock_plant_repo.get_all.return_value = ([], 0)
        mock_care_reminder_service.get_care_dashboard.return_value = []

        result = service.generate_care_checklist_pdf("t1")

        assert result == b"%PDF-1.7 mock content"
        context = mock_print_engine.render_pdf.call_args[0][1]
        assert context["entries"] == []
        assert context["urgency_groups"] == []

    def test_species_name_resolution_with_cache(
        self,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_care_reminder_service,
        mock_print_engine,
    ):
        """Caches species lookups to avoid repeated DB queries."""
        plant1 = MagicMock()
        plant1.key = "p1"
        plant1.plant_name = "Plant 1"
        plant1.instance_id = "P-001"
        plant1.species_key = "sp1"

        plant2 = MagicMock()
        plant2.key = "p2"
        plant2.plant_name = "Plant 2"
        plant2.instance_id = "P-002"
        plant2.species_key = "sp1"  # Same species

        mock_plant_repo.get_all.return_value = ([plant1, plant2], 2)

        species = MagicMock()
        species.common_names = ["Tomate"]
        mock_species_repo.get_by_key.return_value = species

        mock_care_reminder_service.get_care_dashboard.return_value = []

        service.generate_care_checklist_pdf("t1")

        # Species repo should only be called once for the shared species_key
        assert mock_species_repo.get_by_key.call_count == 1


class TestUrgencyLabel:
    def test_german_labels(self):
        assert PrintService._get_urgency_label("overdue", "de") == "\u00dcberf\u00e4llig"
        assert PrintService._get_urgency_label("due_today", "de") == "Heute f\u00e4llig"
        assert PrintService._get_urgency_label("upcoming", "de") == "Demn\u00e4chst"

    def test_english_labels(self):
        assert PrintService._get_urgency_label("overdue", "en") == "Overdue"
        assert PrintService._get_urgency_label("due_today", "en") == "Due today"
        assert PrintService._get_urgency_label("upcoming", "en") == "Upcoming"

    def test_unknown_locale_falls_back_to_german(self):
        assert PrintService._get_urgency_label("overdue", "fr") == "\u00dcberf\u00e4llig"

    def test_unknown_urgency_returns_raw_value(self):
        assert PrintService._get_urgency_label("unknown", "de") == "unknown"


def _make_plant_instance(key: str = "p1", species_key: str = "sp1") -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key="t1",
        instance_id=f"INST-{key}",
        species_key=species_key,
        cultivar_key="cv1",
        location_key="loc1",
        plant_name="Test Plant",
        planted_on=date(2026, 3, 15),
        current_phase_key="phase1",
    )


class TestGeneratePlantLabelsPdf:
    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_happy_path(
        self,
        mock_qr,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_site_repo,
        mock_print_engine,
    ):
        """Successfully generates plant labels PDF with all fields."""
        mock_qr.return_value = "data:image/png;base64,AAAA"

        plant = _make_plant_instance()
        mock_plant_repo.get_by_key.return_value = plant

        species = MagicMock()
        species.scientific_name = "Solanum lycopersicum"
        species.common_names = ["Tomate"]
        species.family_key = "fam1"
        mock_species_repo.get_by_key.return_value = species

        cultivar = MagicMock()
        cultivar.name = "San Marzano"
        mock_species_repo.get_cultivar_by_key.return_value = cultivar

        # The location name is read through the site anchor (#1397): the location's site belongs to t1.
        mock_site_repo.get_location_by_key.return_value = Location(
            _key="loc1", name="Growzelt A", site_key="s1", area_m2=1
        )
        mock_site_repo.get_site_by_key.return_value = Site(_key="s1", tenant_key="t1", name="Keller")

        mock_plant_repo.resolve_phase_name.return_value = "Vegetative"

        result = service.generate_plant_labels_pdf(
            tenant_key="t1",
            tenant_slug="my-garden",
            plant_keys=["p1"],
            fields=["name", "scientific_name", "cultivar", "location"],
            layout="grid_2x4",
            qr_size_mm=25,
            locale="de",
        )

        assert result == b"%PDF-1.7 mock content"
        mock_print_engine.render_pdf.assert_called_once()
        call_args = mock_print_engine.render_pdf.call_args
        assert call_args[0][0] == "plant_label.html"
        context = call_args[0][1]
        assert len(context["cards"]) == 1
        assert context["cards"][0]["name"] == "Test Plant"
        assert context["cards"][0]["scientific_name"] == "Solanum lycopersicum"
        assert context["cards"][0]["cultivar"] == "San Marzano"
        assert context["cards"][0]["location"] == "Growzelt A"
        assert context["layout"] == "grid_2x4"
        assert context["fields"] == ["name", "scientific_name", "cultivar", "location"]

        # Verify QR code URL
        mock_qr.assert_called_once_with("https://app.example.com/t/my-garden/plants/p1", 25)

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_plant_not_found_raises(
        self,
        mock_qr,
        service,
        mock_plant_repo,
    ):
        """Raises NotFoundError when plant does not exist."""
        mock_plant_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.generate_plant_labels_pdf(
                tenant_key="t1",
                tenant_slug="my-garden",
                plant_keys=["missing"],
                fields=["name"],
            )

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_multiple_plants(
        self,
        mock_qr,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_site_repo,
        mock_print_engine,
    ):
        """Generates labels for multiple plants."""
        mock_qr.return_value = "data:image/png;base64,AAAA"

        plant1 = _make_plant_instance("p1", "sp1")
        plant2 = _make_plant_instance("p2", "sp1")
        plant2.plant_name = "Plant Two"
        mock_plant_repo.get_by_key.side_effect = lambda k: {"p1": plant1, "p2": plant2}.get(k)

        species = MagicMock()
        species.scientific_name = "Solanum lycopersicum"
        species.common_names = ["Tomate"]
        species.family_key = None
        mock_species_repo.get_by_key.return_value = species
        mock_species_repo.get_cultivar_by_key.return_value = None
        mock_site_repo.get_location_by_key.return_value = None
        mock_plant_repo.resolve_phase_name.return_value = ""

        service.generate_plant_labels_pdf(
            tenant_key="t1",
            tenant_slug="my-garden",
            plant_keys=["p1", "p2"],
            fields=["name"],
        )

        context = mock_print_engine.render_pdf.call_args[0][1]
        assert len(context["cards"]) == 2
        assert context["cards"][0]["name"] == "Test Plant"
        assert context["cards"][1]["name"] == "Plant Two"

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_species_cache_prevents_repeated_lookups(
        self,
        mock_qr,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_site_repo,
        mock_print_engine,
    ):
        """Species repo is only queried once for the same species_key."""
        mock_qr.return_value = "data:image/png;base64,AAAA"

        plant1 = _make_plant_instance("p1", "sp1")
        plant2 = _make_plant_instance("p2", "sp1")
        mock_plant_repo.get_by_key.side_effect = lambda k: {"p1": plant1, "p2": plant2}.get(k)

        species = MagicMock()
        species.scientific_name = "Test"
        species.common_names = []
        species.family_key = None
        mock_species_repo.get_by_key.return_value = species
        mock_species_repo.get_cultivar_by_key.return_value = None
        mock_site_repo.get_location_by_key.return_value = None
        mock_plant_repo.resolve_phase_name.return_value = ""

        service.generate_plant_labels_pdf(
            tenant_key="t1",
            tenant_slug="slug",
            plant_keys=["p1", "p2"],
            fields=["name"],
        )

        # Species should be looked up only once (cached)
        assert mock_species_repo.get_by_key.call_count == 1

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_single_layout(
        self,
        mock_qr,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_site_repo,
        mock_print_engine,
    ):
        """Layout parameter is passed through to the template context."""
        mock_qr.return_value = "data:image/png;base64,AAAA"

        plant = _make_plant_instance()
        mock_plant_repo.get_by_key.return_value = plant
        mock_species_repo.get_by_key.return_value = None
        mock_species_repo.get_cultivar_by_key.return_value = None
        mock_site_repo.get_location_by_key.return_value = None
        mock_plant_repo.resolve_phase_name.return_value = ""

        service.generate_plant_labels_pdf(
            tenant_key="t1",
            tenant_slug="slug",
            plant_keys=["p1"],
            fields=["name"],
            layout="single",
        )

        context = mock_print_engine.render_pdf.call_args[0][1]
        assert context["layout"] == "single"

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_english_locale_date_format(
        self,
        mock_qr,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_site_repo,
        mock_print_engine,
    ):
        """English locale uses ISO date format."""
        mock_qr.return_value = "data:image/png;base64,AAAA"

        plant = _make_plant_instance()
        mock_plant_repo.get_by_key.return_value = plant
        mock_species_repo.get_by_key.return_value = None
        mock_species_repo.get_cultivar_by_key.return_value = None
        mock_plant_repo.resolve_phase_name.return_value = ""

        service.generate_plant_labels_pdf(
            tenant_key="t1",
            tenant_slug="slug",
            plant_keys=["p1"],
            fields=["planted_date"],
            locale="en",
        )

        context = mock_print_engine.render_pdf.call_args[0][1]
        assert context["cards"][0]["planted_date"] == "2026-03-15"
        assert mock_print_engine.render_pdf.call_args[0][2] == "en"

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_german_locale_date_format(
        self,
        mock_qr,
        service,
        mock_plant_repo,
        mock_species_repo,
        mock_site_repo,
        mock_print_engine,
    ):
        """German locale uses DD.MM.YYYY date format."""
        mock_qr.return_value = "data:image/png;base64,AAAA"

        plant = _make_plant_instance()
        mock_plant_repo.get_by_key.return_value = plant
        mock_species_repo.get_by_key.return_value = None
        mock_species_repo.get_cultivar_by_key.return_value = None
        mock_plant_repo.resolve_phase_name.return_value = ""

        service.generate_plant_labels_pdf(
            tenant_key="t1",
            tenant_slug="slug",
            plant_keys=["p1"],
            fields=["planted_date"],
            locale="de",
        )

        context = mock_print_engine.render_pdf.call_args[0][1]
        assert context["cards"][0]["planted_date"] == "15.03.2026"


class TestPlantLabelsTenantIsolation:
    """#2899 related finding: the plant labels resolved a plant by key alone and printed a foreign tenant's plant."""

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_a_foreign_plant_is_not_found_and_nothing_is_rendered(
        self, mock_qr, service, mock_plant_repo, mock_print_engine
    ):
        mock_plant_repo.get_by_key.return_value = _make_plant_instance().model_copy(update={"tenant_key": "t2"})

        with pytest.raises(NotFoundError):
            service.generate_plant_labels_pdf(tenant_key="t1", tenant_slug="slug", plant_keys=["p1"], fields=["name"])

        mock_print_engine.render_pdf.assert_not_called()
        mock_qr.assert_not_called()

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_a_location_under_a_foreign_site_prints_no_name(
        self, mock_qr, service, mock_plant_repo, mock_species_repo, mock_site_repo, mock_print_engine
    ):
        mock_qr.return_value = "data:image/png;base64,AAAA"
        mock_plant_repo.get_by_key.return_value = _make_plant_instance()
        mock_species_repo.get_by_key.return_value = None
        mock_species_repo.get_cultivar_by_key.return_value = None
        mock_plant_repo.resolve_phase_name.return_value = ""
        mock_site_repo.get_location_by_key.return_value = Location(_key="loc1", name="Fremd", site_key="s2", area_m2=1)
        mock_site_repo.get_site_by_key.return_value = Site(_key="s2", tenant_key="t2", name="Fremde Site")

        service.generate_plant_labels_pdf(tenant_key="t1", tenant_slug="slug", plant_keys=["p1"], fields=["location"])

        assert mock_print_engine.render_pdf.call_args[0][1]["cards"][0]["location"] == ""


class _Types:
    def __init__(self, *types: LocationType) -> None:
        self._types = {t.key: t for t in types}

    def get_by_key(self, key):
        return self._types.get(key)


@pytest.fixture
def label_service(mock_site_repo, mock_print_engine) -> PrintService:
    """A print service with a bed type and a non-bed type; the site repo is the shared MagicMock."""
    return PrintService(
        nutrient_plan_service=MagicMock(),
        care_reminder_service=MagicMock(),
        fertilizer_repo=MagicMock(),
        plant_repo=MagicMock(),
        species_repo=MagicMock(),
        print_engine=mock_print_engine,
        site_repo=mock_site_repo,
        app_base_url="https://app.example.com/",
        location_type_repo=_Types(  # type: ignore[arg-type]
            LocationType(_key="raised_bed", name="Hochbeet", name_en="Raised bed", is_bed=True),
            LocationType(_key="room", name="Raum"),
        ),
    )


def _place(mock_site_repo, *, location_type_key: str = "raised_bed", area: float = 2.5, tenant: str = "t1") -> None:
    mock_site_repo.get_location_by_key.return_value = Location(
        _key="bed1", name="Beet Nord", site_key="s1", location_type_key=location_type_key, area_m2=area
    )
    mock_site_repo.get_site_by_key.return_value = Site(_key="s1", tenant_key=tenant, name="Garten")


class TestLocationLabelUrl:
    def test_a_bed_opens_in_field_mode_with_its_sheet(self):
        url = location_label_url("https://app.example.com/", site_key="s1", location_key="bed1", is_bed=True)

        assert url == "https://app.example.com/standorte/sites/s1/plan?mode=field&bed=bed1"

    def test_another_location_opens_its_page(self):
        url = location_label_url("https://app.example.com", site_key="s1", location_key="room1", is_bed=False)

        assert url == "https://app.example.com/standorte/locations/room1"

    def test_keys_cannot_add_a_segment_or_a_parameter(self):
        url = location_label_url("https://a.example", site_key="s/../x", location_key="b&mode=plan", is_bed=True)

        assert url == "https://a.example/standorte/sites/s%2F..%2Fx/plan?mode=field&bed=b%26mode%3Dplan"


class TestGenerateLocationLabelPdf:
    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_a_bed_label_carries_name_site_type_area_and_the_field_mode_qr(
        self, mock_qr, label_service, mock_site_repo, mock_print_engine
    ):
        mock_qr.return_value = "data:image/png;base64,AAAA"
        _place(mock_site_repo)

        result = label_service.generate_location_label_pdf("bed1", tenant_key="t1", locale="de")

        assert result == b"%PDF-1.7 mock content"
        url = "https://app.example.com/standorte/sites/s1/plan?mode=field&bed=bed1"
        mock_qr.assert_called_once_with(url, LOCATION_LABEL_QR_DEFAULT_MM)
        template, context, locale = mock_print_engine.render_pdf.call_args[0]
        assert (template, locale) == ("location_label.html", "de")
        label = context["label"]
        assert label["name"] == "Beet Nord" and label["site_name"] == "Garten" and label["type_name"] == "Hochbeet"
        assert label["area"] == "2,5" and label["qr_url"] == url
        assert (label["title_key"], label["hint_key"], label["qr_alt_key"]) == (
            "location_label_title",
            "location_label_scan_hint",
            "location_label_qr_alt",
        )

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_english_uses_the_english_type_name_and_a_point(
        self, mock_qr, label_service, mock_site_repo, mock_print_engine
    ):
        mock_qr.return_value = "data:image/png;base64,AAAA"
        _place(mock_site_repo)

        label_service.generate_location_label_pdf("bed1", tenant_key="t1", qr_size_mm=30, locale="en")

        label = mock_print_engine.render_pdf.call_args[0][1]["label"]
        assert label["type_name"] == "Raised bed" and label["area"] == "2.5"
        assert mock_qr.call_args[0][1] == 30

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_a_non_bed_without_area_links_its_page_and_prints_no_area(
        self, mock_qr, label_service, mock_site_repo, mock_print_engine
    ):
        mock_qr.return_value = "data:image/png;base64,AAAA"
        _place(mock_site_repo, location_type_key="room", area=0)

        label_service.generate_location_label_pdf("bed1", tenant_key="t1")

        label = mock_print_engine.render_pdf.call_args[0][1]["label"]
        assert label["qr_url"] == "https://app.example.com/standorte/locations/bed1"
        assert label["area"] == "" and label["title_key"] == "location_label_title_location"

    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_an_unknown_type_shows_the_raw_key_and_is_no_bed(
        self, mock_qr, label_service, mock_site_repo, mock_print_engine
    ):
        mock_qr.return_value = "data:image/png;base64,AAAA"
        _place(mock_site_repo, location_type_key="custom_thing")

        label_service.generate_location_label_pdf("bed1", tenant_key="t1")

        label = mock_print_engine.render_pdf.call_args[0][1]["label"]
        assert label["type_name"] == "custom_thing"
        assert label["qr_url"].endswith("/standorte/locations/bed1")

    @pytest.mark.parametrize("case", ["foreign_site", "absent_location", "absent_site", "empty_tenant"])
    @patch("app.domain.services.print_service.PrintEngine.generate_qr_code_base64")
    def test_every_refusal_is_the_same_not_found(self, mock_qr, case, label_service, mock_site_repo, mock_print_engine):
        _place(mock_site_repo, tenant="t2" if case == "foreign_site" else "t1")
        if case == "absent_location":
            mock_site_repo.get_location_by_key.return_value = None
        if case == "absent_site":
            mock_site_repo.get_site_by_key.return_value = None
        tenant = "" if case == "empty_tenant" else "t1"

        with pytest.raises(NotFoundError) as raised:
            label_service.generate_location_label_pdf("bed1", tenant_key=tenant)

        assert "Location" in str(raised.value) and "Garten" not in str(raised.value)
        mock_qr.assert_not_called()
        mock_print_engine.render_pdf.assert_not_called()

    def test_without_a_site_repository_it_refuses(self, mock_print_engine):
        bare = PrintService(
            nutrient_plan_service=MagicMock(),
            care_reminder_service=MagicMock(),
            fertilizer_repo=MagicMock(),
            plant_repo=MagicMock(),
            species_repo=MagicMock(),
            print_engine=mock_print_engine,
        )

        with pytest.raises(NotFoundError):
            bare.generate_location_label_pdf("bed1", tenant_key="t1")
