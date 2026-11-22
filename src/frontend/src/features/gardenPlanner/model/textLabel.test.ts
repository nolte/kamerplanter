/** The caption rules of the client (REQ-053 GP-UX-071, #2913) - the same as the server's `garden_object.py`. */
import { describe, expect, it } from 'vitest';
import {
  newTextHeightM,
  refitTextLabel,
  TEXT_LABEL_MAX_CHARS,
  textBoxWidthM,
  textLabelFontM,
  textLabelGeometry,
  textLabelProblem,
} from './textLabel';

describe('textLabelProblem', () => {
  it('accepts one trimmed line up to the limit, markup included (escaping is the export\'s job)', () => {
    expect(textLabelProblem('  Kräuterecke ')).toBeNull();
    expect(textLabelProblem('<b>Beet & Co</b>')).toBeNull();
    expect(textLabelProblem('a'.repeat(TEXT_LABEL_MAX_CHARS))).toBeNull();
    // Code points, as the server counts: 80 emoji are 80 characters, not 160.
    expect(textLabelProblem('🌱'.repeat(TEXT_LABEL_MAX_CHARS))).toBeNull();
  });

  it.each([
    ['', 'empty'],
    ['   ', 'empty'],
    ['a'.repeat(TEXT_LABEL_MAX_CHARS + 1), 'too_long'],
    ['Zeile 1\nZeile 2', 'control'],
    ['tab\tinside', 'control'],
    ['bell\u0007', 'control'],
    ['line\u2028sep', 'control'],
    ['rtl \u202eoverride', 'control'],
    ['isolate \u2066x\u2069', 'control'],
  ] as const)('refuses %j as %s', (text, problem) => {
    expect(textLabelProblem(text)).toBe(problem);
  });
});

describe('the caption box', () => {
  it('sizes a new caption to read 20 px high where it is set, within 5 cm and 2 m', () => {
    expect(newTextHeightM(40)).toBe(0.5);
    expect(newTextHeightM(2000)).toBe(0.05);
    expect(newTextHeightM(1)).toBe(2);
  });

  it('makes the box as wide as its text at the full font size, never narrower than high', () => {
    // 10 characters × 0.8 × 0.5 m × 0.6 = 2.4 m.
    expect(textBoxWidthM('abcdefghij', 0.5)).toBe(2.4);
    expect(textBoxWidthM('a', 0.5)).toBe(0.5);
    expect(textLabelGeometry([3, 4], 'abcdefghij', 0.5)).toEqual({
      kind: 'rect',
      origin: [3, 4],
      width_m: 2.4,
      length_m: 0.5,
      rotation_deg: 0,
    });
  });

  it('fills the height unless the text would run past the width (the PDF\'s rule)', () => {
    expect(textLabelFontM(10, 0.5, 'abc')).toBeCloseTo(0.4);
    expect(textLabelFontM(1.2, 0.5, 'abcdefghij')).toBeCloseTo(0.2);
  });

  it('refits the width to a new text and keeps anchor, height and turn', () => {
    const box = { kind: 'rect' as const, origin: [1, 2] as [number, number], width_m: 1, length_m: 0.5, rotation_deg: 30 };
    expect(refitTextLabel(box, 'abcdefghij')).toEqual({ ...box, width_m: 2.4 });
    const same = { ...box, width_m: 2.4 };
    expect(refitTextLabel(same, 'abcdefghij')).toBe(same);
    expect(refitTextLabel({ kind: 'circle', origin: [1, 1], radius_m: 1 }, 'x')).toBeNull();
  });
});
