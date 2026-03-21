---
req_id: REQ-027
title: Light-Modus (Anonymer Zugang)
category: Plattform & Deployment
test_count: 52
coverage_areas:
  - Erster App-Start im Light-Modus (Seed-Logik)
  - Keine Login-Pflicht (anonymer Zugang)
  - Onboarding-Wizard ohne Login-Schritt
  - Feature-Visibility-Matrix (ausgeblendete UI-Elemente)
  - Routing im Light-Modus (/login, /register nicht erreichbar)
  - AppBar-Anpassungen (kein User-Avatar, kein Tenant-Switcher)
  - Sidebar-Anpassungen (keine Mitglieder-/Einladungs-Links)
  - AccountSettingsPage im Light-Modus (nur Sprache + Erfahrungsstufe)
  - Vollstaendige Kernfunktionalitaet (Pflanzen, Standorte, Aufgaben, IPM, Ernte)
  - Aufgaben ohne User-Zuweisung
  - Externe Anreicherung deaktiviert (ENABLE_ENRICHMENT_LIGHTMODE)
  - Moduswechsel Upgrade Light-auf-Full
  - Uebernahme-Dialog nach Upgrade (accept=true / accept=false)
  - Moduswechsel Downgrade Full-auf-Light
  - Roundtrip Light-Full-Light-Full
  - GET /api/v1/mode Endpunkt
  - Idempotenz der Seed-Logik
  - Mehrgeraete-Zugriff im LAN (kein Login pro Geraet)
generated: 2026-03-21
version: "1.2"
---

# TC-REQ-027: Light-Modus (Anonymer Zugang)

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-027 Light-Modus v1.2**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in den Testschritten. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

Der Light-Modus ist ein Deployment-Modus fuer lokale Instanzen (Raspberry Pi, Home-Server, Docker Compose), bei dem Auth, Tenants und DSGVO-Consent deaktiviert sind. Die App oeffnet sich sofort ohne Login. Ein System-User und ein System-Tenant werden beim ersten Start automatisch erzeugt.

---

## 1. Erster App-Start im Light-Modus

### TC-027-001: App-Start ohne Login-Screen — Direktweiterleitung zum Dashboard

**Requirement**: REQ-027 § 1.1 Szenario 1, AK-01, FK-01
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light` und `VITE_KAMERPLANTER_MODE=light`
- Frische Instanz (keine DB-Eintraege vorhanden)
- Nutzer oeffnet den Browser

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173` (oder der entsprechenden Server-Adresse)

**Erwartete Ergebnisse**:
- Die App laedt und leitet sofort auf `/t/mein-garten/dashboard` weiter
- Es erscheint **kein** Login-Formular
- Es erscheint **keine** Registrierungsseite
- Es erscheint **kein** DSGVO-Consent-Banner
- Das Dashboard ist direkt sichtbar und vollstaendig bedienbar

**Nachbedingungen**:
- System-User (`system@local`, display_name="Gaertner") ist in der Datenbank angelegt
- System-Tenant (slug="mein-garten", name="Mein Garten") ist in der Datenbank angelegt
- System-User hat admin-Membership in System-Tenant und Platform-Tenant

**Tags**: [req-027, light-modus, app-start, login-screen, seed-logik, ak-01, fk-01]

---

### TC-027-002: Onboarding-Wizard startet beim ersten App-Start ohne Login-Schritt

**Requirement**: REQ-027 § 1.1 Szenario 3, § 7.5, AK-06
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Erster Start der App — Onboarding wurde noch nicht abgeschlossen

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173`
2. Nutzer betrachtet den geladenen Bildschirminhalt

**Erwartete Ergebnisse**:
- Der Onboarding-Wizard (REQ-020) wird angezeigt
- Der Wizard beginnt direkt bei Schritt 1 "Erfahrungsstufe" — kein vorheriger "Account erstellen"-Schritt
- Alle Onboarding-Schritte (Erfahrungsstufe, Starter-Kit, Standort, ggf. Wasser) sind navigierbar
- Nach Abschluss des Wizards werden die Pflanzen/der Standort sofort angezeigt

**Nachbedingungen**:
- Onboarding-Status ist als abgeschlossen gespeichert
- Beim naechsten App-Start erscheint der Wizard nicht mehr

**Tags**: [req-027, light-modus, onboarding, wizard, login-schritt-uebersprungen, ak-06]

---

### TC-027-003: Zweiter App-Start — Seed-Logik ist idempotent

**Requirement**: REQ-027 § 3.5, AK-03
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- App wurde bereits einmal gestartet (System-User + System-Tenant existieren)
- Nutzer hat eine Pflanze angelegt

**Testschritte**:
1. Nutzer beendet den Browser und startet ihn neu
2. Nutzer navigiert erneut zu `http://localhost:5173`

**Erwartete Ergebnisse**:
- Die App laedt und leitet auf `/t/mein-garten/dashboard` weiter — ohne Login
- Die zuvor angelegte Pflanze ist noch sichtbar (Daten sind erhalten)
- Es erscheinen keine Fehlermeldungen bezueglich Duplikaten oder Konflikten
- Die App verhaelt sich identisch wie beim ersten Start

**Nachbedingungen**:
- Keine neuen System-User oder System-Tenants wurden angelegt (keine Duplikate)

**Tags**: [req-027, light-modus, idempotenz, seed-logik, datenpersistenz, ak-03]

---

### TC-027-004: Mehrere Tabs oder Geraete im LAN — kein erneutes Login erforderlich

**Requirement**: REQ-027 § 1.1 Szenario 2
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light` auf einem Home-Server
- Pflanze "Tomate-1" ist bereits im System-Tenant angelegt

**Testschritte**:
1. Nutzer A oeffnet die App auf dem Laptop (`http://homeserver:5173`)
2. Nutzer B oeffnet die App auf dem Tablet (`http://homeserver:5173`)
3. Nutzer A navigiert zu "Pflanzen" und sieht "Tomate-1"
4. Nutzer B navigiert zu "Pflanzen"

**Erwartete Ergebnisse**:
- Auf beiden Geraeten erscheint **kein** Login-Bildschirm
- Beide Geraete zeigen dieselbe Pflanzenliste inklusive "Tomate-1"
- Beide Geraete koennen Pflanzen anlegen, bearbeiten und loeschen

**Nachbedingungen**:
- Aenderungen von Geraet A sind auf Geraet B nach Seitenaktualisierung sichtbar

**Tags**: [req-027, light-modus, lan, mehrgeraete, familien-nutzung, system-user]

---

## 2. Ausgeblendete UI-Elemente im Light-Modus

### TC-027-005: Login-Route ist nicht erreichbar

**Requirement**: REQ-027 § 2.2, FK-01
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/login`

**Erwartete Ergebnisse**:
- Die Route `/login` ist nicht definiert
- Es erscheint eine 404-Seite ("Seite nicht gefunden") oder eine Weiterleitung auf das Dashboard
- Kein Login-Formular ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, routing, login-route, fk-01, 404]

---

### TC-027-006: Register-Route ist nicht erreichbar

**Requirement**: REQ-027 § 2.2, FK-01
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/register`

**Erwartete Ergebnisse**:
- Die Route `/register` ist nicht definiert
- Es erscheint eine 404-Seite oder eine Weiterleitung auf das Dashboard
- Kein Registrierungsformular ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, routing, register-route, fk-01, 404]

---

### TC-027-007: Passwort-vergessen-Route ist nicht erreichbar

**Requirement**: REQ-027 § 2.2, FK-01
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/forgot-password`

**Erwartete Ergebnisse**:
- Die Route `/forgot-password` ist nicht definiert
- Es erscheint eine 404-Seite oder eine Weiterleitung auf das Dashboard
- Kein Passwort-zuruecksetzen-Formular ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, routing, forgot-password-route, fk-01, 404]

---

### TC-027-008: Mitglieder-Route ist nicht erreichbar

**Requirement**: REQ-027 § 2.2
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/t/mein-garten/members`

**Erwartete Ergebnisse**:
- Die Route `/t/{slug}/members` ist nicht definiert
- Es erscheint eine 404-Seite oder eine Weiterleitung auf das Dashboard
- Keine Mitgliederverwaltungs-Ansicht ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, routing, mitglieder-route, 404]

---

### TC-027-009: Einladungen-Route ist nicht erreichbar

**Requirement**: REQ-027 § 2.2
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/t/mein-garten/invitations`

**Erwartete Ergebnisse**:
- Die Route `/t/{slug}/invitations` ist nicht definiert
- Es erscheint eine 404-Seite oder eine Weiterleitung auf das Dashboard
- Keine Einladungsverwaltungs-Ansicht ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, routing, einladungen-route, 404]

---

### TC-027-010: AppBar ohne User-Avatar und Logout-Button

**Requirement**: REQ-027 § 2.2, § 7.3, FK-02
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- App ist geladen, Dashboard ist sichtbar

**Testschritte**:
1. Nutzer betrachtet die obere Navigationsleiste (AppBar)

**Erwartete Ergebnisse**:
- **Kein** User-Avatar ist in der AppBar sichtbar
- **Kein** Logout-Button ist in der AppBar sichtbar
- **Kein** Tenant-Switcher-Dropdown ist in der AppBar sichtbar
- **Kein** Benachrichtigungs-Icon fuer Einladungen ist sichtbar
- Sichtbar in der AppBar: App-Titel, Sprach-Umschalter, Theme-Toggle

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, appbar, user-avatar, logout, tenant-switcher, fk-02]

---

### TC-027-011: Sidebar ohne Mitglieder- und Einladungs-Menüpunkte

**Requirement**: REQ-027 § 2.2, § 7.2, FK-03
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- App ist geladen, Sidebar ist sichtbar

**Testschritte**:
1. Nutzer betrachtet die linke Seitennavigation (Sidebar)

**Erwartete Ergebnisse**:
- Der Menüpunkt "Mitglieder" ist **nicht** in der Sidebar sichtbar
- Der Menüpunkt "Einladungen" ist **nicht** in der Sidebar sichtbar
- Der Menüpunkt "Standort-Zuweisungen" ist **nicht** in der Sidebar sichtbar
- Alle anderen Navigationspunkte (Pflanzen, Standorte, Aufgaben, Duengung, IPM, Ernte, Stammdaten) sind sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, sidebar, navigation, mitglieder, einladungen, fk-03]

---

### TC-027-012: AccountSettingsPage zeigt nur Allgemein und Erfahrungsstufe

**Requirement**: REQ-027 § 2.2, § 7.4, FK-04
**Priority**: Critical
**Category**: Detailansicht
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Nutzer navigiert zu den Kontoeinstellungen (soweit erreichbar, z.B. ueber Einstellungs-Icon oder direkten Link)

**Testschritte**:
1. Nutzer oeffnet die AccountSettingsPage (z.B. ueber `/account`)
2. Nutzer betrachtet die Tabs der Seite

**Erwartete Ergebnisse**:
- Tab "Allgemein" (Sprache, Zeitzone) ist sichtbar und klickbar
- Tab "Erfahrungsstufe" (REQ-021) ist sichtbar und klickbar
- Tab "Sicherheit" (Passwort aendern, Auth-Provider) ist **nicht** sichtbar
- Tab "Sessions" (aktive Sitzungen) ist **nicht** sichtbar
- Tab "Datenschutz" (DSGVO-Einstellungen) ist **nicht** sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, account-settings, tabs, sicherheit, datenschutz, fk-04]

---

### TC-027-013: DSGVO-Consent-Banner erscheint nicht

**Requirement**: REQ-027 § 1 (Business Case), § 2.1, FK-05
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Frische Instanz, erster Start

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173`
2. Nutzer wartet, bis die App vollstaendig geladen ist
3. Nutzer scrollt durch die Seite und betrachtet alle sichtbaren Elemente

**Erwartete Ergebnisse**:
- Kein DSGVO-Consent-Banner erscheint zu keinem Zeitpunkt
- Kein "Cookie-Banner" oder "Datenschutz akzeptieren"-Dialog erscheint
- Keine Einwilligungsabfrage fuer Drittanbieter-Dienste erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, dsgvo, consent-banner, fk-05]

---

### TC-027-014: Standort-Detailseite hat keinen Zuweisungen-Tab

**Requirement**: REQ-027 § 2.2
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Mindestens ein Standort ist angelegt

**Testschritte**:
1. Nutzer navigiert zu "Standorte" in der Sidebar
2. Nutzer klickt auf einen bestehenden Standort, um die Detailseite zu oeffnen
3. Nutzer betrachtet die Tabs der Standort-Detailseite

**Erwartete Ergebnisse**:
- Der Tab "Zuweisungen" ist **nicht** sichtbar (dient der Nutzer-Standort-Zuweisung im Full-Modus)
- Alle anderen Tabs (z.B. Uebersicht, Sensoren, Pflegeprofil) sind sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, standort, detailseite, zuweisungen-tab]

---

### TC-027-015: Aufgaben-Formular hat kein "Zuweisen an"-Dropdown

**Requirement**: REQ-027 § 2.2, § 2.1
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Nutzer navigiert zu "Aufgaben"

**Testschritte**:
1. Nutzer klickt auf "Neue Aufgabe erstellen" (oder oeffnet ein Aufgaben-Formular)
2. Nutzer betrachtet die Formularfelder

**Erwartete Ergebnisse**:
- Das Dropdown-Feld "Zuweisen an" (fuer Nutzer-Zuweisung) ist **nicht** im Formular sichtbar
- Alle anderen Aufgabenfelder (Titel, Beschreibung, Faelligkeitsdatum, Prioritaet) sind sichtbar und bearbeitbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, aufgaben, zuweisen-an, formular]

---

## 3. Kernfunktionalität im Light-Modus

### TC-027-016: Pflanze anlegen im Light-Modus

**Requirement**: REQ-027 § 2.1, AK-07, FK-06
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Mindestens eine Art (Species) ist in den Stammdaten vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Pflanzen" in der Sidebar
2. Nutzer klickt auf "Erstellen"
3. Nutzer fuellt das Formular aus (Name, Art, Standort)
4. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Die Pflanze erscheint in der Pflanzenliste
- Eine Erfolgs-Snackbar wird angezeigt (z.B. "Pflanze wurde erstellt")
- Kein Login-Redirect tritt auf
- Die Pflanze ist dem System-Tenant zugeordnet (sichtbar durch Verbleib in der Ansicht)

**Nachbedingungen**:
- Pflanze ist persistent gespeichert

**Tags**: [req-027, light-modus, pflanzen, anlegen, happy-path, ak-07, fk-06]

---

### TC-027-017: Pflanze bearbeiten und loeschen im Light-Modus

**Requirement**: REQ-027 § 2.1, AK-07, FK-06
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Pflanze "Basilikum-1" ist angelegt

**Testschritte**:
1. Nutzer navigiert zu "Pflanzen" und oeffnet "Basilikum-1"
2. Nutzer klickt auf "Bearbeiten"
3. Nutzer aendert den Namen auf "Basilikum-Ernte"
4. Nutzer klickt auf "Speichern"
5. Nutzer kehrt zur Pflanzenliste zurueck
6. Nutzer oeffnet "Basilikum-Ernte" erneut und klickt auf "Loeschen"
7. Nutzer bestaetigt den Loeschdialog

**Erwartete Ergebnisse**:
- Nach Schritt 4: Erfolgs-Snackbar erscheint, Name ist aktualisiert
- Nach Schritt 7: Pflanze ist aus der Liste verschwunden, Erfolgs-Snackbar erscheint
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Pflanze "Basilikum-Ernte" existiert nicht mehr

**Tags**: [req-027, light-modus, pflanzen, bearbeiten, loeschen, ak-07]

---

### TC-027-018: Standort anlegen und verwalten im Light-Modus

**Requirement**: REQ-027 § 2.1, FK-06
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert zu "Standorte" in der Sidebar
2. Nutzer klickt auf "Erstellen"
3. Nutzer gibt Name "Wintergarten" ein und speichert
4. Nutzer oeffnet den neuen Standort "Wintergarten"

**Erwartete Ergebnisse**:
- Standort erscheint nach dem Speichern in der Liste
- Detailseite von "Wintergarten" ist vollstaendig navigierbar
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Standort "Wintergarten" ist persistent gespeichert

**Tags**: [req-027, light-modus, standorte, anlegen, fk-06]

---

### TC-027-019: Duengung und Bewaesserung vollstaendig nutzbar im Light-Modus

**Requirement**: REQ-027 § 2.1, FK-06
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Pflanzendurchlauf mit mindestens einer Pflanze ist vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Duengung" oder dem entsprechenden Bereich
2. Nutzer oeffnet die Naehrstoffkalkulation fuer einen Durchlauf
3. Nutzer erstellt einen Naehrstoffplan

**Erwartete Ergebnisse**:
- Alle Duengungs- und Bewaesserungs-Funktionen sind ohne Einschraenkungen bedienbar
- Kein Hinweis erscheint, dass Funktionen im Light-Modus nicht verfuegbar sind
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Naehrstoffplan ist gespeichert

**Tags**: [req-027, light-modus, duengung, bewaesserung, fk-06]

---

### TC-027-020: IPM und Pflanzenschutz vollstaendig nutzbar im Light-Modus

**Requirement**: REQ-027 § 2.1, FK-06
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Mindestens eine Pflanze ist vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Pflanzenschutz" (IPM)
2. Nutzer erfasst eine Schaderreger-Inspektion fuer eine Pflanze

**Erwartete Ergebnisse**:
- IPM-Funktionen sind vollstaendig ohne Einschraenkungen bedienbar
- Inspektion wird gespeichert und in der Historie angezeigt
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Inspektion ist persistent gespeichert

**Tags**: [req-027, light-modus, ipm, pflanzenschutz, fk-06]

---

### TC-027-021: Erntemanagement vollstaendig nutzbar im Light-Modus

**Requirement**: REQ-027 § 2.1, FK-06
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Pflanze in Erntephase ist vorhanden (keine offenen Karenz-Verstossverhinderungen)

**Testschritte**:
1. Nutzer navigiert zu "Ernte"
2. Nutzer erfasst eine Ernte fuer eine Pflanze

**Erwartete Ergebnisse**:
- Ernte-Erfassung ist ohne Einschraenkungen bedienbar
- Ernte wird gespeichert und erscheint in der Liste
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Ernte ist persistent gespeichert

**Tags**: [req-027, light-modus, ernte, erntemanagement, fk-06]

---

### TC-027-022: Pflegeerinnerungen vollstaendig nutzbar im Light-Modus

**Requirement**: REQ-027 § 2.1, AK-08
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Pflanze mit Pflegeprofil ist vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Pflege" oder "Pflegedashboard"
2. Nutzer betrachtet die Pflegeerinnerungen

**Erwartete Ergebnisse**:
- Pflegeerinnerungen sind sichtbar und nach Dringlichkeit gruppiert
- Nutzer kann Pflegeaktionen bestaetigen
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Pflegeaktion ist als erledigt markiert

**Tags**: [req-027, light-modus, pflegeerinnerungen, pflegedashboard, ak-08]

---

### TC-027-023: Phasensteuerung vollstaendig nutzbar im Light-Modus

**Requirement**: REQ-027 § 2.1, FK-06
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Pflanzendurchlauf in Phase "Keimling" ist vorhanden

**Testschritte**:
1. Nutzer navigiert zu einem Pflanzendurchlauf
2. Nutzer klickt auf "Naechste Phase" (Wechsel zu "Vegetativ")
3. Nutzer bestaetigt den Phasenwechsel im Dialog

**Erwartete Ergebnisse**:
- Phasenwechsel wird ausgefuehrt
- Status-Badge aktualisiert sich auf "Vegetativ"
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Durchlauf befindet sich in Phase "Vegetativ"

**Tags**: [req-027, light-modus, phasensteuerung, phasenwechsel, fk-06]

---

### TC-027-024: Stammdaten-Import vollstaendig nutzbar im Light-Modus

**Requirement**: REQ-027 § 2.1, FK-06
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- CSV-Datei mit gueltigen Stammdaten liegt vor

**Testschritte**:
1. Nutzer navigiert zu "Stammdaten" → "Import"
2. Nutzer laedt eine CSV-Datei hoch
3. Nutzer bestaetigt den Import nach der Vorschau

**Erwartete Ergebnisse**:
- Import-Vorschau zeigt die geparsten Eintraege korrekt an
- Nach Bestaetigung erscheint eine Erfolgs-Meldung
- Importierte Eintraege sind in den Stammdaten sichtbar
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Stammdaten sind importiert

**Tags**: [req-027, light-modus, stammdaten-import, fk-06]

---

### TC-027-025: Alle globalen Stammdaten sind im Light-Modus ohne manuelle Zuweisung sichtbar

**Requirement**: REQ-027 § 3.5, AK-13, AK-14
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Globale Stammdaten (Arten, Schaedlinge, Duengemittel) sind im System vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Stammdaten" → "Arten"
2. Nutzer betrachtet die Artenliste
3. Nutzer navigiert zu "Stammdaten" → "Schaedlinge"
4. Nutzer navigiert zu "Stammdaten" → "Duengemittel"

**Erwartete Ergebnisse**:
- Alle vorhandenen Arten sind in der Liste sichtbar (kein leerer Zustand)
- Alle Schaedlinge und Duengemittel sind sichtbar
- Kein Hinweis erscheint, dass eine manuelle Zuweisung notwendig ist
- Die Stammdaten sind ohne zusaetzliche Konfiguration verwendbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, stammdaten, auto-assign, tenant-has-access, ak-13, ak-14]

---

### TC-027-026: Externe Anreicherung ist im Light-Modus standardmaessig deaktiviert

**Requirement**: REQ-027 § 2.1 (Feature-Visibility-Matrix)
**Priority**: Medium
**Category**: Fehlermeldung
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`, `ENABLE_ENRICHMENT_LIGHTMODE` ist **nicht** gesetzt oder `false`
- Nutzer befindet sich in den Stammdaten einer Art

**Testschritte**:
1. Nutzer navigiert zu einer Art in den Stammdaten (z.B. "Tomate")
2. Nutzer sucht nach einem Button oder einer Option "Externe Daten abrufen" / "Anreichern"

**Erwartete Ergebnisse**:
- Der Button fuer externe Anreicherung ist **nicht** sichtbar oder ist deaktiviert (grau, nicht klickbar)
- Es erscheint kein Fehler, wenn die Funktion nicht vorhanden ist

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, externe-anreicherung, deaktiviert, enable-enrichment-lightmode]

---

### TC-027-027: Externe Anreicherung aktivierbar via ENABLE_ENRICHMENT_LIGHTMODE=true

**Requirement**: REQ-027 § 2.1 (Feature-Visibility-Matrix)
**Priority**: Low
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light` und `ENABLE_ENRICHMENT_LIGHTMODE=true`
- Nutzer befindet sich in den Stammdaten einer Art

**Testschritte**:
1. Nutzer navigiert zu einer Art in den Stammdaten
2. Nutzer sucht nach dem Button "Externe Daten abrufen" / "Anreichern"
3. Nutzer klickt auf den Button

**Erwartete Ergebnisse**:
- Der Button fuer externe Anreicherung ist sichtbar und klickbar
- Die Anreicherungsfunktion wird ausgefuehrt (Fortschrittsanzeige erscheint)

**Nachbedingungen**:
- Artdaten koennen mit externen Daten angereichert werden

**Tags**: [req-027, light-modus, externe-anreicherung, aktiviert, enable-enrichment-lightmode]

---

## 4. Moduswechsel: Upgrade Light → Full

### TC-027-028: Nach Upgrade auf Full erscheint der Login-Screen

**Requirement**: REQ-027 § 1.1 Szenario 5, § 7a.2, AK-16
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- App lief zuvor mit `KAMERPLANTER_MODE=light` (Pflanzen, Standorte wurden angelegt)
- Konfiguration wurde auf `KAMERPLANTER_MODE=full` geaendert und Backend wurde neu gestartet
- Browser-Cache wurde geleert bzw. neue Verbindung wird hergestellt

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173`

**Erwartete Ergebnisse**:
- Der Login-Bildschirm erscheint
- Eine Registrierungsoption ist sichtbar
- Kein automatischer Zugang ohne Login

**Nachbedingungen**:
- System befindet sich im Full-Modus
- System-User ist auf Status "inaktiv" gesetzt (nicht sichtbar fuer Nutzer)

**Tags**: [req-027, upgrade, light-zu-full, login-screen, moduswechsel, ak-16]

---

### TC-027-029: Uebernahme-Dialog erscheint nach erster Registrierung

**Requirement**: REQ-027 § 1.1 Szenario 5, § 7a.2, AK-17, AK-18
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Upgrade von Light auf Full wurde durchgefuehrt (siehe TC-027-028)
- Im ehemaligen Light-Modus waren Daten vorhanden (z.B. 10 Pflanzen, 2 Standorte)
- Noch kein Nutzer registriert

**Testschritte**:
1. Nutzer klickt auf "Registrieren" auf dem Login-Bildschirm
2. Nutzer fuellt das Registrierungsformular aus (Name, E-Mail, Passwort) und bestaetigt
3. Nutzer schliisst den Registrierungsprozess ab

**Erwartete Ergebnisse**:
- Nach der Registrierung erscheint ein Uebernahme-Dialog mit folgendem Inhalt (sinngemaeiss):
  "Es gibt bestehende Daten (10 Pflanzen, 2 Standorte). Moechten Sie diese in Ihr Konto uebernehmen?"
- Die Anzahl der Pflanzen und Standorte entspricht den tatsaechlich vorhandenen Datensaetzen
- Der Dialog bietet zwei Optionen: "Ja, uebernehmen" und "Nein, neu starten"
- Ein persoenlicher Tenant wurde noch **nicht** automatisch erstellt

**Nachbedingungen**:
- Uebernahme-Dialog ist sichtbar, noch keine Aktion ausgefuehrt

**Tags**: [req-027, upgrade, uebernahme-dialog, registrierung, pending-takeover, ak-17, ak-18]

---

### TC-027-030: Uebernahme bestaetigen — Daten sind im neuen Account sichtbar

**Requirement**: REQ-027 § 1.1 Szenario 5, § 7a.2, AK-19
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Uebernahme-Dialog ist sichtbar (Vorbedingungen wie TC-027-029)
- Im ehemaligen Light-Modus: 10 Pflanzen, 2 Standorte, 1 Naehrstoffplan vorhanden

**Testschritte**:
1. Nutzer klickt im Uebernahme-Dialog auf "Ja, uebernehmen"

**Erwartete Ergebnisse**:
- Nutzer wird auf das Dashboard weitergeleitet
- Der Tenant-Name lautet "{Anzeigename}s Garten" (z.B. "Annas Garten")
- Die Pflanzenliste zeigt 10 Pflanzen (alle aus dem Light-Modus)
- Die Standortliste zeigt 2 Standorte
- Der Naehrstoffplan ist sichtbar
- Keine Fehlermeldung erscheint
- Der Uebernahme-Dialog erscheint nicht mehr beim naechsten Login

**Nachbedingungen**:
- Neuer Nutzer ist Tenant-Admin im System-Tenant (umbenannt)
- Neuer Nutzer ist KA-Admin im Platform-Tenant
- pending_takeover-Flag wurde entfernt

**Tags**: [req-027, upgrade, uebernahme, bestaetigen, daten-migration, ak-19]

---

### TC-027-031: Uebernahme ablehnen — neuer persoenlicher Tenant wird erstellt

**Requirement**: REQ-027 § 1.1 Szenario 6, AK-20, AK-21
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Uebernahme-Dialog ist sichtbar (Vorbedingungen wie TC-027-029)

**Testschritte**:
1. Nutzer klickt im Uebernahme-Dialog auf "Nein, neu starten"

**Erwartete Ergebnisse**:
- Nutzer wird auf das Dashboard weitergeleitet
- Neuer persoenlicher Tenant ist erstellt und aktiv
- Die Pflanzenliste ist **leer** (keine Light-Modus-Daten)
- Kein Hinweis auf die ehemaligen Light-Modus-Daten
- Der Uebernahme-Dialog erscheint nicht mehr beim naechsten Login

**Nachbedingungen**:
- Neuer Nutzer hat eigenen persoenlichen Tenant (leer)
- System-Tenant (mit alten Daten) bleibt bestehen, ist aber nicht sichtbar fuer den Nutzer
- Neuer Nutzer ist KA-Admin im Platform-Tenant

**Tags**: [req-027, upgrade, uebernahme, ablehnen, persoenlicher-tenant, ak-20, ak-21]

---

### TC-027-032: Uebernahme-Dialog erscheint nicht bei zweitem registrierten Nutzer

**Requirement**: REQ-027 § 7a.2, AK-21
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Upgrade von Light auf Full wurde durchgefuehrt
- Erster Nutzer hat sich bereits registriert und Uebernahme-Dialog bearbeitet (accept=true oder false)
- Zweiter Nutzer registriert sich

**Testschritte**:
1. Zweiter Nutzer klickt auf "Registrieren" und schliisst die Registrierung ab

**Erwartete Ergebnisse**:
- Kein Uebernahme-Dialog erscheint
- Zweiter Nutzer erhaelt Standard-Onboarding (REQ-020) oder Dashboard
- Persoenlicher Tenant wird fuer zweiten Nutzer normal erstellt

**Nachbedingungen**:
- Zweiter Nutzer hat eigenen persoenlichen Tenant

**Tags**: [req-027, upgrade, uebernahme-dialog, zweiter-nutzer, ak-21]

---

## 5. Moduswechsel: Downgrade Full → Light

### TC-027-033: Nach Downgrade erscheint kein Login-Screen mehr

**Requirement**: REQ-027 § 1.1 Szenario 7, § 7a.3, AK-22, AK-26
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- App lief mit `KAMERPLANTER_MODE=full` mit 3 Nutzern, 2 Tenants, 20 Pflanzen im System-Tenant
- Konfiguration wurde auf `KAMERPLANTER_MODE=light` geaendert und Backend wurde neu gestartet

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173`

**Erwartete Ergebnisse**:
- **Kein** Login-Bildschirm erscheint
- App laedt direkt und leitet auf `/t/mein-garten/dashboard` weiter
- Dashboard ist sofort ohne Authentifizierung zugaenglich

**Nachbedingungen**:
- System-User ist reaktiviert oder neu erstellt
- System-Tenant ist reaktiviert oder neu erstellt
- Alle anderen Nutzer-Accounts und Tenants sind in der DB erhalten, aber nicht erreichbar

**Tags**: [req-027, downgrade, full-zu-light, login-screen, ak-22, ak-26]

---

### TC-027-034: Nach Downgrade sind System-Tenant-Daten sichtbar

**Requirement**: REQ-027 § 1.1 Szenario 7, § 7a.3, AK-23, AK-25
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Downgrade von Full auf Light wurde durchgefuehrt (wie TC-027-033)
- Im System-Tenant waren vor dem Downgrade 20 Pflanzen vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Pflanzen" nach dem Downgrade

**Erwartete Ergebnisse**:
- Die 20 Pflanzen aus dem System-Tenant sind sichtbar
- Kein Datenverlust ist erkennbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, downgrade, system-tenant, datenpersistenz, ak-23, ak-25]

---

### TC-027-035: Nach Downgrade sind andere Tenant-Daten nicht sichtbar

**Requirement**: REQ-027 § 7a.3, AK-25
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Downgrade von Full auf Light wurde durchgefuehrt
- Im Full-Modus hatte ein anderer Nutzer "Max" einen eigenen Tenant mit 5 Pflanzen

**Testschritte**:
1. Nutzer navigiert zu "Pflanzen" nach dem Downgrade
2. Nutzer sucht nach Pflanzen, die Max im Full-Modus angelegt hatte

**Erwartete Ergebnisse**:
- Maxens Pflanzen (aus seinem eigenen Tenant) sind **nicht** sichtbar
- Nur Pflanzen des System-Tenants werden angezeigt
- Es erscheint **keine Fehlermeldung** — einfach nicht sichtbar

**Nachbedingungen**:
- Kein Status geaendert (Maxens Daten sind in der DB erhalten, nur nicht erreichbar)

**Tags**: [req-027, downgrade, andere-tenants, datenisolation, ak-25]

---

### TC-027-036: Nach Downgrade sind Stammdaten nach Auto-Assign sichtbar

**Requirement**: REQ-027 § 7a.3, AK-24
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Downgrade von Full auf Light wurde durchgefuehrt
- Globale Stammdaten (Arten, Schaedlinge) sind vorhanden

**Testschritte**:
1. Nutzer navigiert zu "Stammdaten" → "Arten" nach dem Downgrade

**Erwartete Ergebnisse**:
- Alle globalen Arten sind sichtbar (Auto-Assign hat tenant_has_access-Kanten erstellt)
- Kein leerer Zustand in der Stammdaten-Liste

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, downgrade, stammdaten, auto-assign, ak-24]

---

## 6. Roundtrip Light → Full → Light → Full

### TC-027-037: Roundtrip — Daten nach Light→Full→Light→Full erhalten

**Requirement**: REQ-027 § 1.1 Szenario 8, AK-27
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Phase 1 (Light): System-User hat 10 Pflanzen im System-Tenant
- Phase 2 (Full nach Upgrade, Uebernahme bejaht): Nutzer "Anna" hat Tenant uebernommen, 20 weitere Pflanzen angelegt (insg. 30), Freund "Max" hat eigenen Tenant mit 5 Pflanzen
- Phase 3 (Light nach Downgrade): System-User sieht 30 Pflanzen in System-Tenant

**Testschritte**:
1. Konfiguration wird wieder auf `KAMERPLANTER_MODE=full` geaendert und Backend neu gestartet
2. Anna navigiert zu `http://localhost:5173` und meldet sich an
3. Anna betrachtet ihre Pflanzenliste

**Erwartete Ergebnisse**:
- Uebernahme-Dialog erscheint erneut fuer Anna (pending_takeover ist wieder gesetzt nach Downgrade)
- Anna klickt auf "Ja, uebernehmen"
- Anna sieht alle 30 Pflanzen
- Max kann sich anmelden und sieht seinen Tenant mit 5 Pflanzen

**Nachbedingungen**:
- Kein Datenverlust ueber den gesamten Roundtrip

**Tags**: [req-027, roundtrip, light-full-light-full, datenpersistenz, ak-27]

---

## 7. Mode-Informations-Endpunkt (GET /api/v1/mode)

### TC-027-038: Mode-Endpunkt gibt korrekten Light-Modus-Status zurueck

**Requirement**: REQ-027 § 6.3, AK-10
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- App ist geladen

**Testschritte**:
1. Nutzer verwendet die App normal (kein direkter API-Aufruf noetig)
2. Frontend hat beim Start den Mode-Endpunkt abgefragt (intern)
3. Nutzer beobachtet, dass UI im Light-Modus-Verhalten angezeigt wird

**Erwartete Ergebnisse**:
- App verhaelt sich konsistent mit Light-Modus-Verhalten:
  - Kein Login-Screen
  - Keine Auth-Elemente in AppBar
  - Keine Tenant-Verwaltungs-Links
- (Optional, falls im Frontend sichtbar) Mode-Status wird korrekt als "light" kommuniziert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, mode-endpunkt, feature-flags, ak-10]

---

### TC-027-039: Mode-Endpunkt gibt korrekten Full-Modus-Status zurueck

**Requirement**: REQ-027 § 6.3, AK-10
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=full`
- App ist geladen

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173`

**Erwartete Ergebnisse**:
- Login-Screen erscheint (Frontend hat Mode=full erkannt)
- Auth-Elemente (Login-Formular, Registrierungs-Link) sind sichtbar
- Alle Full-Modus-Features sind aktiviert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, mode-endpunkt, full-modus, feature-flags, ak-10]

---

## 8. Erfahrungsstufen im Light-Modus

### TC-027-040: Erfahrungsstufe kann im Light-Modus geaendert werden

**Requirement**: REQ-027 § 2.1, REQ-021
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Aktuelle Erfahrungsstufe ist "Einsteiger"

**Testschritte**:
1. Nutzer oeffnet AccountSettingsPage (z.B. ueber Einstellungs-Icon)
2. Nutzer klickt auf den Tab "Erfahrungsstufe"
3. Nutzer waehlt "Fortgeschrittener" aus
4. Nutzer speichert die Einstellung

**Erwartete Ergebnisse**:
- Die Erfahrungsstufe wird auf "Fortgeschrittener" gesetzt
- Erfolgs-Snackbar erscheint
- In der App sind jetzt zusaetzliche Felder und Navigations-Punkte sichtbar, die fuer "Fortgeschrittener" freigeschaltet sind

**Nachbedingungen**:
- Erfahrungsstufe ist dauerhaft gespeichert

**Tags**: [req-027, light-modus, erfahrungsstufe, req-021, account-settings]

---

### TC-027-041: Sprache kann im Light-Modus geaendert werden

**Requirement**: REQ-027 § 7.4
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Aktuelle Sprache ist Deutsch

**Testschritte**:
1. Nutzer oeffnet AccountSettingsPage
2. Nutzer klickt auf den Tab "Allgemein"
3. Nutzer aendert Sprache auf Englisch
4. Nutzer speichert die Einstellung

**Erwartete Ergebnisse**:
- Die UI wechselt auf Englisch (alle Labels, Buttons und Meldungen erscheinen auf Englisch)
- Erfolgs-Snackbar erscheint (auf Englisch: "Settings saved" o.ae.)
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Spracheinstellung ist dauerhaft gespeichert

**Tags**: [req-027, light-modus, sprache, i18n, account-settings]

---

## 9. Grenzfaelle und Fehlerzustaende

### TC-027-042: Direktaufruf einer gesicherten Route im Light-Modus — kein 401

**Requirement**: REQ-027 § 7.1, AK-04
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu einer geschuetzten Seite, z.B. `/t/mein-garten/pflanzen`

**Erwartete Ergebnisse**:
- Die Pflanzenliste wird direkt angezeigt — kein Redirect auf Login
- Keine "401 Unauthorized"-Meldung erscheint
- Keine "Bitte melden Sie sich an"-Meldung erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, auth-bypass, direktaufruf, 401, ak-04]

---

### TC-027-043: App-Start nach Neustart des Browsers im Light-Modus — kein Session-Verlust

**Requirement**: REQ-027 § 1.1 Szenario 2
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- Nutzer hatte die App zuvor verwendet und Pflanzen angelegt

**Testschritte**:
1. Nutzer schliesst den Browser vollstaendig
2. Nutzer oeffnet den Browser neu
3. Nutzer navigiert zu `http://localhost:5173`

**Erwartete Ergebnisse**:
- App laedt direkt ohne Login
- Alle zuvor angelegten Pflanzen sind sichtbar (Session-Wiederherstellung nicht noetig, da kein Token)
- App ist vollstaendig bedienbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, session, browser-neustart, persistenz]

---

### TC-027-044: Uebernahme-Dialog zeigt korrekte Ressourcen-Anzahl

**Requirement**: REQ-027 § 7a.4, AK-28
**Priority**: Medium
**Category**: Dialog
**Vorbedingungen**:
- Upgrade von Light auf Full wurde durchgefuehrt
- Im Light-Modus: genau 5 Pflanzen, 1 Standort, 2 Aufgaben angelegt

**Testschritte**:
1. Erster Nutzer registriert sich nach dem Upgrade
2. Uebernahme-Dialog erscheint
3. Nutzer liest die Ressourcen-Informationen im Dialog

**Erwartete Ergebnisse**:
- Dialog zeigt korrekte Zahlen: "5 Pflanzen, 1 Standort"
- Zahlen sind konsistent mit den tatsaechlich vorhandenen Datensaetzen
- (Optional, je nach UI-Design) Aufgaben werden ebenfalls angezeigt

**Nachbedingungen**:
- Kein Status geaendert (Dialog noch offen)

**Tags**: [req-027, uebernahme-dialog, ressourcen-anzahl, ak-28]

---

### TC-027-045: Full-Modus — API-Requests ohne Authorization-Header werden abgelehnt

**Requirement**: REQ-027 § 4.2, AK-05
**Priority**: Critical
**Category**: Fehlermeldung
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=full`
- Nutzer ist **nicht** eingeloggt

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/t/mein-garten/pflanzen` ohne eingeloggt zu sein

**Erwartete Ergebnisse**:
- Nutzer wird auf den Login-Screen umgeleitet (AuthGuard greift)
- Die Pflanzenliste ist **nicht** sichtbar ohne Login
- Keine Pflanzen werden angezeigt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, full-modus, auth-guard, 401, ak-05]

---

### TC-027-046: Light-Modus — Tenant-Slug aus URL funktioniert korrekt

**Requirement**: REQ-027 § 7.1
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert direkt zu `http://localhost:5173/t/mein-garten/pflanzen`

**Erwartete Ergebnisse**:
- Pflanzenliste wird angezeigt (kein Fehler)
- URL enthielt `/t/mein-garten/` — der System-Tenant-Slug "mein-garten" wird korrekt aufgeloest

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, tenant-slug, routing, mein-garten]

---

### TC-027-047: Light-Modus — Root-URL leitet auf System-Tenant-Dashboard weiter

**Requirement**: REQ-027 § 7.1
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173/`

**Erwartete Ergebnisse**:
- Browser-URL aendert sich automatisch auf `/t/mein-garten/dashboard`
- Dashboard-Seite wird angezeigt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, routing, redirect, root-url, dashboard]

---

### TC-027-048: Full-Modus — DSGVO-Consent-Banner erscheint

**Requirement**: REQ-027 § 2.1 (Kontrastverhalten zum Light-Modus)
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=full`
- Neuer, nicht eingeloggter Nutzer besucht die App zum ersten Mal

**Testschritte**:
1. Nutzer navigiert zu `http://localhost:5173`
2. Nutzer betrachtet den angezeigten Bildschirm

**Erwartete Ergebnisse**:
- Ein DSGVO-Consent-Banner oder Cookie-Zustimmungsdialog erscheint
- Der Nutzer muss eine Zustimmungsoption auswaehlen, bevor er fortfahren kann

**Nachbedingungen**:
- Consent-Auswahl des Nutzers ist gespeichert

**Tags**: [req-027, full-modus, dsgvo, consent-banner, kontrasttest]

---

## 10. Sprach- und Theme-Optionen in der AppBar

### TC-027-049: Theme-Toggle ist im Light-Modus verfuegbar

**Requirement**: REQ-027 § 7.3
**Priority**: Low
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- App ist im hellen Theme geladen

**Testschritte**:
1. Nutzer klickt auf den Theme-Toggle in der AppBar

**Erwartete Ergebnisse**:
- Die App wechselt auf dunkles Theme
- Alle Seiten und Dialoge sind im dunklen Theme dargestellt
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Theme-Einstellung ist gespeichert (localStorage)

**Tags**: [req-027, light-modus, theme-toggle, dark-mode, appbar]

---

### TC-027-050: Sprach-Umschalter ist im Light-Modus verfuegbar (AppBar)

**Requirement**: REQ-027 § 7.3
**Priority**: Low
**Category**: Happy Path
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`
- App laedt auf Deutsch

**Testschritte**:
1. Nutzer klickt auf den Sprach-Umschalter in der AppBar
2. Nutzer waehlt "English" (EN)

**Erwartete Ergebnisse**:
- Die UI-Sprache wechselt auf Englisch
- Alle sichtbaren Labels, Navigationspunkte und Buttons erscheinen auf Englisch
- Kein Login-Redirect tritt auf

**Nachbedingungen**:
- Spracheinstellung ist gespeichert

**Tags**: [req-027, light-modus, sprach-umschalter, i18n, appbar]

---

## 11. Abgrenzung: Nicht-In-Scope-Verhalten

### TC-027-051: Runtime-Moduswechsel ohne Neustart — nicht moeglich

**Requirement**: REQ-027 § 10 (Scope-Abgrenzung)
**Priority**: Low
**Category**: Fehlermeldung
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer durchsucht die gesamte App-Oberflaeche nach einem "Auf Full-Modus wechseln"-Button

**Erwartete Ergebnisse**:
- Es gibt keinen Button oder Schalter in der UI, der einen Live-Moduswechsel erlaubt
- Der Modus kann ausschliesslich ueber eine Umgebungsvariable + Neustart geaendert werden (nicht sichtbar in der UI)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, scope-abgrenzung, runtime-switch, hot-switching]

---

### TC-027-052: Light-Modus — Nur ein Tenant ist operativ

**Requirement**: REQ-027 § 10 (Scope-Abgrenzung)
**Priority**: Low
**Category**: Listenansicht
**Vorbedingungen**:
- Deployment mit `KAMERPLANTER_MODE=light`

**Testschritte**:
1. Nutzer durchsucht die gesamte App-Oberflaeche nach einem Tenant-Wechsel-Mechanismus

**Erwartete Ergebnisse**:
- Kein Tenant-Switcher ist sichtbar
- Kein Dropdown fuer Tenant-Auswahl ist sichtbar
- Alle Daten befinden sich im System-Tenant "Mein Garten"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-027, light-modus, tenant-switcher, single-tenant, scope-abgrenzung]

---

## Abdeckungsmatrix

| Spec-Abschnitt | Beschreibung | Abgedeckt durch Testfaelle |
|---|---|---|
| § 1.1 Szenario 1 | Erster Start Light-Modus (Raspberry Pi) | TC-027-001, TC-027-002, TC-027-003 |
| § 1.1 Szenario 2 | Mehrere Geraete im LAN | TC-027-004, TC-027-043 |
| § 1.1 Szenario 3 | Onboarding ohne Login-Schritt | TC-027-002 |
| § 1.1 Szenario 4 | API-Zugriff ohne Token | TC-027-042 |
| § 1.1 Szenario 5 | Upgrade Light→Full mit Uebernahme | TC-027-028, TC-027-029, TC-027-030 |
| § 1.1 Szenario 6 | Upgrade Light→Full mit Ablehnung | TC-027-031, TC-027-032 |
| § 1.1 Szenario 7 | Downgrade Full→Light | TC-027-033, TC-027-034, TC-027-035, TC-027-036 |
| § 1.1 Szenario 8 | Roundtrip Light→Full→Light→Full | TC-027-037 |
| § 2.1 Feature-Visibility-Matrix | Vollstaendige Kernfunktionen | TC-027-016 bis TC-027-025 |
| § 2.1 Externe Anreicherung | Standardmaessig deaktiviert | TC-027-026, TC-027-027 |
| § 2.2 Ausgeblendete UI-Elemente | Routing, AppBar, Sidebar, Account | TC-027-005 bis TC-027-015 |
| § 3.5 Seed-Logik (Idempotenz) | Kein Duplikat bei Mehrfachstart | TC-027-003 |
| § 3.4 Platform-Tenant-Membership | KA-Admin fuer System-User | TC-027-001 (Nachbedingungen) |
| § 6.3 Mode-Endpunkt | GET /api/v1/mode | TC-027-038, TC-027-039 |
| § 7.1 Mode-Aware Routing | Light-Routing, Root-Redirect | TC-027-005 bis TC-027-009, TC-027-046, TC-027-047 |
| § 7.3 Mode-Aware App-Bar | Kein Avatar, kein Tenant-Switcher | TC-027-010, TC-027-049, TC-027-050 |
| § 7.4 AccountSettingsPage | Nur Sprache + Erfahrungsstufe | TC-027-012, TC-027-040, TC-027-041 |
| § 7.5 Mode-Aware Onboarding | Wizard ohne Login-Schritt | TC-027-002 |
| § 7a.2 Upgrade Light→Full | System-User inaktiv, Uebernahme-Flow | TC-027-028 bis TC-027-032 |
| § 7a.3 Downgrade Full→Light | System-User reaktiviert, kein Datenverlust | TC-027-033 bis TC-027-036 |
| § 7a.4 Takeover-Status-Endpunkt | Ressourcen-Anzahl im Dialog | TC-027-044 |
| § 8 AK-01 bis AK-28 | Abnahmekriterien | Alle TC-027-* |
| § 8 FK-01 bis FK-07 | Frontend-Kriterien | TC-027-005 bis TC-027-015 |
| § 10 Scope-Abgrenzung | Nicht-In-Scope-Verhalten | TC-027-051, TC-027-052 |
| Full-Modus Kontrasttest | DSGVO-Banner, Auth-Guard aktiv | TC-027-045, TC-027-048 |
