/**
 * The filter model of the bed history and of the tenant-wide history (REQ-053 GP-FR-102, GP-FR-107):
 * category, period, plant, person and the corrections switch, and its translation into query
 * parameters. Pure functions: the tab, the page and their tests share them.
 */
import { BED_CARE_CATEGORIES, NOTE_CATEGORY } from '../care/careCategories';

export type Period = '30d' | '90d' | '365d' | 'all' | 'custom';

export interface HistoryFilters {
  category: string;
  period: Period;
  /** `yyyy-mm-dd`; only read when `period` is `custom`. */
  from: string;
  to: string;
  plantKey: string;
  /** Account key of the member; `''` is everyone. */
  performedBy: string;
  includeCorrections: boolean;
  /** The tenant-wide page only. */
  locationKey: string;
}

export function emptyFilters(period: Period): HistoryFilters {
  return {
    category: '',
    period,
    from: '',
    to: '',
    plantKey: '',
    performedBy: '',
    includeCorrections: false,
    locationKey: '',
  };
}

/** Protocol-only values of `care_events.category` (§20.10) next to the task categories. */
export const PROTOCOL_CATEGORIES = [
  NOTE_CATEGORY,
  'planting',
  'removal',
  'clearing',
  'bed_status_change',
  'position_corrected',
] as const;

/** What the category filter offers: the care categories first, then the protocol entries. */
export const HISTORY_CATEGORIES: readonly string[] = [...BED_CARE_CATEGORIES, ...PROTOCOL_CATEGORIES];

/** Shown by the translation key of the protocol entries; everything else is a task category. */
export function isProtocolCategory(category: string): boolean {
  return (PROTOCOL_CATEGORIES as readonly string[]).includes(category);
}

/** The query of both history endpoints; absent values are left out. */
export interface HistoryQuery {
  category?: string;
  plant_key?: string;
  from?: string;
  to?: string;
  performed_by?: string;
  include_corrections?: boolean;
  location_key?: string;
}

const DAY_MS = 24 * 60 * 60 * 1000;
const PRESET_DAYS: Partial<Record<Period, number>> = { '30d': 30, '90d': 90, '365d': 365 };
/** `all` on the tenant-wide page: the server's 90-day default only applies when no range is sent. */
const OLDEST = '2000-01-01T00:00:00.000Z';

function startOfDay(value: string): string | undefined {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

function endOfDay(value: string): string | undefined {
  const date = new Date(`${value}T23:59:59.999`);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

/**
 * The query for `filters`. A bed's history has no default window, so `all` sends no range there; the
 * tenant-wide log answers the last 90 days unless a range is sent, so `all` sends one.
 */
export function toQuery(filters: HistoryFilters, now: Date, scope: 'bed' | 'tenant'): HistoryQuery {
  const query: HistoryQuery = {};
  if (filters.category) query.category = filters.category;
  if (filters.plantKey) query.plant_key = filters.plantKey;
  if (filters.performedBy) query.performed_by = filters.performedBy;
  if (filters.includeCorrections) query.include_corrections = true;
  if (scope === 'tenant' && filters.locationKey) query.location_key = filters.locationKey;

  const days = PRESET_DAYS[filters.period];
  if (days !== undefined) {
    query.from = new Date(now.getTime() - days * DAY_MS).toISOString();
  } else if (filters.period === 'custom') {
    const from = filters.from ? startOfDay(filters.from) : undefined;
    const to = filters.to ? endOfDay(filters.to) : undefined;
    if (from) query.from = from;
    if (to) query.to = to;
  } else if (scope === 'tenant') {
    query.from = OLDEST;
  }
  return query;
}

/** Whether `custom` names a range that ends before it starts (the server answers 422). */
export function isRangeInverted(filters: HistoryFilters): boolean {
  return filters.period === 'custom' && filters.from !== '' && filters.to !== '' && filters.to < filters.from;
}

/** How many filters differ from the default, for the "reset" affordance and the empty state wording. */
export function activeFilterCount(filters: HistoryFilters, defaults: HistoryFilters): number {
  const keys = Object.keys(defaults) as (keyof HistoryFilters)[];
  return keys.filter((key) => filters[key] !== defaults[key]).length;
}
