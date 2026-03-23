---
req_id: REQ-019
title: Substrat-Konfiguration und Lebenszyklusverwaltung
category: Infrastruktur
test_count: 38
coverage_areas:
  - Substrat-Listenansicht (SubstrateListPage)
  - Substrat-Erstellen-Dialog (SubstrateCreateDialog)
  - Substrat-Detailseite mit Bearbeitungsformular (SubstrateDetailPage)
  - Substrat-Mischungs-Dialog (SubstrateMixDialog)
  - Charge-Erstellen-Dialog (BatchCreateDialog)
  - Charge-Detailseite (BatchDetailPage)
  - Wiederverwendbarkeits-Prüfung (Reusability Check)
  - Favoriten-Funktion
  - Authentifizierung und Zugriffskontrolle
generated: 2026-03-21
version: "4.1"
---

# Testfälle: REQ-019 — Substratverwaltung

**Routen:**
- Substrat-Liste: `/t/{tenant_slug}/standorte/substrates`
- Substrat-Detail: `/t/{tenant_slug}/standorte/substrates/{key}`
- Charge-Detail: `/t/{tenant_slug}/standorte/substrates/batches/{key}`

**Domänenbegriffe:** Substrat, Substratcharge (Batch), pH, EC, Luftporosität, Pufferkapazität, Wasserhaltevermögen, Wiederverwendbarkeit, Substratmischung, Bewässerungsstrategie, Zusammensetzung (Composition)

---

## Gruppe 1: Substrat-Listenansicht

---

## TC-019-001: Substrat-Liste wird korrekt geladen und angezeigt

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD, Listenansicht-Filter
**Priorität**: Kritisch
**Kategorie**: Listenansicht / Happy Path
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied im aktiven Tenant
- Mindestens zwei Substrate unterschiedlichen Typs sind im System angelegt (z. B. "Bio-Erde" vom Typ "Erde" und "Rohfaser Kokos" vom Typ "Kokos")

**Testschritte**:
1. Nutzer navigiert zu `/t/{slug}/standorte/substrates`
2. Nutzer wartet, bis der Ladeindikator verschwindet

**Erwartetes Ergebnis**:
- Seitentitel "Substrate" ist sichtbar
- Tabelle zeigt Spalten: Typ, Bezeichnung, pH-Basis, EC-Basis (mS/cm), Wiederverwendbar
- Jede Zeile zeigt den übersetzten Substrattyp (z. B. "Erde", "Kokos") aus `enums.substrateType.*`
- Die Wiederverwendbar-Spalte zeigt einen grünen Chip "Ja" oder einen grauen Chip "Nein"
- Mischungs-Einträge zeigen zusätzlich einen blauen Chip "Mischung" neben dem Typ
- Schaltflächen "Substrat erstellen" und "Mischung erstellen" sind in der oberen rechten Ecke sichtbar
- Stern-Icon in der ersten Spalte ist für jeden Eintrag sichtbar (leer = noch kein Favorit)

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substrat-liste, listenansicht, happy-path, tabelle]

---

## TC-019-002: Substrat-Liste — Leerzustand bei keinen vorhandenen Einträgen

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD
**Priorität**: Mittel
**Kategorie**: Leerzustand
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied im aktiven Tenant
- Kein Substrat ist im aktuellen Tenant angelegt

**Testschritte**:
1. Nutzer navigiert zu `/t/{slug}/standorte/substrates`

**Erwartetes Ergebnis**:
- Tabelle zeigt einen Leerzustand mit einer Illustration
- Schaltfläche "Substrat erstellen" ist im Leerzustand-Bereich klickbar
- Die Schaltflächen "Substrat erstellen" und "Mischung erstellen" im Header sind weiterhin sichtbar

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-liste, leerzustand]

---

## TC-019-003: Substrat-Liste — Suche filtert Einträge in Echtzeit

**Anforderung**: REQ-019 §6 DoD (Listenansicht-Filter)
**Priorität**: Hoch
**Kategorie**: Listenansicht / Suche
**Vorbedingungen**:
- Nutzer ist authentifiziert
- Mindestens drei Substrate sind angelegt: "Bio-Erde Premium" (Erde), "Rohfaser Kokos" (Kokos), "Steinwollmatte 100x15cm" (Steinwollmatte)

**Testschritte**:
1. Nutzer navigiert zu `/t/{slug}/standorte/substrates`
2. Nutzer gibt "Kokos" in das Suchfeld "Tabelle durchsuchen..." ein
3. Nutzer wartet ca. 300 ms (debounce)

**Erwartetes Ergebnis**:
- Nur Zeile(n) mit "Kokos" im Typ oder in der Bezeichnung sind sichtbar
- Einträge "Bio-Erde Premium" und "Steinwollmatte 100x15cm" sind ausgeblendet

**Testschritte (Folge)**:
4. Nutzer löscht den Suchbegriff vollständig

**Erwartetes Ergebnis**:
- Alle drei Einträge erscheinen wieder in der Tabelle

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substrat-liste, suche, filter, debounce]

---

## TC-019-004: Substrat-Liste — Suche ohne Treffer zeigt Hinweismeldung

**Anforderung**: REQ-019 §6 DoD (Listenansicht-Filter)
**Priorität**: Mittel
**Kategorie**: Fehlermeldung / Listenansicht
**Vorbedingungen**:
- Nutzer ist authentifiziert
- Mindestens ein Substrat ist angelegt

**Testschritte**:
1. Nutzer navigiert zu `/t/{slug}/standorte/substrates`
2. Nutzer gibt "xyzxyz_nicht_vorhanden" in das Suchfeld ein
3. Nutzer wartet ca. 300 ms (debounce)

**Erwartetes Ergebnis**:
- Tabelle zeigt die Meldung "Keine Ergebnisse für Ihre Suche gefunden"

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substrat-liste, suche, leerzustand]

---

## TC-019-005: Substrat-Liste — Navigation zur Detailseite per Zeilen-Klick

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD
**Priorität**: Hoch
**Kategorie**: Navigation
**Vorbedingungen**:
- Nutzer ist authentifiziert
- Mindestens ein Substrat "Bio-Erde Premium" ist angelegt

**Testschritte**:
1. Nutzer navigiert zu `/t/{slug}/standorte/substrates`
2. Nutzer klickt auf die Zeile mit dem Substrat "Bio-Erde Premium"

**Erwartetes Ergebnis**:
- Browser navigiert zur URL `/t/{slug}/standorte/substrates/{key}`
- Die Substrat-Detailseite wird geladen und zeigt den Titel "Bio-Erde Premium"

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substrat-liste, navigation, detail]

---

## TC-019-006: Substrat-Liste — Favorit setzen und Favoriten-Filter aktivieren

**Anforderung**: REQ-019 §6 DoD
**Priorität**: Mittel
**Kategorie**: Zustandswechsel / Listenansicht
**Vorbedingungen**:
- Nutzer ist authentifiziert
- Mindestens zwei Substrate sind angelegt: "Bio-Erde" und "Rohfaser Kokos"

**Testschritte**:
1. Nutzer navigiert zu `/t/{slug}/standorte/substrates`
2. Nutzer klickt das leere Stern-Icon (StarBorderIcon) in der Zeile "Rohfaser Kokos"

**Erwartetes Ergebnis**:
- Das Stern-Icon der Zeile "Rohfaser Kokos" wechselt zu einem gefüllten goldenen Stern (StarIcon)
- Der Favoriten-Filter-Button (FilterListIcon) erscheint in der Header-Toolbar

**Testschritte (Folge)**:
3. Nutzer klickt den Favoriten-Filter-Button

**Erwartetes Ergebnis**:
- Nur die Zeile "Rohfaser Kokos" ist sichtbar
- Der Filter-Button ist in der aktiven Farbe ("warning") hervorgehoben

**Testschritte (Folge)**:
4. Nutzer klickt erneut den Favoriten-Filter-Button

**Erwartetes Ergebnis**:
- Beide Substrate sind wieder sichtbar
- Der Filter-Button hat wieder die neutrale Farbe

**Nachbedingungen**:
- "Rohfaser Kokos" ist als lokaler Favorit gespeichert (localStorage)

**Tags**: [req-019, substrat-liste, favoriten, filter, localStorage]

---

## Gruppe 2: Substrat erstellen

---

## TC-019-007: Substrat erstellen — Happy Path mit Pflichtfeldern

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD (Anlegen)
**Priorität**: Kritisch
**Kategorie**: Happy Path / Dialog
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied (Rolle: Mitglied oder Admin) im aktiven Tenant
- Substrat-Listenansicht ist geöffnet

**Testschritte**:
1. Nutzer klickt die Schaltfläche "Substrat erstellen" oben rechts
2. Der Dialog "Substrat erstellen" öffnet sich
3. Nutzer wählt im Dropdown "Typ" den Wert "Kokos" (`coco`)
4. Nutzer gibt im Feld "Marke" den Text "Plagron" ein
5. Nutzer gibt im Feld "Bezeichnung (DE)" den Text "Rohfaser Kokos 50L" ein
6. Nutzer gibt im Feld "Bezeichnung (EN)" den Text "Coco Coir 50L" ein
7. Nutzer setzt "pH-Basis" auf `5.8`
8. Nutzer setzt "EC-Basis (mS/cm)" auf `0.3`
9. Nutzer wählt im Dropdown "Wasserhaltevermögen" den Wert "Mittel"
10. Nutzer setzt "Luftporosität (%)" auf `35`
11. Nutzer wählt im Dropdown "Pufferkapazität" den Wert "Niedrig"
12. Nutzer aktiviert den Schalter "Wiederverwendbar"
13. Nutzer setzt "Max. Wiederverwendungszyklen" auf `3`
14. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Der Dialog schließt sich
- Eine Erfolgsbenachrichtigung erscheint
- Die Substrat-Liste wird neu geladen und enthält den neuen Eintrag "Rohfaser Kokos 50L" vom Typ "Kokos"
- Die Zeile zeigt einen grünen Chip "Ja" in der Wiederverwendbar-Spalte

**Nachbedingungen**:
- Substrat "Rohfaser Kokos 50L" ist im System gespeichert

**Tags**: [req-019, substrat-erstellen, happy-path, dialog, coco]

---

## TC-019-008: Substrat erstellen — Typ "Kein Substrat" (none) für DWC/NFT

**Anforderung**: REQ-019 §2 (Substrattyp `none` für DWC, Kratky, NFT)
**Priorität**: Hoch
**Kategorie**: Happy Path / Dialog
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied im aktiven Tenant
- Substrat-Listenansicht ist geöffnet

**Testschritte**:
1. Nutzer klickt "Substrat erstellen"
2. Nutzer wählt im Dropdown "Typ" den Wert "Kein Substrat" (`none`)
3. Nutzer gibt in "Bezeichnung (DE)" "DWC-System" ein
4. Alle übrigen Felder bleiben auf Standardwerten
5. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Der Dialog schließt sich
- Eine Erfolgsbenachrichtigung erscheint
- Eintrag "DWC-System" vom Typ "Kein Substrat" erscheint in der Liste

**Nachbedingungen**:
- Substrat "DWC-System" vom Typ "Kein Substrat" ist gespeichert

**Tags**: [req-019, substrat-erstellen, none, DWC, happy-path]

---

## TC-019-009: Substrat erstellen — Alle 14 Substrattypen sind im Dropdown verfügbar

**Anforderung**: REQ-019 §3 SubstrateType-Enum (14 Werte)
**Priorität**: Hoch
**Kategorie**: Listenansicht / Dialog
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied im aktiven Tenant

**Testschritte**:
1. Nutzer klickt "Substrat erstellen"
2. Nutzer öffnet das Dropdown-Feld "Typ"

**Erwartetes Ergebnis**:
Das Dropdown enthält exakt diese 14 Optionen in der deutschen Übersetzung:
- Erde (`soil`)
- Kokos (`coco`)
- Blähton (`clay_pebbles`)
- Perlit (`perlite`)
- Lebende Erde (`living_soil`)
- Torf (`peat`)
- Steinwollmatte (`rockwool_slab`)
- Steinwollwürfel (`rockwool_plug`)
- Vermiculit (`vermiculite`)
- Kein Substrat (`none`)
- Orchideenrinde (`orchid_bark`)
- PON-Mineralsubstrat (`pon_mineral`)
- Sphagnum-Moos (`sphagnum`)
- Hydrolösung (`hydro_solution`)

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-erstellen, dropdown, substrattyp, enum]

---

## TC-019-010: Substrat erstellen — Validierungsfehler bei pH außerhalb 0–14

**Anforderung**: REQ-019 §3 SubstrateValidator (Zod: ph_base min=0, max=14)
**Priorität**: Hoch
**Kategorie**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied im aktiven Tenant
- Dialog "Substrat erstellen" ist geöffnet

**Testschritte**:
1. Nutzer öffnet den Dialog "Substrat erstellen"
2. Nutzer löscht den Wert im Feld "pH-Basis" und gibt `15` ein
3. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Das Formular wird nicht abgesendet
- Das Feld "pH-Basis" zeigt eine Validierungsfehlermeldung unterhalb des Feldes
- Der Dialog bleibt geöffnet

**Testschritte (Grenzwert — gültig)**:
4. Nutzer ändert "pH-Basis" auf `0`
5. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Formular wird abgesendet (kein Fehler am pH-Feld)

**Nachbedingungen**:
- Nur der gültige Eintrag (Schritt 4–5) wird gespeichert

**Tags**: [req-019, substrat-erstellen, formvalidierung, ph-basis, grenzwert]

---

## TC-019-011: Substrat erstellen — Validierungsfehler bei EC-Basis < 0

**Anforderung**: REQ-019 §3 SubstrateValidator (Zod: ec_base_ms min=0)
**Priorität**: Mittel
**Kategorie**: Formvalidierung
**Vorbedingungen**:
- Dialog "Substrat erstellen" ist geöffnet

**Testschritte**:
1. Nutzer löscht den Wert im Feld "EC-Basis (mS/cm)" und gibt `-0.1` ein
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Das Formular wird nicht abgesendet
- Das Feld "EC-Basis (mS/cm)" zeigt eine Validierungsfehlermeldung

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-erstellen, formvalidierung, ec-basis, grenzwert]

---

## TC-019-012: Substrat erstellen — Validierungsfehler bei Luftporosität außerhalb 0–100

**Anforderung**: REQ-019 §3 SubstrateValidator (Zod: air_porosity_percent min=0, max=100)
**Priorität**: Mittel
**Kategorie**: Formvalidierung
**Vorbedingungen**:
- Dialog "Substrat erstellen" ist geöffnet

**Testschritte**:
1. Nutzer löscht "Luftporosität (%)" und gibt `101` ein
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Das Formular wird nicht abgesendet
- Das Feld "Luftporosität (%)" zeigt eine Validierungsfehlermeldung

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-erstellen, formvalidierung, luftporositaet, grenzwert]

---

## TC-019-013: Substrat erstellen — Validierungsfehler bei Max. Wiederverwendungszyklen < 1

**Anforderung**: REQ-019 §3 SubstrateValidator (Zod: max_reuse_cycles min=1)
**Priorität**: Mittel
**Kategorie**: Formvalidierung
**Vorbedingungen**:
- Dialog "Substrat erstellen" ist geöffnet

**Testschritte**:
1. Nutzer löscht "Max. Wiederverwendungszyklen" und gibt `0` ein
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Das Formular wird nicht abgesendet
- Das Feld "Max. Wiederverwendungszyklen" zeigt eine Validierungsfehlermeldung

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-erstellen, formvalidierung, wiederverwendungszyklen, grenzwert]

---

## TC-019-014: Substrat erstellen — Dialog-Abbrechen verwirft Eingaben

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD
**Priorität**: Mittel
**Kategorie**: Dialog / Navigation
**Vorbedingungen**:
- Dialog "Substrat erstellen" ist geöffnet
- Nutzer hat Felder ausgefüllt (z. B. "Bezeichnung (DE)" = "Testsubstrat")

**Testschritte**:
1. Nutzer klickt die Schaltfläche "Abbrechen"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Die Substrat-Liste zeigt kein neues "Testsubstrat"
- Keine Fehler- oder Erfolgsmeldung erscheint

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substrat-erstellen, dialog, abbrechen]

---

## Gruppe 3: Substrat-Detailseite (Bearbeiten)

---

## TC-019-015: Substrat-Detailseite — Formular zeigt korrekte Werte aus der Liste

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD (Lesen)
**Priorität**: Kritisch
**Kategorie**: Detailansicht / Happy Path
**Vorbedingungen**:
- Substrat "Rohfaser Kokos 50L" (Typ: Kokos, pH: 5.8, EC: 0.3, WH: Mittel, LP: 35%, PK: Niedrig, WV: Ja, MWZ: 3) ist angelegt
- Nutzer ist auf der Substrat-Listenansicht

**Testschritte**:
1. Nutzer klickt auf die Zeile "Rohfaser Kokos 50L"

**Erwartetes Ergebnis**:
- Detailseite lädt und zeigt Seitentitel "Rohfaser Kokos 50L"
- Seite ist in vier Karten gegliedert: "Identifikation", "Chemische Eigenschaften", "Physikalische Eigenschaften", "Wiederverwendung"
- Karte "Identifikation": Dropdown "Typ" zeigt "Kokos", Feld "Marke" zeigt "Plagron", Feld "Bezeichnung (DE)" zeigt "Rohfaser Kokos 50L"
- Karte "Chemische Eigenschaften": "pH-Basis" zeigt `5.8`, "EC-Basis (mS/cm)" zeigt `0.30`
- Karte "Physikalische Eigenschaften": "Wasserhaltevermögen" zeigt "Mittel", "Luftporosität (%)" zeigt `35`, "Pufferkapazität" zeigt "Niedrig"
- Karte "Wiederverwendung": Schalter "Wiederverwendbar" ist aktiviert, "Max. Wiederverwendungszyklen" zeigt `3`
- Schaltfläche "Löschen" (rot) ist oben rechts sichtbar
- Abschnitt "Chargen" mit einer Tabelle und Schaltfläche "Charge erstellen" ist unterhalb der Formular-Karten sichtbar

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-detail, detailansicht, happy-path, formular]

---

## TC-019-016: Substrat-Detailseite — Eigenschaften erfolgreich bearbeiten und speichern

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD (Aktualisieren)
**Priorität**: Kritisch
**Kategorie**: Happy Path / Formular
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von "Rohfaser Kokos 50L"
- Formular ist nicht dirty (keine ungespeicherten Änderungen)

**Testschritte**:
1. Nutzer ändert im Feld "pH-Basis" den Wert von `5.8` auf `6.0`
2. Nutzer ändert das Dropdown "Wasserhaltevermögen" von "Mittel" auf "Hoch"
3. Nutzer klickt die Schaltfläche "Speichern"

**Erwartetes Ergebnis**:
- Eine Erfolgsbenachrichtigung erscheint
- Nach dem Speichern zeigt das Feld "pH-Basis" den Wert `6.0`
- Das Feld "Wasserhaltevermögen" zeigt "Hoch"
- Das Formular ist nicht mehr dirty (kein ungespeicherter Zustand)

**Nachbedingungen**:
- Substrat hat pH-Basis `6.0` und Wasserhaltevermögen "Hoch"

**Tags**: [req-019, substrat-detail, bearbeiten, speichern, happy-path]

---

## TC-019-017: Substrat-Detailseite — UnsavedChangesGuard warnt bei Navigation mit dirty Form

**Anforderung**: REQ-019 §6 DoD (UnsavedChangesGuard — Frontend-Architekturmuster)
**Priorität**: Hoch
**Kategorie**: Navigation / Dialog
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von "Rohfaser Kokos 50L"
- Formular wurde verändert (z. B. pH-Basis geändert), aber noch nicht gespeichert

**Testschritte**:
1. Nutzer ändert das Feld "pH-Basis" auf einen anderen Wert (Formular ist jetzt dirty)
2. Nutzer klickt die Schaltfläche "Abbrechen" (oder navigiert im Browser zurück)

**Erwartetes Ergebnis**:
- Ein Browser-Bestätigungsdialog erscheint mit der Meldung "Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Wenn Nutzer "Verlassen" bestätigt: Navigation erfolgt, Änderungen werden verworfen
- Wenn Nutzer "Bleiben" wählt: Nutzer verbleibt auf der Detailseite, Formular bleibt dirty

**Nachbedingungen**:
- Wenn verlassen: Substrat hat den alten pH-Wert

**Tags**: [req-019, substrat-detail, unsaved-changes-guard, navigation, dialog]

---

## TC-019-018: Substrat-Detailseite — Substrat löschen mit Bestätigungsdialog

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD (Löschen)
**Priorität**: Kritisch
**Kategorie**: Zustandswechsel / Dialog
**Vorbedingungen**:
- Nutzer ist authentifiziert mit Rolle Admin im Tenant
- Substrat "Rohfaser Kokos 50L" existiert und hat keine verknüpften Chargen

**Testschritte**:
1. Nutzer öffnet die Detailseite von "Rohfaser Kokos 50L"
2. Nutzer klickt die rote Schaltfläche "Löschen"

**Erwartetes Ergebnis**:
- Bestätigungsdialog erscheint: "Sind Sie sicher, dass Sie 'Rohfaser Kokos 50L' löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
- Dialog hat zwei Schaltflächen: "Abbrechen" und eine rote "Löschen"-Schaltfläche

**Testschritte (Folge — Löschen bestätigen)**:
3. Nutzer klickt die rote "Löschen"-Schaltfläche im Dialog

**Erwartetes Ergebnis**:
- Eine Erfolgsbenachrichtigung erscheint
- Browser navigiert zurück zur Substrat-Liste `/t/{slug}/standorte/substrates`
- Eintrag "Rohfaser Kokos 50L" ist nicht mehr in der Liste

**Nachbedingungen**:
- Substrat ist aus dem System gelöscht

**Tags**: [req-019, substrat-detail, loeschen, bestaetigungsdialog, zustandswechsel]

---

## TC-019-019: Substrat-Detailseite — Löschen-Bestätigungsdialog abbrechen

**Anforderung**: REQ-019 §6 DoD — Substrat-CRUD (Löschen, negativ)
**Priorität**: Mittel
**Kategorie**: Dialog / Formvalidierung
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von "Rohfaser Kokos 50L"
- Bestätigungsdialog ist geöffnet (nach Klick auf "Löschen")

**Testschritte**:
1. Nutzer klickt "Abbrechen" im Bestätigungsdialog

**Erwartetes Ergebnis**:
- Bestätigungsdialog schließt sich
- Nutzer verbleibt auf der Detailseite von "Rohfaser Kokos 50L"
- Substrat ist weiterhin im System vorhanden

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-detail, loeschen, abbrechen, dialog]

---

## TC-019-020: Substrat-Detailseite — Favorit-Toggle auf Detailseite

**Anforderung**: REQ-019 §6 DoD
**Priorität**: Niedrig
**Kategorie**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von "Rohfaser Kokos 50L"
- Substrat ist noch kein Favorit (leerer Stern sichtbar)

**Testschritte**:
1. Nutzer klickt den Stern-Button neben dem Seitentitel

**Erwartetes Ergebnis**:
- Der Stern wechselt von leer (StarBorderIcon) zu gefüllt/golden (StarIcon)

**Testschritte (Folge)**:
2. Nutzer navigiert zur Substrat-Liste

**Erwartetes Ergebnis**:
- In der Liste zeigt die Zeile "Rohfaser Kokos 50L" ebenfalls einen goldenen Stern

**Nachbedingungen**:
- "Rohfaser Kokos 50L" ist als lokaler Favorit gespeichert

**Tags**: [req-019, substrat-detail, favorit, localStorage, zustandswechsel]

---

## Gruppe 4: Substratmischung erstellen (SubstrateMixDialog)

---

## TC-019-021: Substratmischung erstellen — Happy Path (zwei Komponenten, 50/50)

**Anforderung**: REQ-019 §6 DoD — Composition-Validierung
**Priorität**: Hoch
**Kategorie**: Happy Path / Dialog
**Vorbedingungen**:
- Nutzer ist authentifiziert und Mitglied im aktiven Tenant
- Substrate "Bio-Erde" (Typ: Erde) und "Perlit fein" (Typ: Perlit) sind im System angelegt und sind keine Mischungen
- Substrat-Listenansicht ist geöffnet

**Testschritte**:
1. Nutzer klickt "Mischung erstellen" (Button mit Mixer-Icon)
2. Der Dialog "Mischung erstellen" öffnet sich mit zwei vorausgefüllten Zeilen
3. Nutzer gibt "Bezeichnung (DE)" = "Erde-Perlit-Mix 70/30" ein
4. Nutzer gibt "Bezeichnung (EN)" = "Soil Perlite Mix 70/30" ein
5. In Zeile 1: Nutzer wählt "Bio-Erde" aus dem Dropdown
6. Nutzer zieht den Schieberegler auf `70%`
7. In Zeile 2: Nutzer wählt "Perlit fein" aus dem Dropdown
8. Nutzer zieht den Schieberegler auf `30%`

**Erwartetes Ergebnis**:
- Der Gesamtanteil-Chip zeigt "100%" in grüner Farbe
- Die Fehlermeldung "Anteile müssen 100 % ergeben" ist nicht sichtbar

**Testschritte (Folge)**:
9. Nutzer klickt "Vorschau berechnen"

**Erwartetes Ergebnis**:
- Abschnitt "Berechnete Eigenschaften" erscheint unterhalb
- Zeigt berechneten Typ, pH-Basis, EC-Basis (mS/cm), Wasserhaltevermögen, Luftporosität, Pufferkapazität, Wiederverwendbar, Bewässerungsstrategie
- Zusammensetzungs-Chips zeigen "peat: X%", "compost: Y%", "perlite: Z%" o.ä.

**Testschritte (Folge)**:
10. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- Substrat-Liste enthält neuen Eintrag "Erde-Perlit-Mix 70/30" mit blauem Chip "Mischung"

**Nachbedingungen**:
- Mischungs-Substrat "Erde-Perlit-Mix 70/30" ist gespeichert

**Tags**: [req-019, substratmischung, erstellen, happy-path, dialog, composition]

---

## TC-019-022: Substratmischung — Gesamtanteil ungleich 100% blockiert Erstellen-Button

**Anforderung**: REQ-019 §3 SubstrateValidator (composition muss 1.0 ergeben)
**Priorität**: Hoch
**Kategorie**: Formvalidierung / Dialog
**Vorbedingungen**:
- Dialog "Mischung erstellen" ist geöffnet
- Zeile 1: Substrat ausgewählt, Anteil 60%
- Zeile 2: Substrat ausgewählt, Anteil 60%

**Testschritte**:
1. Nutzer betrachtet die Anzeige des Gesamtanteils

**Erwartetes Ergebnis**:
- Gesamtanteil-Chip zeigt "120%" in roter Farbe
- Fehlermeldung "Anteile müssen 100 % ergeben" ist sichtbar
- Schaltfläche "Erstellen" ist deaktiviert (disabled)
- Schaltfläche "Vorschau berechnen" ist deaktiviert (disabled)

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substratmischung, formvalidierung, composition-summe, blockiert]

---

## TC-019-023: Substratmischung — Gleiche Komponente doppelt wählen zeigt Fehler

**Anforderung**: REQ-019 §3 SubstrateValidator (keine Duplikate in Composition)
**Priorität**: Mittel
**Kategorie**: Formvalidierung / Dialog
**Vorbedingungen**:
- Dialog "Mischung erstellen" ist geöffnet mit zwei Zeilen

**Testschritte**:
1. Nutzer wählt in Zeile 1 "Bio-Erde"
2. Nutzer stellt Zeile 1 auf 50%
3. Nutzer wählt in Zeile 2 ebenfalls "Bio-Erde"
4. Nutzer stellt Zeile 2 auf 50%

**Erwartetes Ergebnis**:
- Fehlermeldung "Keine doppelten Komponenten erlaubt" erscheint
- Schaltfläche "Erstellen" ist deaktiviert
- In Zeile 2 ist "Bio-Erde" im Dropdown als bereits gewählte Option deaktiviert (grau, nicht auswählbar)

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substratmischung, formvalidierung, duplikate]

---

## TC-019-024: Substratmischung — Gleichmäßig verteilen (3 Komponenten)

**Anforderung**: REQ-019 §6 DoD — Composition-Validierung
**Priorität**: Mittel
**Kategorie**: Happy Path / Dialog
**Vorbedingungen**:
- Dialog "Mischung erstellen" ist geöffnet mit 2 Zeilen, beide haben ungleiche Anteile

**Testschritte**:
1. Nutzer klickt "+ Komponente hinzufügen"

**Erwartetes Ergebnis**:
- Eine dritte Zeile mit leerem Dropdown und Anteil 0% wird hinzugefügt

**Testschritte (Folge)**:
2. Nutzer klickt "Gleichmäßig verteilen"

**Erwartetes Ergebnis**:
- Alle drei Zeilen zeigen einen Anteil von ca. 33%
- Gesamtanteil-Chip zeigt "100%" in grüner Farbe (letzte Zeile ausgleichend auf 34% falls nötig)

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substratmischung, gleichmaessig-verteilen, dialog]

---

## TC-019-025: Substratmischung — Dritte Zeile entfernen, mindestens 2 bleiben erhalten

**Anforderung**: REQ-019 §6 DoD — Composition-Validierung (min. 2 Komponenten)
**Priorität**: Mittel
**Kategorie**: Dialog / Grenzwert
**Vorbedingungen**:
- Dialog "Mischung erstellen" ist geöffnet mit genau zwei Zeilen

**Testschritte**:
1. Nutzer versucht den Löschen-Button (DeleteIcon) in Zeile 1 zu klicken

**Erwartetes Ergebnis**:
- Der Löschen-Button ist deaktiviert (disabled), weil mindestens 2 Zeilen vorhanden sein müssen

**Testschritte (Folge)**:
2. Nutzer klickt "+ Komponente hinzufügen" (jetzt 3 Zeilen)
3. Nutzer klickt den Löschen-Button in Zeile 3

**Erwartetes Ergebnis**:
- Zeile 3 wird entfernt
- Nur noch 2 Zeilen sind sichtbar
- Vorschau wird zurückgesetzt (kein Vorschau-Ergebnis sichtbar)

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, substratmischung, zeile-entfernen, grenzwert, min-komponenten]

---

## TC-019-026: Substratmischung — Mischungen erscheinen nicht als auswählbare Komponenten

**Anforderung**: REQ-019 §3 SubstrateMixDialog (keine geschachtelten Mischungen)
**Priorität**: Mittel
**Kategorie**: Formvalidierung / Dialog
**Vorbedingungen**:
- Nutzer ist authentifiziert
- Substrat "Erde-Perlit-Mix" (is_mix=true) und "Bio-Erde" (is_mix=false) sind vorhanden

**Testschritte**:
1. Nutzer öffnet Dialog "Mischung erstellen"
2. Nutzer öffnet das Dropdown in Zeile 1

**Erwartetes Ergebnis**:
- "Bio-Erde" erscheint als auswählbare Option
- "Erde-Perlit-Mix" (eine bereits bestehende Mischung) erscheint **nicht** in der Dropdown-Liste

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substratmischung, keine-geschachtelten-mischungen, dropdown]

---

## TC-019-027: Substrat-Detailseite — Mischungskomponenten werden als Chips angezeigt

**Anforderung**: REQ-019 §6 DoD — Composition-Validierung, Substrat-CRUD (Lesen)
**Priorität**: Mittel
**Kategorie**: Detailansicht
**Vorbedingungen**:
- Substrat "Erde-Perlit-Mix 70/30" (Mischung aus Bio-Erde 70% + Perlit fein 30%) existiert

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Erde-Perlit-Mix 70/30"

**Erwartetes Ergebnis**:
- Oberhalb des Bearbeitungsformulars erscheint ein Bereich "Mischungskomponenten"
- Zwei blaue outline Chips sind sichtbar: "Bio-Erde: 70%" und "Perlit fein: 30%"
- Das Hauptformular zeigt die berechneten Eigenschaften der Mischung

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, substrat-detail, mischungskomponenten, chips, detailansicht]

---

## Gruppe 5: Charge (Batch) anlegen und verwalten

---

## TC-019-028: Charge erstellen — Happy Path

**Anforderung**: REQ-019 §6 DoD — Batch-Tracking
**Priorität**: Kritisch
**Kategorie**: Happy Path / Dialog
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von Substrat "Rohfaser Kokos 50L"
- Substrat hat noch keine Chargen

**Testschritte**:
1. Nutzer klickt "Charge erstellen" im Abschnitt "Chargen"
2. Der Dialog "Charge erstellen" öffnet sich
3. Das Feld "Chargen-ID" enthält eine automatisch generierte ID (z. B. "COCO-2026-001")
4. Nutzer überschreibt "Chargen-ID" mit "COCO-2026-001"
5. Nutzer setzt "Volumen (L)" auf `50`
6. Nutzer setzt "Gemischt am" auf das heutige Datum
7. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Dialog schließt sich
- Erfolgsbenachrichtigung erscheint
- Tabelle "Chargen" enthält jetzt eine Zeile mit Chargen-ID "COCO-2026-001", Volumen "50 L", heutigem Datum und "0" verwendeten Zyklen

**Nachbedingungen**:
- Charge "COCO-2026-001" ist dem Substrat "Rohfaser Kokos 50L" zugeordnet

**Tags**: [req-019, charge-erstellen, batch-tracking, happy-path, dialog]

---

## TC-019-029: Charge erstellen — Pflichtfeld Chargen-ID leer zeigt Validierungsfehler

**Anforderung**: REQ-019 §6 DoD — Batch-Tracking (Zod: batch_id min=1)
**Priorität**: Hoch
**Kategorie**: Formvalidierung / Dialog
**Vorbedingungen**:
- Dialog "Charge erstellen" ist geöffnet

**Testschritte**:
1. Nutzer löscht den Inhalt des Pflichtfeldes "Chargen-ID" vollständig
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Formular wird nicht abgesendet
- Feld "Chargen-ID" zeigt eine Validierungsfehlermeldung (Pflichtfeld)
- Dialog bleibt geöffnet

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, charge-erstellen, formvalidierung, pflichtfeld, batch-id]

---

## TC-019-030: Charge erstellen — Pflichtfeld Gemischt-am leer zeigt Validierungsfehler

**Anforderung**: REQ-019 §6 DoD — Batch-Tracking (Zod: mixed_on min=1)
**Priorität**: Mittel
**Kategorie**: Formvalidierung / Dialog
**Vorbedingungen**:
- Dialog "Charge erstellen" ist geöffnet

**Testschritte**:
1. Nutzer löscht das Datum im Feld "Gemischt am" vollständig
2. Nutzer klickt "Erstellen"

**Erwartetes Ergebnis**:
- Formular wird nicht abgesendet
- Feld "Gemischt am" zeigt eine Validierungsfehlermeldung (Pflichtfeld)

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, charge-erstellen, formvalidierung, pflichtfeld, datum]

---

## TC-019-031: Charge-Detailseite — Aktuelle Messwerte (pH, EC, Zyklen) werden angezeigt

**Anforderung**: REQ-019 §6 DoD — Batch-Tracking (pH/EC-Verlauf, cycles_used)
**Priorität**: Hoch
**Kategorie**: Detailansicht
**Vorbedingungen**:
- Charge "COCO-2026-001" mit `cycles_used=2`, `ph_current=6.1`, `ec_current_ms=1.8` existiert
- Nutzer ist auf der Detailseite des übergeordneten Substrats

**Testschritte**:
1. Nutzer klickt auf die Zeile "COCO-2026-001" in der Chargen-Tabelle
2. Browser navigiert zu `/t/{slug}/standorte/substrates/batches/{key}`

**Erwartetes Ergebnis**:
- Seitentitel zeigt "COCO-2026-001"
- Infobereich (grau hinterlegt) zeigt:
  - "Verwendete Zyklen": `2`
  - "Aktueller pH": `6.1`
  - "Aktueller EC": `1.8 mS/cm`

**Nachbedingungen**:
- Keine Zustandsänderung

**Tags**: [req-019, charge-detail, batch-tracking, ph-ec-verlauf, messwerte]

---

## TC-019-032: Charge-Detailseite — Charge bearbeiten und speichern

**Anforderung**: REQ-019 §6 DoD — Batch-Tracking (Aktualisieren)
**Priorität**: Hoch
**Kategorie**: Happy Path / Formular
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von Charge "COCO-2026-001"

**Testschritte**:
1. Nutzer ändert das Feld "Volumen (L)" von `50` auf `45`
2. Nutzer klickt "Speichern"

**Erwartetes Ergebnis**:
- Erfolgsbenachrichtigung erscheint
- Feld "Volumen (L)" zeigt `45` nach dem Speichern

**Nachbedingungen**:
- Charge hat Volumen `45 L`

**Tags**: [req-019, charge-detail, bearbeiten, speichern, happy-path]

---

## TC-019-033: Charge löschen — Über Substrat-Detailseite mit Bestätigung

**Anforderung**: REQ-019 §6 DoD — Batch-Tracking (Löschen)
**Priorität**: Hoch
**Kategorie**: Zustandswechsel / Dialog
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von Substrat "Rohfaser Kokos 50L"
- Charge "COCO-2026-001" ist in der Chargen-Tabelle sichtbar

**Testschritte**:
1. Nutzer klickt den Löschen-Button (DeleteIcon) in der Aktionen-Spalte der Zeile "COCO-2026-001"
2. Bestätigungsdialog erscheint: "Sind Sie sicher, dass Sie 'COCO-2026-001' löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
3. Nutzer klickt "Löschen" (roter Button)

**Erwartetes Ergebnis**:
- Erfolgsbenachrichtigung erscheint
- Zeile "COCO-2026-001" ist nicht mehr in der Chargen-Tabelle sichtbar

**Nachbedingungen**:
- Charge "COCO-2026-001" ist gelöscht

**Tags**: [req-019, charge-loeschen, substrat-detail, bestaetigungsdialog, zustandswechsel]

---

## Gruppe 6: Wiederverwendbarkeits-Prüfung

---

## TC-019-034: Wiederverwendbarkeits-Prüfung — Charge kann wiederverwendet werden (Szenario 2b)

**Anforderung**: REQ-019 §6 Szenario 2b (Steinwolle-Slab wiederverwenden), DoD — Substrat-Recycling
**Priorität**: Kritisch
**Kategorie**: Zustandswechsel / Happy Path
**Vorbedingungen**:
- Substrat "Steinwollmatte Grodan" (Typ: Steinwollmatte, reusable=true, max_reuse_cycles=3) existiert
- Charge "SW-2026-001" mit `cycles_used=1`, `ph_current=5.8`, `ec_current_ms=1.2` ist angelegt
- pH-Verlauf und EC-Verlauf zeigen keine Instabilität
- Nutzer ist auf der Detailseite von "Steinwollmatte Grodan"

**Testschritte**:
1. Nutzer klickt "Wiederverwendbarkeit prüfen" in der Aktionen-Spalte der Zeile "SW-2026-001"

**Erwartetes Ergebnis**:
- Erfolgsbenachrichtigung erscheint: "Wiederverwendbarkeit prüfen: OK"
- Unterhalb der Chargen-Tabelle erscheint eine grüne Alert-Box: "Charge SW-2026-001: Wiederverwendbar"

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, wiederverwendbarkeit, pruefung, ok, steinwolle-slab, happy-path, szenario-2b]

---

## TC-019-035: Wiederverwendbarkeits-Prüfung — Einweg-Substrat wird abgelehnt (Szenario 2a)

**Anforderung**: REQ-019 §6 Szenario 2a (Steinwollwürfel ablehnen), §3 SubstrateLifecycleManager.can_reuse()
**Priorität**: Kritisch
**Kategorie**: Fehlermeldung / Zustandswechsel
**Vorbedingungen**:
- Substrat "Steinwollwürfel 36mm" (Typ: Steinwollwürfel `rockwool_plug`) existiert
- Charge "PLUG-2026-001" mit `cycles_used=1` ist angelegt
- Nutzer ist auf der Detailseite des Substrats "Steinwollwürfel 36mm"

**Testschritte**:
1. Nutzer klickt "Wiederverwendbarkeit prüfen" in der Aktionen-Spalte von "PLUG-2026-001"

**Erwartetes Ergebnis**:
- Warnungsbenachrichtigung erscheint: "Wiederverwendbarkeit prüfen: Einweg-Substrat (Anzucht-Plug) nicht wiederverwendbar" (oder entsprechende Behandlungs-Information)
- Unterhalb der Tabelle erscheint eine orangefarbene Alert-Box: "Charge PLUG-2026-001: Behandlung erforderlich — [...]"

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, wiederverwendbarkeit, pruefung, einweg, abgelehnt, steinwollwuerfel, szenario-2a]

---

## TC-019-036: Wiederverwendbarkeits-Prüfung — pH-Instabilität überschreitet Grenzwert (Szenario 3)

**Anforderung**: REQ-019 §6 Szenario 3, §3 SubstrateLifecycleManager.can_reuse() (pH-Standardabweichung)
**Priorität**: Hoch
**Kategorie**: Fehlermeldung / Grenzwert
**Vorbedingungen**:
- Substrat "Kokos mit pH-Instabilität" (Typ: Kokos) existiert
- Charge "COCO-INSTABIL-001" mit pH-Verlauf `[5.8, 4.5, 6.5, 5.2, 7.0]` (σ=0.88, überschreitet max 0.3 für coco) ist angelegt
- Nutzer ist auf der Detailseite des Substrats

**Testschritte**:
1. Nutzer klickt "Wiederverwendbarkeit prüfen" in der Zeile "COCO-INSTABIL-001"

**Erwartetes Ergebnis**:
- Warnungsbenachrichtigung erscheint mit Hinweis auf pH-Instabilität
- Orangefarbene Alert-Box zeigt: "Charge COCO-INSTABIL-001: Behandlung erforderlich — pH-Instabilität zu hoch (σ=0.88, max 0.3 für coco)" oder äquivalente Anzeige der vom Server zurückgemeldeten Behandlungsmaßnahmen

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, wiederverwendbarkeit, ph-instabilitaet, standardabweichung, szenario-3, grenzwert]

---

## TC-019-037: Wiederverwendbarkeits-Prüfung — Mehrere Chargen-Ergebnisse werden kumuliert angezeigt

**Anforderung**: REQ-019 §6 DoD — Substrat-Recycling
**Priorität**: Mittel
**Kategorie**: Detailansicht / Zustandswechsel
**Vorbedingungen**:
- Substrat "Kokos Multi" hat zwei Chargen: "COCO-A" (wiederverwendbar) und "COCO-B" (nicht wiederverwendbar)
- Nutzer ist auf der Detailseite von "Kokos Multi"

**Testschritte**:
1. Nutzer klickt "Wiederverwendbarkeit prüfen" für "COCO-A"
2. Nutzer klickt "Wiederverwendbarkeit prüfen" für "COCO-B"

**Erwartetes Ergebnis**:
- Unterhalb der Chargen-Tabelle erscheinen zwei Alert-Boxen:
  - Grüne Box: "Charge COCO-A: Wiederverwendbar"
  - Orangefarbene Box: "Charge COCO-B: Behandlung erforderlich — [...]"
- Beide Ergebnisse sind gleichzeitig sichtbar (nicht überschrieben)

**Nachbedingungen**:
- Keine Zustandsänderung im System

**Tags**: [req-019, wiederverwendbarkeit, mehrere-chargen, kumuliert, detailansicht]

---

## Gruppe 7: Authentifizierung und Zugriffskontrolle

---

## TC-019-038: Zugriff ohne Authentifizierung — Weiterleitung zum Login

**Anforderung**: REQ-019 §4 (Auth — alle Endpunkte erfordern Authentifizierung)
**Priorität**: Kritisch
**Kategorie**: Authentifizierung / Navigation
**Vorbedingungen**:
- Nutzer ist **nicht** eingeloggt (keine aktive Sitzung)

**Testschritte**:
1. Nutzer navigiert direkt zu `/t/mein-tenant/standorte/substrates`

**Erwartetes Ergebnis**:
- Browser leitet den Nutzer zur Login-Seite weiter
- Die Substrat-Liste ist nicht zugänglich
- Keine Substrat-Daten sind sichtbar

**Nachbedingungen**:
- Nutzer ist auf der Login-Seite

**Tags**: [req-019, authentifizierung, zugriffskontrolle, weiterleitung, security]

---

## Abdeckungsmatrix

| Spec-Abschnitt | Inhalte | Testfall-IDs |
|----------------|---------|--------------|
| §1 Business Case — Substrattypen | Alle 13 Typen inkl. orchid_bark, pon_mineral, sphagnum, none | TC-019-008, TC-019-009 |
| §2 ArangoDB-Modell — Substrate-Node | Properties (ph_base, ec_base_ms, water_retention, air_porosity_percent, buffer_capacity, reusable, max_reuse_cycles) | TC-019-007, TC-019-010 bis TC-019-013 |
| §2 ArangoDB-Modell — SubstrateBatch-Node | batch_id, volume_liters, mixed_on, cycles_used, ph_current, ec_current_ms | TC-019-028 bis TC-019-033 |
| §3 SubstrateLifecycleManager.can_reuse() | Einweg-Ablehnung, pH-σ-Prüfung, EC-Salzakkumulation, Zyklen-Limit | TC-019-034 bis TC-019-037 |
| §3 SubstrateLifecycleManager.prepare_for_reuse() | Aufbereitungsplan mit Behandlungsschritten | TC-019-034, TC-019-035 |
| §3 SubstrateValidator — composition Summe | Muss 1.0 ±0.01 ergeben | TC-019-022 |
| §3 SubstrateValidator — none hat keine Composition | Typ 'none' darf keine physikalischen Properties haben | TC-019-008 |
| §3 IRRIGATION_STRATEGY_MAP | Bewässerungsstrategie im Mix-Preview | TC-019-021 |
| §4 Authentifizierung | Tenant-scoped, JWT-Pflicht | TC-019-038 |
| §6 DoD — Substrat-CRUD | Erstellen, Lesen, Aktualisieren, Löschen | TC-019-007, TC-019-015 bis TC-019-019 |
| §6 DoD — Batch-Tracking | Chargen anlegen, pH/EC verfolgen, löschen | TC-019-028 bis TC-019-033 |
| §6 DoD — Wiederverwendbarkeits-Check | Prüfung auf pH-σ, EC-Anstieg, Zyklen | TC-019-034 bis TC-019-037 |
| §6 DoD — Aufbereitungs-Anleitung | Behandlungsschritte je Substrattyp | TC-019-034, TC-019-035 |
| §6 DoD — Composition-Validierung | Summenprüfung, Duplikate, min. 2 Komponenten | TC-019-021 bis TC-019-026 |
| §6 DoD — Listenansicht-Filter | Typ-basierte Suche, Favoriten-Filter | TC-019-003, TC-019-004, TC-019-006 |
| §6 Szenario 1 — Coco Recycling | EC-Verlauf + Entsalzung + CalMag-Pufferung | TC-019-037 (als Grundlage) |
| §6 Szenario 2a — Steinwollwürfel ablehnen | Einweg-Substrat nicht wiederverwendbar | TC-019-035 |
| §6 Szenario 2b — Steinwollmatte wiederverwenden | Sterilisation + Entsalzung | TC-019-034 |
| §6 Szenario 3 — pH-Instabilität | σ-Grenzwert überschritten | TC-019-036 |
| UnsavedChangesGuard | Warnung bei dirty Form + Navigation | TC-019-017, TC-019-032 |
| Favoriten | Stern-Toggle, Filter-Button, localStorage | TC-019-006, TC-019-020 |
| Substrat-Mischung (SubstrateMixDialog) | Erstellen, Vorschau, Fraktionsvalidierung, Duplikate | TC-019-021 bis TC-019-027 |

---

*Hinweis zur Selenium/Playwright-Implementierung:*
- `data-testid="substrate-detail-page"` ist am Root-Element der SubstrateDetailPage gesetzt und kann als stabiler Anker verwendet werden
- Schieberegler (Slider) im SubstrateMixDialog sind per Aria-Attributen erreichbar (`role="slider"`)
- Alert-Boxes für Wiederverwendbarkeits-Ergebnisse erscheinen nach dem Chargen-Tabellen-Container und können per `role="alert"` oder MUI `severity`-Attribut selektiert werden
- Bestätigungsdialoge (ConfirmDialog mit `destructive=true`) rendern den Bestätigungs-Button in `color="error"` — im DOM als roter Button erkennbar
