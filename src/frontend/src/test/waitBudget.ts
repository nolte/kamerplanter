/**
 * The one wait budget the catalogue-reach page tests share (#1531).
 *
 * **What it is for.** Those tests drive a composed page — mount, MSW round
 * trip, a 300 ms debounce, a re-render — and assert inside `waitFor`. Every
 * such wait carries a budget, and in this suite that budget is **5 s** whether
 * a case states one or not: `src/test/setup.ts` raises React Testing Library's
 * 1 s default to `asyncUtilTimeout: 5000` for the whole run. Measured rather
 * than read off the source — a bare failing `waitFor` here rejects after
 * 5066 ms — because the difference matters: the waits that carried no explicit
 * timeout were not the tight ones people assume, they were exactly as tight as
 * the explicit `{ timeout: 5000 }` next to them.
 *
 * Under full-suite contention the steps dilate by roughly an order of
 * magnitude, so that sub-budget expires long before the case budget does, and
 * the case fails with "could not find X" — the very message the file exists to
 * report when the catalogue really is short. That is the worst possible way for
 * a regression test to flake, and it is what #1531 measured.
 *
 * This budget therefore raises the suite-wide 5 s for these specific steps,
 * whose cost was measured, rather than moving `asyncUtilTimeout` for 416 files
 * whose costs were not.
 *
 * **Why 12 000 ms.** Measured, not guessed. The steps cost ~0.4 s (mount to
 * first row) and ~1 s (paste to searched row) idle; the worst observed failure
 * under 16 busy loops on 8 cores was 9953 ms. 12 s is about 20 % over that
 * worst observation — enough headroom to stop deciding runs, and deliberately
 * not more, because every millisecond here is time a genuinely broken
 * catalogue spends before it reports.
 *
 * **The constraint that makes it correct.** A case runs at most two of these
 * waits in sequence, so `2 × WAIT_BUDGET` must stay under the per-case
 * `testTimeout`. Otherwise the case timeout fires first and the run reports
 * "test timed out" instead of naming the row it could not find — the file would
 * still be red, but it would have lost the diagnosis it exists to give.
 * {@link TEST_TIMEOUT} is read from `vitest.config.ts` rather than copied next
 * to it, and `waitBudget.test.ts` asserts the inequality, so lowering the
 * project's timeout turns that self-test red rather than silently degrading
 * every catalogue case into a timeout.
 */

// Vite `?raw` imports the config source as a string, the way the other
// source-level guards in this suite read their subjects (no `node:fs`).
import vitestConfigSource from '../../vitest.config.ts?raw';

/**
 * The per-case timeout actually in force, parsed out of `vitest.config.ts`.
 *
 * Parsed rather than restated: a second literal would agree with the config
 * only until somebody changes one of them, and the whole point of the check
 * below is to notice exactly that change.
 */
export const TEST_TIMEOUT = readTestTimeout();

/** Budget for a single asynchronous step in a catalogue-reach page test. */
export const WAIT_BUDGET = 12000;

function readTestTimeout(): number {
  const match = /^\s*testTimeout:\s*(\d+)\s*,/m.exec(vitestConfigSource);
  if (!match) {
    throw new Error(
      'vitest.config.ts no longer declares a numeric `testTimeout`. The wait '
        + 'budgets in src/test/waitBudget.ts are checked against it, so they '
        + 'now have nothing to be checked against — update the parser here '
        + 'rather than dropping the check.',
    );
  }
  return Number(match[1]);
}
