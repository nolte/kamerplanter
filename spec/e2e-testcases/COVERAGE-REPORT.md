---
title: E2E-Testfall-Vollständigkeitsanalyse
generated: 2026-04-02
scope: spec/e2e-testcases/ vs spec/req/ und spec/nfr/
analyst: e2e-testcase-extractor
---

# E2E-Testfall-Vollständigkeitsanalyse

Dieses Dokument vergleicht die vorhandenen E2E-Testfall-Dokumente in `spec/e2e-testcases/` systematisch gegen die 34 Anforderungsdokumente in `spec/req/` und `spec/nfr/`. Grundlage ist die Nutzerperspektive im Browser — alle Lücken beziehen sich auf fehlende UI-Szenarien, nicht auf Backend- oder API-Tests.

**Analysedatum:** 2026-04-02  
**Gesamte Testfälle vorhanden:** 1.654 (über 34 Testfall-Dokumente)  
**REQ-Dokumente mit Testfällen:** 30 von 34 im Scope  
**NFR-Dokumente mit Testfällen:** 4 von 13 (wobei die meisten NFRs keinen Browser-SuT haben)

---

## 1. Übersichtstabelle

| REQ/NFR | Titel (Kurzform) | Spec-Version | TC-Version | Testfälle | Abdeckungsgrad |
|---------|-----------------|:------------:|:----------:|:---------:|:--------------:|
| REQ-001 | Stammdatenverwaltung | 4.0 | 4.0 | 78 | Vollständig |
| REQ-002 | Standortverwaltung | 4.2 | 4.2 | 62 | Vollständig |
| REQ-003 | Phasensteuerung | 2.3 | 2.3 | 42 | Vollständig |
| REQ-004 + 004-A | Dünge-Logik + EC-Budget | 3.4 / 1.1 | 3.4 / 1.1 | 88 | Vollständig |
| REQ-005 | Hybrid-Sensorik | 2.6 | 2.6 | 58 | Vollständig |
| REQ-006 | Aufgabenplanung | 3.0 | 3.0 | 72 | Vollständig |
| REQ-007 | Erntemanagement | 2.3 | 2.3 | 42 | Vollständig |
| REQ-008 | Post-Harvest | 2.2 | 2.2 | 68 | Vollständig |
| REQ-009 | Dashboard | 2.0 | 2.0 | 42 | Vollständig |
| REQ-010 | IPM-System | 1.0 | 1.0 | 58 | Vollständig |
| REQ-011 | Externe Stammdatenanreicherung | 1.0 | 1.0 | 28 | Teilweise |
| REQ-012 | Stammdaten-Import | 1.0 | 1.0 | 54 | Vollständig |
| REQ-013 | Pflanzdurchlauf | **2.0** | **1.2** | 52 | **Teilweise — Version veraltet** |
| REQ-014 | Tankmanagement | 1.5 | 1.5 | 72 | Vollständig |
| REQ-015 + 015-A | Kalenderansicht + Aussaatkalender | 1.5 / 1.2 | 1.5 / 1.2 | 52 | Vollständig |
| REQ-016 | InvenTree-Integration | 1.0 | 1.0 | 52 | Vollständig |
| REQ-017 | Vermehrungsmanagement | 1.2 | 1.2 | 72 | Vollständig |
| REQ-018 | Umgebungssteuerung | 1.2 | 1.2 | 72 | Vollständig |
| REQ-019 | Substratverwaltung | 4.1 | 4.1 | 38 | Vollständig |
| REQ-020 | Onboarding-Wizard | 1.6 | 1.6 | 52 | Vollständig |
| REQ-021 | UI-Erfahrungsstufen | **1.2** | **1.1** | 52 | **Teilweise — Version veraltet** |
| REQ-022 | Pflegeerinnerungen | 2.4 | 2.4 | 68 | Vollständig |
| REQ-023 | Benutzerverwaltung & Auth | 1.8 | 1.8 | 72 | Vollständig |
| REQ-024 | Mandantenverwaltung | 1.4 | 1.4 | 82 | Vollständig |
| REQ-025 | Datenschutz / DSGVO | 1.0 | 1.1 | 46 | Vollständig |
| REQ-026 | Aquaponik-Management | 1.0 | 1.0 | 68 | Vollständig |
| REQ-027 | Light-Modus | 1.2 | 1.2 | 52 | Vollständig |
| REQ-028 | Mischkultur & Companion Planting | 1.0 | 1.0 | 42 | Vollständig |
| REQ-029 | KI-Bilderkennung (Optional) | 1.0 | 1.0 | 58 | Vollständig |
| REQ-030 | Benachrichtigungssystem | 1.0 | 1.0 | 62 | Vollständig |
| **REQ-032** | **Druckansichten & Export** | **1.1** | — | **0** | **FEHLEND** |
| NFR-006 | API-Fehlerbehandlung (UI) | 1.0 | 1.0 | 38 | Vollständig |
| NFR-007 | Betriebsstabilität / Monitoring | 1.0 | 1.0 | 42 | Vollständig |
| NFR-008 | Teststrategie | 1.0 | 1.0 | 48 | Vollständig |
| NFR-010 | UI-Vollständigkeit / CRUD-Matrix | 1.0 | 1.0 | 62 | Vollständig |
| NFR-011 | Aufbewahrungsfristen (UI-seitig) | 1.0 | 1.0 | 38 | Vollständig |

**Nicht im Scope (keine UI-E2E-Tests sinnvoll):**
- NFR-001 (Architekturprinzip), NFR-002 (Kubernetes), NFR-003 (Linting), NFR-004 (Dev-Env), NFR-005 (Dokumentation), NFR-008a (Selenium-Standard), NFR-009 (Dependency-Mgmt), NFR-012 (Enterprise-Skalierung)
- REQ-031 (KI-Assistent) — Out of Scope per Aufgabenstellung

---

## 2. Fehlende Testfälle im Detail

### 2.1 REQ-032 Druckansichten & Export — VOLLSTÄNDIG FEHLEND

**Priorität: Hoch**  
Spec-Version: 1.1. Kein Testfall-Dokument vorhanden.

REQ-032 definiert 8 druckbare Template-Typen und 3 Ausgabeformate (Browser-Druck, PDF-Export, CSV-Export). Da Druckfunktionen immer nutzerseitig ausgelöst werden (PrintButton, Download-Link), sind diese vollständig testbar aus der Browserperspektive.

Fehlende Szenarien:

| Priorität | Fehlende Testfälle |
|-----------|-------------------|
| Critical | Nährstoffplan-PDF aus Nährstoffplan-Detailseite abrufen (PrintButton, Download startet) |
| Critical | Pflege-Checkliste drucken (Zeitraum auswählen, Seite im Browser drucken) |
| High | Ernteprotokoll als PDF exportieren (HarvestBatch-Detailseite, PDF-Download) |
| High | Pflanzen-Infokarte / Einzelkarte mit QR-Code drucken (PlantInstance-Detail) |
| High | Sammelausdruck mehrerer Infokarten auf A4-Blatt (Raster-Layout konfigurieren) |
| High | Gießplan für Urlaubsvertretung drucken |
| Medium | Standort-Übersicht / Beetplan drucken (Location-Detailseite) |
| Medium | Kalender-Übersicht drucken (Monat oder Woche) |
| Medium | Pflanzen-Steckbrief als PDF (Species-Detailseite) |
| Medium | Felder auf Infokarte konfigurieren (Checkbox-Dialog vor Druck) |
| Medium | CSV-Export Nährstoffplan |
| Low | Druckansicht hat korrekte CSS-@media-print-Styles (kein Sidebar, kein Footer sichtbar) |
| Low | Fehlverhalten bei fehlendem `APP_BASE_URL` (QR-Code-Generierung) |

**Empfehlung:** `spec/e2e-testcases/TC-REQ-032.md` mit ca. 42 Testfällen erstellen.

---

### 2.2 REQ-013 Pflanzdurchlauf — Version veraltet (TC v1.2 vs. Spec v2.0)

**Priorität: Hoch**  
Spec wurde auf v2.0 aktualisiert: Run als primäre Verwaltungseinheit, kein Mixed-Culture mehr, PlantDiaryEntry neu eingeführt, Sukzessions-Aussaat (SuccessionPlan) hinzugekommen.

Lücken durch den Versionssprung:

| Priorität | Fehlende Testfälle |
|-----------|-------------------|
| Critical | Run-Erstell-Dialog hat KEIN Mischkultur-Typ mehr — Testfälle TC-013-003 und TC-013-005 (Mischkultur-Pfad) sind veraltet und müssen entfernt/ersetzt werden |
| Critical | PlantDiaryEntry anlegen: Nutzer öffnet Pflanzenprofil im Run → klickt "Tagebucheintrag hinzufügen" → füllt Freitext + Kategorie → speichert |
| Critical | PlantDiaryEntry anzeigen: Tagebuch-Tab in PlantInstance-Detail zeigt Einträge chronologisch |
| High | PlantDiaryEntry bearbeiten und löschen |
| High | Run-Level-Operationen vs. Standalone-Operationen: Nutzer im aktiven Run sieht KEINE individuellen Phasen/Task/Pflege-Controls pro Pflanze (nur Run-Level-Buttons sichtbar) |
| High | Detach-Kategorie muss angegeben werden (Detach-Dialog zeigt Pflichtfeld `detach_category`: disease, experiment, sale, other) |
| High | Nach Detach: Pflanze erscheint als Standalone in `/pflanzen/plant-instances` mit Phase aus Run kopiert |
| High | Run-Zähler nach Detach: Run-Detailseite zeigt `active_plant_count` um 1 reduziert |
| Medium | SuccessionPlan erstellen: Nutzer konfiguriert Staffelaussaat (Intervall, Start-/Enddatum, Anzahl pro Staffel) |
| Medium | Automatisch generierte Staffel-Runs erscheinen in Liste mit Status `planned` und fortlaufenden Namen |
| Medium | Staffel-Run aktivieren: Erinnerung angezeigt → Nutzer bestätigt → Status wechselt zu `active` |
| Medium | Run-Typ `clone`: `source_plant_key` ist Pflichtfeld (fehlt im Dialog → Fehlerhinweis) |
| Low | Run-Detailseite zeigt keine Einzelbearbeitung pro Pflanze (kein "Bearbeiten" pro PlantInstance-Zeile im Run) |

**Empfehlung:** TC-REQ-013.md auf v2.0 updaten. Veraltete Mischkultur-Testfälle entfernen. Ca. 15 neue Testfälle hinzufügen.

---

### 2.3 REQ-021 UI-Erfahrungsstufen — Version veraltet (TC v1.1 vs. Spec v1.2)

**Priorität: Mittel**  
Spec v1.2 erweitert das Beginner-Navigations-Set von 5 auf 8 Menüpunkte (neu hinzugekommen: Standorte, Kalender, Gießprotokoll, Pflege-Dashboard).

Lücken durch den Versionssprung:

| Priorität | Fehlende Testfälle |
|-----------|-------------------|
| High | Einsteiger-Modus zeigt Navigationspunkt "Standorte" (Pfad `/standorte/sites`) — bestehende Tests prüfen nur 5 Punkte |
| High | Einsteiger-Modus zeigt Navigationspunkt "Kalender" (`/kalender`) |
| High | Einsteiger-Modus zeigt Navigationspunkt "Gießprotokoll" (`/giessprotokoll`) |
| High | Einsteiger-Modus zeigt Navigationspunkt "Pflege-Dashboard" (`/pflege`) |
| Medium | Einsteiger-Modus versteckt weiterhin "Durchläufe", "Tanks", "Substrate", "IPM" — negative Prüfung mit neuem 8er-Set |
| Medium | Navigations-Tiering-Referenztabelle: Vollständige Matrix 19 Pfade × 3 Stufen prüfen (§ 3.3) |
| Low | Begründungs-Tooltip: Einsteiger kann auf gesperrten Menüpunkt klicken → Tooltip "Verfügbar ab Stufe Fortgeschritten" erscheint |

**Empfehlung:** TC-REQ-021.md auf v1.2 updaten. Ca. 6–8 neue Testfälle hinzufügen und bestehende Navigations-Testfälle auf 8 Einsteiger-Punkte aktualisieren.

---

### 2.4 REQ-011 Externe Stammdatenanreicherung — Partiell abgedeckt

**Priorität: Niedrig**  
Das Testdokument (28 Testfälle, v1.0) markiert Testfälle mit dedizierter Admin-UI als "UI ausstehend". Da keine Enrichment-Admin-Section im Frontend vorhanden ist, sind folgende UI-Szenarien faktisch nicht testbar, aber für die Vollständigkeit relevant:

| Priorität | Fehlende Testfälle |
|-----------|-------------------|
| Low | Anreicherungsvorschlag ablehnen (wenn Admin-UI implementiert) |
| Low | Manuelle Synchronisierung eines einzelnen Species-Eintrags auslösen (Sync-Button) |
| Low | Anreicherungs-Status pro Species im Detail anzeigen (confidence, source, last_synced_at) |
| Low | Konflikt-Handling-Dialog: vorhandener Wert vs. externer Vorschlag (side-by-side) |

**Empfehlung:** Kein sofortiger Handlungsbedarf. Testfälle ergänzen, wenn Admin-UI für Anreicherung implementiert wird.

---

## 3. Versionsdiskrepanzen ohne inhaltliche Lücken

Die folgenden Dokumente zeigen kleinere Versionsdiskrepanzen, die jedoch keine inhaltlichen Testlücken erzeugen, da die Änderungen rein technischer Natur waren:

| TC-Dokument | TC-Version | Spec-Version | Art der Abweichung | Handlungsbedarf |
|-------------|:----------:|:------------:|-------------------|:--------------:|
| TC-REQ-025 | 1.1 | 1.0 | TC höher als Spec (Vorgriff auf geplante v1.1) | Keiner |
| TC-REQ-015 | 1.5 / 1.2 | 1.5 / 1.2 (REQ-015-A ohne eigene Versionsnr.) | Korrekt | Keiner |

---

## 4. Inhaltliche Lücken innerhalb bestehender Testdokumente

Auch in vollständig versionierten Dokumenten wurden folgende thematische Lücken identifiziert:

### 4.1 REQ-006 Aufgabenplanung (72 Testfälle, v3.0)

Spec v3.0 enthält **phänologische Trigger** (PhenologicalEvent-Knoten: Forsythienblüte, Holunderblüte etc.) als Aufgaben-Auslöser statt fester Kalenderdaten. Die bestehenden Testfälle decken `seasonal_month`-Trigger ab, aber:

- Fehlend: Phänologischen Trigger konfigurieren (Dropdown "Forsythienblüte", "Holunderblüte" etc. im Task-Template-Dialog)
- Fehlend: Aufgabe erscheint erst in der Queue, wenn ein passender PhenologicalEvent vom System erkannt wird (nicht am festen Datum)

### 4.2 REQ-022 Pflegeerinnerungen (68 Testfälle, v2.4)

Spec v2.4 enthält **Überwinterungsmanagement** mit OverwinteringProfile-Knoten und Winterhärte-Ampel. Die Testfälle decken Pflegeerinnerungen umfassend ab, aber:

- Fehlend: Überwinterungs-Profil anlegen für eine Pflanze (OverwinteringProfile-Dialog, 3 Felder: protection_method, storage_location, spring_uncovering_date)
- Fehlend: Winterhärte-Ampel-Anzeige in PlantInstance-Detail (grün/gelb/rot basierend auf frost_sensitivity + climate_zone)
- Fehlend: Erinnerung "Einwintern bis [Datum]" erscheint automatisch im Pflege-Dashboard

### 4.3 REQ-007 Erntemanagement (42 Testfälle, v2.3)

Spec v2.3 enthält **Ernte-Fenster-Vorhersage (W-007)**:

- Fehlend: Vorhergesagtes Ernte-Fenster wird auf der PlantInstance-Detailseite als Datums-Banner angezeigt (frühestes–spätestes Datum)
- Fehlend: Ernte-Fenster-Berechnung per GDD — Nutzer sieht "~12 Tage bis Ernte" basierend auf akkumulierten GDD

### 4.4 REQ-002 Standortverwaltung (62 Testfälle, v4.2)

Spec v4.2 enthält **WaterSource-Konfiguration mit RO-System und Mischverhältnis**:

- Fehlend: Warnung bei veralteter Wasseranalyse (measurement_age_days > 180: gelber Banner "Wasseranalyse älter als 6 Monate")
- Fehlend: RO-Membran-Warnung (ro_membrane_changed_date > 365 Tage: orangener Banner)
- Fehlend: GH-Plausibilitätsprüfung (wenn tap_gh_dh < 1.0: Info-Banner "Sehr weiches Wasser — CalMag-Korrektur empfohlen")

### 4.5 REQ-024 Mandantenverwaltung (82 Testfälle, v1.4)

Spec v1.4 enthält **DutyRotation (Gießdienst-Rotation)**, **Pinnwand (BulletinPost)** und **Ernte-Teilen (SharedShoppingList)**:

- Fehlend: Gießdienst-Rotation konfigurieren (Mitglieder-Reihenfolge, Intervall)
- Fehlend: Pinnwand-Beitrag erstellen, anzeigen, kommentieren
- Fehlend: Ernte-Teilen: HarvestBatch für Mitglieder freigeben (SharedShoppingList)

---

## 5. Priorisierung der Lücken

### Kritisch (sofortiger Handlungsbedarf für normale Nutzer)

| # | Lücke | Betroffener REQ | Aufwand (TC-Anzahl) |
|---|-------|:---------------:|:-------------------:|
| 1 | **TC-REQ-032 komplett fehlend** — Druckfunktionen sind für viele Nutzergruppen (Grower, Gemeinschaftsgarten, Urlaubsvertretung) unverzichtbar | REQ-032 | ~42 |
| 2 | **TC-REQ-013 veraltet** — Mischkultur-Tests basieren auf entfernter Funktion; PlantDiaryEntry komplett ungetestet | REQ-013 | ~15 Neu, 3 Veraltet entfernen |

### Hoch (wichtig für konsistente Testabdeckung)

| # | Lücke | Betroffener REQ | Aufwand (TC-Anzahl) |
|---|-------|:---------------:|:-------------------:|
| 3 | **TC-REQ-021 Navigations-Tiering veraltet** — Beginner-Set hat 8 statt 5 Punkte; Regressionsgefahr wenn Sidebar geändert wird | REQ-021 | ~8 |
| 4 | **Überwinterungsmanagement ungetestet** — OverwinteringProfile + Winterhärte-Ampel aus v2.4 fehlen | REQ-022 | ~6 |
| 5 | **REQ-024 Gemeinschaftsgarten-Kollaboration** — Gießdienst-Rotation, Pinnwand, Ernte-Teilen nicht abgedeckt | REQ-024 | ~10 |

### Mittel (bei nächster Überarbeitung ergänzen)

| # | Lücke | Betroffener REQ | Aufwand (TC-Anzahl) |
|---|-------|:---------------:|:-------------------:|
| 6 | Ernte-Fenster-Vorhersage (GDD-basiert) nicht getestet | REQ-007 | ~4 |
| 7 | Phänologische Task-Trigger (Forsythienblüte etc.) nicht getestet | REQ-006 | ~3 |
| 8 | Wasseranalyse-Alter und RO-Membran-Warnungen nicht getestet | REQ-002 | ~4 |

### Niedrig (kann warten)

| # | Lücke | Betroffener REQ | Aufwand (TC-Anzahl) |
|---|-------|:---------------:|:-------------------:|
| 9 | REQ-011 Admin-Anreicherungs-UI (noch nicht implementiert) | REQ-011 | ~6 (nach Impl.) |

---

## 6. Empfehlungen: Nächste Schritte

### Sofortmaßnahmen (Sprint 1)

1. **TC-REQ-032 erstellen** — neues Dokument für Druckansichten & Export. Die Spec v1.1 ist vollständig und das Feature ist für Endnutzer hochrelevant. Empfohlene Struktur:
   - Gruppe 1: Browser-Druckansicht (PrintButton, @media print)
   - Gruppe 2: PDF-Export (Download-Flow)
   - Gruppe 3: Pflanzen-Infokarte + QR-Code
   - Gruppe 4: Sammelausdruck / Konfigurationsdialog
   - Gruppe 5: CSV-Export
   - Gruppe 6: Fehlerzustände (keine Daten, PDF-Generierung fehlgeschlagen)

2. **TC-REQ-013 auf v2.0 aktualisieren** — veraltete Mischkultur-Testfälle entfernen, neue PlantDiaryEntry-Gruppe hinzufügen, SuccessionPlan-Testfälle ergänzen.

### Kurzfristig (Sprint 2)

3. **TC-REQ-021 auf v1.2 aktualisieren** — Beginner-Navigations-Testfälle auf 8 Menüpunkte anpassen und die vollständige Navigations-Matrix (§ 3.3) abdecken.

4. **TC-REQ-022 erweitern** — Überwinterungsmanagement-Szenarien als neue Gruppe 10 hinzufügen.

5. **TC-REQ-024 erweitern** — Gemeinschaftsgarten-Kollaboration (Gießdienst, Pinnwand, Ernte-Teilen) als neue Gruppen hinzufügen.

### Mittelfristig (Sprint 3+)

6. **TC-REQ-002 erweitern** — Wasseranalyse-Alter und RO-Membran-Warnungen als neue Testgruppe.

7. **TC-REQ-007 erweitern** — Ernte-Fenster-Vorhersage (GDD-Berechnung, Datums-Banner).

8. **TC-REQ-006 erweitern** — Phänologische Trigger in Task-Templates.

9. **TC-REQ-011 ergänzen** — sobald Admin-Anreicherungs-UI implementiert ist.

---

## 7. Zusammenfassung

| Metrik | Wert |
|--------|------|
| Gesamt-Testfälle | 1.654 |
| REQs vollständig abgedeckt | 28 von 30 im Scope |
| REQs mit Versionslücken | 2 (REQ-013, REQ-021) |
| REQs komplett fehlend | 1 (REQ-032) |
| Inhaltliche Lücken in sonst vollständigen Docs | 5 (REQ-002, REQ-006, REQ-007, REQ-022, REQ-024) |
| Empfohlene neue Testfälle (gesamt) | ~98 |
| Veraltete Testfälle zum Entfernen | ~3 (REQ-013 Mischkultur) |

Die **Gesamtabdeckung ist sehr gut**: 1.654 Testfälle decken nahezu alle Kern-Workflows aus der Nutzerperspektive ab. Die identifizierten Lücken konzentrieren sich auf drei Bereiche: ein komplett fehlendes Dokument (REQ-032 Druckansichten), ein veraltetes Dokument durch einen Major-Versionssprung in der Spec (REQ-013 v1.2→v2.0) und kleinere inhaltliche Ergänzungen in bereits gut abgedeckten Bereichen.
