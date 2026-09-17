"""#1489 — the profile bootstrap hands the engine the family NAME, not its stored key.

``Species.family_key`` holds the ArangoDB ``_key`` of a ``botanical_families``
document — server-assigned and numeric (``seed_data.py`` builds
``family_map[name] = created.key``, and ``BaseArangoRepository._to_doc`` pops
``_key`` before every insert). ``FAMILY_CARE_MAP`` is keyed by the family **name**
(``"Cactaceae"``). Handing it the stored key matches nothing, so
``auto_generate_profile`` fell back to the ``TROPICAL`` 7-day preset for every
plant created since #1440 — a Cactaceae included, and the profile is created once
and read thereafter, so those values were the plant's for good.

Three places already knew the resolution (the v0048 backfill, the AI context
builder) and the one path every new plant walks did not. The resolution is now
**one** function — :func:`resolve_care_inputs` — and the service resolves its own
inputs instead of trusting what a caller passed, because "the caller passes it"
is what drifted: the tenant care dashboard passed a hard-coded ``None`` and the
four internal ``may_create=True`` call sites passed nothing at all.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.enums import CareStyleType
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.services.care_reminder_service import CareInputs, CareReminderService, resolve_care_inputs

#: The numeric shape ArangoDB hands back for a ``botanical_families`` document.
_FAMILY_KEY = "123456789"


def _species(**overrides) -> Species:
    data = {
        "scientific_name": "Echinocactus grusonii",
        "family_key": _FAMILY_KEY,
    }
    data.update(overrides)
    return Species(**data)


def _service(species: Species | None, *, families: dict[str, str] | None = None):
    """A service wired exactly as ``dependencies.get_care_reminder_service`` wires it."""
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = None
    care_repo.create_profile.side_effect = lambda profile: profile.model_copy(update={"key": "cp-new"})

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = PlantInstance(
        key="p1",
        instance_id="p-1",
        planted_on=date(2026, 1, 1),
        species_key="sp-1" if species is not None else "",
        tenant_key="tenant-a",
    )
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = species

    known = {_FAMILY_KEY: "Cactaceae"} if families is None else families
    resolver = MagicMock(side_effect=lambda family_key: known.get(family_key))

    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        plant_repo=plant_repo,
        species_repo=species_repo,
        family_name_resolver=resolver,
    )
    return service, care_repo, resolver


class TestTheBootstrapResolvesTheFamily:
    def test_a_cactus_gets_cactus_presets_not_tropical(self) -> None:
        """The defect, at the tier that produced it.

        Red against the old code: the service handed ``species.family_key`` —
        ``"123456789"`` — to ``FAMILY_CARE_MAP`` and got ``TROPICAL``.
        """
        service, _repo, _resolver = _service(_species())

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.care_style == CareStyleType.CACTUS
        assert profile.watering_interval_days == 21, "the CACTUS preset, not the 7-day TROPICAL one"

    def test_the_read_path_resolves_it_too(self) -> None:
        """``may_create=False`` generates without storing — and what it shows the
        user must be what the write path would store, or the care tab renders
        presets the plant will never have."""
        service, repo, _resolver = _service(_species())

        profile = service.get_or_create_profile("p1", may_create=False)

        assert profile.care_style == CareStyleType.CACTUS
        repo.create_profile.assert_not_called()

    def test_reset_resolves_it_too(self) -> None:
        """``POST …/reset-profile`` re-seeds from the presets; it took the same two
        client-supplied values and the frontend sends neither."""
        service, repo, _resolver = _service(_species())
        repo.get_profile_by_plant_key.return_value = None
        repo.update_profile.side_effect = lambda key, profile: profile

        reset = service.reset_profile("p1")

        assert reset.care_style == CareStyleType.CACTUS

    def test_an_unresolvable_family_key_is_not_passed_on_verbatim(self) -> None:
        """A dangling numeric key names no family, and the engine refuses it.

        The fallback is ``TROPICAL`` either way; what must not happen is the key
        reaching the engine, because that is the defect wearing a different value.
        """
        service, _repo, _resolver = _service(_species(), families={})

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.care_style == CareStyleType.TROPICAL

    def test_a_family_stored_as_a_name_is_used_verbatim(self) -> None:
        """An installation whose species carry family *names* in ``family_key`` is
        served — the case v0048 has handled since it shipped."""
        service, _repo, _resolver = _service(_species(family_key="Cactaceae"), families={})

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.care_style == CareStyleType.CACTUS

    def test_a_plant_without_a_species_still_gets_a_profile(self) -> None:
        service, _repo, _resolver = _service(None)

        profile = service.get_or_create_profile("p1", may_create=True)

        assert profile.care_style == CareStyleType.TROPICAL

    def test_the_family_catalogue_is_read_once_per_key(self) -> None:
        """The resolution is memoised per service instance: the dashboard generates
        presets for every unprofiled plant of the tenant in one call."""
        service, _repo, resolver = _service(_species())

        service.get_or_create_profile("p1", may_create=False)
        service.get_or_create_profile("p1", may_create=False)

        assert resolver.call_count == 1


class TestTheResolverIsOne:
    """The resolution is a function, not a method, so the v0050 repair migration
    (which reads its families in one batched AQL pass) shares it rather than
    growing a fourth copy."""

    def test_it_maps_the_key_through_the_catalogue(self) -> None:
        inputs = resolve_care_inputs(_species(), resolve_family_name={_FAMILY_KEY: "Cactaceae"}.get)

        assert inputs == CareInputs(family_name="Cactaceae")

    def test_a_missing_species_resolves_to_nothing(self) -> None:
        assert resolve_care_inputs(None, resolve_family_name=lambda key: "Cactaceae") == CareInputs(family_name=None)

    def test_a_species_without_a_family_never_asks_the_catalogue(self) -> None:
        resolver = MagicMock()

        assert resolve_care_inputs(_species(family_key=None), resolve_family_name=resolver).family_name is None
        resolver.assert_not_called()


class TestTheEngineRefusesAKey:
    """Decision 3 of the group analysis: a ``_key`` reaching ``botanical_family`` is
    a type error, and a type error that answers with plausible presets is how this
    defect survived two releases."""

    def test_a_numeric_family_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="botanical_family"):
            CareReminderEngine().auto_generate_profile(botanical_family=_FAMILY_KEY, plant_key="p1")

    def test_a_family_name_is_accepted(self) -> None:
        """The control — a guard that refused everything would satisfy the case
        above and break every caller."""
        profile = CareReminderEngine().auto_generate_profile(botanical_family="Cactaceae", plant_key="p1")

        assert profile.care_style == CareStyleType.CACTUS

    def test_no_family_at_all_is_accepted(self) -> None:
        assert CareReminderEngine().auto_generate_profile(plant_key="p1").care_style == CareStyleType.TROPICAL
