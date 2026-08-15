"""REQ-044 §6 — pest-detection API DTOs."""

from pydantic import BaseModel, Field


class BoundingBoxSchema(BaseModel):
    x: float
    y: float
    width: float
    height: float


class FindingSchema(BaseModel):
    label: str
    category: str
    common_name: str
    confidence: float
    mode: str
    bounding_box: BoundingBoxSchema | None = None
    matched_pest_key: str | None = None
    matched_beneficial_key: str | None = None


class FeedbackSchema(BaseModel):
    finding_label: str
    confirmed: bool
    actual_label: str | None = None
    was_beneficial: bool = False


class PestDetectionResponse(BaseModel):
    key: str | None = None
    plant_instance_key: str | None = None
    source: str
    #: Which physical device produced the image (#1137). Echoed so a client can
    #: verify what was recorded — the image itself is never retained (§8), so an
    #: unverifiable write would be unrecoverable.
    capture_device: str = "unknown"
    adapter_key: str
    is_confident: bool
    trigger: str
    findings: list[FindingSchema] = Field(default_factory=list)
    tiles_processed: int
    suggested_next_step: str
    image_hash: str
    disclaimer: str
    feedback: list[FeedbackSchema] = Field(default_factory=list)
    created_at: str | None = None


class AdapterStatus(BaseModel):
    configured: bool
    is_external: bool
    requires_consent: str | None = None
    supports_modes: list[str] = Field(default_factory=list)


class PestDetectionStatusResponse(BaseModel):
    available: bool
    feature_enabled: bool
    primary_adapter: str
    active_adapter: str | None = None
    adapters: dict[str, AdapterStatus] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    finding_label: str
    confirmed: bool
    actual_label: str | None = None
    was_beneficial: bool = False


class CreateInspectionResponse(BaseModel):
    inspection_key: str | None = None
    detected_pest_keys: list[str] = Field(default_factory=list)
