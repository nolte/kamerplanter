import { describe, expect, it } from 'vitest';
import i18n from 'i18next';

/**
 * #3017 — the accessible names added for the calendar grid, the Gantt inline editors and the calendar
 * plant filter exist in German and English, keep the same placeholders, and the German strings address
 * nobody formally (the catalogue-wide "du" guard is `privacyInformalAddress.test.ts`).
 */
const KEYS: Record<string, Record<string, unknown>> = {
  'pages.calendar.dayEntryCount': { count: 1 },
  'pages.calendar.dayEntryCount_other': { count: 3 },
  'pages.calendar.plantFilter.showPlantsOf': { run: 'Batch A' },
  'pages.gantt.weekNumber': { week: 4 },
  'pages.gantt.editCell': { field: 'EC, 4', value: 1.5 },
  'pages.gantt.moveFertilizerUp': { name: 'BioGrow' },
  'pages.gantt.moveFertilizerDown': { name: 'BioGrow' },
  'pages.gantt.removeFertilizer': { name: 'BioGrow' },
};

const FORMAL = /\b(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)\b/;

describe('#3017 accessible-name strings', () => {
  it.each(Object.entries(KEYS))('%s is translated in de and en with every placeholder filled', (key, vars) => {
    for (const lng of ['de', 'en']) {
      const raw = i18n.getResource(lng, 'translation', key) as string | undefined;
      expect(raw, `${lng}:${key}`).toBeTruthy();
      const text = i18n.t(key, { ...vars, lng });
      expect(text).not.toContain('{{');
      for (const value of Object.values(vars)) expect(text).toContain(String(value));
    }
    expect(i18n.getResource('de', 'translation', key)).not.toMatch(FORMAL);
  });

  it('pluralises the day entry count', () => {
    expect(i18n.t('pages.calendar.dayEntryCount', { count: 1, lng: 'de' })).toBe('1 Eintrag');
    expect(i18n.t('pages.calendar.dayEntryCount', { count: 3, lng: 'de' })).toBe('3 Einträge');
    expect(i18n.t('pages.calendar.dayEntryCount', { count: 3, lng: 'en' })).toBe('3 entries');
  });
});
