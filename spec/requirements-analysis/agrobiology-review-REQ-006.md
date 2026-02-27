# Agrarbiologisches Anforderungsreview: REQ-006 Aufgabenplanung

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Indoor-Anbau / Zimmerpflanzen / Hydroponik / Outdoor (ergaenzend)
**Analysiertes Dokument:** `spec/req/REQ-006_Aufgabenplanung.md` (Version 2.0)
**Kontext-Dokumente:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-007, REQ-010, REQ-013, REQ-018

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Pflanzenphysiologie (HST, Stress, Auxin) groesstenteils korrekt; einige Ungenauigkeiten bei Recovery-Zeiten und Hormon-Zusammenhaengen |
| Indoor-Vollstaendigkeit | 4/5 | Cannabis und Indoor-Nutzpflanzen gut abgedeckt; Zimmerpflanzen-Workflows und Hydroponik-Wartung fehlen |
| Zimmerpflanzen-Abdeckung | 1/5 | Kein einziges System-Template fuer Zimmerpflanzen vorhanden; Anbaukontext dekorative Innenraumbegruenung komplett ignoriert |
| Hydroponik-Tiefe | 2/5 | Substrate werden benannt (soil, hydro, coco), aber hydroponik-spezifische Wartungs-Tasks fehlen als Built-in-Workflows |
| Messbarkeit der Parameter | 4/5 | Stress-Score, Recovery-Zeiten, Karenzzeiten gut quantifiziert; einige qualitative Angaben verbleiben |
| Praktische Umsetzbarkeit | 4/5 | Technisch fundiert; artspezifische Recovery-Faktoren sind ein sehr guter Ansatz; Datengrundlage fuer einige Faktoren aber duenn |

REQ-006 ist ein bemerkenswert durchdachtes Dokument, das pflanzenphysiologische Grundlagen (Auxin-Dominanz, kumulativer Stress, Hormon-Akkumulation) korrekt in Software-Anforderungen uebersetzt. Die Differenzierung zwischen Early-Flowering (Stretch) und Mid/Late-Flowering fuer HST-Validierung zeigt echtes Fachverstaendnis. Die groesste Schwaeche liegt in der starken Cannabis-Zentrierung: Das System heisst "Kamerplanter" (Zimmerpflanzen), aber REQ-006 enthaelt keinen einzigen Zimmerpflanzen-Workflow. Hydroponik-spezifische Wartungsroutinen fehlen als System-Templates, obwohl REQ-014 (Tankmanagement) explizit referenziert wird.

---

## F -- Fachlich Falsch: Sofortiger Korrekturbedarf

### F-001: Foliar-Feeding-Tageszeit-Empfehlung "lights_off" ist fachlich uebersimplifiziert

**Anforderung:** "lights_off: Fuer Foliar-Feeding (UV + nasses Blatt = Verbrennungen)." (`REQ-006_Aufgabenplanung.md`, Zeile 558)
**Problem:** Die Begruendung ist pflanzenphysiologisch unvollstaendig und teilweise irrelevant. Der Hauptgrund fuer Foliar-Feeding bei ausgeschaltetem Licht ist nicht UV-Verbrennung (die meisten Indoor-LED-Lampen emittieren kaum UV), sondern:
1. **Stomata-Oeffnung:** Viele Pflanzen oeffnen Stomata nachts (CAM-Pflanzen) oder in den fruehen Morgenstunden (C3-Pflanzen). Die optimale Foliar-Aufnahme haengt vom Stomata-Status ab.
2. **Verdunstungsrate:** Bei eingeschalteter Beleuchtung trocknet die Blattoberflaechenfeuchte zu schnell, was die Aufnahme reduziert und Salzrueckstaende hinterlaesst.
3. **Phototoxizitaet:** Manche Foliar-Produkte (insbesondere Oele wie Neem) koennen bei hoher PPFD phototoxisch wirken -- das ist korrekt, aber nicht UV-spezifisch.
4. **VPD-Einfluss:** Bei Lights-Off ist VPD typischerweise niedriger, was die Blattbenetzung laenger aufrechterhaelt.

**Korrekte Formulierung:**
```
"lights_off: Fuer Foliar-Feeding. Gruende: (1) Langsamere Verdunstung erhoet
Kontaktzeit und Aufnahme, (2) Kein Risiko fuer Phototoxizitaet bei oelhaltigen
Produkten (Neem, Mineraloel), (3) Niedrigerer VPD verlaengert Blattbenetzung.
Bei C3-Pflanzen alternativ: fruehe Morgenstunden (Stomata maximal geoeffnet)."
```
**Gilt fuer Anbaukontext:** Indoor / Gewaechshaus

### F-002: Kartoffel als "Nachtschattengewaechs" im Recovery-Faktor falsch kategorisiert

**Anforderung:** "potato: 0.6 -- Robust, aber langsamer als Nachtschattengewaechse" (`REQ-006_Aufgabenplanung.md`, Zeile 708)
**Problem:** Kartoffel (Solanum tuberosum) IST ein Nachtschattengewaechs (Solanaceae). Die Formulierung "langsamer als Nachtschattengewaechse" impliziert, dass Kartoffel kein Nachtschattengewaechs sei. Korrekt ist: Kartoffel regeneriert langsamer als andere Solanaceae-Kulturpflanzen (Tomate, Paprika), da der Fokus auf unterirdischem Knollenwachstum liegt und oberirdisches HST die Assimilat-Verteilung stoert.
**Korrekte Formulierung:**
```python
'potato': 0.6,  # Langsamer als andere Solanaceae (Tomate, Paprika),
                 # da Assimilat-Prioriierung auf Knollenbildung liegt
```
**Gilt fuer Anbaukontext:** Outdoor / Indoor

### F-003: Transplanting "abends (niedrige VPD)" ist pflanzenphysiologisch ungenau

**Anforderung:** "Tageszeit-Empfehlung: Transplanting abends (niedrige VPD)" (`REQ-006_Aufgabenplanung.md`, Zeile 66)
**Problem:** VPD ist abends nicht zwingend niedrig -- es haengt von Temperatur und Luftfeuchtigkeit ab. In vielen Indoor-Setups ist VPD bei Lights-Off sogar HOEHER, wenn die Temperatur faellt und Luftfeuchtigkeit nicht aktiv gesteigert wird (VPD haengt ueberproportional von Blatttemperatur ab). Der korrekte Grund fuer abendliches Transplanting ist:
1. **Reduzierte Transpiration:** Ohne Licht wird kaum transpiriert, was Welkestress nach dem Umsetzen minimiert.
2. **Naechtliche Erholung:** Die Pflanze hat eine volle Dunkelperiode Zeit, um Wurzel-Boden-Kontakt herzustellen, bevor Licht die Transpiration antreibt.
3. **Turgor-Erhalt:** Ohne Lichtdruck bleibt der Turgor hoch.

**Korrekte Formulierung:**
```
"Transplanting abends oder bei Lights-Off: Reduzierte Transpiration waehrend der
Dunkelperiode minimiert Welkestress. Die Pflanze hat eine volle Nacht fuer
Wurzel-Substrat-Kontakt, bevor Licht die Transpiration antreibt."
```
**Gilt fuer Anbaukontext:** Indoor / Gewaechshaus

### F-004: Tomate wird als "Topping"-Kandidat gefuehrt, obwohl Ausgeizen die korrekte Technik ist

**Anforderung:** Topping-species_notes: "ACHTUNG: Tomaten werden AUSGEGEIZT (Seitentriebe entfernen), nicht getoppt." (`REQ-006_Aufgabenplanung.md`, Zeile 883-884)
**Problem:** Die Warnung selbst ist korrekt und wertvoll, aber sie steht im Widerspruch zur Platzierung: Tomaten befinden sich unter den Best-Practices fuer "Topping" und haben einen Recovery-Faktor fuer Topping (0.4). Wenn Tomaten praxisrelevant NICHT getoppt werden sollen (ausser Buschtomaten), sollte das System fuer Stabtomaten (indeterminate types) gar kein Topping-Task anbieten, sondern "Ausgeizen" als eigene Task-Kategorie fuehren. Ausgeizen ist biologisch fundamental anders als Topping: Topping entfernt die Apikaldominanz (Auxin-Quelle), Ausgeizen entfernt Seitenmeristeme (Auxin-Senken). Die Hormonreaktion ist gegensaetzlich.

**Korrekte Formulierung:** Ausgeizen (sucker removal) sollte als eigenstaendige Task-Kategorie mit eigener Beschreibung und eigenen Recovery-Parametern definiert werden:
```python
'ausgeizen': {
    'best_timing': 'Vegetative Phase, woechentlich ab 3. Rispe',
    'steps': [
        '1. Identifiziere Geiztriebe in Blattachseln',
        '2. Ausbrechen bei < 5 cm Laenge (Handabbruch)',
        '3. Bei > 5 cm: Schere verwenden',
    ],
    'recovery': '0-1 Tag (niedriger Stress)',
    'stress_level': 'low',  # nicht 'high' wie Topping!
    'species_notes': {
        'tomato_indeterminate': 'Standard-Pflegemassnahme, kein HST',
        'tomato_determinate': 'NICHT ausgeizen -- Buschtomaten brauchen Seitentriebe',
    }
}
```
**Gilt fuer Anbaukontext:** Indoor / Outdoor / Gewaechshaus

---

## U -- Unvollstaendig: Wichtige Aspekte fehlen

### U-001: Keine System-Templates fuer Zimmerpflanzen-Pflege

**Anbaukontext:** Zimmerpflanzen (dekorative Innenraumbegruenung)
**Fehlende Templates:**
- **Umtopf-Workflow:** Saisonaler Umtopf-Zyklus (Fruehjahr) mit Substrat-Wechsel, Wurzelschnitt, Drainageschicht
- **Ueberwinterungs-Workflow:** Ruhephasen-Management fuer Kakteen, Sukkulenten, Zitruspflanzen (Temperatur senken, Giessen reduzieren, Duenger stoppen)
- **Orchideen-Pflege-Workflow:** Spezifischer Zyklus fuer Phalaenopsis (Duengen waehrend Wachstum, Temperatur-Drop fuer Bluete-Induktion, Wurzelschnitt nach Bluete)
- **Vermehrungs-Workflow Zimmerpflanzen:** Stecklinge (Monstera, Pothos), Teilung (Calathea, Farne), Ableger (Chlorophytum, Pilea)
- **Saisonale Duengungsanpassung:** Sommerdungung (aktiv) vs. Winterpause (kein Duenger) mit automatischer Umschaltung

**Begruendung:** Das Projekt heisst "Kamerplanter" (Zimmerpflanzen). Die aktuelle Template-Bibliothek fokussiert ausschliesslich auf Nutzpflanzen (Cannabis, Tomaten, Kartoffeln, Beerensstraeucher). Dies ist die groesste inhaltliche Luecke im Dokument.

**Formulierungsvorschlag fuer System-Templates:**
```
**Zimmerpflanzen-Templates (Built-in):**
- **Tropische Gruenpflanze (Standard):** Giessen nach Substratfeuchte,
  monatlich duengen Maerz-Oktober, Blattreinigung quartalsweise
- **Orchidee (Phalaenopsis):** Tauchbad woechentlich, Orchideenduenger
  alle 2 Wochen, Temperatur-Drop 5 Grad fuer 4 Wochen zur Bluete-Induktion
- **Kaktus/Sukkulente:** Minimalbewesserung, Winterruhe Oktober-Februar
  (kalt, trocken, kein Duenger), Umtopfen alle 2-3 Jahre
- **Calathea/Marante:** Erhoete Luftfeuchte (>60% rH), destilliertes
  Wasser, regelmaessige Schaedlingskontrolle (Spinnmilben)
```

### U-002: Hydroponik-spezifische Wartungs-Workflows fehlen als System-Templates

**Anbaukontext:** Hydroponik/Soilless
**Fehlende Workflows:**
- **Naehrloesung-Wechsel:** Komplettwechsel alle 7-14 Tage mit EC/pH-Messung, Reservoir-Reinigung, Frisch-Ansatz
- **pH/EC-Kalibrierung:** Woechentliche Kalibrierung der Sonden mit Referenzloesungen
- **Wurzelinspektion:** Regelmaessige Kontrolle auf Pythium, Verfaerbungen, Algenwachstum
- **System-Reinigung:** Leitungen, Pumpen, Tropfer spuelen (H2O2 oder enzymatisch)
- **Algen-Praevention:** Lichtausschluss pruefen, Reservoir-Abdeckung kontrollieren

**Begruendung:** REQ-014 (Tankmanagement) wird in den Abhaengigkeiten als "HOCH" fuer automatische Wartungs-Tasks referenziert (Zeile 1462), aber kein konkretes Hydroponik-Wartungs-Template ist definiert. In der Hydroponik ist regelmaessige Systemwartung ueberlebenswichtig fuer die Pflanzen -- ein vergessener Naehrloesung-Wechsel kann innerhalb von Tagen zu Totalverlust fuehren.

### U-003: Trigger-Typ "GDD-based" (Growing Degree Days) fehlt

**Anbaukontext:** Indoor / Outdoor
**Fehlender Trigger:** REQ-003 definiert GDD (Gradtagsummen) als zentralen Parameter fuer Phasenuebergaenge. REQ-006 bietet jedoch keinen Trigger-Typ `gdd_threshold`, der Tasks basierend auf akkumulierten Waermeeinheiten ausloest.

**Begruendung:** Viele kulturtechnische Massnahmen (insbesondere Outdoor) orientieren sich an GDD statt an Kalendertagen:
- Kartoffel-Haeufelung bei GDD 150, 300, 450 (nicht "Tag 14, 28, 42")
- Maisernte-Vorbereitung bei GDD 2500-2700
- Pflanzenschutz-Timing bei artspezifischen GDD-Schwellen
- Insekten-Schlupftermine basieren auf GDD (Traubenwickler, Apfelwickler)

**Formulierungsvorschlag:**
```python
# Neuer Trigger-Typ
trigger_type: Literal[..., 'gdd_threshold']
gdd_threshold: Optional[float]  # Gradtagsumme ab Pflanzung/Phasenstart
gdd_base_temperature: Optional[float]  # Basistemperatur (artspezifisch, z.B. 10 Grad C fuer Mais)
```

### U-004: Keine Beruecksichtigung von Mondkalender/Biorhythmus (optional, aber relevant fuer Zielgruppe)

**Anbaukontext:** Outdoor / Zimmerpflanzen
**Fehlend:** Viele Gaertner (insbesondere im biologisch-dynamischen Anbau und bei Zimmerpflanzen-Enthusiasten) planen nach Mondphasen:
- Frucht-Tage (Feuerzeichen): Ernte
- Wurzel-Tage (Erdzeichen): Umtopfen
- Blatt-Tage (Wasserzeichen): Blattreinigung, Giessen
- Bluete-Tage (Luftzeichen): Schnitt fuer Bluete

**Begruendung:** Obwohl die wissenschaftliche Evidenz fuer Mondeinfluss auf Pflanzenwachstum schwach ist, nutzt ein signifikanter Teil der Zielgruppe diese Planung. Als **optionaler** Trigger-Typ waere dies ein starkes Feature fuer User-Engagement.

**Formulierungsvorschlag (als optionales Feature):**
```python
# Optional: Biorhythmus-Trigger (User-konfigurierbar, NICHT als wissenschaftlich belegt markieren)
trigger_type: Literal[..., 'lunar_calendar']
lunar_phase: Optional[Literal['new_moon', 'waxing', 'full_moon', 'waning']]
lunar_element: Optional[Literal['fire', 'earth', 'air', 'water']]
```

### U-005: Fehlende Task-Kategorie "Observation/Monitoring" (Beobachtungs-Tasks)

**Anbaukontext:** Alle
**Fehlende Kategorie:** Die Task-Kategorien (Zeile 43-51) umfassen Training, Pruning, Transplanting, Feeding, IPM, Harvest, Maintenance -- aber keine dedizierten **Beobachtungs-Tasks**. Regelmaessige Pflanzenkontrolle (Blattkontrolle, Wachstumsmessung, Fotodokumentation des Fortschritts, pH/EC-Ablesung) ist eine der wichtigsten Taetigkeiten, die oft vergessen wird.

**Formulierungsvorschlag:**
```python
# Neue Kategorie
'observation': 'Regelmaessige Kontrolle: Wachstumsmessung, Blattkontrolle,
               pH/EC-Ablesung, Foto-Fortschrittsdokumentation, Symptom-Check'
```
Dies verbindet sich mit REQ-010 (IPM-Inspektionen), geht aber darueber hinaus: Nicht jede Beobachtung ist ein IPM-Event.

### U-006: Outdoor-spezifische Workflows unterrepraesentiert

**Anbaukontext:** Outdoor
**Fehlende Templates:**
- **Frostschutz-Workflow:** Wetterbasierter Trigger bei Frostwarnung -> Abdeckung, Vlies, Einholen
- **Abhaertungs-Workflow (Hardening Off):** 7-14 Tage gestaffelter Uebergang Indoor -> Outdoor
- **Rasenpflege/Gruenduengung:** Einsaat, Mulchen, Unterfraesen
- **Obstbaum-Jahreszyklus:** Winterschnitt -> Fruehjahrskontrolle -> Ausduenung -> Ernte -> Herbstschnitt
- **Saisonende-Workflow:** Beete raeumen, Bodenanalyse, Gruenduengung einsaeen, Werkzeug einlagern

**Begruendung:** REQ-006 definiert nur "Kartoffel-Haeufelung" und "Beerensstraeucher-Schnitt" als Outdoor-Templates. Der Bereich ist stark unterrepraesentiert gegenueber dem umfangreichen Indoor/Cannabis-Fokus.

### U-007: Fehlende Wechselwirkung zwischen Task-Planung und Umgebungssteuerung (REQ-018)

**Anbaukontext:** Indoor
**Fehlend:** REQ-018 definiert phasengebundene Aktor-Profile und VPD-Steuerung. REQ-006 definiert Tasks wie "Switch zu 12/12 Licht" (Zeile 1507), die de facto eine Aktorsteuerung-Aktion sind. Es fehlt eine klare Schnittstelle:
- Soll der Task "Licht umstellen" einen Aktor-Befehl ausloesen (REQ-018)?
- Oder ist der Task nur ein Reminder fuer manuelle Umstellung?
- Was passiert, wenn ein phasengebundenes Profil (REQ-018) automatisch umschaltet -- wird der korrespondierende Task dann automatisch als "completed" markiert?

**Formulierungsvorschlag:**
```
Task-Aktor-Integration:
- Tasks koennen optional mit Aktor-Aktionen (REQ-018) verknuepft sein
- Bei automatischer Aktor-Ausfuehrung: Task automatisch als 'completed' markieren
- Bei manueller Aktor-Steuerung: Task als Reminder generieren
- Konflikterkennung: Task "Licht 18/6" + Phase-Profil "12/12" = Warnung
```

### U-008: Stress-Recovery ist nicht temperaturabhaengig modelliert

**Anbaukontext:** Indoor / Gewaechshaus
**Fehlend:** Die Recovery-Zeiten nach HST sind temperaturabhaengig. Bei hoeheren Temperaturen laeuft der Metabolismus schneller, die Kallusbildung ist beschleunigt:
- 25-28 Grad C: Optimale Recovery (Basis-Wert)
- 18-22 Grad C: Recovery um 30-50% verlaengert
- >32 Grad C: Recovery verlaengert durch Hitzestress-Ueberlagerung

**Formulierungsvorschlag:**
```python
# Temperatur-Modifikator fuer Recovery-Zeit
TEMPERATURE_RECOVERY_MODIFIERS = {
    (15, 20): 1.5,   # Kuehle Bedingungen: 50% laengere Recovery
    (20, 25): 1.2,   # Unter Optimum: 20% laenger
    (25, 28): 1.0,   # Optimal
    (28, 32): 1.1,   # Leichter Hitzestress
    (32, 40): 1.4,   # Hitzestress: 40% laenger
}
```

---

## P -- Zu Ungenau: Praezisierung noetig

### P-001: Recovery-Zeiten "Cannabis 7d, Tomaten 2-3d, Paprika 5d" ohne Differenzierung nach HST-Typ

**Vage Anforderung:** "Stress-Recovery: Artspezifische Recovery-Zeiten (Cannabis 7d, Tomaten 2-3d, Paprika 5d)" (Zeile 61)
**Problem:** Die Freitext-Angabe im Business Case suggeriert eine flat Recovery-Zeit pro Art, waehrend der Code (BASE_RECOVERY_DAYS + SPECIES_RECOVERY_FACTORS) dies differenziert modelliert. Die Textbeschreibung sollte mit dem Code konsistent sein.
**Messbare Alternative:**
```
Recovery = BASE_RECOVERY_DAYS[hst_type] * SPECIES_RECOVERY_FACTORS[species_type]
Beispiel: Topping Cannabis = 7 * 1.0 = 7 Tage
Beispiel: Topping Tomate = 7 * 0.4 = 2.8 Tage (gerundet: 3 Tage)
Beispiel: Supercropping Cannabis = 5 * 1.0 = 5 Tage
```

### P-002: "herb: 0.5 -- Basilikum, Minze" als Kategorie ist taxonomisch unscharf

**Vage Anforderung:** "herb: 0.5 -- Basilikum, Minze -- schnelle Regeneration" (Zeile 705)
**Problem:** "herb" ist keine taxonomisch sinnvolle Gruppierung fuer Recovery-Faktoren. Basilikum (Ocimum basilicum, Lamiaceae) und Minze (Mentha spp., Lamiaceae) gehoeren zur selben Familie, aber ein "herb" wie Rosmarin (Rosmarinus officinalis, verholzend) regeneriert deutlich langsamer als kraetiges Basilikum. Die Kategorie sollte entweder auf Familienebene (Lamiaceae) oder auf Wuchsform (krautig-einjaerig vs. verholzend-mehrjaehrig) differenzieren.
**Messbare Alternative:**
```python
SPECIES_RECOVERY_FACTORS = {
    'cannabis':              1.0,
    'tomato':                0.4,
    'pepper':                0.7,
    'cucumber':              0.5,
    'herb_annual':           0.4,    # Basilikum, Koriander (krautig, einjaerig)
    'herb_perennial_soft':   0.6,    # Minze, Oregano (krautig, mehrjaehrig)
    'herb_perennial_woody':  0.9,    # Rosmarin, Lavendel (verholzend)
    'potato':                0.6,
    'berry':                 0.8,
    'default':               1.0,
}
```

### P-003: Kumulativer Stress-Score Schwellwert 0.7 ohne wissenschaftliche Begruendung

**Vage Anforderung:** "Kumulativer Stress-Score ueber 14-Tage-Fenster mit Warnung ab Score >0.7" (Zeile 790-796)
**Problem:** Der Schwellwert 0.7 und das 14-Tage-Fenster sind plausible Schaetzwerte, aber nicht literaturbasiert. Die Stress-Weights (topping: 0.3, transplant: 0.35, etc.) sind ebenso geschaetzt. Dies ist akzeptabel fuer einen ersten Entwurf, sollte aber als konfigurierbar und empirisch zu verfeinern markiert werden.
**Praezisierung:**
```python
# Diese Werte sind initiale Schaetzungen und sollten ueber Nutzerfeedback
# und Ergebnisdaten kalibriert werden. Der Schwellwert 0.7 basiert auf
# Expertenschaetzung, nicht auf peer-reviewed Literatur.
CUMULATIVE_STRESS_THRESHOLD: float = 0.7  # Konfigurierbar pro Nutzerprofil
STRESS_WINDOW_DAYS: int = 14              # Konfigurierbar
```

### P-004: SOG-Workflow-Timing (Szenario 1) ohne Sorten-/Genetik-Beruecksichtigung

**Vage Anforderung:** "Tag 21: Switch zu 12/12 Licht, Tag 70: Ernte" (Zeilen 1507, 1510)
**Problem:** Die Tage sind stark sortenabhaengig:
- Autoflower-Sorten: Kein Lichtwechsel noetig (tagneutral), Ernte 60-75 Tage
- Schnelle Indica: Bluete 7-8 Wochen, Ernte ca. Tag 77-84
- Sativa-dominante: Bluete 10-14 Wochen, Ernte ca. Tag 91-119

Das SOG-Beispiel ist nur fuer eine spezifische Genetik (schnelle Indica/Hybrid) valide.
**Messbare Alternative:** Templates sollten relative Offsets statt absoluter Tage verwenden, oder sortenspezifische Parameter als Variablen einsetzen:
```
Tag ${VEGI_DAYS}: Switch zu 12/12 (Default 21, Konfigurierbar)
Tag ${VEGI_DAYS + FLOWER_DAYS - 14}: Flushing starten
Tag ${VEGI_DAYS + FLOWER_DAYS}: Ernte
```

### P-005: "No watering for 24h" nach Topping ist pauschal und teilweise kontraproduktiv

**Vage Anforderung:** "Keine Bewaesserung fuer 24h (Cannabis/Kraeuter)" (Zeile 877)
**Problem:** Diese Empfehlung ist in der Cannabis-Community verbreitet, aber pflanzenphysiologisch nicht generell korrekt:
- Bei Hydroponik: Bewesserungsstopp fuehrt zu Wurzelaustrocknung -- kritisch bei NFT/Aeroponik
- Bei Erde/Substrat: Leichte Austrocknung kann Ethylen-Produktion foerdern (Stress-Signal), was Recovery verlangsamt
- Der eigentliche Grund: Weniger Transpiration nach Schnitt = weniger Wasserverlust ueber die Schnittstelle

**Praezisierung:**
```
'post_topping_water': {
    'soil': 'Normal weitergiessen, keine Ueberwaesserung',
    'coco': 'Normal weitergiessen',
    'hydro_nft': 'System NICHT stoppen (Wurzelaustrocknung!)',
    'hydro_dwc': 'Normal weiter, ggf. EC um 20% reduzieren',
}
```

---

## H -- Hinweise und Best Practices

### H-001: Cannabis-Hermaphroditismus als HST-Risiko: hervorragend modelliert

Die Warnung vor Hermaphroditismus bei HST in der Bluetephase (Zeile 64, 746) ist pflanzenphysiologisch korrekt und praxisrelevant. Cannabis reagiert auf starken Stress mit der Bildung von maennlichen Blueten (genetisch weibliche Pflanzen produzieren Pollen), was die Ernte kontaminieren kann. Die Differenzierung zwischen Early-Flowering (Stretch, einige HST noch moeglich) und Mid/Late-Flowering (kein HST) entspricht der Praxis.

### H-002: Artspezifische Recovery-Faktoren: innovativer Ansatz

Der Ansatz, artspezifische Multiplikatoren fuer Recovery-Zeiten zu verwenden (SPECIES_RECOVERY_FACTORS), ist eine elegante Loesung. In der Literatur finden sich hierzu wenig standardisierte Daten, aber die relativen Verhaeltnisse sind plausibel: Tomaten regenerieren tatsaechlich schneller als Cannabis, und Beerensstraeucher mit verholzten Trieben langsamer.

**Empfehlung:** Diese Faktoren sollten ueber Nutzerfeedback und Ergebnisdokumentation kalibrierbar sein (Machine Learning oder einfache statistische Anpassung basierend auf tatsaechlichen Recovery-Beobachtungen).

### H-003: Karenzzeit-Validator (KarenzzeitValidator) fachlich sehr gut

Die PHI-Validierung (Pre-Harvest Interval) ist ein kritisches Sicherheitsfeature. Die Default-Karenzzeiten sind konservativ und korrekt. Besonders wertvoll:
- Biologische Mittel (BT, Nuetzlinge, Kieselgur): PHI = 0 Tage -- korrekt
- Unbekanntes Produkt: PHI = 14 Tage (konservativ) -- gute Sicherheitspraxis
- Cannabis-spezifischer Hinweis auf Inhalationsrisiko -- sehr relevant

**Ergaenzungsempfehlung:** Temperaturabhaengige Abbauzeiten erwaegen. Manche PSM (insbesondere Pyrethrine) bauen bei hoeheren Temperaturen schneller ab. Dies koennte als optionaler Modifikator implementiert werden.

### H-004: Tageszeit-Empfehlung ist ein hervorragendes Feature

Die Verknuepfung von Task-Typ mit optimaler Tageszeit (morning/afternoon/evening/lights_off) zeigt pflanzenphysiologisches Verstaendnis. Ergaenzend:
- **Training morgens:** Korrekt -- Turgor ist nach naechtlicher Rehydrierung maximal, Staengel sind biegbar
- **Transplanting abends:** Korrekt im Prinzip (s. F-003 fuer praezisere Begruendung)
- **Ernte morgens:** Sollte als Empfehlung ergaenzt werden -- Terpenkonzentration ist morgens am hoechsten, bevor Licht die Terpenverdunstung beschleunigt

### H-005: Erwaegung von Licht-/Wetter-abhaengigen Task-Verschiebungen

Fuer Outdoor-Tasks waere eine Wetter-Integration wertvoll:
- Pflanzenschutz-Spritzung: Nicht bei Regen oder Wind >15 km/h
- Transplanting: Nicht bei Hitze >30 Grad C oder Frost
- Ernte: Nicht bei Regen (Schimmelrisiko)

REQ-010 erwaehnt "Wetter-Integration" als Akzeptanzkriterium, aber REQ-006 bezieht dies nicht auf Task-Planung.

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|--------------------|-----------|
| Recovery-Zeit (Tage) | Ja (artspezifisch) | HST-Typ * Species-Faktor | Hoch |
| Kumulativer Stress-Score | Ja (0-1.0) | Schwelle 0.7 (konfigurierbar) | Hoch |
| Karenzzeit PHI (Tage) | Ja (produktspezifisch) | 0-21 Tage | Hoch |
| Temperatur-Modifikator fuer Recovery | Nein | 1.0 bei 25-28 Grad C, skalierend | Mittel |
| GDD-basierter Trigger | Nein | artspezifisch | Mittel |
| VPD bei Task-Ausfuehrung | Nein (nur als Zeithinweis) | 0.4-0.8 kPa fuer Transplant | Niedrig |
| Substratfeuchte bei Bewesserung-Tasks | Nein | <40% = giessen | Mittel |
| Luftfeuchtigkeit nach Schnitt | Nein | >60% rH reduziert Infektionsrisiko | Niedrig |

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| HST-Techniken Cannabis | Ed Rosenthal: Marijuana Grower's Handbook | -- |
| Recovery-Physiologie | Taiz/Zeiger: Plant Physiology (Kap. Wound Response) | -- |
| Karenzzeiten DE | BVL Pflanzenschutzmittel-Verzeichnis | bvl.bund.de |
| Karenzzeiten international | IRAC/FRAC Mode-of-Action Classification | irac-online.org |
| Ausgeizen Tomate | LWK Niedersachsen Tomaten-Kulturanleitung | lwk-niedersachsen.de |
| GDD-Modelle | NOAA/NWS Growing Degree Day Calculator | weather.gov |
| Zimmerpflanzen-Pflege | Royal Horticultural Society | rhs.org.uk |
| Stress-Physiologie | Lichtenthaler (1996): Vegetation Stress | -- |

---

## Glossar

- **HST** (High-Stress Training): Pflanzenformungstechniken mit hohem Stressniveau -- Topping, FIM, Supercropping, Mainlining. Fuehren zu struktureller Gewebeschaedigung und erfordern Recovery-Zeit.
- **LST** (Low-Stress Training): Biegen und Fixieren von Trieben ohne Gewebeschaedigung -- kein Recovery noetig.
- **Auxin**: Pflanzliches Wachstumshormon, primaer in der Triebspitze (Apex) produziert. Verantwortlich fuer Apikaldominanz. Topping entfernt die Auxin-Quelle -> laterale Knospen werden enthemmt.
- **Jasmonsaeure**: Stress-Hormon der Pflanze, wird bei Verwundung gebildet. Akkumuliert bei mehrfachem Stress und kann Wachstumshemmung verursachen.
- **Ethylen**: Gasfoermiges Pflanzenhormon, foerdert Reifung und Seneszenz. Wird bei Stress verstaerkt gebildet.
- **Kallusbildung**: Wundverschluss-Gewebe, das nach Verletzung gebildet wird. Dauer abhaengig von Art, Temperatur und Wundgroesse.
- **PHI** (Pre-Harvest Interval): Wartezeit zwischen letzter Pflanzenschutz-Anwendung und Ernte. Gesetzlich vorgeschrieben bei zugelassenen PSM.
- **Ausgeizen**: Entfernung von Seitenrieben (Geiztrieben) in Blattachseln -- spezifisch fuer Stabtomaten. Nicht identisch mit Topping.
- **DIF** (Temperatur-Differenz Tag/Nacht): Steuert Streckungswachstum ueber Gibberellin-Synthese. Negativer DIF = kompakter Wuchs.
- **Stretch**: Phase des schnellen Laengenwachstums zu Beginn der Bluete bei Cannabis (Early Flowering). Letzte Moeglichkeit fuer Supercropping.
- **GDD** (Growing Degree Days): Akkumulierte Waermeeinheiten oberhalb einer Basistemperatur. Biologisch aussagekraeftiger als Kalendertage fuer Entwicklungsprognosen.

---

## Zusammenfassung der Findings

| ID | Kategorie | Titel | Schwere |
|----|-----------|-------|---------|
| F-001 | Fachlich Falsch | Foliar-Feeding Begruendung "UV + nasses Blatt" | Mittel |
| F-002 | Fachlich Falsch | Kartoffel "langsamer als Nachtschattengewaechse" | Niedrig |
| F-003 | Fachlich Falsch | Transplanting "niedrige VPD" am Abend | Mittel |
| F-004 | Fachlich Falsch | Tomate unter Topping statt Ausgeizen als eigene Kategorie | Hoch |
| U-001 | Unvollstaendig | Keine Zimmerpflanzen-Workflows | Hoch |
| U-002 | Unvollstaendig | Keine Hydroponik-Wartungs-Templates | Hoch |
| U-003 | Unvollstaendig | GDD-basierter Trigger fehlt | Mittel |
| U-004 | Unvollstaendig | Mondkalender-Trigger fehlt (optional) | Niedrig |
| U-005 | Unvollstaendig | Observation/Monitoring-Kategorie fehlt | Mittel |
| U-006 | Unvollstaendig | Outdoor-Workflows unterrepraesentiert | Mittel |
| U-007 | Unvollstaendig | Task-Aktor-Integration (REQ-018) unklar | Hoch |
| U-008 | Unvollstaendig | Temperaturabhaengige Recovery fehlt | Niedrig |
| P-001 | Ungenau | Recovery-Zeiten im Freitext vs. Code inkonsistent | Niedrig |
| P-002 | Ungenau | "herb" als Recovery-Kategorie taxonomisch unscharf | Mittel |
| P-003 | Ungenau | Stress-Score Schwellwert ohne Kalibrierungshinweis | Niedrig |
| P-004 | Ungenau | SOG-Timing ohne Genetik-Variable | Mittel |
| P-005 | Ungenau | "No watering 24h" nach Topping pauschal | Mittel |
