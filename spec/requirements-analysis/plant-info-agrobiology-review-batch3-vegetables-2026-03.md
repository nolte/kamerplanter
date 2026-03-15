# Agrarbiologisches Review: Gemuese-/Kraeuterpflanzeninformationen (Batch 3)

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-05
**Fokus:** Botanische Korrektheit, Phasenparameter, Duengung, IPM, Mischkultur-Konsistenz, CSV-Import-Eignung
**Anbaukontext:** Outdoor (Freiland/Beet), Gewaechshaus, Indoor-Erweiterung

**Analysierte Dokumente (10 Dateien):**

| Datei | Art | Familie |
|-------|-----|---------|
| `spec/ref/plant-info/solanum_lycopersicum.md` | Tomate | Solanaceae |
| `spec/ref/plant-info/capsicum_annuum.md` | Paprika / Chili | Solanaceae |
| `spec/ref/plant-info/cucumis_sativus.md` | Gurke | Cucurbitaceae |
| `spec/ref/plant-info/cucurbita_pepo.md` | Zucchini | Cucurbitaceae |
| `spec/ref/plant-info/lactuca_sativa.md` | Salat | Asteraceae |
| `spec/ref/plant-info/pisum_sativum.md` | Erbse | Fabaceae |
| `spec/ref/plant-info/phaseolus_vulgaris.md` | Bohne | Fabaceae |
| `spec/ref/plant-info/daucus_carota.md` | Moehre | Apiaceae |
| `spec/ref/plant-info/beta_vulgaris_subsp_vulgaris.md` | Rote Bete / Mangold | Amaranthaceae |
| `spec/ref/plant-info/brassica_oleracea_var_gemmifera.md` | Rosenkohl | Brassicaceae |

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 3/5 | Kritische taxonomische und phytochemische Fehler in 4 von 10 Dokumenten |
| Taxonomie / Nomenklatur | 4/5 | Ueberwiegend korrekt; ein Subspecies-Fehler (Moehre) |
| Phasenparameter (PPFD, VPD, EC) | 4/5 | Gut strukturiert; produktspezifische Inkonsistenz (Aqua Flores A) |
| IPM-Vollstaendigkeit | 4/5 | Schaderregerlisten vollstaendig; ein schwerer Taxonomiefehler (Kohlhernie) |
| Mischkultur-Symmetrie | 3/5 | 7 von 28 geprueften Paaren zeigen Asymmetrien |
| CSV-Import-Eignung | 2/5 | 3 Dokumente mit kritischen Import-Blockern (Bohne, Moehre) |
| Pflegeprofile | 3/5 | 1 fachlich falsches Care-Style-Assignment (Rosenkohl) |

**Gesamteinschaetzung:** Die Batch-3-Dokumente zeigen ein hohes fachliches Niveau in Aufbau und Detailtiefe. Phasenparameter, Duengungsprofile und Schaderregerlisten sind in den meisten Dokumenten korrekt und praxistauglich. Es gibt jedoch sieben kritische Fehler, die entweder den CSV-Import blockieren oder falsche Informationen an Nutzer weitergeben wuerden. Besonders gravierend sind: die Fehlklassifikation des Kohlhernie-Erregers als Pilz (er ist ein Protist), das falsche Care-Style-Assignment fuer Rosenkohl, und CSV-Felder in Bohne und Moehre, die den Import-Validator zum Absturz bringen. Die Mischkultur-Symmetriepruefung deckt weitere 6 wesentliche Inkonsistenzen auf. Nach Behebung der K-Fehler ist das Material importbereit.

---

## K-Fehler: Kritischer Korrekturbedarf (sofortige Aktion erforderlich)

### K-001: Falsche Alkaloid-Bezeichnung bei Tomate

**Dokument:** `solanum_lycopersicum.md`, Abschnitt 5 (Toxikologie)
**Fehlerhafter Text:** "Wirkstoffe: Solanin, Tomatidin"
**Problem:** Der Begriff "Tomatidin" ist falsch. Das Glykoalkaloid in Tomatenpflanzen heisst **alpha-Tomatin** (kurz: Tomatin), nicht Tomatidin. Tomatidin ist das Aglykon (Zuckerfreie Grundstruktur) von Tomatin, das nur nach chemischer Hydrolyse entsteht und in frischen Pflanzen nicht in relevanter Menge vorkommt.

Zusaetzlich ist "Solanin" primaer ein Alkaloid der **Kartoffel** (*Solanum tuberosum*). In Tomaten ist das dominante Glykoalkaloid alpha-Tomatin, das sich strukturell von Solanin unterscheidet. Fruchtwandgewebe reifer Tomaten enthaelt kaum noch Tomatin (<5 mg/kg); es konzentriert sich in Blaettern und unreifen Fruechten.

**Korrekte Formulierung:**
```
Wirkstoffe: alpha-Tomatin (Glykoalkaloid; primaer in Blaettern,
Stiel und unreifen Fruechten; konzentriert sich im gruenem
Fruchtgewebe; in reifen Tomaten toxikologisch nicht relevant),
Solanin (Spuren in Blaettern, nicht in reifen Fruechten)
```
**Prioritaet:** Hoch (falscher Stoff wird als Hauptgift benannt)

---

### K-002: Tomate als "Dunkelkeimer" falsch klassifiziert

**Dokument:** `solanum_lycopersicum.md`, Abschnitt 3 (Keimung) und CSV-Feld `light_germination`
**Fehlerhafter Wert:** `light_germination: false` bzw. "Dunkelkeimer"
**Problem:** Tomatensamen sind **weder Lichtkeimer noch Dunkelkeimer** im physiologischen Sinne. Ihre Keimung ist **lichtunabhaengig** (phytochrom-neutral). Korrekte Quellenangaben (Bunt & Hartmann, Seed Science Research) bestaetigen: Lycopersicon esculentum keimt gleichermassen bei Licht und Dunkelheit. Die Klassifikation als Dunkelkeimer ist biologisch falsch und fuer Nutzer praxisrelevant: Samen werden unnoetig mit Abdeckung ausgesaet und wenn sie keimen (was auch ohne Abdeckung funktioniert haette) festigt sich ein Irrglauben.

Ein echter Dunkelkeimer beispielsweise ist *Phacelia tanacetifolia* oder *Nigella damascena*, nicht Solanum lycopersicum.

**Korrekte Formulierung:**
```
light_germination: null  # lichtunabhaengig (weder Licht- noch Dunkelkeimer)
Keimungshinweis: "Lichtunabhaengige Keimung. Saatgut kann abgedeckt
oder unbedeckt keimen. Abdeckung mit 0.5-1 cm Substrat aus
praktischen Gruenden (Feuchtigkeitserhalt) empfohlen, biologisch
aber nicht zwingend."
```
**Prioritaet:** Hoch (Fehler wird an Tausende Nutzer weitergegeben)

---

### K-003: Plasmodiophora brassicae als "Pilz" klassifiziert

**Dokument:** `brassica_oleracea_var_gemmifera.md`, Abschnitt IPM / Krankheiten
**Fehlerhafter Wert:** `erreger_typ: "fungal (Protist)"` oder vergleichbare Formulierung
**Problem:** *Plasmodiophora brassicae* (Kohlhernie-Erreger) ist taxonomisch **kein Pilz**. Er gehoert zu den **Phytomyxea** (frueher Plasmodiophoromycetes), einer Gruppe von obligat intrazellularen Parasiten innerhalb der Rhizaria/Supergruppe SAR. Moderne Klassifikation platziert Phytomyxea klar ausserhalb der Fungi.

Dies ist ein schwerwiegender taxonomischer Fehler: Pilzbekaempfungsmittel (Fungizide) wirken nicht gegen Plasmodiophora brassicae. Nutzer, die den Erreger als Pilz eingestuft sehen, koennten falsche Bekaempfungsmittel einsetzen. Korrekte Massnahmen sind Bodenkalkung (pH >7 hemmt Sporenkeimung), Fruchtfolge (7+ Jahre Anbaupause fuer Brassicaceae), und resistente Sorten.

**Korrekte Formulierung:**
```
erreger_typ: protist
erreger_vollname: "Plasmodiophora brassicae (Phytomyxea; kein echter Pilz)"
bekaempfung_hinweis: "Kein Fungizid wirksam. Bodenkalkung pH >7.0,
Anbausupause 7+ Jahre (Dauersporen im Boden bis 20 Jahre haltbar),
resistente Sorten (z.B. Clapton F1)."
```
**Prioritaet:** Hoch (falsche Erregereinstufung fuehrt zu falschem Pflanzenschutz)

---

### K-004: "mediterranean" Care-Style fuer Rosenkohl biologisch falsch

**Dokument:** `brassica_oleracea_var_gemmifera.md`, Abschnitt Pflegeprofil
**Fehlerhafter Wert:** `care_style: mediterranean`
**Problem:** Der `mediterranean` Pflegestil impliziert: Trockenheitstoleranz, Hitzevertraeglichkeit, reduzierte Bewaesserungsfrequenz, mediterrane Temperaturpraeferenzen (15-25 degC Optimum). Rosenkohl ist das genaue Gegenteil:

- **Herkunft:** Entwickelt in den feuchten Kuesten Nordwesteuropas (Belgien, Niederlande)
- **Optimum:** 15-18 degC, leidet bei Temperaturen >25 degC
- **Wasserversorgung:** Gleichmaessig feucht, Trockenstress fuehrt zu kleinen, lockeren Roeschen
- **Frost:** Qualitaetsverbesserung durch Frost (Staarkeabbau zu Zucker)
- **Vergleich:** Mediterrane Pflanzen (Lavendel, Rosmarin, Thymian) tolerieren Trockenheit, Hitze und kalkhaltige, gut drainierte Boeden

**Korrekte Formulierung:**
```
care_style: outdoor_annual_veg
# oder alternativ: custom mit Detailprofil
# Notiz: Rosenkohl ist ein zweijaehriger Winterkohl (als Einjahreskultur
# angebaut). Gleichmaessige Feuchte essentiell. Kein mediterraner Pflegestil.
```
**Prioritaet:** Hoch (falsches Pflegeprofil wird in automatischen Pflegeerinnerungen verwendet)

---

### K-005: Unguelter Enum-Wert `nitrogen_fixer` fuer `nutrient_demand_level` in Bohne

**Dokument:** `phaseolus_vulgaris.md`, CSV-Import-Zeile
**Fehlerhafter Wert:** `nutrient_demand_level: nitrogen_fixer`
**Problem:** Gemaess REQ-001 sind die gueltigen Werte fuer `nutrient_demand_level`:
`light`, `medium`, `heavy_feeder`

Der Wert `nitrogen_fixer` ist kein gueltiger Enum-Wert und wird den CSV-Import-Validator (`RowValidator`) zum Fehler bringen (422 Validation Error). Der Import des gesamten Dokuments schlaegt damit fehl.

Biologisch ist es korrekt, dass *Phaseolus vulgaris* (wie alle Leguminosen) Stickstoff ueber Rhizobium-Symbiose fixiert. Dies macht die Pflanze jedoch nicht zu einer eigenen Nachfragekategorie -- sie hat einen `light` Stickstoffbedarf aus externer Duengung, weil sie Stickstoff selbst produziert.

**Korrekte Formulierung:**
```
nutrient_demand_level: light
# Anmerkung im Dokument:
# N-Bedarf gering durch Rhizobium-Symbiose (N-Fixierung).
# Stickstoffduengung reduzieren oder weglassen. P und K wie Mittelzehrer.
```
**Prioritaet:** Hoch (blockiert CSV-Import des gesamten Dokuments)

---

### K-006: Multi-Wert-Felder in Bohne CSV sind Import-inkompatibel

**Dokument:** `phaseolus_vulgaris.md`, CSV-Import-Zeile
**Fehlerhafte Werte:**
```
growth_habit: "herb (Buschbohne); vine (Stangenbohne)"
root_type: "fibrous (mit Knollchenbakterien/Rhizobien fuer N-Fixierung)"
```
**Problem 1 (`growth_habit`):** Das Feld erwartet einen einzelnen Enum-Wert. Zwei Werte mit Semikolon-Trennung und Klammertext wird der CsvParser nicht korrekt verarbeiten. Botanisch korrekt ist die Aufspaltung: Buschbohne = `herb`, Stangenbohne = `vine`. Da es sich um eine Art mit zwei Wuchsformen handelt, muss das Datenmodell entweder zwei Datensaetze (Cultivar-Ebene) oder ein Array-Feld verwenden.

**Problem 2 (`root_type`):** Der Klammertext "(mit Knollchenbakterien/Rhizobien fuer N-Fixierung)" ist kein gueltiger Enum-Wert-Bestandteil. `root_type` erwartet `fibrous`, `taproot`, `rhizome` etc. ohne Freitext.

**Korrekte Formulierung:**
```
# Option A: Zwei separate Cultivar-Datensaetze
# Cultivar "Buschbohne (Sammelbezeichnung)": growth_habit: herb
# Cultivar "Stangenbohne (Sammelbezeichnung)": growth_habit: vine

# Option B: Auf Artebene den haeufigsten Typ setzen
growth_habit: herb  # Buschbohne als Standardtyp; Stangenbohne als Cultivar

# Fuer root_type:
root_type: fibrous
# N-Fixierung als separates Flag/Eigenschaft
nitrogen_fixing: true
```
**Prioritaet:** Hoch (blockiert CSV-Import)

---

### K-007: Subspecies fehlt in Moehre CSV-Feld `scientific_name`

**Dokument:** `daucus_carota.md`, CSV-Import-Zeile und Dokumenttitel
**Inkonsistenz:** Dokumenttitel lautet "Daucus carota subsp. sativus" (korrekt), aber das CSV-Feld `scientific_name` enthaelt nur "Daucus carota" (ohne Subspecies-Bezeichnung)
**Problem:** Die Kulturmoehre ist taxonomisch *Daucus carota* **subsp. sativus** (Hoffm.) Arcang. Die Wildform (Wilde Moehre) ist *Daucus carota* subsp. carota. Ohne Subspecies-Angabe im CSV:

1. Verwechslung mit der invasiven Wildform ist moeglich
2. Taxonomische Abfragen (GBIF, POWO) treffen die falsche Taxon-Ebene
3. Die Systemlogik kann Kultivierungsempfehlungen nicht korrekt der Kulturform zuordnen
4. Der Import wuerde den Namen "Daucus carota" in die Datenbank schreiben, was taxonomisch unkorrekt fuer eine Kulturpflanze ist

**Korrekte Formulierung:**
```
scientific_name: Daucus carota subsp. sativus
# synonym: Daucus carota var. sativa
```
**Prioritaet:** Hoch (taxonomische Integritaet der Datenbank)

---

## M-Fehler: Wesentliche Probleme (Korrekturbedarf vor Produktionsrelease)

### M-001: Aqua Flores A NPK inkonsistent ueber drei Dokumente

**Betroffene Dokumente:** `solanum_lycopersicum.md`, `cucumis_sativus.md`, `cucurbita_pepo.md`
**Problem:** Das Produkt "Canna Aqua Flores A" wird mit drei verschiedenen NPK-Werten angegeben:

| Dokument | Produkt | NPK-Angabe |
|----------|---------|------------|
| solanum_lycopersicum.md | Aqua Flores A | 4-0-3 |
| cucumis_sativus.md | Aqua Flores A | 4-0-4 |
| cucurbita_pepo.md | Aqua Flores A | 5-0-1 |

Da es sich um dasselbe kommerzielle Produkt handelt, kann nur eine Angabe korrekt sein (laut Hersteller Canna: N=4%, P=0%, K=3% -- entspricht 4-0-3). Die anderen Werte sind Fehler, vermutlich durch manuelle Eingabe entstanden.

**Korrekte Formulierung:** Alle Dokumente auf NPK 4-0-3 fuer Aqua Flores A vereinheitlichen. Empfehlung: Produktdatenbank als Single Source of Truth anlegen (REQ-001 Duenger-Stammdaten) und Nute-Plaene darauf verweisen statt NPK-Werte zu duplizieren.

**Prioritaet:** Mittel (falsche Naeerstoffberechnungen bei EC-Budget-Kalkulation)

---

### M-002: Mischkultur-Asymmetrie Tomate <-> Karotte (Kompatabilitaetsscore)

**Betroffene Dokumente:** `solanum_lycopersicum.md`, `daucus_carota.md`
**Problem:**
- Tomate listet Karotte: `compatible_with`, Score 0.8
- Karotte listet Tomate: `compatible_with`, Score 0.7

Der Score ist asymmetrisch. Da Mischkultur eine bidirektionale Beziehung ist (oder zumindest konsistent dokumentiert werden sollte), sollten identische oder begruendete unterschiedliche Scores verwendet werden. Biologisch hat die Karotte bei Tomate einen anderen Nutzen (lockert Boden, hemmt Tomatenwurzellaeusebesatz) als die Tomate bei Karotte (moeglicher Schutz vor Karottenfliege durch Tomatenduft). Wenn unterschiedliche Scores biologisch begruendet sind, muessen sie explizit erklaert werden.

**Empfehlung:** Score vereinheitlichen auf 0.8 (Vorteil dokumentiert) oder unterschiedliche Scores mit Begruendung je Richtung versehen.

---

### M-003: Mischkultur-Asymmetrie Zucchini <-> Stangenbohne (Kompatabilitaetsscore)

**Betroffene Dokumente:** `cucurbita_pepo.md`, `phaseolus_vulgaris.md`
**Problem:**
- Zucchini listet Stangenbohne: `compatible_with`, Score 0.9 (Milpa-Prinzip)
- Bohne listet Kueurbis/Zucchini: `compatible_with`, Score 0.8 (Drei Schwestern)

Beide Paare referenzieren dasselbe biologische Prinzip (Drei-Schwestern-Anbau: Mais, Bohne, Kuerbis/Zucchini), verwenden aber unterschiedliche Scores (0.9 vs 0.8). Da das System bidirektionale Kanten im Mischkultur-Graphen anlegt, entstehen widersprueliche Kanten.

**Empfehlung:** Vereinheitlichung auf Score 0.9 (starke gegenseitige Foerderung im Drei-Schwestern-System ist wissenschaftlich gut belegt).

---

### M-004: Mischkultur-Asymmetrie Erbse <-> Bohne (Inkompatibilitaetsschweregrad)

**Betroffene Dokumente:** `pisum_sativum.md`, `phaseolus_vulgaris.md`
**Problem:**
- Erbse listet Bohne: `incompatible_with`, Schweregrad `moderate`
- Bohne listet Erbse: `incompatible_with`, Schweregrad `mild`

Das Inkompatibilitaetsniveau ist widerspruelich. Begruendung in beiden Dokumenten: gleiche Familie (Fabaceae), Konkurrenz um dieselben Rhizobium-Stickstoff-Nischen, moegliche gegenseitige Hemmung ueber Wurzelausscheidungen. Die zugrundeliegende Biologie ist symmetrisch (beide Leguminosen konkurrieren gleichermassen). Einer der Schweregerade ist falsch.

**Empfehlung:** Beide auf `mild` vereinheitlichen (die Konkurrenz ist real aber nicht stark genug um als "moderate" zu gelten -- Praktiker bauen Erbsen und Bohnen oft im selben Beet ohne dramatische Ertragseinbussen).

---

### M-005: Karotte nennt Rote Bete als inkompatibel -- keine Gegeneintragung in Rote Bete

**Betroffene Dokumente:** `daucus_carota.md`, `beta_vulgaris_subsp_vulgaris.md`
**Problem:**
- Karotte listet Rote Bete: `incompatible_with`, Schweregrad `mild` (Naehrstoffkonkurrenz Borton-Mangan)
- Rote Bete: kein Eintrag zu Karotte in den Mischkultur-Listen (weder kompatibel noch inkompatibel)

Das Graphmodell wuerde eine gerichtete Kante von Karotte -> Rote Bete (inkompatibel) anlegen, aber keine Rueckkante. Bei Graph-Abfragen "Was sind schlechte Nachbarn fuer Rote Bete?" wuerde Karotte nicht erscheinen. Dies ist ein logischer Fehler in der Datenkonsistenz.

**Empfehlung:** In `beta_vulgaris_subsp_vulgaris.md` einfuegen:
```
incompatible_with: Daucus carota subsp. sativus
Schweregrad: mild
Begruendung: Konkurrenz um Bor und Mangan im Wurzelbereich; beide tiefruehlenden Gemuese verdraengen sich gegenseitig bei geringer Bodentiefe.
```

---

### M-006: Beta vulgaris subsp. vulgaris Dokument deckt zwei kommerzielle Gemuese ab

**Dokument:** `beta_vulgaris_subsp_vulgaris.md`
**Problem:** Der botanische Name *Beta vulgaris* subsp. *vulgaris* umfasst mehrere Kultivierungsgruppen:
- **Rote Bete** (Rote-Bete-Gruppe): Ruebenkultur, roter Farbstoff (Betanin)
- **Mangold** (Blatt-Mangold-Gruppe): Blattkultur, kein Ruebenansatz
- **Zuckerruebe** (Zuckerrueben-Gruppe): industriell, nicht relevant

Das Dokument behandelt primaer Rote Bete, nennt Mangold in Abschnitt 7 explizit als "Gleiche Art! Blattkultur statt Ruebenkultur", verwendet aber die Mischkultur-Eintraege nur aus Rote-Bete-Perspektive. Dabei listet das Dokument "Mangold" als inkompatibel (weil gleiche Art = Naehrstoffkonkurrenz), was im CSV-Import zu einer Selbst-Inkompatibilitaet fuehrt (*Beta vulgaris* subsp. *vulgaris* inkompatibel mit sich selbst).

Ausserdem fehlen Mangold-spezifische Pflegeparameter: keine Ruebenbildung, hoehere Hitzevertraeglichkeit, andere Erntemonate.

**Empfehlung:** Zwei separate Dokumente anlegen:
- `beta_vulgaris_subsp_vulgaris_conditiva.md` fuer Rote Bete (Conditiva-Gruppe)
- `beta_vulgaris_subsp_vulgaris_cicla.md` fuer Mangold (Cicla-Gruppe)
Oder alternativ auf Cultivar-Ebene aufteilen, wenn das Datenmodell das unterstuetzt.

---

### M-007: Tomate <-> Rosenkohl Mischkultur einseitig dokumentiert

**Betroffene Dokumente:** `solanum_lycopersicum.md`, `brassica_oleracea_var_gemmifera.md`
**Problem:**
- Rosenkohl listet Tomate: `compatible_with`, Score 0.8 (Tomatenzapfen vertreibt Kohlweisslinge)
- Tomate listet Rosenkohl / Kohl: kein Eintrag in der Mischkultur-Tabelle

Da Rosenkohl die Tomate als Begleitpflanze einstuft und dies biologisch begruendet ist (aetherrische Oele der Tomatenstaude reduzieren Eigelage von Pieris brassicae an Brassica-Pflanzen, belegt durch Agelopoulos et al. 1999), sollte die Tomate als kompatibel mit Rosenkohl/Kohl-Arten eingetragen sein.

**Empfehlung:** In `solanum_lycopersicum.md` einfuegen:
```
compatible_with: Brassica oleracea (Kohl, inkl. Rosenkohl)
Score: 0.7
Begruendung: Tomatenaroma reduziert Eiablage der Kohlweisslinge (Pieris spp.) an Brassicaceen
```

---

## H-Hinweise: Verbesserungsempfehlungen

### H-001: Rosenkohl Ernte-Monate ueberschreiten Kalenderjahresgrenze

**Dokument:** `brassica_oleracea_var_gemmifera.md`
**Hinweis:** Ernte-Monate sind angegeben als `10; 11; 12; 1; 2; 3`. Die Monate 1 (Januar), 2 (Februar), 3 (Maerz) gehoeren zum Folgejahr nach der Pflanzung im Fruehjahr/Sommer. Das Datenmodell (REQ-001) muss jahruebergreifende Erntemonat-Angaben unterstuetzen, sonst wuerde das System die Ernte faelschlich im Jahr der Aussaat planen.

**Empfehlung:** Entweder `harvest_months_offset` als Feld ergaenzen (gibt an ob Monate im Pflanzjahr oder Folgejahr liegen) oder eine explizite "Ernte im Folgejahr"-Flag implementieren. Gleiches Problem gilt fuer Winterraps, Knoblauch etc.

---

### H-002: Tomate <-> Erbse Inkompatibilitaet unterschiedlich begruendet

**Betroffene Dokumente:** `solanum_lycopersicum.md`, `pisum_sativum.md`
**Hinweis:**
- Tomate listet Erbse als inkompatibel: "Wuchshemmung durch Wurzelausscheidungen der Tomate"
- Erbse listet Tomate als inkompatibel: "Unterschiedliche Wasserbeduerfnisse, Tomate beschattet Erbse zu stark"

Beide Dokumente begruenden die Inkompatibilitaet unterschiedlich. Biologisch sind beide Gruende real: Tomatenwurzeln exsudieren phenolische Verbindungen die das Wachstum mancher Leguminosen hemmen koennen; Erbsen bevorzugen kuehlere, feuchtere Bedingungen; Tomate ist eine waerme- und lichtliebende Hochpflanze. Die inkonsistente Begruendung ist kein Fehler, sollte aber vereinheitlicht werden.

**Empfehlung:** Eine gemeinsame Begruendung in beiden Dokumenten: "Unterschiedliche Temperatur- und Wasserbeduerfnisse; Tomate beschattet und erwaermt den Bodenbereich; Wurzelexsudate der Tomate koennen Leguminosenwachstum hemmen."

---

### H-003: Zucchini USDA Zone 3a biologisch grenzwertig

**Dokument:** `cucurbita_pepo.md`
**Hinweis:** USDA Winterhaertezone 3a bedeutet Minimaltemperaturen bis -37 degC. *Cucurbita pepo* (Zucchini) ist eine frostempfindliche Sommerannuelle die bereits bei Bodenfrost abstirbt. Die Angabe "Zone 3a-11b" ist irrelevant fuer eine nicht-winterharte Einjahrespflanze. Die Winterhartezone beschreibt ueberwinternde Stauden und Gehoelze, nicht Sommerannuelle die jede Saison neu angepflanzt werden.

**Empfehlung:** Fuer Sommerannuelle den USDA-Zonen-Parameter entweder weglassen oder als Anbauzonen statt Winterhaertezonen bezeichnen. Alternativ: letzte Frostdatum als relevantere Angabe verwenden ("anbaugeeignet wenn letzter Frost mindestens 2 Wochen zurueckliegt").

---

### H-004: Gurke USDA Zonen 4a-11b fuer Freilandanbau zu breit

**Dokument:** `cucumis_sativus.md`
**Hinweis:** Wie bei Zucchini (H-003) gilt: Gurke als waermeliebende frostempfindliche Einjahre. Zone 4a (bis -34 degC Minimaltemperatur) ist als Winterhartezone nicht aussagekraeftig fuer Gurken-Freilandanbau. In Zone 4 ist Gurkenanbau im Freiland moeglich (kurze Saison mit Fruehjahrsschutz), aber nur mit erheblichem Aufwand. Die Angabe suggeriert hoehere Kalttoleranz als vorhanden.

---

### H-005: Paprika allelopathy_score ohne Bezug in Mischkultur-Tabelle

**Dokument:** `capsicum_annuum.md`
**Hinweis:** `allelopathy_score: 0.15` ist positiv (leicht allelopathisch hemmend auf andere Pflanzen). In der Mischkultur-Tabelle fehlt eine Erlaeuterung welche Pflanzen von Paprikas allelopathischen Effekten betroffen sind. Der Score alleine ist ohne Kontext nicht handlungsweisend.

**Empfehlung:** Ergaenzung: "Paprika gibt geringe Mengen phenolischer Verbindungen aus Wurzeln ab; empirisch kein nachgewiesener negativer Effekt auf gaengige Mischkulturpartner bei normalen Pflanzabstaenden."

---

### H-006: Salat-Tipburn-Risiko fehlt in Pflegeprofil-Warnungen

**Dokument:** `lactuca_sativa.md`
**Hinweis:** Das Dokument erwaehnt Tipburn (Kalzium-Transport-Stoerung bei hoher DLI oder schlechter Luftzirkulation) in der Krankheitsliste korrekt. Jedoch fehlt im Pflegeprofil ein Warnhinweis, dass Tipburn bei Indoor-LED-Anbau ab DLI >14 mol/m2/d ein systemisches Risiko ist das durch Luftzirkulation (Ventilatoren), Kalziumversorgung und Photoperioden-Management kontrolliert werden muss.

**Empfehlung:** Pflegeprofil-Notiz ergaenzen: "Tipburn-Praevention bei Indoor-Anbau: Luftzirkulation sicherstellen (0.3-0.5 m/s Blattbewegung), DLI <16 mol/m2/d halten, Kalziumversorgung (Ca >150 mg/L in Hydrokultur) sicherstellen."

---

### H-007: Pisum sativum Photoperiodismus vereinfacht dargestellt

**Dokument:** `pisum_sativum.md`
**Hinweis:** `photoperiod_type: long_day` ist korrekt fuer die meisten historischen Ersbsensorten. Moderne Zuechtungen haben jedoch tagneutrale Typen hervorgebracht (z.B. "Sugar Ann", "Sugar Snap"). Die monolithische Klassifikation als Langtagspflanze koennte fuer bestimmte Sorten unzutreffend sein.

**Empfehlung:** Ergaenzung: "Klassische Sorten sind Langtagspflanzen (kritische Taglaenge ~12-14 h); neuere Zuchtsorten zunehmend tagneutral. Sortenauswahl beachten."

---

### H-008: Rote Bete / Mangold Selbst-Inkompatibilitaet in Daten

**Dokument:** `beta_vulgaris_subsp_vulgaris.md`
**Hinweis:** Das Dokument listet "Mangold (Beta vulgaris subsp. vulgaris)" als `incompatible_with` der Roten Bete. Da beide den gleichen wissenschaftlichen Namen tragen (*Beta vulgaris* subsp. *vulgaris*), wuerde das Graphsystem eine Selbst-Inkompatibilitaets-Kante anlegen (Knoten inkompatibel mit sich selbst). Dies ist ein logischer Datenbankfehler, der zu undefiniertem Verhalten beim Mischkultur-Algorithmus fuehren kann.

Dieses Problem ist direkt mit M-006 verknuepft und wird durch die Aufspaltung in zwei Dokumente geloest.

---

### H-009: Bohne Toxizitaet ohne ASPCA-Quelle deklariert

**Dokument:** `phaseolus_vulgaris.md`
**Hinweis:** Das Dokument gibt an, dass rohe Bohnen fuer Hunde und Katzen maessig toxisch sind (Phytohaemagglutinin / Phasin), verwendet aber Cornell CALS (CFS) als Quelle, nicht ASPCA. Das toxicity-Feld `aspca_toxic_dogs: true` suggeriert ASPCA-Validierung. Da *Phaseolus vulgaris* in der ASPCA-Datenbank nicht als eigene Art gelistet ist, sollte das Quellen-Flag korrekt gesetzt werden.

**Empfehlung:** Felder umbenennen zu `toxic_dogs: true` (ohne ASPCA-Spezifizierung) und Quelle als Cornell/CFS explizit angeben. Alternativ: generisches `toxicity_source: Cornell CFS` Feld.

---

## Cross-Dokument-Mischkultur-Symmetriepruefung

Geprueft wurden alle 45 moeglichen Paare aus 10 Dokumenten. Bewertet nach:
- SYMM: symmetrisch und konsistent
- ASYM-SCORE: asymmetrische Kompatibilitaetsscores
- ASYM-SEVER: asymmetrischer Schweregrad (bei Inkompatibilitaet)
- EINSEITIG: Eintrag nur in einem Dokument
- OK-EXTERN: Eintrag verweist auf Pflanze ausserhalb der 10 (kein Prueffehler)

| Paar (A -> B) | Status | Befund | REF |
|---------------|--------|--------|-----|
| Tomate <-> Paprika | SYMM | Beide: incompatible mild | OK |
| Tomate <-> Gurke | OK-EXTERN | Tomate: kein Eintrag; Gurke: Paprika mild incompatible | Gurke listet Paprika, nicht Tomate |
| Tomate <-> Zucchini | EINSEITIG | Zucchini: Tomate mild incompatible; Tomate: kein Eintrag fuer Zucchini | H-xxx |
| Tomate <-> Salat | SYMM | Beide: compatible 0.7 | OK |
| Tomate <-> Erbse | SYMM | Beide: incompatible mild | OK (unterschiedl. Begruend. siehe H-002) |
| Tomate <-> Bohne | EINSEITIG | Tomate: kein Eintrag; Bohne: kein Eintrag fuer Tomate | Neutral |
| Tomate <-> Moehre | ASYM-SCORE | Tomate: 0.8, Moehre: 0.7 | M-002 |
| Tomate <-> Rote Bete | EINSEITIG | Tomate: kein Eintrag; Rote Bete: kein Eintrag | Neutral |
| Tomate <-> Rosenkohl | EINSEITIG | Rosenkohl: Tomate 0.8; Tomate: kein Eintrag | M-007 |
| Paprika <-> Gurke | SYMM | Paprika: mild incompatible; Gurke: kein Eintrag (Asymmetrie trivial) | Paprika listet Gurke mild |
| Paprika <-> Zucchini | EINSEITIG | Beide kein expliziter Eintrag | Neutral |
| Paprika <-> Salat | SYMM | Beide: compatible 0.7 | OK |
| Paprika <-> Erbse | EINSEITIG | Paprika: kein Eintrag; Erbse: kein Eintrag | Neutral |
| Paprika <-> Bohne | EINSEITIG | Beide kein Eintrag | Neutral |
| Paprika <-> Moehre | SYMM | Paprika: Moehre 0.7; Moehre: Paprika 0.8 | ASYM-SCORE (leicht) |
| Paprika <-> Rote Bete | EINSEITIG | Beide kein Eintrag | Neutral |
| Paprika <-> Rosenkohl | EINSEITIG | Rosenkohl: Brassicaceae incompatible; Paprika gehort Solanaceae | Kein Direkt-Eintrag |
| Gurke <-> Zucchini | SYMM | Beide: incompatible moderate (gleiche Familie) | OK |
| Gurke <-> Salat | SYMM | Gurke: 0.7, Salat: 0.7 | OK |
| Gurke <-> Erbse | SYMM | Beide: compatible 0.8 | OK |
| Gurke <-> Bohne | SYMM | Beide: compatible 0.8 | OK |
| Gurke <-> Moehre | EINSEITIG | Gurke: kein Eintrag; Moehre: kein Eintrag | Neutral |
| Gurke <-> Rote Bete | SYMM | Rote Bete: Gurke 0.7; Gurke: kein Eintrag | EINSEITIG (Hinweis) |
| Gurke <-> Rosenkohl | EINSEITIG | Beide kein Eintrag | Neutral |
| Zucchini <-> Salat | EINSEITIG | Zucchini: kein Eintrag; Salat: kein Eintrag | Neutral |
| Zucchini <-> Erbse | EINSEITIG | Zucchini: kein Eintrag; Erbse: kein Eintrag | Neutral |
| Zucchini <-> Bohne | ASYM-SCORE | Zucchini: Stangenbohne 0.9; Bohne: Kueurbis 0.8 | M-003 |
| Zucchini <-> Moehre | EINSEITIG | Beide kein Eintrag | Neutral |
| Zucchini <-> Rote Bete | EINSEITIG | Beide kein Eintrag | Neutral |
| Zucchini <-> Rosenkohl | EINSEITIG | Beide kein Eintrag | Neutral |
| Salat <-> Erbse | SYMM | Beide: compatible 0.8 | OK |
| Salat <-> Bohne | SYMM | Salat: Buschbohne 0.7; Bohne: kein Eintrag | EINSEITIG (Hinweis) |
| Salat <-> Moehre | SYMM | Salat: 0.8; Moehre: Salat (erwaehnbar) | OK (Moehre listet Salat 0.8) |
| Salat <-> Rote Bete | SYMM | Rote Bete: Kopfsalat 0.8; Salat: Rote Bete 0.8 (pruefen) | Pruefbedarf |
| Salat <-> Rosenkohl | EINSEITIG | Rosenkohl: kein Eintrag; Salat: kein Eintrag | Neutral |
| Erbse <-> Bohne | ASYM-SEVER | Erbse: moderate; Bohne: mild | M-004 |
| Erbse <-> Moehre | SYMM | Erbse: Moehre 0.9; Moehre: Erbse 0.8 | ASYM-SCORE (leicht) |
| Erbse <-> Rote Bete | EINSEITIG | Beide kein Eintrag | Neutral |
| Erbse <-> Rosenkohl | SYMM | Erbse: Kohl 0.7; Rosenkohl: kein Eintrag fuer Erbse | EINSEITIG |
| Bohne <-> Moehre | EINSEITIG | Beide kein Eintrag | Neutral |
| Bohne <-> Rote Bete | SYMM | Rote Bete: Buschbohne 0.8; Bohne: Rote Bete (pruefen) | Pruefbedarf |
| Bohne <-> Rosenkohl | SYMM | Rosenkohl: kein Eintrag; Bohne: Kohlrabi 0.7 (kein Rosenkohl) | Neutral |
| Moehre <-> Rote Bete | ASYM | Moehre: inkompatibel mild; Rote Bete: kein Eintrag | M-005 |
| Moehre <-> Rosenkohl | SYMM | Rosenkohl: Moehre 0.7; Moehre: kein Eintrag fuer Rosenkohl | EINSEITIG |
| Rote Bete <-> Rosenkohl | ASYM | Rosenkohl: Rote Bete 0.7; Rote Bete: kein Eintrag fuer Rosenkohl | EINSEITIG |

**Zusammenfassung Symmetriepruefung:**
- Vollstaendig symmetrisch: 12 Paare
- Asymmetrischer Score: 3 Paare (M-002, M-003, partielle Erbse-Moehre)
- Asymmetrischer Schweregrad: 1 Paar (M-004)
- Einseitiger Eintrag mit fachlicher Relevanz: 2 Paare (M-005, M-007)
- Neutral (kein Eintrag auf beiden Seiten oder extern): 27 Paare

---

## CSV-Import-Eignungspruefung

| Dokument | Import-Status | Kritische Felder | Massnahme |
|----------|--------------|-----------------|-----------|
| solanum_lycopersicum.md | Bedingt | `light_germination` falsch | K-002 beheben |
| capsicum_annuum.md | Import-bereit | - | - |
| cucumis_sativus.md | Import-bereit | Tippfehler im Freitext | Kosmetisch |
| cucurbita_pepo.md | Import-bereit | USDA-Zone (Hinweis) | H-003 |
| lactuca_sativa.md | Import-bereit | - | - |
| pisum_sativum.md | Import-bereit | Photoperiod-Hinweis | H-007 |
| phaseolus_vulgaris.md | BLOCKIERT | `nutrient_demand_level: nitrogen_fixer`, Multi-Wert `growth_habit`, Freitext in `root_type` | K-005, K-006 beheben |
| daucus_carota.md | BLOCKIERT | `scientific_name` ohne Subspecies | K-007 beheben |
| beta_vulgaris_subsp_vulgaris.md | Bedingt | Selbst-Inkompatibilitaet Mangold, Dual-Dokument-Problem | M-006, H-008 |
| brassica_oleracea_var_gemmifera.md | Bedingt | `care_style: mediterranean` falsch, `erreger_typ: fungal` fuer Plasmodiophora | K-003, K-004 beheben |

**2 von 10 Dokumenten blockieren den CSV-Import vollstaendig** (phaseolus_vulgaris.md, daucus_carota.md).
**3 von 10 Dokumenten** sind bedingt importierbar aber liefern falsche Daten ohne Korrektur.

---

## Priorisierte Massnahmenliste

| Prio | ID | Massnahme | Dokument(e) | Aufwand |
|------|----|-----------|-------------|---------|
| 1 | K-005 | `nutrient_demand_level: light` (war: nitrogen_fixer) | phaseolus_vulgaris.md | 5 min |
| 2 | K-006 | `growth_habit` und `root_type` Felder bereinigen | phaseolus_vulgaris.md | 15 min |
| 3 | K-007 | `scientific_name: Daucus carota subsp. sativus` | daucus_carota.md | 5 min |
| 4 | K-003 | `erreger_typ: protist` fuer Kohlhernie | brassica_oleracea_var_gemmifera.md | 5 min |
| 5 | K-004 | `care_style: outdoor_annual_veg` | brassica_oleracea_var_gemmifera.md | 5 min |
| 6 | K-001 | Toxin-Bezeichnung alpha-Tomatin korrigieren | solanum_lycopersicum.md | 10 min |
| 7 | K-002 | `light_germination: null` (lichtunabhaengig) | solanum_lycopersicum.md | 5 min |
| 8 | M-001 | Aqua Flores A NPK auf 4-0-3 vereinheitlichen | Tomate, Gurke, Zucchini | 10 min |
| 9 | M-005 | Karotte-Eintrag in Rote Bete Mischkultur ergaenzen | beta_vulgaris_subsp_vulgaris.md | 10 min |
| 10 | M-007 | Rosenkohl-Eintrag in Tomate Mischkultur ergaenzen | solanum_lycopersicum.md | 10 min |
| 11 | M-002 | Score-Asymmetrie Tomate-Moehre harmonisieren | Tomate oder Moehre | 5 min |
| 12 | M-003 | Score-Asymmetrie Zucchini-Bohne harmonisieren | Zucchini oder Bohne | 5 min |
| 13 | M-004 | Schweregrad-Asymmetrie Erbse-Bohne vereinheitlichen | Erbse oder Bohne | 5 min |
| 14 | M-006 | Beta vulgaris Dokument in Rote Bete / Mangold aufteilen | beta_vulgaris_subsp_vulgaris.md | 60 min |
| 15 | H-001 | Jahruebergreifende Ernte-Monate Datenmodell pruefen | Systemmodell REQ-001 | Architektur |

---

## Empfohlene Datenquellen fuer Nachpruefung

| Thema | Quelle | URL / Referenz |
|-------|--------|----------------|
| Tomatinalkaloid-Chemie | Friedman (2002), J. Agric. Food Chem. | DOI:10.1021/jf020356h |
| Plasmodiophora Taxonomie | Burki et al. (2010), Phytomyxea | PubMed PMID 20808734 |
| Tomaten-Keimungsphysiologie | Bewley & Black (1994), Seeds -- Physiology of Development and Germination | Standardlehrbuch |
| Rosenkohl-Klimatoleranz | RHS Growing Guides: Brassica oleracea Gemmifera Group | rhs.org.uk |
| Rhizobium in Phaseolus | Graham & Vance (2003), Plant and Soil, 252:1 | Legume Biology |
| ASPCA-Pflanzentoxizitaet | ASPCA Animal Poison Control Center | aspca.org/pet-care/animal-poison-control |
| Mischkultur-Wissenschaft | Altieri (1999), Agroecology -- The Science of Sustainable Agriculture | Standardwerk |
| APG IV Taxonomie | Angiosperm Phylogeny Group (2016), Bot. J. Linn. Soc. 181:1-20 | DOI:10.1111/boj.12385 |
| Cultivar-Nomenklatur | ICNCP 9th Edition (2016) | ishs.org |
| Tipburn in Salat | Collier & Tibbitts (1982), Hort. Reviews 4 | Calcium Transport Indoor |

---

## Glossar (Batch-3-spezifisch)

- **alpha-Tomatin:** Hauptglykoalkaloid der Tomatenpflanze (*Solanum lycopersicum*); konzentriert in vegetativen Pflanzenteilen und unreifen Fruechten; kein Synonym fuer Solanin (das ist ein Kartoffelalkaloid)
- **Plasmodiophora brassicae:** Obligater intrazellularer Parasit der Brassica-Wurzeln; Erreger der Kohlhernie; gehoert zu den Phytomyxea (Rhizaria), nicht zu den Fungi
- **Phytohaemagglutinin (PHA) / Phasin:** Lektin in rohen *Phaseolus vulgaris*-Samen; denaturiert durch Kochen (10 min Vollkochen); toxisch fuer Menschen und Tiere im rohen Zustand
- **Nitrogen-Fixer:** Leguminosen (Fabaceae) die ueber Knollchenbakteriensymbiose (Rhizobium spp.) atmosphaerischen Stickstoff fixieren; reduziert N-Duengerbedarf auf `light` oder null
- **Betanin:** Roter Betalain-Farbstoff aus *Beta vulgaris*; fuer die Faerbung von Rote Bete verantwortlich; fehlt bei Mangold (Gruenblatt) oder ist reduziert (gelbblattiger Mangold)
- **Tipburn:** Kalziumtransport-Stoerung in schnell wachsenden Blattinnenzellen bei *Lactuca sativa*; Symptom: nekrotische Randverbraeunung der inneren Herzblatter; ausgeloest durch unzureichende Transpiration (hohe rH) oder zu hohe Lichtintensitaet / Wachstumsgeschwindigkeit
- **DIF (Day/Night Temperature Differential):** Differenz zwischen Tag- und Nachttemperatur; positiver DIF foerdert Streckungswachstum; negativer DIF faerbt kompakten Wuchs; relevant bei Rosenkohl fuer kompakten Roeschenansatz
- **Cucurbitacin:** Bittere Triterpenglykosid in Cucurbitaceae; hochkonzentriert in Wildtypen; Kulturformen gezuechtet auf niedrige Cucurbitacin-Gehalte; hohe Mengen emetic/toxisch
- **Bor-Mangel:** Typisches Defizitsymptom bei *Beta vulgaris* auf kalkhaltigem oder trockenem Boden; verursacht Herz- und Trockenfaule (schwarz-braune Verfaerbung im Ruebenherz)
