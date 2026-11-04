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
  isDayOfYear,
  thresholdsToFields,
  thresholdsToPayload,
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
  ...thresholdsToFields(null),
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

describe('siteForm — garden-planning thresholds (REQ-053 WP 8.24)', () => {
  const sun = (patch: Partial<SiteFormData['sun_class_thresholds']>) => ({
    ...baseForm,
    sun_class_thresholds: { ...baseForm.sun_class_thresholds, ...patch },
  });
  const reach = (patch: Partial<SiteFormData['reach_thresholds']>) => ({
    ...baseForm,
    reach_thresholds: { ...baseForm.reach_thresholds, ...patch },
  });

  it('starts from the RHS sun classes on 21 June and the reach 1.2 / 0.6 m', () => {
    expect(thresholdsToFields(null)).toEqual({
      sun_class_thresholds: {
        full_sun_min_hours: 6,
        partial_shade_min_hours: 3,
        shade_min_hours: 2,
        reference_month: 6,
        reference_day: 21,
      },
      reach_thresholds: { both_sides_m: 1.2, one_side_m: 0.6 },
    });
  });

  it('accepts the defaults and other descending bounds', async () => {
    const resolver = buildSiteResolver(identityT);
    expect((await runResolver(resolver, baseForm)).errors).toEqual({});
    expect(
      (await runResolver(resolver, sun({ full_sun_min_hours: 8, partial_shade_min_hours: 4, shade_min_hours: 1 })))
        .errors,
    ).toEqual({});
  });

  it.each([
    ['full_sun_min_hours', 0],
    ['partial_shade_min_hours', -1],
    ['shade_min_hours', 0],
  ] as const)('refuses %s = %s (bounds must be more than 0)', async (field, value) => {
    const result = await runResolver(buildSiteResolver(identityT), sun({ [field]: value }));
    expect(result.errors.sun_class_thresholds).toBeTruthy();
  });

  it('refuses bounds that are not strictly descending', async () => {
    const resolver = buildSiteResolver(identityT);
    const equal = await runResolver(resolver, sun({ partial_shade_min_hours: 6 }));
    expect(equal.errors.sun_class_thresholds?.partial_shade_min_hours?.message).toBe(
      'pages.sites.thresholds.partialBelowFull',
    );
    const inverted = await runResolver(resolver, sun({ shade_min_hours: 4 }));
    expect(inverted.errors.sun_class_thresholds?.shade_min_hours?.message).toBe(
      'pages.sites.thresholds.shadeBelowPartial',
    );
  });

  it('refuses a reference day that does not exist and takes 29 February', async () => {
    const resolver = buildSiteResolver(identityT);
    const result = await runResolver(resolver, sun({ reference_month: 2, reference_day: 30 }));
    expect(result.errors.sun_class_thresholds?.reference_day?.message).toBe('pages.sites.thresholds.noSuchDay');
    expect(isDayOfYear(2, 29)).toBe(true);
    expect(isDayOfYear(4, 31)).toBe(false);
  });

  it.each([
    [{ both_sides_m: 0 }],
    [{ one_side_m: -0.5 }],
  ])('refuses a reach of 0 or less: %o', async (patch) => {
    const result = await runResolver(buildSiteResolver(identityT), reach(patch));
    expect(result.errors.reach_thresholds).toBeTruthy();
  });

  it('refuses a one-side reach above the two-side reach', async () => {
    const result = await runResolver(buildSiteResolver(identityT), reach({ both_sides_m: 1, one_side_m: 1.1 }));
    expect(result.errors.reach_thresholds?.one_side_m?.message).toBe('pages.sites.thresholds.oneAboveBoth');
  });

  it('sends only the part that changed; an unchanged part keeps what is stored (null)', () => {
    const site = thresholdsToFields(null);
    expect(thresholdsToPayload(site, null)).toEqual({ sun_class_thresholds: null, reach_thresholds: null });
    const changed = { ...site, reach_thresholds: { both_sides_m: 1.5, one_side_m: 0.6 } };
    expect(thresholdsToPayload(changed, null)).toEqual({
      sun_class_thresholds: null,
      reach_thresholds: { both_sides_m: 1.5, one_side_m: 0.6 },
    });
  });
});
