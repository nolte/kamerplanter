/**
 * The negative control the shared helper needs to be worth having (#1094).
 *
 * An a11y assertion that never fails is the failure class NFR-018 §1 catalogues,
 * and it is the *easy* one to ship here: axe on a well-formed component returns
 * an empty violation list, so a helper that filtered everything away — wrong
 * impact comparison, a filter inverted, results read from the wrong field —
 * would be green on every page it was added to and would certify nothing.
 *
 * So this file seeds real violations and requires the helper to catch them, and
 * requires it *not* to catch the noise that would get it switched off.
 */

import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { expectNoA11yViolations } from './expectNoA11yViolations';

/** An input with no accessible name — axe reports this as `critical`. */
function CriticalViolation() {
  return (
    <div>
      <input type="text" />
    </div>
  );
}

/** Well-formed: label bound to input, so nothing critical is reported. */
function Clean() {
  return (
    <div>
      <label htmlFor="name">Name</label>
      <input id="name" type="text" />
    </div>
  );
}

describe('expectNoA11yViolations', () => {
  it('passes on markup with no critical violations', async () => {
    const { container } = render(<Clean />);

    await expectNoA11yViolations(container);
  });

  it('fails on a seeded critical violation', async () => {
    const { container } = render(<CriticalViolation />);

    await expect(expectNoA11yViolations(container)).rejects.toThrow();
  });

  it('names the rule and the offending markup in the failure', async () => {
    // The whole reason for the custom message. `toEqual([])` on axe's raw
    // violation objects prints a wall of internals; someone reading CI output
    // needs the rule id and the element.
    const { container } = render(<CriticalViolation />);

    await expect(expectNoA11yViolations(container)).rejects.toThrow(/label|<input/i);
  });

  it('ignores a violation below the configured floor', async () => {
    // The other half of the calibration, and the one that keeps the helper
    // switched on. Rendering a fragment outside its layout makes axe report
    // landmark and contrast findings that are artefacts of the test, not of the
    // component. A helper that failed on those would be removed rather than
    // fixed. `Clean` has no critical finding but is not landmark-complete.
    const { container } = render(<Clean />);

    await expectNoA11yViolations(container, { minImpact: 'critical' });
  });

  it('can be tightened per call', async () => {
    // `minImpact` is what lets a surface that has earned the stricter bar ask
    // for it, instead of the default becoming a ceiling nobody can raise.
    const { container } = render(<CriticalViolation />);

    await expect(
      expectNoA11yViolations(container, { minImpact: 'moderate' }),
    ).rejects.toThrow();
  });
});
