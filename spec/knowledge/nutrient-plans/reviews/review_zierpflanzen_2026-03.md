# Fachliches Review: Zierpflanzen-Naehrstoffplaene -- Dahlie, Petunie, Tigerblume

**Reviewer:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-06
**Pruefgegenstand:**
- `spec/ref/nutrient-plans/dahlie_plagron_terra.md` v1.0
- `spec/ref/nutrient-plans/petunie_plagron_terra.md` v1.0
- `spec/ref/nutrient-plans/tigerblume_plagron_terra.md` v1.0

**Quell-Dokumente:**
- `spec/ref/plant-info/dahlia_x_hybrida_armateras.md`
- `spec/ref/plant-info/petunia_x_hybrida.md`
- `spec/ref/plant-info/tigridia_pavonia.md`
- `spec/ref/products/plagron_terra_grow.md`
- `spec/ref/products/plagron_terra_bloom.md`
- `spec/ref/products/plagron_pk_13_14.md`
- `spec/ref/products/plagron_pure_zym.md`
- `spec/ref/products/plagron_sugar_royal.md`

**EC-Faktoren (gemaess Pruefauftrag):**
Terra Grow 0.08, Terra Bloom 0.10, Power Roots 0.01, Pure Zym 0.00, Sugar Royal 0.02, PK 13-14 0.25 mS/cm pro ml/L

---

## Gesamtbewertung

| Dimension | Dahlie | Petunie | Tigerblume | Kommentar |
|-----------|--------|---------|------------|-----------|
| Biologische Korrektheit | 4 / 5 | 4 / 5 | 5 / 5 | Tigerblume fachlich am praezisesten |
| NPK-Stimmigkeit zum Steckbrief | 3 / 5 | 4 / 5 | 4 / 5 | Dahlie FLOWERING-NPK abweichend; alle Plaene korrekt P/K-betont in Bluete |
| EC-Budget-Konsistenz | 2 / 5 | 2 / 5 | 4 / 5 | Systemischer target_ec_ms-Fehler bei Dahlie und Petunie |
| Knollen-Zyklus-Korrektheit | 5 / 5 | -- | 5 / 5 | Vorkeimen, Dormanz-Temps, cycle_restart korrekt |
| DORMANCY-Temperaturen | 5 / 5 | 4 / 5 | 5 / 5 | Dahlie 4-8 degC, Tigerblume 10-13 degC korrekt differenziert |
| cycle_restart Korrektheit | 5 / 5 | 5 / 5 | 5 / 5 | Alle drei korrekt (perennierend = 1, annuell = null) |
| Lueckenlos-Pruefung | 5 / 5 | 5 / 5 | 5 / 5 | Alle drei Zyklen lueckenlos 52 / 40 / 52 Wochen |
| Tabellen-JSON-Konsistenz | 4 / 5 | 3 / 5 | 4 / 5 | Petunie: NPK-Inkonsistenz VEGETATIVE Tabelle vs. JSON |

**Gesamteinschaetzung:** Alle drei Plaene sind fachlich grundsaetzlich korrekt konzipiert und zeigen ein tiefes Verstaendnis der artspezifischen Beduerfnisse. Der groesste systemische Fehler ist eine Diskrepanz zwischen den deklarierten `target_ec_ms`-Werten in den Delivery-Channel-Daten und den tatsaechlich erreichbaren EC-Werten laut EC-Budget-Kalkulation -- betroffen sind alle aktiven Phasen von Dahlie und Petunie, sowie marginal die Tigerblume. Dieser Fehler ist importkritisch, da das System die `target_ec_ms`-Werte als Soll-Werte interpretiert. Der Knollen-Zyklus ist bei Dahlie und Tigerblume vorbildlich modelliert; die Temperaturdifferenzierung (Dahlie 4-8 degC, Tigerblume 10-13 degC) ist korrekt und fachlich wichtig.

---

## 1. DAHLIE -- Plagron Terra + PK 13-14

### 1.1 NPK-Stimmigkeit

**Pruefpunkt: Passen die Duengerprodukte zum arttypischen Naehrstoffbedarf?**

**Befund: UEBERWIEGEND BESTANDEN -- eine fachliche Praezisierung noetig**

| Phase | NPK Steckbrief (Idealwert) | NPK Naehrstoffplan | Produkt | Bewertung |
|-------|---------------------------|-------------------|---------|-----------|
| GERMINATION | 0:0:0 | 0:0:0 | kein Duenger | Korrekt |
| VEGETATIVE | 1:1:1 bis 2:1:1 | 3:1:3 | Terra Grow | Abweichung -- siehe U-001 |
| FLOWERING | 1:3:3 bis 0:2:3 | 2:2:4 | Terra Bloom | Abweichung -- siehe U-002 |
| HARVEST | 0:0:0 | 0:0:0 | kein Duenger | Korrekt |
| DORMANCY | 0:0:0 | 0:0:0 | kein Duenger | Korrekt |

**U-001 -- Vegetatives NPK:**
Der Steckbrief empfiehlt NPK 1:1:1 bis 2:1:1 fuer die vegetative Phase. Terra Grow liefert NPK 3-1-3, also ein N:K-Verhaeltnis von 1:1, aber mit hoeherem Absolutgehalt beider Makronaehrstoffe als in den Steckbrief-Richtwerten. Fuer Dahlien ist das vertretbar, da Dahlien als Starkzehrer ein hohes Naehrstoffangebot tolerieren. Der Plan adressiert das im Naehrstoffprofil-Hinweis ("K fuer Staengelstaerke"). Ergaenzend sollte erwaehnt werden, dass das N-Niveau von Terra Grow (3-1-3) im Vergleich zum Steckbrief-Idealwert an der oberen Grenze liegt -- bei N-sensiblen Kultivaren (Embassy, kleinwuechsig) koennte eine Dosisreduzierung auf 4 ml/L sinnvoll sein.

**U-002 -- Bluete-NPK:**
Das ist der fachlich bedeutsamste Befund dieses Plans. Der Steckbrief (Abschnitt 2.3) empfiehlt fuer die Bluete explizit NPK 1:3:3 bis 0:2:3 -- deutlich P/K-betont und nahezu stickstofffrei. Terra Bloom liefert NPK 2-2-4, was einem moderaten N-Gehalt entspricht. Der Plan erkennt dies korrekt und benennt es an mehreren Stellen ("Terra Bloom liefert 2:2:4, was etwas mehr N enthaelt als ideal"). Die Entscheidung, kein Sugar Royal (9-0-0) zu verwenden, ist biologisch korrekt und ausdruecklich begruendet.

Fachliche Einschaetzung: Bei der Dosierung 5 ml/L Terra Bloom und ausreichend K-Versorgung (K2O 3.9%) ist die Bluetefoerderung gegeben. Das NPK-Verhaeltnis Terra Bloom ist fuer eine reine Zierpflanze-Formulation nicht ideal, aber bei Dahlien ist dieses Kompromiss im Plagron-Terra-Sortiment unvermeidlich. Der Plan handhert es korrekt.

**Wochentiming PK 13-14:**
Woche 15-16 der Bluetephase entspricht ca. 3 Wochen nach Beginn von FLOWERING (Sequenzwoche 13). Das Produktdatenblatt empfiehlt Woche 3-4 der Bluete fuer den PK-Boost ("maximale Zellteilung in Blueten"). Der Timing-Einsatz stimmt also mit der Cannabis-orientierten Herstellerempfehlung ueberein und ist auf Dahlien (peak Knospenansatz Juli) biologisch korrekt uebertragen.

Dosierung: 0.75 ml/L statt der Herstellerstandard-Dosis 1.5 ml/L -- korrekte Halbierung fuer Zierpflanze (niedrigere EC-Toleranz als Cannabis). Der Plan begruendet dies explizit.

---

### 1.2 EC-Budget -- Kritischer Befund

**Pruefpunkt: Stimmen target_ec_ms-Werte mit der tatsaechlichen Dosierungskalkulation ueberein?**

**Befund: FEHLERHAFT -- Korrekturbedarf vor Import**

Die `target_ec_ms`-Werte in den Delivery-Channel-Daten weichen systematisch von den berechneten EC-Werten ab. Das Feld `target_ec_ms` repraesentiert im Kamerplanter-System den tatsaechlich angestrebten Messwert der fertigen Giessloesung -- nicht das Steckbrief-Optimum.

**Rechenweg (Basisannahme: Leitungswasser 0.4 mS/cm):**

| Phase | EC-Kalkulation | Kalkulation-Ergebnis | Deklarierter target_ec_ms | Differenz |
|-------|---------------|---------------------|--------------------------|-----------|
| VEGETATIVE | TG 5.0 x 0.08 + PR 1.0 x 0.01 + PZ 0.00 + 0.40 Wasser | 0.40 + 0.01 + 0.40 = **0.81 mS/cm** | 1.2 | +0.39 |
| FLOWERING (ohne PK) | TB 5.0 x 0.10 + PZ 0.00 + 0.40 Wasser | 0.50 + 0.40 = **0.90 mS/cm** | 1.4 | +0.50 |
| FLOWERING (mit PK W15-16) | TB 5.0 x 0.10 + PK 0.75 x 0.25 + 0.40 Wasser | 0.50 + 0.19 + 0.40 = **1.09 mS/cm** | 1.4 | +0.31 |
| FLOWERING (reduziert W23-26) | TB 3.0 x 0.10 + 0.40 Wasser | 0.30 + 0.40 = **0.70 mS/cm** | 1.4 | +0.70 |

**Einordnung:** Die EC-Budget-Kommentare im Plan (0.81, 0.90, 1.09, 0.70) sind rechnerisch korrekt. Die `target_ec_ms`-Werte (1.2 und 1.4) entsprechen dem optimalen EC-Bereich aus dem Steckbrief (0.8-1.4 mS/cm) -- wurden also als Steckbrief-Richtwerte und nicht als tatsaechliche Dosierungsergebnisse eingetragen.

**Konsequenz:** Ein Giesssystem, das auf Basis von `target_ec_ms: 1.4` befuellt wird, wuerde die Duengerdosen verdoppeln, bis der EC-Wert 1.4 erreicht ist -- das waere eine massive Ueberdosierung. Fuer manuelle Nutzung (Giesskanne) wird `target_ec_ms` als Kontrollwert verstanden, nicht als automatischer Regelwert, was das Problem abschwaecht. Dennoch ist die Inkonsistenz zwischen tatsaechlicher Dosierung und deklariertem Zielwert zu korrigieren.

**Empfehlung F-001:** `target_ec_ms`-Werte an berechnete EC-Budgets anpassen:
- VEGETATIVE: `target_ec_ms: 0.8` (abgerundet fuer hartes Wasser; Budget 0.81)
- FLOWERING (Standard): `target_ec_ms: 0.9`
- FLOWERING (mit PK W15-16): als `optional`-Flag-Kommentar "~1.1 in PK-Woche" dokumentieren
- FLOWERING (reduziert W23-26): als Hinweis in `notes` dokumentieren, nicht als eigener Channel

---

### 1.3 Knollen-Zyklus und DORMANCY-Temperatur

**Befund: BESTANDEN -- vorbildlich dokumentiert**

**Temperatur 4-8 degC:**
Der Steckbrief (Abschnitt 4.3, Ueberwinderung) gibt exakt `winter_quarter_temp_min: 4` und `winter_quarter_temp_max: 10` degC an. Der Naehrstoffplan nennt 4-8 degC -- liegt vollstaendig im Steckbrief-Korridor und entspricht dem Praxisstandard (American Dahlia Society, RHS, Floret Flowers: 4-8 degC). Korrekt.

**Biologische Begruendung:** Dahlia-Knollen sind Inulinspeicher (Fructose-Polysaccharid). Temperaturen unter 4 degC koennten Eiskristallbildung in weniger geschuetzten Knollenteilen ausloesen; ueber 10 degC stimuliert Ethylen das Austreiben. Der Bereich 4-8 degC ist das optimale Lagerfenster. Die Empfehlung "dunkel" ist korrekt -- Licht foerdert vorzeitiges Austreiben auch bei kuehler Temperatur.

**Lagermedium:** Der Plan nennt "leicht feuchtes Vermiculite, Kokoserde oder Zeitungspapier". Der Steckbrief empfiehlt dasselbe ("Vermiculite, Torf oder Kokoserde") und warnt vor feuchtem Saegemehl (Faeulnis). Diese Differenzierung fehlt im Naehrstoffplan -- ein Hinweis "Saegemehl nicht empfohlen (Faeulnisrisiko)" waere sinnvoll, aber nicht importkritisch.

**cycle_restart_from_sequence: 1:**
Korrekt. Der Zyklus startet nach DORMANCY neu bei Sequenz 1 (GERMINATION = Vorkeimen). Die Knolle ist das Ueberdauerungsorgan, die Vorkeimphase (GERMINATION) entpricht biologisch korrekt dem Aufwecken der Knollenreserven. Die Verwendung von GERMINATION fuer "Knollenaustreibung" ist eine zulassige semantische Erweiterung des Enums -- im Plan klar erklaert.

**is_recurring: true fuer DORMANCY:**
Korrekt. Die Dormanzphase wiederholt sich jaehrlich. Die Kombination `is_recurring: true` auf der letzten Sequenzphase + `cycle_restart_from_sequence: 1` bildet den perennierenden Knollenzyklus korrekt ab.

**Lueckenlos-Pruefung:**
Plan-Aussage: 4 + 8 + 14 + 4 + 22 = 52 Wochen.
Kontrollrechnung:
- GERMINATION: W1-4 = 4 Wochen
- VEGETATIVE: W5-12 = 8 Wochen
- FLOWERING: W13-26 = 14 Wochen
- HARVEST: W27-30 = 4 Wochen
- DORMANCY: W31-52 = 22 Wochen
- Summe: 52 Wochen -- lueckenlos. Korrekt.

---

### 1.4 Weitere Befunde Dahlie

**Bewertung des HARVEST-Phasen-Einsatzes:**
HARVEST wird doppelt verwendet: (a) fuer laufende Schnittblumenernte waehrend FLOWERING und (b) fuer die eigentliche Knollenernte am Saisonende. Dies ist eine modellierungsbedingte Pragmatik, da KA kein separates "senescence"-Enum hat. Die Klarstellung im Notes-Text ist ausreichend.

**Giessplan-Override DORMANCY (interval_days: 0, times_per_day: 0):**
Technisch korrekte Darstellung von "kein Giessen" in der DORMANCY-Phase. Ob interval_days: 0 im System als "deaktiviert" interpretiert wird, sollte vom Entwicklerteam geprueft werden -- ein alternatives Modell waere `enabled: false` auf dem gesamten Delivery-Channel. Kein fachlicher Fehler.

**Entspitzen-Hinweis (Pinching):**
Korrekt erwaehnt (30-40 cm, ueber 3. Blattpaar). Stimmt mit Steckbrief und Floret-Flowers-Quelle ueberein. Bei allen 5 Cultivaren empfohlen -- biologisch korrekt.

---

## 2. PETUNIE -- Plagron Terra

### 2.1 Dauer-Bluete-Konzept mit P/K-Betonung

**Pruefpunkt: Ist das Dauerblueter-Konzept (Mai-Okt) mit P+K-Betonung biologisch sinnvoll?**

**Befund: BESTANDEN -- biologisch korrekt und gut begruendet**

Petunia x hybrida ist tagneutral (day_neutral, Steckbrief 1.1) und benoetigt keine photoperiodische Induktion fuer die Bluetenbildung. Die Dauerbluete von Mai bis Oktober entspricht dem Steckbrief (bloom_months: 5,6,7,8,9,10). Das Konzept der durchgehenden Terra-Bloom-Duengung ab Mitte Mai ist daher korrekt.

**P/K-Betonung waehrend FLOWERING:**
Der Steckbrief (Abschnitt 2.3) empfiehlt fuer die Bluetephase NPK 1:2:3, EC 1.2-2.0 mS/cm. Terra Bloom liefert NPK 2-2-4 (entspricht ca. 1:1:2 in relativer Betrachtung), was etwas N-haltiger ist als das Idealverhaeltnis. Kombiniert mit Sugar Royal (9-0-0) ergibt sich ein hoeherer N-Anteil in der Mischung. Dies ist bei Petunien als heavy_feeder mit Dauerwachstum biologisch vertretbar, da Petunien durch kontinuierliches Neutriebwachstum einen hoeheren N-Bedarf als echte Ruheblueher aufweisen.

**Sugar Royal in der Bluetephase:**
Sugar Royal (9-0-0) liefert organische Aminosaeuren und N. Bei 1.0 ml/L betraegt der EC-Beitrag 0.02 mS/cm (vernachlaessigbar). Der Plan begruendet den Einsatz mit "Aminosaeuren, Chlorophyll-Stimulation". Der Steckbrief nennt keine explizite Einschraenkung von Sugar Royal fuer Petunien. Biologisch vertretbar -- Petunien profitieren als Dauerblueher von Aminosaeure-Zufuhr fuer Chlorophyllstoffwechsel. Im Gegensatz zu Dahlien, wo Sugar Royal die N-Ueberlast verstaerken wuerde, ist bei Petunien der zusaetzliche N-Input durch das kontinuierliche Wachstum gerechtfertigt.

**Mitte-Sommer-Rueckschnitt (Juli):**
Der Plan modelliert den Rueckschnitt korrekt als einmalige Terra-Grow-Gabe (3 ml/L) fuer den Neuaustrieb, danach Rueckkehr zu Terra Bloom. Dies entspricht dem Steckbrief-Hinweis (Abschnitt 1.5: summer_pruning, Monate 6,7,8) und der Praxisempfehlung. Biologisch korrekt: N-Impuls nach Rueckschnitt foerdert schnellen Neutrieb, dann K-Betonung fuer zweite Bluetenwelle.

---

### 2.2 EC-Budget -- Kritischer Befund

**Befund: FEHLERHAFT -- Korrekturbedarf vor Import**

**Rechenweg (Basisannahme: Leitungswasser 0.4 mS/cm):**

| Phase | EC-Kalkulation | Kalkulation-Ergebnis | Deklarierter target_ec_ms | Differenz |
|-------|---------------|---------------------|--------------------------|-----------|
| SEEDLING | TG 2.5 x 0.08 + 0.40 Wasser | 0.20 + 0.40 = **0.60 mS/cm** | 0.8 | +0.20 |
| VEGETATIVE | TG 5.0 x 0.08 + PZ 0.00 + SR 1.0 x 0.02 + 0.40 Wasser | 0.40 + 0.02 + 0.40 = **0.82 mS/cm** | 1.2 | +0.38 |
| FLOWERING | TB 5.0 x 0.10 + PZ 0.00 + SR 1.0 x 0.02 + 0.40 Wasser | 0.50 + 0.02 + 0.40 = **0.92 mS/cm** | 1.6 | +0.68 |

**Einordnung:** Die berechneten EC-Werte (0.60, 0.82, 0.92) sind agronomisch plausibel und werden im Plan selbst korrekt ausgewiesen. Die `target_ec_ms`-Werte wurden wie bei der Dahlie aus dem Steckbrief-Optimumbereich entnommen (Steckbrief Abschnitt 2.3: Saemling 0.4-0.8, Vegetativ 0.8-1.4, Bluete 1.2-2.0). Die Diskrepanz in FLOWERING betraegt 0.68 mS/cm -- die groesste aller drei Plaene.

Der Steckbrief-Bereich fuer die Bluetephase (1.2-2.0 mS/cm) ist fuer einen Starkzehrer korrekt. Um diesen EC-Bereich tatsaechlich zu erreichen, wuerde man bei Leitungswasser 0.4 mS/cm eine Dosierung von ca. 8-16 ml/L Terra Bloom benoetigen -- deutlich ueber der 5 ml/L-Dosierung im Plan. Fuer Petunien im Freiland/Kuebel ist das tatsaechliche EC-Niveau von 0.92 mS/cm agronomisch vertretbar; der plan-eigene Hinweis ("bei wuechsigen Sorten und weichem Wasser kann auf 6 ml/L gesteigert werden") ist sinnvoll. Der target_ec_ms muss jedoch auf den tatsaechlichen EC-Wert gesetzt werden.

**Empfehlung F-002:** `target_ec_ms`-Werte an berechnete EC-Budgets anpassen:
- SEEDLING: `target_ec_ms: 0.6`
- VEGETATIVE: `target_ec_ms: 0.8`
- FLOWERING: `target_ec_ms: 0.9` (mit Hinweis in notes: "bei 6 ml/L TB ca. 1.0 mS/cm erreichbar")

---

### 2.3 DORMANCY-Mapping fuer Annuelle

**Befund: AKZEPTABEL -- analoges Problem wie Stiefmuetterchen-Review**

Petunia x hybrida ist in Mitteleuropa eine annuelle Zierpflanze (cycle_type: annual, Steckbrief 1.1). Der "DORMANCY"-Eintrag im Plan bildet die Seneszenz-Phase ab (nach erstem Frost), nicht eine echte physiologische Ruhephase. Der Plan setzt korrekt:
- `is_recurring: false` -- die Pflanze stirbt, keine echte Wiederholung
- `cycle_restart_from_sequence: null` -- annuell, kein Neustart
- Notes-Text macht klar: "Seneszenz nach erstem Frost. Keine Duengung. Pflanze entfernen."

Dies ist ein modellierungsbedingter Kompromiss (kein SENESCENCE-Enum im KA-System). Bei korrekten Metadaten ist das Mapping akzeptabel. Ein Kommentar "Mapping-Kompromiss: DORMANCY wird als Seneszenz-Proxy verwendet; biologisch kein echter Ruhezustand" waere empfehlenswert.

**DORMANCY-Giessplan-Override:** interval_days: 5 -- die Pflanze ist zu diesem Zeitpunkt bereits sterbend oder tot. Das Override sorgt fuer minimales Giessen "nur bei Trockenheit". Biologisch sinnlos, aber als Sicherheitsnetz fuer die wenigen Tage zwischen erstem Frost und Entsorgung vertretbar.

---

### 2.4 Inkonsistenz NPK-Verhaeltnis VEGETATIVE

**Befund: INKONSISTENZ -- Tabelle vs. JSON**

| Ort | npk_ratio Wert |
|-----|---------------|
| Abschnitt 4.3 Tabelle | (2, 1, 2) -- `NPK-Verhaeltnis: (2, 1, 2)` |
| JSON VEGETATIVE `npk_ratio` | [2.0, 1.0, 2.0] |

Die npk_ratio (2:1:2) entspricht nicht dem eingesetzten Produkt Terra Grow (3-1-3). Der Steckbrief empfiehlt fuer Vegetativ NPK 2:1:2 (Abschnitt 2.3), was als Steckbrief-Zielwert korrekt ist, aber Terra Grow liefert 3-1-3. Das deklarierte npk_ratio [2.0, 1.0, 2.0] ist somit der Steckbrief-Idealwert, nicht das tatsaechliche Produktverhaeltnis.

**Einordnung:** Im KA-Datenmodell repraesentiert `npk_ratio` in `NutrientPlanPhaseEntry` vermutlich das Ziel-NPK-Profil der Phase, nicht die exakte Produktanalyse. In diesem Sinne ist das Vorgehen (Steckbrief-Idealwert als npk_ratio) konsistent mit dem Ansatz in den anderen Phasen. Allerdings ist die Diskrepanz zwischen erklaetem npk_ratio und tatsaechlichem Produktverhaeltnis dokumentationsbeduerftig, da ein automatisierter Vergleich (Ist-Duenger vs. Soll-Profil) zu einer faelschlichen Abweichungsmeldung fuehren koennte.

Analoges gilt fuer die SEEDLING-Phase: npk_ratio [3.0, 1.0, 3.0] stimmt mit Terra Grow 3-1-3 ueberein.

**Empfehlung P-001:** Einheitliche Konvention festlegen: Entweder repraesentiert npk_ratio immer das Steckbrief-Ideal (wie in VEGETATIVE) oder immer das Produktverhaeltnis (wie in SEEDLING). Im aktuellen Plan ist die Konvention gemischt.

---

### 2.5 Eisenchloros-Management

**Befund: BESTANDEN -- kritischer Faktor gut abgedeckt**

Der Steckbrief identifiziert Eisenmangel-Chlorose als "haeufigsten Naehrstoffmangel" bei Petunien (Abschnitt 2.3). Der Plan greift das an mehreren Stellen auf:
- pH-Zielwert 5.8 (unter dem kritischen Schwellenwert 6.2 fuer Fe-Loeslichkeit)
- Hinweis auf Eisenchelat-Ergaenzung (Fe-EDTA, 0.5-1 g/10 L) bei Chlorose
- Terra Bloom enthaelt 0.21% Fe -- Plan erwaehnt korrekt, dass dies bei pH > 6.2 nicht ausreicht

Biologisch korrekt: Eisen ist in der Bodenmatrix bei pH > 6.2 als schwer loesliches Fe(OH)3 gebunden. Terra Blooms Fe-Gehalt ist nur bei pH < 6.2 bioverfuegbar. Der Hinweis auf aktive pH-Absenkung bei kalkreichem Wasser (> 14 degdH) ist fachlich richtig und praxisrelevant.

---

## 3. TIGERBLUME -- Plagron Terra

### 3.1 DORMANCY-Temperatur 10-13 degC -- Differenzierung zu Dahlien

**Befund: BESTANDEN -- korrekt und mehrfach prominent dokumentiert**

Dies ist der fachlich wichtigste Differenzierungspunkt zwischen den zwei Knollengewaechsen im Review.

**Biologische Begruendung:**
Tigridia pavonia stammt aus Kiefer-Eichenwald-Zonen Mexikos auf 2000-3000 m Hoehe (Steckbrief 1.1: "Mexiko, Guatemala, Kolumbien; Kiefer- und Eichenwald-Zonen auf 2000-3000 m"). Das Ursprungsklima ist warm-temperiert mit trockenen Wintern, aber ohne intensive Froestperioden. Die Knollen (botanisch korrekt: Kormen) sind deshalb kaelteempfindlicher als Dahlia-Knollen.

Die Literatur (Pacific Bulb Society, Gardening Know How, Gardenmarkt.de) ist einheitlich: Tigridia-Kormen bei 10-13 degC lagern. Tiefere Temperaturen (unter 8-10 degC) fuehren zu Zellschaeden durch Kaeltedenaturierung der Membranproteine. Der Steckbrief bestaetigt exakt: `winter_quarter_temp_min: 10`, `winter_quarter_temp_max: 13` degC.

**Dokumentation im Plan:**
- Phasen-Mapping Abschnitt 2, DORMANCY-Zeile: "10-13 degC lagern"
- Abschnitt 4.5 DORMANCY-Hinweise: "Knollen frostfrei lagern bei 10-13 degC (NICHT 4-8 degC wie Dahlien!)"
- Abschnitt 6 Praxis-Hinweise: nochmalige Betonung
- JSON DORMANCY notes: "NICHT 4-8 degC wie Dahlien!"

Die Differenzierung ist prominenter als bei anderen Plans und ist biologisch essentiell. Bei gemeinsamer Lagerung von Dahlien und Tigerblumen (was in der Praxis haeufig vorkommt) wuerde der Dahlien-Temperaturbereich (4-8 degC) die Tigridia-Kormen nachhaltig schaedigen.

**Vorzeitiges Austreiben bei > 15 degC:**
Plan erwaehnt: "Vorzeitiges Austreiben -- bei > 15 degC moeglich, Lagertemperatur pruefen." Korrekt. Tigridia treibt frueher aus als Dahlien; der engere Temperaturkorridor (10-13 degC) muss aktiv eingehalten werden.

---

### 3.2 NPK-Stimmigkeit Tigerblume

**Befund: BESTANDEN -- angemessene Dosierungsreduktion korrekt durchgefuehrt**

| Phase | NPK Steckbrief (Idealwert) | NPK Naehrstoffplan | Dosierung | Bewertung |
|-------|---------------------------|-------------------|-----------|-----------|
| GERMINATION | 0:0:0 | 0:0:0 | kein Duenger | Korrekt |
| VEGETATIVE | 2:1:1 | 3:1:3 | TG 2.0 ml/L (untere Dosis) | Akzeptabel -- niedrige Dosis kompensiert das Verhaeltnis |
| FLOWERING | 0:2:2 bis 1:2:2 | 2:2:4 | TB 2.5 ml/L (niedrige Dosis) | Vertretbar -- Steckbrief-Idealwert waere P/K-betonter |
| HARVEST | 0:0:0 | 0:0:0 | kein Duenger | Korrekt |
| DORMANCY | 0:0:0 | 0:0:0 | kein Duenger | Korrekt |

**Vegetatives Wachstum:**
Der Steckbrief empfiehlt NPK 2:1:1 (N-leicht-betont) fuer Vegetativ. Terra Grow (3-1-3) hat ein hoeheres K als ideal, aber das wird durch die niedrige Dosierung (2.0 ml/L, weniger als halbe Herstellerdosis) kompensiert. Der absolute N-Eintrag ist damit moderat. Fuer einen Schwachzehrer ist diese Dosierungsreduktion korrekt und notwendig.

**Bluetephase:**
Der Steckbrief empfiehlt 0:2:2 bis 1:2:2 -- deutlich P/K-betont, N minimal bis null. Terra Bloom (2-2-4) bei 2.5 ml/L enthaelt noch etwas N. Der Plan erkennt dies explizit: "Terra Bloom liefert 2:2:4, was etwas mehr N enthaelt als ideal, aber bei niedriger Dosis tolerierbar." Das ist eine korrekte Einschaetzung -- bei 2.5 ml/L ist der absolute N-Eintrag gering. Im Vergleich zu vollstaendiger N-Abwesenheit ist dies eine vertretbare Praxis-Loesung, da im Plagron-Terra-Sortiment kein Produkt mit reinem P/K-Profil ohne N existiert (ausser PK 13-14, das hier wegen der extremen Konzentration nicht eingesetzt wird).

---

### 3.3 EC-Budget Tigerblume

**Befund: AKZEPTABEL -- geringe Abweichungen, plausibler Kontext**

**Rechenweg (Basisannahme: Leitungswasser 0.4 mS/cm):**

| Phase | EC-Kalkulation | Kalkulation-Ergebnis | Deklarierter target_ec_ms | Differenz | Steckbrief-EC |
|-------|---------------|---------------------|--------------------------|-----------|---------------|
| VEGETATIVE | TG 2.0 x 0.08 + PZ 0.00 + 0.40 | 0.16 + 0.40 = **0.56 mS/cm** | 0.6 | +0.04 | 0.8-1.2 |
| FLOWERING | TB 2.5 x 0.10 + PZ 0.00 + 0.40 | 0.25 + 0.40 = **0.65 mS/cm** | 0.7 | +0.05 | 0.8-1.2 (Knospen) |

Die Abweichungen (+0.04 und +0.05 mS/cm) liegen im Toleranzbereich der Leitungswasser-Variabilitat (0.3-0.5 mS/cm in Deutschland). Bei Leitungswasser EC 0.45 mS/cm wuerde das Budget genau auf target_ec_ms treffen. Kein importkritischer Fehler.

**Hinweis zur Steckbrief-Abweichung:**
Der Steckbrief empfiehlt fuer Knospenbildung EC 1.0-1.4 mS/cm und fuer Bluete 0.8-1.2 mS/cm. Die tatsaechliche Giessloesung (0.65-0.70 mS/cm) liegt unterhalb dieser Werte. Der Plan deklariert Tigridia als Schwach-/Mittelzehrer und begrenzt die EC bewusst. Diese Strategie ist korrekt -- der Steckbrief-EC-Bereich entspricht dem Steckbrief-Naehrstoffprofil (das auf Kalk-/Steckbrief-Empfehlungen basiert), waehrend die tatsaechliche Duengungsnotwendigkeit fuer Tigridia in der Praxis oft mit weniger als dem theoretischen Optimum gedeckt ist. Eine kurze Begruendung dieser Abweichung im Plan waere sinnvoll.

---

### 3.4 Weitere Befunde Tigerblume

**Korm vs. Knolle:**
Der Steckbrief klassifiziert Tigridia korrekt als Korm (solid, ohne Schalen). Der Plan verwendet durchgehend "Knolle" als Volkssprachlichen Begriff, was in der Gartenpraxis akzeptabel ist. Fuer die KA-Taxonomie-Daten ist der korrekte Typ `corm` (Steckbrief root_type: corm). Dies ist kein Fehler im Naehrstoffplan, aber ein Hinweis fuer konsistente Terminologie in der Benutzeroberflaeche.

**Eintagsblueten:**
Der Plan dokumentiert korrekt: "Jede Einzelbluete oeffnet nur 1 Tag -- nicht erschrecken, naechste Knospe folgt." Dies ist eine wichtige Nutzerhinweis, da viele Gaertner die schnell verwelkenden Blueten als Zeichen von Pflanzenproblemen interpretieren. Der Hinweis ist an mehreren Stellen prominent platziert.

**Wuehlmaus-Schutz:**
Korrekt erwaehnt (Abschnitt 6). Tigridia-Kormen sind fuer Wuehlmaeuse attraktiv (susser Geschmack durch Starkekorrme). Der Pflanzkorb aus Kaninchendraht ist die effektivste Praevention und wird im Plan richtig empfohlen.

**Lueckenlos-Pruefung:**
Plan-Aussage: 4 + 6 + 10 + 2 + 30 = 52 Wochen.
Kontrollrechnung:
- GERMINATION: W1-4 = 4 Wochen
- VEGETATIVE: W5-10 = 6 Wochen
- FLOWERING: W11-20 = 10 Wochen
- HARVEST: W21-22 = 2 Wochen
- DORMANCY: W23-52 = 30 Wochen
- Summe: 52 Wochen -- lueckenlos. Korrekt.

---

## 4. UEBERGREIFENDE BEFUNDE (alle drei Plaene)

### 4.1 cycle_restart_from_sequence -- Korrektheitspruefung

**Befund: ALLE DREI KORREKT**

| Plan | Typ | cycle_restart_from_sequence | Bewertung |
|------|-----|----------------------------|-----------|
| Dahlie | perennierend via Knolle | 1 (Neustart bei GERMINATION = Vorkeimen) | Korrekt |
| Petunie | annuell | null | Korrekt |
| Tigerblume | perennierend via Korm | 1 (Neustart bei GERMINATION = Vorkeimen) | Korrekt |

Die Differenzierung zwischen echtem Neustart (cycle_restart_from_sequence: 1) und einjaerigem Ende (null) ist biologisch korrekt umgesetzt. Bei Dahlie und Tigerblume startet der jaehrliche Zyklus korrekt bei Sequenz 1 (Vorkeimen/Knollenaustreibung), was der biologischen Realitaet entspricht: Die eingelagerte Knolle "erwacht" im Fruehjahr, durchlaeuft den vollen Zyklus und ruht erneut.

### 4.2 DORMANCY-Temperaturen -- Vergleich und Differenzierung

**Befund: KORREKT DIFFERENZIERT**

| Pflanze | DORMANCY-Temperatur Plan | DORMANCY-Temperatur Steckbrief | Korrekt? |
|---------|------------------------|-------------------------------|---------|
| Dahlie (Dahlia pinnata) | 4-8 degC | 4-10 degC (winter_quarter_temp_min: 4, max: 10) | Ja (konservativ, aber im Korridor) |
| Tigerblume (Tigridia pavonia) | 10-13 degC | 10-13 degC (winter_quarter_temp_min: 10, max: 13) | Ja (exakt) |
| Petunie | -- (annuell; keine Lagerung) | Winterquartier Stecklinge: 5-12 degC | -- (Stecklinge optional; Plan erwaehnt 5-12 degC korrekt) |

Die Temperaturdifferenzierung zwischen Dahlie (4-8 degC) und Tigerblume (10-13 degC) ist der biologisch kritischste Punkt beider Knollenplaene und wird korrekt umgesetzt. Die expliziten Warnungen ("NICHT 4-8 degC wie Dahlien!") in allen relevanten Abschnitten des Tigerblumen-Plans sind vorbildlich.

### 4.3 Mischungsreihenfolge der Produkte

**Befund: KORREKT**

Alle drei Plaene halten die Mischpriorititaeten (mixing_priority-Werte aus den Produktdaten) ein:
- Terra Grow / Terra Bloom: Prio 20 (zuerst ins Wasser)
- PK 13-14: Prio 30 (nach Basisduenger)
- Sugar Royal: Prio 65 (spaet)
- Pure Zym: Prio 70 (am Ende)
- pH-Pruefung: immer zuletzt

Die Reihenfolge ist in den Delivery-Channel-Hinweisen korrekt dokumentiert. Kein Hinweis auf potenzielle Ausfaellungen zwischen den Produkten gefunden.

---

## 5. ZUSAMMENFASSUNG DER BEFUNDE

### Rote Befunde -- Korrekturbedarf vor Import

**F-001 (Dahlie): target_ec_ms-Werte nicht konsistent mit EC-Budget-Kalkulation**
- Betrifft: VEGETATIVE (deklariert 1.2, kalkuliert 0.81) und FLOWERING (deklariert 1.4, kalkuliert 0.90-1.09)
- Problem: `target_ec_ms` wurde aus dem Steckbrief-Optimumbereich entnommen, nicht aus der tatsaechlichen Dosierungskalkulation
- Empfehlung: Werte auf 0.8 (VEG), 0.9 (FLO Standard), 1.1 (FLO mit PK-Boost) setzen
- Import-Risiko: Systeme, die auf Basis von target_ec_ms die Dosierung regulieren, wuerden massiv ueberdosieren

**F-002 (Petunie): target_ec_ms-Werte nicht konsistent mit EC-Budget-Kalkulation**
- Betrifft: SEEDLING (deklariert 0.8, kalkuliert 0.60), VEGETATIVE (deklariert 1.2, kalkuliert 0.82), FLOWERING (deklariert 1.6, kalkuliert 0.92)
- Problem: Gleiche Ursache wie F-001, FLOWERING-Diskrepanz betraegt 0.68 mS/cm
- Empfehlung: Werte auf 0.6 (SEED), 0.8 (VEG), 0.9 (FLO) setzen; Steckbrief-Zielbereiche nur in notes-Text referenzieren
- Import-Risiko: Identisch mit F-001, bei FLOWERING besonders ausgepraegt

### Orangene Befunde -- Empfohlene Verbesserungen

**U-001 (Dahlie): NPK-Abweichung FLOWERING zu Steckbrief ohne explizite Mengenbegruendung**
- Steckbrief empfiehlt 1:3:3 bis 0:2:3; Terra Bloom liefert 2:2:4
- Plan erkennt dies, begruendet aber nicht explizit, warum 5 ml/L Terra Bloom dennoch ausreicht
- Empfehlung: Ergaenzung in Hinweisen: "Bei 5 ml/L Terra Bloom und EC < 1.0 mS/cm ist der absolute N-Eintrag (5 ml/L x 0.01% N fuer TG-Aequivalent) gering genug, um die P/K-Wirkung nicht zu beeintraechtigen."

**U-002 (Petunie): Warum Sugar Royal in FLOWERING -- Begruendung ausbaubar**
- Sugar Royal (9-0-0) bei 1 ml/L traegt minimal bei (0.02 mS/cm EC, ca. 0.09 mg/L N)
- Plan nennt "Aminosaeuren, Chlorophyll-Stimulation" als Begruendung
- Bei einer N-kritischen Pflanze wie Petunien in der Bluetephase sollte expliziter erklaert werden, warum der N-Beitrag von Sugar Royal bei 1 ml/L unproblematisch ist
- Empfehlung: Ergaenzung: "1 ml/L Sugar Royal traegt weniger als 0.1 ppm N bei -- vernachlaessigbar; Hauptnutzen sind Aminosaeuren als Wuchsstimulanzien fuer Dauertriebwachstum"

**U-003 (Tigerblume): EC-Zielwerte unterhalb Steckbrief-Optimum ohne Begruendung**
- Steckbrief empfiehlt 0.8-1.2 mS/cm fuer Knospenbildung und Bluete
- Plan-EC: 0.65-0.70 mS/cm (Schwachzehrer-Strategie)
- Abweichung ist fachlich korrekt, aber sollte als bewusste Entscheidung dokumentiert werden
- Empfehlung: Erlaeuterung hinzufuegen: "Bewusst unter Steckbrief-Optimum (0.8-1.2 mS/cm), da Tigridia pavonia als Schwachzehrer im Freiland/Kuebel bei hoeherer EC Wachstumshemmung zeigt; Freilandregendilution reduziert tatsaechliche Substrat-EC"

### Gelbe Befunde -- Hinweise und Praezisierungen

**P-001 (Petunie): npk_ratio-Konvention inkonsistent**
- SEEDLING: npk_ratio [3.0, 1.0, 3.0] = Terra Grow Produktverhaeltnis (korrekt)
- VEGETATIVE: npk_ratio [2.0, 1.0, 2.0] = Steckbrief-Idealwert (nicht Produktverhaeltnis)
- FLOWERING: npk_ratio [1.0, 2.0, 3.0] = Steckbrief-Idealwert
- Empfehlung: Einheitliche Konvention waehlen; Steckbrief-Idealwert als npk_ratio ist vertretbar, aber muss einheitlich sein

**P-002 (Dahlie): Lagermedium-Praezisierung fuer DORMANCY**
- Plan nennt "Vermiculite, Kokoserde oder Zeitungspapier" als Lagermedium
- Steckbrief-Protokoll warnt explizit vor nassem Saegemehl
- Plan erwaehnt in Section 6 "Einlagerung" kein Saegemehl, aber "Kisten mit leicht feuchtem Vermiculite/Kokoserde" -- Zeitungspapier als Alternative empfohlen
- Ergaenzung empfohlen: "Nasses Saegemehl vermeiden (Faeulnisrisiko; Saegemehl haelt zu viel Feuchtigkeit)"

**P-003 (alle drei Plaene): Giessplan-Override DORMANCY interval_days: 0**
- Technische Frage: Interpretiert das System `interval_days: 0` als "deaktiviert" oder als "sofort-Wiederholung"?
- Fuer Dahlie und Tigerblume ist kein Giessen waehrend Dormanz biologisch korrekt
- Fallback-Sicherheit: Wenn das System 0 als "taeglich giessen" interpretiert, waere das ein katastrophaler Fehler fuer trocken eingelagerte Knollen
- Empfehlung an Entwickler: Semantik von `interval_days: 0` im System klaeren; alternativ `enabled: false` auf dem Delivery-Channel

---

## 6. EMPFEHLUNG ZUM IMPORT

### Dahlie
**Status: Importierbar nach Korrektur F-001**
1. Vor Import (kritisch): target_ec_ms in VEGETATIVE-Kanal auf 0.8 setzen; target_ec_ms in FLOWERING-Kanal auf 0.9 (Standard) und 1.1 (mit PK-Boost) setzen
2. Empfohlen (nicht kritisch): Hinweis fuer FLOWERING ergaenzen (U-001); Saegemehl-Warnung ergaenzen (P-002)

### Petunie
**Status: Importierbar nach Korrektur F-002 und P-001**
1. Vor Import (kritisch): Alle aktiven target_ec_ms-Werte auf berechnete EC-Budgets anpassen (F-002)
2. Vor Import (empfohlen): npk_ratio-Konvention vereinheitlichen (P-001); Sugar Royal-Begruendung ergaenzen (U-002)

### Tigerblume
**Status: Importierbar -- keine kritischen Fehler**
1. Empfohlen: EC-Abweichung vom Steckbrief-Optimum begruenden (U-003); interval_days: 0 Semantik mit Entwicklern klaeren (P-003)

---

## 7. PRODUKTDOSIERUNGSVERGLEICH MIT HERSTELLERPLAN

Der offizielle Plagron 100% TERRA Grow Schedule sieht fuer die Hauptkulturen 5.0 ml/L Terra Grow und 5.0 ml/L Terra Bloom vor. Die Zierpflanzen-Plaene weichen davon systematisch ab:

| Plan | Produkt | Herstellerplan | Naehrstoffplan | Reduktionsfaktor | Begruendung |
|------|---------|---------------|----------------|-------------------|-------------|
| Dahlie (Starkzehrer) | Terra Grow VEG | 5.0 ml/L | 5.0 ml/L | 1.0x | Korrekt -- Starkzehrer volle Dosis |
| Dahlie | Terra Bloom FLO | 5.0 ml/L | 5.0 ml/L (3.0 reduziert Sep) | 1.0x (0.6x) | Korrekt |
| Dahlie | PK 13-14 | 1.5 ml/L | 0.75 ml/L | 0.5x | Korrekt -- halbiert fuer Zierpflanze |
| Petunie (Starkzehrer) | Terra Grow VEG | 5.0 ml/L | 5.0 ml/L | 1.0x | Korrekt |
| Petunie | Terra Bloom FLO | 5.0 ml/L | 5.0 ml/L | 1.0x | Korrekt fuer Starkzehrer |
| Tigerblume (Schwachzehrer) | Terra Grow VEG | 5.0 ml/L | 2.0 ml/L | 0.4x | Korrekt -- Schwachzehrer 40% Dosis |
| Tigerblume | Terra Bloom FLO | 5.0 ml/L | 2.5 ml/L | 0.5x | Korrekt -- Schwachzehrer 50% Dosis |

Die Dosierungsreduktionen fuer die Tigerblume (40-50%) sind biologisch korrekt und konsistent mit der Schwachzehrer-Einstufung. Fuer Dahlie und Petunie als Starkzehrer sind die vollen Herstellerdosen angemessen.

---

## 8. BIOLOGISCHE SONDERTHEMEN

### Knollen-Zyklus-Modellierung im Vergleich

Beide perennierenden Knollengewaechse (Dahlie und Tigerblume) verwenden GERMINATION fuer die Vorkeimphase, obwohl technisch gesehen keine Samenkeimung stattfindet. Dies ist eine biologisch begruendete Nutzung des Enums:
- Die Knollenaustreibung verlaeuft physiologisch analog zur Samenkeimung (Reservestoffmobilisierung durch Amylasen/Proteasen, erster Austrieb aus dem Speicherorgan)
- Das Merkmal "Knolle hat Naehrstoffreserven -- kein Duenger noetig" gilt analog zur Cotyledon-Phase bei der Samenkeimung
- Das watering_schedule_override ("erst nach Austrieb giessen") entspricht dem Trockenkeimungshinweis bei bestimmten Samentypen

Diese semantische Erweiterung ist in der Praxis akzeptabel. Bei kuenftiger Modellierungsarbeit koennte ein explizites Enum `SPROUTING` oder `TUBER_ACTIVATION` die Unterscheidung klarer machen, ist aber fuer den aktuellen Importbetrieb nicht erforderlich.

### Photoperiodismus und Dahlien-Knospenbildung

Der Steckbrief klassifiziert Dahlien als `short_day` (fakultativ): "Blueteninitiierung bei Nachtlaenge > 12 h gefoerdert; Tuberisierung eindeutig kurztaggesteuert." Der Naehrstoffplan beruecksichtigt dies implizit durch die Phasen-Kalendrisierung (FLOWERING ab Mitte Juni, also bei beginnender Tagverkuerzung nach Sommersolstitium). Eine explizite Erwaehnung in den Phase-Hinweisen ("Knospenbildung ab Mitte Juni = natuerliche Kurztagresponse ab Sommersonnenwende") wuerde den biologischen Mechanismus transparent machen, ist aber nicht zwingend erforderlich.

### Kaelte-Impuls fuer Dahlie vor Einlagerung

Der Plan empfiehlt: "Pflanze nach erstem Frost einziehen lassen -- Laub wird schwarz/braun. 1-2 Tage stehen lassen fuer Kaelteimpuls." Dies ist eine korrekte und biologisch wichtige Praxis: Der Kaelte-Impuls foerdert die Verlagerung von Naehrstoffen aus dem sterbenden oberirdischen Gewebe in die Knollen und induziert den physiologischen Dormanz-Eintritt. Der Plan begruendet diesen Schritt nicht physiologisch, was fuer die Nutzer-Kommunikation erwaehnenswert waere.

---

**Dokumentversion:** 1.0
**Review abgeschlossen:** 2026-03-06
**Naechste Pruefung empfohlen nach:** Korrekturen gemaess F-001 (Dahlie) und F-002 (Petunie)
