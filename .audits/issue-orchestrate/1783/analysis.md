# Pre-analysis — Issue #1783

- **Issue:** https://github.com/nolte/kamerplanter/issues/1783 — "reach: re-anchor the four REQ-025 probes on the #1780 squash commit"
- **Author:** nolte (owner, trusted)
- **Classification:** `spec-change` — the change edits the approved reach-probe set (`project/reach-probes/`), the durable declaration artefact of `capability-reach-audit`; secondary: a structural anchoring question against the shared `reach-probe-v1.0` schema.
- **Requirements gate:** operator override — the issue carries three machine-checkable acceptance items; no `project/requirements/` artefact elicited (recorded under the owner's standing pre-approval of 2026-09-24/25).
- **Route:** implement directly (one outcome, one PR strand, no roadmap item).

## Verified claims (claim provenance)

- **Established:** `c9d6d29ee` is #1780's squash commit and the latest commit of `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` on develop (`git log -1 -- spec/req/REQ-025*`).
- **Established:** the four probes carry `derived_from: e9e0c3a52…`, which is not in develop's history (`git merge-base --is-ancestor` fails without the pull ref).
- **Established:** the runner's re-baseline check resolves the probe's *previous* `derived_from` (`reach_audit.py::_rebaseline_problem`, "cannot both be resolved to commits") — so `refs/pull/1780/head` and `refs/pull/1776/head` must be fetched before a run.
- **Established:** `derived_from` is defined by the shared schema as a commit, "no content hash is stored" (`claude-shared/schemas/reach-probe-v1.0.schema.yaml` `derived_from.description`). The runner lives in `claude-shared/plugins/nolte-engineering/skills/capability-reach-audit/scripts/reach_audit.py`, not in this repository.

## Scope

- In: re-derive the 4 REQ-025 probes + 7 REQ-025 entries of `_not-constructible.yml` with `derived_from = c9d6d29ee…`; runner proof (change detection + T2); runner report.
- Out: changing the anchoring rule here (shared schema owns it → claude-shared issue).

## Work packages

| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| WP1 | Re-derive the REQ-025 probes and manifest entries on `c9d6d29ee` | `derived_from` = c9d6d29ee in 4 probes + 7 entries; observe/targets/expectations unchanged (digest identical) | `project/reach-probes/*.yml` | `nolte-engineering:capability-reach-audit` (derive) → `capability-reach-scanner` | — |
| WP2 | Runner proof | all probes `clean`, 4 REQ-025 probes `reached` with `--include-t2` | `.audits/capability-reach/2026-09-25.md` | `reach_audit.py` (via `capability-reach-audit run`) | WP1 committed |
| WP3 | Structural anchoring question | decision recorded; claude-shared issue filed if spec-owned | — | generalist (issue filing) | — |

## Risks

- A probe edit is itself a re-baseline: the commit moving `derived_from` must be the only change to each probe file after derivation, and the branch must not be rebased (merge-update only).
- After this PR squashes, the probes' baseline is the new squash commit and the prior `derived_from` (`e9e0c3a52`) must still be resolvable for the re-baseline check → every run needs the pull ref fetched (see claude-shared issue).

## Results

- WP1 (`capability-reach-scanner` via `capability-reach-audit derive`): hypothesis confirmed — all 11 entries unchanged except `derived_from`; persisted under the owner's standing pre-approval; digests verified equal. Commit 38bb658b2.
- WP2 (`reach_audit.py --include-t2` at 38bb658b2): 11/11 probes `clean`, T0 1 · T1 1 · T2 9 reached, findings none; 4 REQ-025 probes reached (2/2, 2/2, 7/7, 1/1).
- Squash simulation of this branch onto develop: all 11 `clean` with pull refs fetched; in a clone without `refs/pull/1780|1776/head` the 7 re-anchored probes read `weakened` ("cannot both be resolved to commits") — durable cost recorded for WP3.
- WP3: anchoring rule is schema-owned (`reach-probe-v1.0.schema.yaml` `derived_from`: commit, "no content hash is stored"; runner lives in claude-shared) → claude-shared issue, no local change.
