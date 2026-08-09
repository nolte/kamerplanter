---
number: 2
status: active
started: 2026-08-09
ended: null
value_statement: Gemeinschaftsgarten-Mitglieder sehen im Arten-Katalog nur die gemeinsamen und ihre eigenen Arten — privat angelegte Arten anderer Mandanten bleiben verborgen.
artifact_ref: null
last_commit: 85960e9c5
roadmap_items: [R-14]
features: [F-3, F-4, F-5]
---

## Goal

Gemeinschaftsgarten-Mitglieder sehen im Arten-Katalog nur die gemeinsamen
(globalen Seed-)Arten und ihre eigenen — privat angelegte Arten anderer
Mandanten bleiben verborgen. Dazu bekommt `Species` echte Mandanten-Ownership
(REQ-001 v4.0, Roadmap-Item R-14): ein `tenant_key`-Feld auf jedem Write-Pfad
(F-3, inkl. der Cutover-Migration, die Bestandsarten per Policy global lässt),
ein einziges geteiltes Union-Leseprädikat statt der heute mehrfach duplizierten
Inline-AQL (F-4), und das tenant-bewusste Lesen auf der bislang globalen
Species-Route über einen neuen Tenant-Auflösungs-Mechanismus (F-5). Dieser Sprint
liefert den **species-only**-Schnitt; Cultivar und die `tenant_has_access`-Edge
sind bewusst als Folge-Requirement zurückgestellt. Der value-verifizierende
Nachweis ist F-5 `acceptance-2`: eine Art eines fremden Mandanten erscheint nicht
in der Liste eines anderen Mandanten.

Umsetzungsreihenfolge (Abhängigkeit): **F-3 → F-4 → F-5** — das Leseprädikat von
F-5 ist inert, bis F-3 den `tenant_key` liefert, und nutzt den Helfer aus F-4.

**Mission-Scope-Vermerk / Zurückstellung (Operator-Entscheid 2026-08-09):** R-14
trägt Outcome **O-4** (Gemeinschaftsgarten-Verwalter), das bewusst **nicht** in
den `relevant_outcomes` der Mission steht — der aktuelle MVP ist der Home-Grower
(`O-1/2/3/5/8`). R-14 ist damit **post-MVP** (`mvp: false`). Der
`sprint-readiness-reviewer` hat die Aktivierung korrekt als NO-GO blockiert:
`planned → active` feuert nur über ein Feature `ready → in_progress`, und dieser
Übergang ist für ein post-MVP-Item gesperrt, solange `mvp_status` nicht
`stabilised` ist (aktuell `in_progress`). Dieser Sprint bleibt daher **`planned`
und wird zurückgestellt**, bis der MVP stabilisiert ist; die Planung (Sprint +
F-3/F-4/F-5 + Requirement) ist vollständig und startklar, sobald das Gate fällt.
Die Planung selbst ist sauber — nur die Aktivierung wartet auf die
MVP-Stabilisierung. `sprint-execute` wird nach der Stabilisierung erneut mit dem
Readiness-Gate aufgerufen.

## Features

- [F-3](../features/species-tenant-key-and-cutover.md) — status: done
- [F-4](../features/tenant-scope-union-predicate.md) — status: done
- [F-5](../features/species-tenant-aware-read.md) — status: done

## Out of scope

- **Cultivar** — dieselbe Mandanten-Ownership, aber als separates
  Folge-Requirement (Operator-Entscheid „Species-only zuerst"); Cultivars bleiben
  bis dahin global sichtbar. Bezug: R-14.
- **`tenant_has_access`-Edge** (REQ-001 v4.0, explizite Grants über Ownership
  hinaus) — zurückgestellt; die Cutover-Regel + Ownership-Prädikat liefern die
  Isolation ohne sie. Bezug: R-14.
- **Frontend-Origin-Filter** (#397) — eigenes Requirement, unabhängig.

## Review notes

_Populated by `sprint-review` at closure._
