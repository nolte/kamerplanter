# Paradiesvogelblume — Strelitzia reginae

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [PLNTS.com](https://plnts.com/en/care/houseplants-family/strelitzia), [Garden Pals](https://gardenpals.com/bird-of-paradise/), [The Sill](https://www.thesill.com/blog/how-to-care-for-bird-of-paradise), [Greenery Unlimited](https://greeneryunlimited.co/blogs/plant-care/bird-of-paradise-care), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Strelitzia reginae | `species.scientific_name` |
| Volksnamen (DE/EN) | Paradiesvogelblume, Königin-Strelitzie; Bird of Paradise, Crane Flower | `species.common_names` |
| Familie | Strelitziaceae | `species.family` → `botanical_families.name` |
| Gattung | Strelitzia | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 30–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurz-/Langtagblüher → kein numerischer Stunden-Schwellwert; Blüte stress-/lichtinduziert, nicht photoperiodisch --> | `lifecycle_configs.critical_day_length_hours` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — toleriert kurze Fröste bis -3°C. Mindesttemperatur 8°C, optimal 18–29°C. Kühle Winter (12–18°C) fördert Blütenbildung. | `species.hardiness_detail` |
| Heimat | Südafrika (Ostkap, KwaZulu-Natal) — trockene Buschsavanne | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Strelitzia reginae blüht in Zimmerkultur nur bei ausreichend Licht UND einem kühlen Winter. Pflanzen brauchen 3–5 Jahre bis zur ersten Blüte. Schlüsselfaktoren für Blüte: maximales Tageslicht (mindestens 6h direkte Sonne), Sommer draußen, kühlerer Winterstandort (12–18°C) und beengte Wurzeln (nicht zu groß umtopfen). Häufigster Fehler: zu dunkel oder zu warm in Winter.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 2, 3, 4, 5, 9, 10 (Orange-blaue Blüten; bei guten Bedingungen fast ganzjährig) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen — Pflanzebüschel sorgfältig trennen, dabei die Wurzeln möglichst erhalten. Samen: frisch bei 22–26°C, Keimung in 1–6 Monate, sehr variabel. Geteilte Pflanzen brauchen oft 2–3 Jahre bis zur erneuten Blüte.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | flowers, seeds (Blätter und Stängel weniger toxisch) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | hydrocyanic_acid (in Samen), tannins | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4, 10 (verblühte Blütenstiele und abgestorbene Blätter entfernen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–25 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Mai–Oktober im Freien, volle Sonne — stark blütenfördernd) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, gut durchlässige Einheitserde mit 20% Perlite. pH 5.5–7.5. Gute Drainage wichtig (fleischige Wurzeln anfällig für Staunässe). Töpfe nicht zu groß (beengter Wurzelraum fördert Blüte). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: keine artspezifische peer-reviewte LCP-Messung für Strelitzia reginae auffindbar; als sonnen-/halbschattenliebende C3-Breitblattart läge er im Bereich heliophiler Arten, aber ohne belegten Wert nicht eingetragen --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–60 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: keine quantitative Maas-Hoffman-ECe-Schwelle (Substrat-ECe) für die Art belegt; Quellen nennen nur qualitativ "moderate salt tolerance" --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–7.5 | `species.soil_ph_preference` |

**Hinweis:** Sonnenliebend (heliophil) — natürliche Standorte an Flussufern in voller Sonne, randständig auch im lichten Schatten (Quelle: SANBI/PlantZAfrica). Volle Sonne fördert die Blüte, Halbschatten ergibt größere Blüten an längeren Stielen. Fleischige, fingerartige Wurzeln (≈25 mm Durchmesser) bilden einen kompakten Ballen; bodengewachsene Pflanzen wurzeln bis ≈60 cm tief, dehnen sich aber wenig in Breite/Tiefe aus. Staunässe ist kritisch (Wurzelfäule). Salztoleranz: mäßig salzverträglich (moderate Salzwasser-/Salzwind-Toleranz, Küstendickicht-Herkunft); geschützte Lage mit Windschutz empfohlen — die pH-Spanne ist mit §1.6/§2.3 (5.5–7.5) harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (kühle Ruhephase — blüteninduzierend) | 90–120 | 2 | false | false | medium |
| Blütezeit | 60–90 | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (April–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1200+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–50 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.7–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe / Blüteninduktion (Oktober–März)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 10–25 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 12–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 5.5–7.5 | 100 | 40 | 0.5 | 0.05 | 0.03 | 0.05 |
| Winterruhe | 0:1:1 | 0.4–0.6 | 5.5–7.5 | 60 | 20 | 0.25 | 0.03 | 0.02 | 0.03 |
| Blütezeit | 1:3:2 | 0.8–1.2 | 5.5–7.5 | 80 | 35 | 0.5 | 0.05 | 0.03 | 0.05 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu Mikronährstoffen:** Die Mn/Zn/Cu/Mo-Werte (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`) folgen allgemeinen ausgewogenen Nährlösungs-Zielwerten (general-purpose / Hoagland-Niveau) für mittelzehrende Zierpflanzen; eine artspezifische Mikronährstoff-Messung für Strelitzia reginae ist nicht publiziert. In der Ruhephase entsprechend der reduzierten EC halbiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 2–3 Wochen) | Wachstum |
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 5 ml/L | Blütezeit |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | – | organisch | 30–50 g/Topf | Frühjahr |
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 2–3 Wochen März bis September. Im Winter monatlich oder gar nicht. Stickstoff während Wachstum, Phosphor für Blütenanregung. Im Winter kühler Standort + weniger Wasser wichtiger als Düngung für Blütenbildung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; gleichmäßig feucht halten — nicht staunass. Fleischige Wurzeln anfällig für Fäule. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (nur umtopfen wenn unbedingt nötig — beengte Wurzeln fördern Blüte) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profile.hardiness_rating` |
| Winter-Maßnahme + Monat | move_indoors (Monat 10) | `overwintering_profile.winter_action` |
| Frühjahrs-Maßnahme + Monat | move_outdoors (Monat 5, nach den Eisheiligen) | `overwintering_profile.spring_action` |
| Winterquartier-Temperatur (°C) | 8–15 (Minimum 8; kühl 12–15 fördert Blüteninduktion) | `overwintering_profile.winter_quarter_temp_c` |
| Winterquartier-Licht | hell — südseitiges Fenster oder Pflanzenlicht; kein Dunkellager | `overwintering_profile.winter_quarter_light` |
| Winterquartier-Gießen | sparsam, Substrat zwischen den Gaben antrocknen lassen (Gießintervall 14–21 Tage); Staunässe vermeiden | `overwintering_profile.winter_quarter_watering` |

**Hinweis:** Strelitzia reginae ist nicht winterhart in Mitteleuropa (USDA 6–8) und muss als Kübelpflanze frostfrei (frost_free) drinnen überwintern. Kurze Fröste bis −3 °C werden nur ausnahmsweise toleriert; Dauerfrost ist tödlich. Im Mai/Juni (nach den Eisheiligen) wieder ins Freie an einen vollsonnigen Standort. Ein heller, kühler Winterstandort (12–15 °C) bei reduziertem Gießen ist der wichtigste Blühauslöser.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, weiche Stängelbasis | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–6 / m² (Befallsherde) | 2–3 Wochen |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–5 / m² | 3–4 Wochen |
| Schlupfwespe | Metaphycus helvolus | Weiche/braune Schildlaus (Coccus hesperidum, Coccidae) | 5 / m² (3 Freilassungen im 14-Tage-Takt) | 3–4 Wochen |

**Hinweis:** Metaphycus helvolus parasitiert ausschließlich Weichschildläuse (Coccidae, hier Coccus hesperidum) — nicht Panzer-/Deckelschildläuse (Diaspididae, für die Aphytis-Arten zuständig wären). Nützlinge benötigen warme Bedingungen (Metaphycus: >22 °C über mehrere Stunden täglich, sonnig); für Indoor-/Wintergarten-Einsatz im Sommerhalbjahr geeignet.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze (kann Sommer im Freien verbringen).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Riesenstrelitzie | Strelitzia nicolai | Gleiche Gattung | Größer (bis 3 m), imposanteres Erscheinungsbild |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,photosynthesis_type,base_temp,growth_habit,root_type,shade_tolerance,waterlogging_tolerance,salt_tolerance_class,soil_ph_preference,effective_root_depth_cm,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Strelitzia reginae,"Paradiesvogelblume;Königin-Strelitzie;Bird of Paradise;Crane Flower",Strelitziaceae,Strelitzia,perennial,day_neutral,c3,10,herb,fibrous,partial_shade,sensitive,moderately_tolerant,5.5-7.5,30-60,"9a;9b;10a;10b;11a;11b","Südafrika (Ostkap, KwaZulu-Natal)",yes,10-25,30,100-200,80-150,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [PLNTS.com — Strelitzia](https://plnts.com/en/care/houseplants-family/strelitzia) — Ganzjahrespflege
2. [Garden Pals — Strelitzia reginae](https://gardenpals.com/bird-of-paradise/) — Kulturdaten
3. [The Sill — Bird of Paradise](https://www.thesill.com/blog/how-to-care-for-bird-of-paradise) — Pflegehinweise
4. [Greenery Unlimited — Bird of Paradise](https://greeneryunlimited.co/blogs/plant-care/bird-of-paradise-care) — Schädlinge, Gießen
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [SANBI / PlantZAfrica — Strelitzia reginae](https://pza.sanbi.org/strelitzia-reginae) — Naturhabitat (Küstendickicht, Flussufer in voller Sonne), Wurzelsystem (fleischig, fingerartig ≈25 mm), Blütezeit/stressinduzierte Blüte
7. [NC State Extension — Strelitzia reginae](https://plants.ces.ncsu.edu/plants/strelitzia-reginae/) — Sonne/Halbschatten, Boden-pH, Rhizom/Wuchsform
8. [Wikipedia — Strelitziaceae](https://en.wikipedia.org/wiki/Strelitziaceae) — taxonomische Stellung (Zingiberales, Verwandtschaft mit Musaceae/Bananen → C3-Einordnung)
9. [Backyard Gardener — Strelitzia reginae](https://www.backyardgardener.com/plantname/strelitzia-reginae-bird-of-paradise/) — Boden-pH 5.5–7.5, Salzverträglichkeit, Lichtexposition
10. [Gardening Know How — Bird of Paradise](https://www.gardeningknowhow.com/ornamental/flowers/bop/bird-of-paradise-an-exotic-flower-like-none-other.htm) — Mindesttemperatur (Wachstumsstopp unter ~10 °C), kurzfristige Frosttoleranz bis ≈−4.5 °C
11. [PestCentric / Dovebugs — Biological Control of Scale Insects](https://www.dovebugs.co.uk/BioControl%20ScaleInsect.pdf) — Metaphycus helvolus Wirtsspektrum (Weichschildläuse) & Ausbringrate (5/m², 3 Freilassungen)
12. [Wikipedia — Metaphycus helvolus](https://en.wikipedia.org/wiki/Metaphycus_helvolus) — Zielschädlinge (Coccidae), Temperaturansprüche
13. [Gardenia.net — Strelitzia reginae](https://www.gardenia.net/plant/strelitzia-reginae-bird-of-paradise) — moderate Salzwasser-/Salzwind-Toleranz, Standortansprüche
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
