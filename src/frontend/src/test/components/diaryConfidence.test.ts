import { describe, it, expect } from 'vitest';
import {
  confidenceBand,
  confidencePercent,
  confidenceSeverity,
} from '@/components/diary/confidence';

/**
 * REQ-050 AK-30 — the wording half of a confidence display.
 *
 * The bands are checked at their boundaries because that is where a silent
 * off-by-one turns "sehr unsicher" into "sehr wahrscheinlich" on a value the
 * user is meant to weigh a plant decision against.
 */
describe('confidenceBand (REQ-050 AK-30)', () => {
  it.each([
    [0, 'veryLow'],
    [0.19, 'veryLow'],
    [0.2, 'low'],
    [0.39, 'low'],
    [0.4, 'moderate'],
    [0.59, 'moderate'],
    [0.6, 'high'],
    [0.79, 'high'],
    [0.8, 'veryHigh'],
    [1, 'veryHigh'],
  ])('maps %s to "%s"', (value, expected) => {
    expect(confidenceBand(value)).toBe(expected);
  });

  it('clamps values the backend should never have let through', () => {
    // The API validates 0.0–1.0 (§4.5). A display component is the wrong place
    // to throw over a value that got past that check anyway.
    expect(confidenceBand(-1)).toBe('veryLow');
    expect(confidenceBand(5)).toBe('veryHigh');
    expect(confidenceBand(Number.NaN)).toBe('veryLow');
  });

  it('never colours a low confidence as a success', () => {
    expect(confidenceSeverity('veryLow')).toBe('warning');
    expect(confidenceSeverity('low')).toBe('warning');
    expect(confidenceSeverity('moderate')).toBe('info');
    expect(confidenceSeverity('high')).toBe('success');
    expect(confidenceSeverity('veryHigh')).toBe('success');
  });
});

describe('confidencePercent', () => {
  it('rounds to whole percentage points', () => {
    // "71.5 %" would claim half a point of resolution from an estimate.
    expect(confidencePercent(0.715)).toBe(72);
    expect(confidencePercent(0.0)).toBe(0);
    expect(confidencePercent(1)).toBe(100);
  });

  it('clamps out-of-range input rather than reporting 500 %', () => {
    expect(confidencePercent(5)).toBe(100);
    expect(confidencePercent(-2)).toBe(0);
  });
});
