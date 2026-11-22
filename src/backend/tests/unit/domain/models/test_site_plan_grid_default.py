"""REQ-053 WP 10.8 (GP-FR-182, §9.8): the snap grid a new plan starts with follows the site type."""

from __future__ import annotations

import pytest

from app.common.enums import INDOOR_PLAN_SITE_TYPES, WEATHER_RELEVANT_SITE_TYPES, SiteType
from app.domain.models.site import DEFAULT_GRID_M, DEFAULT_INDOOR_GRID_M, default_grid_m_for


def test_the_indoor_plan_types_are_the_flat_the_windowsill_and_the_grow_tent() -> None:
    assert frozenset({SiteType.INDOOR, SiteType.WINDOWSILL, SiteType.GROW_TENT}) == INDOOR_PLAN_SITE_TYPES


def test_every_site_type_is_either_an_indoor_plan_or_weather_relevant() -> None:
    """One set derived from the other: a new site type cannot fall between them."""
    assert INDOOR_PLAN_SITE_TYPES.isdisjoint(WEATHER_RELEVANT_SITE_TYPES)
    assert frozenset(SiteType) == INDOOR_PLAN_SITE_TYPES | WEATHER_RELEVANT_SITE_TYPES


@pytest.mark.parametrize("site_type", [SiteType.INDOOR, SiteType.WINDOWSILL, SiteType.GROW_TENT])
def test_an_indoor_plan_starts_on_5_cm(site_type: SiteType) -> None:
    assert default_grid_m_for(site_type) == DEFAULT_INDOOR_GRID_M == 0.05


@pytest.mark.parametrize("site_type", [SiteType.OUTDOOR, SiteType.GREENHOUSE, SiteType.BALCONY])
def test_a_garden_plan_still_starts_on_10_cm(site_type: SiteType) -> None:
    assert default_grid_m_for(site_type) == DEFAULT_GRID_M == 0.10
