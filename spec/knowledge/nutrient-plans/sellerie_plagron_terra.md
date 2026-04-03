# Naehrstoffplan: Knollensellerie -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Apium graveolens var. rapaceum (Starkzehrer, Indoor-Vorkultur + Outdoor ab Mai)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_*.md, spec/ref/products/plagron_power_roots.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_sugar_royal.md, spec/ref/plant-info/apium_graveolens_var_rapaceum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Knollensellerie -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Knollensellerie mit Indoor-Vorkultur ab Mitte Februar und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 5 Produkten. Klassischer Starkzehrer mit sehr langer Kulturzeit (180--200 Tage), hohem Ca/K-Bedarf und Bor-Empfindlichkeit. Einjaehrige Kultur (biologisch zweijahrig), kein Zyklus-Neustart. 32 Wochen Gesamtdauer (Februar--Oktober). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | sellerie, knollensellerie, celeriac, apium, graveolens, starkzehrer, plagron, terra, erde, outdoor, wurzelgemuese | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaehrig, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 1 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Taeglich giessen als Sommerbasis -- Knollensellerie hat einen sehr hohen Wasserbedarf. Gleichmaessige Wasserversorgung ist entscheidend: Trockenheit fuehrt zu holzigen, rissigen Knollen und Hohlraeumen. In GERMINATION (1 Tag, leichte Spruehung), SEEDLING (2 Tage) und FLUSHING (3 Tage) ueber `watering_schedule_override` angepasst. Mulchen mit Rasenschnitt oder Stroh hilft, die Bodenfeuchte zu stabilisieren.

---

## 2. Phasen-Mapping

Knollensellerie ist eine zweijahrige Pflanze, die im 1. Kulturjahr als Einjaehrige genutzt wird (Ernte vor der Bluete im 2. Jahr). Sehr lange Kulturzeit (180--200 Tage). Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Sellerie-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|---------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--3 | Mitte Februar--Anfang Maerz | Indoor-Aussaat, Lichtkeimer, 20--22 degC, hohe Luftfeuchte. Kein Duenger. Sehr langsame Keimung (14--28 Tage). | false |
| Saemling | SEEDLING | 4--10 | Maerz--Ende April | Sehr lange Jungpflanzenphase. Pikieren nach 2. echtem Blattpaar. ACHTUNG: Nie unter 10 degC -- Vernalisation loest Schossen aus! | false |
| Vegetatives Wachstum | VEGETATIVE | 11--18 | Mai--Ende Juni | Auspflanzung nach Eisheiligen (ca. 15. Mai). Volle Duengung Terra Grow. Blattrosetten-Aufbau, Knollenbeginn. | false |
| Knollenbildung | FLOWERING | 19--28 | Juli--Mitte September | Umstellung auf Terra Bloom. Hauptknollenwachstum. K-betonte Duengung. Aeussere Blaetter entfernen, Seitenwurzeln abschneiden. | false |
| Ernte + Einlagerung | HARVEST | 29--30 | Mitte September--Oktober | Reduzierter Terra Bloom. Ernte vor starkem Frost. | false |
| Saisonende/Spuelung | FLUSHING | 31--32 | Oktober | Kein Duenger, nur Wasser + Pure Zym. Letzte Ernte, Einlagerung. | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (einjaehrige Kultur, keine Ueberwinterung der Pflanze; Knollen werden geerntet und eingelagert)

**Phasen-Mapping Knollenbildung -> FLOWERING:** Die Knollenbildungsphase wird auf FLOWERING gemappt, da sie die generative Wachstumsphase darstellt (Speicherorganbidlung statt Bluete). Dies entspricht dem Wechsel von N-betonter zu K-betonter Duengung, analog zur Bluetephase bei Fruchtgemuese.

**Kein Zyklus-Neustart:** Knollensellerie ist einjaehrig in Kultur. Nach Saisonende Knollen ernten und einlagern. Im Folgejahr: neue Pflanzen, neuer Durchlauf. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Apiaceae (Moehre, Petersilie, Fenchel, Pastinake, Dill) auf gleicher Flaeche!

**Lueckenlos-Pruefung:** 3 + 7 + 8 + 10 + 2 + 2 = 32 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Verschiedene Kanaele fuer unterschiedliche Produktkombinationen.

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Keimungsspruehung (Spruehflasche) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Nur Wasser, feine Spruehung. Substrat gleichmaessig feucht halten, nicht durchnaessen. LICHTKEIMER -- Samen NUR leicht andruecken, NICHT mit Erde bedecken! Abdeckung mit Klarsichtfolie/Haube fuer hohe Luftfeuchte (80--90%). | `delivery_channels.notes` |
| method_params | drench, 0.03 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Bodennah giessen, nicht ueber Blaetter (Septoria-Risiko). | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Knollenbildung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-knolle | `delivery_channels.channel_id` |
| Label | Knollenduengung K-betont (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> Sugar Royal -> pH pruefen. K-betonte Duengung foerdert Knollenqualitaet und Lagerfaehigkeit. | `delivery_channels.notes` |
| method_params | drench, 0.5--1.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Optionales Pure Zym fuer Substratpflege und Salzabbau. | `delivery_channels.notes` |
| method_params | drench, 1.0 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Knollensellerie

Knollensellerie ist ein Starkzehrer mit hoher EC-Toleranz (bis 2.4 mS/cm in Hydrokultur). **In Erdkultur** ist die benoetigte EC in der Giessloessung deutlich niedriger, da das Substrat Naehrstoffe puffert und speichert. Besonders hoher Ca- und K-Bedarf waehrend der Knollenbildung. **Bor-Mangel** fuehrt zu Herzfaeule (braune, hohle Stellen im Knolleninneren) -- Terra Bloom enthaelt 0.48% Bor, was eine gute Grundversorgung darstellt.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Knollenbildung, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Knollenbildung |

### 4.1 GERMINATION -- Keimung (Woche 1--3)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 3 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Indoor-Aussaat in Anzuchterde, **LICHTKEIMER** -- Samen NUR leicht andruecken, NICHT mit Erde bedecken! Substrattemperatur 20--22 degC (konstant, NICHT unter 16 degC). Feine Spruehung, gleichmaessig feucht. Kein Duenger -- Anzuchterde liefert Grundversorgung. Abdeckung mit Klarsichtfolie/Haube fuer hohe Luftfeuchte (80--90%). Taeglich lueften. Keimung nach 14--28 Tagen (sehr langsam und oft ungleichmaessig!). | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.03 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.2 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) -- Ziel-pH 6.0--6.5

### 4.2 SEEDLING -- Saemling (Woche 4--10)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 10 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 80 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 30 | `phase_entries.magnesium_ppm` |
| Hinweise | Sehr lange Jungpflanzenphase (7 Wochen). Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren in Einzeltoepfe (6--8 cm) nach 2. echtem Blattpaar (ca. Woche 6). Power Roots foerdert fruehe Wurzelentwicklung. **SCHOSS-GEFAHR:** Temperaturen NICHT unter 10 degC fuer laengere Zeit (>10 Tage) -- loest Vernalisation aus und Pflanze schiesst im 1. Jahr! Abhaertung ab Woche 9 vorsichtig durchfuehren -- nie unter 12 degC, idealerweise nur tagsueber bei 15+ degC. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.2 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | -- (noch nicht) |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm**

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 11--18)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 11 | `phase_entries.week_start` |
| week_end | 18 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Auspflanzung nach Eisheiligen (ca. 15. Mai), Pflanzabstand 35--40 cm. **FLACH pflanzen** -- Knolle waechst zur Haelfte ueber der Erde, NICHT mit Erde anhaeufeln! Volle Dosis Terra Grow (5 ml/L). Kraeftiger Blattrosetten-Aufbau. Power Roots weiter fuer Wurzelentwicklung. Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal fuer Chlorophyllbildung. Gleichmaessig giessen -- Trockenheit fuehrt zu holzigen Knollen! Mulchen empfohlen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.2 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 (optional) |

**EC-Budget:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm**

**Hinweis Erdkultur:** Die berechnete EC der Giessloessung (~0.8 mS/cm) liegt unter den hydroponischen Zielwerten (1.4--2.0 mS/cm). Das ist korrekt fuer Erdkultur -- das Substrat speichert und puffert Naehrstoffe. Bei wuechsigen Pflanzen Terra Grow auf 6--7 ml/L steigern (EC ~1.0 mS/cm).

### 4.4 FLOWERING -- Knollenbildung (Woche 19--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 19 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| NPK-Abweichung | Terra Bloom liefert NPK 2-2-4; Steckbrief-Ideal fuer Knollenbildung ist 2-1-4. Abweichung bei P ist systembedingt (1-Komponenten-Produkt) und praxistauglich. | |
| Calcium (ppm) | 180 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 60 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) wenn Knolle sichtbar ueber der Erde und ca. 3--5 cm Durchmesser hat. K-betonte Duengung foerdert Knollenqualitaet, Geschmack und Lagerfaehigkeit. Power Roots absetzen (Abschluss mit Ende VEGETATIVE, Woche 18). Pure Zym + Sugar Royal weiter. **Blaetter entfernen:** Ab Mitte Juli aeussere, aeltere Blaetter abbrechen (nicht schneiden). **Seitenwurzeln abschneiden:** Regelmaessig Seitenwurzeln an der Knollenoberseite entfernen -- foerdert glatte, runde Knolle. Nie mehr als 1/3 der Blaetter auf einmal entfernen! **Calcium-Hinweis:** Gleichmaessige Ca-Versorgung verhindert Schwarzherz. **Bor-Hinweis:** Terra Bloom enthaelt 0.48% Bor -- gute Grundversorgung. Bei Verdacht auf Bor-Mangel (Herzfaeule) zusaetzlich Borax-Blattspruehung (0.1% Loesung, einmalig im Juni). N ab August reduzieren (Lagerfaehigkeit). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-knolle**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.8  |
| reference_ec_ms | 1.8  |
| target_ph | 6.2 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 (bis August, dann absetzen) |

**EC-Budget:** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.92 mS/cm**

**Hinweis N-Reduktion:** Ab August (ca. Woche 24) Sugar Royal absetzen (organischer N 9-0-0), um die Knollenreife und Lagerfaehigkeit zu foerdern. Terra Bloom auf 4 ml/L reduzieren.

### 4.5 HARVEST -- Ernte + Einlagerung (Woche 29--30)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 29 | `phase_entries.week_start` |
| week_end | 30 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (3 ml/L). Kein Sugar Royal. Pure Zym weiter. Ernte wenn Knolle 10--15 cm Durchmesser hat, VOR starkem Frost (vertraegt leichte Froeste bis -5 degC). Knolle mit Grabgabel vorsichtig aus dem Boden heben. **Lagerung:** Blaetter auf ca. 5 cm kuerzen, Knollen in feuchtem Sand bei 0--2 degC lagern (haelt 4--6 Monate). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-knolle**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.2  |
| reference_ec_ms | 1.2  |
| target_ph | 6.2 |
| Terra Bloom ml/L | 3.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.30 (TB 3.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm**

### 4.6 FLUSHING -- Saisonende/Spuelung (Woche 31--32)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 6 | `phase_entries.sequence_order` |
| week_start | 31 | `phase_entries.week_start` |
| week_end | 32 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Salzreste aus Substrat ausspuelen. Letzte Knollen ernten und einlagern. Pflanzen kompostieren. Substrat kann fuer Nicht-Apiaceae wiederverwendet werden. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Pflanze baut ab) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.2 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm**

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan Februar--Oktober.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|-----------------|----------|
| Feb (spaet) | GERMINATION | -- | -- | -- | -- | -- | 0.4 | Spruehung 1d |
| Maerz | SEEDLING | 1.5 | -- | 1.0 | -- | -- | 0.5 | alle 2d |
| April | SEEDLING | 1.5 | -- | 1.0 | -- | -- | 0.5 | alle 2d |
| Mai | SEED->VEG | 1.5->5.0 | -- | 1.0 | -->1.0 | -->1.0 | 0.5->0.8 | 2d->1d |
| Juni | VEGETATIVE | 5.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | taeglich |
| Juli | VEG->FLOW | 5.0->-- | -->5.0 | 1.0->-- | 1.0 | 1.0 | 0.8->0.9 | taeglich |
| August | FLOWERING | -- | 5.0->4.0 | -- | 1.0 | 1.0->-- | 0.9->0.8 | taeglich |
| September | FLOW->HARV | -- | 4.0->3.0 | -- | 1.0 | -- | 0.8->0.7 | taeglich |
| Oktober | HARV->FLUSH | -- | 3.0->0 | -- | 1.0 | -- | 0.7->0.4 | taegl.->3d |

```
Monat:       |Feb(s)|Mär  |Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |Okt|
KA-Phase:    |GERM  |SEED |SEED |S→VEG|VEG  |V→FLO|FLOW |F→HAR|FLU|
Terra Grow:  |---   |##-  |##-  |##→==|===  |===  |---  |---  |---|
Terra Bloom: |---   |---  |---  |---  |---  |-->==|===→#|###  |---|
Power Roots: |---   |===  |===  |===  |===  |==→--|---  |---  |---|
Pure Zym:    |---   |---  |---  |-->==|===  |===  |===  |===  |===|
Sugar Royal: |---   |---  |---  |-->==|===  |===  |==→--|---  |---|

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, --> = Start, ->  = Uebergang
```

### Jahresverbrauch (geschaetzt)

Bei einer Sellerie-Pflanze, 0.5--1.0 L Giessloessung pro Duengung:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (7 Wo x 3.5/Wo x 1.5ml + 8 Wo x 7/Wo x 5ml) = 317 ml | **~320 ml** |
| Terra Bloom | (10 Wo x 7/Wo x 4.5ml + 2 Wo x 7/Wo x 3ml) = 357 ml | **~360 ml** |
| Power Roots | (15 Wo x 5/Wo x 1ml) = 75 ml | **~75 ml** |
| Pure Zym | (22 Wo x 6/Wo x 1ml) = 132 ml | **~130 ml** |
| Sugar Royal | (14 Wo x 7/Wo x 1ml) = 98 ml | **~100 ml** |

---

## 6. Knollensellerie-spezifische Praxis-Hinweise

### Herzfaeule (Bor-Mangel)

Herzfaeule ist die haeufigste physiologische Stoerung bei Knollensellerie -- braune, hohle Stellen im Knolleninneren, erst bei der Ernte sichtbar.

**Ursachen:**
- **Bor-Mangel** -- haeufigste Ursache, besonders auf leichten, sandigen Boeden
- **Kalkhaltiger Boden** (pH > 7.5) -- Bor wird bei hohem pH fixiert
- **Trockenheit** -- eingeschraenkte Bor-Aufnahme bei Wassermangel

**Praevention:**
- **Terra Bloom** enthaelt 0.48% Bor -- gute Grundversorgung ab Knollenbildungsphase
- **Borax-Blattspruehung** praeventiv im Juni: 0.1% Loesung (1 g Borax / 1 L Wasser), einmalig
- **Gleichmaessig giessen** -- Bor-Transport benoetigt stetigen Wasserstrom
- **pH 6.0--6.5** halten -- Bor-Verfuegbarkeit optimal in diesem Bereich

### Schwarzherz (Calcium-Mangel)

Schwarze Verfaerbung im Knolleninneren durch unzureichenden Ca-Transport.

**Praevention:**
- **Gleichmaessige Bewaesserung** -- wie bei BER der Tomate ist KONSISTENZ entscheidender als Menge
- **EC unter 2.0 mS/cm** in der Giessloessung halten
- **Mulchen** reduziert Verdunstung und stabilisiert Bodenfeuchte
- Bei weichem Wasser (<0.4 mS/cm) optional Calciumnitrat 0.3 g/L ins Giesswasser

### Schossen (Vernalisation)

**Das groesste Risiko bei Knollensellerie in der Jungpflanzenphase!**

- Temperaturen unter 10 degC fuer laengere Zeit (>10 Tage) in der Jungpflanzenphase loesen Vernalisation aus
- Die Pflanze "denkt" sie hat den Winter erlebt und bildet im 1. Jahr Bluetenstaende statt Knollen
- **Praevention:** Jungpflanzen IMMER ueber 12 degC halten, Abhaertung vorsichtig durchfuehren
- Schossfeste Sorten waehlen (z.B. 'Mars', 'Monarch')

### Blaetter und Seitenwurzeln entfernen

- Ab Mitte Juli aeussere, aeltere Blaetter **abbrechen** (nicht schneiden -- Bruchstelle heilt besser)
- Seitenwurzeln an der Knollenoberseite **abschneiden** -- foerdert glatte, runde Knolle
- Nie mehr als 1/3 der Blaetter auf einmal entfernen

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Apiaceae (Sellerie, Moehre, Petersilie, Fenchel, Pastinake, Dill) auf gleicher Flaeche
- **Gute Vorfruechte:** Huelsenfruechte (N-Fixierung), Gruenduengung
- **Gute Nachfruechte:** Schwachzehrer (Salat, Radieschen, Spinat)
- **Gute Nachbarn:** Lauch (klassisch!), Kohl, Tomate, Buschbohne
- **Schlechte Nachbarn:** Moehre, Petersilie, Pastinake (gleiche Familie)

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet

**Apium graveolens var. rapaceum ist NICHT giftig:**

- Alle Pflanzenteile sind essbar (Knolle, Stiel, Blaetter)
- **Phototoxisch:** Furanocumarine (Psoralen, Bergapten) in Blaettern/Stielen koennen bei intensivem Hautkontakt + Sonnenlicht Photodermatitis ausloesen (Sellerie-Dermatitis bei Feldarbeitern)
- **Sellerie-Allergie:** Eine der haeufigsten Nahrungsmittelallergien in Mitteleuropa, kreuzreaktiv mit Beifuss-Pollen (Beifuss-Sellerie-Syndrom)
- Bei empfindlichen Personen Handschuhe bei der Feldarbeit tragen

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Geerntete Knollen vor Verzehr gruendlich waschen und schaelen
- **2 Wochen duengerfreie FLUSHING-Phase** vor Saisonende empfohlen

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Knollensellerie \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Knollensellerie mit Indoor-Vorkultur ab Mitte Februar und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 5 Produkten. Starkzehrer mit sehr langer Kulturzeit, hohem Ca/K-Bedarf und Bor-Empfindlichkeit. 32 Wochen (Februar\u2013Oktober).",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["sellerie", "knollensellerie", "celeriac", "apium", "graveolens", "starkzehrer", "plagron", "terra", "erde", "outdoor", "wurzelgemuese"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 1,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 8.2 NutrientPlanPhaseEntry (6 Eintraege)

#### GERMINATION

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 3,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Indoor-Aussaat in Anzuchterde, LICHTKEIMER \u2013 Samen nur leicht andr\u00fccken. 20\u201322\u00b0C Substrattemperatur. Feine Spr\u00fchung, kein D\u00fcnger. Keimung nach 14\u201328 Tagen.",
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
      "label": "Keimungsspr\u00fchung (Spr\u00fchflasche)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur Wasser. Feine Spr\u00fchung, Substrat gleichm\u00e4\u00dfig feucht halten. Lichtkeimer!",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.2,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.03}
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
  "week_start": 4,
  "week_end": 10,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": 80,
  "magnesium_ppm": 30,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren nach 2. Blattpaar. Temperaturen NIE unter 10\u00b0C (Vernalisation/Schoss-Gefahr!). Abh\u00e4rtung ab Woche 9 vorsichtig, nie unter 12\u00b0C.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 2,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung S\u00e4mling (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis + Power Roots",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
  "week_start": 11,
  "week_end": 18,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": 150,
  "magnesium_ppm": 50,
  "notes": "Volle Dosis Terra Grow (5 ml/L). Auspflanzung nach Eisheiligen (ca. 15. Mai), flach pflanzen. Kr\u00e4ftiger Blattrosetten-Aufbau. Gleichm\u00e4\u00dfig gie\u00dfen, mulchen. Bei sehr w\u00fcchsigen Pflanzen auf 6\u20137 ml/L steigern.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + alle Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
    }
  ]
}
```

#### FLOWERING (Knollenbildung)

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flowering",
  "sequence_order": 4,
  "week_start": 19,
  "week_end": 28,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 180,
  "magnesium_ppm": 60,
  "notes": "Umstellung auf Terra Bloom (5 ml/L). K-betonte D\u00fcngung f\u00fcr Knollenqualit\u00e4t. Power Roots absetzen. \u00c4u\u00dfere Bl\u00e4tter ab Juli entfernen, Seitenwurzeln abschneiden. Sugar Royal bis August, dann absetzen (N-Reduktion). Terra Bloom ab August auf 4 ml/L reduzieren. Bor-Versorgung \u00fcber Terra Bloom (0.48% B). Gleichm\u00e4\u00dfig gie\u00dfen (Schwarzherz-Pr\u00e4vention).",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-knolle",
      "label": "Knollend\u00fcngung K-betont (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive. Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.8,
      "reference_ec_ms": 1.8,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true, "_comment": "Bis August, dann absetzen (N-Reduktion)"}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
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
  "week_start": 29,
  "week_end": 30,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 150,
  "magnesium_ppm": 50,
  "notes": "Reduzierter Terra Bloom (3 ml/L). Kein Sugar Royal. Ernte wenn Knolle 10\u201315 cm Durchmesser, vor starkem Frost. Lagerung: Bl\u00e4tter auf 5 cm k\u00fcrzen, Knollen in feuchtem Sand bei 0\u20132\u00b0C (4\u20136 Monate haltbar).",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-knolle",
      "label": "Ernte-D\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom. Kein Sugar Royal.",
      "target_ec_ms": 1.2,
      "reference_ec_ms": 1.2,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

#### FLUSHING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flushing",
  "sequence_order": 6,
  "week_start": 31,
  "week_end": 32,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Substrat mit klarem Wasser durchsp\u00fclen. Pure Zym f\u00fcr Salzabbau. Letzte Knollen ernten und einlagern. Pflanzen kompostieren.",
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
      "channel_id": "wasser-pur",
      "label": "Substratsp\u00fclung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur Wasser + Pure Zym. Kein D\u00fcnger.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    }
  ]
}
```

### 8.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/ref/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Power Roots | `spec/ref/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Sugar Royal | `spec/ref/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |
| Species: Apium graveolens var. rapaceum | `spec/ref/plant-info/apium_graveolens_var_rapaceum.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/ref/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/ref/products/plagron_sugar_royal.md`
6. Knollensellerie Pflanzensteckbrief: `spec/ref/plant-info/apium_graveolens_var_rapaceum.md`
7. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
8. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
