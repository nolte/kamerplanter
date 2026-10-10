"""An edit through the API keeps the fields its body does not carry.

``PUT /species/{key}``, ``PUT /growth-phases/{key}``, ``PUT /location-types/{key}``
and ``PUT /substrates/{key}`` rebuild the domain model from the request body
(``Model(**body.model_dump())``). Every model field the body schema does not
declare reached the repository at its **default**, and the merge-mode repositories
write every non-``None`` value they are handed:

* ``LocationType.is_system`` became ``False`` — the next ``DELETE`` removed a
  seeded system type the service's delete guard exists to protect.
* ``Substrate.is_mix`` / ``mix_components`` became ``False`` / ``[]`` — a mix
  turned into a plain substrate, usable as a component of a new mix.
* ``Species.traits`` / ``pruning_months`` / ``green_manure_suitable`` became
  ``[]`` / ``[]`` / ``False``.
* ``GrowthPhase.is_recurring`` / ``kc_source`` became ``False`` / ``""``.

The deployed ``app.main`` app, the real services and repository doubles that
record the model each update would write — the path a client takes. The same
class on the site / location / slot routes is pinned in
``test_site_edit_keeps_server_maintained_fields.py``; the class guard is
``tests/unit/guards/test_put_rebuild_keeps_fields_the_body_lacks.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_active_tenant_context, get_current_user, get_is_platform_admin
from app.common.dependencies import (
    get_family_repo,
    get_location_type_service,
    get_phase_service,
    get_species_service,
    get_substrate_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.location_type import LocationType
from app.domain.models.species import Species
from app.domain.models.substrate import MixComponent, Substrate
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.location_type_service import LocationTypeService
from app.domain.services.phase_service import PhaseService
from app.domain.services.species_service import SpeciesService
from app.domain.services.substrate_service import SubstrateService
from tests.support.grant_fakes import NoGrantsMixin

_TENANT = "tenant_own"


class _Store:
    """Holds rows by key and records the model each update would write."""

    def __init__(self, entity: str, rows: list) -> None:
        self._entity = entity
        self.rows = {row.key: row for row in rows}
        self.written: list = []

    def get(self, key: str):
        row = self.rows.get(key)
        if row is None:
            raise NotFoundError(self._entity, key)
        return row.model_copy(deep=True)

    def write(self, key: str, model):
        self.written.append(model)
        self.rows[key] = model.model_copy(update={"key": key}, deep=True)
        return self.rows[key]


class _LocationTypeRepo(_Store):
    def get_or_raise(self, key: str) -> LocationType:
        return self.get(key)

    def update(self, key: str, location_type: LocationType) -> LocationType:
        return self.write(key, location_type)

    def delete(self, key: str) -> bool:
        del self.rows[key]
        return True


class _SubstrateRepo(_Store):
    def get_substrate_or_raise(self, key: str) -> Substrate:
        return self.get(key)

    def update_substrate(self, key: str, substrate: Substrate) -> Substrate:
        return self.write(key, substrate)


class _SpeciesRepo(NoGrantsMixin, _Store):
    def get_or_raise(self, key: str) -> Species:
        return self.get(key)

    def update(self, key: str, species: Species) -> Species:
        return self.write(key, species)


class _PhaseRepo(_Store):
    def get_phase_or_raise(self, key: str) -> GrowthPhase:
        return self.get(key)

    def update_phase(self, key: str, phase: GrowthPhase) -> GrowthPhase:
        return self.write(key, phase)


@pytest.fixture
def location_types() -> _LocationTypeRepo:
    return _LocationTypeRepo(
        "LocationType",
        [
            LocationType(_key="lt_greenhouse", name="Gewächshaus", is_indoor=True, is_system=True, sort_order=1),
            LocationType(_key="lt_custom", name="Eigener Typ", is_system=False, sort_order=9),
        ],
    )


@pytest.fixture
def substrates() -> _SubstrateRepo:
    return _SubstrateRepo(
        "Substrate",
        [
            Substrate(
                _key="mix_own",
                name_de="Eigener Mix",
                tenant_key=_TENANT,
                is_mix=True,
                mix_components=[
                    MixComponent(substrate_key="sub_coco", fraction=0.7),
                    MixComponent(substrate_key="sub_perlite", fraction=0.3),
                ],
            ),
            Substrate(_key="sub_coco", name_de="Kokos", tenant_key=_TENANT),
        ],
    )


@pytest.fixture
def species() -> _SpeciesRepo:
    return _SpeciesRepo(
        "Species",
        [
            Species(
                _key="sp_own",
                scientific_name="Phacelia tanacetifolia",
                tenant_key=_TENANT,
                traits=["bee_friendly", "nitrogen_fixer"],
                pruning_months=[3, 9],
                green_manure_suitable=True,
                cultivation_flexible=True,
                representative_image_url="https://images.example.org/phacelia.jpg",
            )
        ],
    )


@pytest.fixture
def phases() -> _PhaseRepo:
    return _PhaseRepo(
        "GrowthPhase",
        [
            GrowthPhase(
                _key="ph_fruiting",
                name="fruiting",
                lifecycle_key="lc_tomato",
                typical_duration_days=90,
                sequence_order=4,
                allows_harvest=True,
                is_recurring=True,
                crop_coefficient_kc=1.15,
                kc_source="FAO-56 Table 12",
            )
        ],
    )


@pytest.fixture
def client(
    location_types: _LocationTypeRepo, substrates: _SubstrateRepo, species: _SpeciesRepo, phases: _PhaseRepo
) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: User(_key="lead", email="lead@example.org", display_name="L")
    app.dependency_overrides[get_is_platform_admin] = lambda: True
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=_TENANT, tenant_slug="own", user_key="lead", role=TenantRole.LEAD
    )
    app.dependency_overrides[get_location_type_service] = lambda: LocationTypeService(location_types)  # type: ignore[arg-type]
    app.dependency_overrides[get_substrate_service] = lambda: SubstrateService(substrates)  # type: ignore[arg-type]
    app.dependency_overrides[get_species_service] = lambda: SpeciesService(species, graph_repo=None)  # type: ignore[arg-type]
    app.dependency_overrides[get_family_repo] = lambda: SimpleNamespace(get_by_key=lambda _key: None)
    app.dependency_overrides[get_phase_service] = lambda: PhaseService(phases, MagicMock())  # type: ignore[arg-type]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ── location types: the system flag ─────────────────────────────────────────


def test_an_edited_system_location_type_stays_a_system_type(client: TestClient, location_types) -> None:
    response = client.put(
        "/api/v1/location-types/lt_greenhouse",
        json={"name": "Gewächshaus (beheizt)", "is_indoor": True, "sort_order": 1},
    )

    assert response.status_code == 200
    assert location_types.written[-1].name == "Gewächshaus (beheizt)"
    assert location_types.written[-1].is_system is True
    assert response.json()["is_system"] is True


def test_an_edited_system_location_type_still_cannot_be_deleted(client: TestClient, location_types) -> None:
    """The consequence that made the reset severe: the delete guard reads ``is_system``."""
    client.put("/api/v1/location-types/lt_greenhouse", json={"name": "Gewächshaus", "sort_order": 1})

    response = client.delete("/api/v1/location-types/lt_greenhouse")

    assert response.status_code == 422
    assert "lt_greenhouse" in location_types.rows


def test_a_location_type_body_cannot_make_a_type_a_system_type(client: TestClient, location_types) -> None:
    response = client.put("/api/v1/location-types/lt_custom", json={"name": "Eigener Typ", "is_system": True})

    assert response.status_code == 200
    assert location_types.written[-1].is_system is False


# ── substrates: a mix stays a mix ────────────────────────────────────────────


def test_an_edited_mix_stays_a_mix_with_its_components(client: TestClient, substrates) -> None:
    response = client.put("/api/v1/substrates/mix_own", json={"name_de": "Eigener Mix (fein)", "ph_base": 6.0})

    assert response.status_code == 200
    written = substrates.written[-1]
    assert (written.name_de, written.ph_base) == ("Eigener Mix (fein)", 6.0)
    assert written.is_mix is True
    assert [(c.substrate_key, c.fraction) for c in written.mix_components] == [
        ("sub_coco", 0.7),
        ("sub_perlite", 0.3),
    ]


def test_a_substrate_body_cannot_turn_a_medium_into_a_mix(client: TestClient, substrates) -> None:
    response = client.put(
        "/api/v1/substrates/sub_coco",
        json={"name_de": "Kokos", "is_mix": True, "mix_components": [{"substrate_key": "x", "fraction": 1.0}]},
    )

    assert response.status_code == 200
    assert (substrates.written[-1].is_mix, substrates.written[-1].mix_components) == (False, [])


# ── species: master data the edit form does not show ────────────────────────


def test_a_species_edit_keeps_traits_pruning_months_and_green_manure(client: TestClient, species) -> None:
    response = client.put(
        "/api/v1/species/sp_own",
        json={"scientific_name": "Phacelia tanacetifolia", "common_names": ["Büschelschön"]},
    )

    assert response.status_code == 200
    written = species.written[-1]
    assert written.common_names == ["Büschelschön"]
    assert written.traits == ["bee_friendly", "nitrogen_fixer"]
    assert written.pruning_months == [3, 9]
    assert written.green_manure_suitable is True
    # Kept before this change too — pinned so the shared helper did not lose them.
    assert written.cultivation_flexible is True
    assert written.representative_image_url == "https://images.example.org/phacelia.jpg"


def test_a_species_body_cannot_set_the_traits(client: TestClient, species) -> None:
    response = client.put(
        "/api/v1/species/sp_own",
        json={"scientific_name": "Phacelia tanacetifolia", "traits": ["edible"], "green_manure_suitable": False},
    )

    assert response.status_code == 200
    assert species.written[-1].traits == ["bee_friendly", "nitrogen_fixer"]
    assert species.written[-1].green_manure_suitable is True


# ── growth phases: the recurring flag and the Kc provenance ─────────────────


def test_a_phase_edit_keeps_it_recurring_and_its_kc_source(client: TestClient, phases) -> None:
    response = client.put(
        "/api/v1/growth-phases/ph_fruiting",
        json={
            "name": "fruiting",
            "lifecycle_key": "lc_tomato",
            "typical_duration_days": 120,
            "sequence_order": 4,
            "allows_harvest": True,
        },
    )

    assert response.status_code == 200
    written = phases.written[-1]
    assert written.typical_duration_days == 120
    assert written.is_recurring is True
    assert (written.crop_coefficient_kc, written.kc_source) == (1.15, "FAO-56 Table 12")
