# Geldbaum — Crassula ovata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/jade-plant-crassula-ovata/), [Wikipedia Crassula ovata](https://en.wikipedia.org/wiki/Crassula_ovata), [Old Farmer's Almanac](https://www.almanac.com/plant/jade-plants), [ASPCA](https://www.aspca.org/), [Joy Us Garden](https://www.joyusgarden.com/jade-plant-care/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Crassula ovata | `species.scientific_name` |
| Volksnamen (DE/EN) | Geldbaum, Pfennigbaum, Jade-Pflanze; Jade Plant, Money Plant, Friendship Tree | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Crassula | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | succulent <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher shrub) --> | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 50–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | ~10 (Blüteninduktion bei ≥14 h ununterbrochener Dunkelheit / Kurztag) | `lifecycle_configs.critical_day_length_hours` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> kein publizierter Wuchs-/Phänologie-Basiswert (nur Kardinaltemperaturen; nicht als GDD-Basis verwendbar) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07-03 (R4-Korrektur, ✅ GESICHERT 3/3 Quellen) -->
| Dormanz erforderlich | true (herbstlich-winterliche Ruheperiode mit stark reduziertem Wuchs und Gießen — natürlicher Bestandteil des Jahreszyklus, siehe §2.1 „Winterruhe" und §4.3) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Anmerkung: kühl-induzierter Blühreiz — Nachttemperaturen 10–15 °C über mehrere Wochen kombiniert mit Kurztag/langen ununterbrochenen Dunkelphasen und Trockenheit im Herbst sind Voraussetzung für zuverlässige Blüte in Zimmerkultur; kein klassischer Vernalisationsbedarf im engeren Sinn biennaler Pflanzen) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindestdauer (Tage) | 28–42 (4–6 Wochen kühle Nächte 10–15 °C in Kombination mit Kurztag und reduziertem Gießen) | `lifecycle_configs.vernalization_min_days` |
<!-- /Quelle: growing-phase-auditor 2026-07-03 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 5°C (Kältestress unter 10°C), optimal 15–29°C. Im Winter kühler Standort (10–15°C) fördert Blütenbildung. | `species.hardiness_detail` |
| Heimat | Südafrika (Mosambik, Ostkap-Region — trockene Buschsavanne) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Crassula ovata ist ein echter Sukkulentenstrauch und kann Indoor-Pflanzen der Jahrzehnte werden — bis zu 1 m Höhe und Stammdicken von 5–8 cm. Die Pflanze benötigt sehr viel Licht für guten Wuchs und Blüte. Kulturell bekannt als Glücksbringer in vielen asiatischen Kulturen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 11, 12, 1, 2 (bei reifen Pflanzen ab 5–7 Jahren bei kühlem Winterstandort) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge: 7–10 cm Ast abschneiden, 2–3 Tage Schnittfläche trocknen lassen (callus), dann in Kakteensubstrat stecken. Nicht gießen bis Widerststand beim Zupfen spürbar (Bewurzelung). Blattstecklinge: Einzelne Blätter abdrehen, trocknen lassen, auf feuchtes Substrat legen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | unknown_toxin (Wirkstoff nicht vollständig identifiziert) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken:** Übelkeit, Erbrechen, Depression bei Tieren. Quelle: ASPCA Animal Poison Control. Schweregrad gering bei normalen Mengen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Regelmäßiger Rückschnitt fördert buschigen Wuchs und verhindert "Leggy"-Wuchs. Im Frühling überlange Triebe um 1/3 kürzen. Bewurzelung der Schnittlinge möglich.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer, volle Sonne, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde oder Einheitserde mit 50% Perlite/Grobsand. Sehr gute Drainage. Tongefäße ideal. Kleiner Topf (root-bound fördert Blüte). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein artspezifischer Messwert in 2 unabhängigen seriösen Quellen belegt (CAM-Sukkulenten generell niedrig, aber keine validierte Spanne für *C. ovata*) | `species.light_compensation_point_ppfd_min` / `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | <!-- DATEN FEHLEN --> nur anekdotische Angaben zu Salzluft-Toleranz; keine quantitative Klassifizierung in 2 unabhängigen seriösen Quellen | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> kein Maas-Hoffman-Schwellenwert (a) publiziert | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein Maas-Hoffman-Slope (b) publiziert | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis (Standortqualität):** *C. ovata* wächst in voller Sonne wie im Halbschatten (full sun or semi-shade, SANBI), blüht jedoch nur bei vollsonnigem Stand zuverlässig — daher `full_sun` als Primärwert; Halbschatten wird vegetativ toleriert, führt aber zu vergeiltem ("leggy") Wuchs. Das Wurzelwerk ist flach und fleischig (Hauptmasse in den oberen 10–15 cm), was die geringe Staunässe-Toleranz (Wurzelfäule binnen Stunden bei stehendem Wasser) erklärt. Der pH-Vorzug 6.0–7.0 ist quellentreu und mit §1.6/§2.3 (Nährlösung pH 6.0–7.0) harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (vollsonniger Freilandstand; offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 (kurze Tage für Blüteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 7–13 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 12–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (vollsonniger Freilandstand; offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:2:2 (P/K-betont) | 0.4–0.8 | 6.0–7.0 | 40 | 15 | <!-- DATEN FEHLEN --> n.b. | <!-- DATEN FEHLEN --> n.b. | <!-- DATEN FEHLEN --> n.b. | <!-- DATEN FEHLEN --> n.b. |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Für *C. ovata* (extremer Schwachzehrer) sind keine artspezifischen Mn/Zn/Cu/Mo-Sollwerte (ppm) in zwei unabhängigen seriösen Quellen belegt → `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm` als DATEN FEHLEN (n.b. = nicht belegt). Mikronährstoffe werden in der Praxis über einen ausgewogenen Kakteen-/Sukkulentendünger (vgl. §3.1) als Spurenelement-Mix mitgeliefert; eine separate Dosierung ist nicht erforderlich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 3 ml/L (alle 6–8 Wochen) | Wachstum |
| Kakteen Dünger | Substral | base | 3-6-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Extremer Schwachzehrer. 2–3 Düngergaben pro Wachstumssaison ausreichend. Niemals im Winter düngen. Überdüngung führt zu weichem, anfälligem Gewebe.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; Staunässe ist häufigste Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (vor dem ersten Frost / bei Nachttemperaturen < 10 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (nach den Eisheiligen, langsam an Sonne gewöhnen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 5–15 (optimal 10–13; kühl-trocken fördert Blüteninduktion) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (vollsonniges Fenster oder Pflanzenlicht; kein Vollschatten) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | stark reduziert (alle 4–6 Wochen, nur leicht durchfeuchten; Staunässe vermeiden) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis (Überwinterung):** *C. ovata* ist nicht frosthart (Mindesttemperatur ~5 °C; SANBI nennt eine Kurzzeit-Toleranz bis −1 °C nur für die Zone-10-Freilandkultur, nicht für Mitteleuropa). Daher als frostfrei (`frost_free`) überwinternde Kübel-/Zimmerpflanze einzustufen: Im Herbst vor dem ersten Frost ins Haus holen (`move_indoors`), kühl-hell und trocken halten, im Mai nach den Eisheiligen wieder hinaus (`move_outdoors`). Der kühle, trockene Winterstand ist zugleich Voraussetzung für die Blüteninduktion (Kurztag + Kühle + Trockenheit).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste (bei sehr trockener Luft) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Weicher, verfärbter Stamm, Blätter fallen ab | Überbewässerung |
| Anthraknose | fungal | Braune, eingesunkene Flecken | Hohe Luftfeuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Schmierlaus-Zerstörer) | Cryptolaemus montrouzieri | Schmierläuse (*Pseudococcus* spp., Pseudococcidae) | 5–10 Käfer/m² (2–3 Teilausbringungen) | 2–4 Wochen |
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (*Tetranychus urticae*) | 5–20 Milben/m² (leichter Befall), bis 40/m² (starker Befall) | 1–3 Wochen |

**Hinweis (Nützlingseinsatz):** *Cryptolaemus montrouzieri* benötigt für Aktivität und Reproduktion warme Bedingungen (25–29 °C, 70–80 % rF) und ist daher v. a. im Sommerquartier / Gewächshaus wirksam, nicht im kühlen Winterstand. *Phytoseiulus persimilis* greift nur bei ausreichender Luftfeuchte — die für Spinnmilben günstige trockene Luft bremst zugleich den Räuber; ggf. Befallsherde zusätzlich anfeuchten. Beide Nützlinge sind mit dem Neemöl-Einsatz (§5.3) nicht zeitgleich zu kombinieren.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Gollum-Jade | Crassula ovata 'Gollum' | Gleiche Art, röhrenförmige Blätter | Skurrile Optik, pflegeleicht |
| Dickblatt | Crassula arborescens | Gleiche Gattung | Silbrig-grüne Blätter |
| Haworthia | Haworthiopsis fasciata | Asphodelaceae (nicht gleiche Familie) | Mehr schattenverträglich, kompakter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Crassula ovata,"Geldbaum;Pfennigbaum;Jade Plant;Money Plant",Crassulaceae,Crassula,perennial,short_day,shrub,fibrous,"10a;10b;11a;11b","Südafrika (Ostkap-Region)",yes,3-15,20,30-120,30-90,yes,yes,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Gollum,Crassula ovata,"ornamental;tubular_leaves",clone
Hobbit,Crassula ovata,"ornamental;curled_leaves",clone
Tricolor,Crassula ovata,"ornamental;variegated;green_white_pink",clone
```

---

## Quellenverzeichnis

1. [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/jade-plant-crassula-ovata/) — Kulturdaten
2. [Wikipedia — Crassula ovata](https://en.wikipedia.org/wiki/Crassula_ovata) — Taxonomie, Heimat
3. [Old Farmer's Almanac — Jade Plant](https://www.almanac.com/plant/jade-plants) — Pflegehinweise
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
5. [Joy Us Garden](https://www.joyusgarden.com/jade-plant-care/) — Vermehrung, Praxiswissen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [SANBI PlantZAfrica — Crassula ovata](https://pza.sanbi.org/crassula-ovata) — Heimat, Frosttoleranz (Min. −1 °C nur Zone 10), Licht (full sun / semi-shade), Bodenpräferenz (Photosynthese-Typ-Kontext, Schattentoleranz, Überwinterung)
7. [Wikipedia — Crassulacean acid metabolism (CAM)](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Photosynthese-Typ, VPD-Sensitivität (low)
8. [Britannica — Crassulacean Acid Metabolism](https://www.britannica.com/science/crassulacean-acid-metabolism) — CAM-Bestätigung (Photosynthese-Typ)
9. [Wisconsin Horticulture — Jade Plant (Kurztag/Blüteninduktion)](https://hort.extension.wisc.edu/articles/jade-plant-crassula-ovata/) — Kurztagblüher, lange Nächte, kühl-trockene Blüteninduktion (kritische Tageslänge)
10. [Gardener's Path — Jade Not Blooming](https://gardenerspath.com/plants/houseplants/jade-not-blooming/) — Kurztag/lange-Nächte-Bestätigung (kritische Tageslänge ~14 h Dunkelheit)
11. [GardenerBible — Do Jade Plants Like Acidic Soil](https://gardenerbible.com/do-jade-plants-like-acidic-soil/) — Boden-pH-Vorzug 6.0–7.0
12. [Greg — Best Soil for Jade Plant](https://greg.app/plant-care/soil/crassula-ovata-jade/) — Boden-pH-Vorzug (Bestätigung)
13. [Biology Insights — Do Jade Plants Have Deep Roots](https://biologyinsights.com/do-jade-plants-have-deep-roots/) — flaches, fleischiges Wurzelwerk (effektive Wurzeltiefe), Staunässe-Empfindlichkeit
14. [Greeny Gardener — Jade Plant Root System](https://greenygardener.com/jade-plant-root-system/) — Wurzeltiefe (obere 10–15 cm), Wurzelfäule durch Staunässe (Staunässe-Toleranz sensitive)
15. [ForwardPlant — Ideal Temperature for Jade Plant](https://www.forwardplant.com/care/temperature/crassula-ovata/) — Optimaltemperatur ~18–24 °C (Photosynthese-T_opt), Min. 10 °C nachts
16. [Cacti.com — Crassula ovata](https://shop.cacti.com/landscape-succulents/crassula-ovata/) — Temperaturoptimum/Standort (Bestätigung T_opt, Winterquartier)
17. [Zhen & Bugbee (2020), Far-red photons / open daylight FR-Fraction ~0.5](https://hortamericas.com/blog/science/photoperiod-and-flowering/) — Far-Red-Fraction-Anker (offenes Tageslicht/Vollsonne ≈ 0.5, R:FR ≈ 1.1; Schatten höher)
18. [Cornell NYSIPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Nützling gegen Spinnmilbe, Ausbringrate/Etablierung
19. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Spinnmilben-Räuber (Bestätigung)
20. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Schmierlaus-Zerstörer, Ausbringrate 5–10/m², Optimalbedingungen
21. [Dragonfli — Mealybug Predator Cryptolaemus montrouzieri](https://dragonfli.co.uk/products/mealybug-predator-adults-cryptolaemus-montrouzieri) — Ausbringrate gegen Schmierläuse (Bestätigung)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07-03 -->
22. [Greeny Gardener — Crassula Ovata Flowering](https://greenygardener.com/crassula-ovata-flowering/) — Kühlperiode 10–15 °C für 4–6 Wochen zur Blüteninduktion (Vernalisation Mindestdauer)
23. [Growli — Jade Plant Watering](https://www.getgrowli.app/water/jade-plant) — Wuchsverlangsamung im Herbst, stark reduziertes Gießen im Winter (Dormanz-Bestätigung)
<!-- /Quelle: growing-phase-auditor 2026-07-03 -->
