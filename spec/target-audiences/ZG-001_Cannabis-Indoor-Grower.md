# ZG-001: Ambitionierter Cannabis Indoor Grower

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Primaere Zielgruppe (stark adressiert)
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Cannabis Indoor Grower (Heimanbau bis Semi-Professionell) |
| **Altersgruppe** | 25-45 Jahre |
| **Betriebsgroesse** | 4-50 Pflanzen, 1-3 Growzelte oder ein Indoor-Raum |
| **Technische Affinitaet** | Hoch |
| **Botanisches Vorwissen** | Hoch (Spezialisiert auf Cannabis) |
| **Primaere Nutzungsumgebung** | Desktop (Planung), Tablet/Smartphone (im Growzelt) |
| **Abdeckungsgrad** | Vollstaendig -- originaere Designzielgruppe |

## 2. Persona

**Name:** Max, 34, Software-Entwickler
**Situation:** Betreibt seit 3 Jahren zwei Growzelte (120x120cm) im Keller. Arbeitet mit Coco/Perlite-Substrat und Tropfbewaesserung. Hat Home Assistant mit Temperatur-, Luftfeuchte- und CO2-Sensoren eingerichtet. Dokumentiert akribisch seine Grows in Spreadsheets und moechte auf ein strukturiertes System umsteigen. Seit der CanG-Liberalisierung 2024 legt er Wert auf lueckenlose Dokumentation.

**Motivation:**
- Maximale Kontrolle ueber alle Wachstumsparameter (Temperatur, Luftfeuchte, VPD, PPFD, EC, pH)
- Genetische Rueckverfolgbarkeit seiner Klonlinien ueber mehrere Generationen
- Optimaler Erntezeitpunkt durch Trichom-Monitoring und Multi-Indikator-Bewertung
- Lueckenlose Dokumentation fuer Rechtssicherheit (CanG)
- Vergleich von Grows ueber verschiedene Naehrstoffplaene und Umgebungsbedingungen

## 3. Kernbeduerfnisse

### 3.1 Phasensteuerung (REQ-003)
- Photoperiodische Steuerung: 18/6 (vegetativ) -> 12/12 (Bluete) als Trigger
- Autoflower-Sonderlogik: Zeitbasierte Phasen (60-90 Tage Gesamtzyklus), keine Lichtumstellung
- GDD-Tracking fuer praezise Reifebestimmung
- VPD-Zielwerte pro Phase (0.8-1.5 kPa vegetativ, 0.8-1.2 kPa Bluete)
- Dark Period vor Ernte (24-48h)

### 3.2 Naehrstoffmanagement (REQ-004)
- Multi-Part-Duenger-Mischungen (A+B, CalMag, PK-Booster)
- EC-Budget-Berechnung: Ziel-EC minus Basis-Wasser-EC
- CalMag-Korrektur basierend auf Wasserhaerte
- Mischsequenz-Validierung (CalMag VOR Sulfaten -- Ausfaellung verhindern)
- Runoff-Analyse (EC/pH des Abflusswassers)
- Flush-Protokoll vor Ernte (2 Wochen reines Wasser)

### 3.3 Ernte-Optimierung (REQ-007)
- Trichom-Mikroskopie: Klar/Milchig/Bernstein-Verhaeltnis als Reife-Indikator
- Pistil-Faerbung: Weiss -> Orange/Braun Prozentsatz
- Harvest-Window-Berechnung aus mehreren Indikatoren
- Dark Period als Vorbereitung
- Nassgewicht -> Trockengewicht-Tracking

### 3.4 Post-Harvest (REQ-008)
- Trocknungs-Protokoll (60% RH, 18-20 Grad C, 7-14 Tage)
- Jar-Curing mit Burping-Schedule (anfangs taeglich, dann abnehmend)
- Feuchtigkeits-Monitoring waehrend Curing (62% Ziel)
- Qualitaetsentwicklung ueber Curing-Dauer

### 3.5 Genetik und Vermehrung (REQ-017)
- Klonlinien-Management: Mutterpflanzen -> Stecklinge -> Generationen
- `descended_from`-Graph fuer genetische Rueckverfolgbarkeit
- Clone-Run: Batch von Stecklingen aus einer Mutterpflanze
- Phaenotpy-Selektion: Bewertung und Auswahl der besten Exemplare
- Seed-Cross-Dokumentation (maennlich x weiblich)

### 3.6 Schaedlingsmanagement (REQ-010)
- Hermaphrodismus-Erkennung und -Protokoll (Isolation, Entfernung)
- Wirkstoff-Rotation (max. 3x gleicher Wirkstoff in 90 Tagen)
- Karenz-Gate: Mindestabstand zwischen letzter Behandlung und Ernte
- IPM-3-Stufen: Praevention (Nuetzlinge) -> Monitoring -> Intervention

### 3.7 Umgebungssteuerung (REQ-018)
- VPD-Regelkreis mit Hysterese (kein Oszillieren)
- Phase-spezifische Profile (Vegetativ vs. Bluete vs. Trocknung)
- Home Assistant / MQTT Integration fuer Luefter, Befeuchter, Heizung
- Sensor-Schwellwert-Alarme (Temperatur zu hoch, RH zu niedrig)

### 3.8 Dokumentation und Compliance
- Seed-to-Shelf-Traceability (REQ-013): Saatgut/Klon -> Pflanze -> Ernte -> Charge
- CanG-konforme Aufbewahrungsfristen (NFR-011)
- Revisionssichere Ernte-Protokolle
- Batch-IDs als Chargen-Nummern

## 4. Typische Workflows

### 4.1 Neuen Grow starten
1. PlantingRun anlegen (Strain, Substrat, Standort)
2. Naehrstoffplan zuweisen (Vegetativ-Schema des Duenger-Herstellers)
3. Pflanzen aus Klonen oder Samen erstellen
4. Phase: Keimung/Bewurzelung -> Setzling -> Vegetativ

### 4.2 Taegliche Routine
1. Dashboard pruefen: VPD, Temperatur, Luftfeuchte, CO2
2. Giesserinnerung bestaetigen oder Giessplan-Eintrag loggen
3. EC/pH des Drain-Wassers notieren
4. Optionale Inspektion: Schaedlinge, Hermaphroditen, Mutterpflanzen-Status

### 4.3 Erntephase
1. Trichom-Beobachtung dokumentieren (% klar/milchig/bernstein)
2. Ernte-Readiness pruefen (Multi-Indikator-Score)
3. Dark Period starten (24-48h)
4. Ernte durchfuehren: Nassgewicht dokumentieren
5. Trocknungsphase starten (Umgebungswerte tracken)
6. Jar-Curing beginnen, Burping-Erinnerungen folgen

### 4.4 Klonlinie pflegen
1. Mutterpflanze auswaehlen (beste Phaenotype aus vorherigem Run)
2. Stecklinge schneiden -> Clone-Run erstellen
3. Bewurzelungs-Phase tracken (7-14 Tage)
4. Erfolgreiche Klone dem neuen PlantingRun zuweisen
5. Genetische Linie im Graph nachverfolgen

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Hoch | Species/Cultivar mit Cannabis-spezifischen Feldern (Autoflower, THC/CBD-Profile) |
| REQ-003 | Kritisch | Phasensteuerung mit 12/12-Trigger, Autoflower-Sonderlogik, VPD-Ziele |
| REQ-004 | Kritisch | EC-Budget, CalMag-Korrektur, Multi-Part-Mischung, Flush-Protokoll |
| REQ-005 | Hoch | Sensor-Integration (HA/MQTT), VPD-Berechnung, Alarme |
| REQ-007 | Kritisch | Trichom-Mikroskopie, Harvest-Window, Dark Period |
| REQ-008 | Hoch | Jar-Curing, Burping-Schedule, Feuchtigkeits-Tracking |
| REQ-010 | Hoch | Hermaphrodismus-Protokoll, Wirkstoff-Rotation, Karenz-Gate |
| REQ-013 | Kritisch | PlantingRun (Clone-Run, Seed-to-Shelf), Batch-Operationen |
| REQ-014 | Hoch | Tankmanagement (Stammloesung, Rezirkulationssystem) |
| REQ-017 | Hoch | Genetische Linie, Klonlinien, Seed-Cross |
| REQ-018 | Hoch | VPD-Regelkreis, Phase-Profile, Aktor-Steuerung |
| REQ-019 | Mittel | Substrattypen (Coco, Perlite, Steinwolle) |
| REQ-022 | Mittel | Pflege-Erinnerungen (Giessen, Duengen) |
| NFR-011 | Hoch | CanG-Aufbewahrungsfristen |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | ZG-001 (Cannabis) | ZG-002 (Freiland) | ZG-003 (Zimmer) |
|---------|:-:|:-:|:-:|
| Indoor-Fokus | Ja | Nein | Ja |
| EC/pH-Monitoring | Taeglich | Selten | Nein |
| Genetik-Tracking | Kritisch | Unwichtig | Selten |
| Ernte-Praezision | Trichom-Level | Saisonal | N/A |
| Compliance-Bedarf | Hoch (CanG) | Gering | Nein |
| Automatisierung | Hoch (HA/MQTT) | Gering | Nein |
| Naehrstoff-Komplexitaet | Multi-Part + EC-Budget | Organisch/m2 | Einfach |

## 7. Evaluationskriterien

Fuer kontextbezogene Eval-Dokumente sollten folgende Aspekte geprueft werden:

1. **Phasensteuerung:** Kann der Nutzer einen vollstaendigen Grow-Zyklus (Keimung -> Ernte) mit korrekten Phasenuebergaengen durchfuehren?
2. **Naehrstoff-Praezision:** Werden EC-Budgets korrekt berechnet? Wird die Mischsequenz validiert?
3. **Ernte-Timing:** Funktioniert die Multi-Indikator-Bewertung (Trichom + Pistil + GDD)?
4. **Genetik-Konsistenz:** Ist die Klonlinie ueber Generationen nachverfolgbar?
5. **Karenz-Sicherheit:** Wird die Ernte blockiert wenn ein aktiver Karenz-Intervall vorliegt?
6. **Sensor-Integration:** Werden VPD, Temperatur, RH korrekt aus HA/MQTT bezogen?
7. **Dokumentations-Vollstaendigkeit:** Ist der Seed-to-Shelf-Trail lueckenlos?
8. **Flush-Protokoll:** Wird der Naehrstoffplan korrekt auf Flush umgestellt?
9. **Post-Harvest:** Funktioniert Jar-Curing mit Burping-Erinnerungen?
10. **Compliance:** Werden CanG-Aufbewahrungsfristen eingehalten?

## 8. Sprachstil und Fachbegriffe

Diese Zielgruppe verwendet folgende Fachbegriffe selbstverstaendlich:

- **Strain** (Sorte/Genetik), **Pheno** (Phaenotyp-Auspraegung)
- **EC** (Electrical Conductivity), **PPM** (Parts per Million -- EC-Umrechnung)
- **VPD** (Vapor Pressure Deficit), **PPFD** (Lichtintensitaet)
- **CalMag** (Calcium-Magnesium-Ergaenzung)
- **Flush** (Naehrstoff-Auswaschung vor Ernte)
- **Trichome** (Harz-Druesen), **Amber/Milky/Clear** (Trichom-Reifestadien)
- **LST** (Low Stress Training), **HST** (High Stress Training), **Topping**, **FIM**
- **SOG** (Sea of Green), **ScrOG** (Screen of Green)
- **Clone** (Steckling), **Mother** (Mutterpflanze)
- **Veg** (vegetative Phase), **Flower** (Bluetephase)
- **DWC** (Deep Water Culture), **Coco** (Kokosfaser-Substrat)
- **Runoff** (Abflusswasser), **Feed Chart** (Duengeschema)
