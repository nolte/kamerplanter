import i18n from '@/i18n/i18n';
import { normalizeNameLanguage } from '@/utils/plantDisplay';

/**
 * #3025 M14 (audit A-13, A-21, B-10) — every date, time, number and text comparison the UI
 * shows goes through this module, which reads the ACTIVE UI language itself. A bare
 * `toLocaleDateString()`, `toFixed()` or `localeCompare()` follows the browser's locale
 * instead (a German UI on an English browser showed "4/4/2026" and "0.2 L"); a call site
 * that passes `i18n.language` by hand is the same rule written N times.
 * Guarded by `src/test/guards/localeFormattingHasOneHome.test.ts`.
 *
 * Components still read `useTranslation()` so they re-render on a language switch; the
 * helpers then format in the new language.
 */

/**
 * Strip HTML markup from a string and return its plain text.
 *
 * Reference-image attributions sourced from Wikimedia Commons (`extmetadata`
 * `Artist`) can contain HTML (e.g. `<a href="...">Name</a> from France`).
 * Rendered as text that markup would leak into the caption, so we reduce it to
 * its text content and collapse whitespace. Returns an empty string for nullish
 * input.
 */
export function stripHtml(value: string | null | undefined): string {
  if (!value) return '';
  // Fast path: no tags and no entities → just collapse whitespace.
  if (!value.includes('<') && !value.includes('&')) return value.replace(/\s+/g, ' ').trim();
  // DOMParser strips tags AND decodes entities (e.g. "&amp;" → "&").
  const doc = new DOMParser().parseFromString(value, 'text/html');
  return (doc.body.textContent ?? '').replace(/\s+/g, ' ').trim();
}

/** BCP-47 locale per UI language; German is the default and the fallback. */
const LOCALES: Readonly<Record<string, string>> = { de: 'de-DE', en: 'en-US' };

/** Return the active BCP-47 locale (e.g. "de-DE", "en-US"). `de-AT` or `de_DE` count as German. */
export function activeLocale(): string {
  return LOCALES[normalizeNameLanguage(i18n.language)] ?? LOCALES.de;
}

/** Matches a bare calendar date `YYYY-MM-DD` with no time component. */
const DATE_ONLY_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Parse a date/time value into a `Date`.
 *
 * A bare `YYYY-MM-DD` string (e.g. a forecast date) is interpreted as a **local**
 * calendar date rather than UTC midnight: `new Date('2026-07-06')` parses as UTC
 * midnight, which renders as the *previous* day in negative-UTC-offset zones
 * (the Americas). Strings that carry a time component are left to the native
 * parser unchanged, so existing callers are unaffected.
 */
function toDate(value: string | Date | number): Date {
  if (typeof value === 'number') return new Date(value);
  if (typeof value !== 'string') return value;
  const match = DATE_ONLY_RE.exec(value);
  if (match) {
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }
  return new Date(value);
}

/**
 * Format a date/time string or Date object as locale-aware date+time.
 * Example DE: "04.04.2026, 12:04"
 * Example EN: "4/4/2026, 12:04 PM"
 */
export function formatDateTime(value: string | Date | number | null | undefined): string {
  if (value == null || value === '') return '—';
  const date = toDate(value);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleString(activeLocale(), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a date string or Date object as locale-aware date only.
 * Example DE: "04.04.2026"
 * Example EN: "4/4/2026"
 */
export function formatDate(value: string | Date | number | null | undefined): string {
  if (value == null || value === '') return '—';
  const date = toDate(value);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(activeLocale(), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

/**
 * Format a date/time with explicit `Intl` options in the active locale — a weekday, a month
 * name, "5. März". Only the fields in `options` are shown; with none (e.g. only a
 * `timeZone`) the numeric date. A bare `YYYY-MM-DD` is a local calendar day (see `toDate`) unless the
 * options fix a `timeZone`: then the instant is kept as parsed, so `{ timeZone: 'UTC' }` on
 * a server date shows that date. Returns '—' for a missing or invalid value.
 */
export function formatDateWith(
  value: string | Date | number | null | undefined,
  options: Intl.DateTimeFormatOptions,
): string {
  if (value == null || value === '') return '—';
  const date = options.timeZone && typeof value === 'string' ? new Date(value) : toDate(value);
  if (isNaN(date.getTime())) return '—';
  // `Intl.DateTimeFormat` shows exactly the fields asked for and the numeric date when none is.
  return new Intl.DateTimeFormat(activeLocale(), options).format(date);
}

/**
 * Format the time of day, hours and minutes. Example DE: "14:05" — EN: "02:05 PM".
 */
export function formatTime(value: string | Date | null | undefined): string {
  return formatDateWith(value, { hour: '2-digit', minute: '2-digit' });
}

/** Name of a month, `month` 1–12. Example DE `long`: "März" — EN `short`: "Mar". */
export function formatMonthName(month: number, style: 'long' | 'short' | 'narrow' = 'long'): string {
  if (!Number.isInteger(month) || month < 1 || month > 12) return '—';
  return new Date(2000, month - 1, 1).toLocaleString(activeLocale(), { month: style });
}

/** The seven weekday names, Monday first. Example DE `short`: "Mo.", "Di.", … */
export function formatWeekdayNames(style: 'long' | 'short' | 'narrow' = 'short'): string[] {
  // 2024-01-01 was a Monday.
  return Array.from({ length: 7 }, (_, offset) => formatDateWith(new Date(2024, 0, 1 + offset), { weekday: style }));
}

/**
 * Format a number with locale-aware decimal separator.
 * Example DE: 0,2 — Example EN: 0.2
 */
export function formatNumber(
  value: number | null | undefined,
  options?: { minimumFractionDigits?: number; maximumFractionDigits?: number },
): string {
  if (value == null) return '—';
  return value.toLocaleString(activeLocale(), {
    minimumFractionDigits: options?.minimumFractionDigits ?? 0,
    maximumFractionDigits: options?.maximumFractionDigits ?? 3,
  });
}

/**
 * A number with exactly `digits` decimals in the active locale — the display form of
 * `value.toFixed(digits)`. Example DE `formatFixed(0.2, 2)`: "0,20" — EN: "0.20".
 * Returns '—' for a missing or non-finite value.
 */
export function formatFixed(value: number | null | undefined, digits: number): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return formatNumber(value, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** Group and decimal separator of the active locale (de-DE: "." and ","; en-US: "," and "."). */
function localeSeparators(): { group: string; decimal: string } {
  const parts = new Intl.NumberFormat(activeLocale()).formatToParts(12345.6);
  return {
    group: parts.find((part) => part.type === 'group')?.value ?? ',',
    decimal: parts.find((part) => part.type === 'decimal')?.value ?? '.',
  };
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Read back a number as the helpers above display it, in the active locale: DE "6,5",
 * "1.234,5", EN "6.5", "1,234.5". Grouping must be well-formed (groups of three); a
 * string that is not such a number falls back to `Number()` (a raw `String(6.5)` in a
 * table cell), and anything else is `null`. Ambiguous on purpose only where the display
 * is: in German "1.234" is one thousand two hundred thirty-four, as `formatNumber` writes it.
 */
export function parseLocaleNumber(text: string | null | undefined): number | null {
  const value = text?.trim() ?? '';
  if (!value) return null;
  const { group, decimal } = localeSeparators();
  const g = escapeRegExp(group);
  const d = escapeRegExp(decimal);
  const localized = new RegExp(`^[+-]?(?:\\d{1,3}(?:${g}\\d{3})+|\\d+)(?:${d}\\d+)?$`);
  if (localized.test(value)) {
    const canonical = value.split(group).join('').replace(decimal, '.');
    const parsed = Number(canonical);
    if (Number.isFinite(parsed)) return parsed;
  }
  const raw = Number(value);
  return Number.isFinite(raw) ? raw : null;
}

/**
 * Fold the separator between two digits to one character, so a search for "6.5" finds
 * "6,5" and the other way round. A separator after a digit at the very end counts too
 * ("6," while the user is still typing). Text without digits is unchanged. Used to add
 * matches, never to replace the plain comparison (see DataTable's search).
 */
export function foldDecimalSeparators(text: string): string {
  return text.replace(/(\d)[.,](?=\d|$)/g, '$1.');
}

const collators = new Map<string, Intl.Collator>();

/**
 * Compare two texts for sorting in the active UI language — the replacement for
 * `a.localeCompare(b)`, which sorts by the browser's locale. Collators are cached per
 * locale and options. Options as for `Intl.Collator` (e.g. `{ sensitivity: 'base' }`,
 * `{ numeric: true }`).
 */
export function compareText(a: string, b: string, options?: Intl.CollatorOptions): number {
  const locale = activeLocale();
  const cacheKey = `${locale}|${options ? JSON.stringify(options) : ''}`;
  let collator = collators.get(cacheKey);
  if (!collator) {
    collator = new Intl.Collator(locale, options);
    collators.set(cacheKey, collator);
  }
  return collator.compare(a, b);
}

/**
 * Format a hyphenated slug (e.g. an entity key like `species_key`
 * "ocimum-basilicum") as a readable label ("Ocimum Basilicum").
 *
 * This is a purely cosmetic slug→label transform (capitalise each
 * hyphen-separated word), not a localized/looked-up display name — it exists
 * for call sites that only have the raw key on hand and no catalog lookup
 * (e.g. the `plant_grid` dashboard widget, #461, whose aggregated payload
 * carries `species_key` but not a resolved species name). Returns an empty
 * string for nullish/blank input so callers can `||`-chain it into a further
 * fallback.
 */
export function humanizeSlug(slug: string | null | undefined): string {
  if (!slug) return '';
  return slug
    .split('-')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format a number with a unit suffix.
 * Example DE: "0,2 L" — Example EN: "0.2 L"
 */
export function formatNumberWithUnit(
  value: number | null | undefined,
  unit: string,
  options?: { minimumFractionDigits?: number; maximumFractionDigits?: number },
): string {
  if (value == null) return '—';
  return `${formatNumber(value, options)} ${unit}`;
}
