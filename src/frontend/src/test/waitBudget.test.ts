import { describe, it, expect } from 'vitest';
import { TEST_TIMEOUT, WAIT_BUDGET } from './waitBudget';

/**
 * Self-test for the shared wait budget (#1531).
 *
 * The property the catalogue-reach tests rely on is not "12 000 is a nice
 * number", it is `2 × WAIT_BUDGET < testTimeout` — a relation between a value in
 * this suite and a value in `vitest.config.ts`, two files that otherwise know
 * nothing about each other. Break it and no catalogue case fails in a way that
 * points here: they all keep passing, and the *next* genuine catalogue defect
 * reports "test timed out" instead of the row it could not find.
 *
 * Counter-check for whoever touches either number: lower `testTimeout` in
 * `vitest.config.ts` to 20000 and this file must go red. If it does not, the
 * parser in `waitBudget.ts` has stopped reading the value that is in force and
 * the check is inert.
 */
describe('shared wait budget (#1531)', () => {
  it('reads the per-case timeout that is actually configured', () => {
    // A failed parse throws at import; this pins that the parsed value is a
    // usable duration rather than, say, a `0` matched out of a comment.
    expect(Number.isInteger(TEST_TIMEOUT)).toBe(true);
    expect(TEST_TIMEOUT).toBeGreaterThan(0);
  });

  it('leaves room for two sequential waits inside one case', () => {
    expect(2 * WAIT_BUDGET).toBeLessThan(TEST_TIMEOUT);
  });
});
