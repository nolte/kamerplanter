---
req_id: REQ-015
title: Kalenderansicht & Kalender-Integration (iCal/webcal)
category: Visualisierung & Integration
test_count: 52
coverage_areas:
  - Monatsansicht (§3.7)
  - Listenansicht / Agenda-Modus (§3.7)
  - Phasen-Timeline-Ansicht (§3.7)
  - Aussaatkalender-Modus (§3.8, REQ-015-A)
  - Saisonübersicht-Modus (§3.9)
  - Kategorie-Filter (§3.7)
  - Location-Filter (§3.7)
  - Timeline-Toggle (§3.7)
  - Event-Popover & Navigation (§3.7)
  - Feed-Management CRUD (§4.3)
  - iCal-Export & webcal-URL (§4.2)
  - Token-Rotation (§4.3)
  - Frosttermin-Konfiguration (§3.8, REQ-015-A §4)
  - Aussaatbalken-Berechnung (REQ-015-A §3)
  - Mehrere Anbauzeitraeume / GrowingPeriod (REQ-015-A §6)
  - Zierpflanzen-Bluetebalken (REQ-015-A §3.5)
  - Jahresuebergreifende Kulturen (REQ-015-A §3.3)
  - Jahresvergleich (§3.8.1)
  - Responsive-Verhalten (§3.7)
generated: 2026-03-21
version: "1.5 (REQ-015) / 1.2 (REQ-015-A)"
---

# Testfaelle: REQ-015 Kalenderansicht & Kalender-Integration

> Alle Testfaelle sind aus der **Nutzerperspektive im Browser** formuliert.
> Keine API-Aufrufe, HTTP-Codes oder Datenbankabfragen in den Testschritten.
> Phaenomensprache: was der Nutzer sieht, klickt, eingibt und erwartet.

---

## Abschnitt A — Grundlegende Kalenderansicht (`/kalender`)

---

### TC-015-001: Kalenderseite aufrufen — Standardansicht Monat

**Zusammenfassung:** Nutzer navigiert zur Kalenderseite und sieht die Monatsansicht als Standarddarstellung.

**Anforderung:** REQ-015 §3.7 — Kalenderseite (`/kalender`), Monatsansicht als Desktop-Default
**Prioritaet:** Critical
**Kategorie:** Happy Path / Navigation
**Tags:** [req-015, kalender, monatsansicht, navigation, routing]

**Vorbedingungen:**
- Nutzer ist eingeloggt und Mitglied eines Tenants
- Mindestens ein Task existiert im aktuellen Monat

**Testschritte:**
1. Nutzer navigiert in der Seitenleiste auf den Menuepunkt "Kalender" (oder oeffnet direkt `/kalender`)
2. Nutzer betrachtet die angezeigte Seite

**Erwartetes Ergebnis:**
- Die Seite zeigt den Titel "Kalender"
- Eine Monatsgitter-Ansicht (7 Spalten fuer Mo–So) wird angezeigt
- Die Navigationsleiste zeigt Ansicht-Tabs: "Monatsansicht", "Listenansicht" sowie weitere Ansichts-Schaltflaechen
- Der aktuelle Monat und das aktuelle Jahr sind in der Kopfzeile sichtbar (z.B. "Maerz 2026")
- Pfeil-Schaltflaechen (`◀` / `▶`) zum Blaettern zwischen Monaten sind sichtbar
- Eine "Heute"-Schaltflaeche ist vorhanden
- Der aktuelle Tag ist im Grid visuell hervorgehoben
- In der linken Sidebar sind Kategorie-Filter mit Checkboxen sichtbar
- Tasks des aktuellen Monats erscheinen als farbkodierte Bloecke in den entsprechenden Tages-Zellen

**Nachbedingungen:** Keine Datenaenderung.

---

### TC-015-002: Monatsnavigation — Naechsten Monat aufrufen

**Zusammenfassung:** Nutzer navigiert mit dem Pfeil-Button zum naechsten Monat.

**Anforderung:** REQ-015 §3.7 — Navigation zwischen Monaten
**Prioritaet:** High
**Kategorie:** Navigation
**Tags:** [req-015, monatsansicht, navigation, paginierung]

**Vorbedingungen:**
- Nutzer befindet sich auf der Kalenderseite in der Monatsansicht

**Testschritte:**
1. Nutzer notiert sich den aktuell angezeigten Monat und das Jahr (z.B. "Maerz 2026")
2. Nutzer klickt auf die Pfeil-Schaltflaeche `▶` (naechster Monat)

**Erwartetes Ergebnis:**
- Die Kopfzeile zeigt den Folgemonat an (z.B. "April 2026")
- Das Monatsgrid aktualisiert sich und zeigt die Tage des neuen Monats
- Events des neuen Monats werden geladen und angezeigt

---

### TC-015-003: Monatsnavigation — Zurueck zum aktuellen Monat

**Zusammenfassung:** Nutzer navigiert mehrere Monate vor und kehrt per "Heute"-Schaltflaeche zum aktuellen Monat zurueck.

**Anforderung:** REQ-015 §3.7 — "Heute"-Schaltflaeche
**Prioritaet:** Medium
**Kategorie:** Navigation
**Tags:** [req-015, monatsansicht, heute-button, navigation]

**Vorbedingungen:**
- Nutzer ist auf der Kalenderseite und hat per `▶▶` zu einem anderen Monat navigiert

**Testschritte:**
1. Nutzer klickt zweimal auf `▶` und landet z.B. bei "Mai 2026"
2. Nutzer klickt auf die "Heute"-Schaltflaeche

**Erwartetes Ergebnis:**
- Die Kopfzeile zeigt wieder den aktuellen Monat und das aktuelle Jahr
- Der heutige Tag ist im Grid hervorgehoben

---

### TC-015-004: Ansichtswechsel — Listenansicht

**Zusammenfassung:** Nutzer wechselt von der Monatsansicht in die Listenansicht.

**Anforderung:** REQ-015 §3.7 — Listenansicht / Agenda-Modus
**Prioritaet:** High
**Kategorie:** Navigation / Ansichtswechsel
**Tags:** [req-015, listenansicht, ansichtswechsel]

**Vorbedingungen:**
- Nutzer ist auf der Kalenderseite in der Monatsansicht
- Mindestens 3 Tasks existieren im aktuellen Zeitraum

**Testschritte:**
1. Nutzer klickt auf den Tab bzw. die Schaltflaeche "Listenansicht"

**Erwartetes Ergebnis:**
- Die Gitter-Darstellung verschwindet
- Eine chronologisch sortierte Liste von Events erscheint
- Jeder Listeneintrag zeigt: farbigen Indikator (Kategorie-Farbe), Titel, Datum/Uhrzeit und Prioritaet
- Die Filteroptionen in der Sidebar bleiben erhalten und aktiv

---

### TC-015-005: Ansichtswechsel — Aussaatkalender-Tab

**Zusammenfassung:** Nutzer wechselt in den Aussaatkalender-Modus.

**Anforderung:** REQ-015 §3.7 / §3.8 — Aussaatkalender als fuenfter Ansichtsmodus
**Prioritaet:** High
**Kategorie:** Navigation / Ansichtswechsel
**Tags:** [req-015, aussaatkalender, ansichtswechsel]

**Vorbedingungen:**
- Nutzer ist auf der Kalenderseite
- Mindestens eine Site ist konfiguriert

**Testschritte:**
1. Nutzer klickt auf den Aussaat-Tab (gekennzeichnet mit Pflanzensymbol / "Aussaatkalender")

**Erwartetes Ergebnis:**
- Die Monatsansicht wird durch die Aussaatkalender-Ansicht (`SowingCalendarView`) ersetzt
- Eine horizontale Zeitbalken-Tabelle erscheint mit Monatsspalten (Jan bis Dez)
- In der Sidebar oder Kopfzeile ist eine Standort-Auswahl fuer die Site sichtbar
- Die Titel-Zeile zeigt "Aussaatkalender [Jahr]"

---

### TC-015-006: Ansichtswechsel — Saisonuebersicht-Tab

**Zusammenfassung:** Nutzer wechselt in den Saisonuebersicht-Modus.

**Anforderung:** REQ-015 §3.9 — Saisonuebersicht als sechster Ansichtsmodus
**Prioritaet:** High
**Kategorie:** Navigation / Ansichtswechsel
**Tags:** [req-015, saisonuebersicht, ansichtswechsel]

**Vorbedingungen:**
- Nutzer ist auf der Kalenderseite

**Testschritte:**
1. Nutzer klickt auf den Saisonuebersicht-Tab (Balkendiagramm-Symbol / "Saisonuebersicht")

**Erwartetes Ergebnis:**
- 12 Monatskarten werden in einem Grid-Layout angezeigt (3x4 oder 4x3)
- Jede Karte zeigt: Monatsname, Anzahl Aussaaten, Anzahl Ernten, Anzahl Tasks
- Der aktuelle Monat ist visuell hervorgehoben (dunklerer Hintergrund oder Rahmen)

---

### TC-015-007: Phasen-Timeline-Ansicht aufrufen

**Zusammenfassung:** Nutzer wechselt in die Phasen-Timeline-Ansicht.

**Anforderung:** REQ-015 §3.7 — PhaseTimelineView
**Prioritaet:** Medium
**Kategorie:** Navigation / Ansichtswechsel
**Tags:** [req-015, phasen-timeline, ansichtswechsel]

**Vorbedingungen:**
- Nutzer ist auf der Kalenderseite

**Testschritte:**
1. Nutzer klickt auf den Timeline-Tab (Timeline-Symbol)

**Erwartetes Ergebnis:**
- Die `PhaseTimelineView`-Komponente wird angezeigt
- Titel "Phasen-Timeline" ist sichtbar
- Schaltflaechen zum Filtern nach Durchlaeufen und Pflanzen sind vorhanden

---

## Abschnitt B — Kategorie- und Standort-Filterung

---

### TC-015-010: Kategorie-Filter — Einzelne Kategorie aktivieren

**Zusammenfassung:** Nutzer filtert den Kalender auf eine einzelne Kategorie und sieht nur Events dieser Kategorie.

**Anforderung:** REQ-015 §3.7 — Filter nach Kategorie; §7 Akzeptanzkriterium "Filter ... funktionieren einzeln"
**Prioritaet:** High
**Kategorie:** Filterung / Happy Path
**Tags:** [req-015, filter, kategorie, happy-path]

**Vorbedingungen:**
- Der Kalender zeigt Events mindestens zweier verschiedener Kategorien im aktuellen Monat
- Alle Kategorien sind initial aktiv (alle Checkboxen angehakt)

**Testschritte:**
1. Nutzer deaktiviert alle Kategorien per Klick auf jede Checkbox ausser "Duengung"
2. Nutzer betrachtet das aktualisierte Monatsgrid

**Erwartetes Ergebnis:**
- Nur Events der Kategorie "Duengung" (blaue Farbe, `#2196F3`) sind noch sichtbar
- Events aller anderen Kategorien sind aus dem Grid verschwunden
- Das Grid zeigt keine Fehlermeldung, sondern nur die verbleibenden Events

---

### TC-015-011: Kategorie-Filter — Alle Kategorien deaktivieren (Leerszustand)

**Zusammenfassung:** Nutzer deaktiviert alle Kategorien und sieht einen leeren Kalender.

**Anforderung:** REQ-015 §3.7 — Leerzustand bei aktiven Filtern
**Prioritaet:** Medium
**Kategorie:** Filterung / Fehlermeldung / Leerszustand
**Tags:** [req-015, filter, leerszustand, empty-state]

**Vorbedingungen:**
- Nutzer ist auf der Kalenderseite in der Monatsansicht mit sichtbaren Events

**Testschritte:**
1. Nutzer deaktiviert alle Kategorie-Checkboxen nacheinander

**Erwartetes Ergebnis:**
- Das Kalendergrid bleibt strukturell erhalten (Tages-Zellen sichtbar)
- In den Tages-Zellen erscheinen keine Events mehr
- Kein Fehler-Dialog, keine Fehlermeldung

---

### TC-015-012: Standort-Filter — Events eines Standorts isolieren

**Zusammenfassung:** Nutzer filtert den Kalender nach einem bestimmten Standort und sieht nur dessen Events.

**Anforderung:** REQ-015 §3.7 — Filter nach Location; §7 Testszenario 2
**Prioritaet:** High
**Kategorie:** Filterung / Happy Path
**Tags:** [req-015, filter, standort, location]

**Vorbedingungen:**
- Mindestens 2 Standorte existieren (z.B. "Zelt 1" und "Garten")
- Beide haben Tasks im aktuellen Monat (z.B. 4 fuer "Zelt 1", 6 fuer "Garten")

**Testschritte:**
1. Nutzer oeffnet den Standort-Filter (Dropdown oder Baumstruktur "PlantFilterTree")
2. Nutzer waehlt "Zelt 1" aus

**Erwartetes Ergebnis:**
- Im Kalender sind nur noch die 4 Events fuer "Zelt 1" sichtbar
- Events des anderen Standorts ("Garten") sind ausgeblendet

---

### TC-015-013: Pflanzenstamm-Filter — Events einer Pflanzeninstanz isolieren

**Zusammenfassung:** Nutzer filtert auf eine einzelne Pflanzeninstanz.

**Anforderung:** REQ-015 §3.7 — Filter nach Pflanze (PlantFilterTree)
**Prioritaet:** Medium
**Kategorie:** Filterung / Happy Path
**Tags:** [req-015, filter, pflanze, plantfilter]

**Vorbedingungen:**
- Mindestens ein Pflanzdurchlauf mit Pflanzeninstanzen und zugeordneten Tasks existiert

**Testschritte:**
1. Nutzer klickt auf "Nach Pflanze / Durchlauf filtern"
2. Im `PlantFilterTree`-Panel waehlt Nutzer eine konkrete Pflanzeninstanz aus
3. Nutzer betrachtet den Kalender

**Erwartetes Ergebnis:**
- Nur Tasks dieser Pflanzeninstanz sind im Kalender sichtbar
- Die Pflanzenfilter-Auswahl bleibt aktiviert und ist sichtbar markiert

---

### TC-015-014: Kombinierter Filter — Kategorie + Standort

**Zusammenfassung:** Nutzer kombiniert Kategorie- und Standort-Filter und sieht die Schnittmenge.

**Anforderung:** REQ-015 §7 Akzeptanzkriterium "Filter ... funktionieren ... kombiniert"
**Prioritaet:** High
**Kategorie:** Filterung / Happy Path
**Tags:** [req-015, filter, kombiniert, kategorie, standort]

**Vorbedingungen:**
- Mindestens 2 Kategorien und 2 Standorte mit Tasks sind vorhanden

**Testschritte:**
1. Nutzer setzt Kategorie-Filter auf nur "IPM" (Pflanzenschutz)
2. Nutzer setzt Standort-Filter auf "Zelt 1"

**Erwartetes Ergebnis:**
- Nur IPM-Tasks, die dem Standort "Zelt 1" zugeordnet sind, erscheinen im Kalender
- Tasks mit IPM-Kategorie bei anderem Standort sind nicht sichtbar
- Tasks anderer Kategorien bei Standort "Zelt 1" sind nicht sichtbar

---

## Abschnitt C — Timeline-Toggle & Event-Interaktion

---

### TC-015-020: Timeline-Toggle — Vergangene Events einblenden

**Zusammenfassung:** Nutzer aktiviert den Timeline-Toggle und sieht zusaetzliche historische Events.

**Anforderung:** REQ-015 §3.7 — Timeline-Toggle; §7 Testszenario 4
**Prioritaet:** High
**Kategorie:** Zustandswechsel / Happy Path
**Tags:** [req-015, timeline, toggle, zustandswechsel]

**Vorbedingungen:**
- Mindestens 5 aktive Tasks im aktuellen Zeitraum
- Mindestens 3 abgeschlossene Phasentransitionen im Zeitraum in `phase_histories`

**Testschritte:**
1. Nutzer notiert die Anzahl sichtbarer Events (z.B. 5 Tasks)
2. Timeline-Checkbox ist initial deaktiviert
3. Nutzer aktiviert die Checkbox "Timeline anzeigen"

**Erwartetes Ergebnis:**
- Zusaetzliche Events erscheinen im Kalender (Phasentransitionen, Tank-Wartungen, Bewaesserungen)
- Phasentransitionen erscheinen als violette (`#9C27B0`) Events mit Titel-Format "Phase: [VonPhase] → [ZurPhase]"
- Die Gesamtanzahl sichtbarer Events erhoeht sich (z.B. von 5 auf 8)
- Historische Events sind als "abgeschlossen" markiert (andere visuelle Darstellung als offene Tasks)

---

### TC-015-021: Timeline-Toggle — Vergangene Events ausblenden

**Zusammenfassung:** Nutzer deaktiviert den Timeline-Toggle und die historischen Events verschwinden.

**Anforderung:** REQ-015 §3.7 — Timeline-Toggle
**Prioritaet:** Medium
**Kategorie:** Zustandswechsel
**Tags:** [req-015, timeline, toggle, zustandswechsel]

**Vorbedingungen:**
- Timeline-Toggle ist aktiviert, Nutzer sieht gemischte Events

**Testschritte:**
1. Nutzer deaktiviert die Checkbox "Timeline anzeigen"

**Erwartetes Ergebnis:**
- Historische Events (Phasentransitionen, Wartungen, Bewaesserungen) verschwinden
- Nur aktive Tasks sind noch sichtbar
- Die Anzahl der Events nimmt entsprechend ab

---

### TC-015-022: Event-Klick — Popover mit Details

**Zusammenfassung:** Nutzer klickt auf ein Event im Kalender und sieht ein Detail-Popover.

**Anforderung:** REQ-015 §3.7 — Event-Interaktion: "Click auf Event: Popover mit Details"
**Prioritaet:** Critical
**Kategorie:** Detailansicht / Happy Path
**Tags:** [req-015, event, popover, detail, interaktion]

**Vorbedingungen:**
- Mindestens ein Task-Event ist im Monatskalender sichtbar

**Testschritte:**
1. Nutzer klickt auf ein Event-Baustein im Kalendergrid

**Erwartetes Ergebnis:**
- Ein Popover (schwebende Karte) erscheint neben dem angeklickten Event
- Das Popover zeigt: Titel des Events, Beschreibung/Anweisung (falls vorhanden), Kategorie (als farbigen Chip), Prioritaet, Status
- Wenn dem Event ein Standort zugeordnet ist, erscheint der Standortname
- Eine Schaltflaeche "Details anzeigen" ist vorhanden, die zur Quell-Entitaet navigiert (Task-Detailseite oder Pflanzeninstanz-Seite)
- Drag & Drop ist nicht moeglich (Events sind nicht verschiebbar)

---

### TC-015-023: Event-Klick — Navigation zur Quell-Entitaet

**Zusammenfassung:** Nutzer klickt im Popover auf "Details anzeigen" und landet auf der Quell-Seite.

**Anforderung:** REQ-015 §3.7 — "Click-through: Link zur Quell-Entitaet"
**Prioritaet:** High
**Kategorie:** Navigation / Happy Path
**Tags:** [req-015, navigation, task-detail, click-through]

**Vorbedingungen:**
- Ein Task-Event ist im Kalender sichtbar
- Das zugehoerige Popover ist geoeffnet (aus TC-015-022)

**Testschritte:**
1. Nutzer klickt im Popover auf die Schaltflaeche "Details anzeigen" (oder Link-Symbol)

**Erwartetes Ergebnis:**
- Browser navigiert zur Task-Detailseite (`/aufgaben/tasks/[task_key]`)
- Die Task-Detailseite zeigt die korrekten Daten des angeklickten Tasks
- Bei einem Phasentransitions-Event fuehrt der Link zur Pflanzeninstanz-Seite (`/pflanzen/plant-instances/[key]`)

---

### TC-015-024: Bewässerungsvoranschau-Event bestaetigen

**Zusammenfassung:** Nutzer bestaetigt einen Gießplan-Vorschau-Event direkt im Kalender.

**Anforderung:** REQ-015 §3.7 — "Gegossen"-Schaltflaeche fuer Watering-Forecast-Events
**Prioritaet:** High
**Kategorie:** Zustandswechsel / Happy Path
**Tags:** [req-015, watering, gießplan, bestaetigen, zustandswechsel]

**Vorbedingungen:**
- Mindestens ein Gießplan-Vorschau-Event (Kategorie "Gießplan-Vorschau", blaue Farbe `#42A5F5`) existiert im Kalender

**Testschritte:**
1. Nutzer klickt auf ein Gießplan-Vorschau-Event
2. Im Popover klickt Nutzer auf die Schaltflaeche "Gegossen"

**Erwartetes Ergebnis:**
- Eine Erfolgs-Benachrichtigung erscheint: "Gießvorgang protokolliert — Vorschau wird aktualisiert"
- Das Event verschwindet aus dem Vorschau-Bereich oder wechselt seinen Status auf "abgeschlossen"

---

## Abschnitt D — Feed-Management

---

### TC-015-030: Feed erstellen — Happy Path

**Zusammenfassung:** Nutzer erstellt einen neuen iCal-Feed mit Namen und erhalt eine webcal-URL.

**Anforderung:** REQ-015 §4.3 — POST /api/v1/calendar/feeds; §7 DoD "Feed-CRUD ... funktioniert ueber UI-Dialog"
**Prioritaet:** Critical
**Kategorie:** Happy Path / Dialog / Feed-Management
**Tags:** [req-015, feed, erstellen, ical, webcal, dialog]

**Vorbedingungen:**
- Nutzer ist eingeloggt und auf der Kalenderseite

**Testschritte:**
1. Nutzer klappt den Bereich "iCal-Feeds" in der Seitenleiste auf (oder klickt auf Feed-Symbol)
2. Nutzer klickt auf "Feed erstellen" (oder "+ Neuen Feed erstellen")
3. In dem erscheinenden Dialog gibt Nutzer als Feed-Name "Mein Hauptkalender" ein
4. Nutzer klickt auf "Erstellen" (oder "Speichern")

**Erwartetes Ergebnis:**
- Der Dialog schliesst sich
- Der neue Feed "Mein Hauptkalender" erscheint in der Feed-Liste
- Eine `webcal://`-URL wird fuer den Feed angezeigt (Format: `webcal://[host]/api/v1/calendar/feeds/[feed_id]/feed.ics?token=[token]`)
- Eine Erfolgs-Benachrichtigung erscheint
- Der Feed zeigt seinen Namen, eine Zusammenfassung der konfigurierten Filter, sowie Schaltflaechen "URL kopieren", "Token erneuern", "Loeschen"

---

### TC-015-031: Feed erstellen — Validierung leerer Name

**Zusammenfassung:** Nutzer versucht einen Feed ohne Namen zu erstellen und sieht eine Validierungsfehlermeldung.

**Anforderung:** REQ-015 §3.2 — `CalendarFeedCreate.name: min_length=1`
**Prioritaet:** High
**Kategorie:** Formvalidierung / Fehlermeldung
**Tags:** [req-015, feed, validierung, fehlermeldung, pflichtfeld]

**Vorbedingungen:**
- Feed-Erstellungs-Dialog ist geoeffnet

**Testschritte:**
1. Nutzer laesst das Feld "Feed-Name" leer
2. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Das Feld "Feed-Name" zeigt eine Fehlermarkierung oder Fehlermeldung (z.B. "Name ist erforderlich")
- Kein neuer Feed wird erstellt
- Der Dialog bleibt geoeffnet

---

### TC-015-032: Feed-URL kopieren

**Zusammenfassung:** Nutzer kopiert die webcal-URL eines Feeds in die Zwischenablage.

**Anforderung:** REQ-015 §3.7 — Feed-Management-Dialog: "[URL kopieren]"-Button
**Prioritaet:** High
**Kategorie:** Happy Path / Feed-Management
**Tags:** [req-015, feed, url-kopieren, zwischenablage]

**Vorbedingungen:**
- Mindestens ein Feed existiert in der Feed-Liste

**Testschritte:**
1. Nutzer klickt in der Feed-Karte auf "URL kopieren" (Clipboard-Symbol)

**Erwartetes Ergebnis:**
- Eine Erfolgs-Benachrichtigung erscheint: "URL kopiert"
- Die `webcal://`-URL befindet sich anschliessend in der Systemzwischenablage (nicht direkt pruefbar, aber die Benachrichtigung bestaetigt den Vorgang)

---

### TC-015-033: Feed-Token erneuern

**Zusammenfassung:** Nutzer erneuert den Token eines Feeds und erhaelt eine neue webcal-URL.

**Anforderung:** REQ-015 §4.3 — POST .../regenerate-token; §7 DoD "Token-Rotation invalidiert alten Token sofort"
**Prioritaet:** Critical
**Kategorie:** Zustandswechsel / Sicherheit / Happy Path
**Tags:** [req-015, feed, token, rotation, sicherheit]

**Vorbedingungen:**
- Mindestens ein Feed mit einer sichtbaren webcal-URL existiert
- Nutzer hat die alte URL notiert

**Testschritte:**
1. Nutzer klickt auf "Token erneuern" (Aktualisierungs-Symbol) in der Feed-Karte
2. Evtl. erscheint ein Bestaetigung-Dialog — Nutzer bestaetigt

**Erwartetes Ergebnis:**
- Eine Erfolgs-Benachrichtigung erscheint
- Die angezeigte webcal-URL in der Feed-Karte aendert sich (neues Token in der URL sichtbar)
- Die alte URL ist ab sofort ungueltig — wenn Nutzer die alte URL im Browser oeffnet, erscheint ein Fehler (Feed nicht gefunden oder 401/403)

---

### TC-015-034: Feed loeschen

**Zusammenfassung:** Nutzer loescht einen Feed nach Bestaetigung des Losch-Dialogs.

**Anforderung:** REQ-015 §4.3 — DELETE .../feeds/{feed_id}
**Prioritaet:** High
**Kategorie:** Zustandswechsel / Dialog / Happy Path
**Tags:** [req-015, feed, loeschen, confirm-dialog]

**Vorbedingungen:**
- Mindestens ein Feed existiert in der Feed-Liste

**Testschritte:**
1. Nutzer klickt auf "Feed loeschen" (Muelleimer-Symbol) in der Feed-Karte
2. Ein Bestaetigung-Dialog erscheint (ConfirmDialog mit destruktiver Aktion)
3. Nutzer klickt auf "Loeschen" / "Bestaetigen"

**Erwartetes Ergebnis:**
- Der Dialog schliesst sich
- Der Feed verschwindet aus der Feed-Liste
- Eine Erfolgs-Benachrichtigung erscheint
- Die ehemalige webcal-URL des Feeds liefert keinen iCal-Inhalt mehr

---

### TC-015-035: Feed loeschen — Abbrechen

**Zusammenfassung:** Nutzer beginnt einen Feed zu loeschen, bricht aber im Bestaetigung-Dialog ab.

**Anforderung:** REQ-015 §4.3 — ConfirmDialog mit Abbrechen-Option
**Prioritaet:** Medium
**Kategorie:** Dialog / Negativtest
**Tags:** [req-015, feed, loeschen, abbrechen]

**Vorbedingungen:**
- Mindestens ein Feed existiert; Bestaetigung-Dialog ist geoeffnet

**Testschritte:**
1. Nutzer klickt auf "Abbrechen" im Bestaetigung-Dialog

**Erwartetes Ergebnis:**
- Der Dialog schliesst sich
- Der Feed ist weiterhin in der Feed-Liste vorhanden
- Keine Aenderung am Systemzustand

---

### TC-015-036: Feed auflisten — Mehrere Feeds sichtbar

**Zusammenfassung:** Nutzer sieht eine Auflistung aller seiner iCal-Feeds.

**Anforderung:** REQ-015 §4.3 — GET .../feeds
**Prioritaet:** Medium
**Kategorie:** Listenansicht / Happy Path
**Tags:** [req-015, feed, liste]

**Vorbedingungen:**
- Drei Feeds wurden erstellt

**Testschritte:**
1. Nutzer klappt den "iCal-Feeds"-Bereich auf

**Erwartetes Ergebnis:**
- Alle drei Feeds werden als separate Karten angezeigt
- Jede Karte zeigt: Feed-Name, Filter-Zusammenfassung, webcal-URL, Schaltflaechen (URL kopieren, Token erneuern, Loeschen)

---

## Abschnitt E — Aussaatkalender-Modus (§3.8 und REQ-015-A)

---

### TC-015-040: Aussaatkalender — Nutzpflanze mit Voranzucht und Ernte

**Zusammenfassung:** Nutzer sieht fuer eine Nutzpflanze mit Voranzucht alle vier Balken korrekt in den richtigen Farben.

**Anforderung:** REQ-015 §3.8; REQ-015-A §3.1, §3.2, §3.3, §3.4
**Prioritaet:** Critical
**Kategorie:** Aussaatkalender / Happy Path
**Tags:** [req-015, req-015-a, aussaatkalender, nutzpflanze, balken, farbe]

**Vorbedingungen:**
- Site "Garten Sued" konfiguriert mit `last_frost_date_avg = 15. Mai 2026`, `eisheilige_date = 15. Mai 2026`
- Art "Paprika" (`sp_paprika`) hat: `sowing_indoor_weeks_before_last_frost = 10`, `frost_sensitivity = sensitive`, `direct_sow_months` NICHT gesetzt, `sowing_outdoor_after_last_frost_days = 0`, `harvest_months = [7, 8, 9]`, `allows_harvest = true`
- Nutzer befindet sich im Aussaatkalender-Tab, Standort "Garten Sued", Jahr 2026

**Testschritte:**
1. Nutzer betrachtet die Zeile "Paprika" im Aussaatkalender

**Erwartetes Ergebnis:**
- **Gelber Balken (Voranzucht):** Beginnt ca. Anfang Maerz (10 Wochen vor 15. Mai = ca. 6. Maerz), endet 14. Mai — Farbe `#FDD835`
- **Gruener Balken (Auspflanzen):** Beginnt 16. Mai (Tag nach Frost, da `frost_sensitivity=sensitive` nach Eisheiligen), Dauer ca. 14 Tage — Farbe `#66BB6A`
- **Blauer Balken (Wachstum):** Fuellt die Luecke zwischen Auspflanzen-Ende und Ernte-Beginn (ca. Ende Mai bis 30. Juni) — Farbe `#42A5F5`
- **Oranger Balken (Ernte):** Juli bis September — Farbe `#FFA726`
- Kein pinker Balken, kein oranger Ernte-Balken ausserhalb Juli–September
- Die vier Balken schliessen nahtlos aneinander an (keine Luecke im Balkendiagramm)

---

### TC-015-041: Aussaatkalender — Eisheiligen-Verzoegerung bei frostempfindlicher Pflanze

**Zusammenfassung:** Nutzer prueft, dass eine frostempfindliche Pflanze ihren Auspflanz-Balken erst NACH den Eisheiligen beginnt.

**Anforderung:** REQ-015-A §3.2 — Eisheiligen-Verzoegerung (nur bei Fallback-Berechnung `sowing_outdoor_after_last_frost_days`)
**Prioritaet:** Critical
**Kategorie:** Aussaatkalender / Edge Case / Berechnungsregel
**Tags:** [req-015, req-015-a, eisheilige, frost-sensitivity, verzoegerung]

**Vorbedingungen:**
- Site mit `last_frost_date_avg = 10. Mai`, `eisheilige_date = 15. Mai`
- Pflanze A: `frost_sensitivity = sensitive`, `sowing_outdoor_after_last_frost_days = 0`
- Pflanze B: `frost_sensitivity = hardy`, `sowing_outdoor_after_last_frost_days = 0`
- Kein `direct_sow_months` bei beiden (damit Fallback greift)

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender fuer das Jahr 2026 mit der konfigurierten Site

**Erwartetes Ergebnis:**
- Pflanze A (sensitive): gruener Auspflanzen-Balken beginnt am **16. Mai** (Tag nach Eisheiligen = max(10. Mai + 0, 15. Mai + 1))
- Pflanze B (hardy): gruener Auspflanzen-Balken beginnt am **10. Mai** (direkt nach letztem Frost, kein Eisheiligen-Delay)
- Beide Balken sind gruen (`#66BB6A`)

---

### TC-015-042: Aussaatkalender — Direktsaat-Vorrang vor Fallback

**Zusammenfassung:** Nutzer prueft, dass `direct_sow_months` Vorrang gegenueber `sowing_outdoor_after_last_frost_days` hat.

**Anforderung:** REQ-015-A §3.2 — "Wenn `direct_sow_months` vorhanden ist, wird `sowing_outdoor_after_last_frost_days` IGNORIERT"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Berechnungsregel
**Tags:** [req-015, req-015-a, direktsaat, fallback, vorrang]

**Vorbedingungen:**
- Art "Moehre" mit `direct_sow_months = [3, 4, 5, 6, 7]` UND `sowing_outdoor_after_last_frost_days = 0` (beide Felder gesetzt)
- Site mit `last_frost_date_avg = 15. Mai`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender und betrachtet die Zeile "Moehre"

**Erwartetes Ergebnis:**
- Der gruene Auspflanzen-Balken beginnt am **1. Maerz** (erster Monat aus `direct_sow_months`) — NICHT nach dem Frosttermin
- Es gibt **keinen zweiten** Auspflanzen-Balken basierend auf `sowing_outdoor_after_last_frost_days`
- Nur ein gruener Balken von Maerz bis Ende Juli

---

### TC-015-043: Aussaatkalender — Zierpflanze mit Bluetepause (AB-010)

**Zusammenfassung:** Nutzer prueft, dass eine Zierpflanze mit nicht-zusammenhaengenden `bloom_months` ZWEI getrennte pinke Blute-Balken und keinen orangen Ernte-Balken zeigt.

**Anforderung:** REQ-015-A §3.5 — Zierpflanzen, Bluetepause; §9 Akzeptanzkriterium AB-010
**Prioritaet:** Critical
**Kategorie:** Aussaatkalender / Zierpflanze / Edge Case
**Tags:** [req-015, req-015-a, zierpflanze, bluetepause, ornamental, ab-010]

**Vorbedingungen:**
- Art "Stiefmuetterchen" (`sp_viola`): `traits = ['ornamental']`, `allows_harvest = false`, `bloom_months = [3, 4, 5, 6, 9, 10]`, `sowing_indoor_weeks_before_last_frost = 12`, `frost_sensitivity = hardy`
- Site "Balkon" mit `last_frost_date_avg = 15. Mai`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender, Jahr 2026, Site "Balkon"
2. Nutzer betrachtet die Zeile "Stiefmuetterchen"

**Erwartetes Ergebnis:**
- **Gelber Balken (Voranzucht):** Ca. Mitte Februar bis 14. Mai (12 Wochen vor 15. Mai)
- **Gruener Balken (Auspflanzen):** Nach Voranzucht-Ende, da `hardy` auch vor Eisheiligen moeglich
- **ZWEI pinke Balken (Bluete):** Maerz bis Ende Juni UND September bis Ende Oktober — Farbe `#EC407A`
- **KEINE Bluete** in Juli und August (sichtbare Luecke / Bluetepause zwischen den zwei Balken)
- **KEIN oranger Ernte-Balken** (da `allows_harvest = false`)
- **KEIN durchgehender** Balken von Maerz bis Oktober

---

### TC-015-044: Aussaatkalender — Nutzpflanze ohne Voranzucht (nur Direktsaat)

**Zusammenfassung:** Nutzer prueft, dass eine Pflanze ohne Voranzucht keinen gelben Balken hat.

**Anforderung:** REQ-015-A §3.1 — "Nur anzeigen wenn `sowing_indoor_weeks_before_last_frost` gesetzt"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Happy Path
**Tags:** [req-015, req-015-a, direktsaat, kein-voranzucht-balken]

**Vorbedingungen:**
- Art "Radieschen": `sowing_indoor_weeks_before_last_frost = null`, `direct_sow_months = [3,4,5,6,7,8,9]`, `harvest_months = [4,5,6,7,8,9,10]`, `allows_harvest = true`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender und betrachtet die Zeile "Radieschen"

**Erwartetes Ergebnis:**
- Kein gelber Balken (kein Voranzucht-Balken)
- Gruener Balken beginnt am 1. Maerz und endet am 30. September
- Oranger Ernte-Balken April bis Oktober
- Der Wachstums-Balken (blau) erscheint nur wenn eine Luecke zwischen Auspflanzen-Ende und Ernte-Beginn besteht

---

### TC-015-045: Aussaatkalender — Pflanze ohne Aussaatdaten erscheint nicht

**Zusammenfassung:** Nutzer prueft, dass Pflanzen ohne Aussaatdaten nicht im Aussaatkalender erscheinen.

**Anforderung:** REQ-015-A §7 — "Pflanzen ohne Aussaat-Daten erscheinen NICHT im Aussaatkalender"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Negativtest / Edge Case
**Tags:** [req-015, req-015-a, keine-aussaatdaten, negativtest]

**Vorbedingungen:**
- Art "Zimmerpflanze X" hat keines der Felder gesetzt: kein `sowing_indoor_weeks_before_last_frost`, kein `direct_sow_months`, kein `sowing_outdoor_after_last_frost_days`, kein `harvest_months`, kein `bloom_months`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender
2. Nutzer sucht in der Pflanzenliste nach "Zimmerpflanze X"

**Erwartetes Ergebnis:**
- "Zimmerpflanze X" erscheint NICHT in der Aussaatkalender-Zeilen-Liste
- Keine Zeile ohne Balken wird fuer diese Art angezeigt

---

### TC-015-046: Aussaatkalender — Filter "Nur meine geplanten Pflanzen"

**Zusammenfassung:** Nutzer aktiviert den Filter fuer geplante Pflanzen und sieht nur Arten aus aktiven Pflanzdurchlaeufen.

**Anforderung:** REQ-015 §3.8 — "Filter: Nur meine geplanten Pflanzen / Alle verfuegbaren Pflanzen"; §7 Testszenario 7
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Filterung
**Tags:** [req-015, aussaatkalender, filter, geplante-pflanzen, planned-only]

**Vorbedingungen:**
- 20 Arten existieren in den Stammdaten
- 5 Arten sind in einem aktiven Pflanzdurchlauf (REQ-013) fuer den ausgewaehlten Standort eingetragen

**Testschritte:**
1. Nutzer ist im Aussaatkalender-Tab, Standort "Garten Sued" gewaehlt
2. Nutzer aktiviert den Filter "Nur Favoriten" bzw. "Nur geplante Pflanzen"

**Erwartetes Ergebnis:**
- Nur die 5 geplanten Arten sind als Zeilen im Aussaatkalender sichtbar
- Die 15 anderen Arten werden nicht angezeigt

**Testschritte (Fortsetzung):**
3. Nutzer deaktiviert den Filter wieder

**Erwartetes Ergebnis:**
- Alle 20 verfuegbaren Arten sind wieder sichtbar

---

### TC-015-047: Aussaatkalender — Tooltip bei Balken-Hover

**Zusammenfassung:** Nutzer hovert ueber einen Zeitbalken und sieht einen informativen Tooltip.

**Anforderung:** REQ-015 §3.8 — "Hover zeigt Tooltip: 'Tomate San Marzano: Voranzucht ab 1. Maerz...'"
**Prioritaet:** Medium
**Kategorie:** Aussaatkalender / Interaktion
**Tags:** [req-015, aussaatkalender, tooltip, hover]

**Vorbedingungen:**
- Aussaatkalender zeigt mindestens eine Pflanze mit Balken

**Testschritte:**
1. Nutzer bewegt die Maus ueber den Voranzucht-Balken (gelb) einer Pflanze

**Erwartetes Ergebnis:**
- Ein Tooltip erscheint mit Informationen wie: "[Pflanzenname]: Voranzucht ab [Startdatum], Auspflanzen ab [Datum], Ernte [Monate]"
- Der Tooltip verschwindet, sobald die Maus den Balken verlaesst

---

### TC-015-048: Aussaatkalender — Frosttermin-Konfiguration bei fehlendem Standort

**Zusammenfassung:** Nutzer oeffnet Aussaatkalender ohne Standortauswahl und sieht einen Hinweis.

**Anforderung:** REQ-015 §4.4 — `site_id` ist Pflichtparameter; §3.8 — Frosttermin auf Site-Level
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Fehlermeldung / Edge Case
**Tags:** [req-015, aussaatkalender, site-auswahl, pflichtfeld]

**Vorbedingungen:**
- Nutzer ist im Aussaatkalender-Tab
- Kein Standort ist in der Dropdown-Liste ausgewaehlt (oder kein Standort konfiguriert)

**Testschritte:**
1. Nutzer oeffnet den Aussaatkalender-Tab ohne Standort ausgewaehlt zu haben

**Erwartetes Ergebnis:**
- Eine Meldung wie "Keine Pflanzen mit Aussaatdaten vorhanden" ODER ein Hinweis auf die Standortauswahl wird angezeigt
- Kein Fehler-Dialog oder Absturz der Seite

---

### TC-015-049: Aussaatkalender — Eisheiligen-Markierung sichtbar

**Zusammenfassung:** Nutzer sieht die vertikale Eisheiligen-Markierungslinie im Aussaatkalender.

**Anforderung:** REQ-015-A §4 — "Wird als vertikale gestrichelte Linie (rot) im Kalender dargestellt"; §7 DoD
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Visuelle Darstellung
**Tags:** [req-015, req-015-a, eisheilige, markierung, visualisierung]

**Vorbedingungen:**
- Site mit konfiguriertem `eisheilige_date` (z.B. 15. Mai)
- Aussaatkalender fuer das aktuelle Jahr ist geoeffnet

**Testschritte:**
1. Nutzer betrachtet den Aussaatkalender mit Fokus auf den Mai-Bereich

**Erwartetes Ergebnis:**
- Eine vertikale gestrichelte oder andersfarbige Linie erscheint bei der Eisheiligen-Spalte (Mitte Mai)
- Die Linie ist visuell deutlich von den Zeitbalken unterscheidbar
- Ein Label oder Tooltip beschriftet die Linie als "Eisheilige" oder zeigt das Datum

---

### TC-015-050: Aussaatkalender — Mehrere Anbauzeitraeume (GrowingPeriods)

**Zusammenfassung:** Nutzer prueft, dass eine Art mit zwei GrowingPeriods (z.B. Weizen) als zwei getrennte Zeilen dargestellt wird.

**Anforderung:** REQ-015-A §6.3 — "Jede GrowingPeriod erzeugt eine eigene Kalender-Zeile"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / GrowingPeriod / Edge Case
**Tags:** [req-015, req-015-a, growing-periods, mehrere-perioden, zeilen]

**Vorbedingungen:**
- Art "Weizen" hat explizit zwei GrowingPeriods:
  - Period 1: `label="Sommerweizen"`, `direct_sow=[3,4]`, `harvest=[7,8]`
  - Period 2: `label="Winterweizen"`, `direct_sow=[10,11]`, `harvest=[6,7]`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender
2. Nutzer sucht die Zeilen fuer "Weizen"

**Erwartetes Ergebnis:**
- **Zwei getrennte Zeilen** sind sichtbar: "Weizen (Sommerweizen)" und "Weizen (Winterweizen)"
- Sommerweizen-Zeile: gruener Balken Maerz–April, Ernte-Balken Juli–August
- Winterweizen-Zeile: gruener Balken Oktober–November (Aussaat aktuelles Jahr); zusaetzlich Wachstums-Balken Jan–Mai (vom Vorjahres-Zyklus) und Ernte-Balken Juni–Juli
- Kein Suffix bei einer Einzelperiode (z.B. Radieschen zeigt nur "Radieschen", kein "(spring)")

---

### TC-015-051: Aussaatkalender — Jahresuebergreifende Ernte-Wrap-around

**Zusammenfassung:** Nutzer prueft, dass ein Ernte-Balken der ueber den Jahreswechsel geht, am 31. Dezember abgeschnitten wird.

**Anforderung:** REQ-015-A §3.4 — "Wrap-around-Balken am 31. Dezember abschneiden"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Edge Case / Jahresgrenze
**Tags:** [req-015, req-015-a, wrap-around, jahresgrenze, ernte]

**Vorbedingungen:**
- Art "Winterporree" (GrowingPeriod 2): `direct_sow=[5,6]`, `harvest_months = [12, 1, 2, 3]`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender fuer das Jahr 2026 und betrachtet "Porree (Winterporree)"

**Erwartetes Ergebnis:**
- Ernte-Balken beginnt am **1. Dezember** und endet am **31. Dezember** (Jahresende-Kappung)
- Es gibt keinen orangen Balken fuer Januar–Maerz im Kalender 2026 (der gehoert zum Folgejahr)
- Kein zweiter Ernte-Balken Jan–Maerz wird im selben Jahreskalender angezeigt

---

### TC-015-052: Aussaatkalender — Jährlich wiederkehrende Pflanze (annual_repeat)

**Zusammenfassung:** Nutzer sieht eine jährlich wiederkehrende Pflanze automatisch im Aussaatkalender des Folgejahres.

**Anforderung:** REQ-015 §3.8.1 — "Automatische Voranzucht-Erinnerung" bei `annual_repeat = true`
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Jährlich / Happy Path
**Tags:** [req-015, annual-repeat, wiederkehrend, jährlich, aussaatkalender]

**Vorbedingungen:**
- PlantingRun "Stiefmuetterchen 2025" existiert mit `annual_repeat = true`, `repeat_month = 2`
- Stiefmuetterchen hat `sowing_indoor_weeks_before_last_frost = 12`
- Site mit `last_frost_date_avg = 15. Mai`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender fuer das Jahr 2026

**Erwartetes Ergebnis:**
- Stiefmuetterchen erscheint automatisch im Aussaatkalender 2026 (aus `annual_repeat`)
- Gelber Voranzucht-Balken startet im Februar (12 Wochen vor 15. Mai = ca. Mitte Februar)

---

### TC-015-053: Aussaatkalender — Jahresvergleich (halbtransparente Referenzlinie)

**Zusammenfassung:** Nutzer sieht bei jährlich wiederkehrenden Pflanzen mit `previous_run_key` eine halbtransparente Referenzlinie des Vorjahres-Runs.

**Anforderung:** REQ-015 §3.8.1 — "Jahresvergleich: Vorjahres-Daten als halbtransparente Referenzlinie"
**Prioritaet:** Medium
**Kategorie:** Aussaatkalender / Jahresvergleich / Visualisierung
**Tags:** [req-015, jahresvergleich, previous-run, referenzlinie]

**Vorbedingungen:**
- PlantingRun "Stiefmuetterchen 2025" hat `annual_repeat = true` und `previous_run_key` zeigt auf abgeschlossenen Run "Stiefmuetterchen 2024"

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender 2026
2. Nutzer betrachtet die Zeile "Stiefmuetterchen"

**Erwartetes Ergebnis:**
- Unter den aktuellen Balken erscheint eine duennere, halbtransparente Linie, die die tatsaechlichen Zeitraeume des Vorjahres-Runs darstellt
- Die Referenzlinie ist optisch klar von den aktuellen Balken unterscheidbar (halbtransparent / anderer Stil)

---

### TC-015-054: Aussaatkalender — Kategorie-Filter "Blumen"

**Zusammenfassung:** Nutzer setzt den Kategorie-Filter auf "Blumen" und sieht nur Zierpflanzen.

**Anforderung:** REQ-015 §3.8; REQ-015-A §9 Akzeptanzkriterium "Kategorie-Filter 'Blumen' filtert korrekt auf ornamental"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Filterung
**Tags:** [req-015, req-015-a, aussaatkalender, filter, blumen, ornamental]

**Vorbedingungen:**
- 8 Nutzpflanzen und 4 Zierpflanzen (mit `traits: ['ornamental']`) existieren in den Stammdaten

**Testschritte:**
1. Nutzer ist im Aussaatkalender-Tab
2. Nutzer klickt auf den Kategorie-Filter und waehlt "Blumen" aus

**Erwartetes Ergebnis:**
- Nur die 4 Zierpflanzen werden als Zeilen angezeigt
- Alle 4 zeigen pinke Bluete-Balken (Farbe `#EC407A`), kein oranger Ernte-Balken

---

### TC-015-055: Aussaatkalender — Leerzustand wenn keine Aussaatdaten

**Zusammenfassung:** Nutzer oeffnet den Aussaatkalender, wenn fuer den ausgewaehlten Standort keine Pflanzen mit Aussaatdaten vorhanden sind.

**Anforderung:** REQ-015 §3.8 — i18n-Key `calendar.sowingCalendar.noData`
**Prioritaet:** Medium
**Kategorie:** Aussaatkalender / Leerszustand / Fehlermeldung
**Tags:** [req-015, aussaatkalender, leerszustand, empty-state]

**Vorbedingungen:**
- Der ausgewaehlte Standort hat keine Pflanzen-Verknuepfungen oder alle Arten haben keine Aussaatdaten

**Testschritte:**
1. Nutzer oeffnet den Aussaatkalender-Tab
2. Nutzer waehlt einen Standort ohne zugeordnete Pflanzen mit Aussaatdaten

**Erwartetes Ergebnis:**
- Statt einer leeren Tabelle erscheint der Text: "Keine Pflanzen mit Aussaatdaten vorhanden. Tragen Sie Aussaat- und Erntedaten bei den Arten ein."
- Kein Fehler-Dialog oder Absturz

---

## Abschnitt F — Saisonuebersicht-Modus (§3.9)

---

### TC-015-060: Saisonuebersicht — 12 Monatskarten mit Zaehlanzeige

**Zusammenfassung:** Nutzer oeffnet die Saisonuebersicht und sieht 12 Monatskarten mit korrekten Saat-/Ernte-/Task-Zaehlanzeigen.

**Anforderung:** REQ-015 §3.9 — SeasonOverview, §7 Testszenario 8
**Prioritaet:** Critical
**Kategorie:** Saisonuebersicht / Happy Path
**Tags:** [req-015, saisonuebersicht, monatskarten, zaehlung]

**Vorbedingungen:**
- Aussaatkalender-Daten fuer mindestens 5 Pflanzen im Jahr 2026 vorhanden
- Mindestens 10 Tasks ueber das Jahr 2026 verteilt
- Site ausgewaehlt

**Testschritte:**
1. Nutzer klickt auf den Saisonuebersicht-Tab

**Erwartetes Ergebnis:**
- Genau 12 Monatskarten werden angezeigt (Januar bis Dezember)
- Jede Karte zeigt: Monatsname (z.B. "Maerz"), "X Aussaat", "Y Ernte", "Z Aufgaben"
- Monate mit Aussaat zeigen einen Saat-Zaehler > 0
- Monate ohne Aussaat zeigen "0 Aussaat"
- Die Gesamtsumme der Task-Zaehler ueber alle Monate entspricht der Gesamtzahl Tasks des Jahres

---

### TC-015-061: Saisonuebersicht — Aktueller Monat hervorgehoben

**Zusammenfassung:** Nutzer prueft, dass der aktuelle Monat in der Saisonuebersicht visuell hervorgehoben ist.

**Anforderung:** REQ-015 §3.9 — "Aktueller-Monat-Highlight"; §7 DoD "Aktueller Monat ist in der Saisonuebersicht visuell hervorgehoben"
**Prioritaet:** High
**Kategorie:** Saisonuebersicht / Visuelle Darstellung
**Tags:** [req-015, saisonuebersicht, highlight, aktueller-monat]

**Vorbedingungen:**
- Saisonuebersicht-Tab ist aktiv; aktuelles Datum ist z.B. Maerz 2026

**Testschritte:**
1. Nutzer betrachtet die 12 Monatskarten

**Erwartetes Ergebnis:**
- Die Karte fuer den aktuellen Monat (z.B. "Maerz") ist visuell hervorgehoben (z.B. staerkerer Rahmen, andere Hintergrundfarbe, vergroesserte Karte)
- Alle anderen Monatskarten haben eine einheitliche, nicht-hervorgehobene Darstellung
- Die hervorgehobene Karte zeigt mehr Details oder ist "expandiert" (Top-3 Aufgaben sichtbar)

---

### TC-015-062: Saisonuebersicht — Klick auf Monatskarte wechselt Ansicht

**Zusammenfassung:** Nutzer klickt auf eine Monatskarte und wechselt zur Monatsansicht des gewaehlten Monats.

**Anforderung:** REQ-015 §3.9 — "Klick auf Monatskarte: Wechselt zur Monatsansicht"; §7 Testszenario 8
**Prioritaet:** High
**Kategorie:** Navigation / Saisonuebersicht
**Tags:** [req-015, saisonuebersicht, navigation, monatsansicht, klick]

**Vorbedingungen:**
- Saisonuebersicht-Tab ist aktiv

**Testschritte:**
1. Nutzer klickt auf die Monatskarte "Mai"

**Erwartetes Ergebnis:**
- Die Ansicht wechselt automatisch zur Monatsansicht
- Die Kopfzeile zeigt "Mai 2026"
- Tasks des Monats Mai sind als Events im Monatsgrid sichtbar

---

### TC-015-063: Saisonuebersicht — Jahreszaehler Top-3 Aufgaben sichtbar

**Zusammenfassung:** Nutzer prueft, dass die wichtigsten 3 Aufgaben eines Monats in der Saisonuebersicht angezeigt werden.

**Anforderung:** REQ-015 §3.9 — "Top-3 wichtigste Aufgaben des Monats"
**Prioritaet:** Medium
**Kategorie:** Saisonuebersicht / Happy Path
**Tags:** [req-015, saisonuebersicht, top3, aufgaben]

**Vorbedingungen:**
- Fuer einen Monat (z.B. Mai) existieren mindestens 5 Tasks mit verschiedenen Prioritaeten (mind. 2 critical/high)

**Testschritte:**
1. Nutzer betrachtet die Monatskarte "Mai" in der Saisonuebersicht

**Erwartetes Ergebnis:**
- Maximal 3 Task-Eintraege sind in der Karte sichtbar
- Diese 3 Tasks haben die hoechste Prioritaet des Monats (critical > high > medium > low)

---

## Abschnitt G — Responsive Verhalten

---

### TC-015-070: Mobile Darstellung — Agenda-Listenansicht als Default

**Zusammenfassung:** Nutzer oeffnet die Kalenderseite auf einem Smartphone und sieht automatisch die Agenda-Listenansicht.

**Anforderung:** REQ-015 §3.7 — "Mobile (<768px): Agenda-Listenansicht als Default"; §7 Testszenario 5
**Prioritaet:** High
**Kategorie:** Responsive / Happy Path
**Tags:** [req-015, responsive, mobile, agenda, listenansicht]

**Vorbedingungen:**
- Browser-Fenster auf <768px Breite eingestellt (oder mobiles Geraet)
- Mindestens 3 Events existieren in der kommenden Woche

**Testschritte:**
1. Nutzer oeffnet `/kalender` im schmalen Browser-Fenster (<768px)

**Erwartetes Ergebnis:**
- Die Monats-Grid-Ansicht ist NICHT das Default
- Stattdessen wird die Agenda-/Listen-Ansicht gezeigt (chronologisch sortierte Event-Liste)
- Events zeigen Datum, Uhrzeit, Farb-Indikator, Titel und Prioritaet
- Kategorie-Filter sind als "Bottom-Sheet" oder "Drawer" zugaenglich, nicht als permanente Sidebar

---

### TC-015-071: Mobile — Tap auf Event oeffnet Detail-Ansicht

**Zusammenfassung:** Nutzer tippt auf ein Event in der mobilen Agenda-Ansicht und sieht die Detailansicht.

**Anforderung:** REQ-015 §3.7 — "Tap auf Event oeffnet Bottom-Sheet mit Details"
**Prioritaet:** High
**Kategorie:** Responsive / Interaktion / Mobile
**Tags:** [req-015, responsive, mobile, tap, event-detail]

**Vorbedingungen:**
- Mobile Agenda-Ansicht ist aktiv (< 768px); Events sind sichtbar

**Testschritte:**
1. Nutzer tippt auf einen Event-Eintrag in der Agenda-Liste

**Erwartetes Ergebnis:**
- Ein Bottom-Sheet oder Popover/Modal oeffnet sich von unten
- Detail-Informationen werden angezeigt: Titel, Beschreibung, Kategorie, Prioritaet, Standort
- Eine "Details anzeigen"-Option ist vorhanden

---

### TC-015-072: Desktop — Kalender-Grid mit Filter-Sidebar

**Zusammenfassung:** Nutzer oeffnet die Kalenderseite auf einem Desktop-Browser und sieht das Grid mit Sidebar.

**Anforderung:** REQ-015 §3.7 — "Desktop (>=1024px): Kalender-Grid mit Filter-Sidebar"
**Prioritaet:** Medium
**Kategorie:** Responsive / Happy Path
**Tags:** [req-015, responsive, desktop, sidebar, grid]

**Vorbedingungen:**
- Browser-Fenster >=1024px breit

**Testschritte:**
1. Nutzer oeffnet `/kalender` im breiten Browser-Fenster

**Erwartetes Ergebnis:**
- Eine dauerhafte linke Sidebar mit Filteroptionen ist sichtbar
- Das Monats-Grid belegt den Hauptbereich rechts
- Sidebar zeigt: Kategorie-Checkboxen, Standort-Auswahl, Prioritaets-Filter, Status-Filter, Timeline-Toggle, Feed-Bereich

---

## Abschnitt H — Sicherheits- und Zugriffskontrollen

---

### TC-015-080: Unauthentifizierter Zugriff auf Kalenderseite

**Zusammenfassung:** Nicht eingeloggter Nutzer versucht die Kalenderseite aufzurufen und wird zur Login-Seite weitergeleitet.

**Anforderung:** REQ-015 §5 — "Alle Endpunkte erfordern Authentifizierung und Tenant-Mitgliedschaft"
**Prioritaet:** Critical
**Kategorie:** Sicherheit / Authentifizierung
**Tags:** [req-015, auth, zugriffskontrolle, redirect]

**Vorbedingungen:**
- Nutzer ist NICHT eingeloggt

**Testschritte:**
1. Nutzer navigiert direkt zu `/kalender`

**Erwartetes Ergebnis:**
- Der Nutzer wird zur Login-Seite weitergeleitet (z.B. `/login`)
- Die Kalenderseite wird nicht angezeigt

---

### TC-015-081: iCal-Feed-Token-Sicherheit — ungultiger Token

**Zusammenfassung:** Nutzer ruft eine iCal-Feed-URL mit ungueltigem Token ab und erhaelt eine Fehlerantwort.

**Anforderung:** REQ-015 §2 — CF-001, CF-003; §4.2 — Token-basierte Authentifizierung fuer Feed-Endpunkte
**Prioritaet:** Critical
**Kategorie:** Sicherheit / Authentifizierung / Fehlermeldung
**Tags:** [req-015, ical, token, sicherheit, cf-001, cf-003]

**Vorbedingungen:**
- Ein Feed existiert, aber der Token wurde per "Token erneuern" rotiert (alter Token ungueltig)

**Testschritte:**
1. Nutzer versucht die alte `webcal://`-URL im Browser zu oeffnen (oder fuegt sie in einen Kalender-Client ein)

**Erwartetes Ergebnis:**
- Die Anfrage schlaegt fehl (Kalender-Client zeigt Fehler)
- Kein iCal-Inhalt wird ausgeliefert
- Der Feed liefert kein valides iCalendar-Dokument mehr

---

### TC-015-082: Feed-Inhalte enthalten keine personenbezogenen Daten

**Zusammenfassung:** Nutzer prueft, dass der exportierte iCal-Feed keine Nutzernamen oder E-Mail-Adressen enthaelt.

**Anforderung:** REQ-015 §2 — CF-006: "Feed-Inhalte DUERFEN KEINE personenbezogenen Daten enthalten"
**Prioritaet:** Critical
**Kategorie:** Sicherheit / Datenschutz / DSGVO
**Tags:** [req-015, ical, datenschutz, cf-006, dsgvo, pii]

**Vorbedingungen:**
- Ein Feed mit Events ist erstellt; der Nutzer hat einen Namen und eine E-Mail-Adresse

**Testschritte:**
1. Nutzer kopiert die webcal-URL und oeffnet sie direkt im Browser (zeigt den Roh-iCal-Text)
2. Nutzer sucht im ical-Text nach seiner E-Mail-Adresse und seinem Klarnamen

**Erwartetes Ergebnis:**
- Die E-Mail-Adresse des Nutzers erscheint NICHT im iCal-Text
- Der Buergerliche Name des Nutzers erscheint NICHT im iCal-Text
- SUMMARY/DESCRIPTION enthalten nur Sachdaten (Pflanzenname, Aufgabentyp, Standortname)

---

## Abschnitt I — i18n und Vollständigkeit

---

### TC-015-090: Sprachumschaltung — Kalender auf Englisch

**Zusammenfassung:** Nutzer wechselt die Sprache auf Englisch und alle Kalender-Labels werden auf Englisch angezeigt.

**Anforderung:** REQ-015 §7 DoD — "i18n: Alle Labels in DE und EN vorhanden"
**Prioritaet:** Medium
**Kategorie:** i18n / Internationalisierung
**Tags:** [req-015, i18n, englisch, sprachumschaltung]

**Vorbedingungen:**
- Nutzer befindet sich auf der Kalenderseite mit Deutsch als aktiver Sprache

**Testschritte:**
1. Nutzer wechselt in den Einstellungen die Sprache auf "English"
2. Nutzer navigiert zurueck zur Kalenderseite

**Erwartetes Ergebnis:**
- Alle sichtbaren Kalender-Labels sind auf Englisch (Ansichtsmodi, Kategorie-Namen, Button-Texte)
- Keine deutschen Platzhalter-Texte oder leeren Label-Felder sichtbar
- Der Titel lautet "Calendar" (statt "Kalender")
- Kategorienamen: "Training", "Pruning", "Transplanting" etc.

---

### TC-015-091: Alle Kategorie-Farben korrekt und konsistent

**Zusammenfassung:** Nutzer prueft, dass jede Kategorie im Kalender die spezifizierte Farbe verwendet.

**Anforderung:** REQ-015 §3.7 — CATEGORY_COLORS; §1 "Farbkodierung pro Kategorie"
**Prioritaet:** Medium
**Kategorie:** Visuelle Darstellung / Happy Path
**Tags:** [req-015, farbe, kategorie, farbkodierung]

**Vorbedingungen:**
- Fuer jede Kategorie existiert mindestens ein Task im aktuellen Monat

**Testschritte:**
1. Nutzer betrachtet den Monatskalender mit Events aller Kategorien

**Erwartetes Ergebnis:**
- Training: gruener Hintergrund (`#4CAF50`)
- Schnitt/Pruning: hellgruener Hintergrund
- Umtopfen: brauner Hintergrund
- Duengung/Feeding: blauer Hintergrund
- Pflanzenschutz/IPM: oranger Hintergrund
- Ernte/Harvest: roter Hintergrund (gem. Frontend-Implementierung)
- Wartung/Maintenance: grauer Hintergrund
- Phasenwechsel/Phase_Transition: violetter Hintergrund (`#9C27B0`)
- Tankwartung: cyan/tuerkis Hintergrund

---

## Abschnitt J — Aussaatkalender Berechnungs-Edge-Cases (REQ-015-A)

---

### TC-015-100: Voranzucht-Datum vor 1. Januar wird auf 1. Januar gekuerzt

**Zusammenfassung:** Nutzer prueft, dass ein Voranzucht-Startdatum, das im Vorjahr liegt, auf den 1. Januar gekuerzt wird.

**Anforderung:** REQ-015-A §3.1 — "Wenn `start_date` vor dem 1. Januar des Bezugsjahres liegt: auf 1. Januar kappen"
**Prioritaet:** Medium
**Kategorie:** Aussaatkalender / Edge Case / Berechnungsregel
**Tags:** [req-015-a, voranzucht, datum-kappung, grenzwert]

**Vorbedingungen:**
- Art mit `sowing_indoor_weeks_before_last_frost = 20` (20 Wochen vor 15. Mai = ca. 30. Dezember Vorjahr)
- Site mit `last_frost_date_avg = 15. Mai`

**Testschritte:**
1. Nutzer oeffnet Aussaatkalender fuer 2026

**Erwartetes Ergebnis:**
- Gelber Voranzucht-Balken beginnt am **1. Januar 2026** (nicht im Dezember 2025)
- Der Balken ist trotz der Kappung sichtbar und korrekt bis zum 14. Mai

---

### TC-015-101: Wachstums-Balken entfaellt bei direkt aneinander grenzenden Phasen

**Zusammenfassung:** Nutzer prueft, dass kein Wachstums-Balken erscheint, wenn Auspflanzen und Ernte direkt aneinander grenzen.

**Anforderung:** REQ-015-A §3.3 — "Kein Wachstums-Balken wenn Auspflanzen und Ernte direkt aneinander grenzen oder ueberlappen"
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Edge Case / Berechnungsregel
**Tags:** [req-015-a, wachstum, kein-balken, grenzfall]

**Vorbedingungen:**
- Art mit `direct_sow_months = [5, 6, 7]` und `harvest_months = [7, 8, 9]` (Auspflanzen endet 31. Juli, Ernte beginnt 1. Juli — Ueberlappung)

**Testschritte:**
1. Nutzer betrachtet die Zeile dieser Art im Aussaatkalender

**Erwartetes Ergebnis:**
- Kein blauer Wachstums-Balken ist sichtbar
- Gruener Auspflanzen-Balken und oranger Ernte-Balken grenzen aneinander oder ueberlappen

---

### TC-015-102: Wachstums-Balken erscheint nur bei Luecke von mindestens 2 Tagen

**Zusammenfassung:** Nutzer prueft, dass ein Wachstums-Balken nur dann erscheint, wenn die Luecke mindestens 2 Tage betraegt.

**Anforderung:** REQ-015-A §3.3 — "Nur anzeigen wenn `growth_start < growth_end` (Luecke mindestens 2 Tage)"
**Prioritaet:** Medium
**Kategorie:** Aussaatkalender / Edge Case / Grenzwert
**Tags:** [req-015-a, wachstum, grenzwert, 2-tage]

**Vorbedingungen:**
- Art A: Auspflanzen endet 30. Juni, Ernte beginnt 1. Juli (1 Tag Luecke → kein Wachstum)
- Art B: Auspflanzen endet 30. Juni, Ernte beginnt 3. Juli (3 Tage Luecke → Wachstum muss erscheinen)

**Testschritte:**
1. Nutzer betrachtet beide Arten im Aussaatkalender

**Erwartetes Ergebnis:**
- Art A: KEIN blauer Wachstums-Balken
- Art B: Blauer Wachstums-Balken vom 1. bis 2. Juli sichtbar

---

### TC-015-103: Legacy-Felder werden als einzelne GrowingPeriod interpretiert

**Zusammenfassung:** Nutzer prueft, dass eine Art ohne explizite `growing_periods` ueber ihre Legacy-Felder korrekt berechnet wird (eine Zeile, kein Suffix).

**Anforderung:** REQ-015-A §6.2 — Abwaertskompatibilitaet; §6.3 "Bei einer einzigen Periode wird kein Suffix angezeigt"
**Prioritaet:** Medium
**Kategorie:** Aussaatkalender / Abwaertskompatibilitaet
**Tags:** [req-015-a, legacy-felder, abwaertskompatibilitaet, kein-suffix]

**Vorbedingungen:**
- Art "Tomate" hat KEINE expliziten `growing_periods`, aber hat: `direct_sow_months = [5]`, `harvest_months = [8,9,10]`, `sowing_indoor_weeks_before_last_frost = 8`

**Testschritte:**
1. Nutzer betrachtet die Zeile "Tomate" im Aussaatkalender

**Erwartetes Ergebnis:**
- **Genau eine Zeile** fuer "Tomate" ist sichtbar
- Kein Suffix "(spring)" oder "(summer)" hinter dem Namen
- Balken werden korrekt aus Legacy-Feldern berechnet

---

### TC-015-104: Jahresuebergreifende Kultur — Wachstums-Balken ab 1. Januar

**Zusammenfassung:** Nutzer prueft, dass eine jahresuebergreifende Kultur (Herbstaussaat, Sommerernte) einen Wachstums-Balken ab 1. Januar des Bezugsjahres zeigt.

**Anforderung:** REQ-015-A §3.3 — "Jahresuebergreifende Perioden (Herbstaussaat → Sommerernte)": Wachstum-Balken 1. Januar bis Ernte-Beginn
**Prioritaet:** High
**Kategorie:** Aussaatkalender / Edge Case / Jahresgrenze
**Tags:** [req-015-a, jahresuebergreifend, herbstaussaat, winterweizen, wachstum]

**Vorbedingungen:**
- Art "Winterweizen" hat GrowingPeriod: `label="Winterweizen"`, `direct_sow=[10,11]`, `harvest=[6,7]`
- Ernte-Monate liegen chronologisch VOR den Aussaat-Monaten im Kalender

**Testschritte:**
1. Nutzer betrachtet die Zeile "Weizen (Winterweizen)" im Aussaatkalender 2026

**Erwartetes Ergebnis:**
- **Blauer Wachstums-Balken** beginnt am 1. Januar 2026 und endet am 31. Mai (Tag vor Ernte-Beginn)
- **Oranger Ernte-Balken** Juni–Juli 2026
- **Gruener Aussaat-Balken** Oktober–November 2026 (fuer den naechsten Zyklus)
- Kein Wachstums-Balken erscheint VOR dem 1. Januar

---

## Deckungsmatrix

| Spez.-Abschnitt | Beschreibung | Testfaelle |
|-----------------|-------------|-----------|
| REQ-015 §1 | Business Case / User Stories | TC-015-001 |
| REQ-015 §3.7 | Frontend-Konzept: Ansichten | TC-015-001 bis TC-015-007 |
| REQ-015 §3.7 | Kategorie-Filter | TC-015-010, TC-015-011 |
| REQ-015 §3.7 | Standort-Filter | TC-015-012 |
| REQ-015 §3.7 | Pflanzenstamm-Filter | TC-015-013 |
| REQ-015 §3.7 | Kombinierter Filter | TC-015-014 |
| REQ-015 §3.7 | Timeline-Toggle | TC-015-020, TC-015-021 |
| REQ-015 §3.7 | Event-Interaktion (Popover) | TC-015-022, TC-015-023 |
| REQ-015 §3.7 | Gießplan bestaetigen | TC-015-024 |
| REQ-015 §3.7 | Responsive Verhalten | TC-015-070, TC-015-071, TC-015-072 |
| REQ-015 §4.3 | Feed CRUD | TC-015-030 bis TC-015-036 |
| REQ-015 §4.2 | iCal-Export | TC-015-081, TC-015-082 |
| REQ-015 §3.8 | Aussaatkalender-Modus | TC-015-005, TC-015-040 bis TC-015-055 |
| REQ-015 §3.8.1 | Jährlich wiederkehrende Pflanzen | TC-015-052, TC-015-053 |
| REQ-015 §3.9 | Saisonuebersicht | TC-015-060 bis TC-015-063 |
| REQ-015 §5 | Auth & Autorisierung | TC-015-080, TC-015-081, TC-015-082 |
| REQ-015 §7 | i18n | TC-015-090 |
| REQ-015 §7 | Farbkodierung | TC-015-091 |
| REQ-015-A §3.1 | Voranzucht-Berechnung | TC-015-040, TC-015-100 |
| REQ-015-A §3.2 | Direktsaat / Fallback / Eisheilige | TC-015-041, TC-015-042, TC-015-049 |
| REQ-015-A §3.3 | Wachstums-Balken Berechnung | TC-015-040, TC-015-101, TC-015-102, TC-015-104 |
| REQ-015-A §3.4 | Ernte-Balken / Wrap-around | TC-015-051 |
| REQ-015-A §3.5 | Bluete-Balken / Zierpflanzen | TC-015-043 |
| REQ-015-A §4 | Frosttermin-Konfiguration | TC-015-041, TC-015-049 |
| REQ-015-A §5 | Balken-Reihenfolge & Lueckenfreiheit | TC-015-040, TC-015-101, TC-015-102 |
| REQ-015-A §6 | Mehrere Anbauzeitraeume | TC-015-050, TC-015-104 |
| REQ-015-A §6.2 | Legacy-Felder / Abwaertskompatibilitaet | TC-015-103 |
| REQ-015-A §7 | Pflanzen ohne Aussaatdaten | TC-015-045 |
| REQ-015-A §9 | Akzeptanzkriterien AB-010 (Bluetepause) | TC-015-043 |

### Ueberpruefte Akzeptanzkriterien (§7 DoD REQ-015)

| Akzeptanzkriterium | Testfall(e) |
|-------------------|------------|
| Alle Tasks im Zeitraum als farbkodierte Events | TC-015-001, TC-015-010 |
| Monats-, Wochen-, Tages- und Agenda-Ansicht | TC-015-001, TC-015-004, TC-015-070 |
| Filter einzeln und kombiniert | TC-015-010 bis TC-015-014 |
| Timeline-Toggle | TC-015-020, TC-015-021 |
| Event-Popover mit Details und Link | TC-015-022, TC-015-023 |
| Feed-CRUD ueber UI-Dialog | TC-015-030 bis TC-015-036 |
| RFC 5545-konformer iCal | TC-015-082 |
| webcal:// URL korrekt generiert | TC-015-030, TC-015-032 |
| Token-Rotation invalidiert alten Token | TC-015-033, TC-015-081 |
| Farbkodierung konsistent | TC-015-091 |
| Responsive: Mobile Agenda, Desktop Grid | TC-015-070, TC-015-072 |
| i18n DE und EN | TC-015-090 |
| Aussaatkalender zeigt Zeitbalken | TC-015-040, TC-015-044 |
| Frosttermine konfigurierbar | TC-015-041 |
| Eisheiligen-Markierung sichtbar | TC-015-049 |
| Frostempfindliche Pflanzen nach Eisheiligen | TC-015-041 |
| Filter geplante vs. alle Pflanzen | TC-015-046 |
| Saisonuebersicht 12 Monatskarten | TC-015-060 |
| Aktueller Monat hervorgehoben | TC-015-061 |
| Klick auf Monatskarte wechselt Ansicht | TC-015-062 |
| Zierpflanzen zeigen Bluete-Balken (pink) | TC-015-043, TC-015-054 |
| Bluetepause erkannt (AB-010) | TC-015-043 |
| Filter "Blumen" korrekt | TC-015-054 |
| Filter "Jährlich wiederkehrend" | TC-015-046, TC-015-052 |
| Jahresvergleich (previous_run_key) | TC-015-053 |
