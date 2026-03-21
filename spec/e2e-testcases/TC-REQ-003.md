---
req_id: REQ-003
title: Phänologische Phasensteuerung & Ressourcen-Profile
category: Wachstumslogik
test_count: 42
coverage_areas:
  - Lebenszyklus-Konfiguration (LifecycleConfigSection)
  - Wachstumsphasen-Verwaltung (GrowthPhaseListSection, GrowthPhaseDialog)
  - Ressourcen- und Nährstoffprofile (ProfilesSection, ProfileEditDialog)
  - Phasenübergang manuell & Korrekturmodus (PhaseTransitionDialog)
  - Pflanzinstanz Phasen-Ansicht (PlantInstanceDetailPage Tab "Phasen")
  - Phasenverlauf-Tabelle (PhaseHistoryTable)
  - Phasen-Zeitstrahl (PlantPhaseTimeline / PhaseKamiTimeline)
  - Berechnungsseite VPD, GDD, Photoperiode (CalculationsPage)
  - Validierung Formularfelder (client-seitig Zod + server-seitig)
  - Rückwärts-Transition-Sperre & Korrekturmodus
  - Autoflower-Cultivar-Verhalten (Photoperiode konstant, HST-Warnung)
  - Dauerkulturen (Perennial, Zyklus-Neustart, Saison-Tracking)
generated: 2026-03-21
version: "2.3"
---

# Testfälle: REQ-003 — Phänologische Phasensteuerung & Ressourcen-Profile

## Übersicht

Dieses Dokument enthält alle End-to-End-Testfälle für REQ-003 aus der **Perspektive des Nutzers im Browser**. Jede Aktion beschreibt, was der Nutzer sieht, klickt, eingibt und als Ergebnis erwartet. API-Aufrufe und Datenbankzustände werden nicht beschrieben — nur sichtbare UI-Reaktionen.

Alle Test-IDs folgen dem Schema `TC-003-NNN`.

**Relevante URLs:**
- Pflanzinstanz-Liste: `/pflanzen/plant-instances`
- Pflanzinstanz-Detail: `/pflanzen/plant-instances/:key` (Tabs: info, phases, nutrient-plan, watering-log, care, activity-plan, tasks, edit)
- Stammdaten-Artenseite (mit Lebenszyklus-Tab): `/stammdaten/species/:key` → Tab "Lebenszyklus-Konfiguration"
- Berechnungsseite: `/pflanzen/calculations`

---

## Gruppe A: Lebenszyklus-Konfiguration (LifecycleConfigSection)

*Kontext: Tab "Lebenszyklus-Konfiguration" auf der Artenseite (`/stammdaten/species/:key`)*

---

## TC-003-001: Lebenszyklus-Konfiguration erstmalig anlegen (Happy Path)

**Anforderung**: REQ-003 §1 — Lifecycle-Konfiguration; §3 Datenvalidierung `LifecycleConfig`
**Priorität**: Critical
**Kategorie**: Happy Path

**Vorbedingungen:**
- Nutzer ist angemeldet und Mitglied eines Tenants
- Spezies "Cannabis sativa" existiert ohne Lebenszyklus-Konfiguration
- Nutzer navigiert zu `/stammdaten/species/:key` der genannten Spezies

**Testschritte:**
1. Nutzer klickt auf Tab "Lebenszyklus-Konfiguration"
2. Seite zeigt ein leeres Formular mit Standardwerten: Zyklustyp "annual", Photoperioden-Typ "day_neutral", alle Schalter (Dormanz, Vernalisation) ausgeschaltet
3. Nutzer wählt im Dropdown "Zyklustyp" den Wert "annual"
4. Nutzer wählt im Dropdown "Photoperioden-Typ" den Wert "short_day"
5. Nutzer gibt im Feld "Kritische Tageslänge (h)" den Wert `12` ein
6. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung erscheint (Snackbar mit Bestätigungstext)
- Das Formular zeigt keine Fehlermeldungen
- Beim erneuten Laden des Tabs sind die gespeicherten Werte vorausgefüllt: Zyklustyp "annual", Photoperioden-Typ "short_day", Kritische Tageslänge "12"

**Nachbedingungen:**
- Lebenszyklus-Konfiguration für die Spezies existiert in der Datenbank

**Tags**: [req-003, lifecycle-config, happy-path, stammdaten, annual]

---

## TC-003-002: Lebenszyklus-Konfiguration für perenniale Pflanze anlegen

**Anforderung**: REQ-003 §1 — Dauerkulturen-Modus; §2 `seasonal_cycles`; §3 `PerennialCycleEngine`
**Priorität**: High
**Kategorie**: Happy Path

**Vorbedingungen:**
- Spezies "Malus domestica" (Apfelbaum) existiert ohne Lebenszyklus-Konfiguration
- Nutzer navigiert zu Tab "Lebenszyklus-Konfiguration" dieser Spezies

**Testschritte:**
1. Nutzer wählt "Zyklustyp" → "perennial"
2. Nutzer gibt "Lebensdauer (Jahre)" → `25` ein
3. Nutzer aktiviert Schalter "Winterruhe erforderlich"
4. Nutzer aktiviert Schalter "Vernalisation erforderlich"
5. Nutzer gibt "Vernalisation (Tage)" → `60` ein
6. Nutzer wählt "Photoperioden-Typ" → "long_day"
7. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung erscheint
- Formular zeigt keine Validierungsfehler
- Tab "Wachstumsphasen" zeigt darunter eine leere Phasenliste mit Button "Phase erstellen"

**Nachbedingungen:**
- Lebenszyklus-Konfiguration mit `cycle_type=perennial`, `dormancy_required=true`, `vernalization_required=true` gespeichert

**Tags**: [req-003, lifecycle-config, perennial, happy-path, dauerkulturen]

---

## TC-003-003: Lebenszyklus-Konfiguration bearbeiten — UnsavedChangesGuard

**Anforderung**: REQ-003 §6 DoD — Vollständiges Tracking; NFR (UnsavedChangesGuard)
**Priorität**: Medium
**Kategorie**: Navigation / Formvalidierung

**Vorbedingungen:**
- Spezies mit vorhandener Lebenszyklus-Konfiguration (Zyklustyp "annual")
- Nutzer öffnet Tab "Lebenszyklus-Konfiguration"

**Testschritte:**
1. Nutzer ändert "Photoperioden-Typ" von "day_neutral" auf "short_day"
2. Nutzer klickt auf einen anderen Tab (z.B. "Sorten") ohne zu speichern

**Erwartetes Ergebnis:**
- Browser-Bestätigungsdialog erscheint mit dem Text "Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Wenn Nutzer "Abbrechen" klickt: Dialog schließt sich, Nutzer bleibt auf "Lebenszyklus-Konfiguration"-Tab mit der ungespeicherten Änderung
- Wenn Nutzer "Bestätigen" klickt: Nutzer wechselt zum angeklickten Tab ohne zu speichern

**Nachbedingungen:**
- Bei Abbrechen: Kein Datenverlust, Formular zeigt noch die geänderten Werte

**Tags**: [req-003, lifecycle-config, unsaved-changes-guard, navigation]

---

## TC-003-004: Bienniale Pflanze — Vernalisation-Pflichtfeld

**Anforderung**: REQ-003 §3 Datenvalidierung; CLAUDE.md — "Biennial lifecycle MUST have vernalization_required=true"
**Priorität**: High
**Kategorie**: Formvalidierung / Fehlermeldung

**Vorbedingungen:**
- Spezies ohne Lebenszyklus-Konfiguration
- Nutzer öffnet Tab "Lebenszyklus-Konfiguration"

**Testschritte:**
1. Nutzer wählt "Zyklustyp" → "biennial"
2. Nutzer lässt den Schalter "Vernalisation erforderlich" ausgeschaltet
3. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Fehlerbenachrichtigung erscheint (Snackbar oder Inline-Fehlermeldung)
- Die Konfiguration wird nicht gespeichert

**Nachbedingungen:**
- Keine Lebenszyklus-Konfiguration gespeichert

**Tags**: [req-003, lifecycle-config, biennial, validierung, fehlermeldung]

---

## Gruppe B: Wachstumsphasen-Verwaltung (GrowthPhaseListSection + GrowthPhaseDialog)

*Kontext: Tab "Lebenszyklus-Konfiguration" → Unterbereich "Wachstumsphasen" auf der Artenseite*

---

## TC-003-005: Wachstumsphase anlegen — Happy Path

**Anforderung**: REQ-003 §2 `growth_phases`; §6 DoD "Phasen-State-Machine"
**Priorität**: Critical
**Kategorie**: Happy Path

**Vorbedingungen:**
- Spezies mit vorhandener Lebenszyklus-Konfiguration
- Nutzer ist auf Tab "Lebenszyklus-Konfiguration"

**Testschritte:**
1. Nutzer klickt "Phase erstellen" (Button mit Plus-Icon)
2. Dialog "Phase erstellen" öffnet sich
3. Nutzer gibt im Feld "Name" den Wert `vegetative` ein
4. Nutzer gibt "Anzeigename" → `Vegetatives Wachstum` ein
5. Nutzer gibt "Typische Dauer (Tage)" → `28` ein
6. Nutzer gibt "Reihenfolge" → `2` ein
7. Nutzer wählt "Stresstoleranz" → "mittel"
8. Nutzer lässt "Endphase" und "Ernte erlaubt" deaktiviert
9. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- Die neue Phase "Vegetatives Wachstum" erscheint in der Phasenliste mit: Reihenfolge "2", Dauer "28d", Stresstoleranz "Mittel"
- Keine Chips "Endphase" oder "Ernte erlaubt" sichtbar

**Nachbedingungen:**
- Phase "vegetative" existiert als Wachstumsphase unter dieser Lebenszyklus-Konfiguration

**Tags**: [req-003, growth-phase, create, happy-path, stammdaten]

---

## TC-003-006: Wachstumsphase anlegen — Pflichtfeld "Name" fehlt

**Anforderung**: REQ-003 §3 Datenvalidierung — `GrowthPhase.name min(1)`
**Priorität**: High
**Kategorie**: Formvalidierung

**Vorbedingungen:**
- Dialog "Phase erstellen" ist geöffnet

**Testschritte:**
1. Nutzer lässt das Feld "Name" leer
2. Nutzer gibt "Typische Dauer (Tage)" → `14` ein
3. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Dialog bleibt geöffnet
- Das Feld "Name" zeigt eine Validierungsfehlermeldung (Pflichtfeld-Hinweis)
- Keine Erfolgsbenachrichtigung erscheint

**Nachbedingungen:**
- Keine Phase gespeichert

**Tags**: [req-003, growth-phase, validierung, pflichtfeld, fehlermeldung]

---

## TC-003-007: Wachstumsphase anlegen — "Typische Dauer" unter Minimalwert

**Anforderung**: REQ-003 §3 Zod-Schema `typical_duration_days.min(1)`
**Priorität**: Medium
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen:**
- Dialog "Phase erstellen" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Name" → `seedling` ein
2. Nutzer gibt "Typische Dauer (Tage)" → `0` ein
3. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Dialog bleibt geöffnet
- Das Feld "Typische Dauer (Tage)" zeigt einen Validierungsfehler (Minimalwert 1)
- Keine Phase gespeichert

**Tags**: [req-003, growth-phase, validierung, grenzwert, minimum]

---

## TC-003-008: Wachstumsphase als "Endphase" und "Ernte erlaubt" markieren

**Anforderung**: REQ-003 §2 `growth_phases.is_terminal`, `allows_harvest`; §6 DoD "Multi-Phase-Harvests"
**Priorität**: High
**Kategorie**: Happy Path / Zustandswechsel

**Vorbedingungen:**
- Dialog "Phase erstellen" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Name" → `ripening` ein
2. Nutzer gibt "Typische Dauer (Tage)" → `14` ein
3. Nutzer gibt "Reihenfolge" → `5` ein
4. Nutzer aktiviert Schalter "Endphase"
5. Nutzer aktiviert Schalter "Ernte erlaubt"
6. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich mit Erfolgsbenachrichtigung
- In der Phasenliste erscheint "ripening" mit zwei farbigen Chips: orangefarbener Chip "Endphase" und grüner Chip "Ernte erlaubt"

**Nachbedingungen:**
- Phase mit `is_terminal=true`, `allows_harvest=true` gespeichert

**Tags**: [req-003, growth-phase, is-terminal, allows-harvest, chips]

---

## TC-003-009: Wachstumsphase bearbeiten (Edit-Dialog öffnen per Tabellenklick)

**Anforderung**: REQ-003 §2 `growth_phases` — CRUD
**Priorität**: High
**Kategorie**: Happy Path / Detailansicht

**Vorbedingungen:**
- Mindestens eine Wachstumsphase existiert in der Liste

**Testschritte:**
1. Nutzer klickt auf eine Zeile in der Phasenliste
2. Dialog öffnet sich mit Titel "Bearbeiten"
3. Alle Felder sind mit den aktuellen Werten vorausgefüllt (Name, Anzeigename, Dauer, Reihenfolge, Stresstoleranz, Schalter)
4. Nutzer ändert "Typische Dauer (Tage)" von `28` auf `35`
5. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- In der Phasenliste zeigt die bearbeitete Phase nun `35d` als Dauer

**Tags**: [req-003, growth-phase, edit, dialog, happy-path]

---

## TC-003-010: Wachstumsphase löschen — Bestätigungsdialog

**Anforderung**: REQ-003 §2 `growth_phases` — CRUD; UI-Pattern ConfirmDialog (destructive)
**Priorität**: High
**Kategorie**: Dialog / Zustandswechsel

**Vorbedingungen:**
- Mindestens eine Wachstumsphase existiert in der Liste

**Testschritte:**
1. Nutzer klickt den Löschen-Icon-Button (Papierkorb) in der Zeile der Phase
2. Bestätigungsdialog erscheint mit dem Text "Sind Sie sicher, dass Sie \"[Phasenname]\" löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
3. Nutzer klickt "Abbrechen"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Phase ist weiterhin in der Liste vorhanden

**Nachbedingungen:**
- Keine Phase gelöscht

**Tags**: [req-003, growth-phase, delete, confirm-dialog, abbruch]

---

## TC-003-011: Wachstumsphase löschen — Bestätigung

**Anforderung**: REQ-003 §2 `growth_phases` — CRUD
**Priorität**: High
**Kategorie**: Zustandswechsel

**Vorbedingungen:**
- Mindestens eine Wachstumsphase existiert
- Löschen-Bestätigungsdialog ist geöffnet

**Testschritte:**
1. Nutzer klickt "Löschen" (destructive button) im Bestätigungsdialog

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- Die gelöschte Phase ist nicht mehr in der Phasenliste sichtbar

**Tags**: [req-003, growth-phase, delete, bestätigung, zustandswechsel]

---

## TC-003-012: Wachstumsphasen-Liste — Sortierung nach Reihenfolge

**Anforderung**: REQ-003 §2 `growth_phases.sequence_order`; UI-Pattern DataTable
**Priorität**: Medium
**Kategorie**: Listenansicht

**Vorbedingungen:**
- Mindestens drei Wachstumsphasen mit unterschiedlichen `sequence_order`-Werten existieren (z.B. 0, 2, 1)

**Testschritte:**
1. Nutzer navigiert zu Tab "Lebenszyklus-Konfiguration"

**Erwartetes Ergebnis:**
- Phasenliste ist standardmäßig aufsteigend nach der Spalte "#" (Reihenfolge) sortiert
- Phase mit `sequence_order=0` erscheint als erste Zeile, dann `sequence_order=1`, dann `sequence_order=2`

**Tags**: [req-003, growth-phase, sortierung, listenansicht, sequence-order]

---

## TC-003-013: Wachstumsphasen-Liste — Suchfunktion

**Anforderung**: REQ-003 §2 `growth_phases`; UI-Pattern DataTable Suche
**Priorität**: Low
**Kategorie**: Listenansicht

**Vorbedingungen:**
- Mehrere Wachstumsphasen existieren (z.B. "vegetative", "flowering", "seedling")

**Testschritte:**
1. Nutzer gibt in das Suchfeld "Tabelle durchsuchen..." den Begriff `flower` ein
2. Nutzer wartet ca. 300 ms (debounced)

**Erwartetes Ergebnis:**
- Tabelle zeigt nur Zeilen, die "flower" im Namen oder Anzeigenamen enthalten
- Zeilen für "vegetative" und "seedling" sind nicht sichtbar

**Tags**: [req-003, growth-phase, suche, listenansicht, datatabel]

---

## Gruppe C: Ressourcen- und Nährstoffprofile (ProfilesSection + ProfileEditDialog)

*Kontext: In der Phasenliste auf "Profil"-Button klicken → ProfilesSection erscheint / Edit-Dialog*

---

## TC-003-014: Standardwerte für Ressourcenprofil automatisch generieren

**Anforderung**: REQ-003 §3 `ResourceProfileGenerator`; §6 DoD "Profile-Versionierung"
**Priorität**: Critical
**Kategorie**: Happy Path

**Vorbedingungen:**
- Wachstumsphase "vegetative" existiert ohne zugewiesene Profile
- Nutzer klickt in der Phasenliste den Button "Profil" für diese Phase

**Testschritte:**
1. Die `ProfilesSection` erscheint unterhalb der Tabelle
2. Nutzer sieht den Hinweis "Noch kein Profil vorhanden. Standardwerte generieren oder manuell eingeben."
3. Nutzer klickt "Standardwerte generieren"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung erscheint
- Die `ProfilesSection` zeigt nun zwei Karten: "Anforderungsprofil" und "Nährstoffprofil"
- Das Anforderungsprofil zeigt numerische Werte für PPFD, Photoperiode, Tagestemperatur, Nachttemperatur, Luftfeuchtigkeit Tag/Nacht, VPD-Zielwert
- Das Nährstoffprofil zeigt NPK-Verhältnis (z.B. 3-1-2 für Vegetativ), Ziel-EC und Ziel-pH

**Tags**: [req-003, profile, generate-defaults, happy-path, resource-profile, nutrient-profile]

---

## TC-003-015: Ressourcenprofil manuell bearbeiten — Happy Path

**Anforderung**: REQ-003 §3 `RequirementProfileDefinition`; §6 DoD "Ressourcen-Profile"
**Priorität**: High
**Kategorie**: Happy Path

**Vorbedingungen:**
- Wachstumsphase mit vorhandenem Anforderungsprofil
- ProfilesSection ist sichtbar
- Nutzer klickt den Bearbeiten-Icon-Button (Stift)

**Testschritte:**
1. Dialog "Profile bearbeiten" öffnet sich
2. Nutzer sieht zwei Sektionen: "Anforderungsprofil" (Licht, Temperatur, Luftfeuchtigkeit, Bewässerung) und "Nährstoffprofil" (NPK, EC, pH)
3. Nutzer ändert "Licht-PPFD" von `400` auf `600`
4. Nutzer ändert "Photoperiode (h)" von `18` auf `12`
5. Nutzer ändert NPK-Felder: N=`1`, P=`3`, K=`3`
6. Nutzer ändert "Ziel-EC" auf `1.8`
7. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- In der ProfilesSection zeigt das Anforderungsprofil jetzt PPFD `600`, Photoperiode `12 h`
- Das Nährstoffprofil zeigt NPK `1-3-3` und EC `1.8`

**Tags**: [req-003, profile, edit, happy-path, ppfd, photoperiode, npk, ec]

---

## TC-003-016: Ressourcenprofil — Nachttemperatur höher als Tagestemperatur

**Anforderung**: REQ-003 §3 `validate_temp_range` — Nacht muss niedriger als Tag sein
**Priorität**: High
**Kategorie**: Formvalidierung / Fehlermeldung

**Vorbedingungen:**
- Dialog "Profile bearbeiten" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Tagestemperatur" → `20` ein
2. Nutzer gibt "Nachttemperatur" → `25` ein (höher als Tag)
3. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Fehlerbenachrichtigung erscheint (Snackbar oder Inline-Fehlermeldung)
- Dialog bleibt geöffnet, Profile werden nicht gespeichert

**Tags**: [req-003, profile, validierung, temperatur, nacht-tag, fehlermeldung]

---

## TC-003-017: Nährstoffprofil — EC-Grenzwert max 4.0

**Anforderung**: REQ-003 §3 `target_ec_ms: Field(ge=0.0, le=4.0)`
**Priorität**: Medium
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen:**
- Dialog "Profile bearbeiten" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Ziel-EC" → `4.5` ein (über Maximum)
2. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Validierungsfehlermeldung am Feld "Ziel-EC" erscheint
- Dialog bleibt geöffnet, Profile werden nicht gespeichert

**Tags**: [req-003, profile, validierung, ec, grenzwert, maximum]

---

## TC-003-018: Nährstoffprofil — pH-Bereich 4.0–8.0

**Anforderung**: REQ-003 §3 `target_ph: Field(ge=4.0, le=8.0)`
**Priorität**: Medium
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen:**
- Dialog "Profile bearbeiten" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Ziel-pH" → `3.5` ein (unter Minimum)
2. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Validierungsfehlermeldung am Feld "Ziel-pH" erscheint (Minimalwert 4.0)
- Dialog bleibt geöffnet, Profile werden nicht gespeichert

**Tags**: [req-003, profile, validierung, ph, grenzwert, minimum]

---

## Gruppe D: Manuelle Phasenübergänge (PlantInstanceDetailPage + PhaseTransitionDialog)

*Kontext: Pflanzinstanz-Detailseite `/pflanzen/plant-instances/:key` → Tab "Phasen"*

---

## TC-003-019: Manuelle Phasentransition — Happy Path

**Anforderung**: REQ-003 §1 "Manual-Override"; §6 DoD "Manual-Override"
**Priorität**: Critical
**Kategorie**: Happy Path / Zustandswechsel

**Vorbedingungen:**
- Pflanzinstanz existiert mit zugeordneter Spezies und Lebenszyklus-Konfiguration
- Pflanzinstanz befindet sich in Phase "vegetative"
- Mindestens eine folgende Phase ("flowering") existiert in der Lebenszyklus-Konfiguration
- Nutzer navigiert zu `/pflanzen/plant-instances/:key` → Tab "Phasen"

**Testschritte:**
1. Nutzer sieht den Button "Phasenwechsel" (mit Icon SwapHoriz)
2. Nutzer klickt "Phasenwechsel"
3. Dialog "Phasenwechsel" öffnet sich (`data-testid="phase-transition-dialog"`)
4. Dropdown "Zielphase" zeigt alle verfügbaren Phasen der Lebenszyklus-Konfiguration
5. Nutzer wählt "flowering" aus dem Dropdown (Anzeige: "Blüte (56d)")
6. Nutzer gibt im Feld "Grund" den Text `Blüte manuell eingeleitet` ein
7. Schalter "Phase korrigieren (Fehlanlage)" ist deaktiviert
8. Nutzer klickt "Bestätigen"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- Auf dem Tab "Phasen" zeigt die Anzeige "Aktuelle Phase" jetzt "flowering" (oder den konfigurierten Anzeigenamen)
- Im Phasenverlauf (PhaseHistoryTable) erscheint ein neuer Eintrag für "vegetative" mit gesetztem Enddatum und dem eingegebenen Übergangsgrund

**Nachbedingungen:**
- Pflanzinstanz befindet sich in Phase "flowering"

**Tags**: [req-003, phase-transition, manuell, happy-path, dialog, phase-history]

---

## TC-003-020: Phasentransition — Zielphase nicht ausgewählt (Button deaktiviert)

**Anforderung**: REQ-003 §3 State-Machine Validierung; PhaseTransitionDialog `disabled={!targetPhaseKey}`
**Priorität**: High
**Kategorie**: Formvalidierung

**Vorbedingungen:**
- PhaseTransitionDialog ist geöffnet
- Kein Wert im Dropdown "Zielphase" ausgewählt

**Testschritte:**
1. Nutzer sieht, dass der Dropdown "Zielphase" noch leer ist
2. Nutzer prüft den Bestätigen-Button

**Erwartetes Ergebnis:**
- Der Bestätigen-Button ("Bestätigen") ist deaktiviert (disabled) und kann nicht angeklickt werden

**Tags**: [req-003, phase-transition, validierung, button-disabled, zielphase]

---

## TC-003-021: Phasentransition rückwärts — Korrekturmodus erforderlich

**Anforderung**: REQ-003 §3 `validate_transition` — Rückwärts-Transition-Sperre; §6 DoD "Rückwärts-Transition"
**Priorität**: Critical
**Kategorie**: Fehlermeldung / Zustandswechsel

**Vorbedingungen:**
- Pflanzinstanz befindet sich in Phase "flowering" (sequence_order 3)
- Phase "vegetative" (sequence_order 2) existiert in der Lebenszyklus-Konfiguration
- Dialog "Phasenwechsel" ist geöffnet

**Testschritte:**
1. Nutzer wählt "vegetative" als Zielphase (niedrigere sequence_order als aktuelle Phase)
2. Nutzer lässt den Schalter "Phase korrigieren (Fehlanlage)" deaktiviert
3. Nutzer klickt "Bestätigen"

**Erwartetes Ergebnis:**
- Fehlerbenachrichtigung erscheint (Snackbar mit Fehlermeldung über ungültige Rückwärts-Transition)
- Dialog bleibt geöffnet, Phase wird nicht gewechselt

*Siehe auch: TC-003-022 für den erfolgreichen Korrekturmodus*

**Tags**: [req-003, phase-transition, rueckwaerts, rückwärts-sperre, fehlermeldung]

---

## TC-003-022: Phasentransition rückwärts — Korrekturmodus (Fehlanlage)

**Anforderung**: REQ-003 §6 DoD "Rückwärts-Transition"; PhaseTransitionDialog `force`-Flag
**Priorität**: High
**Kategorie**: Happy Path / Zustandswechsel

**Vorbedingungen:**
- Pflanzinstanz befindet sich in Phase "flowering"
- Dialog "Phasenwechsel" ist geöffnet

**Testschritte:**
1. Nutzer aktiviert Schalter "Phase korrigieren (Fehlanlage)"
2. Eine orange Warnung erscheint im Dialog: "Erlaubt das Zurücksetzen auf eine frühere Phase, z.B. bei einer Fehlanlage."
3. Der Bestätigen-Button wechselt zu orange und zeigt jetzt "Phase korrigieren" statt "Bestätigen"
4. Nutzer wählt "vegetative" als Zielphase
5. Nutzer klickt "Phase korrigieren"

**Erwartetes Ergebnis:**
- Dialog schließt sich mit Erfolgsbenachrichtigung
- Aktuelle Phase der Pflanzinstanz ist jetzt wieder "vegetative"
- Phasenverlauf dokumentiert den Eintrag mit Übergangsgrund "correction"

**Tags**: [req-003, phase-transition, force, korrekturmodus, zustandswechsel]

---

## TC-003-023: Phasentransition — Kein Lifecycle zugeordnet (leere Dropdown-Liste)

**Anforderung**: REQ-003 §5 Abhängigkeiten — LifecycleConfig muss vorhanden sein
**Priorität**: Medium
**Kategorie**: Fehlermeldung / Edge Case

**Vorbedingungen:**
- Pflanzinstanz ist einer Spezies zugeordnet, die keine Lebenszyklus-Konfiguration hat
- Dialog "Phasenwechsel" wird geöffnet

**Testschritte:**
1. Nutzer öffnet den Dialog "Phasenwechsel"
2. Das Dropdown "Zielphase" wird geladen

**Erwartetes Ergebnis:**
- Dropdown "Zielphase" ist leer (keine Optionen verfügbar)
- Der Bestätigen-Button bleibt deaktiviert
- Nutzer kann keine Transition durchführen

**Tags**: [req-003, phase-transition, edge-case, kein-lifecycle, leere-dropdown]

---

## Gruppe E: Phasen-Zeitstrahl und Verlaufsansicht

*Kontext: Pflanzinstanz-Detailseite Tab "Phasen"*

---

## TC-003-024: Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen

**Anforderung**: REQ-003 §6 DoD "Phase-History"; PhaseKamiTimeline
**Priorität**: High
**Kategorie**: Detailansicht

**Vorbedingungen:**
- Pflanzinstanz mit vollständiger Lebenszyklus-Konfiguration (mind. 4 Phasen: germination, seedling, vegetative, flowering)
- Pflanzinstanz hat Phase "germination" (abgeschlossen) und "seedling" (abgeschlossen) in der History
- Pflanzinstanz befindet sich aktuell in Phase "vegetative"

**Testschritte:**
1. Nutzer navigiert zur Pflanzinstanz-Detailseite → Tab "Phasen"

**Erwartetes Ergebnis:**
- Der Phasen-Zeitstrahl zeigt "germination" als abgeschlossen (completed — mit tatsächlichem Start- und Enddatum)
- "seedling" als abgeschlossen
- "vegetative" als aktiv/current (mit Startdatum und berechnetem Enddatum)
- "flowering" als geplant/projected (mit prognostizierten Daten, grau oder mit anderem visuellen Stil)
- Eine Lade-Animation erscheint während der Zeitstrahl geladen wird; danach ist sie nicht mehr sichtbar

**Tags**: [req-003, phase-timeline, completed, current, projected, detailansicht]

---

## TC-003-025: Phasen-Zeitstrahl ohne Spezies-Zuordnung — Leerer Zustand

**Anforderung**: REQ-003 §5 Abhängigkeiten; PlantPhaseTimeline edge case
**Priorität**: Low
**Kategorie**: Edge Case / Detailansicht

**Vorbedingungen:**
- Pflanzinstanz ohne zugeordnete Spezies

**Testschritte:**
1. Nutzer navigiert zur Pflanzinstanz-Detailseite → Tab "Phasen"

**Erwartetes Ergebnis:**
- Kein Zeitstrahl wird gerendert (leerer Bereich oder Hinweistext)
- Kein Fehler im UI sichtbar

**Tags**: [req-003, phase-timeline, leer, keine-spezies, edge-case]

---

## TC-003-026: Phasenverlauf-Tabelle zeigt historische Einträge

**Anforderung**: REQ-003 §2 `phase_histories`; §6 DoD "Phase-History"
**Priorität**: High
**Kategorie**: Detailansicht

**Vorbedingungen:**
- Pflanzinstanz hat mindestens zwei abgeschlossene Phasen in der History

**Testschritte:**
1. Nutzer öffnet Tab "Phasen" auf der Pflanzinstanz-Detailseite
2. Nutzer scrollt zur Phasenverlauf-Tabelle

**Erwartetes Ergebnis:**
- Tabelle zeigt für jede abgeschlossene Phase: Beginn-Datum, Ende-Datum, Dauer (Tage), Übergangsgrund
- Die aktuelle (noch nicht abgeschlossene) Phase erscheint ohne Enddatum (Feld "Ende" leer oder "—")
- Einträge sind chronologisch sortiert (neueste oben oder älteste oben — konsistent)

**Tags**: [req-003, phase-history, tabelle, verlauf, detailansicht]

---

## Gruppe F: VPD-, GDD- und Photoperioden-Berechnungsseite

*Kontext: `/pflanzen/calculations`*

---

## TC-003-027: VPD-Rechner — Happy Path (Ergebnis im optimalen Bereich)

**Anforderung**: REQ-003 §3 `VPDCalculator`; §6 Testszenario 2; §6 DoD "VPD-Berechnung"
**Priorität**: High
**Kategorie**: Happy Path

**Vorbedingungen:**
- Nutzer navigiert zu `/pflanzen/calculations`

**Testschritte:**
1. Nutzer sieht den Bereich "VPD-Rechner" auf der Seite
2. Nutzer gibt "Temperatur (°C)" → `28` ein
3. Nutzer gibt "Luftfeuchtigkeit (%)" → `55` ein
4. Nutzer klickt "Berechnen"

**Erwartetes Ergebnis:**
- Das Feld "VPD (kPa)" zeigt einen Wert nahe `1.28` kPa (gemäß Spezifikation Szenario 2: SVP_leaf(26°C) - AVP(28°C, 55%) = ca. 1.28 kPa)
- Das Feld "Status" zeigt einen grünen/positiven Indikator (z.B. "OPTIMAL" oder entsprechendes visuelles Feedback)

**Tags**: [req-003, vpd, rechner, berechnung, optimal, happy-path]

---

## TC-003-028: VPD-Rechner — Ergebnis "zu niedrig" bei hoher Luftfeuchtigkeit

**Anforderung**: REQ-003 §3 `VPDCalculator.get_vpd_recommendation`; §6 Testszenario 2
**Priorität**: High
**Kategorie**: Zustandswechsel / Fehlermeldung

**Vorbedingungen:**
- Nutzer ist auf `/pflanzen/calculations`

**Testschritte:**
1. Nutzer gibt "Temperatur (°C)" → `28` ein
2. Nutzer gibt "Luftfeuchtigkeit (%)" → `80` ein
3. Nutzer klickt "Berechnen"

**Erwartetes Ergebnis:**
- Das Feld "VPD (kPa)" zeigt einen Wert nahe `0.34` kPa
- Das Feld "Status" zeigt einen roten/negativen Indikator (z.B. "ZU NIEDRIG" oder entsprechendes visuelles Feedback)

**Tags**: [req-003, vpd, rechner, zu-niedrig, hohe-luftfeuchtigkeit, status]

---

## TC-003-029: GDD-Rechner — Tagesakkumulation berechnen

**Anforderung**: REQ-003 §3 `PhaseTransitionEngine.calculate_daily_gdd`; §6 DoD "GDD-Transition"
**Priorität**: High
**Kategorie**: Happy Path

**Vorbedingungen:**
- Nutzer ist auf `/pflanzen/calculations`

**Testschritte:**
1. Nutzer sieht den Bereich "GDD-Rechner"
2. Nutzer gibt "Basistemperatur (°C)" → `10` ein
3. Nutzer klickt "Berechnen"

**Erwartetes Ergebnis:**
- Das Feld "Akkumulierte GDD" zeigt einen numerischen Wert (Berechnung basierend auf aktuellen oder eingegebenen Temperaturen)
- Kein Fehler im UI sichtbar

**Tags**: [req-003, gdd, rechner, berechnung, happy-path]

---

## TC-003-030: Photoperioden-Übergang berechnen (18h → 12h über 7 Tage)

**Anforderung**: REQ-003 §3 `PhotoperiodManager.calculate_transition_schedule`; §6 Testszenario 4
**Priorität**: High
**Kategorie**: Happy Path

**Vorbedingungen:**
- Nutzer ist auf `/pflanzen/calculations`

**Testschritte:**
1. Nutzer gibt "Aktuelle Stunden" → `18` ein
2. Nutzer gibt "Zielstunden" → `12` ein
3. Nutzer gibt "Übergangstage" → `7` ein
4. Nutzer klickt "Berechnen"

**Erwartetes Ergebnis:**
- Das Ergebnis zeigt einen schrittweisen Plan über 8 Einträge (Tag 0 bis Tag 7)
- Tag 0 zeigt `18:00 h`
- Tag 7 zeigt `12:00 h` (Ziel erreicht)
- Zwischenschritte zeigen graduell absteigende Werte (pro Tag ca. -51 Minuten)

**Tags**: [req-003, photoperiode, rechner, transition, graduell, 7-tage]

---

## TC-003-031: Berechnungsseite — Eingabe außerhalb des gültigen Bereichs (VPD)

**Anforderung**: REQ-003 §3 Formvalidierung — Grenzwerte
**Priorität**: Medium
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen:**
- Nutzer ist auf `/pflanzen/calculations`

**Testschritte:**
1. Nutzer gibt "Luftfeuchtigkeit (%)" → `110` ein (über 100)
2. Nutzer klickt "Berechnen"

**Erwartetes Ergebnis:**
- Validierungsfehlermeldung erscheint am Feld (Maximalwert 100)
- Keine Berechnung wird durchgeführt, kein Ergebnis angezeigt

**Tags**: [req-003, vpd, validierung, grenzwert, luftfeuchtigkeit, maximum]

---

## Gruppe G: Pflanzinstanz-Listenansicht — Filter und Spalten

---

## TC-003-032: Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte

**Anforderung**: REQ-003 §6 DoD "Dashboard-Integration", "Listenansicht-Filter"
**Priorität**: High
**Kategorie**: Listenansicht

**Vorbedingungen:**
- Mehrere Pflanzinstanzen existieren, davon mindestens eine mit zugewiesener Phase "vegetative" und eine mit "flowering"

**Testschritte:**
1. Nutzer navigiert zu `/pflanzen/plant-instances`

**Erwartetes Ergebnis:**
- Tabelle zeigt eine Spalte für die aktuelle Phase (Phase-Badge oder Chip)
- Pflanzinstanzen ohne zugewiesene Phase zeigen "—" oder leeren Wert in der Phasenspalte

**Tags**: [req-003, plant-list, phase-spalte, listenansicht]

---

## TC-003-033: Pflanzinstanz erstellen mit Spezies-Zuordnung

**Anforderung**: REQ-003 §5 Abhängigkeiten — Pflanzinstanz braucht Spezies für Phasensteuerung
**Priorität**: High
**Kategorie**: Happy Path

**Vorbedingungen:**
- Spezies "Cannabis sativa" mit vollständiger Lebenszyklus-Konfiguration und Phasen existiert
- Nutzer ist auf `/pflanzen/plant-instances`

**Testschritte:**
1. Nutzer klickt "Pflanze erstellen" (Button mit Plus-Icon)
2. Dialog "Pflanze erstellen" öffnet sich
3. Nutzer wählt Spezies "Cannabis sativa" aus dem Dropdown
4. Nutzer gibt "Gepflanzt am" → aktuelles Datum ein
5. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich mit Erfolgsbenachrichtigung
- Neue Pflanzinstanz erscheint in der Liste
- Bei Klick auf die neue Pflanzinstanz → Tab "Phasen" zeigt: Kein aktiver Phasenübergang noch nicht gesetzt ("Aktuelle Phase" zeigt leeren Zustand oder erste Phase der Konfiguration)

**Tags**: [req-003, plant-create, spezies-zuordnung, happy-path]

---

## Gruppe H: Autoflower-Cultivar-Spezifika

*Anforderung: REQ-003 §1 "Autoflower (Cultivar-Level)"; §3 AutoflowerTransitionPreset; §6 DoD Autoflower-Punkte*

---

## TC-003-034: Autoflower-Pflanzinstanz — Phasenübergang ohne Photoperioden-Wechsel (UI-Indikator)

**Anforderung**: REQ-003 §6 DoD "Autoflower-Lichtprofil", Testszenario 3c
**Priorität**: High
**Kategorie**: Zustandswechsel / Detailansicht

**Vorbedingungen:**
- Spezies "Cannabis sativa" mit Cultivar "Northern Lights Auto" (`photoperiod_type='autoflower'`) existiert
- Pflanzinstanz mit diesem Autoflower-Cultivar befindet sich in Phase "vegetative"
- Das Ressourcenprofil der Phase zeigt Photoperiode `20 h` (Autoflower-Standard)
- Nutzer navigiert zur Detailseite → Tab "Phasen"

**Testschritte:**
1. Nutzer öffnet Dialog "Phasenwechsel"
2. Nutzer wählt Zielphase "flowering"
3. Nutzer klickt "Bestätigen"

**Erwartetes Ergebnis:**
- Phase wechselt zu "flowering"
- Das auf der Detailseite angezeigte Ressourcenprofil der Phase "flowering" zeigt weiterhin Photoperiode `20 h` (kein Wechsel auf 12 h)
- Keine Warnung über Photoperioden-Wechsel sichtbar

*Hinweis: Ohne Autoflower-Erkennung würde das System auf 12 h wechseln — dieser Test stellt sicher, dass dies NICHT passiert.*

**Tags**: [req-003, autoflower, photoperiode, kein-12h-wechsel, flowering, zustandswechsel]

---

## TC-003-035: Autoflower — HST-Methode erzeugt Warnung im Aufgaben-Workflow

**Anforderung**: REQ-003 §3 `AutoflowerTrainingGuard`; §6 Testszenario 3b; Cross-Ref REQ-006
**Priorität**: Medium
**Kategorie**: Fehlermeldung / Warnung

**Vorbedingungen:**
- Pflanzinstanz mit Autoflower-Cultivar befindet sich in Phase "vegetative" seit 10 Tagen
- Nutzer navigiert zur Pflanzinstanz-Detailseite

**Testschritte:**
1. Nutzer öffnet Tab "Aktivitätsplan" oder navigiert zur Aufgabenerstellung
2. Nutzer erstellt einen Task mit Trainings-Methode "Topping" (eine HST-Methode)
3. System verarbeitet die Aufgaben-Anfrage

**Erwartetes Ergebnis:**
- Eine Warnmeldung erscheint im UI: Text enthält sinngemäß "HST-Methode nicht empfohlen" und Hinweis auf die begrenzte vegetative Phase bei Autoflower
- Die Aufgabe wird NICHT blockiert — Nutzer kann die Warnung ignorieren und den Task trotzdem erstellen
- Bei LST-Methoden (z.B. "Bending", "ScrOG"): Keine Warnung, direkte Erstellung

**Tags**: [req-003, autoflower, hst-warnung, training, topping, warnung-nicht-blockade]

---

## Gruppe I: Dauerkulturen und Saisonzyklus

*Anforderung: REQ-003 §1 Dauerkulturen-Modus; §3 PerennialCycleEngine; §6 Szenarien 5–7*

---

## TC-003-036: Perenniale Pflanze — Saisonales Phasen-Template in der Detailansicht

**Anforderung**: REQ-003 §6 DoD "Dauerkulturen-Zyklus", "Perennial-Phasen-Template"; Szenario 5
**Priorität**: High
**Kategorie**: Detailansicht

**Vorbedingungen:**
- Spezies "Malus domestica" mit `cycle_type=perennial` und vollständigem Phasen-Template existiert (dormancy, bud_break, vegetative, flowering, fruit_development, ripening, senescence)
- Pflanzinstanz (Apfelbaum) existiert und befindet sich in Phase "dormancy"

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Apfelbaum-Pflanzinstanz → Tab "Phasen"

**Erwartetes Ergebnis:**
- Phasen-Zeitstrahl zeigt alle 7 Phasen des perennialen Templates
- Phase "dormancy" ist als aktiv/current markiert
- Phasen bud_break, vegetative, flowering, fruit_development, ripening, senescence sind als geplant/projected angezeigt
- `is_recurring`-Phasen sind visuell gekennzeichnet (falls implementiert)

**Tags**: [req-003, perennial, dauerkulturen, phasen-template, dormancy, seasonal]

---

## TC-003-037: Perenniale Pflanze — Zyklischer Übergang (Seneszenz → Dormanz) mit is_cycle_restart

**Anforderung**: REQ-003 §3 Validierung `is_cycle_restart`; §6 DoD "Zyklische Transition"; Szenario 7
**Priorität**: High
**Kategorie**: Zustandswechsel / Edge Case

**Vorbedingungen:**
- Perenniale Pflanzinstanz befindet sich in Phase "senescence" (sequence_order 6)
- Die Übergangsregel `senescence → dormancy` hat `is_cycle_restart=true` konfiguriert
- Dialog "Phasenwechsel" ist geöffnet

**Testschritte:**
1. Nutzer wählt Zielphase "dormancy" (sequence_order 0 — normalerweise Rückwärts-Transition)
2. Nutzer lässt Schalter "Phase korrigieren (Fehlanlage)" deaktiviert
3. Nutzer klickt "Bestätigen"

**Erwartetes Ergebnis:**
- Phasenwechsel wird ERFOLGREICH durchgeführt (keine Rückwärts-Transition-Fehlermeldung)
- Pflanzinstanz ist jetzt in Phase "dormancy"
- Erfolgsbenachrichtigung erscheint
- Im Phasenverlauf ist der Übergang dokumentiert

*Hinweis: Dieser Test unterscheidet sich von TC-003-021, wo eine normale Rückwärts-Transition blockiert wird. Hier erlaubt `is_cycle_restart=true` den Übergang explizit.*

*Siehe auch: TC-003-021 für blockierte Rückwärts-Transition ohne is_cycle_restart*

**Tags**: [req-003, perennial, is-cycle-restart, zyklisch, seneszenz, dormancy, rueckwaerts-erlaubt]

---

## TC-003-038: Perenniale Pflanze — Reifegradanzeige in der Saisonansicht

**Anforderung**: REQ-003 §3 `PerennialCycleEngine.get_maturity_stage`; §6 DoD "Reifegrad-Berechnung"; Szenario 5 und 6
**Priorität**: Medium
**Kategorie**: Detailansicht

**Vorbedingungen:**
- Apfelbaum-Pflanzinstanz, gepflanzt 2024, `first_bearing_year=3`
- Pflanzinstanz durchläuft Saison 1 (2024)

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Pflanzinstanz → Tab "Phasen"
2. Nutzer sucht nach Anzeige des aktuellen Reifegrades / Saisoninformationen

**Erwartetes Ergebnis:**
- Saisonales Info-Element zeigt Reifegrad "juvenil" (da Alter < 3 Jahre)
- Saison-Nummer "1" und Jahr "2024" sind sichtbar

**Tags**: [req-003, perennial, reifegrad, juvenile, saison, maturity-stage]

---

## Gruppe J: Gießintervall-Konfiguration in Wachstumsphasen

---

## TC-003-039: Wachstumsphase mit phasenspezifischem Gießintervall anlegen

**Anforderung**: REQ-003 §2 `growth_phases` — `watering_interval_days`; GrowthPhaseDialog Feld
**Priorität**: Medium
**Kategorie**: Happy Path

**Vorbedingungen:**
- Dialog "Phase erstellen" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Name" → `dormancy` ein
2. Nutzer gibt "Typische Dauer (Tage)" → `90` ein
3. Nutzer gibt "Gießintervall (Tage)" → `14` ein
4. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Phase wird angelegt
- In der Phasenliste zeigt die Spalte "Gießintervall (Tage)" den Wert `14d`

**Tags**: [req-003, growth-phase, gießintervall, watering-interval, happy-path]

---

## TC-003-040: Wachstumsphase — Gießintervall über Maximalwert 90 Tage

**Anforderung**: REQ-003 Zod-Schema `watering_interval_days.max(90)`
**Priorität**: Low
**Kategorie**: Formvalidierung / Grenzwert

**Vorbedingungen:**
- Dialog "Phase erstellen" oder "Bearbeiten" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Gießintervall (Tage)" → `95` ein (über Maximum)
2. Nutzer klickt "Erstellen" / "Speichern"

**Erwartetes Ergebnis:**
- Validierungsfehlermeldung erscheint am Feld "Gießintervall (Tage)" (Maximalwert 90)
- Phase wird nicht gespeichert

**Tags**: [req-003, growth-phase, gießintervall, validierung, maximum]

---

## TC-003-041: Wachstumsphase — Gießintervall leer lassen (kein Pflichtfeld)

**Anforderung**: REQ-003 Zod-Schema `watering_interval_days` nullable
**Priorität**: Low
**Kategorie**: Grenzwert / Happy Path

**Vorbedingungen:**
- Dialog "Phase erstellen" ist geöffnet

**Testschritte:**
1. Nutzer gibt "Name" → `seedling` ein
2. Nutzer gibt "Typische Dauer (Tage)" → `10` ein
3. Nutzer lässt das Feld "Gießintervall (Tage)" leer
4. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis:**
- Phase wird ohne Fehler angelegt
- In der Phasenliste zeigt die Spalte "Gießintervall (Tage)" den Wert `—` (kein Wert gesetzt)

**Tags**: [req-003, growth-phase, gießintervall, optional, null, happy-path]

---

## Gruppe K: Ressourcenprofil-Anzeige auf der Pflanzinstanz-Detailseite

---

## TC-003-042: Aktuelle Phasen-Ressourcen auf Pflanzinstanz-Detailseite sichtbar

**Anforderung**: REQ-003 §6 DoD "Ressourcen-Profile"; PlantInstanceDetailPage Tab "Phasen"
**Priorität**: High
**Kategorie**: Detailansicht

**Vorbedingungen:**
- Pflanzinstanz befindet sich in Phase "vegetative" mit zugewiesenem Ressourcenprofil (PPFD, Photoperiode, VPD-Zielwert) und Nährstoffprofil (NPK, EC, pH)

**Testschritte:**
1. Nutzer navigiert zur Pflanzinstanz-Detailseite → Tab "Phasen"

**Erwartetes Ergebnis:**
- Die Seite zeigt die aktuelle Phase mit ihrem Anzeigenamen (z.B. "Vegetatives Wachstum")
- Ressourcen-Informationen der aktuellen Phase sind sichtbar (mindestens: aktuelle Phase, Tage in Phase, typische Dauer)
- Wenn ein Ressourcenprofil vorhanden ist, werden Werte für PPFD und VPD-Zielwert angezeigt
- Wenn ein Nährstoffprofil vorhanden ist, werden NPK-Verhältnis und EC-Zielwert angezeigt

**Tags**: [req-003, plant-detail, ressourcenprofil, aktuelle-phase, detailansicht]

---

## Abdeckungsmatrix

| Spezifikationsabschnitt | Testfälle |
|---|---|
| §1 Business Case — LifecycleConfig (annual/biennial/perennial) | TC-003-001, TC-003-002, TC-003-004 |
| §1 Business Case — Autoflower Cultivar | TC-003-034, TC-003-035 |
| §1 Business Case — Dauerkulturen / Perennial | TC-003-036, TC-003-037, TC-003-038 |
| §2 ArangoDB — `growth_phases` CRUD | TC-003-005 bis TC-003-013 |
| §2 ArangoDB — `requirement_profiles` / `nutrient_profiles` | TC-003-014 bis TC-003-018 |
| §2 ArangoDB — `phase_histories` | TC-003-024, TC-003-026 |
| §2 ArangoDB — `seasonal_cycles` (Perennial) | TC-003-036, TC-003-037, TC-003-038 |
| §3 Python — PhaseTransitionEngine (manual, force, rückwärts) | TC-003-019 bis TC-003-023 |
| §3 Python — VPDCalculator | TC-003-027, TC-003-028 |
| §3 Python — GDD Calculator | TC-003-029 |
| §3 Python — PhotoperiodManager | TC-003-030 |
| §3 Python — ResourceProfileGenerator (generate defaults) | TC-003-014 |
| §3 Python — AutoflowerTrainingGuard | TC-003-035 |
| §3 Python — PerennialCycleEngine | TC-003-036, TC-003-037, TC-003-038 |
| §3 Python — Datenvalidierung Grenzwerte (EC, pH, Temperatur) | TC-003-016, TC-003-017, TC-003-018, TC-003-031 |
| §6 DoD — UnsavedChangesGuard | TC-003-003 |
| §6 DoD — Rückwärts-Transition-Sperre | TC-003-021, TC-003-022 |
| §6 DoD — Phase-History vollständig | TC-003-024, TC-003-026 |
| §6 DoD — Listenansicht Phasenspalte | TC-003-032 |
| §6 DoD — Gießintervall (watering_interval_days) | TC-003-039, TC-003-040, TC-003-041 |
| §6 DoD — Ressourcen-Profile auf Pflanzinstanz | TC-003-042 |
| §6 DoD — Pflanzinstanz-Erstellung mit Spezies | TC-003-033 |
| §6 Testszenario 2 — VPD außerhalb Zielbereich | TC-003-027, TC-003-028 |
| §6 Testszenario 4 — Gradueller Photoperioden-Wechsel | TC-003-030 |
| §6 Testszenario 5/6/7 — Perennial Apfelbaum | TC-003-036, TC-003-037, TC-003-038 |
| §6 Testszenario 3a/3b/3c — Autoflower | TC-003-034, TC-003-035 |
