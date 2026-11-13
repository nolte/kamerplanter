/**
 * The plan tool "Pflanze setzen" in the editor (REQ-053 GP-UX-071, #2913): a rail button for writing roles, a click
 * on a free point slot opens the dialog for exactly that slot, the plant is created through the single-plant API
 * with `slot_key`, the plan is read again and the tool stays on. Everything else a click lands on is told, the
 * server's refusals are readable in the dialog, offline nothing is set, and the properties panel is the way without
 * a pointer.
 */
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { server } from '@/test/mocks/server';
import { gardenPlanSlice, setPlanOffline } from '../state/gardenPlanSlice';
import { BASE, species, usePlantingBackend } from '../planting/plantingTestKit';
import { setupEditor, stubPhone } from './editorTestKit';
import { testPlan, testPlanResponse } from './tools/toolTestKit';

const restores: (() => void)[] = [];
afterEach(() => {
  cleanup();
  while (restores.length) restores.pop()?.();
});

const LETTUCE = species('sp_lettuce', 'Lettuce');

interface PlantBackend {
  created: Record<string, unknown>[];
  planReads: number;
}

/**
 * The planting backend plus the single-plant path: the slot check, the slot read, the create and the plan read
 * again (with the new plant on slot s2).
 */
function usePlantBackend(options: {
  valid?: boolean;
  createError?: { status: number; code: string };
} = {}): PlantBackend {
  usePlantingBackend({ species: [LETTUCE] });
  const backend: PlantBackend = { created: [], planReads: 0 };
  server.use(
    http.post(`${BASE}/plant-instances/slots/:slot/validate-planting`, () =>
      HttpResponse.json({ valid: options.valid ?? true, warnings: [], benefits: [] }),
    ),
    http.post(`${BASE}/plant-instances`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      backend.created.push(body);
      if (options.createError) {
        return HttpResponse.json(
          {
            error_id: 'e1',
            error_code: options.createError.code,
            message: 'refused',
            details: [],
            path: '/plant-instances',
            method: 'POST',
          },
          { status: options.createError.status },
        );
      }
      return HttpResponse.json({ key: 'p_new', ...body }, { status: 201 });
    }),
    http.get(`${BASE}/sites/:key/plan`, () => {
      backend.planReads += 1;
      return HttpResponse.json(
        testPlanResponse([
          { key: 'p1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 's1' },
          { key: 'p_new', instance_id: 'LETTU-1', species_key: 'sp_lettuce', slot_key: 's2' },
        ]),
      );
    }),
  );
  return backend;
}

/** The editor with the plant tool on. */
function plantSetup() {
  const t = setupEditor({ connected: true });
  t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-plant')));
  return t;
}

async function chooseLettuce(user: ReturnType<typeof userEvent.setup>) {
  const dialog = await screen.findByTestId('garden-plan-plant-dialog');
  const box = await within(dialog).findByRole('combobox', { name: /^Species/ });
  await user.click(box);
  await user.type(box, 'Lett');
  await user.click(await screen.findByRole('option', { name: /Lettuce/ }));
  return dialog;
}

describe('the plant tool on the rail (GP-UX-071)', () => {
  it('is a rail tool with a verb tooltip, a 48 px target and the hand cursor; the status says what a click does', () => {
    const t = plantSetup();
    const button = screen.getByTestId('garden-plan-tool-plant');
    expect(t.state().tool).toBe('plant');
    expect(button).toHaveAttribute('aria-pressed', 'true');
    expect(button).toHaveAccessibleName('Set a plant');
    expect(t.canvas()).toHaveStyle({ cursor: 'pointer' });
    const status = screen.getByTestId('garden-plan-plant-status');
    expect(status).toHaveTextContent('Click a free planting spot');
    expect(status).toHaveAttribute('aria-live', 'polite');
    // Seven tools now, within GP-UX-001's eight.
    const rail = within(screen.getByRole('group', { name: 'Tool' }));
    // The tools' own buttons (the sub-menu buttons beside area, bed and garden object are no tools).
    expect(rail.getAllByRole('button').filter((node) => node.getAttribute('aria-pressed') !== null)).toHaveLength(7);
    expect(button).toHaveStyle({ minWidth: '48px', minHeight: '48px' });
  });

  it('a viewer gets neither the tool nor the panel entry', () => {
    const t = setupEditor({ role: 'viewer' });
    expect(screen.getByTestId('garden-plan-tool-measure')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-tool-plant')).toBeNull();
    t.click(4, 3.2); // bed 1, which has a free spot
    expect(t.selected()).toEqual(['b1']);
    expect(screen.getByTestId('garden-plan-panel')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-panel-plant-spot')).toBeNull();
  });
});

describe('a click with the plant tool', () => {
  it('on a free point slot opens the dialog for that bed and slot; occupied, missed and no-bed clicks say why', async () => {
    usePlantBackend();
    const t = plantSetup();
    t.click(4.5, 4.5); // s2, free
    const dialog = await screen.findByTestId('garden-plan-plant-dialog');
    expect(within(dialog).getByRole('heading')).toHaveTextContent('Set a plant: Bed 1, spot B1_2');
    expect(t.selected()).toEqual(['s2']);
    // One spot clicked: no spot choice in the dialog.
    expect(within(dialog).queryByTestId('garden-plan-plant-dialog-slot')).toBeNull();
    fireEvent.click(within(dialog).getByTestId('garden-plan-plant-dialog-cancel'));
    await waitFor(() => expect(screen.queryByTestId('garden-plan-plant-dialog')).toBeNull());

    t.click(3.5, 3.5); // s1, the tomato stands there
    expect(screen.queryByTestId('garden-plan-plant-dialog')).toBeNull();
    expect(t.selected()).toEqual(['p1']);
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('A plant stands here already');

    t.click(4.6, 3.3); // inside bed 1, beside its spots
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('Missed');

    t.click(7, 4); // bed 2 has no planting spots
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('This bed has no planting spots yet');
    expect(t.selected()).toEqual(['b2']);

    t.click(19, 19); // empty ground
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('There is no bed here');
    expect(screen.queryByTestId('garden-plan-plant-dialog')).toBeNull();
    expect(t.state().tool).toBe('plant');
  });

  it('with the spots hidden by the level of detail zooms in around the click and says so', () => {
    const t = setupEditor({
      onZoom: vi.fn(),
      viewport: { originM: [0, 400], pxPerM: 1, widthPx: 800, heightPx: 800 },
    });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-plant')));
    // Model (4, 4) at 1 px per metre: x 4 px, y 396 px.
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), { pointerId: 1, pointerType: 'mouse', button: 0, clientX: 4, clientY: 396 });
      fireEvent.pointerUp(t.canvas(), { pointerId: 1, pointerType: 'mouse', button: 0, clientX: 4, clientY: 396 });
    });
    expect(t.onZoom).toHaveBeenCalledTimes(1);
    const [pxPerM, anchor] = t.onZoom!.mock.calls[0];
    expect(pxPerM).toBeGreaterThan(1);
    expect(anchor).toEqual([4, 396]);
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('the plan is zoomed in now');
    expect(screen.queryByTestId('garden-plan-plant-dialog')).toBeNull();
  });
});

describe('the plant dialog', () => {
  it('needs a species, creates ONE plant with the slot_key, reads the plan again and keeps the tool on', async () => {
    const backend = usePlantBackend();
    const user = userEvent.setup();
    const t = plantSetup();
    t.click(4.5, 4.5);
    const dialog = await screen.findByTestId('garden-plan-plant-dialog');
    // The species catalogue is loaded once the picker is there; then "Set the plant" without a species refuses.
    await within(dialog).findByRole('combobox', { name: /^Species/ });
    await user.click(within(dialog).getByTestId('garden-plan-plant-dialog-submit'));
    expect(await within(dialog).findByText('Choose a species.')).toBeInTheDocument();
    expect(backend.created).toEqual([]);

    await chooseLettuce(user);
    const submit = within(dialog).getByTestId('garden-plan-plant-dialog-submit');
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    await waitFor(() => expect(screen.queryByTestId('garden-plan-plant-dialog')).toBeNull());

    expect(backend.created).toHaveLength(1);
    expect(backend.created[0]).toMatchObject({
      species_key: 'sp_lettuce',
      slot_key: 's2',
      location_key: 'b1',
      site_key: 'site_1',
      cultivar_key: null,
    });
    expect(backend.created[0].planted_on).toBe(new Date().toISOString().slice(0, 10));
    expect(backend.planReads).toBe(1);
    // Announced politely, the new plant selected, the tool still on for the next spot, nothing pending in the plan.
    const info = await screen.findByTestId('garden-plan-info');
    expect(info).toHaveTextContent('Lettuce set in Bed 1.');
    expect(info).toHaveAttribute('role', 'status');
    expect(t.state().tool).toBe('plant');
    expect(t.state().selection).toEqual([{ entity: 'plant', key: 'p_new' }]);
    expect(t.state().pending).toEqual([]);
    expect(t.state().plan?.plants.p_new?.slot_key).toBe('s2');
  });

  it('a hard rotation block: says there is no "plant anyway" for one plant, points to the bed and sends nothing', async () => {
    const backend = usePlantBackend({ valid: false });
    const opened: string[] = [];
    const user = userEvent.setup();
    const t = setupEditor({ connected: true, onOpenLocation: vi.fn((key: string) => void opened.push(key)) });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-plant')));
    t.click(4.5, 4.5);
    const dialog = await chooseLettuce(user);
    const blocked = await within(dialog).findByTestId('garden-plan-plant-dialog-blocked');
    expect(blocked).toHaveTextContent('A single plant has no “Plant anyway”');
    expect(within(dialog).getByTestId('garden-plan-plant-dialog-submit')).toBeDisabled();
    // The single plant has no override step in the hints either.
    expect(within(dialog).queryByTestId('planting-override-check')).toBeNull();
    await user.click(within(dialog).getByTestId('garden-plan-plant-dialog-open-bed'));
    expect(opened).toEqual(['b1']);
    expect(backend.created).toEqual([]);
  });

  it('a refusal of the create (ROTATION_VIOLATION) is a readable sentence in the dialog, never silent', async () => {
    usePlantBackend({ createError: { status: 422, code: 'ROTATION_VIOLATION' } });
    const user = userEvent.setup();
    const t = plantSetup();
    t.click(4.5, 4.5);
    const dialog = await chooseLettuce(user);
    const submit = within(dialog).getByTestId('garden-plan-plant-dialog-submit');
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    const blocked = await within(dialog).findByTestId('garden-plan-plant-dialog-blocked');
    expect(blocked).toHaveTextContent('crop rotation does not allow this plant family here yet');
    expect(screen.getByTestId('garden-plan-plant-dialog')).toBeInTheDocument();
  });

  it("a slot taken meanwhile: the server's 409 slot.occupied reads as its sentence in the dialog", async () => {
    const backend = usePlantBackend({ createError: { status: 409, code: 'slot.occupied' } });
    const user = userEvent.setup();
    const t = plantSetup();
    t.click(4.5, 4.5);
    const dialog = await chooseLettuce(user);
    const submit = within(dialog).getByTestId('garden-plan-plant-dialog-submit');
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(await within(dialog).findByTestId('garden-plan-plant-dialog-error')).toHaveTextContent(
      'A plant stands on this planting spot by now',
    );
    // The request went out: the server decides, the client does not guess from an older read.
    expect(backend.created).toHaveLength(1);
    expect(backend.planReads).toBe(1);
  });

  it('a server error that has no sentence of its own still shows one in the dialog', async () => {
    usePlantBackend({ createError: { status: 409, code: 'SOMETHING_ELSE' } });
    const user = userEvent.setup();
    const t = plantSetup();
    t.click(4.5, 4.5);
    const dialog = await chooseLettuce(user);
    const submit = within(dialog).getByTestId('garden-plan-plant-dialog-submit');
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(await within(dialog).findByTestId('garden-plan-plant-dialog-error')).toHaveTextContent(
      'The plant could not be set',
    );
  });

  it('has no axe violations', async () => {
    usePlantBackend();
    const user = userEvent.setup();
    const t = plantSetup();
    t.click(4.5, 4.5);
    const dialog = await chooseLettuce(user);
    await within(dialog).findByTestId('planting-hints');
    await expectNoA11yViolations(dialog);
  });
});

describe('without a connection', () => {
  it('the status says the tool needs one and a click opens nothing', () => {
    const t = plantSetup();
    t.after(() => t.store.dispatch(setPlanOffline(true)));
    expect(screen.getByTestId('garden-plan-plant-status')).toHaveTextContent('you are offline right now');
    t.click(4.5, 4.5);
    expect(screen.queryByTestId('garden-plan-plant-dialog')).toBeNull();
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('Setting a plant needs a connection');
  });
});

describe('the way without a pointer: the properties panel', () => {
  it('a selected bed with one free spot offers "Set a plant" for that spot', async () => {
    usePlantBackend();
    const t = setupEditor({ connected: true });
    t.click(4, 3.2); // bed 1 with the select tool: s1 is taken, s2 is free
    const entry = await screen.findByTestId('garden-plan-panel-plant-spot');
    expect(screen.getByText('Set one plant on the only free planting spot of this bed.')).toBeInTheDocument();
    fireEvent.click(entry);
    const dialog = await screen.findByTestId('garden-plan-plant-dialog');
    expect(within(dialog).getByRole('heading')).toHaveTextContent('Set a plant: Bed 1, spot B1_2');
    expect(within(dialog).queryByTestId('garden-plan-plant-dialog-slot')).toBeNull();
  });

  it('a selected bed with several free spots lets the dialog choose the spot, the first preselected', async () => {
    usePlantBackend();
    const base = testPlan();
    const plan = {
      ...base,
      slots: {
        ...base.slots,
        s3: { key: 's3', slot_id: 'B1_3', location_key: 'b1', plan_geometry: { origin: [4.5, 3.5] as [number, number] } },
      },
    };
    const t = setupEditor({ connected: true, plan });
    t.click(3.3, 4.6); // bed 1, away from its spots
    fireEvent.click(await screen.findByTestId('garden-plan-panel-plant-spot'));
    const dialog = await screen.findByTestId('garden-plan-plant-dialog');
    expect(within(dialog).getByRole('heading')).toHaveTextContent('Set a plant: Bed 1');
    expect(within(dialog).getByTestId('garden-plan-plant-dialog-slot')).toHaveValue('s2');
  });

  it('a selected free slot offers "Set a plant" for exactly that slot', async () => {
    usePlantBackend();
    const t = setupEditor({ connected: true });
    t.after(() => t.store.dispatch(gardenPlanSlice.actions.setSelection([{ entity: 'slot', key: 's2' }])));
    fireEvent.click(await screen.findByTestId('garden-plan-panel-plant-slot'));
    const dialog = await screen.findByTestId('garden-plan-plant-dialog');
    expect(within(dialog).getByRole('heading')).toHaveTextContent('spot B1_2');
    // An occupied slot offers nothing to plant.
    cleanup();
    const u = setupEditor({ connected: true });
    u.after(() => u.store.dispatch(gardenPlanSlice.actions.setSelection([{ entity: 'slot', key: 's1' }])));
    expect(screen.queryByTestId('garden-plan-panel-plant-slot')).toBeNull();
  });
});

describe('touch below md', () => {
  it('the touch bar offers nothing for the plant tool and a tap opens the dialog', async () => {
    restores.push(stubPhone());
    usePlantBackend();
    const t = plantSetup();
    expect(screen.queryByTestId('garden-plan-touch-place')).toBeNull();
    expect(screen.getByTestId('garden-plan-plant-status')).toHaveTextContent('Tap a free planting spot');
    t.click(4.5, 4.5, { pointerType: 'touch' });
    expect(await screen.findByTestId('garden-plan-plant-dialog')).toBeInTheDocument();
  });
});
