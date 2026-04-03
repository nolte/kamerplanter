---
req_id: REQ-006
title: Modulare Aufgabenplanung & Benutzerdefinierte Workflows
category: Prozessmanagement
test_count: 75
coverage_areas:
  - Task-Queue (Aufgabenliste)
  - Task-Detailseite (CRUD, Status, Tabs)
  - Aufgabe erstellen (TaskCreateDialog)
  - Workflow-Template-Liste
  - Workflow-Detailseite
  - Workflow instanziieren
  - Workflow erstellen (benutzerdefiniert)
  - Activity Plan Übersicht
  - Checkliste & Teilschritte
  - Tags & Kategorisierung
  - Bewertungen nach Abschluss
  - Timer-Funktion (W-006)
  - Wiederkehrende Aufgaben (Recurrence)
  - Batch-Aktionen (Bulk-Select)
  - Foto-Upload-Enforcement
  - Kommentare & Änderungshistorie
  - HST-Validierung (High-Stress-Training)
  - Autoflower-Guard
  - Recovery-Timer & Canopy-Metriken
  - Dormant-Status & Phasengebundene Tasks
  - Dependency-Ketten & Auto-Rescheduling
  - Phänologische Ereignisse & Seasonal-Trigger
  - Phänologischer Trigger im Task-Template-Dialog konfigurieren
  - Gießplan-Tasks (Watering-Integration)
generated: 2026-04-02
version: "3.0"
---

# Testfälle: REQ-006 — Modulare Aufgabenplanung & Benutzerdefinierte Workflows

## Übersicht

Dieses Dokument enthält alle End-to-End-Testfälle für REQ-006 aus der Perspektive des Nutzers im Browser. Alle Testschritte beschreiben Browser-Aktionen (klicken, tippen, navigieren). Alle erwarteten Ergebnisse beschreiben, was der Nutzer auf dem Bildschirm sieht.

**Routen:**
- Task-Queue: `/aufgaben/queue`
- Task-Detailseite: `/aufgaben/tasks/:key`
- Workflow-Template-Liste: `/aufgaben/workflows`
- Workflow-Detailseite: `/aufgaben/workflows/:key`
- Activity Plan Übersicht: `/aufgaben/activity-plans`

---

## Gruppe 1: Task-Queue — Aufgabenübersicht

### TC-006-001: Task-Queue aufrufen — Leerer Zustand

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege
**Priorität**: High
**Kategorie**: Listenansicht / Leerer Zustand

**Vorbedingungen**:
- Nutzer ist eingeloggt und einem Tenant zugewiesen
- Keine Tasks vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`

**Erwartetes Ergebnis**:
- Seite lädt und zeigt Seitenüberschrift (Task-Queue)
- Illustration (`kamiTasks`) und leere Zustandsmeldung werden angezeigt
- Button "Aufgabe erstellen" ist sichtbar und klickbar
- Keine Fehlermeldung

**Nachbedingungen**: Seite im leeren Zustand

**Tags**: [req-006, task-queue, leer, navigation]

---

### TC-006-002: Task-Queue — Aufgaben nach Dringlichkeit gruppiert

**Anforderung**: REQ-006 §2 AQL — Task-Queue mit Priorisierung
**Priorität**: Critical
**Kategorie**: Listenansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mind. je eine Aufgabe mit Status `pending` in den Gruppen: überfällig, heute fällig, diese Woche, in der Zukunft

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer wartet bis Ladevorgang abgeschlossen ist

**Erwartetes Ergebnis**:
- Tasks sind in Abschnitten gruppiert: "Überfällig" (roter Rand), "Heute" (gelb/orange), "Diese Woche" (blau), "Zukunft" (grau)
- Überfällige Tasks werden mit roter Umrandung hervorgehoben
- Jede Task-Karte zeigt: Name, Kategorie-Badge, Prioritäts-Badge, relatives Fälligkeitsdatum (z.B. "3d überfällig", "Heute", "Morgen")
- Sortierung: Kritische + überfällige Tasks erscheinen zuerst

**Tags**: [req-006, task-queue, dringlichkeit, gruppierung]

---

### TC-006-003: Task-Queue — Filterung nach Kategorie

**Anforderung**: REQ-006 §6 Akzeptanzkriterien — Listenansicht-Filter
**Priorität**: High
**Kategorie**: Filter / Listenansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Tasks verschiedener Kategorien vorhanden (z.B. `training`, `feeding`, `maintenance`)

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer wählt im Kategorie-Dropdown den Wert "Training" aus

**Erwartetes Ergebnis**:
- Nur Aufgaben der Kategorie "Training" werden angezeigt
- Alle anderen Kategorien werden ausgeblendet
- Wenn keine passenden Tasks vorhanden: leere Zustandsmeldung erscheint
- Filter bleibt beim Seitenwechsel in der URL erhalten

**Tags**: [req-006, task-queue, filter, kategorie]

---

### TC-006-004: Task-Queue — Filterung nach Pflanze

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege
**Priorität**: Medium
**Kategorie**: Filter / Listenansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mehrere PlantInstances vorhanden, jede mit mindestens einer Task

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer wählt im Pflanzen-Filter (Autocomplete) eine Pflanze aus

**Erwartetes Ergebnis**:
- Nur Tasks der ausgewählten Pflanze werden angezeigt
- Pflanzennamen-Chip erscheint im Filter als aktiv
- Button "Filter löschen" (X-Icon) ist sichtbar zum Zurücksetzen

**Tags**: [req-006, task-queue, filter, pflanze]

---

### TC-006-005: Task-Queue — Quelle-Filter (Tasks vs. Pflegeerinnerungen)

**Anforderung**: REQ-006 §1 / REQ-022 (Pflege-Integration in Task-Queue)
**Priorität**: Medium
**Kategorie**: Filter / Listenansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Sowohl manuelle Tasks (`source: task`) als auch Pflegeerinnerungen (`source: care`) vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf Toggle-Button "Nur Aufgaben"
3. Nutzer klickt auf Toggle-Button "Nur Pflege"
4. Nutzer klickt auf Toggle-Button "Alle"

**Erwartetes Ergebnis**:
- "Nur Aufgaben": Nur manuelle und workflow-generierte Tasks werden angezeigt
- "Nur Pflege": Nur Pflegeerinnerungen (Gießen, Düngen etc.) werden angezeigt
- "Alle": Beide Quellen werden gemeinsam angezeigt
- Toggle-Buttons zeigen aktiven Zustand deutlich an

**Tags**: [req-006, req-022, task-queue, filter, quelle]

---

### TC-006-006: Task-Queue — Task starten (pending → in_progress)

**Anforderung**: REQ-006 §3 — Task-Status-Übergänge
**Priorität**: Critical
**Kategorie**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens eine Task mit Status `pending` vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer sucht eine Task mit Status "Ausstehend"
3. Nutzer klickt auf den "Starten"-Button (Play-Icon) der Task-Karte

**Erwartetes Ergebnis**:
- Erfolgsmeldung "Aufgabe gestartet" erscheint als Snackbar (unten links oder oben)
- Status-Badge der Task wechselt von "Ausstehend" zu "In Bearbeitung" (blau)
- Task bleibt in der Liste sichtbar (sie ist weiterhin offen)

**Nachbedingungen**: Task hat Status `in_progress`

**Tags**: [req-006, task-queue, status, starten, zustandswechsel]

---

### TC-006-007: Task-Queue — Task direkt abschließen (Quick-Complete)

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege
**Priorität**: Critical
**Kategorie**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens eine Task mit Status `pending` vorhanden, die kein Pflicht-Foto erfordert

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf den "Abschließen"-Button (Haken-Icon) der Task-Karte

**Erwartetes Ergebnis**:
- Erfolgsmeldung "Aufgabe abgeschlossen" erscheint als Snackbar
- Task verschwindet aus den aktiven Gruppen (überfällig, heute, diese Woche)
- Wenn "Erledigte Tasks anzeigen" aktiv: Task erscheint mit Status "Erledigt" (grün)

**Nachbedingungen**: Task hat Status `completed`

**Tags**: [req-006, task-queue, status, abschliessen, zustandswechsel]

---

### TC-006-008: Task-Queue — Task überspringen

**Anforderung**: REQ-006 §3 — Task-Status-Übergänge
**Priorität**: Medium
**Kategorie**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens eine Task mit Status `pending` vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf den "Überspringen"-Button (Skip-Icon) einer Task-Karte

**Erwartetes Ergebnis**:
- Erfolgsmeldung erscheint als Snackbar
- Task wechselt zu Status "Übersprungen" oder verschwindet aus der aktiven Liste
- Kein Bestätigungsdialog erforderlich (Quick-Action)

**Nachbedingungen**: Task hat Status `skipped`

**Tags**: [req-006, task-queue, status, ueberspringen, zustandswechsel]

---

### TC-006-009: Task-Queue — Bulk-Modus aktivieren und mehrere Tasks auswählen

**Anforderung**: REQ-006 §6 DoD — Bulk-Aktionen-UI (UI-NFR-010 R-025–R-028)
**Priorität**: High
**Kategorie**: Batch-Aktion

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens 3 Tasks mit Status `pending` vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf "Mehrfachauswahl"-Button zum Aktivieren des Bulk-Modus
3. Nutzer setzt Checkboxen bei 3 Tasks

**Erwartetes Ergebnis**:
- Bulk-Modus wird aktiviert: Checkboxen erscheinen an allen Task-Karten
- Ausgewählte Tasks werden visuell hervorgehoben (z.B. Hintergrundfarbe)
- Aktionsleiste erscheint am unteren Bildschirmrand mit Optionen: "Abschließen", "Überspringen", "Löschen"
- Zähler zeigt die Anzahl ausgewählter Tasks an (z.B. "3 ausgewählt")

**Tags**: [req-006, task-queue, bulk, batch, mehrfachauswahl]

---

### TC-006-010: Task-Queue — Bulk-Abschließen mehrerer Tasks

**Anforderung**: REQ-006 §1 — Batch-Operationen (POST /tasks/batch/status)
**Priorität**: High
**Kategorie**: Batch-Aktion

**Vorbedingungen**:
- Bulk-Modus aktiviert (aus TC-006-009)
- 3 Tasks ausgewählt

**Testschritte**:
1. Nutzer klickt in der Aktionsleiste auf "Abschließen"

**Erwartetes Ergebnis**:
- Alle 3 ausgewählten Tasks wechseln zu Status `completed`
- Erfolgsmeldung erscheint: "X Aufgaben abgeschlossen"
- Tasks verschwinden aus der aktiven Liste
- Bulk-Modus wird deaktiviert

**Nachbedingungen**: 3 Tasks haben Status `completed`

**Tags**: [req-006, task-queue, bulk, batch, abschliessen]

---

### TC-006-011: Task-Queue — Bulk-Löschen mit Bestätigungsdialog

**Anforderung**: REQ-006 §1 — Batch-Operationen (POST /tasks/batch/delete)
**Priorität**: High
**Kategorie**: Batch-Aktion / Dialog

**Vorbedingungen**:
- Bulk-Modus aktiviert
- 2 Tasks mit Status `pending` oder `skipped` ausgewählt

**Testschritte**:
1. Nutzer klickt in der Aktionsleiste auf "Löschen"
2. Bestätigungsdialog erscheint
3. Nutzer klickt "Löschen bestätigen"

**Erwartetes Ergebnis**:
- Nach Schritt 1: Bestätigungsdialog erscheint mit Warnung "2 Aufgaben löschen?" und destructive Styling (roter Button)
- Nach Schritt 3: Tasks werden aus der Liste entfernt
- Erfolgsmeldung erscheint als Snackbar

**Nachbedingungen**: 2 Tasks sind nicht mehr in der Liste

**Tags**: [req-006, task-queue, bulk, loeschen, bestaetigungsdialog]

---

### TC-006-012: Task-Queue — Pflegeerinnerungen generieren

**Anforderung**: REQ-006 / REQ-022 — Pflegeerinnerungen aus CareProfile
**Priorität**: Medium
**Kategorie**: Aktion / Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens ein Plant mit CareProfile vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf "Pflegeerinnerungen generieren"-Button

**Erwartetes Ergebnis**:
- Ladeindikator erscheint während der Generierung
- Bei neuen Erinnerungen: Snackbar "X neue Pflegeerinnerungen erstellt"
- Bei keinen neuen: Snackbar "Keine neuen Erinnerungen fällig"
- Task-Liste wird aktualisiert; neue Care-Reminder erscheinen in der Liste

**Tags**: [req-006, req-022, pflegeerinnerungen, generieren]

---

## Gruppe 2: Task erstellen

### TC-006-013: Neue Aufgabe erstellen — Happy Path

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege (CRUD)
**Priorität**: Critical
**Kategorie**: Happy Path / Dialog

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens eine PlantInstance vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf "Aufgabe erstellen"-Button (+ Icon)
3. Dialog öffnet sich
4. Nutzer gibt im Feld "Name" ein: "Topping vorbereiten"
5. Nutzer wählt im Dropdown "Kategorie": "Training"
6. Nutzer wählt im Datumspicker "Fälligkeit": morgen
7. Nutzer wählt "Priorität": "Hoch"
8. Nutzer wählt im Autocomplete-Feld "Pflanze" eine Pflanze aus
9. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Snackbar erscheint: "Erstellt" oder "Aufgabe erstellt"
- Neue Task "Topping vorbereiten" erscheint in der Task-Queue in der Gruppe "Morgen" mit Prioritäts-Badge "Hoch" und Kategorie-Badge "Training"

**Nachbedingungen**: Neue Task ist in der Liste sichtbar

**Tags**: [req-006, aufgabe-erstellen, dialog, happy-path]

---

### TC-006-014: Aufgabe erstellen — Pflichtfeld "Name" leer gelassen

**Anforderung**: REQ-006 §3 Python-Code — TaskInstance.name min_length=3
**Priorität**: High
**Kategorie**: Formvalidierung

**Vorbedingungen**:
- Dialog "Aufgabe erstellen" ist geöffnet

**Testschritte**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog bleibt geöffnet
- Fehlermeldung unter dem Feld "Name" erscheint (z.B. "Dieses Feld ist erforderlich" oder "Mindestens 1 Zeichen")
- Kein API-Aufruf wird abgesetzt

**Tags**: [req-006, aufgabe-erstellen, formvalidierung, pflichtfeld]

---

### TC-006-015: Aufgabe erstellen — Checkliste mit Teilschritten

**Anforderung**: REQ-006 §1 — Checkliste (Subtasks)
**Priorität**: High
**Kategorie**: Happy Path / Dialog

**Vorbedingungen**:
- Dialog "Aufgabe erstellen" ist geöffnet
- Name "Test-Aufgabe" wurde eingegeben

**Testschritte**:
1. Nutzer gibt in das Checkliste-Eingabefeld "Schritt 1" ein und drückt Enter
2. Nutzer gibt "Schritt 2" ein und drückt Enter
3. Nutzer gibt "Schritt 3" ein und drückt Enter
4. Nutzer klickt auf das Löschen-Icon neben "Schritt 2"
5. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Nach Schritt 1–3: Drei Einträge erscheinen in der Checkliste-Liste unterhalb des Eingabefelds
- Nach Schritt 4: Nur "Schritt 1" und "Schritt 3" verbleiben in der Liste (Nummerierung wird angepasst)
- Nach Schritt 5: Task wird erstellt; in der Detailansicht ist die Checkliste mit 2 Einträgen sichtbar

**Tags**: [req-006, aufgabe-erstellen, checkliste, teilschritte]

---

### TC-006-016: Aufgabe erstellen — Tags hinzufügen (Intermediate)

**Anforderung**: REQ-006 §1 — Tags & freie Kategorisierung
**Priorität**: Medium
**Kategorie**: Happy Path / Dialog / Erfahrungsstufe

**Vorbedingungen**:
- Nutzer hat Erfahrungsstufe "Fortgeschrittener" oder höher
- Dialog "Aufgabe erstellen" ist geöffnet

**Testschritte**:
1. Nutzer scrollt zum Abschnitt "Zuweisung" im Dialog
2. Nutzer gibt im Tags-Feld "dringend" ein und drückt Enter
3. Nutzer gibt "hochbeet-a" ein und drückt Enter
4. Nutzer gibt "mit-luna-besprechen" ein und drückt Enter
5. Nutzer klickt auf Name-Feld und gibt "Test-Tag-Task" ein
6. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Tags erscheinen als Chips im Tags-Feld (z.B. "dringend ×", "hochbeet-a ×", "mit-luna-besprechen ×")
- Jeder Tag kann einzeln durch Klick auf "×" entfernt werden
- Nach dem Erstellen: Task mit allen Tags ist in der Detailansicht abrufbar

**Tags**: [req-006, aufgabe-erstellen, tags, erfahrungsstufe]

---

### TC-006-017: Aufgabe erstellen — Wiederholung mit Cron-Ausdruck (Intermediate)

**Anforderung**: REQ-006 §1 — Wiederkehrende Aufgaben (Recurrence)
**Priorität**: Medium
**Kategorie**: Happy Path / Dialog / Erfahrungsstufe

**Vorbedingungen**:
- Nutzer hat Erfahrungsstufe "Fortgeschrittener" oder höher
- Dialog "Aufgabe erstellen" ist geöffnet, Name eingegeben

**Testschritte**:
1. Nutzer gibt im Feld "Wiederholung (Cron)" ein: `0 8 * * 1` (jeden Montag 08:00)
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog schließt sich, Snackbar erscheint: "Erstellt"
- In der Task-Detailseite ist im Metadaten-Bereich die Wiederholungsregel `0 8 * * 1` angezeigt

**Nachbedingungen**: Wiederkehrende Task ist angelegt

**Tags**: [req-006, aufgabe-erstellen, wiederholung, cron, erfahrungsstufe]

---

### TC-006-018: Aufgabe erstellen — Timer-Dauer und Timer-Label (Intermediate)

**Anforderung**: REQ-006 §1 — Task-Timer & Countdown (W-006)
**Priorität**: Medium
**Kategorie**: Happy Path / Dialog / Erfahrungsstufe

**Vorbedingungen**:
- Nutzer hat Erfahrungsstufe "Fortgeschrittener" oder höher
- Dialog "Aufgabe erstellen" ist geöffnet, Name eingegeben

**Testschritte**:
1. Nutzer gibt im Feld "Timer-Dauer (Sek.)" den Wert `120` ein
2. Nutzer gibt im Feld "Timer-Beschriftung" den Text "Umrühren" ein
3. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog schließt sich, Task wird erstellt
- In der Detailansicht sind Timer-Dauer (120 Sekunden = 2 Minuten) und Timer-Beschriftung "Umrühren" sichtbar
- Timer-UI-Komponente ist in der Detailseite unter "Abschließen"-Tab erreichbar

**Tags**: [req-006, aufgabe-erstellen, timer, w-006, erfahrungsstufe]

---

## Gruppe 3: Task-Detailseite

### TC-006-019: Task-Detailseite aufrufen — Tab-Navigation

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege
**Priorität**: High
**Kategorie**: Navigation / Detailansicht

**Vorbedingungen**:
- Mindestens eine Task mit Status `pending` oder `in_progress` vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf eine Task-Karte (nicht auf einen Action-Button)

**Erwartetes Ergebnis**:
- Browser navigiert zu `/aufgaben/tasks/:key`
- Seitenüberschrift zeigt den Task-Namen
- Bei Status `pending`/`in_progress`: 5 Tabs sichtbar — "Details", "Abschließen", "Kommentare", "Verlauf", "Bearbeiten"
- Bei Status `completed`/`skipped`: 4 Tabs sichtbar — "Details", "Kommentare", "Verlauf", "Bearbeiten"
- Standard-Tab "Details" ist aktiv

**Tags**: [req-006, task-detail, tabs, navigation]

---

### TC-006-020: Task-Detailseite — Details-Tab

**Anforderung**: REQ-006 §3 — TaskInstance Properties
**Priorität**: High
**Kategorie**: Detailansicht

**Vorbedingungen**:
- Task mit allen Feldern vorhanden (Kategorie, Priorität, Fälligkeit, Pflanze, Instruktion, Checkliste)

**Testschritte**:
1. Nutzer öffnet die Detailseite einer Task

**Erwartetes Ergebnis**:
- Details-Tab zeigt:
  - Status-Badge (z.B. "Ausstehend" grau, "In Bearbeitung" blau)
  - Prioritäts-Badge (niedrig/mittel/hoch/kritisch mit Farbe)
  - Kategorie-Badge (z.B. "Training")
  - Fälligkeitsdatum (absolut oder relativ, z.B. "Heute")
  - Pflanzenverweis als verlinkter Text (Klick navigiert zur Pflanzen-Detailseite)
  - Instruktion / Beschreibung (Freitext)
  - Checkliste mit Fortschrittsanzeige "x/y Schritte erledigt" (falls vorhanden)
  - Tags als Chips (falls vorhanden)
  - Timer-Anzeige (falls timer_duration_seconds > 0)

**Tags**: [req-006, task-detail, details-tab, metadaten]

---

### TC-006-021: Task-Detailseite — Checkliste abhaken

**Anforderung**: REQ-006 §1 — Checkliste (Subtasks), Fortschrittsanzeige
**Priorität**: High
**Kategorie**: Zustandswechsel / Detailansicht

**Vorbedingungen**:
- Task mit 3 Checklist-Einträgen vorhanden
- Task hat Status `pending` oder `in_progress`

**Testschritte**:
1. Nutzer öffnet die Task-Detailseite
2. Nutzer klickt die Checkbox von Checklist-Eintrag 1
3. Nutzer klickt die Checkbox von Checklist-Eintrag 2

**Erwartetes Ergebnis**:
- Nach Schritt 2: Eintrag 1 wird als erledigt markiert (durchgestrichen oder Haken), Fortschrittsanzeige wechselt auf "1/3 Schritte erledigt"
- Nach Schritt 3: Fortschrittsanzeige zeigt "2/3 Schritte erledigt"
- Geänderter Zustand wird gespeichert (bleibt nach Seitenaktualisierung bestehen)

**Tags**: [req-006, task-detail, checkliste, abhaken, fortschritt]

---

### TC-006-022: Task-Detailseite — Neuen Checklist-Eintrag hinzufügen

**Anforderung**: REQ-006 §1 — Checkliste: Nutzer können Einträge frei hinzufügen
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Detailansicht

**Vorbedingungen**:
- Task mit vorhandener Checkliste geöffnet

**Testschritte**:
1. Nutzer gibt in das Checkliste-Eingabefeld "Neuer Schritt" ein und drückt Enter (oder klickt "+"-Button)

**Erwartetes Ergebnis**:
- "Neuer Schritt" erscheint als neuer Eintrag am Ende der Checkliste
- Fortschrittsanzeige aktualisiert sich (z.B. "2/4 Schritte erledigt")
- Eingabefeld wird geleert für den nächsten Eintrag

**Tags**: [req-006, task-detail, checkliste, hinzufuegen]

---

### TC-006-023: Task-Detailseite — Timer starten und pausieren

**Anforderung**: REQ-006 §1 — Task-Timer (W-006), Timer-Zustand clientseitig
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Detailansicht / Timer

**Vorbedingungen**:
- Task mit `timer_duration_seconds=120` und `timer_label="Umrühren"` geöffnet
- Task hat Status `in_progress`

**Testschritte**:
1. Nutzer klickt auf den "Starten"-Button im Timer-Widget
2. Nutzer beobachtet den Countdown (ca. 5 Sekunden)
3. Nutzer klickt auf den "Pause"-Button
4. Nutzer klickt erneut auf "Starten" zum Fortsetzen
5. Nutzer klickt auf "Zurücksetzen" (Reset)

**Erwartetes Ergebnis**:
- Nach Schritt 1: Countdown läuft (z.B. 1:59, 1:58 …), Timer-Label "Umrühren" ist angezeigt, Kreis- oder Balken-Fortschritt sichtbar
- Nach Schritt 3: Timer stoppt bei aktuellem Stand (z.B. 1:53)
- Nach Schritt 4: Timer läuft weiter von 1:53
- Nach Schritt 5: Timer zeigt wieder 2:00 (120 Sekunden)
- Zu keinem Zeitpunkt blockiert der Timer das Abschließen der Task

**Tags**: [req-006, task-detail, timer, w-006, countdown]

---

### TC-006-024: Task-Detailseite — Aufgabe abschließen mit Bewertung

**Anforderung**: REQ-006 §1 — Bewertungen nach Abschluss (difficulty_rating, quality_rating)
**Priorität**: High
**Kategorie**: Zustandswechsel / Dialog / Bewertung

**Vorbedingungen**:
- Task mit Status `pending` oder `in_progress` geöffnet
- Tab "Abschließen" ist sichtbar

**Testschritte**:
1. Nutzer klickt auf Tab "Abschließen"
2. Nutzer gibt "Abschlussnotizt: Topping gut gelungen" ins Notizfeld ein
3. Nutzer setzt "Aufwand" auf 3 Sterne (Schwierigkeitsbewertung)
4. Nutzer setzt "Qualität" auf 5 Sterne
5. Nutzer gibt "Tatsächliche Dauer" ein: 15 Minuten
6. Nutzer klickt "Abschließen"

**Erwartetes Ergebnis**:
- Task wechselt zu Status "Erledigt" (grün)
- Snackbar: "Aufgabe abgeschlossen"
- In der Detailansicht sind Bewertungen (Schwierigkeit: 3/5, Qualität: 5/5) und Abschlussnotiz sichtbar
- Tab "Abschließen" ist nicht mehr sichtbar

**Nachbedingungen**: Task hat Status `completed` mit Bewertungen gespeichert

**Tags**: [req-006, task-detail, abschliessen, bewertung, sterne]

---

### TC-006-025: Task-Detailseite — Foto-Upload-Enforcement

**Anforderung**: REQ-006 §6 DoD — Foto-Upload-Enforcement; §5 Szenario 5
**Priorität**: Critical
**Kategorie**: Formvalidierung / Foto-Upload

**Vorbedingungen**:
- Task mit `requires_photo=true` und Status `pending` oder `in_progress` geöffnet

**Testschritte**:
1. Nutzer klickt auf Tab "Abschließen"
2. Nutzer klickt "Abschließen" ohne ein Foto hochzuladen

**Erwartetes Ergebnis**:
- Task wird NICHT abgeschlossen
- Fehlermeldung erscheint: "Foto-Dokumentation erforderlich für diesen Task"
- Foto-Upload-Bereich (Kamera oder Datei-Auswahl) wird hervorgehoben oder angezeigt
- Task behält Status `in_progress` bzw. `pending`

**Tags**: [req-006, task-detail, foto-pflicht, formvalidierung, enforcement]

---

### TC-006-026: Task-Detailseite — Foto hochladen und Aufgabe abschließen

**Anforderung**: REQ-006 §6 DoD — Foto-Upload-Enforcement
**Priorität**: High
**Kategorie**: Happy Path / Foto-Upload

**Vorbedingungen**:
- Task mit `requires_photo=true` und Status `in_progress` geöffnet

**Testschritte**:
1. Nutzer klickt auf Tab "Abschließen"
2. Nutzer klickt auf "Foto hinzufügen"
3. Nutzer wählt eine Bilddatei aus dem Dateisystem aus
4. Nutzer klickt "Abschließen"

**Erwartetes Ergebnis**:
- Nach Schritt 3: Bild-Vorschau erscheint im Upload-Bereich
- Nach Schritt 4: Task wird erfolgreich abgeschlossen
- Snackbar: "Aufgabe abgeschlossen"
- In der Detailansicht ist das Foto unter den gespeicherten Fotos sichtbar

**Tags**: [req-006, task-detail, foto-upload, abschliessen]

---

### TC-006-027: Task-Detailseite — Task bearbeiten (Edit-Tab)

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege (CRUD)
**Priorität**: High
**Kategorie**: Happy Path / Detailansicht

**Vorbedingungen**:
- Task-Detailseite ist geöffnet

**Testschritte**:
1. Nutzer klickt auf Tab "Bearbeiten"
2. Nutzer ändert den Namen auf "Topping durchgeführt — Revision"
3. Nutzer ändert die Priorität auf "Kritisch"
4. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Nach Schritt 4: Snackbar "Gespeichert" erscheint
- Seitenüberschrift zeigt den neuen Namen "Topping durchgeführt — Revision"
- Prioritäts-Badge zeigt "Kritisch" (rot)
- UnsavedChangesGuard: Bei Verlassen der Seite mit ungespeicherten Änderungen erscheint Bestätigungsdialog

**Tags**: [req-006, task-detail, bearbeiten, edit-tab, speichern]

---

### TC-006-028: Task-Detailseite — Kommentar hinzufügen

**Anforderung**: REQ-006 §1 — Task-Kommentare (CRUD)
**Priorität**: Medium
**Kategorie**: Happy Path / Kommentare

**Vorbedingungen**:
- Task-Detailseite ist geöffnet

**Testschritte**:
1. Nutzer klickt auf Tab "Kommentare"
2. Nutzer gibt in das Kommentarfeld ein: "Pflanze hat gut reagiert, kein Stress sichtbar"
3. Nutzer klickt "Senden" (oder drückt Enter)

**Erwartetes Ergebnis**:
- Kommentar erscheint in der Kommentarliste mit Zeitstempel und Autorname
- Eingabefeld wird geleert
- Kommentare sind chronologisch sortiert (neueste zuletzt)

**Tags**: [req-006, task-detail, kommentare, hinzufuegen]

---

### TC-006-029: Task-Detailseite — Kommentar löschen

**Anforderung**: REQ-006 §1 — Task-Kommentare CRUD (DELETE)
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Kommentare

**Vorbedingungen**:
- Task mit mindestens einem eigenen Kommentar geöffnet

**Testschritte**:
1. Nutzer klickt auf Tab "Kommentare"
2. Nutzer klickt auf das Löschen-Icon (Mülleimer) neben dem eigenen Kommentar
3. Bestätigungsdialog erscheint — Nutzer klickt "Löschen"

**Erwartetes Ergebnis**:
- Kommentar verschwindet aus der Liste
- Snackbar bestätigt Löschung

**Tags**: [req-006, task-detail, kommentare, loeschen]

---

### TC-006-030: Task-Detailseite — Änderungshistorie (Audit-Trail)

**Anforderung**: REQ-006 §1 — Task-Änderungshistorie; §6 DoD — Task-Änderungshistorie
**Priorität**: Medium
**Kategorie**: Detailansicht / Verlauf

**Vorbedingungen**:
- Task, bei der mindestens eine Statusänderung oder ein Update durchgeführt wurde

**Testschritte**:
1. Nutzer klickt auf Tab "Verlauf"

**Erwartetes Ergebnis**:
- Chronologische Liste aller Änderungen wird angezeigt
- Jeder Eintrag zeigt: Zeitpunkt der Änderung, Aktion (z.B. "Status geändert"), alten und neuen Wert, ausführenden Nutzer
- Älteste Einträge am Ende (oder Pagination vorhanden)

**Tags**: [req-006, task-detail, verlauf, audit-trail, history]

---

### TC-006-031: Task-Detailseite — Task klonen

**Anforderung**: REQ-006 §1 — Task-Klonen (Duplikate)
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Aktion

**Vorbedingungen**:
- Task-Detailseite mit Status `pending` oder `in_progress` geöffnet

**Testschritte**:
1. Nutzer klickt auf "Klonen"-Button (Kopieren-Icon, Duplicate)

**Erwartetes Ergebnis**:
- Snackbar: "Aufgabe geklont" oder "Kopie erstellt"
- Browser navigiert zur neuen geklonten Task-Detailseite
- Geklonte Task hat: selber Name + evtl. " (Kopie)", Status `pending`, kein Fälligkeitsdatum gesetzt, Checkliste und Tags aus Original übernommen
- Photo-Referenzen sind NICHT übernommen (laut Spezifikation zurückgesetzt)

**Nachbedingungen**: Neue Task-Instanz existiert im System

**Tags**: [req-006, task-detail, klonen, duplikat]

---

### TC-006-032: Task-Detailseite — Task wiedereröffnen (Reopen)

**Anforderung**: REQ-006 §1 — Task-Wiedereröffnung (Reopen)
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Aktion

**Vorbedingungen**:
- Task mit Status `completed` oder `skipped` geöffnet

**Testschritte**:
1. Nutzer klickt auf "Wiedereröffnen"-Button (Replay-Icon)

**Erwartetes Ergebnis**:
- Snackbar: "Aufgabe wiedereröffnet"
- Task-Status wechselt zu "Ausstehend" (`pending`)
- Abschlussnotiz und tatsächliche Dauer werden zurückgesetzt (gemäß Spec)
- Tags, Checkliste und Fotos bleiben erhalten
- Tab "Abschließen" wird wieder angezeigt

**Nachbedingungen**: Task hat Status `pending`

**Tags**: [req-006, task-detail, wiedereroeffnen, reopen, zustandswechsel]

---

### TC-006-033: Task-Detailseite — Task löschen

**Anforderung**: REQ-006 §1 — Vollständige Einzelaufgaben-Pflege (Delete)
**Priorität**: High
**Kategorie**: Zustandswechsel / Dialog

**Vorbedingungen**:
- Task-Detailseite geöffnet

**Testschritte**:
1. Nutzer klickt auf "Löschen"-Button (Mülleimer-Icon)
2. Bestätigungsdialog erscheint: "Sind Sie sicher, dass Sie diese Aufgabe löschen möchten?"
3. Nutzer klickt "Löschen"

**Erwartetes Ergebnis**:
- Browser navigiert zurück zur Task-Queue
- Snackbar: "Aufgabe gelöscht"
- Task ist nicht mehr in der Liste

**Nachbedingungen**: Task ist gelöscht

**Tags**: [req-006, task-detail, loeschen, bestaetigungsdialog]

---

## Gruppe 4: Workflow-Template-Liste

### TC-006-034: Workflow-Template-Liste aufrufen

**Anforderung**: REQ-006 §1 — Template-Bibliothek (System-Workflows)
**Priorität**: High
**Kategorie**: Listenansicht / Navigation

**Vorbedingungen**:
- Nutzer ist eingeloggt
- System-Workflows sind vorhanden (z.B. "Cannabis SOG", "Tomaten Multi-Stem", "Nährlösung-Wechsel")

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/workflows`

**Erwartetes Ergebnis**:
- Seitenüberschrift "Workflows" wird angezeigt
- Tabelle mit Spalten: Name, Art/Spezies, Zugewiesene Pflanzen, Aktionen
- System-Workflows tragen den Badge "System" (blau, outlined)
- Auto-generierte Workflows tragen den Badge "Automatisch generiert" (lila, outlined)
- Suchfeld über der Tabelle ist sichtbar
- Buttons "Aus Spezies generieren" und "Workflow erstellen" sind sichtbar

**Tags**: [req-006, workflow-liste, navigation, system-workflows]

---

### TC-006-035: Workflow-Template-Liste — System-Template kann nicht gelöscht werden

**Anforderung**: REQ-006 §4 — Auth-Tabelle: WorkflowTemplates löschen = Admin; System-Templates readonly
**Priorität**: High
**Kategorie**: Fehlermeldung / Zustandswechsel

**Vorbedingungen**:
- Workflow-Template-Liste ist geöffnet
- Mind. ein System-Workflow vorhanden

**Testschritte**:
1. Nutzer sucht einen Workflow mit Badge "System"
2. Nutzer bewegt den Mauszeiger über den Löschen-Button (Mülleimer-Icon)

**Erwartetes Ergebnis**:
- Löschen-Button ist ausgegraut (disabled)
- Tooltip erscheint: "System-Templates können nicht gelöscht werden" (oder ähnlicher Text)
- Kein Klick möglich

**Tags**: [req-006, workflow-liste, system-template, loeschen-deaktiviert, tooltip]

---

### TC-006-036: Workflow-Template-Liste — Eigenen Workflow löschen

**Anforderung**: REQ-006 §4 — WorkflowTemplates löschen = Admin
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Dialog

**Vorbedingungen**:
- Nutzer ist Admin im Tenant
- Mindestens ein benutzerdefinierter (nicht-System) Workflow vorhanden

**Testschritte**:
1. Nutzer klickt auf den Löschen-Button eines eigenen Workflows
2. Bestätigungsdialog erscheint mit dem Namen des Workflows
3. Nutzer klickt "Löschen"

**Erwartetes Ergebnis**:
- Nach Schritt 2: Dialog zeigt "Sind Sie sicher, dass Sie '[Workflow-Name]' löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden." (destructive Styling)
- Nach Schritt 3: Workflow verschwindet aus der Liste
- Snackbar: "Workflow gelöscht"

**Tags**: [req-006, workflow-liste, eigener-workflow, loeschen, dialog]

---

### TC-006-037: Workflow aus Spezies generieren

**Anforderung**: REQ-006 §1 — Auto-Generierung von Activity Plans aus Spezies
**Priorität**: High
**Kategorie**: Happy Path / Dialog

**Vorbedingungen**:
- Mindestens eine Species in der Datenbank vorhanden
- Keine existierenden Workflows für die gewählte Species

**Testschritte**:
1. Nutzer klickt auf "Aus Spezies generieren"-Button
2. Dialog öffnet sich mit Spezies-Dropdown
3. Nutzer wählt eine Spezies aus (z.B. "Cannabis sativa")
4. Nutzer klickt "Generieren"

**Erwartetes Ergebnis**:
- Ladeindikator erscheint während Generierung (CircularProgress im Button)
- Nach erfolgreicher Generierung: Snackbar "Workflow generiert"
- Browser navigiert automatisch zur neuen Workflow-Detailseite
- Neuer Workflow trägt Badge "Automatisch generiert"

**Nachbedingungen**: Neuer Workflow für die gewählte Spezies existiert

**Tags**: [req-006, workflow-generieren, spezies, dialog]

---

### TC-006-038: Workflow instanziieren (auf Pflanze anwenden)

**Anforderung**: REQ-006 §1 — Phasengebundene Workflow-Gestaltung; Szenario 1
**Priorität**: Critical
**Kategorie**: Happy Path / Dialog / Zustandswechsel

**Vorbedingungen**:
- Mindestens ein Workflow und mindestens eine PlantInstance vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/workflows`
2. Nutzer klickt auf den "Starten"-Button (Play-Icon) eines Workflows
3. Dialog "Workflow anwenden" öffnet sich
4. Nutzer wählt eine Pflanze aus dem Dropdown
5. Nutzer klickt "Anwenden"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Browser navigiert zur Task-Queue
- Snackbar: "Workflow angewendet" oder "Tasks erstellt"
- In der Task-Queue erscheinen die neu erstellten Tasks aus dem Workflow (Status `pending` für aktive Phasen, ggf. `dormant` für zukünftige Phasen)

**Nachbedingungen**: Workflow-Instanz ist aktiv; Tasks sind in der Queue sichtbar

**Tags**: [req-006, workflow-instanziieren, pflanze, dialog, happy-path]

---

## Gruppe 5: Workflow-Detailseite

### TC-006-039: Workflow-Detailseite aufrufen — Tabs

**Anforderung**: REQ-006 §1 — Workflow-Instanz-Übersicht
**Priorität**: High
**Kategorie**: Navigation / Detailansicht

**Vorbedingungen**:
- Mindestens ein Workflow existiert

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/workflows`
2. Nutzer klickt auf einen Workflow-Eintrag in der Tabelle

**Erwartetes Ergebnis**:
- Browser navigiert zu `/aufgaben/workflows/:key`
- Seitenüberschrift zeigt den Workflow-Namen
- Tabs sind sichtbar (z.B. "Aufgaben-Templates", "Einstellungen")
- Tab "Aufgaben-Templates" ist standardmäßig aktiv

**Tags**: [req-006, workflow-detail, tabs, navigation]

---

### TC-006-040: Workflow-Detailseite — Task-Template hinzufügen

**Anforderung**: REQ-006 §1 — User-Blueprints editierbar
**Priorität**: High
**Kategorie**: Happy Path / Detailansicht / Dialog

**Vorbedingungen**:
- Benutzerdefinierter (nicht-System) Workflow ist geöffnet

**Testschritte**:
1. Nutzer klickt auf "Task-Template hinzufügen"-Button (+ Icon)
2. Dialog öffnet sich
3. Nutzer gibt Name ein: "Wachstum messen"
4. Nutzer wählt Kategorie: "Beobachtung"
5. Nutzer wählt Trigger-Typ: "Tage nach Phase"
6. Nutzer gibt Trigger-Phase ein: "vegetative"
7. Nutzer gibt Tage-Versatz ein: 7
8. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Neues Task-Template "Wachstum messen" erscheint in der Template-Tabelle
- Template zeigt Trigger-Info: "7 Tage nach vegetative-Phase"

**Tags**: [req-006, workflow-detail, task-template, hinzufuegen, dialog]

---

### TC-006-041: Workflow-Detailseite — Task-Template bearbeiten

**Anforderung**: REQ-006 §1 — User-Blueprints editierbar, Versionierung
**Priorität**: Medium
**Kategorie**: Happy Path / Detailansicht

**Vorbedingungen**:
- Benutzerdefinierter Workflow mit mindestens einem Task-Template geöffnet

**Testschritte**:
1. Nutzer klickt auf das Edit-Icon neben einem Task-Template
2. Dialog öffnet sich mit vorausgefüllten Werten
3. Nutzer ändert den Namen
4. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Aktualisierter Name erscheint in der Template-Tabelle
- Änderungen sind gespeichert (persistieren nach Seitenaktualisierung)

**Tags**: [req-006, workflow-detail, task-template, bearbeiten]

---

### TC-006-042: Workflow-Detailseite — Workflow-Metadaten bearbeiten (Edit-Tab)

**Anforderung**: REQ-006 §1 — User-Blueprints editierbar
**Priorität**: Medium
**Kategorie**: Happy Path / Detailansicht

**Vorbedingungen**:
- Benutzerdefinierter Workflow ist geöffnet

**Testschritte**:
1. Nutzer navigiert zum Tab "Einstellungen" oder "Bearbeiten"
2. Nutzer ändert den Workflow-Namen
3. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Snackbar: "Gespeichert"
- Seitenüberschrift zeigt den neuen Workflow-Namen
- UnsavedChangesGuard verhindert Seitenwechsel ohne Speichern

**Tags**: [req-006, workflow-detail, bearbeiten, metadaten]

---

## Gruppe 6: HST-Validierung und Training

### TC-006-043: HST-Validierung — Topping in Early Flowering blockiert

**Anforderung**: REQ-006 §1 — HST-Validation; §5 Szenario 2a
**Priorität**: Critical
**Kategorie**: Fehlermeldung / Validierung / Zustandswechsel

**Vorbedingungen**:
- Cannabis-Pflanze, aktuell in Phase "Early Flowering" (early_flowering)

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt "Aufgabe erstellen"
3. Nutzer gibt Name "Topping" ein
4. Nutzer wählt Kategorie "Training"
5. Nutzer wählt die Cannabis-Pflanze in der frühen Blütephase aus
6. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Fehlermeldung erscheint (Snackbar oder Inline): "KRITISCH: Topping in Early-Flowering verboten. Supercropping und Transplant sind im Stretch noch möglich."
- Task wird NICHT erstellt
- Dialog bleibt geöffnet oder Fehlermeldung ist deutlich sichtbar

**Tags**: [req-006, hst-validierung, topping, early-flowering, blockiert, kritisch]

---

### TC-006-044: HST-Validierung — Supercropping im Stretch erlaubt

**Anforderung**: REQ-006 §1 — HST-Validation; §5 Szenario 2b
**Priorität**: High
**Kategorie**: Happy Path / Validierung

**Vorbedingungen**:
- Cannabis-Pflanze, aktuell in Phase "Early Flowering" (Stretch)

**Testschritte**:
1. Nutzer erstellt eine neue Task "Supercropping"
2. Nutzer wählt Kategorie "Training" und die Cannabis-Pflanze in früher Blüte
3. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Task wird erfolgreich erstellt
- Snackbar: "Erstellt"
- Optional: Hinweis-Meldung "ERLAUBT: Supercropping im Stretch (Early Flowering) noch möglich — ab Mitte Blüte nicht mehr möglich" erscheint (Info, kein Fehler)

**Tags**: [req-006, hst-validierung, supercropping, stretch, erlaubt]

---

### TC-006-045: HST-Validierung — Recovery-Zeit-Warnung (Überschreitbar)

**Anforderung**: REQ-006 §1 — HST Recovery-Zeit; §5 Szenario 6
**Priorität**: High
**Kategorie**: Fehlermeldung / Warnung / Zustandswechsel

**Vorbedingungen**:
- Pflanze bei der vor 3 Tagen ein HST-Event (Supercropping) abgeschlossen wurde
- Empfohlene Recovery-Zeit: 7 Tage (für Cannabis)

**Testschritte**:
1. Nutzer versucht eine neue Training-Task "Topping" für diese Pflanze zu erstellen
2. Warnung erscheint
3. Nutzer klickt "Trotzdem fortfahren" (Override)

**Erwartetes Ergebnis**:
- Nach Schritt 1/2: Warnmeldung erscheint: "Nur 3 Tage seit letztem HST (Supercropping). Empfohlene Recovery-Zeit: 7 Tage." mit Severity "Warnung" (nicht "Kritisch")
- Schaltfläche "Trotzdem fortfahren" ist sichtbar
- Nach Schritt 3: Task wird erstellt, Warnung verschwindet

**Tags**: [req-006, hst-validierung, recovery, warnung, override, can-override]

---

### TC-006-046: Autoflower-Guard — HST-Warnung für Autoflower-Cultivar

**Anforderung**: REQ-006 §1 — Autoflower-Guard; §5 Szenario 13
**Priorität**: High
**Kategorie**: Fehlermeldung / Warnung

**Vorbedingungen**:
- Cannabis-Pflanze mit Autoflower-Cultivar (`flowering_type='autoflower'`) in vegetativer Phase

**Testschritte**:
1. Nutzer erstellt eine Task "Topping" für die Autoflower-Pflanze
2. Warnung erscheint
3. Nutzer klickt "Trotzdem fortfahren"

**Erwartetes Ergebnis**:
- Warnmeldung erscheint: "HST nicht empfohlen bei Autoflower-Sorten. Autoflower haben eine fixe Lebenszeit; Stress-Recovery reduziert die produktive Wachstumsphase überproportional."
- Vorgeschlagene Alternativen: "LST Bend", "LST Tie", "Defoliation", "SCROG Tucking"
- Severity: `warning` (nicht `critical`) — Override möglich
- Nach Schritt 3: Task wird erstellt

**Tags**: [req-006, autoflower-guard, warnung, topping, override, can-override]

---

### TC-006-047: Autoflower-Guard — LST für Autoflower ohne Warnung erlaubt

**Anforderung**: REQ-006 §1 — Autoflower-Guard; §5 Szenario 14
**Priorität**: Medium
**Kategorie**: Happy Path

**Vorbedingungen**:
- Cannabis-Pflanze mit Autoflower-Cultivar

**Testschritte**:
1. Nutzer erstellt Task "LST Bend" für Autoflower-Pflanze
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Keine Warnung oder Fehlermeldung erscheint
- Task wird direkt erstellt, Snackbar: "Erstellt"

**Tags**: [req-006, autoflower-guard, lst, kein-fehler, happy-path]

---

## Gruppe 7: Dormant-Status und Phasengebundene Tasks

### TC-006-048: Dormant-Tasks nach Workflow-Instantiation sichtbar

**Anforderung**: REQ-006 §1 — Dormant-Status für phasengebundene Tasks; §6 DoD — Dormant-Status
**Priorität**: High
**Kategorie**: Zustandswechsel / Listenansicht

**Vorbedingungen**:
- Workflow mit phasengebundenen Tasks instanziiert auf eine Pflanze in Phase "Keimung"
- Workflow enthält Tasks für Phase "Blüte" (noch nicht aktiv)

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer sucht nach dormanten Tasks für die Pflanze

**Erwartetes Ergebnis**:
- Dormante Tasks erscheinen in einem separaten Abschnitt "Geplant" (dormant section)
- Diese Tasks haben Status "Geplant" oder ein anderes visuelles Dormant-Badge
- Action-Buttons (Starten, Abschließen) sind für dormante Tasks ausgegraut oder nicht vorhanden

**Tags**: [req-006, dormant, phasengebunden, listenansicht]

---

### TC-006-049: Dormant-Tasks werden bei Phasenwechsel aktiviert

**Anforderung**: REQ-006 §1 — Phase-Transition-Hook; §6 DoD — Phase-Transition-Hook
**Priorität**: Critical
**Kategorie**: Zustandswechsel / Integration REQ-003

**Vorbedingungen**:
- Pflanze hat dormante Task für Phase "Blüte" (`trigger_phase: 'flowering'`)
- Pflanze ist aktuell in vegetativer Phase

**Testschritte**:
1. Nutzer navigiert zur PlantInstance-Detailseite (oder PlantingRun-Detailseite)
2. Nutzer wechselt die Pflanzphase zu "Blüte" (z.B. durch Klick auf "Nächste Phase")
3. Nutzer navigiert zurück zu `/aufgaben/queue`

**Erwartetes Ergebnis**:
- Dormante Task für Phase "Blüte" hat jetzt Status `pending`
- Task erscheint in der aktiven Task-Queue (nicht mehr im Dormant-Bereich)
- Fälligkeitsdatum wurde basierend auf dem Trigger-Typ berechnet und ist angezeigt

**Nachbedingungen**: Dormante Task ist aktiv (pending)

**Tags**: [req-006, req-003, dormant, phase-transition, aktivierung, zustandswechsel]

---

### TC-006-050: Dependency-Blockierung — Blockierte Task nicht startbar

**Anforderung**: REQ-006 §1 — Dependency-Chains; §5 Szenario 4
**Priorität**: High
**Kategorie**: Fehlermeldung / Zustandswechsel

**Vorbedingungen**:
- Workflow instanziiert mit zwei Tasks: Task A (Transplant, pending) blockiert Task B (Heavy Defoliation)

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer klickt auf den "Starten"-Button von Task B (Heavy Defoliation)

**Erwartetes Ergebnis**:
- Start-Button ist ausgegraut (disabled) ODER
- Fehlermeldung erscheint: "Wartend auf: Transplant" oder "Dieser Task ist blockiert durch: [Task A Name]"
- Task B bleibt im Status `pending`

**Tags**: [req-006, dependency, blockierung, wartend, fehlermeldung]

---

### TC-006-051: Auto-Rescheduling — Abhängige Tasks werden verschoben

**Anforderung**: REQ-006 §1 — Dependency-Chains; §5 Szenario 3
**Priorität**: High
**Kategorie**: Zustandswechsel / Integration

**Vorbedingungen**:
- Workflow mit Tasks: Task A (Due: 15.01, depends_on: nichts), Task B (Due: 22.01, abhängig von Task A mit min_delay=7)
- Task A ist 5 Tage nach dem Fälligkeitsdatum noch nicht abgeschlossen

**Testschritte**:
1. Nutzer schließt Task A ab (5 Tage nach Fälligkeitsdatum)
2. Nutzer navigiert zur Task-Queue und sucht Task B

**Erwartetes Ergebnis**:
- Task B hat ein neues Fälligkeitsdatum: ursprüngliches Datum + 5 Tage (verschoben)
- Informations-Hinweis: "Workflow ist 5 Tage hinter Zeitplan" (oder ähnlich)
- Kein separates manuelles Eingreifen des Nutzers notwendig (automatisches Rescheduling)

**Tags**: [req-006, auto-rescheduling, dependency, verschiebung, verzögerung]

---

## Gruppe 8: Activity Plans

### TC-006-052: Activity Plan Übersicht aufrufen

**Anforderung**: REQ-006 §1 — Phasengebundene Workflow-Gestaltung / Activity Plans
**Priorität**: Medium
**Kategorie**: Listenansicht / Navigation

**Vorbedingungen**:
- Mindestens 2 Species in der Datenbank vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/activity-plans`

**Erwartetes Ergebnis**:
- Seite lädt mit Überschrift "Aktivitätspläne" oder ähnlich
- Grid mit Species-Karten wird angezeigt (2 oder 3 Spalten je nach Bildschirmbreite)
- Jede Karte zeigt: Artname (Common Name), wissenschaftlicher Name, Loading-Spinner während Plan generiert wird
- Nach Generierung: Karte zeigt Chips für Phasenanzahl, Aktivitätenanzahl, Gesamtdauer in Tagen
- Karte ist klickbar (navigiert zu Workflow-Detailseite)

**Tags**: [req-006, activity-plans, uebersicht, listenansicht]

---

### TC-006-053: Activity Plan — keine Species vorhanden (Leerer Zustand)

**Anforderung**: REQ-006 / REQ-001 — Abhängigkeit Stammdaten
**Priorität**: Medium
**Kategorie**: Leerer Zustand

**Vorbedingungen**:
- Keine Species in der Datenbank

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/activity-plans`

**Erwartetes Ergebnis**:
- Leere-Zustands-Meldung erscheint: "Keine Pflanzenarten vorhanden"
- CTA-Button: "Pflanzenart hinzufügen" (navigiert zu `/stammdaten/species`)

**Tags**: [req-006, req-001, activity-plans, leer, empty-state]

---

## Gruppe 9: Timer-Funktion (W-006)

### TC-006-054: Timer ad-hoc starten — Task ohne vordefinierte Timer-Dauer

**Anforderung**: REQ-006 §1 — Manuelle Timer (Ad-hoc); §5 Szenario 12
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Timer

**Vorbedingungen**:
- Task ohne `timer_duration_seconds` geöffnet, Status `in_progress`
- Tab "Abschließen" oder "Details" ist aktiv

**Testschritte**:
1. Nutzer klickt auf "Timer starten" oder "Timer hinzufügen"
2. Nutzer gibt Dauer ein: 1800 (30 Minuten)
3. Nutzer bestätigt

**Erwartetes Ergebnis**:
- Countdown-Timer erscheint mit 30:00
- Start/Pause/Reset-Buttons sind sichtbar
- Timer startet zu laufen

**Tags**: [req-006, timer, ad-hoc, w-006, manuell]

---

### TC-006-055: Timer nicht-blockierend — Aufgabe vor Timer-Ablauf abschließbar

**Anforderung**: REQ-006 §1 — Kein Blockieren (Timer nicht-blockierend)
**Priorität**: High
**Kategorie**: Happy Path / Timer

**Vorbedingungen**:
- Task mit laufendem Timer (noch nicht abgelaufen)

**Testschritte**:
1. Timer läuft (z.B. noch 25 Minuten verbleibend)
2. Nutzer klickt auf "Abschließen"-Button

**Erwartetes Ergebnis**:
- Task wird erfolgreich abgeschlossen, obwohl Timer noch läuft
- Snackbar: "Aufgabe abgeschlossen"
- Kein Fehler oder Blockierungsmeldung wegen laufendem Timer

**Tags**: [req-006, timer, nicht-blockierend, abschliessen, w-006]

---

## Gruppe 10: Phänologische Ereignisse und Seasonal-Trigger

### TC-006-056: Phänologisches Ereignis dokumentieren

**Anforderung**: REQ-006 §1 — Phenological-Trigger (G-005); §6 DoD — PhenologicalEvent-Dokumentation
**Priorität**: Medium
**Kategorie**: Happy Path / Dialog

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Funktion zur Dokumentation phänologischer Ereignisse ist über UI zugänglich (z.B. über Site-Detailseite oder separaten Menüpunkt)

**Testschritte**:
1. Nutzer navigiert zur Seite für phänologische Ereignisse
2. Nutzer klickt "Ereignis dokumentieren"
3. Nutzer wählt Ereignistyp: "Forsythienblüte" (forsythia_bloom)
4. Nutzer gibt Beobachtungsdatum ein: heute
5. Nutzer gibt Notiz ein: "Forsythie an der Westseite blüht"
6. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Ereignis wird gespeichert und in der Ereignis-Liste angezeigt
- Verknüpfte Tasks mit `trigger_type='phenological'` und `phenological_event='forsythia_bloom'` werden aktiviert (aus `dormant` → `pending`)
- Snackbar: "Ereignis gespeichert" und ggf. "X Aufgaben wurden aktiviert"

**Tags**: [req-006, phaenologie, ereignis, g-005, seasonal-trigger]

---

### TC-006-057: Seasonal-Month-Trigger — Oktober-Tasks werden angezeigt

**Anforderung**: REQ-006 §1 — Seasonal-Month-Trigger (G-005); §5 12-Monats-Gartenkalender
**Priorität**: Medium
**Kategorie**: Zustandswechsel / Listenansicht

**Vorbedingungen**:
- 12-Monats-Gartenkalender-Workflow instanziiert
- Aktueller Monat ist Oktober

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`

**Erwartetes Ergebnis**:
- Oktober-Tasks erscheinen als aktiv (pending): "Winterschutz-Checklist", "Dahlien ausgraben", "Kübelpflanzen rein"
- Saisonale Tasks tragen Kategorie-Badge "Saisonal"
- November- und Dezember-Tasks sind noch dormant (in separatem Bereich)

**Tags**: [req-006, seasonal-month, oktober, gartenkalender, g-005]

---

## Gruppe 10b: Phänologische Trigger konfigurieren (Task-Template-Dialog)

### TC-006-073: Task-Template — Trigger-Typ "Phänologisch" auswählen und Zeigerpflanze konfigurieren

**Anforderung**: REQ-006 §1 — Phenological-Trigger (G-005); TaskTemplate.trigger_type='phenological', TaskTemplate.phenological_event
**Priorität**: High
**Kategorie**: Happy Path / Dialog / Formvalidierung

**Vorbedingungen**:
- Nutzer ist eingeloggt und befindet sich auf der Workflow-Detailseite eines eigenen (nicht System-)Workflows
- Tab "Task-Templates" ist aktiv
- Dialog "Task-Template hinzufügen" oder "Task-Template bearbeiten" ist geöffnet

**Testschritte**:
1. Nutzer öffnet den Dialog "Task-Template hinzufügen" (Button "+ Task hinzufügen")
2. Nutzer gibt Name ein: "Rosen schneiden"
3. Nutzer wählt im Dropdown "Trigger-Typ" den Wert "Phänologisch" aus
4. Das Formular zeigt ein neues Dropdown "Phänologisches Ereignis"
5. Nutzer wählt im Dropdown "Phänologisches Ereignis" den Wert "Forsythienblüte" (forsythia_bloom) aus
6. Nutzer gibt Kategorie "Saisonal" an
7. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Nach Schritt 3: Das Feld "Phänologisches Ereignis" erscheint im Formular; Felder für "Tage-Offset" und "Kalenderdatum" werden ausgeblendet oder sind deaktiviert
- Nach Schritt 5: Das Dropdown zeigt alle vordefinierten phänologischen Zeigerpflanzen: "Haselblüte", "Forsythienblüte", "Apfelblüte", "Holunderblüte", "Lindenblüte", "Erster Frost"
- Nach Schritt 7: Dialog schließt sich, Snackbar "Gespeichert"
- Das neue Task-Template erscheint in der Template-Liste mit Trigger-Badge "Phänologisch: Forsythienblüte" (oder ähnliche Anzeige)

**Nachbedingungen**: TaskTemplate mit trigger_type='phenological' und phenological_event='forsythia_bloom' ist gespeichert

**Tags**: [req-006, phaenologie, task-template, trigger-typ, forsythia-bloom, g-005, dialog]

---

### TC-006-074: Phänologisch getriggerte Task bleibt dormant bis Ereignis eingetreten ist

**Anforderung**: REQ-006 §1 — Phenological-Trigger (G-005); PhenologicalEvent-Dokumentation als Aktivierungsbedingung
**Priorität**: Critical
**Kategorie**: Zustandswechsel / Grenzwert

**Vorbedingungen**:
- Workflow mit TaskTemplate (trigger_type='phenological', phenological_event='elderberry_bloom') ist auf eine Pflanze instanziiert
- Kein PhenologicalEvent vom Typ 'elderberry_bloom' für das aktuelle Jahr und den zugehörigen Standort ist dokumentiert

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`
2. Nutzer aktiviert Anzeige "Geplante Tasks" (dormant section)

**Erwartetes Ergebnis**:
- Die phänologisch verknüpfte Task ("Bohnen säen" oder ähnlich) ist NICHT in der aktiven Task-Queue sichtbar
- Die Task erscheint im Bereich "Geplant" (dormant) mit dem Hinweis "Wartet auf: Holunderblüte" oder "Ausstehend: phänologisches Ereignis nicht eingetreten"
- Kein Fälligkeitsdatum ist gesetzt (oder es wird "—" angezeigt)
- Action-Buttons (Starten, Abschließen) sind ausgegraut oder nicht vorhanden

**Nachbedingungen**: Task bleibt im Status dormant bis Holunderblüte dokumentiert wird

**Tags**: [req-006, phaenologie, dormant, holunderblüte, elderberry-bloom, g-005, grenzwert]

---

### TC-006-075: Phänologischen Trigger durch Kalenderdatum-Trigger ersetzen (Trigger-Typ ändern)

**Anforderung**: REQ-006 §1 — Phenological-Trigger (G-005); TaskTemplate editierbar; §1 Individuelle Task-Anpassung innerhalb von Workflows
**Priorität**: Medium
**Kategorie**: Happy Path / Dialog / Zustandswechsel

**Vorbedingungen**:
- Task-Template mit trigger_type='phenological' und phenological_event='apple_bloom' existiert in einem Workflow
- Der Dialog "Task-Template bearbeiten" ist für dieses Template geöffnet

**Testschritte**:
1. Nutzer öffnet den Bearbeiten-Dialog für das phänologische Task-Template
2. Nutzer wählt im Dropdown "Trigger-Typ" den Wert "Absolutes Datum" aus
3. Das Formular zeigt ein Kalender-Datumsfeld; das Dropdown "Phänologisches Ereignis" verschwindet
4. Nutzer gibt ein konkretes Datum ein: 20.04. (des aktuellen Jahres)
5. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Nach Schritt 2: Das Feld "Phänologisches Ereignis" (Zeigerpflanzen-Dropdown) wird ausgeblendet oder deaktiviert; stattdessen erscheint ein Datum-Eingabefeld
- Nach Schritt 5: Dialog schließt sich, Snackbar "Gespeichert"
- Das Task-Template zeigt in der Übersicht nun Trigger-Badge "Absolutes Datum: 20.04." statt "Phänologisch: Apfelblüte"
- Bereits dormante Instanzen dieses Templates in der Task-Queue zeigen nun das Fälligkeitsdatum 20.04. und sind nicht mehr auf ein phänologisches Ereignis angewiesen

**Nachbedingungen**: TaskTemplate hat trigger_type='absolute_date'; vorheriger phenological_event-Wert ist nicht mehr aktiv

**Tags**: [req-006, phaenologie, trigger-typ-aendern, absolutes-datum, apple-bloom, dialog, g-005]

---

## Gruppe 11: Gießplan-Task-Integration (REQ-004/REQ-014)

### TC-006-058: Gießplan-Task erscheint in Task-Queue (Weekday-Modus)

**Anforderung**: REQ-006 §3 — Celery-Beat generate_watering_tasks; §6 DoD — Gießplan-Wochentag-Modus
**Priorität**: High
**Kategorie**: Listenansicht / Integration

**Vorbedingungen**:
- PlantingRun mit Status `active` und NutrientPlan + WateringSchedule (weekdays-Modus, z.B. Montag, Mittwoch, Freitag) vorhanden
- Heute ist ein konfigurierter Gießtag (z.B. Montag)
- Celery-Beat hat `generate_watering_tasks` heute bereits ausgeführt

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`

**Erwartetes Ergebnis**:
- Gießplan-Task erscheint: Name z.B. "Gießen: [Run-Name]"
- Task hat Kategorie `feeding`, Priorität `hoch`, Fälligkeit heute
- Task ist mit dem PlantingRun verknüpft (Verlinkung zum Run sichtbar)

**Tags**: [req-006, req-004, giessplan, celery, weekday, task-queue]

---

### TC-006-059: Gießplan-Task-Idempotenz — Kein Duplikat bei mehrfachem Lauf

**Anforderung**: REQ-006 §6 DoD — Gießplan-Idempotenz
**Priorität**: High
**Kategorie**: Grenzwert / Edge Case

**Vorbedingungen**:
- Gießplan-Task für heute existiert bereits
- Celery-Beat läuft erneut (z.B. nach Pod-Restart)

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue`

**Erwartetes Ergebnis**:
- Nur EINE Gießplan-Task für denselben Run und denselben Tag ist sichtbar
- Keine doppelten Tasks erscheinen

**Tags**: [req-006, giessplan, idempotenz, kein-duplikat]

---

## Gruppe 12: Neue Workflow erstellen (Benutzerdefiniert)

### TC-006-060: Neuen Workflow manuell erstellen

**Anforderung**: REQ-006 §1 — User-Blueprints (Eigene Strategien)
**Priorität**: High
**Kategorie**: Happy Path / Dialog

**Vorbedingungen**:
- Nutzer ist Admin oder Grower im Tenant

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/workflows`
2. Nutzer klickt "Workflow erstellen"-Button
3. Dialog öffnet sich
4. Nutzer gibt Name ein: "Mein Tomatenpflege-Workflow"
5. Nutzer gibt Beschreibung ein
6. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Snackbar: "Workflow erstellt"
- Neuer Workflow erscheint in der Workflow-Liste ohne System- oder Auto-generiert-Badge
- Workflow-Detailseite ist per Klick aufrufbar

**Nachbedingungen**: Neuer leerer Workflow existiert

**Tags**: [req-006, workflow-erstellen, benutzerdefiniert, dialog]

---

## Gruppe 13: Canopy-Metriken und Recovery-Tracker (G-004)

### TC-006-061: Recovery-Timer nach HST-Event angezeigt

**Anforderung**: REQ-006 §1 — Recovery-Timer (G-004); §5 Szenario 15
**Priorität**: High
**Kategorie**: Detailansicht / Visualisierung

**Vorbedingungen**:
- Cannabis-Pflanze, bei der vor 2 Tagen ein Topping-Task abgeschlossen wurde
- TrainingEvent mit `recovery_days=7` und `recovery_end_date` in 5 Tagen existiert

**Testschritte**:
1. Nutzer navigiert zur PlantInstance-Detailseite
2. Nutzer öffnet den Bereich für Training-History oder Detailansicht

**Erwartetes Ergebnis**:
- Recovery-Timer-Anzeige: "Tag 2/7 Erholung nach Topping"
- Fortschrittsbalken zeigt ca. 28% Fortschritt
- Hinweis: nächstes Training erst ab [recovery_end_date] ohne Warnung möglich

**Tags**: [req-006, req-013, recovery-timer, g-004, topping, pflanze]

---

### TC-006-062: Recovery-Überlappungswarnung

**Anforderung**: REQ-006 §1 — Recovery-Timer (G-004); §5 Szenario 16
**Priorität**: High
**Kategorie**: Fehlermeldung / Warnung

**Vorbedingungen**:
- Pflanze mit laufender Recovery-Phase nach Topping (recovery_end_date in 4 Tagen)
- Nutzer plant eine neue Training-Task

**Testschritte**:
1. Nutzer erstellt eine neue "Supercropping"-Task für die Pflanze mit Fälligkeit in 2 Tagen

**Erwartetes Ergebnis**:
- Warnmeldung: "Erholungsphase nach Topping endet am [Datum]. Geplantes Supercropping liegt 2 Tage vor Ablauf. Aktueller Status: Tag 5/7 Erholung nach Topping"
- `can_override: true` — Button "Trotzdem fortfahren" sichtbar
- Task kann mit Override erstellt werden

**Tags**: [req-006, recovery-uberlappung, warnung, g-004, can-override]

---

### TC-006-063: Canopy-Messung erfassen

**Anforderung**: REQ-006 §1 — Canopy-Metriken (G-004); §6 DoD — Canopy-Metriken
**Priorität**: Medium
**Kategorie**: Happy Path / Dialog / Detailansicht

**Vorbedingungen**:
- Cannabis-Pflanze mit SCROG-Equipment (SCROG-Netz zugewiesen)
- Nutzer ist auf der PlantInstance-Detailseite oder Canopy-Messungs-Dialog

**Testschritte**:
1. Nutzer klickt "Canopy-Messung hinzufügen"
2. Nutzer gibt ein: Min-Höhe 28 cm, Max-Höhe 35 cm, Anzahl Triebe 6
3. Nutzer gibt SCROG-Füllgrad ein: 65%
4. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Canopy-Messung wird gespeichert
- Berechnete Werte werden angezeigt:
  - Durchschnittliche Höhe: 31,5 cm
  - Evenness-Score: 0,8 (kein Interventions-Hinweis, da > 0,7)
  - SCROG-Füllgrad: 65% mit Hinweis "Netz noch nicht bereit für Blüte-Switch, Ziel: 80–95%"

**Tags**: [req-006, canopy-messung, g-004, scrog, evenness-score]

---

### TC-006-064: Canopy-Evenness-Score — Interventionsempfehlung bei Score < 0,7

**Anforderung**: REQ-006 §1 — Canopy-Metriken (G-004); §6 DoD — Canopy-Evenness-Score
**Priorität**: Medium
**Kategorie**: Fehlermeldung / Hinweis / Detailansicht

**Vorbedingungen**:
- Cannabis-Pflanze, Canopy-Messung wird erfasst mit sehr ungleichmäßigen Höhen

**Testschritte**:
1. Nutzer gibt in die Canopy-Messung ein: Min-Höhe 10 cm, Max-Höhe 40 cm, Triebe 6
2. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Evenness-Score: ca. 0,75 (1,0 - 30/40 = 0,25 → Score = 0,75) — gerade noch ok
- Wenn der Score unter 0,7 fällt (z.B. Min=5, Max=40): Hinweis erscheint "Ungleichmäßige Canopy — Intervention empfohlen (LST/Supercropping zur Höhenkorrektur)"

**Tags**: [req-006, canopy, evenness-score, g-004, intervention-empfehlung]

---

## Gruppe 14: Grenzwerte und Edge Cases

### TC-006-065: Task erstellen — Name zu kurz (< 1 Zeichen)

**Anforderung**: REQ-006 §3 — TaskInstance.name min_length=1; Frontend-Schema z.string().min(1).max(200)
**Priorität**: Medium
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen**:
- Dialog "Aufgabe erstellen" ist geöffnet

**Testschritte**:
1. Nutzer gibt im Feld "Name" ein Leerzeichen ein (oder lässt es leer)
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Fehlermeldung unter dem Name-Feld erscheint
- Task wird nicht erstellt
- Dialog bleibt geöffnet

**Tags**: [req-006, formvalidierung, name, grenzwert, min-laenge]

---

### TC-006-066: Task erstellen — Bewertungsfeld außerhalb 1–5

**Anforderung**: REQ-006 §3 — difficulty_rating Optional[int] ge=1, le=5
**Priorität**: Low
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen**:
- Task-Detailseite mit Tab "Abschließen" geöffnet

**Testschritte**:
1. Nutzer versucht, einen Wert 0 (oder 6) im Bewertungsfeld einzugeben (sofern Freitext-Eingabe möglich)

**Erwartetes Ergebnis**:
- UI verhindert die Eingabe durch Sterne-Widget (min=1, max=5 — nur Sterne-Klick möglich)
- Oder: Fehlermeldung bei manueller Eingabe außerhalb des Bereichs

**Tags**: [req-006, formvalidierung, bewertung, grenzwert, sterne]

---

### TC-006-067: Task erstellen — Timer-Dauer außerhalb 1–7200 Sekunden

**Anforderung**: REQ-006 §3 — timer_duration_seconds ge=1, le=7200 (max. 2 Stunden)
**Priorität**: Medium
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen**:
- Dialog "Aufgabe erstellen" geöffnet (Nutzer mit Erfahrungsstufe intermediate+)

**Testschritte**:
1. Nutzer gibt im Feld "Timer-Dauer" den Wert 7201 ein
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Fehlermeldung: "Maximale Timer-Dauer: 7200 Sekunden (2 Stunden)"
- Task wird nicht erstellt

**Tags**: [req-006, formvalidierung, timer, grenzwert, max-timer]

---

### TC-006-068: Workflow instanziieren — Keine Pflanze ausgewählt

**Anforderung**: REQ-006 §1 — Workflow-Instantiation erfordert Pflanze
**Priorität**: Medium
**Kategorie**: Formvalidierung

**Vorbedingungen**:
- Workflow-Template-Liste geöffnet
- Instanziierungs-Dialog ist offen

**Testschritte**:
1. Nutzer klickt "Anwenden" ohne eine Pflanze ausgewählt zu haben

**Erwartetes Ergebnis**:
- Fehlermeldung: "Bitte wählen Sie eine Pflanze aus" (oder Feld ist als required markiert)
- Dialog bleibt geöffnet
- Kein API-Aufruf

**Tags**: [req-006, workflow-instanziieren, formvalidierung, pflanze-erforderlich]

---

### TC-006-069: Foto-Upload — Ungültiges Dateiformat

**Anforderung**: REQ-006 §6 DoD — Foto-Upload-Enforcement
**Priorität**: Low
**Kategorie**: Fehlermeldung / Formvalidierung

**Vorbedingungen**:
- Task-Detailseite mit Foto-Upload-Bereich geöffnet

**Testschritte**:
1. Nutzer versucht, eine PDF-Datei in den Foto-Upload-Bereich zu laden

**Erwartetes Ergebnis**:
- Fehlermeldung: "Ungültiger Dateityp — nur Bilder erlaubt (JPEG, PNG, WEBP)" oder ähnlich
- Upload wird abgewiesen

**Tags**: [req-006, foto-upload, dateiformat, fehlermeldung]

---

## Gruppe 15: Mobile-Ansicht und Barrierefreiheit

### TC-006-070: Task-Queue auf mobiler Ansicht

**Anforderung**: REQ-006 §6 DoD — Mobile-Optimierung; UI-NFR (MobileCard)
**Priorität**: Medium
**Kategorie**: Responsive / Mobile

**Vorbedingungen**:
- Browser-Viewport auf mobile Breite gesetzt (< 600px)
- Mindestens 3 Tasks vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/queue` auf mobiler Ansicht

**Erwartetes Ergebnis**:
- Task-Karten werden als vertikale Cards (MobileCard) statt als Tabellen-Zeilen dargestellt
- Aktions-Buttons (Starten, Abschließen, Überspringen) sind als Icon-Buttons auf der Karte sichtbar und touch-freundlich (ausreichende Tap-Fläche)
- Filter-Bereich ist kollabierbar oder als Dropdown zugänglich

**Tags**: [req-006, mobile, responsive, task-queue, touch-friendly]

---

### TC-006-071: Workflow-Template-Liste auf mobilem Viewport

**Anforderung**: REQ-006 / UI-NFR — Mobile Card View
**Priorität**: Low
**Kategorie**: Responsive / Mobile

**Vorbedingungen**:
- Browser-Viewport auf mobile Breite (< 600px)

**Testschritte**:
1. Nutzer navigiert zu `/aufgaben/workflows` auf mobilem Viewport

**Erwartetes Ergebnis**:
- Workflows werden als MobileCards angezeigt statt als Tabelle
- System-Badge und Auto-generiert-Badge sind auf der Card sichtbar
- Play-Button (Instanziieren) und Delete-Button sind erreichbar

**Tags**: [req-006, mobile, responsive, workflow-liste]

---

## Gruppe 16: Navigation und Routing

### TC-006-072: Breadcrumb-Navigation von Task-Queue zur Startseite

**Anforderung**: REQ-006 — Navigation
**Priorität**: Low
**Kategorie**: Navigation

**Vorbedingungen**:
- Nutzer ist auf der Task-Queue-Seite

**Testschritte**:
1. Nutzer klickt auf den Breadcrumb "Dashboard" oder das Haus-Icon

**Erwartetes Ergebnis**:
- Browser navigiert zu `/dashboard`
- Kein Fehler

**Tags**: [req-006, navigation, breadcrumb, dashboard]

---

## Abdeckungsmatrix

| Spezifikationsabschnitt | Testfälle |
|------------------------|-----------|
| §1 Task-Queue (Übersicht, Filter, Gruppierung) | TC-006-001, TC-006-002, TC-006-003, TC-006-004, TC-006-005 |
| §1 Task-Statusübergänge (Starten, Abschließen, Überspringen) | TC-006-006, TC-006-007, TC-006-008 |
| §1 Batch-Operationen (Bulk-Modus, Mehrfachauswahl) | TC-006-009, TC-006-010, TC-006-011 |
| §1 Pflegeerinnerungen-Integration | TC-006-012 |
| §1 Task erstellen (CRUD, Formvalidierung) | TC-006-013, TC-006-014, TC-006-065, TC-006-066, TC-006-067 |
| §1 Checkliste (Teilschritte, Abhaken) | TC-006-015, TC-006-021, TC-006-022 |
| §1 Tags | TC-006-016 |
| §1 Wiederkehrende Aufgaben (Recurrence) | TC-006-017 |
| §1 Timer (W-006, Ad-hoc, nicht-blockierend) | TC-006-018, TC-006-023, TC-006-054, TC-006-055 |
| §1 Task-Detailseite (Tabs, Details, Bearbeiten) | TC-006-019, TC-006-020, TC-006-027 |
| §1 Bewertungen nach Abschluss | TC-006-024 |
| §1 Foto-Upload-Enforcement | TC-006-025, TC-006-026, TC-006-069 |
| §1 Kommentare (CRUD) | TC-006-028, TC-006-029 |
| §1 Änderungshistorie (Audit-Trail) | TC-006-030 |
| §1 Task klonen | TC-006-031 |
| §1 Task wiedereröffnen (Reopen) | TC-006-032 |
| §1 Task löschen | TC-006-033 |
| §1 Workflow-Template-Liste | TC-006-034, TC-006-035, TC-006-036 |
| §1 Workflow aus Spezies generieren | TC-006-037 |
| §1 Workflow instanziieren | TC-006-038, TC-006-068 |
| §1 Workflow-Detailseite (Tabs, Task-Template CRUD) | TC-006-039, TC-006-040, TC-006-041, TC-006-042 |
| §1 HST-Validierung (Topping, Supercropping, Recovery) | TC-006-043, TC-006-044, TC-006-045 |
| §1 Autoflower-Guard | TC-006-046, TC-006-047 |
| §1 Dormant-Status, Phasenwechsel-Hook | TC-006-048, TC-006-049 |
| §1 Dependency-Ketten, Auto-Rescheduling | TC-006-050, TC-006-051 |
| §1 Activity Plans Übersicht | TC-006-052, TC-006-053 |
| §1 Phänologische Ereignisse — Dokumentation (G-005) | TC-006-056 |
| §1 Seasonal-Month-Trigger (G-005) | TC-006-057 |
| §1 Phänologischer Trigger im Task-Template-Dialog konfigurieren (G-005) | TC-006-073 |
| §1 Dormant-Verhalten phänologisch getriggerter Tasks (G-005) | TC-006-074 |
| §1 Phänologischen Trigger auf Kalender-Trigger umstellen (G-005) | TC-006-075 |
| §3 Gießplan-Tasks (Celery-Beat, Idempotenz) | TC-006-058, TC-006-059 |
| §1 Workflow manuell erstellen | TC-006-060 |
| §1 Recovery-Timer, Canopy-Metriken (G-004) | TC-006-061, TC-006-062, TC-006-063, TC-006-064 |
| Mobile-Optimierung | TC-006-070, TC-006-071 |
| Navigation / Routing | TC-006-072 |

---

## Querbezüge zu anderen Anforderungen

| Testfall | Querbezug |
|----------|-----------|
| TC-006-005 | REQ-022 (Pflegeerinnerungen — in Task-Queue integriert) |
| TC-006-012 | REQ-022 (CareProfile-Erinnerungen) |
| TC-006-043–TC-006-047 | REQ-001 (Cultivar.flowering_type für Autoflower-Guard), REQ-003 (Wachstumsphasen) |
| TC-006-048–TC-006-049 | REQ-003 (Phase-Transition-Hook aktiviert dormante Tasks) |
| TC-006-051 | REQ-003 (Phasengebundene Task-Kette) |
| TC-006-058–TC-006-059 | REQ-004 (NutrientPlan + WateringSchedule), REQ-013 (PlantingRun) |
| TC-006-061–TC-006-064 | REQ-013 (PlantInstance), REQ-005 (Canopy-Höhe als Sensorwert) |
| TC-006-073–TC-006-075 | REQ-002 (Standort/Site für observed_at_site-Edge), REQ-001 (Zeigerpflanzen-Vokabular) |
