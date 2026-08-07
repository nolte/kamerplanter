# Aufgaben

Kamerplanter bündelt manuell erstellte Aufgaben, automatisch generierte Pflegeerinnerungen und aus Workflow-Vorlagen erzeugte Aufgabenpakete in einer gemeinsamen Warteschlange. Du behältst jederzeit die volle Kontrolle: Aufgaben können angepasst, gebündelt bearbeitet und flexibel verwaltet werden.

---

## Voraussetzungen

- Mindestens eine angelegte Pflanze oder ein aktiver Pflanzdurchlauf
- Für automatische Pflegeerinnerungen: ein Pflegeprofil (wird automatisch beim ersten Zugriff erstellt) — siehe [Pflegeerinnerungen](care-reminders.md)

---

## Aufgaben in der Übersicht

Öffne **Aufgaben** in der Navigation (`/aufgaben/queue`). Die Übersicht gruppiert alle Einträge nach Dringlichkeit:

- **Überfällig**: Fälligkeitsdatum überschritten (rot markiert)
- **Heute**: Heute fällig
- **Diese Woche**: Fällig in den nächsten 7 Tagen
- **Zukunft**: Alles Weitere ohne festes Fälligkeitsdatum bzw. später fällig

Über den Filter **Quelle** (Alle / Aufgaben / Pflege) blendest du wahlweise nur manuell/aus Workflows erstellte Aufgaben, nur automatische Pflegeerinnerungen oder beides gemeinsam ein.

Jede Aufgabe zeigt:

- Titel und Kategorie
- Zugehörige Pflanze bzw. Pflanzdurchlauf
- Priorität (Niedrig / Mittel / Hoch / Kritisch), sofern von „Mittel" abweichend
- Fälligkeitsdatum

---

## Aufgaben-Kategorien

Kamerplanter kennt zwölf Aufgaben-Kategorien:

| Kategorie | Beschreibung |
|-----------|-------------|
| Wartung | Allgemeine Pflegearbeiten |
| Düngung | Düngeereignisse |
| Training | High-/Low-Stress-Training (HST/LST)-Maßnahmen |
| Schnitt | Rückschnitt |
| Ausgeizen | Entfernen von Geiztrieben (v.a. Tomaten) |
| Umtopfen | Umtopf-Termine |
| Pflanzenschutz | Maßnahmen des Integrierten Pflanzenschutzes (IPM) |
| Ernte | Erntetermine |
| Beobachtung | Reifebeobachtung, Kontrollgänge |
| Pflegeerinnerung | Automatisch aus dem Pflegeprofil erzeugt |
| Saisonale Aufgabe | An die Jahreszeit gebundene Aufgaben |
| Phänologische Aufgabe | An Naturereignisse gebundene Aufgaben |

<!-- Quelle: src/backend/app/common/enums.py (TaskCategory) -->

!!! note "Kein eigener Aufgabentyp Gießen"
    Es gibt keine eigene Kategorie „Gießen". Automatische Gieß-Erinnerungen laufen über die Kategorie **Pflegeerinnerung**; manuelle Bewässerungs-Aufgaben legst du unter **Wartung** oder **Beobachtung** an, je nach Kontext.

---

## Woher Aufgaben kommen

- **Manuell erstellt**: über den Button **Aufgabe erstellen**
- **Aus Workflow-Vorlagen**: durch Anwenden eines Workflow-Templates (siehe unten)
- **Automatisch als Pflegeerinnerung**: aus dem Pflegeprofil einer Pflanze (Gießen, Düngen, Umtopfen, Schädlingskontrolle, Standort-Check, Luftfeuchte-Check) — siehe [Pflegeerinnerungen](care-reminders.md)

---

## Eine manuelle Aufgabe erstellen

### Schritt 1: Neue Aufgabe anlegen

Klicke in der Aufgaben-Übersicht auf **Aufgabe erstellen**.

### Schritt 2: Aufgabe beschreiben

| Feld | Beschreibung |
|------|-------------|
| Name | Kurze, prägnante Beschreibung der Aufgabe (Pflichtfeld) |
| Anleitung | Schrittweise Anleitung zur Durchführung |
| Kategorie | Eine der zwölf Aufgaben-Kategorien |
| Fälligkeitsdatum | Wann muss die Aufgabe erledigt sein? |
| Priorität | Niedrig / Mittel / Hoch / Kritisch |
| Geschätzte Dauer (Min.) | Für die Zeitplanung |
| Pflanze | Zuordnung zu einer Pflanze |

Weitere Felder — **Fähigkeitsstufe**, **Wiederholung**, **Zugewiesen an**, **Timer-Dauer/-Bezeichnung** und **Tags** — erscheinen erst ab der Erfahrungsstufe „Fortgeschritten" (Einstellungen → Erfahrungsstufe).

### Schritt 3: Checkliste (optional)

Füge beliebig viele Checklisten-Punkte hinzu (Enter zum Bestätigen). Die Checkliste dient der eigenen Übersicht während der Durchführung — sie blockiert das Abschließen der Aufgabe nicht.

### Schritt 4: Speichern

Die Aufgabe erscheint sofort in der Aufgaben-Übersicht und im Kalender.

---

## Aufgabe als erledigt markieren

### Einzelne Aufgabe abschließen

1. Öffne die Aufgabe durch Klick auf den Titel.
2. Klicke auf **Starten**, um sie in Bearbeitung zu setzen (optional, aktiviert bei Bedarf den Timer).
3. Klicke auf **Abschließen**. Optional trägst du Notizen, die tatsächliche Dauer sowie eine Schwierigkeits- und Qualitätsbewertung (1–5) ein.
4. Bestätige.

!!! warning "Foto-Pflicht"
    Ist bei der Aufgabe **Foto erforderlich** aktiviert, blockiert Kamerplanter den Abschluss, bis mindestens ein Foto hochgeladen wurde.

### Aufgabe direkt aus der Listenansicht abhaken

Klicke auf das Häkchen-Symbol neben einer Aufgabe in der Liste. Die Aufgabe wird sofort als erledigt markiert (sofern kein Foto erforderlich ist).

### Timer

Hat eine Aufgabe eine Timer-Dauer hinterlegt (z.B. bei Mischprotokollen: „Rühren & warten"), erscheint der Countdown-Timer, sobald du die Aufgabe startest.

---

## Eine Aufgabe nachträglich ändern

Öffne die Aufgabe und wechsle in den Tab **Bearbeiten**. Dort passt du dieselben Felder an, die du beim Anlegen ausgefüllt hast, und speicherst mit **Speichern**.

!!! tip "Fehlerhinweise stehen direkt am Feld"
    Ist eine Eingabe unzulässig — ein leerer **Name**, eine geschätzte Dauer unter einer Minute —, wird das Speichern abgebrochen und der Grund erscheint als roter Hinweistext unter dem betroffenen Feld. Das gilt genauso für den Tab **Abschließen**. Zuvor griff in diesen Fällen die Prüfung des Browsers zuerst: Sie zeigte eine kurz eingeblendete Sprechblase in der Sprache des Browsers, verschwand beim nächsten Klick wieder und ließ das Formular ungespeichert zurück, ohne dass am Feld selbst etwas markiert war. <!-- REQ-006 -->

---

## Mehrere Aufgaben auf einmal bearbeiten

Wenn viele Aufgaben gleichzeitig anfallen, kannst du sie gebündelt bearbeiten, statt jede einzeln anzufassen.

1. Klicke in der Aufgaben-Übersicht oben rechts auf **Mehrere auswählen**. (Der Button erscheint, sobald mindestens eine Aufgabe vorhanden ist.)
2. Neben jeder Aufgabe erscheint eine Auswahl-Checkbox. Hake die gewünschten Aufgaben an — oder nutze **Alle auswählen** in der Aktionsleiste.
3. Wähle in der Aktionsleiste die gewünschte Sammelaktion:
    - **Abschließen** — alle markierten Aufgaben werden als erledigt markiert.
    - **Überspringen** — alle markierten Aufgaben werden übersprungen.
    - **Löschen** — alle markierten Aufgaben werden entfernt.
4. Über **Abbrechen** verlässt du den Auswahlmodus wieder, ohne etwas zu ändern.

---

## Workflow-Templates nutzen

Workflow-Templates sind vordefinierte Aufgabenpakete für wiederkehrende Pflegeszenarien. Ein Template anzuwenden bedeutet: Das System erstellt daraus eine Reihe konkreter Aufgaben für deine Pflanze, deinen Durchlauf, einen Standort oder einen Tank.

### Schritt 1: Template auswählen

Navigiere zu **Aufgaben → Workflow-Templates** (`/aufgaben/workflows`). Kamerplanter liefert vier System-Vorlagen aus:

| Template | Zielentität | Kategorie | Beschreibung |
|----------|-------------|-----------|-------------|
| Cannabis SOG | Pflanze | Ernte | Sea-of-Green-Ablauf für Cannabis, von Umtopfen in SOG-Position bis zur Ernte (6 Aufgaben über Vegetativ- und Blütephase) |
| Tomato Standard | Pflanze | Wartung | Standard-Tomatenanbau: Umpflanzen, Rankhilfe, Ausgeizen, wöchentliches Düngen, Reifebeobachtung, Ernte |
| General Maintenance | Pflanze | Wartung | Allgemeine wiederkehrende Kontroll- und Pflegeaufgaben, unabhängig von der Pflanzenart |
| Tank Anmischen | Tank | Düngung | Schritt-für-Schritt-Mischprotokoll für Nährstofflösungen in der korrekten Mischreihenfolge, inklusive Rühr- und Wartezeiten-Timer |

<!-- Quelle: src/backend/app/migrations/seed_data/workflows.yaml -->

!!! tip "Aufgaben passen sich der Wachstumsphase an"
    Aufgaben, die an eine bestimmte Wachstumsphase gebunden sind (z.B. „Auf 12/12 umstellen" bei Cannabis SOG), werden beim Anwenden mit dem Status **Ruhend** angelegt und erst aktiviert, sobald die Pflanze diese Phase tatsächlich erreicht.

!!! note "System-Vorlagen sind schreibgeschützt — dupliziere sie zum Anpassen"
    Die vier System-Vorlagen gehören zum Systemkatalog und stehen allen Mandanten gleichermaßen zur Verfügung. Deshalb lassen sich weder ihre Phasen noch ihre Aufgabenvorlagen ändern — auf der Detailseite einer System-Vorlage fehlen entsprechend die Schaltflächen zum Hinzufügen, Bearbeiten und Löschen von Phasen und Aufgabenvorlagen, und auch der Aktiv-Schalter sowie das Tage-Offset-Feld einzelner Aufgabenvorlagen sind deaktiviert. Möchtest du eine System-Vorlage an deine Bedürfnisse anpassen, **dupliziere** sie zunächst über die Schaltfläche **Duplizieren** in der Workflow-Übersicht: Die Kopie übernimmt alle Phasen und Aufgabenvorlagen und gehört danach vollständig dir — sie ist frei bearbeitbar.

### Schritt 2: Template anwenden

1. Klicke auf **Template anwenden** neben dem gewünschten Template.
2. Wähle die passende Zielentität (Pflanze, Pflanzdurchlauf, Standort oder Tank — je nach Template).
3. Bestätige — alle Aufgaben werden sofort angelegt. Fälligkeitsdaten berechnen sich ab dem heutigen Tag entsprechend der im Template hinterlegten Tage-Offsets.

### Eigene Templates erstellen

Wenn du eine Abfolge von Aufgaben öfter nutzt, kannst du ein eigenes Template anlegen:

1. Navigiere zu **Aufgaben → Workflow-Templates → Neues Template**.
2. Gib Name, Beschreibung, Kategorie und Zielentität(en) an.
3. Öffne das neu angelegte Template und füge über **Aufgabe hinzufügen** einzelne Aufgabenvorlagen mit Titel, Anleitung, Kategorie, Auslöser und Tage-Offset hinzu.
4. Das Template steht danach für alle deine Pflanzen bzw. Zielentitäten zur Verfügung.

!!! note "Erfahrungsstufe empfohlen"
    Der Workflow-Editor richtet sich an erfahrene Nutzer — einige Dropdown-Felder verwenden technische Bezeichnungen. Für den Einstieg eignen sich die vier System-Templates meist besser als ein komplett neu erstelltes Template.

---

## Aktivitätspläne

Für einen einzelnen Pflanzdurchlauf kannst du zusätzlich einen **Aktivitätsplan** anwenden — eine aus den hinterlegten Aktivitäten der Pflanzenart abgeleitete Aufgabenvorschlagsliste. Du findest ihn im Tab **Aktivitätsplan** auf der Detailseite des Pflanzdurchlaufs. Mehr dazu: [Pflanzdurchläufe](planting-runs.md).

---

## Pflegeerinnerungen

Automatisch generierte Gieß-, Dünge- und weitere Pflegeerinnerungen sind kein separater Bereich, sondern erscheinen in derselben Aufgaben-Übersicht (Quellen-Filter „Pflege"). Wie das Pflegeprofil funktioniert, welche Erinnerungstypen es gibt und wie die Eskalation abläuft, erfährst du unter [Pflegeerinnerungen](care-reminders.md).

Schließt du eine Gieß-Erinnerung hier in der Warteschlange ab, legt Kamerplanter die nächste Gieß-Aufgabe sofort mit an — siehe [Die nächste Gieß-Aufgabe entsteht sofort](care-reminders.md#naechste-giess-aufgabe).

---

## Aufgaben filtern

In der Aufgaben-Übersicht stehen folgende Filter zur Verfügung:

- **Quelle**: Alle / Aufgaben / Pflege
- **Kategorie**: eine der zwölf Aufgaben-Kategorien (nur für die Quelle „Aufgaben")
- **Pflanze**: auf eine bestimmte Pflanze eingrenzen

!!! note "Kein Filter nach Standort, Priorität oder Tags"
    Diese Filter existieren in der Aufgaben-Übersicht aktuell nicht.

---

## Häufige Fragen

??? question "Kann ich eine automatisch erstellte Aufgabe löschen?"
    Ja, sofern sie sich im Status Ausstehend, Übersprungen oder Ruhend befindet. Bereits gestartete oder abgeschlossene Aufgaben lassen sich nicht mehr löschen. Wenn du eine offene Pflegeerinnerung löschst, erstellt Kamerplanter beim nächsten täglichen Planungsdurchlauf bei Bedarf eine neue — sofern das Pflegeprofil noch aktiv ist.

??? question "Was passiert mit den Aufgaben, wenn ich eine Pflanze entferne?"
    Wenn du eine Pflanze entfernst, werden ihre noch offenen Aufgaben (ausstehend, in Bearbeitung, ruhend) automatisch aus der Warteschlange entfernt. Bereits erledigte, übersprungene oder fehlgeschlagene Aufgaben bleiben als Verlauf erhalten. Für entfernte Pflanzen werden außerdem keine neuen automatischen Pflegeerinnerungen mehr erzeugt.

??? question "Eskaliert Kamerplanter überfällige Aufgaben automatisch?"
    Nur für **Gieß-Erinnerungen**: Bleibt eine Gieß-Erinnerung unbestätigt, erhöht das System die Dringlichkeit der Benachrichtigung nach 2 Tagen auf „Hoch" und nach 4 Tagen auf „Kritisch"; nach 7 Tagen folgt eine letzte Warnung. Für andere Aufgabentypen gibt es keine automatische Eskalation — die rote Überfällig-Markierung ist hier nur ein visueller Hinweis.

??? question "Kann ich wiederkehrende Aufgaben anlegen?"
    Ja, direkt beim Erstellen einer Aufgabe über das Feld **Wiederholung** (täglich/wöchentlich/zweiwöchentlich/monatlich) — sichtbar ab der Erfahrungsstufe „Fortgeschritten". Sobald du eine wiederkehrende Aufgabe abschließt, legt Kamerplanter automatisch die nächste Instanz an.

??? question "Kann ich Aufgaben an andere Mitglieder meines Mandanten zuweisen?"
    Ja, wenn du in einem Gemeinschaftsgarten (mit mehreren Mitgliedern) arbeitest. Öffne die Aufgabe und trage im Feld **Zugewiesen an** den entsprechenden Nutzer ein (sichtbar ab Erfahrungsstufe „Fortgeschritten").

---

## Siehe auch

- [Kalender](calendar.md)
- [Pflegeerinnerungen](care-reminders.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Integrierter Pflanzenschutz](pest-management.md)
