"""Follow-up crop recommendation for a bed (REQ-053 GP-FR-133, §16.3): the order of the feeder cycle, nothing else.

Pure functions, no I/O. The cycle is heavy feeder -> medium feeder -> light feeder -> green manure or fallow ->
heavy feeder again, read on ``nutrient_demand`` and ``plan_role`` of the rows the bed timeline already carries
(:class:`~app.domain.engines.crop_rotation_validator.TimelineEntry`). It decides **which step comes next**; it never
names a nitrogen amount, a fertiliser dose or a yield (E-10, review "hint only"). A species without a stored
``nutrient_demand`` never qualifies for a feeder step: there is no silent default, a missing value means the species
does not appear.

Which *families* may follow is not decided here: the service intersects the step with the ``rotation_after`` edges
of the catalogue (REQ-001) and the pause a family still has to keep in the bed.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from app.common.enums import NutrientDemand, PlanRole
from app.domain.engines.crop_rotation_validator import TimelineEntry
from app.domain.models.species import Species

#: The next step of the cycle: a feeder level, or ``restoring`` (green manure or fallow, no feeder level of its own).
SuccessionTarget = Literal["heavy_feeder", "medium_feeder", "light_feeder", "restoring"]

#: Strongest feeder first, the order a mixed bed is read in.
_DEMAND_ORDER: tuple[NutrientDemand, ...] = (
    NutrientDemand.HEAVY_FEEDER,
    NutrientDemand.MEDIUM_FEEDER,
    NutrientDemand.LIGHT_FEEDER,
)

_NEXT: dict[str, SuccessionTarget] = {
    NutrientDemand.HEAVY_FEEDER.value: "medium_feeder",
    NutrientDemand.MEDIUM_FEEDER.value: "light_feeder",
    NutrientDemand.LIGHT_FEEDER.value: "restoring",
}

#: After a green manure or a fallow year the cycle starts again with a heavy feeder.
AFTER_RESTORING: SuccessionTarget = "heavy_feeder"


@dataclass(frozen=True)
class PreviousYear:
    """What the bed carried in the latest year that has any entry."""

    year: int
    #: ``main_crop`` when at least one main crop stood there, else ``restoring`` (green manure / fallow only).
    step: Literal["main_crop", "restoring"]
    #: The strongest ``nutrient_demand`` of the main crops; ``None`` when no main crop states one (or it was restoring).
    nutrient_demand: str | None
    #: Families of that year (main crops and green manure), without duplicates, in the order of the rows.
    family_keys: tuple[str, ...]


def _distinct(keys: Iterable[str]) -> tuple[str, ...]:
    """The keys without duplicates, in first-seen order."""
    return tuple({key: None for key in keys})


def previous_year(rows: Sequence[TimelineEntry]) -> PreviousYear | None:
    """The latest year with any row of the timeline, or ``None`` for a bed without recorded history."""
    if not rows:
        return None
    year = max(row.year for row in rows)
    of_year = [row for row in rows if row.year == year]
    mains = [row for row in of_year if row.plan_role == PlanRole.MAIN_CROP.value]
    families = _distinct(row.family_key for row in of_year if row.family_key is not None)
    if not mains:
        return PreviousYear(year, "restoring", None, families)
    stated = {row.nutrient_demand for row in mains if row.nutrient_demand is not None}
    strongest = next((level.value for level in _DEMAND_ORDER if level.value in stated), None)
    return PreviousYear(year, "main_crop", strongest, families)


def basis_family_keys(rows: Sequence[TimelineEntry], previous: PreviousYear) -> tuple[str, ...]:
    """The families whose ``rotation_after`` successors are the candidates.

    After a main-crop year these are the families of that year. After a restoring year (green manure / fallow only)
    the edges of the green-manure family say little - the curated successors belong to crop families - so the families
    of the latest year that had a main crop are used instead (the cycle continues from the crop, not from the cover).
    """
    if previous.step == "main_crop":
        return previous.family_keys
    crop_years = [row.year for row in rows if row.plan_role == PlanRole.MAIN_CROP.value and row.family_key is not None]
    if not crop_years:
        return previous.family_keys
    latest = max(crop_years)
    return _distinct(
        row.family_key
        for row in rows
        if row.year == latest and row.plan_role == PlanRole.MAIN_CROP.value and row.family_key is not None
    )


def planting_year(previous: PreviousYear, today_year: int) -> int:
    """The year the recommendation is for: this year, or the next one when the latest recorded year is this year."""
    return max(today_year, previous.year + 1)


def target_after(previous: PreviousYear) -> SuccessionTarget | None:
    """The next step of the cycle, or ``None`` when the previous main crop stated no feeder level.

    A missing level is not guessed: the caller reports it (``demand_unknown``) instead of recommending anything.
    """
    if previous.step == "restoring":
        return AFTER_RESTORING
    if previous.nutrient_demand is None:
        return None
    # not `.get`: the write-route call graph counts every untyped attribute call (test_write_route_gates ceiling)
    return _NEXT[previous.nutrient_demand] if previous.nutrient_demand in _NEXT else None  # noqa: SIM401


def species_fits(species: Species, target: SuccessionTarget) -> bool:
    """Whether the species belongs to the step: a stored ``nutrient_demand`` equal to the feeder level, or - for the
    restoring step - ``green_manure_suitable``. No stored level, no match."""
    if target == "restoring":
        return species.green_manure_suitable
    return species.nutrient_demand is not None and species.nutrient_demand.value == target


def pause_held_back(last_year: int | None, pause_years: int | None, today_year: int) -> bool:
    """Whether a family still has to keep its pause: it stood in the bed ``last_year`` and the pause is known and
    not over. An unknown pause (``None``) holds nothing back - the caller says the pause is unknown."""
    if last_year is None or pause_years is None:
        return False
    return today_year - last_year < pause_years
