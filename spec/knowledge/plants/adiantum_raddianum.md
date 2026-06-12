# Frauenhaarfarn — Adiantum raddianum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/adiantum-raddianum/), [Gardeners World](https://www.gardenersworld.com/house-plants/how-to-grow-maidenhair-fern-adiantum-raddianum/), [Guide to Houseplants](https://www.guide-to-houseplants.com/maidenhair-fern.html), [Plant Care Today](https://plantcaretoday.com/maidenhair-fern.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Adiantum raddianum | `species.scientific_name` |
| Volksnamen (DE/EN) | Frauenhaarfarn, Delta-Frauenhaarfarn; Maidenhair Fern, Delta Maidenhair Fern | `species.common_names` |
| Familie | Pteridaceae | `species.family` → `botanical_families.name` |
| Gattung | Adiantum | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Photosynthese-Typ | c3 | `species.photosynthesis_type` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Kritische Tageslänge (h) | — (tagneutral/day_neutral — kein Kurztag-/Langtagbluher; Wedelbildung lichtmengen-, nicht tageslängengesteuert) | `lifecycle_configs.critical_day_length_hours` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> (kein etabliertes GDD-Modell fuer tropische Zierfarne; kein quellengestuetzter Basiswert) | `species.base_temp` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–24°C. Zieht bei Kälte ein und kann sich erholen. | `species.hardiness_detail` |
| Heimat | Tropisches und subtropisches Amerika (Brasilien, Andes) — feuchte Wälder, felsige Bachufer | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Frauenhaarfarn ist einer der anspruchsvollsten Zimmerfarne — er reagiert äußerst empfindlich auf Lufttrockenheit, direkte Zugluft und unregelmäßiges Gießen. Wilkt der Farn ein, kann er sich bei sofortiger Bewässerung und erhöhter Luftfeuchtigkeit noch erholen — aber ist stark gestresst. Das schwarze, drahtartige Stängel-System (Adiantum = "nicht benetzt") ist charakteristisch: Wasser perlt ab. Ideal für Badezimmer oder auf feuchten Kieselsteinen. Als Sterbenmuster gilt: braune, trockene Wedel = zu trocken oder zu warm.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farn — keine Blüten, Sporenbildung April–Oktober) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, spore | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen im Frühjahr — Rhizom mit mehreren Wedeln abtrennen, in feuchtes Substrat pflanzen. Sporenvermehrung möglich aber langwierig (mehrere Monate). Teilung ist die praktikabelste Methode.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Sporen können bei empfindlichen Personen reagieren) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (alle abgestorbenen Wedel entfernen, fördert Neuaustrieb) | `species.pruning_months` |

**Hinweis:** Bei stark ausgetrockneten Pflanzen alle Wedel bis zur Erdbasis abschneiden und feucht halten — oft erholt sich die Pflanze vollständig.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–45 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, windgeschützt, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut durchlässige aber feuchtigkeitshaltende Erde. pH 6.0–7.0. Torffreier Anzuchtmix mit Perlite, Kokosfaser und Lauberde. Nie austrocknen lassen. | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (PPFD µmol/m²/s) | 5–20 | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> (kein quellengestuetzter Maas-Hoffman-Schwellwert fuer Adiantum; Substrat-ECe-Bezug, nicht Gießwasser) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> (kein quellengestuetzter Maas-Hoffman-Slope publiziert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Der Frauenhaarfarn ist ein Waldboden-Unterwuchsfarn (understory fern) und damit ausgesprochen schattenadaptiert (shade-adapted) — der Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) liegt im niedrigen Bereich schattentoleranter Krautpflanzen. Echte Filmfarne erreichen ~1.5–5 µmol/m²/s; für den weniger extrem schattenliebenden Adiantum ist eine Spanne von 5–20 µmol/m²/s plausibel. **Davon klar zu trennen:** Lichtsättigung (light saturation) und Photoinhibition liegen weit höher — die Photosynthese sättigt bereits bei ca. 200–300 µmol/m²/s, oberhalb ~600 µmol/m²/s droht Photoinhibition (diese Werte gehören NICHT in das Kompensationspunkt-Feld). RHS klassifiziert die Art als Halbschatten (partial shade, Ost/Nord/West), nicht als Tiefschatten oder Vollsonne. Die Salzempfindlichkeit ist hoch: Chlorid-, Fluorid- und allgemeine Salzanreicherung im Substrat führen rasch zu Blattspitzennekrosen (tip burn) — weiches, kalkarmes Wasser ist Pflicht. Das flach kriechende Rhizom (rhizome) wurzelt nur oberflächennah (vgl. Mindest-Topftiefe 12 cm in §1.6).

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–180 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Schwelle (kPa) | 0.9 | `requirement_profiles.vpd_threshold_kpa` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` <!-- Quelle: Steckbrief-Erweiterung 2026-06 --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 50 | 20 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu Mikronährstoffen (Mn/Zn/Cu/Mo):** Für *Adiantum raddianum* liegen keine artspezifischen, quellengestützten Mikronährstoff-Sollkonzentrationen (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`) vor; allgemeine Nährlösungs-Richtwerte (z.B. Hoagland) sind nicht artspezifisch und werden daher hier nicht als belegte Werte eingetragen. Als sehr leichter Zehrer (light feeder) ist der Bedarf gering — ein vollständiger Spurenelement-Mix in halber Dosierung deckt ihn im Wachstum ab. Mikronährstoff-Felder bleiben bis zu einer belegbaren Quelle als `<!-- DATEN FEHLEN -->` markiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich, halbe Dosis) | Wachstum |
| Farn- und Zimmerpflanzendünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Komposttee | Eigenherstellung | organisch | 1× monatlich gießen | Wachstum |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Nur monatlich düngen, niemals in der Winterruhe. Immer halbe Empfehlungsdosis. Überdüngung und Salze im Substrat schädigen die feinen Wurzeln und führen zu Blattbräunung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser (Regenwasser ideal). Nie austrocknen lassen, aber keine Staunässe. Erhöhte Luftfeuchtigkeit ist wichtiger als häufiges Gießen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (September, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier — Temperatur (°C) | 15–20 (Minimum 12, niemals unter 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier — Licht | Hell, indirekt (Ost-/Nord-/Westfenster); kein direktes Sonnenlicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier — Gießen | Reduziert, aber nie ganz austrocknen; Substrat zwischen den Gaben leicht abtrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** *Adiantum raddianum* ist nicht winterhart (USDA 10–11) und in Mitteleuropa (USDA 6–8) ausschließlich als frostfrei drinnen überwinternde Kübel-/Zimmerpflanze zu führen — daher `frost_free` (nicht `dig_and_store`: es gibt keine einzulagernden Knollen). RHS-Einstufung H1c: nur im Sommer ins Freie, ganzjährig „unter Glas" bzw. im warmen Raum. Im Winter Düngung einstellen, Gießen reduzieren und vor Heizungsluft, Zugluft und plötzlichen Temperaturschwankungen schützen — diese sind der häufigste Grund für Wedelbräune. Unter ~10–13 °C beginnt die Pflanze, Wedel abzuwerfen.

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Blätter vergilben, Gespinste (bei Trockenheit) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |
| Blatttrockenheit | physiologisch | Braune, knusprige Wedel | Zu wenig Luftfeuchtigkeit, Zugluft |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Luftbefeuchter, Kieselsteinschale | 0 | Spinnmilbe, Blatttrockenheit (Prävention) |
| Neemöl | biological | Sprühen 0.3% (verdünnt) | 0 Tage | Spinnmilbe, Schmierläuse |
| Giesshygiene | cultural | Staunässe vermeiden | 0 | Wurzelfäule (Prävention) |

### 5.4 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 / m² (wöchentlich 1–2× wiederholen) | ~1–2 Wochen |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 5–40 / m² (alle 1–2 Wochen, mind. 3×) | ~2–4 Wochen |
| Nematoden | Steinernema feltiae | Trauermücken-Larven (Bradysia spp.) | 2.000.000 / m² (Gießanwendung) | ~1–2 Wochen |

**Hinweis:** *Phytoseiulus persimilis* ist für den Frauenhaarfarn besonders geeignet, da die Raubmilbe relative Luftfeuchtigkeit > 70 % benötigt — exakt das Klima, das der Farn ohnehin braucht. Optimaler Wirkbereich 13–27 °C; oberhalb 30 °C unwirksam. *Cryptolaemus montrouzieri* wirkt am besten bei 25–28 °C. *Steinernema feltiae* (entomopathogene Nematoden) wird über das Substrat gegossen und ist zwischen 14–26 °C am aktivsten; greift die feinen Wurzeln nicht an.

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze (ideal für Terraria und Badezimmer-Arrangements).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Nordafrikanischer Frauenhaarfarn | Adiantum capillus-veneris | Gleiche Gattung | Ähnliche Pflege, etwas robuster |
| Nestfarn | Asplenium nidus | Farn, Zimmerpflanze | Viel robuster, toleriert Trockenheit besser |
| Schwertfarn | Nephrolepis exaltata | Farn, Zimmerpflanze | Robuster, toleriert mehr Licht |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Adiantum raddianum,"Frauenhaarfarn;Delta-Frauenhaarfarn;Maidenhair Fern;Delta Maidenhair",Pteridaceae,Adiantum,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Tropisches Amerika (Brasilien)",yes,1-5,12,20-45,20-40,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [NC State Extension — Adiantum raddianum](https://plants.ces.ncsu.edu/plants/adiantum-raddianum/) — Botanische Basisdaten, USDA-Zonen
2. [Gardeners World — Maidenhair Fern](https://www.gardenersworld.com/house-plants/how-to-grow-maidenhair-fern-adiantum-raddianum/) — Pflegehinweise
3. [Guide to Houseplants — Maidenhair Fern](https://www.guide-to-houseplants.com/maidenhair-fern.html) — Kulturdaten
4. [Plant Care Today — Maidenhair Fern](https://plantcaretoday.com/maidenhair-fern.html) — Schädlinge, Propagation
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
6. [RHS — Adiantum raddianum (Delta maidenhair fern)](https://www.rhs.org.uk/plants/20650/adiantum-raddianum/details) — Halbschatten (partial shade), Hardiness H1c, Mindesttemperatur, Standort <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
7. [Tosens et al. 2016, New Phytologist — Photosynthetic capacity in 35 ferns and fern allies](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.13719) — Farne als C3-Pflanzen, mesophylle CO₂-Diffusion <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
8. [Springer, Journal of Plant Research — Rapid response of leaf photosynthesis in fern species (Pteridium, Thelypteris)](https://link.springer.com/article/10.1007/s10265-015-0736-5) — C3-Photosynthese bei Farnen <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
9. [Saldaña et al. 2015, PMC4699196 — Photosynthetic Light Responses, Hymenophyllaceae](https://pmc.ncbi.nlm.nih.gov/articles/PMC4699196/) — Lichtkompensationspunkte schattenadaptierter Farne (1.45–4.9 µmol/m²/s) <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
10. [Craine & Reich 2005, New Phytologist — Leaf-level light compensation points in shade-tolerant species](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2005.01420.x) — LCP-Bereich schattentoleranter Unterwuchspflanzen (10–50 µmol/m²/s) <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
11. [Healthy Houseplants — Maidenhair Fern (Adiantum) Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/maidenhair-fern-adiantum-care-guide/) — pH 6.0–7.0, Staunässe-Empfindlichkeit, Salzanreicherung <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
12. [Greg.app — Best Soil for Maidenhair Fern](https://greg.app/plant-care/soil/maidenhair-fern/) — pH-Vorzug, gut durchlässiges Substrat <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
13. [Plantura — Maidenhair fern: care, location & toxicity](https://plantura.garden/uk/houseplants/maidenhair-fern/maidenhair-fern-overview) — Überwinterung ~15 °C, min. 12 °C, nicht winterhart <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
14. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate 2–50/m², RH > 70 %, gegen Spinnmilben <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
15. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate 5–40/m² gegen Schmierläuse <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
16. [Koppert — Scia-Rid (Steinernema feltiae)](https://www.koppert.com/scia-rid/) — 2 Mio. Nematoden/m² gegen Trauermücken-Larven <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
