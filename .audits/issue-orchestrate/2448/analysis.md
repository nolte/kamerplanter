# Pre-analysis: #2448 REQ-053 status table, reach probe (transient, removed before merge)

Class: docs (spec drift pass). Source: issue #2448 (WP 6.4): add the "Implementierungsstand" table to REQ-053 (per section: implemented / partial / not implemented with PR links; the adjacency endpoint paths missing in the GP-API table, see #2425), a `capability-reach-audit` probe for `GET /plan`, a handover memory; bump the spec version with a changelog row. Acceptance: status table matches `git log`/endpoints (MEASURED, not copied); probe passes. Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single).

## Hard rule: reach-probe approval (memory feedback-reach-probe-approval-operator-only)
Probe `approval:` blocks (approved_by / approved_at) are written only by the main session after an explicit operator approval of that exact derivation; the delegation of 2026-10-04 covered three other issues only, the 2026-10-09/30 autonomy covers plan gate, dispatch, merge, closing — NOT probe approval. The dispatched specialist writes the probe as a DRAFT with `TO_BE_SET_BY_MAIN_SESSION` placeholders and never an approval. `reach-audit.yml` is periodic and not a merge gate, so a draft in develop is harmless; "probe passes" is reported as pending operator approval.

## Established
- `project/reach-probes/` holds approved probes (REQ-025 erasure etc.); `project/reach-probes/_not-constructible.yml` the not-constructible manifest; tasks in `.taskfiles/reach.yaml`, observe helpers in `scripts/reach/`; schema `schemas/reach-probe-v1.3.schema.yaml` of nolte/claude-shared (the capability-reach-audit skill/agent derive probes against it).
- REQ-053 spec: `spec/req/REQ-053_Grafische-Garten-Beetplanung.md`, version table at the top (latest rows 1.6 Nachtrag …); GP-API table (l.~1433: GP-API-014 PATCH /slots/{key} triggers adjacency_recompute); #2425 (adjacency engine decisions closed) mentions adjacency endpoint paths missing in the table.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | "Implementierungsstand" table in REQ-053: per section (§ numbers and the GP-FR/GP-API/GP-NFR groups), status implemented / partial / not implemented, evidence = PR numbers from `git log` and the endpoint/code that exists; MEASURE: for each route of the GP-API table check the mounted route (`app.routes`/router files), for each UI claim the component; adjacency endpoint paths added to the GP-API table; version bump + changelog row | fullstack-developer |
| P2 | reach probe draft for `GET /sites/{key}/plan` (the plan read model) in `project/reach-probes/`, per the capability-reach-audit method (declaration anchor, tier, typed expectation, observe step emitting raw data, derived_from content blob / pinned ref), approval placeholders only; update `_not-constructible.yml` only if something cannot be constructed | fullstack-developer |
Review after: spec-readiness-reviewer-style read of the table vs code by a code-reading reviewer.

## Out of scope
Handover memory (written by the main session after the merge).
