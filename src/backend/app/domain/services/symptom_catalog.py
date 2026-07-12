"""REQ-036 §4.1 — the curated symptom catalogue.

A static, in-process catalogue (no ArangoDB collection, no migration). The
catalogue seeds the diagnosis wizard's first step and provides the human-readable
symptom labels the analysis engine folds into the knowledge-base query. Kept as
code (not a ``spec/`` YAML) so it ships inside the backend image and is trivially
unit-testable — the container build context is ``src/backend`` and never
``spec/``.
"""

from __future__ import annotations

from app.domain.models.diagnosis import SymptomCatalogEntry, SymptomCategory

#: Phase keys used across the catalogue (mirror REQ-003 lifecycle phases).
_ALL_PHASES = ["germination", "seedling", "vegetative", "flowering", "harvest"]
_LATE_PHASES = ["vegetative", "flowering", "harvest"]


def _entry(
    slug: str,
    category: SymptomCategory,
    label_de: str,
    label_en: str,
    *,
    phases: list[str],
    hint_de: str,
    hint_en: str,
) -> SymptomCatalogEntry:
    return SymptomCatalogEntry(
        slug=slug,
        category=category,
        label_de=label_de,
        label_en=label_en,
        applicable_phases=phases,
        common_causes_hint_de=hint_de,
        common_causes_hint_en=hint_en,
    )


#: The curated catalogue (>=30 symptoms across the seven categories, §2.1).
SYMPTOM_CATALOG: list[SymptomCatalogEntry] = [
    # ── leaf_color_change ──────────────────────────────────────────────
    _entry(
        "leaves_yellowing_lower",
        SymptomCategory.LEAF_COLOR_CHANGE,
        "Vergilbung der unteren Blaetter",
        "Yellowing of lower leaves",
        phases=_LATE_PHASES,
        hint_de="Haeufig Stickstoffmangel oder Ueberwaesserung.",
        hint_en="Often nitrogen deficiency or overwatering.",
    ),
    _entry(
        "leaves_yellowing_upper",
        SymptomCategory.LEAF_COLOR_CHANGE,
        "Vergilbung der oberen Blaetter",
        "Yellowing of upper leaves",
        phases=_LATE_PHASES,
        hint_de="Deutet auf Eisen- oder Schwefelmangel hin.",
        hint_en="Suggests iron or sulphur deficiency.",
    ),
    _entry(
        "interveinal_chlorosis",
        SymptomCategory.LEAF_COLOR_CHANGE,
        "Chlorose zwischen den Blattadern",
        "Interveinal chlorosis",
        phases=_LATE_PHASES,
        hint_de="Typisch fuer Magnesium- oder Manganmangel.",
        hint_en="Typical of magnesium or manganese deficiency.",
    ),
    _entry(
        "leaf_edges_browning",
        SymptomCategory.LEAF_COLOR_CHANGE,
        "Braune Blattraender",
        "Browning leaf edges",
        phases=_LATE_PHASES,
        hint_de="Naehrstoffbrand (Ueberduengung) oder Kaliummangel.",
        hint_en="Nutrient burn (over-fertilisation) or potassium deficiency.",
    ),
    _entry(
        "purple_stems",
        SymptomCategory.LEAF_COLOR_CHANGE,
        "Violette Stiele oder Blattunterseiten",
        "Purple stems or leaf undersides",
        phases=["seedling", "vegetative"],
        hint_de="Phosphormangel oder Kaeltestress.",
        hint_en="Phosphorus deficiency or cold stress.",
    ),
    _entry(
        "white_powdery_coating",
        SymptomCategory.LEAF_COLOR_CHANGE,
        "Weisser, mehliger Belag",
        "White powdery coating",
        phases=_LATE_PHASES,
        hint_de="Klassisches Zeichen fuer Echten Mehltau.",
        hint_en="Classic sign of powdery mildew.",
    ),
    # ── leaf_shape_change ──────────────────────────────────────────────
    _entry(
        "leaves_curling_down",
        SymptomCategory.LEAF_SHAPE_CHANGE,
        "Nach unten eingerollte Blaetter",
        "Leaves curling downward",
        phases=_LATE_PHASES,
        hint_de="Ueberwaesserung, Hitze oder Ueberduengung.",
        hint_en="Overwatering, heat or over-fertilisation.",
    ),
    _entry(
        "leaves_curling_up",
        SymptomCategory.LEAF_SHAPE_CHANGE,
        "Nach oben eingerollte Blaetter (Taco)",
        "Leaves curling upward (taco)",
        phases=_LATE_PHASES,
        hint_de="Hitze- oder Lichtstress.",
        hint_en="Heat or light stress.",
    ),
    _entry(
        "leaves_wilting",
        SymptomCategory.LEAF_SHAPE_CHANGE,
        "Welke, haengende Blaetter",
        "Wilting, drooping leaves",
        phases=_ALL_PHASES,
        hint_de="Unter- oder Ueberwaesserung, Wurzelprobleme.",
        hint_en="Under- or overwatering, root problems.",
    ),
    _entry(
        "leaf_spots",
        SymptomCategory.LEAF_SHAPE_CHANGE,
        "Flecken auf den Blaettern",
        "Spots on the leaves",
        phases=_LATE_PHASES,
        hint_de="Pilzkrankheit, Blattflecken oder Naehrstoffmangel.",
        hint_en="Fungal disease, leaf spot or nutrient deficiency.",
    ),
    _entry(
        "leaf_holes",
        SymptomCategory.LEAF_SHAPE_CHANGE,
        "Loecher oder Frassspuren im Blatt",
        "Holes or feeding marks in the leaf",
        phases=_LATE_PHASES,
        hint_de="Fressende Schaedlinge wie Raupen oder Kaefer.",
        hint_en="Chewing pests such as caterpillars or beetles.",
    ),
    _entry(
        "leaf_deformation",
        SymptomCategory.LEAF_SHAPE_CHANGE,
        "Verkrueppelte oder deformierte Blaetter",
        "Crippled or deformed leaves",
        phases=_LATE_PHASES,
        hint_de="Virusbefall, Milben oder Herbizidschaden.",
        hint_en="Virus, mites or herbicide damage.",
    ),
    # ── growth_anomaly ─────────────────────────────────────────────────
    _entry(
        "stunted_growth",
        SymptomCategory.GROWTH_ANOMALY,
        "Verkuemmertes Wachstum",
        "Stunted growth",
        phases=_ALL_PHASES,
        hint_de="Wurzelprobleme, Naehrstoffmangel oder pH-Sperre.",
        hint_en="Root problems, nutrient deficiency or pH lockout.",
    ),
    _entry(
        "leggy_stretching",
        SymptomCategory.GROWTH_ANOMALY,
        "Vergeilung (duenne, lange Triebe)",
        "Leggy stretching (thin, long shoots)",
        phases=["seedling", "vegetative"],
        hint_de="Zu wenig Licht oder falsche Photoperiode.",
        hint_en="Too little light or wrong photoperiod.",
    ),
    _entry(
        "slow_seed_germination",
        SymptomCategory.GROWTH_ANOMALY,
        "Verzoegerte oder ausbleibende Keimung",
        "Delayed or absent germination",
        phases=["germination"],
        hint_de="Temperatur, Feuchte oder altes Saatgut.",
        hint_en="Temperature, moisture or old seed.",
    ),
    _entry(
        "damping_off",
        SymptomCategory.GROWTH_ANOMALY,
        "Umfallkrankheit der Saemlinge",
        "Damping-off of seedlings",
        phases=["germination", "seedling"],
        hint_de="Pilzbefall bei zu hoher Feuchte.",
        hint_en="Fungal infection at excessive moisture.",
    ),
    _entry(
        "wilting_despite_moisture",
        SymptomCategory.GROWTH_ANOMALY,
        "Welke trotz feuchtem Substrat",
        "Wilting despite moist substrate",
        phases=_LATE_PHASES,
        hint_de="Wurzelfaeule oder Sauerstoffmangel im Wurzelraum.",
        hint_en="Root rot or oxygen deficit in the root zone.",
    ),
    # ── pest_visible ───────────────────────────────────────────────────
    _entry(
        "small_flying_insects",
        SymptomCategory.PEST_VISIBLE,
        "Kleine fliegende Insekten",
        "Small flying insects",
        phases=_LATE_PHASES,
        hint_de="Trauermuecken oder Weisse Fliege.",
        hint_en="Fungus gnats or whitefly.",
    ),
    _entry(
        "webbing_on_leaves",
        SymptomCategory.PEST_VISIBLE,
        "Feine Gespinste an den Blaettern",
        "Fine webbing on the leaves",
        phases=_LATE_PHASES,
        hint_de="Deutlicher Hinweis auf Spinnmilben.",
        hint_en="Clear sign of spider mites.",
    ),
    _entry(
        "sticky_honeydew",
        SymptomCategory.PEST_VISIBLE,
        "Klebriger Honigtau auf Blaettern",
        "Sticky honeydew on leaves",
        phases=_LATE_PHASES,
        hint_de="Blattlaeuse, Schild- oder Wollaeuse.",
        hint_en="Aphids, scale or mealybugs.",
    ),
    _entry(
        "visible_aphids",
        SymptomCategory.PEST_VISIBLE,
        "Sichtbare Blattlaeuse an Trieben",
        "Visible aphids on shoots",
        phases=_LATE_PHASES,
        hint_de="Blattlausbefall, oft an jungen Trieben.",
        hint_en="Aphid infestation, often on young shoots.",
    ),
    _entry(
        "tiny_moving_dots",
        SymptomCategory.PEST_VISIBLE,
        "Winzige bewegliche Punkte (Lupe)",
        "Tiny moving dots (under a loupe)",
        phases=_LATE_PHASES,
        hint_de="Milben oder Thripse.",
        hint_en="Mites or thrips.",
    ),
    _entry(
        "silvery_leaf_speckling",
        SymptomCategory.PEST_VISIBLE,
        "Silbrige Sprenkelung der Blaetter",
        "Silvery speckling of the leaves",
        phases=_LATE_PHASES,
        hint_de="Typisches Thrips-Schadbild.",
        hint_en="Typical thrips damage pattern.",
    ),
    # ── disease_visible ────────────────────────────────────────────────
    _entry(
        "grey_mould",
        SymptomCategory.DISEASE_VISIBLE,
        "Grauer, pelziger Schimmel",
        "Grey, fuzzy mould",
        phases=["flowering", "harvest"],
        hint_de="Botrytis (Grauschimmel), vor allem an Blueten.",
        hint_en="Botrytis (grey mould), especially on flowers.",
    ),
    _entry(
        "downy_mildew",
        SymptomCategory.DISEASE_VISIBLE,
        "Gelbe Flecken mit grauem Belag unterseits",
        "Yellow spots with grey coating underneath",
        phases=_LATE_PHASES,
        hint_de="Falscher Mehltau.",
        hint_en="Downy mildew.",
    ),
    _entry(
        "rust_pustules",
        SymptomCategory.DISEASE_VISIBLE,
        "Rostbraune Pusteln auf der Blattunterseite",
        "Rust-brown pustules on the leaf underside",
        phases=_LATE_PHASES,
        hint_de="Rostpilz.",
        hint_en="Rust fungus.",
    ),
    _entry(
        "stem_rot",
        SymptomCategory.DISEASE_VISIBLE,
        "Faulender, weicher Stiel an der Basis",
        "Rotting, soft stem at the base",
        phases=_LATE_PHASES,
        hint_de="Stengelfaeule oder Wurzelhalsfaeule.",
        hint_en="Stem rot or crown rot.",
    ),
    _entry(
        "mosaic_pattern",
        SymptomCategory.DISEASE_VISIBLE,
        "Mosaikartige Aufhellung der Blaetter",
        "Mosaic-like mottling of the leaves",
        phases=_LATE_PHASES,
        hint_de="Virusinfektion (z. B. Mosaikvirus).",
        hint_en="Viral infection (e.g. mosaic virus).",
    ),
    # ── flowering_issue ────────────────────────────────────────────────
    _entry(
        "no_flowering",
        SymptomCategory.FLOWERING_ISSUE,
        "Ausbleibende Bluetenbildung",
        "Absent flower formation",
        phases=["vegetative", "flowering"],
        hint_de="Photoperiode, Alter oder Naehrstoffprofil.",
        hint_en="Photoperiod, age or nutrient profile.",
    ),
    _entry(
        "flower_drop",
        SymptomCategory.FLOWERING_ISSUE,
        "Abfallende Blueten oder Fruchtansaetze",
        "Dropping flowers or fruit set",
        phases=["flowering"],
        hint_de="Hitze-, Wasser- oder Bestaeubungsstress.",
        hint_en="Heat, water or pollination stress.",
    ),
    _entry(
        "hermaphrodite_flowers",
        SymptomCategory.FLOWERING_ISSUE,
        "Zwittrige Blueten",
        "Hermaphrodite flowers",
        phases=["flowering"],
        hint_de="Lichtstress oder genetische Instabilitaet.",
        hint_en="Light stress or genetic instability.",
    ),
    _entry(
        "buds_not_ripening",
        SymptomCategory.FLOWERING_ISSUE,
        "Blueten reifen nicht aus",
        "Buds not ripening",
        phases=["flowering", "harvest"],
        hint_de="Zu niedrige Temperatur oder Naehrstoffueberschuss.",
        hint_en="Temperature too low or nutrient excess.",
    ),
    # ── environmental ──────────────────────────────────────────────────
    _entry(
        "leaf_burn_tips",
        SymptomCategory.ENVIRONMENTAL,
        "Verbrannte Blattspitzen unter der Lampe",
        "Burnt leaf tips under the lamp",
        phases=_LATE_PHASES,
        hint_de="Lichtbrand (Lampe zu nah).",
        hint_en="Light burn (lamp too close).",
    ),
    _entry(
        "cold_stress_symptoms",
        SymptomCategory.ENVIRONMENTAL,
        "Kaelteschaeden (violette/schlaffe Blaetter)",
        "Cold damage (purple/limp leaves)",
        phases=_ALL_PHASES,
        hint_de="Temperatur unter dem Optimum.",
        hint_en="Temperature below optimum.",
    ),
    _entry(
        "heat_stress_symptoms",
        SymptomCategory.ENVIRONMENTAL,
        "Hitzestress (Taco-Blaetter, Welke)",
        "Heat stress (taco leaves, wilting)",
        phases=_LATE_PHASES,
        hint_de="Temperatur oder VPD zu hoch.",
        hint_en="Temperature or VPD too high.",
    ),
    _entry(
        "overwatering_signs",
        SymptomCategory.ENVIRONMENTAL,
        "Anzeichen von Ueberwaesserung",
        "Signs of overwatering",
        phases=_ALL_PHASES,
        hint_de="Staunaesse, schwere haengende Blaetter.",
        hint_en="Waterlogging, heavy drooping leaves.",
    ),
]


class SymptomCatalog:
    """Read-only access to the curated symptom catalogue."""

    def __init__(self, entries: list[SymptomCatalogEntry] | None = None) -> None:
        self._entries = entries if entries is not None else SYMPTOM_CATALOG
        self._by_slug = {e.slug: e for e in self._entries}

    def list_symptoms(
        self,
        *,
        phase: str | None = None,
        category: str | None = None,
    ) -> list[SymptomCatalogEntry]:
        """Return the catalogue, optionally filtered by phase and/or category."""
        results = self._entries
        if phase:
            results = [e for e in results if not e.applicable_phases or phase in e.applicable_phases]
        if category:
            results = [e for e in results if e.category == category]
        return list(results)

    def get_symptom(self, slug: str) -> SymptomCatalogEntry | None:
        """Return one catalogue entry by slug (or ``None`` when unknown)."""
        return self._by_slug.get(slug)

    def resolve(self, slugs: list[str]) -> list[SymptomCatalogEntry]:
        """Resolve a list of slugs to catalogue entries, dropping unknowns."""
        resolved = [self._by_slug.get(slug) for slug in slugs]
        return [e for e in resolved if e is not None]
