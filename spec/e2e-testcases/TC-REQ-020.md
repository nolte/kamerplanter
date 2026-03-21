---
req_id: REQ-020
title: "Geführter Onboarding-Wizard für Erstnutzer"
category: Benutzerführung
test_count: 52
coverage_areas:
  - "5.2 Wizard-Schritte (Schritt 1–7)"
  - "5.3 Wizard-Trigger (Erststart, Wiederaufruf, Skip)"
  - "5.4 Responsive Design"
  - "6. Akzeptanzkriterien (Funktional)"
  - "1.1 Szenarien Moduswechsel (A–E)"
  - "1.2 Starter-Kits und Stammdaten-Scoping (Szenarien F, G)"
  - "Favoriten-System v1.5 (Schritt 4 + 5)"
  - "Smart-Home-Toggle v1.6"
  - "Resume-Funktion"
  - "Fehlerzustände und Netzwerkfehler"
generated: "2026-03-21"
version: "1.6"
---

# TC-REQ-020: Onboarding-Wizard — End-to-End-Testfälle

Alle Testfälle beschreiben ausschließlich Aktionen und Beobachtungen aus der Perspektive
eines Nutzers, der einen Browser bedient. Interne API-Calls, HTTP-Statuscodes und
Datenbank-Interna sind keine Testgegenstände; die entsprechenden UI-Manifestationen
(Fehlermeldungen, Statusänderungen, Weiterleitungen) werden stattdessen geprüft.

Route: `/onboarding` (lazy-loaded in AppRoutes)
Komponente: `src/frontend/src/pages/onboarding/OnboardingWizard.tsx`
`data-testid`: `onboarding-wizard`

---

## Gruppe A — Wizard-Trigger und Initialisierung

---

## TC-020-001: Erststart — Wizard öffnet automatisch bei unvollständigem Onboarding-Status

**Requirement**: REQ-020 §5.3 — Wizard-Trigger: Erststart
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (z.B. Demo-User `demo@kamerplanter.local`)
- `onboarding_state.completed == false` und `onboarding_state.skipped == false`
- Keine vorherigen Wizard-Fortschritte gespeichert (`wizard_step == 0`)

**Test Steps**:
1. Nutzer navigiert zur Anwendungs-URL (z.B. `http://localhost:5173`)
2. Nutzer öffnet die Route `/onboarding` direkt oder wird vom System dorthin gelenkt

**Expected Results**:
- Das Element `[data-testid="onboarding-wizard"]` ist sichtbar
- Der MUI-Stepper zeigt Schritt 1 als aktiven Schritt an (Desktop: erster Step hervorgehoben)
- Das Element `[data-testid="onboarding-step-welcome"]` ist sichtbar
- Drei Erfahrungsstufen-Karten sind sichtbar: `[data-testid="experience-beginner"]`, `[data-testid="experience-intermediate"]`, `[data-testid="experience-expert"]`
- Die Karte "Einsteiger" ist initial ausgewählt (hervorgehobene Rahmendarstellung)
- Die Schaltfläche `[data-testid="skip-onboarding"]` ist sichtbar
- Die Schaltfläche `[data-testid="onboarding-back"]` ist nicht vorhanden (Schritt 1 hat keinen Zurück-Button)
- Die Schaltfläche `[data-testid="onboarding-next"]` ist sichtbar und aktiv

**Postconditions**:
- Nutzer befindet sich auf Schritt 1 des Wizards

**Tags**: [req-020, onboarding, wizard-trigger, erststart, happy-path]

---

## TC-020-002: Bereits abgeschlossenes Onboarding — Abgeschlossen-Karte statt Wizard

**Requirement**: REQ-020 §5.3 — Wizard-Trigger: Wiederaufruf
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- `onboarding_state.completed == true`

**Test Steps**:
1. Nutzer navigiert zur Route `/onboarding`

**Expected Results**:
- Das Element `[data-testid="onboarding-wizard"]` ist sichtbar
- KEIN MUI-Stepper und kein Schritt-Inhalt wird angezeigt
- Eine Card mit Checkmark-Icon und dem Text "Onboarding bereits abgeschlossen" (o.ä.) ist sichtbar
- Die Schaltfläche `[data-testid="onboarding-restart"]` ist sichtbar (Label: "Erneut starten" o.ä.)
- Die Schaltfläche `[data-testid="onboarding-go-dashboard"]` ist sichtbar (Label: "Zum Dashboard")

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, onboarding, wizard-trigger, abgeschlossen, zustandswechsel]

---

## TC-020-003: Übersprungenes Onboarding — Abgeschlossen-Karte zeigt Neustart-Option

**Requirement**: REQ-020 §6 — Akzeptanzkriterien: "Überspringen" setzt skipped=true
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- `onboarding_state.skipped == true`

**Test Steps**:
1. Nutzer navigiert zur Route `/onboarding`

**Expected Results**:
- Abgeschlossen-Karte ist sichtbar (gleiche Darstellung wie TC-020-002)
- Schaltflächen "Erneut starten" und "Zum Dashboard" sind sichtbar
- Stepper und Schritt-Inhalte sind nicht sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, onboarding, skipped, zustandswechsel]

---

## TC-020-004: Neustart des Wizards aus der Abgeschlossen-Karte

**Requirement**: REQ-020 §5.3 — Wiederaufruf
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- `onboarding_state.completed == true` oder `skipped == true`
- Nutzer befindet sich auf der Abgeschlossen-Karte (aus TC-020-002)

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-restart"]`

**Expected Results**:
- Die Abgeschlossen-Karte verschwindet
- Der MUI-Stepper erscheint, Schritt 1 ist aktiv
- `[data-testid="onboarding-step-welcome"]` ist sichtbar
- Alle Wizard-Felder sind auf Standardwerte zurückgesetzt (Erfahrungsstufe: Einsteiger, kein Kit gewählt)

**Postconditions**:
- Wizard ist auf Schritt 1 zurückgesetzt; `onboarding_state` wird serverseitig zurückgesetzt

**Tags**: [req-020, onboarding, neustart, zustandswechsel]

---

## TC-020-005: Wizard überspringen über "Überspringen"-Link

**Requirement**: REQ-020 §5.3 — Skip: "Überspringen"-Link auf Schritt 1
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Wizard ist auf Schritt 1 (TC-020-001)

**Test Steps**:
1. Nutzer klickt auf `[data-testid="skip-onboarding"]`

**Expected Results**:
- Während der Verarbeitung ist der Button deaktiviert und ein Lade-Indikator sichtbar
- Nach Abschluss wird der Nutzer zur Route `/pflanzen/plant-instances` weitergeleitet
- Eine Informations-Benachrichtigung erscheint (SnackBar) mit dem Text aus dem i18n-Schlüssel `pages.onboarding.skip`
- Die Weiterleitungs-URL ändert sich zu `/pflanzen/plant-instances`

**Postconditions**:
- `onboarding_state.skipped == true`, `experience_level == 'beginner'`

**Tags**: [req-020, onboarding, skip, navigation]

---

## TC-020-006: Wizard-Resume nach Browser-Schließen

**Requirement**: REQ-020 §6 (Technisch) — "OnboardingState wird bei jedem Wizard-Schritt gespeichert"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat in einer vorherigen Session Schritt 3 erreicht, Kit "fensterbank-kraeuter" gewählt, Standortname "Mein Kräutergarten" eingegeben und den Browser geschlossen
- `onboarding_state.wizard_step == 3`, `selected_kit_id == "fensterbank-kraeuter"`, `site_name == "Mein Kräutergarten"`

**Test Steps**:
1. Nutzer öffnet Browser neu und navigiert zur Route `/onboarding`

**Expected Results**:
- Wizard öffnet sich direkt auf Schritt 3 (Standort einrichten)
- Das Feld `[data-testid="site-name-field"]` enthält den Wert "Mein Kräutergarten"
- Der MUI-Stepper zeigt Schritt 3 als aktiv an; die Schritte 1 und 2 sind als abgeschlossen markiert
- Die Schaltfläche `[data-testid="onboarding-back"]` ist sichtbar und aktiv

**Postconditions**:
- Nutzer kann den Wizard ab Schritt 3 fortsetzen

**Tags**: [req-020, onboarding, resume, wizard-fortschritt, zustandswechsel]

---

## Gruppe B — Schritt 1: Erfahrungsstufe & Smart-Home

---

## TC-020-007: Erfahrungsstufe "Einsteiger" auswählen — Default-Zustand

**Requirement**: REQ-020 §5.2 — Schritt 1: Begrüßung & Erfahrungsstufe
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Wizard befindet sich auf Schritt 1

**Test Steps**:
1. Nutzer beobachtet die initiale Darstellung

**Expected Results**:
- Die Karte `[data-testid="experience-beginner"]` ist ausgewählt (primärfarbener Rahmen, fettes Label)
- Die Karten `[data-testid="experience-intermediate"]` und `[data-testid="experience-expert"]` sind nicht ausgewählt
- Der Smart-Home-Toggle-Bereich ist NICHT sichtbar (bei Einsteiger wird der Toggle nicht angezeigt)
- Die Schaltfläche `[data-testid="onboarding-next"]` ist aktiv (canProceed == true für Schritt 1)

**Postconditions**:
- Keine Zustandsänderung

**Tags**: [req-020, schritt-1, experience-level, beginner, smart-home]

---

## TC-020-008: Erfahrungsstufe "Fortgeschritten" auswählen — Smart-Home-Toggle erscheint

**Requirement**: REQ-020 §5.2 — Schritt 1: Smart-Home-Toggle bei intermediate/expert
REQ-020 v1.6 — Smart-Home-Deaktivierung
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 1

**Test Steps**:
1. Nutzer klickt auf `[data-testid="experience-intermediate"]`

**Expected Results**:
- Die Karte "Fortgeschritten" ist jetzt ausgewählt (primärfarbener Rahmen)
- Die Karte "Einsteiger" ist nicht mehr ausgewählt
- Unterhalb der drei Erfahrungsstufen-Karten erscheint ein Abschnitt mit dem Smart-Home-Toggle
- Der Toggle `[data-testid="smart-home-toggle"]` ist sichtbar und zeigt den Zustand "Aus" (deaktiviert)
- Ein Hinweistext erklärt den deaktivierten Zustand ("Kein Problem! Du kannst alles manuell erfassen.")
- Der MUI-Stepper zeigt weiterhin die korrekte Schrittzahl an (abhängig von Erfahrungsstufe — intermediate fügt den "Pflanzen"-Schritt hinzu)

**Postconditions**:
- `experience_level == 'intermediate'`, `smart_home_enabled == false`

**Tags**: [req-020, schritt-1, experience-level, intermediate, smart-home-toggle, zustandswechsel]

---

## TC-020-009: Erfahrungsstufe "Experte" auswählen — Smart-Home-Toggle erscheint

**Requirement**: REQ-020 §5.2 — Schritt 1: Smart-Home-Toggle bei intermediate/expert
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 1

**Test Steps**:
1. Nutzer klickt auf `[data-testid="experience-expert"]`

**Expected Results**:
- Die Karte "Experte" ist ausgewählt (primärfarbener Rahmen)
- Smart-Home-Toggle `[data-testid="smart-home-toggle"]` ist sichtbar
- Hinweistext im deaktivierten Zustand ist sichtbar

**Postconditions**:
- `experience_level == 'expert'`, `smart_home_enabled == false`

**Tags**: [req-020, schritt-1, experience-level, expert, smart-home-toggle]

---

## TC-020-010: Smart-Home-Toggle aktivieren und Hinweistext wechselt

**Requirement**: REQ-020 v1.6 §6 — Smart-Home-Toggle Persistierung
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 1, Erfahrungsstufe "Fortgeschritten" oder "Experte" ist gewählt, Smart-Home-Toggle ist sichtbar und deaktiviert

**Test Steps**:
1. Nutzer klickt auf den Toggle `[data-testid="smart-home-toggle"]`

**Expected Results**:
- Der Toggle wechselt in den "An"-Zustand (visuell als aktiviert dargestellt)
- Der Hinweistext ändert sich auf den aktivierten Text ("Sensoren, Aktoren und Live-Messwerte werden im System verfügbar.")
- Die Schaltfläche `[data-testid="onboarding-next"]` bleibt aktiv

**Postconditions**:
- `smart_home_enabled == true` im lokalen Wizard-Zustand

**Tags**: [req-020, schritt-1, smart-home-toggle, zustandswechsel, v1.6]

---

## TC-020-011: Von "Fortgeschritten" zurück zu "Einsteiger" — Smart-Home-Toggle verschwindet

**Requirement**: REQ-020 v1.6 §6 — "Bei beginner wird der Toggle nicht angezeigt"
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 1, Erfahrungsstufe "Fortgeschritten" ist gewählt, Toggle ist sichtbar

**Test Steps**:
1. Nutzer klickt auf `[data-testid="experience-beginner"]`

**Expected Results**:
- Die Karte "Einsteiger" ist ausgewählt
- Der Smart-Home-Toggle-Bereich ist vollständig ausgeblendet

**Postconditions**:
- `experience_level == 'beginner'`, `smart_home_enabled` wird intern auf `false` zurückgesetzt

**Tags**: [req-020, schritt-1, smart-home-toggle, beginner, zustandswechsel]

---

## TC-020-012: Dynamische Stepper-Anzahl bei Erfahrungsstufe Einsteiger

**Requirement**: REQ-020 §5.2 — Dynamische Steps (beginner: keine Pflanzen-/Nährstoffplan-Schritte)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 1, Erfahrungsstufe "Einsteiger" ist aktiv

**Test Steps**:
1. Nutzer beobachtet den MUI-Stepper (Desktop-Ansicht)

**Expected Results**:
- Der Stepper zeigt 5 Schritte an: Erfahrung, Szenario, Favoriten, Standort, Zusammenfassung
- Kein "Pflanzen"-Schritt und kein "Nährstoffpläne"-Schritt sind sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, stepper, dynamische-schritte, beginner]

---

## TC-020-013: Dynamische Stepper-Anzahl bei Erfahrungsstufe Fortgeschritten

**Requirement**: REQ-020 OnboardingWizard.tsx — wizardSteps-Logik (intermediate adds 'plants' step)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 1

**Test Steps**:
1. Nutzer klickt auf `[data-testid="experience-intermediate"]`
2. Nutzer beobachtet den MUI-Stepper

**Expected Results**:
- Der Stepper zeigt 6 Schritte an: Erfahrung, Szenario, Favoriten, Standort, Pflanzen, Zusammenfassung
- Der "Nährstoffpläne"-Schritt ist noch nicht sichtbar (erscheint nur wenn Species-Favoriten vorhanden)

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, stepper, dynamische-schritte, intermediate]

---

## Gruppe C — Schritt 2: Starter-Kit-Auswahl

---

## TC-020-014: Starter-Kit-Liste wird angezeigt — Happy Path

**Requirement**: REQ-020 §5.2 — Schritt 2: Anbau-Szenario wählen
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 1; Nutzer klickt auf "Weiter"

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-next"]`

**Expected Results**:
- Das Element `[data-testid="onboarding-step-kit"]` ist sichtbar
- Ein Grid mit Kit-Karten ist sichtbar (mindestens 5 Kits gemäß Akzeptanzkriterium)
- Jede Karte zeigt: Icon/Name, Kurzbeschreibung, Standorttyp-Chip, Pflanzenanzahl-Chip, Schwierigkeits-Chip (farbkodiert: grün=Einsteiger, gelb=Fortgeschritten, rot=Fortgeschritten+)
- Karten mit toxischen Pflanzen zeigen einen gelben "Toxizitätswarnung"-Chip (z.B. "Zimmerpflanzen")
- Kein Kit ist initial ausgewählt
- Hinweis "Kit-Auswahl ist optional" ist unter dem Grid sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-2, starter-kit, listenansicht]

---

## TC-020-015: Starter-Kit "Fensterbank-Kräuter" auswählen — Auto-Befüllung

**Requirement**: REQ-020 OnboardingWizard.tsx — handleKitSelect: Auto-populate site type + name + plant configs
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Wizard befindet sich auf Schritt 2

**Test Steps**:
1. Nutzer klickt auf `[data-testid="kit-fensterbank-kraeuter"]`

**Expected Results**:
- Die Karte "Fensterbank-Kräuter" ist ausgewählt (primärfarbener Rahmen, fettes Label)
- Das Kit zeigt die Eigenschaften: Standorttyp "Fensterbank", Pflanzenanzahl 5, Schwierigkeitsgrad "Einsteiger"
- (Intern für spätere Schritte: site_type wird auf 'windowsill' vorbelegt, site_name auf Standardwert für Fensterbank)

**Postconditions**:
- `selected_kit_id == 'fensterbank-kraeuter'`; Standorttyp und Pflanzkonfigurationen sind vorbelegt

**Tags**: [req-020, schritt-2, starter-kit, auto-befuellung, happy-path]

---

## TC-020-016: Starter-Kit "Zimmerpflanzen" — Toxizitätswarnung sichtbar

**Requirement**: REQ-020 §6 — "Starter-Kits mit toxischen Pflanzen zeigen toxicity_warning an"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 2

**Test Steps**:
1. Nutzer sucht die Karte für das Kit "Zimmerpflanzen"

**Expected Results**:
- Die Karte `[data-testid="kit-zimmerpflanzen"]` zeigt einen Chip "Toxizitätswarnung" (gelb/warning color)
- Das Kit "Zimmerpflanzen (haustierfreundlich)" (`[data-testid="kit-zimmerpflanzen-haustierfreundlich"]`) zeigt KEINEN Toxizitätswarnung-Chip

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-2, toxizitaet, warnung]

---

## TC-020-017: Starter-Kit abwählen durch erneutes Klicken

**Requirement**: REQ-020 StarterKitStep.tsx — Toggle-Logik: onSelect(isSelected ? null : kit.kit_id)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 2, Kit "fensterbank-kraeuter" ist ausgewählt

**Test Steps**:
1. Nutzer klickt erneut auf `[data-testid="kit-fensterbank-kraeuter"]`

**Expected Results**:
- Die Karte "Fensterbank-Kräuter" ist nicht mehr ausgewählt (normaler Rahmen)
- Kein Kit ist ausgewählt

**Postconditions**:
- `selected_kit_id == null`

**Tags**: [req-020, schritt-2, starter-kit, abwaehlen]

---

## TC-020-018: Kit "Indoor Growzelt" — Schwierigkeitsbadge "Fortgeschritten" (orange)

**Requirement**: REQ-020 StarterKitStep.tsx — Chip colorierungslogik
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 2

**Test Steps**:
1. Nutzer sucht die Karte `[data-testid="kit-indoor-growzelt"]`

**Expected Results**:
- Der Schwierigkeits-Chip zeigt "Fortgeschritten" mit der Farbe "warning" (orange/gelb)
- Die Karte zeigt Standorttyp "Growzelt" und enthält einen Toxizitätswarnung-Chip

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-2, starter-kit, schwierigkeit, growzelt]

---

## TC-020-019: Kein verfügbares Starter-Kit für eingeschränkten Tenant (Szenario G)

**Requirement**: REQ-020 §1.2 — Szenario G: Kein Kit verfügbar
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Enterprise-Tenant aktiv; kein globales Starter-Kit hat Species, die dem aktuellen Tenant per `tenant_has_access` zugewiesen sind
- Wizard befindet sich auf Schritt 2

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-kit"]`

**Expected Results**:
- Das Kit-Grid ist leer — keine Kit-Karten werden angezeigt
- Ein Hinweistext ist sichtbar: "Für diesen Garten sind keine vorkonfigurierten Szenarien verfügbar. Du kannst deine Pflanzen manuell einrichten." (o.ä.)
- Eine prominente "Eigenes Setup"-Option ist sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-2, tenant-scoping, kein-kit, fehlermeldung, szenario-g]

---

## Gruppe D — Schritt 3: Favoriten-Auswahl

---

## TC-020-020: Favoriten-Schritt — Kit-Species sind vorausgewählt

**Requirement**: REQ-020 OnboardingWizard.tsx — handleKitSelect: dispatch(setFavoriteSpecies(kit.species_keys))
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Wizard befindet sich auf Schritt 1; Nutzer wählt "Fensterbank-Kräuter" auf Schritt 2; Nutzer klickt "Weiter"

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-next"]` auf Schritt 2

**Expected Results**:
- Das Element `[data-testid="onboarding-step-favorites"]` ist sichtbar
- Die Anzeige "X Favoriten ausgewählt" zeigt 5 (Anzahl der Species im Kit "fensterbank-kraeuter")
- Die Kit-Species sind als Favoriten markiert (gelber Rahmen + Stern-Icon an den Tiles)
- Jede Tile der Kit-Species zeigt einen "Im Kit"-Badge (primärfarbener Chip)
- Eine Suchfeld `[data-testid="favorites-search"]` ist sichtbar
- Alle verfügbaren Species werden als Grid angezeigt (Kit-Species ganz oben sortiert)

**Postconditions**:
- Favoriten-Status der Kit-Species ist vorausgewählt

**Tags**: [req-020, schritt-3, favoriten, vorauswahl, happy-path]

---

## TC-020-021: Favoriten-Tile — Toggle einzelner Species

**Requirement**: REQ-020 §5.2 — Schritt 4: Favoriten-Toggle (Stern-Icon) pro Species
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 3 (Favoriten); Kit "fensterbank-kraeuter" ist gewählt; Basilikum ist vorausgewählt

**Test Steps**:
1. Nutzer klickt auf die Tile `[data-testid="favorite-tile-species/ocimum-basilicum"]`
2. Nutzer klickt erneut auf dieselbe Tile

**Expected Results**:
- Nach Schritt 1: Tile wechselt auf nicht-favorisiert (normaler Rahmen, kein Stern-Icon); Zähler "X Favoriten" verringert sich um 1
- Nach Schritt 2: Tile wechselt zurück auf favorisiert (gelber Rahmen, Stern-Icon); Zähler erhöht sich um 1

**Postconditions**:
- Favoriten-Status ist nach zweifachem Toggle auf ursprünglichem Wert

**Tags**: [req-020, schritt-3, favoriten, toggle, zustandswechsel]

---

## TC-020-022: Favoriten-Suche filtert Species-Liste

**Requirement**: REQ-020 FavoriteSpeciesStep.tsx — Suchfeld-Filterung nach scientific_name und common_names
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 3 (Favoriten); alle Species sind geladen

**Test Steps**:
1. Nutzer gibt "Basil" in das Feld `[data-testid="favorites-search"]` ein

**Expected Results**:
- Die Species-Liste filtert sich und zeigt nur Einträge, die "Basil" im wissenschaftlichen Namen oder im Trivialnamen enthalten (z.B. Basilikum / Ocimum basilicum)
- Nicht passende Species werden ausgeblendet

**Test Steps** (Fortsetzung — Kein-Ergebnis-Fall):
2. Nutzer löscht den Inhalt und gibt "xyznotexistent" ein

**Expected Results (Fortsetzung)**:
- Ein Leerzustand wird angezeigt mit dem Text aus i18n-Schlüssel `pages.onboarding.favorites.noResults`

**Postconditions**:
- Suchfeld-Eingabe hat keinen Einfluss auf die Favoriten-Selektion

**Tags**: [req-020, schritt-3, favoriten, suche, listenansicht]

---

## TC-020-023: Favoriten-Schritt ohne Kit — Kein Badge auf Species

**Requirement**: REQ-020 FavoriteSpeciesStep.tsx — isFromKit-Badge nur wenn Species im Kit
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 2; kein Kit ist ausgewählt; Nutzer klickt "Weiter"

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-next"]` ohne Kit-Auswahl
2. Nutzer beobachtet Schritt 3 (Favoriten)

**Expected Results**:
- Das Favoriten-Grid zeigt alle Species ohne "Im Kit"-Badge
- Keine Species sind vorausgewählt (Zähler: "0 Favoriten ausgewählt")

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-3, favoriten, kein-kit, badge]

---

## TC-020-024: Bereits vorhandene Favoriten-Markierung aus vorherigen Sessions

**Requirement**: REQ-020 FavoriteSpeciesStep.tsx — existingFavoriteKeys: "existingBadge" (grüner Chip)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat in einer früheren Session außerhalb des Wizards bereits Basilikum als Favorit markiert
- Wizard befindet sich auf Schritt 3 (Favoriten)

**Test Steps**:
1. Nutzer beobachtet die Tile von Basilikum

**Expected Results**:
- Die Tile von Basilikum zeigt einen grünen "Bereits favorisiert"-Badge (Chip mit `color="success"`)

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-3, favoriten, vorhandene-favoriten, badge]

---

## Gruppe E — Schritt 4: Standort einrichten

---

## TC-020-025: Standort-Schritt — Auto-Befüllung aus Kit-Auswahl

**Requirement**: REQ-020 §5.2 — Schritt 3: Standort einrichten; handleKitSelect setzt siteType + siteName
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Kit "fensterbank-kraeuter" ist gewählt (site_type: windowsill); Wizard hat Schritt 3 erreicht

**Test Steps**:
1. Nutzer navigiert zu Schritt 4 (Standort) durch Klick auf "Weiter"

**Expected Results**:
- Das Element `[data-testid="onboarding-step-site"]` ist sichtbar
- Die "Neue Standort"-Karte (`[data-testid="site-option-new"]`) ist ausgewählt (primärfarbener Rahmen)
- Das Textfeld `[data-testid="site-name-field"]` zeigt den automatisch generierten Standardnamen (z.B. "Meine Fensterbank" für Fensterbank-Kits)
- Der Standorttyp-Selektor `[data-testid="site-type-select"]` zeigt "Fensterbank"
- Kein Wasserquellen-Abschnitt ist sichtbar (Erfahrungsstufe = Einsteiger)

**Postconditions**:
- Standortdaten sind aus Kit vorbelegt

**Tags**: [req-020, schritt-4, standort, auto-befuellung, happy-path]

---

## TC-020-026: Standortname manuell ändern

**Requirement**: REQ-020 SiteSetupStep.tsx — handleSiteNameChange setzt siteNameManuallyChanged=true
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Wizard befindet sich auf Schritt 4 (Standort); Standardname ist vorbelegt

**Test Steps**:
1. Nutzer klickt in das Feld `[data-testid="site-name-field"]`
2. Nutzer löscht den Inhalt und gibt "Mein Küchenfenster" ein

**Expected Results**:
- Das Feld zeigt "Mein Küchenfenster"
- Wenn der Nutzer jetzt zurückgeht (zu Schritt 2) und ein anderes Kit wählt, bleibt der Standortname "Mein Küchenfenster" (manuelle Änderung wird nicht überschrieben)

**Postconditions**:
- `site_name == "Mein Küchenfenster"`, `siteNameManuallyChanged == true`

**Tags**: [req-020, schritt-4, standort, manueller-name, formvalidierung]

---

## TC-020-027: Standorttyp ändern

**Requirement**: REQ-020 §5.2 — Schritt 3: Standorttyp als Icon-Auswahl (vorbelegt aus Kit, änderbar)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Wizard befindet sich auf Schritt 4 (Standort); Standorttyp "Fensterbank" ist vorbelegt

**Test Steps**:
1. Nutzer klickt auf `[data-testid="site-type-select"]`
2. Nutzer wählt "Balkon" aus dem Dropdown

**Expected Results**:
- Der Selektor zeigt "Balkon"
- Die "Neue Standort"-Karte aktualisiert den Untertitel auf "Balkon"

**Postconditions**:
- `siteType == 'balcony'`

**Tags**: [req-020, schritt-4, standort, standorttyp]

---

## TC-020-028: Wasserquellen-Abschnitt bei Einsteiger ausgeblendet

**Requirement**: REQ-020 §5.2 — "Optionaler Abschnitt Dein Wasser: nur ab Erfahrungsstufe intermediate"
REQ-020 §6 — Akzeptanzkriterium: "Optionaler Wasserabschnitt bei beginner ausgeblendet"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 4 (Standort); Erfahrungsstufe ist "Einsteiger"

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-site"]`

**Expected Results**:
- Der Abschnitt "Dein Wasser" ist nicht sichtbar
- Das Textfeld `[data-testid="onboarding-tap-ec"]` ist nicht im DOM
- Das Textfeld `[data-testid="onboarding-tap-ph"]` ist nicht im DOM
- Der Toggle `[data-testid="onboarding-ro-toggle"]` ist nicht im DOM

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-4, wasser, beginner, req-021, versteckt]

---

## TC-020-029: Wasserquellen-Abschnitt bei Fortgeschritten sichtbar und bedienbar

**Requirement**: REQ-020 §5.2 — "Dein Wasser" bei intermediate
REQ-020 §6 — Wizard-Abschluss mit Wasserdaten erstellt Site.water_source
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Wizard befindet sich auf Schritt 4 (Standort); Erfahrungsstufe ist "Fortgeschritten"

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-site"]`
2. Nutzer gibt "0.4" in das Feld `[data-testid="onboarding-tap-ec"]` ein
3. Nutzer gibt "7.2" in das Feld `[data-testid="onboarding-tap-ph"]` ein
4. Nutzer aktiviert den Toggle `[data-testid="onboarding-ro-toggle"]`

**Expected Results**:
- Schritt 1: Der Abschnitt "Dein Wasser" ist sichtbar; alle drei Felder sind vorhanden
- Schritt 2: Das EC-Feld zeigt "0.4" mit der Einheit "mS/cm" rechts
- Schritt 3: Das pH-Feld zeigt "7.2"
- Schritt 4: Der RO-Toggle zeigt den aktivierten Zustand

**Postconditions**:
- `tap_water_ec_ms == 0.4`, `tap_water_ph == 7.2`, `has_ro_system == true`

**Tags**: [req-020, schritt-4, wasser, intermediate, tap-water-ec, ro-system, formvalidierung]

---

## TC-020-030: EC-Wert Grenzwert-Validierung im Browser

**Requirement**: REQ-020 §3 — OnboardingWizardRequest: tap_water_ec_ms Field(ge=0, le=2.0)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Wizard befindet sich auf Schritt 4 (Standort); Erfahrungsstufe ist "Fortgeschritten"

**Test Steps**:
1. Nutzer gibt "2.5" in das Feld `[data-testid="onboarding-tap-ec"]` ein

**Expected Results**:
- Das HTML-Inputfeld verhindert Werte > 2.0 (inputProps max=2.0)
- Alternativ: Der Wert wird auf 2.0 geclampt
- Kein Fehlertext aus Servervalidierung erscheint, da Browser-Validierung greift

**Test Steps** (Fortsetzung):
2. Nutzer gibt "-1" in das EC-Feld ein

**Expected Results (Fortsetzung)**:
- Das HTML-Inputfeld verhindert Werte < 0 (inputProps min=0)

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-4, wasser, grenzwert, ec-validierung, formvalidierung]

---

## TC-020-031: Vorhandenen Standort auswählen statt neuen erstellen

**Requirement**: REQ-020 SiteSetupStep.tsx — existingSites-Auswahl
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer hat bereits mindestens einen Standort im System (z.B. aus einem früheren Onboarding)
- Wizard befindet sich auf Schritt 4 (Standort)

**Test Steps**:
1. Nutzer beobachtet, dass unterhalb der "Neue Standort"-Karte eine Sektion "Vorhandene Standorte" erscheint
2. Nutzer klickt auf eine der vorhandenen Standort-Karten (z.B. `[data-testid="site-option-{site.key}"]`)

**Expected Results**:
- Die gewählte Standort-Karte erhält einen primärfarbenen Rahmen und ein Checkmark-Icon
- Die "Neue Standort"-Karte verliert ihre Auswahl (normaler Rahmen)
- Die Felder für Standortname und -typ sind ausgeblendet (da vorhandener Standort gewählt)

**Postconditions**:
- `selectedSiteKey == site.key`, Formular für neuen Standort ist nicht sichtbar

**Tags**: [req-020, schritt-4, standort, vorhandener-standort, happy-path]

---

## TC-020-032: Rück-Toggle: Vorhandenen Standort abwählen und neu erstellen

**Requirement**: REQ-020 SiteSetupStep.tsx — Deselect-Logik: onSelectedSiteKeyChange(null)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Ein vorhandener Standort ist in Schritt 4 ausgewählt

**Test Steps**:
1. Nutzer klickt erneut auf denselben vorhandenen Standort
   ODER
   Nutzer klickt auf die "Neue Standort"-Karte

**Expected Results**:
- Die "Neue Standort"-Karte ist wieder ausgewählt (primärfarbener Rahmen)
- Das Formular für Standortname und -typ erscheint wieder

**Postconditions**:
- `selectedSiteKey == null`

**Tags**: [req-020, schritt-4, standort, toggle, zustandswechsel]

---

## Gruppe F — Schritt 5: Pflanzenauswahl (nur intermediate/expert)

---

## TC-020-033: Pflanzen-Schritt — Pflanzenkonfiguration mit Zähler

**Requirement**: REQ-020 §5.2 — Schritt 4: Pflanzenanzahl-Zähler; PlantSelectionStep.tsx
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Erfahrungsstufe ist "Fortgeschritten"; Kit "fensterbank-kraeuter" ist gewählt; Wizard hat Schritt 5 (Pflanzen) erreicht
- Kit-Species sind als Favoriten vorausgewählt

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-plant-selection"]`
2. Nutzer klickt auf `[data-testid="plant-count-plus-species/ocimum-basilicum"]`
3. Nutzer klickt auf `[data-testid="plant-count-plus-species/ocimum-basilicum"]`

**Expected Results**:
- Schritt 1: Jede favorisierte Species hat eine Zeile mit Minus-Button, Zahlenfeld, Plus-Button und (bei count>0) einem Phasenauswahl-Dropdown
- Die Gesamtzahl der Pflanzen wird unten angezeigt
- Schritt 2 + 3: Zähler für Basilikum steigt um je 1; Gesamtzahl aktualisiert sich entsprechend

**Postconditions**:
- Pflanzenkonfiguration ist aktualisiert

**Tags**: [req-020, schritt-5, pflanzen, zaehler, happy-path]

---

## TC-020-034: Pflanzenzähler Grenzwert — Maximum 50

**Requirement**: REQ-020 PlantSelectionStep.tsx — incrementCount: if (current < 50)
REQ-020 §3 — OnboardingWizardRequest: plant_count Field(ge=1, le=50)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Wizard befindet sich auf Schritt 5 (Pflanzen); Basilikum-Zähler ist auf 50

**Test Steps**:
1. Nutzer klickt auf `[data-testid="plant-count-plus-species/ocimum-basilicum"]`

**Expected Results**:
- Der Plus-Button ist deaktiviert (`disabled` Attribut)
- Der Zähler bleibt auf 50

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-5, pflanzen, grenzwert, maximum-50, formvalidierung]

---

## TC-020-035: Pflanzenzähler auf 0 setzen — Konfiguration wird entfernt

**Requirement**: REQ-020 PlantSelectionStep.tsx — updateConfig: if (updated.count > 0) newConfigs.push(updated)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Wizard befindet sich auf Schritt 5; Basilikum-Zähler ist auf 1

**Test Steps**:
1. Nutzer klickt auf `[data-testid="plant-count-minus-species/ocimum-basilicum"]`

**Expected Results**:
- Der Basilikum-Zähler fällt auf 0
- Der Minus-Button wird deaktiviert
- Das Phasenauswahl-Dropdown für Basilikum verschwindet (nur bei count > 0 sichtbar)
- Die Zeile zeigt weiterhin die Species-Information, aber ohne Phasen-Selektor

**Postconditions**:
- Basilikum ist aus den Pflanzenkonfigurationen entfernt

**Tags**: [req-020, schritt-5, pflanzen, null-zaehler, zustandswechsel]

---

## TC-020-036: Anfangsphase für eine Pflanze ändern

**Requirement**: REQ-020 PlantSelectionStep.tsx — Phase-Selektor (germination/seedling/vegetative/flowering)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Wizard befindet sich auf Schritt 5; Basilikum-Zähler ist > 0; Phasen-Selektor ist sichtbar

**Test Steps**:
1. Nutzer klickt auf `[data-testid="plant-phase-select-species/ocimum-basilicum"]`
2. Nutzer wählt "Sämling" (seedling) aus dem Dropdown

**Expected Results**:
- Der Phasen-Selektor zeigt "Sämling"
- Die Auswahl gilt nur für diese Species

**Postconditions**:
- `initial_phase == 'seedling'` für Basilikum

**Tags**: [req-020, schritt-5, pflanzen, anfangsphase, dropdown]

---

## TC-020-037: Schritt Pflanzen ohne Favoriten — Leerzustand

**Requirement**: REQ-020 PlantSelectionStep.tsx — Leerzustand wenn favoriteSpeciesKeys.length === 0
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Erfahrungsstufe "Fortgeschritten"; kein Kit gewählt; keine Favoriten markiert; Wizard auf Schritt 5

**Test Steps**:
1. Nutzer beobachtet `[data-testid="onboarding-step-plant-selection"]`

**Expected Results**:
- Ein Leerzustand-Container ist sichtbar mit dem Text aus `pages.onboarding.plants.noFavorites`
- Keine Pflanzen-Zeilen werden angezeigt

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-5, pflanzen, leerzustand, keine-favoriten]

---

## Gruppe G — Schritt 6: Nährstoffpläne (bedingt, v1.5)

---

## TC-020-038: Nährstoffplan-Schritt erscheint nur bei Favoriten + Erfahrungsstufe intermediate/expert

**Requirement**: REQ-020 §5.2 — "Schritt 5 wird nur angezeigt wenn mindestens eine Species favorisiert"
REQ-020 §6 — "Nährstoffplan-Schritt bedingt"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Erfahrungsstufe "Fortgeschritten"; mindestens eine Species ist als Favorit markiert; Wizard befindet sich auf Schritt 5 (Pflanzen)
- Passende Nährstoffpläne sind im System vorhanden

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-next"]` auf Schritt 5

**Expected Results**:
- Das Element `[data-testid="onboarding-step-nutrient-plans"]` ist sichtbar
- Eine Überschrift "Düngepläne für deine Favoriten" ist sichtbar
- Während des Ladens werden Skeleton-Platzhalter angezeigt
- Nach dem Laden erscheinen Nährstoffplan-Karten
- Der MUI-Stepper hat einen Schritt "Nährstoffpläne" eingefügt

**Postconditions**:
- Nährstoffplan-Schritt ist aktiv

**Tags**: [req-020, schritt-6, naehrstoffplaene, bedingt, happy-path, v1.5]

---

## TC-020-039: Nährstoffplan-Schritt wird übersprungen — Keine Favoriten oder kein Kit mit Plänen

**Requirement**: REQ-020 OnboardingWizard.tsx — wizardSteps: "Only show nutrient plans step if user has favorites"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Erfahrungsstufe "Fortgeschritten"; KEINE Species sind als Favorit markiert; Wizard befindet sich auf Schritt 5 (Pflanzen)

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-next"]` auf Schritt 5

**Expected Results**:
- Der Wizard springt DIREKT zum Zusammenfassungs-Schritt (`[data-testid="onboarding-step-complete"]`)
- Kein Nährstoffplan-Schritt erscheint zwischen Schritt 5 und Zusammenfassung

**Postconditions**:
- Wizard ist auf dem Zusammenfassungs-Schritt

**Tags**: [req-020, schritt-6, naehrstoffplaene, uebersprungen, bedingt]

---

## TC-020-040: Nährstoffplan favorisieren — Cascade-Hinweis sichtbar

**Requirement**: REQ-020 §5.2 — Schritt 5: "Kaskaden-Hinweis (Info-Icon)"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 6 (Nährstoffpläne); mindestens ein Plan ist geladen

**Test Steps**:
1. Nutzer beobachtet den Inhalt unterhalb der Pläne-Liste

**Expected Results**:
- Ein Info-Icon mit Hinweistext ist sichtbar: "Wenn du einen Plan favorisierst, werden die enthaltenen Dünger automatisch zu deinen Favoriten hinzugefügt." (i18n: `pages.onboarding.nutrientPlans.favoriteHint`)
- Jede Plan-Karte zeigt einen Stern-Toggle

**Test Steps** (Fortsetzung):
2. Nutzer klickt auf den Stern-Toggle einer Nährstoffplan-Karte

**Expected Results (Fortsetzung)**:
- Die Karte wechselt in den favorisierten Zustand (gelbes Stern-Icon aktiviert)

**Postconditions**:
- Plan ist als Favorit markiert im lokalen Wizard-Zustand

**Tags**: [req-020, schritt-6, naehrstoffplaene, favorisieren, kaskade, v1.5]

---

## TC-020-041: Nährstoffplan-Schritt — Erfahrungsstufe "Einsteiger" — Reduzierte Darstellung

**Requirement**: REQ-020 §5.2 — "beginner: Nur Plan-Name, Kurzbeschreibung und X Dünger enthalten"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 6 (Nährstoffpläne); Erfahrungsstufe ist "Einsteiger"

**Test Steps**:
1. Nutzer beobachtet die Plan-Karten

**Expected Results**:
- Jede Plan-Karte zeigt: Plan-Name, Kurzbeschreibung, Chip "X Dünger enthalten"
- Keine detaillierte Dünger-Liste (Brand + Produktname) ist sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-6, naehrstoffplaene, beginner, reduzierte-darstellung, req-021]

---

## TC-020-042: Nährstoffplan-Schritt — Erfahrungsstufe "Fortgeschritten" — Volle Darstellung

**Requirement**: REQ-020 §5.2 — "intermediate/expert: Volle Dünger-Detailliste"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf Schritt 6 (Nährstoffpläne); Erfahrungsstufe ist "Fortgeschritten"

**Test Steps**:
1. Nutzer beobachtet die Plan-Karten

**Expected Results**:
- Jede Plan-Karte zeigt die vollständige Dünger-Liste mit Brand und Produktname (z.B. "Plagron Terra Grow", "Plagron Terra Bloom")
- Substrat-Badge ist sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-6, naehrstoffplaene, intermediate, volle-darstellung, req-021]

---

## TC-020-043: Nährstoffplan-Schritt — Leerzustand wenn keine Pläne gefunden

**Requirement**: REQ-020 §5.2 — "Wenn keine passenden Pläne gefunden: Leerzustand"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Wizard befindet sich auf Schritt 6 (Nährstoffpläne); die API liefert keine passenden Pläne zurück

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-nutrient-plans"]`

**Expected Results**:
- Ein Leerzustand ist sichtbar mit Icon und dem Text aus `pages.onboarding.nutrientPlans.noPlans`
- Kein Plan-Grid wird angezeigt

**Postconditions**:
- Kein Zustandswechsel; Nutzer kann ohne Plan-Favorisierung zum nächsten Schritt

**Tags**: [req-020, schritt-6, naehrstoffplaene, leerzustand, fehlermeldung]

---

## Gruppe H — Schritt 7: Zusammenfassung und Abschluss

---

## TC-020-044: Zusammenfassungs-Schritt — Vollständige Darstellung mit Kit und Favoriten

**Requirement**: REQ-020 §5.2 — Schritt 6: Zusammenfassung & Abschluss
REQ-020 §6 — "Favoriten in Zusammenfassung"
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf dem Zusammenfassungs-Schritt
- Kit "fensterbank-kraeuter" ist gewählt; Site-Name "Meine Fensterbank"; 2 Favoriten-Species; 1 Favoriten-Nährstoffplan

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-complete"]`

**Expected Results**:
- Checkmark-Icon ist sichtbar
- Überschrift mit "Überblick über dein Setup" o.ä.
- Abschnitt "Setup" zeigt: Erfahrungsstufe (z.B. "Einsteiger"), Szenario-Name "Fensterbank-Kräuter" mit Schwierigkeits-Badge, Standorttyp und Standortname "Meine Fensterbank", Pflanzenanzahl
- Abschnitt "Pflanzen" zeigt pro aktiver Pflanzenkonfiguration: Species-Name, Anzahl-Chip, Phasen-Chip
- Abschnitt "Favoriten" ist sichtbar: "2 Pflanzen" (Stern-Icon) und "1 Düngeplan" (Wissenschafts-Icon)
- Schaltfläche `[data-testid="onboarding-complete"]` ist sichtbar und aktiv

**Postconditions**:
- Kein Zustandswechsel; Nutzer ist bereit den Wizard abzuschließen

**Tags**: [req-020, schritt-7, zusammenfassung, favoriten, detailansicht]

---

## TC-020-045: Zusammenfassung ohne Favoriten — Favoriten-Abschnitt ausgeblendet

**Requirement**: REQ-020 SummaryStep.tsx — hasFavorites: favoriteSpeciesCount > 0 || favoriteNutrientPlanCount > 0
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Wizard befindet sich auf dem Zusammenfassungs-Schritt; keine Favoriten gesetzt

**Test Steps**:
1. Nutzer beobachtet den Inhalt von `[data-testid="onboarding-step-complete"]`

**Expected Results**:
- Der Abschnitt "Favoriten" ist nicht sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, schritt-7, zusammenfassung, keine-favoriten, ausgeblendet]

---

## TC-020-046: Wizard abschließen — Happy Path (Einsteiger mit Kit)

**Requirement**: REQ-020 §6 — "Nach Wizard-Abschluss existieren mindestens: 1 Site, 1 Location, 1+ PlantInstances, 1 PlantingRun"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Wizard befindet sich auf dem letzten Schritt (Zusammenfassung)
- Kit "fensterbank-kraeuter" gewählt, Erfahrungsstufe "Einsteiger", Site-Name eingegeben

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-complete"]`

**Expected Results**:
- Der Button zeigt einen CircularProgress-Ladeindikator und ist deaktiviert
- Alle anderen Buttons (Zurück, Überspringen) sind ebenfalls deaktiviert (`submitting == true`)
- Nach erfolgreicher Verarbeitung erscheint eine Erfolgs-SnackBar mit dem Text aus `pages.onboarding.complete`
- Nutzer wird zur Route `/pflanzen/plant-instances` weitergeleitet (replace: true)
- Die Pflanzenliste zeigt die neu angelegten Pflanzen (aus dem Starter-Kit)

**Postconditions**:
- `onboarding_state.completed == true`
- Neue Entitäten sind sichtbar in der Pflanzenliste

**Tags**: [req-020, schritt-7, abschluss, weiterleitung, happy-path, critical]

---

## TC-020-047: Wizard-Abschluss schlägt fehl — Fehlerbenachrichtigung

**Requirement**: REQ-020 OnboardingWizard.tsx — handleComplete: catch(err) → handleError(err)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Wizard befindet sich auf dem letzten Schritt; das Netzwerk ist simuliert fehlerhaft (oder Server antwortet mit 500)

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-complete"]`

**Expected Results**:
- Der Ladeindikator erscheint kurz
- Nach dem Fehler: Eine Fehler-SnackBar erscheint (Text entspricht dem Serverfehler oder Netzwerkfehler aus i18n, z.B. "Serverfehler...")
- Der Wizard verbleibt auf dem Zusammenfassungs-Schritt
- Die Schaltfläche `[data-testid="onboarding-complete"]` ist wieder aktiv

**Postconditions**:
- Kein Zustandswechsel; `onboarding_state.completed == false`

**Tags**: [req-020, schritt-7, abschluss, netzwerkfehler, fehlermeldung]

---

## Gruppe I — Navigation und Zurück-Schaltfläche

---

## TC-020-048: Zurück-Navigation zwischen Schritten

**Requirement**: REQ-020 §6 — "Jeder Schritt hat einen Zurück-Button (außer Schritt 1)"
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Wizard befindet sich auf Schritt 3 (Favoriten)

**Test Steps**:
1. Nutzer klickt auf `[data-testid="onboarding-back"]`

**Expected Results**:
- Wizard springt zu Schritt 2 (Starter-Kit-Auswahl)
- Das Element `[data-testid="onboarding-step-kit"]` ist sichtbar
- Das zuvor gewählte Kit ist noch ausgewählt (Zustand bleibt erhalten)

**Test Steps** (Fortsetzung):
2. Nutzer klickt auf `[data-testid="onboarding-back"]` erneut

**Expected Results (Fortsetzung)**:
- Wizard springt zu Schritt 1 (Erfahrungsstufe)
- `[data-testid="onboarding-back"]` ist jetzt nicht mehr sichtbar / deaktiviert (Schritt 1 hat keinen Zurück-Button auf Desktop)

**Postconditions**:
- Wizard ist auf Schritt 1

**Tags**: [req-020, navigation, zurueck-button, schrittnavigation]

---

## TC-020-049: "Weiter"-Button auf letztem Schritt ist durch "Abschließen" ersetzt

**Requirement**: REQ-020 OnboardingWizard.tsx — isLastStep-Logik: "Abschließen" statt "Weiter"
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Wizard befindet sich auf dem letzten Schritt (Zusammenfassung)

**Test Steps**:
1. Nutzer beobachtet die Navigationsbereich

**Expected Results**:
- Die Schaltfläche `[data-testid="onboarding-complete"]` ist sichtbar (mit CheckCircle-Icon)
- Die Schaltfläche `[data-testid="onboarding-next"]` ist NICHT sichtbar
- Die Schaltfläche `[data-testid="onboarding-back"]` ist sichtbar

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, navigation, letzter-schritt, abschliessen-button]

---

## Gruppe J — Moduswechsel-Szenarien

---

## TC-020-050: Szenario A — Upgrade Light→Full mit System-Tenant-Übernahme — Kein Wizard

**Requirement**: REQ-020 §1.1 — Szenario A: Upgrade Light→Full, User übernimmt System-Tenant
REQ-020 §6 — "Upgrade Light→Full (Übernahme): Neuer User erhält OnboardingState mit completed=true"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Light-Modus; System-User hatte Onboarding abgeschlossen (30 Pflanzen)
- Nutzer "Anna" registriert sich im Full-Modus und übernimmt den System-Tenant

**Test Steps**:
1. Anna öffnet die Anwendungs-URL nach der Tenant-Übernahme

**Expected Results**:
- Anna sieht KEINEN Onboarding-Wizard — der Wizard startet NICHT automatisch
- Das Dashboard zeigt die vorhandenen 30 Pflanzen
- Wenn Anna manuell zu `/onboarding` navigiert, sieht sie die Abgeschlossen-Karte (TC-020-002)

**Postconditions**:
- `onboarding_state.completed == true` für Anna

**Tags**: [req-020, moduswechsel, szenario-a, light-full, uebernahme, kein-wizard]

---

## TC-020-051: Szenario B — Upgrade Light→Full ohne Tenant-Übernahme — Wizard startet

**Requirement**: REQ-020 §1.1 — Szenario B: Upgrade Light→Full, User lehnt Übernahme ab
REQ-020 §6 — "Upgrade Light→Full (Ablehnung): Wizard startet automatisch"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Light-Modus; Nutzer "Anna" registriert sich im Full-Modus und LEHNT die Übernahme des System-Tenants ab
- Annas neuer persönlicher Tenant ist leer

**Test Steps**:
1. Anna öffnet die Anwendungs-URL nach der Ablehnung

**Expected Results**:
- Der Onboarding-Wizard startet automatisch
- `[data-testid="onboarding-wizard"]` ist sichtbar
- Wizard befindet sich auf Schritt 1 (Erfahrungsstufe)

**Postconditions**:
- `onboarding_state.completed == false`, `wizard_step == 1`

**Tags**: [req-020, moduswechsel, szenario-b, light-full, ablehnung, wizard-start]

---

## TC-020-052: Tenant-gefiltertes Kit — Nicht zugewiesene Species markiert (Szenario F)

**Requirement**: REQ-020 §1.2 — Szenario F: Kit mit teilweise nicht zugewiesenen Species
REQ-020 §6 — "Nicht verfügbare Species: in Schritt 4 ausgegraut und nicht auswählbar"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Enterprise-Tenant mit eingeschränkter Species-Zuweisung; ein Starter-Kit hat 5 Species, davon sind nur 3 dem Tenant zugewiesen
- Wizard befindet sich auf Schritt 2; das teilweise verfügbare Kit ist sichtbar

**Test Steps**:
1. Nutzer klickt auf das teilweise verfügbare Kit
2. Nutzer navigiert zu Schritt 3 (Favoriten)

**Expected Results**:
- Der `species_count`-Chip auf der Kit-Karte zeigt die verfügbare Anzahl (3), nicht die Gesamt-Anzahl (5)
- Auf Schritt 3 (Favoriten): Die nicht zugewiesenen Species sind ausgegraut und beim Klicken nicht als Favorit markierbar (oder zeigen einen Hinweis "Nicht verfügbar in diesem Garten")

**Postconditions**:
- Nur verfügbare Species sind im Favoriten-Schritt interagierbar

**Tags**: [req-020, tenant-scoping, szenario-f, species-verfuegbarkeit, ausgegraut]

---

## Gruppe K — Responsive Design und mobile Darstellung

---

## TC-020-053: Mobile Darstellung — MobileStepper statt Stepper

**Requirement**: REQ-020 §5.4 — Responsive Design: Mobile (< 768px): MobileStepper mit Dot-Indikator
REQ-020 OnboardingWizard.tsx — isMobile useMediaQuery
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Browser-Viewport auf < 600px eingestellt (Mobile Breakpoint in MUI)
- Wizard befindet sich auf Schritt 1

**Test Steps**:
1. Nutzer beobachtet die Darstellung des Wizards

**Expected Results**:
- Der MUI `Stepper`-Komponent (Desktop) ist NICHT sichtbar
- Ein mobiler Schritt-Indikator erscheint (Text: "Schritt X von Y — Schrittname")
- Navigation erfolgt über `MobileStepper` mit Dot-Indikatoren und Pfeil-Buttons
- Ein "Überspringen"-Link erscheint unterhalb des MobileSteppers

**Postconditions**:
- Kein Zustandswechsel

**Tags**: [req-020, responsive, mobile, stepper, navigation]

---

## Abdeckungsmatrix

| Spec-Abschnitt | Abgedeckte Test Cases |
|---|---|
| §1.1 Szenarien A–E (Moduswechsel) | TC-020-050, TC-020-051 |
| §1.2 Szenario F–G (Tenant-Scoping) | TC-020-019, TC-020-052 |
| §5.2 Schritt 1 — Erfahrungsstufe | TC-020-007 bis TC-020-013 |
| §5.2 Schritt 2 — Smart-Home-Toggle (v1.6) | TC-020-008 bis TC-020-011 |
| §5.2 Schritt 2 — Starter-Kit-Auswahl | TC-020-014 bis TC-020-018 |
| §5.2 Schritt 3 — Favoriten (v1.5) | TC-020-020 bis TC-020-024 |
| §5.2 Schritt 4 — Standort einrichten | TC-020-025 bis TC-020-032 |
| §5.2 Schritt 5 — Pflanzenauswahl (intermediate/expert) | TC-020-033 bis TC-020-037 |
| §5.2 Schritt 6 — Nährstoffpläne (bedingt, v1.5) | TC-020-038 bis TC-020-043 |
| §5.2 Schritt 7 — Zusammenfassung & Abschluss | TC-020-044 bis TC-020-047 |
| §5.3 Wizard-Trigger (Erststart, Wiederaufruf, Skip) | TC-020-001 bis TC-020-006 |
| §5.4 Responsive Design | TC-020-053 |
| §6 Akzeptanzkriterien — Navigation (Zurück/Weiter) | TC-020-048, TC-020-049 |
| §6 Akzeptanzkriterien — Netzwerkfehler beim Abschluss | TC-020-047 |
| §6 Akzeptanzkriterien — Wasserquellen (REQ-020 v1.1) | TC-020-028 bis TC-020-030 |

### Nicht abgedeckte Bereiche (offene Punkte)

- REQ-020 Szenario C/D/E (Downgrade Full→Light): Kein UI-Test formulierbar ohne REQ-027-Implementierung (Admin-UI für Moduswechsel)
- REQ-020 §5.2 "Konfetti-Animation nach Abschluss": Optionales Feature, kein Akzeptanzkriterium
- REQ-020 §6 "Wizard in weniger als 3 Minuten abschließbar": Performance-Test (nicht E2E)
- REQ-020 §5.5 i18n-Schlüssel für EN-Locale: Erfordert separate i18n-Testdurchläufe
