"""REQ-053 GP-NFR-029 (#2900), REQ-032 §8 — the garden-plan PDF is a tagged PDF with title and language.

Read from the bytes the service returns (``pypdf``), not from the HTML: the tags are written by WeasyPrint's
``pdf_tags`` step, which an HTML assertion cannot see. The structure tree is walked in document order, which is the
reading order a screen reader follows.
"""

from __future__ import annotations

import pytest

from app.domain.engines import print_engine
from app.domain.engines.plan_svg_engine import PlanSvgOptions
from app.domain.engines.print_engine import PrintEngine
from app.domain.models.site import SitePlan
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.garden_plan_fakes import SITE, TENANT, FakePlanRepo, FakeSites, make_location, make_site, rect
from tests.support.pdf_text import pdf_accessibility

HOSTILE = '"><image href="http://169.254.169.254/"/>'


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0}, plan_revision=2
    )
    repository = FakePlanRepo(FakeSites(site))
    repository.locations["b1"] = make_location("b1", "Beet 1", geometry=rect(1, 1, 2, 1))
    return repository


def _pdf(repo: FakePlanRepo, *, locale: str = "de", bed_list: bool = False) -> bytes:
    service = GardenPlanExportService(repo._sites, repo, GardenPlanService(repo._sites, repo), PrintEngine())
    return service.render_pdf(SITE, tenant_key=TENANT, options=PlanSvgOptions(locale=locale), bed_list=bed_list).content


class TestTheGardenPlanPdfIsTagged:
    def test_it_has_a_structure_tree_and_is_marked(self, repo) -> None:
        facts = pdf_accessibility(_pdf(repo))

        assert facts.tagged and facts.marked
        assert facts.structure[0][0] == "/Document"

    def test_it_names_its_title_and_language_and_the_viewer_shows_the_title(self, repo) -> None:
        facts = pdf_accessibility(_pdf(repo))

        assert facts.lang == "de"
        assert facts.title == "Gartenplan: Garten"
        assert facts.display_doc_title

    def test_the_english_export_says_so(self, repo) -> None:
        facts = pdf_accessibility(_pdf(repo, locale="en"))

        assert (facts.lang, facts.title) == ("en", "Garden plan: Garten")

    def test_the_reading_order_is_heading_then_plan_then_bed_list(self, repo) -> None:
        roles = [role for role, _alt in pdf_accessibility(_pdf(repo, bed_list=True)).structure]

        assert roles.index("/H1") < roles.index("/Figure") < roles.index("/H2") < roles.index("/Table")

    def test_the_plan_figure_carries_its_alternative_text(self, repo) -> None:
        figures = [alt for role, alt in pdf_accessibility(_pdf(repo)).structure if role == "/Figure"]

        assert figures == ["Gartenplan: Garten (Maßstab 1:50)"]

    def test_a_hostile_site_name_is_only_text_in_the_title_and_the_alternative_text(self, repo) -> None:
        repo._sites.sites[SITE].name = HOSTILE

        facts = pdf_accessibility(_pdf(repo))

        assert facts.title == f"Gartenplan: {HOSTILE}"
        assert [alt for role, alt in facts.structure if role == "/Figure"] == [f"Gartenplan: {HOSTILE} (Maßstab 1:50)"]


class TestEveryPrintPdfIsTagged:
    def test_the_engine_tags_by_default(self, tmp_path) -> None:
        """REQ-032 §8 asks it of every print PDF; the engine-wide switch keeps a new template from opting out."""
        (tmp_path / "t.html").write_text(
            '<!DOCTYPE html><html lang="{{ locale }}"><head><title>{{ title }}</title></head>'
            "<body><h1>{{ title }}</h1></body></html>"
        )

        facts = pdf_accessibility(PrintEngine(templates_dir=tmp_path).render_pdf("t.html", {"title": "Plan"}))

        assert print_engine.PDF_TAGS is True
        assert facts.tagged and facts.marked and facts.lang == "de" and facts.title == "Plan"
