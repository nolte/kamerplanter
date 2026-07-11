import { describe, it, expect } from 'vitest';
import type { SiteType } from '@/api/types';
import {
  SITE_TYPE_VALUES,
  WEATHER_RELEVANT_SITE_TYPES,
  isWeatherRelevantSiteType,
  buildSiteResolver,
  gpsToPayload,
  gpsToFields,
  siteTypeOptions,
  type SiteFormData,
} from '@/pages/standorte/siteForm';

type Resolver = ReturnType<typeof buildSiteResolver>;
const identityT = ((key: string) => key) as unknown as Parameters<typeof buildSiteResolver>[0];

async function runResolver(resolver: Resolver, values: SiteFormData) {
  return resolver(
    values,
    undefined,
    { fields: {}, shouldUseNativeValidation: false, criteriaMode: 'firstError', names: [] },
  );
}

const baseForm: SiteFormData = {
  name: 'Site',
  type: 'balcony',
  gps_lat: '',
  gps_lon: '',
  climate_zone: '',
  total_area_m2: 0,
  timezone: 'UTC',
};

describe('siteForm — WEATHER_RELEVANT_SITE_TYPES SSOT', () => {
  it('treats outdoor, greenhouse and balcony as weather-relevant', () => {
    expect(isWeatherRelevantSiteType('outdoor')).toBe(true);
    expect(isWeatherRelevantSiteType('greenhouse')).toBe(true);
    expect(isWeatherRelevantSiteType('balcony')).toBe(true);
  });

  it('keeps genuinely indoor types disabled', () => {
    expect(isWeatherRelevantSiteType('indoor')).toBe(false);
    expect(isWeatherRelevantSiteType('windowsill')).toBe(false);
    expect(isWeatherRelevantSiteType('grow_tent')).toBe(false);
  });

  it('handles null/undefined defensively', () => {
    expect(isWeatherRelevantSiteType(null)).toBe(false);
    expect(isWeatherRelevantSiteType(undefined)).toBe(false);
  });

  it('mirrors the frost-exposed set exactly (no drift)', () => {
    expect([...WEATHER_RELEVANT_SITE_TYPES].sort()).toEqual(
      (['balcony', 'greenhouse', 'outdoor'] satisfies SiteType[]).sort(),
    );
  });

  it('every weather-relevant type is a selectable site type', () => {
    for (const type of WEATHER_RELEVANT_SITE_TYPES) {
      expect(SITE_TYPE_VALUES).toContain(type);
    }
  });

  it('every selectable type is classified deterministically', () => {
    for (const type of SITE_TYPE_VALUES) {
      expect(typeof isWeatherRelevantSiteType(type)).toBe('boolean');
    }
  });
});

describe('siteForm — GPS mapping is site-type agnostic', () => {
  it('persists coordinates for a balcony site', () => {
    expect(gpsToPayload({ ...baseForm, type: 'balcony', gps_lat: 52.5, gps_lon: 13.4 })).toEqual([
      52.5, 13.4,
    ]);
  });

  it('returns null when a balcony site has no coordinates', () => {
    expect(gpsToPayload({ ...baseForm, type: 'balcony' })).toBeNull();
  });

  it('round-trips balcony coordinates back into form fields', () => {
    expect(gpsToFields([52.5, 13.4])).toEqual({ gps_lat: 52.5, gps_lon: 13.4 });
    expect(gpsToFields(null)).toEqual({ gps_lat: '', gps_lon: '' });
    expect(gpsToFields(undefined)).toEqual({ gps_lat: '', gps_lon: '' });
  });

  it('returns null when only one coordinate is filled', () => {
    expect(gpsToPayload({ ...baseForm, gps_lat: 52.5, gps_lon: '' })).toBeNull();
    expect(gpsToPayload({ ...baseForm, gps_lat: '', gps_lon: 13.4 })).toBeNull();
  });
});

describe('siteForm — buildSiteResolver GPS validation', () => {
  it('accepts a balcony site with a valid coordinate pair', async () => {
    const resolver = buildSiteResolver(identityT);
    const result = await runResolver(resolver, { ...baseForm, gps_lat: 48.1, gps_lon: 11.6 });
    expect(result.errors).toEqual({});
  });

  it('accepts a balcony site with no coordinates', async () => {
    const resolver = buildSiteResolver(identityT);
    const result = await runResolver(resolver, { ...baseForm });
    expect(result.errors).toEqual({});
  });

  it('rejects a single (unpaired) coordinate', async () => {
    const resolver = buildSiteResolver(identityT);
    const result = await runResolver(resolver, { ...baseForm, gps_lat: 48.1, gps_lon: '' });
    expect(result.errors.gps_lon).toBeTruthy();
  });

  it('rejects an out-of-range latitude', async () => {
    const resolver = buildSiteResolver(identityT);
    const result = await runResolver(resolver, { ...baseForm, gps_lat: 999, gps_lon: 11.6 });
    expect(result.errors.gps_lat).toBeTruthy();
  });

  it('rejects an out-of-range longitude', async () => {
    const resolver = buildSiteResolver(identityT);
    const result = await runResolver(resolver, { ...baseForm, gps_lat: 48.1, gps_lon: 999 });
    expect(result.errors.gps_lon).toBeTruthy();
  });
});

describe('siteForm — siteTypeOptions', () => {
  it('builds a translated option per selectable site type', () => {
    const t = ((key: string) => key) as unknown as Parameters<typeof siteTypeOptions>[0];
    const options = siteTypeOptions(t);
    expect(options).toHaveLength(SITE_TYPE_VALUES.length);
    expect(options.map((o) => o.value)).toEqual([...SITE_TYPE_VALUES]);
    expect(options.find((o) => o.value === 'balcony')?.label).toBe('enums.siteType.balcony');
  });
});
