/**
 * Editor comfort (REQ-053 wave 7, WP 7.10-7.13): the template picker and the standard sizes (GP-FR-043/044/045),
 * object snap with align / distribute (GP-FR-012, GP-FR-029, GP-FR-154), the mini-map and the auto-save option
 * (GP-UX-014, GP-UX-004) and multi-duplicate (GP-FR-025). The network is the mocked API module.
 */
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { planResponse } from '@/test/gardenPlanFixtures';
import * as api from '../api/gardenPlan';
import type { BedTemplate, Point } from '../model/types';
import { AUTO_SAVE_DELAY_MS } from './useAutoSave';
import { applyAction, setSelection } from '../state/gardenPlanSlice';
import { pointer, px, setupEditor, VIEWPORT } from './editorTestKit';

vi.mock('../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
  listBedTemplates: vi.fn(),
  createBedTemplate: vi.fn(),
  placeBedTemplate: vi.fn(),
}));
const listLocationTypes = vi.hoisted(() => vi.fn());
vi.mock('@/api/endpoints/sites', () => ({ listLocationTypes }));

const getGardenPlan = vi.mocked(api.getGardenPlan);
const applyPlanBatch = vi.mocked(api.applyPlanBatch);
const listBedTemplates = vi.mocked(api.listBedTemplates);
const createBedTemplate = vi.mocked(api.createBedTemplate);
const placeBedTemplate = vi.mocked(api.placeBedTemplate);

const template = (patch: Partial<BedTemplate>): BedTemplate => ({
  key: 'sys_bed_2x1',
  name: 'Bed 2 x 1 m',
  location_type_key: 'bed',
  default_geometry: { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 1, rotation_deg: 0 },
  height_m: null,
  recurring_task_templates: [],
  is_system: true,
  ...patch,
});
const CATALOGUE: BedTemplate[] = [
  template({}),
  template({
    key: 'sys_raised_bed_2x1x0_8',
    name: 'Raised bed 2 x 1 x 0.8 m',
    location_type_key: 'raised_bed',
    height_m: 0.8,
  }),
  template({ key: 'own_1', name: 'My herb bed', is_system: false }),
];

beforeEach(() => {
  vi.resetAllMocks();
  window.localStorage.clear();
  listBedTemplates.mockResolvedValue(CATALOGUE);
  listLocationTypes.mockResolvedValue([]);
});
afterEach(() => {
  vi.useRealTimers();
  cleanup();
});

type Harness = ReturnType<typeof setupEditor>;
const select = (t: Harness, ...keys: string[]) =>
  t.after(() => {
    act(() => {
      t.store.dispatch(setSelection(keys.map((key) => ({ entity: 'location' as const, key }))));
    });
  });
const originOf = (t: Harness, key: string): Point =>
  (t.state().plan!.locations[key].geometry as { origin: Point }).origin;

describe('object snap (GP-FR-012, GP-FR-154)', () => {
  it('lands a moved bed on the corner of another bed, not on the grid beside it', () => {
    const t = setupEditor();
    select(t, 'solo');
    // solo's corner (14,2) is dragged to (8.1, 5.1); the corner of b2 at (8,5) is within 10 px
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(15, 3)));
      fireEvent.pointerMove(t.canvas(), pointer(px(14, 5)));
      fireEvent.pointerMove(t.canvas(), pointer(px(9.1, 6.1)));
      fireEvent.pointerUp(t.canvas(), pointer(px(9.1, 6.1)));
    });
    expect(originOf(t, 'solo')).toEqual([8, 5]);
  });

  it('snaps the right edge of the moved bed to the left edge of another and marks the snapped corner', () => {
    const t = setupEditor();
    select(t, 'solo');
    // solo (14..16 x 2..4) dragged by (-10.1, 0.5): its right edge is 0.1 m (4 px) left of b2's left edge x = 6.
    // The pointer itself is beside b1's right edge (x = 5) - the old marker showed that, not the snap.
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(15, 3)));
      fireEvent.pointerMove(t.canvas(), pointer(px(14, 3.5)));
      fireEvent.pointerMove(t.canvas(), pointer(px(4.9, 3.5)));
    });
    const marker = screen.getByTestId('garden-plan-snap-marker');
    expect(marker).toHaveAttribute('data-kind', 'edge');
    const ring = marker.querySelector('circle')!;
    // the marker sits on the snapped source - solo's upper-right corner at (6, 4.5) - not on the pointer
    expect(Number(ring.getAttribute('cx'))).toBeCloseTo(6 * 40, 3);
    expect(Number(ring.getAttribute('cy'))).toBeCloseTo((20 - 4.5) * 40, 3);
    const guide = screen.getByTestId('garden-plan-snap-guide');
    expect([guide.getAttribute('x1'), guide.getAttribute('x2')]).toEqual(['240', '240']);
    t.after(() => fireEvent.pointerUp(t.canvas(), pointer(px(4.9, 3.5))));
    expect(originOf(t, 'solo')).toEqual([4, 2.5]);
  });

  it('hides the marker while Alt moves freely', () => {
    const t = setupEditor();
    select(t, 'solo');
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(15, 3)));
      fireEvent.pointerMove(t.canvas(), pointer(px(14, 3.5)));
      fireEvent.pointerMove(t.canvas(), pointer({ ...px(4.9, 3.5), altKey: true }));
    });
    expect(screen.queryByTestId('garden-plan-snap-marker')).toBeNull();
  });

  it('Alt keeps the exact value', () => {
    const t = setupEditor();
    select(t, 'solo');
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(15, 3)));
      fireEvent.pointerMove(t.canvas(), pointer(px(14, 5)));
      fireEvent.pointerMove(t.canvas(), pointer({ ...px(9.1, 6.1), altKey: true }));
      fireEvent.pointerUp(t.canvas(), pointer({ ...px(9.1, 6.1), altKey: true }));
    });
    expect(originOf(t, 'solo')[0]).toBeCloseTo(8.1, 2);
  });
});

describe('align and distribute (GP-FR-029, GP-FR-155)', () => {
  it('aligns two beds in ONE undo step and undo takes it back', () => {
    const t = setupEditor();
    select(t, 'b1', 'b2', 'solo');
    const pastBefore = t.state().past.length;
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-align-button')));
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-align-bottom')));
    // b1 (y 3) and b2 (y 3) are already at the bottom of the group? no: solo is at y 2
    expect(originOf(t, 'b1')[1]).toBe(2);
    expect(originOf(t, 'b2')[1]).toBe(2);
    expect(t.state().past).toHaveLength(pastBefore + 1);
    expect(
      t.state().past[t.state().past.length - 1].ops.every((op) => op.op === 'update_geometry'),
    ).toBe(true);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(originOf(t, 'b1')[1]).toBe(3);
    expect(t.state().past).toHaveLength(pastBefore);
  });

  it('does not count a locked bed: with one movable bed left there is nothing to align', () => {
    const t = setupEditor();
    select(t, 'solo', 'lock');
    expect(screen.getByTestId('garden-plan-align-button')).toBeDisabled();
    expect(originOf(t, 'lock')).toEqual([14, 8]);
  });

  it('says why it does not distribute beds that overlap along the axis, and changes nothing (#2536)', () => {
    const t = setupEditor();
    // b1 and b2 (y 3..5) and solo (y 2..4): 6 m of beds in a 3 m span would need a negative gap
    select(t, 'b1', 'b2', 'solo');
    const pastBefore = t.state().past.length;
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-align-button')));
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-distribute-vertical')));
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(
      /überlappen in dieser Richtung|overlap in this direction/,
    );
    expect(t.state().past).toHaveLength(pastBefore);
    expect(originOf(t, 'solo')).toEqual([14, 2]);
  });

  it('is disabled for a single selection and distribute needs three', () => {
    const t = setupEditor();
    select(t, 'solo');
    expect(screen.getByTestId('garden-plan-align-button')).toBeDisabled();
    select(t, 'solo', 'b1');
    expect(screen.getByTestId('garden-plan-align-button')).toBeEnabled();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-align-button')));
    expect(screen.getByTestId('garden-plan-distribute-horizontal')).toHaveAttribute(
      'aria-disabled',
      'true',
    );
  });
});

describe('mini-map (GP-UX-014, §9.6)', () => {
  // 160 px per metre in 400 x 400 px shows 2.5 x 2.5 m of the 20 x 20 m garden: far more than four viewports
  const ZOOMED = { originM: [4, 12] as Point, pxPerM: 160, widthPx: 400, heightPx: 400 };

  it('is not there while the garden fits the view', () => {
    setupEditor();
    expect(screen.queryByTestId('garden-plan-minimap')).toBeNull();
  });

  it('shows 120 x 120 px with the viewport rectangle once the site exceeds four viewports', () => {
    setupEditor({ viewport: ZOOMED });
    const map = screen.getByTestId('garden-plan-minimap');
    expect(map).toHaveStyle({ width: '120px', height: '120px' });
    expect(within(map).getByTestId('garden-plan-minimap-viewport')).toBeInTheDocument();
  });

  it('a click jumps: the view is panned so the clicked spot is centred', () => {
    const onPan = vi.fn();
    setupEditor({ viewport: ZOOMED, onPan });
    // jsdom has no layout: the box is at 0,0. Pixel (60, 60) is the middle of the 20 x 20 m extent -> (10, 10).
    fireEvent.click(screen.getByTestId('garden-plan-minimap'), { clientX: 60, clientY: 60 });
    expect(onPan).toHaveBeenCalledTimes(1);
    const [dx, dy] = onPan.mock.calls[0] as [number, number];
    // the view's middle is (5.25, 10.75): to (10, 10) the plan moves 4.75 m left and 0.75 m ... in pixels
    expect(dx).toBeCloseTo(-(10 - 5.25) * 160, 0);
    expect(dy).toBeCloseTo((10 - 10.75) * 160, 0);
  });

  it('does not start a gesture of the plan beneath it', () => {
    const t = setupEditor({ viewport: ZOOMED });
    fireEvent.pointerDown(
      screen.getByTestId('garden-plan-minimap'),
      pointer({ clientX: 60, clientY: 60 }),
    );
    expect(t.state().selection).toEqual([]);
  });
});

describe('auto-save (GP-UX-004, D-12)', () => {
  const edit = (t: Harness) =>
    t.after(() => {
      act(() => {
        t.store.dispatch(
          applyAction([{ op: 'set_locked', entity: 'location', key: 'solo', locked: true }], null),
        );
      });
    });

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false });
  });

  it('is off by default: an edit stays unsaved', async () => {
    const t = setupEditor();
    edit(t);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(AUTO_SAVE_DELAY_MS * 3);
    });
    expect(applyPlanBatch).not.toHaveBeenCalled();
  });

  it('saves two seconds after the last edit when the user switched it on, and remembers the choice', async () => {
    applyPlanBatch.mockResolvedValue({
      plan_revision: 8,
      key_map: {},
      updated: [],
      deleted: [],
      derived: {},
    });
    const t = setupEditor();
    fireEvent.click(screen.getByTestId('garden-plan-autosave'));
    expect(window.localStorage.getItem('kp_garden_plan_auto_save')).toBe('1');
    edit(t);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(AUTO_SAVE_DELAY_MS - 100);
    });
    expect(applyPlanBatch).not.toHaveBeenCalled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(200);
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
    expect(t.state().pending).toHaveLength(0);
  });

  it('waits for the quiet: every new edit restarts the two seconds', async () => {
    applyPlanBatch.mockResolvedValue({
      plan_revision: 8,
      key_map: {},
      updated: [],
      deleted: [],
      derived: {},
    });
    const t = setupEditor();
    fireEvent.click(screen.getByTestId('garden-plan-autosave'));
    edit(t);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });
    t.after(() => {
      act(() => {
        t.store.dispatch(
          applyAction([{ op: 'set_locked', entity: 'location', key: 'b1', locked: true }], null),
        );
      });
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });
    expect(applyPlanBatch).not.toHaveBeenCalled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
  });

  it('pauses on a 409 conflict and says so', async () => {
    applyPlanBatch.mockRejectedValue(
      new ApiError(
        {
          error_id: 'e1',
          error_code: 'plan.revision_conflict',
          message: 'changed',
          details: [{ current_revision: 9, changed_by: 'Sabine' } as never],
          timestamp: '',
          path: '/plan/batch',
          method: 'POST',
        },
        409,
      ),
    );
    const t = setupEditor();
    fireEvent.click(screen.getByTestId('garden-plan-autosave'));
    edit(t);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(AUTO_SAVE_DELAY_MS + 100);
    });
    t.after(() => undefined);
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
    expect(t.state().saveStatus).toBe('conflict');
    expect(screen.getByTestId('garden-plan-autosave-paused')).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(AUTO_SAVE_DELAY_MS * 5);
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
  });

  it('does not retry a refused save every two seconds', async () => {
    applyPlanBatch.mockRejectedValue(
      new ApiError(
        {
          error_id: 'e2',
          error_code: 'validation_error',
          message: 'refused',
          details: [{ op_index: 0, field: 'geometry', code: 'geometry.invalid' } as never],
          timestamp: '',
          path: '/plan/batch',
          method: 'POST',
        },
        422,
      ),
    );
    const t = setupEditor();
    fireEvent.click(screen.getByTestId('garden-plan-autosave'));
    edit(t);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(AUTO_SAVE_DELAY_MS * 4);
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
  });
});

describe('multi-duplicate (GP-FR-025, GP-NFR-017)', () => {
  const openDialog = (t: Harness) => {
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-overflow')));
    t.after(() =>
      fireEvent.click(
        screen.getByRole('menuitem', { name: /Duplicate several times|Mehrfach duplizieren/ }),
      ),
    );
  };
  const set = (id: string, value: string) =>
    fireEvent.change(screen.getByTestId(id), { target: { value } });

  it('makes the copies in one undo step, named by the scheme, without slots', async () => {
    const t = setupEditor();
    select(t, 'b1');
    const slotsBefore = Object.keys(t.state().plan!.slots).length;
    const pastBefore = t.state().past.length;
    openDialog(t);
    await screen.findByTestId('garden-plan-multi-dialog');
    set('garden-plan-multi-count', '2');
    set('garden-plan-multi-direction', 'up');
    set('garden-plan-multi-spacing', '0.5');
    set('garden-plan-multi-scheme', 'Plot {n}');
    expect(screen.getByTestId('garden-plan-multi-preview')).toHaveTextContent('Plot 1 … Plot 2');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-multi-submit')));
    const names = Object.values(t.state().plan!.locations).map((l) => l.name);
    expect(names).toEqual(expect.arrayContaining(['Plot 1', 'Plot 2']));
    expect(t.state().past).toHaveLength(pastBefore + 1);
    expect(Object.keys(t.state().plan!.slots)).toHaveLength(slotsBefore);
    expect(t.state().selection).toHaveLength(2);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(Object.values(t.state().plan!.locations).some((l) => l.name === 'Plot 1')).toBe(false);
  });

  it('explains a refusal inside the dialog and creates nothing', async () => {
    const t = setupEditor();
    select(t, 'solo');
    openDialog(t);
    await screen.findByTestId('garden-plan-multi-dialog');
    set('garden-plan-multi-count', '30');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-multi-submit')));
    expect(screen.getByTestId('garden-plan-multi-error')).toHaveTextContent(
      /ragt aus ihrem Bereich|sticks out of its area/,
    );
    expect(t.state().past).toHaveLength(0);
  });

  it('previews the numbers over all selected beds, and says so when only objects are selected', async () => {
    const t = setupEditor();
    select(t, 'b1', 'b2');
    openDialog(t);
    await screen.findByTestId('garden-plan-multi-dialog');
    set('garden-plan-multi-count', '3');
    set('garden-plan-multi-scheme', 'P {n}');
    expect(screen.getByTestId('garden-plan-multi-preview')).toHaveTextContent('P 1 … P 6');
    cleanup();
    const u = setupEditor();
    u.after(() => {
      act(() => {
        u.store.dispatch(setSelection([{ entity: 'garden_object', key: 't1' }]));
      });
    });
    openDialog(u);
    await screen.findByTestId('garden-plan-multi-dialog');
    expect(screen.queryByTestId('garden-plan-multi-preview')).toBeNull();
    expect(screen.getByTestId('garden-plan-multi-no-names')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const t = setupEditor();
    select(t, 'b1');
    openDialog(t);
    await expectNoA11yViolations(await screen.findByTestId('garden-plan-multi-dialog'), {
      minImpact: 'serious',
    });
  });
});

describe('bed templates (GP-FR-043/044/045)', () => {
  const openTool = async (t: Harness) => {
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-template')));
    await screen.findByTestId('garden-plan-template-panel');
    await waitFor(() => expect(screen.getByTestId('garden-plan-template-select')).toBeEnabled());
  };
  const pick = async (key: string) => {
    fireEvent.mouseDown(
      within(screen.getByTestId('garden-plan-template-panel')).getByRole('combobox'),
    );
    fireEvent.click(await screen.findByRole('option', { name: new RegExp(key) }));
  };

  it('places the picked template where the click lands, turned, and reloads the plan', async () => {
    placeBedTemplate.mockResolvedValue({
      plan_revision: 8,
      key_map: { template_bed: 'loc_new' },
      updated: [],
      deleted: [],
      derived: {},
    });
    getGardenPlan.mockResolvedValue(planResponse());
    const t = setupEditor();
    const revision = t.state().plan!.revision;
    await openTool(t);
    await pick('My herb bed');
    fireEvent.click(screen.getByTestId('garden-plan-template-rotate'));
    expect(screen.getByTestId('garden-plan-template-rotate')).toHaveTextContent('90');
    fireEvent.pointerMove(t.canvas(), pointer(px(4.04, 15.03)));
    expect(screen.getByTestId('garden-plan-template-ghost')).toBeInTheDocument();
    await act(async () => {
      fireEvent.pointerDown(t.canvas(), pointer(px(4.04, 15.03)));
      fireEvent.click(t.canvas(), pointer(px(4.04, 15.03)));
    });
    await waitFor(() => expect(placeBedTemplate).toHaveBeenCalledTimes(1));
    expect(placeBedTemplate).toHaveBeenCalledWith('site_1', {
      template_key: 'own_1',
      origin: [4, 15],
      rotation_deg: 90,
      expected_revision: revision,
    });
    await waitFor(() => expect(getGardenPlan).toHaveBeenCalled());
    // a pointer press with the tool on selects nothing
    expect(t.state().pending).toHaveLength(0);
  });

  it('saves unsaved edits first, and places nothing when that fails', async () => {
    applyPlanBatch.mockRejectedValue(new Error('offline'));
    const t = setupEditor();
    t.after(() => {
      act(() => {
        t.store.dispatch(
          applyAction([{ op: 'set_locked', entity: 'location', key: 'solo', locked: true }], null),
        );
      });
    });
    await openTool(t);
    await pick('My herb bed');
    await act(async () => {
      fireEvent.click(screen.getByTestId('garden-plan-template-place-center'));
    });
    await waitFor(() => expect(screen.getByTestId('garden-plan-notice')).toBeInTheDocument());
    expect(placeBedTemplate).not.toHaveBeenCalled();
  });

  it('Esc ends the template tool also from inside the panel', async () => {
    const t = setupEditor();
    await openTool(t);
    t.after(() =>
      fireEvent.keyDown(screen.getByTestId('garden-plan-template-rotate'), { key: 'Escape' }),
    );
    expect(screen.queryByTestId('garden-plan-template-panel')).toBeNull();
  });

  it('Esc and another tool end the template tool', async () => {
    const t = setupEditor();
    await openTool(t);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Escape' }));
    expect(screen.queryByTestId('garden-plan-template-panel')).toBeNull();
    await openTool(t);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-select')));
    expect(screen.queryByTestId('garden-plan-template-panel')).toBeNull();
  });

  it('"Save as template" sends the bed in the bed frame, with its type', async () => {
    createBedTemplate.mockResolvedValue(template({ key: 'own_2', is_system: false }));
    const t = setupEditor();
    select(t, 'b2');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-save-template-button')));
    const name = await screen.findByTestId('garden-plan-template-save-name');
    fireEvent.change(name, { target: { value: 'Two by two' } });
    await act(async () => {
      fireEvent.click(screen.getByTestId('garden-plan-template-save-submit'));
    });
    await waitFor(() => expect(createBedTemplate).toHaveBeenCalledTimes(1));
    expect(createBedTemplate).toHaveBeenCalledWith({
      name: 'Two by two',
      location_type_key: 'bed',
      default_geometry: { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 2, rotation_deg: 0 },
    });
    await waitFor(() => expect(screen.getByTestId('garden-plan-info')).toBeInTheDocument());
  });

  it('is only enabled with exactly one bed selected', () => {
    const t = setupEditor();
    expect(screen.getByTestId('garden-plan-save-template-button')).toBeDisabled();
    select(t, 'b1', 'b2');
    expect(screen.getByTestId('garden-plan-save-template-button')).toBeDisabled();
    select(t, 'b1');
    expect(screen.getByTestId('garden-plan-save-template-button')).toBeEnabled();
  });

  it('the standard-size choice of "add with dimensions" fills shape, size, bed type and height', async () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-with-dimensions')));
    const chip = await screen.findByTestId('garden-plan-add-standard-sys_raised_bed_2x1x0_8');
    fireEvent.click(chip);
    expect(screen.getByTestId('garden-plan-add-width')).toHaveValue('2');
    expect(screen.getByTestId('garden-plan-add-length')).toHaveValue('1');
    expect(screen.getByTestId('garden-plan-add-height')).toHaveValue('0.8');
    // own templates are not standard sizes
    expect(screen.queryByTestId('garden-plan-add-standard-own_1')).toBeNull();
    fireEvent.change(screen.getByTestId('garden-plan-add-x'), { target: { value: '14' } });
    fireEvent.change(screen.getByTestId('garden-plan-add-y'), { target: { value: '14' } });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-submit')));
    const [key] = t.selected();
    expect(t.state().plan!.locations[key]).toMatchObject({
      location_type_key: 'raised_bed',
      height_m: 0.8,
      geometry: { kind: 'rect', width_m: 2, length_m: 1 },
    });
  });

  it('has no accessibility violations (picker and standard sizes)', async () => {
    const t = setupEditor();
    await openTool(t);
    await expectNoA11yViolations(screen.getByTestId('garden-plan-template-panel'), {
      minImpact: 'serious',
    });
    cleanup();
    const u = setupEditor();
    u.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-with-dimensions')));
    await screen.findByTestId('garden-plan-add-standard-sys_bed_2x1');
    await expectNoA11yViolations(screen.getByTestId('garden-plan-add-dialog'), {
      minImpact: 'serious',
    });
  });
});

// keeps the unused viewport export referenced for readers of the zoom values above
void VIEWPORT;
