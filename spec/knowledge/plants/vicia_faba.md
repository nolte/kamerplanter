# Ackerbohne — Vicia faba

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Royal Horticultural Society, USDA PLANTS Database, Bayerische LfL Körnerleguminosen, University of Warwick, FAO Faba Bean Crop Profile

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Vicia faba | `species.scientific_name` |
| Volksnamen (DE/EN) | Ackerbohne, Saubohne, Pferdebohne, Dicke Bohne; Fava Bean, Broad Bean, Field Bean | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Vicia | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr kältetolerant; Winterformen (Winterackerbohne) überstehen -12°C bis -15°C; Frühjahrs-Direktsaat ab Februar/März möglich; übersteht Spätfröste bis -8°C nach Keimung | `species.hardiness_detail` |
| Heimat | Naher Osten / Mittelmeer (Ursprung unklar; domestiziert ca. 6.000–8.000 v. Chr.) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**N-Fixierung:** Vicia faba fixiert in Symbiose mit *Rhizobium leguminosarum* bv. viciae 100–200 kg N/ha — höchste N-Fixierungsleistung unter den europäischen Körnerleguminosen. Impfung des Saatguts empfohlen bei Erstanbau. Ideal als Vorfrucht für Starkzehrer.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkultur möglich; aber Direktsaat bevorzugt da tiefe Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -35 bis -42 (Frühsaat ab Februar/März; sehr kältetolerant) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 2, 3, 4 (Frühjahr); 10, 11 (Winterackerbohne) | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (Frischbohne); 8, 9 (Trockenbohne) | `species.harvest_months` |
| Blütemonate | 4, 5, 6 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Rohe Bohnen (insb. bei Favismus-Risiko-Personen); reife grüne Bohnen roh wenig verträglich | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Vicin, Convicin (hämolytisch bei G6PD-Mangel / Favismus); Lektine; Trypsinhemmer (roh) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (WARNUNG: bei G6PD-Mangel / Favismus können rohe Bohnen lebensbedrohlich sein!) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Fabaceae-Pollen; mäßiges Allergen) | `species.allergen_info.pollen_allergen` |

**KRITISCHER SICHERHEITSHINWEIS — Favismus:** Menschen mit Glucose-6-Phosphat-Dehydrogenase-Mangel (G6PD-Mangel; ca. 8% der Weltbevölkerung; häufig mediterrane und afrikanische Abstammung) können nach Verzehr roher Ackerbohnen eine hämolytische Krise entwickeln. Völlig durchgegarte Bohnen sind in der Regel unbedenklich.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Herzaustreiben pinchen verhindert Blattlausbefall) | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (Pinchen der Triebspitzen bei Blattlausbefall) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 (tiefe Pfahlwurzel) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30–40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 50–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–20 cm in der Reihe; 45–60 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (hohe Sorten lagern bei Wind) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lehmige, nährstoffreiche Erde; pH 6,0–7,5; gut drainiert; tiefe Töpfe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | high |
| Sämling | 14–28 | 2 | false | false | high |
| Vegetativ | 28–56 | 3 | false | false | high |
| Blüte | 21–35 | 4 | false | false | low |
| Hülsenansatz | 14–28 | 5 | false | true | medium |
| Reife | 28–42 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.3–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–28 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtagpflanze) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 6–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 4–7 (gleichmäßige Feuchte kritisch für Hülsenansatz) | `requirement_profiles.irrigation_frequency_days` |

**Hinweis Bestäubung:** Ackerbohnen werden hauptsächlich von Hummeln bestäubt (Hummelgang — kurze Zunge Hummelarten nach Nektar). Blütenduft attraktiv für Wildinsekten.

#### Phase: Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.5 | — | — |
| Sämling | 0:1:1 | 0.4–0.8 | 6.0–7.5 | 60 | 25 |
| Vegetativ | 0:1:2 | 0.6–1.2 | 6.0–7.5 | 100 | 40 |
| Blüte | 0:2:2 | 0.8–1.4 | 6.0–7.5 | 100 | 50 |
| Reife | 0:1:1 | 0.4–0.8 | 6.0–7.5 | 60 | 25 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Biologisch/Organisch

| Produkt | Marke | Typ | Ausbringrate | Phasen |
|---------|-------|-----|-------------|--------|
| Rhizobium leguminosarum bv. viciae | diverse | Saatgutimpfung | 250 ml/25 kg Saatgut | Vor Saat |
| Kompost (reif) | eigen | organisch | 3–5 L/m² | Herbst/Frühjahr |
| Steinmehl | diverse | Bodenverbesserer | 100–200 g/m² | Grunddüngung |

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Superphosphat | diverse | mineralisch | 0-46-0 | 15–20 g/m² | Grunddüngung |
| Kaliumsulfat | diverse | mineralisch | 0-0-50 | 10–15 g/m² | Grunddüngung |

### 3.2 Besondere Hinweise zur Düngung

KEINE Stickstoffdüngung — hemmt Knöllchenbildung. Kalzium-Versorgung wichtig (keine sauren Böden; Kalkung bei pH < 6,0). Gute Phosphorversorgung fördert Knöllchenbildung. Ackerbohne hinterlässt bis zu 100 kg N/ha für Folgekulturen — beste N-Vorfrucht im Gemüsegarten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | — (kein Dünger nötig) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (Blattlaus-Monitoring wichtig) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Frühsaat | Direktsaat so früh wie möglich (Bodengare); 5 cm Tiefe | hoch |
| Apr | Blattlauskontrolle | Schwarze Bohnenblattlaus (Aphis fabae) ab April überwachen | hoch |
| Mai | Triebspitzen pinchen | Spitzen der Haupttriebe entfernen = Blattlausreduktion; fördert Hülsenansatz | mittel |
| Jun–Jul | Ernte Frischbohne | Hülsen schwellen; Körner noch grün und weich | hoch |
| Aug–Sep | Trockenernte | Hülsen schwarz; Körner hart; Pflanze abgestorben | mittel |
| Sep–Okt | Winterackerbohne-Saat | Herbstaussaat für überwinterte Frühjahrsernte | mittel |
| Okt–Nov | Einarbeitung | Wurzeln mit N-Knöllchen einarbeiten | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Schwarze Bohnenblattlaus | Aphis fabae | Dichte schwarze Kolonien; Honigtau; Triebverformung | Triebspitze | Blüte, Hülsenansatz |
| Sitona-Rüssler | Sitona lineatus | Halbrunde Fraßkerben an Blatträndern; Larven in Knöllchen | Blatt, Knöllchen | Sämling |
| Schokoladenfarbige Bohnenlaus | Therioaphis trifolii | Gelb-grüne Läuse; weniger massiv als A. fabae | Blatt | Vegetativ |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Schokoladenfleckenkrankheit | fungal (Botrytis fabae) | Schokoladenbraune Flecken; Hülsenfäule | kühl-feucht; dichte Bestände |
| Brennflecken | fungal (Colletotrichum truncatum) | Dunkle Läsionen; Stängelfäule | warm-feucht |
| Echte Mehltau | fungal (Erysiphe pisi) | Weißgrauer Belag | trocken-warm; Spätsommer |
| Bohnenmosaik | viral (BBMV, BYMV) | Mosaikflecken; Deformation | Blattlaus-Übertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) |
|----------|---------------|-------------------|
| Marienkäfer (Coccinella septempunctata) | Schwarze Bohnenblattlaus | 1–3 |
| Florfliegenlarven (Chrysoperla carnea) | Blattläuse | 5–10 |
| Schlupfwespe (Aphidius matricariae) | Blattläuse | 3–5 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Triebspitzen pinchen | cultural | — | Manuell bei Blütenansatz | 0 | Schwarze Bohnenblattlaus |
| Schmierseife | biological | Kaliumoleat | Sprühen 2–3% | 1 | Blattläuse |
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Rüssler |
| Pyrethrin | biological | Pyrethrine | Sprühen bei starkem Befall | 3 | Blattläuse |
| Weite Fruchtfolge | cultural | — | 3–4 Jahre Pause | 0 | Botrytis, Sklerotinia |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Toleranz gegen schwarze Bohnenblattlaus (sortenabhängig) | Schädling | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (liefert N für Folgekultur) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide (Winterweizen, Wintergerste); Mais |
| Empfohlene Nachfrucht | Starkzehrer (Kohl, Kürbis, Mais, Tomaten profitieren stark) |
| Anbaupause (Jahre) | 4–5 Jahre auf gleichem Standort (Botrytis, Sklerotinia) |

**Besonderheit Gemüsegarten:** Ackerbohne ist die *beste N-Vorfrucht* im europäischen Gartenbau. Ein guter Bestand kann 80–150 kg N/ha im Boden hinterlassen.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Hafer | Avena sativa | 0.9 | Klassisches Ackerbohnen-Hafer-Gemenge; Hafer stützt Bohne | `compatible_with` |
| Kartoffel | Solanum tuberosum | 0.7 | Ackerbohne schreckt Kartoffelkäfer ab (Anekdotisch) | `compatible_with` |
| Spinat | Spinacia oleracea | 0.8 | Bodenbeschattung durch Bohne; N-Profiteur | `compatible_with` |
| Sommer-Savory | Satureja hortensis | 0.8 | Abwehr schwarzer Bohnenblattlaus; traditionell | `compatible_with` |
| Tagetes | Tagetes spp. | 0.8 | Nematoden-Hemmung; Bestäuber-Anlockung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Knoblauch | Allium sativum | Hemmt Rhizobium-Knöllchenbildung | moderate | `incompatible_with` |
| Zwiebel | Allium cepa | Gleiche Wirkung auf Rhizobien | moderate | `incompatible_with` |
| Linse | Lens culinaris | Gleiche Familie; gleiche Pathogene; Konkurrenz | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Gleiche Familie; gleiche Krankheiten | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Fabaceae | `shares_pest_risk` | Botrytis, Sklerotinia, Sitona-Rüssler | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ackerbohne |
|-----|-------------------|-------------|------------------------------|
| Erbse | Pisum sativum | Fabaceae; Frühsaat | Höherer Frischkonsumwert; mehr Sorten |
| Sojabohne | Glycine max | Fabaceae; N-Fixierung | Wärmeliebend; höherer Proteingehalt |
| Linse | Lens culinaris | Fabaceae; kältetolerant | Kleiner; trockentoleranter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Vicia faba,"Ackerbohne;Saubohne;Pferdebohne;Dicke Bohne;Fava Bean;Broad Bean",Fabaceae,Vicia,annual,long_day,herb,taproot,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Naher Osten / Mittelmeer",limited,no,limited,false,true,nitrogen_fixer,true,half_hardy,"2;3;4;10;11","6;7;8;9","4;5;6"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Dreifach Weiße,Vicia faba,"spring_type;large_bean;fresh_consumption",75,open_pollinated
Witkiem Manita,Vicia faba,"spring_type;early;medium_plant",70,open_pollinated
Aquadulce Claudia,Vicia faba,"winter_type;overwintering;early_harvest",90,open_pollinated
```

---

## Quellenverzeichnis

1. [Royal Horticultural Society — Broad Beans](https://www.rhs.org.uk/vegetables/broad-beans/grow-your-own) — Gartenpraxis
2. [USDA PLANTS — Vicia faba](https://plants.usda.gov/plant-profile/VIFA) — Taxonomie
3. [Bayerische LfL — Körnerleguminosen](https://www.lfl.bayern.de/ipz/leguminosen) — Anbaupraxis Mitteleuropa
4. [FAO Faba Bean Crop Profile](https://www.fao.org) — Globale Anbausysteme
5. [Anbauleitfaden Körnerleguminosen KTBL](https://www.ktbl.de) — Agrarpraxis Deutschland
