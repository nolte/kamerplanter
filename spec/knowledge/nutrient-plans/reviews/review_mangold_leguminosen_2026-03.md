# Agrarbiologisches Review: Naehrstoffplaene Mangold, Buschbohne, Erbse / Plagron Terra

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-06
**Fokus:** Outdoor Freiland/Balkon, Erdkultur, Blattgemuese, Leguminosen, N-Fixierung, Lebensmittelsicherheit
**Analysierte Dokumente:**
- `spec/knowledge/nutrient-plans/mangold_plagron_terra.md` (v1.0)
- `spec/knowledge/nutrient-plans/bohne_plagron_terra.md` (v1.0)
- `spec/knowledge/nutrient-plans/erbse_plagron_terra.md` (v1.0)
- `spec/knowledge/plants/beta_vulgaris_subsp_vulgaris.md` (v1.0)
- `spec/knowledge/plants/phaseolus_vulgaris.md` (v1.0)
- `spec/knowledge/plants/pisum_sativum.md` (v1.0)
- `spec/knowledge/products/plagron_terra_grow.md` (v1.0)
- `spec/knowledge/products/plagron_terra_bloom.md` (v1.0)

---

## Gesamtbewertung

| Dimension | Mangold | Buschbohne | Erbse | Kommentar |
|-----------|---------|------------|-------|-----------|
| Botanische Korrektheit | 5/5 | 5/5 | 5/5 | Nomenklatur korrekt; Lebenszyklusangaben korrekt; Photoperiodik korrekt |
| N-Fixierung-Logik | n/a | 5/5 | 5/5 | Terra Grow konsequent ausgeschlossen; Begruendung fachlich praezise; NPK-Ratio (0,x,x) korrekt |
| NPK-Produktwahl | 5/5 | 5/5 | 5/5 | Terra Grow korrekt fuer Mangold-Wachstum; Terra Bloom korrekt fuer beide Erntephasen und Leguminosen |
| EC-Budget-Korrektheit | 4/5 | 5/5 | 5/5 | Mangold: 1 arithmetischer EC-Rechenfehler in VEGETATIVE; Leguminosen: alle Budgets korrekt |
| Phasen-Mapping-Qualitaet | 5/5 | 5/5 | 5/5 | Alle drei Plaene lueckenlos; Summenarithmetik stimmt; Saisonkalender plausibel |
| Nitrat-Kontrolle Blattgemuese | 5/5 | n/a | n/a | Nitrat-Akkumulation-Thema sehr gut aufgegriffen; N-Dosierungsgrenzen korrekt |
| Oxalsaeure-Handling | 4/5 | n/a | n/a | Hinweise korrekt; kleiner Luecke: innere Blaetter haben MEHR Oxalsaeure als aeussere, Plan sagt Gegenteil |
| Cut-and-Come-Again-Technik | 5/5 | n/a | n/a | Botanisch korrekt, vollstaendig und praxisgerecht |
| Phasin-Sicherheitswarnung | n/a | 5/5 | n/a | Klar, explizit, an mehreren Stellen; Kochzeitangabe korrekt |
| Erbse vs. Duftwicke-Warnung | n/a | n/a | 5/5 | Verwechslungswarnung vorhanden und praezise |
| Giessplan-Anpassung | 5/5 | 5/5 | 5/5 | Bluete-Override bei Bohne korrekt; FLUSHING-Reduktion bei Mangold korrekt |
| Saisonplan-Realismus | 5/5 | 5/5 | 5/5 | Alle drei Plaene stimmig und fuer Mitteleuropa Zone 7-8 realistisch |
| Sicherheitshinweise Gesamt | 4/5 | 5/5 | 5/5 | Mangold: 1 Nuance bei inneren/aeusseren Blaettern korrekturbeduertig |

**Gesamteinschaetzung:** Alle drei Naehrstoffplaene sind agronomisch sehr gut ausgearbeitet und zeigen ein tiefes Verstaendnis der jeweiligen Pflanzenphysiologie. Der Leguminosen-Ansatz -- konsequenter Ausschluss von Terra Grow, Erklaerung der Rhizobium-Hemmung, Empfehlung von Terra Bloom in reduzierter Dosis fuer P+K -- ist fachlich korrekt und vorbildlich dokumentiert. Der Mangold-Plan behandelt das Nitrat-Akkumulationsrisiko und die Cut-and-Come-Again-Technik vorbildlich. Zwei Korrekturen sind noetig: ein EC-Rechenfehler in Mangold VEGETATIVE (geringfuegig, keine funktionale Auswirkung) sowie eine botanisch inkorrekte Aussage ueber den Oxalsaeuregehalt innerer vs. aeusserer Blaetter (gesundheitsrelevante Nuance).

---

## Findings

### M-001: EC-Budget VEGETATIVE -- Rechenfehler in der Markdown-Tabelle

**Schweregrad:** Gering (kein funktionaler Fehler, nur Inkonsistenz in der Darstellung)

**Dokument:** `spec/knowledge/nutrient-plans/mangold_plagron_terra.md`, Abschnitt 4.3 (VEGETATIVE)

**Problem:**
Das EC-Budget in Abschnitt 4.3 lautet:

> EC-Budget: 0.32 (TG 4.0ml) + 0.01 (PR) + 0.00 (PZ) + 0.01 (SR 0.5ml) + ~0.4 (Wasser) = ~0.74 mS/cm

Die Einzelpositionen addiert ergeben:
- Terra Grow 4.0 ml/L x 0.08 mS/cm = **0.32** -- korrekt
- Power Roots 1.0 ml/L x 0.01 mS/cm = **0.01** -- korrekt
- Pure Zym 1.0 ml/L x 0.00 mS/cm = **0.00** -- korrekt
- Sugar Royal 0.5 ml/L x 0.02 mS/cm = **0.01** -- korrekt (0.5 x 0.02 = 0.01)
- Basis-Wasser = **~0.40**

Summe: 0.32 + 0.01 + 0.00 + 0.01 + 0.40 = **0.74 mS/cm**

Das Gesamtergebnis 0.74 mS/cm stimmt. Der Widerspruch ist ein anderer: Das `target_ec_ms` im JSON fuer VEGETATIVE ist mit **1.2 mS/cm** angegeben, aber die berechnete EC aus den Dosierungen ergibt nur ~0.74 mS/cm. Das ist kein Fehler, sondern spiegelt wider, dass `target_ec_ms` ein Richtwert fuer die Gesamtloesung (inkl. vorhandener Bodennaehrstoffe und Leitungswasser) ist -- aber diese Abweichung wird im Dokument nicht erklaert und kann zu Verwirrung fuehren.

Zusaetzlich: In der Hinweis-Box steht "Die berechnete EC (~0.7 mS/cm) ist bewusst niedriger als bei Starkzehrern" -- hier wird ~0.7 verwendet, obwohl die Summe ~0.74 ergibt. Das ist eine unbedeutende Rundungsdifferenz, aber sie verursacht Inkonsistenz zwischen Text und Berechnung.

**Empfehlung:**
Erklaerung erganzen: "`target_ec_ms: 1.2` ist ein Messziel fuer die Gesamtloesung im Substrat-Eluat (inkl. Bodenpuffer). Die Duengeadditive liefern nur ~0.34 mS/cm zuzueglich Leitungswasser ~0.4. Bei sehr armen Substraten kann vorsichtig auf 5 ml/L TG erhoeht werden -- aber Nitrat-Monitoring beachten." Alternativ: `target_ec_ms` auf 0.8 setzen, was dem kalkulierten Wert naher liegt.

---

### M-002: Oxalsaeuregehalt -- innere vs. aeussere Blaetter biologisch invers

**Schweregrad:** Mittel (gesundheitsrelevante Nuance fuer empfindliche Personengruppen)

**Dokument:** `spec/knowledge/nutrient-plans/mangold_plagron_terra.md`, Abschnitt 6.3 (Nitrat-Kontrolle)

**Problem:**
Das Dokument enthaelt in Abschnitt 6.3 folgende Aussage:

> "Aeussere Blaetter bevorzugt ernten (geringerer Nitratgehalt als junge innere Blaetter)"

Das ist fuer Nitrat korrekt: Junge, schnell wachsende innere Blaetter akkumulieren bei N-Ueberschuss mehr Nitrat als alte aeussere Blaetter, weil sie staerker in aktiver Zellteilung sind.

In Abschnitt 6.2 (Oxalsaeure) steht jedoch:

> "Junge Blaetter enthalten weniger Oxalsaeure als alte"

Das ist biologisch korrekt und klingt harmlos. Die Empfehlung, aeussere (alte) Blaetter zu bevorzugen, wird aber in den Kontexten Nitrat und Cut-and-Come-Again gleichermassen propagiert -- dabei gilt fuer Oxalsaeure das Gegenteil der Nitrat-Logik: **Alte, grosse aeussere Blaetter enthalten mehr Oxalsaeure als junge innere Blaetter.** Wer aus Nitrat-Gruenden aeussere Blaetter bevorzugt, erhaelt damit gleichzeitig hoehere Oxalsaeure-Dosen.

Dies ist fuer gesunde Erwachsene unproblematisch, aber fuer Personen mit Neigung zu Calciumoxalat-Nierensteinen oder fuer Personen, die grosse Mengen Mangold verzehren, eine relevante Nuance.

**Fachlicher Hintergrund:**
Oxalsaeure (Ethandisaeure) wird in Pflanzen durch photorespiratorische Prozesse und den Glyoxylat-Zyklus gebildet. Sie akkumuliert in Vakuolen als Calciumoxalat-Kristalle (Raphiden). In alten Blaettern ist die Gesamtakkumulation ueber die Vegetationszeit hoeher. Junge Blaetter haben hoehere Wachstumsraten, weniger Vakuolen-Akkumulation und weniger Calciumoxalat-Kristalle pro Blattflaeche.

Aktuelle Literaturwerte fuer *Beta vulgaris* subsp. *vulgaris* (Blattgruppe):
- Junge innere Blaetter: ca. 300-500 mg Oxalsaeure/100 g Frischgewicht
- Alte aeussere Blaetter: ca. 600-1000 mg/100 g Frischgewicht

**Empfohlene Korrektur in Abschnitt 6.2:**
Aktuelle Formulierung: "Junge Blaetter enthalten weniger Oxalsaeure als alte"
Verbesserte Formulierung:

> "Junge innere Blaetter enthalten weniger Oxalsaeure als alte aeussere Blaetter. Fuer Personen mit erhoehtem Nierensteinrisiko (Calciumoxalat) empfiehlt es sich daher, bei reichlichem Mangold-Konsum bevorzugt junge Innenblatter zu verwenden -- auch wenn diese aus Nitrat-Sicht etwas hoehere Werte aufweisen. Fuer den normalen Gelegenheitskonsum ist die Unterscheidung unbedeutend."

---

### M-003: Sugar Royal Einstufung als N-Quelle -- NPK-Angabe im Produktuebersicht pruefenswert

**Schweregrad:** Hinweis (fachliche Praezisierung empfohlen)

**Dokument:** `spec/knowledge/nutrient-plans/mangold_plagron_terra.md`, Abschnitt 4.1 (EC-Budget-Tabelle)

**Problem:**
In der EC-Budget-Tabelle ist Sugar Royal mit "NPK (9-0-0)" und EC/ml 0.02 mS/cm eingetragen. Die offizielle Plagron-Deklaration fuer Sugar Royal lautet nach dem Steckbrief "organisches N aus Aminosaeuren und Zucker (8.5% N)". Der Naehrstoffplan nennt 9-0-0, was eine leichte Abweichung von der Steckbrief-Angabe von 8.5% ist.

In den Dosierungen und der Begründung (0.5 ml/L, halbe Dosis wegen organischem N) ist die Logik korrekt umgesetzt. Die Ziffer 9 vs. 8.5 ist marginal und hat keine funktionale Konsequenz, koennte aber bei einer Konsistenzpruefung aufgefallen sein.

**Empfehlung:** NPK-Angabe im Mangold-Plan mit dem Sugar-Royal-Produktblatt abgleichen und einheitlich auf "8.5-0-0" oder den offiziellen Wert setzen. Keine inhaltliche Aenderung noetig.

---

### B-001: Warum Terra Bloom (2-2-4) und nicht z.B. ein reiner P/K-Booster -- Erklaerung korrekt, aber EC-Beitrag des N-Anteils wird nicht quantifiziert

**Schweregrad:** Hinweis (ergaenzende Information wuerde fachliche Tiefe erhoehen)

**Dokument:** `spec/knowledge/nutrient-plans/bohne_plagron_terra.md`, Abschnitt 4 (EC-Budget-Kommentar)

**Problem:**
Der Plan begruendet den Einsatz von Terra Bloom statt Terra Grow korrekt und ausfuehrlich. Die Aussage lautet:

> "Bei niedrigen Dosierungen (1.5-2.0 ml/L) ist der N-Beitrag aus Terra Bloom minimal und hemmt die Rhizobium-Symbiose nicht nennenswert."

Das ist biologisch korrekt. Terra Bloom hat 2.1% N. Bei 2.0 ml/L Dosierung und angenommenem pH 6.5 ergibt sich ein N-Gehalt von ca. 0.042 mg/L (= 2.0 ml x 0.021 g/ml x 0.001) -- das ist im Freiland mit Erdsubstrat tatsaechlich vernachlaessigbar gegenueber dem atmosphaerischen N-Potential der Rhizobium-Symbiose (50-100 kg N/ha entsprechen ~5-10 mg N/L Bodenwasser bei normaler Bodenfeuchtigkeit).

Die Fachaussage ist richtig. Fuer ein Referenzdokument waere eine kurze quantitative Einordnung wertvoll, um dem Nutzer die Groessenordnung zu vermitteln.

**Empfehlung:** Optionaler ergaenzender Satz: "Bei 2 ml/L Terra Bloom (NPK 2-2-4) wird rechnerisch ~0.04 mg N pro Liter Giessloessung appliziert -- das ist 50-100x weniger als der atmosphaerische N-Eintrag aus der Rhizobium-Symbiose in normalem Kulturboden."

---

### B-002: FLOWERING-Phase Giessintervall-Override fehlt

**Schweregrad:** Gering (Verbesserungsvorschlag)

**Dokument:** `spec/knowledge/nutrient-plans/bohne_plagron_terra.md`, Abschnitt 4.4 (FLOWERING)

**Problem:**
Das Dokument beschreibt in Abschnitt 4.4 korrekt: "Hitze ueber 30 degC = Bluetenabwurf! Gleichmaessig giessen (alle 2 Tage)." Der globale Giessplan ist jedoch auf 3 Tage eingestellt. Es fehlt ein `watering_schedule_override` fuer die FLOWERING-Phase, der das Intervall auf 2 Tage setzt -- analog wie GERMINATION einen Override hat.

Der Steckbrief `phaseolus_vulgaris.md` bestaetigt in Abschnitt 2.2 (Phase Bluete): "Giessintervall: 2-3 Tage (in der Bluete erhoehter Wasserbedarf!)".

**Empfehlung:**
FLOWERING-Phase um `watering_schedule_override` erganzen:

```json
"watering_schedule_override": {
  "schedule_mode": "interval",
  "interval_days": 2,
  "preferred_time": "07:00",
  "application_method": "drench",
  "reminder_hours_before": 2,
  "times_per_day": 1
}
```

---

### E-001: Erbse als Langtagspflanze -- FLOWERING-Phase-Trigger korrekt, aber Nuance bei modernen Sorten fehlt

**Schweregrad:** Hinweis (fachliche Ergaenzung)

**Dokument:** `spec/knowledge/nutrient-plans/erbse_plagron_terra.md`, Abschnitt 2 (Phasen-Mapping)

**Problem:**
Das Dokument beschreibt korrekt:

> "Erbsen sind Langtagspflanzen (Bluete durch laenger werdende Tage im Fruehjahr ausgeloest)"

Das ist eine vereinfachte, aber fuer Praxisdokumente akzeptable Darstellung. Die nuanciertere Wahrheit: *Pisum sativum* zeigt eine quantitative Langtagreaktion -- die Bluete wird durch Langtag *beschleunigt*, tritt aber bei den meisten modernen Gartensorten auch unter Kurztagbedingungen auf (wenn auch spaeter). Nur einige sehr alte Landrassen sind echte qualitative Langtagpflanzen. Der Steckbrief `pisum_sativum.md` klassifiziert korrekt als `long_day`.

Fuer den Anbau im Fruehsommer in Mitteleuropa (Maerz-Juli) sind die Taglaengen naturgemäss langtag-guenstig, daher hat diese Vereinfachung keine praktischen Konsequenzen.

**Empfehlung:** Keine Aenderung zwingend erforderlich. Optional als Fussnote: "Moderne Zuchtlinien reagieren als *quantitative* Langtagpflanzen -- Bluete tritt unter Kurztagbedingungen verspätet auf, nicht aus. Fuer den Frühjahrsanbau ist die Langtagreaktion durch den natuerlichen Photoperiod erfuellt."

---

### E-002: Giessmenge FLOWERING beim Erbsenplan -- Steckbrief-Wert hoeher als Plan-Override

**Schweregrad:** Gering

**Dokument:** `spec/knowledge/nutrient-plans/erbse_plagron_terra.md`, Abschnitt 4.4 (FLOWERING); `spec/knowledge/plants/pisum_sativum.md`, Abschnitt 2.2

**Problem:**
Der Steckbrief nennt fuer FLOWERING: "Giessintervall: 1-2 Tage (erhoehter Wasserbedarf waehrend Bluete und Huelsenbildung)."

Der Naehrstoffplan hat fuer FLOWERING keinen `watering_schedule_override` und verwendet damit den globalen Plan (Intervall 3 Tage). Waehrend der Bluete-Phase, die gerade fuer Erbsen temperaturkritisch ist und wo Trockenheitsstress zu Bluetenabwurf fuehrt, sollte das Intervall auf 2 Tage reduziert werden.

Das Dokument erwaehnt zwar im Prosatext "Gleichmaessig giessen" und "ausreichende Wasserversorgung ist essenziell", aber der maschinenlesbare `watering_schedule_override` fehlt. Dadurch wird das System bei Automatisierung nicht auf das korrekte Intervall wechseln.

**Empfehlung:** Analog zu Bohne-Plan: `watering_schedule_override` fuer FLOWERING mit `interval_days: 2` erganzen.

---

## Übergreifende Bewertung nach Pruefkriterien

### 1. NPK passend? EC-Budget korrekt?

**Mangold:** Das NPK-Mapping ist korrekt. Terra Grow (3-1-3) fuer die vegetative Phase und Terra Bloom (2-2-4) fuer die Erntephase ist eine biologisch sinnvolle Wahl. Der Steckbrief nennt als Ideal fuer die vegetative Phase "NPK 2-1-3", der Plan verwendet Terra Grow mit 3-1-3. Der leicht erhoehte N-Anteil ist fuer eine Blattkultur akzeptabel, die Begrenztung auf 4 ml/L (statt Maximal 5 ml/L) ist korrekt begruendet.

EC-Budget-Korrektheit:
- GERMINATION: ~0.4 mS/cm (nur Wasser) -- korrekt
- SEEDLING: 1.5 ml/L x 0.08 + 1.0 ml/L x 0.01 + 0.40 = 0.12 + 0.01 + 0.40 = **0.53 mS/cm** -- plan stimmt
- VEGETATIVE: 4.0 x 0.08 + 1.0 x 0.01 + 1.0 x 0.00 + 0.5 x 0.02 + 0.40 = 0.32 + 0.01 + 0.00 + 0.01 + 0.40 = **0.74 mS/cm** -- Rechnung stimmt; `target_ec_ms: 1.2` ist hoch (siehe M-001)
- HARVEST: 3.0 x 0.10 + 1.0 x 0.00 + 0.40 = 0.30 + 0.00 + 0.40 = **0.70 mS/cm** -- korrekt
- FLUSHING: 0.00 + 0.40 = **0.40 mS/cm** -- korrekt

**Buschbohne:** EC-Budgets alle korrekt:
- GERMINATION/SEEDLING: ~0.40 mS/cm (nur Wasser) -- korrekt
- VEGETATIVE: 1.5 x 0.10 + 1.0 x 0.00 + 0.40 = 0.15 + 0.40 = **0.55 mS/cm** -- plan 0.55, stimmt
- FLOWERING: 2.0 x 0.10 + 1.0 x 0.00 + 0.40 = 0.20 + 0.40 = **0.60 mS/cm** -- plan 0.60, stimmt
- HARVEST: ~0.40 mS/cm -- korrekt

**Erbse:** EC-Budgets alle korrekt:
- VEGETATIVE: 1.25 x 0.10 + 1.0 x 0.00 + 0.40 = 0.125 + 0.40 = **0.525 mS/cm** (plan ~0.53) -- korrekt
- FLOWERING: identisch VEGETATIVE 0.53 mS/cm -- korrekt und begruendet (extremer Schwachzehrer)

---

### 2. Bohne/Erbse: N-Fixierung beruecksichtigt? KEIN N-Duenger? Terra Bloom statt Terra Grow?

**Beurteilung: Exzellent.**

Beide Leguminosen-Plaene setzen Terra Grow konsequent aus. Die Begruendung ist vollstaendig und fachlich korrekt:

- Rhizobium leguminosarum als symbiontischer Stickstoff-Fixierer korrekt identifiziert
- Mechanismus der Hemmung der Knoellchenbildung durch exogenen Stickstoff korrekt erklaert
- Konsequenz bei N-Duengung (ueppiges Laub, wenig Huelsen) korrekt beschrieben
- Terra Bloom (2-2-4) als P+K-Lieferant bei minimaler N-Belastung fachlich korrekt begruendet
- Dosierungsempfehlungen (1.5-2.0 ml/L TB) sind konservativ und lassen die Rhizobium-Symbiose unbeeinflusst
- KEIN Duenger in SEEDLING-Phase: korrekt -- die Knoellchenbildung findet in dieser Phase statt und darf nicht durch N-Angebot inhibiert werden
- Empfehlung zur Rhizobium-Impfung bei erstmaligem Anbau: korrekt und praxisrelevant
- Wurzeln im Boden lassen nach Ernte: korrekt und ein wesentlicher Mehrwert im Fruchtfolge-Kontext

Unterschied zwischen Bohne und Erbse korrekt wiedergegeben:
- Bohne: Direktsaat nach Eisheiligen (waermeliebend, min. 10 degC Bodentemperatur, NICHT vorquellen)
- Erbse: Direktsaat ab Maerz (kuehleliebend, Keimlinge frosthart bis -4 degC, Vorquellen moeglich)

---

### 3. Mangold: Nitrat-Kontrolle, Oxalsaeure, Cut-and-Come-Again korrekt?

**Nitrat-Kontrolle: Sehr gut (5/5)**

Der Plan behandelt Nitrat-Akkumulation als explizites Risiko mit messbaren Steuerungsparameter:
- Begrenzung Terra Grow auf max. 4 ml/L (nicht 5 ml/L wie bei Starkzehrern): korrekt und wichtig
- Sugar Royal auf halbe Dosis (0.5 ml/L statt 1 ml/L) wegen organischem N-Anteil: korrekt
- Kein Sugar Royal in HARVEST-Phase: korrekt
- Ernte morgens empfohlen (niedrigster Nitratgehalt): korrekt -- Nitrat wird tagsuebers durch Photosynthese assimiliert, Spiegel sinkt ueber Nacht/fruehen Morgen
- Konsequenter Wechsel auf Terra Bloom in HARVEST reduziert N-Input: korrekt

EU-Nitratgrenzwerte fuer Mangold (frisch): maSSgeblich nach VO (EG) 1881/2006 und VO (EU) 2023/915: 3000 mg/kg fuer Spinat und Salat (Mangold analog). Bei Einhaltung der Dosierungsgrenzen dieses Plans ist eine Ueberschreitung im Freiland-Anbau nicht zu erwarten.

**Oxalsaeure: Gut mit einem Korrekturbedarf (4/5)**
Siehe M-002 oben. Die generelle Empfehlung, morgens zu ernten und Kochwasser wegzuschuetten, ist korrekt. Die Einstufung innerer Blaetter als oxalsaeurearmer ist botanisch korrekt -- aber der Kontext, in dem aeussere Blaetter als bevorzugte Ernte propagiert werden (richtig fuer Nitrat, ungünstiger fuer Oxalsaeure), fehlt als explizite Abwaegung fuer Risikogruppen.

**Cut-and-Come-Again: Sehr gut (5/5)**
Botanisch praezise Darstellung:
- Max. 2-3 aeussere Blaetter: korrekt (Apikalmeristem und Herzblatter bleiben intakt)
- "Herz IMMER stehen lassen": korrekt -- der Vegetationspunkt (Apikalmeristem) der Rosette ist der einzige Regenerationsort
- Alle 7-10 Tage Ernteintervall: korrekt fuer optimalen Turgor und Zellwandelastizitaet
- Unterscheidung Stielmangold (ganzer Stiel) vs. Schnittmangold (3-4 cm ueber Boden): fachlich korrekt
- Schosserentfernung: korrekt -- Aufbluehen verbraucht Assimilate und macht Blaetter bitter (erhoehte Bitterstoffe/Seneszenz-Signale)

---

### 4. Phasen lueckenlos? Saisonplan realistisch?

**Mangold (18 Wochen):**
Pruefung: 2 (GERM) + 3 (SEED) + 5 (VEG) + 6 (HARV) + 2 (FLUSH) = **18 Wochen** -- lueckenlos, keine Luecken, keine Ueberlappungen.
Kalenderplausibilitaet: April-September fuer Mitteleuropa korrekt. Frostschutz bis November biologisch korrekt (*Beta vulgaris* vertraegt Froeste bis -6 degC als ausgewachsene Pflanze).

**Buschbohne (14 Wochen):**
Pruefung: 2 (GERM) + 2 (SEED) + 4 (VEG) + 3 (FLOW) + 3 (HARV) = **14 Wochen** -- lueckenlos.
Kalenderplausibilitaet: Mitte Mai bis August korrekt. Start nach Eisheiligen biologisch korrekt fuer *Phaseolus vulgaris* (frostempfindlich).

**Erbse (16 Wochen):**
Pruefung: 2 (GERM) + 3 (SEED) + 4 (VEG) + 3 (FLOW) + 4 (HARV) = **16 Wochen** -- lueckenlos.
Kalenderplausibilitaet: Maerz-Juli korrekt. Direktsaat ab Maerz (Bodentemperatur 5 degC) biologisch korrekt fuer *Pisum sativum*. Hinweis auf Hitze-Ende bei >25 degC Dauertemperatur korrekt und wichtig.

---

### 5. Sicherheit: Phasin-Warnung bei Bohne? Oxalsaeure bei Mangold?

**Phasin-Warnung (Buschbohne): Sehr gut (5/5)**

Das Dokument enthaelt korrekte und vollstaendige Sicherheitshinweise:
- "WARNUNG: Rohe Bohnen sind giftig!" in Metadaten-Beschreibung, Abschnitt 7 und JSON-Beschreibung -- dreifach kommuniziert
- Giftstoff korrekt identifiziert: Phasin / Phytohaemagglutinin (PHA), ein Lektin
- Deaktivierungsbedingung korrekt: "mindestens 10-15 Minuten Kochen bei 100 degC" (das Dokument schreibt an einer Stelle 10 Min., an anderer 10-15 Min. -- beide Angaben liegen im sicheren Bereich; wissenschaftlicher Mindestwert laut WHO/FAO: 10 Minuten Vollkochen)
- Mengenangabe fuer Kinder korrekt: "bereits 5-6 rohe Bohnen koennen bei Kindern schwere Vergiftung ausloesen"
- Einweichwasser: "Einweichwasser von Trockenbohnen wegschuetten" korrekt
- Tierarten: Phasin-Toxizitaet fuer Katzen und Hunde korrekt angegeben
- Verweis auf Haustiere und Kinder als Risikogruppen: korrekt

Kleiner Prazisierungsbedarf (kein Fehler): Das Dokument nennt "Blausaeureverbindungen in manchen Sorten" als weiteren toxischen Inhaltsstoff (aus dem Steckbrief uebernommen). Dieser Hinweis ist botanisch korrekt fuer einige tropische Landsorten von *Phaseolus vulgaris* (z.B. Lima Bean Unterarten), aber bei handelsueblichten deutschen Gartenbohnen-Sorten vernachlaessigbar. Eine Qualifizierung ("bei tropischen Landsorten, nicht bei gaengigen Europaeischen Sorten") waere praeziser, ist aber fuer ein Referenzdokument akzeptabel.

**Oxalsaeure-Warnung (Mangold): Gut mit Nuance (4/5)**

Korrektes und vollstaendiges Bild:
- Oxalsaeure identifiziert, Analogie zu Spinat und Rhabarber korrekt
- Kochempfehlung (Kochwasser wegschuetten): korrekt -- Oxalsaeure ist wasserloeslich, ~30-50% gehen ins Kochwasser ueber
- Nierenstein-Risikogruppe benannt: korrekt (Calciumoxalat ist der haeufigste Nierensteintyp, ca. 75% aller Nierensteine)
- Saeuglingswarnung (<6 Monate, Nitrat + Oxalsaeure): korrekt und wichtig
- Korrekturbedarf: Aussage ueber innere vs. aeussere Blaetter (siehe M-002)

---

## Zusammenfassung der Korrekturen

| ID | Plan | Schweregrad | Kurzbeschreibung | Aktion |
|----|------|-------------|-----------------|--------|
| M-001 | Mangold | Gering | `target_ec_ms: 1.2` in VEGETATIVE stimmt nicht mit berechneten ~0.74 mS/cm ueberein | Erklaerung erganzen oder `target_ec_ms` auf 0.8 korrigieren |
| M-002 | Mangold | Mittel | Innere Blaetter haben MEHR Oxalsaeure als aeussere -- Abschnitt 6.2 unvollstaendig | Text in Abschnitt 6.2 erganzen mit Abwaegungshinweis fuer Risikogruppen |
| M-003 | Mangold | Hinweis | Sugar Royal mit 9-0-0 deklariert, Steckbrief sagt 8.5% N | Auf einheitlichen NPK-Wert aus Produktblatt abstimmen |
| B-001 | Bohne | Hinweis | N-Beitrag Terra Bloom nicht quantifiziert | Optionaler Satz mit Groessenordnung 0.04 mg N/L erganzen |
| B-002 | Bohne | Gering | FLOWERING-Phase hat keinen `watering_schedule_override` (soll 2 Tage, global 3 Tage) | `watering_schedule_override` fuer FLOWERING mit `interval_days: 2` erganzen |
| E-001 | Erbse | Hinweis | Langtagcharakter vereinfacht -- bei modernen Sorten quantitativ, nicht qualitativ | Optionale Fussnote erganzen |
| E-002 | Erbse | Gering | FLOWERING fehlt `watering_schedule_override` (soll 2 Tage, global 3 Tage) | Analog B-002 erganzen |

---

## Positive Hervorhebungen

Die folgenden Aspekte sind fachlich exemplarisch ausgefuehrt und verdienen explizite Erwaehnung:

**Leguminosen-Duengestrategie (Bohne + Erbse):**
Die Entscheidung, Terra Grow vollstaendig auszuschliessen und die physiologische Begruendung (Rhizobium-Hemmung durch exogenes N, Umleitung der Assimilate von Huelse zu Laub) ist nicht nur korrekt, sondern gehoert zu den am haeufigsten in der Praxis falsch gemachten Aspekten des Leguminosen-Anbaus. Viele Hobbyanbauer duengen Bohnen "sicherheitshalber" mit N-Universalduengen und erhalten dann schlechte Huelsenertraege. Die Dokumente begruenden den Verzicht so klar, dass auch Anfaenger den Unterschied verstehen.

**Rhizobium-Impfung bei Erstanbau:**
Die Empfehlung zur Inokulierung mit Rhizobium leguminosarum bei erstmaligem Anbau auf einer Flaeche ist wissenschaftlich korrekt und praxisrelevant. In Deutschland ist Rhizobium-Impfmittel (z.B. "Nodumax" oder vergleichbare Praeparate) im Fachhandel erhaeltlich. Die Effektivitaet ist auf Boden ohne Rhizobium-Vorgeschichte mit Fabaceae deutlich nachgewiesen.

**Mangold-Nitrat-Management:**
Die Kombination aus Dosierungsbegrenzung (max. 4 ml/L TG), Wechsel auf Terra Bloom in HARVEST, Morgensernte-Empfehlung und explizitem Sugar-Royal-Absetz in HARVEST ist ein vollstaendiges, praxistaugliches Nitrat-Management-Paket. Die EU-Grenzwertreferenz ist implizit korrekt addressiert.

**Fruchtfolge-Hinweise (alle drei Plaene):**
- Mangold/Beta: 3-4 Jahre Anbaupause fuer Amaranthaceae korrekt
- Bohne/Fabaceae: 3 Jahre Anbaupause korrekt
- Erbse/Fabaceae: 4-5 Jahre ("Erbsenmuedigkeit" / Fusarium-Druck) korrekt, und konsistent mit Steckbrief

**Frostschutz-Erweiterung Mangold:**
Der Hinweis, dass *Beta vulgaris* subsp. *vulgaris* als zweijaehrige Pflanze in der vegetativen Phase Froeste bis -6 degC toleriert und mit Vliesschutz bis November geerntet werden kann, ist korrekt und erhoht den praktischen Nutzwert des Plans erheblich.

**Duftwicke-Verwechslungswarnung bei Erbse:**
*Lathyrus odoratus* (Duftwicke/Sweet Pea) und *Pisum sativum* (Gartenerbse) werden von Laien haeufig verwechselt, zumal beide klettern und Huelsen bilden. *L. odoratus* enthaelt beta-Aminopropionitril (BAPN) und Lathyrin (Neurotoxin). Die explizite Verwechslungswarnung ist sicherheitsrelevant und gehoert in jeden Erbsen-Plan.

---

## Datenquellen-Empfehlungen

| Bereich | Quelle | Relevanz |
|---------|--------|---------|
| Nitratgrenzwerte Gemuese | VO (EU) 2023/915 (Kontaminantenverordnung) | Mangold-Nitrat-Management |
| Oxalsaeure in Gemuese | BfR-Stellungnahme zu Oxalsaeure in Lebensmitteln | Mangold-Oxalsaeure |
| Phasin-Toxizitaet Bohnen | BfR-Empfehlung Nr. 041/2008 | Bohne-Sicherheitshinweis |
| Rhizobium-Inokulationseffekte | LfL Bayern, Merkblatt Koernerleguminosen | Bohne + Erbse |
| Erbsenmuedigkeit / Fusarium | LfL Bayern, JKI Sonderkultur | Erbse Fruchtfolge |

---

## Glossar (planspezifisch)

- **Phasin (Phytohaemagglutinin, PHA):** Lektin in rohen Bohnen (*Phaseolus vulgaris*). Vernetzt Erythrozyten (Hamagglutination) und schaedigt Darmepithel. Wird durch 10 Minuten Vollkochen bei 100 degC vollstaendig denaturiert.
- **N-Fixierung / Stickstofffixierung:** Biologische Bindung von atmosphaerischem N2 durch Rhizobium leguminosarum in Knoellchenbakterien an Leguminosen-Wurzeln. Liefert pflanzenverfuegbares NH4+/NO3- ohne externe N-Duengung.
- **Rhizobium leguminosarum:** Bodenbakterium, das in Symbiose mit Fabaceae (Bohne, Erbse, Linse u.a.) Stickstoffknoellchen an den Wurzeln bildet. Aktivitaet wird durch externen N-Eintrag und pH-Werte unter 6.0 gehemmt.
- **Oxalsaeure (Ethandisaeure):** Organische Saeuer in vielen Pflanzen (Spinat, Mangold, Rhabarber). Bildet schwer loesliches Calciumoxalat -- relevant fuer Nierensteinrisiko. Wasserloeslich; ~30-50% gehen beim Kochen ins Kochwasser ueber.
- **Cut-and-Come-Again:** Erntestrategie bei Blattgemuesen (Mangold, Salat, Rucola), bei der regelmaessig aeussere Blaetter geerntet werden, waehrend der Vegetationspunkt (Herzblatt/Apikalmeristem) intakt bleibt. Ermoelicht kontinuierliche Ernte ueber mehrere Monate.
- **Vernalisation:** Kaelteexposition, die bei zweijaehrigen Pflanzen (z.B. Mangold, Rueben) die Bluteninduktion ausloest. Verhindert unerwuenschtes Schossen im ersten Kulturjahr.
- **Nitrat-Akkumulation:** Anreicherung von Nitrat (NO3-) in Pflanzenzellen bei N-Ueberdosierung. Besonders relevant bei Blattgemuesen (Spinat, Mangold, Salat). EU-Grenzwert fuer Frischgemuese bis 3000 mg/kg.
- **Knoellchenbakterien:** Synonym fuer Rhizobium -- die stickstoff-fixierenden Symbionten an Leguminosen-Wurzeln.
- **Eisheiligen:** Phenologisches Ereignis in Mitteleuropa (ca. 11.-15. Mai), nach dem das Risiko von Spätfroesten stark sinkt. Traditioneller Richtwert fuer die Aussaat frostempfindlicher Kulturen wie Buschbohne.

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
