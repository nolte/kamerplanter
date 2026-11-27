from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums import (
    CycleType,
    FailureCauseClass,
    PathogenConfirmationSource,
    SoilHazard,
    SoilHazardFollowUpKind,
    SubstrateType,
    TerminationCause,
    TerminationType,
)
from app.domain.engines.failure_cause_engine import find_failure_cause_violations
from app.domain.models.site import MAX_CONTAINER_VOLUME_L

#: A caller-supplied document key. ``min_length=1`` because ``""`` is not a key:
#: it resolves to nothing, and before this constraint existed it was *also* not
#: resolved — ``PlantInstanceService._resolve_references`` read ``if not value``
#: and treated an empty string as "no reference supplied". Measured on the
#: pre-constraint route: ``POST {"species_key": ""}`` answered **201** and stored
#: a plant whose species does not exist; ``PUT`` stripped an existing plant's
#: species the same way.
#:
#: Refusing it here rather than in the service is deliberate — ``""`` is
#: malformed input, not a reference to something the caller may not see, so the
#: honest answer is a 422 naming the field and not the 404 the service would
#: raise. The service still resolves a stored ``""`` (other callers exist), so
#: the two halves overlap rather than depend on each other.
ReferenceKey = Annotated[str, Field(min_length=1)]

#: The nullable form. The constraint sits on the ``str`` arm of the union, never
#: on the union itself: ``None`` must stay accepted, because an explicit ``null``
#: is how ``PATCH`` clears a reference (#1098) and omission is how ``PUT`` does.
OptionalReferenceKey = ReferenceKey | None


class PlantCreate(BaseModel):
    instance_id: str
    species_key: ReferenceKey
    cultivar_key: OptionalReferenceKey = None
    site_key: OptionalReferenceKey = None
    location_key: OptionalReferenceKey = None
    slot_key: OptionalReferenceKey = None
    substrate_batch_key: OptionalReferenceKey = None
    substrate_key: OptionalReferenceKey = None
    plant_name: str | None = None
    planted_on: date
    current_phase_key: OptionalReferenceKey = None
    container_volume_liters: float | None = Field(default=None, ge=0.1, le=MAX_CONTAINER_VOLUME_L)
    substrate_type_override: SubstrateType | None = None
    # ADR-006 E1 — per-instance cultivation cycle override; None = "same as the species".
    cultivation_cycle_type: CycleType | None = None


class PlantPatch(BaseModel):
    """Partial update of a plant instance — only the fields actually sent (#1098).

    The sibling ``PUT`` takes :class:`PlantCreate` and is a **full replacement**:
    it assigns thirteen of the fourteen body fields onto the stored row, so every
    optional field the caller omits is written back as ``None`` and — because
    ``ArangoPlantInstanceRepository._update_is_full_replace`` is ``True``, which it
    must be so a ``PUT`` can *clear* a nullable field — removed from the document.

    Measured on the real route: a call carrying only the three required fields
    plus the one being changed erases ``location_key``, ``slot_key``,
    ``cultivar_key``, ``plant_name``, ``container_volume_liters`` and
    ``substrate_batch_key``. Nothing in the endpoint's name or its schema says so.
    That is fine for the edit form, which always sends the whole record, and a trap
    for anything composing a request from the schema alone.

    Here **omitted means untouched** and an explicit ``null`` means *clear this
    field*. The two are distinguished by ``model_fields_set`` (via
    ``exclude_unset``), not by the value — a dump that could not tell them apart
    would make one of the two intents unreachable.

    ``instance_id`` and ``current_phase_key`` are deliberately **absent**.
    ``instance_id`` is the plant's human-facing identity, and renaming a plant as
    a side effect of setting its substrate is the class of surprise this endpoint
    removes. ``current_phase_key`` is server-managed — the ``PUT`` excludes it too
    — and moves only through the phase-transition path, which enforces the state
    machine (REQ-003); accepting it here would be a second, ungated way to set a
    phase. ``extra="forbid"`` rejects both outright rather than dropping them,
    because a silently ignored field reads to the caller as success.
    """

    species_key: OptionalReferenceKey = None
    cultivar_key: OptionalReferenceKey = None
    site_key: OptionalReferenceKey = None
    location_key: OptionalReferenceKey = None
    slot_key: OptionalReferenceKey = None
    substrate_batch_key: OptionalReferenceKey = None
    substrate_key: OptionalReferenceKey = None
    plant_name: str | None = None
    planted_on: date | None = None
    container_volume_liters: float | None = Field(default=None, ge=0.1, le=MAX_CONTAINER_VOLUME_L)
    substrate_type_override: SubstrateType | None = None
    cultivation_cycle_type: CycleType | None = None

    model_config = {"extra": "forbid"}


class RemovePlantRequest(BaseModel):
    """Optional body for POST /{key}/remove (REQ-003 E5).

    Backward compatible: an empty body keeps the previous plain-removal behaviour.
    ``termination_cause`` is only valid together with ``termination_type='died'``.

    The cause class (REQ-003 E5 v2.23; pathogen fields v2.24, #2888) follows the pre-fill table: an abiotic
    cause may omit it (it is derived), ``disease``/``pest`` must name foliar or soil. A pathogen is only valid
    for a soil-borne class; ``failure_pathogen_source`` only for a confirmed pathogen, which needs one.
    Violations answer 422 here, from the same rule the service applies.
    """

    termination_type: TerminationType | None = None
    termination_cause: TerminationCause | None = None
    failure_cause_class: FailureCauseClass | None = Field(
        default=None,
        description=(
            "Where the cause sat (died only). Omit to take the pre-fill of the cause; required for disease "
            "(disease_foliar/disease_soil) and pest (pest_foliar/pest_soil)."
        ),
        examples=["disease_soil"],
    )
    failure_pathogen: SoilHazard | None = Field(
        default=None,
        description="Pathogen of a soil-borne loss (pest_soil/disease_soil), one of the soil-hazard list.",
        examples=["verticillium"],
    )
    failure_pathogen_confirmed: bool | None = Field(
        default=None,
        description="Whether the named pathogen was confirmed; defaults to false when a pathogen is named.",
        examples=[True],
    )
    failure_pathogen_source: PathogenConfirmationSource | None = Field(
        default=None,
        description="Who confirmed the pathogen; required when failure_pathogen_confirmed is true.",
        examples=["lab_test"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"termination_type": "died", "termination_cause": "frost"},
                {
                    "termination_type": "died",
                    "termination_cause": "heat",
                    "failure_cause_class": "disease_soil",
                    "failure_pathogen": "verticillium",
                    "failure_pathogen_confirmed": True,
                    "failure_pathogen_source": "lab_test",
                },
            ]
        }
    )

    @model_validator(mode="after")
    def _failure_cause_fits(self) -> Self:
        """The rule of the pre-fill table, read from its one home (BACKEND.md §5.4)."""
        violations = find_failure_cause_violations(
            termination_type=self.termination_type,
            termination_cause=self.termination_cause,
            failure_cause_class=self.failure_cause_class,
            failure_pathogen=self.failure_pathogen,
            failure_pathogen_confirmed=self.failure_pathogen_confirmed,
            failure_pathogen_source=self.failure_pathogen_source,
        )
        if violations:
            raise ValueError("; ".join(violations))
        return self


class SpeciesSummary(BaseModel):
    """Denormalized species fields for human-readable plant labels."""

    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    #: Language code -> names in preference order (REQ-001, #2902).
    common_names_i18n: dict[str, list[str]] = Field(default_factory=dict)


class CultivarSummary(BaseModel):
    """Denormalized cultivar fields for human-readable plant labels."""

    name: str


class PlantRunSummaryResponse(BaseModel):
    """A compact reference to a planting run a plant instance belongs to."""

    key: str = Field(description="Document key of the planting run.")
    name: str = Field(description="Human-readable name of the planting run.")
    status: str = Field(description="Current lifecycle status of the planting run.")


class PlantResponse(BaseModel):
    key: str
    instance_id: str
    species_key: str
    cultivar_key: str | None
    site_key: str | None = None
    location_key: str | None = None
    slot_key: str | None
    substrate_batch_key: str | None
    substrate_key: str | None = None
    plant_name: str | None
    planted_on: date
    removed_on: date | None
    termination_type: TerminationType | None = None
    termination_cause: TerminationCause | None = None
    failure_cause_class: FailureCauseClass | None = Field(
        default=None,
        description="Where the cause of a died loss sat (#2888). null = no class: legacy data or a bulk bed clear.",
        examples=["pest_soil"],
    )
    failure_pathogen: SoilHazard | None = Field(
        default=None,
        description="Pathogen named for a soil-borne loss, one of the soil-hazard list; null when none was named.",
        examples=["clubroot"],
    )
    failure_pathogen_confirmed: bool | None = Field(
        default=None,
        description="Whether the named pathogen was confirmed; null when no pathogen was named.",
        examples=[False],
    )
    failure_pathogen_source: PathogenConfirmationSource | None = Field(
        default=None,
        description="Who confirmed the pathogen; null unless it was confirmed.",
        examples=["clear_symptoms"],
    )
    current_phase: str = ""
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    # REQ-017 / REQ-003 D10 — clonal-pup ancestry pointer (mother instance key).
    mother_key: str | None = None
    container_volume_liters: float | None = None
    substrate_type_override: SubstrateType | None = None
    # ADR-006 E1 — per-instance cultivation cycle override (None = same as the species).
    cultivation_cycle_type: CycleType | None = None
    species: SpeciesSummary | None = None
    cultivar: CultivarSummary | None = None
    planting_runs: list[PlantRunSummaryResponse] | None = Field(
        default=None,
        description=(
            "The planting runs the plant is attached to, newest first (#3015). Filled by the list route "
            "`GET /plant-instances` only; `null` on every other route means *not resolved here*, not *no run* - "
            "`GET /plant-instances/{key}/planting-runs` answers it for one plant."
        ),
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SoilHazardFollowUpResponse(BaseModel):
    """What the app proposes after a soil-borne loss (REQ-053 §11.3a Nr. 5, #2888 F-20); nothing is written yet."""

    kind: SoilHazardFollowUpKind = Field(
        description=(
            "`offer`: take the confirmed pathogen over into the bed - the client asks, and on yes sends "
            "`POST /locations/{location_key}/soil-hazards` with `plant_key`. `clean_system`: a hydroponic location, "
            "no soil hazard - clean and disinfect the system before replanting."
        ),
        examples=["offer"],
    )
    location_key: str = Field(description="The bed or hydroponic location of the loss.", examples=["loc_b03"])
    hazard: SoilHazard | None = Field(
        default=None, description="The hazard the offer would record; null for `clean_system`.", examples=["clubroot"]
    )
    confirmed_at: date | None = Field(
        default=None,
        description="The day of the loss, recorded as the confirmation date; null for `clean_system`.",
        examples=["2026-07-01"],
    )
    source: PathogenConfirmationSource | None = Field(
        default=None, description="How the pathogen was confirmed; null for `clean_system`.", examples=["lab_test"]
    )


class RemovePlantResponse(PlantResponse):
    """``POST /plant-instances/{key}/remove``: the ended plant and what the app proposes after its loss."""

    soil_hazard_follow_up: SoilHazardFollowUpResponse | None = Field(
        default=None,
        description=(
            "After a soil-borne loss: the offer to take its confirmed, listed pathogen over into the bed, or the "
            "clean-system hint at a hydroponic location; null otherwise. An unconfirmed loss is never offered."
        ),
        examples=[
            {
                "kind": "offer",
                "location_key": "loc_b03",
                "hazard": "clubroot",
                "confirmed_at": "2026-07-01",
                "source": "lab_test",
            }
        ],
    )


class FailureCauseRuleResponse(BaseModel):
    """One row of the cause-class pre-fill table, resolved for the plant (REQ-003 E5, research §5)."""

    termination_cause: TerminationCause = Field(description="The observed cause this row is for.", examples=["heat"])
    prefill: FailureCauseClass | None = Field(
        description="Class pre-filled for the cause; null = the gardener must choose (disease, pest).",
        examples=["abiotic"],
    )
    choices: list[FailureCauseClass] = Field(
        description="Every class that may be recorded for the cause, the pre-fill included.",
        examples=[["abiotic", "disease_soil"]],
    )
    asks_wilt_follow_up: bool = Field(
        description=(
            "Whether the dialog asks if the plant wilted on moist soil or had brown vessels or roots; a yes "
            "records wilt_follow_up_class. Always for heat, drought and waterlogging, for unknown only on a "
            "wilt-prone family."
        ),
        examples=[True],
    )


class TerminationOptionsResponse(BaseModel):
    """What the termination dialog offers for one plant (REQ-003 E5/E6, REQ-053 §11.3a, #2888 F-19)."""

    suggested_cause: TerminationCause | None = Field(
        description="Cause to pre-fill: bolting when the plant stands in a premature bolting phase, else null.",
        examples=["bolting"],
    )
    wilt_prone_family: bool = Field(
        description="Whether the plant's family is wilt-prone (Solanaceae, Brassicaceae, Cucurbitaceae, Rosaceae).",
        examples=[True],
    )
    rules: list[FailureCauseRuleResponse] = Field(
        description="One row per termination cause, in display order.",
    )
    wilt_follow_up_class: FailureCauseClass = Field(
        description="Class a yes to the wilt follow-up records.",
        examples=["disease_soil"],
    )
    pathogen_classes: list[FailureCauseClass] = Field(
        description="Classes for which a pathogen may be named.",
        examples=[["pest_soil", "disease_soil"]],
    )
    pathogens: list[SoilHazard] = Field(
        description="The pathogens that may be named: the soil-hazard list.",
        examples=[["clubroot", "verticillium"]],
    )
    confirmation_sources: list[PathogenConfirmationSource] = Field(
        description="Who may have confirmed a pathogen.",
        examples=[["lab_test", "advisory_service", "clear_symptoms"]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "suggested_cause": None,
                    "wilt_prone_family": True,
                    "rules": [
                        {
                            "termination_cause": "heat",
                            "prefill": "abiotic",
                            "choices": ["abiotic", "disease_soil"],
                            "asks_wilt_follow_up": True,
                        }
                    ],
                    "wilt_follow_up_class": "disease_soil",
                    "pathogen_classes": ["pest_soil", "disease_soil"],
                    "pathogens": ["clubroot", "verticillium"],
                    "confirmation_sources": ["lab_test", "advisory_service", "clear_symptoms"],
                }
            ]
        }
    )


class TerminationTypeCountResponse(BaseModel):
    termination_type: TerminationType
    count: int


class TerminationCauseCountResponse(BaseModel):
    termination_cause: TerminationCause
    count: int


class PhaseLossCountResponse(BaseModel):
    phase_name: str
    count: int


class SurvivalStatsResponse(BaseModel):
    """Survival-rate / failure-cause analytics for the tenant (REQ-003 G1)."""

    total: int
    terminated: int
    active: int
    died: int
    survived: int
    survival_rate: float
    by_termination_type: list[TerminationTypeCountResponse] = Field(default_factory=list)
    by_termination_cause: list[TerminationCauseCountResponse] = Field(default_factory=list)
    loss_by_phase: list[PhaseLossCountResponse] = Field(default_factory=list)


class PlantInstanceInPhaseResponse(BaseModel):
    """A tenant's active plant instance currently in a given phase definition (FIX-01 List 1).

    ``days_in_phase`` is intentionally NOT part of the payload: the frontend derives it
    from ``current_phase_started_at`` so the elapsed count stays live without re-fetching.
    """

    key: str
    instance_id: str
    plant_name: str | None = None
    species_key: str
    species_scientific_name: str | None = None
    species_common_names: list[str] = Field(default_factory=list)
    species_common_names_i18n: dict[str, list[str]] = Field(default_factory=dict)
    location_key: str | None = None
    location_name: str | None = None
    slot_key: str | None = None
    slot_label: str | None = None
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None


class PlantInstancesInPhaseResponse(BaseModel):
    """List-1 payload: the tenant's active instances in a phase definition + total count (R3)."""

    total: int
    items: list[PlantInstanceInPhaseResponse] = Field(default_factory=list)


class ValidatePlantingRequest(BaseModel):
    species_key: str


class ValidatePlantingResponse(BaseModel):
    valid: bool
    warnings: list[str]
    benefits: list[str]


class ActiveChannelDosage(BaseModel):
    fertilizer_key: str
    product_name: str
    ml_per_liter: float
    optional: bool = False
    mixing_priority: int = 50


class ActiveChannelResponse(BaseModel):
    channel_id: str
    label: str
    application_method: str
    target_ec_ms: float | None = None
    target_ph: float | None = None
    plan_key: str
    plan_name: str
    entry_key: str | None = None
    phase_name: str
    week_start: int
    week_end: int
    dosages: list[ActiveChannelDosage] = Field(default_factory=list)


class AssignNutrientPlanRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""


class AssignNutrientPlanStatusResponse(BaseModel):
    """Acknowledgement that a nutrient plan was assigned to a plant instance."""

    status: str = Field(description="Assignment status marker (always ``assigned``).")
