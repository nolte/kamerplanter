---
id: F-3
title: Species-Mandanten-Ownership — Feld, Write-Stamping & Cutover-Migration
status: done
roadmap_item: R-14
sprint: 2
created: 2026-08-09
ended: 2026-08-09
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-08-09
  agent_version: feature-consistency-reviewer@27055772e
  findings:
    - kind: drift
      target: src/backend/app/domain/models/species.py:261
      resolution: proceed
      evidence: "Species model carries `origin: DataOrigin` (line 447) but NO `tenant_key` field; REQ-001 v4.0 requires it. Drift-to-spec — the genuine unimplemented core of F-3.acc-1, not a contradiction."
    - kind: prior-art
      target: src/backend/app/api/v1/species/router.py:112
      resolution: proceed
      evidence: "create_species does `Species(**body.model_dump(), origin=DataOrigin.TENANT)` — the single interactive create path (F-3.acc-2). Global paths confirmed: import_service.py:107, species_repository.py:40 upsert_by_normalized_scientific_name (F-3.acc-3). None set tenant_key today."
    - kind: prior-art
      target: src/backend/app/migrations/backfill_tenant_key.py:19
      resolution: proceed
      evidence: "Existing backfill migration stamps a DEFAULT tenant on orphaned docs and deliberately EXCLUDES species from TOP_LEVEL_COLLECTIONS. F-3's cutover migration MUST NOT reuse this default-stamp path — R6 calls default-stamp the #324 regression verbatim."
    - kind: prior-art
      target: src/backend/app/migrations/versions/v0006_backfill_data_origin.py:149
      resolution: proceed
      evidence: "v0006 already classified existing species as origin=system|tenant. The `origin:tenant` population F-3.acc-4 must leave un-stamped is exactly this set; the cutover is a no-stamp/marker migration over an already-classified population."
---

## Description

Neu angelegte Arten gehören künftig dem Mandanten, der sie erstellt: `Species`
erhält ein `tenant_key`-Feld (leer `""` = global/System, analog zum
Hybrid-Katalog), das auf jedem Schreibpfad gesetzt wird. Der einzige interaktive
Create-Pfad stempelt den Tenant des Erstellers; alle globalen Pfade (Import,
Seed, Enrichment, Normalisierungs-Upsert) legen Arten mit leerem `tenant_key`
an. Bestandsdaten werden nach der bestätigten **Cutover-Regel** behandelt: Arten,
die vor der Umstellung als `origin: tenant` angelegt wurden, behalten kein
`tenant_key` und bleiben per expliziter Policy Teil des geteilten Katalogs —
denn welcher Mandant sie erstellt hat, wurde nie erfasst, und ein Default-Stamp
wäre die #324-Regression (jeder Nutzer außer einem verlöre selbst angelegte
Arten). Dieses Feature liefert das Feld, das Stamping und die Cutover-Migration;
das tenant-bewusste Lesen darauf ist F-5.

## Acceptance criteria

- [x] **acceptance-1** Das `Species`-Modell trägt ein `tenant_key`-Feld; ein leerer Wert `""` bedeutet global/System.
- [x] **acceptance-2** Eine über den interaktiven Create-Pfad (`species/router.py`) angelegte Art wird mit dem `tenant_key` des erstellenden Mandanten gestempelt.
- [x] **acceptance-3** Die globalen Schreibpfade (Import, Seed, Enrichment, `upsert_by_normalized_scientific_name`) legen Arten mit leerem `tenant_key` (`""`) an.
- [x] **acceptance-4** Eine neue, idempotente Cutover-Migration lässt Bestands-`origin:tenant`-Arten ohne `tenant_key` (global) und stempelt keinen Default-Tenant; `SPECIES` wird NICHT zu `backfill_tenant_key.py`'s `TOP_LEVEL_COLLECTIONS` hinzugefügt.

## Test hooks

- **acceptance-1** — Unit-Test `Species`-Modell (Feld vorhanden, Default `""`) — passing
- **acceptance-2** — API/Service-Test create_species stempelt Caller-Tenant — passing
- **acceptance-3** — Unit-Tests der globalen Schreibpfade (import/seed/enrichment/upsert) → `tenant_key == ""` — passing
- **acceptance-4** — Migrationstest der Cutover-Migration (Bestands-`origin:tenant` bleibt un-gestempelt; Idempotenz) — passing

## Consistency notes

- **drift (species.py):** REQ-001 v4.0 verlangt `tenant_key` auf `Species`; das
  Modell trägt heute nur `origin` (Provenienz, nicht Ownership). Das ist der
  echte Kern von acceptance-1 — Drift-zur-Spec, kein Widerspruch. Resolution:
  `proceed`.
- **prior-art (Write-Pfade):** Es gibt genau einen interaktiven Create-Pfad
  (`species/router.py:112`, `origin=DataOrigin.TENANT`); die globalen Pfade
  (`import_service.py:107`, `species_repository.py:40`) sind bekannt. acceptance-2/3
  ergänzen dort nur das Stamping. Resolution: `proceed`.
- **prior-art (Default-Stamp-Anti-Pattern):** `backfill_tenant_key.py` löst einen
  Default-Tenant auf und stempelt ihn über `TOP_LEVEL_COLLECTIONS` — `SPECIES`
  ist dort bewusst NICHT enthalten. acceptance-4 muss eine **separate, stampfreie**
  Migration sein; das Hinzufügen von `SPECIES` zu jener Liste würde die
  #324-Regression (R6 verboten) still wieder einführen. Resolution: `proceed`.
- **prior-art (v0006):** `v0006_backfill_data_origin.py` hat Bestands-Species
  bereits als `system`/`tenant` klassifiziert; die Cutover-Migration arbeitet über
  genau diese vorklassifizierte Population. Resolution: `proceed`.

## Risks

- Ein Implementierer könnte „den bestehenden tenant_key-Backfill wiederverwenden"
  und `SPECIES` zu `TOP_LEVEL_COLLECTIONS` hinzufügen — das ist exakt die von R6
  verbotene Default-Stamp-Regression. Die Cutover-Migration MUSS eigenständig und
  stampfrei sein (siehe acceptance-4).
- `Cultivar` teilt dieselbe Lücke (`cultivars/router.py:42` stempelt `origin=TENANT`
  ohne `tenant_key`), ist aber bewusst als Folge-Requirement ausgeklammert (A2/A4);
  bis dahin bleiben Cultivars global sichtbar.
