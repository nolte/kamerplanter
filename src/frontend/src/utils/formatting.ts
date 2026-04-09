import i18n from '@/i18n/i18n';

/** Return the active BCP-47 locale (e.g. "de-DE", "en-US"). */
function activeLocale(): string {
  const lang = i18n.language ?? 'de';
  return lang === 'de' ? 'de-DE' : 'en-US';
}

/**
 * Format a date/time string or Date object as locale-aware date+time.
 * Example DE: "04.04.2026, 12:04"
 * Example EN: "4/4/2026, 12:04 PM"
 */
export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return '\u2014';
  const date = typeof value === 'string' ? new Date(value) : value;
  if (isNaN(date.getTime())) return '\u2014';
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
  if (!value) return '\u2014';
  const date = typeof value === 'string' ? new Date(value) : value;
  if (isNaN(date.getTime())) return '\u2014';
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
  if (value == null) return '\u2014';
  return value.toLocaleString(activeLocale(), {
    minimumFractionDigits: options?.minimumFractionDigits ?? 0,
    maximumFractionDigits: options?.maximumFractionDigits ?? 3,
  });
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
  if (value == null) return '\u2014';
  return `${formatNumber(value, options)} ${unit}`;
}
