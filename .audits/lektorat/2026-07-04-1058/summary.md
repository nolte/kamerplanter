# Lektorat Audit Summary

- **Operation:** audit (read-only)
- **Ran at:** 2026-07-04T10:58:45Z
- **Scope:** Welle-1 remediation prose (10 files: 4 DE user-guide, 6 EN)
- **Severity floor:** suggestion
- **Totals:** 8 critical · 21 warning · 1 suggestion · 1 infrastructure condition

## Infrastructure conditions

- **vale-unavailable** (EN): `vale 3.14.1` is installed but no `.vale.ini`/`vale.yml` exists in the worktree → every call returns `E100 config-not-found`. D3/D4 EN mechanics were skipped this run. (Separate follow-up: add a Vale config or run `prose-vale-curator`.)

## Critical

| id | file | dim | issue |
|----|------|-----|-------|
| d2-de-ai-assistant-l3 | docs/de/user-guide/ai-assistant.md | D2 | Bare `REQ-031` in admonition title (jargon for end users) |
| d2-en-ai-assistant-l3 | docs/en/user-guide/ai-assistant.md | D2 | Bare `REQ-031` in admonition title |
| d2-de-privacy-l4 | docs/de/user-guide/privacy.md | D2 | Bare `REQ-025` in first callout |
| d2-en-privacy-l4 | docs/en/user-guide/privacy.md | D2 | Bare `REQ-025` in first callout |
| d2-en-troubleshooting-l161 | docs/en/guides/troubleshooting.md | D2 | `CanG`/`PflSchG` unexpanded in danger callout |
| d2-de-planting-runs-l124 | docs/de/user-guide/planting-runs.md | D2 | `Karenzzeiten` unglossed jargon |
| d1-en-adr-001-l13 | docs/en/adr/001-arangodb-multi-model.md | D1 | LIX 69 (crit>65) — dense compound clauses |
| d1-en-ai-providers-l4 | docs/en/user-guide/ai-providers.md | D1 | LIX 63 (crit>55) — long setup sentences |

## Warning (21)

- **D1 readability (7):** ai-assistant DE l4, ai-providers DE l4, planting-runs DE l31, privacy DE l4, privacy EN l4, ai-assistant EN l39, troubleshooting EN l115 — all marginally over the warn corridor; dominant lever is long-word ratio (technical compounds).
- **D4 register — informal "du" (6):** ai-assistant DE l6, ai-providers DE l127, planting-runs DE l3, privacy DE l6 — site-wide convention (see dismissals).
- **D4 heading case (2):** ai-assistant EN (Welle-1 new headings), troubleshooting EN (pre-existing subsections).
- **D5 wrong-audience API blocks (4):** ai-assistant DE/EN, privacy DE/EN — raw REST/curl detail on end-user pages.
- **D6 coinage (2):** ai-providers EN "click-path", privacy EN "click-paths".

## Suggestion (1)

- d6-en-privacy-l242 — trailing "...if so" reads translated.

See `run.json` for configuration and `dismissals.json` for triage decisions.
