# Lila Sauerklee, Glücksklee — Oxalis triangularis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Bloomscape](https://bloomscape.com/plant-care-guide/oxalis/), [Ohio Tropics](https://www.ohiotropics.com/2019/08/11/oxalis-triangularis-purple-shamrock/), [House Plant House](https://houseplanthouse.com/2018/10/09/oxalis-triangularis-dormancy/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Oxalis triangularis | `species.scientific_name` |
| Volksnamen (DE/EN) | Lila Sauerklee, Glücksklee, Dreiecksklee; Purple Shamrock, False Shamrock, Wood Sorrel | `species.common_names` |
| Familie | Oxalidaceae | `species.family` → `botanical_families.name` |
| Gattung | Oxalis | `species.genus` |
| Ordnung | Oxalidales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (sporadische Dormanz alle 2–7 Jahre) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur Wuchsphase (base temp, °C) | <!-- DATEN FEHLEN — keine belegte Wuchs-/Phänologie-GDD-Basis für diese Zierpflanze auffindbar; tropische Waldbodenstaude, Hauptwuchs bei 15–24 °C --> | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN — tagneutral (day_neutral), kein Kurztag-/Langtagblüher; daher kein numerischer Stunden-Schwellwert anwendbar --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — Zwiebeln im Boden überwintern in Zone 6+. Mindesttemperatur -15°C für kurze Fröste. Als Zimmerpflanze optimal bei 15–21°C. | `species.hardiness_detail` |
| Heimat | Brasilien, Argentinien — tropische und subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Oxalis triangularis ist bekannt für ihre photoperiodische Blattbewegung (Nyktinastie) — die lila Dreiblätter öffnen und schließen sich je nach Lichtverhältnissen. Die sporadische Dormanz kann den Besitzer erschrecken: die Pflanze zieht scheinbar vollständig ein und "stirbt" — tatsächlich erholen sich die Zwiebeln nach 2–4 Wochen Trockenheit vollständig. Oxalsäure (daher Oxalidaceae) macht die Pflanze für Haustiere leicht giftig.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6, 9, 10 (weiß-rosa Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Zwiebelknöllchen beim Umtopfen teilen und getrennt einpflanzen. Sehr einfach und erfolgreich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (mild bitter, kaum Menge verzehrt) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (Blätter, Stängel, Zwiebeln) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | oxalic_acid (Oxalsäure — kann Nierensteine bei übermäßigem Konsum fördern) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt nötig. Abgestorbene Stiele und Blätter abzupfen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, frosttolerante Zwiebeln) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20% Perlite. pH 6.0–7.0. Zwiebeln ca. 3 cm tief einpflanzen. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-Schwellwert (a) für Oxalis triangularis; Klasse "sensitive" impliziert ECe < 2 dS/m, jedoch kein quantitativer Quellenbeleg --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-Slope auffindbar --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Als tropische Waldbodenstaude (forest understory) hat *Oxalis triangularis* einen niedrigen Lichtkompensationspunkt typischer Schattenpflanzen (10–50 µmol/m²/s; hier konservativ 10–30) und behält dennoch eine hohe Plastizität — bei hellem indirektem Licht intensiviert sich die Blattfärbung. Die Salzempfindlichkeit (salt sensitivity) zeigt sich praktisch in Blattspitzenverbrennung (tip burn) bei Düngersalz-Anreicherung oder hartem/chlor-/fluoridhaltigem Leitungswasser; Regen-, Filter- oder destilliertes Wasser wird bevorzugt. Der pH-Vorzug 6.0–7.0 ist konsistent mit den Angaben in §1.6 und §2.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum | 180–365 (bis Dormanz) | 1 | false | false | medium |
| Dormanz (sporadisch) | 14–28 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–24 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 (kühle, dunkle Ecke) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 42–60 (fast gar nicht) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0–20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.4–0.8 | 6.0–7.0 | 40 | 15 |
| Dormanz | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (ppm):**

| Phase | Mn (Mangan) | Zn (Zink) | Cu (Kupfer) | Mo (Molybdän) |
|-------|-------------|-----------|-------------|---------------|
| Aktives Wachstum | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Dormanz | — | — | — | — |

KA-Felder: `nutrient_profiles.manganese_ppm` / `nutrient_profiles.zinc_ppm` / `nutrient_profiles.copper_ppm` / `nutrient_profiles.molybdenum_ppm`. Für *Oxalis triangularis* als salzempfindlichen Leichtzehrer (light feeder) liegen keine artspezifisch belegten Mikronährstoff-Zielkonzentrationen aus mindestens zwei seriösen Quellen vor; daher als DATEN FEHLEN markiert (kein Übertragen generischer Hoagland-Standardwerte).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 3 ml/L (monatlich) | Wachstum |
| Zimmerpflanzen-Dünger | Compo | base | 7-3-6 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatliche Düngung im aktiven Wachstum. Niemals während der Dormanz düngen. Halbe Empfehlungsdosis ausreichend.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.3 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Salzempfindlich (salt_tolerance_class: sensitive) — weiches Regen-, Filter- oder destilliertes Wasser bevorzugt; hartes/chlor-/fluoridhaltiges Leitungswasser kann Blattspitzenverbrennung (tip burn) verursachen. Substrat zwischen den Güssen leicht antrocknen lassen; bei Dormanz fast trocken lagern <!-- Quelle: Steckbrief-Erweiterung 2026-06: an Salztoleranz §1.7 angeglichen --> | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 5–12 (kühle Ruheperiode) bzw. 15–21 als durchkultivierte Zimmerpflanze | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell indirekt bei Durchkultur; dunkel bei eingeleiteter Dormanz | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam; bei eingeleiteter Dormanz Knollen fast trocken halten (nie ohne Substrat lagern) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** *Oxalis triangularis* ist frostempfindlich (RHS-Härtegrad H1b) und überwintert in Mitteleuropa (USDA 6–8) frostfrei im Haus — daher `hardiness_rating: frost_free` (nicht `dig_and_store`, da die Knollen üblicherweise im Topf mit Substrat verbleiben). Zwei Überwinterungswege sind möglich: (1) durchkultiviert als Zimmerpflanze bei 15–21 °C, oder (2) eingeleitete Ruheperiode in kühlem (5–12 °C), dunklem Raum von November bis Februar mit stark reduziertem Gießen. Die Knollen niemals substratlos lagern — sie werden binnen weniger Tage weich und vertrocknen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Kleine gelbe Punkte, Gespinste | medium |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |
| Blattläuse | Aphis spp. | Klebrige Ausscheidungen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Blattläuse |
| Sand auf Oberfläche | cultural | 1 cm Quarzsand | 0 | Trauermücke (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|-----------------------|---------------------|----------------|-----------------|------------------|
| Raubmilbe (predatory mite) | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m² je Ausbringung | ca. 1–2 Wochen (bei 13–27 °C, > 70 % rF) |
| Schlupfwespe (parasitic wasp) | Aphidius colemani | Blattläuse (Aphis spp.) | 0,25–4 Tiere/m² (typ. 0,5–1), 2–3 Ausbringungen im Wochenabstand | ca. 2–3 Wochen über mehrere Ausbringungen |
| Nematode (entomopathogenic nematode) | Steinernema feltiae | Trauermücke (Bradysia spp.), Larven | 0,5 Mio. infektiöse Juvenile/m² (Substrat-Drench) | Larvenmortalität in 24–48 h; Wiederholung nach 1–2 Wochen |

**Hinweis:** Die Nützling-Wirt-Zuordnung ist auf die in §5.1 gelisteten Schädlinge abgestimmt. *Phytoseiulus persimilis* benötigt > 70 % relative Luftfeuchte und Temperaturen von 15–25 °C, was bei einer feuchteliebenden Zimmerpflanze gut erreichbar ist. *Steinernema feltiae* wird als Gieß-/Drench-Anwendung in das feuchte Substrat eingebracht und bekämpft die Trauermückenlarven in der Wurzelzone — ergänzend zur kulturellen Quarzsand-Barriere aus §5.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Grüner Sauerklee | Oxalis tetraphylla | Gleiche Gattung | Grüne Blätter, ähnliche Pflege |
| Maranta | Maranta leuconeura | Nyktinastie, ähnliches Blattverhalten | Nicht giftig für Haustiere |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Oxalis triangularis,"Lila Sauerklee;Glücksklee;Purple Shamrock;False Shamrock",Oxalidaceae,Oxalis,perennial,day_neutral,herb,bulbous,"6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a","Brasilien, Argentinien",yes,0.5-3,10,15-30,20-40,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Bloomscape — Oxalis Care Guide](https://bloomscape.com/plant-care-guide/oxalis/) — Pflegehinweise, Nyktinastie
2. [Ohio Tropics — Oxalis triangularis](https://www.ohiotropics.com/2019/08/11/oxalis-triangularis-purple-shamrock/) — Kulturdaten
3. [House Plant House — Oxalis Dormancy](https://houseplanthouse.com/2018/10/09/oxalis-triangularis-dormancy/) — Dormanz-Management
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (Oxalsäure — mild giftig für Haustiere)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Useful Tropical Plants — Oxalis triangularis](https://tropical.theferns.info/viewtropical.php?id=Oxalis+triangularis) — Heimat/Habitat (Unterwuchs feuchter Schattenwälder Brasiliens), C3-Lebensform (kein Sukkulent), Wurzeltiefe
6. [Gardenia.net — Oxalis triangularis (False Shamrock)](https://www.gardenia.net/plant/oxalis-triangularis) — Lichttoleranz (Halbschatten), Standortqualität
7. [UK Houseplants — False Shamrock (Oxalis)](https://www.ukhouseplants.com/plants/false-shamrock-oxalis) — Wuchstemperatur 12–24 °C, RHS-Härtegrad H1b, Schatten-/Sonnentoleranz, Chemikalienempfindlichkeit
8. [Garden-ID — Oxalis pourpre](https://www.garden-id.com/en/blog/blog-garden-id-7/oxalis-pourpre-a-trendy-plant-thats-easy-to-grow-11) — Überwinterung 5–12 °C dunkel (Nov–Feb), frostfrei einräumen
9. [Greg App — Oxalis triangularis Care](https://greg.app/plant-care/oxalis-triangularis) — Optimaltemperatur 15–24 °C, Wasser-/Salzempfindlichkeit
10. [LiteracyChange — How to Fertilize Oxalis](https://literacychange.org/how-to-fertilize-oxalis-pi1809/) — Salzempfindlichkeit (Düngersalz-Anreicherung → tip burn), Regen-/destilliertes Wasser
11. [ScienceDirect — Light Compensation Point (overview)](https://www.sciencedirect.com/topics/engineering/light-compensation) — Lichtkompensationspunkt schattentoleranter Unterwuchspflanzen (10–50 µmol/m²/s)
12. [Craine & Reich (2005), New Phytologist — Leaf-level light compensation points in shade-tolerant woody seedlings](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2005.01420.x) — niedrige LCP-Werte schattentoleranter Arten (peer-reviewed)
13. [Academic.oup.com (Journal of Experimental Botany) — Canopy light / R:FR](https://academic.oup.com/jxb/article/76/3/712/7727419) — R:FR ≈ 1.1 in offener Sonne → FR-Fraction ≈ 0.5; Anstieg im Schatten/Unterwuchs (peer-reviewed)
14. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Spinnmilben-Raubmilbe, Ausbringrate 2–50/m², Klimaansprüche
15. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Blattlaus-Schlupfwespe, Ausbringrate 0,25–4/m², mehrfache Ausbringung
16. [Natural Enemies — Entonem (Steinernema feltiae) Commercial Guide](https://naturalenemies.com/news-and-information/entonem-steinernema-feltiae-commercial-guide-for-soilstage-pest-control/) — Trauermücken-Nematode, 0,5 Mio. IJ/m² Substrat-Drench
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
