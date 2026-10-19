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
    ...renderWithProviders(<BedPlantingTab bed={bed} onChanged={onChanged} />, {
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

  it('says so when nothing is planted', async () => {
    useTabBackend([]);
    renderTab();
    expect(await screen.findByText('Nothing planted yet')).toBeInTheDocument();
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

    for (let step = 0; step < 3; step += 1) await user.click(within(dialog).getByTestId('position-right'));
    expect(within(dialog).getByTestId('position-x')).toHaveValue('33');
    await user.click(within(dialog).getByTestId('position-save'));

    await waitFor(() => expect(backend.writes).toHaveLength(1));
    expect(backend.writes[0]).toEqual({
      url: '/slots/s1',
      body: { geometry: { kind: 'point', origin: [0.33, 0.9] } },
    });
    // The client writes no care event itself: the server does, with the plant.
    expect(backend.seen.filter((s) => s.url.startsWith('/care-events'))).toEqual([]);
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByTestId('position-dialog')).toBeNull());
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
