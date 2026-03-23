---
req_id: REQ-004 + REQ-004-A
title: Dynamische Nährstoff- und Dünge-Engine (inkl. EC-Budget-Kalkulation)
category: Bewässerung & Düngung
test_count: 88
coverage_areas:
  - Düngemittel-Katalog (CRUD, Filterung, Lagerbestand)
  - Nährstoffplan-Verwaltung (CRUD, Phasen-Entries, Klonen, Zuweisung)
  - Multi-Channel Delivery (DeliveryChannel, Validierungsregeln)
  - EC-Budget-Kalkulation (WaterMixCalculator, 3-Stufen-Pipeline)
  - Mischprotokoll (Mischreihenfolge, Inkompatibilitätsprüfung)
  - Flushing-Protokoll (Pre-Harvest, substratabhängige Dauer)
  - Runoff-Analyse (EC/pH-Abweichungen, Salzakkumulation)
  - Gießplan (WateringSchedule, Wochentage/Intervall-Modus)
  - Gantt-Diagramm (Phasen-Zeitstrahl, Hover-Tooltip, Zyklus-Modus)
  - Dosierungsrechner-Tab (NED normalisierte Referenzdosierung)
  - Foliar-Warnung Blütephase
  - FeedingEvent (Dokumentation, Filter, Export)
  - Lagerbestand-Tracking und Niedrigbestand-Warnung
generated: 2026-03-21
version: REQ-004 v3.4, REQ-004-A v1.1
---

# Testfälle: REQ-004 — Dynamische Nährstoff- und Dünge-Engine

> Alle Testfälle sind aus der **End-Nutzer-Perspektive im Browser** formuliert.
> Browserpfade gelten innerhalb des Tenants, d. h. nach `/t/{tenant_slug}/`.

---

## Gruppe A — Düngemittel-Katalog (FertilizerListPage, FertilizerDetailPage)

---

## TC-004-001: Düngemittel-Liste aufrufen und Übersicht prüfen

**Requirement**: REQ-004 §3 (Fertilizer-Modell) / §7 DoD „Düngemittel-Filterung"
**Priority**: Critical
**Category**: Happy Path / Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und befindet sich in einem Tenant
- Mindestens drei Düngemittel sind im Katalog vorhanden (z. B. FloraGro, CalMag, pH-Down)

**Test Steps**:
1. Nutzer navigiert über die Seitenleiste zu „Düngung" → „Düngemittel".
2. Nutzer beobachtet die geladene Tabelle.

**Expected Results**:
- Die Tabelle zeigt alle Düngemittel mit mindestens den Spalten: Produktname, Hersteller (Brand), Typ, Tank-sicher (Ja/Nein), Bio.
- Die Gesamtanzahl wird als „Zeigt X von Y Einträgen" angezeigt.
- Ein Suchfeld mit Platzhalter „Tabelle durchsuchen…" ist vorhanden.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, list, catalog]

---

## TC-004-002: Düngemittel-Filter nach Typ anwenden

**Requirement**: REQ-004 §7 DoD „Düngemittel-Filterung" (fertilizer_type)
**Priority**: High
**Category**: Listenansicht / Filterung
**Preconditions**:
- Düngemittel verschiedener Typen sind vorhanden (z. B. `base`, `supplement`, `booster`, `biological`, `ph_adjuster`).

**Test Steps**:
1. Nutzer öffnet die Düngemittel-Liste.
2. Nutzer klickt auf den Filter-Chip „Typ" und wählt „Basis-Dünger" (base).
3. Nutzer beobachtet die gefilterte Tabelle.

**Expected Results**:
- Nur Düngemittel mit Typ `base` werden angezeigt.
- Ein aktiver Filter-Chip „Typ: Basis-Dünger" erscheint oberhalb der Tabelle.
- Die Eintragsanzahl reduziert sich entsprechend.

**Postconditions**:
- Filterauswahl bleibt bis zur Zurücksetzung aktiv.

**Tags**: [REQ-004, fertilizer, filter, type]

---

## TC-004-003: Düngemittel-Filter nach Tank-Sicherheit

**Requirement**: REQ-004 §7 DoD „Düngemittel-Filterung" (tank_safe)
**Priority**: High
**Category**: Listenansicht / Filterung
**Preconditions**:
- Sowohl tanksichere als auch nicht-tanksichere Düngemittel vorhanden.

**Test Steps**:
1. Nutzer öffnet die Düngemittel-Liste.
2. Nutzer aktiviert den Filter „Tank-sicher: Ja".
3. Nutzer beobachtet die Ergebnisse.
4. Nutzer wechselt den Filter auf „Tank-sicher: Nein".
5. Nutzer beobachtet die Ergebnisse.

**Expected Results**:
- Filter „Ja": Nur Einträge mit `tank_safe = true` sichtbar; kein organischer Feststoff-Dünger in der Liste.
- Filter „Nein": Nur Einträge mit `tank_safe = false` sichtbar (z. B. organische Flüssigdünger, Feststoffe).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, filter, tank-safe]

---

## TC-004-004: Düngemittel-Filter kombinieren (AND-Verknüpfung)

**Requirement**: REQ-004 §7 DoD „Düngemittel-Filterung" (kombinierbar)
**Priority**: Medium
**Category**: Listenansicht / Filterung
**Preconditions**:
- Mehrere Düngemittel vorhanden mit verschiedenen Kombinationen aus Typ, Bio und Tank-sicher.

**Test Steps**:
1. Nutzer öffnet die Düngemittel-Liste.
2. Nutzer setzt Filter „Typ: Biologisch" und „Bio: Ja" gleichzeitig.
3. Nutzer beobachtet die Ergebnisse.

**Expected Results**:
- Nur Düngemittel, die **beide** Bedingungen erfüllen, werden angezeigt (AND-Verknüpfung).
- Beide Filter-Chips sind gleichzeitig aktiv und sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, filter, combined]

---

## TC-004-005: Düngemittel-Filter zurücksetzen

**Requirement**: REQ-004 §7 / UI-NFR-010
**Priority**: Medium
**Category**: Listenansicht / Navigation
**Preconditions**:
- Mindestens ein Filter ist aktiv (z. B. Typ: Basis-Dünger).

**Test Steps**:
1. Mit aktivem Filter ist die Trefferliste reduziert.
2. Nutzer klickt auf den Button „Filter zurücksetzen" (`data-testid="reset-filters-button"`).

**Expected Results**:
- Alle aktiven Filter-Chips verschwinden.
- Die vollständige ungefilterte Düngerliste wird wieder angezeigt.
- Die Eintragsanzahl zeigt wieder den ursprünglichen Gesamtwert.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, filter, reset]

---

## TC-004-006: Neues Düngemittel erstellen — Happy Path

**Requirement**: REQ-004 §3 (Fertilizer-Modell), §7 DoD „Nährstoffplan-CRUD"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist als Mitglied eingeloggt (Schreibrecht auf Fertilizers).

**Test Steps**:
1. Nutzer navigiert zur Düngemittel-Liste und klickt „Erstellen".
2. Im Dialog füllt der Nutzer aus:
   - Produktname: „FloraGro Test"
   - Hersteller: „General Hydroponics"
   - Typ: „Basis-Dünger"
   - NPK-Verhältnis: N 2.0 / P 1.0 / K 6.0
   - EC-Beitrag pro ml/L: 0.10
   - Misch-Priorität: 4
   - Tank-sicher: aktiviert
   - Empfohlene Applikation: „Fertigation"
3. Nutzer klickt „Erstellen".

**Expected Results**:
- Erfolgsmeldung (Snackbar) „FloraGro Test wurde erstellt." erscheint.
- Der neue Eintrag erscheint in der Düngemittel-Liste.
- Klick auf den Eintrag öffnet die Detailseite mit allen eingegebenen Werten.

**Postconditions**:
- Düngemittel „FloraGro Test" ist im Katalog vorhanden.

**Tags**: [REQ-004, fertilizer, create, happy-path]

---

## TC-004-007: Düngemittel erstellen — Pflichtfeld-Validierung

**Requirement**: REQ-004 §3 (Fertilizer-Modell: product_name, brand min 1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Der Erstellen-Dialog ist geöffnet.

**Test Steps**:
1. Nutzer lässt das Feld „Produktname" leer.
2. Nutzer klickt „Erstellen".

**Expected Results**:
- Der Dialog bleibt geöffnet.
- Das Feld „Produktname" zeigt eine Inline-Fehlermeldung (z. B. „Pflichtfeld").
- Kein Snackbar für Erfolg erscheint.

**Postconditions**:
- Kein neuer Eintrag wurde erstellt.

**Tags**: [REQ-004, fertilizer, create, validation]

---

## TC-004-008: Düngemittel-Detailseite — Planverwendungs-Anzeige (Reverse Lookup)

**Requirement**: REQ-004 §7 DoD „Dünger-Planzuordnung (Reverse Lookup)"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Düngemittel „CalMag" ist in mindestens einem Nährstoffplan einer Phase-Entry zugeordnet.

**Test Steps**:
1. Nutzer öffnet die Detailseite von „CalMag".
2. Nutzer sucht den Abschnitt zur Planverwendung.

**Expected Results**:
- Ein Abschnitt „Verwendet in Nährstoffplänen" zeigt klickbare Chips/Links mit den Plannamen.
- Klick auf einen Plan-Chip navigiert zur NutrientPlanDetailPage des entsprechenden Plans.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, detail, reverse-lookup, plans]

---

## TC-004-009: Düngemittel-Detailseite — Kein Plan zugeordnet

**Requirement**: REQ-004 §7 DoD „Dünger-Planzuordnung (Reverse Lookup)"
**Priority**: Medium
**Category**: Detailansicht / Leerzustand
**Preconditions**:
- Düngemittel „Neues Enzym-Produkt" ist in keinem Nährstoffplan verwendet.

**Test Steps**:
1. Nutzer öffnet die Detailseite von „Neues Enzym-Produkt".
2. Nutzer beobachtet den Planverwendungs-Abschnitt.

**Expected Results**:
- Der Abschnitt zeigt explizit „Keinem Plan zugeordnet" (oder äquivalente Leer-Meldung).
- Keine leere Chip-Liste ohne Erklärung.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, detail, reverse-lookup, empty]

---

## TC-004-010: Lagerbestand erfassen

**Requirement**: REQ-004 §3 (FertilizerStock), §7 DoD „Inventar-Tracking"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Düngemittel „FloraGro" ist vorhanden ohne Lagerbestand.

**Test Steps**:
1. Nutzer öffnet die Detailseite von „FloraGro".
2. Nutzer klickt im Abschnitt „Lagerbestand" auf „Bestand hinzufügen".
3. Nutzer füllt aus: Volumen 1000 ml, Kaufdatum heute, Ablaufdatum in 18 Monaten, Chargennummer „LOT-001".
4. Nutzer klickt „Speichern".

**Expected Results**:
- Erfolgsmeldung erscheint.
- Der neue Lagerbestand erscheint in der Lagerbestandsliste mit 1000 ml und den eingegebenen Werten.

**Postconditions**:
- Lagerbestand für „FloraGro" ist mit 1000 ml eingetragen.

**Tags**: [REQ-004, fertilizer, stock, create]

---

## TC-004-011: Niedrigbestand-Warnung anzeigen

**Requirement**: REQ-004 §7 DoD „Inventar-Tracking: Warnung bei niedrigem Stock (<2 Wochen Vorrat)"
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel
**Preconditions**:
- Düngemittel „FloraGro" hat einen Lagerbestand von 100 ml.
- Der durchschnittliche Verbrauch liegt bei mehr als 50 ml/Woche (aus Feeding-Events ableitbar).

**Test Steps**:
1. Nutzer navigiert zur Düngemittel-Liste.
2. Nutzer beobachtet den Eintrag „FloraGro".
3. Nutzer öffnet die Detailseite von „FloraGro".

**Expected Results**:
- In der Listenansicht wird ein Warnbadge oder Hinweis bei „FloraGro" angezeigt (z. B. orangefarbenes Symbol oder Chip „Niedrig").
- Auf der Detailseite erscheint ein Warnhinweis: „Vorrat reicht für weniger als 2 Wochen" (oder äquivalente Formulierung).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, stock, low-stock-warning]

---

## Gruppe B — Nährstoffplan-Verwaltung (NutrientPlanListPage, NutrientPlanDetailPage)

---

## TC-004-012: Nährstoffplan-Liste aufrufen

**Requirement**: REQ-004 §3 (NutrientPlan), §7 DoD „Nährstoffplan-CRUD"
**Priority**: Critical
**Category**: Happy Path / Listenansicht
**Preconditions**:
- Mindestens zwei Nährstoffpläne sind im Tenant vorhanden.

**Test Steps**:
1. Nutzer navigiert über „Düngung" → „Nährstoffpläne".
2. Nutzer beobachtet die Liste.

**Expected Results**:
- Tabelle zeigt alle Pläne mit Spalten: Name, Substrat-Empfehlung, Tags, Autor, ist Template.
- Gesamtanzahl wird angezeigt.
- Suchfeld ist vorhanden.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, list]

---

## TC-004-013: Nährstoffplan nach Substrattyp filtern

**Requirement**: REQ-004 §7 DoD „Plan-Filterung" (substrate_type)
**Priority**: High
**Category**: Listenansicht / Filterung
**Preconditions**:
- Pläne für verschiedene Substrate vorhanden (coco, soil, hydro).

**Test Steps**:
1. Nutzer öffnet die Nährstoffplan-Liste.
2. Nutzer wählt Filter „Substrat: Coco".
3. Nutzer beobachtet die Ergebnisse.

**Expected Results**:
- Nur Pläne mit `recommended_substrate_type = coco` werden angezeigt.
- Filter-Chip „Substrat: Coco" ist aktiv.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, filter, substrate]

---

## TC-004-014: Nährstoffplan nach Tags filtern

**Requirement**: REQ-004 §7 DoD „Plan-Filterung" (tags)
**Priority**: Medium
**Category**: Listenansicht / Filterung
**Preconditions**:
- Pläne mit verschiedenen Tags vorhanden (z. B. „organic", „autoflower").

**Test Steps**:
1. Nutzer öffnet die Nährstoffplan-Liste.
2. Nutzer gibt im Suchfeld oder Tag-Filter „organic" ein.
3. Nutzer beobachtet die Ergebnisse.

**Expected Results**:
- Nur Pläne, die den Tag „organic" besitzen, werden angezeigt.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, filter, tags]

---

## TC-004-015: Neuen Nährstoffplan erstellen — Happy Path

**Requirement**: REQ-004 §3 (NutrientPlan), §7 DoD „Nährstoffplan-CRUD"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist als Mitglied eingeloggt.

**Test Steps**:
1. Nutzer klickt auf der Nährstoffplan-Liste auf „Erstellen".
2. Im Dialog gibt der Nutzer ein:
   - Name: „Tomato Heavy Coco"
   - Beschreibung: „Schwerer Tomatenplan für Coco"
   - Empfohlenes Substrat: „Coco"
   - Tags: „heavy-feeder", „coco"
   - Als Vorlage markieren: Nein
3. Nutzer klickt „Erstellen".

**Expected Results**:
- Erfolgsmeldung „Tomato Heavy Coco wurde erstellt." erscheint.
- Der neue Plan erscheint in der Liste.
- Klick auf den Plan öffnet die Detailseite mit Version „1", author = eingeloggter Nutzer.

**Postconditions**:
- Plan „Tomato Heavy Coco" ist vorhanden.

**Tags**: [REQ-004, nutrient-plan, create, happy-path]

---

## TC-004-016: Nährstoffplan erstellen — Namensfeld leer

**Requirement**: REQ-004 §3 (NutrientPlan: name.min_length=1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Der Plan-Erstellen-Dialog ist geöffnet.

**Test Steps**:
1. Nutzer lässt das Feld „Name" leer.
2. Nutzer klickt „Erstellen".

**Expected Results**:
- Dialog bleibt geöffnet.
- Inline-Fehlermeldung beim Namensfeld erscheint.
- Kein Plan wird erstellt.

**Postconditions**:
- Kein neuer Plan wurde erstellt.

**Tags**: [REQ-004, nutrient-plan, create, validation]

---

## TC-004-017: Phase-Entry zu Nährstoffplan hinzufügen — Happy Path

**Requirement**: REQ-004 §3 (NutrientPlanPhaseEntry), §7 DoD „Phase-Entry-Verwaltung"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plan „Tomato Heavy Coco" ist geöffnet (Detailseite, Tab „Phasen-Entries").

**Test Steps**:
1. Nutzer klickt auf „Phase hinzufügen".
2. Im Dialog wählt der Nutzer:
   - Phasenname: „Keimung" (germination)
   - Reihenfolge: 1
   - Woche Start: 1, Woche Ende: 2
   - NPK-Verhältnis: 2 / 1 / 2
   - Ziel-EC (Legacy): 0.5 mS
   - Ziel-pH (Legacy): 6.2
3. Nutzer klickt „Speichern".

**Expected Results**:
- Snackbar: Erfolgsbestätigung.
- Die Keimungsphase erscheint als Karte/Zeile im Phasen-Abschnitt des Plans.
- Woche 1–2, EC 0.5, pH 6.2, NPK 2/1/2 sind sichtbar.

**Postconditions**:
- Phase-Entry „germination" ist dem Plan zugeordnet.

**Tags**: [REQ-004, nutrient-plan, phase-entry, create]

---

## TC-004-018: Phase-Entry — week_end kleiner als week_start abgelehnt

**Requirement**: REQ-004 §3 (NutrientPlanPhaseEntry: week_end > week_start)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Phase-Entry-Dialog ist geöffnet.

**Test Steps**:
1. Nutzer gibt week_start = 5 und week_end = 3 ein.
2. Nutzer klickt „Speichern".

**Expected Results**:
- Inline-Fehlermeldung: „Woche Ende muss größer als Woche Start sein" (oder äquivalent).
- Dialog bleibt geöffnet; kein Entry wird gespeichert.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, phase-entry, validation, week-range]

---

## TC-004-019: Dünger einer Phase-Entry zuweisen

**Requirement**: REQ-004 §3 (USES_FERTILIZER), §7 DoD „Dünger-Zuweisung mit Dosierungen"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plan „Tomato Heavy Coco" hat die Phase-Entry „Vegetative" (Woche 3–6).
- Düngemittel „CalMag" und „FloraGro" sind im Katalog vorhanden.

**Test Steps**:
1. Nutzer öffnet die Phase-Entry „Vegetative" (Bearbeiten/Expand).
2. Nutzer klickt auf „Dünger hinzufügen".
3. Nutzer wählt „CalMag", Dosierung 1.5 ml/L, Optional: Nein.
4. Nutzer klickt „Speichern".
5. Nutzer wiederholt für „FloraGro", 2.0 ml/L, Optional: Nein.

**Expected Results**:
- Beide Dünger erscheinen in der Düngerliste der Phase-Entry.
- Dosierungen 1.5 und 2.0 ml/L sind sichtbar.
- Die Mischreihenfolge (mixing_priority) von CalMag < FloraGro wird korrekt sortiert angezeigt.

**Postconditions**:
- Zwei Dünger-Zuweisungen für die Vegetative-Phase sind gespeichert.

**Tags**: [REQ-004, nutrient-plan, phase-entry, fertilizer-dosage]

---

## TC-004-020: Dünger-Dosierung löschen aus Phase-Entry

**Requirement**: REQ-004 §3 (USES_FERTILIZER löschen)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Phase-Entry „Vegetative" enthält die Dünger „CalMag" und „FloraGro".

**Test Steps**:
1. Nutzer öffnet die Phase-Entry „Vegetative".
2. Nutzer klickt das Löschen-Symbol neben „FloraGro".
3. Nutzer bestätigt den Lösch-Dialog.

**Expected Results**:
- Erfolgsmeldung erscheint.
- „FloraGro" ist nicht mehr in der Düngerliste der Phase-Entry sichtbar.
- „CalMag" bleibt unverändert.

**Postconditions**:
- Die FloraGro-Zuweisung ist entfernt.

**Tags**: [REQ-004, nutrient-plan, phase-entry, fertilizer-dosage, delete]

---

## TC-004-021: Plan-Vollständigkeits-Validierung — fehlende Pflichtphasen

**Requirement**: REQ-004 §3 (NutrientPlanValidator.MANDATORY_PHASES: seedling, vegetative, flowering)
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel
**Preconditions**:
- Plan „Unvollständiger Plan" hat nur die Phase-Entry „Keimung" (germination), keine vegetative oder flowering.

**Test Steps**:
1. Nutzer öffnet den Plan und klickt auf „Plan validieren" (oder navigiert zum Validierungs-Tab).

**Expected Results**:
- Validierungsergebnis zeigt „Unvollständig".
- Die fehlenden Pflichtphasen werden aufgelistet: „Sämling (seedling)", „Vegetativ (vegetative)", „Blüte (flowering)" oder deren Teilmenge.
- Kein Hardblock — der Plan bleibt speicherbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, validation, completeness]

---

## TC-004-022: EC-Budget-Validierung — Abweichung angezeigt

**Requirement**: REQ-004 §3 (NutrientPlanValidator.validate_ec_budget, Toleranz ±0.3 mS)
**Priority**: High
**Category**: Zustandswechsel / Fehlermeldung
**Preconditions**:
- Phase-Entry „Vegetative" hat Ziel-EC 1.4 mS.
- Die zugewiesenen Dünger-Dosierungen ergeben zusammen eine berechnete EC von 0.8 mS (Differenz 0.6 mS > Toleranz 0.3 mS).

**Test Steps**:
1. Nutzer öffnet den Plan und klickt „Plan validieren".

**Expected Results**:
- Validierungsergebnis zeigt für die Vegetative-Phase den Status „EC-Budget-Abweichung".
- Die Anzeige zeigt: Ziel-EC 1.4 mS, berechnete EC 0.8 mS, Abweichung 0.6 mS.
- Hinweis mit Empfehlung „Dosierungen anpassen" ist sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, validation, ec-budget]

---

## TC-004-023: Nährstoffplan klonen (Deep Copy)

**Requirement**: REQ-004 §3 (clone_plan), §7 DoD „Plan-Klonen (Deep Copy)"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Plan „Tomato Heavy Coco" (Version 3, 4 Phase-Entries mit Düngern) ist vorhanden.

**Test Steps**:
1. Nutzer öffnet den Plan „Tomato Heavy Coco".
2. Nutzer klickt auf „Klonen" / „Als Kopie speichern".
3. Im Dialog gibt der Nutzer den neuen Namen „Tomato Light Coco" ein.
4. Nutzer klickt „Klonen".

**Expected Results**:
- Erfolgsmeldung erscheint.
- Plan „Tomato Light Coco" erscheint in der Plan-Liste.
- Der geklonte Plan hat Version 1 und denselben Autor wie der eingeloggte Nutzer.
- Detailseite des Klons zeigt alle 4 Phase-Entries mit identischen Dosierungen wie das Original.

**Postconditions**:
- Plan „Tomato Light Coco" ist unabhängig vom Original.

**Tags**: [REQ-004, nutrient-plan, clone]

---

## TC-004-024: Nährstoffplan einer PlantInstance zuweisen

**Requirement**: REQ-004 §3 (assign_plan_to_plant / FOLLOWS_PLAN), §7 DoD „Plan-Zuweisung an PlantInstance"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- PlantInstance „Tomate-001" hat keinen zugewiesenen Nährstoffplan.
- Plan „Tomato Heavy Coco" ist vorhanden.

**Test Steps**:
1. Nutzer navigiert zur Detailseite von „Tomate-001" (PflanzenDetailPage, Tab „Nährstoffplan").
2. Nutzer klickt „Nährstoffplan zuweisen".
3. Nutzer wählt „Tomato Heavy Coco" aus dem Dropdown.
4. Nutzer klickt „Zuweisen".

**Expected Results**:
- Erfolgsmeldung erscheint.
- Tab zeigt nun „Zugewiesener Plan: Tomato Heavy Coco" mit Zuweisung-Zeitstempel.

**Postconditions**:
- FOLLOWS_PLAN-Edge von „Tomate-001" zu „Tomato Heavy Coco" ist gespeichert.

**Tags**: [REQ-004, nutrient-plan, assign, plant-instance]

---

## TC-004-025: Plan-Zuweisung wechseln

**Requirement**: REQ-004 §3 (assign_plan_to_plant — ersetzt vorherige), §7 Szenario 9
**Priority**: High
**Category**: Happy Path / Zustandswechsel
**Preconditions**:
- PlantInstance „Tomate-001" hat Plan „Tomato Heavy Coco" zugewiesen.

**Test Steps**:
1. Nutzer öffnet den Tab „Nährstoffplan" von „Tomate-001".
2. Nutzer klickt „Plan wechseln".
3. Nutzer wählt „Auto Light Feed" aus dem Dropdown.
4. Nutzer klickt „Zuweisen".

**Expected Results**:
- Erfolgsmeldung erscheint.
- Tab zeigt nun „Zugewiesener Plan: Auto Light Feed".
- Vorgänger-Plan „Tomato Heavy Coco" ist nicht mehr als aktiv ausgewiesen.

**Postconditions**:
- Nur eine FOLLOWS_PLAN-Edge ist aktiv (zu „Auto Light Feed").

**Tags**: [REQ-004, nutrient-plan, assign, switch]

---

## TC-004-026: Aktuelle Dosierungen aus Plan + Phase ableiten

**Requirement**: REQ-004 §3 (get_current_dosages), §7 Szenario 7
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- PlantInstance „Tomate-001" hat Plan „Tomato Heavy Coco" zugewiesen.
- „Tomate-001" befindet sich in Phase „vegetative".
- Vegetative Phase-Entry hat CalMag (1.5 ml/L, Prio 3) + FloraMicro (2 ml/L, Prio 4) + FloraGro (2 ml/L, Prio 5).

**Test Steps**:
1. Nutzer öffnet den Tab „Nährstoffplan" von „Tomate-001".
2. Nutzer beobachtet die aktuellen Dosierungen.

**Expected Results**:
- Aktuelle Dosierungsliste zeigt: CalMag 1.5 ml/L, FloraMicro 2.0 ml/L, FloraGro 2.0 ml/L.
- Die Dünger sind nach mixing_priority aufsteigend sortiert (CalMag zuerst).
- EC-Ziel und pH-Ziel der Vegetative-Phase werden angezeigt.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, current-dosages, plant-instance]

---

## TC-004-027: Nährstoffplan löschen

**Requirement**: REQ-004 §3 (delete_plan)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Plan „Temporärer Testplan" ist vorhanden und keiner PlantInstance zugewiesen.

**Test Steps**:
1. Nutzer öffnet die Detailseite von „Temporärer Testplan".
2. Nutzer klickt „Löschen".
3. Im Bestätigungsdialog liest der Nutzer die Meldung und klickt „Löschen bestätigen".

**Expected Results**:
- Bestätigungsdialog zeigt: „Sind Sie sicher, dass Sie ‚Temporärer Testplan' löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
- Nach Bestätigung erscheint Erfolgsmeldung.
- Plan ist nicht mehr in der Nährstoffplan-Liste vorhanden.

**Postconditions**:
- Plan „Temporärer Testplan" ist gelöscht.

**Tags**: [REQ-004, nutrient-plan, delete]

---

## Gruppe C — Nährstoff-Berechnungsseite (NutrientCalculationsPage)

---

## TC-004-028: Berechnungsseite aufrufen und Formular befüllen

**Requirement**: REQ-004 §3 (NutrientSolutionCalculator), §7 DoD „EC-Budget-Kalkulation"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt.
- Düngemittel mit `ec_contribution_per_ml > 0` sind vorhanden.

**Test Steps**:
1. Nutzer navigiert über „Düngung" → „Nährstoffrechner".
2. Nutzer füllt aus: Zielvolumen 50 L, Ziel-EC 1.8 mS, Ziel-pH 6.0, Basis-EC 0.20 mS.
3. Nutzer fügt Dünger hinzu: FloraGro (Base B), FloraMicro (Base A), CalMag.
4. Nutzer klickt „Berechnen".

**Expected Results**:
- Das Mischprotokoll wird angezeigt mit:
  - Berechneter EC-Wert nahe 1.8 mS (± Toleranz).
  - Dosierungen in ml/L und ml-Gesamtmenge pro Dünger.
  - Schritt-für-Schritt-Misch-Anleitung.

**Postconditions**:
- Keine Datenmutation (zustandslose Berechnung).

**Tags**: [REQ-004, calculator, ec-budget, happy-path]

---

## TC-004-029: Basis-EC höher als Ziel-EC — Warnung

**Requirement**: REQ-004-A §4.1 / REQ-004 §3 (validate_ec_for_substrate)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Berechnungsformular ist geöffnet.

**Test Steps**:
1. Nutzer gibt ein: Ziel-EC 0.8 mS, Basis-EC 1.2 mS.
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Eine Warnmeldung erscheint: „Basis-EC des Wassers (1.2 mS) erreicht oder überschreitet den Ziel-EC (0.8 mS). Erhöhen Sie den Osmose-Anteil oder senken Sie den Ziel-EC."
- Keine Dosierungsliste wird ausgegeben (leere Liste).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, calculator, ec-budget, warning, base-ec-too-high]

---

## TC-004-030: EC-Obergrenze überschritten — Warnung (kein Hardblock)

**Requirement**: REQ-004-A §4.2 (EC_max nach Substrat/Phase), §9.2
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Substrat Coco, Phase Seedling: EC_max = 1.0 mS.

**Test Steps**:
1. Nutzer wählt Substrat „Coco", Phase „Keimling (Seedling)".
2. Nutzer gibt Ziel-EC 1.5 mS ein (überschreitet Obergrenze 1.0 mS für Coco Seedling).
3. Nutzer klickt „Berechnen".

**Expected Results**:
- Warnmeldung erscheint: „Ziel-EC (1.5 mS) überschreitet die empfohlene Obergrenze (1.0 mS) für Keimling auf Coco."
- Das Berechnungsergebnis wird **trotzdem** angezeigt (kein Hardblock).
- Mischprotokoll enthält die berechneten Werte mit deutlichem Warnhinweis.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, calculator, ec-max, warning]

---

## TC-004-031: Misch-Reihenfolge im Protokoll korrekt sortiert

**Requirement**: REQ-004 §1 (Empfohlene Misch-Reihenfolge via mixing_priority), §7 Szenario 1
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Düngemittel: CalMag (mixing_priority 2), FloraMicro (mixing_priority 4), FloraGro (mixing_priority 5).

**Test Steps**:
1. Nutzer gibt im Rechner alle drei Dünger ein.
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Im Mischprotokoll / Schritt-für-Schritt-Anleitung erscheinen die Dünger in der Reihenfolge:
  1. Wasser vorbereiten
  2. CalMag zugeben
  3. FloraMicro zugeben
  4. FloraGro zugeben
  5. pH-Korrektur
  6. Finale Messung

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, calculator, mixing-order, protocol]

---

## TC-004-032: Inkompatibilitätswarnung im Mischprotokoll

**Requirement**: REQ-004 §3 (MixingSafetyValidator), §7 Szenario 4
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Düngemittel „CalMag" (enthält Calcium) und „Bittersalz" (MgSO₄, enthält Sulfat) sind mit INCOMPATIBLE_WITH-Edge verknüpft (severity: CRITICAL).

**Test Steps**:
1. Nutzer wählt im Rechner „CalMag" und „Bittersalz".
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Im Mischprotokoll erscheint ein roter Warnhinweis: „KRITISCH: Nicht zusammen mischen: Calcium-Sulfat-Ausfällung (Gips)" oder äquivalente Formulierung.
- Die Schwere ist CRITICAL sichtbar markiert.
- Empfehlung zur sequenziellen Zugabe mit Wartezeit ist sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, calculator, incompatibility, warning]

---

## TC-004-033: Einzeldünger-Sicherheitslimit überschritten

**Requirement**: REQ-004-A §5.5 (max_ml_per_liter: Herstellerangabe oder 20 ml/L Fallback)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Düngemittel „Enzym-Reiniger" hat `max_dose_ml_per_liter = 5.0`.

**Test Steps**:
1. Nutzer gibt für „Enzym-Reiniger" eine Dosierung von 25 ml/L ein (überschreitet 5 ml/L).
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Warnmeldung erscheint: „Dosierung (25 ml/L) überschreitet das Sicherheitslimit von 5 ml/L für Enzym-Reiniger."
- Das Ergebnis wird ggf. mit der maximalen Dosierung gekappt und entsprechend angezeigt.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, calculator, safety-limit, dosage]

---

## Gruppe D — WaterMix-Empfehlung (WaterMixRecommendationBox)

---

## TC-004-034: Mischverhältnis-Empfehlung anzeigen

**Requirement**: REQ-004 §1 / REQ-004-A §3.3 / §7 DoD „Mischverhältnis-Empfehlung UI"
**Priority**: High
**Category**: Happy Path / Detailansicht
**Preconditions**:
- Site „Gewächshaus-1" hat ein TapWaterProfile (EC 0.55 mS, Ca 120 ppm, Mg 25 ppm) und ein RoWaterProfile (EC 0.02 mS).
- Nährstoffplan „Cannabis Coco" ist geöffnet und der Site zugeordnet.

**Test Steps**:
1. Nutzer öffnet den Plan und navigiert zur Phase-Entry „Vegetative" (oder zum Dosierungsrechner-Tab).
2. Nutzer wählt Site „Gewächshaus-1" im Dropdown.
3. Nutzer beobachtet die WaterMix-Empfehlung-Box.

**Expected Results**:
- Die Box zeigt:
  - Empfohlenen Osmose-Anteil (z. B. „75% Osmose empfohlen").
  - Effektiven Wasser-EC nach Mischung.
  - EC-Headroom für Dünger (in %).
  - Ob CalMag-Supplement benötigt wird.
  - Chlor-Warnung (falls Chlor > 0.5 ppm).
  - Begründungstext (reasoning).
- 2–3 Alternativen werden angezeigt mit Trade-off-Beschreibung.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, water-mix, recommendation, ui]

---

## TC-004-035: Mischverhältnis-Empfehlung — kein Osmose-System

**Requirement**: REQ-004-A §9.4 (kein RO-System)
**Priority**: Medium
**Category**: Fehlermeldung / Leerzustand
**Preconditions**:
- Site „Freiland-1" hat `has_ro_system = false`.

**Test Steps**:
1. Nutzer wählt im Dosierungsrechner-Tab Site „Freiland-1".

**Expected Results**:
- Die WaterMix-Box zeigt: „Kein Osmose-System vorhanden. Basis-EC = Leitungswasser-EC (X mS)."
- Kein Osmose-Anteil-Schieberegler/Dropdown wird angezeigt.
- EC-Budget wird direkt basierend auf dem Leitungswasser-EC berechnet.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, water-mix, no-ro-system]

---

## TC-004-036: Mischverhältnis-Empfehlung — Chlorwarnung

**Requirement**: REQ-004 §1 / REQ-004-A §5 (effective_chlorine > 0.5 ppm)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Site mit Leitungswasser-Chlor von 0.8 ppm.
- Phase „Blüte" (flowering) ist ausgewählt.

**Test Steps**:
1. Nutzer wählt die Site mit hohem Chlorgehalt im Dosierungsrechner.
2. Nutzer beobachtet die Mischverhältnis-Empfehlung.

**Expected Results**:
- Die Empfehlung zeigt `chlorine_warning: true`.
- Hinweis: „Chlorgehalt über Schwellenwert (0.8 ppm > 0.5 ppm) — höheren Osmose-Anteil verwenden zum Schutz des Wurzelmikrobioms."
- Empfohlener Osmose-Anteil ist ≥ 70% (Chlorwert erzwingt höheren Anteil).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, water-mix, chlorine-warning]

---

## TC-004-037: CalMag-Empfehlung bei hohem Osmose-Anteil

**Requirement**: REQ-004-A §3.6 / §7 DoD „CalMag-Empfehlung"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Site mit Leitungswasser Ca 120 ppm, Mg 25 ppm, RO-System vorhanden.
- Empfohlener Osmose-Anteil aus Empfehlung: 75%.

**Test Steps**:
1. Nutzer wählt 75% Osmose-Anteil im Dosierungsrechner.
2. Nutzer beobachtet die CalMag-Empfehlung.

**Expected Results**:
- Effektives Ca im Mischwasser: 120 × 0.25 = 30 ppm (< Zielwert von 150 ppm für Vegetative).
- Anzeige: „CalMag-Supplement empfohlen: Ca-Defizit 120 ppm, Mg-Defizit X ppm."
- Empfohlene CalMag-Dosierung in ml/L wird angezeigt.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, water-mix, calmag, recommendation]

---

## Gruppe E — Dosierungsrechner-Tab (NED normalisierte Referenzdosierung)

---

## TC-004-038: Dosierungsrechner-Tab aufrufen — mit Wasserprofil

**Requirement**: REQ-004 §4b.7 (UI Dosierungsrechner), §7 DoD „UI Dosierungsrechner (NED-13)"
**Priority**: High
**Category**: Happy Path / Detailansicht
**Preconditions**:
- Plan „Cannabis Coco Standard" hat `reference_base_ec: 0.0` und Phase-Entries mit `target_ec_ms`.
- Site „Growzelt-1" hat vollständiges Wasserprofil (EC_tap 0.45 mS, Ca 80 ppm, Mg 15 ppm).

**Test Steps**:
1. Nutzer öffnet NutrientPlanDetailPage von „Cannabis Coco Standard".
2. Nutzer klickt auf Tab „Dosierungsrechner".
3. Nutzer wählt Site „Growzelt-1" im Site-Dropdown.

**Expected Results**:
- Wasser-Info-Box zeigt: EC_tap, EC_RO, empfohlenes Mischverhältnis, effektive Wasserparameter.
- Für jede Phase: Bereich mit Referenzdosierungen (grau, „Herstellerangabe") UND berechneten Dosierungen (hervorgehoben, „Für dein Wasser").
- EC-Budget-Visualisierung (z. B. Segmented Bar) zeigt Aufteilung: Wasser / CalMag / Dünger / pH-Reserve.
- Misch-Anleitung (Step-by-Step) wird generiert.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, dosage-calculator, ned, water-profile]

---

## TC-004-039: Dosierungsrechner-Tab — kein Wasserprofil (Fallback)

**Requirement**: REQ-004 §4b.7 / §7 DoD „Kein-Wasser-Fallback (NED-08)"
**Priority**: High
**Category**: Leerzustand / Fehlermeldung
**Preconditions**:
- Plan „Cannabis Coco Standard" ist geöffnet.
- Keine Site ist ausgewählt oder Site hat kein Wasserprofil.

**Test Steps**:
1. Nutzer öffnet Tab „Dosierungsrechner" ohne Site-Auswahl.

**Expected Results**:
- Unveränderte Referenzdosierungen werden angezeigt.
- Hinweis: „Wasserprofil auf der Site hinterlegen für automatische Dosierungsanpassung."
- Kein Fehler-Screen — Seite bleibt nutzbar mit statischen Werten.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, dosage-calculator, no-water-profile, fallback]

---

## TC-004-040: Dosierungsrechner — Proportionserhaltung bei Skalierung

**Requirement**: REQ-004 §4b.2 (Proportionserhaltung), §7 DoD „Proportionserhaltung (NED-07)"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Phase „Vegetative" hat Referenzdosierungen: Micro 4 ml/L, Grow 4 ml/L, Bloom 4 ml/L (3:2:1 Rezept).
- Skalierungsfaktor k = 0.83 (aus Beispielrechnung REQ-004-A §7).

**Test Steps**:
1. Nutzer wählt eine Site und beobachtet die berechneten Dosierungen.

**Expected Results**:
- Berechnete Dosierungen: Micro ≈ 3.32 ml/L, Grow ≈ 3.32 ml/L, Bloom ≈ 3.32 ml/L (Verhältnis 1:1:1 bleibt).
- Das Verhältnis zwischen den Düngern ist unverändert.
- `source`-Feld zeigt „scaled" für alle skalierten Dünger.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, dosage-calculator, proportionality, ned]

---

## TC-004-041: Dosierungsrechner — source-Feld sichtbar

**Requirement**: REQ-004 §4b.5 / §7 DoD „Dosage-Source-Feld (NED-10)"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Phase „Vegetative" hat CalMag (auto_calmag), Rhino Skin (reference, ec=0), Micro/Grow/Bloom (scaled).

**Test Steps**:
1. Nutzer beobachtet die Dosierungsliste im Rechner-Tab.

**Expected Results**:
- Jeder Eintrag zeigt ein visuelles Kennzeichen für die Quelle:
  - „Herstellerangabe" (reference) — grau
  - „Skaliert" (scaled) — normal
  - „Auto-CalMag" (auto_calmag) — hervorgehoben (z. B. blau/grün mit Erklärung)

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, nutrient-plan, dosage-calculator, source-field]

---

## TC-004-042: RO-Anteil ≥ 80% — pH-Puffer-Warnung

**Requirement**: REQ-004 §4b.3 / §7 DoD „RO-Warnung (NED-09)"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Site mit niedrigem Leitungswasser-EC (0.1 mS).

**Test Steps**:
1. Nutzer wählt manuell 85% Osmose-Anteil im Dosierungsrechner.

**Expected Results**:
- Warnung: „Kein pH-Puffer (KH~0) — pH nach dem Mischen prüfen. Bei >80% Osmose-Anteil fehlt die Karbonathärte als pH-Puffer."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, dosage-calculator, ro-warning, ph-buffer]

---

## Gruppe F — Flushing-Protokoll

---

## TC-004-043: Flushing-Protokoll aufrufen — Coco-Substrat

**Requirement**: REQ-004 §1 (Flushing-Strategien) / §3 (FlushingProtocol), §7 DoD „Flushing-Scheduler"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- PlantInstance in Phase „Blüte" auf Coco-Substrat mit aktueller EC 2.2 mS.
- Bis zur Ernte sind 14 Tage.

**Test Steps**:
1. Nutzer öffnet die Detailseite der Pflanze.
2. Nutzer klickt auf „Flush-Protokoll starten" oder navigiert zum Flushing-Bereich.

**Expected Results**:
- Flush-Plan wird angezeigt:
  - Gesamtdauer: 10–14 Tage (Coco-Optimum).
  - Tag 0–4: Reduzierte Dosis (EC schrittweise sinkend von 2.2 auf ca. 1.1 mS).
  - Tag 5–9: Minimale Dosis (EC sinkt auf ca. 0.5 mS).
  - Tag 10–14: Nur Wasser (EC 0.0).
- Hinweis: „Blätter vergilben = normal!" ist sichtbar.
- Alle 3 Tage ist eine EC-Messung markiert.

**Postconditions**:
- Kein automatischer Phasenwechsel; Protokoll ist ein Informations-/Planungsartefakt.

**Tags**: [REQ-004, flushing, protocol, coco]

---

## TC-004-044: Flushing zu spät gestartet — TOO_LATE Warnung

**Requirement**: REQ-004 §3 (FlushingProtocol: days_until_harvest < min)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Bis zur Ernte: 4 Tage (weniger als Coco-Minimum 10 Tage).

**Test Steps**:
1. Nutzer öffnet das Flushing-Protokoll.

**Expected Results**:
- Warnmeldung: „Nur noch 4 Tage — Minimum für Coco: 10 Tage. Notfall-Flush (nur Wasser, täglich spülen)."
- Status TOO_LATE ist sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, flushing, too-late, warning]

---

## Gruppe G — Runoff-Analyse

---

## TC-004-045: Runoff-Analyse — Salzakkumulation (SALT_BUILDUP)

**Requirement**: REQ-004 §3 (RunoffAnalyzer), §7 Szenario 3
**Priority**: High
**Category**: Happy Path / Zustandswechsel
**Preconditions**:
- FeedingEvent-Formular oder Runoff-Analyse-Widget ist geöffnet.

**Test Steps**:
1. Nutzer gibt ein: Input-EC 1.6 mS, Runoff-EC 2.8 mS.
2. Nutzer klickt „Analysieren".

**Expected Results**:
- EC-Analyse zeigt Status: „SALT_BUILDUP" (Salzakkumulation).
- Empfehlung: „Flush erforderlich — Salzakkumulation im Substrat."
- Unterschied: +1.2 mS sichtbar.
- Gesamt-Gesundheitsstatus: „CRITICAL" oder „WARNING — Anpassungen empfohlen".

**Postconditions**:
- Keine Datenmutation (Analyse ist zustandslos).

**Tags**: [REQ-004, runoff, salt-buildup, analysis]

---

## TC-004-046: Runoff-Analyse — Runoff-Prozentsatz zu niedrig

**Requirement**: REQ-004 §3 (RunoffAnalyzer: runoff_percent < 10%)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Runoff-Analyse-Widget ist geöffnet.

**Test Steps**:
1. Nutzer gibt ein: Input-Volumen 10 L, Runoff-Volumen 0.8 L (8%).
2. Nutzer klickt „Analysieren".

**Expected Results**:
- Runoff-Status: „Zu wenig Runoff".
- Empfehlung: „Erhöhe Wassermenge (Ziel: 15–20%)."
- Aktueller Prozentsatz 8% ist sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, runoff, too-low, analysis]

---

## TC-004-047: Runoff-Analyse — Optimaler Bereich

**Requirement**: REQ-004 §3 (RunoffAnalyzer: status OK)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Runoff-Analyse-Widget ist geöffnet.

**Test Steps**:
1. Nutzer gibt ein: Input-EC 1.6 mS, Runoff-EC 1.7 mS, Input-Vol. 10 L, Runoff-Vol. 1.8 L (18%).
2. Nutzer klickt „Analysieren".

**Expected Results**:
- EC-Status: „OK — Nährstoffaufnahme im normalen Bereich."
- Runoff-Status: „OK — Runoff im Zielbereich (18%)."
- Gesamt-Gesundheitsstatus: „HEALTHY — Alles im grünen Bereich."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, runoff, optimal, analysis]

---

## Gruppe H — FeedingEvent (Düngungsdokumentation)

---

## TC-004-048: Feeding-Event für eine Pflanze erfassen

**Requirement**: REQ-004 §3 (FeedingEvent), §7 DoD „Dosierungs-Historie"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- PlantInstance „Cannabis-001" ist in Phase „vegetative".
- Nutzer ist auf der FeedingEvent-Erstellseite oder öffnet den Dialog.

**Test Steps**:
1. Nutzer navigiert zu „Düngung" → „Düngungsprotokoll" → „Neu".
2. Nutzer wählt Pflanze „Cannabis-001".
3. Nutzer wählt Applikationsmethode: „Drench (Gießkanne)".
4. Nutzer gibt ein: Volumen 5 L, EC vorher 1.8 mS, EC nachher 1.7 mS, pH vorher 6.0, pH nachher 6.1.
5. Nutzer klickt „Speichern".

**Expected Results**:
- Erfolgsmeldung erscheint.
- Das neue FeedingEvent erscheint in der FeedingEvent-Liste.
- Datum/Uhrzeit, Pflanze, EC/pH-Werte und Methode „Drench" sind sichtbar.

**Postconditions**:
- FeedingEvent ist gespeichert.

**Tags**: [REQ-004, feeding-event, create, happy-path]

---

## TC-004-049: Foliar-Warnung in Blütephase ab Woche 2

**Requirement**: REQ-004 §1 (Phasenbasierte Foliar-Warnung, G-013), §7 DoD „Foliar-Warnung Blüte"
**Priority**: Critical
**Category**: Fehlermeldung / Zustandswechsel
**Preconditions**:
- PlantInstance befindet sich in Phase „flowering", Woche 3 (≥ Woche 2).

**Test Steps**:
1. Nutzer öffnet FeedingEvent-Erstellen-Dialog für die betreffende Pflanze.
2. Nutzer wählt Applikationsmethode: „Foliar (Blattdüngung)".

**Expected Results**:
- Gelbes Warnsymbol (⚠) erscheint neben dem Applikationsmethoden-Dropdown.
- Alert-Banner erscheint: „Foliar-Feeding in der Blüte (ab Woche 2) vermeiden! Schimmelrisiko auf Buds, Geschmacksverunreinigung und Rückstände auf Erntegut. Blattdüngung nur in Vegetationsphase oder maximal Blütewoche 1."
- Der Nutzer kann das FeedingEvent **trotzdem** speichern (kein Hardblock).

**Postconditions**:
- FeedingEvent ist mit Warnung speicherbar.

**Tags**: [REQ-004, feeding-event, foliar, warning, flowering, g-013]

---

## TC-004-050: Foliar-Warnung in Blütephase Woche 1 — nur INFO

**Requirement**: REQ-004 §1 (Phasenbasierte Foliar-Warnung: Woche 1 = INFO, ab Woche 2 = WARNING)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- PlantInstance befindet sich in Phase „flowering", Woche 1.

**Test Steps**:
1. Nutzer wählt Applikationsmethode: „Foliar (Blattdüngung)".

**Expected Results**:
- Ein informativer Hinweis (blau/INFO) erscheint — kein gelbes Warnbanner.
- Der Hinweis ist weniger prominent als das WARNING ab Woche 2.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, feeding-event, foliar, info, flowering-week1]

---

## TC-004-051: Foliar-Warnung unterdrückt bei IPM-Notfallbehandlung

**Requirement**: REQ-004 §1 (Ausnahmeregel: is_emergency = true, REQ-010 TreatmentApplication)
**Priority**: Medium
**Category**: Zustandswechsel / Happy Path
**Preconditions**:
- PlantInstance in Phase „flowering", Woche 3.
- FeedingEvent ist mit einer TreatmentApplication (REQ-010) verknüpft, die `is_emergency = true` hat.

**Test Steps**:
1. Nutzer erstellt FeedingEvent und verknüpft eine Notfall-IPM-Behandlung.
2. Nutzer wählt Applikationsmethode: „Foliar".

**Expected Results**:
- Das gelbe WARNING-Banner erscheint **nicht**.
- Optional: Ein informativer Hinweis zeigt, dass die Warnung aufgrund der Notfallbehandlung unterdrückt ist.

**Postconditions**:
- FeedingEvent mit Foliar in der Blüte ist ohne Warnung speicherbar.

**Tags**: [REQ-004, feeding-event, foliar, emergency-exception, ipm]

---

## TC-004-052: FeedingEvent-Liste — Zeitraum-Filter

**Requirement**: REQ-004 §7 DoD „FeedingEvent-Filter" (date_from, date_to, URL-persistiert)
**Priority**: High
**Category**: Listenansicht / Filterung
**Preconditions**:
- FeedingEvents für die letzten 60 Tage sind vorhanden.

**Test Steps**:
1. Nutzer navigiert zu „Düngung" → „Düngungsprotokoll".
2. Nutzer wählt Datum-Range: Beginn (heute − 7 Tage), Ende (heute).
3. Nutzer beobachtet die gefilterte Liste.

**Expected Results**:
- Nur FeedingEvents der letzten 7 Tage werden angezeigt.
- Die URL enthält die Filter-Parameter (z. B. `?date_from=...&date_to=...`).
- Nach Neuladen der Seite bleiben die Filter aktiv (URL-Persistenz).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, feeding-event, filter, date-range, url-persistence]

---

## TC-004-053: FeedingEvent-Liste — Run-Filter

**Requirement**: REQ-004 §7 DoD „FeedingEvent-Filter" (Run-Dropdown)
**Priority**: Medium
**Category**: Listenansicht / Filterung
**Preconditions**:
- FeedingEvents für mehrere PlantingRuns vorhanden.

**Test Steps**:
1. Nutzer öffnet das Düngungsprotokoll.
2. Nutzer wählt im Run-Dropdown „Durchlauf Sommer 2026".
3. Nutzer beobachtet die Ergebnisse.

**Expected Results**:
- Nur FeedingEvents für Pflanzen des Durchlaufs „Sommer 2026" werden angezeigt.
- Filter-Chip ist aktiv.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, feeding-event, filter, run]

---

## TC-004-054: FeedingEvent-Liste — CSV-Export

**Requirement**: REQ-004 §7 DoD „Düngeprotokoll-Export"
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- FeedingEvents sind sichtbar (gefilterte oder ungefilterte Ansicht).

**Test Steps**:
1. Nutzer klickt auf den Button „CSV exportieren" in der FeedingEvent-Liste.

**Expected Results**:
- Ein Datei-Download wird ausgelöst (CSV-Datei).
- Die Datei enthält die aktuell sichtbaren/gefilterten FeedingEvents mit Spalten: Datum, Pflanze, EC vorher/nachher, pH vorher/nachher, Volumen, Applikationsmethode.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, feeding-event, export, csv]

---

## Gruppe I — Gießplan (WateringSchedule)

---

## TC-004-055: Gießplan im Wochentage-Modus erstellen

**Requirement**: REQ-004 §3 (WateringSchedule), §7 DoD „WateringSchedule-Modus Weekdays"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- NutrientPlan-Bearbeitungsformular ist geöffnet.

**Test Steps**:
1. Nutzer aktiviert den Abschnitt „Gießplan".
2. Nutzer wählt Modus: „Feste Wochentage".
3. Nutzer wählt Montag, Mittwoch, Freitag (0, 2, 4).
4. Nutzer gibt bevorzugte Zeit „08:00" ein.
5. Nutzer klickt „Speichern".

**Expected Results**:
- Plan wird gespeichert.
- Auf der Detailseite zeigt der Gießplan „Mo / Mi / Fr, 08:00 Uhr".

**Postconditions**:
- Gießplan-Konfiguration ist gespeichert.

**Tags**: [REQ-004, watering-schedule, weekdays]

---

## TC-004-056: Gießplan im Wochentage-Modus — Duplikat abgelehnt

**Requirement**: REQ-004 §3 (WateringSchedule: keine Duplikate in weekday_schedule)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Gießplan-Formular ist geöffnet, Modus „Wochentage".

**Test Steps**:
1. Nutzer versucht, Montag zweimal auszuwählen (0, 0).
2. Nutzer klickt „Speichern".

**Expected Results**:
- Fehlermeldung: „Wochentage dürfen keine Duplikate enthalten."
- Oder: Die UI verhindert die doppelte Auswahl (z. B. deaktivierter zweiter Klick).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, watering-schedule, validation, duplicate]

---

## TC-004-057: Gießplan im Intervall-Modus erstellen

**Requirement**: REQ-004 §3 (WateringSchedule), §7 DoD „WateringSchedule-Modus Interval"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Gießplan-Formular ist geöffnet, Modus „Intervall".

**Test Steps**:
1. Nutzer wählt Modus: „Intervall".
2. Nutzer gibt Intervall „3" Tage ein.
3. Nutzer klickt „Speichern".

**Expected Results**:
- Plan wird gespeichert.
- Detailseite zeigt „alle 3 Tage".

**Postconditions**:
- Gießplan-Konfiguration ist gespeichert.

**Tags**: [REQ-004, watering-schedule, interval]

---

## TC-004-058: Gießplan Intervall — Grenzwert 0 abgelehnt

**Requirement**: REQ-004 §3 (WateringSchedule: interval_days ≥ 1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Gießplan-Formular ist geöffnet, Modus „Intervall".

**Test Steps**:
1. Nutzer gibt Intervall „0" Tage ein.
2. Nutzer klickt „Speichern".

**Expected Results**:
- Fehlermeldung: „Intervall muss mindestens 1 Tag betragen."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, watering-schedule, interval, validation, boundary]

---

## TC-004-059: Gießplan Intervall — Grenzwert 90 akzeptiert, 91 abgelehnt

**Requirement**: REQ-004 §3 (WateringSchedule: interval_days ≤ 90)
**Priority**: Medium
**Category**: Formvalidierung / Grenzwert
**Preconditions**:
- Gießplan-Formular ist geöffnet, Modus „Intervall".

**Test Steps**:
1. Nutzer gibt Intervall „90" ein → Speichern → erwartet Erfolg.
2. Nutzer ändert Intervall auf „91" → Speichern → erwartet Fehler.

**Expected Results**:
- Intervall 90: Erfolgreich gespeichert.
- Intervall 91: Fehlermeldung „Intervall darf maximal 90 Tage betragen."

**Postconditions**:
- Gießplan mit 90 Tagen ist gespeichert (nach Schritt 1).

**Tags**: [REQ-004, watering-schedule, interval, boundary-90]

---

## TC-004-060: Fertigation in Plan-Level WateringSchedule abgelehnt

**Requirement**: REQ-004 §3 (WateringSchedule: application_method ≠ fertigation)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Gießplan-Formular auf Plan-Ebene ist geöffnet.

**Test Steps**:
1. Nutzer wählt Applikationsmethode „Fertigation" im Plan-Level-Gießplan.
2. Nutzer klickt „Speichern".

**Expected Results**:
- Fehlermeldung: „Fertigation ist nicht als manuelle Gießplan-Methode zulässig. Tank-basierte Bewässerung wird über REQ-014 Tankmanagement gesteuert."
- Oder: Die Option „Fertigation" ist im Dropdown nicht verfügbar (deaktiviert).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, watering-schedule, fertigation-excluded, validation]

---

## Gruppe J — Gantt-Diagramm (FertilizerGanttChart)

---

## TC-004-061: Gantt-Diagramm-Tab öffnen

**Requirement**: REQ-004 §1 (Gantt-Diagramm-Visualisierung), §7 DoD „Gantt-Diagramm"
**Priority**: High
**Category**: Happy Path / Detailansicht
**Preconditions**:
- Plan „Tomato Heavy Coco" mit 4 Phase-Entries (Seedling W1–2, Vegetative W3–6, Flowering W7–12, Harvest W13–14) ist vorhanden.
- Jede Phase hat mindestens einen Dünger zugewiesen.

**Test Steps**:
1. Nutzer öffnet NutrientPlanDetailPage von „Tomato Heavy Coco".
2. Nutzer klickt auf Tab „Zeitplan" (oder togglet auf Gantt-Ansicht).

**Expected Results**:
- Gantt-Diagramm wird geladen (lazy/React.lazy — kurzer Ladeindikator ist akzeptabel).
- X-Achse zeigt Wochen 1–14.
- Phasen-Header-Zeile zeigt 4 farbige Balken:
  - Seedling W1–2 (hellgrün)
  - Vegetative W3–6 (blau)
  - Flowering W7–12 (lila)
  - Harvest W13–14 (orange)
- Y-Achse listet alle verwendeten Dünger.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, overview, tabs]

---

## TC-004-062: Gantt-Dünger-Zeilen und Dosierungsbeschriftung

**Requirement**: REQ-004 §1 (Gantt-Dünger-Zeilen), §7 DoD „Gantt-Dünger-Zeilen"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Plan „Tomato Heavy Coco" mit CalMag in Seedling, Vegetative und Flowering ist geöffnet.
- PK 13-14 ist als optional=true für Flowering eingetragen.

**Test Steps**:
1. Nutzer öffnet Tab „Zeitplan".

**Expected Results**:
- CalMag-Zeile: 3 zusammenhängende Balken (W1–2, W3–6, W7–12).
- Auf jedem Balken ist die Dosierung in ml/L beschriftet (z. B. „1.0 ml/L", „1.5 ml/L", „1.0 ml/L").
- PK 13-14-Zeile: 1 gestrichelter Balken (W7–12, optional).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, fertilizer-rows, dosage-labels]

---

## TC-004-063: Gantt-Hover-Tooltip — Phasen-Details

**Requirement**: REQ-004 §1 (Gantt-Hover-Tooltip), §7 Szenario 11
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Gantt-Diagramm von „Tomato Heavy Coco" ist geöffnet.
- Flowering-Phase: EC 1.8 mS, pH 6.0, NPK 1-3-3, Dünger: CalMag (1 ml/L), FloraBloom (3 ml/L), PK 13-14 (0.5 ml/L, optional).

**Test Steps**:
1. Nutzer fährt mit der Maus über den Flowering-Phasen-Header-Balken (Woche 7–12).

**Expected Results**:
- Tooltip erscheint und zeigt:
  - Phasenname: „Blüte (Flowering)" + Wochenzeitraum: „Woche 7–12"
  - Zielwerte: EC 1.8 mS, pH 6.0, NPK 1-3-3
  - Düngertabelle: CalMag 1 ml/L, FloraBloom 3 ml/L, PK 13-14 0.5 ml/L (optional)
  - EC-Budget-Status (✓ gültig oder ✗ Abweichung)

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, hover-tooltip, phase-details]

---

## TC-004-064: Gantt-Lücken-Erkennung

**Requirement**: REQ-004 §1 (Gantt-Lücken-Erkennung), §7 DoD „Gantt-Lücken-Erkennung"
**Priority**: Medium
**Category**: Detailansicht / Fehlermeldung
**Preconditions**:
- Plan hat Phase-Entries: Seedling W1–2, Vegetative W4–6 (Lücke in Woche 3!).

**Test Steps**:
1. Nutzer öffnet Tab „Zeitplan".

**Expected Results**:
- Woche 3 erscheint als leere Spalte mit grauem Hintergrund.
- Die Lücke ist visuell klar von belegten Wochen unterscheidbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, gap-detection]

---

## TC-004-065: Gantt-Überlappung — Warnung

**Requirement**: REQ-004 §1 (Gantt-Überlappung), §7 DoD „Gantt-Überlappung"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Plan hat Phase-Entries: Vegetative W3–7, Flowering W5–12 (Wochen 5–7 überlappen!).

**Test Steps**:
1. Nutzer öffnet Tab „Zeitplan".

**Expected Results**:
- Die überlappenden Balken werden als gestapelt oder farblich überlagert dargestellt.
- Ein roter Rahmen oder Warnhinweis ist sichtbar für die Überlappungswochen.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, overlap, warning]

---

## TC-004-066: Gantt-Modus A — Einjähriger Plan

**Requirement**: REQ-004 §1 (Gantt Modus A), §7 DoD „Gantt-Modus-A (Einjährig)"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Plan hat `cycle_restart_from_sequence = null` (linearer Plan).

**Test Steps**:
1. Nutzer öffnet Tab „Zeitplan".

**Expected Results**:
- X-Achse zeigt einen linearen Zeitstrahl (kein Zyklusindikator, kein ↻-Symbol).
- Der Zeitstrahl endet nach der letzten Phase — kein Wrap-Around.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, mode-a, annual]

---

## TC-004-067: Gantt-Modus B — Saisonaler Zyklus (perennial)

**Requirement**: REQ-004 §1 (Gantt Modus B), §7 DoD „Gantt-Modus-B (Saisonal)"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Plan hat `cycle_restart_from_sequence = 3` (Zyklusstart bei Phase-Entry mit sequence_order=3).
- Plan hat 4 Phasen: 1=Bewurzelung (W1–4), 2=Juvenil (W5–8), 3=Vegetativ (W9–20), 4=Dormanz (W21–28).

**Test Steps**:
1. Nutzer öffnet Tab „Zeitplan".

**Expected Results**:
- Eine gestrichelte vertikale Linie (Zyklus-Grenze) erscheint zwischen Phase 2 (Juvenil) und Phase 3 (Vegetativ).
- Linker Bereich (W1–8, Setup-Phasen): normaler Hintergrund.
- Rechter Bereich (W9–28, wiederkehrende Phasen): dezenter Hintergrund + ↻-Symbol im Phasen-Header.
- Am rechten Rand: „↻ Zyklus wiederholt ab Phase Vegetativ".

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, gantt, mode-b, perennial, cycle]

---

## Gruppe K — Multi-Channel Delivery (DeliveryChannelAccordion, DeliveryChannelDialog)

---

## TC-004-068: Channel hinzufügen — Happy Path (Fertigation)

**Requirement**: REQ-004 §4.2 (DeliveryChannel), §7 DoD „UI Channel-Dialog"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Phase-Entry „Vegetative" eines Plans ist geöffnet.
- Nutzer hat Expert-Erfahrungsstufe (REQ-021).

**Test Steps**:
1. Nutzer scrollt zum Abschnitt „Ausbringungskanäle" und klickt „+ Channel hinzufügen".
2. Im ChannelCreateDialog (Schritt 1 — Methode): Nutzer wählt „Fertigation (Tank/Tropfer)".
3. (Schritt 2 — Parameter): runs_per_day = 3, duration_minutes = 10.
4. (Schritt 3 — Zeitplan): Modus Intervall, 1 Tag.
5. (Schritt 4 — Dünger): FloraGro 2.0 ml/L hinzufügen.
6. Nutzer klickt „Fertig".

**Expected Results**:
- Neuer Channel-Chip erscheint unterhalb der Phase-Zielwerte.
- Chip zeigt: Fertigation-Icon + Label + „3x/Tag".
- Im expandierten Accordion ist der Channel mit allen Parametern sichtbar.

**Postconditions**:
- Channel „Fertigation" ist der Phase-Entry zugeordnet.

**Tags**: [REQ-004, delivery-channel, create, fertigation, expert]

---

## TC-004-069: Channel für Beginner-Nutzer ausgeblendet

**Requirement**: REQ-004 §4.8 (Erfahrungsstufen: Multi-Channel ausgeblendet bei Beginner)
**Priority**: High
**Category**: Navigation / Zustandswechsel
**Preconditions**:
- Nutzer hat Erfahrungsstufe „Einsteiger" (Beginner).

**Test Steps**:
1. Nutzer öffnet Phase-Entry-Bearbeitungsformular.
2. Nutzer sucht den Abschnitt „Ausbringungskanäle".

**Expected Results**:
- Der Abschnitt „Ausbringungskanäle" ist **nicht sichtbar**.
- Nur die Legacy-Felder (Gießfrequenz, Volumen pro Gießvorgang) sind sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, delivery-channel, beginner, hidden, expertise-level]

---

## TC-004-070: Tank-Safe-Validierung bei Fertigation-Channel (MCD-V01)

**Requirement**: REQ-004 §4.3 (MCD-V01: Tank-Safe-Prüfung)
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Phase-Entry hat einen Fertigation-Channel.
- Düngemittel „Komposttee" hat `tank_safe = false`.

**Test Steps**:
1. Nutzer versucht im Fertigation-Channel das Düngemittel „Komposttee" hinzuzufügen.

**Expected Results**:
- Fehlermeldung (CRITICAL): „Komposttee ist nicht tanksicher. Organische Feststoffe/Schwebstoffe verstopfen Tropfer und verursachen Biofilm im Tank."
- Das Düngemittel wird nicht dem Fertigation-Channel zugewiesen.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, delivery-channel, tank-safe, validation, mcd-v01]

---

## TC-004-071: EC-Limit auf Foliar-Channel — Warnung bei > 1.0 mS (MCD-V04)

**Requirement**: REQ-004 §4.3 (MCD-V04: Foliar EC-Limit)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Phase-Entry hat einen Foliar-Channel.

**Test Steps**:
1. Nutzer gibt für den Foliar-Channel ein target_ec von 1.5 mS ein.

**Expected Results**:
- Hinweis (INFO/WARNING): „Foliar-Lösungen über 1.0 mS können Blattverbrennungen verursachen."
- Speichern bleibt möglich (kein Hardblock).

**Postconditions**:
- Channel ist mit Warnung speicherbar.

**Tags**: [REQ-004, delivery-channel, foliar, ec-limit, mcd-v04]

---

## TC-004-072: Channel-ID Duplikat abgelehnt (MCD-V08)

**Requirement**: REQ-004 §4.3 (MCD-V08: channel_id eindeutig)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Phase-Entry hat bereits einen Channel mit channel_id „dripper-base".

**Test Steps**:
1. Nutzer versucht einen zweiten Channel mit channel_id „dripper-base" zu erstellen.
2. Nutzer klickt „Fertig".

**Expected Results**:
- Fehlermeldung: „Channel-ID ‚dripper-base' wird bereits in dieser Phase-Entry verwendet."
- Channel wird nicht gespeichert.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, delivery-channel, channel-id, duplicate, mcd-v08]

---

## TC-004-073: Maximum 10 Channels pro Phase-Entry (MCD-V12)

**Requirement**: REQ-004 §4.3 (MCD-V12: max 10 Channels)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Phase-Entry hat bereits 10 Channels.

**Test Steps**:
1. Nutzer versucht einen 11. Channel hinzuzufügen.

**Expected Results**:
- Button „+ Channel hinzufügen" ist deaktiviert oder eine Fehlermeldung erscheint: „Maximal 10 Channels pro Phase erlaubt."

**Postconditions**:
- Kein 11. Channel wurde erstellt.

**Tags**: [REQ-004, delivery-channel, max-channels, mcd-v12]

---

## TC-004-074: Cross-Channel Dünger-Duplikat Warnung (MCD-V20)

**Requirement**: REQ-004 §4.3 (MCD-V20: Dünger-Duplikat-Warnung)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Phase-Entry hat zwei Channels.
- Düngemittel „FloraGro" ist in beiden Channels zugewiesen.

**Test Steps**:
1. Nutzer klickt „Plan validieren" (oder die Validierung erfolgt automatisch beim Speichern).

**Expected Results**:
- Warnung: „FloraGro ist in 2 Channels zugewiesen — Gesamt-EC-Beitrag prüfen."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, delivery-channel, cross-channel, duplicate, mcd-v20]

---

## TC-004-075: Fertigation-Channel zu Plan-Level konvertieren (Legacy-Toggle)

**Requirement**: REQ-004 §4.8 (Legacy-Toggle: „Zu Multi-Channel konvertieren")
**Priority**: Medium
**Category**: Happy Path / Zustandswechsel
**Preconditions**:
- Phase-Entry hat `delivery_channels = []` (Legacy-Modus).
- Legacy-Felder (Frequenz, Volumen, Dünger) sind gesetzt.

**Test Steps**:
1. Nutzer öffnet die Phase-Entry.
2. Nutzer klickt „Zu Multi-Channel konvertieren".
3. Nutzer bestätigt den Dialog.

**Expected Results**:
- Erfolgsmeldung erscheint.
- Ein synthetischer Channel (Methode: Drench, Label: „Standard") mit den Legacy-Düngern wurde erstellt.
- Der neue Channel ist im Accordion sichtbar.
- Die Legacy-Felder sind nun ausgegraut/deaktiviert mit Hinweis „Channel-Modus aktiv".

**Postconditions**:
- Phase-Entry ist im Multi-Channel-Modus.

**Tags**: [REQ-004, delivery-channel, legacy-migration, convert]

---

## Gruppe L — EC-Budget-Kalkulation (REQ-004-A)

---

## TC-004-076: Wassermischung berechnen — Vorwärtsrechnung

**Requirement**: REQ-004-A §3.2 (EC_mix = EC_ro × r/100 + EC_tap × (1 − r/100))
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- NutrientSolutionCalculator oder dedizierter WaterMix-Bereich ist geöffnet.
- Leitungswasser EC 0.50 mS, Osmosewasser EC 0.02 mS.

**Test Steps**:
1. Nutzer gibt ein: EC_tap = 0.50 mS, EC_ro = 0.02 mS, Osmose-Anteil r = 70%.
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Berechnetes Mischwasser-EC: 0.164 mS (0.02 × 0.7 + 0.50 × 0.3 = 0.164).
- V_ro = X × 0.7 Liter Osmosewasser, V_tap = X × 0.3 Liter Leitungswasser werden angezeigt.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, water-mix, forward-calculation]

---

## TC-004-077: Osmose-Anteil berechnen — Rückwärtsrechnung

**Requirement**: REQ-004-A §3.3 (r = (EC_tap − EC_mix) / (EC_tap − EC_ro) × 100)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- WaterMix-Bereich mit Rückwärtsrechnung ist verfügbar.

**Test Steps**:
1. Nutzer gibt ein: EC_tap = 0.80 mS, EC_ro = 0.02 mS, gewünschter EC_mix = 0.20 mS.
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Berechneter Osmose-Anteil: 76.9% (= (0.80 − 0.20) / (0.80 − 0.02) × 100).
- Mischwasser: „76.9% Osmosewasser, 23.1% Leitungswasser".

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, water-mix, backward-calculation]

---

## TC-004-078: Osmose-Ziel physikalisch unerreichbar

**Requirement**: REQ-004-A §3.3 (Randbedingung: EC_mix < EC_ro → Fehler) / §9.3
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- WaterMix-Bereich ist geöffnet. EC_ro = 0.02 mS.

**Test Steps**:
1. Nutzer gibt gewünschten EC_mix = 0.01 mS ein (< EC_ro = 0.02 mS).
2. Nutzer klickt „Berechnen".

**Expected Results**:
- Fehlermeldung: „Gewünschter Basis-EC (0.01 mS) ist niedriger als der EC des Osmosewassers (0.02 mS). Ziel ist physikalisch nicht erreichbar."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, water-mix, unreachable-target, error]

---

## TC-004-079: Temperaturkorrektur EC@25 anzeigen

**Requirement**: REQ-004-A §4.4 (EC-Temperaturkorrektur)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- FeedingEvent-Erfassungsformular oder TankState-Formular hat ein optionales Temperaturfeld.

**Test Steps**:
1. Nutzer gibt EC-Wert 1.72 mS und Wassertemperatur 18°C ein.

**Expected Results**:
- Das System zeigt den korrigierten EC@25: 2.00 mS.
- Hinweis: „EC-Wert wurde auf 25°C normiert (gemessen bei 18°C)."
- Der normierte Wert wird für Validierungen verwendet.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, ec-temperature-correction, ec25]

---

## TC-004-080: EC@25 — kein Temperaturwert angegeben (Hinweis)

**Requirement**: REQ-004-A §4.4 (UI-Hinweis wenn keine Temperatur)
**Priority**: Low
**Category**: Fehlermeldung / Hinweis
**Preconditions**:
- FeedingEvent-Formular ist geöffnet, kein Temperaturwert eingetragen.

**Test Steps**:
1. Nutzer gibt EC-Wert ein, lässt Temperatur-Feld leer.
2. Nutzer klickt neben das Temperaturfeld.

**Expected Results**:
- Hinweis (INFO): „EC-Wert wird als EC@25 interpretiert. Falls Ihr Messgerät keine automatische Temperaturkompensation hat, geben Sie die Wassertemperatur an."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, ec-temperature-hint]

---

## TC-004-081: Ca/Mg-Verhältnis zu niedrig — Warnung

**Requirement**: REQ-004-A §3.6 (Ca/Mg-Ratio < 2.0 → WARNING)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Dosierungsrechner berechnet Ca/Mg nach CalMag-Zugabe.

**Test Steps**:
1. Nutzer konfiguriert Mischung so, dass das resultierende Ca/Mg-Verhältnis unter 2.0 liegt (z. B. Ca 30 ppm, Mg 20 ppm = Ratio 1.5).

**Expected Results**:
- Warnung: „Ca/Mg-Verhältnis (1.5:1) zu niedrig — Ca-Aufnahmehemmung möglich. Verwenden Sie ein CalMag-Produkt mit höherem Ca-Anteil."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, calmag, ratio, warning-low]

---

## TC-004-082: Ca/Mg-Verhältnis zu hoch — Warnung

**Requirement**: REQ-004-A §3.6 (Ca/Mg-Ratio > 5.0 → WARNING)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Resultierendes Ca/Mg-Verhältnis > 5.0 (z. B. Ca 300 ppm, Mg 50 ppm = Ratio 6.0).

**Test Steps**:
1. Nutzer konfiguriert Mischung mit sehr hohem Ca-Anteil.

**Expected Results**:
- Warnung: „Ca/Mg-Verhältnis (6.0:1) zu hoch — Mg-Aufnahmehemmung möglich. Reduzieren Sie die CalMag-Dosierung oder ergänzen Sie Magnesium separat."

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, calmag, ratio, warning-high]

---

## TC-004-083: Volles Praxisbeispiel — 50L Nährlösung (REQ-004-A §7)

**Requirement**: REQ-004-A §7 (Praxisbeispiel End-to-End)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Site mit EC_tap = 0.55 mS, Ca = 120 ppm, Mg = 25 ppm.
- Gewünschter Basis-EC 0.15 mS, Zielvolumen 50 L, Ziel-EC 1.80 mS.
- Dünger: CalMag (ec 0.15/ml), Flora Micro (ec 0.10/ml), Flora Gro (ec 0.10/ml), Flora Bloom (ec 0.15/ml).
- Referenz-Rezept: Micro 3:Gro 2:Bloom 1 ml/L.

**Test Steps**:
1. Nutzer öffnet den Dosierungsrechner, wählt die Site.
2. Nutzer startet die Berechnung für Phase „Vegetative".

**Expected Results**:
- Osmose-Anteil: ≈ 75.5%.
- Wasservolumina: ≈ 37.75 L RO + 12.25 L Leitungswasser.
- CalMag-Defizit erkannt (Ca 29.4 ppm < Ziel 150 ppm).
- EC-Budget-Aufteilung wird angezeigt.
- Endgültige Dosierungen: Flora Micro ≈ 6.79 ml/L, Flora Gro ≈ 4.52 ml/L, Flora Bloom ≈ 2.26 ml/L.
- Verhältnis Flora-Serie bleibt 3:2:1 (Proportionen erhalten).
- Finale EC ≈ 1.80 mS (± Toleranz).
- Mischprotokoll zeigt alle 8 Schritte in korrekter Reihenfolge.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004-A, full-calculation, example, proportionality]

---

## Gruppe M — Authentifizierung & Zugriffsschutz

---

## TC-004-084: Düngemittel-CRUD erfordert Authentifizierung

**Requirement**: REQ-004 §5 (Fertilizer: Lesen erfordert Auth)
**Priority**: High
**Category**: Navigation / Zustandswechsel
**Preconditions**:
- Nutzer ist **nicht** eingeloggt.

**Test Steps**:
1. Nutzer ruft direkt die URL `/duengung/duengemittel` auf.

**Expected Results**:
- Nutzer wird zur Login-Seite weitergeleitet.
- Nach Login gelangt der Nutzer zurück zur Düngemittel-Liste.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, auth, access-control, redirect]

---

## TC-004-085: Nährstoffplan nur im eigenen Tenant sichtbar

**Requirement**: REQ-004 §5 (NutrientPlans: Tenant-scoped)
**Priority**: High
**Category**: Zustandswechsel / Navigation
**Preconditions**:
- Nutzer ist in Tenant „Mein Garten" eingeloggt.
- Tenant „Freundes-Garten" hat eigene Nährstoffpläne.

**Test Steps**:
1. Nutzer navigiert zur Nährstoffplan-Liste in Tenant „Mein Garten".

**Expected Results**:
- Nur Nährstoffpläne des Tenants „Mein Garten" sind sichtbar.
- Pläne von „Freundes-Garten" erscheinen nicht in der Liste.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, auth, tenant-scope, multitenancy]

---

## Gruppe N — Tabletten-Layout (Responsive)

---

## TC-004-086: Düngemittel-Liste auf Tablet — Spalten ausgeblendet

**Requirement**: REQ-004 §7 DoD „Tablet-Spaltenprioritäten" (UI-NFR-010 §8.1)
**Priority**: Medium
**Category**: Listenansicht / Responsive
**Preconditions**:
- Browser-Viewport auf Tablet-Breite eingestellt (768–1024 px).

**Test Steps**:
1. Nutzer öffnet die Düngemittel-Liste auf Tablet.

**Expected Results**:
- Spalten „EC-Beitrag pro ml/L" und „Tank-sicher" sind ausgeblendet.
- Primärspalten Produktname, Typ und Hersteller bleiben sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, fertilizer, tablet, responsive, column-priority]

---

## TC-004-087: FeedingEvent-Liste auf Tablet — Notizen ausgeblendet

**Requirement**: REQ-004 §7 DoD „Tablet-Spaltenprioritäten" (UI-NFR-010 §8.1)
**Priority**: Medium
**Category**: Listenansicht / Responsive
**Preconditions**:
- Browser-Viewport auf Tablet-Breite eingestellt.

**Test Steps**:
1. Nutzer öffnet das Düngungsprotokoll auf Tablet.

**Expected Results**:
- Spalte „Notizen" ist ausgeblendet.
- Primärspalten Datum, Pflanze/Run, EC-Ist sind sichtbar.

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, feeding-event, tablet, responsive, column-priority]

---

## TC-004-088: Organische Düngungsempfehlung für Freilandpflanzen

**Requirement**: REQ-004 §1 (Organische Freiland-Düngung), §1 (Abgrenzung Hydro/Freiland)
**Priority**: Medium
**Category**: Detailansicht / Zustandswechsel
**Preconditions**:
- Pflanze „Tomate (Freiland)" wächst in Substrat `soil` oder `raised_bed_mix`.
- Nutzer hat Erfahrungsstufe „Einsteiger" oder „Fortgeschrittener".

**Test Steps**:
1. Nutzer öffnet den Düngungsbereich für die Freiland-Pflanze.

**Expected Results**:
- Die EC/pH-Mischlogik ist **ausgeblendet** (Beginner/Intermediate).
- Stattdessen wird eine vereinfachte Düngungsempfehlung angezeigt:
  - Kompost: 3–4 L/m²
  - Hornspäne: 80 g/m²
  - Jauche alle 2 Wochen (Mai–August)
  - Dies basiert auf `nutrient_demand_level = heavy_feeder` (Tomate ist Starkzehrer).

**Postconditions**:
- Keine Datenmutation.

**Tags**: [REQ-004, outdoor, organic-fertilization, freiland, expertise-level]

---

## Abdeckungs-Übersicht

| Spec-Abschnitt | Beschreibung | Testfälle |
|---|---|---|
| REQ-004 §1 (Business Case) | Mischprotokoll, CalMag, organische Düngung, Foliar-Warnung | TC-004-028 bis TC-004-033, TC-004-049 bis TC-004-051, TC-004-088 |
| REQ-004 §3 (Fertilizer-CRUD) | Erstellen, Filtern, Lagerbestand, Reverse Lookup | TC-004-001 bis TC-004-011 |
| REQ-004 §3 (NutrientPlan-CRUD) | Plan, Phase-Entry, Dünger-Zuweisung, Klonen, Zuweisung | TC-004-012 bis TC-004-027 |
| REQ-004 §3 (WateringSchedule) | Wochentage/Intervall, Validierungen | TC-004-055 bis TC-004-060 |
| REQ-004 §4 (Multi-Channel Delivery) | Channel-CRUD, Validierungsregeln MCD-V01–V22 | TC-004-068 bis TC-004-075 |
| REQ-004 §4b (Normalisierte Referenzdosierung) | Dosierungsrechner-Tab, Proportionen, Quell-Feld | TC-004-038 bis TC-004-042 |
| REQ-004 §5 (Auth & Tenant-Scope) | Zugriffsschutz, Tenant-Isolation | TC-004-084 bis TC-004-085 |
| REQ-004 §7 (DoD & Szenarien) | Alle DoD-Punkte abgedeckt, 11 Szenarien | Verteilt auf alle Gruppen |
| REQ-004-A §3 (Wassermischung) | Vorwärts-/Rückwärtsrechnung, pH-Mischung, CalMag | TC-004-034 bis TC-004-037, TC-004-076 bis TC-004-082 |
| REQ-004-A §4 (EC-Budget) | EC-Obergrenze, Temperaturkorrektur, Salzakkumulation | TC-004-029 bis TC-004-030, TC-004-079 bis TC-004-080 |
| REQ-004-A §5 (Dosier-Sicherheit) | Sicherheitslimits, Sonderfälle | TC-004-033 |
| REQ-004-A §7 (Praxisbeispiel) | End-to-End Vollständige Berechnung | TC-004-083 |
| Gantt-Diagramm | Modus A/B, Tooltip, Lücken, Überlappungen | TC-004-061 bis TC-004-067 |
| Runoff-Analyse | SALT_BUILDUP, TOO_LOW, OK | TC-004-045 bis TC-004-047 |
| Flushing-Protokoll | Coco/Hydro/Soil, TOO_LATE | TC-004-043 bis TC-004-044 |
| FeedingEvent | Erfassung, Foliar-Warnung, Filter, Export | TC-004-048 bis TC-004-054 |
| Responsive (Tablet) | Spaltenpriorisierung | TC-004-086 bis TC-004-087 |
