---
review-type: agent-review
target: ".claude/agents/e2e-result-reviewer.md"
target-kind: agent
specs-applied:
  - slug: agent-management
    revision: "0e3b6f9"
  - slug: skill-vs-agent
    revision: "0e3b6f9"
  - slug: review-plan
    revision: "0e3b6f9"
  - slug: agent-review
    revision: "0e3b6f9"
repo-revision: "c558f311"
created: "2026-04-27"
status: open
---

# Agent Review: e2e-result-reviewer

## Scope

Target: `.claude/agents/e2e-result-reviewer.md` (frontmatter + body, ~210 lines, no sibling assets).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime image analysis behavior, Vale/markdown style.

## Summary

- BLOCKER: 4
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — Read-only review agent declares `Bash`, body is German, no rationale section, output shape stated only in Phase 7 template without upfront contract.
Next concrete action: author addresses the four BLOCKERs (drop `Bash` or justify minimum, English-translate body, add rationale section, declare output contract upfront).

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Read-only review agent (description verbs: "Analysiert", "Erkennt", "Gibt … Handlungshinweise aus") declares `Bash` in `tools`; `agent-review` lists `Bash` alongside `Edit`/`Write`/`NotebookEdit` as forbidden execution tools for read-only agents.
      Where: `.claude/agents/e2e-result-reviewer.md:5` (`tools: Read, Glob, Grep, Bash`).
      Fix: Remove `Bash` from `tools`. Body uses Bash only via the example "Glob: test-reports/e2e/*/protokoll.md" which is actually Glob notation; no Bash invocation is documented in the procedure. If sorting screenshot directories by timestamp truly needs Bash, document the use case in writes-tools-goals per `agent-management.acceptance` — otherwise drop it.
      Verify: `tools` lists only `Read, Glob, Grep`, or `Bash` is retained with documented goals/preconditions.

- [ ] [agent-management.english-body] Body MUST be in English; the entire body is German — Kernaufgabe paragraph, all "Schritt N" headings, all checklist items, the Phase 7 report template.
      Where: `.claude/agents/e2e-result-reviewer.md:10-210`.
      Fix: Translate the body to English; UI-NFR domain terms (DataTable, Snackbar, Empty-State) MAY stay as-is, but section headings ("Schritt 3: Screenshots visuell analysieren") and prose must be English.
      Verify: A `lang detect` pass returns >95% English.

- [ ] [skill-vs-agent.rationale-section] No rationale section in the body naming a decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent`.
      Where: `.claude/agents/e2e-result-reviewer.md:1-210`.
      Fix: Add a rationale block citing decisive dimensions — most plausibly *context-window protection* (large screenshot reads + every TC spec), *parallelism* (multiple test runs reviewable concurrently), and *specialization* (visual QA persona). Optionally name *tool restriction* (read-only review).
      Verify: A "## Rationale" or equivalent section exists naming ≥1 decisive dimension.

- [ ] [agent-management.output-shape] System prompt's expected output shape is only described in "Schritt 7: Bericht erstellen" (line 127ff) — no upfront output contract per `agent-management.structure` MUST.
      Where: `.claude/agents/e2e-result-reviewer.md:127-194`.
      Fix: Add an "Output contract" section near the top stating (a) what is returned to the caller, (b) the report sections (Testlauf-Übersicht, Spec-Abweichungen, Failure-Analyse, etc.), (c) write semantics — the prompt never says whether the report is written to disk or returned inline.
      Verify: Reading the upfront section tells the caller the deliverable shape without scrolling.

### WARNING

- [ ] [agent-management.bash-vs-dedicated] `Bash` is declared but every operation the body describes (Glob screenshots, Read protokoll.md, Read TC specs) is covered by `Read` and `Glob`; preferring dedicated tools is a `agent-management.tool-access` SHOULD.
      Where: `.claude/agents/e2e-result-reviewer.md:5`.
      Fix: Drop `Bash` (resolves BLOCKER too), or add a body section stating the Bash use case (e.g., sorting test-report directories by timestamp suffix) — and ensure it cannot be done with Glob's natural ordering.
      Verify: Either `Bash` is gone, or the body justifies it.

- [ ] [agent-management.tags] No `tags` field declared; `tags: [review]` (or `[review, quality-gate]`) would slot it into the review cluster per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/e2e-result-reviewer.md:1-8`.
      Fix: Add `tags: [review]`.
      Verify: Frontmatter parses with `tags` matching the lowercase-kebab/length rules.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `selenium-test-reviewer` (which reviews the test code) and `frontend-usability-optimizer` (post-implementation usability). The boundary — `e2e-result-reviewer` reviews *test outputs* (screenshots+protokoll), `selenium-test-reviewer` reviews the *test source*, `frontend-usability-optimizer` reviews *implementation* — is not stated in the description, so a calling Claude could mis-route.
      Where: `.claude/agents/e2e-result-reviewer.md:4`.
      Fix: Add negative triggers: "don't use for reviewing the Selenium test source code (use `selenium-test-reviewer`); don't use for general frontend-implementation usability (use `frontend-usability-optimizer`)."
      Verify: `description` contains negative triggers naming both peers.

- [ ] [agent-management.prompt-structure-order] System prompt opens with role, then Referenz-Dokumente, then Workflow steps, then "Wichtige Prinzipien" at the bottom; output contract is buried in Schritt 7. `agent-management.recommendations` SHOULD: role → output → method.
      Where: `.claude/agents/e2e-result-reviewer.md:10-210`.
      Fix: Restructure: (1) Role + boundaries, (2) Output contract (currently Schritt 7), (3) Working method (Schritt 1-6). The "Wichtige Prinzipien" footer either folds into role or stays as a bottom appendix.
      Verify: First three top-level sections, in order, are role / output / method.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: opus` is justified by multimodal screenshot analysis; the rationale comment is solid — the only suggestion is to make the rationale a body-level paragraph in addition to the comment, so it survives reformatting.
      Where: `.claude/agents/e2e-result-reviewer.md:6`.
      Fix: Move (or duplicate) the rationale into the rationale section being added per the skill-vs-agent BLOCKER, calling out *opus for vision-quality* explicitly.
      Verify: Body contains a sentence stating opus is pinned for multimodal screenshot reasoning.

### INFO

- [ ] [review-plan.observation] No sibling folder `agents/e2e-result-reviewer/`; if the prompt-structure-order WARNING leads to factoring the Phase 7 report template out, a sibling folder will be needed.
      Where: `.claude/agents/e2e-result-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-review.observation] Body length (~210 lines) is right at the ~200-line soft target; not a SHOULD violation but worth watching as more checklist items accrue.
      Where: `.claude/agents/e2e-result-reviewer.md:1-210`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
