# Kamerplanter — GDPR Privacy Architecture and Implementation Specification

```
Location: spec/privacy/ (see decision-log.md DEC-01 for why not docs/specs/privacy/)
Version: 1.0 · 2026-11-09 · measured against develop 24d1c2988
Status: implementation-ready draft; legal review pending for every LEG-nn item
Language: English (artefacts); German is used for operator-facing summaries
Owner: engineering (authoring) · DPO / counsel (LEG decisions) · operator (DEC decisions)
```

## Purpose

This package is the authoritative technical foundation for implementing privacy by design
in Kamerplanter as a multi-tenant application that may be operated commercially. It
separates **what the repository already does** (verified at the commit above), **what this
package proposes**, and **what only legal counsel can decide**. A developer or coding agent
can implement each roadmap item from the referenced sections without rediscovering the
reasoning.

It builds on, and never silently changes, the existing specifications: REQ-025
(Datenschutz & Betroffenenrechte), NFR-011 (Aufbewahrungsfristen), REQ-023/REQ-024/REQ-049
(accounts, tenants, roles), REQ-053 (garden plan, care log, offline), UI-NFR-012 (PWA).
Where a change to those documents is needed it is listed as a **spec change proposal**
(`06-retention-and-legal-basis.md` §9, roadmap item E16).

## Document hierarchy and reading order

| # | Document | Answers | Requirement IDs |
|---|----------|---------|-----------------|
| 01 | [`01-privacy-architecture.md`](01-privacy-architecture.md) | vocabulary, components, data flows, trust boundaries, identity separation, lifecycle overview | PRIV-001…012 |
| 02 | [`02-personal-data-inventory.md`](02-personal-data-inventory.md) | every entity/field with personal data: category, purpose, basis, visibility, retention, erasure, anonymisation, lineage; fields that do **not** exist | PRIV-030…031 |
| 03 | [`03-account-and-membership-lifecycle.md`](03-account-and-membership-lifecycle.md) | account deletion, membership end, tenant deletion, rejoin, offline deletion, statutory users, reprocessing | PRIV-100…134 |
| 04 | [`04-anonymization-and-redaction.md`](04-anonymization-and-redaction.md) | marker vs tombstone vs anonymous, tombstone allowlist, free-text review queue, generic redaction, audit behaviour, legacy migration, verification, before/after examples | PRIV-200…236 |
| 05 | [`05-access-and-visibility.md`](05-access-and-visibility.md) | who may see performer/creator/confirmer identities, free text, history, exports; tenant vs platform access; purpose permissions | PRIV-300…316 |
| 06 | [`06-retention-and-legal-basis.md`](06-retention-and-legal-basis.md) | retention matrix with legal bases, statutory applicability per tenant, three-step LIAs, employee/volunteer data, purpose limitation, spec change proposals | PRIV-400…408 |
| 07 | [`07-offline-privacy.md`](07-offline-privacy.md) | device storage inventory, TDDDG classification, cache/queue lifecycle, retention, logout, tenant switch, revocation, shared devices, replay | PRIV-500…530 |
| 08 | [`08-api-and-data-model.md`](08-api-and-data-model.md) | registry attributes, `PersonRef`, new collections, settings, routes, enum values, error codes, compatibility | PRIV-600…608 |
| 09 | [`09-migrations-and-backfills.md`](09-migrations-and-backfills.md) | v0107–v0109, reclassification, persisted dry-run reports, backups and restore replay, salt constraint, device migration | PRIV-700…717 |
| 10 | [`10-testing-and-acceptance.md`](10-testing-and-acceptance.md) | TA-nnn matrix per requirement group, negative "cannot reappear" tests, gates | TA-001…TA-809, PRIV-900…902 |
| 11 | [`11-dpia-pre-screening.md`](11-dpia-pre-screening.md) | processing operations, risk register RISK-01…18, Art. 35 threshold assessment, DPIA inputs | — |
| 12 | [`12-implementation-roadmap.md`](12-implementation-roadmap.md) | epics PRIV-E01…E17 with P0–P3, scope, dependencies, acceptance, tests, legal items; lane order | — |
| — | [`decision-log.md`](decision-log.md) | DEC-01…22 (architecture/product), LEG-01…17 (legal), operator decisions relied upon, change control | — |

Read `01` first, then `03`→`04`→`05` for behaviour, `06` for the legal frame, `07` for the
client, `08`/`09` to implement, `10` to verify, `12` to schedule. `02` is the reference
table; `11` and the decision log are the hand-over to the DPO and the operator.

## Implementation order

P0 (defects, next lane after the wave-10 plan): **E01** (= GitHub #2770) → **E03** → **E02** →
**E04**. P1: **E05** (registry + resolver) → **E10** (offline revocation) → **E07** (review
queue) → **E08** (visibility) → **E06** (former members) → **E09** (record keeping).
P2: E11 → E13 → E12 → E14. P3: E15, E16, E17. Details and the dependency graph:
`12-implementation-roadmap.md`.

## Traceability model

```
REQ-025 / NFR-011 / REQ-053 … (existing requirements, German)
        │ builds on / proposes versioned changes (06 §9, E16)
        ▼
PRIV-nnn  (RFC-2119 requirement in 01–09; [verified] / [proposal] / [legal] marked)
        │ every PRIV names ≥ 1 acceptance criterion
        ▼
TA-nnn    (10: test type, assertion, path; TA numbering mirrors the document: TA-1xx ↔ 03, TA-2xx ↔ 04 …)
        │ every P0/P1 epic lists its TA set
        ▼
PRIV-Enn  (12: implementation unit; names LEG-nn defaults it ships with)
        │
        ▼
DEC-nn / LEG-nn (decision-log: who decides, default, alternative, where it lands)
```

Rules: a requirement without a TA is not implementation-ready (the final review found
none); a LEG item never blocks engineering — the default is specified and switchable; the
code inventories (`ErasureEngine.*`, `DataExportEngine.*`) remain the single source of the
lists, this package adds classification that is guarded (`08` §2, TA-001/030/606).

## What is verified, proposed, legal, outstanding

- **Verified repository facts** are marked `[verified]`/`[v]` and cite `path:symbol`
  (line numbers only where the file did not change between `68460e817` and `24d1c2988`).
  The repository analysis used seven read-only passes (erasure engine, tenants/RBAC, care
  log, free text, offline, specifications, migrations/exports); the primary checkout was
  fast-forwarded to `24d1c2988` because the earlier local state lacked wave 9.
- **Proposed architecture** is marked `[proposal]` and summarised in DEC-01…22.
- **Legal assumptions** are explicit in `06` and LEG-01…17 with the shipping default.
- **Outstanding implementation**: everything in `12`; nothing from this package has been
  implemented, no application behaviour was changed, no GitHub issue was created or closed.

## Conventions

RFC 2119 keywords are normative. "Anonymised" is used only where a row has been reviewed or
holds no identifying content; "attribution removed" (marker `_anonymized`) and
"pseudonymised" (tombstone `anon_<16hex>`) otherwise (`04` §1). Error codes follow NFR-006,
service methods that load by key and write take `*, tenant_key: str` (#2107), new routes
join the isolation route walk and the bounded-list guard, enums are additive with DE/EN i18n.

## Maintenance

Each document carries its own version/date header. When a LEG item is decided, update the
decision log and the affected PRIV requirement in the same change; when REQ/NFR documents
are edited (E16), reference `spec/privacy` in their changelog rows.
