import { describe, it, expect } from 'vitest';

// TEMPORARY — proves the newly required `lint-test-build (22)` check actually
// blocks a merge (#828 AC 5). Deleted immediately after the demonstration.
describe('required-gate probe', () => {
  it('fails on purpose', () => {
    expect(1).toBe(2);
  });
});
