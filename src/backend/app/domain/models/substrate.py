from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import BufferCapacity, IrrigationStrategy, SubstrateType, WaterRetention


class MixComponent(BaseModel):
    """A component in a substrate mix — references an existing substrate + fraction."""

    substrate_key: str
    fraction: float = Field(ge=0.01, le=1.0)


class Substrate(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    #: Owning tenant — a **hybrid catalogue** marker (#1195).
    #:
    #: ``""`` is the seeded base catalogue every tenant reads, exactly as it is
    #: for :class:`~app.domain.models.species.Species` and ``Cultivar`` since
    #: #1090. A non-empty key is a mix a tenant created for itself: the operator
    #: decision on #1098 is that a community garden which mixes its own medium
    #: owns that mix, rather than pushing it into the catalogue everyone shares.
    #:
    #: Reads therefore take the *union* (own ∪ global), never a strict filter —
    #: a strict ``== @tenant_key`` would blank the whole seeded catalogue for
    #: every real tenant, which is the #324 regression in its other direction.
    tenant_key: str = ""
    type: SubstrateType = SubstrateType.SOIL
    brand: str | None = None
    name_de: str = ""
    name_en: str = ""
    is_mix: bool = False
    mix_components: list[MixComponent] = Field(default_factory=list)
    ph_base: float = Field(default=6.5, ge=0, le=14)
    ec_base_ms: float = Field(default=0.5, ge=0)
    water_retention: WaterRetention = WaterRetention.MEDIUM
    #: Air-filled porosity at container capacity, or ``None`` where the field does
    #: not apply (#1175).
    #:
    #: Nullable because a nutrient solution has no pore space to describe. The
    #: seeded ``Hydrokultur (kein Substrat)`` record carried ``100.0`` as a
    #: placeholder for "not applicable", and no consumer could tell that from a
    #: measured 100: it was volume-weighted into every mix that contained it,
    #: reported over MCP as a physical property and rendered as ``100.0 %`` in the
    #: detail view. The same record's ``composition`` was already allowed to be
    #: empty and mean exactly that; this is the same statement about the same
    #: record, in the field that was still lying.
    air_porosity_percent: float | None = Field(default=25.0, ge=0, le=100)
    #: Bulk constituents as volume fractions of the medium, summing to 1.0.
    #:
    #: **Bulk only** — see :attr:`additives`.
    composition: dict[str, float] = Field(default_factory=dict)
    #: Amendments the product contains, named without a quantity (#1175).
    #:
    #: One normalised vector cannot carry both bulk components and additives: peat
    #: and perlite are tens of percent by volume, lime and trace elements go in at
    #: single-digit kg/m³, two orders of magnitude below. Carried in
    #: :attr:`composition` they were read as real proportions — ``kalk: 0.10`` on
    #: BioBizz Light·Mix meant ten percent lime, which contradicted the
    #: ``ph_base: 6.2`` the same record declared, and trace elements are ppm by
    #: definition (#1152 §C).
    #:
    #: Deliberately a list of names and **not** a second numeric map. The catalogue
    #: has no sourced dose rate for any of these products, and the seed file's own
    #: header forbids inventing one; a plausible ``kalk: 0.005`` would look settled
    #: while being no better founded than the 0.10 it replaced. The record knows
    #: *that* the medium is limed, so that is what it says.
    additives: list[str] = Field(default_factory=list)
    #: True for a soil conditioner — a concentrate, not something a plant grows in.
    #:
    #: ``BioBizz Pre·Mix`` is 30 % peat and the rest bone meal, blood meal, guano,
    #: dolomite, seaweed and leonardite. It is typed ``peat`` because that is the
    #: material family, and the type stays: every ``dict[SubstrateType, ...]`` table
    #: in the engines (irrigation strategy, flush duration, EC class, pH-stability
    #: threshold, preparation steps) answers a question about medium physics with a
    #: silent ``.get(..., default)``, so a new ``soil_amendment`` member would have
    #: made five engines return a confident default for a thing that is not a
    #: medium — the same "not applicable encoded as a value" defect
    #: :attr:`air_porosity_percent` above exists to remove.
    #:
    #: What was actually wrong is that it was *selectable as a medium*, so that is
    #: what this flag gates (see ``SubstrateService.get_growing_medium``). It stays
    #: a legal **mix component**: blending Pre·Mix into a soil is what the product
    #: is for.
    is_amendment: bool = False
    buffer_capacity: BufferCapacity = BufferCapacity.MEDIUM
    reusable: bool = False
    max_reuse_cycles: int = Field(default=3, ge=1)
    water_holding_capacity_percent: float | None = Field(default=None, ge=0, le=100)
    easily_available_water_percent: float | None = Field(default=None, ge=0, le=100)
    cec_meq_per_100cm3: float | None = Field(default=None, ge=0)
    particle_size_mm: float | None = Field(default=None, ge=0)
    bulk_density_g_per_l: float | None = Field(default=None, ge=0)
    irrigation_strategy: IrrigationStrategy | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_composition(self) -> Substrate:
        if self.type == SubstrateType.NONE:
            if self.composition:
                msg = "Composition must be empty for substrate type 'none'."
                raise ValueError(msg)
            return self
        if self.composition:
            total = sum(self.composition.values())
            if abs(total - 1.0) > 0.01:
                msg = f"Composition fractions must sum to 1.0 (±0.01), got {total:.4f}."
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_mix_components(self) -> Substrate:
        if self.mix_components:
            total = sum(c.fraction for c in self.mix_components)
            if abs(total - 1.0) > 0.01:
                msg = f"Mix component fractions must sum to 1.0 (±0.01), got {total:.4f}."
                raise ValueError(msg)
        return self


class SubstrateBatch(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    #: Owning tenant — **strict**, unlike :class:`Substrate` (#1195).
    #:
    #: A batch is a physical thing one tenant mixed: a volume, a mix date, its own
    #: pH/EC history and reuse cycles. There is no such thing as a *global* batch,
    #: so reads filter on equality and never union with ``""``.
    #:
    #: A row left at ``""`` by the ``v0043`` backfill — one whose owner could not
    #: be established because plants of several tenants pointed at it — is
    #: consequently invisible to every tenant in ``full`` mode, since a real
    #: tenant key is never empty. That is the fail-safe direction (shown to nobody
    #: rather than to everybody) and it is why the migration *counts* those rows
    #: instead of guessing an owner. In ``light`` mode the sole operator resolves
    #: to ``""`` and still sees them, which is correct for a single-operator
    #: install.
    tenant_key: str = ""
    batch_id: str
    substrate_key: str = ""
    volume_liters: float = Field(ge=0)
    mixed_on: date
    last_amended: date | None = None
    cycles_used: int = Field(default=0, ge=0)
    ph_current: float | None = Field(default=None, ge=0, le=14)
    ec_current_ms: float | None = Field(default=None, ge=0)
    temperature_c: float | None = None
    ph_history: list[float] = Field(default_factory=list)
    ec_history: list[float] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
