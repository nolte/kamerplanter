# ZG-002: Freilandgaertner / Gemuesegaertner

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Primaere Zielgruppe (stark adressiert)
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Hobby-Freilandgaertner mit Gemuese- und Kraeutergarten |
| **Altersgruppe** | 35-65 Jahre |
| **Betriebsgroesse** | 20-200 Pflanzen, 1-5 Beete, 10-100 m2 |
| **Technische Affinitaet** | Gering bis Mittel |
| **Botanisches Vorwissen** | Mittel bis Hoch (Erfahrungswissen) |
| **Primaere Nutzungsumgebung** | Tablet/Smartphone (im Garten), Desktop (Winterplanung) |
| **Abdeckungsgrad** | Vollstaendig -- durch Outdoor-Garden-Planner Review systematisch erweitert |

## 2. Persona

**Name:** Sabine, 52, Lehrerin
**Situation:** Hat einen 60 m2 grossen Gemuese- und Kraeutergarten hinter dem Haus. Baut seit 15 Jahren Tomaten, Zucchini, Bohnen, Salat und Kuechenkraeuter an. Kompostiert, nutzt Hornspane und Brennnesseljauche. Plant Fruchtfolgen im Kopf, verliert aber bei 5 Beeten den Ueberblick. Moechte im Winter die naechste Saison strukturiert planen. Spart eigenes Saatgut von samenfesten Sorten auf.

**Motivation:**
- Strukturierter Aussaatkalender mit Voranzucht-Terminen
- Fruchtfolge-Tracking (welche Familie stand wo in den letzten 3 Jahren?)
- Mischkultur-Empfehlungen (welche Pflanzen foerdern/hemmen sich?)
- Saisonale Erinnerungen (Abhaerten, Auspflanzen nach Eisheiligen, Frostschutz)
- Ernteplanung fuer kontinuierliche Versorgung (Sukzessions-Aussaat)

## 3. Kernbeduerfnisse

### 3.1 Beetplanung und Fruchtfolge (REQ-002)
- Beete als Standort-Hierarchie: Garten -> Beet -> Reihe/Abschnitt
- CropRotationPlan: 4-Jahres-Zyklus (Starkzehrer -> Mittelzehrer -> Schwachzehrer -> Gruenduengung)
- Familien-basierte Rotation (keine Solanaceen nach Solanaceen)
- Visuelle Beet-Belegung ueber Saisons hinweg
- Winterharte vs. einjaehrige Kulturen unterscheiden

### 3.2 Aussaatkalender und Phasen (REQ-003, REQ-015)
- Voranzucht-Termine (indoor auf Fensterbank/Gewaechshaus)
- Direktsaat-Termine (outdoor nach letztem Frost)
- Auspflanz-Termine (nach Abhaertung)
- Eisheiligen als konfigurierbarer Frosttermin
- Phaenologische Trigger (Forsythienbluete = Kartoffeln legen, Holunderbluete = Gurken saeen)
- Saisonuebersicht: 12-Monats-Karten mit allen Kulturen

### 3.3 Mischkultur (REQ-028)
- Graph-basierte Kompatibilitaets-Engine
- Gute Nachbarn / Schlechte Nachbarn pro Art
- Empfehlungen beim Anlegen eines neuen Beetes
- Beruecksichtigung von Allelopathie und Naehrstoffkonkurrenz

### 3.4 Organische Duengung (REQ-004)
- Flaechenbasierte Dosierung: g/m2 (Hornspane, Kompost), L/m2 (Jauche)
- Bodenanalyse-Integration (pH, Naehrstoffgehalte)
- Naehrstoffbedarfs-Stufen (Starkzehrer/Mittelzehrer/Schwachzehrer)
- Organische Duengemittel: Kompost, Hornspane, Gesteinsmehl, Jauchen
- Kein EC-Monitoring (Freiland-irrelevant)

### 3.5 Wetter-Integration (REQ-005)
- DWD/OpenWeatherMap/Open-Meteo als Wetter-Datenquelle
- Frostwarnung (Nachttemperatur < 0 Grad C)
- Spaetwarn-Benachrichtigung (Vlies auflegen, Kuebelpflanzen reinstellen)
- Regenprognose (Giessen heute unnoetig?)

### 3.6 Sukzessions-Aussaat (REQ-013)
- Gestaffelte Aussaaten in 2-3-Wochen-Intervallen
- Ziel: Durchgehende Ernte ueber die Saison
- SuccessionPlan-Knoten mit Intervall und Anzahl Durchgaenge
- Kalender-Visualisierung der geplanten Durchgaenge

### 3.7 Ueberwinterung (REQ-022)
- Winterhaerte-Ampel: Gruen (winterhart), Gelb (Schutz noetig), Rot (einraeumen)
- Ueberwinterungs-Profile (Schutzmethode, Lagerort, Fruehjahrs-Ausraeum-Termin)
- Knollen-Zyklus: Ausgraben -> Lagern -> Vorkeimen -> Einpflanzen (Dahlien, Gladiolen)
- Frost-Sensitivitaets-Daten pro Art

### 3.8 Aufgabenplanung (REQ-006)
- 8 Outdoor-Templates (Frostschutz, Obstbaum-Schnitt, Abhaertungs-Workflow, etc.)
- Saisonale Trigger (Monat-basiert oder phaenologisch)
- Erinnerungen an wiederkehrende Aufgaben (Kompost umsetzen, Beete vorbereiten)

### 3.9 Wasserquellen (REQ-002, REQ-014)
- Wasserquellen-Konfiguration am Standort (Leitungswasser, Regenwasser, Brunnen)
- TapWaterProfile: EC, pH, Gesamthaerte
- Regenwassernutzung als bevorzugte Quelle
- Einfache Wasserplanung (kein Tank-Management wie Indoor)

## 4. Typische Workflows

### 4.1 Winterplanung (November-Februar)
1. Beete im System anlegen/aktualisieren
2. Fruchtfolge-Empfehlung pruefen (was stand letztes Jahr wo?)
3. Kulturen pro Beet planen (Mischkultur-Check)
4. Sukzessions-Aussaaten planen (Salat alle 3 Wochen)
5. Saatgut-Bestand pruefen, Bestellliste erstellen

### 4.2 Voranzucht (Februar-April)
1. Aussaatkalender zeigt faellige Voranzuchten
2. Voranzucht-Aufgabe bestaetigen, Sorte und Menge dokumentieren
3. Setzlings-Phase tracken (Keimung beobachten)
4. Abhaertungs-Workflow starten (7-10 Tage vor Auspflanzen)

### 4.3 Hauptsaison (Mai-September)
1. Taegliche Aufgaben-Liste pruefen (Giessen, Ernten, Nachsaeen)
2. Wetter-Warnung beachten (Frost, Hitze, Starkregen)
3. Ernte dokumentieren (Menge, Qualitaet)
4. Schaedlings-Inspektionen loggen
5. Sukzessions-Saaten durchfuehren

### 4.4 Saisonende (Oktober-November)
1. Ueberwinterungs-Aufgaben abarbeiten (Knollen ausgraben, Vlies aufspannen)
2. Kuebelpflanzen einraeumen (Winterhaerte-Ampel pruefen)
3. Beete raeumen, Gruenduengung saeen
4. Saison-Rueckblick: Ertraege vergleichen

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Hoch | Species-Felder: frost_sensitivity, sowing_dates, harvest_months, nutrient_demand_level |
| REQ-002 | Kritisch | Beetplanung, CropRotationPlan, Wasserquellen |
| REQ-003 | Hoch | Phasen fuer Freilandpflanzen (Aussaat->Setzling->Vegetativ->Bluete->Ernte) |
| REQ-004 | Hoch | Organische Duengung (g/m2, Jauchen), Bodenanalyse |
| REQ-005 | Hoch | Wetter-Integration (DWD), Frostwarnung |
| REQ-006 | Kritisch | 8 Outdoor-Templates, phaenologische Trigger |
| REQ-007 | Mittel | Ernte-Dokumentation (Menge, Qualitaet) |
| REQ-013 | Hoch | Sukzessions-Aussaat, Batch-Operationen |
| REQ-015 | Kritisch | Aussaatkalender-Modus, Saisonuebersicht |
| REQ-019 | Mittel | Substrattypen fuer Hochbeet, Freiland |
| REQ-022 | Kritisch | Ueberwinterung, Winterhaerte-Ampel, saisonale Erinnerungen |
| REQ-028 | Kritisch | Mischkultur-Engine, Companion Planting |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | ZG-002 (Freiland) | ZG-001 (Cannabis) | ZG-003 (Zimmer) |
|---------|:-:|:-:|:-:|
| Outdoor-Fokus | Ja | Nein | Nein |
| Saisonalitaet | Kritisch | Nein (ganzjaehrig) | Gering |
| Fruchtfolge | Kritisch | Irrelevant | Irrelevant |
| Mischkultur | Kritisch | Irrelevant | Gering |
| Wetter-Abhaengigkeit | Hoch | Nein (kontrolliert) | Nein |
| EC/pH-Monitoring | Selten (Bodenanalyse) | Taeglich | Nein |
| Ueberwinterung | Kritisch | Irrelevant | Teilweise |
| Naehrstoff-Ansatz | Organisch/m2 | Mineralisch/EC | Einfach |

## 7. Evaluationskriterien

1. **Beetplanung:** Kann der Nutzer Beete mit Fruchtfolge-Empfehlung anlegen und ueber Jahre verfolgen?
2. **Aussaatkalender:** Werden Voranzucht- und Direktsaat-Termine korrekt berechnet (Frosttermin, Eisheiligen)?
3. **Mischkultur:** Werden gute/schlechte Nachbarn korrekt empfohlen?
4. **Fruchtfolge-Validierung:** Wird gewarnt wenn 2x hintereinander Solanaceen auf demselben Beet stehen?
5. **Sukzession:** Werden gestaffelte Aussaaten korrekt geplant und erinnert?
6. **Organische Duengung:** Ist die flaechenbasierte Dosierung (g/m2) korrekt berechnet?
7. **Wetter-Integration:** Werden Frostwarnungen rechtzeitig ausgeloest?
8. **Ueberwinterung:** Werden Aufgaben basierend auf Winterhaerte-Ampel generiert?
9. **Phaenologie:** Koennen natuerliche Indikatoren (Forsythienbluete) als Trigger gesetzt werden?
10. **Saisonuebersicht:** Ist eine 12-Monats-Gesamtansicht aller Kulturen verfuegbar?

## 8. Sprachstil und Fachbegriffe

Diese Zielgruppe verwendet folgende Begriffe (oft deutsch statt englisch):

- **Fruchtfolge** (Crop Rotation), **Starkzehrer/Mittelzehrer/Schwachzehrer** (Naehrstoffbedarfs-Stufen)
- **Mischkultur** (Companion Planting), **Gute/Schlechte Nachbarn**
- **Voranzucht** (Indoor Pre-sowing), **Direktsaat** (Direct Sowing)
- **Eisheilige** (Ice Saints, ~11.-15. Mai als letzter Frosttermin)
- **Abhaerten** (Hardening Off -- schrittweise Gewoehnung an Aussentemperatur)
- **Hornspane/Hornmehl** (Horn shavings -- organischer Stickstoffduenger)
- **Jauche/Bruehe** (Fermented plant tea -- Brennnessel, Beinwell)
- **Gruenduengung** (Green manure -- Phacelia, Senf, Klee)
- **Kompost** (Compost), **Mulch** (Mulch)
- **Hochbeet** (Raised Bed), **Parzelle** (Plot/Patch)
- **Saatgut** (Seeds), **samenfest** (Open-pollinated)
- **Knollen** (Tubers/Bulbs), **Rhizome**, **Zwiebeln** (Bulbs)
- **Winterhart** (Hardy), **Frostempfindlich** (Frost-tender)
- **Phaenologie** (Phenology -- natuerliche Jahreszeit-Indikatoren)
