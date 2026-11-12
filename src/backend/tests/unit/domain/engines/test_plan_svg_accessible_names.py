"""REQ-053 GP-NFR-029 (#2900) — every drawn object of the plan SVG carries a ``<title>`` and a ``<desc>``.

Parsed as XML, not grepped: "every object" is the set of elements that carry a ``data-key`` (beds, garden objects,
slots) plus the plant symbols and the boundary shape, so a new object kind that forgets its accessible name fails
here. The escaping assertions read the parsed text back: a name that broke out of its ``<title>`` would show up as an
element, not as the text.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.common.enums import BedStatus, GardenObjectType, LampKind
from app.domain.calculators.plant_state_calculator import AttentionReason, PlantVisualState
from app.domain.engines.plan_svg_engine import (
    ALLOWED_ELEMENTS,
    PlanSvgLayer,
    PlanSvgOptions,
    PlantStateMarks,
    render_plan_svg,
)
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import GardenPlanView, PlanSlotView, PlantShortInfo
from app.domain.models.site import SitePlan
from tests.support.garden_plan_fakes import SITE, make_location, rect

SVG = "{http://www.w3.org/2000/svg}"
HOSTILE = '"><image href="http://169.254.169.254/"/>'
ALL_LAYERS = frozenset(PlanSvgLayer)


def _object(key: str, object_type: GardenObjectType, geometry: dict, props: dict, **kwargs) -> GardenObject:
    return GardenObject(_key=key, site_key=SITE, object_type=object_type, geometry=geometry, props=props, **kwargs)


def _view(*, bed_name: str = "Tomaten", object_label: str = "Apfel", site_name: str = "Garten") -> GardenPlanView:
    """Two beds (one planned), a labelled tree with a species, an unlabelled wall (a line), a lamp (a point), an
    off-site building, a slot and three plants: one in the slot, two loose in the first bed."""
    return GardenPlanView(
        site_key=SITE,
        site_name=site_name,
        plan_revision=1,
        plan=SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0},
            plan_revision=1,
        ),
        locations=[
            make_location("b1", bed_name, geometry=rect(1, 1, 2, 1)),
            make_location("b2", "Kräuter", geometry=rect(5, 1, 2, 2), bed_status=BedStatus.PLANNED),
        ],
        garden_objects=[
            _object(
                "o_tree",
                GardenObjectType.TREE,
                {"kind": "circle", "origin": [5, 5], "radius_m": 0.8},
                {"crown_radius_m": 0.8, "species_label": "Malus domestica", "height_m": 4.0},
                label=object_label,
            ),
            _object(
                "o_wall",
                GardenObjectType.WALL,
                {"kind": "polyline", "points": [[0.5, 0.5], [3.5, 0.5]], "width_m": 0.2},
                {"height_m": 1.2},
            ),
            _object(
                "o_lamp",
                GardenObjectType.LAMP,
                {"kind": "point", "origin": [8, 4]},
                {"kind": next(iter(LampKind)).value, "height_m": 2.0},
            ),
            _object(
                "o_house",
                GardenObjectType.BUILDING,
                {"kind": "rect", "origin": [8.5, 0.5], "width_m": 1, "length_m": 1, "rotation_deg": 0},
                {},
                off_site=True,
            ),
        ],
        slots=[
            PlanSlotView(
                key="s1",
                slot_id="A_1",
                location_key="b1",
                slot_role="position",
                capacity_plants=1,
                currently_occupied=True,
                plan_geometry={"kind": "point", "origin": [1.5, 1.5]},
            )
        ],
        plants=[
            PlantShortInfo(key="p1", instance_id="PL-1", species_key="sp", slot_key="s1"),
            PlantShortInfo(key="p2", instance_id="PL-2", species_key="sp", location_key="b1", phase_key="ph"),
            PlantShortInfo(key="p3", instance_id="PL-3", species_key="sp", location_key="b1"),
        ],
    )


def _marks() -> PlantStateMarks:
    state = PlantVisualState(
        lifecycle="active",
        phase_key="ph",
        phase_progress=None,
        attention=(AttentionReason("water", 1),),
        harvest_ready=False,
        harvest_ready_from=None,
    )
    return PlantStateMarks(states={"p2": state}, phase_names={"ph": "flowering"})


def _render(view: GardenPlanView, marks: PlantStateMarks | None = None, *, locale: str = "de") -> ET.Element:
    options = PlanSvgOptions(layers=ALL_LAYERS, locale=locale)
    return ET.fromstring(render_plan_svg(view, options, marks).svg)


def _layer(root: ET.Element, layer_id: str) -> ET.Element:
    (layer,) = [e for e in root.iter() if e.attrib.get("id") == layer_id]
    return layer


def _drawn_objects(root: ET.Element) -> list[ET.Element]:
    """Beds, garden objects and slots (by ``data-key``, labels excluded), the plant discs and the boundary shape."""
    keyed = [e for e in root.iter() if "data-key" in e.attrib and e.tag != f"{SVG}text"]
    plants = _layer(root, "layer-plants").findall(f"{SVG}circle")
    boundary = list(_layer(root, "layer-boundary"))
    return keyed + plants + boundary


def _title(element: ET.Element) -> str | None:
    return element[0].text if len(element) and element[0].tag == f"{SVG}title" else None


def _desc(element: ET.Element) -> str | None:
    return element[1].text if len(element) > 1 and element[1].tag == f"{SVG}desc" else None


def _by_key(root: ET.Element, key: str) -> ET.Element:
    (element,) = [e for e in root.iter() if e.attrib.get("data-key") == key and e.tag != f"{SVG}text"]
    return element


class TestEveryObjectIsNamedAndDescribed:
    def test_every_drawn_object_starts_with_a_title_and_a_desc(self) -> None:
        root = _render(_view(), _marks())

        drawn = _drawn_objects(root)
        # 2 beds + 4 objects + 1 slot + 3 plants + the boundary: the fixture really reaches every kind.
        assert len(drawn) == 11
        missing = [(e.tag, e.attrib.get("data-key")) for e in drawn if not _title(e) or not _desc(e)]
        assert missing == []

    def test_the_root_exposes_its_children_to_assistive_technology(self) -> None:
        root = _render(_view())

        assert root.attrib["role"] == "graphics-document"
        assert [child.tag for child in root[:2]] == [f"{SVG}title", f"{SVG}desc"]

    def test_ids_and_keys_of_the_drawing_are_unchanged(self) -> None:
        root = _render(_view())

        ids = [e.attrib["id"] for e in root.iter() if "id" in e.attrib]
        assert ids[:7] == [
            "layer-grid",
            "layer-beds",
            "layer-objects",
            "layer-boundary",
            "layer-slots",
            "layer-plants",
            "layer-labels",
        ]
        assert _tags(root) <= ALLOWED_ELEMENTS


def _tags(root: ET.Element) -> set[str]:
    return {element.tag.removeprefix(SVG) for element in root.iter()}


class TestWhatTheyCarry:
    def test_a_bed_names_its_class_and_describes_status_area_plants_and_phases(self) -> None:
        root = _render(_view(), _marks())

        bed = _by_key(root, "b1")
        assert _title(bed) == "Beet: Tomaten"
        assert _desc(bed) == "aktiv; Fläche 2,0 m²; 3 Pflanzen; Phasen: Blüte"
        assert _desc(_by_key(root, "b2")) == "geplant; Fläche 4,0 m²; keine Pflanzen"

    def test_a_garden_object_names_class_and_label_and_describes_species_size_and_height(self) -> None:
        root = _render(_view())

        tree = _by_key(root, "o_tree")
        assert _title(tree) == "Baum: Apfel"
        assert _desc(tree) == "Art: Malus domestica; Fläche 2,0 m²; Höhe 4,0 m"

    def test_an_object_without_a_label_is_named_by_its_class(self) -> None:
        root = _render(_view())

        assert _title(_by_key(root, "o_wall")) == "Mauer"
        assert _desc(_by_key(root, "o_wall")) == "Länge 3,0 m; Höhe 1,2 m"
        assert _desc(_by_key(root, "o_lamp")) == "Punktobjekt; Höhe 2,0 m"
        assert _desc(_by_key(root, "o_house")) == "Fläche 1,0 m²; außerhalb der Plangrenze"

    def test_a_plant_and_a_slot_say_where_they_stand_and_how_the_plant_is(self) -> None:
        root = _render(_view(), _marks())

        plants = {_title(disc): _desc(disc) for disc in _layer(root, "layer-plants").findall(f"{SVG}circle")}
        assert plants["Pflanze: PL-2"] == "in Tomaten; Phase: Blüte; wächst; Achtung: gießen"
        assert plants["Pflanze: PL-3"] == "in Tomaten"
        slot = _by_key(root, "s1")
        assert (_title(slot), _desc(slot)) == ("Pflanzplatz: A_1", "in Tomaten; belegt")

    def test_the_boundary_is_named_and_measured(self) -> None:
        root = _render(_view())

        (boundary,) = list(_layer(root, "layer-boundary"))
        assert (_title(boundary), _desc(boundary)) == ("Plangrenze: Garten", "Fläche 60,0 m²")

    def test_the_export_locale_translates_them(self) -> None:
        root = _render(_view(), _marks(), locale="en")

        assert _title(_by_key(root, "b1")) == "Bed: Tomaten"
        assert _desc(_by_key(root, "b1")) == "active; area 2.0 m²; 3 plants; phases: Flowering"
        assert _title(_by_key(root, "o_tree")) == "Tree: Apfel"
        assert _desc(_by_key(root, "o_wall")) == "length 3.0 m; height 1.2 m"


class TestEscaping:
    @pytest.mark.parametrize("where", ["bed", "object", "site"])
    def test_a_hostile_name_stays_text_in_every_title_and_desc_it_reaches(self, where: str) -> None:
        view = _view(
            bed_name=HOSTILE if where == "bed" else "Tomaten",
            object_label=HOSTILE if where == "object" else "Apfel",
            site_name=HOSTILE if where == "site" else "Garten",
        )

        root = _render(view, _marks())

        assert "image" not in _tags(root)
        texts = [e.text or "" for e in root.iter() if e.tag in {f"{SVG}title", f"{SVG}desc"}]
        expected = {
            "bed": ["Beet: " + HOSTILE, "in " + HOSTILE],
            "object": ["Baum: " + HOSTILE],
            "site": ["Plangrenze: " + HOSTILE],
        }[where]
        for text in expected:
            assert any(entry == text or entry.startswith(text + ";") for entry in texts), text

    def test_control_characters_are_dropped_and_whitespace_collapsed(self) -> None:
        root = _render(_view(bed_name="Beet\x00\x01  mit\n\tUmbruch"))

        assert _title(_by_key(root, "b1")) == "Beet: Beet mit Umbruch"
