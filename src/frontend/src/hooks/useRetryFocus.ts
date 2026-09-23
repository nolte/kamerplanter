import { useCallback, useEffect, useMemo, useRef } from 'react';
import type { CatalogueStatus } from '@/hooks/useCatalogue';

/**
 * Keeps focus somewhere useful across a catalogue retry (#1568 UI review, B2).
 *
 * **The defect.** The three states render as mutually exclusive branches. Press
 * the retry control and the status flips to `loading` in the same tick, so the
 * whole `failed` branch — including the button that still has focus — unmounts.
 * With no explicit focus management the browser falls back to `<body>`: the user
 * loses their position in the dialog and has to tab in from the start. Both
 * surfaces had it.
 *
 * **Why it compounds.** Of the three transitions exactly one announces itself
 * for free: `→ failed`, because MUI's `Alert` inside `ErrorDisplay` carries a
 * native `role="alert"`. `→ loading` and `→ ready` are silent, so after a
 * *successful* retry an assistive-technology user got no feedback at all beyond
 * focus silently vanishing. The live region added alongside this (`LoadingStatus`)
 * covers the announcement; this hook covers the position.
 *
 * **Why a hook and not two inline effects.** The behaviour is identical on both
 * surfaces and only the success target differs. Two copies of it is the shape
 * this whole pull request exists to remove — a picker rebuilding shared logic
 * locally, then drifting from its sibling.
 *
 * **Focus is only moved when the user asked for it, and only while they are
 * still there.** `beginRetry` arms the effect; nothing happens on a first load
 * or on a re-render. Stealing focus because a catalogue merely finished loading
 * would be its own defect.
 *
 * The second half of that sentence is load-bearing and was missing. Both dialogs
 * survive close-and-reopen as the **same component instance** —
 * `SpeciesCreateDialog` is rendered unconditionally by `SpeciesListPage` and the
 * activity dialog lives in a page that never unmounts; `open` only drives MUI.
 * So the refs outlive the dialog. A user who pressed retry and closed the dialog
 * before the request settled left `pending` armed with no further
 * `status !== 'loading'` transition to disarm it — and the *next* opening, even a
 * plain cached one, jumped the focus while they were typing somewhere else.
 * `enabled` going false is therefore what abandons a retry, not the status.
 */

/** What {@link useRetryFocus} returns. */
export interface RetryFocus {
  /**
   * Attach to an element containing **both** the success target and the
   * `ErrorDisplay`. Focus targets are resolved inside it at settle time rather
   * than held as refs, because the failure branch unmounts and remounts — a ref
   * captured when the button first rendered is stale by the time it is needed.
   *
   * A **callback** rather than a `RefObject`, and named for what it is: handing
   * a `RefObject` out means the consumer reads `focus.regionRef` during render,
   * which `react-hooks/refs` flags — correctly, since the rule cannot tell a
   * read-for-attachment from a read of `.current`. A stable callback is the same
   * wiring with none of that ambiguity.
   *
   * Destructure it at the call site (`const { attachRegion } = useRetryFocus(…)`)
   * rather than reaching through the returned object in JSX: `react-hooks/refs`
   * flags the member access itself, whatever the property holds.
   */
  attachRegion: (node: HTMLElement | null) => void;
  /** Call from the retry handler, before (or with) the reload. */
  beginRetry: () => void;
}

/** Options for {@link useRetryFocus}. */
export interface UseRetryFocusOptions {
  /**
   * Whether the surface is on screen — pass the dialog's `open` flag. Going
   * `false` abandons any retry in flight: the user walked away from it, and
   * focusing into a closed dialog on the next opening is a defect, not a
   * courtesy.
   */
  enabled?: boolean;
  /**
   * CSS selector, resolved within the region, for the retry control to focus
   * when the retry lands back on `failed` (the request failed again).
   *
   * Defaults to `ErrorDisplay`'s own documented hook
   * (`[data-testid="error-retry-button"]`), which is what both original call
   * sites (`WorkflowDetailPage`, `SpeciesCreateDialog`) render. A consumer
   * whose failure branch is a different component — `CatalogueLoadError`
   * (#1628) — passes its own retry button's selector here instead.
   */
  failureSelector?: string;
}

/**
 * Restores focus after a user-initiated catalogue retry settles.
 *
 * @param status The reader's current status.
 * @param successSelector CSS selector, resolved within the region, for the
 *   element to focus once the retry succeeds — normally the control the user was
 *   trying to use. Callers pass a selector that the target component's own
 *   documentation declares stable (`FormSelectField`/`SpeciesAutocompleteField`
 *   name their `data-testid`-scoped trigger; the activity dialog uses its
 *   search testid).
 * @param options See {@link UseRetryFocusOptions}.
 * @returns See {@link RetryFocus}; the object is `useMemo`-stabilised
 *   (FRONTEND.md §6.1).
 */
export function useRetryFocus(
  status: CatalogueStatus,
  successSelector: string,
  options?: UseRetryFocusOptions,
): RetryFocus {
  const enabled = options?.enabled ?? true;
  const failureSelector = options?.failureSelector ?? '[data-testid="error-retry-button"]';
  const pending = useRef(false);
  const region = useRef<HTMLElement | null>(null);

  const attachRegion = useCallback((node: HTMLElement | null) => {
    region.current = node;
  }, []);

  const beginRetry = useCallback(() => {
    pending.current = true;
  }, []);

  // Abandoning a retry is its own event, and it is *not* a status transition —
  // a closed dialog's reader freezes wherever it was, so waiting for the next
  // settle means waiting forever.
  useEffect(() => {
    if (enabled) return;
    pending.current = false;
  }, [enabled]);

  useEffect(() => {
    // `loading` is the middle of the transition, not the end of it: acting here
    // would focus the spinner and then lose it again when the branch swaps.
    if (!enabled || !pending.current || status === 'loading') return;
    pending.current = false;
    const container = region.current;
    if (!container) return;
    const target =
      status === 'failed'
        ? // The failure branch re-renders a *new* button for the second
          // failure, so this is resolved now rather than remembered.
          container.querySelector<HTMLElement>(failureSelector)
        : container.querySelector<HTMLElement>(successSelector);
    target?.focus();
  }, [status, successSelector, failureSelector, enabled]);

  return useMemo(() => ({ attachRegion, beginRetry }), [attachRegion, beginRetry]);
}
