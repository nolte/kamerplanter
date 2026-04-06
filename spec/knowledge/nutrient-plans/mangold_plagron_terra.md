# Naehrstoffplan: Mangold -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Beta vulgaris subsp. vulgaris (Blattgruppe) (Mittelzehrer, Direktsaat/Vorkultur ab April, kontinuierliche Blatternte)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_*.md, spec/knowledge/products/plagron_power_roots.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/products/plagron_sugar_royal.md, spec/knowledge/plants/beta_vulgaris_subsp_vulgaris.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Mangold -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Mangold (Schnitt-/Stielmangold) mit Vorkultur ab Ende Maerz oder Direktsaat ab Mitte April. Plagron Terra-Linie mit 5 Produkten. Mittelzehrer mit moderatem N- und hohem K-Bedarf, kontinuierliche Blatternte ueber die gesamte Saison. Robuste, dankbare Anfaengerkultur. Zweijaehrig, aber als Einjaehrige kultiviert. 18 Wochen Gesamtdauer (April--August, Ernte bis November). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | mangold, chard, swiss-chard, beta, vulgaris, mittelzehrer, plagron, terra, erde, outdoor, balkon, blattgemuese | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaehrig kultiviert, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

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

**Hinweis:** Alle 2 Tage als Basis -- Mangold braucht gleichmaessige Bodenfeuchte, ist aber genuegsamer als Tomaten oder Zucchini. In GERMINATION (2 Tage) und SEEDLING (2--3 Tage) ueber `watering_schedule_override` angepasst. Gleichmaessige Wasserversorgung ist entscheidend -- Wechsel zwischen Trockenheit und Naesse fuehrt zu Blattverfaerbungen und Schossen. Mulchen hilft enorm.

---

## 2. Phasen-Mapping

Mangold ist eine zweijaehrige Pflanze (Beta vulgaris subsp. vulgaris, Blattgruppe), die als Einjaehrige kultiviert wird. Gleiche Art wie Rote Bete, aber Blattkultur statt Ruebenkultur. Typische Sorten: Bright Lights, Fordhook Giant, Rhubarb Chard. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Mangold-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|---------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Anfang April | Vorkultur Indoor oder Direktsaat ab Mitte April. 10--20 degC. Dunkelkeimer, 2--3 cm tief. Knauelfruchte -- vereinzeln noetig! | false |
| Saemling | SEEDLING | 3--5 | Mitte April--Anfang Mai | Jungpflanze mit Keimblaettern + 4--6 echten Blaettern. Vereinzeln auf 25--30 cm Abstand. Viertel-Dosis Terra Grow. | false |
| Vegetatives Wachstum | VEGETATIVE | 6--10 | Mai--Mitte Juni | Volle Duengung Terra Grow. Kraeftiges Blattwachstum. Erste aeussere Blaetter koennen ab Woche 8 geerntet werden. | false |
| Blatternte (Dauerernte) | HARVEST | 11--16 | Mitte Juni--Ende August | Kontinuierliche Blatternte. Terra Bloom reduziert. Immer 2--3 aeussere Blaetter pro Ernte, Herz stehen lassen. Nachwachsende Blattrosette. | false |
| Saisonende/Spuelung | FLUSHING | 17--18 | September | Kein Duenger, nur Wasser + Pure Zym. Letzte Blaetter ernten. Pflanze kann mit Frostschutz bis November stehen bleiben (Blaetter vertragen leichte Froeste bis -6 degC). | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Bluete/Schossen ist unerwuenscht -- Schosser sofort entfernen)
- **DORMANCY** entfaellt (einjaehrig kultiviert)

**Besonderheit HARVEST = Blatternte:** Bei Mangold ist HARVEST keine terminale Phase im ueblichen Sinne, sondern eine kontinuierliche Erntephase mit nachwachsenden Blaettern. Die Pflanze produziert laufend neue Blaetter aus der Rosette, solange das Herz intakt bleibt und die Naehrstoffversorgung stimmt.

**Kein Zyklus-Neustart:** Mangold wird als Einjaehrige kultiviert. Nach Saisonende (Woche 18, ca. September/Oktober) Pflanzen entfernen und kompostieren. Im 2. Jahr wuerden die Pflanzen schossen. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Amaranthaceae (Mangold, Rote Bete, Spinat) auf gleicher Flaeche!

**Lueckenlos-Pruefung:** 2 + 3 + 5 + 6 + 2 = 18 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne.

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Keimungsspruehung (Spruehflasche/Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Nur Wasser. Substrat gleichmaessig feucht halten. Dunkelkeimer, 2--3 cm tief. Saatgut vor Aussaat 12--24 Stunden in lauwarmem Wasser einweichen (beschleunigt Keimung). Knauelfruchte: 2--4 Keimlinge pro Stelle -- nach Aufgang auf 1 vereinzeln! | `delivery_channels.notes` |
| method_params | drench, 0.02 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Bodennah giessen. | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Ernte

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-ernte | `delivery_channels.channel_id` |
| Label | Ernteduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. K-betont fuer kontinuierliche Blattbildung. | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Optionales Pure Zym fuer Substratpflege. | `delivery_channels.notes` |
| method_params | drench, 0.3 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Mangold

Mangold ist ein Mittelzehrer mit moderatem EC-Bedarf (Steckbrief: 1.0--1.6 mS/cm vegetativ). **In Erdkultur** sind die Dosierungen noch niedriger. Leitungswasser liefert typisch 0.2--0.8 mS/cm. **Stickstoff nicht ueberdosieren** -- zu viel N fuehrt zu Nitrat-Akkumulation in den Blaettern (gesundheitlich bedenklich). Kein PK-Booster noetig.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Ernte (K-betont fuer Blattnachwuchs) |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ (frueh) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (8.5-0-0) | 0.02 | 65 | Vegetativ (optional, moderate Dosis) |

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
| Hinweise | Vorkultur Indoor in Topfplatten oder Direktsaat ab Mitte April (Bodentemperatur >8 degC). Dunkelkeimer, 2--3 cm tief. 10--20 degC (optimal 15 degC). Saatgut 12--24 h einweichen. Knauelfruchte: mehrere Keimlinge pro Stelle -- auf staerksten vereinzeln! Kein Duenger. Keimung nach 10--14 Tagen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage (gleichmaessig feucht) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 3--5)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 5 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). **Vereinzeln** wenn Saemlinge 5 cm hoch sind -- pro Knauel nur die kraeftigste Pflanze stehen lassen (Abstand 25--30 cm in der Reihe, 30 cm Reihenabstand). Entfernte Saemlinge koennen vorsichtig verpflanzt werden. Power Roots foerdert Wurzelentwicklung. Noch kein Pure Zym oder Sugar Royal noetig. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2--3 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.5 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | -- (noch nicht) |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm** ✓

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 6--10)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 6 | `phase_entries.week_start` |
| week_end | 10 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| NPK-Abweichung | Steckbrief-Ideal 2-1-3; Terra Grow liefert 3-1-3. Leicht erhoehter N-Anteil ist fuer Blattkultur akzeptabel, aber Dosierung nicht ueber 4 ml/L steigern (Nitrat-Akkumulation!). | |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Moderate Dosis Terra Grow (4 ml/L) -- Mittelzehrer, nicht ueberdosieren! Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal optional fuer Chlorophyllbildung (nur 0.5 ml/L -- halbe Dosis wegen organischem N!). Power Roots bis Woche 8, dann absetzen. Kraeftiges Blattwachstum. **Erste Blatternte** ab Woche 8--9 moeglich: 2--3 aeussere Blaetter abschneiden, Herz stehen lassen. Mulchen mit Stroh oder Grasschnitt fuer gleichmaessige Bodenfeuchte. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.2  |
| reference_ec_ms | 1.2  |
| target_ph | 6.5 |
| Terra Grow ml/L | 4.0 (moderate Dosis -- Mittelzehrer!) |
| Power Roots ml/L | 1.0 (nur bis Woche 8) |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 0.5 (halbe Dosis, optional) |

**EC-Budget:** 0.32 (TG 4.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.01 (SR 0.5ml) + ~0.4 (Wasser) = **~0.74 mS/cm** ✓

**Hinweis Mittelzehrer:** Die berechnete EC (~0.7 mS/cm) ist bewusst niedriger als bei Starkzehrern (Tomate: ~0.8, Zucchini: ~0.8). Mangold ist genuegsamer und reagiert auf Ueberdosierung mit Nitrat-Akkumulation. **Nicht auf 5 ml/L steigern.**

**Hinweis target_ec_ms:** `target_ec_ms: 1.2` ist ein Messziel fuer die Gesamtloesung im Substrat-Eluat (inkl. Bodenpuffer). Die Duengeadditive liefern nur ~0.34 mS/cm zuzueglich Leitungswasser ~0.4. Bei sehr armen Substraten kann vorsichtig auf 5 ml/L TG erhoeht werden -- aber Nitrat-Monitoring beachten.

### 4.4 HARVEST -- Blatternte / Dauerernte (Woche 11--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 11 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Wechsel auf Terra Bloom (3 ml/L, reduziert) fuer K-betonte Duengung. Kalium foerdert die Blattqualitaet, Zellwandstaerke und den Geschmack. Kein Sugar Royal (N-Reduktion in Erntephase). Pure Zym weiter fuer Substratgesundheit. **Ernteregel:** Maximal 2--3 aeussere Blaetter pro Ernte abschneiden (Messer, bodennah). Herz IMMER stehen lassen -- die Pflanze treibt aus der Rosette nach! Alle 7--10 Tage ernten. Stielmangold: ganzer Stiel mit Blatt ernten. Schnittmangold: Blaetter 3--4 cm ueber dem Boden abschneiden. Bei Schossern: Bluetenstiel sofort entfernen (Energieverschwendung). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-ernte**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.0  |
| reference_ec_ms | 1.0  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 3.0 (reduziert -- Mittelzehrer!) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.30 (TB 3.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.70 mS/cm** ✓

### 4.5 FLUSHING -- Saisonende/Spuelung (Woche 17--18)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 17 | `phase_entries.week_start` |
| week_end | 18 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Letzte Blaetter ernten. Mangold vertraegt leichte Froeste (bis -6 degC) -- mit Frostschutz (Vlies, Stroh) kann die Ernte bis November verlaengert werden. Pflanzen danach kompostieren. Im 2. Jahr wuerden sie schossen -- fuer Saatgutgewinnung eine Pflanze ueberwintern. | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Herbst) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan April--September (Ernte verlaengerbar bis November mit Frostschutz).

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|-----------------|----------|
| April (frueh) | GERMINATION | -- | -- | -- | -- | -- | 0.4 | alle 2d |
| April (spaet) | SEEDLING | 1.5 | -- | 1.0 | -- | -- | 0.5 | alle 2--3d |
| Mai | SEED/VEG | 1.5->4.0 | -- | 1.0 | -->1.0 | -->0.5 | 0.5->0.7 | alle 2d |
| Juni | VEG->HARV | 4.0->-- | -->3.0 | 1.0->-- | 1.0 | 0.5->-- | 0.7->0.7 | alle 2d |
| Juli | HARVEST | -- | 3.0 | -- | 1.0 | -- | 0.7 | alle 2d |
| August | HARVEST | -- | 3.0 | -- | 1.0 | -- | 0.7 | alle 2d |
| September | HARV->FLUSH | -- | 3.0->0 | -- | 1.0 | -- | 0.7->0.4 | 2d->3d |
| Okt--Nov* | -- | -- | -- | -- | -- | -- | -- | natuerlich |

*Optional: Mit Frostschutz (Vlies) Ernte bis November verlaengern, aber ohne Duengung.

```
Monat:       |Apr(f)|Apr(s)|Mai  |Jun  |Jul  |Aug  |Sep  |Okt* |
KA-Phase:    |GERM  |SEED  |S→VEG|V→HAR|HARV |HARV |H→FLU| --  |
Terra Grow:  |---   |##-   |##→##|##→--|---  |---  |---  |---  |
Terra Bloom: |---   |---   |---  |-->##|###  |###  |##→--|---  |
Power Roots: |---   |===   |===  |==→--|---  |---  |---  |---  |
Pure Zym:    |---   |---   |-->==|===  |===  |===  |===  |---  |
Sugar Royal: |---   |---   |-->=-|=- --|---  |---  |---  |---  |

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, ##  = moderate Dosis (4 ml/L TG, 3 ml/L TB)
         =- = halbe Dosis (0.5 ml/L), --> = Start, ->  = Uebergang
         * Okt--Nov: optional mit Frostschutz, ohne Duengung
```

### Jahresverbrauch (geschaetzt)

Bei 5 Mangold-Pflanzen, 0.3--0.5 L Giessloessung pro Duengung, alle 2 Tage:

| Produkt | Formel | Verbrauch/5 Pflanzen/Saison |
|---------|--------|------------------------------|
| Terra Grow | (3 Wo x 2/Wo x 1.5ml + 5 Wo x 3.5/Wo x 4ml) = 79 ml | **~80 ml** |
| Terra Bloom | (6 Wo x 3.5/Wo x 3ml) = 63 ml | **~65 ml** |
| Power Roots | (6 Wo x 3/Wo x 1ml) = 18 ml | **~20 ml** |
| Pure Zym | (12 Wo x 3.5/Wo x 1ml) = 42 ml | **~40 ml** |
| Sugar Royal | (4 Wo x 3.5/Wo x 0.5ml) = 7 ml | **~7 ml** |

**Kosten-Schaetzung:** Mangold ist sehr sparsam im Duengerverbrauch (Mittelzehrer, moderate Dosierungen). Die kleinsten Flaschengroessen (250 ml) reichen fuer viele Saisons. Ideale Einsteigerkultur fuer das Plagron-Terra-System.

---

## 6. Mangold-spezifische Praxis-Hinweise

### Blatternte-Technik

Mangold ist ein "Cut-and-Come-Again"-Gemuese -- die Pflanze waechst nach jeder Ernte nach, solange das Herz intakt bleibt.

**Regeln:**
- **Maximal 2--3 aeussere Blaetter** pro Pflanze und Ernte abschneiden
- **Herz (Vegetationspunkt) IMMER stehen lassen** -- sonst stirbt die Pflanze
- Blaetter bodennah abschneiden (scharfes Messer, kein Reissen)
- **Alle 7--10 Tage** ernten fuer optimalen Nachwuchs
- Junge Blaetter (15--20 cm) sind zarter, grosse Blaetter (30+ cm) haben mehr Ertrag aber groebere Textur
- **Stielmangold:** Ganzer Stiel mit Blatt ernten; Stiel ist die Delikatesse (wie Spargel zubereiten)
- **Schnittmangold:** Blaetter 3--4 cm ueber dem Boden abschneiden, treiben bueschelweise nach

### Schossen verhindern

Mangold ist zweijaehrig und schosst normalerweise erst im 2. Jahr nach Vernalisation. Im 1. Jahr kann Schossen ausgeloest werden durch:
- **Kaelteperioden** (unter 5 degC fuer mehrere Tage) bei bereits grossen Pflanzen
- **Trockenheitsstress**
- **Zu fruehe Aussaat** mit anschliessendem Kaelterueckfall

**Praevention:**
- Nicht vor Mitte April direkt saeen (Bodentemperatur >8 degC)
- Gleichmaessig giessen
- Schosser sofort entfernen (Bluetenstiel abschneiden)

### Oxalsaeure

Mangold-Blaetter enthalten Oxalsaeure (wie Spinat, Rhabarber). In normalen Mengen unbedenklich.

**Hinweise:**
- Kochen reduziert den Oxalsaeuregehalt erheblich (geht ins Kochwasser ueber -- wegschuetten!)
- Personen mit Neigung zu Nierensteinen (Calciumoxalat-Typ) sollten Konsum einschraenken
- **Abwaegung innere/aeussere Blaetter:** Junge innere Blaetter enthalten weniger Oxalsaeure als alte aeussere Blaetter (ca. 300-500 mg/100 g vs. 600-1000 mg/100 g Frischgewicht). Fuer Personen mit erhoehtem Nierensteinrisiko (Calciumoxalat) empfiehlt es sich daher, bei reichlichem Mangold-Konsum bevorzugt junge Innenblaetter zu verwenden -- auch wenn diese aus Nitrat-Sicht etwas hoehere Werte aufweisen. Fuer den normalen Gelegenheitskonsum ist die Unterscheidung unbedeutend.
- Fuer Saeuglinge unter 6 Monaten wegen Nitrat- und Oxalsaeuregehalt nicht geeignet

### Nitrat-Kontrolle

Mangold akkumuliert bei Ueberdosierung von Stickstoff Nitrat in den Blaettern.

**Massnahmen:**
- **Terra Grow maximal 4 ml/L** (nicht 5 ml/L wie bei Starkzehrern!)
- **Sugar Royal nur halbe Dosis** (0.5 ml/L) wegen 8.5% organischem N
- **Kein Sugar Royal in der Erntephase** (nur Terra Bloom als einzige N-Quelle)
- Morgens ernten (Nitratgehalt ist morgens am niedrigsten, da Licht Nitrat ueber Nacht abgebaut hat)
- Aeussere Blaetter bevorzugt ernten (geringerer Nitratgehalt als junge innere Blaetter)

### Substrat

- Tiefgruendige, humose, lockere Erde
- pH 6.0--7.5 (toleriert breiten Bereich)
- Mittlerer Naehrstoffgehalt genuegt (Mittelzehrer!)
- Keine Steine (deformierte Wurzeln)
- Topfkultur gut moeglich: mind. 5--10 L pro 3--5 Pflanzen, Topftiefe mind. 25 cm
- **Balkongeeignet:** Mangold ist eine der besten Blattgemuese-Kulturen fuer Balkon und Terrasse

### Dekorativer Wert

Buntstielige Sorten (Bright Lights, Rainbow, Rhubarb Chard) sind ausgesprochen dekorativ und eignen sich hervorragend als essbare Zierpflanzen in Blumenbeeten, Hochbeeten und Kuebeln.

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Amaranthaceae (Mangold, Rote Bete, Spinat, Zuckerruebe) auf gleicher Flaeche
- **Gute Vorfruechte:** Huelsenfruechte, Kartoffeln, Getreide
- **Gute Nachfruechte:** Schwachzehrer (Feldsalat, Radieschen), Gruenduengung
- **Gute Nachbarn:** Zwiebel, Knoblauch, Buschbohne, Kohlrabi, Kopfsalat
- **Schlechte Nachbarn:** Rote Bete (gleiche Art!), Spinat (gleiche Familie), Kartoffel

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet

**Mangold ist grundsaetzlich NICHT giftig:**

- Fuer Katzen und Hunde in kleinen Mengen unbedenklich (Oxalsaeure in grossen Mengen kann Magen-Darm reizen)
- Fuer Kinder und Erwachsene als Lebensmittel unbedenklich
- **Ausnahme Saeuglinge:** Nicht fuer Saeuglinge unter 6 Monaten (Nitratgehalt kann Methaemoglobinaemie ausloesen)
- **Nierensteine:** Personen mit Calciumoxalat-Neigung sollten Konsum einschraenken
- Roter Saft faerbt Haut und Kleidung (kein Allergen, nur kosmetisch)

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Geerntete Blaetter vor Verzehr gruendlich waschen (Erde und Duengerrueckstaende)
- **2 Wochen duengerfreie FLUSHING-Phase** vor Saisonende empfohlen
- **Nitrat-Hinweis:** Nicht ueberdoesiert duengen! N-Ueberschuss fuehrt zu Nitrat-Akkumulation im essbaren Blattgemuese

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Mangold \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Mangold (Schnitt-/Stielmangold) mit Vorkultur ab Ende M\u00e4rz oder Direktsaat ab Mitte April. Plagron Terra-Linie mit 5 Produkten. Mittelzehrer, 18 Wochen (April\u2013September). Kontinuierliche Blatternte.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["mangold", "chard", "swiss-chard", "beta", "vulgaris", "mittelzehrer", "plagron", "terra", "erde", "outdoor", "balkon", "blattgemuese"],
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
  "notes": "Vorkultur Indoor oder Direktsaat ab Mitte April. Dunkelkeimer, 2\u20133 cm tief. 10\u201320\u00b0C. Saatgut 12\u201324 h einweichen. Knauelfr\u00fcchte: auf st\u00e4rksten Keimling vereinzeln. Keimung nach 10\u201314 Tagen.",
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
      "channel_id": "wasser-keimung",
      "label": "Keimungsbew\u00e4sserung (Spr\u00fchflasche)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur Wasser. Substrat gleichm\u00e4\u00dfig feucht halten.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.02}
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
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Vereinzeln auf 25\u201330 cm Abstand. Power Roots f\u00f6rdert Wurzelentwicklung.",
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
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.5,
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
  "week_start": 6,
  "week_end": 10,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Moderate Dosis Terra Grow (4 ml/L) \u2013 Mittelzehrer, nicht \u00fcberdosieren! Pure Zym + Sugar Royal (halbe Dosis 0.5 ml/L). Power Roots bis W8. Erste Blatternte ab W8\u20139 m\u00f6glich. Mulchen empfohlen. Hinweis: target_ec_ms 1.2 ist ein Messziel f\u00fcr die Gesamtl\u00f6sung im Substrat-Eluat (inkl. Bodenpuffer). Die D\u00fcngeadditive liefern nur ~0.34 mS/cm zzgl. Leitungswasser ~0.4. Bei sehr armen Substraten kann vorsichtig auf 5 ml/L TG erh\u00f6ht werden \u2013 aber Nitrat-Monitoring beachten.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow moderate Dosis + Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen. NICHT auf 5 ml/L steigern (Nitrat!).",
      "target_ec_ms": 1.2,
      "reference_ec_ms": 1.2,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 4.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": true, "_comment": "Nur bis Woche 8"},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 0.5, "optional": true, "_comment": "Halbe Dosis wegen org. N"}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.4}
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
  "week_start": 11,
  "week_end": 16,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom reduziert (3 ml/L). K-betont f\u00fcr Blattqualit\u00e4t. Kein Sugar Royal (N-Reduktion). Kontinuierliche Blatternte: max. 2\u20133 \u00e4u\u00dfere Bl\u00e4tter, Herz stehen lassen. Alle 7\u201310 Tage ernten. Schosser sofort entfernen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-ernte",
      "label": "Ernte-D\u00fcngung K-betont (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom. Kein Sugar Royal.",
      "target_ec_ms": 1.0,
      "reference_ec_ms": 1.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 3.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.4}
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
  "week_start": 17,
  "week_end": 18,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Pure Zym f\u00fcr Salzabbau. Letzte Bl\u00e4tter ernten. Mit Frostschutz (Vlies) Ernte bis November verl\u00e4ngerbar. Pflanzen danach kompostieren.",
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
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
| Species: Beta vulgaris subsp. vulgaris | `spec/knowledge/plants/beta_vulgaris_subsp_vulgaris.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/knowledge/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/knowledge/products/plagron_sugar_royal.md`
6. Beta vulgaris subsp. vulgaris Pflanzensteckbrief: `spec/knowledge/plants/beta_vulgaris_subsp_vulgaris.md`
7. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
8. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
