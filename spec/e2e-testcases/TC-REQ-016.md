---
req_id: REQ-016
title: Optionale InvenTree-Integration (Inventar- & Verbrauchsmaterialverwaltung)
category: Integration & Inventar
test_count: 52
coverage_areas:
  - InvenTree-Verbindung anlegen / bearbeiten / Health-Check (Einstellungsseite Admin)
  - Feature-Toggle-Verhalten (Integration deaktiviert vs. aktiv)
  - Equipment-Verwaltung (Liste, Detail, Erstellen, Bearbeiten, Status-Lifecycle)
  - Equipment nach Location filtern
  - InvenTree-Part suchen und Entitaet verlinken (Dünger, Tank, Equipment)
  - Verlinkung aufheben
  - InvenTree-Bestandsanzeige in Dünger-Detail / Tank-Detail
  - auto_deduct-Konfiguration pro Verlinkung
  - Manueller Sync-Trigger (Full-Sync)
  - Einzelreferenz-Sync
  - Transaktions-Log (Listenansicht, Filterung, Status-Badge)
  - Graceful Degradation bei InvenTree-Ausfall (kein UI-Blocking)
  - Sicherheits-Sichtbarkeit (API-Token nie in UI sichtbar)
  - SSL-Zertifikat-Warnung bei verify_ssl=false
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-016: Optionale InvenTree-Integration

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-016 Optionale InvenTree-Integration v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

> **Implementierungsstand:** REQ-016 ist in Spezifikation Version 1.0 beschrieben. Eine Frontend-Seite fuer InvenTree-Einstellungen und Equipment-Verwaltung ist zum Zeitpunkt der Testerstellung noch nicht implementiert. Diese Testfaelle definieren das erwartete UI-Verhalten und dienen als Grundlage fuer die Implementierung und spaetere Selenium/Playwright-Automatisierung. Die erwarteten Routen basieren auf den Mustern der bestehenden Adminseiten (`/admin/...`) und Einstellungsseiten (`/settings/...`).

---

## 1. Feature-Toggle-Verhalten (InvenTree deaktiviert)

### TC-016-001: Keine InvenTree-Sektion sichtbar ohne aktive Verbindung

**Requirement**: REQ-016 § 1 — Optionalitaet
**Priority**: Critical
**Category**: Feature-Toggle / Navigation
**Preconditions**:
- Nutzer ist eingeloggt (beliebige Rolle: Mitglied oder Admin)
- Keine InvenTree-Verbindung in der Systemkonfiguration eingetragen
- InvenTree-Integration ist nicht aktiv

**Test Steps**:
1. Nutzer navigiert zur Hauptnavigation (Sidebar)
2. Nutzer sucht nach einem Navigationseintrag fuer "InvenTree" oder "Inventar-Integration"
3. Nutzer oeffnet die Duengerdetailseite eines beliebigen Duengers
4. Nutzer prueft, ob ein Abschnitt "InvenTree-Bestand" oder "Verlinkung" sichtbar ist
5. Nutzer oeffnet die Tankdetailseite eines beliebigen Tanks
6. Nutzer prueft, ob ein Abschnitt "InvenTree" sichtbar ist

**Expected Results**:
- Kein InvenTree-Navigationseintrag erscheint in der Sidebar
- Duengerdetailseite zeigt keinen InvenTree-Abschnitt
- Tankdetailseite zeigt keinen InvenTree-Abschnitt
- Alle anderen Funktionen (Duengung erfassen, Tankbefuellung etc.) funktionieren unveraendert

**Postconditions**:
- System befindet sich im gleichen Zustand wie vor dem Test

**Tags**: [req-016, feature-toggle, navigation, graceful-degradation]

---

### TC-016-002: Equipment-Menueintrag sichtbar unabhaengig von InvenTree-Konfiguration

**Requirement**: REQ-016 § 1 — Equipment als First-Class-Entity
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied oder Admin)
- InvenTree-Verbindung ist NICHT konfiguriert

**Test Steps**:
1. Nutzer navigiert zur Hauptnavigation
2. Nutzer sucht nach einem Navigationseintrag fuer "Equipment" oder "Betriebsmittel"
3. Nutzer klickt auf den Menueintrag

**Expected Results**:
- Ein Menueintrag "Equipment" oder "Betriebsmittel" ist in der Navigation sichtbar (Equipment ist unabhaengig von InvenTree)
- Die Equipment-Listenseite oeffnet sich
- Listenseite ist leer oder zeigt vorhandene Equipment-Eintraege
- Kein InvenTree-spezifischer Inhalt (Bestand, Part-ID) wird angezeigt, wenn keine Verbindung aktiv ist

**Postconditions**:
- Equipment-Listenseite ist geoeffnet

**Tags**: [req-016, equipment, navigation, feature-toggle]

---

## 2. InvenTree-Verbindungsverwaltung (Admin)

### TC-016-003: InvenTree-Verbindung anlegen (Happy Path)

**Requirement**: REQ-016 § 3.7 — Connection-CRUD, § 6 Akzeptanzkriterien DoD Connection-CRUD
**Priority**: Critical
**Category**: Formvalidierung / Happy Path
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Keine InvenTree-Verbindung vorhanden
- Seite fuer InvenTree-Verbindungsverwaltung erreichbar (z.B. `/admin/integrations/inventree`)

**Test Steps**:
1. Nutzer navigiert zur Seite "Integrationen" im Admin-Bereich
2. Nutzer klickt auf "InvenTree-Verbindung anlegen" oder "Neue Verbindung"
3. Im Erstellungs-Dialog oder Formular gibt Nutzer ein:
   - Name: `Haupt-Inventar`
   - URL: `https://inventree.local/api/`
   - API-Token: `inv-token-abc123`
   - Sync-Intervall: `60` Minuten
   - Push-Intervall: `5` Minuten
   - SSL verifizieren: aktiviert (Checkbox gesetzt)
4. Nutzer klickt "Speichern"

**Expected Results**:
- Erfolgs-Snackbar erscheint: z.B. "InvenTree-Verbindung wurde erfolgreich angelegt."
- Verbindung erscheint in der Liste mit Name "Haupt-Inventar" und Status-Badge "Nicht geprueft" oder "Inaktiv"
- Das API-Token-Feld zeigt NICHT den Klartext-Token (Feld ist leer oder zeigt Maskierung wie `•••••••`)
- URL ist sichtbar: `https://inventree.local/api/`

**Postconditions**:
- Eine InvenTree-Verbindung "Haupt-Inventar" ist angelegt

**Tags**: [req-016, connection, crud, admin, security, token-masking]

---

### TC-016-004: InvenTree-Verbindung anlegen — Pflichtfelder fehlen

**Requirement**: REQ-016 § 3.1 — InvenTreeConnection-Validierung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Verbindungs-Dialog oder Formular ist geoeffnet

**Test Steps**:
1. Nutzer laesst das Feld "Name" leer
2. Nutzer laesst das Feld "URL" leer
3. Nutzer laesst das Feld "API-Token" leer
4. Nutzer klickt "Speichern"

**Expected Results**:
- Fehlermeldungen erscheinen direkt an den Pflichtfeldern:
  - Neben "Name": "Name ist erforderlich" oder aequivalente Meldung
  - Neben "URL": "URL ist erforderlich"
  - Neben "API-Token": "API-Token ist erforderlich"
- Das Formular wird NICHT abgesendet
- Kein Snackbar erscheint

**Postconditions**:
- Keine neue Verbindung wurde angelegt

**Tags**: [req-016, connection, formvalidierung, pflichtfelder]

---

### TC-016-005: InvenTree-Verbindung anlegen — ungueltige URL

**Requirement**: REQ-016 § 3.1 — InvenTreeConnection HttpUrl-Validierung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Verbindungs-Dialog oder Formular ist geoeffnet

**Test Steps**:
1. Nutzer gibt im Feld "Name" ein: `Mein Inventar`
2. Nutzer gibt im Feld "URL" ein: `nicht-eine-url` (kein gueltiges URL-Format)
3. Nutzer gibt im Feld "API-Token" ein: `token-123`
4. Nutzer klickt "Speichern"

**Expected Results**:
- Fehlermeldung erscheint am URL-Feld: "Bitte geben Sie eine gueltige URL ein" oder aequivalente Meldung
- Formular wird nicht abgesendet

**Postconditions**:
- Keine neue Verbindung wurde angelegt

**Tags**: [req-016, connection, formvalidierung, url-validierung]

---

### TC-016-006: InvenTree-Verbindung anlegen — SSL-Warnung bei deaktivierter Zertifikatspruefung

**Requirement**: REQ-016 § 4.1 — IT-003 SSL-Zertifikat standardmaessig validieren, UI-Warnung bei Deaktivierung
**Priority**: High
**Category**: Sicherheit / UI-Feedback
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Verbindungs-Dialog oder Formular ist geoeffnet

**Test Steps**:
1. Nutzer gibt gueltigen Namen und URL ein
2. Nutzer deaktiviert die Checkbox "SSL verifizieren" (setzt `verify_ssl` auf false)
3. Nutzer beobachtet die UI-Reaktion direkt nach dem Deaktivieren

**Expected Results**:
- Sofort nach Deaktivieren der Checkbox erscheint eine sichtbare Warnung (gelbes Info-Banner, Hinweistext oder Icon) mit sinngemaeß: "Achtung: Die SSL-Zertifikatspruefung ist deaktiviert. Dies sollte nur fuer Self-Signed-Zertifikate in lokalen Netzwerken verwendet werden."
- Die Warnung verschwindet, wenn die Checkbox wieder aktiviert wird

**Postconditions**:
- Verbindungs-Dialog bleibt offen

**Tags**: [req-016, connection, ssl, sicherheit, warnung]

---

### TC-016-007: InvenTree-Verbindung Health-Check ausfuehren — Verbindung erfolgreich

**Requirement**: REQ-016 § 3.7 — Health-Check Endpunkt, § 6 Szenario 1
**Priority**: Critical
**Category**: Happy Path / UI-Feedback
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- InvenTree-Verbindung "Haupt-Inventar" ist angelegt (vgl. TC-016-003)
- InvenTree-Server ist erreichbar und antwortet mit OK

**Test Steps**:
1. Nutzer navigiert zur InvenTree-Verbindungsliste
2. Nutzer oeffnet die Detailseite der Verbindung "Haupt-Inventar" oder klickt auf "Verbindung testen" / "Health-Check"
3. Nutzer klickt auf den Button "Verbindung testen" / "Health-Check starten"
4. Nutzer wartet auf die Antwort (Loading-Indikator erwartet)

**Expected Results**:
- Waehrend des Checks erscheint ein Lade-Indikator (Spinner) auf oder neben dem Button
- Nach erfolgreichem Check wird ein gruenes Status-Badge oder Icon angezeigt: "Verbunden" oder "Gesund" (healthy)
- Der Zeitstempel "Letzter Health-Check" aktualisiert sich auf die aktuelle Zeit
- Kein Fehlertext erscheint

**Postconditions**:
- Health-Check-Status der Verbindung ist "Gesund" / "true"

**Tags**: [req-016, connection, health-check, admin, happy-path]

---

### TC-016-008: InvenTree-Verbindung Health-Check — Server nicht erreichbar

**Requirement**: REQ-016 § 4.1 — IT-006 generische Fehlermeldung, § 6 Szenario 4
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- InvenTree-Verbindung ist angelegt
- InvenTree-Server ist NICHT erreichbar (Server ausgefallen oder falsche URL)

**Test Steps**:
1. Nutzer navigiert zur InvenTree-Verbindungsdetailseite
2. Nutzer klickt auf "Verbindung testen"
3. Nutzer wartet auf die Antwort

**Expected Results**:
- Nach Ablauf der Wartezeit erscheint eine Fehlermeldung: "Verbindung fehlgeschlagen" oder "InvenTree-Server nicht erreichbar"
- Die Fehlermeldung offenbart NICHT, ob die URL eine gueltige InvenTree-Instanz ist (generische Formulierung)
- Status-Badge wechselt zu rotem "Nicht verbunden" oder "Fehler"
- Zeitstempel "Letzter Health-Check" aktualisiert sich

**Postconditions**:
- Health-Check-Status der Verbindung ist "Fehler" / "false"

**Tags**: [req-016, connection, health-check, fehlermeldung, sicherheit]

---

### TC-016-009: InvenTree-Verbindung bearbeiten (URL und Sync-Intervall aendern)

**Requirement**: REQ-016 § 3.7 — PUT /connections/{key}
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Verbindung "Haupt-Inventar" existiert
- Verbindungsdetailseite ist geoeffnet

**Test Steps**:
1. Nutzer klickt auf "Bearbeiten" oder das Stift-Icon der Verbindung
2. Nutzer aendert das Sync-Intervall-Feld von `60` auf `120`
3. Nutzer klickt "Speichern"

**Expected Results**:
- Erfolgs-Snackbar: "Verbindung wurde aktualisiert."
- In der Detailansicht steht nun Sync-Intervall: `120 Minuten`
- Das API-Token-Feld zeigt weiterhin nur die Maskierung (kein Klartext-Token sichtbar)

**Postconditions**:
- Verbindung hat Sync-Intervall 120 Minuten

**Tags**: [req-016, connection, crud, bearbeiten, admin]

---

### TC-016-010: InvenTree-Verbindung — Mitglieder (Nicht-Admin) haben keinen Zugriff auf Connection-Verwaltung

**Requirement**: REQ-016 § 4 — Auth-Matrix: Connection-Config nur Admin
**Priority**: High
**Category**: Zugriffskontrolle
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Mitglied" (nicht Admin)
- InvenTree-Verbindung ist angelegt

**Test Steps**:
1. Nutzer navigiert zu `/admin/integrations/inventree` oder versucht den Admin-Integrationsbereich zu oeffnen
2. Nutzer sucht nach einem Button "Neue Verbindung" oder "InvenTree konfigurieren"

**Expected Results**:
- Entweder: Der Admin-Bereich ist fuer Mitglieder nicht zugaenglich (Weiterleitung oder "Kein Zugriff"-Seite)
- Oder: Falls die Seite erreichbar ist, sind "Anlegen"-, "Bearbeiten"- und "Loeschen"-Buttons nicht vorhanden oder deaktiviert
- Keine Moeglichkeit, Connection-Konfiguration zu aendern

**Postconditions**:
- Keine Aenderungen an der Verbindungskonfiguration

**Tags**: [req-016, connection, zugriffsschutz, rbac, mitglied]

---

## 3. Equipment-Verwaltung

### TC-016-011: Equipment anlegen — Happy Path (Sensor)

**Requirement**: REQ-016 § 3.7 — Equipment-CRUD, § 6 Szenario 5
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied oder Admin)
- Equipment-Listenseite ist geoeffnet (`/equipment/` oder aequivalent)
- Mindestens eine Location "Growzelt 1" existiert

**Test Steps**:
1. Nutzer klickt auf "Equipment anlegen" oder "+ Neu"
2. Im Erstellungs-Dialog fuellt Nutzer aus:
   - Name: `Bluelab pH Pen`
   - Typ: `Sensor` (aus Dropdown)
   - Marke: `Bluelab`
   - Modell: `pH Pen`
   - Seriennummer: `BL-PH-2024-0042`
   - Kaufdatum: `15.06.2025`
   - Garantie bis: `15.06.2027`
   - Standort: `Growzelt 1` (aus Dropdown)
   - Status: `Aktiv` (Standard)
   - Notizen: `Kalibrierung alle 2 Wochen`
3. Nutzer klickt "Speichern"

**Expected Results**:
- Erfolgs-Snackbar: "Equipment wurde erfolgreich angelegt."
- "Bluelab pH Pen" erscheint in der Equipment-Liste
- Liste zeigt: Name, Typ (Sensor), Status-Badge (Aktiv), Standort (Growzelt 1)
- Kein InvenTree-Bestand sichtbar (wenn keine Verlinkung vorhanden)

**Postconditions**:
- Equipment "Bluelab pH Pen" ist angelegt, Status "Aktiv", Standort "Growzelt 1"

**Tags**: [req-016, equipment, crud, anlegen, happy-path]

---

### TC-016-012: Equipment anlegen — Pflichtfelder fehlen

**Requirement**: REQ-016 § 3.1 — Equipment-Modell (name, equipment_type Pflicht)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment-Erstellungs-Dialog ist geoeffnet

**Test Steps**:
1. Nutzer laesst das Feld "Name" leer
2. Nutzer laesst den "Typ" nicht ausgewaehlt
3. Nutzer klickt "Speichern"

**Expected Results**:
- Fehlermeldung neben dem Feld "Name": "Name ist erforderlich"
- Fehlermeldung neben dem Feld "Typ": "Typ ist erforderlich" oder Dropdown-Fehler
- Kein Equipment wurde angelegt

**Postconditions**:
- Kein neues Equipment im System

**Tags**: [req-016, equipment, formvalidierung, pflichtfelder]

---

### TC-016-013: Equipment-Typen korrekt im Dropdown angezeigt

**Requirement**: REQ-016 § 3.1 — EquipmentType Enum (tool, consumable, sensor, lighting, pump, filter, container, cleaning_agent, other)
**Priority**: Medium
**Category**: Listenansicht / Formularinhalt
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment-Erstellungs-Dialog ist geoeffnet

**Test Steps**:
1. Nutzer klickt auf das Dropdown-Feld "Typ"
2. Nutzer liest alle Eintraege im Dropdown

**Expected Results**:
- Dropdown enthaelt exakt folgende Optionen (deutschen Bezeichnungen):
  - Werkzeug (tool)
  - Verbrauchsmaterial (consumable)
  - Sensor (sensor)
  - Beleuchtung (lighting)
  - Pumpe (pump)
  - Filter (filter)
  - Behaelter (container)
  - Reinigungsmittel (cleaning_agent)
  - Sonstiges (other)
- Keine weiteren Eintraege

**Postconditions**:
- Dialog bleibt offen

**Tags**: [req-016, equipment, dropdown, enum, formularinhalt]

---

### TC-016-014: Equipment-Status-Lifecycle — Status von "Aktiv" auf "Wartung" aendern

**Requirement**: REQ-016 § 3.1 — EquipmentStatus (active, maintenance, stored, defective, retired)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment "Bluelab pH Pen" mit Status "Aktiv" existiert (vgl. TC-016-011)
- Equipment-Detailseite oder Edit-Dialog ist geoeffnet

**Test Steps**:
1. Nutzer navigiert zur Detailseite von "Bluelab pH Pen"
2. Nutzer klickt "Bearbeiten"
3. Nutzer aendert das Feld "Status" von `Aktiv` auf `Wartung`
4. Nutzer klickt "Speichern"

**Expected Results**:
- Erfolgs-Snackbar: "Equipment wurde aktualisiert."
- In der Detailansicht wird das Status-Badge aktualisiert: "Wartung" (gelb oder orange)
- In der Equipment-Liste zeigt "Bluelab pH Pen" das Status-Badge "Wartung"

**Postconditions**:
- Equipment "Bluelab pH Pen" hat Status "Wartung"

**Tags**: [req-016, equipment, statuswechsel, zustandswechsel]

---

### TC-016-015: Alle fuenf Equipment-Status korrekt darstellbar

**Requirement**: REQ-016 § 3.1 — EquipmentStatus vollstaendig abgedeckt
**Priority**: Medium
**Category**: Zustandswechsel / Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment-Bearbeitungs-Dialog ist geoeffnet

**Test Steps**:
1. Nutzer oeffnet das Status-Dropdown im Bearbeitungs-Dialog
2. Nutzer prueft alle verfuegbaren Status-Optionen

**Expected Results**:
- Dropdown enthaelt exakt 5 Optionen (deutschen Bezeichnungen):
  - Aktiv (active)
  - Wartung (maintenance)
  - Eingelagert (stored)
  - Defekt (defective)
  - Ausgemustert (retired)

**Postconditions**:
- Dialog bleibt unveraendert

**Tags**: [req-016, equipment, status, dropdown, enum]

---

### TC-016-016: Equipment nach Location filtern

**Requirement**: REQ-016 § 3.7 — GET /equipment/by-location/{key}
**Priority**: High
**Category**: Listenansicht / Filter
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment "Bluelab pH Pen" ist Standort "Growzelt 1" zugeordnet
- Equipment "Juno Pumpe A" ist Standort "Mischraum" zugeordnet
- Equipment-Listenseite ist geoeffnet

**Test Steps**:
1. Nutzer aktiviert den Location-Filter oder waehlt "Standort" aus dem Filter-Dropdown
2. Nutzer waehlt "Growzelt 1" aus
3. Nutzer beobachtet die gefilterte Liste

**Expected Results**:
- Liste zeigt nur "Bluelab pH Pen"
- "Juno Pumpe A" ist nicht sichtbar
- Filter-Chip oder Label zeigt aktiven Filter "Growzelt 1" an
- Nutzer kann Filter durch Klick auf "X" im Chip oder "Filter zuruecksetzen" entfernen; dann erscheinen beide Equipment-Eintraege

**Postconditions**:
- Equipment-Liste mit aktivem Location-Filter

**Tags**: [req-016, equipment, filter, location, listenansicht]

---

### TC-016-017: Equipment nach Typ filtern

**Requirement**: REQ-016 § 3.7 — GET /equipment/?equipment_type={type}
**Priority**: Medium
**Category**: Listenansicht / Filter
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment-Liste enthaelt mindestens einen "Sensor" und einen "Pumpe"-Eintrag

**Test Steps**:
1. Nutzer aktiviert Typ-Filter auf der Equipment-Listenseite
2. Nutzer waehlt "Sensor" aus
3. Nutzer beobachtet die Liste

**Expected Results**:
- Nur Equipment vom Typ "Sensor" ist sichtbar
- Pumpen, Werkzeuge etc. sind ausgeblendet
- Filter-Status ist in der UI sichtbar (z.B. als Chip "Typ: Sensor")

**Postconditions**:
- Typ-Filter ist aktiv

**Tags**: [req-016, equipment, filter, typ, listenansicht]

---

### TC-016-018: Equipment-Detailseite zeigt alle gespeicherten Felder

**Requirement**: REQ-016 § 3.1 — Equipment-Modell vollstaendig
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Equipment "Bluelab pH Pen" mit allen Feldern angelegt (vgl. TC-016-011)

**Test Steps**:
1. Nutzer klickt auf "Bluelab pH Pen" in der Equipment-Liste
2. Detailseite oeffnet sich

**Expected Results**:
- Sichtbar auf der Detailseite:
  - Name: Bluelab pH Pen
  - Typ: Sensor
  - Marke: Bluelab
  - Modell: pH Pen
  - Seriennummer: BL-PH-2024-0042
  - Kaufdatum: 15.06.2025
  - Garantie bis: 15.06.2027
  - Standort: Growzelt 1
  - Status-Badge: Aktiv
  - Notizen: "Kalibrierung alle 2 Wochen"

**Postconditions**:
- Detailseite von "Bluelab pH Pen" ist offen

**Tags**: [req-016, equipment, detailansicht, vollstaendigkeit]

---

## 4. InvenTree-Part suchen und Entitaeten verlinken

### TC-016-019: InvenTree-Parts suchen (Verknüpfungs-Dialog) — Happy Path

**Requirement**: REQ-016 § 3.7 — GET /browse/parts, § 6 Szenario 2
**Priority**: Critical
**Category**: Happy Path / Dialog
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied oder Admin)
- InvenTree-Verbindung ist aktiv und erreichbar
- Dünger "BioBizz Bio-Bloom" existiert in Kamerplanter
- InvenTree enthaelt Part #42 "BioBizz Bio-Bloom 1L"
- Nutzer befindet sich auf der Detailseite des Duengers "BioBizz Bio-Bloom"

**Test Steps**:
1. Nutzer klickt auf "InvenTree verlinken" oder "+ Part verknuepfen" auf der Duenger-Detailseite
2. Dialog "InvenTree-Part suchen" oeffnet sich
3. Nutzer gibt im Suchfeld ein: `BioBizz`
4. Nutzer wartet auf Suchergebnisse (Loading-Indikator sichtbar waehrend Suche)
5. Nutzer beobachtet die Ergebnisliste

**Expected Results**:
- Ladeindikator erscheint waehrend der Suche
- Suchergebnisse enthalten "BioBizz Bio-Bloom 1L" (Part #42) mit:
  - Part-Name: BioBizz Bio-Bloom 1L
  - IPN (Interner Produktname): FERT-BB-001 (falls vorhanden)
  - Kategorie: z.B. "Duenger"
  - Aktueller Bestand: 12.5 (mit Einheit)
- Sucheingabe muss mindestens 2 Zeichen haben (Validierung: weniger als 2 Zeichen → Suche startet nicht oder zeigt Hinweis "Bitte mindestens 2 Zeichen eingeben")

**Postconditions**:
- Dialog mit Suchergebnissen ist offen

**Tags**: [req-016, browse, part-suche, dialog, happy-path]

---

### TC-016-020: InvenTree-Part suchen — Eingabe unter Mindestlaenge

**Requirement**: REQ-016 § 3.7 — GET /browse/parts?query= (min_length=2)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- Dialog "InvenTree-Part suchen" ist geoeffnet

**Test Steps**:
1. Nutzer gibt im Suchfeld nur ein einzelnes Zeichen ein: `B`
2. Nutzer wartet einen Moment

**Expected Results**:
- Keine Suchanfrage wird ausgeloest
- Hinweistext erscheint: "Bitte mindestens 2 Zeichen eingeben" oder die Suchergebnisliste bleibt leer mit entsprechendem Hinweis
- Kein Fehler-Snackbar

**Postconditions**:
- Dialog unveraendert offen

**Tags**: [req-016, browse, formvalidierung, mindestlaenge]

---

### TC-016-021: Duenger mit InvenTree-Part verlinken — inkl. auto_deduct-Konfiguration

**Requirement**: REQ-016 § 3.4 link_entity, § 6 Szenario 2
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied oder Admin)
- InvenTree-Verbindung aktiv
- Dünger "BioBizz Bio-Bloom" auf Detailseite
- Part-Suche hat "BioBizz Bio-Bloom 1L" (Part #42) gefunden (vgl. TC-016-019)

**Test Steps**:
1. Nutzer waehlt "BioBizz Bio-Bloom 1L" in der Suchergebnisliste aus
2. Optionale Felder erscheinen:
   - "Automatisch abbuchen (auto_deduct)": Checkbox, Nutzer aktiviert diese
   - "Abbuchungseinheit": `ml`
3. Nutzer klickt "Verlinken" oder "Verbindung herstellen"

**Expected Results**:
- Erfolgs-Snackbar: "Duenger wurde erfolgreich mit InvenTree Part verlinkt."
- Auf der Duenger-Detailseite erscheint ein neuer Abschnitt "InvenTree-Bestand":
  - Part-Name: BioBizz Bio-Bloom 1L
  - IPN: FERT-BB-001
  - Aktueller Bestand: 12.5 Liter
  - Zuletzt aktualisiert: [aktuelles Datum/Uhrzeit]
  - auto_deduct: Ja
- Ein "Verlinkung loesen"-Button ist sichtbar

**Postconditions**:
- Dünger "BioBizz Bio-Bloom" ist mit InvenTree Part #42 verlinkt, auto_deduct=true

**Tags**: [req-016, reference, link, duenger, auto-deduct, happy-path]

---

### TC-016-022: InvenTree-Bestandsanzeige in der Duenger-Detailseite

**Requirement**: REQ-016 § 5 Abhaengigkeiten — Bestandswarnung bei niedrigem Duenger-Stock
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Dünger "BioBizz Bio-Bloom" ist mit InvenTree Part #42 verlinkt (vgl. TC-016-021)
- InvenTree-Verbindung ist aktiv

**Test Steps**:
1. Nutzer navigiert zur Detailseite von "BioBizz Bio-Bloom"
2. Nutzer scrollt zum Abschnitt "InvenTree-Bestand"

**Expected Results**:
- Abschnitt "InvenTree-Bestand" ist sichtbar und zeigt:
  - Part-Name: BioBizz Bio-Bloom 1L
  - Bestand: 12.5 l (oder aequivalente Einheitsdarstellung)
  - Zeitstempel "Zuletzt synchronisiert": z.B. "vor 30 Minuten" oder absolutes Datum
- Kein API-Token oder interne ID (ausser Part-Nummer) ist sichtbar

**Postconditions**:
- Detailseite offen

**Tags**: [req-016, reference, bestandsanzeige, duenger, detailansicht]

---

### TC-016-023: Tank mit InvenTree-Part verlinken

**Requirement**: REQ-016 § 1.2 Tank → InvenTree Part (READ only)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- InvenTree-Verbindung aktiv
- Tank "IBC-Container 1000L" existiert in Kamerplanter
- InvenTree enthaelt Part #1089 fuer den Tank

**Test Steps**:
1. Nutzer navigiert zur Tank-Detailseite "IBC-Container 1000L"
2. Nutzer klickt auf "InvenTree verlinken"
3. Nutzer sucht nach "IBC" und waehlt Part #1089 aus
4. Nutzer belaesst auto_deduct deaktiviert (Tank: nur READ)
5. Nutzer klickt "Verlinken"

**Expected Results**:
- Erfolgs-Snackbar: "Tank wurde erfolgreich mit InvenTree Part verlinkt."
- Tank-Detailseite zeigt InvenTree-Seriennummer oder Stock-Item-Info
- auto_deduct ist nicht aktiv — kein automatisches Abbuchen
- Keine "auto_deduct"-Checkbox verpflichtend fuer Tanks

**Postconditions**:
- Tank "IBC-Container 1000L" ist mit InvenTree Part #1089 verlinkt

**Tags**: [req-016, reference, link, tank, happy-path]

---

### TC-016-024: Equipment mit InvenTree-Part verlinken (consumable, auto_deduct)

**Requirement**: REQ-016 § 1.2 Equipment (consumable) → InvenTree (READ + WRITE)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- InvenTree-Verbindung aktiv
- Equipment "H2O2 3% 5L" (Typ: Reinigungsmittel) existiert in Kamerplanter
- InvenTree enthaelt einen passenden Part

**Test Steps**:
1. Nutzer navigiert zur Equipment-Detailseite "H2O2 3% 5L"
2. Nutzer klickt "InvenTree verlinken"
3. Nutzer sucht nach "H2O2" und waehlt den Part aus
4. Nutzer aktiviert "Automatisch abbuchen" und gibt Einheit `ml` ein
5. Nutzer klickt "Verlinken"

**Expected Results**:
- Verlinkung wird bestaetigt (Snackbar)
- Equipment-Detailseite zeigt InvenTree-Bestandsanzeige
- auto_deduct: Ja, Einheit: ml

**Postconditions**:
- Equipment mit InvenTree verlinkt, auto_deduct=true

**Tags**: [req-016, reference, link, equipment, consumable, auto-deduct]

---

### TC-016-025: Verlinkung mit nicht-existierendem InvenTree-Part — Fehlermeldung

**Requirement**: REQ-016 § 3.4 — link_entity raises ValueError wenn Part nicht gefunden
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- InvenTree-Verbindung aktiv
- Dialog "InvenTree-Part suchen" ist geoeffnet
- Part-ID die verlinkt werden soll, existiert nicht in InvenTree

**Test Steps**:
1. Nutzer gibt eine Part-ID manuell ein (falls das Formular eine direkte ID-Eingabe erlaubt): `999999`
2. Nutzer klickt "Verlinken"

**Expected Results**:
- Fehlermeldung (Snackbar oder inline): "InvenTree Part nicht gefunden" oder "Der angegebene Part existiert in InvenTree nicht."
- Keine Verlinkung wird gespeichert

**Postconditions**:
- Keine neue Verlinkung vorhanden

**Tags**: [req-016, reference, fehlermeldung, part-nicht-gefunden]

---

### TC-016-026: Verlinkung loesen (Unlink)

**Requirement**: REQ-016 § 3.7 — DELETE /references/{key}
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Dünger "BioBizz Bio-Bloom" ist mit InvenTree Part #42 verlinkt
- Detailseite des Duengers ist geoeffnet

**Test Steps**:
1. Nutzer klickt auf "Verlinkung loesen" oder "InvenTree-Verbindung entfernen"
2. Ein Bestaetigungs-Dialog erscheint: "Moechten Sie die InvenTree-Verlinkung wirklich aufheben? Bestehende Transaktionen im Log bleiben erhalten."
3. Nutzer klickt "Bestaetigen" / "Ja, loesen"

**Expected Results**:
- Erfolgs-Snackbar: "Verlinkung wurde erfolgreich aufgehoben."
- Der InvenTree-Bestandsabschnitt verschwindet von der Duenger-Detailseite
- Bestehende Transaktionen im Transaktions-Log bleiben erhalten (nicht geloescht)

**Postconditions**:
- Kein Dünger mit InvenTree Part verlinkt; Transaktionshistorie bleibt erhalten

**Tags**: [req-016, reference, unlink, loesen, happy-path]

---

## 5. Synchronisation und Transaktions-Log

### TC-016-027: Manuellen Full-Sync ausloesen

**Requirement**: REQ-016 § 3.7 — POST /sync/trigger
**Priority**: High
**Category**: Happy Path / UI-Feedback
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied oder Admin)
- InvenTree-Verbindung aktiv und erreichbar
- InvenTree-Integrationsseite oder -Einstellungsabschnitt ist geoeffnet

**Test Steps**:
1. Nutzer navigiert zur InvenTree-Integrationsseite oder einem Bereich mit Sync-Steuerung
2. Nutzer klickt auf "Jetzt synchronisieren" oder "Full-Sync starten"
3. Nutzer beobachtet UI-Feedback

**Expected Results**:
- Button zeigt kurz Lade-Zustand (Spinner oder "Synchronisiert...")
- Snackbar erscheint: "Synchronisation wurde gestartet." oder "Sync-Task ausgeloest."
- Hinweis: "Die Synchronisation lauft im Hintergrund. Ergebnisse erscheinen im Transaktions-Log."
- Der Zeitstempel "Letzter Sync" aktualisiert sich nach Abschluss

**Postconditions**:
- Sync-Task wurde ausgeloest; Hintergrundverarbeitung laeuft

**Tags**: [req-016, sync, trigger, happy-path, ui-feedback]

---

### TC-016-028: Einzelne Referenz manuell synchronisieren

**Requirement**: REQ-016 § 3.7 — POST /references/{key}/sync
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Dünger "BioBizz Bio-Bloom" mit InvenTree-Verlinkung existiert
- Detailseite des Duengers ist geoeffnet

**Test Steps**:
1. Im InvenTree-Bestandsabschnitt des Duengers klickt Nutzer auf "Bestand aktualisieren" oder das Refresh-Icon
2. Nutzer beobachtet die Aktualisierung

**Expected Results**:
- Lade-Indikator erscheint kurz am Bestandsfeld oder Refresh-Icon
- Der angezeigte Bestand aktualisiert sich auf den aktuellen InvenTree-Wert
- Zeitstempel "Zuletzt synchronisiert" zeigt aktuelle Zeit

**Postconditions**:
- Bestand der Referenz ist frisch aus InvenTree abgerufen

**Tags**: [req-016, sync, einzelreferenz, refresh, happy-path]

---

### TC-016-029: Transaktions-Log — Listenansicht mit allen Eintraegen

**Requirement**: REQ-016 § 3.7 — GET /transactions, § 2 stock_transactions-Modell
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt (Mitglied oder Admin)
- Mehrere Stock-Transaktionen existieren: mindestens eine "synced", eine "pending", eine "failed"
- Transaktions-Log-Seite oder -Abschnitt ist erreichbar

**Test Steps**:
1. Nutzer navigiert zur Seite "Transaktions-Log" oder oeffnet den Abschnitt (z.B. Tab auf InvenTree-Seite oder `/inventree/transactions`)
2. Nutzer betrachtet die Tabelle

**Expected Results**:
- Tabelle zeigt Spalten mit: Datum/Uhrzeit, Typ (Abbuchen/Hinzufuegen/Inventur), Menge, Einheit, Begruendung, Quell-Ereignis (z.B. "FeedingEvent feed_042"), Status-Badge
- Status-Badges farblich unterschieden:
  - "Ausstehend" (pending) — gelb/orange
  - "Synchronisiert" (synced) — gruen
  - "Fehlgeschlagen" (failed) — rot
- Zeitstempel und Begruendungstext sind lesbar
- Transaktionen sind unveraenderlich — kein "Loeschen"- oder "Bearbeiten"-Button

**Postconditions**:
- Transaktions-Log ist sichtbar

**Tags**: [req-016, transactions, log, listenansicht, immutable]

---

### TC-016-030: Transaktions-Log — nach Status filtern

**Requirement**: REQ-016 § 3.7 — GET /transactions?status={status}
**Priority**: Medium
**Category**: Listenansicht / Filter
**Preconditions**:
- Transaktions-Log-Seite ist offen
- Transaktionen mit verschiedenen Status existieren

**Test Steps**:
1. Nutzer aktiviert Status-Filter und waehlt "Fehlgeschlagen" aus
2. Nutzer beobachtet die gefilterte Liste

**Expected Results**:
- Nur Transaktionen mit Status "Fehlgeschlagen" (failed) werden angezeigt
- Jede angezeigte Transaktion zeigt die Fehlerursache in einem sichtbaren Feld (z.B. "Letzter Fehler: No stock items found")
- Retry-Zaehler ist sichtbar (z.B. "Versuche: 2/3")

**Postconditions**:
- Filter "Fehlgeschlagen" ist aktiv

**Tags**: [req-016, transactions, filter, fehlgeschlagen, listenansicht]

---

### TC-016-031: Transaktions-Log — nach Collection filtern

**Requirement**: REQ-016 § 3.7 — GET /transactions?entity_collection={coll}
**Priority**: Medium
**Category**: Listenansicht / Filter
**Preconditions**:
- Transaktions-Log-Seite ist offen
- Transaktionen aus "feeding_events" und "maintenance_logs" existieren

**Test Steps**:
1. Nutzer aktiviert Collection-Filter und waehlt "Duengeereignisse" (feeding_events)
2. Nutzer beobachtet die Liste

**Expected Results**:
- Nur Transaktionen mit Quell-Collection "Duengeereignisse" sind sichtbar
- Wartungsprotokoll-Transaktionen sind ausgeblendet

**Postconditions**:
- Collection-Filter ist aktiv

**Tags**: [req-016, transactions, filter, collection, feeding-events]

---

## 6. Automatisches Verbrauchstracking (ConsumptionTracker)

### TC-016-032: Verbrauch nach FeedingEvent — Transaktion erscheint im Log

**Requirement**: REQ-016 § 3.5 — ConsumptionTracker.on_feeding_event, § 6 Szenario 3
**Priority**: Critical
**Category**: Zustandswechsel / Happy Path
**Preconditions**:
- Dünger "CalMag" ist mit InvenTree-Part verlinkt, auto_deduct=true, Bestand laut Cache: 500 ml
- Nutzer erstellt ein Duengeereignis (FeedingEvent) mit CalMag: 5 ml/L × 10 L = 50 ml

**Test Steps**:
1. Nutzer navigiert zur Seite fuer Duengeereignisse (z.B. Pflanzdurchlauf-Detail oder Duengungsplan)
2. Nutzer erstellt ein neues Duengeereignis mit CalMag, Menge 50 ml
3. Nutzer speichert das Duengeereignis
4. Nutzer navigiert zum Transaktions-Log (InvenTree-Bereich)
5. Nutzer sucht den neuen Eintrag

**Expected Results**:
- Im Transaktions-Log erscheint ein neuer Eintrag:
  - Typ: "Abbuchen" (remove)
  - Menge: 50 ml
  - Begruendung: enthaelt Hinweis auf das Duengeereignis und Dünger "CalMag"
  - Status: "Ausstehend" (pending)
  - Quell-Ereignis: Referenz auf das erstellte FeedingEvent sichtbar
- Nach dem naechsten automatischen Push-Lauf (max. 5 Minuten) oder manuellem Sync-Trigger (vgl. TC-016-027) wechselt Status auf "Synchronisiert" (synced)

**Postconditions**:
- Transaktion im Log mit Status "Ausstehend" oder "Synchronisiert"

**Tags**: [req-016, consumption-tracker, feeding-event, auto-deduct, transactions]

---

### TC-016-033: Kein Duengeereignis-Tracking fuer Duenger ohne auto_deduct

**Requirement**: REQ-016 § 3.5 — ConsumptionTracker prueft auto_deduct vor Erstellung
**Priority**: High
**Category**: Zustandswechsel (negativ)
**Preconditions**:
- Dünger "BioBloom" ist mit InvenTree verlinkt, aber auto_deduct=false
- Nutzer erstellt ein FeedingEvent mit BioBloom

**Test Steps**:
1. Nutzer erstellt ein Duengeereignis mit dem Dünger "BioBloom"
2. Nutzer navigiert zum Transaktions-Log

**Expected Results**:
- Im Transaktions-Log erscheint KEIN neuer Eintrag fuer "BioBloom"
- Das Duengeereignis selbst wird normal gespeichert
- Kein Fehler oder Warnung erscheint

**Postconditions**:
- Duengeereignis gespeichert, keine neue Transaktion im Log

**Tags**: [req-016, consumption-tracker, auto-deduct-false, negativ]

---

### TC-016-034: Verbrauch nach Wartungsprotokoll (MaintenanceLog) — Transaktion erscheint im Log

**Requirement**: REQ-016 § 3.5 — ConsumptionTracker.on_maintenance_log, § 6 Szenario 7
**Priority**: High
**Category**: Zustandswechsel / Happy Path
**Preconditions**:
- Equipment "H2O2 3% 5L" (Typ: Reinigungsmittel) mit InvenTree-Ref (auto_deduct=true) existiert
- Ein Tank mit Wartungsprotokoll (MaintenanceLog, Typ: Desinfektion) existiert

**Test Steps**:
1. Nutzer erstellt ein Wartungsprotokoll fuer den Tank (Typ: Desinfektion)
2. Nutzer fuegt im Protokoll das Produkt "H2O2 3% 5L", Menge 250 ml hinzu
3. Nutzer speichert das Wartungsprotokoll
4. Nutzer navigiert zum Transaktions-Log

**Expected Results**:
- Im Transaktions-Log erscheint ein neuer Eintrag:
  - Typ: "Abbuchen" (remove)
  - Menge: 250 ml
  - Begruendung: enthaelt Hinweis auf das Wartungsprotokoll und "H2O2 3% 5L"
  - Status: "Ausstehend" (pending)

**Postconditions**:
- Transaktion fuer H2O2-Verbrauch im Log

**Tags**: [req-016, consumption-tracker, maintenance-log, auto-deduct]

---

### TC-016-035: FeedingEvent ohne InvenTree-Verlinkung — kein Blocking

**Requirement**: REQ-016 § 1 — Optionalitaet: InvenTree blockiert keine Kernfunktionen
**Priority**: Critical
**Category**: Graceful Degradation
**Preconditions**:
- Kein Dünger ist mit InvenTree verlinkt ODER InvenTree-Verbindung ist nicht konfiguriert
- Nutzer erstellt ein normales Duengeereignis

**Test Steps**:
1. Nutzer navigiert zur Duengungsfunktion
2. Nutzer erstellt ein FeedingEvent mit beliebigem Dünger
3. Nutzer speichert

**Expected Results**:
- Das FeedingEvent wird OHNE Fehler gespeichert
- Kein InvenTree-bezogener Fehler oder Warnung erscheint
- Keine Verzoegerung oder Blockierung durch fehlende InvenTree-Konfiguration

**Postconditions**:
- FeedingEvent normal gespeichert

**Tags**: [req-016, graceful-degradation, feeding-event, optionalitaet]

---

## 7. Graceful Degradation bei InvenTree-Ausfall

### TC-016-036: InvenTree-Server nicht erreichbar — Kernfunktionen weiterhin verfuegbar

**Requirement**: REQ-016 § 1 — Optionalitaet, § 6 Szenario 4 — Graceful Degradation
**Priority**: Critical
**Category**: Graceful Degradation
**Preconditions**:
- InvenTree-Verbindung konfiguriert
- InvenTree-Server ist NICHT erreichbar (simulierter Ausfall)
- Dünger "CalMag" mit InvenTree-Verlinkung, auto_deduct=true

**Test Steps**:
1. Nutzer erstellt ein FeedingEvent mit CalMag 50 ml
2. Nutzer speichert das FeedingEvent
3. Nutzer navigiert zum Transaktions-Log

**Expected Results**:
- Das FeedingEvent wird OHNE Fehler oder Warnung ueber InvenTree-Ausfall gespeichert
- Im Transaktions-Log erscheint die neue Transaktion mit Status "Ausstehend" (pending)
- Keine blockierende Fehlermeldung unterbricht den Speichervorgang
- Nach Health-Check (vgl. TC-016-008) zeigt die Verbindungsseite Status "Nicht verbunden"

**Postconditions**:
- FeedingEvent gespeichert; Transaktion steht im Log als "Ausstehend"

**Tags**: [req-016, graceful-degradation, ausfall, pending-transaction]

---

### TC-016-037: InvenTree-Bestandsanzeige bei nicht erreichbarem Server — Cache-Wert angezeigt

**Requirement**: REQ-016 § 2 — inventree_references.cached_stock (lokaler Cache)
**Priority**: High
**Category**: Graceful Degradation / Detailansicht
**Preconditions**:
- Dünger "BioBizz Bio-Bloom" mit InvenTree-Verlinkung, cached_stock=12.5 l
- InvenTree-Server NICHT erreichbar

**Test Steps**:
1. Nutzer navigiert zur Detailseite von "BioBizz Bio-Bloom"
2. Nutzer betrachtet den InvenTree-Bestandsabschnitt

**Expected Results**:
- Der letzte bekannte Bestand (Cache) wird angezeigt: 12.5 l
- Ein Hinweistext oder Icon zeigt an, dass der Wert moeglicherweise veraltet ist: "Zuletzt synchronisiert: [Zeitstempel]" oder "Bestand nicht aktuell — Verbindung nicht verfuegbar"
- Kein Fehler-Snackbar der die Seite blockiert

**Postconditions**:
- Seite bleibt bedienbar

**Tags**: [req-016, graceful-degradation, cache, veraltet, bestandsanzeige]

---

### TC-016-038: Fehlgeschlagene Transaktion — Retry-Zaehler sichtbar

**Requirement**: REQ-016 § 3.4 — push_pending_transactions: max 3 Versuche
**Priority**: High
**Category**: Fehlermeldung / Transaktions-Log
**Preconditions**:
- InvenTree-Server war beim letzten Sync-Lauf nicht erreichbar
- Eine Transaktion hat bereits 2 fehlgeschlagene Versuche (retry_count=2)

**Test Steps**:
1. Nutzer navigiert zum Transaktions-Log
2. Nutzer filtert nach Status "Fehlgeschlagen"
3. Nutzer betrachtet die fehlgeschlagene Transaktion

**Expected Results**:
- Transaktion zeigt Retry-Zaehler: "Versuche: 2 von 3" oder aequivalente Anzeige
- Letzter Fehler ist sichtbar: z.B. "Verbindung abgelehnt" oder "InvenTree nicht erreichbar"
- Nach 3 fehlgeschlagenen Versuchen: Status wechselt zu "Fehlgeschlagen" (endgueltig, kein weiterer automatischer Retry)

**Postconditions**:
- Transaktion mit Retry-Zaehler sichtbar

**Tags**: [req-016, retry, fehlgeschlagen, transactions, log]

---

## 8. InvenTree-Kategorien-Browser

### TC-016-039: InvenTree-Kategorien anzeigen im Verknuepfungs-Dialog

**Requirement**: REQ-016 § 3.7 — GET /browse/categories
**Priority**: Medium
**Category**: Dialog / Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- InvenTree-Verbindung aktiv
- Dialog "InvenTree-Part suchen" ist geoeffnet

**Test Steps**:
1. Nutzer klickt auf "Kategorien durchsuchen" oder "Nach Kategorie filtern" im Suchen-Dialog
2. Nutzer betrachtet die Kategorienliste

**Expected Results**:
- Kategorieliste aus InvenTree wird geladen und dargestellt (z.B. "Duenger", "Sensoren", "Werkzeuge")
- Nutzer kann eine Kategorie anklicken, um die Part-Suche auf diese Kategorie einzuschraenken
- Nach Kategorieauswahl werden nur Parts der gewahlten Kategorie in der Suche zurueckgegeben

**Postconditions**:
- Kategorie-Filter ist aktiv im Suchen-Dialog

**Tags**: [req-016, browse, kategorien, dialog, filter]

---

## 9. Sicherheit — API-Token-Schutz

### TC-016-040: API-Token wird in der UI niemals im Klartext angezeigt

**Requirement**: REQ-016 § 4.1 — IT-002 Token darf nicht in API-Responses/UI erscheinen
**Priority**: Critical
**Category**: Sicherheit
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- InvenTree-Verbindung "Haupt-Inventar" mit API-Token ist gespeichert

**Test Steps**:
1. Nutzer navigiert zur Detailseite der Verbindung "Haupt-Inventar"
2. Nutzer liest alle sichtbaren Felder der Seite
3. Nutzer klickt auf "Bearbeiten"
4. Nutzer betrachtet das API-Token-Feld im Bearbeitungs-Formular

**Expected Results**:
- In der Detailansicht: API-Token-Feld zeigt entweder "••••••••" (Maskierung) oder ist gar nicht sichtbar; KEIN Klartext
- Im Bearbeitungs-Formular: Token-Feld ist leer (Eingabe neues Token erforderlich zum Aendern) ODER zeigt Maskierung
- Unter keinen Umstaenden erscheint der Klartext-Token auf der Seite
- URL, Name, Sync-Intervall sind weiterhin lesbar

**Postconditions**:
- Kein Klartext-Token sichtbar

**Tags**: [req-016, sicherheit, token-masking, api-token, admin]

---

### TC-016-041: API-Token aendern (Token-Rotation) ohne Neuanlage der Verbindung

**Requirement**: REQ-016 § 4.1 — IT-004 Token-Rotation soll unterstuetzt werden
**Priority**: Medium
**Category**: Happy Path / Sicherheit
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- InvenTree-Verbindung "Haupt-Inventar" existiert
- Bearbeitungs-Dialog ist geoeffnet

**Test Steps**:
1. Nutzer klickt auf "Bearbeiten" bei der Verbindung "Haupt-Inventar"
2. Nutzer gibt im Feld "API-Token aktualisieren" oder "Neuer Token" einen neuen Token-Wert ein: `inv-new-token-xyz789`
3. Nutzer laesst alle anderen Felder unveraendert
4. Nutzer klickt "Speichern"

**Expected Results**:
- Erfolgs-Snackbar: "Verbindung wurde aktualisiert."
- Verbindung bleibt bestehen (wird nicht neu angelegt)
- Alle bestehenden Verlinkungen (Referenzen) bleiben erhalten
- Der neue Token wird maskiert gespeichert — kein Klartext sichtbar

**Postconditions**:
- Verbindung nutzt neuen Token; alle bestehenden Referenzen unveraendert

**Tags**: [req-016, token-rotation, sicherheit, admin, it-004]

---

## 10. Referenz-Uebersicht (Alle Verlinkungen)

### TC-016-042: Alle InvenTree-Referenzen in der Uebersicht anzeigen

**Requirement**: REQ-016 § 3.7 — GET /references
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mehrere Entitaeten sind verlinkt: 1 Dünger, 1 Tank, 2 Equipment-Eintraege

**Test Steps**:
1. Nutzer navigiert zur Seite "InvenTree-Verlinkungen" oder einem entsprechenden Abschnitt
2. Nutzer betrachtet die Uebersichtstabelle

**Expected Results**:
- Tabelle zeigt alle 4 Verlinkungen mit Spalten:
  - Entitaet (z.B. "Dünger: BioBizz Bio-Bloom")
  - InvenTree-Part-Name
  - IPN (falls vorhanden)
  - Aktueller Bestand (Cache) mit Einheit und Zeitstempel
  - auto_deduct (Ja/Nein)
- Jede Zeile hat einen "Sync"-Button (Einzelreferenz) und einen "Loesen"-Button

**Postconditions**:
- Referenz-Uebersicht sichtbar

**Tags**: [req-016, references, uebersicht, listenansicht]

---

### TC-016-043: Referenzen nach Collection filtern (nur Duenger anzeigen)

**Requirement**: REQ-016 § 3.7 — GET /references?entity_collection=fertilizers
**Priority**: Medium
**Category**: Listenansicht / Filter
**Preconditions**:
- Referenz-Uebersicht mit Duengern, Tanks und Equipment-Verlinkungen ist offen

**Test Steps**:
1. Nutzer aktiviert Filter "Entitaetstyp" und waehlt "Duenger" aus
2. Nutzer betrachtet die gefilterte Liste

**Expected Results**:
- Nur Duenger-Verlinkungen werden angezeigt
- Tank- und Equipment-Verlinkungen sind ausgeblendet
- Filter-Chip zeigt "Typ: Duenger"

**Postconditions**:
- Filter ist aktiv

**Tags**: [req-016, references, filter, collection, duenger]

---

## 11. Synchronisations-Protokoll (Stock-Sync)

### TC-016-044: Nach erfolgreichem Stock-Sync — Bestandswerte aktualisiert

**Requirement**: REQ-016 § 3.4 — sync_stock_levels, § 6 Szenario 6
**Priority**: High
**Category**: Zustandswechsel / Happy Path
**Preconditions**:
- Dünger "BioGrow" mit Verlinkung, cached_stock=1000 ml
- InvenTree zeigt aktuell 900 ml (leichte Abweichung < 20%)
- Nutzer loest manuellen Sync aus (vgl. TC-016-027) oder wartet auf automatischen Lauf

**Test Steps**:
1. Nutzer loest Full-Sync aus (klickt "Jetzt synchronisieren")
2. Nutzer wartet auf Abschluss (oder refresht nach einigen Sekunden)
3. Nutzer navigiert zur Duenger-Detailseite von "BioGrow"

**Expected Results**:
- Bestandsanzeige auf der Duenger-Detailseite zeigt 900 ml
- Zeitstempel "Zuletzt synchronisiert" ist auf aktuelle Zeit aktualisiert
- Keine Warnung fuer Drift (< 20% Abweichung)

**Postconditions**:
- cached_stock = 900 ml in Anzeige

**Tags**: [req-016, sync, stock-levels, bestandsaktualisierung]

---

### TC-016-045: Drift-Warnung bei mehr als 20% Bestandsabweichung

**Requirement**: REQ-016 § 3.4 — STOCK_DRIFT_THRESHOLD = 0.20, § 6 Szenario 6
**Priority**: High
**Category**: Fehlermeldung / UI-Feedback
**Preconditions**:
- Dünger "BioGrow" mit cached_stock=1000 ml
- InvenTree zeigt nach Sync 750 ml (25% Abweichung > 20% Schwellwert)

**Test Steps**:
1. Nutzer loest Full-Sync aus
2. Nutzer betrachtet die Sync-Ergebnisanzeige oder Detailseite von "BioGrow"

**Expected Results**:
- Eine Drift-Warnung erscheint in der Sync-Ergebnisanzeige oder als Hinweis auf der Detailseite:
  - Entitaet: BioGrow
  - Alter Bestand: 1000 ml, Neuer Bestand: 750 ml
  - Abweichung: 25%
  - Meldung: "Bestandsabweichung von 25% festgestellt. Bitte pruefen Sie Ihren InvenTree-Bestand."
- Bestand wird dennoch auf 750 ml aktualisiert (keine Blockierung)

**Postconditions**:
- Bestand auf 750 ml aktualisiert; Drift-Warnung sichtbar

**Tags**: [req-016, sync, drift, warnung, 20-prozent-schwelle]

---

## 12. Berechtigungen fuer Equipment-Verwaltung

### TC-016-046: Admin kann Equipment loeschen

**Requirement**: REQ-016 § 4 — Auth-Matrix: Equipment-Loeschen nur Admin
**Priority**: High
**Category**: Zugangskontrolle
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Equipment "Bluelab pH Pen" existiert

**Test Steps**:
1. Nutzer navigiert zur Equipment-Listenseite
2. Nutzer klickt auf den Loeschen-Button oder das Papierkorb-Icon bei "Bluelab pH Pen"
3. Bestaetigungs-Dialog erscheint: "Sind Sie sicher, dass Sie 'Bluelab pH Pen' loeschen moechten? Diese Aktion kann nicht rueckgaengig gemacht werden."
4. Nutzer klickt "Loeschen"

**Expected Results**:
- Erfolgs-Snackbar: "Equipment wurde geloescht."
- "Bluelab pH Pen" erscheint nicht mehr in der Equipment-Liste

**Postconditions**:
- Equipment "Bluelab pH Pen" ist geloescht

**Tags**: [req-016, equipment, loeschen, admin, rbac]

---

### TC-016-047: Mitglied kann Equipment NICHT loeschen

**Requirement**: REQ-016 § 4 — Auth-Matrix: Equipment-Loeschen nur Admin
**Priority**: High
**Category**: Zugangskontrolle
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Mitglied" (nicht Admin)
- Equipment "Juno Pumpe" existiert

**Test Steps**:
1. Nutzer navigiert zur Equipment-Listenseite
2. Nutzer sucht nach einem Loeschen-Button bei "Juno Pumpe"

**Expected Results**:
- Loeschen-Button/-Icon ist NICHT sichtbar oder ist deaktiviert fuer Mitglieder
- Kein Loeschen moeglich

**Postconditions**:
- Equipment "Juno Pumpe" weiterhin vorhanden

**Tags**: [req-016, equipment, loeschen-verboten, mitglied, rbac]

---

## 13. Integration in bestehende Entity-Detailseiten

### TC-016-048: InvenTree-Bestandsabschnitt in Tank-Detailseite sichtbar (wenn verlinkt)

**Requirement**: REQ-016 § 5 Abhaengigkeiten — Tank-Detailseite zeigt InvenTree-Bestand
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Tank "IBC-Container 1000L" ist mit InvenTree Part #1089 verlinkt (vgl. TC-016-023)
- Tank-Detailseite ist geoeffnet

**Test Steps**:
1. Nutzer navigiert zur Tank-Detailseite von "IBC-Container 1000L"
2. Nutzer scrollt zum InvenTree-Abschnitt

**Expected Results**:
- Abschnitt "InvenTree" oder "Bestandsinfo" zeigt:
  - Part-Name: z.B. "IBC-Container 1000L"
  - Seriennummer / Stock-Item (falls trackable)
  - Letzter Sync-Zeitstempel
- "Verlinkung loesen"-Option vorhanden

**Postconditions**:
- Tank-Detailseite mit InvenTree-Abschnitt sichtbar

**Tags**: [req-016, tank, detailansicht, inventree-bestand]

---

### TC-016-049: Keine InvenTree-Abschnitte auf Entitaetsseiten wenn InvenTree nicht konfiguriert

**Requirement**: REQ-016 § 1 — Optionalitaet: keine UI-Beeintraechtigung ohne InvenTree
**Priority**: Critical
**Category**: Feature-Toggle
**Preconditions**:
- InvenTree-Verbindung ist NICHT konfiguriert
- Dünger-Detailseite und Tank-Detailseite sind zugaenglich

**Test Steps**:
1. Nutzer oeffnet Duenger-Detailseite eines beliebigen Duengers
2. Nutzer scrollt durch die gesamte Seite
3. Nutzer oeffnet Tank-Detailseite eines beliebigen Tanks
4. Nutzer scrollt durch die gesamte Seite

**Expected Results**:
- Weder auf der Duenger- noch auf der Tank-Detailseite erscheint ein InvenTree-Abschnitt, "Verlinkung"-Button oder Bestandsinfo
- Keine InvenTree-bezogenen Fehlermeldungen erscheinen
- Alle anderen Seitenabschnitte (Nährwerte, Phasenkonfiguration, etc.) sind unveraendert sichtbar

**Postconditions**:
- Keine Aenderungen

**Tags**: [req-016, feature-toggle, optionalitaet, kein-inventree]

---

## 14. End-to-End-Nutzungsszenarien

### TC-016-050: Vollstaendiger Workflow: Duenger verlinken → Duengen → Transaktion im Log pruefen

**Requirement**: REQ-016 § 6 Szenarien 2 und 3 kombiniert
**Priority**: Critical
**Category**: Happy Path / End-to-End
**Preconditions**:
- Nutzer ist eingeloggt
- InvenTree-Verbindung aktiv und erreichbar
- Dünger "CalMag" in Kamerplanter vorhanden
- InvenTree-Part "CalMag 500ml" (Part #55) mit Bestand 500 ml vorhanden
- Aktiver Pflanzdurchlauf mit mindestens einer Pflanze existiert

**Test Steps**:
1. Nutzer navigiert zur Duenger-Detailseite "CalMag"
2. Nutzer klickt "InvenTree verlinken", sucht "CalMag" und waehlt Part #55
3. Nutzer aktiviert "Automatisch abbuchen", Einheit: `ml`, bestaetigt Verlinkung
4. Nutzer navigiert zur Duengungsseite des Pflanzdurchlaufs
5. Nutzer erstellt ein FeedingEvent: CalMag 5 ml/L × 10 L = 50 ml, speichert
6. Nutzer navigiert zum InvenTree-Transaktions-Log
7. Nutzer prueft den neuen Eintrag
8. Nutzer loest manuellen Sync aus (TC-016-027)
9. Nutzer navigiert zur Duenger-Detailseite "CalMag" und prueft Bestand

**Expected Results**:
- Schritt 3: Verlinkung bestaetigt, Bestandsanzeige 500 ml sichtbar
- Schritt 5: FeedingEvent gespeichert ohne Fehler
- Schritt 7: Transaktion "Abbuchen 50 ml, CalMag, Status: Ausstehend" sichtbar
- Schritt 8: Sync-Bestaetigung
- Schritt 9: Bestand zeigt 450 ml (nach InvenTree-Sync), Status der Transaktion "Synchronisiert"

**Postconditions**:
- CalMag mit Bestand 450 ml in Kamerplanter-Anzeige; Transaktion im Log "Synchronisiert"

**Tags**: [req-016, e2e, workflow, duenger, verlinkung, feeding-event, sync]

---

### TC-016-051: Vollstaendiger Workflow: Equipment anlegen → Location zuordnen → In Location-Ansicht pruefen

**Requirement**: REQ-016 § 6 Szenario 5
**Priority**: High
**Category**: Happy Path / End-to-End
**Preconditions**:
- Nutzer ist eingeloggt
- Location "Growzelt 1" existiert

**Test Steps**:
1. Nutzer navigiert zur Equipment-Listenseite
2. Nutzer legt Equipment "Bluelab pH Pen" an (Typ: Sensor, Standort: Growzelt 1, vgl. TC-016-011)
3. Nutzer navigiert zur Standort-Detailseite von "Growzelt 1"
4. Nutzer sucht auf der Standort-Detailseite nach einem Equipment-Abschnitt oder Tab "Equipment"
5. Nutzer betrachtet die Liste

**Expected Results**:
- In der Standort-Detailseite "Growzelt 1" erscheint "Bluelab pH Pen" im Equipment-Abschnitt
- Typ (Sensor) und Status (Aktiv) sind sichtbar
- Klick auf "Bluelab pH Pen" fuehrt zur Equipment-Detailseite

**Postconditions**:
- Equipment "Bluelab pH Pen" sichtbar in Standort-Ansicht "Growzelt 1"

**Tags**: [req-016, e2e, equipment, location, standort-ansicht]

---

### TC-016-052: Vollstaendiger Admin-Workflow: Verbindung anlegen → Health-Check → Verlinkung testen → Sync

**Requirement**: REQ-016 § 6 alle Szenarien kombiniert
**Priority**: Critical
**Category**: Happy Path / End-to-End / Admin
**Preconditions**:
- Nutzer ist eingeloggt mit Admin-Rolle
- Noch keine InvenTree-Verbindung konfiguriert
- InvenTree-Server ist erreichbar

**Test Steps**:
1. Nutzer navigiert zu Admin-Bereich > Integrationen > InvenTree
2. Nutzer legt neue Verbindung an (Name: "Haupt-Inventar", URL, Token, SSL: aktiv)
3. Nutzer klickt "Verbindung testen" — geprueft (TC-016-007)
4. Nutzer navigiert zu einem Dünger und verlinkt ihn mit einem InvenTree-Part (TC-016-021)
5. Nutzer navigiert zu Equipment und legt "pH Pen" an mit Standort (TC-016-011)
6. Nutzer verlinkt "pH Pen" mit einem InvenTree-Part (TC-016-024)
7. Nutzer navigiert zur InvenTree-Seite und loest Full-Sync aus (TC-016-027)
8. Nutzer prueft Transaktions-Log (TC-016-029)

**Expected Results**:
- Schritt 2: Verbindung angelegt, Token maskiert
- Schritt 3: Verbindungs-Status "Gesund"
- Schritt 4: Verlinkung mit Bestandsanzeige sichtbar
- Schritt 5: Equipment in Liste, Standort "Growzelt 1" zugeordnet
- Schritt 6: Equipment-Verlinkung bestaetigt
- Schritt 7: Sync gestartet, Bestaetigung sichtbar
- Schritt 8: Transaktions-Log zeigt Sync-Ergebnisse mit Status "Synchronisiert"

**Postconditions**:
- Vollstaendig konfigurierte InvenTree-Integration mit Verlinkungen, Health-Check "Gesund", Sync erfolgreich

**Tags**: [req-016, e2e, admin, vollstaendiger-workflow, setup]

---

## Abdeckungs-Matrix

| Spec-Abschnitt | Beschreibung | Testfaelle |
|---------------|-------------|------------|
| § 1 Optionalitaet / Feature-Toggle | Keine UI-Beeintraechtigung ohne InvenTree | TC-016-001, TC-016-049 |
| § 1 Equipment als First-Class-Entity | Navigation, Menueintrag | TC-016-002 |
| § 3.1 Enums & Modelle — InvenTreeConnection | Formularvalidierung, SSL-Warnung | TC-016-003, TC-016-004, TC-016-005, TC-016-006 |
| § 3.1 Enums — EquipmentType | Dropdown-Vollstaendigkeit | TC-016-013 |
| § 3.1 Enums — EquipmentStatus | Status-Lifecycle, Dropdown | TC-016-014, TC-016-015 |
| § 3.4 InvenTreeSyncEngine — link_entity | Verlinkung Duenger/Tank/Equipment | TC-016-021, TC-016-023, TC-016-024, TC-016-025 |
| § 3.4 InvenTreeSyncEngine — sync_stock_levels | Stock-Pull, Drift-Detection | TC-016-044, TC-016-045 |
| § 3.4 InvenTreeSyncEngine — push_pending_transactions | Transaction-Push, Retry | TC-016-036, TC-016-038 |
| § 3.5 ConsumptionTracker — on_feeding_event | Automatisches Tracking nach Duengung | TC-016-032, TC-016-033, TC-016-035 |
| § 3.5 ConsumptionTracker — on_tank_fill_event | Automatisches Tracking nach Tankbefuellung | (integriert in TC-016-035) |
| § 3.5 ConsumptionTracker — on_maintenance_log | Tracking nach Wartungsprotokoll | TC-016-034 |
| § 3.7 Connection-CRUD (5 Endpoints) | Anlegen, Bearbeiten, Health-Check | TC-016-003, TC-016-007, TC-016-008, TC-016-009 |
| § 3.7 Referenz-Management (4 Endpoints) | Verlinken, Loesen, Uebersicht, Filter | TC-016-021, TC-016-026, TC-016-042, TC-016-043 |
| § 3.7 InvenTree-Browse (2 Endpoints) | Part-Suche, Kategorien-Browser | TC-016-019, TC-016-020, TC-016-039 |
| § 3.7 Sync & Transaktions-Log (2 Endpoints) | Manueller Sync, Log-Anzeige | TC-016-027, TC-016-028, TC-016-029, TC-016-030, TC-016-031 |
| § 3.7 Equipment-CRUD (5 Endpoints) | Anlegen, Bearbeiten, Filtern, Detail | TC-016-011, TC-016-012, TC-016-016, TC-016-017, TC-016-018 |
| § 4 Auth-Matrix | Admin/Mitglied-Berechtigungen | TC-016-010, TC-016-046, TC-016-047 |
| § 4.1 Sicherheit — IT-002 Token-Masking | Token nie im Klartext | TC-016-040 |
| § 4.1 Sicherheit — IT-003 SSL-Warnung | Warnung bei verify_ssl=false | TC-016-006 |
| § 4.1 Sicherheit — IT-004 Token-Rotation | Token aendern ohne Neuanlage | TC-016-041 |
| § 4.1 Sicherheit — IT-006 generische Fehlermeldung | Health-Check kein Informations-Leak | TC-016-008 |
| § 5 Bestandsanzeige in Duenger/Tank-Seiten | InvenTree-Abschnitt in bestehenden Seiten | TC-016-022, TC-016-048 |
| § 6 Szenario 1 | Verbindung anlegen + Health-Check | TC-016-003, TC-016-007 |
| § 6 Szenario 2 | Duenger verlinken | TC-016-019, TC-016-021 |
| § 6 Szenario 3 | Bestandsreduktion nach FeedingEvent | TC-016-032 |
| § 6 Szenario 4 | Graceful Degradation bei Ausfall | TC-016-036, TC-016-037, TC-016-038 |
| § 6 Szenario 5 | Equipment anlegen und Location zuordnen | TC-016-011, TC-016-051 |
| § 6 Szenario 6 | Stock-Sync mit Drift-Warning | TC-016-044, TC-016-045 |
| § 6 Szenario 7 | Wartungsprodukt-Verbrauch | TC-016-034 |
| End-to-End Szenarien | Kombinierte Workflows | TC-016-050, TC-016-051, TC-016-052 |

**Gesamtanzahl Testfaelle: 52**

**Prioritaetsverteilung:**
- Critical: TC-016-001, 003, 007, 011, 019, 021, 029, 032, 035, 036, 040, 049, 050, 052 — 14 Testfaelle
- High: TC-016-002, 004, 005, 006, 008, 009, 010, 014, 016, 018, 022, 023, 024, 025, 026, 027, 030, 033, 034, 037, 038, 044, 045, 046, 047, 048 — 26 Testfaelle
- Medium: TC-016-012, 013, 015, 017, 020, 028, 031, 039, 041, 042, 043, 051 — 12 Testfaelle

**MUSS-Anforderungen ohne Happy-Path (offen / als Spec-Risiko markiert):**
- Rate-Limiting 60 req/min (IT-005): Nicht UI-testbar — Backend-Verhalten, kein visuelles Signal definiert in Spec v1.0
- TankFillEvent-Consumption-Tracking: Kein explizites UI-Szenario in Spec — TC-016-035 deckt Negativ-Szenario ab; positiver E2E-Test haengt von TankFillEvent-UI-Implementation ab
