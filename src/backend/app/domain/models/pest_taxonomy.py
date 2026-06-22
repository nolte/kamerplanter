"""REQ-044 WP-4 — finale Klassen-Taxonomie der Schädlingserkennung.

Die Taxonomie ist die **Label-Menge** der Bilderkennung und gleichzeitig die
Quelle für das ``beneficials``-Seed (WP-8) sowie das Mapping eines Findings
gegen die REQ-010-``pests``-Stammdaten (über ``scientific_name``).

GBIF-``taxon_key``s sind in WP-4 live verifiziert (ACCEPTED). Ausnahmen sind im
Readiness-Dokument vermerkt. Die finale trainierte Modellwahl (D-FINE/RF-DETR)
und die Gewichte sind extern blockiert (WP-1/WP-2/WP-3); diese Taxonomie ist
davon unabhängig und sofort nutzbar.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.enums import PestFindingCategory


class PestTaxon(BaseModel):
    """Eine erkennbare Klasse (Schädling, Schadbild-Symptom oder Nützling)."""

    slug: str = Field(min_length=1, max_length=80)
    category: PestFindingCategory
    common_name_de: str
    scientific_name: str
    gbif_taxon_key: str | None = None
    # Optional explicit iNaturalist taxon id. GBIF keys are NOT iNat ids, so the
    # iNaturalist client resolves the id by scientific name at runtime; setting
    # it here pins the mapping and avoids the lookup (more robust for ambiguous
    # family-level names). Left None → resolve-by-name (cached per process).
    inat_taxon_id: int | None = None
    # Optional iNaturalist lifeStage annotation value (e.g. "Larva") used to
    # target larvae instead of adults — critical for the beneficial-larvae gap
    # (ladybird/lacewing/hoverfly). None → no lifeStage filter.
    # See spec/analysis/pest-image-sources-analysis.md §4.1 / §8.
    inat_life_stage: str | None = None
    # Bezug zu pests-Slugs (nur bei category == BENEFICIAL relevant, WP-8).
    preys_on: list[str] = Field(default_factory=list)
    # Kurze Schadbild-Beschreibung (Modus-2-Symptom, WP-4.1).
    symptom_hint_de: str | None = None

    model_config = {"frozen": True}


# WP-4.1 — Schädlinge (category=pest). ``scientific_name`` matcht die
# REQ-010-pests-Stammdaten; ``symptom_hint_de`` deckt den Schadbild-Modus ab.
_PESTS: list[PestTaxon] = [
    PestTaxon(
        slug="spider_mite",
        category=PestFindingCategory.PEST,
        common_name_de="Gemeine Spinnmilbe",
        scientific_name="Tetranychus urticae",
        gbif_taxon_key="2130185",
        symptom_hint_de=("helle Sprenkelung der Blattoberseite, feine Gespinste an der Blattunterseite, Bronzefärbung"),
    ),
    PestTaxon(
        slug="thrips_frankliniella",
        category=PestFindingCategory.PEST,
        common_name_de="Kalifornischer Blütenthrips",
        scientific_name="Frankliniella occidentalis",
        gbif_taxon_key="8351995",
        symptom_hint_de="silbrig-graue Saugflecken, schwarze Kotpünktchen, deformierte Blätter/Blüten",
    ),
    PestTaxon(
        slug="thrips_echinothrips",
        category=PestFindingCategory.PEST,
        common_name_de="Bunter Blütenthrips",
        scientific_name="Echinothrips americanus",
        gbif_taxon_key="1420846",
        symptom_hint_de="silbrig-bronzene Saugflächen auf der Blattoberseite",
    ),
    PestTaxon(
        slug="fungus_gnat",
        category=PestFindingCategory.PEST,
        common_name_de="Trauermücken",
        scientific_name="Sciaridae",
        gbif_taxon_key="3525",
        symptom_hint_de="schwarze Mücken über dem Substrat; weiße Larven im Substrat (Wurzelfraß)",
    ),
    PestTaxon(
        slug="aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Blattläuse",
        scientific_name="Aphididae",
        gbif_taxon_key="3042",
        symptom_hint_de="Honigtau/klebrig, Rußtau, gekräuselte Triebspitzen, Kolonien, Häutungshüllen",
    ),
    PestTaxon(
        slug="mealybug",
        category=PestFindingCategory.PEST,
        common_name_de="Schmier-/Wollläuse",
        scientific_name="Pseudococcidae",
        gbif_taxon_key="4534",
        symptom_hint_de="weiße Watte in Blattachseln, Honigtau und Rußtau",
    ),
    PestTaxon(
        slug="whitefly",
        category=PestFindingCategory.PEST,
        common_name_de="Weiße Fliege",
        scientific_name="Trialeurodes vaporariorum",
        gbif_taxon_key="2012132",
        symptom_hint_de="aufsteigende weiße Fliegen, Larven an der Blattunterseite, Honigtau/Rußtau",
    ),
    # WP-4.1b — erweiterte REQ-010-Katalog-Schädlinge (Outdoor/Garten + weitere
    # Indoor-Arten). GBIF-``taxon_key``s sind live gegen die GBIF-Match-API
    # verifiziert (confidence >= 92, fast alle EXACT). Das Mapping zu den
    # pests-Stammdaten laeuft ueber ``detection_slug`` in ipm.yaml; ``scientific_name``
    # nutzt den sauberen GBIF-Namen (Gattung bei spp.) fuer den iNat-Resolve.
    # Siehe spec/analysis/pest-image-sources-analysis.md.
    PestTaxon(
        slug="cabbage_looper",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlsilbereule",
        scientific_name="Trichoplusia ni",
        gbif_taxon_key="1786360",
    ),
    PestTaxon(
        slug="scale_insect",
        category=PestFindingCategory.PEST,
        common_name_de="Schildläuse",
        scientific_name="Coccoidea",
        gbif_taxon_key="5953662",
    ),
    PestTaxon(
        slug="flea_beetle",
        category=PestFindingCategory.PEST,
        common_name_de="Erdflöhe",
        scientific_name="Phyllotreta",
        gbif_taxon_key="1049215",
    ),
    PestTaxon(
        slug="spanish_slug",
        category=PestFindingCategory.PEST,
        common_name_de="Spanische Wegschnecke",
        scientific_name="Arion vulgaris",
        gbif_taxon_key="7540164",
    ),
    PestTaxon(
        slug="root_knot_nematode",
        category=PestFindingCategory.PEST,
        common_name_de="Wurzelgallenälchen",
        scientific_name="Meloidogyne",
        gbif_taxon_key="9705419",  # microscopic — only damage (root galls) photographable
    ),
    PestTaxon(
        slug="large_cabbage_white",
        category=PestFindingCategory.PEST,
        common_name_de="Großer Kohlweißling",
        scientific_name="Pieris brassicae",
        gbif_taxon_key="1920506",
    ),
    PestTaxon(
        slug="small_cabbage_white",
        category=PestFindingCategory.PEST,
        common_name_de="Kleiner Kohlweißling",
        scientific_name="Pieris rapae",
        gbif_taxon_key="1920496",
    ),
    PestTaxon(
        slug="colorado_potato_beetle",
        category=PestFindingCategory.PEST,
        common_name_de="Kartoffelkäfer",
        scientific_name="Leptinotarsa decemlineata",
        gbif_taxon_key="1047536",
    ),
    PestTaxon(
        slug="codling_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Apfelwickler",
        scientific_name="Cydia pomonella",
        gbif_taxon_key="1737847",
    ),
    PestTaxon(
        slug="leek_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Lauchmotte",
        scientific_name="Acrolepiopsis assectella",
        gbif_taxon_key="4525339",
    ),
    PestTaxon(
        slug="carrot_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Möhrenfliege",
        scientific_name="Psila rosae",
        gbif_taxon_key="5713486",
    ),
    PestTaxon(
        slug="onion_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Zwiebelfliege",
        scientific_name="Delia antiqua",
        gbif_taxon_key="5077646",
    ),
    PestTaxon(
        slug="cabbage_root_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlfliege",
        scientific_name="Delia radicum",
        gbif_taxon_key="5077574",
    ),
    PestTaxon(
        slug="cherry_fruit_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Kirschfruchtfliege",
        scientific_name="Rhagoletis cerasi",
        gbif_taxon_key="1622583",
    ),
    PestTaxon(
        slug="box_tree_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Buchsbaumzünsler",
        scientific_name="Cydalima perspectalis",
        gbif_taxon_key="4532122",
    ),
    PestTaxon(
        slug="strawberry_blossom_weevil",
        category=PestFindingCategory.PEST,
        common_name_de="Erdbeerblütenstecher",
        scientific_name="Anthonomus rubi",
        gbif_taxon_key="1196192",
    ),
    PestTaxon(
        slug="vine_weevil",
        category=PestFindingCategory.PEST,
        common_name_de="Dickmaulrüssler",
        scientific_name="Otiorhynchus sulcatus",
        gbif_taxon_key="1195129",
    ),
    PestTaxon(
        slug="cabbage_whitefly",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlmottenschildlaus",
        scientific_name="Aleyrodes proletella",
        gbif_taxon_key="4484303",
    ),
    PestTaxon(
        slug="wireworm",
        category=PestFindingCategory.PEST,
        common_name_de="Drahtwurm (Larve des Schnellkäfers)",
        scientific_name="Agriotes",
        gbif_taxon_key="1162125",
    ),
    PestTaxon(
        slug="european_corn_borer",
        category=PestFindingCategory.PEST,
        common_name_de="Maiszünsler",
        scientific_name="Ostrinia nubilalis",
        gbif_taxon_key="8223165",
    ),
    PestTaxon(
        slug="green_peach_aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Grüne Pfirsichblattlaus",
        scientific_name="Myzus persicae",
        gbif_taxon_key="2076179",
    ),
    PestTaxon(
        slug="potato_aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Kartoffelblattlaus",
        scientific_name="Macrosiphum euphorbiae",
        gbif_taxon_key="2077747",
    ),
    PestTaxon(
        slug="cabbage_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Kohleule",
        scientific_name="Mamestra brassicae",
        gbif_taxon_key="1788522",
    ),
    PestTaxon(
        slug="diamondback_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlschabe",
        scientific_name="Plutella xylostella",
        gbif_taxon_key="1831136",
    ),
    PestTaxon(
        slug="waterlily_aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Seerosenblattlaus",
        scientific_name="Rhopalosiphum nymphaeae",
        gbif_taxon_key="9565622",
    ),
    PestTaxon(
        slug="waterlily_leaf_beetle",
        category=PestFindingCategory.PEST,
        common_name_de="Seerosenblattkäfer",
        scientific_name="Galerucella nymphaeae",
        gbif_taxon_key="1048344",
    ),
    PestTaxon(
        slug="brown_china_mark",
        category=PestFindingCategory.PEST,
        common_name_de="Seerosenzünsler",
        scientific_name="Elophila nymphaeata",
        gbif_taxon_key="5884851",
    ),
]

# WP-4.2 — Nützlinge (category=beneficial). Werden NIE als Schädling gemeldet
# (§9.1). ``preys_on`` referenziert pest-Slugs für die WP-8-beneficials-Seed.
_BENEFICIALS: list[PestTaxon] = [
    PestTaxon(
        slug="ladybird",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Marienkäfer (inkl. Larven)",
        scientific_name="Coccinellidae",
        gbif_taxon_key="7782",
        inat_life_stage="Larva",  # close the beneficial-larvae gap (§4.1)
        preys_on=["aphid", "spider_mite", "mealybug"],
    ),
    PestTaxon(
        slug="lacewing",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Florfliegen (Larven)",
        scientific_name="Chrysopidae",
        gbif_taxon_key="9265",
        inat_life_stage="Larva",  # close the beneficial-larvae gap (§4.1)
        preys_on=["aphid", "spider_mite", "thrips_frankliniella"],
    ),
    PestTaxon(
        slug="hoverfly",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Schwebfliegen (Larven)",
        scientific_name="Syrphidae",
        gbif_taxon_key="6920",
        inat_life_stage="Larva",  # close the beneficial-larvae gap (§4.1)
        preys_on=["aphid"],
    ),
    PestTaxon(
        slug="predatory_mite",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Raubmilben",
        scientific_name="Phytoseiidae",
        gbif_taxon_key="3511",
        preys_on=["spider_mite", "thrips_frankliniella", "thrips_echinothrips"],
    ),
    PestTaxon(
        slug="parasitoid_wasp",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Schlupfwespe (Encarsia formosa)",
        scientific_name="Encarsia formosa",
        gbif_taxon_key="1365418",
        # Encarsia formosa parasitiert ausschliesslich Weisse Fliege, nicht
        # Blattlaeuse (dafuer waeren Aphidius-Arten zustaendig).
        preys_on=["whitefly"],
    ),
]

# WP-4.3 — Reject-/Abstention-Klasse (Open-Set). Nie persistiert als Stammdaten.
UNKNOWN_TAXON = PestTaxon(
    slug="unknown",
    category=PestFindingCategory.UNKNOWN,
    common_name_de="Unbekannt",
    scientific_name="",
)

PEST_TAXONOMY: list[PestTaxon] = [*_PESTS, *_BENEFICIALS]

_BY_SLUG: dict[str, PestTaxon] = {t.slug: t for t in PEST_TAXONOMY}


def get_taxon(slug: str) -> PestTaxon | None:
    """Return the taxon for a slug, or ``None`` for an unknown label."""
    if slug == UNKNOWN_TAXON.slug:
        return UNKNOWN_TAXON
    return _BY_SLUG.get(slug)


def beneficial_taxa() -> list[PestTaxon]:
    """Return the beneficial classes (WP-8 ``beneficials`` seed source)."""
    return list(_BENEFICIALS)


def pest_taxa() -> list[PestTaxon]:
    """Return the pest classes (Modus-1/2 detection labels)."""
    return list(_PESTS)
