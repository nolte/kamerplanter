# Naehrstoffplan: Lauch (Porree) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Allium porrum (Starkzehrer, Vorkultur Februar + Freiland ab Mai/Juni)
> **Produkte:** Plagron Terra Grow, Terra Bloom, Power Roots, Pure Zym, Sugar Royal
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_*.md, spec/knowledge/products/plagron_power_roots.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/products/plagron_sugar_royal.md, spec/knowledge/plants/allium_porrum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Lauch (Porree) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Winterlauch mit langer Indoor-Vorkultur ab Februar und Freilandpflanzung ab Mai/Juni. Plagron Terra-Linie mit 5 Produkten. Starkzehrer mit hohem N- und K-Bedarf, extrem lange vegetative Phase (Schaftbildung). Kein Bluetebooster noetig (Bluete unerwuenscht -- Schossen vermeiden!). K-betonte Duengung ab Spaetsommer fuer Winterhaerte. Ernte Oktober--Maerz. 34 Wochen Gesamtdauer (Februar--Oktober, Ernte bis Maerz). | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | lauch, porree, winterlauch, leek, allium, porrum, starkzehrer, plagron, terra, erde, outdoor, winter | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaehrig, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Alle 2 Tage als Basis -- Lauch braucht gleichmaessige Bodenfeuchte fuer dicke Schaefte, ist aber weniger wasserintensiv als Tomaten oder Zucchini. In GERMINATION (1 Tag, Spruehung) und SEEDLING (2 Tage) sowie HARVEST (natuerlicher Niederschlag) ueber `watering_schedule_override` angepasst. Bodennah giessen, **nie ins Herz** (Faeulnisgefahr!). Bei Hitzeperioden im Sommer taeglich giessen.

---

## 2. Phasen-Mapping

Porree ist eine zweijaehrige Pflanze, die als Einjaehrige kultiviert wird (Allium porrum). Typische Winterlauch-Sorten: Blaugruener Winter, Carentan 2, De Solaise. Die Phasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Lauch-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--3 | Februar | Indoor-Aussaat in Topfplatten, 15--20 degC. Dunkelkeimer, 1--2 cm tief. Kein Duenger. Keimung nach 10--20 Tagen. | false |
| Saemling (Voranzucht) | SEEDLING | 4--11 | Maerz--April | Lange Saemlings-Phase (8 Wochen). Grasartige Blaetter, langsames Wachstum. Viertel-Dosis Terra Grow. Abhaertung ab April. | false |
| Vegetatives Wachstum | VEGETATIVE | 12--26 | Mai--August | Volle Duengung Terra Grow, dann Terra Bloom. Extrem lange Phase (15 Wochen). Schaftwachstum, Anhaeuefeln in 3 Etappen. Auspflanzen Mai/Juni in tiefe Furchen. Ab August K-betonte Duengung (Terra Bloom) fuer Winterhaerte. | false |
| Ernte (Winterernte) | HARVEST | 27--34 | September--Oktober (Ernte bis Maerz) | Keine Duengung mehr. Ernte nach Bedarf, Winterlauch steht im Beet. Frostschutz (Vlies/Laub) auflegen. Vor Schossen im Fruehjahr alle Pflanzen ernten. | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Bluete ist bei Lauch unerwuenscht -- Schossen bedeutet Qualitaetsverlust. Bluetenstaende sofort entfernen!)
- **FLUSHING** entfaellt (Winterlauch steht bis zur Ernte im Boden, natuerlicher Uebergang)
- **DORMANCY** entfaellt (Erntephase deckt die Winterperiode ab)

**Kein Zyklus-Neustart:** Porree wird als Einjaehrige kultiviert. Im Folgejahr: neue Pflanzen, neuer Durchlauf. **Fruchtfolge beachten:** 3--4 Jahre Anbaupause fuer Amaryllidaceae (Lauch, Zwiebel, Knoblauch, Schnittlauch) auf gleicher Flaeche!

**Besonderheit Phasen-Mapping:** Die VEGETATIVE-Phase ist mit 15 Wochen ungewoehnlich lang. Sie umfasst sowohl die N-betonte Wachstumsphase (Terra Grow, Mai--Juli) als auch die K-betonte Winterhaerte-Vorbereitung (Terra Bloom, August--September). Der Wechsel Terra Grow -> Terra Bloom erfolgt INNERHALB der vegetativen Phase (ca. Woche 20, August), nicht bei einem Phasenwechsel. Dies wird ueber die Delivery-Channel-Konfiguration mit Hinweis geloest.

**Lueckenlos-Pruefung:** 3 + 8 + 15 + 8 = 34 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne (Vorkultur) und Freiland-Duengung.

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Keimungsspruehung (Spruehflasche) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Nur Wasser, feine Spruehung. Substrat gleichmaessig feucht halten. Dunkelkeimer, 1--2 cm tief. | `delivery_channels.notes` |
| method_params | drench, 0.01 L pro Spruehung | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum (N-betont)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung N-betont (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Additive ins Giesswasser. Reihenfolge: Terra Grow -> Power Roots -> Pure Zym -> Sugar Royal -> pH pruefen. Fuer Blatt- und Schaftwachstum (Mai--Juli). | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Naehrloesung Winterhaerte (K-betont)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-winterhaerte | `delivery_channels.channel_id` |
| Label | K-betonte Duengung Winterhaerte (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. Kalium-betont fuer Winterhaerte ab August. Kein Sugar Royal (N-Duengung einstellen). | `delivery_channels.notes` |
| method_params | drench, 0.3--0.5 L pro Pflanze | `delivery_channels.method_params` |

### 3.4 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne/natuerlich) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Winterernte: natuerlicher Niederschlag genuegt, bei Trockenheit giessen. | `delivery_channels.notes` |
| method_params | drench, 0.3 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Lauch

Lauch ist ein Starkzehrer mit hohem N- und K-Bedarf. In Erdkultur sind die benoetigten EC-Werte moderat. Leitungswasser liefert typisch 0.2--0.8 mS/cm. **Kein PK 13-14 noetig** -- Lauch soll nicht bluehen! Terra Bloom liefert ausreichend K fuer Winterhaerte.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ (Mai--Juli) |
| Terra Bloom (2-2-4) | 0.10 | 20 | Vegetativ spaet (Aug--Sep, K-betont) |
| Power Roots (0-0-2) | 0.01 | 60 | Saemling, Vegetativ (Mai--Juli) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ bis Ernte |
| Sugar Royal (9-0-0) | 0.02 | 65 | Vegetativ (Mai--Juli) |

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
| Hinweise | Indoor-Aussaat in Topfplatten/Saatschalen, Samen 1--2 cm tief (Dunkelkeimer). 15--20 degC (optimal 18 degC). Feine Spruehung, Substrat gleichmaessig feucht. Kein Duenger. Keimung nach 10--20 Tagen. Saemlinge sind anfangs sehr duenn und grasartig. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichte Spruehung, 0.01 L) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser) ✓

### 4.2 SEEDLING -- Saemling/Voranzucht (Woche 4--11)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 4 | `phase_entries.week_start` |
| week_end | 11 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L), alle 2 Wochen. Lange Voranzuchtsphase (8 Wochen). Saemlinge wachsen langsam und sind duenn/grasartig. Power Roots foerdert Wurzelentwicklung. Noch kein Pure Zym oder Sugar Royal noetig. Abhaertung ab Woche 9--10 (April). Blatt- und Wurzelspitzen bei Pflanzung auf 2/3 kuerzen (foerdert Anwachsen). Pflanzung wenn Saemlinge bleistiftdick sind (ca. 6--8 mm, 15--20 cm hoch). | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage | `phase_entries.watering_schedule_override` |

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

**EC-Budget:** 0.12 (TG 1.5ml) + 0.01 (PR) + ~0.4 (Wasser) = **~0.53 mS/cm** ✓

### 4.3 VEGETATIVE -- Schaftwachstum (Woche 12--26)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 12 | `phase_entries.week_start` |
| week_end | 26 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| NPK-Abweichung | NPK 3-1-3 (Terra Grow) fuer Mai--Juli. Ab August Wechsel auf Terra Bloom (2-2-4) fuer Kalium-betonte Winterhaerte-Vorbereitung. Der Wechsel erfolgt innerhalb der Phase (ca. Woche 20). | |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | **Phase 1 (Woche 12--19, Mai--Juli): N-betonte Wachstumsduengung.** Volle Dosis Terra Grow (5 ml/L). Auspflanzen in Furchen oder Loecher (10--15 cm tief), Pflanzabstand 15 cm, Reihenabstand 30--40 cm. Power Roots bei Pflanzung. Pure Zym + Sugar Royal ab Woche 14. **1. Anhaeuefeln** (Juli, Woche 16--18): Erde 5--10 cm am Schaft hochziehen. Keine Erde ins Herz! **Phase 2 (Woche 20--26, August--September): K-betonte Winterhaerte-Duengung.** Wechsel auf Terra Bloom (4 ml/L). Sugar Royal absetzen (N-Duengung einstellen!). **2. Anhaeuefeln** (August, Woche 20--22). **3. Anhaeuefeln** (September, Woche 24--26). Kulturschutznetze gegen Lauchmotte/Minierfliege kontrollieren. | `phase_entries.notes` |

**Delivery Channel Phase 1 (Woche 12--19): naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.5  |
| reference_ec_ms | 1.5  |
| target_ph | 6.5 |
| Terra Grow ml/L | 5.0 (volle Dosis) |
| Power Roots ml/L | 1.0 (nur bis Woche 14) |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | 1.0 (optional) |

**EC-Budget Phase 1:** 0.40 (TG 5.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.02 (SR) + ~0.4 (Wasser) = **~0.83 mS/cm** ✓

**Delivery Channel Phase 2 (Woche 20--26): naehrloesung-winterhaerte**

| Feld | Wert |
|------|------|
| target_ec_ms | 1.2  |
| reference_ec_ms | 1.2  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 4.0 |
| Pure Zym ml/L | 1.0 |
| Sugar Royal ml/L | -- (abgesetzt, kein N mehr!) |

**EC-Budget Phase 2:** 0.40 (TB 4.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.80 mS/cm** ✓

**Hinweis N-Stopp:** Ab August/September keinen Stickstoff mehr zuefuehren! N foerdert weiches Gewebe, das bei Frost geschaedigt wird. Kalium (K) staerkt die Zellwaende und erhoeht die Frostresistenz. Terra Bloom liefert K2O 3.9% bei nur N 2.1% -- ideales Verhaeltnis fuer Winterhaerte.

### 4.4 HARVEST -- Winterernte (Woche 27--34)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 27 | `phase_entries.week_start` |
| week_end | 34 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung mehr. Winterlauch-Sorten stehen den ganzen Winter im Beet (frosthart bis -15 degC). Ernte nach Bedarf bei frostfreiem Boden. Frostschutz: Vlies oder Laubschicht auflegen, damit Boden nicht komplett durchfriert (sonst Ernte unmoeglich). **Vor dem Schossen** im Fruehjahr (Maerz/April) alle verbleibenden Pflanzen ernten! Schosser (Bluetenstaende) sofort entfernen. | `phase_entries.notes` |
| Giessplan-Override | kein Giessen (natuerlicher Niederschlag; bei Trockenheit im Herbst gelegentlich giessen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.4 (nur Wasser/Niederschlag) ✓

---

## 5. Jahresplan (Monat-fuer-Monat)

Einjaehrige Kultur, kein zyklischer Betrieb. Saisonplan Februar--Oktober (Ernte bis Maerz Folgejahr).

| Monat | KA-Phase | Terra Grow ml/L | Terra Bloom ml/L | Power Roots ml/L | Pure Zym ml/L | Sugar Royal ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|------------------|-----------------|--------------|-----------------|-----------------|----------|
| Februar | GERMINATION | -- | -- | -- | -- | -- | 0.4 | Spruehung 1d |
| Maerz | SEEDLING | 1.5 | -- | 1.0 | -- | -- | 0.5 | alle 2 Wo |
| April | SEEDLING | 1.5 | -- | 1.0 | -- | -- | 0.5 | alle 2 Wo |
| Mai | SEED->VEG | 1.5->5.0 | -- | 1.0 | -->1.0 | -- | 0.5->0.8 | 2d->2d |
| Juni | VEGETATIVE | 5.0 | -- | 1.0->-- | 1.0 | 1.0 | 0.8 | alle 2d |
| Juli | VEGETATIVE | 5.0 | -- | -- | 1.0 | 1.0 | 0.8 | alle 2d |
| August | VEG (K-bet.) | 5.0->-- | -->4.0 | -- | 1.0 | 1.0->-- | 0.8->0.8 | alle 2d |
| September | VEG->HARV | -- | 4.0->0 | -- | 1.0->-- | -- | 0.8->0.4 | alle 2d->nat. |
| Oktober | HARVEST | -- | -- | -- | -- | -- | -- | natuerlich |
| Nov--Maerz | HARVEST | -- | -- | -- | -- | -- | -- | natuerlich |

```
Monat:       |Feb  |Mär  |Apr  |Mai  |Jun  |Jul  |Aug  |Sep  |Okt  |Nov-Mär|
KA-Phase:    |GERM |SEED |SEED |S→VEG|VEG  |VEG  |VEG-K|V→HAR|HARV | HARV  |
Terra Grow:  |---  |##-  |##-  |##→==|===  |===  |==→--|---  |---  | ---   |
Terra Bloom: |---  |---  |---  |---  |---  |---  |-->##|##→--|---  | ---   |
Power Roots: |---  |===  |===  |===  |==→--|---  |---  |---  |---  | ---   |
Pure Zym:    |---  |---  |---  |-->==|===  |===  |===  |==→--|---  | ---   |
Sugar Royal: |---  |---  |---  |---  |-->==|===  |==→--|---  |---  | ---   |

Legende: --- = nicht verwendet, ### = reduzierte Dosis, === = volle Dosis
         ##- = Viertel-Dosis, --> = Start, ->  = Uebergang
         VEG-K = Vegetativ mit K-betonter Duengung (Terra Bloom statt Terra Grow)
```

### Jahresverbrauch (geschaetzt)

Bei 10 Lauch-Pflanzen, 0.3--0.5 L Giessloessung pro Duengung, alle 2 Tage im Sommer (Vorkultur weniger):

| Produkt | Formel | Verbrauch/10 Pflanzen/Saison |
|---------|--------|------------------------------|
| Terra Grow | (8 Wo x 1/Wo x 1.5ml + 8 Wo x 3.5/Wo x 5ml) = 152 ml | **~150 ml** |
| Terra Bloom | (8 Wo x 3.5/Wo x 4ml) = 112 ml | **~110 ml** |
| Power Roots | (12 Wo x 2/Wo x 1ml) = 24 ml | **~25 ml** |
| Pure Zym | (14 Wo x 3.5/Wo x 1ml) = 49 ml | **~50 ml** |
| Sugar Royal | (8 Wo x 3.5/Wo x 1ml) = 28 ml | **~30 ml** |

**Kosten-Schaetzung:** Lauch verbraucht relativ wenig Plagron-Produkte, da die Voranzucht wenig Naehrloesung benoetigt und die Giessmenge pro Pflanze geringer ist als bei Tomaten/Zucchini. Fuer den typischen Hobbygaertner mit 10--20 Pflanzen reichen die kleinsten Flaschengroessen (250 ml) fuer mehrere Saisons.

---

## 6. Lauch-spezifische Praxis-Hinweise

### Anhaeuefeln (Bleichen)

Der weisse Schaftteil entsteht durch Anhaeuefeln -- Erde am Schaft hochziehen, um Licht abzuschirmen. Das ist die wichtigste Pflegemassnahme bei Lauch.

**Vorgehen:**
- **3 Etappen:** Juli (1.), August (2.), September (3.)
- Pro Etappe 5--10 cm Erde anhaeuefeln
- **KEINE Erde ins Herz** (= Vegetationspunkt in der Mitte) -- fuehrt zu Faeulnis!
- Alternativ zur Erde: Papp-/Kartonhuelsen (10--15 cm) um den Schaft stellen
- Bei Pflanzung in tiefe Furchen (10--15 cm) ist weniger Anhaeuefeln noetig

### Kulturschutznetze (WICHTIGSTE Schutzmassnahme!)

Lauchmotte und Lauchminierfliege sind die Hauptschaedlinge. Kulturschutznetze sind die einzig wirksame Praevention.

- **Feinmaschig** (<0.8 mm Maschenweite)
- **Ab Pflanzung** lueckenlos verschliessen
- Netz regelmaessig auf Beschaedigungen pruefen
- Beim Anhaeuefeln kurz oeffnen, sofort wieder schliessen
- Alternativ: Mischkultur mit Moehren (Geruchstarnung)

### Schossen verhindern

Schossen (Bluete im 1. Jahr) wird ausgeloest durch:
- **Kaelteperioden** (Vernalisation) bei bereits grossen Pflanzen
- **Zu fruehe Aussaat** bei anschliessend kalten Temperaturen
- **Stress** (Trockenheit, Naehrstoffmangel)

**Praevention:**
- Nicht zu frueh auspflanzen (Jungpflanzen unter 8 mm Durchmesser bei Kaeltephasen sind weniger gefaehrdet)
- Gleichmaessig giessen und duengen
- Schosser sofort entfernen (Bluetenstab abschneiden)

### Substrat

- Naehrstoffreiche, tiefgruendige, humose Erde
- pH 6.0--7.5 (kalkvertraeglich)
- Vor Pflanzung: 5--8 L/m2 Kompost + 80--100 g/m2 Hornspane einarbeiten
- Tiefe Pflanzung: Locher mit Dibber (Pflanzholz) vorstechen, Saemling einsetzen, NICHT angiessen (Wasser fuellt das Loch und drueckt die Erde an)

### Fruchtfolge

- **3--4 Jahre Anbaupause** fuer alle Amaryllidaceae (Lauch, Zwiebel, Knoblauch, Schnittlauch) auf gleicher Flaeche
- **Gute Vorfruechte:** Huelsenfruechte (N-Fixierung), Gruenduengung
- **Gute Nachfruechte:** Schwachzehrer (Feldsalat, Spinat), Mittelzehrer (Moehre, Salat)
- **Klassische Mischkultur:** Moehre + Lauch (gegenseitige Schaedlingsabwehr: Moehrenfliege vs. Lauchmotte)
- **Schlechte Nachbarn:** Huelsenfruechte (Allicin hemmt Knollchenbakterien), andere Allium-Arten

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet (WICHTIG fuer Haustiere!)

**Allium porrum ist GIFTIG fuer Katzen und Hunde:**

- **ALLE Allium-Arten** (Zwiebel, Knoblauch, Schnittlauch, Lauch) sind fuer Katzen und Hunde giftig -- roh, gekocht, getrocknet oder fluessig
- **Giftiger Inhaltsstoff:** N-Propyl-Disulfid (verursacht oxidative Schaedigung der roten Blutkoerperchen)
- **Symptome:** Erbrechen, haemolytische Anaemie (Abbau roter Blutkoerperchen), Blut im Urin, Schwaeche, erhoehte Herzfrequenz
- **Fuer Menschen:** Als Lebensmittel in normalen Mengen unbedenklich

**Schutzmassnahmen:**
- Haustiere von Lauch-Beeten fernhalten
- Ernte und Kuechenabfaelle nicht fuer Hunde/Katzen zugaenglich lassen

### Duengemittel-Sicherheit

- Plagron-Konzentrate: nicht gesundheitsschaedlich, aber nicht fuer Verzehr geeignet
- Alle Flaschen ausserhalb der Reichweite von Kindern und Haustieren aufbewahren
- Bei Hautkontakt mit Wasser abspuelen
- Geernteten Lauch vor Verzehr gruendlich waschen (Erde und Duengerrueckstaende zwischen Blattschichten)

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Lauch (Porree) \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Winterlauch mit langer Vorkultur ab Februar und Freilandpflanzung ab Mai/Juni. Plagron Terra-Linie mit 5 Produkten. Starkzehrer, 34 Wochen (Februar\u2013Oktober, Ernte bis M\u00e4rz). K-betonte D\u00fcngung ab August f\u00fcr Winterh\u00e4rte.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["lauch", "porree", "winterlauch", "leek", "allium", "porrum", "starkzehrer", "plagron", "terra", "erde", "outdoor", "winter"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 8.2 NutrientPlanPhaseEntry (4 Eintraege)

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
  "notes": "Indoor-Aussaat in Topfplatten, 15\u201320\u00b0C. Dunkelkeimer, 1\u20132 cm tief. Feine Spr\u00fchung, kein D\u00fcnger. Keimung nach 10\u201320 Tagen.",
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
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.01}
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
  "week_end": 11,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L), alle 2 Wochen. Lange Voranzucht (8 Wochen). Power Roots f\u00f6rdert Wurzelentwicklung. Abh\u00e4rtung ab April. Pflanzung wenn S\u00e4mling bleistiftdick (6\u20138 mm, 15\u201320 cm).",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 14,
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
      "notes": "Terra Grow Viertel-Dosis + Power Roots, alle 2 Wochen",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
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
  "week_start": 12,
  "week_end": 26,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Phase 1 (W12\u201319, Mai\u2013Juli): Volle Dosis Terra Grow (5 ml/L), N-betont f\u00fcr Schaftwachstum. Power Roots bis W14. Pure Zym + Sugar Royal ab W14. Anh\u00e4ufeln 1. Etappe Juli. Phase 2 (W20\u201326, Aug\u2013Sep): Wechsel auf Terra Bloom (4 ml/L), K-betont f\u00fcr Winterh\u00e4rte. Sugar Royal absetzen (kein N mehr!). Anh\u00e4ufeln 2. + 3. Etappe. Kulturschutznetze kontrollieren.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung N-betont (Gie\u00dfkanne) \u2013 W12\u201319",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow + Additive. Mai\u2013Juli. Reihenfolge: Terra Grow \u2192 Power Roots \u2192 Pure Zym \u2192 Sugar Royal \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.5,
      "reference_ec_ms": 1.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 5.0, "optional": false},
        {"fertilizer_key": "<power_roots_key>", "ml_per_liter": 1.0, "optional": true, "_comment": "Nur bis Woche 14"},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false},
        {"fertilizer_key": "<sugar_royal_key>", "ml_per_liter": 1.0, "optional": true}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
    },
    {
      "channel_id": "naehrloesung-winterhaerte",
      "label": "K-betonte D\u00fcngung Winterh\u00e4rte (Gie\u00dfkanne) \u2013 W20\u201326",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom + Pure Zym. Aug\u2013Sep. Kein Sugar Royal (N-Stopp!). Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 pH pr\u00fcfen",
      "target_ec_ms": 1.2,
      "reference_ec_ms": 1.2,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 4.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.5}
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
  "week_start": 27,
  "week_end": 34,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Winterlauch steht im Beet (frosthart bis -15\u00b0C). Ernte nach Bedarf bei frostfreiem Boden. Frostschutz: Vlies/Laub auflegen. Vor Schossen (M\u00e4rz/April) alle Pflanzen ernten.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 7,
    "preferred_time": "07:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nat\u00fcrliche Bew\u00e4sserung / bei Bedarf",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Nat\u00fcrlicher Niederschlag gen\u00fcgt. Bei Trockenheit im Herbst gelegentlich gie\u00dfen.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
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
| Species: Allium porrum | `spec/knowledge/plants/allium_porrum.md` | `species.scientific_name` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
3. Plagron Power Roots Produktdaten: `spec/knowledge/products/plagron_power_roots.md`
4. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
5. Plagron Sugar Royal Produktdaten: `spec/knowledge/products/plagron_sugar_royal.md`
6. Lauch (Porree) Pflanzensteckbrief: `spec/knowledge/plants/allium_porrum.md`
7. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
8. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
