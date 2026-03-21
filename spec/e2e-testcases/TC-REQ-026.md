---
req_id: REQ-026
title: Aquaponik-Management — Fisch-Pflanzen-Kreislaufsysteme
category: Aquaponik
test_count: 68
coverage_areas:
  - Aquaponik-System CRUD (AquaponicSystemListPage, AquaponicSystemDetailPage)
  - Systemtyp-Validierung (Media-Bed vs. DWC/NFT/Hybrid/Wicking — Biofilter-Pflicht)
  - Fischbestand-Verwaltung (FishStockSection — Anlegen, Bearbeiten, Mortalität, Löschen)
  - Fischart-Katalog (FishSpeciesListPage — global, filter nach Temperaturzone)
  - Fisch-Pflanzen-Kompatibilität (Kompatibilitäts-Graph, Inkompatibilitätswarnungen)
  - Wassertest-Erfassung (WaterTestCreateDialog — immutable, automatische NH3-Berechnung)
  - Wassertest-Historie (WaterTestHistorySection — Zeitreihe, Alarmanzeige)
  - Stickstoffkreislauf-Visualisierung (NitrogenCycleChart TAN/NO2/NO3)
  - Biofilter-Cycling-Fortschritt (CyclingProgressCard — Status, Prozentzahl, Phasenbeschreibung)
  - Fütterungsempfehlung (FeedingRecommendationCard — temperaturkorrigiert, Ramp-up)
  - Fütterungsereignisse (FeedingEventSection — Dokumentation, Fressverhalten)
  - Supplementierung (SupplementationSection — Ergänzungsmittel, Vorher/Nachher)
  - Nährstoffdefizit-Analyse (DeficiencyCheckSection — Fe/K/Ca/Mg/Zn/B, PO4-Akkumulation)
  - Sicherheitsvalidierung (AquaponicsSafetyValidator — Dünger-Block, Kupfer-PSM-Block, Chlor-Warnung)
  - Alarme und Warnungen (AlertsSection — Severity-Stufen, Sofortmaßnahmen)
  - Alkalitäts-Management (KH-Crash-Warnung, pH-Korrektur-Regeln)
  - Regulatorische Hinweise (RegulatoryNotes — länderspezifisch, Invasive Arten)
  - Besatzdichte-Prüfung (StockingDensityCard — kg/1000L, Fisch-Pflanzen-Ratio)
  - Fischgesundheit-Monitor (HealthAlertSection — Mortalitätsrate, Fressverhalten)
  - Saisonale Dormanz und Ramp-up (Outdoor-Systeme)
  - Formularvalidierung (Pflichtfelder, Enum-Werte, Grenzwerte)
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-026: Aquaponik-Management — Fisch-Pflanzen-Kreislaufsysteme

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-026 Aquaponik-Management v1.0**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-026 führt Aquaponik als eigenständiges Anwendungsgebiet ein: Fischbestandsverwaltung, Stickstoffkreislauf-Überwachung (TAN → NO2 → NO3), Biofilter-Cycling-Erkennung, Fütterungsempfehlungen und eine Sicherheitsschicht gegen fischgiftige Substanzen.

---

## 1. Fischart-Katalog (FishSpeciesListPage)

### TC-026-001: Fischart-Katalog aufrufen — globale Seed-Daten und Listenstruktur

**Requirement**: REQ-026 § 4.2 — Fish Species Stammdaten (global); § 7 DoD — FishSpecies Seed-Daten 8 Arten
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und Mitglied eines Tenants
- System enthält die 8 Seed-Fischarten (Tilapia, Forelle, Karpfen, Europ. Wels, Barsch, Goldfisch, Zander, Saibling)

**Testschritte**:
1. Nutzer navigiert zu `/aquaponik/fischarten`

**Erwartete Ergebnisse**:
- Seite lädt mit Seitentitel "Fischarten"
- Tabelle zeigt mindestens 8 Zeilen mit den Seed-Fischarten
- Spalten enthalten: Wissenschaftlicher Name, Deutscher Name, Temperaturzone, Futter-Typ, Max. Besatzdichte
- Nil-Tilapia (Oreochromis niloticus) ist in der Liste sichtbar mit Temperaturzone "Warmwasser"
- Regenbogenforelle (Oncorhynchus mykiss) ist sichtbar mit Temperaturzone "Kaltwasser"
- Goldfisch (Carassius auratus) ist sichtbar mit Temperaturzone "Temperiert"
- Filter-Dropdowns für Temperaturzone und Futtertyp sind vorhanden

**Nachbedingungen**:
- Kein Status geändert (nur Lesevorgang)

**Tags**: [req-026, fish-species, listenansicht, seed-daten, global]

---

### TC-026-002: Fischart-Katalog nach Temperaturzone filtern

**Requirement**: REQ-026 § 4.2 — GET /by-temperature-zone/{zone}; § 1 — Temperaturzonen-Tabelle
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- FishSpeciesListPage ist geladen mit allen 8 Seed-Arten
- Filter-Dropdown für Temperaturzone ist vorhanden

**Testschritte**:
1. Nutzer klickt den Filter-Dropdown "Temperaturzone"
2. Nutzer wählt "Kaltwasser"

**Erwartete Ergebnisse**:
- Liste zeigt nur Kaltwasser-Fische: Regenbogenforelle, Seesaibling
- Tilapia, Karpfen, Goldfisch, Zander, Europäischer Wels, Barsch sind nicht sichtbar
- Filterindikator zeigt aktiven Filter an

**Nachbedingungen**:
- Nach Zurücksetzen des Filters sind wieder alle 8 Arten sichtbar

**Tags**: [req-026, fish-species, filter, temperaturzone, kaltwasser]

---

### TC-026-003: Fischart-Detailseite aufrufen — Grenzwerte und regulatorische Hinweise

**Requirement**: REQ-026 § 4.2 — GET /{species_key}; § 7 DoD — Regulatorische Hinweise; § 2 Seed-Daten
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- FishSpeciesListPage ist geladen
- Regenbogenforelle (trout_rainbow) ist in der Liste vorhanden

**Testschritte**:
1. Nutzer klickt auf die Zeile "Regenbogenforelle" in der Tabelle

**Erwartete Ergebnisse**:
- Detailseite "Regenbogenforelle" öffnet sich
- Folgende Grenzwerte sind sichtbar: Max TAN 0.5 mg/L, Max Nitrit 0.1 mg/L, Max Nitrat 80 mg/L
- DO-Werte sind sichtbar: Minimum 5.0 mg/L, Optimal 8.0 mg/L, Stress-Schwelle 6.0 mg/L
- Temperaturbereich ist sichtbar: Optimal 12–16°C, Lethalbereich unter 0.5°C / über 22°C
- Hinweistext zur Empfindlichkeit gegenüber hohen Temperaturen und Nitrit ist lesbar
- Regulatorischer Hinweis für DE erscheint: "Gewerbliche Haltung: Sachkundenachweis erforderlich"
- Hinweis "Hobby: frei" ist sichtbar

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, fish-species, detailansicht, grenzwerte, regulatorisch, forelle]

---

### TC-026-004: Invasive-Art-Warnung — Gattung Clarias

**Requirement**: REQ-026 § 1 — Regulatorische Hinweise (EU-VO 1143/2014); § 2 Seed-Daten Europäischer Wels
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- FishSpeciesListPage ist geladen

**Testschritte**:
1. Nutzer klickt auf "Europäischer Wels" (Silurus glanis)

**Erwartete Ergebnisse**:
- Detailseite des Europäischen Wels öffnet sich
- Ein Hinweisblock (Info-Chip oder Infobox) verweist auf die Unionsliste invasiver Arten
- Text erklärt, dass die Gattung Clarias (inkl. C. gariepinus und C. batrachus) auf der EU-Unionsliste steht
- Silurus glanis wird als heimische, nicht eingeschränkte Alternative hervorgehoben
- Referenz auf EU-VO 1143/2014 / DVO 2016/1141 ist lesbar

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, fish-species, regulatorisch, invasive-art, clarias, eu-vo-1143]

---

### TC-026-005: Fisch-Pflanzen-Kompatibilität für Regenbogenforelle anzeigen

**Requirement**: REQ-026 § 4.2 — GET /{species_key}/compatible-plants; § 7 DoD — Fisch-Pflanzen-Kompatibilität; Szenario 5
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Detailseite der Regenbogenforelle ist geöffnet
- Kompatibilitätsgraph enthält Seed-Daten (kompatible: Salat, Kresse, Petersilie; inkompatibel: Tomate)

**Testschritte**:
1. Nutzer klickt auf den Tab "Kompatible Pflanzen" auf der Fischart-Detailseite

**Erwartete Ergebnisse**:
- Zwei Abschnitte sind sichtbar: "Kompatible Pflanzen" (grün) und "Inkompatible Pflanzen" (rot/orange)
- In "Kompatible Pflanzen" erscheinen: Salat, Kresse, Petersilie mit temperature_match ≥ 0.9
- In "Inkompatible Pflanzen" erscheint Tomate mit Begründung: "Temperaturzone inkompatibel: Kaltwasser (12–16°C) vs. Warmwasser-Wurzelzone (>18°C)"
- Jeder Eintrag zeigt temperature_match als numerischen Wert oder Balken

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, fisch-pflanzen-kompatibilitaet, forelle, tomate, temperaturzone]

---

## 2. Aquaponik-System CRUD (AquaponicSystemListPage / AquaponicSystemDetailPage)

### TC-026-006: Aquaponik-Systeme-Liste aufrufen — Leerstand und Tabellenstruktur

**Requirement**: REQ-026 § 4.1 — GET /systems; § 7 DoD — AquaponicSystem CRUD
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und Mitglied von Tenant "mein-garten"
- Noch keine Aquaponik-Systeme für diesen Tenant angelegt

**Testschritte**:
1. Nutzer navigiert zu `/t/mein-garten/aquaponik/systeme`

**Erwartete Ergebnisse**:
- Seite lädt mit Seitentitel "Aquaponik-Systeme"
- Leerer-Zustand-Illustration mit Text "Noch kein Aquaponik-System angelegt" ist sichtbar
- Button "System erstellen" ist rechts oben sichtbar und aktiv

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-026, aquaponik-system, listenansicht, leerzustand]

---

### TC-026-007: Aquaponik-System erstellen — Media-Bed (kein separater Biofilter erforderlich)

**Requirement**: REQ-026 § 4.1 — POST /systems; § 3 AquaponicSystemCreate; § 7 DoD — Systemtyp-Validierung
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf der Aquaponik-Systeme-Listenansicht
- Mindestens ein Tank und ein Slot/Standort sind im Tenant vorhanden

**Testschritte**:
1. Nutzer klickt "System erstellen"
2. Dialog "Aquaponik-System erstellen" öffnet sich
3. Nutzer gibt ein:
   - Name: "Goldfisch Media-Bed"
   - Systemtyp: "Media-Bed (Blähton)"
   - Gesamtvolumen: 300 (Liter)
   - Anbaufläche: 2 (m²)
   - pH Ziel Min: 6.4
   - pH Ziel Max: 7.0
4. Nutzer beachtet, dass das Feld "Biofilter-Typ" deaktiviert oder ausgeblendet ist
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schließt sich ohne Fehlermeldung
- Erfolgsmeldung (Snackbar): "Aquaponik-System 'Goldfisch Media-Bed' erstellt"
- Neues System erscheint in der Liste mit:
  - Status-Badge "Neu" (cycling_status: new)
  - Systemtyp "Media-Bed"
  - Volumen 300 L

**Nachbedingungen**:
- System "Goldfisch Media-Bed" existiert mit cycling_status "new"

**Tags**: [req-026, aquaponik-system, erstellen, media-bed, happy-path]

---

### TC-026-008: Aquaponik-System erstellen — DWC ohne Biofilter wird abgelehnt (Validierung)

**Requirement**: REQ-026 § 3 AquaponicSystemCreate model_validator — DWC/NFT benötigen separaten Biofilter; § 7 DoD — Systemtyp-Validierung
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Aquaponik-System erstellen" ist geöffnet

**Testschritte**:
1. Nutzer wählt Systemtyp: "DWC (Deep Water Culture)"
2. Nutzer lässt das Feld "Biofilter-Typ" leer / nicht ausgewählt
3. Nutzer füllt restliche Pflichtfelder: Name "Test DWC", Volumen 500, Anbaufläche 4
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Formular wird nicht abgeschickt
- Fehlermeldung erscheint unter dem Feld "Biofilter-Typ": "DWC/NFT/Hybrid/Wicking-Bed benötigen einen separaten Biofilter. Bitte Biofilter-Typ angeben."
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Kein System wurde erstellt

**Tags**: [req-026, aquaponik-system, formvalidierung, dwc, biofilter-pflicht, negativ]

---

### TC-026-009: Aquaponik-System erstellen — NFT mit Biofilter (Happy Path)

**Requirement**: REQ-026 § 3 AquaponicSystemCreate; § 4.1 POST /systems; § 7 DoD — Systemtyp-Validierung
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Dialog "Aquaponik-System erstellen" ist geöffnet

**Testschritte**:
1. Nutzer wählt Systemtyp: "NFT (Nutrient Film Technique)"
2. Nutzer gibt ein:
   - Name: "Forellen-Kräuter NFT"
   - Gesamtvolumen: 2400
   - Anbaufläche: 12
   - Biofilter-Typ: "Trickle-Filter (Lavastein)"
   - Biofilter-Volumen: 200
   - Klarifier vorhanden: Ja (Checkbox aktivieren)
   - Klarifier-Typ: "Trommelfilter"
   - Mineralisierungs-Tank: Ja (Checkbox aktivieren)
   - Outdoor: Nein
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schließt sich ohne Fehlermeldung
- Snackbar: "Aquaponik-System 'Forellen-Kräuter NFT' erstellt"
- System erscheint in der Liste mit Typ "NFT" und Status "Neu"
- In der Systemdetailansicht sind die Systemkomponenten sichtbar: Trommelfilter, Trickle-Filter, Mineralisierungs-Tank

**Nachbedingungen**:
- System "Forellen-Kräuter NFT" mit cycling_status "new" existiert

**Tags**: [req-026, aquaponik-system, nft, biofilter, klarifier, mineralisierung, happy-path]

---

### TC-026-010: Aquaponik-System erstellen — Klarifier ausgewählt ohne Klarifier-Typ (Validierung)

**Requirement**: REQ-026 § 3 AquaponicSystemCreate model_validator — has_clarifier + clarifier_type Pflicht
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Aquaponik-System erstellen" ist geöffnet

**Testschritte**:
1. Nutzer aktiviert Checkbox "Klarifier vorhanden"
2. Nutzer lässt "Klarifier-Typ" leer
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint: "Klarifier-Typ muss angegeben werden wenn 'Klarifier vorhanden' aktiviert ist."
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Kein System erstellt

**Tags**: [req-026, aquaponik-system, formvalidierung, klarifier, negativ]

---

### TC-026-011: Aquaponik-System-Detail anzeigen — Systemübersicht mit Status

**Requirement**: REQ-026 § 4.1 — GET /systems/{system_key}; § 7 DoD — AquaponicSystem CRUD
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- System "Tilapia-Salat DWC" existiert mit cycling_status "cycled"
- Fischbestand: 15 Tilapia, Biomasse 2.5 kg
- Letzte Wasserwerte vorhanden

**Testschritte**:
1. Nutzer klickt auf System "Tilapia-Salat DWC" in der Systemliste

**Erwartete Ergebnisse**:
- Detailseite lädt mit Systemname "Tilapia-Salat DWC" als Überschrift
- Status-Chip zeigt "Eingefahren" (cycling_status: cycled) in grüner Farbe
- Systemtyp "DWC", Gesamtvolumen, Anbaufläche sind sichtbar
- Abschnitt "Fischbestände" zeigt: 15 Tilapia, Biomasse 2.5 kg
- Abschnitt "Letzte Wasserwerte" zeigt aktuellen pH, TAN, Nitrit, Nitrat
- Abschnitt "Fütterungsempfehlung" ist sichtbar mit heutiger Empfehlung in Gramm

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-026, aquaponik-system, detailansicht, status-chip, cycling-cycled]

---

### TC-026-012: Aquaponik-System bearbeiten — pH-Zielbereich anpassen

**Requirement**: REQ-026 § 4.1 — PATCH /systems/{system_key}; § 1 — pH-Zielbereich Kompromisszone
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- System "Tilapia-Salat DWC" ist in der Detailansicht geöffnet
- Aktueller pH-Bereich: 6.8–7.2

**Testschritte**:
1. Nutzer klickt den Bearbeiten-Button auf der Detailseite
2. Nutzer ändert "pH Ziel Min" auf 6.6 und "pH Ziel Max" auf 7.0
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Snackbar: "System aktualisiert"
- Detailseite zeigt aktualisierten pH-Zielbereich: 6.6–7.0

**Nachbedingungen**:
- ph_target_min: 6.6, ph_target_max: 7.0 im System gespeichert

**Tags**: [req-026, aquaponik-system, bearbeiten, ph-zielbereich]

---

### TC-026-013: Aquaponik-System löschen — mit aktivem Fischbestand abgelehnt

**Requirement**: REQ-026 § 4.1 — DELETE /systems/{system_key} nur wenn kein Fischbestand; § 4 Fehlerbehandlung 409
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-Salat DWC" existiert mit aktivem Fischbestand (15 Tilapia)
- Nutzer hat Admin-Rolle im Tenant

**Testschritte**:
1. Nutzer öffnet System "Tilapia-Salat DWC"
2. Nutzer klickt den Löschen-Button
3. Bestätigungsdialog erscheint: "System 'Tilapia-Salat DWC' wirklich löschen?"
4. Nutzer klickt "Löschen"

**Erwartete Ergebnisse**:
- Fehlermeldung (Snackbar oder Dialog): "System kann nicht gelöscht werden — aktiver Fischbestand vorhanden. Zuerst alle Fischbestände entfernen."
- System bleibt in der Liste erhalten

**Nachbedingungen**:
- System und Fischbestand unverändert

**Tags**: [req-026, aquaponik-system, loeschen, aktiver-fischbestand, negativ, konflikt]

---

### TC-026-014: Aquaponik-System löschen — ohne Fischbestand erfolgreich

**Requirement**: REQ-026 § 4.1 — DELETE /systems/{system_key}; nur Admin
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- System "Test-System" existiert ohne Fischbestand
- Nutzer hat Admin-Rolle

**Testschritte**:
1. Nutzer öffnet System "Test-System"
2. Nutzer klickt Löschen-Button
3. Bestätigungsdialog erscheint
4. Nutzer bestätigt mit "Löschen"

**Erwartete Ergebnisse**:
- Snackbar: "System 'Test-System' gelöscht"
- Nutzer wird zur Systemliste zurückgeleitet
- System "Test-System" erscheint nicht mehr in der Liste

**Nachbedingungen**:
- System nicht mehr vorhanden

**Tags**: [req-026, aquaponik-system, loeschen, happy-path, admin]

---

## 3. Fischbestand-Verwaltung (FishStockSection)

### TC-026-015: Fischbestand anlegen — korrekte Besatzdichte

**Requirement**: REQ-026 § 4.3 — POST /systems/{system_key}/fish-stocks; § 7 DoD — FishStock CRUD; Szenario 1
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- System "Tilapia-Salat DWC" (500L Fischtank, DWC) ist geöffnet
- Fischart Nil-Tilapia ist im Seed-Katalog vorhanden

**Testschritte**:
1. Nutzer navigiert zum Tab "Fischbestände" auf der Systemdetailseite
2. Nutzer klickt "Bestand hinzufügen"
3. Dialog öffnet sich
4. Nutzer füllt aus:
   - Name: "Tilapia Kohorte März 2026"
   - Fischart: "Nil-Tilapia" (Auswahl aus Dropdown mit allen Fischarten)
   - Anzahl: 15
   - Durchschnittsgewicht (g): 150
   - Besatzdatum: heute
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Snackbar: "Fischbestand 'Tilapia Kohorte März 2026' hinzugefügt"
- Bestand erscheint im Abschnitt "Fischbestände" mit: 15 Fische, Biomasse 2.25 kg
- Besatzdichte-Anzeige: 4.5 kg/1000L (weit unter Maximum 25 kg/1000L für Tilapia)
- Fisch-Pflanzen-Ratio: ca. 16.9 g Futter/m² (unter 100 g/m² Empfehlung für DWC)

**Nachbedingungen**:
- Fischbestand angelegt, Biomasse berechnet aus count × avg_weight_g

**Tags**: [req-026, fischbestand, erstellen, tilapia, besatzdichte, happy-path]

---

### TC-026-016: Fischbestand anlegen — Besatzdichte-Warnung bei Überschreitung

**Requirement**: REQ-026 § 7 DoD — Besatzdichte-Prüfung; § 3 StockingDensityCalculator
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-Salat DWC" (500L Fischtank) ist geöffnet
- Nil-Tilapia max_stocking_density: 25 kg/1000L

**Testschritte**:
1. Nutzer öffnet "Bestand hinzufügen"
2. Nutzer gibt ein: Fischart "Nil-Tilapia", Anzahl 100, Durchschnittsgewicht 200 g
   (Biomasse: 100 × 200g = 20 kg, Dichte: 20 kg / 0.5 m³ = 40 kg/1000L → überschreitet Maximum 25)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Warnung oder Fehlermeldung erscheint: "Besatzdichte 40 kg/1000L überschreitet das empfohlene Maximum für Nil-Tilapia (25 kg/1000L). Bitte Anzahl oder Gewicht reduzieren."
- System erlaubt ggf. Weiterfahren mit Bestätigung (Warnung) ODER blockiert vollständig (je nach Implementierung)

**Nachbedingungen**:
- Wenn blockiert: kein Bestand erstellt; wenn Warnung: Nutzer kann bestätigen

**Tags**: [req-026, fischbestand, besatzdichte, warnung, negativ]

---

### TC-026-017: Fischbestand aktualisieren — Durchschnittsgewicht nach Wägung

**Requirement**: REQ-026 § 4.3 — PATCH /systems/{system_key}/fish-stocks/{stock_key}; § 2 FishStock last_weighed_at
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Fischbestand "Tilapia Kohorte März 2026" ist angelegt
- Ausgangswerte: 15 Fische, 150g Durchschnitt

**Testschritte**:
1. Nutzer klickt den Bearbeiten-Button beim Fischbestand
2. Nutzer ändert "Durchschnittsgewicht" auf 200 g
3. Nutzer setzt "Letzte Wägung" auf heute
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Snackbar: "Fischbestand aktualisiert"
- Biomasse-Anzeige aktualisiert sich: 15 × 200g = 3.0 kg
- "Letzte Wägung" zeigt aktuelles Datum

**Nachbedingungen**:
- Biomasse = 3.0 kg, last_weighed_at = heute

**Tags**: [req-026, fischbestand, bearbeiten, biomasse, wägung]

---

### TC-026-018: Mortalitätseintrag dokumentieren

**Requirement**: REQ-026 § 4.3 — POST /systems/{system_key}/fish-stocks/{stock_key}/mortality; § 7 DoD — FishStock CRUD Mortalitäts-Tracking
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Fischbestand "Tilapia Kohorte März 2026" mit 15 Fischen ist vorhanden

**Testschritte**:
1. Nutzer klickt "Verlust melden" beim Fischbestand
2. Dialog öffnet sich
3. Nutzer gibt ein: Anzahl Verluste: 2, Notizen: "2 Tiere tot aufgefunden"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Snackbar: "Verlust dokumentiert"
- Fischbestand zeigt aktualisierte Anzahl: 13 Fische (15 − 2)
- Biomasse wird neu berechnet: 13 × 150g = 1.95 kg
- Mortalitätszähler zeigt: 2 kumulative Verluste
- Mortalitätsrate (% pro Woche) wird in der Gesundheitsübersicht aktualisiert

**Nachbedingungen**:
- mortality_count: 2, count: 13

**Tags**: [req-026, fischbestand, mortalität, verlust, happy-path]

---

### TC-026-019: Mortalitätsrate-Warnung — Kritischer Schwellenwert überschritten

**Requirement**: REQ-026 § 3 FishHealthMonitor — MORTALITY_RATE_CRITICAL = 5%/Woche; § 7 DoD — FishHealthMonitor
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Fischbestand mit 20 Fischen (initial_count: 20)
- Innerhalb der letzten 7 Tage wurden 2 Verluste dokumentiert (10% = kritisch)

**Testschritte**:
1. Nutzer öffnet die Systemdetailseite
2. Nutzer navigiert zum Tab "Fischgesundheit"

**Erwartete Ergebnisse**:
- Gesundheits-Alert erscheint mit Severity "Kritisch" (rote Farbe)
- Meldung: "Mortalitätsrate 10%/Woche überschreitet kritischen Schwellenwert (5%). Mögliche Ursachen: schlechte Wasserqualität, Krankheit, Hitzestress."
- Empfohlene Maßnahme ist sichtbar (z.B. "Sofort Wassertest durchführen, Fütterung reduzieren")

**Nachbedingungen**:
- Alert bleibt sichtbar bis Situation sich verbessert

**Tags**: [req-026, fischgesundheit, mortalitaet, warnung, kritisch, alert]

---

### TC-026-020: Fressverhalten-Alarm — 2 aufeinanderfolgende Verweigerungen

**Requirement**: REQ-026 § 3 FishHealthMonitor — REFUSED_FEEDING_THRESHOLD = 2; § 7 DoD
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Fischbestand vorhanden
- In den letzten 2 Fütterungseinträgen war fish_response = "refused"

**Testschritte**:
1. Nutzer navigiert zum Tab "Fischgesundheit" auf der Systemdetailseite

**Erwartete Ergebnisse**:
- Health-Alert erscheint: "Fische verweigern Futter seit 2 aufeinanderfolgenden Fütterungen — mögliches Gesundheitsproblem"
- Severity: Warnung oder Kritisch
- Hinweis auf mögliche Ursachen: schlechte Wasserqualität, Krankheit, Temperaturstress

**Nachbedingungen**:
- Keine Datenänderung durch Ansicht

**Tags**: [req-026, fischgesundheit, fressverhalten, refused, gesundheitsalarm]

---

## 4. Wassertest-Erfassung und Stickstoffkreislauf

### TC-026-021: Wassertest erfassen — Happy Path mit automatischer NH3-Berechnung

**Requirement**: REQ-026 § 4.4 — POST /systems/{system_key}/water-tests; § 7 DoD — WaterTest immutable, Emerson-Formel; Szenario 2
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- System "Tilapia-Salat DWC" mit Tilapia-Fischbestand ist geöffnet

**Testschritte**:
1. Nutzer klickt "Wassertest erfassen"
2. Dialog "Wassertest erfassen" öffnet sich
3. Nutzer füllt aus:
   - pH: 7.2
   - TAN (mg/L): 1.5
   - Nitrit (mg/L): 0.3
   - Nitrat (mg/L): 45
   - Temperatur (°C): 26
   - Gelöster Sauerstoff (mg/L): 6.5
   - Karbonathärte KH (°dH): 5.0
   - Quelle: "Testkit"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Snackbar: "Wassertest gespeichert"
- Im Wassertest-Verlauf erscheint der neue Eintrag
- Berechnetes freies Ammoniak (NH3) wird angezeigt: ca. 0.0143 mg/L (unter Grenzwert 0.02 — Status: OK)
- Alert-Abschnitt zeigt: Nitrit 0.3 mg/L liegt über dem Grenzwert für Forelle (0.1 mg/L) — aber dieser Test betrifft Tilapia (Grenzwert 1.0 mg/L) → keine kritische Warnung für Tilapia

**Nachbedingungen**:
- WaterTest-Eintrag ist immutable (kein Bearbeiten/Löschen-Button sichtbar)

**Tags**: [req-026, wassertest, erstellen, nh3-berechnung, emerson, happy-path, immutable]

---

### TC-026-022: Emerson-Formel Testvektor — pH 7.0, 25°C, TAN 1.0 mg/L

**Requirement**: REQ-026 § 7 DoD — Emerson-Formel korrekt: pH 7.0, 25°C, TAN 1.0 → free NH3 ≈ 0.0057 mg/L (±5%)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Ein Aquaponik-System ist vorhanden

**Testschritte**:
1. Nutzer erfasst Wassertest mit: pH 7.0, TAN 1.0 mg/L, Temperatur 25°C, Nitrit 0.05, Nitrat 10
2. Nutzer speichert den Wassertest

**Erwartete Ergebnisse**:
- Wassertest wird gespeichert
- Angezeigtes freies Ammoniak (NH3): 0.0055–0.0060 mg/L (Toleranz ±5%)
- Status: OK (unter Grenzwert 0.02 mg/L)

**Nachbedingungen**:
- Testvektor-Kontrolle: pKa ≈ 9.245, fraction ≈ 0.0057 → NH3 ≈ 0.0057 mg/L

**Tags**: [req-026, wassertest, emerson-formel, testvektor, nh3-berechnung, grenzwert]

---

### TC-026-023: Wassertest — kritisches freies Ammoniak löst Alarm aus

**Requirement**: REQ-026 § 1 — NH3 Grenzwert <0.02 mg/L; § 7 Szenario 2 — Ammoniak-Spike Emergency
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System mit Tilapia-Bestand ist geöffnet
- pH 7.5, Temperatur 28°C

**Testschritte**:
1. Nutzer erfasst Wassertest mit:
   - pH: 7.5
   - TAN: 3.0 mg/L
   - Nitrit: 0.2 mg/L
   - Temperatur: 28°C
   - Nitrat: 30 mg/L
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Wassertest wird gespeichert
- Berechnetes NH3 ≈ 0.065 mg/L (über Grenzwert 0.02 mg/L)
- Kritischer Alert erscheint sofort: "Freies Ammoniak 0.065 mg/L — KRITISCH für Fische! Grenzwert: 0.02 mg/L"
- Sofortmaßnahmen werden angezeigt:
  - "Fütterung sofort stoppen (0g bis TAN <0.5 mg/L)"
  - "Teilwasserwechsel empfohlen (max. 20% Systemvolumen)"
  - "Belüftung maximieren"
- Fütterungsempfehlung zeigt 0 g

**Nachbedingungen**:
- Alert bleibt aktiv in der Alarmliste

**Tags**: [req-026, wassertest, nh3, kritisch, alert, sofortmassnahmen, ammoniak-spike]

---

### TC-026-024: Wassertest — artspezifischer Nitrit-Alarm für Forelle

**Requirement**: REQ-026 § 7 DoD — Artspezifische Grenzwertprüfung: Forelle max NO2 <0.1 mg/L
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System mit Regenbogenforellen-Bestand vorhanden (max_nitrite_mgl: 0.1)

**Testschritte**:
1. Nutzer erfasst Wassertest: pH 7.0, TAN 0.2, Nitrit 0.15, Nitrat 20, Temperatur 14°C
2. Nutzer speichert

**Erwartete Ergebnisse**:
- Alert erscheint: "Nitrit 0.15 mg/L überschreitet artspezifischen Grenzwert für Regenbogenforelle (max 0.1 mg/L)"
- Severity: Kritisch
- Empfehlung: Wasseraustausch, Fütterung reduzieren

**Nachbedingungen**:
- Alert aktiv bis Nitrit unter 0.1 mg/L sinkt

**Tags**: [req-026, wassertest, nitrit, forelle, artspezifisch, kritisch]

---

### TC-026-025: Wassertest-Formular — Pflichtfeld-Validierung (TAN negativ)

**Requirement**: REQ-026 § 3 WaterTestCreate — ammonia_tan_mgl: ge=0
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Wassertest erfassen" ist geöffnet

**Testschritte**:
1. Nutzer gibt pH: 7.0, TAN: -0.5 ein
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint beim TAN-Feld: "Wert muss ≥ 0 sein"
- Dialog bleibt geöffnet, Formular nicht abgeschickt

**Nachbedingungen**:
- Kein Wassertest erstellt

**Tags**: [req-026, wassertest, formvalidierung, negativ, tan-grenzwert]

---

### TC-026-026: Wassertest-Formular — Temperatur außerhalb Bereich (45°C überschritten)

**Requirement**: REQ-026 § 3 WaterTestCreate — temperature_c: ge=0, le=45
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Wassertest erfassen" ist geöffnet

**Testschritte**:
1. Nutzer gibt Temperatur: 50 ein
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Temperatur muss zwischen 0 und 45°C liegen"
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Kein Wassertest erstellt

**Tags**: [req-026, wassertest, formvalidierung, temperatur, grenzwert]

---

### TC-026-027: Wassertest — immutable (kein Bearbeiten/Löschen sichtbar)

**Requirement**: REQ-026 § 7 DoD — WaterTest immutable: Insert-only (kein Update/Delete)
**Priority**: High
**Category**: Negativ
**Preconditions**:
- Mindestens ein Wassertest-Eintrag existiert im System

**Testschritte**:
1. Nutzer öffnet die Wassertest-Historieansicht
2. Nutzer klickt auf einen vorhandenen Wassertest-Eintrag

**Erwartete Ergebnisse**:
- Kein "Bearbeiten"-Button ist sichtbar
- Kein "Löschen"-Button ist sichtbar
- Wassertest-Eintrag ist nur als Nur-Lesen-Ansicht dargestellt
- Hinweis sichtbar: "Wassertests können nicht bearbeitet werden (immutable)"

**Nachbedingungen**:
- Keine Änderung möglich

**Tags**: [req-026, wassertest, immutable, kein-bearbeiten, kein-loeschen]

---

### TC-026-028: Stickstoffkreislauf-Diagramm anzeigen (TAN/NO2/NO3 Zeitreihe)

**Requirement**: REQ-026 § 4.4 — GET /systems/{system_key}/nitrogen-cycle-chart; § 7 DoD — Cycling-Status-Transitions
**Priority**: High
**Category**: Visualisierung
**Preconditions**:
- System "Neue Anlage" hat Wassertests über 6 Wochen: Ammonia-Peak (Woche 1–2), Nitrit-Peak (Woche 3–4), Stabilisierung (Woche 5–6)

**Testschritte**:
1. Nutzer öffnet Systemdetailseite
2. Nutzer klickt auf Tab "Stickstoffkreislauf"

**Erwartete Ergebnisse**:
- Liniendiagramm erscheint mit 3 Linien: TAN (blau), Nitrit NO2 (orange), Nitrat NO3 (grün)
- Zeitreihe zeigt: TAN-Peak in Woche 1–2, dann fallend; NO2-Peak in Woche 3–4, dann fallend; NO3 stetig steigend
- X-Achse: Datum, Y-Achse: mg/L
- Eine vierte Linie für freies NH3 ist optional sichtbar (ebenfalls kleinere Skala)
- Grenzwert-Linien (horizontal, gestrichelt) zeigen artspezifische Limits

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, stickstoffkreislauf, diagramm, tan, nitrit, nitrat, visualisierung]

---

### TC-026-029: Alkalitäts-Crash-Warnung bei KH < 4°dH

**Requirement**: REQ-026 § 1 — KH <4°dH = pH-Crash-Gefahr; § 7 DoD — Alkalitäts-Crash-Warnung; Szenario 8
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-Salat DWC" mit daily_feed_target_g: 100 vorhanden

**Testschritte**:
1. Nutzer erfasst Wassertest mit: pH 7.0, TAN 0.3, Nitrit 0.05, Nitrat 25, Temperatur 26°C, KH: 3.0°dH
2. Nutzer speichert

**Erwartete Ergebnisse**:
- Kritischer Alert erscheint: "Karbonathärte 3.0°dH — pH-Crash-Risiko!"
- Erklärungstext sichtbar: "Nitrifikation verbraucht ca. 7.1 mg CaCO3 pro mg NH4-N oxidiert."
- Empfehlung: "Nachpuffern mit Ca(OH)₂ oder KOH empfohlen"
- Severity: Kritisch (rot)

**Nachbedingungen**:
- Alert aktiv

**Tags**: [req-026, wassertest, kh, alkalitiät, ph-crash, warnung, kritisch]

---

### TC-026-030: Gelöstsauerstoff-Warnung — DO unter 70% der Sättigungsgrenze

**Requirement**: REQ-026 § 7 DoD — DO-Sättigung: Warnung wenn DO < 70% der temperaturabhängigen Sättigung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Tilapia-Bestand, Temperatur 28°C (DO-Sättigung ≈ 7.8 mg/L)

**Testschritte**:
1. Nutzer erfasst Wassertest: pH 7.0, TAN 0.5, Nitrit 0.1, Nitrat 30, Temperatur 28°C, DO: 5.0 mg/L
   (70% von 7.8 mg/L = 5.46 mg/L → 5.0 liegt darunter)
2. Nutzer speichert

**Erwartete Ergebnisse**:
- Warnung erscheint: "Gelöster Sauerstoff 5.0 mg/L liegt unter 70% der Sättigung bei 28°C (70% = ca. 5.5 mg/L)"
- Empfehlung: "Belüftung prüfen und intensivieren"
- Severity: Warnung

**Nachbedingungen**:
- Warnung sichtbar in Alarmliste

**Tags**: [req-026, wassertest, do, sauerstoff, saettigung, warnung]

---

### TC-026-031: Gesamthärte GH — Warnung bei Osmosewasser (<4°dH)

**Requirement**: REQ-026 § 3 NitrogenCycleEngine.evaluate_water_quality — GH <4°dH Warnung bei Osmose/Regenwasser
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- System ist geöffnet

**Testschritte**:
1. Nutzer erfasst Wassertest mit GH: 2.0°dH (unter Schwelle 4°dH)
2. Nutzer speichert

**Erwartete Ergebnisse**:
- Warnung erscheint: "Gesamthärte 2.0°dH — möglicher Ca/Mg-Mangel (typisch bei Osmose- oder Regenwasser)"
- Empfehlung zu Ca- oder Mg-Supplementierung wird angezeigt

**Nachbedingungen**:
- Warnung in Alarmliste aktiv

**Tags**: [req-026, wassertest, gh, osmose, calcium-mangel, warnung]

---

## 5. Biofilter-Cycling (CyclingProgressCard)

### TC-026-032: Cycling-Fortschritt anzeigen — Status "Neu"

**Requirement**: REQ-026 § 4.4 — GET /systems/{system_key}/cycling-progress; § 7 DoD — Cycling-Status-Transitions
**Priority**: Critical
**Category**: Visualisierung
**Preconditions**:
- System "Neue Anlage" mit cycling_status "new" ist angelegt
- Noch keine Wassertests erfasst

**Testschritte**:
1. Nutzer öffnet System "Neue Anlage"
2. Nutzer klickt auf Tab "Biofilter-Cycling"

**Erwartete Ergebnisse**:
- Status-Badge: "Neu" (grau oder blau)
- Fortschrittsbalken: 0%
- Phasenbeschreibung: "Biofilter frisch befüllt — Nitrifikationsbakterien noch nicht aktiv"
- Hinweis: "Noch keine Fische einsetzen. Erst Ammoniakquelle hinzufügen um Cycling zu starten."

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, cycling, status-neu, fortschritt]

---

### TC-026-033: Cycling-Status new → cycling durch ersten TAN-Messwert >0.5 mg/L

**Requirement**: REQ-026 § 1 — Cycling-Erkennung: new → cycling bei erstem TAN >0.5 mg/L; § 7 DoD Szenario 3
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- System "Neue Anlage" hat cycling_status "new"

**Testschritte**:
1. Nutzer erfasst Wassertest: pH 7.2, TAN 0.8 mg/L (>0.5), Nitrit 0.0, Nitrat 0, Temperatur 24°C
2. Nutzer speichert Wassertest
3. Nutzer klickt Tab "Biofilter-Cycling"

**Erwartete Ergebnisse**:
- Cycling-Status hat sich geändert: "Cycling" (Einfahrphase)
- Fortschrittsbalken: > 0%
- Phasenbeschreibung: "Nitrosomonas-Bakterien bauen sich auf — Ammoniak-Peak normal"
- Warnung sichtbar: "Noch keine Fische in voller Besatzdichte einsetzen!"

**Nachbedingungen**:
- cycling_status: "cycling"

**Tags**: [req-026, cycling, zustandswechsel, new-to-cycling, tan-peak]

---

### TC-026-034: Cycling-Status cycling → cycled nach 7 stabilen Tagen

**Requirement**: REQ-026 § 1 — cycling → cycled: TAN <0.25 UND NO2 <0.1 für ≥7 aufeinanderfolgende Tage; § 7 DoD
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- System hat cycling_status "cycling"
- 7 aufeinanderfolgende Wassertests mit TAN <0.25 UND NO2 <0.1 bei Wassertemperatur >15°C und ≥80% der Zielfuttermenge wurden erfasst

**Testschritte**:
1. Nutzer öffnet Tab "Biofilter-Cycling"

**Erwartete Ergebnisse**:
- Status-Badge wechselt auf "Eingefahren" (cycled) in grüner Farbe
- Fortschrittsbalken: 100%
- Erfolgsmeldung: "Biofilter eingefahren — volle Besatzdichte möglich"
- Empfehlung: "Fische einsetzen (Ramp-up: Woche 1 mit 25% Zielfuttermenge beginnen)"
- stable_days: 7 angezeigt

**Nachbedingungen**:
- cycling_status: "cycled"

**Tags**: [req-026, cycling, zustandswechsel, cycled, 7-tage-stabil]

---

### TC-026-035: Cycling-Status cycled → dormant bei Temperatur <10°C für 7 Tage

**Requirement**: REQ-026 § 1 — cycled → dormant: Wassertemperatur <10°C für ≥7 Tage; § 7 DoD
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Outdoor-System mit cycling_status "cycled"
- 7 aufeinanderfolgende Wassertests mit Temperatur <10°C wurden erfasst (Winterbedingungen)

**Testschritte**:
1. Nutzer öffnet Tab "Biofilter-Cycling"

**Erwartete Ergebnisse**:
- Status wechselt auf "Winterruhe" (dormant)
- Phasenbeschreibung: "Biofilter-Bakterien inaktiv bei <10°C — Nitrifikation gestoppt"
- Empfehlung: "Fütterung einstellen oder stark reduzieren. Biofilter muss im Frühling neu eingefahren werden."

**Nachbedingungen**:
- cycling_status: "dormant"

**Tags**: [req-026, cycling, zustandswechsel, dormant, winter, outdoor]

---

### TC-026-036: Cycling-Status manuell überschreiben

**Requirement**: REQ-026 § 4.1 — POST /systems/{system_key}/cycling-status; § 7 DoD — Cycling-Status-Transitions
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- System mit cycling_status "cycling" ist geöffnet

**Testschritte**:
1. Nutzer klickt "Status manuell setzen" auf der Cycling-Tab-Ansicht
2. Dialog öffnet sich
3. Nutzer wählt: Neuer Status "Eingefahren (cycled)"
4. Nutzer klickt "Bestätigen"

**Erwartete Ergebnisse**:
- Bestätigungsdialog: "Status manuell auf 'Eingefahren' setzen? Diese Aktion überschreibt die automatische Erkennung."
- Nach Bestätigung: Status-Badge wechselt auf "Eingefahren"
- Snackbar: "Cycling-Status manuell aktualisiert"

**Nachbedingungen**:
- cycling_status: "cycled" (manuell gesetzt)

**Tags**: [req-026, cycling, manueller-override, status-setzen]

---

## 6. Fütterungsempfehlung und Fütterungsereignisse

### TC-026-037: Fütterungsempfehlung anzeigen — temperaturkorrigierte Berechnung

**Requirement**: REQ-026 § 4.5 — GET /systems/{system_key}/feeding-recommendation; § 3 FeedingRateCalculator
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- System "Tilapia-Salat DWC" mit 15 Tilapia (Biomasse 2.5 kg) ist geöffnet
- cycling_status: "cycled"
- Aktueller Wassertest zeigt Temperatur 22°C (unter Optimum 26–30°C)

**Testschritte**:
1. Nutzer öffnet Systemdetailseite
2. Nutzer klickt auf Tab "Fütterung"

**Erwartete Ergebnisse**:
- Fütterungsempfehlung-Karte zeigt:
  - Empfohlene Menge: ca. 56.25 g (2.5 kg × 3% × Temperatur-Faktor 0.75)
  - Hinweis: "Wassertemperatur 22°C liegt unter Optimum (26–30°C) — Futtermenge um 25% reduziert (Q10-Korrektur)"
  - Biofilter-Status: "Eingefahren — volle Fütterung erlaubt"
  - Biomasse: 2.5 kg, Fischart: Nil-Tilapia

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, fütterungsempfehlung, q10, temperaturkorrektur, cycling-cycled]

---

### TC-026-038: Fütterungsempfehlung 0g bei kritischem Ammoniak-Spike

**Requirement**: REQ-026 § 3 FeedingRateCalculator — Bei fish_response='refused': Empfehlung 0g; Szenario 2
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System mit aktuellem Wassertest TAN >2.0 mg/L (über Tilapia-Grenzwert) und free_NH3 >0.02 mg/L

**Testschritte**:
1. Nutzer navigiert zu Tab "Fütterung"

**Erwartete Ergebnisse**:
- Empfehlung zeigt: 0 g
- Roter Warnhinweis: "Fütterung stoppen! TAN-Wert kritisch erhöht (3.0 mg/L > Grenzwert 2.0 mg/L für Nil-Tilapia)."
- Anleitung: "Erst wieder füttern wenn TAN <0.5 mg/L"

**Nachbedingungen**:
- Empfehlung bleibt 0g bis Situation sich normalisiert

**Tags**: [req-026, fütterungsempfehlung, fütterungsstopp, ammoniak, kritisch]

---

### TC-026-039: Ramp-up-Plan anzeigen nach Frühlings-Reaktivierung (Dormanz → Cycling)

**Requirement**: REQ-026 § 1 — Saisonaler Ramp-up; § 3 FeedingRateCalculator.calculate_ramp_up_schedule; § 7 Szenario 6
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Outdoor-System mit cycling_status "dormant" seit November 2025
- Aktueller Wassertest: Temperatur 16°C (zwischen 15–20°C)
- Fütterung wird wieder aufgenommen

**Testschritte**:
1. Nutzer erfasst Fütterungsereignis: 75g (volle Zielmenge)
2. Nutzer öffnet Tab "Fütterung" → Ramp-up-Empfehlung

**Erwartete Ergebnisse**:
- Warnung erscheint: "Biofilter war im Winterschlaf — Ramp-up-Plan empfohlen!"
- Cycling-Status wechselt auf "Cycling" (Reaktivierung)
- Ramp-up-Plan-Tabelle ist sichtbar:
  - Bei 16°C (unter 20°C): verlängerter Plan (~14 Wochen)
  - Stufe 1 (Woche 1–2): 18.75 g (25% von 75g)
  - Stufe 2 (Woche 3–4): 37.5 g (50%)
  - Stufe 3 (Woche 5–6): 56.25 g (75%)
  - Stufe 4 (ab Woche 7): 75 g (100%)
- Wasserqualitäts-Gate sichtbar: "Nächste Stufe nur freischalten wenn TAN <0.5 UND NO2 <0.5 mg/L"

**Nachbedingungen**:
- cycling_status: "cycling" (Reaktivierung)

**Tags**: [req-026, rampup, dormanz, fruehling, saisonal, wasserqualitaets-gate]

---

### TC-026-040: Fütterungsereignis dokumentieren — Normal mit Futtermarke

**Requirement**: REQ-026 § 4.5 — POST /systems/{system_key}/feeding-events; § 3 FishFeedingEventCreate
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- System mit Fischbestand ist geöffnet

**Testschritte**:
1. Nutzer klickt "Fütterung dokumentieren"
2. Dialog öffnet sich
3. Nutzer füllt aus:
   - Futtermarke: "Coppens Tilapia Grower"
   - Futtertyp: "Pellet"
   - Proteingehalt: 32%
   - Menge (g): 75
   - Wassertemperatur (°C): 26
   - Fressverhalten: "Normal"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Snackbar: "Fütterung dokumentiert"
- Eintrag erscheint im Fütterungsverlauf mit: Datum, 75 g, "Normal", "Coppens Tilapia Grower"

**Nachbedingungen**:
- FeedingEvent ist immutable (kein Bearbeiten/Löschen sichtbar)

**Tags**: [req-026, fütterungsereignis, dokumentieren, happy-path, immutable]

---

### TC-026-041: Fütterungsereignis — Fressverhalten "Verweigert" mit Warnung

**Requirement**: REQ-026 § 3 FeedingRateCalculator — Bei fish_response='refused': Empfehlung 0g + Warnung; § 7 DoD
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Fischbestand geöffnet

**Testschritte**:
1. Nutzer dokumentiert Fütterung: Menge 75g, Fressverhalten "Verweigert (refused)"
2. Nutzer speichert

**Erwartete Ergebnisse**:
- Fütterungseintrag wird gespeichert
- Warnung erscheint: "Fische haben Futter verweigert — mögliches Warnsignal!"
- Wenn 2+ aufeinanderfolgende "Verweigert": Gesundheitsalarm erscheint (vgl. TC-026-020)

**Nachbedingungen**:
- FeedingEvent mit fish_response "refused" gespeichert

**Tags**: [req-026, fütterungsereignis, fressverhalten, refused, warnung]

---

## 7. Supplementierung und Nährstoffdefizit-Analyse

### TC-026-042: Nährstoffdefizit-Analyse anzeigen — Eisenmangel erkannt

**Requirement**: REQ-026 § 4.6 — GET /systems/{system_key}/deficiency-check; § 7 DoD Szenario 7 — Eisenmangel
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- System mit Wassertest: iron_ppm = 0.5 (unter Zielwert 2–5 ppm)

**Testschritte**:
1. Nutzer öffnet Tab "Nährstoffe / Supplementierung"
2. Nutzer klickt "Defizit-Analyse"

**Erwartete Ergebnisse**:
- Abschnitt "Nährstoffdefizite" erscheint
- Eintrag: "Eisen 0.5 ppm — unter Zielwert (2–5 ppm)" mit Severity Warnung
- Empfehlung: "Fe-DTPA nachdosieren (fischsicher, stabil bis pH 7.5)"
- Hinweis: "NICHT Fe-EDTA verwenden (instabil bei pH >6.5)"
- K, Ca, Mg werden ebenfalls geprüft und als "OK" oder mit spezifischen Werten angezeigt

**Nachbedingungen**:
- Keine Datenänderung (Lesevorgang)

**Tags**: [req-026, naehrstoffdefizit, eisen, fe-dtpa, fe-edta, empfehlung]

---

### TC-026-043: Nährstoffdefizit — Phosphat-Akkumulationswarnung >80 ppm

**Requirement**: REQ-026 § 1 Nährstofftabelle — PO4 >80 ppm Teilwasserwechsel oder P-reiche Pflanzen; § 7 DoD
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Wassertest: phosphate_ppm = 95 (über 80 ppm Warnschwelle)

**Testschritte**:
1. Nutzer öffnet Defizit-Analyse

**Erwartete Ergebnisse**:
- Warnung: "Phosphat 95 ppm — Akkumulation! Empfehlung: Teilwasserwechsel oder P-reiche Pflanzen (Tomaten, Paprika) einsetzen."
- Hinweis: "Phosphat-Überangebot reduziert Eisenverfügbarkeit (Fe-P-Präzipitation) und fördert Algenblüten."

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, naehrstoffdefizit, phosphat, akkumulation, warnung]

---

### TC-026-044: Supplementierungs-Ereignis dokumentieren — Fe-DTPA

**Requirement**: REQ-026 § 4.6 — POST /systems/{system_key}/supplementation-events; § 3 SupplementationEventCreate
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- System ist geöffnet, Eisenmangel wurde erkannt

**Testschritte**:
1. Nutzer klickt "Supplementierung dokumentieren"
2. Dialog öffnet sich
3. Nutzer füllt aus:
   - Ergänzungsmittel-Typ: "Fe-DTPA (Chelat-Eisen, bis pH 7.5)"
   - Menge (ml): 10
   - Zielparameter: "Eisen"
   - Messwert vorher: 0.5 ppm
   - Messwert nachher: 2.8 ppm
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Snackbar: "Supplementierung dokumentiert"
- Eintrag erscheint im Supplementierungsverlauf mit: Datum, Fe-DTPA, 10 ml, vorher 0.5 → nachher 2.8 ppm

**Nachbedingungen**:
- SupplementationEvent ist immutable (kein Bearbeiten/Löschen)

**Tags**: [req-026, supplementierung, fe-dtpa, dokumentieren, happy-path, immutable]

---

### TC-026-045: Supplementierungs-Formular — weder amount_ml noch amount_g angegeben

**Requirement**: REQ-026 § 3 SupplementationEventCreate model_validator — Entweder amount_ml oder amount_g Pflicht
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Supplementierung dokumentieren" ist geöffnet

**Testschritte**:
1. Nutzer wählt Ergänzungsmittel-Typ: "MgSO4 (Bittersalz)"
2. Nutzer lässt beide Mengenfelder (ml und g) leer
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Entweder Menge (ml) oder Menge (g) muss angegeben werden"
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Kein Eintrag erstellt

**Tags**: [req-026, supplementierung, formvalidierung, pflichtfeld, negativ]

---

### TC-026-046: Borüberdosierungs-Warnung sichtbar im Supplementierungsdialog

**Requirement**: REQ-026 § 1 Nährstofftabelle — H3BO3 sehr enger Toxizitätsbereich (>1 ppm schädigt Pflanzen UND Fische)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Supplementierung dokumentieren" ist geöffnet

**Testschritte**:
1. Nutzer wählt Ergänzungsmittel-Typ: "H3BO3 (Borsäure)"

**Erwartete Ergebnisse**:
- Prominente Warnmeldung erscheint sofort nach Auswahl: "Sehr enger Toxizitätsbereich! Überdosierung >1 ppm schädigt Pflanzen UND Fische. Zielwert: 0.1–0.5 ppm. Mit höchster Vorsicht dosieren."
- Warnfarbe: Orange oder Rot

**Nachbedingungen**:
- Keine Datenänderung durch Auswahl alleine

**Tags**: [req-026, supplementierung, borsäure, toxizitaet, warnung, h3bo3]

---

## 8. Sicherheitsvalidierung (AquaponicsSafetyValidator)

### TC-026-047: Synthetischer Dünger auf Aquaponik-System blockiert

**Requirement**: REQ-026 § 3 AquaponicsSafetyValidator.validate_fertilizer_safe; § 7 DoD — AquaponicsSafetyValidator; Szenario 4
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-Salat DWC" ist mit einem Fischtank verbunden
- Dünger "Flora Micro" mit aquaponic_safe: false ist im Dünger-Katalog vorhanden (REQ-004)

**Testschritte**:
1. Nutzer navigiert zur Düngekalkulation (REQ-004) für den mit dem Aquaponik-System verbundenen Tank
2. Nutzer versucht, "Flora Micro" (synthetischer Dünger, aquaponic_safe: false) der Düngemischung hinzuzufügen

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint: "Synthetischer Dünger 'Flora Micro' ist nicht fischsicher (aquaponic_safe=false). Dieser Dünger darf in Aquaponik-Systemen nicht verwendet werden."
- "Flora Micro" kann nicht hinzugefügt werden (Button deaktiviert oder Ablehnung nach Klick)
- Hinweis auf erlaubte Alternativen: "Erlaubt: Fe-DTPA, KOH, Ca(OH)₂, MgSO4"

**Nachbedingungen**:
- Kein Dünger auf Aquaponik-System angewendet

**Tags**: [req-026, sicherheit, synthetischer-duenger, aquaponic-safe, block, req-004]

---

### TC-026-048: Kupfer-Pestizid auf Aquaponik-System blockiert

**Requirement**: REQ-026 § 3 AquaponicsSafetyValidator.validate_no_copper_pesticide; § 7 DoD — Kupfer-PSM-Verbot
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-Salat DWC" mit Fischbestand ist geöffnet
- Kupferhaltiges Pflanzenschutzmittel ist im IPM-Katalog (REQ-010) vorhanden

**Testschritte**:
1. Nutzer navigiert zur IPM-Behandlung (REQ-010) für eine Pflanze im Aquaponik-System
2. Nutzer versucht, ein kupferhaltiges PSM auszuwählen

**Erwartete Ergebnisse**:
- Fehlermeldung: "Kupferhaltiges Pflanzenschutzmittel in Aquaponik-Systemen verboten! Kupfer ist bereits bei >0.1 ppm fischgiftig."
- Anwendung wird blockiert (Button deaktiviert oder Ablehnung)

**Nachbedingungen**:
- Kein kupferhaltiges PSM auf Aquaponik-Pflanzen angewendet

**Tags**: [req-026, sicherheit, kupfer-psm, verboten, block, req-010]

---

### TC-026-049: Chlor-Warnung bei Leitungswasser-Wasserauffüllung

**Requirement**: REQ-026 § 3 AquaponicsSafetyValidator.validate_no_chlorine; § 7 DoD — Chlor-Warnung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System ist geöffnet
- Nutzer füllt Wasser auf (oder erfasst Wasserquelle "Leitungswasser")

**Testschritte**:
1. Nutzer dokumentiert Wasserzugabe aus Leitungswasser
2. Chlorgehalt ist im Wasserquellen-Profil hinterlegt (z.B. 0.1 ppm freies Chlor)

**Erwartete Ergebnisse**:
- Warnung erscheint: "Leitungswasser enthält freies Chlor (0.1 ppm) — vor Zugabe abstehen lassen (24–48h) oder Vitamin C (Ascorbinsäure) zum Entchloren verwenden."
- Falls Chloramin-Wert vorhanden: Strenge Warnung: "Chloramin kann NICHT durch Abstehen entfernt werden — Aktivkohlefilter oder Ascorbinsäure-Behandlung erforderlich."

**Nachbedingungen**:
- Warnung erscheint, Nutzer kann fortfahren wenn Chlor-Entfernung bestätigt

**Tags**: [req-026, sicherheit, chlor, leitungswasser, warnung, entchloren]

---

### TC-026-050: Wasserwechsel-Warnung bei >20% Systemvolumen

**Requirement**: REQ-026 § 3 AquaponicsSafetyValidator.validate_water_change_rate; § 7 DoD — Wasserwechsel-Limit
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Gesamtvolumen 640L ist geöffnet

**Testschritte**:
1. Nutzer dokumentiert einen Wasserwechsel von 150L (>20% von 640L = 128L)

**Erwartete Ergebnisse**:
- Warnung erscheint: "Wasserwechsel 150L (23.4%) überschreitet empfohlenes Maximum von 20% (128L). Große Wasserwechsel verursachen pH/Temperatur-Schock."
- Nutzer kann trotzdem mit Bestätigung fortfahren

**Nachbedingungen**:
- Wenn bestätigt: Wasserwechsel dokumentiert mit Warnsymbol

**Tags**: [req-026, sicherheit, wasserwechsel, 20-prozent, warnung]

---

### TC-026-051: pH-Korrektur mit Säure — Hard-Block für Einsteiger

**Requirement**: REQ-026 § 1 — Kritische Regel pH-Korrektur: keine Säuren als pH-Down (Einsteiger: Hard-Block)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Einsteiger" oder "Fortgeschritten" (nicht "Experte")
- System ist geöffnet

**Testschritte**:
1. Nutzer navigiert zu pH-Korrektur-Werkzeug des Systems
2. Nutzer versucht eine Säure (z.B. Phosphorsäure H3PO4 oder Salpetersäure HNO3) als pH-Down-Maßnahme hinzuzufügen

**Erwartete Ergebnisse**:
- Hard-Block-Meldung erscheint: "Säuren als pH-Down in Aquaponik-Systemen nicht erlaubt! Der pH senkt sich natürlich durch Nitrifikation — abwarten ist die korrekte Maßnahme."
- Aktion wird vollständig blockiert (kein "trotzdem fortfahren")
- Empfehlung: "pH-Up: Alternierend KOH und Ca(OH)₂ verwenden (gleichzeitige K- und Ca-Versorgung)"

**Nachbedingungen**:
- Kein pH-Eingriff mit Säure dokumentiert

**Tags**: [req-026, sicherheit, ph-korrektur, saeure-verbot, einsteiger, hard-block, req-021]

---

### TC-026-052: pH-Korrektur mit Phosphorsäure für Experten erlaubt (mit Einschränkung)

**Requirement**: REQ-026 § 1 — Ausnahme Experten (REQ-021): H3PO4 max 0.5 mL/100L, pH nicht unter 6.5
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Experte" (REQ-021)
- System mit sehr hartem Leitungswasser (KH >15°dH) ist geöffnet

**Testschritte**:
1. Nutzer navigiert zu pH-Korrektur
2. Nutzer wählt "Phosphorsäure (H3PO4)" als pH-Down-Maßnahme

**Erwartete Ergebnisse**:
- Keine vollständige Blockierung (Expertenmodus freigegeben)
- Warnung erscheint: "Nur für Experten: Max. 0.5 mL/100L. pH darf nie unter 6.5 gesenkt werden. Nur bei KH >15°dH wenn Nitrifikation pH nicht ausreichend senkt."
- Mengen-Eingabefeld mit Maximum-Begrenzer (0.5 mL/100L)

**Nachbedingungen**:
- Wenn gespeichert: SupplementationEvent mit Expertenmodus-Flag dokumentiert

**Tags**: [req-026, sicherheit, ph-korrektur, phosphorsäure, experte, req-021]

---

## 9. Alarme und Sicherheitsstatus (AlertsSection)

### TC-026-053: Alarm-Übersicht — alle aktiven Warnungen sortiert nach Severity

**Requirement**: REQ-026 § 4.7 — GET /systems/{system_key}/alerts; § 7 DoD
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- System hat mehrere aktive Alerts: free_NH3 kritisch, Nitrit-Warnung (Tilapia), KH niedrig

**Testschritte**:
1. Nutzer öffnet Tab "Alarme" auf der Systemdetailseite

**Erwartete Ergebnisse**:
- Alarm-Liste ist nach Severity sortiert: Kritisch (rot) zuerst, dann Warnung (orange), dann Info (blau)
- Für jeden Alarm: Parameter, gemessener Wert, Grenzwert, Empfehlung
- Zeitstempel des letzten relevanten Wassertests ist bei jedem Alarm sichtbar
- Button "Sofortmaßnahmen" ist für kritische Alarme vorhanden

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, alarme, severity, sortierung, sofortmassnahmen]

---

### TC-026-054: Gesamtsicherheits-Status anzeigen — alle grün

**Requirement**: REQ-026 § 4.7 — GET /systems/{system_key}/safety-status
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- System "Tilapia-Salat DWC" mit allen Parametern im Normalbereich
- Letzter Wassertest: NH3 < 0.02, NO2 < 1.0, Temp im Optimalbereich, DO > 5.0

**Testschritte**:
1. Nutzer navigiert zur Systemübersicht / Dashboard-Karte

**Erwartete Ergebnisse**:
- Sicherheits-Status-Karte zeigt alle Indikatoren grün:
  - Wasserwerte: OK
  - Besatzdichte: OK
  - Temperatur: OK
  - Biofilter: Eingefahren
  - Sauerstoff: OK

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, sicherheitsstatus, alle-gruen, dashboard]

---

## 10. Fischgesundheit (FishHealthSection)

### TC-026-055: FCR-Analyse anzeigen — Futterverwertungsrate

**Requirement**: REQ-026 § 4.5 — GET /systems/{system_key}/fcr-analysis; § 3 FeedingRateCalculator
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- System mit 30 Tagen Fütterungs- und Gewichtsdaten

**Testschritte**:
1. Nutzer klickt auf Tab "Fütterung" → Unterabschnitt "FCR-Analyse"

**Erwartete Ergebnisse**:
- FCR-Wert wird angezeigt: z.B. "FCR letzte 30 Tage: 1.9"
- Referenzwert für Tilapia (Hobby): 1.8 ist sichtbar
- Bewertung: "Leicht über Referenz (1.8) — Fressverhalten prüfen"

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, fcr, futterverwertung, analyse]

---

### TC-026-056: Temperaturstress-Warnung bei Temperatur außerhalb Optimalbereich

**Requirement**: REQ-026 § 3 NitrogenCycleEngine.evaluate_water_quality — Temperatur-Schwellenstufen: info/warning/critical
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Regenbogenforellen (optimal 12–16°C, max 18°C)
- Letzter Wassertest Temperatur: 20°C (über temperature_max_c)

**Testschritte**:
1. Nutzer öffnet Tab "Alarme"

**Erwartete Ergebnisse**:
- Warnung erscheint: "Wassertemperatur 20°C überschreitet Stressbereich für Regenbogenforelle (max 18°C)"
- Severity: Warnung
- Empfehlung: Kühlung, Beschattung, Wasserwechsel mit kühlerem Wasser

**Nachbedingungen**:
- Warnung aktiv

**Tags**: [req-026, temperatur, stressbereich, forelle, warnung]

---

### TC-026-057: Letale Temperatur — Kritischer Alert

**Requirement**: REQ-026 § 3 NitrogenCycleEngine.evaluate_water_quality — temperature_c > temperature_lethal_high: critical
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- System mit Regenbogenforellen (lethal_high: 22°C)
- Wassertest Temperatur: 23°C (über temperature_lethal_high_c)

**Testschritte**:
1. Nutzer erfasst Wassertest mit Temperatur 23°C
2. Nutzer speichert

**Erwartete Ergebnisse**:
- Kritischer Alert erscheint sofort: "Wassertemperatur 23°C überschreitet Letalgrenze für Regenbogenforelle (22°C) — UNMITTELBARE LEBENSGEFAHR!"
- Severity: Kritisch (rot, prominent)
- Sofortmaßnahmen sichtbar

**Nachbedingungen**:
- Kritischer Alert bleibt aktiv

**Tags**: [req-026, temperatur, letal, kritisch, sofortmassnahmen, forelle]

---

## 11. Temperaturzonen und Fisch-Pflanzen-Inkompatibilität

### TC-026-058: Warmwasser-Fisch + Kaltwasser-Pflanze — Inkompatibilitäts-Warnung beim Anlegen

**Requirement**: REQ-026 § 3 AquaponicsSafetyValidator.validate_temperature_compatibility; § 7 DoD — Temperaturzonen-Match; Szenario 5
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-DWC" mit Tilapia (warmwater, 26–30°C)
- Nutzer versucht Salat-Pflanzung einem DWC-Growbed zuzuordnen, der mit dem System verbunden ist
- Aber zusätzlich: Nutzer möchte Tomate (benötigt Wurzelzone >18°C) hinzufügen — passt, kein Problem
- Test: Nutzer versucht eine Pflanze hinzuzufügen die explizit als incompatible_fish_plant markiert ist

**Testschritte**:
1. Nutzer navigiert zu Tab "Growbeds / Pflanzen" auf der Systemdetailseite
2. Nutzer versucht eine inkompatible Pflanzenkombination zuzuordnen (z.B. Erdbeere im Warmwasser-System mit Tilapia)

**Erwartete Ergebnisse**:
- Warnung erscheint: "Temperaturzone inkompatibel: Nil-Tilapia (Warmwasser, 26–30°C) vs. Erdbeere (benötigt kühlere Wassertemperatur)"
- Nutzer kann trotzdem zuordnen (Warnung, kein Block), aber Warnung bleibt in Systemalarmen

**Nachbedingungen**:
- Warnung persistiert in Alarmliste

**Tags**: [req-026, temperaturzone, fisch-pflanze-kompatibilitaet, warnung, inkompatibel]

---

### TC-026-059: Salat schosst im Sommer — Saisonale Warnung bei >25°C

**Requirement**: REQ-026 § 1 — Sommer-Hinweis: Salat schosst bei >25°C und >14h Tageslicht
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- System "Tilapia-Salat DWC", Sommer, Temperatur 27°C
- Salat ist im DWC-Growbed eingepflanzt

**Testschritte**:
1. Nutzer öffnet Systemdetailseite
2. Nutzer öffnet Tab "Alarme / Hinweise"

**Erwartete Ergebnisse**:
- Saisonaler Hinweis erscheint: "Salat kann bei >25°C schossen (Bolting) — hitzetolerante Sorten wählen oder Beschattung vorsehen"
- Severity: Info (blau)

**Nachbedingungen**:
- Hinweis sichtbar

**Tags**: [req-026, saisonal, salat, sommer, bolting, info]

---

## 12. Regulatorische Hinweise und Artenschutz

### TC-026-060: Regulatorische Hinweise für Tilapia anzeigen — Hobby-Ausnahme

**Requirement**: REQ-026 § 7 DoD — Regulatorische Hinweise; § 2 Seed-Daten Tilapia regulatory_notes
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Fischbestand mit Nil-Tilapia angelegt

**Testschritte**:
1. Nutzer öffnet Fischart-Detailseite "Nil-Tilapia"
2. Nutzer navigiert zu Abschnitt "Regulatorische Hinweise"

**Erwartete Ergebnisse**:
- Hinweis für DE: "Hobby: keine Einschränkung. Gewerblich: Sachkundenachweis §11 TierSchG erforderlich."
- Hobby-Ausnahme visuell hervorgehoben (grünes Symbol oder "Hobby: frei")

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, regulatorisch, tilapia, hobby-ausnahme, tierschutzgesetz]

---

### TC-026-061: Regulatorische Hinweise für Zander — Sachkundenachweis

**Requirement**: REQ-026 § 2 Seed-Daten Zander regulatory_notes; § 7 DoD — Regulatorische Hinweise
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- FishSpeciesListPage aufgerufen

**Testschritte**:
1. Nutzer klickt auf "Zander" (Sander lucioperca)
2. Nutzer navigiert zu "Regulatorische Hinweise"

**Erwartete Ergebnisse**:
- Hinweis für DE: "Gewerbliche Haltung: Sachkundenachweis (TierSchG §11)"
- Hobby-Ausnahme: "Hobby: frei"

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, regulatorisch, zander, sachkundenachweis, tierschutz]

---

## 13. Saisonale Outdoor-Aquaponik

### TC-026-062: Outdoor-System — saisonale Fütterungsanpassung Herbst

**Requirement**: REQ-026 § 1 — Saisonale Aspekte DACH, Herbst: Futtermenge reduzieren; § 7 DoD — Saisonale Logik
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Outdoor-Aquaponik-System mit cycling_status "cycled"
- Aktuelles Datum: Oktober (Herbst)
- Wassertemperatur: 14°C (sinkend)

**Testschritte**:
1. Nutzer öffnet Tab "Fütterung" auf dem Outdoor-System

**Erwartete Ergebnisse**:
- Saisonaler Hinweis erscheint: "Herbst-Modus: Wassertemperatur sinkt — Futtermenge reduzieren"
- Fütterungsempfehlung ist temperaturkorrigiert geringer als im Sommer
- Hinweis: "Biofilter-Kapazität nimmt mit fallenden Temperaturen ab"

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, saisonal, herbst, outdoor, fütterung, temperaturkorrektur]

---

### TC-026-063: Biofilter-Kapazität bei Niedrigtemperatur — Nitrifikations-Untergrenze

**Requirement**: REQ-026 § 7 DoD — Nitrifikations-Untergrenze: Biofilter-Kapazität = 0 unter 5°C, <10% bei 5–10°C
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Outdoor-System, letzter Wassertest: Temperatur 4°C

**Testschritte**:
1. Nutzer öffnet Tab "Biofilter-Cycling" oder "Alarme"

**Erwartete Ergebnisse**:
- Warnung erscheint: "Wassertemperatur 4°C — Nitrifikation praktisch gestoppt (<5°C). Biofilter hat keine Kapazität."
- Fütterungsempfehlung: 0g oder minimal
- Empfehlung: "System auf Winterruhe (Dormanz) vorbereiten"

**Nachbedingungen**:
- Cycling-Status wird auf "Dormant" vorbereitet oder ist bereits gewechselt

**Tags**: [req-026, biofilter, nitrifikation, untergrenze, 5grad, winter]

---

## 14. Besatzdichte und Fisch-Pflanzen-Verhältnis

### TC-026-064: Besatzdichte-Karte anzeigen — OK-Status

**Requirement**: REQ-026 § 3 StockingDensityCalculator; § 7 DoD — Besatzdichte-Prüfung; Szenario 1
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- System "Tilapia-Salat DWC" (500L Fischtank), 15 Tilapia, 150g Durchschnitt
- Biomasse: 2.25 kg, Dichte: 4.5 kg/1000L (max: 25 kg/1000L)

**Testschritte**:
1. Nutzer öffnet Systemdetailseite
2. Nutzer klickt auf Tab "Fischbestände / Besatzdichte"

**Erwartete Ergebnisse**:
- Besatzdichte-Anzeige: "4.5 kg/1000L" mit Status "OK" (grün)
- Auslastung: 18% (von 25 kg/1000L Maximum)
- Fisch-Pflanzen-Ratio: "16.9 g Futter/m²/Tag" (unter 100 g/m²-Empfehlung für DWC)
- Visualisierung (Fortschrittsbalken oder Gauge) zeigt verbleibenden Spielraum

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, besatzdichte, fisch-pflanzen-ratio, ok, visualisierung]

---

### TC-026-065: Biofilter-Dimensionierung — Warnung bei unzureichender Kapazität

**Requirement**: REQ-026 § 3 BiofilterManager.estimate_required_surface_area; § 7 DoD — Biofilter-Kapazität
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- System mit Biofilter-Volumen 20L (MBBR, SSA 650 m²/m³)
- Futtermenge 200g/Tag (hohe TAN-Produktion)

**Testschritte**:
1. Nutzer öffnet Tab "Biofilter-Dimensionierung" oder sieht entsprechende Karte in der Systemübersicht

**Erwartete Ergebnisse**:
- Anzeige: benötigte Oberfläche X m² vs. vorhandene Oberfläche Y m²
- Status: "Unzureichend" wenn vorhandene < benötigte Kapazität
- Warnung: "Biofilter-Kapazität reicht möglicherweise nicht für 200g/Tag Futtermenge aus"
- Empfehlung: Biofilter vergrößern oder Futtermenge reduzieren

**Nachbedingungen**:
- Keine Datenänderung

**Tags**: [req-026, biofilter, dimensionierung, warnung, kapazitaet]

---

## 15. Formularvalidierung (Grenzwerte und Pflichtfelder)

### TC-026-066: AquaponicSystem — pH-Validierung (Ziel Min > Max abgelehnt)

**Requirement**: REQ-026 § 3 AquaponicSystemCreate — ph_target_min: ge=5.0, le=9.0; ph_target_max: ge=5.0, le=9.0
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Aquaponik-System erstellen" ist geöffnet

**Testschritte**:
1. Nutzer gibt pH Ziel Min: 7.5 und pH Ziel Max: 7.0 ein (Min > Max)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "pH-Ziel-Minimum darf nicht größer als Maximum sein"
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Kein System erstellt

**Tags**: [req-026, formvalidierung, ph-ziel, min-max, negativ]

---

### TC-026-067: FishStock — Pflichtfelder leer (Name fehlt)

**Requirement**: REQ-026 § 3 FishStockCreate — name: min_length=1
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Bestand hinzufügen" ist geöffnet

**Testschritte**:
1. Nutzer lässt "Name" leer
2. Nutzer füllt alle anderen Felder aus
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung beim Namensfeld: "Bitte Namen eingeben"
- Dialog bleibt geöffnet, kein Eintrag erstellt

**Nachbedingungen**:
- Kein FishStock erstellt

**Tags**: [req-026, fischbestand, formvalidierung, pflichtfeld, name]

---

### TC-026-068: FishFeedingEvent — Menge muss > 0 sein

**Requirement**: REQ-026 § 3 FishFeedingEventCreate — amount_g: gt=0
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Fütterung dokumentieren" ist geöffnet

**Testschritte**:
1. Nutzer gibt Menge 0 g ein
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Futtermenge muss größer als 0 sein"
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Kein Fütterungseintrag erstellt

**Tags**: [req-026, fütterungsereignis, formvalidierung, menge-null, negativ]

---

## Coverage-Übersicht

| Spezifikationsabschnitt | Beabdeckte Testfälle |
|------------------------|----------------------|
| § 1 Stickstoffkreislauf, Emerson-Formel | TC-026-021, TC-026-022, TC-026-023 |
| § 1 Systemtypen (media_bed, dwc, nft, hybrid, wicking) | TC-026-007, TC-026-008, TC-026-009 |
| § 1 Biofilter-Management / Cycling-Erkennung | TC-026-032, TC-026-033, TC-026-034, TC-026-035, TC-026-036 |
| § 1 Feststoff-Management und Mineralisierung | TC-026-009 |
| § 1 Nährstoffdefizite und Supplementierung | TC-026-042, TC-026-043, TC-026-044, TC-026-045, TC-026-046 |
| § 1 pH-Korrektur-Regeln (Säure-Verbot, Experten-Ausnahme) | TC-026-051, TC-026-052 |
| § 1 Alkalitäts-Management (KH) | TC-026-029 |
| § 1 Fisch-Pflanzen-Kompatibilität / Temperaturzonen | TC-026-005, TC-026-058, TC-026-059 |
| § 1 Saisonale Aspekte (DACH, Outdoor) | TC-026-039, TC-026-062, TC-026-063 |
| § 1 Regulatorische Hinweise (TierSchG, EU-VO 1143/2014) | TC-026-004, TC-026-060, TC-026-061 |
| § 2 FishSpecies Seed-Daten (8 Arten) | TC-026-001, TC-026-002, TC-026-003, TC-026-004 |
| § 2 AquaponicSystem-Modell | TC-026-006, TC-026-007, TC-026-008, TC-026-009, TC-026-010, TC-026-011, TC-026-012, TC-026-013, TC-026-014 |
| § 2 FishStock-Modell / Biomasse | TC-026-015, TC-026-016, TC-026-017, TC-026-018 |
| § 2 WaterTest immutable / Emerson | TC-026-021 – TC-026-031 |
| § 3 NitrogenCycleEngine (NH3, DO, GH, Temp-Stufen) | TC-026-022, TC-026-024, TC-026-029, TC-026-030, TC-026-031, TC-026-056, TC-026-057 |
| § 3 StockingDensityCalculator | TC-026-015, TC-026-016, TC-026-064 |
| § 3 FeedingRateCalculator (Q10, Ramp-up, Cycling-Faktor) | TC-026-037, TC-026-038, TC-026-039 |
| § 3 AquaponicsSafetyValidator | TC-026-047, TC-026-048, TC-026-049, TC-026-050, TC-026-051, TC-026-052 |
| § 3 BiofilterManager (Dimensionierung, Turnover) | TC-026-065 |
| § 3 FishHealthMonitor (Mortalität, Fressverhalten) | TC-026-019, TC-026-020, TC-026-041 |
| § 4.2 Fish Species API (global, Kompatibilität) | TC-026-001, TC-026-002, TC-026-003, TC-026-005 |
| § 4.3 Fish Stocks CRUD + Mortalität | TC-026-015 – TC-026-020 |
| § 4.4 Water Tests (immutable, NH3 berechnet) | TC-026-021 – TC-026-031 |
| § 4.4 Cycling-Progress + Nitrogen-Chart | TC-026-028, TC-026-032 – TC-026-036 |
| § 4.5 Feeding Recommendation + FCR | TC-026-037, TC-026-038, TC-026-040, TC-026-041, TC-026-055 |
| § 4.6 Supplementation + Deficiency Check | TC-026-042 – TC-026-046 |
| § 4.7 Safety Status + Alerts | TC-026-053, TC-026-054 |
| § 4.8 Fish Health | TC-026-019, TC-026-020, TC-026-056, TC-026-057 |
| § 5 Auth / Tenant-Scoping | TC-026-006, TC-026-013 (Admin-Rolle) |
| § 7 DoD-Prüfpunkte (alle) | Verteilt über alle Testfälle |
| § 7 Testszenarien 1–8 | TC-026-015 (S1), TC-026-023 (S2), TC-026-034 (S3), TC-026-047 (S4), TC-026-005 (S5), TC-026-039 (S6), TC-026-042 (S7), TC-026-029 (S8) |
| Formularvalidierung (alle Schemas) | TC-026-008, TC-026-010, TC-026-025, TC-026-026, TC-026-045, TC-026-066, TC-026-067, TC-026-068 |
