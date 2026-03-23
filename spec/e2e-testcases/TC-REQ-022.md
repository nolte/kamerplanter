---
req_id: REQ-022
title: Einfache Pflegeerinnerungen fuer Zimmerpflanzen & Ueberwinterungsmanagement
category: Pflege & Erinnerungen
test_count: 68
coverage_areas:
  - PflegeDashboardPage (/pflege) — Kartenansicht aller faelliger Erinnerungen
  - ReminderCard — Einzelne Erinnerungskarte mit Dringlichkeits-Badge
  - Ein-Tap-Bestaetigung (Confirm-Button auf ReminderCard)
  - Snooze-Funktion (Verschieben um +2 Tage)
  - CareProfileEditDialog — Intervall-Anpassung per Slider
  - Care-Style-Wechsel mit Bestaetigung
  - Standort-Check-Konfiguration (Winter/Fruehling Monate)
  - Luftfeuchte-Check Toggle
  - Adaptive-Learning Toggle und Anzeige gelernter Intervalle
  - Reset-auf-Standardwerte Funktion
  - Giessmethode-Anleitungstext auf ReminderCard
  - Wasserqualitaets-Hinweis (Orchidee, Calathea, Farn)
  - Symptom-Check-Hinweis bei Umtopf-Erinnerungen
  - Leerer Zustand (Alle Pflanzen versorgt)
  - Dungegruard (Saisonalitaet + Dormanz-Phasen)
  - Giessplan-Guard (Unterdrueckung bei aktivem WateringSchedule)
  - Saisonale Erinnerungen (Standort-Check Oktober/Maerz)
  - Luftfeuchte-Erinnerungen (Heizperiode Okt-Maerz)
  - Bestaetigungshistorie pro Pflanze
  - Navigations-Tiering (Einsteiger Position 3)
  - Ueberwinterungs-Erinnerungen (winter_protection, spring_uncover, tuber_dig)
  - Winterhaerte-Ampel-Widget im Dashboard
  - Fehlerbehandlung und Validierungsmeldungen
generated: 2026-03-21
version: "2.4"
---

# TC-REQ-022: Einfache Pflegeerinnerungen fuer Zimmerpflanzen & Ueberwinterungsmanagement

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-022 Pflegeerinnerungen v2.4**,
ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes
oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der
Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren
die deutschen i18n-Texte aus `pages.care.*` und `enums.careStyle.*`.

REQ-022 stellt eine vereinfachte Pflege-Schicht ueber dem REQ-006-Task-System bereit. Die
primaere Benutzeroberflaeche ist die **PflegeDashboardPage** unter `/pflege`. Erinnerungen
erscheinen als **ReminderCards** sortiert nach Dringlichkeit. Jede Karte bietet einen
prominenten Ein-Tap-Bestaetigen-Button und einen dezenten Snooze-Link.

---

## 1. PflegeDashboardPage — Seitenaufruf und Grundzustand

### TC-022-001: PflegeDashboardPage zeigt alle faelligen Erinnerungen sortiert nach Dringlichkeit

**Requirement**: REQ-022 § 5.1 — PflegeDashboardPage Layout
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Mitglied
- Mindestens 3 PlantInstances mit CareProfile existieren
- Pflanze A hat eine Gieß-Erinnerung 3 Tage ueberfaellig
- Pflanze B hat eine Gieß-Erinnerung heute faellig
- Pflanze C hat eine Schädlingskontrolle in 1 Tag faellig

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage via Seitenleiste "Pflege" oder URL `/pflege`
2. Nutzer betrachtet die angezeigte Liste der ReminderCards

**Erwartete Ergebnisse**:
- Seitenheader zeigt "Pflege-Erinnerungen" mit dem aktuellen Datum
- Pflanze A (3 Tage ueberfaellig) erscheint zuerst mit rotem Badge "3 Tage ueberfaellig"
- Pflanze B (heute faellig) erscheint danach mit gelbem/orangenem Badge "Heute fällig"
- Pflanze C (morgen faellig) erscheint am Ende mit grauem Badge "In 1 Tag"
- Jede ReminderCard zeigt: Pflanzenname, Artname, Erinnerungstyp-Icon, Dringlichkeits-Badge, Bestaetigen-Button und Snooze-Link

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, dashboard, sortierung, dringlichkeit, reminder-card]

---

### TC-022-002: PflegeDashboardPage im leeren Zustand zeigt Erfolgsmeldung

**Requirement**: REQ-022 § 5.1 — Leerer Zustand
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Alle PlantInstances haben keine faelligen oder demnächst faelligen Erinnerungen (alle wurden heute bestaetigt oder es existieren keine Pflanzen mit CareProfile)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`

**Erwartete Ergebnisse**:
- Keine ReminderCards werden angezeigt
- Eine Erfolgs-Illustration ist sichtbar
- Der Text "Alle Pflanzen sind versorgt!" erscheint unterhalb der Illustration
- Keine Fehlermeldungen oder leeren Tabellen erscheinen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, dashboard, leer-zustand, alle-versorgt]

---

### TC-022-003: PflegeDashboardPage — Navigation fuer Einsteiger an Position 3

**Requirement**: REQ-022 § 5.6 — Navigations-Integration (REQ-021)
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Erfahrungsstufe ist auf "Einsteiger" gesetzt

**Testschritte**:
1. Nutzer betrachtet die Seitenleisten-Navigation
2. Nutzer zaehlt die Navigationspunkte

**Erwartete Ergebnisse**:
- In der Seitenleiste erscheint "Pflege" als Navigationspunkt
- "Pflege" steht an Position 3 (nach Dashboard und Meine Pflanzen)
- Klick auf "Pflege" navigiert zur PflegeDashboardPage `/pflege`

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, navigation, einsteiger, tiering, req-021]

---

### TC-022-004: PflegeDashboardPage — Navigation fuer Experten zeigt zusaetzlichen Punkt

**Requirement**: REQ-022 § 5.6 — Navigations-Integration (REQ-021), Experten-Modus
**Priority**: Medium
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Erfahrungsstufe ist auf "Experte" gesetzt

**Testschritte**:
1. Nutzer betrachtet die Seitenleisten-Navigation

**Erwartete Ergebnisse**:
- Der Navigationspunkt heißt "Pflege & Erinnerungen" (erweiterter Label fuer Experten)
- Der Punkt ist an Position 6 sichtbar
- Zusaetzlich ist auch "Aufgaben & Workflows" (REQ-006) als separater Navigationspunkt vorhanden

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, navigation, experte, tiering, req-021]

---

## 2. ReminderCard — Darstellung und Inhalt

### TC-022-005: Gieß-Erinnerungskarte zeigt Giessmethode als Anleitungstext

**Requirement**: REQ-022 § 5.1 — ReminderCard, Giessmethode
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Eine Orchidee mit care_style="orchid" hat eine faellige Gieß-Erinnerung
- Das CareProfile der Orchidee hat watering_method="soak"

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die ReminderCard der Orchidee (Erinnerungstyp: Gießen)

**Erwartete Ergebnisse**:
- Der Anleitungstext lautet: "Tauchbad: Topf 10–15 Min. in zimmerwarmes Wasser stellen, abtropfen lassen."
- Der Erinnerungstyp-Icon zeigt einen Wassertropfen
- Der Bestaetigen-Button zeigt "Gegossen"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, giessmethode, soak, orchid, anleitung]

---

### TC-022-006: Gieß-Erinnerungskarte zeigt Wasserqualitaets-Hinweis fuer Calathea

**Requirement**: REQ-022 § 5.1 — ReminderCard, Wasserqualitaets-Hinweis
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Eine Calathea mit care_style="calathea" hat eine faellige Gieß-Erinnerung
- Das CareProfile hat water_quality_hint gesetzt (pages.care.waterQuality.calathea)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die ReminderCard der Calathea (Erinnerungstyp: Gießen)

**Erwartete Ergebnisse**:
- Ein Tooltip oder Hinweis-Element ist sichtbar (z.B. Info-Icon oder aufgeklappter Hinweistext)
- Der Hinweistext lautet: "Kalkempfindlich! Regenwasser, gefiltertes oder abgestandenes Wasser verwenden."
- Der Hinweis ist visuell vom Anleitungstext abgegrenzt (z.B. anderer Icon oder Farbe)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, wasserqualitaet, calathea, kalkempfindlich]

---

### TC-022-007: Gieß-Erinnerungskarte fuer tropical zeigt keinen Wasserqualitaets-Hinweis

**Requirement**: REQ-022 § 5.1 — ReminderCard, Wasserqualitaets-Hinweis = null
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Eine Monstera mit care_style="tropical" hat eine faellige Gieß-Erinnerung
- Das CareProfile hat water_quality_hint=null

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die ReminderCard der Monstera (Erinnerungstyp: Gießen)

**Erwartete Ergebnisse**:
- Kein Wasserqualitaets-Hinweis-Element ist auf der Karte sichtbar
- Kein Info-Icon fuer Wasserqualitaet erscheint
- Nur der Anleitungstext "Von oben gießen, bis Wasser unten herausläuft." ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, wasserqualitaet, tropical, kein-hinweis]

---

### TC-022-008: Umtopf-Erinnerungskarte zeigt Symptom-Check-Hinweis

**Requirement**: REQ-022 § 5.1 — ReminderCard, Symptom-Check fuer repotting
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Eine PlantInstance hat eine faellige Umtopf-Erinnerung (reminder_type="repotting")

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die ReminderCard mit Erinnerungstyp "Umtopfen"

**Erwartete Ergebnisse**:
- Der Erinnerungstyp-Icon zeigt einen Blumentopf
- Der Bestaetigen-Button zeigt "Umgetopft"
- Ein Symptom-Check-Hinweis ist auf der Karte sichtbar mit dem Text:
  "Prüfen: (1) Wachsen Wurzeln aus dem Ablaufloch? (2) Trocknet das Substrat ungewöhnlich schnell? (3) Wächst die Pflanze merklich langsamer?"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, umtopfen, repotting, symptom-check]

---

### TC-022-009: ReminderCard zeigt korrekten Dringlichkeits-Badge in drei Farben

**Requirement**: REQ-022 § 5.1 — Farbcodierung (overdue/due_today/upcoming)
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze X: Gieß-Erinnerung 5 Tage ueberfaellig (days_overdue=5)
- Pflanze Y: Duenge-Erinnerung heute faellig (days_overdue=0)
- Pflanze Z: Schädlingskontrolle in 2 Tagen (days_overdue=-2)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die Dringlichkeits-Badges der drei Karten

**Erwartete Ergebnisse**:
- Pflanze X: Badge in Rot (error.main) mit Text "5 Tage überfällig"
- Pflanze Y: Badge in Gelb/Orange (warning.main) mit Text "Heute fällig"
- Pflanze Z: Badge in Grau (text.secondary) mit Text "In 2 Tagen"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, dringlichkeit, farbcodierung, overdue, due-today, upcoming]

---

### TC-022-010: ReminderCard zeigt "Letzte Aktion"-Information

**Requirement**: REQ-022 § 5.1 — ReminderCard, letzte Aktion
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A wurde vor 8 Tagen zuletzt gegossen (CareConfirmation mit reminder_type="watering" existiert)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die Gieß-ReminderCard von Pflanze A

**Erwartete Ergebnisse**:
- Auf der Karte erscheint der Text im Format: "Zuletzt Gegossen: vor 8 Tagen"
- Das Format entspricht dem i18n-Key "pages.care.lastAction" mit den Interpolationen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, letzte-aktion, i18n, care-confirmation]

---

### TC-022-011: ReminderCard fuer erstmalig neu erstellte Pflanze ohne Bestaetigungshistorie

**Requirement**: REQ-022 § 3 — CareReminderEngine, Nie bestaetigte Erinnerung (days_since=999)
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Eine neue PlantInstance wurde gerade erstellt, noch nie eine Pflegeaktion bestaetigt

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht die ReminderCard fuer die neue Pflanze

**Erwartete Ergebnisse**:
- Die ReminderCard erscheint mit rotem Dringlichkeits-Badge (sofort faellig)
- Kein "Zuletzt"-Text erscheint (oder "Noch nie" als Alternativtext)
- Der Bestaetigen-Button ist aktiv und klickbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, reminder-card, erstmalig, nie-bestaetigt, neue-pflanze]

---

## 3. Ein-Tap-Bestaetigung

### TC-022-012: Gieß-Erinnerung bestaetigen entfernt Karte sofort aus Dashboard (Optimistic Update)

**Requirement**: REQ-022 § 5.4 — Optimistic Updates, confirmReminder
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat eine faellige Gieß-Erinnerung auf der PflegeDashboardPage

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sieht die ReminderCard von Pflanze A mit Erinnerungstyp "Gießen"
3. Nutzer klickt auf den prominenten Button "Gegossen" auf der Karte

**Erwartete Ergebnisse**:
- Die ReminderCard von Pflanze A verschwindet sofort aus dem Dashboard (vor API-Response — Optimistic Update)
- Es erscheint kein Ladeindikator auf der Karte
- Falls dies die letzte Erinnerung war: der Leer-Zustand "Alle Pflanzen sind versorgt!" erscheint
- Keine Fehler-Snackbar erscheint

**Nachbedingungen**:
- Die Gieß-Erinnerung fuer Pflanze A gilt als erledigt
- Die naechste Gieß-Erinnerung wird erst nach Ablauf des Gießintervalls wieder erscheinen

**Tags**: [req-022, bestaetigung, ein-tap, optimistic-update, confirm, dashboard]

---

### TC-022-013: Duenge-Erinnerung bestaetigen mit Bestaetigen-Button

**Requirement**: REQ-022 § 5.1 — ReminderCard, Bestaetigen-Aktion fuer fertilizing
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat eine faellige Duenge-Erinnerung (reminder_type="fertilizing")

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sieht die ReminderCard fuer Duengen von Pflanze A
3. Nutzer klickt auf den Button "Gedüngt"

**Erwartete Ergebnisse**:
- Die Karte verschwindet sofort aus dem Dashboard
- Kein Fehlerzustand erscheint

**Nachbedingungen**:
- Die Duenge-Erinnerung fuer Pflanze A ist erledigt

**Tags**: [req-022, bestaetigung, duengen, fertilizing, optimistic-update]

---

### TC-022-014: Schädlingskontrolle bestaetigen mit "Kontrolliert"-Button

**Requirement**: REQ-022 § 5.1 — ReminderCard, Bestaetigen-Aktion fuer pest_check
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat eine faellige Schädlingskontrolle (reminder_type="pest_check")

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sieht die ReminderCard fuer "Schädlingskontrolle" mit Lupe-Icon
3. Nutzer klickt auf den Button "Kontrolliert"

**Erwartete Ergebnisse**:
- Die Karte verschwindet sofort aus dem Dashboard
- Kein Fehlerzustand erscheint

**Nachbedingungen**:
- Die Schädlingskontrolle fuer Pflanze A ist erledigt

**Tags**: [req-022, bestaetigung, schaedlingskontrolle, pest-check, kontrolliert]

---

### TC-022-015: Bestaetigung schlaegt fehl — Karte erscheint wieder mit Fehler-Snackbar

**Requirement**: REQ-022 § 5.4 — Optimistic Update Rollback bei API-Fehler
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat eine faellige Gieß-Erinnerung
- Der Backend-Dienst ist voruebe rgehend nicht erreichbar (Netzwerkfehler)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer klickt auf "Gegossen" fuer Pflanze A
3. Die ReminderCard verschwindet zuerst (Optimistic Update)
4. Das Backend antwortet mit einem Fehler

**Erwartete Ergebnisse**:
- Die ReminderCard von Pflanze A wird wieder in die Liste eingefuegt (Rollback)
- Eine Fehler-Snackbar erscheint mit einem Hinweis (z.B. "Netzwerkfehler...")
- Die Karte zeigt denselben Zustand wie vor dem Klick

**Nachbedingungen**:
- Der Zustand der Erinnerung ist unveraendert

**Tags**: [req-022, bestaetigung, fehler, rollback, snackbar, netzwerkfehler]

---

## 4. Snooze-Funktion

### TC-022-016: Snooze verschiebt Erinnerungskarte auf "Demnachst" (Grau)

**Requirement**: REQ-022 § 5.4 — Optimistic Updates, snoozeReminder
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat eine heute faellige Gieß-Erinnerung (days_overdue=0, Badge gelb)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sieht die ReminderCard von Pflanze A mit gelbem Badge "Heute fällig"
3. Nutzer klickt auf den dezenten Snooze-Link "Später (+2 Tage)" auf der Karte

**Erwartete Ergebnisse**:
- Die ReminderCard von Pflanze A wechselt sofort zu grauem Badge (Optimistic Update)
- Das Badge zeigt "In 2 Tagen"
- Die Karte rutscht in den "Demnachst"-Bereich der Liste (unterhalb aller ueberfaelligen und heute faelligen Karten)
- Keine Fehler-Snackbar erscheint

**Nachbedingungen**:
- Die Gieß-Erinnerung fuer Pflanze A ist um 2 Tage verschoben

**Tags**: [req-022, snooze, verschieben, upcoming, optimistic-update, grau]

---

### TC-022-017: Snooze-Link zeigt konfigurierte Anzahl Tage im Label

**Requirement**: REQ-022 § 5.1 — ReminderCard, Snooze-Link mit days-Parameter
**Priority**: Medium
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Eine faellige Erinnerung ist auf dem Dashboard sichtbar
- Der Standard-Snooze-Wert ist 2 Tage (CareSnoozeRequest Default)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet den Snooze-Link auf einer ReminderCard

**Erwartete Ergebnisse**:
- Der Snooze-Link zeigt den Text "Später (+2 Tage)" (i18n-Key: pages.care.actions.snooze mit days=2)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, snooze, link-text, i18n, default-2-tage]

---

## 5. CareProfileEditDialog — Pflegeprofil bearbeiten

### TC-022-018: CareProfileEditDialog oeffnet sich von der ReminderCard aus

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Erreichbarkeit
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat eine faellige Erinnerung auf dem Dashboard

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht einen "Bearbeiten"- oder "Einstellungen"-Link auf der ReminderCard von Pflanze A
3. Nutzer klickt auf diesen Link

**Erwartete Ergebnisse**:
- Der CareProfileEditDialog "Pflegeprofil bearbeiten" oeffnet sich als Modal-Dialog
- Der Dialog zeigt den aktuellen care_style im Dropdown-Feld "Pflegestil" vorbelegt
- Alle Slider-Felder (Gießintervall, Duengeintervall, etc.) zeigen die aktuellen Werte

**Nachbedingungen**:
- Kein Profilwert geaendert

**Tags**: [req-022, care-profile-dialog, oeffnen, reminder-card, navigation]

---

### TC-022-019: Gießintervall-Slider aendern und speichern

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Gießintervall
**Priority**: Critical
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet fuer Pflanze A
- Aktuelles Gießintervall ist 7 Tage (tropical Preset)

**Testschritte**:
1. Nutzer sieht den Slider "Gießintervall (Tage)" bei Wert 7
2. Nutzer verschiebt den Slider auf Wert 10
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Slider zeigt nach dem Verschieben den Wert "10 Tage" als Label
- Nach dem Klick auf "Speichern" schliesst sich der Dialog
- Auf dem Dashboard zeigt die naechste Gieß-Erinnerung fuer Pflanze A das neue 10-Tage-Intervall an

**Nachbedingungen**:
- CareProfile von Pflanze A hat watering_interval_days=10

**Tags**: [req-022, care-profile, giesintervall, slider, speichern]

---

### TC-022-020: Winter-Multiplikator-Slider zeigt berechnetes effektives Intervall

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Winter-Multiplikator mit Ergebnis-Anzeige
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet fuer eine Pflanze mit Gießintervall 7 Tage

**Testschritte**:
1. Nutzer sieht den Slider "Winter-Multiplikator" bei Wert 1.5
2. Nutzer betrachtet die Ergebnis-Anzeige daneben
3. Nutzer verschiebt den Slider auf Wert 2.0

**Erwartete Ergebnisse**:
- Bei Multiplikator 1.5 und Basis-Intervall 7 Tage: Ergebnis-Anzeige zeigt "Im Winter: 11 Tage" (gerundet)
- Nach Verschieben auf 2.0: Ergebnis-Anzeige zeigt "Im Winter: 14 Tage"
- Die Beschriftung des Sliders lautet "Im Winter X-mal seltener gießen"

**Nachbedingungen**:
- Kein Profilwert gespeichert (noch kein Klick auf Speichern)

**Tags**: [req-022, care-profile, winter-multiplikator, slider, ergebnis-anzeige]

---

### TC-022-021: Aktive Duengemonate per Monats-Chips konfigurieren

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Aktive Düngemonate
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet fuer eine Pflanze mit care_style="tropical"
- Aktive Monate sind Maerz bis Oktober (Chips 3-10 aktiv)

**Testschritte**:
1. Nutzer sieht die Monats-Chips Jan bis Dez
2. Nutzer betrachtet welche Chips aktiviert (hervorgehoben) sind
3. Nutzer klickt auf den Chip "Nov" um November zu aktivieren
4. Nutzer klickt auf den Chip "Mrz" (Maerz) um ihn zu deaktivieren

**Erwartete Ergebnisse**:
- Zu Beginn sind die Chips Mrz, Apr, Mai, Jun, Jul, Aug, Sep, Okt aktiv (hervorgehoben)
- Nach Klick auf "Nov": Chip "Nov" ist nun auch hervorgehoben (aktiv)
- Nach Klick auf "Mrz": Chip "Mrz" ist nicht mehr hervorgehoben (inaktiv)
- Die Chips geben visuelles Feedback (aktivierter = gefuellte Chip-Farbe)

**Nachbedingungen**:
- Kein Wert gespeichert (noch kein Klick auf Speichern)

**Tags**: [req-022, care-profile, duengemonate, chips, multi-select]

---

### TC-022-022: Standort-Check deaktivieren blendet Monats-Konfiguration aus

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Standort-Check Toggle
**Priority**: Medium
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- location_check_enabled ist aktiviert (Toggle = ein)

**Testschritte**:
1. Nutzer sieht den Toggle "Saisonale Standort-Erinnerungen" in aktiviertem Zustand
2. Nutzer sieht die Felder "Winter-Warnung" und "Frühlings-Erinnerung" (Monats-Dropdown) sichtbar
3. Nutzer klickt auf den Toggle um ihn zu deaktivieren

**Erwartete Ergebnisse**:
- Der Toggle wechselt in den deaktivierten Zustand
- Die zwei Monats-Dropdown-Felder "Winter-Warnung" und "Frühlings-Erinnerung" verschwinden (werden ausgeblendet)

**Nachbedingungen**:
- Kein Wert gespeichert

**Tags**: [req-022, care-profile, standort-check, toggle, bedingte-felder, location-check]

---

### TC-022-023: Standort-Check aktivieren zeigt Monats-Dropdown-Felder

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Standort-Check Monate konfigurierbar
**Priority**: Medium
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- location_check_enabled ist deaktiviert (Toggle = aus)

**Testschritte**:
1. Nutzer sieht den Toggle "Saisonale Standort-Erinnerungen" deaktiviert
2. Nutzer klickt auf den Toggle um ihn zu aktivieren
3. Nutzer aendert das "Winter-Warnung"-Dropdown von Oktober auf September

**Erwartete Ergebnisse**:
- Nach dem Aktivieren des Toggles erscheinen die Dropdown-Felder "Winter-Warnung (Monat)" und "Frühlings-Erinnerung (Monat)"
- Die Defaults sind: Winter-Warnung = Oktober, Frühlings-Erinnerung = März (fuer Nordhalbkugel)
- Nach Auswahl von September im Winter-Warnung-Dropdown: Der Wert "September" ist im Dropdown ausgewaehlt

**Nachbedingungen**:
- Kein Wert gespeichert

**Tags**: [req-022, care-profile, standort-check, monate, konfigurierbar, nordhalbkugel]

---

### TC-022-024: Luftfeuchte-Check Toggle aktiviert bedingt Intervall-Slider

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Luftfeuchte-Check
**Priority**: Medium
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet fuer eine Pflanze mit care_style="tropical" (humidity_check_enabled=true)

**Testschritte**:
1. Nutzer sieht den Toggle "Luftfeuchte-Erinnerungen (Heizperiode)" im aktivierten Zustand
2. Nutzer sieht den Slider "Luftfeuchte-Check (Tage)" sichtbar
3. Nutzer klickt auf den Toggle um Luftfeuchte-Check zu deaktivieren

**Erwartete Ergebnisse**:
- Nach dem Deaktivieren: Der Slider "Luftfeuchte-Check (Tage)" verschwindet (wird ausgeblendet)
- Der Toggle befindet sich im deaktivierten Zustand

**Nachbedingungen**:
- Kein Wert gespeichert

**Tags**: [req-022, care-profile, luftfeuchte, toggle, bedingte-felder, humidity-check]

---

### TC-022-025: Adaptive-Learning Toggle deaktivieren

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Adaptive Learning Toggle
**Priority**: Medium
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- adaptive_learning_enabled ist aktiviert (Toggle = ein)

**Testschritte**:
1. Nutzer sieht den Toggle "Automatische Intervallanpassung" in aktiviertem Zustand
2. Nutzer klickt auf den Toggle

**Erwartete Ergebnisse**:
- Der Toggle wechselt in den deaktivierten Zustand
- Der Dialog zeigt keinerlei Fehlermeldung

**Nachbedingungen**:
- Kein Wert gespeichert

**Tags**: [req-022, care-profile, adaptive-learning, toggle]

---

### TC-022-026: Notizfeld im CareProfileEditDialog speichert Freitext

**Requirement**: REQ-022 § 5.2 — CareProfileEditDialog, Notizen-Feld
**Priority**: Low
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- Das Notizfeld ist leer

**Testschritte**:
1. Nutzer klickt in das Textfeld "Notizen"
2. Nutzer tippt: "Mag kein Leitungswasser, immer Regenwasser verwenden."
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich nach dem Speichern
- Nach erneutem Oeffnen des CareProfileEditDialog ist der eingegebene Text im Notizfeld sichtbar

**Nachbedingungen**:
- CareProfile hat notes="Mag kein Leitungswasser, immer Regenwasser verwenden."

**Tags**: [req-022, care-profile, notizen, freitext, speichern]

---

### TC-022-027: Care-Style-Wechsel zeigt Bestaetigung und setzt alle Intervalle zurueck

**Requirement**: REQ-022 § 5.2 — Care-Style-Wechsel mit Bestaetigung
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet fuer eine Pflanze mit care_style="tropical"
- Gießintervall ist manuell auf 10 Tage gesetzt (abweichend vom Preset-Wert 7)

**Testschritte**:
1. Nutzer aendert das Dropdown "Pflegestil" von "Tropische Grünpflanze" auf "Sukkulente"
2. Ein Bestaetigungs-Dialog erscheint

**Erwartete Ergebnisse**:
- Ein Bestaetigungs-Dialog erscheint mit dem Text: "Alle Intervalle werden auf Sukkulente-Standardwerte zurückgesetzt. Fortfahren?"
- (i18n-Key: pages.care.profile.styleChangeConfirm mit style="Sukkulente")
- Buttons "Abbrechen" und "Bestätigen" sind sichtbar

**Nachbedingungen**:
- Kein Wert noch geaendert (Dialog noch offen)

**Tags**: [req-022, care-profile, care-style, wechsel, bestaetigung, reset]

---

### TC-022-028: Care-Style-Wechsel bestaetigen setzt alle Intervalle auf Preset-Werte

**Requirement**: REQ-022 § 5.2 — Care-Style-Wechsel nach Bestaetigung
**Priority**: Critical
**Category**: Dialog
**Vorbedingungen**:
- Wie TC-022-027, aber Nutzer klickt auf "Bestätigen" im Bestaetigung-Dialog

**Testschritte**:
1. Nutzer hat Care-Style von "tropical" auf "succulent" geaendert
2. Bestaetigungs-Dialog ist sichtbar
3. Nutzer klickt auf "Bestätigen"

**Erwartete Ergebnisse**:
- Der Bestaetigungs-Dialog schliesst sich
- Im CareProfileEditDialog sind alle Slider auf die Sukkulenten-Preset-Werte gesetzt:
  - Gießintervall: 14 Tage (statt zuvor manuell 10)
  - Winter-Multiplikator: 2.5
  - Duengeintervall: 30 Tage
  - Umtopfintervall: 24 Monate
  - Schädlingskontrolle: 21 Tage
- Der Luftfeuchte-Check Toggle ist deaktiviert (succulent Preset: humidity_check_enabled=false)

**Nachbedingungen**:
- Werte noch nicht gespeichert (kein Klick auf Speichern-Button des Dialogs)

**Tags**: [req-022, care-profile, care-style, succulent, preset-werte, reset-intervalle]

---

### TC-022-029: Care-Style-Wechsel abbrechen behält bestehende Intervalle

**Requirement**: REQ-022 § 5.2 — Care-Style-Wechsel abbrechen
**Priority**: High
**Category**: Dialog
**Vorbedingungen**:
- Wie TC-022-027, aber Nutzer klickt auf "Abbrechen" im Bestaetigungsdialog

**Testschritte**:
1. Nutzer hat Care-Style auf "succulent" geaendert
2. Bestaetigungs-Dialog ist sichtbar
3. Nutzer klickt auf "Abbrechen"

**Erwartete Ergebnisse**:
- Der Bestaetigungs-Dialog schliesst sich
- Der Dropdown "Pflegestil" zeigt wieder "Tropische Grünpflanze" (unveraendert)
- Das manuell gesetzte Gießintervall von 10 Tagen ist unver aendert

**Nachbedingungen**:
- Kein Profilwert geaendert

**Tags**: [req-022, care-profile, care-style, abbrechen, rollback]

---

## 6. Reset auf Standardwerte

### TC-022-030: Reset auf Species-Defaults setzt gelernte Intervalle zurueck

**Requirement**: REQ-022 § 4 — POST /plants/{plant_key}/reset-profile
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat ein CareProfile mit gelerntem Gießintervall (watering_interval_learned=8.5)
- Der Nutzer ist auf der CareProfileEditDialog-Seite fuer Pflanze A
- Ein "Zurücksetzen"-Button ist im Dialog sichtbar

**Testschritte**:
1. Nutzer oeffnet den CareProfileEditDialog fuer Pflanze A
2. Nutzer klickt auf den Button "Auf Standardwerte zurücksetzen?"
3. Ein Bestaetigung-Dialog erscheint
4. Nutzer klickt auf "Bestätigen"

**Erwartete Ergebnisse**:
- Nach der Bestaetigung schliesst sich der Bestaetigung-Dialog
- Im CareProfileEditDialog sind die Slider auf die Species-Defaults zurueckgesetzt
- Das gelernte Intervall ist nicht mehr sichtbar (watering_interval_learned = nicht angezeigt oder als null dargestellt)
- Eine Bestaetigung (z.B. Snackbar "Profil zurückgesetzt") erscheint

**Nachbedingungen**:
- CareProfile von Pflanze A hat watering_interval_learned=null und verwendet wieder die Species-Defaults

**Tags**: [req-022, reset-profil, defaults, species, gelernte-intervalle]

---

## 7. Dungegruard — Saisonalitaet

### TC-022-031: Dashboard zeigt keine Duenge-Erinnerung außerhalb der Aktivmonate

**Requirement**: REQ-022 § 1 — Dünge-Guard, fertilizing_active_months
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Januar (außerhalb der tropical Aktivmonate Maerz-Oktober)
- Pflanze A hat care_style="tropical" mit fertilizing_active_months=[3,4,5,6,7,8,9,10]
- Das Duenge-Intervall ist rechnerisch abgelaufen (letzte Duengung vor 20 Tagen)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer durchsucht alle ReminderCards nach einer Duenge-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Duenge-Erinnerung fuer Pflanze A erscheint auf dem Dashboard
- Falls Gieß- oder andere Erinnerungen fuer Pflanze A faellig sind, erscheinen diese normal
- Die Duenge-Erinnerung bleibt unterdrueckt bis der erste Aktivmonat beginnt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, duenge-guard, saisonalitaet, aktivmonate, januar, tropical]

---

### TC-022-032: Dashboard zeigt keine Duenge-Erinnerung in Dormanz-Phase

**Requirement**: REQ-022 § 1 — Dünge-Guard, DORMANCY_PHASES
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Juni (innerhalb Aktivmonate fuer tropical)
- Pflanze A befindet sich in der Phase "dormancy" (Winterruhe)
- Das Duenge-Intervall ist rechnerisch abgelaufen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Duenge-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Duenge-Erinnerung fuer Pflanze A erscheint (Dormanz-Phase blockiert)
- Falls Gieß-Erinnerungen faellig sind, erscheinen diese weiterhin
- Die Schädlingskontroll-Erinnerung erscheint weiterhin (nicht durch Dormanz unterdrueckt)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, duenge-guard, dormanz, dormancy, phase, unterdrueckt]

---

### TC-022-033: Dashboard unterdrueckt Duenge-Erinnerung in acclimatization-Phase

**Requirement**: REQ-022 § 1 — Dünge-Guard, DORMANCY_PHASES (acclimatization)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Mai (innerhalb Aktivmonate)
- Pflanze A wurde gerade gekauft und befindet sich in der Phase "acclimatization"
- Das Duenge-Intervall ist rechnerisch abgelaufen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Duenge-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Duenge-Erinnerung fuer Pflanze A erscheint (acclimatization ist eine DORMANCY_PHASE)
- Eine Gieß-Erinnerung kann erscheinen, aber mit laengerem Intervall (×1.3 Faktor — naechster Testfall)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, duenge-guard, acclimatization, eingewoehnungsphase, neue-pflanze]

---

### TC-022-034: Dashboard unterdrueckt Duenge-Erinnerung in repotting_recovery-Phase

**Requirement**: REQ-022 § 1 — Dünge-Guard, DORMANCY_PHASES (repotting_recovery)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Juli (innerhalb Aktivmonate)
- Pflanze A wurde gerade umgetopft und befindet sich in Phase "repotting_recovery"
- Das Duenge-Intervall ist abgelaufen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Duenge-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Duenge-Erinnerung fuer Pflanze A erscheint
- Andere Erinnerungstypen (z.B. Schädlingskontrolle) erscheinen weiterhin

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, duenge-guard, repotting-recovery, umtopfen-erholung, dormancy]

---

## 8. Gießintervall in der Acclimatization-Phase (Faktor 1.3)

### TC-022-035: Gieß-Erinnerung in acclimatization-Phase erscheint spaeter (×1.3)

**Requirement**: REQ-022 § 3 — CareReminderEngine, Acclimatization-Faktor 1.3
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A hat care_style="tropical" mit watering_interval_days=7
- Pflanze A befindet sich in Phase "acclimatization"
- Aktueller Monat ist kein Wintermonat (Sommer — kein winter_watering_multiplier aktiv)
- Letzte Gießbestaetigung war vor 8 Tagen (7 × 1.3 = 9.1 → gerundet 9 Tage)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Gieß-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Nach 8 Tagen erscheint noch keine Gieß-Erinnerung fuer Pflanze A (9 Tage effektiv)
- Erst nach 9 Tagen erscheint die Gieß-Erinnerung (Faktor 1.3 × 7 = 9.1 → 9)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, acclimatization, giesintervall, faktor-1.3, spaeter]

---

## 9. Giessplan-Guard

### TC-022-036: Dashboard zeigt keine Gieß- und Duenge-Erinnerung fuer Pflanze in aktivem Giessplan

**Requirement**: REQ-022 § 3 — Celery Task, Gießplan-Guard
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A ist in einem aktiven PlantingRun mit NutrientPlan und WateringSchedule
- Alle Bedingungen des Gießplan-Guards sind erfuellt (Run aktiv + NutrientPlan + WateringSchedule)
- Gieß- und Duenge-Intervalle von Pflanze A sind abgelaufen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Gieß- und Duenge-ReminderCards fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Gieß-Erinnerung (watering) fuer Pflanze A erscheint
- Keine Duenge-Erinnerung (fertilizing) fuer Pflanze A erscheint
- Schädlingskontrolle (pest_check) erscheint weiterhin fuer Pflanze A (nicht vom Guard unterdrueckt)
- Umtopf-Erinnerung (repotting) erscheint weiterhin (nicht vom Guard unterdrueckt)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, giessplan-guard, watering-schedule, nutrient-plan, unterdrückt, req-004, req-013]

---

### TC-022-037: Dashboard zeigt Gieß-Erinnerung wenn PlantingRun abgeschlossen ist (Guard inaktiv)

**Requirement**: REQ-022 § 3 — Celery Task, Gießplan-Guard (Guard nur bei aktivem Run)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A war in einem PlantingRun mit WateringSchedule, der Run ist jetzt abgeschlossen (Status "completed")
- Das Gieß-Intervall von Pflanze A ist abgelaufen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Gieß-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine Gieß-Erinnerung fuer Pflanze A erscheint auf dem Dashboard
- Der Gießplan-Guard ist inaktiv (Run nicht mehr im Status "active")

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, giessplan-guard, run-completed, guard-inaktiv, giesserinnerung-aktiv]

---

## 10. Saisonale Standort-Check-Erinnerungen

### TC-022-038: Standort-Check Oktober — Erinnerung erscheint in ersten 15 Tagen des Oktober

**Requirement**: REQ-022 § 3 — CareReminderEngine, location_check Oktober (Nordhalbkugel)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum ist 7. Oktober (erste 15 Tage des Oktober)
- Pflanze A hat location_check_enabled=true
- Site hat hemisphere="northern"
- Keine location_check_months Konfiguration (Default: Oktober)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Standort-Check-ReminderCard fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine Standort-Check-Erinnerung erscheint fuer Pflanze A
- Das Icon zeigt Mond/Sonne (Standort-Icon)
- Der Anleitungstext lautet: "[Pflanzennamen] ins Winterquartier holen"
  (i18n-Key: pages.care.instructions.location_check_oct)
- Der Bestaetigen-Button zeigt "Kontrolliert"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, standort-check, oktober, nordhalbkugel, saisonal, location-check]

---

### TC-022-039: Standort-Check Oktober — Keine Erinnerung nach dem 15. Oktober

**Requirement**: REQ-022 § 3 — CareReminderEngine, location_check Zeitfenster (erste 15 Tage)
**Priority**: High
**Category**: Grenzwert
**Vorbedingungen**:
- Aktuelles Datum ist 20. Oktober (nach den ersten 15 Tagen)
- Pflanze A hat location_check_enabled=true, keine benutzerdefinierte Monats-Konfiguration

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Standort-Check-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Standort-Check-Erinnerung fuer Oktober erscheint (Zeitfenster 1.-15. Oktober ist abgelaufen)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, standort-check, grenzwert, oktober-15, kein-reminder]

---

### TC-022-040: Standort-Check Maerz — Frühlings-Erinnerung erscheint im Maerz

**Requirement**: REQ-022 § 3 — CareReminderEngine, location_check März (Nordhalbkugel)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum ist 5. Maerz (erste 15 Tage des Maerz)
- Pflanze A hat location_check_enabled=true
- Site hat hemisphere="northern"

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einer Standort-Check-ReminderCard fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine Standort-Check-Erinnerung erscheint fuer Pflanze A
- Der Anleitungstext lautet: "[Pflanzennamen] an helleren Standort stellen"
  (i18n-Key: pages.care.instructions.location_check_mar)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, standort-check, maerz, nordhalbkugel, fruehling, location-check]

---

### TC-022-041: Standort-Check deaktiviert — Keine saisonalen Erinnerungen erscheinen

**Requirement**: REQ-022 § 3 — CareReminderEngine, location_check_enabled=false
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum ist 7. Oktober
- Pflanze A hat location_check_enabled=false (manuell deaktiviert)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach Standort-Check-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Standort-Check-Erinnerung fuer Pflanze A erscheint
- Andere Erinnerungstypen (Gießen, Duengen) erscheinen weiterhin

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, standort-check, deaktiviert, location-check-disabled]

---

### TC-022-042: Benutzerdefinierte Standort-Check-Monate werden verwendet (September statt Oktober)

**Requirement**: REQ-022 § 3 — CareReminderEngine, konfigurierbare location_check_months
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A hat location_check_months={"winter_warning": 9, "spring_reminder": 4} (September/April statt Oktober/Maerz)
- Aktuelles Datum ist 10. September
- location_check_enabled=true

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach Standort-Check-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine Standort-Check-Erinnerung fuer Pflanze A erscheint (September als konfigurierter Monat)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, standort-check, benutzerdefiniert, september, klimazone]

---

## 11. Luftfeuchte-Check-Erinnerungen (Heizperiode)

### TC-022-043: Luftfeuchte-Check erscheint in Heizperiode fuer Calathea

**Requirement**: REQ-022 § 1 — humidity_check, nur in Heizperiode, feuchtigkeitsempfindliche Presets
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Dezember (Heizperiode NH: Okt-Feb)
- Pflanze A hat care_style="calathea" mit humidity_check_enabled=true, humidity_check_interval_days=7
- Letzte Luftfeuchte-Bestaetigung war vor 8 Tagen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach einem Luftfeuchte-Check-ReminderCard fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine Luftfeuchte-Check-Erinnerung erscheint fuer Pflanze A
- Icon zeigt Tropfen/Nebel-Symbol
- Anleitungstext: "Luftfeuchtigkeit bei [Pflanzennamen] prüfen — ggf. Luftbefeuchter oder Kieselschale verwenden"
  (i18n-Key: pages.care.instructions.humidity_check)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, luftfeuchte, heizperiode, calathea, humidity-check, dezember]

---

### TC-022-044: Luftfeuchte-Check erscheint NICHT im Sommer (außerhalb Heizperiode)

**Requirement**: REQ-022 § 3 — CareReminderEngine, humidity_check nur in Wintermonaten
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Juli (kein Wintermonat NH)
- Pflanze A hat care_style="calathea" mit humidity_check_enabled=true

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach Luftfeuchte-Check-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Luftfeuchte-Check-Erinnerung fuer Pflanze A erscheint (kein Wintermonat)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, luftfeuchte, sommer, kein-reminder, juli, nordhalbkugel]

---

### TC-022-045: Luftfeuchte-Check erscheint NICHT fuer Sukkulente (humidity_check_enabled=false)

**Requirement**: REQ-022 § 1 — humidity_check_enabled=false bei succulent Preset
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Januar (Heizperiode)
- Pflanze A hat care_style="succulent" mit humidity_check_enabled=false

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht nach Luftfeuchte-Check-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Luftfeuchte-Check-Erinnerung fuer Pflanze A erscheint (succulent hat humidity_check disabled)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, luftfeuchte, succulent, disabled, kein-reminder]

---

## 12. Saisonale Gießintervall-Anpassung (Winter-Multiplikator)

### TC-022-046: Kaktus-Gieß-Erinnerung erscheint im Winter erst nach 63 Tagen (21 × 3.0)

**Requirement**: REQ-022 § 1 — winter_watering_multiplier, Kaktus 3.0×
**Priority**: High
**Category**: Grenzwert
**Vorbedingungen**:
- Aktueller Monat ist Dezember (Wintermonat NH)
- Pflanze A hat care_style="cactus" mit watering_interval_days=21, winter_watering_multiplier=3.0
- Letzte Gießbestaetigung war vor 62 Tagen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Gieß-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Nach 62 Tagen erscheint noch keine Gieß-Erinnerung (effektives Intervall = 63 Tage: 21 × 3.0)
- Erst nach 63 Tagen ist die Erinnerung faellig

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, winter-multiplikator, kaktus, 63-tage, grenzwert, saison]

---

### TC-022-047: Tropical-Gieß-Erinnerung erscheint im Winter nach 11 Tagen (7 × 1.5)

**Requirement**: REQ-022 § 1 — winter_watering_multiplier, tropical 1.5×
**Priority**: High
**Category**: Grenzwert
**Vorbedingungen**:
- Aktueller Monat ist Januar (Wintermonat NH)
- Pflanze A hat care_style="tropical" mit watering_interval_days=7, winter_watering_multiplier=1.5
- Letzte Gießbestaetigung war vor 10 Tagen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Gieß-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Nach 10 Tagen erscheint noch keine Gieß-Erinnerung (effektives Intervall = 11 Tage: 7 × 1.5 = 10.5 → gerundet 11)
- Erst nach Tag 11 erscheint die Erinnerung

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, winter-multiplikator, tropical, 11-tage, grenzwert, saison]

---

## 13. Auto-Generierung des CareProfile

### TC-022-048: Erstmaliger Aufruf des Pflegeprofils einer Pflanze generiert es automatisch

**Requirement**: REQ-022 § 3 — CareReminderService.get_or_create_profile
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat noch kein CareProfile (neue Pflanze, z.B. eine Phalaenopsis-Orchidee)
- Die Species der Pflanze A gehoert zur Familie Orchidaceae

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Die Erinnerungen fuer alle Pflanzen werden geladen

**Erwartete Ergebnisse**:
- Pflanze A erscheint auf dem Dashboard mit einer Gieß-Erinnerung (sofort faellig — noch nie bestaetigt)
- Beim Oeffnen des CareProfileEditDialog fuer Pflanze A zeigt der Dialog care_style="orchid" vorbelegt
- Das Gießintervall ist 7 Tage (orchid Preset)
- Die Gießmethode ist "Tauchbad" (soak)
- Das Profil ist als automatisch generiert erkennbar (z.B. Hinweistext "Automatisch generiert aus Artdaten")

**Nachbedingungen**:
- CareProfile fuer Pflanze A ist erstellt mit care_style="orchid" und auto_generated=true

**Tags**: [req-022, auto-generierung, care-profile, orchidaceae, orchid, mapping]

---

### TC-022-049: Auto-Generierung fuer Kaktus aus Familie Cactaceae

**Requirement**: REQ-022 § 3 — CareReminderService.get_or_create_profile, Cactaceae → cactus
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Pflanze A ist eine Echeveria (Familie: Crassulaceae) — sollte "succulent" ergeben
- Pflanze B ist ein Cereus-Kaktus (Familie: Cactaceae) — sollte "cactus" ergeben

**Testschritte**:
1. Nutzer navigiert zum CareProfileEditDialog fuer Pflanze A (Echeveria)
2. Nutzer betrachtet den aktuellen care_style
3. Nutzer navigiert zum CareProfileEditDialog fuer Pflanze B (Cereus)
4. Nutzer betrachtet den aktuellen care_style

**Erwartete Ergebnisse**:
- Pflanze A (Echeveria, Crassulaceae): care_style = "Sukkulente"
- Pflanze B (Cereus, Cactaceae): care_style = "Kaktus"

**Nachbedingungen**:
- Kein Profilwert manuell geaendert

**Tags**: [req-022, auto-generierung, cactaceae, cactus, crassulaceae, succulent, mapping]

---

## 14. Bestaetigungshistorie

### TC-022-050: Bestaetigungshistorie einer Pflanze anzeigen

**Requirement**: REQ-022 § 4 — GET /plants/{plant_key}/history
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat mindestens 5 Bestaetigungen in der Vergangenheit

**Testschritte**:
1. Nutzer navigiert zur PlantInstance-Detailseite von Pflanze A
2. Nutzer klickt auf den Tab oder Link "Pflege-Verlauf" bzw. "Bestaetigungshistorie"

**Erwartete Ergebnisse**:
- Eine chronologisch sortierte Liste von Bestaetigungen wird angezeigt
- Jeder Eintrag zeigt: Erinnerungstyp-Icon, Aktion (Bestaetigt/Verschoben/Uebersprungen), Datum und ggf. Notiz
- Die neuesten Eintraege erscheinen zuerst (absteigend nach Datum)
- Es werden maximal 50 Eintraege angezeigt (Default-Limit)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, bestaetigungshistorie, history, plant-detail, verlauf]

---

### TC-022-051: Bestaetigungshistorie gefiltert nach Erinnerungstyp "Gießen"

**Requirement**: REQ-022 § 4 — GET /plants/{plant_key}/history?reminder_type=watering
**Priority**: Medium
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Pflanze A hat sowohl Gieß- als auch Duenge-Bestaetigungen in der Historie

**Testschritte**:
1. Nutzer navigiert zur Bestaetigungshistorie von Pflanze A
2. Nutzer waehlt im Filter-Dropdown den Erinnerungstyp "Gießen"

**Erwartete Ergebnisse**:
- Nur Eintraege mit Erinnerungstyp "Gießen" werden angezeigt
- Duenge- und andere Bestaetigungen sind aus der Liste gefiltert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, bestaetigungshistorie, filter, watering, reminder-type]

---

## 15. Adaptive Learning — Sichtbare Auswirkungen im UI

### TC-022-052: Gelerntes Gießintervall wird im CareProfileEditDialog angezeigt

**Requirement**: REQ-022 § 1 — Adaptive Learning, watering_interval_learned
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Pflanze A hat ein CareProfile mit watering_interval_days=7 (Basis) und watering_interval_learned=8.5 (gelernt)
- Das Adaptive Learning hat nach 3 konsistenten Signalen das Intervall erhoet

**Testschritte**:
1. Nutzer oeffnet den CareProfileEditDialog fuer Pflanze A

**Erwartete Ergebnisse**:
- Der Slider fuer Gießintervall zeigt den gelernten Wert (8.5 → angezeigt als ca. 9 Tage oder 8.5 Tage)
- Ein Hinweis ist sichtbar, der das gelernte Intervall vom Basis-Intervall unterscheidet (z.B. "Automatisch angepasst: 9 Tage (Basis: 7 Tage)")
- Der Reset-Button kann verwendet werden um zum Basis-Intervall zurueckzukehren

**Nachbedingungen**:
- Kein Profilwert geaendert

**Tags**: [req-022, adaptive-learning, gelerntes-intervall, anzeige, slider]

---

### TC-022-053: Adaptive Learning respektiert ±30%-Grenze — Maximales Intervall sichtbar

**Requirement**: REQ-022 § 1 — Adaptive Learning, max ±30% Abweichung
**Priority**: High
**Category**: Grenzwert
**Vorbedingungen**:
- Pflanze A hat watering_interval_days=7 (Basis), gelernt wird 9.1 (=130% von 7)
- Der Adaptive-Learning-Algorithmus hat 3 konsistente Signale von > +1 Tag

**Testschritte**:
1. Nutzer wartet bis Adaptive Learning greift (passiert im Hintergrund via Celery)
2. Nutzer oeffnet den CareProfileEditDialog fuer Pflanze A

**Erwartete Ergebnisse**:
- Der Slider zeigt maximal 9 Tage (7 × 1.3 = 9.1 → Grenze) — nicht mehr als 130%
- Ein weiteres Auslernen ueber diese Grenze hinaus ist nicht moeglich

**Nachbedingungen**:
- Kein Profilwert manuell geaendert

**Tags**: [req-022, adaptive-learning, grenze, max-30-prozent, sicherheitsgrenze]

---

## 16. Validierungsfehler im CareProfileEditDialog

### TC-022-054: Gießintervall außerhalb 1-90 Tage zeigt Validierungsfehler

**Requirement**: REQ-022 § 3 — CareProfile, watering_interval_days Field(ge=1, le=90)
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- Slider fuer Gießintervall ist sichtbar (Bereich 1-30 Tage laut Spec §5.2)

**Testschritte**:
1. Nutzer versucht den Gießintervall-Slider unter den Minimalwert (1 Tag) zu schieben
2. Nutzer versucht den Slider ueber den Maximalwert (30 Tage fuer Slider-UI, 90 Tage Backend) zu schieben

**Erwartete Ergebnisse**:
- Der Slider stoppt am Minimum-Endpunkt (1 Tag) und kann nicht weiter nach links geschoben werden
- Der Slider stoppt am Maximum-Endpunkt (30 Tage) und kann nicht weiter nach rechts geschoben werden
- Kein manuelles Eingabefeld erlaubt Werte außerhalb des Bereichs

**Nachbedingungen**:
- Kein Profilwert geaendert (Slider nur bewegt, nicht gespeichert)

**Tags**: [req-022, care-profile, validierung, giesintervall, slider-grenzen, min-max]

---

### TC-022-055: Duengeintervall außerhalb 7-90 Tage wird durch Slider verhindert

**Requirement**: REQ-022 § 3 — CareProfile, fertilizing_interval_days Field(ge=7, le=90)
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- Slider fuer Duengeintervall ist sichtbar (Bereich 7-60 Tage laut Spec §5.2)

**Testschritte**:
1. Nutzer versucht den Duengeintervall-Slider unter 7 Tage zu schieben

**Erwartete Ergebnisse**:
- Der Slider stoppt bei 7 Tagen (Minimum)

**Nachbedingungen**:
- Kein Wert geaendert

**Tags**: [req-022, care-profile, validierung, duengeintervall, slider-minimum]

---

### TC-022-056: Aktivmonate — Mindestens ein Monat muss ausgewaehlt bleiben

**Requirement**: REQ-022 § 3 — CareProfile, fertilizing_active_months min_length=1
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist eingeloggt
- CareProfileEditDialog ist geoeffnet
- Nur noch ein Monat in den Aktivmonaten-Chips ist aktiv (z.B. nur "Jun")

**Testschritte**:
1. Nutzer klickt auf den letzten aktiven Chip "Jun" um ihn zu deaktivieren
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Entweder: Der Chip "Jun" kann nicht deaktiviert werden (bleibt aktiv, kein Click-Effekt wenn letzter Chip)
- Oder: Eine Fehlermeldung erscheint beim Klick auf "Speichern": "Mindestens ein Dünge-Monat muss ausgewählt sein"

**Nachbedingungen**:
- Kein Profilwert geaendert

**Tags**: [req-022, care-profile, aktivmonate, min-1, validierung]

---

## 17. Authentifizierung und Zugriffsschutz

### TC-022-057: PflegeDashboardPage ohne Anmeldung — Weiterleitung zur Login-Seite

**Requirement**: REQ-022 § 7 — Authentifizierung
**Priority**: Critical
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist NICHT eingeloggt (keine aktive Session)

**Testschritte**:
1. Nutzer navigiert direkt zur URL `/pflege`

**Erwartete Ergebnisse**:
- Nutzer wird zur Login-Seite weitergeleitet
- Die PflegeDashboardPage ist nicht sichtbar
- Kein Datenzugriff findet statt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, auth, login, redirect, unauthenticated]

---

### TC-022-058: Bestaetigungsversuch ohne Anmeldung — Fehlermeldung oder Redirect

**Requirement**: REQ-022 § 7 — Authentifizierung fuer Schreib-Operationen
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Nutzer war eingeloggt, Session ist abgelaufen
- PflegeDashboardPage ist noch im Browser-Tab geladen

**Testschritte**:
1. Nutzer klickt auf "Gegossen" fuer eine Pflanze (Session abgelaufen)

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (z.B. Snackbar "Sitzung abgelaufen. Bitte erneut anmelden.")
- Oder: Nutzer wird zur Login-Seite weitergeleitet
- Die Bestaetigung wird nicht gespeichert

**Nachbedingungen**:
- Kein Bestaetigungseintrag erstellt

**Tags**: [req-022, auth, session-abgelaufen, bestaetigung-fehler]

---

## 18. Ueberwinterungs-Erinnerungen (Outdoor-Pflanzen)

### TC-022-059: Winterschutz-Erinnerung erscheint fuer frost_tender Pflanze im Oktober

**Requirement**: REQ-022 § 1 — Erinnerungstyp winter_protection, Prioritaet high
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum ist 5. Oktober (NH)
- Pflanze A ist eine Dahlie (frost_sensitivity="tender", hardiness_rating="dig_and_store")
- Pflanze A hat ein OverwinteringProfile mit winter_action_month=10

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer betrachtet die Liste der Erinnerungskarten

**Erwartete Ergebnisse**:
- Eine Winterschutz-Erinnerung (reminder_type="winter_protection" oder "tuber_dig") erscheint fuer Pflanze A
- Das Badge zeigt hohe Prioritaet ("critical" oder "high") mit entsprechender Farbe
- Der Anleitungstext beschreibt die Winterschutz-Maßnahme (z.B. "Dahlienknollen ausgraben")

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, ueberwinterung, winterschutz, tuber-dig, frost-tender, oktober, outdoor]

---

### TC-022-060: Keine Winterschutz-Erinnerung fuer frostharte Pflanze (frost_sensitivity=hardy)

**Requirement**: REQ-022 § 2 — Winterschutz-Guard fuer frostharte Pflanzen
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum ist 7. Oktober (NH)
- Pflanze A ist ein Hornveilchen/Stiefmuetterchen (Species.frost_sensitivity="hardy")

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Winterschutz-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Winterschutz-Erinnerung (winter_protection, spring_uncover, tuber_dig, storage_check) erscheint fuer Pflanze A
- Der Winterschutz-Guard verhindert irreführende Erinnerungen fuer frostharte Pflanzen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, winterschutz-guard, frosthart, hardy, stiefmuetterchen, viola, kein-reminder]

---

### TC-022-061: Fruehlingsauspacken-Erinnerung erscheint im Maerz fuer ueberwinterte Pflanze

**Requirement**: REQ-022 § 1 — Erinnerungstyp spring_uncover, spring_action_month=3
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum ist 8. Maerz (NH)
- Pflanze A hat ein OverwinteringProfile mit spring_action="uncover", spring_action_month=3

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Fruehlingsauspacken-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine "Frühlings-Auspacken"-Erinnerung (reminder_type="spring_uncover") erscheint fuer Pflanze A mit Prioritaet "high"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, spring-uncover, fruehling, maerz, ueberwinterung, spring-action]

---

### TC-022-062: Knollen-Kontrolle erscheint waehrend Lagerzeit (stored-Status)

**Requirement**: REQ-022 § 2 — Knolle-Zyklus, storage_check Intervall
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktueller Monat ist Dezember (NH)
- Pflanze A (Dahlie) hat OverwinteringProfile mit tuber_status="stored"
- storage_check_interval_days=30
- Letzte Knollen-Kontrolle war vor 31 Tagen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Knollen-Kontrolle-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine "Knollen-Kontrolle"-Erinnerung (reminder_type="storage_check") erscheint fuer Pflanze A
- Der Anleitungstext beschreibt den Zweck: Faeulnis und Austrocknung pruefen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, storage-check, knollen-kontrolle, stored, dezember, ueberwinterung]

---

## 19. Winterhaerte-Ampel Widget im Dashboard

### TC-022-063: Winterhaerte-Ampel-Widget erscheint ab September

**Requirement**: REQ-022 § 2 — Dashboard-Widget "Winterschutz-Uebersicht" ab September
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Aktuelles Datum liegt im September oder spaeter (NH)
- Mindestens eine Pflanze hat ein OverwinteringProfile

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer scrollt nach unten und sucht das Winterschutz-Widget

**Erwartete Ergebnisse**:
- Ein Widget "Winterschutz-Uebersicht" ist auf der Seite sichtbar
- Das Widget zeigt die Anzahl Pflanzen je Ampelfarbe, z.B. "42 grün / 18 gelb / 7 rot"
- Die rot-markierten Pflanzen sind mit konkreter Handlungsanweisung aufgelistet

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, winterschutz-widget, ampel, dashboard, september, ueberwinterung]

---

### TC-022-064: Winterhaerte-Ampel-Widget erscheint NICHT im Juli (außerhalb September-Saison)

**Requirement**: REQ-022 § 2 — Dashboard-Widget nur ab September
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- Aktuelles Datum liegt im Juli (NH)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer scrollt durch die gesamte Seite

**Erwartete Ergebnisse**:
- Das "Winterschutz-Uebersicht"-Widget ist NICHT sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, winterschutz-widget, juli, nicht-sichtbar, saisonal]

---

## 20. Deadheading-Erinnerung (outdoor_annual_ornamental)

### TC-022-065: Deadheading-Erinnerung erscheint fuer Stiefmuetterchen in Bluetephase

**Requirement**: REQ-022 § 3 — Preset outdoor_annual_ornamental, deadheading_enabled=true
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A ist ein Stiefmuetterchen mit care_style="outdoor_annual_ornamental"
- Pflanze A befindet sich in Phase "flowering" (Bluetephase)
- Letzte Deadheading-Bestaetigung war vor 6 Tagen (Intervall: 5 Tage)

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Deadheading-Erinnerung fuer Pflanze A

**Erwartete Ergebnisse**:
- Eine Deadheading-Erinnerung ("Verblühtes entfernen") erscheint fuer Pflanze A
- Der Bestaetigen-Button zeigt "Kontrolliert" oder "Erledigt"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, deadheading, stiefmuetterchen, flowering, outdoor-annual-ornamental]

---

### TC-022-066: Keine Deadheading-Erinnerung fuer self_cleaning Cultivar (Surfinia)

**Requirement**: REQ-022 § 2 — Deadheading-Guard fuer self_cleaning Cultivare (AB-016)
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A ist eine Surfinia-Petunie mit Cultivar.traits=["self_cleaning"]
- care_style="outdoor_annual_ornamental" (deadheading_enabled=true in Preset)
- Pflanze A befindet sich in Phase "flowering"
- Letzte Deadheading-Bestaetigung war vor 7 Tagen

**Testschritte**:
1. Nutzer navigiert zur PflegeDashboardPage `/pflege`
2. Nutzer sucht Deadheading-Erinnerungen fuer Pflanze A

**Erwartete Ergebnisse**:
- Keine Deadheading-Erinnerung erscheint fuer Pflanze A
- Der self_cleaning-Guard verhindert die Erinnerung trotz aktiviertem Preset

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, deadheading-guard, self-cleaning, surfinia, petunia, keine-erinnerung]

---

## 21. Integration mit REQ-021 Einsteiger-Pflegekarte

### TC-022-067: Naechste-Aktion-Zeile auf Einsteiger-Pflegekarte zeigt Daten aus REQ-022

**Requirement**: REQ-022 § 5.3 — Integration mit REQ-021 Einsteiger-Pflegekarte
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt im Einsteiger-Modus
- Pflanze A hat eine dringende Gieß-Erinnerung (heute faellig)
- Die PlantInstance-Detailseite von Pflanze A hat eine Einsteiger-Pflegekarte

**Testschritte**:
1. Nutzer navigiert zur PlantInstance-Detailseite von Pflanze A
2. Nutzer betrachtet die Einsteiger-Pflegekarte

**Erwartete Ergebnisse**:
- Die "Nächste Aktion"-Zeile zeigt: "Heute gießen" oder "Heute fällig: Gießen"
- Die "Letzte Pflege"-Zeile zeigt: "Zuletzt gegossen: vor X Tagen"
- Die Pflegeprofil-Zeile zeigt den Care-Style: "Tropische Grünpflanze" (oder entsprechendes Label)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-022, einsteiger-pflegekarte, naechste-aktion, req-021, integration]

---

## 22. Giessplan-Interop (REQ-014 CareConfirmation)

### TC-022-068: Bestaetigung eines Giessplan-Tasks erzeugt CareConfirmation fuer Adaptive Learning

**Requirement**: REQ-022 § 3 — CareConfirmation-Interop mit Giessplan-Workflow
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Pflanze A ist in einem aktiven PlantingRun mit WateringSchedule
- Der Gießplan-Guard unterdrückt direkte Gieß-Erinnerungen fuer Pflanze A (kein REQ-022-Reminder sichtbar)
- Ein Gießplan-Task fuer Pflanze A erscheint in der Aufgabenliste (REQ-006)
- Pflanze A hat ein CareProfile

**Testschritte**:
1. Nutzer navigiert zur Aufgabenliste oder zur Gießplan-Bestaetigungsseite (REQ-006/REQ-014)
2. Nutzer bestaetigt den Gießplan-Task fuer Pflanze A
3. Nutzer navigiert zurueck zur Pflege-Bestaetigungshistorie von Pflanze A (`/pflege/pflanzen/{key}/history` oder entsprechende Route)

**Erwartete Ergebnisse**:
- In der Bestaetigungshistorie von Pflanze A erscheint ein neuer Eintrag:
  - Erinnerungstyp: "Gießen"
  - Aktion: "Bestaetigt"
  - Datum: heute
- Der Eintrag ist durch den Gießplan-Task erzeugt worden (kein manueller REQ-022-Reminder)
- Die "Zuletzt gegossen"-Anzeige auf einer eventuell vorhandenen Pflegekarte ist aktualisiert

**Nachbedingungen**:
- CareConfirmation-Eintrag fuer Gießen von Pflanze A ist erstellt
- Adaptive Learning erhaelt den korrekten Datenpunkt

**Tags**: [req-022, care-confirmation-interop, giessplan, req-014, adaptive-learning, watering-event]

---

## Abdeckungsmatrix

| Spec-Abschnitt | Beschreibung | Testfall-IDs |
|----------------|-------------|--------------|
| § 1 Business Case — Care-Style-Presets | 9 Presets, Gießmethoden, Wasserqualitaets-Hinweise | TC-022-005, TC-022-006, TC-022-007, TC-022-028, TC-022-046, TC-022-047 |
| § 1 Business Case — Erinnerungstypen (10 Typen) | watering, fertilizing, repotting, pest_check, location_check, humidity_check, winter_protection, spring_uncover, tuber_dig, storage_check | TC-022-012, TC-022-013, TC-022-014, TC-022-038, TC-022-039, TC-022-040, TC-022-043, TC-022-059, TC-022-061, TC-022-062 |
| § 1 Business Case — Dünge-Guard | Saison + Dormanz-Phasen | TC-022-031, TC-022-032, TC-022-033, TC-022-034 |
| § 1 Business Case — Adaptive Learning | 3 konsistente Signale, ±30% Grenze | TC-022-025, TC-022-052, TC-022-053 |
| § 1 Business Case — Gießplan-Guard | Unterdrueckung bei aktivem WateringSchedule | TC-022-036, TC-022-037, TC-022-068 |
| § 1 Business Case — Winter-Multiplikator | Saisonale Gießintervall-Anpassung | TC-022-046, TC-022-047 |
| § 1 Business Case — Acclimatization-Faktor 1.3 | Gießintervall bei neuer Pflanze | TC-022-033, TC-022-035 |
| § 2 ArangoDB — Winterhaerte-Ampel | Ampel-Logik, Guard fuer frostharte Pflanzen | TC-022-059, TC-022-060, TC-022-063, TC-022-064 |
| § 2 ArangoDB — Knollen-Zyklus | 6 Status-Stufen, storage_check | TC-022-062 |
| § 2 ArangoDB — Deadheading-Guard | self_cleaning Cultivar | TC-022-065, TC-022-066 |
| § 3 Technische Umsetzung — Auto-Generierung CareProfile | get_or_create_profile, Mapping-Logik | TC-022-048, TC-022-049 |
| § 3 Technische Umsetzung — CareConfirmation-Interop | Gießplan-Bestaetigung erzeugt CareConfirmation | TC-022-068 |
| § 3 Technische Umsetzung — location_check saisonal | konfigurierbare Monate, Hemisphäre | TC-022-038, TC-022-039, TC-022-040, TC-022-041, TC-022-042 |
| § 5.1 Frontend — PflegeDashboardPage | Layout, Sortierung, leerer Zustand | TC-022-001, TC-022-002, TC-022-009, TC-022-010, TC-022-011 |
| § 5.1 Frontend — ReminderCard Elemente | Icon, Badge, Bestaetigen, Snooze, Letzte Aktion | TC-022-005 bis TC-022-011 |
| § 5.1 Frontend — Gießmethoden-Anleitungstext | watering_method auf ReminderCard | TC-022-005 |
| § 5.1 Frontend — Wasserqualitaets-Hinweis | water_quality_hint (Calathea, Orchidee, Farn) | TC-022-006, TC-022-007 |
| § 5.1 Frontend — Symptom-Check bei Umtopfen | repotting_hint auf ReminderCard | TC-022-008 |
| § 5.2 Frontend — CareProfileEditDialog | Slider, Chips, Toggles, Speichern | TC-022-019 bis TC-022-026 |
| § 5.2 Frontend — Care-Style-Wechsel | Bestaetigungs-Dialog, Reset aller Intervalle | TC-022-027, TC-022-028, TC-022-029 |
| § 5.3 Frontend — REQ-021 Integration | Einsteiger-Pflegekarte, Naechste-Aktion | TC-022-067 |
| § 5.4 Frontend — Optimistic Updates | Confirm/Snooze sofortige UI-Aktualisierung, Rollback | TC-022-012, TC-022-015, TC-022-016 |
| § 5.6 Frontend — Navigations-Tiering | Einsteiger Position 3, Experte Position 6 | TC-022-003, TC-022-004 |
| § 6 Akzeptanzkriterien — Reset-Profile | Zuruecksetzen auf Species-Defaults | TC-022-030 |
| § 6 Akzeptanzkriterien — Bestaetigungshistorie | history Endpunkt, Filter | TC-022-050, TC-022-051 |
| § 6 Akzeptanzkriterien — Adaptive Learning Toggle | An/Aus schalten | TC-022-025 |
| § 7 Authentifizierung | Zugriffsschutz, Session-Ablauf | TC-022-057, TC-022-058 |
| Grenzwerte Formvalidierung | Slider-Grenzen, min Aktivmonat | TC-022-054, TC-022-055, TC-022-056 |
