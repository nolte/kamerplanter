# Sonnenblume — Helianthus annuus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** USDA Plants Database, University of Minnesota Extension, Royal Horticultural Society, BLE (Bundesanstalt für Landwirtschaft und Ernährung), Hortipendium, Purdue University — Allelopathy in Crops

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Helianthus annuus | `species.scientific_name` |
| Volksnamen (DE/EN) | Sonnenblume; Common Sunflower, Sunflower | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Helianthus | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | `herb` (krautig, aufrecht; je nach Sorte 30–300 cm Höhe) | `species.growth_habit` |
| Wurzeltyp | `taproot` (Pfahlwurzel mit kräftigem Seitenwurzelsystem; Wurzeltiefe bis 150–200 cm) | `species.root_type` |
| Lebenszyklus | `annual` (einjährig — vollständiger Zyklus Aussaat bis Samenreife in einer Vegetationsperiode) | `lifecycle_configs.cycle_type` |
| Photoperiode | `day_neutral` (kultivierte Sorten sind weitgehend tagneutral; Wildformen zeigen fakultative Kurztagsreaktion) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a, 2b, 3a, 3b, 4a, 4b, 5a, 5b, 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | `tender` (frostempfindlich — Jungpflanzen werden durch Spätfrost getötet; ausgewachsene Pflanzen tolerieren leichten Frost kurzfristig) | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht winterhart. Einjährig, stirbt nach Samenreife ab. Keimung benötigt Bodentemperatur von mindestens 10 °C, besser 12–15 °C. Jungpflanzen frostempfindlich; Direktsaat nach den Eisheiligen (Mitte Mai). | `species.hardiness_detail` |
| Heimat | Nordamerika (Great Plains, Prärien); domestiziert vor ca. 4.000 Jahren von indigenen Völkern | `species.native_habitat` |
| Allelopathie-Score | -0.6 (deutlich hemmend — Helianthus annuus produziert mehrere allelopathische Substanzen, insbesondere Terpenlactone und Phenolsäuren, die Keimung und Wachstum benachbarter Pflanzen hemmen können) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | `heavy_feeder` (Starkzehrer — hoher N-, P- und K-Bedarf; besonders K-hungrig für Stängelstabilität und Samenbildung) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false (Allelopathie verhindert Eignung; Biomasse kann aber gehäckselt als Mulch dienen — 4–6 Wochen vor Nachkultur einarbeiten) | `species.green_manure_suitable` |
| Traits | `['ornamental', 'edible', 'bee_friendly']` (Zierpflanze und Nutzpflanze; Kerne essbar; herausragender Pollenspender für Bienen und Hummeln) | `species.traits` |

**Allelopathie-Detail:**
Die allelopathische Wirkung von Helianthus annuus ist gut dokumentiert (Purdue University, Macias et al. 2003). Heliannuol A–E und andere Sesquiterpenlactone werden über Wurzelexsudate und Blattstreu in den Boden abgegeben. Sie hemmen die Keimung und das Wurzelwachstum empfindlicher Arten (Salat, Weizen, Kartoffel). Nach der Ernte sollte Sonnenblumenreste mindestens 4–6 Wochen kompostieren, bevor die Fläche neu bestellt wird.

### 1.2 Aussaat- & Erntezeiten

Mitteleuropa (Zone 7–8), Bezugspunkt: letzter Frost Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (kurze Vorkultur möglich, aber Direktsaat bevorzugt wegen Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (sofort nach letztem Frost, wenn Bodentemperatur ≥ 10 °C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (Mai–Juni; April nur bei milder Witterung und Vliesabdeckung) | `species.direct_sow_months` |
| Erntemonate | 8, 9, 10 (August–Oktober; je nach Sorte und Aussaatzeitpunkt) | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (Juli–September) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | `seed` | `species.propagation_methods` |
| Schwierigkeit | `easy` (grosssamig, schnelle Keimung in 7–14 Tagen, kindertauglich) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 20–25 °C
- Minimale Keimtemperatur: 10 °C (langsame Keimung)
- Keimdauer: 7–14 Tage
- Saattiefe: 2–3 cm (Dunkelkeimer)
- Direktsaat bevorzugt — Pfahlwurzel toleriert Verpflanzen schlecht
- Bei Vorkultur: grosse Töpfe (min. 8 cm) verwenden, früh auspflanzen bevor Pfahlwurzel spiralisiert

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (nicht giftig; alle Pflanzenteile essbar: Kerne, Blütenblätter, junge Stängel, Keimlinge) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | `none` | `species.toxicity.severity` |
| Kontaktallergen | false (einzelne Personen können auf die raue Behaarung der Stängel empfindlich reagieren — keine echte Allergie) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Sonnenblumenpollen kann bei sensibilisierten Personen Allergien auslösen; Kreuzreaktion mit Beifuss/Artemisia möglich — Asteraceae-Pollenallergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | `none` (einjährig; kein Rückschnitt erforderlich. Bei verzweigenden Sorten kann Entspitzen des Haupttriebs mehr Seitentriebe und damit mehr Blüten fördern.) | `species.pruning_type` |
| Rückschnitt-Monate | null | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (nur Zwergsorten bis 60 cm Höhe; hochwüchsige Sorten benötigen Freiland) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--20 (Zwergsorten min. 5 L; Standardsorten min. 15--20 L) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 (Pfahlwurzel benötigt tiefe Gefässe) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30--300 (sortenabhängig; Zwergsorten 30--60 cm, Standardsorten 150--200 cm, Riesensorten bis 300 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30--60 (sortenabhängig; Riesensorten 60 cm, Zwergsorten 30 cm) | `species.spacing_cm` |
| Indoor-Anbau | no (Lichtbedarf extrem hoch, min. 800 PPFD; Indoor-Kultur nicht praktikabel) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Zwergsorten in grossen Töpfen bei voller Sonne; standfest verankern wegen Windlast) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (zu gross, Bestäubung durch Insekten nötig) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (bei hochwüchsigen Sorten >150 cm Stützstab oder Pfahl empfohlen; Zwergsorten standfest) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, tiefgründige Erde. Schwere Töpfe (Ton/Terrakotta) für Standfestigkeit. Drainage am Topfboden wichtig. | — |

**Hinweis:** Sonnenblumen sind primär Freilandpflanzen. Für Topf-/Balkonkultur eignen sich ausschliesslich Zwergsorten wie 'Big Smile', 'Teddy Bear', 'Sunspot' oder 'Pacino'. Die Pfahlwurzel verträgt Verpflanzen schlecht -- daher Direktsaat in den endgültigen Topf bevorzugen. Volle Sonne (mindestens 6--8 Stunden) ist zwingend erforderlich.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

Phasensequenz: **Annuelle (Ernte)** — Keimung → Sämling → Vegetativ → Blüte → Fruchtreife → Seneszenz. Bei reinen Ziersortenlines ohne Samengewinnung: `allows_harvest: false`.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 7–14 | 1 | false | false | low |
| Sämling (seedling) | 14–21 | 2 | false | false | low |
| Vegetativ (vegetative) | 28–56 | 3 | false | false | medium |
| Blüte (flowering) | 14–28 | 4 | false | false | medium |
| Fruchtreife (ripening) | 21–42 | 5 | false | true | high |
| Seneszenz (senescence) | 7–14 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 (Dunkelkeimer — Samen 2–3 cm tief) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0 (unter Erde) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | — | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–80 (Bodenfeuchte entscheidend) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | — (nicht relevant unterirdisch) | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1–2 (Boden gleichmässig feucht, nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–250 (Indoor-Voranzucht) / 300–500 (Freiland nach Auspflanzung, volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (natürlich; Langtag im Mai/Juni) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null (Freiland) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1000 (volle Sonne; Sonnenblumen sind obligate Volllichtpflanzen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (natürlich) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 (optimal 25; hitzetolerant bis 35 °C bei ausreichender Wasserversorgung) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null (Freiland) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2–4 (bei Hitze täglich; tiefgründig giessen, damit Pfahlwurzel in die Tiefe wächst) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500–2000 (je nach Pflanzengrösse — grosse Sonnenblumen transpirieren enorm) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 13–15 (natürlich; Juli–August) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 (trockener halten um Botrytis an Blütenkorb zu vermeiden) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2–3 (Wasserbedarf während Blüte am höchsten) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 1000–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Fruchtreife (ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (natürlich; August–September) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 35–50 (trocken halten — Schimmelgefahr an Samenköpfen) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–1.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3–5 (Bewässerung reduzieren für Samenreife) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500–1000 (reduziert) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Seneszenz (senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | natürlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | — | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natürlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | — (natürlich, Herbst) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | — | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | — | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | — | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | — | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | null | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | — (Bewässerung einstellen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Sämling | 2:1:1 | 0.8–1.0 | 6.0–6.5 | 80 | 40 | 30 | 2.0 |
| Vegetativ | 3:1:2 | 1.5–2.2 | 6.0–6.8 | 150 | 60 | 50 | 3.0 |
| Blüte | 1:2:3 | 1.5–2.0 | 6.0–6.8 | 120 | 60 | 50 | 2.5 |
| Fruchtreife | 0:1:3 | 1.0–1.5 | 6.0–6.8 | 100 | 50 | 40 | 2.0 |
| Seneszenz | 0:0:0 | 0.0 | — | — | — | — | — |

**Besonderheiten:**
- **Bor (B):** Sonnenblumen haben einen aussergewöhnlich hohen Borbedarf — Mangel führt zu verformten Blütenköpfen und schlechter Samenbildung. Bor-Düngung: 1–2 kg Borax/ha bei Bormangel-Böden.
- **Kalium (K):** Extrem K-hungrig für Stängelstabilität. K-Mangel zeigt sich als Braunfärbung der Blattränder.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung → Sämling | `time_based` | 7–14 Tage | Keimblätter entfaltet, Hypokotyl aufrecht |
| Sämling → Vegetativ | `time_based` | 14–21 Tage | 4–6 echte Blätter, stabiler Stängel |
| Vegetativ → Blüte | `gdd_based` | GDD ca. 800–1200 (T_base = 7.2 °C, USDA-Standard) / ~600–900 (T_base = 10 °C, europaeischer Standard) | Blütenknospe sichtbar (R1-Stadium); Heliotropismus endet — Blüte zeigt dauerhaft nach Osten |
| Blüte → Fruchtreife | `event_based` | 14–28 Tage | Blütenblätter verwelkt, Bestäubung abgeschlossen, Rückseite des Blütenkorbs verfärbt sich gelb |
| Fruchtreife → Seneszenz | `conditional` | 21–42 Tage | Blütenkorb braun, hängt nach unten, Samen lösen sich bei Berührung; Feuchte der Kerne < 15 % |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Beet/Topf)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|----------------|--------|
| Universaldünger flüssig | Compo | Volldünger | 7-3-6 | ~0.08 | 3 | vegetativ |
| Tomatendünger flüssig | Substral (Scotts) | PK-betont | 6-12-9 | ~0.10 | 3 | blüte, fruchtreife |
| Blaukorn Novatec | Compo Expert | Depot-Dünger | 14-7-17 (+2 MgO) | — (Granulat) | — | vegetativ (einmalig bei Pflanzung) |
| CalMag | Canna | Supplement | 0-0-0 + 5 % Ca, 2 % Mg | ~0.05 | 2 | alle |
| Bor-Blattdünger | Compo / Lebosol | Mikronährstoff | — + 11 % B | — (Sprühanwendung) | — | vegetativ, blüte (bei Bormangel) |

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | Bodenverbesserer | 5–8 L/m² | Frühjahr bei Pflanzung | Grundversorgung |
| Hornspäne (grob) | Oscorna / Neudorff | Langzeit-N | 80–120 g/m² | Frühjahr einarbeiten | Starkzehrer |
| Rinderdung-Pellets | Oscorna Animalin | Volldünger | 100–150 g/m² | Frühjahr einarbeiten | Starkzehrer |
| Holzasche | eigen | K-Quelle | 100–200 g/m² (maximal!) | Frühjahr | K-Nachlieferung (Vorsicht: pH-Anstieg) |
| Beinwell-Jauche | eigen | K-reiche Flüssigdüngung | 1:10 verdünnt, wöchentlich | Vegetativ bis Blüte | Starkzehrer, K-Nachlieferung |

### 3.2 Düngungsplan (Beispiel: Freiland-Beetkultur)

| Woche | Phase | EC (mS) | pH | Düngung | Hinweise |
|-------|-------|---------|-----|---------|----------|
| 0 | Beetvorbereitung | — | 6.0–6.8 | 5–8 L/m² Kompost + 100 g/m² Hornspäne einarbeiten | 2 Wochen vor Aussaat |
| 1–2 | Keimung | 0.0 | 6.0–6.5 | nur Wasser | Kein Dünger — Keim benötigt nur Samennährstoffe |
| 3–5 | Sämling | 0.8–1.0 | 6.0–6.5 | Flüssigdünger 2 ml/L alle 14 Tage | Bei Topfkultur/Voranzucht |
| 6–12 | Vegetativ | 1.5–2.2 | 6.0–6.8 | Volldünger wöchentlich ODER 50 g/m² Blaukorn alle 4 Wochen | Hauptwachstumsphase — höchster N-Bedarf |
| 13–16 | Blüte | 1.5–2.0 | 6.0–6.8 | PK-betonter Dünger (Tomatendünger) alle 2 Wochen + Beinwell-Jauche | P und K für Blüte und Samenansatz |
| 17–20 | Fruchtreife | 1.0–1.5 | 6.0–6.8 | Düngung reduzieren; letzte Gabe 3 Wochen vor Ernte | Überdüngung verzögert Abreife |

### 3.3 Mischungsreihenfolge

> **Kritisch bei Flüssigdüngung (Topfkultur):**

1. CalMag (falls benötigt — besonders bei RO-Wasser oder kalkarmem Wasser)
2. Basisdünger (Volldünger oder Tomatendünger)
3. Bor-Supplement (falls Bormangel diagnostiziert — NICHT prophylaktisch, Bor-Toxizität eng!)
4. pH-Korrektur (IMMER zuletzt — Ziel pH 6.0–6.8)

### 3.4 Besondere Hinweise zur Düngung

- **Starkzehrer:** Sonnenblumen sind extrem nährstoffhungrig. Ein 2-m-Exemplar transpiriert an heissen Tagen 3–5 Liter Wasser und benötigt entsprechend Nährstoffe.
- **Bor:** Sonnenblumen haben den höchsten Borbedarf aller gängigen Kulturpflanzen. Bormangel führt zu hohlen Stängeln, verformten Blütenköpfen und schlechter Samenbildung. Bor-Blattdüngung (150 ppm Borsäurelösung) bei ersten Mangelsymptomen.
- **Kalium:** Entscheidend für Stängelstabilität (verhindert Umknicken) und Samenqualität (Ölgehalt). K-Mangel: nekrotische Blattränder, beginnend an älteren Blättern.
- **Kein Frischmist!** Stickstoff-Überschuss führt zu weichem Gewebe und erhöhter Pilzanfälligkeit (Sclerotinia).
- **Allelopathie-Warnung:** Sonnenblumenreste (Stängel, Blütenköpfe, Wurzeln) enthalten allelopathische Substanzen. Nicht direkt in den Boden einarbeiten und sofort nachbestellen — mindestens 4–6 Wochen Kompostierung oder Entfernung vor Nachkultur.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `outdoor_annual_veg` (am besten passend — einjährige Freilandkultur mit hohem Pflegebedarf) | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2 (bei Hitze und Trockenheit täglich; grosse Pflanzen transpirieren enorm) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig, keine Winterkultur) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | `top_water` (an den Fuss giessen, Blütenkörbe trocken halten) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | null (Leitungswasser problemlos) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 (Flüssigdüngung) oder einmalig Depotdünger bei Pflanzung | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5, 6, 7, 8, 9 (Mai–September — gesamte Kulturzeit) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | null (Freilandkultur, einjährig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Freiland) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Saatgut besorgen | Sortenwahl: Riesen (2–3 m), Zwerge (30–60 cm), verzweigend (Schnittblumen), pollenarm (Vasenblumen) | niedrig |
| Apr | Beetvorbereitung | Kompost + Hornspäne einarbeiten. Boden lockern bis 30 cm Tiefe (Pfahlwurzel!). Ggf. Vorkultur in Töpfen starten. | mittel |
| Mai | Direktsaat/Pflanzung | Nach den Eisheiligen (ab 15. Mai): Direktsaat 2–3 cm tief, Abstand 40–60 cm. Stützstab bei Riesensorten gleich mit einsetzen! | hoch |
| Jun | Vegetatives Wachstum | Wöchentlich düngen. Tiefgründig giessen (fördert tiefe Durchwurzelung). Mulchen mit Stroh (5 cm). Schnecken kontrollieren. | hoch |
| Jul | Blütenbeginn | PK-betonte Düngung. Stützstab festbinden (Windbruchgefahr!). Bestäuber beobachten. Bor-Symptome prüfen. | hoch |
| Aug | Blüte + Fruchtansatz | Verwelkte Blütenblätter entfernen (Botrytis-Prävention). Bewässerung beibehalten. Vogelschutz anbringen (Netz/Vlies über Samenköpfe). | mittel |
| Sep | Samenreife | Bewässerung reduzieren. Düngung einstellen. Reife prüfen: Blütenkorb braun, Samen lösen sich bei Berührung, Feuchte < 15 %. | mittel |
| Okt | Ernte + Aufräumen | Samenköpfe ernten und nachtrocknen (Luftig, trocken, 1–2 Wochen). Stängel NICHT einarbeiten — Allelopathie! Kompostieren oder entsorgen. | hoch |

### 4.3 Überwinterung

Entfällt — einjährige Kultur. Nach Samenreife stirbt die Pflanze ab.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse (Aphids) | Aphis fabae, Myzus persicae | Verkrüppelte Triebspitzen, Honigtau, Russtau; besonders an jungen Blättern und Blütenknospen | leaf, flower | vegetative, flowering | easy |
| Schnecken (Slugs) | Arion vulgaris, Deroceras reticulatum | Frass an Keimblättern und jungen Blättern; Totalverlust bei Sämlingen möglich | leaf, stem | germination, seedling | easy |
| Sonnenblumenmotte | Homoeosoma nebulella | Larven bohren sich in Samenkörner, Mehl und Gespinste im Blütenkorb | flower, seed | ripening | hard |
| Drahtwürmer (Wireworms) | Agriotes spp. | Frass an Wurzeln und Sämlingsstängeln unter der Erdoberfläche, Welke | root, stem | germination, seedling | hard |
| Vögel (Birds) | Passer domesticus (Spatz), Carduelis carduelis (Stieglitz) | Samenfrass direkt am Blütenkorb | seed | ripening | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Sklerotinia-Fäule (White Mold) | `fungal` | Weisses, wattiges Mycel am Stängelgrund oder Blütenkorb, schwarze Sklerotien, Welke | Feuchtigkeit, dichter Stand, Stickstoff-Überschuss | 7–14 | flowering, ripening |
| Grauschimmel (Botrytis) | `fungal` | Grauer Pilzrasen auf Blütenblättern und Samenkörpern, Fäulnis am Blütenkorb | Hohe Luftfeuchtigkeit, Regen auf Blütenkorb | 3–7 | flowering, ripening |
| Falscher Mehltau (Downy Mildew) | `fungal` | Gelbliche Flecken auf Blattoberseiten, grauer Belag unterseits | Kühle, feuchte Witterung im Frühjahr (Plasmopara halstedii) | 7–14 | seedling, vegetative |
| Sonnenblumenrost (Rust) | `fungal` | Orangebraune Pusteln auf Blattunterseiten, Blattverlust | Feuchtigkeit, Temperaturwechsel (Puccinia helianthi) | 7–10 | vegetative, flowering |
| Verticillium-Welke | `fungal` | Einseitige Welke, braune Verfärbung der Leitungsbahnen im Stängelquerschnitt | Bodenbürtige Infektion, schwere Böden | 14–21 | vegetative, flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarven) | Blattläuse | 5–10 | 14 |
| Coccinella septempunctata (Marienkäfer) | Blattläuse | 5–10 | 14–21 |
| Steinernema feltiae (Nematoden) | Drahtwürmer (begrenzte Wirkung) | 500.000/m² | 14–28 |
| Phasmarhabditis hermaphrodita (Schneckennematoden) | Nacktschnecken | 300.000/m² | 7–14 |
| Trichogramma spp. (Eiparasiten) | Sonnenblumenmotte | 100.000/ha (Karten) | 14–21 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | `biological` | Azadirachtin | Sprühen, 0.5 % Lösung | 3 (bei Kerngewinnung; 0 bei Zierpflanze) | Blattläuse |
| Kaliseife | `biological` | Kaliumsalze von Fettsäuren | Sprühen, 2 % Lösung | 0 | Blattläuse |
| Schneckenkorn (Eisen-III-Phosphat) | `chemical` | Eisen-III-Phosphat | Streuen, 5 g/m² | 0 | Schnecken |
| Vogelschutznetz | `mechanical` | — | Über Blütenkorb ab Samenansatz | 0 | Vögel |
| Mulchen + weiter Pflanzabstand | `cultural` | — | 5 cm Strohmulch, min. 40 cm Abstand | 0 | Sclerotinia, Botrytis (Luftzirkulation) |
| Fruchtfolge einhalten | `cultural` | — | Mindestens 3 Jahre keine Asteraceae auf gleicher Fläche | 0 | Sclerotinia, Verticillium, Sonnenblumenrost |
| Contans WG | `biological` | Coniothyrium minitans | Einarbeiten in Boden vor Kultur, 2–4 kg/ha | 0 | Sclerotinia (biologische Sklerotien-Zersetzung) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Falscher Mehltau (partielle Resistenz bei bestimmten Cultivars) | Krankheit | `resistant_to` |

Hinweis: Resistenz gegen Plasmopara halstedii ist sortenabhängig und rassenspezifisch. Cultivars mit Resistenz-Gen Pl (z.B. einige USDA-Lines) bieten Schutz gegen bestimmte Rassen, aber nicht alle.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (`heavy_feeder`) |
| Fruchtfolge-Kategorie | Korbblütler (Asteraceae) |
| Empfohlene Vorfrucht | Hülsenfrüchtler (Fabaceae — Bohne, Erbse; hinterlassen Reststickstoff) oder Getreide (Poaceae — Bodenstruktur) |
| Empfohlene Nachfrucht | Schwachzehrer (Lamiaceae, Violaceae) oder Gründüngung (Phacelia, Senf); NICHT direkt Salat oder Getreide (Allelopathie-Rückstände!) |
| Anbaupause (Jahre) | 3–4 Jahre gleiche Fläche (Asteraceae), um Sclerotinia-Inokulum und Verticillium im Boden zu reduzieren |

**Allelopathie-Warnung:** Sonnenblumenreste setzen beim Abbau allelopathische Substanzen frei (Heliannuol A–E, Chlorogensäure). Empfindliche Nachkulturen (Salat, Weizen, Kartoffel) sollten frühestens 4–6 Wochen nach Einarbeitung oder Entfernung der Rückstände folgen.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Buschbohne | Phaseolus vulgaris | 0.8 | N-Fixierung ergänzt den N-Hunger der Sonnenblume; Bohnen profitieren vom Windschutz | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Sonnenblume als Windschutz und Rankhilfe; Bodendeckung durch Gurkenlaub | `compatible_with` |
| Mais | Zea mays | 0.7 | Ähnliche Standortansprüche (volle Sonne, viel Wasser); gegenseitiger Windschutz in Reihen | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes patula | 0.8 | Nematoden-Abwehr durch Thiophen-Exsudate; Bestäuber-Magnet | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Fangpflanze (lenkt Läuse von Sonnenblume ab); Bodendeckung | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Windschutz fuer Dill, gemeinsam Nuetzlinge und Bestauber anlocken | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Allelopathische Hemmung durch Sonnenblumen-Wurzelexsudate; Konkurrrenz um Nährstoffe und Wasser | `severe` | `incompatible_with` |
| Kopfsalat | Lactuca sativa | Allelopathische Hemmung — Keimungs- und Wachstumshemmung durch Heliannuol nachgewiesen | `severe` | `incompatible_with` |
| Stiefmütterchen | Viola x wittrockiana | Licht- und Nährstoffkonkurrenz (2-m-Sonnenblume beschattet komplett); allelopathische Hemmstoffe | `moderate` | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Gegenseitige allelopathische Hemmung (Fenchel hemmt viele Asteraceae) | `moderate` | `incompatible_with` |
| Zichorie / Wegwarte | Cichorium intybus | Allelopathie durch Sonnenblumen-Wurzelexsudate, Beschattung | `mild` | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Asteraceae (intern) | `shares_pest_risk` | Sclerotinia sclerotiorum, Botrytis cinerea, Blattläuse (Aphis fabae), Sonnenblumenrost | `shares_pest_risk` |
| Solanaceae | `shares_pest_risk` | Verticillium dahliae (bodenbürtiger Pilz; befällt sowohl Helianthus als auch Solanum) | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Sonnenblume |
|-----|-------------------|-------------|------------------------------|
| Topinambur (Erdbirne) | Helianthus tuberosus | Gleiche Gattung, perennial | Mehrjährig, essbare Knollen, Windschutz; ACHTUNG: kann invasiv werden! |
| Mexikanische Sonnenblume | Tithonia rotundifolia | Ähnliche Optik, Asteraceae | Hitzeverträglicher, buschiger Wuchs, geringere Allelopathie |
| Cosmea (Schmuckkörbchen) | Cosmos bipinnatus | Asteraceae, einjährig, ähnliche Kultur | Weniger Nährstoffbedarf (Mittelzehrer), filigraner, windstabiler |
| Ringelblume | Calendula officinalis | Asteraceae, einjährig, essbar | Deutlich anspruchsloser, Schwachzehrer, Heilpflanze, Nematoden-Prävention |
| Rudbeckia (Sonnenhut) | Rudbeckia hirta | Ähnliche Optik (gelbe Strahlenblüte), Asteraceae | Auch einjährig/biennial, kompakter, weniger allelopathisch |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,bloom_months,harvest_months,direct_sow_months,sowing_indoor_weeks_before_last_frost,sowing_outdoor_after_last_frost_days,traits
Helianthus annuus,Sonnenblume;Common Sunflower;Sunflower,Asteraceae,Helianthus,annual,day_neutral,herb,taproot,2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b,-0.6,Nordamerika (Great Plains),tender,heavy_feeder,7;8;9,8;9;10,5;6,4,0,ornamental;edible;bee_friendly
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type
Sunrich Gold,Helianthus annuus,Takii Seed,--,single_stem;pollenless;cut_flower;uniform_height,f1_hybrid
Mammoth Grey Stripe,Helianthus annuus,--,--,giant;edible_seeds;vigorous;tall,open_pollinated
Teddy Bear,Helianthus annuus,--,--,dwarf;double_flower;compact;container_suitable,open_pollinated
Velvet Queen,Helianthus annuus,--,--,branching;dark_red;cut_flower;ornamental,open_pollinated
ProCut Orange,Helianthus annuus,Sakata Seed,--,single_stem;pollenless;cut_flower;early_flowering,f1_hybrid
Autumn Beauty,Helianthus annuus,--,--,branching;multicolor;tall;ornamental,open_pollinated
```

---

## Quellenverzeichnis

1. USDA Plants Database — Helianthus annuus: https://plants.usda.gov/home/plantProfile?symbol=HEAN3
2. University of Minnesota Extension — Growing Sunflowers: https://extension.umn.edu/flowers/growing-sunflowers
3. Royal Horticultural Society — Helianthus annuus: https://www.rhs.org.uk/plants/8297/helianthus-annuus/details
4. Purdue University — Allelopathy in Sunflower (Macias et al.): https://www.hort.purdue.edu/newcrop/proceedings/allelopathy.html
5. Hortipendium — Sonnenblume Pflanzenschutz: https://www.hortipendium.de/Sonnenblume
6. BLE — Sonnenblumenanbau in Deutschland: https://www.ble.de
7. ASPCA — Sunflower: Non-toxic to Dogs and Cats
8. Kamerplanter Spec REQ-001 v3.1 — Asteraceae Seed-Daten (botanical_families, rotation_after, shares_pest_risk)
