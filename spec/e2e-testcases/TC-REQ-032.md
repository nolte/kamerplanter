---
req_id: REQ-032
title: Druckansichten & Export
category: Ausgabe & Dokumentation
test_count: 47
coverage_areas:
  - PrintButton-Komponente (Browser-Druck und PDF-Download)
  - Browser-Druckansicht (CSS @media print)
  - PDF-Export-Download-Flow (alle Template-Typen)
  - Pflanzen-Infokarte / Pflanzenetikett (PlantLabelDialog)
  - QR-Code-Anzeige und Inhalt
  - Sammelausdruck (Mehrfachauswahl, Grid-Layouts)
  - Konfigurationsdialog (Feld-Checkboxen, Layout-Auswahl, Vorschau)
  - Nährstoffplan-Druckansicht (REQ-004)
  - Pflege-Checkliste-Druckansicht (REQ-022)
  - Gießplan / Urlaubsvertretung-Druckansicht
  - Ernteprotokoll-Druckansicht (REQ-007)
  - Standort-Übersicht / Beetplan-Druckansicht (REQ-002)
  - Pflanzen-Steckbrief-Druckansicht (REQ-001)
  - Kalender-Übersicht-Druckansicht (REQ-015)
  - CSV-Export (tabellarische Templates)
  - Fehlerzustände (keine Daten, PDF-Generierungsfehler, Timeout)
  - Berechtigungsprüfung (viewer, grower, admin)
  - i18n (DE / EN Locale-Auswahl)
generated: "2026-04-02"
version: "1.1"
---

# TC-REQ-032: Druckansichten & Export

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-032 Druckansichten & Export v1.1**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Aufrufe, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

URL-Muster (Print-Endpunkte werden vom Browser automatisch als Download ausgelöst, keine direkte Navigation durch den Nutzer):
- Nährstoffplan-Druckansicht: ab Nährstoffplan-Detailseite `/t/{slug}/nutrient-plans/{id}`
- Pflege-Checkliste-Druck: ab Pflege-Dashboard `/t/{slug}/care`
- Ernteprotokoll-Druck: ab Ernte-Detailseite `/t/{slug}/harvests/{id}`
- Standort-Übersicht-Druck: ab Standort-Detailseite `/t/{slug}/locations/{id}`
- Pflanzen-Infokarte: ab Pflanzen-Liste `/t/{slug}/plants` oder Pflanzen-Detailseite `/t/{slug}/plants/{key}`

---

## 1. PrintButton-Komponente — Grundfunktionen

### TC-032-001: PrintButton erscheint in der Toolbar der Nährstoffplan-Detailseite

**Requirement**: REQ-032 §6.1 — PrintButton-Komponente, Platzierung
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt (Tenant-Mitglied, Rolle: grower oder admin)
- Mindestens ein Nährstoffplan ist im System vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines vorhandenen Nährstoffplans
2. Nutzer betrachtet die Toolbar / Aktionsleiste der Seite

**Erwartete Ergebnisse**:
- Ein Drucken-Button (Drucker-Icon oder Button mit Beschriftung "Drucken" / "PDF herunterladen") ist in der Toolbar sichtbar
- Der Button ist aktiviert (nicht deaktiviert)
- Beim Hover zeigt der Button einen Tooltip mit "Nährstoffplan drucken" oder "Als PDF herunterladen"

**Nachbedingungen**:
- Keine Statusänderung; Seite bleibt unverändert

**Screenshot-Checkpoint**: Toolbar mit sichtbarem PrintButton

**Tags**: [req-032, print-button, toolbar, nutrient-plan]

---

### TC-032-002: PrintButton im Icon-Modus erscheint in engen Toolbars

**Requirement**: REQ-032 §6.1 — PrintButton `variant="icon"`
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf einer Seite mit kompakter Toolbar (z.B. Standort-Detailseite)

**Testschritte**:
1. Nutzer öffnet eine Standort-Detailseite
2. Nutzer sucht den Drucken-Button in der Toolbar

**Erwartete Ergebnisse**:
- Der PrintButton erscheint als reines Drucker-Icon ohne Text-Beschriftung
- Beim Hover erscheint ein Tooltip mit der Aktion (z.B. "Standort-Übersicht drucken")
- Das Icon ist optisch klar erkennbar (Drucker-Symbol)

**Nachbedingungen**:
- Keine Statusänderung

**Screenshot-Checkpoint**: Icon-Modus des PrintButton in kompakter Toolbar

**Tags**: [req-032, print-button, icon-mode, toolbar]

---

## 2. Browser-Druckansicht (CSS @media print)

### TC-032-003: Browser-Druckansicht blendet Navigationselemente aus

**Requirement**: REQ-032 §3.1 — Browser-Druckansicht, CSS @media print
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf der Nährstoffplan-Detailseite
- Browser unterstützt `window.print()` (alle modernen Browser)

**Testschritte**:
1. Nutzer klickt auf den PrintButton (Modus: Browser-Druck)
2. Browser öffnet den Druckdialog oder wechselt in die Druckvorschau

**Erwartete Ergebnisse**:
- In der Druckvorschau sind Sidebar, Navigationsleiste und Footer **nicht** sichtbar
- Nur der druckrelevante Inhalt (Nährstoffplan-Tabelle, Phasen, Mischanleitungen) wird angezeigt
- Hintergrundfarben sind für den Druck angepasst (kein dunkler Hintergrund)
- Schrift ist kontraststark (schwarz auf weiß)
- Seitenumbrüche sind an logischen Stellen gesetzt (nicht mitten in einer Phasen-Tabelle)

**Nachbedingungen**:
- Nach Abbruch des Druckdialogs kehrt der Nutzer zur normalen Seitenansicht zurück

**Screenshot-Checkpoint**: Druckvorschau ohne Sidebar und Navigation

**Tags**: [req-032, browser-print, media-print, navigation-hidden]

---

### TC-032-004: Druckansicht zeigt korrekten Seitenumbruch bei mehrseitigem Nährstoffplan

**Requirement**: REQ-032 §3.1 — Seitenumbrüche (`page-break-before`, `page-break-inside: avoid`)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Nährstoffplan mit mindestens 4 Phasen ist vorhanden (genug Inhalt für 2+ Druckseiten)

**Testschritte**:
1. Nutzer öffnet die Detailseite eines mehrstufigen Nährstoffplans (4+ Phasen)
2. Nutzer klickt auf den PrintButton (Browser-Druck)
3. Nutzer betrachtet die Druckvorschau und navigiert zu Seite 2

**Erwartete Ergebnisse**:
- Jede Phase beginnt entweder auf der gleichen Seite vollständig oder startet auf einer neuen Seite
- Keine Phasen-Überschrift erscheint am unteren Seitenrand ohne zugehörigen Inhalt
- Tabellen werden nicht mitten in einer Zeile umgebrochen
- Seitenzahlen oder Kopfzeilen sind sichtbar (falls implementiert)

**Nachbedingungen**:
- Nutzer bricht Druck ab oder druckt das Dokument

**Screenshot-Checkpoint**: Mehrseitige Druckvorschau mit korrekten Seitenumbrüchen

**Tags**: [req-032, browser-print, page-break, multi-page]

---

### TC-032-005: Pflege-Checkliste zeigt druckbare Checkboxen in der Druckvorschau

**Requirement**: REQ-032 §2.2 — Pflege-Checkliste, Checkboxen
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 3 Pflegeerinnerungen für den aktuellen Tag oder die aktuelle Woche sind vorhanden

**Testschritte**:
1. Nutzer navigiert zum Pflege-Dashboard (`/t/{slug}/care`)
2. Nutzer klickt auf den PrintButton "Pflege-Checkliste drucken"
3. Nutzer betrachtet die Druckvorschau

**Erwartete Ergebnisse**:
- Jede Pflegeerinnerung erscheint als Zeile mit: Pflanzenname, Standort, Aktionstyp (z.B. "Gießen", "Düngen"), leere Checkbox (☐)
- Checkboxen sind als leere Quadrate gedruckt (zum manuellen Abhaken)
- Der Zeitraum (Tag/Woche) ist als Überschrift sichtbar
- Pflanzspezifische Hinweise (z.B. "Tauchbad", "Regenwasser") erscheinen als kleine Notiz unter der Pflanzenzeile
- Keine interaktiven UI-Elemente (Buttons, Chips) erscheinen in der Druckansicht

**Nachbedingungen**:
- Druckdialog erscheint oder Nutzer bricht ab

**Screenshot-Checkpoint**: Pflege-Checkliste in Druckvorschau mit Checkboxen

**Tags**: [req-032, care-checklist, browser-print, checkboxes]

---

## 3. PDF-Export — Download-Flow

### TC-032-006: PDF-Download des Nährstoffplans startet automatisch

**Requirement**: REQ-032 §3.2 — PDF-Export, Response mit `Content-Disposition: attachment`
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Rolle: grower oder admin)
- Ein Nährstoffplan mit vollständigen Phasen und Mischanleitungen ist vorhanden

**Testschritte**:
1. Nutzer öffnet die Detailseite eines Nährstoffplans
2. Nutzer klickt auf den Button "PDF herunterladen" (oder wählt "PDF-Download" im PrintButton-Menü)
3. Nutzer wartet auf den Download-Abschluss

**Erwartete Ergebnisse**:
- Browser zeigt einen Lade-Indikator oder Spinner im PrintButton während die PDF generiert wird
- Nach max. 5 Sekunden startet ein Datei-Download automatisch
- Der Dateiname enthält den Plan-Namen und das Datum (z.B. `naehrstoffplan-grundplan-2026-04-02.pdf`)
- Die heruntergeladene Datei hat die Endung `.pdf`
- Eine Erfolgsbenachrichtigung ("PDF wurde heruntergeladen") erscheint kurz als Snackbar, falls implementiert

**Nachbedingungen**:
- Die PDF-Datei liegt im Download-Ordner des Nutzers vor

**Screenshot-Checkpoint**: Download-Indikator während PDF-Generierung; Snackbar nach Abschluss

**Tags**: [req-032, pdf-export, download, nutrient-plan, happy-path]

---

### TC-032-007: PDF-Download des Ernteprotokolls enthält alle Pflichtfelder

**Requirement**: REQ-032 §2.4 — Ernteprotokoll, behördentaugliches Format
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Rolle: grower oder admin)
- Eine abgeschlossene Ernte-Charge (HarvestBatch) mit Qualitätsbewertung und mindestens einer IPM-Behandlung ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite der Ernte-Charge
2. Nutzer klickt auf "Ernteprotokoll als PDF herunterladen"
3. Nutzer öffnet die heruntergeladene PDF-Datei

**Erwartete Ergebnisse**:
- Die PDF enthält: HarvestBatch-ID (oder lesbare Kennung), Erntedatum, Sortenname
- Frisch- und Trockengewicht sind ausgewiesen
- Qualitätsbewertung (Score, visuelle und olfaktorische Bewertung) ist aufgeführt
- Trichom-Stadium erscheint, falls im System erfasst
- Letzte IPM-Behandlungen mit Karenz-Status sind aufgelistet
- Freitext-Notizen sind enthalten
- Das Dokument ist im Format A4 Hochformat erstellt
- Die PDF enthält einen Dokumenttitel (Tagged PDF, nicht leer)

**Nachbedingungen**:
- Protokoll liegt als vollständiges, behördentaugliches Dokument vor

**Screenshot-Checkpoint**: Erste Seite der Ernteprotokoll-PDF geöffnet im Browser-PDF-Viewer

**Tags**: [req-032, pdf-export, harvest-report, mandatory-fields]

---

### TC-032-008: PDF-Download der Standort-Übersicht verwendet Querformat

**Requirement**: REQ-032 §2.5 — Standort-Übersicht, A4 Querformat
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Standort mit mehreren Beeten und belegten Slots ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines Standorts
2. Nutzer klickt auf "Standort-Übersicht herunterladen" (oder "PDF herunterladen")
3. Nutzer öffnet die heruntergeladene PDF-Datei

**Erwartete Ergebnisse**:
- Die PDF-Seite ist im Querformat (Landscape, A4) formatiert
- Die Standort-Hierarchie (Zone → Bereich → Beet/Slot) ist tabellarisch oder als visueller Grundriss dargestellt
- Jeder Slot zeigt: aktuelle Pflanze, Wachstumsphase, Familiengruppe / Vorkultur
- Die Darstellung passt auf eine Seite oder hat logische Seitenumbrüche

**Nachbedingungen**:
- PDF liegt im Querformat vor

**Screenshot-Checkpoint**: PDF-Viewer zeigt Querformat-Seite mit Standort-Übersicht

**Tags**: [req-032, pdf-export, location-overview, landscape, a4]

---

### TC-032-009: PDF-Download-Ladeindikator verhindert Doppelklick

**Requirement**: REQ-032 §6.1 — PrintButton, Lade-Zustand
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Nährstoffplan-Detailseite ist geöffnet
- Netzwerkverbindung ist vorhanden (PDF-Generierung dauert messbar)

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen"
2. Nutzer versucht sofort ein zweites Mal auf den Button zu klicken (bevor der Download startet)

**Erwartete Ergebnisse**:
- Nach dem ersten Klick wechselt der Button in einen Lade-Zustand (Spinner sichtbar, Button deaktiviert)
- Der zweite Klick löst keine weitere Anfrage aus
- Button bleibt deaktiviert bis der Download gestartet hat oder ein Fehler auftritt

**Nachbedingungen**:
- Nur ein PDF wird heruntergeladen

**Screenshot-Checkpoint**: PrintButton im Lade-Zustand (Spinner, deaktiviert)

**Tags**: [req-032, pdf-export, loading-state, double-click-prevention]

---

### TC-032-010: Locale-Auswahl DE/EN beim PDF-Download

**Requirement**: REQ-032 §3.2 — Query-Parameter `locale`, §8 — i18n
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Pflanzen-Steckbrief für eine vorhandene Art ist verfügbar
- Das Template ist in DE und EN implementiert

**Testschritte**:
1. Nutzer navigiert zur Artenseite (Pflanzen-Steckbrief)
2. Nutzer öffnet das PDF-Download-Menü oder eine Druckoptionen-Auswahl
3. Nutzer wählt die Sprache "Englisch" aus
4. Nutzer klickt auf "PDF herunterladen"
5. Nutzer öffnet die heruntergeladene PDF-Datei

**Erwartete Ergebnisse**:
- Die heruntergeladene PDF enthält englische Beschriftungen ("Light requirement", "Temperature", "Growth phase" anstelle der deutschen Begriffe)
- Zahlenwerte und Daten bleiben inhaltlich identisch
- Der Dateiname enthält ggf. ein Sprachkürzel (`...-en.pdf`)

**Nachbedingungen**:
- PDF in englischer Sprache liegt vor

**Screenshot-Checkpoint**: Erste Seite der englischen PDF mit englischen Feldbezeichnungen

**Tags**: [req-032, pdf-export, i18n, locale-en, plant-factsheet]

---

## 4. Pflanzen-Infokarte und QR-Code (PlantLabelDialog)

### TC-032-011: PlantLabelDialog öffnet sich von der Pflanzen-Detailseite

**Requirement**: REQ-032 §6.2 — PlantLabelDialog, Aufrufstellen
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt (Tenant-Mitglied)
- Mindestens eine PlantInstance ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer PlantInstance (`/t/{slug}/plants/{key}`)
2. Nutzer klickt auf den PrintButton oder "Etiketten drucken" in der Toolbar

**Erwartete Ergebnisse**:
- Ein Dialog mit dem Titel "Pflanzen-Infokarte drucken" (oder ähnlich) öffnet sich
- Der Dialog zeigt die vorausgewählte Pflanze in der Pflanzenauswahl-Liste
- Feld-Checkboxen sind sichtbar mit den Default-Einstellungen:
  - ☑ Pflanzenname (an)
  - ☑ Wissenschaftlicher Name (an)
  - ☐ Gattung / Familie (aus)
  - ☑ Pflanzdatum (an)
  - ☐ Aktuelle Phase (aus)
  - ☐ Standort (aus)
  - ☐ Sorte (aus)
  - ☐ Kurzhinweis (aus)
  - ☑ QR-Code (an, Checkbox ist deaktiviert / nicht abwählbar)
- Layout-Radio-Buttons sind sichtbar (Einzelkarte A6 / 8 pro Seite / 9 pro Seite)
- Eine schematische Kartenvorschau ist sichtbar
- Button "PDF herunterladen" ist sichtbar und aktiviert

**Nachbedingungen**:
- Dialog ist geöffnet; keine Datei wurde noch heruntergeladen

**Screenshot-Checkpoint**: PlantLabelDialog mit Default-Einstellungen

**Tags**: [req-032, plant-label, dialog, default-fields, qr-code]

---

### TC-032-012: QR-Code-Checkbox ist nicht abwählbar

**Requirement**: REQ-032 §2.7 — QR-Code immer enthalten
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- PlantLabelDialog ist geöffnet (Vorbedingungen wie TC-032-011)

**Testschritte**:
1. Nutzer versucht, die Checkbox "QR-Code" zu deaktivieren (Klick auf die Checkbox)

**Erwartete Ergebnisse**:
- Die QR-Code-Checkbox bleibt aktiviert (Häkchen bleibt gesetzt)
- Die Checkbox ist als deaktiviert/gesperrt dargestellt (z.B. ausgegraut, nicht anklickbar)
- Alternativ: Ein Tooltip erklärt "QR-Code ist immer enthalten"
- Der Zustand der anderen Checkboxen bleibt unverändert

**Nachbedingungen**:
- QR-Code ist weiterhin für den Druck ausgewählt

**Screenshot-Checkpoint**: Deaktivierte QR-Code-Checkbox mit Tooltip

**Tags**: [req-032, plant-label, qr-code, mandatory-field, checkbox-locked]

---

### TC-032-013: Vorschau aktualisiert sich bei Änderung der Feld-Auswahl

**Requirement**: REQ-032 §6.2 — PlantLabelDialog, Vorschau
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- PlantLabelDialog ist geöffnet
- Nur Pflanzename, Wissenschaftlicher Name, Pflanzdatum und QR-Code sind aktiv (Default)

**Testschritte**:
1. Nutzer aktiviert die Checkbox "Aktuelle Phase"
2. Nutzer betrachtet die schematische Kartenvorschau

**Erwartete Ergebnisse**:
- Die Vorschau-Karte zeigt nun ein zusätzliches Feld für "Aktuelle Phase" (Platzhaltertext oder tatsächlicher Phasenwert)
- Die Vorschau-Karte erscheint dichter/kleiner, da mehr Felder angezeigt werden
- Der QR-Code ist weiterhin in der Vorschau sichtbar

**Testschritte (Fortsetzung)**:
3. Nutzer deaktiviert wieder die Checkbox "Aktuelle Phase"

**Erwartete Ergebnisse (Fortsetzung)**:
- Die Vorschau-Karte zeigt das Feld nicht mehr
- Die Karte hat wieder die ursprüngliche Größe / Raumaufteilung

**Nachbedingungen**:
- Vorschau spiegelt immer die aktuelle Feldauswahl wider

**Screenshot-Checkpoint**: Vor/Nach-Vergleich der Vorschau mit und ohne "Aktuelle Phase"

**Tags**: [req-032, plant-label, preview, dynamic-update, field-selection]

---

### TC-032-014: Layout-Wechsel von Einzelkarte zu Grid-Ansicht in der Vorschau

**Requirement**: REQ-032 §2.7 — Format-Optionen (Einzelkarte / Grid 2×4 / Grid 3×3)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- PlantLabelDialog ist geöffnet
- Standard-Layout "8 pro Seite (2×4)" ist ausgewählt

**Testschritte**:
1. Nutzer wählt den Radio-Button "Einzelkarte (A6)"
2. Nutzer betrachtet die Vorschau

**Erwartete Ergebnisse**:
- Vorschau zeigt eine einzelne, größere Karte (A6-Format-Proportionen)
- Die Karte hat mehr Platz für alle konfigurierten Felder
- QR-Code ist größer als in der Grid-Ansicht

**Testschritte (Fortsetzung)**:
3. Nutzer wählt den Radio-Button "9 pro Seite (3×3)"
4. Nutzer betrachtet die Vorschau

**Erwartete Ergebnisse (Fortsetzung)**:
- Vorschau zeigt eine kleinere Karte (3×3-Raster-Proportionen)
- Der QR-Code ist kleiner, aber noch erkennbar

**Nachbedingungen**:
- Layout-Auswahl ist korrekt gesetzt für den nachfolgenden Download

**Screenshot-Checkpoint**: Vorschau in Einzelkarten-Modus vs. 3×3-Grid-Modus

**Tags**: [req-032, plant-label, layout, single-card, grid-layout, preview]

---

### TC-032-015: PDF-Download der Pflanzen-Infokarte enthält lesbaren QR-Code

**Requirement**: REQ-032 §2.7 — QR-Code-Größe min. 20×20mm, Deep-Link-Inhalt
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- PlantLabelDialog ist geöffnet mit einer ausgewählten PlantInstance
- Standard-Layout (2×4 Grid) ist ausgewählt
- Standard-Felder (Name, Wissenschaftlicher Name, Pflanzdatum, QR-Code) sind ausgewählt

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen" im PlantLabelDialog
2. Nutzer öffnet die heruntergeladene PDF-Datei
3. Nutzer scannt den QR-Code auf der Infokarte mit einem Smartphone

**Erwartete Ergebnisse**:
- Die PDF enthält 8 Infokarten im 2×4-Raster auf einer A4-Seite
- Jede Karte zeigt: Pflanzenname, Wissenschaftlichen Namen (kursiv), Pflanzdatum, QR-Code
- Der QR-Code ist mindestens 20×20mm groß
- Das Scannen des QR-Codes öffnet im Browser die URL `{app_base_url}/t/{slug}/plants/{plant_key}`
- Schnittmarken sind zwischen den Karten sichtbar (zum Ausschneiden)

**Nachbedingungen**:
- QR-Code-Link ist funktional und führt zur richtigen PlantInstance-Seite

**Screenshot-Checkpoint**: PDF geöffnet mit 8 Infokarten im 2×4-Raster; QR-Code-Scan-Ergebnis

**Tags**: [req-032, plant-label, qr-code, deep-link, grid-2x4, pdf-download]

---

### TC-032-016: Kurzhinweis-Freitext wird auf der Infokarte gedruckt

**Requirement**: REQ-032 §2.7 — Kurzhinweis (Konfigurierbar), Freitext-Eingabe
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- PlantLabelDialog ist geöffnet mit einer ausgewählten PlantInstance

**Testschritte**:
1. Nutzer aktiviert die Checkbox "Kurzhinweis"
2. Ein Freitext-Eingabefeld erscheint (pro Pflanze oder als globaler Hinweis)
3. Nutzer gibt ein: "Kalkfrei gießen — nur Regenwasser"
4. Nutzer klickt auf "PDF herunterladen"
5. Nutzer öffnet die PDF

**Erwartete Ergebnisse**:
- Die Infokarte in der PDF zeigt den Hinweis "Kalkfrei gießen — nur Regenwasser" als Freitext-Feld
- Der Hinweis ist optisch vom Rest der Karte abgegrenzt (z.B. in einem Hinweis-Kasten oder kursiv)

**Nachbedingungen**:
- PDF enthält personalisierten Kurzhinweis

**Screenshot-Checkpoint**: Infokarte mit Kurzhinweis-Feld in der PDF

**Tags**: [req-032, plant-label, custom-note, free-text, pdf]

---

## 5. Sammelausdruck — Mehrfachauswahl

### TC-032-017: Mehrere Pflanzen über Checkboxen in der Listenansicht auswählen

**Requirement**: REQ-032 §6.2 — Aufrufstellen: PlantInstance-Listenansicht mit Mehrfachauswahl
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 5 PlantInstances sind in der Pflanzen-Listenansicht sichtbar

**Testschritte**:
1. Nutzer navigiert zur Pflanzen-Listenansicht (`/t/{slug}/plants`)
2. Nutzer aktiviert die Auswahl-Checkboxen (z.B. durch Klick auf eine Zeilen-Checkbox)
3. Nutzer wählt 3 Pflanzen aus (Checkboxen in Zeilen 1, 3 und 5)
4. Nutzer sucht in der Toolbar nach dem Button "Etiketten drucken"

**Erwartete Ergebnisse**:
- Jede Tabellenzeile hat eine Auswahlcheckbox (links in der Zeile)
- Nach Auswahl von 3 Zeilen erscheint in der Toolbar ein Button "Etiketten drucken (3)" oder "Infokarten drucken"
- Der Button zeigt die Anzahl der ausgewählten Pflanzen
- Ein "Alle auswählen"-Checkbox im Tabellenkopf ist sichtbar

**Nachbedingungen**:
- 3 Pflanzen sind ausgewählt; "Etiketten drucken"-Button ist aktiviert

**Screenshot-Checkpoint**: Pflanzen-Liste mit 3 ausgewählten Zeilen und aktiviertem "Etiketten drucken"-Button

**Tags**: [req-032, plant-label, batch-select, list-view, multi-select]

---

### TC-032-018: PlantLabelDialog öffnet sich mit allen ausgewählten Pflanzen vorausgefüllt

**Requirement**: REQ-032 §6.2 — PlantLabelDialog mit `plantKeys` aus Listenauswahl
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer hat in der Pflanzen-Listenansicht 3 Pflanzen ausgewählt (Vorbedingungen wie TC-032-017)
- "Etiketten drucken (3)"-Button ist in der Toolbar aktiv

**Testschritte**:
1. Nutzer klickt auf "Etiketten drucken (3)" in der Toolbar

**Erwartete Ergebnisse**:
- PlantLabelDialog öffnet sich
- In der Pflanzenauswahl-Liste sind alle 3 ausgewählten Pflanzen aufgeführt mit ihren Namen
- Jede Pflanze kann einzeln aus dem Dialog entfernt werden (Löschen-Icon pro Pflanze)
- Es gibt eine Möglichkeit, weitere Pflanzen zum Dialog hinzuzufügen
- Die Feld-Checkboxen und Layout-Auswahl sind wie bei einer Einzelkarte verfügbar

**Nachbedingungen**:
- Dialog zeigt 3 Pflanzen; Einstellungen gelten für alle Karten gleichzeitig

**Screenshot-Checkpoint**: PlantLabelDialog mit 3 vorausgefüllten Pflanzen in der Auswahlliste

**Tags**: [req-032, plant-label, dialog, batch-print, prefilled]

---

### TC-032-019: Sammelausdruck mit Grid 2×4 passt 8 Karten auf eine A4-Seite

**Requirement**: REQ-032 §2.7 — Sammelausdruck, Raster-Layout, Schnittmarken
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- PlantLabelDialog ist mit 8 ausgewählten Pflanzen geöffnet
- Layout "8 pro Seite (2×4)" ist ausgewählt

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen"
2. Nutzer öffnet die heruntergeladene PDF

**Erwartete Ergebnisse**:
- Die PDF-Seite enthält exakt 8 Infokarten im 2×4-Raster auf einer A4-Seite (Hochformat)
- Jede Karte ist optisch durch Schnittmarken oder gepunktete Linien vom Nachbarn getrennt
- Alle 8 Karten haben identisches Layout und identische Felder (entsprechend der Dialog-Einstellungen)
- Jede Karte hat einen eindeutigen QR-Code für die jeweilige Pflanze

**Nachbedingungen**:
- PDF mit Sammelausdruck liegt vor

**Screenshot-Checkpoint**: PDF-Seite mit 8 Infokarten im 2×4-Raster

**Tags**: [req-032, plant-label, batch-print, grid-2x4, cut-marks]

---

### TC-032-020: Sammelausdruck mit mehr als 8 Pflanzen erzeugt mehrere Seiten

**Requirement**: REQ-032 §2.7 — Sammelausdruck mit Mehrseiten
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- PlantLabelDialog ist mit 12 ausgewählten Pflanzen geöffnet
- Layout "8 pro Seite (2×4)" ist ausgewählt

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen"
2. Nutzer öffnet die heruntergeladene PDF und navigiert zu Seite 2

**Erwartete Ergebnisse**:
- Seite 1 enthält die ersten 8 Infokarten im 2×4-Raster
- Seite 2 enthält die verbleibenden 4 Infokarten (mit Leerfeldern für die restlichen 4 Positionen oder ohne Leerfelder)
- Die PDF hat insgesamt 2 Seiten
- Alle 12 QR-Codes sind eindeutig und korrekt

**Nachbedingungen**:
- Alle 12 Infokarten sind in der PDF enthalten

**Screenshot-Checkpoint**: Seite 2 der PDF mit verbleibenden 4 Infokarten

**Tags**: [req-032, plant-label, batch-print, multi-page, pagination]

---

### TC-032-021: Alle Pflanzen eines Standorts via Standort-Detailseite drucken

**Requirement**: REQ-032 §6.2 — Aufrufstellen: Standort-Detailseite (alle Pflanzen eines Standorts)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Standort mit 6 belegten Slots / PlantInstances ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Standorts
2. Nutzer klickt auf den Button "Etiketten für alle Pflanzen drucken" (oder ähnliche Aktion in der Toolbar)

**Erwartete Ergebnisse**:
- PlantLabelDialog öffnet sich
- Alle 6 Pflanzen des Standorts sind in der Pflanzenauswahl-Liste vorausgefüllt
- Layout-Standard ist "8 pro Seite (2×4)"
- Der Nutzer kann einzelne Pflanzen aus der Auswahl entfernen

**Nachbedingungen**:
- Dialog ist geöffnet mit allen Standort-Pflanzen vorausgefüllt

**Screenshot-Checkpoint**: PlantLabelDialog mit 6 Standort-Pflanzen vorausgefüllt

**Tags**: [req-032, plant-label, location-based, batch-print, prefilled]

---

## 6. CSV-Export

### TC-032-022: CSV-Export des Nährstoffplans wird heruntergeladen

**Requirement**: REQ-032 §3.3 — CSV-Export, `format=csv`, UTF-8 mit BOM
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Rolle: grower oder admin)
- Ein Nährstoffplan mit mindestens 2 Phasen und zugeordneten Düngemitteln ist vorhanden

**Testschritte**:
1. Nutzer öffnet die Detailseite eines Nährstoffplans
2. Nutzer öffnet das Export-Menü (Dropdown am PrintButton oder separater "Export"-Button)
3. Nutzer wählt die Option "CSV herunterladen"
4. Nutzer wartet auf den Download
5. Nutzer öffnet die CSV-Datei in einem Tabellenkalkulationsprogramm (z.B. Excel oder LibreOffice Calc)

**Erwartete Ergebnisse**:
- Browser startet den Download einer `.csv`-Datei
- Der Dateiname enthält den Plan-Namen und das Datum (z.B. `naehrstoffplan-grundplan-2026-04-02.csv`)
- Die CSV-Datei öffnet sich in Excel/LibreOffice ohne Zeichensatz-Fehler (Umlaute korrekt dargestellt)
- Die CSV-Datei hat Spaltenüberschriften (z.B. "Phase", "EC-Ziel", "NPK-Verhältnis", "Produkt", "Menge/L", "Mischreihenfolge")
- Alle Phasen-Daten sind als Zeilen enthalten

**Nachbedingungen**:
- CSV-Datei mit vollständigen Nährstoffplan-Daten liegt vor

**Screenshot-Checkpoint**: CSV-Datei in Excel geöffnet mit korrekten Umlauten und Spalten

**Tags**: [req-032, csv-export, nutrient-plan, utf8-bom, excel-compatible]

---

### TC-032-023: CSV-Export des Ernteprotokolls ist tabellarisch strukturiert

**Requirement**: REQ-032 §3.3 — CSV-Export nur bei tabellarischen Templates
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 3 Ernte-Chargen mit Qualitätsbewertungen sind vorhanden

**Testschritte**:
1. Nutzer navigiert zur Ernte-Übersichtsseite oder einer spezifischen Ernte-Charge
2. Nutzer öffnet das Export-Menü
3. Nutzer wählt "CSV herunterladen"
4. Nutzer öffnet die heruntergeladene CSV

**Erwartete Ergebnisse**:
- CSV enthält Spalten: Batch-ID, Datum, Sorte, Frischgewicht (g), Trockengewicht (g), Qualitäts-Score, Notizen
- Jede Ernte-Charge erscheint als eigene Zeile
- Dezimalzahlen verwenden das korrekte Locale-Format (z.B. Komma für DE)
- Datum im ISO-Format oder dem deutschen Datumsformat (DD.MM.YYYY)

**Nachbedingungen**:
- CSV mit allen Ernte-Daten liegt strukturiert vor

**Screenshot-Checkpoint**: CSV-Datei mit Ernte-Chargen-Daten in Tabellenform

**Tags**: [req-032, csv-export, harvest-report, structured-data]

---

### TC-032-024: CSV-Export ist nicht verfügbar für nicht-tabellarische Templates

**Requirement**: REQ-032 §3.3 — CSV nur bei tabellarischen Templates
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf einer Seite mit einem nicht-tabellarischen Template (z.B. Pflanzen-Steckbrief oder Gießplan)

**Testschritte**:
1. Nutzer öffnet die Export-Optionen für den Pflanzen-Steckbrief
2. Nutzer sucht nach der Option "CSV herunterladen"

**Erwartete Ergebnisse**:
- Die Option "CSV herunterladen" ist im Menü **nicht vorhanden** oder ist ausgegraut/deaktiviert
- Nur "PDF herunterladen" und "Browser-Druck" sind als Optionen verfügbar
- Falls ausgegraut: Ein Tooltip erklärt "CSV-Export nur für tabellarische Inhalte verfügbar"

**Nachbedingungen**:
- Kein CSV-Download wurde ausgelöst

**Screenshot-Checkpoint**: Export-Menü ohne CSV-Option für nicht-tabellarisches Template

**Tags**: [req-032, csv-export, unavailable, plant-factsheet, validation]

---

## 7. Weitere Template-Typen

### TC-032-025: Gießplan / Urlaubsvertretung enthält Pflanzenfotos (falls vorhanden)

**Requirement**: REQ-032 §2.3 — Gießplan, Karten-Layout mit optionalem Foto
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 2 PlantInstances haben ein hochgeladenes Foto
- Mindestens 1 PlantInstance hat kein Foto

**Testschritte**:
1. Nutzer navigiert zum Gießplan oder zur Urlaubsvertretungs-Ansicht
2. Nutzer klickt auf "Gießplan drucken" (Browser-Druck oder PDF)
3. Nutzer betrachtet die Druckvorschau oder öffnet die PDF

**Erwartete Ergebnisse**:
- Pflanzen mit Foto zeigen das Bild als Thumbnail auf ihrer Pflanzen-Karte
- Die Pflanze ohne Foto zeigt einen Platzhalter (Icon oder grauer Bereich) anstelle des Fotos
- Jede Karte zeigt: Pflanzenname, Standort, Gießintervall, Wassermenge, Besonderheiten, Dünger-Info (ja/nein/welcher)
- Das Layout ist klar und auch für Personen ohne App-Kenntnisse verständlich

**Nachbedingungen**:
- Druckbares Dokument für Urlaubsvertretung liegt vor

**Screenshot-Checkpoint**: Gießplan mit Foto-Karte und Platzhalter-Karte nebeneinander

**Tags**: [req-032, watering-plan, vacation-handover, photos, cards-layout]

---

### TC-032-026: Pflanzen-Steckbrief enthält alle Stammdaten-Felder

**Requirement**: REQ-032 §2.6 — Pflanzen-Steckbrief, Einzelseite pro Pflanze
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Eine Pflanzenart mit vollständig ausgefüllten Stammdaten ist vorhanden (inklusive Foto, NPK-Bedarf, Mischkulturpartner)

**Testschritte**:
1. Nutzer navigiert zur Artenseite einer Pflanzenart
2. Nutzer klickt auf "Steckbrief drucken" oder "PDF herunterladen"
3. Nutzer öffnet die heruntergeladene PDF oder die Druckvorschau

**Erwartete Ergebnisse**:
- Die Seite enthält: Art-Name, Sorte (falls zutreffend), Pflanzenfamilie
- Foto ist oben rechts oder als Thumbnail eingebettet (falls vorhanden)
- Pflegeanforderungen sind aufgelistet: Lichtverhältnis, Temperatur-Bereich, Luftfeuchtigkeit
- Phasen-Zeitplan ist als Zeitleiste oder Tabelle dargestellt (Aussaat → Ernte mit Monatsangaben)
- NPK-Bedarf pro Phase ist in einer kompakten Tabelle aufgeführt
- Mischkultur-Empfehlungen: gute Nachbarn (grün markiert) und schlechte Nachbarn (rot markiert)
- Das Dokument passt auf eine A4-Seite (Hochformat)

**Nachbedingungen**:
- Steckbrief-PDF liegt als vollständige Einzelseite vor

**Screenshot-Checkpoint**: Pflanzen-Steckbrief-PDF mit allen Feldern auf einer A4-Seite

**Tags**: [req-032, plant-factsheet, pdf-export, stammdaten, a4]

---

### TC-032-027: Kalender-Übersicht wird als Querformat-PDF exportiert

**Requirement**: REQ-032 §2.8 — Kalender-Übersicht, A4 Querformat
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Die Kalenderansicht für den aktuellen Monat enthält mindestens 5 Termine (Tasks, Phasenwechsel)

**Testschritte**:
1. Nutzer navigiert zur Kalenderansicht (`/t/{slug}/calendar`)
2. Nutzer klickt auf "Kalenderansicht drucken" oder "PDF herunterladen"
3. Nutzer öffnet die heruntergeladene PDF

**Erwartete Ergebnisse**:
- Die PDF-Seite ist im Querformat (Landscape A4)
- Ein Kalender-Raster für den aktuellen Monat ist dargestellt (7 Spalten für Wochentage)
- Termine sind farblich nach Kategorie codiert (z.B. Tasks, Phasenwechsel, Erntetermine)
- Eine Legende zeigt die Farbcodierung
- Das Raster passt vollständig auf eine Seite

**Nachbedingungen**:
- Kalender-PDF im Querformat liegt vor

**Screenshot-Checkpoint**: Kalender-PDF im Querformat mit farbcodierten Terminen

**Tags**: [req-032, calendar-view, pdf-export, landscape, color-coding]

---

## 8. Fehlerzustände

### TC-032-028: Fehlermeldung bei leerem Template (keine Daten vorhanden)

**Requirement**: REQ-032 §2 — Druckbare Inhalte; implizit: Leer-Zustand
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Die Pflege-Checkliste für die aktuelle Woche ist leer (keine fälligen Pflegeerinnerungen)

**Testschritte**:
1. Nutzer navigiert zum Pflege-Dashboard
2. Nutzer klickt auf "Pflege-Checkliste drucken"

**Erwartete Ergebnisse**:
- Entweder:
  - Eine Benachrichtigung erscheint: "Keine fälligen Pflegeaufgaben für diesen Zeitraum. Ausdruck nicht möglich." — und kein Download/Druckdialog wird ausgelöst
  - Oder: Der Druck erfolgt, aber das Dokument enthält einen leeren Zustand mit dem Hinweis "Keine Aufgaben für diese Woche"
- In keinem Fall wird ein leeres/defektes PDF heruntergeladen (0-Byte-Datei oder PDF ohne Inhalt)

**Nachbedingungen**:
- Kein fehlerhaftes PDF liegt im Download-Ordner vor

**Screenshot-Checkpoint**: Benachrichtigung "Keine Daten für den Ausdruck" oder leeres-Zustand-Meldung

**Tags**: [req-032, error-state, empty-data, care-checklist, no-tasks]

---

### TC-032-029: Fehlermeldung bei Netzwerkfehler während PDF-Generierung

**Requirement**: REQ-032 §3.2 — PDF-Export; implizit: Fehlerbehandlung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Nährstoffplan-Detailseite ist geöffnet
- Netzwerkverbindung wird während der PDF-Generierung unterbrochen (simuliert)

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen"
2. Während der Lade-Indikator angezeigt wird, wird die Netzwerkverbindung unterbrochen
3. Nutzer wartet auf das Ergebnis

**Erwartete Ergebnisse**:
- Der Lade-Indikator im PrintButton erlischt nach Timeout
- Eine Fehlerbenachrichtigung erscheint als Snackbar: "PDF-Generierung fehlgeschlagen. Bitte versuchen Sie es erneut." oder ähnlicher Text
- Der PrintButton ist wieder aktiviert (nicht mehr im Lade-Zustand)
- Kein leeres oder beschädigtes PDF wurde heruntergeladen
- Ein "Erneut versuchen"-Hinweis oder Button ist sichtbar

**Nachbedingungen**:
- Kein fehlerhaftes PDF im Download-Ordner; Seite ist wieder bedienbar

**Screenshot-Checkpoint**: Fehler-Snackbar nach fehlgeschlagenem PDF-Download

**Tags**: [req-032, error-state, network-error, pdf-generation-failed, snackbar]

---

### TC-032-030: Fehlermeldung bei Timeout der PDF-Generierung (> 5 Sekunden)

**Requirement**: REQ-032 §8 — PDF-Generierung < 5 Sekunden NFR
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Server-seitige PDF-Generierung ist stark verzögert (Testszenario mit simulierter Verzögerung)

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen" für ein komplexes Template (z.B. Standort-Übersicht mit vielen Slots)
2. Nutzer wartet mehr als 5 Sekunden ohne Download-Start
3. Nutzer beobachtet das UI-Verhalten nach Ablauf des Timeouts

**Erwartete Ergebnisse**:
- Nach Ablauf des Timeouts erscheint eine Fehlermeldung: "PDF-Generierung hat zu lange gedauert. Bitte versuchen Sie es erneut." oder ähnlich
- Der PrintButton verlässt den Lade-Zustand und ist wieder klickbar
- Kein Browser-Freeze oder unendlicher Lade-Zustand
- Die Seiten-Navigation ist weiterhin möglich

**Nachbedingungen**:
- Seite ist nach Timeout-Fehler wieder vollständig bedienbar

**Screenshot-Checkpoint**: Timeout-Fehlermeldung nach 5+ Sekunden

**Tags**: [req-032, error-state, timeout, pdf-generation, performance]

---

### TC-032-031: PlantLabelDialog — Validierung bei leerer Pflanzenauswahl

**Requirement**: REQ-032 §5 — Query-Parameter `plant_keys` Pflicht, min. 1
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- PlantLabelDialog ist geöffnet mit einer vorausgewählten Pflanze

**Testschritte**:
1. Nutzer entfernt die einzige Pflanze aus der Pflanzenauswahl-Liste im Dialog (Klick auf Löschen-Icon)
2. Nutzer klickt auf "PDF herunterladen"

**Erwartete Ergebnisse**:
- Der Button "PDF herunterladen" ist deaktiviert, sobald die Pflanzenauswahl leer ist
- Alternativ: Eine Fehlermeldung erscheint: "Bitte wählen Sie mindestens eine Pflanze aus"
- Kein Download wird ausgelöst
- Die Feld-Checkboxen und Layout-Auswahl bleiben zugänglich

**Nachbedingungen**:
- Dialog ist weiterhin geöffnet; keine Datei wurde heruntergeladen

**Screenshot-Checkpoint**: Deaktivierter Download-Button bei leerer Pflanzenauswahl

**Tags**: [req-032, plant-label, validation, empty-selection, download-disabled]

---

### TC-032-032: Serverfehler bei PDF-Generierung zeigt verständliche Fehlermeldung

**Requirement**: REQ-032 §3.2 — PDF-Export; Fehlerbehandlung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Backend gibt einen Server-Fehler zurück bei der PDF-Generierung (Testszenario)

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen" (bei simuliertem Backend-Fehler)
2. Nutzer beobachtet die UI-Reaktion

**Erwartete Ergebnisse**:
- Eine Fehler-Snackbar erscheint mit einer verständlichen Meldung (z.B. "PDF konnte nicht erstellt werden. Bitte versuchen Sie es später erneut.")
- Der PrintButton verlässt den Lade-Zustand
- Keine technischen Details (Stack-Trace, Datenbankfehler, Python-Fehlermeldungen) sind für den Nutzer sichtbar
- Die restliche Seite bleibt bedienbar

**Nachbedingungen**:
- Kein Datei-Download; Seite ist wieder vollständig nutzbar

**Screenshot-Checkpoint**: Fehler-Snackbar ohne technische Interna

**Tags**: [req-032, error-state, server-error, no-technical-details, snackbar]

---

## 9. Berechtigungen und Zugriffsschutz

### TC-032-033: Viewer-Rolle kann alle lesbaren Templates drucken

**Requirement**: REQ-032 §7 — Berechtigungen: viewer kann alle Templates drucken, die er lesen darf
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "viewer" im Tenant
- Ein Nährstoffplan und ein Ernteprotokoll sind im System vorhanden und für den Tenant sichtbar

**Testschritte**:
1. Nutzer (viewer) navigiert zur Detailseite eines Nährstoffplans
2. Nutzer betrachtet die Toolbar
3. Nutzer klickt auf "PDF herunterladen"

**Erwartete Ergebnisse**:
- Der PrintButton ist für den viewer sichtbar und aktiviert
- Der PDF-Download startet erfolgreich
- Keine "Nicht autorisiert"- oder "Zugriff verweigert"-Meldung erscheint

**Nachbedingungen**:
- PDF liegt vor; viewer-Berechtigungen wurden korrekt angewendet

**Screenshot-Checkpoint**: Erfolgreicher PDF-Download mit viewer-Konto

**Tags**: [req-032, permissions, viewer-role, pdf-download, authorized]

---

### TC-032-034: Nicht eingeloggter Nutzer wird bei PDF-Abruf zum Login weitergeleitet

**Requirement**: REQ-032 §7 — PDF-Endpunkte erfordern gültiges JWT-Token
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist nicht eingeloggt (Session ist abgelaufen oder Nutzer ist ausgeloggt)

**Testschritte**:
1. Nutzer versucht, eine druckbare Ansicht aufzurufen (z.B. durch direkten URL-Aufruf eines Print-Endpunkts oder durch Klick auf einen zuvor gespeicherten Link)
2. Nutzer beobachtet die UI-Reaktion

**Erwartete Ergebnisse**:
- Browser leitet den Nutzer zur Login-Seite weiter
- Alternativ: Eine "Nicht autorisiert"-Meldung wird angezeigt
- Kein PDF oder HTML wird ohne gültige Session ausgeliefert
- Nach erfolgreichem Login kann der Nutzer erneut versuchen, den Druck/Export auszulösen

**Nachbedingungen**:
- Kein ungeschützter Zugriff auf Druckdaten

**Screenshot-Checkpoint**: Redirect zur Login-Seite bei unauthentifiziertem Zugriff

**Tags**: [req-032, permissions, unauthenticated, redirect-login, jwt]

---

### TC-032-035: Nutzer kann keine Druckdaten eines anderen Tenants abrufen

**Requirement**: REQ-032 §7 — Berechtigungen unterliegen REQ-024 RBAC
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied in Tenant A, aber nicht in Tenant B)
- Tenant B hat einen Nährstoffplan

**Testschritte**:
1. Nutzer versucht, den Print-Endpunkt eines fremden Tenants aufzurufen (z.B. durch Manipulation der URL: `/t/tenant-b-slug/print/nutrient-plan/{plan_id}`)
2. Nutzer beobachtet die Reaktion

**Erwartete Ergebnisse**:
- Eine "Nicht gefunden"- oder "Zugriff verweigert"-Meldung erscheint (Fehlerseite oder Snackbar)
- Keine PDF-Daten aus Tenant B werden ausgeliefert
- Keine internen Tenant-Informationen sind in der Fehlermeldung sichtbar

**Nachbedingungen**:
- Datenisolation zwischen Tenants ist gewährleistet

**Screenshot-Checkpoint**: Fehlerseite oder Redirect bei Tenant-Isolation-Verstoß

**Tags**: [req-032, permissions, tenant-isolation, rbac, unauthorized]

---

## 10. Weitere Drucktypen und Randfälle

### TC-032-036: Pflanzen-Steckbrief QR-Code verlinkt auf Species-Seite (ohne konkrete Pflanze)

**Requirement**: REQ-032 §2.7 — QR-Code-Inhalt: alternativ zur Species bei Steckbrief ohne konkrete Pflanze
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer druckt einen Pflanzen-Steckbrief für eine Pflanzenart (ohne spezifische PlantInstance)

**Testschritte**:
1. Nutzer navigiert zur Artenseite einer Pflanzenart (z.B. "Tomate - Lycopersicon esculentum")
2. Nutzer klickt auf "Steckbrief drucken"
3. Nutzer öffnet die PDF und scannt den QR-Code

**Erwartete Ergebnisse**:
- Die PDF enthält einen QR-Code
- Das Scannen des QR-Codes öffnet die URL `{app_base_url}/species/{species_key}` (Arten-Seite, nicht Pflanzen-Instanz-Seite)
- Die verlinkte Seite zeigt die Arteninformationen für "Tomate"

**Nachbedingungen**:
- QR-Code führt korrekt zur Arten-Seite

**Screenshot-Checkpoint**: QR-Code-Scan-Ergebnis zeigt Species-Seite

**Tags**: [req-032, plant-factsheet, qr-code, species-link, no-plant-instance]

---

### TC-032-037: QR-Code-Größe ist mindestens 20mm in allen Layouts

**Requirement**: REQ-032 §2.7 — QR-Code-Größe min. 20×20mm
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- PlantLabelDialog ist geöffnet mit einer Pflanze
- Layout "9 pro Seite (3×3)" ist ausgewählt (kleinste Karten, kritischste Anforderung)

**Testschritte**:
1. Nutzer wählt Layout "9 pro Seite (3×3)"
2. Nutzer klickt auf "PDF herunterladen"
3. Nutzer öffnet die PDF und misst den QR-Code (oder verifiziert in der PDF-Metadaten-Ansicht)

**Erwartete Ergebnisse**:
- Der QR-Code auf jeder Karte ist mindestens 20×20mm groß (im 3×3-Grid ist dies die kritische Mindestgröße)
- Der QR-Code kann mit einem handelsüblichen Smartphone-Scanner gelesen werden
- Der QR-Code ist nicht durch andere Kartenelemente überdeckt

**Nachbedingungen**:
- Alle QR-Codes sind funktional scanbar

**Screenshot-Checkpoint**: PDF mit 9 Karten; QR-Code-Größe erkennbar

**Tags**: [req-032, plant-label, qr-code, min-size-20mm, grid-3x3]

---

### TC-032-038: PrintButton erscheint auch in der Pflege-Dashboard-Toolbar (Pflege-Checkliste)

**Requirement**: REQ-032 §2.2 — Pflege-Checkliste Druckzugang; §6.1 — PrintButton-Platzierung
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Pflege-Dashboard ist geöffnet und zeigt mindestens eine fällige Aufgabe

**Testschritte**:
1. Nutzer navigiert zum Pflege-Dashboard
2. Nutzer betrachtet die Toolbar der Seite

**Erwartete Ergebnisse**:
- Ein "Checkliste drucken"-Button oder ein PrintButton-Icon ist in der Toolbar sichtbar
- Der Button ist aktiviert
- Beim Hover zeigt er "Pflege-Checkliste drucken" als Tooltip

**Nachbedingungen**:
- Keine Statusänderung

**Screenshot-Checkpoint**: Pflege-Dashboard-Toolbar mit PrintButton

**Tags**: [req-032, care-checklist, print-button, toolbar, care-dashboard]

---

### TC-032-039: Druckansicht des Nährstoffplans zeigt korrekte Mischreihenfolge

**Requirement**: REQ-032 §2.1 — Nährstoffplan, Mischanleitungen mit Mischreihenfolge
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Ein Nährstoffplan ist vorhanden mit einer Phase, die mehrere Düngemittel enthält (darunter CalMag)
- Die Mischreihenfolge ist: CalMag → Base A → Base B → Additive

**Testschritte**:
1. Nutzer öffnet die Nährstoffplan-Detailseite
2. Nutzer klickt auf "PDF herunterladen" (oder Browser-Druck)
3. Nutzer betrachtet die Mischanleitung in der PDF / Druckvorschau

**Erwartete Ergebnisse**:
- Die Mischanleitung für jede Phase ist als nummerierte Liste dargestellt (1. CalMag, 2. Base A, 3. Base B, 4. Additive)
- Die Reihenfolge entspricht der im System definierten Mischreihenfolge (CalMag vor Sulfaten)
- Mengenangaben in ml/L sind klar lesbar
- Wasser-Konfiguration (Basis-EC, pH-Ziel, RO-Anteil) ist im Kopfbereich der Tabelle aufgeführt

**Nachbedingungen**:
- Druckdokument zeigt korrekte Mischreihenfolge

**Screenshot-Checkpoint**: Mischanleitung mit nummerierter Reihenfolge in der PDF

**Tags**: [req-032, nutrient-plan, mixing-order, calmag, pdf-content]

---

### TC-032-040: Druckansicht des Ernteprotokolls enthält Karenz-Status der letzten Behandlung

**Requirement**: REQ-032 §2.4 — Ernteprotokoll: Behandlungen + Karenz-Status
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Eine Ernte-Charge ist vorhanden
- Für die zugehörige Pflanze gab es zuletzt eine IPM-Behandlung mit einem Karenz-Intervall (z.B. "Behandlung Datum: 20.03.2026, Karenz: 14 Tage, Ernte: 05.04.2026 → Karenz eingehalten")

**Testschritte**:
1. Nutzer öffnet die Detailseite der Ernte-Charge
2. Nutzer klickt auf "Ernteprotokoll herunterladen"
3. Nutzer öffnet die PDF

**Erwartete Ergebnisse**:
- Die PDF zeigt im Abschnitt "IPM-Behandlungen" die letzte Behandlung mit: Datum, Wirkstoff/Mittel, Karenz-Intervall (Tage)
- Der Karenz-Status ist klar ausgewiesen: "Karenz eingehalten ✓" oder "Karenzzeit nicht abgelaufen ✗"
- Die Berechnung ist nachvollziehbar (Behandlungsdatum + Karenz-Tage = Freigabedatum)

**Nachbedingungen**:
- Karenz-Dokumentation ist im Protokoll vollständig

**Screenshot-Checkpoint**: Ernteprotokoll-PDF mit Karenz-Status-Abschnitt

**Tags**: [req-032, harvest-report, karenz-status, ipm-treatment, pdf-content]

---

### TC-032-041: Browser-Druck der Standort-Übersicht blendet interaktive Elemente aus

**Requirement**: REQ-032 §3.1 — Browser-Druckansicht: keine interaktiven Elemente
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf einer Standort-Detailseite mit belegten Slots

**Testschritte**:
1. Nutzer klickt auf "Standort-Übersicht drucken" (Browser-Druck-Modus)
2. Nutzer betrachtet die Druckvorschau

**Erwartete Ergebnisse**:
- Buttons (Bearbeiten, Hinzufügen, Filter, Sortierung) sind in der Druckvorschau nicht sichtbar
- Dropdown-Menüs und interaktive Chips sind ausgeblendet
- Nur die tabellarische oder visuelle Darstellung der Slot-Belegung ist sichtbar
- Die Farbcodierung der Phasen ist in Graustufen oder mit ausreichendem Kontrast für den Schwarz-Weiß-Druck dargestellt

**Nachbedingungen**:
- Druckvorschau zeigt nur druckbaren Inhalt

**Screenshot-Checkpoint**: Druckvorschau der Standort-Übersicht ohne Buttons und Chips

**Tags**: [req-032, location-overview, browser-print, no-interactive-elements]

---

### TC-032-042: PDF-Dateiname enthält Entity-Name und Datum

**Requirement**: REQ-032 §3.2 — Response mit `Content-Disposition: attachment`
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Nährstoffplan mit dem Namen "Grundplan Tomate" ist vorhanden

**Testschritte**:
1. Nutzer klickt auf "PDF herunterladen" auf der Detailseite des Nährstoffplans "Grundplan Tomate"
2. Nutzer betrachtet den Dateinamen der heruntergeladenen Datei im Download-Bereich des Browsers

**Erwartete Ergebnisse**:
- Der Dateiname ist sprechend und enthält: den Plan-Namen (slugified, z.B. "grundplan-tomate") und das heutige Datum (z.B. "2026-04-02")
- Beispiel-Dateiname: `naehrstoffplan-grundplan-tomate-2026-04-02.pdf`
- Sonderzeichen und Umlaute sind im Dateinamen escaped oder ersetzt (keine ungültigen Zeichen)
- Die Dateiendung ist `.pdf`

**Nachbedingungen**:
- PDF liegt mit sprechendem Dateinamen vor

**Screenshot-Checkpoint**: Browser-Download-Bereich mit korrektem Dateinamen

**Tags**: [req-032, pdf-export, filename, content-disposition, download]

---

### TC-032-043: Gießplan zeigt vollständigen Zeitraum (Tage der Abwesenheit)

**Requirement**: REQ-032 §2.3 — Gießplan / Urlaubsvertretung
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 3 Pflanzen mit konfigurierten Gießintervallen sind vorhanden

**Testschritte**:
1. Nutzer navigiert zur Gießplan-Ansicht oder Urlaubsvertretungs-Funktion
2. Nutzer wählt einen Zeitraum aus (z.B. 7 Tage: 05.04.2026 – 12.04.2026)
3. Nutzer klickt auf "Gießplan drucken" (Browser-Druck oder PDF)
4. Nutzer betrachtet das Dokument

**Erwartete Ergebnisse**:
- Der ausgewählte Zeitraum ist als Überschrift sichtbar ("Gießplan 05.04.2026 – 12.04.2026")
- Für jede Pflanze sind die Gießtage innerhalb des Zeitraums aufgelistet oder als Wochentag-Raster dargestellt
- Wassermenge (ml/L pro Gießvorgang) ist angegeben
- Besonderheiten ("Von unten gießen", "Nebeln", "Kein Kalk") sind je Pflanze aufgeführt
- Dünger-Information (ob gedüngt werden soll, welches Mittel, wie viel) ist enthalten

**Nachbedingungen**:
- Urlaubsvertretungs-Gießplan liegt vollständig vor

**Screenshot-Checkpoint**: Gießplan mit Zeitraum-Überschrift und Tagesplan pro Pflanze

**Tags**: [req-032, watering-plan, vacation-handover, date-range, watering-schedule]

---

### TC-032-044: i18n — Druckansicht wechselt bei aktiver EN-Locale zur englischen Sprache

**Requirement**: REQ-032 §8 — i18n: alle Templates in DE und EN
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- App-Sprache ist auf Englisch umgestellt (im Nutzerprofil oder Sprachumschalter)

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines Nährstoffplans
2. Nutzer klickt auf "Download PDF" (Button-Beschriftung erscheint in der aktiven Sprache)
3. Nutzer öffnet die heruntergeladene PDF

**Erwartete Ergebnisse**:
- Die PDF enthält englische Beschriftungen ("Nutrient Plan", "Phase", "EC Target", "Mixing Instructions", "Notes")
- Der PrintButton in der Toolbar ist mit englischem Text beschriftet ("Print" / "Download PDF")
- Daten (Zahlen, Einheiten) sind identisch zur deutschen Version

**Nachbedingungen**:
- Englischsprachige PDF liegt vor

**Screenshot-Checkpoint**: PDF in englischer Sprache mit englischen Spaltenüberschriften

**Tags**: [req-032, i18n, locale-en, pdf-export, english-labels]

---

### TC-032-045: PDF-Generierung unter 5 Sekunden für Einzeldokumente

**Requirement**: REQ-032 §8 — PDF-Generierung < 5 Sekunden für Einzeldokumente
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Nährstoffplan-Detailseite ist geöffnet (Einzeldokument, nicht Sammelausdruck)
- System ist unter normaler Last (keine simulierte Überlast)

**Testschritte**:
1. Nutzer notiert die Uhrzeit (oder ein Tester misst mit Stoppuhr)
2. Nutzer klickt auf "PDF herunterladen"
3. Nutzer wartet bis der Download beginnt
4. Nutzer notiert die Zeit bis zum Download-Start

**Erwartete Ergebnisse**:
- Der Download-Start tritt innerhalb von 5 Sekunden nach dem Klick ein
- Der Lade-Indikator im PrintButton ist sichtbar während der Generierung
- Kein Browser-Timeout oder Freeze tritt auf
- Die Seite bleibt während der Generierung responsive (andere Elemente der Seite können noch geklickt werden)

**Nachbedingungen**:
- PDF liegt vor; Generierungszeit war unter 5 Sekunden

**Screenshot-Checkpoint**: Lade-Indikator während PDF-Generierung

**Tags**: [req-032, performance, pdf-generation, under-5-seconds, nfr]

---

### TC-032-046: Standort-Übersicht-Druck ist aus der Standort-Detailseite erreichbar

**Requirement**: REQ-032 §6.1 — PrintButton-Platzierung; §2.5 — Standort-Übersicht
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens ein Standort mit belegten Slots ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines Standorts
2. Nutzer sucht nach einem Druck-/Export-Button in der Toolbar oder im Aktionsbereich

**Erwartete Ergebnisse**:
- Ein PrintButton (Icon oder Button "Standort drucken") ist in der Toolbar sichtbar
- Der Button ist aktiviert
- Beim Hover zeigt der Button "Standort-Übersicht drucken" oder "Beetplan als PDF herunterladen"

**Nachbedingungen**:
- Keine Statusänderung

**Screenshot-Checkpoint**: Standort-Detailseite-Toolbar mit PrintButton

**Tags**: [req-032, location-overview, print-button, toolbar, navigation]

---

### TC-032-047: Ernteprotokoll-Druck ist aus der Ernte-Charge-Detailseite erreichbar

**Requirement**: REQ-032 §6.1 — PrintButton-Platzierung; §2.4 — Ernteprotokoll
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens eine abgeschlossene Ernte-Charge ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Ernte-Charge
2. Nutzer sucht nach einem Druck-/Export-Button in der Toolbar

**Erwartete Ergebnisse**:
- Ein PrintButton oder "Protokoll herunterladen"-Button ist in der Toolbar sichtbar
- Der Button ist aktiviert
- Beim Hover zeigt der Button "Ernteprotokoll als PDF herunterladen" oder ähnlich

**Nachbedingungen**:
- Keine Statusänderung

**Screenshot-Checkpoint**: Ernte-Charge-Detailseite-Toolbar mit PrintButton

**Tags**: [req-032, harvest-report, print-button, toolbar, navigation]

---

## Coverage-Matrix

| Spec-Abschnitt | Beschreibung | Testfälle |
|----------------|--------------|-----------|
| §2.1 | Nährstoffplan-Druckinhalt | TC-032-003, TC-032-004, TC-032-006, TC-032-039 |
| §2.2 | Pflege-Checkliste | TC-032-005, TC-032-028, TC-032-038 |
| §2.3 | Gießplan / Urlaubsvertretung | TC-032-025, TC-032-043 |
| §2.4 | Ernteprotokoll | TC-032-007, TC-032-023, TC-032-040, TC-032-047 |
| §2.5 | Standort-Übersicht / Beetplan | TC-032-008, TC-032-041, TC-032-046 |
| §2.6 | Pflanzen-Steckbrief | TC-032-010, TC-032-026, TC-032-036 |
| §2.7 Pflanzen-Infokarte | QR-Code, Felder, Layouts | TC-032-011 bis TC-032-016, TC-032-019, TC-032-020, TC-032-037 |
| §2.7 Sammelausdruck | Mehrfachauswahl, Grid | TC-032-017, TC-032-018, TC-032-019, TC-032-020, TC-032-021 |
| §2.8 | Kalender-Übersicht | TC-032-027 |
| §3.1 | Browser-Druckansicht (@media print) | TC-032-003, TC-032-004, TC-032-005, TC-032-041 |
| §3.2 | PDF-Export | TC-032-006, TC-032-007, TC-032-008, TC-032-009, TC-032-010, TC-032-029, TC-032-030, TC-032-032, TC-032-042 |
| §3.3 | CSV-Export | TC-032-022, TC-032-023, TC-032-024 |
| §5 | API Query-Parameter | TC-032-010, TC-032-031 |
| §6.1 | PrintButton-Komponente | TC-032-001, TC-032-002, TC-032-009, TC-032-038, TC-032-046, TC-032-047 |
| §6.2 | PlantLabelDialog | TC-032-011 bis TC-032-016, TC-032-017, TC-032-018, TC-032-031 |
| §7 | Berechtigungen | TC-032-033, TC-032-034, TC-032-035 |
| §8 | NFR (Performance, i18n, A4) | TC-032-010, TC-032-044, TC-032-045 |
