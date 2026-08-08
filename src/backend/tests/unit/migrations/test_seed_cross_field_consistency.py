"""Cross-field invariants on the merged seed species corpus.

The 17 seed schemas contain **zero** cross-field rules — no ``if``/``then``, no
``dependentRequired``, no ``allOf`` constraint (audit 2026-08-08 §3 finding 8).
Every seed defect in that cluster is therefore a relationship *between* fields
that JSON Schema, as the schemas are written, cannot express. This module carries
the ones that are checkable as data invariants, in pytest rather than in schema,
because a data invariant needs an allowlist with an obsolescence check and JSON
Schema has nowhere to put one.

What a "species record" is here
===============================

A consumer never sees one YAML record; it sees the merge the seeders produce:
base records (``species.yaml:species[]``, ``plant_info*.yaml:new_species[]``,
``adventskalender.yaml:new_species[]``) plus **fill-if-empty** enrichment
(``<file>:species_enrichment[<name>]`` — ``seed_plant_info.py`` §S3 applies a
value only where the stored one is ``None``/``""``/``[]``). Checking per file
would be a check that looks stricter than it is: *Allium porrum*'s growing
periods live in ``adventskalender.yaml`` while its flat month lists live in
``plant_info_outdoor_1.yaml``, and neither file is wrong read alone.

Invariant C — an omitted ``toxicity`` is not a safety clearance (#1005)
=======================================================================

``get_species_info`` omits unpopulated fields entirely, so a consumer cannot tell
"no toxicity data" from "not toxic". The absence reads as a clearance nobody gave
— and the reported species (*Dracaena reflexa*, a foliage houseplant) is listed
by the ASPCA as toxic to cats and dogs. The `# MISSING` comment convention and
the ``check-seed-data`` gotchas had this polarity backwards: a missing safety
field was a hint, not a blocker (finding 10).

Scope is where absence is *dangerous*: a plant kept in the living space (pets and
children reach it) or one that is eaten. Ornamental outdoor species that are
neither are out of scope — the rule is deliberately not "every species", because
a rule that fires on the whole corpus is a rule everyone learns to ignore.

The debt is a register, not a waiver
------------------------------------

176 of the 186 in-scope species carry no ``toxicity`` today. That is real,
pre-existing debt this change cannot research away, and PR #1034 holds several of
these files open. :data:`TOXICITY_UNRESEARCHED` names every one of them, so:

* a **new** species entering the corpus in scope must carry an explicit toxicity
  fact or be added to the register by hand — the default is now closed, which is
  the whole point of #1005;
* a species that *gains* toxicity data and stays on the register makes
  :func:`test_toxicity_register_has_no_obsolete_entries` fail, so the register
  shrinks with the debt and cannot outlive it.

Read the size of the register, not the colour of the run.

Invariants A and B — deliberately not implemented here (named omission)
=======================================================================

The brief for this module also listed ``allows_harvest: true`` ⇒ harvest data
(#1002) and top-level months ⇒ union of ``growing_periods`` (#1008). Both are
already implemented, red-first, by ``scripts/check_seed_harvest_integrity.py`` in
**PR #1034**, wired into pre-commit and ``backend.yml``, and that implementation
evaluates the *effective* ``allows_harvest`` (the model defaults it to ``True``,
so 44 of the 45 offending records carry no key at all) — a per-file, literal
reading here would have found one of them and reported green over the rest.

Re-implementing them would be a second source of truth for one rule, which is the
duplication class the same audit catalogues (M5), and its allowlist would consist
entirely of records #1034 fixes: it would go fully obsolete on that merge and turn
this suite red for a reason unrelated to any change.

:func:`test_harvest_and_month_invariants_are_enforced_by_the_dedicated_guard`
holds the omission open instead of assuming it: it **runs** that guard once the
script exists and skips, visibly, while it does not. Skipped is not passed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

import app.migrations

_SEED = Path(app.migrations.__file__).parent / "seed_data"
_REPO_ROOT = Path(app.migrations.__file__).resolve().parents[4]

#: Values the seeders treat as "no value recorded" when applying enrichment.
_EMPTY: tuple[Any, ...] = (None, "", [], {})

#: ``plant_category`` values that put a plant in the living space, where a pet or a
#: child can reach it. ``outdoor_ornamental`` is deliberately absent: it is neither
#: eaten nor kept indoors, so an absent toxicity fact there is a gap, not a hazard.
_LIVING_SPACE_CATEGORIES = frozenset(
    {"indoor_houseplant", "tropical_foliage", "succulent_cactus", "orchid", "balcony_plant"}
)

#: ``plant_category`` values that imply the plant is eaten.
_EDIBLE_CATEGORIES = frozenset({"outdoor_vegetable", "herb", "bulb_tuber"})

#: Species in scope of invariant C that carry no toxicity fact yet (#1005).
#:
#: One shared reason, because it is one debt: the corpus was authored before an
#: absent safety field counted as an error. Each name is listed so the register can
#: only shrink deliberately — adding to it is a visible edit, and an entry that no
#: longer violates fails the obsolescence test.
#:
#: Measured 2026-08-08 across species.yaml + plant_info*.yaml + adventskalender.yaml.
#: Several of these files are held open by PR #1034 (harvest/month correction), so
#: the values are not researched here.
TOXICITY_UNRESEARCHED: frozenset[str] = frozenset(
    {
        "Adiantum raddianum",
        "Aechmea fasciata",
        "Aeschynanthus radicans",
        "Aglaonema commutatum",
        "Allium porrum",
        "Allium schoenoprasum",
        "Alocasia x amazonica",
        "Aloe vera",
        "Anethum graveolens",
        "Anthurium andraeanum",
        "Aphelandra squarrosa",
        "Apium graveolens",
        "Apium graveolens var. rapaceum",
        "Ardisia crenata",
        "Artemisia dracunculus",
        "Asparagus setaceus",
        "Aspidistra elatior",
        "Asplenium nidus",
        "Avena sativa",
        "Beaucarnea recurvata",
        "Begonia rex-cultorum",
        "Begonia semperflorens",
        "Beta vulgaris subsp. vulgaris",
        "Brassica oleracea var. botrytis",
        "Brassica oleracea var. capitata",
        "Brassica oleracea var. gemmifera",
        "Brassica oleracea var. gongylodes",
        "Brassica oleracea var. italica",
        "Cannabis sativa",
        "Capsicum annuum",
        "Cattleya hybrida",
        "Ceropegia woodii",
        "Chamaedorea elegans",
        "Chlorophytum comosum",
        "Cichorium intybus",
        "Citrullus lanatus",
        "Clivia miniata",
        "Codiaeum variegatum",
        "Coffea arabica",
        "Coriandrum sativum",
        "Crassula ovata",
        "Ctenanthe burle-marxii",
        "Cucumis melo",
        "Cucumis sativus",
        "Cucurbita maxima",
        "Cucurbita pepo",
        "Curio rowleyanus",
        "Cyclamen persicum",
        "Dahlia pinnata",
        "Daucus carota",
        "Dendrobium nobile",
        "Dieffenbachia seguine",
        "Dracaena angolensis",
        "Dracaena fragrans",
        "Dracaena marginata",
        "Dracaena trifasciata",
        "Dypsis lutescens",
        "Echeveria elegans",
        "Epipremnum aureum",
        "Eruca vesicaria",
        "Euphorbia pulcherrima",
        "Fatsia japonica",
        "Ficus benjamina",
        "Ficus elastica",
        "Ficus lyrata",
        "Fittonia albivenis",
        "Foeniculum vulgare",
        "Fragaria x ananassa",
        "Gardenia jasminoides",
        "Glycine max",
        "Goeppertia lancifolia",
        "Goeppertia makoyana",
        "Goeppertia orbifolia",
        "Guzmania lingulata",
        "Gymnocalycium mihanovichii",
        "Haworthiopsis fasciata",
        "Hedera helix",
        "Helianthus annuus",
        "Hibiscus rosa-sinensis",
        "Hippeastrum hybridum",
        "Hordeum vulgare",
        "Howea forsteriana",
        "Hoya carnosa",
        "Humulus lupulus",
        "Impatiens walleriana",
        "Jasminum polyanthum",
        "Kalanchoe blossfeldiana",
        "Kalanchoe daigremontiana",
        "Lactuca sativa",
        "Lavandula angustifolia",
        "Lens culinaris",
        "Levisticum officinale",
        "Lithops spp.",
        "Livistona chinensis",
        "Luffa aegyptiaca",
        "Lupinus polyphyllus",
        "Malus domestica",
        "Mammillaria spp.",
        "Maranta leuconeura",
        "Matricaria chamomilla",
        "Medicago sativa",
        "Melissa officinalis",
        "Mentha piperita",
        "Monstera adansonii",
        "Monstera deliciosa",
        "Neoregelia carolinae",
        "Nephrolepis exaltata",
        "Nymphaea alba",
        "Ocimum basilicum",
        "Opuntia microdasys",
        "Origanum vulgare",
        "Oryza sativa",
        "Oxalis triangularis",
        "Pachira aquatica",
        "Pastinaca sativa",
        "Pelargonium zonale",
        "Peperomia obtusifolia",
        "Petroselinum crispum",
        "Petunia x hybrida",
        "Phacelia tanacetifolia",
        "Phalaenopsis hybrida",
        "Phaseolus vulgaris",
        "Philodendron hederaceum",
        "Physalis peruviana",
        "Pilea peperomioides",
        "Pisum sativum",
        "Platycerium bifurcatum",
        "Plectranthus verticillatus",
        "Prunus avium",
        "Prunus domestica",
        "Pyrus communis",
        "Raphanus sativus",
        "Rheum rhabarbarum",
        "Rhipsalis baccifera",
        "Rhododendron simsii",
        "Ribes rubrum",
        "Ribes uva-crispa",
        "Rubus fruticosus agg.",
        "Rubus idaeus",
        "Salvia officinalis",
        "Salvia rosmarinus",
        "Sambucus nigra",
        "Satureja hortensis",
        "Schefflera arboricola",
        "Schlumbergera truncata",
        "Sedum morganianum",
        "Sinapis alba",
        "Solanum lycopersicum",
        "Solanum melongena",
        "Solanum tuberosum",
        "Soleirolia soleirolii",
        "Sorghum bicolor",
        "Spathiphyllum wallisii",
        "Spinacia oleracea",
        "Stephanotis floribunda",
        "Strelitzia reginae",
        "Streptocarpus hybridus",
        "Stromanthe sanguinea",
        "Tagetes patula",
        "Thymus vulgaris",
        "Tigridia pavonia",
        "Tillandsia usneoides",
        "Tradescantia zebrina",
        "Trifolium pratense",
        "Triticum aestivum",
        "Tropaeolum majus",
        "Vaccinium corymbosum",
        "Verbena x hybrida",
        "Vicia faba",
        "Viola x wittrockiana",
        "Vitis vinifera",
        "Vriesea splendens",
        "Yucca elephantipes",
        "Zamioculcas zamiifolia",
        "Zantedeschia aethiopica",
        "Zea mays",
    }
)


# --------------------------------------------------------------------------- #
# Corpus assembly
# --------------------------------------------------------------------------- #


def _seed_files() -> list[Path]:
    """Return the species-carrying seed files in seeding order."""
    return [_SEED / "species.yaml", *sorted(_SEED.glob("plant_info*.yaml")), _SEED / "adventskalender.yaml"]


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def merged_species() -> dict[str, dict[str, Any]]:
    """Return ``{scientific_name: fields}`` as the seeders assemble it.

    Base records first (in seeding order), then fill-if-empty enrichment — the same
    rule ``seed_plant_info.py`` §S3 applies, so a field contributed by one file and
    a field contributed by another end up on the record a consumer reads.
    """
    merged: dict[str, dict[str, Any]] = {}

    def absorb(name: str, values: dict[str, Any]) -> None:
        target = merged.setdefault(name, {})
        for key, value in values.items():
            if key not in target or target[key] in _EMPTY:
                target[key] = value

    files = _seed_files()
    for path in files:
        document = _load(path)
        for section in ("species", "new_species"):
            for entry in document.get(section) or []:
                if isinstance(entry, dict) and entry.get("scientific_name"):
                    absorb(str(entry["scientific_name"]), entry)
    for path in files:
        document = _load(path)
        for name, entry in (document.get("species_enrichment") or {}).items():
            if isinstance(entry, dict):
                absorb(str(name), entry)

    return merged


def _is_in_living_space_or_eaten(fields: dict[str, Any]) -> bool:
    """Return whether an absent toxicity fact is *dangerous* for this species."""
    category = fields.get("plant_category")
    return bool(
        category in _LIVING_SPACE_CATEGORIES
        or fields.get("indoor_suitable") in ("yes", "limited")
        or category in _EDIBLE_CATEGORIES
        or fields.get("harvested_part")
        or fields.get("allows_harvest") is True
    )


def _has_explicit_toxicity(fields: dict[str, Any]) -> bool:
    """Return whether the record states a toxicity fact rather than omitting one.

    ``is_toxic_cats: false`` and ``severity: none`` count — they are *negations*, and
    the point of #1005 is that a negation and an omission must not look alike. An
    empty or all-null block does not count: it says nothing.
    """
    toxicity = fields.get("toxicity")
    if not isinstance(toxicity, dict):
        return False
    return any(value is not None for value in toxicity.values())


# --------------------------------------------------------------------------- #
# Invariant C — toxicity is stated, never omitted, where absence is dangerous
# --------------------------------------------------------------------------- #


def test_corpus_is_assembled_as_a_consumer_sees_it() -> None:
    """Guard the merge itself — a broken merge would silently empty every check below."""
    merged = merged_species()
    assert len(merged) >= 200, f"expected the full species corpus, assembled only {len(merged)}"

    porrum = merged.get("Allium porrum")
    assert porrum is not None
    # Cross-file evidence: the growing periods come from adventskalender.yaml and the
    # bloom months from a plant_info file. A per-file reading sees neither together.
    assert len(porrum.get("growing_periods") or []) == 2, (
        "Allium porrum's two cultivation windows are not on the merged record — the "
        "merge no longer reproduces what a consumer reads"
    )


def test_species_in_the_living_space_or_on_the_plate_state_a_toxicity_fact() -> None:
    merged = merged_species()
    offenders = sorted(
        name
        for name, fields in merged.items()
        if _is_in_living_space_or_eaten(fields)
        and not _has_explicit_toxicity(fields)
        and name not in TOXICITY_UNRESEARCHED
    )
    assert not offenders, (
        "Species are kept in the living space or eaten but state no toxicity fact "
        "(#1005: an omitted field reads as a safety clearance nobody gave). Populate "
        "`toxicity` — an explicit negation such as `severity: none` / `is_toxic_cats: "
        "false` is a valid answer — or add the species to TOXICITY_UNRESEARCHED with "
        "the debt it inherits:\n" + "\n".join(offenders)
    )


def test_toxicity_register_has_no_obsolete_entries() -> None:
    """The register must shrink with the debt, not outlive it."""
    merged = merged_species()
    resolved = sorted(name for name in TOXICITY_UNRESEARCHED if name in merged and _has_explicit_toxicity(merged[name]))
    unknown = sorted(name for name in TOXICITY_UNRESEARCHED if name not in merged)
    out_of_scope = sorted(
        name for name in TOXICITY_UNRESEARCHED if name in merged and not _is_in_living_space_or_eaten(merged[name])
    )

    assert not resolved, (
        "TOXICITY_UNRESEARCHED names species that now carry a toxicity fact — remove "
        "them, the register may not outlive the debt:\n" + "\n".join(resolved)
    )
    assert not unknown, (
        "TOXICITY_UNRESEARCHED names species that are not in the seed corpus (renamed "
        "or removed):\n" + "\n".join(unknown)
    )
    assert not out_of_scope, (
        "TOXICITY_UNRESEARCHED names species that are no longer in scope of the rule — "
        "remove them so the register measures the debt it claims to:\n" + "\n".join(out_of_scope)
    )


def test_the_toxicity_rule_fires_on_a_species_that_omits_the_field() -> None:
    """Negative control: the invariant must be able to fail.

    A rule evaluated only against a corpus that is fully allowlisted proves nothing
    about the rule. This feeds it the exact #1005 shape — a foliage houseplant with
    no toxicity block — and asserts the two predicates that decide the case.
    """
    dracaena_reflexa = {
        "scientific_name": "Dracaena reflexa",
        "plant_category": "tropical_foliage",
        "indoor_suitable": "yes",
        "allows_harvest": True,
    }
    assert _is_in_living_space_or_eaten(dracaena_reflexa)
    assert not _has_explicit_toxicity(dracaena_reflexa)
    assert not _has_explicit_toxicity({**dracaena_reflexa, "toxicity": {}})
    assert not _has_explicit_toxicity({**dracaena_reflexa, "toxicity": {"severity": None}})
    # An explicit negation is an answer, and must clear the rule.
    assert _has_explicit_toxicity({**dracaena_reflexa, "toxicity": {"severity": "none"}})
    assert _has_explicit_toxicity({**dracaena_reflexa, "toxicity": {"is_toxic_cats": False}})
    # An outdoor ornamental is out of scope — the rule is bounded, not universal.
    assert not _is_in_living_space_or_eaten(
        {"plant_category": "outdoor_ornamental", "indoor_suitable": "no", "allows_harvest": False}
    )


# --------------------------------------------------------------------------- #
# Invariants A + B — enforced elsewhere, verified rather than assumed
# --------------------------------------------------------------------------- #

_HARVEST_GUARD = _REPO_ROOT / "scripts" / "check_seed_harvest_integrity.py"


def test_harvest_and_month_invariants_are_enforced_by_the_dedicated_guard() -> None:
    """Run #1034's guard if it is on the tree; skip, visibly, while it is not.

    ``allows_harvest: true`` ⇒ harvest data (#1002) and top-level months ⇒ union of
    the growing periods (#1008) are owned by ``scripts/check_seed_harvest_integrity.py``,
    not duplicated here. This test makes the delegation falsifiable: the moment that
    script lands, the invariants are checked from this suite too, against the one
    implementation — no second source of truth, and no claim that something is
    covered when it is not.
    """
    if not _HARVEST_GUARD.exists():
        pytest.skip(
            "scripts/check_seed_harvest_integrity.py is not on this tree yet (PR #1034). "
            "Invariants A (#1002) and B (#1008) are deliberately not duplicated here; "
            "this test starts enforcing them automatically once that guard merges."
        )

    spec = importlib.util.spec_from_file_location("_seed_harvest_integrity_guard", _HARVEST_GUARD)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # Driven through the guard's CLI entry point rather than its internals: that is
    # the surface pre-commit and backend.yml use, so this cannot pass while the wired
    # invocation fails. It prints its own findings, which pytest surfaces on failure.
    exit_code = module.main([])
    assert exit_code == 0, "scripts/check_seed_harvest_integrity.py reports violations (see captured output above)"
