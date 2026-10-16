from datetime import datetime

from pydantic import BaseModel, Field


class LocationTypeCreate(BaseModel):
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    is_bed: bool = False
    supports_layout: bool = False
    sort_order: int = 0
    description: str | None = None


class LocationTypeUpdate(BaseModel):
    """Full replace. The REQ-053 flags are **required**: an older client gets a 422, never a silent reset.

    ``PUT`` rebuilds the model from this body; a defaulted ``is_bed: bool = False``
    would turn ``bed`` into a non-bed on every edit by an older client — the defect
    class ``LocationTypeService.update`` documents for ``is_system``. ``is_system``
    stays off the body and is kept from the stored record.
    """

    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    is_bed: bool = Field(description="REQ-053 GP-FR-040: a bed type. Required on a full replace.")
    supports_layout: bool = Field(
        description="REQ-053 §9.2a: may carry a geometry with slot layout; forced true when is_bed. Required."
    )
    sort_order: int = 0
    description: str | None = None


class LocationTypeResponse(BaseModel):
    key: str
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    is_bed: bool = False
    supports_layout: bool = False
    is_system: bool = False
    sort_order: int = 0
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
