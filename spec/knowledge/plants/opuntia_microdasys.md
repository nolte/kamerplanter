# Hasenohren-Kaktus, Bunny Ears — Opuntia microdasys

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/opuntia-microdasys-bunny-ears), [NC State Extension](https://plants.ces.ncsu.edu/plants/opuntia-microdasys/), [Epic Gardening](https://www.epicgardening.com/opuntia-microdasys/), [Plant Care Today](https://plantcaretoday.com/opuntia-microdasys.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Opuntia microdasys | `species.scientific_name` |
| Synonyme | Opuntia microdasys var. albispina (weißhöckrige Variante) | — |
| Volksnamen (DE/EN) | Hasenohren-Kaktus, Bunny Ears, Polka-Dot-Kaktus; Bunny Ears Cactus, Angel Wings, Polka Dot Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Opuntia | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 15–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurztag-/Langtag-Blüher — daher kein numerischer Stunden-Schwellenwert; Tagneutralität ist in `lifecycle_configs.photoperiod_type` = day_neutral hinterlegt --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht für Mitteleuropäische Freiland. Im Topf bei 7–13°C überwintern — kühle Winterruhe für optimale Gesundheit. | `species.hardiness_detail` |
| Heimat | Nordmexiko — trockene Hochplateaus, Chihuahua-Wüste | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Hasenohren-Kaktus ist einer der beliebtesten Feigenkakteen für die Zimmerpflanzenpflege. Die runden, abgeflachten Kaktuspaddes haben statt langer Stacheln kleine Büschel aus winzigen Widerhaken (Glochiden). ACHTUNG: Diese Glochiden sind besonders tückisch — sie sind mikroskopisch klein, brechen leicht ab und verursachen extremen Juckreiz in Haut und Augen. Die Pflanze IMMER mit Handschuhen anfassen. Im Sommer können gelbe Blüten erscheinen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (gelbe Blüten bei älteren Pflanzen und genügend Sonne) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Kaktuspadde mit Pinzette (niemals mit bloßen Händen!) abbrechen, 1–2 Wochen trocknen lassen (Wundverschluss), dann in Kakteenerde stecken. Bewurzelung in 3–6 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Glochiden = winzige Widerhaken verursachen extremen Juckreiz/Verletzungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Sicherheitshinweis:** GLOCHIDEN SIND GEFÄHRLICH — die winzigen Widerhaken können sich in Haut, Augen und Schleimhäute bohren und sind sehr schwer zu entfernen. Immer mit dicken Lederhandschuhen anfassen. Kinder und Haustiere fernhalten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde oder Einheitserde + 50% Sand/Perlite. pH 6.0–7.5. Sehr gute Drainage essentiell. Terrakotta-Töpfe bevorzugt (bessere Feuchtigkeitsregulation). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Kompensationspunkt (Netto-Photosynthese = 0) für O. microdasys bzw. CAM-Kakteen in seriösen Quellen belegt; verfügbare Quellen nennen nur Sättigungs-/Optimum-PPFD --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Schwellenwert für O. microdasys belegt; FAO-Salztoleranztabellen führen Opuntia nicht, artspezifische Schwelle nicht ableitbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope für O. microdasys belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweis:** Sonnenliebende Wüstenart aus offenen, vollbesonnten Standorten (volle Sonne ≥ 6 h/Tag). Flachwurzler mit Hauptwurzelmasse in den oberen ~15 cm; gelegentliche Pfahlwurzel reicht tiefer, in Topfkultur sind 15–30 cm effektive Durchwurzelungstiefe maßgeblich. Sehr staunässeempfindlich (waterlogging-sensitiv) — Fäule ist die häufigste Verlustursache. Salztoleranz-Klasse moderately_sensitive aus Gattungs-/Verwandtschaftsdaten (Opuntia gilt als Glykophyt; Cladoden-Wachstum bereits bei moderater NaCl-Belastung reduziert); numerische Maas-Hoffman-Kennwerte (ECe-Schwelle, Slope) bleiben mangels artspezifischer Quellen offen. Boden-pH-Vorzug quellentreu 6.0–7.5, harmonisiert mit §1.6 und §2.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum/Blüte (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 10–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–3.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 3.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 7–13 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 10–15 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 42–60 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:7:7 | 0.4–0.8 | 6.0–7.5 | 50 | 20 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Mangan, Zink, Kupfer und Molybdän zählen zu den essentiellen Spurenelementen für Kakteen und sind in handelsüblichen Kakteen-/Sukkulentendüngern (z. B. Wuxal Kaktus, Compo Kaktus) in chelatierter/sulfatierter Form enthalten. Artspezifische Sollkonzentrationen in ppm sind für Opuntia microdasys in seriösen Quellen nicht belegt — daher als `<!-- DATEN FEHLEN -->` markiert; eine separate Mikronährstoff-Düngung ist bei Verwendung eines vollwertigen Kakteendüngers in der Regel nicht erforderlich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen-Flüssigdünger | Compo | base | 5-3-8 | 3 ml/L (monatlich) | Wachstum |
| Sukkulenten-Dünger | Substral | base | 3-8-10 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kakteenerde mit Mineralanteil | Fertigsubstrat | organisch-mineralisch | 100% | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis August. September bis März kein Dünger. Kakteendünger mit erhöhtem Kalium- und Phosphatanteil bevorzugen — stickstoffreiche Dünger führen zu weichem, schlaff wirkendem Wuchs.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat VOLLSTÄNDIG austrocknen zwischen Güssen; im Winter fast kein Wasser (alle 6–8 Wochen) — Überwässerung ist häufigste Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 7 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Pseudococcus spp. | Weiße Wollflocken | easy |
| Schildlaus | Coccus spp. | Braune Schilder am Padde | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzel-/Stängelfäule | fungal | Braune weiche Stellen | Staunässe |
| Sonnenbrand | physiologisch | Braune Verfärbungen | Direktes Sonnenlicht nach Dunkelphase |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Alkohol 70% | mechanical | Wattestäbchen mit Pinzette | 0 | Schildläuse, Wollläuse |
| Weniger gießen | cultural | Substrat komplett austrocknen | 0 | Fäule (Prävention) |
| Langsame Eingewöhnung | cultural | Schritt für Schritt an Sonne gewöhnen | 0 | Sonnenbrand |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Wollläuse (Pseudococcus spp., Schmierläuse) | ~1 Käfer/m² (Befallsherd: lokal höher) | 2–4 Wochen |
| Schlupfwespe (parasitic wasp) | Leptomastix dactylopii | Citrus-/Wollläuse (Pseudococcus spp.) | ~2–5 Tiere/m² | 2–4 Wochen |
| Zehrwespe (parasitic wasp) | Metaphycus helvolus | Weichschildläuse (Coccidae, z. B. Coccus spp.) | ~2–5 Tiere/m² | 3–5 Wochen |

**Hinweis:** Nützlingseinsatz nur im warmen Innenraum/Gewächshaus sinnvoll (Aktivität ab ~20 °C). `Cryptolaemus montrouzieri` und `Leptomastix dactylopii` zielen auf die in §5.1 gelisteten Woll-/Schmierläuse (Pseudococcus); `Metaphycus helvolus` auf Weichschildläuse der Familie Coccidae (z. B. `Coccus` spp.). Für Panzer-/Deckelschildläuse (Diaspididae) wären stattdessen `Aphytis`-Arten zuständig — diese sind hier nicht gelistet, da die nachgewiesenen Schädlinge zu den Schmier- und Weichschildläusen gehören. Aufgrund der dichten, wachsigen Glochiden-Areolen ist die Zugänglichkeit für Nützlinge eingeschränkt; mechanische Bekämpfung (§5.3) bleibt erste Wahl.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze/Kübelpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Feigenkaktus | Opuntia ficus-indica | Gleiche Gattung | Größer, essbare Früchte |
| Gymnocalycium | Gymnocalycium mihanovichii | Cactaceae, Zimmerkaktus | Stachellos, kompakt |
| Echinopsis | Echinopsis oxygona | Cactaceae | Schöne große Blüten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Opuntia microdasys,"Hasenohren-Kaktus;Bunny Ears;Polka-Dot-Kaktus;Bunny Ears Cactus;Angel Wings",Cactaceae,Opuntia,perennial,day_neutral,shrub,fibrous,"9a;9b;10a;10b;11a;11b","Nordmexiko (Chihuahua-Wüste)",yes,3-15,15,40-90,60-150,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Opuntia microdasys](https://www.gardenia.net/plant/opuntia-microdasys-bunny-ears) — Botanische Daten
2. [NC State Extension — Opuntia microdasys](https://plants.ces.ncsu.edu/plants/opuntia-microdasys/) — Kulturdaten
3. [Epic Gardening — Opuntia microdasys](https://www.epicgardening.com/opuntia-microdasys/) — Pflegehinweise
4. [Plant Care Today — Opuntia microdasys](https://plantcaretoday.com/opuntia-microdasys.html) — Schädlinge, Glochiden-Warnung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig — Glochiden mechanisch gefährlich)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [dryGrow Foundation — Carbon Capturing Mechanisms in Opuntia](https://www.drygrow.org/carbon-capturing-mechanisms-in-opuntia/) — Photosynthese-Typ CAM (Crassulacean Acid Metabolism)
7. [Annals of Botany / Oxford Academic — Developmental dynamics of CAM in Opuntia ficus-indica](https://academic.oup.com/aob/article/132/4/869/7187259) — CAM-Bestätigung Gattung Opuntia (peer-reviewed)
8. [Springer / Plant and Soil — Salt tolerance of prickly pear cactus (Opuntia ficus-indica), Nerd & Karadi](https://link.springer.com/article/10.1007/BF00011198) — Salztoleranz-Klasse (Cladoden-Wachstum salzempfindlich, Glykophyt)
9. [USDA/ARS AgResearch Magazine — Using Cactus as a Bioremediation Tool](https://agresearchmag.ars.usda.gov/2012/jan/cactus) — Salztoleranz Opuntia genotypabhängig, generell empfindlich
10. [FAO — Annex 1. Crop salt tolerance data](https://www.fao.org/4/y4263e/y4263e0e.htm) — Beleg, dass Opuntia NICHT in den Maas-Hoffman-Salztoleranztabellen geführt wird (ECe/Slope nicht ableitbar)
11. [ScienceDirect — Root distribution of Opuntia ficus-indica and O. robusta](https://www.sciencedirect.com/science/article/pii/S0254629906000330) — Flachwurzler, Hauptwurzelmasse in oberen ~15 cm
12. [Lady Bird Johnson Wildflower Center (NPIN) — Root depth of Opuntia](https://www.wildflower.org/expert/show.php?id=1222) — Wurzeltiefe, Pfahlwurzel
13. [NC State Extension — Opuntia microdasys](https://plants.ces.ncsu.edu/plants/opuntia-microdasys/) — Boden-pH-Vorzug, Vollsonne
14. [Wiley / Functional Ecology — Drennan & Nobel: Root growth dependence on soil temperature for Opuntia ficus-indica](https://besjournals.onlinelibrary.wiley.com/doi/10.1046/j.1365-2435.1998.00276.x) — Temperaturoptima (Tag/Nacht 25/15 °C optimal), Wuchsschwelle ~10 °C
15. [Wiley / New Phytologist — Nobel: Temperature tolerances of Opuntia ficus-indica cladodes/roots](https://nph.onlinelibrary.wiley.com/doi/full/10.1046/j.1469-8137.2003.00675.x) — Wuchs-Schwellentemperatur / GDD-Basis ~10 °C
16. [Oxford Academic / Plant Physiology — Stomatal Biology of CAM Plants](https://academic.oup.com/plphys/article/174/2/550/6117326) — VPD-Sensitivität low (nächtliche Stomata-Öffnung, hohe Wassereffizienz)
17. [Michigan State University Extension — The R to FR Ratio](https://www.canr.msu.edu/uploads/resources/pdfs/rfrratio.pdf) — Tageslicht/Vollsonne R:FR ≈ 1.1–1.3 → Far-Red-Fraction ≈ 0.5
18. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Nützling gegen Wollläuse, Ausbringrate
19. [ScienceDirect Topics — Cryptolaemus montrouzieri overview](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/cryptolaemus-montrouzieri) — Ausbringrate ~1 Käfer/m², Kombination mit Leptomastix dactylopii
20. [The Cactus Expert — Fertilizer / Cultivation of Cacti](https://www.cactusexpert.org/cultivation-of-cacti/fertilizer.html) — Mikronährstoffe (Mn/Zn/Cu/Mo) als Spurenelemente für Kakteen
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
