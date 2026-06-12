# Zwergschefflera — Schefflera arboricola

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Bloomscape](https://bloomscape.com/plant-care-guide/schefflera/), [Almanac.com](https://www.almanac.com/plant/umbrella-plant-care-guide-schefflera), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/umbrella-plant-schefflera-arboricola-care-guide/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-a-schefflera), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Schefflera arboricola | `species.scientific_name` |
| Volksnamen (DE/EN) | Zwergschefflera, Strahlenaralie; Dwarf Umbrella Tree, Umbrella Plant | `species.common_names` |
| Familie | Araliaceae | `species.family` → `botanical_families.name` |
| Gattung | Schefflera | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein speziesspezifischer, belegter Wuchs-/Phänologie-GDD-Basiswert für die tropische Zimmerpflanze auffindbar (warmliebende Art, konventionell ~10 °C, jedoch nicht aus 2 Quellen belegt → nicht eingetragen, kein Keimwert umetikettiert) | `species.base_temp` |
| Kritische Tageslänge (h) | — (tagneutral, kein numerischer Schwellenwert; vgl. `photoperiod_type = day_neutral`) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 12°C, optimal 18–27°C. Toleriert kurze Abkühlungen auf 10°C. | `species.hardiness_detail` |
| Heimat | Taiwan und Hainan (Südchina) — tropische und subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Schefflera arboricola (Zwergform) und S. actinophylla (große Form, "Sonnenschirm-Pflanze") werden oft verwechselt. Beide sind als Zimmerpflanzen beliebt, aber arboricola bleibt kompakter (bis 2 m Indoor). Sehr tolerant gegenüber schwächerem Licht, was sie für dunklere Zimmerecken qualifiziert. Kann als Bonsai kultiviert werden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Halbholzige Stecklinge (8–12 cm) bei 22–26°C und hoher Luftfeuchtigkeit bewurzeln. Bewurzelung in 4–8 Wochen. Abmoosen (Luftabsenker) ist zuverlässiger für Stämme.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, berries | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides, saponins | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Saft — bei empfindlichen Personen Hautreizungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Verträgt starken Rückschnitt gut — treibt zuverlässig neu aus. Im Frühjahr auf gewünschte Form bringen. Regelmäßiges Pinzen der Triebspitzen fördert buschigen Wuchs.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–200 (Indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–120 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (frostfreie Monate, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Einheitserde mit 20% Perlite. pH 6.0–6.5. Gute Drainage wichtig. Tongefäße bevorzugt (verhindert Überwässerung). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | <!-- DATEN FEHLEN --> kein speziesspezifischer, belegter Wert aus 2 Quellen auffindbar (flachwurzelnd-faserig im Topf, aber keine zitierfähige Tiefenangabe) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, Maas-Hoffman a, dS/m) | <!-- DATEN FEHLEN --> keine speziesspezifischen Maas-Hoffman-Parameter publiziert (Salinitätsstudien belegen nur qualitative Empfindlichkeit) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN --> nicht publiziert | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Schefflera arboricola ist eine ausgesprochen schattentolerante (shade-tolerant) Art, die in ihrer Heimat über ein breites Strahlungsspektrum von Tiefschatten (deep shade) bis Vollsonne (full sun) vorkommt; im Innenraum wird sie als Tiefschatten-verträgliche Zimmerpflanze geführt. Der Lichtkompensationspunkt liegt entsprechend niedrig (schattenadaptierte Blätter ~5–20 µmol/m²/s; in Büro-/Innenraumstudien sicherten bereits ~6,8 µmol/m²/s/9 h dauerhaftes Wachstum). Lichtsättigung und Photoinhibition (bei plötzlichem Wechsel Tiefschatten→Starklicht) sind separate Phänomene und nicht in das LCP-Feld eingetragen. Salzempfindlich: regelmäßiges Durchspülen des Topfes alle 2–3 Monate gegen Salzanreicherung empfohlen; eine exakte ECe-Schwelle (Substrat-ECe, nicht Gießwasser-EC) ist für die Art nicht belegt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–350 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–6.5 | 100 | 40 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–6.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Die Mikronährstoff-Werte (Mn/Zn/Cu/Mo) für die Wachstumsphase entsprechen der Hoagland-Standard-Nährlösung (Hoagland & Arnon), dem etablierten Referenz-Baseline für Zier-/Blattpflanzen-Nährlösungen — sie sind nicht speziesspezifisch für Schefflera arboricola publiziert. KA-Felder: `nutrient_profiles.manganese_ppm` / `nutrient_profiles.zinc_ppm` / `nutrient_profiles.copper_ppm` / `nutrient_profiles.molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Hornmehl | – | organisch | 30–50 g/Topf | Frühjahr |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Stickstoffbetonte Formel für üppiges Blattwerk. Bei wenig Licht: Düngermenge auf 1/4 reduzieren.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; gleichmäßige Feuchtigkeit, keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 13–20 (Mindesttemperatur 12 °C; nicht unter 10 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirektes Licht (Nord-/Ostfenster); ggf. LED-Pflanzenlicht 12–14 h bei dunklem Standort | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert, alle 10–14 Tage; Substrat zwischen den Gaben antrocknen lassen, keine Staunässe | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Schefflera arboricola ist nicht frosthart (frost_free) und überwintert als Kübel-/Zimmerpflanze frostfrei im Innenraum — sie wird weder gemulcht noch eingegraben. Im Sommer ist ein halbschattiger Stand auf Balkon/Terrasse möglich; vor dem ersten Frost (Oktober) hereinholen, nach den Eisheiligen (Mitte Mai) langsam wieder nach draußen gewöhnen (abhärten). Zugluft und kalte Fensterscheiben im Winter meiden; Heizungsluft mit Anstaubrett/Untersetzer ausgleichen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |
| Blattlaus | Aphididae | Kolonien an Triebspitzen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, Blattverlust | Staunässe |
| Alternaria-Blattflecken | fungal | Braune Flecken | Nasses Laub, hohe Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Sprühen | 3 Tage | Blattläuse, Schildläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–4/m² (kurativ), Wdh. 2–3× im 14-Tage-Abstand | 2–3 Wochen |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–5/m² (bzw. 5–10 Käfer/Pflanze bei Befallsherden) | 3–4 Wochen |
| Schlupfwespe | Metaphycus helvolus | Weichschildläuse (Coccidae, z. B. Coccus hesperidum) | 5/m², 3 Freilassungen im 14-Tage-Abstand | 3–4 Wochen |
| Blattlaus-Schlupfwespe | Aphidius colemani | Blattläuse (Aphididae) | 0,25–4/m², mind. 3 Freilassungen wöchentlich | 2–3 Wochen |

**Hinweis:** Ausbringraten für geschützte Innenraum-/Gewächshauskultur (Temperatur 18–27 °C, rel. Luftfeuchte 40–60 %). Nützlinge nicht mit Neemöl oder Insektizidseife kombinieren (Wartezeit zwischen chemischer/biologischer Behandlung und Nützlingseinsatz einhalten). Metaphycus helvolus ist ausschließlich gegen Weichschildläuse (Coccidae) wirksam; gegen Panzer-/Deckelschildläuse (Diaspididae) wären stattdessen Aphytis-Arten einzusetzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Große Schefflera | Schefflera actinophylla | Gleiche Gattung | Eindrucksvolleres Erscheinungsbild |
| Fatsia | Fatsia japonica | Gleiche Familie | Frostharder, für kühlere Räume |
| Monstera | Monstera deliciosa | Großblättrig, tropisch | Spektakulärer, ähnlich pflegeleicht |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Schefflera arboricola,"Zwergschefflera;Strahlenaralie;Dwarf Umbrella Tree;Umbrella Plant",Araliaceae,Schefflera,perennial,day_neutral,shrub,fibrous,"9b;10a;10b;11a;11b","Taiwan, Hainan (Südchina)",yes,5-20,25,80-200,60-120,yes,yes,false,medium_feeder,0.6
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Gold Capella,Schefflera arboricola,"ornamental;variegated;yellow_green",clone
Trinette,Schefflera arboricola,"ornamental;variegated;cream_green",clone
Renate,Schefflera arboricola,"ornamental;compact;dark_green",clone
```

---

## Quellenverzeichnis

1. [Bloomscape — Schefflera Care](https://bloomscape.com/plant-care-guide/schefflera/) — Pflegehinweise
2. [Almanac.com — Umbrella Plant](https://www.almanac.com/plant/umbrella-plant-care-guide-schefflera) — Kulturdaten
3. [Healthy Houseplants — Schefflera arboricola](https://www.healthyhouseplants.com/indoor-houseplants/umbrella-plant-schefflera-arboricola-care-guide/) — Schädlinge, Krankheiten
4. [The Sill — Schefflera](https://www.thesill.com/blogs/plants-101/how-to-care-for-a-schefflera) — Gießen, Licht
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [ScienceDirect Topics — Schefflera arboricola](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/schefflera-arboricola) — Tiefschatten-/Vollsonne-Toleranz, niedrige max. Photosynthesekapazität, Lichtsammelverhalten (Schattentoleranz, LCP-Einordnung)
7. [Adaptation of indoor ornamental plants to various lighting levels — Scientific Reports (Nature) 2024](https://www.nature.com/articles/s41598-024-67877-y) — Lichtkompensationspunkt schattentoleranter Zierpflanzen; ~6,8 µmol/m²/s/9 h sichert Wachstum (LCP-Spanne)
8. [Plantly — Schefflera arboricola Plant Care](https://plantly.io/plant-care/schefflera-arboricola/) — Boden-pH 6,0–6,5, Staunässe-Empfindlichkeit/Wurzelfäule
9. [Healthy Houseplants — Umbrella Plant Care Guide (Salz-/Flushing-Hinweis)](https://www.healthyhouseplants.com/indoor-houseplants/umbrella-plant-schefflera-arboricola-care-guide/) — Salzanreicherung, Durchspülen alle 2–3 Monate (Salzempfindlichkeit)
10. [ResearchGate — Response of Schefflera arboricola to gypsum/sulphur under saline water (Mazhar et al.)](https://www.researchgate.net/publication/281700022_Response_of_Schefflera_Arboricola_L_to_gypsum_and_sulphur_application_irrigated_with_different_levels_of_saline_water) — signifikante Wachstumsminderung unter Salzwasser (Salzklasse sensitive)
11. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Baseline Mn 0,5 / Zn 0,05 / Cu 0,02 / Mo 0,01 ppm
12. [MSU Extension — Secondary and Micronutrients for Vegetable and Field Crops (E486)](https://www.canr.msu.edu/resources/secondary_and_micro_nutrients_for_vegetable_and_field_crops_e486) — Mikronährstoff-Bezugswerte (Mn/Zn/Cu/Mo)
13. [Warming puts the squeeze on photosynthesis — lessons from tropical trees (J. Exp. Bot. 2017)](https://academic.oup.com/jxb/article/68/9/2073/3858317) — Photosynthese-T_opt tropischer Bäume 23–32 °C, Mittel ~30 °C (T_opt)
14. [Seasonal variation in the red/far-red ratio in a sub-tropical rainforest (Agric. For. Meteorol.)](https://sciencedirect.com/science/article/pii/016819239390096Z) — R:FR in Sonne/Schatten, FR-Anreicherung im Unterwuchs (Far-Red-Fraction-Anker)
15. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Raubmilbe gegen Spinnmilben, Ausbringung/Etablierung
16. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Australischer Marienkäfer gegen Schmierläuse, Ausbringrate
17. [Wikipedia — Metaphycus helvolus](https://en.wikipedia.org/wiki/Metaphycus_helvolus) — Schlupfwespe gegen Weichschildläuse (Coccus hesperidum), 5/m² × 3 Freilassungen
18. [Koppert — Encarsia formosa / Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Blattlaus-Schlupfwespe, Ausbringrate 0,25–4/m²
19. [University of Connecticut IPM — Aphidius colemani / Whitefly Biological Control](https://ipm.cahnr.uconn.edu/ipm-biological-control-of-whiteflies/) — Nützling-Wirt-Zuordnung, Freilassungsfrequenz
20. [Clemson HGIC — Schefflera factsheet](https://hgic.clemson.edu/factsheet/schefflera-2/) — Mindesttemperatur, Überwinterung (frost_free), Innenraumkultur
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
