# Herzblatt-Philodendron — Philodendron hederaceum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/how-to-care-for-heartleaf-philodendron/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-philodendron), [ASPCA](https://www.aspca.org/), [Healthy Houseplants](https://www.healthyhouseplants.com/), [Soltech](https://soltech.com/products/heartleaf-philodendron-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Philodendron hederaceum | `species.scientific_name` |
| Volksnamen (DE/EN) | Herzblatt-Philodendron, Kletterphilodendron; Heartleaf Philodendron, Sweetheart Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Philodendron | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wurzeltyp | aerial | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> (tagneutral, kein photoperiodischer Blühreiz) | `lifecycle_configs.critical_day_length_hours` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> (kein artspezifischer Wuchs-/Phänologie-GDD-Wert belegt; reine Zimmerkultur. Bekannt: Wachstum stoppt unter ca. 10 °C, Schäden ab < 13 °C — dies sind Mindesttemperaturen, NICHT die GDD-Basis) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–26°C. Sehr empfindlich gegenüber Kälte und Zugluft. | `species.hardiness_detail` |
| Heimat | Tropisches Mittelamerika und Karibik (Mexiko, Jamaika, Brasilien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** *Philodendron hederaceum* ist die korrekte Bezeichnung für den weit verbreiteten "Kletterphilodendron" oder "Herzblattphilodendron". Früher oft als *P. scandens* oder *P. oxycardium* geführt — diese Namen sind synonymisch. Im Handel auch als "Brasil" (variegierte Sorte) oder "Lemon Lime" bekannt. Verwechslungsgefahr mit Epipremnum aureum (Efeutute) — beide sehen ähnlich aus, sind aber getrennte Gattungen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor nicht) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–3 Knoten und mindestens 2 Blättern. Bewurzelung in Wasser (2–4 Wochen) oder direkt in feuchtem Substrat. Sehr hohe Erfolgsrate. Jeder Steckling sollte mindestens einen Knoten unterhalb der Wasseroberfläche haben.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft kann Kontaktdermatitis auslösen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 (hängend/kletternd bis 200+) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (optional — Moosstab fördert größere Blätter) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, durchlässige Einheitserde mit 20–30% Perlite. pH 6.0–7.0. Guter Wasserabzug wichtig. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (kein belegter numerischer Kompensationspunkt; als ausgeprägte Schattenpflanze liegt er erfahrungsgemäß sehr niedrig) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> (keine Maas-Hoffman-Schwelle für Zierpflanze belegt; qualitativ salzempfindlich) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** *Lichtkompensationspunkt (light compensation point):* Als isomorpher Unterwuchs-Aroid mit hoher Schattentoleranz fängt *P. hederaceum* Schwachlicht effizient ab; der echte Kompensationspunkt (Netto-Photosynthese = 0) ist nicht numerisch publiziert. Praktisch beginnt sichtbares Wachstum erst oberhalb ca. 50 PPFD — das ist eine Wachstums-Untergrenze, NICHT der Kompensationspunkt und gehört daher nicht ins LCP-Feld. *Wurzeltiefe:* flaches, fibröses (faseriges) Wurzelsystem, in Topfkultur effektiv flach (15–30 cm); trocknet schneller ab als aufrechte Arten. *Staunässe (waterlogging):* sehr empfindlich, Staunässe führt rasch zu Wurzelfäule — durchlässiges Substrat und Topf-Drainage zwingend. *Salztoleranz:* salzempfindlich; Akkumulation aus Leitungswasser/Dünger verursacht braune Blattspitzen, Substrat sollte monatlich durchgespült werden. *Boden-pH:* Quellen nennen leicht sauer bis neutral (überlappend ca. 5.5–7.0); der eingetragene Bereich 6.0–7.0 harmonisiert mit §1.6 (Substrat-Empfehlung) und §2.3 (Nährstoffprofile derselben Datei).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.60–0.75 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.60–0.75 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.2 | 6.0–7.0 | 100 | 40 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Mikronährstoffe Mn/Zn/Cu/Mo: keine artspezifischen ppm-Sollwerte aus zwei seriösen Quellen für P. hederaceum belegt; werden über handelsübliche Grünpflanzen-Volldünger (Spurenelemente enthalten) abgedeckt. Daher als DATEN FEHLEN markiert statt erfundener Werte. -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Schwachzehrer — alle 4 Wochen in der Wachstumsphase reicht. Überdüngung führt zu braunen Blattspitzen. Im Winter kein Dünger.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; abgestandenes Wasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor Nachttemperaturen < 13 °C ins Haus) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach Eisheiligen, nur frostfrei) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–22 (nie unter 13 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; ggf. Pflanzenlicht bei < 8 h Tageslicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam, Substrat zwischen den Gaben antrocknen lassen (Intervall 14–21 Tage) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** *P. hederaceum* ist nicht frosthart (USDA 10–11). In Mitteleuropa (USDA 6–8) ausschließlich als Zimmer-/Kübelpflanze; ein Sommeraufenthalt auf Balkon/Terrasse ist nur in den frostfreien Monaten möglich. Die Pflanze wird NICHT ausgegraben/eingelagert (kein `dig_and_store`), sondern als immergrüne Pflanze frostfrei im Haus überwintert (`frost_free`). Keine echte Dormanz — nur wachstumsverlangsamte Winterruhe (vgl. §2.1).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, gelbe Punkte | leaf | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Achseln | leaf, stem | easy |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | root | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Wurzeln | Überbewässerung |
| Blattflecken | bacterial | Braune, nasse Flecken | Wasser auf Blättern |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Nematoden | biological | Gießen (Steinernema feltiae) | 0 Tage | Trauermücke |
| Systeminsektizid | chemical | Stäbchen | 14 Tage | Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | 2–5 Käfer/Pflanze (mehrere kleine Freisetzungen besser als eine große) | mehrere Wochen bis Monate (langsam bei langsam wachsenden Zierpflanzen) |
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | ca. 5–20/m² bei leichtem Befall (0.5–2/sq ft) | 1–2 Wochen, Wiederholung alle 1–2 Wochen |
| Insektenpathogene Nematoden | Steinernema feltiae | Trauermücke (Bradysia spp., Larven im Substrat) | ca. 0.5 Mio./m² (Gießanwendung) | 1–2 Wochen, feuchtes Substrat erforderlich |

**Hinweis:** Reihenfolge der Ausbringung: zuerst Boden-Nützlinge (*Steinernema*) ausbringen, danach Blatt-Räuber (*Phytoseiulus*, *Cryptolaemus*). Nützlinge nicht mit chemischen Breitband-Insektiziden (§5.3 Systeminsektizid) kombinieren — mindestens 4 Wochen Abstand nach chemischer Anwendung. Encarsia formosa (gegen Weiße Fliege) ist hier nicht gelistet, da Weiße Fliege bei *P. hederaceum* kein typischer Schädling ist (vgl. §5.1).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Efeutute | Epipremnum aureum | Sehr ähnliche Hängepflanze | Noch robuster, verträgt mehr Vernachlässigung |
| Velvet Philodendron | Philodendron micans | Gleiche Gattung | Samtartige, dunkel-bronzefarbene Blätter |
| Philodendron Brasil | Philodendron hederaceum 'Brasil' | Sorte mit Variegation | Dekorativere Blätter mit gelbgrünen Streifen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Philodendron hederaceum,"Herzblatt-Philodendron;Kletterphilodendron;Heartleaf Philodendron",Araceae,Philodendron,perennial,day_neutral,vine,aerial,"10a;10b;11a;11b","Tropisches Mittelamerika",yes,2-10,15,20-200+,40-100,yes,limited,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Brasil,Philodendron hederaceum,"ornamental;variegated;yellow_green",clone
Lemon Lime,Philodendron hederaceum,"ornamental;chartreuse_leaves",clone
```

**Hinweis:** Micans (Philodendron micans) wird in neuerer Literatur teils als eigene Art geführt und ist in Sektion 7 als "Ähnliche Art" aufgelistet — daher kein Cultivar-Eintrag hier.

---

## Quellenverzeichnis

1. [Smart Garden Guide — Heartleaf Philodendron](https://smartgardenguide.com/how-to-care-for-heartleaf-philodendron/) — Pflegehinweise
2. [The Sill — Philodendron Care](https://www.thesill.com/blogs/plants-101/how-to-care-for-philodendron) — Praxiswissen
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Soltech — Heartleaf Philodendron](https://soltech.com/products/heartleaf-philodendron-care) — Lichtanforderungen
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/heartleaf-philodendron-plant-care-guide/) — Ganzjahrespflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Mioranza et al. (2018), Theoretical and Experimental Plant Physiology 30:89–101 — *Philodendron hederaceum*, isomorpher Aroid, Boden-Kronen-Transition](https://link.springer.com/article/10.1007/s40626-018-0105-6) — Blattphysiologie/Schattenanpassung (Stomatadichte, Chlorophyll, Elektronentransportrate)
7. [Holtum et al. (2011), PubMed — CAM im ZZ-Pflanze *Zamioculcas zamiifolia* (Araceae)](https://pubmed.ncbi.nlm.nih.gov/21636363/) — Beleg: CAM in Araceae extrem selten, Philodendron = C3
8. [Wikipedia — Crassulacean acid metabolism](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Verbreitung, C3 als Standard außerhalb der bekannten CAM-Linien
9. [Foliage Factory — Beneficial Insects for Indoor Plants](https://www.foliage-factory.com/post/beneficial-insects-biological-pest-control) — Nützlinge für Zimmerpflanzen (Cryptolaemus, Phytoseiulus, Steinernema)
10. [NaturesGoodGuys — Phytoseiulus persimilis Introduction Rates](https://www.naturesgoodguys.com/pages/phytoseiulus-persimilis-introduction-rates) — Ausbringraten Raubmilbe
11. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Ausbringstrategie Mealybug destroyer
12. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Etablierung/Anwendung Raubmilbe
13. [UConn Home & Garden Education — Houseplant Temperature Tolerance](https://homegarden.cahnr.uconn.edu/2025/08/02/houseplant-temps/) — Mindesttemperaturen, Kälteempfindlichkeit
14. [Gardener's Path — Philodendron Brown Leaves (soluble salts)](https://gardenerspath.com/plants/houseplants/philodendron-brown-leaves/) — Salzempfindlichkeit, Substrat-Spülung
15. [Greg — Heartleaf Philodendron Roots](https://greg.app/heartleaf-philodendron-roots/) — flaches/fibröses Wurzelsystem, Staunässe-Empfindlichkeit
16. [Greg — Best Soil for Philodendron hederaceum (pH)](https://greg.app/philodendron-hederaceum-var-hederaceum-soil/) — Boden-pH-Vorzug (leicht sauer bis neutral)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
