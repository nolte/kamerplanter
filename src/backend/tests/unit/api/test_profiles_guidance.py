"""The profiles nutrient response surfaces the E8 pH-gating guidance (Issue #383)."""

from app.api.v1.profiles.router import _nutrient_response_with_guidance
from app.domain.models.phase import NutrientProfile


def test_optimal_ph_keeps_micros_available():
    resp = _nutrient_response_with_guidance(
        NutrientProfile(phase_key="p", npk_ratio=(3, 1, 2), target_ec_ms=1.5, target_ph=6.2)
    )
    assert resp.micros_available is True
    assert resp.feed is True
    assert "optimal" in resp.ph_note


def test_high_ph_locks_out_micros():
    resp = _nutrient_response_with_guidance(
        NutrientProfile(phase_key="p", npk_ratio=(1, 3, 2), target_ec_ms=1.8, target_ph=7.3)
    )
    assert resp.micros_available is False
    assert "lock out" in resp.ph_note


def test_flush_profile_marks_no_feed():
    resp = _nutrient_response_with_guidance(
        NutrientProfile(phase_key="p", npk_ratio=(0, 0, 0), target_ec_ms=0.0, target_ph=6.0)
    )
    assert resp.feed is False
    assert resp.micros_available is True
