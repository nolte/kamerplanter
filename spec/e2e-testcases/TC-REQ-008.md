---
req_id: REQ-008
title: "Post-Harvest: Veredelung, Fermentierung & Lagerreife"
category: Post-Harvest
test_count: 68
coverage_areas:
  - Batch-Statusmaschine (fresh → drying → curing → aging → stored → consumed/disposed)
  - Trocknungs-Dashboard (Fortschrittsbalken, Gewichts-Tracking, Snap-Test)
  - Jar-Curing & Burping-Assistent (Cannabis)
  - Schimmel-Praeventions-Dashboard (RH-Monitoring, Mold-Alert-Anzeige)
  - Lager-Inventar (StorageLocation, Haltbarkeits-Prognose)
  - Trim-Protokoll-Erfassung (wet/dry/machine trim, Gewichte)
  - Qualitaetsbewertung & Beobachtungen (StorageObservation)
  - Spezies-spezifische Protokoll-Guides (Cannabis, Zwiebel, Kartoffel, Chili, Pilze)
  - CO2-Ueberwachung (U-005)
  - UV/Licht-Degradations-Hinweise (U-008)
  - Anbausystem-Modifier-Hinweise (U-002)
  - Karenz-Gate (REQ-010-Verknuepfung)
  - Stoerfall-Protokolle (Schimmel-Fund, Uebertrocknungs-Warnung, Notfallmasnahmen)
  - Authentifizierung & Tenant-Scoping
generated: 2026-03-21
version: "2.2"
---

# TC-REQ-008: Post-Harvest — Veredelung, Fermentierung & Lagerreife

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-008 Post-Harvest v2.2**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-008 setzt REQ-007 (Ernte) voraus: Post-Harvest beginnt mit einem Batch, der aus einer abgeschlossenen Ernte stammt. Der Karenz-Gate aus REQ-010 (IPM) muss bestanden sein, bevor ein Batch in Post-Harvest uebergehen darf.

---

## 1. Batch-Statusmaschine (Zustandsuebersicht)

### TC-REQ-008-001: Batch-Status "fresh" nach Ernte-Abschluss anzeigen

**Requirement**: REQ-008 § 5 (Abh. REQ-007), § 6 DoD (Batch-Status-Machine U-006)
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt und Mitglied eines Tenants
- Ein HarvestBatch wurde ueber REQ-007 erstellt und hat Status `fresh`
- Kein offener Karenz-Verstoss (REQ-010) fuer diese Pflanze

**Testschritte**:
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf den Batch in der Listentabelle

**Erwartete Ergebnisse**:
- Die Batch-Detailseite oeffnet sich
- Ein Status-Badge zeigt "Frisch" (oder vergleichbarer Label fuer `fresh`)
- Die verfuegbaren Aktionen enthalten eine Schaltflaeche "Trocknung starten"
- Die Schaltflaeche "Curing starten" ist nicht aktiv oder nicht sichtbar (da der Schritt Trocknung noch aussteht)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-008, batch-status, fresh, statusmaschine, u-006, ernte-uebergang]

---

### TC-REQ-008-002: Batch-Statusuebergang von "fresh" zu "drying" ausloesen

**Requirement**: REQ-008 § 6 DoD (Batch-Status-Machine U-006), § 5 Abh. REQ-010
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Batch ist im Status `fresh`
- Karenz-Gate (REQ-010): letzte chemische Behandlung liegt laenger zurueck als die gesetzlich vorgeschriebene Karenzzeit

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite
2. Nutzer klickt auf "Trocknung starten"
3. Ein Dialog erscheint mit Trocknungsparametern (Methode, Lagerort, Startgewicht)
4. Nutzer waehlt Methode "Haengetrocknung" aus der Dropdown-Liste
5. Nutzer gibt Startgewicht "450" g ein
6. Nutzer waehlt einen bestehenden Lagerort "Trocknungsraum" aus
7. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich
- Das Status-Badge des Batches wechselt zu "In Trocknung" (`drying`)
- Ein Fortschrittsbereich "Trocknungs-Fortschritt" wird auf der Seite sichtbar
- Das Startgewicht (450 g) ist im Trocknungs-Tracking gespeichert und wird angezeigt
- Eine Erfolgsbenachrichtigung erscheint: "Trocknung gestartet"

**Nachbedingungen**:
- Batch-Status ist `drying`
- DryingProgress-Eintrag ist angelegt

**Tags**: [req-008, batch-status, drying, statusmaschine, u-006, trocknung-start]

---

### TC-REQ-008-003: Karenz-Gate blockiert Batch-Uebergang in Post-Harvest

**Requirement**: REQ-008 § 5 Abh. REQ-010 (Karenz-Gate), § 6 DoD
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Batch ist im Status `fresh`
- Eine chemische Behandlung (REQ-010) liegt weniger als die vorgeschriebene Karenzzeit zurueck
- Das System hat einen aktiven Karenz-Verstoss fuer diesen Batch

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite
2. Nutzer klickt auf "Trocknung starten"

**Erwartete Ergebnisse**:
- Es erscheint entweder ein Warndialog oder die Schaltflaeche "Trocknung starten" ist deaktiviert
- Falls Dialog: Meldung erklaert, dass die Karenzzeit noch nicht abgelaufen ist, und zeigt das erwartete Freigabedatum an
- Falls deaktivierte Schaltflaeche: Ein Tooltip oder Hinweistext erklaert die Sperrung (z.B. "Karenzzeit laeuft ab am: TT.MM.JJJJ")
- Der Batch verbleibt im Status `fresh`

**Nachbedingungen**:
- Batch-Status unveraendert (`fresh`)

**Tags**: [req-008, karenz-gate, req-010, blockierung, sicherheit, post-harvest]

---

### TC-REQ-008-004: Alle Batch-Statusuebergaenge sequenziell durchlaufen

**Requirement**: REQ-008 § 6 DoD (Batch-Status-Machine U-006)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Batch ist im Status `fresh`
- Kein Karenz-Verstoss

**Testschritte**:
1. Nutzer startet Trocknung → Status wechselt zu `drying`
2. Nach Abschluss der Trocknung: Nutzer klickt "Curing starten" → Status wechselt zu `curing`
3. Nutzer klickt (optional) "Reifung starten" → Status wechselt zu `aging`
4. Nutzer klickt "In Lager einlagern" → Status wechselt zu `stored`
5. Nutzer klickt "Als verbraucht markieren" → Status wechselt zu `consumed`

**Erwartete Ergebnisse**:
- Jeder Schritt zeigt das korrekte Status-Badge
- Die jeweils naechste verfuegbare Aktion wird nach jedem Uebergang angezeigt
- Rueckwaertsuebergaenge (z.B. von `curing` zurueck zu `fresh`) sind nicht moeglich — entsprechende Schaltflaechen fehlen oder sind deaktiviert

**Nachbedingungen**:
- Batch-Status ist `consumed`

**Tags**: [req-008, batch-status, statusmaschine, u-006, alle-zustaende, sequenz]

---

### TC-REQ-008-005: Batch als "entsorgt" markieren mit Begruendungseingabe

**Requirement**: REQ-008 § 6 DoD (Batch-Status-Machine U-006), Schimmel-Notfallprotokoll
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Batch befindet sich in einem aktiven Status (z.B. `drying` oder `curing`)

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite
2. Nutzer klickt auf "Entsorgen"
3. Ein Bestaedigungsdialog oeffnet sich
4. Nutzer gibt eine Begruendung ein: "Schimmel entdeckt — Botrytis"
5. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich
- Status-Badge wechselt zu "Entsorgt" (`disposed`)
- Begruendung wird im Batch-Verlauf oder einer Notiz gespeichert und ist sichtbar
- Alle Aktions-Schaltflaechen ausser "Zurueck zur Liste" sind deaktiviert

**Nachbedingungen**:
- Batch-Status ist `disposed`

**Tags**: [req-008, batch-status, disposed, schimmel-notfall, u-006]

---

## 2. Trocknungs-Dashboard & Gewichts-Tracking

### TC-REQ-008-006: Trocknungs-Fortschrittsbalken nach Gewichtseingabe aktualisieren

**Requirement**: REQ-008 § 6 DoD (Gewichts-Tracking, Dryness-Progress-Tracking)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `drying`
- Startgewicht: 450 g, Zielgewicht: 90 g (80% Verlust = 10% Restfeuchte)

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Trocknung"
2. Nutzer sieht den Fortschrittsbalken mit aktuellem Stand
3. Nutzer klickt auf "Gewicht erfassen"
4. Nutzer gibt aktuelles Gewicht "180" g ein
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Fortschrittsbalken zeigt ca. 73% Trocknungsfortschritt (berechnet aus 450 → 180 g)
- Anzeige "Geschaetzte verbleibende Tage: 2"
- Ein Hinweis erscheint: "Snap-Test jetzt empfohlen" (da Fortschritt ≥70%)
- Der Gewichtsverlauf aktualisiert sich in der Tabelle (neue Zeile: Datum + 180 g)
- Eine Erfolgsbenachrichtigung erscheint: "Gewicht gespeichert"

**Nachbedingungen**:
- Neuer Gewichtseintrag im Trocknungs-Tracking sichtbar

**Tags**: [req-008, trocknungs-tracking, gewicht, fortschrittsbalken, szenario-1]

---

### TC-REQ-008-007: Snap-Test-Ergebnis als "optimal" erfassen und Empfehlung anzeigen

**Requirement**: REQ-008 § 6 DoD (Snap-Test-Assistent P-002), Szenario 5
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `drying`, Fortschritt ≥70%
- Der Hinweis "Snap-Test empfohlen" ist sichtbar

**Testschritte**:
1. Nutzer klickt auf "Snap-Test erfassen"
2. Ein Dialog mit zwei Optionen oeffnet sich: "Zweig bricht sauber" (Checkbox), "Zweig splittert" (Checkbox)
3. Nutzer aktiviert "Zweig bricht sauber" und laesst "Zweig splittert" deaktiviert
4. Nutzer klickt "Test speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Im Trocknungs-Bereich wird "Snap-Test: OPTIMAL" angezeigt
- Empfehlung erscheint: "Perfekt getrocknet — Bereit fuer Curing. In Jars umfuellen und mit Curing beginnen."
- Feuchtigkeitsschaetzung wird angezeigt: "10–12%"
- Die Schaltflaeche "Curing starten" wird aktiv oder hervorgehoben

**Nachbedingungen**:
- Snap-Test-Ergebnis `OPTIMAL` ist gespeichert

**Tags**: [req-008, snap-test, optimal, p-002, curing-bereit, trocknungs-assistent]

---

### TC-REQ-008-008: Snap-Test-Ergebnis "OVERDRIED" erfassen und Notfallempfehlung anzeigen

**Requirement**: REQ-008 § 6 DoD (Snap-Test-Assistent P-002), Szenario 5
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Batch ist im Status `drying`, Fortschritt ≥70%

**Testschritte**:
1. Nutzer klickt auf "Snap-Test erfassen"
2. Dialog oeffnet sich
3. Nutzer aktiviert sowohl "Zweig bricht sauber" als auch "Zweig splittert"
4. Nutzer klickt "Test speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Status-Anzeige: "Snap-Test: UEBERTROCKNOT" (OVERDRIED)
- Warnmeldung erscheint: "Zu trocken — Rehydrierung noetig"
- Empfehlung: "Boveda 62% Pack fuer 24h in Jar, dann neu testen"
- Feuchtigkeitsschaetzung: "<8%"

**Nachbedingungen**:
- Snap-Test-Ergebnis `OVERDRIED` gespeichert

**Tags**: [req-008, snap-test, overdried, p-002, uebertrocknung, boveda-empfehlung]

---

### TC-REQ-008-009: Snap-Test-Ergebnis "UNDERDRIED" und Weiter-Trocknen-Empfehlung

**Requirement**: REQ-008 § 6 DoD (Snap-Test-Assistent P-002)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Batch ist im Status `drying`, Fortschritt ≥70%

**Testschritte**:
1. Nutzer klickt auf "Snap-Test erfassen"
2. Dialog oeffnet sich
3. Nutzer laesst beide Checkboxen deaktiviert (Zweig biegt sich nur)
4. Nutzer klickt "Test speichern"

**Erwartete Ergebnisse**:
- Status-Anzeige: "Snap-Test: NOCH FEUCHT" (UNDERDRIED)
- Empfehlung: "Noch zu feucht — Weiter trocknen. Noch 2–3 Tage haengen lassen, dann neu testen."
- Feuchtigkeitsschaetzung: ">15%"
- "Curing starten" bleibt deaktiviert

**Nachbedingungen**:
- Snap-Test-Ergebnis `UNDERDRIED` gespeichert

**Tags**: [req-008, snap-test, underdried, p-002, noch-feucht]

---

### TC-REQ-008-010: Gewichts-Tracking-Verlauf als Tabelle oder Chart anzeigen

**Requirement**: REQ-008 § 6 DoD (Gewichts-Tracking taeglich in ersten 7 Tagen)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Batch ist im Status `drying`
- Mehrere Gewichtsmessungen wurden ueber mehrere Tage erfasst (z.B. Tag 0: 450g, Tag 3: 320g, Tag 7: 180g)

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Trocknung"
2. Nutzer scrollt zum Abschnitt "Gewichtsverlauf"

**Erwartete Ergebnisse**:
- Eine Tabelle oder ein Liniendiagramm zeigt den zeitlichen Gewichtsverlauf
- Jede Zeile/Datenpunkt enthaelt: Datum, Gewicht in g, berechneter Gewichtsverlust in %
- Der neueste Eintrag steht oben oder ist hervorgehoben
- Der Trocknungsfortschritt in % ist deutlich sichtbar

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, gewichtsverlauf, trocknungs-tracking, chart, verlauf]

---

### TC-REQ-008-011: Uebertrocknung-Warnung bei >85% Gewichtsverlust

**Requirement**: REQ-008 § 3 DryingProtocol.calculate_dryness_progress (over_dried bei >85%)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Batch ist im Status `drying`
- Startgewicht: 450 g

**Testschritte**:
1. Nutzer klickt auf "Gewicht erfassen"
2. Nutzer gibt aktuelles Gewicht "60" g ein (entspricht 86.7% Gewichtsverlust)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fortschrittsbereich zeigt roten Warnhinweis: "WARNUNG: Uebertrocknot — Sofort in Jars mit Boveda-Pack (62%)"
- Gewichtsverlust-Prozentsatz wird als kritisch markiert (z.B. roter Text oder Icon)
- Die Empfehlung "Boveda 62% Pack" ist gut sichtbar hervorgehoben

**Nachbedingungen**:
- Warnung persistiert bis eine Gegenmassnahme eingeleitet wird

**Tags**: [req-008, uebertrocknung, over-dried, warnung, boveda]

---

### TC-REQ-008-012: Spezies-spezifische Trocknungsparameter im Guide anzeigen (Cannabis)

**Requirement**: REQ-008 § 6 DoD (Spezies-spezifische Guides, Pilz-Differenzierung), § 3 SpeciesSpecificDrying
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu einem Pflanzen-Run mit Spezies "Cannabis sativa"
- Batch ist im Status `drying`

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Trocknung"
2. Nutzer scrollt zum Abschnitt "Protokoll / Guide" oder klickt auf "Trocknungs-Hinweise anzeigen"

**Erwartete Ergebnisse**:
- Der Guide zeigt spezifische Parameter fuer Cannabis: Temperatur 15–21°C, Luftfeuchte 45–55%
- Empfohlene Methode: "Haengetrocknung (hang_dry)"
- Dauer: 7–14 Tage
- Hinweise: "Langsame Trocknung = besseres Aroma", "Nie ueber 25°C (Terpen-Verlust)", "Dunkelheit (UV degradiert THC)", "Luftzirkulation ohne direkten Wind"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, species-guide, cannabis, trocknungsparameter, uv-schutz, u-008]

---

### TC-REQ-008-013: Spezies-spezifischer Guide fuer Speisepilze zeigt Temperatur-Differenzierung

**Requirement**: REQ-008 § 6 DoD (Pilz-Differenzierung), § 3 SpeciesSpecificDrying (Agaricus bisporus)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu Spezies "Agaricus bisporus" (Champignon)
- Batch ist im Status `drying`

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Trocknung"
2. Nutzer betrachtet den Trocknungs-Guide

**Erwartete Ergebnisse**:
- Empfohlene Temperatur: 45–55°C
- Empfohlene Methode: Doerrgerat (dehydrator)
- Kritischer Hinweis: "Speisepilze vertragen 45–55°C — NICHT ueber 60°C (Aromaverlust und Texturschaeden)"
- Hinweis auf empfindliche Pilze (Psilocybe, Loewenmaehne): "max. 40°C verwenden (Wirkstoffverlust bei hoeheren Temperaturen)"
- Zielfeuchte: "cracker-dry (a_w < 0.30)"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, pilz-differenzierung, speisepilze, dehydrator, agaricus, heilpilze, temperatur-kritisch]

---

### TC-REQ-008-014: Anbausystem-Modifier-Hinweis fuer Hydro-Batch anzeigen

**Requirement**: REQ-008 § 6 DoD (Anbausystem-Modifier U-002), § 3 GrowingSystemModifier
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Batch stammt aus einem Planting-Run mit Anbausystem "hydro"
- Batch ist im Status `drying`

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Trocknung"
2. Nutzer betrachtet den Hinweisbereich zum Anbausystem

**Erwartete Ergebnisse**:
- Ein Info-Banner oder Hinweiskasten zeigt: "Hydro-Material trocknet ca. 15% schneller — Uebertrocknung vermeiden"
- Empfehlung: "Flushing empfohlen fuer saubereren Geschmack"
- Die berechnete Trocknungsdauer ist um ~15% kuerzer als der Standard-Basiswert

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, anbausystem, hydro, u-002, growing-system-modifier]

---

## 3. Jar-Curing & Burping-Assistent

### TC-REQ-008-015: Jar-Curing starten und Burping-Schedule anzeigen (Tag 1–7)

**Requirement**: REQ-008 § 6 DoD (Burping-Timer), Szenario 2
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `drying`, Snap-Test zeigt OPTIMAL
- Nutzer hat Trocknung abgeschlossen (Fortschritt ≥95% oder Snap-Test positiv)

**Testschritte**:
1. Nutzer klickt auf "Curing starten"
2. Ein Dialog fragt nach Jar-Anzahl (z.B. 4) und Gramm pro Jar (z.B. 28g)
3. Nutzer bestaetigt
4. Nutzer oeffnet Tab "Curing" auf der Batch-Detailseite

**Erwartete Ergebnisse**:
- Status-Badge wechselt zu "In Curing" (`curing`)
- Der Curing-Bereich zeigt:
  - "Tage im Cure: 0" (oder 1 nach dem naechsten Tag)
  - Aktueller Burping-Plan: "2x taeglich, 15 Minuten" mit Zeiten "09:00 und 21:00"
  - Begruendung: "Woche 1 — Hohe Restfeuchte"
  - Ziel-RH im Jar: 58–62%
  - Hinweis: "Kondensations-Check bei jedem Burping"

**Nachbedingungen**:
- Batch-Status ist `curing`, Curing-Startdatum gesetzt

**Tags**: [req-008, jar-curing, burping-schedule, woche-1, szenario-2, curing-start]

---

### TC-REQ-008-016: Burping-Schedule nach 10 Tagen Curing auf "taeglich" reduziert

**Requirement**: REQ-008 § 3 JarCuringManager.get_burping_schedule (Tage 8–14 = daily)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Batch ist seit 10 Tagen im Status `curing`
- Curing-Startdatum liegt 10 Tage in der Vergangenheit

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Curing"
2. Nutzer betrachtet den aktuellen Burping-Plan

**Erwartete Ergebnisse**:
- "Tage im Cure: 10"
- Burping-Frequenz: "1x taeglich, 10 Minuten"
- Zeit: "12:00 Uhr"
- Begruendung: "Woche 2 — Feuchte stabilisiert sich"
- Hinweis: "Boveda 62% Packs ab Woche 2 empfohlen" ist sichtbar

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-008, burping-schedule, woche-2, taeglich, boveda]

---

### TC-REQ-008-017: Burping-Schedule nach 25 Tagen auf "woechentlich" reduziert

**Requirement**: REQ-008 § 3 JarCuringManager.get_burping_schedule (>22 Tage = weekly)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Batch ist seit 25 Tagen im Status `curing`

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Curing"
2. Nutzer betrachtet den aktuellen Burping-Plan

**Erwartete Ergebnisse**:
- "Tage im Cure: 25"
- Burping-Frequenz: "1x woechentlich, 5 Minuten"
- Begruendung: "Final Cure — Nur Wartung"
- Qualitaets-Indikatoren-Bereich zeigt positive Meldungen (z.B. "Terpen-Profil voll entwickelt nach 21+ Tagen")

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-008, burping-schedule, final-cure, woechentlich, qualitaets-indikatoren]

---

### TC-REQ-008-018: Burping-Ereignis erfassen und in Verlauf speichern

**Requirement**: REQ-008 § 2 BurpingEvent-Node, § 6 DoD (Burping-Timer)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `curing`
- Ein faelliger Burping-Termin existiert

**Testschritte**:
1. Nutzer klickt auf "Burping jetzt ausfuehren" oder "Burping protokollieren"
2. Ein Formular-Dialog oeffnet sich
3. Nutzer gibt RH vor dem Burping ein: "64%"
4. Nutzer gibt RH nach dem Burping ein: "60%"
5. Nutzer aktiviert nicht "Kondensation beobachtet"
6. Nutzer gibt Aroma-Notiz ein: "Leicht gruen, beginnt fruchtig zu werden"
7. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- In der Burping-Verlaufstabelle erscheint ein neuer Eintrag mit Zeitstempel, RH-Werten und Aroma-Notiz
- Die Anzeige "Naechstes Burping" aktualisiert sich auf den naechsten faelligen Zeitpunkt
- Erfolgsbenachrichtigung: "Burping protokolliert"

**Nachbedingungen**:
- Neuer BurpingEvent-Eintrag in der Verlaufstabelle sichtbar

**Tags**: [req-008, burping-event, protokollierung, jar-rh, aroma-notiz]

---

### TC-REQ-008-019: Jar-RH zu hoch (>65%) — Schimmelgefahr-Warnung beim Burping

**Requirement**: REQ-008 § 3 JarCuringManager.assess_jar_rh (>65% = TOO_HIGH = SCHIMMEL-GEFAHR), Szenario 4
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Batch ist im Status `curing`
- Nutzer oeffnet Burping-Dialog

**Testschritte**:
1. Nutzer klickt auf "Burping protokollieren"
2. Nutzer gibt RH vor dem Burping ein: "72%"
3. Nutzer verlaesst das Feld oder klickt auf das naechste Formularfeld

**Erwartete Ergebnisse**:
- Sofortige Warnmeldung im Dialog: "SCHIMMEL-GEFAHR: RH 72% liegt deutlich ueber dem kritischen Wert (65%)"
- Empfohlene Aktion: "SOFORT burpen und laenger offen lassen (30 min+)"
- Der Status-Indikator zeigt "ZU HOCH" in roter Farbe

**Nachbedingungen**:
- Keine Curing-Daten geaendert bis Nutzer speichert

**Tags**: [req-008, jar-rh, zu-hoch, schimmelgefahr, szenario-4, kritisch]

---

### TC-REQ-008-020: Jar-RH optimal (58–62%) — OK-Status anzeigen

**Requirement**: REQ-008 § 3 JarCuringManager.assess_jar_rh (58–62% = OPTIMAL)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `curing`

**Testschritte**:
1. Nutzer klickt auf "Burping protokollieren"
2. Nutzer gibt RH vor dem Burping ein: "60%"

**Erwartete Ergebnisse**:
- Gruer Status-Indikator: "OPTIMAL"
- Meldung: "Perfekter Cure-Bereich (58–62%)"
- Empfehlung: "Weiter wie bisher"

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-008, jar-rh, optimal, curing, ok-status]

---

### TC-REQ-008-021: Jar-RH zu niedrig (<55%) — Boveda-Pack-Empfehlung

**Requirement**: REQ-008 § 3 JarCuringManager.assess_jar_rh (<55% = TOO_LOW), § 6 DoD (Boveda-Pack-Empfehlung)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Batch ist im Status `curing`

**Testschritte**:
1. Nutzer klickt auf "Burping protokollieren"
2. Nutzer gibt RH vor dem Burping ein: "50%"

**Erwartete Ergebnisse**:
- Warnmeldung: "RH zu niedrig — Terpen-Verlust, Material wird bruechig"
- Empfohlene Aktion: "Boveda 62% Pack DRINGEND einlegen + seltener burpen"
- Status-Indikator: "ZU NIEDRIG" in gelbem oder orangenem Text

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-008, jar-rh, zu-niedrig, boveda-empfehlung, terpen-verlust]

---

### TC-REQ-008-022: Curing-Qualitaets-Timeline — Meilensteine nach Tagen anzeigen

**Requirement**: REQ-008 § 6 DoD (Curing-Quality-Timeline), § 3 _get_quality_indicators
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Batch ist seit 22 Tagen im Status `curing`

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite, Tab "Curing"
2. Nutzer betrachtet den Abschnitt "Qualitaets-Entwicklung"

**Erwartete Ergebnisse**:
- Folgende Meilensteine sind als erreicht markiert (z.B. Haken-Icon):
  - "Erste Aroma-Veraenderungen erkennbar" (ab Tag 3)
  - "Chlorophyll-Abbau begonnen (weniger gruen)" (ab Tag 7)
  - "Harshness reduziert, smootherer Geschmack" (ab Tag 14)
  - "Terpen-Profil voll entwickelt" (ab Tag 21)
- Empfohlene Gesamtdauer-Optionen sind sichtbar (z.B. "2 Wochen = Akzeptabel", "4 Wochen = Gut", "6 Wochen = Optimal")

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, curing-timeline, qualitaets-indikatoren, meilensteine]

---

## 4. Schimmel-Praevention & Mold-Alert

### TC-REQ-008-023: Schimmel-Alert bei RH >65% ueber 6 Stunden anzeigen

**Requirement**: REQ-008 § 6 DoD (Schimmel-Alert automatische Warnung), Szenario 3
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Ein Lagerort "Trocknungsraum" ist angelegt und mit einem Batch verknuepft
- Sensor-Daten zeigen RH = 68% im Durchschnitt der letzten 6 Stunden
- Das System hat automatisch einen MoldAlert generiert

**Testschritte**:
1. Nutzer navigiert zum Post-Harvest-Dashboard oder zur Lagerort-Seite
2. Nutzer sieht eine rote Warnung oder ein Alert-Banner oben auf der Seite

**Erwartete Ergebnisse**:
- Ein roter Alert-Banner erscheint: "SCHIMMEL-RISIKO: KRITISCH"
- Angabe des Lagerorts: "Trocknungsraum"
- Angabe des Ausloeser-Grunds: "RH 68% > 65% ueber 6h"
- Empfohlene Sofortmassnahmen sind aufgelistet (z.B. "Dehumidifier einschalten", "Luftaustausch erhoehen", "Alle Batches visuell pruefen")
- Eine Push-Notification oder In-App-Benachrichtigung hat den Nutzer bereits informiert (Glocken-Icon zeigt Badge)

**Nachbedingungen**:
- Alert ist sichtbar bis der Nutzer ihn als behoben markiert

**Tags**: [req-008, mold-alert, kritisch, rh-ueberschreitung, szenario-3, push-notification]

---

### TC-REQ-008-024: Schimmel-Alert als behoben markieren

**Requirement**: REQ-008 § 2 MoldAlert-Node (resolved_at), § 6 DoD
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Ein offener MoldAlert ist in der UI sichtbar

**Testschritte**:
1. Nutzer klickt auf den Alert-Banner oder navigiert zur Alert-Detailansicht
2. Nutzer gibt eingeleitete Massnahme ein: "Dehumidifier eingeschaltet, Fenster geoeffnet"
3. Nutzer klickt "Als behoben markieren"

**Erwartete Ergebnisse**:
- Der Alert-Banner verschwindet aus dem Dashboard
- In der Schimmel-Alert-Historie erscheint der Eintrag mit Status "Behoben" und Zeitstempel
- Die eingeleitete Massnahme ist gespeichert und sichtbar

**Nachbedingungen**:
- MoldAlert hat `resolved_at`-Zeitstempel gesetzt

**Tags**: [req-008, mold-alert, behoben, resolved, massnahme]

---

### TC-REQ-008-025: Schimmeltyp-Identifikations-Assistent oeffnen und Botrytis identifizieren

**Requirement**: REQ-008 § 6 DoD (Mold-Type-Identification), § 3 MoldPreventionMonitor.identify_mold_type
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer befindet sich auf der Lagerort-Seite oder einem offenen Mold-Alert
- Funktion "Schimmeltyp bestimmen" ist verfuegbar

**Testschritte**:
1. Nutzer klickt auf "Schimmeltyp bestimmen" oder "Hilfe bei Schimmel-Identifikation"
2. Ein Hilfe-Dialog oeffnet sich mit Eingabefeldern: visuelle Beschreibung, Farbe, Textur
3. Nutzer waehlt Farbe "Grau" aus
4. Nutzer waehlt Textur "Flauschig" aus
5. Nutzer klickt "Identifizieren"

**Erwartete Ergebnisse**:
- Ergebnis: "Botrytis (Grauschimmel / Bud Rot)"
- Gefahrenstufe: "KRITISCH"
- Sofortmassnahme: "Gesamte Bluete entfernen + 5 cm Umkreis"
- Praevention: "RH <50% in Bluete, gute Luftzirkulation"
- Allgemeiner Haftungsausschluss: "WARNUNG: Nur informativ — kein Ersatz fuer Experten"

**Nachbedingungen**:
- Keine Daten gespeichert (Identifikations-Tool ist nur informativ)

**Tags**: [req-008, schimmeltyp, botrytis, mold-identification, disclaimer]

---

### TC-REQ-008-026: Aspergillus flavus identifizieren — Aflatoxin-Warnung anzeigen

**Requirement**: REQ-008 § 6 DoD (Aspergillus-Differenzierung U-004), § 3 identify_mold_type
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Schimmeltyp-Assistent ist geoeffnet

**Testschritte**:
1. Nutzer waehlt Farbe "Gruen-Gelb" im Schimmeltyp-Dialog
2. Nutzer waehlt Textur "Koernig/Pudrig"
3. Nutzer klickt "Identifizieren"

**Erwartete Ergebnisse**:
- Ergebnis: "Aspergillus flavus"
- Gefahrenstufe: "KRITISCH"
- Hervorgehobener Warntext: "SOFORTIGE ENTSORGUNG — Aflatoxin ist kanzerogen! Nicht beruehren ohne Handschuhe."
- Hinweis auf Mykotoxin: "Aflatoxin B1 (kanzerogen, IARC Klasse 1)"
- Empfohlene Massnahme: "Lagerort desinfizieren"

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [req-008, aspergillus-flavus, aflatoxin, u-004, kritisch-gesundheit]

---

### TC-REQ-008-027: Aspergillus fumigatus identifizieren — Invasive-Aspergillose-Warnung

**Requirement**: REQ-008 § 6 DoD (Aspergillus-Differenzierung U-004)
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Schimmeltyp-Assistent ist geoeffnet

**Testschritte**:
1. Nutzer waehlt Farbe "Blaugrau" im Schimmeltyp-Dialog
2. Nutzer klickt "Identifizieren"

**Erwartete Ergebnisse**:
- Ergebnis: "Aspergillus fumigatus (Invasiver Schimmelpilz)"
- Gefahrenstufe: "KRITISCH"
- Warntext: "SOFORTIGE ENTSORGUNG — Invasive Aspergillose bei Immungeschwachten! Atemschutzmaske (FFP2+) und Handschuhe tragen."
- Spezifischer Hinweis fuer Cannabis-Nutzer: "Sporen sind durch Inhalation besonders gefaehrlich"
- Praevention: "Strikte RH-Kontrolle <55%, HEPA-Filterung im Trocknungsraum"

**Nachbedingungen**:
- Keine Daten gespeichert

**Tags**: [req-008, aspergillus-fumigatus, u-004, aspergillose, ffp2, hepa]

---

### TC-REQ-008-028: Schimmel-Risikoanzeige bei Wasseraktivitaets-Sensor (a_w > 0.65)

**Requirement**: REQ-008 § 2 StorageCondition (target_water_activity), § 3 MoldPreventionMonitor (a_w-basierte Bewertung bevorzugt)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Lagerort hat einen a_w-Sensor verbunden
- Letzter a_w-Messwert: 0.67 (ueber kritischem Schwellenwert 0.65)

**Testschritte**:
1. Nutzer navigiert zur Lagerort-Detailseite
2. Nutzer betrachtet die aktuellen Messwerte im Monitoring-Bereich

**Erwartete Ergebnisse**:
- Der a_w-Wert 0.67 wird rot hervorgehoben
- Meldung: "KRITISCH: Wasseraktivitaet 0.67 > 0.65 — Schimmelpilz-Wachstum moeglich"
- Hinweis: "a_w-basierte Bewertung (biologisch praeziser als RH-Messung)"
- Empfehlungen sind sichtbar (Dehumidifier, Luftaustausch, visuelle Pruefung)

**Nachbedingungen**:
- Alert ggf. automatisch erstellt (sichtbar in Alert-Historie)

**Tags**: [req-008, wasser-aktivitaet, a_w, schimmel-risiko, sensor-monitoring]

---

### TC-REQ-008-029: CO2-Warnung bei Ueberschreitung 1500 ppm im Trocknungsraum

**Requirement**: REQ-008 § 6 DoD (CO2-Ueberwachung U-005), § 3 CO2Monitor (WARNING bei ≥1500 ppm)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Lagerort hat einen CO2-Sensor
- Aktueller CO2-Messwert: 1600 ppm

**Testschritte**:
1. Nutzer navigiert zur Lagerort-Detailseite
2. Nutzer betrachtet den CO2-Monitoring-Bereich

**Erwartete Ergebnisse**:
- CO2-Wert 1600 ppm ist gelb oder orange hervorgehoben
- Hinweismeldung: "Belueftung erhoehen. CO2 > 1500 ppm weist auf unzureichenden Luftaustausch hin."
- Empfehlung: CO2-Level unter 1200 ppm bringen

**Nachbedingungen**:
- Keine Daten veraendert (Sensor-Lesewert)

**Tags**: [req-008, co2-ueberwachung, u-005, co2-warnung, belueftung]

---

### TC-REQ-008-030: CO2-Kritisch-Warnung bei >2000 ppm — Sofortmassnahme

**Requirement**: REQ-008 § 3 CO2Monitor (CRITICAL bei ≥2000 ppm), § 6 DoD (CO2-Ueberwachung U-005)
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Lagerort hat einen CO2-Sensor
- Aktueller CO2-Messwert: 2200 ppm

**Testschritte**:
1. Nutzer navigiert zur Lagerort-Detailseite

**Erwartete Ergebnisse**:
- Roter Alert-Banner: "CO2-KRITISCH: 2200 ppm — Sofortige Belueftung erforderlich!"
- Erklaerung: "CO2 > 2000 ppm foerdert anaerobe Prozesse und Schimmelbildung"
- Sofortmassnahme hervorgehoben: "Abluftventilator aktivieren"

**Nachbedingungen**:
- Alert sichtbar bis Massnahme getroffen

**Tags**: [req-008, co2-kritisch, u-005, anaerob, sofortmassnahme]

---

## 5. Lager-Inventar & Haltbarkeitsprognose

### TC-REQ-008-031: Lagerort anlegen und in Liste anzeigen

**Requirement**: REQ-008 § 2 StorageLocation-Node, § 3 StorageLocationManager
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Post-Harvest-Bereich ist in der Navigation zugaenglich

**Testschritte**:
1. Nutzer navigiert zu "Post-Harvest" → "Lagerorte"
2. Nutzer klickt auf "Lagerort anlegen"
3. Ein Dialog oeffnet sich mit Feldern: Name, Typ, Kapazitaet (kg), Klimaanlage vorhanden
4. Nutzer gibt ein: Name "Trocknungsraum", Typ "Raum (room)", Kapazitaet "2.0" kg
5. Nutzer aktiviert nicht "Aktive Klimasteuerung vorhanden"
6. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Der neue Lagerort "Trocknungsraum" erscheint in der Lagerorts-Liste
- Kapazitaet: 2.0 kg, Auslastung: 0%
- Erfolgsbenachrichtigung: "Lagerort erstellt"

**Nachbedingungen**:
- Lagerort ist in der Liste sichtbar und fuer Batches waehlbar

**Tags**: [req-008, lagerort, anlegen, storage-location, erstellen]

---

### TC-REQ-008-032: Lager-Inventar-Uebersicht mit Haltbarkeits-Prognose anzeigen

**Requirement**: REQ-008 § 6 DoD (Lager-Inventar mit Haltbarkeits-Prognose), Szenario 7
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Mindestens ein Lagerort existiert
- Ein Cannabis-Batch ist seit 120 Tagen im Status `stored` und in diesem Lagerort eingelagert
- Lagerbedingungen sind korrekt (ideale Temp/RH)

**Testschritte**:
1. Nutzer navigiert zu "Post-Harvest" → "Lager-Inventar"

**Erwartete Ergebnisse**:
- Eine Uebersichtstabelle zeigt alle belegten Lagerorte
- Fuer den Cannabis-Batch sind sichtbar:
  - Batch-ID
  - Spezies: "Cannabis sativa"
  - Gewicht in g
  - "Tage im Lager: 120"
  - "Verbleibende Tage: 245" (Gesamthaltbarkeit 365 Tage)
  - "Haltbarkeit genutzt: 33%"
  - Kein Alert (noch > 30 Tage verbleibend)

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, lager-inventar, haltbarkeits-prognose, szenario-7, cannabis-storage]

---

### TC-REQ-008-033: Haltbarkeits-Alert bei weniger als 30 verbleibenden Tagen

**Requirement**: REQ-008 § 2 AQL Storage-Inventar (alerts wenn days_remaining < 30)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Ein Batch ist im Status `stored`
- Berechnete Restlaufzeit: 20 Tage

**Testschritte**:
1. Nutzer navigiert zu "Post-Harvest" → "Lager-Inventar"

**Erwartete Ergebnisse**:
- Der betroffene Batch ist rot oder orange hervorgehoben
- Alert-Text: "[Batch-ID] laeuft in 20 Tagen ab"
- Eine separate Alert-Spalte oder ein Icon signalisiert die nahende Ablaufzeit

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, haltbarkeits-alert, ablauf, 30-tage, storage-inventar]

---

### TC-REQ-008-034: Parametrische Haltbarkeitsprognose mit schlechten Lagerbedingungen reduziert sich

**Requirement**: REQ-008 § 6 DoD (Parametrische Haltbarkeitsprognose P-001), § 3 ShelfLifeEstimator
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Ein Cannabis-Batch ist im Status `stored`
- Tatsaechliche Lagertemperatur weicht +8°C vom Zielwert ab (schlechte Bedingungen)
- Tatsaechliche RH weicht +12% vom Zielwert ab

**Testschritte**:
1. Nutzer oeffnet die Lagerort-Detailseite mit diesem Batch
2. Nutzer betrachtet die Haltbarkeitsprognose fuer den Batch

**Erwartete Ergebnisse**:
- Angezeigte Haltbarkeit ist deutlich kuerzer als 365 Tage (konditionsreduziert)
- Der Konditions-Faktor wird angezeigt (z.B. "Konditions-Faktor: 0.60")
- Erklaerung: "Abweichung von Ziel-Temperatur und RH reduziert die Haltbarkeit"
- Empfehlung: Lagerbedingungen verbessern

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, haltbarkeit, p-001, konditions-faktor, lagerbedingungen-schlecht]

---

### TC-REQ-008-035: Multi-Species-Storage-Optimierer — Konflikt zwischen Kartoffel und Zwiebel

**Requirement**: REQ-008 § 6 DoD (Storage-Condition-Optimizer), Szenario 6
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Ein Lagerort "Wurzelkeller" enthaelt sowohl Kartoffeln (Solanum tuberosum) als auch Zwiebeln (Allium cepa)
- Funktion "Optimale Lagerbedingungen berechnen" ist verfuegbar

**Testschritte**:
1. Nutzer navigiert zum Lagerort "Wurzelkeller"
2. Nutzer klickt auf "Optimale Bedingungen anzeigen" oder "Conditions-Optimizer"

**Erwartete Ergebnisse**:
- Berechnete optimale Temperatur: 10°C (Ueberschneidung beider Bedarfsbereiche)
- Berechnete RH: "Konflikt" — Kartoffeln benoetigen 85–90%, Zwiebeln 60–70%
- Hinweis: "Zwiebeln und Kartoffeln sollten NICHT zusammen gelagert werden"
- Zusaetzlicher Hinweis: "Kartoffeln: KOMPLETT dunkel — sonst Solanin-Bildung"
- Empfehlung: Getrennte Lagerorte anlegen

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, storage-optimizer, multi-species, kartoffel-zwiebel, szenario-6, solanin]

---

### TC-REQ-008-036: Lagerort-Auslastungswarnung bei >90% Kapazitaet

**Requirement**: REQ-008 § 3 StorageLocationManager.calculate_utilization (>90% = CRITICAL_FULL)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Lagerort hat Kapazitaet 2 kg
- Aktuell eingelagert: 1.85 kg (92.5% Auslastung)

**Testschritte**:
1. Nutzer navigiert zur Lagerorts-Uebersicht

**Erwartete Ergebnisse**:
- Der betroffene Lagerort ist rot markiert
- Auslastungsanzeige: "92.5% — KRITISCH VOLL"
- Empfehlung: "Sofort alternative Lagerung suchen"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, lagerort, kapazitaet, kritisch-voll, u-auslastung]

---

## 6. Trim-Protokoll-Erfassung

### TC-REQ-008-037: Trim-Protokoll "Wet Trim" fuer Batch erfassen

**Requirement**: REQ-008 § 6 DoD (Trim-Protokoll U-007), § 2 TrimProtocol-Node
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `fresh` (direkt nach Ernte) oder `drying`
- Funktion "Trim-Protokoll erfassen" ist auf der Batch-Detailseite verfuegbar

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite
2. Nutzer klickt auf "Trim erfassen"
3. Ein Formular-Dialog oeffnet sich
4. Nutzer waehlt Methode: "Wet Trim (direkt nach Ernte)"
5. Nutzer waehlt Qualitaetsstufe: "Hand Premium"
6. Nutzer gibt Gewicht vor Trim ein: "450" g
7. Nutzer gibt Gewicht nach Trim ein: "380" g
8. Nutzer gibt Verschnitt ein: "70" g, davon verwertbar: "40" g
9. Nutzer gibt Trimmende-Name ein: "Anna M."
10. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Auf der Batch-Detailseite erscheint der Trim-Protokoll-Bereich mit:
  - Methode: "Wet Trim"
  - Verschnitt: 15.6% (70 g von 450 g)
  - Verwertbarer Verschnitt: 40 g (57.1% des Verschnitts)
  - Trim-Effizienz: 84.4% (380 g / 450 g)
  - Empfehlung basierend auf Verschnitt-Prozentsatz
- Erfolgsbenachrichtigung: "Trim-Protokoll gespeichert"

**Nachbedingungen**:
- TrimProtocol-Eintrag ist gespeichert und sichtbar

**Tags**: [req-008, trim-protokoll, wet-trim, u-007, verschnitt, effizienz]

---

### TC-REQ-008-038: Trim-Protokoll-Validierung: Gewicht nach Trim darf nicht groesser als vorher sein

**Requirement**: REQ-008 § 3 TrimProtocol.validate_post_trim (post ≤ pre)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Trim-Formular-Dialog ist geoeffnet
- Nutzer hat Gewicht vor Trim "380" g eingegeben

**Testschritte**:
1. Nutzer gibt Gewicht nach Trim "400" g ein (groesser als Gewicht vor Trim)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eine Validierungsfehlermeldung erscheint beim Feld "Gewicht nach Trim": "Gewicht nach Trim darf nicht groesser sein als Gewicht vor Trim"
- Der Dialog bleibt geoeffnet
- Keine Daten werden gespeichert

**Nachbedingungen**:
- Kein TrimProtocol gespeichert

**Tags**: [req-008, trim-protokoll, formvalidierung, gewicht-validierung, u-007]

---

### TC-REQ-008-039: Hoher Trim-Verschnitt (>40%) erzeugt Hinweis-Empfehlung

**Requirement**: REQ-008 § 3 TrimProtocol._get_trim_recommendation (>40% = hoher Verschnitt)
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Trim-Protokoll ist gespeichert mit Verschnitt 45% (z.B. 200g Verschnitt von 440g Gesamt)

**Testschritte**:
1. Nutzer oeffnet das gespeicherte Trim-Protokoll auf der Batch-Detailseite

**Erwartete Ergebnisse**:
- Die Trim-Statistiken zeigen Verschnitt: 45%
- Eine Empfehlungs-Meldung erscheint: "Hoher Verschnitt — pruefen ob weniger aggressiv getrimmt werden kann"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, trim-empfehlung, hoher-verschnitt, u-007]

---

## 7. Qualitaetsbewertung & Beobachtungen

### TC-REQ-008-040: Lager-Beobachtung (StorageObservation) erfassen

**Requirement**: REQ-008 § 2 StorageObservation-Node, § 6 DoD (Qualitaets-Monitoring)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `drying`, `curing` oder `stored`
- Tab "Beobachtungen" ist auf der Batch-Detailseite verfuegbar

**Testschritte**:
1. Nutzer klickt auf "Beobachtung erfassen"
2. Ein Formular-Dialog oeffnet sich
3. Nutzer gibt ein:
   - Aktuelles Gewicht: "200" g
   - Temperatur: "18.5" °C
   - Luftfeuchte: "52" %
   - Visueller Zustand: "Gut" (good)
   - Aromawert: "Akzeptabel" (acceptable)
   - Defekte: leer (keine)
   - Notiz: "Leichte Verbesserung des Aromas, keine sichtbaren Probleme"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Neue Beobachtung erscheint in der Beobachtungs-Tabelle mit Zeitstempel
- Alle eingegebenen Werte sind korrekt gespeichert und sichtbar
- Erfolgsbenachrichtigung: "Beobachtung gespeichert"

**Nachbedingungen**:
- StorageObservation-Eintrag in der Verlaufstabelle sichtbar

**Tags**: [req-008, beobachtung, storage-observation, erfassen, qualitaets-monitoring]

---

### TC-REQ-008-041: Schimmel-Defekt in Beobachtung erzwingt "kritischen" Zustandswert

**Requirement**: REQ-008 § 3 StorageObservation.validate_critical_defects (mold → visual_condition='critical')
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Beobachtungs-Dialog ist geoeffnet

**Testschritte**:
1. Nutzer gibt im Feld "Defekte" den Wert "mold_spot" ein (oder waehlt ihn aus einer Liste)
2. Nutzer laesst den visuellen Zustand auf "Gut" (good) eingestellt
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eine Validierungsfehlermeldung erscheint: "Schimmel erfordert einen kritischen Zustandswert ('Kritisch')"
- Der Dialog bleibt geoeffnet
- Das Feld "Visueller Zustand" wird als Fehlerfeld hervorgehoben

**Nachbedingungen**:
- Keine Beobachtung gespeichert

**Tags**: [req-008, beobachtung, formvalidierung, schimmel-defekt, kritischer-zustand, storage-observation]

---

### TC-REQ-008-042: Wasseraktivitaet (a_w) in Beobachtung erfassen und Schimmelrisiko-Ampel zeigen

**Requirement**: REQ-008 § 6 DoD (Water-Activity-Tracking), § 2 StorageObservation (water_activity)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Beobachtungs-Dialog ist geoeffnet
- Nutzer hat ein a_w-Messgeraet und kann einen Wert eingeben

**Testschritte**:
1. Nutzer gibt a_w-Wert "0.63" im Feld "Wasseraktivitaet (a_w)" ein
2. Nutzer speichert die Beobachtung

**Erwartete Ergebnisse**:
- a_w-Wert 0.63 wird in der Beobachtung gespeichert und angezeigt
- Eine Statusampel zeigt "WARNUNG" (gelb), da 0.63 > 0.60 aber < 0.65
- Hinweis: "a_w > 0.60 — Schimmelrisiko erhoehen, auf < 0.60 senken"
- Erklaerung: "Schimmelpilze wachsen ab a_w > 0.65 (unabhaengig von Raumluftfeuchte)"

**Nachbedingungen**:
- a_w-Wert gespeichert, Warnung sichtbar

**Tags**: [req-008, water-activity, a_w, schimmelrisiko-ampel, 0-63]

---

### TC-REQ-008-043: Trocknungs-Zielwert fuer Cannabis a_w korrekt angezeigt

**Requirement**: REQ-008 § 2 StorageCondition (target_water_activity 0.55–0.65 fuer Cannabis)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Cannabis sativa"
- Batch ist im Status `drying`

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite, Tab "Trocknung"
2. Nutzer sucht nach dem Ziel-a_w-Wert-Hinweis

**Erwartete Ergebnisse**:
- Hinweis sichtbar: "Ziel-Wasseraktivitaet (a_w): 0.55–0.65"
- Erklaerung: "a_w ist ein biologisch praeziserer Endpunkt-Indikator als die Restfeuchte in %"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, water-activity, cannabis, a_w-ziel, 0-55-0-65]

---

## 8. Spezies-spezifische Protokoll-Guides

### TC-REQ-008-044: Zwiebel-Phasentrennung — Haertungs-Guide anzeigen (UV erwuenscht)

**Requirement**: REQ-008 § 6 DoD (Zwiebel-Phasentrennung P-004), § 3 LightDegradationManager (onion curing = 'controlled')
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Allium cepa" (Zwiebel)
- Batch ist im Status `drying` (Haertungsphase)

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite, Tab "Trocknungs-Protokoll" oder "Guide"
2. Nutzer betrachtet die Protokoll-Hinweise zur Haertungsphase

**Erwartete Ergebnisse**:
- Phase 1 "Schalenhartung (Curing)": Dauer 2–3 Wochen, Temperatur 25–30°C, niedrige RLF
- Hervorgehobener Hinweis: "UV-Exposition ERWUENSCHT: Foerdert Schalenhartung und antimikrobielle Wirkung"
- Empfehlung: "Gut beluefteter, sonniger (aber nicht heisser) Standort"
- Phase 2 "Langzeitlagerung": KEIN UV, dunkel, 10–15°C, 60–70% RLF
- Hinweis: "Licht foerdert Keimung und Ergrunung (Chlorophyll-Synthese)"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, zwiebel, phasentrennung, p-004, uv-erwuenscht, haertung, u-008]

---

### TC-REQ-008-045: Kartoffel-Guide — Solanin-Warnung bei Lichtkontakt anzeigen

**Requirement**: REQ-008 § 3 LightDegradationManager (potato: 'none' — Solanin-Biosynthese), § 6 DoD (UV/Licht U-008)
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Solanum tuberosum" (Kartoffel)
- Batch ist in einem Lagerstatus

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite
2. Nutzer betrachtet den Lager-Guide / Hinweisbereich

**Erwartete Ergebnisse**:
- Kritischer Warnhinweis: "ABSOLUT DUNKEL lagern: Licht (auch indirektes) induziert Solanin-Biosynthese"
- Erklaerung: "Gruene Stellen = Solanin = giftig"
- UV-Exposition-Einstellung: "Keines ('none')"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, kartoffel, solanin, u-008, absolut-dunkel, licht-warnung]

---

### TC-REQ-008-046: Kartoffel-Haltbarkeit mit Keimhemmungs-Modifier anzeigen (P-005)

**Requirement**: REQ-008 § 6 DoD (Kartoffel-Keimhemmung P-005), § 3 ShelfLifeEstimator (sprouting_inhibition)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Solanum tuberosum", Sorte "festkochend" (waxy)
- Keimhemmung: "Nur Kuehllagerung 3–4°C" (cold)
- Batch ist im Status `stored`

**Testschritte**:
1. Nutzer oeffnet die Batch-Detailseite oder das Lager-Inventar
2. Nutzer betrachtet die Haltbarkeitsprognose

**Erwartete Ergebnisse**:
- Basis-Haltbarkeit: 270 Tage (fuer Kartoffel allgemein)
- Sorten-Modifier angezeigt: "Festkochend: 0.7"
- Keimhemmungs-Modifier angezeigt: "Nur Kuehllagerung: 0.8"
- Berechnete Haltbarkeit: 270 × 0.7 × 0.8 = ca. 151 Tage
- Hinweis: "Ohne Keimhemmung (CIPC) signifikant kuerzer"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, kartoffel, p-005, keimhemmung, haltbarkeit, sorten-modifier]

---

### TC-REQ-008-047: Sauerkraut-Fermentationsguide — zweiphasige Temperaturprofile anzeigen

**Requirement**: REQ-008 § 1 Business Case (Sauerkraut-Fermentation), § 6 DoD (Phasen-Fermentation)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Brassica oleracea" (Weisskohlvarietaet) oder ist als Sauerkraut-Fermentation angelegt
- Batch ist im Status `curing`

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite, Tab "Fermentations-Protokoll"

**Erwartete Ergebnisse**:
- Phase 1 "Leuconostoc (Tag 1–3)": Temperatur 18–22°C, schnelle CO2-Bildung, taeglich Gasen ablassen
- Phase 2 "Lactobacillus (Tag 4–21)": Temperatur 15–18°C, langsamere, aromatischere Fermentation
- Salzlake-Hinweis: "2–2.5% Salzgehalt, Gemuese muss vollstaendig unter Lake sein"
- Fertig-Kriterien: "pH < 4.0, milchsauer, keine Gasbildung mehr"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, sauerkraut, fermentation, leuconostoc, lactobacillus, zweiphasig, p-fermentation]

---

### TC-REQ-008-048: Tomate-Ethylen-Management-Hinweis anzeigen

**Requirement**: REQ-008 § 1 Business Case (Tomate Nachreife, Ethylen-Management)
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Solanum lycopersicum" (Tomate), grun geerntet
- Batch ist im Status `aging`

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite, Tab "Reifungs-Protokoll"

**Erwartete Ergebnisse**:
- Zwei Methoden sind dokumentiert:
  - "Professionell: Kontrollierte Ethylen-Begasung (0.1–1 ppm) bei 18–21°C, 85–90% RH"
  - "Hobby: Mit reifen Aepfeln/Bananen in geschlossener Papiertute lagern"
- WICHTIGER Hinweis: "Ethylen-empfindliche Produkte (Salat, Gurke, Brokkoli, Kraeuter) NICHT zusammen mit Ethylen-Produzenten (Tomate, Apfel) lagern"
- Nachreife-Dauer: 1–3 Wochen bei 18–21°C

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, tomate, ethylen, nachreife, ethylen-sensibel, lager-kompatibilitaet]

---

## 9. UV/Licht-Degradations-Warnungen

### TC-REQ-008-049: Cannabis-Lagerung — UV-Warnung und opake Behaelter-Empfehlung

**Requirement**: REQ-008 § 6 DoD (UV/Licht-Degradation U-008), § 3 LightDegradationManager
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Batch gehoert zu "Cannabis sativa"
- Batch ist im Status `stored`

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite
2. Nutzer betrachtet den Lager-Guide Abschnitt "Licht / UV"

**Erwartete Ergebnisse**:
- UV-Exposition: "Keines — UV degradiert THC"
- Verpackungsempfehlung: "Opakes Glas (Violettglas/Miron) oder lichtdichte Behaelter"
- Degradations-Hinweis: "THC → CBN: ~0.5%/Monat dunkel, ~3%/Monat bei indirektem Licht"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, cannabis, uv-degradation, u-008, thc-cbn, violettglas]

---

## 10. Stoerfall-Protokolle (Emergency Protocols)

### TC-REQ-008-050: Emergency-Protokoll fuer Schimmel-Fund anzeigen

**Requirement**: REQ-008 § 6 DoD (Emergency-Protocols: Schimmel-Fund)
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer hat Schimmel in einem Batch entdeckt
- Ein offener MoldAlert existiert oder Nutzer greift ueber "Notfall-Protokoll" zu

**Testschritte**:
1. Nutzer klickt auf "Notfall-Protokoll" oder "Was tun bei Schimmel-Fund?"
2. Ein Hilfe-Dialog oder eine Seite oeffnet sich

**Erwartete Ergebnisse**:
- Schritt-fuer-Schritt-Anleitung erscheint:
  1. "SOFORTIGE MASSNAHMEN erforderlich!"
  2. "1. Dehumidifier einschalten"
  3. "2. Luftaustausch maximieren"
  4. "3. Alle Batches visuell auf Schimmel pruefen"
  5. "4. Temperatur senken wenn moeglich"
  6. "5. Betroffene Bereiche isolieren"
- Hinweis auf den Schimmeltyp-Identifikations-Assistenten
- Optionen: "Batch entsorgen" und "Batch isolieren"

**Nachbedingungen**:
- Keine Daten veraendert (Informations-Dialog)

**Tags**: [req-008, notfall-protokoll, schimmel-fund, emergency, sofortmassnahmen]

---

### TC-REQ-008-051: Emergency-Protokoll fuer Uebertrocknung — Rehydrierung anleiten

**Requirement**: REQ-008 § 3 DryingProtocol._get_next_action (over_dried), § 6 DoD (Emergency-Protocols: Uebertrocknung)
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Snap-Test hat Ergebnis OVERDRIED zurueckgegeben oder Gewichtsverlust > 85%

**Testschritte**:
1. Nutzer betrachtet die OVERDRIED-Warnung auf der Batch-Detailseite
2. Nutzer klickt auf den enthaltenen Link "Rehydrierungs-Anleitung" oder "Was jetzt tun?"

**Erwartete Ergebnisse**:
- Anleitung wird angezeigt:
  - "Sofort in Jars mit Boveda-Pack (62%)"
  - "24h warten"
  - "Snap-Test erneut durchfuehren"
- Falls immer noch zu trocken: "Weiteren Boveda-Pack hinzufuegen, 24h warten"

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, uebertrocknung, rehydrierung, boveda, notfall-protokoll]

---

## 11. Authentifizierung & Zugriffsrechte

### TC-REQ-008-052: Nicht-eingeloggter Nutzer wird zu Login weitergeleitet

**Requirement**: REQ-008 § 4 (Authentifizierung & Autorisierung, alle Endpoints erfordern JWT)
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist nicht eingeloggt (kein gueltiges Session-Cookie)

**Testschritte**:
1. Nutzer navigiert direkt zur URL `/post-harvest/batches`

**Erwartete Ergebnisse**:
- Der Nutzer wird zur Login-Seite weitergeleitet
- Nach erfolgreichem Login wird er zur urspruenglich angeforderten Seite weitergeleitet

**Nachbedingungen**:
- Nutzer ist nach Erfolg eingeloggt und auf der Batches-Seite

**Tags**: [req-008, authentifizierung, auth-redirect, sicherheit, sec-h-001]

---

### TC-REQ-008-053: Mitglied darf Trocknungsprozesse lesen und schreiben

**Requirement**: REQ-008 § 4 Authentifizierung (Mitglied = Lesen/Schreiben)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Mitglied" (grower) im aktuellen Tenant
- Mindestens ein Batch existiert im Tenant

**Testschritte**:
1. Nutzer navigiert zu "Post-Harvest" → "Batches"
2. Nutzer oeffnet einen Batch und klickt auf "Gewicht erfassen"
3. Nutzer gibt ein Gewicht ein und klickt "Speichern"

**Erwartete Ergebnisse**:
- Die Liste der Batches wird korrekt angezeigt
- Der Nutzer kann eine neue Gewichtsmessung speichern
- Es erscheint keine "Keine Berechtigung"-Fehlermeldung

**Nachbedingungen**:
- Gewichtsmessung ist gespeichert

**Tags**: [req-008, berechtigung, mitglied, grower, lesen-schreiben]

---

### TC-REQ-008-054: Nur Admin darf Batch loeschen — Mitglied hat keine Loeschen-Schaltflaeche

**Requirement**: REQ-008 § 4 Authentifizierung (Loeschen = Admin only)
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Mitglied" (grower), NICHT Admin
- Ein Batch existiert

**Testschritte**:
1. Nutzer navigiert zur Batch-Detailseite
2. Nutzer sucht nach einer "Loeschen"-Schaltflaeche

**Erwartete Ergebnisse**:
- Die Schaltflaeche "Batch loeschen" ist entweder nicht vorhanden oder ausgegraut
- Kein Loeschen-Icon oder -Button ist fuer einen Nicht-Admin sichtbar/aktiv

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, berechtigung, admin, loeschen-gesperrt, rbac]

---

## 12. Formvalidierungen (Grenzwerte & Eingabe-Checks)

### TC-REQ-008-055: Startgewicht muss groesser als Null sein

**Requirement**: REQ-008 § 3 DryingProtocol (initial_weight_g: Field(gt=0))
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Trocknung starten" ist geoeffnet

**Testschritte**:
1. Nutzer laesst das Feld "Startgewicht" leer oder gibt "0" ein
2. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Validierungsfehlermeldung am Feld: "Startgewicht muss groesser als 0 sein"
- Dialog bleibt geoeffnet, keine Daten werden gespeichert

**Nachbedingungen**:
- Keine Trocknung gestartet

**Tags**: [req-008, formvalidierung, startgewicht, gt-0, trocknung]

---

### TC-REQ-008-056: Aktuelles Gewicht darf nicht groesser als Startgewicht sein

**Requirement**: REQ-008 § 3 DryingProtocol.validate_weight_reduction (current ≤ initial)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Batch ist im Status `drying`, Startgewicht 450 g
- Dialog "Gewicht erfassen" ist geoeffnet

**Testschritte**:
1. Nutzer gibt aktuelles Gewicht "500" g ein (groesser als Startgewicht)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Validierungsfehlermeldung: "Aktuelles Gewicht kann nicht groesser als das Startgewicht sein"
- Kein Gewichtseintrag wird gespeichert

**Nachbedingungen**:
- Kein neuer Gewichtseintrag

**Tags**: [req-008, formvalidierung, gewicht, current-groesser-initial, validierung]

---

### TC-REQ-008-057: Jar-Curing: Anzahl Jars muss zwischen 1 und 100 liegen

**Requirement**: REQ-008 § 3 JarCuringManager (jar_count: Field(ge=1, le=100))
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Curing starten" ist geoeffnet

**Testschritte**:
1. Nutzer gibt Jar-Anzahl "0" ein
2. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Validierungsfehlermeldung: "Anzahl Jars muss zwischen 1 und 100 liegen"
- Dialog bleibt geoeffnet

**Nachbedingungen**:
- Kein Curing gestartet

**Tags**: [req-008, formvalidierung, jar-count, ge-1-le-100]

---

### TC-REQ-008-058: Ziel-RH fuer Curing muss zwischen 55% und 65% liegen

**Requirement**: REQ-008 § 3 JarCuringManager (target_rh_percent: Field(ge=55, le=65))
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Curing starten" ist geoeffnet und zeigt ein optionales Feld fuer Ziel-RH

**Testschritte**:
1. Nutzer gibt Ziel-RH "70" % ein
2. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Validierungsfehlermeldung: "Ziel-RH muss zwischen 55% und 65% liegen"
- Dialog bleibt geoeffnet

**Nachbedingungen**:
- Kein Curing gestartet

**Tags**: [req-008, formvalidierung, ziel-rh, curing, 55-65-prozent]

---

### TC-REQ-008-059: Lagerort-Kapazitaet muss zwischen 0 und 1000 kg liegen

**Requirement**: REQ-008 § 3 StorageLocationManager (capacity_kg: Field(gt=0, le=1000))
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Lagerort anlegen" ist geoeffnet

**Testschritte**:
1. Nutzer gibt Kapazitaet "1500" kg ein
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Validierungsfehlermeldung: "Kapazitaet muss zwischen 0 und 1000 kg liegen"
- Dialog bleibt geoeffnet, kein Lagerort wird erstellt

**Nachbedingungen**:
- Kein neuer Lagerort angelegt

**Tags**: [req-008, formvalidierung, kapazitaet, lagerort, le-1000]

---

### TC-REQ-008-060: Temperaturfeld in Beobachtung: -10°C bis +50°C erlaubt

**Requirement**: REQ-008 § 3 StorageObservation (temperature_c: Field(ge=-10, le=50))
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Beobachtungs-Dialog ist geoeffnet

**Testschritte**:
1. Nutzer gibt Temperatur "60" °C ein
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Validierungsfehlermeldung: "Temperatur muss zwischen -10°C und 50°C liegen"
- Dialog bleibt geoeffnet

**Nachbedingungen**:
- Keine Beobachtung gespeichert

**Tags**: [req-008, formvalidierung, temperatur, beobachtung, ge-minus10-le-50]

---

## 13. Navigation & Listenansichten

### TC-REQ-008-061: Post-Harvest-Batch-Liste zeigt alle Batches des Tenants

**Requirement**: REQ-008 § 4 (Tenant-scoped), alle Batch-Zutaende
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mehrere Batches mit verschiedenen Statuswerten existieren im Tenant (fresh, drying, stored)

**Testschritte**:
1. Nutzer navigiert zu "Post-Harvest" → "Batches"

**Erwartete Ergebnisse**:
- Eine Tabelle zeigt alle Batches des Tenants
- Sichtbare Spalten: Batch-ID, Spezies, Status-Badge (farbkodiert), aktuelles Gewicht, Tage im aktuellen Status
- Status-Badges sind farblich unterschiedlich: "Frisch" (blau), "In Trocknung" (gelb), "Eingelagert" (gruen)
- Tabelle ist sortierbar nach Status und Datum

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, batch-liste, listenansicht, tenant-scoped, status-badges]

---

### TC-REQ-008-062: Post-Harvest-Bereich fuer anderen Tenant zeigt keine Batches

**Requirement**: REQ-008 § 4 (Tenant-scoped), REQ-024 (Mandantentrennung)
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist Mitglied in zwei Tenants: "Garten A" (mit Batches) und "Garten B" (ohne Batches)
- Nutzer ist derzeit in Tenant "Garten B" aktiv

**Testschritte**:
1. Nutzer navigiert zu "Post-Harvest" → "Batches" (in Kontext "Garten B")

**Erwartete Ergebnisse**:
- Die Liste zeigt "Keine Batches vorhanden" oder einen leeren Zustand
- Batches aus "Garten A" sind NICHT sichtbar
- Leerzustand-Message ist klar und benutzerfreundlich

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, tenant-isolierung, req-024, leer-zustand, mandanten]

---

### TC-REQ-008-063: Batch-Detailseite — Navigation mit Tabs

**Requirement**: REQ-008 § 6 DoD (alle Tracking-Bereiche als Tabs erreichbar)
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Batch ist im Status `curing`
- Detailseite hat mehrere Tabs (Trocknung, Curing, Beobachtungen, Trim-Protokoll, Lagerort)

**Testschritte**:
1. Nutzer oeffnet Batch-Detailseite
2. Nutzer klickt auf Tab "Curing"
3. Nutzer klickt auf Tab "Beobachtungen"
4. Nutzer klickt auf Tab "Trim-Protokoll"

**Erwartete Ergebnisse**:
- Jeder Tab-Wechsel zeigt den korrekten Inhalt
- Die URL aktualisiert sich mit dem Tab-Parameter (z.B. `?tab=curing`)
- Nach Browser-Refresh wird derselbe Tab wieder angezeigt
- Keine Daten gehen verloren beim Tab-Wechsel

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, navigation, tabs, url-persistenz, batch-detail]

---

### TC-REQ-008-064: Batch-Uebersichtsbereich im Dashboard-Widget (Storage-Inventar)

**Requirement**: REQ-008 § 5 "Wird benoetigt von" REQ-009 (Dashboard Storage-Inventar-Widget)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Mindestens ein Batch ist im Status `stored`
- Dashboard-Seite hat ein Post-Harvest/Storage-Widget

**Testschritte**:
1. Nutzer navigiert zum Dashboard

**Erwartete Ergebnisse**:
- Ein Widget "Lager-Inventar" oder "Post-Harvest" ist sichtbar
- Es zeigt eine kompakte Uebersicht: Anzahl gelagerter Batches, Gesamtgewicht, naechste Ablaufdaten
- Ein Link "Zum Lager-Inventar" fuehrt zur vollstaendigen Ansicht

**Nachbedingungen**:
- Keine Daten veraendert

**Tags**: [req-008, dashboard, storage-widget, req-009-integration]

---

## 14. Photo-Dokumentation & Jar-ID-System

### TC-REQ-008-065: Foto-Referenzen in Beobachtung speichern (Photo-Comparison)

**Requirement**: REQ-008 § 6 DoD (Photo-Comparison Before/After), § 2 StorageObservation (photo_refs)
**Priority**: Low
**Category**: Happy Path
**Preconditions**:
- Beobachtungs-Dialog ist geoeffnet
- Nutzer hat ein Foto hochgeladen oder eine URL eingegeben

**Testschritte**:
1. Nutzer klickt im Beobachtungs-Dialog auf "Foto hinzufuegen"
2. Nutzer waehlt ein Bild aus (JPEG, max. 5 MB)
3. Nutzer speichert die Beobachtung

**Erwartete Ergebnisse**:
- Das Foto-Thumbnail ist in der Beobachtungs-Zeile der Verlaufstabelle sichtbar
- Klick auf das Thumbnail oeffnet eine Vorschau in voller Groesse
- In der Verlaufstabelle koennen mehrere Beobachtungen mit Fotos verglichen werden ("Before/After"-Ansicht bei Auswahl zweier Eintraege)

**Nachbedingungen**:
- Foto-Referenz in der Beobachtung gespeichert

**Tags**: [req-008, foto-dokumentation, photo-refs, before-after, beobachtung]

---

### TC-REQ-008-066: Jar-ID-System — QR-Code fuer Glas generieren

**Requirement**: REQ-008 § 6 DoD (Jar-ID-System mit QR-Codes)
**Priority**: Low
**Category**: Dialog
**Preconditions**:
- Batch ist im Status `curing`
- Jar-Curing laeuft mit mehreren Jars

**Testschritte**:
1. Nutzer oeffnet Tab "Curing" auf der Batch-Detailseite
2. Nutzer klickt auf "Jar-Labels generieren" oder "QR-Codes erstellen"
3. Ein Dialog zeigt QR-Codes fuer jedes Glas (z.B. Jar 1 von 4, Jar 2 von 4, ...)

**Erwartete Ergebnisse**:
- Fuer jedes Glas wird ein QR-Code angezeigt
- Der QR-Code kodiert die Batch-ID und eine Jar-Nummer
- Ein Drucken-Button ermoeglicht das Ausdrucken der Labels
- Alternativ: Download als PDF

**Nachbedingungen**:
- Keine Daten veraendert (QR-Codes sind generiert)

**Tags**: [req-008, jar-id, qr-code, labels, curing, drucken]

---

## 15. Grenzwert-Tests & Edge Cases

### TC-REQ-008-067: Trocknungs-Fortschritt bei genau 95% — "Bereit fuer Curing"-Status

**Requirement**: REQ-008 § 3 DryingProtocol.calculate_dryness_progress (ready_for_curing bei ≥95%)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Batch ist im Status `drying`
- Startgewicht: 450 g, Zielgewicht: 45 g (10% Restfeuchte = 90% Verlust)

**Testschritte**:
1. Nutzer gibt Gewicht "47" g ein (entspricht ~95% Trocknungsfortschritt)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fortschrittsbalken zeigt ≥95% (gruen)
- Status-Meldung: "BEREIT — Jetzt Jar-Curing starten"
- Schaltflaeche "Curing starten" wird aktiv/hervorgehoben
- Geschaetzte verbleibende Tage: 0

**Nachbedingungen**:
- Dryness Progress zeigt "bereit"

**Tags**: [req-008, grenzwert, 95-prozent, curing-bereit, trocknungsfortschritt]

---

### TC-REQ-008-068: Gleichzeitiger Zugriff — UnsavedChanges-Guard bei Navigation weg vom Formular

**Requirement**: REQ-008 (allgemeines Formular-Guard-Pattern des Frontends)
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Nutzer hat das Burping-Formular geoeffnet und RH-Werte eingegeben
- Nutzer hat noch nicht gespeichert

**Testschritte**:
1. Nutzer hat im Burping-Dialog Werte eingegeben aber NICHT gespeichert
2. Nutzer klickt im Seitennavigationsmenue auf "Dashboard"

**Erwartete Ergebnisse**:
- Ein Browser-Dialog oder ein MUI-Bestaedigungsdialog erscheint: "Sie haben ungespeicherte Aenderungen. Moechten Sie die Seite wirklich verlassen?"
- Nutzer klickt "Abbrechen" → verbleibt auf der aktuellen Seite, Formulardaten bleiben erhalten
- Nutzer klickt "Verlassen" → Navigation wird ausgefuehrt, Formulardaten werden verworfen

**Nachbedingungen**:
- Abhaengig von Nutzer-Entscheidung

**Tags**: [req-008, unsaved-changes, guard, navigation, formular-schutz]

---

## Abdeckungs-Matrix

| Spec-Abschnitt | Funktionsbereich | Testfall-IDs |
|---|---|---|
| § 1 Trocknungs-Prozesse (Cannabis, Pilze, Zwiebel, Tomate) | Spezies-Guides | TC-008-012 bis TC-008-014, TC-008-044 bis TC-008-048 |
| § 1 Curing-Prozesse (Jar-Curing, Sauerkraut, Kimchi) | Jar-Curing-Assistent, Fermentation | TC-008-015 bis TC-008-022, TC-008-047 |
| § 1 Lagerung (Temperatur-Zonen, RH-Zonen) | Lager-Inventar | TC-008-031 bis TC-008-036 |
| § 2 Batch-Status-Machine (U-006) | Statusuebergaenge | TC-008-001 bis TC-008-005 |
| § 2 DryingProgress-Node | Trocknungs-Tracking | TC-008-006 bis TC-008-011 |
| § 2 BurpingEvent-Node | Burping-Erfassung | TC-008-018 |
| § 2 TrimProtocol-Node (U-007) | Trim-Protokoll | TC-008-037 bis TC-008-039 |
| § 2 MoldAlert-Node | Schimmel-Alert | TC-008-023 bis TC-008-024 |
| § 2 StorageObservation-Node | Beobachtungen | TC-008-040 bis TC-008-043 |
| § 3 DryingProtocol (Snap-Test P-002) | Snap-Test-Assistent | TC-008-007 bis TC-008-009 |
| § 3 JarCuringManager (Burping-Schedule) | Burping-Zeitplan | TC-008-015 bis TC-008-017, TC-008-019 bis TC-008-021 |
| § 3 MoldPreventionMonitor | Schimmel-Praeventons-Assistent | TC-008-025 bis TC-008-030 |
| § 3 TrimProtocol | Trim-Validierungen | TC-008-037 bis TC-008-039 |
| § 3 ShelfLifeEstimator (P-001, P-004, P-005) | Haltbarkeitsprognose | TC-008-032 bis TC-008-034, TC-008-046 |
| § 3 GrowingSystemModifier (U-002) | Anbausystem-Hinweise | TC-008-014 |
| § 3 CO2Monitor (U-005) | CO2-Ueberwachung | TC-008-029 bis TC-008-030 |
| § 3 LightDegradationManager (U-008) | UV/Licht-Degradation | TC-008-044, TC-008-045, TC-008-049 |
| § 4 Authentifizierung & Autorisierung | Auth & RBAC | TC-008-052 bis TC-008-054 |
| § 5 Karenz-Gate (REQ-010) | Sicherheits-Gate | TC-008-003 |
| § 6 DoD — Emergency-Protokolle | Notfall-Guides | TC-008-050 bis TC-008-051 |
| § 6 DoD — Jar-ID-System, QR-Codes | Jar-Labels | TC-008-066 |
| § 6 DoD — Photo-Comparison | Foto-Dokumentation | TC-008-065 |
| Formvalidierungen (alle Modelle) | Grenzwerte & Validierung | TC-008-055 bis TC-008-060 |
| Navigation & UI-Patterns | Listenansichten, Tabs, Guard | TC-008-061 bis TC-008-064, TC-008-068 |
| Grenzwert 95% Trocknungsfortschritt | Edge Case | TC-008-067 |
