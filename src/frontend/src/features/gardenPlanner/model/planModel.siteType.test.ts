/** The plan model carries the site type and its default grid (REQ-053 WP 10.8, GP-FR-182). */
import { describe, expect, it } from 'vitest';
import { planResponse } from '@/test/gardenPlanFixtures';
import { applyOperation } from './applyOperation';
import { normalizePlan } from './planModel';
import type { Geometry } from './types';

const ROOM: Geometry = { kind: 'rect', origin: [0, 0], width_m: 4, length_m: 3, rotation_deg: 0 };

describe('normalizePlan: site type and default grid', () => {
  it('takes the site type and the default grid of the response', () => {
    const model = normalizePlan(planResponse({ site_type: 'grow_tent', site_default_grid_m: 0.05, plan: null }));
    expect(model.siteType).toBe('grow_tent');
    expect(model.defaultGridM).toBe(0.05);
  });

  it('reads a response without them (a plan cached before WP 10.8) as an unknown type and no default', () => {
    const model = normalizePlan(planResponse());
    expect(model.siteType).toBeNull();
    expect(model.defaultGridM).toBeUndefined();
  });
});

describe('applyOperation set_boundary on a plan that does not exist yet', () => {
  it('starts an indoor plan on the 5 cm grid of its site type, as the server stores it', () => {
    const plan = normalizePlan(planResponse({ site_type: 'indoor', site_default_grid_m: 0.05, plan: null }));
    const { plan: next } = applyOperation(plan, { op: 'set_boundary', boundary: ROOM });
    expect(next.settings?.default_grid_m).toBe(0.05);
  });

  it('starts a garden plan on 10 cm, as before', () => {
    const plan = normalizePlan(planResponse({ site_type: 'outdoor', site_default_grid_m: 0.1, plan: null }));
    const { plan: next } = applyOperation(plan, { op: 'set_boundary', boundary: ROOM });
    expect(next.settings?.default_grid_m).toBe(0.1);
  });

  it('keeps a stored grid: the default is for a new plan only', () => {
    const plan = normalizePlan(planResponse({ site_type: 'indoor', site_default_grid_m: 0.05 }));
    const { plan: next } = applyOperation(plan, { op: 'set_boundary', boundary: ROOM });
    expect(next.settings?.default_grid_m).toBe(0.1);
  });
});
