/**
 * What an area offers once it is selected (REQ-053 §9.5, GP-UX-071, #2913): the properties panel, the context menu and
 * the selection group in the rail. An area is no bed - no bed axis, zone/watering line, sun of its own, "Plant it" or
 * "Save as template" - but it keeps name, type, size, lock, duplicate, order, delete and "Open details"; rotate and
 * align work on it as on any shape. The delete confirmation says truthfully what goes and what stays.
 */
import { act, cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PlanModel } from '../model/planModel';
import type { Point } from '../model/types';
import { setSelection } from '../state/gardenPlanSlice';
import { testPlan } from './tools/toolTestKit';
import { pointer, px, setupEditor, typeAndBlur } from './editorTestKit';

vi.mock('@/api/endpoints/sites', () => ({
  listLocationTypes: () => Promise.resolve([]),
  getSite: () => Promise.reject(new Error('the site is not read in this test')),
}));

afterEach(() => cleanup());

/**
 * The tool test plan with its `area` (2,2)-(12,12) marked an area - holding b1, b2 and the tree t1 - and a second
 * area `yard` (13,11)-(19,16), not square (a bed of that shape has a long axis). `solo` (14,2) and `lock` (14,8) stay beds.
 */
function areaPlan(): PlanModel {
  const plan = testPlan();
  const yard = {
    ...plan.locations.area,
    key: 'yard',
    name: 'Yard',
    geometry: { kind: 'rect' as const, origin: [13, 11] as Point, width_m: 6, length_m: 5, rotation_deg: 0 },
    bbox: [13, 11, 19, 16] as [number, number, number, number],
    area_m2: 30,
    open_task_count: 0,
  };
  return {
    ...plan,
    areaTypeKeys: ['area'],
    locations: { ...plan.locations, area: { ...plan.locations.area, is_area: true }, yard: { ...yard, is_area: true } },
  };
}

type Harness = ReturnType<typeof setupEditor>;
const select = (t: Harness, ...keys: string[]) =>
  t.after(() => {
    act(() => {
      t.store.dispatch(setSelection(keys.map((key) => ({ entity: 'location' as const, key }))));
    });
  });
const originOf = (t: Harness, key: string): Point =>
  (t.state().plan!.locations[key].geometry as { origin: Point }).origin;
const rightClick = (t: Harness, x: number, y: number) =>
  t.after(() => {
    fireEvent.pointerDown(t.canvas(), pointer({ ...px(x, y), button: 2 }));
    return fireEvent.contextMenu(t.canvas(), { ...px(x, y) });
  });

describe('the properties panel of an area', () => {
  it('keeps name, type, size, lock, duplicate, order, delete and details, and drops the bed-only rows', () => {
    const t = setupEditor({ plan: areaPlan(), onOpenLocation: vi.fn() });
    // `yard` is empty: as a bed it would offer "Plant it".
    select(t, 'yard');
    for (const id of [
      'garden-plan-panel-name',
      'garden-plan-panel-type',
      'garden-plan-panel-geometry',
      'garden-plan-panel-locked-switch',
      'garden-plan-panel-duplicate',
      'garden-plan-panel-front',
      'garden-plan-panel-back',
      'garden-plan-panel-delete',
      'garden-plan-panel-details',
    ]) {
      expect(screen.getByTestId(id)).toBeInTheDocument();
    }
    for (const id of [
      'garden-plan-panel-bed-axis',
      'garden-plan-panel-sun',
      'garden-plan-panel-empty-bed',
      'garden-plan-panel-plant',
    ]) {
      expect(screen.queryByTestId(id)).toBeNull();
    }
  });

  it('still shows the bed rows for a bed (the control)', () => {
    const t = setupEditor({ plan: areaPlan(), onOpenLocation: vi.fn() });
    select(t, 'solo');
    expect(screen.getByTestId('garden-plan-panel-sun')).toBeInTheDocument();
  });

  it('turns an area by its rotation field, in one undo step', () => {
    const t = setupEditor({ plan: areaPlan() });
    select(t, 'yard');
    const before = t.state().past.length;
    t.after(() => typeAndBlur(screen.getByTestId('garden-plan-panel-field-rotation'), '90'));
    expect(t.state().plan!.locations.yard.geometry).toMatchObject({ rotation_deg: 90 });
    expect(t.state().past).toHaveLength(before + 1);
    expect(screen.queryByTestId('garden-plan-notice')).toBeNull();
  });
});

describe('the context menu and the rail for an area', () => {
  it('offers no "Plant it" and no "Save as template", but edit, duplicate, order, lock and delete', () => {
    const t = setupEditor({ plan: areaPlan(), onOpenLocation: vi.fn() });
    rightClick(t, 16, 15);
    expect(t.selected()).toEqual(['yard']);
    const menu = screen.getByRole('menu', { name: 'Actions for the selection' });
    for (const name of ['Edit', 'Duplicate', 'Bring to front', 'Send to back', 'Lock', 'Delete']) {
      expect(within(menu).getByRole('menuitem', { name })).toBeInTheDocument();
    }
    expect(within(menu).queryByRole('menuitem', { name: 'Plant it' })).toBeNull();
    expect(within(menu).queryByTestId('garden-plan-menu-saveTemplate')).toBeNull();
  });

  it('a bed keeps "Plant it" in its menu (the control)', () => {
    const t = setupEditor({ plan: areaPlan(), onOpenLocation: vi.fn() });
    rightClick(t, 15, 3);
    expect(t.selected()).toEqual(['solo']);
    expect(screen.getByRole('menuitem', { name: 'Plant it' })).toBeInTheDocument();
  });

  it('aligns two areas like any two shapes: one undo step, the area moves', () => {
    const t = setupEditor({ plan: areaPlan() });
    select(t, 'area', 'yard');
    const before = t.state().past.length;
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-align-button')));
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-align-top')));
    // area's top edge is y 12, yard's y 16: aligned to the top, area moves up by 4 (still inside the 20 m boundary).
    expect(originOf(t, 'area')[1]).toBe(6);
    expect(t.state().past).toHaveLength(before + 1);
  });
});

describe('deleting an area says what goes and what stays', () => {
  it('lists the children it deletes and that standing plants make the save refuse it', async () => {
    const t = setupEditor({ plan: areaPlan() });
    select(t, 'area');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-delete-button')));
    const text = (await screen.findByTestId('confirm-dialog')).textContent ?? '';
    expect(text).toContain('This also deletes:');
    expect(text).toContain('2 contained beds');
    // b1 holds a standing plant: the server deletes nothing with a plant in it (V-09) - not "also deleted".
    expect(text).toContain('1 plant still stands in it. As long as it does, saving refuses this deletion');
    expect(text).not.toMatch(/•\s*1 plant/);
  });

  it('names the beds that lay inside before the area was drawn: they stay on the plan', async () => {
    const plan = areaPlan();
    // A bed in the yard that is no child of it (drawn before the yard).
    const before = {
      ...plan.locations.solo,
      key: 'before',
      name: 'Before',
      geometry: { kind: 'rect' as const, origin: [14, 12] as Point, width_m: 2, length_m: 2, rotation_deg: 0 },
      bbox: [14, 12, 16, 14] as [number, number, number, number],
    };
    const t = setupEditor({ plan: { ...plan, locations: { ...plan.locations, before } } });
    select(t, 'yard');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-delete-button')));
    const dialog = await screen.findByTestId('confirm-dialog');
    const text = dialog.textContent ?? '';
    expect(text).toContain('Not deleted: 1 bed or object that lay inside before the area was drawn');
    // Not the claim that nothing lies inside.
    expect(text).not.toContain('It contains no further beds');
    t.after(() => fireEvent.click(within(dialog).getByTestId('confirm-dialog-confirm')));
    expect(t.state().plan!.locations.yard).toBeUndefined();
    expect(t.state().plan!.locations.before).toBeDefined();
  });
});
