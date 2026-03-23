---
req_id: REQ-017
title: Vermehrungsmanagement & Genetische Rueckverfolgbarkeit
category: Pflanzenvermehrung
test_count: 72
coverage_areas:
  - Vermehrungsevents-Liste (/vermehrung/events) — 12 Methoden, Filter, Paginierung
  - Vermehrungsevent erstellen (CreateDialog) — alle 12 PropagationMethods
  - Stecklingstyp-Differenzierung (CuttingType) — apical, nodal, heel, softwood, semi_hardwood, hardwood, leaf_petiole, leaf_section
  - Ergebnis-Nachtragung (Outcome Dialog) — survived_count, failure_reasons
  - Fortschritts-Tracking (Progress Update) — callus/roots/transplant Zeitpunkte
  - Bewurzelungsprotokolle-Liste (/vermehrung/protokolle) — Templates und individuelle Protokolle
  - Bewurzelungsprotokoll erstellen/bearbeiten — Temperaturvalidierung, PPFD-Warnung, Timeline
  - Vermehrungsbatches-Liste (/vermehrung/batches) — Status, Methode, Filter
  - Batch erstellen und Events zuordnen
  - Batch finalisieren und an PlantingRun uebergeben
  - Mutterpflanzen-Liste (/vermehrung/mutterpflanzen) — Gesundheits-Score, Stecklingshistorie
  - Mutterpflanze designieren (Designate-Dialog auf PlantInstance-Detailseite)
  - Mutterpflanze pensionieren (Retire-Dialog)
  - Gesundheitsbewertung aktualisieren
  - Retirement-Empfehlung als Warnung im UI
  - Abstammungsgraph (Lineage-Tab auf PlantInstance-Detailseite)
  - Nachkommen-Ansicht (Descendants-Tab)
  - Phänotyp-Notizen (Phenotype-Tab auf PlantInstance-Detailseite)
  - Phänotyp-Notiz erstellen und loeschen
  - Veredelungs-Kompatibilitaetspruefung (GraftCompatibility-Dialog)
  - IPM-Felder (Werkzeugsterilisation, Quarantaene, Virusstatus-Warnung)
  - Somatische Mutationslast-Warnung (ab Generation 10)
  - Erholungszeit-Warnung (bei zu fruehzeitiger Stecklingnahme)
  - Statistiken-Dashboard (/vermehrung/statistiken)
  - Validierungsmeldungen (Hormone-Konzentration, Temperatur-Delta, Timeline)
  - Authentifizierung und Zugriffskontrolle
generated: 2026-03-21
version: "1.2"
---

# TC-REQ-017: Vermehrungsmanagement & Genetische Rueckverfolgbarkeit

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-017 Vermehrungsmanagement v1.2**,
ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes
oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der
Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). REQ-017 ist zum Zeitpunkt der Erstellung
spezifiziert, aber noch nicht im Frontend implementiert. Diese Testfaelle definieren das
**erwartete UI-Verhalten** als Grundlage fuer die Implementierung und spaetere Selenium-/Playwright-Automatisierung.

Die primaeren UI-Bereiche sind:
- `/vermehrung/events` — Vermehrungsevent-Liste
- `/vermehrung/batches` — Vermehrungsbatch-Liste
- `/vermehrung/protokolle` — Bewurzelungsprotokoll-Liste
- `/vermehrung/mutterpflanzen` — Mutterpflanzen-Uebersicht
- `/vermehrung/statistiken` — Erfolgsraten-Dashboard
- Tabs auf PlantInstance-Detailseite: "Abstammung", "Nachkommen", "Phaenotyp"

---

## 1. Vermehrungsevents-Liste und Navigation

### TC-017-001: Vermehrungsevents-Liste oeffnen und Grundzustand pruefen

**Requirement**: REQ-017 § 6 DoD — PropagationEvent-CRUD
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Mitglied
- Mindestens 3 PropagationEvents verschiedener Methoden existieren (z.B. cutting, seed_sowing, water_propagation)
- Kein aktiver Suchfilter

**Testschritte**:
1. Nutzer navigiert zur Vermehrungsevents-Liste via Seitenleiste "Vermehrung" → "Events" oder URL `/vermehrung/events`
2. Nutzer betrachtet die angezeigte Tabelle

**Erwartete Ergebnisse**:
- Seitenheader zeigt "Vermehrungsevents"
- Eine Datentabelle ist sichtbar mit Spalten: Datum, Methode, Anzahl, Ueberlebt, Erfolgsrate, Quelle, Status
- Alle 3 Events sind aufgelistet mit korrekter Methoden-Bezeichnung (z.B. "Steckling", "Aussaat", "Wasserbewurzelung")
- Ein Button "Neues Event" ist sichtbar
- Paginierungssteuerung ist vorhanden
- Suchfeld "Tabelle durchsuchen..." ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, events-liste, navigation, grundzustand]

---

### TC-017-002: Vermehrungsevents nach Methode filtern

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/events (Filter: method)
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist auf der Events-Listenseite `/vermehrung/events`
- Events verschiedener Methoden existieren: 5x cutting, 3x seed_sowing, 2x water_propagation

**Testschritte**:
1. Nutzer klickt auf den Methoden-Filter-Dropdown (Label: "Methode")
2. Nutzer waehlt "Steckling" (cutting)
3. Nutzer betrachtet die aktualisierte Tabelle

**Erwartete Ergebnisse**:
- Tabelle zeigt nur die 5 Stecklingsereignisse
- Filteranzeige zeigt "Methode: Steckling" als aktiven Filter
- Andere Methoden sind aus der Tabelle verschwunden
- Zeilenanzeige zeigt "Zeigt 1–5 von 5 Eintraegen"

**Nachbedingungen**:
- Filter bleibt aktiv bis Nutzer ihn entfernt

**Tags**: [req-017, events-liste, filter, methode, cutting]

---

### TC-017-003: Vermehrungsevent-Detailansicht oeffnen

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/events/{event_key}
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist auf der Events-Listenseite
- PropagationEvent "prop_evt_001" existiert (10 Cannabis-Stecklinge, Protokoll "Cannabis Steckling Standard")

**Testschritte**:
1. Nutzer klickt auf den Tabelleneintrag fuer Event "prop_evt_001" (z.B. "10 Stecklinge von GSC Mutter #1")
2. Nutzer betrachtet die Detailansicht

**Erwartete Ergebnisse**:
- Detailseite oder Seitenleisten-Panel oeffnet sich
- Event-Typ "Steckling (apikaler Trieb)" ist sichtbar
- Datum und Uhrzeit der Entnahme sind angezeigt
- Anzahl entnommener Stecklinge: "10"
- Ueberlebt: "—" (noch nicht nachgetragen) oder aktueller Wert
- Quellpflanze ist als verlinkter Name angezeigt (z.B. "GSC Mutter #1")
- Verwendetes Protokoll ist verlinkt: "Cannabis Steckling Standard"
- Bewurzelungsparameter sind aufgelistet: Medium (Steinwolle), Luftfeuchtigkeit (85%), Temperatur (20°C Luft / 22°C Substrat), PPFD (100), VPD-Ziel (0.4 kPa)
- IPM-Felder: Werkzeugsterilisation, Quarantaene-Status
- Fortschritts-Meilensteine: Kallus, Wurzeln, Transplant-bereit (jeweils mit Datum oder "—")
- Button "Ergebnis nachtragen" ist sichtbar
- Button "Fortschritt aktualisieren" ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, event-detail, detailansicht, protokoll, parameter]

---

## 2. Vermehrungsevent erstellen — alle 12 Methoden

### TC-017-004: Stecklingsevent mit Protokoll-Vorlage erstellen (Happy Path)

**Requirement**: REQ-017 § 6 DoD — PropagationEvent-CRUD, Stecklingstyp-Differenzierung
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Mitglied
- PlantInstance "GSC Mutter #1" (is_mother=true) existiert
- Bewurzelungsprotokoll "Cannabis Steckling Standard" (proto_cannabis_std) existiert als Vorlage
- Letzte Stecklingnahme von GSC Mutter #1 war vor mehr als 14 Tagen

**Testschritte**:
1. Nutzer navigiert zu `/vermehrung/events`
2. Nutzer klickt auf Button "Neues Event"
3. Der Erstellungs-Dialog oeffnet sich
4. Nutzer waehlt im Feld "Vermehrungsmethode" den Wert "Steckling"
5. Das Feld "Stecklingstyp" wird sichtbar
6. Nutzer waehlt "Triebspitze (apikal)"
7. Nutzer klickt auf "Protokoll-Vorlage laden" und waehlt "Cannabis Steckling Standard"
8. Die Bewurzelungsparameter werden automatisch aus dem Protokoll befuellt
9. Nutzer waehlt im Feld "Quellpflanze" den Eintrag "GSC Mutter #1"
10. Nutzer gibt im Feld "Anzahl" den Wert "8" ein
11. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Kein Warnbanner erscheint (Erholungszeit eingehalten)
- Erfolgsmeldung (Snackbar): "Vermehrungsevent wurde erstellt"
- Dialog schliesst sich
- Neuer Eintrag erscheint in der Events-Liste: "8 Stecklinge (apikal)", Datum heute
- Bewurzelungsparameter aus Protokoll sind gespeichert: Steinwolle, 85% LF, 20°C Luft, 22°C Substrat, 100 PPFD, VPD 0.4 kPa
- Quellpflanze "GSC Mutter #1" ist verlinkt

**Nachbedingungen**:
- PropagationEvent in der Liste sichtbar
- Erholungszeit-Zaehler fuer GSC Mutter #1 wurde zurueckgesetzt

**Tags**: [req-017, event-erstellen, cutting, protokoll, happy-path]

---

### TC-017-005: Stecklingsevent ohne Protokoll-Vorlage manuell erfassen

**Requirement**: REQ-017 § 2 PropagationEvent Properties
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Mitglied
- PlantInstance "Tomate Sorrento #3" existiert (kein Mutterpflanzenstatus)

**Testschritte**:
1. Nutzer oeffnet den Erstellungs-Dialog via "Neues Event"
2. Nutzer waehlt Methode: "Steckling", Stecklingstyp: "Halbverholzt (semi_hardwood)"
3. Nutzer waehlt Quellpflanze: "Tomate Sorrento #3"
4. Nutzer gibt Anzahl: "4" ein
5. Nutzer waehlt Medium: "Steinwolle"
6. Nutzer gibt Lufttemperatur: "22" °C und Substrattemperatur: "24" °C ein
7. Nutzer gibt PPFD: "150" ein
8. Nutzer waehlt Hormon-Typ: "Keine" (none)
9. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Warnhinweis erscheint (gelb, nicht blockierend): "Pflanze ist nicht als Mutterpflanze markiert — Stecklingsnahme trotzdem moeglich, aber empfohlen zuerst zu designieren"
- Nutzer bestaetigt trotzdem
- Erfolgsmeldung (Snackbar): "Vermehrungsevent wurde erstellt"
- Event erscheint in der Liste mit korrekt erfassten Parametern

**Nachbedingungen**:
- PropagationEvent in der Liste sichtbar

**Tags**: [req-017, event-erstellen, cutting, warnung, nicht-mutterpflanze]

---

### TC-017-006: Aussaat-Event mit Mutter- und Vaterpflanze dokumentieren

**Requirement**: REQ-017 § 6 Testszenario 6 — Aussaat mit Kreuzungs-Dokumentation
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Mitglied
- PlantInstance "Haze Mother" (is_mother=true, Cannabis) existiert
- PlantInstance "Kush Father" (Cannabis, Pollenspender) existiert
- Bewurzelungsprotokoll "Standard-Aussaat Indoor" (proto_seed_general) existiert

**Testschritte**:
1. Nutzer oeffnet den Erstellungs-Dialog via "Neues Event"
2. Nutzer waehlt Methode: "Aussaat"
3. Feld "Stecklingstyp" ist nicht sichtbar (nur bei Methode "Steckling")
4. Nutzer waehlt Mutterpflanze (Samen-Traegerin): "Haze Mother"
5. Das Feld "Vaterpflanze (Pollenspender)" wird sichtbar
6. Nutzer waehlt Vaterpflanze: "Kush Father"
7. Nutzer gibt Anzahl Samen: "20" ein
8. Nutzer laedt Protokoll: "Standard-Aussaat Indoor"
9. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Vermehrungsevent wurde erstellt"
- Ereignis zeigt Methode "Aussaat", 20 Samen
- Mutterpflanze "Haze Mother" und Vaterpflanze "Kush Father" sind verlinkt
- In der Detailansicht sind beide Elternteile mit ihren Rollen (Mutter/Vater) angezeigt

**Nachbedingungen**:
- PropagationEvent mit Kreuzungs-Dokumentation in der Liste sichtbar

**Tags**: [req-017, aussaat, kreuzung, mutter-vater, seed-sowing, happy-path]

---

### TC-017-007: Zimmerpflanzen-Methoden — Blattsteckling (leaf_cutting) erstellen

**Requirement**: REQ-017 § 6 DoD — Zimmerpflanzen-Methoden
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt
- PlantInstance "Sansevieria trifasciata #1" existiert

**Testschritte**:
1. Nutzer oeffnet den Erstellungs-Dialog
2. Nutzer waehlt Methode: "Blattsteckling"
3. Das Feld "Stecklingstyp" zeigt speziell fuer Blattstecklinge geeignete Typen (leaf_petiole, leaf_section) oder ist nicht vorhanden
4. Nutzer waehlt Quellpflanze: "Sansevieria trifasciata #1"
5. Nutzer laedt Protokoll: "Sansevieria Blattsteckling"
6. Felder werden befuellt: Medium Perlit, 50% Luftfeuchtigkeit, 22°C Luft, 24°C Substrat
7. Nutzer gibt Anzahl: "6" (Blattsegmente) ein
8. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Vermehrungsevent wurde erstellt"
- Event zeigt Methode "Blattsteckling", 6 Stueck
- Alle Protokoll-Parameter korrekt uebernommen

**Nachbedingungen**:
- PropagationEvent in der Liste sichtbar

**Tags**: [req-017, blattsteckling, leaf-cutting, zimmerpflanze, sansevieria]

---

### TC-017-008: Abmoosen (air_layering) — Zimmerpflanzen-Methode erstellen

**Requirement**: REQ-017 § 6 DoD — Zimmerpflanzen-Methoden (air_layering)
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt
- PlantInstance "Monstera deliciosa #2" existiert

**Testschritte**:
1. Nutzer oeffnet den Erstellungs-Dialog
2. Nutzer waehlt Methode: "Abmoosen (air_layering)"
3. Nutzer waehlt Quellpflanze: "Monstera deliciosa #2"
4. Nutzer laedt Protokoll: "Monstera Abmoosen"
5. Nutzer gibt Anzahl: "1" ein
6. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Vermehrungsevent wurde erstellt"
- Event zeigt Methode "Abmoosen", 1 Stueck
- Protokoll-Anleitung ist in der Detailansicht abrufbar

**Nachbedingungen**:
- PropagationEvent in der Liste sichtbar

**Tags**: [req-017, abmoosen, air-layering, zimmerpflanze, monstera]

---

### TC-017-009: Wasserbewurzelung (water_propagation) erstellen

**Requirement**: REQ-017 § 6 DoD — Zimmerpflanzen-Methoden (water_propagation)
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt
- PlantInstance "Pothos aureum #1" existiert

**Testschritte**:
1. Nutzer oeffnet den Erstellungs-Dialog
2. Nutzer waehlt Methode: "Wasserbewurzelung"
3. Nutzer waehlt Quellpflanze: "Pothos aureum #1"
4. Nutzer laedt Protokoll: "Pothos/Philodendron Wasserbewurzelung"
5. Nutzer gibt Anzahl: "3" ein
6. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Vermehrungsevent wurde erstellt"
- Event zeigt Methode "Wasserbewurzelung", Medium "Wasser"

**Nachbedingungen**:
- PropagationEvent in der Liste sichtbar

**Tags**: [req-017, wasserbewurzelung, water-propagation, pothos]

---

## 3. Ergebnis-Nachtragung und Fortschritts-Tracking

### TC-017-010: Bewurzelungs-Fortschritt aktualisieren — Kallus sichtbar (Happy Path)

**Requirement**: REQ-017 § 3 REST-API — PATCH /events/{key}/progress; § 6 Testszenario 2
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von PropagationEvent "prop_evt_001"
- 10 Cannabis-Stecklinge, gestartet vor 5 Tagen, callus_observed_at = null
- roots_observed_at = null, transplant_ready_at = null

**Testschritte**:
1. Nutzer klickt auf Button "Fortschritt aktualisieren"
2. Ein Dialog oeffnet sich mit drei Datumspicker-Feldern: "Kallus beobachtet am", "Wurzeln beobachtet am", "Transplant-bereit am"
3. Nutzer waehlt im Feld "Kallus beobachtet am" das Datum von heute
4. Felder "Wurzeln beobachtet am" und "Transplant-bereit am" bleiben leer
5. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgsmeldung (Snackbar): "Fortschritt aktualisiert"
- In der Detailansicht zeigt "Kallus beobachtet am" das eingegebene Datum
- "Wurzeln beobachtet am" und "Transplant-bereit am" zeigen weiterhin "—"
- Fortschritts-Stepper oder Timeline wird aktualisiert

**Nachbedingungen**:
- callus_observed_at gesetzt, roots/transplant noch leer

**Tags**: [req-017, fortschritt, kallus, progress-update, happy-path]

---

### TC-017-011: Bewurzelungs-Fortschritt — Zeitreihen-Validierung schlaegt fehl

**Requirement**: REQ-017 § 3 PropagationEvent model_validator — Timeline-Validierung
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von PropagationEvent "prop_evt_001"
- callus_observed_at = 2026-02-20 (bereits gesetzt)
- roots_observed_at = null

**Testschritte**:
1. Nutzer klickt auf "Fortschritt aktualisieren"
2. Nutzer traegt im Feld "Wurzeln beobachtet am" das Datum 2026-02-18 ein (VOR dem Kallus-Datum)
3. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung (rot, am Datumsfeld oder als Snackbar): "Wurzeln-Datum (18.02.2026) darf nicht vor Kallus-Datum (20.02.2026) liegen"
- Der Dialog bleibt offen, Daten werden nicht gespeichert
- Datumspicker-Feld "Wurzeln beobachtet am" ist visuell als fehlerhaft markiert

**Nachbedingungen**:
- Kein Fortschritt geaendert

**Tags**: [req-017, formvalidierung, timeline, datum-reihenfolge, fehler]

---

### TC-017-012: Ergebnis-Nachtragung — Ueberlebt-Anzahl und Misserfolgs-Gruende eintragen

**Requirement**: REQ-017 § 6 Testszenario 2 — Ergebnis-Nachtragung; DoD Ergebnis-Nachtragung
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von PropagationEvent "prop_evt_001" (10 Stecklinge, kein Ergebnis bisher)
- roots_observed_at wurde bereits gesetzt

**Testschritte**:
1. Nutzer klickt auf Button "Ergebnis nachtragen"
2. Ein Dialog oeffnet sich
3. Nutzer gibt im Feld "Ueberlebt" den Wert "8" ein
4. Nutzer waehlt in der Mehrfachauswahl "Misserfolgs-Gruende": "Faeulnis (rot)" und "Kein Wurzelwachstum (no_roots)"
5. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Ergebnis wurde eingetragen"
- Dialog schliesst sich
- In der Detailansicht: "Ueberlebt: 8 von 10" mit Erfolgsrate "80%"
- Misserfolge: "2 Ausfaelle (Faeulnis, Kein Wurzelwachstum)"
- Erfolgsrate wird auch in der Events-Liste aktualisiert

**Nachbedingungen**:
- survived_count=8, success_rate=0.8, failure_count=2, failure_reasons=[rot, no_roots]

**Tags**: [req-017, ergebnis, survived-count, failure-reasons, success-rate, happy-path]

---

### TC-017-013: Ergebnis-Nachtragung — Ueberlebt-Anzahl groesser als Gesamt schlaegt fehl

**Requirement**: REQ-017 § 3 PropagationEvent model_validator validate_success_rate
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Ergebnis-Nachtragen-Dialog fuer ein Event mit quantity=10

**Testschritte**:
1. Nutzer gibt im Feld "Ueberlebt" den Wert "12" ein (mehr als die 10 entnommenen Stecklinge)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung am Feld: "Anzahl Ueberlebter (12) kann nicht groesser sein als Gesamtanzahl (10)"
- Formular bleibt offen, Speichern wird verhindert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, formvalidierung, survived-count, grenzwert, fehler]

---

## 4. Bewurzelungsprotokolle

### TC-017-014: Bewurzelungsprotokolle-Liste oeffnen und Vorlagen anzeigen

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/protocols; Seed-Daten
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- 10 System-Protokoll-Vorlagen existieren (Seed-Daten aus REQ-017 §3)

**Testschritte**:
1. Nutzer navigiert zu `/vermehrung/protokolle`
2. Nutzer betrachtet die Liste

**Erwartete Ergebnisse**:
- Seitenheader "Bewurzelungsprotokolle" ist sichtbar
- 10 Protokolle sind aufgelistet, darunter: "Cannabis Steckling Standard", "Tomate Steinwolle Rapid", "Basilikum Wasserglas", "Pothos/Philodendron Wasserbewurzelung", "Sansevieria Blattsteckling", "Monstera Abmoosen", "Aloe/Haworthia Kindel-Abtrennung", "Rose Hartholz-Steckling Winter", "Erdbeere Ableger/Auslaeufer", "Standard-Aussaat Indoor"
- Vorlagen-Protokolle sind mit einem "Vorlage"-Badge gekennzeichnet
- Spalten: Name, Methode, Medium, Erwartete Bewurzelungszeit, Vorlage (Ja/Nein)
- Button "Neues Protokoll" ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, protokolle-liste, seed-daten, vorlagen]

---

### TC-017-015: Neues Bewurzelungsprotokoll erstellen (Happy Path)

**Requirement**: REQ-017 § 3 REST-API — POST /api/v1/propagation/protocols
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist auf der Protokoll-Listenseite
- Keine besonderen Vorbedingungen

**Testschritte**:
1. Nutzer klickt auf "Neues Protokoll"
2. Der Erstellungs-Dialog oeffnet sich
3. Nutzer gibt Name: "Mein Cannabis Protokoll v2" ein
4. Nutzer waehlt Methode: "Steckling"
5. Nutzer waehlt empfohlene Stecklingstypen: "Triebspitze (apikal)", "Nodal"
6. Nutzer waehlt Medium: "Steinwolle"
7. Nutzer gibt Lufttemperatur: "20" °C ein
8. Nutzer gibt Substrattemperatur: "23" °C ein (Delta 3°C — im empfohlenen Bereich 2–5°C)
9. Nutzer gibt PPFD: "100" ein
10. Nutzer waehlt Lichtspektrum: "Kuehlweiss (cool_white)"
11. Nutzer gibt Beleuchtungsdauer: "18" Stunden ein
12. Nutzer gibt Luuftfeuchtigkeit: "85" % ein
13. Nutzer gibt VPD-Ziel: "0.4" kPa ein
14. Nutzer gibt erwartete Kallus-Bildung: "5" Tage ein
15. Nutzer gibt erwartete Bewurzelung: "10" Tage ein
16. Nutzer gibt erwartete Transplant-Bereitschaft: "14" Tage ein
17. Nutzer gibt Anleitung: "Schritt-fuer-Schritt-Anleitung hier..." ein
18. Nutzer aktiviert Checkbox "Als Vorlage speichern"
19. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Protokoll wurde erstellt"
- Dialog schliesst sich
- Neues Protokoll "Mein Cannabis Protokoll v2" erscheint in der Liste mit Vorlage-Badge
- Temperatur-Delta wird korrekt als 3°C angezeigt (kein Warnhinweis)

**Nachbedingungen**:
- RootingProtocol in der Liste sichtbar und als Vorlage bei Event-Erstellung verfuegbar

**Tags**: [req-017, protokoll-erstellen, vorlage, happy-path]

---

### TC-017-016: Protokoll-Validierung — Temperaturgradient ueber 8°C wird blockiert

**Requirement**: REQ-017 § 3 RootingProtocol model_validator validate_bottom_heat_delta
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Protokoll-Erstellungs-Dialog

**Testschritte**:
1. Nutzer gibt Lufttemperatur: "20" °C ein
2. Nutzer gibt Substrattemperatur: "30" °C ein (Delta 10°C — ueber der 8°C-Grenze)
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint (rot): "Temperaturgradient Substrat/Luft (10.0°C) ist groesser als 8°C — Stress durch extremen Temperaturgradient. Empfohlen: 2–5°C."
- Formular bleibt offen
- Speichern wird blockiert

**Nachbedingungen**:
- Kein Protokoll erstellt

**Tags**: [req-017, formvalidierung, temperatur-delta, bottom-heat, fehler]

---

### TC-017-017: Protokoll-Validierung — Substrattemperatur unter Lufttemperatur

**Requirement**: REQ-017 § 3 RootingProtocol model_validator validate_bottom_heat_delta
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Protokoll-Erstellungs-Dialog

**Testschritte**:
1. Nutzer gibt Lufttemperatur: "25" °C ein
2. Nutzer gibt Substrattemperatur: "20" °C ein (Substrat kaelter als Luft)
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Substrattemperatur (Bottom Heat) sollte gleich oder waermer als Lufttemperatur sein"
- Formular bleibt offen, Speichern blockiert

**Nachbedingungen**:
- Kein Protokoll erstellt

**Tags**: [req-017, formvalidierung, bottom-heat, temperatur, fehler]

---

### TC-017-018: Protokoll-Validierung — PPFD ueber 150 unter Dome erzeugt Warnhinweis

**Requirement**: REQ-017 § 1 Bewurzelungs-Protokolle — Warnung >150 PPFD unter Dome (Photoinhibition)
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Protokoll-Erstellungs-Dialog

**Testschritte**:
1. Nutzer gibt PPFD: "200" ein (ueber dem 150-Schwellenwert)
2. Nutzer sieht sofort (oder beim Verlassen des Feldes) einen Warnhinweis

**Erwartete Ergebnisse**:
- Gelber Warnhinweis erscheint unterhalb des PPFD-Felds: "PPFD ueber 150 unter Dome kann Photoinhibition bei wurzellosen Stecklingen verursachen. Empfohlen: max. 150 PPFD."
- Das Formular kann trotzdem gespeichert werden (Warnung, kein Fehler)

**Nachbedingungen**:
- Bei Bestaetigung: Protokoll wird mit dem hoeheren PPFD-Wert gespeichert

**Tags**: [req-017, ppfd, photoinhibition, warnung, dome]

---

### TC-017-019: Protokoll-Validierung — Timeline-Reihenfolge verletzt (Kallus nach Wurzeln)

**Requirement**: REQ-017 § 3 RootingProtocol model_validator validate_timeline_order
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Protokoll-Erstellungs-Dialog

**Testschritte**:
1. Nutzer gibt erwartete Kallus-Bildung: "10" Tage ein
2. Nutzer gibt erwartete Bewurzelung: "8" Tage ein (frueher als Kallus)
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Erwartete Kallus-Bildung (10 Tage) muss vor erwarteter Bewurzelung (8 Tage) liegen"
- Formular bleibt offen

**Nachbedingungen**:
- Kein Protokoll erstellt

**Tags**: [req-017, formvalidierung, protokoll, timeline, reihenfolge]

---

### TC-017-020: Protokoll-Statistiken einsehen

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/protocols/{key}/stats; Testszenario 8
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von Protokoll "Cannabis Steckling Standard"
- Protokoll wurde in 15 Events verwendet (Cannabis 10x avg 82%, Tomate 3x avg 90%, Basilikum 2x avg 95%)

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Protokolls "Cannabis Steckling Standard"
2. Nutzer klickt auf den Tab "Statistiken"

**Erwartete Ergebnisse**:
- Tab "Statistiken" zeigt:
  - Gesamt-Events: "15"
  - Gesamt-Erfolgsrate: "85.3%"
  - Aufschluesselung nach Spezies:
    - Cannabis sativa: 10 Events, Durchschnitt 82%
    - Solanum lycopersicum: 3 Events, Durchschnitt 90%
    - Ocimum basilicum: 2 Events, Durchschnitt 95%
  - Ein Balkendiagramm oder Tabelle visualisiert die Daten

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, protokoll-statistiken, erfolgsraten, spezies]

---

## 5. Vermehrungsbatches

### TC-017-021: Vermehrungsbatch erstellen (Happy Path)

**Requirement**: REQ-017 § 3 REST-API — POST /api/v1/propagation/batches
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Mitglied
- Keine besonderen Vorbedingungen

**Testschritte**:
1. Nutzer navigiert zu `/vermehrung/batches`
2. Nutzer klickt auf "Neuer Batch"
3. Dialog oeffnet sich
4. Nutzer gibt Name: "GSC-Klone Fruehling 2026" ein
5. Nutzer waehlt Methode: "Steckling"
6. Nutzer gibt Startdatum: "15.02.2026" ein
7. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Batch wurde erstellt"
- Neuer Batch "GSC-Klone Fruehling 2026" erscheint in der Liste mit Status "In Bearbeitung"
- Batch-Detailseite zeigt: Name, Methode, Startdatum, Status "in_progress"

**Nachbedingungen**:
- PropagationBatch in der Liste sichtbar, Status "in_progress"

**Tags**: [req-017, batch-erstellen, happy-path]

---

### TC-017-022: Event zu einem Batch hinzufuegen

**Requirement**: REQ-017 § 2 Edge part_of_batch — Batch-Zuordnung
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Batch "GSC-Klone Fruehling 2026" (Status "in_progress") existiert
- Neues PropagationEvent "10 Cannabis-Stecklinge" wurde gerade erstellt

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Batches "GSC-Klone Fruehling 2026"
2. Nutzer klickt auf "Event hinzufuegen"
3. Ein Dialog oder Dropdown zeigt verfuegbare Events ohne Batch-Zuordnung
4. Nutzer waehlt das Event "10 Cannabis-Stecklinge von GSC Mutter #1 (15.02.2026)"
5. Nutzer bestaetigt die Zuordnung

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Event wurde zum Batch hinzugefuegt"
- Event erscheint in der Batch-Detailansicht unter "Enthaltene Events"
- Gesamtmenge des Batches aktualisiert sich auf "10"

**Nachbedingungen**:
- Event ist dem Batch zugeordnet (part_of_batch-Edge)

**Tags**: [req-017, batch, event-zuordnen, part-of-batch]

---

### TC-017-023: Batch finalisieren und an PlantingRun uebergeben

**Requirement**: REQ-017 § 6 Testszenario 7 — Batch-Finalisierung mit PlantingRun-Uebergabe
**Priority**: Critical
**Category**: Happy Path
**Vorbedingungen**:
- Batch "GSC-Klone Fruehling 2026" (Status "in_progress") mit 10 Stecklingen
- 8 Stecklinge ueberlebt (Ergebnis nachgetragen via TC-017-012)
- PlantingRun "GSC Grow Cycle #5" (Status "geplant") existiert

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Batches "GSC-Klone Fruehling 2026"
2. Nutzer klickt auf "Batch abschliessen"
3. Ein Finalisierungs-Dialog oeffnet sich
4. Dialog zeigt: Gesamtmenge 10, Ueberlebt 8, Erfolgsrate 80%
5. Nutzer waehlt im Feld "Ziel-Durchlauf": "GSC Grow Cycle #5"
6. Nutzer klickt auf "Abschliessen und Pflanzen uebergeben"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Batch abgeschlossen — 8 Pflanzen an GSC Grow Cycle #5 uebergeben"
- Batch-Status aendert sich auf "Abgeschlossen" (completed)
- Batch-Karte zeigt: Gesamt 10, Ueberlebt 8, Erfolgsrate 80%
- PlantingRun "GSC Grow Cycle #5" zeigt nun 8 neue Eintraege

**Nachbedingungen**:
- Batch status=completed, PlantingRun hat 8 neue PlantInstances (seedling-Phase)

**Tags**: [req-017, batch-finalisieren, planting-run, uebergabe, happy-path]

---

### TC-017-024: Batch-Finalisierung ohne vorheriges Ergebnis nicht moeglich

**Requirement**: REQ-017 § 6 DoD — PropagationBatch Batch-Finalisierung
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Batch "Test-Batch" (Status "in_progress") mit 5 Stecklingen
- Kein Ergebnis bisher nachgetragen (survived_count = null)

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Batches
2. Nutzer klickt auf "Batch abschliessen"

**Erwartete Ergebnisse**:
- Entweder: Button "Batch abschliessen" ist deaktiviert (grau) mit Tooltip "Zuerst Ergebnis fuer alle Events nachtragen"
- Oder: Ein Hinweis erscheint: "Nicht alle Events haben ein eingetragenes Ergebnis. Bitte Ueberlebt-Anzahl fuer alle Events nachtragen vor dem Abschluss."
- Finalisierung wird nicht durchgefuehrt

**Nachbedingungen**:
- Batch bleibt "in_progress"

**Tags**: [req-017, batch-finalisieren, validierung, fehlerzustand]

---

## 6. Mutterpflanzen-Verwaltung

### TC-017-025: Mutterpflanzen-Liste oeffnen und Uebersicht pruefen

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/mothers
**Priority**: Critical
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Mindestens 3 PlantInstances haben is_mother=true: "GSC Mutter #1" (Prioritaet critical, Health 85), "Tomate Mutter" (Prioritaet standard, Health 90), "Old Mother" (Prioritaet important, Health 35)

**Testschritte**:
1. Nutzer navigiert zu `/vermehrung/mutterpflanzen`
2. Nutzer betrachtet die Liste

**Erwartete Ergebnisse**:
- Seitenheader "Mutterpflanzen" ist sichtbar
- Tabelle zeigt alle 3 Mutterpflanzen
- Spalten: Name, Spezies, Prioritaet, Health-Score, Letzte Entnahme, Tage bis Erholung, Generation, Stecklinge Gesamt, Avg. Erfolgsrate
- "Old Mother" (Health 35) hat einen roten/orangen Health-Balken oder Badge
- "GSC Mutter #1" hat ein "CRITICAL"-Prioritaets-Badge
- Button "Als Mutterpflanze designieren" ist sichtbar (leitet zur PlantInstance-Seite)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, mutterpflanzen-liste, health-score, prioritaet]

---

### TC-017-026: PlantInstance als Mutterpflanze designieren

**Requirement**: REQ-017 § 3 REST-API — PATCH /api/v1/propagation/mothers/{plant_key}/designate
**Priority**: Critical
**Category**: Zustandswechsel
**Vorbedingungen**:
- PlantInstance "Kush Mother Kandidatin" existiert (is_mother=false)
- Nutzer navigiert zur Detailseite dieser PlantInstance

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Kush Mother Kandidatin" (PlantInstance-Detail)
2. Nutzer klickt auf den Tab "Vermehrung" oder einen Button "Als Mutterpflanze markieren"
3. Ein Dialog oder Abschnitt fuer Mutterpflanzen-Konfiguration oeffnet sich
4. Nutzer waehlt Prioritaet: "Wichtig (important)"
5. Nutzer setzt Erholungszeit: "14" Tage
6. Nutzer klickt auf "Als Mutterpflanze designieren"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Pflanze wurde als Mutterpflanze designiert"
- PlantInstance-Detailseite zeigt jetzt ein Mutterpflanzen-Badge oder Icon
- Felder: Prioritaet "Wichtig", Erholungszeit "14 Tage", Designiert am (heute), Generation "0"
- Pflanze erscheint nun in der Mutterpflanzen-Liste `/vermehrung/mutterpflanzen`

**Nachbedingungen**:
- PlantInstance.is_mother=true, mother_priority="important", mother_designated_at=heute

**Tags**: [req-017, mutterpflanze, designieren, zustandswechsel]

---

### TC-017-027: Gesundheitsbewertung einer Mutterpflanze aktualisieren

**Requirement**: REQ-017 § 3 REST-API — PATCH /api/v1/propagation/mothers/{plant_key}/health
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist auf der Mutterpflanzen-Detailseite von "GSC Mutter #1"
- Aktueller Health-Score: 85

**Testschritte**:
1. Nutzer klickt auf "Gesundheitsbewertung aktualisieren"
2. Ein Slider oder Zahleneingabe erscheint (0–100)
3. Nutzer setzt den Wert auf "70"
4. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Gesundheitsbewertung aktualisiert"
- Health-Score-Anzeige auf der Detailseite springt von 85 auf 70
- Farbliche Darstellung aendert sich (gruen bei 70 statt gelbem Bereich)
- Kein Retirement-Hinweis erscheint (70 liegt noch ueber dem kritischen Schwellenwert von 30)

**Nachbedingungen**:
- mother_health_score=70

**Tags**: [req-017, health-score, mutterpflanze, aktualisieren]

---

### TC-017-028: Retirement-Empfehlung bei kritisch niedriger Gesundheit wird angezeigt

**Requirement**: REQ-017 § 3 PropagationEngine.suggest_retirement; Testszenario 5
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Nutzer navigiert zur Detailseite von "Old Mother" (Health 35, Generation 12, letzte 3 Entnahmen: avg 48%)

**Testschritte**:
1. Nutzer oeffnet die Detailseite von "Old Mother" in der Mutterpflanzen-Liste

**Erwartete Ergebnisse**:
- Ein prominentes Warnbanner erscheint (gelb oder orange): "Gesundheit kritisch (35/100) — Abloesung dringend empfohlen"
- Ein zweiter Hinweis: "Generation 12 — hohes Risiko fuer somatische Mutationslast. Neue Mutterpflanze aus Samen empfohlen."
- Erfolgsraten-Diagramm zeigt abfallenden Trend der letzten Entnahmen
- Button "Mutterpflanze pensionieren" ist gut sichtbar

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-017, retirement-empfehlung, warnung, health, somatische-mutationslast]

---

### TC-017-029: Mutterpflanze pensionieren

**Requirement**: REQ-017 § 3 REST-API — PATCH /api/v1/propagation/mothers/{plant_key}/retire
**Priority**: High
**Category**: Zustandswechsel
**Vorbedingungen**:
- Nutzer ist auf der Mutterpflanzen-Detailseite von "Old Mother"

**Testschritte**:
1. Nutzer klickt auf "Mutterpflanze pensionieren"
2. Ein Bestaetigungs-Dialog oeffnet sich: "Sind Sie sicher, dass Sie 'Old Mother' als pensioniert markieren moechten? Diese Aktion kann nicht rueckgaengig gemacht werden."
3. Nutzer gibt optionalen Grund ein: "Gesundheit zu schlecht, neue Mutterpflanze aus Samen gezogen"
4. Nutzer klickt auf "Pensionieren"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Mutterpflanze wurde pensioniert"
- Detailseite zeigt: "Status: Pensioniert" mit Datum
- Button "Als Mutterpflanze designieren" ist deaktiviert oder verschwunden
- Pflanze erscheint in der Mutterpflanzen-Liste mit "Pensioniert"-Badge
- Neues Stecklingsevent von dieser Mutterpflanze zeigt Warnung: "Mutterpflanze ist bereits als pensioniert markiert"

**Nachbedingungen**:
- mother_retired_at=heute, mother_retire_reason gesetzt

**Tags**: [req-017, mutterpflanze, pensionieren, zustandswechsel, warnung]

---

## 7. IPM-Integration und Virusstatus-Warnungen

### TC-017-030: Warnung bei Vermehrung einer virusinfizierten Mutterpflanze

**Requirement**: REQ-017 § 1 IPM-Integration — Virusstatus; PropagationEngine.validate_cutting_from_mother
**Priority**: Critical
**Category**: Fehlermeldung
**Vorbedingungen**:
- Mutterpflanze "Infected Mother" hat virus_status="infected"
- Nutzer versucht ein neues Stecklingsevent von dieser Pflanze zu erstellen

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog fuer neues Event
2. Nutzer waehlt Quellpflanze: "Infected Mother"
3. Sobald die Pflanze ausgewaehlt ist, erscheint eine Warnung

**Erwartete Ergebnisse**:
- Sofort nach Auswahl der Quellpflanze erscheint ein roter Warnbanner: "WARNUNG: Mutterpflanze ist als virusinfiziert markiert. Vermehrung uebertraegt Viren auf alle Nachkommen. Werkzeugsterilisation und Quarantaene dringend empfohlen."
- Das Formular kann weitergenutzt werden (keine Blockierung), aber:
  - Das Feld "Werkzeugsterilisation" ist automatisch als Pflichtfeld hervorgehoben
  - Das Feld "Quarantaene erforderlich" ist automatisch auf "Ja" gesetzt
- Nutzer kann das Event trotzdem erstellen

**Nachbedingungen**:
- Wenn erstellt: Event mit Virus-Warnung gespeichert, quarantine_required=true

**Tags**: [req-017, ipm, virusstatus, warnung, infected]

---

### TC-017-031: Warnung bei Critical-Mutterpflanze mit ungetesteten Virusstatus

**Requirement**: REQ-017 § 3 PropagationEngine.validate_cutting_from_mother — untested + critical
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Mutterpflanze "Elite Mother" hat mother_priority="critical" und virus_status="untested"

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog fuer neues Event
2. Nutzer waehlt Quellpflanze: "Elite Mother"

**Erwartete Ergebnisse**:
- Hinweis (gelb, nicht blockierend): "Mutterpflanze mit Prioritaet 'Kritisch (critical)' hat Status 'Ungetestet'. Virustest empfohlen vor weiterer Vermehrung."
- Formular bleibt nutzbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, ipm, virusstatus, critical, hinweis]

---

### TC-017-032: IPM-Felder — Werkzeugsterilisation und Quarantaene eintragen

**Requirement**: REQ-017 § 1 IPM-Integration; § 2 PropagationEvent.tool_sterilization_method
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog fuer ein neues Stecklingsevent

**Testschritte**:
1. Nutzer scrollt im Dialog zum Abschnitt "IPM & Hygiene"
2. Nutzer waehlt im Feld "Werkzeugsterilisation": "Isopropanol 70% (alcohol_70)"
3. Nutzer aktiviert "Quarantaene erforderlich": Ja
4. Nutzer gibt Quarantaene-Dauer: "14" Tage ein
5. Nutzer schliesst das Formular ab und speichert

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Vermehrungsevent wurde erstellt"
- In der Detailansicht: IPM-Abschnitt zeigt Werkzeugsterilisation "Isopropanol 70%", Quarantaene "14 Tage"

**Nachbedingungen**:
- PropagationEvent mit IPM-Feldern gespeichert

**Tags**: [req-017, ipm, werkzeugsterilisation, quarantaene]

---

## 8. Erholungszeit-Warnung und Somatische Mutationslast

### TC-017-033: Erholungszeit-Warnung bei zu fruehzeitiger Stecklingnahme

**Requirement**: REQ-017 § 6 Testszenario 1 — Erholungszeit-Pruefung; PropagationEngine.validate_cutting_from_mother
**Priority**: Critical
**Category**: Fehlermeldung
**Vorbedingungen**:
- Mutterpflanze "GSC Mutter #1" (mother_recovery_days=14)
- Letzte Stecklingnahme war vor 10 Tagen

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog fuer neues Stecklingsevent
2. Nutzer waehlt Quellpflanze: "GSC Mutter #1"
3. Sofort erscheint eine Warnmeldung in der Pflanzauswahl oder nach der Auswahl

**Erwartete Ergebnisse**:
- Gelber Warnhinweis erscheint: "Erholungszeit nicht eingehalten: 10 von 14 Tagen seit letzter Entnahme (Methode 'Steckling': 14 Tage, Mutterpflanze: 14 Tage)"
- Das Formular ist NICHT blockiert (Warnung, kein Fehler — Nutzer kann trotzdem speichern)
- In der Mutterpflanzen-Detail-Uebersicht: "Erholungszeit: Noch 4 Tage bis naechste Entnahme moeglich"

**Nachbedingungen**:
- Wenn Nutzer trotzdem speichert: Event wird angelegt, Warnung im Aktivitaetslog festgehalten

**Tags**: [req-017, erholungszeit, warnung, recovery-days, mutterpflanze]

---

### TC-017-034: Methodenspezifische Erholungszeit — Teilung benoetigt 21 Tage

**Requirement**: REQ-017 § 3 PropagationEngine.RECOVERY_DAYS_BY_METHOD — division: 21
**Priority**: Medium
**Category**: Fehlermeldung
**Vorbedingungen**:
- Mutterpflanze "Spathiphyllum #1" (mother_recovery_days=14, letzte Teilung vor 15 Tagen)

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog
2. Nutzer waehlt Methode: "Teilung (division)"
3. Nutzer waehlt Quellpflanze: "Spathiphyllum #1"

**Erwartete Ergebnisse**:
- Warnhinweis: "Erholungszeit nicht eingehalten: 15 von 21 Tagen seit letzter Entnahme (Methode 'Teilung': 21 Tage, Mutterpflanze: 14 Tage)"
- Hinweis erklaert, dass Teilung 21 Tage benoetigt (nicht 14 wie bei Stecklingen)

**Nachbedingungen**:
- Kein Status geaendert (Warnung, keine Blockierung)

**Tags**: [req-017, erholungszeit, teilung, division, methodenspezifisch]

---

### TC-017-035: Somatische Mutationslast-Warnung ab Generation 10

**Requirement**: REQ-017 § 6 Testszenario 9 — Generationswarnung; PropagationEngine.SOMATIC_MUTATION_WARNING_GENERATION=10
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- Mutterpflanze "Clone-Gen-11" hat mother_generation=11

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog fuer neues Stecklingsevent
2. Nutzer waehlt Quellpflanze: "Clone-Gen-11"

**Erwartete Ergebnisse**:
- Warnhinweis erscheint: "Generation 11 — somatische Mutationslast erhoeht. Empfehlung: Neue Mutterpflanze aus Samen ziehen."
- Warnung ist gelb/orange und gut lesbar
- Das Formular ist nicht blockiert

**Nachbedingungen**:
- Wenn Event erstellt: Nachkommen erhalten Generation 12

**Tags**: [req-017, somatische-mutationslast, generation, warnung]

---

### TC-017-036: Generation 9 zeigt keine Somatische Mutationslast-Warnung (Grenzwert)

**Requirement**: REQ-017 § 3 PropagationEngine.SOMATIC_MUTATION_WARNING_GENERATION=10 — Grenzwert
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Mutterpflanze "Clone-Gen-9" hat mother_generation=9

**Testschritte**:
1. Nutzer waehlt Quellpflanze "Clone-Gen-9" im Erstellungs-Dialog

**Erwartete Ergebnisse**:
- Kein Warnhinweis wegen somatischer Mutationslast erscheint
- Eventuell anderer Kontext-Hinweis: "Generation 9 — nahe dem Empfehlungs-Schwellenwert (10)"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, somatische-mutationslast, generation, grenzwert, kein-fehler]

---

## 9. Abstammungsgraph und Genetische Rueckverfolgbarkeit

### TC-017-037: Abstammungsgraph einer Pflanze — Lineage-Tab auf PlantInstance-Detailseite

**Requirement**: REQ-017 § 6 Testszenario 3 — Abstammungslinie ueber 3 Generationen; § 3 REST-API GET /lineage
**Priority**: Critical
**Category**: Detailansicht
**Vorbedingungen**:
- PlantInstance "GSC-Clone-A1" abstammt von "GSC-Mother-1" (Klon, Generation 2)
- "GSC-Mother-1" abstammt von "GSC-Seed-Original" (Samen/Saemling, Generation 1)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von PlantInstance "GSC-Clone-A1"
2. Nutzer klickt auf den Tab "Abstammung"

**Erwartete Ergebnisse**:
- Tab "Abstammung" ist sichtbar
- Ein visueller Stammbaum oder eine Baumstruktur wird angezeigt
- Abstammungslinie: GSC-Clone-A1 → GSC-Mother-1 → GSC-Seed-Original
- Jede Ebene zeigt: Pflanzenname, Beziehungstyp (Klon / Saemling), Generation
- "GSC-Clone-A1": Generation 2 (Klon)
- "GSC-Mother-1": Generation 1 (Klon)
- "GSC-Seed-Original": Generation 0 (Ursprung)
- Pflanzenname-Eintraege in der Abstammung sind anklickbar (navigieren zur jeweiligen PlantInstance-Detailseite)
- Gesamtzahl Generationen: "2"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, abstammung, lineage, generationen, stammbaum]

---

### TC-017-038: Nachkommen-Ansicht einer Mutterpflanze (Klon-Baum)

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/plant-instances/{key}/descendants; § 6 Testszenario 3
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- "GSC-Mother-1" hat 5 direkte Klon-Kinder und 3 Klon-Enkel (insgesamt 8 Nachkommen)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "GSC-Mother-1"
2. Nutzer klickt auf den Tab "Nachkommen"

**Erwartete Ergebnisse**:
- Tab "Nachkommen" ist sichtbar
- Eine Baumansicht oder Liste zeigt alle 8 Nachkommen
- Direkte Kinder (5) sind auf Ebene 1 angezeigt
- Enkel (3) sind auf Ebene 2 angezeigt (eingerueckt oder als Unterknoten)
- Jeder Eintrag zeigt: Name, Ebene/Generation, Beziehungstyp (Klon)
- Gesamtzahl Nachkommen: "8"
- Alle Eintraege sind als Links zur jeweiligen PlantInstance-Detailseite klickbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, nachkommen, descendants, klon-baum]

---

### TC-017-039: Kreuzungs-Abstammung — beide Elternteile im Lineage-Tab sichtbar

**Requirement**: REQ-017 § 2 Edge descended_from — seed_mother/seed_father; Testszenario 6
**Priority**: High
**Category**: Detailansicht
**Vorbedingungen**:
- F1-Pflanze "Haze-Kush-F1-#3" wurde aus Kreuzung erstellt
- Mutter: "Haze Mother", Vater: "Kush Father"

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Haze-Kush-F1-#3"
2. Nutzer klickt auf den Tab "Abstammung"

**Erwartete Ergebnisse**:
- Abstammungs-Ansicht zeigt ZWEI Elternpflanzen
- "Haze Mother" mit Beziehungs-Label "Samenmutter (seed_mother)"
- "Kush Father" mit Beziehungs-Label "Samenvater (seed_father)"
- Generation wird als "F1" dargestellt (filial generation)
- Beide Elternteile sind anklickbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, kreuzung, abstammung, seed-mother, seed-father, f1]

---

### TC-017-040: Pflanze ohne Abstammung — Leerzustand auf Abstammungs-Tab

**Requirement**: REQ-017 § 2 Graph — Leerzustand
**Priority**: Medium
**Category**: Listenansicht
**Vorbedingungen**:
- PlantInstance "Ursprung-Pflanze #1" wurde manuell angelegt (kein Vermehrungsevent, keine Eltern)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Ursprung-Pflanze #1"
2. Nutzer klickt auf den Tab "Abstammung"

**Erwartete Ergebnisse**:
- Kein Stammbaum sichtbar
- Leerzustand-Meldung: "Keine Abstammungsdaten vorhanden. Diese Pflanze ist der Ursprung einer Linie."
- Tab "Nachkommen" zeigt ggf. Kinder wenn vorhanden (oder ebenfalls Leertext)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, abstammung, leerzustand, ursprung]

---

## 10. Phaenotyp-Notizen

### TC-017-041: Phaenotyp-Notiz erstellen (Happy Path)

**Requirement**: REQ-017 § 6 Testszenario 10 — Phaenotyp-Dokumentation; § 3 REST-API POST /phenotypes
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist auf der Detailseite von "F1 Pflanze #3" (aus Haze x Kush Kreuzung)
- Keine Phaenotyp-Notizen bisher vorhanden

**Testschritte**:
1. Nutzer klickt auf den Tab "Phaenotyp"
2. Tab zeigt "Keine Phaenotyp-Notizen vorhanden" und Button "Notiz hinzufuegen"
3. Nutzer klickt auf "Notiz hinzufuegen"
4. Dialog oeffnet sich
5. Nutzer waehlt Kategorie: "Aroma"
6. Nutzer gibt Merkmal ein: "Zitrus-Terpen-dominant mit Kiefer-Untertoenen"
7. Nutzer setzt Bewertung: "9" (auf Skala 1–10)
8. Nutzer gibt Notiz: "Auffaellig starke Terpen-Produktion ab Woche 5 Bluete"
9. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Phaenotyp-Notiz wurde gespeichert"
- Dialog schliesst sich
- Phaenotyp-Tab zeigt neue Notiz: Kategorie "Aroma", Merkmal "Zitrus-Terpen-dominant...", Bewertung "9/10", Datum heute
- Bewertung ist visuell als Sterne oder Balken dargestellt

**Nachbedingungen**:
- PhenotypeNote erstellt, has_phenotype-Edge zur Pflanze

**Tags**: [req-017, phaenotyp, notiz, aroma, bewertung, happy-path]

---

### TC-017-042: Mehrere Phaenotyp-Kategorien fuer eine Pflanze dokumentieren

**Requirement**: REQ-017 § 2 PhenotypeCategory — morphology, aroma, flavor, vigor, resistance, yield, potency, other
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist auf dem Phaenotyp-Tab von "F1 Pflanze #3"
- Eine Aroma-Notiz existiert bereits

**Testschritte**:
1. Nutzer klickt auf "Notiz hinzufuegen"
2. Nutzer waehlt Kategorie: "Vitalitaet (vigor)"
3. Nutzer gibt Merkmal: "Sehr kompakter Wuchs, internodale Abstaende 2-3 cm"
4. Nutzer setzt Bewertung: "8"
5. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Phaenotyp-Tab zeigt jetzt 2 Notizen: Aroma und Vitalitaet
- Notizen sind nach Kategorie gruppiert oder chronologisch sortiert
- Alle 8 verfuegbaren Kategorien sind im Dropdown auswaehlbar: Morphologie, Aroma, Geschmack, Vitalitaet, Resistenz, Ertrag, Wirkstaerke, Sonstiges

**Nachbedingungen**:
- Zwei PhenotypeNotes zur Pflanze

**Tags**: [req-017, phaenotyp, kategorien, mehrere-notizen]

---

### TC-017-043: Phaenotyp-Notiz loeschen mit Bestaetigung

**Requirement**: REQ-017 § 3 REST-API — DELETE /api/v1/plant-instances/{key}/phenotypes/{note_key}
**Priority**: Medium
**Category**: Zustandswechsel
**Vorbedingungen**:
- PlantInstance "F1 Pflanze #3" hat eine Phaenotyp-Notiz mit ID "pheno_note_001"

**Testschritte**:
1. Nutzer klickt auf den Tab "Phaenotyp"
2. Nutzer klickt auf das Loeschen-Icon bei der Notiz "Zitrus-Terpen-dominant"
3. Bestaetigungs-Dialog erscheint: "Soll die Phaenotyp-Notiz 'Zitrus-Terpen-dominant mit Kiefer-Untertoenen' wirklich geloescht werden? Diese Aktion kann nicht rueckgaengig gemacht werden."
4. Nutzer klickt auf "Loeschen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung: "Phaenotyp-Notiz wurde geloescht"
- Notiz verschwindet aus dem Tab
- Wenn keine weiteren Notizen: Leerzustand-Text erscheint

**Nachbedingungen**:
- PhenotypeNote aus der Datenbank entfernt, has_phenotype-Edge entfernt

**Tags**: [req-017, phaenotyp, loeschen, bestaetigung]

---

### TC-017-044: Phaenotyp-Bewertung ausserhalb des gueltigen Bereichs (Grenzwert)

**Requirement**: REQ-017 § 3 PhenotypeNote.rating — ge=1, le=10
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Phaenotyp-Notiz-Erstellen-Dialog

**Testschritte**:
1. Nutzer gibt im Bewertungsfeld den Wert "0" ein (unter dem Minimum)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Validierungsfehler am Feld: "Bewertung muss zwischen 1 und 10 liegen"
- Formular bleibt offen

**Testschritte (Variante: Ueber Maximum)**:
1. Nutzer gibt im Bewertungsfeld den Wert "11" ein
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse (Variante)**:
- Validierungsfehler: "Bewertung muss zwischen 1 und 10 liegen"

**Nachbedingungen**:
- Keine Notiz erstellt

**Tags**: [req-017, phaenotyp, bewertung, validierung, grenzwert]

---

## 11. Veredelungs-Kompatibilitaetspruefung

### TC-017-045: Veredelungs-Kompatibilitaet — gleiche Gattung kompatibel (Happy Path)

**Requirement**: REQ-017 § 6 Testszenario 4 — Kompatibilitaetspruefung gleiche Gattung; PropagationEngine.check_graft_compatibility
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer erstellt neues Veredelungs-Event (Methode: "Veredelung / grafting")
- PlantInstance "Tomate San Marzano" (Solanum lycopersicum) soll auf "Tomate Beaufort F1" (Solanum lycopersicum) veredelt werden

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog, waehlt Methode "Veredelung"
2. Im Dialog erscheinen Felder: "Edelreis-Pflanze" und "Unterlage-Pflanze"
3. Nutzer waehlt "Tomate San Marzano" als Edelreis
4. Nutzer waehlt "Tomate Beaufort F1" als Unterlage
5. Eine Kompatibilitaets-Pruefung wird automatisch ausgefuehrt (oder Nutzer klickt "Kompatibilitaet pruefen")

**Erwartete Ergebnisse**:
- Gruener Banner erscheint: "Kompatibel — Gleiche Gattung (Solanum) — Veredelung empfohlen"
- Level wird als "Kompatibel (gleiche Gattung)" angezeigt
- Nutzer kann das Event erstellen

**Nachbedingungen**:
- Wenn erstellt: Veredelungs-Event mit grafted_onto-Edge erstellt

**Tags**: [req-017, veredelung, grafting, kompatibilitaet, gleiche-gattung]

---

### TC-017-046: Veredelungs-Kompatibilitaet — verschiedene Familien inkompatibel

**Requirement**: REQ-017 § 6 Testszenario 4 — Kompatibilitaetspruefung inkompatibel
**Priority**: High
**Category**: Fehlermeldung
**Vorbedingungen**:
- "Tomate San Marzano" (Solanaceae) soll auf "Gurke Markusovszky" (Cucurbitaceae) veredelt werden

**Testschritte**:
1. Nutzer oeffnet Erstellungs-Dialog, waehlt Methode "Veredelung"
2. Nutzer waehlt "Tomate San Marzano" als Edelreis
3. Nutzer waehlt "Gurke Markusovszky" als Unterlage
4. Kompatibilitaets-Pruefung laeuft

**Erwartete Ergebnisse**:
- Roter Warnbanner: "Inkompatibel — Verschiedene Familien (Solanaceae vs. Cucurbitaceae) — Veredelung nicht empfohlen"
- Button "Event trotzdem erstellen" ist sichtbar aber zurueckhaltend gestylt (nicht prominenter CTA)
- Nutzer wird deutlich auf das Risiko hingewiesen

**Nachbedingungen**:
- Kein Event erstellt (ausser Nutzer erzwingt es)

**Tags**: [req-017, veredelung, inkompatibel, verschiedene-familien, warnung]

---

### TC-017-047: Veredelungs-Kompatibilitaet — gleiche Familie (possibly_compatible)

**Requirement**: REQ-017 § 3 PropagationEngine.check_graft_compatibility — same_family=True
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- "Tomate San Marzano" (Solanaceae) soll auf "Kartoffel Desirée" (Solanaceae, anderer Genus) veredelt werden

**Testschritte**:
1. Nutzer waehlt Edelreis: "Tomate San Marzano", Unterlage: "Kartoffel Desirée"
2. Kompatibilitaets-Pruefung laeuft

**Erwartete Ergebnisse**:
- Gelber/oranger Banner: "Moeglicherweise kompatibel — Gleiche Familie (Solanaceae) — Veredelung moeglich, aber Abstossungsrisiko erhoeht (keine expliziten Erfahrungsdaten)"
- Nutzer kann das Event erstellen

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-017, veredelung, possibly-compatible, gleiche-familie]

---

### TC-017-048: Veredelungs-Kompatibilitaet — Edelreis und Unterlage identisch blockiert

**Requirement**: REQ-017 § 3 GraftRequestValidator.validate_different_plants
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Veredelungs-Event-Erstellungs-Dialog

**Testschritte**:
1. Nutzer waehlt sowohl als Edelreis als auch als Unterlage dieselbe Pflanze: "Tomate San Marzano"
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Edelreis und Unterlage muessen verschiedene Pflanzen sein"
- Formular bleibt offen, Speichern blockiert

**Nachbedingungen**:
- Kein Event erstellt

**Tags**: [req-017, veredelung, validierung, identische-pflanze, fehler]

---

## 12. Hormon-Konzentrations-Validierung

### TC-017-049: Hormon-Konzentration ueber empfohlenem Maximum — Warnung

**Requirement**: REQ-017 § 3 PropagationEngine.validate_hormone_concentration; HORMONE_RANGES
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog fuer ein Stecklingsevent
- Stecklingstyp "Weichholz (softwood)", Applikationsmethode "Quick-Dip" ausgewaehlt (Empfehlung: 500–1500 ppm)

**Testschritte**:
1. Nutzer gibt Hormon-Konzentration: "2000" ppm ein (ueber dem Maximum von 1500 ppm)
2. Nutzer verlasst das Feld

**Erwartete Ergebnisse**:
- Gelbe Warnung erscheint: "Hormon-Konzentration 2000 ppm ueber empfohlenem Maximum (1500 ppm) fuer Weichholz/Quick-Dip. Toxizitaetsrisiko!"
- Formular bleibt benutzbar (keine Blockierung)

**Nachbedingungen**:
- Nutzer kann trotzdem speichern (Warnung, kein Fehler)

**Tags**: [req-017, hormon, konzentration, warnung, toxizitaet, softwood]

---

### TC-017-050: Hormon-Konzentration doppeltes Maximum — kritische Warnung

**Requirement**: REQ-017 § 3 PropagationEngine.validate_hormone_concentration — >2x max
**Priority**: High
**Category**: Formvalidierung
**Vorbedingungen**:
- Stecklingstyp "Weichholz", Quick-Dip (Empfehlung: 500–1500 ppm)

**Testschritte**:
1. Nutzer gibt Hormon-Konzentration: "4000" ppm ein (>2x Maximum 1500 ppm)

**Erwartete Ergebnisse**:
- Rote kritische Warnung: "KRITISCH: 4000 ppm ist mehr als das Doppelte der oberen Grenze (1500 ppm) — extreme Toxizitaetsgefahr (Kallusnekrose, Stecklingstod)"
- Zusaetzlich die erste Warnung bleibt sichtbar
- Speichern koennte blockiert sein oder erfordert explizite Bestaetigung

**Nachbedingungen**:
- Wenn blockiert: kein Event erstellt

**Tags**: [req-017, hormon, kritisch, toxizitaet, hardwood]

---

### TC-017-051: Hormon-Konzentration korrekt — kein Hinweis erscheint

**Requirement**: REQ-017 § 3 PropagationEngine.validate_hormone_concentration — keine Warnung
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Stecklingstyp "Hartholz (hardwood)", Applikationsmethode "Long-Soak" (Empfehlung: 50–200 ppm)

**Testschritte**:
1. Nutzer gibt Hormon-Konzentration: "100" ppm ein (innerhalb des Bereichs)

**Erwartete Ergebnisse**:
- Kein Warnhinweis erscheint
- Feld zeigt keinen Fehlerstatus

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, hormon, kein-fehler, grenzwert]

---

## 13. Statistiken-Dashboard

### TC-017-052: Statistiken-Dashboard oeffnen und Gesamtueberblick

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/stats
**Priority**: High
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist eingeloggt
- Verschiedene PropagationEvents mit Ergebnissen existieren (cutting 75%, seed_sowing 85%, water_propagation 90%)

**Testschritte**:
1. Nutzer navigiert zu `/vermehrung/statistiken`

**Erwartete Ergebnisse**:
- Seitenheader "Vermehrungs-Statistiken" ist sichtbar
- Balken- oder Kreisdiagramm zeigt Erfolgsraten pro Methode
- Tabelle oder Karten zeigen Kennzahlen: Gesamte Events, Gesamt Ueberlebt, Gesamt Ausgefallen, Durchschnittliche Erfolgsrate
- Detaillierte Aufschluesselung nach Methode sichtbar
- Filter fuer Zeitraum (z.B. letzter Monat, letztes Quartal, gesamt)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, statistiken, erfolgsraten, dashboard]

---

### TC-017-053: Statistiken nach Sorte (Cultivar) filtern

**Requirement**: REQ-017 § 3 REST-API — GET /api/v1/propagation/stats/by-cultivar
**Priority**: Medium
**Category**: Listenansicht
**Vorbedingungen**:
- Nutzer ist auf der Statistiken-Seite
- Events fuer verschiedene Sorten existieren

**Testschritte**:
1. Nutzer klickt auf Tab "Nach Sorte" oder Filter "Sorte"
2. Nutzer waehlt Cultivar: "GSC (Girl Scout Cookies)"

**Erwartete Ergebnisse**:
- Statistiken werden auf Events fuer "GSC" gefiltert angezeigt
- Erfolgsraten pro Methode fuer diese Sorte
- Anzahl Events fuer diese Sorte

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, statistiken, cultivar, filter]

---

## 14. Navigations-Tiering und Zugangskontrolle (REQ-021)

### TC-017-054: Vermehrungsbereich in der Seitenleiste sichtbar (Experten-Stufe)

**Requirement**: REQ-017 § 5 Abhaengigkeiten; REQ-021 Erfahrungsstufen-Navigation
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt mit Erfahrungsstufe "Experte"

**Testschritte**:
1. Nutzer betrachtet die Seitenleiste

**Erwartete Ergebnisse**:
- Seitenleiste zeigt Menupunkt "Vermehrung" mit Unterpunkten:
  - "Events"
  - "Batches"
  - "Protokolle"
  - "Mutterpflanzen"
  - "Statistiken"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, navigation, experten-stufe, seitenleiste]

---

### TC-017-055: Vermehrungsbereich fuer Einsteiger nicht in Seitenleiste (Tiering)

**Requirement**: REQ-021 Erfahrungsstufen-Navigation — Einsteiger sieht nur max. 5 Punkte
**Priority**: Medium
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist eingeloggt mit Erfahrungsstufe "Einsteiger"

**Testschritte**:
1. Nutzer betrachtet die Seitenleiste

**Erwartete Ergebnisse**:
- Menupunkt "Vermehrung" ist in der Seitenleiste NICHT sichtbar
- Die Seiten sind bei direkter URL-Eingabe (/vermehrung/events) trotzdem zugaenglich (kein Auth-Gate, nur Tiering)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, navigation, einsteiger, tiering, rei-021]

---

### TC-017-056: Nicht-Mitglied hat keinen Zugriff auf Vermehrungsseiten

**Requirement**: REQ-017 § 4 Authentifizierung — Alle Endpunkte erfordern Authentifizierung
**Priority**: High
**Category**: Navigation
**Vorbedingungen**:
- Nutzer ist NICHT eingeloggt

**Testschritte**:
1. Nutzer navigiert direkt zu `/vermehrung/events`

**Erwartete Ergebnisse**:
- Nutzer wird zur Login-Seite `/login` umgeleitet
- Nach erfolgreichem Login: Weiterleitung zu `/vermehrung/events`

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, auth, zugangskontrolle, nicht-eingeloggt]

---

## 15. Bewurzelungsparameter-Felder im Erstellungs-Dialog

### TC-017-057: VPD-Ziel-Hinweis im Erstellungs-Dialog — niedrig fuer Stecklinge

**Requirement**: REQ-017 § 1 Bewurzelungs-Protokolle — target_vpd_kpa 0.3–0.5 kPa fuer wurzellose Stecklinge
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog und hat Methode "Steckling" gewaehlt

**Testschritte**:
1. Nutzer scrollt zu den Bewurzelungsparametern
2. Nutzer gibt VPD-Ziel: "0.4" kPa ein

**Erwartete Ergebnisse**:
- Tooltip oder Hilfstext neben dem VPD-Feld: "Empfohlen: 0.3–0.5 kPa fuer wurzellose Stecklinge unter Haube"
- Kein Fehler oder Warnung fuer Wert 0.4 kPa

**Nachbedingungen**:
- Parameter wird gespeichert

**Tags**: [req-017, vpd, bewurzelungsparameter, hinweis]

---

### TC-017-058: Lichtspektrum-Dropdown zeigt alle 7 Optionen

**Requirement**: REQ-017 § 3 LightSpectrum Enum — 7 Werte
**Priority**: Low
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog oder Protokoll-Dialog und sucht Lichtspektrum-Feld

**Testschritte**:
1. Nutzer klickt auf das Dropdown-Feld "Lichtspektrum"

**Erwartete Ergebnisse**:
- Dropdown zeigt alle 7 Optionen:
  - "Blau-dominant (blue_dominant)"
  - "Rot-dominant (red_dominant)"
  - "Rot-Blau-Mix (red_blue_mix)"
  - "Vollspektrum (full_spectrum)"
  - "Warmweiss (warm_white)"
  - "Kuehlweiss (cool_white)"
  - "Leuchtstoffroehre (fluorescent)"
- Auswaehlen einer Option schliesst das Dropdown

**Nachbedingungen**:
- Ausgewaehlter Wert wird im Formular angezeigt

**Tags**: [req-017, lichtspektrum, dropdown, enum]

---

## 16. Edge Cases und Grenzwerte

### TC-017-059: Maximale Anzahl Stecklinge pro Event (Grenzwert 1000)

**Requirement**: REQ-017 § 3 PropagationEvent.quantity — ge=1, le=1000
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog

**Testschritte**:
1. Nutzer gibt Anzahl: "1001" ein
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Validierungsfehler: "Maximale Anzahl: 1000"
- Formular bleibt offen

**Testschritte (Variante: Genau 1000)**:
1. Nutzer gibt Anzahl: "1000" ein
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse (Variante)**:
- Kein Fehler, Event wird gespeichert

**Nachbedingungen**:
- Bei 1001: kein Event erstellt; bei 1000: Event erstellt

**Tags**: [req-017, grenzwert, anzahl, validierung]

---

### TC-017-060: Minimale Anzahl Stecklinge — 0 wird blockiert

**Requirement**: REQ-017 § 3 PropagationEvent.quantity — ge=1
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog

**Testschritte**:
1. Nutzer gibt Anzahl: "0" ein
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Validierungsfehler: "Anzahl muss mindestens 1 sein"
- Formular bleibt offen

**Nachbedingungen**:
- Kein Event erstellt

**Tags**: [req-017, grenzwert, anzahl, minimum, validierung]

---

### TC-017-061: Hormon-Konzentration oberhalb absoluter Obergrenze 10.000 ppm blockiert

**Requirement**: REQ-017 § 3 PropagationEvent.hormone_concentration_ppm — le=10000
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog, Hormon-Typ ausgewaehlt

**Testschritte**:
1. Nutzer gibt Hormon-Konzentration: "15000" ppm ein
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Validierungsfehler: "Maximale Hormon-Konzentration: 10.000 ppm"
- Formular bleibt offen

**Nachbedingungen**:
- Kein Event erstellt

**Tags**: [req-017, grenzwert, hormon, 10000ppm, validierung]

---

### TC-017-062: Medium-pH ausserhalb des gueltigen Bereichs (3.0–8.0) blockiert

**Requirement**: REQ-017 § 3 PropagationEvent.medium_ph — ge=3.0, le=8.0
**Priority**: Medium
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog, Substrat-Integration-Abschnitt sichtbar

**Testschritte**:
1. Nutzer gibt Medium-pH: "2.5" ein (unter dem Minimum 3.0)
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Validierungsfehler: "pH muss zwischen 3.0 und 8.0 liegen"
- Formular bleibt offen

**Nachbedingungen**:
- Kein Event erstellt

**Tags**: [req-017, grenzwert, medium-ph, substrat, validierung]

---

### TC-017-063: Medium-EC ueber Maximum (5.0 mS/cm) blockiert

**Requirement**: REQ-017 § 3 PropagationEvent.medium_ec_ms — ge=0, le=5.0
**Priority**: Low
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer gibt Medium-EC: "6.0" mS/cm ein (ueber Maximum)

**Testschritte**:
1. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Validierungsfehler: "EC darf maximal 5.0 mS/cm betragen"
- Hilfstext: "Fuer Stecklinge empfohlen: unter 0.5 mS/cm (naehrstoffarm)"
- Formular bleibt offen

**Nachbedingungen**:
- Kein Event erstellt

**Tags**: [req-017, grenzwert, medium-ec, validierung]

---

### TC-017-064: Quarantaene-Dauer ohne Quarantaene-Flag — Feld ausgeblendet

**Requirement**: REQ-017 § 3 PropagationEvent.quarantine_required / quarantine_days
**Priority**: Low
**Category**: Formvalidierung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog

**Testschritte**:
1. Nutzer betrachtet den IPM-Abschnitt
2. "Quarantaene erforderlich" ist standardmaessig auf "Nein" gesetzt
3. Das Feld "Quarantaene-Dauer (Tage)" ist nicht sichtbar oder deaktiviert
4. Nutzer aktiviert "Quarantaene erforderlich" auf "Ja"

**Erwartete Ergebnisse**:
- Das Feld "Quarantaene-Dauer (Tage)" wird sichtbar und aktiv
- Eingabe "14" Tage ist moeglich

**Nachbedingungen**:
- Quarantaene-Dauer wird nur angezeigt wenn quarantine_required=true

**Tags**: [req-017, quarantaene, bedingtes-feld, conditional-display]

---

## 17. Gewebekultur und seltene Methoden

### TC-017-065: Alle 12 Vermehrungsmethoden im Dialog verfuegbar

**Requirement**: REQ-017 § 6 DoD — PropagationEvent-CRUD 12 Methoden
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog

**Testschritte**:
1. Nutzer klickt auf das Methoden-Dropdown

**Erwartete Ergebnisse**:
- Alle 12 Methoden sind auswaehlbar:
  1. Steckling (cutting)
  2. Blattsteckling (leaf_cutting)
  3. Stammstuck (stem_section)
  4. Aussaat (seed_sowing)
  5. Teilung (division)
  6. Kindel/Ableger (offset)
  7. Absenker (layering)
  8. Abmoosen (air_layering)
  9. Brutzwiebel (bulbil)
  10. Wasserbewurzelung (water_propagation)
  11. Veredelung (grafting)
  12. Gewebekultur (tissue_culture)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, methoden, 12-methoden, dropdown, vollstaendigkeit]

---

### TC-017-066: Stecklingstyp nur bei Methode "Steckling" sichtbar

**Requirement**: REQ-017 § 2 PropagationEvent.cutting_type — nur bei event_type='cutting'
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog

**Testschritte**:
1. Nutzer waehlt Methode: "Aussaat"
2. Nutzer betrachtet das Formular: Ist "Stecklingstyp"-Feld sichtbar?
3. Nutzer aendert Methode auf: "Steckling"
4. Nutzer betrachtet das Formular erneut

**Erwartete Ergebnisse**:
- Bei Methode "Aussaat": Kein Stecklingstyp-Feld sichtbar
- Bei Methode "Steckling": Stecklingstyp-Feld ist sichtbar mit 8 Optionen (apical, nodal, heel, softwood, semi_hardwood, hardwood, leaf_petiole, leaf_section)
- Das Feld erscheint/verschwindet dynamisch beim Wechsel der Methode

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, cutting-type, bedingtes-feld, stecklingstyp, methode]

---

## 18. Suche, Leerszenarien und Fehlerbehandlung

### TC-017-067: Events-Liste — Suchfeld filtert nach Quellpflanze

**Requirement**: REQ-017 allgemein — DataTable Suchfunktion
**Priority**: Medium
**Category**: Listenansicht
**Vorbedingungen**:
- Events-Liste hat 20 Eintraege von verschiedenen Quellpflanzen
- 3 Events stammen von "GSC Mutter #1"

**Testschritte**:
1. Nutzer tippt "GSC" in das Suchfeld "Tabelle durchsuchen..."
2. Nutzer wartet 300ms (Debounce)

**Erwartete Ergebnisse**:
- Tabelle zeigt nur die 3 Events von "GSC Mutter #1"
- Suchbegriff "GSC" ist im Suchfeld sichtbar
- Trefferanzahl: "Zeigt 1–3 von 3 Eintraegen"

**Nachbedingungen**:
- Filter aktiv

**Tags**: [req-017, suche, filter, datatable]

---

### TC-017-068: Events-Liste leer — Leerzustand wird angezeigt

**Requirement**: REQ-017 allgemein — Leerzustand DataTable
**Priority**: Medium
**Category**: Listenansicht
**Vorbedingungen**:
- Keine PropagationEvents im System vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/vermehrung/events`

**Erwartete Ergebnisse**:
- Tabelle zeigt Leerzustand: "Keine Vermehrungsevents vorhanden. Klicken Sie auf 'Neues Event', um Ihren ersten Vermehrungsvorgang zu dokumentieren."
- Button "Neues Event" ist sichtbar
- Keine Fehlermeldung erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, leerzustand, events-liste]

---

### TC-017-069: Suchfeld ergibt keine Treffer — Meldung anzeigen

**Requirement**: REQ-017 allgemein — DataTable kein Suchergebnis
**Priority**: Low
**Category**: Listenansicht
**Vorbedingungen**:
- Events-Liste hat Eintraege, aber keine passende zum Suchbegriff

**Testschritte**:
1. Nutzer tippt "XYZNOTEXIST" in das Suchfeld

**Erwartete Ergebnisse**:
- Tabelle zeigt: "Keine Ergebnisse fuer Ihre Suche gefunden"
- Suchfeld bleibt aktiv

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-017, suche, keine-treffer, datatable]

---

### TC-017-070: Netzwerkfehler bei Event-Erstellung — Fehlermeldung erscheint

**Requirement**: REQ-017 allgemein — Fehlerbehandlung
**Priority**: Medium
**Category**: Fehlermeldung
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog, alle Pflichtfelder sind ausgefuellt
- Server ist nicht erreichbar (Netzwerkfehler)

**Testschritte**:
1. Nutzer klickt auf "Erstellen"
2. Anfrage schlaegt fehl (Netzwerkfehler)

**Erwartete Ergebnisse**:
- Fehlermeldung (Snackbar, rot): "Netzwerkfehler — Verbindung zum Server nicht moeglich"
- Dialog bleibt offen, eingegebene Daten bleiben erhalten
- Nutzer kann es erneut versuchen

**Nachbedingungen**:
- Kein Event erstellt

**Tags**: [req-017, netzwerkfehler, fehlermeldung, fehlerbehandlung]

---

### TC-017-071: Protokoll-Vorlage laden — befuellt Felder automatisch korrekt

**Requirement**: REQ-017 § 1 Bewurzelungs-Protokolle — Vorladen aus Protokoll
**Priority**: High
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog fuer ein neues Event

**Testschritte**:
1. Nutzer klickt auf "Protokoll-Vorlage laden"
2. Liste der verfuegbaren Vorlagen erscheint (alle is_template=true Protokolle)
3. Nutzer waehlt "Cannabis Steckling Standard"

**Erwartete Ergebnisse**:
- Folgende Felder werden automatisch befuellt:
  - Medium: "Steinwolle (rockwool)"
  - Hormon-Typ: "IBA"
  - Hormon-Konzentration: "1000 ppm"
  - Applikationsmethode: "Pulver (powder)"
  - Luftfeuchtigkeit: "85 %"
  - VPD-Ziel: "0.4 kPa"
  - Lufttemperatur: "20 °C"
  - Substrattemperatur: "22 °C"
  - PPFD: "100"
  - Lichtspektrum: "Kuehlweiss (cool_white)"
  - Beleuchtungsdauer: "18 h"
- Nutzer kann die Felder nach dem Laden noch individuell anpassen

**Nachbedingungen**:
- Felder befuellt, aber noch nicht gespeichert

**Tags**: [req-017, protokoll, vorlage-laden, autofill]

---

### TC-017-072: Stecklingstyp-Auswahl beeinflusst empfohlene Hormon-Ranges im Dialog

**Requirement**: REQ-017 § 3 PropagationEngine.HORMONE_RANGES — stecklingstypspezifische Werte
**Priority**: Medium
**Category**: Happy Path
**Vorbedingungen**:
- Nutzer ist im Erstellungs-Dialog, Methode "Steckling" gewaehlt

**Testschritte**:
1. Nutzer waehlt Stecklingstyp: "Hartholz (hardwood)"
2. Nutzer waehlt Applikationsmethode: "Long-Soak"
3. Nutzer liest den Hilfstext zum Hormon-Konzentrations-Feld

**Erwartete Ergebnisse**:
- Hilfstext oder Tooltip zeigt: "Empfohlen fuer Hartholz / Long-Soak: 50–200 ppm (12–24h Einwirkzeit)"
- Wenn Nutzer nun "2500" ppm eingibt: Warnung erscheint (ueber Maximum fuer diese Kombination)

**Testschritte (Variante: Stecklingstyp aendern)**:
1. Nutzer aendert Stecklingstyp auf "Weichholz (softwood)", Methode "Quick-Dip"
2. Hilfstext zum Hormon-Konzentrations-Feld aendert sich

**Erwartete Ergebnisse (Variante)**:
- Hilfstext zeigt: "Empfohlen fuer Weichholz / Quick-Dip: 500–1500 ppm"

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-017, hormon-ranges, stecklingstyp, dynamisch, hilfstext]

---

## Abdeckungsmatrix

| REQ-017 Spezifikations-Abschnitt | Testfaelle | Beschreibung |
|----------------------------------|-----------|--------------|
| § 1 Business Case — Mutterpflanzen | TC-017-025 bis TC-017-029 | Designation, Health, Pensionierung, Retirement-Empfehlung |
| § 1 Vermehrungsmethoden (12) | TC-017-004 bis TC-017-009, TC-017-065 | Alle 12 Methoden, Zimmerpflanzen-Methoden |
| § 1 Stecklingstyp (CuttingType) | TC-017-004, TC-017-066, TC-017-072 | 8 Typen, bedingtes Feld, Hormon-Ranges |
| § 1 Bewurzelungs-Protokolle | TC-017-014 bis TC-017-020, TC-017-071 | CRUD, Validierungen, Statistiken, Vorlage-Laden |
| § 1 IPM-Integration | TC-017-030 bis TC-017-032 | Virusstatus, Werkzeugsterilisation, Quarantaene |
| § 1 Genetische Abstammung | TC-017-037 bis TC-017-040 | Lineage-Tab, Nachkommen, Kreuzung, Leerzustand |
| § 1 Vermehrungsbatch | TC-017-021 bis TC-017-024 | CRUD, Events zuordnen, Finalisieren, Validierung |
| § 2 PropagationEvent Model | TC-017-010 bis TC-017-013, TC-017-059 bis TC-017-064 | Validierungen, Grenzwerte, Timeline |
| § 2 PropagationBatch Model | TC-017-021 bis TC-017-024 | Status, Finalisierung |
| § 2 RootingProtocol Model | TC-017-015 bis TC-017-019 | Temperatur-Delta, PPFD, Timeline |
| § 2 PhenotypeNote Model | TC-017-041 bis TC-017-044 | CRUD, Kategorien, Bewertung |
| § 3 PropagationEngine | TC-017-033 bis TC-017-036, TC-017-049 bis TC-017-051 | Erholungszeit, Somatische Mutationslast, Hormon |
| § 3 LineageEngine | TC-017-037 bis TC-017-040 | Stammbaum, Nachkommen, Verwandtschaft |
| § 3 GraftCompatibility | TC-017-045 bis TC-017-048 | gleiche Gattung, verschiedene Familien, identisch |
| § 3 REST-API Events | TC-017-001 bis TC-017-013 | CRUD, Filter, Progress, Outcome |
| § 3 REST-API Batches | TC-017-021 bis TC-017-024 | CRUD, Finalisierung |
| § 3 REST-API Mothers | TC-017-025 bis TC-017-029 | Liste, Designate, Retire, Health |
| § 3 REST-API Lineage | TC-017-037 bis TC-017-040 | Abstammung, Nachkommen |
| § 3 REST-API Statistiken | TC-017-052 bis TC-017-053 | Gesamt, nach Cultivar |
| § 3 Seed-Daten (10 Protokolle) | TC-017-014 | Systemseitig vorhandene Protokoll-Vorlagen |
| § 4 Authentifizierung | TC-017-056 | Nicht-eingeloggt → Redirect |
| § 5 REQ-021 Erfahrungsstufen | TC-017-054 bis TC-017-055 | Experte/Einsteiger Navigation-Tiering |
| § 6 DoD — alle Akzeptanzkriterien | TC-017-001 bis TC-017-072 (alle) | Vollstaendige DoD-Abdeckung |
| § 6 Testszenarien 1–10 | TC-017-033, TC-017-012, TC-017-037, TC-017-045, TC-017-028, TC-017-006, TC-017-023, TC-017-020, TC-017-035, TC-017-041 | 1:1 Zuordnung Testszenario → Testfall |
| Allgemein: DataTable-Patterns | TC-017-001, TC-017-002, TC-017-067 bis TC-017-069 | Suche, Filter, Leerzustand |
| Allgemein: Fehlerbehandlung | TC-017-070 | Netzwerkfehler |
