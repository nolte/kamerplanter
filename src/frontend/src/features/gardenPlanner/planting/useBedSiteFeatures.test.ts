import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useBedSiteFeatures } from './useBedSiteFeatures';

describe('useBedSiteFeatures', () => {
  it('reads frost risk, wind and drainage from the bed document', () => {
    const { result } = renderHook(() =>
      useBedSiteFeatures({
        site_conditions: { microclimate: { frost_risk: 'high' }, wind_exposure: 'exposed' },
        soil_profile: { drainage: 'poor' },
      }),
    );
    expect(result.current).toStrictEqual({ frostRisk: 'high', windExposure: 'exposed', drainage: 'poor' });
  });

  it('answers undefined for what is not recorded and keeps the object stable across renders', () => {
    const bed = { site_conditions: null, soil_profile: null };
    const { result, rerender } = renderHook(() => useBedSiteFeatures(bed));
    const first = result.current;
    rerender();
    expect(first).toStrictEqual({ frostRisk: undefined, windExposure: undefined, drainage: undefined });
    expect(result.current).toBe(first);
  });
});
