---
req_id: REQ-030
title: Multi-Kanal-Benachrichtigungssystem mit Home Assistant als primaerem Zustellkanal
category: Pflege & Kommunikation
test_count: 62
coverage_areas:
  - In-App Notification Center (Bell-Icon, Badge, Drawer)
  - Benachrichtigungseinstellungen (AccountSettingsPage Tab "Benachrichtigungen")
  - Kanalverwaltung (HA, E-Mail, PWA, Apprise)
  - Quiet Hours Konfiguration
  - Batching-Einstellungen
  - Eskalationsstufen
  - Typ-Overrides
  - Test-Notification
  - Kanal-Statusanzeige
  - Notification als gelesen markieren
  - Actionable Notifications (Erledigt-Button)
  - Daily Summary Konfiguration
  - Feature-Toggle-Logik (kein Kanal aktiv → InApp-Fallback)
  - Erfahrungsstufen-Integration (REQ-021)
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-030: Multi-Kanal-Benachrichtigungssystem

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-030 Multi-Kanal-Benachrichtigungssystem v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-030 schliesst die Zustellluecke von REQ-022 (Pflegeerinnerungen) und REQ-006 (Aufgabenplanung): Erinnerungen existieren in der Datenbank — REQ-030 bringt sie aktiv zum Nutzer.

---

## 1. In-App Notification Center

### TC-REQ-030-001: Bell-Icon zeigt Badge fuer ungelesene Benachrichtigungen

**Requirement**: REQ-030 § 5.2 — In-App Notification Center
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und befindet sich auf einer beliebigen Seite (z.B. Dashboard)
- Mindestens 3 ungelesene Benachrichtigungen sind in der Datenbank vorhanden
- Keine externen Kanaele konfiguriert (InApp-Fallback aktiv)

**Testschritte**:
1. Nutzer navigiert zu `/dashboard`
2. Nutzer betrachtet die obere Navigationsleiste (AppBar)

**Erwartete Ergebnisse**:
- In der AppBar ist ein Glocken-Icon sichtbar
- Das Glocken-Icon zeigt ein rotes Badge mit der Anzahl ungelesener Benachrichtigungen (z.B. "3")
- Das Badge zeigt die korrekte Anzahl ungelesener Eintraege

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-030, in-app, bell-icon, badge, unread-count, notification-center]

---

### TC-REQ-030-002: Notification Center oeffnen per Bell-Icon-Klick

**Requirement**: REQ-030 § 5.2 — In-App Notification Center
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Bell-Icon mit Badge ist in der AppBar sichtbar (mindestens 1 ungelesene Notification)

**Testschritte**:
1. Nutzer klickt auf das Glocken-Icon in der AppBar

**Erwartete Ergebnisse**:
- Ein Dropdown oder Seitenpanel (Drawer) oeffnet sich
- Die Notification-Liste wird angezeigt mit mindestens einer Eintraegen
- Jeder Eintrag zeigt Titel und Kurztext der Benachrichtigung
- Ungelesene Eintraege sind visuell hervorgehoben (z.B. fetter Text, anderer Hintergrund)
- Ein "Alle gelesen"-Button ist sichtbar

**Nachbedingungen**:
- Notification Center ist geoeffnet

**Tags**: [req-030, in-app, notification-center, dropdown, drawer, open]

---

### TC-REQ-030-003: Notification Center anzeigen ohne ungelesene Benachrichtigungen

**Requirement**: REQ-030 § 5.2 — In-App Notification Center
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Alle Benachrichtigungen sind als gelesen markiert
- Das Bell-Icon zeigt kein Badge

**Testschritte**:
1. Nutzer klickt auf das Glocken-Icon in der AppBar

**Erwartete Ergebnisse**:
- Das Notification Center oeffnet sich
- Eine Hinweismeldung wie "Keine ungelesenen Benachrichtigungen" oder eine leere Liste erscheint
- Es gibt keinen roten Badge am Glocken-Icon

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, in-app, empty-state, no-unread]

---

### TC-REQ-030-004: Einzelne Notification als gelesen markieren

**Requirement**: REQ-030 § 5.2, § 3.11 POST /{key}/read
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat mindestens 2 ungelesene Benachrichtigungen
- Notification Center ist geoeffnet

**Testschritte**:
1. Nutzer klickt auf eine ungelesene Benachrichtigung in der Liste (oder auf ein "Als gelesen"-Symbol)

**Erwartete Ergebnisse**:
- Die angeklickte Benachrichtigung verliert die visuelle Hervorhebung (wird als "gelesen" dargestellt)
- Der Badge-Zaehler am Glocken-Icon verringert sich um 1
- Die restlichen ungelesenen Benachrichtigungen bleiben unveraendert

**Nachbedingungen**:
- Benachrichtigung hat Status "gelesen"
- Badge-Zaehler stimmt mit verbleibenden ungelesenen Eintraegen ueberein

**Tags**: [req-030, in-app, mark-read, badge-update, zustandswechsel]

---

### TC-REQ-030-005: Alle Benachrichtigungen als gelesen markieren

**Requirement**: REQ-030 § 5.2 — "Alle gelesen"-Button
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat 5 ungelesene Benachrichtigungen
- Notification Center ist geoeffnet
- "Alle gelesen"-Button ist sichtbar

**Testschritte**:
1. Nutzer klickt auf den "Alle gelesen"-Button im Notification Center

**Erwartete Ergebnisse**:
- Alle Benachrichtigungen in der Liste verlieren die visuelle Hervorhebung
- Der rote Badge am Glocken-Icon verschwindet vollstaendig
- Eine Bestaetigung (z.B. Snackbar "Alle Benachrichtigungen als gelesen markiert") erscheint

**Nachbedingungen**:
- Alle Benachrichtigungen haben Status "gelesen"
- Kein Badge am Glocken-Icon

**Tags**: [req-030, in-app, mark-all-read, badge-clear, snackbar]

---

### TC-REQ-030-006: Klick auf Benachrichtigung navigiert zur relevanten Seite

**Requirement**: REQ-030 § 5.2 — Navigation per Klick
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Notification Center ist geoeffnet
- Eine Giess-Erinnerung ist sichtbar mit action_url="/pflege"

**Testschritte**:
1. Nutzer klickt auf die Giess-Erinnerungs-Benachrichtigung

**Erwartete Ergebnisse**:
- Der Browser navigiert zur Pflege-Seite (z.B. `/aufgaben/queue` oder `/pflege`)
- Das Notification Center schliesst sich
- Die Benachrichtigung wird als gelesen markiert

**Nachbedingungen**:
- Nutzer befindet sich auf der Pflege-Seite
- Benachrichtigung ist gelesen

**Tags**: [req-030, in-app, navigation, action-url, deep-link]

---

### TC-REQ-030-007: Benachrichtigung per Swipe-to-dismiss entfernen (Mobile)

**Requirement**: REQ-030 § 5.2 — Swipe-to-dismiss
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer nutzt einen mobilen Browser (oder mobilem Viewport)
- Notification Center ist geoeffnet mit mindestens 2 Eintraegen

**Testschritte**:
1. Nutzer wischt eine Benachrichtigung nach links oder rechts (Swipe-Geste)

**Erwartete Ergebnisse**:
- Die Benachrichtigung verschwindet aus der Liste mit einer Slide-Animation
- Der Badge-Zaehler aktualisiert sich entsprechend
- Die uebrigen Benachrichtigungen bleiben unveraendert sichtbar

**Nachbedingungen**:
- Benachrichtigung ist ausgeblendet/entfernt

**Tags**: [req-030, in-app, swipe-dismiss, mobile, animation]

---

### TC-REQ-030-008: Notification-Liste zeigt Dringlichkeits-Indikator

**Requirement**: REQ-030 § 1.2 Eskalationsstufen, § 5.2
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Liste enthaelt Benachrichtigungen mit verschiedenen Dringlichkeitsstufen:
  - Eine `normal`-Benachrichtigung (Giessen faellig)
  - Eine `high`-Benachrichtigung (ueberfaellig seit 2 Tagen)
  - Eine `critical`-Benachrichtigung (ueberfaellig seit 4 Tagen oder Frostwarnung)

**Testschritte**:
1. Nutzer betrachtet die geoeffnete Notification-Liste

**Erwartete Ergebnisse**:
- `critical`-Benachrichtigungen sind visuell prominent hervorgehoben (z.B. roter Rand, Warnsymbol)
- `high`-Benachrichtigungen zeigen eine orangefarbene oder gelbe Markierung
- `normal`-Benachrichtigungen haben neutrale Darstellung
- Die Reihenfolge priorisiert hoehere Dringlichkeit oben

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, in-app, urgency, critical, high, normal, visual-hierarchy]

---

## 2. Benachrichtigungseinstellungen — Tab "Benachrichtigungen"

### TC-REQ-030-009: Notification-Einstellungs-Tab in Kontoeinstellungen navigieren

**Requirement**: REQ-030 § 5.1 — Route `/einstellungen/benachrichtigungen`, Tab 6 in AccountSettingsPage
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- AccountSettingsPage existiert mit mehreren Tabs

**Testschritte**:
1. Nutzer navigiert zu `/einstellungen` (oder klickt auf das Nutzerprofil-Icon → "Einstellungen")
2. Nutzer klickt auf den Tab "Benachrichtigungen" in der Tab-Leiste

**Erwartete Ergebnisse**:
- Der Tab "Benachrichtigungen" ist sichtbar und anklickbar
- Nach dem Klick wird der Inhalt der Benachrichtigungseinstellungen angezeigt
- Die URL aendert sich zu `/einstellungen?tab=benachrichtigungen` (oder aequivalent)
- Mindestens folgende Sektionen sind sichtbar:
  - "Kanaele" (Kanal-Toggles)
  - "Zeitplan" (Quiet Hours, Daily Summary)
  - "Batching"
  - "Eskalation"

**Nachbedingungen**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Tags**: [req-030, settings, navigation, tab, account-settings]

---

### TC-REQ-030-010: Kanalverwaltung — Uebersicht aller Kanaele

**Requirement**: REQ-030 § 5.1 Kanaele-Sektion
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf dem Tab "Benachrichtigungen" in den Kontoeinstellungen

**Testschritte**:
1. Nutzer betrachtet die Sektion "Kanaele" auf dem Benachrichtigungseinstellungen-Tab

**Erwartete Ergebnisse**:
- Mindestens folgende Kanaele werden aufgelistet mit je einem Toggle-Schalter:
  - Home Assistant (HA)
  - E-Mail
  - PWA (Browser-Push)
  - Apprise (optional, nur bei Intermediate/Expert-Stufe)
- Jeder Kanal zeigt seinen aktuellen Aktivierungsstatus (an/aus)
- Der HA-Kanal zeigt einen Verbindungsstatus-Indikator (z.B. "Verbunden" / "Nicht konfiguriert")

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, channels, toggle, ha-status, overview]

---

### TC-REQ-030-011: Home-Assistant-Kanal aktivieren

**Requirement**: REQ-030 § 5.1 Kanaele-Sektion, § 6.3 Feature-Toggle-Logik
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- HA-URL und HA-Token sind in den Servereinstellungen konfiguriert
- HA-Kanal ist aktuell deaktiviert

**Testschritte**:
1. Nutzer schaltet den Toggle "Home Assistant" auf "An"
2. Nutzer klickt auf "Speichern" (oder der Toggle speichert sofort)

**Erwartete Ergebnisse**:
- Der Toggle-Schalter wechselt visuell in den "An"-Zustand
- Eine Bestaetigung (z.B. Snackbar "Einstellungen gespeichert") erscheint
- Der Verbindungsstatus-Indikator zeigt "Verbunden" (wenn HA erreichbar)
- Die HA-spezifischen Konfigurationsoptionen werden sichtbar:
  - Toggle "Persistente Benachrichtigungen" (HA-Frontend)
  - Toggle "Mobile Push" (Companion App)
  - Toggle "Sprachansagen (TTS)"
  - Eingabefeld "TTS-Lautsprecher-Entity" (z.B. media_player.kueche)
  - Toggle "Actionable Buttons"

**Nachbedingungen**:
- HA-Kanal ist aktiviert und gespeichert
- HA-Konfigurationsoptionen sind sichtbar

**Tags**: [req-030, settings, ha-channel, enable, feature-toggle, tts, actionable-buttons]

---

### TC-REQ-030-012: Home-Assistant-Kanal zeigt "Nicht konfiguriert" wenn HA fehlt

**Requirement**: REQ-030 § 6.3 Feature-Toggle-Logik
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- HA_URL und HA_TOKEN sind NICHT in den Servereinstellungen gesetzt

**Testschritte**:
1. Nutzer betrachtet den HA-Kanal-Eintrag in der Kanaele-Sektion

**Erwartete Ergebnisse**:
- Der HA-Kanal-Toggle ist deaktiviert (ausgegraut) oder mit einem Hinweis versehen
- Ein Hinweistext wird angezeigt, z.B. "Home Assistant ist nicht konfiguriert. Bitte HA_URL und HA_TOKEN in den Servereinstellungen setzen."
- Der Toggle kann nicht aktiviert werden

**Nachbedingungen**:
- HA-Kanal bleibt deaktiviert

**Tags**: [req-030, settings, ha-channel, not-configured, disabled, error-state]

---

### TC-REQ-030-013: E-Mail-Kanal aktivieren und E-Mail-Adresse eintragen

**Requirement**: REQ-030 § 5.1 Kanaele-Sektion (E-Mail)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- E-Mail-Kanal ist aktuell deaktiviert

**Testschritte**:
1. Nutzer schaltet den Toggle "E-Mail" auf "An"
2. Ein Eingabefeld fuer die E-Mail-Adresse erscheint
3. Nutzer gibt "anna@example.com" ein
4. Nutzer waehlt den Digest-Modus "Taeglich" aus dem Dropdown
5. Nutzer waehlt Digest-Zeit "07:00"
6. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Das E-Mail-Eingabefeld wird sichtbar, wenn der Toggle aktiviert wird
- Digest-Modus-Dropdown zeigt Optionen: "Sofort" und "Taeglich"
- Digest-Zeit-Auswahl erscheint nur wenn "Taeglich" gewaehlt
- Nach dem Speichern: Snackbar "Einstellungen gespeichert" erscheint
- Die eingegebene E-Mail-Adresse bleibt gespeichert (nach Seiten-Reload sichtbar)

**Nachbedingungen**:
- E-Mail-Kanal aktiv mit "anna@example.com", Digest-Modus "Taeglich", 07:00

**Tags**: [req-030, settings, email-channel, enable, digest-mode, form-validation]

---

### TC-REQ-030-014: E-Mail-Kanal speichern ohne E-Mail-Adresse — Validierungsfehler

**Requirement**: REQ-030 § 5.1 Kanaele-Sektion (E-Mail)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- E-Mail-Toggle ist aktiviert
- Das E-Mail-Eingabefeld ist leer

**Testschritte**:
1. Nutzer laesst das E-Mail-Adressfeld leer
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Ein Validierungsfehler erscheint direkt am Eingabefeld: "E-Mail-Adresse ist erforderlich" oder aequivalent
- Das Formular wird NICHT gespeichert
- Die Einstellungsseite bleibt geoeffnet

**Nachbedingungen**:
- E-Mail-Kanal bleibt unveraendert (nicht gespeichert)

**Tags**: [req-030, settings, email-channel, validation-error, required-field]

---

### TC-REQ-030-015: Apprise-Kanal — URL eingeben (Expert-Stufe)

**Requirement**: REQ-030 § 5.1, § 5.3 Erfahrungsstufen-Integration
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Experte" gesetzt (REQ-021)
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Apprise-Kanal ist sichtbar und aktuell deaktiviert

**Testschritte**:
1. Nutzer schaltet den Toggle "Apprise" auf "An"
2. Ein Textbereich (Textarea) fuer Apprise-URLs erscheint
3. Nutzer gibt folgende URL ein: `tgram://bottoken/chatid`
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Nach dem Aktivieren des Apprise-Toggles erscheint eine Textarea fuer URLs
- Ein Hilfetext erklaert das URL-Format (z.B. "Eine URL pro Zeile. Beispiele: tgram://..., slack://..., gotify://...")
- Nach dem Speichern: Snackbar "Einstellungen gespeichert"
- Die eingegebene URL bleibt sichtbar nach dem Reload

**Nachbedingungen**:
- Apprise-Kanal aktiv mit Telegram-URL

**Tags**: [req-030, settings, apprise-channel, expert-level, urls, textarea]

---

### TC-REQ-030-016: Apprise-Kanal ist bei Beginner-Erfahrungsstufe ausgeblendet

**Requirement**: REQ-030 § 5.3 Erfahrungsstufen-Integration (Beginner: nur HA + E-Mail)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Einsteiger" (Beginner) gesetzt (REQ-021)
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet die Kanaele-Sektion

**Erwartete Ergebnisse**:
- Nur HA-Kanal und E-Mail-Kanal sind sichtbar
- Apprise-Kanal wird NICHT angezeigt
- PWA-Kanal ist ebenfalls nicht sichtbar (nur Intermediate+)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, expertise-level, beginner, apprise-hidden, channel-visibility]

---

### TC-REQ-030-017: PWA-Kanal bei Intermediate-Stufe sichtbar

**Requirement**: REQ-030 § 5.3 Erfahrungsstufen-Integration
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Fortgeschrittener" (Intermediate) gesetzt
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet die Kanaele-Sektion

**Erwartete Ergebnisse**:
- HA-Kanal, E-Mail-Kanal und PWA-Kanal sind sichtbar
- Apprise-Kanal ist NICHT sichtbar (nur Expert)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, expertise-level, intermediate, pwa-visible, apprise-hidden]

---

## 3. Quiet Hours Konfiguration

### TC-REQ-030-018: Quiet Hours aktivieren und Zeitfenster konfigurieren

**Requirement**: REQ-030 § 5.1 Zeitplan-Sektion, § 1 Grundprinzipien (Quiet Hours)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Quiet Hours sind aktuell deaktiviert

**Testschritte**:
1. Nutzer klickt in der Zeitplan-Sektion auf den Toggle "Ruhestunden aktivieren"
2. Eingabefelder "Von" und "Bis" werden sichtbar
3. Nutzer setzt "Von" auf "22:00"
4. Nutzer setzt "Bis" auf "07:00"
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Nachdem der Toggle aktiviert wurde, erscheinen Zeitfelder fuer Beginn und Ende
- Die Zeitfelder akzeptieren Eingaben im HH:MM-Format
- Nach dem Speichern: Snackbar "Einstellungen gespeichert"
- Die gespeicherten Werte bleiben nach Reload sichtbar: "22:00" und "07:00"

**Nachbedingungen**:
- Quiet Hours aktiv: 22:00–07:00

**Tags**: [req-030, settings, quiet-hours, time-range, enable, form-validation]

---

### TC-REQ-030-019: Quiet Hours Beginner-Stufe — Default-Wert nicht aenderbar

**Requirement**: REQ-030 § 5.3 Erfahrungsstufen-Integration (Beginner: Default 22-07)
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Einsteiger"
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet die Zeitplan-Sektion

**Erwartete Ergebnisse**:
- Quiet Hours sind als aktiviert und mit Standardwert "22:00–07:00" angezeigt
- Die Zeitfelder sind ausgegraut / read-only (nicht konfigurierbar fuer Beginner)
- Ein Hinweistext wie "Ruhestunden sind in der Einsteiger-Ansicht auf 22:00–07:00 festgelegt" erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, quiet-hours, beginner, readonly, default-value]

---

### TC-REQ-030-020: Quiet Hours — Ungueltige Zeitangabe zeigt Validierungsfehler

**Requirement**: REQ-030 § 5.1 Zeitplan-Sektion
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Quiet Hours sind aktiviert

**Testschritte**:
1. Nutzer setzt "Von" auf "25:00" (ungueltiger Wert)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Validierungsfehler erscheint am Eingabefeld: "Ungueltige Uhrzeit" oder aequivalent
- Das Formular wird nicht gespeichert

**Nachbedingungen**:
- Quiet Hours bleiben unveraendert

**Tags**: [req-030, settings, quiet-hours, validation-error, invalid-time]

---

## 4. Batching-Einstellungen

### TC-REQ-030-021: Batching aktivieren und Zeitfenster einstellen

**Requirement**: REQ-030 § 5.1 Batching-Sektion
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Batching-Sektion ist sichtbar

**Testschritte**:
1. Nutzer aktiviert den Batching-Toggle (falls nicht aktiv)
2. Nutzer setzt das Zeitfenster auf "30" Minuten
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eingabefeld fuer Zeitfenster (Minuten) erscheint nach Toggle-Aktivierung
- Standardwert ist "30" Minuten
- Nach Speichern: Snackbar "Einstellungen gespeichert"

**Nachbedingungen**:
- Batching aktiv mit 30-Minuten-Fenster

**Tags**: [req-030, settings, batching, window-minutes, enable]

---

### TC-REQ-030-022: Batching deaktivieren — Einzelne Benachrichtigungen

**Requirement**: REQ-030 § 5.1 Batching-Sektion
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Batching ist aktuell aktiviert

**Testschritte**:
1. Nutzer schaltet den Batching-Toggle auf "Aus"
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Das Zeitfenster-Eingabefeld verschwindet oder wird ausgegraut
- Nach Speichern: Snackbar "Einstellungen gespeichert"

**Nachbedingungen**:
- Batching deaktiviert

**Tags**: [req-030, settings, batching, disable]

---

## 5. Eskalationsstufen

### TC-REQ-030-023: Eskalation fuer Giess-Erinnerungen konfigurieren

**Requirement**: REQ-030 § 5.1 Eskalation-Sektion, § 1.2
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Eskalations-Sektion ist sichtbar

**Testschritte**:
1. Nutzer betrachtet die Eskalations-Sektion
2. Der Toggle "Giess-Eskalation aktivieren" ist standardmaessig eingeschaltet
3. Nutzer beobachtet die konfigurierten Eskalationstage: "2, 4, 7"

**Erwartete Ergebnisse**:
- Toggle "Giess-Eskalation aktivieren" ist sichtbar und standardmaessig aktiv
- Die Eskalationstage "2, 4, 7" sind konfigurierbar (Eingabefelder oder Chips)
- Ein erklaerungstext ist sichtbar: "Nach X Tagen wird die Erinnerung mit erhoehter Dringlichkeit erneut gesendet"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, escalation, watering, days-config, default-values]

---

### TC-REQ-030-024: Eskalation bei Expert-Stufe — Individuelle Tage konfigurieren

**Requirement**: REQ-030 § 5.3 (Expert: Eskalation + Tage konfigurierbar)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Experte"
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer aendert die Eskalationstage von "2, 4, 7" auf "1, 3, 5"
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Die Eskalationstage-Eingabefelder sind editierbar (bei Expert)
- Eingabe von "1, 3, 5" ist moeglich
- Nach Speichern: Snackbar "Einstellungen gespeichert"
- Die neuen Werte "1, 3, 5" bleiben nach Reload gespeichert

**Nachbedingungen**:
- Eskalationstage auf 1, 3, 5 gesetzt

**Tags**: [req-030, settings, escalation, expert-level, custom-days]

---

### TC-REQ-030-025: Eskalation deaktivieren

**Requirement**: REQ-030 § 5.1 Eskalation-Sektion
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Eskalation ist aktuell aktiviert

**Testschritte**:
1. Nutzer schaltet den Toggle "Giess-Eskalation aktivieren" auf "Aus"
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Die Eskalationstage-Felder verschwinden oder werden ausgegraut
- Nach Speichern: Snackbar "Einstellungen gespeichert"

**Nachbedingungen**:
- Eskalation deaktiviert

**Tags**: [req-030, settings, escalation, disable]

---

## 6. Typ-Overrides

### TC-REQ-030-026: Typ-Overrides sind bei Beginner-Stufe ausgeblendet

**Requirement**: REQ-030 § 5.3 Erfahrungsstufen (Beginner: Typ-Overrides ausgeblendet)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Einsteiger"
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet den gesamten Benachrichtigungseinstellungen-Tab

**Erwartete Ergebnisse**:
- Es gibt keine Sektion "Typ-Overrides" oder "Benachrichtigungstypen"
- Die Seite zeigt nur die fuer Einsteiger relevanten Sektionen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, type-overrides, beginner, hidden]

---

### TC-REQ-030-027: Typ-Override fuer Giess-Erinnerung konfigurieren (Intermediate)

**Requirement**: REQ-030 § 5.1 Typ-Overrides, § 5.3 (Intermediate: vereinfacht)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Fortgeschrittener"
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Mindestens HA und E-Mail Kanaele sind aktiviert

**Testschritte**:
1. Nutzer klickt auf die Sektion "Benachrichtigungstypen" oder "Typ-Overrides"
2. Nutzer findet den Eintrag "Giess-Erinnerung" in der Liste
3. Nutzer waehlt als Kanal "Nur Home Assistant" aus
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Die Typ-Override-Sektion zeigt eine vereinfachte Liste der wichtigsten Benachrichtigungstypen
- Fuer "Giess-Erinnerung" kann ein Kanal gewaehlt werden
- Nach Speichern: Snackbar "Einstellungen gespeichert"

**Nachbedingungen**:
- Giess-Erinnerungen werden nur ueber HA-Kanal zugestellt

**Tags**: [req-030, settings, type-overrides, intermediate, watering-channel]

---

### TC-REQ-030-028: Typ-Override sensor.alert — Quiet Hours ignorieren (Expert)

**Requirement**: REQ-030 § 5.1 Typ-Overrides, § 1 (ignore_quiet_hours)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Experte"
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Quiet Hours sind aktiviert (22:00–07:00)

**Testschritte**:
1. Nutzer oeffnet den vollstaendigen Typ-Overrides-Bereich
2. Nutzer findet den Eintrag "Sensor-Alarm (sensor.alert)"
3. Der Schalter "Ruhestunden ignorieren" ist fuer diesen Typ standardmaessig aktiviert
4. Nutzer belaesst den Schalter aktiv und klickt "Speichern"

**Erwartete Ergebnisse**:
- Fuer "Sensor-Alarm" gibt es einen Schalter "Ruhestunden ignorieren"
- Dieser ist standardmaessig aktiviert (kritische Alarme werden immer zugestellt)
- Nach Speichern: Snackbar "Einstellungen gespeichert"
- Erklaerungstext: "Sensor-Alarme werden auch waehrend der Ruhestunden zugestellt"

**Nachbedingungen**:
- sensor.alert ignoriert Quiet Hours

**Tags**: [req-030, settings, type-overrides, expert, quiet-hours-override, sensor-alert]

---

## 7. Test-Notification senden

### TC-REQ-030-029: Test-Notification fuer aktivierten HA-Kanal senden

**Requirement**: REQ-030 § 5.1 Test-Button, § 3.11 POST /test
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- HA-Kanal ist aktiviert und HA-Verbindung ist aktiv

**Testschritte**:
1. Nutzer klickt auf den Button "Test senden" neben dem Home-Assistant-Kanal

**Erwartete Ergebnisse**:
- Eine Ladeanzeige erscheint kurz am Button
- Nach erfolgreicher Zustellung: Snackbar oder Hinweis "Test-Benachrichtigung ueber Home Assistant gesendet"
- Im HA-Frontend erscheint eine persistente Notification "Kamerplanter Test" (extern verifizierbar)

**Nachbedingungen**:
- Test-Notification wurde zugestellt

**Tags**: [req-030, settings, test-notification, ha-channel, success]

---

### TC-REQ-030-030: Test-Notification fuer E-Mail-Kanal senden

**Requirement**: REQ-030 § 5.1 Test-Button
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- E-Mail-Kanal ist aktiviert mit konfigurierter Adresse "anna@example.com"

**Testschritte**:
1. Nutzer klickt auf den Button "Test senden" neben dem E-Mail-Kanal

**Erwartete Ergebnisse**:
- Eine Ladeanzeige erscheint kurz am Button
- Nach erfolgreicher Zustellung: Snackbar "Test-Benachrichtigung an anna@example.com gesendet"

**Nachbedingungen**:
- Test-E-Mail wurde an anna@example.com versandt

**Tags**: [req-030, settings, test-notification, email-channel, success]

---

### TC-REQ-030-031: Test-Notification fuer nicht konfigurierten Kanal schlaegt fehl

**Requirement**: REQ-030 § 5.1 Test-Button, § 7 Rate-Limiting (5/Stunde)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- E-Mail-Kanal ist aktiviert, aber die E-Mail-Adresse ist leer oder SMTP ist nicht konfiguriert

**Testschritte**:
1. Nutzer klickt auf "Test senden" neben dem E-Mail-Kanal

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Test-Benachrichtigung konnte nicht gesendet werden. Ursache: [Fehlertext]"
- Kein Snackbar-Erfolg erscheint

**Nachbedingungen**:
- Keine Test-Notification zugestellt

**Tags**: [req-030, settings, test-notification, failure, error-message]

---

### TC-REQ-030-032: Test-Notification Rate-Limit (5 pro Stunde) erschoepft

**Requirement**: REQ-030 § 7 Rate-Limiting (5/Stunde fuer /test)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Nutzer hat in der letzten Stunde bereits 5 Test-Notifications gesendet

**Testschritte**:
1. Nutzer klickt erneut auf "Test senden" fuer einen beliebigen Kanal

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Zu viele Test-Benachrichtigungen. Bitte warte eine Stunde." oder aequivalent
- Der Test-Button ist fuer eine Zeit deaktiviert oder zeigt einen Countdown

**Nachbedingungen**:
- Keine weitere Test-Notification gesendet

**Tags**: [req-030, settings, test-notification, rate-limit, error-message]

---

### TC-REQ-030-033: Test-Button bei Expert-Stufe zeigt Response-Details

**Requirement**: REQ-030 § 5.3 (Expert: Test-Button + Response-Details)
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Experte"
- HA-Kanal ist aktiviert und verbunden

**Testschritte**:
1. Nutzer klickt auf "Test senden" neben dem HA-Kanal

**Erwartete Ergebnisse**:
- Zusaetzlich zur Erfolgs-Snackbar erscheinen technische Details der Antwort
- Z.B.: Kanal-Key, externe ID, Zeitstempel der Zustellung
- Diese Details sind bei Beginner/Intermediate nicht sichtbar

**Nachbedingungen**:
- Test-Notification zugestellt, Details angezeigt

**Tags**: [req-030, settings, test-notification, expert-level, response-details]

---

## 8. Kanal-Statusanzeige

### TC-REQ-030-034: Kanal-Status-Uebersicht aufrufen

**Requirement**: REQ-030 § 3.11 GET /channels/status
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Mindestens ein Kanal ist konfiguriert

**Testschritte**:
1. Nutzer sucht in der Kanaele-Sektion nach Status-Indikatoren oder klickt auf einen "Status pruefen"-Button

**Erwartete Ergebnisse**:
- Fuer jeden konfigurierten Kanal wird ein Status-Indikator angezeigt:
  - Gruener Punkt / "Verbunden" — Kanal erreichbar
  - Gelber Punkt / "Konfiguriert, nicht getestet" — Kanal konfiguriert aber unbekannter Status
  - Roter Punkt / "Nicht erreichbar" — Health-Check fehlgeschlagen
- Der HA-Kanal zeigt bei gesetzter Verbindung "Verbunden" mit HA-URL

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, channel-status, health-check, connected, disconnected]

---

### TC-REQ-030-035: HA-Kanal zeigt "Nicht erreichbar" bei ausgefallener HA-Instanz

**Requirement**: REQ-030 § 3.11 GET /channels/status
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- HA-URL ist in den Servereinstellungen gesetzt
- Die HA-Instanz ist jedoch nicht erreichbar (Netzwerkfehler oder abgestuerzt)
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer laedt den Benachrichtigungseinstellungen-Tab
2. Nutzer betrachtet den HA-Kanal-Status

**Erwartete Ergebnisse**:
- HA-Kanal zeigt einen roten Indikator "Nicht erreichbar"
- Ein Hinweistext erscheint: "Home Assistant ist nicht erreichbar. Bitte Verbindung pruefen."
- Der HA-Toggle ist aktiv aber der Status ist rot

**Nachbedingungen**:
- Kein Status geaendert (HA bleibt konfiguriert aber nicht erreichbar)

**Tags**: [req-030, settings, ha-channel, not-reachable, error-state, health-check]

---

## 9. Daily Summary Konfiguration

### TC-REQ-030-036: Daily Summary aktivieren

**Requirement**: REQ-030 § 5.1 Zeitplan-Sektion (Daily Summary)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Daily Summary ist aktuell deaktiviert

**Testschritte**:
1. Nutzer schaltet in der Zeitplan-Sektion den Toggle "Taegliche Zusammenfassung" auf "An"
2. Ein Zeitfeld "Uhrzeit" und ein Kanal-Dropdown erscheinen
3. Nutzer setzt die Uhrzeit auf "07:00"
4. Nutzer waehlt Kanal "Home Assistant"
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Toggle laesst sich aktivieren
- Zeitfeld und Kanal-Dropdown erscheinen nach Aktivierung
- Kanal-Dropdown zeigt nur aktivierte Kanaele als Optionen
- Nach Speichern: Snackbar "Einstellungen gespeichert"

**Nachbedingungen**:
- Daily Summary aktiv: 07:00 Uhr, Kanal: Home Assistant

**Tags**: [req-030, settings, daily-summary, time, channel-selection, enable]

---

### TC-REQ-030-037: Daily Summary Kanal-Dropdown zeigt nur aktive Kanaele

**Requirement**: REQ-030 § 5.1 Zeitplan-Sektion (Daily Summary)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Nur E-Mail-Kanal ist aktiviert; HA und PWA sind deaktiviert
- Daily Summary Toggle ist aktiviert

**Testschritte**:
1. Nutzer oeffnet das Kanal-Dropdown fuer die Daily Summary

**Erwartete Ergebnisse**:
- Das Dropdown zeigt nur "E-Mail" als Option
- HA, PWA und Apprise sind NICHT im Dropdown (da deaktiviert)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, settings, daily-summary, channel-dropdown, only-active-channels]

---

## 10. Feature-Toggle-Logik und Fallback

### TC-REQ-030-038: Kein Kanal konfiguriert — InApp-Fallback aktiv

**Requirement**: REQ-030 § 6.3 Feature-Toggle-Logik (InApp als Fallback)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer hat KEINE externen Kanaele konfiguriert (HA, E-Mail, PWA, Apprise alle deaktiviert)
- Eine Pflegeerinnerung wurde vom System generiert

**Testschritte**:
1. Nutzer navigiert zum Dashboard
2. Nutzer betrachtet das Bell-Icon in der AppBar

**Erwartete Ergebnisse**:
- Das Bell-Icon zeigt ein Badge mit der Anzahl ungelesener InApp-Benachrichtigungen
- Beim Oeffnen des Notification Centers ist die Pflegeerinnerung sichtbar
- Die App funktioniert vollstaendig ohne externe Kanalkonfiguration
- Das Pflege-Dashboard (REQ-022) zeigt die faelligen Tasks wie gewohnt

**Nachbedingungen**:
- InApp-Benachrichtigung ist in der Liste sichtbar

**Tags**: [req-030, fallback, in-app, no-channel, feature-toggle, pflege-dashboard]

---

### TC-REQ-030-039: PWA-Kanal ohne VAPID-Keys deaktiviert

**Requirement**: REQ-030 § 6.3 Feature-Toggle-Logik (VAPID Keys → PWA aktiv)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- VAPID_PRIVATE_KEY und VAPID_PUBLIC_KEY sind NICHT in den Servereinstellungen gesetzt
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet den PWA-Kanal-Eintrag in der Kanaele-Sektion

**Erwartete Ergebnisse**:
- Der PWA-Toggle ist ausgegraut oder deaktiviert
- Ein Hinweis erscheint: "PWA-Push ist auf diesem Server nicht konfiguriert"
- Der Nutzer kann den PWA-Kanal nicht aktivieren

**Nachbedingungen**:
- PWA-Kanal bleibt deaktiviert

**Tags**: [req-030, settings, pwa-channel, vapid, not-configured, disabled]

---

## 11. Notifications in der InApp-Liste — Typen und Inhalte

### TC-REQ-030-040: Giess-Erinnerung erscheint in Notification Center (InApp)

**Requirement**: REQ-030 § 1.1 Notification-Typen (care.watering)
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Keine externen Kanaele konfiguriert (InApp-Fallback)
- REQ-022 hat 3 faellige Giess-Tasks generiert (Monstera, Ficus, Basilikum)
- Das Celery-Batching hat eine Batch-Notification erstellt

**Testschritte**:
1. Nutzer klickt auf das Bell-Icon in der AppBar

**Erwartete Ergebnisse**:
- Eine Benachrichtigung "3 Pflanzen giessen heute" ist in der Liste sichtbar
- Der Benachrichtigungstext nennt die Pflanzennamen: "Monstera, Ficus und Basilikum brauchen heute Wasser."
- Dringlichkeit: "normal" (keine Eskalation)
- Zeitstempel zeigt wann die Benachrichtigung erstellt wurde

**Nachbedingungen**:
- Benachrichtigung ist sichtbar (ungelesen)

**Tags**: [req-030, in-app, care-watering, batch, notification-content]

---

### TC-REQ-030-041: Frostwarnung erscheint als kritische Notification

**Requirement**: REQ-030 § 1.1 (weather.frost, critical)
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Eine Frostwarnung wurde vom System generiert (weather.frost, urgency=critical)

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Eine Notification "Frostwarnung morgen Nacht: -3°C erwartet" erscheint in der Liste
- Diese ist visuell als kritisch markiert (z.B. roter Hintergrund, Warnsymbol)
- Die Frostwarnung erscheint ganz oben (hoechste Prioritaet)

**Nachbedingungen**:
- Frostwarnung ist als ungelesen sichtbar

**Tags**: [req-030, in-app, frost-warning, critical-urgency, visual-priority, weather]

---

### TC-REQ-030-042: Tank-Alarm erscheint in Notification Center

**Requirement**: REQ-030 § 1.1 (tank.low, high)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Tank A hat Fuellstand unter 20% (tank.low generiert)

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Notification "Tank A: Fuellstand unter 20%" ist sichtbar
- Dringlichkeit: "high" (orangefarbene Markierung)
- Klick navigiert zur Tank-Verwaltungsseite

**Nachbedingungen**:
- Tank-Alarm ist als ungelesen sichtbar

**Tags**: [req-030, in-app, tank-alert, high-urgency, navigation]

---

### TC-REQ-030-043: Ueberfaellige Giess-Erinnerung zeigt Eskalationsstufe in der Liste

**Requirement**: REQ-030 § 1.2 Eskalationsstufen
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Eine Giess-Erinnerung fuer Monstera wurde vor 2 Tagen nicht bestaetigt
- Eskalation hat eine neue Notification erstellt: "UEBERFAELLIG: Monstera giessen (seit 2 Tagen!)"

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Notification "UEBERFAELLIG: Monstera giessen (seit 2 Tagen!)" erscheint in der Liste
- Dringlichkeit ist "high" (orange/gelbe Markierung)
- Der Text enthalt den Hinweis auf die Ueberfaelligkeit (Tage)

**Nachbedingungen**:
- Eskalations-Notification ist als ungelesen sichtbar

**Tags**: [req-030, in-app, escalation, overdue, high-urgency, watering]

---

### TC-REQ-030-044: Actionable Notification — "Erledigt"-Button bestaetigt Pflegeerinnerung

**Requirement**: REQ-030 § 3.11 POST /{key}/act (action_id=confirm_watering)
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Notification Center ist geoeffnet
- Eine Giess-Erinnerung mit "Erledigt"-Button ist sichtbar (Notification mit actions)

**Testschritte**:
1. Nutzer sieht in der Notification-Liste einen Eintrag mit einem "Erledigt"-Button
2. Nutzer klickt auf den "Erledigt"-Button

**Erwartete Ergebnisse**:
- Die Benachrichtigung verschwindet aus der ungelesenen Liste oder wird als "bearbeitet" markiert
- Eine Bestaetigung erscheint: Snackbar "Pflegeaufgabe bestaetigt"
- Der Pflege-Task in REQ-022 wird als erledigt markiert (das Pflege-Dashboard zeigt den Task nicht mehr als faellig)
- Der Badge-Zaehler am Bell-Icon reduziert sich

**Nachbedingungen**:
- Pflegeaufgabe wurde bestaetigt (acted_at gesetzt)
- Benachrichtigung ist als "bearbeitet" markiert

**Tags**: [req-030, in-app, actionable, confirm-watering, care-confirmation, acted]

---

### TC-REQ-030-045: Phasen-Uebergang erscheint als normale Notification

**Requirement**: REQ-030 § 1.1 (phase.transition, normal)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Eine Pflanze hat die Bluetephase erreicht (phase.transition generiert)

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Notification "Basilikum: Bluetephase erreicht" erscheint in der Liste
- Dringlichkeit: "normal" (neutrale Darstellung)
- Klick auf die Notification navigiert zur Pflanzen-Detailseite

**Nachbedingungen**:
- Phase-Notification ist sichtbar (ungelesen)

**Tags**: [req-030, in-app, phase-transition, normal-urgency, navigation]

---

### TC-REQ-030-046: IPM-Alarm erscheint als hochdringliche Notification

**Requirement**: REQ-030 § 1.1 (ipm.alert, high)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- IPM hat Spinnmilben-Befall erkannt (ipm.alert generiert)

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Notification "Spinnmilben erkannt bei Monstera" erscheint in der Liste
- Dringlichkeit: "high" (orangefarbene Markierung)
- Klick navigiert zur IPM-Seite der betroffenen Pflanze

**Nachbedingungen**:
- IPM-Alarm ist als ungelesen sichtbar

**Tags**: [req-030, in-app, ipm-alert, high-urgency, navigation]

---

## 12. Einstellungen — Seitenwechsel und unsaved Changes

### TC-REQ-030-047: Benachrichtigungseinstellungen — unsaved Changes Guard

**Requirement**: REQ-030 § 5.1 (Einstellungsseite)
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- Nutzer hat Aenderungen vorgenommen (z.B. E-Mail-Toggle aktiviert) aber NICHT gespeichert

**Testschritte**:
1. Nutzer klickt auf einen anderen Tab in den Kontoeinstellungen (z.B. "Profil")

**Erwartete Ergebnisse**:
- Ein Bestaetgungsdialog erscheint: "Sie haben ungespeicherte Aenderungen. Moechten Sie die Seite wirklich verlassen?"
- Nutzer kann "Verlassen" oder "Bleiben" waehlen
- Bei "Verlassen": Tab wechselt, Aenderungen werden verworfen
- Bei "Bleiben": Nutzer bleibt auf dem Benachrichtigungseinstellungen-Tab

**Nachbedingungen**:
- Je nach Wahl: Tab gewechselt (Aenderungen verworfen) ODER unveraendert auf Benachrichtigungs-Tab

**Tags**: [req-030, settings, unsaved-changes-guard, dialog, navigation]

---

### TC-REQ-030-048: Benachrichtigungseinstellungen erfolgreich laden

**Requirement**: REQ-030 § 3.11 GET /preferences
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer hat Einstellungen gespeichert (E-Mail aktiv, Quiet Hours 22:00-07:00, Batching an)
- Nutzer ladet die Seite neu

**Testschritte**:
1. Nutzer druckt F5 (Seite neu laden)
2. Nutzer navigiert zum Tab "Benachrichtigungen"

**Erwartete Ergebnisse**:
- Alle gespeicherten Einstellungen werden korrekt angezeigt:
  - E-Mail-Toggle: aktiv
  - E-Mail-Adresse: "anna@example.com"
  - Quiet Hours: aktiviert, 22:00–07:00
  - Batching: aktiviert, 30 Minuten

**Nachbedingungen**:
- Einstellungen sind unveraendert und korrekt geladen

**Tags**: [req-030, settings, preferences, persistence, page-reload]

---

## 13. Benachrichtigungs-History und Pagination

### TC-REQ-030-049: Benachrichtigungs-Liste zeigt bis zu 50 Eintraege

**Requirement**: REQ-030 § 3.11 GET /notifications (limit=50)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat mehr als 50 Benachrichtigungen in der Geschichte
- Notification Center ist geoeffnet

**Testschritte**:
1. Nutzer scrollt in der Notification-Liste nach unten

**Erwartete Ergebnisse**:
- Maximal 50 Benachrichtigungen werden initial angezeigt
- Ein "Mehr laden"-Button oder Endless Scroll laedt weitere Eintraege nach
- Die Gesamtanzahl ist sichtbar (z.B. "Zeigt 50 von 127 Benachrichtigungen")

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, in-app, pagination, load-more, list-limit]

---

### TC-REQ-030-050: Nur ungelesene Benachrichtigungen filtern

**Requirement**: REQ-030 § 3.11 GET /notifications (unread_only=true)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Nutzer hat 3 ungelesene und 10 gelesene Benachrichtigungen

**Testschritte**:
1. Nutzer klickt auf einen Filter "Nur ungelesene" oder aktiviert eine entsprechende Option im Notification Center

**Erwartete Ergebnisse**:
- Nur die 3 ungelesenen Benachrichtigungen werden angezeigt
- Gelesene Benachrichtigungen sind ausgeblendet
- Ein Zaehler zeigt "3 ungelesene"

**Nachbedingungen**:
- Kein Status geaendert (nur Filteransicht)

**Tags**: [req-030, in-app, filter, unread-only, list-view]

---

## 14. i18n und Texte

### TC-REQ-030-051: Alle Benachrichtigungseinstellungen sind in Deutsch angezeigt

**Requirement**: REQ-030 § 9 DoD (i18n: DE und EN)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat die App-Sprache auf "Deutsch" eingestellt (Standard)
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet alle Sektionen auf dem Benachrichtigungseinstellungen-Tab

**Erwartete Ergebnisse**:
- Alle Labels sind auf Deutsch:
  - "Kanaele", "Home Assistant", "E-Mail", "PWA", "Apprise"
  - "Ruhestunden", "Von", "Bis"
  - "Batching aktivieren", "Zeitfenster"
  - "Giess-Eskalation aktivieren"
  - "Taegliche Zusammenfassung"
  - "Test senden", "Speichern"
- Keine englischen Strings oder Platzhalter sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, i18n, deutsch, labels, complete-translation]

---

### TC-REQ-030-052: Benachrichtigungen sind in Englisch angezeigt wenn EN-Locale

**Requirement**: REQ-030 § 9 DoD (i18n: DE und EN)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat die App-Sprache auf "English" umgestellt
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer betrachtet die Sektionen auf dem Benachrichtigungseinstellungen-Tab

**Erwartete Ergebnisse**:
- Alle Labels sind auf Englisch:
  - "Channels", "Home Assistant", "Email", "PWA", "Apprise"
  - "Quiet Hours", "From", "To"
  - "Enable Batching", "Time Window"
  - "Enable Watering Escalation"
  - "Daily Summary"
  - "Send Test", "Save"
- Keine deutschen Texte sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, i18n, english, labels, locale-switch]

---

## 15. Authentifizierung und Tenant-Scoping

### TC-REQ-030-053: Nicht eingeloggter Nutzer kann Notification Center nicht sehen

**Requirement**: REQ-030 § 7 Authentifizierung (JWT + Tenant)
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist NICHT eingeloggt

**Testschritte**:
1. Nutzer versucht direkt zu `/einstellungen/benachrichtigungen` zu navigieren

**Erwartete Ergebnisse**:
- Weiterleitung zur Login-Seite (`/login`)
- Das Bell-Icon in der AppBar ist nicht sichtbar (da AppBar nur fuer eingeloggte Nutzer)

**Nachbedingungen**:
- Nutzer wird zur Login-Seite weitergeleitet

**Tags**: [req-030, auth, unauthenticated, redirect, protected-route]

---

### TC-REQ-030-054: Nutzer sieht nur eigene Benachrichtigungen (Tenant-Isolation)

**Requirement**: REQ-030 § 7 (nur eigene Notifications)
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Zwei Nutzer (Anna und Bob) sind Mitglieder desselben Tenants
- Anna hat 3 Benachrichtigungen, Bob hat 2 Benachrichtigungen
- Anna ist eingeloggt

**Testschritte**:
1. Anna oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Nur Annas 3 Benachrichtigungen werden angezeigt
- Bobs Benachrichtigungen sind NICHT sichtbar
- Die Gesamtzahl im Badge ist "3"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, auth, tenant-isolation, user-scoped, security]

---

## 16. Edge Cases und Grenzwerte

### TC-REQ-030-055: Badge-Zaehler bei mehr als 99 ungelesenen Notifications

**Requirement**: REQ-030 § 5.2 Bell-Icon Badge
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat mehr als 99 ungelesene Benachrichtigungen (z.B. 127)

**Testschritte**:
1. Nutzer betrachtet das Bell-Icon in der AppBar

**Erwartete Ergebnisse**:
- Das Badge zeigt "99+" statt "127" (um Platz zu sparen)
- Oder alternativ ein Kreis ohne Zahl bei sehr grossen Zahlen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, in-app, badge, overflow, 99-plus, edge-case]

---

### TC-REQ-030-056: Benachrichtigungseinstellungen — Apprise URL-Liste leer speichern

**Requirement**: REQ-030 § 5.1 (Apprise-Kanal, leere URL-Liste)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Experte"
- Apprise-Toggle ist aktiviert
- Die URL-Textarea ist leer

**Testschritte**:
1. Nutzer klickt "Speichern" mit leerem Apprise-URL-Feld

**Erwartete Ergebnisse**:
- Validierungsfehler: "Mindestens eine Apprise-URL ist erforderlich wenn Apprise aktiviert ist"
- Das Formular wird nicht gespeichert

**Nachbedingungen**:
- Apprise-Einstellungen bleiben unveraendert

**Tags**: [req-030, settings, apprise-channel, validation-error, empty-urls]

---

### TC-REQ-030-057: Gleichzeitige Eskalations-Notification und neue Notification

**Requirement**: REQ-030 § 1.2 Eskalation, § 3.8 Dedup
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Eine bestehende Giess-Erinnerung wurde eskaliert (escalation_level=1)
- Gleichzeitig wurde eine neue Giess-Erinnerung fuer eine andere Pflanze generiert

**Testschritte**:
1. Nutzer betrachtet die Notification-Liste

**Erwartete Ergebnisse**:
- BEIDE Notifications sind sichtbar (Eskalation und neue)
- Die Eskalations-Notification (urgency=high) erscheint hoeher in der Liste
- Es gibt keine Verdoppelung (Dedup verhindert doppeltes Senden derselben Notification)

**Nachbedingungen**:
- Beide Notifications sind separat sichtbar

**Tags**: [req-030, in-app, escalation, dedup, list-ordering, edge-case]

---

### TC-REQ-030-058: Notification-Einstellungen bei erstmaligem Aufruf (Default-Werte)

**Requirement**: REQ-030 § 3.8 _default_preferences
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Neuer Nutzer hat sich gerade registriert (noch keine Benachrichtigungseinstellungen)
- Nutzer navigiert zum Benachrichtigungseinstellungen-Tab

**Testschritte**:
1. Nutzer oeffnet den Benachrichtigungseinstellungen-Tab zum ersten Mal

**Erwartete Ergebnisse**:
- Alle Kanaele sind standardmaessig deaktiviert
- Quiet Hours sind aktiviert mit Standard: 22:00–07:00
- Batching ist aktiviert mit Standard: 30 Minuten
- Eskalation (Giessen) ist standardmaessig aktiviert mit Tagen: 2, 4, 7
- InApp-Fallback ist aktiv (Bell-Icon erscheint auch ohne externe Kanaele)

**Nachbedingungen**:
- Default-Einstellungen werden korrekt angezeigt

**Tags**: [req-030, settings, defaults, new-user, first-time, quiet-hours-default]

---

### TC-REQ-030-059: Notification-Details — Vollstaendiger Text lesbar

**Requirement**: REQ-030 § 5.2 In-App Notification Center
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Eine Batch-Benachrichtigung mit langem Text ist vorhanden: "8 Pflanzen giessen heute: Monstera, Ficus, Basilikum, Orchidee, Calathea, Pothos, Dracaena, Yucca"

**Testschritte**:
1. Nutzer klickt auf die Batch-Benachrichtigung um sie zu expandieren oder zu oeffnen

**Erwartete Ergebnisse**:
- Der vollstaendige Benachrichtigungstext ist lesbar (ggf. nach Expand)
- In der Listenansicht kann der Text abgeschnitten sein (z.B. "8 Pflanzen giessen heute: Monstera, Ficus...")
- Im Detail-/Expandierten-View sind alle Pflanzennamen sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-030, in-app, long-text, expand, detail-view, batch-notification]

---

### TC-REQ-030-060: HA-Kanal TTS-Entity eingeben und validieren

**Requirement**: REQ-030 § 5.1 HA-Kanaloptionen (TTS)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf dem Benachrichtigungseinstellungen-Tab
- HA-Kanal ist aktiviert
- TTS-Toggle ist aktiviert

**Testschritte**:
1. Nutzer aktiviert den TTS-Toggle
2. Das Eingabefeld "TTS-Lautsprecher-Entity" erscheint
3. Nutzer gibt "media_player.kueche" ein
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Das TTS-Entity-Feld erscheint nach Toggle-Aktivierung
- Eingabe von "media_player.kueche" ist moeglich
- Nach Speichern: Snackbar "Einstellungen gespeichert"
- Der Wert bleibt nach Reload gespeichert

**Nachbedingungen**:
- TTS aktiviert mit entity_id "media_player.kueche"

**Tags**: [req-030, settings, ha-channel, tts, entity-id, form-validation]

---

### TC-REQ-030-061: Ernte-bereit Notification erscheint in der Liste

**Requirement**: REQ-030 § 1.1 (harvest.ready, normal)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- REQ-007 hat Ernte-Bereitschaft erkannt (harvest.ready)

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Notification "Tomaten: Erntebereitschaft erkannt" erscheint in der Liste
- Dringlichkeit: "normal"
- Klick navigiert zur Ernte-Seite

**Nachbedingungen**:
- Harvest-Notification ist sichtbar

**Tags**: [req-030, in-app, harvest-ready, normal-urgency, navigation]

---

### TC-REQ-030-062: Karenz-Ablauf Notification erscheint in der Liste

**Requirement**: REQ-030 § 1.1 (ipm.karenz_end, normal)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Notification Center ist geoeffnet
- Karenzzeit fuer eine Behandlung ist abgelaufen (ipm.karenz_end generiert)

**Testschritte**:
1. Nutzer oeffnet das Notification Center

**Erwartete Ergebnisse**:
- Notification "Karenzzeit abgelaufen: Tomate erntereif" erscheint in der Liste
- Dringlichkeit: "normal"
- Klick navigiert zur IPM/Karenz-Statusseite

**Nachbedingungen**:
- Karenz-Ablauf-Notification ist sichtbar

**Tags**: [req-030, in-app, karenz-end, ipm, normal-urgency, navigation]

---

## Abdeckungsmatrix

| Spezifikationsabschnitt | Test Cases | Abdeckungsstatus |
|--------------------------|------------|-----------------|
| § 1.1 Notification-Typen (alle 15 Typen) | TC-030-040..046, 061, 062 | Stichproben der wichtigsten Typen (care.watering, weather.frost, tank.low, phase.transition, ipm.alert, harvest.ready, ipm.karenz_end) |
| § 1.2 Eskalationsstufen (Tag 0, +2, +4, +7) | TC-030-043, 023, 024, 025 | Happy Path + Konfiguration |
| § 5.1 Notification-Einstellungsseite | TC-030-009..037, 047, 048, 056, 058, 060 | Alle Sektionen abgedeckt |
| § 5.1 Kanaele (HA, E-Mail, PWA, Apprise) | TC-030-010..017 | Alle 4 Kanaele + Feature-Toggle |
| § 5.1 Quiet Hours | TC-030-018..020 | Happy Path + Validierung + Beginner |
| § 5.1 Batching | TC-030-021..022 | Aktivieren und Deaktivieren |
| § 5.1 Eskalation-Sektion | TC-030-023..025 | Konfiguration + Expert |
| § 5.1 Typ-Overrides | TC-030-026..028 | Alle Stufen + quiet_hours_override |
| § 5.1 Test-Button | TC-030-029..033 | Erfolg + Fehler + Rate-Limit + Expert |
| § 5.2 In-App Notification Center | TC-030-001..008 | Bell-Icon, Badge, Liste, Navigation, Swipe, Dringlichkeit |
| § 5.2 Actionable Buttons (In-App) | TC-030-044 | Erledigt-Button → CareConfirmation |
| § 5.3 Erfahrungsstufen | TC-030-016, 017, 019, 024, 026, 027, 028, 033 | Alle 3 Stufen fuer relevante Elemente |
| § 6.3 Feature-Toggle-Logik | TC-030-011, 012, 038, 039 | HA, InApp-Fallback, PWA/VAPID |
| § 7 Authentifizierung / Tenant-Isolation | TC-030-053, 054 | Unauthenticated + User-Scoping |
| § 3.11 REST-API (list, read, act, prefs, test) | TC-030-004, 005, 029, 044, 048 | Via UI-Interaktion |
| i18n DE/EN | TC-030-051, 052 | Beide Sprachen |
| Edge Cases / Grenzwerte | TC-030-055..060 | Badge 99+, leere URLs, Defaults, langer Text |
