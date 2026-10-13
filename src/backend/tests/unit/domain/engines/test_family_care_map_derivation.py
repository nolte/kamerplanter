"""FAMILY_CARE_MAP is what its stated derivation rule produces (#1505, review SCR-003).

The map's 64 entries are documented as "rule 1: the majority ``Pflege-Stil`` of the
family's Steckbriefe; rule 2: where that majority is absent, the style that fits the
seeded species; rule 3: never ``custom``". Until this module existed, that was a
claim about a hand-written table — nothing recomputed it, so a transcription slip or
a later Steckbrief edit could not be noticed. Two such slips were in the first draft
and are fixed in the map's comments: ``Bromeliaceae`` was labelled rule 2 while rule
1 does produce a majority (``tropical`` 3/5), and ``Asparagaceae``'s count listed 6
of its 11 votes.

What rule 1 means here, precisely
=================================

Per family, over the Steckbriefe that declare a style, **deduplicated by scientific
name** (``Dracaena marginata`` has two documents), rule 1 fires when one value holds
a **strict majority** of all votes — more than half, ``custom`` and non-``CareStyleType``
values (two documents say ``temperate``) included in the denominator — and that
value is a ``CareStyleType`` other than ``custom``. Anything else is a rule-2
judgement and must appear in :data:`_DEVIATIONS` with its reason.

The allowlist is checked in **both** directions: a family in it that rule 1 actually
agrees with fails too, so the list cannot quietly accumulate entries that have
stopped being exceptions.
"""

from __future__ import annotations

import collections
import re
from pathlib import Path

import pytest

from app.common.enums import CareStyleType
from app.domain.engines.care_reminder_engine import FAMILY_CARE_MAP

_PLANT_DOCS = Path(__file__).resolve().parents[6] / "spec" / "knowledge" / "plants"

_FAMILY_ROW = re.compile(r"^\|\s*Familie\s*\|\s*([A-Za-z]+)", re.M)
_STYLE_ROW = re.compile(r"^\|\s*Pflege-Stil\s*\|\s*`?([a-z_]+)`?", re.M)
_NAME_ROW = re.compile(r"^\|\s*Wissenschaftlicher Name\s*\|\s*([^|(]+?)\s*[|(]", re.M)

#: Families whose entry is a rule-2 judgement rather than the rule-1 majority, with
#: the reason. Entries marked "pre-existing" predate #1505 and were deliberately
#: left alone: changing them rewrites stored profiles on a decision this issue does
#: not make.
_DEVIATIONS: dict[str, str] = {
    # ── rule 1 produces a majority, and the map deviates from it ──
    "Bromeliaceae": (
        "majority `tropical` 3/5, but no houseplant preset waters a leaf funnel or "
        "feeds an extreme light feeder as sparingly as the family record demands — "
        "hence the BROMELIAD preset"
    ),
    "Cannabaceae": (
        "the only doc with a style is humulus_lupulus.md (`mediterranean`); the family "
        "record says `typical_nutrient_demand: heavy` and the second seeded species is "
        "indoor Cannabis sativa, both of which a 30-day feeding interval contradicts"
    ),
    "Iridaceae": (
        "tigridia_pavonia.md says `mediterranean`; the seeds say `bulb_tuber`, "
        "frost-sensitive geophyte — the definition of FROST_TENDER_TUBER"
    ),
    "Strelitziaceae": (
        "strelitzia_reginae.md says `mediterranean`; the seeds say tropical_foliage, indoor_suitable, frost-sensitive"
    ),
    "Verbenaceae": (
        "the doc says `mediterranean`; Verbena x hybrida is a frost-tender balcony "
        "bedder, the use case OUTDOOR_ANNUAL_ORNAMENTAL was written for"
    ),
    "Vitaceae": (
        "the doc says `mediterranean`, whose 36-month repotting interval would put a "
        "repotting reminder on a grapevine in the ground; FRUIT_TREE caps it at 60"
    ),
    "Balsaminaceae": "pre-existing (REQ-022 v2.5 ornamentals); Impatiens is a balcony annual",
    "Geraniaceae": "pre-existing (REQ-022 v2.5 ornamentals); Pelargonium is an annual balcony bedder",
    "Lamiaceae": (
        "pre-existing and contested: 8 of 10 docs say `mediterranean`. Changing it "
        "rewrites stored profiles, so #1505 left it — follow-up with an agrobiology review"
    ),
    # ── rule 1 produces no majority; the entry is a rule-2 judgement ──
    "Amaranthaceae": "no majority (custom 1 / outdoor_annual_veg 1); both species are outdoor vegetables",
    "Amaryllidaceae": (
        "no majority; 4 of the 6 seeded species are kitchen Alliums, the two indoor bulbs (Clivia, Hippeastrum) deviate"
    ),
    "Asparagaceae": (
        "no majority: succulent 4, tropical 3, and custom / fern / cactus / temperate "
        "once each — 4 of 11 votes. The family record itself warns it is heterogeneous. "
        "SUCCULENT is the safer default because these store water and rot on a 7-day "
        "rhythm; the price is that Hosta and Asparagus officinalis, both outdoor "
        "perennials, get a 14-day drench-and-drain default until a species guide or a "
        "user profile overrides it"
    ),
    "Asphodelaceae": "pre-existing; a three-way tie (cactus / succulent / mediterranean)",
    "Asteraceae": (
        "no majority (outdoor_annual_veg 4 of 13); counting the two `custom` vegetables "
        "the kitchen-garden reading is the plurality. The price is that Tagetes and "
        "Dahlia lose the deadheading reminder"
    ),
    "Begoniaceae": "tie calathea / tropical; the generic style wins",
    "Cucurbitaceae": "tie herb_tropical / outdoor_annual_veg; all six seeded species are outdoor vegetables",
    "Ericaceae": (
        "all three docs say `custom` (rule 3). Vaccinium is a berry shrub and the "
        "preset's numbers fit the ericaceous acid-soil, low-feed regime"
    ),
    "Grossulariaceae": "both docs say `custom` (rule 3); the BERRY_SHRUB comment names currant and gooseberry",
    "Hydrangeaceae": (
        "the only doc says `temperate`, which is not a CareStyleType (hosta_spp.md is the "
        "second such document); a hardy shrub with a high water demand"
    ),
    "Nymphaeaceae": "the doc says `custom` and states outright that no standard preset fits an aquatic plant",
    "Polygonaceae": "the only doc says `custom` (rule 3); rhubarb is a hardy perennial vegetable",
    "Primulaceae": (
        "pre-existing and contested: the two seeded species are indoor pot plants "
        "(Ardisia, Cyclamen persicum). Out of #1505's scope — follow-up"
    ),
    "Ranunculaceae": (
        "no majority; `mediterranean` 2 of 4, but all four are hardy outdoor perennials "
        "and Clematis and Delphinium are thirsty"
    ),
    "Rosaceae": (
        "the majority is `custom` (rule 3); 4 of the 8 seeded species are the fruit "
        "trees FRUIT_TREE names. Rosa and Rubus deserve their own styles, which a "
        "family map cannot give them"
    ),
    "Rubiaceae": "tie tropical / calathea (Coffea, Gardenia); both are warm indoor plants",
    "Urticaceae": "tie tropical / fern (Pilea, Soleirolia); both are warm indoor foliage",
    "Violaceae": "pre-existing (REQ-022 v2.5 ornamentals); the Viola doc carries no style row",
}


def _votes() -> dict[str, dict[str, str]]:
    """``family -> {scientific name: declared style}`` from the Steckbriefe."""
    collected: dict[str, dict[str, str]] = collections.defaultdict(dict)
    for document in sorted(_PLANT_DOCS.glob("*.md")):
        text = document.read_text(encoding="utf-8")
        family = _FAMILY_ROW.search(text)
        style = _STYLE_ROW.search(text)
        if family is None or style is None:
            continue
        name = _NAME_ROW.search(text)
        collected[family.group(1)][name.group(1).strip() if name else document.name] = style.group(1)
    return dict(collected)


def _rule_one_majority(styles: dict[str, str]) -> str | None:
    """The strict majority style, or ``None`` when rule 1 does not decide."""
    tally = collections.Counter(styles.values())
    total = sum(tally.values())
    top, count = tally.most_common(1)[0]
    if sum(1 for value in tally.values() if value == count) > 1:
        return None
    if count * 2 <= total:
        return None
    if top == CareStyleType.CUSTOM.value or top not in {member.value for member in CareStyleType}:
        return None
    return top


@pytest.fixture(scope="module")
def votes() -> dict[str, dict[str, str]]:
    return _votes()


def test_the_steckbrief_corpus_is_read_at_all(votes: dict[str, dict[str, str]]) -> None:
    """A derivation check over an empty corpus would be green for the wrong reason."""
    assert len(votes) >= 55, f"only {len(votes)} families parsed from {_PLANT_DOCS}"
    assert sum(len(styles) for styles in votes.values()) >= 190
    assert votes["Solanaceae"]["Solanum lycopersicum"] == "outdoor_annual_veg"


def test_every_rule_one_majority_is_what_the_map_holds(votes: dict[str, dict[str, str]]) -> None:
    mismatches: list[str] = []
    for family, styles in sorted(votes.items()):
        majority = _rule_one_majority(styles)
        if majority is None or family in _DEVIATIONS:
            continue
        mapped = FAMILY_CARE_MAP.get(family)
        if mapped is None or mapped.value != majority:
            mismatches.append(f"{family}: docs say {majority!r}, map says {mapped and mapped.value!r}")
    assert not mismatches, (
        "FAMILY_CARE_MAP contradicts the majority of its families' Steckbriefe without "
        f"a recorded reason: {mismatches}. Either follow rule 1 or record the deviation "
        "in _DEVIATIONS with its measurement."
    )


def test_every_family_without_a_majority_records_its_reason(votes: dict[str, dict[str, str]]) -> None:
    undocumented = sorted(
        family
        for family, styles in votes.items()
        if family in FAMILY_CARE_MAP and _rule_one_majority(styles) is None and family not in _DEVIATIONS
    )
    assert not undocumented, (
        "the Steckbriefe give no majority for these families, so their entry is a "
        f"judgement — record it in _DEVIATIONS with the count it is based on: {undocumented}"
    )


def test_no_deviation_entry_has_become_unnecessary(votes: dict[str, dict[str, str]]) -> None:
    """An allowlist that outlives its exception is a licence, not a record."""
    stale = sorted(
        family
        for family, reason in _DEVIATIONS.items()
        if family in votes
        and (majority := _rule_one_majority(votes[family])) is not None
        and FAMILY_CARE_MAP.get(family) is not None
        and FAMILY_CARE_MAP[family].value == majority
    )
    assert not stale, f"_DEVIATIONS names families the Steckbriefe now agree with: {stale}"


def test_no_deviation_entry_names_an_unknown_family(votes: dict[str, dict[str, str]]) -> None:
    unknown = sorted(family for family in _DEVIATIONS if family not in votes)
    assert not unknown, f"_DEVIATIONS names families no Steckbrief mentions: {unknown}"


def test_every_deviation_carries_a_reason() -> None:
    thin = sorted(family for family, reason in _DEVIATIONS.items() if len(reason) < 40)
    assert not thin, f"_DEVIATIONS entries without a real reason: {thin}"


def test_no_family_default_is_custom() -> None:
    """Rule 3 — as a default, CUSTOM is TROPICAL's numbers under an opaque name."""
    custom = sorted(family for family, style in FAMILY_CARE_MAP.items() if style is CareStyleType.CUSTOM)
    assert not custom, f"families defaulting to CUSTOM: {custom}"


def test_the_derivation_check_can_fail(votes: dict[str, dict[str, str]]) -> None:
    """Proof the majority computation bites, on the exact expression the gate uses."""
    assert _rule_one_majority(votes["Solanaceae"]) == "outdoor_annual_veg"
    # A tie decides nothing …
    assert _rule_one_majority({"a": "tropical", "b": "fern"}) is None
    # … nor does a plurality that is not a majority …
    assert _rule_one_majority({"a": "tropical", "b": "tropical", "c": "fern", "d": "cactus"}) is None
    assert _rule_one_majority({"a": "custom", "b": "custom", "c": "fern"}) is None
    assert _rule_one_majority({"a": "temperate", "b": "temperate", "c": "fern"}) is None
