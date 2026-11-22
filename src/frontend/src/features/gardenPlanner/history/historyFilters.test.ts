import { describe, expect, it } from 'vitest';
import {
  activeFilterCount,
  emptyFilters,
  HISTORY_CATEGORIES,
  isProtocolCategory,
  isRangeInverted,
  toQuery,
} from './historyFilters';

const NOW = new Date('2026-06-15T12:00:00Z');
const DAY = 24 * 3600 * 1000;

describe('toQuery', () => {
  it('sends nothing for a bed with the default "all time" - a bed has no default window', () => {
    expect(toQuery(emptyFilters('all'), NOW, 'bed')).toEqual({});
  });

  it('sends a range for "all time" on the tenant-wide log, whose server default is 90 days', () => {
    const query = toQuery(emptyFilters('all'), NOW, 'tenant');
    expect(query.from).toBe('2000-01-01T00:00:00.000Z');
    expect(query.to).toBeUndefined();
  });

  it.each([
    ['30d', 30],
    ['90d', 90],
    ['365d', 365],
  ] as const)('%s starts that many days before now', (period, days) => {
    expect(toQuery(emptyFilters(period), NOW, 'tenant').from).toBe(new Date(NOW.getTime() - days * DAY).toISOString());
  });

  it('turns a custom range into the first and the last instant of the days', () => {
    const query = toQuery({ ...emptyFilters('custom'), from: '2026-03-01', to: '2026-03-31' }, NOW, 'bed');
    expect(new Date(query.from ?? '').getTime()).toBe(new Date('2026-03-01T00:00:00').getTime());
    expect(new Date(query.to ?? '').getTime()).toBe(new Date('2026-03-31T23:59:59.999').getTime());
  });

  it('leaves an unparsable custom date out instead of sending "Invalid Date"', () => {
    const query = toQuery({ ...emptyFilters('custom'), from: 'garbage', to: '' }, NOW, 'bed');
    expect(query).toEqual({});
  });

  it('carries the other filters, and the bed only on the tenant-wide scope', () => {
    const filters = {
      ...emptyFilters('all'),
      category: 'watering',
      plantKey: 'pi_1',
      performedBy: 'u_1',
      includeCorrections: true,
      locationKey: 'loc_1',
    };
    expect(toQuery(filters, NOW, 'bed')).toEqual({
      category: 'watering',
      plant_key: 'pi_1',
      performed_by: 'u_1',
      include_corrections: true,
    });
    expect(toQuery(filters, NOW, 'tenant').location_key).toBe('loc_1');
  });
});

describe('the range', () => {
  it('is inverted only for a custom range that ends before it starts', () => {
    expect(isRangeInverted({ ...emptyFilters('custom'), from: '2026-06-10', to: '2026-06-01' })).toBe(true);
    expect(isRangeInverted({ ...emptyFilters('custom'), from: '2026-06-01', to: '2026-06-10' })).toBe(false);
    expect(isRangeInverted({ ...emptyFilters('custom'), from: '2026-06-01', to: '' })).toBe(false);
    expect(isRangeInverted({ ...emptyFilters('90d'), from: '2026-06-10', to: '2026-06-01' })).toBe(false);
  });
});

describe('activeFilterCount', () => {
  it('counts what differs from the default of the surface', () => {
    const defaults = emptyFilters('90d');
    expect(activeFilterCount(defaults, defaults)).toBe(0);
    expect(activeFilterCount({ ...defaults, category: 'feeding', includeCorrections: true }, defaults)).toBe(2);
    expect(activeFilterCount({ ...defaults, period: 'all' }, defaults)).toBe(1);
  });
});

describe('the categories on offer', () => {
  it('offer the protocol entries a care log holds beside the task categories', () => {
    for (const category of ['note', 'planting', 'removal', 'clearing', 'bed_status_change', 'position_corrected']) {
      expect(HISTORY_CATEGORIES).toContain(category);
      expect(isProtocolCategory(category)).toBe(true);
    }
    expect(isProtocolCategory('watering')).toBe(false);
    expect(new Set(HISTORY_CATEGORIES).size).toBe(HISTORY_CATEGORIES.length);
  });
});
