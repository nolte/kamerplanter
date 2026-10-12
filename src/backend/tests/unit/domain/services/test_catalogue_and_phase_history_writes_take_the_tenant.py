"""#2107 — species, cultivar, substrate and phase-history writes take the tenant themselves.

The catalogue slice of #2107. Before it:

* every species/cultivar/substrate write defaulted ``tenant_key=None`` — the
  "system context" of a seeder that, measured, writes through the repository and
  never calls these methods. A caller that forgot the tenant ran with no ownership
  gate at all, against a foreign tenant's row as much as its own;
* ``create_species`` took no tenant and trusted the ``tenant_key`` the route had
  set on the model — the model default is ``""``, so a forgotten stamp minted a
  *global* species;
* the phase-history writes loaded the plant unscoped and relied on the router's
  ``require_owned_plant``: the #948 check-then-act shape.

Per method: an omitted tenant does not run (``TypeError``, nothing written), a
foreign row is a 404 and writes nothing, a global seed row needs a platform admin
(403). Hybrid gate arms that already held before the slice are pinned here once
more on purpose, through the new required keywords, so a later "default it again"
edit fails in one place.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Cultivar, Species
from app.domain.models.substrate import MixComponent, Substrate, SubstrateBatch
from app.domain.services.phase_service import PhaseService
from app.domain.services.species_service import SpeciesService
from app.domain.services.substrate_service import SubstrateService

OWN = "t_own"
FOREIGN = "t_foreign"
LEAD: dict[str, Any] = {"caller_role": TenantRole.LEAD, "is_platform_admin": False}


def _raise_missing(entity: str, rows: dict[str, Any]) -> Callable[[str], Any]:
    def load(key: str) -> Any:
        if key not in rows:
            raise NotFoundError(entity, key)
        return rows[key]

    return load


# ── species and cultivars ────────────────────────────────────────────────────


def _species_service() -> tuple[SpeciesService, MagicMock]:
    species = {
        "sp_own": Species(_key="sp_own", scientific_name="Rosa canina", tenant_key=OWN),
        "sp_foreign": Species(_key="sp_foreign", scientific_name="Cannabis sativa", tenant_key=FOREIGN),
        "sp_global": Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
    }
    cultivars = {
        "cv_own": Cultivar(_key="cv_own", name="Own", species_key="sp_own", tenant_key=OWN),
        "cv_foreign": Cultivar(_key="cv_foreign", name="Foreign", species_key="sp_foreign", tenant_key=FOREIGN),
        "cv_global": Cultivar(_key="cv_global", name="Global", species_key="sp_global", tenant_key=""),
    }
    repo = MagicMock()
    repo.get_or_raise.side_effect = _raise_missing("Species", species)
    repo.get_cultivar_or_raise.side_effect = _raise_missing("Cultivar", cultivars)
    repo.is_granted_to.return_value = False
    repo.is_cultivar_granted_to.return_value = False
    repo.get_by_normalized_scientific_name_for_tenant.return_value = None
    repo.find_synonym_match_candidates.return_value = []
    repo.upsert_by_normalized_scientific_name.side_effect = lambda s: s
    repo.update.side_effect = lambda _key, s: s
    repo.update_cultivar.side_effect = lambda _key, c: c
    repo.create_cultivar.side_effect = lambda c: c
    return SpeciesService(repo, graph_repo=MagicMock()), repo


_SPECIES_WRITES: dict[str, Callable[..., Any]] = {
    "update_species": lambda svc, key, **kw: svc.update_species(key, Species(scientific_name="Edited name"), **kw),
    "delete_species": lambda svc, key, **kw: svc.delete_species(key, **kw),
    "update_cultivar": lambda svc, key, **kw: svc.update_cultivar(key, Cultivar(name="Edited", species_key=""), **kw),
    "delete_cultivar": lambda svc, key, **kw: svc.delete_cultivar(key, **kw),
}
_SPECIES_WRITE_REPO_CALL = {
    "update_species": "update",
    "delete_species": "delete",
    "update_cultivar": "update_cultivar",
    "delete_cultivar": "delete_cultivar",
}


def _row(method: str, owner: str) -> str:
    prefix = "cv" if "cultivar" in method else "sp"
    return f"{prefix}_{owner}"


@pytest.mark.parametrize("method", sorted(_SPECIES_WRITES))
def test_a_species_or_cultivar_write_without_a_tenant_does_not_run(method: str) -> None:
    service, repo = _species_service()
    with pytest.raises(TypeError):
        _SPECIES_WRITES[method](service, _row(method, "foreign"))

    getattr(repo, _SPECIES_WRITE_REPO_CALL[method]).assert_not_called()


@pytest.mark.parametrize("method", sorted(_SPECIES_WRITES))
def test_a_foreign_species_or_cultivar_is_a_404_and_writes_nothing(method: str) -> None:
    service, repo = _species_service()
    with pytest.raises(NotFoundError):
        _SPECIES_WRITES[method](service, _row(method, "foreign"), tenant_key=OWN, **LEAD)

    getattr(repo, _SPECIES_WRITE_REPO_CALL[method]).assert_not_called()


@pytest.mark.parametrize("method", sorted(_SPECIES_WRITES))
def test_a_global_species_or_cultivar_needs_a_platform_admin(method: str) -> None:
    service, repo = _species_service()
    with pytest.raises(ForbiddenError):
        _SPECIES_WRITES[method](service, _row(method, "global"), tenant_key=OWN, **LEAD)

    getattr(repo, _SPECIES_WRITE_REPO_CALL[method]).assert_not_called()


@pytest.mark.parametrize("method", sorted(_SPECIES_WRITES))
def test_an_own_species_or_cultivar_is_written(method: str) -> None:
    service, repo = _species_service()
    _SPECIES_WRITES[method](service, _row(method, "own"), tenant_key=OWN, **LEAD)

    getattr(repo, _SPECIES_WRITE_REPO_CALL[method]).assert_called_once()


def test_create_species_without_a_tenant_does_not_run() -> None:
    service, repo = _species_service()
    with pytest.raises(TypeError):
        service.create_species(Species(scientific_name="Mentha spicata"), **LEAD)  # type: ignore[call-arg]

    repo.upsert_by_normalized_scientific_name.assert_not_called()


def test_create_species_stamps_the_tenant_not_the_model_default() -> None:
    # Red before #2107: the service wrote whatever the model carried, and the model
    # default is "" — a global species minted by a caller that forgot to stamp it.
    service, repo = _species_service()
    created = service.create_species(Species(scientific_name="Mentha spicata"), tenant_key=OWN, **LEAD)

    assert created.tenant_key == OWN
    assert repo.upsert_by_normalized_scientific_name.call_args.args[0].tenant_key == OWN


def test_create_species_checks_the_default_plan_against_the_given_owner() -> None:
    # The keyed load of create_species is the default nutrient plan: another tenant's
    # private plan must not travel into this tenant's species.
    service, repo = _species_service()
    plans = MagicMock()
    plans.get_by_key.return_value = MagicMock(tenant_key=FOREIGN)
    service._nutrient_plan_repo = plans  # noqa: SLF001

    with pytest.raises(NotFoundError):
        service.create_species(
            Species(scientific_name="Mentha spicata", default_nutrient_plan_key="plan_foreign"),
            tenant_key=OWN,
            **LEAD,
        )

    repo.upsert_by_normalized_scientific_name.assert_not_called()


def test_create_cultivar_under_a_foreign_species_is_a_404() -> None:
    service, repo = _species_service()
    with pytest.raises(NotFoundError):
        service.create_cultivar(Cultivar(name="Sneaky", species_key="sp_foreign"), tenant_key=OWN, **LEAD)

    repo.create_cultivar.assert_not_called()


def test_create_cultivar_without_a_tenant_does_not_run() -> None:
    service, repo = _species_service()
    with pytest.raises(TypeError):
        service.create_cultivar(Cultivar(name="Sneaky", species_key="sp_foreign"), **LEAD)  # type: ignore[call-arg]

    repo.create_cultivar.assert_not_called()


def test_create_cultivar_stamps_the_tenant_it_resolved_the_parent_in() -> None:
    service, repo = _species_service()
    service.create_cultivar(Cultivar(name="Mine", species_key="sp_global"), tenant_key=OWN, **LEAD)

    assert repo.create_cultivar.call_args.args[0].tenant_key == OWN


# ── substrates, mixes and batches ────────────────────────────────────────────


def _substrate_service() -> tuple[SubstrateService, MagicMock]:
    substrates = {
        "s_own": Substrate(_key="s_own", name_de="Own mix", tenant_key=OWN),
        "s_foreign": Substrate(_key="s_foreign", name_de="Foreign mix", tenant_key=FOREIGN),
        "s_global": Substrate(_key="s_global", name_de="Global medium", tenant_key=""),
        "s_global_2": Substrate(_key="s_global_2", name_de="Global medium 2", tenant_key=""),
    }
    batches = {
        f"b_{owner}": SubstrateBatch(
            _key=f"b_{owner}",
            batch_id=owner,
            volume_liters=10,
            mixed_on=date(2026, 1, 1),
            substrate_key="s_global",
            tenant_key=tenant,
        )
        for owner, tenant in (("own", OWN), ("foreign", FOREIGN))
    }
    repo = MagicMock()
    repo.get_substrate_or_raise.side_effect = _raise_missing("Substrate", substrates)
    repo.get_batch_or_raise.side_effect = _raise_missing("SubstrateBatch", batches)
    for write in ("create_substrate", "create_batch"):
        getattr(repo, write).side_effect = lambda row: row
    for write in ("update_substrate", "update_batch"):
        getattr(repo, write).side_effect = lambda _key, row: row
    return SubstrateService(repo), repo


def _batch_body() -> SubstrateBatch:
    return SubstrateBatch(batch_id="edited", volume_liters=10, mixed_on=date(2026, 1, 1), substrate_key="s_global")


_SUBSTRATE_WRITES: dict[str, tuple[Callable[..., Any], str]] = {
    "update_substrate": (
        lambda svc, key, **kw: svc.update_substrate(f"s_{key}", Substrate(name_de="Edited"), **kw),
        "update_substrate",
    ),
    "delete_substrate": (lambda svc, key, **kw: svc.delete_substrate(f"s_{key}", **kw), "delete_substrate"),
    "update_batch": (lambda svc, key, **kw: svc.update_batch(f"b_{key}", _batch_body(), **kw), "update_batch"),
    "delete_batch": (lambda svc, key, **kw: svc.delete_batch(f"b_{key}", **kw), "delete_batch"),
    "create_batch": (
        lambda svc, key, **kw: svc.create_batch(
            SubstrateBatch(batch_id="new", volume_liters=10, mixed_on=date(2026, 1, 1), substrate_key=f"s_{key}"), **kw
        ),
        "create_batch",
    ),
    "create_mix": (
        lambda svc, key, **kw: svc.create_mix(
            [
                MixComponent(substrate_key=f"s_{key}", fraction=0.5),
                MixComponent(substrate_key="s_global", fraction=0.5),
            ],
            **kw,
        ),
        "create_substrate",
    ),
}


@pytest.mark.parametrize("method", sorted(_SUBSTRATE_WRITES))
def test_a_substrate_write_without_a_tenant_does_not_run(method: str) -> None:
    service, repo = _substrate_service()
    call, write = _SUBSTRATE_WRITES[method]
    with pytest.raises(TypeError):
        call(service, "foreign", **LEAD)

    getattr(repo, write).assert_not_called()


@pytest.mark.parametrize("method", sorted(_SUBSTRATE_WRITES))
def test_a_foreign_substrate_or_batch_is_a_404_and_writes_nothing(method: str) -> None:
    service, repo = _substrate_service()
    call, write = _SUBSTRATE_WRITES[method]
    with pytest.raises(NotFoundError):
        call(service, "foreign", tenant_key=OWN, **LEAD)

    getattr(repo, write).assert_not_called()


@pytest.mark.parametrize("method", ["update_substrate", "delete_substrate"])
def test_a_global_substrate_needs_a_platform_admin(method: str) -> None:
    service, repo = _substrate_service()
    call, write = _SUBSTRATE_WRITES[method]
    with pytest.raises(ForbiddenError):
        call(service, "global", tenant_key=OWN, **LEAD)

    getattr(repo, write).assert_not_called()


@pytest.mark.parametrize("method", ["create_batch", "create_mix"])
def test_a_substrate_create_is_owned_by_the_tenant_it_is_given(method: str) -> None:
    service, repo = _substrate_service()
    call, write = _SUBSTRATE_WRITES[method]
    call(service, "global_2" if method == "create_mix" else "own", tenant_key=OWN, **LEAD)

    assert getattr(repo, write).call_args.args[0].tenant_key == OWN


@pytest.mark.parametrize("method", ["update_batch", "delete_batch"])
def test_a_batch_write_without_a_role_does_not_run(method: str) -> None:
    # The batch role gate admitted ``caller_role=None`` as the system context; with the
    # role required, an omitted one is a TypeError instead of a skipped role check.
    service, repo = _substrate_service()
    call, write = _SUBSTRATE_WRITES[method]
    with pytest.raises(TypeError):
        call(service, "own", tenant_key=OWN, is_platform_admin=False)

    getattr(repo, write).assert_not_called()


# ── phase history of a plant ─────────────────────────────────────────────────


def _phase_service() -> tuple[PhaseService, MagicMock, MagicMock]:
    plants = {
        f"p_{owner}": PlantInstance(
            _key=f"p_{owner}",
            tenant_key=tenant,
            instance_id=owner,
            species_key="sp_global",
            plant_name=owner,
            planted_on=date(2026, 1, 1),
        )
        for owner, tenant in (("own", OWN), ("foreign", FOREIGN))
    }
    phase_repo = MagicMock()
    phase_repo.get_phase_history.return_value = [
        PhaseHistory(_key="h1", phase_key="veg", entered_at=datetime(2026, 1, 1, tzinfo=UTC)),
    ]
    phase_repo.update_phase_history.side_effect = lambda _key, h: h
    plant_repo = MagicMock()
    plant_repo.get_or_raise.side_effect = _raise_missing("PlantInstance", plants)
    return PhaseService(phase_repo, plant_repo), phase_repo, plant_repo


_HISTORY_WRITES: dict[str, Callable[..., Any]] = {
    "delete_phase_history": lambda svc, plant, **kw: svc.delete_phase_history(plant, "h1", **kw),
    "update_phase_history_dates": lambda svc, plant, **kw: svc.update_phase_history_dates(
        plant, "h1", datetime(2026, 1, 2, tzinfo=UTC), **kw
    ),
}


def _history_untouched(phase_repo: MagicMock, plant_repo: MagicMock) -> None:
    phase_repo.delete_phase_history.assert_not_called()
    phase_repo.update_phase_history.assert_not_called()
    plant_repo.update.assert_not_called()


@pytest.mark.parametrize("method", sorted(_HISTORY_WRITES))
def test_a_foreign_plants_history_is_a_404_and_writes_nothing(method: str) -> None:
    # Red before #2107: the service loaded the plant unscoped and wrote, trusting the
    # router's require_owned_plant to have run first.
    service, phase_repo, plant_repo = _phase_service()
    with pytest.raises(NotFoundError):
        _HISTORY_WRITES[method](service, "p_foreign", tenant_key=OWN)

    _history_untouched(phase_repo, plant_repo)


@pytest.mark.parametrize("method", sorted(_HISTORY_WRITES))
def test_an_empty_caller_tenant_owns_no_plant(method: str) -> None:
    service, phase_repo, plant_repo = _phase_service()
    with pytest.raises(NotFoundError):
        _HISTORY_WRITES[method](service, "p_own", tenant_key="")

    _history_untouched(phase_repo, plant_repo)


@pytest.mark.parametrize("method", sorted(_HISTORY_WRITES))
def test_a_history_write_without_a_tenant_does_not_run(method: str) -> None:
    service, phase_repo, plant_repo = _phase_service()
    with pytest.raises(TypeError):
        _HISTORY_WRITES[method](service, "p_own")

    _history_untouched(phase_repo, plant_repo)


def test_the_own_plants_history_is_written() -> None:
    service, phase_repo, _plant_repo = _phase_service()
    service.delete_phase_history("p_own", "h1", tenant_key=OWN)
    service.update_phase_history_dates("p_own", "h1", datetime(2026, 1, 2, tzinfo=UTC), tenant_key=OWN)

    phase_repo.delete_phase_history.assert_called_once_with("h1")
    assert phase_repo.update_phase_history.call_count == 1
