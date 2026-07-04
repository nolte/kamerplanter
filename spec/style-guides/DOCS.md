# Documentation Style Guide — MkDocs Material (DE/EN)

> Mandatory style guide for the Kamerplanter end-user and reference documentation under `docs/`.
> Enforced by `mkdocs build --strict` (`task docs:build`), the docs Lektorat-Audit (D1–D6) pass, and
> manual DE/EN parity review — see NFR-005 (Technische Dokumentation mit MkDocs Material).

**Scope:** `docs/de/`, `docs/en/`, `mkdocs.yml`, `docs/includes/`, `docs/stylesheets/`

**References:**
- `spec/analysis/docs-audit-execution-plan-2026-07.md` §0 — origin of these conventions (Fable-5 audit, Waves 1–5, patterns M-1/M-2/M-5)
- `spec/style-guides/BACKEND.md`, `FRONTEND.md`, `HELM.md`, `HA-INTEGRATION.md` — sibling code style guides
- `.claude/agents/mkdocs-documentation.md` — the executing authoring role for this guide

---

## 1. Tooling & Verification

| Tool | Purpose | Command |
|---|---|---|
| MkDocs (strict build) | Validates broken links/anchors/nav for both languages | `task docs:build` (isolated `.venv-docs`; see `Taskfile.yaml`) |
| MkDocs serve | Local preview | `task docs:serve` |
| Lektorat-Audit (D1–D6) | Editorial/factual proofreading pass over changed pages | run over every changed `docs/**` page (DE + EN) before committing |
| `scripts/docs/gen_catalog.py` | Regenerates the skill/agent catalog pages | `task docs:catalog` |
| `scripts/docs/gen_fact_tables.py` (planned, WP-P1 of the audit plan) | Regenerates drift-prone fact tables from backend code/seed data | include target for the tables listed in §7 |

### 1.1 Definition of Done (every docs change)

1. `task docs:build` passes — no broken links/anchors, both languages build successfully.
2. DE/EN parity: identical heading structure, both files touched together (see §2).
3. Every factual claim is checked against the actual code/seed data, not just the spec (see §9) — no "docs ahead of implementation".
4. Lektorat-Audit (D1–D6) run over all changed `docs/` pages (DE + EN); findings above the severity threshold are fixed before commit.
5. If a page references frontend UI, the label/button text quoted matches the real i18n key output, not an invented name.

---

## 2. Languages — DE is canonical, EN is mirrored

- German (`docs/de/`) is the canonical source language; English (`docs/en/`) mirrors it 1:1.
- Every content change is made **pairwise**: touch `docs/de/<path>.md` and `docs/en/<path>.md` in the same commit/PR, with an **identical heading structure** (same number and order of `##`/`###` sections).
- `docs_structure: folder` (mkdocs-static-i18n) requires identical slugs between the two trees — never rename a slug in one language without the other.
- A page existing in only one language is a defect (a "Freshness" finding), unless explicitly and temporarily flagged as work-in-progress in the PR description.

---

## 3. Voice — informal "du" (deliberate, not "Sie")

- German pages address the reader with the informal **"du"** form throughout — e.g. "Klicke auf …", "Trage deinen Standort ein …", "dein Pflanzdurchlauf".
- This is a deliberate, portfolio-wide product-voice decision. It was **raised and explicitly set aside as out of scope** in all four Lektorat rounds (finding "D4"). Do **not** "fix" it to "Sie" in a future editorial pass — that would be a product decision, not an editorial one.
- English pages use neutral second-person "you"; no formality distinction applies in English.

---

## 4. Admonition conventions (resolves audit patterns M-1 / M-2)

Feature-implementation status is signalled through a fixed set of MkDocs Material admonitions, placed **at the top of the page or section** they describe.

| Status | Admonition | DE title (verbatim) | EN title (verbatim) | Body tense |
|---|---|---|---|---|
| Not implemented / scaffold only | `!!! warning` | `"Noch nicht implementiert"` | `"Not yet implemented"` | Future tense throughout ("wird … bieten", "wirst du … können") |
| Partially available | `!!! note` | `"Teilweise verfügbar"` (optionally suffixed, e.g. `"Teilweise verfügbar: Status „Ernte""`) | `"Partially available"` (same optional suffix pattern) | Present tense for the implemented part, future tense for the rest; mark affected subsections individually |
| API-only / operator configuration, no UI | `!!! info` | `"Nur über API / Betreiber-Konfiguration"` (or scoped, e.g. `"Nur über API: EC-Verdünnungsrechner"`) | `"API only / operator configuration"` (or scoped, e.g. `"API only: EC Dilution Calculator"`) | Present tense — the API/env-var path is real and documented as such |

**Rules:**
- The admonition **title never contains a REQ-/Issue-ID** (Lektorat finding from Wave 1) — the title stays plain-language and laienverständlich.
- A REQ-ID useful for traceability goes into the first sentence of the callout body, glossed, e.g. "Dieses Feature ist geplant (interne Referenz: REQ-031)" — never as a bare `REQ-031` token, and never in the title.
- Example (verbatim, from `docs/de/guides/climate-zones.md`):

```markdown
!!! warning "Noch nicht implementiert"
    Dieses geplante Feature ist noch nicht umgesetzt. Die folgenden Abschnitte
    beschreiben das geplante Verhalten im Futur. <!-- REQ-039 -->
```

- Use the scoped-suffix form (`"Teilweise verfügbar: <Sub-Feature>"`, `"Nur über API: <Sub-Feature>"`) when only part of a page/section is affected, so multiple admonitions on one page each name what they scope, rather than repeating an unscoped generic title three times.

---

## 5. Internal IDs (REQ-/Issue-/NFR-) — never in reader-visible text

- REQ-, Issue- and NFR-identifiers exist for engineering traceability only. They **must never appear as a bare identifier in reader-visible text** — not in page titles, not in admonition titles, not in running prose, not in a table cell a garden-hobbyist reader would see.
- The only permitted place for a raw ID is an HTML comment, `<!-- REQ-XXX -->`, placed at the end of the relevant paragraph or admonition — invisible in the rendered site, grep-able in the Markdown source for traceability.
- If an ID must be surfaced to the reader at all (rare — e.g. "this is tracked internally"), it is glossed in prose ("interne Referenz", "intern verfolgt als") — never as a naked code-styled `REQ-031` token in the visible text.
- This is stricter than a few pre-existing pages (e.g. an inline "(interne Referenz: REQ-031)" gloss, or a REQ column in `user-guide/index.md`). Those predate this guide and are not automatically non-compliant — align them opportunistically the next time the page is touched for another reason; do not treat this guide as retroactively broken by them.

---

## 6. Audience separation — end-user vs. technical/self-hoster content

- Raw REST endpoints, `curl` examples, environment variables, Kubernetes/Helm details and other operator-facing content **never** appear inline on end-user pages (`user-guide/`, `guides/`).
- Where such content is unavoidable on an otherwise end-user page (e.g. a self-hosted instance needs an env var to enable a feature), it goes into a clearly titled, dedicated subsection with this verbatim heading:
  - DE: `## Für technische Nutzer / Self-Hoster`
  - EN: `## For Technical Users / Self-Hosters`
- Operator/deployment documentation (installation, scaling, backup, environment variables, CI/CD) belongs under `development/` or `deployment/`, never mixed into the end-user `guides/` tree (see audit decision E-5 — the `troubleshooting.md` relocation).

---

## 7. Fact tables — generate from source, don't hand-maintain

Tables mirroring code/seed data drift silently once hand-copied (audit pattern M-3/M-5): Care-Presets, `FAMILY_CARE_MAP`, Starter-Kits, Substrate types, Workflow templates, Enum value lists.

- **Preferred:** generate the table via `scripts/docs/gen_fact_tables.py` and pull it into the page with a `pymdownx.snippets` include, so the table stays in sync with `src/backend/` without manual re-verification per edit.
- **If generation isn't wired up yet:** hand-maintain the table, but mark its origin directly above it with `<!-- Quelle: <path/to/source-file> -->`, so the next editor knows exactly where to re-verify it.
- Never invent counts or values ("11 Starter-Kits", "16 Workflow-Templates") without checking them against the current code/seed data first — drifted, hand-typed counts made up the majority of the Wave 2 findings.

---

## 8. Terminology & abbreviations

- Gloss a domain term on its **first occurrence per page** (a short inline clause) or link to `reference/glossary.md` if a longer explanation is warranted.
- Spell out abbreviations (EC, VPD, GDD, IPM, OIDC, PWA, DWC, NFT, …) once per page at first use, e.g. "Leitfähigkeit (EC)". `docs/includes/abbreviations.md` (auto-appended via `pymdownx.snippets`) provides the hover-tooltip glossary but does **not** replace the inline spell-out on first use.
- Use the established DE↔EN term mapping consistently (Stammdaten/Master Data, Pflanzdurchlauf/Planting Run, Karenzzeit/Pre-Harvest Interval, Dampfdruckdefizit (VPD)/Vapor Pressure Deficit (VPD), etc.) — never introduce a synonym for an already-established term.

---

## 9. Verification of claims against code

- Every statement of the form "you can …" / "the system does …" is checked against `src/backend/` and `src/frontend/` (or seed data) before it is written, or re-checked while editing the surrounding section — not inferred from the spec alone.
- If a spec'd feature (`spec/req/`) is not implemented, the page uses the admonition convention in §4 — it does not silently describe the spec as if it were already shipped.
- When editing an existing page for an unrelated reason, re-verify at minimum the claims in the section actually being touched; do not propagate a stale claim forward untouched.

---

## 10. Known open issue — German quotation-mark typography

German pages inconsistently mix curly quotes (`„…"`) with a straight closing quote instead of the curly one (e.g. `„Klon"` in `docs/de/guides/journey-cannabis-cycle.md`, closed with `"` instead of `"`). This is a **site-wide typography defect**, not a per-page content issue.

- **Do not** fix this ad hoc as a side effect of unrelated content edits — a partial fix makes the inconsistency worse (some pages "modernized", others not) and pollutes unrelated diffs.
- It is tracked as its own, dedicated, site-wide find/replace pass (own PR, own review), not bundled into content work packages.

---

## 11. For Agents (`mkdocs-documentation`)

This guide is directly actionable alongside `BACKEND.md` / `FRONTEND.md` / `HELM.md` / `HA-INTEGRATION.md`: the admonition templates and verbatim titles in §4 can be copy-pasted, and the checklist in §1.1 is the pre-commit gate. See `.claude/agents/mkdocs-documentation.md` for the full authoring role, and `spec/analysis/docs-audit-execution-plan-2026-07.md` for the audit history these rules resolve (WP-P2).
