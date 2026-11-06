"""REQ-053 WP 1.7 (#2326) — a ``PUT`` through the pre-plan bodies keeps the garden-plan fields.

``LocationCreate`` / ``SlotCreate`` do not carry ``geometry``, ``soil_profile``,
``slot_role`` …; the rebuilt model holds their defaults, and the location view
replaces the whole document (#714). Without the service keeping them, every
rename of a bed would unplace it. The assertion is on the model the repository
receives — the same object the write serialises — and, for ``PUT /locations``,
on the columns the service tells the repository not to write (#2623): the kept
copy may be stale, so the location write leaves those columns as stored and the
``frost_exposed`` mirror travels as the one ``frost_risk`` sub-path.
"""

from __future__ import annotations

from app.common.enums import BedStatus, FrostRisk, SlotRole, SunExposure, SunWindow
from app.domain.models.site import Location, Site, Slot
from app.domain.services.site_service import (
    LOCATION_FIELDS_KEPT_ON_EDIT,
    SLOT_COLUMNS_A_PUT_LEAVES,
    SLOT_FIELDS_KEPT_ON_EDIT,
    SiteService,
)

TENANT = "tenant_own"
_RECT = {"kind": "rect", "origin": [1.0, 1.0], "width_m": 2.0, "length_m": 1.0}


class _Repo:
    def __init__(self) -> None:
        self.site = Site(_key="site_1", tenant_key=TENANT, name="Garten", type="outdoor")
        self.location = Location(
            _key="loc_1",
            name="Hochbeet 3",
            site_key="site_1",
            area_m2=0.0,
            geometry=_RECT,
            height_m=0.8,
            bed_status=BedStatus.PLANNED,
            sun_exposure=SunExposure.FULL_SUN,
            irrigation_zone_key="zone_1",
            soil_profile={"soil_texture": "loam", "ph": 6.8},
            site_conditions={"sun_profile": {"sun_window": "afternoon"}, "wind_exposure": "exposed"},
            notes="Tomaten wegen Dachüberstand.",
            description="Lärchenholz",
            locked=True,
            z_order=10,
            pitch_m=0.25,
            rotation_exempt=True,
            rotation_enabled=False,
        )
        self.slot = Slot(
            _key="slot_1",
            slot_id="BEET_R1",
            location_key="loc_1",
            currently_occupied=True,
            slot_role=SlotRole.ROW,
            geometry={"kind": "polyline", "points": [[0, 0.3], [2, 0.3]], "width_m": 0.1},
            row_index=0,
            sequence=1,
            geometry_source="layout",
            container_volume_l=None,
            planned_spacing_cm=30,
        )
        self.written: list[object] = []
        #: The keyword arguments of the last location write (#2623).
        self.location_write: dict[str, object] = {}
        self.stored_after_write: Location | None = None

    def get_site_by_key(self, key):
        return self.site if key == "site_1" else None

    def get_site_or_raise(self, key):
        return self.site

    def get_location_by_key(self, key):
        return self.location if key == "loc_1" else None

    def get_location_or_raise(self, key):
        return self.location

    def get_slot_by_key(self, key):
        return self.slot if key == "slot_1" else None

    def get_slot_or_raise(self, key):
        return self.slot

    def update_location(self, key, location, *, untouched, frost_risk=None):
        self.written.append(location)
        self.location_write = {"untouched": tuple(untouched), "frost_risk": frost_risk}
        # What the real repository answers: the location as stored after the write, not the model handed in.
        self.stored_after_write = self.location.model_copy(update={"name": location.name})
        return self.stored_after_write

    def update_slot(self, key, slot, *, untouched=()):
        self.written.append(slot)
        #: The columns the last slot write leaves as stored (#2639).
        self.slot_untouched = tuple(untouched)
        return slot


def _service(repo: _Repo) -> SiteService:
    return SiteService(repo)  # type: ignore[arg-type]


class TestUpdateLocation:
    def test_the_plan_fields_come_from_the_stored_row_and_area_follows_the_geometry(self) -> None:
        repo = _Repo()
        body = Location(name="Hochbeet 3 (neu)", site_key="site_1", area_m2=99.0)  # what LocationCreate rebuilds

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        written = repo.written[0]
        assert isinstance(written, Location)
        assert written.name == "Hochbeet 3 (neu)"
        for field in LOCATION_FIELDS_KEPT_ON_EDIT:
            assert getattr(written, field) == getattr(repo.location, field), field
        # GP-ACC-035: the kept geometry, not the body, decides the area.
        assert written.area_m2 == 2.0
        assert written.bbox == (1.0, 1.0, 3.0, 2.0)

    def test_the_plan_fields_and_a_placed_area_are_not_written_2623(self) -> None:
        """The kept copy is as old as the read: written back, it reverts a plan batch that landed since."""
        repo = _Repo()
        body = Location(name="Hochbeet 3 (neu)", site_key="site_1", area_m2=99.0)

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert repo.location_write == {"untouched": (*LOCATION_FIELDS_KEPT_ON_EDIT, "area_m2"), "frost_risk": None}

    def test_the_response_is_the_stored_location_not_the_model_handed_in(self) -> None:
        repo = _Repo()
        body = Location(name="Hochbeet 3 (neu)", site_key="site_1", area_m2=99.0)

        returned = _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert returned is repo.stored_after_write and returned is not repo.written[0]

    def test_without_a_stored_geometry_the_body_s_area_stands(self) -> None:
        repo = _Repo()
        repo.location = repo.location.model_copy(update={"geometry": None, "bbox": None})
        body = Location(name="Beet", site_key="site_1", area_m2=4.5)

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        written = repo.written[0]
        assert isinstance(written, Location)
        assert (written.geometry, written.bbox, written.area_m2) == (None, None, 4.5)
        assert repo.location_write["untouched"] == LOCATION_FIELDS_KEPT_ON_EDIT  # area_m2 is the body's: written

    def test_the_kept_tuple_names_every_plan_field_the_body_lacks(self) -> None:
        from app.api.v1.locations.schemas import LocationCreate

        plan_fields = set(Location.model_fields) - set(LocationCreate.model_fields)
        plan_fields -= {"key", "created_at", "updated_at", "depth", "path", "area_m2"}
        assert plan_fields == set(LOCATION_FIELDS_KEPT_ON_EDIT)


class TestFrostExposedMirror:
    """WP 3.9: the legacy boolean and ``microclimate.frost_risk`` move together on ``PUT /locations``.

    Since #2623 the update hands the repository the mirrored risk alone (``frost_risk``), which it merges
    into the stored ``site_conditions``; the kept ``site_conditions`` of the model is not written.
    """

    def test_a_changed_boolean_sets_the_risk_and_keeps_the_other_site_conditions(self) -> None:
        repo = _Repo()
        body = Location(name="Hochbeet 3", site_key="site_1", area_m2=0.0, frost_exposed=True)

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert repo.location_write["frost_risk"] is FrostRisk.HIGH
        assert "site_conditions" in repo.location_write["untouched"]  # the sun profile is not written over
        written = repo.written[0]
        assert isinstance(written, Location) and written.site_conditions is not None
        assert written.site_conditions.sun_profile.sun_window is SunWindow.AFTERNOON
        # the stored row is not touched
        assert repo.location.site_conditions.microclimate.frost_risk is FrostRisk.UNKNOWN  # type: ignore[union-attr]

    def test_an_unchanged_boolean_leaves_an_entered_risk_alone(self) -> None:
        repo = _Repo()
        repo.location = repo.location.model_copy(
            update={
                "frost_exposed": True,
                "site_conditions": {"microclimate": {"frost_risk": "normal"}},
            }
        )
        repo.location = Location.model_validate(repo.location.model_dump(by_alias=True))
        body = Location(name="Hochbeet 3", site_key="site_1", area_m2=0.0, frost_exposed=True)

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert repo.location_write["frost_risk"] is None

    def test_a_migrated_protected_bed_keeps_both_fields_on_the_next_save(self) -> None:
        """#2464 (4): the location form sends the stored ``False`` back; v0098's ``normal`` stays, so does ``False``."""
        repo = _Repo()
        repo.location = Location.model_validate(
            {
                **repo.location.model_dump(by_alias=True),
                "frost_exposed": False,
                "site_conditions": {"microclimate": {"frost_risk": "normal"}},
            }
        )
        body = Location(name="Hochbeet 3 (renamed)", site_key="site_1", area_m2=0.0, frost_exposed=False)

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        written = repo.written[0]
        assert isinstance(written, Location) and written.frost_exposed is False
        assert repo.location_write["frost_risk"] is None  # the stored ``normal`` is not touched

    def test_clearing_the_boolean_resets_the_risk_to_unknown(self) -> None:
        repo = _Repo()
        repo.location = Location.model_validate({**repo.location.model_dump(by_alias=True), "frost_exposed": False})
        body = Location(name="Hochbeet 3", site_key="site_1", area_m2=0.0, frost_exposed=None)

        _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert repo.location_write["frost_risk"] is FrostRisk.UNKNOWN

    def test_create_with_a_boolean_writes_the_risk(self) -> None:
        repo = _Repo()
        repo.created = []  # type: ignore[attr-defined]
        repo.create_location = lambda location: repo.created.append(location) or location  # type: ignore[attr-defined,method-assign]
        body = Location(name="Neues Beet", site_key="site_1", area_m2=1.0, frost_exposed=False)

        created = _service(repo).create_location(body, tenant_key=TENANT)

        assert created.site_conditions is not None
        assert created.site_conditions.microclimate.frost_risk is FrostRisk.NORMAL  # #2464: false → normal


class TestUpdateSlot:
    def test_the_plan_fields_come_from_the_stored_row(self) -> None:
        repo = _Repo()
        body = Slot(slot_id="BEET_R1", location_key="loc_1", capacity_plants=3)  # what SlotCreate rebuilds

        written = _service(repo).update_slot("slot_1", body, tenant_key=TENANT)

        assert written is repo.written[0]
        assert written.capacity_plants == 3
        assert written.currently_occupied is True
        for field in SLOT_FIELDS_KEPT_ON_EDIT:
            assert getattr(written, field) == getattr(repo.slot, field), field
        assert written.slot_role is SlotRole.ROW

    def test_the_columns_the_body_lacks_are_not_written_2639(self) -> None:
        """The kept copy is as old as the read: written back, it reverts a PATCH or an occupation since."""
        repo = _Repo()
        body = Slot(slot_id="BEET_R1", location_key="loc_1", capacity_plants=3)

        _service(repo).update_slot("slot_1", body, tenant_key=TENANT)

        assert repo.slot_untouched == SLOT_COLUMNS_A_PUT_LEAVES
        assert set(SLOT_COLUMNS_A_PUT_LEAVES) == {*SLOT_FIELDS_KEPT_ON_EDIT, "currently_occupied", "last_sanitization"}
        assert not set(SLOT_COLUMNS_A_PUT_LEAVES) & {"slot_id", "location_key", "capacity_plants"}  # the body's

    def test_the_kept_tuple_names_every_plan_field_the_body_lacks(self) -> None:
        from app.api.v1.slots.schemas import SlotCreate

        plan_fields = set(Slot.model_fields) - set(SlotCreate.model_fields)
        plan_fields -= {"key", "created_at", "updated_at", "currently_occupied", "last_sanitization"}
        assert plan_fields == set(SLOT_FIELDS_KEPT_ON_EDIT)


class TestTheDerivedAreaSurvivesAnOrdinaryEdit:
    """REQ-053 WP 1.8 — ``PUT /sites`` carries a ``total_area_m2`` (default 0) that looks like a typed value."""

    def _service(self, boundary: bool):
        from app.domain.models.site import SitePlan

        class _SiteRepo:
            def __init__(self) -> None:
                plan = SitePlan(boundary=_RECT_BOUNDARY, plan_revision=2) if boundary else None
                self.site = Site(_key="site_1", tenant_key=TENANT, name="Garten", type="outdoor", plan=plan)
                if boundary:
                    assert self.site.total_area_m2 == 100.0
                self.written: Site | None = None

            def get_site_or_raise(self, key):
                return self.site

            def update_site(self, key, site):
                self.written = site
                return site

        repo = _SiteRepo()
        return SiteService(repo), repo  # type: ignore[arg-type]

    def test_with_a_boundary_the_stored_area_wins_over_the_body(self) -> None:
        service, repo = self._service(boundary=True)
        body = Site(name="Garten (umbenannt)", type="outdoor", total_area_m2=0.0)
        service.update_site("site_1", body, tenant_key=TENANT)
        assert repo.written is not None and repo.written.total_area_m2 == 100.0

    def test_without_a_boundary_the_body_still_sets_the_area(self) -> None:
        service, repo = self._service(boundary=False)
        body = Site(name="Garten", type="outdoor", total_area_m2=42.5)
        service.update_site("site_1", body, tenant_key=TENANT)
        assert repo.written is not None and repo.written.total_area_m2 == 42.5


_RECT_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}
