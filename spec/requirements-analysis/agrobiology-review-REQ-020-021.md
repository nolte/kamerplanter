# Agrarbiologisches Anforderungsreview v2 -- REQ-020, REQ-021, UI-NFR-011

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Re-Review nach Korrekturen: Onboarding-Wizard, Starter-Kits, Fachbegriff-Erklaerungen, UI-Erfahrungsstufen
**Analysierte Dokumente:**
- `spec/req/REQ-020_Onboarding-Wizard.md` (v1.0, korrigiert)
- `spec/req/REQ-021_UI-Erfahrungsstufen.md` (v1.0, korrigiert)
- `spec/ui-nfr/UI-NFR-011_Fachbegriff-Erklaerungen.md` (v1.0, korrigiert)
- `src/backend/app/migrations/seed_data.py` (Seed-Daten-Referenz)
- `spec/req/REQ-001_Stammdatenverwaltung.md` (Taxonomie-Kontext)
- `spec/req/REQ-003_Phasensteuerung.md` (Phasen-Kontext)
- `spec/req/REQ-013_Pflanzdurchlauf.md` (PlantingRun-Kontext)
- `spec/req/REQ-019_Substratverwaltung.md` (Substrat-Kontext)
- `test-reports/agrobiology-review-REQ020-021-NFR011.md` (v1-Report -- Referenz)

---

## Gesamtbewertung

| Dimension | v1 | v2 | Kommentar |
|-----------|-----|-----|-----------|
| Fachliche Korrektheit | 4/5 | 5/5 | Alle identifizierten Fehler korrekt behoben |
| Starter-Kit-Qualitaet | 3/5 | 4/5 | Deutlich verbessert (Cultivars, Toxizitaet, Chili-Aufteilung) |
| Glossar-Korrektheit | 4/5 | 5/5 | Alle Glossar-Eintraege biologisch korrekt und differenziert |
| Feld-Sichtbarkeitslogik | 4/5 | 5/5 | Species-Seed-Daten-Lookup statt statischer Defaults |
| Default-Werte-Qualitaet | 3/5 | 5/5 | Dynamische Defaults aus Species-Daten eliminieren Pauschalfehler |
| Glossar-Vollstaendigkeit | 3/5 | 5/5 | Von 30 auf 38 Pflicht-Begriffe erweitert, alle Einsteiger-Luecken geschlossen |
| Praktische Umsetzbarkeit | 4/5 | 4/5 | Unveraendert -- Seed-Daten-Erweiterung bleibt umfangreiche Arbeit |

**Gesamteinschaetzung:**
Die Korrekturen wurden gruendlich und fachlich korrekt umgesetzt. Alle fuenf fachlich falschen Befunde (F-001 bis F-005) sind behoben, ohne dass dabei neue biologische Fehler eingefuehrt wurden. Die Glossar-Erweiterung auf 38 Begriffe schliesst die kritischsten Luecken fuer Einsteiger. Die Umstellung von statischen Defaults auf Species-Seed-Daten-Lookup (P-001/P-002/P-003) ist die qualitativ wichtigste Verbesserung, da sie systemische Folgefehler in GDD-Berechnung und Fruchtfolge-Empfehlungen verhindert. Es verbleiben einige untergeordnete Hinweise zur weiteren Verfeinerung, aber keine fachlich falschen Anforderungen mehr.

---

## Korrektur-Verifikation: Fachlich Falsch (v1)

### F-001 [BEHOBEN]: *Sansevieria trifasciata* -> *Dracaena trifasciata*

**v1-Befund:** Taxonomisch veralteter Name im Zimmerpflanzen-Kit.
**Korrektur in REQ-020, Zeile 251:**
```
*Dracaena trifasciata* (syn. *Sansevieria trifasciata*)
```
**Bewertung:** Korrekt umgesetzt. Der aktuell gueltige Name nach POWO wird verwendet, das gaengige Synonym fuer den Wiedererkennungswert behalten. Keine neuen Probleme.

---

### F-002 [BEHOBEN]: Photoperiodismus -- ununterbrochene Dunkelperiode

**v1-Befund:** "brauchen >12h Dunkelheit" fehlte der entscheidende Hinweis auf die Unterbrechungsempfindlichkeit.
**Korrektur in UI-NFR-011, Zeile 205:**
```
"Kurztagspflanzen (z.B. Cannabis, Weihnachtsstern) brauchen eine ununterbrochene
Dunkelperiode ueber einer kritischen Schwelle (oft 12-14h). Selbst kurze
Lichtunterbrechungen in der Nacht koennen die Bluete verhindern."
```
**Bewertung:** Korrekt umgesetzt. Das Wort "ununterbrochen" und der Hinweis auf Lichtunterbrechungen sind die biologisch entscheidenden Ergaenzungen. Der beginnerTip erwaehnt korrekt "Kein Licht waehrend der Dunkelphase!" -- praxisnah und praezise. Keine neuen Probleme.

---

### F-003 [KEIN HANDLUNGSBEDARF IN DIESEN DOCS]: Basilikum-Photoperiodismus

**v1-Befund:** REQ-001 Testszenario beschreibt Basilikum falsch als Kurztagspflanze.
**Status:** Dieser Befund betrifft REQ-001, nicht die hier geprueften Dokumente. Die Seed-Daten (`seed_data.py`, Zeile 169) setzen bereits korrekt `PhotoperiodType.DAY_NEUTRAL` fuer alle Species. Fuer REQ-020 ist dies kein Problem, da die Starter-Kits die Seed-Daten referenzieren.

---

### F-004 [BEHOBEN]: VPD-Bereich artabhaengig gemacht

**v1-Befund:** "0,8-1,2 kPa ideal" als Universalwert.
**Korrektur in UI-NFR-011, Zeile 147:**
```
"Optimale Werte sind artabhaengig: Tropische Pflanzen moegen 0,4-0,8 kPa,
Nutzpflanzen im Wachstum 0,8-1,2 kPa, Kakteen tolerieren ueber 1,5 kPa."
```
**typicalRange:** `"0,4-1,6 kPa (artabhaengig)"`

**Bewertung:** Korrekt umgesetzt. Die Differenzierung nach Pflanzengruppen ist biologisch korrekt und deckt die Bandbreite der Starter-Kit-Species ab (tropische Zimmerpflanzen bis Sukkulenten). Der beginnerTip "Im Zimmer normalerweise kein Problem. Nur bei geschlossenen Growzelten relevant." ist eine pragmatisch korrekte Vereinfachung. Keine neuen Probleme.

---

### F-005 [BEHOBEN]: Vernalisation -- Zwiebel entfernt, Temperaturbereich korrigiert

**v1-Befund:** Zwiebel faelschlich als Vernalisationspflanze, Temperaturbereich unpraezise, Endodormanz nicht unterschieden.
**Korrektur in UI-NFR-011, Zeile 190-191:**
```
"Zweijahrige Pflanzen (z.B. Petersilie, Kohl, Sellerie) und Wintergetreide brauchen
mehrere Wochen Kaelte (0-7 Grad C), bevor sie im Fruehling Blueten bilden koennen.
Obstbaeume brauchen aehnlich eine Kaelteperiode (Chill-Hours), um die Knospenruhe
zu brechen."
```
**Bewertung:** Korrekt umgesetzt. Alle drei v1-Kritikpunkte behoben:
1. Zwiebel (*Allium cepa*) entfernt -- korrekt, da primaer photoperiodisch gesteuert.
2. Temperaturbereich "0-7 Grad C" statt "unter 5-10 Grad C" -- biologisch praeziser.
3. Obstbaum-Mechanismus korrekt als "Chill-Hours" / "Knospenruhe" differenziert (nicht Vernalisation im engeren Sinne).
Der beginnerTip ist praxisnah: "Betrifft v.a. Petersilie und Kohl im zweiten Jahr." Keine neuen Probleme.

---

## Korrektur-Verifikation: Unvollstaendig (v1)

### U-001 [BEHOBEN]: Seed-Daten-Vollstaendigkeit als Akzeptanzkriterium

**v1-Befund:** Fehlende botanische Familien und Species fuer Starter-Kits.
**Korrektur in REQ-020, Zeile 503:**
```
- [ ] Alle in Starter-Kits referenzierten Species existieren als vollstaendige
      Seed-Daten (BotanicalFamily, Species, LifecycleConfig, GrowthPhases,
      RequirementProfiles)
```
**Bewertung:** Das Akzeptanzkriterium ist korrekt ergaenzt. Allerdings verbleibt ein praktisches Delta: Die tatsaechlichen Seed-Daten (`seed_data.py`) enthalten weiterhin nur 5 Species und 9 Familien. Die folgenden Familien und Species muessen noch angelegt werden (Tracking in U-001-RESIDUAL unten). Dies ist kein Fehler der Spezifikation, sondern eine Implementierungsaufgabe.

---

### U-002 [OFFEN -- kein Korrekturbedarf im v1-Report]: Zimmerpflanzen-Lifecycle-Phasen

**v1-Befund:** Zimmerpflanzen benoetigen andere GrowthPhases als Nutzpflanzen.
**Status:** Dieser Befund wurde im v1-Report als Strukturhinweis formuliert, nicht als konkreter Korrekturbedarf an REQ-020/021/NFR-011. REQ-020 Zeile 263 spezifiziert "Mindestens 3 vorkonfigurierte GrowthPhases mit Dauern" und "GrowthPhases werden automatisch aus den Species-Seed-Daten konfiguriert" (Zeile 495). Die Implementierung der zimmerpflanzenspezifischen Phasen (acclimatization, active_growth, maintenance, repotting_recovery) ist damit eine Seed-Daten-Aufgabe, keine Spec-Luecke.

---

### U-003 [BEHOBEN]: Cultivars zum Zimmerpflanzen-Kit

**v1-Befund:** Zimmerpflanzen-Kit hatte keine Cultivar-Angaben.
**Korrektur in REQ-020, Zeile 251:**
```
| zimmerpflanzen | Zimmerpflanzen | [...] | Golden Pothos, Ficus lyrata 'Bambino' | beginner |
```
**Bewertung:** Korrekt umgesetzt. 'Golden Pothos' (*Epipremnum aureum*) und 'Bambino' (*Ficus lyrata*) sind die anfaengerfreundlichsten Cultivars ihrer jeweiligen Species. 'Golden Pothos' ist tatsaechlich der robusteste Pothos-Cultivar, und 'Bambino' bleibt kompakter als die Baumform -- ideal fuer begrenzte Stellflaechen. Keine neuen Probleme.

---

### U-004 [BEHOBEN]: Toxizitaetswarnungen und haustierfreundliches Kit

**v1-Befund:** Toxische Pflanzen im Zimmerpflanzen-Kit ohne Warnung, kein haustierfreundliches Alternativ-Kit.
**Korrekturen:**
1. `toxicity_warning` als Property im StarterKit-Modell (REQ-020, Zeile 59):
   ```
   toxicity_warning: Optional[dict] (z.B. {"cats": "warning", "dogs": "warning",
   "children": "caution"}. Werte: "safe", "caution", "warning", "danger")
   ```
2. Neues Kit `zimmerpflanzen-haustierfreundlich` (REQ-020, Zeile 252):
   ```
   | zimmerpflanzen-haustierfreundlich | Zimmerpflanzen (haustierfreundlich) |
     Chlorophytum comosum, Chamaedorea elegans, Pilea peperomioides,
     Maranta leuconeura | Gruenlilie, Bergpalme, Glueckstaler, Pfeilwurz | beginner |
   ```
3. Akzeptanzkriterium (REQ-020, Zeile 504):
   ```
   - [ ] Starter-Kits mit toxischen Pflanzen zeigen toxicity_warning an
   ```

**Bewertung:** Beide Optionen (Warnung + alternatives Kit) umgesetzt -- entspricht der v1-Empfehlung. Die Species-Auswahl im haustierfreundlichen Kit ist biologisch korrekt:
- *Chlorophytum comosum*: ASPCA-gelistet als ungiftig fuer Katzen und Hunde. Korrekt.
- *Chamaedorea elegans*: ASPCA-gelistet als ungiftig. Korrekt.
- *Pilea peperomioides*: ASPCA-gelistet als ungiftig. Korrekt.
- *Maranta leuconeura*: ASPCA-gelistet als ungiftig. Korrekt.

Alle vier Pflanzen sind robust, pflegeleicht und fuer Einsteiger geeignet. Die Cultivar-Bezeichnungen (Gruenlilie, Bergpalme, Glueckstaler, Pfeilwurz) sind die im Handel gaengigen deutschen Trivialnamen. Keine neuen Probleme.

**Hinweis zu fehlenden Familien:** Das haustierfreundliche Kit fuehrt eine weitere fehlende botanische Familie ein:
- *Chamaedorea elegans* -> Arecaceae (Palmengewaechse) -- Familie fehlt in Seed-Daten
- *Pilea peperomioides* -> Urticaceae (Brennnesselgewaechse) -- Familie fehlt in Seed-Daten
- *Maranta leuconeura* -> Marantaceae (Pfeilwurzgewaechse) -- Familie fehlt in Seed-Daten
- *Chlorophytum comosum* -> Asparagaceae (Spargelgewaechse) -- gleiche Familie wie *Dracaena trifasciata*, bereits im Zimmerpflanzen-Kit referenziert

Dies erhoeht die Gesamtzahl fehlender Familien auf mindestens 7 (Araceae, Moraceae, Asparagaceae, Amaryllidaceae, Arecaceae, Urticaceae, Marantaceae). Siehe U-001-RESIDUAL.

---

### U-005 [BEHOBEN]: Glossar-Erweiterung auf 38 Begriffe

**v1-Befund:** 30 Pflicht-Begriffe unzureichend, wichtige Einsteiger-Begriffe fehlten.
**Korrektur in UI-NFR-011:**
- Mindest-Glossarumfang von 30 auf 38 erhoht (Zeile 321)
- 11 neue Glossar-Eintraege hinzugefuegt mit vollstaendigen short/long/beginnerTip-Texten (ab Zeile 243):
  - `substrat` (Zeile 243-248)
  - `cultivar_sorte` (Zeile 249-254)
  - `standort_location_slot` (Zeile 255-260)
  - `pflanzdurchlauf` (Zeile 261-266)
  - `mischkultur` (Zeile 267-272)
  - `fruchtfolge` (Zeile 273-278)
  - `ph_wert` (Zeile 279-284)
  - `staunaesse` (Zeile 285-290)
  - `drainage` (Zeile 291-296)
  - `umtopfen` (Zeile 297-302)
  - `lux_vs_ppfd` (Zeile 239-242)

**Bewertung der neuen Glossar-Eintraege:**

| Eintrag | short | long | beginnerTip | Biologisch korrekt? |
|---------|-------|------|-------------|---------------------|
| `substrat` | Korrekt | Korrekt, gute Beispielaufzaehlung | Praxisnah und korrekt | Ja |
| `cultivar_sorte` | Korrekt (Cultivar = Sorte) | Korrekt, gutes Beispiel mit Tiny Tim | Praxisnah | Ja |
| `standort_location_slot` | Korrekt (3-Ebenen-System) | Korrekt, konsistent mit REQ-002 | Guter Hinweis "Slots erst bei vielen Pflanzen" | Ja |
| `pflanzdurchlauf` | Korrekt | Korrekt, konsistent mit REQ-013 | Gute Analogie "wie ein Projekt" | Ja |
| `mischkultur` | Korrekt | Korrekt, gutes Beispiel (Tomate+Basilikum) | Praxisnah, inkl. Negativbeispiel (Fenchel) | Ja |
| `fruchtfolge` | Korrekt | Korrekt, 3-Jahres-Faustregel stimmt | Guter Praxis-Hinweis "ab dem zweiten Gartenjahr" | Ja |
| `ph_wert` | Korrekt | Korrekt, Skala erklaert, Heidelbeere als Beispiel gut | Praxisnah "erst bei Problemen pruefen" | Ja |
| `staunaesse` | Korrekt | Korrekt, "haeufigste Ursache fuer Pflanzentod" ist faktisch richtig | Exzellent -- "30 Minuten Untersetzer wegkippen" | Ja |
| `drainage` | Korrekt | Korrekt | Praxisnah "Loch im Topf = wichtigste Drainage" | Ja |
| `umtopfen` | Korrekt, "2-4 cm groesser" ist Standardempfehlung | Korrekt, Fruehling als beste Zeit stimmt | Gute Symptom-Erkennung fuer Einsteiger | Ja |
| `lux_vs_ppfd` | Korrekt und wichtig | Korrekt, Faustformel PPFD = Lux/70 ist fuer weisse LEDs brauchbar | Praxisnah, erwaehnt Smartphone-Limitierung | Ja |

**Gesamtbewertung der neuen Eintraege:** Alle 11 neuen Glossar-Eintraege sind biologisch korrekt, in verstaendlicher Sprache formuliert und liefern praxisnahe beginnerTips. Keine neuen Probleme.

Die Kategorie-Zuordnung der neuen Eintraege (Zeile 247: `"category": "substrat"`, Zeile 253: `"category": "taxonomie"`, etc.) ist korrekt und konsistent mit der Pflicht-Begriffe-Tabelle (Zeile 310-321).

---

### U-006 [BEHOBEN]: Microgreens praezisiert

**v1-Befund:** *Brassica oleracea* zu unspezifisch, Sprossen/Microgreens vermischt.
**Korrektur in REQ-020, Zeile 256:**
```
| microgreens | Microgreens | Brassica oleracea var. italica,
  Raphanus sativus, Helianthus annuus |
  Brokkoli-Microgreens 'Calabrese', Radieschen-Microgreens 'China Rose',
  Sonnenblumen-Microgreens | beginner |
```
**Bewertung:** Korrekt umgesetzt:
1. *Brassica oleracea* var. *italica* statt nur *B. oleracea* -- taxonomisch praezise.
2. Kit-Name geaendert zu "Microgreens" (ohne "Sprossen") -- korrekte Abgrenzung.
3. Cultivar-Angaben hinzugefuegt: 'Calabrese' ist ein Standard-Brokkoli-Cultivar fuer Microgreens, 'China Rose' ein gaengiger Radieschen-Cultivar.

Keine neuen Probleme.

---

### U-007 [BEHOBEN]: Einsteiger-Pflegekarte spezifiziert

**v1-Befund:** Einsteiger-Modus blendet die drei wichtigsten Pflegeparameter (Licht, Wasser, Erde) aus.
**Korrektur in REQ-021, Zeile 244-255:**
```
Einsteiger-Pflegekarte (PlantInstance-Detail):
  - Lichtbedarf: aus requirement_profile.ppfd, natuerlichsprachlich
  - Giessen: aus irrigation_strategy / Species-Defaults
  - Substrat: aus Species-Defaults / REQ-019
  - Naechste Aktion: aus Task-System (REQ-006)
  - Standort: Location-Name
```
**Bewertung:** Korrekt umgesetzt. Die Pflegekarte zeigt genau die drei Kernparameter, die ein Einsteiger braucht:
1. Lichtbedarf uebersetzt in natuerliche Sprache ("Helles indirektes Licht", "Volle Sonne") -- entspricht v1-Hinweis H-002
2. Giessinformation aus den richtigen Quellen (irrigation_strategy + Species-Defaults)
3. Substrat-Information verknuepft mit REQ-019

Die Quellzuordnungen sind technisch korrekt (requirement_profile.ppfd -> natuerlichsprachlich, Task-System fuer naechste Aktion). Keine neuen Probleme.

---

### U-008 [BEHOBEN]: Chili-Kit aufgeteilt

**v1-Befund:** *Capsicum chinense* als `intermediate` unterschaetzt.
**Korrektur in REQ-020, Zeile 254-255:**
```
| chili-zucht | Chili-Zucht (Einsteiger) | Capsicum annuum |
  Jalapeno, Cayenne, Hungarian Wax | beginner |
| superhot-chili | Superhot-Chili | Capsicum chinense, Capsicum annuum |
  Habanero Orange, Carolina Reaper, Trinidad Scorpion | advanced |
```
**Bewertung:** Korrekt umgesetzt:
1. Einsteiger-Chili-Kit nur mit *C. annuum* (beginner) -- biologisch sinnvoll, da *C. annuum* in Mitteleuropa gut outdoor/Balkon reift (90-120 Tage)
2. Superhot-Kit als `advanced` statt `intermediate` -- korrekt, *C. chinense* (150-200 Tage, hohe Temperaturanforderungen) erfordert Erfahrung
3. Superhot-Kit enthaelt auch *C. annuum* neben *C. chinense* -- sinnvoll fuer Sortenvielfalt

Biologischer Hinweis: 'Trinidad Scorpion' ist tatsaechlich *Capsicum chinense* (obwohl es gelegentlich als eigene Art diskutiert wird). Die Zuordnung ist korrekt.

Die Kit-Anzahl steigt damit auf 9 (vorher 7), was die Akzeptanzbedingung "Mindestens 5 Starter-Kits" (Zeile 502) komfortabel erfuellt. Keine neuen Probleme.

---

## Korrektur-Verifikation: Praezisierung (v1)

### P-001/P-002/P-003 [BEHOBEN]: Dynamische Defaults aus Species-Seed-Daten

**v1-Befund:** Statische Defaults fuer `root_type`, `base_temp`, `allelopathy_score` sind fuer 40-60% der Species falsch.
**Korrektur in REQ-021, Zeile 40 (Konzeptaenderung):**
```
Species-abhaengige Felder (z.B. root_type, base_temp, allelopathy_score) werden
per Lookup aus den Species-Seed-Daten befuellt; statische Fallbacks greifen nur,
wenn keine Species ausgewaehlt ist.
```
**Korrektur in REQ-021, Zeile 99-103 (Feld-Konfiguration):**
```
| root_type        | -- | -- | Sichtbar | Aus Species-Seed-Daten (Fallback: 'fibrous') |
| allelopathy_score | -- | -- | Sichtbar | Aus Species-Seed-Daten (Fallback: 0)          |
| base_temp        | -- | -- | Sichtbar | Aus Species-Seed-Daten (Fallback: 10.0)       |
```

**Bewertung:** Korrekt umgesetzt. Der Mechanismus "Species-Lookup mit statischem Fallback" ist die richtige Architektur:
- Wenn eine Species ausgewaehlt ist (der Normalfall im Einsteiger-Modus via Starter-Kit): Korrekte Werte aus Seed-Daten
- Wenn keine Species ausgewaehlt ist (nur moeglich bei manuellem Erstellen im Experten-Modus): Statische Fallbacks greifen als sinnvolle Naeherung

Die Fallback-Werte (`fibrous`, `0`, `10.0`) sind als "sicherste Annahme" akzeptabel:
- `fibrous` ist der haeufigste Wurzeltyp unter Nutzpflanzen
- `allelopathy_score: 0` (neutral) verursacht keine falschen Mischkultur-Empfehlungen
- `base_temp: 10.0` ist ein mittlerer Wert, der fuer ~50% der gaengigen Arten korrekt ist

**Voraussetzung:** Die Seed-Daten muessen fuer alle Starter-Kit-Species korrekte Werte fuer `root_type`, `base_temp` und `allelopathy_score` enthalten. Dies ist durch U-001 (Akzeptanzkriterium) abgedeckt.

Keine neuen Probleme.

---

### P-004 [BEHOBEN]: PPFD-beginnerTip nach Himmelsrichtung differenziert

**v1-Befund:** "200-400 umol/m^2/s auf der Fensterbank" zu hoch und undifferenziert.
**Korrektur in UI-NFR-011, Zeile 162:**
```
"Faustregel: Suedfenster mit Direktsonne im Sommer ca. 200-400 (wenige Stunden).
 Ost-/Westfenster: 100-200. Nordfenster: unter 50.
 Fuer Tomaten und Chili oft zu wenig -- Growlampe empfehlenswert."
```
**Bewertung:** Korrekt umgesetzt. Die Differenzierung nach Himmelsrichtung und der Hinweis "(wenige Stunden)" fuer Suedfenster sind die zwei entscheidenden Verbesserungen. Der Zusatz "Fuer Tomaten und Chili oft zu wenig" ist eine wichtige Einsteiger-Warnung, die unrealistische Erwartungen an Fensterbank-Anbau von Fruchtgemuese dampft.

Die Werte sind realistisch:
- Suedfenster Direktsonne Sommer: 200-400 umol/m^2/s (peaks bis 600, aber zeitlich begrenzt) -- korrekt
- Ost-/Westfenster: 100-200 umol/m^2/s (morgens/abends Direktsonne) -- korrekt
- Nordfenster: unter 50 umol/m^2/s -- korrekt (nur diffuses Licht)

Keine neuen Probleme.

---

### P-005 [BEHOBEN]: EC Gesamt vs. Netto klargestellt

**v1-Befund:** EC-Wert ohne Unterscheidung zwischen Gesamt-EC und Netto-EC.
**Korrektur in UI-NFR-011, Zeile 154-156:**
```
"EC misst die Naehrstoffkonzentration im Giesswasser. Gesamt-EC = Leitungswasser-EC +
 Duenger-EC. Deutsches Leitungswasser hat ca. 0,3-0,8 mS/cm. Fuer Topfpflanzen
 Gesamt-EC 1,0-2,0 mS/cm anstreben. Hydroponik praeziser: Netto-EC (nur Duenger)
 nach Pflanzenart einstellen."
```
**Bewertung:** Korrekt umgesetzt. Die Trennung Gesamt-EC vs. Netto-EC (nur Duenger) ist die zentrale Klarstellung. Die Angabe "deutsches Leitungswasser 0,3-0,8 mS/cm" ist korrekt (Bundesdurchschnitt, regionabhaengig). Der beginnerTip "Halte dich an die Dosierungsempfehlung auf der Duenger-Flasche. Lieber etwas weniger als zu viel." ist pragmatisch und korrekt. Keine neuen Probleme.

---

### P-006 [BEHOBEN]: Dormanz -- Winter-Verlangsamung bei tropischen Zimmerpflanzen

**v1-Befund:** "Tropische Zimmerpflanzen machen keine echte Dormanz" irrefuehrend ohne Erwaehnung der praktischen Winter-Verlangsamung.
**Korrektur in UI-NFR-011, Zeile 196:**
```
"Kakteen und Sukkulenten brauchen eine kuehle Winterruhe (10-15 Grad C, kaum giessen).
 Tropische Zimmerpflanzen haben keine echte Dormanz, wachsen aber im Winter langsamer
 wegen weniger Licht -- dann weniger giessen und nicht duengen."
```
**Bewertung:** Korrekt umgesetzt. Der Satz "wachsen aber im Winter langsamer wegen weniger Licht -- dann weniger giessen und nicht duengen" schliesst die v1-Luecke praezise. Die Kausalitaet (weniger Licht -> langsamer -> weniger Wasser/Duenger) ist biologisch korrekt und vermeidet die irrefuehrende Implikation, dass tropische Pflanzen indoor "weitermachen wie im Sommer". Keine neuen Probleme.

---

### P-008 [BEHOBEN]: CEC Kokos-Wert ergaenzt

**v1-Befund:** CEC-Glossar springt von Blaehton (2-5) auf Erde (100-200) ohne Kokos-Zwischenwert.
**Korrektur in UI-NFR-011, Zeile 230:**
```
"Blaehton ca. 2-5, Kokos ca. 40-100, Erde ca. 100-200 meq/100g."
```
**Bewertung:** Korrekt umgesetzt. Die Ergaenzung um Kokos (40-100 meq/100g) schliesst die Luecke zwischen Blaehton und Erde. Die Werte sind konsistent mit REQ-019 Zeile 50. Keine neuen Probleme.

---

### H-005 [BEHOBEN]: Lux vs. PPFD Glossar-Eintrag

**v1-Befund:** Der empfohlene Glossar-Eintrag "Lux vs. PPFD" sollte ausgebaut werden.
**Korrektur in UI-NFR-011, Zeile 239-242:**
```
"lux_vs_ppfd": {
  "short": "Lux = fuer menschliche Augen, PPFD = fuer Pflanzen",
  "long": "Lux misst die Helligkeit fuer das menschliche Auge und gewichtet
           Gruenlicht am staerksten. Pflanzen nutzen vor allem Rot- und Blaulicht.
           Eine Natriumdampflampe und eine LED koennen identische Lux-Werte haben,
           aber voellig unterschiedliche PPFD-Werte liefern.
           Faustformel fuer weisses LED-Licht: PPFD = Lux / 70.",
  "beginnerTip": "Smartphone-Lux-Apps geben nur einen groben Anhaltspunkt.
                  Fuer praezise Pflanzenbeleuchtung ist ein PPFD-Messgeraet
                  noetig -- oder verlass dich auf die Herstellerangaben
                  deiner Growlampe."
}
```
**Bewertung:** Korrekt umgesetzt. Die Faustformel "PPFD = Lux / 70" ist fuer weisses LED-Licht (4000-6500K) eine brauchbare Naeherung (Literaturwerte: 65-80 je nach Spektrum). Der Hinweis auf Natriumdampflampe vs. LED ist ein exzellentes Beispiel, das die Spektrumabhaengigkeit verdeutlicht. Keine neuen Probleme.

---

## Neue Befunde (v2)

### Fachlich Falsch -- KEINE neuen fachlichen Fehler identifiziert

Die Korrekturen haben keine neuen biologischen Fehler eingefuehrt. Alle Glossar-Texte, Species-Zuordnungen und parametrischen Angaben sind fachlich korrekt.

---

## Verbleibende Unvollstaendigkeiten (v2)

### U-001-RESIDUAL: Seed-Daten-Delta -- 7 Familien und 18+ Species fehlen in Implementierung

**Anbaukontext:** Alle Starter-Kits
**Status:** Spezifikation korrekt (Akzeptanzkriterium vorhanden), Implementierung ausstehend
**Problem:** Die Seed-Daten (`seed_data.py`) enthalten 5 Species und 9 Familien. Fuer die 9 Starter-Kits werden benoetigt:

**Fehlende Botanische Familien (7):**

| Familie | Common Name | Benoetigt fuer Kit |
|---------|-------------|-------------------|
| Araceae | Aronstabgewaechse | zimmerpflanzen (*Monstera*, *Epipremnum*) |
| Moraceae | Maulbeergewaechse | zimmerpflanzen (*Ficus lyrata*) |
| Asparagaceae | Spargelgewaechse | zimmerpflanzen (*Dracaena trifasciata*), haustierfreundlich (*Chlorophytum*) |
| Amaryllidaceae | Amaryllisgewaechse | fensterbank-kraeuter (*Allium schoenoprasum*) |
| Arecaceae | Palmengewaechse | zimmerpflanzen-haustierfreundlich (*Chamaedorea elegans*) |
| Urticaceae | Brennnesselgewaechse | zimmerpflanzen-haustierfreundlich (*Pilea peperomioides*) |
| Marantaceae | Pfeilwurzgewaechse | zimmerpflanzen-haustierfreundlich (*Maranta leuconeura*) |

**Fehlende Species (18):**

| Species | Familie | Kit |
|---------|---------|-----|
| *Monstera deliciosa* | Araceae | zimmerpflanzen |
| *Ficus lyrata* | Moraceae | zimmerpflanzen |
| *Epipremnum aureum* | Araceae | zimmerpflanzen |
| *Dracaena trifasciata* | Asparagaceae | zimmerpflanzen |
| *Chlorophytum comosum* | Asparagaceae | haustierfreundlich |
| *Chamaedorea elegans* | Arecaceae | haustierfreundlich |
| *Pilea peperomioides* | Urticaceae | haustierfreundlich |
| *Maranta leuconeura* | Marantaceae | haustierfreundlich |
| *Mentha spicata* | Lamiaceae | fensterbank-kraeuter |
| *Petroselinum crispum* | Apiaceae | fensterbank-kraeuter |
| *Allium schoenoprasum* | Amaryllidaceae | fensterbank-kraeuter |
| *Anethum graveolens* | Apiaceae | fensterbank-kraeuter |
| *Phaseolus vulgaris* | Fabaceae | kleines-gemusebeet |
| *Daucus carota* | Apiaceae | kleines-gemusebeet |
| *Brassica oleracea* var. *italica* | Brassicaceae | microgreens |
| *Raphanus sativus* | Brassicaceae | microgreens |
| *Helianthus annuus* | Asteraceae | microgreens |
| *Capsicum chinense* | Solanaceae | superhot-chili |

**Prioritaet:** Hoch -- blockiert die Starter-Kit-Funktionalitaet
**Kein Spec-Fehler** -- das Akzeptanzkriterium ist korrekt formuliert. Dies ist ein Implementierungs-Tracking-Hinweis.

---

### U-009 (NEU): Haustierfreundliches Kit fehlt `toxicity_warning` mit `safe`-Werten

**Anbaukontext:** Zimmerpflanzen
**Problem:** Das Kit `zimmerpflanzen-haustierfreundlich` (Zeile 252) definiert bewusst ungiftige Pflanzen. Es wird jedoch kein expliziter `toxicity_warning`-Wert angegeben. Fuer Konsistenz und um in der UI das Kit als "sicher" kennzeichnen zu koennen, sollte ein explizites Safety-Label gesetzt werden.

**Formulierungsvorschlag:**
```
toxicity_warning: {"cats": "safe", "dogs": "safe", "children": "safe"}
```
Dies ermoeglicht im Frontend eine positive Kennzeichnung ("Haustierfreundlich") statt nur der Abwesenheit einer Warnung.

**Prioritaet:** Niedrig -- rein kosmetisch/UX, kein fachlicher Fehler

---

### U-010 (NEU): Kit-spezifische `toxicity_warning` fehlt im normalen Zimmerpflanzen-Kit

**Anbaukontext:** Zimmerpflanzen
**Problem:** Das Kit `zimmerpflanzen` (Zeile 251) enthaelt vier Pflanzen, die alle fuer Haustiere toxisch sind (siehe v1-Report U-004). Das `toxicity_warning`-Feld wurde zwar als Property definiert (Zeile 59) und als Akzeptanzkriterium aufgenommen (Zeile 504), aber die Seed-Daten-Tabelle (Zeile 248-256) enthaelt keine konkreten `toxicity_warning`-Werte pro Kit.

**Formulierungsvorschlag:** In der Seed-Daten-Tabelle oder einem ergaenzenden Abschnitt sollte pro Kit der konkrete `toxicity_warning`-Wert angegeben werden:

| Kit-ID | toxicity_warning |
|--------|-----------------|
| zimmerpflanzen | `{"cats": "warning", "dogs": "warning", "children": "caution"}` |
| zimmerpflanzen-haustierfreundlich | `{"cats": "safe", "dogs": "safe", "children": "safe"}` |
| fensterbank-kraeuter | `{"cats": "safe", "dogs": "safe", "children": "safe"}` |
| balkon-tomaten | `{"cats": "caution", "dogs": "caution", "children": "safe"}` |
| indoor-growzelt | `{"cats": "caution", "dogs": "caution", "children": "danger"}` |

Hinweis: Tomatengruenpflanze (*Solanum lycopersicum*) enthaelt Solanin/Tomatidin in Blaettern und unreifen Fruechten -- milde Toxizitaet fuer Haustiere. Cannabis-Pflanzenmaterial ist fuer Tiere problematisch und fuer Kinder kontrolliert.

**Prioritaet:** Mittel -- das Akzeptanzkriterium verlangt die Warnung, die konkreten Werte fehlen in der Spec

---

### U-011 (NEU): Zimmerpflanzen-Lifecycle-Phasen nicht spezifiziert

**Anbaukontext:** Zimmerpflanzen
**Problem:** REQ-020 Zeile 263 spezifiziert "Mindestens 3 vorkonfigurierte GrowthPhases mit Dauern". Die bestehenden DEFAULT_PHASES (seedling, vegetative, flowering, ripening) in `seed_data.py` sind fuer einjahrige Nutzpflanzen konzipiert und biologisch unpassend fuer Zimmerpflanzen wie *Monstera deliciosa* oder *Dracaena trifasciata*. Es fehlt eine Spezifikation, welche Phasen fuer Zimmerpflanzen-Kits genutzt werden sollen.

**Empfohlene Zimmerpflanzen-Phasen:**
```
- acclimatization (Eingewoehnung nach Kauf/Umtopfen): 14-28 Tage
- active_growth (aktives Wachstum): ganzjaehrig bei Kunstlicht, saisonal bei Tageslicht
- maintenance (Erhaltungspflege / Winterverlangsamung): an Jahreszeit gekoppelt
- repotting_recovery (Umtopf-Erholung): 7-14 Tage (optional, event-triggered)
```

**Prioritaet:** Mittel -- betrifft die fachliche Qualitaet der Zimmerpflanzen-Kits
**Empfehlung:** Dies ist eine Aufgabe fuer die Seed-Daten-Erweiterung (U-001-RESIDUAL), sollte aber im Kontext von REQ-003 dokumentiert werden, da das Phase-System dort definiert ist.

---

## Zu Ungenau -- Verbleibende Praezisierungen (v2)

### P-009 (NEU): DIF-Glossar fehlt in UI-NFR-011 Beispiel-JSON

**Problem:** In der Pflicht-Begriffe-Tabelle (Zeile 313) wird DIF (Temperatur-Differenzial Tag/Nacht) als Pflicht-Begriff unter "Klima" aufgefuehrt. Im ausfuehrlichen Glossar-Beispiel-JSON (Zeile 143-303) fehlt jedoch ein DIF-Eintrag. Im Kontrast dazu sind VPD, rH und Hysterese als Klima-Begriffe in der Pflicht-Tabelle gelistet, aber ebenfalls nicht alle im Beispiel-JSON enthalten.

**Bewertung:** Die Pflicht-Tabelle ist die normative Referenz (38 Begriffe als MUSS). Das Beispiel-JSON ist eine Vorlage, nicht die vollstaendige Liste. Da die Pflicht-Tabelle DIF korrekt als Pflicht-Begriff auffuehrt, ist dies eine geringe Luecke -- die Implementierung muss den Eintrag ohnehin erstellen.

**Formulierungsvorschlag fuer DIF:**
```json
{
  "dif": {
    "short": "Temperatur-Unterschied zwischen Tag und Nacht",
    "long": "DIF beschreibt die Differenz zwischen Tag- und Nachttemperatur. Positiver DIF (Tag waermer als Nacht) foerdert Streckungswachstum. Negativer DIF (Nacht waermer) haelt Pflanzen kompakt. In professionellen Gewaechshaeusern wird DIF gezielt zur Wuchssteuerung eingesetzt.",
    "beginnerTip": "Fuer Zimmerpflanzen: Nachts darf es 3-5 Grad kuehler sein als tagsueber -- das ist natuerlich und gut fuer die Pflanze.",
    "category": "klima"
  }
}
```

**Prioritaet:** Niedrig -- die Pflicht-Tabelle ist korrekt, nur das Beispiel ist unvollstaendig

---

### P-010 (NEU): Hysterese-Glossar fehlt im Beispiel-JSON

**Problem:** Wie DIF ist Hysterese als Pflicht-Begriff (Zeile 313, Kategorie "Klima") aufgefuehrt, aber nicht im Beispiel-JSON enthalten.

**Formulierungsvorschlag:**
```json
{
  "hysterese": {
    "short": "Schaltschwellen-Abstand, der Geraetependeln verhindert",
    "long": "Hysterese bedeutet, dass ein Geraet bei einem hoeheren Wert einschaltet als es ausschaltet. Beispiel: Befeuchter AN bei 50% rH, AUS erst bei 60% rH. Ohne Hysterese wuerde das Geraet im Sekundentakt ein- und ausschalten.",
    "beginnerTip": "Wird automatisch vom System gesteuert. Nur relevant, wenn du eigene Automatisierungsregeln erstellst.",
    "category": "klima"
  }
}
```

**Prioritaet:** Niedrig

---

### P-011 (NEU): Mixing Priority als Pflicht-Begriff gelistet, aber nicht im JSON

**Problem:** "Mixing Priority" steht in der Pflicht-Begriffe-Tabelle (Zeile 315, Naehrstoffe), fehlt aber im Beispiel-JSON. Fuer Einsteiger, die den Experten-Modus aktivieren und den Mixing-Kalkulator nutzen, ist das ein relevanter Begriff.

**Formulierungsvorschlag:**
```json
{
  "mixing_priority": {
    "short": "Reihenfolge, in der Duenger ins Wasser geruehrt wird",
    "long": "Beim Anmischen einer Naehrloesung ist die Reihenfolge wichtig: Erst CalMag, dann Basispulver, zuletzt Additive. Falsche Reihenfolge kann zu Ausfaellungen fuehren (sichtbar als Truebung oder Bodensatz).",
    "beginnerTip": "Nur bei Hydroponik relevant. Bei Fluessigduenger fuer Zimmerpflanzen einfach ins Wasser geben.",
    "category": "naehrstoffe"
  }
}
```

**Prioritaet:** Niedrig

---

## Hinweise & Best Practices (v2)

### H-006 (NEU): Fehlende Familien-spezifische Attribute fuer Zimmerpflanzen-Familien

Die neuen botanischen Familien (Araceae, Moraceae, Asparagaceae, Amaryllidaceae, Arecaceae, Urticaceae, Marantaceae) benoetigen bei der Implementierung familienspezifische Attribute, die sich von den bestehenden Nutzpflanzen-Familien deutlich unterscheiden:

| Familie | typical_nutrient_demand | nitrogen_fixing | typical_root_depth | frost_tolerance |
|---------|------------------------|----------------|-------------------|----------------|
| Araceae | medium | false | SHALLOW (Epiphyten!) | SENSITIVE |
| Moraceae | medium-heavy | false | MEDIUM | SENSITIVE-MODERATE |
| Asparagaceae | light | false | SHALLOW | MODERATE (Dracaena SENSITIVE) |
| Amaryllidaceae | medium | false | SHALLOW (Zwiebeln) | MODERATE-HARDY |
| Arecaceae | medium | false | MEDIUM | SENSITIVE |
| Urticaceae | light | false | SHALLOW | MODERATE |
| Marantaceae | light-medium | false | SHALLOW | SENSITIVE |

Besonders wichtig: Die Araceae (Monstera, Epipremnum) sind zu einem grossen Teil Epiphyten oder Hemiepiphyten. Ihr `typical_root_depth: SHALLOW` ist korrekt fuer die erdgebundene Kultur, aber ihre natuerliche Wuchsform beinhaltet Luftwurzeln, die fuer die Substrat-Wahl relevant sind (luftdurchlaessig, keine Staunaesse).

---

### H-007 (NEU): Biologische Validierung der Einsteiger-Doengeansicht

REQ-021 Zeile 237 spezifiziert die vereinfachte Duengeempfehlung im Einsteiger-Modus: "Alle 2 Wochen mit Fluessigduenger (halbe Dosierung)". Diese Faustregel ist fuer die Hauptwachstumsperiode (Maerz-Oktober) korrekt, sollte aber mit zwei Einschraenkungen versehen werden:

1. **Saisonale Anpassung:** Im Winter (November-Februar) sollte bei den meisten Zimmerpflanzen gar nicht geduengt werden (reduziertes Wachstum, erhoehtes Salzakkumulationsrisiko). Die Einsteiger-Ansicht sollte dies automatisch anpassen.

2. **Artspezifische Ausnahmen:**
   - Sukkulenten/Kakteen: Seltener duengen (monatlich oder seltener, 1/4 Dosierung)
   - Orchideen: Speziellen Orchideenduenger verwenden, nicht Universalduenger
   - Karnivoren: Nie duengen (toedlich fuer die Pflanze!)

Da die Starter-Kits keine Karnivoren enthalten, ist die Faustregel fuer alle Kit-Species akzeptabel. Fuer zukuenftige Kit-Erweiterungen sollte die Einsteiger-Duengeansicht jedoch aus den Species-Defaults abgeleitet werden, nicht statisch sein.

---

### H-008 (NEU): Cannabis-Kit -- Autoflowering-Hinweis empfehlenswert

Das Indoor-Growzelt-Kit (Zeile 253) enthaelt *Cannabis sativa* mit Cultivar "Northern Lights Auto". "Auto" steht fuer autoflowering (tagneutral durch *C. ruderalis*-Genetik). Dies steht in einem interessanten Spannungsverhaeltnis zum Photoperiodismus-Glossar-Eintrag (Zeile 205), der Cannabis als Kurztagspflanze beschreibt.

Empfehlung: Der Glossar-Eintrag zum Photoperiodismus koennte im beginnerTip erwaehnen:
```
"Autoflowering-Sorten (z.B. Northern Lights Auto) sind tagneutral und bluehen
unabhaengig von der Lichtdauer -- ideal fuer Einsteiger."
```

Dies ist kein Fehler, sondern eine Verbesserungsmoeglichkeit. Die aktuelle Formulierung "Bluete durch 12/12 Lichtumstellung" ist fuer photoperiodische Sorten korrekt, trifft aber nicht auf den im Kit empfohlenen Autoflowering-Cultivar zu.

**Prioritaet:** Niedrig

---

## Parameter-Uebersicht: Status der Messwerte in Starter-Kits (v2 Update)

| Parameter | v1 Status | v2 Status | Kommentar |
|-----------|-----------|-----------|-----------|
| PPFD (umol/m^2/s) | Fehlend | Per Akzeptanzkriterium gefordert (RequirementProfiles) | Korrekt |
| DLI (mol/m^2/d) | Fehlend | Implizit ueber PPFD + Photoperiode berechenbar | Akzeptabel |
| Bewasserungsfrequenz | Fehlend | Ueber Einsteiger-Pflegekarte (U-007) abgedeckt | Korrekt |
| Temperaturbereich | Fehlend | Per RequirementProfiles gefordert | Korrekt |
| Luftfeuchtigkeit (rH%) | Fehlend | Per RequirementProfiles gefordert | Korrekt |
| Substrattyp | Fehlend | Ueber Einsteiger-Pflegekarte (U-007) abgedeckt | Korrekt |
| Toxizitaet | Fehlend | `toxicity_warning` Property + Akzeptanzkriterium | Korrekt |
| Topfgroesse | Fehlend | Nicht explizit adressiert | Wuenschenswert (v1 P-007) |
| VPD (kPa) | Im Einsteiger-Modus verborgen | Korrekter artabhaengiger Bereich im Glossar | Korrekt |
| EC-Wert (mS/cm) | Im Einsteiger-Modus verborgen | Gesamt/Netto-EC im Glossar klargestellt | Korrekt |

---

## Zusammenfassende Bewertung der Korrekturen

### Vollstaendig und korrekt behoben (12/15 v1-Befunde):

| ID | Typ | Titel | Status |
|----|-----|-------|--------|
| F-001 | Fachlich Falsch | Sansevieria -> Dracaena | BEHOBEN, korrekt |
| F-002 | Fachlich Falsch | Photoperiodismus Dunkelperiode | BEHOBEN, korrekt |
| F-004 | Fachlich Falsch | VPD artabhaengig | BEHOBEN, korrekt |
| F-005 | Fachlich Falsch | Vernalisation praezisiert | BEHOBEN, korrekt |
| U-001 | Unvollstaendig | Seed-Daten Akzeptanzkriterium | BEHOBEN (Spec), Implementierung offen |
| U-003 | Unvollstaendig | Zimmerpflanzen-Cultivars | BEHOBEN, korrekt |
| U-004 | Unvollstaendig | Toxizitaetswarnung + Haustier-Kit | BEHOBEN, korrekt |
| U-005 | Unvollstaendig | Glossar auf 38 Begriffe | BEHOBEN, korrekt |
| U-006 | Unvollstaendig | Microgreens praezisiert | BEHOBEN, korrekt |
| U-008 | Unvollstaendig | Chili-Kit aufgeteilt | BEHOBEN, korrekt |
| P-001/P-002/P-003 | Praezisierung | Dynamische Defaults | BEHOBEN, korrekt |
| P-004 | Praezisierung | PPFD nach Himmelsrichtung | BEHOBEN, korrekt |
| P-005 | Praezisierung | EC Gesamt/Netto | BEHOBEN, korrekt |
| P-006 | Praezisierung | Dormanz Winter-Verlangsamung | BEHOBEN, korrekt |
| P-008 | Praezisierung | CEC Kokos-Wert | BEHOBEN, korrekt |
| H-005 | Hinweis | Lux vs. PPFD Glossar | BEHOBEN, korrekt |
| U-007 | Unvollstaendig | Einsteiger-Pflegekarte | BEHOBEN, korrekt |

### Nicht in diesen Docs adressiert (erwartet):

| ID | Typ | Titel | Status |
|----|-----|-------|--------|
| F-003 | Fachlich Falsch | Basilikum Kurztagspflanze | REQ-001-Befund, nicht in Scope |
| U-002 | Unvollstaendig | Zimmerpflanzen-Lifecycle-Phasen | Implementierungs-Aufgabe (U-011 neu) |
| P-007 | Praezisierung | Topfgroesse pro Cultivar | Optional, nicht umgesetzt |

### Neue v2-Befunde (5, alle Niedrig-Mittel):

| ID | Typ | Titel | Prioritaet |
|----|-----|-------|-----------|
| U-009 | Unvollstaendig | Haustierfreundlich-Kit safe-Label | Niedrig |
| U-010 | Unvollstaendig | Konkrete toxicity_warning pro Kit | Mittel |
| U-011 | Unvollstaendig | Zimmerpflanzen-Lifecycle-Phasen | Mittel |
| P-009 | Praezisierung | DIF-Glossar-JSON | Niedrig |
| P-010 | Praezisierung | Hysterese-Glossar-JSON | Niedrig |
| P-011 | Praezisierung | Mixing Priority-Glossar-JSON | Niedrig |

---

## Empfohlene Datenquellen (aktualisiert)

| Bereich | Quelle | URL |
|---------|--------|-----|
| Zimmerpflanzen-Toxizitaet | ASPCA Animal Poison Control | aspca.org/pet-care/animal-poison-control |
| Taxonomie (aktuell, APG IV) | Plants of the World Online (POWO) | powo.science.kew.org |
| Zimmerpflanzen-Pflege | Royal Horticultural Society | rhs.org.uk |
| Araceae-Taxonomie (Monstera, Epipremnum) | International Aroid Society | aroid.org |
| Arecaceae-Taxonomie (Chamaedorea) | Palmweb | palmweb.org |
| Microgreens-Anbaudaten | Universitaet Florida IFAS | edis.ifas.ufl.edu |
| Chili-Cultivar-Daten | Chile Pepper Institute (NMSU) | chile.nmsu.edu |
| Licht-Grundlagen (PPFD vs. Lux) | Apogee Instruments | apogeeinstruments.com |

---

## Glossar

- **APG IV** (Angiosperm Phylogeny Group IV): Aktuelles phylogenetisches Klassifikationssystem fuer Bluetenpflanzen (2016). Referenzstandard fuer die Familienzuordnung im System.
- **POWO** (Plants of the World Online): Referenzdatenbank fuer aktuelle botanische Nomenklatur, betrieben von Kew Gardens. Autoritaet fuer die Gueltigkeit wissenschaftlicher Pflanzennamen.
- **ASPCA**: American Society for the Prevention of Cruelty to Animals. Betreibt die massgebliche Datenbank fuer Pflanzentoxizitaet bei Haustieren.
- **CEC** (Cation Exchange Capacity): Kationenaustauschkapazitaet in meq/100g -- Mass fuer die Faehigkeit eines Substrats, Naehrstoffe zu binden und wieder freizugeben.
- **DIF** (Temperature Differential): Differenz zwischen Tag- und Nachttemperatur. Steuert Streckungswachstum bei vielen Pflanzenarten.
- **Autoflowering**: Cannabis-Cultivars mit *C. ruderalis*-Genetik, die tagneutral bluehen -- im Gegensatz zu photoperiodischen Sorten.
- **Raphide**: Nadelfoermige Calciumoxalat-Kristalle in Pflanzenzellen. Ursache fuer Mund-/Rachenreizung beim Verschlucken von Araceae-Blaettern (Monstera, Philodendron, Epipremnum).
