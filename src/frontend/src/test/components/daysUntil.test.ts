import { describe, it, expect, afterEach, vi } from 'vitest';
import { daysUntil } from '@/components/dashboard/SeasonOverviewPanel';

/**
 * F3 regression — the frost countdown must compute calendar days on a single,
 * consistent (local) calendar basis. The previous implementation parsed the
 * `YYYY-MM-DD` string via `new Date(iso)` (UTC midnight) and then read local
 * calendar fields off `today`, so in negative UTC offsets (America/*) the target
 * landed a day early and the countdown / `frost.now` fired one day too soon.
 *
 * These assertions pin the intended contract in every timezone: a date string
 * built from the *local* calendar of a fixed "today" must yield the exact day
 * delta, never off-by-one.
 */

/** Local `YYYY-MM-DD` for a Date, mirroring the calendar dates the panel gets. */
function localIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

describe('daysUntil (F3 timezone-safe frost countdown)', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns 0 for today (no off-by-one at midnight boundaries)', () => {
    vi.useFakeTimers();
    // A local wall-clock late in the evening — this is exactly when the old
    // UTC-parse produced the off-by-one in western hemispheres.
    vi.setSystemTime(new Date(2026, 9, 24, 22, 30, 0)); // 24 Oct 2026, 22:30 local
    expect(daysUntil(localIso(new Date(2026, 9, 24)))).toBe(0);
  });

  it('counts a future frost date exactly, on the local calendar', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 20, 23, 15, 0)); // 20 Oct 2026, 23:15 local
    expect(daysUntil('2026-10-24')).toBe(4);
  });

  it('returns a negative count for a past date', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 24, 1, 0, 0));
    expect(daysUntil('2026-10-22')).toBe(-2);
  });

  it('tolerates a full ISO datetime and rejects garbage', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 20, 12, 0, 0));
    expect(daysUntil('2026-10-24T00:00:00Z')).toBe(4);
    expect(daysUntil('not-a-date')).toBeNull();
  });
});
