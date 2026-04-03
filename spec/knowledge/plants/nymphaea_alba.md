# Weiße Seerose — Nymphaea alba

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-04-02
> **Quellen:** Wikipedia Nymphaea alba, RHS Plant Database, PFAF Plant Database, Gartenteich-Ratgeber.com, Seerosenfarm.de, Teichpflanzen-Teichbau.com, NC State Extension, Gardenia.net

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Nymphaea alba | `species.scientific_name` |
| Volksnamen (DE/EN) | Weiße Seerose; White Water Lily, European White Waterlily | `species.common_names` |
| Familie | Nymphaeaceae | `species.family` → `botanical_families.name` |
| Gattung | Nymphaea | `species.genus` |
| Ordnung | Nymphaeales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–10b (winterharte Arten); 9a–12b (tropische Arten) | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy (Nymphaea alba); tender (tropische Sorten) | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25 °C (Zone 4); Rhizom bleibt frostfrei im Teichschlamm ab 60 cm Wassertiefe. Tropische Sorten frostfrei bei min. 10 °C überwintern. | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, gemäßigtes Asien (Nymphaea alba); Tropen/Subtropen weltweit (tropische Arten) | `species.native_habitat` |
| Allelopathie-Score | -0.2 (leicht hemmend durch abgestorbene Biomasse, Algenkonkurrenz durch Beschattung positiv) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

> **Aquatischer Hinweis:** Nymphaea ist vollständig aquatisch — sämtliche Wuchsparameter beziehen sich auf die submerse/emerse Wuchsform im Teich oder Pflanzkorb. Die Pflanze wächst vom Substrat am Teichboden aus, Blätter und Blüten schwimmen an der Wasseroberfläche. Klassische Kübel-/Topfkultur-Parameter (Substrat, Topfvolumen) entsprechen hier dem Pflanzkorb im Teich.

### 1.2 Sortengruppen-Übersicht

| Gruppe | Herkunft | Winterhärte | Blütezeit | Wassertiefe | Blütenfarbe | USDA Zone |
|--------|----------|-------------|-----------|-------------|-------------|-----------|
| **Winterharte Seerosen** (Nymphaea-Hybriden) | Europa, Nordamerika | Hardy (bis -25 °C) | Jun–Sep | 30–100 cm | Weiß, Rosa, Rot, Gelb, Violett | 4–10 |
| Nymphaea alba (Wildform) | Europa, N-Afrika | Hardy | Jul–Aug | 50–300 cm | Weiß | 4–10 |
| Nymphaea odorata (duftend) | Nordamerika | Hardy | Jun–Sep | 30–90 cm | Weiß, duftend | 3–11 |
| Nymphaea 'James Brydon' | Hybrid | Hardy | Jun–Sep | 30–60 cm | Karminrot | 3–11 |
| Nymphaea 'Escarboucle' | Hybrid | Hardy | Jun–Sep | 40–80 cm | Kirschrot | 4–11 |
| Nymphaea 'Marliacea Chromatella' | Hybrid | Hardy | Jun–Sep | 40–80 cm | Gelb | 4–10 |
| **Tropische Seerosen (tagblühend)** | Tropen/Subtropen | Tender (min. 10 °C) | Jul–Sep | 20–50 cm | Blau, Violett, Weiß, Rosa, Gelb | 9–12 |
| Nymphaea capensis | Südafrika | Tender | Jul–Sep | 30–60 cm | Hellblau | 9–12 |
| Nymphaea coerulea | Nordafrika, Ägypten | Tender | Jul–Sep | 20–50 cm | Hellblau | 9–12 |
| **Tropische Seerosen (nachtblühend)** | Tropen | Tender | Aug–Sep | 30–60 cm | Rot, Rosa, Weiß | 9–12 |
| Nymphaea lotus | Ostafrika, Asien | Tender (Aquarium) | Ganzjährig | 20–60 cm | Weiß, Rot | 9–12 |

### 1.3 Aussaat- & Pflanzzeiträume

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor Auspflanzung) | 8–12 (Anzucht aus Samen in flachem, warmem Wasser ab 20 °C) | `species.sowing_indoor_weeks_before_last_frost` |
| Pflanzung in den Teich (nach letztem Frost) | 14–28 Tage (Wassertemperatur min. 10–12 °C) | `species.sowing_outdoor_after_last_frost_days` |
| Pflanz-Monate (Rhizomteilung/Einsetzen) | 5, 6 | `species.direct_sow_months` |
| Blütemonate (winterharte Sorten) | 6, 7, 8, 9 | `species.bloom_months` |
| Blütemonate (tropische Sorten) | 7, 8, 9 | `species.bloom_months` |
| "Ernte" (Samenkapseln/Rhizomteilung) | 8, 9, 10 | `species.harvest_months` |

### 1.4 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division (Rhizomteilung, Mai–Juni), seed (Aussaat in Wasser), offset (Kindpflanzen bei tropischen Sorten) | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

> **Praxishinweis Rhizomteilung:** Das Rhizom alle 3–5 Jahre teilen. Mit einem scharfen, sauberen Messer ein ca. 15 cm langes Stück von der Spitze abtrennen — es muss mindestens 2–3 Wachstumsaugen aufweisen. Schnittstellen sofort mit Aktivkohle bestäuben, um Fäulnis zu verhindern. Anschließend schräg im Substrat verankern (Spitze zeigt nach oben, ca. 45°-Winkel).

### 1.5 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannten stark giftigen Teile; Rhizom enthält Gerbstoffe (adstringierend) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Nuphar-Alkaloide gering (hauptsächlich Nupharin) im Rhizom; in der Zubereitung volksheilkundlich genutzt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Pollen schwimmt auf Wasser, kein Windflug) | `species.allergen_info.pollen_allergen` |

### 1.6 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (Frühjahr: verrottete Blätter entfernen), 9, 10 (Herbst: abgestorbene Teile bis knapp über Rhizom kürzen) | `species.pruning_months` |

> **Praxishinweis Schnitt:** Vergilbende Blätter und abgeblühte Stängel konsequent entfernen — sie verrotteten im Wasser und belasten die Wasserqualität. Schnitt möglichst tief am Rhizom, nie die Pflanze in der Wachstumssaison (Jun–Aug) stark zurückschneiden.

### 1.7 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (Pflanzkorb im Teich; Miniteich auf Balkon möglich mit kleinen Sorten) | `species.container_suitable` |
| Empf. Pflanzkorb-Volumen (L) | 5–10 (Zwergsorten), 10–20 (mittelgroße Sorten), 20–40 (großwüchsige Sorten wie N. alba) | `species.recommended_container_volume_l` |
| Min. Wassersäule über Rhizom (cm) | 20 (Zwergsorten), 40–60 (mittelgroße Sorten), 60–150 (N. alba Wildform) | `species.min_container_depth_cm` |
| Wuchshöhe über Wasser (cm) | 10–30 (Blüten/Blätter erheben sich 10–30 cm über Oberfläche) | `species.mature_height_cm` |
| Ausbreitung Wasseroberfläche (cm) | 60–300 (je nach Sorte: Zwerg 60–100 cm, mittel 100–200 cm, groß 200–300 cm) | `species.mature_width_cm` |
| Platzbedarf Teichfläche (m²) | 0.3–1 (Zwerg), 1–3 (mittel), 3–6 (groß) | `species.spacing_cm` |
| Indoor-Anbau | limited (tropische Sorten als Aquariumpflanze oder Winterquartier-Becken) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Miniteich-Kübel mit Zwergsorten: N. 'Pygmaea Alba', N. tetragona) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (winterharte Sorten); true (tropische Sorten für Überwinterung) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Pflanzkorb) | Schwere, lehmige Gartenerde mit 50–80 % Tonanteil; KEIN Torf, KEIN Kompost (würde im Wasser vergären). Alternativ: spezielles Seerosensubstrat (handelsüblich). Obere Schicht: 3–5 cm feiner Kies als Abdeckung gegen Aufwirbelung. | — |

---

## 2. Wachstumsphasen

> **Aquatische Besonderheit:** Das Phasenmodell für Seerosen weicht von terrestrischen Pflanzen ab. Statt Keimung aus Samen (bei Züchtern) dominiert im Teich die vegetative Vermehrung. Der Jahreszyklus folgt der Wassertemperatur und der Tageslänge (Photoperiode). Alle Temperaturangaben beziehen sich auf die Wassertemperatur.

### 2.1 Phasenübersicht (Winterharte Sorten — Jahreszyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe (Dormanz) | 120–180 (Nov–Apr) | 1 | false | false | high |
| Austrieb (Frühjahr) | 21–42 (Apr–Mai) | 2 | false | false | low |
| Vegetatives Wachstum | 28–56 (Mai–Jun) | 3 | false | false | medium |
| Blüte & Vollwachstum | 60–90 (Jun–Sep) | 4 | false | true | medium |
| Seneszenz (Herbst) | 28–56 (Sep–Okt) | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Winterruhe (Dormanz)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 (unter Wasser/Eis, keine Anforderung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–1 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | nicht relevant (Rhizom unter Wasser ruhend) | `requirement_profiles.photoperiod_hours` |
| Wassertemperatur (°C) | 1–8 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit (%) | 100 (aquatisch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | nicht anwendbar | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | nicht anwendbar | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | nicht anwendbar (stehendes Gewässer) | `requirement_profiles.irrigation_frequency_days` |
| Wassertiefe (cm) | min. 60 (frostfreie Zone, Teichboden) | — |
| Düngung | keine | — |

#### Phase: Austrieb (Frühjahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (natürliches Tageslicht) | `requirement_profiles.photoperiod_hours` |
| Wassertemperatur Tag (°C) | 10–16 | `requirement_profiles.temperature_day_c` |
| Wassertemperatur Nacht (°C) | 6–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit (%) | 100 (aquatisch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | nicht anwendbar | `requirement_profiles.vpd_target_kpa` |
| Wassertiefe Pflanzkorb (cm) | 10–20 (flach stellen, fördert Erwärmung und frühen Austrieb) | — |
| Düngung | erste Depot-Tablette eindrücken wenn erste Blätter erscheinen | — |

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag) | `requirement_profiles.photoperiod_hours` |
| Wassertemperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Wassertemperatur Nacht (°C) | 12–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit (%) | 100 (aquatisch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | nicht anwendbar | `requirement_profiles.vpd_target_kpa` |
| Wassertiefe Pflanzkorb (cm) | 20–40 (je nach Sorte langsam tiefer stellen) | — |
| Düngung | 1× monatlich Depot-Tablette | — |

#### Phase: Blüte & Vollwachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 800–2000 (volle Sonne optimal, min. 4–6 h/Tag direkte Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (min. 4–6 h direkte Mittagssonne) | `requirement_profiles.photoperiod_hours` |
| Wassertemperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Wassertemperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit (%) | 100 (aquatisch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | nicht anwendbar | `requirement_profiles.vpd_target_kpa` |
| Wassertiefe Pflanzkorb (cm) | 30–80 (sortenabhängig, Endposition) | — |
| Düngung | alle 4–6 Wochen Depot-Tablette, letzter Dünger spätestens Aug | — |

#### Phase: Seneszenz (Herbst)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 (sinkende Lichtstunden, Herbst) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–13 (abnehmend) | `requirement_profiles.photoperiod_hours` |
| Wassertemperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Wassertemperatur Nacht (°C) | 6–12 | `requirement_profiles.temperature_night_c` |
| Wassertiefe Pflanzkorb (cm) | 60–100 (tiefer stellen vor dem Winter) | — |
| Düngung | keine | — |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | pH (Wasser) | Ca (ppm) | Mg (ppm) | Fe (ppm) | Hinweis |
|-------|----------------|-------------|----------|----------|----------|---------|
| Winterruhe | 0:0:0 | 6.5–8.5 (Teich-pH) | — | — | — | keine Düngung |
| Austrieb | 5:10:5 (Anwurzeln fördern) | 6.5–7.5 | 40–60 | 10–20 | 1 | 1 Depot-Tab wenn Blätter erscheinen |
| Vegetativ | 10:6:6 (Wachstum) | 6.5–7.5 | 60–80 | 20–30 | 2 | 1× monatlich |
| Blüte | 10:10:10 bis 5:10:5 (Blütenförderung) | 6.5–7.5 | 60–80 | 20–30 | 2 | alle 4–6 Wochen |
| Seneszenz | 0:0:0 | 6.5–8.5 | — | — | — | keine Düngung ab Sep |

> **Hinweis Wasserchemie:** Nymphaea toleriert ein breites pH-Spektrum (6.0–8.5). Entscheidend ist, dass Nährstoffe ausschließlich über Depot-Tabletten direkt ins Substrat des Pflanzkorbs gelangen — niemals flüssige Dünger ins Teichwasser geben, da dies Algenwachstum massiv fördert.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Zeitfenster | Bedingung |
|------------|---------|-------------|-----------|
| Winterruhe → Austrieb | conditional | März–April | Wassertemperatur dauerhaft über 8–10 °C |
| Austrieb → Vegetativ | time_based | 3–6 Wochen nach ersten Blättern | Erste schwimmende Blätter an Oberfläche |
| Vegetativ → Blüte | event_based | Mai–Juni | Erste Blattstiele nehmen Schirm-Form an, Wassertemperatur über 16 °C |
| Blüte → Seneszenz | event_based | September–Oktober | Tageslänge unter 12 h, Wassertemperatur unter 14 °C |
| Seneszenz → Winterruhe | time_based | Oktober–November | Blätter vollständig eingezogen, Wassertemperatur unter 8 °C |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Grundprinzip aquatischer Düngung

> **Kritischer Unterschied zur terrestrischen Düngung:** Bei Seerosen im Teich darf **ausschließlich** Depot-Dünger (Tabletten, Kegel, Stäbchen) verwendet werden, der direkt in das Substrat des Pflanzkorbs gedrückt wird. Flüssigdünger oder wasserlösliche Granulate ins Teichwasser geben ist **verboten** — dies führt unmittelbar zu massivem Algenwachstum (Fadenalgen, Blaualgen) und kippen der Wasserqualität.

### 3.2 Empfohlene Düngerprodukte

#### Depot-Tabletten & Langzeitdünger (Hauptmethode)

| Produkt | Marke | Typ | NPK | Wirkdauer | Anwendung | Phasen |
|---------|-------|-----|-----|-----------|-----------|--------|
| SeeroseVital Depot-Düngerkegel | SBM (Substral) | Langzeit-Depot | 10-6-6 | 3 Monate | 1 Kegel/Pflanze, 10 cm tief | Austrieb, Vegetativ, Blüte |
| Seerosentabletten | Tetra Pond / Pond Technologie | Depot-Tab | 10-10-10 | 4–6 Wochen | 1 Tab/Pflanze, 8–10 cm tief | Vegetativ, Blüte |
| Aquatic Plant Fertilizer Tablets | Oase | Langzeit-Depot | 7-5-6 + Mikro | 3–4 Monate | 2–3 Tabs/Pflanzkorb | Austrieb, Vegetativ, Blüte |
| Waterplant Fertiliser Spikes | Westland | Depot-Stäbchen | 5-10-5 | 6–8 Wochen | 2 Stäbchen/Pflanzkorb | Austrieb, Blüte |

#### Organische Optionen (Basis-Substrat-Anreicherung)

| Produkt | Typ | Ausbringrate | Anwendung | Hinweis |
|---------|-----|-------------|-----------|---------|
| Hornspäne (gemahlen) | Organisch, langsam | 20–30 g je Pflanzkorb (Untermischung) | Beim Einpflanzen ins Substrat mischen | Nur beim Neumischen des Substrats — nicht nachträglich ins Teichwasser geben |
| Blut- und Knochenmehl | Organisch | 15–20 g je Pflanzkorb | Beim Einpflanzen einarbeiten | Gleiche Einschränkung wie Hornspäne |
| Lehm-Tonkugeln (nährstoffreich) | Natürliches Substrat | Als Pflanzsubstrat-Basis | Beim Einpflanzen in Körbe | Kein Kompost oder Torf — vergärt im Wasser |

### 3.3 Düngungsplan (Jahresübersicht)

| Monat | Phase | Maßnahme | Produkt | Menge | Hinweise |
|-------|-------|----------|---------|-------|----------|
| Apr | Austrieb | 1. Depot-Düngung | Depot-Kegel/Tab | 1 Tab oder 1 Kegel pro Pflanzkorb | Erst wenn erste Blätter an der Oberfläche erscheinen |
| Mai | Vegetativ | Düngung | Seerosentabletten | 1 Tab pro Pflanzkorb | 10 cm tief ins Substrat drücken |
| Jun | Vegetativ/Blüte | Düngung | Seerosentabletten | 1 Tab pro Pflanzkorb | alle 4–6 Wochen Rhythmus |
| Jul | Blüte | Düngung | Seerosentabletten | 1 Tab pro Pflanzkorb | Hochblüte — regelmäßige Versorgung sichert Blütenanzahl |
| Aug | Blüte | letzte Düngung | Seerosentabletten | 1 Tab pro Pflanzkorb | Letzter Dünger der Saison, max. Ende August |
| Sep–Mär | Seneszenz/Dormanz | keine Düngung | — | — | Pflanze zieht sich zurück, keine Nährstoffaufnahme |

### 3.4 Mischungsreihenfolge bei Depot-Tabletten

> Bei Depot-Tabletten gibt es keine klassische Mischungsreihenfolge wie bei Flüssigdüngern. Die Anwendungsreihenfolge im Jahresverlauf:

1. **Substrat-Vorbereitung beim Einpflanzen:** Hornspäne/Knochenmehl vorab in Lehmerde einmischen
2. **Erste Depot-Tablette im April** (beim ersten Blattaustrieb), ca. 8–10 cm tief neben dem Rhizom platzieren
3. **Folgedüngungen alle 4–6 Wochen** (Mai bis August) an verschiedenen Stellen rund um das Rhizom platzieren
4. **Nicht auf der Rhizom-Spitze oder direkt an Wurzeltrieben** — 5–10 cm Abstand halten, um Verbrennungen zu vermeiden
5. **Loch mit Daumen oder Stäbchen verschließen** nach dem Eindrücken der Tablette

### 3.5 Besondere Hinweise zur Düngung

Seerosen sind klassische Starkzehrer und bei optimaler Versorgung extrem blühfreudig. Unterdüngung zeigt sich zuerst durch kleiner werdende Blüten und abnehmende Blütenanzahl. Die Pflanze reagiert im Teich auf Nährstoffüberschuss im Wasser (durch externe Quellen wie Vogelkot, Laubeintrag) mit exzessivem Blattwachstum auf Kosten der Blüten — dann Düngung reduzieren und auf Wasserqualität achten. Regelmäßiger Wasserwechsel (10–20 % monatlich) verhindert Nährstoffüberakkumulation.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `custom` (kein Standard-Preset passt für aquatische Pflanzen; nächstverwandter Preset: `mediterranean` wegen saisonal-ruhender Pflege) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | nicht anwendbar (stehendes Gewässer — Verdunstungsverluste kompensieren: ca. 2–5 cm/Woche im Sommer) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | nicht anwendbar | `care_profiles.winter_watering_multiplier` |
| Gießmethode | nicht anwendbar (Teich) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; pH 6.5–8.5 toleriert; kein stehendes Faulwasser (Teichbelüftung sicherstellen); Koiteich nicht geeignet (Koi fressen Triebe) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28–42 (alle 4–6 Wochen, Depot-Tabletten) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 (April bis August) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–60 (alle 3–5 Jahre Pflanzkorb erneuern und Rhizom teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (aquatisch) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf (12-Monats-Kalender)

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Teichkontrolle | Teich auf Eisbedeckung kontrollieren. Bei vollständigem Zufrieren: Belüftungsloch freihalten (NIEMALS Eis hacken — Druckwellen schädigen Fische). Seerosentriebe schlafen unter Wasser. | niedrig |
| Feb | Planung & Bestellung | Neue Sorten und Pflanzenkörbe bestellen. Substrat (Seerosenerde, Kies) besorgen. Sortenkatalog prüfen. | niedrig |
| Mär | Winterquartier-Kontrolle | Tropische Sorten im Winterbecken kontrollieren: Wassertemperatur, Licht, Fäulnis an Blättern prüfen. Ggf. abgestorbene Blätter entfernen. | mittel |
| Apr | Austrieb einleiten | Pflanzkorb von der Tiefposition (60–100 cm) in Flachwasserzone (10–20 cm) umsetzen — höhere Wassertemperatur und mehr Licht beschleunigen den Austrieb. Erste Depot-Tablette ins Substrat drücken wenn erste Blätter erscheinen (nicht vorher!). Rhizomteilung kann ab Ende April erfolgen. | hoch |
| Mai | Einpflanzen & Umsetzen | Neupflanzungen und Rhizomteilungen jetzt vornehmen (Wassertemperatur min. 10–12 °C). Pflanzkörbe langsam auf Endtiefe absenken (stufenweise über 2–3 Wochen). Erste Düngung (Depot-Tab). Teichrand auf Froschlaich und Nützlinge prüfen. | hoch |
| Jun | Hochsaisonstart | Regelmäßig verblühte Blüten und vergilbte Blätter entfernen. Düngung (Depot-Tab alle 4–6 Wochen). Auf Schädlingsbefall prüfen (Seerosenblattlaus, Seerosenblattkäfer). Algenwachstum beobachten — ggf. Fadenalgen manuell entfernen. | hoch |
| Jul | Hochblüte | Blüten täglich beobachten (öffnen sich morgens, schließen nachmittags). Abgefallene Blüten und absterbende Blätter täglich entfernen. Depot-Düngung wiederholen wenn 4–6 Wochen seit letzter Gabe vergangen. Wasserverlust durch Verdunstung mit Leitungswasser ausgleichen. | hoch |
| Aug | Nachsommerblüte | Letzte Depot-Düngung der Saison (max. Ende August). Samenkapseln können geerntet werden wenn gewünscht. Pflanzkorb-Kontrolle: Sitzt das Rhizom noch sicher? Teich auf Wasserqualität prüfen (erhöhte Verdunstung, Laubeintrag beginnt). | mittel |
| Sep | Vorbereitung Herbst | Düngung einstellen. Seneszente Blätter und Stängel konsequent entfernen (nicht im Wasser verrotten lassen). Tropische Sorten: Pflanzkorb aus dem Teich holen und einwintern (bevor Wassertemperatur unter 12 °C sinkt). Pflanzkorb für winterharte Sorten langsam auf Tiefposition absenken. | hoch |
| Okt | Herbstpflege | Laubeintrag konsequent aus dem Teich entfernen (Laubschutzgitter über Teich spannen). Verrottende Pflanzenteile entfernen. Teichbelüftung kontrollieren. Letzte Kontrolle aller Pflanzkörbe. Frostwarnung beachten. | hoch |
| Nov | Wintervorbereitung | Alle Pflanzkörbe auf Tiefposition (min. 60–80 cm, für N. alba min. 80–100 cm). Teichpumpe und Technik winterfest machen oder in Betrieb lassen für Sauerstoffversorgung. | mittel |
| Dez | Winterruhe | Teich beobachten, keine aktiven Maßnahmen. Bei gefrorenem Teich: Luftloch über der Pumpe offenhalten. Keine Düngung, kein Eingriff in die Pflanzenkörbe. | niedrig |

---

## 5. Überwinterung

### 5.1 Winterharte Sorten (Nymphaea alba, europäische und nordamerikanische Hybriden)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (bei ausreichender Wassertiefe) / mulch (flache Teiche) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10–11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors (Pflanzkorb vom Teichboden in Flachwasserzone umsetzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 1 (unter Wasser, frostfrei) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 8 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark (unter Wasser, Licht irrelevant während Dormanz) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | none (aquatisch, steht im Wasser) | `overwintering_profiles.winter_watering` |

**Detailbeschreibung winterharte Überwinterung im Teich:**

Die Überwinterung im Teich funktioniert zuverlässig wenn folgende Bedingungen erfüllt sind:

- **Wassertiefe über dem Rhizom:** min. 60 cm (Zone 5–6), min. 80 cm (Zone 4), min. 40 cm (Zone 7–8). Das Rhizom muss unterhalb der Gefrierschicht liegen.
- **Pflanzkorb auf Tiefposition** absenken (Oktober–November), bevor der Teich zufriert.
- Alle absterbenden Blätter und Stängel entfernen — sie verbrauchen beim Verrotten Sauerstoff, was Fische und das Ökosystem belastet.
- **Belüftung aufrechterhalten:** Teichpumpe oder Belüfter verhindert vollständiges Zufrieren und sichert Sauerstoffversorgung.
- Bei sehr flachen Teichen (unter 40 cm): Pflanzkorb in einem kühlen, frostfreien Keller in einer Wanne mit Wasser überwintern (5–8 °C, dunkel).

### 5.2 Tropische Sorten (Nymphaea capensis, N. coerulea, N. lotus u.a.)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (bei Wassertemperatur unter 15–18 °C, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors (nach letztem Frost, Wassertemperatur mind. 18–20 °C) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 6 (frühestens Ende Mai, besser Juni) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 15 (nachtblühende Sorten); 18 (tagblühende Sorten) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 28 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright (min. 10–12 h Kunstlicht, DLI > 15 mol/m²/d) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | normal (stehen weiterhin im Wasser, 20–40 cm Tiefe, beheizt) | `overwintering_profiles.winter_watering` |

**Detailbeschreibung tropische Überwinterung:**

Es gibt zwei praktikable Methoden für Mitteleuropa:

**Methode 1 — Beheiztes Winterbecken (empfohlen):**
Pflanzkorb im September/Oktober in ein beheizbares Aquarium oder Gewächshausbecken umsetzen. Wassertemperatur dauerhaft 18–22 °C halten. Beleuchtung mit Pflanzenlampen (min. 5000 Lumen, Vollspektrum) 10–14 h täglich. Düngung stark reduzieren (1 Depot-Tab pro Saison im Winter). Regelmäßige Wasserwechsel (20 % monatlich).

**Methode 2 — Trocken-Lagerung (als Knolle):**
Einige tropische Sorten bilden Brutknollen (Vivipara-Arten). Knolle nach der Saison aus dem Substrat nehmen, säubern, bei 15–20 °C trocken-kühl (nicht frost!) in leicht feuchtem Sand lagern. Im Frühjahr ab April in warmem Wasser ankeimen.

**Methode 3 — Jährliche Neupflanzung:**
In Mitteleuropa oft wirtschaftlichste Methode: Tropische Seerosen als Saisonneuheiten kaufen (Kosten ca. 5–15 €/Stück), im Herbst kompostieren und im nächsten Jahr neue Pflanzen einsetzen. Empfehlung für Einsteiger.

---

## 6. IPM — Schädlinge, Krankheiten & Behandlungsmethoden

> **Kritischer Aquatik-Hinweis:** Im Gartenteich gilt ein **faktisches Chemikalienverbot** für nahezu alle konventionellen Insektizide und Fungizide. Die Anwendung von Pflanzenschutzmitteln im oder unmittelbar am Gewässer ist in Deutschland nach dem **Wasserhaushaltsgesetz (WHG)** und der **Pflanzenschutz-Anwendungsverordnung** stark reglementiert oder vollständig verboten. Jeder Einsatz chemischer Mittel gefährdet Fische, Amphibien, Wasserinsekten und das gesamte Teich-Ökosystem. **Ausschließlich mechanische und biologische Methoden verwenden.**

### 6.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------|-------------------|------------------------|
| Seerosenblattlaus | Rhopalosiphum nymphaeae | Kolonien auf Blattunterseite und Blüten, hellgelbe Einstichstellen, Honigtau, rußartiger Pilzbelag | leaf, flower | vegetative, flowering | easy |
| Seerosenblattkäfer | Galerucella nymphaeae | Fensterfraß auf Blattoberfläche (braun-glasige Stellen), Larven auf Blattunterseite (gelblich, schleimig), Skelettierung | leaf | vegetative, flowering | medium |
| Seerosenzünsler (Wasserlilienmotte) | Elophila nymphaeata | Röhrenartige Blatt-Gespinste, Blätter von Larven zusammengerollt, Fraßspuren an Blatträndern | leaf | vegetative, flowering | medium |
| Seerosenblattminierfliege | Hydrellia spec. | Minen (helle, gewundene Gänge) im Blatt, Blätter werden fleckig und vergilben | leaf | vegetative | difficult |
| Teichmückenlarven | Chironomidae | Schlammbewohner, kein direkter Schaden an Pflanze; können Substrat aufwühlen | root | alle | medium |
| Wasserschwertlilien-Blattkäfer | Lilioceris merdigera | Ähnlich Seerosenblattkäfer, befällt auch Iris im Uferbereich | leaf | vegetative | medium |

### 6.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-----------------|
| Seerosenfleckenkrankheit | fungal (Ramularia nymphaearum) | Braune, oft rundliche Flecken auf Blattoberfläche, Blätter vergilben und sterben ab | hohe Luftfeuchtigkeit, schlechte Luftzirkulation über Wasseroberfläche, nasse Blätter | 5–14 | vegetative, flowering |
| Rhizomfäule | bacterial/fungal | Weiche, braune bis schwarze Verfärbung des Rhizoms, fauliger Geruch, Pflanze treibt nicht aus | Überdüngung, beschädigte Rhizomstücke, anaerobes Substrat, Staunässe | 14–28 | dormancy, spring |
| Echter Mehltau auf Seerosen | fungal (Erysiphaceae) | Weißer mehliger Belag auf Blattoberfläche | trockene Hitze kombiniert mit kühlen Nächten, schlechte Luftzirkulation | 7–14 | flowering |
| Botrytis-Fäule | fungal (Botrytis cinerea) | Grauer Schimmelbelag auf absterbenden Blättern und Blüten, besonders bei kühlem, nassem Wetter | kühle, feuchte Witterung, abgestorbene Pflanzenteile | 3–7 | senescence |
| Algen-Überwucherung | nicht pathogen (ökologisches Ungleichgewicht) | Grüne Algenmatten, Fadenalgen überdecken Blätter; Pflanze kann nicht photosynthetisieren | Nährstoffüberschuss im Wasser (v.a. Phosphat), zu viel Licht, fehlende Teichbeschattung durch Seerosen | — | alle |

### 6.3 Nützlinge (Biologische Bekämpfung im Teich-Ökosystem)

| Nützling | Ziel-Schädling | Ausbringung/Etablierung | Hinweise |
|----------|---------------|------------------------|---------|
| Froschlaich / Kröten-Ansiedlung | Seerosenzünsler, allgemein Insektenlarven | natürliche Ansiedlung fördern (Laichgewässer anlegen, Uferstreifen) | Wichtigste Präventionsmaßnahme: naturnahes Teich-Ökosystem |
| Blaumeise, Kohlmeise, Teichmolch | Seerosenblattlaus, Seerosenblattkäfer | natürliche Ansiedlung (Nistkästen, naturnahe Bepflanzung am Teichufer) | Vögel lesen Läuse direkt von den Blättern |
| Raubmilben (freilebende Arten) | Blattläuse | natürliche Etablierung im Teichbereich | Kein gezielter Einsatz im Teich möglich |
| Florfliegen-Larven (Chrysoperla carnea) | Seerosenblattlaus | Freilassung an Teichrand-Vegetation | Nicht direkt auf schwimmenden Blättern, wirken aber im Uferbereich |

### 6.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff/Material | Anwendung | Karenzzeit | Gegen | Aquatik-Eignung |
|---------|-----|--------------------|-----------|------------|-------|-----------------|
| Blätter unter Wasser drücken | mechanical | — | Befallene Blätter kurz unter Wasser halten (10–15 Sek.) — Läuse fallen ab und werden von Fischen gefressen | 0 | Seerosenblattlaus | vollständig geeignet |
| Befallene Blätter entfernen | cultural | — | Stark befallene Blätter am Stiel abschneiden und im Hausmüll entsorgen (nicht kompostieren) | 0 | Alle Schädlinge und Pilze | vollständig geeignet |
| Wasserspritzer / starker Wasserstrahl | mechanical | — | Scharfen Wasserstrahl auf Läuse-Kolonien richten | 0 | Seerosenblattlaus | vollständig geeignet |
| Gelbe Leimtafeln (am Teichrand) | mechanical | — | 30–50 cm über der Wasseroberfläche platzieren — fängt fliegende Aphiden und Käfer | 0 | Seerosenblattlaus, Seerosenblattkäfer | vollständig geeignet (nicht über Wasser) |
| Rapsmethode / Ölfilm | biological | reines Rapsöl (sehr geringe Menge) | Nur in absoluten Ausnahmefällen und NUR wenn kein Fischbesatz vorhanden: minimale Menge (1 ml/m² Wasserfläche) auf betroffene Blätter auftragen — KEIN Abtropfen ins Wasser | 0 | Seerosenblattlaus | bedingt (nur ohne Fische, nicht empfohlen) |
| Kupfermittel gegen Pilze | chemical | Kupferhydroxid | VERBOTEN im Gartenteich (WHG § 38, PflSchAnwV) | — | Pilzkrankheiten | nicht geeignet |
| Neem-Öl / Azadirachtin | biological/chemical | Azadirachtin | VERBOTEN im Gartenteich (WHG) | — | Schädlinge allgemein | nicht geeignet |
| Insektizide allgemein | chemical | diverse | VERBOTEN im und am Gartenteich | — | Insekten | absolut verboten |
| Kalkzugabe ins Teichwasser | cultural | Kalk | kann helfen bei sehr niedrigem pH, aber vorsichtig dosieren — pH-Schwankungen schädigen Teichbewohner | 0 | pH-Optimierung | bedingt geeignet (nur wenn pH < 6.5) |

### 6.5 Prävention (wichtigste Maßnahme)

- **Naturnahes Teich-Ökosystem** aufbauen: ausgewogenes Verhältnis von Wasserpflanzen (Seerosen bedecken 30–50 % der Wasseroberfläche), Sauerstoffpflanzen (Wasserpest, Hornkraut), Uferstauden
- **Regelmäßige Blatt-Kontrolle** (alle 14 Tage) auf Larven-Eier und erste Befallszeichen
- **Kranke/vergilbende Blätter sofort entfernen** um Sporenlast und Schädlingsreservoire zu reduzieren
- **Kein Überbesatz** mit Fischen (Koi fressen Seerosen-Triebe direkt; Goldfish in Maßen akzeptabel)
- **Fadenalgen mechanisch entfernen** sobald sie erscheinen (Teichstab oder Harke) bevor sie die Blätter überwachsen

---

## 7. Teichgemeinschaft (Mischkultur im aquatischen Bereich)

> **Hinweis:** Bei Teichpflanzen ersetzt das Konzept der "Teichgemeinschaft" die terrestrische Mischkultur. Es geht nicht um Allelopathie im Bodenbereich, sondern um ökologische Kompatibilität in verschiedenen Teichzonen (Tiefwasser-, Flachwasser-, Sumpfzone, Uferzone) und die gemeinsame Wasserqualitätspflege.

### 7.1 Teichzonen-Gliederung

| Teichzone | Wassertiefe | Seerose-Stellung | Geeignete Begleitpflanzen |
|-----------|-------------|-----------------|--------------------------|
| Tiefwasserzone | 60–150 cm | Großwüchsige Sorten (N. alba, 'Escarboucle') | Krebsschere, Wassernuss (Trapa natans) |
| Mittelwasserzone | 30–60 cm | Mittelgroße Sorten ('James Brydon', 'Marliacea') | Froschbiss, Krebsschere, Wasserhahnenfuß |
| Flachwasserzone | 10–30 cm | Zwergsorten (N. tetragona) | Hechtkraut, Wasserschwertlilie, Pfeilkraut |
| Sumpfzone | 0–10 cm (wechselfeucht) | nicht geeignet | Sumpfdotterblume, Vergissmeinnicht, Iris pseudacorus |
| Uferzone | oberhalb Wasser | nicht geeignet | Rohrkolben, Blutweiderich, Sumpfschwertlilie |

### 7.2 Gute Partner (kompatible Teichgemeinschaft)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | Teichzone | KA-Edge |
|---------|-------------------|----------------------|--------|-----------|---------|
| Froschbiss | Hydrocharis morsus-ranae | 0.9 | Natürliche Algenreduktion durch Beschattung; Insektenhabitat; heimische Art; nimmt nicht überhand | Mittelwasser, frei schwimmend | `compatible_with` |
| Krebsschere | Stratiotes aloides | 0.8 | Sauerstoffproduktion, Wasserfilterung, Wasserqualität, Laichplatz für Amphibien | Mittelwasser/Tiefwasser | `compatible_with` |
| Wasserpest | Elodea canadensis / Egeria densa | 0.7 | Sauerstoffproduktion, Algenhemmung durch Nährstoffentzug, Laichplatz | Tauchwasser | `compatible_with` |
| Hornkraut | Ceratophyllum demersum | 0.8 | Sauerstoffproduktion ohne Wurzeln, sehr pflegeleicht, Wasserklärer | Tauchwasser | `compatible_with` |
| Hechtkraut | Pontederia cordata | 0.8 | Uferbereich, Bestäuber-Attraktivität (Bienen), optischer Kontrast zur Seerose, keine Konkurrenz | Flachwasser/Sumpf | `compatible_with` |
| Sumpfschwertlilie | Iris pseudacorus | 0.7 | Uferbereich, Beschattung vor Algen im Randbereich, heimisch | Sumpf/Ufer | `compatible_with` |
| Pfeilkraut | Sagittaria sagittifolia | 0.8 | Wasserfilterung, Laichplatz, zieht keine Fläche auf Seerosenblättern | Flachwasser | `compatible_with` |
| Wassernabel | Hydrocotyle vulgaris | 0.7 | Lückenbüßer in Flachwasserzone, kein Flächenkämpfer | Sumpf/Flachwasser | `compatible_with` |

### 7.3 Schlechte Partner (Konflikt-Pflanzen im Teich)

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Wasserhyazinthe | Eichhornia crassipes | Extrem wuchsstark, verbreitet sich in wenigen Wochen flächendeckend, verdrängt Seerose durch Beschattung; invasive Art; nicht winterhart | severe | `incompatible_with` |
| Große Teichrose | Nuphar lutea | Direkte Flächenkonkurrenz, ähnliche Tiefenwurzlung; kämpft mit Seerose um Teichfläche und Licht | moderate | `incompatible_with` |
| Koi (Fisch) | Cyprinus rubrofuscus (Zuchtform) | Fressen Seerosen-Triebe, Blätter und Rhizome direkt ab; wühlen Pflanzenkörbe um | severe | `incompatible_with` |
| Wasseraloe / Krebsschere (Überbesatz) | Stratiotes aloides | Bei unkontrollierter Ausbreitung: verdrängt Seerosen durch zu dichte Beschattung der Wasseroberfläche | moderate | `incompatible_with` |
| Enten (Wassergeflügel) | Anas platyrhynchos u.a. | Fressen junge Triebe und Schwimmblätter; Teich mit Enten-Besatz ist kein geeigneter Seerosenstrandort | moderate | `incompatible_with` |

### 7.4 Teichökologische Faustregel

- Seerosenblätter sollten **30–50 % der Wasseroberfläche** bedecken — so wird ausreichend Algen hemmende Beschattung erzeugt ohne den Sauerstoffhaushalt durch fehlende Photosynthese zu gefährden
- Nährstoffkonkurrenz erwünscht: Seerosen und Wasserpflanzen entziehen dem Wasser gemeinsam Nitrat und Phosphat und reduzieren so den Algendruck
- Wasserwechsel (10–20 % monatlich) verbessert die Wasserqualität für alle Teichbewohner

---

## 8. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Besonderheit | Vorteil gegenüber N. alba |
|-----|-------------------|-------------|--------------------------|
| Zwerg-Seerose | Nymphaea tetragona | Sehr klein (Blätter 5–10 cm), ideal für Miniteich/Kübel | Balkon- und Terrassenteich geeignet (ab 20 L Wasservolumen), kein großer Teich nötig |
| Duftseerose | Nymphaea odorata | Stark duftende Blüten, nordamerikanisch, sehr winterhart (Zone 3) | Extremwinterhart, duftend, für kühlere Klimazonen |
| Teichrose | Nuphar lutea | Verwandt, einheimisch, extrem robust | Übersteht sehr flache und nährstoffreiche Gewässer, kein Pflanzkorb nötig |
| Lotosblume | Nelumbo nucifera | Nicht mit Nymphaea verwandt; emerse Blätter erheben sich hoch über Wasser | Spektakulärere Blüten, heilige Symbolik, Samen und Wurzel essbar; anspruchsvoller |
| Tropische Blaue Seerose | Nymphaea coerulea | Blaue Blütenfarbe, tropisch, für beheizte Teiche | Einzigartige Blütenfarbe (Blau); historisch/mythologisch bedeutsam (Ägypten) |
| Zwerg-Lotosblume | Nelumbo 'Momo Botan' | Kompakte Sorte, für mittelgroße Kübel | Kompromiss zwischen Lotosblume und Seerose für begrenzte Flächen |
| Victoria-Seerose | Victoria amazonica | Riesige Schwimmblätter bis 3 m Durchmesser | Spektakulärste Seerose der Welt; nur für große beheizbare Gewächshaus-Teiche |

---

## 9. Diagnosetabelle — Häufige Symptome und Sofortmaßnahmen

| Symptom | Ursache (wahrscheinlichste) | Sofortmaßnahme | Folgeschritt |
|---------|----------------------------|----------------|-------------|
| Keine Blüten trotz gesunder Blätter | Zu wenig Licht (min. 4 h Direktsonne nötig), oder Unterdüngung, oder zu tiefes Pflanzen | Standort auf Besonnung prüfen (ganztägig); Pflanzkorb auf korrekte Tiefe kontrollieren; Depot-Tab eindrücken | Standortwechsel oder Pflanzkorb tiefer/flacher stellen |
| Blätter sehr groß, aber wenige Blüten | Überdüngung oder Stickstoffüberschuss im Teich (z.B. durch Fischkot, Laubeintrag) | Düngung einstellen, Wasserqualität testen (Nitrat > 20 mg/L?) | Wasserwechsel 30 %, Nährstoffe reduzieren |
| Blätter gelb/braun mit Löchern (Fraßschäden) | Seerosenblattkäfer (Galerucella nymphaeae) | Betroffene Blätter entfernen; Larven und Eier von Blattunterseite abwischen | Regelmäßige Kontrolle alle 7 Tage; natürliche Fressfeinde fördern |
| Dichte schwarze Kolonien auf Blättern und Blüten | Seerosenblattlaus (Rhopalosiphum nymphaeae) | Blätter unter Wasser drücken (Läuse fallen ab, Fische fressen sie); stark befallene Blätter abschneiden | Wöchentliche Kontrolle, natürliche Gegenspieler fördern |
| Blätter von Larven zu Röhren zusammengerollt | Seerosenzünsler (Elophila nymphaeata) | Befallene Blätter mitsamt Larven entfernen und im Restmüll entsorgen | Gelbe Leimtafeln am Teichrand aufhängen |
| Braune, nasse Flecken auf Blättern, Pflanze riecht faulig | Rhizomfäule (bakteriell/pilzlich) | Pflanzkorb aus dem Teich holen; befaultes Rhizomgewebe großzügig herausschneiden; Schnittstellen mit Aktivkohle behandeln; frisch einpflanzen | Falls mehr als 50 % des Rhizoms befallen: Pflanze entsorgen, neues Rhizom kaufen |
| Weißlicher mehliger Belag auf Blattoberfläche | Echter Mehltau | Befallene Blätter entfernen; Standort auf Luftzirkulation prüfen | Keine chemische Behandlung möglich im Teich |
| Pflanze treibt im Frühjahr nicht aus | Rhizom erfroren (Teich zu flach) oder Rhizom verfault | Pflanzkorb aus dem Teich holen und Rhizom prüfen | Rhizom erfroren: neupflanzen; Teich vertiefern für nächsten Winter |
| Fadenalgen überdecken Blätter | Nährstoffüberschuss im Teichwasser (Phosphat/Nitrat), zu viel Licht, zu wenig Sauerstoffpflanzen | Fadenalgen sofort manuell mit Teichstab entfernen; Wasserqualität testen | Sauerstoffpflanzen einsetzen (Hornkraut, Elodea); Wasserwechsel 20–30 % |
| Teich riecht faulig, Wasser trüb-grün | Kippen der Wasserqualität (zu viel Nährstoffe, Sauerstoffmangel) | Belüftung einschalten; 30–40 % Wasserwechsel; verrottende Pflanzenteile entfernen | Besatz und Düngung überprüfen; ggf. Teichfilter nachrüsten |
| Blüten öffnen sich nicht oder schließen zu früh | Zu wenig Sonnenstunden, Wassertemperatur unter 18 °C (tropische Sorten) oder unter 16 °C (winterharte Sorten) | Standort prüfen; bei tropischen Sorten: frühestens bei dauerhaft 20 °C Wassertemperatur in den Außenteich setzen | Frühjahrspflanzung in flachere (wärmere) Zone |

---

## 10. CSV-Import-Daten (KA REQ-012 kompatibel)

### 10.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,frost_sensitivity,hardiness_detail,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,pruning_type,bloom_months,harvest_months
"Nymphaea alba","Weiße Seerose;White Water Lily;European White Waterlily","Nymphaeaceae","Nymphaea","perennial","long_day","herb","rhizomatous","4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b","hardy","Winterhart bis -25°C; Rhizom muss unter frostfreier Wasserschicht (min. 60 cm) überwintern",-0.2,"Europa; Nordafrika; gemäßigtes Asien","yes",20,60,30,200,100,"limited","yes","false","false","heavy_feeder","false","after_harvest","6;7;8;9","8;9;10"
```

### 10.2 Cultivar CSV-Zeilen (empfohlene Sorten)

```csv
name,parent_species,seed_type,traits,days_to_maturity,disease_resistances,notes
"Nymphaea alba (Wildform)","Nymphaea alba","open_pollinated","large_flowers;native;wildlife_friendly",730,"",,"Einheimische Wildart; für große Naturteiche ab 50 m² Wasserfläche; Blüten weiß mit gelben Staubblättern; Wassertiefe 50–300 cm"
"James Brydon","Nymphaea (Hybrid)","open_pollinated","double_flowers;shade_tolerant;fragrant;compact",365,"","Winterharte Hybridsorte; karminrote Doppelblüten; shade-tolerant (nur 2–3 h Sonne); für mittlere Teiche; USDA Zone 3–11; Wassertiefe 30–60 cm"
"Escarboucle","Nymphaea (Hybrid)","open_pollinated","large_flowers;free_flowering;fragrant",365,"","Winterharte Hybridsorte; kirschrote große Blüten; sehr blühfreudig über lange Saison; für mittelgroße bis große Teiche; Wassertiefe 40–80 cm"
"Marliacea Chromatella","Nymphaea (Hybrid)","open_pollinated","yellow_flowers;medium_pond",365,"","Winterharte Hybridsorte; gelbe Blüten; eine der ältesten Hybridsorte (Latour-Marliac 1877); bewährt und robust"
"Pygmaea Alba","Nymphaea (Pygmaea-Gruppe)","open_pollinated","miniature;container_suitable;balcony",180,"","Zwergseerose; weiße Miniaturblüten; ideal für Miniteich und Kübel (ab 20 L); Wassertiefe 15–30 cm; USDA Zone 4–11"
"Nymphaea capensis","Nymphaea capensis","open_pollinated","blue_flowers;tropical;day_blooming",120,"","Tropische Seerose; hellblaue Blüten; tagblühend; Wassertemperatur min. 20°C; in Deutschland nur Saisonkultur oder beheizter Winterteich"
"Nymphaea coerulea","Nymphaea coerulea","open_pollinated","blue_flowers;tropical;fragrant;historical",120,"","Tropische Blaue Seerose; historisch bedeutsam (altägyptisch); duftend; tagblühend; Winterquartier bei min. 18°C"
```

### 10.3 BotanicalFamily CSV-Zeile

```csv
name,common_name_de,common_name_en,order,typical_nutrient_demand,nitrogen_fixing,frost_tolerance,typical_growth_forms,rotation_category
"Nymphaeaceae","Seerosengewächse","Water Lily Family","Nymphaeales","heavy","false","MODERATE","herb","Aquatische Zierpflanzen"
```

---

## Quellenverzeichnis

1. [Wikipedia — Nymphaea alba](https://en.wikipedia.org/wiki/Nymphaea_alba) — Taxonomie, Verbreitung, Morphologie
2. [Wikipedia — Weiße Seerose (DE)](https://de.wikipedia.org/wiki/Wei%C3%9Fe_Seerose) — Deutschsprachige Artbeschreibung, Vermehrung
3. [PFAF Plant Database — Nymphaea alba](https://pfaf.org/user/plant.aspx?latinname=Nymphaea+alba) — Nutzbarkeit, Toxizität, Wuchsansprüche
4. [RHS — Nymphaea alba](https://www.rhs.org.uk/plants/11623/nymphaea-alba-(h)/details) — Kulturbedingungen, Hardiness
5. [Gartenteich-Ratgeber.com — Seerosen düngen](https://www.gartenteich-ratgeber.com/pflanzen/pflanzenpflege/seerosen/seerosen-duengen/) — Düngungsempfehlungen, Depot-Tabletten
6. [Gartenteich-Ratgeber.com — Seerosenblattlaus](https://www.gartenteich-ratgeber.com/pflanzen/pflanzenpflege/seerosen/seerosenblattlaus/) — Schädlingsbeschreibung
7. [Gartenteich-Ratgeber.com — Seerosen verjüngen](https://www.gartenteich-ratgeber.com/pflanzen/pflanzenpflege/seerosen/seerosen-verjuengen/) — Rhizomteilung
8. [Pflanzen-Kölle — Seerosenblattkäfer](https://www.pflanzen-koelle.de/ratgeber/pflanzendoktor/schaedlinge-und-krankheiten/seerosenblattkaefer/) — Schädlingsbeschreibung Galerucella nymphaeae
9. [Teichpflanzen-Teichbau.com — Seerosen Schädlinge](https://teichpflanzen-teichbau.com/seerosen-schaedlinge-und-ihre-bekaempfung) — Schädlinge und Bekämpfungsmethoden
10. [Seerosenfarm.de — Tropische Seerosen](http://seerosenfarm.de/tropische-seerosen-pflanzen-pflegen-ueberwintern-in-deutschland-seerosenfarm/) — Überwinterung tropischer Sorten
11. [Teichpflanzen-Teichbau.com — Seerosen überwintern](https://teichpflanzen-teichbau.com/seerosen-ueberwintern-tipps-fuer-teiche-und-kuebel) — Überwinterungsmethoden
12. [Gardenjournal.net — Seerose winterhart](https://www.gartenjournal.net/seerose-winterhart) — Winterhärte-Details
13. [Gardenia.net — Nymphaea James Brydon](https://www.gardenia.net/plant/nymphaea-james-brydon) — Sortenbeschreibung, USDA-Zonen
14. [NC State Extension — Nymphaea Hardy Water Lilies](https://plants.ces.ncsu.edu/plants/nymphaea-hardy-water-lilies/) — Kulturanleitung, Wassertiefe
15. [Gardenia.net — Nymphaea odorata](https://www.gardenia.net/plant/nymphaea-odorata) — Sortenbeschreibung, Winterhärte Zone 3
16. [Blauteich.de — Gartenteichkalender](https://www.blauteich.de/gartenteichkalender-teichpflege-das-ganze-jahr-ueber) — Jahrespflegekalender
17. [Gartenteich-Ratgeber.com — Seerosenteich anlegen](https://www.gartenteich-ratgeber.com/sonderformen/seerosenteich/) — Teichgemeinschaft, Begleitpflanzen
18. [H2O-Pflanze.de — Seerosensubstrat und Pflanzenkörbe](https://h2o-pflanze.de/seerosen/) — Substrat, Pflanzkorb, Produktempfehlungen
