# Naehrstoffplan: Petersilie (1. Jahr Blattkultur) -- Plagron Terra

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Petroselinum crispum (Mittelzehrer, biennial -- hier 1. Jahr Blattkultur)
> **Produkte:** Plagron Terra Grow, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_grow.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/plants/petroselinum_crispum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Petersilie (1. Jahr Blattkultur) -- Plagron Terra | `nutrient_plans.name` |
| Beschreibung | Saisonplan fuer Petersilie (Petroselinum crispum) im 1. Anbaujahr (Blattkultur). Plagron Terra-Linie mit 2 Produkten: Terra Grow + Pure Zym. Mittelzehrer mit halber Herstellerdosis. Zweijaerig, aber nur 1. Jahr fuer Blatternte nutzbar -- im 2. Jahr schiesst die Pflanze und wird unbrauchbar (bitter, holzig). Bedeckt saeen (Furanocumarine in Samenschale), notorisch langsame Keimung (3--4 Wochen). Indoor-Vorkultur ab Maerz, Freiland ab Mai, kontinuierliche Blatternte Mai--November. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | petersilie, petroselinum, parsley, plagron, terra, erde, kraeutergarten, mittelzehrer, outdoor, indoor, biennale | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (1. Jahr Blattkultur, kein Neustart -- 2. Jahr unbrauchbar) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 08:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 3-Tage-Intervall als Basis. Petersilie mag gleichmaessig feuchte Erde, vertraegt aber kurze Trockenperioden besser als Staunaesse. In GERMINATION auf taegliches leichtes Spruehen umstellen (Override 1 Tag). Im Hochsommer bei Hitze alle 2 Tage. In DORMANCY (Spaetherbst) auf 5 Tage reduzieren.

---

## 2. Phasen-Mapping

Petersilie (Petroselinum crispum) ist botanisch zweijaerig: Im 1. Jahr bildet sie eine Blattrosette (Erntephase), im 2. Jahr schiesst sie, bildet einen Bluetenstiel und wird fuer die Blatternte unbrauchbar (Blaetter werden bitter und hart). Dieser Plan deckt ausschliesslich das 1. Anbaujahr ab. Aussaat ab Maerz indoor, Ernte Mai--November, Saisonende mit erstem starkem Frost.

**Besonderheit Keimung:** Petersilie hat eine extrem langsame Keimung (14--28 Tage!). Die Samenschale enthaelt keimhemmende Furanocumarine -- bedeckt saeen (0.5 cm), da der Bodenkontakt fuer die Keimung entscheidend ist (Licht ist kein limitierender Faktor). 24h Einweichen vor Aussaat verkuerzt die Keimzeit um ca. 7 Tage.

| Petersilie-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|------------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--4 | Maerz | Bedeckt saeen (0.5 cm, Furanocumarine in Samenschale), 14--28 Tage Keimzeit! Indoor bei 18--22 degC. Kein Duenger. | false |
| Saemling | SEEDLING | 5--10 | April--Mitte Mai | Pikierte Jungpflanzen. Viertel-Dosis Terra Grow. Ab Mitte April Abhaertung. Auspflanzung nach Eisheiligen. | false |
| Vegetatives Wachstum (Blattrosette) | VEGETATIVE | 11--24 | Mitte Mai--Mitte August | Hauptwachstum der Blattrosette. Halbe Dosis Terra Grow + Pure Zym. Kontinuierliche Blatternte moeglich. | false |
| Erntephase (Spaetsommer/Herbst) | HARVEST | 25--36 | Mitte August--Oktober | Fortgesetzte Blatternte bei reduzierter Duengung. Wachstum verlangsamt sich. Letzte Ernte vor Frost. | false |
| Saisonende / Winterruhe | DORMANCY | 37--44 | November--Dezember | Keine Duengung. Pflanze kann mit Vlies-Schutz ueberwintern (bis -8 degC), wird aber im 2. Jahr unbrauchbar. | false |

**Nicht genutzte Phasen:**
- **FLOWERING** entfaellt (Bluetenbildung erst im 2. Jahr -- dann ist die Pflanze fuer Blatternte unbrauchbar)
- **FLUSHING** entfaellt (moderate Dosierung, keine Salzbelastung)

**Annueller Nutzungszyklus:** Obwohl botanisch biennial, wird Petersilie hier als einjaehrige Blattkultur gefuehrt. Kein `cycle_restart_from_sequence`. Nach Saisonende neue Aussaat starten.

**Lueckenlos-Pruefung:** 4 + 6 + 14 + 12 + 8 = 44 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Mittelzehrer -- moderate Volumina.

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Spruehwasser Keimung | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Substrat gleichmaessig feucht halten (Abdeckung mit Folie/Vlies). Nicht austrocknen lassen -- bei Petersilie ist das die haeufigste Ursache fuer Keimversagen. | `delivery_channels.notes` |
| method_params | drench (spray), 0.05 L pro Giessen | `delivery_channels.method_params` |

### 3.2 Naehrloesung Wachstum

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-wachstum | `delivery_channels.channel_id` |
| Label | Wachstumsduengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Grow + Pure Zym ins Giesswasser. Reihenfolge: Terra Grow -> Pure Zym -> pH pruefen. Terra Grow puffert auf pH 6.0--6.5 (Selbstpufferung). Ziel-pH 5.8--6.2 (Steckbrief-Optimum). | `delivery_channels.notes` |
| method_params | drench, 0.3 L pro Pflanze (bei Topfkultur bis zur Drainage) | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Fuer DORMANCY (minimal, nur bei Trockenheit). | `delivery_channels.notes` |
| method_params | drench, 0.2 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Petersilie

Petersilie ist ein Mittelzehrer -- sie vertraegt mehr als Schwachzehrer wie Basilikum, aber deutlich weniger als Starkzehrer wie Tomaten. Ziel-EC der Gesamtloesung: **0.5--0.8 mS/cm** (inkl. Basis-Wasser). Herstellerempfehlung halbiert. Ueberduengung fuehrt zu weichem, geschmacksarmem Laub und erhoehter Pilzanfaelligkeit (Septoria, Falscher Mehltau).

**pH-Hinweis:** Terra Grow puffert die Naehrloesung auf pH 6.0--6.5 (Selbstpufferung). Petersilie bevorzugt pH 5.8--6.2 (Steckbrief). Aktive pH-Absenkung ist nicht noetig.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Grow (3-1-3) | 0.08 | 20 | Saemling, Vegetativ, Ernte |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Ernte (durchgehend) |

**Warum kein Terra Bloom?** Petersilie wird im 1. Jahr als Blattkultur angebaut -- die Bluetenbildung ist unerwuenscht (macht die Blaetter bitter). Terra Grow mit N-betontem 3-1-3-Profil foerdert Blattwachstum. Kein Bloom-Duenger noetig, da wir keine Bluete wollen.

### 4.1 GERMINATION -- Keimung (Woche 1--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Samen bedeckt saeen (0,5 cm) -- keimhemmende Furanocumarine in der Samenschale erfordern Bodenkontakt, Licht ist kein entscheidender Faktor. 24h in lauwarmem Wasser einweichen vor Aussaat (loest Furanocumarine, verkuerzt Keimdauer um 5--10 Tage). Temperatur 18--22 degC. Keimdauer 14--28 Tage -- Geduld! Substrat gleichmaessig feucht halten, Abdeckung mit Folie oder Vlies. NICHT austrocknen lassen -- Samen keimen nicht nach! Kein Duenger. | `phase_entries.notes` |
| Giessplan-Override | Intervall 1 Tag (leichtes Spruehen) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** 0.00 + ~0.4 (Wasser) = **~0.4 mS/cm** (nur Wasser)

### 4.2 SEEDLING -- Saemling (Woche 5--10)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 10 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren ab 2. echtem Blattpaar in Einzeltoepfe (9 cm). Petersilie bildet eine Pfahlwurzel -- tiefe Toepfe verwenden! Kuehle Temperaturen (15--18 degC) fuer kompakten Wuchs. Ab Mitte April Abhaertung draussen beginnen. Auspflanzung nach Eisheiligen (Mitte Mai). Alle 14 Tage duengen. Pure Zym wird bewusst erst ab VEGETATIVE eingesetzt. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 1.5 (Viertel-Dosis) |
| Pure Zym ml/L | -- (noch nicht) |

**EC-Budget:** 0.12 (TG 1.5ml) + ~0.4 (Wasser) = **~0.52 mS/cm** -- im Mittelzehrer-Bereich

### 4.3 VEGETATIVE -- Blattrosette (Woche 11--24)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 11 | `phase_entries.week_start` |
| week_end | 24 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Halbe Dosis Terra Grow (2.5 ml/L) + Pure Zym. Hauptwachstum der Blattrosette. N-betonte Duengung foerdert Blattproduktion. Kontinuierliche Blatternte moeglich: aeussere Blaetter von aussen nach innen ernten, Herzblatter stehen lassen. Bei konsequenter Ernte bleibt die Rosette kompakt und produktiv. Alle 14 Tage duengen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.5 (halbe Dosis) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.20 (TG 2.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.60 mS/cm** -- Mittelzehrer-Optimum

### 4.4 HARVEST -- Erntephase Spaetsommer/Herbst (Woche 25--36)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 25 | `phase_entries.week_start` |
| week_end | 36 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (3, 1, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Reduzierter Terra Grow (2.0 ml/L) + Pure Zym. Fortgesetzte Blatternte bei nachlassendem Wachstum. Ab September alle 3 Wochen duengen statt alle 14 Tage. Petersilie vertraegt leichte Froeste bis -8 degC -- Ernteperiode laesst sich mit Vlies-Abdeckung bis in den November verlaengern. Letzte grosse Ernte vor erstem starken Frost. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-wachstum**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.0 |
| Terra Grow ml/L | 2.0 (reduziert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.16 (TG 2.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.56 mS/cm** -- reduziert fuer Spaetsaison

### 4.5 DORMANCY -- Saisonende / Winterruhe (Woche 37--44)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 37 | `phase_entries.week_start` |
| week_end | 44 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Petersilie kann mit Winterschutz (Vlies, Reisig, Mulch) ueberwintern -- sie uebersteht Froeste bis -8 degC. ABER: Im 2. Jahr schiesst sie (Bluetenstiel), die Blaetter werden bitter und holzig. Daher ist Ueberwintern fuer die Blatternte nicht sinnvoll. Empfehlung: Restliche Blaetter ernten, Pflanze entfernen, im Fruehjahr neue Aussaat starten. | `phase_entries.notes` |
| Giessplan-Override | Intervall 5 Tage (minimal, nur bei Trockenheit) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.0 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser)

---

## 5. Jahresplan (Monat-fuer-Monat)

Aussaat Anfang Maerz indoor, Ernte Mai--November, Saisonende Dezember.

| Monat | KA-Phase | Terra Grow ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|-----------------|---------------|-----------------|----------|
| Maerz | GERMINATION | -- | -- | 0.4 | taeglich (Spruehen) |
| April | GERM->SEED | -- -> 1.5 | -- | 0.4->0.5 | spray -> alle 14d |
| Mai | SEEDLING->VEG | 1.5->2.5 | -- -> 1.0 | 0.5->0.6 | alle 14d |
| Juni | VEGETATIVE | 2.5 | 1.0 | 0.6 | alle 14d |
| Juli | VEGETATIVE | 2.5 | 1.0 | 0.6 | alle 14d |
| August | VEG->HARVEST | 2.5->2.0 | 1.0 | 0.6->0.5 | alle 14d |
| September | HARVEST | 2.0 | 1.0 | 0.5 | alle 21d |
| Oktober | HARVEST | 2.0 | 1.0 | 0.5 | alle 21d |
| November | HAR->DOR | 2.0->-- | 1.0->-- | 0.5->0.4 | alle 21d->-- |
| Dezember | DORMANCY | -- | -- | 0.4 | minimal |

```
Monat:        |Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|
KA-Phase:     |GER|G→S|S→V|VEG|VEG|V→H|HAR|HAR|H→D|DOR|
Terra Grow:   |---|#--|##-|===|===|==#|##-|##-|#--|---|
Pure Zym:     |---|---|===|===|===|===|===|===|#--|---|

Legende: --- = nicht verwendet, #-- = Viertel-Dosis,
         ##- = halbe Dosis / reduziert, === = volle Phase-Dosis
         ==#/##- = auslaufend/reduziert
```

### Jahresverbrauch (geschaetzt)

Bei einer Petersilienpflanze im 3L-Topf/Beet, 0.3 L Giessloessung pro Duengung:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Grow | (3 Dueng x 1.5ml/L x 0.3L + 7 Dueng x 2.5ml/L x 0.3L + 6 Dueng x 2.0ml/L x 0.3L) = 1.35 + 5.25 + 3.60 = 10.2 ml | **~10 ml** |
| Pure Zym | (13 Dueng x 1.0ml/L x 0.3L) = 3.9 ml | **~4 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche Terra Grow reicht fuer ca. 100 Petersilie-Saisons. Sinnvoll nur in Kombination mit anderen Pflanzen.

---

## 6. Petersilie-spezifische Praxis-Hinweise

### Substrat

- Humusreiche, durchlaessige Gartenerde, pH 5.8--6.2
- Pfahlwurzel -- tiefe Toepfe (min. 20 cm) verwenden
- Topfgroesse: min. 3 L pro Pflanze, ideal 5 L
- Drainage essentiell -- Staunaesse foerdert Wurzelfaeule
- Vorgeduengte Blumenerde: in den ersten 3--4 Wochen keinen zusaetzlichen Duenger

### Keimung (der kritischste Punkt)

- **Notorisch langsame Keimung:** 14--28 Tage sind normal -- GEDULD!
- Samenschale enthaelt keimhemmende Furanocumarine
- **Trick:** 24h in lauwarmem Wasser einweichen vor Aussaat (verkuerzt Keimzeit um ~7 Tage)
- **Bedeckt saeen:** Samen 0.5 cm mit Erde bedecken (im Gegensatz zu Basilikum!) -- Furanocumarine in der Samenschale erfordern Bodenkontakt
- Substrat NICHT austrocknen lassen -- gleichmaessige Feuchte ist entscheidend
- Abdeckung mit Folie/Vlies haelt Feuchtigkeit und Waerme
- Temperatur 18--22 degC optimal
- Bei Austrocknung waehrend der Keimung: Neuaussaat noetig (Samen keimen nicht nach!)

### Ernte-Technik

- **Immer aeussere Blaetter von aussen nach innen ernten** -- Herzblatter (innerste) stehen lassen
- Ganze Stiele bodennah abschneiden (nicht nur Blattspitzen)
- Nie mehr als 1/3 der Rosette auf einmal ernten
- Regelmaessige Ernte stimuliert Nachwuchs
- Morgenernte bevorzugt (hoechster Aromaoelgehalt)
- Petersilie kann gewaschen, gehackt und eingefroren werden (besser als Trocknen)

### 2. Jahr -- Warum unbrauchbar?

- Im 2. Jahr bildet Petersilie nach Vernalisation (Kaltphase Winter) einen Bluetenstiel
- Blaetter werden bitter, hart und holzig
- Pflanze investiert alle Energie in Bluete und Samenproduktion
- **Empfehlung:** Im Fruehjahr neue Aussaat starten, 2.-Jahr-Pflanze entfernen
- Einziger Grund fuer 2. Jahr: Saatgut-Gewinnung (Selbstbestaeubung moeglich)

### Mischkultur-Tipps

- Gute Partner: Tomaten, Schnittlauch, Radieschen, Erdbeeren
- Schlechte Partner: Salat (Konkurrenz), Dill (hemmt Petersilie -- Allelopathie)
- Petersilie wehrt durch aetherische Oele einige Schaedlinge ab (besonders an Rosen)

### Schaedlinge und Krankheiten

- **Moehrenfliege (Psila rosae):** Hauptschaedling! Larven fressen an der Pfahlwurzel. Kulturschutznetz ab Aussaat verwenden.
- **Blattlaeuse:** Ab Fruehling moeglich. Kaliseife-Spritzung.
- **Septoria-Blattflecken:** Gelbe/braune Flecken auf Blaettern. Befallene Blaetter entfernen, nicht ueber Kopf giessen.
- **Falscher Mehltau:** Gelblich-gruene Blattflecken, Unterseite grauer Belag. Luftzirkulation verbessern.

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Petersilie (1. Jahr Blattkultur) \u2014 Plagron Terra",
  "description": "Saisonplan f\u00fcr Petersilie (Petroselinum crispum) im 1. Anbaujahr (Blattkultur). Plagron Terra-Linie mit 2 Produkten. Mittelzehrer mit halber Herstellerdosis. Zweij\u00e4hrig, aber nur 1. Jahr nutzbar \u2014 im 2. Jahr schie\u00dft die Pflanze. Bedeckt s\u00e4en (Furanocumarine in Samenschale), langsame Keimung (3\u20134 Wochen). Kontinuierliche Blatternte Mai\u2013November.",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["petersilie", "petroselinum", "parsley", "plagron", "terra", "erde", "kr\u00e4utergarten", "mittelzehrer", "outdoor", "indoor", "biennale"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "08:00",
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
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Bedeckt s\u00e4en: Samen 0.5 cm mit Erde bedecken (Furanocumarine in Samenschale erfordern Bodenkontakt). 24h einweichen vor Aussaat. Temperatur 18\u201322 \u00b0C. Keimdauer 14\u201328 Tage \u2014 Geduld! Substrat gleichm\u00e4\u00dfig feucht halten.",
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
      "label": "Spr\u00fchwasser Keimung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Substrat feucht halten, nicht austrocknen lassen.",
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
  "week_start": 5,
  "week_end": 10,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Viertel-Dosis Terra Grow (1.5 ml/L). Pikieren ab 2. echtem Blattpaar. Tiefe T\u00f6pfe wegen Pfahlwurzel. Ab Mitte April Abh\u00e4rtung. Alle 14 Tage d\u00fcngen. Pure Zym erst ab VEGETATIVE.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Grow Viertel-Dosis. Mittelzehrer \u2014 moderate Versorgung.",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_grow_key>", "ml_per_liter": 1.5, "optional": false}
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
  "week_end": 24,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Halbe Dosis Terra Grow (2.5 ml/L) + Pure Zym. Hauptwachstum der Blattrosette. Kontinuierliche Blatternte: \u00e4u\u00dfere Bl\u00e4tter von au\u00dfen nach innen, Herzbl\u00e4tter stehen lassen. Alle 14 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Halbe Dosis Terra Grow + Pure Zym. Reihenfolge: Terra Grow \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
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

#### HARVEST

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "harvest",
  "sequence_order": 4,
  "week_start": 25,
  "week_end": 36,
  "is_recurring": false,
  "npk_ratio": [3.0, 1.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Reduzierter Terra Grow (2.0 ml/L) + Pure Zym. Fortgesetzte Blatternte bei nachlassendem Wachstum. Ab September alle 3 Wochen d\u00fcngen. Petersilie vertr\u00e4gt leichte Fr\u00f6ste bis -8 \u00b0C \u2014 Ernteperiode mit Vlies verl\u00e4ngerbar.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-wachstum",
      "label": "Wachstumsd\u00fcngung reduziert (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Reduzierter Terra Grow + Pure Zym. Sp\u00e4tsaison-Dosierung.",
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

#### DORMANCY

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "dormancy",
  "sequence_order": 5,
  "week_start": 37,
  "week_end": 44,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Petersilie kann \u00fcberwintern (bis -8 \u00b0C mit Vlies), wird aber im 2. Jahr unbrauchbar (schie\u00dft, Bl\u00e4tter bitter). Empfehlung: Restbl\u00e4tter ernten, Pflanze entfernen, neue Aussaat im Fr\u00fchjahr.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 5,
    "preferred_time": "08:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Saisonende)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Nur bei Trockenheit gie\u00dfen.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.2}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Grow | `spec/knowledge/products/plagron_terra_grow.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Petroselinum crispum | `spec/knowledge/plants/petroselinum_crispum.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Haustier-Warnung:** Petersilie ist in groesseren Mengen giftig fuer Katzen und Hunde (ASPCA: toxic). Giftstoff: Furanocumarine (Psoralen, Bergapten). Symptom: Photosensibilisierung. Petersilie-Toepfe ausserhalb der Reichweite von Haustieren aufstellen.
- **Kinder:** Als Kuechenkraut in normalen Mengen unbedenklich. Schwangere sollten grosse Mengen meiden (uterustonisierend).
- **Kontaktallergen:** Bei intensivem Hautkontakt + Sonnenlicht koennen Furanocumarine photoallergische Reaktionen ausloesen (Wiesendermatitis). Handschuhe beim Ernten grosser Mengen empfohlen.

### Verwechslungsgefahr

- **KRITISCH:** Petersilie kann mit der giftigen Hundspetersilie (Aethusa cynapium) oder dem Gefleckten Schierling (Conium maculatum) verwechselt werden! Nur eigenes, sicher bestimmtes Saatgut verwenden. Keine Wildsammlung!

### Duengemittel

- Plagron-Konzentrate nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren

---

## Quellenverzeichnis

1. Plagron Terra Grow Produktdaten: `spec/knowledge/products/plagron_terra_grow.md`
2. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
3. Petersilie Pflanzendaten: `spec/knowledge/plants/petroselinum_crispum.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
