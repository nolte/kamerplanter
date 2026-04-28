---
review-type: agent-review
target: ".claude/agents/selenium-test-generator.md"
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

# Agent Review: selenium-test-generator

## Scope

Iteration 2 of this plan. The `agent-management` and `agent-review` specs have been revised: a project-distribution agent in a project whose root convention file (`CLAUDE.md`) authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here.

Target: `.claude/agents/selenium-test-generator.md` (frontmatter + body, ~590 lines, no sibling assets under `.claude/agents/selenium-test-generator/`).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, factual correctness of the embedded Selenium code samples, the dispatching skill (none declared but the project's `quality-gate` and `test-extract` skills are conceptually adjacent).

## Summary

- BLOCKER: 3
- WARNING: 6
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three remaining MUST violations after the language relaxation: missing rationale section, missing upfront output contract, and consolidated write-effect goals/preconditions for the substantial files this agent creates under `tests/e2e/` plus a `.gitignore` mutation.
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effects section listing every created/modified path) and trims the 590-line body via sibling assets.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/selenium-test-generator.md:1-590` (no "Why this is an agent" section).
      Fix: Add a short rationale paragraph near the top naming decisive dimensions — most plausibly specialization (NFR-008/NFR-008a-conformant scaffolding, Page-Object pattern, screenshot checkpoints), context-window protection (large reads of `spec/req/`, `spec/nfr/`, frontend Router/data-testid scan), and self-contained input/output (testfall-doc → tests/e2e/ tree). Important given the peer `selenium-test-reviewer` agent.
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep returns ≥1 hit for "specialization", "context-window", or "self-contained".

- [ ] [agent-management.output-shape] Expected output shape is implied by the embedded code blocks (conftest, protocol_plugin, base_page, multiple page objects, multiple test files, requirements.txt) but the file lacks an upfront "Output contract" enumerating every created path.
      Where: `.claude/agents/selenium-test-generator.md:44-590`.
      Fix: Add an "Output contract" section near the top stating (a) the full list of created files (`tests/e2e/conftest.py`, `tests/e2e/protocol_plugin.py`, `tests/e2e/pages/base_page.py`, per-feature page objects, per-feature test files, `tests/e2e/requirements.txt`), (b) any `.gitignore` mutation (`test-reports/`), (c) the chat-summary shape, (d) the overwrite policy if files already exist.
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller every deliverable.

- [ ] [agent-management.write-effects-documented] Agent declares `Read, Write, Edit, Glob, Grep, Bash` and creates many production-test files plus mutates `.gitignore`, but the system prompt does not consolidate the goals and preconditions of those side effects upfront.
      Where: `.claude/agents/selenium-test-generator.md:5` (tools) vs. body lacking an upfront write-goals block.
      Fix: Add a "File outputs" section consolidating: every created path, the `.gitignore` patch, preconditions (existing tests/e2e/ tree honored, no overwrite without explicit signal), and the explicit invariant that frontend production code is never modified.
      Verify: Body contains a single consolidated write-effects section naming every target and the `.gitignore` mutation; grep for "tests/e2e" and ".gitignore" both return hits in that section.

### WARNING

- [ ] [agent-management.body-length] Body is ~590 lines, well above the SHOULD soft target of ~200 lines. Long-form code samples (conftest, protocol_plugin, base_page, three page objects, three test files) should move into `.claude/agents/selenium-test-generator/templates/` and be referenced by relative path.
      Where: `.claude/agents/selenium-test-generator.md:1-590`.
      Fix: Factor each code sample into a sibling template file under `.claude/agents/selenium-test-generator/templates/` and reference them; keep the body as a procedural index pointing at the templates.
      Verify: Body length drops below ~250 lines; sibling folder exists.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `selenium-test-reviewer` (peer agent, same NFR-008 surface) and with the project's `e2e-testcase-extractor` agent (test-case discovery from spec). Per `agent-review.duplicate-prevention` this is a WARNING; the `description` does not declare negative triggers naming either peer.
      Where: `.claude/agents/selenium-test-generator.md:4` vs. peers `.claude/agents/selenium-test-reviewer.md`, `.claude/agents/e2e-testcase-extractor.md`.
      Fix: Add negative triggers to `description`: "nicht für Review existierender Tests — dafür `selenium-test-reviewer`; nicht für reine Testfall-Extraktion — dafür `e2e-testcase-extractor`".
      Verify: `description` contains "nicht für" naming both peer agents.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, then project config table, then a "Workflow" with five steps; output shape is implicit. Role-then-output-then-method ordering SHOULD is not honored.
      Where: `.claude/agents/selenium-test-generator.md:10-590`.
      Fix: Restructure: persona → "Output contract" (deliverable file list) → procedure (Schritte 1-5) → reference templates (in sibling folder).
      Verify: Reading the first 80 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `quality-gate` and `scaffolding` would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/selenium-test-generator.md:1-8` (frontmatter).
      Fix: Add `tags: [quality-gate, scaffolding]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront that the agent writes code; the calling Claude must read it at dispatch time per `agent-management.recommendations` SHOULD.
      Where: `.claude/agents/selenium-test-generator.md:10-590`.
      Fix: Add one sentence near the top: "This agent writes test code under `tests/e2e/` and mutates `.gitignore`; it does not modify frontend or backend production code."
      Verify: One sentence near the top names "writes test code", "tests/e2e/", and "no production-code edits".

- [ ] [agent-review.tools-bidirectional] `Bash` is declared but the body never demonstrably invokes it during code generation (Steps 1-5 use Read/Write/Glob/Grep). The closing "Befehle anzeigen" block lists *example* commands the user should run, not commands the agent runs. Possible dead permission per `agent-review.tool-scope`.
      Where: `.claude/agents/selenium-test-generator.md:5` and lines 580-589.
      Fix: Drop `Bash` from `tools` unless a legitimate use case is added (e.g. `pytest --collect-only` smoke-check after generation); or document the bash use case explicitly.
      Verify: Either `tools` no longer lists `Bash`, or body contains at least one explicit bash invocation block with rationale.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named; for this agent a plausible counter is interactivity (user might want to review the planned file list before generation).
      Where: `.claude/agents/selenium-test-generator.md:1-590` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity as the counter-dimension and explain why it was outweighed (e.g. files are scoped to `tests/e2e/`, easy to revert, and the orchestrator skill can wrap interactivity).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German throughout; per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER.
      Where: `.claude/agents/selenium-test-generator.md:4` (description), lines 10-590 (body).
      Fix: n/a (observation — language exception applies).
      Verify: n/a.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: opus` with rationale ("Test-Code-Generierung mit Page-Object-Pattern, Screenshot-Checkpoints, NFR-008-Compliance"); satisfies `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/selenium-test-generator.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; no plugin-co-located asset references appear.
      Where: `.claude/agents/selenium-test-generator.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/selenium-test-generator.md:1-590`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
