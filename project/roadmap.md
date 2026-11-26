# Roadmap

Diese Datei ist die Arbeits-Queue, die von `spec/project/roadmap/` geregelt wird.
Jeder Eintrag ist eine Level-3-Überschrift, gefolgt von einem `yaml`-Codeblock
(`id`, `title`, `detail`, `outcomes`, `target_sprint`, `mvp`, `status` — in dieser
Reihenfolge) und einem Freitext-Body. Der Detailgrad (`detail`: `fine` /
`coarse` / `backlog`) und der Status-Lebenszyklus (`status`: `proposed` →
`active` → `done`, dazu `cancelled` aus `proposed`/`active`) werden durch
`roadmap-plan` (Hinzufügen/Ändern) und `roadmap-refine` (Detail-Invariante)
durchgesetzt — nicht von Hand in dieser Datei.

Roadmap-Einträge tragen die IDs `R-1`, `R-2`, … monoton aufsteigend; eine ID wird
über die gesamte Projekt-Lebenszeit nie wiederverwendet. Die Queue startet leer:
Der erste von `roadmap-plan` vergebene Eintrag ist `R-1`. Outcome-IDs (`O-n` in
`goals.md`) sind ein davon unabhängiger Zähler — die Ströme nicht kreuzen.

Die folgenden Phasen sind reine Dokumentation (kein Schema). Einträge werden
ihnen über `roadmap-plan` zugeordnet.

## Phase 1 — Fundament & Kernpflege

<!-- Einträge werden ausschließlich über `roadmap-plan` hinzugefügt. -->

## Phase 2 — Stabilisierung & Betrieb

### R-14 — Stammdaten-Mandanten-Scoping (Species & Cultivar)

```yaml
id: R-14
title: Stammdaten-Mandanten-Scoping (Species & Cultivar)
detail: fine
outcomes: [O-4]
target_sprint: 2
mvp: true
status: done
```

**MVP-Flip (Operator-Entscheid 2026-08-09):** `mvp: false → true`. Erlaubt, weil
`mvp_status` (mission.md) noch nicht `stabilised` ist (`in_progress`) — der
Mission-Spec erlaubt den Flip jederzeit vor der Stabilisierung. Der Operator hat
Species-Mandanten-Isolation (O-4) bewusst in den MVP-Scope gezogen, um Sprint 2
jetzt umzusetzen (überschreibt die frühere Zurückstellung).

Species und Cultivar erhalten echte Mandanten-Ownership (REQ-001 v4.0): ein
`tenant_key` auf beiden Modellen, auf jedem Write-Pfad gesetzt, plus ein
geteiltes #324-Union-Leseprädikat statt der heute 3–4-fach duplizierten
Inline-AQL — so bleiben globale Seed-Stammdaten für alle sichtbar, während
tenant-eigene Records nicht mehr an fremde Mandanten leaken. Umfasst als
Architektur-Teil die bislang fehlende Tenant-Auflösung für globale-aber-
tenant-bewusste Routen (heute ist `get_current_tenant` an `/t/{slug}/` gebunden)
und eine Migration, die die zu bestätigende **Cutover-Backfill-Policy** trägt
(Bestands-`origin:tenant`-Species bleiben per Policy global). Entblockt durch
#780 / REQ-049.

Sprint 2 liefert den **species-only**-Schnitt (Cultivar und die
`tenant_has_access`-Edge sind bewusst als Folge-Requirement zurückgestellt,
Operator-Entscheid „Species-only zuerst"). Backfill = **Cutover-Regel** (final,
teach-back-bestätigt). Requirement: `project/requirements/species-tenant-ownership.md`.

- [x] F-3 — Species-Mandanten-Ownership: Feld, Write-Stamping & Cutover-Migration (`species-tenant-key-and-cutover`)
- [x] F-4 — Geteiltes Mandanten-Union-Leseprädikat (Extraktion) (`tenant-scope-union-predicate`)
- [x] F-5 — Tenant-bewusstes Species-Lesen auf der globalen Route (`species-tenant-aware-read`)

<!-- Herkunft: Issue #808 (issue-orchestrate → roadmap-plan, 2026-08-09).
Requirements-Override (Operator): die τ_high-Erhebung via `requirements-elicit`
erfolgt beim `promote`→`fine` / Sprint-Pull, nicht jetzt (Item ist `coarse` und
ungeplant). Die Backfill-Cutover-Policy ist ein Kandidat, final in der
Feature-Zerlegung zu bestätigen. -->

### R-15 — ADR-008: Tasks/Care/Notifications auf eine Recurrence-Engine & einen Propagationspfad konsolidieren

```yaml
id: R-15
title: ADR-008 — Tasks/Care/Notifications auf eine Recurrence-Engine & einen Propagationspfad konsolidieren
detail: fine
outcomes: [O-8]
target_sprint: null
mvp: false
status: proposed
```

Drei Subsysteme (Tasks/REQ-006, Care-Reminders/REQ-022, Notifications/REQ-030)
implementieren dieselbe Fälligkeit-/Sichtbarkeit-/Wiederholung-/Propagation-Logik
dreifach — zwölf Issues im letzten Monat waren Symptome dieser einen Duplikation
(Cluster I / Meta-Pattern M5). Dieses Outcome führt **ADR-008** aus: jede
Next-Occurrence-Berechnung geht durch die einzige `RecurrenceEngine`, jeder
Notification-Write durch den einzigen `NotificationPropagationService`,
done/skipped/rescheduled wird eine geteilte Transition, und die Grenzen werden in
`BACKEND.md` plus einem mechanischen Gate (nach #1046-Muster) eingefroren. Fünf
shippbare Phasen (0 Inventar-Baseline → 1 Recurrence → 2 Propagation → 3
Completion-Transition → 4 Freeze); ADR-008 wird dabei von `Proposed` auf
`Accepted` gehoben.

<!-- Herkunft: Issue #1061 (issue-orchestrate → roadmap-plan, 2026-08-09).
Promotion coarse→fine am 2026-08-10: requirements-elicit abgeschlossen
(project/requirements/adr008-recurrence-consolidation.md, U_gate 0.8 = τ_high)
und in F-6..F-10 dekomponiert (feature-decompose, consistency-checked).
Phase-0-Baseline ist computed (NFR-018 §2.1). ADR-008-Acceptance ist die
Go/No-Go-Entscheidung dieses Outcomes. -->

### R-17 — Einstellungsseite in Gruppen mit Seitennavigation umbauen

```yaml
id: R-17
title: Einstellungsseite in Gruppen mit Seitennavigation umbauen
detail: fine
outcomes: [O-1, O-5]
target_sprint: 3
mvp: true
status: done
```

**MVP-Flip (Operator-Entscheid 2026-11-17):** `mvp: false → true`, damit Sprint 0003 starten kann. Erlaubt, weil `mvp_status` (mission.md) noch `in_progress` ist; gleiches Vorgehen wie bei R-14 (2026-08-09).

Die Einstellungsseite verliert ihre horizontal scrollende Leiste mit bis zu 14
Tabs. Stattdessen gliedert eine Seitennavigation (Desktop) bzw. eine
Gruppenliste mit Detailansicht (mobil) die Einstellungen in sechs Gruppen:
Profil & Konto, Anzeige & Verhalten, Benachrichtigungen, Sicherheit & Zugang,
Integrationen und — sichtbar abgesetzt, nur für Betreiber — Installation.
Alle bestehenden Einstellungen bleiben genau einmal erreichbar, die
Sichtbarkeits-Gates bleiben unverändert; die Plattform-Einstellungen ziehen in
den Admin-Bereich.

- [x] F-12 — Plattform-Einstellungen im Admin-Bereich (`platform-settings-in-admin`) — zuerst
- [x] F-11 — Gruppierte Einstellungsnavigation (`settings-grouped-navigation`)

<!-- Herkunft: Issue #2935 (issue-backlog-partition 2026-11-16 → requirements-elicit →
roadmap-plan, 2026-11-17). Anforderungs-Gate erfüllt:
project/requirements/settings-page-grouping.md (U_gate 0.8 = τ_high, Sättigung).
Outcomes O-1/O-5 gewählt, weil keines der Outcomes die Einstellungsseite exakt
trifft (O-1: Nutzer ohne Vorwissen finden ihre Einstellungen; O-5: Betreiber-
Einstellungen getrennt von persönlichen). #2934 (Wetter-Abrufintervall) baut auf
der Gruppe „Installation“ auf. -->

### R-18 — Konfigurierbarer Wetterabruf mit manuellem Start

```yaml
id: R-18
title: Konfigurierbarer Wetterabruf mit manuellem Start
detail: fine
outcomes: [O-5, O-2]
target_sprint: 3
mvp: true
status: done
```

**MVP-Flip (Operator-Entscheid 2026-11-17):** `mvp: false → true`, damit Sprint 0003 starten kann. Erlaubt, weil `mvp_status` (mission.md) noch `in_progress` ist; gleiches Vorgehen wie bei R-14 (2026-08-09).

Der Wetterabruf läuft heute fest einmal täglich um 06:00. Künftig stellt der
Plattform-Admin das Abrufintervall in Stunden ein (mindestens und
standardmäßig 6 h, also höchstens viermal täglich), startet bei Bedarf einen
Abruf von Hand und sieht, wann der letzte erfolgreiche Abruf war und wann der
nächste ansteht. Nach jedem erfolgreichen Abruf werden Frost-Frühwarnung und
Bewässerungsbedarf neu berechnet, statt nur einmal am Tag.

- [x] F-13 — Intervallgesteuerter Wetterabruf mit manuellem Start (`weather-fetch-scheduling`)
- [x] F-14 — Wetterabruf-Einstellungen in der Installations-Gruppe (`weather-fetch-settings-ui`) — nach F-11

<!-- Herkunft: Issue #2934 (issue-backlog-partition 2026-11-16 → requirements-elicit →
roadmap-plan, 2026-11-17). Anforderungs-Gate erfüllt:
project/requirements/weather-fetch-interval.md (U_gate 0.8 = τ_high, Sättigung).
Outcomes: O-5 (Betreiber steuert den Betrieb), O-2 (frischere Frost- und
Bewässerungsempfehlungen). Sensor-Niederschlag im Bewässerungsbedarf
ausgegliedert nach #3002. -->

### R-19 — Mandanten-Export/-Import vollständig und in realistischer Größe

```yaml
id: R-19
title: Mandanten-Export/-Import vollständig und in realistischer Größe
detail: fine
outcomes: [O-5, O-4]
target_sprint: null
mvp: true
status: proposed
```

Export und Import eines Mandanten sind geliefert (#2267 ff.), stellen einen
Garten aber noch nicht vollständig und nur bis rund 50 MiB wieder her.
Künftig kommen Archive bis etwa 500 MiB durch (größere werden verständlich
abgelehnt), die Sensor-Historie (Rohdaten, Stunden- und Tageswerte) wird beim
Import mit wiederhergestellt, und der Plattform-Admin prüft ein Archiv vorab,
ordnet die Mitglieder per E-Mail des Zielkontos zu und sieht frühere Importe
in einer Liste.

- [ ] F-15 — Archivgrößen bis ~500 MiB mit klarer Grenze (`tenant-archive-size-limits`)
- [ ] F-16 — Sensor-Historie beim Import wiederherstellen (`tenant-readings-import`)
- [ ] F-17 — Import-Vorprüfung mit E-Mail-Zuordnung und Importliste (`tenant-import-preflight`) — nach F-15

<!-- Herkunft: Issue #2138 (MT-042; issue-backlog-partition 2026-11-16 → requirements-elicit →
roadmap-plan, 2026-11-17). Anforderungs-Gate erfüllt:
project/requirements/tenant-export-import-remainder.md (U_gate 0.8 = τ_high, Sättigung).
Outcomes: O-5 (Backups/Wiederherstellung), O-4 (Umzug eines Gemeinschaftsgartens).
Archiv bleibt ohne E-Mail (REQ-056 E-09). -->

### R-20 — Bodengefahren und bodenbürtige Ausfälle beim Nachpflanzen

```yaml
id: R-20
title: Bodengefahren und bodenbürtige Ausfälle beim Nachpflanzen
detail: fine
outcomes: [O-2, O-1]
target_sprint: 4
mvp: true
status: active
```

**MVP-Flip (Operator-Entscheid 2026-11-22):** `mvp: false → true`, damit Sprint 0004 starten kann. Erlaubt, weil `mvp_status` (mission.md) noch `in_progress` ist; gleiches Vorgehen wie bei R-14, R-17 und R-18.

Fällt eine Pflanze aus, unterscheidet der Nachpflanz-Hinweis heute nur grob
nach Krankheit, Schädling oder unbekannt. Künftig hält der Gärtner fest, ob
der Ausfall bodenbürtig war; ein bestätigter Befall mit einem dauerhaften
Bodenerreger (z. B. Kohlhernie, Weißfäule) wird als Bodengefahr des Beets
gespeichert. Nachpflanz-Hinweis und Fruchtfolgeprüfung warnen dann gezielt
für die betroffenen Wirtspflanzen und so lange, wie die belegte Anbaupause
reicht — nie als harte Sperre. Frisches Substrat im Kübel hebt die Warnung
auf; „dieselbe Saison" richtet sich nach dem Anbaufenster der ersetzten
Pflanze.

- [ ] F-18 — Wissenstabelle Bodengefahren mit Belegstatus (`soil-hazard-knowledge`) — zuerst, Spec vor Code
- [ ] F-19 — Ursachenklasse am Ausfall (`failure-cause-class`)
- [ ] F-20 — Bodengefahren am Beet (`bed-soil-hazards`)
- [ ] F-21 — Bodengefahren im Nachpflanz-Hinweis (`soil-aware-replant-hint`)

<!-- Herkunft: Issue #2888 (REQ-053 §11.3 W-015 → REQ-054 H-10; issue-backlog-partition
2026-11-16 → requirements-elicit → roadmap-plan, 2026-11-17). Anforderungs-Gate erfüllt:
project/requirements/soil-hazards-replant.md (U_gate 0.8 = τ_high, Sättigung). Fachgrundlage:
spec/analysis/agrobiology-soil-hazards-research-2888.md. Unabhängig vom REQ-054-Planer
gebaut, der die Daten später liest. E-10: nur 3/3-belegte Werte steuern die Warndauer;
Nachrecherche als eigenes Issue. -->

### R-21 — Mehrere Dashboards mit Ansichten und handlungsfähige Pflege-Widgets

```yaml
id: R-21
title: Mehrere Dashboards mit Ansichten und handlungsfähige Pflege-Widgets
detail: fine
outcomes: [O-1, O-2]
target_sprint: null
mvp: true
status: proposed
```

Heute hat jeder Nutzer genau ein Dashboard, für alle Gärten gleich, und die
meisten Pflege-Widgets zeigen nur Zahlen. Künftig legt jeder Nutzer pro
Garten (Mandant) bis zu zehn Dashboards mit je bis zu zehn Ansichten an —
etwa „Wohnzimmer“, „Gewächshaus“, „Balkon“ — wechselt per Auswahl und Tabs
und fügt Widgets direkt auf dem Dashboard hinzu, auch mehrfach mit eigenem
Filter. Aufgaben, Pflege-Erinnerungen und die Pflanzenübersicht zeigen
Pflanze, Fälligkeit und Dringlichkeit und lassen sich direkt abhaken. Das
bisherige Layout wird übernommen.

- [ ] F-22 — Dashboard-Modell v3 pro Nutzer und Mandant (`dashboard-model-v3`) — zuerst
- [ ] F-23 — Dashboards und Ansichten verwalten (`dashboard-and-view-management`)
- [ ] F-24 — Handlungsfähige Pflege-Widgets (`actionable-care-widgets`)

<!-- Herkunft: Epic #2502 (issue-backlog-partition 2026-11-16 → requirements-elicit →
roadmap-plan, 2026-11-17). Anforderungs-Gate erfüllt: project/requirements/multi-dashboard.md
(U_gate 0.8 = τ_high, Sättigung). Erstes Release = Kern A (Dashboards/Ansichten) + B
(Pflege-Widgets); Vorlagen in R-22, Teilen/Tenant-Default (REQ-045 Phase 2) und
Sensor-/HA-Widgets später. -->

## Phase 3 — Erweiterung & Intelligenz

### R-1 — Pflanzenfoto-Galerie

```yaml
id: R-1
title: Pflanzenfoto-Galerie
detail: fine
outcomes: [O-2]
target_sprint: 1
mvp: true
status: done
```

Pflanzen-Besitzer laden eigene Fotos ihrer Pflanzen hoch und sehen sie als
chronologische Galerie je Pflanze — so dokumentieren und verfolgen sie den
Wachstumsverlauf visuell über die gesamte Lebensphase. Die Bilder werden über
das bestehende, admin-konfigurierbare Object-Storage-Backend (local-fs/S3,
NFR-013) abgelegt und sind in die DSGVO-Löschung eingebunden. Kanonische
Anforderung ist die bereits vorhandene Spec REQ-034.

**Status: abgeschlossen (`done`).** Geliefert via PR #246 (`feat/plant-gallery`,
Squash `f473cc19`, 2026-06-20) — Backend und Frontend-Galerie vollständig.

- [ ] F-1 — Foto-Upload & Speicherung (`plant-photo-upload`)
- [ ] F-2 — Pflanzenfoto-Galerie-Ansicht (`plant-photo-gallery`)

<!-- Der ursprünglich vorgesehene `dinov2-embedding-hook` entfällt als eigenes
Feature: Die DINOv2-Infrastruktur existiert bereits (REQ-029-A), und der optionale
Referenz-Rückfluss ist in REQ-034 §4 spezifiziert. Konsistenzprüfung 2026-06-20,
resolution: merge-into REQ-034. -->

### R-16 — REQ-053 Welle 8 — Standortmerkmale, Backfill & EC-Skalierung im Gartenplan

```yaml
id: R-16
title: REQ-053 Welle 8 — Standortmerkmale, Backfill & EC-Skalierung im Gartenplan
detail: coarse
outcomes: [O-4]
target_sprint: null
mvp: false
status: proposed
```

Welle 8 des grafischen Gartenplans (REQ-053 §34): M4-Backfill und Konsistenz-Job
(E-11), EC-Skalierung mit Agrobiologie-Review (E-17) und GP-FR-161–168
(Mikroklima/Frostrisiko je Beet, Wind, Hang, Erreichbarkeit). Offene Issues der
Welle: #2515, #2516, #2569 (GitHub-Milestone „REQ-053 Welle 8").

<!-- Herkunft: Issue #2494 (WP 7.28, issue-backlog-partition 2026-11-01 → roadmap-plan).
Anforderungs-Gate: Operator-Override 2026-11-01 — Grundlage ist die Spec REQ-053 v1.9
(kein project/requirements-Artefakt). Outcome O-4 gewählt, weil keines der Outcomes den
Gartenplan exakt trifft. -->

### R-22 — Thematische Dashboard-Vorlagen

```yaml
id: R-22
title: Thematische Dashboard-Vorlagen
detail: backlog
outcomes: [O-1]
target_sprint: null
mvp: false
status: proposed
```

Editierbare Startvorlagen für Zimmerpflanzen, Balkon, Gemüsegarten, Gewächshaus und Hydrokultur auf Basis von R-21, nur mit funktionierenden Widgets und echten Daten.

<!-- Herkunft: Epic #2502 Workstream 6, aus dem ersten Release ausgegliedert (Betreiberentscheid 2026-11-17). -->

### R-23 — Plant Social Welle 1: Ereignisindex und Pflanzen-Timeline

```yaml
id: R-23
title: Plant Social Welle 1 — Ereignisindex und Pflanzen-Timeline
detail: fine
outcomes: [O-1, O-2]
target_sprint: null
mvp: true
status: proposed
```

Jede Pflanze bekommt eine Timeline: eine chronologische Sicht auf alles, was
mit ihr passiert ist — Tagebuch, Gießen, Düngen, Phasenwechsel, Fotos,
Ernte — mit Herkunftskennzeichen (Mensch, Kamerplanter, Sensor, Import …).
Ein Ereignisindex sammelt die Ereignisse aus ihren Quellen, ohne einen
zweiten Erfassungsweg; der Bestand wird nachgetragen. Die Timeline ist ohne
jede Social-Funktion nützlich und die Grundlage für Profil (R-24) und
Mastodon (R-25). Grundlage: REQ-055 v1.5 §10, §11, §37 Welle 1.

- [ ] F-25 — Ereignis-Recorder und Anbindungs-Inventar (`plant-event-recorder`)
- [ ] F-26 — Nachtragen und Abgleich des Ereignisindex (`plant-event-backfill`)
- [ ] F-27 — Timeline-Tab an der Pflanze (`plant-timeline-tab`)

<!-- Herkunft: #2140/#2141 (MT-047/MT-048) → Betreiberentscheid 2026-11-16 „mit REQ-055
umsetzen"; roadmap-plan 2026-11-17. Anforderungs-Gate: Operator-Override 2026-11-17 —
Grundlage ist REQ-055 v1.5 (alle offenen Punkte O-01…O-20 entschieden, Security- und
Casual-User-Review eingearbeitet); kein project/requirements-Artefakt. -->

### R-24 — Plant Social Welle 2: öffentliches Pflanzenprofil und Link

```yaml
id: R-24
title: Plant Social Welle 2 — öffentliches Pflanzenprofil und Link
detail: coarse
outcomes: [O-1, O-7]
target_sprint: null
mvp: false
status: proposed
```

Pflanzen erhalten eine optionale Identität mit öffentlichem Profil unter
`/p/{slug}` bzw. einem teilbaren Link — ohne Provider; enthält die
Allowlist-Projektion aus #2141 (MT-048), opake Medien-URLs mit EXIF-Invariante
und die Änderung der Sichtbarkeit je Ereignis (PS-EVT-005, aus R-23 verschoben) (REQ-055 §37 Welle 2; die feldgenaue DSGVO-Einbindung der Ereignisse ist nach R-23 vorgezogen).

<!-- Herkunft: REQ-055 §37 Welle 2; #2141 Teil Projektion. Promotion auf fine via roadmap-refine. -->

### R-25 — Plant Social Welle 3: Mastodon (MVP komplett)

```yaml
id: R-25
title: Plant Social Welle 3 — Mastodon-Anbindung (MVP komplett)
detail: coarse
outcomes: [O-1, O-7]
target_sprint: null
mvp: false
status: proposed
```

Verknüpfung mit Mastodon (OAuth mit Sitzungsbindung), manuelle und
automatische Posts aus Ereignissen mit Freigabe, Limits und Kill-Switch;
enthält den mandanteneigenen Credential-Store aus #2140 (MT-047) sowie
Outbound-Budget und Guard aus #2141 (MT-048) (REQ-055 §37 Welle 3).

<!-- Herkunft: REQ-055 §37 Welle 3; #2140, #2141 Teil Budget/Guard. Promotion auf fine via roadmap-refine. -->

### R-26 — Plant Social Wellen 3b–6: Komfort, Sensoren, KI, Ausbau

```yaml
id: R-26
title: Plant Social Wellen 3b–6 — Komfort, Sensor-Ereignisse, KI, Ausbau
detail: backlog
outcomes: [O-1]
target_sprint: null
mvp: false
status: proposed
```

Profil-Sync, Statistiken, Atom-Feed, weitere Fediverse-Server, Sensor-Ereignisse, KI-Texte und Ausbau gemäß REQ-055 §37 Wellen 3b–6.

<!-- Herkunft: REQ-055 §37 Wellen 3b–6. -->

### R-27 — Gemessener Regen und Bodenwasser-Bilanz im Gießbedarf

```yaml
id: R-27
title: Gemessener Regen und Bodenwasser-Bilanz im Gießbedarf
detail: fine
outcomes: [O-1, O-6]
target_sprint: null
mvp: true
status: proposed
```

Hat es geregnet, obwohl die Prognose trocken war, soll Kamerplanter nicht mehr
zum Gießen raten. Ein Regenmesser (z. B. Netatmo über Home Assistant), heute schon als
Wetterquelle bindbar, liefert die gemessene Tagessumme künftig neben der Prognose. Der Gießbedarf wird zu
einer mehrtägigen Bodenwasser-Bilanz nach FAO-56, die gemessenen Regen der
Vortage berücksichtigt; ohne frischen Messwert gilt die Prognose. Deckt der
Regen den Bedarf, verschiebt Kamerplanter die Gießerinnerung mit Vermerk, und
der Nutzer kann sie zurückholen.

- [ ] F-28 — Gemessener Regen neben der Prognose (`site-rain-sensor`)
- [ ] F-29 — Bodenwasser-Bilanz im Gießbedarf (`soil-water-balance`) — Modell vorab agrarbiologisch prüfen
- [ ] F-31 — Wasserbilanz-Widget mit gemessenem Regen (`water-balance-widget`)
- [ ] F-30 — Gießerinnerung nach gemessenem Regen verschieben (`rain-deferred-watering-reminder`) — nach F-28, F-29 und F-31

<!-- Herkunft: Issue #3002 (issue-backlog-partition 2026-11-17 → requirements-elicit →
roadmap-plan, 2026-11-17). Anforderungs-Gate erfüllt:
project/requirements/measured-rain-soil-water-balance.md (U_gate 0.8 = τ_high, Sättigung).
Outcomes: O-1 (Pflege passend zur tatsächlichen Witterung), O-6 (Smart-Home-Sensor
fließt in die Empfehlung). Abgespalten aus #2934 (R-18). -->
