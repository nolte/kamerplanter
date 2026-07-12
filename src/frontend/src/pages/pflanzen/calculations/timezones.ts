/**
 * IANA time-zone options for the sun-times calculator. Prefers the runtime's own
 * complete list via `Intl.supportedValuesOf('timeZone')` (all modern browsers +
 * Node 18+); falls back to a curated common subset where the API is unavailable
 * (e.g. some test/JSDOM runtimes). Always includes the default so the control
 * never renders an unmatched value.
 */

export const DEFAULT_TIMEZONE = 'Europe/Berlin';

const FALLBACK_TIMEZONES: readonly string[] = [
  'UTC',
  'Europe/Berlin',
  'Europe/Vienna',
  'Europe/Zurich',
  'Europe/London',
  'Europe/Paris',
  'Europe/Madrid',
  'Europe/Rome',
  'Europe/Amsterdam',
  'Europe/Warsaw',
  'Europe/Athens',
  'Europe/Moscow',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Sao_Paulo',
  'Africa/Cairo',
  'Asia/Dubai',
  'Asia/Kolkata',
  'Asia/Shanghai',
  'Asia/Tokyo',
  'Australia/Sydney',
  'Pacific/Auckland',
] as const;

interface IntlWithSupportedValues {
  supportedValuesOf?: (key: 'timeZone') => string[];
}

/**
 * Returns the sorted list of selectable IANA zones. Guaranteed to contain
 * {@link DEFAULT_TIMEZONE}. Memoised at module scope by the caller via `useMemo`.
 */
export function getTimezoneOptions(): string[] {
  const intl = Intl as unknown as IntlWithSupportedValues;
  let zones: string[];
  if (typeof intl.supportedValuesOf === 'function') {
    try {
      zones = intl.supportedValuesOf('timeZone');
    } catch {
      zones = [...FALLBACK_TIMEZONES];
    }
  } else {
    zones = [...FALLBACK_TIMEZONES];
  }
  if (!zones.includes(DEFAULT_TIMEZONE)) {
    zones = [DEFAULT_TIMEZONE, ...zones];
  }
  return zones;
}
