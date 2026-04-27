---
review-type: agent-review
target: ".claude/agents/selenium-test-reviewer.md"
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

# Agent Review: selenium-test-reviewer

## Scope

Target: `.claude/agents/selenium-test-reviewer.md` (frontmatter + body, ~295 lines, no sibling assets under `.claude/agents/selenium-test-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, NFR-008/008a content correctness, the dispatching skill (none declared).

## Summary

- BLOCKER: 4
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: body is German, no rationale section, no upfront output contract, write-effect goals/preconditions are implied (the agent edits/creates Selenium files) but not declared. Also material duplicate-prevention overlap with `selenium-test-generator` (both touch the same files) and the `check-test-pyramid` skill.
Next concrete action: author addresses the four BLOCKERs (translate body, add rationale, lift output contract, document Edit/Bash write-effect goals/preconditions) and clarifies the boundary against the generator agent.

## Findings

### BLOCKER

- [ ] [agent-management.english-body] Frontmatter `description` and the entire system-prompt body are German; `agent-management` Structure-MUST requires English content.
      Where: `.claude/agents/selenium-test-reviewer.md:4` (description) and lines 10-295 (entire body — phase headings, table columns, anti-pattern explanations, embedded comments).
      Fix: Translate description, all section headings ("Schritt 1: Tests und Konfiguration finden" → "Step 1: Locate tests and config"), prose, table columns, and code comments to English. Keep German only when literally quoting NFR-008 spec section titles or German UI literals.
      Verify: A `lang detect` pass on body returns >95% English; section headings read `## Step N:` etc.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/selenium-test-reviewer.md:1-295` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *specialization* (NFR-008 compliance review of Selenium tests), *tool restriction* (no `Write` — only `Edit` — to constrain damage), and *self-contained input/output* (existing tests in, compliance report + targeted edits out). Cite at least one counter-dimension.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep returns ≥1 hit for "specialization" or "tool restriction".

- [ ] [agent-management.output-shape] Expected output shape is described only in Step 6 as a Markdown report skeleton inside the prompt; the file lacks an upfront "Output contract" stating what the parent caller receives (report + edits).
      Where: `.claude/agents/selenium-test-reviewer.md:223-273`.
      Fix: Add an "Output contract" section near the top stating: (a) what the parent receives (a NFR-008 compliance report in chat plus targeted edits to `tests/e2e/**`), (b) the report's required sections (struktur-compliance, kernfunktions-abdeckung, code-qualität, behobene probleme, offene empfehlungen), (c) the file-edit policy (declared in BLOCKER below), (d) syntax-check output expectations from Step 7.
      Verify: A "Output contract" section exists near the top; reading it tells a parent caller what the deliverable looks like.

- [ ] [agent-management.write-effects-documented] Agent declares `Edit` and `Bash` (write/execution tools) and the body mandates fixes (Step 6 "Behobene Probleme" with file:line, Step 7 pytest --collect-only); yet the system prompt does not declare goals/preconditions of those side effects per `agent-management.acceptance`.
      Where: `.claude/agents/selenium-test-reviewer.md:5` (`tools: Read, Edit, Grep, Glob, Bash`) vs. body Step 5-7.
      Fix: Add an explicit "File outputs and edits" subsection near the top declaring (a) edits are confined to `tests/e2e/**` (no edits to `src/` production code), (b) preconditions (existing test logic and TC references preserved per Step 7 prinzipien), (c) when missing files (`base_page.py`, `protocol_plugin.py`) may be created, (d) the bash invocation `pytest --collect-only` is the only execution side effect.
      Verify: A "File outputs and edits" section exists; it scopes edits to `tests/e2e/**`, names preconditions, and lists the only bash command run.

### WARNING

- [ ] [agent-review.duplicate-prevention] Material capability overlap with peer `selenium-test-generator`: both touch the same `tests/e2e/**` files, both reference NFR-008/008a, and the boundary "generate vs. review" is fuzzy because the reviewer is allowed to *create* missing files (Step 6 "Wichtige Prinzipien" at line 290-291). Also overlap with the `check-test-pyramid` skill which audits the broader test pyramid and the `test-extract` skill which extracts E2E cases from REQ.
      Where: `.claude/agents/selenium-test-reviewer.md:4` (description) and lines 290-291; vs. peers `selenium-test-generator`, `check-test-pyramid`, `test-extract`.
      Fix: Add explicit negative triggers to `description` ("don't use for greenfield scaffolding of the `tests/e2e/` directory — use `selenium-test-generator`; don't use for full-pyramid coverage audits — use `check-test-pyramid`; don't use for extracting test cases from REQ — use `test-extract`"). Also tighten Step 6's "Wichtige Prinzipien" to state that creation of `base_page.py` / `protocol_plugin.py` is permitted only when the file is missing, otherwise the agent stops and refers to the generator.
      Verify: `description` contains "don't use for" naming at least the three closest peers/skills; the body's create-when-missing rule is explicit.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, immediately declares "primaere/ergaenzende Referenz" + style guide, then jumps into Step 1; role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored — output shape only emerges in Step 6.
      Where: `.claude/agents/selenium-test-reviewer.md:10-295`.
      Fix: Restructure: persona paragraph → "Output contract" → procedure (Steps 1-7). Keep the style-guide pointer, but move the report skeleton up to live next to the contract.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tags `review` and `quality-gate` would apply per `agent-management.tag-vocabulary` SHOULD (review-type artifact gating NFR-008 quality).
      Where: `.claude/agents/selenium-test-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, quality-gate]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches; the writes intent (Edit) is implicit and is mixed with read-mostly review semantics. Per `agent-management.recommendations` SHOULD this distinction must be visible at dispatch time.
      Where: `.claude/agents/selenium-test-reviewer.md:10-295`.
      Fix: Add a one-line statement near the top: "This agent reviews and minimally edits: it edits files under `tests/e2e/**` only when an NFR-008 compliance fix is required; it never edits production source under `src/`. It also runs `pytest --collect-only` once at the end."
      Verify: One sentence near the top declares write scope, exclusions, and the bash invocation.

- [ ] [agent-review.tool-scope-bash-vs-dedicated] `Bash` is declared and the body uses it once (Step 7 `pytest --collect-only`). The use is justified, but the SHOULD per `agent-review.tool-scope` is to document why the dedicated alternative isn't suitable.
      Where: `.claude/agents/selenium-test-reviewer.md:5` (`tools: ..., Bash`) and lines 277-285 (Step 7).
      Fix: Add a one-line note in Step 7 stating that `pytest --collect-only` is the only bash invocation and there is no dedicated tool alternative for it.
      Verify: Step 7 contains an explicit one-line note justifying bash; or `Bash` is removed and the syntax check is dropped.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (an author may want to approve fix-ups before they land), which would push toward a skill.
      Where: `.claude/agents/selenium-test-reviewer.md:1-295` (will be addressed once rationale section exists).
      Fix: Within the rationale section, add one bullet naming interactivity (fix-approval) as the counter-dimension and the reason it was outweighed (e.g. fixes are minimal and confined to `tests/e2e/`, PR review provides a post-hoc gate).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` and the comment line states a rationale ("Test-Code-Review gegen NFR-008-Konformitaet; sonnet adaequat fuer strukturierte Findings"), satisfying `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/selenium-test-reviewer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; matches project-scoped reuse.
      Where: `.claude/agents/selenium-test-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/selenium-test-reviewer.md:1-295`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
