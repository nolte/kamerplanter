# Naehrstoffplan: Gurke -- Plagron Terra + PK 13-14

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Cucumis sativus (Starkzehrer, Indoor-Vorkultur + Gewaechshaus/Freiland ab Mai)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal, PK 13-14
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_*.md, spec/ref/products/plagron_power_roots.md, spec/ref/products/plagron_pure_zym.md, spec/ref/products/plagron_sugar_royal.md, spec/ref/products/plagron_pk_13_14.md, spec/ref/plant-info/cucumis_sativus.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Gurke -- Plagron Terra + PK 13-14 | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Salatgurken und Einlegegurken mit Indoor-Vorkultur ab April und Gewaechshaus-/Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 6 Produkten inkl. PK 13-14 Fruchtbooster. Klassischer Starkzehrer mit extrem hohem Wasser- und Kaliumbedarf. Einjaehrige Kultur, kein Zyklus-Neustart. 22 Wochen Gesamtdauer (April--September). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | gurke, cucumber, cucumis, sativus, starkzehrer, plagron, terra, pk-13-14, erde, gewaechshaus, outdoor | `nutrient_plans.tags` |
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

**Hinweis:** Taeglich giessen als Basis -- Gurken bestehen zu 95% aus Wasser und haben einen enormen Wasserbedarf. In der Fruchtphase bei Hitze ggf. 2x taeglich giessen. Gleichmaessige Wasserversorgung ist absolut kritisch -- Trockenstress fuehrt sofort zu bitteren, missgeformten Fruechten. **Giesswasser auf mindestens 18 degC temperieren** -- Gurken reagieren empfindlich auf kaltes Wasser! **Nie ueber die Blaetter giessen** -- Mehltau-Risiko! In GERMINATION (1 Tag, leichte Spruehung), SEEDLING (2 Tage) und FLUSHING (3 Tage) ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Gurke ist eine einjaehrige Nutzpflanze in Mitteleuropa (Cucumis sativus). Typische Sorten: Marketmore 76, Picolino F1 (Gewaechshaus), Vorgebirgstraube (Einlegegurke). Gurken wachsen extrem schnell -- von Aussaat bis Ernte vergehen nur 50--70 Tage. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Gurken-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|--------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1 | Anfang April | Indoor-Aussaat auf Heizmatte, 25--30 degC Substrattemperatur. Kein Duenger. Dunkelkeimer, 2--3 cm tief. | false |
| Saemling | SEEDLING | 2--4 | Mitte April | Jungpflanze mit Keimblaettern + ersten echten Blaettern. Viertel-Dosis Terra Grow. NICHT pikieren -- empfindliche Wurzeln! | false |
| Vegetatives Wachstum | VEGETATIVE | 5--8 | Mai | Volle Duengung Terra Grow. Kraeftiger Blatt- und Rankenaufbau. Auspflanzen nach Eisheiligen (ca. 15. Mai). Rankhilfe aufstellen. | false |
| Bluete + Fruchtansatz | FLOWERING | 9--12 | Juni | Umstellung auf Terra Bloom. Erste Bluetenknospen, Fruchtansatz beginnt. PK 13-14 einmalig in Woche 10--11 (peak Fruchtansatz). | false |
| Dauerertrag + Ernte | HARVEST | 13--20 | Juli--August | Kontinuierliche Ernte alle 1--2 Tage. Terra Bloom reduziert. REGELMAESSIG ERNTEN -- ueberreife Gurken hemmen Neuansatz! | false |
| Saisonende/Spuelung | FLUSHING | 21--22 | September | Kein Duenger, nur Wasser + Pure Zym. Letzte Fruechte ernten. Pflanzen entfernen. | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (einjaehrige Kultur, keine Ueberwinterung)

**Kein Zyklus-Neustart:** Gurke ist einjaehrig. Nach Saisonende (Woche 22, ca. September) wird die Pflanze entfernt und kompostiert. Im Folgejahr: neue Pflanzen, neuer Durchlauf. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Cucurbitaceae auf gleicher Flaeche!

**Lueckenlos-Pruefung:** 1 + 3 + 4 + 4 + 8 + 2 = 22 Wochen, keine Luecken

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
| Hinweise | Nur warmes Wasser (18--24 degC), feine Spruehung. Substrat gleichmaessig feucht halten, nicht durchnaessen. | `delivery_channels.notes` |
| method_params | drench, 0.03 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Giesswasser auf 18--24 degC temperieren! Nie ueber Blaetter giessen! | `delivery_channels.notes` |
| method_params | drench, 0.5--1.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom -> PK 13-14 (nur W10--11) -> Pure Zym -> Sugar Royal -> pH pruefen. PK 13-14 Basisdosis reduzieren auf 70% Terra Bloom! | `delivery_channels.notes` |
| method_params | drench, 1.0--2.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Optionales Pure Zym fuer Substratpflege und Salzabbau. Warmes Wasser verwenden (18--24 degC). | `delivery_channels.notes` |
| method_params | drench, 1.0 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Gurken

Gurken sind Starkzehrer mit hoher EC-Toleranz (bis 2.5 mS/cm in Hydrokultur). **In Erdkultur** ist die benoetigte EC in der Giessloessung deutlich niedriger, da das Substrat Naehrstoffe puffert und speichert. Leitungswasser liefert typisch 0.2--0.8 mS/cm (regionenabhaengig). In Hartwasserregionen (>0.7 mS/cm) Terra-Bloom-Dosis bei Bedarf auf 4 ml/L reduzieren oder 20--30% Regenwasser/Osmosewasser beimischen. EC des lokalen Leitungswassers beim Wasserversorger erfragen oder mit EC-Geraet messen. Die Plagron-Dosierungen sind fuer Erdkultur kalibriert.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Bluete |
| PK 13-14 (0-13-14) | 0.25 | 30 | Nur Woche 10--11 (Fruchtbooster) |

### 4.1 GERMINATION -- Keimung (Woche 1)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 1 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Indoor-Aussaat in Anzuchterde, Samen 2--3 cm tief (Dunkelkeimer), Substrattemperatur 25--30 degC (Heizmatte empfohlen). Feine Spruehung mit warmem Wasser, Substrat gleichmaessig feucht aber nicht nass. Kein Duenger -- Anzuchterde liefert Grundversorgung. Abdeckung mit Klarsichtfolie/Haube fuer hohe Luftfeuchte (80--90%). Keimung nach 3--7 Tagen. Samen NIE unter 15 degC saeen -- faulen leicht in kalter, nasser Erde! Einzeln in 8--10 cm Toepfe saeen (Gurken vertragen kein Pikieren). | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.03 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.2 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) -- OK

### 4.2 SEEDLING -- Saemling (Woche 2--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 2 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Gurken wachsen schnell -- EC zuegig steigern (Starkzehrer!). NICHT pikieren -- empfindliche Wurzeln! Direkt in Einzeltoepfe saeen. Kuehlere Nachttemperaturen (18 degC) foerdern kompakten Wuchs. Power Roots foerdert fruehe Wurzelentwicklung. Noch kein Pure Zym oder Sugar Royal noetig. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | -- (noch nicht) |
| Sugar Royal ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm** -- OK

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
| Hinweise | Volle Dosis Terra Grow (5 ml/L). Kraeftiger Blatt-, Ranken- und Wurzelaufbau. Power Roots weiter fuer Wurzelentwicklung. Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal fuer verbesserte Chlorophyllbildung. **Abhaertung:** Ab Woche 7 taeglich einige Stunden nach draussen stellen (7--10 Tage). **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai) in Gewaechshaus/Freiland. Pflanzabstand 60--100 cm. Rankhilfe (Gitter, Schnuere, Spalier) aufstellen. Pflanzloch mit Kompost anreichern. Mulch ausbringen (5--10 cm Stroh) fuer Feuchtigkeitserhalt. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 (optional) |

**EC-Budget:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm** -- OK

**Hinweis Erdkultur:** Die berechnete EC der Giessloessung (~0.8 mS/cm) liegt unter den hydroponischen Zielwerten (1.5--2.0 mS/cm). Das ist korrekt fuer Erdkultur -- das Substrat speichert und puffert Naehrstoffe. Bei sehr wuechsigen Pflanzen Terra Grow auf 6--7 ml/L steigern (EC ~1.0 mS/cm).

### 4.4 FLOWERING -- Bluete + Fruchtansatz (Woche 9--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150--180 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) bei ersten Bluetenknospen. Pure Zym + Sugar Royal weiter. Power Roots absetzen (Abschluss mit Ende VEGETATIVE, Woche 8). **PK 13-14 NUR in Woche 10--11 (0.5 ml/L)** -- einmaliger Boost waehrend peak Fruchtansatz. Danach sofort absetzen! **Bestaeubung:** Parthenokarpe Gewaechshaus-Sorten (z.B. Picolino F1) brauchen KEINE Bestaeubung. Freiland-Sorten brauchen Insektenbestaeubung -- Dill als Nachbar lockt Bestaeuber an. **Calcium-Hinweis:** Gleichmaessig giessen, Ca-Transport sicherstellen. Bei weichem Wasser Calciumchlorid-Foliarspray (0.5 g CaCl2/L) erwaegen. **Ausgeizen (Gewaechshaus-Schlangengurken):** Seitentriebe nach dem 1. Fruchtansatz zurueckschneiden, Haupttrieb an Rankhilfe hochleiten. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.8  |
| reference_ec_ms | 1.8  |
| target_ph | 6.0 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |
| PK 13-14 ml/L | 0.5 (NUR Woche 10--11!) |

**EC-Budget (ohne PK):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.92 mS/cm** -- OK
**EC-Budget (mit PK, W10--11):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + 0.125 (PK 0.5ml) + ~0.4 (Wasser) = **~1.05 mS/cm** -- OK

**Hinweis PK 13-14:** Der Fruchtbooster wird bei Gurken in niedriger Dosis (0.5 ml/L statt 1.5 ml/L) eingesetzt. Gurke profitiert vom P/K-Schub fuer den Fruchtansatz, aber die Anwendung ist kuerzer und sanfter als bei Cannabis. Plagron-Empfehlung fuer Erde: 0.5--1.0 ml/L. Bei EC-Anstieg auf >1.5 mS/cm in der Giessloessung PK weglassen.

### 4.5 HARVEST -- Dauerertrag + Ernte (Woche 13--20)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 20 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| NPK-Abweichung | Terra Bloom liefert NPK 2-2-4; Steckbrief-Ideal fuer Ernte ist 1-2-3. Abweichung ist systembedingt (1-Komponenten-Produkt) und praxistauglich -- hoehere K-Versorgung foerdert Fruchtqualitaet. | |
| Calcium (ppm) | 150--200 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (4 ml/L) waehrend Dauerernte. Kein Sugar Royal -- organischer Stickstoff (9-0-0) foerdert vegetatives Wachstum und verschlechtert Fruchtqualitaet. Pure Zym weiter fuer Substratgesundheit. **Kein PK 13-14 mehr!** Haupternte-Phase: ALLE 1--2 TAGE kontrollieren und ernten! Salatgurken bei 25--30 cm, Einlegegurken bei 5--10 cm ernten. Ueberreife Gurken (gelb, dick) hemmen den Neuansatz massiv. Morgenfrueche Ernte ist optimal (hoechster Wassergehalt, knackig). **Kalium:** Terra Bloom liefert K2O 3.9% -- gute Versorgung fuer Fruchtqualitaet und -haltbarkeit. Kaliummangel = birnenfoermige, bittere Fruechte! **Wasserbedarf:** In Erntephase 0.5--1.5 L pro Pflanze pro Tag. Bei Hitze 2x taeglich giessen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.0 |
| Terra Bloom ml/L | 4.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.40 (TB 4.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.80 mS/cm** -- OK

**Hinweis Erdkultur:** Fuer grosse, ertragreiche Pflanzen kann die Dosis auf 5 ml/L TB gesteigert werden (EC ~1.0 mS/cm). Drainagewasser-EC kontrollieren -- bei EC >2.5 mit klarem Wasser durchspuelen.

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
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Salzreste aus Substrat ausspuelen. Letzte Fruechte ernten. Pflanzen entfernen und kompostieren. Substrat nicht fuer Cucurbitaceae wiederverwenden (Krankheitsrisiko). | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Pflanze baut ab) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** -- OK

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan April--September.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | PK 13-14 ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|----------------|-----------------|----------|
| April (frueh) | GERMINATION | -- | -- | -- | -- | -- | -- | 0.4 | Spruehung 1d |
| April (spaet) | SEEDLING | 1.5 | -- | 1.0 | -- | -- | -- | 0.5 | alle 2d |
| Mai | SEED/VEG | 1.5->5.0 | -- | 1.0 | 1.0* | 1.0* | -- | 0.5->0.8 | alle 2d->1d |
| Juni | VEG->FLOW | 5.0->-- | -->5.0 | 1.0->-- | 1.0 | 1.0 | 0.5** | 0.8->1.1 | taeglich |
| Juli | FLOW->HARV | -- | 5.0->4.0 | -- | 1.0 | 1.0->-- | -- | 0.9->0.8 | taeglich |
| August | HARVEST | -- | 4.0 | -- | 1.0 | -- | -- | 0.8 | taeglich |
| September | HARV->FLUSH | -- | 4.0->0 | -- | 1.0 | -- | -- | 0.8->0.4 | taegl.->3d |

*Pure Zym und Sugar Royal ab VEGETATIVE-Phase (ca. Anfang Mai, Woche 5).
**PK 13-14 nur 1--2 Wochen in Juni (Woche 10--11, peak Fruchtansatz).

```
Monat:       |Apr(f)|Apr(s)|Mai  |Jun  |Jul  |Aug  |Sep  |
KA-Phase:    |GERM  |SEED  |S→VEG|V→FLO|F→HAR|HARV |H→FLU|
Terra Grow:  |---   |##-   |##→==|===  |---  |---  |---  |
Terra Bloom: |---   |---   |---  |-->==|==→##|###  |##→--|
Power Roots: |---   |===   |===  |==→--|---  |---  |---  |
Pure Zym:    |---   |---   |-->==|===  |===  |===  |===  |
Sugar Royal: |---   |---   |-->==|===  |==→--|---  |---  |
PK 13-14:    |---   |---   |---  |=*=  |---  |---  |---  |

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, =*= = nur 1--2 Wochen in diesem Monat
         --> = Start, ->  = Uebergang
```

### Jahresverbrauch (geschaetzt)

Bei einer Gurkenpflanze, 0.5--1.5 L Giessloessung pro Duengung, taeglich im Sommer:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (3 Wo x 3.5/Wo x 1.5ml + 4 Wo x 7/Wo x 5ml) = 156 ml | **~160 ml** |
| Terra Bloom | (4 Wo x 7/Wo x 5ml + 8 Wo x 7/Wo x 4ml) = 364 ml | **~360 ml** |
| Power Roots | (7 Wo x 5/Wo x 1ml) = 35 ml | **~35 ml** |
| Pure Zym | (16 Wo x 6/Wo x 1ml) = 96 ml | **~100 ml** |
| Sugar Royal | (8 Wo x 7/Wo x 1ml) = 56 ml | **~56 ml** |
| PK 13-14 | (1.5 Wo x 7 x 0.5ml) = 5 ml | **~5 ml** |

**Kosten-Schaetzung:** Gurken verbrauchen etwas weniger Naehrloesung als Tomaten (kuerzere Saison, 22 vs. 28 Wochen). Bei 1L-Flaschen: Terra Bloom reicht fuer ca. 3 Pflanzen-Saisons, Terra Grow fuer ca. 6. PK 13-14 (1L-Flasche) reicht quasi unbegrenzt.

---

## 6. Gurken-spezifische Praxis-Hinweise

### Bittere Gurken vermeiden

Bitter schmeckende Gurken enthalten erhoehte Cucurbitacin-Konzentrationen. Ursachen und Praevention:

**Ursachen:**
- **Trockenstress** -- die haeufigste Ursache! Unregelmaessige Bewaesserung
- **Hitzestress** -- Temperaturen ueber 32 degC
- **Kaeltestress** -- Temperaturen unter 14 degC, kaltes Giesswasser
- **Naehrstoffmangel** -- besonders Kaliummangel
- **Alte Sorten** -- moderne F1-Hybriden sind cucurbitacinfrei selektiert

**Praevention:**
- **TAEGLICH gleichmaessig giessen** -- KONSISTENZ ist das Wichtigste!
- **Giesswasser auf 18--24 degC temperieren**
- **Mulchen** -- reduziert Verdunstung und stabilisiert Bodenfeuchte
- **Kalium sicherstellen** -- Terra Bloom liefert K2O 3.9%
- **Schattiernetz** bei extremer Hitze (>30 degC)
- **Fruehmorgens ernten** -- bester Geschmack

### Mehltau-Management

Echter Mehltau ist die haeufigste Gurkenkrankheit:

**Praevention:**
- **NIE ueber die Blaetter giessen** -- Bodenbewaesserung (DRENCH) ist Pflicht
- **Luftzirkulation** -- nicht zu eng pflanzen, Seitentriebe auslichten
- **Resistente Sorten** waehlen (Picolino F1, Diamant F1)
- **Mulchen** -- reduziert Spritzwasser-Infektionen
- **Tropfbewaesserung** ideal

**Behandlung bei Befall:**
- Befallene Blaetter sofort entfernen (Restmuell, NICHT Kompost)
- Kaliumbicarbonat 0.5% spruehen (alle 7 Tage)
- Milch-Wasser-Loesung 1:9 (praeventiv, alle 3--5 Tage)
- Netzschwefel 0.2% (ACHTUNG: nicht bei ueber 25 degC -- Blattverbrennungen!)

### Ausgeizen (Gewaechshaus-Schlangengurken)

**Warum:** Gewaechshaus-Schlangengurken werden an Schnur/Draht gezogen. Unkontrollierte Seitentriebe reduzieren Fruchtgroesse und -qualitaet.

**Wie:**
- Seitentriebe nach dem 1. Fruchtansatz zurueckschneiden
- Haupttrieb an der Rankhilfe hochleiten
- Bodenberuehrende, kranke Blaetter entfernen
- **Freiland-/Einlegegurken:** Weniger Schnitt noetig -- nur kranke Blaetter entfernen

### Substrat

- Naehrstoffreiche, humose, wasserhaltende Erde (Gemuese-Substrat)
- pH 6.0--6.8, gut drainierend trotz hohem Wasserbedarf
- Topfgroesse: min. 20 L pro Pflanze, ideal 30--40 L
- Im Freiland: 60--100 cm Pflanzabstand (an Rankhilfe enger, am Boden weiter)
- **Mulchen:** 5--10 cm Stroh oder Grasschnitt -- reduziert Verdunstung, Unkraut und Fruchtfaeule durch Bodenkontakt

### Temperatur-Hinweise

- **Optimum:** 24--28 degC Tag, 18--22 degC Nacht
- **Wachstumsstopp:** Unter 14 degC stellt die Pflanze das Wachstum ein
- **Kaelteschaden:** Unter 10 degC -- Blattverfaerbung, reduzierte Fruchtqualitaet
- **Hitzestress:** Ueber 32 degC -- bittere Fruechte, Bluetenabwurf
- **Frostempfindlich:** Stirbt bei Temperaturen unter 5 degC ab
- **Nicht vor Mitte Mai auspflanzen** (nach Eisheiligen!)
- **Giesswasser temperieren:** Mindestens 18 degC -- kaltes Wasser verursacht Wurzelstress

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Cucurbitaceae (Gurke, Zucchini, Kuerbis, Melone) auf gleicher Flaeche
- **Gute Vorfruechte:** Huelsenfruechte (N-Fixierung), Gruenduengung
- **Gute Nachfruechte:** Mittelzehrer (Moehren, Fenchel) oder Schwachzehrer (Salat, Radieschen)
- **Schlechte Nachbarn:** Kartoffel, Melone, Kuerbis/Zucchini, Fenchel
- **Gute Nachbarn:** Dill (klassisch!), Bohnen, Erbsen, Mais, Salat, Radieschen, Tagetes

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet

**Cucumis sativus ist NICHT GIFTIG fuer Katzen, Hunde oder Kinder (moderne Kultursorten).**

**ACHTUNG -- Cucurbitacin-Warnung:**
- **Bitter schmeckende Gurken NICHT essen!** Bittere Fruechte koennen erhoehte Cucurbitacin-Konzentrationen enthalten
- **Moderne Kultursorten** sind cucurbitacinfrei selektiert und unbedenklich
- **Ziergugewaechse NIEMALS essen** -- Cucurbitacin-Vergiftung ist lebensgefaehrlich
- **Symptome bei Cucurbitacin-Vergiftung:** Heftiges Erbrechen, Durchfall, Kolikschmerzen
- **Immer VOR dem Kochen ein kleines Stueck roh probieren** -- bei Bitterkeit sofort entsorgen
- **Cucurbitacine werden durch Kochen NICHT zerstoert!**

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Geerntete Fruechte vor Verzehr gruendlich waschen (Duengerrueckstaende auf Oberflaeche moeglich)
- **2 Wochen duengerfreie FLUSHING-Phase** vor Saisonende empfohlen

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Gurke \u2014 Plagron Terra + PK 13-14",
  "description": "Saisonplan f\u00fcr Salatgurken und Einlegegurken mit Indoor-Vorkultur ab April und Gew\u00e4chshaus-/Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 6 Produkten inkl. PK 13-14 Fruchtbooster. Starkzehrer, 22 Wochen (April\u2013September).",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["gurke", "cucumber", "cucumis", "sativus", "starkzehrer", "plagron", "terra", "pk-13-14", "erde", "gewaechshaus", "outdoor"],
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
  "week_end": 1,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Indoor-Aussaat in Anzuchterde, 25\u201330\u00b0C Substrattemperatur (Heizmatte). Dunkelkeimer, 2\u20133 cm tief. Feine Spr\u00fchung, kein D\u00fcnger. Keimung nach 3\u20137 Tagen.",
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
      "notes": "Nur warmes Wasser (18\u201324\u00b0C). Feine Spr\u00fchung, Substrat gleichm\u00e4\u00dfig feucht halten.",
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
  "week_start": 2,
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). NICHT pikieren \u2013 empfindliche Wurzeln! Power Roots f\u00f6rdert Wurzelentwicklung. EC z\u00fcgig steigern (Starkzehrer).",
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
      "target_ph": 6.0,
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
  "notes": "Volle Dosis Terra Grow (5 ml/L). Kr\u00e4ftiger Blatt- und Rankenaufbau. Abh\u00e4rtung ab Woche 7. Auspflanzen nach Eisheiligen (ca. 15. Mai). Rankhilfe aufstellen, Mulch ausbringen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + alle Additive. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.0,
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
  "notes": "Umstellung auf Terra Bloom (5 ml/L). Power Roots absetzen. PK 13-14 (0.5 ml/L) NUR in Woche 10\u201311 als einmaliger Fruchtansatz-Boost. Danach sofort absetzen! Ausgeizen bei Gew\u00e4chshaus-Schlangengurken. Calcium gleichm\u00e4\u00dfig sicherstellen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive + PK 13-14 (nur W10\u201311!). Reihenfolge: Terra Bloom \u2192 PK 13-14 \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.8,
      "reference_ec_ms": 1.8,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true},
        {"fertilizer_key": "<pk_13_14_key>", "ml_per_liter": 0.5, "optional": true, "_comment": "NUR Woche 10-11, danach absetzen!"}
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
  "calcium_ppm": 175,
  "magnesium_ppm": 50,
  "notes": "Reduzierter Terra Bloom (4 ml/L). Kein Sugar Royal (organischer N verschlechtert Fruchtqualit\u00e4t). Kein PK 13-14. Alle 1\u20132 Tage ernten! Salatgurken bei 25\u201330 cm, Einlegegurken bei 5\u201310 cm. \u00dcberreife Gurken hemmen Neuansatz massiv. Kalium sicherstellen (K-Mangel = birnenf\u00f6rmige, bittere Fr\u00fcchte).",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Ernte-D\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Bloom. Kein Sugar Royal, kein PK 13-14.",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.0,
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
  "notes": "Kein D\u00fcnger. Substrat mit klarem Wasser durchsp\u00fclen. Pure Zym f\u00fcr Salzabbau. Letzte Fr\u00fcchte ernten. Pflanzen kompostieren.",
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
      "target_ph": 6.0,
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
| Fertilizer: PK 13-14 | `spec/ref/products/plagron_pk_13_14.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |
| Species: Cucumis sativus | `spec/ref/plant-info/cucumis_sativus.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/ref/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/ref/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/ref/products/plagron_sugar_royal.md`
6. Plagron PK 13-14 Produktdaten: `spec/ref/products/plagron_pk_13_14.md`
7. Gurke Pflanzensteckbrief: `spec/ref/plant-info/cucumis_sativus.md`
8. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
9. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
