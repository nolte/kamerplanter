# Naehrstoffplan: Basilikum (Sweet Basil) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Ocimum basilicum (einjaehrig, Schwachzehrer, Indoor ganzjaehrig / Outdoor Mai--September)
> **Produkte:** Plagron Terra Grow, Pure Zym
> **Erstellt:** 2026-03-01
> **Quellen:** spec/knowledge/products/plagron_terra_grow.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/plants/ocimum_basilicum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Basilikum (Sweet Basil) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Minimalistischer Naehrstoffplan fuer Basilikum (Schwachzehrer). Nur 2 Produkte: Terra Grow (Basis) + Pure Zym (Enzym-Substratpflege). Bewusst niedrige Dosierung -- Ueberduengung reduziert den Gehalt aetherischer Oele um bis zu 28%. Ziel ist aromatisches Kraut, nicht maximale Biomasse. Einjaehrig, 18-Wochen-Zyklus von Aussaat bis Saisonende. Mehrere Aussaaten pro Jahr moeglich. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | basilikum, ocimum, sweet-basil, plagron, terra, erde, kraeutergarten, schwachzehrer, indoor, outdoor, aroma | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (einjaehrig, kein Zyklus-Neustart -- neue Aussaat starten) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 2 | `watering_schedule.interval_days` |
| Uhrzeit | 08:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 2-Tage-Intervall als Standardbasis. Basilikum mag gleichmaessig feuchtes (nicht nasses!) Substrat. In GERMINATION auf taegliches leichtes Spruehen umstellen (Override 1 Tag). **Immer morgens giessen** -- nie ueber die Blaetter (Pilzrisiko, besonders Falscher Mehltau und Fusarium). Substrat zwischen Giessen leicht abtrocknen lassen, Staunaesse ist der haeufigste Pflegefehler bei Basilikum.

---

## 2. Phasen-Mapping

Basilikum ist eine einjaehrige Pflanze tropischen Ursprungs (Indien/Suedostasien). Sie stirbt bei Temperaturen unter 5 degC ab und wird in Mitteleuropa als Saisonkultur (Freiland Mai--September) oder ganzjaehrig indoor (Fensterbank/Growlight) kultiviert. Die vegetative Phase ist gleichzeitig die Haupt-Erntephase -- regelmaessiges Entspitzen verzoegert die Bluete und foerdert buschigen Wuchs.

**Kernprinzip:** Weniger ist mehr. Basilikum ist ein Schwachzehrer. Jede Erhoehung der Duengerdosis ueber das hier beschriebene Mass hinaus verschlechtert die Aromaoelqualitaet direkt und messbar. Der Plan ist bewusst zurueckhaltend dosiert.

| Basilikum-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-----------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | ab Aussaat | Lichtkeimer, Samen nur andruecken. Bodentemperatur 20--25 degC. Kein Duenger. | false |
| Saemling | SEEDLING | 3--5 | +2 Wochen | Erstes echtes Blattpaar bis 2--3 Blattpaare. Minimale Vierteldosis Terra Grow (1.5 ml/L). | false |
| Erntephase (vegetativ) | VEGETATIVE | 6--12 | +3 Wochen | HAUPTERNTEPHASE -- regelmaessiges Entspitzen stimuliert Verzweigung. Halbe Dosis Terra Grow (2.5 ml/L). Bluetenansaetze sofort entfernen. | false |
| Bluete / Spaetphase | FLOWERING | 13--16 | +7 Wochen | Pflanze beginnt zu bluehen (Kurztagreaktion). Reduzierte Duengung (2.0 ml/L). Fuer Blatternten: ALLE Bluetenknospen ausbrechen. Fuer Saatgut: bluehen lassen. | false |
| Seneszenz / Letzte Ernte | HARVEST | 17--18 | +4 Wochen | Kein Duenger. Letzte Ernte aller brauchbaren Blaetter. Pflanze wird seneszent und stirbt ab. | false |

**Nicht genutzte Phasen:**
- **FLUSHING** entfaellt: Bei diesen minimalen Dosierungen ist keine Substratspuelung noetig. Die letzte duengerfreie Woche in HARVEST reicht aus.
- **DORMANCY** entfaellt: Basilikum ist einjaehrig -- es gibt keine Winterruhe.

**Kein Zyklus-Neustart:** Basilikum ist annuell. Nach 18 Wochen stirbt die Pflanze. Fuer Nachschub: neue Aussaat starten (siehe Abschnitt 5, Jahresplan).

**Hinweis zu HARVEST:** Der KA-Enum "HARVEST" wird hier fuer die botanische Seneszenz-Phase verwendet (kein "SENESCENCE"-Enum verfuegbar). Die letzte Ernte findet am Beginn dieser Phase statt; die Pflanze stirbt danach ab (einjaehrig, kein Weiteranbau).

**Lueckenlos-Pruefung:** 2 + 3 + 7 + 4 + 2 = 18 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne oder Spruehflasche. Minimales 2-Kanal-System passend zum minimalistischen Produktansatz.

### 3.1 Wasser -- Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung (Spruehflasche) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Feiner Spruehstrahl oder leichtes Giessen. Samen nicht wegschwemmen. | `delivery_channels.notes` |
| method_params | drench, 0.05 L pro Giessen (Spruehen) | `delivery_channels.method_params` |

### 3.2 Wasser -- Duengerfrei (Seneszenz)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-nur | `delivery_channels.channel_id` |
| Label | Nur Wasser (duengerfrei) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Fuer duengerfreie Phasen (Seneszenz/letzte Ernte) mit normalem Giessvolumen. | `delivery_channels.notes` |
| method_params | drench, 0.3 L pro Giessen | `delivery_channels.method_params` |

### 3.3 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> pH pruefen. NICHT ueberdosieren -- Basilikum braucht wenig! | `delivery_channels.notes` |
| method_params | drench, 0.3 L pro Giessen | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Basilikum

**WICHTIG: Basilikum ist ein Schwachzehrer.** Die hier angegebenen Dosierungen liegen bewusst bei 30--50% der Plagron-Herstellerempfehlung. Hoehere Dosierungen verschlechtern die Aromaoelqualitaet messbar (bis zu 28% weniger aetherische Oele bei Ueberduengung). EC der Gesamtloesung darf **1.6 mS/cm niemals ueberschreiten** (inkl. Basiswasser). Bei hartem Leitungswasser (>0.5 mS/cm) die Duengerdosis entsprechend weiter reduzieren.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase | Dosierung (% der Herstellerempfehlung) |
|---------|---------------|-----------------|-------|-----------------------------------------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ, Bluete | 30--50% |
| Pure Zym (0-0-0) | 0.00 | 70 | Saemling, Vegetativ, Bluete | 100% (Standard 1 ml/L) |

**Warum nur 2 Produkte?** Basilikum ist ein Schwachzehrer-Kraut. Komplexe Mehrstoff-Systeme (Bloom-Booster, PK-Ergaenzungen, Zucker-Additive) sind nicht nur ueberfluessig, sondern kontraproduktiv: Sie erhoehen das Risiko der Ueberduengung, die bei Basilikum direkt den Aromaoelgehalt -- also genau das, was die Pflanze wertvoll macht -- reduziert. Terra Grow liefert N-betonte Ernaehrung fuer Blattproduktion. Pure Zym haelt das Substrat gesund. Kein Bloom-Duenger noetig, da wir Bluete aktiv unterdruecken wollen.

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
| Hinweise | Kein Duenger! Basilikum ist ein Lichtkeimer -- Samen auf feuchtes Substrat druecken, NICHT bedecken. Bodentemperatur 20--25 degC (Heizmatte empfohlen). Substrat gleichmaessig feucht halten durch feines Spruehen, nie nass. Abdeckung mit Klarsichtfolie/Haube fuer Luftfeuchtigkeit 80--90%. Keimung in 5--10 Tagen. Pure Zym wird bewusst erst ab SEEDLING eingesetzt (nicht in GERMINATION): Substrat bei Aussaat ist noch frisch und unbelastet, Enzym-Kontakt mit frischen Keimlingen ist nicht noetig. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (taegliches Spruehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| reference_ec_ms | 0.0 |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** 0.00 + ~0.3--0.4 (Wasser) = **~0.3--0.4 mS/cm** (nur Wasser)

### 4.2 SEEDLING -- Saemling (Woche 3--5)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 5 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 1, 1) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Vierteldosis Terra Grow (1.5 ml/L) -- Basilikum-Saemlinge sind empfindlich. Vorgeduengte Blumenerde liefert Grundversorgung fuer 2--4 Wochen, daher erst ab Woche 3 beginnen. Weniger ist mehr: Lieber eine Woche laenger warten als zu frueh duengen. Pure Zym ab jetzt fuer Substratgesundheit. Nach 2. echtem Blattpaar pikieren in Einzeltoepfe (9 cm). Achtung: NH4-N-Anteil in Terra Grow gering halten (nur 0.6% NH4, Hauptanteil ist NO3 -- das ist gut fuer Basilikum, da ueberschuessiges Ammonium die Aromaoelproduktion hemmt). | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| reference_ec_ms | 0.5 |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Vierteldosis -- 30% der Herstellerempfehlung) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.12 (TG 1.5ml) + 0.00 (PZ) + ~0.3 (Wasser) = **~0.42 mS/cm** -- weit unter der Schmerzgrenze von 1.6 mS/cm

### 4.3 VEGETATIVE -- Erntephase (Woche 6--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 6 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | **HAUPTERNTEPHASE.** Halbe Dosis Terra Grow (2.5 ml/L) -- das ist die MAXIMALE Dosierung fuer Basilikum, nicht die Startdosis! Regelmaessiges Entspitzen der Triebspitzen (immer ueber einem Blattpaar schneiden) stimuliert Seitenverzweigung und verzoegert die Bluete. Bluetenansaetze sofort entfernen (Pinzieren). Nach der Ernte sinkt der Aromaoelgehalt nur leicht, bei Ueberduengung dagegen drastisch (bis zu 28%). Daher: Dosierung NICHT erhoehen, auch wenn die Pflanze "noch mehr vertragen koennte". EC-Zielwert 0.6 mS/cm (nicht 0.8!) -- bei Basilikum bringt weniger Duenger mehr Aroma. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6 |
| reference_ec_ms | 0.6 |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.5 (halbe Dosis -- 50% der Herstellerempfehlung) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.20 (TG 2.5ml) + 0.00 (PZ) + ~0.3 (Wasser) = **~0.50 mS/cm** -- bewusst niedrig fuer maximale Aromaoelqualitaet

### 4.4 FLOWERING -- Bluete / Spaetphase (Woche 13--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Grow (2.0 ml/L). Basilikum ist eine Kurztagspflanze -- kuerzere Tage im Spaetsommer/Herbst loesen die Bluete aus. Zwei Strategien: **(A) Blatternten-Modus (Standard):** ALLE Bluetenknospen sofort ausbrechen. Weiter ernten, solange Blaetter aromatisch sind. Duengung reduzieren, da die Pflanze trotzdem langsam an Kraft verliert. **(B) Saatgut-Modus:** Bluete zulassen, nicht mehr duengen, Saatgut nach Reife sammeln. Bei Indoor-Kultur mit >14h Belichtung kann die Bluete monatelang verzoegert werden (Langtagsverzoegerung). **Kein Bloom-Duenger noetig:** Wir WOLLEN die Bluete unterdruecken, nicht foerdern. Terra Grow (N-betont) bleibt korrekt. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| reference_ec_ms | 0.5 |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.0 (reduziert -- 40% der Herstellerempfehlung) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.16 (TG 2.0ml) + 0.00 (PZ) + ~0.3 (Wasser) = **~0.46 mS/cm** -- weiter reduziert, da die Pflanze ohnehin nachlasst

### 4.5 HARVEST -- Seneszenz / Letzte Ernte (Woche 17--18)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 17 | `phase_entries.week_start` |
| week_end | 18 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger. Letzte Ernte aller noch brauchbaren Blaetter. 1 Woche Abstand zwischen letzter Duengung und letzter Ernte empfohlen (Duengerreste auf Blaettern abwaschen). Blaetter trocknen, einfrieren oder als Pesto verarbeiten. Pflanze wird seneszent und stirbt ab. Substrat kann mit Pure Zym behandelt fuer naechste Aussaat vorbereitet werden (Wurzelrueckstaende abbauen). | `phase_entries.notes` |

**Delivery Channel: wasser-nur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| reference_ec_ms | 0.0 |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer -- kein Duenger) |

**EC-Budget:** ~0.3--0.4 (nur Wasser)

---

## 5. Jahresplan (Aussaat-Zyklen)

Basilikum ist einjaehrig -- es gibt keinen zyklischen Jahresplan wie bei perennialen Pflanzen. Stattdessen koennen mehrere unabhaengige 18-Wochen-Zyklen pro Jahr gestartet werden, besonders bei Indoor-Kultur:

### 5.1 Indoor-Aussaatkalender (ganzjaehrig moeglich)

| Aussaat | Startmonat | Erntefenster | Bemerkung |
|---------|-----------|-------------|-----------|
| Aussaat 1 | Februar | April--Juni | Indoor auf Fensterbank/Growlight, fruehester Start |
| Aussaat 2 | Mai | Juli--September | Outdoor nach Eisheiligen (ab 15. Mai) oder indoor |
| Aussaat 3 | August | Oktober--Dezember | Indoor fuer Herbst-/Winterernte, Zusatzbelichtung empfohlen |

Fuer jede Aussaat gelten die 18-Wochen-Phasen aus Abschnitt 2 identisch.

### 5.2 Monats-Uebersicht (Beispiel: Aussaat Februar indoor)

| Monat | KA-Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|---------------|-----------------|----------|
| Feb | GERMINATION | -- | -- | 0.3 | taeglich (Spruehen) |
| Maerz | SEEDLING | 1.5 | 1.0 | 0.4 | alle 2d |
| April | VEGETATIVE | 2.5 | 1.0 | 0.5 | alle 2d |
| Mai | VEGETATIVE | 2.5 | 1.0 | 0.5 | alle 2d |
| Juni | FLOWERING | 2.0 | 1.0 | 0.5 | alle 2d |
| Juli | HARVEST | -- | -- | 0.3 | alle 2d |

```
Monat (Aussaat Feb):  |Feb|Mär|Apr|Mai|Jun|Jul|
KA-Phase:             |GER|SEE|VEG|VEG|FLO|HAR|
Terra Grow:           |---|#--|===|===|##-|---|
Pure Zym:             |---|===|===|===|===|---|

Legende: --- = nicht verwendet, #-- = Vierteldosis, === = halbe Dosis (Maximum!)
         ##- = reduziert (40%)
```

### 5.3 Jahresverbrauch (geschaetzt)

Bei einem Basilikumtopf (1.5L Topf), 0.3 L Giessloessung pro Duengung, ein 18-Wochen-Zyklus:

| Produkt | Formel | Verbrauch/Zyklus |
|---------|--------|------------------|
| Terra Grow | (3 Wo x 3.5/Wo x 0.3L x 1.5ml + 7 Wo x 3.5/Wo x 0.3L x 2.5ml + 4 Wo x 3.5/Wo x 0.3L x 2.0ml) = 4.7 + 18.4 + 8.4 = 31.5 ml | **~30 ml** |
| Pure Zym | (14 Wo x 3.5/Wo x 0.3L x 1.0ml) = 14.7 ml | **~15 ml** |

**Kosten-Schaetzung:** Bei 1L-Flaschen reicht das Sortiment fuer ca. 30 Basilikum-Zyklen (Terra Grow) bzw. ca. 65 Zyklen (Pure Zym). Extrem kostenguenstig -- passend zu einem Kuechenkraut.

Bei 3 Aussaaten pro Jahr: ~90 ml Terra Grow, ~45 ml Pure Zym pro Jahr.

---

## 6. Basilikum-spezifische Praxis-Hinweise

### Substrat

- Durchlaessige, humusreiche Blumenerde, pH 5.8--6.2
- Topfgroesse: min. 1.5 L pro Pflanze, ideal 3--5 L fuer buschige Pflanzen
- Drainage-Loecher essentiell -- **Staunaesse ist der Killer Nr. 1** (Fusarium, Pythium)
- Perlite oder Sand untermischen fuer bessere Drainage (20--30% Anteil)
- Vorgeduengte Blumenerde: in den ersten 2--3 Wochen KEINEN zusaetzlichen Duenger geben

### Ernte-Technik (entscheidend fuer Pflanzenform)

- **Immer ueber einem Blattpaar schneiden** -- aus jedem Blattpaar treiben zwei neue Seitentriebe
- Nie mehr als 1/3 der Pflanze auf einmal ernten
- Einzelne Blaetter abzupfen statt ganzer Triebe = Pflanze wird kahl und duenn
- Morgenernte bevorzugt (hoechster Aromaoelgehalt vor Mittagshitze)
- Ab 6. Blattpaar das Entspitzen beginnen (foerdert Buschform)

### Bluetenunterdrueckung (Pinzieren)

- **Entscheidend fuer Aromaoelqualitaet:** Nach der Bluete sinkt der Gehalt aetherischer Oele deutlich
- Bluetenstaende sofort bei Erscheinen ausbrechen -- nicht erst warten bis sie offen sind
- Bei Indoor-Kultur: Photoperiode >14h verzoegert die Bluete (Kurztagspflanze)
- Konsequentes Pinzieren kann die Erntephase um 4--6 Wochen verlaengern

### Ueberduengung erkennen (WICHTIG!)

Basilikum zeigt Ueberduengung anders als Starkzehrer:

- **Grosse, waerige Blaetter mit wenig Duft** = zu viel Stickstoff (haeufigster Fehler!)
- **Schnelles, duennes Wachstum ("Vergeilen")** = zu viel N, zu wenig Licht
- **Blattrandnekrosen (braun-schwarz)** = pH zu niedrig (<5.8) -> Fe/Mn-Toxizitaet, NICHT Kaliummangel
- **Dunkelgruene, hart anfuehlende Blaetter** = N-Ueberschuss
- **Aromaverlust** = das sicherste Zeichen -- wenn Basilikum nicht mehr nach Basilikum riecht, war die Duengung zu hoch

**Gegenmassnahme:** 2--3x mit klarem Wasser durchgiessen, dann mit reduzierter Dosis (1.5 ml/L) weitermachen.

### Fusarium-/Pythium-Praevention

- **Substrat nie stauend nass halten** -- lieber einmal zu wenig als einmal zu viel giessen
- Giessen morgens, damit Substrat ueber den Tag abtrocknet
- Keine Erdreste von befallenen Pflanzen wiederverwenden
- Bei Fusarium-Verdacht (einseitige Welke, braune Staengelbasis): Pflanze sofort entfernen und entsorgen (NICHT kompostieren)
- Pure Zym hilft praeventiv: Enzyme bauen abgestorbene Wurzeln ab, die als Naehrboden fuer Pathogene dienen

### Mischkultur-Tipp

Basilikum und Tomate sind klassische Partner (Kompatibilitaets-Score 0.9):
- Aetherische Oele des Basilikums wehren Weisse Fliege ab
- Gleiche Waerme- und Wasserbeduerfnisse
- Tomate als Starkzehrer kann hoeheren EC vertragen -- bei gemeinsamer Bewaesserung das Basilikum separat giessen oder in eigenen Topf setzen

### Empfohlene Umgebungsparameter je Phase

| Phase | Temp Tag (degC) | VPD (kPa) | rH% (Tag) |
|-------|-----------------|-----------|-----------|
| GERMINATION | 22--28 | 0,4--0,8 | 80--90 |
| SEEDLING | 20--25 | 0,5--0,8 | 65--75 |
| VEGETATIVE | 22--28 | 0,8--1,2 | 55--65 |
| FLOWERING | 22--28 | 1,0--1,4 | 50--60 |
| HARVEST | 18--25 | 1,0--1,4 | 50--60 |

Quelle: `spec/knowledge/plants/ocimum_basilicum.md`, Abschnitt 2.2

### Wasserqualitaet

- Basilikum ist kalkvertraeglich -- Leitungswasser in Ordnung
- Bei chloriertem Wasser: 24h abstehen lassen (Chlor entgast, und Chlor inaktiviert die Enzyme im Pure Zym)
- Giesswasertemperatur 18--22 degC (kaltes Wasser unter 15 degC verursacht Wurzelstress)

---

## 7. Sicherheitshinweise & Ernte-Hygiene

### Pflanze

- **Ungiftig** -- Basilikum ist ein Speisekraut (ASPCA: safe for cats, dogs, horses)
- Konzentriertes Basilikum-aetherisches Oel kann fuer Katzen problematisch sein -- frische Pflanze ist unbedenklich, aetherische Oel-Produkte von Katzen fernhalten
- Keine Kontaktallergene, keine Pollenallergene

### Duengerprodukte

- Plagron Terra Grow: Nicht als gefaehrlich eingestuft, aber **nicht zum Verzehr geeignet**
- Plagron Pure Zym: Unbedenklich, enthaelt keine Hormone, Gentechnik oder tierische Bestandteile
- **Kinder:** Beide Produkte ausserhalb der Reichweite von Kindern aufbewahren
- **Hautkontakt:** Mit Wasser abspuelen
- **Augenkontakt:** Gruendlich mit Wasser ausspuelen

### Ernte-Sicherheit

- **1 Woche duengerfrei vor der letzten Ernte** empfohlen (Duengerreste auf Blaettern minimieren)
- Geerntete Blaetter vor dem Verzehr gruendlich waschen
- Bei den hier empfohlenen niedrigen Dosierungen ist das Risiko minimal, aber Hygiene ist immer sinnvoll

---

## 8. KA-Import-Daten

### 8.1 NutrientPlan

```json
{
  "name": "Basilikum (Sweet Basil) \u2014 Plagron Terra",
  "description": "Minimalistischer Nährstoffplan für Basilikum (Schwachzehrer). Nur 2 Produkte: Terra Grow + Pure Zym. Bewusst niedrige Dosierung \u2014 Überdüngung reduziert ätherische Öle um bis zu 28%. Einjährig, 18-Wochen-Zyklus.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["basilikum", "ocimum", "sweet-basil", "plagron", "terra", "erde", "kraeutergarten", "schwachzehrer", "indoor", "outdoor", "aroma"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 2,
    "preferred_time": "08:00",
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
  "notes": "Kein Dünger. Lichtkeimer: Samen nur andrücken, nicht bedecken. Bodentemperatur 20\u201325\u00b0C. Substrat feucht halten durch feines Sprühen. Pure Zym erst ab SEEDLING — Substrat bei Aussaat noch frisch, Enzym-Kontakt mit Keimlingen nicht nötig.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 1,
    "preferred_time": "08:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-keimung",
      "label": "Sprühwasser Keimung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein Dünger. Feiner Sprühstrahl, Samen nicht wegschwemmen.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.05}
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
  "npk_ratio": [1.0, 1.0, 1.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Vierteldosis Terra Grow (1.5 ml/L). Schwachzehrer \u2014 weniger ist mehr. Vorgedüngte Blumenerde liefert Grundversorgung für 2\u20134 Wochen. Pure Zym für Substratgesundheit.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsdüngung (Gießkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Vierteldosis + Pure Zym. Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 pH prüfen",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
    }
  ]
}
```

#### VEGETATIVE (Erntephase)

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 3,
  "week_start": 6,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Haupterntephase. Halbe Dosis Terra Grow (2.5 ml/L) \u2014 das ist die MAXIMALE Dosierung für Basilikum. Regelmäßiges Entspitzen stimuliert Verzweigung. Blütenansätze sofort entfernen. Dosierung NICHT erhöhen \u2014 Überdüngung reduziert Aromaölgehalt um bis zu 28%.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsdüngung (Gießkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Halbe Dosis Terra Grow + Pure Zym. NICHT überdosieren! Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 pH prüfen",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Reduzierter Terra Grow (2.0 ml/L). Blütenknospen ausbrechen für Blatternten-Modus. Kein Bloom-Dünger \u2014 wir wollen Blüte unterdrücken, nicht fördern. Indoor: Photoperiode >14h verzögert Blüte.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsdüngung reduziert (Gießkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Grow + Pure Zym. Kein Bloom-Dünger nötig.",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 2.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.3}
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
  "week_end": 18,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein Dünger. Letzte Ernte aller brauchbaren Blätter. 1 Woche düngerfrei vor Ernte empfohlen. Blätter waschen. Pflanze stirbt ab (einjährig). Substrat kann mit Pure Zym für nächste Aussaat vorbereitet werden.",
  "delivery_channels": [
    {
      "channel_id": "wasser-nur",
      "label": "Nur Wasser (düngerfrei)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein Dünger. Nur Wasser bis Pflanze entsorgt wird.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
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
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Ocimum basilicum | `spec/knowledge/plants/ocimum_basilicum.md` | `nutrient_plans` -> `species` (via edge) |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
3. Basilikum Pflanzendaten: `spec/knowledge/plants/ocimum_basilicum.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`
6. NCSU Extension -- Ocimum basilicum: https://plants.ces.ncsu.edu/plants/ocimum-basilicum/
7. Upstart Farmers -- Growing Hydroponic Basil: https://university.upstartfarmers.com/blog/hydroponic-basil
8. Johnny's Seeds -- Hydroponic Basil Guide: https://www.johnnyseeds.com/growers-library/herbs/basil/hydroponic-container-basil-guide.html

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
