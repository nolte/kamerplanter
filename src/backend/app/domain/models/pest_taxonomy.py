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
    # English name, set only where a source names one (E-10, #2936); the source sits
    # next to each value. ``None`` -> an English UI shows ``common_name_de``.
    common_name_en: str | None = None
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

    def names_i18n(self) -> dict[str, list[str]]:
        """The taxon's names as a ``common_names_i18n`` map (REQ-010 v1.8, #2936): only the languages it names."""
        names: dict[str, list[str]] = {"de": [self.common_name_de]}
        if self.common_name_en:
            names["en"] = [self.common_name_en]
        return names


# WP-4.1 — Schädlinge (category=pest). ``scientific_name`` matcht die
# REQ-010-pests-Stammdaten; ``symptom_hint_de`` deckt den Schadbild-Modus ab.
_PESTS: list[PestTaxon] = [
    PestTaxon(
        slug="spider_mite",
        category=PestFindingCategory.PEST,
        common_name_de="Gemeine Spinnmilbe",
        # "common names include red spider mite and two-spotted spider mite"
        # Source: https://en.wikipedia.org/wiki/Tetranychus_urticae
        common_name_en="Two-spotted spider mite",
        scientific_name="Tetranychus urticae",
        gbif_taxon_key="2130185",
        symptom_hint_de=("helle Sprenkelung der Blattoberseite, feine Gespinste an der Blattunterseite, Bronzefärbung"),
    ),
    PestTaxon(
        slug="thrips_frankliniella",
        category=PestFindingCategory.PEST,
        common_name_de="Kalifornischer Blütenthrips",
        # "The western flower thrips [Frankliniella occidentalis (Pergande)] is an invasive pest"
        # Source: https://en.wikipedia.org/wiki/Western_flower_thrips
        common_name_en="Western flower thrips",
        scientific_name="Frankliniella occidentalis",
        gbif_taxon_key="8351995",
        symptom_hint_de="silbrig-graue Saugflecken, schwarze Kotpünktchen, deformierte Blätter/Blüten",
    ),
    PestTaxon(
        slug="thrips_echinothrips",
        category=PestFindingCategory.PEST,
        common_name_de="Bunter Blütenthrips",
        # "Suggested common names include Poinsettia thrips and Impatiens thrips."
        # Source: https://en.wikipedia.org/wiki/Echinothrips_americanus
        common_name_en="Poinsettia thrips",
        scientific_name="Echinothrips americanus",
        gbif_taxon_key="1420846",
        symptom_hint_de="silbrig-bronzene Saugflächen auf der Blattoberseite",
    ),
    PestTaxon(
        slug="fungus_gnat",
        category=PestFindingCategory.PEST,
        common_name_de="Trauermücken",
        # "a family of flies, commonly known as dark-winged fungus gnats"
        # Source: https://en.wikipedia.org/wiki/Sciaridae
        common_name_en="Dark-winged fungus gnats",
        scientific_name="Sciaridae",
        gbif_taxon_key="3525",
        symptom_hint_de="schwarze Mücken über dem Substrat; weiße Larven im Substrat (Wurzelfraß)",
    ),
    PestTaxon(
        slug="aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Blattläuse",
        # "Aphids are small sap-sucking insects in the family Aphididae"
        # Source: https://en.wikipedia.org/wiki/Aphid
        common_name_en="Aphids",
        scientific_name="Aphididae",
        gbif_taxon_key="3042",
        symptom_hint_de="Honigtau/klebrig, Rußtau, gekräuselte Triebspitzen, Kolonien, Häutungshüllen",
    ),
    PestTaxon(
        slug="mealybug",
        category=PestFindingCategory.PEST,
        common_name_de="Schmier-/Wollläuse",
        # "Mealybugs are insects in the family Pseudococcidae"
        # Source: https://en.wikipedia.org/wiki/Mealybug
        common_name_en="Mealybugs",
        scientific_name="Pseudococcidae",
        gbif_taxon_key="4534",
        symptom_hint_de="weiße Watte in Blattachseln, Honigtau und Rußtau",
    ),
    PestTaxon(
        slug="whitefly",
        category=PestFindingCategory.PEST,
        common_name_de="Weiße Fliege",
        # "commonly known as the glasshouse whitefly or greenhouse whitefly"
        # Source: https://en.wikipedia.org/wiki/Greenhouse_whitefly
        common_name_en="Greenhouse whitefly",
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
        # "The cabbage looper (Trichoplusia ni) is a medium-sized moth"
        # Source: https://en.wikipedia.org/wiki/Cabbage_looper
        common_name_en="Cabbage looper",
        scientific_name="Trichoplusia ni",
        gbif_taxon_key="1786360",
    ),
    PestTaxon(
        slug="scale_insect",
        category=PestFindingCategory.PEST,
        common_name_de="Schildläuse",
        # "Scale insects are small insects of the order Hemiptera"
        # Source: https://en.wikipedia.org/wiki/Scale_insect
        common_name_en="Scale insects",
        scientific_name="Coccoidea",
        gbif_taxon_key="5953662",
    ),
    PestTaxon(
        slug="flea_beetle",
        category=PestFindingCategory.PEST,
        common_name_de="Erdflöhe",
        # "Phyllotreta is a genus of flea beetles in the family Chrysomelidae."
        # Source: https://en.wikipedia.org/wiki/Phyllotreta
        common_name_en="Flea beetles",
        scientific_name="Phyllotreta",
        gbif_taxon_key="1049215",
    ),
    PestTaxon(
        slug="spanish_slug",
        category=PestFindingCategory.PEST,
        common_name_de="Spanische Wegschnecke",
        # "The Spanish slug (Arion vulgaris, but formerly widely referred to as Arion lusitanicus"
        # Source: https://en.wikipedia.org/wiki/Spanish_slug
        common_name_en="Spanish slug",
        scientific_name="Arion vulgaris",
        gbif_taxon_key="7540164",
    ),
    PestTaxon(
        slug="root_knot_nematode",
        category=PestFindingCategory.PEST,
        common_name_de="Wurzelgallenälchen",
        # "Root-knot nematodes are plant-parasitic nematodes from the genus Meloidogyne."
        # Source: https://en.wikipedia.org/wiki/Root-knot_nematode
        common_name_en="Root-knot nematodes",
        scientific_name="Meloidogyne",
        gbif_taxon_key="9705419",  # microscopic — only damage (root galls) photographable
    ),
    PestTaxon(
        slug="large_cabbage_white",
        category=PestFindingCategory.PEST,
        common_name_de="Großer Kohlweißling",
        # "Pieris brassicae, the large white, also called cabbage butterfly, cabbage white"
        # Source: https://en.wikipedia.org/wiki/Pieris_brassicae
        common_name_en="Large white",
        scientific_name="Pieris brassicae",
        gbif_taxon_key="1920506",
    ),
    PestTaxon(
        slug="small_cabbage_white",
        category=PestFindingCategory.PEST,
        common_name_de="Kleiner Kohlweißling",
        # "It is known in Europe as the small white"
        # Source: https://en.wikipedia.org/wiki/Pieris_rapae
        common_name_en="Small white",
        scientific_name="Pieris rapae",
        gbif_taxon_key="1920496",
    ),
    PestTaxon(
        slug="colorado_potato_beetle",
        category=PestFindingCategory.PEST,
        common_name_de="Kartoffelkäfer",
        # "The Colorado potato beetle (Leptinotarsa decemlineata; also known as the Colorado beetle"
        # Source: https://en.wikipedia.org/wiki/Colorado_potato_beetle
        common_name_en="Colorado potato beetle",
        scientific_name="Leptinotarsa decemlineata",
        gbif_taxon_key="1047536",
    ),
    PestTaxon(
        slug="codling_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Apfelwickler",
        # "The codling moth or (especially Australia) codlin moth (Cydia pomonella)"
        # Source: https://en.wikipedia.org/wiki/Codling_moth
        common_name_en="Codling moth",
        scientific_name="Cydia pomonella",
        gbif_taxon_key="1737847",
    ),
    PestTaxon(
        slug="leek_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Lauchmotte",
        # "The leek moth or onion leaf miner (Acrolepiopsis assectella)"
        # Source: https://en.wikipedia.org/wiki/Leek_moth
        common_name_en="Leek moth",
        scientific_name="Acrolepiopsis assectella",
        gbif_taxon_key="4525339",
    ),
    PestTaxon(
        slug="carrot_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Möhrenfliege",
        # "The carrot fly (Chamaepsila rosae) is a pest of gardens and farms"
        # Source: https://en.wikipedia.org/wiki/Carrot_fly
        common_name_en="Carrot fly",
        scientific_name="Psila rosae",
        gbif_taxon_key="5713486",
    ),
    PestTaxon(
        slug="onion_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Zwiebelfliege",
        # "Delia antiqua, commonly known as the onion fly"
        # Source: https://en.wikipedia.org/wiki/Delia_antiqua
        common_name_en="Onion fly",
        scientific_name="Delia antiqua",
        gbif_taxon_key="5077646",
    ),
    PestTaxon(
        slug="cabbage_root_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlfliege",
        # "known variously as the cabbage fly, cabbage root fly, root fly or turnip fly"
        # Source: https://en.wikipedia.org/wiki/Delia_radicum
        common_name_en="Cabbage root fly",
        scientific_name="Delia radicum",
        gbif_taxon_key="5077574",
    ),
    PestTaxon(
        slug="cherry_fruit_fly",
        category=PestFindingCategory.PEST,
        common_name_de="Kirschfruchtfliege",
        # "Rhagoletis cerasi (the cherry fruit fly or European cherry fruit fly)"
        # Source: https://en.wikipedia.org/wiki/Rhagoletis_cerasi
        common_name_en="European cherry fruit fly",
        scientific_name="Rhagoletis cerasi",
        gbif_taxon_key="1622583",
    ),
    PestTaxon(
        slug="box_tree_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Buchsbaumzünsler",
        # "Cydalima perspectalis, the box moth or box tree moth"
        # Source: https://en.wikipedia.org/wiki/Cydalima_perspectalis
        common_name_en="Box tree moth",
        scientific_name="Cydalima perspectalis",
        gbif_taxon_key="4532122",
    ),
    PestTaxon(
        slug="strawberry_blossom_weevil",
        category=PestFindingCategory.PEST,
        common_name_de="Erdbeerblütenstecher",
        # "Anthonomus rubi, the strawberry-blossom weevil or strawberry blossom weevil"
        # Source: https://en.wikipedia.org/wiki/Anthonomus_rubi
        common_name_en="Strawberry blossom weevil",
        scientific_name="Anthonomus rubi",
        gbif_taxon_key="1196192",
    ),
    PestTaxon(
        slug="vine_weevil",
        category=PestFindingCategory.PEST,
        common_name_de="Dickmaulrüssler",
        # "The black vine weevil (Otiorhynchus sulcatus) is an insect native to Europe"
        # Source: https://en.wikipedia.org/wiki/Vine_weevil
        common_name_en="Black vine weevil",
        scientific_name="Otiorhynchus sulcatus",
        gbif_taxon_key="1195129",
    ),
    PestTaxon(
        slug="cabbage_whitefly",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlmottenschildlaus",
        # "Aleyrodes proletella, the cabbage whitefly, is a species of whitefly"
        # Source: https://en.wikipedia.org/wiki/Aleyrodes_proletella
        common_name_en="Cabbage whitefly",
        scientific_name="Aleyrodes proletella",
        gbif_taxon_key="4484303",
    ),
    PestTaxon(
        slug="wireworm",
        category=PestFindingCategory.PEST,
        common_name_de="Drahtwurm (Larve des Schnellkäfers)",
        # "the larvae (wireworms) are elongated with a hardened cuticle"
        # Source: https://en.wikipedia.org/wiki/Agriotes
        common_name_en="Wireworms",
        scientific_name="Agriotes",
        gbif_taxon_key="1162125",
    ),
    PestTaxon(
        slug="european_corn_borer",
        category=PestFindingCategory.PEST,
        common_name_de="Maiszünsler",
        # "The European corn borer (Ostrinia nubilalis), also known as the European corn worm"
        # Source: https://en.wikipedia.org/wiki/European_corn_borer
        common_name_en="European corn borer",
        scientific_name="Ostrinia nubilalis",
        gbif_taxon_key="8223165",
    ),
    PestTaxon(
        slug="green_peach_aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Grüne Pfirsichblattlaus",
        # "known as the green peach aphid, greenfly, or the peach-potato aphid"
        # Source: https://en.wikipedia.org/wiki/Myzus_persicae
        common_name_en="Green peach aphid",
        scientific_name="Myzus persicae",
        gbif_taxon_key="2076179",
    ),
    PestTaxon(
        slug="potato_aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Kartoffelblattlaus",
        # "Macrosiphum euphorbiae, the potato aphid, is a sap-sucking pest insect"
        # Source: https://en.wikipedia.org/wiki/Macrosiphum_euphorbiae
        common_name_en="Potato aphid",
        scientific_name="Macrosiphum euphorbiae",
        gbif_taxon_key="2077747",
    ),
    PestTaxon(
        slug="cabbage_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Kohleule",
        # "The cabbage moth (Mamestra brassicae) is primarily known as a pest"
        # Source: https://en.wikipedia.org/wiki/Cabbage_moth
        common_name_en="Cabbage moth",
        scientific_name="Mamestra brassicae",
        gbif_taxon_key="1788522",
    ),
    PestTaxon(
        slug="diamondback_moth",
        category=PestFindingCategory.PEST,
        common_name_de="Kohlschabe",
        # "The diamondback moth (Plutella xylostella)"
        # Source: https://en.wikipedia.org/wiki/Diamondback_moth
        common_name_en="Diamondback moth",
        scientific_name="Plutella xylostella",
        gbif_taxon_key="1831136",
    ),
    PestTaxon(
        slug="waterlily_aphid",
        category=PestFindingCategory.PEST,
        common_name_de="Seerosenblattlaus",
        # "Rhopalosiphum nymphaeae, the waterlily aphid, is a species of aphid"
        # Source: https://en.wikipedia.org/wiki/Rhopalosiphum_nymphaeae
        common_name_en="Waterlily aphid",
        scientific_name="Rhopalosiphum nymphaeae",
        gbif_taxon_key="9565622",
    ),
    PestTaxon(
        slug="waterlily_leaf_beetle",
        category=PestFindingCategory.PEST,
        common_name_de="Seerosenblattkäfer",
        # "known generally as the water-lily beetle or water lily leaf beetle"
        # Source: https://en.wikipedia.org/wiki/Galerucella_nymphaeae
        common_name_en="Water lily leaf beetle",
        scientific_name="Galerucella nymphaeae",
        gbif_taxon_key="1048344",
    ),
    PestTaxon(
        slug="brown_china_mark",
        category=PestFindingCategory.PEST,
        common_name_de="Seerosenzünsler",
        # "Elophila nymphaeata, the brown china mark, is a species of moth"
        # Source: https://en.wikipedia.org/wiki/Elophila_nymphaeata
        common_name_en="Brown china mark",
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
        # Source: https://en.wikipedia.org/wiki/Coccinellidae ("commonly known as ... ladybirds")
        common_name_en="Ladybirds",
        scientific_name="Coccinellidae",
        gbif_taxon_key="7782",
        inat_life_stage="Larva",  # close the beneficial-larvae gap (§4.1)
        preys_on=["aphid", "spider_mite", "mealybug"],
    ),
    PestTaxon(
        slug="lacewing",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Florfliegen (Larven)",
        # Source: https://en.wikipedia.org/wiki/Chrysopidae ("Green lacewings are insects in ... Chrysopidae")
        common_name_en="Green lacewings",
        scientific_name="Chrysopidae",
        gbif_taxon_key="9265",
        inat_life_stage="Larva",  # close the beneficial-larvae gap (§4.1)
        preys_on=["aphid", "spider_mite", "thrips_frankliniella"],
    ),
    PestTaxon(
        slug="hoverfly",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Schwebfliegen (Larven)",
        # Source: https://en.wikipedia.org/wiki/Hoverfly ("Hoverflies ... make up the insect family Syrphidae")
        common_name_en="Hoverflies",
        scientific_name="Syrphidae",
        gbif_taxon_key="6920",
        inat_life_stage="Larva",  # close the beneficial-larvae gap (§4.1)
        preys_on=["aphid"],
    ),
    PestTaxon(
        slug="predatory_mite",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Raubmilben",
        # Source: https://en.wikipedia.org/wiki/Phytoseiidae ("a family of predatory mites")
        common_name_en="Predatory mites",
        scientific_name="Phytoseiidae",
        gbif_taxon_key="3511",
        preys_on=["spider_mite", "thrips_frankliniella", "thrips_echinothrips"],
    ),
    PestTaxon(
        slug="parasitoid_wasp",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Schlupfwespe (Encarsia formosa)",
        # No English common name: https://en.wikipedia.org/wiki/Encarsia_formosa names
        # the species only by its scientific name, so an English UI shows the German one.
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
