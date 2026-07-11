"""SEC-001/SEC-003 — pin the documented effective identification settings.

These tests guard the deduplicated identification block in
:class:`app.config.settings.Settings`. Python keeps only the *last* assignment
for a field defined twice in a class body, so a re-introduced duplicate would
silently shadow the documented defaults. Pinning the *effective* values here
turns such a regression into a hard test failure (the duplicate's value would
differ from the one asserted below).
"""

from __future__ import annotations

from app.config.settings import Settings


def test_primary_adapter_default_is_plantnet_phase1():
    """REQ-029-A §0.1.1 — Phase-1 primary adapter is Pl@ntNet, not local_embedding.

    A duplicate definition previously shadowed this with ``"local_embedding"``;
    the effective default must be the documented Phase-1 value.
    """
    assert Settings().identification_primary_adapter == "plantnet"


def test_external_in_light_mode_default_is_false():
    """REQ-034 §4a.3 — the external path in Light mode is opt-in, off by default."""
    assert Settings().identification_external_in_light_mode is False


def test_rate_limit_per_user_day_has_sensible_floor():
    """SEC-003 — a per-user daily floor > 0 so one account cannot drain the quota."""
    assert Settings().identification_rate_limit_per_user_day > 0


def test_identification_fields_defined_exactly_once():
    """SEC-001 — no identification field is defined twice in the class body.

    ``model_fields`` collapses duplicates to one entry, so we instead assert the
    documented defaults survive intact. If a second block were re-added with the
    old values, at least one of these effective defaults would flip and fail.
    """
    settings = Settings()
    # The values that a re-introduced duplicate block historically clobbered.
    assert settings.identification_primary_adapter == "plantnet"
    assert settings.identification_external_in_light_mode is False
    assert settings.identification_confidence_auto_accept == 0.85
    assert settings.identification_confidence_min_show == 0.10
    assert settings.identification_max_image_size_mb == 5
    assert settings.identification_http_timeout == 60
    assert settings.identification_max_image_dimension == 1024
    # Fields that only existed in the (now removed) second block must still exist.
    assert settings.inference_service_enabled is False
    assert settings.plantnet_enabled is True
    assert settings.reference_image_min_usable == 5
