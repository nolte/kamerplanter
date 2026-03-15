# Naehrstoffplan: Erbse -- Plagron Terra (Leguminose)

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Pisum sativum (Schwachzehrer, Outdoor, annuell, N-Fixierer, Kuehle-Liebhaber)
> **Produkte:** Plagron Terra Bloom, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/ref/products/plagron_terra_bloom.md, spec/ref/products/plagron_pure_zym.md, spec/ref/plant-info/pisum_sativum.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Erbse -- Plagron Terra (Leguminose) | `nutrient_plans.name` |
| Beschreibung | Minimalduegungs-Plan fuer Erbse (Pisum sativum) als Stickstoff-Fixierer und Kuehle-Liebhaber. Plagron Terra-Linie mit nur 2 Produkten. KEIN Terra Grow (zu viel N)! Leguminosen fixieren Stickstoff ueber Rhizobium-Symbiose -- N-Duengung ist kontraproduktiv. Terra Bloom in Viertel-Dosis fuer minimale P+K-Versorgung. Direktsaat ab Maerz (Keimlinge vertragen leichten Frost bis -4 degC). 12--16 Wochen Kulturzeit. Fruehjahrskultur -- leidet ab 25 degC Dauertemperatur. Annuell -- kein Zyklus-Neustart. | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | erbse, pisum, fabaceae, leguminose, plagron, terra, erde, outdoor, schwachzehrer, n-fixierer, gemuese, kuehleliebhaber | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

### 1.1 Giessplan (WateringSchedule)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Modus | INTERVAL | `watering_schedule.schedule_mode` |
| Intervall (Tage) | 3 | `watering_schedule.interval_days` |
| Uhrzeit | 07:00 | `watering_schedule.preferred_time` |
| Methode | DRENCH | `watering_schedule.application_method` |
| Erinnerung (Stunden vorher) | 2 | `watering_schedule.reminder_hours_before` |
| Giessen pro Tag | 1 | `watering_schedule.times_per_day` |

**Hinweis:** 3-Tage-Intervall als Basis fuer Beet. Erbsen brauchen gleichmaessige Feuchte, besonders waehrend Bluete und Huelsenbildung. Trockenheit fuehrt zu Huelsenabwurf. Morgens giessen, nicht ueber Blaetter (Mehltau-Gefahr). Staunaesse vermeiden (Wurzelfaeule). In GERMINATION ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Erbsen (Pisum sativum) sind Leguminosen mit Rhizobium-Symbiose und klassische Kuehle-Liebhaber. **Stickstoff-Duengung ist kontraproduktiv:** Sie unterdrueckt die N-Fixierung und foerdert ueppiges Laub auf Kosten der Huelsenbildung. Erbsen brauchen nur minimale P+K-Versorgung. Terra Grow (NPK 3-1-3) wird bewusst NICHT verwendet -- zu viel Stickstoff. Terra Bloom (NPK 2-2-4) wird in Viertel-Dosis eingesetzt; der minimale N-Beitrag bei dieser Dosierung ist vernachlaessigbar.

Erbsen sind Langtagspflanzen (Bluete durch laenger werdende Tage im Fruehjahr ausgeloest) und vertragen Temperaturen ueber 25 degC sehr schlecht -- Bluetenabwurf, Ertragsdepression, vorzeitiges Absterben. Daher ist die Erbse eine klassische Fruehjahrskultur (Maerz--Juli).

| Erbse-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Maerz | Direktsaat ab Maerz, Bodentemperatur ab 5 degC genuegt. Keimlinge vertragen Frost bis -4 degC! Dunkelkeimer, 3--5 cm tief. Kein Duenger. | false |
| Saemling | SEEDLING | 3--5 | Maerz--April | Erste Blaetter und Ranken. Rankhilfe aufstellen. Kein Duenger -- Rhizobium etabliert sich. | false |
| Vegetatives Wachstum | VEGETATIVE | 6--9 | April--Mai | Aktives Rankenwachstum. Minimale P+K-Versorgung. Terra Bloom in Viertel-Dosis. | false |
| Bluete + Huelsenbildung | FLOWERING | 10--12 | Mai--Juni | Bluete durch Langtag ausgeloest. Hitze >25 degC = Bluetenabwurf! Terra Bloom in Viertel-Dosis. Regelmaessig giessen. | false |
| Ernte | HARVEST | 13--16 | Juni--Juli | Alle 2--3 Tage ernten! Ueberreife Huelsen hemmen Neuansatz. Kein Duenger. Wurzeln im Boden lassen! | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (annuelle Pflanze, kein Ueberdauerungsorgan)
- **FLUSHING** entfaellt (Freiland mit Erdsubstrat, minimale Salzbelastung)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Der Plan laeuft einmalig durch (16 Wochen).

**Lueckenlos-Pruefung:** 2 + 3 + 4 + 3 + 4 = 16 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Sehr kleine Volumina (Schwachzehrer, minimale Duengung).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Wasser Keimung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Boden gleichmaessig feucht halten, nicht nass. Saatgut kann vorher 12--24 Stunden eingeweicht werden (beschleunigt Keimung). | `delivery_channels.notes` |
| method_params | drench, 0.01--0.03 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung P+K

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-pk | `delivery_channels.channel_id` |
| Label | P+K-Duengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. KEIN Terra Grow (N-Fixierer brauchen keinen Stickstoff!). Viertel-Dosis -- minimale Duengung genuegt. Morgens giessen, nicht ueber Blaetter. | `delivery_channels.notes` |
| method_params | drench, 0.1--0.3 L pro Pflanze | `delivery_channels.method_params` |

### 3.3 Nur Wasser

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-pur | `delivery_channels.channel_id` |
| Label | Nur Wasser (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Keimung, Saemling und Erntephase. | `delivery_channels.notes` |
| method_params | drench, 0.05--0.2 L pro Pflanze | `delivery_channels.method_params` |

---

## 4. Dosierung pro Phase

### EC-Budget Plagron-Produkte fuer Erbse

Erbsen sind Schwachzehrer UND N-Fixierer mit dem niedrigsten Duengebedarf aller Gemuese. Ziel-EC der Gesamtloesung: **0.3--0.6 mS/cm** (inkl. Basis-Wasser). Leitungswasser liefert typisch 0.2--0.6 mS/cm. Bei hartem Wasser (>0.4 mS/cm) ist eine zusaetzliche Duengung oft ueberflüssig. **KRITISCH: KEIN Stickstoff-Duenger!** Die Rhizobium-Symbiose liefert allen benoetigten Stickstoff.

**Warum Terra Bloom in Viertel-Dosis:** Terra Bloom (NPK 2-2-4) liefert P und K, die Erbsen fuer Bluete und Huelsenbildung brauchen. Bei Viertel-Dosis (1.25 ml/L) ist der N-Beitrag aus Terra Bloom vernachlaessigbar (~0.03% effektiv) und hemmt die Rhizobium-Symbiose nicht. Terra Grow (NPK 3-1-3) wird bewusst NICHT verwendet -- hoeerer N-Anteil und weniger P.

**pH-Hinweis:** Erbsen bevorzugen pH 6.0--7.5 (kalkvertraeglich). Terra Bloom puffert auf pH 6.0--6.5. Rhizobium-Aktivitaet funktioniert optimal bei pH 6.0--7.0. Bei saurem Boden (pH <6.0) vor Aussaat kalken!

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Bloom (2-2-4) | 0.10 | 20 | Vegetativ, Bluete (minimale P+K-Versorgung) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Bluete (durchgehend) |

**NICHT verwendet:** Terra Grow (3-1-3) -- zu viel Stickstoff fuer Leguminosen!

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
| Hinweise | Direktsaat ab Maerz, Bodentemperatur ab 5 degC genuegt (optimal 8--15 degC). Erbsen sind kuehle Keimer! Keimlinge vertragen leichten Frost bis -4 degC. Dunkelkeimer -- Samen 3--5 cm tief legen. Saatgut vorher 12--24 Stunden in lauwarmem Wasser einweichen (beschleunigt Keimung). Reihenabstand 30--50 cm, in der Reihe 5--8 cm. Impfung mit Rhizobium leguminosarum bei erstmaligem Erbsenanbau empfohlen. Keimdauer 7--14 Tage. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage (gleichmaessig feucht, nicht nass) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

### 4.2 SEEDLING -- Saemling (Woche 3--5)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 5 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger. Rhizobium-Knoellchen bilden sich an den Wurzeln -- N-Duengung wuerde die Knoellchenbildung hemmen! Erste Blaetter und Ranken entwickeln sich. Rankhilfe ab ca. 15 cm Hoehe bereitstellen (Reisig, Maschendraht, Schnuere). Kuehle Temperaturen (12--18 degC) sind ideal fuer kompakten, stabilen Wuchs. | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

### 4.3 VEGETATIVE -- Wachstum (Woche 6--9)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 6 | `phase_entries.week_start` |
| week_end | 9 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Terra Bloom in Viertel-Dosis (1.25 ml/L) + Pure Zym. Minimale P+K-Versorgung -- Rhizobium liefert den Stickstoff. Aktives Rankenwachstum, Pflanze klettert an Stuetze. Erbsen sind in der vegetativen Phase genuegsam. Alle 14 Tage duengen. Optimale Temperatur 14--20 degC. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-pk**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| target_ph | 6.5 |
| Terra Bloom ml/L | 1.25 (Viertel-Dosis, minimale Duengung) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.13 (TB 1.25ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.53 mS/cm** -- ok

### 4.4 FLOWERING -- Bluete + Huelsenbildung (Woche 10--12)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 10 | `phase_entries.week_start` |
| week_end | 12 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 2, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Terra Bloom in Viertel-Dosis (1.25 ml/L) + Pure Zym. P+K fuer Bluete und Huelsenbildung. Kalium foerdert Huelsenqualitaet. **KRITISCH: Hitze ueber 25 degC fuehrt zu Bluetenabwurf und stark reduziertem Huelsenansatz!** Ausreichende Wasserversorgung in dieser Phase essenziell. Erbsen sind Selbstbestaeuber. Alle 14 Tage duengen. Bei Hitze: Mulchschicht 5 cm (Bodentemperatur senken) und Halbschatten-Standort bevorzugen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-pk**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5 |
| target_ph | 6.5 |
| Terra Bloom ml/L | 1.25 (Viertel-Dosis, unveraendert) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.13 (TB 1.25ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.53 mS/cm** -- ok

**Hinweis:** Die Dosierung bleibt in FLOWERING unveraendert gegenueber VEGETATIVE. Erbsen sind extreme Schwachzehrer -- eine Dosissteigerung ist nicht noetig und wuerde nur das Risiko einer Salzbelastung erhoehen.

### 4.5 HARVEST -- Ernte (Woche 13--16)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 13 | `phase_entries.week_start` |
| week_end | 16 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger. **REGELMAESSIG ERNTEN!** Alle 2--3 Tage kontrollieren und pfluckreife Huelsen ernten. Zuckererbsen: Huelsen noch flach. Markerbsen: Koerner vorgewoelbt aber noch gruen. Ueberreife Huelsen hemmen Neuansatz. **Nach der Ernte: Pflanzen als Gruenduengung in den Boden einarbeiten** (Stickstoff fuer Nachfolgekultur!) oder abschneiden und Wurzeln mit N-Knoellchen im Boden lassen. Ideale Nachfrucht: Starkzehrer (Kohl, Tomate, Kuerbis). | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0 |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

---

## 5. Jahresplan (Monat-fuer-Monat)

Annueller Zyklus, Start Maerz. 16 Wochen Kulturzeit. Fruehjahrskultur -- Erbsen leidet ab 25 degC.

| Monat | KA-Phase | Terra Bloom ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|------------------|---------------|-----------------|----------|
| Maerz | GERM->SEED | -- | -- | 0.4 | alle 2--3d |
| April | SEED->VEG | -->1.25 | -->1.0 | 0.4->0.5 | alle 14d |
| Mai | VEG->FLO | 1.25 | 1.0 | 0.5 | alle 14d |
| Juni | FLO->HARV | 1.25->0 | 1.0->-- | 0.5->0.4 | alle 14d->-- |
| Juli | HARVEST | -- | -- | 0.4 | alle 2--3d (Ernte) |

```
Monat:        |Maer |Apr  |Mai  |Jun  |Jul  |
KA-Phase:     |G->SE|S->VE|V->FL|F->HA|HARV |
Terra Bloom:  |---  |-->#-|#--  |#-->-|---  |
Pure Zym:     |---  |-->==|===  |==-->|---  |

Legende: --- = nicht verwendet, #-- = Viertel-Dosis
         === = volle Phase-Dosis, --> = Start/Auslaufen
```

### Jahresverbrauch (geschaetzt)

Bei einer Erbsen-Reihe (20 Pflanzen), 0.15 L Giessloessung pro Duengung (gesamte Reihe), Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Bloom | (4 Duengungen x 1.25ml/L x 0.15L) = 0.75 ml | **~1 ml** |
| Pure Zym | (4 Duengungen x 1.0ml/L x 0.15L) = 0.6 ml | **~1 ml** |

**Kosten-Schaetzung:** Vernachlaessigbar. Eine 1L-Flasche Terra Bloom reicht fuer ueber 1000 Erbsen-Saisons. Dieses Produkt macht bei Erbsen nur Sinn, wenn es bereits fuer andere Pflanzen im Einsatz ist.

---

## 6. Erbse-spezifische Praxis-Hinweise

### Substrat

- Lockere, humose Gartenerde mit guter Drainage
- pH 6.0--7.5 (kalkvertraeglich, Rhizobium braucht pH >6.0)
- Keine stickstoffreiche Erde noetig (N-Fixierung!)
- Bei saurem Boden (pH <6.0) vor Aussaat kalken (Algenkalk 100--200 g/m2)
- Topfkultur: 10--20 L fuer 3--5 Pflanzen, Zwergsorten bevorzugt

### Kuehle-Liebhaber -- der wichtigste Kulturfaktor

**Erbsen sind Kuehlewetter-Pflanzen. Hitze ist der Hauptfeind!**

- Optimale Temperatur: 12--18 degC (Tagestemperatur)
- Ab 25 degC Dauertemperatur: Bluetenabwurf, Ertragsdepression, vorzeitiges Absterben
- In heissen Sommern ist Anbau ab Juli nicht mehr sinnvoll
- Fruehe Aussaat ab Maerz nutzt die kuehle Jahreszeit optimal
- Keimlinge vertragen Frost bis -4 degC -- daher fruehe Aussaat moeglich und empfohlen
- Bei Hitze: Mulchschicht 5 cm zum Bodentemperatur-Senken, Morgensonne + Nachmittagsschatten

### N-Fixierung -- der Schluessel zur Erbsen-Duengung

**Erbsen sind die klassische Gruenduengung im Gemuesebau.**

- Rhizobium leguminosarum fixiert atmosphaerischen Stickstoff
- N-Duengung unterdrueckt die symbiotische N-Fixierung
- Pflanze stellt bei externem N-Angebot die Knoellchenbildung ein
- Resultat bei N-Duengung: ueppiges Laub, weniger Huelsen
- **Nach der Ernte: Pflanzen als Gruenduengung einarbeiten!**
- Ideale Vorfrucht fuer Starkzehrer (Kohl, Tomate, Kuerbis)
- Anbaupause: 4--5 Jahre fuer Fabaceae auf gleicher Flaeche (Erbsenmuedigkeit, Fusarium)

### Ernte-Tipps

- **Alle 2--3 Tage ernten!** Ueberreife Huelsen hemmen Neuansatz
- Zuckererbsen: ernten wenn Huelsen noch flach (Koerner kaum spuerbar)
- Markerbsen: ernten wenn Koerner in der Huelsse deutlich vorgewoelbt aber noch gruen
- Knackerbsen (Sugar Snap): ernten wenn Huelsen prall gefuellt und Koerner vorgewoelbt
- Morgens ernten (hoehere Zuckerkonzentration)
- Frisch geerntete Erbsen sofort verwerten (Zucker wandelt sich schnell in Staerke um)

### Rankhilfe

- Ab ca. 15 cm Hoehe Rankhilfe bereitstellen
- Reisig (natuerlich, kostenguenstig) in die Reihe stecken
- Alternativ: Maschendraht, Erbsennetz, gespannte Schnuere
- Zwergsorten (40--60 cm) brauchen weniger Stuetze
- Hohe Sorten (bis 200 cm) brauchen stabile Rankhilfe

### Schaedlinge und Krankheiten

- **Erbsenblattlaus:** Grosse gruene Laeuse an Triebspitzen. Kaliseife (2%), Florfliegenlarven
- **Erbsenwickler:** Raupen in den Huelsen. Kulturschutznetze (Maschenweite <1.3 mm) ab Bluetebeginn
- **Blattrandkaefer:** Halbkreisfoermiger Randfass (typisch!). Larven fressen an Wurzelknoellchen. Meist tolerierbar
- **Echter Mehltau:** Weisser Belag bei warmen Tagen + kuehlen Naechten. Gute Luftzirkulation, resistente Sorten
- **Brennfleckenkrankheit (Ascochyta):** Samenbuertig! Nur zertifiziertes Saatgut verwenden
- **Schnecken:** Bei Jungpflanzen. Eisenphosphat-Schneckenkorn, Schneckennetz

### Nicht verwechseln: Erbse vs. Duftwicke

**ACHTUNG:** Nicht verwechseln mit der Duftwicke (Lathyrus odoratus / Sweet Pea)! Die Duftwicke ist eine Zierpflanze und giftig! Gartenerbse (Pisum sativum) ist essbar und laut ASPCA ungiftig fuer Katzen und Hunde.

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Erbse \u2014 Plagron Terra (Leguminose)",
  "description": "Minimald\u00fcngungs-Plan f\u00fcr Erbse (Pisum sativum) als N-Fixierer und K\u00fchle-Liebhaber. KEIN Terra Grow! Nur Terra Bloom (P+K) in Viertel-Dosis. Rhizobium-Symbiose liefert Stickstoff. Direktsaat ab M\u00e4rz, 12\u201316 Wochen Kulturzeit. Leidet ab 25\u00b0C.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["erbse", "pisum", "fabaceae", "leguminose", "plagron", "terra", "erde", "outdoor", "schwachzehrer", "n-fixierer", "gem\u00fcse", "k\u00fchleliebhaber"],
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

### 7.2 NutrientPlanPhaseEntry (5 Eintraege)

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
  "notes": "Direktsaat ab M\u00e4rz, Bodentemperatur ab 5\u00b0C. K\u00fchle Keimer! Keimlinge vertragen Frost bis -4\u00b0C. Dunkelkeimer, 3\u20135 cm tief. Saatgut 12\u201324 h einweichen. Rhizobium-Impfung bei erstmaligem Anbau empfohlen.",
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
      "label": "Wasser Keimung",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Gleichm\u00e4\u00dfig feucht, nicht nass.",
      "target_ec_ms": 0.0,
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
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Rhizobium-Kn\u00f6llchen bilden sich an den Wurzeln. N-D\u00fcngung hemmt Kn\u00f6llchenbildung! Rankhilfe ab 15 cm H\u00f6he bereitstellen. K\u00fchle Temperaturen (12\u201318\u00b0C) ideal.",
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (S\u00e4mling)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Rhizobium-Etablierung nicht st\u00f6ren.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.05}
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
  "week_end": 9,
  "is_recurring": false,
  "npk_ratio": [0.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom Viertel-Dosis (1.25 ml/L) + Pure Zym. Minimale P+K-Versorgung \u2014 Rhizobium liefert N. Aktives Rankenwachstum. Alle 14 Tage d\u00fcngen. Optimale Temperatur 14\u201320\u00b0C.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-pk",
      "label": "P+K-D\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom Viertel-Dosis + Pure Zym. KEIN Terra Grow! Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 1.25, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.15}
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
  "week_start": 10,
  "week_end": 12,
  "is_recurring": false,
  "npk_ratio": [0.0, 2.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom Viertel-Dosis (1.25 ml/L) + Pure Zym. P+K f\u00fcr Bl\u00fcte und H\u00fclsenbildung. Hitze \u00fcber 25\u00b0C = Bl\u00fctenabwurf! Gleichm\u00e4\u00dfig gie\u00dfen. Alle 14 Tage d\u00fcngen. Bei Hitze: Mulch 5 cm.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-pk",
      "label": "P+K-D\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom Viertel-Dosis + Pure Zym. Dosierung bleibt gleich wie VEGETATIVE (extremer Schwachzehrer).",
      "target_ec_ms": 0.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 1.25, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.15}
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
  "week_end": 16,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Alle 2\u20133 Tage ernten! \u00dcberreife H\u00fclsen hemmen Neuansatz. Nach der Ernte: Pflanzen als Gr\u00fcnd\u00fcngung einarbeiten oder Wurzeln im Boden lassen (N-Anreicherung f\u00fcr Nachfolgekultur).",
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Ernte)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Gleichm\u00e4\u00dfig gie\u00dfen f\u00fcr H\u00fclsenqualit\u00e4t.",
      "target_ec_ms": 0.0,
      "target_ph": 6.5,
      "fertilizer_dosages": [],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.1}
    }
  ]
}
```

### 7.3 Referenzierte Entitaeten

| Entitaet | Referenz-Dokument | KA-Feld |
|----------|-------------------|---------|
| Fertilizer: Terra Bloom | `spec/ref/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/ref/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Pisum sativum | `spec/ref/plant-info/pisum_sativum.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **Ungiftig:** Pisum sativum ist laut ASPCA ungiftig fuer Katzen und Hunde
- **Essbar:** Erbsen (Huelsen und Koerner) sind roh und gekocht essbar
- **ACHTUNG: Nicht verwechseln mit Duftwicke (Lathyrus odoratus / Sweet Pea)** -- diese Zierpflanze ist giftig!
- Rohe Erbsen enthalten geringe Mengen Lektine und Protease-Inhibitoren, die durch Kochen inaktiviert werden -- bei normaler Ernaehrung vernachlaessigbar

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- **Essbare-Ernte-Hinweis:** Mindestens 7 Tage nach letzter Duengung warten bevor Huelsen geerntet werden. Bei der sehr niedrigen Dosierung dieses Plans (1.25 ml/L TB) und 14-Tage-Intervall ist dies automatisch gewaehrleistet.

---

## Quellenverzeichnis

1. Plagron Terra Bloom Produktdaten: `spec/ref/products/plagron_terra_bloom.md`
2. Plagron Pure Zym Produktdaten: `spec/ref/products/plagron_pure_zym.md`
3. Pisum sativum Pflanzensteckbrief: `spec/ref/plant-info/pisum_sativum.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
