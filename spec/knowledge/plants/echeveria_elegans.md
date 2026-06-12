# Mexikanische Schneekugel — Echeveria elegans

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Old Farmer's Almanac](https://www.almanac.com/plant/complete-guide-growing-and-caring-echeveria-succulents), [Epic Gardening](https://www.epicgardening.com/haworthia-attenuata/), [Plant Care Today](https://plantcaretoday.com/echeveria-elegans.html), [Gardens Whisper](https://gardenswhisper.com/echeveria-elegans-care-propagation/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Echeveria elegans | `species.scientific_name` |
| Volksnamen (DE/EN) | Mexikanische Schneekugel, Glashausrose; Mexican Snowball, Mexican Gem, White Mexican Rose | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Echeveria | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Echeveria elegans auffindbar; CAM-Sukkulente ohne publizierte Wuchs-GDD-Basis --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 3–10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — toleriert kurze Fröste bis -5°C. Mindesttemperatur 5°C, optimal 18–27°C. Kühle Winter (10–15°C) fördert Blütenbildung. | `species.hardiness_detail` |
| Heimat | Mexiko (Hidalgo) — Felsen und trockene Hänge | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Echeveria elegans ist wegen ihrer perfekten, symmetrischen Rosettenform eine der beliebtesten Sukkulenten. Die bläulich-silberne Blattfarbe (durch Wachsschicht, sog. Farina) ist besonders attraktiv. Die Farina niemals mit den Fingern berühren — einmal weg, wächst sie nicht nach. Sehr beliebt für Hochzeitsdekorationen, Sukkulenten-Arrangements und Terrarien.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (rosa-rote Glöckchenblüten auf langen Stängeln) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_leaf, offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Blattstecklinge: Einzelne, gesunde Blätter mit sanftem Drehen abtrennen (sauber von der Basis lösen!), 2–3 Tage trocknen lassen, dann flach auf feuchtes Substrat legen — nicht stecken! Bewurzelung und neue Rosette in 4–8 Wochen. Ableger einfach abtrennen.

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

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | deadheading | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (verblühte Stängel entfernen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.3–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 6 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 8–15 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 8–30 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, frostgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde mit 30% Perlite/Sand. pH 6.0–7.0. Flache Töpfe bevorzugt. Excellent Drainage. Tongefäß empfohlen. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer, peer-reviewter Kompensationspunkt (Netto-Photosynthese = 0) für Echeveria elegans auffindbar --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: keine quantitative Maas-Hoffman-Schwelle (a) für Echeveria elegans belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope (b) für Echeveria elegans belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Echeveria elegans ist eine Vollsonnenpflanze (full sun) aus bright/semi-desert-Habitaten Mexikos; benötigt ganzjährig hohe Lichtmengen, etioliert (vergeilt) bei Lichtmangel. Fibröses, flach-horizontal streichendes Wurzelsystem (shallow, fibrous) — die effektive Wurzeltiefe (effective root depth) liegt bei ca. 15–30 cm, weshalb flache, breite Gefäße bevorzugt werden. Sehr empfindlich gegenüber Staunässe (waterlogging) — schon kurze Nässephasen führen zu Wurzelfäule. Als Sukkulente mit empfindlicher Salzreaktion (salt-sensitive) wird Düngung niedrig dosiert (EC 0.3–0.6 mS); die fehlenden Maas-Hoffman-Kennwerte (ECe-Schwelle, Slope) sind in der Literatur für die Art nicht quantifiziert. Boden-pH-Vorzug 6.0–7.0 harmonisiert mit der Substrat-Empfehlung in §1.6 und den Phasen-Nährstoffprofilen in §2.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–180 | 1 | false | false | high |
| Winterruhe | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 3.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 10–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 21–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 15–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.0–7.0 | 30 | 10 | 0.5 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.02 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.01 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Mn/Zn/Cu/Mo sind als Spurenelement-Standardgehalte (trace micronutrients) einer vollständigen Hoagland-&-Arnon-Nährlösung angegeben (Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.01 ppm). Als extrem leichter Zehrer (light feeder) werden diese Werte nur in der aktiven Wachstumsphase und stark verdünnt (EC 0.3–0.6 mS) ausgebracht; in der Winterruhe entfällt jede Düngung (0:0:0).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (1×/Saison im Frühjahr) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Extrem leichter Zehrer. 1–2 Düngergaben im Frühjahr vollständig ausreichend. Niemals im Winter düngen. Stickstoffarme, P-K-reiche Formel (Kakteendünger) ist ideal.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; NIEMALS auf Blätter gießen (Farina zerstören, Fäule); vollständig abtrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–5 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–15 | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (bright) — Süd-/Westfenster, mind. 6 h helles Licht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam, alle 21–42 Tage, vollständig abtrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Echeveria elegans ist frostempfindlich (frost-tender) und überwintert in Mitteleuropa (USDA 6–8) frostfrei drinnen (frost_free) — als Kübel-/Zimmerpflanze, NICHT im Freiland ausgepflanzt. Im Herbst (Oktober) vor dem ersten Frost ins helle, kühle Winterquartier (10–15 °C) holen; die kühle, helle Überwinterung fördert zudem die Blütenbildung im Frühjahr. Im Mai nach den Eisheiligen wieder an einen frostgeschützten, vollsonnigen Balkon-/Terrassenplatz stellen (schrittweise an direkte Sonne gewöhnen, um Sonnenbrand zu vermeiden). Kurzzeitige leichte Fröste bis ca. −5 °C werden zwar toleriert, eine sichere Überwinterung ist jedoch nur frostfrei gewährleistet.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Rosettenfäule | fungal | Braune, matschige Rosettenmitte | Wasser auf Blätter, hohe Feuchtigkeit |
| Wurzelfäule | fungal | Welke, verfärbte Basis | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Nie auf Blätter gießen | cultural | Gießtechnik ändern | 0 | Rosettenfäule (Prävention) |
| Neemöl | biological | Bodenbehandlung (Gießen) | 0 | Trauermücke |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|-----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | ~10 Käfer/m² (≈ 1/sq ft); bei Befall 2–5 pro Pflanze | 3–6 Wochen (optimal bei ~27 °C; April–Oktober) |
| Insektenpathogene Nematoden | Steinernema feltiae | Trauermücke (Bradysia spp.), Larven | 0,5 Mio. infektiöse Juvenile/m² (Gießanwendung) | 1–2 Wochen (Boden feucht, 10–28 °C) |
| Raubmilbe | Stratiolaelaps scimitus (syn. Hypoaspis miles) | Trauermücke (Bradysia spp.), Larven/Puppen | ~250 Milben/m² (Streuanwendung aufs Substrat) | 2–4 Wochen |

**Hinweis:** Nützlingseinsatz ist v. a. bei Sammlungen/Gewächshaus sinnvoll. *Cryptolaemus montrouzieri* (Marienkäfer) frisst Schmierläuse und deren Eier; abends ausbringen (geringere Abwanderung). Gegen Trauermücken-Larven im Substrat wirken die Nematode *Steinernema feltiae* (Gießanwendung) und die Raubmilbe *Stratiolaelaps scimitus* (früher *Hypoaspis miles*) komplementär — beide bekämpfen das Bodenstadium und ergänzen die Gießtechnik (Substratoberfläche abtrocknen lassen) als kulturelle Maßnahme.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze (eignet sich als Kompositionspflanze in Sukkulenten-Arrangements).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Graylii-Echeverie | Echeveria subsessilis | Gleiche Gattung | Blaugrüner, ähnliche Pflege |
| Graptopetalum | Graptopetalum paraguayense | Gleiche Familie | Sehr robust, für Anfänger |
| Haworthia | Haworthiopsis fasciata | Sukkulente, ähnliche Pflege (Asphodelaceae) | Schattenverträglicher |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Echeveria elegans,"Mexikanische Schneekugel;Glashausrose;Mexican Snowball;Mexican Gem",Crassulaceae,Echeveria,perennial,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b","Mexiko (Hidalgo)",yes,0.3-2,6,8-15,8-30,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Old Farmer's Almanac — Echeveria Care](https://www.almanac.com/plant/complete-guide-growing-and-caring-echeveria-succulents) — Kulturdaten
2. [Plant Care Today — Echeveria elegans](https://plantcaretoday.com/echeveria-elegans.html) — Pflegehinweise
3. [Gardens Whisper — Echeveria elegans](https://gardenswhisper.com/echeveria-elegans-care-propagation/) — Vermehrung
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Britannica — Crassulacean Acid Metabolism](https://www.britannica.com/science/crassulacean-acid-metabolism) — CAM-Photosynthese (Crassulaceae)
6. [Henry Shaw Cactus and Succulent Society — C3, C4, CAM Photosynthesis](https://hscactus.org/resources/digest/plant-info/c3-c4-cam/) — CAM-Photosynthese bei Sukkulenten
7. [Kellogg Garden Organics — Echeveria elegans for Beginners](https://kellogggarden.com/blog/gardening/echeverias-the-easiest-succulent-to-grow/) — Boden-pH 6.0, Standort, full sun
8. [Gardener's Path — How to Grow Echeveria Succulents](https://gardenerspath.com/plants/succulents/grow-echeveria/) — Wurzelsystem, Staunässe, pH, Standort
9. [AskGardening — Which Succulents Have Shallow and Deep Roots](https://askgardening.com/do-succulents-have-shallow-roots/) — Wurzeltiefe (6–12 inch ≈ 15–30 cm), fibröses Flachwurzelsystem
10. [Greg — Prolific Echeveria Roots](https://greg.app/prolific-echeveria-roots/) — Staunässe-Empfindlichkeit, Wurzeltiefe
11. [Succulent Growing Tips — Is Echeveria Frost Hardy?](https://succulentgrowingtips.com/is-echeveria-frost-hardy/) — Frostempfindlichkeit, frostfreie Überwinterung
12. [Succulent.care — Will Echeveria Survive Freezing Winter](https://www.succulent.care/will-echeveria-survive-freezing-winter/) — Winterquartier-Temperatur, Frostschutz
13. [Ottershaw Cacti — Do Echeverias Like Full Sun or Shade?](https://ottershawcacti.com/news-events/echeveria/do-echeverias-like-full-sun-or-shade/) — Vollsonne, Lichtbedarf, Etiolierung
14. [RHS — Biological Control in the Garden](https://www.rhs.org.uk/prevention-protection/biological-control-garden) — Nützlinge gegen Schmierläuse (Cryptolaemus) und Trauermücken (Steinernema feltiae, Hypoaspis)
15. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Ausbringrate Marienkäfer (≈ 1/sq ft), Bedingungen
16. [Natural Enemies — Entonem (Steinernema feltiae) Commercial Guide](https://naturalenemies.com/news-and-information/entonem-steinernema-feltiae-commercial-guide-for-soilstage-pest-control/) — Ausbringrate 0,5 Mio./m², Temperaturbereich
17. [Henry Shaw Cactus & Succulent Society / AskGardening — Succulent Light Levels](https://askgardening.com/succulent-light-needs/) — PPFD-Bereiche, Lichtkompensationshinweis (kein artspez. Kompensationspunkt)
18. [Nutrient Solution for Hydroponics (Hoagland & Arnon)](https://www.researchgate.net/publication/358182542_Nutrient_Solution_for_Hydroponics) — Mikronährstoff-Standardgehalte Mn/Zn/Cu/Mo (ppm)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
