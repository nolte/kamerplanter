# Lektorat Audit — Wave 2 (consolidated)

- **Operation:** audit (read-only), 4 parallel scanner batches
- **Ran at:** 2026-07-04 (16:11–16:27Z)
- **Scope:** all ~44 Wave-2 prose pages (DE canonical + EN), grouped Kultur / Wasser-Sensor / Ernte-Pflege / KI-Plattform
- **Pipelines:** LanguageTool HTTP API (DE grammar/spelling) + LIX readability; Vale unavailable (no `.vale.ini` in repo — recorded as `vale-unavailable`, EN D3/D4 Vale mechanics skipped).

## Totals (≈130 findings across 4 batches)

| Dimension | Applied | Deferred |
|-----------|---------|----------|
| D1 readability (LIX) | extreme cases only (companion 70, care-reminders 69, tasks 66, watering-log 68, nutmix 66 → densest sentences split / long enumerations → lists) | marginal warn/crit (majority) — inherent technical-compound density, `how-to` corridor is strict |
| D2 abbreviations/jargon | **all** (IPM, OIDC, RAG, ONNX, GeoNutzV, USDA, TDS, NFT, CalMag, DWC, VPD, Fertigation, ASPCA, HST/LST, EC) expanded once per page / linked | — |
| D3 grammar/spelling | **all real errors** (broken nested-quote admonition title `tasks.md:55`, „eine→einen Kategorie-Chip", „Schimmelpilzen→Schimmelpilze", „von 7–14"→„von 7 bis 14", Tip→Tipp, colon-capitalisation) + compound-consistency (Substratcharge, Gemüsebeet, Re-Ranker, Anfängermodus, Kontoeinstellungen, Aufgabenpakete, Pflegestil, Düngeerinnerung) | German quote typography („…" closed with straight `"`, 33× across 5 DE files) — site-wide legacy style, separate pass |
| D4 register/consistency | English headings in `care-reminders.md` DE → German; "Guard" programmer jargon → plain language | site-wide informal „du" address (deliberate product voice) |
| D5 audience-fit | **all** — REQ-IDs removed from visible prose (→ HTML comments), raw REST endpoints moved into "For technical users" sections (mirroring privacy.md), API-only callouts reframed as self-hoster notes | — |
| D6 idiomatic (EN) | **all** calques/coinages glossed (resin-development, click-path→screen earlier, precipitations, concrete situation, Agrobiologically reviewed, Binding:, few-shot capable, PHI-FAQ circularity, fronted predicates, …) | — |

## Refined convention (Wave-2 learning)

Wave 1 kept REQ-IDs out of admonition **titles**; Wave 2's D5 findings showed they still leaked into **body prose** (harvest/post-harvest/climate-zones). New rule, now applied and to be back-ported to the execution plan: **internal REQ-/Issue-IDs must not appear in any user-visible text** (title or prose) — keep them only as `<!-- REQ-XXX -->` comments for traceability. Raw REST endpoints belong in clearly-labelled "For technical users / self-hosters" sections, never inline on end-user pages.

## Deferred (documented, not regressions)

1. **Informal „du" address** — deliberate, site-wide product voice matching the hobby-grower audiences; flipping only Wave-2 pages would create inconsistency. Same decision as Wave 1.
2. **German quote typography** (`„…"` closed with ASCII `"`) — pre-existing across the whole DE tree (33 occurrences); a dedicated site-wide find/replace pass, not a Wave-2 regression. (The one genuinely broken nested-quote title that risked corrupt rendering *was* fixed.)
3. **Marginal D1-LIX** — dominant lever is unavoidable domain-compound density (Umgebungsvariablen, Winterhärtezonen, pre-harvest interval); only extreme outliers were entzerrt.

Verified with `task docs:build` (green, no dead anchors) after application.
