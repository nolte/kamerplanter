import { describe, it, expect } from 'vitest';
import {
  PHASE_KEYS,
  PHASE_PROFILES,
  PPFD_PRESETS,
  GDD_BASE_TEMP_PRESETS,
  SPACING_PRESETS,
} from '@/pages/pflanzen/calculations/phasePresets';
import { DEFAULT_TIMEZONE, getTimezoneOptions } from '@/pages/pflanzen/calculations/timezones';

describe('calculations presets', () => {
  it('defines a profile for every phase key', () => {
    for (const key of PHASE_KEYS) {
      const profile = PHASE_PROFILES[key];
      expect(profile.vpdMin).toBeLessThanOrEqual(profile.vpdMax);
      expect(profile.ppfd).toBeGreaterThan(0);
      expect(profile.photoperiodHours).toBeGreaterThan(0);
    }
  });

  it('mirrors the backend flowering reference band', () => {
    expect(PHASE_PROFILES.flowering).toEqual({
      vpdMin: 1.0,
      vpdMax: 1.5,
      ppfd: 600,
      photoperiodHours: 12,
    });
  });

  it('exposes discrete PPFD and spacing presets', () => {
    expect(PPFD_PRESETS).toContain(400);
    expect(SPACING_PRESETS).toContain(30);
    expect(GDD_BASE_TEMP_PRESETS.map((p) => p.key)).toContain('tomato');
  });
});

describe('getTimezoneOptions', () => {
  it('always includes the default zone', () => {
    const zones = getTimezoneOptions();
    expect(zones).toContain(DEFAULT_TIMEZONE);
    expect(zones.length).toBeGreaterThan(0);
  });

  it('returns only non-empty IANA-style strings', () => {
    const zones = getTimezoneOptions();
    expect(zones.every((z) => typeof z === 'string' && z.length > 0)).toBe(true);
    expect(zones.length).toBeGreaterThan(1);
  });

  it('falls back to the curated list when the Intl API is unavailable', () => {
    const intl = Intl as unknown as { supportedValuesOf?: unknown };
    const original = intl.supportedValuesOf;
    try {
      delete intl.supportedValuesOf;
      const zones = getTimezoneOptions();
      expect(zones).toContain('UTC');
      expect(zones).toContain(DEFAULT_TIMEZONE);
    } finally {
      intl.supportedValuesOf = original;
    }
  });

  it('falls back and still guarantees the default when the Intl API throws', () => {
    const intl = Intl as unknown as { supportedValuesOf?: unknown };
    const original = intl.supportedValuesOf;
    try {
      intl.supportedValuesOf = () => {
        throw new Error('unsupported');
      };
      const zones = getTimezoneOptions();
      expect(zones).toContain('UTC');
      expect(zones).toContain(DEFAULT_TIMEZONE);
    } finally {
      intl.supportedValuesOf = original;
    }
  });
});
