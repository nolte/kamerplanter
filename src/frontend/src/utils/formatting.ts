import i18n from '@/i18n/i18n';

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

/** Return the active BCP-47 locale (e.g. "de-DE", "en-US"). */
function activeLocale(): string {
  const lang = i18n.language ?? 'de';
  return lang === 'de' ? 'de-DE' : 'en-US';
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
function toDate(value: string | Date): Date {
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
export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return '—';
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
export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return '—';
  const date = toDate(value);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(activeLocale(), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
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
