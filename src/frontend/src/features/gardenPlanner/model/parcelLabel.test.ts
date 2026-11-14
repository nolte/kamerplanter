import { describe, expect, it } from 'vitest';
import { PARCEL_LABEL_MAX_CHARS, parcelLabelProblem, parcelLabelValue } from './parcelLabel';

describe('parcel label (GP-FR-176, #2759)', () => {
  it('takes a short single line and strips the space around it', () => {
    expect(parcelLabelProblem('  A-17 ')).toBeNull();
    expect(parcelLabelValue('  A-17 ')).toBe('A-17');
  });

  it('reads a blank text as "no label" (clears it)', () => {
    expect(parcelLabelProblem('   ')).toBeNull();
    expect(parcelLabelValue('   ')).toBeNull();
  });

  it('counts characters as the server does and refuses one past the limit', () => {
    expect(parcelLabelProblem('🌱'.repeat(PARCEL_LABEL_MAX_CHARS))).toBeNull();
    expect(parcelLabelProblem('x'.repeat(PARCEL_LABEL_MAX_CHARS + 1))).toBe('too_long');
  });

  it.each(['A\n17', 'A\t17', 'A‮71', 'A B'])(
    'refuses a break, a control or a bidi character',
    (text) => {
      expect(parcelLabelProblem(text)).toBe('control');
    },
  );
});
