# Pre-analysis: #1768 — REQ-025 erasure scope as acceptance criteria + reach-probe re-derivation

- Issue: https://github.com/nolte/kamerplanter/issues/1768 (author `nolte`, owner — trusted)
- Scope addition: owner comment (three probes anchored on `2994893c9`)
- Classification: `spec-change` (secondary: none). Rationale: the deliverable is REQ-025 acceptance criteria plus the reach probes whose declaration they anchor on; no product code changes.
- Requirements gate: **operator override** — the issue carries explicit acceptance; the operator's standing authorization (2026-09-24/25) pre-approves every gate. No `project/requirements/` artefact is created.
- Route: **implement directly** (one outcome, one PR strand, no roadmap item).

## Established facts (measured)

| Claim | Evidence |
|---|---|
| Renditions deleted with the original by both storage adapters | `src/backend/app/data_access/storage/local_fs_adapter.py:398-401`, `s3_adapter.py:339-342`, `rendition_keys()` `domain/engines/storage/thumbnail_generator.py:146` |
| Late renditions discarded by the thumbnail task | `src/backend/app/tasks/storage_tasks.py:70-76` |
| Pest prototypes deleted for every contribution regardless of status, before link documents; failure raises | `domain/services/privacy_service.py:1775-1800` |
| Tenant deletion removes contributed reference vectors, then pest prototypes, before ArangoDB; unwired pest store refuses | `domain/services/tenant_service.py:298-326` |
| No-op bindings refuse once a contributions marker is set | `data_access/vectordb/noop_reference_index_store.py:48-61`, `pest_prototype_stores.py:76-90` |
| Report/erasure record carry `reference_index_binding/_removed`, `pest_prototype_binding/pest_prototypes_removed` | `privacy_service.py:1479-1490`, `1979-2011` |
| Admin + unverified deletion go through `erase_account_now` (config refusal 503, persisted request with `origin`, deactivate+revoke, atomic claim 409, `completed` only when nothing unreached, else `partially_completed` + retry / 500) | `privacy_service.py:577-690`, `1440-1525`; `ErasureOrigin` `domain/models/privacy.py:23` |
| REQ-025 has no EN mirror | `ls spec/req` — German only; no `spec/.spec-config.yml` |
| Squash is the only merge method | `gh api repos/nolte/kamerplanter` → `allow_merge_commit=false`, `allow_rebase_merge=false` |
| `2994893c9` resolvable via `refs/pull/1776/head` | `gh api .../compare/2994893c9...<pr head>` → `ahead` |

## Work packages

| ID | Problem | Acceptance | Files | Specialist | Depends |
|---|---|---|---|---|---|
| WP1 | REQ-025 does not state the landed erasure scope | New AK rows for renditions, pest prototypes, reference-index binding, immediate (admin/unverified) erasure; changelog + version bump | `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` | generalist — no matching specialised agent (`nolte-shared:spec` governs `spec/<topic>/<lang>.md` with `.spec-config.yml`, absent here) | — |
| WP2 | Editing REQ-025 makes its probes stale; three probes anchored on unreachable `2994893c9` | Re-derived via `capability-reach-scanner`, approved under standing pre-approval, anchored on commits reachable at the PR head | `project/reach-probes/*` | `nolte-engineering:capability-reach-scanner` + `capability-reach-audit` | WP1 |
| WP3 | Evidence | `reach_audit.py --include-t2`: every REQ-025 probe `reached` | `.audits/capability-reach/<date>.md` | `capability-reach-audit` runner | WP2 |
| WP4 | User docs parity | Check whether `docs/*/guides/data-retention.md` already names the scope (landed with #1766/#1776); edit only on a gap | `docs/` | `mkdocs-documentation` (if gap) | WP1 |

## Risks / open points

- Squash-only merging: a probe anchored on REQ-025 needs `derived_from` ⊒ the commit that last changed REQ-025; after the squash that is the squash commit itself, which a file inside it cannot name. See PR "Risk / rollout notes".
