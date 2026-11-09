# SPEC-05 — Access and Visibility Matrix

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-300 … PRIV-339
Depends on: REQ-049 (roles), REQ-024 (tenants), 01 §4 (attribution roles), 03 §3 (former members)
```

A restriction on **filtering** is not a restriction on **visibility** (#2517): today every
member sees every performer in the unfiltered list and in the CSV; only the shortcut
(filter by someone else) is role-gated. This document defines who may see which personal
attribution, for which purpose, and separates tenant-level permissions from platform-level
access.

---

## 1. Actors

| Actor | Definition [verified] | Notes |
|-------|------------------------|-------|
| **Anonymous** | no token | reaches `/api/v1/auth/*`, `/privacy/policy`, public catalogue (light mode: everything as the system user) |
| **Viewer** (`viewer`) | member, rank 0 | reads, prints, exports all tenant data (REQ-049 §2.3: "Buchhalter, Prüfer, Angehörige") |
| **Grower** (`grower`) | rank 1 | creates and edits; no delete; typical holders include "Mitarbeiter, Saisonkraft" |
| **Lead** (`lead`) | rank 2 | deletes, assigns to others, changes structure, voids/redacts care events |
| **Management** (`admin_scopes ∋ management`) | axis 2, rank-independent | members, roles, invites, location assignments; tenant deletion with `lead` |
| **Technical** (`admin_scopes ∋ technical`) | axis 2 | integrations, service accounts (with `lead`); reads the member list |
| **Tenant administrator** | not a role in code; this package uses it for `lead ∧ management` | the two-axis model has no single "admin" |
| **Platform operator** | `lead` in tenant `platform` (light mode: always) | administrative data across tenants (existence, name, member list, security audit); **no domain data** (REQ-049 P4, AK-09) |
| **Platform viewer** | specified (REQ-024 §1a.4), **not implemented** (#2179) | no access today |
| **Service account** | `account_type: service`, max role `grower`, tenant-scoped API key | no interactive login |
| **Data subject (self)** | any account about its own data | Art. 15–21 self-service |

**[verified]** `require_permission(resource, action)` ignores `resource` ("does not change the
decision today"); the descriptive matrix `core/permissions.py:_RBAC` disagrees with the real
gates in places (tenant `UPDATE` granted to viewer in the table, `management` required in
the router; membership writes granted to `lead` in the table, gated by `management` in
code). This package does not fix the table (follow-up noted in `12`), it adds **visibility
rules** evaluated in the service, next to the ownership predicate.

---

## 2. Visibility dimensions

| Dimension | Meaning |
|-----------|---------|
| **P** performer identity | `performed_by` / `performed_for` of care events, harvests, treatments, inspections, confirmations-derived events |
| **C** creator identity | `created_by` of diary entries, comments, objects, templates, attachments, care events |
| **K** confirmation identity | the principal of a task completion / care confirmation (= P of the derived event; no separate field) |
| **M** modifier/actor identity | `voided_by`, `redacted_by`, `plan_updated_by`, `garden_plan_audit.user_key` |
| **F** free-text content | summaries, notes, names, comments, captions |
| **H** historical records | the rows themselves (care log, diary, audit) |
| **E** member directory | `display_name`, `email`, role, scopes, `joined_at` of members |
| **A** privacy administration | review queue, redaction, erasure state per tenant |
| **X** exports | CSV with names, plan PDF/JSON, Art. 15 bundle, tenant archive |
| **S** statistics per person | counts/aggregations of activity by member |

Rendering states of an identity (from `01` §4.3): `member` (name shown), `former_member`
(no name after N days), `erased`, `third_party` (label), `system`, `service_account`.

---

## 3. The matrix

Legend: **N** = name shown; **R** = role/relationship only ("a member", "a lead"), no name;
**–** = nothing / no access; **own** = only the actor's own rows; **S** = self-service;
**!** = audited read (security audit row, PRIV-330); **(t)** = subject to the tenant
setting `attribution_visibility` (§4); **[v]** verified today; **[p]** proposal.

| Dimension | Anonymous | Viewer | Grower | Lead | Management | Lead ∧ Management | Platform operator | Service account |
|-----------|-----------|--------|--------|------|------------|-------------------|-------------------|-----------------|
| **P** performer of a current member | – | N (t) [v: N] | N (t) [v: N] | N | N | N | – | R |
| **P** performer, former member (> N days) | – | R | R | R | R | R | – (account page only) | R |
| **P** performer, erased | – | `erased` | `erased` | `erased` | `erased` | `erased` | – | `erased` |
| **P** third-party label | – | label | label | label | label | label | – | label |
| **P** filter / search by another person | – | – [v] | – [v] | yes [v] | yes [v] | yes | – | – |
| **C** creator of diary / comment / object | – | N (t) | N (t) | N | N | N | – | R |
| **C** own-row marker (`created_by_me`) | – | own | own | own | own | own | – | own |
| **K** who confirmed a task | – | N (t) | N (t) | N | N | N | – | R |
| **M** who voided / redacted | – | R [p; v: N via performer join only] | R | N | N | N | – | R |
| **M** plan audit actor (`changed_by`) | – | R [p; v: N] | R | N | N | N | – | – |
| **F** free text of any member | – | yes [v] | yes [v] | yes | yes | yes | – | yes (read tools) |
| **F** redact free text | – | – | – | yes [v: care events only] | yes [p] | yes | – | – |
| **H** care log, diary, history (rows) | – | yes [v] | yes [v] | yes | yes | yes | – | yes |
| **H** `garden_plan_audit` rows | – | yes [v] | yes | yes | yes | yes | – | – |
| **E** member display names + roles | – | yes [v] | yes | yes | yes | yes | yes (admin list) | yes |
| **E** member e-mail addresses | – | yes [v] → **–** [p, LEG-14] | – [p] | – [p] | yes | yes | yes | – |
| **A** review queue, erasure state of the tenant | – | – | – | yes [p] | yes [p] | yes | counts only [p] | – |
| **A** own Art. 15–21 requests | – | S | S | S | S | S | S (admin erasure, preview) | – |
| **X** care-event CSV with other members' names | – | – [p; v: yes] | – [p; v: yes] | yes ! | yes ! | yes ! | – | – |
| **X** care-event CSV, own rows / names rendered as R | – | yes | yes | yes | yes | yes | – | – |
| **X** bed list CSV `include_assignment=true` | – | yes [v, §32.5 Pkt. 13] → (t) [p] | (t) | yes ! | yes ! | yes ! | – | – |
| **X** plan JSON / SVG / PDF (no names by design) | – | yes [v] | yes | yes | yes | yes | – | yes |
| **X** tenant archive (REQ-056) | – | – | – | – | yes ! [v: management + step-up] | yes ! | export of orphaned tenant ! | – |
| **S** per-person activity statistics | – | – | – | – [p: none exists; MUST NOT be built without LEG-05] | – | – | – | – |

### 3.1 Readings of the matrix

- **Tenant level**: everything above except the "Platform operator" column. Platform access
  never reaches dimension P/C/K/M/F/H of a tenant (REQ-049 P4); it sees E (admin member
  lists with e-mail, needed for support and INV-1), A as counts, and the security audit.
- **Statutory rows** (`06` §3): the applicator/harvester of a `treatment_applications` /
  `harvest_batches` row follows **P** while the account exists; after erasure the pseudonym
  is never rendered (state `erased`); the typed display name is cleared [v].
- **Light mode**: a single system user; the matrix collapses to "Lead ∧ Management" for the
  only actor; no `former_member`/`erased` states arise (no accounts).

---

## 4. Tenant setting `attribution_visibility` [proposal, DEC-10]

**PRIV-300** A tenant MUST carry `settings.attribution_visibility ∈ {all_members,
leads_and_self}` with default `all_members` (today's behaviour, REQ-049 P2 "no private areas
within a tenant"). With `leads_and_self`, dimensions P/C/K/M render **R** for viewers and
growers unless the row is their own (`own` → N). Leads and `management` always see N for
current members.

**PRIV-301** The setting MUST be changeable only by `lead ∧ management` with the reason shown
in the UI: "In organisations with employees, the law may require that activity of individual
employees is not visible to all colleagues (Art. 88 GDPR, §26 BDSG, §87(1) No. 6 BetrVG)."
**[legal LEG-05]** whether the default for an organisation tenant should be `leads_and_self`
instead. The package recommends: default `all_members` for `personal`, **`leads_and_self` for
`organization`** created after the change, `all_members` for existing tenants (no silent
behaviour change) — the operator decides.

**PRIV-302** The setting MUST be part of the tenant export (REQ-056) and of the Art. 15
bundle's personal-tenant section (it is the person's own setting there).

**PRIV-303** Notifications MUST follow the setting: a notification text to a viewer/grower
MUST NOT name the performer of another member's action when the tenant is `leads_and_self`
[verified today: system notification texts carry task and plant names, not member names —
REQ-025 §3.1.2 rule 8 measurement; keep it that way regardless of the setting].

---

## 5. Purpose-specific permissions

**PRIV-304** Three purpose permissions MUST exist in `core/permissions.py` and be wired where
the matrix says, evaluated in the service (not at the router alone, following #2107):

| Permission | Granted to | Gates |
|------------|-----------|-------|
| `attribution.filter` | `lead`, `management` [v: `MembershipEngine.can_filter_care_log_by_member`] | `performed_by` filter for someone else (care log, bed history) |
| `attribution.export` | `lead`, `management` | CSV/export rows carrying other members' names; `include_assignment=true` on the bed list CSV when `attribution_visibility = leads_and_self` |
| `privacy.review` | `lead`, `management` | review queue read, decisions, generic redaction (PRIV-228) |

**PRIV-305** `GET /tenants/{slug}/members` MUST return `email` only to `management` (and the
platform admin routes); for every other member the field is omitted (not nulled, to keep
the schema's semantics) — **spec change proposal** to REQ-024/REQ-049; **[legal LEG-14]**
necessity of showing every member's e-mail to every member. [verified] today the route is
gated only by `get_current_tenant` and `MemberInfoResponse` includes `email`.

**PRIV-306** `technical` scope reads the member list as today (REQ-049 §2.4) — names and
roles, no e-mail (PRIV-305 applies).

---

## 6. Exports and bulk reads

**PRIV-307** A CSV export that would contain other members' names MUST require
`attribution.export`; for everyone else the same export MUST succeed with the P/C/K columns
rendered **R** (`"Mitglied"` / `"member"` via i18n of the requested `locale`, or the own name
for own rows). Rationale: a 50 000-row CSV with names is an activity profile; the operational
need of a viewer ("print the watering plan") does not require names. [verified today] every
member exports the CSV with display names.

**PRIV-308** [proposal] Exports with names MUST write a `security_audit_log` row
(`ATTRIBUTION_EXPORTED`, `tenant_key`, actor, row count, no content). Today the tenant
archive logs `tenant_export_requested` [verified in NFR-011 R-38 plan], the care-log CSV logs
nothing.

**PRIV-309** The bed-list CSV `include_assignment=true` [verified: no role check, §32.5
Pkt. 13 argues that every member reads `/members` and `/assignments` anyway] MUST follow
`attribution_visibility`: under `leads_and_self` the assignment column renders R for
non-leads; the `/assignments` read follows the same rule (location assignments are
responsibility hints, REQ-049 §3.5).

**PRIV-310** MCP read tools MUST return `PersonRef` renderings, never raw keys. [verified]
`mcp_server/tools/diary.py` returns `created_by` as the bare `users._key`; `ipm.py` writes
`inspector = "mcp:<account_key>"` (a free-text pseudo-key — reclassify: it is an account
reference in disguise and MUST become `inspected_by_key` = service-account key, label
`service_account`).

---

## 7. Platform level

**PRIV-311** The platform operator MUST NOT gain any read on dimensions P/C/K/M/F/H through
this package. The privacy-operations endpoint (`08` §5) returns per-tenant **counts** and
operation **states**; the erasure preview and `GET /admin/platform/erasures/{key}` stay as
today [verified].

**PRIV-312** A future **platform viewer** (#2179) MUST inherit the operator's column with
every write removed; it is noted, not specified here.

**PRIV-313** Light mode (`kamerplanter_mode = light`) has no accounts; every rule above that
depends on a person's state is inert there, and the review queue is not created (there is
no erasure).

---

## 8. Historical records and the "former member" boundary

**PRIV-314** Historical rows (H) remain readable to every member regardless of who wrote
them — the tenant's history is the tenant's (REQ-049 P2). What changes with this package is
only the **rendering of the person** (P/C/K/M) and the **reviewability of the text** (F).

**PRIV-315** The `former_member` state MUST render identically for every tenant role (no
lead exception, `03` PRIV-113); the platform operator sees the account on the user page only
if it still exists.

---

## 9. Audit logging of privacy-sensitive reads

**PRIV-316** The following reads MUST write a `security_audit_log` row (actor, tenant,
action, count; no content): exports with names (PRIV-308), tenant archive, platform-admin
erasure preview, review-queue decisions. Ordinary list reads MUST NOT be audited (volume,
and REQ-049's "no surveillance of members").

---

## 10. Acceptance (summary)

| ID | Criterion |
|----|-----------|
| TA-300 | With `leads_and_self`, a grower's care-log list renders other members' performer as `R`, own rows as `N`; a lead sees `N`. |
| TA-301 | With `all_members`, behaviour equals today (regression pin). |
| TA-302 | `GET /members` omits `email` for viewer/grower/lead without `management`; includes it for `management` and platform admin. |
| TA-303 | CSV export by a viewer renders other members as `R`; by a lead with names and writes `ATTRIBUTION_EXPORTED`. |
| TA-304 | MCP diary/ipm tools return no raw `users._key`. |
| TA-305 | Platform admin cannot read review items (403), only counts. |
| TA-306 | `performed_by` filter for another member by a grower → 403 (regression pin); for a former suppressed member → 422. |
| TA-307 | Route walk: every new `/t/{slug}/privacy/*` route is in `test_garden_plan_tenant_isolation`-style matrix and refuses a foreign tenant with 404. |
