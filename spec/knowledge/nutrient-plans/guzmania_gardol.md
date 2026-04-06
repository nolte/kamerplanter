# Naehrstoffplan: Guzmania lingulata -- Gardol Gruenpflanzenduenger

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Guzmania lingulata (light_feeder, perennial/monokarp, Indoor/Orchideensubstrat)
> **Produkt:** Gardol Gruenpflanzenduenger NPK 6-4-6 (Bauhaus)
> **Erstellt:** 2026-03-01
> **Quellen:** spec/knowledge/plants/guzmania_lingulata.md, spec/knowledge/products/gardol_gruenpflanzenduenger.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Guzmania lingulata -- Gardol Gruenpflanzenduenger | `nutrient_plans.name` |
| Beschreibung | Lebenszyklus-Plan fuer Guzmania lingulata (Bromelie) in Orchideensubstrat. Einzelduenger-Konzept mit Gardol Gruenpflanzenduenger (NPK 6-4-6) auf 1/4-Dosis reduziert. Monokarper Lebenszyklus: Kindel-Etablierung, vegetatives Wachstum (~1 Jahr), Bluete, Seneszenz mit Kindel-Bildung. Kein saisonaler Zyklus -- linearer Durchlauf (~2 Jahre). Ausschliesslich weiches Wasser (Regenwasser/destilliert) verwenden. | `nutrient_plans.description` |
| Substrattyp | ORCHID_BARK | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | guzmania, bromelie, epiphyt, zimmerpflanze, gardol, orchideensubstrat, indoor, schwachzehrer, monokarp | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | 100 (ausschliesslich weiches Wasser: Regenwasser, destilliert oder RO) | `nutrient_plans.water_mix_ratio_ro_percent` |

<!-- Weiches Wasser ist PFLICHT bei Bromelien: Kalkablagerungen verstopfen die Trichome (Saugschuppen) irreversibel. Leitungswasser ist nur bei sehr weichem Wasser (<5 dH) akzeptabel. Bei RO-/Regenwasser ist KEIN CalMag-Supplement noetig -- Bromelien sind extreme Schwachzehrer und benoetigen minimales Ca/Mg. -->
| Zyklus-Neustart ab Sequenz | null (kein Neustart -- monokarper Lebenszyklus; Mutterpflanze stirbt nach Bluete, Kindel = neue Pflanzeninstanz) | `nutrient_plans.cycle_restart_from_sequence` |

> **Substratunabhaengig:** Die EC-Zielwerte in diesem Plan sind fuer Erdsubstrat (SOIL) kalibriert. Bei Verwendung anderer Substrate (Coco, Hydro) werden die Werte automatisch ueber den SubstrateEcAdapter angepasst.

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 10 | `watering_schedule.interval_days` |
| Uhrzeit | 09:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** Der Basis-Giessplan bezieht sich auf die Substratbewaesserung (DRENCH). Die Trichterbewaesserung (primaere Naehrstoffzufuhr) erfolgt ueber den separaten Delivery Channel "trichter-duengung" alle 28 Tage mit Duengerloesung bzw. Wasseraustausch alle 4-6 Wochen. **KEIN Wasser in den Trichter bei Raumtemperatur unter 18 C!** Stehendes Wasser im Trichter bei kuehlen Temperaturen fuehrt zu Trichterfaeule (Heart Rot) -- die haeufigste Todesursache bei Guzmania.

---

## 2. Phasen-Mapping

Guzmania lingulata ist eine **monokarpe** tropische Bromelie mit linearem Lebenszyklus. Die Mutterpflanze blueht einmalig und stirbt danach ab; Kindel (Offsets/Pups) setzen den Bestand fort. Die Guzmania-spezifischen Lebensphasen werden auf das KA-PhaseName-Enum wie folgt gemappt:

| Guzmania-Phase | PhaseName (Enum) | Wochen | Zeitraum | Begruendung | is_recurring |
|----------------|-----------------|--------|----------|-------------|-------------|
| Kindel-Etablierung | GERMINATION | 1--8 | Nach Abtrennung vom Mutterstock | Frisch abgetrenntes Kindel etabliert eigene Wurzeln, keine Duengung. GERMINATION als Platzhalter fuer vegetative Vermehrung (kein separates PROPAGATION-Enum). | false |
| Vegetatives Wachstum | VEGETATIVE | 9--60 | ~1 Jahr aktives Wachstum | Hauptwachstumsphase. Pflanze baut Blattrosette auf (12+ Blaetter bis Bluetereife). Minimale Duengung (1/4-Dosis Gardol). Ethylen-Induktion am Ende dieser Phase moeglich (W50--60): reifer Apfel in versiegelte Tuete mit Pflanze, 10 Tage -- muss VOR Bluetebeginn erfolgen. | false |
| Bluete | FLOWERING | 61--76 | 4 Monate | Bluetenstand entfaltet sich (2-4 Monate sichtbar). Minimale Duengung beibehalten. | false |
| Seneszenz / Kindel-Bildung | DORMANCY | 77--104 | ~7 Monate | Mutterpflanze stirbt langsam ab, bildet 1-5 Kindel. Keine Duengung. Kindel individuell versorgen, sobald abgetrennt. DORMANCY als Platzhalter fuer terminale Seneszenz (kein SENESCENCE-Enum). | false |

**Nicht genutzte Phasen:**
- **SEEDLING:** Keine separate juvenile Phase -- Kindel gehen direkt in vegetatives Wachstum ueber.
- **FLUSHING:** Kein aktives Flushing noetig (Orchideensubstrat, extrem niedrige Duengerdosen).
- **HARVEST:** Keine Ernte (Zierpflanze).

**Monokarper Lebenszyklus:** Alle Phasen sind `is_recurring: false`. Nach Abschluss der DORMANCY-Phase (Woche 104) ist der Lebenszyklus der Mutterpflanze beendet. Abgetrennte Kindel starten als neue Pflanzeninstanzen mit eigenem Naehrstoffplan (erneut bei GERMINATION Woche 1). `cycle_restart_from_sequence: null`.

**Lueckenlos-Pruefung:** 1--8 | 9--60 | 61--76 | 77--104 (8 + 52 + 16 + 28 = 104 Wochen, keine Luecken)

---

## 3. Delivery Channels

Guzmania hat als Bromelie eine einzigartige Naehrstoffaufnahme ueber drei Wege: Trichter (Tank/Rosette), Blattspruehung (Trichome) und Substratbewaesserung (Verankerungswurzeln). Dies erfordert drei separate Delivery Channels.

### 3.1 Trichter-Duengung (Primaerer Kanal)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | trichter-duengung | `delivery_channels.channel_id` |
| Label | Trichter-Duengung (Rosettentank) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Primaere Naehrstoffzufuhr ueber den zentralen Rosettentrichter. Duengerloesung (1 ml/L Gardol in weichem Wasser) ca. 50 ml in den Trichter fuellen (1/4 voll). Trichterwasser alle 4-6 Wochen komplett austauschen (kippen, ausspuelen, frisch befuellen) um Bakterien-/Algenbildung zu vermeiden. KEIN Trichterwasser bei Raumtemperatur unter 18 C! Ausschliesslich kalkfreies Wasser verwenden -- Kalkablagerungen verstopfen die Trichome irreversibel. | `delivery_channels.notes` |

#### Trichter-Parameter

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Duengung (L) | 0.05 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 50 ml Duengerloesung pro Trichter-Befuellung (1/4 des Trichtervolumens). Bei sehr kleinen Kindeln 20-30 ml, bei grossen adulten Pflanzen bis 80 ml.

### 3.2 Blatternaehrung (Sekundaerer Kanal)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | blatternaehrung | `delivery_channels.channel_id` |
| Label | Blatternaehrung (Foliar Spray) | `delivery_channels.label` |
| Methode | FOLIAR | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Sekundaere Naehrstoffzufuhr ueber die Blattoberflaeche (Trichome). Stark verduennte Duengerloesung (0,5 ml/L Gardol) fein auf Blaetter spruehen. Nicht auf den Bluetenstand spruehen (Fleckenbildung). Bromelien koennen Naehrstoffe sehr effektiv ueber ihre Saugschuppen (Trichome) aufnehmen. Methode geeignet als Alternative wenn Trichter leer gehalten wird (Winter, kuehle Bedingungen). Nach dem Spruehen sicherstellen, dass keine stehenden Tropfen auf der Blattoberflaeche verbleiben -- bei geringer Luftzirkulation koennen stehende Wasserreste zu Blattflecken (Helminthosporium) fuehren. Am besten morgens spruehen, damit Blaetter tagsuebers abtrocknen. | `delivery_channels.notes` |

#### Foliar-Parameter

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | foliar | `method_params.method` |
| Volumen pro Spruehung (L) | 0.02 | `method_params.volume_per_spray_liters` |

### 3.3 Wasser Pur (Substratbewaesserung)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Substratbefeuchtung) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Substratbewaesserung ohne Duenger. Orchideensubstrat nur leicht feucht halten -- niemals nass. Die Wurzeln dienen primaer der Verankerung, nicht der Naehrstoffaufnahme. Substrat zwischen den Wassergaben leicht antrocknen lassen. Kleines Volumen, da Orchideensubstrat wenig Wasser speichert. Ausschliesslich weiches Wasser verwenden. | `delivery_channels.notes` |

#### Drench-Parameter

| Feld | Wert | KA-Feld |
|------|------|---------|
| Methode | drench | `method_params.method` |
| Volumen pro Giessen (L) | 0.10 | `method_params.volume_per_feeding_liters` |

**Hinweis:** 100 ml weiches Wasser fuer Substratbefeuchtung. Bei kleinen Kindeln (8 cm Topf) 30-50 ml, bei grossen Pflanzen (14+ cm Topf) 100-150 ml.

---

## 4. Dosierung pro Phase

### EC-Beitrag Gardol Gruenpflanzenduenger (Vierteldosis)

Geschaetzter EC-Beitrag: **~0,06 mS/cm pro ml/L** (Herstellerangabe fehlt, Schaetzung basierend auf NPK 6-4-6 und mineralischer Formulierung).

| Dosierung | ml/L | EC-Beitrag (geschaetzt) | Eignung fuer Guzmania |
|-----------|------|-------------------------|------------------------|
| 1/4 Dosis (Trichter) | 1,0 | ~0,06 mS/cm | Standard -- maximale Dosierung fuer Bromelien |
| 1/8 Dosis (Foliar) | 0,5 | ~0,03 mS/cm | Blattspreuelung -- extra verduennt |
| 1/2 Dosis | 2,0 | ~0,12 mS/cm | ZU STARK -- Verbrennungsgefahr bei Bromelien |
| Volle Dosis | 4,0 | ~0,24 mS/cm | GIFTIG fuer Bromelien -- niemals verwenden |

**Hinweis:** Bromelien sind extreme Schwachzehrer (Epiphyten -- natuerlich auf Naehrstoffarmut eingestellt). **Maximal 1/4 der Herstellerangabe verwenden.** Der Ziel-EC der Duengerloesung liegt bei ~0,3 mS/cm (inkl. Basis-Wasser-EC von ~0,0--0,1 mS/cm bei RO/Regenwasser). Ueberdüngung fuehrt zu Wurzelfaeule, Blattverbrennungen und Trichom-Schaeden.

**Optimaler Duenger:** Ein Orchideenduenger (z.B. COMPO Orchideenduenger NPK 3-4-5) waere ideal fuer Bromelien, da er bereits schwaecher konzentriert ist. Gardol Gruenpflanzenduenger auf 1/4-Dosis ist ein akzeptabler Ersatz, aber nicht die erste Wahl.

**pH-Hinweis Trichteranwendung:** Das Gardol-Produktdatenblatt nennt einen moeglichen organischen Stickstoffanteil (3% org. N von gesamt 6% N, aus Community-Quellen, nicht offiziell bestaetigt). Falls vorhanden, koennte Harnstoff-N bei Trichteranwendung ueber Ammonisierung den pH im stehenden Trichterwasser leicht anheben (>6,5), was den Bromelie-Optimum-Bereich 5,0--6,0 verlassen wuerde. Bei regelmaessigem Trichterwasseraustausch (alle 4--6 Wochen) ist das Risiko gering, da die Verweilzeit kurz und die Dosis minimal ist. Trotzdem: bei sichtbarer Kalkablagerung oder pH-Problemen Orchideenduenger (rein mineralisch, pH-angepasst) vorziehen.

### 4.1 GERMINATION -- Kindel-Etablierung (Woche 1--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 1 | `phase_entries.sequence_order` |
| week_start | 1 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Frisch abgetrenntes Kindel nur mit weichem Wasser versorgen. Substrat (Orchideenrinde/Kokosfaser + Perlite) leicht feucht halten, nie nass. Trichter minimal befuellen (20-30 ml). 10-Tage-Intervall fuer Substrat. Hohe Luftfeuchtigkeit (60-80%) foerdert Bewurzelung. Kindel erst abtrennen wenn es 1/3-1/2 der Muttergroesse erreicht hat und eigene Wurzeln zeigt. Waerme 22-27 C optimal. | `phase_entries.notes` |
| Giessplan-Override | Intervall 10 Tage (vorsichtig, kleines Kindel; Substrat zwischen den Gaben leicht antrocknen lassen) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, Nur-Wasser-Channel fuer Giessplan + Trichter

| Feld | Wert |
|------|------|
| channel_id | wasser-pur |
| application_method | drench |
| target_ec_ms | null (keine Duengung, weiches Wasser EC ~0,0-0,1 mS/cm)  |
| reference_ec_ms | null (keine Duengung, weiches Wasser EC ~0,0-0,1 mS/cm)  |
| target_ph | 5.5 (Substrat-pH-Optimum fuer Bromelien, nicht Giesswasser-pH) |
| fertilizer_dosages | [] (leer) |

### 4.2 VEGETATIVE -- Vegetatives Wachstum (Woche 9--60)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 60 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 1, 1) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 20 (aus Duengerspuren, nicht gezielt supplementiert) | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 10 (aus Duengerspuren, nicht gezielt supplementiert) | `phase_entries.magnesium_ppm` |
| Eisen (ppm) | 1.0 (aus Gardol-Spurenelementen, Steckbrief-Richtwert Vegetativ/Bluete) | `phase_entries.iron_ppm` |
| Hinweise | 1/4-Dosis Gardol (1 ml/L) alle 28 Tage ueber Trichter oder als Blattduengung. NPK-Verhaeltnis 1:1:1 -- Gardol 6-4-6 liefert effektiv 1,5:1:1,5, fuer Bromelien akzeptabel (kein uebermassiger N-Push bei dieser Mikrodosis). EC-Ziel ~0,3 mS/cm Gesamtloesung. Ca/Mg-Bedarf minimal (20/10 ppm) -- wird durch Duengerspuren weitgehend gedeckt, kein Supplement noetig. Trichterwasser alle 4-6 Wochen komplett austauschen. KEIN Trichterwasser unter 18 C. In den Wintermonaten (November-Februar) Duengung pausieren, auch wenn die Pflanze in VEGETATIVE bleibt -- Bromelien folgen keinem strikten saisonalen Zyklus, aber reduziertes Winterlicht erfordert Duengepause. | `phase_entries.notes` |

**Delivery Channel: trichter-duengung (primaer)**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.3  |
| reference_ec_ms | 0.3  |
| target_ph | 5.5 (Substrat-pH-Optimum) |
| Gardol ml/L | 1.0 (1/4-Dosis) |
| EC-Beitrag | ~0,06 mS/cm |
| Gardol optional | false |

**Delivery Channel: blatternaehrung (alternativ)**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.2  |
| reference_ec_ms | 0.2  |
| target_ph | 5.5 |
| Gardol ml/L | 0.5 (1/8-Dosis) |
| EC-Beitrag | ~0,03 mS/cm |
| Gardol optional | true |

### 4.3 FLOWERING -- Bluete (Woche 61--76)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 61 | `phase_entries.week_start` |
| week_end | 76 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (1, 2, 1) | `phase_entries.npk_ratio` |
| Calcium (ppm) | 20 | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | 15 | `phase_entries.magnesium_ppm` |
| Eisen (ppm) | 1.0 (aus Gardol-Spurenelementen) | `phase_entries.iron_ppm` |
| Hinweise | Minimale Duengung beibehalten: 1 ml/L Gardol alle 28 Tage. Ideales NPK-Verhaeltnis waere 1:2:1 (leichter P-Schwerpunkt fuer Bluetenunterhalt) -- Gardol 6-4-6 liefert 1,5:1:1,5 (P-arm), bei dieser Mikrodosis aber unerheblich. Bluetenstand haelt 2-4 Monate, nicht umtopfen oder umstellen. Duengerloesung NICHT auf den Bluetenstand giessen/spruehen (Fleckenbildung). Trichterwasser weiterhin alle 4-6 Wochen erneuern. | `phase_entries.notes` |

**Delivery Channel: trichter-duengung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.3  |
| reference_ec_ms | 0.3  |
| target_ph | 5.5 |
| Gardol ml/L | 1.0 (1/4-Dosis) |
| EC-Beitrag | ~0,06 mS/cm |
| Gardol optional | false |

### 4.4 DORMANCY -- Seneszenz / Kindel-Bildung (Woche 77--104)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 77 | `phase_entries.week_start` |
| week_end | 104 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keine Duengung. Mutterpflanze stirbt langsam ab (vergilbende Blaetter, schrumpfender Trichter). Mutterpflanze NICHT entfernen, solange sie Kindel versorgt -- sie gibt Naehrstoffe an die Ableger weiter. Trichter der Mutterpflanze trocknet zunehmend aus; nur noch wenig Wasser ins Substrat. Kindel an der Basis beobachten: sobald sie 1/3-1/2 der Muttergroesse erreichen und eigene Wurzeln zeigen, koennen sie abgetrennt und als neue Pflanzeninstanz getopft werden (neuer Naehrstoffplan ab GERMINATION W1). Reduziertes Giessintervall 14 Tage fuer Mutterpflanze. Kindel die noch an der Mutterpflanze haengen NICHT duengen. | `phase_entries.notes` |
| Giessplan-Override | Intervall 14 Tage (Mutterpflanze im Rueckgang, minimaler Wasserbedarf) | `phase_entries.watering_schedule_override` |

**Delivery Channel:** Kein Duenger, Nur-Wasser-Channel

| Feld | Wert |
|------|------|
| channel_id | wasser-pur |
| application_method | drench |
| target_ec_ms | null (keine Duengung, weiches Wasser EC ~0,0-0,1 mS/cm)  |
| reference_ec_ms | null (keine Duengung, weiches Wasser EC ~0,0-0,1 mS/cm)  |
| target_ph | 5.5 (Substrat-pH-Optimum) |
| fertilizer_dosages | [] (leer) |

---

## 5. Lebenszyklus-Timeline

Guzmania lingulata folgt keinem saisonalen Kalenderrhythmus. Der Lebenszyklus ist linear und endet mit dem Tod der Mutterpflanze. Kindel starten als neue Pflanzeninstanzen. Die folgende Timeline zeigt den vollstaendigen ~2-Jahres-Zyklus einer einzelnen Pflanze von der Kindel-Abtrennung bis zur Seneszenz.

### 5.1 Wochen-Timeline

| Wochen | KA-Phase | Gardol ml/L | EC-Beitrag | Frequenz | Trichter (ml) | Substrat (ml) | Aktion |
|--------|----------|-------------|------------|----------|---------------|---------------|--------|
| W1--8 | GERMINATION | 0 | 0,00 | -- | 20--30 (nur Wasser) | 30--50 | Kindel-Etablierung: kein Duenger, Substrat leicht feucht, hohe Luftfeuchtigkeit |
| W9--20 | VEGETATIVE | 1,0 | ~0,06 | 28-taegig | 50 (Duengerloesung) | 80--100 | Erste Duengegaben, Pflanze baut Rosette auf |
| W21--40 | VEGETATIVE | 1,0 | ~0,06 | 28-taegig | 50 (Duengerloesung) | 80--100 | Hauptwachstum, Blattmasse nimmt zu |
| W41--60 | VEGETATIVE | 1,0 | ~0,06 | 28-taegig | 50 (Duengerloesung) | 100 | Adulte Pflanze, 12+ Blaetter, bluetereif |
| W61--76 | FLOWERING | 1,0 | ~0,06 | 28-taegig | 50 (Duengerloesung) | 100 | Bluetenstand entfaltet sich, 2-4 Monate sichtbar |
| W77--90 | DORMANCY | 0 | 0,00 | -- | 20--30 (nur Wasser, falls Trichter noch offen) | 50--80 | Mutterpflanze vergilbt, Kindel wachsen |
| W91--104 | DORMANCY | 0 | 0,00 | -- | 0 (Trichter geschlossen) | 30--50 | Mutterpflanze absterbend, Kindel abtrennen wenn bereit |

**Saisonaler Hinweis:** Auch wenn der Lebenszyklus kalenderunabhaengig ist, sollte die Duengung in den Wintermonaten (November--Februar) pausiert werden, da das reduzierte Licht den Stoffwechsel verlangsamt. Die 28-Tage-Frequenz in der VEGETATIVE- und FLOWERING-Phase bezieht sich auf die Aktivmonate (Maerz--Oktober). Im Winter nur weiches Wasser ohne Duenger.

### 5.2 Verbrauch und Visualisierung

**Jahresverbrauch (geschaetzt):** Bei einer Pflanze und 0,05 L Trichter-Loesung pro Duengung:

- VEGETATIVE (W9--60): ~52 Wochen / 28 Tage = ~13 Duengungen x 0,05 L x 1 ml/L = **~0,65 ml**
- FLOWERING (W61--76): ~16 Wochen / 28 Tage = ~4 Duengungen x 0,05 L x 1 ml/L = **~0,20 ml**
- **Gesamt ueber gesamten Lebenszyklus: ~0,85 ml** -- 1 L Flasche reicht fuer ca. 1.176 Guzmania-Lebenszyklen

**Hinweis:** Der extrem niedrige Verbrauch unterstreicht den Schwachzehrer-Status. Bromelien benoetigen Groessenordnungen weniger Duenger als z.B. Monstera (~52 ml/Jahr) oder Erdbeeren (~500+ ml/Saison).

```
Woche:     |1-----8|9-----------60|61------76|77----------104|
KA-Phase:  | GERM  |  VEGETATIVE  | FLOWER   |   DORMANCY    |
Gardol:    |-------|==============|==========|---------------|
           kein    1 ml/L alle    1 ml/L alle kein Duenger
           Duenger 28 Tage       28 Tage     Mutterpfl. stirbt
                   (in Trichter)              Kindel wachsen

Legende: --- = keine Duengung, === = 1/4-Dosis (1 ml/L Gardol)
         GERM = GERMINATION, FLOWER = FLOWERING
```

---

## 6. KA-Import-Daten

### 6.1 NutrientPlan

```json
{
  "name": "Guzmania lingulata — Gardol Grünpflanzendünger",
  "description": "Lebenszyklus-Plan für Guzmania lingulata (Bromelie) in Orchideensubstrat. Einzeldünger-Konzept mit Gardol Grünpflanzendünger (NPK 6-4-6) auf 1/4-Dosis reduziert. Monokarper Lebenszyklus: Kindel → vegetatives Wachstum (~1 Jahr) → Blüte → Seneszenz. Ausschließlich weiches Wasser (Regenwasser/destilliert) verwenden.",
  "recommended_substrate_type": "orchid_bark",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["guzmania", "bromelie", "epiphyt", "zimmerpflanze", "gardol", "orchideensubstrat", "indoor", "schwachzehrer", "monokarp"],
  "water_mix_ratio_ro_percent": 100,
  "cycle_restart_from_sequence": null,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 10,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}
```

### 6.2 NutrientPlanPhaseEntry (4 Eintraege)

#### GERMINATION

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine Düngung. Frisch abgetrenntes Kindel nur mit weichem Wasser (Regenwasser/destilliert) versorgen. Orchideensubstrat leicht feucht halten, nie nass. Trichter minimal befüllen (20–30 ml weiches Wasser). 10-Tage-Intervall für Substrat. Hohe Luftfeuchtigkeit (60–80 %) fördert Bewurzelung. Kein Trichterwasser unter 18 °C.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 10,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Substratbefeuchtung)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur weiches Wasser, kein Dünger. Substrat leicht feucht halten. Trichter minimal befüllen (20–30 ml). DRENCH = Substratbewässerung.",
      "target_ec_ms": null,
      "reference_ec_ms": null,
      "target_ph": 5.5,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.03
      }
    }
  ]
}
```

#### VEGETATIVE

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "vegetative",
  "sequence_order": 2,
  "week_start": 9,
  "week_end": 60,
  "is_recurring": false,
  "npk_ratio": [1.0, 1.0, 1.0],
  "calcium_ppm": 20.0,
  "magnesium_ppm": 10.0,
  "iron_ppm": 1.0,
  "notes": "1/4-Dosis Gardol (1 ml/L) alle 28 Tage über Trichter oder als Blattdüngung. NPK-Ziel 1:1:1 — Gardol 6-4-6 liefert 1,5:1:1,5, bei Mikrodosis akzeptabel. EC-Ziel ~0,3 mS/cm. Ca 20 ppm, Mg 10 ppm aus Düngerspuren gedeckt. Trichterwasser alle 4–6 Wochen komplett austauschen. Kein Trichterwasser unter 18 °C. Wintermonate (Nov–Feb): Düngung pausieren auch in VEGETATIVE. Optimaler Dünger wäre Orchideendünger (z. B. COMPO NPK 3-4-5) — Gardol auf 1/4-Dosis ist akzeptabler Ersatz. Ethylen-Induktion am Ende dieser Phase möglich (W50–60): reifer Apfel in versiegelte Tüte mit Pflanze, 10 Tage — muss VOR Blütebeginn erfolgen, sobald Blütenstand sichtbar ist, ist Ethylen wirkungslos.",
  "delivery_channels": [
    {
      "channel_id": "trichter-duengung",
      "label": "Trichter-Düngung (Rosettentank)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Primäre Nährstoffzufuhr über den zentralen Rosettentrichter. 50 ml Düngerlösung (1 ml/L Gardol in weichem Wasser). Trichterwasser alle 4–6 Wochen komplett austauschen. Kein Trichterwasser unter 18 °C.",
      "target_ec_ms": 0.3,
      "reference_ec_ms": 0.3,
      "target_ph": 5.5,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 1.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.05
      }
    },
    {
      "channel_id": "blatternaehrung",
      "label": "Blattdüngung (Foliar Spray)",
      "application_method": "foliar",
      "enabled": true,
      "notes": "Sekundäre Nährstoffzufuhr über Trichome. 0,5 ml/L Gardol fein auf Blätter sprühen. Nicht auf Blütenstand. Stehende Tropfen vermeiden — bei geringer Luftzirkulation Blattflecken-Risiko (Helminthosporium). Morgens sprühen, damit Blätter tagsüber abtrocknen. Alternative wenn Trichter trocken gehalten wird (Winter).",
      "target_ec_ms": 0.2,
      "reference_ec_ms": 0.2,
      "target_ph": 5.5,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 0.5,
          "optional": true
        }
      ],
      "method_params": {
        "method": "foliar",
        "volume_per_spray_liters": 0.02
      }
    }
  ]
}
```

#### FLOWERING

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "flowering",
  "sequence_order": 3,
  "week_start": 61,
  "week_end": 76,
  "is_recurring": false,
  "npk_ratio": [1.0, 2.0, 1.0],
  "calcium_ppm": 20.0,
  "magnesium_ppm": 15.0,
  "iron_ppm": 1.0,
  "notes": "Minimale Düngung beibehalten: 1 ml/L Gardol alle 28 Tage über Trichter. NPK-Ziel 1:2:1 (leichter P-Schwerpunkt) — Gardol 6-4-6 ist P-arm, bei Mikrodosis unerheblich. Blütenstand hält 2–4 Monate. Nicht umtopfen oder umstellen. Düngerlösung NICHT auf Blütenstand gießen (Fleckenbildung). Trichterwasser weiterhin alle 4–6 Wochen erneuern.",
  "delivery_channels": [
    {
      "channel_id": "trichter-duengung",
      "label": "Trichter-Düngung (Rosettentank)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Primäre Nährstoffzufuhr über Rosettentrichter. 50 ml Düngerlösung. Nicht auf Blütenstand gießen. Trichterwasser alle 4–6 Wochen erneuern.",
      "target_ec_ms": 0.3,
      "reference_ec_ms": 0.3,
      "target_ph": 5.5,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "<gardol_gruenpflanzenduenger_key>",
          "ml_per_liter": 1.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.05
      }
    }
  ]
}
```

#### DORMANCY

```json
{
  "plan_key": "<plan_key>",
  "phase_name": "dormancy",
  "sequence_order": 4,
  "week_start": 77,
  "week_end": 104,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine Düngung. Terminale Seneszenz der Mutterpflanze (monokarper Lebenszyklus). Mutterpflanze vergilbt und stirbt, bildet 1–5 Kindel an der Basis. Mutterpflanze NICHT entfernen solange sie Kindel versorgt — sie gibt Nährstoffe weiter. 14-Tage-Intervall für Substrat, minimales Volumen. Trichter trocknet zunehmend aus. Kindel bei 1/3–1/2 Muttergröße und eigenen Wurzeln abtrennen → neue Pflanzeninstanz mit neuem Nährstoffplan (GERMINATION W1).",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 14,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Substratbefeuchtung)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur weiches Wasser, kein Dünger. Minimales Volumen. Mutterpflanze im Rückgang, Trichter meist geschlossen. Substrat nur leicht feucht halten.",
      "target_ec_ms": null,
      "reference_ec_ms": null,
      "target_ph": 5.5,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.05
      }
    }
  ]
}
```

### 6.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Gardol Gruenpflanzenduenger | `spec/knowledge/products/gardol_gruenpflanzenduenger.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Guzmania lingulata | `spec/knowledge/plants/guzmania_lingulata.md` | Via `nutrient_plans` -> `uses_nutrient_plan` edge |
| SubstrateType: ORCHID_BARK | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 7. Sicherheitshinweise

### Pflanzentoxizitaet

**Ungiftig:** Guzmania lingulata ist nach ASPCA-Daten vollstaendig ungiftig fuer Katzen, Hunde und Kinder. Dies macht sie zu einer der sichersten Zimmerpflanzen fuer Haushalte mit Haustieren und Kleinkindern. Im Duengekontext gibt es keine pflanzenseitigen Risiken -- Drainage-Wasser, Blattkontakt und versehentliches Annagen sind unbedenklich.

### Trichterfaeule (Heart Rot) -- Haeufigste Todesursache

**KRITISCH:** Stehendes Wasser im Trichter bei Temperaturen unter 18 C fuehrt zu bakterieller/pilzlicher Trichterfaeule. Symptome: faulig riechender Trichter, innere Blaetter lassen sich leicht herausziehen, braune matschige Basis. Trichterfaeule ist **nicht heilbar** -- die Pflanze stirbt.

- **Praevention:** Im Winter (November--Februar) und in kuehlen Raeumen den Trichter trocken oder nur minimal befuellt halten.
- **Temperatur-Regel:** Kein Trichterwasser unter 18 C.
- **Trichterhygiene:** Wasser alle 4-6 Wochen komplett austauschen.

### Kalkschaden -- Irreversibel

**KRITISCH:** Hartes Leitungswasser (>10 dH) verstopft die Trichome (Saugschuppen) auf den Blaettern dauerhaft. Die Pflanze kann danach keine Naehrstoffe mehr ueber die Blaetter aufnehmen -- der Schaden ist **nicht reversibel**. Ausschliesslich weiches Wasser verwenden: Regenwasser, destilliertes Wasser, RO-Wasser, oder sehr weiches Leitungswasser (<5 dH).

### Gardol-Konzentrat

Mineralischer Fluessigduenger -- bei versehentlichem Kontakt durch Haustiere oder Kinder:
- **Verschlucken:** Mund ausspuelen, Wasser trinken, aerztlichen Rat einholen. Bei groesseren Mengen Giftnotrufzentrale kontaktieren.
- **Augenkontakt:** Gruendlich mit Wasser ausspuelen (mind. 15 Minuten).
- **Hautkontakt:** Mit Wasser und Seife abwaschen.
- **Flasche:** Ausserhalb der Reichweite von Kindern und Haustieren aufbewahren.

Die Toxizitaetsdaten der Pflanze sind im Steckbrief dokumentiert (vgl. `spec/knowledge/plants/guzmania_lingulata.md`, Abschnitt 1.4).

---

## Quellenverzeichnis

1. Guzmania lingulata Pflanzensteckbrief: `spec/knowledge/plants/guzmania_lingulata.md`
2. Gardol Gruenpflanzenduenger Produktdaten: `spec/knowledge/products/gardol_gruenpflanzenduenger.md`
3. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
4. PhaseName Enum: `src/backend/app/common/enums.py`
5. ASPCA Animal Poison Control -- Guzmania lingulata: https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants
6. Bromeliads.info -- Getting to Know the Guzmania Bromeliad: https://www.bromeliads.info/guzmania-bromeliad/
7. Clemson University Extension -- Bromeliads: https://hgic.clemson.edu/factsheet/bromeliads/

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-01
