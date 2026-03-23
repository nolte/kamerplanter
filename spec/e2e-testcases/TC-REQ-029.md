---
req_id: REQ-029
title: KI-basierte Pflanzenidentifikation via Plant.id (Optional)
category: Integration
test_count: 58
coverage_areas:
  - Feature-Toggle-Anzeige (Kamera-Buttons ein-/ausgeblendet)
  - Consent-Dialog (Einwilligung zur Bildübertragung)
  - Consent-Widerruf (Datenschutz-Einstellungen)
  - PlantIdentificationDialog (Kamera-Button, Datei-Upload, Drag & Drop)
  - Organ-Auswahl (Blatt, Blüte, Frucht, Rinde, Ganze Pflanze)
  - Analysierend-Zustand (Lade-Skeleton, "Pflanze wird analysiert...")
  - Ergebnis-Cards (Konfidenz-Bar, Referenzbild, Common Name)
  - Species-Match-Anzeige (im System vs. noch nicht im System)
  - Auswahl-Bestätigung ("Diese Pflanze anlegen")
  - Manuelle Fallback-Suche
  - Niedrige Konfidenz und Unsicherheits-Hinweis
  - Kein Pflanzenmaterial erkannt
  - Krankheitsdiagnose-Tab (Health Assessment)
  - IPM-Match bei Diagnose
  - Rate-Limit-Fehlermeldung
  - Identifikations-Historie
  - Onboarding-Integration (optionaler Schritt 0)
  - Erfahrungsstufen-Anpassung (Beginner / Intermediate / Expert)
  - EXIF-Stripping (Datenschutz — nicht direkt testbar, proxy über Datenschutzerklärung)
  - PlantNet-Fallback-Verhalten
  - Integration in Stammdaten-Übersicht (FAB)
  - Integration in PlantInstance-Detail
  - Integration in IPM-Inspektion
  - Integration in Pflege-Dashboard
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-029: KI-basierte Pflanzenidentifikation

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-029 KI-basierte Pflanzenidentifikation via Plant.id v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte aus `pages.identification.*`.

REQ-029 ist vollstaendig optional — ohne API-Key ist die Funktion deaktiviert und die App funktioniert ohne Einschraenkung. Testfaelle setzen voraus, dass das Feature-Toggle-Verhalten (aktiviert vs. deaktiviert) explizit geprueft wird.

**Hinweis zur Implementierung:** REQ-029 ist zum Stand 2026-03-21 noch nicht implementiert. Alle Testfaelle sind spec-forward und koennen erst ausgefuehrt werden, wenn `PlantIdentificationDialog`, die API-Endpunkte und die Onboarding-Integration im Frontend vorhanden sind. Testfaelle ohne Implementierungsvorbedingung sind als "blockiert: ausstehende Implementierung" zu kennzeichnen.

---

## 1. Feature-Toggle: Kamera-Buttons ein-/ausgeblendet

### TC-029-001: Kamera-Buttons sind ausgeblendet wenn kein API-Key konfiguriert

**Requirement**: REQ-029 §6.3 — Feature-Toggle-Logik, §9 Szenario 5
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Weder `PLANT_ID_API_KEY` noch `PLANTNET_API_KEY` ist in der Serverumgebung gesetzt
- Nutzer ist eingeloggt und Mitglied eines Tenants
- Nutzer befindet sich auf der Stammdaten-Uebersicht (z.B. `/stammdaten/pflanzen` oder aequivalente Route)

**Testschritte**:
1. Nutzer navigiert zur Stammdaten-Uebersicht (Pflanzen-Liste)
2. Nutzer betrachtet den Bereich mit den Aktions-Buttons (FAB und Erstellen-Button)

**Erwartete Ergebnisse**:
- Es ist **kein** Floating Action Button "Pflanze per Foto hinzufuegen" sichtbar
- Es ist **kein** Kamera-Icon oder Foto-Button in der Toolbar sichtbar
- Der normale "Neue Pflanze"-Button ist weiterhin sichtbar und nutzbar
- Die Seite zeigt keine Fehlermeldung bezueglich der Bilderkennung

**Nachbedingungen**:
- Keine Aenderung am Systemzustand

**Tags**: [req-029, feature-toggle, kamera-button, ausgeblendet, graceful-degradation, stammdaten]

---

### TC-029-002: Kamera-Buttons sind ausgeblendet — PlantInstance-Detail ohne API-Key

**Requirement**: REQ-029 §4.2 — Integration PlantInstance-Detail, §6.3 Feature-Toggle
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Kein API-Key konfiguriert (weder Plant.id noch PlantNet)
- Nutzer ist eingeloggt
- Eine PlantInstance ohne zugeordnete Species existiert im System

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer bestehenden Pflanze (PlantInstance)
2. Nutzer betrachtet die Toolbar / Aktionsbereich der Detailseite

**Erwartete Ergebnisse**:
- Der Button "Per Foto identifizieren" ist **nicht** sichtbar in der Toolbar
- Die uebrigen Toolbar-Aktionen (Bearbeiten, Loeschen) sind weiterhin verfuegbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, feature-toggle, plant-instance, kamera-button, ausgeblendet]

---

### TC-029-003: Kamera-Buttons sichtbar wenn Plant.id konfiguriert

**Requirement**: REQ-029 §4.2, §6.3
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- `PLANT_ID_API_KEY` ist in der Serverumgebung gesetzt und gueltig
- Nutzer ist eingeloggt und hat Consent `plant_identification` noch nicht erteilt
- Nutzer navigiert zur Stammdaten-Uebersicht

**Testschritte**:
1. Nutzer navigiert zur Stammdaten-Uebersicht
2. Nutzer betrachtet den Aktionsbereich

**Erwartete Ergebnisse**:
- Ein Floating Action Button oder Button "Pflanze per Foto hinzufuegen" mit Kamera-Icon ist sichtbar
- Der Button ist anklickbar (nicht disabled)

**Nachbedingungen**:
- Kein Systemzustand geaendert (Consent-Dialog wird erst beim Klick geoeffnet)

**Tags**: [req-029, feature-toggle, kamera-button, sichtbar, plant-id-konfiguriert]

---

### TC-029-004: Kamera-Buttons sichtbar wenn nur PlantNet konfiguriert (Fallback)

**Requirement**: REQ-029 §6.3 — PlantNet als Fallback
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `PLANT_ID_API_KEY` ist NICHT gesetzt
- `PLANTNET_API_KEY` ist in der Serverumgebung gesetzt
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zur Stammdaten-Uebersicht

**Erwartete Ergebnisse**:
- Kamera-Button / FAB "Pflanze per Foto hinzufuegen" ist sichtbar
- Kein Hinweis auf eingeschraenkte Funktionalitaet (Artbestimmung verfuegbar)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, feature-toggle, plantnet, fallback, kamera-button]

---

## 2. Consent-Dialog (DSGVO)

### TC-029-005: Consent-Dialog erscheint beim ersten Klick auf Kamera-Button

**Requirement**: REQ-029 §5.1 — Consent-Anforderungen, §4.1 Identifikations-Dialog
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Plant.id API-Key ist konfiguriert
- Nutzer ist eingeloggt
- Nutzer hat den Consent `plant_identification` noch NICHT erteilt
- Nutzer befindet sich auf der Stammdaten-Uebersicht

**Testschritte**:
1. Nutzer klickt auf den Kamera-Button "Pflanze per Foto hinzufuegen"

**Erwartete Ergebnisse**:
- Ein Modal-Dialog mit dem Titel "Bilderkennung aktivieren" oeffnet sich
- Der Dialog zeigt den Text: "Um Pflanzen per Foto zu identifizieren, wird das Bild an den externen Dienst Plant.id gesendet. Das Bild wird dort nicht dauerhaft gespeichert. Moechten Sie diese Funktion aktivieren?"
- Ein Button "Aktivieren" ist sichtbar
- Ein Button "Nein, danke" ist sichtbar
- Der Identifikations-Dialog selbst oeffnet sich noch NICHT

**Nachbedingungen**:
- Consent-Status unveraendert (weder akzeptiert noch abgelehnt)

**Tags**: [req-029, consent, dsgvo, dialog, plant-identification, erstnutzung]

---

### TC-029-006: Consent akzeptieren oeffnet Identifikations-Dialog

**Requirement**: REQ-029 §5.1
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Consent-Dialog ist geoeffnet (Vorbedingung aus TC-029-005)

**Testschritte**:
1. Nutzer klickt "Aktivieren" im Consent-Dialog

**Erwartete Ergebnisse**:
- Consent-Dialog schliesst sich
- Der `PlantIdentificationDialog` oeffnet sich direkt
- Im Dialog ist ein Kamera-Button "Foto aufnehmen" und ein Upload-Bereich "Foto hochladen" sichtbar
- Beim naechsten Oeffnen des Kamera-Buttons erscheint kein Consent-Dialog mehr

**Nachbedingungen**:
- Consent `plant_identification` ist als erteilt gespeichert
- Einstellungen → Datenschutz zeigt den Consent als aktiv

**Tags**: [req-029, consent, akzeptieren, identifikation-dialog, oeffnet]

---

### TC-029-007: Consent ablehnen schliesst Dialog — Funktion bleibt gesperrt

**Requirement**: REQ-029 §5.1
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Consent-Dialog ist geoeffnet

**Testschritte**:
1. Nutzer klickt "Nein, danke" im Consent-Dialog

**Erwartete Ergebnisse**:
- Consent-Dialog schliesst sich
- Der Identifikations-Dialog oeffnet sich NICHT
- Der Kamera-Button in der Stammdaten-Uebersicht ist weiterhin sichtbar
- Beim erneuten Klick auf den Kamera-Button erscheint der Consent-Dialog erneut

**Nachbedingungen**:
- Consent `plant_identification` bleibt nicht erteilt

**Tags**: [req-029, consent, ablehnen, gesperrt, erneuter-versuch]

---

### TC-029-008: Consent-Widerruf in Datenschutz-Einstellungen

**Requirement**: REQ-029 §5.1, §9 Szenario 10
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat Consent `plant_identification` erteilt (z.B. per TC-029-006)
- Nutzer hat bereits mehrere Identifikationen durchgefuehrt
- Nutzer navigiert zu Einstellungen → Datenschutz

**Testschritte**:
1. Nutzer oeffnet die Seite "Einstellungen → Datenschutz" (z.B. `/settings/privacy`)
2. Nutzer findet den Consent-Toggle fuer "Pflanzenerkennung (Plant.id / PlantNet)"
3. Nutzer deaktiviert den Toggle

**Erwartete Ergebnisse**:
- Toggle wechselt in den Aus-Zustand
- Eine Bestaetigung erscheint (z.B. Snackbar "Einwilligung widerrufen")
- Die Stammdaten-Seite und PlantInstance-Details zeigen nun keine Kamera-Buttons mehr
- Die Identifikations-Historie ist noch sichtbar (keine Bilddaten gespeichert — nur Metadaten)

**Nachbedingungen**:
- Consent `plant_identification` = abgelehnt/widerrufen
- Erneuter Klick auf Kamera-Button (sofern noch sichtbar) zeigt erneut den Consent-Dialog

**Tags**: [req-029, consent, widerruf, datenschutz, toggle, historie-erhalten]

---

### TC-029-009: Kamera-Button nicht sichtbar nach Consent-Widerruf

**Requirement**: REQ-029 §9 Szenario 10
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Consent wurde gemaess TC-029-008 widerrufen
- Nutzer navigiert zur Stammdaten-Uebersicht

**Testschritte**:
1. Nutzer betrachtet die Stammdaten-Uebersicht nach dem Consent-Widerruf

**Erwartete Ergebnisse**:
- Der Kamera-Button / FAB "Pflanze per Foto hinzufuegen" ist ausgeblendet oder ausgegraut
- Die Seite zeigt keinen Fehler, alle anderen Funktionen sind nutzbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, consent, widerruf, kamera-button, ausgeblendet]

---

## 3. PlantIdentificationDialog — Bild-Upload und Analyse

### TC-029-010: Dialog oeffnet mit Kamera- und Upload-Option

**Requirement**: REQ-029 §4.1 — Identifikations-Dialog
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Nutzer klickt Kamera-Button in der Stammdaten-Uebersicht

**Testschritte**:
1. Nutzer klickt auf den FAB "Pflanze per Foto hinzufuegen"

**Erwartete Ergebnisse**:
- Ein Modal-Dialog mit dem Titel "Pflanze identifizieren" oeffnet sich
- Ein Button "Foto aufnehmen" mit Kamera-Icon ist sichtbar
- Ein Bereich "Foto hochladen" (Drag & Drop Zone oder Datei-Button) ist sichtbar
- Ein "Abbrechen"-Button oder X-Icon ist vorhanden

**Nachbedingungen**:
- Dialog ist geoeffnet

**Tags**: [req-029, dialog, upload, kamera, drag-drop, oeffnen]

---

### TC-029-011: JPEG-Datei hochladen und Analyse starten

**Requirement**: REQ-029 §4.1, §3.5 (MAX_IMAGE_SIZE_BYTES = 5 MB), §9 Szenario 1
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- `PlantIdentificationDialog` ist geoeffnet
- Consent erteilt, Plant.id konfiguriert
- Eine JPEG-Testdatei (z.B. `monstera.jpg`, 1,2 MB) steht bereit
- Species "Monstera deliciosa" existiert in den Stammdaten

**Testschritte**:
1. Nutzer klickt auf "Foto hochladen" oder zieht Datei in die Drag & Drop Zone
2. Nutzer waehlt die Datei `monstera.jpg` (1,2 MB, JPEG)
3. Nutzer beobachtet den Dialog

**Erwartete Ergebnisse**:
- Die Datei wird akzeptiert (kein Fehler)
- Ein Lade-Skeleton oder Ladeindikator erscheint mit dem Text "Pflanze wird analysiert..."
- Nach Abschluss der Analyse verschwindet der Ladeindikator
- Mindestens 1 Ergebnis-Card erscheint mit: Pflanzenname (z.B. "Monstera deliciosa"), Konfidenz-Balken, Referenzbild
- Das erste Ergebnis (hoechste Konfidenz) ist prominent dargestellt

**Nachbedingungen**:
- Analyseergebnis ist im Dialog sichtbar

**Tags**: [req-029, upload, jpeg, analyse, ladeindikator, ergebnis-card, happy-path]

---

### TC-029-012: PNG-Datei wird akzeptiert

**Requirement**: REQ-029 §3.5 — validate_image (JPEG oder PNG)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Dialog geoeffnet, Consent erteilt
- Eine PNG-Testdatei (z.B. `fern.png`, 800 KB) steht bereit

**Testschritte**:
1. Nutzer laedt `fern.png` in den Dialog hoch

**Erwartete Ergebnisse**:
- Datei wird akzeptiert
- Analyse startet (Ladeindikator erscheint)
- Keine Fehlermeldung ueber Dateiformat

**Nachbedingungen**:
- Analyse laeuft oder Ergebnis wird angezeigt

**Tags**: [req-029, upload, png, dateiformat, akzeptiert]

---

### TC-029-013: Nicht-unterstuetztes Dateiformat wird abgelehnt (GIF)

**Requirement**: REQ-029 §3.7 (`image/jpeg` oder `image/png`), §4.1
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog geoeffnet
- Eine GIF-Datei (`animation.gif`) steht bereit

**Testschritte**:
1. Nutzer versucht, `animation.gif` hochzuladen (Dateiauswahl oder Drag & Drop)

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint, z.B. "Nur JPEG- und PNG-Bilder werden akzeptiert." oder aequivalent
- Die Analyse startet NICHT
- Der Dialog bleibt geoeffnet und der Upload-Bereich ist erneut nutzbar

**Nachbedingungen**:
- Kein Analyseergebnis

**Tags**: [req-029, upload, dateiformat, fehler, gif, ablehnung]

---

### TC-029-014: Datei zu gross wird abgelehnt (> 5 MB)

**Requirement**: REQ-029 §3.5 — MAX_IMAGE_SIZE_BYTES = 5 MB, §3.8 Konfiguration
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog geoeffnet
- Eine JPEG-Datei `large_photo.jpg` mit 6,5 MB steht bereit

**Testschritte**:
1. Nutzer laedt `large_photo.jpg` (6,5 MB) hoch

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint, z.B. "Das Bild ist zu gross. Maximale Dateigrösse: 5 MB."
- Die Analyse startet NICHT
- Der Upload-Bereich ist erneut nutzbar

**Nachbedingungen**:
- Kein Analyseergebnis

**Tags**: [req-029, upload, dateigrösse, fehler, 5mb-limit]

---

### TC-029-015: Datei genau an der 5-MB-Grenze wird akzeptiert

**Requirement**: REQ-029 §3.5 (Grenzwert-Test)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog geoeffnet
- Eine JPEG-Datei `boundary.jpg` mit exakt 5.242.880 Bytes (5 MB) steht bereit

**Testschritte**:
1. Nutzer laedt `boundary.jpg` (genau 5 MB) hoch

**Erwartete Ergebnisse**:
- Datei wird akzeptiert (kein Grössen-Fehler)
- Analyse startet

**Nachbedingungen**:
- Analyse laeuft oder Ergebnis wird angezeigt

**Tags**: [req-029, upload, dateigrösse, grenzwert, 5mb-exakt]

---

### TC-029-016: Dialog kann ohne Aktion geschlossen werden

**Requirement**: REQ-029 §4.1
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Dialog geoeffnet, noch kein Bild hochgeladen

**Testschritte**:
1. Nutzer klickt auf "Abbrechen" oder das X-Icon des Dialogs

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Nutzer kehrt zur aufrufenden Seite zurueck
- Keine Fehlermeldung oder Datenveraenderung

**Nachbedingungen**:
- Kein Datenbankzustand geaendert

**Tags**: [req-029, dialog, schliessen, abbrechen]

---

## 4. Organ-Auswahl

### TC-029-017: Organ-Auswahl ausgeblendet fuer Beginner

**Requirement**: REQ-029 §4.3 — Erfahrungsstufen, Beginner: Organ-Auswahl ausgeblendet
**Priority**: High
**Category**: Erfahrungsstufen
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Nutzer hat Erfahrungsstufe "Beginner" aktiv
- `PlantIdentificationDialog` ist geoeffnet

**Testschritte**:
1. Nutzer betrachtet den geoeffneten Identifikations-Dialog

**Erwartete Ergebnisse**:
- Die Organ-Auswahl (Chips/Buttons: "Blatt", "Bluete", "Frucht", "Rinde", "Ganze Pflanze") ist **nicht** sichtbar
- Der Dialog zeigt nur Kamera/Upload-Bereich
- Es wird automatisch "Automatisch erkennen" verwendet (kein sichtbarer Hinweis noetig)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, erfahrungsstufen, beginner, organ-auswahl, ausgeblendet]

---

### TC-029-018: Organ-Auswahl sichtbar fuer Intermediate und Expert

**Requirement**: REQ-029 §4.3 — Intermediate/Expert: Organ-Auswahl sichtbar
**Priority**: High
**Category**: Erfahrungsstufen
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Intermediate" oder "Expert" aktiv
- `PlantIdentificationDialog` ist geoeffnet

**Testschritte**:
1. Nutzer betrachtet den geoeffneten Identifikations-Dialog

**Erwartete Ergebnisse**:
- Eine Organ-Auswahl-Sektion mit Label "Was ist auf dem Foto?" ist sichtbar
- Chips oder Buttons fuer: "Blatt", "Bluete", "Frucht", "Rinde", "Ganze Pflanze", "Automatisch erkennen"
- "Automatisch erkennen" ist vorausgewaehlt (Default)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, erfahrungsstufen, intermediate, expert, organ-auswahl, sichtbar]

---

### TC-029-019: Organ "Blatt" auswaehlen und Analyse starten

**Requirement**: REQ-029 §4.1 — Organ-Auswahl, §3.1 PlantOrgan enum
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Intermediate"
- Dialog geoeffnet, Organ-Auswahl sichtbar

**Testschritte**:
1. Nutzer klickt auf den Chip "Blatt"
2. Nutzer laedt ein JPEG-Bild hoch

**Erwartete Ergebnisse**:
- Der "Blatt"-Chip ist visuell als ausgewaehlt markiert (z.B. filled/highlighted)
- Die Analyse startet mit Organ-Parameter "leaf"
- Die Ergebnis-Cards erscheinen wie im normalen Flow

**Nachbedingungen**:
- Analyse abgeschlossen

**Tags**: [req-029, organ, blatt, auswahl, analyse]

---

## 5. Identifikationsergebnisse

### TC-029-020: Ergebnis-Card mit hoher Konfidenz — Species im System

**Requirement**: REQ-029 §4.1, §3.5, §9 Szenario 1
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plant.id API liefert "Monstera deliciosa" mit Konfidenz 0.94 (gemocked oder real)
- Species "Monstera deliciosa" existiert in den lokalen Stammdaten
- Dialog-Analyse abgeschlossen

**Testschritte**:
1. Nutzer betrachtet die Ergebnis-Liste nach abgeschlossener Analyse

**Erwartete Ergebnisse**:
- Mindestens 1 Ergebnis-Card ist sichtbar
- Die erste Card zeigt: "Monstera deliciosa" als Artnamen
- Ein Konfidenz-Indikator (Balken oder Prozentzahl) ist sichtbar
- Ein Referenzbild der Pflanze aus dem Plant.id-Dienst ist sichtbar
- Ein Button "Diese Pflanze anlegen" ist sichtbar
- Kein Hinweis "Diese Art ist noch nicht im System" erscheint

**Nachbedingungen**:
- Keine Aenderung am Datenbankzustand

**Tags**: [req-029, ergebnis-card, hohe-konfidenz, species-match, in-system]

---

### TC-029-021: Ergebnis zeigt mehrere Vorschlaege (Top-3)

**Requirement**: REQ-029 §4.1 — Top-3 Vorschlaege als Cards
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Plant.id liefert 3 oder mehr Vorschlaege mit Konfidenz >= 0.10
- Dialog-Analyse abgeschlossen

**Testschritte**:
1. Nutzer betrachtet die Ergebnis-Liste

**Erwartete Ergebnisse**:
- Es werden bis zu 3 Ergebnis-Cards angezeigt (sortiert nach Konfidenz, hoechste zuerst)
- Jede Card zeigt einen eigenen Pflanzennamen und einen Konfidenz-Indikator
- Jede Card hat einen "Diese Pflanze anlegen"-Button (oder entsprechende Aktion)
- Der erste Vorschlag ist visuell hervorgehoben (z.B. als empfohlene Auswahl)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, ergebnis-liste, top-3, mehrere-vorschlaege, sortierung]

---

### TC-029-022: Konfidenz-Anzeige je Erfahrungsstufe

**Requirement**: REQ-029 §4.3 — Beginner: Konfidenz ausgeblendet; Intermediate: Prozent; Expert: Prozent + Raw Score
**Priority**: Medium
**Category**: Erfahrungsstufen
**Preconditions**:
- Analyse wurde abgeschlossen, Ergebnisse liegen vor

**Testschritte (Beginner)**:
1. Nutzer mit Erfahrungsstufe "Beginner" betrachtet die Ergebnis-Cards

**Erwartete Ergebnisse (Beginner)**:
- Kein numerischer Konfidenz-Wert ist sichtbar (weder Prozent noch Dezimalzahl)

**Testschritte (Intermediate)**:
2. Nutzer wechselt auf Erfahrungsstufe "Intermediate" und fuehrt Analyse erneut durch

**Erwartete Ergebnisse (Intermediate)**:
- Konfidenz als Prozentzahl sichtbar (z.B. "94%")

**Testschritte (Expert)**:
3. Nutzer wechselt auf "Expert"

**Erwartete Ergebnisse (Expert)**:
- Konfidenz als Prozent UND als Dezimalzahl (z.B. "94% (0.9432)")
- GBIF-Link ist sichtbar (sofern vorhanden)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, konfidenz, erfahrungsstufen, beginner, intermediate, expert, anzeige]

---

### TC-029-023: Expert sieht rohe API-Antwortdaten

**Requirement**: REQ-029 §4.3 — Expert: Expandable JSON
**Priority**: Low
**Category**: Erfahrungsstufen
**Preconditions**:
- Erfahrungsstufe "Expert" aktiv
- Analyse abgeschlossen, Ergebnisse vorhanden

**Testschritte**:
1. Nutzer mit Expert-Level klappt den "Rohdaten"-Bereich einer Ergebnis-Card auf (z.B. per "Details"-Button oder Expand-Icon)

**Erwartete Ergebnisse**:
- Ein aufklappbarer Bereich zeigt die rohen JSON-Daten der API-Antwort fuer diesen Vorschlag
- Die Daten sind lesbar formatiert (eingerueckt)
- Fuer Beginner und Intermediate ist dieser Bereich nicht sichtbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, expert, rohdaten, json, expandable, api-response]

---

### TC-029-024: Species NICHT im System — Hinweis und Anlegen-Option

**Requirement**: REQ-029 §4.1, §9 Szenario 2
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Plant.id liefert "Alocasia zebrina" mit Konfidenz 0.87
- Species "Alocasia zebrina" existiert NICHT in den lokalen Stammdaten

**Testschritte**:
1. Nutzer betrachtet die Ergebnis-Cards nach der Analyse

**Erwartete Ergebnisse**:
- Die Ergebnis-Card fuer "Alocasia zebrina" zeigt einen Hinweis, z.B. "Diese Art ist noch nicht im System"
- Statt "Diese Pflanze anlegen" erscheint ein Button "Art hinzufuegen und Pflanze anlegen"
- Der Button ermoeglicht, die Art aus den Plant.id-Daten (Name, Familie, Gattung) als neue Species anzulegen
- Anschliessend wird der PlantInstance-Erstellungsdialog mit der neuen Species vorausgewaehlt

**Nachbedingungen**:
- Neue Species ist im System gespeichert (nach Benutzeraktion)

**Tags**: [req-029, species-nicht-im-system, art-hinzufuegen, neu-anlegen, szenario-2]

---

### TC-029-025: Niedrige Konfidenz — Unsicherheits-Hinweis sichtbar

**Requirement**: REQ-029 §3.5 (CONFIDENCE_AUTO_ACCEPT = 0.85), §9 Szenario 3
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Plant.id liefert Top-Ergebnis mit Konfidenz 0.35 (unter 0.85)
- Andere Ergebnisse haben Konfidenz >= 0.10

**Testschritte**:
1. Nutzer betrachtet die Ergebnis-Cards nach der Analyse

**Erwartete Ergebnisse**:
- Alle Ergebnisse mit Konfidenz >= 0.10 werden angezeigt
- Kein Ergebnis ist als "Auto-Accept" oder bevorzugte Auswahl hervorgehoben
- Ein Hinweis-Banner oder -Text erscheint, z.B. "Die Erkennung ist unsicher. Bitte pruefen Sie die Vorschlaege."
- Der Link "Pflanze nicht dabei? Manuell suchen" ist sichtbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, niedrige-konfidenz, unsicherheit, hinweis, manuelle-suche]

---

### TC-029-026: Ergebnisse unter Mindest-Konfidenz werden nicht angezeigt

**Requirement**: REQ-029 §3.5 — CONFIDENCE_SHOW_RESULTS = 0.10
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Plant.id liefert 5 Vorschlaege, davon 2 mit Konfidenz >= 0.10 und 3 mit Konfidenz < 0.10

**Testschritte**:
1. Nutzer betrachtet die Ergebnis-Liste nach Analyse

**Erwartete Ergebnisse**:
- Genau 2 Ergebnis-Cards sind sichtbar (nur die ueber der 10%-Schwelle)
- Die 3 Vorschlaege unter 0.10 werden nicht angezeigt

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, mindest-konfidenz, 10-prozent-schwelle, filterung]

---

### TC-029-027: Kein Pflanzenmaterial erkannt

**Requirement**: REQ-029 §4.1 — Fehlerzustand "kein Pflanzenmaterial", §9 Szenario 4
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Plant.id liefert `is_plant = false` (z.B. Foto eines Steins)
- Analyse abgeschlossen

**Testschritte**:
1. Nutzer betrachtet den Dialog nach Analyse eines Nicht-Pflanzen-Fotos

**Erwartete Ergebnisse**:
- Meldung erscheint: "Es konnte kein Pflanzenmaterial im Bild erkannt werden."
- Keine Ergebnis-Cards werden angezeigt
- Button "Neues Foto aufnehmen" ist sichtbar
- Link "Manuell suchen" ist sichtbar

**Nachbedingungen**:
- Kein PlantInstance-Erstellungsdialog geoeffnet

**Tags**: [req-029, kein-pflanzenmaterial, fehler, is-plant-false, szenario-4]

---

### TC-029-028: Keine Ergebnisse ueber Mindest-Konfidenz

**Requirement**: REQ-029 §4.1 — Fehlerzustand "noResults"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Plant.id liefert nur Vorschlaege mit Konfidenz < 0.10 (sehr unscharfes Bild)

**Testschritte**:
1. Nutzer betrachtet Dialog nach Analyse

**Erwartete Ergebnisse**:
- Meldung erscheint: "Keine Uebereinstimmung gefunden."
- Link "Pflanze nicht dabei? Manuell suchen" ist sichtbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, keine-ergebnisse, meldung, manuell-suchen]

---

## 6. Auswahl bestaetigen und PlantInstance anlegen

### TC-029-029: "Diese Pflanze anlegen" oeffnet PlantInstance-Erstellungsdialog

**Requirement**: REQ-029 §4.1 — Auswahl-Button, §9 Szenario 1
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Ergebnis-Cards sind sichtbar, Species "Monstera deliciosa" wurde erkannt und ist im System
- Erste Ergebnis-Card zeigt "Monstera deliciosa"

**Testschritte**:
1. Nutzer klickt "Diese Pflanze anlegen" auf der Ergebnis-Card fuer "Monstera deliciosa"

**Erwartete Ergebnisse**:
- Identifikations-Dialog schliesst sich (oder wechselt in naechste Phase)
- PlantInstance-Erstellungsdialog oeffnet sich
- Das Feld "Art" (Species) ist mit "Monstera deliciosa" vorausgefuellt
- Andere Pflichtfelder sind leer und muessen vom Nutzer ausgefuellt werden

**Nachbedingungen**:
- PlantInstance-Dialog geoeffnet mit vorausgefuellter Species

**Tags**: [req-029, anlegen, plant-instance, vorausgefuellt, species-match]

---

### TC-029-030: Manuelle Fallback-Suche per Link

**Requirement**: REQ-029 §4.1 — Fallback-Link "Pflanze nicht dabei? Manuell suchen"
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Ergebnis-Cards sind sichtbar (oder "Keine Ergebnisse"-Meldung)
- Nutzer findet keinen passenden Vorschlag

**Testschritte**:
1. Nutzer klickt auf den Link "Pflanze nicht dabei? Manuell suchen"

**Erwartete Ergebnisse**:
- Identifikations-Dialog schliesst sich oder wird durch Artsuche-Dialog ersetzt
- Ein Suchfeld zur manuellen Artsuche wird angezeigt
- Nutzer kann Artname eintippen und manuell auswaehlen

**Nachbedingungen**:
- Kein Identifikationsauftrag bestaetigt

**Tags**: [req-029, fallback, manuell-suchen, link, navigation]

---

## 7. Rate-Limiting

### TC-029-031: Rate-Limit-Fehlermeldung bei Ueberschreitung

**Requirement**: REQ-029 §7 — Rate-Limiting, §9 Szenario 6
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Plant.id Free Tier: Nutzer hat heute bereits 100 Identifikationen durchgefuehrt
- Kein PlantNet-Fallback konfiguriert
- Nutzer oeffnet Identifikations-Dialog und laedt ein Bild hoch

**Testschritte**:
1. Nutzer klickt Hochladen-Button und startet die Analyse

**Erwartete Ergebnisse**:
- Statt Ergebnissen erscheint die Meldung: "Tages-Limit fuer Bilderkennung erreicht. Morgen wieder verfuegbar."
- Kein Lade-Skeleton mehr sichtbar
- Button "Manuell suchen" ist als Fallback sichtbar

**Nachbedingungen**:
- Kein Identifikationsergebnis

**Tags**: [req-029, rate-limit, tages-limit, fehlermeldung, 429]

---

### TC-029-032: PlantNet-Fallback bei Plant.id Rate-Limit

**Requirement**: REQ-029 §7 Rate-Limit, §6.3 Fallback-Logik, §9 Szenario 6
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Plant.id Daily Limit erreicht (100 Anfragen)
- `PLANTNET_API_KEY` ist konfiguriert (Fallback aktiv)
- Nutzer startet eine neue Identifikation

**Testschritte**:
1. Nutzer laedt ein Bild hoch

**Erwartete Ergebnisse**:
- Analyse startet (Ladeindikator erscheint)
- Ergebnisse werden angezeigt (vom PlantNet-Dienst)
- Kein Rate-Limit-Fehler erscheint fuer den Nutzer
- Optionaler Hinweis moeglich: "Analyse ueber Fallback-Dienst (PlantNet)"

**Nachbedingungen**:
- Analyse ueber PlantNet durchgefuehrt

**Tags**: [req-029, rate-limit, plantnet-fallback, automatischer-wechsel]

---

### TC-029-033: Burst-Limit — 5 Anfragen in 10 Sekunden

**Requirement**: REQ-029 §7 — Burst: 5 Requests / 10 Sekunden
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat in den letzten 10 Sekunden bereits 5 Identifikationen gestartet

**Testschritte**:
1. Nutzer versucht eine sechste Identifikation unmittelbar nach den fuenf vorherigen

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (z.B. "Zu viele Anfragen in kurzer Zeit. Bitte warten Sie kurz.")
- Analyse startet nicht sofort
- Nach Ablauf des Burst-Fensters ist die Funktion wieder verfuegbar

**Nachbedingungen**:
- Keine Analyse abgeschlossen

**Tags**: [req-029, burst-limit, 5-requests, 10-sekunden, rate-limit]

---

## 8. Krankheitsdiagnose (Health Assessment)

### TC-029-034: Diagnose-Tab sichtbar wenn Plant.id konfiguriert

**Requirement**: REQ-029 §4.1 — Krankheitsdiagnose-Tab, §3.7 `POST /diagnose`
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `PLANT_ID_API_KEY` ist konfiguriert (Plant.id unterstuetzt Health Assessment)
- Consent erteilt
- Identifikations-Dialog geoeffnet

**Testschritte**:
1. Nutzer betrachtet den geoeffneten Identifikations-Dialog

**Erwartete Ergebnisse**:
- Ein Tab oder Toggle "Ist meine Pflanze krank?" mit Button "Pflanzen-Diagnose" ist sichtbar
- Der Tab/Toggle ist anklickbar

**Nachbedingungen**:
- Kein Zustandswechsel

**Tags**: [req-029, diagnose, health-assessment, tab, sichtbar, plant-id]

---

### TC-029-035: Diagnose-Tab nicht sichtbar wenn nur PlantNet konfiguriert

**Requirement**: REQ-029 §3.3 — PlantNet: keine Krankheitsdiagnose
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- `PLANT_ID_API_KEY` ist NICHT gesetzt
- Nur `PLANTNET_API_KEY` ist konfiguriert
- Consent erteilt, Dialog geoeffnet

**Testschritte**:
1. Nutzer betrachtet den geoeffneten Identifikations-Dialog

**Erwartete Ergebnisse**:
- Der Tab "Ist meine Pflanze krank?" / "Pflanzen-Diagnose" ist NICHT sichtbar
- Es erscheint kein Button oder Link fuer Krankheitsdiagnose

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, plantnet, diagnose-nicht-verfuegbar, tab-ausgeblendet]

---

### TC-029-036: Erfolgreiche Diagnose mit IPM-Match — Behandlungsvorschlaege

**Requirement**: REQ-029 §1.3 — Krankheitsdiagnose-Workflow, §9 Szenario 7
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Disease "Echter Mehltau" existiert in den IPM-Stammdaten (REQ-010)
- PlantInstance "monstera_01" existiert
- Nutzer oeffnet Diagnose-Dialog an der Pflanze "monstera_01"
- Plant.id Health Assessment liefert "Powdery Mildew" mit Konfidenz 0.87

**Testschritte**:
1. Nutzer oeffnet den Diagnose-Dialog an PlantInstance "monstera_01"
2. Nutzer laedt ein Foto eines befallenen Blatts hoch
3. Nutzer klickt "Gesundheit wird analysiert..."

**Erwartete Ergebnisse**:
- Ladeindikator erscheint mit Text "Gesundheit wird analysiert..."
- Nach Abschluss erscheint eine Diagnose-Sektion mit Titel "Erkannte Probleme"
- "Echter Mehltau" (oder "Powdery Mildew") mit Konfidenz wird angezeigt
- Ein Schweregrad-Indikator ist sichtbar
- Behandlungsvorschlaege aus den lokalen IPM-Stammdaten werden angezeigt (nicht nur externe)
- Abschnitt "Behandlungsvorschlaege" listet Massnahmen auf

**Nachbedingungen**:
- Diagnose-Request in der Datenbank gespeichert (keine Bilddaten)

**Tags**: [req-029, diagnose, ipm-match, behandlungsvorschlaege, powdery-mildew, szenario-7]

---

### TC-029-037: Diagnose ergibt "Pflanze sieht gesund aus"

**Requirement**: REQ-029 §4.4 — i18n `diagnoseHealthy`
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Plant.id liefert `is_healthy = true` mit hoher Konfidenz

**Testschritte**:
1. Nutzer laedt ein Foto einer gesunden Pflanze im Diagnose-Modus hoch

**Erwartete Ergebnisse**:
- Meldung erscheint: "Die Pflanze sieht gesund aus!"
- Keine Krankheits-Cards werden angezeigt

**Nachbedingungen**:
- Keine Behandlungsvorschlaege angezeigt

**Tags**: [req-029, diagnose, gesund, keine-probleme, healthy]

---

### TC-029-038: Diagnose ohne Plant-Instance-Zuordnung (allgemeine Diagnose)

**Requirement**: REQ-029 §3.7 `POST /diagnose` — `plant_instance_key` optional
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Nutzer oeffnet Diagnose ueber Pflege-Dashboard ohne spezifische Pflanzenzuordnung
- Plant.id liefert Diagnoseergebnis

**Testschritte**:
1. Nutzer klickt "Pflanze krank?" im Pflege-Dashboard
2. Nutzer laedt Bild hoch ohne eine spezifische Pflanze auszuwaehlen

**Erwartete Ergebnisse**:
- Diagnose wird durchgefuehrt und Ergebnis angezeigt
- Kein Fehler aufgrund fehlender Pflanzen-Zuordnung
- Hinweis moeglich: "Diagnose wird nicht einer spezifischen Pflanze zugeordnet"

**Nachbedingungen**:
- Diagnose gespeichert ohne `plant_instance_key`

**Tags**: [req-029, diagnose, ohne-pflanzenzuordnung, allgemein, pflege-dashboard]

---

## 9. Identifikations-Historie

### TC-029-039: Identifikations-Historie aufrufen

**Requirement**: REQ-029 §3.7 `GET /history`, §4.1 "historyTitle"
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat in der Vergangenheit mindestens 3 Identifikationen durchgefuehrt (bestaetigt oder nicht)
- Nutzer navigiert zum Bereich "Letzte Identifikationen" (z.B. in Einstellungen oder Profilseite)

**Testschritte**:
1. Nutzer navigiert zur Identifikations-Historie

**Erwartete Ergebnisse**:
- Titel "Letzte Identifikationen" wird angezeigt
- Mindestens 3 Eintraege sind in der Liste sichtbar
- Jeder Eintrag zeigt: Datum/Uhrzeit, erkannter Pflanzenname, Konfidenz, Ergebnis-Status
- Eintraege sind chronologisch absteigend sortiert (neueste zuerst)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, historie, liste, chronologisch, letzte-identifikationen]

---

### TC-029-040: Identifikations-Historie ist leer (Erst-Nutzer)

**Requirement**: REQ-029 §3.7 `GET /history` — Leerzustand
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat noch keine Identifikation durchgefuehrt

**Testschritte**:
1. Nutzer navigiert zur Identifikations-Historie

**Erwartete Ergebnisse**:
- Ein Leer-Zustand wird angezeigt (kein Fehler)
- Moegliche Meldung: "Noch keine Identifikationen durchgefuehrt"
- Ein CTA "Jetzt Pflanze identifizieren" oder Kamera-Button ist sichtbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, historie, leer, empty-state]

---

### TC-029-041: Historie zeigt keine Bilddaten (Datenschutz)

**Requirement**: REQ-029 §5.2 — keine Bild-Persistenz, §3.5
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Mindestens 1 Identifikationseintrag in der Historie

**Testschritte**:
1. Nutzer oeffnet die Identifikations-Historie
2. Nutzer klickt auf einen Historieneintrag (sofern aufklappbar/Detail-Ansicht)

**Erwartete Ergebnisse**:
- Keine Vorschaubilder der hochgeladenen Originalfotos sind sichtbar
- Nur Metadaten: Datum, Pflanzenname, Konfidenz, Adapter-Name
- Referenzbilder vom Plant.id-Dienst koennen angezeigt werden (externe URLs), aber keine lokal gespeicherten Uploads

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, historie, datenschutz, keine-bilddaten, exif, metadaten-only]

---

## 10. Onboarding-Integration (REQ-020)

### TC-029-042: Optionaler Schritt 0 im Onboarding-Wizard erscheint wenn Feature aktiv

**Requirement**: REQ-029 §4.2 — Onboarding-Integration, §9 Szenario 9
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Plant.id API-Key ist konfiguriert
- Nutzer startet den Onboarding-Wizard (REQ-020) als Erstnutzer
- Nutzer hat Erfahrungsstufe "Beginner" oder "Intermediate"

**Testschritte**:
1. Nutzer navigiert zum Onboarding-Wizard (z.B. nach Registrierung oder manuell)

**Erwartete Ergebnisse**:
- Als erster optionaler Schritt erscheint "Pflanze fotografieren" (Schritt 0) vor der Kit-Auswahl
- Der Schritt hat einen "Ueberspringen"-Button
- Der Schritt hat einen "Pflanze fotografieren"-Button mit Kamera-Icon

**Nachbedingungen**:
- Onboarding-Wizard ist auf Schritt 0

**Tags**: [req-029, onboarding, schritt-0, wizard, optional, foto-aufnehmen]

---

### TC-029-043: Schritt 0 nicht sichtbar wenn Feature deaktiviert

**Requirement**: REQ-029 §4.2 — `identification_status.available == true` Bedingung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Kein API-Key konfiguriert (Feature deaktiviert)
- Nutzer startet Onboarding-Wizard

**Testschritte**:
1. Nutzer startet Onboarding-Wizard

**Erwartete Ergebnisse**:
- Schritt 0 "Pflanze fotografieren" erscheint NICHT
- Wizard beginnt direkt mit dem normalen ersten Schritt (z.B. Erfahrungsstufe oder Kit-Auswahl)

**Nachbedingungen**:
- Wizard laeuft normal

**Tags**: [req-029, onboarding, schritt-0, ausgeblendet, feature-deaktiviert]

---

### TC-029-044: Onboarding-Schritt 0 ueberspringen

**Requirement**: REQ-029 §9 Szenario 9 — "Ueberspringen"
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Feature aktiv, Onboarding-Wizard auf Schritt 0

**Testschritte**:
1. Nutzer klickt auf "Ueberspringen" oder "Weiter ohne Foto"

**Erwartete Ergebnisse**:
- Schritt 0 wird uebersprungen
- Wizard wechselt zum naechsten regulaeren Schritt
- Keine Fehlermeldung, keine Pflichtfeld-Validierung

**Nachbedingungen**:
- Wizard auf naechstem Schritt

**Tags**: [req-029, onboarding, ueberspringen, schritt-weiterleitung]

---

### TC-029-045: Onboarding-Foto-Identifikation fuehrt zu PlantInstance-Anlage im Wizard

**Requirement**: REQ-029 §4.2 — Onboarding-Flow nach Identifikation
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Feature aktiv, Consent noch nicht erteilt, Onboarding-Schritt 0
- Plant.id liefert "Ficus benjamina" als Top-Ergebnis mit Konfidenz 0.91
- Species "Ficus benjamina" existiert im System

**Testschritte**:
1. Nutzer klickt "Pflanze fotografieren" in Schritt 0
2. Consent-Dialog erscheint → Nutzer klickt "Aktivieren"
3. Identifikations-Dialog oeffnet sich → Nutzer laedt Foto hoch
4. "Ficus benjamina" erscheint als erstes Ergebnis
5. Nutzer klickt "Diese Pflanze anlegen"

**Erwartete Ergebnisse**:
- Identifikations-Dialog schliesst sich
- Im Onboarding-Wizard ist eine PlantInstance fuer "Ficus benjamina" vorausgewaehlt oder direkt angelegt
- CareProfile fuer die Pflanze wird (automatisch oder mit Nutzerbestaetigung) erstellt
- Wizard wechselt zum naechsten Schritt

**Nachbedingungen**:
- PlantInstance fuer "Ficus benjamina" im System angelegt
- CareProfile vorhanden

**Tags**: [req-029, onboarding, identifikation, plant-instance, care-profile, wizard-flow]

---

## 11. Integration in bestehende Seiten

### TC-029-046: FAB in Stammdaten-Uebersicht oeffnet Identifikations-Dialog

**Requirement**: REQ-029 §4.2 — Stammdaten-Uebersicht FAB
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Nutzer befindet sich auf der Stammdaten-Uebersicht (Pflanzen-Liste)

**Testschritte**:
1. Nutzer klickt auf den FAB "Pflanze per Foto hinzufuegen"

**Erwartete Ergebnisse**:
- `PlantIdentificationDialog` oeffnet sich (kein erneuter Consent-Dialog da bereits erteilt)
- Der Dialog zeigt Kamera/Upload-Optionen

**Nachbedingungen**:
- Dialog geoeffnet

**Tags**: [req-029, fab, stammdaten, uebersicht, dialog-oeffnen]

---

### TC-029-047: "Per Foto identifizieren"-Button in PlantInstance-Detail

**Requirement**: REQ-029 §4.2 — PlantInstance-Detail, Bedingung "Species noch nicht gesetzt"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Eine PlantInstance existiert OHNE zugeordnete Species (z.B. importierte Pflanze ohne Artbestimmung)
- Nutzer navigiert zur Detailseite dieser Pflanze

**Testschritte**:
1. Nutzer betrachtet die Detailseite der Pflanze
2. Nutzer klickt "Per Foto identifizieren" in der Toolbar

**Erwartete Ergebnisse**:
- `PlantIdentificationDialog` oeffnet sich
- Nach erfolgreicher Identifikation und Bestaetigung wird die erkannte Species der PlantInstance zugeordnet
- Die Detailseite aktualisiert sich und zeigt nun die zugeordnete Species

**Nachbedingungen**:
- PlantInstance hat eine Species-Zuordnung

**Tags**: [req-029, plant-instance, detail, per-foto-identifizieren, species-zuordnung]

---

### TC-029-048: "Per Foto identifizieren"-Button ausgeblendet wenn Species schon gesetzt

**Requirement**: REQ-029 §4.2 — Bedingung "Species noch nicht gesetzt"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Eine PlantInstance MIT zugeordneter Species existiert
- Nutzer navigiert zur Detailseite

**Testschritte**:
1. Nutzer betrachtet die Toolbar der PlantInstance-Detailseite

**Erwartete Ergebnisse**:
- Der Button "Per Foto identifizieren" ist NICHT sichtbar oder ist ausgegraut/disabled
- Andere Toolbar-Aktionen sind verfuegbar

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, plant-instance, detail, button-ausgeblendet, species-bereits-gesetzt]

---

### TC-029-049: Foto-Diagnose-Button im IPM-Inspektions-Dialog

**Requirement**: REQ-029 §4.2 — IPM-Inspektion (REQ-010), Bedingung `supports_health == true`
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Plant.id konfiguriert und Health Assessment verfuegbar
- Consent erteilt
- Nutzer hat den IPM-Inspektions-Dialog geoeffnet (REQ-010)

**Testschritte**:
1. Nutzer betrachtet den geoeffneten IPM-Inspektions-Dialog

**Erwartete Ergebnisse**:
- Ein Button "Foto-Diagnose" mit Kamera-Icon ist im Dialog sichtbar
- Klick oeffnet den Diagnose-Modus des `PlantIdentificationDialog`

**Nachbedingungen**:
- Diagnose-Dialog geoeffnet

**Tags**: [req-029, ipm, inspektion, foto-diagnose, integration]

---

### TC-029-050: Quick-Action "Pflanze krank?" im Pflege-Dashboard

**Requirement**: REQ-029 §4.2 — Pflege-Dashboard (REQ-022)
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt, Health Assessment verfuegbar
- Nutzer befindet sich auf dem Pflege-Dashboard (REQ-022)

**Testschritte**:
1. Nutzer klickt auf Quick-Action "Pflanze krank?" mit Kamera-Icon

**Erwartete Ergebnisse**:
- Diagnose-Dialog oeffnet sich
- Nutzer kann ein Foto hochladen

**Nachbedingungen**:
- Diagnose-Dialog geoeffnet

**Tags**: [req-029, pflege-dashboard, quick-action, pflanze-krank, diagnose]

---

## 12. Netzwerk- und API-Fehler

### TC-029-051: Netzwerkfehler waehrend Analyse

**Requirement**: REQ-029 §4.1 — Fehlerzustaende, §1 Grundprinzipien "Graceful Degradation"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Plant.id konfiguriert, Consent erteilt
- Nutzer hat ein Foto hochgeladen und Analyse gestartet
- Waehrend der Analyse tritt ein Netzwerkfehler auf (kein Internetzugang oder API nicht erreichbar)

**Testschritte**:
1. Nutzer laedt Bild hoch (Netzwerkfehler wird simuliert)

**Erwartete Ergebnisse**:
- Ladeindikator verschwindet
- Fehlermeldung erscheint, z.B. "Verbindung fehlgeschlagen. Bitte pruefen Sie Ihre Internetverbindung."
- Button "Erneut versuchen" oder "Manuell suchen" ist sichtbar
- Dialog bleibt offen und nutzbar

**Nachbedingungen**:
- Kein Identifikationsergebnis

**Tags**: [req-029, netzwerkfehler, graceful-degradation, retry, fehlermeldung]

---

### TC-029-052: API-Fehler (Plant.id nicht erreichbar) — Fallback auf ManualSuche

**Requirement**: REQ-029 §1 Grundprinzipien — "Graceful Degradation: Bei API-Ausfall manuelle Suche als Fallback"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Plant.id nicht erreichbar (Service-Ausfall)
- Kein PlantNet-Fallback konfiguriert

**Testschritte**:
1. Nutzer startet Analyse

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint
- Link "Manuell suchen" wird prominent angezeigt als Fallback-Option
- Kein Absturz oder weisser Bildschirm

**Nachbedingungen**:
- Manuelle Suche zugaenglich

**Tags**: [req-029, api-fehler, service-ausfall, fallback, manuelle-suche, graceful-degradation]

---

## 13. DSGVO und Datenschutz (sichtbare UI-Aspekte)

### TC-029-053: Datenschutzhinweis im Consent-Dialog erwaehnt EXIF-Stripping nicht

**Requirement**: REQ-029 §5.4 — EXIF-Stripping (technische Massnahme, kein UI-Element), §5.1 Consent-Text
**Priority**: Low
**Category**: Happy Path
**Preconditions**:
- Consent-Dialog ist geoeffnet (erster Klick auf Kamera-Button)

**Testschritte**:
1. Nutzer liest den Consent-Dialog-Text

**Erwartete Ergebnisse**:
- Der Text erwaehnt: "Das Bild wird dort nicht dauerhaft gespeichert."
- Der Text benennt den Dienstanbieter (Plant.id)
- Der Text gibt die Rechtsgrundlage an (Einwilligung)
- EXIF-Stripping muss nicht explizit erwaehnt werden (technische Massnahme), darf aber erwaehnt werden

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, consent-dialog, datenschutz, exif, hinweis]

---

### TC-029-054: Identifikations-Historie enthaelt keine Upload-Bilder (Datenschutz)

**Requirement**: REQ-029 §5.2 — Keine persistente Bild-Speicherung, Retention 90 Tage nur Metadaten
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Mindestens 3 Identifikationen in der Historie
- Nutzer oeffnet die Identifikations-Historie

**Testschritte**:
1. Nutzer durchsucht alle Eintraege in der Identifikations-Historie

**Erwartete Ergebnisse**:
- Kein Eintrag zeigt ein Vorschaubild des hochgeladenen Originalfotos
- Referenzbilder vom Plant.id-Dienst (externe URL) koennen vorhanden sein
- Jeder Eintrag zeigt nur: Pflanzenname, Datum, Konfidenz, Adapter-Name (Metadaten)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, datenschutz, historie, keine-bilder, metadaten, dsgvo]

---

## 14. PlantNet-Fallback Verhalten

### TC-029-055: Artbestimmung funktioniert mit PlantNet

**Requirement**: REQ-029 §3.3 — PlantNet Adapter (nur Artbestimmung)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nur `PLANTNET_API_KEY` konfiguriert (kein Plant.id)
- Consent erteilt

**Testschritte**:
1. Nutzer oeffnet Identifikations-Dialog und laedt ein Bild hoch

**Erwartete Ergebnisse**:
- Artbestimmungs-Ergebnisse werden angezeigt (vom PlantNet-Adapter)
- Keine Fehlermeldung
- Ergebnisse zeigen: Pflanzenname, Konfidenz, Referenzbild (soweit verfuegbar)

**Nachbedingungen**:
- Analyse via PlantNet abgeschlossen

**Tags**: [req-029, plantnet, artbestimmung, fallback, ergebnisse]

---

### TC-029-056: Diagnose-Funktion nicht verfuegbar mit PlantNet

**Requirement**: REQ-029 §3.3 — PlantNet: `diagnose()` wirft NotImplementedError, UI blendet Tab aus
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nur PlantNet konfiguriert (kein Plant.id)
- Consent erteilt, Dialog geoeffnet

**Testschritte**:
1. Nutzer sucht im Identifikations-Dialog nach einem Diagnose-Tab

**Erwartete Ergebnisse**:
- Kein Tab "Ist meine Pflanze krank?" oder "Pflanzen-Diagnose" ist sichtbar
- Keine Fehlermeldung bezueglich der fehlenden Diagnose-Funktion (einfach nicht vorhanden)

**Nachbedingungen**:
- Keine Aenderung

**Tags**: [req-029, plantnet, diagnose-nicht-verfuegbar, tab-ausgeblendet]

---

## 15. Vollstaendiger User-Journey-Test

### TC-029-057: End-to-End: Unbekannte Pflanze per Foto identifizieren und als PlantInstance anlegen

**Requirement**: REQ-029 §1.2 — Identifikations-Workflow (vollstaendiger Pfad)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plant.id konfiguriert
- Nutzer ist eingeloggt und Mitglied eines Tenants
- Consent `plant_identification` noch nicht erteilt
- Species "Epipremnum aureum" (Efeutute) existiert in den Stammdaten
- Testbild `efeutute.jpg` (1,8 MB JPEG) steht bereit

**Testschritte**:
1. Nutzer navigiert zur Stammdaten-Uebersicht
2. Nutzer klickt auf FAB "Pflanze per Foto hinzufuegen"
3. Consent-Dialog erscheint → Nutzer klickt "Aktivieren"
4. Identifikations-Dialog oeffnet sich → Nutzer laedt `efeutute.jpg` hoch
5. Ladeindikator erscheint mit "Pflanze wird analysiert..."
6. Ergebnis erscheint: "Epipremnum aureum" als erste Card mit Konfidenz >= 0.85
7. Nutzer klickt "Diese Pflanze anlegen"
8. PlantInstance-Erstellungsdialog oeffnet sich mit vorausgefuellter Species "Epipremnum aureum"
9. Nutzer fuellt Pflichtfeld "Name" aus (z.B. "Meine Efeutute")
10. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Schritt 3: Consent erteilt, Dialog oeffnet sich
- Schritt 5: Ladeindikator sichtbar
- Schritt 6: Ergebnis-Card korrekt befuellt
- Schritt 7: PlantInstance-Dialog vorausgefuellt
- Schritt 10: Snackbar "Pflanze gespeichert" erscheint
- Nutzer wird zur Stammdaten-Liste oder PlantInstance-Detailseite weitergeleitet
- "Meine Efeutute" erscheint in der Pflanzenliste mit Species "Epipremnum aureum"

**Nachbedingungen**:
- PlantInstance im System angelegt
- Consent gespeichert
- Identifikations-Request in der Historie

**Tags**: [req-029, end-to-end, journey, consent, upload, analyse, anlegen, happy-path]

---

### TC-029-058: End-to-End: Krankheitsdiagnose an bestehender Pflanze

**Requirement**: REQ-029 §1.3 — Krankheitsdiagnose-Workflow (vollstaendiger Pfad)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plant.id konfiguriert (Health Assessment verfuegbar)
- Consent `plant_identification` erteilt
- PlantInstance "meine_tomate_01" existiert im System
- Disease "Braunfaeule" (oder "Early Blight") existiert in IPM-Stammdaten
- Testbild `krankes_blatt.jpg` (befallenes Tomatenblatt) steht bereit

**Testschritte**:
1. Nutzer navigiert zur Detailseite von PlantInstance "meine_tomate_01"
2. Nutzer klickt auf "Foto-Diagnose" (sofern im IPM-Bereich) oder navigiert zum Pflege-Dashboard
3. Nutzer klickt "Pflanze krank?" Quick-Action
4. Diagnose-Dialog oeffnet sich → Nutzer laedt `krankes_blatt.jpg` hoch
5. Ladeindikator erscheint: "Gesundheit wird analysiert..."
6. Ergebnis erscheint: Erkannte Krankheit mit Konfidenz
7. Behandlungsvorschlaege werden angezeigt

**Erwartete Ergebnisse**:
- Schritt 5: Ladeindikator sichtbar
- Schritt 6: Krankheits-Card zeigt Krankheitsname, Schweregrad-Indikator, Konfidenz
- Schritt 7: Behandlungsvorschlaege aus lokalen IPM-Daten (falls Match) oder externe Hinweise
- Diagnose ist danach in der Identifikations-Historie sichtbar (als Diagnose-Eintrag)

**Nachbedingungen**:
- Diagnose-Request gespeichert (keine Bilddaten)

**Tags**: [req-029, end-to-end, diagnose, krankheit, ipm-match, behandlung, journey]

---

## Abdeckungsmatrix

| Spec-Abschnitt | Beschreibung | Testfaelle |
|----------------|-------------|-----------|
| §1.2 Identifikations-Workflow | Vollstaendiger Ablauf | TC-029-011, TC-029-057 |
| §1.3 Krankheitsdiagnose-Workflow | Diagnose-Ablauf | TC-029-034–TC-029-038, TC-029-058 |
| §3.5 IdentificationEngine (Validierung) | Bild-Validierung, Konfidenz-Schwellen | TC-029-013–TC-029-016, TC-029-025–TC-029-028 |
| §3.6 IdentificationService (Rate-Limit) | Rate-Limiting User/Global/Burst | TC-029-031–TC-029-033 |
| §3.7 REST-Endpunkte | /status, /identify, /diagnose, /confirm, /history | TC-029-001–TC-029-004, TC-029-039–TC-029-041 |
| §4.1 Identifikations-Dialog | Alle Dialog-Elemente und Fehlerzustaende | TC-029-010–TC-029-016, TC-029-027–TC-029-030 |
| §4.2 Integration in bestehende Seiten | Stammdaten, PlantInstance, IPM, Dashboard | TC-029-046–TC-029-050 |
| §4.3 Erfahrungsstufen | Beginner/Intermediate/Expert-Unterschiede | TC-029-017–TC-029-019, TC-029-022–TC-029-023 |
| §4.4 i18n-Keys | Deutsche Beschriftungen | Alle TC (Labels geprueft) |
| §5.1 Consent | Erst-Einwilligung, Widerruf | TC-029-005–TC-029-009 |
| §5.2 Datenverarbeitung | Keine Bild-Persistenz | TC-029-041, TC-029-054 |
| §5.4 EXIF-Stripping | Metadaten entfernt (proxy: Consent-Text) | TC-029-053 |
| §6.3 Feature-Toggle | Key konfiguriert/nicht konfiguriert | TC-029-001–TC-029-004 |
| §7 Auth & Rate-Limits | Rate-Limit-Fehlermeldungen | TC-029-031–TC-029-033 |
| §9 Szenario 1 (Species im System) | Happy Path Match | TC-029-020, TC-029-029 |
| §9 Szenario 2 (Species NICHT im System) | Neu-Anlege-Flow | TC-029-024 |
| §9 Szenario 3 (Niedrige Konfidenz) | Unsicherheits-Hinweis | TC-029-025 |
| §9 Szenario 4 (Kein Pflanzenmaterial) | is_plant = false | TC-029-027 |
| §9 Szenario 5 (Feature deaktiviert) | Buttons ausgeblendet | TC-029-001–TC-029-002 |
| §9 Szenario 6 (Rate-Limit) | 429-Fehlermeldung | TC-029-031 |
| §9 Szenario 7 (Diagnose + IPM-Match) | Behandlungsvorschlaege | TC-029-036 |
| §9 Szenario 8 (EXIF-Stripping) | Kein GPS uebertragen | TC-029-053 |
| §9 Szenario 9 (Onboarding + Foto) | Wizard Schritt 0 | TC-029-042–TC-029-045 |
| §9 Szenario 10 (Consent-Widerruf) | Toggle → Buttons weg | TC-029-008–TC-029-009 |
| PlantNet Fallback (§3.3) | Nur Artbestimmung, keine Diagnose | TC-029-004, TC-029-055–TC-029-056 |
| Netzwerkfehler / Graceful Degradation | Fehlerbehandlung | TC-029-051–TC-029-052 |
