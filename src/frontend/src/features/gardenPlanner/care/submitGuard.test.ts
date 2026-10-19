import { describe, expect, it } from 'vitest';
import { isDuplicateTap, SUBMIT_DEBOUNCE_MS } from './submitGuard';

describe('isDuplicateTap (GP-FR-149)', () => {
  it('lets the first tap through and swallows a second one inside 300 ms', () => {
    expect(SUBMIT_DEBOUNCE_MS).toBe(300);
    expect(isDuplicateTap(0, 10_000, false)).toBe(false);
    expect(isDuplicateTap(10_000, 10_299, false)).toBe(true);
    expect(isDuplicateTap(10_000, 10_300, false)).toBe(false);
  });

  it('swallows every tap while the request is running, however late', () => {
    expect(isDuplicateTap(0, 60_000, true)).toBe(true);
  });
});
