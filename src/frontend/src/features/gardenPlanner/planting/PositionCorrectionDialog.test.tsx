/**
 * "Correct position" snaps a dragged plant to the site grid in the bed frame (REQ-053 GP-FR-068, GP-FR-154, #2893):
 * the drag always lands on the grid step, `Alt` drags freely to the centimetre, the step
 * comes from the site plan (5 cm and 10 cm give different points), and the stepper buttons are not snapped.
 */
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import PositionCorrectionDialog from './PositionCorrectionDialog';
import { BASE, BED_GEOMETRY } from './plantingTestKit';

interface Patch {
  slot: string;
  body: unknown;
}

function useSlotBackend(): Patch[] {
  const patches: Patch[] = [];
  server.use(
    http.get(`${BASE}/slots/:key`, () =>
      HttpResponse.json({ key: 's1', slot_id: 'BED_001', location_key: 'loc_b03', geometry: { kind: 'point', origin: [0.3, 0.9] } }),
    ),
    http.get(`${BASE}/slots`, () => HttpResponse.json([])),
    http.patch(`${BASE}/slots/:key`, async ({ request, params }) => {
      patches.push({ slot: String(params.key), body: await request.json() });
      return HttpResponse.json({ key: String(params.key) });
    }),
  );
  return patches;
}

function renderDialog(gridStepM: number, onCorrected = vi.fn()) {
  renderWithProviders(
    <PositionCorrectionDialog
      bedName="Raised bed 3"
      bedGeometry={BED_GEOMETRY}
      bedKey="loc_b03"
      slotKey="s1"
      plantLabel="TOM-1"
      gridStepM={gridStepM}
      onClose={vi.fn()}
      onCorrected={onCorrected}
    />,
    { store: createTestStore({ ...tenantState('grower'), ...authState() }) },
  );
  return onCorrected;
}

/** The bed (1.2 m x 2 m) plus its padding is 1.44 m x 2.24 m; drawn on 360 x 560 px that is 250 px/m on both axes. */
function clientOf(x: number, y: number): [number, number] {
  return [(x + 0.12) * 250, (2.12 - y) * 250];
}

function pointer(target: Element, type: string, [clientX, clientY]: [number, number], altKey = false) {
  const event = new MouseEvent(type, { clientX, clientY, altKey, bubbles: true });
  act(() => {
    target.dispatchEvent(event);
  });
}

async function dragTo(x: number, y: number, altKey = false) {
  const dialog = await screen.findByTestId('position-dialog');
  const handle = await within(dialog).findByTestId('position-canvas-point-0');
  pointer(handle, 'pointerdown', clientOf(0.3, 0.9), altKey);
  pointer(handle, 'pointermove', clientOf(x, y), altKey);
  pointer(handle, 'pointerup', clientOf(x, y), altKey);
  return dialog;
}

beforeEach(() => {
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(
    () => ({ left: 0, top: 0, width: 360, height: 560, right: 360, bottom: 560, x: 0, y: 0, toJSON: () => ({}) }),
  );
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Correct position: the dragged plant snaps to the site grid in the bed frame (GP-FR-154)', () => {
  it('lands on the 10 cm grid and saves that point', async () => {
    const patches = useSlotBackend();
    const user = userEvent.setup();
    const onCorrected = renderDialog(0.1);

    const dialog = await dragTo(0.42, 0.83);

    expect(within(dialog).getByTestId('position-x')).toHaveValue('40');
    expect(within(dialog).getByTestId('position-y')).toHaveValue('80');
    await user.click(within(dialog).getByTestId('position-save'));
    await waitFor(() => expect(onCorrected).toHaveBeenCalled());
    expect(patches).toEqual([{ slot: 's1', body: { geometry: { kind: 'point', origin: [0.4, 0.8] } } }]);
  });

  it('does not snap while Alt is held: the centimetre rounding stays', async () => {
    useSlotBackend();
    renderDialog(0.1);

    const dialog = await dragTo(0.42, 0.83, true);

    expect(within(dialog).getByTestId('position-x')).toHaveValue('42');
    expect(within(dialog).getByTestId('position-y')).toHaveValue('83');
  });

  it('takes the step from the site plan: a 5 cm grid gives another point than a 10 cm grid', async () => {
    useSlotBackend();
    renderDialog(0.05);

    const dialog = await dragTo(0.42, 0.83);

    expect(within(dialog).getByTestId('position-x')).toHaveValue('40');
    expect(within(dialog).getByTestId('position-y')).toHaveValue('85');
  });

  it('snaps however far the pointer is from a grid line - the grid has no pixel tolerance', async () => {
    useSlotBackend();
    renderDialog(0.1);
    // 4.4 cm and 4.4 cm off their nearest lines: 11 px each, beyond any object-snap tolerance of the mouse
    const dialog = await dragTo(0.456, 0.744);

    expect(within(dialog).getByTestId('position-x')).toHaveValue('50');
    expect(within(dialog).getByTestId('position-y')).toHaveValue('70');
  });

  it('leaves the stepper buttons unsnapped', async () => {
    useSlotBackend();
    const user = userEvent.setup();
    renderDialog(0.1);
    const dialog = await screen.findByTestId('position-dialog');
    await within(dialog).findByTestId('position-x');

    await user.click(within(dialog).getByTestId('position-step-1'));
    await user.click(within(dialog).getByTestId('position-right'));

    expect(within(dialog).getByTestId('position-x')).toHaveValue('31');
    expect(within(dialog).getByTestId('position-y')).toHaveValue('90');
  });
});
