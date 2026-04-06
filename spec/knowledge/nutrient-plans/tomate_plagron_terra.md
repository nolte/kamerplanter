# Naehrstoffplan: Tomate -- Plagron Terra + PK 13-14

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Solanum lycopersicum (Starkzehrer, Indoor-Vorkultur + Outdoor ab Mai)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal, PK 13-14
> **Erstellt:** 2026-03-01
> **Quellen:** spec/knowledge/products/plagron_terra_*.md, spec/knowledge/products/plagron_power_roots.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/products/plagron_sugar_royal.md, spec/knowledge/products/plagron_pk_13_14.md, spec/knowledge/plants/solanum_lycopersicum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Tomate -- Plagron Terra + PK 13-14 | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Tomaten (indeterminiert) mit Indoor-Vorkultur ab Maerz und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 6 Produkten inkl. PK 13-14 Bluetebooster. Klassischer Starkzehrer mit hohem K-Bedarf ab Fruchtbildung. Einjaehrige Kultur, kein Zyklus-Neustart. 28 Wochen Gesamtdauer (Maerz--Oktober). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.1 | `nutrient_plans.version` |
| Tags | tomate, tomato, solanum, lycopersicum, starkzehrer, plagron, terra, pk-13-14, erde, outdoor, gewaechshaus | `nutrient_plans.tags` |
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

**Hinweis:** Taeglich giessen als Sommerbasis -- Tomaten sind Starkzehrer mit hohem Wasserbedarf (1--2 L/Pflanze/Tag bei Hitze). Gleichmaessige Wasserversorgung ist essentiell zur BER-Praevention. In GERMINATION (1 Tag, leichte Spruehung), SEEDLING (2 Tage) und FLUSHING (3 Tage) ueber `watering_schedule_override` angepasst. **Nie ueber die Blaetter giessen** -- Phytophthora-Risiko!

---

## 2. Phasen-Mapping

Tomate ist eine einjaehrige Nutzpflanze in Mitteleuropa (Solanum lycopersicum). Typische indeterminierte Sorten: Harzfeuer, Moneymaker, Ochsenherz. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Tomaten-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|---------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Anfang Maerz | Indoor-Aussaat auf Heizmatte, 22--25 degC Substrattemperatur. Kein Duenger. | false |
| Saemling | SEEDLING | 3--6 | Mitte Maerz--Anfang April | Jungpflanze mit Keimblaettern + ersten echten Blaettern. Viertel-Dosis Terra Grow. Pikieren nach 2. Blattpaar. | false |
| Vegetatives Wachstum | VEGETATIVE | 7--12 | April--Mitte Mai | Volle Duengung Terra Grow. Kraeftiger Stamm- und Blattaufbau. Abhaertung + Auspflanzen nach Eisheiligen (ca. 15. Mai). | false |
| Bluete | FLOWERING | 13--17 | Mitte Mai--Mitte Juni | Umstellung auf Terra Bloom. Erste Bluetentrauben setzen Fruechte an. PK 13-14 einmalig in Woche 15--16 (peak Fruchtansatz). Ausgeizen beginnt. | false |
| Fruchtreife + Ernte | HARVEST | 18--26 | Mitte Juni--Ende August | Kontinuierliche Ernte reifer Fruechte. Terra Bloom reduziert. K:N-Verhaeltnis hoch. Ca-Transport sicherstellen (gleichmaessig giessen!). | false |
| Saisonende/Spuelung | FLUSHING | 27--28 | September | Kein Duenger, nur Wasser + Pure Zym. Salzreste ausspuelen. Letzte gruene Fruechte nachreifen lassen (Karton + Apfel). | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (einjaehrige Kultur, keine Ueberwinterung)

**Kein Zyklus-Neustart:** Tomate ist einjaehrig. Nach Saisonende (Woche 28, ca. Oktober) wird die Pflanze entfernt und kompostiert. Im Folgejahr: neue Pflanzen, neuer Durchlauf. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Solanaceae auf gleicher Flaeche!

**Lueckenlos-Pruefung:** 2 + 4 + 6 + 5 + 9 + 2 = 28 Wochen, keine Luecken

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
| method_params | drench, 0.5--1.0 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Bluete

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-bluete | `delivery_channels.channel_id` |
| Label | Bluetenduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Additive ins Giesswasser. Reihenfolge: Terra Bloom -> PK 13-14 (nur W15--16) -> Pure Zym -> Sugar Royal -> pH pruefen. PK 13-14 Basisdosis reduzieren auf 70% Terra Bloom! | `delivery_channels.notes` |
| method_params | drench, 1.0--2.0 L pro Pflanze | `delivery_channels.method_params` |

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

### EC-Budget Plagron-Produkte fuer Tomaten

Tomaten sind Starkzehrer mit hoher EC-Toleranz (bis 2.5 mS/cm in Hydrokultur). **In Erdkultur** ist die benoetigte EC in der Giessloessung deutlich niedriger, da das Substrat Naehrstoffe puffert und speichert. Leitungswasser liefert typisch 0.2--0.8 mS/cm (regionenabhaengig). In Hartwasserregionen (>0.7 mS/cm) Terra-Bloom-Dosis bei Bedarf auf 4 ml/L reduzieren oder 20--30% Regenwasser/Osmosewasser beimischen. EC des lokalen Leitungswassers beim Wasserversorger erfragen oder mit EC-Geraet messen. Die Plagron-Dosierungen sind fuer Erdkultur kalibriert.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ |
| Terra Bloom (2-2-4) | 0.10 | 20 | Bluete, Ernte |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Spuelung |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ, Bluete |
| PK 13-14 (0-13-14) | 0.25 | 30 | Nur Woche 15--16 (Bluetebooster) |

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
| Hinweise | Indoor-Aussaat in Anzuchterde, Samen 0.5 cm tief, Substrattemperatur 22--25 degC (Heizmatte). Feine Spruehung, Substrat gleichmaessig feucht aber nicht nass. Kein Duenger -- Anzuchterde liefert Grundversorgung. Abdeckung mit Klarsichtfolie/Haube fuer hohe Luftfeuchte (80--90%). Keimung nach 5--10 Tagen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.03 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | null (kein Duenger -- Gesamt-EC entspricht Leitungswasser-EC ~0.3--0.5 mS/cm) |
| reference_ec_ms | null |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling (Woche 3--6)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 6 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren in Einzeltoepfe (8--10 cm) nach 2. echtem Blattpaar (ca. Woche 4). Kuehlere Nachttemperaturen (16 degC) foerdern stockigen Wuchs. Power Roots foerdert fruehe Wurzelentwicklung. Noch kein Pure Zym oder Sugar Royal noetig. | `phase_entries.notes` |
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

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm** ✓

### 4.3 VEGETATIVE -- Vegetatives Wachstum (Woche 7--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 7 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Volle Dosis Terra Grow (5 ml/L). Kraeftiger Stamm- und Blattaufbau. Power Roots weiter fuer Wurzelentwicklung. Pure Zym ab jetzt fuer Substratgesundheit. Sugar Royal fuer verbesserte Chlorophyllbildung und Aminosaeuren. **Abhaertung:** Ab Woche 11 taeglich einige Stunden nach draussen stellen (7--10 Tage). **Auspflanzen:** Nach Eisheiligen (ca. 15. Mai) in Freiland/Gewaechshaus, Stuetzstab setzen, Pflanzloch mit Kompost anreichern. Bei sehr wuechsigen Pflanzen kann auf 6--7 ml/L TG gesteigert werden. | `phase_entries.notes` |

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

**EC-Budget:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm** ✓

**Hinweis Erdkultur:** Die berechnete EC der Giessloessung (~0.8 mS/cm) liegt unter den hydroponischen Zielwerten (1.2--1.8 mS/cm). Das ist korrekt fuer Erdkultur -- das Substrat speichert und puffert Naehrstoffe. Bei wuechsigen Pflanzen Terra Grow auf 6--7 ml/L steigern (EC ~1.0 mS/cm).

### 4.4 FLOWERING -- Bluete (Woche 13--17)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 17 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 150--200 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Umstellung auf Terra Bloom (5 ml/L) bei ersten Bluetenknospen. Pure Zym + Sugar Royal weiter. Power Roots absetzen (Abschluss mit Ende VEGETATIVE, Woche 12 -- nicht mehr in FLOWERING; optional koennen die ersten 2 Wochen von FLOWERING noch Power Roots 1 ml/L enthalten, um Wurzeln bei Hitzebelastung zu unterstuetzen). **PK 13-14 NUR in Woche 15--16 (0.5 ml/L)** -- einmaliger Boost waehrend peak Fruchtansatz der ersten Bluetentrauben. Danach sofort absetzen! **Ausgeizen (indeterminiert):** Woechentlich ALLE Geiztriebe aus Blattachseln entfernen -- mit der Hand abknipsen, NICHT schneiden (Krankheitsuebertragung). 1 Haupttrieb belassen. **Calcium-Hinweis:** Fruchtansatz erhoht Ca-Bedarf drastisch. Bei weichem Wasser (<0.4 mS/cm) Calciumchlorid-Foliarspray (0.5 g CaCl2 pro Liter Wasser) direkt auf junge Fruechte (NICHT auf Blaetter). BER-Praevention: gleichmaessig giessen, EC nicht ueber 2.0 mS/cm! **Bestaeubung unter Glas:** Bluetenstaende taeglich bei geoeffneten Blueten (10--14 Uhr) leicht schuetteln oder mit Handbestaeuber/Vibrationsstab vibrieren. Alternativ: kleiner Ventilator 5--10 Min Luftbewegung erzeugen (einfachste Methode). Im Gewaechshaus: Hummeln (Bombus terrestris) als Standardbestaeuber. Tomaten sind Windbestaeuber. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.8  |
| reference_ec_ms | 1.8  |
| target_ph | 6.0 |
| Terra Bloom ml/L | 5.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 |
| PK 13-14 ml/L | 0.5 (NUR Woche 15--16!) |

**EC-Budget (ohne PK):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.92 mS/cm** ✓
**EC-Budget (mit PK, W15--16):** 0.50 (TB 5.0ml) + 0.00 (PZ) + 0.02 (SR) + 0.125 (PK 0.5ml) + ~0.4 (Wasser) = **~1.05 mS/cm** ✓

**Hinweis PK 13-14:** Der Bluetebooster wird bei Tomaten in niedriger Dosis (0.5 ml/L statt 1.5 ml/L) eingesetzt. Tomate profitiert vom P/K-Schub fuer den Fruchtansatz, aber die Anwendung ist kuerzer und sanfter als bei Cannabis. Plagron-Empfehlung fuer Erde: 0.5--1.0 ml/L. Bei EC-Anstieg auf >1.5 mS/cm in der Giessloessung PK weglassen.

### 4.5 HARVEST -- Fruchtreife + Ernte (Woche 18--26)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 18 | `phase_entries.week_start` |
| week_end | 26 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (2, 2, 4) | `phase_entries.npk_ratio` |
| NPK-Abweichung | Terra Bloom liefert NPK 2-2-4; Steckbrief-Ideal fuer Fruchtreife ist 1-2-4. Abweichung ist systembedingt (1-Komponenten-Produkt) und praxistauglich. | |
| Calcium (ppm) | 150--200 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 50 | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Bloom (4 ml/L) waehrend Fruchtreife. Kein Sugar Royal -- organischer Stickstoff (9-0-0) foerdert vegetatives Wachstum und verschlechtert Fruchtqualitaet. Pure Zym weiter fuer Substratgesundheit. **Kein PK 13-14 mehr!** Haupternte-Phase: kontinuierlich reife Fruechte ernten (rot/gelb je nach Sorte). **K:N-Verhaeltnis:** Terra Bloom liefert K:N von ~1.86:1 (3.9% K2O vs. 2.1% N) -- knapp unterhalb der 2:1-Empfehlung aus dem Steckbrief, aber in der Praxis ausreichend fuer guten Geschmack. Wer K:N exakt >2:1 erreichen moechte: Kaliumsulfat (0.3 g/L, EC +0.08 mS/cm) als optionaler K-Booster. **Calcium weiter sicherstellen:** BER-Risiko steigt bei Hitze + unregelmaessigem Giessen. Taeglich morgens giessen, gleichmaessige Wassermengen. Bei grossen Pflanzen Terra Bloom auf 5--6 ml/L erhoehen. **Ausgeizen:** Weiter woechentlich Geiztriebe entfernen. Ab Mitte August (ca. W24) oberste Triebspitze kappen (Toppen) -- konzentriert Energie in bestehende Fruechte. **Lycopin:** Tagtemperatur ueber 30 degC hemmt Lycopin-Synthese (Fruechte bleiben gelb/orange). Gewaechshaus belueften! | `phase_entries.notes` |

**Delivery Channel: naehrloesung-bluete**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.0 |
| Terra Bloom ml/L | 4.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.40 (TB 4.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.80 mS/cm** ✓

**Hinweis Erdkultur:** Fuer grosse, ertragreiche Pflanzen (>1.5 m) kann die Dosis auf 5--6 ml/L TB gesteigert werden (EC ~1.0 mS/cm). Drainagewasser-EC kontrollieren -- bei EC >2.5 mit klarem Wasser durchspuelen.

### 4.6 FLUSHING -- Saisonende/Spuelung (Woche 27--28)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 6 | `phase_entries.sequence_order` |
| week_start | 27 | `phase_entries.week_start` |
| week_end | 28 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger, nur Wasser + Pure Zym. Salzreste aus Substrat ausspuelen. Letzte reife Fruechte ernten. Gruene Fruechte abnehmen und in Karton mit reifem Apfel nachreifen lassen (Ethylen-Trick). Nach 2 Wochen Pflanzen entfernen und kompostieren. Substrat nicht wiederverwenden fuer Solanaceae (Krankheitsrisiko). | `phase_entries.notes` |
| Giessplan-Override | Intervall 3 Tage (reduziert, Pflanze baut ab) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | null (kein Duenger -- Gesamt-EC entspricht Leitungswasser-EC ~0.3--0.5 mS/cm) |
| reference_ec_ms | null |
| target_ph | 6.0 |
| Pure Zym ml/L | 1.0 |
| fertilizer_dosages | Pure Zym only |

**EC-Budget:** 0.00 (PZ) + ~0.4 (Wasser) = **~0.4 mS/cm** ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan Maerz--Oktober.

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | PK 13-14 ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|----------------|-----------------|----------|
| Maerz (frueh) | GERMINATION | -- | -- | -- | -- | -- | -- | 0.4 | Spruehung 1d |
| Maerz (spaet) | SEEDLING | 1.5 | -- | 1.0 | -- | -- | -- | 0.5 | alle 2d |
| April | SEEDLING/VEG | 1.5->5.0 | -- | 1.0 | 1.0* | 1.0* | -- | 0.5->0.8 | alle 2d->1d |
| Mai | VEG->FLOW | 5.0->-- | -->5.0 | 1.0->-- | 1.0 | 1.0 | -- | 0.8->0.9 | taeglich |
| Juni | FLOWERING | -- | 5.0 | -- | 1.0 | 1.0 | 0.5** | 0.9->1.1 | taeglich |
| Juli | FLOW->HARV | -- | 5.0->4.0 | -- | 1.0 | 1.0->-- | -- | 0.9->0.8 | taeglich |
| August | HARVEST | -- | 4.0 | -- | 1.0 | -- | -- | 0.8 | taeglich |
| September | HARV->FLUSH | -- | 4.0->0 | -- | 1.0 | -- | -- | 0.8->0.4 | taegl.->3d |
| Oktober | -- | -- | -- | -- | -- | -- | -- | -- | Pflanzen entfernen |

*Pure Zym und Sugar Royal ab VEGETATIVE-Phase (ca. Mitte April, Woche 7). In der ersten April-Haelfte (SEEDLING, bis ca. 15. April) noch nicht einsetzen.
**PK 13-14 nur 1 Woche in Juni (Woche 15--16, peak Fruchtansatz erster Bluetentrauben).

```
Monat:       |Mär(f)|Mär(s)|Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |Okt|
KA-Phase:    |GERM  |SEED  |S→VEG|V→FLO|FLOW |F→HAR|HARV |H→FLU| --|
Terra Grow:  |---   |##-   |##→==|===  |---  |---  |---  |---  |---|
Terra Bloom: |---   |---   |---  |-->==|===  |==→##|###  |##→--|---|
Power Roots: |---   |===   |===  |==→--|---  |---  |---  |---  |---|
Pure Zym:    |---   |---   |-->==|===  |===  |===  |===  |===  |---|
Sugar Royal: |---   |---   |-->==|===  |===  |==→--|---  |---  |---|
PK 13-14:    |---   |---   |---  |---  |=*=  |---  |---  |---  |---|

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, =*= = nur 1 Woche in diesem Monat
         --> = Start, ->  = Uebergang
```

### Jahresverbrauch (geschaetzt)

Bei einer Tomatenpflanze, 1.0--1.5 L Giessloessung pro Duengung, taeglich im Sommer:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (4 Wo x 3.5/Wo x 1.5ml + 6 Wo x 7/Wo x 5ml) = 231 ml | **~230 ml** |
| Terra Bloom | (5 Wo x 7/Wo x 5ml + 9 Wo x 7/Wo x 4ml) = 427 ml | **~430 ml** |
| Power Roots | (10 Wo x 5/Wo x 1ml) = 50 ml | **~50 ml** |
| Pure Zym | (20 Wo x 6/Wo x 1ml) = 120 ml | **~120 ml** |
| Sugar Royal | (11 Wo x 7/Wo x 1ml) = 77 ml | **~80 ml** |
| PK 13-14 | (1 Wo x 7 x 0.5ml) = 3.5 ml | **~4 ml** |

**Kosten-Schaetzung:** Tomaten verbrauchen deutlich mehr Naehrloesung als Erdbeeren (taeglich giessen, 28 Wochen). Bei 1L-Flaschen: Terra Bloom reicht fuer ca. 2 Pflanzen-Saisons, Terra Grow fuer ca. 4. PK 13-14 (1L-Flasche) reicht fuer ca. 250 Pflanzen-Saisons -- eine Flasche hinsichtlich Tomate quasi unbegrenzt.

---

## 6. Tomaten-spezifische Praxis-Hinweise

### Bluetenendfaeule (Blossom End Rot, BER)

BER ist die haeufigste physiologische Stoerung bei Tomaten. Es handelt sich **NICHT** um einen Calciummangel im Substrat, sondern um eine **Calcium-Transportstoerug** in der Pflanze.

**Ursachen:**
- **Unregelmaessige Bewaesserung** (Nass-Trocken-Zyklen) -- haeufigste Ursache!
- **Zu hohe EC** (>2.0 mS/cm in Erdkultur) -- osmotischer Stress hemmt Ca-Transport
- **Uebermaessiger Ammonium-Stickstoff (NH4)** -- konkurriert mit Ca-Aufnahme
- **Hohe Temperaturen** + niedrige Luftfeuchte -- erhoehte Transpiration verlagert Ca in Blaetter statt Fruechte
- **Schnelles Fruchtwachstum** -- Ca kann nicht schnell genug eingelagert werden

**Praevention:**
- **Taeglich morgens gleichmaessig giessen** -- KONSISTENZ ist wichtiger als Menge!
- **EC unter 2.0 mS/cm** in der Giessloessung halten
- **Mulchen** -- reduziert Verdunstung und stabilisiert Bodenfeuchte
- **Calciumchlorid-Foliarspray** (0.5 g CaCl2/L Wasser) direkt auf junge Fruechte beim Fruchtansatz (praeventiv, NICHT auf Blaetter). Alternativ bei weichem Wasser: Calciumnitrat (Ca(NO3)2) 0.5 g/L ins Giesswasser (enthaelt N -- in Fruchtphase sparsam dosieren)
- **Nicht ueberdungen** -- besonders kein uebermaessiger N in der Fruchtphase

**Wenn BER auftritt:**
1. EC der Giessloessung um 20% reduzieren
2. Giessfrequenz erhohen (2x taeglich bei Hitze)
3. Foliares Calciumchlorid-Spray (0.5 g CaCl2/L Wasser) direkt auf junge Fruechte (nicht auf Blaetter)
4. Befallene Fruechte entfernen (werden nicht besser)
5. Nicht in Panik verfallen -- naechste Fruchttraube kann normal sein

### Ausgeizen (indeterminierte Sorten)

**Warum:** Indeterminierte (Stab-)Tomaten bilden in jeder Blattachsel Seitentriebe (Geiztriebe). Ohne Ausgeizen wuchert die Pflanze unkontrolliert, bildet viele kleine statt wenige grosse Fruechte und trocknet im Inneren schlecht ab (Pilzrisiko).

**Wie:**
- Woechentlich pruefen (im Sommer alle 3--5 Tage)
- Geiztriebe **mit der Hand abknipsen** bei 3--5 cm Laenge
- **NICHT mit Messer/Schere schneiden** -- Krankheitsuebertragung (TMV, Bakterien)!
- Am besten morgens bei trockenem Wetter (Wunde heilt schneller)
- Blatttriebe (= echte Blaetter am Hauptstamm) NICHT entfernen -- nur Geiztriebe aus Blattachseln
- **1 Haupttrieb** belassen (Standard), bei Buschtomaten determiniert: nicht ausgeizen

**Toppen (Endstopp):**
- Ab Mitte August (ca. 6--8 Wochen vor Saisonende) den Haupttrieb ueber der obersten Bluetetraube kappen
- Konzentriert Energie in bestehende Fruechte statt in neues Wachstum
- Neue Blueten nach diesem Zeitpunkt wuerden vor Saisonende ohnehin nicht mehr ausreifen

### Substrat

- Naehrstoffreiche, humose Erde (Tomatenerde oder universale Pflanzenerde mit Kompost)
- pH 5.8--6.5, gut drainierend
- Topfgroesse: min. 10 L pro Pflanze, ideal 20--40 L (Kuebel, Kiesfilterbeutel)
- Im Freiland: 50x50 cm Pflanzabstand, 30 cm tiefes Pflanzloch mit Kompost und Hornspane (80--120 g/m2)
- **Tief pflanzen:** Tomate bildet Adventivwurzeln am Stamm -- tiefer pflanzen als im Anzuchttopf foerdert Standfestigkeit

### Krautfaeule-Praevention (Phytophthora infestans)

Die wichtigste Tomatenkrankheit im Freiland:
- **NIE ueber die Blaetter giessen** -- Bodenbewaaerung (DRENCH) ist Pflicht
- **Untere Blaetter entfernen** bis zur ersten Fruchttraube (Spritzwasser-Schutz)
- **Luftzirkulation** -- nicht zu eng pflanzen, Geiztriebe entfernen
- **Regenschutz:** Dachvorsprung, Tomatendach oder Gewaechshaus ideal
- **Mulchen:** 5--8 cm Stroh um Stammfuss reduziert Spritzwasser-Infektion
- **Mischkultur mit Basilikum:** Aetherische Oele koennen Pilzbefall reduzieren

### Temperatur-Hinweise

- **Lycopin-Synthese:** Optimum 22--26 degC Tag. Ueber 30 degC wird Lycopin gehemmt -- Fruechte bleiben gelb/orange statt rot. Gewaechshaus belueften!
- **Bluetenabwurf:** Tagestemperaturen ueber 32 degC oder Nachttemperaturen ueber 25 degC fuehren zu Pollensterilitaet und Bluetenabwurf. In Hitzephasen Bewaesserung erhoehen und schattieren.
- **Kalteschaden:** Unter 10 degC stellt die Pflanze das Wachstum ein. Nicht vor Mitte Mai (nach Eisheiligen) auspflanzen!

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Solanaceae (Tomate, Kartoffel, Paprika, Aubergine) auf gleicher Flaeche. **Topfkultur mit frischem Substrat:** Bei jaehrlich erneuertem Substrat ist die Fruchtfolge-Pause nicht zwingend -- wichtig ist nur, das alte Substrat nicht fuer Solanaceae wiederzuverwenden (Sporen ueberdauern im Boden)
- **Gute Vorfruechte:** Huelsenfruechte (N-Fixierung), Getreide (Bodenstruktur)
- **Gute Nachfruechte:** Schwachzehrer (Salat, Spinat, Radieschen), Huelsenfruechte
- **Schlechte Nachbarn:** Kartoffel (gemeinsame Krankheiten!), Fenchel (allelopathisch)
- **Gute Nachbarn:** Basilikum, Tagetes, Karotte, Petersilie, Knoblauch

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet (WICHTIG!)

**Solanum lycopersicum ist GIFTIG fuer Katzen, Hunde und Kinder (gruene Pflanzenteile):**

- **Blaetter, Staengel und UNREIFE (gruene) Fruechte** enthalten Solanin und Tomatin (Glykoalkaloide)
- **Symptome bei Haustieren:** Magen-Darm-Beschwerden, Uebelkeit, Erbrechen, Durchfall, Lethargie
- **Symptome bei Kindern:** Magen-Darm-Beschwerden, Kopfschmerzen, Schwindel
- **Reife (rote/gelbe) Fruechte sind UNBEDENKLICH** -- Solaningehalt sinkt beim Reifen auf unbedenkliches Niveau
- **Kontaktallergen:** Blatttrichome koennen Kontaktdermatitis ausloesen -- bei Empfindlichkeit Handschuhe tragen

**Schutzmassnahmen:**
- Haustiere und Kleinkinder von Tomatenpflanzen fernhalten
- Gruenteile und gruene Fruechte NICHT verzehren
- Abgeerntete Blaetter und Pflanzenschnitt sicher kompostieren (nicht frei zugaenglich)
- Hunde nicht an Tomatenpflanzen knabbern lassen

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Geerntete Fruechte vor Verzehr gruendlich waschen (Duengerrueckstaende auf Oberflaeche moeglich)
- **1 Woche duengerfreie FLUSHING-Phase** vor Saisonende empfohlen

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Tomate \u2014 Plagron Terra + PK 13-14",
  "description": "Saisonplan f\u00fcr Tomaten (indeterminiert) mit Indoor-Vorkultur ab M\u00e4rz und Freilandkultur ab Mitte Mai. Plagron Terra-Linie mit 6 Produkten inkl. PK 13-14 Bl\u00fctebooster. Starkzehrer, 28 Wochen (M\u00e4rz\u2013Oktober).",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.1",
  "tags": ["tomate", "tomato", "solanum", "lycopersicum", "starkzehrer", "plagron", "terra", "pk-13-14", "erde", "outdoor", "gewaechshaus"],
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
  "notes": "Indoor-Aussaat in Anzuchterde, 22\u201325\u00b0C Substrattemperatur (Heizmatte). Feine Spr\u00fchung, kein D\u00fcnger. Keimung nach 5\u201310 Tagen.",
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
      "notes": "Nur Wasser, kein D\u00fcnger. Feine Spr\u00fchung, Substrat gleichm\u00e4\u00dfig feucht halten. Gesamt-EC entspricht Leitungswasser-EC (~0.3\u20130.5 mS/cm).",
      "target_ec_ms": null,
      "reference_ec_ms": null,
      "target_ph": 6.0,
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
  "week_end": 6,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren nach 2. Blattpaar. K\u00fchlere Nachttemperaturen (16\u00b0C) f\u00fcr st\u00f6ckigen Wuchs. Power Roots f\u00f6rdert Wurzelentwicklung.",
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
  "week_start": 7,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Volle Dosis Terra Grow (5 ml/L). Kr\u00e4ftiger Stamm- und Blattaufbau. Abh\u00e4rtung ab Woche 11. Auspflanzen nach Eisheiligen (ca. 15. Mai). Bei sehr w\u00fcchsigen Pflanzen auf 6\u20137 ml/L steigern.",
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
  "week_start": 13,
  "week_end": 17,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 175,
  "magnesium_ppm": 50,
  "notes": "Umstellung auf Terra Bloom (5 ml/L). Power Roots absetzen (Abschluss mit Ende VEGETATIVE W12; optional erste 2 Wochen FLOWERING weiterfuehren). PK 13-14 (0.5 ml/L) NUR in Woche 15\u201316 als einmaliger Fruchtansatz-Boost. Danach sofort absetzen! Ausgeizen w\u00f6chentlich. Calcium-Erg\u00e4nzung empfohlen (CaCl2-Foliarspray 0.5 g/L direkt auf junge Fr\u00fcchte bei weichem Wasser). BER-Pr\u00e4vention: gleichm\u00e4\u00dfig gie\u00dfen, EC <2.0!",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-bluete",
      "label": "Bl\u00fctend\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Additive + PK 13-14 (nur W15\u201316!). Reihenfolge: Terra Bloom \u2192 PK 13-14 \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.8,
      "reference_ec_ms": 1.8,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true},
        {"fertilizer_key": "<pk_13_14_key>", "ml_per_liter": 0.5, "optional": true, "_comment": "NUR Woche 15-16, danach absetzen!"}
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
  "week_start": 18,
  "week_end": 26,
  "is_recurring": false,
  "npk_ratio": [2.0, 2.0, 4.0],
  "calcium_ppm": 175,
  "magnesium_ppm": 50,
  "notes": "Reduzierter Terra Bloom (4 ml/L). NPK 2-2-4 (Steckbrief-Ideal 1-2-4; systembedingte Abweichung, praxistauglich). K:N ~1.86:1 (knapp unter 2:1-Empfehlung; optional Kaliumsulfat 0.3 g/L erg\u00e4nzen). Mg ~50 ppm (Terra Bloom 0.8% + Leitungswasser). Kein Sugar Royal (organischer N verschlechtert Fruchtqualit\u00e4t). Kein PK 13-14. Kontinuierliche Ernte reifer Fr\u00fcchte. K:N-Verh\u00e4ltnis hoch f\u00fcr Geschmack. Calcium weiterhin sicherstellen (BER-Risiko bei Hitze). Ab Mitte August Haupttrieb \u00fcber oberster Fruchttraube kappen.",
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
  "week_start": 27,
  "week_end": 28,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Substrat mit klarem Wasser durchsp\u00fclen. Pure Zym f\u00fcr Salzabbau. Letzte Fr\u00fcchte ernten, gr\u00fcne Fr\u00fcchte in Karton mit Apfel nachreifen. Pflanzen kompostieren.",
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
      "notes": "Nur Wasser + Pure Zym. Kein D\u00fcnger. Gesamt-EC entspricht Leitungswasser-EC (~0.3\u20130.5 mS/cm).",
      "target_ec_ms": null,
      "reference_ec_ms": null,
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
| Fertilizer: Terra Grow | `spec/knowledge/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Terra Bloom | `spec/knowledge/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Power Roots | `spec/knowledge/products/plagron_power_roots.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Sugar Royal | `spec/knowledge/products/plagron_sugar_royal.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: PK 13-14 | `spec/knowledge/products/plagron_pk_13_14.md` | `fertilizer_dosages.fertilizer_key` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |
| Species: Solanum lycopersicum | `spec/knowledge/plants/solanum_lycopersicum.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/knowledge/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/knowledge/products/plagron_sugar_royal.md`
6. Plagron PK 13-14 Produktdaten: `spec/knowledge/products/plagron_pk_13_14.md`
7. Tomate Pflanzensteckbrief: `spec/knowledge/plants/solanum_lycopersicum.md`
8. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
9. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.1
**Erstellt:** 2026-03-01
**Letzte Aenderung:** 2026-04-05 (Review T-001 bis T-012 abgearbeitet)
