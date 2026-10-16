from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class LocationType(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    #: REQ-053 GP-FR-040 / REQ-002 v4.6: a bed type — bed list, bed status, soil
    #: profile and crop-rotation hints hang on it. Seeds: bed, raised_bed, planter,
    #: greenhouse_bed, cold_frame. Not shelf/tent (they carry planters, O-09).
    is_bed: bool = False
    #: REQ-053 §9.2a / W-016.1: the location may carry a geometry with a slot layout
    #: — every ``is_bed`` type plus ``tent`` and ``shelf``. The planting dialog,
    #: ``compute_layout`` and the run layout hang on this flag, not on ``is_bed``.
    supports_layout: bool = False
    is_system: bool = False
    sort_order: int = 0
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _a_bed_supports_a_layout(self) -> LocationType:
        """REQ-053 §9.2a: ``is_bed`` implies ``supports_layout`` — on create, edit and read alike."""
        if self.is_bed and not self.supports_layout:
            self.supports_layout = True
        return self
