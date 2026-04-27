---
review-type: agent-review
target: ".claude/agents/selenium-test-generator.md"
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

# Agent Review: selenium-test-generator

## Scope

Target: `.claude/agents/selenium-test-generator.md` (frontmatter + body, ~590 lines, no sibling assets under `.claude/agents/selenium-test-generator/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, NFR-008/008a content correctness, the dispatching skill (none declared).

## Summary

- BLOCKER: 4
- WARNING: 6
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: body is German, no rationale section, no upfront output contract, body length is ~3× the soft target with embedded code blocks that should be sibling-asset references; plausible duplicate-prevention overlap with `selenium-test-reviewer` and the `test-extract`/`check-test-pyramid` skills.
Next concrete action: author addresses the four BLOCKERs (translate body, add rationale, lift output contract, factor inline code into sibling assets) and clarifies the boundary against the reviewer agent and the test-extract skill.

## Findings

### BLOCKER

- [ ] [agent-management.english-body] Frontmatter `description` and the entire body are German; `agent-management` Structure-MUST requires English content.
      Where: `.claude/agents/selenium-test-generator.md:4` (description) and lines 10-590 (entire body — phase headings, table columns, prose, comments inside example code).
      Fix: Translate description, all section headings ("Schritt 1: NFR-008 und Testfall-Dokumente lesen" → "Step 1: Read NFR-008 and test-case documents"), prose, table columns, and code comments to English. Keep German only when literally quoting NFR-008 spec section titles or German UI literals (`/standorte`, `/pflanzen`).
      Verify: A `lang detect` pass on body returns >95% English; section headings read `## Step N:` etc.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/selenium-test-generator.md:1-590` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *specialization* (NFR-008-conforming Selenium generation), *self-contained input/output* (REQ list in, test files out), *context-window protection* (large reads of `spec/req/`, `spec/nfr/`, `spec/frontend/` source). Cite at least one counter-dimension.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep returns ≥1 hit for "specialization" or "context-window".

- [ ] [agent-management.output-shape] Expected output shape is described only deep inside Step 4-7 as a directory layout; the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/selenium-test-generator.md:44-590` (output description scattered across Step 4 directory tree, code blocks, and Step 7 abschluss).
      Fix: Add an "Output contract" section near the top stating: (a) what the parent receives (paths created + chat summary), (b) the file set: `tests/e2e/conftest.py`, `tests/e2e/protocol_plugin.py`, `tests/e2e/pages/base_page.py`, page objects, test files, `requirements.txt`, .gitignore patch; (c) overwrite policy when files already exist; (d) the absolute-path constraint per `agent-management.runtime-location` MUST NOT (this agent uses relative paths only).
      Verify: A "Output contract" section exists near the top; reading it tells a parent caller the exact file set and overwrite policy.

- [ ] [agent-management.write-effects-documented] Agent declares `Write`, `Edit`, and `Bash` and Step 4-7 mandates creating numerous files (config, page objects, tests, gitignore patches), yet the system prompt does not declare write-effect goals/preconditions per `agent-management.acceptance` ("targets and preconditions of side effects").
      Where: `.claude/agents/selenium-test-generator.md:5` (`tools: Read, Write, Edit, Glob, Grep, Bash`) vs. body Steps 4-7 silently mandating file creation.
      Fix: Add an explicit "File outputs and edits" subsection near the top declaring (a) all write paths under `tests/e2e/`, (b) the `.gitignore` patch (Step 7), (c) preconditions (e.g. existing tests must not be silently overwritten — diff in PR), (d) the agent never edits production source under `src/`.
      Verify: A "File outputs and edits" section exists; it names each write target and preconditions; declares no edits under `src/`.

### WARNING

- [ ] [agent-management.length-target] Body is ~590 lines — ~3× the ~200-line soft target in `agent-management.recommendations`; long inline code blocks (conftest.py, protocol_plugin.py, base_page.py, page objects) belong in `agents/selenium-test-generator/` sibling files referenced by relative path.
      Where: `.claude/agents/selenium-test-generator.md:67-505`.
      Fix: Factor each code block into `.claude/agents/selenium-test-generator/templates/<file>.py.tpl`; the body links them via relative path. Keep the procedure spine inline.
      Verify: Body is ≤300 lines; `.claude/agents/selenium-test-generator/templates/` contains the factored templates.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap: peers `selenium-test-reviewer` (reviews and may edit Selenium tests), the `test-extract` skill (E2E test cases from REQ), and the `check-test-pyramid` skill (test-suite health checks). The current description does not name negatives.
      Where: `.claude/agents/selenium-test-generator.md:4` (description) vs. peers `selenium-test-reviewer`, `test-extract` (skill), `check-test-pyramid` (skill).
      Fix: Add explicit negative triggers to `description` ("don't use for reviewing existing tests — use `selenium-test-reviewer`; don't use for extracting test cases from REQs as a planning artifact — use the `test-extract` skill; don't use for test-pyramid health audits — use `check-test-pyramid`"). Per `skill-vs-agent.duplicate-prevention` plausibly-overlapping artifacts SHOULD propose a clearer split.
      Verify: `description` contains "don't use for" naming at least the three closest peers/skills.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, immediately declares "primaere/ergaenzende Referenz", then jumps into the project config table; role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored — output shape only emerges in Step 4.
      Where: `.claude/agents/selenium-test-generator.md:10-590`.
      Fix: Restructure: persona paragraph → "Output contract" → procedure (Steps 1-7). Move "Projektkonfiguration" table after the contract.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tags `quality-gate` and `scaffolding` would apply per `agent-management.tag-vocabulary` SHOULD (this agent generates/scaffolds test infrastructure plus enforces an NFR-008 quality gate).
      Where: `.claude/agents/selenium-test-generator.md:1-8` (frontmatter).
      Fix: Add `tags: [quality-gate, scaffolding]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches; the writes intent (full `tests/e2e/` directory) is only implicit via Step 4-7.
      Where: `.claude/agents/selenium-test-generator.md:10-590`.
      Fix: Add a one-line statement near the top: "This agent writes code: it scaffolds the entire `tests/e2e/` directory (conftest, protocol plugin, page objects, test files, requirements.txt) and patches `.gitignore`. It does not modify production source under `src/`."
      Verify: One sentence near the top declares write scope and named paths/exclusions.

- [ ] [agent-review.tool-scope-bash-vs-dedicated] `Bash` is declared but the body's only bash references are example shell snippets in Step 7 (running pytest); the agent's own procedure does not need bash. Dead permission per `agent-review.tool-scope`; SHOULD prefer dedicated tools.
      Where: `.claude/agents/selenium-test-generator.md:5` (`tools: ..., Bash`).
      Fix: Drop `Bash` from `tools` (the example pytest commands are user-side guidance, not agent invocations); or document why bash is required (e.g. for gitignore patch verification).
      Verify: Either `tools` no longer lists `Bash`, or body contains an explicit bash invocation step with rationale.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (test scaffolding decisions like file overwrites would benefit from user confirmation), which would push toward a skill.
      Where: `.claude/agents/selenium-test-generator.md:1-590` (will be addressed once rationale section exists).
      Fix: Within the rationale section, add one bullet naming interactivity (overwrite confirmation) as the counter-dimension and the reason it was outweighed (e.g. fire-and-forget scaffolding under a fresh path).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: opus` and the comment line states a rationale ("Test-Code-Generierung mit Page-Object-Pattern, Screenshot-Checkpoints, NFR-008-Compliance, vielen Constraints"), satisfying `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/selenium-test-generator.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; matches project-scoped reuse.
      Where: `.claude/agents/selenium-test-generator.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/selenium-test-generator.md:1-590`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
