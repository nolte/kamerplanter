"""The world of the sowing/thinning tests (REQ-053 W-015): a bed with one sown row reserved by a run of the tenant.

Built on :func:`tests.support.planting_reservation_fakes.build_world` — the real services over the in-memory doubles.
"""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, PlantingRunType, SlotRole
from app.domain.engines.slot_reservation_engine import Reservation
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.site import Slot
from app.domain.services.care_event_service import CareEventService
from app.domain.services.slot_thinning_service import SlotThinningService
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships
from tests.support.fake_species_repo import FakeSpeciesRepo
from tests.support.garden_plan_fakes import TENANT
from tests.support.planting_reservation_fakes import build_world

USER = "u_sabine"
#: 1.20 m of row.
ROW = {"kind": "polyline", "points": [[0.0, 0.5], [1.2, 0.5]], "width_m": 0.05}
#: 0.5 m² of broadcast zone.
ZONE = {"kind": "polygon", "points": [[0.0, 0.0], [1.0, 0.0], [1.0, 0.5], [0.0, 0.5]]}


def sown_world(
    *,
    thinning_to_cm: float | None = 5.0,
    row_spacing_cm: float | None = None,
    species_row_spacing_cm: str | None = None,
    sown_at: date | None = None,
    role: SlotRole = SlotRole.ROW,
    geometry: dict | None = None,
    run_status: PlantingRunStatus = PlantingRunStatus.PLANNED,
    reserved: bool = True,
) -> SimpleNamespace:
    world = build_world()
    run = world.runs.create(
        PlantingRun(
            tenant_key=TENANT,
            name="Carrots",
            run_type=PlantingRunType.MONOCULTURE,
            location_key="bed",
            status=run_status,
        )
    )
    entry = world.runs.create_entry(
        PlantingRunEntry(
            run_key=run.key or "",
            tenant_key=TENANT,
            species_key="sp_carrot",
            quantity=1,
            id_prefix="DAU",
            thinning_to_cm=thinning_to_cm,
            row_spacing_cm=row_spacing_cm,
        )
    )
    world.plan.slots = [
        Slot(
            _key="row1",
            slot_id="BED3_R01",
            location_key="bed",
            slot_role=role,
            geometry=geometry if geometry is not None else (ROW if role is SlotRole.ROW else ZONE),
            sown_at=sown_at if sown_at is not None else today_utc() - timedelta(days=20),
        ),
        Slot(_key="foreign_row", slot_id="F_R01", location_key="loc_foreign", slot_role=SlotRole.ROW, geometry=ROW),
    ]
    if reserved:
        world.repo.reservations.append(
            Reservation(
                slot_key="row1",
                run_key=run.key or "",
                entry_key=entry.key or "",
                planned_species_key="sp_carrot",
                sequence=1,
                planned_from=today_utc() - timedelta(days=30),
                planned_until=None,
                run_status=run_status.value,
            )
        )
    care = CareEventService(
        world.care_repo,
        world.sites,
        FakeMemberships(),
        FakeFertilizers(),
        FakeAttachmentRepo(),
        FakeAttachmentService(),
    )
    world.species = FakeSpeciesRepo()
    world.species.add("sp_carrot", "Daucus carota", row_spacing_cm=species_row_spacing_cm)
    world.thinning = SlotThinningService(world.sites, world.repo, world.runs, world.service, care, world.species)
    world.run_key = run.key
    return world
