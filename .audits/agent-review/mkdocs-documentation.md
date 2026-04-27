---
review-type: agent-review
target: ".claude/agents/mkdocs-documentation.md"
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

# Agent Review: mkdocs-documentation

## Scope

Target: `.claude/agents/mkdocs-documentation.md` (frontmatter + 821-line body, no sibling assets under `agents/mkdocs-documentation/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: actual MkDocs-Material configuration correctness at runtime, Vale/markdown style, the dispatching skill (none documented).

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language and missing rationale block dispatch readiness; severe length excess.
Next concrete action: rewrite system prompt in English, add rationale section, factor the embedded `mkdocs.yml`, ADR template, GitHub Actions workflow into `agents/mkdocs-documentation/` siblings.

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body is authored entirely in German, including all section headings ("Verbindlicher Tech-Stack", "Mehrsprachigkeit", "Endnutzer-Dokumentation — Schreibregeln", "Absolute Verbote") and procedural directives.
      Where: `.claude/agents/mkdocs-documentation.md:10-821`.
      Fix: rewrite the system prompt in English; user-facing docs output may stay German/English (project convention), but the prompt scaffolding itself must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/mkdocs-documentation.md` returns hits only inside quoted German example strings.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice.
      Where: `.claude/agents/mkdocs-documentation.md` (entire body, no rationale block detected).
      Fix: add a short rationale section naming at least one decisive dimension — likely "specialization" (narrow technical-writer system prompt) plus "context-window protection" (heavy reads of `spec/req/**`, `spec/nfr/**`, `spec/style-guides/**`).
      Verify: a paragraph or bulleted list explicitly stating the skill-vs-agent dimensions exists in the body.

- [ ] [agent-management.Recommendations.SHOULD-length] Body is 821 lines, ~4× the soft ~200-line limit, with very large embedded fragments (full `mkdocs.yml`, `extra.css`, GitHub Actions workflow, ADR template, abbreviations file) inlined instead of referenced.
      Where: `.claude/agents/mkdocs-documentation.md:36-380` (mkdocs.yml + i18n), `:444-495` (ADR template), `:556-664` (mkdocstrings + GitHub Actions), `:674-794` (CSS + Mermaid + abbreviations).
      Fix: factor each embedded artifact (`mkdocs.yml`, `extra.css`, `docs.yml` workflow, ADR template, abbreviations) into `agents/mkdocs-documentation/` siblings and reference by relative path; keep the body to procedural guidance only.
      Verify: body line count drops below ~200 after factoring; sibling files cover the long-form references.

### WARNING

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] The system prompt does not state explicitly whether the agent writes code or only researches, despite declaring `Write`, `Edit`, and `Bash`.
      Where: `.claude/agents/mkdocs-documentation.md:1-12` (frontmatter + opening role statement).
      Fix: add one explicit sentence stating "this agent creates and edits files under `docs/` and may run `mkdocs build --strict` via Bash"; the "Ausgabe nach Arbeit" section at line 798 implies this but never declares it up front.
      Verify: the role section names the side effects and the target paths.

- [ ] [agent-review.Tool-scope.SHOULD-bash-vs-dedicated] Bash is declared, but most of the documented Bash usage (mkdocs build, linkchecker, mike) is justified; one mention (`grep` patterns in build validation) could be a `Grep` call instead.
      Where: `.claude/agents/mkdocs-documentation.md:5` tools list.
      Fix: keep Bash but document the build-/serve-only justification in the role block (build commands genuinely need the shell); spot-check that no body step uses Bash where `Read`/`Glob` would suffice.
      Verify: every Bash invocation in the body has a build/serve/test rationale that a dedicated tool wouldn't cover.

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] The agent description claims responsibility for "ADRs, mkdocs.yml configuration, API-Docs, Guides/Tutorials, Docs-CI/CD, Changelog, mike-Versionierung, Custom-Styling" — eight distinct authoring domains in one agent that risk overlap with future docs/scaffolding skills.
      Where: `.claude/agents/mkdocs-documentation.md:4` description.
      Fix: tighten the description to MkDocs-Material authoring only, or split into focused agents (config, content, ADR, CI/CD) so a future docs-scaffolding skill can dispatch them clearly.
      Verify: description names a single, narrow responsibility plus negative triggers for the carved-out concerns.

- [ ] [agent-management.Recommendations.SHOULD-negative-triggers] The description lists positive triggers but no negative cases ("don't use for…"), even though overlap with content-authoring agents (e.g. plant-info-document-generator) is plausible.
      Where: `.claude/agents/mkdocs-documentation.md:4`.
      Fix: add 1–2 negative triggers, e.g. "do not use for spec authoring (use the spec skill) or for plant info documents (plant-info-document-generator)".
      Verify: description contains explicit "don't use for" phrasing.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; adding one (e.g. `[prose, scaffolding]`) would surface it in the catalog's tag index next to peers.
      Where: `.claude/agents/mkdocs-documentation.md:1-8`.
      Fix: add `tags: [prose, scaffolding]` (each ≤30 chars, list ≤5).
      Verify: frontmatter parses with valid `tags`.

### INFO

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — dispatch direction is clean.
      Where: full body grep clean.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.Tool-access.MUST] Tools declared (`Read, Write, Edit, Bash, Glob, Grep`) all map to documented procedure steps (read specs, write docs, run mkdocs build) — bidirectional check passes on spot-check.
      Where: `.claude/agents/mkdocs-documentation.md:5`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
