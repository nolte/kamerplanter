# Elefantenfuß, Pferdeschwanzpalme — Beaucarnea recurvata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/ponytail-palm-beaucarnea-recurvata-care-guide-2/), [OurHouseplants](https://www.ourhouseplants.com/plants/ponytailpalm), [Gardenia.net](https://www.gardenia.net/plant/beaucarnea-recurvata-pony-tail-palm), [PLNTS.com](https://plnts.com/en/care/houseplants-family/beaucarnea), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Beaucarnea recurvata | `species.scientific_name` |
| Volksnamen (DE/EN) | Elefantenfuß, Pferdeschwanzpalme, Flaschenpalme; Ponytail Palm, Elephant Foot, Bottle Palm | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Beaucarnea | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 50–350+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | <!-- DATEN FEHLEN --> (CAM-plausibel: caudiciformer Sukkulent, aber für Beaucarnea/Nolinoideae nicht aus 2 unabhängigen Quellen belegt; CAM ist in Asparagaceae bislang v.a. für Agavoideae und Sansevieria/Dracaena dokumentiert) | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> (wärmeliebende subtropische Art ohne publizierten GDD-Basiswert) | `species.base_temp` |
| Kritische Tageslänge (h) | — (tagneutral, kein Kurztag-/Langtagverhalten) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b <!-- Quelle: growing-phase-auditor 2026-07 (Korrektur: war 9a-11b) --> | `species.hardiness_zones` |
| Frostempfindlichkeit | tender <!-- Quelle: growing-phase-auditor 2026-07 (Korrektur: war half_hardy) --> | `species.frost_sensitivity` |
| Winterhaerte-Detail | Frostempfindlich (tender) — nicht winterhart, verträgt keine dauerhaften Fröste; laut UF/IFAS und NC State Extension nur bis USDA Zone 10 (praktische Kälteschwelle ca. 10°C/50°F) kultivierbar. Ausgewachsene Exemplare können kurzzeitig Temperaturen bis etwa -5 bis -9°C ohne Absterben überstehen, jedoch mit Frostschäden (braune/schwarze Blattspitzen, Stammfäule) — dies ist keine geeignete Überwinterungsstrategie. Mindesttemperatur im Kübel 5°C, optimal 15–29°C. Verträgt Trockenheit sehr gut. <!-- Quelle: growing-phase-auditor 2026-07 (Korrektur: war "Halbfrosthart... bis -5°C") --> | `species.hardiness_detail` |
| Heimat | Östliches Mexiko (Tamaulipas, San Luis Potosí) — trockene Halbwüste, Felsspalten | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Elefantenfuß ist KEINE Palme (trotz des Namens), sondern ein Verwandter der Agaven. Die verdickte Stammbasis dient als Wasserspeicher — daher kann die Pflanze Wochen ohne Wasser überleben. Extrem langsam wachsend (ca. 15 cm/Jahr unter idealen Bedingungen). In Mexiko werden die Blätter als Viehfutter genutzt und die Pflanze ist wildlebend in Mexico als gefährdet eingestuft.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht erst nach Jahrzehnten; nur bei sehr alten, großen Exemplaren im Freiland) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) an der Stammbasis abtrennen (5+ cm groß), Schnittfläche trocknen lassen (1–2 Tage), in trockenes Kakteensubstrat pflanzen. Wurzelbildung in 4–8 Wochen bei 22–26°C. Samen ebenfalls möglich, aber sehr langsam.

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
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Beaucarnea recurvata ist nicht giftig — ASPCA listet die Pflanze als sicher für Katzen und Hunde.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Abgestorbene Blätter vorsichtig von der Basis abziehen. Blätter niemals schneiden — Enden werden braun und sehen unschön aus.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (indoor, sehr langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, frostfreie Monate; im Sommer draußen empfehlenswert) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde oder Einheitserde mit 50% Perlite/Grobsand. pH 6.5–7.5. Hervorragende Drainage zwingend erforderlich. Tongefäße bevorzugt (verhindert Überwässerung). Kleiner Topf (root-bound ist gut). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (kein artspezifischer Messwert in seriösen Quellen) | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–40 (flachwurzelnd; Wasserspeicher im verdickten Stammsockel/Caudex, nicht in tiefen Wurzeln) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> (kein Maas-Hoffman-Substrat-ECe-Wert belegt; UF/IFAS gibt nur „aerosol salt tolerance: moderate" = Sprühsalz, nicht Boden-ECe) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug | 6.5–7.5 | `species.soil_ph_preference` |

**Hinweis:** Wuchs in voller Sonne bis Halbschatten (partial shade); im Freiland (USDA 10–11) bevorzugt volle Sonne, im Zimmer hell-indirekt. Extrem nässeempfindlich — Wurzelfäule (root rot) auf schlecht drainierten/nassen Böden ist die häufigste Todesursache, daher `waterlogging_tolerance = sensitive`. Salzaufbau aus hartem Gießwasser oder Überdüngung verursacht Blattspitzennekrosen (`moderately_sensitive`); die von UF/IFAS genannte „moderate" Toleranz bezieht sich ausschließlich auf Aerosol-/Sprühsalz an Küstenstandorten, nicht auf Substrat-Salzgehalt. Der pH-Vorzug 6.5–7.5 ist konsistent mit der Substrat-Empfehlung in §1.6 und den Nährstoffprofilen in §2.3; UF/IFAS und NC Extension bestätigen Toleranz gegenüber leicht sauren bis alkalischen Böden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: Seed-Profile-Backfill Batch 3 (2026-07-04) -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 18 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 27 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Oberflächensaat, nur leicht andrücken/halb einbetten) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14–56 (KA-Feld: 14) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | <!-- DATEN FEHLEN: qualitativ übereinstimmend als kurzlebig beschrieben (deutlicher Rückgang bereits nach wenigen Monaten; bei Kühllagerung laut einer Quelle bis ca. 2 Jahre), aber kein belastbarer Einzelwert aus ≥2 Quellen --> | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak, scarification | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: keine Angabe aus ≥2 seriösen Quellen auffindbar --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: reine Topf-/Zimmerpflanze, keine Reihen-/Direktsaat mit Feld-Enddichte --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):** [Live to Plant — Ponytail Palm Plant Seeds: Guide to Storing, Sowing and Germination](https://livetoplant.com/ponytail-palm-plant-seeds-guide-to-storing-sowing-and-germination/); [World of Succulents — Beaucarnea recurvata](https://worldofsucculents.com/beaucarnea-recurvata/); [Gardening Know How — Harvesting Ponytail Palm Seeds](https://www.gardeningknowhow.com/houseplants/ponytail-palm/propagating-ponytail-palm-seeds.htm); [Garden Guides — How To Plant Ponytail Palm Seeds](https://www.gardenguides.com/90683-plant-ponytail-palm-seeds/); [Foliage Factory — Ponytail Palm Care Guide](https://www.foliage-factory.com/post/the-ultimate-guide-to-beaucarnea-recurvata).
<!-- /Quelle: Seed-Profile-Backfill Batch 3 (2026-07-04) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–1000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 3.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–29 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–30 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.5–7.5 | 40 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.5–7.5 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo):** Für Beaucarnea recurvata liegen keine artspezifischen Mikronährstoff-Zielwerte aus seriösen Quellen vor — <!-- DATEN FEHLEN --> für `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm` und `nutrient_profiles.molybdenum_ppm`. Als extremer Schwachzehrer (light_feeder) deckt ein vollständiger Kakteen-/Sukkulentendünger mit Spurenelementen (siehe §3.1) den Bedarf ab; eine gezielte Einzeldosierung ist nicht belegt und wird nicht erfunden.
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

Extremer Schwachzehrer. Nur 2–4 Düngergaben pro Wachstumssaison ausreichend. Niemals im Winter düngen. Überdüngung schadet dauerhaft.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; vollständig durchgießen, dann KOMPLETT abtrocknen lassen bis zur nächsten Wässerung | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (September–Oktober, vor erstem Frost / unter 5–7 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 13–18 (Minimum 5–10 °C; unter 5 °C drohen Schäden) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (heller Standort, hell-indirekt bis sonnig) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam (nahezu trocken; nur so viel, dass die Blätter nicht welken) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Frostempfindliche Kübel-/Zimmerpflanze (USDA 10–11); in Mitteleuropa (USDA 6–8) nicht winterhart und muss frostfrei drinnen überwintern (`frost_free`) — kein Ausgraben/Einlagern und kein Vlies-/Erdschutz im Freiland. Während der kühlen Winterruhe (November–Februar) trockener und kühler halten, was das natürliche Trockenklima nachahmt. Kurze Fröste bis etwa −5 °C werden ausnahmsweise toleriert, sind aber kein Dauerzustand und nicht als Überwinterungsstrategie geeignet.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste (selten) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Weicher, verfärbter Stammsockel | Überwässerung, Staunässe |
| Blattendfäule | fungal | Braune Blattspitzen | Überwässerung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Gießintervall erhöhen | 0 | Wurzelfäule (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 1–10 Käfer/m² bzw. 2–5 pro befallene Pflanze, ggf. mehrere Ausbringungen | 2–3 Wochen (aktiv über 2–3 Monate) |
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m² je nach Befall, wöchentlich wiederholen | 1–2 Wochen |

**Hinweis:** *Cryptolaemus montrouzieri* ist auch im Innenraum/Interiorscape gegen Schmierläuse wirksam und arbeitet am besten bei warmen Bedingungen (April–Oktober). *Phytoseiulus persimilis* benötigt > 70 % Luftfeuchte und Temperaturen 13–27 °C — die für den Elefantenfuß typische trockene Raumluft (20–40 % rel. F., siehe §2.2) ist suboptimal; unter trockenen Bedingungen ist die trockentolerantere Raubmilbe *Amblyseius (Neoseiulus) californicus* die robustere Alternative. Spinnmilbenbefall ist bei dieser Art ohnehin selten (siehe §5.1).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Yucca | Yucca elephantipes | Asparagaceae, Baumform | Ähnlicher tropischer Look |
| Drachenbaum | Dracaena marginata | Asparagaceae, Baumform | Mehr Blattfarben, kompakter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Beaucarnea recurvata,"Elefantenfuß;Pferdeschwanzpalme;Flaschenpalme;Ponytail Palm;Elephant Foot",Asparagaceae,Beaucarnea,perennial,day_neutral,tree,tuberous,"9a;9b;10a;10b;11a;11b","Östliches Mexiko",yes,3-15,20,60-200,40-100,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Ponytail Palm](https://www.healthyhouseplants.com/indoor-houseplants/ponytail-palm-beaucarnea-recurvata-care-guide-2/) — Pflegehinweise
2. [OurHouseplants — Ponytail Palm](https://www.ourhouseplants.com/plants/ponytailpalm) — Detaillierte Kulturdaten
3. [Gardenia.net — Beaucarnea recurvata](https://www.gardenia.net/plant/beaucarnea-recurvata-pony-tail-palm) — Botanische Daten
4. [PLNTS.com — Beaucarnea](https://plnts.com/en/care/houseplants-family/beaucarnea) — Ganzjahrespflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [UF/IFAS — Beaucarnea recurvata: Ponytail Palm (ENH252/ST093)](https://ask.ifas.ufl.edu/publication/ST093) — Licht (full sun to partial shade), pH-Toleranz (sauer/alkalisch), Aerosol-Salztoleranz (moderate), Trockenheitstoleranz (high), Wurzelfäule auf nassen Böden, USDA 10A–11
7. [North Carolina Extension Gardener Plant Toolbox — Beaucarnea recurvata](https://plants.ces.ncsu.edu/plants/beaucarnea-recurvata/) — Licht (full sun), Drainage (Good Drainage / Occasionally Dry), Trockenheitsresistenz, USDA 10a–11b
8. [Missouri Botanical Garden — Beaucarnea recurvata Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=282253) — volle Sonne, Wasserbedarf trocken–mittel, sandige Böden mit scharfer Drainage, USDA 10–11
9. [New York Botanical Garden — Houseplant Care: Ponytail Palm](https://libguides.nybg.org/ponytail) — Überwinterung, Winterruhe November–Februar, sparsames Wintergießen
10. [University of Wisconsin Horticulture — Ponytail Palm, Beaucarnea recurvata](https://hort.extension.wisc.edu/articles/ponytail-palm-beaucarnea-recurvata/) — Winterquartier 13–18 °C, Mindesttemperatur, flaches Wurzelsystem, Pflege
11. [Yang et al. (2016), Molecular Phylogenetics and Evolution — Evolution of CAM anatomy in the Agavoideae (Asparagaceae)](https://www.sciencedirect.com/science/article/abs/pii/S1055790316302111) — CAM in Asparagaceae auf Agavoideae bezogen; belegt, dass CAM für Beaucarnea/Nolinoideae NICHT pauschal angenommen werden kann
12. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Schmierläuse, Ausbringrate, Innenraumeignung
13. [Cornell NYSIPM Biocontrol Fact Sheet — Phytoseiulus persimilis](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Raubmilbe gegen Spinnmilben, Ausbringrate, Temperatur-/Feuchteansprüche
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: growing-phase-auditor 2026-07 (Korrektur USDA-Zonen & Frostempfindlichkeit) -->
14. [UF/IFAS — Beaucarnea recurvata: Ponytail Palm (ENH252/ST093)](https://ask.ifas.ufl.edu/publication/ST093) — USDA Zone 10A–11 (bestätigt erneut, kein Zonen-9-Beleg)
15. [NC State Extension Gardener Plant Toolbox — Beaucarnea recurvata](https://plants.ces.ncsu.edu/plants/beaucarnea-recurvata/) — USDA Zone 10a–11b, "hardy to 50 degrees F" (10°C) — keine Frosttoleranz im Normalfall, Kübelhaltung mit Winterquartier nötig
16. [Missouri Botanical Garden — Beaucarnea recurvata Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=282253) — Zone 10 bis 11, außerhalb dieser Zonen ausschließlich als Zimmerpflanze kultiviert
17. [Epic Gardening — 5 Tips to Grow a Ponytail Palm Outdoors](https://www.epicgardening.com/growing-ponytail-palm-outdoors/) — USDA Zone 10–11; kurzzeitige Toleranz bis -9°C (15°F) mit Frostschäden, Umzug ins Winterquartier ab unter 7°C (45°F) erforderlich
<!-- /Quelle: growing-phase-auditor 2026-07 (Korrektur USDA-Zonen & Frostempfindlichkeit) -->
