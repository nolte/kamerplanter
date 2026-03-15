# Fachliches Review: Naehrstoffplan Chlorophytum comosum -- Gardol Gruenpflanzenduenger

**Erstellt von:** Agrarbiologie-Experte
**Datum:** 2026-03-01
**Reviewtyp:** Vollstaendige fachliche Pruefung (NPK, EC, Phasen, Giessplan, Ca/Mg/Fe, Sicherheit, Konsistenz)
**Pruefstatus:** Abgeschlossen

**Gepruefter Plan:** `/spec/ref/nutrient-plans/gruenlilie_gardol.md` v1.0
**Steckbrief:** `/spec/ref/plant-info/chlorophytum_comosum.md`
**Produktdaten:** `/spec/ref/products/gardol_gruenpflanzenduenger.md`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Biologische Korrektheit | 4 / 5 | Solide Grundlagen; ein NPK-Abweichungs-Problem mit Erklaerungsbedarf |
| Agronomische Plausibilitaet | 5 / 5 | Schwachzehrer-Logik konsequent umgesetzt |
| Phasen-Mapping | 4 / 5 | Wochen stimmen; ein Wochendiskrepanz-Risiko dokumentiert |
| Giessplan | 4 / 5 | Intervalle korrekt; ein Inkonsistenz zwischen Prose und Tabelle |
| Ca/Mg/Fe-Versorgung | 4 / 5 | Logisch; EC-Schaetzung fuer Mikronuehrstoffe bleibt unbegruendet |
| Sicherheitshinweise | 5 / 5 | Vollstaendig und artspeziefisch; Steckbrief-Angaben korrekt referenziert |
| Lueckenlos-Pruefung Wochen | 5 / 5 | 3 + 9 + 32 + 16 = 60, keine Luecken, korrekt |
| Konsistenz Tabellen/Text/JSON | 4 / 5 | Ein Volumen-Inkonsistenz SEEDLING (Fliesstext vs. JSON); ein fehlender Override im JSON VEGETATIVE |

**Gesamtbewertung:** Sehr guter Entwurf. Der Plan ist biologisch solide, fuer einen Schwachzehrer agronomisch angemessen konservativ und benutzerfreundlich dokumentiert. Sechs Befunde erfordern Korrekturen oder Klarstellungen, keiner davon ist ein kritischer Fehler. Der Plan ist importierbar mit den unten genannten Anpassungen.

---

## Befunde

### F-001 (Rot) -- NPK-Verhaeltnis VEGETATIVE entspricht nicht dem Steckbrief-Ideal, ohne ausreichende Erklaerung der Konsequenz

**Prioritaet:** Hoch (fachlich relevant, aber kein Fehler -- Dokumentationsluecke)

**Quelle:**
- Naehrstoffplan Abschnitt 4.3: `npk_ratio: [1.5, 1.0, 1.5]`
- Steckbrief Abschnitt 2.3: `Aktives Wachstum -- NPK-Verhaeltnis 3:1:2`

**Problem:**
Der Steckbrief definiert das agronomische Ideal fuer *Chlorophytum comosum* im aktiven Wachstum als **3:1:2** (N deutlich dominant, K staerker als P). Der Plan nutzt **1,5:1:1,5** (Gardol-Produktrealitaet: NPK 6-4-6), was einem Verhaeltnis von ca. 1,5:1:1,5 entspricht.

Das ist keine Falschinformation -- der Plan erklaert die Abweichung korrekt als "fuer Erdkultur akzeptabel". Was fehlt: eine Bewertung der **praktischen Konsequenz** dieser Abweichung. Bei einem Schwachzehrer mit der halben Herstellerdosierung (2 ml/L statt 4 ml/L) sind die absoluten Mengenunterschiede gering. Das Risiko ist real, aber klein: leicht suboptimale N-Versorgung im Vergleich zum Ideal-Verhaeltnis.

Fuer einen Referenzplan (is_template: true) sollte diese Abweichung expliziter kommuniziert werden, damit Anwender informiert entscheiden koennen.

**Empfehlung:**
In den Notes der VEGETATIVE-Phase ergaenzen:

> "Das NPK-Verhaeltnis 1,5:1:1,5 (Gardol-Produktrealitaet) weicht vom pflanzenphysiologischen Ideal 3:1:2 ab. Bei der halben Herstellerdosierung (2 ml/L) betraegt der absolute N-Beitrag ca. 0,12 g/L -- dies liegt weit unterhalb toxischer Schwellen und ist fuer einen Schwachzehrer hinreichend. Wer das Idealverhaeltnis anstrebt, waehlt COMPO Gruenpflanzen- und Palmenduenger (7-3-6) oder Substral (7-3-5)."

---

### F-002 (Rot) -- EC-Zielwert VEGETATIVE unklar: Gesamtloesung oder EC-Beitrag des Duengers?

**Prioritaet:** Hoch (Messgrossenkonsistenz)

**Quelle:**
- Plan Abschnitt 4.3, Delivery Channel: `target_ec_ms: 0.6`
- Plan Abschnitt 4, Hinweis EC-Differenz: "Die EC-Zielwerte beziehen sich auf die Gesamtloesung inkl. Basis-Wasser-EC."
- Plan Abschnitt 4, Tabelle EC-Beitrag: "Halbe Dosis 2,0 ml/L --> ~0,12 mS/cm"

**Problem:**
Der EC-Beitrag von 2 ml/L Gardol wird auf ~0,12 mS/cm geschaetzt. Leitungswasser liefert 0,3--0,7 mS/cm. Die Gesamtloesung liegt also bei **0,42--0,82 mS/cm**, nicht eindeutig bei 0,6.

Der `target_ec_ms: 0.6` im Delivery Channel suggeriert einen Zielwert, der:
- Bei hartem Leitungswasser (0,7 mS/cm Basiswasser) bereits **ohne Duenger ueberschritten** wird
- Bei weichem Leitungswasser (0,3 mS/cm) sinnvoll als Gesamtziel erreichbar ist

Der Plan erklaert im Fliesstext korrekt, dass exakte EC-Steuerung in Erdkultur nicht noetig ist -- aber der numerische `target_ec_ms`-Wert im JSON-Delivery-Channel ist ohne diese Kontextualisierung irrefuehrend.

**Steckbrief-Referenz:** Steckbrief Abschnitt 2.3: EC Aktives Wachstum `0.6--1.0 mS/cm` (Gesamtloesung).
Der Zielwert 0,6 ist also die **untere Grenze des Steckbriefs** und bei Leitungswasser ohne Duenger bereits erreicht. Das ist fachlich zwar korrekt (Schwachzehrer, minimale Duengung genuegt), muss aber klar kommuniziert werden.

**Empfehlung:**
Im JSON VEGETATIVE-Delivery-Channel Kommentar hinzufuegen und den Wert klarstellen:

```json
"target_ec_ms": 0.6,
"target_ec_ms_note": "Gesamtloesung inkl. Basiswasser (Leitungswasser 0.3-0.7 mS/cm + ~0.12 mS/cm Gardol-Beitrag). In Erdkultur kein Monitoring noetig -- Richtwert fuer Kontrollmessung bei Problemen."
```

Alternativ `target_ec_ms` auf `null` setzen und in den Notes erklaeren, dass EC-Monitoring in Erdkultur fuer diesen Schwachzehrer nicht erforderlich ist.

---

### F-003 (Orange) -- SEEDLING-Phase: Giessvolumen inkonsistent zwischen Fliesstext und JSON

**Prioritaet:** Mittel (Importfehler moeglich)

**Quelle:**
- Plan Abschnitt 3.2 (Delivery Channel drench-giessduengung Hinweis): "0,3 L Giessvolumen fuer eine etablierte Gruenlilie (Topf 14--18 cm). Fuer Jungpflanzen gelten reduzierte Volumina (siehe Phaseneintraege)."
- Plan Abschnitt 4.2 (Fliesstext SEEDLING): *kein expliziter Volumenwert angegeben*
- JSON SEEDLING Delivery Channel: `"volume_per_feeding_liters": 0.2`
- JSON GERMINATION Delivery Channel: `"volume_per_feeding_liters": 0.10`
- JSON VEGETATIVE Delivery Channel: `"volume_per_feeding_liters": 0.3`
- JSON DORMANCY Delivery Channel: `"volume_per_feeding_liters": 0.2`

**Problem:**
Das Giessvolumen 0,2 L fuer SEEDLING ist im JSON korrekt definiert, aber im Fliesstext (Abschnitt 4.2) **nicht erwaehnt**. Der allgemeine Kanalhinweis in Abschnitt 3.2 verweist auf "Phaseneintraege", ohne den Wert zu nennen. Ein Leser des Fliesstext-Abschnitts 4.2 koennte 0,3 L (aus dem allgemeinen Kanalhinweis) verwenden.

Der agronomische Wert selbst (0,2 L fuer Jungpflanze in 10--12 cm Topf) ist biologisch korrekt und plausibel.

**Empfehlung:**
In Abschnitt 4.2 (SEEDLING) den Giessplan-Override ergaenzen:

> "Giessvolumen: 0,2 L pro Giessgang (Topf 10--12 cm; bei groesseren Toepfen auf 0,3 L erhoehen)."

---

### F-004 (Orange) -- VEGETATIVE: `watering_schedule_override` fehlt im JSON

**Prioritaet:** Mittel (Import-Vollstaendigkeit)

**Quelle:**
- JSON SEEDLING: hat `watering_schedule_override` (Intervall 21 Tage)
- JSON DORMANCY: hat `watering_schedule_override` (Intervall 12 Tage)
- JSON VEGETATIVE: kein `watering_schedule_override` vorhanden
- Plan Abschnitt 4.3, Notes: "Halbe Dosis alle 21 Tage (April--September)"
- Plan Abschnitt 5 (Jahresplan): Frequenz 21-taegig fuer alle VEGETATIVE-Monate

**Problem:**
Fuer die VEGETATIVE-Phase ist im Fliesstext und im Jahresplan ein 21-Tage-Duengungsintervall beschrieben. Der globale Giessplan (`watering_schedule`) verwendet jedoch 7 Tage. Der Hinweis im Plan besagt, dass zwischen den Duengeterminen "bei Bedarf mit klarem Wasser gegossen" werden soll.

Ohne `watering_schedule_override` in der VEGETATIVE-Phase erbt diese Phase den globalen 7-Tage-Rhythmus. Das ist fuer das **Giessen** (nicht Duengen) korrekt (Gruenlilien brauchen im Sommer tatsaechlich woechentliches Giessen). Fuer die **Duengungsfrequenz** aber ergibt sich eine moegliche Fehlinterpretation: wird das System 7-taegige Duengung planen?

Das haengt von der Implementierungslogik ab (ob `watering_schedule` und Duengungsfrequenz getrennt gesteuert werden). Zur Klarheit sollte ein Override oder ein klarstellender Kommentar vorhanden sein.

**Empfehlung:**
Wenn die Systemlogik Giessen und Duengen im gleichen Rhythmus plant: `watering_schedule_override` mit Intervall 7 (Giessen) ergaenzen, und Duengungsfrequenz separat in den Notes/delivery_channels-Feldern dokumentieren.

Wenn Giessen und Duengen getrennt steuerbar: expliziten Kommentar in den JSON-Notes ergaenzen:

```json
"notes": "... Giessen: alle 7 Tage (globaler Plan). Duengung: alle 21 Tage (nur bei Duengungsgiessgang Gardol zugeben)."
```

---

### F-005 (Gelb) -- Giesshaeufigkeit SEEDLING: Override 21 Tage zu lang fuer eine Jungpflanze

**Prioritaet:** Mittel (biologische Plausibilitaet)

**Quelle:**
- JSON SEEDLING `watering_schedule_override`: `interval_days: 21`
- Steckbrief Phase Juvenil: `irrigation_frequency_days: 5-7`
- Plan Abschnitt 4.2 Notes: "Vierteldosis alle 21 Tage. [...] zwischen den Terminen bei Bedarf mit klarem Wasser giessen"

**Problem:**
Das Duengungsintervall von 21 Tagen fuer die SEEDLING-Phase ist biologisch korrekt. Kritisch ist jedoch, dass der `watering_schedule_override` auf 21 Tage gesetzt ist -- das System interpretiert diesen Override moeglicherweise als **Giessintervall**, nicht als Duengungsintervall.

*Chlorophytum comosum* im Juvenilstadium benoetigt laut Steckbrief **5--7 Tage** Giessintervall. Ein 21-Tage-Override wuerde Jungpflanzen in kleinen Toepfen stark austrocknen lassen, insbesondere bei 20--24 C Raumtemperatur.

Der Fliesstext erklaert den Unterschied ("zwischen den Terminen bei Bedarf giessen"), aber das JSON-Override kommuniziert dies nicht.

**Empfehlung:**
Den Override fuer SEEDLING auf 7 Tage setzen (Giessintervall), und die Duengungsfrequenz (21 Tage) in den delivery_channel-Notes und phase-Notes dokumentieren:

```json
"watering_schedule_override": {
  "interval_days": 7,
  ...
},
"notes": "Giessintervall 7 Tage (Fingertest: obere 2 cm trocken). Duengung nur alle 21 Tage: dann Gardol 1 ml/L ins Giesswasser. An den 2 anderen Giessterminen klares Wasser ohne Duenger."
```

Das gleiche Problem besteht in der VEGETATIVE-Phase (F-004) und muss dort analog behoben werden.

---

### F-006 (Gelb) -- EC-Schaetzung: Untere Grenze (0,06 mS/cm pro ml/L) nicht begruendet

**Prioritaet:** Niedrig (Transparenzhinweis)

**Quelle:**
- Plan Abschnitt 4: "Geschaetzter EC-Beitrag: ~0,06 mS/cm pro ml/L (Herstellerangabe fehlt, Schaetzung basierend auf NPK 6-4-6 und mineralischer Formulierung)"
- Produktdaten Abschnitt 10: `ec_contribution_per_ml: <!-- DATEN FEHLEN -- SCHAETZUNG CA. 0.06-0.10 mS/cm PRO ML/L -->`

**Problem:**
Der EC-Schaetzwert liegt am unteren Ende der Produktdaten-Angabe (0,06--0,10). Die Wahl der unteren Grenze ist konservativ und fuer einen Schwachzehrer angemessen, bleibt aber unbegruendet.

Zum Vergleich: Compo Gruenpflanzen- und Palmenduenger (7-3-6, strukturell aehnlich) hat laut Hersteller einen EC-Beitrag von ca. 0,08--0,10 mS/cm pro ml/L. Ein Wert von 0,06 ist physikalisch plausibel, aber eher niedrig fuer eine vollmineralische 6-4-6-Formulierung.

Die **praktische Auswirkung** ist gering: Bei 2 ml/L ergibt 0,06 --> 0,12 mS/cm, bei 0,10 --> 0,20 mS/cm. Beide Werte liegen weit unter dem EC-Ziel von 0,6 mS/cm und weit innerhalb des sicheren Bereichs fuer Chlorophytum comosum. Kein klinischer Unterschied zu erwarten.

**Empfehlung:**
Schaetzwert auf 0,06--0,10 erweitern und Unsicherheit explizit machen:

```
"Geschaetzter EC-Beitrag: ~0,06--0,10 mS/cm pro ml/L (Herstellerangabe fehlt; Vergleichswert Compo 7-3-6: ~0,08-0,10). Konservative Planung mit unterer Grenze 0,06."
```

---

## Positive Befunde (zur Bestaetigung)

Die folgenden Aspekte sind fachlich korrekt und verdienen explizite Bestaetigung:

### P-001 -- Schwachzehrer-Logik konsequent umgesetzt

Die halbierte Herstellerdosierung (2 ml/L statt 4 ml/L) ist fuer *Chlorophytum comosum* als `light_feeder` korrekt und stimmt mit Steckbrief-Empfehlungen ueberein (Steckbrief Abschnitt 3.2: "halbe Dosis"). Die Vierteldosis in Uebergangsphasen (Maerz, Oktober) ist biologisch sinnvoll. Beides ist intern konsistent.

### P-002 -- Fluorid-Empfindlichkeit korrekt adressiert

Die Fluorid-Empfindlichkeit von *Chlorophytum comosum* ist eine gut belegte, aber haeufig uebersehene artspezifische Eigenschaft. Der Plan adressiert sie korrekt auf mehreren Ebenen: Wasserquelle (abgestanden, Regenwasser), Substrat-pH (6,0--6,5 zur Minimierung der Fluorid-Pflanzenverfuegbarkeit), Hinweis auf Duenger-Fluorid als potenzielle Quelle. Alle drei Ebenen sind fachlich korrekt.

### P-003 -- Saisonale Ruhephase als kulturpraktische Ruhephase korrekt eingestuft

Der Plan unterscheidet korrekt zwischen obligater Dormanz (`dormancy_required: false` im Steckbrief) und kulturpraktischer Ruhephase (reduziertes Licht im Winter fuehrt zu reduziertem Stoffwechsel). Die Formulierung "keine obligate Dormanz" ist biologisch praezise. *Chlorophytum comosum* ist eine tropische Art ohne physiologisch erzwungenen Ruhebedarf.

### P-004 -- Knollenwurzel-Wasserreserve korrekt erklaert

Die Erwaehnung der Rhizotuberkeln (fleischige Speicherwurzeln) als Puffer fuer Trockenperioden und als Risikofaktor fuer Uebergiessen ist biologisch korrekt. Dieser Punkt wird im Steckbrief bestaetigt und im Plan konsistent kommuniziert.

### P-005 -- Salzspuelungs-Rhythmus artspezifisch korrekt

Drei Salzspuelungen pro Jahr (April, Juli, November) sind fuer einen Schwachzehrer mit bekannter Salzempfindlichkeit angemessen. Der Steckbrief empfiehlt alle 3--4 Monate (entspricht 3--4x/Jahr). Der Plan mit 3x/Jahr liegt im korrekten Bereich.

### P-006 -- Phasen-Lueckenlos-Pruefung korrekt

Woche 1--3 (GERMINATION) + Woche 4--12 (SEEDLING) + Woche 13--44 (VEGETATIVE) + Woche 45--60 (DORMANCY) = 3 + 9 + 32 + 16 = 60 Wochen. Keine Luecken, keine Ueberschneidungen. `cycle_restart_from_sequence: 3` (VEGETATIVE) korrekt, da GERMINATION und SEEDLING einmalig sind.

### P-007 -- Stolonenbildung und Photoperiodismus korrekt

Der Hinweis, dass Stolonenbildung durch Kurztagsbedingungen (<12h Licht) ausgeloest wird, ist fachlich korrekt (bestaetigt im Steckbrief Abschnitt 1.3). Die Entscheidung, dafuer keine eigene Duengungsphase einzufuehren, ist agronomisch richtig -- die Stolonenbildung ist keine Naehrstoff-getriebene Reaktion.

### P-008 -- Toxizitaetsdaten korrekt und vollstaendig

ASPCA-Einstufung als nicht giftig fuer Katzen, Hunde und Kinder korrekt (Steckbrief Abschnitt 1.4 bestaetigt). Der differenzierte Hinweis zur Katzen-Attraktion und zum Duengerrueckstand auf Blaettern nach Duengung ist praktisch wertvoll und agronomisch korrekt (Duengerkonzentrat kann Magen-Darm-Reizung verursachen, auch wenn die Pflanze selbst ungiftig ist).

### P-009 -- Jahresverbrauchsrechnung plausibel

Geschaetzte 6 ml Gardol/Jahr bei einer Pflanze ist rechnerisch nachvollziehbar:
- 6 Monate halbe Dosis: ~1,4 Duengungen/Monat x 0,3 L x 2 ml/L = ~5,0 ml
- 2 Monate Vierteldosis: ~1,4 x 0,3 L x 1 ml/L = ~0,84 ml
- Gesamt: ~5,84 ml, gerundet 6 ml -- korrekt.

Die 1-L-Flasche fuer "170 Gruenlilien-Jahre" ist kommunikativ wirkungsvoll und sachlich korrekt.

---

## Zusammenfassung der Befunde

| Nr. | Typ | Beschreibung | Prioritaet | Sektion im Plan |
|-----|-----|-------------|-----------|-----------------|
| F-001 | Dokumentationsluecke | NPK-Abweichung 1,5:1:1,5 vs. Ideal 3:1:2 -- Konsequenz nicht erklaert | Hoch | Abschnitt 4.3 |
| F-002 | Messgroessen-Inkonsistenz | `target_ec_ms: 0.6` im JSON: Gesamtloesung oder Duengerbeitrag unklar | Hoch | JSON VEGETATIVE |
| F-003 | Inkonsistenz Fliesstext/JSON | Giessvolumen SEEDLING (0,2 L) nur im JSON, nicht im Fliesstext | Mittel | Abschnitt 4.2 / JSON |
| F-004 | Import-Luecke | `watering_schedule_override` fehlt im JSON VEGETATIVE | Mittel | JSON VEGETATIVE |
| F-005 | Biologische Plausibilitaet | SEEDLING-Override 21 Tage zu lang als Giessintervall fuer Jungpflanzen | Mittel | JSON SEEDLING |
| F-006 | Transparenz | EC-Schaetzung 0,06 mS/cm/ml am unteren Rand, ohne Begruendung | Niedrig | Abschnitt 4 |

---

## Spezifische Konsistenzpruefung: Tabellen / Fliesstext / JSON

| Parameter | Tabelle (Abschnitt 4.x) | Fliesstext / Notes | JSON | Konsistent? |
|-----------|------------------------|-------------------|------|-------------|
| GERMINATION Wochen 1--3 | Korrekt | Korrekt | `week_start: 1, week_end: 3` | Ja |
| SEEDLING Wochen 4--12 | Korrekt | Korrekt | `week_start: 4, week_end: 12` | Ja |
| VEGETATIVE Wochen 13--44 | Korrekt | Korrekt | `week_start: 13, week_end: 44` | Ja |
| DORMANCY Wochen 45--60 | Korrekt | Korrekt | `week_start: 45, week_end: 60` | Ja |
| GERMINATION Giessintervall 3 Tage | Tabelle: 3 Tage | Notes: 3 Tage | `interval_days: 3` | Ja |
| SEEDLING Duengungsintervall 21 Tage | Tabelle: 21 Tage | Notes: 21 Tage | `interval_days: 21` | Ja (aber: Problem F-005) |
| SEEDLING Giessvolumen 0,2 L | Nicht in Tabelle | Nicht in Notes | `volume: 0.2` | Nein (F-003) |
| VEGETATIVE ml/L 2,0 | Tabelle: 2,0 | Notes: Halbe Dosis | `ml_per_liter: 2.0` | Ja |
| VEGETATIVE Giessvolumen 0,3 L | Abschnitt 3.2: 0,3 L | Notes: implizit | `volume: 0.3` | Ja |
| VEGETATIVE watering_override | Tabelle: kein Override | Notes: 21-taegig Duengung | JSON: fehlt | Nein (F-004) |
| DORMANCY Giessintervall 12 Tage | Tabelle: 12 Tage | Notes: 12 Tage | `interval_days: 12` | Ja |
| DORMANCY Giessvolumen 0,2 L | Nicht in Tabelle | Notes: "reduziertes Volumen" | `volume: 0.2` | Partiell (Wert korrekt, Fliesstext vage) |
| NPK VEGETATIVE | Tabelle: 1,5:1:1,5 | Notes: "Gardol-Produktrealitaet" | `npk_ratio: [1.5, 1.0, 1.5]` | Ja |
| EC VEGETATIVE | Tabelle: 0,6 mS/cm | Fliesstext: Gesamtloesung | `target_ec_ms: 0.6` | Partiell (F-002) |
| Salzspuelungen April, Juli, November | Jahresplan: korrekt | Abschnitt 5 Notes: korrekt | Nicht im JSON | Kein Befund (Salzspuelungen koennen als Task modelliert werden) |
| Jahresverbrauch ~6 ml | Abschnitt 5 Rechnung | Rechnung korrekt | n.a. | Ja |
| DORMANCY Kanalname | "wasser-bewurzelung" | Kanalname aus Abschnitt 3.1 | `channel_id: "wasser-bewurzelung"` | Technisch korrekt, semantisch fragwuerdig* |

*) Der Kanal "wasser-bewurzelung" wird auch fuer DORMANCY (Ruhephase) verwendet. Der Name ist irrefuehrend -- er suggeriert Bewurzelung, wird aber fuer die Winterpause genutzt. Besser waere ein generischer Name wie "nur-wasser" oder zwei getrennte Kanaele. Kein Fehler, aber Verbesserungsmoeglichkeit.

---

## Empfehlungen zur Kanalbezeichnung

Der Kanal `wasser-bewurzelung` wird in zwei semantisch unterschiedlichen Kontexten verwendet:
1. GERMINATION: Kindel-Bewurzelung (passt zum Namen)
2. DORMANCY: Ruhephase-Giessen (passt nicht zum Namen)

**Vorschlag:** Kanal umbenennen in `nur-wasser` oder zwei Kanaele anlegen:
- `nur-wasser-bewurzelung` (GERMINATION)
- `nur-wasser-ruhe` (DORMANCY)

Oder einen generischen Kanal `nur-wasser` fuer beide Phasen verwenden, wenn das System das unterstuetzt.

---

## Korrekte Aspekte: Pruefpunkte aus der Aufgabenstellung

### 1. NPK-Verhaeltnisse und EC-Zielwerte pro Phase

| Phase | Plan | Steckbrief | Beurteilung |
|-------|------|------------|-------------|
| GERMINATION | 0:0:0, EC null | 0:0:0, EC 0,0 | Korrekt |
| SEEDLING | 1:1:1, EC 0,4 | 1:1:1, EC 0,3--0,6 | Korrekt |
| VEGETATIVE | 1,5:1:1,5, EC 0,6 | 3:1:2, EC 0,6--1,0 | NPK-Abweichung erklaert (F-001), EC untere Grenze (F-002) |
| DORMANCY | 0:0:0, EC null | 0:0:0, EC 0,0 | Korrekt |

### 2. Dosierungen fuer einen Schwachzehrer

Steckbrief: `nutrient_demand_level: light_feeder`, Empfehlung "halbe Dosis".
Plan: 2 ml/L (VEGETATIVE) = halbe Herstellerdosierung (4 ml/L).
Beurteilung: **Korrekt.** Konservative, artspeziefische Dosierung.

### 3. Phasen-Mapping: Sind die Wochen realistisch?

| Phase | Wochen | Biolog. Realitaet | Beurteilung |
|-------|--------|-------------------|-------------|
| GERMINATION (Bewurzelung) | 3 Wochen | 1--3 Wochen bis Bewurzelung Kindel | Korrekt, am oberen Rand des realen Bereichs (7--21 Tage = 1--3 Wochen) |
| SEEDLING (Juvenil) | 9 Wochen | 30--90 Tage (4--12 Wochen) | Korrekt (9 Wochen im plausiblen Bereich) |
| VEGETATIVE (Aktives Wachstum) | 32 Wochen | Maerz--Oktober = ca. 32 Wochen | Korrekt |
| DORMANCY (Ruhe) | 16 Wochen | November--Februar = ca. 17 Wochen | Geringfuegige Diskrepanz: 16 Wochen im Plan vs. 17 reale Kalenderwochen November--Februar (je nach Jahresanfang). Kein klinisch relevanter Unterschied fuer eine Zimmerpflanze; die Phasengrenze ist saisonal, nicht starr. Kein Befund. |

Gesamtbewertung Phasen-Mapping: **Korrekt und biologisch plausibel.**

### 4. Giessplan: Stimmen die Intervalle?

| Phase | Plan-Override | Steckbrief-Angabe | Urteil |
|-------|--------------|-------------------|--------|
| GERMINATION | 3 Tage | "Substrat feucht halten" | Korrekt fuer kleine Toepfe bei 20--24 C |
| SEEDLING | 21 Tage (Override) | 5--7 Tage | Problem F-005: Override sollte 7 Tage (Giessen), Duengung separat 21 Tage |
| VEGETATIVE | 7 Tage (global, kein Override) | 5--7 Tage | Korrekt; Override fehlt im JSON (F-004) |
| DORMANCY | 12 Tage | 10--14 Tage | Korrekt, im plausiblen Bereich |

### 5. Ca/Mg/Fe-Versorgung

| Naehrstoff | Plan | Steckbrief | Produktdaten | Beurteilung |
|-----------|------|------------|--------------|-------------|
| Calcium | SEEDLING: 30 ppm (aus Leitungswasser); VEGETATIVE: 60 ppm (aus Leitungswasser) | SEEDLING: 30 ppm; VEGETATIVE: 60 ppm | Gardol: kein Ca | Korrekt: Leitungswasser als Ca-Quelle bei Erdkultur biologisch plausibel. Hinweis auf CalMag bei weichem/Osmosewasser vorhanden. |
| Magnesium | SEEDLING: 15 ppm; VEGETATIVE: 30 ppm | SEEDLING: 15 ppm; VEGETATIVE: 30 ppm | Gardol: kein Mg | Korrekt. Gleiche Begruendung wie Ca. |
| Eisen | VEGETATIVE: 1,5 ppm (Notes) | VEGETATIVE: 1,5 ppm | Gardol: Spurenelemente enthalten (Details fehlen) | Korrekt. Der Plan nennt Fe in Notes, aber nicht als strukturiertes Feld -- Steckbrief gibt 1,5 ppm vor. Gardol enthalt wahrscheinlich Fe-Chelate. Kein Befund, aber Datentransparenz fehlt (Produktdaten unvollstaendig). |
| Calcium GERMINATION/DORMANCY | null | "--" | -- | Korrekt: keine Duengung, kein Bedarf zu spezifizieren. |

Ca/Mg-Logik ist biologisch stimmig: In Erdkultur mit Leitungswasser liefert das Wasser Ca (dt. Durchschnitt ~100 ppm) und Mg (~15 ppm), Gardol ergaenzt Spurenelemente. Die Werte im Plan (60 ppm Ca, 30 ppm Mg fuer VEGETATIVE) entsprechen mittelharten Leitungsverhaeltnissen und sind realistisch.

### 6. Sicherheitshinweise

Pruefpunkte:
- Toxizitaet Katzen: Korrekt (ASPCA: ungiftig, leichte GI-Reizung bei grossen Mengen) -- Ja
- Toxizitaet Hunde: Korrekt -- Ja
- Toxizitaet Kinder: Korrekt -- Ja
- Duenger-Konzentrat-Hinweis: Ja (Drainage-Wasser von Haustieren fernhalten)
- Katzen-Attraktion und Blatt-Duengerueckstand: Ja (praktisch wertvoll)
- Fluorid-Empfindlichkeit: Vollstaendig (Wasserquelle, Substrat-pH, Duenger-Fluorid) -- Ja
- Salzempfindlichkeit: Vollstaendig -- Ja
- Kein Blattgloenzer: Ja

Sicherheitshinweise sind **vollstaendig und artspeziefisch korrekt.**

### 7. Lueckenlos-Pruefung der Wochen

Woche 1--3 (3) + 4--12 (9) + 13--44 (32) + 45--60 (16) = **60 Wochen, lueckenlos.** Im Plan selbst korrekt dokumentiert (Abschnitt 2, Lueckenlos-Pruefung). Keine Befunde.

### 8. Konsistenz zwischen Tabellen, Fliesstext und JSON

Drei Inkonsistenzen gefunden (F-002, F-003, F-004). Details siehe obige Befunde. Uebrige Parameter sind konsistent.

---

## Importbereitschaft (Checkliste)

| Pruefpunkt | Status | Anmerkung |
|-----------|--------|-----------|
| NutrientPlan JSON valide | Ja | |
| Alle 4 PhaseEntry JSONs vorhanden | Ja | |
| sequence_order korrekt (1, 2, 3, 4) | Ja | |
| week_start/week_end lueckenlos | Ja | |
| is_recurring korrekt gesetzt | Ja | GERMINATION/SEEDLING false, VEGETATIVE/DORMANCY true |
| cycle_restart_from_sequence korrekt | Ja | Sequenz 3 (VEGETATIVE) |
| fertilizer_dosages referenziert | Ja | `<gardol_gruenpflanzenduenger_key>` als Platzhalter |
| Delivery Channel IDs konsistent | Ja | wasser-bewurzelung, drench-giessduengung |
| watering_schedule_override vollstaendig | Bedingt | VEGETATIVE-Override fehlt (F-004) |
| Volumen-Angaben konsistent | Bedingt | SEEDLING-Volumen nur im JSON (F-003) |
| target_ec_ms semantisch klar | Bedingt | Interpretationsrisiko (F-002) |

**Importempfehlung:** Plan kann importiert werden. Vor dem Import sollten F-004 (fehlender Override VEGETATIVE) und F-005 (SEEDLING Override-Intervall) behoben werden, da diese die Systemlogik bei der Aufgabengenerierung beeinflussen koennen.

---

## Quellen dieses Reviews

1. Gepruefter Plan: `/spec/ref/nutrient-plans/gruenlilie_gardol.md` v1.0
2. Steckbrief: `/spec/ref/plant-info/chlorophytum_comosum.md`
3. Produktdaten: `/spec/ref/products/gardol_gruenpflanzenduenger.md`
4. ASPCA Animal Poison Control -- Spider Plant: https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/spider-plant
5. NC State Extension -- Chlorophytum comosum: https://plants.ces.ncsu.edu/plants/chlorophytum-comosum/
6. Wisconsin Horticulture Extension -- Spider Plant: https://hort.extension.wisc.edu/articles/spider-plant-chlorophytum-comosum/

---

**Reviewversion:** 1.0
**Erstellt:** 2026-03-01
