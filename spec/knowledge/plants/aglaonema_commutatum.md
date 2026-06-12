# Chinesisches Immergrün — Aglaonema commutatum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Ohio Tropics](https://www.ohiotropics.com/2020/06/27/aglaonema-chinese-evergreen-care/), [Clemson HGIC](https://hgic.clemson.edu/factsheet/chinese-evergreen-aglaonema-care-cultivation-growing-guide/), [Planet Natural](https://www.planetnatural.com/aglaonema/), [NC State Extension](https://plants.ces.ncsu.edu/plants/aglaonema/), [ASPCA](https://www.aspca.org/), [MDPI App. Sci. 13:3021](https://www.mdpi.com/2076-3417/13/5/3021), [Missouri Botanical Garden](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=276174), [USDA-ARS Salt Tolerance](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aglaonema commutatum | `species.scientific_name` |
| Volksnamen (DE/EN) | Chinesisches Immergrün; Chinese Evergreen, Philippine Evergreen | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Aglaonema | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Kritische Tageslänge (critical day length, h) | — (tagneutral, kein Kurz-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | 13 (abgeleitet aus Kälte-/Wachstumsgrenze; kein eigenständiger Literaturwert) | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–29°C. Sehr empfindlich gegen Kälte unter 13°C. | `species.hardiness_detail` |
| Heimat | Philippinen, Borneo, Sulawesi — tropische Regenwälder, Unterwuchs | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | benzene, formaldehyde | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Aglaonema ist eine der tolerantesten Zimmerpflanzen und eignet sich ideal für dunkle Raumecken, wo die meisten anderen Zimmerpflanzen versagen. Faustregel: Dunklere Sorten tolerieren wenig Licht, bunte/rosa Sorten brauchen mehr Licht für ihre Farbintensität. Sehr geeignet für Büros und schlecht beleuchtete Räume.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (kleine Spadix-Blüten, in Zimmerkultur selten; bei älteren Pflanzen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen (Frühjahr). Stängelstecklinge bei 22–26°C bewurzeln. Handschuhe empfohlen (Saft enthält Calciumoxalat).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Saft — Hautreizungen möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kein regelmäßiger Rückschnitt nötig. Abgestorbene Blätter entfernen. Bei leggy-Wuchs: Triebe zurückschneiden — treibt neu aus.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20% Perlite. pH 5.5–6.5 (leicht sauer). Hoher organischer Anteil bevorzugt. Torfmischungen funktionieren gut. | — | <!-- pH-Spanne auf 5.5–6.5 harmonisiert, Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) min | 3 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) max | 8 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | deep_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | < 3 (Maas-Hoffman a) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | — <!-- DATEN FEHLEN: kein artspezifischer Slope-Wert belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt (Netto-Photosynthese = 0) liegt sehr niedrig — typisch für eine obligate Schattenpflanze (obligate shade plant). Die licht-gesättigte Photosyntheserate ist selbst für Schattenpflanzen extrem gering (0.7–1.0 µmol CO₂ m⁻² s⁻¹), die Lichtsättigung (light saturation point) wird bereits bei ~125 µmol/m²/s erreicht — diese Sättigungs-/Optimumwerte gehören NICHT in das Kompensationspunkt-Feld. Salztoleranz-Klasse nach Miyamoto/USDA-Schema (sensitive = ECe-Schwelle 0–3 dS/m, bezogen auf Substrat-ECe, nicht Gießwasser-EC); A. commutatum reagiert empfindlich auf Salzanreicherung im Substrat (Blattspitzen-Nekrose / „tipping" durch Dünger- und Leitungswassersalze) — regelmäßiges Durchspülen empfohlen.
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
| Licht PPFD (µmol/m²/s) | 50–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (vpd threshold, kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 2–6 | `requirement_profiles.dli_target_mol` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 17–24 | `requirement_profiles.temperature_day_c` |
| VPD-Schwelle (vpd threshold, kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 5.5–6.5 | 80 | 30 | — <!-- DATEN FEHLEN --> | — <!-- DATEN FEHLEN --> | — <!-- DATEN FEHLEN --> | — <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.3 | 5.5–6.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Für *Aglaonema commutatum* liegen keine zwei unabhängigen, seriösen Quellen mit artspezifischen Gewebe-Zielwerten (Mn/Zn/Cu/Mo in ppm) vor; die Felder bleiben daher als `DATEN FEHLEN` markiert statt mit allgemeinen Gemüse-Standardwerten belegt zu werden. pH-Spanne auf 5.5–6.5 harmonisiert (konsistent mit §1.6/§1.7).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 4 ml/L (alle 4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen März bis September. Oktober bis Februar: kein Dünger. Leichter Zehrer — halbe bis dreiviertel Dosis ausreichend. Bei wenig Licht: Düngemenge reduzieren.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; Kälte unter 13°C schadet — nie mit kaltem Wasser gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–24 (nie unter 15) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; bei wenig Tageslicht Pflanzenlampe | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert; Substrat zwischen Gaben antrocknen lassen, zimmerwarmes Wasser | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Reine Zimmerpflanze in Mitteleuropa (USDA 6–8 → nicht frosthart). `frost_free` = frostfreie Überwinterung drinnen (kein Ausgraben/Einlagern). Ein sommerlicher Aufenthalt im Freien (Halbschatten, windgeschützt) ist möglich, muss aber vor Temperaturen unter ~15°C beendet werden; Kälteschäden treten bereits unter 13°C auf (dunkle, speckig wirkende Blattflecken).
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
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Blattflecken | fungal/bacterial | Braune, verwässerte Flecken | Nasses Laub, Kälte |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|-----------------------|----------------|--------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 2–6 Tiere/Pflanze bzw. ~20/m² bei Befall | 2–3 Wochen |
| Cryptolaemus montrouzieri (Australischer Marienkäfer / mealybug destroyer) | Schmierlaus (Pseudococcus spp.) | 2–5 Käfer/m² (ggf. mehrere Freilassungen) | 3–4 Wochen |
| Amblyseius / Neoseiulus californicus (Raubmilbe) | Spinnmilbe (präventiv/leichter Befall) | ~25–50/m² | 2–3 Wochen |

**Hinweis:** Nützlinge benötigen ~20–30°C und 60–90% rel. Luftfeuchte — im warmen Wohnraum gut umsetzbar. *Phytoseiulus persimilis* erst bei sichtbarem Spinnmilbenbefall ausbringen (reiner Beutegreifer, verhungert ohne Beute); *Cryptolaemus* wirkt am besten von April bis Oktober. Keine Wartezeit (Karenz) bei rein biologischer Bekämpfung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Dieffenbachie | Dieffenbachia seguine | Gleiche Familie, großblättrig | Schnelleres Wachstum |
| Spathiphyllum | Spathiphyllum wallisii | Ähnlich robust, schattentolerant | Schöne Blüten (ebenfalls toxisch — Calciumoxalat) |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Aglaonema commutatum,"Chinesisches Immergrün;Chinese Evergreen;Philippine Evergreen",Araceae,Aglaonema,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Philippinen, Borneo, Sulawesi",yes,3-10,15,30-120,30-80,yes,no,false,light_feeder,0.6
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Maria,Aglaonema commutatum,"ornamental;dark_green;silver_stripes",clone
Silver Bay,Aglaonema commutatum,"ornamental;silver_center;green_edges",clone
Crete,Aglaonema commutatum,"ornamental;burgundy_red;green",clone
Red Siam,Aglaonema commutatum,"ornamental;red_pink;green_edges",clone
```

---

## Quellenverzeichnis

1. [Ohio Tropics — Aglaonema](https://www.ohiotropics.com/2020/06/27/aglaonema-chinese-evergreen-care/) — Kulturdaten, Sorten
2. [Clemson HGIC — Chinese Evergreen](https://hgic.clemson.edu/factsheet/chinese-evergreen-aglaonema-care-cultivation-growing-guide/) — Wissenschaftliche Grundlagen
3. [Planet Natural — Aglaonema](https://www.planetnatural.com/aglaonema/) — Pflegehinweise
4. [NC State Extension — Aglaonema](https://plants.ces.ncsu.edu/plants/aglaonema/) — Botanische Daten, Lichtkategorie (deep/partial shade), pH (acid <6.0), Boden-Drainage, Min.-Temperatur, Überwinterung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
6. [MDPI Applied Sciences 13(5):3021 — Effect of Light Availability on Photosynthetic Responses of Four Aglaonema commutatum Cultivars](https://www.mdpi.com/2076-3417/13/5/3021) — Photosynthese-Typ (C3), Lichtsättigung ~125 µmol/m²/s, sehr niedrige licht-gesättigte Rate (Schattenpflanze) <!-- Steckbrief-Erweiterung 2026-06 -->
7. [Missouri Botanical Garden — Aglaonema commutatum](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=276174) — Lichtkategorie (part shade to full/heavy shade), well-drained/Staunässe-Empfindlichkeit, 60°F Min.-Wintertemperatur, Wuchsmaße <!-- Steckbrief-Erweiterung 2026-06 -->
8. [Plants For All Seasons — Aglaonema Soil Guide](https://www.plantsforallseasons.co.uk/blogs/aglaonema-care/a-guide-to-the-best-aglaonema-plant-soil) — Boden-pH-Vorzug 5.5–6.5, lockeres, gut durchlässiges Substrat <!-- Steckbrief-Erweiterung 2026-06 -->
9. [USDA-ARS Chapter 13 — Plant Salt Tolerance (Maas & Hoffman)](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — Maas-Hoffman-Modell, Salztoleranz-Klassifikation (sensitive 0–3 dS/m ECe) <!-- Steckbrief-Erweiterung 2026-06 -->
10. [Foliage Factory — Aglaonema Care](https://www.foliage-factory.com/aglaonema) — Salzempfindlichkeit (Tipping durch Dünger-/Wassersalze), realistische Lichtniveaus <!-- Steckbrief-Erweiterung 2026-06 -->
11. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Raubmilbe gegen Spinnmilbe, Ausbringung, Klimaansprüche <!-- Steckbrief-Erweiterung 2026-06 -->
12. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate, Etablierung <!-- Steckbrief-Erweiterung 2026-06 -->
13. [Texas A&M Landscape IPM — Commercially Available Natural Enemies](https://landscapeipm.tamu.edu/types-of-pest-control/biological-2/commercial-natural-enemies/) — Cryptolaemus montrouzieri Ausbringrate, Saison <!-- Steckbrief-Erweiterung 2026-06 -->
