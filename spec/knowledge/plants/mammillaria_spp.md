# Kissenkaktus, Warzenkaktus — Mammillaria spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/mammillaria/), [Gardenia.net](https://www.gardenia.net/genus/mammillaria), [World of Succulents](https://worldofsucculents.com/grow-care-mammillaria/), [Plant Care Today](https://plantcaretoday.com/mammillaria-cactus.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Mammillaria spp. (Gattung, ~147 Arten) | `species.scientific_name` |
| Volksnamen (DE/EN) | Kissenkaktus, Warzenkaktus, Nippelkaktus; Pincushion Cactus, Nipple Cactus, Fishhook Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Mammillaria | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | succulent <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher herb); Mammillaria sind Kakteen/Sukkulenten --> | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Winterdormanz für Blüteninduktion) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> (tagneutral — kein photoperiodischer Blühtrigger; Blüteninduktion über kühle, trockene Winterruhe statt Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Artabhängig — viele Arten tolerieren kurze Fröste bis -5°C (trocken). Mindesttemperatur 5°C empfohlen. Winterdormanz bei 7–13°C fördert Blüte. | `species.hardiness_detail` |
| Heimat | Mexiko, südwestliche USA — Wüsten und Halbwüsten | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Mammillaria ist eine der artenreichsten Kakteengattungen (147 akzeptierte Arten). Charakteristisch: spiralförmig angeordnete Warzen (Tuberkel) anstelle der sonst üblichen Rippen. Die kleinen, ringförmig angeordneten Blüten erscheinen an der Warzenbasis. Sehr beliebt für Einsteiger und Kakteensammlungen. Häufig angebotene Arten: M. hahniana ("Alte Dame"), M. elongata ("Fingerkaktus"), M. prolifera ("Traubenform"). Schlüssel für Blüte: kühle, trockene Winterruhe.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6, 7 (nach kühler Winterruhe, Blühbeginn mit einsetzendem aktivem Wachstum im März — oft ringförmige Blüten in Weiß/Rosa/Rot; Hauptsaison Frühjahr bis Frühsommer, einzelne Arten bis in Hoch-/Spätsommer bzw. mit zweiter Blüte im Herbst) | `species.bloom_months` |

<!-- Quelle: growing-phase-auditor 2026-07 -->
**Korrektur 2026-07 (growing-phase-auditor):** Blütemonate von `2, 3, 4, 5` auf `3, 4, 5, 6, 7` korrigiert. Der bisherige Wert widersprach der im selben Steckbrief (§2.1/§2.2) definierten Winterdormanz-Phase (Oktober–Februar) — Februar war zugleich als Dormanz- UND als Blühmonat gelistet. Fünf unabhängige Quellen belegen übereinstimmend, dass die Hauptblütezeit im Frühjahr beginnt (nicht im Winter/Februar) und bis in den Sommer reicht: (1) NC State Extension — Winterdormanz "encourages spring flowering", Blüte einzelner Arten (z. B. M. longimamma) im Frühjahr; (2) World of Succulents (Artenseiten) — M. bocasana "spring and summer", M. hahniana "spring and summer, occasionally a second bloom in autumn", M. longimamma/M. carnea/M. spinosissima/M. melaleuca "late spring to early/mid summer"; (3) gartenjournal.net — "Frühjahr bis Sommer, einige bis Herbst"; (4) Plant Care Today — "spring and early summer" nach Winterruhe; (5) Pflanzenfreunde.com — Hauptblühsaison "Frühjahr bis Herbst" nach mind. 16-wöchiger Ruheperiode (Okt–März). Keine der fünf Quellen nennt Februar als typischen Blühbeginn für die Kultur (nur eine Quelle nennt Februar als Extremrand der Gesamtspanne über alle ~147 Arten, nicht als Regelfall). Der neue Wert (März–Juli) beginnt konsistent mit dem Start der Aktives-Wachstum-Phase (§2.2: März–September) und deckt die in allen Quellen übereinstimmend genannte Kernsaison Frühjahr/Frühsommer ab; spätsommerliche/herbstliche Nachblüte einzelner Arten bleibt als Artvariation im Freitext dokumentiert statt in `bloom_months` aufgenommen (Konsistenz mit Genus-Aggregat-Konvention). Konfidenz: ✅ GESICHERT (5/5 Quellen stimmen überein).
<!-- /Quelle: growing-phase-auditor 2026-07 -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) im Frühjahr/Sommer abtrennen, 1–2 Tage Schnittstelle trocknen lassen, in trockenes Kakteensubstrat pflanzen. Samen bei 22–28°C, Keimung in 1–3 Wochen.

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

**Hinweis:** Nicht giftig — aber mechanische Verletzungsgefahr durch Stacheln! Stacheln können sich in Haut einbohren. Gartenhandschuhe beim Umtopfen verwenden.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.3–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–30 (artabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 3–20 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, trocken, frostfreie Monate oder frosttolerant je Art) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde mit 50–70% mineralischem Material (Perlite, grober Sand, Bimssplit). pH 6.0–7.0. Hervorragende Drainage zwingend. Flache Tontöpfe bevorzugt. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 40 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 5–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> (keine artspezifische Maas-Hoffman-Schwelle für Mammillaria belegt; Gattung gilt qualitativ als salzempfindlich) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Mammillaria betreibt obligaten Crassulaceen-Säurestoffwechsel (CAM, Crassulacean Acid Metabolism) — Stomata öffnen nachts, was den Lichtkompensationspunkt nicht im klassischen Tagesmittel-Sinn definiert; die angegebene Spanne (10–40 µmol/m²/s) entspricht dem für Wüsten-CAM-Sukkulenten typisch sehr niedrigen Kompensationsbereich. Lichtsättigung der nächtlichen CO₂-Fixierung wird erst bei hohen Tages-PAR-Summen (≈ 20–22 mol/m²/Tag) erreicht (Nobel; gehört NICHT in das Kompensationspunkt-Feld). Wurzelsystem flach und faserig (oberste ~5–15 cm) — passt zur Strategie, kurze Oberflächenfeuchte schnell aufzunehmen. Wegen Wasserspeichergewebe extrem staunässe- und (qualitativ) salzempfindlich. Boden-pH-Vorzug konsistent mit §1.6 und §2.3 (pH 6.0–7.0).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 (§1.3 bereits 22–28°C; Fachliteratur nennt konsistent 20–30°C) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 30 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer; Samen nur auf Substratoberfläche auflegen, nicht bedecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 5 (Radikula-Austritt innerhalb 5–10 Tagen bei Mammillaria als vergleichsweise schnellem Keimer; Keimung erfolgt in Schüben mit langen Intervallen) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 5 (praktische Nutzungsgrenze — nach 5 Jahren Lagerung sinkt die Keimrate spürbar; bei optimaler trockener/kühler/dunkler Lagerung sind Jahrzehnte möglich) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light (direktes Licht für zuverlässige, gleichmäßige Keimung erforderlich; Keimung im Dunkeln/Halbschatten ungleichmäßig bis faulend) | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (keine Stratifikation/Skarifikation erforderlich; einzelne großblütige Arten zeigen einen artspezifischen "Keimbarriere"-Effekt, der durch Trocknen/Neuversuch, nicht durch klassische Vorbehandlung, überwunden wird) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: kein belegter TKG-Wert für Mammillaria spp. aus zwei unabhängigen Quellen auffindbar --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Aussaat erfolgt in Anzuchtschalen/Töpfen, keine Flächen-/Reihensaat --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
1. [Plant Grower World — Germinate Cactus Seeds Like a Pro](https://plantgrowerworld.com/germinating-cactus-seeds-guide/) — Keimtemperatur 21–27°C (70–80°F), Keimdauer 1–2 Wochen, Lichtbedarf
2. [Koehres-Kakteen — Sowing Instructions](https://www.kaktus-koehres.de/Downloads/sowing_instructions.pdf) — Aussaat auf Substratoberfläche, direktes Licht erforderlich, Keimtemperatur 20–30°C
3. [OBLOG (Opuntiads) — Cactus Seed Responses to Temperature](https://opuntiads.com/oblog/cactus-seed-responses-to-temperature/) — Mammillaria als schneller Keimer (Radikula binnen 5–10 Tagen), Keimung in Schüben
4. [UnusualSeeds — How To Grow Mammillaria From Seeds](https://unusualseeds.net/how-to-grow-mammillaria-from-seeds/) — Keimfähigkeitsprüfung, artspezifische Keimbarriere bei großblütigen Arten (Trocknen/Neuversuch)
5. [CactiGuide.com Forum — Seed viability](https://cactiguide.com/forum/viewtopic.php?t=21450) — Keimfähigkeit nach 5 Jahren Lagerung deutlich reduziert; Jahrzehnte bei optimaler Lagerung möglich
6. §1.3 dieses Steckbriefs (bereits zitierte Quelle: Samen bei 22–28°C, Keimung 1–3 Wochen) — Cross-Check Keimtemperatur/-dauer
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterdormanz | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–2000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–55 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 10–30 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–3.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 3.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterdormanz (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 6–15 | `requirement_profiles.dli_target_mol` |
| VPD-Schwelle (kPa) | 2.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 10–15 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 7–13 (kühle Winterruhe) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–10 | `requirement_profiles.temperature_night_c` |
| Gießintervall (Tage) | 42–90 (fast trocken) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0–20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.0–7.0 | 30 | 10 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterdormanz | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Für Mammillaria sind keine artspezifischen Mikronährstoff-Sollwerte (Mn/Zn/Cu/Mo in ppm) aus mindestens zwei unabhängigen seriösen Quellen belegt. Als sehr leichter Zehrer (`light_feeder`) deckt ein vollständiger Kakteen-/Sukkulentendünger mit Spurenelementen den Bedarf in Halbdosis ab; quantitative Phasen-Sollwerte bleiben mangels Beleg als `<!-- DATEN FEHLEN -->` markiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (alle 4–6 Wochen) | Wachstum |
| Kakteendünger | Substral | base | 3-6-7 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 5% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Alle 4–6 Wochen April bis September, halbe Empfehlungsdosis. Oktober bis März: kein Dünger. Überdüngung fördert "Weichheit" und verringert Stacheln-Qualität.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 (extrem wenig im Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; vollständig durchgießen, dann KOMPLETT abtrocknen; im Winter fast komplett trocken | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors (helles, kühles Zimmer) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken an Stacheln und Warzen | easy |
| Spinnmilbe | Tetranychus urticae | Braune Punkte, Gespinste (selten) | difficult |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal/bacterial | Weicher, brauner Stammsockel | Überwässerung, bes. im Winter |
| Schorf | fungal | Braune Flecken auf Körper | Hohe Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Gießintervall verlängern | 0 | Wurzelfäule (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen (vorsichtig wegen Stacheln) | 0 Tage | Schmierlaus, Schildlaus |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10 Käfer/m² (bei Befall 10–20/m²), 2–3 Freilassungen im Abstand von 1–2 Wochen | 2–4 Wochen; optimal bei 25–28 °C |
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–50 Milben/m² je nach Befallsdichte, 1–2 Freilassungen im Wochenabstand | 1–3 Wochen; wirksam 13–27 °C, rF > 70 % |

**Hinweis:** Phytoseiulus persimilis benötigt eine relative Luftfeuchte über 70 % und ist daher unter den für Mammillaria typischen trockenen Bedingungen nur eingeschränkt brauchbar — bei niedriger rF auf Neoseiulus/Amblyseius-Arten oder mechanische Bekämpfung ausweichen. Cryptolaemus montrouzieri ist gegen Schmierläuse die robustere Wahl für Sammlungen. Beide Nützlinge eignen sich primär für Gewächshaus-/Innenraum-Bestände.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze/Balkonpflanze (Sukkulenten-Arrangement).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Echinopsis | Echinopsis spp. | Cactaceae, Kugelkaktus | Größere, spektakuläre Blüten |
| Gymnocalycium | Gymnocalycium spp. | Cactaceae, Kugelkaktus | Toleriert Halbschatten |
| Feigenkaktus | Opuntia spp. | Cactaceae | Rustikaler, flache Glieder |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Mammillaria spp.,"Kissenkaktus;Warzenkaktus;Nippelkaktus;Pincushion Cactus;Nipple Cactus",Cactaceae,Mammillaria,perennial,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b","Mexiko, südwestliche USA",yes,0.3-2,8,5-30,3-20,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [NC State Extension — Mammillaria](https://plants.ces.ncsu.edu/plants/mammillaria/) — Botanische Daten, USDA-Zonen
2. [Gardenia.net — Mammillaria](https://www.gardenia.net/genus/mammillaria) — Gattungsübersicht
3. [World of Succulents — Mammillaria](https://worldofsucculents.com/grow-care-mammillaria/) — Kulturdaten
4. [Plant Care Today — Mammillaria](https://plantcaretoday.com/mammillaria-cactus.html) — Schädlinge, Pflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Foliage Factory — CAM Photosynthesis](https://www.foliage-factory.com/post/nighttime-photosynthesis-how-cam-plants-thrive-on-scarcity) — CAM-Stoffwechsel, nächtliche Stomata-Öffnung (Photosynthese-Typ)
7. [Cervera et al. 2007, Biotropica — Photosynthesis and Optimal Light Microhabitats for Mammillaria gaumeri](https://onlinelibrary.wiley.com/doi/10.1111/j.1744-7429.2007.00311.x) — obligater CAM, optimale Lichtmikrohabitate (60–80 % bzw. 20 % Umgebungs-PPFD), Lichtbedarf
8. [Garcia-Moya & Nobel u.a., PMC — PAR, nächtliche Säureakkumulation und CO₂-Aufnahme bei Opuntia ficus-indica (CAM)](https://pmc.ncbi.nlm.nih.gov/articles/PMC1065988/) — Lichtsättigung der CAM-CO₂-Fixierung bei ≈ 20–22 mol/m²/Tag PAR
9. [Nobel — Shifts in the optimal temperature for nocturnal CO₂ uptake (Cacti/Agaves)](https://www.researchgate.net/publication/230020026_Shifts_in_the_optimal_temperature_for_nocturnal_CO2_uptake_caused_by_changes_in_growth_temperature_for_cacti_and_agaves) — T_opt nächtliche CO₂-Aufnahme 11–23 °C (wachstumstemperaturabhängig); Ferocactus ≈ 12,6 °C (Photosynthese-T_opt)
10. [SuccipulentCareHub — How Deep Do Cactus Roots Go](https://succulentcarehub.com/how-deep-do-cactus-roots-go/) — flaches, faseriges Wurzelsystem (oberste ~5–10 cm); effektive Wurzeltiefe
11. [PlanetDesert — Cactus Soil Guide](https://planetdesert.com/blogs/news/cactus-soil-guide-everything-you-need-to-know) — Boden-pH 5,5–7,0 (Zielwert ~6,0), schnelle Drainage, Staunässe-Empfindlichkeit
12. [Schuch & Kelly — Salinity Tolerance of Cacti and Succulents](https://www.semanticscholar.org/paper/Salinity-Tolerance-of-Cacti-and-Succulents-Schuch-Kelly/ebde84504c21858024b88ba9006d7ec05ca6fa4f) — Wachstumsrückgang von Kakteen mit steigender Bewässerungs-EC (Salzempfindlichkeit, qualitativ)
13. [Koppert — Cryptolaemus montrouzieri (Mealybug destroyer)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate gegen Schmierläuse, Etablierungsbedingungen
14. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate gegen Spinnmilben, Temperatur-/rF-Wirkbereich
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
15. [World of Succulents — Mammillaria bocasana, hahniana, longimamma, carnea, spinosissima, melaleuca (Artenseiten)](https://worldofsucculents.com/) — Blütezeitraum je Art (Frühjahr–Frühsommer/Sommer, teils Herbst-Nachblüte)
16. [gartenjournal.net — Mammillaria](https://www.gartenjournal.net/mammillaria) — Blütezeit "Frühjahr bis Sommer, einige bis Herbst"; Winterruhe-Anforderungen; Frosttoleranz einzelner Arten (z. B. M. crinita bis -2 °C)
17. [Pflanzenfreunde.com — Mammillaria](https://www.pflanzenfreunde.com/lexika/kakteen/mammillaria.htm) — Hauptblühsaison "Frühjahr bis Herbst"; Mindest-Ruheperiode 16 Wochen (Okt–März, 6–10 °C) als Blühinduktions-Voraussetzung
<!-- /Quelle: growing-phase-auditor 2026-07 -->
