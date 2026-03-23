---
req_id: REQ-011
title: Externe Stammdatenanreicherung via Drittanbieter-APIs
category: Stammdaten / Integration
test_count: 28
coverage_areas:
  - Quellenverwaltung (Enrichment Sources)
  - Manueller Sync-Auslöser
  - Sync-Historie und Statusanzeige
  - Anreicherungs-Vorschläge in der Species-Detailansicht
  - Accept/Reject externer Feldvorschläge
  - Lokale Hoheit (manuelle Daten haben Vorrang)
  - Datenprovenienz-Anzeige (Quelle, Zeitstempel, Konfidenz)
  - Graceful Degradation bei API-Ausfall
  - Checksum-basiertes Überspringen unveränderte Einträge
  - Auth / Zugangsberechtigung (Admin vs. Viewer)
  - Externe Suche (Search-Endpunkt)
  - Cannabis-Sorten via Otreeba
  - Companion-Planting-Kanten via OpenFarm
generated: "2026-03-21"
version: "1.0"
---

# Testfälle: REQ-011 — Externe Stammdatenanreicherung

**Anforderungsreferenz:** `spec/req/REQ-011_Externe-Stammdatenanreicherung.md`
**Perspektive:** Endnutzer im Browser (Admin-Rolle und Grower-Rolle)
**Hinweis zur Frontend-Implementierung:** REQ-011 ist primär ein Backend-Feature. Die angereicherten Felder (Winterhärtezonen, Synonyme, Taxonomie u. a.) sind über die bestehende Species-Detailseite (`/stammdaten/arten/:key`) sichtbar und bearbeitbar. Eine dedizierte Enrichment-Admin-Seite ist in der Spezifikation vorgesehen, jedoch noch nicht als eigenständige Frontend-Seite implementiert. Testfälle, die eine dedizierte Admin-Enrichment-UI voraussetzen (z. B. Sync-Auslöser, Source-Liste, Sync-Historie), sind als **"UI ausstehend"** markiert und beschreiben das erwartete Zielverhalten, das bei der Frontend-Implementierung verifiziert werden muss.

---

## Gruppe 1: Quellenverwaltung — Übersichtsliste aller Enrichment-Quellen

### TC-011-001: Enrichment-Quellen-Übersicht aufrufen (Admin)

**Anforderung:** REQ-011 §3.7 `GET /api/v1/enrichment/sources`; §4 Auth-Matrix (Admin: Lesen)
**Priorität:** Hoch
**Kategorie:** Listenansicht
**Status:** UI ausstehend — beschreibt Zielverhalten

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Mindestens die Quellen `perenual`, `gbif`, `openfarm` sind im System konfiguriert

**Testschritte:**
1. Nutzer navigiert zu `/admin/enrichment/sources` (oder dem entsprechenden Admin-Menüpunkt "Externe Quellen")
2. Nutzer wartet, bis die Seite vollständig geladen ist

**Erwartetes Ergebnis:**
- Eine Tabelle/Liste zeigt alle konfigurierten externen Quellen mit mindestens den Spalten: Name, Basis-URL, Priorität, Status (aktiv/inaktiv), letzter Sync-Zeitstempel, Anzahl synchronisierter Einträge
- Einträge für Perenual (Prio 1), OpenFarm (Prio 2), GBIF (Prio 3), Trefle (Prio 4) und Otreeba (Prio 5) sind sichtbar
- Der Status "aktiv" ist jeweils kenntlich gemacht (z. B. grüner Chip)

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, enrichment-sources, admin, listenansicht]

---

### TC-011-002: Enrichment-Quellen-Übersicht — Viewer-Rolle darf lesen

**Anforderung:** REQ-011 §4 Auth-Matrix (Enrichment Sources: Lesen = Ja)
**Priorität:** Mittel
**Kategorie:** Zugangsberechtigung
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Grower- oder Viewer-Rolle (nicht Admin)

**Testschritte:**
1. Nutzer navigiert direkt zu `/admin/enrichment/sources`
2. Nutzer versucht, die Seite zu laden

**Erwartetes Ergebnis:**
- Die Quellenliste ist lesend zugänglich (Seite lädt, Daten werden angezeigt)
- Buttons "Sync auslösen" sind nicht vorhanden oder disabled — nur Admin darf schreiben

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, auth, viewer, leseberechtigung]

---

### TC-011-003: Enrichment-Quelle — Detailansicht mit Health-Check-Status

**Anforderung:** REQ-011 §3.1 `health_check()`; §6 DoD "Health-Check"
**Priorität:** Hoch
**Kategorie:** Detailansicht
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Perenual API ist erreichbar (live oder per Stub)

**Testschritte:**
1. Nutzer öffnet die Quellenliste (`/admin/enrichment/sources`)
2. Nutzer klickt auf die Quelle "Perenual"
3. Nutzer wartet auf die Detailseite

**Erwartetes Ergebnis:**
- Detailseite zeigt: Name "Perenual", Basis-URL, Rate-Limit (100 req/Tag), Priorität 1
- Ein Health-Status-Indikator zeigt "Erreichbar" (grün) oder "Nicht erreichbar" (rot)
- Letzte Sync-Statistiken sind sichtbar: Anzahl abgerufener, erstellter, aktualisierter, übersprungener und fehlgeschlagener Einträge

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, health-check, perenual, detailansicht]

---

## Gruppe 2: Manueller Sync-Auslöser

### TC-011-004: Manuellen inkrementellen Sync für eine Quelle auslösen (Admin)

**Anforderung:** REQ-011 §3.7 `POST /api/v1/enrichment/sources/{source_key}/sync`; §6 DoD "Manueller Sync"
**Priorität:** Kritisch
**Kategorie:** Happy Path
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Mindestens eine Species ohne bestehendes Perenual-Mapping ist vorhanden (z. B. "Solanum lycopersicum" ohne Hardiness Zones)

**Testschritte:**
1. Nutzer öffnet die Quellenliste und wählt "Perenual"
2. Nutzer klickt auf den Button "Sync jetzt auslösen" (inkrementell, `full_sync=false`)
3. Nutzer beobachtet die UI-Rückmeldung

**Erwartetes Ergebnis:**
- Eine Bestätigungsmeldung erscheint (z. B. Snackbar/Toast: "Sync-Task gestartet für Quelle: Perenual")
- Task-ID wird angezeigt oder verlinkt
- Der Button wechselt während der Verarbeitung in einen Ladezustand (deaktiviert + Spinner)
- Nach Abschluss aktualisiert sich der Sync-Status der Quelle in der Liste

**Nachbedingungen:** Ein Sync-Lauf-Eintrag ist in der Sync-Historie der Quelle sichtbar

**Tags:** [req-011, sync-trigger, incremental, admin, happy-path]

---

### TC-011-005: Manuellen Full-Sync auslösen

**Anforderung:** REQ-011 §3.4 `full_sync=True`; §3.7 `?full_sync=true`
**Priorität:** Hoch
**Kategorie:** Happy Path
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle

**Testschritte:**
1. Nutzer öffnet die Quellenliste und wählt "GBIF"
2. Nutzer aktiviert die Option "Vollständige Neusynchronisation (Full Sync)"
3. Nutzer klickt auf "Sync auslösen"

**Erwartetes Ergebnis:**
- Snackbar/Benachrichtigung: "Full-Sync-Task gestartet für Quelle: GBIF"
- Die Quelle wird als "Sync läuft..." in der Liste markiert

**Nachbedingungen:** Ein Full-Sync-Run-Eintrag ist in der Sync-Historie sichtbar

**Tags:** [req-011, sync-trigger, full-sync, gbif]

---

### TC-011-006: Sync-Auslöser durch Nicht-Admin ist nicht möglich

**Anforderung:** REQ-011 §4 Auth-Matrix (Sync-Trigger: Schreiben = Admin)
**Priorität:** Hoch
**Kategorie:** Zugangsberechtigung / Fehlermeldung
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Grower-Rolle (nicht Admin)

**Testschritte:**
1. Nutzer öffnet die Quellenliste (lesend erlaubt)
2. Nutzer sieht — wenn der Button überhaupt angezeigt wird — den Button "Sync auslösen"
3. Nutzer klickt auf den Button

**Erwartetes Ergebnis:**
- Entweder: Der Button "Sync auslösen" ist gar nicht sichtbar
- Oder: Der Button ist sichtbar aber deaktiviert (disabled) mit Tooltip "Nur Administratoren können Syncs auslösen"
- Oder: Eine Fehlermeldung erscheint (Snackbar): "Keine Berechtigung für diese Aktion"

**Nachbedingungen:** Kein Sync wird gestartet

**Tags:** [req-011, auth, fehler, grower-rolle]

---

## Gruppe 3: Sync-Historie

### TC-011-007: Sync-Historie einer Quelle anzeigen

**Anforderung:** REQ-011 §3.7 `GET /api/v1/enrichment/sources/{source_key}/history`; §2 `sync_runs`-Collection
**Priorität:** Hoch
**Kategorie:** Listenansicht
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt (Admin oder Viewer)
- Für Quelle "Perenual" existieren mindestens 3 abgeschlossene Sync-Runs

**Testschritte:**
1. Nutzer öffnet die Detailseite der Quelle "Perenual"
2. Nutzer scrollt zur Sektion "Sync-Historie" oder klickt auf den Tab "Historie"

**Erwartetes Ergebnis:**
- Eine Tabelle zeigt die letzten Sync-Läufe in absteigender Zeitreihenfolge (neuester zuerst)
- Spalten: Gestartet am, Abgeschlossen am, Status (success/failed/partial), Abgerufen, Erstellt, Aktualisiert, Übersprungen, Fehlgeschlagen
- Erfolgreiche Läufe sind grün markiert, fehlgeschlagene rot

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, sync-history, listenansicht, perenual]

---

### TC-011-008: Sync-Run-Detail mit Fehlermeldungen anzeigen

**Anforderung:** REQ-011 §2 `sync_runs.errors`
**Priorität:** Mittel
**Kategorie:** Detailansicht / Fehlermeldung
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Ein Sync-Run mit `errors`-Einträgen existiert in der Historie

**Testschritte:**
1. Nutzer öffnet die Sync-Historie von "Perenual"
2. Nutzer klickt auf einen Eintrag mit Status "partial" oder "failed"

**Erwartetes Ergebnis:**
- Eine Detail-Ansicht oder ein Dialog öffnet sich
- Fehlermeldungen der einzelnen fehlgeschlagenen Einträge sind im Klartext sichtbar (z. B. "Solanum lycopersicum: Connection timeout")
- Anzahl der fehlgeschlagenen Einträge stimmt mit der Liste überein

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, sync-history, fehler-detail, partial-sync]

---

## Gruppe 4: Anreicherungs-Vorschläge in der Species-Detailansicht

### TC-011-009: Automatisch angereicherte Felder in der Species-Detailansicht sichtbar

**Anforderung:** REQ-011 §3.4 `_apply_enrichment` (auto-accept für leere Felder); §6 Szenario 1
**Priorität:** Kritisch
**Kategorie:** Happy Path / Detailansicht

**Vorbedingungen:**
- Nutzer ist eingeloggt (Grower-Rolle oder Admin)
- Species "Solanum lycopersicum" existiert im System
- Ein Perenual-Sync hat `hardiness_zones = ["7a", "7b", "8a"]` automatisch eingetragen (das Feld war vorher leer)

**Testschritte:**
1. Nutzer navigiert zu `/stammdaten/arten` (Artenliste)
2. Nutzer klickt auf die Art "Solanum lycopersicum"
3. Nutzer scrollt zur Feldgruppe "Umgebung" im Bearbeitungsformular

**Erwartetes Ergebnis:**
- Das Feld "Winterhärtezonen" zeigt die Chips "7a", "7b", "8a"
- Die Anzeige ist konsistent mit anderen manuell eingetragenen Feldern — kein visueller Unterschied erkennbar (automatisch übernommene Werte werden wie manuell eingetragene dargestellt)

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, auto-accept, species-detail, hardiness-zones, solanum-lycopersicum]

---

### TC-011-010: Externe Vorschläge für ein bereits befülltes Feld — Konflikt sichtbar

**Anforderung:** REQ-011 §3.4 lokale Hoheit (auto_accept nur wenn `local_value is None`); §6 Szenario 2
**Priorität:** Kritisch
**Kategorie:** Zustandswechsel / Detailansicht
**Status:** UI ausstehend (Enrichment-Vorschlagspanel)

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Species "Cannabis sativa" hat `max_height_cm = "250"` (manuell gesetzt)
- Trefle-Sync hat `max_height_cm = 300` als Vorschlag hinterlegt (`accepted = false, confidence = 0.7`)

**Testschritte:**
1. Nutzer navigiert zur Detailseite von "Cannabis sativa"
2. Nutzer öffnet den Tab "Anreicherungen" oder die Sektion "Externe Datenvorschläge"

**Erwartetes Ergebnis:**
- Ein Hinweisbereich zeigt: "Trefle schlägt vor: Wuchshöhe (cm) → 300 (Konfidenz: 70%)"
- Das aktuelle Feldwert "250" bleibt unverändert im Hauptformular
- Ein Button "Vorschlag übernehmen" und ein Button "Vorschlag ablehnen" sind sichtbar

**Nachbedingungen:** Feldreferenzwert "250" bleibt erhalten

**Tags:** [req-011, lokale-hoheit, konflikt, vorschlag, cannabis-sativa]

---

### TC-011-011: Externen Feldvorschlag manuell akzeptieren (Admin)

**Anforderung:** REQ-011 §3.7 `POST /api/v1/enrichment/species/{key}/enrichments/{source_key}/accept`; §6 Szenario 2
**Priorität:** Kritisch
**Kategorie:** Happy Path / Zustandswechsel
**Status:** UI ausstehend (Accept-Button)

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Species "Cannabis sativa" hat Trefle-Vorschlag: `max_height_cm = 300 (accepted = false)`
- Testschritte aus TC-011-010 wurden ausgeführt (Vorschlagsbereich sichtbar)

**Testschritte:**
1. Nutzer befindet sich auf der Detailseite von "Cannabis sativa", Sektion "Externe Datenvorschläge"
2. Nutzer klickt auf "Vorschlag übernehmen" neben dem Trefle-Vorschlag für "Wuchshöhe"

**Erwartetes Ergebnis:**
- Snackbar/Benachrichtigung: "Vorschlag übernommen: Wuchshöhe = 300"
- Im Hauptformular ändert sich das Feld "Wuchshöhe (cm)" auf "300"
- Der Vorschlag verschwindet aus der Liste "Offene Vorschläge" oder wird als "Akzeptiert" markiert

**Nachbedingungen:**
- `accepted = true` für dieses Mapping
- Das Feld `max_height_cm` zeigt im Formular "300"

**Tags:** [req-011, accept-enrichment, admin, zustandswechsel, cannabis-sativa]

---

### TC-011-012: Externen Feldvorschlag ablehnen (Admin)

**Anforderung:** REQ-011 §3.7 Accept/Reject; §6 DoD "Accept/Reject"
**Priorität:** Hoch
**Kategorie:** Zustandswechsel
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Species "Cannabis sativa" hat offenen Trefle-Vorschlag: `max_height_cm = 300`

**Testschritte:**
1. Nutzer öffnet den Tab "Anreicherungen" auf der Detailseite von "Cannabis sativa"
2. Nutzer klickt auf "Vorschlag ablehnen" neben dem Trefle-Vorschlag

**Erwartetes Ergebnis:**
- Snackbar/Benachrichtigung: "Vorschlag abgelehnt"
- Der Vorschlag wird aus der Liste offener Vorschläge entfernt oder als "Abgelehnt" dargestellt
- Das Hauptformularfeld "Wuchshöhe (cm)" bleibt bei "250"

**Nachbedingungen:** Feldwert "250" unverändert; kein weiterer Vorschlag für dieses Feld/diese Quelle-Kombination

**Tags:** [req-011, reject-enrichment, admin, zustandswechsel]

---

### TC-011-013: Nicht-Admin kann Vorschläge nur lesen, nicht akzeptieren

**Anforderung:** REQ-011 §4 Auth-Matrix (Species-Enrichments: Schreiben = Admin)
**Priorität:** Hoch
**Kategorie:** Zugangsberechtigung

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Grower-Rolle
- Species "Cannabis sativa" hat offenen Trefle-Vorschlag

**Testschritte:**
1. Nutzer öffnet die Detailseite von "Cannabis sativa"
2. Nutzer navigiert zur Sektion "Externe Datenvorschläge"

**Erwartetes Ergebnis:**
- Die Vorschläge sind lesend sichtbar (Quelle, Feldname, Vorschlagswert, Konfidenz)
- Die Buttons "Vorschlag übernehmen" und "Vorschlag ablehnen" sind entweder nicht vorhanden oder disabled

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, auth, grower, read-only-enrichments]

---

### TC-011-014: Datenprovenienz eines angereicherten Felds anzeigen

**Anforderung:** REQ-011 §1 Grundprinzipien "Datenprovenienz"; §2 `external_mappings.field_mappings.mapped_at, .confidence, .source_key`
**Priorität:** Hoch
**Kategorie:** Detailansicht
**Status:** UI ausstehend (Provenienz-Anzeige)

**Vorbedingungen:**
- Species "Solanum lycopersicum" hat `hardiness_zones` durch Perenual-Sync automatisch erhalten
- Ein `external_mappings`-Eintrag existiert mit `source_key = "perenual"`, `confidence = 0.9`, `mapped_at = "2026-02-26T03:15:00Z"`

**Testschritte:**
1. Nutzer öffnet die Detailseite von "Solanum lycopersicum"
2. Nutzer bewegt den Cursor über das Feld "Winterhärtezonen" oder klickt auf ein Provenienz-Symbol (i-Icon) neben dem Feld

**Erwartetes Ergebnis:**
- Ein Tooltip oder ein Provenienz-Infobereich zeigt:
  - Quelle: "Perenual"
  - Zuletzt synchronisiert: "26.02.2026, 03:15 Uhr" (oder relative Zeitangabe)
  - Konfidenz: "90%"
- Manuell eingetragene Felder (ohne Provenienz) zeigen kein Provenienz-Symbol

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, datenprovenienz, tooltip, konfidenz, perenual]

---

## Gruppe 5: Taxonomie-Normalisierung via GBIF

### TC-011-015: Wissenschaftlicher Name und Synonyme durch GBIF angereichert

**Anforderung:** REQ-011 §1.2 Daten-Mapping (scientific_name via GBIF); §6 Szenario 3
**Priorität:** Kritisch
**Kategorie:** Happy Path / Detailansicht

**Vorbedingungen:**
- Nutzer ist eingeloggt (Grower oder Admin)
- Species "Tomate" existiert ohne `scientific_name` im System
- GBIF-Sync hat ausgeführt und `scientific_name = "Solanum lycopersicum"`, `family = "Solanaceae"`, `genus = "Solanum"` eingetragen
- Synonyme `["Lycopersicon esculentum"]` wurden gespeichert

**Testschritte:**
1. Nutzer navigiert zur Artenliste `/stammdaten/arten`
2. Nutzer sucht nach "Tomate" in der Suchleiste
3. Nutzer klickt auf den Eintrag
4. Nutzer scrollt zur Feldgruppe "Taxonomie"

**Erwartetes Ergebnis:**
- Das Feld "Wissenschaftlicher Name" zeigt "Solanum lycopersicum"
- Das Feld "Familie" zeigt "Solanaceae" (verlinkt zur Botanischen Familie)
- Das Feld "Gattung" zeigt "Solanum"
- Das Feld "Synonyme" enthält den Chip "Lycopersicon esculentum"

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, gbif, taxonomie, synonyme, scientific-name, solanaceae]

---

### TC-011-016: Botanische Familie durch GBIF-Anreicherung automatisch verknüpft

**Anforderung:** REQ-011 §1.2 Taxonomische Klassifikation → `BotanicalFamily`
**Priorität:** Hoch
**Kategorie:** Zustandswechsel / Detailansicht

**Vorbedingungen:**
- Species "Paprika" ohne Familienzuordnung im System
- GBIF-Sync hat `family = "Solanaceae"` eingetragen
- Botanische Familie "Solanaceae" existiert bereits in den Stammdaten

**Testschritte:**
1. Nutzer öffnet die Detailseite von "Paprika"
2. Nutzer prüft das Dropdown-Feld "Familie"

**Erwartetes Ergebnis:**
- Das Feld "Familie" zeigt "Solanaceae" als ausgewählten Wert
- Der Link "Familie anzeigen →" führt zur Detailseite der Familie Solanaceae

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, gbif, botanische-familie, verknüpfung, solanaceae]

---

## Gruppe 6: Companion Planting via OpenFarm

### TC-011-017: Companion-Planting-Kante durch OpenFarm-Sync sichtbar

**Anforderung:** REQ-011 §1.2 Companion Planting → `COMPATIBLE_WITH`-Kante; §6 Szenario 4
**Priorität:** Hoch
**Kategorie:** Happy Path / Navigation

**Vorbedingungen:**
- Nutzer ist eingeloggt
- "Daucus carota" (Karotte) und "Allium cepa" (Zwiebel) existieren im System
- OpenFarm-Sync hat eine `COMPATIBLE_WITH`-Beziehung zwischen beiden erstellt

**Testschritte:**
1. Nutzer navigiert zu `/stammdaten/mischkultur` (Companion-Planting-Seite)
2. Nutzer sucht nach "Daucus carota"

**Erwartetes Ergebnis:**
- In der Kompatibilitätsliste von "Daucus carota" erscheint "Allium cepa" als kompatible Pflanzung
- Ein Kompatibilitätswert oder ein Label ist sichtbar (z. B. "Kompatibel", ggf. Punktzahl)
- Die Quelle "OpenFarm" ist als Herkunft der Empfehlung erkennbar

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, openfarm, companion-planting, kompatibel, daucus-carota]

---

### TC-011-018: Neue Species erhält keine Companion-Vorschläge wenn OpenFarm kein Mapping hat

**Anforderung:** REQ-011 §3.4 `records_skipped` wenn kein Match gefunden
**Priorität:** Mittel
**Kategorie:** Listenansicht / Leerzustand

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Eine exotische Species ohne Einträge in OpenFarm ist im System vorhanden

**Testschritte:**
1. Nutzer navigiert zur Companion-Planting-Seite
2. Nutzer sucht nach der exotischen Species

**Erwartetes Ergebnis:**
- Die Companion-Planting-Liste zeigt für diese Species einen Leerzustand-Hinweis, z. B. "Keine Kompatibilitätsdaten verfügbar"
- Die Seite zeigt keinen Fehler, kein Crash

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, openfarm, leerzustand, kein-mapping, graceful-degradation]

---

## Gruppe 7: Cannabis-Sorten via Otreeba

### TC-011-019: Cannabis-Sorte mit Otreeba-Daten in der Cultivar-Detailansicht

**Anforderung:** REQ-011 §1.2 Cannabis-Genetik/Blütezeit/Typ via Otreeba; §6 Szenario 5
**Priorität:** Hoch
**Kategorie:** Detailansicht

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Species "Cannabis sativa" hat eine Sorte "OG Kush" im System
- Otreeba-Sync hat `genetic_lineage`, `strain_type = "indica"`, `flowering_time_days = 63` eingetragen

**Testschritte:**
1. Nutzer navigiert zur Detailseite von "Cannabis sativa"
2. Nutzer wechselt zum Tab "Sorten"
3. Nutzer klickt auf die Sorte "OG Kush"

**Erwartetes Ergebnis:**
- In der Sortendetailansicht sind sichtbar: Genetische Abstammung, Sortentyp "Indica", Blütezeit "63 Tage"
- Die Daten sind als externe Quelle "Otreeba" gekennzeichnet (sofern Provenienz-Anzeige implementiert)

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, otreeba, cannabis, cultivar, strain-type, flowering-time]

---

## Gruppe 8: Graceful Degradation bei API-Ausfall

### TC-011-020: Sync-Fehler bei ausgefallener Perenual-API — andere Quellen laufen weiter

**Anforderung:** REQ-011 §1 Grundprinzipien "Graceful Degradation"; §6 Szenario 6
**Priorität:** Kritisch
**Kategorie:** Fehlermeldung / Zustandswechsel
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Perenual-API ist nicht erreichbar (simuliert durch ungültigen API-Key oder Netzwerkfehler)
- GBIF- und OpenFarm-APIs sind erreichbar

**Testschritte:**
1. Nutzer löst einen manuellen "Sync alle Quellen" aus
2. Nutzer wartet auf Abschluss und öffnet die Sync-Historie

**Erwartetes Ergebnis:**
- In der Sync-Historie ist für Perenual ein Eintrag mit Status "Fehlgeschlagen" sichtbar
- Für GBIF und OpenFarm stehen eigene Einträge mit Status "Erfolgreich"
- Bestehende Stammdaten (z. B. bereits angereicherte Winterhärtezonen) sind unverändert
- Eine Fehlermeldung im UI oder in der Sync-Detail-Ansicht gibt den Fehlergrund an

**Nachbedingungen:** Keine Stammdaten verändert; nur Sync-Run-Einträge erstellt

**Tags:** [req-011, graceful-degradation, api-ausfall, perenual, fehler]

---

### TC-011-021: Nach dreifachem Retry erscheint Quelle dauerhaft als "fehlgeschlagen"

**Anforderung:** REQ-011 §3.5 `max_retries=3`
**Priorität:** Mittel
**Kategorie:** Fehlermeldung
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist Admin
- Perenual-API ist dauerhaft nicht erreichbar
- Drei Retry-Versuche des Celery-Tasks sind abgeschlossen

**Testschritte:**
1. Nutzer öffnet die Quellen-Übersicht
2. Nutzer sieht die Zeile für Perenual

**Erwartetes Ergebnis:**
- Status von Perenual wird als "Fehlgeschlagen" (roter Indikator) dargestellt
- Letzter Sync-Zeitpunkt zeigt den Zeitpunkt des letzten Versuches
- Eine Warnmeldung oder Hinweis ist sichtbar: z. B. "Letzte Synchronisation fehlgeschlagen"

**Nachbedingungen:** Keine Stammdaten verändert

**Tags:** [req-011, retry, max-retries, perenual, fehlerstatus]

---

## Gruppe 9: Checksum-basiertes Überspringen

### TC-011-022: Identische externe Daten werden als "übersprungen" gezählt (kein Update)

**Anforderung:** REQ-011 §3.4 Checksum-Vergleich; §6 Szenario 7
**Priorität:** Hoch
**Kategorie:** Zustandswechsel / Sync-Historie
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt mit Admin-Rolle
- Species "Ocimum basilicum" hat ein bestehendes Mapping zu Perenual mit einem bereits gespeicherten Checksum
- Perenual liefert dieselben Daten wie beim letzten Sync (keine Änderung)

**Testschritte:**
1. Nutzer löst einen manuellen Sync für Perenual aus
2. Nutzer öffnet nach Abschluss die Sync-Historie für Perenual
3. Nutzer klickt auf den neuesten Sync-Lauf

**Erwartetes Ergebnis:**
- In der Sync-Run-Detailansicht ist "Ocimum basilicum" unter "Übersprungen" aufgelistet
- Der Zähler "Übersprungen" ist um 1 erhöht (oder mehr, je nach weiteren unveränderten Einträgen)
- Der Zähler "Aktualisiert" blieb unverändert für diese Species

**Nachbedingungen:** Stammdaten von "Ocimum basilicum" unverändert; `last_checked_at` im Mapping aktualisiert

**Tags:** [req-011, checksum, idempotenz, oversprungen, ocimum-basilicum]

---

## Gruppe 10: Externe Suche (Search-Endpunkt)

### TC-011-023: Externe Suche nach Pflanzenname ausführen

**Anforderung:** REQ-011 §3.7 `POST /api/v1/enrichment/search`
**Priorität:** Hoch
**Kategorie:** Happy Path
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt (Admin oder Viewer)

**Testschritte:**
1. Nutzer navigiert zur Admin-Sektion "Externe Suche" oder öffnet das Such-Panel
2. Nutzer gibt "Tomato" in das Suchfeld ein
3. Nutzer klickt "Suchen" (ohne Quellen-Filter, d. h. alle aktiven Quellen)

**Erwartetes Ergebnis:**
- Ergebnisse aus allen verfügbaren Quellen (Perenual, GBIF, OpenFarm etc.) werden als gruppierte Liste angezeigt
- Jede Quelle zeigt ihre Treffer separat (z. B. "Perenual (3 Treffer)", "GBIF (5 Treffer)")
- Mindestens ein Ergebnis zeigt "Solanum lycopersicum" aus GBIF oder Perenual

**Nachbedingungen:** Keine lokalen Daten geändert

**Tags:** [req-011, external-search, suche, alle-quellen]

---

### TC-011-024: Externe Suche auf eine bestimmte Quelle einschränken

**Anforderung:** REQ-011 §3.7 `search?source_key=gbif`
**Priorität:** Mittel
**Kategorie:** Happy Path / Filter
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt

**Testschritte:**
1. Nutzer öffnet das externe Such-Panel
2. Nutzer wählt im Quellenfilter nur "GBIF" aus
3. Nutzer gibt "Cannabis" ein und klickt "Suchen"

**Erwartetes Ergebnis:**
- Ergebnisse werden ausschließlich aus GBIF angezeigt
- Keine Ergebnisse von Perenual, OpenFarm oder anderen Quellen sind sichtbar

**Nachbedingungen:** Keine lokalen Daten geändert

**Tags:** [req-011, external-search, quellen-filter, gbif]

---

### TC-011-025: Externe Suche — Quelle antwortet mit Fehler, andere Quellen zeigen Ergebnisse

**Anforderung:** REQ-011 §3.7 Fehlerbehandlung im Search-Endpoint (try/except pro Quelle)
**Priorität:** Mittel
**Kategorie:** Fehlermeldung / Graceful Degradation
**Status:** UI ausstehend

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Perenual-API ist nicht erreichbar, GBIF ist erreichbar

**Testschritte:**
1. Nutzer führt eine externe Suche ohne Quellenfilter nach "Basil" durch

**Erwartetes Ergebnis:**
- GBIF-Ergebnisse werden angezeigt
- Für Perenual erscheint ein Fehlerhinweis (z. B. "Perenual: Nicht erreichbar" oder Fehlermeldungstext im entsprechenden Quellenbereich)
- Die Seite lädt vollständig, kein Crash oder leere Seite

**Nachbedingungen:** Keine Daten geändert

**Tags:** [req-011, external-search, fehler, perenual, graceful-degradation]

---

## Gruppe 11: Lokale Hoheit — Manuelle Eingabe hat Vorrang

### TC-011-026: Manuell gesetztes Feld wird nach Sync nicht überschrieben

**Anforderung:** REQ-011 §1 Grundprinzipien "Lokale Hoheit"; §3.4 `auto_accept = local_value is None`
**Priorität:** Kritisch
**Kategorie:** Regression / Zustandswechsel

**Vorbedingungen:**
- Nutzer ist eingeloggt als Admin
- Species "Cannabis sativa" hat `max_height_cm = "250"` (manuell eingetragen)
- Trefle-Sync wird ausgeführt und liefert `max_height_cm = 300`

**Testschritte:**
1. Nutzer löst einen Perenual/Trefle-Sync manuell aus
2. Nach Abschluss des Syncs öffnet der Nutzer die Detailseite von "Cannabis sativa"
3. Nutzer prüft das Feld "Wuchshöhe (cm)"

**Erwartetes Ergebnis:**
- Das Feld "Wuchshöhe (cm)" zeigt weiterhin "250" — der externe Wert wurde NICHT automatisch übernommen
- In der Sektion "Externe Datenvorschläge" (falls sichtbar) erscheint der Trefle-Vorschlag "300 (nicht übernommen)"

**Nachbedingungen:** Feldwert "250" unverändert

**Tags:** [req-011, lokale-hoheit, kein-überschreiben, cannabis-sativa, trefle, regression]

---

### TC-011-027: Manuell eingegebene Species-Felder nach Sync im Formular noch bearbeitbar

**Anforderung:** REQ-011 §1 Lokale Hoheit; REQ-001 §3 Species-Bearbeitung
**Priorität:** Hoch
**Kategorie:** Regression

**Vorbedingungen:**
- Nutzer ist eingeloggt als Admin
- Ein Sync für beliebige Quelle ist abgeschlossen
- Species "Mentha piperita" hat durch Perenual angereicherte Winterhärtezonen

**Testschritte:**
1. Nutzer öffnet Detailseite von "Mentha piperita"
2. Nutzer klickt in das Feld "Winterhärtezonen" und entfernt einen vorhandenen Chip ("7a")
3. Nutzer klickt "Speichern"

**Erwartetes Ergebnis:**
- Speicherung erfolgreich (Snackbar-Bestätigung: "Gespeichert")
- Nach Neuladen der Seite: Chip "7a" ist nicht mehr im Feld vorhanden
- Die manuelle Änderung überschreibt den vorherigen externen Wert dauerhaft

**Nachbedingungen:** `hardiness_zones` enthält nicht mehr "7a"

**Tags:** [req-011, manuelle-eingabe, feld-bearbeitung, nach-sync, mentha-piperita]

---

## Gruppe 12: Edge Cases und Grenzwerte

### TC-011-028: Species ohne Mapping — Anreicherungsbereich zeigt Leerzustand

**Anforderung:** REQ-011 §2 AQL "Nicht-angereicherte Spezies"; §6 DoD "Sync-Historie"
**Priorität:** Mittel
**Kategorie:** Leerzustand / Detailansicht
**Status:** UI ausstehend (Enrichment-Tab)

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Species "Sehr seltene Exotik" wurde neu angelegt und hat noch keine externen Mappings

**Testschritte:**
1. Nutzer öffnet die Detailseite von "Sehr seltene Exotik"
2. Nutzer navigiert zum Tab "Anreicherungen"

**Erwartetes Ergebnis:**
- Der Tab "Anreicherungen" zeigt einen Leerzustand: "Keine externen Daten verfügbar"
- Kein Fehler, kein Crash
- Felder im Hauptformular sind alle leer (wie nach manueller Erstellung erwartet)

**Nachbedingungen:** Keine Datenänderungen

**Tags:** [req-011, leerzustand, kein-mapping, neue-species]

---

## Abdeckungs-Matrix

| Spec-Abschnitt | Testfall-IDs | Status |
|---|---|---|
| §1 Business Case — Lokale Hoheit | TC-011-010, TC-011-026, TC-011-027 | Kritisch, abgedeckt |
| §1 Business Case — Datenprovenienz | TC-011-014 | UI ausstehend |
| §1 Business Case — Graceful Degradation | TC-011-020, TC-011-021, TC-011-025 | UI ausstehend |
| §1 Business Case — Idempotenz / Checksum | TC-011-022 | UI ausstehend |
| §1.1 Externe Quellen — Übersichtsliste | TC-011-001, TC-011-002 | UI ausstehend |
| §1.1 Health-Check | TC-011-003 | UI ausstehend |
| §1.2 Daten-Mapping — Taxonomie (GBIF) | TC-011-015, TC-011-016 | Abgedeckt |
| §1.2 Daten-Mapping — Hardiness Zones (Perenual) | TC-011-009, TC-011-026 | Abgedeckt |
| §1.2 Daten-Mapping — Companion Planting (OpenFarm) | TC-011-017, TC-011-018 | Abgedeckt |
| §1.2 Daten-Mapping — Cannabis-Sorten (Otreeba) | TC-011-019 | Abgedeckt |
| §3.4 Sync-Engine — Inkrementell | TC-011-004, TC-011-022 | UI ausstehend |
| §3.4 Sync-Engine — Full Sync | TC-011-005 | UI ausstehend |
| §3.4 apply_enrichment — Auto-Accept | TC-011-009 | Abgedeckt |
| §3.4 apply_enrichment — Konflikt (Lokale Hoheit) | TC-011-010, TC-011-026 | Abgedeckt / UI ausstehend |
| §3.5 Celery-Tasks — max_retries | TC-011-021 | UI ausstehend |
| §3.7 REST-API — list_sources | TC-011-001, TC-011-002 | UI ausstehend |
| §3.7 REST-API — trigger_sync | TC-011-004, TC-011-005, TC-011-006 | UI ausstehend |
| §3.7 REST-API — sync_history | TC-011-007, TC-011-008 | UI ausstehend |
| §3.7 REST-API — species_enrichments | TC-011-010, TC-011-013, TC-011-028 | UI ausstehend |
| §3.7 REST-API — accept_enrichment | TC-011-011, TC-011-012 | UI ausstehend |
| §3.7 REST-API — external_search | TC-011-023, TC-011-024, TC-011-025 | UI ausstehend |
| §4 Auth — Admin vs. Viewer | TC-011-002, TC-011-006, TC-011-013 | UI ausstehend |
| §6 Szenario 1 — Neues Feld auto-accept | TC-011-009 | Abgedeckt |
| §6 Szenario 2 — Konflikt / Lokale Hoheit | TC-011-010, TC-011-011, TC-011-012 | UI ausstehend |
| §6 Szenario 3 — GBIF Taxonomie | TC-011-015, TC-011-016 | Abgedeckt |
| §6 Szenario 4 — Companion Planting OpenFarm | TC-011-017 | Abgedeckt |
| §6 Szenario 5 — Otreeba Cannabis | TC-011-019 | Abgedeckt |
| §6 Szenario 6 — Graceful Degradation | TC-011-020, TC-011-025 | UI ausstehend |
| §6 Szenario 7 — Checksum Skip | TC-011-022 | UI ausstehend |

**Legende:**
- **Abgedeckt:** Testfall kann bereits gegen bestehende Frontend-Seiten ausgeführt werden (Species-Detailseite)
- **UI ausstehend:** Testfall setzt eine noch nicht implementierte Enrichment-Admin-UI voraus; wird aktiviert, sobald das Feature entwickelt wird
