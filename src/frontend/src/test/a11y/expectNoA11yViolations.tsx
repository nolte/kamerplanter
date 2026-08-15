/**
 * Shared axe assertion for component and page tests (#1094).
 *
 * `vitest-axe` was installed and prescribed by FRONTEND.md §13.5 ("keine
 * kritischen Violations") and used by exactly **one** test file, against a
 * frontend of 361+ test files and dozens of pages. A11y coverage was by memory,
 * not by default. Every test that wanted it had to re-derive the same three
 * things: which impact level fails, how long axe may take, and how to render.
 *
 * Three decisions are baked in here so they stop being per-file guesses:
 *
 * 1. **`critical` fails the test, by default.** Not "no violations at all":
 *    jsdom reports colour-contrast and landmark findings on isolated components
 *    that are artefacts of rendering a fragment outside its layout, and a helper
 *    that failed on those would be turned off within a week. `minImpact` widens
 *    it per call for a surface that has earned the stricter bar.
 * 2. **A generous timeout.** `axe()` is a heavy DOM scan; under full-suite plus
 *    coverage load it exceeds `waitFor`'s 1s default (which is independent of
 *    vitest's `testTimeout`) and fails runs for load rather than for
 *    correctness. Measured on this suite before the shared helper existed.
 * 3. **The violation is reported, not just counted.** `toEqual([])` on the raw
 *    array prints an unreadable wall of axe internals; a caller reading CI
 *    output needs the rule id, the impact and the offending markup.
 */

import { waitFor } from '@testing-library/react';
import { expect } from 'vitest';
import { axe } from 'vitest-axe';

/** Impact levels axe reports, ordered least to most severe. */
const IMPACT_ORDER = ['minor', 'moderate', 'serious', 'critical'] as const;

export type A11yImpact = (typeof IMPACT_ORDER)[number];

/**
 * axe is a full DOM traversal per call. 15s is not a correctness bound — it is
 * headroom so a loaded CI runner cannot decide the verdict.
 */
const AXE_TIMEOUT_MS = 15_000;

/**
 * The default floor is 1: an empty container means axe scanned nothing, and an
 * empty violation list from an empty scan certifies nothing.
 *
 * It stays at 1 because this helper cannot know how large its subject should be
 * — it serves single-component tests as well as whole pages. A caller that
 * *does* know passes `minElements`, and page-level tests should: a page reduced
 * to a router wrapper by a render error or a missing route parameter still
 * produces a handful of nodes and would clear a floor of 1.
 */
const DEFAULT_MIN_ELEMENTS = 1;

interface A11yViolation {
  id: string;
  impact?: string | null;
  help: string;
  nodes: { html: string }[];
}

function atLeast(impact: string | null | undefined, floor: A11yImpact): boolean {
  const index = IMPACT_ORDER.indexOf((impact ?? 'minor') as A11yImpact);
  return index >= IMPACT_ORDER.indexOf(floor);
}

function describeViolations(violations: A11yViolation[]): string {
  return violations
    .map(
      (v) =>
        `  [${v.impact ?? 'unknown'}] ${v.id}: ${v.help}\n` +
        v.nodes.map((n) => `      ${n.html}`).join('\n'),
    )
    .join('\n');
}

/**
 * Assert `container` has no accessibility violations at or above `minImpact`.
 *
 * @param container - the rendered root, e.g. `renderWithProviders(<Page />).container`
 * @param minImpact - lowest impact level that fails the test; defaults to `critical`
 */
export async function expectNoA11yViolations(
  container: HTMLElement,
  {
    minImpact = 'critical' as A11yImpact,
    minElements = DEFAULT_MIN_ELEMENTS,
  }: { minImpact?: A11yImpact; minElements?: number } = {},
): Promise<void> {
  await waitFor(
    async () => {
      // Inside the wait, and before the scan. A container with (almost) nothing
      // in it means axe scanned nothing, and an empty violation list from an
      // empty scan is a green test that certifies nothing — the NFR-018 §1
      // shape. Measured on this suite: two of the four pages backfilled in
      // #1094 sat at 15 elements — a loading skeleton — and passed axe cleanly
      // before this check existed.
      //
      // It retries rather than asserting once because the DOM genuinely changes
      // here: a page mounts with a spinner and fills in when its request
      // resolves. That is a real wait for a real transition, not a retry loop
      // hoping the same moment comes out differently.
      const elementCount = container.querySelectorAll('*').length;
      expect(
        elementCount,
        `axe was handed a container with ${elementCount} element(s), fewer than ` +
          `the ${minElements} this call requires. Too little was scanned for an ` +
          'empty violation list to mean anything. Either the subject never ' +
          'finished loading, or it failed to render — a render error and a ' +
          'missing route parameter both leave a near-empty container that ' +
          'passes every axe rule.',
      ).toBeGreaterThanOrEqual(minElements);

      const results = await axe(container);
      const failing = (results.violations as unknown as A11yViolation[]).filter((v) =>
        atLeast(v.impact, minImpact),
      );
      expect(
        failing,
        failing.length
          ? `${failing.length} accessibility violation(s) at impact >= ${minImpact}:\n${describeViolations(failing)}`
          : '',
      ).toEqual([]);
    },
    { timeout: AXE_TIMEOUT_MS },
  );
}
