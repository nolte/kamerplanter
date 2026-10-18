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
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import OpenerDirector, Request, url2pathname

import pytest

from app.common.enums import BedStatus, GardenObjectType, SunExposure
from app.common.exceptions import NotFoundError, PlanError
from app.domain.engines.plan_svg_engine import PlanOrientation, PlanPaper, PlanSvgLayer, PlanSvgOptions
from app.domain.engines.print_engine import TEMPLATES_DIR, PrintEngine
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import PlantShortInfo
from app.domain.models.site import SitePlan, Slot
from app.domain.services.garden_plan_export_service import GardenPlanExportService, safe_filename_part
from app.domain.services.garden_plan_service import GardenPlanService
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
