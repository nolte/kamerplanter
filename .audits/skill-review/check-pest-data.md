---
review-type: skill-review
target: ".claude/skills/check-pest-data/SKILL.md"
target-kind: skill
specs-applied:
  - slug: skill-management
    revision: "96c513fb9d16293892911440acb7a3dfb802dcac"
  - slug: skill-vs-agent
    revision: "96c513fb9d16293892911440acb7a3dfb802dcac"
  - slug: review-plan
    revision: "96c513fb9d16293892911440acb7a3dfb802dcac"
  - slug: skill-review
    revision: "96c513fb9d16293892911440acb7a3dfb802dcac"
repo-revision: "83e78b49bae96b18aee56dc58dc9fd245fe49d76"
created: "2026-06-22"
status: complete
---

# Skill Review: check-pest-data

## Scope

Target: `.claude/skills/check-pest-data/` (SKILL.md only — no bundled
templates/assets/scripts; the skill reads repo source files
`ipm.yaml`, `ipm.schema.yaml`, `domain/models/ipm.py`, `pest_taxonomy.py`,
`beneficial.py` as runtime input, not as skill-bundled references).
Specs applied: `skill-management`, `skill-vs-agent`, `review-plan`,
`skill-review` (canonical `en`, revisions in frontmatter; specs hosted in the
sibling `claude-shared` repo, the authoritative skill-authoring corpus).
Validator: override — `skills-ref` / Taskfile `validate:skills` is not
provisioned in the kamerplanter repo; documented per `skill-review` §"Checks
derived from external skill-structure validation" rather than silently skipped.
Narrowing: none.

**Cross-repo convention override (documented project decision).** The target is
a **kamerplanter project skill** (`.claude/skills/`), not a `nolte-shared`
plugin skill. kamerplanter governs project skills under its own
`CLAUDE.md` project-language convention (German documentation, English
identifiers) and a lighter `check-*` skill shape (cf. `check-architecture`).
Two `skill-review` checks are therefore overridden, anchored in
kamerplanter `CLAUDE.md`:
- §"Checks derived from the multilingual-template default" (English-only
  frontmatter/body) → German is the kamerplanter convention; recorded as `Info`,
  not `Critical`.
- §"Checks derived from `skill-vs-agent`" (rationale section as `Critical`) →
  applied **advisory** because the nolte-shared plugin specs don't govern
  kamerplanter project skills; recorded as `Warning`, not `Critical`.

Explicitly out of scope: runtime behaviour of the skill, Vale/markdown style
(handled by `task lint`), dispatched agents beyond confirming orchestration
direction.

## Summary

- Critical: 1
- Warning: 2
- Suggestion: 2
- Info: 2

Go/no-go: CONDITIONAL — resolve the one Critical (add a `spec/...` anchor)
before relying on the skill; everything else is non-blocking polish.
Next concrete action: author adds `spec/req/REQ-010_IPM-System.md` and
`spec/req/REQ-044_Schaedlingserkennung.md` citations to the SKILL.md body.

## Findings

### Critical

- [x] [skill-review.spec-anchor] SKILL.md body cites no `spec/...` path; it
      references REQ-010 / REQ-044 by ID and points at `src/backend/...` source
      files, but never the requirement spec itself.
      Where: `.claude/skills/check-pest-data/SKILL.md` — Schritt 1 data-source
      table and throughout.
      Fix: add references to `spec/req/REQ-010_IPM-System.md` and
      `spec/req/REQ-044_Schaedlingserkennung.md` (the sibling `check-architecture`
      skill already cites `spec/nfr/NFR-001_Separation-of-Concerns.md`, so this
      matches the kamerplanter convention, not just the nolte-shared spec).
      Verify: `grep -q 'spec/req/REQ-0' .claude/skills/check-pest-data/SKILL.md`.

### Warning

- [x] [skill-vs-agent.rationale] No rationale section names why this capability
      is a **skill** rather than an **agent**, despite two overlapping agents
      existing (see next finding). Applied advisory per the Scope override.
      Where: `.claude/skills/check-pest-data/SKILL.md` — no "Abgrenzung"/rationale
      block.
      Fix: add a 2–3 line note: skill = deliberate, user-invoked, in-loop check
      with an inline report; the deep biology + indoor/outdoor lens is the
      decisive dimension; counter-dimension: a fire-and-forget agent would lose
      the interactive "soll ich korrigieren?" gate.
      Verify: a rationale/Abgrenzung paragraph naming ≥1 decisive dimension is
      present.

- [x] [skill-review.duplicate-capability] Capability overlap with existing
      agents `seed-data-validator` (validates seed YAML incl. botanical
      plausibility, forwards `[AGROBIO-CHECK]` findings) and
      `agrobiology-requirements-reviewer` (agrobiology review). Without an
      explicit split, a user won't know which to reach for.
      Where: `.claude/agents/seed-data-validator.md`,
      `.claude/agents/agrobiology-requirements-reviewer.md` vs. this skill.
      Fix: state the split in the SKILL.md body — this skill = pest-record
      *Fachlichkeit* (taxonomy, ecology, damage-vs-feeding, indoor/outdoor IPM);
      `seed-data-validator` = schema/referential integrity;
      `agrobiology-requirements-reviewer` = spec-level review.
      Verify: SKILL.md names the two agents and the delimitation.

### Suggestion

- [x] [skill-review.best-practices.gotchas] The branch-divergence caveat
      ("enriched Steckbrief-Felder may be absent in the current branch") is
      inline prose in Schritt 1; a non-obvious environment gotcha that belongs in
      a dedicated section.
      Where: `.claude/skills/check-pest-data/SKILL.md` — Schritt 1 "Wichtig:".
      Fix: lift it into a `## Gotchas` section (the enriched `Pest` fields live
      on `feat/pest-detail-page`/PR #258, not yet on `develop`).
      Verify: a `## Gotchas` section exists.

- [x] [skill-review.evaluation-discipline] No evaluation scenarios bundled
      (no `examples/` with input prompt + expected behaviour); `Suggestion` for a
      new skill.
      Where: `.claude/skills/check-pest-data/` directory.
      Fix: add 2–3 fixtures, e.g. a pest entry with honeydew wrongly attributed
      to a spider mite (expect a 🔴 Dimension-C finding) and a clean entry.
      Verify: an `examples/` folder with ≥3 scenarios exists.

### Info

- [x] [skill-review.multilingual] Frontmatter `description` and body are German.
      Diverges from the nolte-shared English-only rule but conforms to
      kamerplanter `CLAUDE.md` (project-language convention) and matches the
      sibling `check-*` skills. Overridden in Scope.
      Where: `.claude/skills/check-pest-data/SKILL.md` — frontmatter + body.
      Fix: n/a (observation — intentional per project convention).
      Verify: n/a.

- [x] [skill-management.description-third-person] `description` uses the
      imperative "Nutze diesen Skill …" rather than strict third person; matches
      the existing kamerplanter `check-architecture` description style, so kept
      for consistency. (`name` valid, `description` 481/1024 chars, body 180/500
      lines — all within platform limits.)
      Where: `.claude/skills/check-pest-data/SKILL.md` — frontmatter `description`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->

2026-06-22 — spec-anchor — added `spec/req/REQ-010_IPM-System.md` + `spec/req/REQ-044_Schaedlingserkennung.md` citations to the Rolle section — verified: `grep -c 'spec/req/REQ-0' SKILL.md` = 2
2026-06-22 — skill-vs-agent.rationale — added `## Abgrenzung (warum Skill statt Agent)` with decisive + counter dimension — verified: `grep -c '## Abgrenzung' SKILL.md` = 1
2026-06-22 — duplicate-capability — same Abgrenzung section names `seed-data-validator` + `agrobiology-requirements-reviewer` and the split — verified: `grep -c 'seed-data-validator\|agrobiology-requirements-reviewer' SKILL.md` = 2
2026-06-22 — gotchas — branch-divergence caveat lifted from Schritt 1 into `## Gotchas` (+ family-rank + deferred-WebSearch notes) — verified: `grep -c '## Gotchas' SKILL.md` = 2 (heading + cross-ref)
2026-06-22 — evaluation-discipline — added `examples/` with README + 3 fixtures (honeydew-on-spider-mite, inverted-humidity, clean-whitefly) — verified: `ls examples/fixtures | wc -l` = 3
2026-06-22 — multilingual / description-third-person — Info observations acknowledged; kept per kamerplanter `CLAUDE.md` project-language convention — verified: n/a (intentional)
