import { describe, expect, it } from 'vitest';
import { phaseColor } from './phaseColors';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the phase colours runs against the same vector file as the Python reference
 * (`tests/unit/domain/engines/test_phase_colors.py`, #2489): the plan on screen and the PDF legend paint a phase alike.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'phase_color');

describe('phase colour vectors', () => {
  it('carries the operation, the named phases, the normalisation and the hash fallback', () => {
    expect(VECTORS.operations).toHaveProperty('phase_color');
    const ids = CASES.map((vector) => vector.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        'phase-color-flowering',
        'phase-color-upper-case',
        'phase-color-whitespace',
        'phase-color-unknown-dormancy',
        'phase-color-unknown-case-sensitive',
        'phase-color-unknown-astral',
      ]),
    );
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as { name: string };
    expect(phaseColor(input.name)).toBe(vector.expected);
  });
});
