---
req_id: REQ-002
title: "Standortverwaltung — Räumliche Platzierung und Standort-Hierarchie"
category: Infrastruktur
test_count: 66
coverage_areas:
  - Site-Listenseite (SiteListPage)
  - Site-Erstellen-Dialog (SiteCreateDialog)
  - Site-Detailseite (SiteDetailPage)
  - Wasserquellen-Konfiguration (WaterSourceSection)
  - Wasseranalyse-Warnungen (Messalter, RO-Membran, GH-Plausibilität)
  - Location-Baum (LocationTreeSection)
  - Location-Erstellen-Dialog (LocationCreateDialog)
  - Location-Detailseite (LocationDetailPage)
  - Slot-Erstellen-Dialog (SlotCreateDialog)
  - Slot-Detailseite (SlotDetailPage)
  - LocationType-Stammdaten (CRUD)
  - Fruchtfolge-Validierung (CropRotationValidator)
  - Kaskadierendes Löschen
  - Lichtzeiten-Verwaltung
  - Properties-Vererbung
generated: 2026-03-21
updated: 2026-04-02
version: "4.2"
---

# TC-REQ-002: Standortverwaltung

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-002 Standortverwaltung v4.2**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

Die Standort-Hierarchie bildet das zentrale Rückgrat aller räumlichen Zuordnungen: **Site → Location (rekursiv) → Slot**. Testfälle decken den vollständigen CRUD-Zyklus aller drei Ebenen, die Wasserquellen-Konfiguration, die LocationType-Stammdaten, Fruchtfolge-Validierung sowie kaskadierendes Löschen ab.

---

## 1. Site — Listenseite

### TC-002-001: Site-Liste ist leer (Empty State)

**Requirement**: REQ-002 § 6 — Hierarchische Struktur (DoD)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und Mitglied eines Tenants
- Noch kein Site für diesen Tenant angelegt

**Testschritte**:
1. Nutzer navigiert zu `/standorte/sites`
2. Nutzer betrachtet den Seiteninhalt

**Erwartete Ergebnisse**:
- Die Seite zeigt den Titel "Standorte"
- Kein Tabelleneintrag ist sichtbar
- Ein "Empty State"-Hinweis oder leere Tabelle wird angezeigt
- Der Button "Standort erstellen" ist sichtbar und klickbar

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, listenansicht, empty-state]

---

### TC-002-002: Site-Liste zeigt vorhandene Sites als Akkordeon-Karten

**Requirement**: REQ-002 § 2 — Site-Properties (name, climate_zone, total_area_m2, timezone), § 6 — Hierarchische Struktur
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 2 Sites sind angelegt: "Zuhause" (Klimazone 8a, 50 m², Europe/Berlin) und "Gewächshaus" (Klimazone 9b, 120 m², UTC)

**Testschritte**:
1. Nutzer navigiert zu `/standorte/sites`
2. Nutzer betrachtet die Kartenliste

**Erwartete Ergebnisse**:
- Jeder Site wird als aufklappbare Karte (Card mit Collapse) angezeigt
- Karten-Header zeigt: Name, Klimazone, Gesamtfläche (m²), Anzahl Bereiche
- Klick auf den Karten-Header klappt den Inhalt auf/zu
- Aufgeklappter Inhalt zeigt den Location-Baum (SimpleTreeView) mit verschachtelten Bereichen
- Jeder Baumknoten zeigt: Icon (Typ), Name, Typ-Chip, Slot-/Pflanzenanzahl
- Button "Standort erstellen" ist sichtbar

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, listenansicht, akkordeon, karten]

---

### TC-002-003: Site-Liste — Suchfunktion filtert nach Name

**Requirement**: REQ-002 § 6 — LocationType-Dropdown (DoD)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- 3 Sites angelegt: "Zuhause", "Gewächshaus Süd", "Balkon Ost"

**Testschritte**:
1. Nutzer navigiert zu `/standorte/sites`
2. Nutzer gibt "Gewächs" in das Suchfeld "Tabelle durchsuchen..." ein
3. Nutzer wartet ca. 300 ms (Debounce)

**Erwartete Ergebnisse**:
- Tabelle zeigt nur Zeile "Gewächshaus Süd"
- "Zuhause" und "Balkon Ost" sind nicht mehr sichtbar
- Fußzeile zeigt "Zeigt 1–1 von 1 Einträgen"

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, listenansicht, suche, datatable]

---

### TC-002-004: Klick auf Site-Zeile navigiert zur Detailseite

**Requirement**: REQ-002 § 6 — Hierarchische Struktur (DoD)
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Site "Zuhause" (key=zuhause) ist angelegt

**Testschritte**:
1. Nutzer navigiert zu `/standorte/sites`
2. Nutzer klickt auf die Zeile "Zuhause" in der Tabelle

**Erwartete Ergebnisse**:
- Browser navigiert zu `/standorte/sites/zuhause`
- Site-Detailseite lädt mit Titel "Zuhause"
- Formularfelder "Name", "Klimazone", "Gesamtfläche (m²)", "Zeitzone" sind mit den Site-Daten befüllt

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, navigation, detailseite]

---

## 2. Site — Erstellen

### TC-002-005: Site erfolgreich erstellen (Happy Path)

**Requirement**: REQ-002 § 6 — Hierarchische Struktur: Site implementiert (DoD)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt und Tenant-Mitglied
- Nutzer befindet sich auf `/standorte/sites`

**Testschritte**:
1. Nutzer klickt auf "Standort erstellen"
2. Dialog "Standort erstellen" öffnet sich
3. Nutzer gibt im Feld "Name" den Text "Mein Garten" ein
4. Nutzer gibt im Feld "Klimazone" den Text "8a" ein
5. Nutzer gibt im Feld "Gesamtfläche (m²)" den Wert `50` ein
6. Nutzer gibt im Feld "Zeitzone" den Text "Europe/Berlin" ein
7. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint mit Meldung (entspricht `common.create`)
- Tabelle in der Listenseite enthält nun die neue Zeile "Mein Garten"

**Nachbedingungen**:
- Site "Mein Garten" ist in der Datenbank gespeichert

**Tags**: [REQ-002, site, erstellen, happy-path]

---

### TC-002-006: Site erstellen — Pflichtfeld "Name" leer gelassen

**Requirement**: REQ-002 § 3 — Datenvalidierung: name min_length=1
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- Dialog "Standort erstellen" ist geöffnet

**Testschritte**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer gibt im Feld "Klimazone" "8a" ein
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich nicht
- Feld "Name" zeigt eine Inline-Validierungsfehlermeldung
- Kein Snackbar erscheint

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, site, formvalidierung, pflichtfeld]

---

### TC-002-007: Site erstellen — Abbrechen schließt Dialog ohne Speichern

**Requirement**: REQ-002 § 6 — Hierarchische Struktur (DoD)
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt
- Dialog "Standort erstellen" ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Name" "Testsite" ein
2. Nutzer klickt auf "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Kein Snackbar erscheint
- Tabelle enthält keinen Eintrag "Testsite"

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, dialog, abbrechen]

---

### TC-002-008: Site erstellen mit WaterSource — has_ro_system aktivieren zeigt RO-Profil

**Requirement**: REQ-002 § 1 — WaterSource-Konfiguration: has_ro_system Toggle
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt
- Dialog "Standort erstellen" ist geöffnet
- Erfahrungsstufe ist "Fortgeschritten" oder "Experte" (oder "Alle Felder anzeigen" ist aktiv)

**Testschritte**:
1. Nutzer scrollt zum Abschnitt "Wasserquelle" im Dialog
2. Nutzer sieht den Toggle "Osmoseanlage vorhanden" — dieser ist deaktiviert
3. Nutzer aktiviert den Toggle "Osmoseanlage vorhanden"

**Erwartete Ergebnisse**:
- Der Abschnitt "Osmosewasser-Profil" wird eingeblendet
- Felder "EC (mS/cm)" (RO) und "pH-Wert" (RO) sind sichtbar
- Vor der Aktivierung war der RO-Profil-Abschnitt nicht sichtbar

**Nachbedingungen**:
- Keine Daten gespeichert (Dialog noch offen)

**Tags**: [REQ-002, site, wasserquelle, ro-system, toggle, REQ-021]

---

### TC-002-009: Site erstellen mit vollständigem Leitungswasser-Profil

**Requirement**: REQ-002 § 2 — TapWaterProfile: 8 Wasserparameter
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Dialog "Standort erstellen" ist geöffnet
- Abschnitt "Wasserquelle" ist sichtbar

**Testschritte**:
1. Nutzer gibt im Feld "Name" "Teststite Wasser" ein
2. Nutzer füllt im Abschnitt "Leitungswasser-Profil" aus:
   - EC (mS/cm): `0.5`
   - pH-Wert: `7.2`
   - Alkalinität (ppm CaCO₃): `120`
   - Gesamthärte (ppm CaCO₃): `180`
   - Calcium (ppm): `50`
   - Magnesium (ppm): `15`
   - Chlor (ppm): `0.3`
   - Chloramin (ppm): `0.0`
   - Messdatum: heutiges Datum
   - Quelle / Bemerkung: "Stadtwerke München Jahresanalyse 2025"
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- Site in der Liste sichtbar

**Nachbedingungen**:
- Site mit vollständigem Leitungswasser-Profil gespeichert

**Tags**: [REQ-002, site, wasserquelle, leitungswasser-profil, happy-path]

---

## 3. Site — Detailseite bearbeiten

### TC-002-010: Site-Daten bearbeiten und speichern

**Requirement**: REQ-002 § 6 — Hierarchische Struktur (DoD)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Site "Zuhause" (key=zuhause) ist angelegt
- Nutzer befindet sich auf `/standorte/sites/zuhause`

**Testschritte**:
1. Nutzer leert das Feld "Name" und tippt "Zuhause Aktualisiert"
2. Nutzer leert das Feld "Klimazone" und tippt "9a"
3. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgs-Snackbar erscheint mit Meldung (entspricht `common.save`)
- Seitentitel aktualisiert sich auf "Zuhause Aktualisiert"
- Formularfelder zeigen die aktualisierten Werte

**Nachbedingungen**:
- Site-Daten sind aktualisiert gespeichert

**Tags**: [REQ-002, site, bearbeiten, happy-path]

---

### TC-002-011: UnsavedChangesGuard verhindert unbeabsichtigtes Wegnavigieren

**Requirement**: REQ-002 § 6 — Hierarchische Struktur (DoD)
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Site-Detailseite `/standorte/sites/zuhause` ist geöffnet

**Testschritte**:
1. Nutzer ändert den Wert im Feld "Name" auf "Geänderter Name" (Formular ist jetzt dirty)
2. Nutzer klickt in der Seitennavigation auf einen anderen Menüpunkt (z. B. "Stammdaten")

**Erwartete Ergebnisse**:
- Ein Browser-Bestätigungsdialog erscheint mit der Meldung "Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Bei Klick auf "Abbrechen" bleibt der Nutzer auf der Site-Detailseite, Änderungen bleiben erhalten
- Bei Klick auf "OK" verlässt der Nutzer die Seite, Änderungen werden verworfen

**Nachbedingungen**:
- Abhängig von Nutzerentscheidung

**Tags**: [REQ-002, site, unsaved-changes-guard, navigation]

---

### TC-002-012: Site löschen mit Bestätigungsdialog

**Requirement**: REQ-002 § 6 — Kaskadierendes Löschen (DoD)
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt als Admin des Tenants
- Site "Leere Site" ohne Kind-Locations ist angelegt
- Nutzer ist auf der Detailseite dieser Site

**Testschritte**:
1. Nutzer klickt auf den "Löschen"-Button (rote Schaltfläche oben rechts)
2. ConfirmDialog öffnet sich mit Bestätigungstext
3. Nutzer klickt auf "Löschen" im Dialog

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Browser navigiert zurück zu `/standorte/sites`
- Erfolgs-Snackbar erscheint (entspricht `common.delete`)
- Site "Leere Site" erscheint nicht mehr in der Liste

**Nachbedingungen**:
- Site ist gelöscht

**Tags**: [REQ-002, site, löschen, confirm-dialog, admin]

---

### TC-002-013: Site löschen — Abbrechen im Bestätigungsdialog bewahrt Daten

**Requirement**: REQ-002 § 6 — Kaskadierendes Löschen (DoD)
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt
- Site-Detailseite ist geöffnet

**Testschritte**:
1. Nutzer klickt auf den "Löschen"-Button
2. ConfirmDialog öffnet sich
3. Nutzer klickt auf "Abbrechen" im Dialog

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Nutzer bleibt auf der Site-Detailseite
- Kein Snackbar erscheint
- Site ist weiterhin vorhanden

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, löschen, abbrechen, confirm-dialog]

---

## 4. Wasserquellen-Konfiguration

### TC-002-014: GH-Plausibilitäts-Warnung bei stark abweichendem GH-Wert

**Requirement**: REQ-002 § 2 — Validierungsregeln: GH-Plausibilitäts-Check >30% Abweichung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf der Site-Detailseite oder im Erstellen-Dialog
- Abschnitt "Leitungswasser-Profil" ist sichtbar

**Testschritte**:
1. Nutzer gibt im Feld "Calcium (ppm)" den Wert `50` ein
   (Berechnet: Ca * 2.497 = 124.85 ppm)
2. Nutzer gibt im Feld "Magnesium (ppm)" den Wert `15` ein
   (Berechnet: Mg * 4.116 = 61.74 ppm; Gesamt = 186.59 ppm)
3. Nutzer gibt im Feld "Gesamthärte (ppm CaCO₃)" den Wert `80` ein
   (Abweichung >30% von 186.59 ppm)

**Erwartete Ergebnisse**:
- Eine Soft-Warnung erscheint in der Nähe des GH-Felds: "Gesamthärte weicht von Ca/Mg-Werten ab"
- Das Formular kann trotzdem gespeichert werden (kein Hardblock)

**Nachbedingungen**:
- Daten können gespeichert werden

**Tags**: [REQ-002, wasserquelle, gh-plausibilität, soft-warnung, formvalidierung]

---

### TC-002-015: GH-Plausibilitäts-Warnung erscheint nicht bei konsistenten Werten

**Requirement**: REQ-002 § 2 — Validierungsregeln: GH-Plausibilitäts-Check
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Site-Detailseite
- Abschnitt "Leitungswasser-Profil" ist sichtbar

**Testschritte**:
1. Nutzer gibt im Feld "Calcium (ppm)" den Wert `50` ein
2. Nutzer gibt im Feld "Magnesium (ppm)" den Wert `15` ein
3. Nutzer gibt im Feld "Gesamthärte (ppm CaCO₃)" den Wert `187` ein
   (Konsistent mit Ca*2.497 + Mg*4.116 = 186.59 ppm, <30% Abweichung)

**Erwartete Ergebnisse**:
- Keine GH-Plausibilitäts-Warnung erscheint

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, wasserquelle, gh-plausibilität, no-warning]

---

### TC-002-016: Messalter-Warnung bei über 12 Monate altem Messdatum

**Requirement**: REQ-002 § 2 — Validierungsregeln: Messalter-Warnung >12 Monate
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist auf der Site-Detailseite
- Site hat ein Leitungswasser-Profil mit `measurement_date` älter als 12 Monate (z. B. 2024-01-01)

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite
2. Nutzer betrachtet den Abschnitt "Wasserquelle"

**Erwartete Ergebnisse**:
- Eine Soft-Warnung wird angezeigt: "Wassermessung ist älter als 12 Monate"
- Das Formular ist weiterhin editierbar und speicherbar

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, wasserquelle, messalter, soft-warnung]

---

### TC-002-017: RO-Membran-Warnung bei ec_ms > 0.05 mS

**Requirement**: REQ-002 § 2 — Validierungsregeln: RO-Membran-Warnung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist auf der Site-Detailseite
- "Osmoseanlage vorhanden" ist aktiviert
- RO-Profil-Felder sind sichtbar

**Testschritte**:
1. Nutzer gibt im RO-Profil-Feld "EC (mS/cm)" den Wert `0.08` ein
   (>0.05 mS/cm — Membranverschleiß-Schwelle überschritten)

**Erwartete Ergebnisse**:
- Eine Soft-Warnung erscheint: "RO-Membran möglicherweise verschlissen (EC zu hoch)"
- Das Formular kann trotzdem gespeichert werden

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, wasserquelle, ro-membran, soft-warnung]

---

### TC-002-018: RO-Membran-Warnung erscheint nicht bei ec_ms ≤ 0.05 mS

**Requirement**: REQ-002 § 2 — Validierungsregeln: RO-Membran-Warnung
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist auf der Site-Detailseite
- "Osmoseanlage vorhanden" ist aktiviert

**Testschritte**:
1. Nutzer gibt im RO-Profil-Feld "EC (mS/cm)" den Wert `0.03` ein
   (≤0.05 mS/cm — kein Membranverschleiß)

**Erwartete Ergebnisse**:
- Keine RO-Membran-Warnung wird angezeigt

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, wasserquelle, ro-membran, no-warning]

---

### TC-002-019: WaterSource-Validierung — EC-Grenzwerte (0 bis 2.0 mS/cm)

**Requirement**: REQ-002 § 2 — TapWaterProfile: ec_ms (ge=0, le=2.0)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Site-Detailseite
- Feld "EC (mS/cm)" im Leitungswasser-Profil ist sichtbar

**Testschritte**:
1. Nutzer gibt im Feld "EC (mS/cm)" den Wert `2.5` ein (Grenzwert überschritten)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Das Formular wird nicht gespeichert oder eine Fehlermeldung/Warnung erscheint am Feld
- Kein Erfolgs-Snackbar

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, wasserquelle, grenzwert, ec, formvalidierung]

---

### TC-002-020: has_ro_system deaktiviert — RO-Profil-Sektion ausgeblendet

**Requirement**: REQ-002 § 2 — WaterSource: RO-Profil wird ignoriert wenn has_ro_system=false
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf der Site-Detailseite
- "Osmoseanlage vorhanden" ist deaktiviert

**Testschritte**:
1. Nutzer betrachtet den Abschnitt "Wasserquelle"

**Erwartete Ergebnisse**:
- Der Bereich "Osmosewasser-Profil" ist nicht sichtbar
- Nur das Leitungswasser-Profil wird angezeigt

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, wasserquelle, ro-system, toggle, sichtbarkeit]

---

## 5. Location-Baum (LocationTreeSection)

### TC-002-021: Location-Baum zeigt Site-Kinder in Baumstruktur

**Requirement**: REQ-002 § 6 — Standort-Baum: Vollständiger Baum per Traversal ladbar (DoD)
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf Site-Detailseite "Zuhause"
- Site "Zuhause" hat 2 direkte Kind-Locations: "Garten" (Typ=Garten) und "Haus" (Typ=Gebäude)
- "Haus" hat Kind-Location "Arbeitszimmer" (Typ=Zimmer)
- "Arbeitszimmer" hat Kind-Location "Grow Zelt 1" (Typ=Grow-Zelt)

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite `/standorte/sites/zuhause`
2. Nutzer scrollt zum Abschnitt "Bereiche"
3. Nutzer betrachtet den Standort-Baum (MUI SimpleTreeView)

**Erwartete Ergebnisse**:
- Der Baum zeigt "Garten" und "Haus" als Wurzelknoten
- Der Knoten "Haus" ist aufklappbar und zeigt "Arbeitszimmer" als Kind
- "Arbeitszimmer" zeigt "Grow Zelt 1" als Kind
- Jeder Knoten zeigt das korrekte Typ-Icon (Park für Garten, Home für Gebäude, MeetingRoom für Zimmer, Campaign für Grow-Zelt)

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location-baum, hierarchie, baumansicht]

---

### TC-002-022: Klick auf Location-Knoten navigiert zur Location-Detailseite

**Requirement**: REQ-002 § 6 — Navigation (DoD)
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf Site-Detailseite
- Location "Garten" (key=garten) ist im Baum sichtbar

**Testschritte**:
1. Nutzer klickt auf den Knoten "Garten" im Location-Baum

**Erwartete Ergebnisse**:
- Browser navigiert zur Location-Detailseite `/standorte/locations/garten`
- Location-Detailseite lädt mit Titel "Garten"

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, navigation, detailseite]

---

### TC-002-023: "Bereich hinzufügen"-Button öffnet LocationCreateDialog

**Requirement**: REQ-002 § 6 — Hierarchische Struktur (DoD)
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf Site-Detailseite "Zuhause"
- Location-Baum-Abschnitt ist sichtbar

**Testschritte**:
1. Nutzer klickt auf den "Bereich erstellen"-Button im Abschnitt "Bereiche"

**Erwartete Ergebnisse**:
- Dialog "Bereich erstellen" öffnet sich
- Formularfelder sind: "Name", "Standort-Typ" (Dropdown), "Fläche (m²)", "Beleuchtung", "Bewässerungssystem", "Licht Ein", "Licht Aus", "Dynamische Sonnenstandberechnung"

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, erstellen, dialog]

---

### TC-002-024: Kind-Location zu bestehender Location hinzufügen

**Requirement**: REQ-002 § 2 — Location: parent_location_key, rekursive Verschachtelung
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf Location-Detailseite "Haus"
- Location "Haus" (depth=0) existiert

**Testschritte**:
1. Nutzer klickt auf "Unterlocation hinzufügen"-Button auf der Location-Detailseite
2. Dialog öffnet sich mit Kontext-Vorbelegung (parent_location_key = "haus")
3. Nutzer gibt im Feld "Name" "Arbeitszimmer" ein
4. Nutzer wählt im Dropdown "Standort-Typ" den Wert "Zimmer"
5. Nutzer gibt "Fläche (m²)" = `20` ein
6. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- Location-Baum auf der Eltern-Detailseite aktualisiert sich und zeigt "Arbeitszimmer" als neues Kind

**Nachbedingungen**:
- Location "Arbeitszimmer" ist als Kind von "Haus" gespeichert, depth=1

**Tags**: [REQ-002, location, unterlocation, hierarchie, happy-path]

---

## 6. Location — Erstellen

### TC-002-025: Location erstellen — Pflichtfeld "Name" leer gelassen

**Requirement**: REQ-002 § 3 — LocationDefinition: name min_length=1
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- LocationCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer wählt "Standort-Typ" aus
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich nicht
- Feld "Name" zeigt Inline-Validierungsfehlermeldung
- Kein Snackbar erscheint

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, location, formvalidierung, pflichtfeld]

---

### TC-002-026: Standort-Typ-Dropdown zeigt alle verfügbaren Typen (sortiert)

**Requirement**: REQ-002 § 6 — LocationType-Dropdown: alle Typen sortiert nach sort_order (DoD)
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt
- LocationCreateDialog ist geöffnet
- 10 System-Seed-Typen sind installiert

**Testschritte**:
1. Nutzer klickt auf das Dropdown-Feld "Standort-Typ"

**Erwartete Ergebnisse**:
- Dropdown zeigt mindestens folgende Einträge in dieser Reihenfolge:
  1. Garten
  2. Gewächshaus
  3. Gebäude
  4. Zimmer
  5. Balkon
  6. Terrasse
  7. Grow-Zelt
  8. Beet
  9. Regal
  10. Topf-/Container-Gruppe
- Nutzerdefinierte Typen erscheinen zusätzlich (nach sort_order)

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, standort-typ, dropdown, sort_order]

---

### TC-002-027: Lichtzeiten-Felder nur bei Kunstlicht-Typ sichtbar

**Requirement**: REQ-002 § 2 — Lichtzeiten-Verwaltung: led/hps/cmh → lights_on/lights_off setzen
**Priority**: High
**Category**: Dialog
**Preconditions**:
- LocationCreateDialog ist geöffnet
- Feld "Beleuchtung" ist sichtbar

**Testschritte**:
1. Nutzer wählt im Dropdown "Beleuchtung" den Wert "LED" aus
2. Nutzer betrachtet die Felder "Licht Ein" und "Licht Aus"

**Erwartete Ergebnisse**:
- Felder "Licht Ein" und "Licht Aus" sind sichtbar und editierbar

**Nachbedingungen**:
- Keine Daten verändert

**Siehe auch**: TC-002-028 (Toggle bei natural)

**Tags**: [REQ-002, location, lichtzeiten, kunstlicht, felder-sichtbarkeit]

---

### TC-002-028: Toggle "Dynamische Sonnenstandberechnung" nur bei natural/mixed sichtbar

**Requirement**: REQ-002 § 2 — Lichtzeiten: use_dynamic_sunrise für natural/mixed
**Priority**: High
**Category**: Dialog
**Preconditions**:
- LocationCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer wählt im Dropdown "Beleuchtung" den Wert "Natürliches Licht" aus
2. Nutzer betrachtet die Formularfelder

**Erwartete Ergebnisse**:
- Toggle "Dynamische Sonnenstandberechnung" ist sichtbar
- Felder "Licht Ein" und "Licht Aus" sind sichtbar (für manuellen Override)

**Nachbedingungen**:
- Keine Daten verändert

**Siehe auch**: TC-002-027

**Tags**: [REQ-002, location, lichtzeiten, natural, dynamische-sonnenstandberechnung]

---

### TC-002-029: Licht-Ein-Feld validiert Format HH:MM

**Requirement**: REQ-002 § 2 — lights_on: Format HH:MM
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- LocationCreateDialog ist geöffnet
- Beleuchtungstyp "LED" ausgewählt (Felder "Licht Ein/Aus" sichtbar)

**Testschritte**:
1. Nutzer gibt im Feld "Licht Ein" den Text "25:70" ein (ungültiges Format)
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich nicht
- Feld "Licht Ein" zeigt eine Validierungsfehlermeldung

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, location, lichtzeiten, formatvalidierung]

---

### TC-002-030: Location erfolgreich erstellen (Happy Path, LED-Grow-Zelt)

**Requirement**: REQ-002 § 6 — Hierarchische Struktur: Location implementiert (DoD)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- LocationCreateDialog ist geöffnet mit siteKey="zuhause", parentLocationKey="arbeitszimmer"

**Testschritte**:
1. Nutzer gibt im Feld "Name" "Grow Zelt 1" ein
2. Nutzer wählt im Dropdown "Standort-Typ" den Wert "Grow-Zelt"
3. Nutzer gibt im Feld "Fläche (m²)" den Wert `1.44` ein
4. Nutzer wählt im Dropdown "Beleuchtung" den Wert "LED"
5. Nutzer wählt im Dropdown "Bewässerungssystem" den Wert "Manuell"
6. Nutzer gibt im Feld "Licht Ein" den Wert "06:00" ein
7. Nutzer gibt im Feld "Licht Aus" den Wert "22:00" ein
8. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- Location-Baum aktualisiert sich und zeigt "Grow Zelt 1" als Kind von "Arbeitszimmer"

**Nachbedingungen**:
- Location "Grow Zelt 1" mit depth=2, path="haus/arbeitszimmer/growzelt1" gespeichert

**Tags**: [REQ-002, location, erstellen, happy-path, led, grow-zelt]

---

## 7. Location — Detailseite bearbeiten

### TC-002-031: Location-Detailseite zeigt Breadcrumb-Pfad

**Requirement**: REQ-002 § 6 — Breadcrumb-Pfad: Breadcrumb für jeden Standort generierbar (DoD)
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Location "Grow Zelt 1" (depth=2, path=haus/arbeitszimmer/growzelt1) existiert

**Testschritte**:
1. Nutzer navigiert zu `/standorte/locations/growzelt1`

**Erwartete Ergebnisse**:
- Breadcrumb-Navigation zeigt den Pfad: "Zuhause > Haus > Arbeitszimmer > Grow Zelt 1"
- Jeder Breadcrumb-Teil ist ein anklickbarer Link zur jeweiligen Detailseite
- Die aktuelle Location "Grow Zelt 1" ist als nicht-klickbarer letzter Teil hervorgehoben

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, breadcrumb, navigation]

---

### TC-002-032: Location löschen — Kaskadierendes Löschen ohne belegte Slots

**Requirement**: REQ-002 § 3 — Kaskadierendes Löschen: prüft belegte Slots (DoD)
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- Location "Grow Zelt 2" hat 2 Slots, beide frei (keine aktiven Pflanzen)
- Nutzer ist auf der Detailseite von "Grow Zelt 2"

**Testschritte**:
1. Nutzer klickt auf den "Löschen"-Button
2. ConfirmDialog öffnet sich
3. Nutzer klickt auf "Löschen" im Dialog

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Nutzer wird zurück zur übergeordneten Seite navigiert
- Erfolgs-Snackbar erscheint
- "Grow Zelt 2" und seine 2 Slots erscheinen nicht mehr im Location-Baum

**Nachbedingungen**:
- Location und alle Kind-Slots sind gelöscht

**Tags**: [REQ-002, location, löschen, kaskadierendes-löschen, admin]

---

### TC-002-033: Location löschen blockiert bei belegtem Slot im Teilbaum

**Requirement**: REQ-002 § 3 — Kaskadierendes Löschen: blocked wenn occupied Slots (DoD)
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- Location "Arbeitszimmer" hat Kind-Locations "Grow Zelt 1" (Slot GROWZELT1_1 ist belegt) und "Grow Zelt 2" (alle frei)
- Nutzer ist auf der Detailseite von "Arbeitszimmer"

**Testschritte**:
1. Nutzer klickt auf den "Löschen"-Button
2. ConfirmDialog öffnet sich
3. Nutzer klickt auf "Löschen" im Dialog

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (Snackbar oder Dialog): "Kann nicht löschen: 1 belegter Slot im Teilbaum (GROWZELT1_1)"
- Location "Arbeitszimmer" und alle ihre Kinder bleiben erhalten
- Location-Baum ist unverändert

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, löschen, blocked, belegter-slot, fehlermeldung]

---

### TC-002-034: Tiefenhinweis bei Überschreitung empfohlener Verschachtelungstiefe

**Requirement**: REQ-002 § 3 — Tiefenlimit (Soft): UI zeigt Hinweis ab Tiefe > MAX_LOCATION_DEPTH=5
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Eine Location auf Tiefe 5 (depth=5) existiert
- LocationCreateDialog soll darunter eine weitere Location anlegen

**Testschritte**:
1. Nutzer öffnet den "Bereich hinzufügen"-Dialog auf einer Location mit depth=5
2. Nutzer gibt einen Namen ein und klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Ein Hinweis-Banner oder Warnung erscheint: Empfohlene Verschachtelungstiefe überschritten
- Die Location kann trotzdem erstellt werden (kein Hardblock)

**Nachbedingungen**:
- Location auf Tiefe 6 wird mit Warnung erstellt

**Tags**: [REQ-002, location, tiefenlimit, soft-warnung]

---

## 8. Slot — Erstellen

### TC-002-035: Slot erfolgreich erstellen (Happy Path)

**Requirement**: REQ-002 § 6 — Slot implementiert (DoD)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Location "Grow Zelt 1" ist geöffnet
- Kein Slot vorhanden

**Testschritte**:
1. Nutzer klickt auf den "Stellplatz erstellen"-Button auf der Location-Detailseite
2. Dialog "Stellplatz erstellen" öffnet sich
3. Nutzer gibt im Feld "Stellplatz-ID" den Text "GROWZELT1_A1" ein
4. Nutzer gibt im Feld "Kapazität" den Wert `1` ein
5. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- Slot "GROWZELT1_A1" erscheint in der Stellplatz-Liste der Location

**Nachbedingungen**:
- Slot mit ID "GROWZELT1_A1" ist gespeichert

**Tags**: [REQ-002, slot, erstellen, happy-path]

---

### TC-002-036: Slot-ID-Format-Validierung — ungültiges Format abgelehnt

**Requirement**: REQ-002 § 3 — SlotDefinition: id regex ^[A-Z0-9]+_[A-Z0-9]+$
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- SlotCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Stellplatz-ID" den Text "ungueltig" ein (kein Unterstrich)
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich nicht
- Feld "Stellplatz-ID" zeigt eine Validierungsfehlermeldung (Format: BEREICH_POSITION)
- Kein Snackbar erscheint

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, slot, formvalidierung, id-format]

---

### TC-002-037: Slot-ID wird automatisch in Großbuchstaben umgewandelt

**Requirement**: REQ-002 § 3 — SlotDefinition.id: transform toUpperCase
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- SlotCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Stellplatz-ID" den Text "growzelt1_a1" ein (Kleinbuchstaben)
2. Nutzer verlässt das Feld (Tab oder Klick außerhalb)

**Erwartete Ergebnisse**:
- Das Feld zeigt den transformierten Wert "GROWZELT1_A1" in Großbuchstaben

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, slot, formvalidierung, transform, uppercase]

---

### TC-002-038: Slot-Kapazität-Validierung — Grenzwerte (1–20)

**Requirement**: REQ-002 § 3 — SlotDefinition: capacity_plants ge=1, le=20
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- SlotCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Stellplatz-ID" den Text "TENT01_A1" ein
2. Nutzer gibt im Feld "Kapazität" den Wert `25` ein (über Maximum)
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich nicht
- Feld "Kapazität" zeigt Validierungsfehlermeldung (max 20)
- Kein Snackbar erscheint

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, slot, formvalidierung, grenzwert, kapazität]

---

### TC-002-039: Slot-Kapazität-Validierung — Untergrenze (0 abgelehnt)

**Requirement**: REQ-002 § 3 — SlotDefinition: capacity_plants ge=1
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- SlotCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Stellplatz-ID" den Text "TENT01_B1" ein
2. Nutzer gibt im Feld "Kapazität" den Wert `0` ein (unter Minimum)
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich nicht
- Feld "Kapazität" zeigt Validierungsfehlermeldung (min 1)

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [REQ-002, slot, formvalidierung, grenzwert, kapazität]

---

## 9. Slot — Detailseite

### TC-002-040: Slot-Detailseite zeigt Belegungs-Status

**Requirement**: REQ-002 § 6 — Slot-Verfügbarkeit: Echtzeit-Status belegt/frei (DoD)
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Slot "GROWZELT1_A1" existiert
- Der Slot ist aktuell belegt (aktive Pflanzinstanz zugeordnet)

**Testschritte**:
1. Nutzer navigiert zur Slot-Detailseite `/standorte/slots/GROWZELT1_A1`

**Erwartete Ergebnisse**:
- Feld "Belegt" zeigt einen aktiven Status (z. B. Chip "Belegt" oder Check-Indikator)
- Slot-ID, Kapazität und Standort-Referenz sind korrekt angezeigt

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, slot, detailansicht, belegung-status]

---

### TC-002-041: Slot löschen — belegt blockiert Löschung

**Requirement**: REQ-002 § 3 — Kaskadierendes Löschen: occupied Slots blockieren
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- Slot "GROWZELT1_A1" ist belegt
- Nutzer ist auf der Detailseite dieses Slots

**Testschritte**:
1. Nutzer klickt auf den "Löschen"-Button
2. ConfirmDialog öffnet sich
3. Nutzer bestätigt das Löschen

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (Snackbar oder Inline): Slot kann nicht gelöscht werden, da eine aktive Pflanze zugeordnet ist
- Slot ist weiterhin vorhanden

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, slot, löschen, blocked, belegt]

---

## 10. LocationType-Stammdaten (CRUD)

### TC-002-042: LocationType-Liste zeigt alle System-Seed-Typen

**Requirement**: REQ-002 § 6 — LocationType-System-Seed: 10 vordefinierte Typen (DoD)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- System ist frisch installiert mit Seed-Daten

**Testschritte**:
1. Nutzer navigiert zur LocationType-Verwaltungsseite (z. B. via Admin-Menü oder `/standorte/location-types`)

**Erwartete Ergebnisse**:
- Tabelle zeigt exakt 10 System-Typen: Garten, Gewächshaus, Gebäude, Zimmer, Balkon, Terrasse, Grow-Zelt, Beet, Regal, Topf-/Container-Gruppe
- Alle System-Typen sind als "System" markiert (z. B. Chip oder Icon)
- Reihenfolge entspricht sort_order (10, 20, 30, ..., 100)

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, locationtype, listenansicht, system-seed]

---

### TC-002-043: Nutzerdefinierten LocationType anlegen (Happy Path)

**Requirement**: REQ-002 § 6 — LocationType-CRUD (DoD)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- LocationType-Verwaltungsseite ist geöffnet

**Testschritte**:
1. Nutzer klickt auf "Standort-Typ erstellen" (oder entsprechenden Erstellen-Button)
2. Dialog öffnet sich
3. Nutzer gibt im Feld "Name" "Hügelbeet" ein
4. Nutzer gibt im Feld "Reihenfolge" den Wert `110` ein
5. Nutzer lässt "Indoor" deaktiviert (Outdoor-Typ)
6. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- "Hügelbeet" erscheint in der LocationType-Liste ohne System-Markierung
- Im Dropdown "Standort-Typ" des LocationCreateDialogs erscheint "Hügelbeet" am Ende der Liste

**Nachbedingungen**:
- Nutzerdefiniierter LocationType "Hügelbeet" gespeichert (is_system=false)

**Tags**: [REQ-002, locationtype, erstellen, happy-path, nutzerdefiniert]

---

### TC-002-044: System-LocationType löschen ist gesperrt

**Requirement**: REQ-002 § 3 — LocationType-Lösch-Schutz: is_system=true → HTTP 403
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- System-Typ "Garten" (is_system=true) ist in der Liste sichtbar

**Testschritte**:
1. Nutzer navigiert zur LocationType-Verwaltungsseite
2. Nutzer versucht den System-Typ "Garten" zu löschen (Löschen-Button klicken oder ConfirmDialog bestätigen)

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "System-Standort-Typen können nicht gelöscht werden"
- Typ "Garten" bleibt in der Liste erhalten
- Alternativ: Der Löschen-Button für System-Typen ist deaktiviert/nicht sichtbar

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, locationtype, löschen, system-schutz, fehlermeldung]

---

### TC-002-045: LocationType löschen blockiert wenn von Location verwendet

**Requirement**: REQ-002 § 3 — LocationType-Referenzielle Integrität: HTTP 409 wenn in Verwendung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- Nutzerdefinierter Typ "Hügelbeet" (is_system=false) existiert
- Mindestens 1 Location referenziert diesen Typ

**Testschritte**:
1. Nutzer navigiert zur LocationType-Verwaltungsseite
2. Nutzer klickt auf "Löschen" bei "Hügelbeet"
3. ConfirmDialog öffnet sich
4. Nutzer bestätigt das Löschen

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (Snackbar oder Dialog): z. B. "Typ wird von 1 Location(s) verwendet"
- Typ "Hügelbeet" bleibt in der Liste erhalten

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, locationtype, löschen, referentielle-integrität, fehlermeldung]

---

### TC-002-046: LocationType löschen — nicht verwendeter Typ wird gelöscht

**Requirement**: REQ-002 § 3 — LocationType-CRUD: Löschen wenn nicht in Verwendung
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist als Admin eingeloggt
- Nutzerdefinierter Typ "Hügelbeet" (is_system=false) existiert
- Keine Location verwendet diesen Typ

**Testschritte**:
1. Nutzer navigiert zur LocationType-Verwaltungsseite
2. Nutzer klickt auf "Löschen" bei "Hügelbeet"
3. ConfirmDialog öffnet sich
4. Nutzer bestätigt das Löschen

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- "Hügelbeet" erscheint nicht mehr in der Liste
- Im Dropdown "Standort-Typ" des LocationCreateDialogs ist "Hügelbeet" nicht mehr vorhanden

**Nachbedingungen**:
- LocationType "Hügelbeet" gelöscht

**Tags**: [REQ-002, locationtype, löschen, happy-path, nutzerdefiniert]

---

## 11. Fruchtfolge-Validierung (Crop Rotation)

### TC-002-047: Fruchtfolge-Kritische Warnung bei Familien-Wiederholung

**Requirement**: REQ-002 § 6 — Testszenario 1: Fruchtfolge-Kritische Wiederholung
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Slot "BEET_A_ROW1" hatte 2023 Tomaten (Solanaceae) und 2024 Paprika (Solanaceae) angebaut
- Nutzer versucht Aubergine (Solanaceae) für 2025 zu planen

**Testschritte**:
1. Nutzer navigiert zur Slot-Detailseite "BEET_A_ROW1"
2. Nutzer klickt auf "Bepflanzung planen" oder entsprechende Aktion
3. Nutzer wählt die Spezies "Solanum melongena" (Aubergine)
4. Nutzer bestätigt die Aktion

**Erwartete Ergebnisse**:
- Eine Warnungsmeldung erscheint: "KRITISCH: Solanaceae wurde zuletzt vor X Jahren an diesem Standort angebaut. Empfohlener Abstand: 3 Jahre."
- Alternativvorschläge werden angezeigt (z. B. Fabaceae, Brassicaceae)
- Die Bepflanzung ist blockiert oder erfordert eine explizite Bestätigung

**Nachbedingungen**:
- Ohne explizite Bestätigung: Keine Bepflanzung gespeichert

**Siehe auch**: TC-002-048 (Warnung bei aufeinanderfolgenden Starkzehrer)

**Tags**: [REQ-002, fruchtfolge, kritische-warnung, familien-wiederholung]

---

### TC-002-048: Fruchtfolge-Warnung bei drei aufeinanderfolgenden Starkzehrer

**Requirement**: REQ-002 § 3 — CropRotationValidator: Nährstoff-Ungleichgewicht
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Slot hatte in den letzten 2 Jahren ausschließlich Starkzehrer (z. B. Tomaten, Kohl)
- Nutzer plant wieder einen Starkzehrer

**Testschritte**:
1. Nutzer navigiert zur Slot-Detailseite
2. Nutzer plant eine dritte Starkzehrer-Folge
3. System prüft die Fruchtfolge

**Erwartete Ergebnisse**:
- Eine Warnung erscheint: "WARNUNG: Drei aufeinanderfolgende Starkzehrer. Erwäge Gründüngung oder Schwachzehrer."
- Die Bepflanzung wird nicht blockiert (nur Warnung, kein Hardblock)

**Nachbedingungen**:
- Bepflanzung kann trotzdem gespeichert werden

**Tags**: [REQ-002, fruchtfolge, warnung, starkzehrer, nutrient-balance]

---

### TC-002-049: Fruchtfolge OK — keine Warnung bei korrekter Rotation

**Requirement**: REQ-002 § 3 — CropRotationValidator: Fruchtfolge OK
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Slot hatte 2023 Tomaten (Solanaceae, Starkzehrer) und 2024 Möhren (Apiaceae, Mittelzehrer)
- Nutzer plant 2025 Bohnen (Fabaceae, Schwachzehrer — andere Familie)

**Testschritte**:
1. Nutzer navigiert zur Slot-Detailseite
2. Nutzer plant Bohnen für den Slot
3. System prüft die Fruchtfolge

**Erwartete Ergebnisse**:
- Keine Warnung oder Blockierung erscheint
- Bepflanzung kann direkt gespeichert werden

**Nachbedingungen**:
- Bepflanzung wird gespeichert

**Tags**: [REQ-002, fruchtfolge, ok, keine-warnung, rotation]

---

## 12. Zirkuläre Referenz verhindern

### TC-002-050: Zirkuläre Referenz wird verhindert

**Requirement**: REQ-002 § 3 — Zirkuläre Referenzen verhindern; § 6 Testszenario 5
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Location "Haus" (parent=null), "Arbeitszimmer" (parent=Haus) existieren
- Nutzer versucht "Haus" als Kind von "Arbeitszimmer" zu setzen

**Testschritte**:
1. Nutzer öffnet die Bearbeitungsseite der Location "Haus"
2. Nutzer ändert das Feld "Übergeordnete Location" auf "Arbeitszimmer"
3. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (Snackbar oder Inline): "Zirkuläre Referenz: 'Haus' ist bereits Vorfahre von 'Arbeitszimmer'"
- Die bestehende Hierarchie bleibt unverändert
- "Haus" bleibt weiterhin auf Tiefe 0 (parent=null)

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, zirkuläre-referenz, fehlermeldung]

---

## 13. Properties-Vererbung

### TC-002-051: Vererbter light_type vom Eltern-Standort sichtbar

**Requirement**: REQ-002 § 3 — Properties-Vererbung: light_type, irrigation_system, orientation
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Location "Arbeitszimmer" hat light_type=null (nicht explizit gesetzt)
- Eltern-Location "Haus" hat light_type="natural"
- Nutzer öffnet die Detailseite von "Arbeitszimmer"

**Testschritte**:
1. Nutzer navigiert zu `/standorte/locations/arbeitszimmer`
2. Nutzer betrachtet das Feld "Beleuchtung"

**Erwartete Ergebnisse**:
- Das Feld "Beleuchtung" zeigt "Natürliches Licht" (vom Eltern-Standort geerbt)
- Ein Hinweis zeigt an, dass der Wert geerbt und nicht lokal gesetzt ist (z. B. "(von Haus geerbt)")

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location, vererbung, light-type, inherited]

---

## 14. Standort-Hierarchie — vollständiger Baum

### TC-002-052: Vollständiger Standort-Baum wird geladen (4 Ebenen)

**Requirement**: REQ-002 § 6 — Testszenario 4: 5-Ebenen-Standort-Hierarchie; Standort-Baum (DoD)
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Site "Zuhause" mit Beispielstruktur aus Spec:
  - Zuhause > Garten (depth=0) — 2 Slots
  - Zuhause > Haus (depth=0) > Arbeitszimmer (depth=1) > Grow Zelt 1 (depth=2) — 3 Slots
  - Zuhause > Haus > Arbeitszimmer > Grow Zelt 2 (depth=2) — 2 Slots

**Testschritte**:
1. Nutzer navigiert zu `/standorte/sites/zuhause`
2. Nutzer klappt alle Knoten im Location-Baum auf

**Erwartete Ergebnisse**:
- Baum zeigt die vollständige Hierarchie: Garten und Haus als Wurzelknoten
- Haus enthält Arbeitszimmer; Arbeitszimmer enthält Grow Zelt 1 und Grow Zelt 2
- Depth-Werte stimmen: Garten=0, Haus=0, Arbeitszimmer=1, Grow Zelt 1=2, Grow Zelt 2=2
- Slot-Anzahl pro Location ist korrekt angezeigt

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, location-baum, hierarchie, vollständig, tiefe]

---

### TC-002-053: Freie Slots unter einem Teilbaum finden

**Requirement**: REQ-002 § 6 — Testszenario 6: Teilbaum-Slot-Abfrage; Teilbaum-Slots (DoD)
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Location "Arbeitszimmer" enthält "Grow Zelt 1" (3 Slots) und "Grow Zelt 2" (2 Slots)
- Slot GROWZELT1_1 ist belegt, alle anderen frei
- Nutzer ist auf der Detailseite "Arbeitszimmer"

**Testschritte**:
1. Nutzer betrachtet den Abschnitt "Stellplätze" oder "Freie Slots" auf der Location-Detailseite "Arbeitszimmer"

**Erwartete Ergebnisse**:
- 4 freie Slots werden angezeigt: GROWZELT1_2, GROWZELT1_3, GROWZELT2_1, GROWZELT2_2
- Slot GROWZELT1_1 (belegt) wird nicht in der Freie-Slots-Ansicht angezeigt
- Jeder Slot zeigt seinen übergeordneten Location-Namen (z. B. "Grow Zelt 1", "Grow Zelt 2")

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, slot, freie-slots, teilbaum, hierarchie]

---

## 15. Lichtzeiten-Verwaltung

### TC-002-054: Lichtzeiten für LED-Location korrekt gespeichert und angezeigt

**Requirement**: REQ-002 § 2 — Lichtzeiten-Verwaltung: led → lights_on/lights_off setzbar
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Location "Grow Zelt 1" mit light_type=led ist geöffnet

**Testschritte**:
1. Nutzer ändert das Feld "Licht Ein" auf "06:00"
2. Nutzer ändert das Feld "Licht Aus" auf "22:00"
3. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgs-Snackbar erscheint
- Beim erneuten Öffnen der Detailseite zeigen die Felder "Licht Ein" = "06:00" und "Licht Aus" = "22:00"

**Nachbedingungen**:
- Location mit Lichtzeiten gespeichert

**Tags**: [REQ-002, location, lichtzeiten, led, happy-path]

---

### TC-002-055: Dynamische Sonnenstandberechnung aktivieren für Natural-Licht

**Requirement**: REQ-002 § 2 — Lichtzeiten-Verwaltung: natural + use_dynamic_sunrise=true
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Location "Garten" mit light_type=natural ist geöffnet
- Site hat GPS-Koordinaten gesetzt

**Testschritte**:
1. Nutzer aktiviert den Toggle "Dynamische Sonnenstandberechnung"
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgs-Snackbar erscheint
- Toggle "Dynamische Sonnenstandberechnung" bleibt aktiviert nach Reload

**Nachbedingungen**:
- use_dynamic_sunrise=true gespeichert

**Tags**: [REQ-002, location, lichtzeiten, natural, dynamische-sonnenstand]

---

## 16. Authentifizierung und Autorisierung

### TC-002-056: Nicht eingeloggter Nutzer kann Standorte nicht aufrufen

**Requirement**: REQ-002 § 4 — Authentifizierung & Autorisierung: JWT erforderlich
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist nicht eingeloggt (kein aktiver JWT)

**Testschritte**:
1. Nutzer navigiert direkt zu `/standorte/sites`

**Erwartete Ergebnisse**:
- Browser wird zur Login-Seite weitergeleitet (`/login` oder `/auth/login`)
- Standort-Daten werden nicht angezeigt

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, auth, unauthenticated, redirect]

---

### TC-002-057: Nur Admin kann Sites löschen

**Requirement**: REQ-002 § 4 — Autorisierung: Sites löschen = Admin
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist als "Grower" (Mitglied, nicht Admin) eingeloggt
- Site-Detailseite ist geöffnet

**Testschritte**:
1. Nutzer betrachtet die Site-Detailseite

**Erwartete Ergebnisse**:
- Der "Löschen"-Button ist entweder nicht sichtbar oder deaktiviert
- Oder: Bei Klick auf "Löschen" erscheint eine Fehlermeldung "Keine Berechtigung"

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, auth, admin, grower, rbac, löschen]

---

## 17. Erfahrungsstufen-Integration (REQ-021)

### TC-002-058: Erweiterte Wasserquelle-Felder nur bei Fortgeschritten+ sichtbar

**Requirement**: REQ-002 § 1 — WaterSource; REQ-021 — ExpertiseFieldWrapper
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Anfänger"
- SiteCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer öffnet den Dialog "Standort erstellen"
2. Nutzer betrachtet den Formularinhalt

**Erwartete Ergebnisse**:
- Der Abschnitt "Wasserquelle" (Leitungswasser-Profil) ist ausgeblendet oder mit ExpertiseFieldWrapper gekennzeichnet
- Nur grundlegende Felder (Name, Klimazone, Fläche, Zeitzone) sind sichtbar

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, REQ-021, erfahrungsstufe, anfänger, feldvisibilität]

---

### TC-002-059: "Alle Felder anzeigen" schaltet Wasserquellen-Sektion sichtbar

**Requirement**: REQ-002 § 1 — WaterSource; REQ-021 — ShowAllFieldsToggle
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Anfänger"
- SiteCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer klickt auf den Toggle "Alle Felder anzeigen"
2. Nutzer betrachtet den Formularinhalt

**Erwartete Ergebnisse**:
- Der Abschnitt "Wasserquelle" wird sichtbar
- Alle Leitungswasser-Profil-Felder (EC, pH, Alkalinität, GH, Ca, Mg, Chlor, Chloramin, Messdatum, Quelle) sind ausfüllbar

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, REQ-021, show-all-toggle, wasserquelle]

---

## 18. Site-Runs-Sektion

### TC-002-060: Site-Detailseite zeigt verknüpfte Pflanzdurchläufe

**Requirement**: REQ-002 § 6 — Hierarchische Struktur; Site als Kontext für PlantingRuns (REQ-013)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Site "Zuhause" hat 2 verknüpfte Pflanzdurchläufe: "Frühling 2025" (active) und "Herbst 2024" (completed)
- Nutzer ist auf der Site-Detailseite

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite `/standorte/sites/zuhause`
2. Nutzer scrollt zum Abschnitt "Pflanzdurchläufe" (SiteRunsSection)

**Erwartete Ergebnisse**:
- Tabelle zeigt beide Pflanzdurchläufe
- "Frühling 2025" zeigt Status-Chip "Aktiv" (blaue Farbe)
- "Herbst 2024" zeigt Status-Chip "Abgeschlossen" (grüne Farbe)
- Klick auf einen Durchlauf navigiert zur PlantingRun-Detailseite

**Nachbedingungen**:
- Keine Daten verändert

**Tags**: [REQ-002, site, pflanzdurchläufe, REQ-013, detailansicht]

---

## 19. Edge Cases und Grenzwerte

### TC-002-061: Site mit minimalen Pflichtdaten erstellen

**Requirement**: REQ-002 § 3 — LocationDefinition: name min_length=1
**Priority**: Medium
**Category**: Grenzwert
**Preconditions**:
- SiteCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Name" exakt 1 Zeichen ein: "X"
2. Lässt alle anderen Felder auf Standardwerten (climate_zone="", total_area_m2=0, timezone="UTC")
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Site wird erfolgreich gespeichert
- Erfolgs-Snackbar erscheint
- Site "X" erscheint in der Liste

**Nachbedingungen**:
- Site "X" gespeichert

**Tags**: [REQ-002, site, grenzwert, minimales-pflichtfeld]

---

### TC-002-062: Location-Fläche Grenzwert — 0 m² erlaubt, negativ nicht

**Requirement**: REQ-002 § 3 — LocationDefinition: area_m2 gt=0, le=10000
**Priority**: Medium
**Category**: Grenzwert
**Preconditions**:
- LocationCreateDialog ist geöffnet

**Testschritte Schritt A (Grenzwert 0)**:
1. Nutzer gibt im Feld "Fläche (m²)" den Wert `0` ein
2. Nutzer gibt "Name" an und klickt auf "Erstellen"

**Erwartete Ergebnisse Schritt A**:
- Formularvalidierung zeigt Fehler: Wert muss > 0 sein (gt=0)

**Testschritte Schritt B (Grenzwert 10000)**:
1. Nutzer gibt im Feld "Fläche (m²)" den Wert `10000` ein
2. Nutzer gibt "Name" an und klickt auf "Erstellen"

**Erwartete Ergebnisse Schritt B**:
- Location wird erfolgreich gespeichert (le=10000 ist erlaubt)

**Nachbedingungen**:
- Abhängig von Schritt

**Tags**: [REQ-002, location, grenzwert, fläche, formvalidierung]

---

## 20. Wasseranalyse-Warnungen (WaterSource)

Diese Gruppe deckt die Soft-Warnungen ab, die auf der Site-Detailseite im Abschnitt "Wasserquelle" eingeblendet werden, wenn Wasseranalysedaten veraltet, inkonsistent oder auf Membranverschleiß hinweisend sind.

### TC-002-063: Warnung bei veralteter Wasseranalyse (measurement_date > 6 Monate)

**Requirement**: REQ-002 § 1 — TapWaterProfile: measurement_date; § 6 DoD — Messalter-Warnung (Soft)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Site "Zuhause" hat eine WaterSource konfiguriert
- `tap_water_profile.measurement_date` ist auf ein Datum gesetzt, das mehr als 180 Tage (6 Monate) in der Vergangenheit liegt (z. B. vor 200 Tagen)
- Nutzer navigiert zur Site-Detailseite `/standorte/sites/zuhause`

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite `/standorte/sites/zuhause`
2. Nutzer scrollt zum Abschnitt "Wasserquelle" (WaterSourceSection)
3. Nutzer betrachtet den angezeigten Inhalt oberhalb oder innerhalb des Leitungswasser-Profils

**Erwartete Ergebnisse**:
- Ein gelber Warn-Banner (MUI Alert, severity="warning") ist sichtbar
- Der Banner enthält den Text "Wasseranalyse älter als 6 Monate" oder eine inhaltlich gleichwertige Meldung
- Das angezeigte `measurement_date`-Feld zeigt das korrekte (alte) Datum
- Der Banner bietet einen Hinweis, die Analyse zu erneuern (z. B. Link oder Hinweistext)
- Die restlichen Wasserparameter (EC, pH, GH usw.) werden weiterhin angezeigt — der Banner blockiert nicht den Zugriff auf die Daten

**Nachbedingungen**:
- Keine Daten verändert

**Siehe auch**: TC-002-066 (kein Banner bei frischer Analyse)

**Tags**: [REQ-002, wasserquelle, measurement-date, messalter-warnung, soft-warnung, banner]

---

### TC-002-064: RO-Membran-Warnung bei erhöhtem Rest-EC (ro_water_profile.ec_ms > 0.05 mS)

**Requirement**: REQ-002 § 1 — RoWaterProfile: ec_ms; § 6 DoD — RO-Membran-Warnung (Soft)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Site "Zuhause" hat eine WaterSource mit `has_ro_system=true` konfiguriert
- `ro_water_profile.ec_ms` ist auf einen Wert über 0.05 mS gesetzt (z. B. 0.08 mS), was auf Membranverschleiß hindeutet
- Nutzer navigiert zur Site-Detailseite `/standorte/sites/zuhause`

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite `/standorte/sites/zuhause`
2. Nutzer scrollt zum Abschnitt "Wasserquelle"
3. Nutzer betrachtet den Bereich "Osmosewasser-Profil"

**Erwartete Ergebnisse**:
- Ein orangener Warn-Banner (MUI Alert, severity="warning" oder severity="error") ist im Bereich des RO-Profils sichtbar
- Der Banner enthält einen Text zum Thema Membranverschleiß, z. B. "RO-Membran-EC über 0.05 mS — Membranverschleiß prüfen" oder sinngemäß
- Das Feld "Rest-EC" zeigt den eingetragenen Wert (z. B. 0.08 mS)
- Der Banner blockiert nicht die Anzeige der übrigen Daten

**Nachbedingungen**:
- Keine Daten verändert

**Siehe auch**: TC-002-019 (has_ro_system=false blendet RO-Sektion aus), TC-002-020 (RO-Toggle-Sichtbarkeit)

**Tags**: [REQ-002, wasserquelle, ro-membran, ec-warnung, soft-warnung, banner, osmose]

---

### TC-002-065: GH-Plausibilitätsprüfung — sehr weiches Wasser löst Info-Banner aus

**Requirement**: REQ-002 § 1 — TapWaterProfile: gh_ppm, Validierungsregeln — GH-Plausibilitäts-Check; § 6 DoD
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Site "Zuhause" hat eine WaterSource konfiguriert
- `tap_water_profile.gh_ppm` ist auf einen sehr niedrigen Wert (z. B. < 17.8 ppm, entspricht < 1.0 °dH sehr weiches Wasser) gesetzt
- Alternativ: `calcium_ppm` und `magnesium_ppm` sind gesetzt und der berechnete GH-Wert (Ca × 2.497 + Mg × 4.116) weicht um mehr als 30 % vom eingetragenen `gh_ppm` ab

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite `/standorte/sites/zuhause`
2. Nutzer scrollt zum Abschnitt "Wasserquelle"
3. Nutzer betrachtet das Leitungswasser-Profil

**Erwartete Ergebnisse**:
- Ein Info-Banner (MUI Alert, severity="info") ist sichtbar
- Der Banner enthält einen Hinweis auf sehr weiches Wasser, z. B. "Sehr weiches Wasser — CalMag-Korrektur empfohlen" oder "GH-Wert weicht von Ca+Mg-Berechnung ab. Daten prüfen."
- Der Banner ist informierend, nicht blockierend — der Nutzer kann die Seite normal verwenden
- Die eingetragenen Wasserparameter werden unverändert angezeigt

**Nachbedingungen**:
- Keine Daten verändert

**Siehe auch**: TC-002-009 (WaterSource-Formular mit GH-Feld), TC-002-063 (Messalter-Warnung)

**Tags**: [REQ-002, wasserquelle, gh-plausibilität, weiches-wasser, calmag, info-banner, soft-warnung]

---

### TC-002-066: Kein Warn-Banner bei frischer Wasseranalyse (measurement_date < 6 Monate)

**Requirement**: REQ-002 § 1 — TapWaterProfile: measurement_date; § 6 DoD — Messalter-Warnung nur bei Überschreitung
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Site "Zuhause" hat eine WaterSource mit vollständig ausgefülltem TapWaterProfile konfiguriert
- `tap_water_profile.measurement_date` ist auf ein Datum gesetzt, das weniger als 180 Tage (6 Monate) in der Vergangenheit liegt (z. B. vor 30 Tagen)
- `ro_water_profile.ec_ms` ist ≤ 0.05 mS (kein Membranverschleiß) oder `has_ro_system=false`
- `gh_ppm` ist plausibel (Abweichung zum berechneten Wert aus Ca+Mg unter 30 %)

**Testschritte**:
1. Nutzer öffnet die Site-Detailseite `/standorte/sites/zuhause`
2. Nutzer scrollt zum Abschnitt "Wasserquelle"
3. Nutzer betrachtet das Leitungswasser-Profil vollständig

**Erwartete Ergebnisse**:
- Kein gelber oder orangener Warn-Banner ist sichtbar
- Kein GH-Plausibilitäts-Info-Banner ist sichtbar
- Alle Wasserparameter (EC, pH, GH, Ca, Mg, Chlor, Chloramin, Messdatum, Quellnotiz) werden ohne Warnung angezeigt
- Die Seite vermittelt dem Nutzer, dass die Wasseranalyse aktuell und gültig ist

**Nachbedingungen**:
- Keine Daten verändert

**Siehe auch**: TC-002-063 (Warnung bei veraltetem Datum), TC-002-064 (RO-Membran-Warnung)

**Tags**: [REQ-002, wasserquelle, measurement-date, kein-banner, frische-analyse, happy-path]

---

## Coverage-Matrix

| Spec-Abschnitt | Beschreibung | Testfall-IDs |
|---|---|---|
| § 1 Business Case — Site | Site-Grundstruktur | TC-002-001 bis TC-002-013 |
| § 1 Wasserquellen-Konfiguration | WaterSource, TapWaterProfile, RoWaterProfile | TC-002-008, TC-002-009, TC-002-014 bis TC-002-020 |
| § 1 Wasseranalyse-Warnungen | Messalter, RO-Membran, GH-Plausibilität, Negativtest | TC-002-063 bis TC-002-066 |
| § 2 ArangoDB — Location | Location-Properties, Verschachtelung | TC-002-021 bis TC-002-034 |
| § 2 ArangoDB — Slot | Slot-Properties | TC-002-035 bis TC-002-041 |
| § 2 Lichtzeiten-Verwaltung | lights_on, lights_off, use_dynamic_sunrise | TC-002-027, TC-002-028, TC-002-029, TC-002-054, TC-002-055 |
| § 2 LocationType-Collection | 10 System-Seeds, CRUD | TC-002-042 bis TC-002-046 |
| § 3 Fruchtfolge-Engine | CropRotationValidator, 3-Jahres-Fenster | TC-002-047 bis TC-002-049 |
| § 3 Validierungsregeln | Zirkularität, site_key-Konsistenz, Tiefenlimit, Kaskadenlöschen, Vererbung | TC-002-032, TC-002-033, TC-002-034, TC-002-050, TC-002-051 |
| § 4 Auth/Authz | JWT, RBAC (Mitglied/Admin) | TC-002-056, TC-002-057 |
| § 6 DoD Checkliste | Breadcrumb, Teilbaum-Slots, vollständiger Baum | TC-002-031, TC-002-052, TC-002-053 |
| § 6 Testszenarien 1–7 | Spec-Szenarien als Browser-Testfälle | TC-002-047, TC-002-050, TC-002-052, TC-002-053, TC-002-033 |
| REQ-021 Integration | Erfahrungsstufen, Feldvisibilität | TC-002-058, TC-002-059 |
| REQ-013 Integration | Pflanzdurchläufe-Sektion auf Site | TC-002-060 |
| Edge Cases / Grenzwerte | Minimale Pflichtdaten, Bereichsgrenzen | TC-002-061, TC-002-062 |

### Nicht abgedeckte Bereiche (Spec vorhanden, Frontend noch nicht implementiert)

| Spec-Abschnitt | Grund |
|---|---|
| Visuelle Beetplanung (Drag & Drop, 2D-Ansicht) | Feature noch nicht implementiert (G-003 Review) |
| CropRotationPlan — 4-Jahres-Rotationsplaner (UI) | Backend-Modell spezifiziert, UI-Seite nicht vorhanden |
| Mobile QR-Code-Scanning für Slots | Feature noch nicht implementiert |
| Mischkultur-Overlay auf Beet-Layout | Feature noch nicht implementiert (G-004 Review) |
| GPS-Eingabefelder auf Location-Ebene | Keine UI-Felder in LocationCreateDialog sichtbar |
