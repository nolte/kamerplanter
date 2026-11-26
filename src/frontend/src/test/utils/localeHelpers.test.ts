import { afterEach, describe, expect, it } from 'vitest';
import i18n from '@/i18n/i18n';
import {
  activeLocale,
  compareText,
  formatDate,
  formatDateWith,
  formatFixed,
  formatMonthName,
  formatNumberWithUnit,
  formatTime,
  formatWeekdayNames,
} from '@/utils/formatting';
import { compareCodes } from '@/utils/compareCodes';
import { localizedText } from '@/utils/localizedText';

/**
 * #3025 M14 — the locale helpers take the ACTIVE UI language, not the browser's: the same
 * value reads "0,20" in German and "0.20" in English, and a switch at runtime applies to
 * the next call.
 */

async function inLanguage(language: string): Promise<void> {
  await i18n.changeLanguage(language);
}

describe('locale helpers follow the active UI language (A-13, A-21, B-10)', () => {
  const initial = i18n.language;
  afterEach(async () => {
    await i18n.changeLanguage(initial);
  });

  it('maps the UI language to one BCP-47 locale', async () => {
    await inLanguage('de');
    expect(activeLocale()).toBe('de-DE');
    await inLanguage('en');
    expect(activeLocale()).toBe('en-US');
  });

  it('formatFixed writes the decimal separator of the language (the toFixed replacement)', async () => {
    await inLanguage('de');
    expect(formatFixed(0.2, 2)).toBe('0,20');
    expect(formatFixed(1234.5, 1)).toBe('1.234,5');
    await inLanguage('en');
    expect(formatFixed(0.2, 2)).toBe('0.20');
    expect(formatFixed(null, 2)).toBe('—');
    expect(formatFixed(Number.NaN, 2)).toBe('—');
  });

  it('formatNumberWithUnit keeps the unit and localizes the number', async () => {
    await inLanguage('de');
    expect(formatNumberWithUnit(1500, 'ml')).toBe('1.500 ml');
  });

  it('formats dates, times, month and weekday names in the active language', async () => {
    await inLanguage('de');
    expect(formatDate(new Date(2026, 3, 4))).toBe('04.04.2026');
    expect(formatMonthName(3)).toBe('März');
    expect(formatWeekdayNames('short')[0]).toMatch(/^Mo/);
    expect(formatDateWith(new Date(2026, 2, 5), { day: 'numeric', month: 'long' })).toBe('5. März');
    expect(formatTime(new Date(2026, 0, 1, 14, 5))).toBe('14:05');
    await inLanguage('en');
    expect(formatDate(new Date(2026, 3, 4))).toBe('04/04/2026');
    expect(formatMonthName(3, 'short')).toBe('Mar');
    expect(formatWeekdayNames('short')[0]).toBe('Mon');
  });

  it('formatDateWith shows only the asked fields and keeps a UTC day in UTC', async () => {
    await inLanguage('de');
    expect(formatDateWith('2026-07-06T00:00:00Z', { timeZone: 'UTC' })).toBe('6.7.2026');
    expect(formatDateWith(null, { month: 'long' })).toBe('—');
    expect(formatDateWith('not a date', { month: 'long' })).toBe('—');
    expect(formatMonthName(13)).toBe('—');
  });

  it('compareText sorts by the active language (German ä next to a)', async () => {
    await inLanguage('de');
    expect(['Zwiebel', 'Ährenrispe', 'Apfel'].sort(compareText)).toEqual(['Ährenrispe', 'Apfel', 'Zwiebel']);
    expect(compareText('apfel', 'Apfel', { sensitivity: 'base' })).toBe(0);
  });
});

describe('compareCodes (machine codes, every language alike)', () => {
  it('orders by code unit and is stable across languages', () => {
    expect(['b', 'a_2', 'A', 'a_10'].sort(compareCodes)).toEqual(['A', 'a_10', 'a_2', 'b']);
    expect(compareCodes('x', 'x')).toBe(0);
  });
});

describe('localizedText (A-16)', () => {
  it('picks the UI language, then the other language, then the fallback', () => {
    const names = { de: 'Gießen', en: 'Watering' };
    expect(localizedText('de', names)).toBe('Gießen');
    expect(localizedText('de-AT', names)).toBe('Gießen');
    expect(localizedText('en', names)).toBe('Watering');
    expect(localizedText('en', { de: 'Gießen', en: '' })).toBe('Gießen');
    expect(localizedText('de', { de: '  ', en: 'Watering' })).toBe('Watering');
    expect(localizedText('de', { de: null, en: undefined }, 'watering')).toBe('watering');
    expect(localizedText('en', {})).toBe('');
  });

  it('reads any language that is not English as German, the app default', () => {
    expect(localizedText('fr', { de: 'Gießen', en: 'Watering' })).toBe('Gießen');
    expect(localizedText(undefined, { de: 'Gießen', en: 'Watering' })).toBe('Gießen');
  });
});
