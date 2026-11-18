import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { toLocalIsoDate, toUtcIsoDate, utcCalendarDaysBetween, utcDayOf } from '@/utils/calendarDay';
import { computeCurrentWeek, computeRunElapsedWeek } from '@/utils/weekCalculation';

/**
 * #3016 — the two calendars, pinned in a zone east of UTC.
 *
 * Every assertion runs with the process in Europe/Berlin (UTC+1 in winter, UTC+2 in summer), where the
 * local day runs ahead of the UTC day for the first one or two hours after local midnight. On a UTC runner
 * the two calendars coincide and none of this could fail, so the zone is set for real (`process.env.TZ`
 * is re-read by Node on assignment) and checked before anything else.
 */
const BERLIN = 'Europe/Berlin';

describe('calendarDay (#3016)', () => {
  const zone = process.env.TZ;

  beforeEach(() => {
    process.env.TZ = BERLIN;
    vi.useFakeTimers({ toFake: ['Date'] });
  });

  afterEach(() => {
    vi.useRealTimers();
    if (zone === undefined) delete process.env.TZ;
    else process.env.TZ = zone;
  });

  it('really runs in a zone east of UTC (the premise of every test below)', () => {
    expect(new Date('2026-11-18T00:00:00Z').getTimezoneOffset()).toBe(-60);
    expect(new Date('2026-07-01T00:00:00Z').getTimezoneOffset()).toBe(-120);
  });

  describe('toLocalIsoDate — the default for a date the user enters', () => {
    it('is the local date at 00:30 CET, while UTC is still on the previous day', () => {
      vi.setSystemTime(new Date('2026-11-17T23:30:00Z')); // 2026-11-18 00:30 CET
      expect(toLocalIsoDate()).toBe('2026-11-18');
      expect(toUtcIsoDate()).toBe('2026-11-17');
    });

    it('is the local date at 00:30 CEST (UTC+2)', () => {
      vi.setSystemTime(new Date('2026-07-01T22:30:00Z')); // 2026-07-02 00:30 CEST
      expect(toLocalIsoDate()).toBe('2026-07-02');
    });

    it('is the local date at 23:30 local, the same day as UTC', () => {
      vi.setSystemTime(new Date('2026-11-17T22:30:00Z')); // 2026-11-17 23:30 CET
      expect(toLocalIsoDate()).toBe('2026-11-17');
      expect(toUtcIsoDate()).toBe('2026-11-17');
    });

    it('formats an explicit date with zero padding', () => {
      expect(toLocalIsoDate(new Date(2026, 0, 5, 12))).toBe('2026-01-05');
    });
  });

  describe('utcDayOf — read a stored value the way the backend does', () => {
    it('reads a value without a zone as UTC, not local time', () => {
      expect(utcDayOf('2026-11-17T23:30:00')).toBe('2026-11-17');
    });

    it('reads an offset value on the UTC calendar', () => {
      expect(utcDayOf('2026-11-18T00:30:00+01:00')).toBe('2026-11-17');
    });

    it('keeps a bare date as that day', () => {
      expect(utcDayOf('2026-11-17')).toBe('2026-11-17');
    });

    it('is null for an absent or unreadable value', () => {
      expect(utcDayOf(null)).toBeNull();
      expect(utcDayOf('')).toBeNull();
      expect(utcDayOf('not-a-date')).toBeNull();
    });
  });

  describe('utcCalendarDaysBetween', () => {
    it('counts whole UTC calendar days, not local ones', () => {
      // 00:30 CET on the 17th is 23:30 UTC on the 16th: six UTC days after the 10th, seven local ones.
      expect(utcCalendarDaysBetween('2026-11-10T12:00:00Z', new Date('2026-11-16T23:30:00Z'))).toBe(6);
    });

    it('is negative for a start that lies ahead and undefined for garbage', () => {
      expect(utcCalendarDaysBetween('2026-11-20', new Date('2026-11-18T12:00:00Z'))).toBe(-2);
      expect(utcCalendarDaysBetween('garbage', new Date('2026-11-18T12:00:00Z'))).toBeUndefined();
    });
  });

  /**
   * The server's rule, `api/v1/planting_runs/tenant_router.py::get_active_channels`:
   *
   *     started_date = started_at as a UTC date (naive = UTC)
   *     current_week = max(1, (today_utc() - started_date).days // 7 + 1)   # None -> 1
   *
   * Each vector below is that expression evaluated by hand; the client must give the same week, because
   * the server returns the dosages of exactly this week.
   */
  describe('computeRunElapsedWeek — agrees with the server at the week boundary', () => {
    const SERVER_VECTORS: Array<{ startedAt: string | null; now: string; week: number; why: string }> = [
      // 2026-11-17 00:30 CET = 2026-11-16 23:30 UTC; (16 - 10) // 7 + 1 = 1. Local days would say 7 -> week 2.
      { startedAt: '2026-11-10T12:00:00Z', now: '2026-11-16T23:30:00Z', week: 1, why: '00:30 local, last UTC day of week 1' },
      // 2026-11-16 23:30 CET = 22:30 UTC; still 6 days on both calendars.
      { startedAt: '2026-11-10T12:00:00Z', now: '2026-11-16T22:30:00Z', week: 1, why: '23:30 local, week 1' },
      // 2026-11-17 01:30 CET = 00:30 UTC on the 17th; (17 - 10) // 7 + 1 = 2.
      { startedAt: '2026-11-10T12:00:00Z', now: '2026-11-17T00:30:00Z', week: 2, why: 'first UTC day of week 2' },
      // Started at 00:30 CET on the 10th = 23:30 UTC on the 9th: the server counts from the 9th.
      { startedAt: '2026-11-09T23:30:00Z', now: '2026-11-16T12:00:00Z', week: 2, why: 'start just after local midnight' },
      // A naive timestamp is UTC on the server, not local time.
      { startedAt: '2026-11-09T23:30:00', now: '2026-11-16T12:00:00Z', week: 2, why: 'naive start is UTC' },
      // Not started yet / start in the future: max(1, …).
      { startedAt: null, now: '2026-11-16T12:00:00Z', week: 1, why: 'no started_at' },
      { startedAt: '2026-12-01T00:00:00Z', now: '2026-11-16T12:00:00Z', week: 1, why: 'future start clamps to 1' },
    ];

    for (const vector of SERVER_VECTORS) {
      it(`week ${vector.week}: ${vector.why}`, () => {
        vi.setSystemTime(new Date(vector.now));
        expect(computeRunElapsedWeek(vector.startedAt)).toBe(vector.week);
      });
    }
  });

  describe('computeCurrentWeek — UTC calendar days like the server', () => {
    it('stays in week 1 at 00:30 local after six UTC days', () => {
      vi.setSystemTime(new Date('2026-11-16T23:30:00Z')); // 2026-11-17 00:30 CET
      expect(computeCurrentWeek('2026-11-10T12:00:00Z')).toBe(1);
    });
  });
});
