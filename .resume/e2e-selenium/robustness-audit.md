# E2E Page-Model Robustness Audit

_Requested mid-run: identify brittle selectors in the page objects and check the
implementation for **missing dedicated `data-testid`s** on logical elements, so the
page model stops breaking on small UI changes. Scope: R6 (non-behavioral
testability affordances)._

## Why this matters (evidence from this very run)

Of the 19 drift failures fixed this session, the majority were **brittle-selector
breakage**, not real bugs:

- **Cluster A (7):** `.MuiSelect-select` stopped matching when a `<Select>` became an
  `<Autocomplete>`.
- **D1:** `cells[0]` read the wrong column after a cover-photo column was inserted.
- **E:** `input:not([type='number'])[0]` grabbed a newly-inserted Select's native input.
- **req003 history:** `[data-testid='phase-history'] tbody tr` broke when the table
  moved to the shared `DataTable`.

These are exactly the "breaks on every small UI change" failures the audit targets.

## Brittleness inventory (61 page objects)

| Pattern | Count | Risk | Breaks on |
|---|---|---|---|
| `.MuiSelect-select` (open a Select) | **65** | High | MUI upgrade, `<Select>`→`<Autocomplete>` refactor |
| MUI-internal classes overall (`.Mui*`) | **48 / 61 files** | High | MUI version bump, restyle |
| Position-based `cells[N]` / `inputs[N]` / `[0]` | **65** | High | column insert/reorder, added field |
| `li[role='option'] contains(text(), <label>)` | 10 files | Medium | i18n / label wording change |
| Result `.MuiAlert-root` / `.MuiSnackbar-root` | ~20 | Medium | MUI restyle, notistack upgrade |
| `.MuiChip-root` / `.MuiListItemText-primary` etc. | ~40 | Low–Med | restyle |

Stable hooks already present and preferred: `data-testid` (page markers, form
fields, rows), `data-value` on MenuItems (i18n-independent), `role='option'` /
`role='dialog'` / `role='combobox'` (ARIA, stable).

## Dedicated IDs that were MISSING → added this session (R6, additive, non-behavioral)

1. **Select options** — `src/frontend/src/components/form/FormSelectField.tsx`
   Added `data-testid=form-option-{name}-{value}` on each `MenuItem` (options were
   already addressable by their stable `data-value`; the testid makes the value
   binding explicit). The clickable trigger is addressed in tests via the stable
   ARIA `[data-testid='form-field-{name}'] [role='combobox']` (no dedicated testid
   needed — the combobox role is MUI-version-stable), replacing the 65×
   `.MuiSelect-select` open-click and the text-`contains` option match across
   **~40 form Selects**. (An earlier `SelectDisplayProps` trigger-testid was
   dropped — it clashed with MUI 7's TextField prop types at build time.)

2. **Table cells** — `src/frontend/src/components/common/DataTable.tsx`
   Added `data-testid=cell-{col.id}` on every `TableCell`. Replaces position-based
   `cells[N]` reads (which broke on the cover-column insert) with column-id
   addressing across **every DataTable-backed list**.

Both are additive: existing selectors still work, so page objects migrate
incrementally without a flag day.

## Robust page-object primitives added (`tests/e2e/pages/base_page.py`)

- `open_select(field_name)` — clicks the dedicated trigger testid, falling back to
  `[role='combobox']` then legacy `.MuiSelect-select`.
- `select_option_by_value(value, field_name=None)` — clicks by `data-value` /
  the per-field option testid (i18n-independent); scroll+JS-click; safe close.
- `choose_select_value(field_name, value)` — open + select in one call.
- `get_row_cell_text(row, col_id)` — column-id cell read instead of `cells[N]`.

**Exemplar migration:** `task_queue_page._select_form_option` now delegates to
`choose_select_value(...)` — the whole brittle trigger-class + i18n-text +
manual-intercept + stray-ESCAPE block collapses to one robust call.

## Recommended follow-up sweep (bounded, mechanical — not done this run)

Migrating all 65 `.MuiSelect-select` sites and 65 `cells[N]` reads touches 48 files
and needs per-file validation, so it is a deliberate follow-up rather than a risky
mid-run flag day. The foundation (dedicated testids + base_page helpers) is in
place, so each is now a mechanical swap:

1. `.MuiSelect-select` open-clicks → `self.open_select(name)` / `choose_select_value`.
2. `contains(text(), label)` option XPaths → `select_option_by_value(value)`.
3. `cells[N]` reads → `get_row_cell_text(row, col_id)` (needs each page's `col.id`).
4. Consider `data-testid` on calculation result Alerts (`{calc}-result`) and on the
   notistack error surface so result/error detection stops relying on `.MuiAlert-root`.

Priority order: Selects (highest count + highest churn) → table cells → result Alerts.
