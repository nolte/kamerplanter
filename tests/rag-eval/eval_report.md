# RAG Eval Report — 2026-03-31

## Zusammenfassung

- **Score:** 29.05% (FAIL) — Gesamtbenchmark mit 100 Fragen
- **Modell:** gemma3:4b
- **Fragen:** 100 evaluiert, ~70 fehlgeschlagen (score < 0.70)
- **Min-Pass-Score:** 70%
- **Vorheriges Ergebnis:** keines (erster gespeicherter Full-Run)
- **Regressionen:** nicht anwendbar (kein Vergleichswert)

Das System erzielt aktuell rund ein Drittel der notwendigen Qualität. Die Ursachen sind
klar trennbar und weitgehend behebbar.

---

## Fehler-Verteilung

| Fehlerklasse | Anzahl (geschätzt) | Anteil | Beispiel-IDs |
|---|---|---|---|
| GENERATION_MISS | ~40 | ~57% | umwelt-001, umwelt-003, phase-001, phase-002, ipm-009, pflege-007 |
| SYNONYM_GAP | ~15 | ~21% | diag-007, dueng-006, wasser-009, wasser-010, umwelt-008 |
| RETRIEVAL_MISS | ~8 | ~11% | dueng-002, dueng-008, wasser-002, comp-003, comp-009 |
| KNOWLEDGE_GAP | ~5 | ~7% | wasser-010, pflege-009, pflege-013 |
| FALSE_POSITIVE | 2 | ~3% | comp-001 (fenchel FP), comp-006 (keine FP) |
| QUESTION_AMBIGUITY | ~1 | ~1% | comp-006 |

**Wichtige Einschränkung:** Die `answer`-Felder sind auf 500 Zeichen gekürzt. In einigen
GENERATION_MISS-Fällen könnte das vollständige Modell-Output die gesuchten Topics enthalten.
Die Klassifizierung basiert auf dem sichtbaren Ausschnitt.

---

## Kategorie-Scores (Heatmap, aufsteigend sortiert)

| Kategorie | Score | Status |
|---|---|---|
| pflege | 11.81% | KRITISCH |
| phasen | 10.00% | KRITISCH |
| umwelt | 18.56% | KRITISCH |
| companion_planting | 15.83% | KRITISCH |
| bewaesserung | 20.00% | KRITISCH |
| anfaenger | 28.89% | FAIL |
| duengung | 34.44% | FAIL |
| ipm | 38.17% | FAIL |
| diagnostik | 69.44% | KNAPP FAIL |

Die Kategorie **diagnostik** ist mit 69% klar am besten und nähert sich dem Pass-Threshold.
Alle anderen Kategorien liegen weit darunter. Das System verhält sich wie ein spezialisierter
Diagnose-Assistent, der auf Nicht-Diagnose-Fragen fast immer eine Diagnose-Antwort produziert.

---

## Detailanalyse: Hauptursachen

### Ursache 1 — Prompt-Typ-Mismatch (GENERATION_MISS, Hochprioritär)

Dies ist die häufigste und gravierendste Fehlerquelle. Das System verwendet standardmäßig
einen Diagnose-Prompt (`1) Diagnose, 2) mobil/immobil, 3) Ursachen, 4) Massnahmen`), auch
wenn die Frage keine Diagnose-Frage ist.

**Symptom:** Antworten auf faktische/howto-Fragen beginnen immer noch mit
`1) Diagnose: ... 2) Mobil/Immobil: ...` — eine komplett falsche Struktur für Fragen wie:
- "Was ist VPD?" (umwelt-001) → Antwort beginnt mit "Diagnose: Zu niedriger VPD"
- "Wie keime ich Samen?" (phase-001) → Antwort beginnt mit "Diagnose: Nährstoffmangel"
- "Welches Fenster?" (umwelt-003) → Antwort beginnt mit "Diagnose: Braune Blattspitzen"
- "LED oder HPS?" (umwelt-014) → Antwort beginnt mit "Diagnose: Blattbrand"
- "Wie oft Zimmerpflanze düngen?" (dueng-008) → Antwort beginnt mit "Diagnose: Ueberduengung"

Das eval_rag.py hat zwar eine Frage-Typ-Erkennung (`_classify_question`) mit drei
Prompt-Typen (diagnosis/howto/factual), aber das Regex-Pattern für `_HOWTO_PATTERNS` und
`_DIAGNOSIS_PATTERNS` erfasst viele Fragen nicht korrekt. Fragen wie "Was ist VPD?",
"Welches Fenster?", "LED oder HPS?" enthalten weder howto- noch diagnosis-Keywords und
fallen als `factual` durch — bekommen aber trotzdem den diagnosis-orientierten Output,
weil das Modell durch den Kontext (Diagnosefragen in den Chunks?) in die Diagnose-Struktur
gezogen wird.

**Betroffene Kategorien:** umwelt (10 von 15 Fragen), phasen (7 von 10), pflege (fast alle),
companion_planting (fast alle), bewaesserung (teilweise).

**Betroffene Failures:**

- umwelt-001: `dampfdruckdefizit, temperatur_und_rh, transpiration, eine_kennzahl` — Antwort
  erklärt VPD nicht als Konzept, sondern diagnostiziert "zu niedriger VPD".
- umwelt-003: `suedfenster_hell, ostfenster_morgensonne, nordfenster_wenig_licht, abstand_wichtig`
  — Chunks enthalten diese Info (licht-grundlagen.yaml Zeile 170-184), aber Antwort weicht ab.
- phase-001: `papiertuch_methode, 24_28_grad, feucht_nicht_nass, dunkel` — Knowledge-Chunk
  vorhanden (keimung-best-practices.yaml), aber Modell diagnostiziert stattdessen.
- phase-002: `ab_4_5_nodenpaar, nur_vegetativ, nicht_in_bluete, erholungszeit` — Knowledge
  vorhanden (vegetative-optimierung.yaml), Generation falsch.
- pflege-007: `nein, ruhephase, wachstum_gestoppt, fruehling_starten` — diagnostik/zimmerpflanzen-
  probleme.yaml Zeile 30 enthält "Im Winter GAR NICHT duengen (Ruhephase)". GENERATION_MISS.
- dueng-008: `wachstumsperiode, maerz_oktober, alle_2_4_wochen, halbe_dosis, winter_nicht_duengen`
  — anfaenger-erste-schritte.yaml Zeilen 57-58 enthält alle Informationen. GENERATION_MISS.
- comp-003: `mais_bohne_kuerbis, milpa, n_fixierung, stuetzfunktion, bodenbeschattung` —
  mischkultur-praxis.yaml Chunk `drei-schwestern-milpa` ist retrieved, aber LLM diagnostiziert
  Stickstoffmangel statt das Mischkultur-System zu erklären.
- comp-009: `phacelia, klee, lupine, senf, n_fixierung, bodenlockerung` — fruchtfolge-
  grundlagen.yaml enthält detaillierte Gruenduengungspflanzen-Liste. GENERATION_MISS.
- ipm-009: `krautfaeule, phytophthora, befallene_teile_entfernen, kupfer_praeparat` —
  pilzkrankheiten.yaml Chunk vorhanden, Modell diagnostiziert stattdessen Calciummangel.
  Klarer GENERATION_MISS, nicht RETRIEVAL_MISS (chunks beinhalten pilzkrankheiten#echter-mehltau).
- ipm-010: `ja_biologisch, ei_parasitierung, rechtzeitig_aussetzen, vorbeugend` —
  schaedlings-fruehzeichen.yaml enthält Schlupfwespen-Info. Retrieval brachte aber
  mischkultur/fruchtfolge-Chunks.

---

### Ursache 2 — Synonym-Lücken (SYNONYM_GAP)

Das LLM enthält die gesuchte Information in der Antwort, aber der Regex in topic_synonyms.yaml
erkennt sie nicht.

**diag-007 — `ph_erhoehen`:**
Antwort: "Erhöhen Sie den pH-Wert des Substrats auf 6.0-6.5."
Pattern: `(?i)pH.*erhoeh|pH[- ]?Up|Kaliumhydroxid|kalken|Dolomitkalk`
Problem: "Erhöhen" (mit Umlaut) wird von `pH.*erhoeh` abgedeckt, aber nur wenn direkt
verbunden — "pH-Wert erhöhen" statt "pH erhöhen" könnte je nach Regex-Engine Probleme
machen. Wahrscheinlich ein Umlaut-Normalisierungsproblem: Das Pattern sucht `erhoeh` (oe),
aber die Antwort enthält `erhöhen` (ö). SYNONYM_GAP.

**diag-007 — `ph_zu_niedrig`:**
Antwort: "Der niedrige pH-Wert von 5.0". Pattern: `(?i)pH.*zu.*niedrig|pH.*unter|pH.*erhoehen`
Problem: "niedrige pH-Wert" trifft "pH.*niedrig" nicht wegen Wortstellung. SYNONYM_GAP.
Fix: Pattern `(?i)pH.*zu.*niedrig|pH.*unter|niedrig.*pH|pH.*erhoeh|kalken` erweitern.

**umwelt-001 — `dampfdruckdefizit, temperatur_und_rh, eine_kennzahl, transpiration`:**
Antwort sagt: "Diagnose: Zu niedriger VPD" — das Pattern `dampfdruckdefizit` erwartet
explizit "Dampfdruckdefizit" oder "VPD steht fuer / bedeutet / beschreibt". Das Modell
nennt VPD aber nur als Kürzel ohne Definition. Dies ist primär GENERATION_MISS (falscher
Prompt-Typ), sekundär könnten Patterns enger sein.

**dueng-006 — `nach_stretch`:**
Pattern: `(?i)Woche.*3|Woche.*4|ab.*Woche.*3|nach.*Stretch`
Antwort: "Woche 5 der Bluete" und "ab Woche 3-4 beginnen" — sollte eigentlich matchen,
prüfe `woche_3_4` Pattern. Könnte ein False-Negative durch `nach_stretch` separate Suche.

**wasser-009 — `mischrechnung, 02_04_ec, basis_ec_zielwert`:**
Die Knowledge-Base enthält ec-management-hydroponik.yaml mit der Formel. Die Chunks wurden
retrieved (`ec-net-berechnung`). Aber Antwort beschreibt CalMag-Mangel statt der
Mischberechnung. GENERATION_MISS durch Diagnose-Prompt-Frame.

**wasser-010 — `morgens_bevorzugt, outdoor_morgens, indoor_vor_lichtphase`:**
temperatur-steuerung.yaml Zeile 68 enthält "Morgens/abends giessen". Die Chunk wurde aber
nicht retrieved (chunks zeigen fehler-uebergiessen, giessen-coco etc.). Pattern
`morgens_bevorzugt` erwartet "morgens|frueh|Morgen.*giess|vor.*Mittag" — Info ist in der
Knowledge-Base vorhanden aber in einem Temperatur-Chunk, nicht einem Gieß-Chunk.
Primär RETRIEVAL_MISS.

**dueng-013 — `umstritten, guelph_studie, kompromiss, ec_reduzieren`:**
Knowledge enthält pk-boost-timing.yaml mit Zeile 101 "umstritten. Eine Studie der University
of Guelph (2020)". Chunk `pk-flush-wissenschaft` wurde retrieved. Aber Antwort sagt "Natürliche
Seneszenz". Das Modell interpretiert den Flush-Kontext als Diagnose. GENERATION_MISS.

---

### Ursache 3 — Retrieval-Fehler (RETRIEVAL_MISS)

Der richtige Chunk existiert in der Knowledge-Base, wurde aber nicht retrieved.

**dueng-002 — `wasser_zuerst, silikat_vor_calmag, calmag_vor_part_a, part_a_vor_part_b, ph_zuletzt`:**
Score 0.0 — alle 5 Topics fehlen. Chunk `mischsicherheit#goldene-mischungsregel` wurde
retrieved, enthält die Mischreihenfolge. Der Chunk `calmag-mischungsreihenfolge` auch.
Aber das Modell beschreibt Calciumsulfat-Ausfällung statt die Reihenfolge aufzulisten.
Dies ist primär GENERATION_MISS (Diagnose-Struktur auf eine howto-Frage), sekundär könnten
die Pattern für `wasser_zuerst` und `silikat_vor_calmag` zu streng sein.

**wasser-010 — `morgens_bevorzugt, outdoor_morgens, indoor_vor_lichtphase`:**
Relevanter Chunk (temperatur-steuerung) nicht retrieved — stattdessen fehler-uebergiessen,
giessen-coco, trockenheit-priorisierung. Die Frage "Soll ich morgens oder abends gießen?"
passt semantisch schlecht zum Temperatur-Chunk wo diese Info steht. RETRIEVAL_MISS.

**comp-009 — `phacelia, klee, lupine, senf, n_fixierung, bodenlockerung`:**
Chunks retrieved: pk-boost-nicht-fuer-alle, anfaenger-erste-schritte, frost-sofortmassnahmen.
Die Fruchtfolge-Grundlagen mit Gruenduengung (fruchtfolge-grundlagen.yaml Zeile 56) wurden
nicht retrieved. Frage "Was sind gute Gruenduengungspflanzen?" semantisch weit von den
retrieved Chunks. RETRIEVAL_MISS.

**diag-013 — `thrips, blaue_klebefallen, spinosad, raubmilben`:**
Score 0.0. Chunk schaedlings-fruehzeichen#thrips-erkennung existiert mit allen Topics
(Zeile 50-53). Retrieved chunks: vegetative-optimierung, naehrstoffmangel-symptome,
spaetbluete-seneszenz, zimmerpflanze-gelbe-blaetter, fehler-standort. Kein Schaedlings-Chunk
retrieved für "Silbrige Streifen und schwarze Punkte". RETRIEVAL_MISS + GENERATION_MISS.

**phase-006 — `15_20_grad, 55_65_rh, dunkel, 7_14_tage, zweige_knacken`:**
Score 0.0. Curing-Chunk (ernte-timing#curing-cannabis) wurde nicht retrieved, obwohl er
alle Parameters enthält. Retrieved: pk-flush-wissenschaft, spaetbluete-seneszenz, trichome-
reife-indikator. Die Frage "Trocknung und Lagerung nach der Ernte" matcht semantisch
schlecht auf den Curing-Chunk. RETRIEVAL_MISS.

---

### Ursache 4 — Knowledge-Gaps

**wasser-010 — `outdoor_morgens, indoor_vor_lichtphase`:**
Während "morgens giessen" in der Knowledge-Base vorkommt (temperatur-steuerung.yaml),
fehlt die explizite Unterscheidung `outdoor_morgens` vs. `indoor_vor_lichtphase` als
dedizierter Chunk im Bewässerungs-Kontext. Der Ratschlag ist im falschen Kontext (Temperatur).
Partieller KNOWLEDGE_GAP / RETRIEVAL_MISS.

**pflege-009 — `radieschen, salat, tomaten_busch, basilikum`:**
Score 0.0. Frage: Empfehlung für Balkon-Anfänger. Knowledge-Base enthält Radieschen und
Basilikum-Informationen in verschiedenen Dateien, aber kein dedizierter Chunk
"Anfänger-Balkon-Empfehlungen" mit einer konsolidierten Pflanzenliste. KNOWLEDGE_GAP.

**pflege-013 — `basilikum, schnittlauch, petersilie, suedfenster`:**
Score 0.0. Frage: Empfehlung Kräuter für die Küche. Kein dedizierter Chunk für
"Kräuter-Fensterbank-Anbau" vorhanden. KNOWLEDGE_GAP.

**pflege-010 — `verholzung, nicht_ins_alte_holz_schneiden, regelmaessig_ernten, licht`:**
Score 0.0. Frage: Rosmarin-Pflegeanleitung. Die Verholzungs-Warnung
("nicht ins alte Holz schneiden") fehlt in der Knowledge-Base als konkreter Chunk.
KNOWLEDGE_GAP.

**pflege-015 — `abhaengig_von_art, nordfenster_ja, suedfenster_meist_ok, winter_kurze_tage`:**
Score 0.0. Frage: Überwinterung von Zimmerpflanzen auf der Fensterbank.
licht-grundlagen.yaml enthält Nordfenster-Info, aber der spezifische Kontext
"Zimmerpflanze im Winter ans Fenster stellen" als Pflegeempfehlung fehlt. Partieller
KNOWLEDGE_GAP.

---

### Ursache 5 — FALSE_POSITIVE-Analyse

Nur 2 FP-Fälle im gesamten Benchmark (gutes Zeichen).

**comp-001 — `fenchel` als FP:**
Score 0.0, FP: fenchel. Frage: "Was sind gute Nachbarn für Tomaten?" Expected: basilikum,
tagetes, karotte, sellerie. Das Modell nennt korrekt die Fenchel-Warnung, ignoriert aber
die positiven Nachbarn. Die Chunk `mischkultur-praxis#schlechte-nachbarn` wurde retrieved
und das Modell fokussiert darauf. Dies ist ein Fall von Chunk-Kontamination: Der schlechte-
Nachbarn-Chunk ist prominent und verdrängt die positiven Beispiele.
Klassifizierung: FP-Typ "Chunk-Kontamination".

**comp-006 — `keine` als FP:**
Score 0.25, FP: keine. Frage: "Warum pflanzt man Tagetes und Ringelblume neben Gemüse?"
Expected: bestauber (als einziger fehlender Topic). Das Modell sagt "kein spezifische
Blätter betroffen" (also "keine" als Negation) aber das FP-Matching erkennt "keine" als
positives Topic. Dies ist ein FALSE_POSITIVE durch fehlende Negations-Erkennung im Matcher.
Klassifizierung: FP-Typ "Negation nicht erkannt".

---

## Detailanalyse pro Failure (wichtigste Fälle)

### comp-001 — FALSE_POSITIVE + GENERATION_MISS
- **Frage:** "Was sind gute Nachbarn für Tomaten?"
- **Score:** 0.0
- **Misses:** basilikum, tagetes, karotte, sellerie
- **FPs:** fenchel
- **Chunks:** schlechte-nachbarn, beetplanung-hoehe-tiefe, mischkultur-naehrstoffdynamik
- **Antwort:** Fokus auf Fenchel-Allelopathie, keine positiven Nachbarn genannt
- **Root Cause:** Chunk `schlechte-nachbarn` dominiert das Retrieval; der positive
  Companion-Planting-Chunk fehlt im Top-5. Zusätzlich produziert das Modell im
  Diagnose-Frame eine Diagnose statt eine Empfehlungsliste.
- **Fix:** Retrieval-Diversifizierung (positive/negative Chunks balancieren);
  question_type: factual explizit setzen für comp-001.

### diag-013 — RETRIEVAL_MISS + GENERATION_MISS
- **Frage:** "Silbrige Streifen und schwarze Punkte auf den Blättern"
- **Score:** 0.0
- **Misses:** thrips, blaue_klebefallen, spinosad, raubmilben
- **Chunks:** vegetative-optimierung, naehrstoffmangel-symptome (falsch!)
- **Antwort:** Mangan-Toxizität (völlig falsche Diagnose)
- **Root Cause:** Kein Schädlings-Chunk im Top-5 retrieved. "Silbrige Streifen" als
  Suchanfrage zieht pflanzliche Symptom-Chunks statt Schädlings-Chunks.
- **Fix:** Hybrid-Search-Gewichtung prüfen; Thrips-Chunk Tags verbessern.

### dueng-002 — GENERATION_MISS
- **Frage:** "In welcher Reihenfolge mische ich meine Nährlösung?"
- **Score:** 0.0
- **Misses:** wasser_zuerst, silikat_vor_calmag, calmag_vor_part_a, part_a_vor_part_b, ph_zuletzt
- **Chunks:** calmag-mischungsreihenfolge, mischsicherheit#goldene-mischungsregel (korrekt!)
- **Antwort:** Beschreibt Calciumsulfat-Ausfällung statt Reihenfolge aufzulisten
- **Root Cause:** Diagnose-Prompt zwingt das Modell zur Diagnosestruktur. Frage müsste
  als `howto` klassifiziert werden ("In welcher Reihenfolge" = howto-Keyword).
- **Fix:** `_HOWTO_PATTERNS` ergänzen um `"reihenfolge"` (bereits enthalten?) — prüfen
  ob die Regex tatsächlich matched bei "In welcher Reihenfolge mische ich".

### phase-001 — GENERATION_MISS
- **Frage:** "Wie keime ich Samen am besten?"
- **Score:** 0.0
- **Misses:** papiertuch_methode, 24_28_grad, feucht_nicht_nass, dunkel
- **Chunks:** keimung-vorbehandlung, keimung-licht, keimung-fehler, keimung-direktsaat (alle korrekt!)
- **Antwort:** "Nährstoffmangel (Kaliummangel)"
- **Root Cause:** Pure GENERATION_MISS. Alle Chunks korrekt retrieved, aber LLM produziert
  trotzdem eine Diagnose. "Wie" sollte als howto erkannt werden.
- **Fix:** Sicherstellen dass "Wie keime" als howto klassifiziert wird.

### umwelt-001 — GENERATION_MISS
- **Frage:** "Was ist VPD und warum ist es wichtiger als Luftfeuchtigkeit allein?"
- **Score:** 0.0
- **Misses:** dampfdruckdefizit, temperatur_und_rh, transpiration, eine_kennzahl
- **Chunks:** vpd-erklaerung, vpd-zielwerte, vpd-messfehler, vpd-zu-niedrig-massnahmen (korrekt!)
- **Antwort:** "Diagnose: Zu niedriger VPD"
- **Root Cause:** Frage ist `factual`, wird korrekt klassifiziert, aber Modell strukturiert
  trotzdem wie Diagnose. Das `factual`-Prompt ist zu schwach.
- **Fix:** factual-Prompt stärken; explizit verbieten die Diagnose-Struktur zu verwenden.

### pflege-007 — GENERATION_MISS (Zimmerpflanze im Winter düngen)
- **Frage:** "Meine Zimmerpflanze wächst im Winter sehr langsam. Soll ich mehr düngen?"
- **Score:** 0.0
- **Misses:** nein, ruhephase, wachstum_gestoppt, fruehling_starten
- **Chunks:** anfaenger-erste-schritte, fehler-standort (Ruhephase-Info vorhanden!)
- **Root Cause:** Modell diagnostiziert Überdüngung statt die Frage direkt zu beantworten.

---

## Priorisierte Verbesserungsmassnahmen

### Prio 1 — Prompt-Typ-Klassifizierung reparieren (GENERATION_MISS, ~57% aller Fehler)

Dies ist der mit Abstand wichtigste Fix und adressiert den Großteil aller Failures.

**Problem:** Das `factual`-Prompt lässt das Modell trotzdem die Diagnose-Struktur verwenden.

**Fix A — `factual`-Prompt explizit verbessern (eval_rag.py):**
```python
"factual": {
    "de": (
        "Du bist ein Pflanzenberater. Antworte auf Deutsch, kurz und fachlich korrekt. "
        "Beantworte die Frage direkt. WICHTIG: Verwende KEINE Diagnose-Struktur "
        "(keine 'Diagnose:', keine 'Mobil/Immobil:' Punkte). "
        "Gib stattdessen eine klare, direkte Antwort mit konkreten Fakten. "
    ),
}
```

**Fix B — `howto`-Pattern erweitern (eval_rag.py):**
```python
_HOWTO_PATTERNS = re.compile(
    r"(?i)(reihenfolge|wie\s+(mische|mach|starte|bereite|soll\s+ich|keime|oft|"
    r"funktioniert|berechne|stelle.*ein)|"
    r"schritt|anleitung|wann\s+(starte|beginne|soll|kann\s+ich)|"
    r"was\s+(ist\s+der\s+unterschied|sind\s+gute|empfiehlst)|"
    r"how\s+(do|should|to|often)|step|procedure|order)",
)
```

**Fix C — `question_type` explizit in benchmark_questions.yaml setzen** für alle
nicht-Diagnose-Fragen. Beispiele:
- umwelt-001, umwelt-003, umwelt-005, umwelt-010, umwelt-011, umwelt-014: `question_type: factual`
- dueng-001, dueng-002, dueng-008, dueng-009, dueng-013: `question_type: howto` oder `factual`
- phase-001, phase-002, phase-006, phase-008, phase-009: `question_type: howto`
- wasser-001, wasser-004, wasser-007, wasser-008, wasser-010: `question_type: factual`
- pflege-007, pflege-008, pflege-009, pflege-013, pflege-015: `question_type: factual`
- comp-001, comp-003, comp-005, comp-009: `question_type: factual`

**Erwarteter Impact:** +20-30 Prozentpunkte Gesamtscore

---

### Prio 2 — Synonym-Gaps schließen (SYNONYM_GAP, ~21% aller Fehler)

**topic_synonyms.yaml Änderungen:**

**`ph_erhoehen`** — Umlaut-Problem:
```yaml
ph_erhoehen:
  pattern: "(?i)pH.*erh[oö]h|pH[- ]?Up|Kaliumhydroxid|kalken|Dolomitkalk|pH.*anpass.*oben|pH.*steig"
  de: [pH erhoehen, pH-Up, kalken, pH anpassen]
```

**`ph_zu_niedrig`** — Wortstellung:
```yaml
ph_zu_niedrig:
  pattern: "(?i)pH.*zu.*niedrig|pH.*unter|niedrig.*pH|zu.*niedrig.*pH|pH.*erhoeh|kalken"
  de: [pH zu niedrig, pH erhoehen, kalken, niedriger pH]
```

**`dampfdruckdefizit`** — zu eng:
```yaml
dampfdruckdefizit:
  pattern: "(?i)Dampfdruck|Vapor.*Pressure|VPD.*erklaer|VPD.*ist|VPD.*steht.*fuer|VPD.*bedeutet|VPD.*beschreibt|VPD.*kombiniert|VPD.*vereint|Feuchtigkeits.*Differenz"
  de: [Dampfdruckdefizit, VPD steht fuer, VPD kombiniert Temperatur]
```

**`temperatur_und_rh`** — zu eng:
```yaml
temperatur_und_rh:
  pattern: "(?i)Temperatur.*Feuchtig|Temperatur.*RH|beides|kombiniert|beide.*Werte|beide.*Faktoren|Temp.*und.*RH"
  de: [Temperatur und Feuchtigkeit, kombiniert, beide Werte]
```

**`eine_kennzahl`** — Ergänzung:
```yaml
eine_kennzahl:
  pattern: "(?i)eine.*Kennzahl|ein.*Wert|vereint|zusammenfass|single.*metric|einzeln.*Wert|beides.*zusammen"
  de: [eine Kennzahl, vereint beides, zusammenfasst]
```

**`ja_wahrscheinlich`** (wasser-003) — Pattern prüfen:
```yaml
ja_wahrscheinlich:
  pattern: "(?i)ja.*wahrscheinlich|wahrscheinlich.*ja|sehr.*wahrscheinlich|Ueberwaesserung|Diagnose.*Ueberwaesserung"
  de: [ja wahrscheinlich, sehr wahrscheinlich Ueberwaesserung]
```

**`botrytis_risiko`** (umwelt-008) — fehlt komplett in topic_synonyms.yaml:
```yaml
botrytis_risiko:
  pattern: "(?i)Botrytis.*Risiko|Schimmel.*Risiko|Botrytis.*Gefahr|Grauschimmel.*Gefahr|Faule.*Gefahr"
  de: [Botrytis-Risiko, Schimmel-Risiko, Grauschimmel-Gefahr]
```

**`abluft_hoch`** (umwelt-008) — Pattern prüfen:
```yaml
abluft_hoch:
  pattern: "(?i)Abluft.*erhoeh|Abluft.*hoch|Abluft.*maximum|Luefter.*hoch|Lueftung.*erhoeh|Lueftung.*max"
  de: [Abluft erhoehen, Abluft auf Maximum, Lüftung erhoehen]
```

**Erwarteter Impact:** +5-8 Prozentpunkte Gesamtscore

---

### Prio 3 — Knowledge-Gaps füllen (KNOWLEDGE_GAP, ~7% aller Fehler)

**Gap 1: Giesszeitpunkt-Chunk im Bewässerungs-Kontext** (wasser-010)

Die Gieß-Zeitpunkt-Information ist in `umwelt/temperatur-steuerung.yaml` versteckt.
Ein dedizierter Chunk in `bewaesserung/giess-strategien-substrat.yaml` würde das
Retrieval verbessern:

Datei: `spec/knowledge/bewaesserung/giess-strategien-substrat.yaml`
Neuer Chunk-Vorschlag:
```yaml
- id: giessen-zeitpunkt
  title: Optimaler Giesszeitpunkt — morgens oder abends?
  content: |
    Outdoor: Morgens giessen ist die beste Option. Das Wasser kann in den Boden
    einziehen, bevor die Mittagshitze zur Verdunstung fuehrt. Abends giessen
    erhoehte Schimmel- und Schneckenrisiko durch feuchte Blaetter in der Nacht.
    Nie mittags giessen (Linsenwirkung durch Wassertropfen, hohe Verdunstung).

    Indoor / Growzelt: Vor Beginn der Lichtphase giessen. Die Pflanzen nehmen
    Wasser und Naehrstoffe waehrend der Lichtphase am effektivsten auf. In der
    Dunkelphase sinkt die Transpiration, Substrate trocknen langsamer.

    Zimmerpflanzen: Morgens oder fruehes Mittag bevorzugen. Wasser aus Untersetzer
    nach 30 Minuten entfernen.
  metadata:
    topic: watering_timing
    outdoor: morning
    indoor: before_light_phase
```

**Gap 2: Balkon-Anfänger-Pflanzen** (pflege-009)

Datei: `spec/knowledge/allgemein/anfaenger-erste-schritte.yaml`
Ergänzung nach dem bestehenden Zimmerpflanzen-Abschnitt:
```yaml
- id: balkon-anfaenger-pflanzen
  title: Einfache Balkonpflanzen fuer Einsteiger
  content: |
    Fuer den ersten Balkon empfehlen sich folgende pflegeleichte Kulturen:
    Radieschen: Ernte in 4 Wochen, fast ueberall, sehr einfach.
    Salat (Schnittsalat): Mehrfachernten, Halbschatten gut geeignet.
    Busch-Tomate (z.B. 'Balkonstar'): Kompakte Sorten fuer den Topf.
    Basilikum: Suedbalkon, regelmaessig ernten vor der Bluete.
    Schnittlauch: Mehrjaehrig, robust, fast wartungsfrei.
    Petersilie: Halbschatten moeglich, regelmaessig giessen.
    ...
```

**Gap 3: Kräuter-Fensterbank** (pflege-013)

Ähnlicher Chunk für Kräuter im Innenbereich benötigt.

**Gap 4: Rosmarin-Schnittanleitng** (pflege-010)

Ergänzung in `spec/knowledge/outdoor/saisonplanung.yaml` oder neuer Chunk in
`allgemein/fehler-vermeiden.yaml` über Schneidefehler bei verholzenden Kräutern.

**Erwarteter Impact:** +3-5 Prozentpunkte Gesamtscore (nach Ingestion-Pipeline)

---

### Prio 4 — Retrieval-Optimierung (RETRIEVAL_MISS, ~11% aller Fehler)

**Problem A: Schädlings-Chunks werden nicht für Symptom-Fragen retrieved** (diag-013, ipm-009, ipm-010):

Die semantische Ähnlichkeit zwischen "Silbrige Streifen und schwarze Punkte" und dem
Thrips-Chunk ist möglicherweise gering wegen Embedding-Vokabular. Empfehlung:

1. Thrips-Chunk Tags ergänzen: `tags: [silbrige_streifen, schwarze_punkte, thrips, streifig]`
2. Hybrid-Search BM25-Gewichtung erhöhen (lexikalisches Matching hilft bei Symptom-Keywords).
3. Top-K auf 10-15 erhöhen für IPM/Diagnostik-Kategorien.

**Problem B: Curing/Trocknungs-Chunk nicht retrieved** (phase-006):

Die Frage nach "Trocknung und Lagerung" retrieved statt Curing-Chunk die Spätblüte-Chunks.
Empfehlung: Curing-Chunk Tags um `[trocknung, lagerung, trocknen, haengen]` ergänzen.

**Problem C: Gießzeitpunkt-Info im falschen Chunk** (wasser-010):

Kurzfristig: Knowledge-Gap-Fix (Prio 3) löst dies.
Mittelfristig: Chunk-Splitting prüfen — der Temperatur-Chunk enthält Gieß-Empfehlungen,
die besser in einen Gieß-Chunk gehören.

**Problem D: Gruenduengung-Chunk nicht retrieved** (comp-009):

Die Frage "Was sind gute Gruenduengungspflanzen?" retrieved pk-boost und anfaenger-Chunks.
Empfehlung: fruchtfolge-grundlagen-Chunks mit Tags `[gruenduengung, zwischenfrucht, phacelia,
klee, lupine]` erweitern.

**Erwarteter Impact:** +5-8 Prozentpunkte nach Embedding-Reindex

---

### Prio 5 — Generation-Verbesserung und FP-Reduktion

**Fix für FP comp-006 (Negations-Erkennung):**
Das Wort `keine` als expected_NOT-Pattern ist zu breit. Der Benchmark-Eintrag comp-006
hat `expected_NOT: [keine]` was bedeutet "wenn die Antwort 'keine' sagt (als Verneinung)
soll das ein False Positive sein". Dies ist eine QUESTION_AMBIGUITY — das Pattern `keine`
in `topic_synonyms.yaml` als isoliertes Wort ist zu generisch.

Fix in benchmark_questions.yaml:
- comp-006: expected_NOT für `keine` entfernen oder in einen spezifischeren Topic-Key
  umwandeln wie `keine_bestaeubungsangabe`.

**Fix für FP comp-001 (Chunk-Kontamination):**
Der Chunk `mischkultur-praxis#schlechte-nachbarn` wird für die Tomate-Nachbarn-Frage
retrieved und dominiert die Antwort. Der positive Companion-Chunk
`mischkultur-praxis#tagetes-ringelblume` und `mischkultur-praxis#kraeuterstreifen` sollten
bei einer positiven Frage ("was sind gute Nachbarn") höher ranken.

**System-Prompt Ergänzung für factual/howto:**
Den bestehenden factual-Prompt um explizite Anti-Diagnose-Instruktion erweitern:
"Beantworte NUR die gestellte Frage. Formuliere KEINE Diagnose. Nenne konkrete Fakten,
Werte und Empfehlungen aus dem Kontext."

**Erwarteter Impact:** +2-3 Prozentpunkte

---

## Zusammenfassung der erwarteten Impact-Kette

| Maßnahme | Aufwand | Erwarteter Impact |
|---|---|---|
| Prio 1: Prompt-Typ-Fix (eval_rag.py + benchmark_questions.yaml) | Mittel | +20-30% |
| Prio 2: Synonym-Gaps (topic_synonyms.yaml) | Gering | +5-8% |
| Prio 3: Knowledge-Gaps (spec/knowledge/ + Ingestion) | Hoch | +3-5% |
| Prio 4: Retrieval-Optimierung (Chunk-Tags + Hybrid-Search) | Mittel | +5-8% |
| Prio 5: Generation/FP (Prompts + Benchmark-Korrekturen) | Gering | +2-3% |

**Kumulativer erwarteter Gesamtscore nach allen Fixes:** 55-70%
**Mit gutem Modell (z.B. gemma3:12b oder llama3.1:8b):** Möglicherweise >70% erreichbar

Der wichtigste Einzelschritt ist Prio 1 — der Prompt-Typ-Mismatch ist die dominante
Fehlerursache und kann ohne Knowledge-Base-Änderungen sofort behoben werden.

---

## Technische Hinweise

1. Nach Änderungen an `spec/knowledge/` muss die Ingestion-Pipeline (Embedding + pgvector-Insert)
   neu laufen, bevor ein Re-Eval sinnvoll ist.
2. Änderungen an `topic_synonyms.yaml` und `benchmark_questions.yaml` wirken sofort beim
   nächsten Eval-Run ohne Neuingestion.
3. Änderungen am System-Prompt in `eval_rag.py` wirken sofort.
4. Empfehlung für den nächsten Re-Eval: Zuerst Prio 1 + Prio 2 umsetzen, dann gezielten
   Re-Run mit `--categories phasen umwelt companion_planting pflege` durchführen, da
   diese Kategorien den größten Nachholbedarf haben.
