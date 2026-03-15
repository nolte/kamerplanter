# Agrarbiologisches Review: Nährstoffplan Monstera deliciosa / Gardol Grünpflanzendünger

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Indoor-Anbau, Zimmerpflanzen, Erdkultur
**Analysierte Dokumente:**
- `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md` (v1.1)
- `spec/ref/plant-info/monstera_deliciosa.md`
- `spec/ref/products/gardol_gruenpflanzenduenger.md` (v1.0)
- `spec/req/REQ-003_Phasensteuerung.md` (v2.3)
- `spec/req/REQ-004_Duenge-Logik.md` (v3.2)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Botanische Korrektheit | 4/5 | Phasenkonzept gut, aber `dormancy_required: false` im Steckbrief vs. DORMANCY-Phase im Plan ist ein konzeptioneller Widerspruch |
| Phasen-Mapping-Qualitaet | 4/5 | GERMINATION/SEEDLING-Mapping ist ungewoehnlich aber vertretbar; DORMANCY korrekt nach REQ-003 v2.3 |
| NPK-Konsistenz | 3/5 | Abweichung Ideal 3:1:2 zu Gardol 1,5:1:1,5 ist akzeptabel, aber im Datenmodell als Ideal-Ratio dokumentiert statt als tatsaechliche Produktratio |
| EC-Plausibilitaet | 3/5 | target_ec_ms=1.0 fuer VEGETATIVE korrekt fuer Erde, aber target_ec_ms=0.0 fuer GERMINATION und DORMANCY ist technisch pruefenswert |
| Dosierungslogik | 4/5 | 4 ml/L als Hersteller-Standarddosierung korrekt; EC-Schaetzung transparent kommuniziert |
| Gießplan-Intervalle | 3/5 | 3 Tage fuer Bewurzelung zu starr, 12 Tage fuer DORMANCY als Fixwert statt Bereich problematisch |
| Mikronährstoff-Abdeckung | 2/5 | Eisen fehlt komplett als Feldeintrag; Spurenelemente von Gardol nicht verifiziert und nicht modelliert |
| Widersprueche Steckbrief/Plan | 3/5 | top_water (Steckbrief) vs. DRENCH (Plan) ist erklaerungsbeduerftig; dormancy_required: false vs. DORMANCY-Phase |
| REQ-003 v2.3-Konformitaet | 4/5 | cycle_restart_from_sequence korrekt; is_recurring korrekt gesetzt |
| Vollstaendigkeit fuer Anfaenger | 4/5 | Salzspuelung dokumentiert; pH-Hinweis fuer Leitungswasser fehlt |

**Gesamteinschaetzung:** Der Nährstoffplan ist fuer einen Anfaenger-Referenzplan solide konzipiert und biologisch weitgehend korrekt. Die groessten Schwaechen liegen in der fehlenden Eisendosierung, im konzeptionellen Widerspruch zwischen `dormancy_required: false` im Steckbrief und der DORMANCY-Phase im Plan sowie in zu rigiden Gießintervallen fuer die Bewurzelungsphase. Die EC-Schaetzung fuer Gardol ist transparent kommuniziert, aber die Diskrepanz zwischen dem npk_ratio-Feld im Datenmodell (Idealwert 3:1:2) und dem tatsaechlich gelieferten Gardol-Verhaeltnis (1,5:1:1,5) birgt Modellierungsrisiken. Insgesamt ist der Plan fuer den vorgesehenen Zweck -- Einzelduenger-Konzept fuer Anfaenger in Erdkultur -- geeignet.

---

## Findings

### MN-001: Konzeptioneller Widerspruch -- dormancy_required: false vs. DORMANCY-Phase

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/plant-info/monstera_deliciosa.md`, Zeile 26; `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 2

**Problem:**
Der Pflanzensteckbrief deklariert `dormancy_required: false` im LifecycleConfig-Feld. Der Nährstoffplan ordnet dennoch eine DORMANCY-Phase (sequence_order 4, November-Februar, is_recurring: true) zu. Beide Dokumente wurden am selben Tag erstellt und beziehen sich aufeinander -- der Widerspruch ist nicht aufgeloest.

Aus pflanzenphysiologischer Sicht ist die Situation wie folgt zu bewerten: *Monstera deliciosa* ist eine tropische Art aus mexikanischen Regenwäldern (ca. 19. Breitengrad), wo saisonale Temperatur- und Lichtvariation minimal ist. Die Art hat evolutionär keine obligate Dormanz entwickelt. Unter Indoor-Bedingungen in Mitteleuropa erfährt die Pflanze jedoch eine tatsaechliche Wachstumsverlangsamung von November bis Februar, ausgeloest durch:
- Reduziertes Tageslicht (DLI sinkt von ~8-12 mol/m²/d im Sommer auf ~1-3 mol/m²/d im Winter am Nordfenster)
- Leicht reduzierte Temperaturen in schlecht beheizten Raeumen

Diese Verlangsamung ist keine physiologische Dormanz (keine Knospenruhe, kein Einzug des Laubs, kein Abschalten des Chlorophylls), sondern eine lichtbedingte Wachstumspause. REQ-003 v2.3 beschreibt diese korrekt: "Bildung auf saisonale Ruhephase: reduzierter Stoffwechsel, keine Duengung, verlaengertes Gießintervall."

Das `dormancy_required: false`-Feld in REQ-001 beschreibt die biologische Notwendigkeit einer Dormanz -- was bei Monstera korrekt `false` ist. Der DORMANCY-Phaseneintrag im Nährstoffplan beschreibt die kulturpraktische Anpassung an den reduzierten Licht-Metabolismus im mitteleuropaeischen Winter -- was korrekt und sinnvoll ist.

Der Widerspruch ist semantischer Natur, nicht biologischer. Das Feld `dormancy_required` im Steckbrief sollte klargestellt werden.

**Korrekturvorschlag:**
1. Im Steckbrief `dormancy_required: false` mit Kommentar versehen: `# Keine obligate Ruhephase; saisonale Wachstumsverlangsamung durch reduziertes Winterlicht (Nov-Feb) wird als DORMANCY-Phase im Nährstoffplan abgebildet`
2. Alternativ: REQ-001 ein zusaetzliches Feld `has_seasonal_growth_reduction: bool` einfuehren, das zwischen obligater Dormanz (`dormancy_required: true`) und kulturpraktischer Ruhephase (`has_seasonal_growth_reduction: true`) unterscheidet
3. Im Nährstoffplan, Abschnitt 2, klarstellen: "Die DORMANCY-Phase des Plans entspricht nicht einer biologisch obligaten Dormanz (dormancy_required: false), sondern der empfohlenen Pflegepause bei reduziertem Winterlicht."

---

### MN-002: npk_ratio im Phaseneintrag bildet Ideal, nicht Produktrealitaet ab

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitte 4.3 und 6.2 (VEGETATIVE)

**Problem:**
Das Feld `npk_ratio` im NutrientPlanPhaseEntry ist im Modell laut REQ-004 als tatsaechliches NPK-Verhaeltnis der eingesetzten Nährstoffe definiert. Im Plan ist es als Idealwert `[3.0, 1.0, 2.0]` gefuellt, obwohl Gardol Grünpflanzendünger NPK 6-4-6 liefert, was einem Verhaeltnis von 1,5:1:1,5 entspricht.

Dies erzeugt eine Diskrepanz: Das Datenmodell haelt ein Verhaeltnis (3:1:2), das der eingesetzte Duenger (1,5:1:1,5) nicht liefert. Ein Algorithmus, der `npk_ratio` aus dem Phaseneintrag ausliest (z.B. fuer Dashboard-Anzeige oder Duengerempfehlung), wuerde ein falsches Bild vermitteln.

Die Hinweisnotiz im Phaseneintrag erklaert die Abweichung, aber die strukturierten Felder sagen etwas anderes als der Hinweistext. Das ist ein Datenintegritaetsproblem.

**Agronomische Einordnung der Abweichung:**
Fuer eine Blattpflanze in Erde mit Pufferkapazitaet ist das Gardol-Verhaeltnis 1,5:1:1,5 praktisch akzeptabel:
- Das idealere N:K-Verhaeltnis von 3:2 (VEGETATIVE) foerdert kraeftiges Blattwachstum mit geringer Lagergefahr
- Gardol 6-4-6 hat einen aehnlichen N:K-Wert (6:6 = 1:1), der minimal mehr K relativ zu N liefert
- Dies foerdert Zellstabilitaet und Krankheitsresistenz leicht mehr als das 3:2-Ideal -- fuer eine Zimmerpflanze kein Nachteil
- Das erhoehte P-Verhaeltnis (4% in Gardol vs. ideal ~1/6 des N) foerdert Wurzelbildung, was fuer einen etablierten Steckling unschaedlich ist

Die Abweichung ist agronomisch vertretbar. Das Datenbankfeld ist aber falsch gefuellt.

**Korrekturvorschlag:**
Option A: `npk_ratio` auf das tatsaechliche Produktverhaeltnis setzen: `[1.5, 1.0, 1.5]` oder normiert `[6.0, 4.0, 6.0]` und das Ideal als Kommentar in `notes` dokumentieren.

Option B: Das Datenmodell um ein separates Feld `ideal_npk_ratio` erweiterern (Zielwert der Biologie) vs. `npk_ratio` (tatsaechlich gelieferter Wert durch den eingesetzten Duenger). Dies wuerde das Modell sauberer machen fuer Faelle, in denen kein Duenger das exakte Ideal trifft.

Empfehlung: Option A fuer den kurzfristigen Fix; Option B als Modell-Verbesserung in REQ-004.

---

### MN-003: Fehlendes Eisen-Feldeintrag im Datenmodell

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 4; `spec/ref/plant-info/monstera_deliciosa.md`, Abschnitt 2.3

**Problem:**
Der Pflanzensteckbrief deklariert in der Nährstofftabelle (Abschnitt 2.3) fuer die Phase Aktives Wachstum einen Eisenbedarf von `Fe (ppm): 2`. Der Nährstoffplan enthaelt in keiner Phasenoption ein `iron_ppm`-Feld oder einen Hinweis auf Eisenversorgung.

Eisen ist fuer Monstera deliciosa ein praxisrelevanter Mikronährstoff: Die Art zeigt bei Fe-Mangel intervenoese Chlorose (Vergilbung der Blattflaeche bei gruen bleibenden Blattadern), ein haeufiges Indoor-Problem, besonders bei:
- Kalkhaltigem Leitungswasser (erhoehter pH > 6,5 sperrt Fe)
- Ausgelaugtem Substrat (nach 18+ Monaten ohne Umtopfen)
- Substraten mit hohem pH-Puffer (gewisse Blumenerden enthalten Kalk)

Gardol enthalt laut Produktdaten "wahrscheinlich chelatiertes Eisen" -- aber explizit nicht verifiziert (Produktdaten-Dokument vermerkt dies mit Kommentar). Das Datenmodell in REQ-003 sieht `micro_nutrients: dict[str, int]` im nutrient_profile vor. Der Nährstoffplan nutzt dieses Feld nicht.

**Korrekturvorschlag:**
Im VEGETATIVE-Phaseneintrag erwaehnen:
- `iron_ppm: 2` als Richtwert aus Steckbrief
- Hinweis in `notes`: "Gardol enthaelt wahrscheinlich chelatiertes Eisen (nicht verifiziert). Bei Anzeichen intervenoser Chlorose (Blattadern gruen, Blattflaeche gelb): separaten Eisendünger (Fe-EDDHA Chelat, 0.1 ml/L) alle 4 Wochen zusaetzlich. pH des Substrats kontrollieren -- bei pH > 6.5 Fe-Aufnahme blockiert."

Fuer SEEDLING-Phase analog:
- `iron_ppm: 1` (Steckbrief-Wert fuer Juvenil)

Systemseitig sollte das `phase_entries`-Modell ein `micro_nutrients`-Feld erhalten, das dem `nutrient_profiles.micro_nutrients`-Feld aus REQ-003 entspricht, um Spurenelementangaben strukturiert zu erfassen statt nur in Freitextnotizen.

---

### MN-004: target_ec_ms = 0.0 fuer GERMINATION und DORMANCY -- semantisch problematisch

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitte 4.1 und 4.4 (JSON-Delivery-Channels)

**Problem:**
Beide Phasen ohne Duengung (GERMINATION, DORMANCY) setzen `target_ec_ms: 0.0`. Dies ist als Datenbankwert irrefuehrend: EC 0.0 mS/cm wuerde bedeuten, dass destilliertes Wasser oder Reinstwasser (keine Ionen) verwendet wird. Leitungswasser hat typisch 0.3-0.7 mS/cm.

Bei Erdkultur ist ein EC-Zielwert fuer das Gießwasser ohne Duenger physiologisch korrekt als "Leitungswasser-EC" zu verstehen (0.3-0.7 mS/cm je nach Haushalt), nicht als 0.0.

Fuer die Substratsteuerung (EC-Messung des Ablaufwassers oder Substrat-EC) waere 0.0 als Zielwert foermlich falsch -- das wuerde maximales Ausspuelen bedeuten.

**Hinweis zur Severity:**
Das Problem ist fuer Anfaenger-Nutzer in Erdkultur praktisch irrelevant (kein EC-Meter vorhanden). Fuer fortgeschrittene Nutzer mit EC-Meter koennten 0.0-Eintraege verwirrend sein. Fuer automatisierte Systeme (REQ-018) wuere ein EC-Zielwert 0.0 als Steuerungsparameter gefaehrlich.

**Korrekturvorschlag:**
- `target_ec_ms` auf `null` setzen fuer Phasen ohne aktive Duengung, statt 0.0
- Oder: Minimaler Richtwert fuer Leitungswasser angeben: `target_ec_ms: 0.4` mit Hinweis "Leitungswasser, keine Duengung" -- haengt von Systemdefinition ab
- In REQ-004 klarstellen, was `target_ec_ms = null` vs. `0.0` semantisch bedeutet

---

### MN-005: Gießintervall 3 Tage fuer Bewurzelung (GERMINATION) zu rigide

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitte 4.1 und 1.1

**Problem:**
Der Gießplan-Override fuer GERMINATION setzt `interval_days: 3`. Die Phase-Notes empfehlen "Substrat feucht halten, nicht nass." Diese beiden Aussagen sind teilweise im Widerspruch: Ein festes 3-Tage-Intervall kann je nach Topfgroesse, Substrat und Raumklima zu viel oder zu wenig sein.

Der Pflanzensteckbrief gibt fuer Bewurzelung als Gießintervall: "Substrat konstant feucht, nicht nass" -- bewusst ohne Zahlenwert, weil die Varianz zu hoch ist.

**Agronomische Begruendung:**
Monstera-Stecklinge in einem kleinen Anzuchttopf (8-10 cm) mit lockerer Anzuchterde und 22-26°C:
- Im Sommer (trockene Heizungsluft) kann das Substrat in 2-3 Tagen austrocknen -> 3 Tage korrekt
- Im Winter bei 18°C und 60% rH kann das Substrat 5-7 Tage feucht bleiben -> 3-Tage-Intervall fuehrt zu Ueberwaesserung und erhoehtem Trauermücken-Risiko
- Bei Bewurzelung in Wasser (was der Steckbrief erwaehnt als Alternative) entfaellt das Gießintervall komplett

Das Datenmodell erlaubt keinen Feuchtigkeitssensor-gesteuerten Modus fuer diesen Fall -- das ist eine Systemgrenze, nicht ein Dokumentenfehler. Aber das Dokument sollte den Nutzungskontext einschraenken.

**Korrekturvorschlag:**
- `interval_days: 3` beibehalten als Mindestwert, aber in `notes` erklären: "3-Tage-Intervall gilt fuer kleine Toepfe (8-10 cm) bei 22-25°C. In kuehlen oder feuchten Raeumen verlängern auf 5-7 Tage. Fingerprobe vorrangig: Obercm Substrat feucht = kein Giessen noetig. Bewurzelung in Wasser: Gießplan entfaellt."
- Systemseitig pruefen: Kann der watering_schedule_override auch einen `interval_days_range: [3, 7]` erlauben statt eines Fixwerts?

---

### MN-006: Gießintervall 12 Tage fuer DORMANCY als Fixwert zu kurz

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 4.4

**Problem:**
Das `watering_schedule_override` fuer DORMANCY setzt `interval_days: 12`. Die `notes` des Phaseneintrags empfehlen "Gießintervall auf 10-14 Tage verlaengern". Es gibt eine Inkonsistenz zwischen dem Fixwert 12 (Systemfeld) und dem empfohlenen Bereich 10-14 Tage (Textfeld).

12 Tage als Fixwert liegt in der Mitte des empfohlenen Bereichs -- das ist pragmatisch akzeptabel. Das eigentliche Problem ist, dass 12 Tage fuer DORMANCY unter Heizungsbedinungen (trockene Luft, Substrat trocknet schneller) zu selten sein kann, während bei kuehlen Winterstandorten (Treppenhaus, Wintergarten, 15-18°C) 12 Tage zu haeufig waere.

Pflanzensteckbrief gibt fuer Ruheperiode: "Gießintervall: 10-14 Tage" -- der Plan setzt genau die Mitte, was aber das dynamische Element der Substratfeuchte-Kontrolle nicht abbildet.

**Zusaetzlicher Aspekt: Monatliche Substratspuelung**
Der Plan empfiehlt in `notes` DORMANCY: "Alle 4 Wochen Substrat mit klarem Wasser durchspuelen". Dies ist eine agronomisch korrekte Empfehlung (Salzakkumulation aus Sommerdüngung), aber das Spuelen wird nicht als separates Event im Gießplan-System abgebildet. In einem 12-Tage-Intervall ergibt sich automatisch eine Spuelung ca. alle 24-36 Tage -- das ist nicht planmaessig gesteuert, sondern Zufall.

**Korrekturvorschlag:**
- 12 Tage als Standard-Intervall beibehalten, aber in notes praezisieren: "12 Tage bei normaler Raumtemperatur (18-22°C). Bei kuehleren Winterstandorten (15-18°C) auf 14 Tage verlaengern. Fingerprobe vorrangig: Obere 4-5 cm Substrat trocken = giessen."
- Substratspuelung als eigenstaendige Aufgabe im Task-System (REQ-006) planen: 1x pro Monat November-Februar "Substrat mit 2x Topfvolumen klarem Wasser durchspuelen".

---

### MN-007: GERMINATION-Phase -- Gießvolumen im JSON (0.15 L) vs. Prosa-Hinweis inkonsistent

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 6.2 (GERMINATION JSON) vs. Abschnitt 3.1 (DRENCH-Parameter)

**Problem:**
Im JSON der GERMINATION-Phase ist `volume_per_feeding_liters: 0.15` eingetragen. In Abschnitt 3.1 steht fuer den DRENCH-Hauptkanal `volume_per_feeding_liters: 0.5`, mit dem Hinweis "fuer mittelgrosse Monstera (Topf 18-24 cm)".

0.15 L fuer Bewurzelung (Topf ca. 8-10 cm) ist agronomisch korrekt und sinnvoll -- ein kleiner Steckling in einem kleinen Topf braucht kein halbes Liter. Die Inkonsistenz ist hier keine fachliche Fehler, sondern eine fehlende Erklaerung, die beim Nutzer Verwirrung ausloesen kann ("Warum anders als normal?").

Der Steckbrief gibt fuer Bewurzelung: "Giessmenge: 50-100 ml/Pflanze" -- das entspricht 0.05-0.10 L. Der Plan setzt 0.15 L, was am oberen Rand liegt und nur bei groesseren Anzuchtoepfen (12 cm) angemessen ist.

**Korrekturvorschlag:**
- `volume_per_feeding_liters` fuer GERMINATION auf `0.10` reduzieren (passt besser zur Steckbrief-Angabe 50-100 ml)
- Oder Bereich dokumentieren: "0.05-0.15 L je nach Topfgroesse (8-12 cm)"
- Im Abschnitt 3.1 erlaeutern, dass das angegebene Standardvolumen (0.5 L) fuer etablierte Pflanzen gilt und fuer Stecklinge deutlich reduziert wird

---

### MN-008: Calcium/Magnesium VEGETATIVE -- Verhaeltnis und Herkunft pruefen

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 4.3; `spec/ref/plant-info/monstera_deliciosa.md`, Abschnitt 2.3

**Problem:**
Der Plan setzt Ca 80 ppm / Mg 40 ppm fuer VEGETATIVE, was einem Ca:Mg-Verhaeltnis von 2:1 entspricht. Das ist agronomisch korrekt -- das klassische Ca:Mg-Verhaeltnis liegt bei 2:1 bis 3:1, wobei ein ueberhoehter Ca-Anteil die Mg-Aufnahme antagonistisch hemmt (Ionenkonkurrenz) und ein zu niedriger Ca-Anteil bei gleichzeitig hohem Mg zu Magnesiose-Symptomen fuehrt (braune Blattspitzen, Chlorose zwischen den Blattnerven).

Jedoch: Der eingesetzte Duenger (Gardol NPK 6-4-6) enthaelt nach aktueller Etikettendeklaration **kein deklariertes Calcium und kein deklariertes Magnesium** als Hauptbestandteil. Leitungswasser liefert je nach Haertegrad Ca und Mg (mittelhartes deutsches Leitungswasser typisch 80-120 mg/L Ca, 10-20 mg/L Mg = 80-120 ppm Ca, 10-20 ppm Mg).

Die im Plan angegebenen Ca 80 ppm und Mg 40 ppm kommen also bei Einsatz von Leitungswasser aus dem Wasser selbst, nicht aus dem Duenger. Das ist eine wichtige Information, die im Plan fehlt.

**Bei weichemWasser oder Osmosewasser** (was der Plan mit `water_mix_ratio_ro_percent: null` implizit ausschliesst, aber nicht explizit kommuniziert) wuerden Ca und Mg in der Giesslosung auf nahezu 0 sinken -- bei ausschliesslicher Gardol-Verwendung ohne CalMag-Ergaenzung.

**Agronomischer Hintergrund:**
Monstera deliciosa ist relativ Ca-tolerant (kalkhaltiges Leitungswasser ist unproblematisch). Mg-Mangel zeigt sich spaeter als Ca-Mangel und wird durch das Leitungswasser in den meisten deutschen Haushalten ausreichend gedeckt. Ein separates CalMag-Supplement ist bei Leitungswasser typisch nicht noetig -- das ist fachlich korrekt so im Plan dargestellt.

**Korrekturvorschlag:**
- In `notes` zur VEGETATIVE-Phase ergaenzen: "Ca 80 ppm und Mg 40 ppm werden bei mittelhartem Leitungswasser (dt. Durchschnitt ~100 ppm Ca, 15 ppm Mg) automatisch erreichtt oder ueberschritten. Gardol liefert kein Ca oder Mg. Bei Verwendung von weichem Wasser oder Osmosewasser ist ein CalMag-Supplement (z.B. 0.5 ml/L) erforderlich."
- In Abschnitt 1.1 (Metadata) `water_mix_ratio_ro_percent: null` mit Erklaerung versehen: "null = 100% Leitungswasser vorausgesetzt. Bei RO/Regenwasser Ca/Mg-Ergaenzung notwendig."

---

### MN-009: SEEDLING-Phase -- Duengefrequenz 14-taetig vs. Gießplan 7 Tage

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitte 4.2 und 1.1

**Problem:**
Der Plan-Level-Gießplan setzt `interval_days: 7`. Der SEEDLING-Phaseneintrag schreibt "Halbe Dosis alle 14 Tage." Es gibt keinen `watering_schedule_override` fuer SEEDLING. Das bedeutet: Das System wird die Pflanze alle 7 Tage giessen -- aber nur jedes zweite Mal (alle 14 Tage) mit Duenger.

Fuer die Bewässerungssteuerung ist das korrekt: Jedes zweite Gießen = klares Wasser, jedes zweite = Duengeloesung. Das Datenmodell sieht dies vermutlich ueber die `fertilizer_dosages`-Steuerung ab, nicht ueber den Gießplan selbst.

Die Frage ist: Wie kodiert das Kamerplanter-Datenmodell "jedes zweite Giessen duengen"? Wenn der Delivery Channel fuer SEEDLING auf `optional: false` gesetzt ist und der Gießplan 7-taetig laeuft, wird bei jeder Bewaesserung Duenger dosiert -- also woechentlich, nicht 14-taeglich.

**Loesungsvorschlag:**
Das ist ein Datenmodell-Frage, nicht nur ein Dokumentfehler:
- Option A: `interval_days: 14` als `watering_schedule_override` fuer SEEDLING setzen (nur alle 14 Tage giessen + duengen) -- aber dann wird die Pflanze in der Juvenilphase zu selten bewaessert
- Option B: Den Gießplan auf 7 Tage belassen und `fertilizer_dosages.optional: true` fuer SEEDLING setzen, mit Hinweis, dass nur jedes zweite Giessen Duenger enthaelt
- Option C: REQ-004 um ein Feld `fertilizing_every_n_waterings: int` erweiterern (jedes n-te Giessen duengen)

Empfehlung: Option A fuer diesen spezifischen Plan, da Monstera-Jungpflanzen in Erde bei 14-taegigem Giessen gut funktionieren. In der `notes` erklaeren: "Gießplan auf 14 Tage fuer SEEDLING. Zwischen den Giessterminen Substrat-Feuchte pruefen -- bei trockener Heizungsluft gelegentlich mit klarem Wasser befeuchten (nicht im Plan)."

---

### MN-010: pH-Zielwert 6.0 -- Substrat-pH vs. Giessloesungs-pH nicht unterschieden

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, alle Delivery Channels

**Problem:**
Alle Delivery Channels setzen `target_ph: 6.0`. Fuer Erdkultur mit Leitungswasser ist die Angabe eines Giessloesungs-pH von 6.0 nicht praxisrelevant:
- Deutsches Leitungswasser hat typisch pH 7.0-7.8 (gesetzliches Ziel pH 6.5-9.5)
- Der Nutzer hat in der Regel keine Moeglichkeit, den pH des Leitungswassers auf 6.0 zu senken, ohne Saeuren einzusetzen -- was fuer Anfaenger-Nutzer nicht vorgesehen ist
- Blumenerde hat einen eigenen pH-Puffer (meist pH 6.0-7.0 kommerziell), der kurzfristige pH-Abweichungen des Gießwassers ausgleicht

Ein `target_ph: 6.0` ist technisch korrekt als Substrat-pH-Zielwert fuer Monstera, aber als Gießwasser-pH-Vorgabe fuer Leitungswasser-Nutzer nicht umsetzbar und irrefuehrend.

**Vergleich Steckbrief:** Abschnitt 2.3 gibt pH-Bereich "5.5-6.5" fuer alle Phasen -- als Substrat-pH, nicht als Gießwasser-pH. Dies ist korrekt.

**Korrekturvorschlag:**
- `target_ph: 6.0` mit Kommentar erlaeutern: "pH 6.0 bezieht sich auf das Substrat-pH-Optimum, nicht auf den Gießwasser-pH. Leitungswasser muss fuer Erdkultur nicht pH-korrigiert werden -- die Erde puffert. pH-Messung nur bei Verdacht auf pH-Problem relevant."
- Oder: `target_ph: null` fuer Erdkultur-Delivery-Channels, mit Hinweis, dass pH-Steuerung nur fuer Hydroponik relevant ist
- In REQ-004 semantisch klaeren: Was bedeutet `target_ph` im Delivery Channel -- Gießwasser-pH oder Substrat-pH?

---

### MN-011: Widerspruch Giessmethode top_water (Steckbrief) vs. DRENCH (Plan)

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/plant-info/monstera_deliciosa.md`, Abschnitt 4.1 (`watering_method: top_water`); `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 3 (`application_method: DRENCH`)

**Problem:**
Der Pflanzensteckbrief definiert das Care-Profil mit `watering_method: top_water` und erklaert die Methode ausfuehrlich (von oben langsam und gleichmaessig giessen, bis Wasser aus Abzugsloechern laeuft). Der Nährstoffplan nutzt durchgehend `DRENCH` als `application_method`.

Aus agronomischer Sicht sind `top_water` und `DRENCH` im Kontext Zimmerpflanze / Gießkanne faktisch identisch. Beide beschreiben das Giessen von oben, bis das Substrat durchtraenkt ist und Drainage-Wasser ablauft. Der Unterschied liegt im Systemvokabular:
- `top_water` = Pflegeprofil-Begriff (REQ-022): Beschreibt die Gießmethode aus Nutzerperspektive
- `DRENCH` = Applikationsmethode (REQ-004): Beschreibt die Duengerausbringung -- Duenger wird ins Giesswasser gemischt und als Substrat-Durchtränkung appliziert (im Gegensatz zu FOLIAR = Blattspruehen, BOTTOM_WATER = Untersetzer, DRIP = Troepfbewässerung)

Die beiden Terme beschreiben nicht denselben Sachverhalt, aber sie schliessen einander nicht aus: `top_water` (Methode) mit `DRENCH` (Duengerapplikation) ist vollstaendig konsistent -- man giesst von oben, und dabei wird Duenger mitgegeben.

Es handelt sich um eine scheinbare Inkonsistenz, die aus unterschiedlichen Klassifikationssystemen entsteht. Fuer den Nutzer kann es dennoch verwirrend sein.

**Korrekturvorschlag:**
- In den Delivery-Channel-Notes ergaenzen: "DRENCH = Duenger ins Giesswasser mischen und von oben giessen (entspricht der top_water-Methode aus dem Pflegeprofil). Nicht mit Troepfbewässerung oder Blattsprühen verwechseln."
- Systemseitig pruefen, ob eine Mapping-Tabelle oder Synonym-Hinweis zwischen `watering_method`-Werten (REQ-022) und `application_method`-Werten (REQ-004) in der UI hilfreich waere.

---

### MN-012: Jahresplan September -- Unstimmigkeit mit Phaseneintrag

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 5 (Jahresplan) vs. Abschnitt 3.4 (Gardol Produktdaten)

**Problem:**
Das Gardol-Produktdokument beschreibt September als "Letzte Vollduengung" (September = volle Dosis), der Uebergang zur halben Dosis beginnt laut Produktbeschreibung im Oktober. Der Monstera-Nährstoffplan uebernimmt dies korrekt: September volle Dosis, Oktober halbe Dosis.

Im Pflanzensteckbrief (Abschnitt 3.2) wird Mai-August als Hauptwachstum mit voller Dosis und September-Oktober als Wachstumsende mit halber Dosis (3-5 ml/L COMPO) angegeben. Das ist eine leichte Abweichung vom Nährstoffplan (September = volle Dosis vs. halbe Dosis).

Dies liegt am unterschiedlichen Referenzprodukt: COMPO 7-3-6 (7 ml/L = volle Dosis) vs. Gardol 6-4-6 (4 ml/L = volle Dosis). Der Steckbrief verwendet COMPO als Beispielprodukt, der Nährstoffplan Gardol. Das ist keine fachliche Inkonsistenz, aber es kann Nutzer verwirren.

**Agronomischer Kommentar:**
September in Mitteleuropa hat noch substantielles Wachstum bei Monstera (DLI ~8-12 mol/m²/d, Temperatur 18-24°C). Eine volle Duengung bis Ende September ist agronomisch sinnvoll. Der Uebergang zur halben Dosis im Oktober ist ebenfalls korrekt, da DLI dann auf ~5-8 mol/m²/d faellt.

**Korrekturvorschlag:** Kein fachlicher Korrekturbedarf. Hinweis in Abschnitt 5 ergaenzen: "September weicht vom Steckbrief-Beispielplan ab (dort halbe Dosis ab September) -- der Unterschied ist produktspezifisch und beides ist agronomisch korrekt."

---

### MN-013: Salzakkumulations-Risiko -- Spuelungshinweis unzureichend kommuniziert

**Schweregrad:** Wichtig

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitte 4.4 (DORMANCY-Notes) und 3.4 (Gardol-Produktdaten)

**Problem:**
Der Plan empfiehlt in DORMANCY-Notes: "Alle 4 Wochen Substrat mit klarem Wasser durchspuelen." Das Gardol-Produktdokument empfiehlt "Alle 2-3 Monate" (Abschnitt 8, Pro-Tipps). Das sind unterschiedliche Frequenzen fuer das gleiche Problem.

Fuer die Aktivwachstumsphase (April-September, 6 Monate woechentlicher Vollduengung) fehlt ein Spuelungshinweis komplett. Bei woechentlicher Duengung mit 4 ml/L (0.24 mS/cm EC-Beitrag) und 0.5 L Gießmenge pro Duengung wird eine relevante Salzmenge eingetragen. Bei einem 2L-Topf (Substratvolumen ca. 1.5L) akkumulieren nach 6 Monaten (24 Duengungen) theoretisch: 24 x 0.5 L x 4 ml/L = 48 ml Gardol-Konzentrat insgesamt -- das entspricht je nach Substratpuffer einer nennenswerten Salzlast.

Symptome von Salzakkumulation bei Monstera in Erde (relevant fuer Nutzer-Erkennung):
- Weisse Krusten auf der Erdoberflaeche (Salz-Ausblueungen)
- Braune Blattspitzen (Osmotischer Stress durch hohe Substrat-EC)
- Generell verlangsamtes Wachstum trotz korrekter Duengung

**Korrekturvorschlag:**
- In VEGETATIVE-Phase-Notes ergaenzen: "Alle 6-8 Wochen (ca. alle 2 Monate) eine Gießung ohne Duenger vergroessern: 1.5-2x das normale Gießvolumen mit klarem Wasser, um Salzablagerungen auszuwaschen. Drainagewasser pruefen -- wenn weiss/trueb: Spuelung notwendig."
- DORMANCY-Spuelungshinweis von "alle 4 Wochen" auf "einmalig zu Beginn der Ruheperiode (November) + bei Bedarf" praezisieren. Im Winter wird wenig gedüngt, eine monatliche Spuelung bei klarem Wasser ist uebertrieben und foerdert Trauermücken.
- Einheitliche Spuelungs-Empfehlung im Jahresplan als eigene Zeile eintragen (z.B. April, Juli, November).

---

### MN-014: Phasen-Mapping GERMINATION fuer Stecklinge -- semantische Diskrepanz

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md`, Abschnitt 2 (Phasen-Mapping-Tabelle)

**Problem:**
Das Phasen-Mapping verwendet GERMINATION fuer "Bewurzelung" (Steckling/Teilung). Biologisch ist Keimung (Germination) der Prozess der Samenentwicklung -- von der Quellung des Samens ueber Radikeln-Austritt bis zum ersten echten Laubblatt. Ein Steckling keimt nicht, er bewurzelt sich (Adventivwurzelbildung).

REQ-003 v2.3 beschreibt in der Phasensequenz fuer "Perenniale Zimmerpflanze (Indoor)" explizit: "Bewurzelung -> Juvenil -> [Aktives Wachstum -> Dormanz] ↻" -- das Wort "Bewurzelung" wird als eigener Begriff genutzt, gemappt auf GERMINATION (weil kein separates "PROPAGATION"-Enum-Wert vorhanden ist).

Das Mapping ist pragmatisch korrekt (GERMINATION ist die einzige verfuegbare Phase, die "Anfangsphase ohne Wachstum/Duengung" semantisch abdeckt), aber biologisch ungenau. Ein Nutzer, der Monstera aus Samen anzieht (was selten, aber moeglich ist), wuerde diese Phase korrekt als Keimung erleben -- ein Nutzer mit Steckling hingegen erlebt Bewurzelung.

**Systemseitig:**
Ob das GERMINATION-Enum fuer nicht-generative Vermehrung (Stecklinge, Teilung) genutzt werden kann, ist eine REQ-003-Frage. Das Mapping-Dokument erlaeutert es transparent ("Steckling/Teilung etabliert Wurzeln"), sodass der Irrtum fuer Nutzer gering ist.

**Korrekturvorschlag (langfristig):**
REQ-003 und das PhaseName-Enum um `propagation` (Vegetative Vermehrung) oder `rooting` (Bewurzelung) erweiterern, separate von `germination` (Samenkeimung). Das ermoeglicht eine saubere Unterscheidung:
- `germination`: Samen → Keimling
- `propagation` / `rooting`: Steckling / Teilung → bewurzelte Jungpflanze

Kurzfristig: Mapping beibehalten, in Abschnitt 2 explizit hinzufuegen: "GERMINATION wird hier als Platzhalter fuer die Bewurzelungsphase von Stecklingen genutzt, da kein separates PROPAGATION-Enum existiert. Bei generativer Vermehrung (Samen) entfaellt diese Phase."

---

### MN-015: Toxizitaetshinweis fehlt im Duengekontext

**Schweregrad:** Hinweis

**Dokument:** `spec/ref/nutrient-plans/monstera_deliciosa_gardol.md` (komplett)

**Problem:**
Monstera deliciosa ist laut Steckbrief toxisch fuer Katzen, Hunde und Kinder (Calciumoxalat-Raphiden, Schweregrad moderate). Der Nährstoffplan enthaelt keinen Hinweis auf Toxizitaet im Duengekontext. Dies ist fuer Endbenutzer relevant in folgenden Situationen:
- Drainage-Wasser aus der Gießschale kann von Haustieren getrunken werden
- Stecklinge in Wasser auf dem Fensterbrett sind fuer Katzen zuganglich
- Beim Umtopfen (Abschnitt 4.4 erwaehnt keine Schutzhinweise fuer den Umgang)

Das Gardol-Produkt selbst ist ebenfalls ein mineralischer Duenger, der bei versehentlichem Kontakt durch Haustiere (Trinken aus der Gießkanne) leichte Vergiftungserscheinungen verursachen kann.

**Korrekturvorschlag:**
- In Abschnitt 1 (Metadata-Beschreibung) oder in einem Sicherheitshinweis ergaenzen: "Sicherheitshinweis: Monstera deliciosa ist giftig fuer Katzen, Hunde und Kinder (Calciumoxalat-Raphiden). Drainage-Wasser und Gießloesungen von Haustieren fernhalten. Beim Umtopfen Handschuhe tragen (Kontaktallergen-Risiko durch Pflanzensaft)."
- Systemseitig: Die Toxizitaetsdaten aus dem Steckbrief sollten im Nährstoffplan-Template als Warning-Flag mit angezeigt werden (z.B. als Link auf `species.toxicity`).

---

## Parameter-Uebersicht

| Parameter | Im Plan vorhanden | Plausibilitaet | Anmerkung |
|-----------|------------------|----------------|-----------|
| NPK-Ratio (Phase) | Ja (Idealwert) | Praezisierungsbeduerftig | Idealwert statt Produktrealitaet; siehe MN-002 |
| EC-Zielwert (mS/cm) | Ja | Korrekt fuer Erde | 0.6 (Juvenil), 1.0 (Vegetativ); 0.0 fuer dungefreie Phasen pruefenswert (MN-004) |
| pH-Zielwert | Ja | Erklaerungsbeduerftig | 6.0 als Substrat-pH-Ziel korrekt, aber als Gießwasser-pH nicht umsetzbar (MN-010) |
| Ca-Bedarf (ppm) | Ja | Korrekt | 40 (Juvenil), 80 (Vegetativ); Herkunft aus Leitungswasser, nicht Duenger (MN-008) |
| Mg-Bedarf (ppm) | Ja | Korrekt | 20 (Juvenil), 40 (Vegetativ); Ca:Mg 2:1 korrekt |
| Fe-Bedarf (ppm) | Nein | Fehlend | Steckbrief: 2 ppm (Vegetativ). Chelatiertes Fe in Gardol unbestaetigt (MN-003) |
| Sonstige Mikros | Nein | Fehlend | Mn, Zn, Cu, B, Mo nicht modelliert; fuer Anfaengerplan akzeptabel |
| Gießintervall | Ja (variierend) | Praezisierungsbeduerftig | 3 Tage (Bewurzelung) zu rigide (MN-005); 12 Tage (Dormancy) als Fixwert unkritisch (MN-006) |
| Gießmenge | Ja (variierend) | Leicht ueberschaetzt | GERMINATION 0.15 L > Steckbrief 0.05-0.1 L (MN-007) |
| Dosierung ml/L | Ja | Korrekt | 4 ml/L = Hersteller-Standarddosierung fuer Zimmerpflanzen |
| EC-Beitrag Duenger | Ja (Schaetzung) | Transparent kommuniziert | ~0.06 mS/cm pro ml/L als Schaetzung; fehlende Herstellerangabe dokumentiert |
| Salzspuelung | Teils | Unvollstaendig | DORMANCY erwaehnt, Aktivwachstum vergessen (MN-013) |
| Toxizitaetswarnung | Nein | Fehlend | Monstera ist moderat toxisch; Hinweis im Duengekontext fehlt (MN-015) |

---

## Biologische Korrektheit der Phasen-Mappings: Beurteilung

### GERMINATION fuer Bewurzelung
Biologisch ungenau (Keimung ist generativer Vorgang; Stecklinge bewurzeln sich, keimen nicht), aber pragmatisch vertretbar im System, solange kein `propagation`-Enum existiert. Transparenz durch Dokumentation gegeben. Langfristig: eigenes Enum einfuehren (MN-014).

### SEEDLING fuer Juvenilphase
Biologisch korrekt im weiteren Sinne: Der Jugendzustand einer Kletterpflanze (noch keine adulte Blattform, keine Fenestration) entspricht dem Saemlingsstadium in der Ressourcenanforderung (reduzierte Duengung, geringere Lichtanforderung). Das Mapping ist vertretbar.

### VEGETATIVE fuer Aktives Wachstum (Maerz-Oktober)
Biologisch korrekt. Monstera ist in dieser Phase vegetativ (Blattbildung, keine Bluete). VEGETATIVE als Dauerzustand fuer eine nie bluehende Zimmerpflanze ist das sinnvollste verfuegbare Mapping.

### DORMANCY fuer Ruhephase (November-Februar)
Biologisch ungenau (keine obligate Dormanz, sondern lichtbedingte Wachstumsverlangsamung -- siehe MN-001), aber kulturpraktisch korrekt und in REQ-003 v2.3 explizit so vorgesehen. Das Mapping ist systemkonform und sinnvoll.

**Gesamtbewertung Phasen-Mapping:** Fuer das vorliegende Datenmodell optimal genutzt. Die biologischen Ungenauigkeiten sind systembedingt (Enum-Beschraenkungen) und durch Kommentare transparent gemacht. Keine Aenderung am Mapping notwendig.

---

### REQ-003 v2.3-Konformitaet: Beurteilung

Die Implementierung des Nährstoffplans ist weitgehend konform mit REQ-003 v2.3:

| REQ-003 Anforderung | Im Plan umgesetzt | Beurteilung |
|--------------------|------------------|-------------|
| `is_recurring: true` fuer zyklische Phasen | Ja (VEGETATIVE, DORMANCY) | Korrekt |
| `cycle_restart_from_sequence: 3` (ab VEGETATIVE) | Ja | Korrekt -- Erstphasen (GERMINATION, SEEDLING) nicht wiederholt |
| DORMANCY als saisonale Zimmerpflanzen-Ruhephase | Ja | REQ-003 v2.3 konform; semantische Frage (MN-001) geklaert |
| `watering_schedule_override` pro Phase | Ja (GERMINATION, DORMANCY) | Korrekt; SEEDLING fehlt Override (MN-009) |
| Keine FLUSHING-Phase fuer Zimmerpflanze | Ja (explizit dokumentiert) | Korrekt nach REQ-003 v2.3 |
| Keine HARVEST-Phase fuer Zierpflanze | Ja | Korrekt |
| `is_terminal: false` fuer alle Phasen | Implizit (keine Angabe) | Sollte fuer DORMANCY explizit `is_terminal: false` setzen |

---

## Zusammenfassung der Empfehlungen

### Sofortiger Korrekturbedarf (Datenintegritaet)

1. **MN-002:** `npk_ratio` fuer VEGETATIVE-Phase von `[3.0, 1.0, 2.0]` (Ideal) auf `[1.5, 1.0, 1.5]` oder `[6.0, 4.0, 6.0]` (Produktrealitaet) korrigieren.

2. **MN-005:** `interval_days: 3` fuer GERMINATION um Kontext-Hinweis erweiterern; Volumen GERMINATION von 0.15 L auf 0.10 L reduzieren (MN-007).

3. **MN-009:** Gießplan-Konflikt SEEDLING (7 Tage Giessen vs. 14 Tage Duengen) aufloesen -- entweder `watering_schedule_override` mit 14 Tagen setzen oder Datenmodell um `fertilizing_every_n_waterings` erweiterern.

### Wichtige Ergaenzungen

4. **MN-003:** Eisenbedarf (`iron_ppm`) in SEEDLING (1 ppm) und VEGETATIVE (2 ppm) als Feldeintrag erwaehnen; Hinweis auf potenzielle Fe-Mangel-Symptome und CalMag-Bedarf bei Weichwaasser ergaenzen.

5. **MN-008:** `notes` VEGETATIVE um Herkunft Ca/Mg (Leitungswasser, nicht Gardol) und CalMag-Bedarf bei Weichwaasser ergaenzen.

6. **MN-013:** Salzspuelungshinweis auf Aktivwachstumsphase ausweiterern; DORMANCY-Spuelungsfrequenz praezisieren.

### Systemseitige Modell-Verbesserungen (mittelfristig)

7. **MN-001:** REQ-001 Feld `has_seasonal_growth_reduction: bool` einfuehren fuer Unterscheidung obligate Dormanz vs. kulturpraktische Ruheperiode.

8. **MN-002:** REQ-004 Modell um `ideal_npk_ratio` (biologischer Zielwert) vs. `npk_ratio` (tatsaechlich gelieferter Wert) erweiterern.

9. **MN-004:** Semantik von `target_ec_ms: null` vs. `0.0` in REQ-004 klaeren.

10. **MN-014:** PhaseName-Enum in REQ-003 um `propagation` oder `rooting` erweiterern fuer vegetative Vermehrung.

---

## Glossar (kontextspezifisch)

- **Adventivwurzeln:** Wurzeln, die nicht aus dem normalen Wurzelsystem entstehen, sondern an Stängeln oder Blättern -- typisch bei Stecklingsvermehrung und Luftwurzeln von Monstera
- **Ca:Mg-Antagonismus:** Konkurenz zwischen Calcium- und Magnesium-Ionen an denselben Wurzel-Aufnahmetransportern; bei Ca:Mg-Verhaeltnis >3:1 wird Mg-Aufnahme gehemmt
- **Chelatierung:** Komplexbildung von Metallionen (z.B. Fe, Mn, Zn) mit organischen Molekuelen (Chelate), die die Ionenbindung an Ton- oder Kalk-Partikel verhindert und damit die Verfuegbarkeit im Boden erhoehlt
- **DLI (Daily Light Integral):** Tagessumme der photosynthetisch nutzbaren Strahlung in mol/m²/Tag; Nordfenster Deutschland Winter ca. 1-3 mol/m²/d, Sommer 5-12 mol/m²/d
- **Dormanz, obligate:** Genetisch programmierte Ruhephase mit Aufloesung biochemischer Aktivitaet, Einzug des Laubs oder Knospenruhe -- bei Monstera deliciosa nicht vorhanden
- **Dormanz, fakultative / kulturpraktische:** Durch Umweltfaktoren (Licht, Temperatur) induzierte Wachstumspause ohne genetisches Programm -- bei Monstera deliciosa im mitteleuropaeischen Winter
- **EC (Electrical Conductivity):** Elektrische Leitfaehigkeit einer Loessung in mS/cm; Maß fuer die Gesamtionenlast; fuer Leitungswasser 0.3-0.7 mS/cm, fuer Erde mit Duengung 0.8-1.4 mS/cm optimal
- **Fenestration:** Lochbildung (Fenestrierung) in Monsterra-Blaettern; tritt erst im Adultstadium auf (ab ca. 4-6 Blaettern der Normalgroe); junge Blaetter sind ungeteilt
- **Intervenoese Chlorose:** Vergilbung des Blattgewebes zwischen den Blattnerven bei noch gruenen Nerven -- typisches Eisenmangel-Symptom; kann auch auf Manganmangel hinweisen
- **NPK:** Hauptnaehrstoff-Dreierpack Stickstoff (N), Phosphor (P), Kalium (K); Prozentwerte auf Duengeretiketten geben N als Gesamtstickstoff, P als P2O5, K als K2O an
- **Osmotischer Stress:** Schaedigung durch hohe Salzkonzentration im Substrat; hohe Substrat-EC zieht Wasser aus den Wurzelzellen (inverser Osmose), fuehrt zu Welke und braunen Blattspitzen
- **VPD (Vapor Pressure Deficit):** Dampfdruckdefizit in kPa; Maß fuer den "Durst" der Luft; bei 22°C und 60% rH = ca. 1.05 kPa -- im optimalen Bereich fuer Monstera VEGETATIVE
