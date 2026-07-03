# Waldrebe — Clematis spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Clematis Baumschule W. Kruse, Intratuin Clematis-Pflanzenlexikon, Plantura Phlox, COMPO Clematis

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Clematis spp. | `species.scientific_name` |
| Volksnamen (DE/EN) | Waldrebe; Clematis | `species.common_names` |
| Familie | Ranunculaceae | `species.family` → `botanical_families.name` |
| Gattung | Clematis | `species.genus` |
| Ordnung | Ranunculales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> | `species.base_temp` |
| Lebensdauer (Jahre) | 15–50 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (chilling/endodormancy) | true (chilling) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (min days) | 42 (ca. 6 Wochen Knospen-Chilling bei ≤ 7,5 °C) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–9b (sortenabhängig) | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -10°C (alle Arten); die meisten Sorten vertragen -20 bis -25°C; immergrüne Sorten (C. armandii) nur bis -10°C | `species.hardiness_detail` |
| Heimat | Europa, Asien, Nordamerika (je nach Art) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zur Photoperiode (Korrektur):** Die Blüte der Clematis ist nicht über eine kritische Tageslänge gesteuert, sondern über Holzalter/Schnittgruppe und Temperatur. Die drei Schnittgruppen blühen über extrem unterschiedliche Tageslängen hinweg (Gruppe 1 April–Mai, Gruppe 2 Mai–Juni, Gruppe 3 Juli–September). Die Art ist damit faktisch tagneutral (day_neutral); der bisherige Eintrag `long_day` war fachlich inkonsistent und wurde korrigiert (inkl. CSV-Zeile §8.1). Es wird keine kritische Tageslänge angegeben.

**Hinweis zur Vernalisation/Chilling:** Als laubabwerfendes Gehölz der Zonen 4–9 benötigt Clematis eine Winterruhe (Dormanz) mit Kältephase zum Bruch der Endodormanz (Knospen-Chilling), korrekter "chilling" statt echter Vernalisation. Aus Samen verlangen die meisten Arten 4–8 Wochen Kaltstratifikation (0–5 °C); das ist jedoch eine Keim-Stratifikation und keine belastbare Angabe für die Knospen-Chilling-Dauer der etablierten Pflanze. Für die etablierte Pflanze nennen zwei unabhängige Quellen (Michigan State University Extension; Clearview Horticultural Products) übereinstimmend eine dormante Periode von ca. **sechs Wochen** (≈ 42 Tagen), induziert durch Nachttemperaturen von ≤ 7,5 °C (45 °F); Pflanzen blühen nach einem solchen Chilling deutlich besser. `vernalization_min_days` wird daher mit 42 belegt (untere, quellentreue Grenze; ergänzende Literatur nennt bis zu 6–8 Wochen). Der Wert ist konsistent mit der Phase "Winterruhe" (120–150 Tage, §2.1), von der das Chilling ein Teilabschnitt ist.

**Hinweis zur GDD-Basistemperatur:** Für Clematis liegt keine über zwei unabhängige seriöse Quellen belegte GDD-Basistemperatur der Hauptwuchsphase vor; `base_temp` bleibt unbelegt (DATEN FEHLEN).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6 (Gruppe 1+2); 7, 8, 9 (Gruppe 3) | `species.bloom_months` |

**Hinweis:** Blütezeit ist stark sortenabhängig und von der Schnittgruppe abhängig. Gruppe 1 (Frühjahrsblüher wie C. montana): April–Mai. Gruppe 2 (zweimal blühend wie 'Nelly Moser'): Mai–Juni und August–September. Gruppe 3 (Sommerblüher wie C. viticella): Juli–September.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Stecklinge im Juni/Juli von halbverholzten Trieben. Absenker im Frühjahr. Aussaat möglich, aber 2–3 Jahre bis zur Blüte.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile, besonders Blätter und Stängel | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Protoanemonin (Ranunculaceae-typisch), Anemonin | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Frischer Saft kann Hautreizungen und Blasen verursachen. Beim Schneiden Handschuhe tragen.

### 1.5 Rückschnitt

**KRITISCH: Die Schnittgruppe bestimmt alles!**

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (nach Blüte, gruppenabhängig) | `species.pruning_type` |
| Rückschnitt-Monate | Gruppe 1: 4–5 (direkt nach Blüte); Gruppe 2: 2–3 (leicht); Gruppe 3: 2–3 (stark) | `species.pruning_months` |

**Schnittgruppen im Detail:**
- **Gruppe 1** (Frühjahrsblüher, C. montana, C. alpina, C. macropetala): Blüten an vorjährigem Holz. KEIN routinemäßiger Schnitt — nur Auslichten bei Bedarf, direkt nach der Blüte. Niemals im Herbst oder Winter schneiden!
- **Gruppe 2** (Großblumige Hybriden wie 'Nelly Moser', 'The President'): Leichter Rückschnitt Ende Februar auf kräftige Knospen (auf ca. 1 m zurück). Blühen an altem und neuem Holz.
- **Gruppe 3** (Sommerblüher: C. viticella, C. jackmanii, 'Hagley Hybrid'): Starker Rückschnitt Ende Februar / Anfang März auf 20–50 cm über dem Boden. Blühen ausschließlich an neuen Trieben.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–600 (sortenabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80–100 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgründige, humusreiche Erde; pH 6,0–7,0; Drainageschicht am Boden; Fuß kühl und schattig halten (Mulch oder Nachbarpflanze) | — |

**Standort-Besonderheit:** "Kopf in der Sonne, Fuß im Schatten" — die unteren 30–50 cm sollten beschattet sein (Mulch, Steinplatten, Bodendecker, Nachbarpflanze).

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 45–120 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweise zu §1.7:**
- **Schatten-/Sonnentoleranz:** Clematis wächst in voller Sonne bis Halbschatten; viele Arten stammen aus dem Gehölzrand/Unterwuchs und vertragen lichten Schatten gut, blühen in tiefem Schatten aber schlecht (RHS). Einstufung `partial_shade`.
- **Wurzeltiefe:** Clematis ist tiefwurzelnd; etablierte Pflanzen erreichen ~120 cm (bis ~4 ft), Pflanz-/Etablierungshorizont ~45 cm (18 in). Spanne 45–120 cm.
- **Staunässe:** RHS empfiehlt tiefgründigen, feuchten, aber gut drainierten Boden und rät von Pflanzung in staunassen Böden ab → `sensitive`.
- **Lichtkompensationspunkt:** Keine über zwei seriöse Quellen belegte artspezifische Messung gefunden → DATEN FEHLEN. (Die Sättigungs-/Optimumwerte stehen separat in §2.2, nicht im LCP-Feld.)
- **Salztoleranz:** Keine belastbaren ECe-Schwellen-/Slope-Daten (Maas-Hoffman) noch Klasseneinstufung für Clematis gefunden → DATEN FEHLEN.
- **Boden-pH:** Quellen reichen von 6.0–7.0 (leicht sauer bis neutral) bis 6.5–7.5 (neutral bis leicht alkalisch). Quellentreu und konsistent mit §1.6 und §2.3 (jeweils 6,0–7,0) wird die Spanne 6.0–7.0 übernommen und nicht eigenmächtig erweitert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum | 42–84 | 2 | false | false | medium |
| Blüte | 30–60 | 3 | false | false | medium |
| Nachblüte / Samenbildung | 30–60 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (volle Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 800–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 6.0–7.0 | 100 | 50 | — | 2 |
| Vegetativ | 2:1:1 | 1.0–1.4 | 6.0–7.0 | 120 | 60 | — | 3 |
| Blüte | 1:2:2 | 1.0–1.4 | 6.0–7.0 | 100 | 50 | — | 2 |
| Nachblüte | 1:1:2 | 0.8–1.2 | 6.0–7.0 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

**Hinweis:** Kein Stickstoff nach Ende Juli — Triebe müssen ausreifen, sonst Frostschäden.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo) je Phase:**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Frühjahrsaustrieb | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Vegetativ | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Nachblüte | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

**Hinweis zu Mikronährstoffen:** Für Clematis liegen keine über zwei unabhängige seriöse Quellen belegten phasenspezifischen Mangan-/Zink-/Kupfer-/Molybdän-Sollwerte (ppm) vor; die Felder `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm` bleiben unbelegt (DATEN FEHLEN). Eine Versorgung über Volldünger mit Spurenelementmix ist praxisüblich, liefert aber keine quantifizierbaren Sollwerte.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Stauden & Beetpflanzen | Compo | organisch-mineralisch | 80–100 g/m² | April, Juni | medium_feeder |
| Hornspäne | Oscorna | organisch | 50–80 g/m² | März–April | Stickstoffversorgung |
| Osmocote Exact (8–9 Monate) | ICL Specialty Fertilizers | slow_release | 30 g/Pflanze | April | Kübel/Topfkultur |
| Kompost (reif) | eigen | organisch | 3–5 L/m² | Herbst/Frühjahr | Bodenverbesserung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| April | Austrieb | Hornspäne + Kompost | 60 g/m² + 3 L/m² | Erste Düngung nach Winter |
| Mai–Juni | Blüte/Wachstum | Flüssig-Blütendünger | alle 2–4 Wochen | Kalibetont; N niedrig halten |
| Juli | Sommerblüher nachblühen | Kalibetonter Dünger | einmalig | Triebausreifung fördern |
| KEIN Dünger | Ab August | — | — | Triebe müssen ausreifen |

### 3.3 Besondere Hinweise zur Düngung

Ab Ende Juli kein stickstoffreicher Dünger mehr — die Triebe müssen vor dem Winter vollständig ausreifen. Junge Pflanzen im ersten Jahr sparsam düngen. Im Kübel alle 2–4 Wochen mit Flüssigdünger versorgen, da Nährstoffe schneller ausgewaschen werden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser geeignet; gleichmäßig feucht halten, aber keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 (alle 3 Jahre) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Schnitt Gruppe 2+3 | Gruppe 2: leicht auf 1 m; Gruppe 3: stark auf 20–50 cm | hoch |
| Apr | Düngung starten | Hornspäne + Kompost einarbeiten | mittel |
| Apr–Mai | Schleckengitter | Frische Austriebe vor Schnecken schützen | hoch |
| Mai–Sep | Gießen | Gleichmäßig feucht; Fuß mulchen | mittel |
| Jun–Jul | Stecklinge | Halbverholzte Triebe für Vermehrung | niedrig |
| Nach Blüte | Gruppe 1 auslichten | Nur wenn zu dicht; direkt nach Blüte | niedrig |
| Aug–Sep | Blüte Gruppe 3 | Keine Düngung mehr ab August | — |
| Nov | Winterschutz Kübel | Kübelpflanzen: Vlies, in geschützten Bereich stellen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

**Hinweis:** Kübelpflanzen an frostgeschützten Standort stellen (Garage, unbeheiztes Gewächshaus) oder dick mit Vlies einwickeln. Wurzelbereich mit Mulch schützen. Immergrüne Sorten (C. armandii) in Zone 7b ohne Schutz gefährdet.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schnecken | Arion rufus, Deroceras reticulatum | Fraßschäden an frischen Trieben; Schleimspuren | shoot | Frühjahrsaustrieb | easy |
| Ohrwürmer | Forficula auricularia | Löcher in Blütenblättern, nächtlicher Fraß | flower | flowering | medium |
| Blattläuse | Aphis spp. | Honigtau, Blattdeformationen | leaf, shoot | vegetative | easy |
| Spinnmilben | Tetranychus urticae | Gespinste, gelbe Punkte, Blattverfärbung | leaf | vegetative (Hitze) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Clematis-Welke | fungal (Phoma clematidina / Calophoma clematidina) | Plötzliches Welken einzelner Triebe; braune Stängelflecken an der Basis | Verletzungen, Feuchtigkeit | 7–14 | vegetative, flowering |
| Echter Mehltau | fungal (Erysiphaceae) | Weißer Belag auf Blättern | Trocken-Warm-Klima; schlechte Luftzirkulation | 5–10 | vegetative (Hochsommer) |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmelbelag, Triebfäule | Hohe Feuchtigkeit, kühle Temperaturen | 3–7 | Frühjahr |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 10–20 | 14–21 |
| Ohrwurm-Unterkünfte (Töpfe mit Stroh) | Ohrwürmer | — (natürliche Förderung) | sofort |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Clematis-Welke: Tief pflanzen | cultural | — | Rhizom 10–15 cm unter Erde pflanzen; Triebe können wieder austreiben | 0 | Clematis-Welke |
| Neemöl | biological | Azadirachtin | Sprühen 0.5%; abends | 3 | Blattläuse, Spinnmilben |
| Schneckenkorn (Eisenphosphat) | biological | Eisen(III)-phosphat | Streuen 3–5 g/m² | 0 | Schnecken |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen bei Mehltaubefall | 14 | Mehltau |
| Brennnesselbrühe | biological | — | Verdünnt sprühen 1:10 | 0 | Blattläuse vorbeugend |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| C. viticella-Sorten: weniger anfällig für Welke | Krankheit | `resistant_to` |

**Hinweis zur Clematis-Welke:** NICHT die ganze Pflanze vernichten! Tief einschneiden und auf austriebsfähige Knospen zurückschneiden. Durch tiefes Pflanzen (Rhizom 10–15 cm unter Boden) überleben Pflanzen die Welke häufig und treiben wieder aus.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kletterpflanzen / Zierpflanzen |
| Empfohlene Vorfrucht | — (Gehölz; kein Fruchtwechsel nötig) |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — (Mehrjährig; Standort bis 20+ Jahre) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rosen | Rosa spp. | 0.9 | Klassische Kombination; ergänzende Blütezeiten; Fuß gegenseitig beschatten | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.8 | Beschattet Clematisbase; Bestäuber anlocken | `compatible_with` |
| Hosta | Hosta spp. | 0.8 | Beschattet Clematisbase im Schatten- und Halbschattenbereich | `compatible_with` |
| Geranium | Geranium sanguineum | 0.7 | Bodendecker schützt Clematisbase vor Austrocknung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Walnuss | Juglans regia | Allelopathische Hemmung durch Juglon | severe | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Ranunculaceae | `shares_pest_risk` | Protoanemonin-Toxizität | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Clematis spp. |
|-----|-------------------|-------------|----------------------------------|
| Jungfernrebe | Parthenocissus tricuspidata | Kletterpflanze, keine Rankhilfe nötig | Haftet selbst; keine Schnittgruppen-Komplexität |
| Wilder Wein | Parthenocissus quinquefolia | Ähnliches Wuchsprinzip | Sehr robust; schöne Herbstfärbung |
| Knöterich | Fallopia baldschuanica | Sehr schnell wachsend | Einfachste Pflege; aber extrem invasiv |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Clematis spp.,"Waldrebe;Clematis",Ranunculaceae,Clematis,perennial,day_neutral,vine,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Europa, Asien, Nordamerika",yes,30,40,400,150,90,no,yes,false,true,medium_feeder,false,hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Clematis Baumschule W. Kruse — Pflanz- und Pflegetipps](https://www.clematis.de/contents/de/d12_clematis-pflanz-und-pflegetipps.html) — Schnittgruppen, Pflegehinweise
2. [Intratuin — Clematis Pflanzenlexikon](https://www.intratuin.de/pflanzenlexikon/clematis-waldrebe-pflege) — Standort, Winterhärte
3. [COMPO — Clematis](https://www.compo.de/ratgeber/pflanzen/gartenpflanzen/clematis) — Düngung
4. [Pflanzen-Kölle — Clematis Pflegeratgeber](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-clematis-richtig/) — IPM, Pflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Michigan State University Extension — "An Introduction to Clematis"](https://www.canr.msu.edu/hrt/uploads/534/79846/06-Growing-Clematis-English.pdf) — Knospen-Chilling/Dormanz: ca. 6 Wochen dormante Periode, Induktion bei Nachttemperaturen ≤ 7,5 °C (45 °F)
6. [Clearview Horticultural Products — Clematis Info](https://www.clearviewhort.com/about-clematis/) — bestätigt unabhängig: dormante Periode ca. 6 Wochen, ≤ 7,5 °C (45 °F) zur Dormanz-Induktion (Beleg für `vernalization_min_days`)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
