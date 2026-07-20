import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

export type MonthLabelFormat = 'long' | 'short';

/**
 * Localised month labels for the active app locale — e.g. January…December
 * ('long') or Jan…Dez ('short'). Index 0 is January, index 11 is December.
 *
 * Uses `Intl.DateTimeFormat` so no per-month i18n keys are needed (keeps the
 * translation bundles small). The returned array is memoised on locale + format
 * to satisfy the custom-hook stability rule (FRONTEND.md).
 */
export function useMonthLabels(format: MonthLabelFormat = 'long'): string[] {
  const { i18n } = useTranslation();
  return useMemo(() => {
    const fmt = new Intl.DateTimeFormat(i18n.language, { month: format });
    // Any non-leap year works; day 1 of each month renders the month name only.
    return Array.from({ length: 12 }, (_, idx) =>
      fmt.format(new Date(2001, idx, 1)),
    );
  }, [i18n.language, format]);
}

export default useMonthLabels;
