"""REQ-053 WP 5.2 (#2431) — the export service: JSON backup, SVG, PDF.

* **GP-ACC-030** — a 10 × 6 m plan with three beds, A4 landscape, ``scale=auto``: a PDF within 5 s, scale 1:50,
  a 2 × 1 m bed measures 40 × 20 mm *in the SVG that is embedded in the PDF*, scale bar, north arrow and legend.
* **GP-ACC-045** — a bed named ``"><image href="http://169.254.169.254/"/>`` (or ``file:///etc/passwd``) yields no
  ``<image>`` element and the name as escaped text, and the print engine's fetcher is asked for nothing but
  ``data:`` URIs, while the opener underneath is never reached for anything else.
* **Cross-tenant** — every method answers a foreign site like an absent one, before any document is read.
* **SR-024** — the PDF carries no notes, coordinates or account references; the JSON backup no plants, tasks,
  events or ``*_by``.
"""

from __future__ import annotations

import base64
import json
import re
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from time import perf_counter
from types import SimpleNamespace
from urllib.parse import urlsplit
from urllib.request import OpenerDirector, Request, url2pathname

import pytest

from app.common.enums import BedStatus, GardenObjectType, SunExposure
from app.common.exceptions import NotFoundError, PlanError
from app.domain.calculators.plant_state_calculator import OpenTask
from app.domain.engines.plan_svg_engine import (
    PLANT_COUNTER_THRESHOLD,
    PlanOrientation,
    PlanPaper,
    PlanSvgLayer,
    PlanSvgOptions,
)
from app.domain.engines.print_engine import TEMPLATES_DIR, PrintEngine
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, PlantStateSource
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import PlantShortInfo
from app.domain.models.site import SitePlan, Slot
from app.domain.services.garden_plan_export_service import (
    STATE_PAGE_SIZE,
    GardenPlanExportService,
    safe_filename_part,
)
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.plant_state_service import PlantStateService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

HOSTILE_IMAGE_NAME = '"><image href="http://169.254.169.254/"/>'
HOSTILE_FILE_NAME = "file:///etc/passwd"
SVG = "{http://www.w3.org/2000/svg}"
FOREIGN_SITE = "site_foreign"


def _service(repo: FakePlanRepo, engine: PrintEngine | None = None) -> GardenPlanExportService:
    return GardenPlanExportService(repo._sites, repo, GardenPlanService(repo._sites, repo), engine)


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0},
        plan_revision=7,
        plan_updated_by="u_secret_account",
    )
    site.gps_coordinates = (52.52, 13.405)
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": FOREIGN_SITE})
    repository = FakePlanRepo(FakeSites(site, foreign))
    repository.locations["b1"] = make_location(
        "b1", "Beet 1", geometry=rect(1, 1, 2, 1), notes="Frau Müller, Parzelle 7"
    )
    repository.locations["b2"] = make_location("b2", "Beet 2", geometry=rect(4, 1, 2, 1))
    repository.locations["b3"] = make_location(
        "b3", "Beet 3", geometry=rect(7, 1, 2, 1), sun_exposure=SunExposure.FULL_SUN
    )
    return repository


def _options(**kwargs) -> PlanSvgOptions:
    return PlanSvgOptions(**kwargs)


def _embedded_svg(html: str) -> ET.Element:
    (uri,) = re.findall(r'src="(data:image/svg\+xml;base64,[A-Za-z0-9+/=]+)"', html)
    return ET.fromstring(base64.b64decode(uri.split(",", 1)[1]))


class _CapturingEngine(PrintEngine):
    """The production engine, plus a record of the HTML it rendered and of every URL WeasyPrint asked it for."""

    def __init__(self) -> None:
        super().__init__()
        self.html: list[str] = []
        self.fetched: list[str] = []
        original = self.url_fetcher.fetch

        def spy(url, headers=None):
            self.fetched.append(url)
            return original(url, headers)

        self.url_fetcher.fetch = spy  # type: ignore[method-assign]

    def render_html(self, template_name, context, locale="de"):
        html = super().render_html(template_name, context, locale)
        self.html.append(html)
        return html


@pytest.fixture
def opener_calls(monkeypatch, tmp_path) -> list[str]:
    """Every URL that reaches ``OpenerDirector.open`` — the method every real fetch funnels through.

    ``data:`` URIs and files below the template tree are served for real (the page CSS, fonts); anything else is
    answered with an ``OSError``, so a regression can never turn this test into a live request or a file read.
    """
    calls: list[str] = []
    original = OpenerDirector.open

    def serves(full_url: str) -> bool:
        if full_url.startswith("data:"):
            return True
        if full_url.startswith("file:"):
            return url2pathname(urlsplit(full_url).path).startswith(str(TEMPLATES_DIR))
        return False

    def spy(self, url, data=None, timeout=None):
        full_url = url.full_url if isinstance(url, Request) else url
        calls.append(full_url)
        if not serves(full_url):
            raise OSError("access blocked by test harness")
        return original(self, url, data, timeout)

    monkeypatch.setattr(OpenerDirector, "open", spy)
    return calls


class TestGpAcc030:
    def test_the_pdf_is_rendered_within_five_seconds_at_one_to_fifty(self, repo) -> None:
        engine = _CapturingEngine()
        service = _service(repo, engine)

        started = perf_counter()
        pdf = service.render_pdf(
            SITE,
            tenant_key=TENANT,
            options=_options(paper=PlanPaper.A4, orientation=PlanOrientation.LANDSCAPE),
        )
        elapsed = perf_counter() - started

        assert pdf.content[:5] == b"%PDF-"
        assert elapsed <= 5.0, f"the PDF took {elapsed:.2f} s"
        assert pdf.scale == 50 and pdf.suggest_a3 is False
        assert pdf.filename == f"garden-plan-{SITE}.pdf"

    def test_a_two_by_one_metre_bed_measures_forty_by_twenty_millimetres_in_the_embedded_svg(self, repo) -> None:
        engine = _CapturingEngine()
        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options())

        root = _embedded_svg(engine.html[-1])
        scale = int(root.attrib["data-scale"])
        (bed,) = [e for e in root.iter(f"{SVG}polygon") if e.attrib.get("data-key") == "b1"]
        pairs = [tuple(float(v) for v in pair.split(",")) for pair in bed.attrib["points"].split()]
        width = (max(p[0] for p in pairs) - min(p[0] for p in pairs)) / scale
        height = (max(p[1] for p in pairs) - min(p[1] for p in pairs)) / scale
        assert (width, height) == (pytest.approx(40.0, abs=0.5), pytest.approx(20.0, abs=0.5))
        ids = {e.attrib.get("id") for e in root.iter()}
        assert {"scale-bar", "north-arrow", "legend"} <= ids

    def test_the_title_block_names_the_scale_the_paper_and_the_revision(self, repo) -> None:
        engine = _CapturingEngine()
        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(locale="en"))

        html = engine.html[-1]
        assert "1:50" in html and "A4 landscape" in html and "Garden plan" in html

    def test_a_page_that_cannot_hold_the_plan_is_refused_and_nothing_is_rendered(self, repo, monkeypatch) -> None:
        engine = _CapturingEngine()
        rendered: list[str] = []
        monkeypatch.setattr(engine, "render_pdf", lambda *a, **k: rendered.append("pdf"))
        repo._sites.sites[SITE].plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 28, "length_m": 20, "rotation_deg": 0},
            plan_revision=1,
        )

        with pytest.raises(PlanError) as excinfo:
            _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(scale=20))

        assert excinfo.value.status_code == 422 and excinfo.value.error_code == "plan.does_not_fit"
        assert rendered == []

    def test_a_large_garden_asks_for_a3_instead_of_failing(self, repo) -> None:
        repo._sites.sites[SITE].plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 50, "length_m": 36, "rotation_deg": 0},
            plan_revision=1,
        )

        pdf = _service(repo).render_pdf(SITE, tenant_key=TENANT, options=_options())

        assert pdf.suggest_a3 is True and pdf.scale > 200

    def test_a3_portrait_is_honoured(self, repo) -> None:
        engine = _CapturingEngine()
        _service(repo, engine).render_pdf(
            SITE, tenant_key=TENANT, options=_options(paper=PlanPaper.A3, orientation=PlanOrientation.PORTRAIT)
        )

        assert "A3 portrait" in engine.html[-1]


class TestGpAcc045:
    @pytest.mark.parametrize("hostile", [HOSTILE_IMAGE_NAME, HOSTILE_FILE_NAME])
    def test_the_svg_has_no_image_element_and_the_name_as_text(self, repo, hostile) -> None:
        repo.locations["b1"] = make_location("b1", hostile, geometry=rect(1, 1, 2, 1))

        rendered = _service(repo).render_svg(SITE, tenant_key=TENANT, options=_options())

        root = ET.fromstring(rendered.svg)
        assert not list(root.iter(f"{SVG}image"))
        assert hostile in [e.text for e in root.iter(f"{SVG}title")]
        assert "<image" not in rendered.svg

    @pytest.mark.parametrize("hostile", [HOSTILE_IMAGE_NAME, HOSTILE_FILE_NAME])
    def test_the_pdf_fetches_nothing_but_data_uris(self, repo, opener_calls, hostile) -> None:
        repo.locations["b1"] = make_location("b1", hostile, geometry=rect(1, 1, 2, 1))
        engine = _CapturingEngine()

        pdf = _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(), bed_list=True)

        assert pdf.content[:5] == b"%PDF-"
        html = engine.html[-1]
        assert "<image" not in html and re.search(r"""(src|href)\s*=\s*["']?file:""", html) is None
        assert engine.fetched, "the spy must sit on the fetcher WeasyPrint really uses"
        assert all(url.startswith("data:") for url in engine.fetched), engine.fetched
        assert all(url.startswith("data:") for url in opener_calls), opener_calls
        # The embedded SVG is the one place the name sits as markup context: it is escaped there too.
        embedded = _embedded_svg(html)
        assert not list(embedded.iter(f"{SVG}image"))

    def test_the_bed_list_escapes_the_name_into_text(self, repo) -> None:
        repo.locations["b1"] = make_location("b1", HOSTILE_IMAGE_NAME, geometry=rect(1, 1, 2, 1))
        engine = _CapturingEngine()

        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(), bed_list=True)

        assert "&#34;&gt;&lt;image href=&#34;http://169.254.169.254/&#34;/&gt;" in engine.html[-1]


class TestNoPersonalDataByDefault:
    """GP-FR-142 / SR-024: no notes, no coordinates, no account references on paper."""

    def test_the_pdf_html_and_the_embedded_svg_carry_none_of_them(self, repo) -> None:
        engine = _CapturingEngine()

        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(), bed_list=True)

        html = engine.html[-1]
        embedded = ET.tostring(_embedded_svg(html), encoding="unicode")
        for secret in ("Frau Müller", "Parzelle 7", "52.52", "13.405", "u_secret_account", "u_sabine"):
            assert secret not in html
            assert secret not in embedded

    def test_the_bed_list_names_placed_beds_only_sorted_with_localised_labels(self, repo) -> None:
        repo.locations["unplaced"] = make_location("unplaced", "Zelt ohne Platz")
        repo.locations["b2"] = make_location("b2", "alpha", geometry=rect(4, 1, 2, 1), bed_status=BedStatus.PLANNED)
        engine = _CapturingEngine()

        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(), bed_list=True)

        html = engine.html[-1]
        assert "Zelt ohne Platz" not in html
        assert html.index("alpha") < html.index("Beet 1") < html.index("Beet 3")
        assert "geplant" in html and "Vollsonne" in html

    def test_without_the_bed_list_there_is_no_second_page(self, repo) -> None:
        engine = _CapturingEngine()

        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options())

        assert "bed-list" in engine.html[-1] and "<section" not in engine.html[-1]


class TestCrossTenant:
    """Every method resolves the site through the tenant anchor before it reads a document of it."""

    @pytest.fixture
    def reads(self, repo, monkeypatch) -> list[str]:
        seen: list[str] = []
        original = repo.load_read_model

        def spy(site_key, **kwargs):
            seen.append(site_key)
            return original(site_key, **kwargs)

        monkeypatch.setattr(repo, "load_read_model", spy)
        return seen

    @pytest.mark.parametrize("method", ["export_json", "render_svg", "render_pdf"])
    def test_a_foreign_site_is_not_found_and_nothing_is_read(self, repo, reads, method) -> None:
        service = _service(repo)
        kwargs = {"options": _options()} if method != "export_json" else {}

        with pytest.raises(NotFoundError):
            getattr(service, method)(FOREIGN_SITE, tenant_key=TENANT, **kwargs)
        with pytest.raises(NotFoundError):
            getattr(service, method)(SITE, tenant_key=OTHER_TENANT, **kwargs)

        assert reads == []

    @pytest.mark.parametrize("method", ["export_json", "render_svg", "render_pdf"])
    def test_an_absent_site_answers_the_same_as_a_foreign_one(self, repo, method) -> None:
        service = _service(repo)
        kwargs = {"options": _options()} if method != "export_json" else {}

        with pytest.raises(NotFoundError) as foreign:
            getattr(service, method)(FOREIGN_SITE, tenant_key=TENANT, **kwargs)
        with pytest.raises(NotFoundError) as absent:
            getattr(service, method)("site_nobody", tenant_key=TENANT, **kwargs)

        assert foreign.value.status_code == absent.value.status_code == 404
        assert str(foreign.value).replace(FOREIGN_SITE, "X") == str(absent.value).replace("site_nobody", "X")

    @pytest.mark.parametrize("method", ["export_json", "render_svg", "render_pdf"])
    def test_an_empty_tenant_key_resolves_nothing(self, repo, method) -> None:
        kwargs = {"options": _options()} if method != "export_json" else {}

        with pytest.raises(NotFoundError):
            getattr(_service(repo), method)(SITE, tenant_key="", **kwargs)


class TestJsonExport:
    def _populate(self, repo: FakePlanRepo) -> None:
        repo.objects["o1"] = GardenObject(
            _key="o1",
            site_key=SITE,
            object_type=GardenObjectType.TREE,
            label="Apfel",
            geometry={"kind": "circle", "origin": [8, 4], "radius_m": 0.8},
            props={"crown_radius_m": 0.8, "species_label": "Malus"},
            created_by="u_secret_account",
        )
        repo.slots = [
            Slot(
                _key="s1",
                slot_id="B1_A1",
                location_key="b1",
                geometry={"kind": "point", "origin": [-0.5, 0.2]},
                currently_occupied=True,
            ),
            Slot(_key="s_old", slot_id="B1_A2", location_key="b1", archived_at="2026-01-01T00:00:00Z"),
        ]
        repo.plants = [PlantShortInfo(key="p1", instance_id="p1", species_key="sp", slot_key="s1", location_key="b1")]

    def test_it_holds_the_structure_with_schema_version_one(self, repo) -> None:
        self._populate(repo)

        export = _service(repo).export_json(SITE, tenant_key=TENANT)
        document = json.loads(export.model_dump_json())

        assert document["schema_version"] == "1"
        assert document["site"] == {"name": "Garten", "type": "outdoor"}
        assert document["plan"]["boundary"]["kind"] == "rect"
        assert {loc["key"] for loc in document["locations"]} == {"b1", "b2", "b3"}
        assert [slot["key"] for slot in document["slots"]] == ["s1"], "an archived slot is not part of the plan"
        assert document["slots"][0]["geometry"]["origin"] == [-0.5, 0.2], "slots stay in the bed frame"
        assert document["garden_objects"][0]["props"]["species_label"] == "Malus"

    def test_a_backup_keeps_the_notes_it_has_to_restore(self, repo) -> None:
        document = json.loads(_service(repo).export_json(SITE, tenant_key=TENANT).model_dump_json())

        notes = {loc["key"]: loc["notes"] for loc in document["locations"]}
        assert notes["b1"] == "Frau Müller, Parzelle 7"

    def test_no_plants_tasks_events_or_account_references(self, repo) -> None:
        self._populate(repo)

        document = json.loads(_service(repo).export_json(SITE, tenant_key=TENANT).model_dump_json())

        names = _all_keys(document)
        assert not {"plants", "tasks", "events", "care_events", "photos", "tenant_key", "gps_coordinates"} & names
        assert not [n for n in names if n.endswith(("_by", "_user_key"))], names
        text = json.dumps(document)
        assert "u_secret_account" not in text and "52.52" not in text and "u_sabine" not in text

    def test_the_export_is_a_pure_read(self, repo) -> None:
        self._populate(repo)

        _service(repo).export_json(SITE, tenant_key=TENANT)

        assert repo.applied == [] and repo.field_updates == []


def _all_keys(node) -> set[str]:
    if isinstance(node, dict):
        return set(node) | set().union(*(_all_keys(v) for v in node.values()), set())
    if isinstance(node, list):
        return set().union(*(_all_keys(v) for v in node), set())
    return set()


class TestLayerSelection:
    def test_plants_are_only_read_when_their_layer_is_on(self, repo, monkeypatch) -> None:
        seen: list[bool] = []
        original = repo.load_read_model

        def spy(site_key, **kwargs):
            seen.append(kwargs["include_plants"])
            return original(site_key, **kwargs)

        monkeypatch.setattr(repo, "load_read_model", spy)
        service = _service(repo)

        service.render_svg(SITE, tenant_key=TENANT, options=_options(layers=frozenset({PlanSvgLayer.BEDS})))
        service.render_svg(SITE, tenant_key=TENANT, options=_options(layers=frozenset({PlanSvgLayer.PLANTS})))

        assert seen == [False, True]


class TestFilename:
    @pytest.mark.parametrize(("key", "expected"), [("site_1", "site_1"), ('a"b\r\nX: y', "a_b__X__y"), ("", "plan")])
    def test_a_key_becomes_a_header_safe_fragment(self, key, expected) -> None:
        assert safe_filename_part(key) == expected


class TestBedListAndPage:
    def test_the_bed_list_names_beds_not_areas(self, repo) -> None:
        repo.locations["gh"] = make_location(
            "gh", "Gewächshaus", geometry=rect(0.5, 3, 5, 2), location_type_key="greenhouse"
        )
        engine = _CapturingEngine()

        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(), bed_list=True)

        table = engine.html[-1].split("<tbody>")[1]
        assert "Beet 1" in table and "Gewächshaus" not in table

    def test_the_generic_header_and_the_german_page_counter_are_switched_off(self, repo) -> None:
        engine = _CapturingEngine()

        _service(repo, engine).render_pdf(SITE, tenant_key=TENANT, options=_options(locale="en"))

        html = engine.html[-1]
        assert (
            "@bottom-center { content: none; }" in html.split("{% block")[0]
            or "content: none" in html.split("@page")[-1]
        )


# ── Plant states and phase colours in the print (#2489) ───────────────────────

STATE_NOW = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)


class _StateRows(IPlantStateRepository):
    """The plant-state source as a recording double: rows per bed, windowed like the real read."""

    def __init__(self, rows: dict[str, list[PlantStateSource]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, str, int, int]] = []

    def list_bed_plants(self, location_key, *, tenant_key, now, offset, limit):
        self.calls.append((location_key, tenant_key, offset, limit))
        return self.rows.get(location_key, [])[offset : offset + limit]


class _Phases:
    """The growth-phase lookup the export reads names from; counts the reads per key."""

    def __init__(self, names: dict[str, str]) -> None:
        self.names = names
        self.reads: list[str] = []

    def get_phase_by_key(self, key):
        self.reads.append(key)
        name = self.names.get(key)
        return None if name is None else SimpleNamespace(key=key, name=name)


def _source(plant_key: str, phase_key: str | None = "ph-flower", **overrides) -> PlantStateSource:
    fields = {
        "plant_key": plant_key,
        "instance_id": plant_key.upper(),
        "species_key": "tomato",
        "planted_on": date(2026, 4, 1),
        "phase_key": phase_key,
        "phase_started_on": date(2026, 5, 20),
        "phase_typical_days": 60,
    }
    fields.update(overrides)
    return PlantStateSource(**fields)


def _stated_world(repo: FakePlanRepo, per_bed: dict[str, list[PlantStateSource]]):
    repo.plants = [
        PlantShortInfo(
            key=row.plant_key,
            instance_id=row.instance_id,
            species_key="tomato",
            location_key=bed,
            phase_key=row.phase_key,
        )
        for bed, rows in per_bed.items()
        for row in rows
    ]
    states = _StateRows(per_bed)
    phases = _Phases({"ph-flower": "flowering", "ph-veg": "vegetative"})
    service = GardenPlanExportService(
        repo._sites,
        repo,
        GardenPlanService(repo._sites, repo),
        _CapturingEngine(),
        plant_state_repo=states,
        phase_repo=phases,  # type: ignore[arg-type]
    )
    return service, states, phases


class TestPlantStateEnrichment:
    def test_phase_names_are_read_once_per_distinct_phase_key(self, repo) -> None:
        rows = {
            "b1": [_source("p1"), _source("p2"), _source("p3", "ph-veg")],
            "b2": [_source("p4"), _source("p5", "ph-veg"), _source("p6", "ph-entry")],
        }
        service, _states, phases = _stated_world(repo, rows)
        view = service._view(SITE, tenant_key=TENANT, options=_options())

        marks = service._plant_marks(view, tenant_key=TENANT, options=_options(), now=STATE_NOW)

        assert marks is not None
        assert sorted(phases.reads) == ["ph-entry", "ph-flower", "ph-veg"]
        # A key that is no growth phase (a phase-sequence entry) has no name, as on screen.
        assert dict(marks.phase_names) == {"ph-flower": "flowering", "ph-veg": "vegetative"}

    def test_the_states_equal_the_plant_state_service_for_the_same_plant(self, repo) -> None:
        """The point of the shared assembly: the PDF and ``GET /locations/{key}/plant-states`` agree (#2489)."""
        rows = {
            "b1": [
                _source(
                    "p1",
                    open_tasks=(OpenTask("watering", date(2026, 6, 10)), OpenTask("pruning", date(2026, 6, 9))),
                    open_finding_count=1,
                ),
                _source("p2", phase_allows_harvest=True, harvest_batch_count=2),
                _source("p3", None),
            ]
        }
        service, states, _phases = _stated_world(repo, rows)
        view = service._view(SITE, tenant_key=TENANT, options=_options())

        marks = service._plant_marks(view, tenant_key=TENANT, options=_options(), now=STATE_NOW)
        api = PlantStateService(repo._sites, states).list_plant_states(
            "b1", tenant_key=TENANT, limit=200, now=STATE_NOW
        )

        assert marks is not None
        assert {entry.source.plant_key: entry.state for entry in api} == dict(marks.states)
        assert marks.states["p1"].attention[0].reason == "problem"
        assert marks.states["p2"].lifecycle == "harvesting" and marks.states["p2"].harvest_ready is True

    def test_the_tenant_reaches_every_read_and_a_large_bed_is_read_in_bounded_pages(self, repo) -> None:
        rows = {"b1": [_source(f"p{i:04d}") for i in range(450)]}
        service, states, _phases = _stated_world(repo, rows)
        view = service._view(SITE, tenant_key=TENANT, options=_options())

        marks = service._plant_marks(view, tenant_key=TENANT, options=_options(), now=STATE_NOW)

        assert marks is not None and len(marks.states) == 450
        assert states.calls == [
            ("b1", TENANT, 0, STATE_PAGE_SIZE),
            ("b1", TENANT, 200, STATE_PAGE_SIZE),
            ("b1", TENANT, 400, STATE_PAGE_SIZE),
        ]

    def test_from_the_counter_threshold_on_nothing_is_read(self, repo) -> None:
        rows = {"b1": [_source(f"p{i:04d}") for i in range(PLANT_COUNTER_THRESHOLD)]}
        service, states, phases = _stated_world(repo, rows)

        svg = service.render_svg(SITE, tenant_key=TENANT, options=_options(), now=STATE_NOW)

        assert svg.plant_counters is True
        assert states.calls == [] and phases.reads == []

    def test_with_the_plants_layer_off_nothing_is_read(self, repo) -> None:
        service, states, phases = _stated_world(repo, {"b1": [_source("p1")]})

        service.render_svg(
            SITE, tenant_key=TENANT, options=_options(layers=frozenset({PlanSvgLayer.BEDS})), now=STATE_NOW
        )

        assert states.calls == [] and phases.reads == []

    def test_a_foreign_site_reads_no_plant_state(self, repo) -> None:
        service, states, phases = _stated_world(repo, {"b1": [_source("p1")]})

        with pytest.raises(NotFoundError):
            service.render_svg(FOREIGN_SITE, tenant_key=TENANT, options=_options(), now=STATE_NOW)

        assert states.calls == [] and phases.reads == []

    def test_the_svg_draws_the_phase_colour_and_names_the_phase_in_the_legend(self, repo) -> None:
        service, _states, _phases = _stated_world(repo, {"b1": [_source("p1"), _source("p2", "ph-veg")]})

        svg = service.render_svg(SITE, tenant_key=TENANT, options=_options(locale="en"), now=STATE_NOW)

        root = ET.fromstring(svg.svg)
        (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
        assert sorted(c.attrib["fill"] for c in layer.findall(f"{SVG}circle")) == ["#43A047", "#AB47BC"]
        (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
        texts = [e.text for e in legend.iter(f"{SVG}text")]
        assert {"Phase: Flowering", "Phase: Vegetative", "Ring: growing"} <= set(texts)

    def test_without_a_plant_state_source_the_plants_stay_uniform(self, repo) -> None:
        repo.plants = [PlantShortInfo(key="p1", instance_id="p1", species_key="sp", location_key="b1")]

        svg = _service(repo).render_svg(SITE, tenant_key=TENANT, options=_options(locale="en"))

        root = ET.fromstring(svg.svg)
        (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
        assert "Plant" in [e.text for e in legend.iter(f"{SVG}text")]


class TestStatedPdfBudget:
    def test_a_large_stated_plan_prints_within_five_seconds(self, repo) -> None:
        """GP-NFR-038 / GP-ACC-030 with states on: just below the counter threshold, every plant stated and badged."""
        reasons = [
            {"open_finding_count": 1},
            {"open_tasks": (OpenTask("watering", date(2026, 6, 10)),)},
            {"open_tasks": (OpenTask("pruning", date(2026, 6, 1)),)},
            {"phase_allows_harvest": True, "harvest_batch_count": 1},
            {},
        ]
        rows: dict[str, list[PlantStateSource]] = {"b1": [], "b2": [], "b3": []}
        for index in range(PLANT_COUNTER_THRESHOLD - 1):
            rows[("b1", "b2", "b3")[index % 3]].append(
                _source(f"p{index:04d}", ("ph-flower", "ph-veg")[index % 2], **reasons[index % len(reasons)])
            )
        service, states, phases = _stated_world(repo, rows)

        started = perf_counter()
        pdf = service.render_pdf(SITE, tenant_key=TENANT, options=_options(), now=STATE_NOW)
        elapsed = perf_counter() - started

        assert pdf.content[:5] == b"%PDF-"
        assert elapsed <= 5.0, f"the stated PDF took {elapsed:.2f} s"
        assert sorted(phases.reads) == ["ph-flower", "ph-veg"]
        assert {call[0] for call in states.calls} == {"b1", "b2", "b3"}
        root = _embedded_svg(service._print.html[-1])  # type: ignore[attr-defined]
        (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
        assert len(layer.findall(f"{SVG}circle")) == PLANT_COUNTER_THRESHOLD - 1
        assert len(layer.findall(f"{SVG}g")) > 0
