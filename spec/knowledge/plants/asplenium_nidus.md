# Nestfarn — Asplenium nidus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/birds-nest-fern-care-guide-asplenium-nidus/), [Clemson HGIC](https://hgic.clemson.edu/how-to-grow-and-care-for-birds-nest-fern-asplenium-nidus/), [Planet Natural](https://www.planetnatural.com/birds-nest-fern/), [NC State Extension](https://plants.ces.ncsu.edu/plants/asplenium-nidus/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Asplenium nidus | `species.scientific_name` |
| Volksnamen (DE/EN) | Nestfarn, Vogelnestfarn; Bird's Nest Fern | `species.common_names` |
| Familie | Aspleniaceae | `species.family` → `botanical_families.name` |
| Gattung | Asplenium | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Photosynthese-Typ (photosynthesis pathway) | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein publizierter GDD-Basiswert für *Asplenium nidus*; als wärmeliebende Tropenpflanze (Wachstumsstopp < 13–15°C) läge die Basis deutlich oberhalb der ~10°C wärmeliebender Freilandkulturen, jedoch ohne belastbare Quelle nicht belegbar | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Reagiert empfindlich auf Kälte unter 13°C und Zugluft. | `species.hardiness_detail` |
| Heimat | Tropisches Asien, Australien, Ostafrika — epiphytisch in Baumkronen tropischer Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Nestfarn ist einer der wenigen Farne, die als robuste Zimmerpflanze bestehen können. Im Gegensatz zu anderen Farnen (z.B. Adiantum) verträgt er auch mal ein Vergessen beim Gießen. Die trichterförmige Blattrosette sammelt natürlich Wasser und organisches Material — daher die Bezeichnung "Vogelnest". Wichtig: Wasser niemals direkt in die Mitte gießen (Fäulnis-Gefahr). Die zuerst aufrollenden Blattwedel sind extrem empfindlich — niemals berühren.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farne blühen nicht — Vermehrung über Sporen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | spore | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Ausschließlich über Sporen (braune Sporenlager unter den Wedeln). Sporen auf steriles feuchtes Torfsubstrat aufstreuen, mit Klarsichtfolie abdecken, bei 22–24°C halten. Nach 4–6 Wochen Protallen sichtbar; nach 3–6 Monaten erste echte Wedel. Sehr langsam. Teilung ist bei monotypischen Rosetten nicht möglich. Im Handel werden Pflanzen vegetativ via Gewebezucht (Meristeming) vermehrt.

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
| Pollenallergen | true (Sporen können bei Farnsporen-Allergikern reagieren) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Abgestorbene Wedel an der Basis entfernen. Niemals junge, aufrollende Wedel beschädigen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, feuchtigkeitshaltende aber gut durchlässige Farnerde: Einheitserde mit 20% Perlite + 20% Torf oder Kokoserde. pH 5.5–7.0. Epiphytensubstrat mit Pinienrinde ist ebenfalls geeignet. Kein schweres, kompaktes Substrat. | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 15 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | 1.5 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN --> kein artspezifischer Maas-Hoffman-Slope publiziert | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–7.0 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) liegt für diese schattenadaptierte epiphytische C3-Pflanze am unteren Rand der C3-Spanne (8–16 µmol/m²/s; Schattenblätter darunter). Der hier eingetragene Wert ist NUR der Kompensationspunkt. Lichtsättigung und Optimum liegen deutlich höher (bevorzugtes Kulturlicht hell-indirekt, ~50–250 µmol/m²/s, siehe §2.2); direkte Sonne verbrennt die Wedel (Photoinhibition). — Salztoleranz: *Asplenium*-Farne reagieren ausgesprochen salzempfindlich (Klasse `sensitive`); die ECe-Schwelle bezieht sich auf die Substrat-Sättigungsextrakt-Leitfähigkeit (saturated paste ECe), NICHT auf die Gießwasser-EC. Der Wert 1.5 dS/m liegt im Bereich der Maas-Hoffman-Klasse "sensitive" (< ~2 dS/m). Daher halbe Düngerdosis und weiches, salzarmes Gießwasser (vgl. §3.2). — Wurzelsystem flach und feinfaserig (epiphytisch); Rhizom an der Substratoberfläche halten (Fäulnisgefahr).

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.2–0.6 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (stomatärer Kollaps, kPa) | 1.0 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5–0.55 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Schwelle (stomatärer Kollaps, kPa) | 0.9 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.5–7.0 | 70 | 25 | 0.5 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.02 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Winterruhe | 0:0:0 | 0.0 | 5.5–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Die Mn/Zn/Cu/Mo-Werte folgen der Standard-Hoagland-Mikronährstoffreferenz (Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.05 ppm bei Vollnährlösung). Da der Nestfarn ein Schwachzehrer (`light_feeder`) und salzempfindlich ist, werden diese Werte in der Praxis mit halber Dünger-Dosierung (vgl. §3.2) entsprechend verdünnt ausgebracht.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Farn- und Palmendünger | Compo | base | 7-4-5 | 3 ml/L (halbe Dosis, alle 4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4–6 Wochen April bis August — halbe Dosierung! Farne sind sehr salzempfindlich. Kein Dünger September bis März. Fluorid im Wasser schadet (Blattspitzenverbrennung) — weiches, kalkfreies Wasser empfohlen. Nie Düngerlösung direkt in die Blatttrichter gießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt; NICHT in die Blattmitte gießen! Vom Rand her wässern. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | 9 (September, vor Nachttemperaturen < 13°C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | 6 (Juni, nach den Eisheiligen, stabile Nächte > 15°C) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (Minimum 13°C, kurzfristig 10°C toleriert) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (keine direkte Wintersonne); ggf. Pflanzenlicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert; erst gießen, wenn obere Substratschicht abgetrocknet ist (Staunässe = Wurzel-/Herzfäule) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Der Nestfarn ist nicht frosthart und überwintert als frostfreie Zimmer-/Kübelpflanze drinnen (`frost_free`). In Mitteleuropa (USDA 6–8) kann er im Sommer geschützt halbschattig draußen stehen, muss aber rechtzeitig vor Nachttemperaturen unter ~13°C wieder hereingeholt werden. Zugluft, Heizungsnähe und trockene Heizungsluft im Winter meiden; Luftfeuchte > 55% halten.

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben | medium |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Stielen | medium |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Herzfäule | fungal | Braun-matschige Blattmitte, Fäulnisgeruch | Wasser in der Blatttrichter |
| Wurzelfäule | fungal | Welke, gelbe Wedel | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken | Nasse Blätter, schlechte Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Nie in Mitte gießen | cultural | Gießtechnik ändern | 0 | Herzfäule (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Schildlaus |
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke |

### 5.4 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|-------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 10–30 / m² (1–3 / sq ft), bei Befall wiederholen | 2–3 Wochen |
| Steinernema-Nematoden | Steinernema feltiae | Trauermückenlarven (Bradysia spp.) | ~250 000 / m² Substratoberfläche, als Gießgabe | 1–2 Wochen |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Woll-/Schmierläuse, weiche Schildläuse | 5–40 / m² je Ausbringung, 3× im Abstand 1–2 Wochen | 4–8 Wochen |

**Hinweis:** Nützlingseinsatz eignet sich besonders für die geschlossene Innenraum-/Gewächshauskultur. *Phytoseiulus persimilis* benötigt Luftfeuchte > 60% — beim Nestfarn ohnehin gegeben. Da Farne salz- und chemieempfindlich sind, ist die biologische Bekämpfung der chemischen vorzuziehen.

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Wellenblättriger Nestfarn | Asplenium nidus 'Crispy Wave' | Gleiche Art | Gewellte Wedel, dekorativ |
| Lanzettfarn | Asplenium scolopendrium | Gleiche Gattung | Winterharter (für Außenbereich) |
| Schwertfarn | Nephrolepis exaltata | Verschiedene Familie | Robuster, einfacher zu vermehren |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Asplenium nidus,"Nestfarn;Vogelnestfarn;Bird's Nest Fern",Aspleniaceae,Asplenium,perennial,day_neutral,herb,fibrous,"11a;11b;12a","Tropisches Asien, Australien, Ostafrika",yes,2-8,15,30-80,30-80,yes,no,false,light_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Crispy Wave,Asplenium nidus,"ornamental;wavy_fronds;compact",clone
Osaka,Asplenium nidus,"ornamental;narrow_fronds;upright",clone
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Bird's Nest Fern](https://www.healthyhouseplants.com/indoor-houseplants/birds-nest-fern-care-guide-asplenium-nidus/) — Pflegehinweise, Schädlinge
2. [Clemson HGIC — Asplenium nidus](https://hgic.clemson.edu/how-to-grow-and-care-for-birds-nest-fern-asplenium-nidus/) — Kulturdaten
3. [Planet Natural — Bird's Nest Fern](https://www.planetnatural.com/birds-nest-fern/) — Pflegehinweise
4. [NC State Extension — Asplenium nidus](https://plants.ces.ncsu.edu/plants/asplenium-nidus/) — Botanische Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Wikipedia — C3 carbon fixation](https://en.wikipedia.org/wiki/C3_carbon_fixation) — Photosynthese-Typ; C3 als Standardweg bei Farnen
7. [Wiley/IJG — Transcriptomic Evidence of Adaptive Evolution of the Epiphytic Fern *Asplenium nidus*](https://onlinelibrary.wiley.com/doi/10.1155/2019/1429316) — Photosynthese-Gene, Epiphytismus, Lichtanpassung
8. [Light Compensation — ScienceDirect Topics](https://www.sciencedirect.com/topics/engineering/light-compensation) — Definition Lichtkompensationspunkt, niedrigere LCP bei Schattenpflanzen
9. [GPN — Maximizing Supplemental Lighting (Runkle/MSU)](https://www.canr.msu.edu/uploads/resources/pdfs/maximizingsupplementallighting.pdf) — LCP C3-Pflanzen 8–16 µmol/m²/s, Schattenblätter am unteren Rand
10. [FAO — Annex 1. Crop salt tolerance data (Maas-Hoffman)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Salztoleranz-Klassen, ECe-Schwellen, sensitive < ~2 dS/m
11. [USDA-ARS — Plant Salt Tolerance, Handbook 60 (Maas-Hoffman-Modell)](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — ECe-Schwellenwert (saturated paste), Slope-Konzept
12. [ScienceDirect — Germination/reproductive biology in salty conditions of *Asplenium marinum*](https://www.sciencedirect.com/science/article/abs/pii/S0367253009000280) — Salzempfindlichkeit der Gattung *Asplenium*
13. [Missouri Botanical Garden — *Asplenium nidus* Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=285707) — Wurzelsystem (flach, faserig), Halbschatten, Topfkultur
14. [Gardeners HQ — *Asplenium nidus* Growing & Care Guide](https://www.gardenershq.com/Asplenium-nidus.php) — flaches Rhizom an Substratoberfläche, Schattentoleranz
15. [PLOS One — Leaf Photosynthetic Rate of Tropical Ferns Linked to Water Transport](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0084682) — Messung tropischer Farne bei Blatttemp. 25–27°C; epiphytische vs. terrestrische Photosynthesekapazität
16. [Springer — Temperature response of photosynthesis in C3, C4 and CAM plants](https://link.springer.com/article/10.1007/s11120-013-9874-6) — höheres T_opt bei tropisch adaptierten Pflanzen
17. [Foliage Factory — Plant Stomata Explained](https://foliage-factory.com/blogs/plant-care/stomata-plant-function-explained) — Farne 60–80% RH, VPD-Sensitivität tropischer Blattpflanzen
18. [Oxford/Plant Physiology — Stomatal VPD Response: More to the Story Than ABA](https://academic.oup.com/plphys/article/176/1/851/6117386) — VPD-Schwelle & stomatäre Schließung, passive Farn-Reaktion auf Turgorverlust
19. [Clemson HGIC — Bird's Nest Fern Care](https://hgic.clemson.edu/how-to-grow-and-care-for-birds-nest-fern-asplenium-nidus/) — Überwinterung, Mindesttemperatur, Winterpflege
20. [The Sill — How to Care for a Bird's Nest Fern](https://www.thesill.com/blogs/plants-101/how-to-care-for-birds-nest-fern-asplenium-nidus) — Min. 10°C kurzfristig / 15–27°C ideal, Winterquartier
21. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Referenz Mn/Zn/Cu/Mo (ppm)
22. [Grokipedia — Hoagland solution](https://grokipedia.com/page/Hoagland_solution) — Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.05 ppm bei Vollnährlösung
23. [Cornell NYSIPM — *Phytoseiulus persimilis* Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate & Etablierung Spinnmilben-Raubmilbe
24. [Bugs for Growers — Beneficial Nematodes for Fungus Gnats (*Steinernema feltiae*)](https://blog.bugsforgrowers.com/natural-predators/entomopathogenic-nematodes/beneficial-nematodes/two-biocontrol-agents-for-effective-control-of-fungus-gnats/) — Ausbringrate Trauermückenlarven
25. [Koppert — Cryptobug-L (*Cryptolaemus montrouzieri*)](https://www.koppert.com/cryptobug-l/) — Ausbringrate & Etablierungszeit gegen Woll-/Schmierläuse
26. [Understory R:FR / far-red ratio — bioRxiv: Understory light quality](https://www.biorxiv.org/content/10.1101/829036v1.full) — R:FR im Unterwuchs, FR/(R+FR) ≈ 0.5 bei offenem Tageslicht
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
