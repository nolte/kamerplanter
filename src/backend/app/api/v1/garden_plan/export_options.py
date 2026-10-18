"""The query vocabulary of the garden-plan renderers (REQ-053 GP-API-006/007, GP-NFR-052 (c)).

``scale``, ``paper``, ``orientation``, ``layers`` and ``locale`` are enums or fixed patterns, and ``color`` is
``#rrggbb`` — nothing a caller types reaches the SVG writer as free text (the one free text, the plan's own
names, comes from the database and is escaped by the writer). The SVG route and the PDF route read the same
dependency, so the two cannot drift apart on what a valid request is.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Query

from app.common.exceptions import ValidationError
from app.domain.engines.plan_svg_engine import (
    DEFAULT_ACCENT,
    DEFAULT_LAYERS,
    SCALE_STEPS,
    PlanOrientation,
    PlanPaper,
    PlanSvgLayer,
    PlanSvgOptions,
    parse_scale,
)

_SCALE_PATTERN = "^(auto|" + "|".join(f"1:{step}" for step in SCALE_STEPS) + ")$"
_DEFAULT_LAYERS = ",".join(layer.value for layer in PlanSvgLayer if layer in DEFAULT_LAYERS)
_LAYER_VALUES = ", ".join(layer.value for layer in PlanSvgLayer)


def _layers(raw: str) -> frozenset[PlanSvgLayer]:
    names = [part.strip() for part in raw.split(",") if part.strip()]
    try:
        return frozenset(PlanSvgLayer(name) for name in names)
    except ValueError:
        raise ValidationError(
            f"layers accepts {_LAYER_VALUES}.",
            details=[{"field": "layers", "reason": "Unknown layer.", "code": "validation.invalid"}],
        ) from None


def plan_svg_options(
    scale: Annotated[
        str,
        Query(
            pattern=_SCALE_PATTERN,
            description="auto, or one of the twelve steps 1:20 … 1:500 (GP-FR-142). auto picks the finest that fits.",
        ),
    ] = "auto",
    paper: Annotated[
        PlanPaper, Query(description="Paper the plan must fit; A3 is suggested when A4 would need coarser than 1:200.")
    ] = PlanPaper.A4,
    orientation: Annotated[PlanOrientation, Query(description="Page orientation.")] = PlanOrientation.LANDSCAPE,
    layers: Annotated[
        str,
        Query(
            max_length=64,
            pattern=r"^[a-z,]*$",
            description=(
                f"Comma-separated layers to draw: {_LAYER_VALUES}. "
                "Boundary, scale bar, north arrow and legend are always drawn."
            ),
        ),
    ] = _DEFAULT_LAYERS,
    locale: Annotated[
        str, Query(pattern="^(de|en)$", description="Language of the legend and labels: de or en.")
    ] = "de",
    color: Annotated[
        str,
        Query(pattern="^#[0-9A-Fa-f]{6}$", description="Accent colour of the boundary as #rrggbb (send the # as %23)."),
    ] = DEFAULT_ACCENT,
) -> PlanSvgOptions:
    return PlanSvgOptions(
        scale=parse_scale(scale),
        paper=paper,
        orientation=orientation,
        layers=_layers(layers),
        locale=locale,
        accent=color,
    )
