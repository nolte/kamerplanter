"""#1481 — the species' WateringGuide reaches the engine in production.

``auto_generate_profile`` documents ``watering_guide`` as "tier 1, highest
priority" ahead of the botanical family and the ``TROPICAL`` fallback. Measured
2026-09-17 on ``origin/develop``: ``grep -rn "watering_guide=" src/backend/app/``
finds the engine's own signature and a migration docstring — **no production
caller**. Every stored profile in every installation therefore came from tier 2 or
tier 3, and the tier the docstring calls highest existed only in the docstring.

Either the guide shapes the profile or the parameter is dead. The operator decided
to wire it (group analysis ``2026-09-17-care-profile-bootstrap``, decision: "#1481
= verdrahten"), so the same :func:`resolve_care_inputs` that resolves the family
carries it, and the docstring tier becomes a statement about the code.

**The cultivar override comes first**, and that is measured rather than assumed:
``WateringService.get_volume_suggestion`` (``watering_service.py:321-325``) already
resolves ``cultivar.watering_guide_override`` ahead of ``species.watering_guide``,
``cultivar_seed.py`` fills it from the plant-info YAML, and two services
disagreeing about which guide governs one plant is the defect this group exists to
end — one field, one precedence.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import CareStyleType, WateringMethod
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Cultivar, SeasonalWateringAdjustment, Species, WateringGuide
from app.domain.services.care_reminder_service import CareReminderService, resolve_care_inputs

_FAMILY_KEY = "123456789"


def _guide(**overrides) -> WateringGuide:
    data = {
        "interval_days": 4,
        "watering_method": WateringMethod.BOTTOM_WATER,
        "water_quality_hint": "Rainwater only",
        "practical_tip": "Keep the substrate evenly moist",
    }
    data.update(overrides)
    return WateringGuide(**data)


def _species(**overrides) -> Species:
    data = {"scientific_name": "Echinocactus grusonii", "family_key": _FAMILY_KEY}
    data.update(overrides)
    return Species(**data)


def _service(species: Species | None, *, cultivar: Cultivar | None = None):
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = None
    care_repo.create_profile.side_effect = lambda profile: profile.model_copy(update={"key": "cp-new"})
    care_repo.update_profile.side_effect = lambda key, profile: profile

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = PlantInstance(
        key="p1",
        instance_id="p-1",
        planted_on=date(2026, 1, 1),
        species_key="sp-1" if species is not None else "",
        cultivar_key="cv-1" if cultivar is not None else None,
        tenant_key="tenant-a",
    )
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = species
    species_repo.get_cultivar_by_key.return_value = cultivar

    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        plant_repo=plant_repo,
        species_repo=species_repo,
        family_name_resolver={_FAMILY_KEY: "Cactaceae"}.get,
    )
    return service, care_repo


class TestTheGuideReachesTheEngine:
    def test_a_species_guide_shapes_the_new_profile(self) -> None:
        """Red against the old code: nothing passed a guide, so the 21-day CACTUS
        family preset stood even for a species that documents four days."""
        service, _repo = _service(_species(watering_guide=_guide()))

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.watering_interval_days == 4
        assert profile.watering_method == WateringMethod.BOTTOM_WATER
        assert profile.water_quality_hint == "Rainwater only"
        assert profile.notes == "Keep the substrate evenly moist"

    def test_the_family_still_decides_the_care_style(self) -> None:
        """The guide overrides the watering fields, not the style: fertilising,
        repotting and pest intervals stay the family's (engine tiers 1 over 2)."""
        service, _repo = _service(_species(watering_guide=_guide()))

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.care_style == CareStyleType.CACTUS
        assert profile.fertilizing_interval_days == 30, "the CACTUS preset is untouched by the guide"

    def test_without_a_guide_the_family_preset_stands(self) -> None:
        """The control. A wiring that invented a guide would satisfy the case above
        and give every plant the same values again — from the other end."""
        service, _repo = _service(_species())

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.watering_interval_days == 21, "the CACTUS family preset"
        assert profile.notes is None

    def test_a_cultivar_override_wins_over_the_species_guide(self) -> None:
        """Same precedence as ``WateringService.get_volume_suggestion``."""
        service, _repo = _service(
            _species(watering_guide=_guide(interval_days=4)),
            cultivar=Cultivar(name="Nana", species_key="sp-1", watering_guide_override=_guide(interval_days=9)),
        )

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.watering_interval_days == 9

    def test_a_cultivar_without_an_override_falls_back_to_the_species(self) -> None:
        service, _repo = _service(
            _species(watering_guide=_guide(interval_days=4)),
            cultivar=Cultivar(name="Nana", species_key="sp-1"),
        )

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.watering_interval_days == 4

    def test_the_read_path_shows_what_the_write_path_would_store(self) -> None:
        service, repo = _service(_species(watering_guide=_guide()))

        profile = service.get_or_create_profile("p1", may_create=False)

        assert profile.watering_interval_days == 4
        repo.create_profile.assert_not_called()

    def test_reset_re_seeds_from_the_guide(self) -> None:
        service, _repo = _service(_species(watering_guide=_guide()))

        assert service.reset_profile("p1").watering_interval_days == 4

    def test_the_winter_multiplier_comes_from_the_guide(self) -> None:
        """The engine derives it from the winter seasonal adjustment; without a
        caller passing a guide that computation had no input in production."""
        service, _repo = _service(
            _species(
                watering_guide=_guide(
                    interval_days=4,
                    seasonal_adjustments=[
                        SeasonalWateringAdjustment(months=[11, 12, 1, 2], interval_days=8, label="Winter"),
                    ],
                )
            )
        )

        assert service.get_or_create_profile("p1", may_create=True).winter_watering_multiplier == 2.0


class TestTheResolverCarriesIt:
    def test_the_species_guide_is_part_of_the_care_inputs(self) -> None:
        guide = _guide()

        inputs = resolve_care_inputs(_species(watering_guide=guide), resolve_family_name=lambda key: "Cactaceae")

        assert inputs.watering_guide is guide

    def test_no_species_carries_no_guide(self) -> None:
        assert resolve_care_inputs(None, resolve_family_name=lambda key: None).watering_guide is None

    def test_the_cultivar_override_is_preferred(self) -> None:
        override = _guide(interval_days=9)

        inputs = resolve_care_inputs(
            _species(watering_guide=_guide()),
            cultivar=Cultivar(name="Nana", species_key="sp-1", watering_guide_override=override),
            resolve_family_name=lambda key: "Cactaceae",
        )

        assert inputs.watering_guide is override


class TestTheDocstringTierIsBackedByACaller:
    """The AC that closes #1481 as a *claim*, not just as a behaviour.

    ``auto_generate_profile``'s docstring has called the guide "tier 1, highest
    priority" since it was written, while ``grep -rn "watering_guide=" app/`` found
    only the signature declaring it and a migration docstring explaining why it was
    not used. A docstring is the cheapest thing in a repository to keep true and the
    most expensive to trust when it is not — this walks the tree and requires a real
    production call site, so deleting the wiring reddens here even if every
    behavioural case above were deleted with it.
    """

    def test_a_production_caller_passes_the_guide(self) -> None:
        import ast
        from pathlib import Path

        app = Path(__file__).resolve().parents[4] / "app"
        callers = []
        for path in sorted(app.rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                if name != "auto_generate_profile":
                    continue
                if any(keyword.arg == "watering_guide" for keyword in node.keywords):
                    callers.append(f"{path.relative_to(app.parent).as_posix()}:{node.lineno}")

        assert callers, (
            "no production code passes `watering_guide=` — the engine's 'tier 1, "
            "highest priority' docstring then describes a parameter nothing fills, "
            "which is #1481"
        )
