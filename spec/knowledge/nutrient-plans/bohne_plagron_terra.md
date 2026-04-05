# Naehrstoffplan: Buschbohne -- Plagron Terra (Leguminose)

> **Import-Ziel:** Kamerplanter Naehrstoffplan (REQ-004)
> **Pflanze:** Phaseolus vulgaris (Schwachzehrer, Outdoor, annuell, N-Fixierer)
> **Produkte:** Plagron Terra Bloom, Pure Zym
> **Erstellt:** 2026-03-06
> **Quellen:** spec/knowledge/products/plagron_terra_bloom.md, spec/knowledge/products/plagron_pure_zym.md, spec/knowledge/plants/phaseolus_vulgaris.md

---

## 1. Metadata (NutrientPlan)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Name | Buschbohne -- Plagron Terra (Leguminose) | `nutrient_plans.name` |
| Beschreibung | Minimalduegungs-Plan fuer Buschbohne (Phaseolus vulgaris) als Stickstoff-Fixierer. Plagron Terra-Linie mit nur 2 Produkten. KEIN Terra Grow (zu viel N)! Leguminosen fixieren Stickstoff ueber Rhizobium-Symbiose -- N-Duengung ist kontraproduktiv und hemmt die Knoellchenbildung. Nur P+K-Versorgung ueber Terra Bloom in niedriger Dosis. Direktsaat nach Eisheiligen (Mitte Mai), 10--14 Wochen Kulturzeit. Annuell -- kein Zyklus-Neustart. WARNUNG: Rohe Bohnen sind giftig (Phasin/Lektin, zerstoert durch 15 Min Kochen)! | `nutrient_plans.description` |
| Substrattyp | SOIL | `nutrient_plans.recommended_substrate_type` |
| Referenz-Substrat | SOIL | `nutrient_plans.reference_substrate_type` |
| Autor | Kamerplanter Referenzdaten | `nutrient_plans.author` |
| Template | true | `nutrient_plans.is_template` |
| Version | 1.0 | `nutrient_plans.version` |
| Tags | bohne, buschbohne, phaseolus, fabaceae, leguminose, plagron, terra, erde, outdoor, schwachzehrer, n-fixierer, gemuese | `nutrient_plans.tags` |
| Wasserquelle RO-Anteil | null (Leitungswasser) | `nutrient_plans.water_mix_ratio_ro_percent` |
| Zyklus-Neustart ab Sequenz | null (annuell, kein Neustart) | `nutrient_plans.cycle_restart_from_sequence` |

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

**Hinweis:** 3-Tage-Intervall als Basis fuer Beet/Kuebel. Bohnen sind relativ trockentolerant in der vegetativen Phase, brauchen aber in der Bluete mehr Wasser (alle 2 Tage). Staunaesse unbedingt vermeiden (Wurzelfaeule-Risiko). Morgens giessen, nicht ueber Blaetter/Blueten (Grauschimmel, Rost). In GERMINATION ueber `watering_schedule_override` angepasst.

---

## 2. Phasen-Mapping

Buschbohnen (Phaseolus vulgaris) sind Leguminosen mit Rhizobium-Symbiose -- sie fixieren atmosphaerischen Stickstoff ueber Knoellchenbakterien an den Wurzeln. **Stickstoff-Duengung ist kontraproduktiv:** Sie unterdrueckt die N-Fixierung und foerdert ueppiges Laub auf Kosten der Huelsenbildung. Nur Phosphor und Kalium sind als externe Naehrstoffe noetig. Terra Bloom (NPK 2-2-4) wird in niedriger Dosis verwendet -- der geringe N-Anteil (2%) ist bei niedrigen Dosierungen tolerierbar. Terra Grow (NPK 3-1-3) wird bewusst NICHT verwendet, da der hoehere N-Anteil bei Leguminosen kontraproduktiv ist.

| Bohne-Phase | PhaseName (Enum) | Wochen | Kalender (ca.) | Begruendung | is_recurring |
|-------------|-----------------|--------|----------------|-------------|-------------|
| Keimung | GERMINATION | 1--2 | Mitte Mai | Direktsaat nach Eisheiligen, Bodentemperatur mind. 10 degC. Dunkelkeimer, 3--5 cm tief. Kein Duenger. | false |
| Saemling | SEEDLING | 3--4 | Ende Mai--Anfang Juni | Keimblaetter und erste Fiederblaetter. Kein Duenger -- Rhizobium-Knoellchen beginnen sich zu bilden. | false |
| Vegetatives Wachstum | VEGETATIVE | 5--8 | Juni | Aktiver Blattwuchs, Anhaeufelung. Minimale P+K-Versorgung. Terra Bloom in Viertel-Dosis. | false |
| Bluete + Huelsenbildung | FLOWERING | 9--11 | Ende Juni--Mitte Juli | Kritische Phase! Hitze >30 degC = Bluetenabwurf. Terra Bloom in niedriger Dosis fuer P+K. Regelmaessig giessen. | false |
| Ernte | HARVEST | 12--14 | Mitte Juli--August | Alle 2--3 Tage ernten! Ueberreife Huelsen hemmen Neuansatz. Kein Duenger. Wurzeln im Boden lassen! | false |

**Nicht genutzte Phasen:**
- **DORMANCY** entfaellt (annuelle Pflanze, kein Ueberdauerungsorgan)
- **FLUSHING** entfaellt (Freiland mit Erdsubstrat, minimale Salzbelastung)

**Annueller Zyklus:** Kein `cycle_restart_from_sequence`. Der Plan laeuft einmalig durch (14 Wochen). Staffelsaat alle 3--4 Wochen bis Mitte Juli moeglich fuer verlaengerte Ernte.

**Lueckenlos-Pruefung:** 2 + 2 + 4 + 3 + 3 = 14 Wochen, keine Luecken

---

## 3. Delivery Channels

Manuelle Giessduengung per Giesskanne. Kleine Volumina (Schwachzehrer).

### 3.1 Wasser Keimung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | wasser-keimung | `delivery_channels.channel_id` |
| Label | Wasser Keimung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Kein Duenger. Maessig feucht halten, NICHT nass. Bohnen faulen leicht in nasser, kalter Erde. NICHT vorquellen! | `delivery_channels.notes` |
| method_params | drench, 0.01--0.02 L pro Pflanze | `delivery_channels.method_params` |

### 3.2 Naehrloesung P+K

| Feld | Wert | KA-Feld |
|------|------|---------|
| Channel-ID | naehrloesung-pk | `delivery_channels.channel_id` |
| Label | P+K-Duengung (Giesskanne) | `delivery_channels.label` |
| Methode | DRENCH | `delivery_channels.application_method` |
| Aktiv | true | `delivery_channels.enabled` |
| Hinweise | Terra Bloom + Pure Zym ins Giesswasser. Reihenfolge: Terra Bloom -> Pure Zym -> pH pruefen. KEIN Terra Grow (N-Fixierer brauchen keinen Stickstoff!). Niedrige Dosis -- Schwachzehrer. Morgens giessen, nicht ueber Blaetter. | `delivery_channels.notes` |
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

### EC-Budget Plagron-Produkte fuer Buschbohne

Bohnen sind Schwachzehrer UND N-Fixierer. Ziel-EC der Gesamtloesung: **0.3--0.7 mS/cm** (inkl. Basis-Wasser). Leitungswasser liefert typisch 0.2--0.6 mS/cm. Bei hartem Wasser (>0.5 mS/cm) keine zusaetzliche Duengung noetig. **KRITISCH: KEIN Stickstoff-Duenger!** Die Rhizobium-Symbiose liefert allen benoetigten Stickstoff. N-Duengung hemmt die Knoellchenbildung und ist kontraproduktiv.

**Warum Terra Bloom statt Terra Grow:** Terra Bloom (NPK 2-2-4) hat einen niedrigeren N-Anteil als Terra Grow (NPK 3-1-3) und liefert mehr Phosphor und Kalium -- genau was eine Leguminose braucht. Bei niedrigen Dosierungen (1.5--2.0 ml/L) ist der N-Beitrag aus Terra Bloom minimal und hemmt die Rhizobium-Symbiose nicht nennenswert.

**pH-Hinweis:** Bohnen bevorzugen pH 6.0--6.8. Terra Bloom puffert auf pH 6.0--6.5. Rhizobium-Aktivitaet funktioniert am besten bei pH 6.0--7.0 -- die Plagron-Pufferung liegt im optimalen Bereich.

| Produkt | EC/ml (mS/cm) | mixing_priority | Phase |
|---------|---------------|-----------------|-------|
| Terra Bloom (2-2-4) | 0.10 | 20 | Vegetativ, Bluete (P+K-Versorgung) |
| Pure Zym (0-0-0) | 0.00 | 70 | Vegetativ, Bluete (durchgehend) |

**NICHT verwendet:** Terra Grow (3-1-3) -- zu viel Stickstoff fuer Leguminosen!

**Quantitativer N-Beitrag Terra Bloom:** Bei 2 ml/L Terra Bloom (NPK 2-2-4) wird rechnerisch ~0.04 mg N pro Liter Giessloessung appliziert -- das ist 50-100x weniger als der atmosphaerische N-Eintrag aus der Rhizobium-Symbiose in normalem Kulturboden.

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
| Hinweise | Direktsaat nach Eisheiligen (Mitte Mai), Bodentemperatur mind. 10 degC (optimal 18--22 degC). Dunkelkeimer -- Samen 3--5 cm tief in die Erde druecken. **NICHT vorquellen** (Erstickungsgefahr der Samen, Faeulnis). Reihenabstand 40--50 cm, in der Reihe 5--8 cm. Bohnen-Saatgut NICHT in nassen, kalten Boden saeen! Bei erstmaligem Anbau: Rhizobium-Impfung empfehlenswert. Keimdauer 5--10 Tage. | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage (maessig feucht, nicht nass) | `phase_entries.watering_schedule_override` |

**Delivery Channel: wasser-keimung**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

### 4.2 SEEDLING -- Saemling (Woche 3--4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 2 | `phase_entries.sequence_order` |
| week_start | 3 | `phase_entries.week_start` |
| week_end | 4 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Keimblaetter (gross, fleischig) ueber Erdoberflaeche, erste Fiederblaetter (Dreiblatt) entfalten sich. Kein Duenger -- Rhizobium-Knoellchen beginnen sich an den Wurzeln zu bilden. Stickstoff-Duengung in dieser Phase wuerde die Knoellchenbildung hemmen! Maessig giessen. | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

### 4.3 VEGETATIVE -- Wachstum (Woche 5--8)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 3 | `phase_entries.sequence_order` |
| week_start | 5 | `phase_entries.week_start` |
| week_end | 8 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 1, 2) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Terra Bloom in Viertel-Dosis (1.5 ml/L) + Pure Zym. Minimale P+K-Versorgung genuegt -- Rhizobium liefert den Stickstoff. **Anhaeufelung:** 5--8 cm Erde an Staengelbasis = Standfestigkeit + zusaetzliche Wurzeln. Bohnen sind in der vegetativen Phase genuegsam. Alle 14 Tage duengen. Bei Staffelsaat: 2. Satz jetzt saeen. | `phase_entries.notes` |

**Delivery Channel: naehrloesung-pk**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.5  |
| reference_ec_ms | 0.5  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 1.5 (Viertel-Dosis, Schwachzehrer + N-Fixierer) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.15 (TB 1.5ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.55 mS/cm** -- ok

### 4.4 FLOWERING -- Bluete + Huelsenbildung (Woche 9--11)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 4 | `phase_entries.sequence_order` |
| week_start | 9 | `phase_entries.week_start` |
| week_end | 11 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 2, 3) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Terra Bloom niedrige Dosis (2.0 ml/L) + Pure Zym. P+K fuer Bluete und Huelsenbildung. **KRITISCHE PHASE:** Hitze ueber 30 degC und Trockenheit verursachen Bluetenabwurf! Gleichmaessig giessen (alle 2 Tage), morgens, nicht ueber die Blueten. Bohnen sind Selbstbestaeuber. Kalium foerdert Huelsenqualitaet. Alle 14 Tage duengen. Bei Staffelsaat: letzte Saat jetzt (Mitte Juli). | `phase_entries.notes` |
| Giessplan-Override | Intervall 2 Tage (Bluete braucht mehr Wasser) | `phase_entries.watering_schedule_override` |

**Delivery Channel: naehrloesung-pk**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.6  |
| reference_ec_ms | 0.6  |
| target_ph | 6.5 |
| Terra Bloom ml/L | 2.0 (niedrige Dosis) |
| Pure Zym ml/L | 1.0 |

**EC-Budget:** 0.20 (TB 2.0ml) + 0.00 (PZ) + ~0.4 (Wasser) = **~0.60 mS/cm** -- ok

### 4.5 HARVEST -- Ernte (Woche 12--14)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| sequence_order | 5 | `phase_entries.sequence_order` |
| week_start | 12 | `phase_entries.week_start` |
| week_end | 14 | `phase_entries.week_end` |
| is_recurring | false | `phase_entries.is_recurring` |
| NPK-Verhaeltnis | (0, 0, 0) | `phase_entries.npk_ratio` |
| Calcium (ppm) | null | `phase_entries.calcium_ppm` |
| Magnesium (ppm) | null | `phase_entries.magnesium_ppm` |
| Hinweise | Kein Duenger. **REGELMAESSIG ERNTEN!** Alle 2--3 Tage kontrollieren und pfluckreife Huelsen ernten (8--15 cm, Samen noch nicht sichtbar als Ausbeulung). Ueberreife Huelsen an der Pflanze hemmen Neuansatz massiv. Morgens ernten (knackiger). Huelsen vorsichtig abknipsen oder abdrehen. **Nach der Ernte: Pflanzen abschneiden, Wurzeln im Boden belassen!** Die N-reichen Knoellchen an den Wurzeln ernaehren die Nachfolgekultur (Starkzehrer). | `phase_entries.notes` |

**Delivery Channel: wasser-pur**

| Feld | Wert |
|------|------|
| target_ec_ms | 0.0  |
| reference_ec_ms | 0.0  |
| target_ph | 6.5 |
| fertilizer_dosages | [] (leer) |

**EC-Budget:** ~0.4 (nur Wasser) -- ok

---

## 5. Jahresplan (Monat-fuer-Monat)

Annueller Zyklus, Start Mitte Mai. 14 Wochen Kulturzeit.

| Monat | KA-Phase | Terra Bloom ml/L | Pure Zym ml/L | EC gesamt (ca.) | Frequenz |
|-------|----------|------------------|---------------|-----------------|----------|
| Mai (ab Mitte) | GERM->SEED | -- | -- | 0.4 | alle 2--3d |
| Juni | VEG | 1.5 | 1.0 | 0.6 | alle 14d |
| Juli | FLO->HARV | 2.0->0 | 1.0->-- | 0.6->0.4 | alle 14d->-- |
| August | HARVEST | -- | -- | 0.4 | alle 2--3d (Ernte) |

```
Monat:        |Mai  |Jun  |Jul  |Aug  |
KA-Phase:     |G->SE|VEG  |F->HA|HARV |
Terra Bloom:  |---  |#--  |#-->-|---  |
Pure Zym:     |---  |===  |==-->|---  |

Legende: --- = nicht verwendet, #-- = Viertel-Dosis
         #-- = niedrige Dosis, === = volle Phase-Dosis
         --> = auslaufend
```

### Jahresverbrauch (geschaetzt)

Bei einer Buschbohnen-Reihe (10 Pflanzen), 0.1 L Giessloessung pro Pflanze/Duengung, Duengung alle 14 Tage:

| Produkt | Formel | Verbrauch/Saison |
|---------|--------|------------------|
| Terra Bloom | (2 Duengungen x 1.5ml/L x 1.0L + 2 Duengungen x 2.0ml/L x 1.0L) = 3.0 + 4.0 = 7.0 ml | **~7 ml** |
| Pure Zym | (4 Duengungen x 1.0ml/L x 1.0L) = 4.0 ml | **~4 ml** |

**Kosten-Schaetzung:** Extrem sparsam. Eine 1L-Flasche Terra Bloom reicht fuer ca. 140 Bohnen-Saisons (10er-Reihe). Sinnvoll nur in Kombination mit anderen Pflanzen.

---

## 6. Buschbohne-spezifische Praxis-Hinweise

### Substrat

- Durchlaessige, humose Gemuese-Erde. Nicht zu naehrstoffreich (N-Fixierung!)
- pH 6.0--6.8 (Rhizobium-Aktivitaet optimal bei pH 6.0--7.0)
- Keine schweren Tonboeden (Wurzelfaeule-Risiko)
- Topfkultur: 10--15 L Kuebel, 3--4 Pflanzen pro Topf

### N-Fixierung -- der Schluessel zur Bohnen-Duengung

**Bohnen sind die klassische Gruenduengung im Gemuesebau.**

- Rhizobium leguminosarum fixiert 50--100 kg N/ha aus der Atmosphaere
- N-Duengung unterdrueckt die symbiotische N-Fixierung
- Pflanze stellt bei externem N-Angebot die Knoellchenbildung ein
- Resultat bei N-Duengung: ueppiges Laub, weniger Huelsen
- **Nach der Ernte: Pflanzen abschneiden, Wurzeln im Boden lassen!**
- Die N-reichen Knoellchen ernaehren die Nachfolgekultur (ideale Vorfrucht fuer Starkzehrer)

### Staffelsaat

- Buschbohnen alle 3--4 Wochen nachsaeen fuer kontinuierliche Ernte
- 1. Satz: Mitte Mai (nach Eisheiligen)
- 2. Satz: Anfang Juni
- 3. Satz: Anfang--Mitte Juli (letztmoeglicher Termin)
- Jeder Satz kann diesen Naehrstoffplan verwenden

### Ernte-Tipps

- **Alle 2--3 Tage ernten!** Ueberreife Huelsen hemmen Neuansatz massiv
- Huelsen ernten wenn 8--15 cm lang und Samen NICHT als Ausbeulung sichtbar
- Morgens ernten (knackiger, hoehere Zuckerkonzentration)
- Huelsen vorsichtig abknipsen oder abdrehen -- Pflanze nicht beschaedigen

### Schaedlinge und Krankheiten

- **Schwarze Bohnenlaus:** Haeufigster Schaedling. Triebspitzen mit Kolonien abschneiden. Kaliseife (2%). Bohnenkraut als Begleitpflanze (traditionelle Abwehr)
- **Schnecken:** Hauptfeind bei Jungpflanzen. Eisenphosphat-Schneckenkorn
- **Bohnenrost:** Rosbraune Pusteln auf Blattunterseite. Befallenes Laub entfernen. Netzschwefel
- **Grauschimmel:** Bei feuchtem Wetter. Gute Luftzirkulation, morgens giessen
- **Bohnenfliege:** Larven fressen an Keimblaettern unter der Erde. Saatgut in warmen, trockenen Boden

---

## 7. KA-Import-Daten

### 7.1 NutrientPlan

```json
{
  "name": "Buschbohne \u2014 Plagron Terra (Leguminose)",
  "description": "Minimald\u00fcngungs-Plan f\u00fcr Buschbohne (Phaseolus vulgaris) als N-Fixierer. KEIN Terra Grow! Nur Terra Bloom (P+K) in niedriger Dosis. Rhizobium-Symbiose liefert Stickstoff. Direktsaat nach Eisheiligen, 10\u201314 Wochen Kulturzeit. WARNUNG: Rohe Bohnen sind giftig (Phasin)!",
  "recommended_substrate_type": "soil",
  "reference_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.0",
  "tags": ["bohne", "buschbohne", "phaseolus", "fabaceae", "leguminose", "plagron", "terra", "erde", "outdoor", "schwachzehrer", "n-fixierer", "gem\u00fcse"],
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
  "notes": "Direktsaat nach Eisheiligen, Bodentemperatur mind. 10\u00b0C. Dunkelkeimer, 3\u20135 cm tief. NICHT vorquellen! M\u00e4\u00dfig feucht halten, nicht nass. Rhizobium-Impfung bei erstmaligem Anbau empfohlen.",
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
      "notes": "Kein D\u00fcnger. M\u00e4\u00dfig feucht, nicht nass. Bohnen faulen in kalter, nasser Erde.",
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
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Rhizobium-Kn\u00f6llchen bilden sich an den Wurzeln. N-D\u00fcngung w\u00fcrde die Kn\u00f6llchenbildung hemmen! Erste Fiederbl\u00e4tter entfalten sich.",
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (S\u00e4mling)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Rhizobium-Etablierung nicht st\u00f6ren.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
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
  "week_start": 5,
  "week_end": 8,
  "is_recurring": false,
  "npk_ratio": [0.0, 1.0, 2.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom Viertel-Dosis (1.5 ml/L) + Pure Zym. Nur P+K-Versorgung \u2014 Rhizobium liefert N. Anh\u00e4ufelung: 5\u20138 cm Erde an St\u00e4ngelbasis. Alle 14 Tage d\u00fcngen.",
  "delivery_channels": [
    {
      "channel_id": "naehrloesung-pk",
      "label": "P+K-D\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom Viertel-Dosis + Pure Zym. KEIN Terra Grow! Reihenfolge: Terra Bloom \u2192 Pure Zym \u2192 pH pr\u00fcfen.",
      "target_ec_ms": 0.5,
      "reference_ec_ms": 0.5,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 1.5, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.1}
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
  "week_end": 11,
  "is_recurring": false,
  "npk_ratio": [0.0, 2.0, 3.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Terra Bloom niedrige Dosis (2 ml/L) + Pure Zym. P+K f\u00fcr Bl\u00fcte und H\u00fclsenbildung. Hitze \u00fcber 30\u00b0C = Bl\u00fctenabwurf! Gleichm\u00e4\u00dfig gie\u00dfen (alle 2 Tage). Alle 14 Tage d\u00fcngen.",
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
      "channel_id": "naehrloesung-pk",
      "label": "P+K-D\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Terra Bloom niedrige Dosis + Pure Zym. P+K f\u00fcr H\u00fclsenbildung. KEIN Terra Grow!",
      "target_ec_ms": 0.6,
      "reference_ec_ms": 0.6,
      "target_ph": 6.5,
      "fertilizer_dosages": [
        {"fertilizer_key": "<terra_bloom_key>", "ml_per_liter": 2.0, "optional": false},
        {"fertilizer_key": "<pure_zym_key>", "ml_per_liter": 1.0, "optional": false}
      ],
      "method_params": {"method": "drench", "volume_per_feeding_liters": 0.1}
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
  "week_start": 12,
  "week_end": 14,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Kein D\u00fcnger. Alle 2\u20133 Tage ernten! \u00dcberreife H\u00fclsen hemmen Neuansatz. Nach der Ernte: Pflanzen abschneiden, Wurzeln im Boden lassen (N-Anreicherung f\u00fcr Nachfolgekultur).",
  "delivery_channels": [
    {
      "channel_id": "wasser-pur",
      "label": "Nur Wasser (Ernte)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Kein D\u00fcnger. Regelm\u00e4\u00dfig gie\u00dfen f\u00fcr H\u00fclsenqualit\u00e4t.",
      "target_ec_ms": 0.0,
      "reference_ec_ms": 0.0,
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
| Fertilizer: Terra Bloom | `spec/knowledge/products/plagron_terra_bloom.md` | `fertilizer_dosages.fertilizer_key` |
| Fertilizer: Pure Zym | `spec/knowledge/products/plagron_pure_zym.md` | `fertilizer_dosages.fertilizer_key` |
| Species: Phaseolus vulgaris | `spec/knowledge/plants/phaseolus_vulgaris.md` | `species.scientific_name` |
| SubstrateType: SOIL | Built-in Enum | `nutrient_plans.recommended_substrate_type` |

---

## 8. Sicherheitshinweise

### Pflanze

- **WARNUNG: Rohe Bohnen sind giftig!** Das Lektin Phasin (Phytohaemagglutinin) wird erst durch mindestens 10--15 Minuten Kochen bei 100 degC vollstaendig zerstoert
- **Niemals roh essen!** Bereits 5--6 rohe Bohnen koennen bei Kindern schwere Vergiftung ausloesen
- **Symptome:** Uebelkeit, Erbrechen, Durchfall, Bauchkraempfe 1--3 Stunden nach Verzehr; bei grossen Mengen Hospitalisierung noetig
- **Einweichwasser** von Trockenbohnen wegschuetten (enthaelt geloestes Phasin)
- **Giftig fuer Katzen und Hunde:** Phasin ist auch fuer Haustiere giftig
- **Kinder besonders gefaehrdet:** Huelsen und rohe Bohnen aus dem Garten sind ein haeufiger Vergiftungsanlass

### Duengemittel

- Plagron-Konzentrate sind nicht zum Verzehr geeignet
- Bei Hautkontakt mit Wasser abspuelen
- Bei Augenkontakt gruendlich mit Wasser spuelen
- Ausserhalb der Reichweite von Kindern aufbewahren
- **Essbare-Ernte-Hinweis:** Mindestens 7 Tage nach letzter Duengung warten bevor Huelsen geerntet werden (2--3 Giesszyklen fuer vollstaendige Salzpassage). Bei der niedrigen Dosierung dieses Plans (max. 2 ml/L TB) und 14-Tage-Intervall ist dies in der Regel automatisch gewaehrleistet.

---

## Quellenverzeichnis

1. Plagron Terra Bloom Produktdaten: `spec/knowledge/products/plagron_terra_bloom.md`
2. Plagron Pure Zym Produktdaten: `spec/knowledge/products/plagron_pure_zym.md`
3. Phaseolus vulgaris Pflanzensteckbrief: `spec/knowledge/plants/phaseolus_vulgaris.md`
4. NutrientPlan Datenmodell: `src/backend/app/domain/models/nutrient_plan.py`
5. PhaseName Enum: `src/backend/app/common/enums.py`

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
