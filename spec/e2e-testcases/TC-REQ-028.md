---
req_id: REQ-028
title: Mischkultur & Companion Planting
category: Pflanzenplanung
test_count: 42
coverage_areas:
  - CompanionPlantingPage (Stammdaten-Verwaltung der Beziehungen)
  - Artenauswahl-Dropdown (Spezies-Level Kompatibilitaetsanzeige)
  - Kompatible-Partner-Karte (compatible_with-Edges)
  - Inkompatible-Partner-Karte (incompatible_with-Edges)
  - Neue-Beziehung-Dialog (compatible und incompatible anlegen)
  - Ladeindikator und Leer-Zustaende
  - PlantingRun-Erstellung mit run_type mixed_culture
  - Mischkultur-Partner-Panel im PlantingRun-Create-Dialog
  - Quick-Add-Funktion fuer Partnerempfehlungen
  - Kompatibilitaets-Badge am Run-Header (COMPATIBLE / WARNING / INCOMPATIBLE)
  - Kompatibilitaets-Detail-Dialog
  - Familien-Level-Fallback-Badge (Transparenz)
  - Expertise-Level-Filter (Beginner Top-3 / Intermediate Top-5 / Expert alle)
  - Slot-Nachbarschafts-Warnung bei Beetplan-Slot-Zuweisung
  - Beetplan-Visualisierung (Kompatibilitaetslinien zwischen Slots)
  - Effekt-Typ-Icons und Score-Badges
  - Bidirektionale Edge-Darstellung
  - Fehlermeldungen und Validierungsmeldungen
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-028: Mischkultur & Companion Planting

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-028 Mischkultur & Companion Planting v1.0**,
ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder
Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht,
anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren
die deutschen i18n-Texte aus `companion.*`-Keys sowie `pages.companionPlanting.*`-Keys.

REQ-028 definiert zwei UI-Einstiegspunkte: (1) die **CompanionPlantingPage** unter Stammdaten fuer
die Verwaltung von Beziehungs-Edges (nur Platform-Admin), und (2) das **Mischkultur-Partner-Panel**
im PlantingRun-Create-Dialog und -Detail, das alle Mitglieder nutzen koennen.

---

## 1. CompanionPlantingPage — Seitenaufruf und Grundzustand

### TC-028-001: Seite "Mischkultur-Partner" ohne ausgewaehlte Spezies zeigt Leer-Zustand

**Requirement**: REQ-028 § 7 — UI-Integration, CompanionPlantingPage
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt (beliebige Rolle)
- Mindestens eine Species ist im System vorhanden
- Nutzer hat die Companion-Planting-Seite noch nicht benutzt (keine Auswahl)

**Testschritte**:
1. Nutzer navigiert zur Companion-Planting-Seite unter Stammdaten (z.B. via Seitenleiste oder URL `/stammdaten/companion-planting`)
2. Nutzer betrachtet die Seite, ohne im Artenauswahl-Dropdown eine Auswahl zu treffen

**Erwartete Ergebnisse**:
- Seitentitel "Mischkultur-Partner" ist sichtbar
- Ein Einfuehrungstext unter dem Titel beschreibt den Zweck der Seite
- Das Dropdown "Pflanzart auswaehlen" ist sichtbar und hat keinen ausgewaehlten Wert
- Unterhalb des Dropdowns erscheint der Leer-Zustand mit einer Illustrations-Grafik (Kami-Illustration) und dem Hinweistext zum Auswaehlen einer Pflanzart
- Die zwei Karten ("Vertraegliche Arten", "Unveraegliche Arten") sind noch NICHT sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, companion-planting-page, leer-zustand, stammdaten, initial-state]

---

### TC-028-002: Artenauswahl-Dropdown zeigt alle verfuegbaren Spezies

**Requirement**: REQ-028 § 7 — UI-Integration, CompanionPlantingPage
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist auf der Companion-Planting-Seite
- Im System sind mindestens 3 Spezies vorhanden (z.B. Solanum lycopersicum, Ocimum basilicum, Foeniculum vulgare)

**Testschritte**:
1. Nutzer klickt auf das Dropdown-Feld "Pflanzart auswaehlen"
2. Nutzer betrachtet die Liste der Optionen

**Erwartete Ergebnisse**:
- Das Dropdown oeffnet sich und zeigt eine Liste aller im System vorhandenen Spezies
- Jede Spezies wird mit ihrem wissenschaftlichen Namen (scientific_name) angezeigt
- Die Liste laesst sich scrollen wenn mehr Eintraege vorhanden sind

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-028, companion-planting-page, dropdown, species-list]

---

### TC-028-003: Auswahl einer Spezies laedt kompatible und inkompatible Partner

**Requirement**: REQ-028 § 7 — UI-Integration, CompanionPlantingPage; REQ-028 § 3.1
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist auf der Companion-Planting-Seite
- "Solanum lycopersicum" (Tomate) ist im System vorhanden
- Fuer Solanum lycopersicum existieren mindestens 2 kompatible Partner (z.B. Ocimum basilicum, Tagetes patula) und 2 inkompatible Partner (z.B. Foeniculum vulgare, Solanum tuberosum)

**Testschritte**:
1. Nutzer waehlt im Dropdown "Solanum lycopersicum" aus

**Erwartete Ergebnisse**:
- Kurz nach der Auswahl erscheint ein Lade-Indikator (Skeleton-Karte oder Spinner)
- Nach dem Laden erscheinen zwei nebeneinander angeordnete Karten:
  - Linke Karte: "Vertraegliche Arten" mit gruener Hintergrundfarbe und Haekchen-Icon, zeigt mindestens 2 Eintraege
  - Rechte Karte: "Unveraegliche Arten" mit roter Hintergrundfarbe und X-Icon, zeigt mindestens 2 Eintraege
- Jeder Eintrag in der kompatiblen Liste zeigt: wissenschaftlichen Namen + Score-Chip (z.B. "Score: 0.9")
- Jeder Eintrag in der inkompatiblen Liste zeigt: wissenschaftlichen Namen + Begruendung als Untertitel (z.B. "Allelopathische Hemmung durch Wurzelexsudate")
- Die Kopfzeilen der Karten zeigen je einen Zaehler-Chip mit der Anzahl der Eintraege

**Nachbedingungen**:
- Seite zeigt Daten fuer Solanum lycopersicum

**Tags**: [req-028, companion-planting-page, happy-path, kompatibel, inkompatibel, laden]

---

### TC-028-004: Kompatibilitaetsliste zeigt korrekten Score und kein Eintrag fuer nicht-beziehungslose Spezies

**Requirement**: REQ-028 § 6.2 — Seed-Daten, compatible_with-Edges
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- "Solanum lycopersicum" ist ausgewaehlt
- Seed-Daten sind geladen: Ocimum basilicum mit Score 0.9, Tagetes patula mit Score 0.85

**Testschritte**:
1. Nutzer betrachtet die "Vertraegliche Arten"-Karte nach Auswahl von Solanum lycopersicum

**Erwartete Ergebnisse**:
- "Ocimum basilicum" ist in der Liste sichtbar mit Chip "Score: 0.9"
- "Tagetes patula" ist in der Liste sichtbar mit Chip "Score: 0.85"
- Eine Spezies ohne jegliche compatible_with-Edge zu Solanum lycopersicum erscheint NICHT in der Liste
- Die Zaehler-Chip im Kartentitel stimmt mit der Anzahl der angezeigten Eintraege ueberein

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, companion-planting-page, score, seed-daten, kompatibel]

---

### TC-028-005: Inkompatibilitaetsliste zeigt Begruendung aus Seed-Daten

**Requirement**: REQ-028 § 6.3 — Seed-Daten, incompatible_with-Edges
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- "Solanum lycopersicum" ist ausgewaehlt
- Seed-Daten geladen: Foeniculum vulgare mit reason "Allelopathische Hemmung durch Wurzelexsudate", Solanum tuberosum mit reason "Gleiche Familie..."

**Testschritte**:
1. Nutzer betrachtet die "Unveraegliche Arten"-Karte nach Auswahl von Solanum lycopersicum

**Erwartete Ergebnisse**:
- "Foeniculum vulgare" erscheint in der Liste mit Untertitel "Allelopathische Hemmung durch Wurzelexsudate"
- "Solanum tuberosum" erscheint in der Liste mit Untertitel, der Phytophthora/Alternaria-Uebertragung erwaehnt
- Beide Eintraege zeigen den wissenschaftlichen Namen als Haupttext

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, companion-planting-page, inkompatibel, begruendung, seed-daten]

---

### TC-028-006: Spezies ohne jegliche Beziehungs-Edges zeigt beide Karten im Leer-Zustand

**Requirement**: REQ-028 § 7 — UI-Integration
**Priority**: Medium
**Category**: Leer-Zustand
**Vorbedingungen**:
- Eine Spezies "Testpflanze" ohne jegliche compatible_with- oder incompatible_with-Edges existiert im System

**Testschritte**:
1. Nutzer waehlt im Dropdown die Spezies "Testpflanze" aus

**Erwartete Ergebnisse**:
- Nach dem Laden zeigen beide Karten ("Vertraegliche Arten" und "Unveraegliche Arten") je eine Leer-Zustand-Darstellung mit Illustrations-Grafik und einem Hinweistext ("Keine vertraeglichen Arten vorhanden" bzw. "Keine unvertraeglichen Arten vorhanden")
- Die Karten-Zaehler-Chips sind entweder ausgeblendet oder zeigen "0"
- Die Seite setzt keinen Fehlerzustand ein; sie bleibt im Leer-Zustand

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, companion-planting-page, leer-zustand, keine-beziehungen]

---

### TC-028-007: Auswahl einer anderen Spezies aktualisiert beide Karten

**Requirement**: REQ-028 § 7 — UI-Integration
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- "Solanum lycopersicum" ist ausgewaehlt und die Karten sind geladen
- "Daucus carota" (Moehre) ist ebenfalls im System und hat andere Beziehungs-Edges

**Testschritte**:
1. Nutzer aendert die Dropdown-Auswahl von "Solanum lycopersicum" auf "Daucus carota"

**Erwartete Ergebnisse**:
- Die Karten werden neu geladen (Lade-Indikator kurz sichtbar)
- Nach dem Laden zeigen beide Karten die Beziehungs-Edges von Daucus carota
- Die vorherigen Eintraege von Solanum lycopersicum sind nicht mehr sichtbar
- Eintraege wie "Allium cepa" (Score 0.85) erscheinen in der vertraeglichen Liste (gemaess Seed-Daten)

**Nachbedingungen**:
- Seite zeigt Daten fuer Daucus carota

**Tags**: [req-028, companion-planting-page, zustandswechsel, spezies-wechsel]

---

## 2. Neue Beziehungen anlegen (Platform-Admin-Funktion)

### TC-028-008: "Vertraeglichen Partner hinzufuegen"-Button oeffnet Dialog

**Requirement**: REQ-028 § 5.1 — POST /companion-planting/compatible
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt (Platform-Admin-Rechte — nur Platform-Admin kann Edges anlegen)
- "Solanum lycopersicum" ist im Dropdown ausgewaehlt und Karten sind geladen

**Testschritte**:
1. Nutzer klickt auf den "Vertraeglichen Partner hinzufuegen"-Button (Plus-Icon) in der Kopfzeile der "Vertraegliche Arten"-Karte

**Erwartete Ergebnisse**:
- Ein Dialog oeffnet sich mit Titel "Vertraeglichen Partner hinzufuegen"
- Der Dialog enthaelt:
  - Einen Einfuehrungstext, der erklaert, was diese Aktion bewirkt
  - Ein Dropdown "Pflanzart auswaehlen" (Zielspezies), das alle Spezies AUSSER der aktuell ausgewaehlten (Solanum lycopersicum) anzeigt
  - Ein Zahlenfeld "Score" mit Standardwert 1 und Schrittgroesse 0.1
  - Buttons "Abbrechen" und "Erstellen"
- Der "Erstellen"-Button ist initial deaktiviert (keine Zielspezies ausgewaehlt)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, dialog, kompatibel-hinzufuegen, platform-admin]

---

### TC-028-009: Neue kompatible Beziehung erfolgreich anlegen

**Requirement**: REQ-028 § 5.1 — POST /companion-planting/compatible
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist Platform-Admin
- "Solanum lycopersicum" ist ausgewaehlt
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen
- "Petroselinum crispum" (Petersilie) ist im System vorhanden, aber noch NICHT als kompatibler Partner von Solanum lycopersicum eingetragen

**Testschritte**:
1. Nutzer waehlt im Dropdown des Dialogs "Petroselinum crispum" aus
2. Nutzer aendert den Score-Wert auf "0.7"
3. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Eine Erfolgs-Benachrichtigung erscheint (Snackbar oder Toast, z.B. "Erstellen")
- Die "Vertraegliche Arten"-Karte aktualisiert sich und zeigt "Petroselinum crispum" mit Chip "Score: 0.7" in der Liste

**Nachbedingungen**:
- compatible_with-Edge zwischen Solanum lycopersicum und Petroselinum crispum mit Score 0.7 ist angelegt

**Tags**: [req-028, kompatibel-hinzufuegen, happy-path, platform-admin, snackbar]

---

### TC-028-010: Neue kompatible Beziehung ohne Zielspezies — "Erstellen"-Button gesperrt

**Requirement**: REQ-028 § 7 — UI-Validierung
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen
- Im Dropdown ist keine Zielspezies ausgewaehlt

**Testschritte**:
1. Nutzer betrachtet den Dialog ohne eine Zielspezies im Dropdown ausgewaehlt zu haben
2. Nutzer versucht auf "Erstellen" zu klicken

**Erwartete Ergebnisse**:
- Der "Erstellen"-Button ist deaktiviert (disabled)
- Ein Klick auf den Button hat keinen Effekt
- Kein Dialog schliesst sich, kein Fehler wird angezeigt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, formvalidierung, button-deaktiviert, dialog]

---

### TC-028-011: "Unvertraeglichen Partner hinzufuegen"-Button oeffnet Dialog mit Begruendungsfeld

**Requirement**: REQ-028 § 5.1 — POST /companion-planting/incompatible
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist Platform-Admin
- "Daucus carota" ist ausgewaehlt und Karten sind geladen

**Testschritte**:
1. Nutzer klickt auf den "Unvertraeglichen Partner hinzufuegen"-Button (Plus-Icon) in der Kopfzeile der "Unveraegliche Arten"-Karte

**Erwartete Ergebnisse**:
- Ein Dialog oeffnet sich mit Titel "Unvertraeglichen Partner hinzufuegen"
- Der Dialog enthaelt:
  - Ein Dropdown "Pflanzart auswaehlen" (Zielspezies, ohne die aktuell ausgewaehlte)
  - Ein mehrzeiliges Textfeld "Begruendung" (textarea, 2 Zeilen)
  - Buttons "Abbrechen" und "Erstellen"
- Es gibt KEIN Score-Feld (nur bei kompatiblen Beziehungen relevant)
- Der "Erstellen"-Button ist initial deaktiviert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, dialog, inkompatibel-hinzufuegen, platform-admin, begruendungsfeld]

---

### TC-028-012: Neue inkompatible Beziehung erfolgreich anlegen

**Requirement**: REQ-028 § 5.1 — POST /companion-planting/incompatible
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist Platform-Admin
- "Daucus carota" ist ausgewaehlt
- Dialog "Unvertraeglichen Partner hinzufuegen" ist offen
- "Anethum graveolens" (Dill) ist im System vorhanden, aber noch NICHT als inkompatibel eingetragen

**Testschritte**:
1. Nutzer waehlt im Dropdown "Anethum graveolens" aus
2. Nutzer traegt im Begruendungsfeld ein: "Apiaceae-Selbstinkompatibilitaet, Kreuzbestaeubung moeglich"
3. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgs-Benachrichtigung erscheint (Snackbar)
- Die "Unveraegliche Arten"-Karte aktualisiert sich und zeigt "Anethum graveolens" mit Untertitel "Apiaceae-Selbstinkompatibilitaet, Kreuzbestaeubung moeglich"

**Nachbedingungen**:
- incompatible_with-Edge zwischen Daucus carota und Anethum graveolens ist angelegt

**Tags**: [req-028, inkompatibel-hinzufuegen, happy-path, platform-admin, snackbar]

---

### TC-028-013: Abbrechen-Button schliesst Dialog ohne Aenderungen

**Requirement**: REQ-028 § 7 — UI-Integration
**Priority**: Medium
**Category**: Dialog
**Vorbedingungen**:
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen
- Nutzer hat eine Zielspezies ausgewaehlt und einen Score eingetragen

**Testschritte**:
1. Nutzer klickt "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich sofort
- Die "Vertraegliche Arten"-Karte zeigt KEINE neuen Eintraege (Aktion wurde abgebrochen)
- Keine Benachrichtigung erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, dialog, abbrechen, kein-status-wechsel]

---

### TC-028-014: Aktuelle Spezies erscheint nicht in Zielspezies-Dropdown des Dialogs

**Requirement**: REQ-028 § 7 — UI-Integration (Selbstbeziehung verhindern)
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- "Solanum lycopersicum" ist ausgewaehlt
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen

**Testschritte**:
1. Nutzer klickt auf das Dropdown "Pflanzart auswaehlen" im Dialog
2. Nutzer sucht nach "Solanum lycopersicum" in der Dropdown-Liste

**Erwartete Ergebnisse**:
- "Solanum lycopersicum" erscheint NICHT in der Dropdown-Liste des Dialogs
- Alle anderen Spezies im System sind weiterhin waehbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, formvalidierung, selbstbeziehung, dialog, dropdown-filter]

---

## 3. PlantingRun mit mixed_culture — Erstellung und Mischkultur-Partner-Panel

### TC-028-015: PlantingRun-Create-Dialog zeigt Mischkultur-Partner-Panel nach Primary-Auswahl

**Requirement**: REQ-028 § 7.1 — Mischkultur-Partner-Panel im PlantingRun-Create-Dialog
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt (Mitglied eines Tenants)
- Der PlantingRun-Create-Dialog ist geoeffnet
- Im Feld "Typ" wurde "Mischkultur" (run_type = mixed_culture) ausgewaehlt
- Mindestens eine Spezies mit vorhandenen compatible_with-Edges ist im System (z.B. Solanum lycopersicum)

**Testschritte**:
1. Nutzer navigiert zum Pflanzdurchlauf-Bereich (z.B. `/t/{slug}/durchlaeufe`)
2. Nutzer klickt auf "Neuen Durchlauf erstellen"
3. Im Dialog waehlt Nutzer den Typ "Mischkultur"
4. Im ersten Entry-Feld waehlt Nutzer als Spezies "Solanum lycopersicum"

**Erwartete Ergebnisse**:
- Unterhalb der Primary-Spezies-Auswahl erscheint ein Panel "Mischkultur-Partner"
- Das Panel zeigt zwei Sektionen: "Empfohlene Partner" (gruen hinterlegt) und "Vermeiden" (rot hinterlegt)
- In "Empfohlene Partner" erscheinen mindestens 2 Empfehlungen (z.B. Ocimum basilicum, Tagetes patula)
- Jede Empfehlung zeigt: Pflanzenname (DE + wissenschaftlich), Score-Badge, Effekt-Icon, Kurzbeschreibung
- In "Vermeiden" erscheinen die inkompatiblen Spezies (z.B. Foeniculum vulgare)

**Nachbedingungen**:
- Kein Run erstellt, nur Dialog-Zustand

**Tags**: [req-028, planting-run, mixed-culture, mischkultur-panel, empfehlungen]

---

### TC-028-016: Quick-Add-Button fuegt Empfehlung als Entry mit vorgeschlagener Rolle hinzu

**Requirement**: REQ-028 § 7.1 — Quick-Add im Mischkultur-Partner-Panel; REQ-028 § 10 Szenario 7
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- PlantingRun-Create-Dialog ist offen mit Typ "Mischkultur"
- Solanum lycopersicum ist als Primary ausgewaehlt
- Das Mischkultur-Partner-Panel zeigt Ocimum basilicum als Empfehlung mit suggested_role "companion"

**Testschritte**:
1. Nutzer klickt auf den "Als Partner hinzufuegen"-Button bei Ocimum basilicum im Empfehlungs-Panel

**Erwartete Ergebnisse**:
- Im Entry-Bereich des Dialogs wird ein neuer Eintrag fuer Ocimum basilicum angelegt
- Die Rolle des neuen Eintrags ist auf "companion" vorbelegt
- Ocimum basilicum erscheint NICHT mehr in der Empfehlungsliste des Panels (da bereits hinzugefuegt)
- Der Panel aktualisiert sich entsprechend

**Nachbedingungen**:
- Ocimum basilicum ist als Entry mit Rolle "companion" im Formular vorhanden

**Tags**: [req-028, quick-add, mischkultur-panel, entry-rolle, planting-run]

---

### TC-028-017: Mischkultur-Partner-Panel zeigt Familien-Level-Badge bei Fallback-Empfehlungen

**Requirement**: REQ-028 § 3.1 — Familien-Level Fallback; REQ-028 § 7.1
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Eine Spezies "Capsicum annuum" ist ausgewaehlt als Primary
- Capsicum annuum hat KEINE direkten Spezies-Level compatible_with-Edges zu Phaseolus vulgaris
- Aber: family_compatible_with-Edge zwischen Solanaceae und Fabaceae mit Score 0.85 existiert

**Testschritte**:
1. Nutzer oeffnet PlantingRun-Create-Dialog mit Typ "Mischkultur"
2. Nutzer waehlt "Capsicum annuum" als Primary-Spezies im ersten Entry
3. Nutzer betrachtet das Mischkultur-Partner-Panel

**Erwartete Ergebnisse**:
- Im Panel erscheint Phaseolus vulgaris (oder andere Fabaceae-Spezies) als Empfehlung
- Der Score dieser Empfehlung liegt bei ca. 0.68 (0.85 × 0.8 Familien-Abschlag)
- Die Empfehlung traegt ein "Familien-Empfehlung"-Badge (Chip-Label gemaess i18n-Key `companion.badge.familyLevel`)
- Das Badge macht dem Nutzer transparent, dass dies eine Familien-Level-Inferenz ist

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, familien-fallback, badge, transparenz, score-abschlag, planting-run]

---

### TC-028-018: Mischkultur-Partner-Panel passt Anzeige nach Expertise-Level an — Beginner

**Requirement**: REQ-028 § 7.1 — Expertise-Level-Anpassung (REQ-021)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer hat Expertise-Level "Einsteiger" (Beginner) gesetzt
- PlantingRun-Create-Dialog ist offen mit Typ "Mischkultur"
- Solanum lycopersicum ist ausgewaehlt
- Im System existieren 6 kompatible Partner fuer Solanum lycopersicum

**Testschritte**:
1. Nutzer (mit Expertise-Level Einsteiger) betrachtet das Mischkultur-Partner-Panel nach Auswahl von Solanum lycopersicum

**Erwartete Ergebnisse**:
- Das Panel zeigt maximal 3 Empfehlungen ("Top-3")
- Die Beschreibungen verwenden vereinfachte Sprache
- Detaillierte Score-Werte, Match-Level und Quellen sind NICHT sichtbar
- Alle Warnungen ("Vermeiden"-Sektion) werden vollstaendig angezeigt
- Eine Angabe wie "Weitere Partner" oder "X weitere anzeigen" kann optional vorhanden sein

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, expertise-level, beginner, top-3, vereinfachte-sprache, req-021]

---

### TC-028-019: Mischkultur-Partner-Panel passt Anzeige nach Expertise-Level an — Intermediate

**Requirement**: REQ-028 § 7.1 — Expertise-Level-Anpassung (REQ-021)
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer hat Expertise-Level "Fortgeschritten" (Intermediate) gesetzt
- PlantingRun-Create-Dialog ist offen, Solanum lycopersicum ausgewaehlt
- Im System existieren 6 kompatible Partner

**Testschritte**:
1. Nutzer (Intermediate) betrachtet das Mischkultur-Partner-Panel

**Erwartete Ergebnisse**:
- Das Panel zeigt maximal 5 Empfehlungen ("Top-5")
- Effekt-Typ-Icons sind sichtbar (z.B. Schild-Icon fuer Schaedlingsabwehr)
- Effekt-Typ-Bezeichnung ist als Chip sichtbar (z.B. "Schaedlingsabwehr", "Wachstumsfoerderung")
- Score-Werte sind sichtbar
- Quellen sind noch NICHT sichtbar (erst bei Expert)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, expertise-level, intermediate, top-5, effekt-icon, req-021]

---

### TC-028-020: Mischkultur-Partner-Panel zeigt alle Details bei Expert-Level

**Requirement**: REQ-028 § 7.1 — Expertise-Level-Anpassung (REQ-021)
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer hat Expertise-Level "Experte" gesetzt
- PlantingRun-Create-Dialog ist offen, Solanum lycopersicum ausgewaehlt

**Testschritte**:
1. Nutzer (Expert) betrachtet das Mischkultur-Partner-Panel

**Erwartete Ergebnisse**:
- ALLE kompatiblen Partner werden angezeigt (nicht auf Top-3 oder Top-5 begrenzt)
- Score-Werte sind sichtbar
- Match-Level-Angabe ist sichtbar (z.B. "Spezies-Level" oder "Familien-Empfehlung")
- Quellenangabe (source) ist sichtbar, sofern vorhanden
- Effekt-Typ-Icons und Beschreibungen vollstaendig dargestellt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, expertise-level, expert, alle-empfehlungen, match-level, quelle, req-021]

---

### TC-028-021: Effekt-Typ-Sortierung im Mischkultur-Partner-Panel: pest_repellent vor general

**Requirement**: REQ-028 § 3.1 — Sortierung nach Effekt-Typ-Prioritaet
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- PlantingRun-Create-Dialog mit Typ "Mischkultur" offen
- Solanum lycopersicum ausgewaehlt
- Seed-Daten: Tagetes patula (pest_repellent, Score 0.85), Petroselinum crispum (general, Score 0.7), Ocimum basilicum (pest_repellent via growth_enhancer, Score 0.9)

**Testschritte**:
1. Nutzer (Expert-Level) betrachtet die sortierte Empfehlungsliste im Panel

**Erwartete Ergebnisse**:
- Die Empfehlungen sind nach Effekt-Typ-Prioritaet sortiert:
  - Zuerst erscheinen Eintraege mit pest_repellent (z.B. Ocimum basilicum mit Score 0.9, Tagetes patula mit Score 0.85)
  - Danach erscheinen Eintraege mit growth_enhancer, soil_improver etc.
  - Zuletzt erscheinen Eintraege mit general (z.B. Petroselinum crispum)
- Bei gleichem Effekt-Typ ist der hoeherer Score zuerst (Ocimum basilicum vor Tagetes patula wenn beide pest_repellent)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, effekt-typ-sortierung, prioritaet, pest-repellent, general, reihenfolge]

---

### TC-028-022: PlantingRun-Erstellung ohne Mischkultur-Panel wenn run_type = monoculture

**Requirement**: REQ-028 § 7.1 — Panel nur bei mixed_culture
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- PlantingRun-Create-Dialog ist offen

**Testschritte**:
1. Nutzer waehlt Typ "Monokultur" (monoculture)
2. Nutzer waehlt eine beliebige Spezies im Entry-Feld aus

**Erwartete Ergebnisse**:
- Das Mischkultur-Partner-Panel erscheint NICHT
- Der Dialog zeigt nur die Standard-Entry-Felder ohne Empfehlungs-Panel

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, monokultur, kein-panel, dialog]

---

## 4. Kompatibilitaets-Badge am Run-Header und Detail-Dialog

### TC-028-023: Run-Header zeigt gruenen Badge "Vertraeglich" bei COMPATIBLE-Status

**Requirement**: REQ-028 § 7.2 — Kompatibilitaets-Indikator im Run-Detail
**Priority**: Critical
**Category**: Detailansicht
**Vorbedingungen**:
- Ein PlantingRun vom Typ mixed_culture existiert mit den Entries: Solanum lycopersicum (primary) + Ocimum basilicum (companion) + Tagetes patula (trap_crop)
- Keine incompatible_with-Edges zwischen diesen drei Spezies

**Testschritte**:
1. Nutzer navigiert zur Detailseite des PlantingRuns
2. Nutzer betrachtet die Kopfzeile (Header) des Runs

**Erwartete Ergebnisse**:
- Im Run-Header ist ein farbiger Badge sichtbar
- Der Badge ist GRUEN und zeigt einen Text wie "Vertraeglich" oder "Alle Kombinationen vertraeglich" (gemaess i18n-Key `companion.validation.compatible`)
- Ein Tooltip am Badge zeigt eine Kurzfassung, z.B. "2 kompatible Paare, 0 inkompatible Paare"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, run-header, badge, gruen, compatible, tooltip]

---

### TC-028-024: Run-Header zeigt gelben Badge "Warnung" bei WARNING-Status

**Requirement**: REQ-028 § 7.2 — Kompatibilitaets-Indikator; REQ-028 § 10 Szenario 4
**Priority**: Critical
**Category**: Fehlermeldung
**Vorbedingungen**:
- Ein PlantingRun vom Typ mixed_culture existiert mit den Entries: Solanum lycopersicum (primary) + Foeniculum vulgare (companion)
- incompatible_with-Edge zwischen Solanum lycopersicum und Foeniculum vulgare vorhanden (severity: moderate)

**Testschritte**:
1. Nutzer navigiert zur Detailseite des PlantingRuns
2. Nutzer betrachtet den Header

**Erwartete Ergebnisse**:
- Der Badge im Run-Header ist GELB/ORANGE und zeigt Text wie "1 inkompatibles Paar" (gemaess i18n-Key `companion.validation.warning` mit count=1)
- Tooltip zeigt: "1 inkompatibles Paar gefunden"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, run-header, badge, gelb, warning, inkompatibel]

---

### TC-028-025: Klick auf Kompatibilitaets-Badge oeffnet Detail-Dialog mit Paarliste

**Requirement**: REQ-028 § 7.2 — Klick oeffnet Detail-Dialog
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Ein PlantingRun mit WARNING-Status ist vorhanden (Solanum lycopersicum + Foeniculum vulgare)
- Nutzer befindet sich auf der Run-Detailseite

**Testschritte**:
1. Nutzer klickt auf den gelben Kompatibilitaets-Badge im Run-Header

**Erwartete Ergebnisse**:
- Ein Detail-Dialog oeffnet sich
- Der Dialog listet alle Spezies-Paare im Run mit ihrem Status:
  - Solanum lycopersicum ↔ Foeniculum vulgare: Status "Unvertraeglich" (rot), Begruendung "Allelopathische Hemmung durch Wurzelexsudate"
- Der Dialog kann zusaetzlich Empfehlungen anzeigen, z.B. "Fenchel durch Petersilie ersetzen"
- Ein "Schliessen"-Button ist vorhanden

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-028, badge-klick, detail-dialog, paarliste, inkompatibel, begruendung]

---

### TC-028-026: Kompatibilitaets-Detail-Dialog zeigt unbekannte Paare als "Unbekannt"

**Requirement**: REQ-028 § 3.2 — Run-Kompatibilitaets-Validierung, unknown_pairs
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- PlantingRun mit Entries: Solanum lycopersicum + Ocimum basilicum + Tagetes patula
- Seed-Daten: Tomate-Basilikum = compatible, Tomate-Tagetes = compatible, aber Basilikum-Tagetes = kein Edge vorhanden
- Detail-Dialog ist geoeffnet

**Testschritte**:
1. Nutzer betrachtet den Kompatibilitaets-Detail-Dialog

**Erwartete Ergebnisse**:
- Paare mit bekanntem Status werden farbig dargestellt (gruen = kompatibel)
- Das Paar "Ocimum basilicum ↔ Tagetes patula" erscheint mit Status "Unbekannt" (grau)
- Der Gesamtstatus des Runs bleibt "COMPATIBLE" (da keine inkompatiblen Paare)
- Die Anzahl unbekannter Paare ist im Dialog sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, detail-dialog, unbekannt, unknown-pairs, grau]

---

## 5. Beetplan-Visualisierung und Slot-Nachbarschafts-Check

### TC-028-027: Kompatibilitaets-Linien zwischen Slots im Beetplan — gruen fuer kompatibel

**Requirement**: REQ-028 § 7.3 — Beetplan-Visualisierung
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Ein Beet (Bed) mit mindestens 2 Slots ist vorhanden (REQ-002)
- In Slot 1 steht Solanum lycopersicum, in Slot 2 (benachbart) steht Ocimum basilicum
- compatible_with-Edge zwischen Solanum lycopersicum und Ocimum basilicum mit Score 0.9 existiert

**Testschritte**:
1. Nutzer navigiert zur Beetplan-Seite (REQ-002) und oeffnet das entsprechende Beet
2. Nutzer betrachtet die visuelle Darstellung der benachbarten Slots

**Erwartete Ergebnisse**:
- Zwischen Slot 1 und Slot 2 erscheint eine GRUENE Linie (Kompatibilitaets-Indikator)
- Hover ueber die gruene Linie zeigt einen Tooltip mit: Score (0.9), Effekt-Typ ("Schaedlingsabwehr" oder "Wachstumsfoerderung"), Beschreibung

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, beetplan, gruen-linie, kompatibel, tooltip, req-002]

---

### TC-028-028: Kompatibilitaets-Linien im Beetplan — rot fuer inkompatibel

**Requirement**: REQ-028 § 7.3 — Beetplan-Visualisierung
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Beet mit Slot 3 (Solanum lycopersicum) und Slot 4 benachbart (Foeniculum vulgare)
- incompatible_with-Edge zwischen diesen Spezies vorhanden (severity: moderate)

**Testschritte**:
1. Nutzer betrachtet den Beetplan mit belegten Slots 3 und 4

**Erwartete Ergebnisse**:
- Zwischen Slot 3 und Slot 4 erscheint eine ROTE Linie
- Hover zeigt Tooltip: Begruendung "Allelopathische Hemmung durch Wurzelexsudate", Schweregrad "Unvertraeglich" (gemaess `companion.severity.moderate`)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, beetplan, rot-linie, inkompatibel, tooltip, severity, req-002]

---

### TC-028-029: Kompatibilitaets-Linien im Beetplan — grau fuer unbekannte Beziehung

**Requirement**: REQ-028 § 7.3 — Beetplan-Visualisierung
**Priority**: Low
**Category**: Detailansicht
**Vorbedingungen**:
- Beet mit zwei benachbarten Slots, in denen Spezies ohne gegenseitige Edge stehen

**Testschritte**:
1. Nutzer betrachtet den Beetplan mit zwei benachbarten Slots ohne bekannte Beziehung

**Erwartete Ergebnisse**:
- Zwischen den Slots erscheint eine GRAUE Linie (unbekannte Beziehung)
- Hover zeigt Tooltip: "Keine Informationen zur Vertraeglichkeit vorhanden" oder aehnlicher neutraler Text

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, beetplan, grau-linie, unbekannt, tooltip, req-002]

---

### TC-028-030: Slot-Zuweisung zeigt Warnung bei inkompatiblem Nachbar-Slot

**Requirement**: REQ-028 § 1.1 Szenario 4 — Nachbarschafts-Check; REQ-028 § 3.3
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- In Beet B befindet sich Solanum lycopersicum in Slot 3
- Slot 4 ist der benachbarte Slot und ist leer
- incompatible_with-Edge zwischen Solanum lycopersicum und Foeniculum vulgare vorhanden

**Testschritte**:
1. Nutzer navigiert zur Slot-Zuweisung fuer Slot 4
2. Nutzer waehlt "Foeniculum vulgare" als neue Pflanze fuer Slot 4

**Erwartete Ergebnisse**:
- Eine Warnmeldung erscheint (Hinweis-Box oder Validation-Message) mit Text wie: "Inkompatibel mit Tomate (Solanum lycopersicum) in Slot 3 — Allelopathie"
- Die Warnung verhindert NICHT zwingend das Speichern (es ist eine Warnung, kein Fehler), aber macht den Nutzer aufmerksam
- Der "Speichern"-Button bleibt aktiv (Warnung, kein harter Block)

**Nachbedingungen**:
- Warnung ist sichtbar, Nutzer kann trotzdem speichern

**Tags**: [req-028, slot-warnung, nachbarschaft, inkompatibel, warnung-nicht-blockierend]

---

## 6. Bidirektionale Beziehungen und Symmetrie-Tests

### TC-028-031: Empfehlung ist bidirektional — Ocimum basilicum zeigt Tomate als Partner

**Requirement**: REQ-028 § 2.1 — bidirectional: true, AQL ANY-Traversierung; REQ-028 § 10 Szenario 6
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- compatible_with-Edge: Solanum lycopersicum → Ocimum basilicum (Score 0.9, bidirectional: true)
- Es existiert KEINE Edge in Gegenrichtung (Ocimum basilicum → Solanum lycopersicum)

**Testschritte**:
1. Nutzer waehlt im Dropdown auf der CompanionPlantingPage "Ocimum basilicum"
2. Nutzer betrachtet die "Vertraegliche Arten"-Karte

**Erwartete Ergebnisse**:
- "Solanum lycopersicum" erscheint in der "Vertraegliche Arten"-Liste mit Chip "Score: 0.9"
- Die Beziehung wird trotz fehlender Rueck-Edge angezeigt (System traversiert ANY-Richtung)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, bidirektional, rueckrichtung, aql-any, symmetrie]

---

### TC-028-032: Bidirektionale Inkompatibilitaet ist in beiden Richtungen sichtbar

**Requirement**: REQ-028 § 2.1 — incompatible_with bidirectional: true
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- incompatible_with-Edge: Solanum lycopersicum → Foeniculum vulgare (bidirectional: true, severity: moderate)
- Keine Rueck-Edge vorhanden (Foeniculum vulgare → Solanum lycopersicum)

**Testschritte**:
1. Nutzer waehlt "Foeniculum vulgare" im Dropdown der CompanionPlantingPage
2. Nutzer betrachtet die "Unveraegliche Arten"-Karte

**Erwartete Ergebnisse**:
- "Solanum lycopersicum" erscheint in der "Unveraegliche Arten"-Liste
- Die Beziehung ist sichtbar, obwohl nur eine Edge-Richtung gespeichert ist

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, bidirektional, inkompatibel, rueckrichtung, symmetrie]

---

## 7. Edge Cases und Grenzwerte

### TC-028-033: Score-Wert am Grenzwert 0.0 — minimaler kompatibler Partner

**Requirement**: REQ-028 § 4.2 — compatibility_score: float (0.0–1.0)
**Priority**: Low
**Category**: Grenzwert
**Vorbedingungen**:
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen (Platform-Admin)
- Ein gueltig ausgewaehlter Partner ist vorhanden

**Testschritte**:
1. Nutzer setzt den Score-Wert auf "0" (Minimum)
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Die Edge wird erfolgreich angelegt (Score 0.0 ist gueltig)
- In der Liste erscheint der Partner mit Chip "Score: 0"
- Keine Validierungsfehlermeldung

**Nachbedingungen**:
- compatible_with-Edge mit Score 0.0 ist angelegt

**Tags**: [req-028, grenzwert, score-minimum, 0.0, formvalidierung]

---

### TC-028-034: Score-Wert ueber 1.0 — Validierungsfehler im Score-Feld

**Requirement**: REQ-028 § 4.2 — compatibility_score: float (ge=0.0, le=1.0)
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen
- Eine gueltige Zielspezies ist ausgewaehlt

**Testschritte**:
1. Nutzer gibt im Score-Feld den Wert "1.5" ein (oberhalb des Maximums)
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint am Score-Feld oder als Fehler-Benachrichtigung
- Der Dialog bleibt offen
- Keine Edge wird angelegt
- Der Score bleibt auf dem ungueltig eingegebenen Wert oder wird zurueckgesetzt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, grenzwert, score-maximum, validierungsfehler, formvalidierung]

---

### TC-028-035: Run mit nur einer Spezies — keine Paare, kein Badge

**Requirement**: REQ-028 § 3.2 — Run-Kompatibilitaets-Validierung, N×N/2 Paare
**Priority**: Low
**Category**: Edge Case
**Vorbedingungen**:
- Ein PlantingRun vom Typ mixed_culture mit nur EINER Entry-Spezies ist vorhanden (technisch unvollstaendig)

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Runs

**Erwartete Ergebnisse**:
- Der Kompatibilitaets-Badge zeigt entweder keinen Status oder einen neutralen Zustand
- Kein Absturz der Seite, kein JavaScript-Fehler
- Alternativ: Der Badge ist ausgeblendet da keine Paare vorhanden

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, edge-case, einzel-entry, kein-paar, badge-leer]

---

### TC-028-036: Sehr langer Begruendungstext wird korrekt dargestellt

**Requirement**: REQ-028 § 2.1 — reason: str (Freitext)
**Priority**: Low
**Category**: Edge Case
**Vorbedingungen**:
- Dialog "Unvertraeglichen Partner hinzufuegen" ist offen

**Testschritte**:
1. Nutzer gibt im Begruendungsfeld einen sehr langen Text ein (z.B. 300 Zeichen: "Foeniculum vulgare hemmt durch seine aetherischen Oele in Wurzelexsudaten und Blattoberflaechen fast alle Nachbarpflanzen erheblich, insbesondere Tomate, Paprika, Bohne und viele Kraeuter...")
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Die Edge wird erfolgreich angelegt
- In der "Unveraegliche Arten"-Liste wird der Text abgeschnitten dargestellt (mit "..." oder Zeilenumbruch)
- Kein Overflow oder Layout-Bruch in der Listenansicht

**Nachbedingungen**:
- incompatible_with-Edge mit langem reason-Text ist angelegt

**Tags**: [req-028, edge-case, langer-text, layout, overflow]

---

### TC-028-037: Run mit vielen Paaren — alle Paare im Detail-Dialog aufgelistet

**Requirement**: REQ-028 § 3.2 — N×N/2 Paare
**Priority**: Medium
**Category**: Listenansicht
**Vorbedingungen**:
- Ein mixed_culture-Run mit 5 Entries (5 verschiedene Spezies) existiert
- Anzahl Paare: 5×4/2 = 10 Paare

**Testschritte**:
1. Nutzer navigiert zur Run-Detailseite
2. Nutzer klickt auf den Kompatibilitaets-Badge

**Erwartete Ergebnisse**:
- Der Detail-Dialog listet alle 10 Spezies-Paare
- Jedes Paar zeigt Status (kompatibel/inkompatibel/unbekannt) und ggf. Score oder Begruendung
- Die Liste ist scrollbar bei vielen Eintraegen
- Kein Paarliste-Eintraege fehlt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, viele-paare, n-quadrat, detail-dialog, scrollbar]

---

## 8. Fehlerbehandlung und Netzwerkfehler

### TC-028-038: Netzwerkfehler beim Laden der Companion-Daten — Fehlermeldung sichtbar

**Requirement**: REQ-028 § 7 — Fehlerbehandlung (useApiError)
**Priority**: Medium
**Category**: Fehlermeldung
**Vorbedingungen**:
- Nutzer ist auf der CompanionPlantingPage
- Das Backend ist nicht erreichbar oder gibt einen Fehler zurueck

**Testschritte**:
1. Nutzer waehlt eine Spezies im Dropdown aus, waehrend das Backend nicht erreichbar ist

**Erwartete Ergebnisse**:
- Eine Fehler-Benachrichtigung erscheint (Snackbar oder Toast) mit einem Text wie "Netzwerkfehler..." oder "Serverfehler..."
- Die zwei Karten erscheinen in einem Leer-Zustand oder zeigen keine Daten
- Die Seite stuerzt nicht ab und bleibt bedienbar
- Der Nutzer kann eine andere Spezies auswaehlen und es erneut versuchen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, netzwerkfehler, fehlermeldung, snackbar, fehlerbehandlung]

---

### TC-028-039: Fehler beim Anlegen einer Beziehung — Dialog bleibt offen, Fehlermeldung erscheint

**Requirement**: REQ-028 § 7 — Fehlerbehandlung
**Priority**: Medium
**Category**: Fehlermeldung
**Vorbedingungen**:
- Dialog "Vertraeglichen Partner hinzufuegen" ist offen
- Zielspezies und Score sind ausgefuellt
- Das Backend gibt beim Speichern einen Fehler zurueck (z.B. Duplikat oder Serverfehler)

**Testschritte**:
1. Nutzer klickt "Erstellen"
2. Backend antwortet mit einem Fehler

**Erwartete Ergebnisse**:
- Eine Fehler-Benachrichtigung erscheint (Snackbar)
- Der Dialog bleibt offen (Nutzer kann Eingaben korrigieren)
- Die "Vertraegliche Arten"-Karte wird NICHT aktualisiert
- Kein neuer Eintrag erscheint in der Liste

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, fehler-beim-speichern, dialog-bleibt-offen, snackbar, backend-fehler]

---

## 9. Saison- und Standortfilter im Mischkultur-Partner-Panel

### TC-028-040: Standort-Filter in Empfehlungen — nur standortgeeignete Spezies erscheinen

**Requirement**: REQ-028 § 3.1 — Standort-/Saison-Filter (optional)
**Priority**: Medium
**Category**: Filterung
**Vorbedingungen**:
- PlantingRun-Create-Dialog ist offen mit Typ "Mischkultur"
- Einem Run ist ein Standort vom Typ "indoor" zugewiesen
- Solanum lycopersicum ist ausgewaehlt
- Tagetes patula (typisch outdoor) und Ocimum basilicum (indoor geeignet) sind beides kompatible Partner

**Testschritte**:
1. Nutzer betrachtet das Mischkultur-Partner-Panel bei einem Run mit indoor-Standort

**Erwartete Ergebnisse**:
- Das Panel zeigt bevorzugt oder ausschliesslich Partner, die fuer den Standorttyp "indoor" geeignet sind
- Wenn Tagetes patula als rein outdoor-Spezies markiert ist, erscheint sie entweder nicht oder mit einem Hinweis zur Standort-Inkompatibilitaet

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, standort-filter, indoor, outdoor, empfehlung-filterung]

---

## 10. i18n und Textpruefungen

### TC-028-041: Alle Effekt-Typ-Labels erscheinen auf Deutsch

**Requirement**: REQ-028 § 7.4 — i18n-Keys (`companion.effect.*`)
**Priority**: Medium
**Category**: i18n
**Vorbedingungen**:
- UI-Sprache ist Deutsch (Standard)
- Mischkultur-Partner-Panel ist sichtbar mit Empfehlungen aller Effekt-Typen

**Testschritte**:
1. Nutzer betrachtet das Panel im Intermediate- oder Expert-Modus
2. Nutzer prueft die Effekt-Typ-Labels

**Erwartete Ergebnisse**:
- `pest_repellent` wird als "Schaedlingsabwehr" angezeigt
- `growth_enhancer` wird als "Wachstumsfoerderung" angezeigt
- `soil_improver` wird als "Bodenverbesserung" angezeigt
- `nutrient_fixer` wird als "Stickstofffixierung" angezeigt
- `pollinator_attractor` wird als "Bestaeuberanlockung" angezeigt
- `space_optimizer` wird als "Raumoptimierung" angezeigt
- `general` wird als "Allgemein vertraeglich" angezeigt
- Kein Key-Identifier (z.B. "companion.effect.pest_repellent") ist im UI sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, i18n, effekt-typ, deutsch, label]

---

### TC-028-042: Schweregrad-Labels der Inkompatibilitaet erscheinen auf Deutsch

**Requirement**: REQ-028 § 7.4 — i18n-Keys (`companion.severity.*`)
**Priority**: Low
**Category**: i18n
**Vorbedingungen**:
- Kompatibilitaets-Detail-Dialog oder Beetplan-Tooltip ist sichtbar
- Mindestens eine incompatible_with-Edge mit allen drei Schweregraden vorhanden

**Testschritte**:
1. Nutzer betrachtet Inkompatibilitaets-Anzeige im Detail-Dialog oder Tooltip

**Erwartete Ergebnisse**:
- `mild` wird als "Suboptimal" angezeigt
- `moderate` wird als "Unvertraeglich" angezeigt
- `severe` wird als "Stark hemmend" angezeigt
- Kein technischer Enum-Wert ist direkt sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-028, i18n, schweregrad, severity, mild, moderate, severe, deutsch]

---

## Abdeckungs-Matrix

| Spec-Sektion | Beschreibung | Testfaelle |
|---|---|---|
| § 1.1 Szenarien | Business-Szenarien 1–5 | TC-028-003, TC-028-015, TC-028-016, TC-028-017, TC-028-023, TC-028-024, TC-028-030 |
| § 2.1 Edge Collections | compatible_with, incompatible_with, family_compatible_with, family_incompatible_with | TC-028-003, TC-028-004, TC-028-005, TC-028-031, TC-028-032 |
| § 2.2 allelopathy_score | Species-Attribut | TC-028-005 (implizit ueber Seed-Daten) |
| § 2.3 Effekt-Typen | 7 Effekt-Typen, Prioritaet | TC-028-021, TC-028-041 |
| § 2.4 Scoping | Globale Stammdaten | TC-028-001 (implizit) |
| § 3.1 Empfehlungs-Algorithmus | 4-Schritt, Spezies-Level + Familien-Fallback + Saison/Standort + Sortierung | TC-028-003, TC-028-017, TC-028-021, TC-028-040 |
| § 3.2 Run-Kompatibilitaets-Validierung | N×N/2 Paare, overall_status | TC-028-023, TC-028-024, TC-028-026, TC-028-037 |
| § 3.3 Slot-Nachbarschafts-Check | Adjacent-Slots, warnings[], benefits[] | TC-028-030 |
| § 5.1 Companion-Planting-Router | POST/DELETE compatible + incompatible | TC-028-009, TC-028-012 |
| § 5.2 PlantingRun-Integration | POST validate-compatibility | TC-028-023, TC-028-024, TC-028-025 |
| § 6.2 compatible_with Seed-Daten | 25 Paare aus plant-info Dokumenten | TC-028-004, TC-028-031 |
| § 6.3 incompatible_with Seed-Daten | 15 Paare | TC-028-005, TC-028-032 |
| § 6.4 Familien-Level Seed-Daten | 8+3 bidirektionale Familien-Paare | TC-028-017 |
| § 7.1 Mischkultur-Partner-Panel | Quick-Add, Expertise-Level, Familien-Badge | TC-028-015, TC-028-016, TC-028-017, TC-028-018, TC-028-019, TC-028-020, TC-028-022 |
| § 7.2 Kompatibilitaets-Badge | Run-Header gruen/gelb/rot, Detail-Dialog | TC-028-023, TC-028-024, TC-028-025, TC-028-026 |
| § 7.3 Beetplan-Visualisierung | Gruen/Rot/Grau Linien, Tooltip | TC-028-027, TC-028-028, TC-028-029, TC-028-030 |
| § 7.4 i18n-Keys | DE/EN Labels | TC-028-041, TC-028-042 |
| § 9 DoD (Akzeptanzkriterien) | UI-Pruefungen | TC-028-015 bis TC-028-020 |
| § 10 Testszenarien | GIVEN/WHEN/THEN Szenarien | TC-028-003, TC-028-017, TC-028-023, TC-028-024, TC-028-016, TC-028-031 |
| Grenzwerte & Edge Cases | Score 0.0/1.5, langer Text, Einzel-Entry | TC-028-033, TC-028-034, TC-028-035, TC-028-036, TC-028-037 |
| Fehlerbehandlung | Netzwerkfehler, Backend-Fehler | TC-028-038, TC-028-039 |
| Leer-Zustaende | Kein ausgewaehlt, Keine Beziehungen | TC-028-001, TC-028-006 |
| Formvalidierung | Selbstbeziehung, Button-Deaktivierung | TC-028-010, TC-028-014 |
