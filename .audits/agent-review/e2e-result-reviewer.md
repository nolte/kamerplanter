---
review-type: agent-review
target: ".claude/agents/e2e-result-reviewer.md"
target-kind: agent
specs-applied:
  - slug: agent-management
    revision: "7772341"
  - slug: skill-vs-agent
    revision: "0e3b6f9"
  - slug: review-plan
    revision: "0e3b6f9"
  - slug: agent-review
    revision: "7772341"
repo-revision: "728ac421"
created: "2026-04-28"
status: open
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: e2e-result-reviewer

## Scope

Target: `.claude/agents/e2e-result-reviewer.md` (frontmatter + body, ~210 lines, no sibling assets).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent`, `review-plan`, `agent-review` (rev 7772341); revisions in frontmatter.
Iteration: 2 (re-review). Iteration 1 ran against `agent-management` rev `0e3b6f9` and recorded the German body as a BLOCKER. The `7772341` revision introduces a project-language exception for `distribution: project` agents whose project authorizes non-English prose; Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agents. The body-language BLOCKER is therefore downgraded to INFO in this iteration.
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the dispatching skill (none declared), correctness of any specific E2E test case beyond structural review.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — three MUST violations remain (no rationale section, output shape stated only as a fragmented "Bericht" template, undeclared write side effect against an in-prose path while no `Write` tool is granted).
Next concrete action: author addresses the three BLOCKERs (add rationale section per `skill-vs-agent`; declare structured output contract upfront; clarify whether the report is returned as a string to the parent or written to disk — the current ambiguity matters because no `Write` tool is granted yet the prompt opens with "Erstelle einen strukturierten Bericht").

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/e2e-result-reviewer.md:1-210`.
      Fix: Add a 2-4-bullet rationale near the top — likely *specialization* (multimodal screenshot review benefits from a narrow opus-pinned prompt), *context-window protection* (dozens of screenshots + protocol + REQ specs), *tool restriction* (read-only). Cite at least one counter-dimension (mid-flow user approval — "no, the parent skill consumes the structured report").
      Verify: Section "## Rationale" or equivalent exists; grep returns at least one of "specialization", "context-window", "tool restriction".

- [ ] [agent-management.output-shape] System prompt instructs "Erstelle einen strukturierten Bericht im folgenden Format" with an embedded markdown template, but the structured output shape the parent consumes is not stated upfront and the contract is fragmented across Schritt 7 + the markdown template.
      Where: `.claude/agents/e2e-result-reviewer.md:126-193` (Schritt 7 + report template).
      Fix: Add an "Output contract" section near the top (after the Kernaufgabe paragraph) stating (a) what the agent returns to the caller (markdown report string vs. file path), (b) the report's required sections, (c) whether the agent writes the file or only returns the markdown body.
      Verify: A section "Output contract" or equivalent exists; reading just that section tells the caller the deliverable shape.

- [ ] [agent-management.writes-vs-research] Body opens "Erstelle einen strukturierten Bericht" but `tools` does not include `Write` and the prompt never names a target file path or a "do not write" stance — this leaves the side-effect contract undefined per the `agent-management.acceptance` MUST that side-effect goals/preconditions be documented.
      Where: `.claude/agents/e2e-result-reviewer.md:5` (`tools: Read, Glob, Grep, Bash`) vs. `:127` ("Erstelle einen strukturierten Bericht").
      Fix: Decide explicitly: either (a) add "This agent is read-only; the parent skill writes the report" near the top, or (b) declare `Write` in `tools` plus a target path + overwrite policy. Currently the agent will silently fail any disk-write attempt.
      Verify: Either no imperative "Erstelle" referencing a file path remains, or `tools` includes `Write` plus a documented target path.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Bash` is declared in `tools` but the body's procedure (Schritte 1-7) only names the dedicated tools `Glob` and `Read` (for screenshots-as-images); no Bash invocation is justified anywhere.
      Where: `.claude/agents/e2e-result-reviewer.md:5` (`tools: Read, Glob, Grep, Bash`).
      Fix: Either remove `Bash` from `tools` (preferred — `Glob`/`Read`/`Grep` cover the documented procedure), or add a body section that names a concrete Bash invocation the agent needs (and prefer the dedicated tool when it would work, per `agent-review.tool-scope` SHOULD).
      Verify: `tools` no longer lists `Bash`, OR the body contains an explicit Bash use-case the dedicated tools cannot satisfy.

- [ ] [agent-management.tags] No `tags` field declared; tag vocabulary `review` (and possibly `quality-gate`) would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/e2e-result-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, quality-gate]` after the `name`/`description`/`distribution` block.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `selenium-test-reviewer` (both review Selenium output) and `selenium-test-generator` (writes Selenium tests; could be confused as a "fix-up" reviewer). Distinct purposes — but the description shape doesn't name negative triggers.
      Where: `.claude/agents/e2e-result-reviewer.md:4` vs. `selenium-test-reviewer` and `selenium-test-generator`.
      Fix: Append negative triggers to `description` ("nicht für Code-Review der Selenium-Test-Implementierung → `selenium-test-reviewer`; nicht für Test-Generierung → `selenium-test-generator`.").
      Verify: `description` contains "nicht für" / "don't use for" or equivalent negation naming the two closest peers.

- [ ] [agent-management.prompt-structure-order] Body opens with role + Kernaufgabe + reference table, then jumps straight into "Workflow" / Schritte; the expected output shape only emerges at Schritt 7. The role/output/method ordering required by `agent-management.recommendations` SHOULD is therefore split.
      Where: `.claude/agents/e2e-result-reviewer.md:10-127`.
      Fix: Move the output contract (currently Schritt 7 + report template) up to immediately after the role block, before the procedure (Schritte 1-6).
      Verify: First three top-level sections, in order, are role / output / method.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: opus` is justified by multimodal screenshot analysis — a strong rationale that fits the `agent-review` model-plausibility check perfectly. Consider also naming the "Visual diff against spec" task as the load-bearing reason for opus rather than just "Vision-Tiefe", to make the rationale auditable.
      Where: `.claude/agents/e2e-result-reviewer.md:6-7`.
      Fix: Add a one-phrase clarification: "opus for multi-image visual reasoning + spec correlation; sonnet/haiku miss subtle layout regressions in dense MUI screenshots".
      Verify: The model-rationale comment names the visual-correlation task explicitly.

### INFO

- [ ] [agent-management.project-language-exception] Body and `description` are authored in German. Under `agent-management` rev 7772341 this is permitted: the agent declares `distribution: project` and Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agent prose. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`) are correctly English. Iteration 1 had recorded this as a BLOCKER under the prior spec revision; downgrade is the central delta of this re-review.
      Where: `.claude/agents/e2e-result-reviewer.md:4` (description) + `:10-210` (body).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is correctly set; this is consistent with kamerplanter's project-only agent setup and is the precondition activating the project-language exception above.
      Where: `.claude/agents/e2e-result-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.length] Body is ~210 lines, just past the ~200-line soft target — borderline; flagged for awareness only, not a WARNING. The reference-document table and the report template are the obvious factor-out candidates if the file grows.
      Where: `.claude/agents/e2e-result-reviewer.md:1-210`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
