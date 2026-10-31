/**
 * Save bar, conflict dialog, undo/redo UI (REQ-053 WP 2.8): GP-ACC-007 (undo and redo of a move,
 * status "0"), GP-ACC-011 (the 409 dialog, reload empties the undo stack), GP-FR-026 / GP-FR-155
 * (stack kept after a save, shortcuts, tooltip names the action), GP-UX-017 (a refusal is
 * explained per operation). The network is the mocked API module; nothing here waits on a clock.
 */
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { normalizePlan } from '../model/planModel';
import { planResponse, bed } from '@/test/gardenPlanFixtures';
import type { Geometry, PlanBatchResponse, PlanOperation } from '../model/types';
import * as api from '../api/gardenPlan';
import { applyAction } from '../state/gardenPlanSlice';
import { setupEditor } from './editorTestKit';

vi.mock('../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
}));

const getGardenPlan = vi.mocked(api.getGardenPlan);
const applyPlanBatch = vi.mocked(api.applyPlanBatch);

const MOVE_LABEL = 'pages.gardenPlan.editor.actions.move';

const rect = (x: number): Geometry => ({
  kind: 'rect',
  origin: [x, 3],
  width_m: 2,
  length_m: 2,
  rotation_deg: 0,
});
const move = (key: string, x: number): PlanOperation => ({
  op: 'update_geometry',
  entity: 'location',
  key,
  geometry: rect(x),
});

function plan() {
  return normalizePlan(
    planResponse({ locations: [bed('b1', 3, 3), bed('b2', 8, 3)], slots: [], plants: [] }),
  );
}

function ok(extra: Partial<PlanBatchResponse> = {}): PlanBatchResponse {
  return { plan_revision: 43, key_map: {}, updated: [], deleted: [], derived: {}, ...extra };
}

function apiError(status: number, code: string, details: Record<string, unknown>[]): ApiError {
  return new ApiError(
    {
      error_id: 'e1',
      error_code: code,
      message: code,
      details: details as never,
      timestamp: '',
      path: '/plan/batch',
      method: 'POST',
    },
    status,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});
afterEach(() => cleanup());

type Harness = ReturnType<typeof setupEditor>;

/** One user action on the bed `b1`, as the editor tools commit it. */
function moveBed(t: Harness, x: number): void {
  t.after(() => {
    act(() => {
      t.store.dispatch(applyAction([move('b1', x)], MOVE_LABEL));
    });
  });
}

const status = () => screen.getByTestId('garden-plan-save-status');
const originOf = (t: Harness, key: string) => {
  const geometry = t.state().plan?.locations[key].geometry;
  return geometry?.kind === 'rect' ? geometry.origin[0] : undefined;
};

async function clickSave(t: Harness) {
  await act(async () => {
    fireEvent.click(screen.getByTestId('garden-plan-save'));
  });
  t.rerender();
}

describe('save status (GP-NFR-005)', () => {
  it('starts as saved with nothing to save, then counts the unsaved changes', () => {
    const t = setupEditor({ plan: plan() });
    expect(status()).toHaveTextContent('Saved');
    expect(screen.getByTestId('garden-plan-save')).toBeDisabled();
    moveBed(t, 4);
    expect(status()).toHaveTextContent('Unsaved changes (1)');
    expect(screen.getByTestId('garden-plan-save')).toBeEnabled();
    moveBed(t, 5);
    expect(status()).toHaveTextContent('Unsaved changes (2)');
  });
});

describe('undo and redo (GP-ACC-007, GP-FR-026, GP-FR-155)', () => {
  it('Ctrl+Z puts the bed back and the status shows no pending change; Ctrl+Shift+Z redoes the move', () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    expect(originOf(t, 'b1')).toBe(4);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'z', ctrlKey: true }));
    expect(originOf(t, 'b1')).toBe(3);
    expect(status()).toHaveAttribute('data-pending-count', '0');
    expect(status()).toHaveTextContent('Saved');
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Z', ctrlKey: true, shiftKey: true }));
    expect(originOf(t, 'b1')).toBe(4);
    expect(status()).toHaveTextContent('Unsaved changes (1)');
  });

  it('Ctrl+Y and Cmd+Z work as well', () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'z', metaKey: true }));
    expect(originOf(t, 'b1')).toBe(3);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'y', ctrlKey: true }));
    expect(originOf(t, 'b1')).toBe(4);
  });

  it('leaves Ctrl+Z to a text field inside the editor', () => {
    const t = setupEditor({ plan: plan() });
    t.click(4, 4); // selects b1, the panel shows its fields
    moveBed(t, 4);
    const field = screen.getByTestId('garden-plan-panel-name');
    t.after(() => fireEvent.keyDown(field, { key: 'z', ctrlKey: true }));
    expect(originOf(t, 'b1')).toBe(4);
    expect(t.state().past).toHaveLength(1);
  });

  it('the buttons are real buttons whose label names the action (tooltip on sm/xs, too)', () => {
    const t = setupEditor({ plan: plan() });
    const undoButton = screen.getByTestId('garden-plan-undo');
    const redoButton = screen.getByTestId('garden-plan-redo');
    expect(undoButton).toBeDisabled();
    expect(redoButton).toBeDisabled();
    moveBed(t, 4);
    expect(undoButton).toBeEnabled();
    expect(undoButton).toHaveAccessibleName('Undo: Move (Ctrl+Z)');
    t.after(() => fireEvent.click(undoButton));
    expect(originOf(t, 'b1')).toBe(3);
    expect(redoButton).toHaveAccessibleName('Redo: Move (Ctrl+Shift+Z)');
    t.after(() => fireEvent.click(redoButton));
    expect(originOf(t, 'b1')).toBe(4);
  });

  it('one action is one step: two moves need two undos', () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    moveBed(t, 5);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(originOf(t, 'b1')).toBe(4);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(originOf(t, 'b1')).toBe(3);
  });

  it('keeps the stack after a save; undo then makes the plan dirty again', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    applyPlanBatch.mockResolvedValue(ok());
    await clickSave(t);
    expect(status()).toHaveTextContent('Saved');
    expect(t.state().plan?.revision).toBe(43);
    expect(screen.getByTestId('garden-plan-undo')).toBeEnabled();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(originOf(t, 'b1')).toBe(3);
    expect(status()).toHaveTextContent('Unsaved changes (1)');
  });

  it('undoes a saved sun-window edit with the counter-operation and redoes it (#2538)', async () => {
    const t = setupEditor({ plan: plan() });
    const edit: PlanOperation = {
      op: 'update_fields',
      entity: 'location',
      key: 'b1',
      fields: { site_conditions: { sun_profile: { sun_window: 'morning' } } },
    };
    t.after(() => {
      act(() => {
        t.store.dispatch(applyAction([edit], 'pages.gardenPlan.editor.actions.edit'));
      });
    });
    applyPlanBatch.mockResolvedValue(ok({ updated: ['b1'] }));
    await clickSave(t);
    expect(applyPlanBatch.mock.calls[0][1]).toMatchObject({ operations: [edit] });

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(t.state().plan?.locations.b1.site_conditions).toBeUndefined();
    expect(t.state().pending.map((item) => item.op)).toEqual([
      {
        op: 'update_fields',
        entity: 'location',
        key: 'b1',
        fields: { site_conditions: { sun_profile: { sun_window: 'unknown' } } },
      },
    ]);

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-redo')));
    expect(t.state().plan?.locations.b1.site_conditions).toEqual({ sun_profile: { sun_window: 'morning' } });
    // The saved edit is not in the pending queue any more: the redo queues it again after the inverse.
    expect(t.state().pending.map((item) => item.op)).toEqual([
      {
        op: 'update_fields',
        entity: 'location',
        key: 'b1',
        fields: { site_conditions: { sun_profile: { sun_window: 'unknown' } } },
      },
      edit,
    ]);
  });

  it('says so when a saved step cannot be undone (deleting a bed with plants)', async () => {
    const withPlants = normalizePlan(planResponse());
    const t = setupEditor({ plan: withPlants });
    t.after(() => {
      act(() => {
        t.store.dispatch(
          applyAction([{ op: 'delete', entity: 'location', key: 'loc_a' }], 'pages.gardenPlan.editor.actions.delete'),
        );
      });
    });
    applyPlanBatch.mockResolvedValue(ok());
    await clickSave(t);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(
      'This cannot be undone after saving.',
    );
    expect(t.state().pending).toHaveLength(0);
  });
});

describe('saving (GP-NFR-006)', () => {
  it('sends pending with the expected revision and locks the bar while the request runs', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    let resolve: (value: PlanBatchResponse) => void = () => undefined;
    applyPlanBatch.mockReturnValue(new Promise((r) => (resolve = r)));
    act(() => {
      fireEvent.click(screen.getByTestId('garden-plan-save'));
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
    expect(applyPlanBatch.mock.calls[0][1].expected_revision).toBe(42);
    expect(applyPlanBatch.mock.calls[0][1].operations).toHaveLength(1);
    expect(status()).toHaveTextContent('Saving');
    expect(screen.getByTestId('garden-plan-save')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-undo')).toBeDisabled();
    await act(async () => resolve(ok()));
    expect(status()).toHaveTextContent('Saved');
  });

  it('Ctrl+S saves and keeps the browser from opening its own save dialog', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    applyPlanBatch.mockResolvedValue(ok());
    let notPrevented = true;
    await act(async () => {
      notPrevented = fireEvent.keyDown(t.canvas(), { key: 's', ctrlKey: true });
    });
    expect(notPrevented).toBe(false);
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
  });

  it('Ctrl+Z, Ctrl+Y and Ctrl+S stay active with the single-key shortcuts switched off (WCAG 2.1.4)', async () => {
    window.localStorage.setItem('kamerplanter.gardenPlan.singleKeyShortcuts', 'off');
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'z', ctrlKey: true }));
    expect(originOf(t, 'b1')).toBe(3);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'y', ctrlKey: true }));
    expect(originOf(t, 'b1')).toBe(4);
    applyPlanBatch.mockResolvedValue(ok());
    await act(async () => {
      fireEvent.keyDown(t.canvas(), { key: 's', ctrlKey: true });
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
    window.localStorage.removeItem('kamerplanter.gardenPlan.singleKeyShortcuts');
  });

  it('speaks a finished save once and keeps the visible status out of the live regions', async () => {
    const t = setupEditor({ plan: plan() });
    const spoken = () => screen.getByTestId('garden-plan-save-announcement');
    expect(status()).not.toHaveAttribute('aria-live');
    expect(status()).not.toHaveAttribute('role');
    expect(spoken()).toHaveTextContent('');
    moveBed(t, 4);
    expect(spoken()).toHaveTextContent('');
    applyPlanBatch.mockResolvedValue(ok());
    await clickSave(t);
    expect(spoken()).toHaveTextContent('Saved');
    moveBed(t, 5);
    expect(spoken()).toHaveTextContent('');
  });

  it('Ctrl+S inside a field commits the value first, then saves it', async () => {
    const t = setupEditor({ plan: plan() });
    t.click(4, 4); // selects b1, the panel shows its fields
    const field = screen.getByTestId('garden-plan-panel-name');
    applyPlanBatch.mockResolvedValue(ok());
    await act(async () => {
      field.focus();
      fireEvent.change(field, { target: { value: 'Herbs' } });
      fireEvent.keyDown(field, { key: 's', ctrlKey: true });
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
    expect(applyPlanBatch.mock.calls[0][1].operations).toEqual([
      expect.objectContaining({ op: 'update_fields', key: 'b1', fields: { name: 'Herbs' } }),
    ]);
  });

  it('explains a 422 per operation, keeps everything pending and lets the user retry', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    applyPlanBatch.mockRejectedValue(
      apiError(422, 'validation_error', [
        { op_index: 0, field: 'geometry', code: 'geometry.outside_parent' },
      ]),
    );
    await clickSave(t);
    const alert = screen.getByTestId('garden-plan-save-error');
    expect(alert).toHaveTextContent('Nothing was saved');
    expect(within(alert).getByTestId('garden-plan-save-findings')).toHaveTextContent(
      /Change 1 \(Bed b1\)/,
    );
    expect(alert).toHaveTextContent(/sticks out of its area/);
    expect(status()).toHaveTextContent('Saving failed – 1 change still open');
    expect(t.state().pending).toHaveLength(1);
    // The user fixes it and tries again.
    applyPlanBatch.mockResolvedValue(ok());
    await clickSave(t);
    expect(status()).toHaveTextContent('Saved');
    expect(screen.queryByTestId('garden-plan-save-error')).toBeNull();
  });

  it('keeps naming the right operation when the user edits on before reading the message', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    applyPlanBatch.mockRejectedValue(
      apiError(422, 'validation_error', [{ op_index: 0, field: 'geometry', code: 'geometry.invalid' }]),
    );
    await clickSave(t);
    t.after(() => {
      act(() => {
        t.store.dispatch(
          applyAction(
            [
              {
                op: 'update_geometry',
                entity: 'location',
                key: 'b2',
                geometry: rect(12),
              },
            ],
            MOVE_LABEL,
          ),
        );
      });
    });
    expect(screen.getByTestId('garden-plan-save-findings')).toHaveTextContent(/Bed b1/);
  });

  it('says what happened when the server cannot be reached', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    applyPlanBatch.mockRejectedValue(new Error('Network Error'));
    await clickSave(t);
    expect(screen.getByTestId('garden-plan-save-error')).toHaveTextContent(
      /no connection to the server/,
    );
    expect(screen.getByTestId('garden-plan-save-error')).toHaveTextContent(/still here/);
    expect(t.state().pending).toHaveLength(1);
    expect(screen.getByTestId('garden-plan-save')).toHaveTextContent('Save again');
  });

  it('refuses more than 500 pending operations before any request (V-17)', async () => {
    const t = setupEditor({ plan: plan() });
    const many = Array.from({ length: 501 }, (_, i) => move('b1', 3 + (i % 2)));
    t.after(() => {
      act(() => {
        t.store.dispatch(applyAction(many, MOVE_LABEL));
      });
    });
    await clickSave(t);
    expect(applyPlanBatch).not.toHaveBeenCalled();
    expect(screen.getByTestId('garden-plan-save-error')).toHaveTextContent(/More than 500 changes/);
  });

  it('has no accessibility violations in any state of the bar', async () => {
    const t = setupEditor({ plan: plan() });
    await expectNoA11yViolations(screen.getByTestId('garden-plan-save-area'), { minImpact: 'serious' });
    moveBed(t, 4);
    applyPlanBatch.mockRejectedValue(
      apiError(422, 'validation_error', [{ op_index: 0, field: 'geometry', code: 'geometry.invalid' }]),
    );
    await clickSave(t);
    await expectNoA11yViolations(screen.getByTestId('garden-plan-save-area'), { minImpact: 'serious' });
  });
});

describe('409 conflict (GP-ACC-010/011, GP-UX-017)', () => {
  let downloaded: Blob | null;
  let anchorDownload: string | null;

  beforeEach(() => {
    downloaded = null;
    anchorDownload = null;
    URL.createObjectURL = vi.fn((blob: Blob) => {
      downloaded = blob;
      return 'blob:plan-changes';
    });
    URL.revokeObjectURL = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      anchorDownload = this.download;
    });
  });

  async function conflict(t: Harness) {
    moveBed(t, 4);
    applyPlanBatch.mockRejectedValue(
      apiError(409, 'plan.revision_conflict', [
        { current_revision: 43, changed_by: 'Sabine', changed_at: '2026-10-17T09:00:00Z' },
      ]),
    );
    await clickSave(t);
  }

  it('opens the dialog, empties the undo stack and keeps the unsaved changes', async () => {
    const t = setupEditor({ plan: plan() });
    moveBed(t, 4);
    moveBed(t, 5);
    applyPlanBatch.mockRejectedValue(
      apiError(409, 'plan.revision_conflict', [
        { current_revision: 43, changed_by: 'Sabine', changed_at: '2026-10-17T09:00:00Z' },
      ]),
    );
    await clickSave(t);
    const dialog = screen.getByRole('alertdialog');
    expect(screen.getByTestId('plan-conflict-dialog')).toContainElement(dialog);
    expect(screen.getByTestId('plan-conflict-reload')).toHaveFocus();
    expect(dialog).toHaveAccessibleName('The plan was changed meanwhile');
    expect(dialog).toHaveTextContent('Your 2 unsaved changes could not be applied.');
    expect(screen.getByTestId('plan-conflict-who')).toHaveTextContent(/Sabine/);
    expect(
      within(dialog).getByRole('button', { name: 'Keep my changes as a copy (download JSON)' }),
    ).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: 'Reload' })).toBeInTheDocument();
    expect(t.state().past).toHaveLength(0);
    expect(t.state().pending).toHaveLength(2);
    expect(status()).toHaveTextContent('Conflict');
    expect(screen.getByTestId('garden-plan-save')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-undo')).toBeDisabled();
  });

  it('cannot be dismissed with Escape', async () => {
    const t = setupEditor({ plan: plan() });
    await conflict(t);
    fireEvent.keyDown(screen.getByRole('alertdialog'), { key: 'Escape' });
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('downloads the pending operations as JSON without personal data and leaves the dialog open', async () => {
    const t = setupEditor({ plan: plan() });
    await conflict(t);
    fireEvent.click(screen.getByTestId('plan-conflict-download'));
    expect(anchorDownload).toBe('garden-plan-changes-site_1-rev42.json');
    const body = JSON.parse(await downloaded!.text());
    expect(body).toMatchObject({
      format: 'kamerplanter.garden-plan-changes',
      site_key: 'site_1',
      based_on_revision: 42,
      current_revision: 43,
    });
    expect(body.operations).toEqual([move('b1', 4)]);
    expect(JSON.stringify(body)).not.toContain('Sabine');
    expect(screen.getByTestId('plan-conflict-downloaded')).toBeInTheDocument();
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('reloads the current revision: the dialog goes, the pending changes and the stack are empty', async () => {
    const t = setupEditor({ plan: plan() });
    await conflict(t);
    getGardenPlan.mockResolvedValue(
      planResponse({ plan_revision: 43, locations: [bed('b1', 3, 3), bed('b2', 8, 3)], slots: [], plants: [] }),
    );
    await act(async () => {
      fireEvent.click(screen.getByTestId('plan-conflict-reload'));
    });
    t.rerender();
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
    expect(t.state().plan?.revision).toBe(43);
    expect(t.state().pending).toHaveLength(0);
    expect(t.state().past).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-undo')).toBeDisabled();
    expect(status()).toHaveTextContent('Saved');
  });

  it('has no accessibility violations', async () => {
    const t = setupEditor({ plan: plan() });
    await conflict(t);
    await expectNoA11yViolations(screen.getByRole('alertdialog'), { minImpact: 'serious' });
  });
});

describe('layer switch (GP-FR-031)', () => {
  afterEach(() => window.localStorage.clear());

  it('remembers the grid switch in localStorage', () => {
    const t = setupEditor({ plan: plan() });
    const toggle = screen.getByTestId('garden-plan-grid-toggle');
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    t.after(() => fireEvent.click(toggle));
    expect(screen.getByTestId('garden-plan-grid-toggle')).toHaveAttribute('aria-pressed', 'false');
    expect(JSON.parse(window.localStorage.getItem('kp_garden_plan_layers')!)).toEqual({
      grid: false,
      zones: false,
      lastWatered: false,
      underlay: true,
      sun: false,
      moisture: false,
      frost: false,
      plantState: false,
    });
    cleanup();
    setupEditor({ plan: plan() });
    expect(screen.getByTestId('garden-plan-grid-toggle')).toHaveAttribute('aria-pressed', 'false');
  });

  it('still works when the storage throws', () => {
    const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const set = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const t = setupEditor({ plan: plan() });
    const toggle = screen.getByTestId('garden-plan-grid-toggle');
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    t.after(() => fireEvent.click(toggle));
    expect(screen.getByTestId('garden-plan-grid-toggle')).toHaveAttribute('aria-pressed', 'false');
    spy.mockRestore();
    set.mockRestore();
  });
});
