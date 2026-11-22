import { describe, expect, it } from 'vitest';
import { daysSince, wateredByBed, wateredClassOf } from './lastWatered';

const NOW = Date.parse('2026-10-20T10:00:00Z');

describe('wateredClassOf (#2466: 0-1 / 2-3 / 4-7 / >7 days)', () => {
  it.each([
    [0, 'd0_1'],
    [1, 'd0_1'],
    [2, 'd2_3'],
    [3, 'd2_3'],
    [4, 'd4_7'],
    [7, 'd4_7'],
    [8, 'd8plus'],
    [400, 'd8plus'],
  ] as const)('%i days is %s', (days, expected) => {
    expect(wateredClassOf(days)).toBe(expected);
  });
});

describe('daysSince', () => {
  it('counts UTC calendar days, not 24-hour spans', () => {
    expect(daysSince('2026-10-19T23:59:00Z', NOW)).toBe(1);
    expect(daysSince('2026-10-20T00:01:00Z', NOW)).toBe(0);
    expect(daysSince('2026-10-13T12:00:00Z', NOW)).toBe(7);
  });

  it('never goes negative and reads a bad instant as unknown', () => {
    expect(daysSince('2026-10-25T00:00:00Z', NOW)).toBe(0);
    expect(daysSince('not a date', NOW)).toBeNull();
  });
});

describe('wateredByBed', () => {
  it('leaves beds without a watering out, so they get no hatching', () => {
    const result = wateredByBed(
      { a: '2026-10-19T08:00:00Z', b: null, c: undefined, d: '2026-09-01T00:00:00Z', e: 'x' },
      NOW,
    );
    expect(Object.keys(result).sort()).toEqual(['a', 'd']);
    expect(result.a).toEqual({ days: 1, wateredClass: 'd0_1' });
    expect(result.d.wateredClass).toBe('d8plus');
  });
});
