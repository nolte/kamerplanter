import { describe, it, expect } from 'vitest';
import { deFull as de, enFull as en } from '../i18nTestResources';
import { DIARY_ANALYSIS_STATES, DIARY_ENTRY_TYPES } from '@/api/endpoints/diary';

/**
 * REQ-050 AK-28 — every diary surface string exists in DE **and** EN, with DE as
 * default and fallback.
 *
 * The enum member lists are imported from the API module rather than restated,
 * so adding a diary entry type or an analysis state without its two labels
 * fails here instead of shipping a raw key like `enums.diaryEntryType.sketch`
 * into the UI.
 */

function at(locale: unknown, path: string[]): unknown {
  return path.reduce<unknown>(
    (node, key) => (node as Record<string, unknown> | undefined)?.[key],
    locale,
  );
}

function nonEmptyString(value: unknown): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

describe('diary i18n parity (REQ-050 AK-28)', () => {
  it.each(DIARY_ENTRY_TYPES)('labels the entry type "%s" in DE and EN', (value) => {
    expect(nonEmptyString(at(de, ['enums', 'diaryEntryType', value]))).toBe(true);
    expect(nonEmptyString(at(en, ['enums', 'diaryEntryType', value]))).toBe(true);
  });

  it.each(DIARY_ANALYSIS_STATES)('labels the analysis state "%s" in DE and EN', (value) => {
    expect(nonEmptyString(at(de, ['enums', 'diaryAnalysisState', value]))).toBe(true);
    expect(nonEmptyString(at(en, ['enums', 'diaryAnalysisState', value]))).toBe(true);
  });

  it.each(DIARY_ANALYSIS_STATES)('explains the analysis state "%s" in DE and EN', (value) => {
    expect(
      nonEmptyString(at(de, ['pages', 'plantDiary', 'analysis', 'stateHint', value])),
    ).toBe(true);
    expect(
      nonEmptyString(at(en, ['pages', 'plantDiary', 'analysis', 'stateHint', value])),
    ).toBe(true);
  });

  it.each(['veryLow', 'low', 'moderate', 'high', 'veryHigh'])(
    'puts the confidence band "%s" into words in DE and EN (AK-30)',
    (band) => {
      expect(nonEmptyString(at(de, ['enums', 'diaryConfidence', band]))).toBe(true);
      expect(nonEmptyString(at(en, ['enums', 'diaryConfidence', band]))).toBe(true);
    },
  );

  const flatten = (node: unknown, prefix = ''): string[] => {
    if (typeof node !== 'object' || node === null) return [prefix];
    return Object.entries(node as Record<string, unknown>).flatMap(([key, value]) =>
      flatten(value, prefix ? `${prefix}.${key}` : key),
    );
  };

  it.each([['plantDiary'], ['diaryOverview']])(
    'has the identical key set under pages.%s in both locales',
    (section) => {
      const deKeys = flatten(at(de, ['pages', section])).sort();
      const enKeys = flatten(at(en, ['pages', section])).sort();
      expect(enKeys).toEqual(deKeys);
      expect(deKeys.length).toBeGreaterThan(0);
    },
  );

  it('labels the diary module and its nav entry in DE and EN (AK-31, AK-28)', () => {
    // Without these the module list and the sidebar show the raw key: the
    // module is registered, and unreadable.
    for (const locale of [de, en]) {
      expect(nonEmptyString(at(locale, ['modules', 'diary', 'label']))).toBe(true);
      expect(nonEmptyString(at(locale, ['modules', 'diary', 'description']))).toBe(true);
      expect(nonEmptyString(at(locale, ['nav', 'diary']))).toBe(true);
    }
  });

  it('names the two shorthand state filters in both locales (AK-17)', () => {
    // §2.5.2 calls these the most frequent access of all; a missing label would
    // put `pages.diaryOverview.filters.quick.completed` on a chip.
    for (const key of ['all', 'completed', 'requested']) {
      expect(
        nonEmptyString(at(de, ['pages', 'diaryOverview', 'filters', 'quick', key])),
      ).toBe(true);
      expect(
        nonEmptyString(at(en, ['pages', 'diaryOverview', 'filters', 'quick', key])),
      ).toBe(true);
    }
  });

  it('keeps the overview’s waiting hint free of any duration promise (AK-27)', () => {
    const deHint = at(de, ['pages', 'diaryOverview', 'analysis', 'waitingHint']) as string;
    const enHint = at(en, ['pages', 'diaryOverview', 'analysis', 'waitingHint']) as string;
    expect(nonEmptyString(deHint)).toBe(true);
    expect(nonEmptyString(enHint)).toBe(true);
    // No percentage, no "in X minutes": nothing in this installation knows when
    // an externally-run agent will pick the entry up (§3).
    expect(deHint).not.toMatch(/%|\bMinuten\b|\bStunden\b/);
    expect(enHint).not.toMatch(/%|\bminutes\b|\bhours\b/);
  });

  it('states the waiting text without promising a duration (AK-27)', () => {
    const deWaiting = at(de, ['pages', 'plantDiary', 'analysis', 'waiting']) as string;
    const enWaiting = at(en, ['pages', 'plantDiary', 'analysis', 'waiting']) as string;
    expect(deWaiting.toLowerCase()).toContain('wartet');
    expect(enWaiting.toLowerCase()).toContain('waiting');
    // No "in X minutes", no percentage — §3 is explicit that no such promise
    // can be made, because the analysing agent runs outside this system.
    expect(deWaiting).not.toMatch(/%|\bMinuten\b/);
    expect(enWaiting).not.toMatch(/%|\bminutes\b/);
  });
});
