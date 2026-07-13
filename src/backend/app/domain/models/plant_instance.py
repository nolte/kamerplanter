from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import CycleType, SubstrateType, TerminationCause, TerminationType


class PlantInstance(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    instance_id: str
    species_key: str
    cultivar_key: str | None = None
    site_key: str | None = None
    location_key: str | None = None
    slot_key: str | None = None
    substrate_batch_key: str | None = None
    substrate_key: str | None = Field(
        default=None,
        description="Reference to a Substrate record — substrate_type_override is auto-derived",
    )
    plant_name: str | None = None
    planted_on: date
    removed_on: date | None = None
    # ── Lifecycle end (REQ-003 E5) — distinguishes planned end from unplanned loss ──
    termination_type: TerminationType | None = Field(
        default=None,
        description="How the lifecycle ended: harvested/senesced (planned), died (unplanned loss), "
        "cancelled (user aborted). None while the plant is alive.",
    )
    termination_cause: TerminationCause | None = Field(
        default=None,
        description="Cause of an unplanned loss — only set when termination_type='died'.",
    )
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    # ── Per-instance cultivation cycle (ADR-006 E1 / REQ-003, #565 Phase 2) ──
    # The grower's per-plant cultivation decision, the most specific tier of the
    # resolve_effective_cycle cascade (instance → species cultivation_cycle_type →
    # species botanical cycle_type). None = "same as the species" (non-breaking).
    # This is the PRACTISED cycle axis (#297): the botanical cycle_type stays
    # species-fixed; only the cultivation decision becomes instance-overridable —
    # e.g. an overwintered tomato grown perennial, or a strawberry grown as an annual.
    cultivation_cycle_type: CycleType | None = Field(
        default=None,
        description="Per-instance practised lifespan; overrides the species default for the season/"
        "overwintering and cycle-restart decisions. None = same as the species.",
    )
    # ── Genetic lineage (REQ-017 / REQ-003 D10) ──
    mother_key: str | None = Field(
        default=None,
        description="Denormalized lineage pointer to the parent (mother) plant instance this "
        "instance descended from — set for clonal pups spawned when a monocarpic mother enters "
        "its terminal reproductive phase (D10). None for directly-planted instances. The "
        "authoritative link is the descended_from graph edge (child → mother); this field "
        "mirrors it for cheap frontend ancestry lookups.",
    )
    # ── Controlled backward transitions (REQ-003 E3) ──
    reversion_count: int = Field(
        default=0,
        ge=0,
        description="Number of controlled phase reversions (e.g. re-vegging) this plant has undergone.",
    )
    # ── Vernalisation accumulation (REQ-003 E2) ──
    chill_days_accumulated: int = Field(
        default=0,
        ge=0,
        description="Accumulated vernalisation cold days; gates the vernalization_based transition once "
        "it reaches the species' vernalization_min_days.",
    )
    container_volume_liters: float | None = Field(
        default=None,
        ge=0.1,
        le=500,
        description="Actual container/pot volume in liters for this plant instance",
    )
    substrate_type_override: SubstrateType | None = Field(
        default=None,
        description="Direct substrate type — overrides substrate_batch_key lookup",
    )
    photo_refs: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of attachment ids (NFR-013 §2.2) for the plant photo gallery "
            "(REQ-034 §2.1). Display order is newest-first; never raw storage URLs."
        ),
    )
    cover_photo_ref: str | None = Field(
        default=None,
        description=(
            "attachment id marked as cover photo (REQ-034 §2.1). MUST be an element of "
            "photo_refs; None falls back to the first element of photo_refs."
        ),
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
