---
id: F-26
title: Nachtragen und Abgleich des Ereignisindex
status: draft
roadmap_item: R-23
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@4a3321288
  findings:
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:617
      resolution: proceed
      evidence: "PS-SOC-023 (:617) says backfill/import/reconcile events never create posts while PS-EVT-015 (:492), Anhang F (:2107) and AB-26 (:1103) only say never auto; operator decision: never posts, spec cleaned up."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:392
      resolution: proceed
      evidence: "PS-EVT-006: backfill events get visibility = internal and come from a backfill task; added to acceptance-1 (first call enqueues, no write inside GET)."
    - kind: prior-art
      target: src/backend/app/tasks/routing.py:57
      resolution: proceed
      evidence: "QUEUES = (critical, default, bulk); PS-NFR-001 (:1455) asks for a social queue; MT-051 guard (test_every_task_is_scheduled_or_dispatched.py:45) requires a beat entry for the reconcile task; operator decision: bulk queue now."
    - kind: prior-art
      target: src/backend/app/api/v1/auth/router.py:124
      resolution: proceed
      evidence: "tenant_rate_limit_key is used for tenant limits (garden_plan/tenant_router.py:626, bed_templates/tenant_router.py:101); one run per plant needs a Redis SETNX lock (REQ-055:1442)."
    - kind: prior-art
      target: project/features/tenant-archive-size-limits.md
      resolution: proceed
      evidence: "Imported tenants get new keys (F-15..F-17); operator decision: plant_events EXCLUDED from the archive and rebuilt by backfill after import."
---

## Description

Ein Ereignisindex, der erst ab heute zählt, zeigt bei bestehenden Pflanzen
einen leeren Verlauf, obwohl Tagebuch, Gießprotokolle und Phasenhistorie
längst Daten enthalten. Zudem kann ein Ereignis verloren gehen, wenn das
Schreiben nach dem fachlichen Speichern scheitert.

Nach dieser Änderung wird der Bestand nachgetragen: für alle Pflanzen per
Migration und für eine einzelne Pflanze beim ersten Öffnen ihres Verlaufs.
Nachgetragene Ereignisse tragen ihren fachlichen Zeitpunkt, sind als
„nachgetragen“ gekennzeichnet und bleiben intern. Ein Gärtner kann das
Nachtragen für eine Pflanze auch selbst anstoßen und vorher sehen, wie viele
Ereignisse entstehen würden. Ein regelmäßiger Abgleich holt verpasste
Ereignisse nach, ohne Doppelte zu erzeugen. Nach einem Mandanten-Import baut
das Nachtragen den Verlauf neu auf. Nachgetragene, abgeglichene und
importierte Ereignisse führen nie zu einem Post.

## Acceptance criteria

- [ ] **acceptance-1** Der Bestand wird idempotent nachgetragen — per Migration für alle Pflanzen und beim ersten Öffnen des Verlaufs einer Pflanze über einen eingestellten Hintergrundauftrag —, mit fachlichem Zeitpunkt, Herkunft „nachgetragen“ und Sichtbarkeit „intern“.
- [ ] **acceptance-2** Ein Gärtner stößt das Nachtragen für eine Pflanze an und kann vorher die Anzahl sehen; je Pflanze läuft höchstens ein Lauf, je Mandant höchstens 20 pro Stunde.
- [ ] **acceptance-3** Ein regelmäßiger Abgleich erzeugt verpasste Ereignisse nach, ohne Doppelte.
- [ ] **acceptance-4** Nach einem Mandanten-Import ist der Verlauf jeder Pflanze aus ihren Quellen wieder aufgebaut.
- [ ] **acceptance-5** Nachgetragene, abgeglichene und importierte Ereignisse sind dauerhaft so gekennzeichnet, dass sie nie einen Post auslösen; REQ-055 (PS-EVT-015, AB-26, Anhang F) stimmt mit PS-SOC-023 überein.

## Test hooks

- **acceptance-1** — migration dry-run/apply test; GET timeline enqueues without writing; idempotency via unique index — pending
- **acceptance-2** — router tests: dry-run count, 409 while running, 429 at 21/h (`tenant_rate_limit_key`) — pending
- **acceptance-3** — task test: deleted event re-created once; beat entry satisfies MT-051 guard — pending
- **acceptance-4** — tenant import roundtrip test rebuilds events — pending
- **acceptance-5** — model test of the origin flag + spec diff review — pending

## Consistency notes

**Reconcile posting rule (drift, proceed).** Established: PS-SOC-023
(`REQ-055:617`) says backfill, import and reconciliation events never create
posts; PS-EVT-015 (`:492`), Anhang F (`:2107`) and AB-26 (`:1103`) only forbid
`auto`. Operator decision 2026-11-17: never posts; the spec is cleaned up
(acceptance-5).

**Backfill visibility and trigger (drift, proceed).** Established: PS-EVT-006
(`:392`) sets `visibility = internal` and uses a task. Operator decision
2026-11-17: the first timeline call enqueues the task instead of writing in a
GET (acceptance-1).

**Queue (prior-art, proceed).** Established: `routing.py:57` has `critical`,
`default`, `bulk`; PS-NFR-001 (`:1455`) asks for a `social` queue; the MT-051
guard (`test_every_task_is_scheduled_or_dispatched.py:45`) requires a beat
entry. Operator decision 2026-11-17: `bulk` now, `social` with wave 3.

**Rate limits (prior-art, proceed).** Established: `tenant_rate_limit_key`
(`auth/router.py:124`) serves tenant limits elsewhere
(`garden_plan/tenant_router.py:626`); the per-plant run needs a Redis lock
(`REQ-055:1442`).

**Tenant import (prior-art, proceed).** Established: imported tenants get new
keys (F-15..F-17). Operator decision 2026-11-17: `plant_events` is excluded
from the archive and rebuilt by this backfill after import (acceptance-4).

## Risks

- Backfill of large tenants runs long on the shared `bulk` queue; the per-tenant limit bounds manual runs only.

## References

- REQ-055 v1.5 §10.2, §24; roadmap item R-23; after F-25
- Requirement gate: operator override 2026-11-17 (REQ-055 v1.5 as basis)
