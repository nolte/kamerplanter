"""REQ-053 WP 5.2 (#2431) — the plan SVG writer: scale, layout, allowlist and escaping.

GP-ACC-030 (the page maths, measured on the SVG that goes into the PDF) and GP-ACC-045 (a hostile bed name
becomes text, never an element) at the engine level; the PDF and the routes have their own files. Every
security assertion parses the output as XML rather than grepping it: a substring check passes on a document
whose parser sees an element the substring never spelled.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.common.enums import BedStatus, GardenObjectType, LampKind
from app.common.exceptions import PlanError
from app.domain.calculators.plant_state_calculator import (
    ATTENTION_PRIORITY,
    LIFECYCLES,
    AttentionCode,
    AttentionReason,
    Lifecycle,
    PlantVisualState,
)
from app.domain.engines import plan_svg_engine
from app.domain.engines.plan_svg_engine import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_ELEMENTS,
    PDF_HEADER_MM,
    PLANT_COUNTER_THRESHOLD,
    SCALE_STEPS,
    PlanOrientation,
    PlanPaper,
    PlanSvgLayer,
    PlanSvgOptions,
    PlantStateMarks,
    escape_attribute,
    escape_text,
    parse_scale,
    render_plan_svg,
)
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import GardenPlanView, PlanSlotView, PlantShortInfo
from app.domain.models.site import SitePlan
from tests.support.garden_plan_fakes import SITE, make_location, rect

SVG = "{http://www.w3.org/2000/svg}"
HOSTILE_IMAGE_NAME = '"><image href="http://169.254.169.254/"/>'
HOSTILE_FILE_NAME = "file:///etc/passwd"


def _boundary(width: float, length: float) -> dict:
    return {"kind": "rect", "origin": [0, 0], "width_m": width, "length_m": length, "rotation_deg": 0}


def _view(*, width: float = 10, length: float = 6, locations=(), objects=(), slots=(), plants=(), north: float = 0.0):
    return GardenPlanView(
        site_key=SITE,
        site_name="Garten",
        plan_revision=3,
        plan=SitePlan(boundary=_boundary(width, length), plan_revision=3, north_angle_deg=north),
        locations=list(locations),
        garden_objects=list(objects),
        slots=list(slots),
        plants=list(plants),
    )


def _three_beds(**names: str):
    return [
        make_location("b1", names.get("b1", "Beet 1"), geometry=rect(1, 1, 2, 1)),
        make_location("b2", names.get("b2", "Beet 2"), geometry=rect(4, 1, 2, 1)),
        make_location("b3", names.get("b3", "Beet 3"), geometry=rect(7, 1, 2, 1)),
    ]


def _parse(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def _tags(root: ET.Element) -> set[str]:
    return {element.tag.removeprefix(SVG) for element in root.iter()}


def _attribute_names(root: ET.Element) -> set[str]:
    return {name.removeprefix(SVG) for element in root.iter() for name in element.attrib}


def _by_key(root: ET.Element, key: str) -> ET.Element:
    (found,) = [
        element for element in root.iter() if element.attrib.get("data-key") == key and element.tag != f"{SVG}text"
    ]
    return found


def _extent_mm(points: str, scale: int) -> tuple[float, float]:
    pairs = [tuple(float(v) for v in pair.split(",")) for pair in points.split()]
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    return ((max(xs) - min(xs)) / scale, (max(ys) - min(ys)) / scale)


def _render(view: GardenPlanView, marks: PlantStateMarks | None = None, **options):
    return render_plan_svg(view, PlanSvgOptions(header_mm=PDF_HEADER_MM, **options), marks)


class TestScaleAndPageMaths:
    """GP-ACC-030: 10 × 6 m with three beds on A4 landscape → 1:50, a 2 × 1 m bed measures 40 × 20 mm."""

    def test_auto_picks_one_to_fifty_for_the_acceptance_garden(self) -> None:
        rendered = _render(_view(locations=_three_beds()))

        assert rendered.scale == 50
        assert rendered.fits is True
        assert rendered.suggest_a3 is False

    def test_a_bed_of_two_by_one_metres_measures_forty_by_twenty_millimetres(self) -> None:
        rendered = _render(_view(locations=_three_beds()))

        root = _parse(rendered.svg)
        width_mm, height_mm = _extent_mm(_by_key(root, "b1").attrib["points"], rendered.scale)
        assert width_mm == pytest.approx(40.0, abs=0.5)
        assert height_mm == pytest.approx(20.0, abs=0.5)

    def test_the_root_carries_the_paper_size_and_a_millimetre_viewbox(self) -> None:
        rendered = _render(_view(locations=_three_beds()))

        root = _parse(rendered.svg)
        view_w, view_h = (float(v) for v in root.attrib["viewBox"].split()[2:])
        assert root.attrib["width"] == f"{rendered.width_mm:.2f}mm"
        # 1 m = 1 000 units and the printed size is units / scale: the viewBox is the real-world millimetre canvas.
        assert view_w / rendered.scale == pytest.approx(rendered.width_mm, abs=0.01)
        assert view_h / rendered.scale == pytest.approx(rendered.height_mm, abs=0.01)
        assert root.attrib["data-scale"] == "50"

    def test_the_ten_metres_fit_the_277_millimetres_the_acceptance_names(self) -> None:
        rendered = _render(_view(locations=_three_beds()))

        assert rendered.width_mm <= 277.0
        assert rendered.height_mm <= 210.0 - 20.0 - PDF_HEADER_MM

    def test_scale_bar_north_arrow_and_legend_are_present(self) -> None:
        root = _parse(_render(_view(locations=_three_beds())).svg)

        ids = {element.attrib.get("id") for element in root.iter()}
        assert {"scale-bar", "north-arrow", "legend", "layer-boundary"} <= ids

    def test_the_scale_bar_is_as_long_as_it_says(self) -> None:
        rendered = _render(_view(locations=_three_beds()))
        root = _parse(rendered.svg)
        (bar,) = [e for e in root.iter() if e.attrib.get("id") == "scale-bar"]

        segments = [e for e in bar if e.tag == f"{SVG}rect"]
        total_units = sum(float(e.attrib["width"]) for e in segments)
        labels = [e.text for e in bar if e.tag == f"{SVG}text"]
        assert labels[-1] == "2 m"
        assert total_units == pytest.approx(2000.0)
        # 2 m at 1:50 is 40 mm on the paper.
        assert total_units / rendered.scale == pytest.approx(40.0)

    def test_the_north_arrow_turns_with_the_north_angle(self) -> None:
        root = _parse(_render(_view(locations=_three_beds(), north=90.0)).svg)

        (arrow,) = [e for e in root.iter() if e.attrib.get("id") == "north-arrow"]
        assert arrow.attrib["transform"].startswith("rotate(90 ")

    def test_a_28_by_20_metre_garden_lands_on_one_to_150_not_200(self) -> None:
        """The reason for the finer steps (F-15)."""
        rendered = _render(_view(width=28, length=20, locations=[make_location("b", geometry=rect(2, 2, 3, 1))]))

        assert rendered.scale == 150
        assert rendered.suggest_a3 is False

    def test_a_garden_that_needs_coarser_than_one_to_200_suggests_a3(self) -> None:
        rendered = _render(_view(width=50, length=36, locations=[make_location("b", geometry=rect(2, 2, 3, 1))]))

        assert rendered.scale > 200
        assert rendered.suggest_a3 is True

    def test_on_a3_the_same_garden_gets_a_finer_scale_and_no_suggestion(self) -> None:
        view = _view(width=50, length=36, locations=[make_location("b", geometry=rect(2, 2, 3, 1))])

        a4 = _render(view)
        a3 = _render(view, paper=PlanPaper.A3)

        assert a3.scale < a4.scale
        assert a3.suggest_a3 is False

    def test_portrait_swaps_the_page_axes(self) -> None:
        view = _view(width=6, length=10, locations=[make_location("b", geometry=rect(1, 1, 2, 1))])

        landscape = _render(view)
        portrait = _render(view, orientation=PlanOrientation.PORTRAIT)

        assert portrait.scale <= landscape.scale

    def test_a_fixed_scale_that_does_not_fit_is_reported_not_changed(self) -> None:
        rendered = _render(
            _view(width=28, length=20, locations=[make_location("b", geometry=rect(2, 2, 3, 1))]), scale=20
        )

        assert rendered.scale == 20
        assert rendered.fits is False

    def test_a_garden_larger_than_the_coarsest_step_is_reported_as_not_fitting(self) -> None:
        rendered = _render(_view(width=400, length=300, locations=[make_location("b", geometry=rect(2, 2, 3, 1))]))

        assert rendered.scale == SCALE_STEPS[-1]
        assert rendered.fits is False

    @pytest.mark.parametrize(("raw", "expected"), [("auto", None), ("1:50", 50), ("1:20", 20), ("1:500", 500)])
    def test_parse_scale(self, raw: str, expected: int | None) -> None:
        assert parse_scale(raw) == expected

    @pytest.mark.parametrize("raw", ["1:60", "2:50", "1:", "50", "1:1e2", "auto ", "1:50; x"])
    def test_parse_scale_refuses_anything_but_the_twelve_steps(self, raw: str) -> None:
        with pytest.raises(ValueError, match="scale"):
            parse_scale(raw)

    def test_the_twelve_steps_are_those_of_the_spec(self) -> None:
        assert SCALE_STEPS == (20, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500)

    def test_an_empty_plan_is_refused_with_its_published_code(self) -> None:
        empty = GardenPlanView(site_key=SITE, site_name="Garten", plan=SitePlan(plan_revision=1))

        with pytest.raises(PlanError) as excinfo:
            _render(empty)

        assert excinfo.value.status_code == 422
        assert excinfo.value.error_code == "plan.empty"

    def test_without_a_boundary_the_extent_is_that_of_the_placed_beds(self) -> None:
        view = GardenPlanView(site_key=SITE, site_name="Garten", locations=_three_beds())

        rendered = _render(view)

        assert rendered.scale <= 100


class TestAllowlistAndEscaping:
    """GP-NFR-052 (b), GP-ACC-045: only allowlisted elements and attributes, user text escaped for its context."""

    @pytest.mark.parametrize("hostile", [HOSTILE_IMAGE_NAME, HOSTILE_FILE_NAME])
    def test_a_hostile_bed_name_yields_no_image_element_and_survives_as_text(self, hostile: str) -> None:
        rendered = _render(_view(locations=_three_beds(b1=hostile)))

        root = _parse(rendered.svg)  # a name that broke the document would raise here
        assert "image" not in _tags(root)
        assert _tags(root) <= ALLOWED_ELEMENTS
        titles = [e.text for e in root.iter(f"{SVG}title")]
        assert hostile in titles, "the name must survive as text, not vanish"

    def test_the_hostile_markup_never_appears_unescaped_in_the_serialised_document(self) -> None:
        rendered = _render(_view(locations=_three_beds(b1=HOSTILE_IMAGE_NAME)))

        assert "<image" not in rendered.svg
        assert "&lt;image" in rendered.svg

    @pytest.mark.parametrize("hostile", [HOSTILE_IMAGE_NAME, HOSTILE_FILE_NAME, "<script>alert(1)</script>"])
    def test_no_attribute_is_a_reference_or_an_event_handler(self, hostile: str) -> None:
        objects = [
            GardenObject(
                _key="o1",
                site_key=SITE,
                object_type=GardenObjectType.OTHER,
                label=hostile,
                geometry={"kind": "rect", "origin": [8, 4], "width_m": 1, "length_m": 1, "rotation_deg": 0},
                props={},
            )
        ]
        root = _parse(_render(_view(locations=_three_beds(b2=hostile), objects=objects)).svg)

        names = _attribute_names(root)
        assert names <= ALLOWED_ATTRIBUTES
        assert not names & {"href", "xlink:href", "style", "onload", "onclick", "src"}
        assert "script" not in _tags(root)

    def test_the_document_has_no_url_function_anywhere(self) -> None:
        rendered = _render(_view(locations=_three_beds(b1=HOSTILE_FILE_NAME)), layers=frozenset(PlanSvgLayer))

        assert "url(" not in rendered.svg
        assert "javascript:" not in rendered.svg

    def test_characters_xml_cannot_carry_are_dropped_instead_of_breaking_the_document(self) -> None:
        rendered = _render(_view(locations=_three_beds(b1="Beet\x00\x01 mit\x1fSteuerzeichen\ud800")))

        root = _parse(rendered.svg)
        assert any(e.text == "Beet mitSteuerzeichen" for e in root.iter(f"{SVG}title"))

    def test_a_label_is_truncated_to_the_bed_it_labels(self) -> None:
        rendered = _render(_view(locations=_three_beds(b1="B" * 200)))

        root = _parse(rendered.svg)
        labels = [e.text for e in root.iter(f"{SVG}text") if e.attrib.get("data-key") == "b1"]
        assert len(labels) == 1 and len(labels[0]) < 40 and labels[0].endswith("…")

    def test_the_site_name_is_escaped_in_the_title_too(self) -> None:
        view = _view(locations=_three_beds()).model_copy(update={"site_name": HOSTILE_IMAGE_NAME})

        root = _parse(_render(view).svg)

        assert "image" not in _tags(root)
        assert [e.text for e in root.iter(f"{SVG}title")][0] == HOSTILE_IMAGE_NAME

    def test_the_node_refuses_an_element_off_the_allowlist(self) -> None:
        for tag in ("image", "foreignObject", "script", "use", "a", "style", "animate"):
            with pytest.raises(ValueError, match="allowlist"):
                plan_svg_engine._el(tag)

    def test_the_node_refuses_an_attribute_off_the_allowlist(self) -> None:
        for name in ("href", "xlink:href", "style", "onload", "src"):
            with pytest.raises(ValueError, match="allowlist"):
                plan_svg_engine._Node("rect", {name: "x"})

    @pytest.mark.parametrize("paint", ["url(#x)", "javascript:alert(1)", "red", "#12345", "#gggggg", "none; x"])
    def test_the_node_refuses_a_paint_that_is_not_a_hex_colour(self, paint: str) -> None:
        with pytest.raises(ValueError, match="paint"):
            plan_svg_engine._Node("rect", {"fill": paint})

    @pytest.mark.parametrize("accent", ["red", "#12345", "url(#x)", "#gg0000", "#2e7d32; x", ""])
    def test_the_engine_refuses_an_accent_that_is_not_a_hex_colour(self, accent: str) -> None:
        with pytest.raises(ValueError, match="accent"):
            _render(_view(locations=_three_beds()), accent=accent)

    def test_text_escaping(self) -> None:
        assert escape_text('a & <b> "c"') == 'a &amp; &lt;b&gt; "c"'

    def test_attribute_escaping_quotes_and_whitespace_controls(self) -> None:
        assert escape_attribute('"><x a="1"\n') == "&quot;&gt;&lt;x a=&quot;1&quot;&#10;"

    def test_every_tag_and_attribute_the_writer_emits_is_on_the_allowlist(self) -> None:
        """All layers on, with an object of every class: the output stays inside the lists."""
        objects = [
            GardenObject(
                _key=f"o{index}",
                site_key=SITE,
                object_type=object_type,
                label=object_type.value,
                geometry=_geometry_for(object_type),
                props=_props_for(object_type),
            )
            for index, object_type in enumerate(GardenObjectType)
        ]
        view = _view(
            locations=_three_beds(), objects=objects, slots=[_slot("s1", "b1", 1.5, 1.5)], plants=[_plant("p1", "s1")]
        )

        root = _parse(_render(view, layers=frozenset(PlanSvgLayer)).svg)

        drawn = {e.attrib["data-key"] for e in root.iter() if e.attrib.get("data-key", "").startswith("o")}
        assert drawn == {f"o{index}" for index in range(len(GardenObjectType))}, "every class must be drawn"
        assert _tags(root) <= ALLOWED_ELEMENTS
        assert _attribute_names(root) <= ALLOWED_ATTRIBUTES


_LINE = {"kind": "polyline", "points": [[0.5, 0.5], [9, 0.5]], "width_m": 0.3}


def _geometry_for(object_type: GardenObjectType) -> dict:
    if object_type in {
        GardenObjectType.PATH,
        GardenObjectType.WALL,
        GardenObjectType.FENCE,
        GardenObjectType.TRELLIS,
        GardenObjectType.WINDOW,
        GardenObjectType.DOOR,
    }:
        return _LINE
    if object_type in {GardenObjectType.TREE, GardenObjectType.SHRUB}:
        return {"kind": "circle", "origin": [5, 5], "radius_m": 0.8}
    if object_type in {GardenObjectType.WATER_SOURCE, GardenObjectType.LAMP}:
        return {"kind": "point", "origin": [8, 4]}
    return {"kind": "rect", "origin": [0.2, 4], "width_m": 1, "length_m": 1, "rotation_deg": 0}


def _props_for(object_type: GardenObjectType) -> dict:
    return {
        GardenObjectType.TREE: {"crown_radius_m": 0.8},
        GardenObjectType.TRELLIS: {"height_m": 1.5},
        GardenObjectType.WATER_SOURCE: {"water_source_kind": "tap"},
        GardenObjectType.LAMP: {"kind": next(iter(LampKind)).value, "height_m": 1.0},
    }.get(object_type, {})


def _slot(key: str, bed: str, x: float, y: float) -> PlanSlotView:
    return PlanSlotView(
        key=key,
        slot_id=key,
        location_key=bed,
        slot_role="position",
        capacity_plants=1,
        currently_occupied=True,
        plan_geometry={"kind": "point", "origin": [x, y]},
    )


def _plant(key: str, slot: str | None, bed: str | None = None) -> PlantShortInfo:
    return PlantShortInfo(key=key, instance_id=key, species_key="sp", slot_key=slot, location_key=bed)


class TestLayersAndLegend:
    def test_the_default_layers_draw_beds_objects_plants_and_labels_only(self) -> None:
        root = _parse(_render(_view(locations=_three_beds())).svg)

        ids = {e.attrib.get("id") for e in root.iter()}
        assert {"layer-beds", "layer-objects", "layer-plants", "layer-labels"} <= ids
        assert "layer-grid" not in ids and "layer-slots" not in ids

    def test_a_switched_off_layer_is_not_in_the_document(self) -> None:
        root = _parse(_render(_view(locations=_three_beds()), layers=frozenset({PlanSvgLayer.GRID})).svg)

        ids = {e.attrib.get("id") for e in root.iter()}
        assert "layer-grid" in ids
        assert not ids & {"layer-beds", "layer-objects", "layer-plants", "layer-labels"}
        # The boundary, scale bar, north arrow and legend are not layers.
        assert {"layer-boundary", "scale-bar", "north-arrow"} <= ids

    def test_the_grid_pitch_keeps_the_lines_at_least_five_millimetres_apart(self) -> None:
        rendered = _render(
            _view(width=28, length=20, locations=[make_location("b", geometry=rect(2, 2, 3, 1))]),
            layers=frozenset({PlanSvgLayer.GRID}),
        )

        root = _parse(rendered.svg)
        xs = sorted({float(e.attrib["x1"]) for e in root.iter(f"{SVG}line") if e.attrib["x1"] == e.attrib["x2"]})
        assert min(b - a for a, b in zip(xs, xs[1:], strict=False)) / rendered.scale >= 5.0

    def test_the_legend_lists_what_is_on_the_plan_and_only_that(self) -> None:
        beds = [
            make_location("b1", geometry=rect(1, 1, 2, 1)),
            make_location("b2", geometry=rect(4, 1, 2, 1), bed_status=BedStatus.PLANNED),
        ]
        objects = [
            GardenObject(
                _key="t",
                site_key=SITE,
                object_type=GardenObjectType.TREE,
                geometry={"kind": "circle", "origin": [8, 4], "radius_m": 0.8},
                props={"crown_radius_m": 0.8},
            )
        ]
        root = _parse(_render(_view(locations=beds, objects=objects), locale="en").svg)

        (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
        texts = [e.text for e in legend.iter(f"{SVG}text")]
        assert texts == ["Bed", "Bed (planned)", "Tree"]

    def test_the_legend_is_localised(self) -> None:
        root = _parse(_render(_view(locations=_three_beds()), locale="de").svg)

        (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
        assert [e.text for e in legend.iter(f"{SVG}text")] == ["Beet"]

    def test_objects_carry_their_key_as_data_key(self) -> None:
        objects = [
            GardenObject(
                _key="o9",
                site_key=SITE,
                object_type=GardenObjectType.BUILDING,
                geometry={"kind": "rect", "origin": [8, 4], "width_m": 1, "length_m": 1, "rotation_deg": 0},
                props={},
            )
        ]
        root = _parse(_render(_view(locations=_three_beds(), objects=objects)).svg)

        assert _by_key(root, "o9").tag == f"{SVG}polygon"

    def test_off_site_scenery_outside_the_extent_is_left_out(self) -> None:
        neighbour = GardenObject(
            _key="far",
            site_key=SITE,
            object_type=GardenObjectType.BUILDING,
            off_site=True,
            geometry={"kind": "rect", "origin": [100, 100], "width_m": 5, "length_m": 5, "rotation_deg": 0},
            props={},
        )
        root = _parse(_render(_view(locations=_three_beds(), objects=[neighbour])).svg)

        assert not [e for e in root.iter() if e.attrib.get("data-key") == "far"]


class TestPlants:
    """GP-NFR-038: one symbol per plant below 2 000, one counter per bed from 2 000 on."""

    def _crowded(self, count: int) -> GardenPlanView:
        beds = [make_location("b1", geometry=rect(1, 1, 4, 3))]
        plants = [_plant(f"p{i}", None, "b1") for i in range(count)]
        return _view(locations=beds, plants=plants)

    def test_below_the_threshold_every_plant_is_a_symbol(self) -> None:
        rendered = _render(self._crowded(PLANT_COUNTER_THRESHOLD - 1))

        root = _parse(rendered.svg)
        (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
        assert rendered.plant_counters is False
        assert len(layer.findall(f"{SVG}circle")) == PLANT_COUNTER_THRESHOLD - 1

    def test_from_the_threshold_on_a_bed_shows_one_counter_instead(self) -> None:
        rendered = _render(self._crowded(PLANT_COUNTER_THRESHOLD))

        root = _parse(rendered.svg)
        (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
        assert rendered.plant_counters is True
        assert len(layer.findall(f"{SVG}circle")) == 0
        (counter,) = layer.findall(f"{SVG}text")
        assert counter.text == str(PLANT_COUNTER_THRESHOLD)
        assert counter.attrib["data-key"] == "b1"

    def test_a_plant_in_a_slot_is_drawn_at_the_slot(self) -> None:
        beds = [make_location("b1", geometry=rect(1, 1, 4, 3))]
        view = _view(locations=beds, slots=[_slot("s1", "b1", 2.0, 2.0)], plants=[_plant("p1", "s1", "b1")])

        rendered = _render(view)

        root = _parse(rendered.svg)
        (marker,) = [
            e for e in root.iter(f"{SVG}circle") if e.attrib.get("fill") == "#1b5e20" and e.attrib.get("fill-opacity")
        ]
        # x(2.0) = (2.0 - origin_x) * 1000 + centring shift; compare against the bed's own corner instead.
        bed_points = _by_key(root, "b1").attrib["points"].split()
        left = float(bed_points[0].split(",")[0])
        assert float(marker.attrib["cx"]) - left == pytest.approx(1000.0)


class TestReviewFindings:
    def test_slotless_plants_stay_inside_the_bounding_box_of_their_bed(self) -> None:
        bed = make_location("b1", geometry=rect(1, 1, 2, 1))
        plants = [_plant(f"p{i}", None, "b1") for i in range(1500)]

        rendered = _render(_view(locations=[bed], plants=plants))

        root = _parse(rendered.svg)
        (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
        left = float(_by_key(root, "b1").attrib["points"].split()[0].split(",")[0])
        circles = layer.findall(f"{SVG}circle")
        assert len(circles) == 1500
        assert all(left <= float(c.attrib["cx"]) <= left + 2000 for c in circles)

    def test_a_bed_outside_the_boundary_is_inside_the_canvas(self) -> None:
        view = _view(locations=[make_location("out", geometry=rect(12, 1, 2, 1))])

        root = _parse(_render(view).svg)

        canvas_w = float(root.attrib["viewBox"].split()[2])
        points = _by_key(root, "out").attrib["points"].split()
        assert max(float(p.split(",")[0]) for p in points) <= canvas_w


# ── Plant states and phase colours (#2489, GP-UX-005/059/060) ────────────────


def _state(lifecycle: Lifecycle = "active", phase_key: str | None = "ph-flower", *badges: AttentionCode):
    return PlantVisualState(
        lifecycle=lifecycle,
        phase_key=phase_key,
        phase_progress=None,
        attention=tuple(AttentionReason(code, 1) for code in badges),
        harvest_ready="harvest" in badges,
        harvest_ready_from=None,
    )


_PHASES = {"ph-flower": "flowering", "ph-veg": "Vegetative", "ph-rest": "Dormancy"}


def _stated_view() -> tuple[GardenPlanView, PlantStateMarks]:
    """Five plants in one bed: three phases (one unknown name), two rings, three badges and one plant with no state."""
    beds = [make_location("b1", geometry=rect(1, 1, 4, 3))]
    plants = [
        PlantShortInfo(key=key, instance_id=key, species_key="sp", location_key="b1", phase_key=phase)
        for key, phase in (("p0", "ph-flower"), ("p1", "ph-veg"), ("p2", "ph-rest"), ("p3", "ph-veg"), ("p4", None))
    ]
    marks = PlantStateMarks(
        states={
            "p0": _state("active", "ph-flower", "problem", "water"),
            "p1": _state("harvesting", "ph-veg", "harvest"),
            "p2": _state("active", "ph-rest", "overdue"),
            "p3": _state("active", "ph-veg"),
        },
        phase_names=_PHASES,
    )
    return _view(locations=beds, plants=plants), marks


def _legend_texts(root: ET.Element) -> list[str | None]:
    (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
    return [e.text for e in legend.iter(f"{SVG}text")]


def _plant_layer(root: ET.Element) -> ET.Element:
    (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
    return layer


class TestPlantStates:
    """A stated plant is drawn like on screen: phase-coloured disc, lifecycle ring, at most one badge."""

    def test_the_disc_takes_the_phase_colour_and_the_ring_the_lifecycle(self) -> None:
        view, marks = _stated_view()

        layer = _plant_layer(_parse(_render(view, marks).svg))

        discs = layer.findall(f"{SVG}circle")
        assert [d.attrib["fill"] for d in discs] == ["#AB47BC", "#43A047", "#D4E157", "#43A047", "#1b5e20"]
        widths = [float(d.attrib.get("stroke-width", 0)) for d in discs[:4]]
        assert widths[1] > widths[0] == widths[2] == widths[3], "harvesting is the thick ring"
        assert "stroke" not in discs[4].attrib and discs[4].attrib["fill-opacity"] == "0.85", "no state: as before"

    def test_only_the_most_urgent_reason_is_drawn_as_a_badge(self) -> None:
        view, marks = _stated_view()

        layer = _plant_layer(_parse(_render(view, marks).svg))

        badges = [g for g in layer.findall(f"{SVG}g")]
        fills = [g.findall(f"{SVG}path")[0].attrib["fill"] for g in badges]
        # p0 has problem and water: problem wins (GP-UX-060); p3 has none.
        assert fills == ["#b84300", "#1b5e20", "#c62828"]
        assert all(len(g.findall(f"{SVG}path")) == 2 for g in badges)

    @pytest.mark.parametrize(
        ("lifecycle", "dashed", "disc"),
        [
            ("planned", True, "0.4"),
            ("sown", True, "0.4"),
            ("active", False, None),
            ("harvesting", False, None),
            ("failed", False, "none"),
            ("historic", True, "0.5"),
        ],
    )
    def test_every_lifecycle_has_its_ring(self, lifecycle: Lifecycle, dashed: bool, disc: str | None) -> None:
        view, _ = _stated_view()
        marks = PlantStateMarks(states={"p0": _state(lifecycle)}, phase_names=_PHASES)

        (first, *_rest) = _plant_layer(_parse(_render(view, marks).svg)).findall(f"{SVG}circle")

        assert ("stroke-dasharray" in first.attrib) is dashed
        if disc == "none":
            assert first.attrib["fill"] == "none"
        else:
            assert first.attrib.get("fill-opacity") == disc

    def test_a_phase_key_without_a_name_keeps_the_plant_colour_but_draws_the_ring(self) -> None:
        view, marks = _stated_view()
        marks = PlantStateMarks(states=marks.states, phase_names={})

        layer = _plant_layer(_parse(_render(view, marks).svg))

        discs = layer.findall(f"{SVG}circle")
        assert {d.attrib["fill"] for d in discs} == {"#1b5e20"}
        assert all(d.attrib.get("stroke") == "#212121" for d in discs[:4])

    def test_states_inside_the_allowlist_with_every_lifecycle_and_badge(self) -> None:
        """GP-NFR-052 (b): the stated markers, the badges and their legend use listed tags and attributes only."""
        beds = [make_location("b1", geometry=rect(1, 1, 4, 3))]
        keys = [f"p{i}" for i in range(len(LIFECYCLES) * len(ATTENTION_PRIORITY))]
        plants = [_plant(key, None, "b1") for key in keys]
        states = {
            key: _state(LIFECYCLES[i % len(LIFECYCLES)], "ph-x", ATTENTION_PRIORITY[i % len(ATTENTION_PRIORITY)])
            for i, key in enumerate(keys)
        }
        marks = PlantStateMarks(states=states, phase_names={"ph-x": HOSTILE_IMAGE_NAME})

        rendered = _render(_view(locations=beds, plants=plants), marks, layers=frozenset(PlanSvgLayer))

        root = _parse(rendered.svg)
        assert _tags(root) <= ALLOWED_ELEMENTS
        assert _attribute_names(root) <= ALLOWED_ATTRIBUTES
        assert "url(" not in rendered.svg and "<image" not in rendered.svg
        paints = {e.attrib[a] for e in root.iter() for a in ("fill", "stroke") if a in e.attrib}
        assert all(p == "none" or (p.startswith("#") and len(p) == 7) for p in paints)

    def test_from_the_threshold_on_the_states_are_ignored_and_the_counter_stays(self) -> None:
        beds = [make_location("b1", geometry=rect(1, 1, 4, 3))]
        plants = [_plant(f"p{i}", None, "b1") for i in range(PLANT_COUNTER_THRESHOLD)]
        marks = PlantStateMarks(
            states={plant.key: _state("active", "ph-flower", "overdue") for plant in plants}, phase_names=_PHASES
        )

        rendered = _render(_view(locations=beds, plants=plants), marks, locale="en")

        root = _parse(rendered.svg)
        layer = _plant_layer(root)
        assert rendered.plant_counters is True
        assert layer.findall(f"{SVG}circle") == [] and layer.findall(f"{SVG}g") == []
        assert _legend_texts(root) == ["Bed", "Number = plants in the bed"]


class TestPlantStateLegend:
    """GP-UX-005: the legend names the phases, rings and badges on the plan — and only those."""

    @pytest.mark.parametrize(
        ("locale", "expected"),
        [
            (
                "de",
                [
                    "Beet",
                    "Pflanze",
                    "Phase: Blüte",
                    "Phase: Ruhephase",
                    "Phase: Vegetativ",
                    "Ring: wächst",
                    "Ring dick: in Ernte",
                    "Dreieck: Befund",
                    "Kreis: überfällig",
                    "Quadrat: erntereif",
                ],
            ),
            (
                "en",
                [
                    "Bed",
                    "Plant",
                    "Phase: Dormancy",
                    "Phase: Flowering",
                    "Phase: Vegetative",
                    "Ring: growing",
                    "Thick ring: harvesting",
                    "Triangle: finding",
                    "Circle: overdue",
                    "Square: ready to harvest",
                ],
            ),
        ],
    )
    def test_phases_rings_and_badges_present(self, locale: str, expected: list[str]) -> None:
        view, marks = _stated_view()

        assert _legend_texts(_parse(_render(view, marks, locale=locale).svg)) == expected

    def test_the_swatches_carry_the_colours_the_plants_carry(self) -> None:
        view, marks = _stated_view()

        root = _parse(_render(view, marks, locale="en").svg)

        (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
        circles = [c.attrib["fill"] for c in legend.findall(f"{SVG}circle")]
        # plant, Dormancy, Flowering, Vegetative, two ring swatches
        assert circles == ["#1b5e20", "#D4E157", "#AB47BC", "#43A047", "#bdbdbd", "#bdbdbd"]
        badge_fills = [g.findall(f"{SVG}path")[0].attrib["fill"] for g in legend.findall(f"{SVG}g")]
        assert badge_fills == ["#b84300", "#c62828", "#1b5e20"]

    def test_every_plant_with_a_phase_colour_drops_the_uniform_plant_entry(self) -> None:
        view, marks = _stated_view()
        view = view.model_copy(update={"plants": view.plants[:4]})

        texts = _legend_texts(_parse(_render(view, marks, locale="en").svg))

        assert "Plant" not in texts and "Phase: Flowering" in texts

    def test_an_unknown_phase_name_is_printed_as_stored_and_shortened(self) -> None:
        view, marks = _stated_view()
        marks = PlantStateMarks(states={"p0": _state()}, phase_names={"ph-flower": "Nachreife im Keller " * 3})

        texts = _legend_texts(_parse(_render(view, marks).svg))

        (phase,) = [t for t in texts if t and t.startswith("Phase: ")]
        assert phase.startswith("Phase: Nachreife im") and phase.endswith("…")
        assert len(phase) <= plan_svg_engine._LEGEND_LABEL_CHARS

    def test_the_bigger_legend_still_fits_the_acceptance_page(self) -> None:
        view, marks = _stated_view()
        everything = {
            f"p{i}": _state(lifecycle, "ph-flower", code)
            for i, (lifecycle, code) in enumerate(zip(LIFECYCLES, ATTENTION_PRIORITY, strict=False))
        }
        plants = [_plant(key, None, "b1") for key in everything]
        view = view.model_copy(update={"plants": plants, "locations": _three_beds()})

        rendered = _render(view, PlantStateMarks(states=everything, phase_names=_PHASES))

        assert rendered.fits is True and rendered.scale == 50

        # SCR-003: one legend entry per phase made the strip of a many-phase plan tall enough to push a fixed 1:50
        # A4 plan off its page (422 ``plan.does_not_fit``). The phases are capped; the rest share one entry.
        phases = {f"ph-{n:02d}": f"Custom phase {n:02d}" for n in range(12)}
        # p-NN-i: phase NN carries 12 - NN plants, so ph-00 … ph-05 are the six most frequent; phase 00 alone has
        # every lifecycle and the phases together every badge.
        states = {
            f"p-{n:02d}-{i}": _state(LIFECYCLES[i % len(LIFECYCLES)], key, ATTENTION_PRIORITY[n % 5])
            for n, key in enumerate(phases)
            for i in range(12 - n)
        }
        plants = [_plant(key, None, "b1") for key in states]
        view = _view(locations=_three_beds(), plants=plants)

        rendered = _render(view, PlantStateMarks(states=states, phase_names=phases), scale=50, locale="en")

        assert rendered.fits is True and rendered.scale == 50
        texts = [t or "" for t in _legend_texts(_parse(rendered.svg))]
        phase_entries = [t for t in texts if t.startswith("Phase: ") or t.endswith("more phases")]
        assert len(phase_entries) == plan_svg_engine._MAX_PHASE_ENTRIES + 1
        assert phase_entries[:-1] == [f"Phase: Custom phase {n:02d}" for n in range(6)]
        assert phase_entries[-1] == "+6 more phases"

    def test_one_hidden_phase_is_named_in_the_singular(self) -> None:
        phases = {f"ph-{n}": f"Phase {n}" for n in range(7)}
        states = {f"p{n}": _state("active", key) for n, key in enumerate(phases)}
        view = _view(locations=_three_beds(), plants=[_plant(key, None, "b1") for key in states])

        texts = _legend_texts(_parse(_render(view, PlantStateMarks(states=states, phase_names=phases)).svg))

        assert texts[-2:] == ["+1 weitere Phase", "Ring: wächst"]

    def test_a_long_phase_name_is_shortened_to_its_legend_column(self) -> None:
        """SCR-004: the text starts after the swatch, so the whole entry — prefix included — must fit the column."""
        view, _ = _stated_view()
        name = "Nachreife im Keller bei 12 °C!"  # 30 characters
        assert len(name) == 30
        marks = PlantStateMarks(states={"p0": _state()}, phase_names={"ph-flower": name})

        texts = _legend_texts(_parse(_render(view, marks).svg))

        (phase,) = [t for t in texts if t and t.startswith("Phase: ")]
        assert phase.endswith("…") and len(phase) == plan_svg_engine._LEGEND_LABEL_CHARS
        text_mm = len(phase) * plan_svg_engine._LABEL_MM * plan_svg_engine._GLYPH_WIDTH_EM
        offset_mm = plan_svg_engine._LEGEND_SWATCH_MM + plan_svg_engine._LEGEND_TEXT_GAP_MM
        assert offset_mm + text_mm <= plan_svg_engine._LEGEND_COLUMN_MM

    def test_golden_legend_markup_de(self) -> None:
        """Snapshot of the legend block for a fixed fixture: a change to it is a deliberate change of this file."""
        view, marks = _stated_view()

        svg = _render(view, marks, locale="de").svg

        # The legend is the last group of the document; the writer's own bytes are compared, not a re-serialisation.
        start = svg.index('<g id="legend">')
        assert svg.endswith("</svg>")
        assert svg[start : -len("</svg>")] == _GOLDEN_LEGEND.read_text(encoding="utf-8").strip()


_GOLDEN_LEGEND = Path(__file__).with_name("golden") / "plan_svg_legend_de.svg"
