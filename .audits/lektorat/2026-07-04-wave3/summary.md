# Lektorat Audit — Wave 3 (new pages)

- **Operation:** audit (read-only), one batch over the 4 new pages (DE+EN)
- **Scope:** notifications, import, account (user-guide), data-enrichment (guides)
- **Pipelines:** LanguageTool HTTP + LIX; Vale unavailable (no repo config).
- **Totals:** 49 findings (15 critical, 30 warning, 4 suggestion).

## Positive baseline (refined conventions held)

- **D5 clean:** `data-enrichment.md` frames all curl/endpoint detail under an explicit "For technical users / self-hosters" heading. **No REQ-ID leaked into visible text** — all REQ references sit in HTML comments. Both Wave-1 (no REQ-ID in titles) and Wave-2 (no REQ-ID in prose) conventions were followed by construction.

## Applied

- **D2 abbreviations** (all): PWA, VAPID, SMTP, CSV, GBIF (first-use), DSGVO/GDPR, API expanded once per page.
- **D1 extreme cases**: the three how-to LIX-crit sentences (notifications §channels, import §species-columns, account §linked providers) split into shorter sentences (DE+EN).
- **D6 EN calques/collocations**: "is shown by"→active (2×), "shows a hint/corresponding hint"→"message", "wait out the shown time"→"until the lock expires", "Activation happens per device"→"You activate this per device", completive "again" dropped, "not yet operable from"→"not yet available in", "four figures"→"four metrics".
- **D2 markers**: "einfach"/"just" dropped from upload steps.
- **D4 EN consistency**: British "Colour/Grey" → US "Color/Gray" (matches "center").
- **D5 suggestion**: backend env-var names (HA_URL/HA_ACCESS_TOKEN) removed from end-user prose → "your operator's backend configuration".

## Deferred (documented, not regressions)

- Site-wide informal „du" address (deliberate product voice).
- German quote typography („…" closed with ASCII `"`) — site-wide legacy style.
- Marginal D1-LIX (domain-compound density).

Verified with `task docs:build` (green, no dead anchors).
