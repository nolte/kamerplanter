"""Tests for the D8 engine-role mapping (REQ-003 Lifecycle-Audit)."""

from app.domain.engines.phase_role_map import (
    CORE_PHASES,
    core_phase,
    is_productive_phase,
    is_rest_phase,
)


def test_core_phases_map_to_themselves() -> None:
    for name in CORE_PHASES:
        assert core_phase(name) == name


def test_succulent_rest_phases_map_to_dormancy() -> None:
    for name in ("winter_rest", "summer_rest", "cool_rest", "winter_hull_change", "rest_after_bloom"):
        assert core_phase(name) == "dormancy"
        assert is_rest_phase(name) is True


def test_geophyte_and_special_phases_map_to_core() -> None:
    assert core_phase("sprouting") == "bud_break"
    assert core_phase("tuber_formation") == "fruit_development"
    assert core_phase("pup_establishment") == "seedling"
    assert core_phase("young_palm") == "vegetative"
    assert core_phase("leaf_phase") == "active_growth"
    assert core_phase("autumn_ripening") == "ripening"
    assert core_phase("dry_storage") == "dormancy"


def test_productive_classification() -> None:
    assert is_productive_phase("autumn_ripening") is True  # -> ripening
    assert is_productive_phase("fruiting") is True  # -> fruit_development
    assert is_productive_phase("winter_rest") is False


def test_unknown_phase_maps_to_itself() -> None:
    assert core_phase("some_unknown_phase") == "some_unknown_phase"
    assert is_rest_phase("some_unknown_phase") is False
