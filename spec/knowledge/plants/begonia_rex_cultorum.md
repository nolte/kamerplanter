# Königsbegonie — Begonia rex-cultorum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardeners Path](https://gardenerspath.com/plants/houseplants/grow-rex-begonia/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/rex-begonia-care-guide-growing-vibrant-begonia-rex-cultorum/), [Gardenia.net](https://www.gardenia.net/genus/begonia-rex-cultorum-rex-begonia-grow-and-care-tips), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-rex-begonia), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Begonia rex-cultorum | `species.scientific_name` |
| Volksnamen (DE/EN) | Königsbegonie, Zierbegonie; Rex Begonia, King Begonia, Painted-leaf Begonia | `species.common_names` |
| Familie | Begoniaceae | `species.family` → `botanical_families.name` |
| Gattung | Begonia | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 3–5 (ab Teilung neu verjüngen) | `lifecycle_configs.typical_lifespan_years` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis pathway) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage (vernalization min days) | Entfällt (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | Entfällt (tagneutral / day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 13°C, optimal 18–24°C. | `species.hardiness_detail` |
| Heimat | Ostindien (Assam) — ursprünglich, Hybridkultivare weltweit gezüchtet | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Begonia rex-cultorum ist kein Artname, sondern eine Kultivargruppe — alle modernen Sorten sind Kreuzungen und Hybriden. Das Blattspektrum ist unübertroffen: Silber, Purpur, Bronze, Schwarz, Rosa, Grün in unzähligen Mustern (Spiralen, Tupfen, Sterne). Primärer Dekorationswert liegt in den Blättern, nicht in den Blüten (die eher unscheinbar sind). Die Pflanze benötigt hohe Luftfeuchtigkeit aber gleichzeitig trockene Blätter — Blattnässe fördert Mehltau. Unterbewässerung ist besser als Überwässerung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (kleine, unscheinbare rosa-weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_leaf, division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Blattstecklinge: Blatt ablegen, 4–5 Kerben in die Hauptadern schneiden (Unterseite), auf feuchtes Substrat legen. Bewurzelung und neue Pflänzchen in 6–12 Wochen. Oder: Blattstiel im 45°-Winkel in feuchtes Substrat stecken. Teilung des Rhizoms beim Umtopfen ebenfalls möglich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (besonders Rhizom/Rhizom — lösliche Calcium-Oxalate) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides (besonders in Rhizomen) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Rhizom zurückschneiden für kompakteren Wuchs) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 (flache Rhizome) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 25–50 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (windgeschützt, Halbschatten, kein Regen, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 25% Perlite. pH 5.5–6.5. Flache Schalen bevorzugt (Rhizom braucht Breite, nicht Tiefe). | — |

### 1.7 Umgebungs-Physiologie & Standortqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) min/max | 5–20 | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | < 3 (Maas-Hoffman a; Schwelle, ab der Wachstumsdepression beginnt) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> nicht belegt | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis:** Begonia rex-cultorum ist eine schattenadaptierte Unterwuchspflanze (understory) tropisch-subtropischer Wälder mit dünnen, großflächigen Blättern und niedriger Stomata-Dichte; der Lichtkompensationspunkt liegt entsprechend tief (Studien zu 'Black Velvet' nutzen 5–20 µmol/m²/s als Unterwuchs-Spektrum, mit Optimum-Hinweis bei ~20). Helles, indirektes Licht (partial_shade bis shade); direkte Mittagssonne führt zu Blattverbrennungen. Die ECe-Schwelle bezieht sich auf die Substrat-Leitfähigkeit (saturated paste extract), NICHT auf die Gießwasser-EC; die niedrige Schwelle (< 3 dS/m, sensitive-Klasse) ist mit dem niedrigen Dünge-EC-Korridor (0.4–0.8 mS) in §2.3 konsistent. Die GDD-Basistemperatur von 10 °C ist aus den kardinalen Temperaturgrenzen abgeleitet (Wachstumsstopp < 15 °C, Schadschwelle < 10 °C), nicht aus einem publizierten GDD-Versuch.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kritischer stomatärer Kollaps, kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 4–8 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kritischer stomatärer Kollaps, kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.5–6.5 | 50 | 20 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 5.5–6.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Mn/Zn/Cu/Mo (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`) folgen den Standard-Hydroponik-/Hoagland-Untergrenzen (Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.01 ppm). Als Leichtzehrer (light_feeder) wird das untere Ende der gängigen Spannen genutzt; in handelsüblichen Volldüngern sind diese Spuren bereits enthalten. Der toleranzkritische Abstand zwischen Mangel und Toxizität ist bei Mikronährstoffen klein — nicht überdosieren.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 2 ml/L (monatlich) | Wachstum |
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich März bis September, halbe Empfehlungsdosis. Oktober bis Februar kein Dünger. Nie auf die Blätter düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; NIE auf Blätter gießen (Mehltau); Substrat leicht antrocknen lassen zwischen Güssen; Luftfeuchtigkeit mit Kieselstein-Schale erhöhen (nicht besprühen) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor erstem Frost / unter 13 °C hereinholen) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach den Eisheiligen, abgehärtet) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 13–18 (Minimum 13, nie unter 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | Hell, indirekt (helles Fenster, ohne direkte Mittagssonne) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | Sparsam, Substrat nur leicht feucht halten (kein Austrocknen, keine Staunässe) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Begonia rex-cultorum ist frostempfindlich (tender) und als Zimmer-/Kübelpflanze frostfrei (frost_free) drinnen zu überwintern — KEINE Knollen-Einlagerung (kein dig_and_store, das gilt nur für knollige Begonien wie *Begonia × tuberhybrida*). Im Mitteleuropa-Kontext (USDA 6–8) ganzjährig drinnen oder nur im Hochsommer windgeschützt im Halbschatten draußen. Bei Lichtmangel im Winter kann die Pflanze teilweise einziehen (Blattfall); dann Gießmenge reduzieren und auf Neuaustrieb bei längeren Tagen warten.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter verblassen | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen | medium |
| Blattläuse | Aphis spp. | Klebrige Triebe | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Nasse Blätter, schlechte Belüftung |
| Grauschimmel | fungal | Graubrauner Schimmelbelag | Zu hohe Feuchtigkeit |
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Nie besprühen | cultural | Gießtechnik ändern | 0 | Mehltau, Grauschimmel (Prävention) |
| Neemöl | biological | Sprühen 0.3% (Unterseite) | 0 Tage | Spinnmilbe, Schmierläuse |
| Kaliumbicarbonat | biological | Sprühen 0.5% | 0 | Echter Mehltau |

### 5.4 Nützlinge (Biologische Bekämpfung)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Nützling (beneficial) | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|-----------------------|---------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–10 /m² (kurativ, wöchentl. wiederholen) | 2–3 Wochen, Kontrolle nach 4–6 Wo. |
| Thrips-Raubmilbe | Neoseiulus (Amblyseius) cucumeris | Thrips (Frankliniella occidentalis) | 50–100 /m² bzw. 1 Tüte je 1–2 m² | 2–4 Wochen |
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphis spp.) | 0.15–1 /m² präventiv, wöchentl. | 2–3 Wochen |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 5–10 /m² (kurativ), 2–3× im Abstand 1–2 Wo. | 3–4 Wochen |

**Hinweis:** Nützlingseinsatz erfordert moderate Temperaturen (Phytoseiulus 17–28 °C, Cryptolaemus 25–28 °C optimal) und relative Luftfeuchte 60–90 %, was zum Standortprofil der Königsbegonie passt. Nützlinge nicht mit Neemöl/Kaliumbicarbonat-Spritzungen kombinieren — chemische/biologische Spritzbeläge schädigen die Nützlinge; entweder Spritzung ODER Nützling.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Eisenbegonie | Begonia masoniana | Begoniaceae, Blattzierart | Markante Eisenkreuz-Musterung |
| Wachsbegonie | Begonia semperflorens | Begoniaceae | Mehr Blüten, kompakter |
| Calathea orbifolia | Goeppertia orbifolia | Buntlaub, Zimmerpflanze | Tierfreundlich |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Begonia rex-cultorum,"Königsbegonie;Zierbegonie;Rex Begonia;Painted-leaf Begonia",Begoniaceae,Begonia,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Ostindien (Hybridkultivare)",yes,1-5,10,20-50,25-50,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardeners Path — Rex Begonia](https://gardenerspath.com/plants/houseplants/grow-rex-begonia/) — Pflegehinweise, Blatt-Vermehrung
2. [Healthy Houseplants — Rex Begonia](https://www.healthyhouseplants.com/indoor-houseplants/rex-begonia-care-guide-growing-vibrant-begonia-rex-cultorum/) — Kulturdaten
3. [Gardenia.net — Rex Begonia](https://www.gardenia.net/genus/begonia-rex-cultorum-rex-begonia-grow-and-care-tips) — Botanische Daten
4. [The Sill — Rex Begonia](https://www.thesill.com/blogs/plants-101/how-to-care-for-rex-begonia) — Schädlinge, Pflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig — Calcium-Oxalate)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Begonia rex (king begonia)](https://www.rhs.org.uk/plants/101666/begonia-rex-(r)/details) — Schatten/indirektes Licht, Mindesttemperatur 13 °C, Winterruhe
7. [University of Connecticut Extension — Rex Begonia](https://homegarden.cahnr.uconn.edu/factsheets/rex-begonia/) — Mindesttemperatur 13 °C (nie unter 10 °C), Überwinterung, Lichtbedarf
8. [PMC — Photoregulation of lipid metabolism in Begonia 'Black Velvet' (synergistic effects of spectral composition and intensity)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12855531/) — schattenadaptierte Unterwuchspflanze, PPFD 5–20 µmol/m²/s, geringe Stomata-Dichte
9. [Springer / J. Plant Growth Regul. — Photosynthetic biophysical parameters of Begonia rex under light spectra](https://link.springer.com/article/10.1007/s00344-023-11059-z) — Photosynthese-Messungen bei 250 µmol/m²/s, Spektralabhängigkeit
10. [USU Extension — Salinity and Plant Tolerance](https://extension.usu.edu/irrigation/research/salinity-and-plant-tolerance) — Begonia salzempfindlich (sensitive, < 3 dS/m ECe)
11. [American Begonia Society — Basic Information](https://www.begonias.org/basic-information/) — Optimaltemperaturen, Kulturhinweise
12. [Koppert — Phytoseiulus persimilis / Neoseiulus cucumeris / Aphidius colemani / Cryptolaemus montrouzieri](https://www.koppert.com/) — Nützlings-Ausbringraten, Etablierungszeiten, Klimaanforderungen
13. [Proven Winners / Gardening Know How — Overwintering Begonias](https://www.provenwinners.com/learn/overwintering-begonias) — frostfreie Überwinterung, reduziertes Gießen, kein Knollen-Storage bei rhizomatösen/faserwurzligen Typen
14. [Healthy Houseplants / Cafe Planta — Rex Begonia Soil](https://www.healthyhouseplants.com/indoor-houseplants/rex-begonia-care-guide-growing-vibrant-begonia-rex-cultorum/) — Boden-pH 5.5–6.5, flache Rhizome, keine Staunässe
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
