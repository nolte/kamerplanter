"""Server-side SVG writer of the garden plan (REQ-053 §23, GP-FR-142/143, GP-NFR-052 (b)).

Pure logic, no I/O, no SVG library: the plan is drawn as a self-contained SVG whose ``viewBox`` is in
**real-world millimetres** (1 m = 1 000 units, GP-FR-143) and whose ``width``/``height`` are the paper size
at the chosen scale, so a 2 × 1 m bed at 1:50 measures 40 × 20 mm in any viewer and in the PDF. The same
SVG is the ``GET /sites/{key}/plan/render.svg`` download and, embedded as a ``data:`` image, the body of
the garden-plan PDF.

**Why a writer instead of string templates.** Every name on a plan is user input (a bed called
``"><image href="http://169.254.169.254/"/>``), and the SVG ends up in a PDF renderer that can fetch URLs.
:class:`_Node` therefore accepts only the elements and attributes of the allowlist below (SR-015): no
``image``, ``foreignObject``, ``script``, ``use``, ``a``; no ``href``/``xlink:href``/``style``/``on*``
attribute. A tag or attribute outside the list is a programming error and raises, so a future edit cannot
add one quietly. Text content and attribute values are escaped for their own context, and characters XML
cannot carry are dropped (a NUL in a name would otherwise make the document unparsable and the PDF a 500).
Paint values are matched against a hex pattern before they are written; there is no ``url(...)`` anywhere.

**Layout.** One canvas: the plan, below it a strip with the scale bar, the north arrow and the legend. The
scale is chosen from the twelve fixed steps (GP-FR-142) as the finest one at which the plan *and* the strip
fit the page; ``A3`` is suggested when A4 would need a scale coarser than 1:200.

**Plant states (GP-UX-005/059/060, #2489).** When the caller hands :class:`PlantStateMarks` (the export service
computes them with the same assembly as ``GET /locations/{key}/plant-states``), a plant below the counter threshold is
drawn as the plan on screen draws it: the disc in its phase colour (:mod:`app.domain.engines.phase_colors`), the ring
style of its lifecycle (stroke width and dash only) and at most one attention badge (two ``path`` elements in a
``g``) — all inside the allowlist. The legend lists the phases, rings and badges that are on the plan. A plant without
a state keeps the uniform plant colour; from the threshold on, the counters apply as before (GP-NFR-038).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from app.common.enums import BedStatus, GardenObjectType
from app.common.exceptions import PlanError
from app.domain.calculators.geometry_calculator import (
    CircleShape,
    bounding_box,
    centroid,
    to_shape,
)
from app.domain.calculators.label_anchor_calculator import label_anchor
from app.domain.calculators.plant_state_calculator import (
    ATTENTION_PRIORITY,
    LIFECYCLES,
    AttentionCode,
    Lifecycle,
    PlantVisualState,
)
from app.domain.engines.phase_colors import phase_color
from app.domain.models.garden_object import POINT_OBJECT_RADIUS_M, GardenObject
from app.domain.models.garden_plan import GardenPlanView, PlanSlotView, PlantShortInfo
from app.domain.models.geometry import (
    CircleGeometry,
    Geometry,
    PointGeometry,
    PolylineGeometry,
)
from app.domain.models.site import Location

# ── Query vocabulary (GP-NFR-052 (c): enums, not free strings) ────────────────


class PlanPaper(StrEnum):
    A4 = "a4"
    A3 = "a3"


class PlanOrientation(StrEnum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class PlanSvgLayer(StrEnum):
    """The layers a print can switch (GP-FR-031, GP-FR-142 "Ebenenwahl"); boundary, scale bar, north arrow and
    legend are always drawn."""

    GRID = "grid"
    BEDS = "beds"
    OBJECTS = "objects"
    SLOTS = "slots"
    PLANTS = "plants"
    LABELS = "labels"


DEFAULT_LAYERS: Final[frozenset[PlanSvgLayer]] = frozenset(
    {PlanSvgLayer.BEDS, PlanSvgLayer.OBJECTS, PlanSvgLayer.PLANTS, PlanSvgLayer.LABELS}
)

#: The twelve scale steps of GP-FR-142 (denominators), finest first.
SCALE_STEPS: Final[tuple[int, ...]] = (20, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500)
#: A4 would need a scale coarser than this → A3 is suggested (GP-FR-142).
A3_SUGGESTION_ABOVE: Final = 200
#: From this many plants on, a bed shows one counter instead of one symbol per plant (GP-NFR-038).
PLANT_COUNTER_THRESHOLD: Final = 2000

#: Paper size in mm, landscape orientation; portrait swaps the axes.
_PAPER_MM: Final[dict[PlanPaper, tuple[float, float]]] = {PlanPaper.A4: (297.0, 210.0), PlanPaper.A3: (420.0, 297.0)}
PAGE_MARGIN_MM: Final = 10.0
#: Title block height on a PDF page, above the SVG.
PDF_HEADER_MM: Final = 12.0

DEFAULT_ACCENT: Final = "#2e7d32"
_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PAINT = re.compile(r"^(?:none|#[0-9A-Fa-f]{6})$")

# ── Allowlist (SR-015) ────────────────────────────────────────────────────────

ALLOWED_ELEMENTS: Final[frozenset[str]] = frozenset(
    {
        "svg",
        "g",
        "rect",
        "circle",
        "polygon",
        "polyline",
        "line",
        "path",
        "text",
        "tspan",
        "title",
        "desc",
        "defs",
        "pattern",
    }
)
ALLOWED_ATTRIBUTES: Final[frozenset[str]] = frozenset(
    {
        "xmlns",
        "viewBox",
        "width",
        "height",
        "role",
        "aria-label",
        "id",
        "data-key",
        "data-scale",
        "x",
        "y",
        "cx",
        "cy",
        "r",
        "x1",
        "y1",
        "x2",
        "y2",
        "points",
        "d",
        "transform",
        "fill",
        "stroke",
        "stroke-width",
        "stroke-dasharray",
        "stroke-linejoin",
        "stroke-linecap",
        "fill-opacity",
        "opacity",
        "font-family",
        "font-size",
        "font-weight",
        "text-anchor",
        "dominant-baseline",
    }
)
_PAINT_ATTRIBUTES: Final = frozenset({"fill", "stroke"})
_SVG_NAMESPACE: Final = "http://www.w3.org/2000/svg"
_FONT: Final = "Helvetica, Arial, sans-serif"

# Characters XML 1.0 cannot carry: C0 controls but tab/LF/CR, the surrogates and U+FFFE/U+FFFF.
_XML_ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff￾￿]")


def clean_text(value: str) -> str:
    """Drop the characters an XML document cannot hold; the rest is escaped by the node that writes it."""
    return _XML_ILLEGAL.sub("", value)


def escape_text(value: str) -> str:
    """Escape text content (``&``, ``<``, ``>``)."""
    return clean_text(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_attribute(value: str) -> str:
    """Escape an attribute value written between double quotes; whitespace controls become character references."""
    return (
        clean_text(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "&#10;")
        .replace("\r", "&#13;")
        .replace("\t", "&#9;")
    )


def _fine(value: float) -> str:
    """A small factor (a scale, a stroke width inside a scaled group) with three decimals, trailing zeros dropped."""
    if not math.isfinite(value):
        raise ValueError("SVG values must be finite")
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _num(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("SVG coordinates must be finite")
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


AttributeValue = str | int | float


@dataclass
class _Node:
    """One element of the allowlist; the only way a byte reaches the output."""

    tag: str
    attributes: dict[str, AttributeValue] = field(default_factory=dict)
    children: list[_Node | str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.tag not in ALLOWED_ELEMENTS:
            raise ValueError(f"SVG element {self.tag!r} is not on the allowlist")
        for name, value in self.attributes.items():
            if name not in ALLOWED_ATTRIBUTES:
                raise ValueError(f"SVG attribute {name!r} is not on the allowlist")
            if name in _PAINT_ATTRIBUTES and not (isinstance(value, str) and _PAINT.match(value)):
                raise ValueError(f"SVG paint {value!r} is neither none nor #rrggbb")

    def add(self, *children: _Node | str) -> _Node:
        self.children.extend(children)
        return self

    def render(self) -> str:
        rendered = "".join(
            f' {name}="{escape_attribute(_num(value) if isinstance(value, float) else str(value))}"'
            for name, value in self.attributes.items()
        )
        if not self.children:
            return f"<{self.tag}{rendered}/>"
        body = "".join(child.render() if isinstance(child, _Node) else escape_text(child) for child in self.children)
        return f"<{self.tag}{rendered}>{body}</{self.tag}>"


def _el(tag: str, children: list[_Node | str] | None = None, **attributes: AttributeValue) -> _Node:
    # ``stroke_width`` → ``stroke-width``; ``view_box`` is the one camel-case attribute.
    named = {("viewBox" if key == "view_box" else key.replace("_", "-")): value for key, value in attributes.items()}
    return _Node(tag, named, list(children or []))


# ── Labels ────────────────────────────────────────────────────────────────────

_LABELS: Final[dict[str, dict[str, str]]] = {
    "de": {
        "north": "N",
        "legend_bed_active": "Beet",
        "legend_bed_planned": "Beet (geplant)",
        "legend_bed_retired": "Beet (stillgelegt)",
        "legend_plant": "Pflanze",
        "legend_plants_counter": "Zahl = Pflanzen im Beet",
        "legend_slot": "Pflanzplatz",
        "legend_phase": "Phase",
        "legend_more_phase": "+{n} weitere Phase",
        "legend_more_phases": "+{n} weitere Phasen",
        "ring_planned": "Ring: geplant",
        "ring_sown": "Ring: gesät",
        "ring_active": "Ring: wächst",
        "ring_harvesting": "Ring dick: in Ernte",
        "ring_failed": "Ring leer: ausgefallen",
        "ring_historic": "Ring: abgeschlossen",
        "badge_problem": "Dreieck: Befund",
        "badge_frost": "Sechseck: Frostgefahr",
        "badge_overdue": "Kreis: überfällig",
        "badge_water": "Tropfen: gießen",
        "badge_harvest": "Quadrat: erntereif",
        "metre": "m",
        "plants": "Pflanzen",
        "desc": "Maßstäblicher Gartenplan",
        "type_path": "Weg",
        "type_lawn": "Rasen",
        "type_tree": "Baum",
        "type_shrub": "Strauch",
        "type_building": "Gebäude",
        "type_wall": "Mauer",
        "type_fence": "Zaun",
        "type_trellis": "Rankgitter",
        "type_water_source": "Wasserstelle",
        "type_compost": "Kompost",
        "type_storage": "Lager",
        "type_other": "Sonstiges",
        "type_window": "Fenster",
        "type_door": "Tür",
        "type_furniture": "Möbel",
        "type_lamp": "Lampe",
    },
    "en": {
        "north": "N",
        "legend_bed_active": "Bed",
        "legend_bed_planned": "Bed (planned)",
        "legend_bed_retired": "Bed (retired)",
        "legend_plant": "Plant",
        "legend_plants_counter": "Number = plants in the bed",
        "legend_slot": "Planting spot",
        "legend_phase": "Phase",
        "legend_more_phase": "+{n} more phase",
        "legend_more_phases": "+{n} more phases",
        "ring_planned": "Ring: planned",
        "ring_sown": "Ring: sown",
        "ring_active": "Ring: growing",
        "ring_harvesting": "Thick ring: harvesting",
        "ring_failed": "Empty ring: failed",
        "ring_historic": "Ring: finished",
        "badge_problem": "Triangle: finding",
        "badge_frost": "Hexagon: frost risk",
        "badge_overdue": "Circle: overdue",
        "badge_water": "Drop: watering due",
        "badge_harvest": "Square: ready to harvest",
        "metre": "m",
        "plants": "plants",
        "desc": "Garden plan to scale",
        "type_path": "Path",
        "type_lawn": "Lawn",
        "type_tree": "Tree",
        "type_shrub": "Shrub",
        "type_building": "Building",
        "type_wall": "Wall",
        "type_fence": "Fence",
        "type_trellis": "Trellis",
        "type_water_source": "Water source",
        "type_compost": "Compost",
        "type_storage": "Storage",
        "type_other": "Other",
        "type_window": "Window",
        "type_door": "Door",
        "type_furniture": "Furniture",
        "type_lamp": "Lamp",
    },
}

#: Display names of the known growth phases (``enums.phaseName`` of the frontend), keyed like
#: ``PlantStateLegendSection.phaseKeyOf``; any other name is printed as stored.
_PHASE_NAMES: Final[dict[str, dict[str, str]]] = {
    "de": {
        "germination": "Keimung",
        "seedling": "Sämling",
        "vegetative": "Vegetativ",
        "flowering": "Blüte",
        "flushing": "Spülung",
        "dormancy": "Ruhephase",
        "ripening": "Reife",
        "harvest": "Ernte",
        "juvenile": "Juvenil",
        "climbing": "Kletterphase",
        "mature": "Reife Pflanze",
        "establishment": "Etablierung",
        "pup_establishment": "Kindel-Etablierung",
        "pre_bloom": "Vorblüte",
        "senescence": "Seneszenz",
        "recovery": "Erholung",
        "sprouting": "Austrieb",
        "hardening_off": "Abhärtung",
        "budding": "Knospenbildung",
        "corm_ripening": "Knollenreife",
        "tuber_formation": "Knollenbildung",
    },
    "en": {
        "germination": "Germination",
        "seedling": "Seedling",
        "vegetative": "Vegetative",
        "flowering": "Flowering",
        "flushing": "Flushing",
        "dormancy": "Dormancy",
        "ripening": "Ripening",
        "harvest": "Harvest",
        "juvenile": "Juvenile",
        "climbing": "Climbing",
        "mature": "Mature",
        "establishment": "Establishment",
        "pup_establishment": "Pup Establishment",
        "pre_bloom": "Pre-Bloom",
        "senescence": "Senescence",
        "recovery": "Recovery",
        "sprouting": "Sprouting",
        "hardening_off": "Hardening Off",
        "budding": "Budding",
        "corm_ripening": "Corm Ripening",
        "tuber_formation": "Tuber Formation",
    },
}
_PHASE_SEPARATORS = re.compile(r"[\s-]+")
#: Phases the legend names one by one: the most frequent by plant count; the rest share one "+n more phases" entry,
#: so a plan with many phases keeps a strip of bounded height and still fits its page at the requested scale.
_MAX_PHASE_ENTRIES: Final = 6


# ── Styling ───────────────────────────────────────────────────────────────────

_BED_STYLE: Final[dict[BedStatus, tuple[str, str, str | None]]] = {
    BedStatus.ACTIVE: ("#c8e6c9", "#2e7d32", None),
    BedStatus.PLANNED: ("#fff9c4", "#f9a825", "3 2"),
    BedStatus.RETIRED: ("#eeeeee", "#9e9e9e", "1 2"),
}
_BED_LABEL_KEY: Final[dict[BedStatus, str]] = {
    BedStatus.ACTIVE: "legend_bed_active",
    BedStatus.PLANNED: "legend_bed_planned",
    BedStatus.RETIRED: "legend_bed_retired",
}
#: Fill and stroke per object class; line classes (wall, fence, trellis, path polylines) use the stroke only.
_OBJECT_STYLE: Final[dict[GardenObjectType, tuple[str, str]]] = {
    GardenObjectType.PATH: ("#d7ccc8", "#8d6e63"),
    GardenObjectType.LAWN: ("#dcedc8", "#7cb342"),
    GardenObjectType.TREE: ("#81c784", "#2e7d32"),
    GardenObjectType.SHRUB: ("#a5d6a7", "#388e3c"),
    GardenObjectType.BUILDING: ("#bdbdbd", "#424242"),
    GardenObjectType.WALL: ("#616161", "#424242"),
    GardenObjectType.FENCE: ("#a1887f", "#5d4037"),
    GardenObjectType.TRELLIS: ("#8d6e63", "#5d4037"),
    GardenObjectType.WATER_SOURCE: ("#90caf9", "#1565c0"),
    GardenObjectType.COMPOST: ("#bcaaa4", "#6d4c41"),
    GardenObjectType.STORAGE: ("#cfd8dc", "#546e7a"),
    GardenObjectType.OTHER: ("#e0e0e0", "#757575"),
    GardenObjectType.WINDOW: ("#b3e5fc", "#0277bd"),
    GardenObjectType.DOOR: ("#d7ccc8", "#4e342e"),
    GardenObjectType.FURNITURE: ("#d7ccc8", "#6d4c41"),
    GardenObjectType.LAMP: ("#fff59d", "#f9a825"),
}
_OFF_SITE_STYLE: Final = ("#eeeeee", "#9e9e9e")
_TEXT_COLOR: Final = "#212121"
_PLANT_COLOR: Final = "#1b5e20"
_GRID_COLOR: Final = "#cfd8dc"


@dataclass(frozen=True)
class _RingStyle:
    """The ring of a stated plant marker (``renderer/plantMarkerStyle.ts`` ``RING_STYLES``), in what paper can carry:
    the dash pattern (units of :data:`_RING_DASH_MM`), the stroke width and the disc's fill opacity (0 = no disc)."""

    dash: str | None
    width_mm: float
    disc_opacity: float


#: Lifecycle → ring (§11.3). The screen's double ring (harvesting) is a thick ring on paper, the cross on a failed
#: plant an empty ring; every lifecycle stays apart in greyscale.
_RING_STYLE: Final[dict[Lifecycle, _RingStyle]] = {
    "planned": _RingStyle("3 2", 0.2, 0.4),
    "sown": _RingStyle("1 2", 0.2, 0.4),
    "active": _RingStyle(None, 0.2, 1.0),
    "harvesting": _RingStyle(None, 0.5, 1.0),
    "failed": _RingStyle(None, 0.2, 0.0),
    "historic": _RingStyle("6 3", 0.2, 0.5),
}
_RING_DASH_MM: Final = 0.2
#: Fill, outline path and glyph path of the one attention badge (``plantMarkerStyle.ts`` ``BADGE_STYLES``), drawn in a
#: -1…1 box that a ``transform`` places and scales.
_BADGE_STYLE: Final[dict[AttentionCode, tuple[str, str, str]]] = {
    "problem": ("#b84300", "M0 -1L1 0.85L-1 0.85Z", "M0 -0.3V0.3M0 0.55V0.58"),
    "frost": (
        "#01579b",
        "M0 -1L0.87 -0.5L0.87 0.5L0 1L-0.87 0.5L-0.87 -0.5Z",
        "M0 -0.55V0.55M-0.48 -0.27L0.48 0.27M-0.48 0.27L0.48 -0.27",
    ),
    "overdue": ("#c62828", "M0 -1A1 1 0 1 1 0 1A1 1 0 1 1 0 -1Z", "M0 -0.5V0.1M0 0.45V0.48"),
    "water": (
        "#0d47a1",
        "M0 -1C0.8 -0.1 0.95 0.3 0.95 0.5A0.95 0.95 0 0 1 -0.95 0.5C-0.95 0.3 -0.8 -0.1 0 -1Z",
        "M-0.35 0.45A0.4 0.4 0 0 0 0.05 0.85",
    ),
    "harvest": ("#1b5e20", "M-0.85 -0.85H0.85V0.85H-0.85Z", "M-0.5 0L-0.1 0.42L0.55 -0.4"),
}
_BADGE_OUTLINE: Final = "#ffffff"
#: Badge radius and centre offset (upper right) as shares of the marker radius (``plantMarkerStyle.ts``).
_BADGE_RADIUS_SHARE: Final = 0.62
_BADGE_OFFSET_SHARE: Final = 0.85
#: Disc of the ring swatches in the legend: neutral, so a ring entry is not read as a phase.
_RING_SWATCH_FILL: Final = "#bdbdbd"

_LEGEND_COLUMN_MM: Final = 46.0
_LEGEND_ROW_MM: Final = 5.0
#: Swatch width and the gap to its text in a legend entry; the text starts this far into its column.
_LEGEND_SWATCH_MM: Final = 5.0
_LEGEND_TEXT_GAP_MM: Final = 1.8
#: Clearance kept free before the next column's swatch.
_LEGEND_COLUMN_GAP_MM: Final = 0.5
_STRIP_BASE_MM: Final = 24.0
_MIN_CANVAS_MM: Final = 120.0
_PAD_MM: Final = 3.0
_LABEL_MM: Final = 2.8
#: Average glyph width as a share of the font size: the estimate every text fit on the plan uses.
_GLYPH_WIDTH_EM: Final = 0.55
#: Characters a legend text may take before it runs into the next column (25 with the values above).
_LEGEND_LABEL_CHARS: Final = int(
    (_LEGEND_COLUMN_MM - _LEGEND_SWATCH_MM - _LEGEND_TEXT_GAP_MM - _LEGEND_COLUMN_GAP_MM)
    / (_LABEL_MM * _GLYPH_WIDTH_EM)
)
_GRID_MIN_PITCH_MM: Final = 5.0
_NICE_LENGTHS_M: Final = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)


# ── Public types ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlanSvgOptions:
    """What the caller chose; every field is already validated (enums, ``#rrggbb``)."""

    scale: int | None = None
    paper: PlanPaper = PlanPaper.A4
    orientation: PlanOrientation = PlanOrientation.LANDSCAPE
    layers: frozenset[PlanSvgLayer] = DEFAULT_LAYERS
    locale: str = "de"
    accent: str = DEFAULT_ACCENT
    #: Height reserved above the SVG on the page (the PDF's title block); 0 for the stand-alone SVG.
    header_mm: float = 0.0


@dataclass(frozen=True)
class PlantStateMarks:
    """What the plan knows about its plants' states (GP-UX-005/059/060): the visual state per plant key and the
    growth-phase name per phase key. A plant that has no entry in ``states`` is drawn in the uniform plant colour."""

    states: Mapping[str, PlantVisualState] = field(default_factory=dict)
    phase_names: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanFrame:
    """How plan metres land on the printed page, so something drawn *beside* the SVG (the underlay, GP-FR-033)
    can be laid under it: ``x_mm = (x - origin_x_m) * 1000 / scale + shift_x_mm`` and
    ``y_mm = (origin_y_m - y) * 1000 / scale``."""

    origin_x_m: float
    origin_y_m: float
    shift_x_mm: float
    scale: int

    def paper_point(self, x_m: float, y_m: float) -> tuple[float, float]:
        return (
            (x_m - self.origin_x_m) * 1000.0 / self.scale + self.shift_x_mm,
            (self.origin_y_m - y_m) * 1000.0 / self.scale,
        )


@dataclass(frozen=True)
class PlanSvg:
    svg: str
    scale: int
    width_mm: float
    height_mm: float
    #: The plan and its strip fit the page at ``scale``; false only when even 1:500 (or the fixed scale) overflows.
    fits: bool
    #: A3 would give a finer scale than A4 needs (GP-FR-142).
    suggest_a3: bool
    plant_counters: bool
    frame: PlanFrame | None = None


def page_size_mm(paper: PlanPaper, orientation: PlanOrientation) -> tuple[float, float]:
    width, height = _PAPER_MM[paper]
    return (height, width) if orientation is PlanOrientation.PORTRAIT else (width, height)


def parse_scale(raw: str) -> int | None:
    """``auto`` → ``None``; ``1:50`` → 50. Only the twelve steps are accepted."""
    if raw == "auto":
        return None
    prefix, _, denominator = raw.partition(":")
    if prefix != "1" or not denominator.isdigit() or int(denominator) not in SCALE_STEPS:
        raise ValueError(f"scale must be auto or 1:n with n in {SCALE_STEPS}")
    return int(denominator)


# ── Content ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Extent:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


def _union(boxes: list[tuple[float, float, float, float]]) -> _Extent | None:
    if not boxes:
        return None
    return _Extent(
        min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)
    )


def _geometry_box(geometry: Geometry) -> tuple[float, float, float, float]:
    box = bounding_box(geometry)
    if isinstance(geometry, PointGeometry):
        x, y = geometry.origin
        return (
            x - POINT_OBJECT_RADIUS_M,
            y - POINT_OBJECT_RADIUS_M,
            x + POINT_OBJECT_RADIUS_M,
            y + POINT_OBJECT_RADIUS_M,
        )
    return box


def _extent_of(view: GardenPlanView) -> _Extent | None:
    boundary = view.plan.boundary if view.plan is not None else None
    # The boundary and everything placed on the plan: a bed the boundary does not enclose is still drawn, not clipped.
    boxes = [_geometry_box(boundary)] if boundary is not None else []
    boxes += [_geometry_box(loc.geometry) for loc in view.locations if loc.geometry is not None]
    boxes += [_geometry_box(obj.geometry) for obj in view.garden_objects if not obj.off_site]
    return _union(boxes)


@dataclass(frozen=True)
class _LegendEntry:
    swatch: str  # "box" | "circle" | "badge" | "none" (text only)
    fill: str
    stroke: str
    label: str
    dash: str | None = None
    #: Paper millimetres per unit of ``dash``.
    dash_unit_mm: float = 0.4
    #: Stroke width of a circle swatch in paper millimetres.
    width_mm: float = 0.2
    fill_opacity: float | None = None
    badge: AttentionCode | None = None


@dataclass(frozen=True)
class _PlantMarker:
    """One plant symbol: where it stands (plan metres), its state (``None`` = uniform symbol) and its disc colour."""

    point: tuple[float, float]
    state: PlantVisualState | None = None
    fill: str = _PLANT_COLOR
    phase_label: str | None = None


def _phase_label(name: str, locale: str) -> str:
    """The legend name of a growth phase: the translation of a known phase, else the stored name (cleaned). The
    legend entry shortens it to its column (:data:`_LEGEND_LABEL_CHARS`)."""
    key = _PHASE_SEPARATORS.sub("_", name.strip().lower())
    known = _PHASE_NAMES.get(locale, _PHASE_NAMES["de"]).get(key)
    return known if known is not None else " ".join(clean_text(name).split())


def _marker_of(
    plant: PlantShortInfo, point: tuple[float, float], marks: PlantStateMarks | None, locale: str
) -> _PlantMarker:
    state = marks.states.get(plant.key) if marks is not None else None
    if marks is None or state is None:
        return _PlantMarker(point)
    phase_key = state.phase_key or plant.phase_key
    name = marks.phase_names.get(phase_key) if phase_key else None
    if not name or not name.strip():
        return _PlantMarker(point, state)
    return _PlantMarker(point, state, phase_color(name), _phase_label(name, locale))


def _phase_rank(item: tuple[tuple[str, str], int]) -> tuple[int, str, str]:
    """Sort key of a ``((label, fill), count)`` pair: most plants first, then by label and fill."""
    return (-item[1], item[0][0].casefold(), item[0][1])


def _phase_order(phase: tuple[str, str]) -> tuple[str, str]:
    """Sort key of a shown ``(label, fill)`` phase: by label, then fill."""
    return (phase[0].casefold(), phase[1])


def _phase_entries(drawn: list[_PlantMarker], labels: dict[str, str]) -> list[_LegendEntry]:
    """One entry per phase on the plan, at most :data:`_MAX_PHASE_ENTRIES`: the phases with the most plants (ties by
    name), listed by name; the others share one "+n more phases" entry. Each text is shortened to its column."""
    counts = Counter((marker.phase_label, marker.fill) for marker in drawn if marker.phase_label is not None)
    ranked = sorted(counts.items(), key=_phase_rank)
    shown = sorted((phase for phase, _count in ranked[:_MAX_PHASE_ENTRIES]), key=_phase_order)
    entries = [
        _LegendEntry("circle", fill, _TEXT_COLOR, _truncate(f"{labels['legend_phase']}: {label}", _LEGEND_LABEL_CHARS))
        for label, fill in shown
    ]
    hidden = len(ranked) - len(shown)
    if hidden > 0:
        more = labels["legend_more_phase" if hidden == 1 else "legend_more_phases"].format(n=hidden)
        entries.append(_LegendEntry("none", "none", "none", _truncate(more, _LEGEND_LABEL_CHARS)))
    return entries


def _plant_legend(markers: dict[str, list[_PlantMarker]], labels: dict[str, str]) -> Iterator[_LegendEntry]:
    """The plant entries: the uniform symbol if any plant has no phase colour, then the phases, rings and badges that
    are on the plan, each in a fixed order."""
    drawn = [marker for bed in markers.values() for marker in bed]
    if any(marker.phase_label is None for marker in drawn):
        yield _LegendEntry("circle", _PLANT_COLOR, _PLANT_COLOR, labels["legend_plant"])
    yield from _phase_entries(drawn, labels)
    states = [marker.state for marker in drawn if marker.state is not None]
    lifecycles = {state.lifecycle for state in states}
    for lifecycle in LIFECYCLES:
        if lifecycle in lifecycles:
            ring = _RING_STYLE[lifecycle]
            yield _LegendEntry(
                "circle",
                _RING_SWATCH_FILL if ring.disc_opacity > 0 else "none",
                _TEXT_COLOR,
                labels[f"ring_{lifecycle}"],
                dash=ring.dash,
                dash_unit_mm=_RING_DASH_MM,
                width_mm=ring.width_mm,
                fill_opacity=ring.disc_opacity if 0 < ring.disc_opacity < 1 else None,
            )
    badges = {state.attention[0].reason for state in states if state.attention}
    for code in ATTENTION_PRIORITY:
        if code in badges:
            yield _LegendEntry("badge", _BADGE_STYLE[code][0], _BADGE_OUTLINE, labels[f"badge_{code}"], badge=code)


def _legend(
    view: GardenPlanView,
    options: PlanSvgOptions,
    labels: dict[str, str],
    *,
    counters: bool,
    markers: dict[str, list[_PlantMarker]],
) -> Iterator[_LegendEntry]:
    layers = options.layers
    if PlanSvgLayer.BEDS in layers:
        # Only what ``_bed_layer`` draws: areas, not lines or points.
        present = {
            loc.bed_status
            for loc in view.locations
            if loc.geometry is not None and not isinstance(loc.geometry, PolylineGeometry | PointGeometry)
        }
        for status in (BedStatus.ACTIVE, BedStatus.PLANNED, BedStatus.RETIRED):
            if status in present:
                fill, stroke, dash = _BED_STYLE[status]
                yield _LegendEntry("box", fill, stroke, labels[_BED_LABEL_KEY[status]], dash)
    if PlanSvgLayer.OBJECTS in layers:
        # First appearance order, each type once.
        seen = {obj.object_type: None for obj in view.garden_objects if not obj.off_site}
        for object_type in seen:
            fill, stroke = _OBJECT_STYLE[object_type]
            yield _LegendEntry("box", fill, stroke, labels[f"type_{object_type.value}"])
    if PlanSvgLayer.SLOTS in layers and view.slots:
        yield _LegendEntry("circle", "none", _PLANT_COLOR, labels["legend_slot"])
    if PlanSvgLayer.PLANTS in layers and view.plants:
        if counters:
            yield _LegendEntry("box", _PLANT_COLOR, _PLANT_COLOR, labels["legend_plants_counter"])
        elif markers:
            yield from _plant_legend(markers, labels)
        else:
            yield _LegendEntry("circle", _PLANT_COLOR, _PLANT_COLOR, labels["legend_plant"])


# ── Layout ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Layout:
    scale: int
    pad: float  # metres
    canvas_w_mm: float
    plan_h_mm: float
    strip_h_mm: float
    legend_cols: int

    @property
    def canvas_h_mm(self) -> float:
        return self.plan_h_mm + self.strip_h_mm


def _layout_at(scale: int, extent: _Extent, legend_count: int) -> _Layout:
    pad = _PAD_MM * scale / 1000.0
    plan_w_mm = (extent.width + 2 * pad) * 1000.0 / scale
    plan_h_mm = (extent.height + 2 * pad) * 1000.0 / scale
    canvas_w_mm = max(plan_w_mm, _MIN_CANVAS_MM)
    cols = max(1, int(canvas_w_mm // _LEGEND_COLUMN_MM))
    rows = math.ceil(legend_count / cols) if legend_count else 0
    return _Layout(scale, pad, canvas_w_mm, plan_h_mm, _STRIP_BASE_MM + rows * _LEGEND_ROW_MM, cols)


def _fits(layout: _Layout, available_w: float, available_h: float) -> bool:
    # 0.1 mm of slack: the SVG and the page figure carry sizes rounded to 0.01 mm, which must not tip a plan that
    # fits to the next page.
    return layout.canvas_w_mm <= available_w - 0.1 and layout.canvas_h_mm <= available_h - 0.1


def choose_layout(extent: _Extent, legend_count: int, options: PlanSvgOptions) -> tuple[_Layout, bool]:
    """The layout at the requested scale, or the finest step at which plan and strip fit the page.

    Returns the layout and whether it fits. A requested scale is never changed — it either fits or does not,
    and the caller decides what a misfit means (the PDF refuses, the stand-alone SVG has no page).
    """
    page_w, page_h = page_size_mm(options.paper, options.orientation)
    available_w = page_w - 2 * PAGE_MARGIN_MM
    available_h = page_h - 2 * PAGE_MARGIN_MM - options.header_mm
    if options.scale is not None:
        layout = _layout_at(options.scale, extent, legend_count)
        return layout, _fits(layout, available_w, available_h)
    for scale in SCALE_STEPS:
        layout = _layout_at(scale, extent, legend_count)
        if _fits(layout, available_w, available_h):
            return layout, True
    return _layout_at(SCALE_STEPS[-1], extent, legend_count), False


# ── Drawing ───────────────────────────────────────────────────────────────────


class _Canvas:
    """Plan metres → SVG units: x grows right, y grows **up** in the plan and down on the canvas."""

    def __init__(self, extent: _Extent, layout: _Layout) -> None:
        self.layout = layout
        self._origin_x = extent.min_x - layout.pad
        self._origin_y = extent.max_y + layout.pad
        plan_w_mm = (extent.width + 2 * layout.pad) * 1000.0 / layout.scale
        self._shift_x = (layout.canvas_w_mm - plan_w_mm) / 2.0 * layout.scale

    @property
    def scale(self) -> int:
        return self.layout.scale

    @property
    def frame(self) -> PlanFrame:
        return PlanFrame(self._origin_x, self._origin_y, self._shift_x / self.layout.scale, self.layout.scale)

    def paper(self, millimetres: float) -> float:
        """A length on the printed page, in SVG units."""
        return millimetres * self.layout.scale

    def x(self, metres: float) -> float:
        return (metres - self._origin_x) * 1000.0 + self._shift_x

    def y(self, metres: float) -> float:
        return (self._origin_y - metres) * 1000.0

    def point(self, p: tuple[float, float]) -> tuple[float, float]:
        return (self.x(p[0]), self.y(p[1]))

    def points(self, vertices: tuple[tuple[float, float], ...] | list[tuple[float, float]]) -> str:
        return " ".join(f"{_num(self.x(px))},{_num(self.y(py))}" for px, py in vertices)

    @property
    def strip_top(self) -> float:
        return self.layout.plan_h_mm * self.layout.scale


def _vertices(geometry: Geometry) -> tuple[tuple[float, float], ...]:
    shape = to_shape(geometry)
    if isinstance(shape, CircleShape):
        raise ValueError("a circle has no vertices")
    return tuple(shape.vertices)


def _shape_node(
    canvas: _Canvas,
    geometry: Geometry,
    *,
    fill: str,
    stroke: str,
    dash: str | None = None,
    key: str | None = None,
    line_mm: float = 0.35,
) -> _Node:
    stroke_width = canvas.paper(line_mm)
    common: dict[str, AttributeValue] = {}
    if key:
        common["data-key"] = key
    if isinstance(geometry, PolylineGeometry):
        return _Node(
            "polyline",
            {
                "points": canvas.points(_vertices(geometry)),
                "fill": "none",
                "stroke": stroke,
                "stroke-width": max(geometry.width_m * 1000.0, stroke_width),
                "stroke-linejoin": "round",
                "stroke-linecap": "round",
                **common,
            },
        )
    attributes: dict[str, AttributeValue] = {"fill": fill, "stroke": stroke, "stroke-width": stroke_width, **common}
    if dash:
        attributes["stroke-dasharray"] = " ".join(_num(canvas.paper(float(part) * 0.4)) for part in dash.split())
    if isinstance(geometry, CircleGeometry):
        shape = to_shape(geometry)
        assert isinstance(shape, CircleShape)  # noqa: S101 - narrowing for the type checker
        return _Node(
            "circle",
            {
                "cx": canvas.x(shape.center[0]),
                "cy": canvas.y(shape.center[1]),
                "r": shape.radius_m * 1000.0,
                **attributes,
            },
        )
    if isinstance(geometry, PointGeometry):
        x, y = geometry.origin
        return _Node(
            "circle", {"cx": canvas.x(x), "cy": canvas.y(y), "r": POINT_OBJECT_RADIUS_M * 1000.0, **attributes}
        )
    return _Node("polygon", {"points": canvas.points(_vertices(geometry)), **attributes})


def _truncate(text: str, max_chars: int) -> str:
    cleaned = " ".join(clean_text(text).split())
    return cleaned if len(cleaned) <= max_chars else cleaned[: max(1, max_chars - 1)].rstrip() + "…"


def _label_node(canvas: _Canvas, geometry: Geometry, text: str, *, key: str | None) -> _Node | None:
    """The name at the object's label anchor (GP-UX-047): a polygon's pole of inaccessibility, a rect's or circle's
    centre - the point the editor uses too (``label_anchor``, shared vectors) - shortened with "…" to the room a
    centred label has there."""
    cleaned = " ".join(clean_text(text).split())
    if not cleaned:
        return None
    anchor = label_anchor(geometry)
    width_mm = anchor.width_m * 1000.0 / canvas.scale
    max_chars = max(3, int(width_mm / (_LABEL_MM * _GLYPH_WIDTH_EM)))
    cx, cy = anchor.point
    attributes: dict[str, AttributeValue] = {
        "x": canvas.x(cx),
        "y": canvas.y(cy),
        "font-size": canvas.paper(_LABEL_MM),
        "font-family": _FONT,
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "fill": _TEXT_COLOR,
    }
    if key:
        attributes["data-key"] = key
    return _Node("text", attributes, [_truncate(cleaned, max_chars)])


def _bed_layer(canvas: _Canvas, locations: list[Location]) -> _Node:
    layer = _el("g", id="layer-beds")
    drawn = [
        loc
        for loc in locations
        if loc.geometry is not None and not isinstance(loc.geometry, PolylineGeometry | PointGeometry)
    ]
    # Large areas first so a bed inside a greenhouse is drawn on top of it.
    drawn.sort(key=lambda loc: (loc.z_order, -(loc.area_m2 or 0.0)))
    for loc in drawn:
        assert loc.geometry is not None  # noqa: S101 - filtered above
        fill, stroke, dash = _BED_STYLE[loc.bed_status]
        shape = _shape_node(canvas, loc.geometry, fill=fill, stroke=stroke, dash=dash, key=loc.key)
        shape.children.append(_el("title", [loc.name]))
        layer.add(shape)
    return layer


def _object_layer(canvas: _Canvas, objects: list[GardenObject], extent: _Extent) -> _Node:
    layer = _el("g", id="layer-objects")
    for obj in sorted(objects, key=lambda o: o.z_order):
        left, bottom, right, top = _geometry_box(obj.geometry)
        if obj.off_site and (
            right < extent.min_x or left > extent.max_x or top < extent.min_y or bottom > extent.max_y
        ):
            continue
        fill, stroke = _OFF_SITE_STYLE if obj.off_site else _OBJECT_STYLE[obj.object_type]
        shape = _shape_node(canvas, obj.geometry, fill=fill, stroke=stroke, key=obj.key)
        if obj.label:
            shape.children.append(_el("title", [obj.label]))
        layer.add(shape)
    return layer


def _grid_layer(canvas: _Canvas, extent: _Extent, accent_free: str = _GRID_COLOR) -> _Node:
    layer = _el("g", id="layer-grid")
    pitch = next((m for m in (1, 5, 10, 50, 100, 500) if m * 1000.0 / canvas.scale >= _GRID_MIN_PITCH_MM), 500)
    width = canvas.paper(0.1)
    start_x = math.ceil(extent.min_x / pitch) * pitch
    x = float(start_x)
    top, bottom = canvas.y(extent.max_y), canvas.y(extent.min_y)
    while x <= extent.max_x + 1e-9:
        layer.add(
            _el("line", x1=canvas.x(x), y1=top, x2=canvas.x(x), y2=bottom, stroke=accent_free, stroke_width=width)
        )
        x += pitch
    y = float(math.ceil(extent.min_y / pitch) * pitch)
    left, right = canvas.x(extent.min_x), canvas.x(extent.max_x)
    while y <= extent.max_y + 1e-9:
        layer.add(
            _el("line", x1=left, y1=canvas.y(y), x2=right, y2=canvas.y(y), stroke=accent_free, stroke_width=width)
        )
        y += pitch
    return layer


def _slot_point(slot: PlanSlotView) -> tuple[float, float] | None:
    geometry = slot.plan_geometry
    if geometry is None:
        return None
    if geometry["kind"] == "point":
        origin = geometry["origin"]
        return (float(origin[0]), float(origin[1]))
    points = geometry["points"]
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def _slot_layer(canvas: _Canvas, slots: list[PlanSlotView]) -> _Node:
    layer = _el("g", id="layer-slots")
    radius = canvas.paper(0.5)
    for slot in slots:
        geometry = slot.plan_geometry
        if geometry is None:
            continue
        if geometry["kind"] == "point":
            x, y = _slot_point(slot) or (0.0, 0.0)
            layer.add(
                _el(
                    "circle",
                    cx=canvas.x(x),
                    cy=canvas.y(y),
                    r=radius,
                    fill="none",
                    stroke=_PLANT_COLOR,
                    stroke_width=canvas.paper(0.15),
                    data_key=slot.key,
                )
            )
        else:
            vertices = [(float(p[0]), float(p[1])) for p in geometry["points"]]
            tag = "polygon" if geometry["kind"] == "polygon" else "polyline"
            layer.add(
                _el(
                    tag,
                    points=canvas.points(vertices),
                    fill="none",
                    stroke=_PLANT_COLOR,
                    stroke_width=canvas.paper(0.15),
                    data_key=slot.key,
                )
            )
    return layer


def _bedded_plants(
    plants: list[PlantShortInfo],
    beds: dict[str, Location],
    slot_beds: dict[str, str],
    slot_points: dict[str, tuple[float, float] | None],
) -> Iterator[tuple[str, tuple[float, float] | None, PlantShortInfo]]:
    """``(bed key, slot point or None, plant)`` for every plant standing in a drawn bed, in plan order; a plant in no
    drawn bed is left out."""
    for plant in plants:
        bed_key = plant.location_key or slot_beds.get(plant.slot_key or "")
        bed = beds.get(bed_key or "")
        if bed is None or bed.key is None:
            continue
        point = slot_points.get(plant.slot_key or "") if plant.slot_key else None
        yield (bed.key, point, plant)


def _plant_positions(view: GardenPlanView) -> dict[str, list[tuple[tuple[float, float], PlantShortInfo]]]:
    """Plant marker positions per bed: the plant's slot, or — for a slotless plant — a sunflower spread that stays
    inside the bed's bounding box (an ellipse of 40 % of its half-extent), however many plants stand there."""
    slot_points = {slot.key: _slot_point(slot) for slot in view.slots}
    slot_beds = {slot.key: slot.location_key for slot in view.slots}
    beds = {loc.key: loc for loc in view.locations if loc.key and loc.geometry is not None}
    placed: dict[str, list[tuple[tuple[float, float], PlantShortInfo]]] = {}
    resolved = list(_bedded_plants(view.plants, beds, slot_beds, slot_points))
    slotless: Counter[str] = Counter(bed_key for bed_key, point, _plant in resolved if point is None)
    seen: dict[str, int] = {}
    for bed_key, point, plant in resolved:
        if point is None:
            geometry = beds[bed_key].geometry
            assert geometry is not None  # noqa: S101 - beds are filtered on it
            min_x, min_y, max_x, max_y = bounding_box(geometry)
            cx, cy = centroid(geometry)
            index = seen.get(bed_key, 0)
            seen[bed_key] = index + 1
            fraction = math.sqrt((index + 0.5) / slotless[bed_key])
            angle = index * 2.399963  # golden angle
            point = (
                cx + 0.4 * (max_x - min_x) * fraction * math.cos(angle),
                cy + 0.4 * (max_y - min_y) * fraction * math.sin(angle),
            )
        placed.setdefault(bed_key, []).append((point, plant))
    return placed


def _plant_markers(view: GardenPlanView, marks: PlantStateMarks | None, locale: str) -> dict[str, list[_PlantMarker]]:
    """The plant symbols per bed, each with its state and disc colour when ``marks`` carries one."""
    return {
        bed_key: [_marker_of(plant, point, marks, locale) for point, plant in placed]
        for bed_key, placed in _plant_positions(view).items()
    }


def _badge_node(canvas: _Canvas, code: AttentionCode, x: float, y: float, radius: float) -> _Node:
    """The one attention badge: outline and glyph of :data:`_BADGE_STYLE`, placed at ``(x, y)`` and scaled to
    ``radius`` (SVG units). Stroke widths are given in the badge's own -1…1 box, so they shrink with the scale."""
    fill, outline, glyph = _BADGE_STYLE[code]
    line = _fine(canvas.paper(0.12) / radius)
    return _el(
        "g",
        [
            _el("path", d=outline, fill=fill, stroke=_BADGE_OUTLINE, stroke_width=line),
            _el(
                "path",
                d=glyph,
                fill="none",
                stroke=_BADGE_OUTLINE,
                stroke_width=line,
                stroke_linecap="round",
                stroke_linejoin="round",
            ),
        ],
        transform=f"translate({_num(x)} {_num(y)}) scale({_fine(radius)})",
    )


def _ring_attributes(canvas: _Canvas, ring: _RingStyle, fill: str) -> dict[str, AttributeValue]:
    attributes: dict[str, AttributeValue] = {
        "fill": fill if ring.disc_opacity > 0 else "none",
        "stroke": _TEXT_COLOR,
        "stroke-width": canvas.paper(ring.width_mm),
    }
    if 0 < ring.disc_opacity < 1:
        attributes["fill-opacity"] = f"{ring.disc_opacity:g}"
    if ring.dash:
        attributes["stroke-dasharray"] = " ".join(
            _num(canvas.paper(float(part) * _RING_DASH_MM)) for part in ring.dash.split()
        )
    return attributes


def _stated_marker(canvas: _Canvas, marker: _PlantMarker, state: PlantVisualState, radius: float) -> list[_Node]:
    """Disc in the phase colour, ring of the lifecycle and, when the plant needs attention, the most urgent badge."""
    x, y = canvas.x(marker.point[0]), canvas.y(marker.point[1])
    nodes = [
        _Node(
            "circle",
            {"cx": x, "cy": y, "r": radius, **_ring_attributes(canvas, _RING_STYLE[state.lifecycle], marker.fill)},
        )
    ]
    if state.attention:
        offset = radius * _BADGE_OFFSET_SHARE
        nodes.append(
            _badge_node(canvas, state.attention[0].reason, x + offset, y - offset, radius * _BADGE_RADIUS_SHARE)
        )
    return nodes


def _plant_layer(
    canvas: _Canvas, view: GardenPlanView, markers: dict[str, list[_PlantMarker]], *, counters: bool
) -> _Node:
    layer = _el("g", id="layer-plants")
    beds = {loc.key: loc for loc in view.locations if loc.key}
    if counters:
        for bed_key, points in markers.items():
            bed = beds[bed_key]
            assert bed.geometry is not None  # noqa: S101 - positions are built from beds with a geometry
            # Under the bed's name, which sits at the label anchor (GP-UX-047).
            cx, cy = label_anchor(bed.geometry).point
            layer.add(
                _el(
                    "text",
                    [f"{len(points)}"],
                    x=canvas.x(cx),
                    y=canvas.y(cy) + canvas.paper(_LABEL_MM * 1.2),
                    font_size=canvas.paper(_LABEL_MM),
                    font_family=_FONT,
                    font_weight="bold",
                    text_anchor="middle",
                    fill=_PLANT_COLOR,
                    data_key=bed_key,
                )
            )
        return layer
    radius = max(0.08 * 1000.0, canvas.paper(0.6))
    stated_radius = max(0.1 * 1000.0, canvas.paper(1.0))
    for bed_markers in markers.values():
        for marker in bed_markers:
            if marker.state is not None:
                layer.add(*_stated_marker(canvas, marker, marker.state, stated_radius))
                continue
            px, py = marker.point
            layer.add(_el("circle", cx=canvas.x(px), cy=canvas.y(py), r=radius, fill=_PLANT_COLOR, fill_opacity="0.85"))
    return layer


def _label_layer(canvas: _Canvas, view: GardenPlanView, layers: frozenset[PlanSvgLayer]) -> _Node:
    layer = _el("g", id="layer-labels")
    if PlanSvgLayer.BEDS in layers:
        for loc in view.locations:
            if loc.geometry is None or isinstance(loc.geometry, PolylineGeometry | PointGeometry):
                continue
            label = _label_node(canvas, loc.geometry, loc.name, key=loc.key)
            if label is not None:
                layer.add(label)
    if PlanSvgLayer.OBJECTS in layers:
        for obj in view.garden_objects:
            if obj.label and not isinstance(obj.geometry, PolylineGeometry | PointGeometry):
                label = _label_node(canvas, obj.geometry, obj.label, key=obj.key)
                if label is not None:
                    layer.add(label)
    return layer


def _boundary_node(canvas: _Canvas, view: GardenPlanView, accent: str) -> _Node:
    layer = _el("g", id="layer-boundary")
    boundary = view.plan.boundary if view.plan is not None else None
    if boundary is not None:
        layer.add(_shape_node(canvas, boundary, fill="none", stroke=accent, line_mm=0.7))
    return layer


def _format_metres(value: int, labels: dict[str, str]) -> str:
    return f"{value} {labels['metre']}"


def _scale_bar(canvas: _Canvas, labels: dict[str, str], y_top: float) -> _Node:
    layer = _el("g", id="scale-bar")
    length_m = next((n for n in reversed(_NICE_LENGTHS_M) if n * 1000.0 / canvas.scale <= 50.0), _NICE_LENGTHS_M[0])
    total = length_m * 1000.0
    height = canvas.paper(2.0)
    left = canvas.paper(5.0)
    segments = 4
    for index in range(segments):
        layer.add(
            _el(
                "rect",
                x=left + total / segments * index,
                y=y_top,
                width=total / segments,
                height=height,
                fill="#212121" if index % 2 == 0 else "#ffffff",
                stroke="#212121",
                stroke_width=canvas.paper(0.2),
            )
        )
    text_y = y_top + height + canvas.paper(3.2)
    for fraction, text in (
        (0, "0"),
        (0.5, str(length_m // 2) if length_m % 2 == 0 else f"{length_m / 2:g}"),
        (1, _format_metres(length_m, labels)),
    ):
        layer.add(
            _el(
                "text",
                [text],
                x=left + total * fraction,
                y=text_y,
                font_size=canvas.paper(_LABEL_MM),
                font_family=_FONT,
                text_anchor="middle",
                fill=_TEXT_COLOR,
            )
        )
    return layer


def _north_arrow(canvas: _Canvas, view: GardenPlanView, labels: dict[str, str], y_top: float) -> _Node:
    angle = view.plan.north_angle_deg if view.plan is not None else 0.0
    size = canvas.paper(14.0)
    cx = canvas.layout.canvas_w_mm * canvas.scale - canvas.paper(12.0)
    cy = y_top + size / 2
    group = _el("g", id="north-arrow", transform=f"rotate({_num(angle)} {_num(cx)} {_num(cy)})")
    half = size / 2
    arrow_points = " ".join(
        f"{_num(px)},{_num(py)}"
        for px, py in (
            (cx, cy - half),
            (cx + half * 0.45, cy + half * 0.6),
            (cx, cy + half * 0.25),
            (cx - half * 0.45, cy + half * 0.6),
        )
    )
    group.add(
        _el(
            "polygon",
            points=arrow_points,
            fill="#212121",
            stroke="#212121",
            stroke_width=canvas.paper(0.2),
        ),
        _el(
            "text",
            [labels["north"]],
            x=cx,
            y=cy - half - canvas.paper(1.0),
            font_size=canvas.paper(3.5),
            font_family=_FONT,
            font_weight="bold",
            text_anchor="middle",
            fill=_TEXT_COLOR,
        ),
    )
    return group


def _legend_layer(canvas: _Canvas, entries: list[_LegendEntry], y_top: float) -> _Node:
    layer = _el("g", id="legend")
    cols = canvas.layout.legend_cols
    for index, entry in enumerate(entries):
        column, row = index % cols, index // cols
        x = canvas.paper(5.0 + column * _LEGEND_COLUMN_MM)
        y = y_top + canvas.paper(row * _LEGEND_ROW_MM)
        swatch_w, swatch_h = canvas.paper(_LEGEND_SWATCH_MM), canvas.paper(3.0)
        if entry.badge is not None:
            layer.add(_badge_node(canvas, entry.badge, x + swatch_w / 2, y + swatch_h / 2, canvas.paper(1.4)))
        elif entry.swatch == "circle":
            circle = _el(
                "circle",
                cx=x + swatch_w / 2,
                cy=y + swatch_h / 2,
                r=canvas.paper(1.2),
                fill=entry.fill,
                stroke=entry.stroke,
                stroke_width=canvas.paper(entry.width_mm),
            )
            if entry.fill_opacity is not None:
                circle.attributes["fill-opacity"] = f"{entry.fill_opacity:g}"
            if entry.dash:
                circle.attributes["stroke-dasharray"] = " ".join(
                    _num(canvas.paper(float(part) * entry.dash_unit_mm)) for part in entry.dash.split()
                )
            layer.add(circle)
        elif entry.swatch == "box":
            rect = _el(
                "rect",
                x=x,
                y=y,
                width=swatch_w,
                height=swatch_h,
                fill=entry.fill,
                stroke=entry.stroke,
                stroke_width=canvas.paper(0.25),
            )
            if entry.dash:
                rect.attributes["stroke-dasharray"] = " ".join(
                    _num(canvas.paper(float(part) * entry.dash_unit_mm)) for part in entry.dash.split()
                )
            layer.add(rect)
        layer.add(
            _el(
                "text",
                [entry.label],
                x=x + swatch_w + canvas.paper(_LEGEND_TEXT_GAP_MM),
                y=y + swatch_h / 2,
                font_size=canvas.paper(_LABEL_MM),
                font_family=_FONT,
                dominant_baseline="middle",
                fill=_TEXT_COLOR,
            )
        )
    return layer


# ── Entry point ───────────────────────────────────────────────────────────────


def render_plan_svg(view: GardenPlanView, options: PlanSvgOptions, marks: PlantStateMarks | None = None) -> PlanSvg:
    """Draw the plan as one allowlisted SVG document.

    ``marks`` carries the plants' states and phase names (#2489); without it every plant is the uniform symbol.
    From :data:`PLANT_COUNTER_THRESHOLD` plants on the marks are not read: each bed shows its counter.

    Raises:
        PlanError: ``plan.empty`` (422) when the plan has neither a boundary nor a placed bed or object.
    """
    if not _HEX_COLOR.match(options.accent):
        raise ValueError("accent must be #rrggbb")
    labels = _LABELS.get(options.locale, _LABELS["de"])
    extent = _extent_of(view)
    if extent is None:
        raise PlanError("plan.empty", "The plan has no boundary and nothing placed on it.", status_code=422)
    counters = PlanSvgLayer.PLANTS in options.layers and len(view.plants) >= PLANT_COUNTER_THRESHOLD
    markers = (
        _plant_markers(view, None if counters else marks, options.locale)
        if PlanSvgLayer.PLANTS in options.layers
        else {}
    )
    entries = list(_legend(view, options, labels, counters=counters, markers=markers))
    layout, fits = choose_layout(extent, len(entries), options)
    canvas = _Canvas(extent, layout)

    width_units = layout.canvas_w_mm * layout.scale
    height_units = layout.canvas_h_mm * layout.scale
    root = _el(
        "svg",
        xmlns=_SVG_NAMESPACE,
        view_box=f"0 0 {_num(width_units)} {_num(height_units)}",
        width=f"{layout.canvas_w_mm:.2f}mm",
        height=f"{layout.canvas_h_mm:.2f}mm",
        role="img",
        data_scale=str(layout.scale),
    )
    root.add(_el("title", [view.site_name]), _el("desc", [f"{labels['desc']} 1:{layout.scale}"]))
    layers = options.layers
    if PlanSvgLayer.GRID in layers:
        root.add(_grid_layer(canvas, extent))
    if PlanSvgLayer.BEDS in layers:
        root.add(_bed_layer(canvas, view.locations))
    if PlanSvgLayer.OBJECTS in layers:
        root.add(_object_layer(canvas, view.garden_objects, extent))
    root.add(_boundary_node(canvas, view, options.accent))
    if PlanSvgLayer.SLOTS in layers:
        root.add(_slot_layer(canvas, view.slots))
    if PlanSvgLayer.PLANTS in layers:
        root.add(_plant_layer(canvas, view, markers, counters=counters))
    if PlanSvgLayer.LABELS in layers:
        root.add(_label_layer(canvas, view, layers))
    strip_top = canvas.strip_top + canvas.paper(3.0)
    root.add(_scale_bar(canvas, labels, strip_top), _north_arrow(canvas, view, labels, strip_top))
    root.add(_legend_layer(canvas, entries, strip_top + canvas.paper(14.0)))

    suggest_a3 = options.paper is PlanPaper.A4 and (layout.scale > A3_SUGGESTION_ABOVE or not fits)
    return PlanSvg(
        svg=root.render(),
        scale=layout.scale,
        width_mm=round(layout.canvas_w_mm, 2),
        height_mm=round(layout.canvas_h_mm, 2),
        fits=fits,
        suggest_a3=suggest_a3,
        plant_counters=counters,
        frame=canvas.frame,
    )


__all__ = [
    "A3_SUGGESTION_ABOVE",
    "ALLOWED_ATTRIBUTES",
    "ALLOWED_ELEMENTS",
    "DEFAULT_ACCENT",
    "DEFAULT_LAYERS",
    "PAGE_MARGIN_MM",
    "PDF_HEADER_MM",
    "PLANT_COUNTER_THRESHOLD",
    "SCALE_STEPS",
    "PlanFrame",
    "PlanOrientation",
    "PlanPaper",
    "PlanSvg",
    "PlanSvgLayer",
    "PlanSvgOptions",
    "PlantStateMarks",
    "escape_attribute",
    "escape_text",
    "page_size_mm",
    "parse_scale",
    "render_plan_svg",
]
