import { describe, expect, it } from 'vitest';
import i18next from 'i18next';
import i18n from '@/i18n/i18n';
import {
  compareNullableLast,
  isOverdue,
  siteConditionsLine,
  siteFlagsLine,
  sunProfileLine,
  waterSourceText,
} from './bedFormat';

/** The boundary cases live in the shared vectors (`model/overdue.vectors.test.ts`); this pins the re-export. */
describe('isOverdue (bed list column)', () => {
  const now = new Date('2026-06-18T15:30:00Z');

  it('is false for a task due today, whatever the time of day (UTC)', () => {
    expect(isOverdue('2026-06-18T00:00:00Z', now)).toBe(false);
    expect(isOverdue('2026-06-18T23:59:00Z', now)).toBe(false);
  });

  it('is true from the UTC day after the due date', () => {
    expect(isOverdue('2026-06-17T23:59:59Z', now)).toBe(true);
  });

  it('is false for the future, nothing and nonsense', () => {
    expect(isOverdue('2026-06-19T00:00:00Z', now)).toBe(false);
    expect(isOverdue(null, now)).toBe(false);
    expect(isOverdue('not a date', now)).toBe(false);
  });
});

describe('sunProfileLine', () => {
  async function translator(lng: 'de' | 'en') {
    const pages = (await import(`../../../i18n/locales/${lng}/pages.json`)).default as Record<string, unknown>;
    const instance = i18next.createInstance();
    await instance.init({ lng, resources: { [lng]: { translation: pages } }, interpolation: { escapeValue: false } });
    return instance.t.bind(instance);
  }

  it('is null when nothing was recorded', async () => {
    const t = await translator('en');
    expect(sunProfileLine(t, undefined)).toBeNull();
    expect(sunProfileLine(t, { sun_window: 'unknown', direct_sun_hours_summer: null })).toBeNull();
  });

  it('writes the hours in the number format of the language ("6,5" in German)', async () => {
    const profile = { sun_window: 'morning' as const, direct_sun_hours_summer: 6.5, foliage_shade_in_summer: true };
    expect(sunProfileLine(await translator('de'), profile)).toBe(
      'Sonne: Morgens · etwa 6,5 h direkte Sonne · Laubschatten im Sommer',
    );
    expect(sunProfileLine(await translator('en'), profile)).toBe(
      'Sun: Morning · about 6.5 h of direct sun · Leaf shade in summer',
    );
  });
});

describe('siteConditionsLine (GP-FR-162/163/168)', () => {
  const t = ((key: string, options?: Record<string, unknown>) =>
    options?.value !== undefined ? `${key}:${String(options.value)}` : key) as never;

  it('is null when nothing is recorded, also for unknown values', () => {
    expect(siteConditionsLine(t, undefined)).toBeNull();
    expect(siteConditionsLine(t, {})).toBeNull();
    expect(
      siteConditionsLine(t, {
        microclimate: { frost_risk: 'unknown', heat_retention: 'unknown', cold_air_pocket: false },
        wind_exposure: 'unknown',
        access_sides: [],
      }),
    ).toBeNull();
  });

  it('names what was entered in a fixed order, a slope of 0 included', () => {
    const line = siteConditionsLine(t, {
      microclimate: { frost_risk: 'high', cold_air_pocket: true },
      wind_exposure: 'exposed',
      slope_deg: 0,
      access_sides: ['N', 'S'],
    });
    expect(line).toBe(
      [
        'pages.gardenPlan.siteConditions.summary.frost:enums.frostRisk.high',
        'pages.gardenPlan.siteConditions.coldAirPocket.label',
        'pages.gardenPlan.siteConditions.summary.wind:enums.windExposure.exposed',
        'pages.gardenPlan.siteConditions.summary.slope:0',
        'pages.gardenPlan.siteConditions.summary.access:enums.accessSide.N, enums.accessSide.S',
      ].join(' · '),
    );
  });
});

describe('site flags (GP-FR-165, WP 9.11)', () => {
  const de = i18n.getFixedT('de');
  const en = i18n.getFixedT('en');

  it('names exactly the flags that are set', () => {
    expect(siteFlagsLine(de, ['allelopathy_risk'])).toBe('Allelopathie-Risiko am Standort gemeldet');
    expect(siteFlagsLine(de, ['root_competition'])).toBe('Wurzelkonkurrenz am Standort gemeldet');
    expect(siteFlagsLine(en, ['root_competition', 'allelopathy_risk'])).toBe(
      'Root competition/Allelopathy risk reported at this site',
    );
  });

  it('is null without a flag', () => {
    expect(siteFlagsLine(de, [])).toBeNull();
    expect(siteFlagsLine(de, undefined)).toBeNull();
    expect(siteFlagsLine(de, null)).toBeNull();
  });

  it('shows a value it does not know as a neutral report, never as a raw key, and only once', () => {
    const line = siteFlagsLine(de, ['shade_tree', 'other_new_flag', 'root_competition']);
    expect(line).toBe('Weitere Meldung/Wurzelkonkurrenz am Standort gemeldet');
    expect(line).not.toContain('enums.');
  });

  it('is part of the site line, so a bed with flags only has one', () => {
    expect(siteConditionsLine(de, { flags: ['allelopathy_risk'] })).toBe('Konkurrenz: Allelopathie-Risiko');
    expect(siteConditionsLine(en, { wind_exposure: 'exposed', flags: ['root_competition', 'allelopathy_risk'] })).toBe(
      'Wind: Exposed · Competition: Root competition, Allelopathy risk',
    );
    expect(siteConditionsLine(de, { flags: [] })).toBeNull();
  });
});

describe('waterSourceText (GP-FR-167): one formatter for the bed head and the bed list', () => {
  const de = i18n.getFixedT('de');
  const en = i18n.getFixedT('en');

  it('writes "at the bed" for every distance that would print as 0 m, in both places', () => {
    for (const metres of [0, 0.001, 0.0049]) {
      expect(waterSourceText(en, 'en', metres, 'header')).toBe('Right at the bed');
      expect(waterSourceText(en, 'en', metres, 'list')).toBe('Right at the bed');
      expect(waterSourceText(de, 'de', metres, 'list')).toBe('Direkt am Beet');
    }
  });

  it('writes two decimals at most with the locale\'s decimal mark', () => {
    expect(waterSourceText(en, 'en', 0.005, 'list')).toBe('0.01 m');
    expect(waterSourceText(de, 'de', 3.256, 'list')).toBe('3,26 m');
    expect(waterSourceText(en, 'en', 3.25, 'header')).toBe('3.25 m in a straight line from the bed edge');
  });

  it('has nothing to write without a value', () => {
    expect(waterSourceText(en, 'en', null, 'header')).toBeNull();
    expect(waterSourceText(en, 'en', undefined, 'list')).toBeNull();
  });
});

describe('compareNullableLast (a DataTable comparator, which the table multiplies by the direction)', () => {
  const sorted = (values: (number | null)[], direction: 'asc' | 'desc') => {
    const dir = direction === 'asc' ? 1 : -1;
    return [...values].sort((a, b) => compareNullableLast(a, b, direction) * dir);
  };

  it('keeps missing values last in both directions', () => {
    expect(sorted([2, null, 0.5, null, 1], 'asc')).toEqual([0.5, 1, 2, null, null]);
    expect(sorted([2, null, 0.5, null, 1], 'desc')).toEqual([2, 1, 0.5, null, null]);
  });
});
