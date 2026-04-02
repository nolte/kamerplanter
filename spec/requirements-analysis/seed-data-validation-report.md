# Seed-Daten Validierungsreport
**Erstellt von:** Seed-Data-Validator
**Datum:** 2026-04-02
**Zusammenarbeit mit:** agrobiology-requirements-reviewer (fuer [AGROBIO-CHECK] Findings)
**Analysierte Dateien:** 7 YAML-Dateien (Fokus-Scope: plant_info_indoor_4, plant_info_outdoor_3,
botanical_families, species, care_profiles_generated, ipm, plant_info_indoor_1)

---

## Zusammenfassung

| Kategorie | Datensaetze | Fehler | Warnungen | OK |
|-----------|-------------|--------|-----------|-----|
| **Schemas** | 7 geprueft | 5 | 4 | 3 |
| Species (neu) | 2 | 1 | 2 | 0 |
| Cultivars | 9 | 0 | 1 | 8 |
| Growth Phases | 9 Phasen | 2 | 1 | 6 |
| IPM Pests (neu) | 3 | 1 | 0 | 2 |
| IPM Diseases (neu) | 5 | 2 | 1 | 2 |
| IPM Treatments (neu) | 6 | 1 | 0 | 5 |
| IPM Treatment-Edges | 20 neu | 10 | 0 | 10 |
| Botanical Families (neu) | 1 | 0 | 0 | 1 |
| Care Profiles (neu) | 2 | 0 | 1 | 1 |
| **Gesamt** | **64** | **22** | **10** | **38** |

### Kritische Findings auf einen Blick

1. **S-001 (KRITISCH):** 10 Pest-Treatment-Edges in `ipm.yaml` sind in der falschen Sektion
   (`disease_treatments` statt `pest_treatments`) -- diese Edges werden beim Seeding NICHT erstellt.
2. **S-002 (KRITISCH):** `Disease.scientific_name` hat `min_length=1` im Pydantic-Model,
   aber 2 Eintraege in `ipm.yaml` setzen `scientific_name: null` -- Pydantic-Validation schlaegt fehl.
3. **S-003:** Phase-Namen `active_growth` und `winter_rest` sind nicht im Schema-Enum und nicht
   im `PhaseName` Python-Enum -- obwohl das Pydantic-Model `str` akzeptiert.
4. **SCH-001:** `lifecycle_configs` ist ein genutzter Top-Level-Key in allen plant_info-Dateien,
   fehlt aber komplett im `plant_info.schema.yaml` (und `additionalProperties: false` ist gesetzt).
5. **SCH-002:** `species_enrichment` (dict-Format) ist der tatsaechlich genutzte Key,
   aber das Schema definiert `enrich_species` (Array-Format) -- fundamentale Namensdiskrepanz.

---

## Schema-Findings (Phase 0)

### Schema-Abdeckung

| YAML-Datei | Schema vorhanden | Schema-Ref in YAML | Fehlende Top-Level-Keys | Status |
|------------|-----------------|-------------------|-------------------------|--------|
| `plant_info_indoor_4.yaml` | plant_info.schema.yaml | ✅ | `lifecycle_configs` | ⚠️ |
| `plant_info_outdoor_3.yaml` | plant_info.schema.yaml | ✅ | `lifecycle_configs` | ⚠️ |
| `botanical_families.yaml` | botanical_families.schema.yaml | ✅ | -- | ✅ |
| `species.yaml` | species.schema.yaml | ✅ | -- | ✅ |
| `ipm.yaml` | ipm.schema.yaml | ✅ | -- | ✅ |
| `plant_info_indoor_1.yaml` | plant_info.schema.yaml | ✅ | `lifecycle_configs` | ⚠️ |
| `care_profiles_generated.yaml` | **KEIN SCHEMA** | ❌ | -- | ❌ |

### Schema-Aenderungen (SCH-XXX)

#### SCH-001: `lifecycle_configs` fehlt im plant_info.schema.yaml
**Schema:** `schemas/plant_info.schema.yaml`
**Aenderungstyp:** Top-Level-Feld fehlt
**Details:** Alle plant_info-Dateien (`plant_info_indoor_1/2/3/4`, `plant_info_outdoor_1/2/3`)
verwenden `lifecycle_configs` als Dictionary (species_name -> lifecycle-objekt). Das Schema
hat `additionalProperties: false` gesetzt, kennt aber diesen Key nicht. IDE-Validierung
schlaegt bei diesen Dateien komplett fehl.
**Empfehlung:** `lifecycle_configs` als `type: object` mit `additionalProperties: <lifecycle_schema>`
in das Schema aufnehmen.

#### SCH-002: `species_enrichment` vs. `enrich_species` -- Namensdiskrepanz
**Schema:** `schemas/plant_info.schema.yaml`
**Aenderungstyp:** Falscher Key-Name im Schema
**Details:** Das Schema definiert `enrich_species` als Array von Objekten mit `species_name`-Feld.
Der tatsaechlich genutzte Key in allen Dateien ist `species_enrichment` als Dictionary
(species_name -> patch-Felder). Der Seed-Loader `seed_plant_info_extended.py` liest
`species_enrichment` (Zeile 244). Der Schema-Key `enrich_species` wird in keiner YAML-Datei
verwendet.
**Fix:** Schema-Key umbenennen zu `species_enrichment` und Format auf Dictionary anpassen.

#### SCH-003: Phase-Namen `active_growth` und `winter_rest` nicht im Schema-Enum
**Schema:** `schemas/plant_info.schema.yaml` und `schemas/_defs.schema.yaml`
**Aenderungstyp:** Fehlende Enum-Werte
**Details:** Die `phase_name`-Enum-Liste in `_defs.schema.yaml` enthaelt:
`[germination, seedling, vegetative, flowering, flushing, dormancy, harvest, sprouting,
budding, fruiting, ripening, senescence, corm_ripening]`.
Tatsaechlich verwendete Werte in plant_info_indoor_1.yaml und plant_info_indoor_4.yaml:
`active_growth` (26x), `winter_rest` (21x), `cool_rest` (3x), `summer_rest` (1x).
Das Pydantic-Model `GrowthPhase.name` ist als `str` typisiert und akzeptiert beliebige
Werte -- die Enum-Einschraenkung existiert nur im Schema.
**Empfehlung:** Entweder Enum im Schema um `active_growth`, `winter_rest`, `cool_rest`,
`summer_rest` erweitern -- oder GrowthPhase.name im Pydantic-Model auf `PhaseName` einschraenken
(bricht dann aber alle bestehenden Daten).

#### SCH-004: `protist` fehlt im ipm.schema.yaml pathogen_type Enum
**Schema:** `schemas/ipm.schema.yaml`
**Aenderungstyp:** Fehlender Enum-Wert
**Details:** `PathogenType.PROTIST = "protist"` ist in `enums.py` (Zeile 342) definiert.
`ipm.yaml` Zeile 332 nutzt `pathogen_type: protist` fuer Clubroot.
Das `ipm.schema.yaml` definiert `enum: [fungal, bacterial, viral, physiological, oomycete]` --
`protist` fehlt.
**Fix:** `protist` zum pathogen_type-Enum im ipm.schema.yaml hinzufuegen.

#### SCH-005: `care_profiles_generated.yaml` hat kein Schema
**Aenderungstyp:** Schema fehlt komplett
**Details:** Die Datei hat weder einen `# yaml-language-server`-Kommentar noch eine
entsprechende `schemas/care_profiles.schema.yaml`. Es existiert kein Loader, der diese
Datei verarbeitet (keine Referenz in keiner `seed_*.py` Datei). Die Datei ist daher
funktional ein Referenzdokument -- falls sie aktiv geseeded werden soll, muss sowohl
ein Schema als auch ein Loader erstellt werden.
**Status:** `[SCHEMA-MISSING]`

#### SCH-006: `cultivars` und `growth_phases` -- Schema-Format vs. tatsaechliches Format
**Schema:** `schemas/plant_info.schema.yaml`
**Details:** Das Schema definiert `cultivars` als `type: array` von Objekten mit
`species_name`-Feld. Alle Dateien verwenden Dictionary-Format
`species_name -> list[cultivar_dict]`. Gleiches gilt fuer `growth_phases`.
Der Loader `seed_plant_info_extended.py` erwartet Dict-Format (Zeile 247).
Schema und Loader sind inkompatibel -- das Schema beschreibt eine andere Struktur
als tatsaechlich verwendet wird.
**Empfehlung:** Schema-Format auf Dictionary anpassen (mit `patternProperties` oder
`additionalProperties`).

#### SCH-007: ipm.schema.yaml -- Disease-Felder stimmen nicht mit ipm.yaml ueberein
**Schema:** `schemas/ipm.schema.yaml`
**Details:** Das Schema definiert fuer diseases: `name`, `pathogen_type`, `symptoms`,
`affected_parts`. `ipm.yaml` verwendet stattdessen: `scientific_name`, `common_name`,
`pathogen_type`, `incubation_period_days`, `environmental_triggers`, `affected_plant_parts`.
Keines der tatsaechlich genutzten Felder (`common_name`, `incubation_period_days`,
`environmental_triggers`, `affected_plant_parts`) ist im Schema definiert.
Dies ist eine pre-existierende Diskrepanz, nicht durch neue Daten verursacht.

### Schema-Enum-Synchronisation

| Enum | _defs.schema.yaml | Python enums.py | Abweichung |
|------|-------------------|-----------------|------------|
| `phase_name` | 13 Werte | `PhaseName` 7 Werte | Schema hat mehr als Python; beide fehlen `active_growth`, `winter_rest` |
| `pathogen_type` | 5 Werte (fehlt `protist`) | `PathogenType` 6 Werte | ⚠️ protist fehlt im Schema |
| `growth_habit` | 5 Werte | -- | ✅ |
| `root_type` | 5 Werte | -- | ✅ |
| `frost_tolerance` | 4 Werte | -- | ✅ |

---

## Fehler -- Sofortiger Korrekturbedarf

### S-001: Pest-Treatment-Edges in falscher Sektion (KRITISCH)
**Datei:** `src/backend/app/migrations/seed_data/ipm.yaml`
**Bereich:** Zeilen 1076-1087 (innerhalb der `disease_treatments`-Sektion)
**Problem:** 10 Pest-Treatment-Edges sind in der `disease_treatments`-Sektion eingetragen.
Der Loader `seed_data.py` (Zeile 397-406) liest `disease_treatments` und versucht,
den zweiten Eintrag als Disease-Name in `disease_key_map` nachzuschlagen. Da
`Mealybug`, `Scale Insects`, `Fungus Gnats`, `Water Lily Aphid`, `Water Lily Leaf Beetle`
und `Brown China-mark Moth` Schaedlinge sind (nicht in `disease_key_map`), wird `d_key`
als leerer String aufgeloest -- die Edge-Erstellung wird uebersprungen.
Alle 10 Edges werden beim Seeding nicht erstellt.

Betroffene Edges (muessen in `pest_treatments` verschoben werden):
```yaml
  - [Rubbing Alcohol Swab (70%), Mealybug]
  - [Rubbing Alcohol Swab (70%), Scale Insects]
  - [Bacillus thuringiensis israelensis (Bti), Fungus Gnats]
  - [Diatomaceous Earth, Fungus Gnats]
  - [Submerge Leaves (Aphid Removal), Water Lily Aphid]
  - [Remove Infested Leaves (Aquatic), Water Lily Aphid]
  - [Remove Infested Leaves (Aquatic), Water Lily Leaf Beetle]
  - [Remove Infested Leaves (Aquatic), Brown China-mark Moth]
  - [Yellow Sticky Traps (Pond Edge), Water Lily Aphid]
  - [Yellow Sticky Traps (Pond Edge), Water Lily Leaf Beetle]
```
**Fix:** Diese 10 Eintraege vom Ende der `disease_treatments`-Sektion in die
`pest_treatments`-Sektion verschieben.

---

### S-002: `scientific_name: null` verletzt Pydantic-Validation (KRITISCH)
**Datei:** `src/backend/app/migrations/seed_data/ipm.yaml`
**Betroffene Zeilen:** 493 (`Fluoride Tip Burn`), 509 (`Rhizome Rot (Water Lily)`)
**Problem:** Das Pydantic-Model `Disease` (Zeile 35 in `ipm.py`) definiert:
```python
scientific_name: str = Field(min_length=1, max_length=200)
```
`ipm.yaml` setzt `scientific_name: null` fuer zwei Krankheiten ohne bekannten
Wissenschaftsnamen. `Disease.model_validate(disease_data)` wirft bei diesen Eintraegen
einen `ValidationError`, da `None` die `min_length=1`-Constraint verletzt.
Der Seed-Loader `seed_data.py` (Zeile 359) schlaegt bei diesen Krankheiten fehl.

Zusaetzliches Problem: Die Loader-Logik (Zeile 355) mappt `existing_disease_map` auf
`scientific_name` -- zwei `null`-Werte wuerden beide auf denselben Key `None` mappen,
was Upsert-Konflikte verursacht.

**Fix (Option A -- empfohlen):** `scientific_name` im Disease-Modell optional machen:
```python
scientific_name: str | None = Field(default=None, max_length=200)
```
Und Deduplication in `seed_data.py` auf `common_name` umstellen wenn `scientific_name` null.

**Fix (Option B):** Platzhalter-Werte verwenden:
```yaml
# Zeile 493:
scientific_name: "physiological_fluoride_tip_burn"
# Zeile 509:
scientific_name: "bacterial_rhizome_rot_water_lily"
```

---

### S-003: Phase-Namen `active_growth`, `winter_rest` nicht in Enums
**Dateien:** `plant_info_indoor_1.yaml` (26x + 21x), `plant_info_indoor_4.yaml` (1x)
**Problem:** Schema-Validation schlaegt fehl, da diese Namen nicht im `phase_name`-Enum
stehen (`additionalProperties: false` auf Phase-Ebene). In der Praxis kein Runtime-Fehler
(Pydantic-Model hat `str`), aber das Schema ist nicht konform mit den tatsaechlichen Daten.
**Fix:** Enum in `_defs.schema.yaml` und `plant_info.schema.yaml` um
`active_growth`, `winter_rest`, `cool_rest`, `summer_rest` erweitern.

---

### S-004: `new_species.common_names` -- Semikolon-String statt Array
**Datei:** `plant_info_indoor_4.yaml` (Zeile 24) und `plant_info_outdoor_3.yaml` (Zeile 48)
**Problem:** Das Schema in `plant_info.schema.yaml` definiert `common_names` als
`type: array, minItems: 1`. Beide Dateien verwenden Semikolon-getrennten String:
```yaml
common_names: "Duftdracaena;Maispalme;Corn Plant;Mass Cane;Happy Plant"
```
Der Loader verarbeitet beides korrekt via `_to_list()`. Schema-Validation schlaegt aber fehl.
**Fix:** Array-Format verwenden (wie in `species.yaml`):
```yaml
common_names: [Duftdracaena, Maispalme, Corn Plant, Mass Cane, Happy Plant]
```

---

### S-005: `new_species.hardiness_zones` -- Semikolon-String statt Array
**Datei:** `plant_info_indoor_4.yaml` (Zeile 28) und `plant_info_outdoor_3.yaml` (Zeile 52)
**Problem:** Das Schema erwartet `type: array` mit Zonen-Pattern pro Item.
Beide Dateien verwenden Semikolon-String:
```yaml
hardiness_zones: "10b;11a;11b;12a;12b"
```
Loader-kompatibel (`_to_list()`), aber Schema-inkonform.
**Fix:** Array-Format verwenden:
```yaml
hardiness_zones: ["10b", "11a", "11b", "12a", "12b"]
```
Hinweis: Im gleichen File (`plant_info_indoor_4.yaml`) nutzt die `species_enrichment`-Sektion
fuer D. marginata bereits korrekt Array-Format (Zeile 54).

---

### S-006: `companion_planting.compatible` -- Objekt-Format statt Array-Format
**Datei:** `plant_info_indoor_4.yaml` (Zeilen 310-344)
**Problem:** Das Schema (`plant_info.schema.yaml` Zeile 302-314) definiert `compatible`
als Array von Arrays: `[species_a, species_b, score]`.
`plant_info_indoor_4.yaml` verwendet Objekt-Format:
```yaml
- species_a: "Dracaena marginata"
  species_b: "Epipremnum aureum"
  score: 0.9
```
Der Loader (`seed_plant_info_extended.py` Zeile 248) liest `edge["species_a"]` --
erwartet also Objekt-Format. Das Format des Loaders und der YAML-Datei stimmen ueberein,
aber das Schema beschreibt das Array-Format (wie in `companion_planting.yaml` verwendet).
**Status:** Loader-kompatibel, aber Schema-inkonform. Das Objekt-Format ist fuer
Editierbarkeit vorzuziehen -- Schema sollte aktualisiert werden.

---

## Warnungen -- Sollten behoben werden

### V-001: `new_diseases` / `new_treatments` in plant_info-Dateien werden vom Loader ignoriert
**Dateien:** `plant_info_indoor_4.yaml`, `plant_info_outdoor_3.yaml`
**Problem:** Beide Dateien definieren `new_diseases` und `new_treatments` als Top-Level-Keys.
Kein Seed-Loader liest diese Keys. Die tatsaechlichen IPM-Daten muessen direkt in
`ipm.yaml` eingetragen werden (was hier korrekt gemacht wurde). Die `new_diseases`/
`new_treatments`-Sektionen in den plant_info-Dateien sind redundant.
**Empfehlung:** Diese Sektionen entweder loeschen oder als Kommentar `# Referenz nur` markieren.

---

### V-002: `pest_species_edges` / `disease_species_edges` werden vom Loader ignoriert
**Dateien:** `plant_info_indoor_4.yaml` (S11-S14), `plant_info_outdoor_3.yaml` (S11-S14)
**Problem:** Kein Loader verarbeitet `pest_species_edges`, `disease_species_edges`,
`treatment_pest_edges`, `treatment_disease_edges` aus plant_info-Dateien.
Diese Edges muessten fuer tatsaechliche Wirkung in `ipm.yaml` (als `pest_treatments`
bzw. `disease_treatments`) eingetragen werden.
**Status:** Als Dokumentation nutzbar, aber kein Laufzeit-Effekt.

---

### V-003: `care_profiles_generated.yaml` hat keinen Loader
**Datei:** `care_profiles_generated.yaml`
**Problem:** Keine `seed_*.py`-Datei referenziert `care_profiles_generated.yaml`.
Die Care-Profile fuer `Dracaena fragrans` und `Nymphaea alba` werden nicht geseeded.
**Empfehlung:** Pruefen, ob `seed_plant_info_extended.py` um `care_profiles`-Loading
erweitert werden soll.

---

### V-004: Range-String-Format-Inkonsistenz
**Dateien:** `plant_info_indoor_4.yaml`, `plant_info_outdoor_3.yaml` vs. `species.yaml`
**Problem:** `plant_info`-Dateien nutzen Einzel-Bindestrich `"10-30"` waehrend
`species.yaml` Doppel-Bindestrich `"10--30"` nutzt (entsprechend dem Schema-Beispiel).
Das `range_string`-Pattern `[-–—]+` erlaubt beides. Die Felder `recommended_container_volume_l`,
`mature_height_cm`, `mature_width_cm` sind betroffen.
**Empfehlung:** Konvention vereinheitlichen auf Doppel-Bindestrich (wie species.yaml).

---

### V-005: `Nymphaea alba` -- `allows_harvest: false` widerspricht `harvest_months`
**Datei:** `plant_info_outdoor_3.yaml` und `species.yaml`
**Problem:** `Nymphaea alba` hat:
- `harvest_months: [8, 9, 10]` (definiert)
- `allows_harvest: false` (species-Ebene in plant_info_outdoor_3.yaml)
- `allows_harvest: true` (flowering-Phase, Zeile ca. 182)
Drei widerspruchliche Eintraege. `harvest_months` impliziert, dass Ernte moeglich ist
(vermutlich Rhizom oder Samen), aber `allows_harvest: false` sperrt die Ernte-Funktion.
**Empfehlung:** `[AGROBIO-CHECK]` -- Klaeren ob Nymphaea alba fuer den Anwendungsfall
`allows_harvest: false` richtig ist. Falls ja: `harvest_months` entfernen und Phase-Level
`allows_harvest: true` auf `false` aendern.

---

## Fachliche Pruefung [AGROBIO-CHECK]

### P-001: Dracaena fragrans -- dormancy_required: true korrekt?
**Datei:** `plant_info_indoor_4.yaml` (lifecycle_configs)
**Fraglicher Wert:** `dormancy_required: true` fuer `Dracaena fragrans`
**Kontext:** D. fragrans stammt aus tropischem Afrika und ist ein immergruener
Baum. Eine echte Dormanzphase ist botanisch fraglich. Was es gibt: eine Wachstums-
reduktion im Winter bei kuerzeren Tagen und niedrigerer Temperatur in Innenraeumen
(pseudo-Dormanz). In `plant_info_indoor_1.yaml` hat auch `Dracaena marginata`
`dormancy_required: true`.
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer

---

### P-002: Dracaena fragrans -- dormancy-Phase VPD 1.1 kPa hoeher als Active Growth (0.9 kPa)
**Datei:** `plant_info_indoor_4.yaml`
**Fraglicher Wert:** `vpd_target_kpa: 1.1` in der `dormancy`-Phase
**Kontext:** Hoehere VPD im Winter koennte durch niedrigere Luftfeuchtigkeit (Heizungsluft)
erklaert werden. Aber hoehere VPD bei reduziertem Wachstum erhoht Transpirations-Stress.
D. marginata hat in beiden Phasen VPD 0.8 kPa (plant_info_indoor_1.yaml).
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer

---

### P-003: Nymphaea alba -- PPFD 1400 µmol/m²/s in der Bluete-Phase
**Datei:** `plant_info_outdoor_3.yaml`
**Fraglicher Wert:** `light_ppfd_target: 1400` in der `flowering`-Phase
**Kontext:** 1400 µmol/m²/s entspricht direktem Sonnenlicht (Hochsommer-Tagesmitte).
Nymphaea alba ist eine Vollsonnenpflanze -- dieser Wert koennte korrekt sein.
Plausibler Bereich fuer Sonnenpflanzen: 1000-2000 µmol/m²/s.
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer

---

### P-004: Nymphaea alba -- senescence `is_terminal: true` fuer eine Perenne
**Datei:** `plant_info_outdoor_3.yaml`
**Fraglicher Wert:** `is_terminal: true` in der `senescence`-Phase
**Kontext:** `is_terminal: true` signalisiert dem System, dass die Pflanze danach
nicht weiter existiert. Bei einer Perenne mit jaehrlichem Zyklus ist das nicht korrekt.
Nach Senescence folgt Dormanz (Winterruhephase).
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer
**Empfehlung:** Wenn `is_terminal` "Ende des Jahres-Zyklus" bedeutet: OK.
Wenn es "Tod der Pflanze" bedeutet: auf `false` aendern.

---

### P-005: Nymphaea alba -- harvest_months [8,9,10] ohne klaren Erntegegenstand
**Datei:** `plant_info_outdoor_3.yaml` / `species.yaml`
**Kontext:** `harvest_months: [8, 9, 10]` -- was wird geerntet?
Nymphaea alba Rhizome koennen im Herbst (Sep-Okt) geteilt werden; Samen reifen Aug-Okt.
Fuer reinen Zierpflanzen-Kontext waere `harvest_months` gar nicht relevant.
(Kombiniert mit V-005.)
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer

---

### P-006: Dracaena marginata -- bloom_months [5, 6] plausibel?
**Datei:** `plant_info_indoor_4.yaml` (species_enrichment fuer D. marginata)
**Fraglicher Wert:** `bloom_months: [5, 6]` fuer `Dracaena marginata`
**Kontext:** D. marginata blueht in Innenraeumen extrem selten (nur bei optimalen
Bedingungen nach vielen Jahren). Mai-Juni waere fuer Zimmerkultur ungewoehnlich.
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer

---

### P-007: Fusarium Leaf Spot (Dracaena) -- Erreger Fusarium moniliforme korrekt?
**Datei:** `ipm.yaml` (Zeile 479)
**Fraglicher Wert:** `scientific_name: Fusarium moniliforme`
**Kontext:** Der aktuelle wissenschaftliche Name ist *Fusarium verticillioides* (seit 1999).
*F. moniliforme* ist ein Synonym. Fuer Dracaena-Blattflecken ist *Fusarium solani* oder
*F. oxysporum* typischer als *F. moniliforme/verticillioides*, der hauptsaechlich Mais befaellt.
**Status:** ⏳ Awaiting agrobiology-requirements-reviewer

---

## Referenzielle Integritaet

### Verwaiste Referenzen

| Quelle | Referenz | Existiert | Bemerkung |
|--------|----------|-----------|-----------|
| `plant_info_indoor_4.yaml` companion_planting | `Nephrolepis exaltata` | Zu pruefen | Muss in species-Daten existieren |
| `plant_info_indoor_4.yaml` companion_planting | `Phalaenopsis spp.` | Fraglich | `spp.` als Wildcard -- kein exakter Species-Key |
| `plant_info_indoor_4.yaml` disease_species_edge | `Root Rot` | ✅ in ipm.yaml | Edge wird aber nicht geladen |
| `plant_info_outdoor_3.yaml` disease_species_edge | `Botrytis (Grey Mold)` | ✅ in ipm.yaml | Edge wird aber nicht geladen |
| `plant_info_outdoor_3.yaml` disease_species_edge | `Powdery Mildew` | ✅ in ipm.yaml | Edge wird aber nicht geladen |

**Hinweis zu `Phalaenopsis spp.`:** Das Format `spp.` ist eine taxonomische Abkuerzung.
In den Species-Daten gibt es moeglicherweise keinen Eintrag mit exakt diesem scientific_name.
Da `companion_planting`-Edges per species_name lookup aufgeloest werden (und bei Nicht-Treffer
uebersprungen werden), ist dies ein stilles Failure ohne Fehlermeldung.

### Bidirektionalitaet Companion Planting (plant_info_indoor_4.yaml)

Alle 15 definierten Kanten sind einseitig (keine Gegenkante definiert).
Wenn der Empfehlungs-Engine bidirektionale Edges erwartet (wie in `companion_planting.yaml`
wo jedes kompatible Paar als zwei Eintraege definiert wird), werden Empfehlungen
nur in eine Richtung funktionieren.

Betroffene Kanten-Paare (alle in `compatible` und `incompatible`):
Dracaena marginata, Dracaena fragrans je gegen Epipremnum aureum, Spathiphyllum wallisii,
Philodendron hederaceum, Dracaena trifasciata, Chlorophytum comosum, Nephrolepis exaltata,
Phalaenopsis spp. sowie D. marginata <-> D. fragrans.

---

## Konsistenz-Pruefung species.yaml vs. plant_info-Dateien

### Dracaena fragrans

| Feld | species.yaml | plant_info_indoor_4.yaml | Status |
|------|-------------|--------------------------|--------|
| `native_habitat` | "Tropical Africa" | "Tropical Africa (Sudan, Mozambique, Angola)" | ⚠️ Detailgrad unterschiedlich |
| `hardiness_detail` | "...Tropical origin." | "...Tropical origin Sudan-Angola." | ⚠️ Leicht unterschiedlich |
| `recommended_container_volume_l` | "10--30" | "10-30" | ⚠️ Format-Inkonsistenz |
| `mature_height_cm` | "150--300" | "150-300" | ⚠️ Format-Inkonsistenz |
| `bloom_months` | [5, 6] | [5, 6] | ✅ |
| `hardiness_zones` | Array-Format | Semikolon-String | ⚠️ Format-Inkonsistenz |

Loader-Verhalten: plant_info-Daten ueberschreiben species.yaml beim Seeding.

### Nymphaea alba

| Feld | species.yaml | plant_info_outdoor_3.yaml | Status |
|------|-------------|---------------------------|--------|
| `pruning` | Fehlt | Vorhanden | ⚠️ In species.yaml nicht definiert (wird beim Seeding ergaenzt) |
| `recommended_container_volume_l` | "20--40" | "20-40" | ⚠️ Format-Inkonsistenz |
| `mature_height_cm` | "10--30" | "10-30" | ⚠️ Format-Inkonsistenz |
| `allows_harvest` | Fehlt | false | -- |
| `bloom_months` | [6, 7, 8, 9] | [6, 7, 8, 9] | ✅ |

---

## Positiv-Befunde

1. **Nymphaeaceae-Familie korrekt angelegt:** Alle Pflichtfelder vorhanden, fachlich korrekt
   (Nymphaeales, aquatisch, insektenbestaubt, ornamental).

2. **Aquatische Besonderheiten bedacht:** `irrigation_frequency_days: 0.0` und
   `vpd_target_kpa: 0.0` fuer alle Nymphaea-Phasen -- korrekte Behandlung einer Wasserpflanze.

3. **Care-Profile fachlich solide:** Beide neuen Care-Profile haben korrekte Notizen
   (Fluorid-Sensitivitaet D. fragrans, Depoduenger fuer Nymphaea, watering_interval 0 fuer
   Teichpflanze).

4. **IPM-Daten vollstaendig in ipm.yaml:** Neue Schaedlinge (`Rhopalosiphum nymphaeae`,
   `Galerucella nymphaeae`, `Elophila nymphaeata`) und Krankheiten sind mit wissenschaftlichen
   Namen und allen Pflichtfeldern eingetragen.

5. **Dracaena fragrans Wachstumsphasen konsistent:** Phasen-Sequenz seedling -> vegetative ->
   active_growth -> dormancy bildet den typischen Jahresrhythmus ab.

6. **Nymphaea Jahres-Zyklus vollstaendig:** dormancy -> sprouting -> vegetative -> flowering ->
   senescence ist der korrekte jaehrliche Rhythmus einer Seerose.

7. **Cultivar-Daten korrekt:** Die 4 D. fragrans Cultivars (Massangeana, Janet Craig,
   Lemon Lime, Warneckii) und 5 Nymphaea-Cultivars sind die gaengigsten Handelssorten.

8. **Schema-Referenz-Kommentare vorhanden:** Alle neuen plant_info-Dateien haben
   `# yaml-language-server: $schema=./schemas/plant_info.schema.yaml`.

---

## Duplikate

Keine echten Duplikate gefunden. Die `new_treatments`-Sektionen in plant_info-Dateien
definieren konzeptionell dieselben Behandlungen wie ipm.yaml, werden aber vom Loader
nicht verarbeitet und erzeugen daher keine Laufzeit-Duplikate.

---

## Priorisierte Aktionsliste

| Prioritaet | Finding | Datei(en) | Aufwand |
|-----------|---------|-----------|---------|
| KRITISCH | S-001: 10 Pest-Treatment-Edges in falscher Sektion | `ipm.yaml` | 5 min |
| KRITISCH | S-002: `scientific_name: null` verletzt Pydantic | `ipm.yaml` + `ipm.py` | 30 min |
| HOCH | SCH-001: `lifecycle_configs` im Schema fehlt | `plant_info.schema.yaml` | 20 min |
| HOCH | SCH-002: `species_enrichment` vs `enrich_species` | `plant_info.schema.yaml` | 15 min |
| HOCH | SCH-003/S-003: Phase-Enums erweitern | `_defs.schema.yaml` | 10 min |
| HOCH | SCH-004: `protist` im ipm-Schema fehlt | `ipm.schema.yaml` | 5 min |
| MITTEL | S-004/S-005: Array-Format statt Semikolon-String | `plant_info_indoor_4.yaml`, `plant_info_outdoor_3.yaml` | 10 min |
| MITTEL | S-006/SCH-006: companion_planting Schema-Format | `plant_info.schema.yaml` | 15 min |
| MITTEL | Bidirektionale Companion-Edges ergaenzen | `plant_info_indoor_4.yaml` | 20 min |
| NIEDRIG | SCH-005/V-003: Care-Profiles Schema + Loader | `schemas/`, `seed_plant_info_extended.py` | 60 min |
| NIEDRIG | V-004: Range-String-Format vereinheitlichen | `plant_info_indoor_4.yaml`, `plant_info_outdoor_3.yaml` | 5 min |
| NIEDRIG | V-001/V-002: Redundante Sektionen bereinigen oder dokumentieren | `plant_info_indoor_4.yaml`, `plant_info_outdoor_3.yaml` | 10 min |
| AGROBIO | P-001 bis P-007 klaeren | agrobiology-requirements-reviewer | -- |

---

## Empfehlungen fuer agrobiology-requirements-reviewer

Die folgenden [AGROBIO-CHECK] Findings sollten durch den Agrarbiologie-Experten verifiziert werden:

1. **P-001:** Ist `dormancy_required: true` fuer `Dracaena fragrans` botanisch korrekt?
2. **P-002:** Ist VPD-Ziel 1.1 kPa in der Dormanz-Phase fuer D. fragrans sinnvoll?
3. **P-003:** Ist PPFD 1400 µmol/m²/s fuer Nymphaea alba in der Bluete korrekt?
4. **P-004:** `is_terminal: true` in der Senescence-Phase von Nymphaea alba -- Bedeutung klaeren.
5. **P-005/V-005:** Soll `Nymphaea alba` harvest-faehig sein (harvest_months, allows_harvest)?
6. **P-006:** Sind `bloom_months: [5, 6]` fuer `Dracaena marginata` als Indoor-Pflanze korrekt?
7. **P-007:** Ist `Fusarium moniliforme` der korrekte Erreger fuer Dracaena-Blattflecken?

Empfohlener Pruefauftrag an den agrobiology-requirements-reviewer:
> Bitte pruefe die im Seed-Data-Validation-Report markierten [AGROBIO-CHECK] Findings
> (P-001 bis P-007) auf botanische Korrektheit. Der Report liegt unter
> `spec/requirements-analysis/seed-data-validation-report.md`.
