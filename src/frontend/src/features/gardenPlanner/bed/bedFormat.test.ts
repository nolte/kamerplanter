import { describe, expect, it } from 'vitest';
import i18next from 'i18next';
import { isOverdue, siteConditionsLine, sunProfileLine } from './bedFormat';

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
