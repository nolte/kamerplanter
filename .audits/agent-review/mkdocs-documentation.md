---
review-type: agent-review
target: ".claude/agents/mkdocs-documentation.md"
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
status: in-progress
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: mkdocs-documentation

## Scope

Target: `.claude/agents/mkdocs-documentation.md` (frontmatter + 821-line body, no sibling assets under `agents/mkdocs-documentation/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent` (rev 0e3b6f9), `review-plan` (rev 0e3b6f9), `agent-review` (rev 7772341).
Narrowing: none — full re-review (Iteration 2). The relaxed language SHOULD applies: Kamerplanter `CLAUDE.md` lines 9-11 authorize German prose for `distribution: project` agents, so German body+description drop from BLOCKER to INFO. Frontmatter field names + technical identifier values remain English.
Explicitly out of scope: runtime behavior of MkDocs builds, Vale/markdown style, and the duplicate-prevention check against possible documentation skills in `nolte-shared`.

## Summary

- BLOCKER: 1
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — one BLOCKER (rationale section) remains.
Next concrete action: author adds a skill-vs-agent rationale section; trim/factor the 821-line body; address tags and model-rationale WARNINGs.

## Findings

### BLOCKER

- [x] [skill-vs-agent.Rationale-documentation] No rationale section names a decisive skill-vs-agent dimension for the agent-over-skill choice.
      Where: `.claude/agents/mkdocs-documentation.md` body (no "Begruendung"/"Rationale" section anywhere in the 821 lines).
      Fix: Add a short "Skill-vs-Agent-Begruendung" section naming the decisive dimensions (e.g. specialization for MkDocs Material conventions, context-window protection for large mkdocs.yml templates, tool restriction).
      Verify: `grep -i 'rationale\|begruendung\|skill-vs-agent'` returns at least one body-level match.

### WARNING

- [ ] [agent-management.Body-length] Body is 821 lines, far above the ~200-line soft target; large blocks of `mkdocs.yml`, GitHub Actions YAML, CSS, abbreviations and Mermaid examples are inlined rather than factored.
      Where: lines 184-368 (full mkdocs.yml), 589-664 (CI workflow), 678-700 (CSS), 778-794 (abbreviations).
      Fix: Move long-form references into a sibling folder `agents/mkdocs-documentation/` (e.g. `mkdocs.yml.template`, `ci-deploy.yml.template`, `extra.css.template`, `abbreviations.md.template`) and reference them by relative path.
      Verify: Body length drops below ~300 lines and inlined templates are replaced with relative-path references.

- [ ] [agent-management.Model-selection-justification] Pinned `model: sonnet` only carries a one-line frontmatter comment; the body never repeats the rationale.
      Where: frontmatter line 6 (comment) — body has no model-rationale paragraph.
      Fix: Add a short body-level model-rationale (e.g. under "Ausgabe nach Arbeit"): "sonnet for multilingual prose generation; haiku would underfit ADR/guide nuance".
      Verify: `grep -i 'sonnet\|modell' .claude/agents/mkdocs-documentation.md` returns a body-level mention.

- [ ] [agent-management.Side-effects-documentation] `tools` declares `Write`, `Edit`, and `Bash`, but the system prompt never lists the side-effect targets and preconditions in a dedicated section.
      Where: frontmatter line 5 (tools) — body lacks an explicit write-targets section.
      Fix: Add a "Schreibrechte und Bash-Nutzung" subsection naming the targets (`docs/**`, `mkdocs.yml`, `.github/workflows/docs.yml`) and bash preconditions (only `mkdocs build --strict`, `mike` deploy, `linkchecker`).
      Verify: Body contains an explicit listing of write targets and bash command boundaries.

- [ ] [agent-management.Tools-bash-preference] `Bash` is declared but every example bash invocation (`mkdocs build`, `mike`, `linkchecker`, `pip install`) is for command execution that has no dedicated tool — declaration is justified, but the body never says so.
      Where: frontmatter line 5 (tools) — body never disambiguates Bash from Read/Edit roles.
      Fix: Note in the body that `Bash` is required for `mkdocs build --strict`, `mike deploy`, and `linkchecker` since no dedicated tool covers those.
      Verify: Body contains a one-paragraph rationale for the `Bash` declaration.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary] No `tags` field; the catalog cannot place this agent in a documentation cluster.
      Where: frontmatter (no `tags` key).
      Fix: Add `tags: [scaffolding, prose]` or similar from the starter vocabulary.
      Verify: Frontmatter parses with a `tags` list of <=5 lowercase ASCII kebab-case entries.

### INFO

- [ ] [agent-management.Structure-language] Description and body authored in German.
      Where: frontmatter `description` line 4 + entire body.
      Fix: n/a — Kamerplanter `CLAUDE.md` lines 9-11 authorize German prose for `distribution: project` agents.
      Verify: n/a (informational).

- [ ] [agent-review.Review-procedure] Iteration 2 re-review applies the relaxed language SHOULD; previous language BLOCKER drops to INFO.
      Where: this plan's `## Scope`.
      Fix: n/a (procedural note).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-27 — Rationale-documentation — added "## Rationale: Skill vs Agent" naming Specialization, Context-window protection, Self-contained; counter-dimension Lifecycle addressed — verified: grep "Rationale" matches body
