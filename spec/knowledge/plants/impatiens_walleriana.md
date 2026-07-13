# Fleißiges Lieschen — Impatiens walleriana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Hortica — Impatiens walleriana](https://hortica.de/pflanzen/fleissiges-lieschen/), [Pflanzen-Kölle](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-mein-fleissiges-lieschen-richtig/), [Pflanzen-Deutschland](https://www.pflanzen-deutschland.de/Impatiens_walleriana.html), [ASPCA](https://www.aspca.org/), [Plant Addicts — Toxicity](https://plantaddicts.com/are-impatiens-poisonous/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Impatiens walleriana | `species.scientific_name` |
| Synonyme | Impatiens sultanii, Impatiens holstii | — |
| Volksnamen (DE/EN) | Fleißiges Lieschen, Springkraut; Busy Lizzie, Touch-me-not, Patient Lucy | `species.common_names` |
| Familie | Balsaminaceae | `species.family` → `botanical_families.name` |
| Gattung | Impatiens | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: Impatiens walleriana folgt nicht dem typischen linearen Blühraten-/Temperaturmodell der Beetpflanzen (Days-to-flower sinkt 14→26 °C nicht monoton, Quelle [9]); kein belegter Wuchs-GDD-Basiswert auffindbar — kein Keim-/Kardinalwert umetikettiert --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig und wiederholt blühend; frostempfindlich und daher als einjährige Kultur gezogen (cultivation_cycle_type=annual)) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Typische Lebensdauer (Jahre) | 1 (als Einjährige) oder 2–3 (überwintert als Zimmerpflanze) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutraler Blüher (day_neutral, siehe photoperiod_type), kein echter Kurztag-/Langtag-Schwellenwert — daher kein numerischer Stunden-Wert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Als Zimmerpflanze bei mindestens 15°C überwintern. Als Balkonpflanze einjährig. | `species.hardiness_detail` |
| Heimat | Ostafrika (Tansania, Mosambik) — feuchte Bergwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Das Fleißige Lieschen ist eine der beliebtesten Schatten- und Halbschatten-Balkonpflanzen Deutschlands. Es blüht pausenlos von Mai bis Oktober und benötigt kaum Pflege. Besonders wertvoll für schattige Balkon- und Terrassenstandorte, wo andere Blühpflanzen versagen. Als Zimmerpflanze kann es mit genügend Licht ganzjährig blühen. Der Volksname "Fleißiges Lieschen" bezieht sich auf die unermüdliche Blütenproduktion. Achtung: Seit 2011 grassiert der Impatiens-Falsche-Mehltau (Plasmopara obducens) in Mitteleuropa und hat viele Bestände vernichtet — Impatiens New Guinea-Hybriden sind resistent.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat Februar/März, Samen lichtkeimend) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (bis Frost) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge 7–10 cm in Wasser bewurzeln (1–2 Wochen). Samen (Lichtkeimer) auf Substrat-Oberfläche legen, nicht bedecken.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false (ASPCA: nicht gelistet als toxisch) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false (ASPCA: nicht gelistet als toxisch) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (milde Saponine und Oxalsaeure in Blaettern und Stengeln; Verzehr groesserer Mengen kann leichte Magen-Darm-Beschwerden verursachen) | `species.toxicity.toxic_compounds` |
| Schweregrad | very_low (niedrig toxisch; milde Symptome bei Verzehr groesserer Mengen moeglich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

<!-- AB-015: Impatiens walleriana ist nicht auf der ASPCA-Toxizitaetsliste, gilt aber laut Plant Addicts als niedrig toxisch. Milde Symptome (Uebelkeit, Erbrechen) nur bei Verzehr groesserer Mengen. Fuer praktische Zwecke als ungefaehrlich einzustufen. -->

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (leichter Rückschnitt für kompakteren Wuchs) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–50 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Hauptanwendung — Halbschatten!) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, humusreiche, feuchtigkeitshaltende Erde. pH 6.0–7.0. Einheitserde + 10% Kokosfaser. Regelmäßige Feuchtigkeit wichtig. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch belegter Kompensationspunkt (Netto-Photosynthese = 0) auffindbar; in Quelle [6]/[7] werden nur Sättigungs-/Photoinhibitionswerte (> 1200 µmol/m²/s) genannt, die NICHT der Kompensationspunkt sind und daher hier nicht eingetragen werden --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Schwelle (a) für Impatiens walleriana publiziert. Quelle [10] belegt nur, dass die Frischmasse bei Substrat-ECe ~7.0 dS/m bereits um ~21 % sinkt (Bezugsgröße = Substrat-Pour-Through-ECe, nicht Gießwasser-EC) → stützt Klasse moderately_sensitive --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein publizierter Maas-Hoffman-Slope (b) für die Art --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Schattenpflanze (shade) aus ostafrikanischen Bergwäldern — gedeiht von Halbschatten bis Tiefschatten (deep shade tolerant), verträgt aber keine pralle Mittagssonne (Blattverbrennung). Der pH-Optimumkorridor 6.0–6.5 (Quellen [11], [12]) liegt innerhalb des in §1.6/§2.3 genannten verträglichen Bereichs 6.0–7.0 — kein Widerspruch. Salzempfindlich (moderately_sensitive): bereits bei Substrat-ECe ~7 dS/m messbarer Frischmasseverlust (Quelle [10]).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: seed-profile-backfill 2026-07 (Batch 7) -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 29 (Optimum enger bei 22–25 °C je nach Quelle) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer — nur auf die Oberfläche legen und andrücken, nicht bedecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 5 (unterer Wert von 5–15 Tagen) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 1 (kurzlebiges Saatgut; explizit als 1-Jahres-Saatgut in Keimfähigkeits-Übersichten geführt) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | <!-- keine: keine Stratifikation/Skarifikation/Einweichen dokumentiert --> | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 0.7 (sehr feines Saatgut; ca. 1.400–1.500 Samen/g laut Saatgutpackungs-Füllgewichten, entspricht ~0,67–0,71 g/1.000 Korn) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Beetpflanze wird in Presstopf-/Multitopfplatten ausgesät, keine Flächendichte-Angabe wie bei Reihenkulturen dokumentiert --> | `species.seed_profile.sowing_density_per_m2` |

Quellen (§1.8):
1. [UMN Extension — Impatiens](https://extension.umn.edu/flowers/impatiens) — Keimtemperatur, Lichtkeimer
2. [Iowa State University Extension — How to Start Impatiens from Seed](https://yardandgarden.extension.iastate.edu/how-to/how-start-impatiens-seed) — Keimtemperatur, Keimdauer, Saattiefe/Licht
3. [Burpee — How to Grow Impatiens from Seed](https://www.burpee.com/garden-guide/ornamental-gardening/growing-impatiens-from-seed) — Keimdauer, Anzuchtbedingungen
4. [McKenzie Seeds / Harris Seeds — Impatiens-Saatgutpackungen (Füllgewicht/Samenzahl)](https://mckenzieseeds.com/products/impatiens-tropical-fizz-hybrid) — Basis der TKM-Schätzung
5. [joegardener — Seed Longevity Chart](https://joegardener.com/wp-content/uploads/2020/12/Seed-Longevity-Chart.pdf) — Keimfähigkeitsdauer 1 Jahr

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–14 | 1 | false | false | low |
| Wachstum/Blüte (Mai–Oktober) | 150–180 | 2 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum/Blüte (Mai–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06: Mn/Zn/Cu/Mo ergänzt -->
| Wachstum/Blüte | 1:2:2 | 0.8–1.4 | 6.0–7.0 | 70 | 25 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu Mikronährstoffen:** Für Impatiens walleriana sind keine artspezifischen Mn/Zn/Cu/Mo-Zielkonzentrationen (ppm) aus mindestens zwei unabhängigen seriösen Quellen belegt. Quelle [13] empfiehlt für (Sun-)Impatiens generisch ein Vollnährstoff-Mehrnährstoff-NPK mit Spurenelementen (Fe, Mn, Zn in EDTA-Form), nennt aber keine artspezifischen ppm-Werte. Daher als DATEN FEHLEN markiert statt generische Hoagland-Werte einzutragen. `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06: Mn/Zn/Cu/Mo ergänzt -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Flüssigdünger | Compo | base | 5-8-10 | 5 ml/L (alle 14 Tage) | Blüte |
| Balkonpflanzen-Dünger | Substral | base | 5-8-11 | 5 ml/L | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Blaukorn | – | mineralisch Langzeit | 3–5 g/L Substrat | einmalig beim Einpflanzen |

### 3.2 Besondere Hinweise

Mittelzehrer. Alle 14 Tage von Mai bis September. Phosphat-betonter Dünger unterstützt Blütenbildung. Sensibel gegenüber Überdüngung — halbe Empfehlungsdosis ist sicherer.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat gleichmäßig feucht halten — verträgt weder Austrocknung noch Staunässe; NIE auf Blätter gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | 10 (vor erstem Frost, Mitteleuropa) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | 5 (nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier-Temperatur (°C) | 15–18 | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier-Licht | hell, ohne pralle Sonne (Süd-/Ostfenster); Zusatzlicht fördert Winterblüte | `overwintering_profiles.winter_quarter_light` |
| Winterquartier-Gießen | sparsam, Substrat nur leicht feucht halten — keine Staunässe | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Frostempfindliche Kübel-/Zimmerpflanze (frost_sensitivity = tender, USDA 10–11). In Mitteleuropa (USDA 6–8) nicht winterhart — daher frostfreie Überwinterung im Haus (frost_free), nicht im Freiland. Vor dem ersten Frost (meist Oktober) ins helle Winterquartier bei 15–18 °C holen; bei ausreichend Licht blüht die Pflanze ganzjährig weiter. Nach den Eisheiligen (Mitte Mai) wieder nach draußen, vorher abhärten (harden off). Alternativ Stecklinge zur Überwinterung schneiden statt der ganzen Mutterpflanze.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Punkte, welke Blätter | medium |
| Blattläuse | Aphis spp. | Klebrige Triebe, Blattrollungen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Impatiens-Falscher-Mehltau | oomycete (Plasmopara obducens) | Blattunterseite weißer Belag, Blätter fallen ab | Feuchtigkeit, kühle Nächte |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel | Nässe, schlechte Belüftung |
| Wurzelfäule | fungal | Welke | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Impatiens New Guinea kaufen | cultural | Resistente Sortengruppe | 0 | Falscher Mehltau (Prävention) |
| Befallene Pflanzen entfernen | cultural | Sofort entfernen und entsorgen (kein Kompost) | 0 | Falscher Mehltau |
| Neemöl | biological | Sprühen 0.5% | 0 | Blattläuse, Spinnmilben |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (Wissenschaftl. Name) | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|--------------------------------|----------------|--------------|------------------|
| Raubmilbe (Phytoseiulus persimilis) | Gemeine Spinnmilbe (Tetranychus urticae) | 2–10 Stk./m² präventiv, bis ~20 Stk./m² im Befallsherd; RH > 70 % und > 20 °C nötig | 2–3 Wochen |
| Schlupfwespe (Aphidius colemani) | Blattläuse (Aphis spp.) | 0.5–1 Stk./m²/Woche präventiv, höher bei Befall | 2–3 Wochen |
| Gallmücke (Aphidoletes aphidimyza) | Blattläuse (Aphis spp.) | 0.2–1 Stk./m²/Woche, in Befallsherde ausbringen | 2–3 Wochen |

**Hinweis:** Nützling-Wirt-Zuordnung passend zu den unter §5.1 gelisteten Schädlingen: Phytoseiulus persimilis ist der klassische Spinnmilben-Antagonist (benötigt hohe Luftfeuchte > 70 %, daher gut für die feuchteliebende Impatiens-Kultur), Aphidius colemani parasitiert Blattläuse, Aphidoletes aphidimyza ergänzt als räuberische Gallmücke gegen Blattlaus-Herde. Nützlinge früh bei niedriger Schädlingsdichte einsetzen. Gegen den dominierenden Falschen Mehltau (Plasmopara obducens, Oomycet) gibt es KEINEN Nützling — hier greifen nur die kulturellen Maßnahmen aus §5.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Balkon-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Neuguinea-Impatiens | Impatiens hawkeri | Gleiche Gattung | Resistent gegen Falschen Mehltau |
| Wachsbegonie | Begonia semperflorens | Ähnliche Nutzung | Weniger Krankheitsanfällig |
| Fuchsia | Fuchsia x hybrida | Halbschatten-Blüher | Robuster |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Impatiens walleriana,"Fleißiges Lieschen;Springkraut;Busy Lizzie;Touch-me-not",Balsaminaceae,Impatiens,annual,day_neutral,herb,fibrous,"10a;10b;11a;11b","Ostafrika (Tansania, Mosambik)",yes,2-8,15,20-60,20-50,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Hortica — Impatiens walleriana](https://hortica.de/pflanzen/fleissiges-lieschen/) — Pflege, Kulturdaten
2. [Pflanzen-Kölle — Fleißiges Lieschen](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-mein-fleissiges-lieschen-richtig/) — Pflegetipps
3. [Pflanzen-Deutschland — Impatiens walleriana](https://www.pflanzen-deutschland.de/Impatiens_walleriana.html) — Botanische Daten
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
5. [Plant Addicts — Are Impatiens Poisonous?](https://plantaddicts.com/are-impatiens-poisonous/) — Toxizitätsdaten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NC State Extension — Impatiens walleriana](https://plants.ces.ncsu.edu/plants/impatiens-walleriana/) — Lichtbedarf (part shade to deep shade), Boden-pH, Standort (University Extension)
7. [UMN Extension — Impatiens](https://extension.umn.edu/flowers/impatiens) — Schatten-Standort, Pflege, C3-Schattenpflanzen-Charakter (University Extension)
8. [Cafe Planta — Best Soil for Impatiens](https://cafeplanta.com/a/blog/the-best-soil-for-impatiens-a-comprehensive-guide) — Boden-pH 6.0–6.5, Wurzeltiefe, Staunässe-Empfindlichkeit
9. [Blanchard & Runkle, ScienceDirect — Quantifying thermal flowering rates of bedding plants](https://www.sciencedirect.com/science/article/abs/pii/S0304423810005467) — Impatiens walleriana folgt nicht dem linearen Temperatur-/Blühratenmodell (Begründung für fehlende GDD-Basis); peer-reviewed
10. [Assessing Tolerance to Sodium Chloride Salinity in Fourteen Floriculture Species, HortTechnology 21(5) 2011](https://journals.ashs.org/horttech/view/journals/horttech/21/5/article-p539.xml) — Salzempfindlichkeit (moderately_sensitive), Frischmasseverlust ~21 % bei Substrat-ECe ~7.0 dS/m; peer-reviewed
11. [Danziger — Impatiens walleriana](https://www.danzigeronline.com/crops/impatiens-walleriana/) — Boden-pH-Optimum 6.0–6.5, Kulturhinweise (Züchter/Produktionsdaten)
12. [The Old Farmer's Almanac — Impatiens](https://www.almanac.com/plant/impatiens) — pH slightly acidic, Schatten, Wurzelsystem, Frostempfindlichkeit
13. [Greg — SunPatiens Impatiens Fertilizer](https://greg.app/sunpatiens-impatiens-fertilizer/) — Mikronährstoff-Bedarf (Fe/Mn/Zn) generisch, ohne artspezifische ppm-Werte (Beleg für DATEN-FEHLEN-Markierung)
14. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Raubmilbe gegen Spinnmilben, Ausbringraten/Bedingungen (Nützlings-Hersteller)
15. [UMass Amherst — Biological Control: Greenhouse Pests and their Natural Enemies](https://www.umass.edu/agriculture-food-environment/greenhouse-floriculture/fact-sheets/biological-control-greenhouse-pests-their-natural-enemies) — Nützling-Wirt-Zuordnung, Ausbringraten (University Extension)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
