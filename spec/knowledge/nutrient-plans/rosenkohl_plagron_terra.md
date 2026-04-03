# Naehrstoffplan: Rosenkohl -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Brassica oleracea var. gemmifera (Starkzehrer, Indoor-Vorkultur + Outdoor ab Mai)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_*.md, spec/knowledge/products/plagron_power_roots.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/products/plagron_sugar_royal.md, spec/knowledge/plants/brassica_oleracea_var_gemmifera.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Rosenkohl -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Rosenkohl mit Indoor-Vorkultur ab Maerz und Freilandkultur ab Mai. Plagron Terra-Linie mit 5 Produkten (kein PK 13-14 -- Rosenkohl wird vor Bluete geerntet). Klassischer Starkzehrer mit sehr langer Kulturdauer (30 Wochen). N-Duengung ab August stoppen fuer kompakte Roeschen. Frost verbessert Geschmack. Einjaehrige Kultur, kein Zyklus-Neustart. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | rosenkohl, brussels-sprouts, brassica, oleracea, gemmifera, starkzehrer, plagron, terra, erde, outdoor | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaehrig, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

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

**Hinweis:** Rosenkohl braucht gleichmaessige Wasserversorgung, vertraegt aber keine Staunaesse. Alle 2 Tage als Basis -- bei Hitze im Sommer auf taeglich erhoehen (ueber `watering_schedule_override` in VEGETATIVE). In GERMINATION (1 Tag, leichte Spruehung), SEEDLING (3 Tage) und FLUSHING (4 Tage) angepasst. **Bodenbewaaesserung** -- Kohlgewaechse nie ueber die Blaetter giessen (Pilzrisiko, Kohlhernie).

---

## 2. Phasen-Mapping

Rosenkohl ist eine einjaehrige Nutzpflanze in Mitteleuropa mit sehr langer Kulturdauer (165--200 Tage). Typische Sorten: Groninger, Hilds Ideal, Long Island Improved. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Rosenkohl-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-----------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Anfang Maerz | Indoor-Aussaat, 15--20 degC. Dunkelkeimer. Kein Duenger. | false |
| Saemling | SEEDLING | 3--8 | Mitte Maerz--Mitte April | Jungpflanze bis 4--6 echte Blaetter. Viertel-Dosis Terra Grow. Pikieren nach 2. Blattpaar. | false |
| Vegetatives Wachstum | VEGETATIVE | 9--22 | Mitte April--Ende August | Volle Duengung. Stammaufbau, Blattbildung, Roeschenansatz. Auspflanzen nach Eisheiligen. **N-STOPP ab W20 (August)!** | false |
| Roeschenreife + Ernte | HARVEST | 23--28 | September--Mitte Oktober | Roeschen reifen von unten nach oben. Frost verbessert Geschmack. Reduzierte Duengung nur Terra Bloom. | false |
| Saisonende/Spuelung | FLUSHING | 29--30 | Ende Oktober--November | Kein Duenger. Letzte Roeschen ernten. Strunk kompostieren. | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Rosenkohl wird VOR der Bluete geerntet -- Roeschen SIND die Knospen)
- **DORMANCY** entfaellt (einjaehrige Kultur)

**Kein Zyklus-Neustart:** Rosenkohl ist einjaehrig. Nach Saisonende (Woche 30, ca. November) Strunk entfernen und kompostieren. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Brassicaceae auf gleicher Flaeche (Kohlhernie-Praevention)!

**Lueckenlos-Pruefung:** 2 + 6 + 14 + 6 + 2 = 30 Wochen, keine Luecken

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
| Hinweise | Nur Wasser, feine Spruehung. Substrat gleichmaessig feucht halten, nicht durchnaessen. Dunkelkeimer -- Samen 1--2 cm tief abdecken. | `delivery_channels.notes` |
| method_params | drench, 0.03 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Bodenbewaaesserung, nie ueber Blaetter! | `delivery_channels.notes` |
| method_params | drench, 0.5--1.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Reife

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-reife | `delivery_channels.channel_id` |
| Label | Reife-Duengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. Kein Sugar Royal, kein N-betontes Produkt. | `delivery_channels.notes` |
| method_params | drench, 1.0--1.5 L pro Pflanze | `delivery_channels.method_params` |

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

### EC-Budget Plagron-Produkte fuer Rosenkohl

Rosenkohl ist ein Starkzehrer mit moderater EC-Toleranz (bis 2.0 mS/cm in Erdkultur). **Kein PK 13-14** -- Rosenkohl wird vor der Bluete geerntet, ein Bluetebooster ist nicht sinnvoll. Leitungswasser liefert typisch 0.2--0.8 mS/cm. **pH-Zielwert 6.5** durchgehend -- Brassicaceae brauchen leicht alkalisches Milieu zur Kohlhernie-Praevention (Plasmodiophora brassicae gedeiht bei pH <6.5).

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ (bis W20) |
| Terra Bloom (2-2-4) | 0.10 | 20 | Vegetativ (ab W20 N-Stopp), Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ (bis W20, dann absetzen!) |

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
| Hinweise | Indoor-Aussaat in Anzuchterde, 15--20 degC (Rosenkohl keimt kuehler als Tomaten). **Dunkelkeimer:** Samen 1--2 cm tief abdecken. Substrat gleichmaessig feucht, nicht nass. Kein Duenger -- Anzuchterde liefert Grundversorgung. Keimung nach 5--8 Tagen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.03 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser)

### 4.2 SEEDLING -- Saemling (Woche 3--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren in Einzeltoepfe (8--10 cm) nach 2. echtem Blattpaar (ca. Woche 4--5). Rosenkohl waechst langsamer als Tomaten -- laengere Saemlings-Phase. Power Roots foerdert fruehe Wurzelentwicklung. Temperatur 12--18 degC (kuehler als Tomate!). | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.5 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | -- (noch nicht) |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm**

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 9--22)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 22 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Volle Dosis Terra Grow (5 ml/L). Kraeftiger Stamm- und Blattaufbau. Power Roots weiter fuer Wurzelentwicklung. Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal fuer Aminosaeuren und Chlorophyll. **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai) ins Freiland, 60x60 cm Pflanzabstand. Tief pflanzen (bis zu den Keimblaettern). **Koepfen:** In Woche 18--20 (August) Triebspitze entfernen -- foerdert kompakte Roeschenbildung statt Laengenwachstum. **N-STOPP ab W20 (ca. Mitte August):** Terra Grow und Sugar Royal absetzen, Umstellung auf Terra Bloom. Zu viel N fuehrt zu lockeren, bitteren Roeschen. Ab W20 nur noch Terra Bloom (3 ml/L) + Pure Zym. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (Sommer, hoher Wasserbedarf grosser Pflanzen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum (W9--W19)**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.5 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 (optional) |

**EC-Budget (W9--W19):** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm**

**Delivery Channel: naehrloesung-reife (W20--W22, nach N-Stopp)**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.0  |
| reference_ec_ms | 1.0  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 3.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget (W20--W22):** 0.30 (TB 3.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm**

**Hinweis N-Stopp:** Der Wechsel von Terra Grow (3-1-3, N-betont) auf Terra Bloom (2-2-4, K-betont) ab Woche 20 ist der wichtigste Schritt im Rosenkohl-Anbau. Terra Bloom liefert weiterhin etwas N (2%), aber das K:N-Verhaeltnis verschiebt sich zugunsten von Kalium -- genau richtig fuer die Roeschenbildung. Sugar Royal (9-0-0) wird ebenfalls abgesetzt, da reiner organischer N.

### 4.4 HARVEST -- Roeschenreife + Ernte (Woche 23--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 23 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (3 ml/L). Roeschen reifen von unten nach oben am Stamm. Ernten, wenn Roeschen 2--3 cm Durchmesser haben und fest geschlossen sind. **Frost verbessert Geschmack:** Staerke wird in Zucker umgewandelt (-2 bis -5 degC ideal). Rosenkohl vertraegt bis -15 degC. Untere Blaetter sukzessive entfernen, sobald die Roeschen darueber fest sind (bessere Luftzirkulation). Kein Sugar Royal, kein Power Roots. Pure Zym weiter fuer Substratgesundheit. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-reife**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.0  |
| reference_ec_ms | 1.0  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 3.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.30 (TB 3.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm**

**Hinweis Ernte:** Rosenkohl kann ueber Wochen sukzessive geerntet werden -- immer von unten nach oben. Die Roeschen am Stamm belassen, bis sie gebraucht werden. Im Kuehlschrank 2--3 Wochen haltbar.

### 4.5 FLUSHING -- Saisonende/Spuelung (Woche 29--30)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 29 | `phase_entries.week_start` |
| week_end | 30 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Letzte Roeschen ernten. Bei starkem Frost (-10 degC und kaelter) ganze Pflanze ernten -- Roeschen am Stamm im kuehlen Keller 2--3 Wochen haltbar. Strunk kompostieren. | `phase_entries.notes` |
| Giessplan-Override | Intervall 4 Tage (reduziert, Saisonende) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm**

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan Maerz--November.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|-----------------|----------|
| Maerz (frueh) | GERMINATION | -- | -- | -- | -- | -- | 0.4 | Spruehung 1d |
| Maerz (spaet) | SEEDLING | 1.5 | -- | 1.0 | -- | -- | 0.5 | alle 3d |
| April | SEEDLING/VEG | 1.5->5.0 | -- | 1.0 | 1.0* | 1.0* | 0.5->0.8 | 3d->2d |
| Mai | VEGETATIVE | 5.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | alle 2d->1d |
| Juni | VEGETATIVE | 5.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | taeglich |
| Juli | VEGETATIVE | 5.0 | -- | 1.0 | 1.0 | 1.0 | 0.8 | taeglich |
| August | VEG (N-Stopp) | 5.0->-- | -->3.0 | 1.0->-- | 1.0 | 1.0->-- | 0.8->0.7 | taeglich |
| September | HARVEST | -- | 3.0 | -- | 1.0 | -- | 0.7 | alle 2d |
| Oktober | HARVEST | -- | 3.0 | -- | 1.0 | -- | 0.7 | alle 2d |
| November | FLUSHING | -- | -- | -- | 1.0 | -- | 0.4 | alle 4d |

*Pure Zym und Sugar Royal ab VEGETATIVE-Phase (ca. Mitte April, Woche 9). In der ersten April-Haelfte (SEEDLING) noch nicht einsetzen.

```
Monat:       |Mär(f)|Mär(s)|Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |Okt  |Nov|
KA-Phase:    |GERM  |SEED  |S->VG|VEG  |VEG  |VEG  |V(NS)|HARV |HARV |FLU|
Terra Grow:  |---   |##-   |##→==|===  |===  |===  |==→--|---  |---  |---|
Terra Bloom: |---   |---   |---  |---  |---  |---  |-->##|###  |###  |---|
Power Roots: |---   |===   |===  |===  |===  |===  |==→--|---  |---  |---|
Pure Zym:    |---   |---   |-->==|===  |===  |===  |===  |===  |===  |===|
Sugar Royal: |---   |---   |-->==|===  |===  |===  |==→--|---  |---  |---|

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, --> = Start, ->  = Uebergang
         NS = N-Stopp (Umstellung auf Terra Bloom)
```

### Jahresverbrauch (geschaetzt)

Bei einer Rosenkohlpflanze, 0.5--1.5 L Giessloessung pro Duengung:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (6 Wo x 2/Wo x 1.5ml + 11 Wo x 5/Wo x 5ml) = 293 ml | **~290 ml** |
| Terra Bloom | (3 Wo x 5/Wo x 3ml + 6 Wo x 3.5/Wo x 3ml) = 108 ml | **~110 ml** |
| Power Roots | (14 Wo x 4/Wo x 1ml) = 56 ml | **~55 ml** |
| Pure Zym | (20 Wo x 4/Wo x 1ml) = 80 ml | **~80 ml** |
| Sugar Royal | (11 Wo x 5/Wo x 1ml) = 55 ml | **~55 ml** |

**Kosten-Schaetzung:** Rosenkohl verbraucht aehnlich viel Terra Grow wie Tomaten (lange VEGETATIVE-Phase), aber deutlich weniger Terra Bloom (spaeter Einsatz, niedrigere Dosis). Eine 1L-Flasche Terra Grow reicht fuer ca. 3 Pflanzen-Saisons.

---

## 6. Rosenkohl-spezifische Praxis-Hinweise

### Kohlhernie (Plasmodiophora brassicae)

Die wichtigste Krankheit bei allen Brassicaceae. Bodenpilz, der die Wurzeln deformiert (keulenfoermige Verdickungen) und die Naehrstoffaufnahme blockiert.

**Praevention:**
- **pH ueber 6.5 halten** -- der Erreger gedeiht bei niedrigem pH
- **Fruchtfolge einhalten:** 3--4 Jahre KEINE Brassicaceae auf gleicher Flaeche
- **Kalken:** Bei pH <6.5 Algenkalk einarbeiten (100--200 g/m2)
- **Gute Drainage** -- Staunaesse foerdert den Pilz
- **Resistente Sorten** bevorzugen (z.B. Crispus F1)
- **Kreuzbluetler-Beikraeuter** entfernen (Hirtentaeschel, Senf -- sind Wirtspflanzen!)

**Wenn Kohlhernie auftritt:**
1. Befallene Pflanzen SOFORT entfernen (MIT Wurzeln!)
2. NICHT kompostieren -- Sporen ueberleben 15--20 Jahre im Boden
3. Beet fuer 7+ Jahre NICHT mit Brassicaceae bepflanzen
4. Alternativ: Hochbeet mit frischem Substrat verwenden

### Koepfen (Pinzieren)

**Warum:** Rosenkohl bildet Roeschen in den Blattachseln am Stamm. Ohne Koepfen waechst die Pflanze weiter in die Hoehe und bildet kleine, lockere Roeschen. Durch Entfernen der Triebspitze wird die Energie in die vorhandenen Roeschen umgeleitet.

**Wie:**
- **Zeitpunkt:** Mitte bis Ende August (Woche 18--20), wenn die untersten Roeschen ca. 1 cm Durchmesser haben
- **Methode:** Triebspitze (oberste 5 cm) mit scharfem Messer abschneiden
- **NICHT zu frueh koepfen** -- die Pflanze braucht genuegend Blaetter fuer Photosynthese
- **NICHT zu spaet koepfen** -- nach September hat es kaum noch Effekt

### N-Stopp (August)

**Warum:** Zu viel Stickstoff ab August fuehrt zu:
- Lockeren, offenen Roeschen (statt kompakt und fest)
- Bitterem Geschmack
- Erhoehter Anfaelligkeit fuer Frost und Krankheiten
- Verzoegerter Reife

**Umsetzung im Plan:**
- Ab Woche 20 (ca. Mitte August): Terra Grow (3-1-3) absetzen
- Sugar Royal (9-0-0) ebenfalls absetzen (reiner organischer N!)
- Umstellung auf Terra Bloom (2-2-4) -- liefert weniger N, mehr K
- K-Betonung foerdert Frosthaerte und kompakte Roeschen

### Frostvertraeglichkeit

Rosenkohl ist **sehr winterhart** (bis -15 degC):
- **Frost verbessert den Geschmack:** Bei Temperaturen unter 0 degC wird Staerke in Zucker umgewandelt (Kryoprotektion)
- **Ideale Ernte:** Nach den ersten Froesten (ab November)
- **Nicht bei strengem Frost ernten:** Bei <-10 degC die Roeschen noch am Stamm belassen (Auftau-Schaden bei direkter Ernte)
- **Schneeschutz:** Bei Nassschnee koennen schwere Pflanzen umkippen -- Stuetzpfahl empfehlenswert

### Substrat

- Schwerer, naehrstoffreicher Lehmboden ideal (haelt Naehrstoffe und Wasser)
- pH 6.2--6.8, **ideal 6.5** (Kohlhernie-Praevention)
- Im Freiland: 60x60 cm Pflanzabstand, 30 cm tiefes Pflanzloch
- **Tief pflanzen** (bis zu den Keimblaettern) -- stabilisiert die spaeter sehr hohe Pflanze (60--90 cm)
- Kompost und Hornspane (80--120 g/m2) bei der Pflanzung einarbeiten
- **Anhaeuefeln** ab Juli fuer Standfestigkeit

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Brassicaceae (Kohl, Brokkoli, Blumenkohl, Kohlrabi, Radieschen, Rettich, Ruebsen) auf gleicher Flaeche
- **Gute Vorfruechte:** Huelsenfruechte (N-Fixierung), Kartoffeln (Bodenlockerung)
- **Gute Nachfruechte:** Schwachzehrer (Salat, Spinat, Feldsalat)
- **Schlechte Nachbarn:** Andere Brassicaceae (gemeinsame Krankheiten!), Erdbeeren
- **Gute Nachbarn:** Sellerie, Spinat, Rote Bete, Tagetes (Nematoden-Abwehr)

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet

**Brassica oleracea var. gemmifera ist NICHT GIFTIG:**

- Rosenkohl und alle Kohlgewaechse sind fuer Menschen und Haustiere unbedenklich
- **Senfoel-Glykoside (Glucosinolate):** Gesundheitsfoerdernd in normalen Mengen (krebspraeventiv)
- **Bei Schilddruesenproblemen:** Grosse Mengen roher Kohlgewaechse koennen Jodaufnahme hemmen -- Kochen reduziert den Effekt
- **Blaehungen:** Rosenkohl enthaelt Raffinose -- bei empfindlichen Personen kann es zu Verdauungsbeschwerden kommen

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Geerntete Roeschen vor Verzehr gruendlich waschen (Duengerrueckstaende moeglich)
- **2 Wochen duengerfreie FLUSHING-Phase** vor Saisonende empfohlen

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Rosenkohl \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Rosenkohl mit Indoor-Vorkultur ab M\u00e4rz und Freilandkultur ab Mai. Plagron Terra-Linie mit 5 Produkten (kein PK 13-14). Starkzehrer mit sehr langer Kulturdauer, 30 Wochen (M\u00e4rz\u2013November). N-Stopp ab August f\u00fcr kompakte R\u00f6schen.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["rosenkohl", "brussels-sprouts", "brassica", "oleracea", "gemmifera", "starkzehrer", "plagron", "terra", "erde", "outdoor"],
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

### 8.2 NutrientPlanPhaseEntry (5 Eintraege)

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
  "notes": "Indoor-Aussaat in Anzuchterde, 15\u201320\u00b0C. Dunkelkeimer: Samen 1\u20132 cm tief. Kein D\u00fcnger. Keimung nach 5\u20138 Tagen.",
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
      "notes": "Nur Wasser. Feine Spr\u00fchung, Substrat gleichm\u00e4\u00dfig feucht halten. Dunkelkeimer \u2013 abdecken!",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
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
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren nach 2. Blattpaar. K\u00fchlere Temperaturen (12\u201318\u00b0C). Power Roots f\u00f6rdert Wurzelentwicklung.",
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
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung S\u00e4mling (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis + Power Roots",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.5,
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
  "week_start": 9,
  "week_end": 22,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Volle Dosis Terra Grow (5 ml/L) bis W19. Auspflanzen nach Eisheiligen (60\u00d760 cm). K\u00f6pfen W18\u201320 (Triebspitze entfernen). N-STOPP ab W20: Terra Grow + Sugar Royal absetzen, Umstellung auf Terra Bloom (3 ml/L). Zu viel N \u2192 lockere, bittere R\u00f6schen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + alle Additive (W9\u2013W19). Ab W20 N-Stopp: Wechsel auf naehrloesung-reife!",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 1.0}
    },
    {
      "channel_id": "naehrloesung-reife",
      "label": "N-Stopp-D\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Ab W20 (N-Stopp): nur Terra Bloom + Pure Zym. Kein Terra Grow, kein Sugar Royal!",
      "target_ec_ms": 1.0,
      "reference_ec_ms": 1.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
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
  "sequence_order": 4,
  "week_start": 23,
  "week_end": 28,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Reduzierter Terra Bloom (3 ml/L). R\u00f6schen reifen von unten nach oben. Frost verbessert Geschmack (St\u00e4rke \u2192 Zucker). Ernte bei 2\u20133 cm Durchmesser, fest geschlossen. Untere Bl\u00e4tter sukzessive entfernen. Rosenkohl vertr\u00e4gt bis -15\u00b0C.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-reife",
      "label": "Ernte-D\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur Terra Bloom + Pure Zym. Kein N-betontes Produkt.",
      "target_ec_ms": 1.0,
      "reference_ec_ms": 1.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
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
  "sequence_order": 5,
  "week_start": 29,
  "week_end": 30,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Letzte R\u00f6schen ernten. Bei starkem Frost (<-10\u00b0C) ganze Pflanze ernten \u2013 R\u00f6schen am Stamm im Keller 2\u20133 Wochen haltbar. Strunk kompostieren.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 4,
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
      "target_ph": 6.5,
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
| Fertilizer: Terra Grow | `spec/knowledge/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/knowledge/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Power Roots | `spec/knowledge/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Sugar Royal | `spec/knowledge/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |
| Species: Brassica oleracea var. gemmifera | `spec/knowledge/plants/brassica_oleracea_var_gemmifera.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/knowledge/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/knowledge/products/plagron_sugar_royal.md`
6. Rosenkohl Pflanzensteckbrief: `spec/knowledge/plants/brassica_oleracea_var_gemmifera.md`
7. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
8. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
