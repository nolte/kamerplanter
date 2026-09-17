"""Physical invariants of `substrates.yaml` that a JSON Schema cannot express (#1152).

The file declared no schema and shipped three physically impossible records: air
porosity plus water-holding capacity above 100 %, on the same pore space. Adding
`substrates.schema.yaml` pins structure, types and per-field ranges — but every
invariant that actually catches these defects is **cross-field**, and JSON Schema
has no arithmetic across properties. So the schema and this module are two halves
of one check, and a green schema run alone means less than it looks like.

Each rule below is asserted twice: once as a rule, against fixtures that sit on
its boundary, and once over the real seed file. The first is what makes the
boundary a decision rather than an accident of the data; the second is what makes
it bite.

Not covered here: the CEC plausibility band. Its *unit* is settled — the values
are per 100 cm³ of volume, the field is named ``cec_meq_per_100cm3`` and the mix
engine weights it by volume (#1152 §F) — but a per-type band still is not, and
writing one from the values present would only ratify them. The literature
figures in REQ-019 are mass-based (meq/100 g) and converting them needs each
source's own bulk density, which those sources mostly do not report; assembling
that table across fourteen substrate types is a data job, not an inference, and
#1175 deliberately leaves it rather than guessing a band. The one record that
fits neither reading is named in #1152 §F: sphagnum at CEC 8 and 30 g/L implies
267 meq/100 g, above its band, which is a second reason a band derived from this
data would be wrong.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

import app
from app.migrations.yaml_loader import load_yaml

#: Total porosity of even the lightest horticultural medium tops out around 95 %.
#: 100 is used as the invariant because it is the physically impossible line —
#: anything above it is wrong regardless of which medium is meant, so the rule
#: needs no per-type table to be correct.
_MAX_TOTAL_POROSITY = 100.0

#: Composition maps are volume fractions of one medium and must close.
_COMPOSITION_SUM = 1.0
_COMPOSITION_TOLERANCE = 0.01

#: Components that make a medium conductive. A record declaring one of these and
#: `ec_base_ms: 0.0` contradicts itself — and `ec_base_ms` is subtracted from the
#: target as EC-net in `calculate_mixing_protocol`, so the plant is dosed as if
#: the substrate contributed nothing.
_FERTILISER_COMPONENTS = frozenset(
    {"langzeitduenger", "organischer_duenger", "fledermausguano", "pre_mix", "wurmhumus"}
)

#: Amendments dosed by mass, not by volume. Lime and a trace-element blend go into
#: a growing medium at single-digit kg/m³ — well under one percent by volume — so a
#: normalised volume vector cannot carry them next to peat and perlite without
#: reading as ten percent lime (#1152 §C, #1175). They live in ``additives``, which
#: names them and asserts no quantity, because this file has no sourced dose rate
#: for any of them and its own header forbids inventing one.
#:
#: Deliberately only these three. ``wurmhumus``, ``organischer_duenger``,
#: ``fledermausguano``, ``pre_mix``, ``seetang``, ``knochenmehl``, ``blutmehl`` and
#: ``leonardit`` are bulk constituents at the percentages the records declare — a
#: wider set would have moved real volume out of the vector and made the
#: renormalisation below a rewrite rather than a rescale.
_ADDITIVE_COMPONENTS = frozenset({"kalk", "dolomit", "spurenelemente"})

#: Types that are not a medium at all. ``air_porosity_percent`` is a property of a
#: pore space, and a nutrient solution has none — the field does not apply rather
#: than evaluating to a number (#1152 §E).
_NON_SUBSTRATE_TYPES = frozenset({"hydro_solution", "none"})

#: Records that violate an invariant below and are **not** corrected here, because
#: correcting them needs a sourced horticultural value and this file's own header
#: says "do not invent or alter numeric values here". Registered rather than
#: skipped, in the shape ``SCHEMA_DEBT_CEILING`` and ``ALLOWED_DISCREPANCIES``
#: already use in this suite: a violation outside the register fails, and a
#: register entry that has *stopped* violating fails too, so the debt cannot
#: outlive the debt.
#:
#: Tracked in the follow-up issue split out of #1152.
#: Rule identifiers. Explicit constants rather than matching words in the failure
#: message: the first version of this register keyed relevance on ``"porosity" in
#: what`` while the message says "pore space", so the healed-check below never
#: fired and the register could never expire. Caught by healing an entry on a copy
#: of the seed file and observing green.
_RULE_POROSITY = "porosity"
_RULE_FERTILISER_EC = "fertiliser-ec"

_KNOWN_OPEN: dict[str, tuple[str, str]] = {
    # Empty since #1175 closed `Sphagnum-Moos (getrocknet)` with a citation (see the
    # record). The shape stays: the next unsourced violation registers here, with
    # its rule and the search that failed to source it, and leaves the moment it
    # is fixed.
}


def _substrates() -> list[dict[str, Any]]:
    return load_yaml("substrates.yaml")["substrates"]


def _label(entry: dict[str, Any]) -> str:
    return f"{entry.get('brand') or '-'} / {entry.get('name_de')}"


# ── the rules, on their own boundaries ───────────────────────────────────────


def _total_porosity(entry: dict[str, Any]) -> float:
    return float(entry.get("air_porosity_percent") or 0) + float(entry.get("water_holding_capacity_percent") or 0)


@pytest.mark.parametrize(
    ("air", "whc", "ok"),
    [(59.0, 40.0, True), (60.0, 40.0, True), (61.0, 40.0, False)],
    ids=["99", "100", "101"],
)
def test_the_porosity_rule_sits_where_it_is_meant_to(air: float, whc: float, ok: bool) -> None:
    """The boundary is pinned, not inferred from whatever the data happens to hold.

    Without this, a rule written as `< 100` or `<= 99` would look identical against
    today's file and disagree the first time a record lands exactly on 100.
    """
    entry = {"air_porosity_percent": air, "water_holding_capacity_percent": whc}

    assert (_total_porosity(entry) <= _MAX_TOTAL_POROSITY) is ok


def test_the_fertiliser_rule_needs_both_halves() -> None:
    """A fertilised medium with zero EC is the contradiction; either half alone is fine."""
    assert _declares_fertiliser({"composition": {"langzeitduenger": 0.05}})
    assert not _declares_fertiliser({"composition": {"perlit": 1.0}})


def _declares_fertiliser(entry: dict[str, Any]) -> bool:
    return bool(set(entry.get("composition") or {}) & _FERTILISER_COMPONENTS)


# ── the rules, over the real seed file ───────────────────────────────────────


def test_air_and_water_never_exceed_the_pore_space_they_share() -> None:
    """Both are volume percentages of the *same* pore space (#1152 §A).

    The three offenders were the two rockwool records (40 + 80, 35 + 85) and dried
    sphagnum (25 + 80). The other 26 entries sat between 53 % and 85 %, which is
    what rules out a definitional quirk of the field and leaves "three wrong
    values".

    **Sphagnum closed under #1175**, and the last register entry went with it —
    which the healed-check below enforced: with the values corrected and the entry
    still present the test failed with "must be removed from _KNOWN_OPEN". The pair
    is measured at the record's own bulk density (Kämäräinen et al. 2018, Mires and
    Peat 21(17): loosely packed 40 mm fibres at ≈30 g/dm³, ≈28 vol-% water at pF 1,
    total porosity 97.4–97.8 %). The old 80 was the saturation-and-drain reading
    (Müller & Glatzel 2021: 28.4 g/g at 0.03 g/cm³ = 85 vol-%), not the −10 hPa
    reading the field is defined in; the citations live in the record.
    """
    offenders = {
        e.get("name_de"): f"{e.get('air_porosity_percent')} + {e.get('water_holding_capacity_percent')}"
        for e in _substrates()
        if _total_porosity(e) > _MAX_TOTAL_POROSITY
    }

    _assert_only_known_open(offenders, _RULE_POROSITY, "air + water-holding exceeds the shared pore space")


def test_easily_available_water_is_a_subset_of_what_is_held() -> None:
    """Holds today; pinned so it stays true. A plant cannot extract more than is there."""
    violations = [
        f"{_label(e)}: eaw {e.get('easily_available_water_percent')} > whc {e.get('water_holding_capacity_percent')}"
        for e in _substrates()
        if e.get("easily_available_water_percent") is not None
        and e.get("water_holding_capacity_percent") is not None
        and float(e["easily_available_water_percent"]) > float(e["water_holding_capacity_percent"])
    ]

    assert not violations, "; ".join(violations)


def test_every_composition_closes() -> None:
    """Holds today; pinned because the maps are read as real proportions.

    That reading is what makes #1152 §C a defect rather than a labelling choice:
    if the vector sums to 1.0, a `kalk: 0.10` really is ten percent lime.
    """
    violations = [
        f"{_label(e)}: {sum((e.get('composition') or {}).values()):.3f}"
        for e in _substrates()
        # An *empty* composition is not a broken one: `Hydrokultur (kein Substrat)`
        # composes nothing because there is no substrate. The rule is "if a medium
        # names components, they close" — writing it as "every entry sums to 1.0"
        # would have forced a fake component onto the one honest record.
        if e.get("composition") and abs(sum(e["composition"].values()) - _COMPOSITION_SUM) > _COMPOSITION_TOLERANCE
    ]

    assert not violations, "composition fractions do not sum to 1.0: " + "; ".join(violations)


def test_a_fertilised_medium_declares_a_conductivity() -> None:
    """`Lechuza PON` declared 5 % slow-release fertiliser and `ec_base_ms: 0.0` (#1152 §B).

    Not a cosmetic contradiction: `ec_base_ms` is subtracted from the target as
    EC-net, so a plant in that medium is dosed as though the substrate contributed
    nothing at all.

    **Closed under #1175**, and the register entry went with it — which is what the
    healed-check below enforces. LECHUZA\'s own EU-FPR declaration lists the
    controlled-release fertiliser as an ingredient (so the component was the right
    half) and publishes "Elektrische Leitfähigkeit (EC): 5 mS/m" = 0.05 mS/cm (so
    the zero was the wrong half). The citation lives in the record.

    The rule stays, and stays over the whole file: it is the invariant, not a
    single record\'s ticket.
    """
    offenders = {
        e.get("name_de"): f"{sorted(set(e.get('composition') or {}) & _FERTILISER_COMPONENTS)} with ec_base_ms=0"
        for e in _substrates()
        if _declares_fertiliser(e) and float(e.get("ec_base_ms") or 0) == 0.0
    }

    _assert_only_known_open(offenders, _RULE_FERTILISER_EC, "a fertilised medium declares zero conductivity")


def test_every_entry_declaring_cec_also_declares_bulk_density() -> None:
    """Without bulk density the volume/mass conversion is not possible at all.

    Which is the precondition for #1152 §F's option 2 (rewrite the values) even
    being available — so it is worth holding true before the decision, not after.
    """
    missing = [
        _label(e)
        for e in _substrates()
        if e.get("cec_meq_per_100cm3") is not None and not e.get("bulk_density_g_per_l")
    ]

    assert not missing, "CEC declared without bulk_density_g_per_l: " + "; ".join(missing)


def _assert_only_known_open(offenders: dict[str, str], rule: str, what: str) -> None:
    """Fail on an unregistered violation, and on a register entry that has healed.

    Both directions matter. The first is the invariant. The second is what stops
    the register becoming a permanent exemption list: the moment a value is
    corrected its entry has to go, so "known open" cannot sit on data that is now
    fine. ``rule`` scopes the second check — a register keyed by record name has to
    know which invariant each entry answers to, or the porosity rule would report
    the EC entry as healed.
    """
    unregistered = {name: detail for name, detail in offenders.items() if name not in _KNOWN_OPEN}
    assert not unregistered, f"{what}: " + "; ".join(f"{n} ({d})" for n, d in sorted(unregistered.items()))

    healed = [name for name, (entry_rule, _) in _KNOWN_OPEN.items() if entry_rule == rule and name not in offenders]
    assert not healed, f"these no longer violate '{what}' and must be removed from _KNOWN_OPEN: {sorted(healed)}"


# ── additives are not bulk components (#1175 model fix 1) ────────────────────


def _is_amendment(entry: dict[str, Any]) -> bool:
    return bool(entry.get("is_amendment"))


def _additives_in_bulk(entry: dict[str, Any]) -> set[str]:
    return set(entry.get("composition") or {}) & _ADDITIVE_COMPONENTS


def test_the_additive_rule_exempts_an_amendment_and_only_an_amendment() -> None:
    """The rule is about *media*, and that scoping is the decision, not a loophole.

    A growing medium is mostly bulk, so a lime fraction inside its normalised
    vector is read as ten percent lime. An amendment **is** the concentrate — its
    dolomite really is a tenth of the product — so the same key means something
    else there. Pinned with fixtures so the exemption cannot later be widened by
    accident into "additive keys are fine anywhere".
    """
    medium = {"composition": {"torf": 0.9, "kalk": 0.1}}
    amendment = {"is_amendment": True, "composition": {"torf": 0.9, "dolomit": 0.1}}
    clean_medium = {"composition": {"torf": 0.7, "perlit": 0.3}}

    assert _additives_in_bulk(medium) and not _is_amendment(medium)
    assert _additives_in_bulk(amendment) and _is_amendment(amendment)
    assert not _additives_in_bulk(clean_medium)


def test_no_growing_medium_carries_an_additive_as_a_bulk_component() -> None:
    """One normalised vector cannot hold both bulk components and additives (#1152 §C).

    They differ by two orders of magnitude: peat and perlite are tens of percent
    of the volume, lime is kilograms per cubic metre. Because the vector closes to
    1.0 — pinned by ``test_every_composition_closes`` — a ``kalk: 0.10`` is a
    literal ten percent lime, which would put the medium far above the ``ph_base:
    6.2`` the same record declares.
    """
    offenders = {
        _label(e): sorted(_additives_in_bulk(e))
        for e in _substrates()
        if not _is_amendment(e) and _additives_in_bulk(e)
    }

    assert not offenders, "additives carried as bulk components: " + "; ".join(
        f"{n} ({', '.join(k)})" for n, k in sorted(offenders.items())
    )


# ── "not applicable" is absent, not a number (#1175 model fix 2) ─────────────


def test_a_non_substrate_declares_no_air_porosity() -> None:
    """``Hydrokultur`` carried ``air_porosity_percent: 100.0`` (#1152 §E).

    That is "not applicable" written as a number, and it does not stay in the
    record: the field is read by ``calculate_mix_properties``, by the substrate
    MCP summary and by the detail view, none of which can tell a measured 100 from
    a placeholder. The empty ``composition`` on the same record was already
    allowed to say "there is nothing here"; the porosity now says it the same way.
    """
    offenders = {
        _label(e): e.get("air_porosity_percent")
        for e in _substrates()
        if e.get("type") in _NON_SUBSTRATE_TYPES and e.get("air_porosity_percent") is not None
    }

    assert not offenders, "a non-substrate declares an air porosity: " + "; ".join(
        f"{n} ({v})" for n, v in sorted(offenders.items())
    )


# ── the retention enum is a per-type declaration, not a band of the number ───


#: The `water_retention` values REQ-019 fixes **per substrate type**, quoted from
#: its own type list: `orchid_bark` "hohe Luftdurchlässigkeit, […]
#: `water_retention: low`" and `sphagnum` "Torfmoos für feuchtigkeitsliebende
#: Epiphyten und Karnivoren — `water_retention: high`". The other ten types carry
#: no such statement, and this table deliberately does not invent one for them:
#: `soil` alone spans `medium` and `high` across real products.
_TYPE_DECLARED_RETENTION: dict[str, str] = {
    "orchid_bark": "low",
    "sphagnum": "high",
}

#: REQ-019's quantitative ranges for ``water_holding_capacity_percent``: "low
#: <30%, medium 30–60%, high >60%". Present here only so the test below can
#: *state* the disagreement it permits; nothing derives an enum from them.
#:
#: Note which edge is open: ``medium`` is written as a closed 30–60 interval, so
#: 60 is medium and only >60 is high. A first draft of this helper reused one
#: exclusive comparison for both bounds and made 60 ``high``; the boundary test
#: below caught it, which is why that test exists next to the rule.
_WHC_LOW_CEILING = 30.0
_WHC_MEDIUM_CEILING = 60.0


def _whc_band(whc: float) -> str:
    if whc < _WHC_LOW_CEILING:
        return "low"
    if whc <= _WHC_MEDIUM_CEILING:
        return "medium"
    return "high"


def test_the_whc_bands_are_read_the_way_req_019_writes_them() -> None:
    """Boundaries first, so the mapping below is a decision and not an accident.

    REQ-019: "low <30%, medium 30–60%, high >60%". 30 and 60 are therefore the
    *lower* edges of `medium` and `high`; a reading that put 30 in `low` would
    move `Lechuza PON` across a band and change what the next test reports.
    """
    assert _whc_band(29.9) == "low"
    assert _whc_band(30.0) == "medium"
    assert _whc_band(60.0) == "medium"
    assert _whc_band(60.1) == "high"


def test_every_type_req_019_declares_a_retention_for_carries_that_value() -> None:
    """The enum's authority is the **type**, never the record's WHC number (#1175).

    This is the boundary the enum definition was missing. `water_retention` had no
    documented rule at all — the schema listed three strings — while REQ-019 spells
    quantitative bands next to `water_holding_capacity_percent` one line below it,
    which reads like a derivation rule and is not one.

    It bites here because #1175 sources `Sphagnum-Moos (getrocknet)` at WHC 28 %,
    which falls in the `low` band while the record declares `high`. Correcting the
    *enum* to match was the obvious move and is the wrong one, for two measured
    reasons:

    1. **The rule is not the catalogue's.** Applying the bands as a derivation
       makes 10 of the 27 records carrying both fields inconsistent, in both
       directions — `Steinwollmatte` holds 80 % and declares `medium`, and six
       peat-based soils at 55–58 % declare `high`. A rule that ten records break
       is a rule the data was never built on.
    2. **It would change a watering recommendation.** Since #1368
       `_apply_retention_modifier` consults this enum and nothing else; `high` is
       ``*0.80`` and `low` is ``*1.25``, so flipping sphagnum would multiply every
       per-event volume for that medium by 1.56 — the user-visible regression
       #1368's engine fix exists to prevent, arriving through the data instead.

    The number and the enum answer different questions: 28 vol-% is water held at
    pF 1 (EN 13041), the same moss reads 85 vol-% after saturation and free
    drainage (Müller & Glatzel 2021), and neither figure carries its method into
    the field. The enum does not have that ambiguity because it is a type
    statement. So the type declarations are what is pinned.
    """
    offenders = {
        _label(e): f"type={e.get('type')} declares {e.get('water_retention')!r}, "
        f"REQ-019 fixes {_TYPE_DECLARED_RETENTION[str(e.get('type'))]!r}"
        for e in _substrates()
        if str(e.get("type")) in _TYPE_DECLARED_RETENTION
        and e.get("water_retention") != _TYPE_DECLARED_RETENTION[str(e.get("type"))]
    }

    assert not offenders, "water_retention contradicts the type REQ-019 declares it for: " + "; ".join(
        f"{n} ({d})" for n, d in sorted(offenders.items())
    )


def test_a_retention_enum_is_allowed_to_disagree_with_its_own_whc_band() -> None:
    """Pins the disagreement as **legal**, which is the other half of the rule.

    Without this the next reader finds sphagnum at `high`/28 %, reads REQ-019's
    bands as a derivation rule and "repairs" the catalogue — silently rescaling
    the watering volume of every record it touches. Asserting that such records
    exist, and naming how many, makes that edit fail loudly instead.

    The count is deliberately a floor rather than an exact number: a new sourced
    value may legitimately add a disagreement, and pinning equality would turn
    this into a change detector. What must not happen is the set collapsing to
    empty, because only a mass rewrite of the enums gets it there.
    """
    disagreeing = {
        _label(e): f"{e.get('water_retention')} vs whc {e.get('water_holding_capacity_percent')} "
        f"({_whc_band(float(e['water_holding_capacity_percent']))})"
        for e in _substrates()
        if e.get("water_holding_capacity_percent") is not None
        and e.get("water_retention") != _whc_band(float(e["water_holding_capacity_percent"]))
    }

    assert "Sphagnum" in " ".join(disagreeing), (
        "the sourced sphagnum record no longer disagrees with its WHC band. Either the "
        "sourced 28 % was changed, or the enum was aligned to it — the second is the "
        f"regression this test exists for (#1175, #1368). Disagreeing now: {sorted(disagreeing)}"
    )
    assert len(disagreeing) >= 5, (
        "the enum/WHC disagreements have been mass-corrected. REQ-019's bands describe "
        "water_holding_capacity_percent, not water_retention, and the enum is the only "
        f"signal the watering modifier reads (#1368). Disagreeing now: {sorted(disagreeing)}"
    )


# ── the seed header may only name real readers of a field (#1175) ────────────


#: Delimiters of the ``ph_base`` convention block in the seed file's header. The
#: guard below is scoped to it rather than to the whole header, because the block
#: is the part that argues *from* the code: it justifies the water-extract
#: convention by naming who reads the field.
_PH_BLOCK_START = "# pH CONVENTION"
_PH_BLOCK_END = "substrates:"

#: Backticked tokens that are field names, not code locations. They are what the
#: block is *about*, so they are named constantly and resolve to nothing.
_NOT_A_CODE_LOCATION = frozenset({"ph_base", "ph_history", "ec_base_ms"})

_BACKTICKED = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")


def _ph_convention_block() -> str:
    raw = (Path(app.__file__).parent / "migrations" / "seed_data" / "substrates.yaml").read_text(encoding="utf-8")
    start = raw.index(_PH_BLOCK_START)
    end = raw.index(_PH_BLOCK_END, start)
    return raw[start:end]


def _app_sources() -> list[Path]:
    return sorted(Path(app.__file__).parent.rglob("*.py"))


def _resolve(token: str) -> list[Path]:
    """Return the source files that define ``token`` as a module, class or function.

    A token that resolves nowhere is not checked — the block is prose and mentions
    plenty of things that are not code. What must not happen is a token that *does*
    name a place in the codebase while that place never touches the field.
    """
    definition = re.compile(rf"^\s*(?:def|class)\s+{re.escape(token)}\b", re.MULTILINE)
    return [
        path for path in _app_sources() if path.stem == token or definition.search(path.read_text(encoding="utf-8"))
    ]


def test_the_resolver_finds_a_real_reader_and_rejects_a_non_reader() -> None:
    """Boundary first: the guard is only worth anything if resolution actually works.

    ``SubstrateLifecycleManager`` is the counterexample on purpose. The seed header
    named it as a reader of ``ph_base`` and it is not one — ``check_reusability``
    reads ``batch.ph_history`` (the stdev of a grower's own readings) and
    ``substrate.ec_base_ms``, never ``ph_base``. That is the measurement that
    falsified the sentence, and it is pinned here so the guard below cannot quietly
    become one that resolves nothing and passes on everything.
    """
    reader = _resolve("calculate_mix_properties")
    assert reader, "calculate_mix_properties no longer resolves — the guard below would be vacuous"
    assert any("ph_base" in p.read_text(encoding="utf-8") for p in reader)

    non_reader = _resolve("SubstrateLifecycleManager")
    assert non_reader, "SubstrateLifecycleManager no longer resolves"
    assert not any("ph_base" in p.read_text(encoding="utf-8") for p in non_reader), (
        "SubstrateLifecycleManager now reads ph_base. The seed header's argument was rewritten "
        "under #1175 on the measurement that it does not; re-check the header."
    )


def test_every_code_location_the_ph_block_names_reads_ph_base() -> None:
    """The header argues the pH convention *from* its readers, so the list must hold.

    The sentence "every reader of this field puts it in front of a water
    measurement" is the whole justification for storing pH-H₂O rather than the
    CaCl₂ figure German declarations tend to publish — and a reader named there
    that does not read the field makes the argument look stronger than it is while
    being unfalsifiable by reading the file. An earlier draft named
    ``SubstrateLifecycleManager``; nothing caught it, because prose in a YAML
    comment is checked by nobody.
    """
    named = {t for t in _BACKTICKED.findall(_ph_convention_block()) if t not in _NOT_A_CODE_LOCATION}
    liars = {}
    for token in sorted(named):
        paths = _resolve(token)
        if not paths:
            continue
        if not any("ph_base" in path.read_text(encoding="utf-8") for path in paths):
            liars[token] = ", ".join(str(p.relative_to(Path(app.__file__).parent.parent)) for p in paths)

    assert not liars, (
        "the pH-convention block in substrates.yaml names these as readers of ph_base, and they do not "
        "read it: " + "; ".join(f"{n} ({where})" for n, where in sorted(liars.items()))
    )
