# Agrobiologischer Review: Starkzehrer Frucht- und Kohlgemuese
## Plagron Terra-Linie -- Naehrstoffplaene

**Erstellt:** 2026-03-06
**Reviewer:** Agrarbiologie-Subagent (CEA / Indoor-Anbau / Vegetationssteuerung)
**Reviewte Plaene:**
- `spec/ref/nutrient-plans/paprika_plagron_terra.md`
- `spec/ref/nutrient-plans/gurke_plagron_terra.md`
- `spec/ref/nutrient-plans/zucchini_plagron_terra.md`
- `spec/ref/nutrient-plans/rosenkohl_plagron_terra.md`
- `spec/ref/nutrient-plans/sellerie_plagron_terra.md`
- `spec/ref/nutrient-plans/lauch_plagron_terra.md`

**Referenz-Produktdaten:**
- `spec/ref/products/plagron_terra_grow.md` (NPK 3-1-3, EC/ml 0.08 mS/cm)
- `spec/ref/products/plagron_terra_bloom.md` (NPK 2-2-4, EC/ml 0.10 mS/cm)

**Referenz-Steckbriefe:**
- `spec/ref/plant-info/capsicum_annuum.md`
- `spec/ref/plant-info/cucumis_sativus.md`
- `spec/ref/plant-info/brassica_oleracea_var_gemmifera.md`
- `spec/ref/plant-info/apium_graveolens_var_rapaceum.md`
- `spec/ref/plant-info/allium_porrum.md`

---

## Gesamtuebersicht

| Plan | Bewertung | Kritische Fehler | Korrekturen noetig |
|------|-----------|-----------------|-------------------|
| Paprika | AKZEPTIERT mit Korrekturen | 0 | 3 (1 systemisch, 2 minor) |
| Gurke | AKZEPTIERT mit Korrekturen | 0 | 2 (1 systemisch, 1 minor) |
| Zucchini | AKZEPTIERT mit Korrekturen | 0 | 3 (1 systemisch, 2 minor) |
| Rosenkohl | AKZEPTIERT mit Korrekturen | 0 | 2 (1 systemisch, 1 minor) |
| Sellerie | AKZEPTIERT mit Korrekturen | 0 | 2 (1 systemisch, 1 minor) |
| Lauch | AKZEPTIERT mit Korrekturen | 0 | 3 (1 systemisch, 2 spezifisch) |

**Keine der sechs Plaene enthaelt fachlich falsche Angaben, die eine Ablehnung begruenden wuerden.** Alle Plaene sind agrobiologisch fundiert, zeigen korrekte Phasen-Abfolgen, plausible Duengungsintensitaeten und relevante Kulturhinweise. Die Korrekturpunkte betreffen durchweg Datenkonsistenz und Praezision, keine inhaltlichen Fehler.

---

## Systemischer Befund (gilt fuer alle 6 Plaene)

### S-001: target_ec_ms weicht strukturell von berechneter Dosierungs-EC ab

**Schweregrad:** Mittel -- systemische Inkonsistenz

**Betroffene Felder:** `delivery_channel.target_ec_ms` in allen Planphasen aller sechs Dokumente

**Befund:** Die `target_ec_ms`-Werte in den Lieferkanal-Definitionen sind als **Sollwerte fuer das Bodensystem** angegeben (repraesentieren die angestrebte Ernaehrungsintensitaet im Substrat bzw. im Bodenwasser), waehrend die aus den Dosiertabellen berechenbaren EC-Werte der Giessloesungen deutlich darunterliegen:

| Phase | target_ec_ms (gesetzt) | berechnete Giessloesung-EC | Differenz |
|-------|----------------------|--------------------------|-----------|
| SEEDLING | 0.6 mS/cm | ~0.53 mS/cm | +0.07 |
| VEGETATIVE | 1.5 mS/cm | ~0.83 mS/cm | +0.67 |
| FLOWERING | 1.8 mS/cm | ~0.92--1.05 mS/cm | +0.75--0.88 |
| HARVEST | 1.5 mS/cm | ~0.80 mS/cm | +0.70 |

Berechnung Beispiel VEGETATIVE (Paprika, Gurke, Lauch):
- Terra Grow 5 ml/L x 0.08 mS/cm = 0.40 mS/cm
- Sugar Royal 1 ml/L x 0.02 mS/cm = 0.02 mS/cm
- Pure Zym 1 ml/L x 0.00 mS/cm = 0.00 mS/cm
- Power Roots 0.5 ml/L x 0.01 mS/cm = 0.005 mS/cm
- Leitungswasser-Basis: ~0.40 mS/cm
- **Summe: ca. 0.83 mS/cm**

Die Plaene enthalten Erklaerungshinweise zur "Erdkultur-Pufferung", aber diese Erklaerungen befinden sich nur in Prosa-Kommentaren. Das `target_ec_ms`-Feld selbst ist nicht kommentierbar -- ein KA-System, das dieses Feld als Dosier-Schwelle oder Soll-Messwert interpretiert, wuerde entweder ueberdosieren (versucht, den Wert durch hoehere Dosiermenge zu erreichen) oder falsche Alarme ausloesen (misst 0.83 mS/cm und meldet Unterschreitung von Sollwert 1.5 mS/cm).

**Fachliche Begruendung:** Bei Erdkultur (SOIL) gibt der `target_ec_ms`-Wert des Lieferkanals die angestrebte EC im Substratporen-/Bodenwasser an, nicht die EC der zugefuehrten Giessloesung. Der Boden puffert und akkumuliert Naehrstoffe. Eine Giessloesung mit 0.83 mS/cm kann im bewurzelten Substrat kurzfristig EC-Werte von 1.5--2.0 mS/cm aufbauen. Diese Interpretation ist agrobiologisch korrekt -- aber sie muss im Datenschema explizit unterschieden werden.

**Korrekturvorschlag Option A (Feldsemantikaenderung):** Das Feld umbenennen in `target_substrate_ec_ms` und ein separates Feld `giessloesung_ec_ms` ergaenzen, das die tatsaechlich berechnete EC der applizierten Loesung repraesentiert. Dann sind beide Werte korrekt und eindeutig.

**Korrekturvorschlag Option B (Feldbeschreibung):** Wenn eine Umstrukturierung nicht moeglich ist, muss die Feldbeschreibung in der Datenschema-Dokumentation klar definieren: "Bei Substratkultur (SOIL, COCO): Zielwert im Substrat-Porenwasser (nach Aufbau des Gleichgewichts), nicht EC der applizierten Giessloesung." Zusaetzlich sollte ein Kommentarfeld je Delivery-Channel-Eintrag eingefuehrt werden.

**Korrekturvorschlag Option C (Feldwerte anpassen):** Die `target_ec_ms`-Werte auf die tatsaechliche Giessloesung-EC setzen (0.53 / 0.83 / 0.92 / 0.80) und die hoeheren Substrat-EC-Zielwerte in einem neuen separaten Feld fuhren. Das waere semantisch sauberster.

**Empfehlung:** Option A -- klare Feldsemantik-Trennung verhindert zukuenftige Implementierungsfehler.

---

### S-002: Beschriftung "Viertel-Dosis" fachlich ungenau

**Schweregrad:** Niedrig -- Bezeichnungsfehler

**Betroffene Plaene:** Paprika, Gurke, Zucchini, Rosenkohl (SEEDLING-Phase)

**Befund:** Die SEEDLING-Phase verwendet 1.5 ml/L Terra Grow und bezeichnet dies in Hinweistexten als "Viertel-Dosis". Die maximale Herstellerdosis betraegt 5 ml/L.

- Halbe Dosis (Plagron offiziell): 2.5 ml/L
- Viertel-Dosis (25% von 5 ml/L): 1.25 ml/L
- Tatsaechliche Dosis: 1.5 ml/L = 30% der Maximaldosis

**Korrekturvorschlag:** Bezeichnung aendern zu "Starterdosis" oder "reduzierte Anfangsdosis (1.5 ml/L)" -- oder auf 1.25 ml/L absenken, wenn die Bezeichnung "Viertel-Dosis" beibehalten werden soll. Fuer empfindliche Jungpflanzen (besonders Paprika) ist 1.25 ml/L sogar agrobiologisch vorzuziehen, da Paprika in der Keimlings-Phase besonders salzstressempfindlich ist.

---

## Plan 1: Paprika (Capsicum annuum)

### Gesamtbewertung: AKZEPTIERT mit Korrekturen

**Staerken:**
- Phasen-Mapping fachlich korrekt und lueckenlos (3+6+7+6+6+2 = 30 Wochen, lueckenlos)
- PK 13-14 korrekt eingesetzt: nur in Woche 19-20 (peak Fruchtansatz), korrekte Dosisreduktion von Terra Bloom auf 70% beruecksichtigt
- BER-Praevention (Bluetenendstueckfaeule) durch gleichmaessige Bewaesserungshinweise korrekt adressiert
- Toxizitaet korrekt: Solanin + Capsaicin als Gefahr fuer Katzen und Hunde, unreife Fruechte explizit benannt
- Koenigsbluete-Handling agrobiologisch korrekt beschrieben
- Eisheiligen-Timing (15. Mai) fuer Mitteleuropa korrekt
- Fruchtfolge 3-4 Jahre Solanaceae korrekt

**NPK-Ratio-Bewertung:**

| Phase | Plagron-Produkt NPK | Steckbrief-Ziel NPK | Abweichung |
|-------|---------------------|---------------------|-----------|
| VEGETATIVE (Terra Grow) | 3-1-3 | 3-1-2 | K +1 (akzeptabel) |
| FLOWERING (Terra Bloom) | 2-2-4 | 2-2-3 | K +1 (akzeptabel) |
| HARVEST (Terra Bloom red.) | 2-2-4 | 1-2-3 | N +1 (akzeptabel) |

Die Abweichungen sind produktbedingt (Terra-Linie hat feste NPK-Verhaeltnisse) und agrobiologisch akzeptabel. Das leicht erhoehte K in VEGETATIVE foerdert Zellwandstabilitaet -- kein Nachteil fuer Paprika.

**Spezifische Korrekturen:**

#### P-001: Bezeichnung "Viertel-Dosis" ungenau
Siehe systemischen Befund S-002. Gilt fuer SEEDLING-Phase.

#### P-002: target_ec_ms Diskrepanz
Siehe systemischen Befund S-001.

#### P-003: pH-Ziel im Kontext BER
**Befund:** Durchgaengig pH 6.0. Fuer BER-Praevention ist Calcium-Transport entscheidend. Bei pH 6.0 ist Ca-Verfuegbarkeit gut, aber bei leichter pH-Absenkung Richtung 5.8 (Sommerregenwasser im Freiland) koennte Ca-Aufnahme beeintraechtigt werden.
**Empfehlung:** Hinweis ergaenzen: "pH nicht unter 5.8 fallen lassen -- Calcium-Aufnahme und BER-Praevention". Kein struktureller Fehler, aber wertvoller Praxishinweis.

---

## Plan 2: Gurke (Cucumis sativus)

### Gesamtbewertung: AKZEPTIERT mit Korrekturen

**Staerken:**
- Phasen-Mapping korrekt und lueckenlos (1+3+4+4+8+2 = 22 Wochen)
- Kein Pikieren -- biologisch korrekt (Gurken sind wurzelempfindlich, Pfahlwurzelsystem)
- Wassertemperatur-Hinweise (18-24 degC) relevant und korrekt -- Gurken reagieren empfindlich auf kaltes Giesswater
- PK 13-14 korrekt eingesetzt (nur Wochen 10-11, peak Fruchtansatz)
- Cucurbitacin-Toxizitaetswarnung vorhanden und korrekt formuliert
- HARVEST-Phase mit 8 Wochen realistisch (Juli-August Haupternte)
- Taeglich ernten-Hinweis fachlich korrekt (Ueberreife hemmt Neuansatz)

**NPK-Ratio-Bewertung:**

| Phase | Plagron-Produkt NPK | Steckbrief-Ziel NPK | Abweichung |
|-------|---------------------|---------------------|-----------|
| VEGETATIVE (Terra Grow) | 3-1-3 | 3-1-2 | K +1 (akzeptabel) |
| FLOWERING (Terra Bloom) | 2-2-4 | 2-2-3 | K +1 (akzeptabel) |
| HARVEST (Terra Bloom red.) | 2-2-4 | 1-2-3 | N +1 (akzeptabel) |

Identisches Muster wie Paprika -- produktbedingt, agrobiologisch akzeptabel.

**Spezifische Korrekturen:**

#### G-001: Bezeichnung "Viertel-Dosis" ungenau
Siehe systemischen Befund S-002.

#### G-002: target_ec_ms Diskrepanz
Siehe systemischen Befund S-001.

**Hinweis ohne Korrekturpflicht:** Gurken-HARVEST mit target_ec_ms 1.5 und berechnetem Giessloesung-EC 0.80 ist die groesste relative Diskrepanz aller Plaene (Verhaltnis 1:1.9). Bei fruchtenden Gurken sollte die Bewaesserungsfrequenz in Hitzephasen auf 2x taeglich erhoehen -- dies ist in den Hinweistexten implizit erwaehnt, koennte aber als watering_schedule_override in HARVEST expliziter werden. Kein Fehler, guter Verbesserungshinweis.

---

## Plan 3: Zucchini (Cucurbita pepo)

### Gesamtbewertung: AKZEPTIERT mit Korrekturen

**Staerken:**
- Phasen-Mapping korrekt und lueckenlos (2+2+4+4+8+2 = 22 Wochen)
- Handbestaeubungshinweise fachlich korrekt und praxisrelevant (besonders fuer Gewaechshaus/schlechte Insektensituation)
- Cucurbitacin-Warnung korrekt und vollstaendig -- einschliesslich Kreuzbestaeubungsrisiko mit Zierguerbis (kritisch: kann letal sein)
- pH 6.2 korrekt fuer Cucurbitaceae
- Kein PK 13-14 -- fachlich richtig, da Zucchini keine intensive Einzelfrucht-Bildung wie Gurke braucht

**NPK-Ratio-Bewertung:** Identisch zu Gurke -- produktbedingte Abweichungen, agrobiologisch akzeptabel.

**Spezifische Korrekturen:**

#### Z-001: target_ec_ms VEGETATIVE-Phase inkonsistent

**Schweregrad:** Mittel -- datenbankinterner Konsistenzfehler

**Befund:** Zucchini setzt `target_ec_ms` in der VEGETATIVE-Phase auf **1.8 mS/cm**, waehrend alle anderen fuenf Plaene fuer die VEGETATIVE-Phase **1.5 mS/cm** verwenden. Die tatsaechliche Giessloesung-EC ist identisch (Terra Grow 5 ml/L + Zubehoer = ca. 0.83 mS/cm bei Leitungswasser-Basis). Es gibt keinen agrobiologischen Grund fuer diesen Unterschied: Zucchini ist zwar ein Starkzehrer, aber nicht intensiver als Paprika oder Gurke in der Vegetationsphase.

**Nachweis:** VEGETATIVE-Dosierung identisch mit Paprika/Gurke: Terra Grow 5 ml/L, Sugar Royal 1 ml/L, Pure Zym 1 ml/L, Power Roots 0.5 ml/L.

**Korrekturvorschlag:** `target_ec_ms` in der VEGETATIVE-Phase von 1.8 auf **1.5 mS/cm** korrigieren (Konsistenz mit allen anderen Starkzehrer-Plaenen). Falls ein hoeherer Substrat-EC-Zielwert fuer Zucchini gewuenscht ist, muss dieser durch erhoehte Dosierung unterstuetzt werden (z.B. Terra Grow auf 5.5 ml/L), was aber die Produktempfehlung ueberschreiten wuerde.

#### Z-002: Bezeichnung "Viertel-Dosis" ungenau
Siehe systemischen Befund S-002.

#### Z-003: target_ec_ms systemisch
Siehe systemischen Befund S-001.

---

## Plan 4: Rosenkohl (Brassica oleracea var. gemmifera)

### Gesamtbewertung: AKZEPTIERT mit Korrekturen

**Staerken:**
- Kein FLOWERING-Phase -- fachlich korrekt. Rosenkohl-"Sprossenbildung" ist botanisch keine Bluetephase; die Pflanze wuerde bei Schosspflanzung keine Sprosskoepfe bilden. Das Weglassen der FLOWERING-Phase ist eine korrekte und elegante Modellierungsentscheidung.
- pH 6.5 konsequent -- unverzichtbar zur Kohlhernie-Praevention (Plasmodiophora brassicae). Dieser Wert ist in keinem anderen Plan so klar begruendet und priorisiert. Fachlich exemplarisch.
- N-Stopp ab Woche 20 (August) korrekt und gut begruendet: Umstellung auf K-betonte Ernaehrung foerdert Rosettenbildung und Frostharte der Sproesschen.
- Zwei Delivery-Channels innerhalb der langen VEGETATIVE-Phase (Wachstum W9-19 vs. Reife W20-22) zeigen gutes Verstaendnis der Kulturanforderungen.
- Phasen lueckenlos: 2+6+14+6+2 = 30 Wochen.
- Keine Toxizitaet fuer Katzen/Hunde -- korrekt.
- Frost verbessert Geschmack -- korrekt (Glucosinolat-Konversion zu Zucker bei Kaelte).

**Spezifische Korrekturen:**

#### R-001: Keimtemperatur weicht vom Steckbrief ab

**Schweregrad:** Niedrig -- minor Datendiskrepanz

**Befund:** Der Naehrstoffplan gibt fuer die GERMINATION-Phase eine Keimtemperatur von **15-20 degC** an. Der Referenz-Steckbrief `brassica_oleracea_var_gemmifera.md` nennt ein Optimum von **18-22 degC**.

**Fachliche Einordnung:** Beide Bereiche liegen im biologisch moeglichen Keimfenster fuer Brassica oleracea. Die untere Grenze 15 degC fuehrt zu deutlich laengerer Keimdauer (>14 Tage statt 5-7 Tage bei 20 degC). Fuer Fruehsaaten ab Maerz in beheiztem Indoor-Bereich sollte das Optimum von 18-22 degC angestrebt werden -- 15 degC ist zu kuehl fuer schnelle, gleichmaessige Keimung.

**Korrekturvorschlag:** Keimtemperatur auf **18-22 degC** korrigieren (konsistent mit Steckbrief). Optionaler Zusatz: "Unterhalb 15 degC stark verzoegerte Keimung; oberhalb 25 degC Schlechtkeimer."

#### R-002: target_ec_ms systemisch
Siehe systemischen Befund S-001.

---

## Plan 5: Sellerie / Knollensellerie (Apium graveolens var. rapaceum)

### Gesamtbewertung: AKZEPTIERT mit Korrekturen

**Staerken:**
- LICHTKEIMER-Hinweis prominent und korrekt platziert -- kritisch fuer Keimungserfolg. Ein Abdecken der Samen wuerde die Keimung vollstaendig verhindern.
- Vernalisationswarnung korrekt und agrobiologisch praezise: unter 10 degC fuer mehr als 10 Tage induziert Schosspflanzung (Bluetentrieb), was den Knollenansatz verhindert.
- Semantische Remappung FLOWERING -> Knollenbildung ist kreativer aber vertretbarer Kompromiss im bestehenden Phase-Enum. Die Erklaerung im Dokument ist klar.
- Bor-Bezug (Herzfaeule-Praevention) aus Terra Bloom korrekt -- Bor ist essenziell fuer Knollengemuese.
- Calcium-Tracking (Schwarzherz-Praevention) vorhanden -- fachlich korrekt.
- Sellerie-Allergie (Beifuss-Sellerie-Syndrom) korrekt erwahnt.
- Furanocumarin-Phototoxizitaet korrekt beachtet.
- Phasen lueckenlos: 3+7+8+10+2+2 = 32 Wochen.
- Laengster Plan (32 Wochen) korrekt begruendet -- Sellerie benoetigt 150-180 Tage Kulturzeit.

**Spezifische Korrekturen:**

#### Se-001: FLOWERING-Phase semantische Remappung sollte dokumentiert werden

**Schweregrad:** Niedrig -- systemische Konvention empfohlen

**Befund:** Die Remappung der Knollenbildungsphase auf das FLOWERING-Enum ist im vorliegenden Dokument gut erlaeutert. Sie stellt aber eine produktweite Konvention dar, die in der zentralen Phase-Dokumentation (REQ-003 / Phase-State-Machine) festgehalten werden sollte, damit andere Plan-Autoren dasselbe Muster konsistent anwenden koennen.

**Empfehlung:** In REQ-003 oder in einem Kommentar zur Phase-Enum-Definition erlaeutern: "FLOWERING kann bei nicht-bluetenden Produktionsphasen (z.B. Knollenbildung bei Sellerie, Sprossenreife bei Rosenkohl) als 'physiologische Reifephase vor der Ernte' interpretiert werden."

#### Se-002: target_ec_ms systemisch
Siehe systemischen Befund S-001.

**Hinweis ohne Korrekturpflicht:** Die SEEDLING-Phase von Sellerie (7 Wochen, Maerz-Ende April) ist die anspruchsvollste Phase: Lichtkeimer, Vernalisationsrisiko, sehr kleiner Samenling. Der Plan adressiert dies durch reduzierte Duengung (1.5 ml/L Terra Grow). Zusaetzlich waere ein Hinweis auf Pikieren (2x: bei 2. Blattpaar, dann Endgefaess) wertvoll. Kein Fehler, guter Ergaenzungsvorschlag.

---

## Plan 6: Lauch / Porrée (Allium porrum)

### Gesamtbewertung: AKZEPTIERT mit Korrekturen

**Staerken:**
- Kein FLOWERING-Phase -- korrekt. Bei Lauch waere Schosspflanzung (Bluetentrieb) ein Ernteverlust; die Phase ist explizit zu vermeiden.
- Kein FLUSHING-Phase -- korrekt und begruendet. Lauch verbleibt im Boden und wird bei Bedarf geerntet; eine dedizierte Spuelungsphase macht keinen Sinn.
- Zwei Delivery-Channels in VEGETATIVE (Wachstum W12-19 vs. Winterhaerte W20-26) fachlich korrekt und gut motiviert. K-betonte Ernaehrung ab August foerdert Zellwand-Stabilitaet und Frostharte.
- Allium-Toxizitaet fuer Katzen und Hunde korrekt, vollstaendig und prominent gewarnt (N-Propyl-Disulfid, haemolytische Anaemie). Alle Allium-Teile (Blatter, Stangen, Zwiebeln) korrekt als toxisch bezeichnet.
- HARVEST ohne Duengung korrekt -- Lauch im Freiland benoetigt keine Duengung waehrend der Winterernte.
- Taxonomischer Hinweis (Allium porrum syn. Allium ampeloprasum) fachlich korrekt.
- Phasen lueckenlos: 3+8+15+8 = 34 Wochen.
- Laengster Plan (34 Wochen) korrekt -- Lauch hat die laengste Kulturzeit aller sechs Arten.

**Spezifische Korrekturen:**

#### L-001: Beduengungsfrequenz SEEDLING: Textkonflik zwischen Hinweis und Datenfeld

**Schweregrad:** Mittel -- operationeller Fehler moeglich

**Befund:** Im SEEDLING-Delivery-Channel-Hinweis steht "Beduengung alle 2 Wochen (nicht bei jedem Giessen)". Das `watering_schedule_override`-Feld des SEEDLING-Delivery-Channels hat jedoch `interval_days: 2` (alle zwei Tage). Dies ist ein direkter Widerspruch:

- Texthinweis: Beduengung alle 14 Tage
- Datenfeld: Beduengungsintervall alle 2 Tage

**Fachliche Einordnung:** Fuer Lauch-Jungpflanzen im Pikierkasten ist "alle 2 Wochen duengen" agrobiologisch korrekt. In dieser fruehen Phase (Wochen 4-11, ca. Maerz-Mai) sind die Pflanzen noch sehr klein und salzstressempfindlich. Beduengung alle 2 Tage wuerde bei Leitungswasser-Basis und 0.53 mS/cm Giessloesung-EC zu Substrat-EC-Aufbau und Salzstress fuehren.

**Korrekturvorschlag:** `interval_days` im SEEDLING-watering_schedule_override auf **14** korrigieren (konsistent mit Texthinweis "alle 2 Wochen"). Alternativ, falls interval_days sich auf die Giessfrequenz (Wasser ohne Duenger) bezieht und die Duengungsfrequenz separat definiert werden soll, muss das Datenschema diese Trennung unterstuetzen.

#### L-002: Power Roots zeitliche Begrenzung innerhalb VEGETATIVE nicht durch KA-Datenmodell durchsetzbar

**Schweregrad:** Niedrig -- systemische Modellierungsgrenze

**Befund:** Power Roots ist im VEGETATIVE-Delivery-Channel (naehrloesung-wachstum, Wochen 12-19) mit einem `_comment`-Feld versehen: "Nur bis Woche 14". Das KA-Datenmodell kann Fertilizer-Eintraege innerhalb einer Phasen-Delivery-Channel-Definition nicht zeitlich begrenzen -- entweder wird ein Produkt waehrend der gesamten Phase angewendet oder gar nicht.

**Fachliche Einordnung:** Der Hinweis ist agrobiologisch sinnvoll: Power Roots stimuliert Wurzelwachstum und ist in der fruehen Etablierungsphase (Wochen 12-14 nach Auspflanzen) wichtiger als nach vollstaendiger Durchwurzelung. Nach Woche 14 ist die Dosierung nicht schaedlich, aber kostentechnisch ineffizient.

**Loesungsoptionen:**
1. **Zwei Teil-Delivery-Channels** innerhalb von naehrloesung-wachstum: W12-14 (mit Power Roots) und W15-19 (ohne Power Roots). Erfordert, dass das KA-Modell mehrere Delivery-Channels pro Phase-Entry mit Wochenbereich unterstuetzt.
2. **Kompromiss:** Power Roots in den gesamten W12-19 lassen und in einem Hinweistext erlaeutern. Kein agrobiologischer Schaden.
3. **Modellgrenze dokumentieren:** In der System-Dokumentation festhalten, dass zeitlich begrenzte Produkte innerhalb einer Phase nur ueber Sub-Phasen oder Hinweistexte modellierbar sind.

#### L-003: target_ec_ms systemisch
Siehe systemischen Befund S-001.

---

## Phasen-Luecken-Pruefung (Zusammenfassung)

| Plan | Wochensumme | Pruefformel | Ergebnis |
|------|------------|-------------|---------|
| Paprika | 30 | 3+6+7+6+6+2 | Lueckenlos |
| Gurke | 22 | 1+3+4+4+8+2 | Lueckenlos |
| Zucchini | 22 | 2+2+4+4+8+2 | Lueckenlos |
| Rosenkohl | 30 | 2+6+14+6+2 | Lueckenlos |
| Sellerie | 32 | 3+7+8+10+2+2 | Lueckenlos |
| Lauch | 34 | 3+8+15+8 | Lueckenlos |

Alle sechs Plaene sind lueckenlos. Keine fehlenden Wochensequenzen, keine Ueberlappungen.

---

## EC-Budget-Zusammenfassung

### Berechnete Giessloesung-EC (Basis Leitungswasser ~0.40 mS/cm)

| Phase | Hauptprodukt | ml/L | EC-Beitrag | Zusatzstoffe | EC-Zusatz | Basis-H2O | Gesamt-EC |
|-------|-------------|------|-----------|-------------|----------|----------|----------|
| SEEDLING | Terra Grow | 1.5 | 0.12 | Sugar Royal 0.5 ml + Pure Zym 0.5 ml | 0.01 | 0.40 | ~0.53 |
| VEGETATIVE | Terra Grow | 5.0 | 0.40 | SR 1 ml + PZ 1 ml + PR 0.5 ml | 0.025 | 0.40 | ~0.83 |
| FLOWERING | Terra Bloom | 4.5 | 0.45 | SR 1 ml + PZ 1 ml + PR 0.5 ml | 0.025 | 0.40 | ~0.88 |
| FLOWERING + PK | Terra Bloom 4.5 + PK 0.5 | -- | 0.45+0.125 | s.o. | 0.025 | 0.40 | ~1.00 |
| HARVEST | Terra Bloom | 4.0 | 0.40 | SR 1 ml + PZ 1 ml | 0.02 | 0.40 | ~0.82 |
| FLUSHING | -- | 0 | 0 | Pure Zym 1 ml | 0.00 | 0.40 | ~0.40 |

Abkuerzungen: SR = Sugar Royal (EC/ml 0.02), PZ = Pure Zym (EC/ml 0.00), PR = Power Roots (EC/ml 0.01), PK = PK 13-14 (EC/ml 0.25)

**Feststellung:** Die EC-Progression ist biologisch korrekt: SEEDLING (sanft) -> VEGETATIVE (voll) -> FLOWERING (leicht reduziert) -> HARVEST (reduziert) -> FLUSHING (kein Duenger). Das Schema entspricht dem anerkannten "Aufbau-Peak-Auslauf"-Profil fuer Starkzehrer.

---

## Toxizitaets-Matrix

| Art | Mensch | Katze | Hund | Nagetiere | Vorgehen |
|-----|--------|-------|------|----------|---------|
| Paprika (Capsicum annuum) | Unreife Fruechte: Solanin; Capsaicin: Schleimhautreizung | Toxisch (Solanin + Capsaicin) | Toxisch (Solanin + Capsaicin) | Toxisch | Korrekt im Plan |
| Gurke (Cucumis sativus) | Cucurbitacin bei Bitterness (selten) | Nicht toxisch | Nicht toxisch | Nicht toxisch | Korrekt im Plan |
| Zucchini (Cucurbita pepo) | Cucurbitacin bei bitterem Geschmack (Kreuzbestaeuber-Risiko) | Nicht toxisch (modern) | Nicht toxisch (modern) | Nicht toxisch | Korrekt im Plan |
| Rosenkohl (Brassica oleracea) | Keine relevante Toxizitaet | Nicht toxisch | Nicht toxisch | Nicht toxisch | Korrekt im Plan |
| Sellerie (Apium graveolens) | Sellerie-Allergie (Beifuss-Sellerie-Syndrom, Kreuzallergie); Furanocumarine | Nicht signifikant | Nicht signifikant | Nicht signifikant | Korrekt im Plan |
| Lauch (Allium porrum) | Keine wesentliche Toxizitaet in Nahrungsmenge | Alle Pflanzenteile toxisch (N-Propyl-Disulfid, haemolyt. Anaemie) | Alle Pflanzenteile toxisch (s.o.) | Toxisch | Korrekt im Plan |

Alle sechs Plaene enthalten die relevanten Toxizitaets- und Sicherheitshinweise vollstaendig und korrekt.

---

## Saisonalitaets-Pruefung (Mitteleuropa)

| Art | Aussaat Indoor | Auspflanzen | Ernte | Gesamtdauer | Beurteilung |
|-----|---------------|-------------|-------|------------|-------------|
| Paprika | Mitte Feb | Nach Eisheiligen (ca. 15. Mai) | Jul-Sep | 30 Wochen | Korrekt |
| Gurke | Mitte Apr | Mai (frostfrei) | Jul-Sep | 22 Wochen | Korrekt |
| Zucchini | Mitte Apr | Mai (frostfrei) | Jun-Sep | 22 Wochen | Korrekt |
| Rosenkohl | Maerz | Mai | Okt-Nov (bis Frost) | 30 Wochen | Korrekt |
| Sellerie | Mitte Feb | Mai (nach Abharten) | Sep-Okt | 32 Wochen | Korrekt |
| Lauch | Feb | Apr-Mai | Nov-Maerz | 34 Wochen | Korrekt |

Alle Saisonplaene sind realistisch fuer Mitteleuropa (USDA Zone 6-7, D/A/CH Tieflagen). Die Eisheiligen-Referenz (um den 15. Mai) ist als Freiland-Grenztermin korrekt und in der Praxis bewaehrt.

---

## Priorisierte Korrekturen-Liste

| ID | Plan | Schweregrad | Korrekturaktion |
|----|------|-------------|----------------|
| S-001 | Alle 6 Plaene | Mittel | target_ec_ms-Feldsemantik klaeren: Substrat-EC vs. Giessloesung-EC trennen |
| S-002 | Paprika, Gurke, Zucchini, Rosenkohl | Niedrig | Bezeichnung "Viertel-Dosis" auf "Starterdosis 1.5 ml/L" aendern oder auf 1.25 ml/L anpassen |
| Z-001 | Zucchini | Mittel | target_ec_ms VEGETATIVE von 1.8 auf 1.5 korrigieren (Konsistenz) |
| R-001 | Rosenkohl | Niedrig | Keimtemperatur von 15-20 degC auf 18-22 degC korrigieren (Steckbrief-konsistent) |
| L-001 | Lauch | Mittel | interval_days SEEDLING-Override von 2 auf 14 korrigieren (Konfliktosung Hinweis vs. Datenwert) |
| L-002 | Lauch | Niedrig | Power Roots Zeitbegrenzung als Systemgrenze dokumentieren; ggf. Sub-Delivery-Channel-Modell pruefen |

---

## Empfehlungen fuer kuenftige Plan-Erstellung

1. **EC-Budget-Rechner** als Hilfsmittel: Fuer jeden Delivery-Channel sollte eine automatische Berechnung der Giessloesung-EC aus den Dosiermengen und EC/ml-Werten der Einzelprodukte erzeugt werden. Dies wuerde Diskrepanzen zwischen berechneter EC und `target_ec_ms` sofort sichtbar machen.

2. **Phase-Override-Granularitaet:** Das aktuelle Datenmodell unterstuetzt `watering_schedule_override` pro Phase-Entry. Fuer die Modellierung zeitlich unterschiedlicher Duengungsstrategien innerhalb einer langen Phase (z.B. N-Stopp bei Rosenkohl, K-Umstellung bei Lauch) sind mehrere Delivery-Channels pro Phase die bevorzugte Loesung -- dies funktioniert bereits korrekt in Rosenkohl und Lauch.

3. **Produkt-Zeitlimitierung innerhalb einer Phase:** Das aktuelle Modell kann keine "Produkt nur bis Woche X" Regeln innerhalb eines Delivery-Channels erzwingen. Loesungen: (a) Phase in Sub-Phasen splitten, (b) Hinweistexte mit Zeitangabe, (c) Modellierung als separater, zeitlich begrenzter Delivery-Channel wenn das System Wochenbereich pro Channel unterstuetzt.

4. **Steckbrief-Plan-Konsistenz:** Keimtemperatur, EC-Zielwerte und NPK-Anforderungen sollten direkt aus dem Steckbrief-Dokument der jeweiligen Art abgeleitet werden, um Diskrepanzen wie bei Rosenkohl (Keimtemperatur) zu vermeiden. Ein automatisierter Abgleich Steckbrief <-> Plan waere wertvoll.

5. **Organisches Duengungssystem-Kompatibilitaet:** Alle sechs Plaene verwenden Plagron-Terra-Mineralduenger. Fuer biologischen Anbau (REQ-004 organische Freiland-Duengung) waere eine parallele Plan-Serie mit organischen Produkten (Hornspane, Kompost, Tomatendunger auf Guanobasis) fachlich sinnvoll -- besonders fuer Outdoor-Anbau.
