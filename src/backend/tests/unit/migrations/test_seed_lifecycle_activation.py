"""Assert the REQ-003 E4/E6 engine branches are activated by seed data.

The engine logic for E4 (``growth_determinacy`` suppresses auto-advance out of a
productive phase for indeterminate species) and E6 (a ``vegetative -> bolting``
transition rule flagged ``is_premature`` records that on the phase history) is
implemented and unit-tested elsewhere. This module guards that seed data actually
*activates* those branches — otherwise they can never fire in production.

Both checks are performed at the seed-data + loader level without touching the
database: the override map / YAML rule is fed through the exact model
construction the loaders use.
"""

from __future__ import annotations

from pathlib import Path

import yaml

import app.migrations
from app.common.enums import GrowthDeterminacy, TransitionTriggerType
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase import PhaseTransitionRule

_SEED = Path(app.migrations.__file__).parent / "seed_data"

# Spec-named indeterminate species (REQ-003 E4). Only those actually carrying a
# lifecycle seed are asserted here.
_EXPECTED_INDETERMINATE = {
    "Solanum lycopersicum",
    "Capsicum annuum",
    "Cucumis sativus",
}


def _lifecycle_overrides() -> dict[str, dict]:
    data = yaml.safe_load((_SEED / "species.yaml").read_text()) or {}
    return data.get("lifecycle_overrides", {}) or {}


def _outdoor_lifecycles() -> list[dict]:
    data = yaml.safe_load((_SEED / "lifecycles_outdoor.yaml").read_text()) or {}
    return data.get("lifecycles", [])


# ── E4: growth_determinacy activation ────────────────────────────────────────


def test_expected_species_marked_indeterminate_in_overrides() -> None:
    overrides = _lifecycle_overrides()
    for species in _EXPECTED_INDETERMINATE:
        assert species in overrides, f"{species} missing a lifecycle_overrides entry"
        assert overrides[species].get("growth_determinacy") == "indeterminate", (
            f"{species} is not marked growth_determinacy=indeterminate"
        )


def test_override_determinacy_builds_indeterminate_lifecycle() -> None:
    """The override value flows into a valid LifecycleConfig with the enum set —
    this is exactly what the seed loaders construct."""
    overrides = _lifecycle_overrides()
    for species in _EXPECTED_INDETERMINATE:
        determinacy = overrides[species].get("growth_determinacy")
        lc = LifecycleConfig(
            species_key="dummy",
            growth_determinacy=GrowthDeterminacy(determinacy) if determinacy else None,
        )
        assert lc.growth_determinacy is GrowthDeterminacy.INDETERMINATE


def test_determinacy_not_mass_annotated() -> None:
    """Guard against over-annotation: determinacy is only set where intended."""
    overrides = _lifecycle_overrides()
    annotated = {name for name, ov in overrides.items() if ov.get("growth_determinacy")}
    assert annotated == _EXPECTED_INDETERMINATE, (
        f"unexpected growth_determinacy annotations: {annotated ^ _EXPECTED_INDETERMINATE}"
    )


# ── E6: premature-bolting transition rule activation ─────────────────────────


def _spinach_entry() -> dict:
    entry = next((e for e in _outdoor_lifecycles() if e["scientific_name"] == "Spinacia oleracea"), None)
    assert entry is not None, "Spinacia oleracea lifecycle seed is missing"
    return entry


def test_spinach_has_bolting_phase() -> None:
    entry = _spinach_entry()
    phase_names = {p["name"] for p in entry["phases"]}
    assert "bolting" in phase_names, "bolting phase must exist as the premature-bolt target"


def test_spinach_has_premature_bolting_rule() -> None:
    entry = _spinach_entry()
    rules = entry.get("transition_rules", [])
    bolt_rules = [r for r in rules if r["from_phase"] == "vegetative" and r["to_phase"] == "bolting"]
    assert len(bolt_rules) == 1, "expected exactly one vegetative -> bolting rule"
    assert bolt_rules[0].get("is_premature") is True, "the bolting rule must be flagged is_premature"


def test_bolting_rule_builds_premature_transition_rule() -> None:
    """The YAML rule flows into a valid PhaseTransitionRule with is_premature=True —
    what seed_lifecycles_outdoor.py constructs and persists."""
    entry = _spinach_entry()
    rule_data = next(r for r in entry["transition_rules"] if r["to_phase"] == "bolting")
    rule = PhaseTransitionRule(
        from_phase_key="veg-key",
        to_phase_key="bolt-key",
        trigger_type=TransitionTriggerType(rule_data.get("trigger_type", "manual")),
        is_premature=rule_data.get("is_premature", False),
    )
    assert rule.is_premature is True
    assert rule.trigger_type is TransitionTriggerType.PHOTOPERIOD_BASED
