# Naehrstoffplan: Zucchini -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Cucurbita pepo (Starkzehrer, Vorkultur April + Freiland ab Mitte Mai)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_*.md, spec/knowledge/products/plagron_power_roots.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/products/plagron_sugar_royal.md, spec/knowledge/plants/cucurbita_pepo.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Zucchini -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Zucchini (Buschtyp) mit Indoor-Vorkultur ab Mitte April und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 5 Produkten. Klassischer Starkzehrer mit extrem schnellem Wachstum und hohem N-Bedarf in der vegetativen Phase, hohem K-Bedarf ab Fruchtbildung. Dauertraeger mit kontinuierlicher Ernte Juni--Oktober. Einjaehrige Kultur, kein Zyklus-Neustart. 22 Wochen Gesamtdauer (Mitte April--Mitte September). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | zucchini, courgette, cucurbita, pepo, starkzehrer, plagron, terra, erde, outdoor, gewaechshaus | `nutrient_plans.tags` |
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

**Hinweis:** Taeglich giessen als Sommerbasis -- Zucchini sind Starkzehrer mit sehr hohem Wasserbedarf (1--2 L/Pflanze/Tag bei Hitze und Fruchtbildung). Gleichmaessige Wasserversorgung ist essentiell zur BER-Praevention. In GERMINATION (1 Tag, leichte Spruehung) und SEEDLING (2 Tage) ueber `watering_schedule_override` angepasst. **Immer bodennah giessen** -- nie ueber die Blaetter (Mehltaurisiko!).

---

## 2. Phasen-Mapping

Zucchini ist eine einjaehrige Nutzpflanze in Mitteleuropa (Cucurbita pepo). Typische Sorten: Black Beauty, Defender F1, Partenon F1. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Zucchini-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|----------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Mitte April | Indoor-Aussaat in Einzeltoepfe, 22--25 degC. Dunkelkeimer, 2--3 cm tief. Kein Duenger. | false |
| Saemling | SEEDLING | 3--4 | Ende April--Anfang Mai | Jungpflanze mit Keimblaettern + ersten echten Blaettern. Viertel-Dosis Terra Grow. Nicht pikieren (empfindliche Wurzeln)! | false |
| Vegetatives Wachstum | VEGETATIVE | 5--8 | Mai--Anfang Juni | Volle Duengung Terra Grow. Extrem schnelles Blattwachstum. Abhaertung + Auspflanzen nach Eisheiligen (ca. 15. Mai). | false |
| Bluete + Fruchtbildung | FLOWERING | 9--12 | Juni--Anfang Juli | Umstellung auf Terra Bloom. Erste maennliche, dann weibliche Blueten. Bestaeubung durch Insekten oder Hand. | false |
| Dauerernte | HARVEST | 13--20 | Juli--Mitte September | Terra Bloom reduziert. Kontinuierliche Ernte alle 2--3 Tage bei 15--25 cm Fruchtlaenge. K:N-Verhaeltnis hoch. | false |
| Saisonende/Spuelung | FLUSHING | 21--22 | Mitte--Ende September | Kein Duenger, nur Wasser + Pure Zym. Letzte Fruechte ernten. Pflanze stirbt bei erstem Frost. | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (einjaehrige Kultur, keine Ueberwinterung)

**Kein Zyklus-Neustart:** Zucchini ist einjaehrig. Nach Saisonende (Woche 22, ca. Ende September/erster Frost) wird die Pflanze entfernt und kompostiert (nur gesunde Pflanzen; mehltaubefallene in Restmuell). **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Cucurbitaceae auf gleicher Flaeche!

**Lueckenlos-Pruefung:** 2 + 2 + 4 + 4 + 8 + 2 = 22 Wochen, keine Luecken

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
| Hinweise | Nur Wasser, feine Spruehung. Substrat gleichmaessig feucht halten, nicht durchnaessen. Dunkelkeimer -- Samen 2--3 cm tief bedecken. | `delivery_channels.notes` |
| method_params | drench, 0.03 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Bodennah giessen, nie ueber Blaetter! | `delivery_channels.notes` |
| method_params | drench, 0.5--1.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete/Frucht

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluete-/Fruchtduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> Sugar Royal -> pH pruefen. | `delivery_channels.notes` |
| method_params | drench, 1.0--2.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Optionales Pure Zym fuer Substratpflege und Salzabbau. | `delivery_channels.notes` |
| method_params | drench, 1.0--2.0 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Zucchini

Zucchini sind Starkzehrer mit hoher EC-Toleranz (bis 2.8 mS/cm in Hydrokultur, Steckbrief: 2.0--2.8 in Bluete/Frucht). **In Erdkultur** ist die benoetigte EC in der Giessloessung deutlich niedriger, da das Substrat Naehrstoffe puffert und speichert. Leitungswasser liefert typisch 0.2--0.8 mS/cm. Die Plagron-Dosierungen sind fuer Erdkultur kalibriert. EC ueber 3.0 mS/cm vermeiden (Salztoxizitaet).

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Bluete |

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
| Hinweise | Indoor-Aussaat in naehrstoffarme Anzuchterde, Samen einzeln in 8--10 cm Toepfe, 2--3 cm tief (Dunkelkeimer). Substrattemperatur 22--25 degC (Heizmatte empfohlen). Feine Spruehung, Substrat gleichmaessig feucht aber nicht nass. Kein Duenger -- Anzuchterde liefert Grundversorgung. Keimung nach 5--8 Tagen (bei optimaler Temperatur). Nicht pikieren -- Zucchini-Wurzeln sind empfindlich. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.03 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.2 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 3--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Jungpflanzen mit 2--3 echten Blaettern. Power Roots foerdert fruehe Wurzelentwicklung. Noch kein Pure Zym oder Sugar Royal noetig. Nicht pikieren! Kuehlere Nachttemperaturen (16 degC) foerdern gedrungenen Wuchs. Abhaertung beginnt Ende Woche 4 (7--10 Tage raus stellen). | `phase_entries.notes` |
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

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm** ✓

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 5--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Volle Dosis Terra Grow (5 ml/L). Extrem schnelles Blattwachstum -- Zucchini bilden in kurzer Zeit riesige Blattflaechen. Power Roots weiter fuer Wurzelentwicklung. Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal fuer Chlorophyllbildung und Aminosaeuren. **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai) in Freiland/Gewaechshaus. Pflanzabstand mind. 80--100 cm! Pflanzloch mit Kompost anreichern. Bei sehr wuechsigen Pflanzen kann auf 6--7 ml/L TG gesteigert werden. Starkzehrer -- grosszuegig duengen! | `phase_entries.notes` |

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

**EC-Budget:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm** ✓

**Hinweis Erdkultur:** Die berechnete EC der Giessloessung (~0.8 mS/cm) liegt unter den hydroponischen Zielwerten (1.6--2.2 mS/cm). Das ist korrekt fuer Erdkultur -- das Substrat speichert und puffert Naehrstoffe. Bei wuechsigen Pflanzen Terra Grow auf 6--7 ml/L steigern (EC ~1.0 mS/cm).

### 4.4 FLOWERING -- Bluete + Fruchtbildung (Woche 9--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150--180 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) bei ersten Bluetenknospen. Maennliche Blueten erscheinen zuerst (duenner Stiel), weibliche ca. 1 Woche spaeter (kleine Frucht am Stiel). Pure Zym + Sugar Royal weiter. Power Roots absetzen (Abschluss mit Ende VEGETATIVE). **Bestaeubung:** Insekten (Bienen, Hummeln) noetig. Bei schlechtem Fruchtansatz oder Gewaechshaus: Handbestaeubung (maennliche Bluete abzupfen, Pollen auf weibliche Bluete druecken). Bluetenendfaeule kann auch bei Zucchini auftreten -- gleichmaessig giessen! **Erste Ernte:** Ca. 5--6 Wochen nach Pflanzung, Fruechte bei 15--25 cm Laenge ernten. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 2.0  |
| reference_ec_ms | 2.0  |
| target_ph | 6.2 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |

**EC-Budget:** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.92 mS/cm** ✓

### 4.5 HARVEST -- Dauerernte (Woche 13--20)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 20 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150--180 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (4 ml/L) waehrend Dauerernte. Kein Sugar Royal mehr -- organischer Stickstoff (9-0-0) ist bei Fruchtkultur ab jetzt nicht mehr noetig und kann vegetatives Wachstum ueberbetonen. Pure Zym weiter fuer Substratgesundheit. **Dauertraeger:** Zucchini bildet laufend neue Blueten und Fruechte. Alle 2--3 Tage ernten! Fruechte bei 15--25 cm Laenge abschneiden (Messer). Ueberreife Fruechte (>30 cm) signalisieren der Pflanze, die Fruchtproduktion einzustellen -- daher regelmaessig ernten! **Mehltau-Management:** Echter Mehltau nimmt ab August oft zu. Befallene Blaetter entfernen, Pflanze weiterkultivieren. Kaliumbicarbonat (0.5%, Spruehung alle 7 Tage) oder Milch-Wasser (1:9) praeventiv spruehen. Bei grossen Pflanzen Terra Bloom auf 5 ml/L erhoehen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.8  |
| reference_ec_ms | 1.8  |
| target_ph | 6.2 |
| Terra Bloom ml/L | 4.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.40 (TB 4.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.80 mS/cm** ✓

**Hinweis Erdkultur:** Fuer grosse, ertragreiche Pflanzen (5--15 kg Fruechte pro Saison!) kann die Dosis auf 5 ml/L TB gesteigert werden (EC ~1.0 mS/cm). Drainagewasser-EC kontrollieren -- bei EC >2.5 mit klarem Wasser durchspuelen.

### 4.6 FLUSHING -- Saisonende/Spuelung (Woche 21--22)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 6 | `phase_entries.sequence_order` |
| week_start | 21 | `phase_entries.week_start` |
| week_end | 22 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Letzte Fruechte ernten. Pflanze stirbt beim ersten Frost ab. Pflanzenreste kompostieren (nur gesunde Pflanzen; mehltaubefallene in Restmuell). Substrat kann fuer andere Kulturen (keine Cucurbitaceae!) wiederverwendet werden. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Pflanze baut ab) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.2 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan Mitte April--Ende September.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|-----------------|----------|
| April (spaet) | GERM/SEED | -->1.5 | -- | 1.0* | -- | -- | 0.4->0.5 | Spruehung->2d |
| Mai (frueh) | SEEDLING/VEG | 1.5->5.0 | -- | 1.0 | 1.0* | 1.0* | 0.5->0.8 | 2d->1d |
| Mai (spaet) | VEGETATIVE | 5.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | taeglich |
| Juni | VEG->FLOW | 5.0->-- | -->5.0 | 1.0->-- | 1.0 | 1.0 | 0.8->0.9 | taeglich |
| Juli | FLOW->HARV | -- | 5.0->4.0 | -- | 1.0 | 1.0->-- | 0.9->0.8 | taeglich |
| August | HARVEST | -- | 4.0 | -- | 1.0 | -- | 0.8 | taeglich |
| September | HARV->FLUSH | -- | 4.0->0 | -- | 1.0 | -- | 0.8->0.4 | taegl.->3d |

*Power Roots ab SEEDLING (Woche 3). Pure Zym und Sugar Royal ab VEGETATIVE-Phase (ca. Mitte Mai, Woche 5).

```
Monat:       |Apr(s)|Mai(f)|Mai(s)|Jun  |Jul  |Aug  |Sep  |
KA-Phase:    |G→SEE |S→VEG |VEG   |V→FLO|F→HAR|HARV |H→FLU|
Terra Grow:  |-->##-|##→===|===   |==→--|---  |---  |---  |
Terra Bloom: |---   |---   |---   |-->==|==→##|###  |##→--|
Power Roots: |-->===|===   |===   |==→--|---  |---  |---  |
Pure Zym:    |---   |-->===|===   |===  |===  |===  |===  |
Sugar Royal: |---   |-->===|===   |===  |==→--|---  |---  |

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, --> = Start, ->  = Uebergang
```

### Jahresverbrauch (geschaetzt)

Bei einer Zucchinipflanze, 1.0--1.5 L Giessloessung pro Duengung, taeglich im Sommer:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (2 Wo x 3.5/Wo x 1.5ml + 4 Wo x 7/Wo x 5ml) = 150.5 ml | **~150 ml** |
| Terra Bloom | (4 Wo x 7/Wo x 5ml + 8 Wo x 7/Wo x 4ml) = 364 ml | **~365 ml** |
| Power Roots | (6 Wo x 5/Wo x 1ml) = 30 ml | **~30 ml** |
| Pure Zym | (16 Wo x 6/Wo x 1ml) = 96 ml | **~100 ml** |
| Sugar Royal | (8 Wo x 7/Wo x 1ml) = 56 ml | **~55 ml** |

**Kosten-Schaetzung:** Zucchini verbraucht weniger Naehrloesung als Tomaten (kuerzere Saison, 22 statt 28 Wochen). Bei 1L-Flaschen: Terra Bloom reicht fuer ca. 2--3 Pflanzen-Saisons, Terra Grow fuer ca. 6.

---

## 6. Zucchini-spezifische Praxis-Hinweise

### Bluetenendfaeule (Blossom End Rot, BER)

BER tritt auch bei Zucchini auf (gleicher Mechanismus wie bei Tomaten -- gestoeuter Calcium-Transport).

**Ursachen:**
- **Unregelmaessige Bewaesserung** (Nass-Trocken-Zyklen) -- haeufigste Ursache!
- **Zu hohe EC** (>2.5 mS/cm in Erdkultur)
- **Schnelles Fruchtwachstum** bei Hitze

**Praevention:**
- **Taeglich morgens gleichmaessig giessen** -- KONSISTENZ ist wichtiger als Menge!
- **Mulchen** mit Stroh (5--10 cm) -- reduziert Verdunstung, stabilisiert Bodenfeuchte
- **EC unter 2.5 mS/cm** in der Giessloessung halten

### Bestaeubung

Zucchini sind einhaeusig (getrenntgeschlechtliche Blueten an einer Pflanze). Bestaeubung durch Insekten ist essentiell.

**Handbestaeubung (bei schlechtem Fruchtansatz oder Gewaechshaus):**
- Maennliche Bluete morgens abzupfen (duenner Stiel, kein Fruchtknoten)
- Bluetenblaetter zurueckbiegen
- Pollen (gelb) auf die Narbe der weiblichen Bluete druecken (dicker Stiel mit kleiner Frucht)
- Alternativ: Pinsel, Wattebausch
- Maennliche Blueten erscheinen oft 1 Woche vor weiblichen -- das ist normal!

### Ernte-Timing

- **Optimal:** 15--25 cm Laenge, Schale glaenzend, Fingernagel-Test (Schale laesst sich leicht einritzen)
- **Alle 2--3 Tage kontrollieren** -- bei Waerme wachsen Zucchini 3--5 cm pro Tag!
- **Ueberreife Fruechte (>30 cm):** Vermeiden! Signalisieren der Pflanze, Fruchtproduktion einzustellen
- **Ertragsmonster:** 1 Pflanze liefert 5--15 kg Fruechte pro Saison
- **Ernte-Tipp:** Fruechte mit Messer abschneiden, 2--3 cm Stiel dran lassen

### Echter Mehltau

Die haeufigste Krankheit bei Zucchini. Tritt ab Hochsommer (August) fast immer auf.

**Praevention:**
- Pflanzabstand einhalten (mind. 80 cm) fuer gute Luftzirkulation
- Morgens giessen, nie ueber die Blaetter
- Milch-Wasser-Loesung (1:9) praeventiv alle 3--5 Tage spruehen
- Tolerante Sorten waehlen (Partenon F1, Ismalia F1)

**Bei Befall:**
- Befallene Blaetter entfernen (Restmuell, nicht Kompost!)
- Kaliumbicarbonat (0.5%) alle 7 Tage spruehen
- Pflanze weiterkultivieren -- auch mit Mehltau traegt sie noch Wochen Fruechte

### Substrat

- Naehrstoffreiche, humose Erde mit guter Drainage
- pH 6.0--7.0
- Topfgroesse: min. 40 L (Kuebel), besser 60 L
- Im Freiland: 80--100 cm Pflanzabstand, Pflanzloch mit Kompost und Hornmehl anreichern
- Mulchen mit Stroh reduziert Spritzwasser und Verdunstung

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Cucurbitaceae (Zucchini, Gurke, Kuerbis, Melone) auf gleicher Flaeche
- **Gute Vorfruechte:** Huelsenfruechte (N-Fixierung), Gruenduengung, Lauchgewaechse
- **Gute Nachfruechte:** Mittel- oder Schwachzehrer (Salat, Moehren, Radieschen)
- **Gute Nachbarn:** Mais, Stangenbohne (Milpa!), Basilikum, Borretsch, Kapuzinerkresse
- **Schlechte Nachbarn:** Gurke (gemeinsame Krankheiten), Kartoffel (Naehrstoffkonkurrenz)

---

## 7. Sicherheitshinweise

### WARNUNG Cucurbitacin-Vergiftung (WICHTIG!)

**Wenn Zucchini extrem bitter schmecken, NICHT essen!**

- Bittere Zucchini koennen toedliche Mengen Cucurbitacin enthalten
- Ursache: unkontrollierte Kreuzung mit Zierküerbissen (Bienen-Fremdbestaeubung) oder Stressreaktion
- **Immer VOR dem Kochen ein kleines Stueck roh probieren** -- bei Bitterkeit sofort entsorgen
- Cucurbitacine werden durch Kochen NICHT zerstoert
- Symptome bei Vergiftung: heftiges Erbrechen, Durchfall, Kolikschmerzen
- **Saatgut:** Nur zertifiziertes Saatgut verwenden. Bei Eigenanbau-Saatgut: Kreuzung mit Zierküerbissen ausschliessen!

### Pflanzentoxizitaet

- Normale Kulturzucchini sind **NICHT giftig** fuer Katzen, Hunde oder Kinder
- Blatthare koennen bei empfindlichen Personen Kontaktdermatitis ausloesen -- Handschuhe empfohlen

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Geerntete Fruechte vor Verzehr gruendlich waschen
- **2 Wochen duengerfreie FLUSHING-Phase** vor Saisonende empfohlen

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Zucchini \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Zucchini (Buschtyp) mit Indoor-Vorkultur ab Mitte April und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 5 Produkten. Starkzehrer, 22 Wochen (April\u2013September).",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["zucchini", "courgette", "cucurbita", "pepo", "starkzehrer", "plagron", "terra", "erde", "outdoor", "gewaechshaus"],
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
  "week_end": 2,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Indoor-Aussaat in Anzuchterde, 22\u201325\u00b0C Substrattemperatur (Heizmatte). Dunkelkeimer, 2\u20133 cm tief. Feine Spr\u00fchung, kein D\u00fcnger. Keimung nach 5\u20138 Tagen.",
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
      "notes": "Nur Wasser. Feine Spr\u00fchung, Substrat gleichm\u00e4\u00dfig feucht halten.",
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
  "week_start": 3,
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Nicht pikieren (empfindliche Wurzeln). Power Roots f\u00f6rdert Wurzelentwicklung. Abh\u00e4rtung beginnt Ende Woche 4.",
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
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
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
  "week_start": 5,
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Volle Dosis Terra Grow (5 ml/L). Extrem schnelles Blattwachstum. Auspflanzen nach Eisheiligen (ca. 15. Mai). Pflanzabstand mind. 80\u2013100 cm. Bei sehr w\u00fcchsigen Pflanzen auf 6\u20137 ml/L steigern.",
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
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
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
  "week_start": 9,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 165,
  "magnesium_ppm": 50,
  "notes": "Umstellung auf Terra Bloom (5 ml/L). Power Roots absetzen. Bestaeubung sicherstellen (Insekten oder Handbestaeubung). Erste Ernte ca. 5\u20136 Wochen nach Pflanzung. BER-Pr\u00e4vention: gleichm\u00e4\u00dfig gie\u00dfen!",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fcte-/Fruchtd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive. Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 2.0,
      "reference_ec_ms": 2.0,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.5}
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
  "week_start": 13,
  "week_end": 20,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 165,
  "magnesium_ppm": 50,
  "notes": "Reduzierter Terra Bloom (4 ml/L). Kein Sugar Royal. Kontinuierliche Ernte alle 2\u20133 Tage bei 15\u201325 cm Fruchtl\u00e4nge. Mehltau-Management: befallene Bl\u00e4tter entfernen, Kaliumbicarbonat 0.5% spr\u00fchen. Bei gro\u00dfen Pflanzen Terra Bloom auf 5 ml/L erh\u00f6hen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Ernte-D\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom. Kein Sugar Royal.",
      "target_ec_ms": 1.8,
      "reference_ec_ms": 1.8,
      "target_ph": 6.2,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 4.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.5}
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
  "week_start": 21,
  "week_end": 22,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Substrat mit klarem Wasser durchsp\u00fclen. Pure Zym f\u00fcr Salzabbau. Letzte Fr\u00fcchte ernten. Pflanzen kompostieren (nur gesunde).",
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
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.5}
    }
  ]
}
```

### 8.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/knowledge/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/knowledge/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Power Roots | `spec/knowledge/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Sugar Royal | `spec/knowledge/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |
| Species: Cucurbita pepo | `spec/knowledge/plants/cucurbita_pepo.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/knowledge/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/knowledge/products/plagron_sugar_royal.md`
6. Zucchini Pflanzensteckbrief: `spec/knowledge/plants/cucurbita_pepo.md`
7. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
8. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
