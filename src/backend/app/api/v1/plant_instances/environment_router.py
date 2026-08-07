"""REQ-013 §2.3a — read-only preview of a plant's environment snapshot.

``GET /api/v1/t/{tenant_slug}/plant-instances/{key}/environment`` answers what a
diary-entry capture *would* yield right now. It exists so the create dialog can
be honest about what will be stored: a grower who sees "31.2 °C / 28 % from the
Zeltsensor" before saving knows what the entry will carry, and can opt out if
that is not the story they want on the record.

**It is a preview, never an input.** The dialog renders the values read-only and
sends nothing back but the opt-out flag; the capture re-resolves everything
server-side at create time (``PlantDiaryService.create_entry``). The two
therefore *can* differ — a sensor may answer between the preview and the save —
and that is correct: the entry records what was true when it was written, not
what the dialog happened to have painted a minute earlier. Editing an automatic
value is deliberately not offered anywhere: a corrected sensor reading is a
manual measurement and belongs in ``measurements``.

The route sits on its own router rather than inside the diary prefix
(``/plant-instances/{key}/diary``) because it is a property of the *plant*, not
of any entry — the dialog calls it before an entry exists.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.planting_runs.diary_schemas import DiaryEnvironmentReadingResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import get_environment_snapshot_service, get_plant_instance_service
from app.common.enums import DiaryEnvironmentStatus
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.tenant_context import TenantContext
from app.domain.services.environment_snapshot_service import EnvironmentSnapshotService
from app.domain.services.plant_instance_service import PlantInstanceService

router = APIRouter(
    prefix="/plant-instances/{key}/environment",
    tags=["plant-diary"],
    responses=NOT_FOUND_RESPONSE,
)


class PlantEnvironmentPreviewResponse(BaseModel):
    """What an environment capture would store for this plant, right now."""

    plant_key: str
    readings: list[DiaryEnvironmentReadingResponse] = Field(default_factory=list)
    #: When this preview was resolved. ``None`` only when the installation has
    #: the capture switched off, i.e. together with ``not_attempted``.
    captured_at: datetime | None = None
    #: Why ``readings`` looks the way it does. A client that shows an empty
    #: preview must be able to say *which* empty it is — "no sensor covers this
    #: plant" reads very differently from "we could not reach the sensors".
    environment_status: DiaryEnvironmentStatus

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plant_key": "5512099",
                    "readings": [
                        {
                            "metric_type": "temperature_celsius",
                            "value": 31.2,
                            "unit": "°C",
                            "source": "ha_auto",
                            "measured_at": "2026-08-03T18:21:44Z",
                            "sensor_key": "7710455",
                            "origin": "location",
                        }
                    ],
                    "captured_at": "2026-08-03T18:22:03Z",
                    "environment_status": "captured",
                }
            ]
        }
    )


@router.get("", response_model=PlantEnvironmentPreviewResponse)
def preview_plant_environment(
    key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
    environment_service: EnvironmentSnapshotService = Depends(get_environment_snapshot_service),
):
    """Preview the environment snapshot for this plant (REQ-013 §2.3a).

    The plant is resolved against the caller's tenant first, so a foreign key
    answers 404 rather than an empty snapshot — an empty snapshot would confirm
    that the key exists somewhere in the installation.
    """
    plant_service.get_plant(key, tenant_key=ctx.tenant_key)
    snapshot = environment_service.preview_for_plant(key, tenant_key=ctx.tenant_key)
    return PlantEnvironmentPreviewResponse(
        plant_key=key,
        readings=[DiaryEnvironmentReadingResponse(**r.model_dump()) for r in snapshot.readings],
        captured_at=snapshot.captured_at,
        environment_status=snapshot.status,
    )
