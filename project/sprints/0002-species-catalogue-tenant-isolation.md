---
number: 2
status: closed
started: 2026-08-09
ended: 2026-08-09
value_statement: Gemeinschaftsgarten-Mitglieder sehen im Arten-Katalog nur die gemeinsamen und ihre eigenen Arten — privat angelegte Arten anderer Mandanten bleiben verborgen.
artifact_ref: develop@1ed06471 (PR #1087)
last_commit: 1ed06471dbac55f5d02aa5834654c6f107beb36e
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

**Abschluss (sprint-review, 2026-08-09): `closed`.**

**Artefakt-Validierung (Schritt 3).** Projekt ist eine self-hosted Anwendung
(Backend/Frontend/Helm), die kontinuierlich aus `develop` deployt — kein
Per-Sprint-Release-Cut; Artefakt-Konvention wie Sprint 1 (`develop@<sha> (PR #N)`).
- `artifact_ref: develop@1ed06471 (PR #1087)` — der Squash-Merge des
  Sprint-2-Codes (F-3/F-4/F-5 + Security-Härtung) auf `develop`.
- `git rev-parse 1ed06471…` → aufgelöst; `git merge-base --is-ancestor … develop`
  → **REACHABLE** (Exit 0). `last_commit` auf den Merge-Commit korrigiert (der
  vorherige `85960e9c5` wurde vom Squash-Merge verworfen).

**Mehrwert-Verifizierer (Schritt 4).** Genau ein `verifies_sprint_value` über die
Features: **F-5 (`features/species-tenant-aware-read.md`) `acceptance-2`** — „Eine
Art eines fremden Mandanten erscheint NICHT in der Species-Liste eines anderen
Mandanten." Bullet ist `[x]` (abgehakt), beidseitiger Isolationstest grün. Der
Verifizierer beweist das `value_statement` direkt.

**Release-Verkettung (Schritt 5): übersprungen.** Grund: self-hosted Anwendung,
kontinuierlicher Deploy aus `develop`, kein eigener Release-Cut (kein
PyPI/npm/Plugin/Container-Tag pro Sprint). `release-notes-curate` /
`release-publish-trigger` nicht angestoßen — Deployment erfolgt out-of-band über
die bestehende docker-publish/ArgoCD-Pipeline. (Wie Sprint 1.)

**Security.** Die Tenant-Isolation wurde vor dem Merge vom `code-security-reviewer`
geprüft; drei Critical-Cross-Tenant-Lecks (Einzel-Read, Update/Delete-Ownership,
MCP) wurden vor dem Merge behoben und Rot-zuerst verifiziert.

**Roadmap.** R-14 → `done` (alle Features F-3/F-4/F-5 `done`, Sprint `closed`).
Gelieferter Schnitt ist **species-only**; **Cultivar** und die
**`tenant_has_access`-Edge** bleiben Folge-Requirements (eigenes Roadmap-Item),
ebenso die Org-Kontext-Tenant-Auflösung (#808 A1 / REQ-049) und die tenant-aware
MCP-Species-Tools.

**Blog-Trigger-Deferrals.** Keine offenen (`project/blog-triggers/` nicht vorhanden).
