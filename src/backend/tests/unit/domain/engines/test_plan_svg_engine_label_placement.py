"""REQ-053 GP-UX-047 / GP-FR-003 (#2490) - the PDF writer places a name where the editor does.

The name of a bed sits at its label anchor (``label_anchor``, the shared ``label_anchor`` vectors): the pole of
inaccessibility of a polygon, the centre of a rect - never the area centroid, which for an L-shaped bed lies in the
notch, outside the bed. It is shortened to the room a centred label has there, not to the bounding-box width.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.domain.calculators.geometry_calculator import centroid, point_in_polygon
from app.domain.calculators.label_anchor_calculator import label_anchor
from app.domain.engines.plan_svg_engine import PDF_HEADER_MM, PlanSvgOptions, render_plan_svg
from app.domain.models.garden_plan import GardenPlanView
from app.domain.models.geometry import PolygonGeometry, parse_geometry
from app.domain.models.site import SitePlan
from tests.support.garden_plan_fakes import SITE, make_location, rect

SVG = "{http://www.w3.org/2000/svg}"
#: An L-shaped bed (concave, like the vectors' ``label-anchor-polygon-l-shape-pole-not-centroid``).
L_SHAPE = {"kind": "polygon", "points": [[2, 2], [8, 2], [8, 3.2], [3.2, 3.2], [3.2, 6], [2, 6]], "rotation_deg": 0}


def _view(*locations) -> GardenPlanView:
    return GardenPlanView(
        site_key=SITE,
        site_name="Garten",
        plan_revision=1,
        plan=SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 8, "rotation_deg": 0},
            plan_revision=1,
        ),
        locations=list(locations),
        garden_objects=[],
        slots=[],
        plants=[],
    )


def _label(svg: str, key: str) -> ET.Element:
    (found,) = [e for e in ET.fromstring(svg).iter(f"{SVG}text") if e.attrib.get("data-key") == key]
    return found


def _svg_point(rendered, x_m: float, y_m: float) -> tuple[float, float]:
    assert rendered.frame is not None
    x_mm, y_mm = rendered.frame.paper_point(x_m, y_m)
    return (x_mm * rendered.scale, y_mm * rendered.scale)


def test_an_l_shaped_bed_is_labelled_at_its_pole_not_at_its_centroid() -> None:
    rendered = render_plan_svg(
        _view(make_location("l", "Winkelbeet", geometry=L_SHAPE)), PlanSvgOptions(header_mm=PDF_HEADER_MM)
    )

    text = _label(rendered.svg, "l")
    drawn = (float(text.attrib["x"]), float(text.attrib["y"]))
    assert drawn == pytest.approx(_svg_point(rendered, 2.703, 2.703), abs=0.5)
    # the centroid this replaced lies in the notch - outside the bed the name belongs to
    geometry = parse_geometry(L_SHAPE)
    assert isinstance(geometry, PolygonGeometry)
    assert not point_in_polygon(centroid(geometry), geometry.points)
    assert drawn != pytest.approx(_svg_point(rendered, *centroid(geometry)), abs=0.5)


def test_a_rect_bed_keeps_its_centre() -> None:
    rendered = render_plan_svg(
        _view(make_location("r", "Beet", geometry=rect(1, 1, 4, 2))), PlanSvgOptions(header_mm=PDF_HEADER_MM)
    )

    text = _label(rendered.svg, "r")
    assert (float(text.attrib["x"]), float(text.attrib["y"])) == pytest.approx(_svg_point(rendered, 3, 2), abs=0.5)


def test_a_name_is_shortened_to_the_room_at_the_anchor_not_to_the_box() -> None:
    """The L-shape's box is 6 m wide, the centred label at its pole has 1.406 m: the name is cut to the smaller."""
    name = "Staudenbeet am Gartenzaun mit Rosen und Lavendel"
    rendered = render_plan_svg(
        _view(make_location("l", name, geometry=L_SHAPE)), PlanSvgOptions(header_mm=PDF_HEADER_MM)
    )

    shown = _label(rendered.svg, "l").text or ""
    room_mm = label_anchor(parse_geometry(L_SHAPE)).width_m * 1000.0 / rendered.scale
    box_mm = 6.0 * 1000.0 / rendered.scale
    glyph_mm = 2.8 * 0.55
    assert shown.endswith("…")
    assert len(shown) == max(3, int(room_mm / glyph_mm))
    assert len(shown) < int(box_mm / glyph_mm)
