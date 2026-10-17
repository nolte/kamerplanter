"""REQ-053 WP 1.7 (#2326) — a ``PUT`` through the pre-plan bodies keeps the garden-plan fields.

``LocationCreate`` / ``SlotCreate`` do not carry ``geometry``, ``soil_profile``,
``slot_role`` …; the rebuilt model holds their defaults, and the location view
replaces the whole document (#714). Without the service keeping them, every
rename of a bed would unplace it. The assertion is on the model the repository
receives — the same object the write serialises.
"""

from __future__ import annotations

from app.common.enums import BedStatus, SlotRole, SunExposure
from app.domain.models.site import Location, Site, Slot
from app.domain.services.site_service import LOCATION_FIELDS_KEPT_ON_EDIT, SLOT_FIELDS_KEPT_ON_EDIT, SiteService

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
            notes="Tomaten wegen Dachüberstand.",
            description="Lärchenholz",
            locked=True,
            z_order=10,
            pitch_m=0.25,
            rotation_exempt=True,
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

    def update_location(self, key, location):
        self.written.append(location)
        return location

    def update_slot(self, key, slot):
        self.written.append(slot)
        return slot


def _service(repo: _Repo) -> SiteService:
    return SiteService(repo)  # type: ignore[arg-type]


class TestUpdateLocation:
    def test_the_plan_fields_come_from_the_stored_row_and_area_follows_the_geometry(self) -> None:
        repo = _Repo()
        body = Location(name="Hochbeet 3 (neu)", site_key="site_1", area_m2=99.0)  # what LocationCreate rebuilds

        written = _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert written is repo.written[0]
        assert written.name == "Hochbeet 3 (neu)"
        for field in LOCATION_FIELDS_KEPT_ON_EDIT:
            assert getattr(written, field) == getattr(repo.location, field), field
        # GP-ACC-035: the kept geometry, not the body, decides the area.
        assert written.area_m2 == 2.0
        assert written.bbox == (1.0, 1.0, 3.0, 2.0)

    def test_without_a_stored_geometry_the_body_s_area_stands(self) -> None:
        repo = _Repo()
        repo.location = repo.location.model_copy(update={"geometry": None, "bbox": None})
        body = Location(name="Beet", site_key="site_1", area_m2=4.5)

        written = _service(repo).update_location("loc_1", body, tenant_key=TENANT)

        assert (written.geometry, written.bbox, written.area_m2) == (None, None, 4.5)

    def test_the_kept_tuple_names_every_plan_field_the_body_lacks(self) -> None:
        from app.api.v1.locations.schemas import LocationCreate

        plan_fields = set(Location.model_fields) - set(LocationCreate.model_fields)
        plan_fields -= {"key", "created_at", "updated_at", "depth", "path", "area_m2"}
        assert plan_fields == set(LOCATION_FIELDS_KEPT_ON_EDIT)


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
