"""#968 §1+§2 — every model-to-document write goes through one validation funnel.

PR #982 put the re-validation on ``BaseArangoRepository.update``. Measured
afterwards, that method is not the choke point the issue assumed: six
repositories override it and 33 hand-written repository methods dump a model and
write it themselves. This tier pins the two moves that close most of that gap:

* the guard moved to :meth:`BaseArangoRepository._to_doc`, the serialisation step
  21 of those hand-written writers already share;
* the six overrides came back onto the base path — two by delegating the write
  to ``super().update()``, four by admitting they are partial-field updates and
  taking the name ``update_fields``.

**Why this file exists at all.** The #982 probe reported "0 newly red tests" and
the number was worthless: the service tests double their repositories, so the
suite hardly touches the persistence path. Every test here therefore drives a
*real* repository against a doubled ``StandardDatabase`` and asserts on what
reaches ``collection`` / ``aql`` — the layer the guard actually sits in.

**Every negative test primes the double with a valid result document**, so that
against unguarded code the write *succeeds*: the failure is then
``DID NOT RAISE ValidationError`` plus a called ``insert``/``update``, which says
"the invalid document reached the database". Without that priming the same tests
would go red on a ``MagicMock`` failing to become a model on the way back — red
for the wrong reason, and therefore no evidence at all.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with ``MagicMock``. Nothing here opens a connection (#978).
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import (
    AdminScope,
    InvitationStatus,
    IrrigationSystem,
    LightType,
    TenantRole,
    TenantType,
)
from app.common.exceptions import ValidationError
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.hardiness_zone_repository import ArangoHardinessZoneRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.location_assignment_repository import (
    ArangoLocationAssignmentRepository,
)
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.models.hardiness_zone import HardinessZone
from app.domain.models.invitation import Invitation
from app.domain.models.location_assignment import LocationAssignment
from app.domain.models.membership import Membership
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location
from app.domain.models.species import Species
from app.domain.models.tenant import Tenant


@pytest.fixture
def mock_db():
    return MagicMock()


def _doc_of(model, key: str) -> dict:
    """A valid stored document for ``model``, as ArangoDB would return it."""
    return {"_key": key, **model.model_dump(by_alias=True, exclude_none=True, mode="json")}


# ── §1: hand-written writers that serialise through _to_doc ──────────────────


def _zone(**overrides) -> HardinessZone:
    data = {
        "zone": "7a",
        "zone_number": 7,
        "subzone": "a",
        "temp_min_c": -17.8,
        "temp_max_c": -15.0,
        "temp_min_f": 0.0,
        "temp_max_f": 5.0,
    }
    data.update(overrides)
    return HardinessZone(**data)


def _prime_zone_collection(coll, *, exists: bool) -> None:
    """Make every write on the double succeed and read back as a valid zone."""
    coll.has.return_value = exists
    coll.get.return_value = _doc_of(_zone(), "7a")
    coll.insert.return_value = {"new": _doc_of(_zone(), "7a")}
    coll.update.return_value = {"new": _doc_of(_zone(), "7a")}


class TestHandWrittenWriterIsCovered:
    """``upsert_zone`` never calls ``update``/``create`` — it dumps and writes.

    It is one of the 21 methods that reach ArangoDB through ``_to_doc`` without
    touching the base class's public write API, which is exactly the population
    #982's guard could not see.
    """

    def test_a_mutated_model_is_rejected_before_the_insert(self, mock_db):
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)
        zone = _zone()
        zone.zone_number = 99  # ``le=13`` — plain assignment, unchecked by Pydantic

        with pytest.raises(ValidationError) as excinfo:
            repo.upsert_zone(zone)

        assert excinfo.value.status_code == 422
        assert [detail["field"] for detail in excinfo.value.details] == ["zone_number"]
        coll.insert.assert_not_called()
        coll.update.assert_not_called()

    def test_a_mutated_model_is_rejected_before_the_in_place_update(self, mock_db):
        """The same method's other branch: the document already exists."""
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=True)
        zone = _zone()
        zone.subzone = "z"  # ``Literal["a", "b"]``

        with pytest.raises(ValidationError):
            repo.upsert_zone(zone)

        coll.update.assert_not_called()
        coll.insert.assert_not_called()

    def test_a_field_validator_is_re_run_not_just_the_annotation(self, mock_db):
        """``HardinessZone.zone`` is guarded by a ``field_validator``, not a type.

        ``model_validate`` re-runs it, so the funnel catches domain rules and not
        only type mismatches.
        """
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)
        zone = _zone()
        zone.zone = "not-a-zone"

        with pytest.raises(ValidationError) as excinfo:
            repo.upsert_zone(zone)

        assert [detail["field"] for detail in excinfo.value.details] == ["zone"]
        coll.insert.assert_not_called()

    def test_a_valid_zone_still_reaches_the_database(self, mock_db):
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)

        result = repo.upsert_zone(_zone())

        coll.insert.assert_called_once()
        assert result.zone == "7a"


class TestCustomAqlWriterIsCovered:
    """The species UPSERT binds a ``_to_doc`` dump into hand-written AQL."""

    def test_a_mutated_species_never_reaches_the_upsert_query(self, mock_db):
        repo = ArangoSpeciesRepository(mock_db)
        species = Species(scientific_name="Solanum lycopersicum", common_name="Tomate")
        mock_db.aql.execute.return_value = iter([_doc_of(species, "sp1")])
        species.growth_habit = "definitely-not-a-growth-habit"  # type: ignore[assignment]

        with pytest.raises(ValidationError) as excinfo:
            repo.upsert_by_normalized_scientific_name(species)

        assert [detail["field"] for detail in excinfo.value.details] == ["growth_habit"]
        mock_db.aql.execute.assert_not_called()

    def test_a_valid_species_still_reaches_the_upsert_query(self, mock_db):
        repo = ArangoSpeciesRepository(mock_db)
        species = Species(scientific_name="Solanum lycopersicum", common_name="Tomate")
        mock_db.aql.execute.return_value = iter([_doc_of(species, "sp1")])

        result = repo.upsert_by_normalized_scientific_name(species)

        mock_db.aql.execute.assert_called_once()
        assert result.scientific_name == "Solanum lycopersicum"


class TestTheCreatePathIsValidatedToo:
    """``_to_doc`` is on the insert path as well, deliberately.

    A freshly constructed model was validated at construction, so this is
    usually redundant — but a service is free to build, mutate and *then*
    insert, and no domain model sets ``validate_assignment=True``.
    """

    def test_a_model_mutated_between_construction_and_create_is_rejected(self, mock_db):
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)
        zone = _zone()
        zone.temp_min_c = "quite cold"  # type: ignore[assignment]

        with pytest.raises(ValidationError):
            repo.create(zone)

        coll.insert.assert_not_called()

    def test_the_rejected_value_is_not_echoed_on_the_create_path(self, mock_db):
        """NFR-011 — the rejected value can be personal data; field + reason suffice.

        The same no-echo property #982 pinned for ``update`` must hold on every
        path the guard now covers, or moving it would have widened a disclosure
        surface rather than a guarantee.
        """
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)
        zone = _zone()
        zone.description_de = ["user@example.com"]  # type: ignore[assignment]

        with pytest.raises(ValidationError) as excinfo:
            repo.create(zone)

        rendered = excinfo.value.message + str(excinfo.value.details)
        assert "user@example.com" not in rendered
        assert "description_de" in rendered

    def test_a_freshly_constructed_model_is_inserted_unchanged(self, mock_db):
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)

        result = repo.create(_zone())

        assert result.zone == "7a"
        assert coll.insert.call_args.args[0]["zone_number"] == 7


class TestTheModelIsValidatedExactlyOncePerWrite:
    """Moving the guard must not leave a second copy behind on ``update``.

    ``update`` used to call the check itself; now it reaches it through
    ``_update_doc`` → ``_to_doc``. Two calls would be harmless but wasteful, and
    would mean the next reader has to work out which one is load-bearing.
    """

    def test_update_validates_once(self, mock_db, monkeypatch):
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=True)
        calls: list[str] = []
        original = BaseArangoRepository._validate_model_before_write
        monkeypatch.setattr(
            BaseArangoRepository,
            "_validate_model_before_write",
            lambda self, model: (calls.append(type(model).__name__), original(self, model))[1],
        )

        repo.update("7a", _zone())

        assert calls == ["HardinessZone"]

    def test_create_validates_once(self, mock_db, monkeypatch):
        repo = ArangoHardinessZoneRepository(mock_db)
        coll = mock_db.collection.return_value
        _prime_zone_collection(coll, exists=False)
        calls: list[str] = []
        original = BaseArangoRepository._validate_model_before_write
        monkeypatch.setattr(
            BaseArangoRepository,
            "_validate_model_before_write",
            lambda self, model: (calls.append(type(model).__name__), original(self, model))[1],
        )

        repo.create(_zone())

        assert calls == ["HardinessZone"]


# ── §2a: the two full-model overrides, now on the base path ──────────────────


def _plant(**overrides) -> PlantInstance:
    data = {
        "instance_id": "P-0001",
        "species_key": "sp-1",
        "planted_on": date(2026, 3, 1),
        "tenant_key": "t1",
    }
    data.update(overrides)
    return PlantInstance(**data)


class TestPlantInstanceUpdateIsOnTheBasePath:
    """``ArangoPlantInstanceRepository.update`` hand-rolled its own write.

    PlantInstance is one of the two most central entities in the system, and its
    update bypassed the #982 guard completely.
    """

    def test_a_mutated_plant_is_rejected_before_the_write(self, mock_db):
        repo = ArangoPlantInstanceRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_plant(), "p1")}
        plant = _plant()
        plant.substrate_type_override = "gravel"  # type: ignore[assignment]  # the #967 shape

        with pytest.raises(ValidationError) as excinfo:
            repo.update("p1", plant)

        assert excinfo.value.status_code == 422
        assert [detail["field"] for detail in excinfo.value.details] == ["substrate_type_override"]
        coll.update.assert_not_called()

    def test_a_negative_counter_is_rejected(self, mock_db):
        repo = ArangoPlantInstanceRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_plant(), "p1")}
        plant = _plant()
        plant.reversion_count = -1  # ``ge=0``

        with pytest.raises(ValidationError):
            repo.update("p1", plant)

        coll.update.assert_not_called()

    def test_null_clearing_semantics_survive_the_move(self, mock_db):
        """Issue #714 / placement reset: a nulled ``slot_key`` must *clear* it.

        The hand-rolled version dumped with ``exclude_none=False`` and passed
        ``keep_none=False``; that is now the ``_update_is_full_replace`` class
        attribute, and it has to behave identically.
        """
        repo = ArangoPlantInstanceRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_plant(), "p1")}

        repo.update("p1", _plant(slot_key=None, location_key=None))

        payload = coll.update.call_args.args[0]
        assert payload["slot_key"] is None
        assert payload["location_key"] is None
        assert coll.update.call_args.kwargs["keep_none"] is False
        assert coll.update.call_args.kwargs["return_new"] is True
        assert payload["_key"] == "p1"

    def test_a_model_without_created_at_cannot_erase_the_stored_one(self, mock_db):
        """Full-replace + ``keep_none=False`` makes a null ``created_at`` destructive.

        The hand-rolled version popped it; the base path must too, or a service
        that rebuilds a plant from a request body would wipe its creation date.
        """
        repo = ArangoPlantInstanceRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_plant(), "p1")}

        repo.update("p1", _plant())

        payload = coll.update.call_args.args[0]
        assert "created_at" not in payload
        assert payload["updated_at"]

    def test_a_valid_plant_is_still_written_and_mapped_back(self, mock_db):
        repo = ArangoPlantInstanceRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_plant(plant_name="Renamed"), "p1")}

        result = repo.update("p1", _plant(plant_name="Renamed"))

        assert isinstance(result, PlantInstance)
        assert result.plant_name == "Renamed"


def _location(**overrides) -> Location:
    data = {
        "name": "Bed 1",
        "site_key": "site-1",
        "area_m2": 10.0,
        "light_type": LightType.NATURAL,
        "irrigation_system": IrrigationSystem.MANUAL,
    }
    data.update(overrides)
    return Location(**data)


class TestLocationUpdateIsOnTheBasePath:
    """``_LocationRepository.update`` hand-rolled its own write as well."""

    def test_a_mutated_location_is_rejected_before_the_write(self, mock_db):
        repo = ArangoSiteRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_location(), "loc-1")}
        location = _location()
        location.area_m2 = -5.0  # ``ge=0``

        with pytest.raises(ValidationError) as excinfo:
            repo.update_location("loc-1", location)

        assert [detail["field"] for detail in excinfo.value.details] == ["area_m2"]
        coll.update.assert_not_called()

    def test_a_field_validator_violation_is_rejected(self, mock_db):
        repo = ArangoSiteRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_location(), "loc-1")}
        location = _location()
        location.lights_on = "25:00"  # HH:MM validator

        with pytest.raises(ValidationError):
            repo.update_location("loc-1", location)

        coll.update.assert_not_called()

    def test_a_model_without_created_at_cannot_erase_the_stored_one(self, mock_db):
        repo = ArangoSiteRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_location(), "loc-1")}

        repo.update_location("loc-1", _location())

        payload = coll.update.call_args.args[0]
        assert "created_at" not in payload


# ── §2b: the four dict-signature overrides, renamed to update_fields ─────────


def _tenant(**overrides) -> Tenant:
    data = {"name": "Garden", "slug": "garden", "owner_user_key": "u1", "tenant_type": TenantType.PERSONAL}
    data.update(overrides)
    return Tenant(**data)


def _membership(**overrides) -> Membership:
    data = {"user_key": "u1", "tenant_key": "t1", "role": TenantRole.VIEWER}
    data.update(overrides)
    return Membership(**data)


def _invitation(**overrides) -> Invitation:
    data = {
        "tenant_key": "t1",
        "invited_by_user_key": "u1",
        "token_hash": "h",
        "expires_at": datetime(2026, 12, 1, tzinfo=UTC),
    }
    data.update(overrides)
    return Invitation(**data)


def _assignment(**overrides) -> LocationAssignment:
    data = {"membership_key": "m1", "location_key": "loc-1", "tenant_key": "t1"}
    data.update(overrides)
    return LocationAssignment(**data)


class TestTenantPartialUpdateIsNamedForWhatItIs:
    def test_update_fields_merges_and_writes(self, mock_db):
        repo = ArangoTenantRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_tenant(), "t1")
        coll.update.return_value = {"new": _doc_of(_tenant(name="Renamed"), "t1")}

        result = repo.update_fields("t1", {"name": "Renamed"})

        assert result is not None
        assert result.name == "Renamed"
        assert coll.update.call_args.args[0]["name"] == "Renamed"

    def test_a_partial_payload_that_violates_the_model_is_rejected(self, mock_db):
        """The merged model is re-validated, so a bad partial value cannot land.

        Under the base class's own ``update_fields`` this dict would be written
        straight through unchecked — which is precisely why this repository keeps
        its read-modify-write body instead of delegating to it.
        """
        repo = ArangoTenantRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_tenant(), "t1")
        coll.update.return_value = {"new": _doc_of(_tenant(), "t1")}

        with pytest.raises(ValidationError) as excinfo:
            repo.update_fields("t1", {"max_members": 0})  # ``ge=1``

        assert [detail["field"] for detail in excinfo.value.details] == ["max_members"]
        coll.update.assert_not_called()

    def test_a_missing_tenant_returns_none_rather_than_raising(self, mock_db):
        repo = ArangoTenantRepository(mock_db)
        mock_db.collection.return_value.get.return_value = None

        assert repo.update_fields("nope", {"name": "x"}) is None

    def test_the_inherited_full_model_update_is_no_longer_shadowed(self, mock_db):
        """The point of the rename: ``update`` means "full model" again.

        Before, ``update(key, dict)`` shadowed it, so the checked full-model path
        was simply unreachable on this repository.
        """
        repo = ArangoTenantRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_tenant(), "t1")}
        tenant = _tenant()
        tenant.max_members = 0  # ``ge=1``

        with pytest.raises(ValidationError):
            repo.update("t1", tenant)

        coll.update.assert_not_called()


class TestMembershipPartialUpdateIsNamedForWhatItIs:
    def test_update_fields_merges_and_writes(self, mock_db):
        repo = ArangoMembershipRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_membership(), "m1")
        coll.update.return_value = {"new": _doc_of(_membership(role=TenantRole.LEAD), "m1")}

        result = repo.update_fields("m1", {"role": TenantRole.LEAD})

        assert result is not None
        assert result.role is TenantRole.LEAD

    def test_an_undefined_admin_scope_is_rejected(self, mock_db):
        """REQ-049 INV-2 — ``admin_scopes`` holds only defined values."""
        repo = ArangoMembershipRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_membership(), "m1")
        coll.update.return_value = {"new": _doc_of(_membership(), "m1")}

        with pytest.raises(ValidationError) as excinfo:
            repo.update_fields("m1", {"admin_scopes": ["superuser"]})

        assert excinfo.value.details[0]["field"].startswith("admin_scopes")
        coll.update.assert_not_called()

    def test_a_missing_membership_returns_none(self, mock_db):
        repo = ArangoMembershipRepository(mock_db)
        mock_db.collection.return_value.get.return_value = None

        assert repo.update_fields("nope", {"role": TenantRole.LEAD}) is None

    def test_the_inherited_full_model_update_is_no_longer_shadowed(self, mock_db):
        repo = ArangoMembershipRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_membership(), "m1")}
        membership = _membership()
        membership.role = "emperor"  # type: ignore[assignment]

        with pytest.raises(ValidationError):
            repo.update("m1", membership)

        coll.update.assert_not_called()

    def test_a_valid_scope_change_round_trips(self, mock_db):
        repo = ArangoMembershipRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_membership(), "m1")
        coll.update.return_value = {"new": _doc_of(_membership(admin_scopes=[AdminScope.MANAGEMENT]), "m1")}

        result = repo.update_fields("m1", {"admin_scopes": [AdminScope.MANAGEMENT]})

        assert result is not None
        assert result.has_management


class TestInvitationPartialUpdateIsNamedForWhatItIs:
    def test_a_bogus_status_is_rejected(self, mock_db):
        repo = ArangoInvitationRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_invitation(), "i1")
        coll.update.return_value = {"new": _doc_of(_invitation(), "i1")}

        with pytest.raises(ValidationError) as excinfo:
            repo.update_fields("i1", {"status": "half-accepted"})

        assert [detail["field"] for detail in excinfo.value.details] == ["status"]
        coll.update.assert_not_called()

    def test_a_valid_status_change_round_trips(self, mock_db):
        repo = ArangoInvitationRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_invitation(), "i1")
        coll.update.return_value = {"new": _doc_of(_invitation(status=InvitationStatus.REVOKED), "i1")}

        result = repo.update_fields("i1", {"status": InvitationStatus.REVOKED})

        assert result is not None
        assert result.status is InvitationStatus.REVOKED

    def test_a_missing_invitation_returns_none(self, mock_db):
        repo = ArangoInvitationRepository(mock_db)
        mock_db.collection.return_value.get.return_value = None

        assert repo.update_fields("nope", {"status": InvitationStatus.REVOKED}) is None

    def test_the_inherited_full_model_update_is_no_longer_shadowed(self, mock_db):
        repo = ArangoInvitationRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_invitation(), "i1")}
        invitation = _invitation()
        invitation.status = "half-accepted"  # type: ignore[assignment]

        with pytest.raises(ValidationError):
            repo.update("i1", invitation)

        coll.update.assert_not_called()


class TestLocationAssignmentPartialUpdateIsNamedForWhatItIs:
    def test_a_bad_typed_field_is_rejected(self, mock_db):
        repo = ArangoLocationAssignmentRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_assignment(), "a1")
        coll.update.return_value = {"new": _doc_of(_assignment(), "a1")}

        with pytest.raises(ValidationError) as excinfo:
            repo.update_fields("a1", {"can_edit": "sometimes"})

        assert [detail["field"] for detail in excinfo.value.details] == ["can_edit"]
        coll.update.assert_not_called()

    def test_update_fields_merges_and_writes(self, mock_db):
        repo = ArangoLocationAssignmentRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc_of(_assignment(), "a1")
        coll.update.return_value = {"new": _doc_of(_assignment(can_edit=False), "a1")}

        result = repo.update_fields("a1", {"can_edit": False})

        assert result is not None
        assert result.can_edit is False

    def test_a_missing_assignment_returns_none(self, mock_db):
        repo = ArangoLocationAssignmentRepository(mock_db)
        mock_db.collection.return_value.get.return_value = None

        assert repo.update_fields("nope", {"can_edit": False}) is None

    def test_the_inherited_full_model_update_is_reachable(self, mock_db):
        repo = ArangoLocationAssignmentRepository(mock_db)
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc_of(_assignment(), "a1")}

        result = repo.update("a1", _assignment())

        assert isinstance(result, LocationAssignment)


class TestNoneOfTheFourStillCarriesADictUpdate:
    """The four ``update(key, dict)`` signatures are gone, not merely aliased.

    A ``dict`` accepted under the name ``update`` is what made mass assignment
    read like the checked full-model path; leaving a compatibility alias behind
    would have kept exactly that.
    """

    @pytest.mark.parametrize(
        "repo_cls",
        [
            ArangoTenantRepository,
            ArangoMembershipRepository,
            ArangoInvitationRepository,
            ArangoLocationAssignmentRepository,
        ],
    )
    def test_update_is_the_inherited_full_model_method(self, repo_cls):
        assert repo_cls.update is BaseArangoRepository.update
        assert repo_cls.update_fields is not BaseArangoRepository.update_fields
