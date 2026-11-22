/** Garden plan or indoor plan (REQ-053 §9.8, GP-FR-182, WP 10.8). */
import { describe, expect, it } from 'vitest';
import type { SiteType } from '@/api/types';
import { isIndoorPlanSite } from './siteKind';

describe('isIndoorPlanSite', () => {
  it.each<SiteType>(['indoor', 'windowsill', 'grow_tent'])('reads %s as an indoor plan', (type) => {
    expect(isIndoorPlanSite(type)).toBe(true);
  });

  it.each<SiteType>(['outdoor', 'greenhouse', 'balcony'])('reads %s as a garden plan', (type) => {
    expect(isIndoorPlanSite(type)).toBe(false);
  });

  it('reads an unknown type as a garden plan - the behaviour of a plan cached before the type was sent', () => {
    expect(isIndoorPlanSite(null)).toBe(false);
    expect(isIndoorPlanSite(undefined)).toBe(false);
  });
});
