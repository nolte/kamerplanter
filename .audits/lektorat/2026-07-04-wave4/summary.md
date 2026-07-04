# Lektorat Audit — Wave 4 (structure + journeys)

- **Operation:** audit (read-only), one batch over the 6 new prose pages (DE+EN)
- **Scope:** glossary, plant-health-troubleshooting, 4 journeys (cannabis-cycle, garden-year, hydroponics-setup, compliance-anbauvereinigung)
- **Pipelines:** LanguageTool HTTP + LIX; Vale unavailable (no repo config).
- **Totals:** 37 findings (8 critical, 27 warning, 2 suggestion).

## Positive baseline

- **D5 clean:** no raw endpoints, no visible REQ-IDs (internal ZG-IDs only in HTML comments). Both refined conventions held.
- No accidental language-mixing; deliberate bilingual glosses are by design.
- „du" address correctly recognised as the pre-existing site-wide convention (no D4 regression raised).

## Applied

- **D1 critical (8×) — real run-on sentences (ASL 40–55), not just compound density:** the four-symptom lead of the symptom guide (LIX 84/83), the compliance GDPR-erasure/PHI sentences, the cannabis drying/flowering sentences, the hydroponics EC-budget sentence — all split into shorter sentences. This is the first wave where D1 fixes were substantive (laypeople-facing pages).
- **D2:** EC, photoperiod, Karenzzeit/PHI, RO glossed inline or linked to the new `reference/glossary.md` (missing "See Also" glossary links added).
- **D3 (real grammar):** „begünstigt das Pilzkrankheiten"→„…Pilzkrankheiten"; missing commas before infinitive clauses; „Growzelt"/„Grow-Zelt" unified.
- **D6:** „bewirtschaften"→„betreiben", „freely enterable"→„freely editable", adverb placement fixed.

## Deferred (documented, not regressions)

- Site-wide informal „du" address.
- German quote typography („…" closed with ASCII `"`) — site-wide legacy style.
- Marginal D1-LIX warnings from domain-compound density (glossary VPD/NFT entries kept — shortening would cut substance).

Verified with `task docs:build` (green, no dead anchors); glossary anchor targets confirmed.
