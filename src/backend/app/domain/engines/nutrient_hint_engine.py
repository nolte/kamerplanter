"""The nutrient hint of a bed: ``ok | check | likely_deficit | insufficient_data`` (REQ-053 GP-FR-125, W-010).

Pure rules, no database (WP 8.10, #2653). The rule table is REQ-053 §15.3 "Regeltabelle Nährstoff-Hinweis"; this
module is its reference implementation.

**No threshold without a source (E-10).** Every agronomic threshold is configuration (:class:`NutrientHintConfig`)
and only takes part when it has a value *and* a ``source``. The research of WP 8.5
(``spec/analysis/agrobiology-req-053-wave8-ec.md``, addendum) closed none of them, so :data:`DEFAULT_CONFIG` has no
active threshold and the engine answers ``insufficient_data`` for every bed until somebody enters a sourced value.
The qualitative flags (preceding or standing nitrogen fixer, bark mulch, class D/E) are reason codes; they never carry
an amount and never produce a state on their own. The one qualitative rule active by default is the class D/E rule
(R-006, :data:`HIGH_CLASS_SOURCE`): it only *withholds* compost and P, it never raises a state.

**Salt limit (E-17 variant A).** The field-soil conductivity is no EC target; it is only read as the salt-limit hint
of :mod:`app.domain.engines.soil_salinity_hint`. When that sourced rule fires (inert by default, R-001 open), every
answer of a non-substrate bed carries the additive reason ``check_salt_content``. It never changes an amount and,
like the class D/E rule, **never changes the state**: the state is the nutrient *supply* (its ``check`` reads "check
the fertilising"), and a high salt content is no supply finding - raising an ``ok`` to ``check`` would send the
gardener to the feeding when the soil is, if anything, oversupplied. The reason code carries the hint on its own.

What the engine never does (hint-only list): compute or pre-fill a fertiliser amount, derive a feeder level for a
species without one (no family fallback, no silent default), assign a content class from a number, or credit an N
amount for a legume preceding crop.

Precedence (first match wins, all ``insufficient_data``): mineral substrate bed (``substrate_bed``, the EC logic of
REQ-004-A applies there) → no plant standing (``no_current_crop``) → plants stand, but the tenant may read none of
their species (``species_not_readable``) → no current species states its feeder level
(``demand_unknown``) → no rule with a source applies (``thresholds_without_source``). Otherwise the most severe state
of the sourced rules wins; the modifiers below adjust it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.common.enums import GrowingMediumKind, NutrientDemand
from app.domain.engines.soil_salinity_hint import SoilSalinityConfig, needs_salt_check
from app.domain.models.nutrient_hint import (
    DEFAULT_READ_WINDOW_DAYS,
    NutrientHint,
    NutrientHintConfidence,
    NutrientHintReason,
    NutrientHintState,
)
from app.domain.models.site import SoilProfile

#: Materials of a ``mulching`` event that bind nitrogen while they rot (GP-FR-125: "Rindenmulch zählt als N-bindend").
#: A qualitative flag; the amount it binds stays null ("stays null" item 12).
N_BINDING_MULCH_MATERIALS: frozenset[str] = frozenset({"bark_mulch"})
#: Parameters a CAL content class is read for. Mg is extracted by CaCl2, not CAL, and stays out (R-007).
CLASS_PARAMETERS: tuple[str, ...] = ("p", "k")
#: Classes D and E: P/K fertilising is mostly not needed, compost is no nutrient supply there (R-006).
HIGH_CONTENT_CLASSES: frozenset[str] = frozenset({"D", "E"})
#: The two institutional sources of the D/E rule (WP 8.5 addendum, R-006).
HIGH_CLASS_SOURCE = (
    "R-006: Bayerische Gartenakademie (LWG), Merkblatt 2202 Hinweise zur Düngung im Gemüsegarten (12/2020); "
    "Hessisches Landeslabor, Erläuterungen zur Bodenuntersuchung Acker und Grünland (2024)"
)
#: A content class is only read from a lab result by this extraction method (VDLUFA CAL, R-007).
CAL_METHOD = "cal"
#: ``soil_amendment`` materials that reset R1: they supply nitrogen. Compost is left out on purpose - it is no N
#: supplier (R-005) - although it still writes a feeding event for the fertiliser balance (W-007, §12.1).
N_INPUT_AMENDMENT_MATERIALS: frozenset[str] = frozenset({"manure", "horn_shavings"})

#: Strongest feeder level first: a mixed bed is judged by its hungriest stated crop.
_DEMAND_ORDER: tuple[NutrientDemand, ...] = (
    NutrientDemand.HEAVY_FEEDER,
    NutrientDemand.MEDIUM_FEEDER,
    NutrientDemand.LIGHT_FEEDER,
)
_SEVERITY: dict[NutrientHintState, int] = {"ok": 0, "check": 1, "likely_deficit": 2}


# ── Configuration ─────────────────────────────────────────────────────────────


def _has_source(source: str | None) -> bool:
    if source is None:
        return False
    text: str = source
    return bool(text.strip())


@dataclass(frozen=True)
class SourcedThreshold:
    """A threshold that is only used with both a value and the source it comes from (E-10)."""

    value: float | None = None
    source: str | None = None

    @property
    def active(self) -> bool:
        return self.value is not None and _has_source(self.source)


@dataclass(frozen=True)
class SourcedClasses:
    """The lab content classes that count as low supply.

    Class bounds differ by lab, year and federal state (R-007), so the rule is used only when its source names all
    three: ``lab``, ``year`` and ``region`` next to ``source``.
    """

    classes: frozenset[str] = frozenset()
    source: str | None = None
    lab: str | None = None
    year: int | None = None
    region: str | None = None

    @property
    def active(self) -> bool:
        return (
            bool(self.classes)
            and _has_source(self.source)
            and _has_source(self.lab)
            and self.year is not None
            and _has_source(self.region)
        )

    @property
    def cited(self) -> str:
        """The source as the answer names it: source, lab, year and region."""
        return f"{self.source} ({self.lab}, {self.year}, {self.region})"


@dataclass(frozen=True)
class SourcedFlag:
    """A qualitative rule that changes a state; off unless it is enabled *and* names its source."""

    enabled: bool = False
    source: str | None = None

    @property
    def active(self) -> bool:
        return self.enabled and _has_source(self.source)


def _threshold(table: Mapping[NutrientDemand, SourcedThreshold], demand: NutrientDemand) -> SourcedThreshold:
    """The threshold of a feeder level; a level the table leaves out has none."""
    return table[demand] if demand in table else SourcedThreshold()


def _null_per_demand() -> Mapping[NutrientDemand, SourcedThreshold]:
    return {demand: SourcedThreshold() for demand in NutrientDemand}


@dataclass(frozen=True)
class NutrientHintConfig:
    """The thresholds of the rule table. Defaults are ``null`` throughout: no value has a closed research item.

    * ``check_after_days`` / ``likely_deficit_after_days`` - days since the last nutrient input after which a bed of
      the feeder level is ``check`` / ``likely_deficit`` (rule R1; "stays null" items 3 and 4, R-013).
    * ``low_content_classes`` - the CAL classes of P or K that make a deficit likely (rule R2; R-006 covers only D/E,
      R-007: class limits are lab specific).
    * ``nitrogen_fixer_relief`` - a legume preceding crop lowers a ``likely_deficit`` of R1 to ``check`` (modifier M1;
      only the qualitative flag, never an N credit - "stays null" item 6, R-015).
    * ``bark_mulch_binding`` - bark mulch after the last N input turns an ``ok`` of R1 into ``check`` (modifier M2;
      "stays null" item 12, R-014). Off by default; the reason code is given either way.
    * ``soil_salinity`` - the sourced salt limit of a field soil (E-17 variant A, R-001): above it the hint carries
      the reason ``check_salt_content``; the state stays as the other rules set it. Inert by default.
    * ``read_window_days`` - how far back the care log is read. Every active R1 threshold must fit inside it, or an
      input just beyond the window would read as "not recorded" while still being within the threshold.

    The R1 thresholds cite research item R-013 (feeding interval per feeder level); none is closed.
    """

    check_after_days: Mapping[NutrientDemand, SourcedThreshold] = field(default_factory=_null_per_demand)
    likely_deficit_after_days: Mapping[NutrientDemand, SourcedThreshold] = field(default_factory=_null_per_demand)
    low_content_classes: SourcedClasses = field(default_factory=SourcedClasses)
    nitrogen_fixer_relief: SourcedFlag = field(default_factory=SourcedFlag)
    bark_mulch_binding: SourcedFlag = field(default_factory=SourcedFlag)
    soil_salinity: SoilSalinityConfig = field(default_factory=SoilSalinityConfig)
    read_window_days: int = DEFAULT_READ_WINDOW_DAYS

    def __post_init__(self) -> None:
        if self.read_window_days <= 0:
            raise ValueError("read_window_days must be positive.")
        for name, table in (
            ("check_after_days", self.check_after_days),
            ("likely_deficit_after_days", self.likely_deficit_after_days),
        ):
            for demand in NutrientDemand:
                threshold = _threshold(table, demand)
                if not threshold.active:
                    continue
                value = float(threshold.value or 0)
                if not 0 < value <= self.read_window_days:
                    window = self.read_window_days
                    raise ValueError(f"{name}.{demand.value} must lie within 0 < value <= read_window_days ({window}).")

    def active_rules(self) -> tuple[str, ...]:
        """Names of the thresholds that take part; empty for :data:`DEFAULT_CONFIG` (the E-10 test reads this)."""
        names = [
            f"{name}.{demand.value}"
            for name, table in (
                ("check_after_days", self.check_after_days),
                ("likely_deficit_after_days", self.likely_deficit_after_days),
            )
            for demand in NutrientDemand
            if _threshold(table, demand).active
        ]
        if self.low_content_classes.active:
            names += ["low_content_classes"]
        if self.nitrogen_fixer_relief.active:
            names += ["nitrogen_fixer_relief"]
        if self.bark_mulch_binding.active:
            names += ["bark_mulch_binding"]
        if self.soil_salinity.active:
            names += ["soil_salinity"]
        return tuple(names)


#: The shipped configuration: every threshold ``null`` (WP 8.5 closed none; E-10).
DEFAULT_CONFIG = NutrientHintConfig()


# ── Inputs ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NutrientHintInputs:
    """What the service gathered for one bed."""

    now: datetime
    growing_medium_kind: GrowingMediumKind | None = None
    #: The stored ``nutrient_demand`` of each species standing in the bed; ``None`` where the species has none or the
    #: tenant may not read it.
    species_demands: Sequence[NutrientDemand | None] = ()
    #: How many of ``species_demands`` are ``None`` because the tenant may not read the species.
    unreadable_species: int = 0
    #: The preceding crop fixes nitrogen: the newest rotation year before the current one (main crop or green
    #: manure), without the species standing now (``Species.nitrogen_fixing``, else the family's flag).
    preceding_nitrogen_fixing: bool = False
    #: A species standing in the bed now fixes nitrogen (a perennial legume, or one sown last year and still there).
    standing_nitrogen_fixing: bool = False
    #: The newest N input in the read window: any ``feeding``, or a ``soil_amendment`` with
    #: :data:`N_INPUT_AMENDMENT_MATERIALS`; ``None`` when none is recorded. A ``feeding`` counts whatever it supplies
    #: (a pure-K feeding too) until the care event carries an N field.
    last_nutrient_input_at: datetime | None = None
    #: The newest ``mulching`` with an N-binding material (:data:`N_BINDING_MULCH_MATERIALS`).
    last_n_binding_mulch_at: datetime | None = None
    #: ``p`` / ``k`` → the class of the newest lab result by CAL (:func:`lab_content_classes`).
    content_classes: Mapping[str, str] = field(default_factory=dict)
    #: The bed's soil profile; only its ``ec_ms_cm`` + ``ec_method`` are read, for the salt-limit hint.
    soil_profile: SoilProfile | None = None


def lab_content_classes(analyses: Iterable[Sequence[Mapping[str, Any]]]) -> dict[str, str]:
    """``p`` / ``k`` → the content class of the newest analysis that states one, from a lab only.

    ``analyses`` are the ``measurements`` of the soil analyses, **newest first**. A class is only read from a
    measurement with ``source = lab`` **and** ``extraction_method = cal``; a test kit, a sensor or another extraction
    never counts, and no class is derived from a value.
    """
    found: dict[str, str] = {}
    measurement: Mapping[str, Any]
    for measurements in analyses:
        for measurement in measurements:
            parameter = str(measurement.get("parameter"))
            content_class = measurement.get("content_class")
            if parameter not in CLASS_PARAMETERS or parameter in found or not content_class:
                continue
            if measurement.get("source") != "lab" or measurement.get("extraction_method") != CAL_METHOD:
                continue
            found[parameter] = str(content_class)
    return found


def is_n_input_amendment(material: str | None) -> bool:
    """Whether a ``soil_amendment`` material resets R1 (manure, horn shavings; never compost, R-005)."""
    return is_material_of(material, N_INPUT_AMENDMENT_MATERIALS)


def is_n_binding_mulch(material: str | None) -> bool:
    """Whether a ``mulching`` material binds nitrogen (the stored code, compared without case and spaces)."""
    return is_material_of(material, N_BINDING_MULCH_MATERIALS)


def is_material_of(material: str | None, materials: frozenset[str]) -> bool:
    """Whether a stored ``material`` code is one of ``materials`` (compared without case and outer spaces)."""
    if material is None:
        return False
    text: str = material
    return text.strip().lower() in materials


def strongest_demand(demands: Iterable[NutrientDemand | None]) -> NutrientDemand | None:
    """The hungriest stated feeder level, ``None`` when no species states one."""
    stated = {demand for demand in demands if demand is not None}
    return next((level for level in _DEMAND_ORDER if level in stated), None)


# ── Rules ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Verdict:
    state: NutrientHintState
    reason: NutrientHintReason
    source: str


def _feeding_rule(demand: NutrientDemand, inputs: NutrientHintInputs, config: NutrientHintConfig) -> _Verdict | None:
    """R1: days since the last nutrient input against the sourced thresholds of the feeder level."""
    check = _threshold(config.check_after_days, demand)
    likely = _threshold(config.likely_deficit_after_days, demand)
    active = [threshold for threshold in (likely, check) if threshold.active]
    if not active:
        return None
    if inputs.last_nutrient_input_at is None:
        # Not recorded is not the same as not fed: at most "check".
        return _Verdict("check", "no_feeding_recorded", str(active[0].source))
    elapsed: timedelta = inputs.now - inputs.last_nutrient_input_at
    days = elapsed.total_seconds() / 86400
    if likely.active and days > float(likely.value or 0):
        return _Verdict("likely_deficit", "feeding_overdue", str(likely.source))
    if check.active and days > float(check.value or 0):
        return _Verdict("check", "feeding_due", str(check.source))
    return _Verdict("ok", "fed_recently", str(active[0].source))


def _class_rule(inputs: NutrientHintInputs, config: NutrientHintConfig) -> list[_Verdict]:
    """R2: a lab class of P or K in the sourced low classes makes a deficit likely."""
    rule = config.low_content_classes
    classes = inputs.content_classes
    present: dict[str, str] = {parameter: classes[parameter] for parameter in CLASS_PARAMETERS if parameter in classes}
    if not rule.active or not present:
        return []
    source = rule.cited
    low: list[_Verdict] = []
    if present.get("p") in rule.classes:
        low += [_Verdict("likely_deficit", "p_class_low", source)]
    if present.get("k") in rule.classes:
        low += [_Verdict("likely_deficit", "k_class_low", source)]
    return low or [_Verdict("ok", "content_classes_sufficient", source)]


def _flags(inputs: NutrientHintInputs, config: NutrientHintConfig) -> tuple[list[NutrientHintReason], bool]:
    """The qualitative flags every answer carries, and whether compost / P are withheld (class D/E)."""
    flags: list[NutrientHintReason] = []
    # Field soil only: in a mineral substrate bed the EC logic of REQ-004-A applies, not a soil salt limit.
    if inputs.growing_medium_kind != GrowingMediumKind.MINERAL_SUBSTRATE and needs_salt_check(
        inputs.soil_profile, config.soil_salinity
    ):
        flags += ["check_salt_content"]
    if inputs.preceding_nitrogen_fixing:
        flags += ["preceding_nitrogen_fixer"]
    if inputs.standing_nitrogen_fixing:
        flags += ["standing_nitrogen_fixer"]
    if _mulch_after_input(inputs):
        flags += ["bark_mulch_n_binding"]
    classes: Mapping[str, str] = inputs.content_classes
    withheld = any(each in classes and classes[each] in HIGH_CONTENT_CLASSES for each in CLASS_PARAMETERS)
    if withheld:
        flags += ["p_or_k_class_high"]
    return flags, withheld


def _mulch_after_input(inputs: NutrientHintInputs) -> bool:
    mulch = inputs.last_n_binding_mulch_at
    if mulch is None:
        return False
    return inputs.last_nutrient_input_at is None or mulch > inputs.last_nutrient_input_at


def _withheld_source(withheld: bool) -> str | None:
    return HIGH_CLASS_SOURCE if withheld else None


def _insufficient(reason: NutrientHintReason, flags: list[NutrientHintReason], withheld: bool) -> NutrientHint:
    return NutrientHint("insufficient_data", "low", (reason, *flags), withheld, (), _withheld_source(withheld))


def assess(inputs: NutrientHintInputs, config: NutrientHintConfig = DEFAULT_CONFIG) -> NutrientHint:
    """The nutrient hint of one bed by the rule table (REQ-053 §15.3)."""
    flags, withheld = _flags(inputs, config)
    if inputs.growing_medium_kind == GrowingMediumKind.MINERAL_SUBSTRATE:
        return _insufficient("substrate_bed", flags, withheld)
    if not inputs.species_demands:
        return _insufficient("no_current_crop", flags, withheld)
    if inputs.unreadable_species >= len(inputs.species_demands):
        return _insufficient("species_not_readable", flags, withheld)
    demand = strongest_demand(inputs.species_demands)
    if demand is None:
        return _insufficient("demand_unknown", flags, withheld)

    feeding = _feeding_rule(demand, inputs, config)
    verdicts = ([feeding] if feeding is not None else []) + _class_rule(inputs, config)
    if not verdicts:
        return _insufficient("thresholds_without_source", flags, withheld)

    state = max((verdict.state for verdict in verdicts), key=lambda each: _SEVERITY[each])
    deciding = [verdict for verdict in verdicts if verdict.state == state]
    reasons: list[NutrientHintReason] = [verdict.reason for verdict in deciding]
    sources = [verdict.source for verdict in deciding]
    lowered = False

    # M1: a legume preceding crop softens a deficit that rests on the feeding age alone (flag only, no N credit).
    relief = config.nitrogen_fixer_relief
    if (
        state == "likely_deficit"
        and inputs.preceding_nitrogen_fixing
        and relief.active
        and all(verdict.reason == "feeding_overdue" for verdict in deciding)
    ):
        state, lowered = "check", True
        sources += [str(relief.source)]
    # M2: bark mulch after the last N input may bind N while it rots - an "ok" of the feeding age (R1, never of a lab
    # class) becomes "check", only with a sourced flag (R-014); without one the code stays a reason only.
    binding = config.bark_mulch_binding
    if (
        state == "ok"
        and "bark_mulch_n_binding" in flags
        and binding.active
        and all(verdict.reason == "fed_recently" for verdict in deciding)
    ):
        state, lowered = "check", True
        sources += [str(binding.source)]
    # ``check_salt_content`` (E-17 variant A) rides in ``flags`` only: it never changes the state (module docstring).

    partly_unknown = any(each is None for each in inputs.species_demands)
    if partly_unknown:
        reasons += ["demand_partly_unknown"]
    confidence = _confidence(deciding, partly_unknown=partly_unknown, adjusted=lowered)
    return NutrientHint(
        state,
        confidence,
        _unique([*reasons, *flags]),
        withheld,
        _unique(sources),
        _withheld_source(withheld),
    )


def _unique[T](items: Iterable[T]) -> tuple[T, ...]:
    """``items`` without repeats, in their first order."""
    seen: list[T] = []
    for item in items:
        if item not in seen:
            seen += [item]
    return tuple(seen)


def _confidence(deciding: Sequence[_Verdict], *, partly_unknown: bool, adjusted: bool) -> NutrientHintConfidence:
    """``high`` when a lab class decided, ``medium`` for the feeding age, ``low`` with a gap or an adjusted state."""
    if partly_unknown or adjusted or any(verdict.reason == "no_feeding_recorded" for verdict in deciding):
        return "low"
    if any(verdict.reason in ("p_class_low", "k_class_low", "content_classes_sufficient") for verdict in deciding):
        return "high"
    return "medium"
