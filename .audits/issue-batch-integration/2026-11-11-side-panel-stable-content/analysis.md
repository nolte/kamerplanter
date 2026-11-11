# Group 2026-11-11-side-panel-stable-content

- **Tier:** 2 (one repo, frontend only, no published contract)
- **Source:** partition `2026-11-11-req053-remainder` (operator-approved 2026-11-11), `lane: true` → `committed-locally`
- **Research question:** Why does the side panel lose open dialogs and uncommitted input, and is one structural change enough for both members?
- **Logical change (one sentence):** Side-panel content stays at one stable tree position across panel shape changes and tab navigation, so open dialogs and uncommitted drafts survive and tabs change only on deliberate activation.
- **Plan approval basis:** operator decision E-03 (REQ-053 runs autonomous incl. plan gates) + partition approval 2026-11-11 + "weiter so" 2026-11-11.

## Members

| Issue | Predicate | Evidence (develop c1e2b47aa) | Cause status |
|---|---|---|---|
| #2882 | shared touch surface | `editor/GardenPlanEditor.tsx:1728` `sidePanelElement`, placed at `:2175` (`panelVariant === 'docked'`) and `:2195` (`'sheet'`, inside the dock) → a shape change unmounts the whole panel; `WindowSunSuggestion.tsx:71` keeps `open` in local state; `ObjectTasksSection` dialog state local | verified (grep, this run) |
| #2887 | shared touch surface + thematic coupling | `editor/SidePanel.tsx:127` `selectionFollowsFocus`; `:180` `{value === tab ? children : null}` → arrowing activates "Zonen" and unmounts "Eigenschaften"; draft in `objectProps/PropNumberField.tsx:48` (`useState`) | verified (grep, this run) |

Order: #2882 → #2887 (both edit `SidePanel.tsx`; #2882 settles the mount structure first).

## Structural finding

**Symptom cluster** (confirmed): one cause — panel content state lives in components whose mount is tied to presentation (panel variant, active tab). Fix at the mount structure, not by lifting each dialog's state.

Unestablished: whether a `createPortal` into a variant-specific container keeps children mounted when the container changes (React compares the container; a change likely remounts). WP-1 measures it before choosing; the preferred design is one stable JSX position with layout-only differences.

## Completeness matrix

| Area | #2882 | #2887 |
|---|---|---|
| Frontend code | panel rendered at one stable tree position; variant changes only layout/styling (check: vitest remount test) | manual tab activation (arrows move focus, Enter/Space activate) and/or keep visited panels mounted; zones chunk loaded only on deliberate activation (check: vitest) |
| Tests (vitest) | dialog open + typed input survive docked↔sheet (and md/lg) change | arrowing past "Zonen" requests no zones and keeps an uncommitted `PropNumberField` value; AC-5 tabs test stays green |
| E2E | page objects / TC-053-101/102/104 must keep passing: testids unchanged (G-W10 a); no new E2E (check: `py_compile`, testids grep) | same |
| Spec REQ-053 | n/a unless behaviour of GP-UX-068/069 wording changes — record in status row §17.3 that #2882/#2887 are fixed (check: diff) | GP-UX-068 / AC-5: state manual activation if chosen (check: diff) |
| Docs DE/EN | n/a — no user-visible behaviour change except not losing input | keyboard description of panel tabs if the user guide states activation on focus (check: grep `docs/*/user-guide/garden-plan.md`) |
| i18n | n/a — no new text | n/a — no new text |
| a11y | focus stays in the dialog across the shape change (check: vitest) | WAI-ARIA tabs pattern, manual activation variant (check: vitest roles/keys) |

## Risks

- `GardenPlanEditor.tsx` also changed by lane #2892 (committed locally, b5e7a5cac) → that lane rebases after this bundle.
- Keeping panels mounted could double data fetches; zones must still load lazily.

## Out of scope

#2886 (focus on disabled buttons), #2904, #2905 (decimal separator in `PropNumberField` display).

## Mode

Mode A (single strand): both members are needed for the one-sentence change; neither is removable independently with uncertain acceptance.

## Member results

(filled during implement)
