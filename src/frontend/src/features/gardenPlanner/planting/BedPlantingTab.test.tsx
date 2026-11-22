/**
 * The planting tab and the two plant actions (REQ-053 WP 3.6: §11.3, GP-FR-068/069, GP-ACC-022): the planned
 * and standing plants, "Correct position" (stepper and coordinates; the server writes the care event) and
 * "Transplant to …" (the existing `transplant` task), and what a viewer does not get.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedListItem, bedSummary } from '../bed/bedTestKit';
import type { BedSummary } from '../bed/types';
import BedPlantingTab from './BedPlantingTab';
import { BASE, species, usePlantingBackend, type Seen } from './plantingTestKit';
import type { PlantingItem } from './plantingTypes';

const PLANTINGS: PlantingItem[] = [
  { state: 'active', slot_key: 's1', slot_id: 'BED_001', species_key: 'sp_tomato', plant_key: 'pl_1', instance_id: 'TOM-1', planted_on: '2026-05-10' },
  { state: 'active', slot_key: null, slot_id: null, species_key: 'sp_tomato', plant_key: 'pl_2', instance_id: 'TOM-2', planted_on: '2026-05-10' },
  { state: 'planned', slot_key: 's3', slot_id: 'BED_003', species_key: 'sp_basil', run_key: 'run_b', planned_from: '2026-06-01' },
  { state: 'historical', slot_key: 's9', slot_id: 'BED_009', species_key: 'sp_tomato', plant_key: 'pl_old', instance_id: 'TOM-0' },
];

function useTabBackend(plantings: PlantingItem[] = PLANTINGS, slotGeometry: unknown = { kind: 'point', origin: [0.3, 0.9] }) {
  const backend = usePlantingBackend({ species: [] });
  const writes: Seen[] = [];
  server.use(
    http.get(`${BASE}/locations/:key/plantings`, () => HttpResponse.json(plantings)),
    http.get('/api/v1/species/:key', ({ params }) => {
      const names: Record<string, string> = { sp_tomato: 'Tomato', sp_basil: 'Basil' };
      return HttpResponse.json(species(String(params.key), names[String(params.key)] ?? 'Other'));
    }),
    http.get(`${BASE}/slots/:key`, () =>
      HttpResponse.json({ key: 's1', slot_id: 'BED_001', location_key: 'loc_b03', geometry: slotGeometry }),
    ),
    http.patch(`${BASE}/slots/:key`, async ({ request, params }) => {
      writes.push({ url: `/slots/${String(params.key)}`, body: await request.json() });
      return HttpResponse.json({ key: String(params.key) });
    }),
    http.get(`${BASE}/locations`, () => HttpResponse.json([bedListItem('loc_b03'), bedListItem('loc_b04', { name: 'Bed 4' })])),
    http.post(`${BASE}/tasks`, async ({ request }) => {
      writes.push({ url: '/tasks', body: await request.json() });
      return HttpResponse.json({ key: 't1' }, { status: 201 });
    }),
  );
  return { ...backend, writes };
}

function renderTab(role: 'viewer' | 'grower' | 'lead' = 'grower', bed: BedSummary = bedSummary(), onChanged = vi.fn()) {
  return {
    onChanged,
    ...renderWithProviders(<BedPlantingTab bed={bed} onChanged={onChanged} gridStepM={0.1} />, {
      store: createTestStore({ ...tenantState(role), ...authState() }),
    }),
  };
}

afterEach(() => cleanup());

describe('BedPlantingTab', () => {
  it('lists what is planned and what stands, with the species names', async () => {
    useTabBackend();
    renderTab();

    const active = await screen.findByTestId('bed-planting-active');
    await waitFor(() => expect(within(active).getByTestId('planting-active-pl_1')).toHaveTextContent('TOM-1 · Tomato'));
    const planned = screen.getByTestId('bed-planting-planned');
    await waitFor(() => expect(within(planned).getByTestId('planting-planned-s3')).toHaveTextContent('Basil · BED_003'));
    expect(screen.getByTestId('bed-planting-finished')).toHaveTextContent('1 plant is harvested or removed');
  });

  it('links a standing plant to its detail page and a planned species to its species page (#2515)', async () => {
    useTabBackend();
    renderTab('viewer');

    const active = await screen.findByTestId('bed-planting-active');
    const plant = await within(active).findByRole('link', { name: /^TOM-1 · Tomato/ });
    expect(plant).toHaveAttribute('href', '/pflanzen/plant-instances/pl_1');
    expect(within(active).getByRole('link', { name: /^TOM-2 · Tomato/ })).toHaveAttribute('href', '/pflanzen/plant-instances/pl_2');

    const planned = screen.getByTestId('bed-planting-planned');
    const basil = await within(planned).findByRole('link', { name: 'Basil' });
    expect(basil).toHaveAttribute('href', '/stammdaten/species/sp_basil');
    // The finished plants are a count, not a list: nothing to link there.
    expect(within(screen.getByTestId('bed-planting-finished')).queryByRole('link')).toBeNull();
  });

  it('says so when nothing is planted and offers "Plant" as its one action (GP-UX-049)', async () => {
    useTabBackend([]);
    const user = userEvent.setup();
    renderTab();
    const empty = await screen.findByTestId('bed-planting-empty');
    expect(within(empty).getByText('Nothing planted yet')).toBeInTheDocument();
    expect(within(empty).getAllByRole('button')).toHaveLength(1);
    await user.click(within(empty).getByTestId('bed-planting-empty-plant'));
    expect(await screen.findByTestId('planting-dialog')).toBeInTheDocument();
  });

  it('shows a viewer the empty bed without the action, worded for reading', async () => {
    useTabBackend([]);
    renderTab('viewer');
    const empty = await screen.findByTestId('bed-planting-empty');
    expect(within(empty).getByText('Nothing is planned or planted in this bed yet.')).toBeInTheDocument();
    expect(within(empty).queryByRole('button')).toBeNull();
  });

  it('offers no planting action in the empty state of a bed that is not on the plan', async () => {
    useTabBackend([]);
    renderTab('grower', bedSummary({ geometry: null, bbox: null }));
    const empty = await screen.findByTestId('bed-planting-empty');
    expect(within(empty).queryByTestId('bed-planting-empty-plant')).toBeNull();
  });

  it('the empty state with its action has no accessibility violations', async () => {
    useTabBackend([]);
    renderTab();
    await screen.findByTestId('bed-planting-empty-plant');
    await expectNoA11yViolations(screen.getByTestId('bed-planting-tab'));
  });

  it('shows a viewer the lists only: no Plant button, no plant actions', async () => {
    useTabBackend();
    renderTab('viewer');
    expect(await screen.findByTestId('planting-active-pl_1')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-plant-button')).toBeNull();
    expect(screen.queryByTestId('planting-correct-pl_1')).toBeNull();
    expect(screen.queryByTestId('planting-transplant-pl_1')).toBeNull();
  });

  it('cannot plant a bed that is not on the garden plan, and says why', async () => {
    useTabBackend();
    renderTab('grower', bedSummary({ geometry: null, bbox: null }));
    expect(await screen.findByText(/has to be on the garden plan/)).toBeInTheDocument();
    expect(screen.getByTestId('bed-plant-button')).toBeDisabled();
  });

  it('opens the planting dialog', async () => {
    useTabBackend();
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('bed-plant-button'));
    expect(await screen.findByTestId('planting-dialog')).toBeInTheDocument();
  });

  it('hands the competition flags of the bed to the planting dialog (GP-FR-165, WP 9.11)', async () => {
    useTabBackend();
    usePlantingBackend({ species: [species('sp_tomato', 'Tomato', { spacing_cm: '60' })] });
    const user = userEvent.setup();
    renderTab('grower', bedSummary({ site_conditions: { flags: ['root_competition'] } }));
    await user.click(await screen.findByTestId('bed-plant-button'));
    const box = within(await screen.findByTestId('planting-entry-0')).getByRole('combobox', { name: /^Species/ });
    await user.click(box);
    await user.type(box, 'Toma');
    await user.click(await screen.findByRole('option', { name: /Tomato/ }));

    expect(await screen.findByTestId('planting-site-flags')).toHaveTextContent('Root competition');
  });

  it('has no accessibility violations', async () => {
    useTabBackend();
    renderTab();
    await screen.findByTestId('bed-planting-active');
    await expectNoA11yViolations(screen.getByTestId('bed-planting-tab'));
  });
});

describe('Correct position (GP-FR-068, GP-ACC-022)', () => {
  it('moves the plant with the stepper and writes the new slot geometry - the server logs the event', async () => {
    const backend = useTabBackend();
    const user = userEvent.setup();
    const { onChanged } = renderTab();
    await user.click(await screen.findByTestId('planting-correct-pl_1'));
    const dialog = await screen.findByTestId('position-dialog');
    await within(dialog).findByTestId('position-x');
    expect(within(dialog).getByTestId('position-x')).toHaveValue('30');
    expect(within(dialog).getByTestId('position-y')).toHaveValue('90');
    expect(within(dialog).getByTestId('position-save')).toBeDisabled();

    // §18.1 step 9: the stepper moves 10 cm per press unless a finer step is chosen.
    expect(within(dialog).getByTestId('position-step-10')).toHaveAttribute('aria-pressed', 'true');
    expect(within(dialog).getByText('Drag the plant on the bed or move it with the arrows. Each step is 10 cm.')).toBeInTheDocument();
    for (let step = 0; step < 3; step += 1) await user.click(within(dialog).getByTestId('position-right'));
    expect(within(dialog).getByTestId('position-x')).toHaveValue('60');
    await user.click(within(dialog).getByTestId('position-save'));

    await waitFor(() => expect(backend.writes).toHaveLength(1));
    expect(backend.writes[0]).toEqual({
      url: '/slots/s1',
      body: { geometry: { kind: 'point', origin: [0.6, 0.9] } },
    });
    // The client writes no care event itself: the server does, with the plant.
    expect(backend.seen.filter((s) => s.url.startsWith('/care-events'))).toEqual([]);
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByTestId('position-dialog')).toBeNull());
  });

  it('keeps 5 cm and 1 cm reachable as fine steps in every direction', async () => {
    const backend = useTabBackend();
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('planting-correct-pl_1'));
    const dialog = await screen.findByTestId('position-dialog');
    const x = await within(dialog).findByTestId('position-x');
    const y = within(dialog).getByTestId('position-y');
    const stepSize = within(dialog).getByRole('group', { name: 'Step size' });
    expect(within(stepSize).getAllByRole('button').map((button) => button.textContent)).toEqual(['10 cm', '5 cm', '1 cm']);

    await user.click(within(dialog).getByRole('button', { name: '1 cm per step' }));
    expect(within(dialog).getByTestId('position-step-1')).toHaveAttribute('aria-pressed', 'true');
    expect(within(dialog).getByTestId('position-step-10')).toHaveAttribute('aria-pressed', 'false');
    expect(within(dialog).getByText('Drag the plant on the bed or move it with the arrows. Each step is 1 cm.')).toBeInTheDocument();
    await user.click(within(dialog).getByTestId('position-right'));
    expect(x).toHaveValue('31');
    await user.click(within(dialog).getByTestId('position-left'));
    await user.click(within(dialog).getByTestId('position-left'));
    expect(x).toHaveValue('29');
    expect(y).toHaveValue('90');

    await user.click(within(dialog).getByTestId('position-step-5'));
    await user.click(within(dialog).getByTestId('position-down'));
    expect(y).toHaveValue('85');
    await user.click(within(dialog).getByTestId('position-up'));
    await user.click(within(dialog).getByTestId('position-up'));
    expect(y).toHaveValue('95');
    expect(x).toHaveValue('29');
    // Clicking the chosen step again keeps it: there is always one step size.
    await user.click(within(dialog).getByTestId('position-step-5'));
    expect(within(dialog).getByTestId('position-step-5')).toHaveAttribute('aria-pressed', 'true');

    await user.click(within(dialog).getByTestId('position-save'));
    await waitFor(() => expect(backend.writes).toHaveLength(1));
    expect(backend.writes[0].body).toEqual({ geometry: { kind: 'point', origin: [0.29, 0.95] } });
  });

  it('takes typed coordinates too', async () => {
    const backend = useTabBackend();
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('planting-correct-pl_1'));
    const dialog = await screen.findByTestId('position-dialog');
    const x = await within(dialog).findByTestId('position-x');
    await user.clear(x);
    await user.type(x, '60');

    await user.click(within(dialog).getByTestId('position-save'));

    await waitFor(() => expect(backend.writes).toHaveLength(1));
    expect(backend.writes[0].body).toEqual({ geometry: { kind: 'point', origin: [0.6, 0.9] } });
  });

  it('does not save what the field does not say: unreadable text has no position, and a place outside the bed is refused', async () => {
    const backend = useTabBackend();
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('planting-correct-pl_1'));
    const dialog = await screen.findByTestId('position-dialog');
    const x = await within(dialog).findByTestId('position-x');

    await user.clear(x);
    await user.type(x, 'abc');
    expect(within(dialog).getByText('Enter a number in cm.')).toBeInTheDocument();
    expect(within(dialog).getByTestId('position-save')).toBeDisabled();

    await user.clear(x);
    await user.type(x, '500'); // 5 m in a bed 1.2 m wide
    expect(await within(dialog).findByTestId('position-outside')).toBeInTheDocument();
    expect(within(dialog).getByTestId('position-save')).toBeDisabled();

    await user.clear(x);
    await user.type(x, '40');
    expect(within(dialog).queryByTestId('position-outside')).toBeNull();
    expect(within(dialog).getByTestId('position-save')).toBeEnabled();
    expect(backend.writes).toEqual([]);
  });

  it('explains that a plant in a zone has no single position and offers no way to move it', async () => {
    useTabBackend(PLANTINGS, { kind: 'polygon', points: [[0, 0], [1, 0], [1, 1]] });
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('planting-correct-pl_1'));

    expect(await screen.findByTestId('position-zone-note')).toBeInTheDocument();
    expect(screen.queryByTestId('position-x')).toBeNull();
    expect(screen.getByTestId('position-save')).toBeDisabled();
  });

  it('offers no correction for a plant without a slot', async () => {
    useTabBackend();
    renderTab();
    await screen.findByTestId('planting-active-pl_2');
    expect(screen.queryByTestId('planting-correct-pl_2')).toBeNull();
    expect(screen.getByTestId('planting-transplant-pl_2')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    useTabBackend();
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('planting-correct-pl_1'));
    const dialog = await screen.findByTestId('position-dialog');
    await within(dialog).findByTestId('position-x');
    await expectNoA11yViolations(dialog);
  });
});

describe('Transplant to … (GP-FR-069)', () => {
  it('creates the existing transplant task for the plant, naming the target bed', async () => {
    const backend = useTabBackend();
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('planting-transplant-pl_1'));
    const dialog = await screen.findByTestId('transplant-dialog');
    // The bed itself is not offered as a target.
    await user.click(await within(dialog).findByRole('combobox', { name: 'Target bed' }));
    expect(screen.queryByRole('option', { name: 'Bed loc_b03' })).toBeNull();
    await user.click(await screen.findByRole('option', { name: 'Bed 4' }));

    await user.click(within(dialog).getByTestId('transplant-submit'));

    await waitFor(() => expect(backend.writes).toHaveLength(1));
    expect(backend.writes[0].body).toMatchObject({
      category: 'transplant',
      entity_type: 'plant_instance',
      entity_key: 'pl_1',
      name: 'Transplant TOM-1 to Bed 4',
    });
    await waitFor(() => expect(screen.queryByTestId('transplant-dialog')).toBeNull());
  });
});

describe('Sown, thinned out, failed (REQ-053 §11.3, W-015)', () => {
  const ROW: PlantingItem = {
    state: 'planned', slot_key: 'r1', slot_id: 'BED_R01', species_key: 'sp_tomato', run_key: 'run_c', slot_role: 'row',
  };
  const SOWN: PlantingItem = { ...ROW, slot_key: 'r2', slot_id: 'BED_R02', sown_at: '2026-04-12' };
  const FAILED: PlantingItem = {
    state: 'historical', slot_key: 's7', slot_id: 'BED_007', species_key: 'sp_tomato', cultivar_key: null,
    plant_key: 'pl_dead', instance_id: 'TOM-7', removed_on: '2026-06-01', termination_type: 'died',
  };

  it('lists a sown row apart from the planned ones and offers "Thin out" there', async () => {
    useTabBackend([ROW, SOWN]);
    server.use(
      http.get(`${BASE}/slots/:key/thinning`, () =>
        HttpResponse.json({
          slot_key: 'r2', slot_id: 'BED_R02', slot_role: 'row', sown_at: '2026-04-12', run_key: 'run_c',
          entry_key: 'e1', species_key: 'sp_tomato', measure_kind: 'length', measure_value: 1.2,
          thinning_to_cm: 5, suggested_count: 24, max_count: 500,
        }),
      ),
    );
    const user = userEvent.setup();
    renderTab();

    const sown = await screen.findByTestId('bed-planting-sown');
    await waitFor(() => expect(within(sown).getByTestId('planting-sown-r2')).toHaveTextContent('Tomato · BED_R02 · sown on'));
    expect(within(screen.getByTestId('bed-planting-planned')).queryByTestId('planting-planned-r2')).toBeNull();
    await user.click(within(sown).getByTestId('planting-thin-r2'));
    expect(await screen.findByTestId('thinning-dialog')).toBeInTheDocument();
  });

  it('lists a zone stand apart, without "Thin out", and lets the bed be cleared (#2862)', async () => {
    const STAND: PlantingItem = {
      ...ROW, slot_key: 'z1', slot_id: 'BED_Z01', slot_role: 'zone', sown_at: '2026-04-12', thinned_at: '2026-05-20',
    };
    useTabBackend([ROW, STAND]);
    renderTab();

    const stands = await screen.findByTestId('bed-planting-stands');
    await waitFor(() =>
      expect(within(stands).getByTestId('planting-stand-z1')).toHaveTextContent('Tomato · BED_Z01 · sown on'),
    );
    expect(within(stands).getByTestId('planting-stand-z1')).toHaveTextContent('thinned on');
    expect(screen.queryByTestId('bed-planting-sown')).toBeNull();
    expect(screen.queryByTestId('planting-thin-z1')).toBeNull();
    expect(screen.queryByTestId('planting-sow-z1')).toBeNull();
    expect(screen.getByTestId('bed-clear-button')).toBeInTheDocument();
  });

  it('offers "Record sowing" on a planned row and sends the day', async () => {
    useTabBackend([ROW]);
    const puts: unknown[] = [];
    server.use(
      http.put(`${BASE}/slots/:key/sowing`, async ({ request, params }) => {
        puts.push({ key: params.key, body: await request.json() });
        return HttpResponse.json({ key: 'r1', slot_id: 'BED_R01', location_key: 'loc_b03' });
      }),
    );
    const user = userEvent.setup();
    renderTab();

    await user.click(await screen.findByTestId('planting-sow-r1'));
    await user.click(await screen.findByTestId('sowing-submit'));

    await waitFor(() => expect(puts).toHaveLength(1));
    expect(puts[0]).toEqual({ key: 'r1', body: { sown_at: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/) } });
  });

  it('gives a viewer the sown row without the actions', async () => {
    useTabBackend([ROW, SOWN, FAILED]);
    renderTab('viewer');
    await screen.findByTestId('bed-planting-sown');
    expect(screen.queryByTestId('planting-thin-r2')).toBeNull();
    expect(screen.queryByTestId('planting-sow-r1')).toBeNull();
    expect(screen.queryByTestId('planting-replant-s7')).toBeNull();
    expect(screen.getByTestId('planting-failed-s7')).toBeInTheDocument();
  });

  it('offers "Replant" on a failed slot; the planting dialog opens with that crop', async () => {
    useTabBackend([FAILED]);
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({ items: [species('sp_tomato', 'Tomato', { spacing_cm: '60' })], total: 1, offset: 0, limit: 200 }),
      ),
    );
    const user = userEvent.setup();
    renderTab();

    const failed = await screen.findByTestId('bed-planting-failed');
    await waitFor(() => expect(within(failed).getByTestId('planting-failed-s7')).toHaveTextContent('Tomato · BED_007'));
    await user.click(within(failed).getByTestId('planting-replant-s7'));

    expect(await screen.findByTestId('planting-dialog')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('planting-entry-0-spacing')).toHaveValue('60'));
    expect(within(screen.getByTestId('planting-entry-0')).getByRole('combobox', { name: /^Species/ })).toHaveValue(
      'Tomato (Tomato scientificus)',
    );
  });

  it('names the died plant in the crop-rotation check of the replant, so it is no previous crop (#2888)', async () => {
    const backend = useTabBackend([FAILED]);
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({ items: [species('sp_tomato', 'Tomato', { spacing_cm: '60' })], total: 1, offset: 0, limit: 200 }),
      ),
    );
    const user = userEvent.setup();
    renderTab();

    await user.click(await screen.findByTestId('planting-replant-s7'));

    await waitFor(() =>
      expect(backend.validations).toContainEqual({ species_key: 'sp_tomato', replant_of_plant_key: 'pl_dead' }),
    );
  });

  it('names no plant in the check of a planting that is no replant', async () => {
    const backend = useTabBackend([]);
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({ items: [species('sp_tomato', 'Tomato', { spacing_cm: '60' })], total: 1, offset: 0, limit: 200 }),
      ),
    );
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('bed-planting-empty-plant'));
    const entry = await screen.findByTestId('planting-entry-0');
    const box = within(entry).getByRole('combobox', { name: /^Species/ });
    await user.click(box);
    await user.type(box, 'Toma');
    await user.click(await screen.findByRole('option', { name: /Tomato/ }));

    await waitFor(() => expect(backend.validations).toHaveLength(1));
    expect(backend.validations[0]).toEqual({ species_key: 'sp_tomato' });
  });
});
