---
audit-type: phase-0-drift-findings
target-repo: kamerplanter
phase: 0 (Drift-Truthing)
plans-truthed: 6
plans-confirmed-drift: 6
plans-confirmed-sync: 0
created: 2026-04-28
based-on: implementation-plan.md, .audits/req-coverage-audit/REQ-{013,014,015,022,023,024}.md
---

# Phase 0 — Drift-Truthing Befunde

## Zusammenfassung

Ergebnis von 4 parallelen Spec ↔ Code Diffs (REQ-013/14/15/22) plus 2
trivialen Reklassifikationen (REQ-023/24) auf Basis bestehender
MEMORY-Hinweise.

| Plan | Hypothese | Befund | Aktion |
|---|---|---|---|
| REQ-013 | Backend hinkt v2.0 → v2.3 | DRIFT konfirmiert | Slice in Sprint 1B (3 Sub-Tasks + SuccessionPlan separat) |
| REQ-014 | MEMORY hinkt v1.4 → v1.6 | DRIFT konfirmiert (oberflächlich) | Mini-Sync-PR (~3h) |
| REQ-015 | MEMORY hinkt v1.1 → v1.6 | TEILWEISE — iCal/Feed-Drift | Mini-Sync-PR + Follow-Ups |
| REQ-022 | MEMORY hinkt v2.3 → v2.5 | DRIFT konfirmiert (umfangreich) | Slice in Sprint 1B |
| REQ-023 | Service Accounts NICHT impl | bestätigt | Slice in Sprint 1B (Auth-Trio Schritt 2) |
| REQ-024 | RBAC NICHT impl | bestätigt | Slice in Sprint 1B (Auth-Trio Schritt 1) |

**Strategische Erkenntnis**: Phase 0 erzeugt KEINE 5–10-Min-MEMORY-Updates wie
ursprünglich vermutet. Alle 6 Plans bleiben offen und gehen als 6 echte
Slice-/Sync-PRs in Sprint 1B. Der ursprüngliche Plan "Index schrumpft auf ~28"
wird nicht erreicht — Index bleibt bei 32.

## Reconciliation-Update (2026-07-05, post-#299)

> **✅ REQ-013 SuccessionPlan und REQ-022 OverwinteringProfile sind seit #299
> auf `develop` implementiert** — mit echtem Code, Tests und bestandenem
> Coverage-Audit (REQ-013 / REQ-022 = 100 % *Implementiert*). Die unten stehenden
> Drift-Befunde bleiben als historischer Audit-Stand (2026-04-28) erhalten, sind
> aber inline mit **✅**-Markern als aufgelöst gekennzeichnet:
>
> - **SuccessionPlan** (REQ-013) → **#361** (`87e5ec63`): Model + Engine
>   (Szenario-4-Staffelgenerierung), `succession_plans`-Collection +
>   `has_succession_plan`/`succession_at`-Edges,
>   `succession_plan_key`/`clone_from_run_key`/`succession_sequence`/`succession_total`
>   auf `PlantingRun`.
> - **OverwinteringProfile** (REQ-022) → **#360** (`8cd1ee70`): Model + Edges +
>   Repo/Service/API, D5-Winter-Pfad-Invariante (→ 422), Tuber-Zyklus,
>   Winterhärte-Ampel-Widget + `evaluate_winter_hardiness` (REQ-039-Kernlogik).
> - **5 neue ReminderTypes** (`deadheading`, `tuber_dig`, `storage_check`,
>   `spring_uncover`, `winter_protection`) → **#360**: von enum-only nun in den
>   `CareReminderEngine` und beide Producer
>   (`care_reminder_service.get_care_dashboard`,
>   `care_tasks.generate_due_care_reminders`) verdrahtet, inkl. Frost-Hardy- +
>   Self-Cleaning-Guards. `FAMILY_CARE_MAP` hat seine 5 Ornamental-Familien
>   erhalten.
>
> Offen bleiben die übrigen, davon unabhängigen Drift-Befunde (REQ-013
> Detach-Snapshots/Run-Guard, REQ-014/REQ-015-Sync, REQ-022 Run-Owned-Care +
> Outdoor-Presets, REQ-023/REQ-024).

## Reports im Detail

### REQ-013 Pflanzdurchlauf — DRIFT konfirmiert

**Status**: Backend bei v2.0, Spec bei v2.3.

**Synchron**:
- PlantingRun als primäre Verwaltungseinheit mit Run-Level Phase
- PlantDiaryEntry Model + Service + Repository vollständig
- Run CRUD (create/list/get/update/delete)
- PlantingRunEntry Batch-Management & auto-generierte IDs
- Phase Transitions auf Run-Ebene
- Nutrient Plan Assignment zu Run
- Detach-Operation (Basis): kopiert Phase vom Run zur Plant

**Drift**:
- **v2.1 W-003 (REQ-003 §3)**: HTTP 409 `phase.run_owned`-Guard bei direktem
  Phasenwechsel auf Run-gebundenen PlantInstances fehlt
- **v2.2 ADR-001 W-009**: `detach_plant()` Schritt 5 (Treatment-Snapshot) fehlt —
  aktive Run-Treatments werden nicht als geerbte `to_plant`-Edges mit
  `inherited_from_run` + `inherited_at` auf detachte Plant kopiert.
  TreatmentApplication hat keine `inherited_from_run`-/`inherited_at`-Felder
- **v2.3 W-010**: `detach_plant()` Schritt 6 (CareProfile-Snapshot) fehlt —
  Run-CareProfile wird beim Detach nicht als Plant-CareProfile übertragen
- **SuccessionPlan**: ✅ **IMPLEMENTIERT in #361 (`87e5ec63`)** — ehemals
  Model/Repository/Service nicht implementiert, Spec §2 Zeile 217–233,
  `succession_plan_key` auf PlantingRun ignoriert, Staffelanbau-Szenario
  (§1.2 Szenario 4 Salat) nicht umsetzbar. Jetzt: Model + Engine
  (Szenario-4-Staffelgenerierung), `succession_plans`-Collection +
  `has_succession_plan`/`succession_at`-Edges,
  `succession_plan_key`/`clone_from_run_key`/`succession_sequence`/`succession_total`
  auf `PlantingRun`.

**Empfehlung**: Slice in Sprint 1B mit 2 PRs:
1. `feat(planting-run): detach-snapshots + run-membership-guard REQ-013` —
   Treatment-Snapshot + CareProfile-Snapshot + HTTP 409 Guard (Scope: M)
2. `feat(planting-run): succession-plan REQ-013` — eigenes Model + Endpoints
   (Scope: L, eventuell Sprint 2)

### REQ-014 Tankmanagement — DRIFT konfirmiert (oberflächlich)

**Status**: TankFillEvent v1.6-konform, WateringEvent driftet bei Feldnamen.

**Synchron**:
- TankFillEvent: alle v1.6-Felder vorhanden (`water_source` inkl. `MIXED`,
  `water_mix_ratio_ro_percent`, `water_defaults_source`, `base_water_ec_ms`,
  `chlorine_ppm`, `chloramine_ppm`)
- Auto-TankState-Erstellung nach Fill-Event
- `resolve_water_defaults()`-Kaskade (W-021) implementiert mit 4-level cascade
- API-Endpunkte Tank: POST/GET/PUT/DELETE /tanks, /fills, /states, /alerts,
  /maintenance
- WateringEvent-Endpoints: POST /watering-events, GET /watering-events/{key},
  /locations/{location_key}/watering-events, /confirm, /quick-confirm

**Drift** (WateringEvent-Modell, Spec §1 Z. 191–211):
- Spec: `slot_keys: list[str]` — Backend: `plant_keys: list[str]`
  → Mismatch mit Slot-centric Spec-Design
- Spec: `target_ec_ms`, `measured_ec_ms`, `runoff_ec_ms` —
  Backend: `target_ec`, `measured_ec`, `runoff_ec`
  → Einheiten-Suffix fehlt, Inkonsistenz mit TankFillEvent
- Backend hat `channel_id` — nicht in Spec erwähnt
  → entweder in Spec aufnehmen oder entfernen

**Empfehlung**: Mini-Sync-PR (~3h):
- Rename `plant_keys` → `slot_keys` (Dual-Support mit Deprecation-Warning
  zur Schonung der Frontend-Konsumenten)
- Rename EC-Felder mit `_ms`-Suffix (Konsistenz mit TankFillEvent)
- `channel_id` klären (Spec aufnehmen oder Feld entfernen)
- Marker entfernen sobald merged → v1.6 FULL SYNC

### REQ-015 Kalenderansicht — TEILWEISE

**Status**: Aussaatkalender + Saisonübersicht implementiert, iCal/Feed driftet.

**Synchron**:
- Kalenderseite mit 5 Ansichtsmodi (Monat, Woche, Tag, Agenda,
  Aussaatkalender, Saisonübersicht)
- Event-Aggregation aus Tasks (REQ-006) via CalendarAggregationEngine
- Phase-Transitions, Maintenance, Tank-Events, Watering-Events als Timeline
- iCal-Feed-Export (RFC 5545-Basis) mit SUMMARY, DTSTART/DTEND, CATEGORIES,
  X-APPLE-CALENDAR-COLOR
- Feed-CRUD: Erstellen, Auflisten, Bearbeiten, Löschen + Token-Rotation
  (`secrets.token_urlsafe`)
- Sowing Calendar Engine mit Frost-Config (last_frost_date, eisheilige_date)
- Blüte-Balken für Zierpflanzen (ornamental trait), getrennte Perioden
- Season Overview mit 12 Monatskarten
- Responsive Layout (Desktop Grid+Sidebar, Mobile Agenda)
- i18n DE/EN

**Drift**:
- **CF-005 (Spec Z. 94–95)**: CalendarFeed hat kein `expires_at: Optional[datetime]`,
  abgelaufene Feeds liefern kein HTTP 410 Gone
- **CF-007 W-017 (Spec Z. 96–97)**: Light-Modus iCal-Token nicht implementiert —
  abhängig von REQ-027
- **VALARM (Spec Z. 1938)**: ICalGenerator erzeugt keine VALARM-Blöcke
- **PRIORITY + STATUS (Spec Z. 1938)**: ICalGenerator setzt diese Felder nicht
- **Druckversion Aussaatkalender (Spec Z. 1949, Szenario 9)**: weder Backend
  noch Frontend haben Print-Schnittstelle für SowingCalendarView
- **Jahresvergleich via `previous_run_key` (Spec Z. 1960, 2060–2068)**:
  halbtransparente Referenzlinie für Vorjahres-PlantingRun fehlt
- **Filter "Jährlich wiederkehrend" (Spec Z. 1958, 2076–2078)**: Filter
  `□ Jährlich` (annual_repeat: true) in SowingCalendarView fehlt

**Empfehlung**: Mini-Sync-PR + Follow-Ups:
- Mini-Sync-PR (~75 Min): VALARM + PRIORITY + STATUS + `expires_at` + HTTP 410
- Follow-Up Sprint 1C: Light-Modus iCal-Token (W-017, abhängig von REQ-027)
- Follow-Up: Druckversion SowingCalendar (~1h Frontend, koordiniert mit REQ-032)
- Follow-Up: Jahresvergleich-Visualisierung (komplex, 2–3h)
- Marker bleibt bis Mini-Sync-PR merged

### REQ-022 Pflegeerinnerungen — DRIFT konfirmiert (umfangreich)

**Status**: Indoor-Care-Basis v2.3 implementiert, Outdoor/Überwinterung-v2.5 fehlt.

**Synchron** (v2.3-Stand bereits im Code):
- CareProfile-Basis (9 Indoor-Presets: tropical, succulent, orchid, calathea,
  herb_tropical, mediterranean, fern, cactus, custom)
- FAMILY_CARE_MAP Fallback (10 Familien)
- Snooze-Aktion (`snooze_days`-Feld, `/plants/{plant_key}/snooze` Endpoint)
- Adaptive Learning Framework (`adaptive_learning_enabled`, `learned_intervals`)
- Dünge-Guard (Aktivmonate, Dormancy-Phasen)

**Drift** (v2.4/v2.5):
- **OverwinteringProfile (Spec Z. 233–259)**: ✅ **IMPLEMENTIERT in #360
  (`8cd1ee70`)** — ehemals komplett fehlend (kein Datenmodell, keine Edges
  `has_overwintering_profile`/`overwinters_at`, keine Tuber-Zyklus-Logik).
  Jetzt: Model + Edges + Repo/Service/API, D5-Winter-Pfad-Invariante (→ 422),
  Tuber-Zyklus, Winterhärte-Ampel-Widget + `evaluate_winter_hardiness`
  (REQ-039-Kernlogik).
- **Run-Owned CareProfile + Detach-Snapshot W-010 (Spec Z. 47–56)**: Dual-Support
  PlantingRun-zentriert vs. Standalone-Plant nicht implementiert
- **5 neue ReminderTypes (Spec Z. 144–157)**: ✅ **IMPLEMENTIERT in #360** —
  `deadheading`, `tuber_dig`, `storage_check`, `spring_uncover`,
  `winter_protection` sind von enum-only nun in den `CareReminderEngine` und
  beide Producer (`care_reminder_service.get_care_dashboard`,
  `care_tasks.generate_due_care_reminders`) verdrahtet, inkl. Frost-Hardy- +
  Self-Cleaning-Guards.
- **7 fehlende Outdoor-Presets (Spec Z. 128–142)**: Nur `outdoor_annual_veg`,
  `outdoor_perennial` da; fehlen `fruit_tree`, `berry_shrub`, `rose`,
  `frost_tender_tuber`, `frost_tender_container`, `winter_vegetable`,
  `spring_bulb`, `outdoor_annual_ornamental`
- **FAMILY_CARE_MAP (Spec Z. 443–459)**: ✅ **IMPLEMENTIERT in #360** — die 5
  ehemals fehlenden Ornamental-Familien (Violaceae, Primulaceae, Geraniaceae,
  Campanulaceae, Balsaminaceae) sind ergänzt.
- **Deadheading-Guard + Self-Cleaning-Filter (Spec Z. 458)**: ✅ **IMPLEMENTIERT
  in #360** — Prüfung `traits=['self_cleaning']` ist verdrahtet (zusammen mit dem
  Frost-Hardy-Guard).
- **Winterschutz-Ampel + Dashboard-Widget (Spec Z. 427–441, 461–466)**: ✅
  **IMPLEMENTIERT in #360** — Hardiness-Berechnung (`evaluate_winter_hardiness`,
  REQ-039-Kernlogik) + Winterhärte-Ampel-Dashboard-Widget vorhanden.

**Empfehlung**: Slice in Sprint 1B (2 PRs):
1. `feat(care): overwintering-profile + outdoor-presets REQ-022` — neue
   Datenmodelle, Edges, ReminderTypes, FAMILY_CARE_MAP-Erweiterung,
   Deadheading-Guard, Winterhärte-Ampel-Berechnung (Scope: L)
2. `feat(care): run-owned-care-profile-snapshot REQ-022` — gekoppelt mit
   REQ-013-Detach-Snapshot-PR (W-010), gemeinsam ausführen (Scope: M)

### REQ-023 Benutzerverwaltung — Service Accounts fehlen (bestätigt)

**Status**: bekannt — `memory_status_field` sagt "MEMORY v1.7 — Service Accounts
NICHT impl". Plan bleibt: Slice in Sprint 1B (Auth-Trio Schritt 2, nach REQ-024
RBAC).

### REQ-024 Mandantenverwaltung — RBAC fehlt (bestätigt)

**Status**: bekannt — `memory_status_field` sagt "RBAC Permission-Matrix NICHT
impl". Plan bleibt: Slice in Sprint 1B (Auth-Trio Schritt 1, blockiert REQ-023
+ REQ-027).

## Konsequenzen für den Implementierungsplan

1. **Phase 0 abgeschlossen**: 4 Reports erstellt, 0 Marker entfernt.
2. **Sprint 1B aufgebläht**: Statt 3 Auth-PRs jetzt 6+ Slice-PRs in Sprint 1B:
   - REQ-024 RBAC (blockiert REQ-023, REQ-027)
   - REQ-023 Service Accounts
   - REQ-027 Light-Modus
   - REQ-013 Detach-Snapshots + Guard (1 PR) + SuccessionPlan (1 PR, evtl. Sprint 2)
   - REQ-014 WateringEvent-Sync (Mini-PR, parallel möglich)
   - REQ-015 iCal/Feed-Sync (Mini-PR, parallel möglich)
   - REQ-022 Overwintering + Outdoor-Presets (1 PR) + Run-Owned-Care (gekoppelt
     mit REQ-013-Detach-Snapshot-PR)
3. **Index bleibt bei 32**: Phase 0 reduziert keinen Plan auf 100 %.
4. **Status-Prognose revidiert**:

| Status | Heute | nach Phase 0 (revidiert) | nach Phase 1 | nach Phase 2 |
|---|---|---|---|---|
| Implementiert | 40 (57 %) | 40 (57 %) | 46 (66 %) | 53 (76 %) |
| Plans offen | 32 | 32 | 26 | 16 |

5. **Neue Empfehlung Sprint 1B-Reihenfolge**:
   1. REQ-024 RBAC (Foundation) — blockiert 2/3
   2. REQ-023 Service Accounts (parallel zu 4–6 unten)
   3. REQ-027 Light-Modus
   4. REQ-014 WateringEvent-Sync (Quick-Win, parallel ab Tag 1)
   5. REQ-015 iCal/Feed-Sync (Quick-Win, parallel ab Tag 1)
   6. REQ-013 Detach-Snapshots + Guard ⊕ REQ-022 Run-Owned-Care (gekoppelt)
   7. REQ-022 Overwintering + Outdoor-Presets
   8. REQ-013 SuccessionPlan (optional in Sprint 2)
