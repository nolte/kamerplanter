/**
 * The pure rules of field mode (REQ-053 WP 5.1): due and overdue on UTC calendar days (operator decision),
 * the order of "My beds · due today", the task sections of the sheet, the plant groups, the chips, the
 * tap-to-bed mapping and the device memory.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { bedListItem } from '../bed/bedTestKit';
import { careTask } from '../care/careTestKit';
import type { PlantStateWire } from '../planting/plantStateApi';
import { planModeHref, resolvePlanMode } from '../routes/planMode';
import { bedIsDue, fieldTaskSections, isDueBy, isOverdueOn, sortFieldBeds, todayUtc, utcDayOf } from './fieldDue';
import { MAX_PX_PER_M } from '../model/units';
import { bedOfKey, nearestBed, restoreFieldView } from './fieldMapLogic';
import { groupPlants } from './fieldPlants';
import {
  FIELD_PREFS_KEY,
  MAX_VIEWPORTS,
  readFieldPrefs,
  rememberFieldSite,
  rememberFieldViewport,
} from './fieldPrefs';
import { QUICK_CHIPS, quickLogBody } from './quickChips';

describe('due and overdue on UTC calendar days', () => {
  it('reads the UTC day of an instant and tolerates absent or broken values', () => {
    expect(utcDayOf('2026-06-18T23:30:00-02:00')).toBe('2026-06-19');
    expect(utcDayOf(null)).toBeNull();
    expect(utcDayOf('not a date')).toBeNull();
    expect(todayUtc(new Date('2026-06-18T23:59:00Z'))).toBe('2026-06-18');
  });

  it('calls a task overdue only when its due day lies before today, never by the time of day', () => {
    const today = '2026-06-18';
    expect(isOverdueOn('2026-06-17T23:59:59Z', today)).toBe(true);
    // Due earlier today is not overdue (the rule is not `due_date < now`).
    expect(isOverdueOn('2026-06-18T00:00:00Z', today)).toBe(false);
    expect(isOverdueOn('2026-06-18T23:00:00Z', today)).toBe(false);
    expect(isOverdueOn(null, today)).toBe(false);
    expect(isDueBy('2026-06-18T23:00:00Z', today)).toBe(true);
    expect(isDueBy('2026-06-19T00:00:00Z', today)).toBe(false);
  });

  it('splits the sheet tasks into overdue, today and later, by due day, without suggestions', () => {
    const sections = fieldTaskSections(
      [
        careTask('t_later', { due_date: '2026-06-25T00:00:00Z' }),
        careTask('t_none', { due_date: null }),
        careTask('t_today', { due_date: '2026-06-18T08:00:00Z' }),
        careTask('t_old', { due_date: '2026-06-01T00:00:00Z' }),
        careTask('t_older', { due_date: '2026-05-01T00:00:00Z' }),
        careTask('t_sug', { due_date: '2026-06-01T00:00:00Z', suggested: true }),
      ],
      '2026-06-18',
    );
    expect(sections.overdue.map((task) => task.key)).toEqual(['t_older', 't_old']);
    expect(sections.today.map((task) => task.key)).toEqual(['t_today']);
    expect(sections.later.map((task) => task.key)).toEqual(['t_later', 't_none']);
  });

  it('sorts the beds: mine first, then due ones, then most overdue, next due day and name; retired dropped', () => {
    const today = '2026-06-18';
    const beds = [
      bedListItem('b_far', { name: 'Zucchini', next_due_at: '2026-07-01T00:00:00Z' }),
      bedListItem('b_soon', { name: 'Beans', next_due_at: '2026-06-20T00:00:00Z' }),
      bedListItem('b_today', { name: 'Kale', next_due_at: '2026-06-18T10:00:00Z' }),
      bedListItem('b_over2', { name: 'Leek', overdue_task_count: 2 }),
      bedListItem('b_over1', { name: 'Herbs', overdue_task_count: 1 }),
      bedListItem('b_mine', { name: 'Allotment', next_due_at: null }),
      bedListItem('b_old', { name: 'Old', bed_status: 'retired', overdue_task_count: 9 }),
      bedListItem('b_none', { name: 'Carrots' }),
    ];
    const order = sortFieldBeds(beds, new Set(['b_mine']), today, 'en').map((bed) => bed.key);
    expect(order).toEqual(['b_mine', 'b_over2', 'b_over1', 'b_today', 'b_soon', 'b_far', 'b_none']);
    expect(bedIsDue(beds[2], today)).toBe(true);
    expect(bedIsDue(beds[1], today)).toBe(false);
  });
});

describe('plant groups of the sheet', () => {
  const plant = (key: string, overrides: Partial<PlantStateWire> = {}): PlantStateWire => ({
    plant_key: key,
    slot_key: `slot_${key}`,
    instance_id: key.toUpperCase(),
    species_key: 'sp_tomato',
    species_name: 'Tomato',
    planted_on: '2026-05-01',
    lifecycle: 'active',
    phase: { key: 'ph_flower', name: 'Flowering', elapsed_d: 10 },
    last_care: {},
    attention: [],
    harvest: { ready: false },
    inputs: { open_tasks: [], open_findings: 0, frost_risk: false, harvest_batches: 0 },
    ...overrides,
  });

  it('groups by species, cultivar and phase, the largest group first', () => {
    const groups = groupPlants(
      [
        plant('t2'),
        plant('b1', { species_key: 'sp_basil', species_name: 'Basil', phase: null }),
        plant('t1'),
        plant('t3', { phase: { key: 'ph_veg', name: 'Vegetative', elapsed_d: 3 } }),
        plant('t4', { cultivar_name: 'Roma' }),
      ],
      'en',
    );
    expect(groups.map((group) => [group.species, group.cultivar, group.phaseName, group.plants.length])).toEqual([
      ['Tomato', null, 'Flowering', 2],
      ['Basil', null, null, 1],
      ['Tomato', null, 'Vegetative', 1],
      ['Tomato', 'Roma', 'Flowering', 1],
    ]);
    expect(groups[0].plants.map((entry) => entry.instance_id)).toEqual(['T1', 'T2']);
    expect(groups[0].id).toBe('sp-tomato--none--ph-flower');
  });

  it('falls back to the scientific name and the key when the species has no name', () => {
    const [first, second] = groupPlants(
      [
        plant('x1', { species_key: 'sp_x', species_name: null, scientific_name: 'Allium cepa' }),
        plant('y1', { species_key: 'sp_y', species_name: null, scientific_name: null }),
      ],
      'en',
    );
    expect(first.species).toBe('Allium cepa');
    expect(second.species).toBe('sp_y');
  });
});

describe('quick protocol chips', () => {
  it('offers the six chips of the spec in order, three as one tap', () => {
    expect(QUICK_CHIPS.map((chip) => chip.id)).toEqual(['watering', 'harvest', 'sowing', 'weeding', 'planted', 'note']);
    expect(QUICK_CHIPS.filter((chip) => chip.action === 'log').map((chip) => chip.category)).toEqual([
      'watering',
      'sowing',
      'weeding',
    ]);
  });

  it('builds a manual care event body without client-side trigger', () => {
    const body = quickLogBody('loc_1', 'weeding', 'Weeding'.repeat(100), new Date('2026-06-18T07:00:00Z'));
    expect(body).toEqual({
      location_key: 'loc_1',
      category: 'weeding',
      summary: 'Weeding'.repeat(100).slice(0, 500),
      performed_at: '2026-06-18T07:00:00.000Z',
    });
    expect(body).not.toHaveProperty('trigger');
  });
});

describe('which bed a map tap means', () => {
  const plan = smallPlan();
  const beds = new Set(['loc_a', 'loc_b']);

  it('maps a bed, its plant and its slot to the bed, and ignores other objects', () => {
    expect(bedOfKey(plan, 'loc_a', beds)).toBe('loc_a');
    expect(bedOfKey(plan, 'pl_1', beds)).toBe('loc_a');
    expect(bedOfKey(plan, 'slot_1', beds)).toBe('loc_a');
    expect(bedOfKey(plan, 'go_1', beds)).toBeNull();
    expect(bedOfKey(plan, 'loc_a', new Set(['loc_b']))).toBeNull();
  });

  it('finds the closest bed within the tolerance only', () => {
    // loc_a spans x 1…2.2, loc_b x 4…5.2 (both y 1…3).
    expect(nearestBed(plan, beds, [2.3, 2], 0.2)).toBe('loc_a');
    expect(nearestBed(plan, beds, [3.9, 2], 0.2)).toBe('loc_b');
    expect(nearestBed(plan, beds, [3.1, 2], 0.2)).toBeNull();
  });
});

describe('restoring a remembered map view', () => {
  // Plan 0…10 × 0…5 m on a 400 × 200 px canvas; the fit zoom is 40 px/m.
  const bounds: [number, number, number, number] = [0, 0, 10, 5];

  it('keeps a view that shows the plan and clamps its zoom', () => {
    expect(restoreFieldView({ pxPerM: 80, originM: [2, 4] }, bounds, 400, 200, 40)).toEqual({
      pxPerM: 80,
      originM: [2, 4],
    });
    expect(restoreFieldView({ pxPerM: 10, originM: [0, 5] }, bounds, 400, 200, 40)?.pxPerM).toBe(40);
    expect(restoreFieldView({ pxPerM: 1e6, originM: [2, 4] }, bounds, 400, 200, 40)?.pxPerM).toBe(MAX_PX_PER_M);
  });

  it('drops a view that misses the plan or shows only a sliver of it', () => {
    expect(restoreFieldView(null, bounds, 400, 200, 40)).toBeNull();
    // Entirely beside the plan.
    expect(restoreFieldView({ pxPerM: 80, originM: [50, 4] }, bounds, 400, 200, 40)).toBeNull();
    // 5 m × 2.5 m visible, only 0.5 m × 2.5 m of it is plan: under a quarter.
    expect(restoreFieldView({ pxPerM: 80, originM: [9.5, 4] }, bounds, 400, 200, 40)).toBeNull();
    // A canvas without size (not measured yet) restores nothing.
    expect(restoreFieldView({ pxPerM: 80, originM: [2, 4] }, bounds, 0, 200, 40)).toBeNull();
    expect(restoreFieldView({ pxPerM: Number.NaN, originM: [2, 4] }, bounds, 400, 200, 40)).toBeNull();
  });
});

describe('plan mode', () => {
  it('opens field mode by default on xs and lets the parameter decide everywhere', () => {
    expect(resolvePlanMode(null, true)).toBe('field');
    expect(resolvePlanMode(null, false)).toBe('plan');
    expect(resolvePlanMode('field', false)).toBe('field');
    expect(resolvePlanMode('plan', true)).toBe('plan');
    expect(resolvePlanMode('other', true)).toBe('field');
  });

  it('keeps the other query parameters when switching', () => {
    expect(planModeHref('/standorte/sites/s1/plan', new URLSearchParams('year=2026&mode=field'), 'plan')).toBe(
      '/standorte/sites/s1/plan?year=2026&mode=plan',
    );
  });
});

describe('field memory per device', () => {
  afterEach(() => localStorage.clear());
  const context = { userKey: 'user-1', tenantSlug: 'garden', siteKey: 'site_1' };

  it('remembers site, tab and view for the same account and forgets them for another', () => {
    rememberFieldSite({ ...context, tab: 'map' });
    rememberFieldViewport(context, { pxPerM: 40, originM: [1, 2] });
    expect(readFieldPrefs('user-1')).toEqual({
      ...context,
      tab: 'map',
      viewports: { site_1: { pxPerM: 40, originM: [1, 2] } },
    });
    expect(readFieldPrefs('user-2')).toBeNull();
    expect(readFieldPrefs(null)).toBeNull();
  });

  it('starts fresh in another tenant and with the list on another site', () => {
    rememberFieldSite({ ...context, tab: 'map' });
    rememberFieldViewport(context, { pxPerM: 40, originM: [1, 2] });
    rememberFieldSite({ ...context, siteKey: 'site_2' });
    expect(readFieldPrefs('user-1')).toMatchObject({ siteKey: 'site_2', tab: 'list', viewports: { site_1: {} } });
    rememberFieldSite({ ...context, tenantSlug: 'other' });
    expect(readFieldPrefs('user-1')).toMatchObject({ tenantSlug: 'other', viewports: {} });
  });

  it('keeps at most the newest views and drops unreadable entries', () => {
    for (let index = 0; index < MAX_VIEWPORTS + 5; index += 1) {
      rememberFieldViewport({ ...context, siteKey: `s${index}` }, { pxPerM: 10 + index, originM: [0, 0] });
    }
    const views = readFieldPrefs('user-1')?.viewports ?? {};
    expect(Object.keys(views)).toHaveLength(MAX_VIEWPORTS);
    expect(views.s0).toBeUndefined();
    expect(views[`s${MAX_VIEWPORTS + 4}`]).toBeDefined();

    localStorage.setItem(
      FIELD_PREFS_KEY,
      JSON.stringify({ ...context, tab: 'x', viewports: { a: { pxPerM: -1, originM: [0, 0] }, b: { pxPerM: 2, originM: [1] } } }),
    );
    expect(readFieldPrefs('user-1')).toEqual({ ...context, tab: 'list', viewports: {} });
    localStorage.setItem(FIELD_PREFS_KEY, '{broken');
    expect(readFieldPrefs('user-1')).toBeNull();
  });
});
