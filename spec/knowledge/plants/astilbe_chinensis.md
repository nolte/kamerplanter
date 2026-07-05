# Chinesische Prachtspiere — Astilbe chinensis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Astilbe chinensis, Lubera Prachtspiere, Floragard Astilbe chinensis, Gartenjournal Prachtspiere

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Astilbe chinensis | `species.scientific_name` |
| Volksnamen (DE/EN) | Chinesische Prachtspiere, Astilbe; Chinese Astilbe | `species.common_names` |
| Familie | Saxifragaceae | `species.family` → `botanical_families.name` |
| Gattung | Astilbe | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; trockenheitstoleranter als andere Astilbe-Arten; in ganz Norddeutschland problemlos | `species.hardiness_detail` |
| Heimat | China, Korea | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 5 (kühlliebende Staude / cool-season; Wachstum/Blüte ab Bodentemperatur ~13–16 °C) | `species.base_temp` |
| Lebensdauer (Jahre) | 10–15+ (langlebige Staude, alle 3–5 J. teilen) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (obligater Kältebedarf: min. ~10 Wochen < ~4 °C vor Blüteneinleitung) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 70 | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> (fakultativer Langtagblüher / facultative long-day — kein scharfer Schwellenwert belegbar; Kurztag ~9 h löst Dormanz aus) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Teilung bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Trockenblumen möglich) | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (Spätblühend; länger als A. arendsii) | `species.bloom_months` |

**Hinweis:** Astilbe chinensis blüht später als die meisten anderen Astilbe-Arten (Juli–September statt Juni–Juli). Trockenere Standorte als A. arendsii möglich.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3 (Frühjahr) | `species.pruning_months` |

**Hinweis:** Verblühte Blütenstände für dekorativen Winteraspekt stehen lassen — geben interessante Textur bei Frost und Schnee. Im Frühjahr (März) bodennah abschneiden. NICHT im Herbst schneiden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–120 (je nach Sorte; var. pumila: 20–30 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, feuchtigkeitsspeichernde Erde; pH 5,5–6,5; leicht sauer; gut wasserhaltig | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (keine artspezifische Messung aus 2 seriösen Quellen; Astilbe ist schattentolerant, daher physiologisch niedrig, aber kein belegter Zahlenwert) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–30 (flach- bis mittelwurzelnde Staude; Krone 3–5 cm unter Bodenniveau, fibröses Rhizom) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | moderate (liebt gleichmäßig feuchte, auch schwere/sumpfige Böden, verträgt aber keine Dauer-Staunässe/stehendes Wasser) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> (keine belegten Maas-Hoffman-Werte für Astilbe; Klasse "sensitive" impliziert ≈ <2, jedoch kein Zahlenwert aus 2 Quellen) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis (Lichtphysiologie):** Astilbe chinensis ist ein schattentoleranter C3-Unterwuchs-Typ (partial_shade); RHS und Missouri Botanical Garden führen "partial shade" bzw. "part shade to full shade". In voller Sonne nur bei dauerhaft feuchtem Boden, sonst Blattrandverbrennung (leaf scorch). A. chinensis verträgt mehr Sonne und Trockenheit als die A.-×-arendsii-Hybriden, bleibt aber drought-intolerant.

**Hinweis (Salz):** Quellenlage uneinheitlich — einzelne Gartenlisten führen Astilbe als salzverträglich, doch University-Extension-/RHS-nahe Quellen und das feuchte Halbschatten-Profil sprechen klar für eine salzempfindliche (sensitive) Einstufung; Astilbe wird nicht als Küsten-/Streusalzpflanze empfohlen. Bezugsgröße einer etwaigen Schwelle wäre Substrat-ECe, nicht Gießwasser-EC.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- SECTION MISSING: seed_profile — vegetativ vermehrt (Astilbe chinensis wird gärtnerisch praktisch ausschließlich durch Teilung des Rhizoms vermehrt — §1.3 dieses Steckbriefs nennt ausschließlich "division" als Vermehrungsmethode. Die im Handel verbreiteten Sorten sind zudem Hybriden/Kultivare, die aus Samen nicht sortenecht nachkommen. Keine belastbaren, artspezifischen Keimwerte aus ≥2 seriösen Quellen auffindbar; keine Werte erfunden.) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | medium |
| Vegetatives Wachstum | 60–90 | 2 | false | false | high |
| Blüte | 30–60 | 3 | false | false | high |
| Nachblüte (Samen/Dekor) | 30–60 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–350 (Halbschatten bis Schatten; A. chinensis toleriert mehr Sonne als andere Arten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 (kritischer stomatärer Kollaps oberhalb des Zielkorridors; oberer Zielwert 1.0 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high (feuchteliebende Schattenstaude, schließt Stomata / verbrennt bei Trockenstress früh) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- DATEN FEHLEN --> (keine artspezifische Messung; kühlliebend, Hitzestress >25–28 °C, aber kein belegter T_opt-Wert aus 2 Quellen) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN --> (kein belegter phasenspezifischer Messwert; offenes Tageslicht ≈ 0.5, unter Schattendach höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 5.5–6.5 | 80 | 40 | – | 2 |
| Vegetativ | 2:1:2 | 1.0–1.4 | 5.5–6.5 | 100 | 50 | – | 2 |
| Blüte | 1:2:2 | 1.0–1.4 | 5.5–6.5 | 100 | 50 | – | 2 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo):** <!-- DATEN FEHLEN --> — keine artspezifischen Sufficiency-Werte (ppm) für Astilbe aus mind. 2 seriösen Quellen (Extension/Tissue-Standards) belegbar. Felder `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm` bleiben unbelegt. Praxis-Hinweis (nicht ins KA-Feld): leicht saurer Boden-pH (5,5–6,5) sichert die Mn-/Fe-Verfügbarkeit; bei pH >6,5 droht Mikronährstoff-Festlegung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Rhododendron-/Moorbeeterde | diverse | Substrat | Erde mit pH 5,5 | bei Pflanzung | Astilbe (sauer) |
| Kompost (leicht angesäuert) | eigen | organisch | 2–3 L/m² | März, Oktober | Bodenverbesserung |
| Hornmehl | Oscorna | organisch | 30–50 g/m² | April | medium_feeder |
| Flüssig-Langzeitdünger | Substral Osmocote | slow_release | 30 g/m² | April | Topfkultur |

### 3.2 Besondere Hinweise zur Düngung

Astilbe braucht humusreiche, leicht saure Böden (pH 5,5–6,5). Auf normalen Gartenböden Kompost einarbeiten. Einmalige organische Düngung im Frühjahr ausreichend. Im Topf alle 3–4 Wochen leicht flüssig düngen. Astilbe chinensis ist genügsamer als A. arendsii — kommt mit weniger Feuchtigkeit und Nährstoffen aus.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser oder leicht kalkarmes Wasser; gleichmäßige Feuchtigkeit; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 (alle 3 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Rückschnitt | Alte Stiele bodennah; Kompost einarbeiten | hoch |
| Apr | Düngung | Hornmehl + Kompost | mittel |
| Jul–Sep | Blüte | Blütenstände nicht abschneiden während Blüte | – |
| Okt | Blütenstände stehen lassen | Winterdekor; Vogel-Nahrung | niedrig |
| Alle 3–5 J. | Teilung | Im Frühjahr; jedes Teilstück mit mehreren Trieben | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

Astilbe chinensis ist sehr robust und fast schädlingsfrei.

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Dickmaulrüssler | Otiorhynchus sulcatus | Buchtige Blattrandfraßstellen | leaf | vegetative | medium |
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | spring | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 7–10 | vegetative (Spätsommer) |
| Rhizomfäule | fungal (Phytophthora) | Welken; braune Rhizome | Staunässe | 14–21 | alle |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit | Hinweis |
|----------|--------------------|----------------|--------------|------------------|---------|
| Insektenpathogene Nematoden (entomopathogenic nematodes) | Heterorhabditis bacteriophora | Dickmaulrüssler-Larven (Otiorhynchus sulcatus) | ~500.000 Nematoden/m² (500 Mio./1.000 m²) | Larvenabsterben innerhalb weniger Tage (~1 Woche) | Nur auf feuchtem Boden, min. Bodentemperatur 12 °C; Frühjahr/Spätsommer gegen Larvenstadium |

**Hinweis:** Bei Topfkultur als Gießanwendung in feuchtes, gut drainierendes Substrat ausbringen. Heterorhabditis ist auf Bodentemperaturen >12 °C angewiesen — Anwendung daher nicht im Hochwinter. Gegen adulte Käfer (Buchtenfraß am Blattrand) wirken die Nematoden nicht; sie zielen auf das wurzelfressende Larvenstadium.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Farn | Dryopteris filix-mas | 0.9 | Gleicher Schattenstandort | `compatible_with` |
| Funkie | Hosta spp. | 0.9 | Gleiche Standortansprüche; ergänzende Texturen | `compatible_with` |
| Rhododendron | Rhododendron spp. | 0.8 | Gleiche saure Bedingungen | `compatible_with` |
| Waldgeißbart | Aruncus dioicus | 0.7 | Gleiche Feuchtestandorte | `compatible_with` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Astilbe chinensis,"Chinesische Prachtspiere;Astilbe;Chinese Astilbe",Saxifragaceae,Astilbe,perennial,long_day,herb,rhizomatous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"China, Korea",yes,15,25,120,80,50,no,yes,false,false,medium_feeder,false,hardy,"7;8;9"
```

---

## Quellenverzeichnis

1. [Naturadb Astilbe chinensis](https://www.naturadb.de/pflanzen/astilbe-chinensis/) — Steckbrief
2. [Lubera Prachtspiere](https://www.lubera.com/de/gartenbuch/prachtspiere-astilbe-schneiden-pflege-standort-p3179) — Schnitt, Pflege
3. [Floragard Astilbe chinensis](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/stauden/astilbe-chinensis) — Kulturdaten
4. [Gartenjournal Prachtspiere](https://www.gartenjournal.net/prachtspiere) — Pflanzung, Standort
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — Astilbe chinensis (Chinese astilbe)](https://www.rhs.org.uk/plants/1825/astilbe-chinensis/details) — Standort (partial shade), Bodenfeuchte, pH-Adaptabilität, Höhe, Hardiness H7 (< -20 °C), drought-intolerant
6. [Missouri Botanical Garden — Astilbe chinensis 'Visions'](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=h400) — Part shade to full shade, rhizomatöses Wurzelsystem, Teilung alle 3–4 J., bessere Sonnen-/Trockenheitstoleranz als arendsii
7. [MSU Floriculture — Life after cold! (Vernalization part 4)](https://www.canr.msu.edu/resources/vernalization-part-4) — Astilbe chinensis 'Pumila': Dormanz bei 9-h-Kurztag, fakultativer Langtag, Kältebedarf zur Blüteneinleitung
8. [Greenhouse Product News — Perennial Solutions: Astilbe](https://gpnmag.com/article/perennial-solutions-astilbe-younique-series/) — Obligater Kältebedarf min. 10 Wochen < 40 °F (~4 °C), Forcing 10–12 Wochen, long-day-beneficial
9. [Almanac — Planting and Growing Astilbes](https://www.almanac.com/plant/astilbe) — feuchter, gut drainierender Boden (kein Staunässe-Dauerzustand), Pflanztiefe Krone, cool-season-Verhalten
10. [Koppert — Correct application crucial for effective vine weevil control](https://www.koppert.com/news/correct-application-crucial-for-effective-vine-weevil-control/) — Heterorhabditis bacteriophora gegen Otiorhynchus sulcatus, min. Bodentemperatur 12 °C
11. [Green Gardener — When to use nematodes for vine weevil](https://www.greengardener.co.uk/help-and-advice/when-to-use-nematodes-for-slugs-vine-weevil-leatherjackets-and-chafer-grubs/) — Heterorhabditis-Ausbringrate ~500.000/m², Anwendungsfenster
12. [Pondering Petals — Astilbe Soil pH](https://ponderingpetals.com/astilbe/soil-ph-management/) & [GardenerBible — Do Astilbe Like Acidic Soil?](https://gardenerbible.com/do-astilbe-like-acidic-soil/) — leicht saurer pH-Vorzug (high 5s–low 6s), Mikronährstoff-Verfügbarkeit
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
