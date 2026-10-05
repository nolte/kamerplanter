# CLAUDE.md reference (offloaded sections)

Moved verbatim out of the root `CLAUDE.md` to cut per-turn context cost. The root file keeps a short pointer to each section. Read the relevant section when the topic comes up.

## Crash recovery & parallel working copies

A notebook crash, terminal close, or session expiry does **not** destroy
in-flight work — Claude Code persists every top-level session transcript under
`~/.claude/projects/<encoded-cwd>/`. To get back to an interrupted run:

```bash
task resume          # list this working copy's resumable sessions, newest first
claude --continue    # resume the most recent
claude --resume <id> # resume a specific one
```

Two things are **not** recoverable with `claude --resume`, which is why long or
autonomous work must be a top-level session:

- **Dispatched worktree-isolated subagents** — their transcript lives under the
  parent session, not as a standalone session.
- **`Workflow` runs** — resumable only via `Workflow({resumeFromRunId})` from
  inside the parent session; never via `claude --resume`.

A real loss happened this way: the `nfr-lektorat` Workflow run on 2026-06-11
executed inside a worktree nested under `.claude/worktrees/`, whose top-level
transcript was gone after the crash. (Its output had already been merged via
PR #166, so nothing was actually lost that time — but the session was not
resumable.)

**Rule:** run long feature work as a top-level session inside a worktree created
under the centralised worktree root, never from a harness worktree under
`.claude/worktrees/`:

```bash
# from the primary checkout:
task worktree:add -- feat/<branch>        # creates it off origin/develop
cd ${NOLTE_WORKTREE_ROOT:-~/repos/.worktrees}/kamerplanter/<slug>
claude                                     # a top-level, --resume-able session
```

The `guard-nested-worktree` pre-commit hook enforces this by rejecting any
commit made from a worktree under `.claude/worktrees/`.


## Claude Code plugin adoption

kamerplanter is migrating its generic delivery / software-engineering
capabilities to the shared **`nolte-shared`** + **`nolte-engineering`** portfolio
plugins, keeping only its **domain-specialised** assets (plant-profile /
"Steckbrief" capture, agrobiology, horticulture/lifecycle, Home-Assistant
integration, RAG/knowledge) under `.claude/`. Generic capabilities (test-case
extraction, E2E generation, quality gate, PR flow, spec/roadmap tooling, …) come
from the plugins, not from local copies.

**Launch Claude Code with the plugins loaded:**

```bash
task claude                 # → claude --plugin-dir <claude-shared> --plugin-dir <…>/plugins/nolte-engineering
task claude -- --resume     # extra args are forwarded
```

The plugins are consumed from a **local checkout of `nolte/claude-shared`** via
`--plugin-dir` (a runtime launch flag — it does **not** appear in
`.claude/settings.json` / `enabledPlugins`). The target resolves the checkout at
`~/repos/github/claude-shared`; override with the `NOLTE_CLAUDE_SHARED`
environment variable if yours lives elsewhere. `nolte-media` is intentionally
**not** loaded (kamerplanter's image-domain `gemini-graphic-prompt-generator`
stays local for now).

**Rules for this adoption:**

- **No copies (DRY):** never copy a plugin-owned skill/agent into `.claude/`.
  Adoption is by plugin consumption; retiring a local asset means *removing* it,
  not re-vendoring it.
- **Verify before remove:** delete a local asset only after its plugin pendant is
  confirmed present at runtime **and** behaviour parity is checked on a real input.
- **Domain assets stay local.** Only genuine plant/HA/agrobiology/RAG assets have
  no portfolio pendant; leave them untouched.


## Enforcement status: RBAC write gate (CLAUDE.md Key Architectural Decision 9)

**What actually enforces access, as of 2026-08-08.** The write gate is now wired (issue #1042, decision "wire it"). Three dependencies from `src/backend/app/common/auth.py` run in HTTP handlers, all resolving the tenant through `get_current_tenant` (which itself refuses a non-member with 403 before any gate runs): `require_permission(resource, action)` gates tenant-scoped **create/update/delete** on the caller's domain role, `require_tenant_role(min_role)` gates the domain rank directly, and `require_admin_scope(scope)` gates the orthogonal administrative surfaces (member management, integrations). `require_permission` decides purely on `ctx.role` via the pure `MembershipEngine` predicates — `can_edit_resource` (lead/grower) for create/update, `can_delete_resource` (**lead only**, the REQ-049 §2.3 irreversibility boundary) for delete — so the router surface and the engine can never drift on who may delete. Reads stay open (every member may view). The descriptive resource×action matrix in `src/backend/app/core/permissions.py` still backs the attachment guard (`require_attachment_permission`) and the MCP dispatcher (`assert_mcp_permission`, REQ-033); its plant-domain **delete** grant was corrected to lead-only so the two enforcement paths agree. Row-level isolation remains the `tenant_key=ctx.tenant_key` stamping plus per-repository filtering. A per-resource-type matrix behind `require_permission` (the `resource` argument is carried but not yet decision-bearing) is the remaining future refinement.

**Measured again on 2026-10-05 (#2121, `develop` `b064e63b7`) — what decision 9 means in code today:**

- **Vocabulary.** A membership has exactly one domain role `TenantRole` = `viewer` / `grower` / `lead` (ranked) and zero to two `AdminScope` = `management` / `technical`, independent of the rank (REQ-049 §2.3/§2.4). The value `admin` was retired by migration `v0032` (→ `lead` + both scopes). `tests/unit/guards/test_spec_literal_discriminators_match_models.py` keeps REQ-023/024/049, the root `CLAUDE.md` and this file on that vocabulary.
- **Platform admin** = an *active* `lead` membership in the technical `platform` tenant (`app.common.auth.is_platform_admin`); in light mode the system user is platform admin by mode, not by a membership; a tenant-scoped API key never is (#1817). The **platform viewer** of REQ-024 §1a.4 is **not implemented** — a `viewer` membership in `platform` grants no admin access at all.
- **Tokens are informative.** The access token's `tenant_roles` is minted empty and `is_platform_admin` is not read by any gate; guards read the stored membership on every request (REQ-023 v1.46, NFR-001 §6.1).
- **Role grants (#2078, REQ-024 AK-58 — decided by the operator 2026-10-04).** Nobody raises their own membership role; `lead` in `platform` (role change or invitation) is granted only by an active `lead` there; in every other tenant `management` may grant any role — there is deliberately no general rank ceiling (a secretary, `viewer` + `management`, may appoint a lead). Open: `accept_invitation` does not re-check the rule, so a platform `lead` invitation issued before #2084 by a non-lead is still honoured when accepted — revoke such pending invitations at rollout (7-day validity).
- **Location assignments** (`LocationAssignment`, `Task.assigned_to`) express responsibility only and grant no write rights (REQ-049 §3.5; the old "assignment-based write control" is gone).
- **Member limit (#2133, AK-64):** effective limit `min(max_members, TENANT_MAX_MEMBERS_CEILING)` (setting, default 50); a full tenant refuses invitation acceptance and admin additions with `422 MEMBER_LIMIT_REACHED`; a personal tenant is founded with `max_members = 1`.
- **Registration mode (#2132, REQ-023 §3.2d):** `REGISTRATION_MODE` = `open` (default) | `invite_only` | `closed`, optional `REGISTRATION_ALLOWED_DOMAINS`; an e-mail invitation for the address is the exception in `invite_only`.
- **Tenant lifecycle (#2105, #2123, REQ-024 AK-48/AK-52/AK-65, v1.24):** `status` = `active` / `suspended` / `pending_deletion` / `orphaned` / `deleted`; only `active` resolves — every other state answers path, `X-Active-Tenant` and MCP exactly like an unknown slug. The admin switch toggles `active` ↔ `suspended` (step-up). `DELETE /tenants/{slug}` schedules the erasure after a 90-day grace (`RETENTION_TENANT_ERASURE_GRACE_DAYS`, operator decision 2026-10-04), cancellable with step-up; an organisation left without administration by an account erasure becomes `orphaned` and runs into the same grace (#2134). Not built: pausing Celery work of a suspended tenant and a suspension reason (#2143).
- **Home Assistant (REQ-005 §4c, REQ-018 §4, #2112):** single-household model A — one HA instance per installation; tenants bind only granted entities (`tenant_ha_entity_grants`); entity listings need `technical`.
- **Ownership in the service (#2107):** a keyed service write takes `*, tenant_key` and checks ownership itself; see `tests/unit/guards/test_keyed_service_writes_take_the_tenant.py`.

## Enforcement status: DAST (CLAUDE.md Key Architectural Decision 11)

**What is actually enforced, as of 2026-08-01** — this paragraph previously described the target state as if it were in force, which is the failure class NFR-018 §1 catalogues:
    - The Nuclei PR scan runs and reports, but is **advisory**. `develop` requires only `static / Static CI Tests` and `lint-test-build (22)`; verify with `gh api repos/nolte/kamerplanter/branches/develop/protection --jq '.required_status_checks.contexts'`. Promoting it is a decision to be made on measured history per NFR-018 §4, not by editing this sentence — the job runs ~16 minutes and `strict: true` multiplies that across the merge train.
    - The Nuclei nightly scanned nothing at all until 2026-08-01 (it resolved a staging URL that was never configured); it now builds its own ephemeral stack.
    - **ZAP became real on 2026-08-01.** `security-zap-baseline.yml` had been a scaffold that checked three files exist and reported green without scanning. It now runs a Baseline (passive + AjaxSpider) and an OpenAPI-driven API scan against an ephemeral stack on every pull request (#890, advisory), and `security-zap-nightly.yml` runs the authenticated Full-Scan with the cross-tenant passive rule and the auth-bypass two-pass (#891). Both are advisory, like the Nuclei lane. ZAP deviates from NFR-015 §4.1's named `zaproxy/action-*` wrappers and runs via `docker run`; the reason is recorded in §4.1 itself.
