# Bogenhanf — Dracaena trifasciata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [ASPCA](https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants), [Bloomscape Care Guide](https://bloomscape.com/plant-care-guide/sansevieria/), [University of Florida IFAS](https://edis.ifas.ufl.edu/), [Royal Horticultural Society](https://www.rhs.org.uk/plants/details?plantid=4735), [NASA Clean Air Study Wolverton 1989](https://ntrs.nasa.gov/citations/19930073077)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dracaena trifasciata | `species.scientific_name` |
| Volksnamen (DE/EN) | Bogenhanf, Schwiegermutterzunge; Snake Plant, Mother-in-Law's Tongue, Saint George's Sword | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Dracaena | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> kein belegter Wuchs-/Phänologie-Basiswert für diese Zimmerpflanze auffindbar | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–25+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | Entfällt — tagneutral (day_neutral), keine kritische Tageslänge | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–27°C. Unter 10°C Kälteschäden möglich. | `species.hardiness_detail` |
| Heimat | Westafrikanische Tropen (Nigeria, Kongo, Äthiopien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.7 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, trichloroethylene, xylene, toluene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Seit 2017 offiziell in die Gattung *Dracaena* umklassifiziert (zuvor *Sansevieria trifasciata*). Der Name Sansevieria ist im Handel noch weit verbreitet und sollte als Synonym gepflegt werden. Die Art zählt zu den robustesten Zimmerpflanzen überhaupt — verträgt auch Vernachlässigung und sehr wenig Licht.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt (reine Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Entfällt | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (selten, bei Stress/Trockenheit oder reifen Pflanzen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_leaf, offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis Vermehrung:** Drei Methoden möglich: (1) Teilung des Rhizoms beim Umtopfen — schnellste Methode. (2) Blattstecklinge: 5–8 cm lange Stücke eines Blattes in Substrat stecken (dauert 2–3 Monate, verliert bei variegierten Sorten die Bänderung!). (3) Ableger (Ausläufer) am Topfrand, wenn vorhanden. Variegierte Sorten wie 'Laurentii' müssen durch Teilung vermehrt werden — Blattstecklinge produzieren grüne Nachkömmlinge.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, roots | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken:** Übelkeit, Erbrechen, Durchfall. Bei Haustieren: Speichelfluss, Erbrechen. Saponine wirken als Detergens auf die Schleimhäute. Selten lebensbedrohlich bei normalen Mengen. Quelle: ASPCA Animal Poison Control.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Beschädigte oder abgestorbene Blätter können an der Basis abgeschnitten werden. Kein regelmäßiger Rückschnitt notwendig oder sinnvoll. Blütenstand nach der Blüte entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–120 (je nach Sorte) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Monate, Halbschatten bis Sonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus-/Sukkulentenerde oder Einheitserde mit 30–40% Perlite/Sand. Sehr durchlässig, kein Staunasser Topf. Tongefäße ideal für schnellere Austrocknung. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein artspezifischer LCP-Messwert in seriösen Quellen belegt | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein artspezifischer LCP-Messwert in seriösen Quellen belegt | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> qualitativ "high" (UF/IFAS), kein quantitativer Maas-Hoffman-ECe-Schwellenwert belegt | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein Maas-Hoffman-Slope belegt | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweis Standortqualität:** Schatten-/Sonnentoleranz nach UF/IFAS "Part shade — prefers warm, sunny locations, but tolerates some shade; protect from hot afternoon sun", in Mitteleuropa (USDA 9–11 nur als Kübel-/Zimmerpflanze) entspricht das hellem, indirektem Licht. Hohe Salztoleranz (UF/IFAS: "Tolerance to soil and foliar salt exposure is high") qualitativ belegt, daher Klasse `tolerant`; ein quantitativer ECe-Schwellenwert (Bezugsgröße Substrat-ECe, nicht Gießwasser-EC) ist nicht publiziert. Boden-pH-Vorzug harmonisiert mit der pH-Angabe 6.0–7.0 in §2.3 (leicht sauer bis neutral). Staunässe-Toleranz `sensitive` wegen hoher Anfälligkeit für Wurzelfäule (vgl. §5.2).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe (Wachstumsstillstand) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.4–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 2–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–45 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–45 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.4–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:1:1 | 0.4–0.8 | 6.0–7.0 | 60 | 20 | — | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Für die Mikronährstoffe Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) liegen keine artspezifischen, zweifach belegten ppm-Zielwerte für *Dracaena trifasciata* vor. Als ausgesprochener Schwachzehrer (`light_feeder`) wird die Art mit stark verdünnter Volldüngung (1/3–1/2 Normaldosis, EC 0.4–0.8) versorgt; die im Mehrnährstoffdünger enthaltenen Mikronährstoffe genügen. Daher hier `<!-- DATEN FEHLEN -->` statt eines erfundenen Zahlenwerts. `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Winterruhe → Aktives Wachstum | time_based | März; Tageslichtstunden >12h; Temperatur stabil >16°C |
| Aktives Wachstum → Winterruhe | time_based | Oktober; Tageslichtstunden <11h |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (Halbe Normaldosis!) | 1 | Wachstum |
| Zimmerpflanzen-Dünger (stark verdünnt) | Substral | base | 7-3-7 | 3 ml/L (1/3 Normaldosis) | 1 | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil beim Umtopfen | Frühling | alle |
| Pflanzenkohle | Bio-Marken | organisch | 5% Substratanteil | Umtopfen | alle |

### 3.2 Düngungsplan

| Monat | Phase | Maßnahme | Hinweise |
|-------|-------|----------|----------|
| Apr–Aug | Aktives Wachstum | Flüssigdünger alle 6–8 Wochen | Stark verdünnte Dosis (1/3 bis 1/2 normal) |
| Sep–Mär | Winterruhe | Kein Dünger | Überdüngung bei Winterruhe ist häufiger Fehler |

### 3.3 Besondere Hinweise zur Düngung

Bogenhanf ist der archetypische Schwachzehrer — er speichert Nährstoffe in seinen sukkulenten Blättern. Überdüngung ist eine der häufigsten Ursachen für geschwächte Pflanzen und erhöhte Anfälligkeit gegenüber Wurzelfäule. Maximal 2–3 Düngergaben pro Jahr in der Wachstumsphase reichen vollständig aus. Niemals im Winter düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; Staunässe unbedingt vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb/Mär | Umtopfen prüfen | Wurzeln drängen aus dem Topf? Umtopfen in nächstgrößeren Topf | niedrig |
| Apr | Düngung starten | Erste schwache Düngergabe nach dem Winter | niedrig |
| Apr–Aug | Wässern | Substrat komplett austrocknen lassen zwischen Güssen | hoch |
| Sep | Düngung einstellen | Letzte Düngergabe der Saison | niedrig |
| Okt–Feb | Winterruhe | Sehr sparsam gießen (1x/Monat oder seltener), kein Dünger | hoch |
| Ganzjährig | Blätter reinigen | Staubige Blätter feucht abwischen (fördert Lichtaufnahme) | niedrig |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (September/Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 12–18 (min. 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; auch schwächeres Licht toleriert | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam, ca. 1×/Monat oder seltener | `overwintering_profiles.winter_quarter_watering` |

**Hinweis Überwinterung:** Nicht frosthart (USDA 9–11; in Mitteleuropa USDA 6–8 nicht winterhart). Eine im Sommer auf Balkon/Terrasse stehende Pflanze muss frostfrei im Haus überwintern (`frost_free`, nicht `dig_and_store` — es gibt keine einzulagernde Knolle). Mindesttemperatur 10°C, darunter Kälteschäden (vgl. §1.1 Winterhärte-Detail). Im Winterquartier kein Dünger, Wassergaben drastisch reduzieren, um Wurzelfäule zu vermeiden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, gelbliche Punkte | leaf | alle (besonders bei trockener Heizungsluft) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | leaf, root | alle | easy |
| Wurzelschmierlaus | Rhizoecus spp. | Kümmerwuchs, sichtbar bei Umtopfen | root | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|
| Wurzelfäule | fungal (Pythium spp.) | Weiche, braun-schwarze Basis, Blätter gelb | Überstauung, schlechte Drainage, kühle Temperaturen | Winterruhe |
| Blattbasisfäule | fungal | Weiche, gelbe Blattbasis, Geruch | Wasser in Blatttrichter + Kälte | Winterruhe |
| Rußtaupilz | fungal | Schwarzer Belag auf Honigtau | Schildlaus-/Schmierlausbefall | alle |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 0 | Schmierläuse, Spinnmilbe |
| Alkohol (70%) | mechanical | Isopropanol | Mit Wattestäbchen tupfen | 0 | Schmierläuse |
| Systeminsektizid | chemical | Imidacloprid | Stäbchen ins Substrat | 14 | Schmierläuse |
| Umtopfen | cultural | — | Befallene Erde komplett entfernen, Wurzeln abspülen | 0 | Wurzelschmierlaus, Wurzelfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit | Hinweis |
|----------|--------------------|----------------|--------------|------------------|---------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | ca. 5–10 Käfer/m² (0.5–1/sq ft), 2–3 kleinere Freilassungen | mehrere Wochen (mehrere Generationen) | Optimal 25–29°C, 70–80% rF; mehrere Teilausbringungen besser als eine Großgabe |
| Raubmilbe | Phytoseiulus persimilis | Spinnmilben (Tetranychus urticae) | ca. 5–10 Milben/m² (0.5/sq ft), wöchentlich bei Bedarf | ca. 9 Tage bis erste Populationsreduktion | Benötigt ~70% rF im Bestand; Nachsetzen empfohlen, da Räuber nach Tilgung verhungert |

**Hinweis Nützlinge:** Cryptolaemus montrouzieri ist der etablierte Gegenspieler von Weichschmierläusen (Pseudococcus), passend zum Schmierlausbefall in §5.1. Phytoseiulus persimilis bekämpft die Gemeine Spinnmilbe (Tetranychus urticae). Im Innenraum bei trockener Heizungsluft ist die für P. persimilis nötige Luftfeuchte (~70%) oft zu niedrig — dann ergänzend Luftfeuchte erhöhen oder auf Amblyseius-/Neoseiulus-Arten ausweichen. Nützlingseinsatz nicht mit chemischen Systeminsektiziden (§5.3, Imidacloprid) kombinieren.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Zamioculcas | Zamioculcas zamiifolia | 0.9 | Gleiche Pflegeansprüche (Trockenheitsverträglich, Schwachlicht) |
| Aloe vera | Aloe vera | 0.9 | Ähnliche Substrat- und Gießanforderungen |
| Kakteen | diverse | 0.8 | Identische Pflegeanforderungen möglich |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Dracaena trifasciata |
|-----|-------------------|-------------|----------------------------------------|
| Zylindrischer Bogenhanf | Dracaena angolensis (syn. Sansevieria cylindrica) | Gleiche Gattung, zylindrische Blätter | Ungewöhnlichere Optik |
| Moonshine | Dracaena trifasciata 'Moonshine' | Sorte mit silber-grünen Blättern | Hellere Blattfarbe, dekorativer |
| Hahnii | Dracaena trifasciata 'Hahnii' | Kompakte Rosettenform | Platzsparender, ideal für kleine Räume |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,air_purification_score
Dracaena trifasciata,"Bogenhanf;Schwiegermutterzunge;Snake Plant;Mother-in-Law's Tongue",Asparagaceae,Dracaena,perennial,day_neutral,herb,rhizomatous,"9a;9b;10a;10b;11a;11b",0.0,"Westafrikanische Tropen",yes,2-15,15,30-120,20-60,yes,limited,false,false,light_feeder,0.7
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Laurentii,Dracaena trifasciata,"ornamental;gold_edge_variegation",clone
Moonshine,Dracaena trifasciata,"ornamental;silver_leaves;compact",clone
Hahnii,Dracaena trifasciata,"ornamental;compact;rosette_form",clone
Black Gold,Dracaena trifasciata,"ornamental;dark_green",clone
Futura Superba,Dracaena trifasciata,"ornamental;variegated;compact",clone
```

---

## Quellenverzeichnis

1. [ASPCA Animal Poison Control](https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants) — Toxizität Saponine
2. [Bloomscape Snake Plant Care Guide](https://bloomscape.com/plant-care-guide/sansevieria/) — Pflegehinweise
3. [Royal Horticultural Society](https://www.rhs.org.uk/) — Botanische Einordnung, Kulturempfehlungen
4. [World of Succulents](https://worldofsucculents.com/how-to-grow-and-care-for-sansevieria/) — Sukkulenten-Pflegeansprüche
5. [NASA Clean Air Study (Wolverton 1989)](https://ntrs.nasa.gov/citations/19930073077) — Luftreinigungskapazität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Maréchaux et al. / ScienceDirect — Leaf succulence & Crassulacean Acid Metabolism in Sansevieria (Asparagaceae)](https://www.sciencedirect.com/science/article/abs/pii/S0367253019304931) — CAM-Photosynthese-Typ (7 von 10 untersuchten Sansevieria-Arten CAM)
7. [UF/IFAS Environmental Horticulture — Sansevieria trifasciata Fact Sheet](https://hort.ifas.ufl.edu/shrubs/SANTRIB.PDF) — Salztoleranz (hoch), Lichtbedarf (Part shade), Standortqualität
8. [UF/IFAS Extension Nassau County — Fact sheet: Sansevieria trifasciata](https://blogs.ifas.ufl.edu/nassauco/2017/06/10/fact-sheet-sansevieria-trifasciata/) — Lichtbedarf/Schattentoleranz, Substrat
9. [UF/IFAS Assessment — Sansevieria trifasciata Weed Risk Assessment](https://assessment.ifas.ufl.edu/site/assets/files/4978/sansevieria_trifasciata_wra.pdf) — Standort- und Toleranzangaben
10. [All Snake Plant — How Deep Do Snake Plant Roots Grow](https://allsnakeplant.com/how-deep-do-snake-plant-roots-grow/) — Effektive Wurzeltiefe (15–30 cm, flach, Rhizom)
11. [Cornell CALS NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Raubmilbe gegen Spinnmilben, Ausbringung/Etablierung
12. [Kansas State Research & Extension — Phytoseiulus persimilis, Biological Control Agent of the Twospotted Spider Mite (MF3665)](https://bookstore.ksre.ksu.edu/pubs/phytoseiulus-persimilis-biological-control-agent-of-the-twospotted-spider-mite_MF3665.pdf) — Ausbringrate, Etablierungszeit
13. [ScienceDirect — Cryptolaemus montrouzieri overview](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/cryptolaemus-montrouzieri) — Marienkäfer gegen Schmierläuse, Ausbringrate
14. [Biology Insights — Snake Plant Temperature Tolerance and Ideal Conditions](https://biologyinsights.com/snake-plant-temperature-tolerance-and-ideal-conditions/) — Optimaltemperatur 18–27/29°C, Mindesttemperatur 10°C
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
