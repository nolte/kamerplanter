import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  MS_PER_WEEK,
  computeCurrentWeek,
  computeCurrentDay,
  getShortMonthName,
  MONTH_WEEK_SPANS,
} from '@/utils/weekCalculation';

describe('weekCalculation', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-29T12:00:00Z')); // 28 days after Jan 1
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  describe('computeCurrentWeek', () => {
    it('returns week 1 on the epoch day', () => {
      expect(computeCurrentWeek('2026-01-29')).toBe(1);
    });

    it('counts full weeks since the epoch (1-based)', () => {
      // 28 days after epoch = 4 completed weeks -> week 5
      expect(computeCurrentWeek('2026-01-01')).toBe(5);
    });

    it('returns undefined for a future epoch', () => {
      expect(computeCurrentWeek('2026-06-01')).toBeUndefined();
    });

    it('returns undefined for an unparseable epoch', () => {
      expect(computeCurrentWeek('not-a-date')).toBeUndefined();
    });
  });

  describe('computeCurrentDay', () => {
    it('returns day 1 on the epoch day', () => {
      expect(computeCurrentDay('2026-01-29')).toBe(1);
    });

    it('counts days since the epoch (1-based)', () => {
      expect(computeCurrentDay('2026-01-01')).toBe(29);
    });

    it('returns undefined for a future epoch', () => {
      expect(computeCurrentDay('2026-02-15')).toBeUndefined();
    });

    it('returns undefined for an unparseable epoch', () => {
      expect(computeCurrentDay('garbage')).toBeUndefined();
    });
  });

  describe('getShortMonthName', () => {
    it('formats a 0-based month index in the given locale', () => {
      expect(getShortMonthName(0, 'en-US')).toMatch(/jan/i);
      expect(getShortMonthName(11, 'en-US')).toMatch(/dec/i);
    });
  });

  it('MONTH_WEEK_SPANS covers all 12 months and sums to 52 weeks', () => {
    expect(MONTH_WEEK_SPANS).toHaveLength(12);
    expect(MONTH_WEEK_SPANS.reduce((sum, m) => sum + m.span, 0)).toBe(52);
    expect(MONTH_WEEK_SPANS[11].weekEnd).toBe(52);
  });

  it('MS_PER_WEEK is seven days in milliseconds', () => {
    expect(MS_PER_WEEK).toBe(7 * 24 * 60 * 60 * 1000);
  });
});
