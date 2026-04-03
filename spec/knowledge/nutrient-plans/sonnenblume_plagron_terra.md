# Naehrstoffplan: Sonnenblume -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Helianthus annuus (einjaerig, Starkzehrer, Freiland outdoor)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal, Green Sensation
> **Erstellt:** 2026-03-01
> **Quellen:** spec/ref/products/plagron_terra_*.md, spec/ref/products/plagron_power_roots.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_sugar_royal.md, spec/ref/products/plagron_green_sensation.md, spec/ref/plant-info/helianthus_annuus.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Sonnenblume -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Sonnenblumen (Helianthus annuus) im Freiland. Plagron Terra-Linie mit 6 Produkten (inkl. Green Sensation als PK-Booster). Einjaerige Kultur: Direktsaat Mitte Mai bis Samenernte September/Oktober. Starkzehrer mit hoechstem Borbedarf aller gaengigen Kulturen. Kein Zyklus-Neustart (Pflanze stirbt nach Ernte). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | sonnenblume, helianthus, annuus, plagron, terra, erde, outdoor, freiland, starkzehrer, samen | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaerig, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 2 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 2-Tage-Intervall als Basis fuer etablierte Pflanzen im Freiland. Sonnenblumen haben enormen Wasserbedarf -- bei Hitze (>25 C) taeglich giessen (besonders VEGETATIVE und FLOWERING). In GERMINATION taeglich (Override 1 Tag, Boden konstant feucht fuer Keimung), in HARVEST reduziert auf alle 3--4 Tage (Override 3 Tage). Die Pfahlwurzel (bis 150--200 cm!) erschliesst tieferes Bodenwasser, dennoch regelmaessig giessen fuer optimale Naehrstoffaufnahme.

---

## 2. Phasen-Mapping

Sonnenblumen sind einjaerige Pflanzen mit linearem Lebenszyklus. Typische Sorten: Mammut (Riese, bis 4 m), Sunrich Orange, Velvet Queen, Teddy Bear (Zwerg). Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Sonnenblumen-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|--------------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Mitte Mai | Direktsaat nach letztem Frost. Bodentemperatur >10 C. Kein Duenger. | false |
| Saemling | SEEDLING | 3--5 | Ende Mai--Mitte Juni | Jungpflanze mit 2--4 echten Blaettern. Halbe Dosis Terra Grow + Power Roots. | false |
| Vegetatives Wachstum | VEGETATIVE | 6--12 | Mitte Juni--Ende Juli | Explosives Wachstum (5--10 cm/Tag!). Volle Duengung mit allen Additiven. Stab/Stuetze noetig ab 1 m. | false |
| Bluete | FLOWERING | 13--16 | August | Umstellung auf Terra Bloom + Green Sensation (PK-Booster). Bestaeubung durch Insekten. | false |
| Fruchtreife/Samenreife | HARVEST | 17--22 | September--Mitte Oktober | Reduzierte Duengung, dann Duenger-Stopp 2--3 Wochen vor Ernte. Samen reif wenn Kopfrueckseite braun. | false |

**Nicht genutzte Phasen:**
- **FLUSHING** entfaellt (Freiland, kein Substrat-Flush noetig)
- **DORMANCY** entfaellt (einjaerige Pflanze, stirbt nach Samenernte)

**Kein Zyklus-Neustart:** Helianthus annuus ist strikt einjaerig. Nach der Samenernte stirbt die Pflanze ab. Fuer eine neue Saison muss neu ausgesaet werden. `cycle_restart_from_sequence: null`.

**Lueckenlos-Pruefung:** 2 + 3 + 7 + 4 + 6 = 22 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne im Freiland. Verschiedene Kanaele fuer unterschiedliche Produktkombinationen und Lebensphasen.

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Keimwasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Nur klares Wasser. Boden gleichmaessig feucht halten, nicht verschlaemmen. | `delivery_channels.notes` |
| method_params | drench, 0.1--0.3 L pro Pflanzstelle (je nach Bodenbeschaffenheit; bei sandigen Boeden mehr, bei verdichteten/feuchten Boeden weniger) | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow → Power Roots → Sugar Royal → Pure Zym → pH pruefen. Giessvolumen steigend: 1.0 L (Saemling) bis 2.0 L (spaet-vegetativ) pro Pflanze. | `delivery_channels.notes` |
| method_params | drench, 1.0--2.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom → Sugar Royal → Pure Zym → pH pruefen. 2.0--3.0 L pro Pflanze (hoechster Wasserbedarf!). **Kein Green Sensation in fruehen Bluetwochen** (Herstellervorgabe: nicht in den ersten 3 Bluetewochen einsetzen). GS wird stattdessen in der HARVEST-Phase (Kornfuellung) eingesetzt. | `delivery_channels.notes` |
| method_params | drench, 2.0--3.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Fuer Keimphase und letzte 2--3 Wochen vor Samenernte. | `delivery_channels.notes` |
| method_params | drench, 1.0--2.0 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Sonnenblumen

Sonnenblumen sind Starkzehrer mit hoher Salztoleranz. Ziel-EC der Gesamtloesung: **0.8--1.6 mS/cm** (inkl. Basis-Wasser). Leitungswasser liefert typisch 0.3--0.7 mS/cm (je nach Region). Als Starkzehrer vertragen Sonnenblumen volle Plagron-Dosierungen ohne Reduktion. **KEIN frischer Stallmist** -- ueberschuessiger Stickstoff fuehrt zu weichem Gewebe und erhoehter Sclerotinia-Anfaelligkeit. **Bor ist kritisch:** Sonnenblumen haben den hoechsten Borbedarf aller gaengigen Kulturen. Mangel = Hohlstaengel, deformierte Bluetenkoepfe, reduzierter Samenansatz.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Durchgehend ab Saemling |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Bluete |
| Green Sensation (0-9-10) | 0.05 | 30 | Ernte (W17--19, Kornfuellung) |

### 4.1 GERMINATION -- Keimung (Woche 1--2)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 2 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Direktsaat ins Freiland nach letztem Frost (Mitte Mai, Mitteleuropa). Bodentemperatur mindestens 10 C. Saattiefe 2--3 cm, Abstand 40--60 cm. Boden gleichmaessig feucht halten, nicht verschlaemmen. Kein Duenger -- Samenkorn liefert Startenergie. Keimung in 7--14 Tagen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (Boden konstant feucht fuer Keimung) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.3--0.5 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 3--5)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 5 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 1, 1) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis Terra Grow. Jungpflanze hat 2--4 echte Blaetter und beginnt das Pfahlwurzelsystem aufzubauen. Power Roots foerdert Wurzelentwicklung -- besonders wichtig fuer die tiefgehende Pfahlwurzel. Pure Zym fuer Bodenbiologie. Noch kein Sugar Royal oder Green Sensation. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.8  |
| reference_ec_ms | 0.8  |
| target_ph | 6.5 |
| Terra Grow ml/L | 2.5 (halbe Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | -- (noch nicht) |
| Green Sensation ml/L | -- (noch nicht) |

**EC-Budget:** 0.20 (TG 2.5ml) + 0.01 (PR) + 0.00 (PZ) + ~0.5 (Wasser) = **~0.7 mS/cm** ✓

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 6--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 6 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | MASSIVES Wachstum -- Staengel koennen 5--10 cm pro Tag zulegen! Volle Terra Grow Dosis (5 ml/L). Alle Additive einsetzen: Power Roots (Pfahlwurzel bis 150--200 cm), Pure Zym (Bodenbiologie), Sugar Royal (Aminosaeuren, Chlorophyllstimulation). Ab 1 m Hoehe Stuetzstab setzen. Bei Hitze >25 C taeglich giessen. **Kalium-Versorgung:** Terra Grow 3-1-3 liefert gutes K-Verhaeltnis fuer Stengelfestigkeit. **Bor-Ueberwachung:** Bei Symptomen (Hohlstaengel, deformierte Blaetter) sofort Blattspritzung mit Borsaeure 150 ppm als Notmassnahme. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.5 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.40 (TG 5ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.5 (Wasser) = **~0.93 mS/cm** ✓

**Hinweis EC-Diskrepanz:** Der target_ec von 1.5 mS/cm wird bei mittlerem Leitungswasser-EC (0.5 mS/cm) mit der angegebenen Dosierung nicht erreicht (~0.93 mS/cm). Bei kalkarmem Wasser (EC <0.3 mS/cm) kann Terra Grow auf 7.0 ml/L angehoben werden (EC ~1.4 mS/cm). Bei hartem Wasser (EC 0.7+ mS/cm) ergibt sich ~1.1 mS/cm -- fuer Starkzehrer in voller Wachstumsphase sind 1.2--1.5 mS/cm Gesamt-EC anzustreben.

### 4.4 FLOWERING -- Bluete (Woche 13--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 2, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Boron (ppm) | null (Ziel-ppm nicht berechenbar, da Konzentrat-Dichte nicht dokumentiert; Bor-Versorgung ueber Terra Bloom 0.48% B abgedeckt -- siehe notes) | `phase_entries.boron_ppm` |
| Hinweise | Umstellung auf Terra Bloom bei ersten Knospen. **Kein Green Sensation** in der fruehen Bluetephase (Herstellervorgabe: erst ab 4. Bluetewoche) -- bei nur 4-woechiger Bluetephase wird GS stattdessen in HARVEST zur Kornfuellung eingesetzt. **Bor-Versorgung:** Terra Bloom enthaelt 0.48% B -- das ist ein entscheidender Vorteil fuer Sonnenblumen, die den hoechsten Borbedarf aller gaengigen Kulturen haben. Bor ist essentiell fuer Pollenkeimung, Pollenschlauchwachstum und Samenansatz. Sugar Royal weiter fuer Aminosaeuren-Versorgung. Power Roots absetzen (optional: Power Roots kann die ersten 2 Wochen der FLOWERING-Phase weitergefuehrt werden bis Woche 14, um Wurzeln bei Hitzebelastung zu unterstuetzen). Hoechster Wasserbedarf (2--3 L pro Pflanze/Tag bei Hitze). **Bestaeubung:** Sonnenblumen sind Bienenweide -- Insektenflug nicht stoeren, morgens giessen (nicht Bluetenkoepfe bespritzen). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.3 |
| Terra Bloom ml/L | 5.0 (volle Dosis) |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.50 (TB 5ml) + 0.00 (PZ) + 0.02 (SR) + ~0.5 (Wasser) = **~1.02 mS/cm** ✓ (Starkzehrer toleriert bis 1.6; Green Sensation wird erst in HARVEST eingesetzt, s. K-001)

### 4.5 HARVEST -- Fruchtreife/Samenreife (Woche 17--22)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 17 | `phase_entries.week_start` |
| week_end | 22 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (3 ml/L) + **Green Sensation** (1 ml/L, Woche 17--19) fuer Kornfuellung und K-Versorgung waehrend der Samenreife. TB-Reduktion auf 3 ml/L kompensiert GS-EC-Beitrag (Herstellervorgabe: -20% Basisdosis bei GS-Einsatz). Kein Sugar Royal -- organischer Stickstoff (9-0-0) nicht mehr noetig, Pflanze mobilisiert Reserven aus Blaettern. Pure Zym weiter fuer Bodenbiologie. **Duenger-Stopp 2--3 Wochen vor Ernte:** Ab Woche 20 nur noch klares Wasser (Delivery Channel wasser-pur). Woche 20--22 entspricht der Seneszenz-Phase (terminal) des Pflanzensteckbriefs -- die Pflanze stellt aktives Wachstum ein, Naehrstoffe werden aus den Blaettern in die Samen mobilisiert. Giessen reduzieren auf alle 3--4 Tage. **Erntereife-Zeichen:** Rueckseite des Bluetenkopfes wird braun, Randblumen sind abgefallen, Samen loesen sich bei leichtem Druck. Bei Vogelfrass: Netz oder Papiertüete ueber den Kopf. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Samenreife) | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-bluete** (Woche 17--19)

| Feld | Wert |
|------|------|
| target_ec_ms | 1.0  |
| reference_ec_ms | 1.0  |
| target_ph | 6.3 |
| Terra Bloom ml/L | 3.0 (reduziert, -20% wg. Green Sensation) |
| Green Sensation ml/L | 1.0 (Kornfuellung, K-Versorgung) |
| Pure Zym ml/L | 1.0 |

**EC-Budget (Woche 17--19):** 0.30 (TB 3ml) + 0.05 (GS 1ml) + 0.00 (PZ) + ~0.5 (Wasser) = **~0.85 mS/cm** ✓

**Delivery Channel: wasser-pur** (Woche 20--22, Duenger-Stopp)

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer, nur klares Wasser) |

**EC-Budget (Woche 20--22):** ~0.3--0.5 (nur Wasser) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Basierend auf Direktsaat Mitte Mai, Mitteleuropa. Einjaerige Kultur ohne Zyklus-Neustart.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | Green Sensation ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|---------------------|-----------------|----------|
| Jan--April | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Mai (spaet) | GERM→SEED | -- → 2.5 | -- | -- → 1.0 | -- → 1.0 | -- | -- | 0 → 0.8 | taeglich → alle 2d |
| Juni | SEED→VEG | 2.5 → 5.0 | -- | 1.0 | 1.0 | -- → 1.0 | -- | 0.8 → 1.5 | alle 2d |
| Juli | VEG | 5.0 | -- | 1.0 | 1.0 | 1.0 | -- | 1.5 | alle 1--2d |
| August | VEG→FLOW | -- | 5.0 | -- | 1.0 | 1.0 | -- | 1.5 | alle 1--2d |
| September | FLOW→HARV | -- | 5.0 → 3.0 → 0 | -- | 1.0 → 0 | 1.0 → 0 | -- → 1.0 → 0 | 1.5 → 1.0 → 0 | alle 2d → alle 3d |
| Oktober | HARVEST→ -- | -- | -- | -- | -- | -- | -- | 0 | alle 3--4d → Stopp |
| Nov--Dez | -- | -- | -- | -- | -- | -- | -- | -- | -- |

```
Monat:           |Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:        |---|---|---|---|G→S|S→V|VEG|V→F|F→H|H→-|---|---|
Terra Grow:      |---|---|---|---|.##|#==|===|---|---|---|---|---|
Terra Bloom:     |---|---|---|---|---|---|---|===|==#|---|---|---|
Power Roots:     |---|---|---|---|.==|===|===|---|---|---|---|---|
Pure Zym:        |---|---|---|---|.==|===|===|===|==#|---|---|---|
Sugar Royal:     |---|---|---|---|---|.==|===|===|=..|---|---|---|
Green Sensation: |---|---|---|---|---|---|---|---|=..|---|---|---|

Legende: --- = nicht verwendet, ### = halbe Dosis, === = volle Dosis
         .== = anlaufend (Start innerhalb Monat), =.. = auslaufend
         =.# = voll → reduziert, =.#→ Stopp
```

### Jahresverbrauch (geschaetzt)

Bei einer Sonnenblume im Freiland, Giessvolumen 1.0--3.0 L pro Duengung (steigend mit Pflanzengroesse):

| Produkt | Formel | Verbrauch/Pflanze |
|---------|--------|-------------------|
| Terra Grow | (3 Wo x 2/Wo x 1L x 2.5ml + 7 Wo x 3/Wo x 1.5L x 5ml) = 172.5 ml | **~175 ml** |
| Terra Bloom | (4 Wo x 3.5/Wo x 2.5L x 5ml + 3 Wo x 2/Wo x 2L x 3ml) = 211 ml | **~210 ml** |
| Power Roots | (10 Wo x 3/Wo x 1.5L x 1ml) = 45 ml | **~45 ml** |
| Pure Zym | (17 Wo x 3/Wo x 1.5L x 1ml) = 76.5 ml | **~75 ml** |
| Sugar Royal | (11 Wo x 3/Wo x 2L x 1ml) = 66 ml | **~65 ml** |
| Green Sensation | (4 Wo x 3.5/Wo x 2.5L x 1ml) = 35 ml | **~35 ml** |

**Kosten-Schaetzung:** Bei 1L-Flaschen reicht das Sortiment (ohne Green Sensation 250ml) fuer ca. 4--5 Sonnenblumen pro Saison. Sonnenblumen sind deutlich duenger-intensiver als Erdbeeren (Starkzehrer vs. Mittelzehrer).

---

## 6. Sonnenblumen-spezifische Praxis-Hinweise

### Standort und Boden

- **Volle Sonne** (Volllichtpflanze) -- mindestens 6--8 Stunden direkte Sonne taeglich
- **Tiefgruendiger, lockerer Boden** -- Pfahlwurzel reicht bis 150--200 cm! Mindestens 30 cm Bodentiefe, idealerweise unverdichteter Untergrund
- **pH 6.0--6.8** (leicht sauer bis neutral), optimal fuer Naehrstoffverfuegbarkeit und Bor-Aufnahme
- **Drainage** wichtig -- Sonnenblumen vertragen keine Staunaesse (Fusarium-Risiko)
- **Abstand:** 40--60 cm zwischen Pflanzen (Riesen-Sorten 60 cm, Zwerge 30 cm)

### Bor-Management (KRITISCH)

Helianthus annuus hat den **hoechsten Borbedarf aller gaengigen Kulturpflanzen**. Bormangel ist eine der haeufigsten Ursachen fuer Ernteausfaelle bei Sonnenblumen.

- **Mangelsymptome:** Hohlstaengel, sprode/bruechigeStaengel, deformierte oder asymmetrische Bluetenkoepfe, schlechter Samenansatz, verdickte/verformte Blaetter, abgestorbene Triebspitzen
- **Plagron Terra Bloom** enthaelt 0.48% Bor -- damit ist die Bor-Versorgung ab der FLOWERING-Phase gut abgedeckt
- **Risikophase:** VEGETATIVE -- hier wachsen die Staengel am schnellsten, aber Terra Grow hat weniger Bor als Terra Bloom
- **Notfall-Blattspritzung:** Bei Mangelsymptomen in der VEGETATIVE-Phase: Borsaeure-Loesung 150 ppm (= 0.15 g/L) als Blattapplikation, max. 2x im Abstand von 7 Tagen. VORSICHT: Bor hat eine enge Spanne zwischen Mangel und Toxizitaet!
- **Vorbeugend:** Vor der Aussaat 1 g Borax pro m² in den Boden einarbeiten (optional, bei bekanntem Bormangel-Standort). Besonders empfohlen bei sandigen, ausgelaugten Boeden und in Regionen mit bekanntem Bormangel (z.B. Norddeutsche Tiefebene). Der optimale Bor-Bodengehalt fuer Sonnenblumen liegt bei 0.5--1.0 mg B/kg Boden (heisswasser-loesliches B)

### Kalium fuer Stengelfestigkeit

- Sonnenblumen-Staengel muessen enorme Lasten tragen (Bluetenkopf bis 30--40 cm Durchmesser, gefuellt mit Samen)
- **Kalium** ist Schluesselelement fuer Zellturgordruck und Staengelstabilitaet
- Terra Grow (3-1-**3**) und Terra Bloom (2-2-**4**) liefern gute K-Versorgung
- Green Sensation (0-9-**10**) verstaerkt die K-Versorgung in der kritischen Bluete-/Samenphase
- Bei Windexposition: Stuetzstab ab 1 m Hoehe setzen, auch mit optimaler K-Versorgung

### Stickstoff-Management

- **Kein frischer Stallmist!** Ueberschuessiger Stickstoff fuehrt zu weichem Gewebe, erhoehter Lager-Gefahr (Umknicken) und Sclerotinia-Anfaelligkeit
- Terra Grow (3 N) ist gut balanciert -- nicht ueber 5 ml/L dosieren
- Sugar Royal (9-0-0 organisch) nur in VEGETATIVE und FLOWERING, nicht in HARVEST
- In der HARVEST-Phase: N-Bedarf sinkt drastisch, Pflanze mobilisiert N aus Blaettern in die Samen

### Allelopathie-Warnung

Helianthus annuus bildet **allelopathische Substanzen** (Heliannuol A--E), die das Wachstum benachbarter Pflanzen hemmen koennen:

- **Wurzelexudate** koennen waehrend der Kultur Nachbarpflanzen beeintraechtigen -- Abstand halten
- **Nach der Ernte:** Sonnenblumen-Staengel und -Wurzeln NICHT sofort in Gartenbeete einarbeiten
- **Empfehlung:** Pflanzenreste separat kompostieren (4--6 Wochen Mindestzeit) oder verbrennen/entsorgen
- **Fruchtfolge:** 3--4 Jahre Anbaupause fuer Asteraceae am gleichen Standort

### Fruchtfolge (Asteraceae-Pause)

- Sonnenblumen gehoeren zur Familie Asteraceae
- **3--4 Jahre Anbaupause** fuer alle Asteraceae (Sonnenblumen, Topinambur, Salat, Endivie, Artischocke) am gleichen Standort
- Gute Vorfruechte: Getreide, Leguminosen (Stickstoff-Nachlieferung!)
- **Empfindliche Nachkulturen:** Salat, Kopfsalat, Endivie, Weizen -- diese reagieren besonders auf allelopathische Rueckstaende
- Gute Nachfruechte: Leguminosen, Gruenduengung (Boden regenerieren nach Starkzehrer)
- Sonnenblumen selbst sind **exzellente Gruenduengung** -- die tiefe Pfahlwurzel lockert verdichteten Boden

### Schaedlinge und Krankheiten

- **Sclerotinia sclerotiorum** (Weissfaeule): Wichtigste Krankheit. Praevention durch massvolle N-Duengung und gute Belueftung
- **Botrytis cinerea** (Grauschimmel): Am Bluetenkopf, besonders bei feuchter Witterung
- **Blattlaeuse:** Haeufig an Triebspitzen und Knospen. Nuetzlinge foerdern (Marienkaefer, Schwebfliegen)
- **Schnecken:** Jungpflanzen (SEEDLING) besonders gefaehrdet -- Schneckenschutz in den ersten 4 Wochen!
- **Voegel:** Spaetphase (HARVEST) -- Spatzen und Finken fressen reifende Samen. Netz oder Papiertuete ueber Bluetenkopf

### Bestaeubung

- Sonnenblumen sind **hervorragende Bienenweide** -- Bienen, Hummeln, Schwebfliegen
- Bluetenkoepfe oeffnen von aussen nach innen ueber 5--7 Tage
- **Nicht** morgens die Bluetenkoepfe bespritzen -- Pollen wird nass und unattraktiv fuer Bestaeubung
- Giessen am Stammbasis, nicht von oben

### Ernte und Nacherntebehandlung

- **Erntezeitpunkt:** Rueckseite des Bluetenkopfes braun, Randblumen (Zungenblueten) abgefallen, Samen lassen sich bei leichtem Druck loesen
- **Trocknung:** Bluetenkopf abschneiden (30 cm Stiel lassen), kopfueber an trockenen, luftigen Ort haengen, 2--3 Wochen trocknen
- **Samen loesen:** Nach Trocknung Samen mit den Haenden oder einer Buerste auskratzen
- **Lagerung:** Trockene Samen (Feuchte <10%) in luftdichtem Behaelter kuehl lagern, haltbar 1--2 Jahre
- **Speisesamen:** Vollelgefuellte grosse Samen (Sorte "Mammut" oder "Schwarze Russische"), duennschalig

### Sicherheitshinweise

- **Ungiftig:** Sonnenblumen sind nicht giftig fuer Katzen, Hunde und Kinder. Samen sind essbar (Sonnenblumenkerne)!
- **Pollen-Allergie:** Asteraceae-Pollen kann bei empfindlichen Personen allergische Reaktionen ausloesen (Heuschnupfen, Kontaktdermatitis). Bei bekannter Kompositen-Allergie Vorsicht beim Umgang mit Bluetenkoepfen
- **Plagron-Konzentrate:** Alle Fluessigduenger bei Verschlucken giftig, von Kindern fernhalten, Handschuhe beim Anmischen empfohlen
- **Allelopathie:** Pflanzenreste nicht direkt in Beete einarbeiten (s. Abschnitt Allelopathie-Warnung)

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Sonnenblume \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Sonnenblumen (Helianthus annuus) im Freiland. Plagron Terra-Linie mit 6 Produkten (inkl. Green Sensation als PK-Booster). Einj\u00e4hrige Kultur: Direktsaat Mitte Mai bis Samenernte September/Oktober. Starkzehrer mit h\u00f6chstem Borbedarf aller g\u00e4ngigen Kulturen.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["sonnenblume", "helianthus", "annuus", "plagron", "terra", "erde", "outdoor", "freiland", "starkzehrer", "samen"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 2,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 7.2 NutrientPlanPhaseEntry (5 Eintraege)

#### GERMINATION

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 2,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Direktsaat ins Freiland nach letztem Frost (Mitte Mai). Bodentemperatur \u226510\u00b0C. Saattiefe 2\u20133 cm. Boden gleichm\u00e4\u00dfig feucht halten. Kein D\u00fcnger.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 1,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-keimung",
      "label": "Keimwasser (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares Wasser. Boden gleichm\u00e4\u00dfig feucht halten.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
    }
  ]
}
```

#### SEEDLING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "seedling",
  "sequence_order": 2,
  "week_start": 3,
  "week_end": 5,
  "is_recurring": false,
  "npk_ratio": [2.0, 1.0, 1.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Halbe Dosis Terra Grow. Jungpflanze baut Pfahlwurzelsystem auf. Power Roots f\u00f6rdert Wurzelentwicklung.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow halbe Dosis + Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 pH pr\u00fcfen",
      "target_ec_ms": 0.8,
      "reference_ec_ms": 0.8,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.5, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

#### VEGETATIVE

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 3,
  "week_start": 6,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Volle Dosis Terra Grow (5 ml/L). Massives Wachstum (5\u201310 cm/Tag). Alle Additive einsetzen. St\u00fctzstab ab 1 m H\u00f6he. Bei Bormangel-Symptomen (Hohlst\u00e4ngel): Bors\u00e4ure 150 ppm Blattspritzung als Notma\u00dfnahme.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + alle Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Sugar Royal \u2192 Pure Zym \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 2.0}
    }
  ]
}
```

#### FLOWERING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flowering",
  "sequence_order": 4,
  "week_start": 13,
  "week_end": 16,
  "is_recurring": false,
  "npk_ratio": [1.0, 2.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "boron_ppm": null,
  "notes": "Umstellung auf Terra Bloom. Kein Green Sensation in fr\u00fcher Bl\u00fcte (Herstellervorgabe: nicht in ersten 3 Bl\u00fctewochen). GS wird in HARVEST zur Kornf\u00fcllung eingesetzt. Terra Bloom 0.48% Bor \u2014 kritisch f\u00fcr Pollenkeimung und Samenansatz. Power Roots optional bis Woche 14 weitergef\u00fchrt (Wurzelunterst\u00fctzung bei Hitze). H\u00f6chster Wasserbedarf. Best\u00e4ubung nicht st\u00f6ren.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive. Reihenfolge: Terra Bloom \u2192 Sugar Royal \u2192 Pure Zym \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.3,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 3.0}
    }
  ]
}
```

#### HARVEST

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "harvest",
  "sequence_order": 5,
  "week_start": 17,
  "week_end": 22,
  "is_recurring": false,
  "npk_ratio": [0.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Reduzierter Terra Bloom + Green Sensation (W17\u201319) f\u00fcr Kornf\u00fcllung, dann D\u00fcnger-Stopp (W20\u201322). GS liefert K f\u00fcr \u00d6lgehalt und P f\u00fcr ATP-Biosynthese. TB auf 3 ml/L reduziert (Herstellervorgabe: -20% bei GS). W20\u201322 entspricht Seneszenz-Phase (terminal) des Steckbriefs \u2014 N\u00e4hrstoffmobilisierung aus Bl\u00e4ttern in Samen. Samen reifen \u2014 R\u00fcckseite des Kopfes wird braun. Gie\u00dfen reduzieren. Bei Vogelfrass Netz \u00fcber Bl\u00fctenkopf.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom + Green Sensation + Pure Zym. Nur W17\u201319, danach auf wasser-pur wechseln. TB reduziert auf 3 ml/L wg. GS (Herstellervorgabe: -20%).",
      "target_ec_ms": 1.0,
      "reference_ec_ms": 1.0,
      "target_ph": 6.3,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<green_sensation_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 2.0}
    },
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (D\u00fcnger-Stopp)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Ab Woche 20: kein D\u00fcnger, nur klares Wasser. 2\u20133 Wochen vor Samenernte.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 2.0}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Power Roots | `spec/ref/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Sugar Royal | `spec/ref/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Green Sensation | `spec/ref/products/plagron_green_sensation.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/ref/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/ref/products/plagron_sugar_royal.md`
6. Plagron Green Sensation Produktdaten: `spec/ref/products/plagron_green_sensation.md`
7. Pflanzendaten: `spec/ref/plant-info/helianthus_annuus.md`
8. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
9. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
