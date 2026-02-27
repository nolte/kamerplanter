"""Unit tests for the resistance engine."""

from datetime import datetime, timedelta

import pytest

from app.domain.engines.resistance_engine import (
    MAX_CONSECUTIVE,
    ROTATION_WINDOW_DAYS,
    ResistanceManager,
)


@pytest.fixture
def engine():
    return ResistanceManager()


def _make_application(ingredient: str, days_ago: int) -> dict:
    """Helper to create an application dict with a given ingredient applied N days ago."""
    return {
        "active_ingredient": ingredient,
        "applied_at": datetime.now() - timedelta(days=days_ago),
    }


class TestValidateTreatment:
    """Tests for the validate_treatment method."""

    def test_no_recent_applications_is_safe(self, engine):
        """No recent applications means the treatment is safe."""
        is_safe, msg = engine.validate_treatment([], "Pyrethrin")
        assert is_safe is True
        assert msg == ""

    def test_different_ingredients_is_safe(self, engine):
        """Applications of a different ingredient do not count."""
        apps = [
            _make_application("Neem Oil", 10),
            _make_application("Neem Oil", 20),
            _make_application("Neem Oil", 30),
        ]
        is_safe, msg = engine.validate_treatment(apps, "Pyrethrin")
        assert is_safe is True
        assert msg == ""

    def test_below_threshold_is_safe_no_warning(self, engine):
        """Applications below MAX_CONSECUTIVE - 1 give no warning."""
        apps = [_make_application("Pyrethrin", i * 5) for i in range(MAX_CONSECUTIVE - 2)]
        is_safe, msg = engine.validate_treatment(apps, "Pyrethrin")
        assert is_safe is True
        assert msg == ""

    def test_at_warning_threshold(self, engine):
        """At MAX_CONSECUTIVE - 1 applications, a warning is returned but still safe."""
        apps = [_make_application("Pyrethrin", i * 5) for i in range(MAX_CONSECUTIVE - 1)]
        is_safe, msg = engine.validate_treatment(apps, "Pyrethrin")
        assert is_safe is True
        assert "Warning" in msg
        assert "Pyrethrin" in msg

    def test_at_max_consecutive_is_unsafe(self, engine):
        """At MAX_CONSECUTIVE applications, the treatment is blocked."""
        apps = [_make_application("Pyrethrin", i * 5) for i in range(MAX_CONSECUTIVE)]
        is_safe, msg = engine.validate_treatment(apps, "Pyrethrin")
        assert is_safe is False
        assert "Resistance risk" in msg

    def test_none_ingredient_is_always_safe(self, engine):
        """A treatment with no active ingredient (non-chemical) is always safe."""
        apps = [_make_application("Pyrethrin", 5)]
        is_safe, msg = engine.validate_treatment(apps, None)
        assert is_safe is True
        assert msg == ""

    def test_old_applications_outside_window_ignored(self, engine):
        """Applications older than ROTATION_WINDOW_DAYS are not counted."""
        apps = [
            _make_application("Pyrethrin", ROTATION_WINDOW_DAYS + 10),
            _make_application("Pyrethrin", ROTATION_WINDOW_DAYS + 20),
            _make_application("Pyrethrin", ROTATION_WINDOW_DAYS + 30),
        ]
        is_safe, msg = engine.validate_treatment(apps, "Pyrethrin")
        assert is_safe is True
        assert msg == ""

    def test_iso_string_applied_at(self, engine):
        """applied_at as ISO string is correctly parsed."""
        apps = [
            {
                "active_ingredient": "Pyrethrin",
                "applied_at": (datetime.now() - timedelta(days=5)).isoformat(),
            }
            for _ in range(MAX_CONSECUTIVE)
        ]
        is_safe, msg = engine.validate_treatment(apps, "Pyrethrin")
        assert is_safe is False


class TestSuggestAlternatives:
    """Tests for the suggest_alternatives method."""

    def test_empty_available_returns_empty(self, engine):
        """No available treatments means no alternatives."""
        result = engine.suggest_alternatives([], [])
        assert result == []

    def test_sorts_by_ipm_hierarchy(self, engine):
        """Alternatives are sorted by IPM hierarchy: cultural > biological > mechanical > chemical."""
        treatments = [
            {"name": "Spray", "treatment_type": "chemical", "active_ingredient": "X"},
            {"name": "Trap", "treatment_type": "mechanical", "active_ingredient": None},
            {"name": "Companion", "treatment_type": "cultural", "active_ingredient": None},
            {"name": "BioAgent", "treatment_type": "biological", "active_ingredient": None},
        ]
        result = engine.suggest_alternatives([], treatments)
        assert len(result) == 4
        assert result[0]["name"] == "Companion"
        assert result[1]["name"] == "BioAgent"
        assert result[2]["name"] == "Trap"
        assert result[3]["name"] == "Spray"

    def test_excludes_overused_ingredients(self, engine):
        """Ingredients that have been used MAX_CONSECUTIVE times are excluded."""
        apps = [_make_application("Pyrethrin", i * 5) for i in range(MAX_CONSECUTIVE)]
        treatments = [
            {"name": "Pyrethrin Spray", "treatment_type": "chemical", "active_ingredient": "Pyrethrin"},
            {"name": "Neem Spray", "treatment_type": "chemical", "active_ingredient": "Neem Oil"},
        ]
        result = engine.suggest_alternatives(apps, treatments)
        assert len(result) == 1
        assert result[0]["name"] == "Neem Spray"

    def test_no_internal_keys_in_output(self, engine):
        """Internal scoring keys (_hierarchy_score, _usage_count) are stripped."""
        treatments = [
            {"name": "Bio", "treatment_type": "biological", "active_ingredient": None},
        ]
        result = engine.suggest_alternatives([], treatments)
        assert len(result) == 1
        assert "_hierarchy_score" not in result[0]
        assert "_usage_count" not in result[0]

    def test_prefers_less_used_same_hierarchy(self, engine):
        """Among same hierarchy level, prefer less recently used ingredients."""
        apps = [_make_application("A", 5), _make_application("A", 10)]
        treatments = [
            {"name": "T1", "treatment_type": "chemical", "active_ingredient": "A"},
            {"name": "T2", "treatment_type": "chemical", "active_ingredient": "B"},
        ]
        result = engine.suggest_alternatives(apps, treatments)
        assert result[0]["name"] == "T2"
        assert result[1]["name"] == "T1"
