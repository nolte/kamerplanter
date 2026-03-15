# Naehrstoffplan: Paprika -- Plagron Terra + PK 13-14

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Capsicum annuum (Starkzehrer, Indoor-Vorkultur + Outdoor ab Mai)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal, PK 13-14
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_*.md, spec/ref/products/plagron_power_roots.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_sugar_royal.md, spec/ref/products/plagron_pk_13_14.md, spec/ref/plant-info/capsicum_annuum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Paprika -- Plagron Terra + PK 13-14 | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Paprika (Gemuese-Paprika, Blocktyp) mit Indoor-Vorkultur ab Februar und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 6 Produkten inkl. PK 13-14 Bluetebooster. Klassischer Starkzehrer (Solanaceae) mit sehr langer Kulturzeit (120--180 Tage). Einjaehrige Kultur, kein Zyklus-Neustart. 30 Wochen Gesamtdauer (Februar--September). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | paprika, capsicum, annuum, starkzehrer, plagron, terra, pk-13-14, erde, outdoor, gewaechshaus, solanaceae | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaehrig, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 1 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Taeglich giessen als Sommerbasis -- Paprika sind Starkzehrer mit hohem Wasserbedarf (0.5--1.5 L/Pflanze/Tag bei Hitze). Gleichmaessige Wasserversorgung ist essentiell zur BER-Praevention. In GERMINATION (1 Tag, leichte Spruehung), SEEDLING (2 Tage) und FLUSHING (3 Tage) ueber `watering_schedule_override` angepasst. **Nie ueber die Blaetter giessen** -- Pilzrisiko!

---

## 2. Phasen-Mapping

Paprika ist eine einjaehrige Nutzpflanze in Mitteleuropa (Capsicum annuum). Typische Sorten: California Wonder, Yolo Wonder, Palermo F1. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Paprika-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|---------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--3 | Mitte Februar--Anfang Maerz | Indoor-Aussaat auf Heizmatte, 25--28 degC Substrattemperatur. Kein Duenger. Keimdauer 10--21 Tage (laenger als Tomate!). | false |
| Saemling | SEEDLING | 4--9 | Maerz--Mitte April | Jungpflanze mit Keimblaettern + ersten echten Blaettern. Viertel-Dosis Terra Grow. Pikieren nach 2. Blattpaar. Paprika waechst in der Jugendphase langsam! | false |
| Vegetatives Wachstum | VEGETATIVE | 10--16 | Mitte April--Ende Mai | Volle Duengung Terra Grow. Abhaertung + Auspflanzen nach Eisheiligen (ca. 15. Mai). Stuetzstab setzen. | false |
| Bluete | FLOWERING | 17--22 | Juni--Mitte Juli | Umstellung auf Terra Bloom. Erste Bluetenknospen (Koenigsbluete). PK 13-14 einmalig in Woche 19--20 (peak Fruchtansatz). Koenigsbluete bei Gemuese-Paprika ausbrechen. | false |
| Fruchtreife + Ernte | HARVEST | 23--28 | Mitte Juli--Mitte September | Kontinuierliche Ernte. Terra Bloom reduziert. Regelmaessiges Ernten foerdert Neuansatz. Farbausreifung dauert 2--3 Wochen extra. | false |
| Saisonende/Spuelung | FLUSHING | 29--30 | Mitte--Ende September | Kein Duenger, nur Wasser + Pure Zym. Letzte Fruechte ernten vor erstem Frost. | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (einjaehrige Kultur, keine Ueberwinterung)

**Kein Zyklus-Neustart:** Paprika ist einjaehrig. Nach Saisonende (Woche 30, ca. Oktober) wird die Pflanze entfernt und kompostiert. Im Folgejahr: neue Pflanzen, neuer Durchlauf. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Solanaceae auf gleicher Flaeche!

**Lueckenlos-Pruefung:** 3 + 6 + 7 + 6 + 6 + 2 = 30 Wochen, keine Luecken

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
| Hinweise | Nur Wasser, feine Spruehung. Substrat gleichmaessig feucht halten, nicht durchnaessen. | `delivery_channels.notes` |
| method_params | drench, 0.03 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Nie ueber Blaetter giessen! | `delivery_channels.notes` |
| method_params | drench, 0.3--0.8 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom -> PK 13-14 (nur W19--20) -> Pure Zym -> Sugar Royal -> pH pruefen. PK 13-14 Basisdosis reduzieren auf 70% Terra Bloom! | `delivery_channels.notes` |
| method_params | drench, 0.5--1.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Optionales Pure Zym fuer Substratpflege und Salzabbau. | `delivery_channels.notes` |
| method_params | drench, 0.5 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Paprika

Paprika sind Starkzehrer mit hoher EC-Toleranz (bis 2.5 mS/cm in Hydrokultur). **In Erdkultur** ist die benoetigte EC in der Giessloessung deutlich niedriger, da das Substrat Naehrstoffe puffert und speichert. Leitungswasser liefert typisch 0.2--0.8 mS/cm (regionenabhaengig). In Hartwasserregionen (>0.7 mS/cm) Terra-Bloom-Dosis bei Bedarf auf 4 ml/L reduzieren oder 20--30% Regenwasser/Osmosewasser beimischen. Die Plagron-Dosierungen sind fuer Erdkultur kalibriert.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Bluete |
| PK 13-14 (0-13-14) | 0.25 | 30 | Nur Woche 19--20 (Bluetebooster) |

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
| Hinweise | Indoor-Aussaat in Anzuchterde, Samen 0.5--1 cm tief, Substrattemperatur 25--28 degC (Heizmatte dringend empfohlen -- Paprika ist Waermekeimer!). Feine Spruehung, Substrat gleichmaessig feucht aber nicht nass. Kein Duenger -- Anzuchterde liefert Grundversorgung. Abdeckung mit Klarsichtfolie/Haube fuer hohe Luftfeuchte (80--90%). Keimung nach 10--21 Tagen (deutlich langsamer als Tomate!). Dunkelkeimer. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.03 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.2 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 4--9)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 9 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren in Einzeltoepfe (9 cm) nach 2. echtem Blattpaar (ca. Woche 5--6). Paprika waechst in der Jugendphase sehr langsam -- Geduld! Temperaturen unter 15 degC fuehren zu Wachstumsstopp und violetter Blattverfaerbung (Phosphormangel-Symptom). Kuehlere Nachttemperaturen (16--18 degC) foerdern stockigen Wuchs. Power Roots foerdert fruehe Wurzelentwicklung. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | -- (noch nicht) |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm** ✓

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 10--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 10 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Volle Dosis Terra Grow (5 ml/L). Kraeftiger Stamm- und Blattaufbau. Power Roots weiter fuer Wurzelentwicklung. Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal fuer verbesserte Chlorophyllbildung. **Abhaertung:** Ab Woche 14 taeglich einige Stunden nach draussen stellen (7--10 Tage). **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai) in Freiland/Gewaechshaus, Stuetzstab setzen, Pflanzabstand 40--50 cm. Umtopfen in 12--14 cm Toepfe ca. Woche 11--12. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5 |
| target_ph | 6.0 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 (optional) |

**EC-Budget:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm** ✓

**Hinweis Erdkultur:** Die berechnete EC der Giessloessung (~0.8 mS/cm) liegt unter den hydroponischen Zielwerten (1.4--1.8 mS/cm). Das ist korrekt fuer Erdkultur -- das Substrat speichert und puffert Naehrstoffe.

### 4.4 FLOWERING -- Bluete (Woche 17--22)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 17 | `phase_entries.week_start` |
| week_end | 22 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150--180 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) bei ersten Bluetenknospen. Pure Zym + Sugar Royal weiter. Power Roots absetzen (Abschluss mit Ende VEGETATIVE, Woche 16). **PK 13-14 NUR in Woche 19--20 (0.5 ml/L)** -- einmaliger Boost waehrend peak Fruchtansatz. Danach sofort absetzen! **Koenigsbluete:** Bei Gemuese-Paprika (Blocktyp) die erste Bluete an der Verzweigungsgabel ausbrechen -- foerdert kraeftigeren Wuchs und mehr Fruechte. Bei Cayenne-Sorten: stehen lassen. **Calcium-Hinweis:** Fruchtansatz erhoht Ca-Bedarf. Gleichmaessig giessen! Temperaturen ueber 32 degC und unter 15 degC fuehren zu Bluetenabwurf. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.8 |
| target_ph | 6.0 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |
| PK 13-14 ml/L | 0.5 (NUR Woche 19--20!) |

**EC-Budget (ohne PK):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.92 mS/cm** ✓
**EC-Budget (mit PK, W19--20):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + 0.125 (PK 0.5ml) + ~0.4 (Wasser) = **~1.05 mS/cm** ✓

**Hinweis PK 13-14:** Paprika profitiert wie Tomate vom P/K-Schub fuer den Fruchtansatz. Niedrige Dosis (0.5 ml/L), kurze Anwendung (1--2 Wochen). Bei EC-Anstieg auf >1.5 mS/cm in der Giessloessung PK weglassen.

### 4.5 HARVEST -- Fruchtreife + Ernte (Woche 23--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 23 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| NPK-Abweichung | Terra Bloom liefert NPK 2-2-4; Steckbrief-Ideal fuer Ernte ist 1-2-3. Abweichung ist systembedingt (1-Komponenten-Produkt) und praxistauglich. | |
| Calcium (ppm) | 150--180 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50--60 | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (4 ml/L) waehrend Fruchtreife. Kein Sugar Royal -- organischer Stickstoff (9-0-0) foerdert vegetatives Wachstum und verschlechtert Fruchtqualitaet. Pure Zym weiter fuer Substratgesundheit. **Kein PK 13-14 mehr!** Haupternte-Phase: regelmaessig reife Fruechte ernten (gruen essbar, volle Farbausreifung rot/gelb/orange dauert 2--3 Wochen laenger, ergibt aber hoehere Vitamin-C-Gehalte und besseres Aroma). **Regelmaessig ernten foerdert Neuansatz!** Calcium weiter sicherstellen (BER-Risiko bei Hitze + unregelmaessigem Giessen). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5 |
| target_ph | 6.0 |
| Terra Bloom ml/L | 4.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.40 (TB 4.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.80 mS/cm** ✓

### 4.6 FLUSHING -- Saisonende/Spuelung (Woche 29--30)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 6 | `phase_entries.sequence_order` |
| week_start | 29 | `phase_entries.week_start` |
| week_end | 30 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Salzreste aus Substrat ausspuelen. Letzte Fruechte vor erstem Frost ernten. Pflanzen entfernen und kompostieren. Substrat nicht wiederverwenden fuer Solanaceae (Krankheitsrisiko). | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Pflanze baut ab) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.0 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan Februar--September.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | PK 13-14 ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|----------------|-----------------|----------|
| Feb (spaet) | GERMINATION | -- | -- | -- | -- | -- | -- | 0.4 | Spruehung 1d |
| Maerz | GERM/SEED | -->1.5 | -- | 1.0 | -- | -- | -- | 0.4->0.5 | Sprh.->2d |
| April | SEEDLING | 1.5 | -- | 1.0 | -- | -- | -- | 0.5 | alle 2d |
| Mai | SEED/VEG | 1.5->5.0 | -- | 1.0 | 1.0* | 1.0* | -- | 0.5->0.8 | 2d->1d |
| Juni | VEG->FLOW | 5.0->-- | -->5.0 | 1.0->-- | 1.0 | 1.0 | -- | 0.8->0.9 | taeglich |
| Juli | FLOWERING | -- | 5.0 | -- | 1.0 | 1.0 | 0.5** | 0.9->1.1 | taeglich |
| August | FLOW->HARV | -- | 5.0->4.0 | -- | 1.0 | 1.0->-- | -- | 0.9->0.8 | taeglich |
| September | HARV->FLUSH | -- | 4.0->0 | -- | 1.0 | -- | -- | 0.8->0.4 | taegl.->3d |

*Pure Zym und Sugar Royal ab VEGETATIVE-Phase (ca. Mitte Mai, Woche 10).
**PK 13-14 nur 1--2 Wochen in Juli (Woche 19--20, peak Fruchtansatz).

```
Monat:       |Feb(s)|Mär  |Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |
KA-Phase:    |GERM  |G→SEE|SEED |S→VEG|V→FLO|FLOW |F→HAR|H→FLU|
Terra Grow:  |---   |-->##|##-  |##→==|===  |---  |---  |---  |
Terra Bloom: |---   |---  |---  |---  |-->==|===  |==→##|##→--|
Power Roots: |---   |-->==|===  |===  |==→--|---  |---  |---  |
Pure Zym:    |---   |---  |---  |-->==|===  |===  |===  |===  |
Sugar Royal: |---   |---  |---  |-->==|===  |===  |==→--|---  |
PK 13-14:    |---   |---  |---  |---  |---  |=*=  |---  |---  |

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, =*= = nur 1--2 Wochen in diesem Monat
         --> = Start, ->  = Uebergang
```

### Jahresverbrauch (geschaetzt)

Bei einer Paprikapflanze, 0.5--1.0 L Giessloessung pro Duengung, taeglich im Sommer:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (6 Wo x 3.5/Wo x 1.5ml + 7 Wo x 7/Wo x 5ml) = 277 ml | **~280 ml** |
| Terra Bloom | (6 Wo x 7/Wo x 5ml + 6 Wo x 7/Wo x 4ml) = 378 ml | **~380 ml** |
| Power Roots | (12 Wo x 5/Wo x 1ml) = 60 ml | **~60 ml** |
| Pure Zym | (19 Wo x 6/Wo x 1ml) = 114 ml | **~115 ml** |
| Sugar Royal | (12 Wo x 7/Wo x 1ml) = 84 ml | **~85 ml** |
| PK 13-14 | (1.5 Wo x 7 x 0.5ml) = 5.3 ml | **~5 ml** |

---

## 6. Paprika-spezifische Praxis-Hinweise

### Bluetenendstueckfaeule (Blossom End Rot, BER)

BER tritt bei Paprika aehnlich wie bei Tomate auf, wenngleich seltener.

**Ursachen:**
- **Unregelmaessige Bewaesserung** (Nass-Trocken-Zyklen) -- haeufigste Ursache!
- **Zu hohe EC** (>2.0 mS/cm in Erdkultur) -- osmotischer Stress hemmt Ca-Transport
- **Hohe Temperaturen** + niedrige Luftfeuchte

**Praevention:**
- Taeglich morgens gleichmaessig giessen
- EC unter 2.0 mS/cm halten
- Mulchen reduziert Verdunstung und stabilisiert Bodenfeuchte

### Koenigsbluete

Die Koenigsbluete ist die erste Bluete, die sich an der Verzweigungsgabel (Y-Gabelung) des Haupttriebs bildet.

- **Gemuese-Paprika (Blocktyp):** Koenigsbluete AUSBRECHEN -- die Pflanze investiert dann Energie in Verzweigung und bildet insgesamt mehr und groessere Fruechte
- **Cayenne / Chili:** Koenigsbluete STEHEN LASSEN -- diese Sorten bilden viele kleine Fruechte, die einzelne Koenigsfrucht schadet nicht
- Ausbrechen mit den Fingern, nicht schneiden (Krankheitsuebertragung)

### Ausgeizen

Paprika wird NICHT wie Tomate ausgegeizt! Nur die untersten Seitentriebe bis zur Verzweigungsgabel (ca. 20--25 cm Hoehe) entfernen, um Luftzirkulation am Boden zu verbessern und Spritzwasser-Infektionen zu reduzieren.

### Temperatur-Hinweise

- **Optimal:** 22--28 degC Tagestemperatur
- **Bluetenabwurf:** Ueber 32 degC oder unter 15 degC fuehrt zu Pollensterilitaet und Bluetenabwurf
- **Violette Blaetter:** Unter 15 degC -- Phosphor-Aufnahme eingeschraenkt (kein echter P-Mangel, sondern kaeltebedingt)
- **Paprika braucht WAERME:** Gewaechshaus oder windgeschuetzter, vollsonniger Standort ideal

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Solanaceae (Tomate, Kartoffel, Paprika, Aubergine)
- **Gute Nachbarn:** Basilikum, Tagetes, Moehre, Salat, Schnittlauch
- **Schlechte Nachbarn:** Kartoffel, Fenchel, Kohlrabi

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet (WICHTIG!)

**Capsicum annuum ist GIFTIG fuer Katzen und Hunde (Solanin + Capsaicin):**

- **Blaetter, Staengel und UNREIFE (gruene) Fruechte** enthalten Solanin (Glykoalkaloid)
- **Scharfe Sorten (Cayenne, Chili):** Capsaicin reizt Schleimhaeute bei Haustieren
- **Symptome bei Haustieren:** Magen-Darm-Beschwerden, Uebelkeit, Erbrechen, Durchfall
- **Reife suesse Fruechte (Gemuese-Paprika) sind fuer Menschen UNBEDENKLICH**
- **Kontaktallergen:** Capsaicin bei scharfen Sorten -- Handschuhe tragen!

**Schutzmassnahmen:**
- Haustiere von Paprikapflanzen fernhalten
- Gruenteile und unreife Fruechte nicht verfuettern
- Bei scharfen Sorten: Handschuhe beim Ernten und Verarbeiten

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Geerntete Fruechte vor Verzehr gruendlich waschen
- **2 Wochen duengerfreie FLUSHING-Phase** vor Saisonende empfohlen

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Paprika \u2014 Plagron Terra + PK 13-14",
  "description": "Saisonplan f\u00fcr Paprika (Gem\u00fcse-Paprika) mit Indoor-Vorkultur ab Februar und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 6 Produkten inkl. PK 13-14 Bl\u00fctebooster. Starkzehrer (Solanaceae), 30 Wochen (Februar\u2013September).",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["paprika", "capsicum", "annuum", "starkzehrer", "plagron", "terra", "pk-13-14", "erde", "outdoor", "gewaechshaus", "solanaceae"],
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
  "notes": "Indoor-Aussaat in Anzuchterde, 25\u201328\u00b0C Substrattemperatur (Heizmatte dringend empfohlen). Feine Spr\u00fchung, kein D\u00fcnger. Keimung nach 10\u201321 Tagen. Dunkelkeimer.",
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
  "week_end": 9,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren nach 2. Blattpaar. Paprika w\u00e4chst langsam \u2013 Geduld! K\u00fchlere Nachttemperaturen (16\u201318\u00b0C) f\u00f6rdern st\u00f6ckigen Wuchs. Power Roots f\u00f6rdert Wurzelentwicklung.",
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
      "target_ph": 6.0,
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
  "week_start": 10,
  "week_end": 16,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Volle Dosis Terra Grow (5 ml/L). Kr\u00e4ftiger Stamm- und Blattaufbau. Abh\u00e4rtung ab Woche 14. Auspflanzen nach Eisheiligen (ca. 15. Mai), St\u00fctzstab setzen, Pflanzabstand 40\u201350 cm.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + alle Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.8}
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
  "week_start": 17,
  "week_end": 22,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 165,
  "magnesium_ppm": 50,
  "notes": "Umstellung auf Terra Bloom (5 ml/L). Power Roots absetzen. PK 13-14 (0.5 ml/L) NUR in Woche 19\u201320 als Fruchtansatz-Boost. K\u00f6nigsbl\u00fcte bei Gem\u00fcsepaprika ausbrechen. Calcium sicherstellen. Bl\u00fctenabwurf bei >32\u00b0C oder <15\u00b0C.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive + PK 13-14 (nur W19\u201320!). Reihenfolge: Terra Bloom \u2192 PK 13-14 \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.8,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true},
        {"fertilizer_key": "<pk_13_14_key>", "ml_per_liter": 0.5, "optional": true, "_comment": "NUR Woche 19-20, danach absetzen!"}
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
  "week_start": 23,
  "week_end": 28,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 165,
  "magnesium_ppm": 55,
  "notes": "Reduzierter Terra Bloom (4 ml/L). Kein Sugar Royal, kein PK 13-14. Regelm\u00e4\u00dfig ernten f\u00f6rdert Neuansatz. Gr\u00fcne Fr\u00fcchte essbar, volle Farbausreifung (rot/gelb) dauert 2\u20133 Wochen l\u00e4nger, ergibt h\u00f6heren Vitamin-C-Gehalt. Calcium sicherstellen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Ernte-D\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom. Kein Sugar Royal, kein PK 13-14.",
      "target_ec_ms": 1.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 4.0, "optional": false},
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
  "week_start": 29,
  "week_end": 30,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Substrat mit klarem Wasser durchsp\u00fclen. Pure Zym f\u00fcr Salzabbau. Letzte Fr\u00fcchte vor erstem Frost ernten. Pflanzen kompostieren.",
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
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
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
| Fertilizer: PK 13-14 | `spec/ref/products/plagron_pk_13_14.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |
| Species: Capsicum annuum | `spec/ref/plant-info/capsicum_annuum.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/ref/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/ref/products/plagron_sugar_royal.md`
6. Plagron PK 13-14 Produktdaten: `spec/ref/products/plagron_pk_13_14.md`
7. Paprika Pflanzensteckbrief: `spec/ref/plant-info/capsicum_annuum.md`
8. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
9. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
