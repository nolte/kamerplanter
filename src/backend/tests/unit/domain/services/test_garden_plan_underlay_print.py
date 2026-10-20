"""REQ-053 WP 7.14 (#2480) - the underlay on the printed plan: opt-in, geometry, ``data:`` URI only (GP-NFR-052 (f))."""

from __future__ import annotations

import base64
import re

import pytest

from app.common.enums import TenantRole
from app.domain.engines.plan_svg_engine import PlanFrame, PlanSvgOptions
from app.domain.engines.plan_underlay_engine import (
    PDF_MAX_EDGE_PX,
    UnderlayImage,
    UnderlayImageError,
    place_underlay,
    prepare_image,
)
from app.domain.engines.print_engine import PrintEngine
from app.domain.models.site import SitePlan
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_plan_underlay_service import GardenPlanUnderlayService
from tests.support.garden_plan_fakes import SITE, TENANT, FakePlanRepo, FakeSites, make_location, make_site, rect
from tests.support.underlay_fakes import FakeUnderlayAttachments, png_bytes
from tests.unit.domain.services.test_garden_plan_underlay_service import _underlay


class _Engine(PrintEngine):
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
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0}, plan_revision=3
    )
    repository = FakePlanRepo(FakeSites(site))
    repository.locations["b1"] = make_location("b1", "Beet 1", geometry=rect(1, 1, 2, 1))
    return repository


@pytest.fixture
async def stack(repo):
    attachments = FakeUnderlayAttachments()
    attachments.add("att_1", tenant_key=TENANT)
    underlay_service = GardenPlanUnderlayService(repo._sites, repo, attachments, attachments.as_service())  # type: ignore[arg-type]
    await underlay_service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay())
    engine = _Engine()
    export = GardenPlanExportService(
        repo._sites, repo, GardenPlanService(repo._sites, repo), engine, attachment_service=attachments.as_service()
    )
    return export, engine, attachments


class TestCalibrationGeometry:
    def test_two_points_400_px_apart_and_4_m_are_100_px_per_metre(self) -> None:
        underlay = _underlay()

        assert underlay.calibration.pixel_distance == pytest.approx(400.0)
        assert underlay.calibration.metres_per_pixel == pytest.approx(0.01)

    def test_the_picture_lands_where_the_plan_puts_its_origin(self) -> None:
        frame = PlanFrame(origin_x_m=-1.0, origin_y_m=7.0, shift_x_mm=3.0, scale=50)
        image = UnderlayImage(data_uri="data:image/jpeg;base64,AA==", width_px=800, height_px=400)

        placement = place_underlay(_underlay(origin=[1.0, 5.0], rotation_deg=30.0), image, frame)

        # (1 - -1) m = 2 m = 40 mm at 1:50, plus the 3 mm centring shift; (7 - 5) m = 40 mm down.
        assert (placement.left_mm, placement.top_mm) == (pytest.approx(43.0), pytest.approx(40.0))
        # 800 px * 0.01 m/px = 8 m = 160 mm at 1:50; 400 px = 4 m = 80 mm.
        assert (placement.width_mm, placement.height_mm) == (pytest.approx(160.0), pytest.approx(80.0))
        assert placement.rotation_css_deg == pytest.approx(-30.0)


class TestPrepareImage:
    def test_a_large_picture_is_shrunk_but_keeps_its_original_pixel_size_for_the_calibration(self) -> None:
        image = prepare_image(png_bytes(4800, 2400))

        assert (image.width_px, image.height_px) == (4800, 2400)
        header, _, payload = image.data_uri.partition(",")
        assert header == "data:image/jpeg;base64"
        from io import BytesIO

        from PIL import Image

        with Image.open(BytesIO(base64.b64decode(payload))) as decoded:
            assert max(decoded.size) == PDF_MAX_EDGE_PX

    def test_bytes_that_are_no_image_are_refused(self) -> None:
        with pytest.raises(UnderlayImageError):
            prepare_image(b"%PDF-1.7 not a picture")


class TestThePdf:
    async def test_without_the_option_there_is_no_picture(self, stack) -> None:
        export, engine, _ = stack

        export.render_pdf(SITE, tenant_key=TENANT, options=PlanSvgOptions())

        assert "plan-underlay" in engine.html[-1] and 'class="plan-underlay"' not in engine.html[-1]
        assert "data:image/jpeg" not in engine.html[-1]

    async def test_with_the_option_it_sits_under_the_plan_as_a_data_uri_and_nothing_else_is_fetched(
        self, stack
    ) -> None:
        export, engine, _ = stack

        picture = await export.load_underlay(SITE, tenant_key=TENANT)
        pdf = export.render_pdf(SITE, tenant_key=TENANT, options=PlanSvgOptions(), underlay=picture)

        html = engine.html[-1]
        assert pdf.content[:5] == b"%PDF-"
        assert html.index('class="plan-underlay"') < html.index('class="plan-figure"')
        assert re.search(r'class="plan-underlay" src="data:image/jpeg;base64,', html)
        assert engine.fetched and all(url.startswith("data:") for url in engine.fetched), engine.fetched

    async def test_a_picture_that_is_gone_prints_the_plan_without_it(self, stack) -> None:
        export, _, attachments = stack
        attachments.rows.clear()

        assert await export.load_underlay(SITE, tenant_key=TENANT) is None

    async def test_a_site_without_an_underlay_loads_none(self, stack, repo) -> None:
        export, _, _ = stack
        repo._sites.sites[SITE].plan = repo._sites.sites[SITE].plan.model_copy(update={"underlay": None})

        assert await export.load_underlay(SITE, tenant_key=TENANT) is None
