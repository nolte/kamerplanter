# UZG-003: Bildungseinrichtungen (Schule, Berufsschule, Uni)

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Unterversorgte Zielgruppe -- Hohes Potenzial (nicht adressiert)
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Lehr-Gewaechshaus, Schulgarten, Botanik-Labor |
| **Altersgruppe** | Lehrkraefte 30-60 Jahre; Schueler/Studenten 14-25 Jahre |
| **Betriebsgroesse** | 20-200 Pflanzen, 1-3 Gewaechshaeuser oder Beete, 10-30 Nutzer pro Gruppe |
| **Technische Affinitaet** | Gemischt (Lehrkraft mittel, Schueler hoch) |
| **Botanisches Vorwissen** | Lehrkraft hoch, Schueler gering-mittel |
| **Primaere Nutzungsumgebung** | Tablet (im Gewaechshaus/Garten), Desktop (Auswertung) |
| **Abdeckungsgrad** | Nicht adressiert -- Gruppen-/Klassenverwaltung und Datenexport fehlen |
| **Marktpotenzial** | Mittelgross, strategisch wertvoll als Multiplikator |

## 2. Persona

### 2a. Lehrkraft
**Name:** Dr. Martina Hofer, 48, Biologielehrerin an einem Gymnasium
**Situation:** Betreut ein Schul-Gewaechshaus mit 60 Pflanzen und einen 30 m2 Schulgarten. Fuehrt jaehrlich 3 Projekte mit verschiedenen Klassen durch: "Bohnen-Wachstumsexperiment" (7. Klasse), "Photosynthese messen" (10. Klasse), "Substrat-Vergleichsstudie" (Biologie-LK). Braucht reproduzierbare Protokolle, Vergleichsdaten ueber Kohorten und eine einfache Auswertung fuer Schueler-Prasentationen. Aktuell dokumentiert jede Klasse auf Papier-Boegen.

### 2b. Schueler/Student
**Name:** Jonas, 16, Biologie-Leistungskurs
**Situation:** Muss im Rahmen eines Semester-Projekts das Wachstum von 5 Tomatenpflanzen unter verschiedenen Lichtbedingungen dokumentieren. Soll Daten erheben, Grafiken erstellen und ein Protokoll schreiben. Kennt sich mit Apps aus, aber nicht mit Pflanzen.

**Motivation (Lehrkraft):**
- Reproduzierbare Versuchsprotokolle ueber Schuljahre hinweg
- Einfache Dateneingabe fuer Schueler (keine Fehlerquellen)
- Kohortenvergleich: "Klasse 2024 vs. Klasse 2025"
- Datenexport (CSV/JSON) fuer Auswertung in Excel/R/Python
- Einfache Dashboards fuer Schueler-Praesentationen

**Motivation (Schueler):**
- Schnelle Dateneingabe (Pflanzenmessung, Foto)
- Automatische Grafiken (Wachstumskurve)
- Einfache Bedienung ohne Einarbeitung

## 3. Kernbeduerfnisse

### 3.1 Gruppen-/Klassenverwaltung (Fehlend)
- Sub-Gruppen innerhalb eines Tenants (Klassen, Semester-Gruppen)
- Temporaere Mitgliedschaft (Schuljahr/Semester)
- Lehrkraft als Admin, Schueler als Grower mit eingeschraenkten Rechten
- Einladungslink pro Klasse (nicht individuell)
- Automatische Aufraemung nach Projekt-Ende

### 3.2 Versuchsprotokoll-Templates (Fehlend)
- Vordefinierte Versuchsaufbauten: "Wachstumsvergleich", "Substrat-Vergleich", "Licht-Experiment"
- Hypothese, Methodik, Variablen, Kontrollgruppe definieren
- Standardisierte Mess-Zeitpunkte (taeglich, woechentlich)
- Mess-Parameter pro Template (Hoehe, Blattanzahl, Gewicht, pH, EC)
- Foto-Dokumentation zu jedem Messpunkt

### 3.3 Datenexport (Teilweise vorhanden)
- CSV-Export aller Messdaten (fuer Excel-Auswertung)
- JSON-Export (fuer Python/R-Analyse)
- Grafik-Export: Wachstumskurven als PNG/SVG
- TimescaleDB-Zeitreihen exportieren (Sensor-Daten)
- Aggregierte Tabellen fuer Prasentationen

### 3.4 Vereinfachte Dateneingabe (Schueler)
- Mobil-optimierte Mess-Eingabe: Hoehe (cm), Blattanzahl, Bemerkung
- Foto-Upload pro Messpunkt
- Keine komplexen Formulare (nur die im Template definierten Felder)
- Barcode/QR-Code pro Pflanze fuer schnelle Identifikation
- Batch-Eingabe: "Alle 5 Pflanzen heute gemessen"

### 3.5 Kohortenvergleich (Fehlend)
- Vergleich mehrerer PlantingRuns (Klasse A vs. Klasse B)
- Overlay-Grafiken: Wachstumskurven uebereinander
- Statistische Grundauswertung: Mittelwert, Standardabweichung
- Annotation: "Klasse 2024 hatte 2 Wochen Ferien-Ausfall"

### 3.6 Dashboard fuer Prasentationen
- Einfache Ansicht: Wachstumskurve + Fotos + Key-Metrics
- Prasentations-Modus (Full-Screen, grosse Schrift)
- Teilbar als Link (Read-Only fuer Elternabend/Tag der offenen Tuer)
- Klassen-Ranking: "Welche Gruppe hat den hoechsten Ertrag?"

### 3.7 Onboarding fuer Bildung (REQ-020)
- Starter-Kit "Schulgarten/Labor" im Onboarding-Wizard
- Vereinfachte Versuchsprotokolle als Templates
- Lehrkraft-Guide: "So richten Sie ein Klassen-Projekt ein"

## 4. Typische Workflows

### 4.1 Projekt einrichten (Lehrkraft)
1. Neues Projekt als Tenant oder Sub-Gruppe anlegen
2. Versuchsprotokoll-Template waehlen ("Wachstumsvergleich")
3. Variablen definieren (Substrat A vs. B, Licht-Intensitaet 1 vs. 2)
4. Pflanzen anlegen (5 pro Gruppe, mit QR-Codes)
5. Einladungslink an Schueler verteilen
6. Mess-Schedule festlegen (jeden Dienstag und Freitag)

### 4.2 Woechentliche Messung (Schueler)
1. QR-Code an der Pflanze scannen
2. Hoehe messen und eingeben (cm)
3. Blaetter zaehlen und eingeben
4. Foto machen
5. Optional: Bemerkung ("3 neue Blaetter, Blattlaeuse entdeckt")
6. "Messung abschliessen" -- Daten gespeichert

### 4.3 Auswertung (Lehrkraft + Schueler)
1. Dashboard oeffnen: Wachstumskurven aller Gruppen
2. Daten exportieren (CSV fuer Excel oder JSON fuer Python)
3. Grafiken exportieren (PNG fuer Praesentation)
4. Kohortenvergleich: Dieses Jahr vs. letztes Jahr
5. Ergebnisse im Prasentations-Modus zeigen

### 4.4 Projekt abschliessen (Lehrkraft)
1. Abschluss-Dokumentation generieren (Protokoll + Daten + Fotos)
2. Daten archivieren (fuer Kohortenvergleich naechstes Jahr)
3. Schueler-Zugaenge deaktivieren
4. Pflanzen dem Schulgarten-Bestand zuordnen oder entfernen

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-002 | Hoch | Standorte (Gewaechshaus, Beete, Versuchsreihen) |
| REQ-003 | Hoch | Phasen-Tracking (Keimung -> Wachstum -> Bluete) |
| REQ-005 | Mittel | Sensor-Daten (Klima-Monitoring im Gewaechshaus) |
| REQ-009 | Hoch | Dashboard, Grafiken, Prasentations-Modus |
| REQ-012 | Mittel | CSV-Import fuer Pflanzen-Datenbanken |
| REQ-013 | Hoch | Versuchs-Gruppen als PlantingRuns |
| REQ-020 | Hoch | Starter-Kit "Schulgarten/Labor" |
| REQ-024 | Kritisch | Multi-Tenant/Sub-Gruppen fuer Klassen |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | UZG-003 (Bildung) | ZG-004 (Gemeinschaftsgarten) | UZG-007 (Forschung) |
|---------|:-:|:-:|:-:|
| Nutzer-Rotation | Hoch (jaehrlich neue Klassen) | Gering | Gering |
| Datenexport | Kritisch (CSV, JSON) | Irrelevant | Kritisch |
| Reproduzierbarkeit | Kritisch (Versuchsprotokoll) | Irrelevant | Kritisch |
| Vereinfachte Eingabe | Kritisch (Schueler) | Teilweise | Nein |
| Kohortenvergleich | Kritisch | Irrelevant | Hoch |
| Compliance | Nein | Nein | Teilweise (GLP) |

## 7. Evaluationskriterien

1. **Klassen-Verwaltung:** Kann eine Lehrkraft eine Klasse mit 25 Schuelern als Gruppe anlegen?
2. **Versuchsprotokoll:** Kann ein standardisiertes Experiment-Template erstellt werden?
3. **QR-Code-Scan:** Kann ein Schueler per QR-Code eine Pflanze identifizieren und Daten eingeben?
4. **Mess-Eingabe:** Ist die Dateneingabe auf Smartphone in unter 30 Sekunden pro Pflanze moeglich?
5. **Wachstumskurve:** Wird eine automatische Wachstumskurve aus den Messdaten generiert?
6. **CSV-Export:** Koennen alle Messdaten als CSV exportiert werden?
7. **Kohortenvergleich:** Koennen Daten von 2 Versuchsdurchlaeufen uebereinandergelegt werden?
8. **Prasentations-Modus:** Gibt es einen Full-Screen-Modus fuer Beamer-Prasentationen?
9. **Temporaere Zugaenge:** Koennen Schueler-Accounts nach Projektende automatisch deaktiviert werden?
10. **Foto-Zeitreihe:** Koennen Fotos chronologisch als Zeitraffer angezeigt werden?

## 8. Sprachstil und Fachbegriffe

Mischung aus vereinfachter Alltagssprache (fuer Schueler) und paedagogischer Fachsprache (fuer Lehrkraefte):

- **Experiment / Versuch** (nicht "PlantingRun")
- **Messung** (nicht "Observation" oder "Data Point")
- **Hypothese, Methodik, Ergebnis** (wissenschaftliches Protokoll)
- **Kontrollgruppe / Testgruppe** (Experimental Design)
- **Wachstumskurve** (Growth Curve)
- **Klasse / Kurs / Arbeitsgruppe** (nicht "Tenant" oder "Team")
- **Auswertung** (nicht "Analytics" oder "Dashboard")
- **Protokoll** (nicht "Report" oder "Log")
- **Hoehe (cm), Blattanzahl, Gewicht (g)** (einfache Mess-Parameter)
- **Substrat** (hier als Lehr-Begriff akzeptiert)
- **Keimung, Wachstum, Bluete, Frucht** (vereinfachte Phasen)
