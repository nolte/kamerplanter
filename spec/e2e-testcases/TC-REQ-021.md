---
req_id: REQ-021
title: Dreistufiger UI-Modus (Einsteiger / Fortgeschritten / Experte)
category: Benutzerführung
test_count: 52
coverage_areas:
  - Erfahrungsstufen-Umschalter (AccountSettingsPage Tab "Erfahrungsstufe")
  - Onboarding-Schritt ExperienceLevelStep (Erstauswahl)
  - Serverseitige Persistenz (geräteübergreifende Wiederherstellung)
  - Navigations-Tiering (Seitenleiste, 3 Stufen)
  - Feld-Sichtbarkeit SpeciesCreateDialog
  - Feld-Sichtbarkeit PlantingRunCreateDialog
  - Feld-Sichtbarkeit SiteCreateDialog / WaterSourceSection
  - Feld-Sichtbarkeit GrowthPhaseDialog
  - Feld-Sichtbarkeit FertilizerCreateDialog
  - ShowAllFieldsToggle ("Alle Felder anzeigen" / "Weniger Felder anzeigen")
  - Downgrade-Warnung (window.confirm)
  - Kein Datenverlust bei Moduswechsel
  - NutrientCalculationsPage — Kalkulator-Sichtbarkeit
  - Quick-Add-Plant-Dialog (Beginner-Flow, Abschnitt 3.8)
  - Default-Wert für neue Nutzer
  - i18n-Sprachumschaltung (DE/EN)
generated: 2026-03-21
version: "1.1"
---

# TC-REQ-021: Dreistufiger UI-Modus (Erfahrungsstufen)

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-021 Erfahrungsstufen-basierter UI-Modus v1.1**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Schritte beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen entsprechen den deutschen i18n-Texten. Der Modus wird serverseitig in der `user_preferences`-Collection gespeichert und beim Login automatisch geladen; das Backend liefert immer alle Daten — die Filterung erfolgt ausschliesslich im Frontend.

---

## 1. Onboarding — Erstauswahl der Erfahrungsstufe

### TC-021-001: Neuer Nutzer sieht Erfahrungsstufen-Auswahl im Onboarding

**Requirement**: REQ-021 § 4 — Default `beginner` für neue Nutzer; REQ-020 Onboarding-Wizard
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer hat sich neu registriert und startet den Onboarding-Wizard zum ersten Mal
- Die Seite `/onboarding` ist geöffnet
- Schritt mit Erfahrungsstufen-Auswahl ist aktiv (ExperienceLevelStep)

**Testschritte**:
1. Nutzer betrachtet den Onboarding-Schritt mit der Überschrift zur Erfahrungsstufe
2. Nutzer beobachtet die drei Auswahlkarten (Cards)

**Erwartete Ergebnisse**:
- Drei Karten sind sichtbar: "Anfänger" (EmojiNature-Icon), "Fortgeschritten" (School-Icon), "Experte" (Science-Icon)
- Die Karte "Anfänger" ist standardmäßig ausgewählt (blau umrandet, fetter Schriftschnitt des Labels)
- Unterhalb jeder Karte ist eine Kurzbeschreibung sichtbar ("Einfache Ansicht mit den wichtigsten Feldern" / "Erweiterte Optionen für erfahrene Nutzer" / "Alle Felder und Funktionen sichtbar")
- Die Smart-Home-Sektion ist **nicht** sichtbar, solange "Anfänger" ausgewählt ist

**Nachbedingungen**:
- Keine Änderung am gespeicherten Präferenz-Wert (noch im Wizard-Flow)

**Tags**: [req-021, onboarding, beginner-default, experience-level, req-020]

---

### TC-021-002: Nutzer wählt im Onboarding "Fortgeschritten" — Smart-Home-Toggle erscheint

**Requirement**: REQ-021 § 3.8 (Onboarding-Integration); ExperienceLevelStep-Komponente
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer befindet sich im Onboarding-Schritt zur Erfahrungsstufe
- Aktuell ist "Anfänger" ausgewählt

**Testschritte**:
1. Nutzer klickt auf die Karte "Fortgeschritten" (`data-testid="experience-intermediate"`)

**Erwartete Ergebnisse**:
- Die Karte "Fortgeschritten" erhält blauen Rahmen und fetten Schriftschnitt
- Die Karte "Anfänger" ist nicht mehr hervorgehoben
- Unterhalb der Karten erscheint eine neue Sektion: Überschrift "Smart Home" (oder entsprechender i18n-Text) mit einem Toggle-Switch
- Der Toggle ist initial deaktiviert

**Nachbedingungen**:
- Auswahl im lokalen Wizard-State geändert (noch nicht serverseitig persistiert)

**Tags**: [req-021, onboarding, intermediate, smart-home-toggle, progressive-disclosure]

---

### TC-021-003: Nutzer wählt im Onboarding "Experte" — Smart-Home-Toggle erscheint

**Requirement**: REQ-021 § 3.3 — Experte sieht alle Menüpunkte
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Onboarding-Schritt zur Erfahrungsstufe ist aktiv

**Testschritte**:
1. Nutzer klickt auf die Karte "Experte" (`data-testid="experience-expert"`)

**Erwartete Ergebnisse**:
- Die Karte "Experte" ist hervorgehoben (blauer Rahmen)
- Smart-Home-Sektion ist sichtbar (identisch wie bei "Fortgeschritten")
- Karten "Anfänger" und "Fortgeschritten" sind nicht hervorgehoben

**Nachbedingungen**:
- Auswahl im lokalen Wizard-State geändert

**Tags**: [req-021, onboarding, expert, smart-home-toggle]

---

## 2. Erfahrungsstufen-Umschalter in den Einstellungen

### TC-021-004: Nutzer öffnet Tab "Erfahrungsstufe" in den Kontoeinstellungen

**Requirement**: REQ-021 § 3.4 — ExperienceLevelSwitcher; AccountSettingsPage Tab "Erfahrungsstufe"
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Aktuelle Erfahrungsstufe: `beginner`

**Testschritte**:
1. Nutzer navigiert zu `/einstellungen` (oder klickt auf "Einstellungen" in der Seitenleiste)
2. Nutzer klickt auf den Tab "Erfahrungsstufe"

**Erwartete Ergebnisse**:
- Die Seite zeigt die Überschrift "Kontoeinstellungen"
- Der Tab "Erfahrungsstufe" ist aktiv
- Ein ToggleButtonGroup mit drei Buttons ist sichtbar: "Anfänger", "Fortgeschritten", "Experte"
- Der Button "Anfänger" ist als aktiv markiert (farbliche Hervorhebung durch MUI ToggleButton selected state)
- Jeder Button zeigt ein Icon und eine Kurzbeschreibung (z.B. "Einfache Ansicht mit den wichtigsten Feldern")
- Weitere Karten auf der Seite: "Gießkannengröße" und "Einrichtung wiederholen"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, account-settings, experience-tab, toggle-button-group]

---

### TC-021-005: Upgrade von Anfänger auf Fortgeschritten — keine Warnung, sofortige Änderung

**Requirement**: REQ-021 § 4 — "Bei Modus-Upgrade werden sofort alle zusätzlichen Felder sichtbar"
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt, aktuelle Erfahrungsstufe: `beginner`
- Nutzer befindet sich auf dem Tab "Erfahrungsstufe" in den Kontoeinstellungen

**Testschritte**:
1. Nutzer klickt auf den ToggleButton "Fortgeschritten" (`data-testid="experience-toggle-intermediate"`)

**Erwartete Ergebnisse**:
- Es erscheint **keine** Bestätigungs-Dialog-Box (kein `window.confirm`)
- Der Button "Fortgeschritten" ist sofort als aktiv markiert
- Eine Erfolgsmeldung (Snackbar) "Gespeichert" erscheint kurz
- Die Seitenleisten-Navigation ändert sich sofort: Neue Menüpunkte "Standorte", "Düngung", "Stammdaten" und "Kalender" erscheinen in der Navigation

**Nachbedingungen**:
- Erfahrungsstufe ist auf `intermediate` gespeichert (serverseitig via PATCH /api/v1/user-preferences)

**Tags**: [req-021, upgrade, intermediate, no-warning, navigation-tiering, snackbar]

---

### TC-021-006: Upgrade von Anfänger auf Experte — keine Warnung, erweiterte Navigation

**Requirement**: REQ-021 § 4 — Upgrade ohne Warnung
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt, aktuelle Erfahrungsstufe: `beginner`
- Nutzer befindet sich auf dem Tab "Erfahrungsstufe"

**Testschritte**:
1. Nutzer klickt auf den ToggleButton "Experte" (`data-testid="experience-toggle-expert"`)

**Erwartete Ergebnisse**:
- Kein Bestätigungs-Dialog
- Button "Experte" sofort aktiv markiert
- Snackbar "Gespeichert" erscheint
- In der Seitenleiste erscheinen alle Expert-Menüabschnitte: "Pflanzenschutz", "Ernte", "Durchläufe" sowie alle Einzelpunkte wie "Substrate", "Tanks", "Gießvorgänge", "Düngeereignisse", "Nährstoff-Berechnungen", "Workflows"

**Nachbedingungen**:
- Erfahrungsstufe auf `expert` gespeichert

**Tags**: [req-021, upgrade, expert, navigation-tiering, all-menu-items]

---

### TC-021-007: Downgrade von Experte auf Anfänger — Bestätigungs-Dialog erscheint

**Requirement**: REQ-021 § 4 — "Bei Modus-Downgrade erscheint Warnung"
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt, aktuelle Erfahrungsstufe: `expert`
- Nutzer befindet sich auf dem Tab "Erfahrungsstufe" in den Kontoeinstellungen

**Testschritte**:
1. Nutzer klickt auf den ToggleButton "Anfänger" (`data-testid="experience-toggle-beginner"`)

**Erwartete Ergebnisse**:
- Ein browser-nativer Bestätigungs-Dialog (window.confirm) erscheint mit dem Text: "Beim Herunterstufen werden einige Felder und Navigationseinträge ausgeblendet. Ihre Daten bleiben erhalten. Fortfahren?"
- Die Erfahrungsstufe ändert sich noch **nicht** (Dialog wartet auf Bestätigung)

**Nachbedingungen**:
- Erfahrungsstufe unverändert (`expert`), Dialog ist geöffnet

**Tags**: [req-021, downgrade, confirm-dialog, warning, data-preservation]

---

### TC-021-008: Downgrade-Dialog — Nutzer bestätigt, Stufe ändert sich

**Requirement**: REQ-021 § 4 — Downgrade nach Bestätigung
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Downgrade-Bestätigungs-Dialog ist geöffnet (vgl. TC-021-007)

**Testschritte**:
1. Nutzer klickt im browser-nativen Dialog auf "OK" (Bestätigen)

**Erwartete Ergebnisse**:
- Dialog schließt sich
- ToggleButton "Anfänger" ist jetzt aktiv markiert
- Snackbar "Gespeichert" erscheint
- In der Seitenleiste verschwinden sofort alle Expert-/Intermediate-Menüpunkte
- Nur noch 5 Kernmenüpunkte sind sichtbar: Dashboard, Pflanzen (Pflanzeninstanzen), Aufgaben (Aufgabenwarteschlange), Einstellungen sowie ggf. Onboarding/Pflege

**Nachbedingungen**:
- Erfahrungsstufe auf `beginner` gespeichert

**Tags**: [req-021, downgrade, confirmed, beginner-navigation, data-preservation]

---

### TC-021-009: Downgrade-Dialog — Nutzer bricht ab, Stufe bleibt unverändert

**Requirement**: REQ-021 § 4 — Downgrade abgebrochen
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Downgrade-Bestätigungs-Dialog ist geöffnet

**Testschritte**:
1. Nutzer klickt im browser-nativen Dialog auf "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Der ursprüngliche ToggleButton (z.B. "Experte") bleibt aktiv markiert
- Keine Snackbar
- Navigationsseitenleiste unverändert

**Nachbedingungen**:
- Erfahrungsstufe unverändert

**Tags**: [req-021, downgrade, cancelled, no-change]

---

### TC-021-010: Downgrade von Fortgeschritten auf Anfänger — Warnung erscheint

**Requirement**: REQ-021 § 4 — Warnung bei jedem Downgrade-Schritt
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt, aktuelle Erfahrungsstufe: `intermediate`
- Tab "Erfahrungsstufe" in den Kontoeinstellungen ist aktiv

**Testschritte**:
1. Nutzer klickt auf den ToggleButton "Anfänger"

**Erwartete Ergebnisse**:
- Bestätigungs-Dialog mit Downgrade-Warnung erscheint (identischer Text wie TC-021-007)
- Nach Bestätigung wird die Stufe auf `beginner` gesetzt, Navigation reduziert

**Nachbedingungen**:
- Erfahrungsstufe nach Bestätigung: `beginner`

**Tags**: [req-021, downgrade, intermediate-to-beginner, confirm-dialog]

---

## 3. Serverseitige Persistenz und geräteübergreifende Wiederherstellung

### TC-021-011: Nach erneutem Login ist zuletzt gewählte Erfahrungsstufe aktiv

**Requirement**: REQ-021 § 4 — "Nach erneutem Login ... ist die zuletzt gewählte Erfahrungsstufe sofort aktiv"
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer hat in einer früheren Sitzung die Erfahrungsstufe auf `intermediate` gesetzt und sich abgemeldet
- Nutzer ist gerade ausgeloggt

**Testschritte**:
1. Nutzer navigiert zu `/login` und meldet sich mit E-Mail und Passwort an
2. Nutzer beobachtet die Seitenleisten-Navigation nach dem Redirect auf `/dashboard`

**Erwartete Ergebnisse**:
- Die Seitenleiste zeigt sofort Intermediate-Menüpunkte: "Standorte", "Düngung", "Stammdaten", "Kalender" sind sichtbar
- Beginner-only-Menüpunkte fehlen nicht (sie bleiben sichtbar, da Intermediate alle Beginner-Punkte enthält)
- Expert-exklusive Menüpunkte ("Pflanzenschutz", "Ernte", "Durchläufe") sind **nicht** sichtbar
- Im Tab "Erfahrungsstufe" der Kontoeinstellungen ist "Fortgeschritten" als aktiv markiert

**Nachbedingungen**:
- Keine Änderung (Persistenz bestätigt)

**Tags**: [req-021, persistence, cross-session, login-restore, intermediate]

---

### TC-021-012: Default-Erfahrungsstufe für neuen Nutzer ist "Anfänger"

**Requirement**: REQ-021 § 4 — "Default für neue Nutzer: `beginner`"
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Neuer Nutzer hat sich registriert und Onboarding-Wizard abgeschlossen, ohne explizit eine Erfahrungsstufe zu wählen (Standard beibehalten)

**Testschritte**:
1. Nutzer öffnet die Kontoeinstellungen → Tab "Erfahrungsstufe"
2. Nutzer betrachtet die Seitenleiste

**Erwartete Ergebnisse**:
- Im Tab "Erfahrungsstufe" ist "Anfänger" als aktiv markiert
- Seitenleiste zeigt nur Beginner-Menüpunkte (max. 5 Kernpunkte)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, default-beginner, new-user, persistence]

---

## 4. Navigations-Tiering

### TC-021-013: Anfänger-Navigation zeigt genau die Kernmenüpunkte

**Requirement**: REQ-021 § 3.3 — "Einsteiger (5 Menüpunkte)"
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`

**Testschritte**:
1. Nutzer öffnet die Seitenleiste (Sidebar)
2. Nutzer liest alle sichtbaren Menüeinträge

**Erwartete Ergebnisse**:
- Sichtbare Top-Level-Punkte und Abschnitte: Dashboard, Pflanzen (Abschnitt mit Eintrag "Pflanzeninstanzen"), Aufgaben (Abschnitt mit "Aufgabenwarteschlange"), Pflege (wenn Eintrag `/pflege` aktiv)
- Folgende Menüabschnitte sind **nicht** sichtbar: Stammdaten, Standorte, Düngung, Pflanzenschutz, Ernte, Durchläufe
- Folgende Einzelpunkte sind **nicht** sichtbar: "Arten", "Botanische Familien", "Substrate", "Tanks", "Düngemittel", "Nährstoffpläne", "Nährstoff-Berechnungen", "Schädlinge", "Krankheiten", "Behandlungen", "Erntechargen", "Pflanzdurchläufe", "Workflows"
- "Kalender" ist ebenfalls **nicht** sichtbar (erfordert `intermediate`)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, beginner-navigation, sidebar, nav-tiering, 5-items]

---

### TC-021-014: Fortgeschritten-Navigation enthält zusätzliche Abschnitte

**Requirement**: REQ-021 § 3.3 — "Fortgeschritten (8 Menüpunkte)"
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`

**Testschritte**:
1. Nutzer öffnet die Seitenleiste
2. Nutzer liest alle sichtbaren Menüeinträge

**Erwartete Ergebnisse**:
- Alle Beginner-Punkte sind sichtbar
- Zusätzlich sichtbar: Abschnitt "Stammdaten" mit Einträgen "Botanische Familien" und "Arten"; Abschnitt "Standorte" mit Eintrag "Standorte"; Abschnitt "Düngung" mit "Düngemittel" und "Nährstoffpläne"; "Kalender" als Top-Level-Eintrag
- Folgende Expert-Punkte sind **nicht** sichtbar: "Pflanzenschutz", "Ernte", "Durchläufe", "Substrate", "Tanks", "Nährstoff-Berechnungen", "Mischkultur", "Fruchtfolge"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, intermediate-navigation, sidebar, nav-tiering]

---

### TC-021-015: Experten-Navigation zeigt alle Menüpunkte

**Requirement**: REQ-021 § 3.3 — "Experte (alle Menüpunkte)"
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`

**Testschritte**:
1. Nutzer öffnet die Seitenleiste
2. Nutzer liest alle sichtbaren Menüeinträge

**Erwartete Ergebnisse**:
- Alle Menüabschnitte sind sichtbar: Pflanzen, Stammdaten, Standorte, Düngung, Pflanzenschutz, Ernte, Aufgaben, Durchläufe
- Unterhalb der Abschnitte sind alle Einzelpunkte sichtbar, darunter: "Substrate", "Tanks", "Gießvorgänge", "Nährstoff-Berechnungen", "Düngeereignisse", "Schädlinge", "Krankheiten", "Behandlungen", "Erntechargen", "Pflanzdurchläufe", "Workflows", "Mischkultur", "Fruchtfolge", "Import"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, expert-navigation, sidebar, nav-tiering, all-items]

---

### TC-021-016: Direktaufruf einer Expert-only-URL als Anfänger — Seite lädt trotzdem

**Requirement**: REQ-021 § 1 — "Kein Rechte-/Rollenkonzept — der Modus ist eine UI-Präferenz, keine Zugriffskontrolle"
**Priority**: Medium
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`

**Testschritte**:
1. Nutzer gibt in der Adressleiste direkt `/standorte/tanks` ein und drückt Enter

**Erwartete Ergebnisse**:
- Die Tanks-Seite lädt ohne Fehlermeldung und wird vollständig angezeigt
- Der Menüeintrag "Tanks" ist in der Seitenleiste **nicht** aktiv hervorgehoben (da er für Anfänger versteckt ist), aber die Seite ist zugänglich
- Es erscheint **keine** "403 Forbidden"- oder "404 Not Found"-Meldung

**Nachbedingungen**:
- Keine Änderung der Erfahrungsstufe

**Tags**: [req-021, url-direct-access, no-access-control, beginner]

---

## 5. Feld-Sichtbarkeit: SpeciesCreateDialog

### TC-021-017: SpeciesCreateDialog im Anfänger-Modus — alle Felder ausgeblendet

**Requirement**: REQ-021 § 3.2 — SpeciesCreateDialog, v1.1: alle Felder ab `intermediate`
**Priority**: Critical
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- Die Stammdaten-Navigation ist für Anfänger ausgeblendet — Nutzer navigiert direkt zu `/stammdaten/species`

**Testschritte**:
1. Nutzer navigiert zu `/stammdaten/species`
2. Nutzer klickt auf den "Erstellen"-Button, um den SpeciesCreateDialog zu öffnen

**Erwartete Ergebnisse**:
- Der Dialog öffnet sich
- Im Formular sind **keine** Felder sichtbar (weder `scientific_name`, `common_names`, `growth_habit`, `description` noch irgendein anderes Feld)
- Ein "Alle Felder anzeigen"-Button (`ShowAllFieldsToggle`) ist am unteren Ende des Dialogs sichtbar

**Nachbedingungen**:
- Keine Änderung der gespeicherten Daten

**Tags**: [req-021, species-dialog, beginner, no-fields-visible, showallfields]

---

### TC-021-018: SpeciesCreateDialog im Fortgeschritten-Modus — intermediate-Felder sichtbar

**Requirement**: REQ-021 § 3.2 — SpeciesCreateDialog; `fieldConfigs.ts` speciesFieldConfig
**Priority**: Critical
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`
- SpeciesCreateDialog ist geöffnet (via `/stammdaten/species` → Erstellen)

**Testschritte**:
1. Nutzer betrachtet die Felder im geöffneten Dialog

**Erwartete Ergebnisse**:
- Folgende Felder sind sichtbar: `scientific_name` (Wissenschaftlicher Name), `common_names` (Gebräuchliche Namen), `family_key` (Familie), `genus` (Gattung), `description` (Beschreibung), `growth_habit` (Wuchsform), sowie Eignungsfelder: `container_suitable`, `indoor_suitable`, `balcony_suitable`
- Folgende Felder sind **nicht** sichtbar: `root_type`, `allelopathy_score`, `hardiness_zones`, `native_habitat`, `base_temp`, `synonyms`, `taxonomic_authority`, `taxonomic_status`, `recommended_container_volume_l`, `min_container_depth_cm`, `mature_height_cm`, `mature_width_cm`, `spacing_cm`, `greenhouse_recommended`, `support_required`
- Ein "Alle Felder anzeigen"-Button ist am unteren Ende des Dialogs sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, species-dialog, intermediate, field-visibility, fieldconfigs]

---

### TC-021-019: SpeciesCreateDialog im Experten-Modus — alle Felder sichtbar

**Requirement**: REQ-021 § 3.2 — SpeciesCreateDialog; Expert zeigt alle Felder
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`
- SpeciesCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer betrachtet alle Felder im geöffneten Dialog

**Erwartete Ergebnisse**:
- Alle Felder sind sichtbar: zusätzlich zu den Intermediate-Feldern auch `root_type`, `allelopathy_score`, `hardiness_zones`, `native_habitat`, `base_temp`, `synonyms`, `taxonomic_authority`, `taxonomic_status` sowie alle Container/Spacing-Felder
- Kein "Alle Felder anzeigen"-Button ist sichtbar, da bereits alle Felder angezeigt werden (der Toggle hat keinen Effekt mehr)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, species-dialog, expert, all-fields, no-toggle-needed]

---

## 6. ShowAllFieldsToggle — Temporäres Einblenden aller Felder

### TC-021-020: "Alle Felder anzeigen" im Anfänger-Modus aktivieren

**Requirement**: REQ-021 § 1 — "Ein 'Mehr anzeigen'-Link erlaubt temporäres Einblenden aller Felder ohne Modus-Wechsel"; § 3.4 ShowAllFieldsToggle
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- PlantingRunCreateDialog oder SpeciesCreateDialog ist geöffnet (mit ausgeblendeten Feldern)

**Testschritte**:
1. Nutzer klickt auf den Button "Alle Felder anzeigen" am unteren Ende des Dialogs (ExpandMoreIcon sichtbar)

**Erwartete Ergebnisse**:
- Der Button-Text wechselt zu "Weniger Felder anzeigen" (ExpandLessIcon)
- Alle zuvor ausgeblendeten Felder sind jetzt im Formular sichtbar (inkl. Expert-Felder)
- Die Erfahrungsstufe des Nutzers bleibt unverändert bei `beginner`

**Nachbedingungen**:
- `showAllOverride` ist lokal auf `true` gesetzt (nicht persistiert)

**Tags**: [req-021, show-all-fields, toggle, beginner, temporary-override, no-persist]

---

### TC-021-021: "Weniger Felder anzeigen" — erweiterte Felder verschwinden wieder

**Requirement**: REQ-021 § 3.4 — ShowAllFieldsToggle, bidirektional
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Toggle-Zustand ist aktiv ("Alle Felder anzeigen" wurde bereits angeklickt)
- Alle Felder sind sichtbar

**Testschritte**:
1. Nutzer klickt erneut auf den Button "Weniger Felder anzeigen"

**Erwartete Ergebnisse**:
- Button-Text wechselt zurück zu "Alle Felder anzeigen" (ExpandMoreIcon)
- Alle Expert-/Intermediate-Felder verschwinden wieder aus dem Dialog
- Nur die für die Erfahrungsstufe `beginner` vorgesehenen Felder sind sichtbar

**Nachbedingungen**:
- `showAllOverride` ist lokal auf `false` gesetzt

**Tags**: [req-021, show-fewer-fields, toggle, reverse, beginner]

---

### TC-021-022: Toggle-Zustand wird nach Schließen des Dialogs zurückgesetzt

**Requirement**: REQ-021 § 4 — "'Mehr anzeigen'-Zustand ist nicht persistiert (nur für aktuelle Dialog-Instanz)"
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Nutzer hat "Alle Felder anzeigen" aktiviert und dann den Dialog geschlossen (Abbrechen)

**Testschritte**:
1. Nutzer öffnet denselben Dialog erneut (z.B. PlantingRunCreateDialog)

**Erwartete Ergebnisse**:
- Der Dialog öffnet sich im Normalzustand: nur Felder für `beginner` sind sichtbar
- Der Button zeigt "Alle Felder anzeigen" (Toggle war nicht persistiert)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, show-all-fields, not-persisted, dialog-reset, temporary-override]

---

## 7. Feld-Sichtbarkeit: PlantingRunCreateDialog

### TC-021-023: PlantingRunCreateDialog im Anfänger-Modus — nur 3 Kernfelder sichtbar

**Requirement**: REQ-021 § 3.2 — PlantingRunCreateDialog; Beginner: `name`, `entries`, `planned_start_date`
**Priority**: Critical
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- Nutzer navigiert zu `/durchlaeufe/planting-runs` und öffnet den Erstellen-Dialog

**Testschritte**:
1. Nutzer klickt auf "Erstellen"
2. Nutzer betrachtet die Felder im Dialog

**Erwartete Ergebnisse**:
- Sichtbare Felder: "Name" (`name`), Pflanzen-Einträge (`entries` / Pflanzen-Auswahl), "Geplantes Startdatum" (`planned_start_date`)
- Nicht sichtbar: `run_type` (Durchlauftyp), `site_key` (Standort), `location_key` (Ort), `notes` (Notizen), `substrate_batch_key`, `source_plant_key`
- "Alle Felder anzeigen"-Toggle ist sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, planting-run-dialog, beginner, 3-fields, fieldconfigs]

---

### TC-021-024: PlantingRunCreateDialog im Fortgeschritten-Modus — zusätzliche Felder

**Requirement**: REQ-021 § 3.2 — PlantingRunCreateDialog; Intermediate: `run_type`, `site_key`, `location_key`, `notes`
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`
- PlantingRunCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer betrachtet die Felder im Dialog

**Erwartete Ergebnisse**:
- Alle 3 Beginner-Felder sichtbar
- Zusätzlich sichtbar: `run_type` (Dropdown Durchlauftyp), `site_key` (Standort-Dropdown), `location_key` (Ort-Dropdown), `notes` (Notizen-Textarea)
- Nicht sichtbar: `substrate_batch_key`, `source_plant_key`

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, planting-run-dialog, intermediate, site-location-fields]

---

### TC-021-025: PlantingRunCreateDialog im Experten-Modus — alle Felder

**Requirement**: REQ-021 § 3.2 — PlantingRunCreateDialog; Expert: alle Felder
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`
- PlantingRunCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer betrachtet alle Felder im Dialog

**Erwartete Ergebnisse**:
- Alle Intermediate-Felder sichtbar
- Zusätzlich sichtbar: `substrate_batch_key` (Substrat-Charge), `source_plant_key` (Quellpflanze / Mutterpflanze)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, planting-run-dialog, expert, substrate-source-plant]

---

## 8. Feld-Sichtbarkeit: SiteCreateDialog

### TC-021-026: SiteCreateDialog im Anfänger-Modus — nur Name und Typ sichtbar

**Requirement**: REQ-021 § 3.2; `siteFieldConfig`: `name` + `type` sind `beginner`
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- Nutzer öffnet `/standorte/sites` (direkt per URL) → "Erstellen"-Dialog

**Testschritte**:
1. Nutzer öffnet den Erstellen-Dialog für Standorte
2. Nutzer betrachtet die sichtbaren Felder

**Erwartete Ergebnisse**:
- Sichtbar: "Name" und "Typ" (Standorttyp-Dropdown)
- Nicht sichtbar: "Klimazone" (`climate_zone`), "Gesamtfläche" (`total_area_m2`), "Wasserkonfiguration" (`water_config`), "Zeitzone" (`timezone`)
- "Alle Felder anzeigen"-Toggle ist sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, site-dialog, beginner, 2-fields, fieldconfigs]

---

### TC-021-027: SiteCreateDialog — WaterSourceSection zeigt Felder erst ab Fortgeschritten

**Requirement**: REQ-021 § 3.2; `waterSourceFieldConfig`: `ec_ms`, `ph`, `has_ro_system` ab `intermediate`
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`
- SiteCreateDialog ist geöffnet, `water_config`-Sektion ist sichtbar

**Testschritte**:
1. Nutzer klappt die Wasserquellen-Sektion auf (sofern Accordion vorhanden) oder betrachtet die direkt sichtbaren Wasserfelder

**Erwartete Ergebnisse**:
- Sichtbar: "EC (mS/cm)" (`ec_ms`), "pH" (`ph`), "RO-Anlage vorhanden" (`has_ro_system`)
- Nicht sichtbar: `alkalinity_ppm`, `gh_ppm`, `calcium_ppm`, `magnesium_ppm`, `chlorine_ppm`, `chloramine_ppm`, `measurement_date`, `source_note`

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, site-dialog, water-source, intermediate, ec-ph-visible]

---

## 9. Feld-Sichtbarkeit: GrowthPhaseDialog

### TC-021-028: GrowthPhaseDialog im Anfänger-Modus — nur Name und Dauer sichtbar

**Requirement**: REQ-021 § 3.2; `growthPhaseFieldConfig`: `name`, `duration_days` sind `beginner`
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- GrowthPhaseDialog für eine Species-Wachstumsphase ist geöffnet

**Testschritte**:
1. Nutzer betrachtet die sichtbaren Felder im GrowthPhase-Formular

**Erwartete Ergebnisse**:
- Sichtbar: "Name" (`name`), "Dauer (Tage)" (`duration_days`)
- Nicht sichtbar: `photoperiod_hours`, `temp_day_celsius`, `temp_night_celsius`, `vpd_min_kpa`, `vpd_max_kpa`, `ec_min_ms`, `ec_max_ms`, `ph_min`, `ph_max`, `humidity_min_percent`, `humidity_max_percent`, `ppfd_min`, `ppfd_max`

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, growth-phase-dialog, beginner, name-duration-only]

---

### TC-021-029: GrowthPhaseDialog im Fortgeschritten-Modus — Temperatur und Photoperiode sichtbar

**Requirement**: REQ-021 § 3.2; `growthPhaseFieldConfig`: `intermediate`-Felder
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`
- GrowthPhaseDialog ist geöffnet

**Testschritte**:
1. Nutzer betrachtet alle Felder im Dialog

**Erwartete Ergebnisse**:
- Zusätzlich zu Name und Dauer sichtbar: "Photoperiode (Stunden)" (`photoperiod_hours`), "Tagestemperatur (°C)" (`temp_day_celsius`), "Nachttemperatur (°C)" (`temp_night_celsius`)
- Expert-Felder VPD, EC, pH, Luftfeuchtigkeit, PPFD sind **nicht** sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, growth-phase-dialog, intermediate, temperature-photoperiod]

---

### TC-021-030: GrowthPhaseDialog im Experten-Modus — alle Felder inklusive VPD und EC

**Requirement**: REQ-021 § 3.2; `growthPhaseFieldConfig`: Expert zeigt alle
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`
- GrowthPhaseDialog ist geöffnet

**Testschritte**:
1. Nutzer betrachtet alle Felder im Dialog

**Erwartete Ergebnisse**:
- Alle 11 Felder sichtbar, inklusive: `vpd_min_kpa`, `vpd_max_kpa`, `ec_min_ms`, `ec_max_ms`, `ph_min`, `ph_max`, `humidity_min_percent`, `humidity_max_percent`, `ppfd_min`, `ppfd_max`

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, growth-phase-dialog, expert, vpd-ec-ph-ppfd]

---

## 10. Feld-Sichtbarkeit: FertilizerCreateDialog

### TC-021-031: FertilizerCreateDialog im Anfänger-Modus — 3 Basisfelder sichtbar

**Requirement**: REQ-021 § 3.2; `fertilizerFieldConfig`: `beginner`: `product_name`, `manufacturer`, `type`
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- FertilizerCreateDialog ist geöffnet (direkt per URL `/duengung/fertilizers`)

**Testschritte**:
1. Nutzer öffnet den Erstellen-Dialog für Düngemittel
2. Nutzer betrachtet die sichtbaren Felder

**Erwartete Ergebnisse**:
- Sichtbar: "Produktname" (`product_name`), "Hersteller" (`manufacturer`), "Typ" (`type` Dropdown)
- Nicht sichtbar: `npk_ratio`, `recommended_application`, `dosage_ml_per_liter`, `ec_contribution_per_ml`, `ph_effect`, `mixing_priority`, `tank_safe`

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, fertilizer-dialog, beginner, 3-basic-fields]

---

### TC-021-032: FertilizerCreateDialog im Experten-Modus — mixing_priority und ec_contribution sichtbar

**Requirement**: REQ-021 § 3.2; `fertilizerFieldConfig`: Expert zeigt alle inkl. `mixing_priority`
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`
- FertilizerCreateDialog ist geöffnet

**Testschritte**:
1. Nutzer betrachtet alle Felder im Dialog

**Erwartete Ergebnisse**:
- Alle 7 Felder sichtbar, inklusive: `ec_contribution_per_ml` (EC-Beitrag pro ml), `ph_effect` (pH-Effekt), `mixing_priority` (Mischpriorität), `tank_safe` (Tankverträglich)
- Diese Felder sind für Anfänger und Fortgeschrittene ausgeblendet (REQ-004 Düngelogik)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, fertilizer-dialog, expert, mixing-priority, ec-contribution, req-004]

---

## 11. NutrientCalculationsPage — Kalkulator-Sichtbarkeit

### TC-021-033: NutrientCalculationsPage im Anfänger-Modus — nur einfache Dünge-Empfehlung

**Requirement**: REQ-021 § 3.2 — NutrientCalculationsPage; Beginner: "Einfache Dünge-Empfehlung"
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- Nutzer navigiert direkt zu `/duengung/calculations`

**Testschritte**:
1. Nutzer öffnet die Seite "Nährstoff-Berechnungen"
2. Nutzer betrachtet die angezeigten Sektionen/Karten

**Erwartete Ergebnisse**:
- Sichtbar: Eine vereinfachte Karte mit natürlichsprachlicher Düngeempfehlung (z.B. Meldung wie "Deine Pflanze braucht bald wieder Dünger")
- Nicht sichtbar: "Mixing Protocol", "Flushing Protocol", "Runoff Analysis", "Mixing Safety"
- VPD-Rechner, GDD-Rechner, Photoperiod-Rechner und Slot-Capacity sind **nicht** sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, nutrient-calc, beginner, simple-recommendation, req-004]

---

### TC-021-034: NutrientCalculationsPage im Fortgeschritten-Modus — Rechner VPD/GDD/Photoperiod sichtbar

**Requirement**: REQ-021 § 3.2 — NutrientCalculationsPage; Intermediate: VPD, GDD, Photoperiod, Slot-Capacity
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`
- Nutzer navigiert zu `/duengung/calculations`

**Testschritte**:
1. Nutzer betrachtet alle Sektionen der Seite

**Erwartete Ergebnisse**:
- Sichtbar: VPD-Rechner, GDD-Rechner, Photoperiod-Rechner, Slot-Capacity-Rechner
- Nicht sichtbar: "Mixing Protocol", "Flushing Protocol", "Runoff Analysis", "Mixing Safety"
- Die einfache Düngeempfehlung für Anfänger ist **nicht** mehr sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, nutrient-calc, intermediate, vpd-gdd-photoperiod, req-004]

---

### TC-021-035: NutrientCalculationsPage im Experten-Modus — alle Kalkulatoren sichtbar

**Requirement**: REQ-021 § 3.2 — NutrientCalculationsPage; Expert: alle Kalkulatoren
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`
- Nutzer navigiert zu `/duengung/calculations`

**Testschritte**:
1. Nutzer betrachtet alle Sektionen der Seite

**Erwartete Ergebnisse**:
- Alle Kalkulatoren sind sichtbar: Mixing Protocol, Flushing Protocol, Runoff Analysis, Mixing Safety, VPD-Rechner, GDD-Rechner, Photoperiod-Rechner, Slot-Capacity-Rechner

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, nutrient-calc, expert, all-calculators, mixing-protocol, req-004]

---

## 12. Kein Datenverlust bei Moduswechsel

### TC-021-036: Expert-Daten bleiben nach Downgrade auf Anfänger vollständig erhalten

**Requirement**: REQ-021 § 4 — "Bestehende Daten in ausgeblendeten Feldern bleiben erhalten (kein Datenverlust bei Modus-Wechsel)"
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`
- Es existiert eine Species mit gefüllten Expert-Feldern: `root_type = 'taproot'`, `allelopathy_score = 0.5`, `base_temp = 8.0`

**Testschritte**:
1. Nutzer öffnet die Kontoeinstellungen → Tab "Erfahrungsstufe"
2. Nutzer klickt "Anfänger" und bestätigt die Downgrade-Warnung
3. Nutzer navigiert direkt zu `/stammdaten/species` und öffnet die Detail-Seite der betroffenen Species
4. Nutzer wechselt zurück zu Experten-Modus (Einstellungen → Erfahrungsstufe → Experte)
5. Nutzer öffnet erneut die Detail-Seite der Species

**Erwartete Ergebnisse**:
- In Schritt 3: Die Detailseite zeigt die Species; Expert-spezifische Felder sind nicht sichtbar (da Anfänger-Modus aktiv), aber es erscheint **keine** Fehlermeldung über verloren gegangene Daten
- In Schritt 5: Die Expert-Felder sind wieder sichtbar mit den ursprünglichen Werten (`root_type = 'taproot'`, `allelopathy_score = 0.5`, `base_temp = 8.0`) — kein Datenverlust

**Nachbedingungen**:
- Erfahrungsstufe: `expert`; Species-Daten unverändert

**Tags**: [req-021, data-preservation, downgrade, expert-fields, no-data-loss]

---

## 13. Quick-Add-Plant-Dialog (Beginner-Flow)

### TC-021-037: Anfänger-Nutzer sieht "Pflanze hinzufügen"-Button auf der Pflanzen-Seite

**Requirement**: REQ-021 § 3.8 — Quick-Add-Plant; "QuickAddPlantDialog ist über 'Pflanze hinzufügen'-Button erreichbar"
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- Nutzer befindet sich auf `/pflanzen/plant-instances`

**Testschritte**:
1. Nutzer betrachtet die Seite "Pflanzeninstanzen"

**Erwartete Ergebnisse**:
- Ein FAB (Floating Action Button) oder Schaltfläche mit dem Label "Pflanze hinzufügen" ist sichtbar
- Beim Klicken öffnet sich der `QuickAddPlantDialog` (Autocomplete-Suchfeld, **nicht** der normale SpeciesCreateDialog)

**Nachbedingungen**:
- Dialog ist geöffnet

**Tags**: [req-021, quick-add, beginner, fab-button, plant-instances]

---

### TC-021-038: Quick-Add-Plant — Suche nach Pflanzenname ab 2 Zeichen

**Requirement**: REQ-021 § 3.8 — "Suche ab 2 Zeichen, debounced (300ms), max. 10 Ergebnisse"
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- QuickAddPlantDialog ist geöffnet
- In der Datenbank existieren Species mit `common_names` wie "Monstera", "Monarda"

**Testschritte**:
1. Nutzer betrachtet das Autocomplete-Suchfeld mit dem Label "Wie heißt deine Pflanze?"
2. Nutzer tippt "M" (1 Zeichen) in das Suchfeld
3. Nutzer tippt "Mo" (2 Zeichen)

**Erwartete Ergebnisse**:
- Nach 1 Zeichen: Keine Dropdown-Vorschläge erscheinen
- Nach "Mo" (min. 2 Zeichen): Nach ca. 300 ms erscheint eine Dropdown-Liste mit bis zu 10 passenden Pflanzen (z.B. "Monstera (Monstera deliciosa)", "Monarda")
- Jedes Ergebnis zeigt den deutschen Common-Name und ggf. den wissenschaftlichen Namen

**Nachbedingungen**:
- Keine Änderung an gespeicherten Daten

**Tags**: [req-021, quick-add, autocomplete, 2-char-min, debounced-300ms, search]

---

### TC-021-039: Quick-Add-Plant — Auswahl einer Species und Erstellen der PlantInstance

**Requirement**: REQ-021 § 3.8 — "Bei Auswahl einer Species: PlantInstance wird mit 1 Klick erstellt"
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- QuickAddPlantDialog ist geöffnet, Suchergebnis "Monstera (Monstera deliciosa)" ist in der Dropdown-Liste sichtbar

**Testschritte**:
1. Nutzer klickt auf "Monstera (Monstera deliciosa)" in der Dropdown-Liste
2. Nutzer betrachtet den Dialog nach der Auswahl
3. Nutzer klickt auf den "Hinzufügen"-Button

**Erwartete Ergebnisse**:
- Nach der Auswahl wird "Monstera (Monstera deliciosa)" im Suchfeld angezeigt
- Optional: Spitzname-Feld ist sichtbar und ausfüllbar ("Meine große Monstera")
- Optional: Standort-Dropdown ist sichtbar
- Nach Klick auf "Hinzufügen": Dialog schließt sich
- Eine Erfolgsmeldung erscheint: "Monstera wurde hinzugefügt!" (oder entsprechende i18n-Meldung)
- Die neue PlantInstance erscheint in der Tabelle auf `/pflanzen/plant-instances`

**Nachbedingungen**:
- Neue PlantInstance existiert mit der gewählten Species; CareProfile wurde automatisch generiert (REQ-022)

**Tags**: [req-021, quick-add, plant-instance-created, success-message, req-022]

---

### TC-021-040: Quick-Add-Plant — optionaler Spitzname wird gespeichert

**Requirement**: REQ-021 § 3.8 — Quick-Add-Plant FieldConfig: `nickname` optional
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- QuickAddPlantDialog ist geöffnet, Species "Basilikum" wurde ausgewählt

**Testschritte**:
1. Nutzer gibt in das Spitzname-Feld "Mein Balkon-Basilikum" ein
2. Nutzer klickt "Hinzufügen"

**Erwartete Ergebnisse**:
- Dialog schließt sich mit Erfolgsmeldung
- In der Pflanzeninstanz-Liste ist der Spitzname "Mein Balkon-Basilikum" sichtbar (oder in der Detailansicht)

**Nachbedingungen**:
- PlantInstance mit Spitzname gespeichert

**Tags**: [req-021, quick-add, nickname, optional-field]

---

### TC-021-041: Quick-Add-Plant — kein Treffer, "Trotzdem hinzufügen" (Freitext-Fallback)

**Requirement**: REQ-021 § 3.8 — "Freitext-Fallback: Wenn keine Species gefunden, kann Nutzer mit Freitext-Common-Name anlegen"
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- QuickAddPlantDialog ist geöffnet
- In der Datenbank gibt es keine Species mit dem Namen "Komische Rankepflanze"

**Testschritte**:
1. Nutzer tippt "Komische Rankepflanze" in das Autocomplete-Suchfeld
2. Nutzer wartet auf die Suchergebnisse

**Erwartete Ergebnisse**:
- Die Dropdown-Liste zeigt die Meldung "Keine passende Pflanze gefunden"
- Ein Button/Link "Trotzdem hinzufügen" ist sichtbar
- Ein zweiter Link/Hinweis "Ich kenne den Namen nicht" ist sichtbar

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, quick-add, no-results, freetext-fallback, help-link]

---

### TC-021-042: Quick-Add-Plant — "Trotzdem hinzufügen" erstellt PlantInstance mit Freitext-Common-Name

**Requirement**: REQ-021 § 3.8 — "Species wird mit common_names=['Komische Rankepflanze'] erstellt, scientific_name leer"
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- QuickAddPlantDialog zeigt "Keine passende Pflanze gefunden" mit Button "Trotzdem hinzufügen"
- Freitext "Komische Rankepflanze" ist im Suchfeld

**Testschritte**:
1. Nutzer klickt auf "Trotzdem hinzufügen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgsmeldung erscheint: "Komische Rankepflanze wurde hinzugefügt!"
- Ein Hinweis ist sichtbar (oder erscheint im Dialog): "Du kannst den botanischen Namen später ergänzen."
- Die neue PlantInstance erscheint in der Liste

**Nachbedingungen**:
- Neue PlantInstance mit Freitext-Common-Name angelegt; `scientific_name` ist leer

**Tags**: [req-021, quick-add, freetext, scientific-name-optional, later-hint]

---

### TC-021-043: Quick-Add-Plant — "Ich kenne den Namen nicht" zeigt Hilfe-Hinweis

**Requirement**: REQ-021 § 3.8 — "Option B: 'Hilfe — ich kenne den Namen nicht' → Link/Hinweis"
**Priority**: Low
**Category**: Dialog
**Vorbedingungen**:
- QuickAddPlantDialog zeigt "Keine passende Pflanze gefunden"

**Testschritte**:
1. Nutzer klickt auf "Ich kenne den Namen nicht"

**Erwartete Ergebnisse**:
- Ein Hinweis-Text erscheint: "Nutze eine Pflanzenerkennungs-App (z.B. PlantNet) oder beschreibe die Pflanze — du kannst den Namen später ergänzen."
- Ggf. ein externer Link zu einem Pflanzenerkennungs-Tool ist sichtbar

**Nachbedingungen**:
- Keine Änderung an gespeicherten Daten

**Tags**: [req-021, quick-add, help-unknown, plantnet-hint, future-ai-feature]

---

### TC-021-044: Fortgeschritten-Nutzer erhält QuickAddPlantDialog mit optionalen Zusatzfeldern

**Requirement**: REQ-021 § 3.8 — "Intermediate/Expert sehen QuickAddPlantDialog mit optionalen Zusatzfeldern"
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `intermediate`
- Nutzer befindet sich auf `/pflanzen/plant-instances`

**Testschritte**:
1. Nutzer klickt auf "Pflanze hinzufügen"
2. Nutzer betrachtet den geöffneten Dialog

**Erwartete Ergebnisse**:
- Der QuickAddPlantDialog öffnet sich (kein voller SpeciesCreateDialog)
- Zusätzlich zu den Beginner-Feldern sind weitere optionale Felder sichtbar (z.B. Standort-Dropdown mit Unter-Standort-Option)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, quick-add, intermediate, optional-fields]

---

### TC-021-045: Experten-Nutzer hat Zugriff auf den vollen Workflow (Species → PlantInstance → Phase)

**Requirement**: REQ-021 § 3.8 — "Expert: Bestehender Workflow (Species → PlantInstance → Phase)"
**Priority**: Medium
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `expert`

**Testschritte**:
1. Nutzer navigiert zu `/pflanzen/plant-instances`
2. Nutzer klickt auf "Pflanze hinzufügen"

**Erwartete Ergebnisse**:
- Es öffnet sich entweder der QuickAddPlantDialog (mit Expert-Feldern) oder der Nutzer wird auf den normalen Erstellungs-Workflow weitergeleitet
- Der volle Workflow (über Species-Auswahl → PlantInstance-Erstellung → Phasenzuweisung) ist zugänglich

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, quick-add, expert, full-workflow]

---

## 14. i18n und Sprachunterstützung

### TC-021-046: Erfahrungsstufen-Labels sind auf Deutsch korrekt übersetzt

**Requirement**: REQ-021 § 4 — "Alle drei Modi sind in DE und EN verfügbar"
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- UI-Sprache ist Deutsch (Standard)
- Nutzer befindet sich auf dem Tab "Erfahrungsstufe" in den Kontoeinstellungen

**Testschritte**:
1. Nutzer liest die Labels der drei ToggleButtons

**Erwartete Ergebnisse**:
- Labels: "Anfänger", "Fortgeschritten", "Experte" (aus `enums.experienceLevel.*`)
- Beschreibungstexte: "Einfache Ansicht mit den wichtigsten Feldern", "Erweiterte Optionen für erfahrene Nutzer", "Alle Felder und Funktionen sichtbar"

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, i18n, german, labels, translation]

---

### TC-021-047: Erfahrungsstufen-Labels werden auf Englisch korrekt angezeigt

**Requirement**: REQ-021 § 4 — DE und EN verfügbar
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer hat die UI-Sprache auf Englisch umgeschaltet (Kontoeinstellungen → Profil → Sprache: "English")
- Tab "Erfahrungsstufe" (englisch: "Experience Level") ist aktiv

**Testschritte**:
1. Nutzer liest die Labels der drei ToggleButtons

**Erwartete Ergebnisse**:
- Labels zeigen englische Texte: "Beginner", "Intermediate", "Expert"
- Beschreibungstexte sind auf Englisch

**Nachbedingungen**:
- Keine Änderung der Erfahrungsstufe

**Tags**: [req-021, i18n, english, labels, locale-switch]

---

### TC-021-048: ShowAllFieldsToggle-Button zeigt korrekten deutschen Text

**Requirement**: REQ-021 § 3.7 — `common.showAllFields` / `common.showFewerFields`
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- UI-Sprache ist Deutsch
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- Ein Dialog mit ausgeblendeten Feldern ist geöffnet (z.B. SiteCreateDialog)

**Testschritte**:
1. Nutzer betrachtet den Toggle-Button am Ende des Formulars
2. Nutzer klickt auf den Button

**Erwartete Ergebnisse**:
- Initialer Button-Text: "Alle Felder anzeigen" (mit ExpandMoreIcon)
- Nach dem Klick: Button-Text wechselt zu "Weniger Felder anzeigen" (mit ExpandLessIcon)

**Nachbedingungen**:
- `showAllOverride`: `true`

**Tags**: [req-021, i18n, showallfields-button, de-text, expandicon]

---

## 15. Fehlerzustände und Edge Cases

### TC-021-049: Netzwerkfehler beim Speichern der Erfahrungsstufe — Fehlermeldung sichtbar

**Requirement**: REQ-021 § 3.6 — Redux UIModeSlice: `status: 'error'`
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Netzwerkverbindung ist nicht verfügbar oder API gibt Fehler zurück (Simulationstest)

**Testschritte**:
1. Nutzer wechselt im Tab "Erfahrungsstufe" auf "Fortgeschritten"

**Erwartete Ergebnisse**:
- Anstelle der Erfolgs-Snackbar "Gespeichert" erscheint eine Fehler-Snackbar (z.B. "Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung." oder "Serverfehler. Bitte versuchen Sie es später erneut.")
- Die UI behält den vorherigen Zustand bei (kein falscher Toggle-Zustand)

**Nachbedingungen**:
- Erfahrungsstufe unverändert

**Tags**: [req-021, error-state, network-error, snackbar-error, redux-error-status]

---

### TC-021-050: Quick-Add-Plant — Suchfeld ohne Eingabe, kein API-Aufruf

**Requirement**: REQ-021 § 3.8 — "Suche ab 2 Zeichen"
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- QuickAddPlantDialog ist geöffnet

**Testschritte**:
1. Nutzer lässt das Suchfeld leer und klickt auf "Hinzufügen"

**Erwartete Ergebnisse**:
- "Hinzufügen"-Button ist deaktiviert oder eine Inline-Fehlermeldung erscheint (Pflichtfeld-Validierung)
- Kein Dialog schließt sich, keine PlantInstance wird erstellt

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, quick-add, empty-search, form-validation, required-field]

---

### TC-021-051: Gleichzeitiger Moduswechsel auf zwei Geräten — neuester Wert gewinnt

**Requirement**: REQ-021 § 2 — "serverseitig persistiert", geräteübergreifend konsistent
**Priority**: Low
**Category**: Edge Case
**Vorbedingungen**:
- Nutzer ist auf zwei Geräten gleichzeitig eingeloggt
- Gerät A: Erfahrungsstufe `beginner`; Gerät B: gleichzeitig `expert`

**Testschritte**:
1. Auf Gerät B: Nutzer wechselt zu `expert` und sieht Snackbar "Gespeichert"
2. Auf Gerät A: Nutzer lädt die Seite neu (F5)

**Erwartete Ergebnisse**:
- Nach dem Neuladen auf Gerät A wird die Erfahrungsstufe `expert` angezeigt (Server-State wird geladen)
- Die Seitenleiste auf Gerät A zeigt sofort alle Expert-Menüpunkte

**Nachbedingungen**:
- Erfahrungsstufe auf beiden Geräten: `expert`

**Tags**: [req-021, multi-device, server-state, reload, consistency]

---

### TC-021-052: Kein-DOM-Rendering für ausgeblendete Felder (Performance-Test)

**Requirement**: REQ-021 § 4 — "Kein Performance-Impact: Unsichtbare Felder werden nicht gerendert (kein `display: none`)"
**Priority**: Medium
**Category**: Edge Case
**Vorbedingungen**:
- Nutzer ist eingeloggt, Erfahrungsstufe: `beginner`
- SpeciesCreateDialog ist geöffnet (alle Expert-Felder ausgeblendet)

**Testschritte**:
1. Nutzer öffnet die Browser-Entwicklertools (F12 → Inspektor / Elements)
2. Nutzer sucht im DOM nach einem Expert-spezifischen Feld (z.B. Input für `allelopathy_score`)

**Erwartete Ergebnisse**:
- Das Feld `allelopathy_score` ist **nicht** im DOM vorhanden (kein Hidden-Element, kein `display: none`, kein `visibility: hidden`)
- `ExpertiseFieldWrapper` gibt `null` zurück (kein Rendering)

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-021, no-dom-rendering, performance, expert-fields-null, devtools]

---

## Abdeckungsmatrix

| Spezifikationsabschnitt | Anforderung | Testfall(e) |
|-------------------------|-------------|-------------|
| § 1 Business Case — User Story Einsteiger | Default `beginner`, vereinfachte Ansicht | TC-021-012, TC-021-013 |
| § 1 Business Case — User Story Experte | Alle Felder zugänglich, kein Verlust | TC-021-019, TC-021-030, TC-021-035 |
| § 1 Business Case — User Story Umschalter | Jederzeit wechselbar | TC-021-005, TC-021-006, TC-021-007 |
| § 1 Business Case — User Story Mehr anzeigen | Temporäre Einblendung | TC-021-020, TC-021-021, TC-021-022 |
| § 2 Datenmodell — serverseitige Persistenz | Geräteübergreifend | TC-021-011, TC-021-051 |
| § 2 Datenmodell — Default `beginner` | Neue Nutzer | TC-021-012 |
| § 3.1 Feld-Konfigurationssystem | FieldMeta, ExpertiseLevel | TC-021-018, TC-021-023, TC-021-026 |
| § 3.2 SpeciesCreateDialog | Feld-Sichtbarkeit Beginner/Intermediate/Expert | TC-021-017, TC-021-018, TC-021-019 |
| § 3.2 PlantingRunCreateDialog | Feld-Sichtbarkeit | TC-021-023, TC-021-024, TC-021-025 |
| § 3.2 SiteCreateDialog / WaterSourceSection | Feld-Sichtbarkeit | TC-021-026, TC-021-027 |
| § 3.2 GrowthPhaseDialog | Feld-Sichtbarkeit VPD/EC/pH | TC-021-028, TC-021-029, TC-021-030 |
| § 3.2 FertilizerCreateDialog | mixing_priority, ec_contribution | TC-021-031, TC-021-032 |
| § 3.2 NutrientCalculationsPage | Kalkulator-Sichtbarkeit | TC-021-033, TC-021-034, TC-021-035 |
| § 3.3 Navigations-Tiering Anfänger | 5 Kernmenüpunkte | TC-021-013 |
| § 3.3 Navigations-Tiering Fortgeschritten | 8 Menüpunkte | TC-021-014 |
| § 3.3 Navigations-Tiering Experte | alle Menüpunkte | TC-021-015 |
| § 3.4 useExpertiseLevel Hook | isFieldVisible, isNavVisible | TC-021-016, TC-021-052 |
| § 3.4 ExpertiseFieldWrapper | null-Rendering | TC-021-052 |
| § 3.4 ShowAllFieldsToggle | Temporäre Einblendung | TC-021-020, TC-021-021, TC-021-022, TC-021-048 |
| § 3.4 ExperienceLevelSwitcher | ToggleButtonGroup, Downgrade-Warnung | TC-021-004, TC-021-005–TC-021-010 |
| § 3.6 Redux-State | status: 'error' | TC-021-049 |
| § 3.7 i18n-Schlüssel | DE/EN Labels | TC-021-046, TC-021-047, TC-021-048 |
| § 3.8 Quick-Add-Plant | Autocomplete-Suche ab 2 Zeichen | TC-021-037, TC-021-038 |
| § 3.8 Quick-Add-Plant — Happy Path | PlantInstance erstellen | TC-021-039, TC-021-040 |
| § 3.8 Quick-Add-Plant — Freitext-Fallback | Kein Treffer, Freitext | TC-021-041, TC-021-042 |
| § 3.8 Quick-Add-Plant — Hilfe-Link | "Ich kenne den Namen nicht" | TC-021-043 |
| § 3.8 Quick-Add-Plant — Intermediate/Expert | Dialog mit Zusatzfeldern | TC-021-044, TC-021-045 |
| § 4 Akzeptanzkriterien — Upgrade ohne Warnung | Sofortige Wirkung | TC-021-005, TC-021-006 |
| § 4 Akzeptanzkriterien — Downgrade mit Warnung | window.confirm | TC-021-007, TC-021-008, TC-021-009, TC-021-010 |
| § 4 Akzeptanzkriterien — kein Datenverlust | Expert-Daten bleiben erhalten | TC-021-036 |
| § 4 Akzeptanzkriterien — nicht persistierter Toggle | Dialog-Reset | TC-021-022 |
| § 6 Auth | Präferenz-Endpunkte benötigen Auth | TC-021-011 |
| Onboarding ExperienceLevelStep | Erstauswahl | TC-021-001, TC-021-002, TC-021-003 |
| Kein Rechte-/Rollenkonzept | URL-Direktzugriff | TC-021-016 |
| Fehlerzustände | Netzwerkfehler, leere Suche | TC-021-049, TC-021-050 |
| Edge Cases | Multi-Device, DOM-Performance | TC-021-051, TC-021-052 |
