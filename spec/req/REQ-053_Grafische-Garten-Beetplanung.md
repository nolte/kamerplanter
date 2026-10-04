# Spezifikation: REQ-053 - Grafische Garten- und Beetplanung

```yaml
ID: REQ-053
Titel: Grafische Garten- und Beetplanung (metrischer Gartenplan, Beetverwaltung, Pflanzplanung im Beet, Beetpflege und Pflegeprotokoll)
Kategorie: Infrastruktur & Planung
Fokus: Nutzpflanze (Outdoor, Gewächshaus, Hochbeet, Kübel); Zierpflanze mitgedacht
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, React 19, TypeScript 6, MUI 9, Redux Toolkit, WeasyPrint
Status: Entwurf
Priorität: Hoch
Version: 1.2 (drei Reviews eingearbeitet: Agrobiologie, Outdoor-Persona, Security)
Datum: 2026-10-04
Tags: [garden-plan, bed, geometry, canvas, planting-layout, maintenance, care-log, irrigation-zone, mobile, mvp]
Abhängigkeit: REQ-002 v4.4 (Standort-Hierarchie Site → Location → Slot, LocationTypes, `adjacent_to`), REQ-013 v2.7 (Pflanzdurchlauf, `PlantingRunEntry.spacing_cm`, `run_at_location`), REQ-006 (Task-Modell, `entity_type`/`entity_key`, `has_task`), REQ-022 (Pflegeerinnerungen, `care_confirmations`), ADR-008 (einheitlicher Abschluss-Übergang), REQ-014 (`watering_events`), REQ-004 (Flächendosierung, Bodenanalyse-Felder), REQ-019 (Substratchargen, `filled_with`), REQ-028 (Mischkultur-Graph, Nachbarschafts-Check), REQ-001 (Fruchtfolge-Kategorien, `rotation_after`), REQ-007 (Ernte-Batches), REQ-018 (Aktorik, `irrigation_valve`), REQ-037 (ET0-Bewässerungsbedarf), REQ-034/REQ-052/NFR-013 (Fotos, Attachments), REQ-032 (Druck/PDF, `LOCATION_OVERVIEW`), REQ-024 v1.7 (Mandant), REQ-049 v1.4 (Rollenvokabular), REQ-042 (Modul-Sichtbarkeit), REQ-025/NFR-011 (DSGVO), NFR-006 (Fehlerformat), NFR-016 (Migrationen), UI-NFR-001/002/003/012/019/022
Wird benötigt von: REQ-032 (visueller Grundriss im Beetplan-Druck), REQ-028 §7.3 (Beetplan-Visualisierung), REQ-047 (Überwinterungsorte auf dem Plan), künftige Sonnen-/Schattenberechnung
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.2 | 2026-10-04 | **Drei Reviews eingearbeitet** (`spec/analysis/agrobiology-review-req-053.md`, `outdoor-garden-planner-review-req-053.md`, `security-review-req-053.md`) mit Betreiberentscheidungen: **O-07 revidiert** (K-001) — Zehrerstufe (3 Werte) und `nitrogen_fixing` (Bool) getrennt, `PlanRole` für den Rotationsplan (§16.3); **`tenant_key` auf Location und Slot** in v0072 (SR-022, §20.13, §22.3); **Fruchtfolge- und Mischkultur-Hinweis sowie Vorjahresanzeige in den MVP** (F-12, GP-FR-131/132 → MUST); **Plan-Revision nur für Struktur** — Slot-Korrekturen und Quick-Planting laufen außerhalb (F-09, D-06); Retention `care_events` 5 Jahre (SR-005, NFR-011); `performed_by`-Filter für alle Rollen (SR-020); **Slot-Reservierung mit Zeitfenster** und UC „Beet räumen" (F-01/F-02); **Beetstatus = Lebenszyklus, Saisonzustand abgeleitet** (W-014). Dazu: Bodenmodell neu (K-002/K-003: `soil_texture`, `growing_medium_kind`, `conditions[]`, Messwerte mit Methode/Einheit), Anbaupausen je Familie (K-004), Layout-Semantik präzisiert (W-002/W-003: `grid`, `triangular`, Rand quer/längs, Reihenrichtung, Kapazität mit Reihenabstand), Steckbrief-Felder statt Duplikat (W-001), Pflegekatalog erweitert (W-006/F-03), Tasks an Kompost/Wasserquelle (W-008), Zeltregeln (W-016), Schattenfelder vorbereitet (§29), Security: Batch-Rollenprüfung je Op (SR-001), Referenzauflösung GP-NFR-058 (SR-002/003), Quoten (SR-004), Redaktion GP-FR-109 (SR-006), Kaskade/Export (SR-007/008), `trigger` serverseitig (SR-009), Matrix bereinigt (SR-010), Pflicht-Audit (SR-011), Komplexitäts-/Zeitbudget (SR-012), Prüfreihenfolge (SR-013), HA-Entität (SR-014), `url_fetcher`/SVG-Allowlist (SR-015), CSV (SR-016), Rate-Limits (SR-017), Import (SR-018), Sentry/Cache (SR-019). Feldmodus: Sofortspeichern, Schnellprotokoll-Chips, Rückgängig-Snackbar, Stepper als Standard (F-13/F-16/F-18). MoSCoW/MVP-Widersprüche bereinigt (F-06). 11 neue Akzeptanzkriterien (GP-ACC-039…049). |
| 1.1 | 2026-10-04 | **Alle offenen Punkte entschieden** (Betreiber, §32). Folgenreichste Entscheidung O-01: **ein Positionsmodell für Zelt und Beet** — `Slot.geometry` gilt für alle Slots, `Slot.position` (Rasterzelle) wird in Welle 1 per Migration in Geometrie überführt und entfernt (§9.2a, §20.5); damit entfallen der Indoor-Feature-Flag V-18 und die Scope-Einschränkung für Indoor-Sites (§2.3, O-08). O-02: `Location.dimensions` wird in Welle 1 entfernt, nicht gespiegelt (§20.8). O-05: ADR-008 wird in Welle 0 auf Accepted gehoben, RRULE kanonisch, bestehende Cron-Regeln werden migriert (§12.2). O-07: REQ-053 legt das gemeinsame Zehrer-Enum fest (§16.3, GP-FR-138) und ändert REQ-001/REQ-002 mit. O-13: Durchfluss manuell mit optionaler HA-Überschreibung und Provenienz (GP-FR-114). Übrige Punkte wie empfohlen. Roadmap Welle 0/1 und Issue-Kandidaten angepasst. |
| 1.0 | 2026-10-04 | Erstfassung. Fasst die in REQ-002 §1 („Visuelle Beetplanung") nur als Business-Case angelegte Gartenplanung zu einer eigenen, implementierbaren Anforderung zusammen: metrisches Geometriemodell auf Site/Location/Slot (§7, §20), neue Collections `garden_objects`, `care_events`, `irrigation_zones` (§20), Plan-Batch-API mit optimistischer Nebenläufigkeit (§21), Rendering-Entscheidung SVG-in-React mit austauschbarer Renderer-Grenze (§19), Feldmodus für die mobile Nutzung im Garten (§18), MVP-Abgrenzung (§28) und 30 Akzeptanzkriterien (§30). Die Vorgabe aus dem Auftrag (Go-Backend, Vue.js, Tailwind) widerspricht dem verbindlichen Stack (`spec/stack.md`: FastAPI, React 19, MUI 9) und wurde **nicht** übernommen — siehe §3.2. |

---

## Inhalt

1. Executive Summary · 2. Ziel und Scope · 3. Ausgangssituation · 4. Benutzergruppen · 5. Personas · 6. Use Cases · 7. Fachliches Domänenmodell · 8. Funktionale Anforderungen (Übersicht) · 9. Grafischer Garteneditor · 10. Beetverwaltung · 11. Pflanzplanung · 12. Beetpflege · 13. Pflegehistorie · 14. Bewässerung · 15. Boden/Nährstoffe · 16. Fruchtfolge/Mischkultur · 17. UX/UI · 18. Mobile Nutzung · 19. Technische Architektur · 20. Datenmodell · 21. API · 22. Validierung · 23. Import/Export · 24. Accessibility · 25. Performance · 26. Sicherheit · 27. Observability · 28. MVP · 29. Future Features · 30. Akzeptanzkriterien · 31. Risiken · 32. Offene Fragen · 33. Entscheidungsvorlagen · 34. Implementierungs-Roadmap · Anhang A: GitHub-Issue-Kandidaten

**ID-Schema dieses Dokuments.** Anforderungen tragen das Präfix `GP-` (Garden Planner), damit sie nicht mit den Repository-weiten Dokument-IDs kollidieren (`spec/nfr/NFR-012` ist ein Dokument, `GP-NFR-012` eine Anforderung in diesem Dokument):

| Präfix | Bedeutung | Beispiel |
|--------|-----------|----------|
| `GP-FR-nnn` | Functional Requirement | GP-FR-010 |
| `GP-NFR-nnn` | Non-Functional Requirement | GP-NFR-003 |
| `GP-UX-nnn` | UX Requirement | GP-UX-007 |
| `GP-API-nnn` | API Requirement | GP-API-002 |
| `GP-DATA-nnn` | Data Requirement | GP-DATA-004 |
| `GP-ACC-nnn` | Acceptance Criterion | GP-ACC-012 |

Prioritäten nach MoSCoW: **MUST** (MVP-Pflicht), **SHOULD** (erste Folgeversion), **COULD** (bei Gelegenheit), **WON'T** (bewusst nicht in diesem Vorhaben). Die Spalte „MVP" in den Tabellen bedeutet: Teil des in §28 abgegrenzten MVP.

---

## 1. Executive Summary

Kamerplanter kennt heute Standorte als **Baum** (Site → Location → Slot), nicht als **Fläche**. Ein Beet ist eine Location vom Typ `bed` mit einer Quadratmeterzahl (`area_m2`) und einem undokumentierten Maß-Tupel (`dimensions`); ein Pflanzplatz ist ein Slot mit einer Integer-Rasterposition `(row, col)`. Wo ein Beet im Garten liegt, wie es geschnitten ist, was daneben steht und wo im Beet die einzelne Pflanze wächst, weiß das System nicht. Genau das braucht die Zielgruppe der Freiland- und Gemeinschaftsgärtner (ZG-002, ZG-004), die ihre Saison am Schreibtisch plant und mit dem Smartphone im Beet steht.

Diese Anforderung erweitert das vorhandene Standortmodell um ein **metrisches Geometriemodell** (Meter, nicht Pixel) und stellt darauf einen **grafischen Gartenplan** bereit, in dem Gartenflächen, Beete, Wege, Gebäude, Bäume, Gewächshäuser und Wasserquellen maßstäblich gezeichnet, verschoben, gedreht und skaliert werden. Beete werden darin mit dem bestehenden Pflanzdurchlauf-Modell (REQ-013) bepflanzt: Pflanzabstand und Reihenabstand erzeugen Pflanzpositionen, die als Slots persistiert und als Pflanzen auf dem Plan dargestellt werden. Pflegeaufgaben hängen am Beet und an der Pflanze (REQ-006, REQ-022) und münden in ein **einheitliches, revisionssicheres Pflegeprotokoll** (`care_events`), das die heute auf vier Collections verteilten Pflegeereignisse an einem Ort nachvollziehbar macht.

Drei Grundsätze tragen den Entwurf: **Das Domänenmodell führt, das Canvas folgt** (die Rendering-Bibliothek ist hinter einer Renderer-Grenze austauschbar, §19.4); **reale Maße sind die persistente Wahrheit** (Pixel entstehen erst beim Zeichnen, §9.2); **keine Parallelarchitektur** (Garten = Site, Beet = Location, Pflanzposition = Slot, Pflegeaufgabe = Task — es werden nur drei neue Collections eingeführt, §7.1).

Der MVP (§28) umfasst: Gartenfläche und Beete zeichnen und bearbeiten, metrisches Raster mit Snap, Speichern über eine transaktionale Batch-API mit Konfliktschutz, Pflanzdurchläufe auf Beeten mit automatischer Positionsberechnung, Pflanzendarstellung, Pflegeaufgaben am Beet mit Erledigung und Historie, PDF-Export mit Maßstab und ein mobiler **Feldmodus**. Bewässerungszonen, Boden-Historie, Fruchtfolge-/Mischkultur-Overlays, GeoJSON und Sonnen-/Schattenberechnung sind spezifiziert, aber bewusst nachgelagert (§28.3, §29).

---

## 2. Ziel und Scope

### 2.1 Ziel

Der Nutzer bildet seine reale Gartenanlage **maßstäblich oder zumindest metrisch plausibel** ab und nutzt diese Abbildung als Oberfläche für das fachliche Gartenmodell: Beete anlegen, bepflanzen, pflegen, dokumentieren, auswerten. Die Grafik ist ein **Zugang** zum Modell, kein eigenständiger Zeicheneditor.

### 2.2 Im Scope

- Metrisches Geometriemodell für Site (Gartengrenze), Location (Beete, Bereiche, Gewächshäuser) und Slot (Pflanzpositionen im Beet) sowie nicht bepflanzbare Gartenobjekte (Weg, Rasen, Gebäude, Baum, Strauch, Mauer/Zaun, Wasserquelle, Kompost, Lager, Sonstiges).
- Webbasierter Editor mit Zoom, Pan, Auswahl, Mehrfachauswahl, Verschieben, Drehen, Skalieren, Polygon-Punktbearbeitung, Duplizieren, Löschen, Raster, Snap, Undo/Redo, Tastaturbedienung, Touch.
- Beetverwaltung mit Beettypen, Vorlagen, Bodenprofil, Status, Bepflanzungsübersicht (geplant / aktiv / historisch).
- Pflanzplanung im Beet über PlantingRuns: Pflanzabstand, Reihenabstand, Pflanztiefe, Reihen, Zonen, freie Positionen, automatische Positionsberechnung, Korrektur der tatsächlichen Position.
- Beetpflege: Aufgabenkatalog, einmalige/wiederkehrende/vorgeschlagene Aufgaben, Erledigung, einheitliches Pflegeprotokoll.
- Bewässerungszonen als fachliches Modell (Integration mit REQ-018-Aktorik vorbereitet).
- Boden/Substrat-Bezug des Beets; Fruchtfolge- und Mischkultur-Anbindung als fachliche Anforderung.
- API-first (REST/OpenAPI), ArangoDB-Persistenz, Import/Export (JSON-Sicherung, PDF, SVG, PNG, CSV; GeoJSON als COULD).
- Responsive Nutzung inkl. Feldmodus für Smartphone/Tablet im Garten.

### 2.3 Nicht im Scope

- Ein allgemeiner CAD-/GIS-Editor (keine Layer-Verwaltung jenseits der fachlichen Objektklassen, keine Höhenmodelle, kein Georeferenzieren von Luftbildern im MVP).
- Ein zweites Positionsmodell für Indoor: Growzelte, Regale und Beete laufen auf **demselben** Slot-Geometriemodell (§9.2a, Entscheidung O-01). Was nicht im Scope ist, sind indoor-spezifische Editor-Funktionen (Ebenen-Stapel eines Regals, Topfgrößen-Raster) — ein Zelt ist eine Location mit Rechteck-Geometrie und Punkt-Slots, mehr nicht.
- Automatische Bewässerungssteuerung (REQ-018 bleibt zuständig; hier nur Zonen-Modell und Verknüpfung).
- Sonnen-/Schattenberechnung, KI-Pflanzplanung, Ertragsplanung (§29).
- Änderungen am Tenant-, Rollen- oder Rechtemodell (REQ-024/REQ-049 gelten unverändert).

### 2.4 Abgrenzung zu bestehenden Dokumenten

| Dokument | Liefert | Verhältnis zu REQ-053 |
|----------|---------|-----------------------|
| **REQ-002** | Site/Location/Slot, LocationTypes, `adjacent_to`, `bed_*`-Felder im Business Case | **Bleibt Quelle der Hierarchie.** REQ-053 ergänzt `geometry` und `soil_profile` auf Location, `geometry` auf Slot, `plan` auf Site und löst die `bed_*`-Felder in das Geometriemodell auf (§20.8). |
| **REQ-013** | PlantingRun, Entry mit `spacing_cm`, `run_at_location`, Batch-Erzeugung mit `assign_to_slots` | **Bleibt Quelle des Durchlaufs.** REQ-053 ergänzt `row_spacing_cm`, `planting_depth_cm`, `layout_strategy` am Entry und ein Layout-Verfahren, das Slots mit Geometrie erzeugt (§11). |
| **REQ-006 / REQ-022 / ADR-008** | Task-Modell, Erinnerungen, Abschluss-Übergang | **Bleiben Quelle der Aufgabe.** REQ-053 ergänzt Kategorien und macht `entity_type = location` zur ersten Klasse; der Abschluss-Übergang schreibt zusätzlich einen `care_event` (§12, §13). |
| **REQ-014 / REQ-004 / REQ-010** | `watering_events`, `feeding_events`, `treatment_applications` | **Bleiben Quelle der Fachdaten.** `care_events` referenziert sie, dupliziert sie nicht (§13.2). |
| **REQ-028 / REQ-001** | Mischkultur-Graph, Fruchtfolge-Validator (slot-basiert) | REQ-053 leitet `adjacent_to` aus Slot-Geometrie ab und liefert die Beet-Ebene für den Validator (§16). |
| **REQ-032** | `LOCATION_OVERVIEW`-Druck, „tabellarisch oder visueller Grundriss" | REQ-053 liefert den visuellen Grundriss (§23). |
| **REQ-018 / REQ-037** | Aktoren inkl. `irrigation_valve`, ET0-Bedarf je Run | REQ-053 führt `irrigation_zones` ein, die Aktoren und Bedarf bündeln (§14). |

---

## 3. Ausgangssituation

### 3.1 Was heute existiert (gemessen am Code, Stand 2026-10-04)

| Bereich | Befund | Quelle |
|---------|--------|--------|
| Hierarchie | `Site` → `Location` (rekursiv, `parent_location_key`, `depth`, `path`) → `Slot`; Edges `contains`, `has_slot`, `placed_in` | `src/backend/app/domain/models/site.py:41-156`, `data_access/arango/collections.py` |
| Site-Maße | `total_area_m2`, `gps_coordinates`, `timezone`, Frostdaten, `water_config` (Wasser**qualität**, keine Infrastruktur) | `site.py:105-156` |
| Location-Maße | `area_m2` (Pflicht), `dimensions: tuple[float,float,float] = (0,0,0)` ohne dokumentierte Semantik/Einheit, `orientation` nur `north/south/east/west`, `irrigation_system` (Enum), `tank_key`, `frost_exposed` | `site.py:65-102`, `common/enums.py:375,458` |
| Slot | `slot_id` (`TENT01_A1`), `position: tuple[int,int]` (Rasterzelle), `capacity_plants` 1–20, `currently_occupied` | `site.py:41-62` |
| LocationTypes | 10 Seeds: `garden`, `greenhouse`, `building`, `room`, `balcony`, `terrace`, `tent`, `bed`, `shelf`, `container`; nutzerdefinierbar | REQ-002 §2, `src/backend/app/migrations/seed_location_types.py` |
| Pflanzdurchlauf | `PlantingRun` (`planned/active/harvesting/completed/cancelled`), `PlantingRunEntry.spacing_cm` (5–300), `assign_to_slots` bei Batch-Erzeugung; **keine** geplante Position | `domain/models/planting_run.py:18-45` |
| Pflanze | `PlantInstance` mit `site_key/location_key/slot_key`, `planted_on`, `removed_on`, `termination_type`, `photo_refs`; kein Statusfeld | `domain/models/plant_instance.py:8` |
| Aufgaben | `Task` mit `entity_type/entity_key`, `category` (16 Werte inkl. `watering`, `pest_control`, `monitoring`, `cleaning`), `recurrence_rule`, `photo_refs`, Audit-Edge; `has_task` erlaubt bereits `locations` als Quelle | `domain/models/task.py:128`, `collections.py` |
| Pflegeprotokoll | **verteilt**: `watering_logs`, `watering_events`, `feeding_events`, `care_confirmations`, `treatment_applications`, Task-Completion — kein gemeinsamer Ort für was/wann/wer/warum/Produkt/Menge/Ergebnis | §3 Backend-Befund |
| Fruchtfolge/Mischkultur | `CropRotationValidator.validate_planting(slot_key, species_key, *, tenant_key)`, `CompanionPlantingEngine` über `adjacent_to`; **kein** API-Endpunkt, der `adjacent_to` setzt | `domain/engines/crop_rotation_validator.py:33`, `graph_repository.py:206` |
| Bewässerung | `irrigation_demands` (ET0, je Site+Run); Aktoren mit `irrigation_valve`/`pump` an Locations; **keine** Zone | `domain/models/irrigation_demand.py`, `actuator.py:114` |
| Boden | REQ-004 nennt `soil_type`, `soil_ph`, `soil_analysis_date`, aber **kein Träger-Entity**; Substrat nur je Slot (`filled_with`) | REQ-004 §1, REQ-019 |
| Druck | WeasyPrint + Jinja2, `PrintEngine.render_pdf`, Endpunkte `/print/*`; kein SVG, kein CSV-Export für Standorte | `domain/engines/print_engine.py:132` |
| Nebenläufigkeit | Kein `version`/ETag auf CRUD-Ressourcen; `_rev`-Prüfung nur an der Tagebuch-Lease (409 `conflict.concurrent_update`) | `plant_diary_repository.py:292`, `common/exceptions.py` |
| Batch-Muster | `BatchResponse{succeeded, failed}` (Teilerfolg) bei Tasks; keine Transaktion | `api/v1/tasks/schemas.py:349` |
| Frontend | React 19, MUI 9, Redux Toolkit (Slices + Thunks, **kein** RTK Query), `react-grid-layout` (Dashboard), `recharts`; **keine** Canvas-/SVG-/Gesten-Lib, **kein** Undo/Redo, **kein** Offline-Cache; Bundle-Budget 400 KB gzip (Ziel 300, Ist 343) | `src/frontend/package.json`, `bundle-budget.json`, `DashboardEditGrid.tsx:31` |
| Standort-UI | Baum (`SimpleTreeView`), Slot-Tabelle; keine 2D-Darstellung | `src/frontend/src/pages/standorte/` |
| Routing | Flache Routen `standorte/sites/:key` …; Tenant-Präfix setzt der `tenantClient` (`/t/{slug}`) | `src/api/client.ts:316` |
| Mobil | Kiosk-Theme mit Touch-Zielen 64/72 px; keine Pinch/Pan-Gesten | `src/kiosk/kioskTheme.ts:14` |

### 3.2 Korrektur der Vorgabe aus dem Auftrag

Der Auftrag nennt als Zielarchitektur „Go Backend, Vue.js, Tailwind". **Das trifft auf Kamerplanter nicht zu.** Verbindlich sind `spec/stack.md` und NFR-001: Python 3.14 / FastAPI / Celery, ArangoDB + TimescaleDB + Valkey, React 19 / TypeScript 6 / MUI 9 / Redux Toolkit, Vite, Kubernetes/Helm. Vue erscheint in `stack.md` nur als verworfene Alternative. Die übrigen Vorgaben (API-first, versionierte DTOs, OpenAPI, Containerisierung, Kubernetes, responsive, englische Quelltexte, Garten-/Boden-orientiertes UI, Pflanzen/Pflanzdurchläufe/Phasen als zentrale Objekte) gelten unverändert und werden hier eingelöst. Wo der Auftrag „Vue-Komponenten" sagt, ist „React-Komponenten" zu lesen.

### 3.3 Was fehlt (Lückenliste)

1. Räumliche Lage und Form von Locations und Slots (Geometrie in Metern).
2. Nicht bepflanzbare Gartenobjekte (Weg, Gebäude, Baum, Wasserquelle …).
3. Plan-Orientierung (Nordwinkel) und Maßstab.
4. Ein Editor samt Zustandsverwaltung (Undo/Redo, Konfliktschutz).
5. Geplante Pflanzpositionen vor dem Anlegen der Pflanzen.
6. Beet-Bodenprofil als Träger für REQ-004-Felder.
7. Einheitliches Pflegeprotokoll auf Beet-Ebene.
8. Bewässerungszonen.
9. Automatische Ableitung von `adjacent_to` aus Positionen.
10. Visueller Grundriss im Druck (REQ-032 §2.5).

---

## 4. Benutzergruppen

| Gruppe | Zielgruppen-Dokument | Bezug zur Gartenplanung |
|--------|---------------------|-------------------------|
| Freiland-/Gemüsegärtner | `spec/target-audiences/ZG-002_Freilandgaertner.md` | Primär. 1–5 Beete, 10–100 m², Winterplanung am Desktop, Gartenarbeit mit Tablet/Smartphone. Beetplanung dort als „kritisch" markiert. |
| Gemeinschaftsgarten (Leitung + Mitglied) | `ZG-004_Gemeinschaftsgarten.md` | Primär. Viele Parzellen, Gießdienst, Lesezugriff für Beobachter, Zuweisung von Beeten an Mitglieder (`location_assignments`, Koordination, keine Schreibgrenze — REQ-049 §3.5). |
| Gewächshaus-Betrieb | `ZG-005`, `UZG-005` | Sekundär. Tische/Beete im Gewächshaus, Zonen, Bewässerung. |
| Marktgärtner | `UZG-002` | Sekundär. Reihenkulturen, Sukzession, Flächenertrag. |
| Bildungseinrichtungen | `UZG-003` | Sekundär. Schulgarten, viele Lesende, wenige Schreibende. |
| Casual-Hobby-Nutzer | `UZG-001` | Tertiär. Balkon/Terrasse mit Kübeln; profitiert vom Plan nur, wenn er in Minuten entsteht (Vorlagen, §10.4). |
| Cannabis-Indoor-Grower | `ZG-001` | Nicht adressiert (Indoor-Raster bleibt tabellarisch, §2.3). |

---

## 5. Personas

Die Personas sind den bestehenden Zielgruppen-Dokumenten entnommen und um den Planungsbezug ergänzt.

**Sabine, 52, Lehrerin (ZG-002).** 60 m² Gemüsegarten hinter dem Haus, fünf Beete, Kompost, samenfeste Sorten. Plant im Januar am Laptop: Welches Beet bekommt dieses Jahr die Starkzehrer? Sie zeichnet die Beete einmal nach Maß (3,0 × 1,2 m), weil sie wissen will, wie viele Tomaten bei 60 cm Abstand hineinpassen. Im Mai steht sie mit dem Handy im Beet, trägt ein, dass Beet 3 gemulcht ist, und korrigiert, dass die Zucchini doch am Rand gelandet ist.

**Tom, 42, Sozialarbeiter (ZG-004, Leitung).** Gemeinschaftsgarten mit 30 Parzellen in einem Hinterhof. Braucht den Gesamtplan, um Parzellen zuzuweisen, den Gießdienst nach Zonen zu organisieren und neuen Mitgliedern zu zeigen, wo ihre Parzelle liegt. Zeichnet Wege, Wasserhähne, Komposthaufen und den Geräteschuppen ein, damit der Plan auch als Orientierung dient. Will den Plan als PDF am Gartentor aushängen.

**Aisha, 28, Studentin (ZG-004, Mitglied).** Erste eigene Parzelle, keine Erfahrung. Öffnet auf dem Smartphone ihre Parzelle, sieht die offenen Aufgaben dieser Woche, hakt „Gießen" ab und fotografiert einen Schädlingsverdacht. Sie bearbeitet die Geometrie nie; sie braucht große Schaltflächen und wenig Auswahl.

**Jonas, 35, Gärtnermeister (UZG-005).** Zwei Folientunnel mit je vier Beetreihen, Tropfbewässerung in sechs Zonen. Pflanzt in Reihen mit festem Reihen- und Pflanzabstand, nutzt Sukzession, will Zonen an Home-Assistant-Ventile koppeln. Für ihn zählt die Reihenlogik, nicht die Freihandpositionierung.

---

## 6. Use Cases

| ID | Use Case | Akteur | Vorbedingung | Hauptablauf (kurz) | Ergebnis | MVP |
|----|----------|--------|--------------|--------------------|----------|-----|
| UC-01 | Garten anlegen und Fläche definieren | Gärtner | Site mit `type ∈ {outdoor, greenhouse, balcony}` existiert oder wird angelegt | Plan öffnen → Gartengrenze als Rechteck oder Polygon zeichnen → Nordrichtung setzen → speichern | `Site.plan` mit `boundary`, `north_angle_deg`, `plan_revision = 1` | ja |
| UC-02 | Beet zeichnen | Gärtner | UC-01 | Werkzeug „Beet" → Rechteck/Kreis/Polygon ziehen → Name, Beettyp → speichern | Location `location_type = bed`, `geometry`, `area_m2` berechnet | ja |
| UC-03 | Beet verschieben/drehen/skalieren | Gärtner | UC-02 | Auswahl → Griff ziehen oder Eigenschaftenpanel-Werte → speichern | Geometrie aktualisiert, Slots folgen (beet-lokal) | ja |
| UC-04 | Gartenobjekt platzieren | Gärtner | UC-01 | Werkzeug (Weg, Baum, Gebäude, Wasserquelle …) → zeichnen → speichern | `garden_objects`-Dokument | ja (Teilmenge, §9.5) |
| UC-05 | Beet bepflanzen (Durchlauf) | Gärtner | UC-02, Spezies vorhanden | Beet wählen → „Bepflanzen" → Spezies/Sorte, Menge, Pflanzabstand, Reihenabstand, Layout → Vorschau → Durchlauf anlegen | `PlantingRun` (`planned`), Entries, Slots mit Geometrie, `run_planned_at`-Edges | ja |
| UC-06 | Geplante Pflanzung ausführen | Gärtner | UC-05 | Durchlauf starten → Pflanzen erzeugen (REQ-013 `create-plants`) | `PlantInstance` je Slot, `placed_in`, Run `active` | ja |
| UC-07 | Pflanzposition korrigieren | Gärtner | UC-06 | Pflanze auf Plan wählen → verschieben (Desktop: Drag; Mobil: Long-Press + Drag oder Koordinaten) | `Slot.geometry` aktualisiert, Audit | ja |
| UC-08 | Pflegeaufgabe am Beet anlegen | Gärtner | UC-02 | Beet → „Aufgabe" → Kategorie, Fälligkeit, Wiederholung | `Task` mit `entity_type = location` | ja |
| UC-09 | Pflegeaufgabe im Garten erledigen | Mitglied | UC-08, Mobilgerät | Feldmodus → Beet antippen → Aufgabe → „Erledigt" → optional Notiz, Produkt, Menge, Foto | Task `completed`, `care_event` geschrieben | ja |
| UC-10 | Pflegehistorie einsehen | Alle Rollen | Ereignisse vorhanden | Beet → Tab „Historie" → Filter Zeitraum/Kategorie | Chronologische Liste aus `care_events` + Pflanzungen | ja |
| UC-11 | Plan drucken | Alle Rollen | UC-01 | „Drucken" → Format, Maßstab → PDF | Maßstäbliches PDF mit Maßstabsleiste, Nordpfeil, Legende | ja |
| UC-12 | Plan sichern/wiederherstellen | Leitung | UC-01 | Export JSON → später Import in dieselbe oder andere Site | Vollständige Wiederherstellung der Geometrien | ja (Export), SHOULD (Import) |
| UC-13 | Bewässerungszone definieren | Gärtner | UC-02, UC-04 (Wasserquelle) | Zone anlegen → Beete zuordnen → Typ, Quelle, optional Aktor | `irrigation_zones`, `Location.irrigation_zone_key` | nein (SHOULD) |
| UC-14 | Bodenprofil pflegen | Gärtner | UC-02 | Beet → „Boden" → Bodenart, pH, Humus, Drainage; Analyse als Ereignis | `Location.soil_profile`, `care_event(category = soil_analysis)` | teilweise (Profil ja, Analyse-Ereignis SHOULD) |
| UC-15 | Fruchtfolge-/Mischkultur-Hinweis beim Bepflanzen | Gärtner | UC-05, Graphdaten | Bei Spezieswahl: Validator läuft über Beet-Slots → Warnung mit Grund | Hinweis im Dialog, kein Blocker | nein (SHOULD) |
| UC-16 | Beet aus Vorlage anlegen | Gärtner | Vorlagen vorhanden | Werkzeug „Vorlage" → Hochbeet 2 × 1 m → platzieren | Location + ggf. Reihen-Slots | nein (SHOULD) |
| UC-17 | Mehrere Objekte gruppieren und gemeinsam verschieben | Gärtner | ≥ 2 Objekte | Mehrfachauswahl → Verschieben | Batch-Update | ja (Mehrfachauswahl), Gruppen-Persistenz WON'T |

---

## 7. Fachliches Domänenmodell

### 7.1 Zuordnung der geforderten Objekte

Die im Auftrag genannten Objekte werden nicht 1:1 als Entitäten eingeführt, sondern auf das bestehende Modell abgebildet. Entscheidend: **drei neue Collections** (`garden_objects`, `care_events`, `irrigation_zones`), alles andere sind additive Felder und Edges.

| Gefordertes Objekt | Abbildung | Begründung |
|--------------------|-----------|------------|
| Garden | **`Site`** (bestehend) mit neuem eingebetteten `plan` (Grenze, Nordwinkel, Revision) | Der Garten ist bereits die Wurzel der Hierarchie; GPS, Klimazone, Frostdaten, Saison-Zustand hängen daran. |
| GardenArea | **`Location`** (bestehend) mit `geometry`; `location_type` z. B. `garden`, `greenhouse`, `terrace`, nutzerdefiniert „Nutzgarten", „Vorgarten" | Rekursive Locations decken Bereiche ab; ein Bereich kann Beete enthalten (`contains`). |
| Bed | **`Location`** (bestehend) mit `location_type = bed` (Bodenbeet) bzw. neuen Seeds `raised_bed`, `planter`, `greenhouse_bed`, `cold_frame`; `geometry`, `soil_profile`, `bed_status` | REQ-002 sieht `bed_type` vor; als LocationType ist es filterbar, ikonisierbar und nutzererweiterbar. |
| PlantingArea | **`Slot`** (bestehend) mit `geometry` (Punkt oder Polygon, beet-lokal) und `slot_role ∈ {position, zone, row}` | Slot ist bereits das Ziel von `placed_in`; `capacity_plants` erlaubt Zonen mit mehreren Pflanzen. |
| Path, Lawn, Greenhouse*, Tree, Shrub, Building, Wall/Fence, WaterSource, IrrigationArea*, CompostArea, StorageArea, OtherGardenObject | **`GardenObject`** (neu, Collection `garden_objects`) mit `object_type`-Enum | Nicht bepflanzbare Objekte brauchen keine Slots, keine Tasks-Kaskade, keine Fruchtfolge. Eine Collection mit Typ-Enum statt zehn Collections. (*Gewächshaus ist, wenn darin gepflanzt wird, eine Location vom Typ `greenhouse`; als reine Kulisse ein GardenObject `greenhouse_shell` — §7.3. *IrrigationArea ist keine Geometrie, sondern eine Zone, §14.) |
| Plant | **`PlantInstance`** (bestehend) | unverändert; Position ergibt sich aus dem Slot |
| PlantingRun | **`PlantingRun`** + **`PlantingRunEntry`** (bestehend) mit zusätzlichen Layout-Feldern | §11 |
| MaintenanceTask | **`Task`** (bestehend) | `entity_type = location` ist über `has_task` bereits zulässig; Kategorien werden ergänzt |
| MaintenanceEvent | **`CareEvent`** (neu, Collection `care_events`) | Einheitliches, revisionssicheres Protokoll; referenziert die Fachereignisse (§13) |
| Tree/Shrub als **Pflanze** | Wenn ein Baum gepflegt werden soll (Obstbaum): `PlantInstance` in einem eigenen Slot einer Location (`location_type = orchard` o. ä.); als Kulisse: `GardenObject(object_type = tree)` | Beides ist zulässig; §7.3 definiert die Regel |

### 7.2 Beziehungen

```
Site ──contains──▶ Location ──contains──▶ Location (Beet) ──has_slot──▶ Slot
 │                                            │                          ▲
 │ has_garden_object                          │ run_at_location          │ placed_in
 ▼                                            ▼                          │
GardenObject                             PlantingRun ──run_contains──▶ PlantInstance
                                              │
                                              └─run_planned_at──▶ Slot   (geplante Belegung)

Location (Beet) ──has_task──▶ Task ──task_logged_as──▶ CareEvent ──care_event_at──▶ Location
PlantInstance  ──has_task──▶ Task                       CareEvent ──care_event_for──▶ PlantInstance (0..n)
                                                        CareEvent ──care_event_source──▶ watering_events | feeding_events | treatment_applications | harvest_batches

IrrigationZone ──zone_covers──▶ Location (Beet)      IrrigationZone ──zone_supplied_by──▶ GardenObject(water_source)
IrrigationZone ──zone_actuated_by──▶ Actuator         Site ──has_irrigation_zone──▶ IrrigationZone
Slot ──adjacent_to──▶ Slot   (ab REQ-053 aus Geometrie abgeleitet, §16.2)
```

Die geforderten Ketten lauten damit:

- **Garden → GardenArea → Bed → PlantingArea → PlantingRun → Plant** = `Site → Location → Location(bed) → Slot ← run_planned_at ← PlantingRun → run_contains → PlantInstance → placed_in → Slot`
- **Bed → MaintenanceTask → MaintenanceEvent** = `Location(bed) → has_task → Task → task_logged_as → CareEvent`

Vorhandene Fremdschlüssel-Felder (`site_key`, `location_key`, `slot_key`, `parent_location_key`) bleiben parallel zu den Edges bestehen (heutiges Doppelmuster, Backend-Befund §2). Neue Beziehungen folgen demselben Muster: Feld für den 1:1-Elternbezug, Edge für Graph-Traversalen.

### 7.3 Regeln für Objektklassen

| Regel | Inhalt |
|-------|--------|
| R-7.1 | Ein Objekt ist eine **Location**, wenn darin gepflanzt, gemessen oder gepflegt wird (Slots, Sensoren, Tasks, Aktoren hängen daran). Sonst ist es ein **GardenObject**. |
| R-7.2 | Ein GardenObject hat keine Slots und keine Pflanzen. Pflegeaufgaben sind nur für `compost`, `water_source` und `storage` zulässig (Kompost umsetzen, Regentonne winterfest machen, Schuppen aufräumen — W-008): `Task.entity_type = garden_object`, Edge `has_task` wird um `garden_objects` erweitert. `water_source` kann Ziel von `zone_supplied_by` sein. |
| R-7.3 | Ein Gewächshaus, in dem Beete liegen, ist eine Location (`greenhouse`), die Beet-Locations enthält. Die Hülle wird aus der Location-Geometrie gezeichnet; ein zusätzliches GardenObject ist nicht nötig. |
| R-7.4 | Ein Baum oder Strauch, der gepflegt und geerntet wird, ist eine PlantInstance in einem Slot einer Location (z. B. `orchard`, `hedge`). Für die reine Darstellung (Nachbars Baum, Zierstrauch ohne Pflege) ist er ein GardenObject (`tree`, `shrub`) mit Kronenradius. |
| R-7.5 | Beete sind Blatt-Locations in der Planungssemantik: Ein Beet enthält keine weiteren Locations. Unterteilungen innerhalb des Beets sind Slots (`slot_role = zone` oder `row`). |
| R-7.6 | Eine Umwandlung GardenObject ↔ Location ist eine fachliche Neuanlage (kein Typwechsel), weil Edges und Tasks sonst verwaisen. Die UI bietet „als Beet neu anlegen" mit Übernahme der Geometrie. |

### 7.4 Zustandsmodell des Beets

**Lebenszyklus** (`Location.bed_status`, nur für Beet-Typen; entschieden W-014):

```
planned ──▶ active ──▶ retired ──▶ active   (Reaktivierung nach Umbau)
   └──────────────────▶ retired             (nie angelegt)
```

| Status | Bedeutung | Auswirkung |
|--------|-----------|------------|
| `planned` | Gezeichnet, noch nicht angelegt | Keine aktiven Pflanzungen erlaubt; geplante Runs ja |
| `active` | In Nutzung | Standard |
| `retired` | Aufgelöst | Keine neuen Runs; Historie bleibt; auf dem Plan ausgeblendet, über Historie-Filter sichtbar; Reaktivierung durch Leitung |

**Saisonzustand** (`season_state`, **abgeleitet**, nie gesetzt) — was auf dem Beet gerade geschieht:

| Zustand | Ableitung |
|---------|-----------|
| `empty` | kein aktiver Run, keine Pflanze mit `removed_on = null` |
| `planted` | mindestens ein aktiver Run mit `plan_role = main_crop` |
| `green_manure` | aktiver Run mit `plan_role = green_manure` (Gründüngung **ist eine Pflanzung**; ihre Familie zählt in der Fruchtfolge, §16) |
| `fallow` | `empty` und das Beet wurde in der laufenden Saison bewusst nicht bepflanzt (`CropRotationPlan`-Eintrag mit `plan_role = fallow` für das Jahr) |
| `winter_covered` | letztes `care_event(category = covering)` ohne nachfolgendes `uncovering` |

Die Fruchtfolge (§16) liest `season_state` je Jahr; „Brache" und „Gründüngung" werden damit korrekt getrennt gezählt (Senf als Gründüngung ist ein Brassicaceae-Wirt und zählt als Kohlfamilie).

Pflanzungen haben keinen eigenen Statusfeld — ihr Zustand leitet sich ab (§11.3).

## 8. Funktionale Anforderungen (Übersicht)

Die funktionalen Anforderungen sind in §9–§16 thematisch gegliedert. Diese Tabelle ist der Index; die Nummern sind dort wiederzufinden.

| Bereich | IDs | MUST | SHOULD | COULD | WON'T |
|---------|-----|------|--------|-------|-------|
| Garteneditor (§9) | GP-FR-001 … GP-FR-034 | 25 | 5 | 3 | 1 |
| Beetverwaltung (§10) | GP-FR-040 … GP-FR-052 | 7 | 4 | 2 | 0 |
| Pflanzplanung (§11) | GP-FR-060 … GP-FR-076 | 11 | 4 | 2 | 0 |
| Beetpflege (§12) | GP-FR-080 … GP-FR-091 | 7 | 3 | 2 | 0 |
| Pflegehistorie (§13) | GP-FR-100 … GP-FR-108 | 5 | 3 | 1 | 0 |
| Bewässerung (§14) | GP-FR-110 … GP-FR-118 | 0 | 6 | 3 | 0 |
| Boden/Nährstoffe (§15) | GP-FR-120 … GP-FR-127 | 2 | 4 | 2 | 0 |
| Fruchtfolge/Mischkultur (§16) | GP-FR-130 … GP-FR-137 | 1 | 5 | 2 | 0 |
| Import/Export (§23) | GP-FR-140 … GP-FR-148 | 4 | 3 | 2 | 0 |
| **Summe** | 119 FR · 50 NFR · 26 UX · 38 API · 35 ACC | **62** | **37** | **19** | **1** |

---

## 9. Grafischer Garteneditor

### 9.1 Grundsatz: Darstellung ≠ Datenmodell

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-001 | MUST | Der Editor arbeitet ausschließlich auf dem fachlichen Plan-Modell (§20): jede Interaktion erzeugt eine **Plan-Operation** (z. B. `move_object`, `set_geometry`, `create_location`), die lokal auf das Modell angewandt, gerendert und über die Batch-API (§21.3) persistiert wird. Die Rendering-Bibliothek hält keinen eigenen Zustand, der nicht aus dem Modell rekonstruierbar ist. | ja |
| GP-FR-002 | MUST | Jede persistierte Geometrie ist in **Metern** definiert (§9.2). Pixelwerte entstehen ausschließlich in der Transformation Modell → Viewport und werden nie gespeichert. | ja |
| GP-FR-003 | MUST | Der Editor rendert aus dem Modell deterministisch: dieselben Daten ergeben bei gleichem Viewport dieselbe Darstellung (Voraussetzung für Snapshot-Tests und PDF-Gleichheit). | ja |

### 9.2 Koordinatensystem, Maße, Raster

**Koordinatenrahmen.** Es gibt zwei Rahmen:

1. **Plan-Rahmen (Site):** Ursprung ist die linke untere Ecke der Gartengrenzen-Bounding-Box beim ersten Speichern; `+x` nach rechts, `+y` nach oben (mathematisch, nicht Bildschirm). Einheit Meter, Dezimalgenauigkeit 3 Nachkommastellen (= Millimeter). Locations und GardenObjects liegen in diesem Rahmen.
2. **Beet-Rahmen (Location):** Ursprung ist der Ankerpunkt (`origin`) der Beet-Geometrie, Achsen folgen der Beet-Rotation. Slots liegen in diesem Rahmen. **Folge:** Wird ein Beet verschoben oder gedreht, bleiben seine Slot-Geometrien unverändert gültig — ein Beet mit 40 Pflanzpositionen zu verschieben ist ein Update eines Dokuments, nicht von 41.

Die Transformation Beet-Rahmen → Plan-Rahmen ist `p_plan = origin + R(rotation_deg) · p_bed`. Der Nordwinkel (§9.3) wirkt nur auf die Darstellung des Kompasses und auf spätere Sonnenberechnungen, nie auf die gespeicherten Koordinaten.

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-004 | MUST | Längen werden in Metern gespeichert (`float`, gerundet auf 0,001 m). Die UI zeigt wahlweise Meter mit zwei Nachkommastellen oder Zentimeter; die Einstellung ist nutzerbezogen (localStorage, wie `module_visibility`) und ändert die gespeicherten Werte nicht. | ja |
| GP-FR-005 | MUST | Eine Geometrie ist eine von drei Formen: `rect` (origin, width_m, length_m, rotation_deg), `circle` (origin = Mittelpunkt, radius_m), `polygon` (points[], rotation_deg = 0, geschlossen, ≥ 3 Punkte, einfach — keine Selbstüberschneidung). Linienobjekte (Zaun, Mauer, Wegachse) nutzen `polyline` (points[], width_m). | ja |
| GP-FR-006 | MUST | `area_m2` wird für `rect`, `circle`, `polygon` serverseitig berechnet (Shoelace für Polygon) und in `Location.area_m2` geschrieben, sobald eine Geometrie vorliegt. Ohne Geometrie bleibt `area_m2` manuell pflegbar (Bestandsverhalten). Die Berechnung ist in einem reinen Modul (`domain/calculators/geometry_calculator.py`) ohne I/O. | ja |
| GP-FR-007 | MUST | Jedes Objekt besitzt eine serverseitig berechnete **Bounding Box** (`bbox: [min_x, min_y, max_x, max_y]` im Plan-Rahmen, nach Rotation), die für Containment-Prüfung, Viewport-Culling und die Mini-Map verwendet wird. | ja |
| GP-FR-008 | MUST | Rotation wird in Grad gespeichert (`rotation_deg`, 0 ≤ r < 360, gegen den Uhrzeigersinn, bezogen auf `+x`). Die UI bietet Drehgriff, Eingabefeld und Schritte 15°/45°/90°. | ja |
| GP-FR-009 | MUST | Zoom: stufenlos per Mausrad/Pinch, feste Stufen (25 %, 50 %, 100 %, 200 %, 400 %) per Schaltfläche/Tastatur, „An Fläche anpassen". Ein Maßstabsbalken (1 m / 5 m / 10 m je nach Zoom) ist immer sichtbar. | ja |
| GP-FR-010 | MUST | Pan: Mittelklick/Space+Drag/Zwei-Finger-Pan; Tastatur: Pfeile scrollen, Shift+Pfeile scrollen um das Zehnfache. | ja |
| GP-FR-011 | MUST | Raster: Standardgrößen **1 cm, 5 cm, 10 cm, 25 cm, 50 cm, 1 m**. Standardwert 10 cm. Das Raster ist ein-/ausschaltbar (Schalter + Taste `G`); die Rasterlinien werden nur gezeichnet, wenn ihr Bildschirmabstand ≥ 8 px ist (sonst nächstgrößere Stufe), das Snap-Raster bleibt unabhängig davon aktiv. | ja |
| GP-FR-012 | MUST | Snap-to-Grid gilt für Verschieben, Zeichnen und Griffe; es ist mit gehaltener `Alt`-Taste bzw. per Schalter temporär abschaltbar. Zusätzlich SHOULD: Snap an Kanten/Ecken benachbarter Objekte (Toleranz 10 px). | ja (Grid), SHOULD (Objekt-Snap) |
| GP-FR-013 | MUST | Der Plan-Rahmen erlaubt Längen bis 1 000 m je Achse (Streuobstwiese, Gemeinschaftsgarten). Darüber lehnt die API ab (§22). | ja |
| GP-FR-014 | MUST | Maßangaben am Objekt: Bei Auswahl und während des Zeichnens/Skalierens werden Breite, Länge (bzw. Radius) und Fläche als Beschriftung am Objekt angezeigt. | ja |

### 9.2a Ein Positionsmodell für Zelt und Beet (O-01)

Die Betreiberentscheidung lautet: **keine Sonderbehandlung** — ein Growzelt und ein Beet werden mit denselben Koordinaten betrieben. Was das konkret bedeutet:

| Aspekt | Vorher (REQ-002) | Ab REQ-053 |
|--------|------------------|------------|
| Positionsangabe eines Slots | `position: (row, col)` als Rasterzelle ohne Einheit; Zelt-Raster implizit | `geometry` im Beet-/Zelt-lokalen Rahmen in Metern — für Zelte, Regale, Beete, Kübel gleich |
| Zelt-Darstellung | Tabelle (`LocationDetailPage`) | dieselbe Beetansicht (§9.6): Zelt = Location mit `rect`-Geometrie (z. B. 1,2 × 1,2 m), Töpfe = Punkt-Slots; Pflanzen-Marker, Tasks, Historie identisch |
| Raster | nur im Zelt gedacht | Snap-Raster ist eine Editor-Einstellung (§9.2) und für alle Locations gleich; wer ein 4 × 4-Topfraster will, nutzt `compute_layout(grid, spacing = Topfdurchmesser)` (§11.2) |
| Nachbarschaft (`adjacent_to`) | manuell, nur programmatisch | aus Geometrie abgeleitet (GP-FR-130) — auch im Zelt, womit die Mischkultur-Engine erstmals indoor Nachbarn kennt |
| Site-Typen | Plan nur outdoor/greenhouse/balcony | Plan für **alle** `SiteType`s; `V-18` entfällt; Indoor-Sites bekommen Grenze = Raumgrundriss oder bleiben ohne `boundary` (dann gilt nur Containment in der Location) |
| Bestandsdaten | — | Migration v0072 leitet für jeden Slot ohne `geometry` einen Punkt aus `position` ab: `origin = (col × pitch, row × pitch)` mit `pitch` = `location.pitch_m` (neu, Standard 0,30 m — ein 11-l-Topf), `geometry_source = migrated_grid`. `Slot.position` wird danach **entfernt** (keine Spiegelung; Sortierungen nutzen `row_index`/`sequence`, die die Migration ebenfalls füllt). |
| Layout-Fähigkeit | nur Beete | `LocationType.supports_layout = true` für `is_bed`-Typen **und** `tent`, `shelf` (W-016.1); Bepflanzen-Dialog, `compute_layout` und Run-Layout hängen daran, nicht an `is_bed` |
| Topfvolumen | nur `planter.volume_liters` am Beet | `Slot.container_volume_l` (optional) — im Zelt begrenzt das Topfvolumen die Pflanze, nicht der Abstand; der Dialog prüft gegen `Species.recommended_container_volume_l`/`min_container_depth_cm` (Schema vorhanden) und warnt (W-016.5) |
| Licht (SHOULD, nicht MVP) | — | `Location.lighting {lamp_height_cm, canopy_distance_cm, fixture_geometry?}` als Vorbereitung für PPFD-Verteilung; Randabstand im Zelt ist frei konfigurierbar, weil `spacing/2` dort keine Lichtbasis hat (W-016.2/3) |
| Etagen | — | **Eine Ebene = eine Location** (Kind von `shelf`/`tent`) mit eigener Lampe, Klima und Photoperiode; 2D-Geometrie bildet keine Stapel ab (W-016.4) |
| Photoperiode (SHOULD) | — | Validierungshinweis `tent.photoperiod_conflict`, wenn Pflanzen verschiedener Photoperiode-Phasen in derselben Zelt-Location stehen (W-016.6) |
| Nachbarschaftsfaktor | Site-weit | `adjacency_factor` pro Location überschreibbar (SCROG-Überlappung, W-016.8) |
| Fruchtfolge | — | Für `tent`, `shelf`, `planter` standardmäßig aus (GP-FR-137) |

Abgenommen wird der Editor weiterhin primär mit Outdoor-Szenarien (§30), aber die E2E-Grundlinie (Issue 23) enthält **ein Zelt-Szenario** (Location `tent`, 9 Punkt-Slots im 3 × 3-Raster, Pflanze verschieben), damit die Gleichbehandlung nachweisbar ist (GP-ACC-036).

### 9.3 Orientierung

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-015 | MUST | `Site.plan.north_angle_deg` (0–359,9) definiert, wohin **geografisch** Norden auf dem Plan zeigt: Kompass-Azimut **im Uhrzeigersinn**, 0 = `+y` ist Norden, 90 = `+x` ist Norden (abweichend von `rotation_deg`, das mathematisch gegen den Uhrzeigersinn läuft — beide Konventionen sind im Code mit benannten Konvertern zu trennen). Standard 0. Die UI beschriftet „geografisch Nord"; ein Handy-Kompass liefert magnetisch Nord (Missweisung Mitteleuropa wenige Grad), der Wert wird daher nie automatisch übernommen. Ein Kompass-Widget im Editor zeigt N/O/S/W und lässt den Winkel durch Drehen oder Eingabe setzen. | ja |
| GP-FR-016 | SHOULD | Ist `Site.gps_coordinates` gesetzt, zeigt das Kompass-Widget zusätzlich die Richtung von Sonnenauf- und -untergang am heutigen Tag (`sun_calculator`, REQ-002). Keine Verschattungsberechnung (§29). | nein |
| GP-FR-017 | SHOULD | `Location.orientation` (4 Werte) und das in REQ-002 vorgesehene `bed_orientation` werden, wenn eine Geometrie vorliegt, aus `rotation_deg` + `north_angle_deg` **abgeleitet** und nur noch angezeigt, nicht mehr manuell gepflegt. Ohne Geometrie bleibt die manuelle Pflege. | nein |
| GP-FR-018 | COULD | Beim Export (GeoJSON, §23) wird aus `gps_coordinates` + `north_angle_deg` eine affine Transformation Plan → WGS84 berechnet. | nein |

### 9.4 Objektmanipulation

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-019 | MUST | Zeichnen: Rechteck (Drag), Kreis (Drag vom Mittelpunkt), Polygon (Klick je Punkt, Doppelklick/Enter schließt, Esc bricht ab), Polylinie (wie Polygon, offen). | ja |
| GP-FR-020 | MUST | Auswahl: Klick; Mehrfachauswahl per Shift+Klick und Rahmen-Auswahl (Drag auf leerer Fläche im Auswahlwerkzeug); `Ctrl/Cmd+A` wählt alle sichtbaren Objekte der aktiven Ebene. | ja |
| GP-FR-021 | MUST | Verschieben per Drag oder Pfeiltasten (1 Rasterschritt; Shift = 10 Schritte); Mehrfachauswahl verschiebt gemeinsam. | ja |
| GP-FR-022 | MUST | Skalieren über 8 Griffe (Rect) bzw. Radiusgriff (Circle); Shift hält das Seitenverhältnis. Polygon-Skalierung über die Bounding-Box-Griffe (SHOULD). | ja (rect/circle), SHOULD (polygon) |
| GP-FR-023 | MUST | Polygon-Punkte: Punkt ziehen, Punkt hinzufügen (Doppelklick auf Kante), Punkt löschen (Entf bei selektiertem Punkt, min. 3 Punkte bleiben). | ja |
| GP-FR-024 | MUST | Löschen (Entf/Backspace, Kontextmenü, Panel). Beete mit aktiven Pflanzen oder offenen Tasks verlangen eine Bestätigung mit Nennung der Anzahl; die API verweigert das Löschen eines Beets mit `removed_on = null`-Pflanzen (409, §22). | ja |
| GP-FR-025 | MUST | Duplizieren (`Ctrl/Cmd+D`): kopiert Geometrie und Stammfelder mit Versatz um einen Rasterschritt; bei Beeten werden Slots mitkopiert, Pflanzen und Tasks nicht. **Mehrfach duplizieren** (SHOULD, F-10): Anzahl, Richtung, Abstand und Namensschema (`Parzelle {n}`) für Gemeinschaftsgärten mit 30 Parzellen. | ja (einfach), SHOULD (mehrfach) |
| GP-FR-026 | MUST | Undo/Redo (`Ctrl/Cmd+Z`, `Ctrl/Cmd+Shift+Z`) als clientseitiger Operationsstapel (mind. 50 Schritte) über alle Plan-Operationen; nach erfolgreichem Speichern bleibt der Stapel erhalten, bei Konflikt (409) wird er geleert und der Nutzer informiert. | ja |
| GP-FR-027 | MUST | Kontextmenü (Rechtsklick / Long-Press 500 ms) mit Bearbeiten, Duplizieren, Löschen, „Bepflanzen" (Beet), „Aufgabe anlegen", „In Vordergrund/Hintergrund" (z-Order). | ja |
| GP-FR-028 | MUST | Eigenschaftenpanel (Desktop: rechte Seitenleiste; Mobil: Bottom Sheet) zeigt für das ausgewählte Objekt Name, Typ, Position (x, y), Maße, Rotation, Fläche und typspezifische Felder; Werte sind direkt editierbar (Tastatur-Alternative zum Drag, UI-NFR-002 R-024). | ja |
| GP-FR-029 | SHOULD | Ausrichten/Verteilen für Mehrfachauswahl (links/rechts/oben/unten/zentriert, gleichmäßig verteilen). | nein |
| GP-FR-030 | WON'T | Persistente Gruppen (Gruppenobjekt mit eigenem Dokument). Begründung: Die Hierarchie Location → Location leistet fachliches Gruppieren bereits; ein rein grafisches Gruppenobjekt erzeugt ein zweites Containment-Modell. Mehrfachauswahl deckt den Bedienfall ab. | — |
| GP-FR-031 | MUST | Ebenen-Sichtbarkeit: Schalter für Raster, Pflanzen, Beschriftungen (MVP) sowie Gartenobjekte, Beete, Zonen, „zuletzt gegossen" (SHOULD). Die Sichtbarkeit ist nutzerbezogen (localStorage). | ja |
| GP-FR-032 | MUST | Sperren eines Objekts gegen versehentliches Verschieben (`locked: true`, persistiert, Schloss-Symbol). Gartengrenze ist nach dem ersten Speichern standardmäßig gesperrt. | ja |
| GP-FR-033 | COULD | Hintergrundbild (Luftbild/Skizze) als georeferenzierte Unterlage mit Maßstab und Deckkraft. Nur Darstellung, nie Datenquelle. | nein |
| GP-FR-034 | COULD | Messwerkzeug (Abstand zwischen zwei Punkten, Fläche eines temporären Polygons). | nein |

### 9.5 Objektklassen und ihre Darstellung

| Objekt | Entität | Geometrieformen | Pflichtfelder | Darstellung | MVP |
|--------|---------|-----------------|---------------|-------------|-----|
| Gartengrenze | `Site.plan.boundary` | rect, polygon | — | gestrichelte Außenlinie, gesperrt | ja |
| Bereich (GardenArea) | Location (`garden`, `terrace`, `balcony`, `greenhouse`, eigene) | rect, polygon | name, location_type | leichte Füllung, Name | ja |
| Beet | Location (`bed`, `raised_bed`, `planter`, `greenhouse_bed`, `cold_frame`) | rect, circle, polygon | name, location_type | typabhängige Füllung (Boden braun, Hochbeet mit Rand), Name, Status-Badge | ja |
| Weg | GardenObject `path` | polyline, polygon | — | grau, Breite | ja |
| Rasen | GardenObject `lawn` | rect, polygon | — | hellgrün | SHOULD |
| Baum | GardenObject `tree` | circle (Kronenradius) | — | Kronenkreis mit Stammpunkt; Props `species_label?`, `height_m?`, `crown_base_height_m?`, `foliage ∈ {deciduous, evergreen}?` (Schattenvorbereitung, §29) | ja |
| Strauch/Hecke | GardenObject `shrub` | circle, polyline (Hecke, width_m) | — | dunkelgrün | SHOULD |
| Gebäude | GardenObject `building` | rect, polygon | — | dunkelgrau, Name; Props `height_m?` (Traufhöhe), `ridge_height_m?` | ja |
| Mauer/Zaun | GardenObject `wall`, `fence` | polyline | — | dicke Linie / Linie mit Pfosten; Props `height_m?`, `opacity ∈ {opaque, semi, open}?` | ja (fence), SHOULD (wall) |
| Rankhilfe/Spalier | GardenObject `trellis` | polyline | — | gestrichelte Linie mit Pfosten; Props `height_m`; wird im Bepflanzen-Dialog angeboten, wenn `Species.support_required` (W-005) | SHOULD |
| Wasserquelle | GardenObject `water_source` | point (circle r = 0,25 m fest) | `water_source_kind ∈ {tap, rain_barrel, well, pond, cistern, hose_reel}` | Tropfen-Icon | ja |
| Kompost | GardenObject `compost` | rect, circle | — | Icon | SHOULD |
| Lager/Schuppen | GardenObject `storage` | rect | — | Icon | SHOULD |
| Sonstiges | GardenObject `other` | alle | `label` | neutral, Label | ja |
| Pflanzposition/Zone/Reihe | Slot | point, polygon, polyline (row) | slot_id | Punkt mit Pflanzen-Icon; Zone als Schraffur; Reihe als Linie mit Punkten | ja |
| Pflanze | PlantInstance (über Slot) | — | — | Icon/Initiale der Spezies, Phasenfarbe (UI-NFR-016), Status-Ring | ja |

Gewächshaus-Darstellung: Eine Location `greenhouse` wird mit Glasrand gezeichnet; darin liegende Beet-Locations werden normal gezeichnet. Ein GardenObject `greenhouse_shell` ist **nicht** vorgesehen (R-7.3).

**Objekte außerhalb der Gartengrenze:** `GardenObject.off_site = true` (Nachbars Haus, Baum am Zaun) nimmt das Objekt von der Containment-Prüfung V-03 aus; es wird als Kulisse gezeichnet (grau, nicht editierbar in der Fläche) und steht für die Schattenberechnung (§29) zur Verfügung.

### 9.6 Ansichten

| Ansicht | Inhalt | Route | MVP |
|---------|--------|-------|-----|
| **Gartenübersicht** | Gesamter Plan mit allen Objektklassen, Legende, Mini-Map (ab Site-Ausdehnung > 4× Viewport), Werkzeugleiste | `standorte/sites/:key/plan` | ja |
| **Beetansicht** | Ein Beet im Beet-Rahmen, Slots/Reihen/Zonen, Pflanzen, Maße; Tabs: Pflanzung · Pflege · Boden · Historie | `standorte/locations/:key/plan` (Tabs über `useTabUrl`) | ja |
| **Pflanzansicht** | Pflanzen eines Beets als Marker mit Phase, Name, Alter; Klick → Pflanzen-Detail (bestehende Seite) | Tab „Pflanzung" der Beetansicht | ja |
| **Pflegeansicht** | Offene/fällige Tasks des Beets und seiner Pflanzen; Erledigen inline | Tab „Pflege" | ja |
| **Historie** | Vergangene Pflanzungen (Zeitstrahl nach Jahr/Saison) und `care_events` | Tab „Historie" | ja |
| **Feldmodus** | Reduzierte Gartenübersicht für Mobilgeräte (§18) | `standorte/sites/:key/plan?mode=field` | ja |

Die Mini-Map ist nur sinnvoll, wenn der Plan größer als der Viewport ist; sie ist daher bedingt (Schwelle oben), nicht permanent.

---

## 10. Beetverwaltung

### 10.1 Beetfelder

| Feld | Quelle | Neu? | Bemerkung |
|------|--------|------|-----------|
| Name, Beschreibung | `Location.name`, `description` (neu) | `description` neu | |
| Geometrie, Fläche | `Location.geometry`, `area_m2` | `geometry` neu | §9.2 |
| Bodenart, Füllmedium, Bodenzustand | `Location.soil_profile.{soil_texture, growing_medium_kind, conditions[]}` | neu | §15 |
| Standort (Lage im Garten) | `geometry.origin`, Elternbereich | — | |
| Sonneneinstrahlung | `Location.sun_exposure ∈ {full_sun, partial_shade, shade, unknown}` | neu | manuell; später aus Berechnung vorbelegbar (§29) |
| Bewässerungszone, -typ | `Location.irrigation_zone_key`, `irrigation_system` (bestehend) | `irrigation_zone_key` neu | §14 |
| Notizen | `Location.notes` | neu | Freitext, Markdown-frei |
| Status | `Location.bed_status` (Lebenszyklus) + abgeleiteter `season_state` | neu | §7.4 |
| Aktive/historische/geplante Pflanzungen | abgeleitet | — | §7.4 |

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-040 | MUST | Ein Beet ist eine Location, deren `location_type` als Beettyp markiert ist (`LocationType.is_bed = true`, neu). Seeds: `bed` (Bodenbeet, bestehend), `raised_bed` (Hochbeet), `planter` (Pflanzkübel/Topf-Gruppe — ersetzt fachlich den Seed `container`, der bestehen bleibt), `greenhouse_bed` (Gewächshausbeet), `cold_frame` (Frühbeet). **Nicht** `is_bed`: `shelf` (Tisch/Regal trägt Kübel, die selbst `planter` sind — O-09), `tent`, `room`, `garden`, `greenhouse`, `building`, `balcony`, `terrace`. Nutzer können weitere Beettypen anlegen (REQ-002). | ja |
| GP-FR-041 | MUST | Beet-Detailseite mit den Tabs aus §9.6; die bestehende `LocationDetailPage` erhält den Tab „Plan" (Beetansicht) und verlinkt zur Gartenübersicht. | ja |
| GP-FR-042 | MUST | Beetliste je Site (bestehende Tabellenlogik, UI-NFR-010) mit Spalten Name, Typ, Fläche, Status, aktive Pflanzen, offene Aufgaben, nächste Fälligkeit; Klick auf eine Zeile hebt das Beet auf dem Plan hervor. | ja |
| GP-FR-043 | SHOULD | Höhe: Für `raised_bed` und `planter` wird `height_m` (0,1–1,5) im Anlegedialog angeboten und aus der Vorlage vorbelegt; **kein Pflichtfeld** (F-06). Für `planter` zusätzlich `volume_liters` (abgeleitet aus Geometrie × Höhe, überschreibbar). Pflanzen mit `min_container_depth_cm` > `height_m × 100` lösen einen Hinweis aus (H-005). | ja |
| GP-FR-044 | SHOULD | **Beetvorlagen** (`bed_templates`, tenant-scoped, plus globale System-Vorlagen): Name, Beettyp, Standardgeometrie (rect 2,0 × 1,0; 1,2 × 2,4 Hochbeet; Kübel Ø 0,4 m …), Höhe, Standard-Reihenlayout (`row_spacing_cm`), Bodenprofil-Vorgabe. „Aus Vorlage platzieren" erzeugt eine Location mit Kopie der Felder. | nein |
| GP-FR-045 | SHOULD | Standardgrößen als Schnellwahl im Zeichendialog (1 × 1, 2 × 1, 3 × 1,2, 4 × 1,2 m; Hochbeet 2 × 1 × 0,8 m; Kübel Ø 0,3/0,4/0,5 m). | nein |
| GP-FR-046 | MUST | Beetstatus-Wechsel nach §7.4 mit Begründungspflicht bei `retired`; der Wechsel schreibt einen `care_event(category = bed_status_change)`. | ja |
| GP-FR-047 | MUST | Beet-Zusammenfassung (Kopf der Beetansicht): Fläche, Typ, Status, Bodenart, Sonneneinstrahlung, aktive Pflanzen (Anzahl, Spezies), offene Aufgaben, letzte Pflege, nächste Fälligkeit. | ja |
| GP-FR-048 | MUST | Pflanzkübel sind beweglich (REQ-002 „mobile Positionierung"): Ein `planter` darf auch dann verschoben werden, wenn Pflanzen darin stehen — ohne Bestätigung, weil die Pflanzen mitwandern (beet-lokaler Rahmen). Für Bodenbeete mit Pflanzen fragt die UI nach (Plan-Korrektur vs. physische Verlegung). | ja |
| GP-FR-049 | COULD | Beet archivieren mit Ausblendung aus Listen (`retired` + Filter „Archivierte anzeigen"). | nein |
| GP-FR-050 | MUST | Beete einem Mitglied zuweisen (bestehendes `location_assignments`, REQ-024/REQ-049 §3.5): Zuweisung ist im Panel sichtbar und als Filter „Meine Beete" nutzbar; sie ist **keine** Schreibgrenze. | ja |
| GP-FR-051 | SHOULD | Fotos am Beet (`Location.photo_refs`, `cover_photo_ref`, Attachment-Kategorie `location`) über das Galerie-Muster aus REQ-034; Erfassung über REQ-052 Profil `gallery`. | nein |
| GP-FR-052 | COULD | Beet-QR-Etikett (bestehender `plant_label`-Pfad, Vorlage `location_label`) mit Deep-Link in den Feldmodus. | nein |
| GP-FR-053 | MUST | Beet umbenennen ändert nur `name`; `slot_id` und alle Keys bleiben unverändert (Historie hängt per `placed_in` an Slots, F-07). | ja |
| GP-FR-054 | COULD | Beet teilen / zusammenlegen (`POST /locations/{key}/split`, `POST /locations/merge`): Slots werden anhand ihrer Geometrie dem neuen Beet zugeordnet, Historie folgt dem Slot; Tasks am Beet werden dem Nutzer zur Zuordnung vorgelegt. | nein |
| GP-FR-055 | MUST | **Beet räumen / Saisonende** (F-02): Aktion „Beet räumen" beendet alle aktiven Runs des Beets in einem Schritt (je Pflanze `removed_on`, `termination_type` wählbar: `harvested`, `senesced`, `died`, `cancelled`), schreibt einen `care_event(category = clearing)` und gibt die Slots frei. Slots abgeschlossener Runs bleiben als Historie erhalten (`archived_at` gesetzt) und blockieren weder V-06 noch V-08 (nur aktive und geplante Slots zählen). Der nächste Run im Beet darf dieselben Positionen neu belegen oder neue erzeugen. | ja |

---

## 11. Pflanzplanung innerhalb eines Beetes

### 11.1 Ablauf

1. Beet wählen → „Bepflanzen". Der Dialog zeigt **Fruchtfolge-Hinweis** (letzte Familie im Beet, Jahre seit demselben Anbau, Anbaupause der gewählten Familie) und **Mischkultur-Hinweis** zu bereits geplanten/aktiven Nachbarn (GP-FR-131/132, MVP).
2. Spezies/Sorte wählen (bestehende Stammdaten, Favoriten zuerst); Anzahl **oder** „so viele wie passen". Angezeigt werden Endhöhe/-breite und ob eine Rankhilfe nötig ist (`mature_height_cm`, `mature_width_cm`, `support_required` aus dem Steckbrief, W-001/W-005).
3. Layout wählen: `grid` (quadratisch, `row_spacing = spacing`), `rows` (Reihen mit eigenem Reihenabstand), `triangular` (versetzt; `row_spacing` ist **abgeleitet** = spacing × 0,866, nicht editierbar; der Dialog zeigt die berechnete Mehrzahl statt „~15 %"), `zone` (eine Fläche mit Kapazität, Standard für Direktsaat), `free` (manuell gesetzte Positionen; Standard für Gehölze).
4. Abstände: Pflanzabstand `spacing_cm`, Reihenabstand `row_spacing_cm` (nur `rows`), Reihenrichtung `row_direction ∈ {along_length, along_width}`, Randabstand längs/quer (`edge_margin_along_cm` = spacing/2, `edge_margin_across_cm` = row_spacing/2 als Standard), Tiefe mit `depth_kind ∈ {sowing, planting}`; bei Direktsaat zusätzlich `sowing_spacing_cm` und `thinning_to_cm`. Vorbelegung: Steckbrief (`Species.spacing_cm`, `row_spacing_cm`), sonst „zuletzt verwendet" für diese Spezies im Tenant (F-11), sonst leer mit Hinweis.
5. Vorschau auf dem Beet; Pflanzen verschieben/entfernen; bei mehreren Entries: Zonen oder **alternierende Reihen** zuweisen (Möhre/Zwiebel — GP-FR-070 Reihenzuweisung ist MVP, Zonen-Mischkultur SHOULD).
6. Durchlauf anlegen (`PlantingRun.status = planned`, `plan_role = main_crop | green_manure`) → Slots mit Geometrie werden erzeugt, `run_planned_at`-Edges mit **Zeitfenster** gesetzt (GP-FR-065).
7. Später: Durchlauf starten → Pflanzen erzeugen (REQ-013 `create-plants`, `assign_to_slots` nutzt die geplanten Slots). Direktsaat in `zone`/`row`-Slots erzeugt **keine** Pflanze je Samen, sondern den Zustand `sown`; Pflanzen entstehen nach dem Vereinzeln (`thinning`) oder bleiben als Zonen-Bestand (§11.3).

### 11.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-060 | MUST | `PlantingRunEntry` erhält `row_spacing_cm` (5–1 000), `row_direction ∈ {along_length, along_width}`, `edge_margin_along_cm`/`edge_margin_across_cm` (0–200, Standard spacing/2 bzw. row_spacing/2), `depth_cm` (0–100) mit `depth_kind ∈ {sowing, planting}`, `sowing_spacing_cm`/`thinning_to_cm` (optional, Direktsaat), `layout_strategy ∈ {grid, rows, triangular, zone, free}`, `placement_hint`; `spacing_cm` bleibt, Obergrenze wird auf **1 000 cm** angehoben (Gehölze, Streuobst — W-004). Semantik: `grid` setzt `row_spacing = spacing`; `triangular` leitet `row_spacing = spacing × 0,866` ab (W-002). | ja |
| GP-FR-061 | MUST | Vorbelegung aus dem Steckbrief nutzt die **vorhandenen** Schemafelder `Species.spacing_cm` (Range-String, numerisch geparst: unterer Wert), `mature_height_cm`, `mature_width_cm`, `support_required`, `sowing_depth_cm`, `recommended_container_volume_l`, `min_container_depth_cm` (`species.schema.yaml:150–174, 347`); **neu** nur `row_spacing_cm` (O-11, W-001 — kein `spacing_cm_default`-Duplikat). Die Steckbrief-Vorlage erhält den Abschnitt „Pflanzabstand und Reihenabstand", `plant-info-to-seed-yaml` extrahiert ihn, `seed-data-validator` prüft 5–1 000 cm. Fehlt der Wert, gilt „zuletzt verwendet" (F-11), sonst leer mit Hinweis — kein stiller Default. `compute_layout` warnt, wenn `spacing_cm < mature_width_cm × 0,7`. | ja |
| GP-FR-062 | MUST | **Layout-Berechnung** ist eine reine Funktion `compute_layout(bed_geometry, entry_layout, max_count?) → LayoutResult{slots, count, capacity_max, warnings}` in `domain/calculators/planting_layout_calculator.py`; sie liefert Punkte im Beet-Rahmen, die vollständig innerhalb der Beetgeometrie **minus Randabstand als Inset** liegen (Distanz zur Polygonkante, nicht nur Point-in-Polygon — W-002). **Obergrenze (SR-004):** Vorab-Schätzung `Fläche ÷ (spacing × row_spacing)`; ergibt sie > 2 000 Positionen, bricht die Funktion mit 422 `layout.too_many_positions {estimated}` ab, bevor sie Punkte erzeugt. | ja |
| GP-FR-063 | MUST | Die Berechnung ist über `POST …/locations/{key}/planting-layout/preview` abrufbar (ohne Persistenz) und wird vom Dialog für die Live-Vorschau genutzt; derselbe Algorithmus läuft im Frontend (TypeScript-Port mit identischen Testvektoren, §19.6) für verzögerungsfreie Vorschau — die Server-Antwort ist bei Abweichung maßgeblich. | ja |
| GP-FR-064 | MUST | Das Ergebnis der Planung wird als **Slots** persistiert: `slot_role = position` (ein Punkt, `capacity_plants = 1`), `row` (Polylinie mit `capacity_plants = n`), `zone` (Polygon mit `capacity_plants = n`). Die `slot_id` folgt dem bestehenden Format `LOCATION_NNN` (z. B. `BEET03_R2P05`). | ja |
| GP-FR-065 | MUST | **Geplante Pflanzung mit Zeitfenster** (F-01): Edge `run_planned_at` (planting_runs → slots) mit `entry_key`, `planned_species_key`, `sequence`, `planned_from` (= `run.planned_start_date`), `planned_until` (= geplantes Ende aus Kulturdauer des Steckbriefs oder manuell; `null` = offen). Ein Slot darf für mehrere Runs reserviert sein, solange sich die Zeitfenster **nicht überlappen** (Nachkultur: Feldsalat nach Tomate im selben Slot). Konflikt → 409 `slot.already_planned {conflicting_run_key, overlap_from, overlap_until}`. Aktive Pflanzen (`placed_in`, `removed_on = null`) blockieren jede Reservierung, deren `planned_from` vor dem erwarteten Ende des aktuellen Runs liegt (Hinweis, Reservierung mit `planned_from` danach ist erlaubt). | ja |
| GP-FR-066 | MUST | **Tatsächliche Pflanzung:** `create-plants` (REQ-013) nutzt bei `assign_to_slots = true` die `run_planned_at`-Slots in `sequence`-Reihenfolge; überzählige geplante Slots bleiben reserviert, bis der Run `completed`/`cancelled` wird oder der Nutzer sie freigibt. | ja |
| GP-FR-067 | MUST | Pflanzen auf dem Plan: Jede `PlantInstance` mit `placed_in` wird am Slot-Zentrum gezeichnet; bei `slot_role = zone` werden Pflanzen gleichmäßig in der Zone verteilt (nur Darstellung, keine persistierte Einzelposition). | ja |
| GP-FR-068 | MUST | **Einzelne Pflanze verschieben** = Slot-Geometrie ändern (`slot_role = position`), weil Slot und Pflanze 1:1 sind. Die UI nennt das „Position korrigieren"; die Änderung wird als `care_event(category = position_corrected)` protokolliert. Pflanzen in Zonen haben keine Einzelposition und sind nicht verschiebbar (Hinweis in der UI). | ja |
| GP-FR-069 | MUST | Verschieben in ein **anderes Beet** ist kein Drag, sondern die bestehende Umsetzen-Logik (Task `transplant`, REQ-006) — der Plan bietet dafür „Umpflanzen nach …" im Kontextmenü. | ja |
| GP-FR-070 | MUST | **Mischkultur im Beet:** Mehrere Entries verschiedener Spezies werden auf **alternierende Reihen** verteilt (`row_assignment: entry_key je Reihe`, MVP — F-11) oder auf disjunkte Zonen (`slot_role = zone`, SHOULD); der Dialog zeigt die Kompatibilität der gewählten Spezies (REQ-028 `check_compatibility`). | ja (Reihen), SHOULD (Zonen) |
| GP-FR-071 | COULD | **Begleit-/Randbepflanzung:** Ein Entry kann `placement_hint ∈ {interior, edge, corner}` tragen; `edge` erzeugt Positionen entlang der Beetkante mit `spacing_cm`. | nein |
| GP-FR-072 | MUST | **Freie Positionen** (`layout_strategy = free`): Der Nutzer setzt Punkte per Klick/Tipp; Mindestabstand = `spacing_cm` wird als Hinweis (gelber Ring), nicht als Blocker durchgesetzt. | ja |
| GP-FR-073 | MUST | Pflanzenanzahl: Bei „so viele wie passen" liefert `compute_layout` die Maximalzahl (gedeckelt durch GP-FR-062); der Nutzer kann sie reduzieren. Die Kapazitätsanzeige nimmt die **Anzahl aus `compute_layout`**, nicht aus der Fläche (Randeffekte kleiner Beete). `slot_capacity_calculator.calculate_plants_per_m2` wird auf `(spacing_cm, row_spacing_cm=None, strategy)` erweitert — heute rechnet sie 1/spacing² und ignoriert den Reihenabstand (Tomate 60 × 80: 2,08/m² statt 2,78; W-003, nachgemessen `slot_capacity_calculator.py:32`). Für `triangular` gilt 1/(spacing² × 0,866). | ja |
| GP-FR-074 | SHOULD | Sukzessionspläne (REQ-013 `succession_plans`) reservieren Slots je Charge; der Plan zeigt reservierte, noch leere Positionen gestrichelt mit Datum. | nein |
| GP-FR-075 | COULD | Pflanzen einer Zone nachträglich in Einzelpositionen „auflösen" (Zone → n Positionen). | nein |
| GP-FR-076 | COULD | Reihen als bearbeitbare Linie: Reihe verschieben verschiebt alle Positionen der Reihe. | nein |
| GP-FR-077 | MUST | **Vorjahr am Beet** (F-08): Die Info-Blase (GP-UX-006) und der Beetkopf zeigen „Vorjahr: {Familie/Spezies}" aus GP-API-039; ein Jahr-Umschalter in der Planansicht (`?year=`) färbt Beete nach der Familie des gewählten Jahres. | ja |
| GP-FR-078 | COULD | „Saison kopieren": Runs eines Jahres als geplante Runs des Folgejahres duplizieren (ohne Pflanzen), mit Fruchtfolge-Warnungen je Beet. | nein |

### 11.3 Zustände einer Pflanzung (verbindliche Begriffe)

| Begriff | Definition | Darstellung |
|---------|------------|-------------|
| **geplant** | `run_planned_at`-Edge mit Zeitfenster existiert, keine `PlantInstance` im Slot | gestricheltes Icon, Spezies-Initiale, `planned_from` |
| **gesät** (W-015) | `zone`/`row`-Slot mit `sown_at` gesetzt, noch keine Pflanzen (Direktsaat, vor dem Auflaufen/Vereinzeln) | Saatreihen-Muster, Datum |
| **tatsächlich** | `PlantInstance` mit `placed_in`, `removed_on = null` | volles Icon, Phasenfarbe |
| **in Ernte** (W-015) | Pflanze steht, mindestens ein `harvest_batch` referenziert sie (`harvest_type = partial/continuous`) | Icon mit Erntesymbol |
| **geerntet** | `termination_type = harvested`, `removed_on` gesetzt | nur in Historie |
| **ausgefallen** (W-015) | `termination_type ∈ {died, senesced}` mit `termination_cause`; Slot ist frei für Nachpflanzung | Historie; Nachpflanz-Vorschlag am Slot |
| **historisch** | `removed_on != null` (jede Ursache) | Historie/Zeitstrahl |

## 12. Beetpflege

### 12.1 Aufgabenkatalog

Die geforderten Pflegearten werden auf `TaskCategory` abgebildet. Bestehende Werte bleiben; neue sind markiert. Die Zuordnung Kategorie → Fachereignis legt fest, welche Fachdaten bei Erledigung abgefragt werden (§12.3).

| Pflegeart | `TaskCategory` | Neu? | Fachereignis bei Erledigung |
|-----------|----------------|------|-----------------------------|
| Gießen | `watering` | nein (Code) | `watering_events` (Menge, Quelle) |
| Düngen | `feeding` | nein | `feeding_events` (Produkt, Menge; Flächendosierung g/m² oder L/m² nach REQ-004) |
| Mulchen | `mulching` | **neu** | `care_event` (Material, Menge, Schichtdicke) |
| Unkraut entfernen | `weeding` | **neu** | `care_event` |
| Boden lockern | `soil_loosening` | **neu** | `care_event` |
| Aussaat | `sowing` | **neu** | `care_event` + optional Run-Start |
| Pikieren | `pricking_out` | **neu** | `care_event` |
| Umpflanzen | `transplant` | nein | bestehende Umsetzen-Logik + `care_event` |
| Anbinden | `training` | nein | `care_event` |
| Ausgeizen | `ausgeizen` | nein (Enum-Wert bleibt — Umbenennung wäre ein Enum-Retirement; Anzeigename „Ausgeizen/Seitentriebe entfernen") | `care_event` |
| Rückschnitt | `pruning` | nein | `care_event` |
| Schädlingskontrolle | `pest_control` / `ipm` | nein | `treatment_applications` (REQ-010) bei Behandlung, sonst `care_event(observation)` |
| Krankheitskontrolle | `monitoring` | nein | `care_event(observation)` |
| Ernte | `harvest` | nein | `harvest_batches` (REQ-007) |
| Bodenverbesserung | `soil_amendment` | **neu** | `care_event` (Material, Menge); Materialien mit Nährstoffwirkung (`compost`, `manure`, `horn_shavings`) schreiben **zusätzlich** ein `feeding_event` mit Flächendosierung, damit die Düngebilanz (GP-FR-125) sie sieht (W-007) |
| Kompost hinzufügen | `soil_amendment` mit `material = compost` | — | `care_event` |
| Kalkung | `liming` | **neu** | `care_event` (Produkt, g/m², Kalkart `calcium_carbonate \| dolomite \| quicklime`); gilt für Bodenbeete — `ph_adjustment` ist Gießwasser/Nährlösung (Kübel, Hydro, Zelt); pH-Absenkung im Boden = `soil_amendment` mit `sulfur` (W-007) |
| pH-Anpassung | `ph_adjustment` | **neu** | `care_event` (Produkt, Zielwert, Messwert) |
| EC-/Nährstoffkontrolle | `ec_check` | **neu** | `care_event(measurement)` |
| Spülen/Flush | `flush` | **neu** | `watering_events` mit `is_flush = true` (neu); nur für Locations mit `growing_medium_kind ≠ native_soil` angeboten (W-007) |
| Vereinzeln/Ausdünnen | `thinning` | **neu** | `care_event` (+ erzeugt Pflanzen aus `sown`-Zonen, §11.3) |
| Anhäufeln | `hilling` | **neu** | `care_event` |
| Umbrechen/Einarbeiten | `tillage` | **neu** | `care_event` (Gründüngung einarbeiten beendet den `green_manure`-Run) |
| Gründüngung einsäen | `sowing` mit Run `plan_role = green_manure` | — | Run + `care_event` |
| Abdecken / Abdeckung entfernen | `covering` / `uncovering` | **neu** | `care_event` (Material: `fleece`, `net`, `foil`, `frost_cover`); bestimmt `season_state = winter_covered` |
| Lüften (Gewächshaus/Frühbeet) | `ventilating` | **neu** | `care_event` |
| Beet räumen | `clearing` | **neu** | `care_event` (GP-FR-055) |
| Bodenanalyse | `soil_analysis` | **neu** | `care_event(measurements)` (§15) |
| Niederschlag erfassen | `rainfall` | **neu** | `care_event(quantity, unit = l_per_m2)` — Eingang der Wasserbilanz (GP-FR-113) |
| Handbestäubung | `pollinating` | **neu** | `care_event` |
| Fruchtausdünnen/Entlauben | `pruning` mit `pruning_kind ∈ {fruit_thinning, defoliation, shaping}` | — | `care_event` |

Die bestehenden Kategorien `care_reminder`, `seasonal`, `phenological`, `observation`, `maintenance`, `cleaning` bleiben erhalten.

**Kontextabhängige Anzeige:** Der Erledigen-/Protokoll-Dialog bietet nur Kategorien an, die zum Beet passen: `flush`, `ec_check`, `ph_adjustment` nur für `growing_medium_kind ≠ native_soil`; `ventilating` nur in `greenhouse`/`cold_frame`/`tent`; `hilling`, `tillage`, `liming` nur für Bodenbeete (F-03).

### 12.2 Aufgabenarten

| Art | Abbildung | Quelle |
|-----|-----------|--------|
| einmalig | `Task` ohne `recurrence_rule` | REQ-006 |
| wiederkehrend | `Task.recurrence_rule` — kanonisch **RRULE** (RFC 5545, ADR-008 Grenze 1). **Entschieden (O-05):** ADR-008 wird in Welle 0 auf *Accepted* gehoben; Migration `v0076_recurrence_cron_to_rrule` konvertiert bestehende Cron-Regeln (`0 8 * * 1` → `FREQ=WEEKLY;BYDAY=MO;BYHOUR=8`) und verweigert den Start bei nicht konvertierbaren Ausdrücken (Liste im Report); REQ-006 wird auf RRULE umgestellt. Die API nimmt ab dann nur RRULE an. | ADR-008 |
| geplant | `Task.status = pending` mit `due_date` in der Zukunft | REQ-006 |
| automatisch vorgeschlagen | `Task.origin = system`, `source` nennt den Erzeuger (`care_reminder_engine`, `irrigation_demand`, `season_engine`); vorgeschlagene Tasks sind `pending` mit Kennzeichen `suggested = true` (neu) und können angenommen (→ `suggested = false`) oder verworfen (`skipped`) werden | REQ-022, REQ-037, REQ-047 |
| tatsächlich ausgeführt | `care_event` (§13) | neu |

### 12.3 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-080 | MUST | Tasks können an ein Beet (`entity_type = location`) gebunden werden; die bestehende `has_task`-Edge (`locations → tasks`) wird dafür genutzt. Die Task-Liste (`/tasks/queue`) erhält den Filter `location_key` (inkl. untergeordneter Locations). `entity_type = garden_object` ist für `compost`, `water_source`, `storage` zulässig (R-7.2). | ja |
| GP-FR-081 | MUST | Beim Anlegen einer Beet-Aufgabe kann der Nutzer wählen: „für das Beet" (eine Task) oder „für jede Pflanze im Beet" (n Tasks mit `task_cloned_from`, bestehende Clone-Logik). | ja |
| GP-FR-082 | MUST | `TaskCategory` wird um die in §12.1 markierten Werte erweitert; die Migration ist additiv (Enum-Erweiterung, keine Umbenennung — Memory „Enum-Retirement → Startup-Crash" beachten). | ja |
| GP-FR-083 | MUST | **Erledigen** läuft ausschließlich über den einen Abschluss-Übergang (ADR-008 Grenze 4: `POST /tasks/{key}/complete`). Der Übergang schreibt nach erfolgreichem Status-Wechsel **atomar** einen `care_event` mit `task_key`, Kategorie, `performed_by`, `performed_at`, Notiz, Fotos und — je nach Kategorie — dem Fachereignis-Bezug (§12.1). Atomar = ArangoDB-Stream-Transaktion über `tasks`, `care_events`, Fachcollection, Edges. | ja |
| GP-FR-084 | MUST | Der Erledigen-Dialog fragt je Kategorie nur die relevanten Felder (Gießen: Liter/Quelle; Düngen: Produkt/Menge/Einheit; Mulchen: Material/Dicke; sonst: Notiz). Alle Felder außer dem Zeitpunkt sind optional — ein Tipp auf „Erledigt" ohne Eingaben ist zulässig (Feldmodus). | ja |
| GP-FR-085 | MUST | Rückdatieren: `performed_at` darf in der Vergangenheit liegen (max. 365 Tage), nie in der Zukunft (§22). | ja |
| GP-FR-086 | SHOULD | Vorgeschlagene Aufgaben (`suggested = true`) erscheinen im Beet-Pflege-Tab in einem eigenen Abschnitt „Vorschläge" mit Grund (`source`, z. B. „ET0-Bedarf 4,2 L/m² seit 3 Tagen") und zwei Schaltflächen: Annehmen, Verwerfen. | nein |
| GP-FR-087 | SHOULD | Wiederkehrende Beet-Aufgaben aus Vorlage: Beettyp-Vorlagen (GP-FR-044) können einen Satz wiederkehrender Tasks mitbringen (z. B. Hochbeet: jährlich „Erde nachfüllen" im März). | nein |
| GP-FR-088 | MUST | Mehrere Aufgaben desselben Typs auf mehreren Beeten in einem Schritt erledigen (Gießdienst: „alle Beete der Zone gegossen") — nutzt `POST /tasks/batch/status` erweitert um die Fachfelder; erzeugt je Task einen `care_event`. | ja |
| GP-FR-089 | MUST | Aufgaben auf dem Plan als Badge am Beet (Anzahl offen/überfällig) mit Farbcodierung nach Priorität; Klick öffnet den Pflege-Tab. | ja |
| GP-FR-090 | MUST | Pflegeaufgaben ohne Task direkt protokollieren („Ich habe gerade gemulcht"): `POST /care-events` ohne `task_key` (§13). Im Feldmodus als **Schnellprotokoll** mit sechs Chips: Gegossen · Geerntet · Gesät · Gejätet/Gemulcht · Gepflanzt · Notiz (F-03, GP-UX-029). | ja |
| GP-FR-091 | COULD | Aufgaben-Checklisten je Beettyp als Saisonvorlage (Frühjahr/Sommer/Herbst/Winter). | nein |

---

## 13. Pflegehistorie

### 13.1 Zweck

Heute verteilt sich „was wurde gemacht" auf `watering_events`, `feeding_events`, `care_confirmations`, `treatment_applications`, `harvest_batches` und Task-Completion-Felder. Es gibt keinen Ort, an dem **warum**, **Ergebnis** und **betroffene Pflanzen** über alle Pflegearten hinweg stehen, und keine Lesesicht pro Beet. `care_events` ist dieser Ort.

### 13.2 Entscheidung: eigene Collection, nicht nur Projektion

| Option | Vorteil | Nachteil |
|--------|---------|----------|
| A: AQL-Union über die Fachcollections (reine Lesesicht) | keine neue Collection | `why`, `observed_outcome`, Beet-Bezug und Pflegearten ohne Fachcollection (Mulchen, Jäten …) haben keinen Platz; Revision nicht möglich |
| **B: `care_events` als Protokoll mit Referenz auf die Fachcollection** (gewählt) | ein Ort für alle Pflegearten; Revision; Beet-Bezug; Auswertbarkeit | zweite Schreibstelle — gelöst durch die Atomarität im Abschluss-Übergang (GP-FR-083) und einen Konsistenz-Job (GP-FR-105) |
| C: Fachcollections abschaffen und alles in `care_events` | ein Modell | Bruch mit REQ-004/014/010 und laufendem Code; nicht gerechtfertigt |

Die Fachcollections bleiben **Quelle der Fachdaten** (Liter, ml/L, Wirkstoff). `care_events` hält das **Protokoll** (Kontext, Verantwortung, Ergebnis) und zeigt auf die Fachdaten.

### 13.3 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-100 | MUST | Jeder `care_event` beantwortet: **was** (`category`, `summary`), **wann** (`performed_at`), **wer** (`performed_by_user_key` aus dem Token; für ein anderes Mitglied `performed_for_user_key` per Auswahl; für Dritte `performed_by_label` ≤ 80 Zeichen mit UI-Hinweis „keine vollständigen Namen" — SR-006), **wo** (`location_key`, `site_key`), **warum** (`reason` Freitext + `trigger ∈ {task, reminder, suggestion, manual, observation}`), **Produkt** (`product_ref` → `fertilizers`/Freitext `product_label`), **Menge** (`quantity`, `unit ∈ {l, ml, g, kg, l_per_m2, g_per_m2, cm, pieces}`), **betroffene Pflanzen** (`plant_keys[]`, leer = ganzes Beet), **Ergebnis** (`observed_outcome` Freitext, `outcome_rating ∈ {positive, neutral, negative, unknown}`), **Belege** (`photo_refs[]`). | ja |
| GP-FR-101 | MUST | **Revisionssicherheit:** `care_events` sind append-only. Eine Korrektur erzeugt einen neuen Eintrag mit `supersedes_key` auf den alten; der alte erhält `superseded_by_key` und bleibt lesbar (Filter „Korrekturen anzeigen"). Beim Supersede wird `performed_by_user_key` vom Vorgänger übernommen, der Korrigierende steht in `created_by`; ein korrigiertes `performed_at` unterliegt V-11 (SR-009). Storno nur als `voided_at`, `voided_by`, `void_reason`. Physisch löscht nur die DSGVO-Kaskade (REQ-025). In der UI heißt Supersede „Bearbeiten"; `position_corrected`-Einträge sind in der Historie standardmäßig ausgeblendet (F-13). | ja |
| GP-FR-102 | MUST | Historie-Tab des Beets: chronologische Liste (neueste zuerst) aus `care_events` **und** Pflanzungsereignissen (Run gestartet/abgeschlossen, Pflanze gesetzt/entfernt, abgeleitet aus `plant_instances`/`planting_runs`), Filter nach Kategorie, Zeitraum, Pflanze, Person; Paginierung ab 50 Einträgen (UI-NFR-003 R-018). | ja |
| GP-FR-103 | MUST | Pflanzungs-Zeitstrahl: Je Jahr/Saison, welche Spezies (Familie farbcodiert) im Beet standen — Grundlage für den Fruchtfolge-Blick (§16). Rückblick mindestens 5 Jahre (REQ-002: 3–5). | ja |
| GP-FR-104 | SHOULD | Export der Historie eines Beets als CSV (`GET …/locations/{key}/care-events?format=csv`) mit den Feldern aus GP-FR-100 in flacher Form; **CSV-Härtung (SR-016):** Zellen, die mit `=`, `+`, `-`, `@`, Tab oder CR beginnen, werden mit `'` präfixiert; UTF-8 mit BOM, RFC-4180-Quoting; `performed_by` als Anzeigename; ≤ 50 000 Zeilen. | nein |
| GP-FR-105 | SHOULD | Konsistenz-Job (Celery, täglich): findet Fachereignisse (`watering_events`, `feeding_events`, `treatment_applications`, `harvest_batches`) ohne `care_event`-Referenz und erzeugt nachträglich Protokolleinträge mit `trigger = backfill`; Rückwärts-Migration beim Einführen (§34). | nein |
| GP-FR-106 | SHOULD | `care_confirmations` (REQ-022) erzeugen ebenfalls einen `care_event` (`trigger = reminder`), damit Zimmerpflanzen- und Beetpflege in derselben Historie erscheinen. | nein |
| GP-FR-107 | MUST | Die Historie ist mandantenweit filterbar unter `GET /care-events` (alle Beete), mit denselben Filtern; Standard-Zeitraum 90 Tage. | ja |
| GP-FR-108 | COULD | Auswertungen: Gießmenge je Beet und Monat, Düngegaben je m² und Saison, Zeit zwischen Pflanzung und erster Ernte — als Tabellen im Historie-Tab; Grafiken (recharts) nach dataviz-Regeln. | nein |
| GP-FR-109 | MUST | **Redaktion (SR-006, Art. 16/17):** Die Leitung und die DSGVO-Kaskade können die Freitextfelder (`summary`, `reason`, `observed_outcome`, `product_label`, `performed_by_label`) und `photo_refs` eines `care_event` **und aller Vorgänger seiner Supersede-Kette** durch `[redacted]` ersetzen; dabei werden `redacted_at`, `redacted_by`, `redaction_reason` gesetzt und die referenzierten Attachments gelöscht. Redaktion ist neben Supersede und Void die einzige erlaubte Mutation und wird in `garden_plan_audit` protokolliert. Endpunkt GP-API-041. | ja |
| GP-FR-149 | MUST | **Rückgängig im Feldmodus** (F-13): Nach „Erledigt" oder einem Schnellprotokoll-Chip erscheint 8 s eine Snackbar „Rückgängig"; sie storniert den Task-Abschluss (`reopen`) und das `care_event` (`void` mit `void_reason = undo`) in einer Transaktion. | ja |

---

## 14. Bewässerung

### 14.1 Modell

Eine **Bewässerungszone** (`irrigation_zones`, tenant-scoped, Site-Ebene) bündelt Beete, die gemeinsam bewässert werden — manuell (Gießdienst-Runde), per Tropfschlauch an einem Ventil oder per Sprinkler. Sie ist der Anker für Bedarf, letzten/nächsten Vorgang, Verbrauch und — später — für den Aktor.

```
IrrigationZone {
  name, site_key, tenant_key,
  irrigation_type ∈ {manual, drip, sprinkler, soaker_hose, sub_irrigation},
  water_source_key → garden_objects(water_source) | null,
  actuator_key → actuators(irrigation_valve|pump) | null,   // REQ-018
  flow_rate_l_per_min | null, flow_rate_source ∈ {manual, ha_entity}, flow_rate_ha_entity_id | null,   // O-13
  schedule_hint (Freitext) ,
  color (Darstellung)
}
Location.irrigation_zone_key → irrigation_zones | null
```

Verhältnis zu Bestehendem: `Location.irrigation_system` (Enum, bestehend) bleibt als Eigenschaft des Beets („wie wird hier bewässert"); die Zone ist die Gruppierung. Fehlt eine Zone, gilt das Beet als manuell bewässert. `Site.water_config` (Wasser**qualität**) bleibt unberührt; die **Wasserquelle als Objekt** ist das GardenObject `water_source`.

### 14.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-110 | SHOULD | Zonen anlegen/bearbeiten/löschen je Site; Beete per Mehrfachauswahl auf dem Plan einer Zone zuordnen; die Zone wird als farbiger Umriss/Schraffur über ihren Beeten dargestellt (Ebene „Zonen"). | nein |
| GP-FR-111 | SHOULD | `water_source`-Objekt mit `water_source_kind` (§9.5) und optional `capacity_liters` (Regentonne, Zisterne) und `last_refilled_at`. | nein |
| GP-FR-112 | SHOULD | **Letzter Vorgang:** je Zone und je Beet abgeleitet aus dem jüngsten `care_event(category = watering)` bzw. `watering_events` mit `slot_keys` im Beet. **Nächster geplanter Vorgang:** jüngster offener Task `watering` am Beet/den Beeten der Zone. | nein |
| GP-FR-113 | SHOULD | **Bedarf:** REQ-037 berechnet `irrigation_demands` je Site und Run; die Zone aggregiert `net_demand_mm × bepflanzte Fläche` (REQ-037 `irrigated_area`; bei Mischbeeten Flächenanteil je Entry) ihrer Beete zu Litern, geteilt durch `application_efficiency` (Brutto). Für `planter`/`raised_bed`/`tent` wird die Einzelgabe durch nutzbare Wasserkapazität × Substratvolumen gedeckelt (W-017). `rainfall`-Ereignisse (§12.1) gehen als effektiver Niederschlag ein. Anzeige im Zonen-Panel und als Vorschlags-Task (GP-FR-086). | nein |
| GP-FR-114 | SHOULD | **Verbrauch:** Summe `volume_liters` aus `watering_events` je Zone und Zeitraum; bei Aktor-Zonen zusätzlich `flow_rate_l_per_min × Laufzeit` aus `control_events` (REQ-018). **Durchfluss-Quelle (O-13):** manuell (`flow_rate_l_per_min`, `flow_rate_source = manual`) oder HA-Entität (`flow_rate_ha_entity_id`, `flow_rate_source = ha_entity`), die bei Wert ≤ 24 h alt den manuellen überschreibt; Provenienz am Verbrauchswert (`consumption_source ∈ {manual_log, actuator_runtime_manual_rate, actuator_runtime_ha_rate}`). **Validierung (SR-014):** `flow_rate_ha_entity_id` passt auf `^sensor\.[a-z0-9_]{1,64}$`, muss in der Entitätsliste der HA-Integration **des Tenants** existieren und `device_class ∈ {water, volume_flow_rate}` tragen; setzen darf nur die Zusatzberechtigung **Technik**; der Rohzustand der Entität geht nie an den Client, nur der abgeleitete Liter-Wert; Abruf ausschließlich über den bestehenden HA-Adapter mit SSRF-Guard. **Wirkungsgrad (W-017):** `application_efficiency` je `irrigation_type` (Tropf 0,9, Sprinkler 0,7, manuell 0,8 — überschreibbar); Laufzeit = Brutto-Liter / Durchfluss. | nein |
| GP-FR-115 | COULD | Aktor-Kopplung: Zone → `actuator_key`; „Jetzt bewässern (n Minuten)" ruft den bestehenden `POST /actuators/{key}/command` (REQ-018) auf; der Plan zeigt den Aktorzustand am Ventil-Symbol. | nein |
| GP-FR-116 | COULD | Home-Assistant-Export der Zone als Entität (`ha_publish`, bestehend): Bedarf (L), letzter Vorgang, nächster Vorgang als Sensoren; Ventil als Switch — Vertrag im HA-Dokument (`ha-integration-requirements-engineer`). | nein |
| GP-FR-117 | SHOULD | Gießdienst-Runde (ZG-004): Alle Beete einer Zone in einem Schritt als gegossen protokollieren (GP-FR-088) mit Gesamtmenge, die anteilig nach Beetfläche verteilt wird (Kennzeichnung `allocation = by_area`, alternativ `by_demand`); in Auswertungen (GP-FR-108) werden verteilte Werte nie als gemessen dargestellt. Gießrunde mit Übergabenotiz und „Regen — übersprungen" (F-05). | nein |
| GP-FR-118 | COULD | Bodenfeuchte-Sensor (REQ-005) einer Zone/einem Beet zuordnen; Anzeige des letzten Werts am Beet. | nein |
| GP-FR-119 | SHOULD | Konfliktregel `IrrigationZone.irrigation_type` vs. `Location.irrigation_system`: Die Zone gewinnt für Bedarf/Verbrauch; weicht das Beet ab, zeigt die UI einen Hinweis. Kapazität einer `water_source` (`capacity_liters`) wird gegen den Tagesbedarf der versorgten Zonen geprüft (Hinweis „Regentonne reicht für n Tage"). | nein |

---

## 15. Boden und Substrat

### 15.1 Modell (K-002/K-003 eingearbeitet)

REQ-004 benennt Bodenanalyse-Felder ohne Träger; REQ-019 ordnet Substratchargen nur Slots zu. Für Beete ist die **Location** der richtige Träger. Bodenart (Korngröße), Füllmedium und Zustand sind **drei getrennte Achsen**:

```
Location.soil_profile {
  growing_medium_kind ∈ {native_soil, raised_bed_mix, potting_mix, mineral_substrate, other},
  soil_texture ∈ {sand, loamy_sand, sandy_loam, loam, silt_loam, clay_loam, clay, unknown},   // Korngröße; Hobby-Erfassung über 4 Klassen + Fingerprobe-Hilfe
  stone_content_class ∈ {none, few, many, unknown},
  substrate_key → substrates | null,            // REQ-019, für raised_bed_mix/potting_mix
  substrate_batch_key → substrate_batches | null,
  ph | null, ph_method ∈ {cacl2, h2o, probe_unknown} | null,
  ec_ms_cm | null, humus_percent | null, caco3_percent | null,
  drainage ∈ {poor, moderate, good, unknown},
  site_water_regime ∈ {dry, fresh, moist, wet, unknown},   // Standortansprache (nicht Sensorzustand, H-002)
  conditions: list[ConditionFlag] ⊆ {compacted, depleted, waterlogged, crusting, stony},
  target_ph | null,                              // abgeleitet aus soil_texture (Sand 5,5–6,5, Lehm 6,0–7,0, Ton 6,5–7,5; überschreibbar)
  established_on | null,                        // Anlage-/Befülldatum (Hochbeet-Erstjahr, W-012)
  rotation_reset_at | null,                     // Substratwechsel setzt Fruchtfolge-Historie zurück
  rotation_exempt: bool = false,                 // Dauerkultur (Spargel, Beerensträucher, W-013)
  mulch_factor | null,                           // 0,5–1,0 Verdunstungsmodifikator (W-011)
  last_analysis_at | null,
  notes
}
```

`needs_lime` ist **kein** Feld, sondern wird aus `ph`, `ph_method`, `soil_texture` und `target_ph` abgeleitet (Anzeige „Kalkbedarf wahrscheinlich"). Messwerte werden **als Ereignis** erfasst (`care_event(category = soil_analysis)`) mit je Messwert `{value, unit, extraction_method ∈ {cal, ammonium_acetate, saturated_paste, quick_test, sensor}, sample_depth_cm, source ∈ {lab, test_kit, sensor}}`; Einheiten für Boden sind `mg_per_100g` (P, K, Mg nach CAL, Gehaltsklassen A–E) und `kg_n_per_ha` (Nmin), für Nährlösung/Substrat `mg_per_l` (W-009). Das Profil hält nur den letzten Stand (`ph`, `ec_ms_cm`, `humus_percent`, `caco3_percent`, `last_analysis_at`).

### 15.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-120 | MUST | `soil_profile` am Beet pflegbar (Tab „Boden"); `growing_medium_kind`, `soil_texture` (mit Fingerprobe-Hilfe), `drainage`, `site_water_regime`, `conditions[]` als Auswahl, Rest optional. | ja |
| GP-FR-121 | MUST | Beet-Substrat: für `raised_bed`/`planter` kann ein `substrate_key` (REQ-019) gewählt werden; `ph`/`ec_ms` werden aus `Substrate.ph_base`/`ec_base_ms` vorbelegt. Die Slot-Ebene (`filled_with`) bleibt für Indoor/Hydro; Beet-Slots erben das Beet-Substrat, wenn sie keins haben. | ja |
| GP-FR-122 | SHOULD | Bodenanalyse als Ereignis (§15.1) mit Verlaufsdiagramm pH/EC/Humus im Boden-Tab. | nein |
| GP-FR-123 | SHOULD | **Flächendosierung** (REQ-004 `application_rate_g_per_m2`/`l_per_m2`): Der Düngen-Dialog am Beet rechnet g/m² × `area_m2` in die Gesamtmenge um und schreibt beides (`quantity`, `unit = g_per_m2`, `quantity_total_g`) in den `care_event`. | nein |
| GP-FR-124 | SHOULD | Bodenverbesserungen (Kompost, Mulch, Kalk, Sand, Gründüngung) als `care_event(category ∈ {soil_amendment, mulching, liming})` mit `material ∈ {compost, manure, horn_shavings, lime, sulfur, rock_dust, wood_ash, sand, perlite, biochar, straw_mulch, bark_mulch, grass_clippings, coffee_grounds, green_manure, other}` und Menge. | nein |
| GP-FR-125 | SHOULD | Nährstoff-Hinweis am Beet (W-010): aus `nutrient_demand` der aktuellen Spezies (REQ-001), Vorfrucht (`nitrogen_fixing`-Gutschrift), letzter Düngung/Bodenverbesserung mit Nährstoffwirkung und Gehaltsklassen der Bodenanalyse eine Einschätzung `ok \| check \| likely_deficit \| insufficient_data` mit `confidence` und Begründungstext; beschriftet als „Düngebedarf wahrscheinlich", nie als Messwert. Regelwerk in einem reinen Engine-Modul; Rindenmulch zählt als N-bindend. | nein |
| GP-FR-126 | COULD | Mulchschicht-Status (`mulched_at`, `mulch_material`, `mulch_depth_cm`) im Profil, aus dem letzten Mulch-Ereignis abgeleitet. | nein |
| GP-FR-127 | COULD | Verknüpfung mit `substrate_ec_adapter` / Nährstoffplänen (REQ-004): Nährstoffplan für ein Beet (statt je Pflanze) mit Flächenbezug. | nein |

---

## 16. Fruchtfolge und Mischkultur

### 16.1 Vorhandene Grundlage

- `CropRotationValidator.validate_planting(slot_key, species_key, rotation_window_years, *, tenant_key)` prüft **je Slot** die Familienhistorie der letzten 3 Jahre über `placed_in`.
- `CompanionPlantingEngine.check_compatibility(...)` prüft **Nachbarn** über `adjacent_to` (slots → slots, `distance_cm`); die Kante wird heute nur programmatisch gesetzt, es gibt keinen Endpunkt.
- Graph: `compatible_with`, `incompatible_with`, `family_compatible_with`, `family_incompatible_with`, `rotation_after`, `shares_pest_risk` (global, Plattform-Admin).
- `CropRotationPlan` (REQ-002) mit `demand_level` je Jahr/Saison; `SuccessionPlan` (REQ-013).

### 16.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-130 | MUST | **Nachbarschaft aus Geometrie:** Nach jeder Slot-Geometrieänderung in einem Beet leitet der Service `adjacent_to`-Kanten neu ab: zwei Slots sind benachbart, wenn der Abstand ihrer Zentren ≤ `adjacency_factor × max(spacing_a, row_spacing_a, spacing_b, row_spacing_b)` ist (Standard 1,5 — Diagonale √2 eingeschlossen, übernächster Dreiecksnachbar 1,73 ausgeschlossen; **mit Reihenabstand**, sonst wären alternierende Reihen wirkungslos — W-018); `distance_cm` wird gesetzt. Bei bekanntem `mature_width_cm` beider Arten gilt stattdessen der Interaktionsradius `(w_a + w_b)/2 × 1,2`. Ab 200 Punkt-Slots je Beet werden Nachbarschaften nur noch **zwischen Zonen/Reihen** abgeleitet (Kantenlimit). Manuell gesetzte Kanten (`source = manual`) bleiben; sie werden über einen eigenen Endpunkt mit Site-Gleichheitsprüfung beider Enden gesetzt (SR-021). Der Celery-Job erhält nur `location_key` und löst Site/Tenant selbst auf. Beetübergreifend (Beetkanten ≤ 50 cm) ist SHOULD. | ja (beetintern) |
| GP-FR-131 | MUST | **Fruchtfolge auf Beet-Ebene** (F-12, MVP): `validate_planting_in_location(location_key, species_key, *, tenant_key)` führt die Historie aller Slots des Beets zusammen (ab `rotation_reset_at`, nicht für `rotation_exempt`); Ergebnis je Familie: letzte Spezies, Jahre seit demselben Anbau, **Anbaupause** aus `BotanicalFamily.rotation_pause_years` (neu, Default je Familie; Spezies-Override `Species.rotation_pause_years`; Fallback `rotation_window_years`, Obergrenze auf 8 angehoben — K-004) und `severity` mit Grund (z. B. „Kohlhernie-Risiko: Brassicaceae vor 2 Jahren"). Gründüngung zählt mit ihrer Familie. Mischbeete: jede Familie des Jahres zählt. Vorjahre können nacherfasst werden (Rotationsmatrix editierbar für vergangene Jahre, GP-FR-135; MVP: einfacher Dialog „Was stand hier {Jahr}?" am Beet). | ja |
| GP-FR-132 | MUST | Im Bepflanzen-Dialog (§11.1 Schritt 1) erscheinen Fruchtfolge-Warnung und Mischkultur-Hinweis (zu bereits geplanten/aktiven Nachbarn im Beet über `adjacent_to`) **als Hinweis mit Stärkestufe, nicht als Blocker** (D-09); „Trotzdem pflanzen" speichert den Grund am Run (`rotation_override_reason`). Das Beet trägt auf dem Plan ein Badge, wenn eine aktive Pflanzung einen Fruchtfolge-Hinweis hat. Für `planter`/`tent`/`shelf` standardmäßig aus (GP-FR-137). | ja |
| GP-FR-133 | SHOULD | **Folgekultur-Empfehlung:** aus `rotation_after` (REQ-001) und dem `demand_level`-Zyklus (Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung) eine Liste geeigneter Familien/Spezies für das nächste Jahr, angezeigt im Historie-Tab unter dem Zeitstrahl. | nein |
| GP-FR-134 | SHOULD | **Mischkultur-Overlay** (REQ-028 §7.3): Ebene auf dem Plan, die zwischen benachbarten Pflanzen grüne (kompatibel), rote (inkompatibel) und graue (unbekannt) Verbindungen zeichnet; Hover/Tipp zeigt Grund und Score. Nur für sichtbare Beete, max. 500 Kanten je Viewport (Culling). | nein |
| GP-FR-135 | SHOULD | **Rotationsmatrix** (REQ-002 §1 „Beet × Jahr") als Tabelle je Site: Zeilen Beete, Spalten Jahre, Zellen **Liste** der Familien je Saison (Vor-/Haupt-/Nachkultur, W-013) farbcodiert nach `nutrient_demand`; Datenquelle `care_events`/`plant_instances`, Zukunftsspalten aus `CropRotationPlan`. | nein |
| GP-FR-136 | COULD | Problematische Pflanzen je Beet: Spezies, deren Familie in den letzten `rotation_window_years` im Beet stand oder die mit aktiven Nachbarn inkompatibel sind — als Negativliste im Bepflanzen-Dialog ausgegraut mit Grund. | nein |
| GP-FR-137 | MUST | Fruchtfolge für `planter`, `tent`, `shelf` standardmäßig aus (Substratwechsel ersetzt die Rotation, REQ-001) und für `rotation_exempt`-Beete (Dauerkulturen) aus; je Beet einschaltbar. | ja |

### 16.3 Zehrerstufe, Stickstofffixierung und Planrolle (O-07, revidiert nach K-001)

Heute existieren drei Enums für dieselbe Sache und ein Merkmal steckt im falschen Enum: `Species.nutrient_demand_level` (`heavy_feeder|medium_feeder|light_feeder|nitrogen_fixer`), `BotanicalFamily.typical_nutrient_demand` (`light|medium|heavy`) plus `BotanicalFamily.nitrogen_fixing` (Bool), `CropRotationPlan.demand_level` (`…|green_manure|fallow`). `nitrogen_fixer` ist **keine** Zehrerstufe — eine Erbse ist Schwachzehrer *und* N-Fixierer (K-001). REQ-053 legt daher **drei getrennte Begriffe** fest, die REQ-001 und REQ-002 übernehmen:

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-138 | MUST | **`NutrientDemand`** = `heavy_feeder \| medium_feeder \| light_feeder` an Spezies (`Species.nutrient_demand`, Pflicht bei Nutzpflanzen, mit `source`/`confidence` — H-004) und Familie (`BotanicalFamily.typical_nutrient_demand`). **`nitrogen_fixing: bool`** an Spezies (neu) und Familie (vorhanden). **`PlanRole`** = `main_crop \| green_manure \| fallow` am `PlantingRun` (`plan_role`, Standard `main_crop`) und am `CropRotationPlan` (ersetzt `demand_level`; `fallow` ist dort der einzige Wert ohne Run). Pydantic-Validatoren: `fallow` nie an Spezies/Familie/Run; `green_manure` am Run verlangt `Species.green_manure_suitable = true`. | ja (Welle 1) |
| GP-FR-139 | MUST | Migration `v0077_nutrient_demand_split`: `Species.nutrient_demand_level = nitrogen_fixer` → `nitrogen_fixing = true` und `nutrient_demand` aus dem Steckbrief (Pflichtfeld in `plant_info.schema.yaml`; fehlt der Wert, bleibt `nutrient_demand = null` und der Dry-Run-Report listet die Spezies — **kein** stiller Default); `BotanicalFamily.typical_nutrient_demand` `light→light_feeder`, `medium→medium_feeder`, `heavy→heavy_feeder`; `CropRotationPlan.demand_level` → `nutrient_demand` + `plan_role`. Schemas `_defs.schema.yaml:51`, `species.schema.yaml`, `plant_info.schema.yaml`, `botanical_families.schema.yaml:31` und Seeds werden umgestellt; `seed-data-validator` prüft danach. REQ-001 §2 und REQ-002 §2 erhalten eine Changelog-Zeile mit Verweis auf GP-FR-138. | ja (Welle 1) |

Die Rotationslogik (Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung/Brache) in GP-FR-131/133/135 arbeitet auf `NutrientDemand` + `PlanRole`; die N-Gutschrift einer Leguminosen-Vorfrucht kommt aus `nitrogen_fixing`.

## 17. UX/UI

### 17.1 Layout

| Breakpoint (UI-NFR-001) | Layout |
|-------------------------|--------|
| ≥ md (Desktop/Tablet quer) | Dreiteilig: linke Werkzeugleiste (vertikal, 48 px Icons mit Tooltip), Canvas in der Mitte, rechtes Eigenschaftenpanel (320 px, einklappbar). Kopfzeile nach UI-NFR-021 (Titel, Speichern-Status, Undo/Redo, Zoom, Raster, Drucken). |
| sm (Tablet hochkant) | Werkzeugleiste oben horizontal, Panel als Bottom Sheet (halb/voll), Canvas füllt den Rest. |
| xs (Smartphone) | Feldmodus als Standard (§18); Editiermodus erreichbar über „Bearbeiten", mit reduzierten Werkzeugen (Verschieben, Position korrigieren, Eigenschaften) — Zeichnen neuer Polygone auf xs ist zulässig, aber nicht abgenommen (O-10, entschieden). |

### 17.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-001 | MUST | Die Werkzeugleiste zeigt höchstens 8 Werkzeuge auf oberster Ebene (Auswahl, Hand/Pan, Beet, Bereich, Gartenobjekt ▸ Untermenü, Pflanze setzen, Messen [COULD], Text/Label); seltene Objekte liegen im Untermenü. Max. 2 Ebenen (UI-NFR-019 R-019 sinngemäß). | ja |
| GP-UX-002 | MUST | Jeder Cursor-Modus ist sichtbar (Cursor-Form + aktives Werkzeug hervorgehoben) und per Esc verlassbar. | ja |
| GP-UX-003 | MUST | Speichern-Status in der Kopfzeile: „Gespeichert", „Ungespeicherte Änderungen (n)", „Speichert…", „Konflikt" — kein Auto-Save im **Planungsmodus**; expliziter Speichern-Button + `Ctrl/Cmd+S`; Verlassen mit ungespeicherten Änderungen fragt nach (Guard-Dialog, bestehendes Muster, Memory #1689 beachten). Im **Feldmodus** gibt es keinen Dirty-Zustand: jede Aktion (Erledigt, Notiz, Foto, Position korrigieren, Gepflanzt) wird sofort gesendet (F-16). | ja |
| GP-UX-004 | SHOULD | Auto-Save nach 2 s Inaktivität als nutzerbezogene Option; bei Konflikt wird Auto-Save pausiert. | nein |
| GP-UX-005 | MUST | Legende (ein-/ausblendbar) mit allen auf dem Plan vorkommenden Objektklassen und Phasenfarben; Legende ist Teil des PDF. | ja |
| GP-UX-006 | MUST | Hover (Desktop) / Tipp (Touch) auf ein Objekt zeigt eine Info-Blase: Name, Typ, Maße, bei Beeten aktive Pflanzen, offene Aufgaben, **Vorjahr** (GP-FR-077) und zuletzt gegossen; Doppelklick/zweiter Tipp öffnet die Detailseite. | ja |
| GP-UX-007 | MUST | Drag & Drop mit Vorschau (Geisterobjekt), Snap-Markierung (Hilfslinie), Abbruch per Esc; während des Drags werden Position und Maß live angezeigt (GP-FR-014). | ja |
| GP-UX-008 | MUST | Touch: Ein-Finger-Drag auf Objekt = Verschieben nur nach **Long-Press 500 ms** (sonst Pan) — verhindert versehentliches Verschieben beim Scrollen; Zwei-Finger = Pan/Zoom/Rotate-Geste (Rotate SHOULD). Touch-Ziele für Griffe ≥ 48 px (UI-NFR-001 R-011), auf Beeten ohne Griffe: ganze Fläche. | ja |
| GP-UX-009 | MUST | Tastatursteuerung vollständig (§24): Tab durch Objekte in DOM-Reihenfolge (Zeile, dann Spalte, UI-NFR-002 R-026), Pfeile verschieben, `R` rotiert 15°, `+/-` Zoom, `G` Raster, `Entf`, `Ctrl+D`, `Ctrl+Z/Y`, `Esc`. Hilfe-Overlay mit `?`. | ja |
| GP-UX-010 | MUST | Beschreibende Texte (Feedback-Memory „Beschreibende Texte in der UI"): Leerzustand des Plans erklärt in zwei Sätzen, was zuerst zu tun ist („Zeichne die Umrisse deines Gartens. Du kannst sie später jederzeit anpassen."); jedes Werkzeug hat einen Tooltip mit Verb. | ja |
| GP-UX-011 | MUST | Fachbegriffe (Pflanzabstand, Reihenabstand, Randabstand, Fruchtfolge) mit Glossar-Erklärung nach UI-NFR-011. | ja |
| GP-UX-012 | MUST | `data-testid` nach UI-NFR-022: `garden-plan-page`, `garden-plan-canvas`, `plan-tool-<name>`, `plan-object-<key>`, `plan-handle-<position>`, `plan-properties-panel`, `form-field-<name>`, `save-plan-button`, `plan-conflict-dialog`, `bed-detail-page`, `bed-plan-tab`, `care-event-row-<key>`. Neue Muster werden vor Verwendung in UI-NFR-022 registriert (R-020). | ja |
| GP-UX-013 | MUST | i18n-Schlüssel unter `pages.gardenPlanner.*`, Enums unter `enums.gardenObjectType.*`, `enums.bedStatus.*`, `enums.careEventCategory.*`, `enums.irrigationType.*`, `enums.layoutStrategy.*`; DE und EN vollständig (NFR-017). | ja |
| GP-UX-014 | SHOULD | Mini-Map rechts unten (120 × 120 px), bedingt sichtbar (§9.6), zeigt Viewport-Rechteck, Klick springt. | nein |
| GP-UX-015 | MUST | Phasenfarben und Icons der Pflanzen folgen UI-NFR-016; die Farbe ist nie der einzige Informationsträger (Icon + Beschriftung bei Zoom ≥ 100 %). | ja |
| GP-UX-016 | MUST | Dark Mode: Plan-Palette hat eigene Tokens (Boden, Rasen, Weg, Wasser) mit Kontrast ≥ 3:1 gegen den Hintergrund in beiden Themes (UI-NFR-006). | ja |
| GP-UX-017 | MUST | Fehler-Feedback nach UI-NFR-004: Validierungsfehler der API (§22) werden am betroffenen Objekt markiert (roter Rand) und im Panel erklärt; ein 409-Konflikt öffnet einen Dialog mit „Neu laden" / „Meine Änderungen als Kopie behalten (JSON herunterladen)". | ja |

---

## 18. Mobile Nutzung im Garten (Feldmodus)

### 18.1 Zentrales Szenario

Der Nutzer steht mit Smartphone oder Tablet im Garten, Hände feucht oder verschmutzt, Sonne auf dem Display, oft nur eine Hand frei. Er will **lesen und bestätigen**, selten zeichnen.

| Schritt | Interaktion im Feldmodus | Zielzeit |
|---------|--------------------------|----------|
| 1. Plan öffnen | Site-Liste → „Plan" (oder QR-Etikett am Beet, GP-FR-052); der Plan lädt mit letztem Viewport | < 3 s auf 4G (GP-NFR-002) |
| 2. Beet auswählen | Ein Tipp auf das Beet (ganze Fläche ist Ziel; Mindestgröße auf dem Bildschirm 48 px, sonst Auto-Zoom auf das Beet beim Tipp in die Nähe) | 1 Tipp |
| 3. Sehen, was gepflanzt ist | Bottom Sheet mit Beetname, Pflanzen (Spezies, Anzahl, Phase), offene Aufgaben | sofort |
| 4. Pflegeaufgabe sehen | Aufgaben als Liste im Sheet, überfällige zuerst, Kategorie-Icon ≥ 32 px | — |
| 5. Als erledigt markieren | Großer Button „Erledigt" (≥ 64 × 64 px, UI-NFR-019 R-007) → Schnell-Dialog mit optionalen Feldern (Menge/Notiz) → „Fertig". **Zwei Tipps** nach der Beetauswahl (GP-ACC-029); 8 s „Rückgängig" (GP-FR-149) | 2 Tipps |
| 6. Notiz hinzufügen | „Notiz" im Sheet → Textfeld + Spracheingabe des OS → `care_event(category = note)` | 3 Tipps |
| 7. Foto hinzufügen | „Foto" → Kamera (REQ-052 Profil `gallery`) → Zuordnung Beet oder Pflanze | 3 Tipps |
| 8. Neue Pflanzung dokumentieren | „Gepflanzt" → Spezies (Favoriten zuerst, REQ-020-Favoriten), Anzahl, Layout-Vorgabe → Run `active` + Pflanzen werden sofort erzeugt (Kurzpfad aus §11.1) | ≤ 6 Tipps |
| 9. Tatsächliche Position korrigieren | Pflanze antippen → „Position korrigieren" → **Stepper als Standard** (±10 cm, bildschirmbezogen hoch/runter/links/rechts, F-16) auf dem vergrößerten Beet; Long-Press-Drag als Alternative | ≤ 4 Tipps |

### 18.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-020 | MUST | Feldmodus ist die Standardansicht auf xs (< 600 px) und per Schalter auf allen Breiten verfügbar (`?mode=field`); er blendet Zeichenwerkzeuge, Raster und Griffe aus und vergrößert Touch-Ziele auf 64 px (Kiosk-Theme-Konstanten `KIOSK_TOUCH_TARGET` wiederverwenden). | ja |
| GP-UX-021 | MUST | Kontrast im Feldmodus ≥ 7:1 für Text und ≥ 4,5:1 für Objektgrenzen (UI-NFR-019 R-040 sinngemäß, Sonnenlicht); Phasenfarben bekommen Umriss. | ja |
| GP-UX-022 | MUST | Keine reine Swipe-Bedienung (UI-NFR-019 R-028); jede Geste hat eine Schaltflächen-Alternative. | ja |
| GP-UX-023 | MUST | Debounce 300 ms auf „Erledigt" (R-029), Long-Press 500 ms für Verschieben, 2 s für destruktive Aktionen (Löschen ist im Feldmodus nicht verfügbar); nach dem ersten Tipp auf „Erledigt" ist der Button bis zur Server-Antwort gesperrt (Doppeltipp, F-16). | ja |
| GP-UX-024 | SHOULD | Offline-Lesen des Plans (UI-NFR-012 R-020: Standorte offline lesbar): letzter geladener Plan je Site im IndexedDB-Cache (TTL 15 min, R-012); Erledigen/Notiz/Foto werden als Offline-Einträge gepuffert (R-015, max. 500, R-019) und bei Verbindung mit `performed_at` aus dem Erfassungszeitpunkt gesendet. Geometrie-Änderungen bleiben online-only (Konfliktrisiko). Cache-Schlüssel enthält `user_key` und `tenant_key`; Logout und Tenant-Wechsel leeren Plan-Cache und Offline-Puffer (SR-019). Bis dahin zeigt der Feldmodus bei fehlender Verbindung einen sichtbaren Offline-Hinweis und sperrt „Erledigt" statt still zu verlieren (F-17, MVP). | nein (Puffer), ja (Offline-Hinweis) |
| GP-UX-025 | MUST | Der Feldmodus funktioniert ohne Hover: alle Infos erscheinen per Tipp; Tooltips werden durch Sheet-Inhalte ersetzt. | ja |
| GP-UX-026 | SHOULD | GPS-Hilfe: Ist `Site.gps_coordinates` + `north_angle_deg` gesetzt und erlaubt der Nutzer die Ortung (REQ-002 Opt-in-Muster), markiert ein Punkt die ungefähre eigene Position auf dem Plan (Genauigkeitskreis ≥ 3 m). **Die Eigenposition verlässt das Gerät nie** (SR-019): kein API-Request, keine URL, kein Redux-Persist, kein IndexedDB, kein Log, kein Sentry-Event — nur flüchtiger Komponentenzustand. | nein |
| GP-UX-027 | MUST | Der Kurzpfad „Gepflanzt" (Schritt 8) erzeugt Run **und** Pflanzen in einem Request (`POST …/locations/{key}/quick-planting`), damit im Garten kein zweistufiger Ablauf nötig ist; der Run erhält `source = field_mode`. | ja |
| GP-UX-028 | SHOULD | Beet-QR-Code (GP-FR-052) öffnet direkt die Beetansicht im Feldmodus; ohne Session → Login → Rücksprung (bestehende Redirect-Logik, UI-NFR-014). | nein |
| GP-UX-029 | MUST | **Schnellprotokoll** im Feldmodus (F-03): sechs Chips (Gegossen · Geerntet · Gesät · Gejätet/Gemulcht · Gepflanzt · Notiz) im Beet-Sheet; jeder Chip erzeugt mit einem Tipp ein `care_event` (bzw. öffnet den Kurzpfad für Gepflanzt/Geerntet) und zeigt die Rückgängig-Snackbar. | ja |
| GP-UX-030 | MUST | **Einstieg über Liste** (F-18): Der Feldmodus startet mit „Meine Beete · heute fällig" (Liste, nach Zuweisung und Fälligkeit sortiert) und bietet „Karte" als zweiten Tab; Tenant, Site und Viewport werden je Gerät gemerkt (localStorage); Schrift ≥ 16 px; Aufgaben werden vor der Geometrie geladen (zwei Requests, Liste zuerst). | ja |
| GP-UX-031 | SHOULD | Ebene „zuletzt gegossen" (Farbskala Tage seit letztem `watering`-Ereignis je Beet) für Gießdienste (F-05). | nein |

---

## 19. Technische Architektur

### 19.1 Schichten (NFR-001)

```
Presentation  React 19 / MUI 9 / Redux Toolkit
  features/gardenPlanner/
    model/        PlanModel (TS-Typen = DTO v1), PlanOperation, applyOperation(), geometry.ts (Port der Calculators)
    state/        gardenPlanSlice (Plan, Auswahl, Werkzeug, Undo-Stack, Dirty-Flag, Konflikt)
    renderer/     PlanRenderer (Interface) → SvgPlanRenderer (MVP) | KonvaPlanRenderer (Fallback)
    editor/       GardenPlanEditor, Toolbar, PropertiesPanel, FieldModeSheet, Handles, Gestures
    api/          gardenPlan.ts (axios über tenantClient)
API           FastAPI  api/v1/garden_plan/ (tenant_router, schemas v1), Erweiterungen locations/slots/planting_runs/tasks
Business      domain/services/garden_plan_service.py, care_event_service.py, irrigation_zone_service.py
              domain/calculators/geometry_calculator.py, planting_layout_calculator.py
              domain/engines/adjacency_engine.py
Data Access   data_access/arango/garden_object_repository.py, care_event_repository.py, irrigation_zone_repository.py,
              Erweiterung site_repository (plan), location/slot (geometry); Stream-Transaktion im garden_plan_repository
Persistence   ArangoDB Collections + Edges (§20), Migration v0072+
```

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-001 | MUST | Keine neue Schicht, kein zweiter API-Stil: Endpunkte unter `/api/v1/t/{tenant_slug}/…`, Fehlerformat NFR-006, Pydantic-v2-Schemas mit `to_response`, Service-Signaturen mit `tenant_key` **keyword-only ohne Default** (Memory „Guard opt-in am Aufrufort"). |
| GP-NFR-002 | MUST | Plan-Ladezeit: `GET …/sites/{key}/plan` liefert den gesamten Plan (Site-Plan, Locations mit Geometrie, GardenObjects, Slots mit Geometrie, Pflanzen-Kurzinfo, Task-Zähler) in **einem** Request; Antwort ≤ 500 KB bei einem großen Garten (§25) und ≤ 300 ms p95 serverseitig. |
| GP-NFR-003 | MUST | Der Editor wird per Dynamic Import geladen (UI-NFR-003 R-012/R-028); der Initial-Bundle-Zuwachs durch dieses Feature ist **0 KB**; der Editor-Chunk ≤ 120 KB gzip (SVG-Renderer) bzw. ≤ 200 KB gzip (mit Konva). `bundle-budget.json` erhält einen Eintrag `gardenPlanner` mit diesem Budget. |
| GP-NFR-004 | MUST | Versionierte DTOs: Plan-Schemas tragen `schema_version: "1"` im Export (§23) und in `GET /plan`; Breaking Changes erzeugen `schema_version: "2"` mit Import-Migration. |

### 19.2 Domänenmodell im Frontend

Das Frontend hält den Plan als **normalisiertes Modell** (`entities: {locations, gardenObjects, slots, plants}`, `ids`), identisch zum DTO. Der Renderer bekommt dieses Modell plus Viewport und liefert ein Bild; er hält keinen Zustand außer Caches. Alle Nutzeraktionen werden zu `PlanOperation`s:

```ts
type PlanOperation =
  | { op: 'create_location'; temp_key: string; data: LocationCreate }
  | { op: 'update_geometry'; entity: 'location' | 'garden_object' | 'slot'; key: string; geometry: Geometry }
  | { op: 'update_fields'; entity: ...; key: string; patch: Partial<...> }
  | { op: 'create_garden_object'; temp_key: string; data: GardenObjectCreate }
  | { op: 'delete'; entity: ...; key: string }
  | { op: 'set_boundary'; boundary: Geometry; north_angle_deg?: number };
```

`applyOperation(model, op) → model` ist rein und invertierbar (jede Operation kennt ihre Umkehrung für Undo). Die Operationsliste ist zugleich der Request-Body der Batch-API (§21.3).

### 19.3 State Management

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-005 | MUST | Ein Slice `gardenPlanSlice` (RTK `createSlice`, Thunks für load/save, kein RTK Query — Bestandsmuster). Undo/Redo als `past[]/future[]` von Operationen im Slice; Dirty-Flag = `pending.length > 0`. |
| GP-NFR-006 | MUST | Optimistic Updates: Operationen werden sofort auf das Modell angewandt; Speichern sendet `pending[]` mit `expected_revision`; bei 2xx wird `plan_revision` übernommen und `pending` geleert; bei 409 bleibt `pending` erhalten, Konflikt-Dialog (GP-UX-017). |
| GP-NFR-007 | MUST | Concurrent Editing: **kein** Echtzeit-Mehrbenutzer-Editing (WON'T, §29). Schutz ist die optimistische Revision auf Site-Ebene **für Strukturänderungen** (Locations, GardenObjects, Boundary, Zonen — alles, was Containment betrifft). **Außerhalb der Revision** (F-09, D-06 revidiert) laufen: Slot-Geometrie-Korrekturen (GP-FR-068), Quick-Planting (GP-API-017), Slot-Batch eines Beets (GP-API-015), Tasks und `care_events` — sie kollidieren nicht mit einem offenen Planungs-Editor; der Editor übernimmt sie beim nächsten Laden oder per Hinweis „Beet 3 wurde aktualisiert" (Polling 30 s im Planungsmodus, SHOULD). Zwei Gärtner, die gleichzeitig Struktur ändern, bekommen beim zweiten Speichern 409. Parzellen können für Mitglieder `locked` sein (GP-FR-032); `locked` sperrt Struktur, nicht Pflege. |
| GP-NFR-008 | MUST | Custom Hooks mit Objekt-/Array-Rückgabe nutzen `useMemo` (FRONTEND.md); Renderer-Props sind referenzstabil, damit Objekte nur bei Änderung neu zeichnen. |

### 19.4 Rendering-Technologie

**Bewertungskriterien** (je 0–3; Lizenz ist K.-o.): Open-Source-Lizenz · React-19-Integration · Polygon-Bearbeitung · Zoom/Pan · Touch · Drag & Drop · Snap-to-Grid · Performance bei 2 000 Objekten · Persistierbarkeit (Trennung Modell/Ansicht) · Accessibility (DOM-Semantik) · Wartbarkeit/Testbarkeit (jsdom, Snapshot) · Bundle-Größe · Projektrisiko (Pflege, Bus-Faktor).

| Kriterium | **SVG in React** (kein Framework) | **Konva + react-konva** | **Fabric.js v6** | **HTML Canvas roh** | **Pixi.js** |
|-----------|----|----|----|----|----|
| Lizenz | — (Browser) ✔ | MIT ✔ | MIT ✔ | — ✔ | MIT ✔ |
| React 19 | 3 (nativ) | 3 (react-konva 19.x) | 1 (imperativ, Wrapper nötig) | 1 | 1 (react-pixi veraltet) |
| Polygon-Editing | 3 (DOM-Punkte, eigene Griffe) | 2 (Line + eigene Griffe) | 3 (eingebaut) | 1 | 1 |
| Zoom/Pan | 3 (viewBox) | 3 (Stage scale) | 2 | 2 | 3 |
| Touch | 2 (Pointer Events) | 3 | 2 | 2 | 3 |
| Drag & Drop | 2 (Pointer Events, eigene Logik) | 3 | 3 | 1 | 2 |
| Snap-to-Grid | 3 (Modellseitig, unabhängig) | 3 | 2 | 3 | 3 |
| Performance 2 000 Objekte | 2 (DOM; bis ~3 000 flüssig mit Culling) | 3 | 2 | 3 | 3 |
| Persistierbarkeit | 3 (Modell ist die Quelle) | 3 (wenn diszipliniert) | 1 (Fabric-JSON verführt zum Modell) | 3 | 3 |
| Accessibility | 3 (`role`, `aria-label`, Fokus je `<g>`) | 0 (Bitmap; Parallel-DOM nötig) | 0 | 0 | 0 |
| Testbarkeit | 3 (jsdom, Snapshot, `data-testid`) | 1 (Canvas-Mock) | 1 | 1 | 1 |
| Bundle | 3 (0 KB) | 2 (~50 KB gzip) | 1 (~100 KB) | 3 | 1 (~150 KB) |
| Projektrisiko | 3 | 2 (kleines Team, aktiv) | 2 (v6-Umbruch 2024) | 3 | 2 |
| **Summe** | **33** | **28** | **20** | **23** | **23** |

**Entscheidung D-01 (§33): SVG in React als MVP-Renderer**, mit `PlanRenderer`-Grenze, hinter der ein Konva-Renderer nachgerüstet wird, sobald die Performance-Schwelle (GP-NFR-013: > 3 000 sichtbare Objekte oder Frame-Zeit > 16 ms bei Drag) in der Messung gerissen wird. Begründung: Accessibility (UI-NFR-002 R-024–R-027 verlangen fokussierbare, benannte Objekte — mit Canvas nur über ein Parallel-DOM), Testbarkeit mit dem bestehenden vitest/jsdom-Setup, 0 KB Bundle (Budget-Memory), und die Gartengrößen der Zielgruppe (§25: „groß" = 500 Objekte, 2 000 Pflanzen) liegen innerhalb der SVG-Komfortzone mit Viewport-Culling. Konva wurde **nicht** verworfen, sondern als zweiter Renderer vorgesehen; die Grenze ist nicht spekulativ, weil sie die Testdoubles (Headless-Renderer für Unit-Tests) ohnehin braucht.

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-009 | MUST | `PlanRenderer`-Interface: `render(model, viewport, selection, options) → ReactNode`, `hitTest(point_px) → key \| null`, `toScreen(p_m)`, `toModel(p_px)`. Editor-Logik (Werkzeuge, Griffe, Snap, Undo) importiert **keine** Renderer-Bibliothek. Ein ESLint-`no-restricted-imports`-Eintrag erzwingt das für `features/gardenPlanner/editor/**`. |
| GP-NFR-010 | MUST | Viewport-Culling: nur Objekte, deren `bbox` den Viewport schneidet (± 20 % Rand), werden gerendert; Pflanzen-Marker erst ab Zoom ≥ 50 %, Beschriftungen ab 100 %. |
| GP-NFR-011 | MUST | Drag-Rendering nutzt eine CSS-Transformation des bewegten `<g>` (kein Re-Render des Modells je Mausbewegung); das Modell wird erst beim Loslassen aktualisiert. |

### 19.5 Backend

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-012 | MUST | Geometrie-Validierung und Flächenberechnung in `domain/calculators/geometry_calculator.py` (rein, ohne I/O, Property-Tests mit Hypothesis: Fläche ≥ 0, Shoelace = Rechteckformel für rect, Rotation erhält Fläche). Keine externe Geometrie-Bibliothek im MVP (Shapely wäre nur für Polygon-Schnitt nötig → COULD für GP-FR-012 Objekt-Snap und Überlappungsprüfung; Entscheidung D-04). |
| GP-NFR-013 | MUST | Die Batch-API läuft in **einer** ArangoDB-Stream-Transaktion (`db.begin_transaction(write=[…])`) mit Revisionsprüfung: `IF site.plan.plan_revision != expected → abort 409`. Alles-oder-nichts, im Gegensatz zum bestehenden `BatchResponse`-Teilerfolg bei Tasks (bewusste Abweichung: eine halb gespeicherte Geometrieänderung ist nicht reparierbar). **Komplexitätsbudget (SR-012):** zusätzlich zu 500 Operationen gilt Σ Polygonpunkte ≤ 20 000 je Batch, Request-Body ≤ 2 MB und ein Zeitbudget von 10 s (422 `batch.too_complex`); Containment- und Überlappungsprüfung laufen **vor** dem Öffnen der Transaktion (nur Revisionsprüfung und Schreiben laufen darin). |
| GP-NFR-014 | MUST | Containment-Regeln (§22) werden im Service geprüft, nicht im Router; der Service nimmt Eltern-Keys und `tenant_key` keyword-only (Memory „Prädikat in den Service"). |
| GP-NFR-015 | MUST | Migrationen nach NFR-016/ADR-005: `v0072_garden_plan_geometry` (Collections, Edges, Indizes; `dimensions` → `geometry`/`height_m` und `Slot.position` → `geometry` mit `pitch_m`, beide Felder danach entfernt — O-01/O-02), `v0073_location_type_is_bed` (Seeds, `is_bed`), `v0074_task_category_extension`, `v0075_care_events_backfill` (SHOULD, GP-FR-105), `v0076_recurrence_cron_to_rrule` (O-05), `v0077_feeder_level_unify` (O-07). Jede Migration ist `reversible` oder begründet nicht; v0072, v0076 und v0077 liefern einen Dry-Run-Report (`--dry-run`), weil sie Bestandsdaten umformen. |
| GP-NFR-016 | SHOULD | Celery: `adjacency_recompute` (nach Slot-Batch, entkoppelt, idempotent), `care_events_consistency` (täglich), `irrigation_zone_demand_aggregate` (täglich nach REQ-037). |
| GP-NFR-017 | MUST | **Harte Quoten (SR-004):** je Site ≤ 500 Locations + GardenObjects, ≤ 8 000 Slots; je Beet ≤ 2 000 Slots; Quick-Planting `quantity` ≤ 500. Überschreitung → 422 `plan.quota_exceeded {limit, current}`. §25.1 „Belastungsgrenze" ist damit eine Quote, keine Prosa. |

### 19.6 Geteilte Berechnungen (Backend ↔ Frontend)

`planting_layout_calculator.py` und `geometry_calculator.py` werden in TypeScript portiert (`features/gardenPlanner/model/geometry.ts`, `layout.ts`). Beide Seiten laufen gegen **dieselben Testvektoren** (`spec/e2e-testcases/fixtures/garden-plan-vectors.json`, neu anzulegen, SSOT; je ein Test in pytest und vitest liest die Datei). Die Serverantwort ist bei Abweichung maßgeblich (GP-FR-063). Damit entsteht keine Logik-Duplikation ohne Kontrolle — das Memory-Muster „Test erreicht die Regel über einen anderen Pfad als die Produktion" wird durch die gemeinsamen Vektoren adressiert.

### 19.7 Import/Export-Architektur

Export und Import laufen serverseitig (§23): JSON-Backup über `garden_plan_service.export()`/`import_()`, PDF über den bestehenden `PrintEngine` mit einer Jinja-Vorlage `garden_plan.html`, in die ein serverseitig erzeugtes SVG eingebettet wird (ein Python-SVG-Writer in `domain/engines/plan_svg_engine.py`, ohne externe Lib — WeasyPrint rendert SVG nativ). PNG entsteht clientseitig aus dem SVG-DOM (Canvas `drawImage`, bestehendes Muster aus `PlantTagDialog`).

---

## 20. Datenmodell

### 20.1 Geometrie (eingebetteter Werttyp, Pydantic `Geometry`)

```json
{ "kind": "rect",     "origin": [2.000, 3.500], "width_m": 3.000, "length_m": 1.200, "rotation_deg": 0.0 }
{ "kind": "circle",   "origin": [8.250, 1.000], "radius_m": 0.400 }
{ "kind": "polygon",  "points": [[0,0],[4.2,0],[4.2,1.5],[2.0,2.6],[0,1.5]], "rotation_deg": 0.0 }
{ "kind": "polyline", "points": [[0,5],[12,5]], "width_m": 0.800 }
{ "kind": "point",    "origin": [0.300, 0.300] }
```

| Feld | Typ | Regel |
|------|-----|-------|
| `kind` | `rect \| circle \| polygon \| polyline \| point` | je Objektklasse eingeschränkt (§9.5) |
| `origin` | `[x, y]` in m | Rect: linke untere Ecke vor Rotation; Circle/Point: Mittelpunkt |
| `width_m`, `length_m`, `radius_m`, `width_m` (polyline) | float, 3 Dezimalen | 0,01 ≤ v ≤ 1 000 |
| `points` | `[[x,y], …]` | polygon ≥ 3, polyline ≥ 2, ≤ 200 Punkte; polygon einfach (keine Selbstschnitte) |
| `rotation_deg` | float | 0 ≤ r < 360; für circle/point/polyline nicht erlaubt |

Abgeleitet (serverseitig, read-only im DTO): `area_m2`, `bbox`, `centroid`.

**Rahmen:** `Site.plan.boundary`, `Location.geometry`, `GardenObject.geometry` → Plan-Rahmen. `Slot.geometry` → Beet-Rahmen der übergeordneten Location (§9.2).

### 20.2 Site (bestehend, additiv)

```json
{
  "_key": "site_7f3a",
  "tenant_key": "t_garten_sabine",
  "name": "Gemüsegarten hinterm Haus",
  "type": "outdoor",
  "gps_coordinates": [52.5200, 13.4050],
  "total_area_m2": 60.0,
  "plan": {
    "boundary": { "kind": "polygon", "points": [[0,0],[10,0],[10,6],[0,6]], "rotation_deg": 0.0 },
    "north_angle_deg": 15.0,
    "default_grid_m": 0.10,
    "adjacency_factor": 1.5,
    "plan_revision": 42,
    "plan_updated_at": "2026-10-04T09:12:33Z",
    "plan_updated_by": "u_sabine"
  }
}
```

`plan` ist optional; eine Site ohne `plan` ist eine Site ohne Gartenplan (Bestandsverhalten). `total_area_m2` wird bei gesetzter `boundary` daraus berechnet.

### 20.3 Location (bestehend, additiv) — Beispiel Beet

```json
{
  "_key": "loc_b03", "tenant_key": "t_garten_sabine",
  "site_key": "site_7f3a",
  "parent_location_key": "loc_nutzgarten",
  "location_type_key": "raised_bed",
  "name": "Hochbeet 3",
  "description": "Südseite, Lärchenholz, 2024 gebaut",
  "depth": 2, "path": "site_7f3a/loc_nutzgarten/loc_b03",
  "geometry": { "kind": "rect", "origin": [1.0, 1.0], "width_m": 2.0, "length_m": 1.0, "rotation_deg": 90.0 },
  "height_m": 0.8,
  "area_m2": 2.0,
  "bbox": [1.0, 1.0, 2.0, 3.0],
  "bed_status": "active", "season_state": "planted",
  "sun_exposure": "full_sun",
  "irrigation_system": "drip",
  "irrigation_zone_key": "zone_sued",
  "soil_profile": {
    "growing_medium_kind": "raised_bed_mix", "soil_texture": "unknown", "stone_content_class": "none", "substrate_key": "sub_hochbeet_mix", "substrate_batch_key": null,
    "ph": 6.8, "ph_method": "cacl2", "ec_ms_cm": 1.1, "humus_percent": 8.0, "caco3_percent": null, "drainage": "good", "site_water_regime": "fresh",
    "conditions": [], "target_ph": 6.5, "established_on": "2024-04-01", "rotation_reset_at": null, "rotation_exempt": false, "mulch_factor": 0.8, "last_analysis_at": "2026-03-12", "notes": "Kompost oben nachgefüllt"
  },
  "notes": "Tomaten hier wegen Regenschutz durch Dachüberstand.",
  "locked": false,
  "z_order": 10,
  "photo_refs": [], "cover_photo_ref": null,
  "orientation": "south",
  "light_type": "natural",
  "frost_exposed": true,
  "created_at": "…", "updated_at": "…"
}
```

Bestandsfelder `dimensions` (3-Tupel) und die in REQ-002 vorgesehenen `bed_width_cm`, `bed_length_cm`, `bed_orientation`, `bed_type`, `bed_rows`, `row_spacing_cm` werden **nicht** eingeführt bzw. als abgeleitet markiert (§20.8).

### 20.4 GardenObject (neu, Collection `garden_objects`)

```json
{
  "_key": "go_91ab",
  "tenant_key": "t_garten_sabine",
  "site_key": "site_7f3a",
  "parent_location_key": null,
  "object_type": "water_source",
  "label": "Regentonne Ost",
  "geometry": { "kind": "point", "origin": [9.7, 0.4] },
  "bbox": [9.45, 0.15, 9.95, 0.65],
  "props": { "water_source_kind": "rain_barrel", "capacity_liters": 300, "last_refilled_at": null },
  "locked": false, "z_order": 5,
  "notes": "",
  "created_at": "…", "updated_at": "…", "created_by": "u_sabine"
}
```

| Feld | Regel |
|------|-------|
| `object_type` | `path \| lawn \| tree \| shrub \| building \| wall \| fence \| trellis \| water_source \| compost \| storage \| other` |
| `props` | typabhängiges Objekt, Pydantic-Discriminated-Union nach `object_type` (`TreeProps{species_label?, crown_radius_m, height_m?}`, `WaterSourceProps{water_source_kind, capacity_liters?, last_refilled_at?}`, `PathProps{surface ∈ {gravel, paving, bark, grass, other}}`, …) |
| `parent_location_key` | optional: Objekt liegt in einem Bereich (z. B. Weg im Gewächshaus); Containment wird geometrisch validiert |
| `off_site` | `bool = false`; `true` nimmt das Objekt von V-03 aus (Nachbargrundstück, §9.5) |

Edges: `has_garden_object` (sites → garden_objects). `belongs_to_tenant` wird um `garden_objects` erweitert.

### 20.5 Slot (bestehend, additiv)

```json
{
  "_key": "slot_b03_r2p05",
  "tenant_key": "t_garten_sabine",
  "slot_id": "BEET03_R2P05",
  "location_key": "loc_b03",
  "slot_role": "position",
  "geometry": { "kind": "point", "origin": [0.30, 0.90] },
  "capacity_plants": 1,
  "currently_occupied": true,
  "row_index": 2, "sequence": 11,
  "geometry_source": "layout", "container_volume_l": null, "sown_at": null, "archived_at": null,
  "planned_spacing_cm": 30,
  "created_at": "…", "updated_at": "…"
}
```

`position` (Rasterzelle) **entfällt** (O-01, §9.2a): Migration v0072 leitet daraus `geometry` ab und füllt `row_index`/`sequence`; danach wird das Feld aus Modell, Schema und Frontend entfernt (`geometry_source ∈ {editor, layout, migrated_grid}` dokumentiert die Herkunft). `pitch_m` (neu an Location, Standard 0,30) ist nur die Migrations-Annahme für Alt-Slots. `slot_role ∈ {position, row, zone}`; Standard `position`. Neu außerdem `container_volume_l` (Topfvolumen, W-016), `sown_at` (Direktsaat-Zustand, §11.3), `archived_at` (Slot eines abgeschlossenen Runs, GP-FR-055). Für `row`: `geometry.kind = polyline`; für `zone`: `polygon`.

### 20.6 PlantingRun / Entry (bestehend, additiv) und geplante Belegung

```json
{
  "_key": "run_2026_tom_b03",
  "name": "Tomaten Hochbeet 3 · 2026",
  "run_type": "monoculture",
  "status": "planned", "plan_role": "main_crop", "rotation_override_reason": null,
  "location_key": "loc_b03",
  "planned_quantity": 6,
  "planned_start_date": "2026-05-15",
  "source": "plan_editor",
  "entries": [
    {
      "_key": "entry_1", "species_key": "sp_solanum_lycopersicum", "cultivar_key": "cv_harzfeuer",
      "quantity": 6, "id_prefix": "TOM",
      "spacing_cm": 60, "row_spacing_cm": 80, "row_direction": "along_length", "edge_margin_along_cm": 30, "edge_margin_across_cm": 40, "depth_cm": 10, "depth_kind": "planting",
      "layout_strategy": "rows", "placement_hint": "interior"
    }
  ]
}
```

Edge `run_planned_at` (planting_runs → slots): `{ "entry_key": "entry_1", "planned_species_key": "sp_…", "sequence": 3, "planned_from": "2026-05-15", "planned_until": "2026-10-15", "planned_at": "…" }`.

### 20.7 PlantInstance (bestehend, unverändert) — Beispiel

```json
{
  "_key": "pi_tom_003",
  "instance_id": "TOM-003",
  "species_key": "sp_solanum_lycopersicum",
  "site_key": "site_7f3a", "location_key": "loc_b03", "slot_key": "slot_b03_r2p05",
  "planted_on": "2026-05-16", "removed_on": null,
  "current_phase_key": "phase_vegetative",
  "photo_refs": ["att_…"]
}
```

Die Position der Pflanze ist `Slot.geometry` ihres `slot_key` — kein zusätzliches Feld (D-03).

### 20.8 Auflösung der REQ-002-Felder

| REQ-002-Feld | REQ-053-Entsprechung | Umgang |
|--------------|----------------------|--------|
| `bed_width_cm`, `bed_length_cm` | `geometry.width_m/length_m` | nicht einführen |
| `bed_orientation` | abgeleitet aus `rotation_deg` + `north_angle_deg` | nicht einführen; GP-FR-017 |
| `bed_type` | `location_type_key` mit `LocationType.is_bed` | nicht einführen |
| `bed_rows`, `row_spacing_cm` | `PlantingRunEntry.layout_strategy = rows`, `row_spacing_cm`; Slots `slot_role = row` | nicht einführen (Reihen hängen an der Pflanzung, nicht am Beet) |
| `dimensions: (l, b, h)` (im Code) | `geometry` + `height_m` | **Entfernt in Welle 1** (O-02): Migration v0072 übernimmt `(l, b)` als `rect`-Geometrie mit `origin = (0,0)` für Locations ohne Geometrie und `h` als `height_m`; Leser im Code werden auf `geometry`/`height_m` umgestellt (Issue 56). |
| `Slot.dimensions_cm` (REQ-002) | `Slot.geometry` | nicht einführen |
| `Slot.position: (row, col)` (im Code) | `Slot.geometry` + `row_index`/`sequence` | **Entfernt in Welle 1** (O-01, §9.2a) |

### 20.9 Task (bestehend, additiv)

Neue Felder: `suggested: bool = false`, `suggestion_reason: str | null`. Neue `TaskCategory`-Werte: §12.1. `entity_type = "location"` wird im Schema als zulässiger Wert dokumentiert (die Edge erlaubt ihn bereits).

```json
{
  "_key": "task_mulch_b03",
  "name": "Hochbeet 3 mulchen",
  "category": "mulching",
  "entity_type": "location", "entity_key": "loc_b03",
  "status": "pending", "priority": "medium",
  "due_date": "2026-06-01",
  "recurrence_rule": "FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=1",
  "origin": "user", "suggested": false,
  "checklist": [], "photo_refs": []
}
```

### 20.10 CareEvent (neu, Collection `care_events`)

```json
{
  "_key": "ce_8d2e",
  "tenant_key": "t_garten_sabine",
  "site_key": "site_7f3a",
  "location_key": "loc_b03",
  "plant_keys": ["pi_tom_003", "pi_tom_004"],
  "category": "feeding",
  "summary": "Tomaten mit Brennnesseljauche gedüngt",
  "performed_at": "2026-06-14T18:30:00Z",
  "performed_by_user_key": "u_sabine",
  "performed_for_user_key": null, "performed_by_label": null,
  "trigger": "task",
  "task_key": "task_feed_b03_w24",
  "reason": "Blattaufhellung, 2 Wochen seit letzter Gabe",
  "product_ref": { "kind": "fertilizer", "key": "fert_nettle_tea" },
  "product_label": null,
  "quantity": 2.0, "unit": "l_per_m2", "quantity_total": 4.0, "quantity_total_unit": "l",
  "material": null,
  "measurements": null,
  "observed_outcome": null, "outcome_rating": "unknown",
  "photo_refs": ["att_…"],
  "source_ref": { "collection": "feeding_events", "key": "fe_…" },
  "supersedes_key": null, "superseded_by_key": null,
  "voided_at": null, "voided_by": null, "void_reason": null,
  "redacted_at": null, "redacted_by": null, "redaction_reason": null,
  "created_at": "2026-06-14T18:31:02Z", "created_by": "u_sabine"
}
```

| Feld | Regel |
|------|-------|
| `category` | Vereinigung aus `TaskCategory` (§12.1) + protokollspezifische Werte `note`, `observation`, `soil_analysis`, `bed_status_change`, `position_corrected`, `planting`, `removal`, `clearing` |
| `trigger` | `task \| reminder \| suggestion \| manual \| observation \| backfill \| system`; der Client darf nur `manual`/`observation` setzen, alle anderen setzt der Server (SR-009) |
| `source_ref` | optionaler Zeiger auf `watering_events`, `feeding_events`, `treatment_applications`, `harvest_batches`, `care_confirmations` |
| `measurements` | nur bei `soil_analysis`/`ec_check`: Liste `{parameter ∈ {ph, ec, n_min, p, k, mg, humus, caco3, moisture}, value, unit, extraction_method?, sample_depth_cm?, source}` (§15.1) |
| Unveränderlich nach Anlage | alles außer `superseded_by_key`, `voided_at`, `voided_by`, `void_reason` und der Redaktion (GP-FR-109) |

Edges: `care_event_at` (care_events → locations), `care_event_for` — **bestehende** Edge (care_confirmations → plant_instances) wird um `care_events` als Quelle erweitert, `task_logged_as` (tasks → care_events). Indizes: `(tenant_key, location_key, performed_at desc)`, `(tenant_key, performed_at desc)`, `(task_key)`, `(source_ref.collection, source_ref.key)` unique-sparse.

### 20.11 IrrigationZone (neu, Collection `irrigation_zones`)

```json
{
  "_key": "zone_sued",
  "tenant_key": "t_garten_sabine", "site_key": "site_7f3a",
  "name": "Südzone (Tropfschlauch)",
  "irrigation_type": "drip",
  "water_source_key": "go_91ab",
  "actuator_key": null,
  "flow_rate_l_per_min": null, "flow_rate_source": "manual", "application_efficiency": 0.9, "flow_rate_ha_entity_id": null,
  "color": "#2E7D32",
  "schedule_hint": "morgens, 20 min",
  "created_at": "…", "updated_at": "…"
}
```

Edges: `has_irrigation_zone` (sites → irrigation_zones), `zone_covers` (irrigation_zones → locations), `zone_supplied_by` (irrigation_zones → garden_objects), `zone_actuated_by` (irrigation_zones → actuators).

### 20.12 BedTemplate (neu, SHOULD, Collection `bed_templates`)

`{ name, tenant_key | null (global), location_type_key, default_geometry, height_m?, default_layout {row_spacing_cm?, spacing_cm?}, soil_profile_defaults?, recurring_task_templates[] (→ task_templates) }`.

### 20.13 Zeitstempel, IDs, Historisierung

| Aspekt | Regel |
|--------|-------|
| IDs | ArangoDB `_key`, serverseitig vergeben; Client sendet `temp_key` für neu erzeugte Objekte im Batch und erhält die Zuordnung zurück |
| Zeitstempel | `created_at`, `updated_at` UTC ISO-8601 (Bestand); `performed_at` in `care_events` ebenfalls UTC, UI zeigt Site-Zeitzone |
| Plan-Historie | `Site.plan.plan_revision` monoton (nur Struktur, GP-NFR-007); **keine** Geometrie-Versionstabelle im MVP (O-03). **Pflicht-Audit (SR-011):** jede löschende oder strukturverändernde Operation (Batch-`delete`, `DELETE`-Endpunkte, `bed_status = retired`, Import `replace`, Redaktion) schreibt atomar in derselben Transaktion `garden_plan_audit {site_key, revision, user_key, op, entity, key, at, summary}` (Collection, **MUST**); vor Import `replace` wird ein Snapshot geschrieben (GP-FR-148 für diesen Pfad MUST) |
| Pflege-Historie | append-only mit Supersede/Void (§13.3) |
| Tenant | alle neuen Dokumente tragen `tenant_key`. **Entschieden (SR-022):** v0072 stempelt `tenant_key` auch auf `locations` und `slots` (aus `site.tenant_key`) und legt Indizes an; Repositories filtern zusätzlich darauf; das Site-Anker-Prädikat (§22.3) bleibt als Defense-in-Depth. Das bisherige Modell „Location/Slot ohne tenant_key" ist damit aufgehoben |

### 20.14 Graph-Änderungen (Zusammenfassung für v0072)

Neue Collections: `garden_objects`, `care_events`, `irrigation_zones`, `bed_templates` (SHOULD), `garden_plan_audit` (MUST).
Neue Edge-Definitionen: `has_garden_object`, `run_planned_at`, `care_event_at`, `task_logged_as`, `has_irrigation_zone`, `zone_covers`, `zone_supplied_by`, `zone_actuated_by`.
Erweiterte Edge-Definitionen: `belongs_to_tenant` (+ `garden_objects`, `care_events`, `irrigation_zones`), `care_event_for` (+ `care_events` als from), `has_task` (+ `garden_objects` als from).
Neue Indizes: `locations(tenant_key)`, `slots(tenant_key)`, `locations(site_key, bed_status)`, `garden_objects(site_key, object_type)`, `slots(location_key, slot_role)`, `care_events` (§20.10).

---

## 21. API

Alle Pfade unter `/api/v1/t/{tenant_slug}`. Schemas in `api/v1/garden_plan/schemas.py` (v1). Fehler nach NFR-006 (`{code, message, details}`), Codes in §22.

### 21.1 Plan (Site-Ebene)

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-001 | `GET /sites/{key}/plan` | Vollständiger Plan (§20.2–20.5 + Pflanzen-Kurzinfo `{key, instance_id, species_key, phase_key, slot_key}` + Task-Zähler je Location + Zonen). Query: `include=plants,tasks,zones` (Standard alle), `as_of=YYYY-MM-DD` (SHOULD: historischer Stand der Pflanzen) | Alle Rollen |
| GP-API-002 | `PUT /sites/{key}/plan/boundary` | Gartengrenze + `north_angle_deg`, `default_grid_m`; legt `plan` an, wenn fehlend | Ab Gärtner |
| GP-API-003 | `POST /sites/{key}/plan/batch` | Transaktionale Operationsliste (§21.3). **Abschließende Op-Liste** `create_location`, `create_garden_object`, `update_geometry`, `update_fields`, `delete`, `set_boundary`, `set_locked`, `set_z_order`; **jede Operation wird einzeln gegen §21.8 geprüft, vor der Domain-Validierung** (SR-001): `delete` auf `location`/`garden_object` verlangt Leitung; enthält ein Batch eine Operation über der Rolle des Aufrufers, wird er komplett mit 403 `batch.operation_forbidden {op_index}` abgewiesen. Slot-Operationen laufen **nicht** über den Plan-Batch (GP-API-014/015, außerhalb der Revision). | Ab Gärtner (Lesen der Antwort: Alle) |
| GP-API-004 | `GET /sites/{key}/plan/export` | JSON-Sicherung (`schema_version`, alle Plan-Objekte, ohne Pflanzen/Tasks/Events) | Alle Rollen (`Action.EXPORT`) |
| GP-API-005 | `POST /sites/{key}/plan/import` | Wiederherstellung; Modus `replace` (schreibt Snapshot, löscht vorhandene Geometrien nur für Beete **ohne** aktive Pflanzen — `force` hebt die Leer-Bedingung auf, V-09 gilt immer) oder `merge` (fügt hinzu, Keys werden immer neu vergeben). `dry_run=true` liefert `{would_create, would_update, would_delete, dropped_references[], errors}`. Beide Modi: **Nur Leitung** (SR-010). | Nur Leitung |
| GP-API-006 | `GET /sites/{key}/plan/render.svg` | Serverseitiges SVG (für PDF und Download), Query `scale`, `layers`, `locale` | Alle Rollen |
| GP-API-007 | `GET /print/garden-plan/{site_key}` | PDF (REQ-032-Muster), Query `paper=a4\|a3`, `orientation`, `scale=auto\|1:50\|1:100\|1:200`, `layers`, `locale` | Alle Rollen |
| GP-API-008 | `GET /sites/{key}/plan/audit` | Plan-Änderungsprotokoll (SHOULD) | Alle Rollen |

### 21.2 Locations / GardenObjects / Slots (Einzelressourcen)

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-010 | `PATCH /locations/{key}` (bestehendes `PUT` bleibt) | Teilupdate inkl. `geometry`, `soil_profile`, `bed_status`, `sun_exposure`, `irrigation_zone_key`, `notes`, `locked`, `z_order`; Geometrie-Update außerhalb des Batch erhöht ebenfalls `plan_revision` | Ab Gärtner |
| GP-API-011 | `GET /locations?site_key=&is_bed=true&bed_status=` | Beetliste mit Zählern (`active_plant_count`, `open_task_count`, `next_due_at`) | Alle Rollen |
| GP-API-012 | `GET /locations/{key}/summary` | Kopfdaten der Beetansicht (GP-FR-047) | Alle Rollen |
| GP-API-013 | `GET\|POST /sites/{key}/garden-objects`, `GET\|PATCH\|DELETE /garden-objects/{key}` | Einzel-CRUD (Batch ist der Hauptweg) | Alle / Ab Gärtner / Nur Leitung (Löschen) |
| GP-API-014 | `PATCH /slots/{key}` | `geometry`, `slot_role`, `capacity_plants`; löst `adjacency_recompute` aus | Ab Gärtner |
| GP-API-015 | `POST /locations/{key}/slots/batch` | Slots eines Beets ersetzen/ergänzen (`mode = replace_unoccupied \| append`), transaktional | Ab Gärtner |
| GP-API-016 | `POST /locations/{key}/planting-layout/preview` | `{entry: {spacing_cm, row_spacing_cm, edge_margin_cm, layout_strategy, max_count?}}` → `{slots: [SlotGeometry], count, capacity_max}` ohne Persistenz; Obergrenze 2 000 Positionen (GP-FR-062) | Alle Rollen |
| GP-API-017 | `POST /locations/{key}/quick-planting` | Feldmodus-Kurzpfad: Run anlegen + Slots + Pflanzen in einer Transaktion (GP-UX-027); `quantity` ≤ 500; läuft außerhalb der Plan-Revision | Ab Gärtner |
| GP-API-018 | `POST /locations/{key}/status` | `bed_status`-Wechsel mit `reason` (schreibt `care_event`) | Ab Gärtner |
| GP-API-019 | `POST /locations/{key}/clear` | Beet räumen (GP-FR-055): `{termination_type, reason?, harvested_batch?}` → beendet aktive Runs/Pflanzen, archiviert Slots, schreibt `care_event(clearing)` | Ab Gärtner |

### 21.3 Batch-Vertrag (GP-API-003)

Request:
```json
{
  "expected_revision": 42,
  "operations": [
    { "op": "create_location", "temp_key": "tmp1", "data": { "name": "Beet 6", "location_type_key": "bed", "parent_location_key": "loc_nutzgarten", "geometry": { "kind": "rect", "origin": [4,1], "width_m": 2, "length_m": 1, "rotation_deg": 0 } } },
    { "op": "update_geometry", "entity": "location", "key": "loc_b03", "geometry": { "kind": "rect", "origin": [1,1.5], "width_m": 2, "length_m": 1, "rotation_deg": 90 } },
    { "op": "create_garden_object", "temp_key": "tmp2", "data": { "object_type": "path", "geometry": { "kind": "polyline", "points": [[0,3],[10,3]], "width_m": 0.6 } } },
    { "op": "delete", "entity": "garden_object", "key": "go_old" }
  ]
}
```
Response 200:
```json
{ "plan_revision": 43, "key_map": { "tmp1": "loc_a91c", "tmp2": "go_77f0" }, "updated": ["loc_b03"], "deleted": ["go_old"], "derived": { "loc_b03": { "area_m2": 2.0, "bbox": [1.0,1.5,2.0,3.5] }, "loc_a91c": { "area_m2": 2.0, "bbox": [4,1,6,2] } } }
```
Fehler: 409 `plan.revision_conflict` `{current_revision, changed_by, changed_at}`; 422 `validation_error` mit `details[{op_index, field, code}]` — die gesamte Transaktion wird verworfen. Limit: 500 Operationen je Request.

### 21.4 Pflanzung

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-020 | `POST /planting-runs` (bestehend, erweitert) | Entries mit Layout-Feldern; bei `location_key` eines Beets mit Geometrie und `layout_strategy != free` werden Slots + `run_planned_at` erzeugt | Ab Gärtner |
| GP-API-021 | `POST /planting-runs/{key}/plan-slots` | Geplante Belegung setzen/ersetzen (`{entry_key, slot_keys[]}`), für `free`-Layouts und Korrekturen; `slot_keys` ⊆ Slots von `run.location_key` (GP-NFR-058) | Ab Gärtner |
| GP-API-022 | `DELETE /planting-runs/{key}/plan-slots/{slot_key}` | Reservierung freigeben | Ab Gärtner, solange der Run `planned` ist; sonst Nur Leitung (SR-010) |
| GP-API-023 | `POST /planting-runs/{key}/create-plants` (bestehend) | `assign_to_slots = true` nutzt `run_planned_at` in `sequence`-Reihenfolge | Ab Gärtner |
| GP-API-024 | `GET /locations/{key}/plantings?state=planned\|active\|harvested\|historical&year=` | Pflanzungen eines Beets nach Zustand (§11.3) | Alle Rollen |
| GP-API-025 | `POST /locations/{key}/validate-planting` | Beet-Variante von REQ-013/028-Validierung: Fruchtfolge + Nachbarn, nur Hinweise (MUST, GP-FR-131/132) | Alle Rollen |

### 21.5 Pflege und Historie

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-030 | `GET /tasks/queue?location_key=&include_children=true` (bestehend, Filter neu) | Aufgaben eines Beets/Bereichs | Alle Rollen |
| GP-API-031 | `POST /tasks/{key}/complete` (bestehend, Body erweitert) | `{performed_at?, notes?, photo_refs?, plant_keys?, reason?, product_ref?, product_label?, quantity?, unit?, material?, measurements?, observed_outcome?, outcome_rating?}` → schreibt `care_event` + Fachereignis atomar | Ab Gärtner |
| GP-API-032 | `POST /tasks/batch/status` (bestehend, Body erweitert) | gleiche Fachfelder für n Tasks (Gießdienst) | Ab Gärtner |
| GP-API-033 | `POST /care-events` | Protokoll ohne Task (GP-FR-090); Body ohne `trigger`-Werte außer `manual`/`observation`, ohne `created_by`/`source_ref` (serverseitig, SR-009) | Ab Gärtner |
| GP-API-034 | `GET /care-events?location_key=&plant_key=&category=&from=&to=&performed_by=&include_superseded=false&format=json\|csv` | Historie (mandantenweit oder je Beet). Filter `performed_by` für **alle Rollen** (Betreiberentscheid SR-020; Hinweis: in Gemeinschaftsgärten ermöglicht das Aktivitätsprofile — bei der DSFA nach REQ-025 zu berücksichtigen); `performed_by` erscheint als Anzeigename oder „anonymisiert", nie als Nutzer-Key | Alle Rollen |
| GP-API-035 | `GET /care-events/{key}` | Einzelereignis inkl. Supersede-Kette | Alle Rollen |
| GP-API-036 | `POST /care-events/{key}/supersede` | Korrektur (neuer Eintrag, alter bleibt) | Ab Gärtner (eigene = `created_by` ist der Aufrufer), Nur Leitung (fremde); Prädikat im Service |
| GP-API-037 | `POST /care-events/{key}/void` | Storno mit Grund | Nur Leitung |
| GP-API-038 | `GET /locations/{key}/history?from=&to=` | Kombinierte Historie (care_events + Pflanzungsereignisse), paginiert | Alle Rollen |
| GP-API-039 | `GET /locations/{key}/rotation?years=5` | Zeitstrahl Familie/Spezies je Jahr (GP-FR-103) | Alle Rollen |
| GP-API-040 | `POST /tasks/{key}/accept-suggestion`, `POST /tasks/{key}/dismiss-suggestion` | Vorschläge (SHOULD) | Ab Gärtner |
| GP-API-041 | `POST /care-events/{key}/redact` | Redaktion (GP-FR-109) `{reason}`; wirkt auf die Supersede-Kette | Nur Leitung |

### 21.6 Bewässerungszonen (SHOULD)

| ID | Methode & Pfad | Rolle |
|----|----------------|-------|
| GP-API-050 | `GET\|POST /sites/{key}/irrigation-zones`, `GET\|PATCH\|DELETE /irrigation-zones/{key}` | Alle / Ab Gärtner / Nur Leitung; Felder `actuator_key`, `flow_rate_ha_entity_id`: nur Technik (SR-014) |
| GP-API-051 | `PUT /irrigation-zones/{key}/locations` `{location_keys[]}` | Ab Gärtner |
| GP-API-052 | `GET /irrigation-zones/{key}/status` → `{last_watering, next_planned, demand_liters_today, consumption_liters_30d}` | Alle Rollen |
| GP-API-053 | `POST /irrigation-zones/{key}/log-watering` `{volume_liters, allocation: by_area\|equal, performed_at?}` → n `care_events` | Ab Gärtner |

### 21.7 Vorlagen (SHOULD)

`GET /bed-templates` (global + tenant), `POST /bed-templates`, `POST /sites/{key}/plan/place-template` `{template_key, origin, rotation_deg}` → Batch-Response.

### 21.8 Autorisierung

Standardregel: Lesen „Alle Rollen", Anlegen/Ändern „Ab Gärtner", Löschen „Nur Leitung" (REQ-049 §3.3). `ResourceType` erhält `garden_object`, `care_event`, `irrigation_zone`, `bed_template`; Plan-Batch nutzt `ResourceType.LOCATION` + `Action.UPDATE` als Eingangs-Gate **und** eine Rollenprüfung je Operation im Service (SR-001). Datenabhängige Regeln dieser Tabelle (belegt/unbelegt, eigene/fremde, `planned`) setzt der **Service** durch (`require_permission` ist heute rollen-, nicht ressourcenabhängig); je Zeile und Rolle gibt es einen Negativtest (SR-010).

| Ressource | Lesen | Anlegen | Ändern | Löschen | Sonderaktionen |
|-----------|-------|---------|--------|---------|----------------|
| Gartenplan (Grenze, Batch) | Alle Rollen | Ab Gärtner | Ab Gärtner | — | Batch-`delete`: Nur Leitung (je Op geprüft); Import `merge`/`replace`: Nur Leitung; Export: Alle Rollen |
| Beet (Location) | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Status `retired`: Nur Leitung |
| Gartenobjekt | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | — |
| Slot (Pflanzposition) | Alle Rollen | Ab Gärtner | Ab Gärtner | Ab Gärtner (unbelegt, keine aktive Reservierung), Nur Leitung (belegt) — Prädikat im Service, nicht im Router-Gate | Position korrigieren: Ab Gärtner |
| Pflanzdurchlauf / geplante Belegung | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung (Run); Reservierung: Ab Gärtner solange `planned` | Beet räumen: Ab Gärtner |
| Pflegeaufgabe | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Erledigen: Ab Gärtner |
| Pflegeereignis | Alle Rollen | Ab Gärtner | Eigene (Supersede), Nur Leitung (fremde) | — (Void, Redaktion: Nur Leitung) | Filter nach Person: Alle Rollen (SR-020) |
| Bewässerungszone | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Aktor-/HA-Kopplung (`actuator_key`, `flow_rate_ha_entity_id`): Technik; Aktor-Befehl: Rolle nach REQ-018 (Bedienen), nicht Technik (REQ-049 §2) |
| Beetvorlage (tenant) | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Globale Vorlagen: Plattform-Admin |

Die Standort-Zuweisung (`location_assignments`) bleibt Koordination ohne Schreibgrenze (REQ-049 §3.5). Modul-Sichtbarkeit (O-15, entschieden): Modul `garden_planner` in REQ-042 registrieren; Navigation unter „Standorte" (Plan als Unterpunkt der Site, kein eigener Hauptmenüpunkt, REQ-021); im Light-Modus (REQ-027) verfügbar.

---

## 22. Validierung

### 22.1 Ebenen

| Ebene | Prüft | Reaktion |
|-------|-------|----------|
| **UI** | Snap, Mindestgrößen beim Zeichnen, Containment-Vorschau (rote Markierung), Pflichtfelder, Zahlenbereiche | sofort, verhindert Operation oder markiert |
| **API (Pydantic)** | Typen, Bereiche, Enum-Werte, Punktzahl, Rotation, Operationslimit | 422 `validation_error` |
| **Domain (Service/Calculator)** | Geometrie einfach, Containment, Überlappung, Pflanzabstände, Zustandsübergänge, zeitliche Plausibilität, Tenant-Anker | 409/422 mit Fachcode |
| **Datenbank** | Unique-Indizes (`slot_id` je Location, `source_ref`), Edge-Definitionen (erlaubte Collections), Transaktion | Transaktion bricht ab; Fehler wird in 409/500 übersetzt |

**Feste Prüfreihenfolge (SR-013):** (1) Authentifizierung → (2) Tenant-Anker und Auflösung aller referenzierten Keys (§22.3, GP-NFR-058) → (3) Rolle je Operation (§21.8) → (4) Pydantic → (5) Domain-Validierung → (6) Revisionsprüfung in der Transaktion. Ein fremder oder fehlender Kontext liefert immer 404 ohne Body-Details; `changed_by` im 409 ist der Anzeigename, nie der Nutzer-Key. So kann weder ein 409 die Existenz fremder Sites noch ein `outside_parent` fremde Geometrie verraten.

### 22.2 Regeln

| Regel | Ebene | Code | Inhalt |
|-------|-------|------|--------|
| V-01 | API | `geometry.invalid` | Maße > 0, Punkte im zulässigen Bereich (0 ≤ x,y ≤ 1 000 m), Rotation 0–359,999, Polygon ≥ 3 Punkte, ≤ 200 Punkte |
| V-02 | Domain | `geometry.self_intersecting` | Polygon ist einfach (Segment-Schnitt-Test, O(n²) bei n ≤ 200 akzeptabel) |
| V-03 | Domain | `geometry.outside_parent` | Location/GardenObject mit `parent_location_key` liegt vollständig in der Eltern-Geometrie (Punkt-in-Polygon aller Eckpunkte; für rotierte Rects über die 4 transformierten Ecken). Ohne Eltern: innerhalb der Gartengrenze, falls gesetzt. Toleranz 1 cm. |
| V-04 | Domain | `slot.outside_bed` | Slot-Geometrie liegt innerhalb der Beet-Geometrie (Beet-Rahmen), Randabstand als **Inset** zur Kante — **die geforderte Regel „Pflanzen dürfen nicht außerhalb eines Beetes liegen"** |
| V-05 | Domain | `bed.overlap` | Zwei Beete derselben Eltern-Location dürfen sich nicht überlappen (Bounding-Box-Vortest, dann Polygon-Schnitt über Separating-Axis für konvexe bzw. Kantentest für konkave Formen). Beet ↔ Gartenobjekt darf überlappen (Weg unter Hochbeet) — nur Warnung in der UI. |
| V-06 | Domain | `slot.overlap` | Slot-Zonen (`zone`) innerhalb eines Beets dürfen sich nicht überlappen — geprüft nur gegen **aktive und geplante** Slots (`archived_at = null`, F-02); Positionen (`point`) haben keinen Überlappungsbegriff |
| V-07 | Domain (Hinweis) | `planting.spacing_below_minimum` | Abstand zweier geplanter Positionen < `spacing_cm` → **Hinweis** in Preview-Antwort (`warnings[]`), kein Fehler (GP-FR-072) |
| V-08 | Domain | `slot.already_planned` | Slot hat eine Reservierung mit **überlappendem Zeitfenster** oder eine aktive Pflanze, deren erwartetes Ende nach `planned_from` liegt (GP-FR-065) |
| V-09 | Domain | `location.has_active_plants` | Löschen/`retired` eines Beets mit Pflanzen `removed_on = null` verweigert |
| V-10 | Domain | `bed_status.invalid_transition` | nur Übergänge aus §7.4 |
| V-11 | Domain | `care_event.performed_in_future` / `care_event.too_old` | `performed_at ≤ now + 5 min` und `≥ now − 365 d` (Backfill-Trigger ausgenommen) |
| V-12 | Domain | `care_event.immutable` | Änderung an bestehendem Ereignis außer Supersede/Void |
| V-13 | Domain | `care_event.sequence` | `supersedes_key` muss selbes Beet + nicht bereits superseded sein (keine Verzweigung) |
| V-14 | Domain | `plan.revision_conflict` | `expected_revision != plan_revision` |
| V-15 | Domain | `tenant.mismatch` → 404 | Site/Location/Slot gehört nicht zum aktiven Tenant (bestehendes 404-Muster) |
| V-16 | Domain | `garden_object.not_plantable` | Run/Task/Slot auf ein GardenObject |
| V-17 | API | `batch.too_many_operations` | > 500 |
| V-18 | Domain | `reference.not_found` | Ein in Body/Import referenzierter Key ist nicht auflösbar oder gehört nicht zum Tenant (GP-NFR-058) — ein Text für beides |
| V-19 | Domain | `boundary.shrinks_below_objects` | Neue Gartengrenze lässt bestehende Objekte außerhalb → Fehler mit Liste der Keys (Nutzer verschiebt zuerst) |
| V-20 | DB | unique `slots(location_key, slot_id)` | bestehende Regel |
| V-21 | API | `batch.operation_forbidden` | Operation über der Rolle des Aufrufers (403, SR-001) |
| V-22 | API/Domain | `plan.quota_exceeded`, `layout.too_many_positions`, `batch.too_complex` | Quoten (GP-NFR-017), Layout-Obergrenze (GP-FR-062), Komplexitäts-/Zeitbudget (GP-NFR-013) |
| V-23 | Domain | `tent.photoperiod_conflict` | Hinweis (kein Fehler): Pflanzen verschiedener Photoperiode-Phasen in einer Zelt-Location (SHOULD) |

### 22.3 Mandanten-Anker und Referenzauflösung

Mit v0072 tragen auch Locations und Slots `tenant_key` (SR-022); Repositories filtern darauf. Zusätzlich gilt als Defense-in-Depth das Site-Anker-Prädikat — und zwar so, dass `site_key` **nie aus dem Request stammt** (SR-002):

| Regel | Inhalt |
|-------|--------|
| T-01 | `site_key` wird **immer aus dem gespeicherten Dokument** abgeleitet: Location → `site_key`; Slot → `location_key` → `site_key`; GardenObject/Zone/CareEvent → `site_key`. Request-Felder mit `site_key` werden ignoriert. |
| T-02 | Für Endpunkte mit Site im Pfad gilt `resource.site_key == path.site_key`, sonst 404. |
| T-03 | Im Batch und im Import wird jede referenzierte Location bzw. jeder Slot (einschließlich `parent_location_key`) **vor** jeder Geometrie- oder Containment-Prüfung aufgelöst und muss zur Pfad-Site gehören. |
| T-04 | Jede Service-Methode nimmt `tenant_key` keyword-only ohne Default und prüft `site.tenant_key == tenant_key` vor der ersten Schreib- oder Rechenoperation (Prädikat im Service, nicht im Router — Memory „Guard opt-in am Aufrufort"). |

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-058 | MUST | **Referenzauflösung (SR-003):** Jeder Key in einem Request-Body oder Import wird serverseitig gegen den aktiven Tenant aufgelöst; globale Stammdaten mit `tenant_key = null` sind nur für `species`, `cultivar`, `fertilizer`, `substrate`, `bed_template`, `location_type` zulässig. Teilmengenregeln: `care_events.plant_keys` ⊆ Pflanzen mit `location_key` im Teilbaum des Event-Beets; `slot_keys` (GP-API-021) ⊆ Slots von `run.location_key`; Zone `location_keys` ⊆ Locations der Zone-Site; `water_source_key` = GardenObject `water_source` derselben Site; `actuator_key` = Aktor des Tenants an einer Location derselben Site; `photo_refs` = Attachments des Tenants, die der Aufrufer hochgeladen hat oder die dem Zielobjekt zugeordnet sind; `supersedes_key` = Event desselben Tenants und Beets; `source_ref` nur serverseitig; Task-Keys in `tasks/batch/*` einzeln tenant-geprüft, ein fremder Key lässt den Batch mit 404 scheitern. Ungültige Referenz → 422 `reference.not_found` ohne Unterscheidung fremd/fehlt. Negativtest je Feld (GP-ACC-041). |

## 23. Import und Export

| ID | Prio | Format | Inhalt | Richtung | MVP |
|----|------|--------|--------|----------|-----|
| GP-FR-140 | MUST | **JSON** (`schema_version: "1"`) | Site-Plan, Locations (Beet-Felder, Geometrie, Bodenprofil), GardenObjects, Slots, Zonen, Vorlagen-Referenzen; **keine** Pflanzen, Tasks, Ereignisse, Fotos | Export | ja |
| GP-FR-141 | SHOULD | JSON | Import `merge`/`replace` (GP-API-005) mit Vorab-Prüfbericht (`dry_run=true`). **Grenzen (SR-018):** Quoten aus GP-NFR-017, ≤ 10 Ebenen Verschachtelung, alle V-Regeln und GP-NFR-058; interne Verweise über eine Import-lokale Key-Map umgeschrieben, externe gegen den Tenant aufgelöst oder auf `null` gesetzt und als `dropped_references[]` berichtet; `flow_rate_ha_entity_id` und `actuator_key` werden beim Import **immer** verworfen (Neukopplung durch Technik). | Import | nein |
| GP-FR-142 | MUST | **PDF** | Maßstäblicher Plan: Standard **A4 quer, Maßstab automatisch** (O-12); Stufen **1:20, 1:25, 1:50, 1:75, 1:100, 1:125, 1:150, 1:200, 1:250, 1:300, 1:400, 1:500** (F-15: feinere Stufen, damit ein 28 × 20-m-Garten auf 1:150 statt 1:200 fällt); A3 wird automatisch vorgeschlagen, wenn A4 unter 1:200 fiele; Ebenenwahl für den Druck; Maßstabsleiste, Nordpfeil, Legende, Titelblock (Garten, Datum, Revision), Beetbeschriftungen; Tagged PDF, DE/EN (REQ-032 NFR). **Standardmäßig ohne personenbezogene Angaben** (SR-024): keine Mitgliedernamen, Zuweisungen, Notizen, GPS-Koordinaten, `*_by`-Felder; „Zuweisungen anzeigen" ist eine ausdrückliche Option. Vorschau mit Maßstab vor dem Download. Optional zweite Seite: Beetliste. | Export | ja |
| GP-FR-143 | MUST | **SVG** | Serverseitig (GP-API-006), Einheit mm (`viewBox` in mm, 1 m = 1 000 Einheiten), Layer als `<g id="layer-…">`, Objekt-IDs als `data-key` | Export | ja |
| GP-FR-144 | SHOULD | **PNG** | Clientseitig aus dem SVG-DOM in 1×/2×/4× Auflösung; Wasserzeichen „Kamerplanter · Datum" | Export | nein |
| GP-FR-145 | SHOULD | **CSV** | Beetliste (`GET /locations?…&format=csv`): Name, Typ, Fläche, Status, Bodenart, Zone, aktive Pflanzen; Historie (GP-FR-104) (gleiche CSV-Härtung wie GP-FR-104) | Export | nein |
| GP-FR-146 | COULD | **GeoJSON** | Nur wenn `gps_coordinates` + `north_angle_deg` gesetzt: affine Transformation Plan-Meter → WGS84 (lokale ENU-Näherung, ausreichend für < 1 km); `FeatureCollection` mit `properties {kind, key, name, location_type}`; Import GeoJSON WON'T (Georeferenzierung nicht Ziel); Export der WGS84-Koordinaten (= Wohnort) **nur Leitung** (SR-024) | Export | nein |
| GP-FR-147 | MUST | JSON | Sicherung und Wiederherstellung: JSON-Export ist in der DSGVO-Datenexport-Kaskade (`DataExportEngine`, REQ-025) enthalten; Import in dieselbe Site stellt Geometrien vollständig wieder her (AC in §30) | beide | ja (Export), SHOULD (Import) |
| GP-FR-148 | SHOULD (vor Import `replace`: MUST, SR-011) | JSON | Automatischer Snapshot je Saison (`garden_plan_snapshots`, 1. Januar / vor `replace`-Import) mit Wiederherstellung | beide | nein |

---

## 24. Accessibility (WCAG 2.1 AA, UI-NFR-002)

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-NFR-020 | MUST | Jedes Plan-Objekt ist ein fokussierbares `<g role="button" tabindex="0" aria-label="Hochbeet 3, Beet, 2 × 1 m, 6 Pflanzen, 2 offene Aufgaben">`; die DOM-Reihenfolge folgt Zeile → Spalte nach `bbox` (R-026). | ja |
| GP-NFR-021 | MUST | Vollständige Tastatur-Alternative für jede Drag-Interaktion (R-024): Verschieben per Pfeiltasten, Skalieren/Drehen über das Eigenschaftenpanel, Polygon-Punkte über eine Punktliste im Panel mit x/y-Feldern. Griffe nur für die Maus: `tabindex="-1"` (R-025). | ja |
| GP-NFR-022 | MUST | `aria-live="polite"`-Region meldet Ergebnis jeder Operation („Hochbeet 3 verschoben nach x 1,0 m, y 1,5 m", „Gespeichert, Revision 43", „Konflikt") (R-027). | ja |
| GP-NFR-023 | MUST | **Alternative Darstellung des Plans:** Schalter „Als Liste" zeigt dieselben Objekte als hierarchische Liste (Bereich → Beet → Pflanzen) mit allen Werten des Panels; alle Aktionen (außer Freihandzeichnen) sind dort ausführbar. Die Liste ist zugleich die Screenreader-Hauptnavigation. | ja |
| GP-NFR-024 | MUST | Kontraste: Objektfüllung gegen Hintergrund ≥ 3:1 (R-017), Text ≥ 4,5:1, Fokusring 2 px mit ≥ 3:1 (R-005); Information nie nur über Farbe (R-018): Beettyp über Muster + Icon, Phase über Icon + Text im Tooltip/Liste. | ja |
| GP-NFR-025 | MUST | 200 % Browser-Zoom ohne Funktionsverlust (R-019): Werkzeugleiste umbricht, Panel wird Bottom Sheet. | ja |
| GP-NFR-026 | MUST | `prefers-reduced-motion`: keine Zoom-Animation, kein Geisterobjekt-Fading (R-022). | ja |
| GP-NFR-027 | MUST | Touch-Bedienung ohne Hover (GP-UX-025), Ziele ≥ 48 px, im Feldmodus ≥ 64 px. | ja |
| GP-NFR-028 | SHOULD | `vitest-axe` auf Editor und Beetansicht; E2E-a11y-Lauf (bestehende Nightly-Kontrolle) enthält den Plan. | ja |
| GP-NFR-029 | SHOULD | SVG-Export trägt `<title>`/`<desc>` je Objekt; PDF ist Tagged PDF mit Lesereihenfolge (REQ-032). | nein |

---

## 25. Performance

### 25.1 Größenklassen (Begründung: Zielgruppen-Betriebsgrößen aus `spec/target-audiences/`)

| Klasse | Beispiel | Beete | Gartenobjekte | Pflanzen (aktiv) | Slots | Ereignisse/Jahr |
|--------|----------|-------|---------------|------------------|-------|-----------------|
| **klein** | Balkon, Kleingarten (ZG-002 untere Grenze, UZG-001) | ≤ 5 | ≤ 10 | ≤ 50 | ≤ 60 | ≤ 500 |
| **mittel** | Gemüsegarten 60–200 m² (ZG-002) | ≤ 20 | ≤ 40 | ≤ 300 | ≤ 400 | ≤ 3 000 |
| **groß** | Gemeinschaftsgarten 30 Parzellen, Gewächshausbetrieb (ZG-004, UZG-005) | ≤ 150 | ≤ 300 | ≤ 2 000 | ≤ 3 000 | ≤ 20 000 |
| **Belastungsgrenze** | Marktgärtnerei (UZG-002) | 500 | 500 | 5 000 | 8 000 | 50 000 |

Die Zielwerte gelten für „groß"; die Belastungsgrenze ist zugleich die **harte Quote** (GP-NFR-017, SR-004) und die Schwelle, ab der der Konva-Renderer (D-01) und Server-Paginierung der Pflanzen verpflichtend werden.

### 25.2 Zielwerte

| ID | Prio | Metrik | Ziel | Begründung |
|----|------|--------|------|------------|
| GP-NFR-030 | MUST | `GET /plan` p95 Serverzeit (groß) | ≤ 300 ms | Ein Request, Indizes auf `site_key`; 3 000 Slots sind ein AQL-Scan |
| GP-NFR-031 | MUST | `GET /plan` Antwortgröße (groß) | ≤ 500 KB unkomprimiert | Pflanzen als Kurzinfo, keine Fotos |
| GP-NFR-032 | MUST | Zeit bis interaktiver Plan nach Navigation (groß, Desktop, Cache warm) | ≤ 2,0 s; Feldmodus 4G ≤ 3,0 s | UI-NFR-003 TTI < 3,5 s mit Reserve für den Dynamic Import |
| GP-NFR-033 | MUST | Drag-Frame-Zeit (groß, 1 Objekt) | ≤ 16 ms (60 fps) auf Mittelklasse-Laptop, ≤ 33 ms auf Mittelklasse-Smartphone | CSS-Transform statt Re-Render (GP-NFR-011) |
| GP-NFR-034 | MUST | Zoom/Pan-Frame-Zeit (groß) | ≤ 16 ms | `viewBox`-Änderung, Culling |
| GP-NFR-035 | MUST | Batch-Speichern (50 Operationen) p95 | ≤ 500 ms | eine Transaktion, Containment-Checks O(n·m) mit bbox-Vortest |
| GP-NFR-036 | MUST | Layout-Preview (200 Positionen, Polygon-Beet) | ≤ 100 ms serverseitig, ≤ 50 ms clientseitig | reine Rechnung |
| GP-NFR-037 | MUST | Historie-Seite (50 Einträge aus 20 000) | ≤ 200 ms | Index `(tenant_key, location_key, performed_at desc)` |
| GP-NFR-038 | MUST | PDF-Erzeugung (groß) | ≤ 5 s (REQ-032) | WeasyPrint mit SVG; Pflanzen-Marker ab 2 000 als Zähler je Beet statt Einzelsymbol |
| GP-NFR-039 | SHOULD | Speicher Editor-Tab (groß) | ≤ 150 MB Heap | DOM-Knoten ≈ 4 × Objekte + Culling |
| GP-NFR-040 | MUST | Messung: Lighthouse-CI (`lighthouserc.json`) erhält die Plan-Route; vitest-Benchmark für `applyOperation` und `compute_layout`; pytest-Benchmark für Containment-Check mit 3 000 Slots | CI-Assertion | Zielwerte werden als Assertion geführt, nicht als Prosa |

---

## 26. Sicherheit

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-050 | MUST | Alle Endpunkte tenant-scoped (`/t/{slug}`), Rollen nach §21.8 über `require_permission`; fremde Ressourcen liefern 404 (Bestandsmuster). Negativtests je Endpunkt (cross-tenant read/write) nach dem Muster der ZAP-Nightly (NFR-015). |
| GP-NFR-051 | MUST | Import (JSON): Größe ≤ 5 MB, `schema_version` geprüft, keine Keys aus dem Import übernommen (immer neue `_key`), Grenzen und Referenzregeln nach GP-FR-141/GP-NFR-058; der Export enthält keine `*_by`-Felder und keine Nutzer-Keys. |
| GP-NFR-052 | MUST | **SVG/PDF-Härtung (SR-015):** (a) Die PDF-Erzeugung nutzt einen restriktiven WeasyPrint-`url_fetcher`, der nur `data:`-URIs und Pfade unterhalb des Template-Verzeichnisses zulässt — der heutige `PrintEngine` (`print_engine.py:172`) ruft `HTML()` ohne `url_fetcher` auf, der Default lädt `http(s)://` und `file://` (SSRF/Local-File-Read; betrifft auch die bestehenden `/print/*`-Endpunkte → eigenes Issue). (b) Der SVG-Writer emittiert nur eine Allowlist (`svg, g, rect, circle, polygon, polyline, line, path, text, tspan, title, desc, defs, pattern`) ohne `href`/`xlink:href`/`style url()`/`foreignObject`/`script`/`image`; Nutzertext wird kontextgerecht escaped (Text **und** Attribut). (c) `color` passt auf `^#[0-9A-Fa-f]{6}$`; `layers`, `locale`, `scale`, `paper` sind Enums. (d) Jinja-Autoescape an. (e) SVG-Download mit `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'`. (f) Bilder im PDF nur als serverseitig eingebettete `data:`-URIs aus NFR-013-Attachments des Tenants. Negativtest: Beetname `"><image href="http://169.254.169.254/"/>` und `file:///etc/passwd` erzeugen weder Abruf noch Element (GP-ACC-045). |
| GP-NFR-053 | MUST | Fotos über die bestehende Attachment-Pipeline (NFR-013: EXIF-Strip, Größenlimits, Virenscan-Hook); keine GPS-Daten aus Fotos in den Plan übernehmen. QR-Deep-Links (GP-FR-052) enthalten nur einen relativen App-Pfad, kein Token; Rücksprung nach Login nur same-origin; Nicht-Mitglied → 404 ohne Tenant-Wechsel (SR-023). |
| GP-NFR-054 | MUST | `performed_by_user_key` wird aus dem Token gesetzt, nie aus dem Body; `performed_by_label` (Dritte) ist Freitext ohne Nutzerbezug. |
| GP-NFR-055 | MUST | DSGVO (REQ-025/NFR-011): **Retention (SR-005, Betreiberentscheid):** NFR-011 erhält die Zeile `care_events` — **5 Jahre** ab `performed_at` (analog Fruchtfolge-Rückblick GP-FR-103), danach werden `performed_by_user_key`, `performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`, alle Freitexte und `photo_refs` anonymisiert bzw. gelöscht, Kategorie/Zeit/Menge/Beet/Pflanzen bleiben (Fruchtfolge); für `category ∈ {pest_control, ipm}` gilt der PflSchG-Vorbehalt wie bei `treatment_applications`; `garden_plan_audit` 1 Jahr, danach Hard-Delete. Der Celery-Master-Task setzt beides durch. **Löschkaskade (SR-007):** `ErasureEngine.ANONYMIZE_COLLECTIONS` ersetzt den Nutzer-Key in `care_events.{performed_by_user_key, performed_for_user_key, created_by, voided_by, redacted_by}`, `garden_objects.created_by`, `sites.plan.plan_updated_by`, `garden_plan_audit.user_key`, `bed_templates.created_by` durch `_anonymized`; ein Inventar-Test prüft, dass jedes `*_by`/`*_user_key`-Feld der neuen Collections in der Kaskade steht. **Art. 15/20 (SR-008):** der DSGVO-Export enthält alle `care_events`, die der Betroffene ausgeführt oder angelegt hat, und seine `garden_plan_audit`-Einträge. Geometrien sind keine personenbezogenen Daten; GPS der Site unterliegt der bestehenden Regel; Eigenposition siehe GP-UX-026. |
| GP-NFR-056 | MUST | **Rate-Limits (SR-017)** über den Bestands-Limiter, 429 nach NFR-006 mit `Retry-After`: Batch 10/min je Nutzer; Preview 60/min; PDF/SVG/Export/CSV 10/min je Nutzer und 30/min je Tenant; Import 3/min je Tenant; `quick-planting`, `slots/batch`, `log-watering`, `clear` 20/min je Nutzer; `POST /care-events` und `tasks/batch/status` 60/min je Nutzer, Batch-Größe ≤ 200 Tasks; `GET /plan?as_of=` 30/min. |
| GP-NFR-057 | SHOULD | `security-review`-Skill auf den PR mit Batch-API und Import; ZAP-Nightly-Negativtest für `POST /plan/import` cross-tenant. |

---

## 27. Observability (NFR-007)

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-060 | MUST | Structlog-Events: `garden_plan.batch_applied {site_key, revision, op_count, duration_ms}`, `garden_plan.revision_conflict`, `garden_plan.validation_failed {codes[]}`, `care_event.created {category, trigger}`, `planting_layout.computed {strategy, count, duration_ms}`; keine Nutzertexte in Logs; Batch-/Import-Payloads, Pydantic-`input`-Werte in 422-Details (Log-Seite), `flow_rate_ha_entity_id` und Dateinamen werden nie geloggt (SR-025, NFR-011 L-1…L-9). |
| GP-NFR-061 | MUST | Prometheus-Metriken: `garden_plan_batch_duration_seconds` (Histogram), `garden_plan_conflicts_total`, `care_events_created_total{category}`, `garden_plan_size_objects` (Gauge je Request-Bucket klein/mittel/groß). |
| GP-NFR-062 | MUST | Frontend: Sentry nur bei erteilter Einwilligung (REQ-025 Consent-Middleware, SR-019); Breadcrumbs enthalten Ereignistyp und Zähler, aber keine Namen, Notizen, Koordinaten oder Keys; Redux-State geht nicht an Sentry (`stateTransformer → null`); Fehler im Renderer werden mit Modellgröße (nicht Inhalt) gemeldet. Web-Vitals der Plan-Route über die bestehende Lighthouse-CI. |
| GP-NFR-063 | SHOULD | Celery-Tasks (Adjacency, Konsistenz) melden Laufzeit und Trefferzahl; Konsistenz-Job alarmiert ab > 100 Fachereignissen ohne Protokoll. |
| GP-NFR-064 | MUST | Fehlerbehandlung: alle Fachfehler als NFR-006-Fehlerobjekte; 500 nur bei echten Defekten; der Konflikt-Dialog bietet den JSON-Download der ungespeicherten Operationen (kein Datenverlust). |

---

## 28. MVP

### 28.1 Umfang (MUST-Anforderungen mit „MVP = ja")

| # | Vorgabe aus dem Auftrag | Erfüllt durch |
|---|-------------------------|---------------|
| 1 | Garten anlegen | bestehende Site + GP-API-002 (UC-01) |
| 2 | Gartenfläche definieren | GP-FR-005/015, Boundary + Nordwinkel |
| 3 | Beete zeichnen | GP-FR-019/040, rect/circle/polygon |
| 4 | Beete verschieben und skalieren | GP-FR-021/022/023 (+ drehen GP-FR-008) |
| 5 | Metrische Maße anzeigen | GP-FR-004/014, Maßstabsbalken GP-FR-009 |
| 6 | Raster verwenden | GP-FR-011/012 |
| 7 | Beete speichern | GP-API-003 Batch mit Revision, GP-NFR-013 |
| 8 | Pflanzen einem Beet zuordnen | GP-FR-060–066, GP-API-020/023 |
| 9 | Pflanzen grafisch darstellen | GP-FR-067 |
| 10 | Einfache Pflanzabstände | GP-FR-062/063/073 (grid, rows, free) |
| 11 | Pflegeaufgaben erstellen | GP-FR-080–082 |
| 12 | Pflegeaufgaben als erledigt markieren | GP-FR-083–085, GP-API-031 |
| 13 | Pflegehistorie anzeigen | GP-FR-100–103/107, GP-API-034/038 |
| 14 | Responsive Bedienung | §17.1, Feldmodus GP-UX-020–023/025/027 |
| 15 | REST API | §21 (MUST-Zeilen) |
| 16 | Persistente Speicherung in ArangoDB | §20, Migrationen v0072–v0074 |

Zusätzlich im MVP, weil ohne sie das Obige nicht abnehmbar ist: Gartenobjekte `path`, `tree`, `building`, `fence`, `water_source`, `other` (Orientierung auf dem Plan); Undo/Redo (ohne es ist jeder Fehlklick ein Datenverlust); PDF/SVG-Export (REQ-032 §2.5 wartet darauf); JSON-Export (Sicherung); Bodenprofil-Grundfelder (Beetfelder laut Auftrag §6); Beet-Nachbarschaft aus Geometrie (sonst läuft die bestehende Mischkultur-Engine für Beete leer); **nach Review (F-12, Betreiberentscheid):** Fruchtfolge-Hinweis auf Beet-Ebene mit Anbaupausen je Familie, Mischkultur-Hinweis im Dialog, Vorjahr am Beet (GP-FR-077/131/132), Beet räumen (GP-FR-055), Schnellprotokoll und Rückgängig im Feldmodus (GP-UX-029, GP-FR-149), Redaktion (GP-FR-109), Quoten und Pflicht-Audit.

### 28.2 Bewusst nicht im MVP (mit Begründung)

| Funktion | Prio | Begründung |
|----------|------|------------|
| Bewässerungszonen, Aktor-Kopplung, HA-Export (§14) | SHOULD/COULD | Fachlich eigenständig; der Plan funktioniert ohne Zonen. Zuerst muss die Beet-Ebene stehen, an der Zonen hängen. |
| JSON-Import, Vorlagen, Standardgrößen-Schnellwahl (§10, §23) | SHOULD | Export sichert die Daten; Import und Vorlagen sind Komfort und erzeugen eigene Validierungsfälle (`replace`-Semantik). |
| Mischkultur-Overlay, Rotationsmatrix, Folgekultur-Empfehlung (§16) | SHOULD | Die **Hinweise** sind im MVP (F-12); Overlay und Matrix sind Visualisierungen derselben Daten und folgen in Welle 8. |
| Bodenanalyse-Ereignisse, Nährstoff-Ampel, Flächendosierung (§15) | SHOULD | Flächendosierung hängt an REQ-004-Arbeit; die Ampel braucht ein begründbares Regelwerk (Agrobiologie-Review). |
| Offline-Lesen/-Puffern (GP-UX-024) | SHOULD | UI-NFR-012 ist repo-weit nicht umgesetzt (kein Workbox); der Plan darf nicht der erste Offline-Fall sein (F-17, Betreiberentscheid). Im MVP: sichtbarer Offline-Hinweis und gesperrtes „Erledigt" statt stillem Verlust. |
| Vorgeschlagene Aufgaben (GP-FR-086) | SHOULD | Hängt an ADR-008 Phase 3 (Propagation), die nicht abgeschlossen ist. |
| Objekt-Snap, Ausrichten/Verteilen, Messwerkzeug, Hintergrundbild | SHOULD/COULD | Editor-Komfort ohne fachlichen Mehrwert für die ersten Nutzer. |
| GeoJSON, PNG, CSV | COULD/SHOULD | PDF/SVG decken Drucken und Weitergabe ab. |
| Konva-Renderer | bedingt | Erst bei gemessener Schwelle (GP-NFR-013); die Renderer-Grenze ist im MVP. |
| Echtzeit-Mehrbenutzer, persistente Gruppen, Sonnen-/Schattenberechnung | WON'T | §29 bzw. GP-FR-030 |

### 28.3 Priorisierte MVP-Anforderungsliste

Reihenfolge = Implementierungsreihenfolge (Abhängigkeiten), siehe §34.

1. GP-DATA/GP-NFR-015: Migration v0072 (Collections, Edges, Indizes, `dimensions`/`position` → Geometrie), v0073 (`is_bed`, Seeds), v0074 (TaskCategory), v0076 (Cron → RRULE), v0077 (NutrientDemand-Split); Entfernung der Altfelder samt Lesern
2. GP-FR-004–008, GP-NFR-012: `Geometry`-Typ, `geometry_calculator` (Fläche, bbox, Containment, Einfachheit) + Testvektoren
3. GP-API-001/002/003, GP-NFR-013/014, V-01–V-05, V-14, V-15, V-17, V-19: Plan lesen, Grenze, Batch
4. GP-API-010/013/014/015: Einzelressourcen
5. GP-NFR-003/005/006/009/010/011: Editor-Grundgerüst (Slice, Operationen, SVG-Renderer, Culling, Dynamic Import)
6. GP-FR-009–012, 014, 015, 019–028, 032: Werkzeuge, Raster, Snap, Undo/Redo, Panel, Kontextmenü
7. GP-UX-001–003, 005–013, 015, 017: UX-Grundlagen, Konflikt-Dialog, testids, i18n
8. GP-NFR-020–027: Accessibility (parallel zu 5–7, nicht danach)
9. GP-FR-040–043, 046, 047, 050, GP-FR-053, 055, GP-API-011/012/018/019: Beetverwaltung, Beetansicht, Beet räumen
10. GP-FR-060–070, 072, 073, 077, GP-API-016/020–025, V-04, V-06–V-08: Pflanzplanung (mit Zeitfenster-Reservierung, Reihenzuweisung, Vorjahr)
11. GP-FR-130–132, 137, 138/139: Adjacency, Fruchtfolge-/Mischkultur-Hinweis, NutrientDemand-Split
12. GP-FR-080–085, 088, GP-API-030–032, V-11: Beetpflege
13. GP-FR-100–103, 107, 109, 110a, GP-API-033–038, 041, V-11–V-13, GP-NFR-055: Pflegeprotokoll, Redaktion, Historie
14. GP-FR-120/121: Bodenprofil
15. GP-UX-020–023, 025, 027, 029, 030, GP-API-017: Feldmodus mit Schnellprotokoll und Listen-Einstieg
16. GP-FR-140, 142, 143, 147, GP-API-004/006/007: Export
17. GP-NFR-017, 030–038, 040, 050–056, 058, 060–062, 064: Quoten, Performance-/Security-/Observability-Nachweise

---

## 29. Future Features

Alle als WON'T für dieses Vorhaben; das Datenmodell lässt sie zu, ohne dass heute etwas dafür gebaut wird.

| Funktion | Anknüpfungspunkt im Modell | Was fehlt |
|----------|---------------------------|-----------|
| Automatische Bewässerungsempfehlung | `irrigation_zones` + `irrigation_demands` (REQ-037) + `care_events(watering)` | Regelwerk „Bedarf − letzte Gabe − Niederschlag" |
| Wetterintegration | `Site.gps_coordinates`, REQ-046 Quellen | Niederschlag in die Verbrauchsbilanz |
| Bodenfeuchtesensoren | REQ-005 Sensoren an Locations | Zuordnung Sensor → Beet/Zone (GP-FR-118) |
| Home Assistant | `zone_actuated_by`, `ha_publish` | Entitätsvertrag (HA-Dokument) |
| NFC/RFID | Beet-QR (GP-FR-052) | NFC-Tag-URL = dieselbe Deep-Link-Route |
| Automatische Pflegeerinnerungen am Beet | `Task.suggested`, REQ-022 Engine | Beet-Profile (Intervalle je Beettyp/Saison) |
| Pflanzenkrankheitserkennung | REQ-036/038/044 am Foto | Foto-Zuordnung Beet → Pflanze (GP-FR-051) |
| KI-Pflanzplanung | `compute_layout`, REQ-028-Graph, REQ-031 Assistent | Zielfunktion (Ertrag, Kompatibilität, Fruchtfolge) |
| Automatische Fruchtfolgeplanung | `CropRotationPlan`, GP-FR-133 | Optimierer über Beete × Jahre |
| Automatische Mischkulturplanung | `slot_role = zone`, `compatible_with` | Zuteilungsalgorithmus |
| Sonnen-/Schattenberechnung | `north_angle_deg`, `gps_coordinates`, GardenObject `tree.height_m`, `building` (Höhe COULD), `sun_calculator` | Schattenwurf-Geometrie, Stundenintegration → `sun_exposure` vorbelegen. **Jetzt angelegt (billig, später teuer):** `height_m` an `building`/`wall`/`fence`/`shrub`/`trellis`/`tree`, `ridge_height_m`, `crown_base_height_m`, `foliage`, `opacity`, `off_site` (§9.5); `Site.plan.terrain {slope_deg, aspect_deg}` und `Site.elevation_m` (optional, SHOULD); Frühbeet/Tunnel `cover_material`, `light_transmission_percent`; `Location.sun_exposure_source ∈ {manual, computed}` + `sun_hours_direct`; `sun_exposure`-Schwellen fest: `full_sun` ≥ 6 h, `partial_shade` 3–6 h, `shade` < 3 h direkte Sonne am Sommer-Äquinoktium (H-006) |
| Ertrags-/Ernteplanung | `harvest_batches`, `area_m2`, `yield_per_m2_g` (REQ-007) | Prognose je Beet aus Historie |
| Echtzeit-Mehrbenutzer-Editing | `plan_revision` | CRDT/OT, WebSocket — bewusst nicht (Gartenpläne werden selten gleichzeitig bearbeitet) |
| Georeferenzierte Unterlage (Luftbild) | GP-FR-033 | Kachel-Quelle, Lizenz |

---

## 30. Akzeptanzkriterien

Alle Kriterien sind Given/When/Then; Tier in Klammern (U = Unit, I = Integration/API, E = E2E). TC-IDs werden bei Übernahme in `spec/e2e-testcases/TC-REQ-053.md` vergeben.

**Geometrie und Editor**

- **GP-ACC-001** (I) Given eine Outdoor-Site ohne Plan, When `PUT /plan/boundary` mit einem Rechteck 10 × 10 m und `north_angle_deg = 0` gesendet wird, Then antwortet die API 200 mit `plan_revision = 1`, `total_area_m2 = 100.0`, und `GET /plan` liefert die Grenze unverändert.
- **GP-ACC-002** (E) Given ein Garten 10 × 10 m, When der Nutzer mit dem Beet-Werkzeug ein Rechteck zieht, das nach Snap 2,0 × 1,0 m misst, und speichert, Then enthält `GET /plan` eine Location mit `geometry.width_m = 2.0`, `length_m = 1.0`, `area_m2 = 2.0`, And das Beet wird bei Zoom 100 % in genau dem Verhältnis 2:1 gerendert (SVG-`width`/`height` in Modelleinheiten).
- **GP-ACC-003** (U) Given ein Polygon mit den Punkten (0,0),(4,0),(4,3),(0,3), When `geometry_calculator.area()` aufgerufen wird, Then ist das Ergebnis 12,000; And für dasselbe Polygon mit `rotation_deg = 37` bleibt die Fläche 12,000 (±0,001).
- **GP-ACC-004** (U) Given ein Polygon mit Selbstschnitt (0,0),(2,2),(2,0),(0,2), When validiert wird, Then wird `geometry.self_intersecting` zurückgegeben.
- **GP-ACC-005** (I) Given ein Beet mit 12 Slots, When `update_geometry` das Beet um 1 m verschiebt und 90° dreht, Then bleiben alle 12 Slot-Geometrien im Datenbankdokument byte-identisch, And `GET /plan` liefert ihre Plan-Koordinaten transformiert (Stichprobe: Slot (0,0) landet auf `origin + R(90°)·(0,0)`).
- **GP-ACC-006** (E) Given ein gespeicherter Plan mit Raster 10 cm, When der Nutzer ein Beet mit der Maus um 23 cm nach rechts zieht, Then liegt die neue x-Koordinate auf einem Vielfachen von 0,10 m (hier +0,20), And bei gehaltener Alt-Taste bei genau +0,23.
- **GP-ACC-007** (E) Given ein Beet ausgewählt, When der Nutzer `Ctrl+Z` drückt, nachdem er es verschoben hat, Then steht das Beet an der ursprünglichen Position, der Speichern-Status zeigt „Ungespeicherte Änderungen (0)", And `Ctrl+Shift+Z` stellt die Verschiebung wieder her.
- **GP-ACC-008** (E) Given ein Beet ausgewählt und die Tastatur als einziges Eingabegerät, When der Nutzer Pfeil-rechts dreimal drückt, Then ist das Beet um 3 Rasterschritte verschoben, And die `aria-live`-Region hat die neue Position angesagt (Text enthält die Koordinate).
- **GP-ACC-009** (I) Given ein Garten mit Grenze 10 × 10 m, When ein Batch eine Location mit `origin = [9.5, 9.5]`, 2 × 1 m erzeugen will, Then antwortet die API 422 mit `details[0].code = geometry.outside_parent` und `op_index = 0`, And es wurde nichts persistiert (`plan_revision` unverändert).
- **GP-ACC-010** (I) Given zwei Nutzer mit demselben `expected_revision = 5`, When beide einen Batch senden, Then erhält der erste 200 mit `plan_revision = 6`, der zweite 409 `plan.revision_conflict` mit `current_revision = 6`, And die Operationen des zweiten sind nicht persistiert.
- **GP-ACC-011** (E) Given der 409 aus GP-ACC-010 im Browser des zweiten Nutzers, When der Konflikt-Dialog erscheint, Then bietet er „Neu laden" und „Änderungen als JSON herunterladen", And nach „Neu laden" zeigt der Plan Revision 6 und der Undo-Stapel ist leer.
- **GP-ACC-012** (I) Given ein Beet mit 2 aktiven Pflanzen, When `DELETE /locations/{key}`, Then 409 `location.has_active_plants` mit `details.active_plant_count = 2`.
- **GP-ACC-013** (I) Given ein Batch mit 501 Operationen, When gesendet, Then 422 `batch.too_many_operations`.
- **GP-ACC-014** (I) Given Tenant A besitzt Site S, When Nutzer aus Tenant B `GET /t/b/sites/S/plan` oder `POST /t/b/sites/S/plan/batch` aufruft, Then 404 in beiden Fällen, And kein Log-Eintrag `garden_plan.batch_applied`.

**Beetverwaltung**

- **GP-ACC-015** (I) Given ein Beet `active`, When `POST /locations/{key}/status {bed_status: "planned"}`, Then 422 `bed_status.invalid_transition`; When stattdessen `fallow` mit `reason`, Then 200 And ein `care_event(category = bed_status_change)` existiert mit `reason`.
- **GP-ACC-016** (E) Given die Beetliste einer Site mit 3 Beeten, When der Nutzer eine Zeile anklickt, Then ist das Beet auf dem Plan selektiert und im Viewport (Bounding Box sichtbar).

**Pflanzplanung**

- **GP-ACC-017** (U) Given ein Rechteckbeet 3,0 × 1,2 m, `layout_strategy = rows`, `spacing_cm = 30`, `row_spacing_cm = 40`, `edge_margin_cm = 15`, When `compute_layout` läuft, Then entstehen 3 Reihen (y = 0,15/0,55/0,95) × 10 Positionen (x = 0,15 … 2,85) = 30 Positionen, And alle liegen innerhalb des Beets abzüglich Rand, And das TypeScript-Pendant liefert für denselben Vektor aus `garden-plan-vectors.json` dieselben 30 Punkte (±0,001).
- **GP-ACC-018** (U) Given ein Polygonbeet (Dreieck (0,0),(4,0),(0,3)), `grid`, 50 cm, Rand 0, When `compute_layout`, Then liegt jede Position innerhalb des Dreiecks (Point-in-Polygon), And keine außerhalb.
- **GP-ACC-019** (I) Given ein Beet mit Geometrie, When `POST /planting-runs` mit einem Entry (`quantity = 6`, `rows`, 60/80 cm) und `location_key` des Beets, Then existieren 6 Slots mit `slot_role = position` und `run_planned_at`-Edges mit `sequence 1..6`, And `GET /locations/{key}/plantings?state=planned` listet 6 geplante Positionen.
- **GP-ACC-020** (I) Given GP-ACC-019, When `POST /planting-runs/{key}/create-plants {assign_to_slots: true}`, Then existieren 6 `plant_instances` mit `slot_key` genau der geplanten Slots in `sequence`-Reihenfolge, And `state=planned` ist leer, `state=active` hat 6.
- **GP-ACC-021** (I) Given ein Slot ist für Run A (`planned`) reserviert, When Run B denselben Slot per `plan-slots` beansprucht, Then 409 `slot.already_planned`.
- **GP-ACC-022** (E) Given eine aktive Pflanze auf Position (0,30, 0,90) im Beet, When der Nutzer im Feldmodus „Position korrigieren" wählt und per Long-Press-Drag auf (0,60, 0,90) zieht, Then hat `Slot.geometry.origin = [0.60, 0.90]`, And in der Historie steht ein `care_event(category = position_corrected)` mit `plant_keys = [die Pflanze]`.
- **GP-ACC-023** (I) Given ein Beet mit Slots im Abstand 30 cm und `adjacency_factor = 1.5`, When ein Slot verschoben wird, Then existieren `adjacent_to`-Kanten genau zwischen Slots mit Zentrumsabstand ≤ 45 cm (beidseitig, `distance_cm` gesetzt), And eine Kante mit `source = manual` bleibt unverändert.

**Beetpflege und Historie**

- **GP-ACC-024** (I) Given ein Task `category = feeding`, `entity_type = location`, `entity_key = Beet`, When `POST /tasks/{key}/complete` mit `{product_ref: fertilizer X, quantity: 2, unit: "l_per_m2", plant_keys: [p1, p2]}`, Then ist der Task `completed`, And genau ein `care_event` existiert mit `task_key`, `category = feeding`, `quantity_total = 2 × area_m2`, `performed_by_user_key` = Aufrufer, `source_ref` auf ein neu erzeugtes `feeding_events`-Dokument, And beides liegt in einer Transaktion (Fehler beim `feeding_event` → Task bleibt `pending`, kein `care_event`).
- **GP-ACC-025** (I) Given `POST /tasks/{key}/complete` mit `performed_at` 10 Minuten in der Zukunft, Then 422 `care_event.performed_in_future`; mit `performed_at` vor 400 Tagen, Then 422 `care_event.too_old`.
- **GP-ACC-026** (I) Given ein `care_event` E1, When `POST /care-events/E1/supersede` mit korrigierter Menge, Then existiert E2 mit `supersedes_key = E1`, E1 hat `superseded_by_key = E2`, And `GET /care-events?location_key=…` liefert nur E2, mit `include_superseded=true` beide; When `PATCH /care-events/E1` versucht wird, Then 405 oder 422 `care_event.immutable`.
- **GP-ACC-027** (E) Given ein Beet mit 60 `care_events` über 2 Jahre, When der Nutzer den Tab „Historie" öffnet und nach Kategorie „Gießen" filtert, Then erscheinen nur Gieß-Ereignisse, paginiert zu 50, neueste zuerst, And der Zeitstrahl zeigt je Jahr die Familien der Pflanzungen.
- **GP-ACC-028** (I) Given Pflanzen in einem Beet 2024 (Solanaceae) und 2025 (Fabaceae), When `GET /locations/{key}/rotation?years=5`, Then enthält die Antwort je Jahr die Familie und `nutrient_demand_level`.

**Feldmodus, Export, Accessibility, Performance**

- **GP-ACC-029** (E, Viewport 390 × 844) Given ein Beet mit einer offenen Aufgabe „Gießen", When der Nutzer das Beet antippt und im Sheet „Erledigt" tippt und ohne weitere Eingabe „Fertig" tippt, Then ist die Aufgabe `completed` mit genau 2 Tipps nach der Beetauswahl, And das Touch-Ziel „Erledigt" misst ≥ 64 × 64 px, And ein `care_event(category = watering)` ohne Menge existiert.
- **GP-ACC-030** (I) Given ein Plan mit Grenze 10 × 6 m und 3 Beeten, When `GET /print/garden-plan/{site}?paper=a4&orientation=landscape&scale=auto`, Then ist das PDF ≤ 5 s erzeugt, Maßstab 1:50 gewählt (10 m → 200 mm passen auf 277 mm), And ein Beet 2 × 1 m misst im PDF 40 × 20 mm (±0,5 mm, geprüft über das eingebettete SVG), And Maßstabsleiste, Nordpfeil und Legende sind vorhanden.
- **GP-ACC-031** (I) Given ein Plan mit 5 Beeten, 20 Slots, 3 Gartenobjekten, When `GET /plan/export` und anschließend `POST /plan/import {mode: "replace"}` in eine leere Site desselben Tenants, Then stimmen alle Geometrien, Namen, Typen und Bodenprofile überein (Diff ohne `_key`, Zeitstempel leer), And die Keys sind neu vergeben.
- **GP-ACC-032** (E) Given der Plan im Browser, When die Ansicht „Als Liste" aktiviert wird, Then sind alle Objekte als Liste mit Name, Typ, Position, Maßen erreichbar, And `vitest-axe` meldet keine Verstöße auf Editor und Liste.
- **GP-ACC-033** (U, Benchmark) Given ein Modell der Klasse „groß" (150 Beete, 300 Objekte, 3 000 Slots, 2 000 Pflanzen), When `applyOperation(move)` 100-mal läuft, Then ≤ 1 ms Median, And der SVG-Renderer rendert bei Viewport auf 10 % der Fläche ≤ 400 DOM-Objekte (Culling).
- **GP-ACC-034** (I, Benchmark) Given dieselbe Klasse „groß" in ArangoDB, When `GET /plan` 20-mal läuft, Then p95 ≤ 300 ms und Antwort ≤ 500 KB.
- **GP-ACC-035** (I) Given ein Beet ohne Geometrie (Bestandsdaten), When `GET /plan`, Then erscheint es in `locations` mit `geometry = null` und bleibt in der Beetliste; When der Nutzer ihm eine Geometrie gibt, Then wird `area_m2` überschrieben; And Bestands-Locations mit `dimensions ≠ (0,0,0)` haben nach v0072 eine `rect`-Geometrie mit diesen Maßen und `height_m`.
- **GP-ACC-036** (E) Given eine Indoor-Site mit einer Location `tent` 1,2 × 1,2 m und 9 Slots, die v0072 aus `position` (3 × 3, `pitch_m = 0.3`) abgeleitet hat, When der Nutzer die Beetansicht öffnet und den mittleren Slot per Drag um 10 cm nach rechts verschiebt, Then liegt `geometry.origin` bei `(0.40, 0.30)`, And Ansicht, Werkzeuge und Historie sind identisch zur Beetansicht eines Outdoor-Beets (gleiche Komponenten, kein Zelt-Sonderpfad — nachweisbar über denselben `data-testid`-Satz).
- **GP-ACC-037** (I) Given eine Familie mit `typical_nutrient_demand = "heavy"` vor v0077, When die Migration läuft, Then steht dort `heavy_feeder`; And `PUT /botanical-families/{key}` mit `typical_nutrient_demand = "fallow"` antwortet 422; And `CropRotationPlan.demand_level = "green_manure"` ist danach `plan_role = green_manure` mit `nutrient_demand = null`.
- **GP-ACC-038** (I) Given ein Task mit `recurrence_rule = "0 8 * * 1"` vor v0076, When die Migration läuft, Then ist die Regel `FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0`, And `POST /tasks` mit einer Cron-Regel antwortet 422 `recurrence.rrule_required`.
- **GP-ACC-039** (I) Given ein Slot mit Reservierung Run A `planned_from = 2026-05-15`, `planned_until = 2026-09-30`, When Run B denselben Slot mit `planned_from = 2026-10-05` beansprucht, Then 200 (Nachkultur); When Run C mit `planned_from = 2026-08-01`, Then 409 `slot.already_planned` mit `overlap_from = 2026-08-01`, `overlap_until = 2026-09-30`.
- **GP-ACC-040** (I) Given ein Beet mit 2 aktiven Runs und 12 Pflanzen, When `POST /locations/{key}/clear {termination_type: "senesced"}`, Then sind alle 12 Pflanzen `removed_on = heute`, beide Runs `completed`, 12 Slots `archived_at` gesetzt, ein `care_event(clearing)` existiert; And ein neuer Run im Beet mit Zonen-Layout wird **nicht** durch V-06 gegen die archivierten Slots abgewiesen.
- **GP-ACC-041** (I) Given Tenant B besitzt Pflanze P, When Tenant A `POST /t/a/care-events {plant_keys: [P], …}` sendet, Then 422 `reference.not_found`, And kein `care_event_for`-Edge auf P; dasselbe für `slot_keys` in `plan-slots`, `location_keys` in Zonen, `photo_refs` mit fremdem Attachment, `supersedes_key` auf fremdes Event, `water_source_key` auf fremdes Objekt.
- **GP-ACC-042** (I) Given ein Gärtner (nicht Leitung), When er `POST /plan/batch` mit `[{op: "update_geometry", …}, {op: "delete", entity: "location", key: …}]` sendet, Then 403 `batch.operation_forbidden {op_index: 1}`, And auch die erste Operation ist nicht persistiert.
- **GP-ACC-043** (I) Given ein Beet 1 000 × 1 000 m, When `planting-layout/preview` mit `spacing_cm = 5`, Then 422 `layout.too_many_positions` mit `estimated ≈ 4e8`, And die Antwortzeit ist < 50 ms (Vorab-Schätzung, keine Punkterzeugung).
- **GP-ACC-044** (I) Given ein `care_event` E1 mit `summary = "Nachbarin Frau Müller hat gegossen"` und zwei Fotos, superseded durch E2, When die Leitung `POST /care-events/E2/redact {reason}`, Then enthalten E1 und E2 `summary = "[redacted]"`, `photo_refs = []`, `redacted_by` = Leitung, die beiden Attachments sind gelöscht, And `garden_plan_audit` hat einen Eintrag `op = redact`.
- **GP-ACC-045** (I) Given ein Beet mit `name = '"><image href="http://169.254.169.254/"/>'`, When `GET /plan/render.svg` und `GET /print/garden-plan/{site}`, Then enthält das SVG kein `<image>`-Element und den Namen escaped als Text, And der Test-`url_fetcher` protokolliert keinen Abruf; dasselbe für `file:///etc/passwd` im Namen.
- **GP-ACC-046** (I) Given Location L von Tenant A, When das Repository mit `tenant_key = B` nach L fragt (`get_location(key, tenant_key=B)`), Then `None`/404 — der Filter greift auf dem neuen `locations.tenant_key`-Index, nicht erst am Site-Anker (SR-022).
- **GP-ACC-047** (E) Given ein Beet, in dem 2025 Brassicaceae standen und `rotation_pause_years(Brassicaceae) = 4`, When der Nutzer 2026 „Bepflanzen" mit Blumenkohl öffnet, Then zeigt der Dialog vor der Layout-Wahl einen Fruchtfolge-Hinweis mit Grund und Stärke, And „Trotzdem pflanzen" verlangt einen Grund, der am Run als `rotation_override_reason` gespeichert wird, And das Beet trägt danach ein Badge.
- **GP-ACC-048** (E, 390 × 844) Given das Beet-Sheet im Feldmodus, When der Nutzer den Chip „Gejätet/Gemulcht" tippt, Then existiert nach einem Tipp ein `care_event(category = weeding)` mit `trigger = manual`, And eine Snackbar „Rückgängig" ist 8 s sichtbar; When er sie tippt, Then ist das Event `voided_at` gesetzt mit `void_reason = undo`.
- **GP-ACC-049** (U) Given die Familie Fabaceae mit `nitrogen_fixing = true` und die Spezies Erbse mit `nutrient_demand = light_feeder`, When v0077 auf einem Bestand mit `nutrient_demand_level = nitrogen_fixer` läuft, Then hat die Spezies `nitrogen_fixing = true` und `nutrient_demand` aus dem Steckbrief (oder `null` + Eintrag im Dry-Run-Report), And `PUT /species/{key}` mit `nutrient_demand = "fallow"` oder `"nitrogen_fixer"` antwortet 422.

---

## 31. Risiken

| ID | Risiko | Eintritt | Auswirkung | Gegenmaßnahme |
|----|--------|----------|------------|---------------|
| R-01 | SVG-Renderer skaliert nicht bis zur Belastungsgrenze (5 000 Pflanzen) | mittel | Ruckeln beim Pan auf großen Plänen | Renderer-Grenze (GP-NFR-009) + Culling + Benchmark GP-ACC-033; Konva als zweiter Renderer hinter derselben Schnittstelle |
| R-02 | Logik-Drift zwischen Python- und TypeScript-Layout-Rechner | mittel | Vorschau ≠ gespeichertes Ergebnis | gemeinsame Testvektoren (§19.6), Server maßgeblich |
| R-03 | Zweite Schreibstelle `care_events` driftet von Fachcollections | mittel | Historie unvollständig | Atomarität im Abschluss-Übergang, Konsistenz-Job (GP-FR-105), Metrik |
| R-04 | Cron→RRULE-Migration (O-05) trifft nicht konvertierbare Ausdrücke | mittel | Migration bricht ab | Dry-Run-Report vor dem Lauf; nicht konvertierbare Regeln werden gelistet und manuell übersetzt; ADR-008 ist mit Welle 0 Accepted |
| R-05 | Bundle-Budget (Ist 343 KB bei 300 Ziel) | hoch | CI rot | Dynamic Import, 0 KB Initial-Zuwachs, eigener Chunk mit Budget (GP-NFR-003) |
| R-06 | Touch-Konflikte (Pan vs. Drag) auf Mobil | mittel | Frust im Feldmodus | Long-Press-Regel (GP-UX-008), E2E auf 390 px |
| R-07 | Polygon-Containment/Überlappung ohne Geometrie-Lib fehlerhaft bei konkaven Formen | mittel | falsche 422 oder stille Überlappung | Property-Tests; Shapely als COULD (D-04), falls Fälle auftreten |
| R-08 | Bestandsbeete ohne Geometrie (`dimensions = (0,0,0)`) und Alt-Slots mit falscher `pitch_m`-Annahme | sicher | Plan zeigt nicht alle Beete; Zelt-Slots liegen zu eng/weit | GP-ACC-035: Locations ohne Geometrie bleiben in Listen, Plan bietet „auf dem Plan platzieren"; `geometry_source = migrated_grid` wird im Editor als „geschätzt" markiert, bis der Nutzer die Location einmal speichert |
| R-09 | Locations ohne `tenant_key` → Tenant-Leck über Slot-/Geometrie-Endpunkte | mittel | Datenleck | §22.3, Negativtests GP-ACC-014 je Endpunkt, abgeleiteter Tenant-Guard-Sweep (Memory Welle 13) |
| R-10 | Enum-Erweiterung `TaskCategory` kollidiert mit Frontend-Mappings/i18n | mittel | Startup-/Render-Fehler | additive Migration, i18n-Vollständigkeits-Check (`i18n-completeness-checker`) |
| R-11 | Accessibility-Anspruch (Liste + Tastatur + aria-live) verdoppelt UI-Aufwand | hoch | Zeit | Liste ist zugleich mobile Fallback und Test-Oberfläche; früh bauen (Welle 2) |
| R-12 | ADR-007 (Breakpoints Code ≠ UI-NFR-001) offen | niedrig | Layout-Umschaltpunkte uneinheitlich | Feldmodus an `useMediaQuery(theme.breakpoints.down('sm'))` binden, nicht an Pixelzahlen |
| R-13 | `calculate_plants_per_m2` und `print_engine` werden von Bestandscode genutzt; die Erweiterungen (Reihenabstand, `url_fetcher`) ändern Verhalten außerhalb von REQ-053 | sicher | bestehende Tests/`/print/*` betroffen | eigene Issues (Anhang A, 6d/6e) mit Regressionstests vor Welle 1; `url_fetcher` ist eine Sicherheitskorrektur und geht zuerst |
| R-14 | `nutrient_demand` ist für viele Spezies im Steckbrief nicht erfasst → v0077 lässt `null` | hoch | Fruchtfolge-Hinweise ohne Zehrerstufe | Dry-Run-Report als Arbeitsliste für `plant-info-document-generator`; Hinweis funktioniert familienbasiert auch ohne Spezieswert |

---

## 32. Offene Fragen — entschieden am 2026-10-04

Alle Punkte wurden vom Betreiber entschieden; die Tabelle bleibt als Protokoll stehen. Spalte „Eingearbeitet" nennt die Stelle, an der die Entscheidung im Dokument wirkt.

| ID | Frage | Entscheidung | Eingearbeitet |
|----|-------|--------------|---------------|
| O-01 | `Slot.position` für Beet-Slots füllen? | **Kein zweites Positionsmodell.** Zelt und Beet laufen auf `Slot.geometry`; `position` wird migriert und entfernt. | §9.2a, §20.5, §20.8, GP-ACC-036, v0072 |
| O-02 | Wann `Location.dimensions` entfernen? | **Sofort in Welle 1** — Migration übernimmt (l, b) als Geometrie, h als `height_m`; keine Spiegelung. | §20.8, GP-ACC-035, Issue 56 |
| O-03 | Geometrie-Snapshots im MVP? | **Nein**, nur `garden_plan_audit` (SHOULD); Snapshots COULD mit Import-Welle. | §20.13, GP-FR-148 |
| O-04 | Beete mit Kind-Locations? | **Nein** — Reihen und Zonen sind Slots (`slot_role`). | R-7.5, D-10 |
| O-05 | ADR-008-Status | **Accepted in Welle 0**, RRULE kanonisch, Cron-Bestand per v0076 konvertiert, REQ-006 umgestellt. | §12.2, GP-NFR-015, GP-ACC-038, Issue 5 |
| O-06 | Kante für care_events → Pflanze | **`care_event_for` wiederverwenden**, Edge-Definition um `care_events` erweitern. | §20.10, §20.14 |
| O-07 | Zehrer-Enums | **In REQ-053 lösen** — zunächst als 6-Werte-Enum, nach K-001 revidiert zu `NutrientDemand` (3) + `nitrogen_fixing` + `PlanRole`; REQ-001/REQ-002 ziehen nach; v0077. | §16.3 (GP-FR-138/139), GP-ACC-037/049 |
| O-08 | Indoor-Sites auf dem Plan? | **Ja, für alle Site-Typen** (Folge von O-01); V-18 entfällt. | §2.3, §9.2a, §22.2 |
| O-09 | `shelf` als Beet? | **Nein** — nur `bed`, `raised_bed`, `planter`, `greenhouse_bed`, `cold_frame`. | GP-FR-040 |
| O-10 | Polygon-Zeichnen auf Smartphone | **Zulassen, nicht abnehmen.** | §17.1 |
| O-11 | Quelle für `spacing_cm_default` | **Steckbrief-Pipeline erweitern** (Schema, Vorlage, `plant-info-to-seed-yaml`, Validator). | GP-FR-061, Issue 57 |
| O-12 | PDF-Standard | **A4 quer, Maßstab automatisch**; A3 und fester Maßstab wählbar. | GP-FR-142 |
| O-13 | Durchfluss-Quelle der Zone | **Manuell mit optionaler HA-Überschreibung**, Provenienz am Verbrauchswert. | §14.1, GP-FR-114, §20.11 |
| O-14 | Fremde `care_events` korrigieren | **Eigene ab Gärtner, fremde nur Leitung.** | §21.8, GP-API-036 |
| O-15 | Modulname und Navigation | **`garden_planner`, unter „Standorte"**, kein eigener Hauptmenüpunkt. | §21.8, Issue 41 |
| K-001 | `nitrogen_fixer` im Zehrer-Enum (Review Agrobiologie) | **O-07 revidiert:** 3 Stufen + Bool + `PlanRole`. | §16.3, GP-FR-138/139, GP-ACC-049 |
| SR-022 | `tenant_key` auf Location/Slot (Review Security) | **Ja, v0072.** | §20.13, §22.3, GP-ACC-046 |
| F-12 | Fruchtfolge/Mischkultur im MVP (Review Persona) | **Ja, Hinweise + Vorjahr.** | GP-FR-077/131/132, §28 |
| F-09/F-17 | Revision je Objekt / Offline-Puffer (Review Persona) | **Revision nur für Struktur; Offline-Puffer SHOULD, Offline-Hinweis MVP.** | GP-NFR-007, GP-UX-024 |
| SR-005 | Retention `care_events` (Review Security) | **5 Jahre.** | GP-NFR-055, NFR-011 |
| SR-020 | `performed_by`-Filter (Review Security) | **Alle Rollen.** | GP-API-034 |
| F-01/F-02 | Reservierung ohne Zeitfenster, kein Saisonwechsel (Review Persona) | **Modellkorrektur eingearbeitet.** | GP-FR-055/065, V-06/V-08, GP-ACC-039/040 |
| W-014 | Beetstatus mischt Lebenszyklus und Saison (Review Agrobiologie) | **Getrennt.** | §7.4, D-19 |

Es gibt keine offenen Fragen mehr, die die Implementierung des MVP blockieren. Neue Fragen, die während der Umsetzung entstehen, werden als Issue mit Label `spec:REQ-053` erfasst, nicht hier nachgetragen.

---

## 33. Entscheidungsvorlagen

| ID | Entscheidung | Optionen | Empfehlung | Begründung |
|----|--------------|----------|------------|------------|
| **D-01** | Rendering-Technologie | SVG-in-React · Konva · Fabric · Canvas roh · Pixi | **SVG-in-React** mit Renderer-Grenze; Konva bei gemessener Schwelle | §19.4: Accessibility, Testbarkeit, 0 KB, Zielgrößen |
| **D-02** | Garten/Beet als neue Entitäten oder bestehende | neue Collections `gardens`/`beds` · Site/Location erweitern | **Site/Location erweitern** | keine Parallelarchitektur; Edges, Tasks, Sensoren, Fruchtfolge hängen bereits an Location |
| **D-03** | Pflanzenposition | eigenes Feld an PlantInstance · Slot-Geometrie | **Slot-Geometrie** (Slot = Position) | `placed_in` existiert; eine Wahrheit statt zwei |
| **D-04** | Geometrie-Bibliothek Backend | keine · Shapely | **keine im MVP** (eigene Calculator, Property-Tests) | Rechtecke/Kreise/einfache Polygone ≤ 200 Punkte; Shapely erst bei Bedarf (Objekt-Snap, komplexe Überlappung) |
| **D-05** | Koordinatenrahmen | alles im Plan-Rahmen · Slots beet-lokal | **Slots beet-lokal** | Beet verschieben = 1 Dokument (GP-ACC-005) |
| **D-06** | Nebenläufigkeit | keine · Revision je Objekt · Revision je Plan · Echtzeit | **Revision je Plan für Struktur** (Locations, GardenObjects, Boundary, Zonen); Slots, Quick-Planting, Pflege außerhalb (revidiert F-09) | Containment ist planweit; Feldarbeit darf den Desktop-Planer nicht mit 409 stören |
| **D-07** | Pflegeprotokoll | AQL-Projektion · eigene Collection mit Referenz · Fachcollections ersetzen | **eigene Collection `care_events`** | §13.2 |
| **D-08** | Batch-Semantik | Teilerfolg (Bestand bei Tasks) · Transaktion | **Transaktion** (alles oder nichts) | halbe Geometrieänderung ist nicht reparierbar |
| **D-09** | Fruchtfolge-/Mischkultur-Verstöße beim Bepflanzen | blocken (`validate_or_raise`) · Hinweis | **Hinweis** für Beete | Gärtner entscheiden bewusst; Blocker frustriert; Slot-Ebene bleibt wie bisher |
| **D-10** | Reihen | Locations · Slots (`row`) · Entry-Attribut | **Slots mit `slot_role = row`** + Layout am Entry | Reihen gehören zur Pflanzung, nicht zum Beet |
| **D-11** | GardenObject-Typen | je Collection · eine Collection mit Enum + Props-Union | **eine Collection** | zehn fast leere Collections wären Overhead ohne Nutzen |
| **D-12** | Auto-Save | ja · nein · optional | **nein im MVP**, optional SHOULD | explizites Speichern + Revision ist erklärbar; Auto-Save mit 409 ist es nicht |
| **D-13** | Persistente Gruppen | ja · nein | **nein** (WON'T) | GP-FR-030 |
| **D-14** | ID-Schema im Dokument | FR-xxx · GP-FR-xxx | **GP-** | Kollision mit `spec/nfr/NFR-0xx` |
| **D-15** | Positionsmodell Indoor vs. Outdoor | zwei Modelle (Raster + Geometrie) · ein Modell | **ein Modell** (`Slot.geometry`) | O-01: keine Sonderbehandlung; Mischkultur-Engine sieht damit auch Zelt-Nachbarn |
| **D-16** | Altfelder `Location.dimensions`, `Slot.position` | spiegeln · sofort entfernen | **sofort entfernen** (v0072) | O-01/O-02: zwei Wahrheiten für Maße sind die Fehlerquelle, die REQ-053 beseitigen soll |
| **D-17** | Zehrer-Enum | eigenes Spec-Issue · in REQ-053 | **in REQ-053**: `NutrientDemand` (3) + `nitrogen_fixing` (Bool) + `PlanRole` (revidiert nach K-001) | O-07: Rotationslogik braucht ein Enum; N-Fixierung ist orthogonal zur Zehrerstufe |
| **D-18** | `tenant_key` auf Location/Slot | nein (Site-Anker) · ja (stempeln) | **ja, in v0072** (SR-022) | schließt die Klasse Cross-Tenant-Lecks strukturell; Site-Anker bleibt als zweite Linie |
| **D-19** | Beetstatus vs. Saisonzustand | ein Enum · getrennt | **getrennt** (W-014): `bed_status` Lebenszyklus, `season_state` abgeleitet | Gründüngung ist eine Pflanzung, keine Brache |
| **D-20** | Slot-Reservierung | exklusiv · Zeitfenster | **Zeitfenster** (F-01) | Nachkultur im selben Jahr ist der Normalfall |
| **D-21** | Fruchtfolge/Mischkultur im MVP | nein · Hinweise ja | **Hinweise ja** (F-12) | Persona bleibt sonst für die Jahresplanung bei Papier |
| **D-22** | `performed_by`-Filter | Leitung/me · alle | **alle Rollen** (SR-020, Betreiber) | Transparenz im Gemeinschaftsgarten; DSFA-Vermerk |
| **D-23** | Offline-Puffer im MVP | ja · nein | **nein** (F-17) | wartet auf UI-NFR-012-Basis; Offline-Hinweis statt stillem Verlust |

---

## 34. Implementierungs-Roadmap

Wellen sind sequenziell abhängig; innerhalb einer Welle sind die Pakete parallelisierbar (ein Agent je Paket, schreibende Agenten auf geteiltem Tree sequenziell — Feedback-Memory). Jede Welle endet mit grünem Quality-Gate, Review (`/code-review`), PR gegen `develop`, und — bei Frontend-Änderungen — der 3-Agent-Kette (Memory `feedback_auto_docs`).

| Welle | Inhalt | Pakete | Abhängig von | Schätzung |
|-------|--------|--------|--------------|-----------|
| **0 — Spec-Abschluss** | ✅ Betreiberentscheidungen O-01…O-15 (2026-10-04); ADR-008 auf Accepted heben; ✅ Agrobiologie-, Outdoor-Persona- und Security-Review (2026-10-04, `spec/analysis/*-req-053.md`); Restliste der Reviews als Issues (Anhang A, 58–66); verbleibende Review (`agrobiology-requirements-reviewer`) und Outdoor-Review (`outdoor-garden-planner-reviewer`) auf dieses Dokument; Security-Spec-Review; `TC-REQ-053.md` aus §30 (`test-case-extractor`); REQ-002/REQ-013/REQ-006-Pins und Querverweise | 5 | — | 1 Woche |
| **1 — Fundament Backend** | v0072 (inkl. `tenant_key` auf Location/Slot) – v0074 + v0076 (Cron→RRULE) + v0077 (NutrientDemand-Split), jeweils mit Dry-Run-Report; `print_engine` `url_fetcher` (Sicherheitskorrektur, zuerst); `calculate_plants_per_m2` mit Reihenabstand; GP-NFR-058 Referenzauflösung + Quoten + Pflicht-Audit; Entfernung von `Location.dimensions` und `Slot.position` samt aller Leser (Backend + Frontend); `Geometry`, `geometry_calculator` + Testvektoren; Site-`plan`, Location-/Slot-/GardenObject-Felder; `garden_plan_service` mit Batch-Transaktion und Containment; Endpunkte GP-API-001–003, 010–015; Tenant-Negativtests; Observability-Events | 6 | 0 | 2 Wochen |
| **2 — Editor-Kern** | `gardenPlanSlice`, Operationen, Undo/Redo; `PlanRenderer` + `SvgPlanRenderer` + Headless-Renderer; Werkzeuge Auswahl/Pan/Beet/Objekte/Polygon; Raster/Snap; Panel; Kontextmenü; Konflikt-Dialog; **Liste-Ansicht + Tastatur + aria-live** (nicht später!); Dynamic Import + Budget-Eintrag; i18n DE/EN; testids; vitest + axe; E2E-Grundlauf | 8 | 1 | 3 Wochen |
| **3 — Beet & Pflanzung** | `is_bed`-Seeds, Beetansicht mit Tabs, Beetliste, Summary; Bodenprofil; Entry-Layout-Felder, `planting_layout_calculator` (py + ts), Preview-Endpunkt, `run_planned_at`, `create-plants`-Anpassung, Pflanzen-Marker, Position korrigieren; Adjacency-Engine + Celery-Task; Bepflanzen-Dialog mit Fruchtfolge-/Mischkultur-Hinweis (Beet-Validator, `rotation_pause_years`); Zeitfenster-Reservierung; Beet räumen; Vorjahr am Beet | 7 | 2 | 3 Wochen |
| **4 — Pflege & Historie** | ADR-008 ist Accepted (Welle 0) und RRULE migriert (Welle 1); `TaskCategory`-Erweiterung; `care_events` + Service + Endpunkte inkl. Redaktion; Rückgängig-Snackbar; Abschluss-Übergang atomar; Batch-Erledigen; Historie-Tab + Zeitstrahl + `rotation`-Endpunkt; DSGVO-Kaskade; Backfill-Migration (SHOULD) | 6 | 1 (parallel zu 2–3 möglich, Merge nach 3) | 2 Wochen |
| **5 — Feldmodus & Export** | Feldmodus (Listen-Einstieg, Sheet, Schnellprotokoll-Chips, Stepper, Sofortspeichern, Offline-Hinweis, Quick-Planting); `plan_svg_engine`, PDF-Vorlage, Print-Endpunkt, JSON-Export; E2E auf 390 px; Lighthouse-Route; Performance-Benchmarks GP-ACC-033/034 | 5 | 3, 4 | 2 Wochen |
| **6 — MVP-Abnahme** | Alle GP-ACC-001…035 grün (Unit/Integration/E2E), ZAP-Negativtests, Docs (MkDocs DE/EN: Nutzerhandbuch „Gartenplan", technische Seite Geometriemodell), Release-Notes, REQ-042-Modul, REQ-032 §2.5-Verweis | 4 | 5 | 1 Woche |
| **7 — SHOULD-Welle A** | Bewässerungszonen (§14), Import mit Dry-Run, Beetvorlagen, Standardgrößen, Objekt-Snap, Ausrichten | 6 | 6 | 3 Wochen |
| **8 — SHOULD-Welle B** | Fruchtfolge-Beet-Validator, Hinweise im Dialog, Mischkultur-Overlay, Rotationsmatrix, Bodenanalyse-Ereignisse, Flächendosierung, Vorschlags-Tasks, Beet-Fotos, CSV | 8 | 6, ADR-008 | 3 Wochen |
| **9 — Offline & Konva** | Offline-Lesen/Puffern (nur wenn UI-NFR-012 repo-weit kommt), Konva-Renderer bei gemessener Schwelle, PNG, GeoJSON | 4 | Messung | nach Bedarf |

Gesamt bis MVP (Wellen 0–6): ~16 Wochen (Review-Zuwachs: Fruchtfolge-/Mischkultur-Hinweis, Beet räumen, Redaktion, Quoten, Referenzauflösung) Kalenderzeit bei einem durchgängigen Strang, kürzer bei paralleler Welle 4.

---

## Anhang A: GitHub-Issue-Kandidaten

Direkt aus den Anforderungen ableitbar; Titel englisch (Feedback-Memory). Labels: `feature`, `spec:REQ-053`, Bereich. Schätzung S/M/L. Reihenfolge = Roadmap.

**Welle 0 — Spec**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 1 | spec(REQ-053): record operator decisions O-01…O-15 — ✅ erledigt mit v1.1 | §32 | S |
| 2 | spec(REQ-053): agrobiology + outdoor-planner + security reviews of garden planning requirements | §30 | M |
| 3 | spec(REQ-053): derive TC-REQ-053 test cases from acceptance criteria | GP-ACC-* | M |
| 4 | spec(REQ-002/013/006): cross-reference REQ-053, mark bed_* fields as superseded | §20.8 | S |
| 5 | spec(ADR-008): set status Accepted (RRULE canonical, single completion transition), update REQ-006 recurrence_rule to RRULE | O-05, §12.2 | M |

**Welle 1 — Backend-Fundament**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 6 | feat(db): migration v0072 garden plan collections/edges/indexes + dimensions→geometry/height_m + Slot.position→geometry (pitch_m, dry-run report); v0073 LocationType.is_bed + seeds; v0074 TaskCategory extension | GP-NFR-015, §9.2a, §20.14, GP-ACC-035/036 | L |
| 6a | refactor(locations)!: remove Location.dimensions and Slot.position from models, schemas, repositories and frontend after v0072 | O-01, O-02, D-16 | M |
| 6b | feat(db): migration v0076 recurrence cron→RRULE with dry-run report; API rejects cron (422 recurrence.rrule_required) | O-05, GP-ACC-038 | M |
| 6c | feat(db): migration v0077 NutrientDemand split (3 levels + nitrogen_fixing bool + PlanRole), BotanicalFamily light/medium/heavy → *_feeder, dry-run report for species without nutrient_demand, seed/schema update | GP-FR-138/139, GP-ACC-037 | M |
| 6d | fix(print)!: restrictive WeasyPrint url_fetcher (no http/file), Jinja autoescape, SVG allowlist — affects existing /print/* (SR-015) | GP-NFR-052, GP-ACC-045 | S |
| 6e | fix(calculators): calculate_plants_per_m2 with row_spacing and strategy; bed-level crop rotation validator with BotanicalFamily.rotation_pause_years | GP-FR-073/131, W-003, K-004 | M |
| 6f | feat(db): v0072 stamps tenant_key on locations/slots + indexes; repositories filter on it | SR-022, D-18, GP-ACC-046 | M |
| 6g | feat(garden-plan): per-operation role check in batch, closed op list, GP-NFR-058 reference resolution, quotas GP-NFR-017, mandatory garden_plan_audit, complexity/time budget | SR-001/003/004/011/012/013, GP-ACC-041/042/043 | L |
| 7 | feat(domain): Geometry value type + geometry_calculator (area, bbox, containment, simple-polygon) with shared test vectors | GP-FR-004–008, GP-NFR-012, GP-ACC-003/004 | M |
| 8 | feat(sites): Site.plan (boundary, north_angle_deg, grid, revision) + PUT /plan/boundary | GP-API-002, GP-FR-015, GP-ACC-001 | S |
| 9 | feat(garden-plan): GET /sites/{key}/plan aggregated read model | GP-API-001, GP-NFR-002/030/031, GP-ACC-034/035 | M |
| 10 | feat(garden-plan): transactional POST /plan/batch with plan revision conflict (409) and containment validation | GP-API-003, GP-NFR-013/014, V-01–V-05, V-14, V-17, V-19, GP-ACC-005/009/010/013 | L |
| 11 | feat(locations): geometry, soil_profile, bed_status, sun_exposure, notes, locked, z_order on Location; PATCH endpoint; status transition endpoint | GP-API-010/018, GP-FR-046, GP-ACC-012/015 | M |
| 12 | feat(garden-objects): garden_objects collection, props union, CRUD endpoints | GP-API-013, §20.4 | M |
| 13 | feat(slots): slot geometry, slot_role, PATCH + batch replace endpoint | GP-API-014/015, §20.5 | M |
| 14 | test(security): cross-tenant negative tests for every garden-plan endpoint | GP-NFR-050, GP-ACC-014 | S |
| 15 | feat(observability): structlog events + Prometheus metrics for garden plan | GP-NFR-060/061 | S |

**Welle 2 — Editor-Kern**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 16 | feat(frontend): gardenPlanSlice with PlanOperation model, undo/redo, dirty state, optimistic save + conflict handling | GP-NFR-005–007, GP-FR-026, GP-ACC-007/011 | L |
| 17 | feat(frontend): PlanRenderer interface + SvgPlanRenderer with viewport culling and CSS-transform drag; headless renderer for tests; ESLint import boundary | GP-NFR-009–011, GP-ACC-033 | L |
| 18 | feat(frontend): editor tools — select, pan, rect/circle/polygon/polyline drawing, handles, rotate, polygon vertex editing | GP-FR-019–023, GP-UX-002/007 | L |
| 19 | feat(frontend): grid + snap (1 cm…1 m), scale bar, zoom levels, compass widget | GP-FR-009–012, 014, 015, GP-ACC-006 | M |
| 20 | feat(frontend): properties panel, context menu, duplicate, delete with confirmation, lock | GP-FR-024/025/027/028/032 | M |
| 21 | feat(frontend): accessibility — list view, keyboard operation, aria-live announcements, focus order | GP-NFR-020–027, GP-ACC-008/032 | L |
| 22 | feat(frontend): garden plan page route, dynamic import, bundle budget entry, i18n de/en, data-testids | GP-NFR-003, GP-UX-012/013, UI-NFR-022 registration | M |
| 23 | test(e2e): garden plan editor baseline (draw, move, save, conflict) desktop + one tent scenario proving no indoor special path | GP-ACC-002/006/007/011/036 | M |

**Welle 3 — Beet & Pflanzung**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 24 | feat(beds): bed detail page with Plan/Planting/Care/Soil/History tabs, bed list with counters, summary endpoint | GP-FR-041/042/047, GP-API-011/012, GP-ACC-016 | L |
| 25 | feat(beds): soil profile editing + substrate linkage | GP-FR-120/121 | S |
| 26 | feat(planting): PlantingRunEntry layout fields + planting_layout_calculator (py + ts) + preview endpoint | GP-FR-060/062/063/073, GP-API-016, GP-ACC-017/018 | L |
| 27 | feat(planting): run_planned_at reservation **with time window** (F-01), plan-slots endpoints, bed clearing endpoint (GP-FR-055), create-plants uses planned slots, plantings-by-state endpoint | GP-FR-064–066, GP-API-020–024, V-08, GP-ACC-019–021 | L |
| 28 | feat(frontend): planting dialog with crop-rotation + companion hints (MVP, F-12), live preview, row assignment for mixed culture, free placement, plant markers, "correct position", previous-year line in bed tooltip | GP-FR-067/068/072, GP-ACC-022 | L |
| 29 | feat(engines): adjacency_engine deriving adjacent_to from slot geometry + Celery task | GP-FR-130, GP-NFR-016, GP-ACC-023 | M |

**Welle 4 — Pflege & Historie**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 30 | feat(care-events): care_events collection, service, append-only supersede/void/**redact** (GP-FR-109), server-side trigger/created_by, endpoints, DSGVO cascade incl. all *_by fields, NFR-011 retention rows (5 y / 1 y), Art. 15/20 export | GP-FR-100/101/107, GP-API-033–037, V-11–V-13, GP-NFR-055, GP-ACC-025/026 | L |
| 31 | feat(tasks): location-bound tasks, queue filter by location, per-plant fan-out, suggested flag | GP-FR-080/081, GP-API-030, §20.9 | M |
| 32 | feat(tasks): atomic completion transition writing care_event + domain event; batch completion with care fields | GP-FR-083–085/088, GP-API-031/032, GP-ACC-024 | L |
| 33 | feat(frontend): bed care tab (complete inline, category-specific quick dialog) | GP-FR-084, GP-FR-089 badge | M |
| 34 | feat(history): combined bed history endpoint, rotation timeline endpoint, history tab UI | GP-FR-102/103, GP-API-038/039, GP-ACC-027/028 | L |
| 35 | feat(db): care_events backfill migration from watering/feeding/treatment/harvest records (SHOULD) | GP-FR-105, v0075 | M |

**Welle 5 — Feldmodus & Export**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 36 | feat(frontend): field mode (list-first entry, bottom sheet, 64 px targets, quick-protocol chips, undo snackbar, stepper default, immediate save, offline notice) + quick-planting endpoint | GP-UX-020–023/025/027, GP-API-017, GP-ACC-029 | L |
| 37 | feat(print): plan_svg_engine + garden plan PDF (finer scale steps, A3 auto-suggest, no personal data by default, preview) + SVG endpoint with allowlist + CSP | GP-FR-142/143, GP-API-006/007, GP-NFR-052, GP-ACC-030 | L |
| 38 | feat(garden-plan): JSON export (schema_version 1) + inclusion in DSGVO data export | GP-FR-140/147, GP-API-004 | M |
| 39 | test(e2e): field mode on 390 px viewport; lighthouse route; performance benchmarks | GP-ACC-029/033/034, GP-NFR-040 | M |

**Welle 6 — Abnahme**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 40 | docs(mkdocs): user guide "Gartenplan" (de/en) + technical page geometry model | NFR-005, DOCS.md | M |
| 41 | feat(modules): register garden_planner module (REQ-042), navigation placement (REQ-021), REQ-032 §2.5 link | O-15 | S |
| 42 | test(security): ZAP nightly negative tests for plan import/batch | GP-NFR-057 | S |

**Wellen 7–9 — SHOULD/COULD (Auswahl)**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 43 | feat(irrigation): irrigation_zones model, endpoints, zone overlay, zone status, log-watering by area | GP-FR-110–114/117, GP-API-050–053 | L |
| 44 | feat(garden-plan): JSON import with dry-run, merge/replace | GP-FR-141, GP-API-005, GP-ACC-031 | M |
| 45 | feat(beds): bed templates + standard sizes + place-template | GP-FR-044/045, GP-API-… §21.7 | M |
| 46 | feat(rotation): bed-level crop rotation validator + hints in planting dialog + rotation matrix | GP-FR-131–133/135, GP-API-025 | L |
| 47 | feat(companion): compatibility overlay on plan | GP-FR-134 | M |
| 48 | feat(soil): soil analysis events, area-based dosing in feeding dialog, amendment materials | GP-FR-122–124 | M |
| 49 | feat(tasks): suggested tasks accept/dismiss (after ADR-008 phase 3) | GP-FR-086, GP-API-040 | M |
| 50 | feat(beds): bed photos (location attachments category) | GP-FR-051 | M |
| 51 | feat(frontend): object snap, align/distribute, mini-map, auto-save option | GP-FR-012/029, GP-UX-004/014 | M |
| 52 | feat(frontend): KonvaPlanRenderer behind PlanRenderer (only if GP-NFR-013 threshold is measured) | D-01 | L |
| 53 | feat(export): PNG client-side, CSV bed list + history, GeoJSON (if GPS + north set) | GP-FR-144–146 | M |
| 54 | feat(offline): plan read cache + offline completion buffer (blocked on UI-NFR-012 baseline) | GP-UX-024 | L |
| 55 | spec(REQ-001/REQ-002): adopt NutrientDemand/nitrogen_fixing/PlanRole from REQ-053 §16.3 and BotanicalFamily.rotation_pause_years (changelog lines, enum tables) | O-07 | S |
| 56 | ~~chore(locations): retire Location.dimensions after geometry adoption~~ → in Welle 1 (Issue 6a) | O-02 | — |
| 57 | feat(knowledge): row_spacing_cm, nutrient_demand (required for crops), rotation_pause_years in plant_info/botanical_families schema; Steckbrief template section; plant-info-to-seed-yaml extraction; validator ranges | O-11, GP-FR-061 | M |

**Restliste aus den Reviews (eigene Issues nur für medium+, Rest als Bündel-Notiz — Feedback-Memory „Folge-Issue-Inflation")**

| # | Titel | Quelle | Größe |
|---|-------|--------|-------|
| 58 | feat(beds): season_state derivation (empty/planted/green_manure/fallow/winter_covered) + bed_status transitions planned→retired, retired→active | W-014, §7.4 | M |
| 59 | feat(soil): soil_profile v2 — growing_medium_kind, soil_texture + finger-test helper, conditions[], site_water_regime, target_ph derivation, established_on, rotation_exempt, mulch_factor; soil_analysis measurements with method/unit/depth | K-002/K-003, W-009/W-011/W-012 | L |
| 60 | feat(planting): sown state for zone/row slots, thinning creates plants, harvesting/failed states, replant suggestion on failed slot | W-015 | M |
| 61 | feat(tasks): TaskCategory additions thinning/hilling/tillage/covering/uncovering/ventilating/clearing/soil_analysis/rainfall/pollinating; context-dependent category offer; organic amendments also write feeding_events | W-006/W-007, F-03 | M |
| 62 | feat(garden-objects): trellis type, heights/opacity/foliage props, off_site flag, tasks on compost/water_source/storage | W-005/W-008, §29 | M |
| 63 | feat(tent): LocationType.supports_layout, Slot.container_volume_l check against species, per-location adjacency_factor, lighting profile fields (SHOULD), photoperiod conflict hint (SHOULD) | W-016 | M |
| 64 | feat(irrigation): application_efficiency, irrigated-area based demand, rainfall intake, zone/location irrigation_type conflict rule, source capacity check, HA entity validation (Technik only) | W-017, SR-014, GP-FR-119 | L (Welle 7) |
| 65 | feat(frontend): bed multi-duplicate with naming scheme, last-watered layer, print preview with scale | F-10, GP-UX-031, F-15 | M (Welle 7) |
| 66 | feat(export): CSV formula hardening, PDF without personal data by default, GeoJSON lead-only | SR-016/SR-024 | S |
| 67 | chore(spec): register REQ-053 testids in UI-NFR-022, module garden_planner in REQ-042, NFR-011 rows care_events/garden_plan_audit, REQ-049 note on Technik vs. actuator command | GP-UX-012, O-15, SR-005, SR-010 | S |

Bündel-Notizen (keine eigenen Issues): H-001 Beetbreiten-Warnung → in 24; H-002/H-003 Feldnamen → in 59; H-005 Tiefenprüfung → in 24; H-007 Lichtdurchlässigkeit → in 62; F-06 MoSCoW-Bereinigung → erledigt in v1.2; F-14 Ergebnisfelder einklappen → in 33; F-18 Schrift/Foto-Standard → in 36; SR-021 Adjacency-Payload → in 29; SR-023 QR → in 36; SR-025 Logging → in 15; SR-028 ha_publish → HA-Dokument.
