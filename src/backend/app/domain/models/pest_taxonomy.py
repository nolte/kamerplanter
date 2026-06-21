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
        preys_on=["aphid", "spider_mite", "mealybug"],
    ),
    PestTaxon(
        slug="lacewing",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Florfliegen (Larven)",
        scientific_name="Chrysopidae",
        gbif_taxon_key="9265",
        preys_on=["aphid", "spider_mite", "thrips_frankliniella"],
    ),
    PestTaxon(
        slug="hoverfly",
        category=PestFindingCategory.BENEFICIAL,
        common_name_de="Schwebfliegen (Larven)",
        scientific_name="Syrphidae",
        gbif_taxon_key="6920",
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
        common_name_de="Schlupfwespen",
        scientific_name="Encarsia formosa",
        gbif_taxon_key="1365418",
        preys_on=["whitefly", "aphid"],
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
