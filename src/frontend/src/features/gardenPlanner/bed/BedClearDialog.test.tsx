/**
 * "Beet räumen" (REQ-053 GP-FR-055, GP-API-019, GP-ACC-040, TC-053-027) through the real planting tab and dialog: who is offered
 * the action, what the dialog names before anything is written, the one request with the chosen termination type,
 * the reload after success and the open dialog after a refusal.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedPlantingTab from '../planting/BedPlantingTab';
import { BASE, species } from '../planting/plantingTestKit';
import type { PlantingItem } from '../planting/plantingTypes';
import { bedSummary } from './bedTestKit';

/** Three plants of two runs stand in the bed; one position is planned for a later run. */
const STANDING: PlantingItem[] = [
  { state: 'active', slot_key: 's1', slot_id: 'BED_001', species_key: 'sp_tomato', plant_key: 'pl_1', instance_id: 'TOM-1', run_key: 'run_a', planted_on: '2026-05-10' },
  { state: 'active', slot_key: 's2', slot_id: 'BED_002', species_key: 'sp_tomato', plant_key: 'pl_2', instance_id: 'TOM-2', run_key: 'run_a', planted_on: '2026-05-10' },
  { state: 'active', slot_key: 's3', slot_id: 'BED_003', species_key: 'sp_basil', plant_key: 'pl_3', instance_id: 'BAS-1', run_key: 'run_b', planted_on: '2026-05-20' },
  { state: 'planned', slot_key: 's9', slot_id: 'BED_009', species_key: 'sp_basil', run_key: 'run_c', planned_from: '2026-09-01' },
];

const CLEARED: PlantingItem[] = [
  ...STANDING.filter((item) => item.state === 'active').map((item) => ({
    ...item,
    state: 'historical' as const,
    removed_on: '2026-10-01',
    termination_type: 'died',
  })),
  STANDING[3],
];

interface ClearBackend {
  bodies: unknown[];
  plantingReads: () => number;
}

/** The plantings of the bed (before and after a clearing) and a recording clear route answering `answer`. */
function useClearBackend(answer: () => Response = () => HttpResponse.json(clearedAnswer())): ClearBackend {
  const bodies: unknown[] = [];
  let reads = 0;
  let cleared = false;
  server.use(
    http.get(`${BASE}/locations/:key/plantings`, () => {
      reads += 1;
      return HttpResponse.json(cleared ? CLEARED : STANDING);
    }),
    http.get('/api/v1/species/:key', ({ params }) => {
      const names: Record<string, string> = { sp_tomato: 'Tomato', sp_basil: 'Basil' };
      return HttpResponse.json(species(String(params.key), names[String(params.key)] ?? 'Other'));
    }),
    http.post(`${BASE}/locations/:key/clear`, async ({ request, params }) => {
      bodies.push({ key: String(params.key), body: await request.json() });
      const response = answer();
      if (response.ok) cleared = true;
      return response;
    }),
  );
  return { bodies, plantingReads: () => reads };
}

function clearedAnswer() {
  return { plants_removed: 3, runs_completed: 2, slots_archived: 3, slots_released: 0, care_event_key: 'ce_1' };
}

function renderTab(
  role: 'viewer' | 'grower' | 'lead' = 'grower',
  { editsLocked = false, onChanged = vi.fn() }: { editsLocked?: boolean; onChanged?: () => void } = {},
) {
  return {
    onChanged,
    ...renderWithProviders(
      <BedPlantingTab bed={bedSummary()} onChanged={onChanged} gridStepM={0.1} editsLocked={editsLocked} />,
      { store: createTestStore({ ...tenantState(role), ...authState() }) },
    ),
  };
}

async function openDialog(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByTestId('bed-clear-button'));
  return screen.findByTestId('bed-clear-dialog');
}

afterEach(() => cleanup());

describe('Beet räumen (GP-FR-055)', () => {
  it('names the plants and runs it ends and what clearing does, before anything is written', async () => {
    const backend = useClearBackend();
    const user = userEvent.setup();
    renderTab();

    const dialog = await openDialog(user);
    const affected = within(dialog).getByTestId('bed-clear-affected');
    expect(affected).toHaveTextContent('This affects 3 plants from 2 runs.');
    expect(affected).toHaveAttribute('data-plant-count', '3');
    expect(affected).toHaveAttribute('data-run-count', '2');
    const effects = within(dialog).getByTestId('bed-clear-effects');
    expect(within(effects).getAllByRole('listitem')).toHaveLength(4);
    expect(effects).toHaveTextContent(/ends today/);
    expect(effects).toHaveTextContent(/runs are completed/);
    expect(effects).toHaveTextContent(/planting spots are archived/);
    expect(effects).toHaveTextContent(/one entry "Bed cleared"/);
    expect(within(dialog).getByTestId('bed-clear-irreversible')).toHaveTextContent('Clearing cannot be undone.');
    expect(backend.bodies).toEqual([]);
  });

  it('offers the four termination types, "Harvested" by default', async () => {
    useClearBackend();
    const user = userEvent.setup();
    renderTab();

    const dialog = await openDialog(user);
    const group = within(dialog).getByRole('radiogroup', { name: 'How did the plants end?' });
    const radios = within(group).getAllByRole('radio');
    expect(radios.map((radio) => (radio as HTMLInputElement).value)).toEqual(['harvested', 'senesced', 'died', 'cancelled']);
    expect(within(group).getByRole('radio', { name: 'Harvested' })).toBeChecked();
  });

  it('sends one request with the chosen type and the note, then reloads the bed and says so', async () => {
    const backend = useClearBackend();
    const user = userEvent.setup();
    const { onChanged } = renderTab();
    await screen.findByTestId('planting-active-pl_1');
    const readsBefore = backend.plantingReads();

    const dialog = await openDialog(user);
    await user.click(within(dialog).getByRole('radio', { name: 'Died (loss)' }));
    await user.type(within(dialog).getByTestId('bed-clear-reason'), '  Frost night  ');
    await user.click(within(dialog).getByTestId('bed-clear-submit'));

    await waitFor(() => expect(screen.queryByTestId('bed-clear-dialog')).toBeNull());
    expect(backend.bodies).toEqual([{ key: 'loc_b03', body: { termination_type: 'died', reason: 'Frost night' } }]);
    expect(await screen.findByText('Bed cleared: 3 plants ended.')).toBeInTheDocument();
    // The same reload as every other action of the tab: the list is read again and the page reloads its summary.
    await waitFor(() => expect(backend.plantingReads()).toBe(readsBefore + 1));
    expect(onChanged).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByTestId('bed-planting-active')).toBeNull());
    expect(screen.getByTestId('bed-planting-finished')).toHaveTextContent('3 plants are harvested or removed');
    // Nothing stands any more, so there is nothing left to clear.
    expect(screen.queryByTestId('bed-clear-button')).toBeNull();
  });

  it('sends the default type without a note when the grower only confirms', async () => {
    const backend = useClearBackend();
    const user = userEvent.setup();
    renderTab('lead');

    const dialog = await openDialog(user);
    await user.click(within(dialog).getByTestId('bed-clear-submit'));

    await waitFor(() => expect(backend.bodies).toHaveLength(1));
    expect(backend.bodies[0]).toEqual({ key: 'loc_b03', body: { termination_type: 'harvested' } });
  });

  it('writes nothing when the dialog is cancelled', async () => {
    const backend = useClearBackend();
    const user = userEvent.setup();
    const { onChanged } = renderTab();

    const dialog = await openDialog(user);
    await user.click(within(dialog).getByTestId('bed-clear-cancel'));

    await waitFor(() => expect(screen.queryByTestId('bed-clear-dialog')).toBeNull());
    expect(backend.bodies).toEqual([]);
    expect(onChanged).not.toHaveBeenCalled();
    expect(screen.getByTestId('planting-active-pl_1')).toBeInTheDocument();
  });

  it('keeps the dialog open with the choice and shows the refusal when the server says no (409)', async () => {
    const backend = useClearBackend(() =>
      HttpResponse.json(
        {
          error_id: 'err_1',
          error_code: 'CONFLICT',
          message: 'The bed is being changed by another request.',
          details: [],
          timestamp: '',
          path: '',
          method: 'POST',
        },
        { status: 409 },
      ),
    );
    const user = userEvent.setup();
    const { onChanged } = renderTab();
    await screen.findByTestId('planting-active-pl_1');
    const readsBefore = backend.plantingReads();

    const dialog = await openDialog(user);
    await user.click(within(dialog).getByRole('radio', { name: 'Senesced (natural end)' }));
    await user.click(within(dialog).getByTestId('bed-clear-submit'));

    expect(await screen.findByText('Conflict: The resource has been modified.')).toBeInTheDocument();
    expect(backend.bodies).toHaveLength(1);
    const still = screen.getByTestId('bed-clear-dialog');
    await waitFor(() => expect(within(still).getByTestId('bed-clear-submit')).toBeEnabled());
    expect(within(still).getByRole('radio', { name: 'Senesced (natural end)' })).toBeChecked();
    expect(onChanged).not.toHaveBeenCalled();
    expect(backend.plantingReads()).toBe(readsBefore);
  });

  it('is not offered to a viewer', async () => {
    useClearBackend();
    renderTab('viewer');
    expect(await screen.findByTestId('planting-active-pl_1')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-clear-button')).toBeNull();
  });

  it('is not offered while the page shows cached data or is offline', async () => {
    useClearBackend();
    renderTab('grower', { editsLocked: true });
    expect(await screen.findByTestId('planting-active-pl_1')).toBeInTheDocument();
    expect(screen.getByTestId('bed-plant-button')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-clear-button')).toBeNull();
  });

  it('is not offered while nothing stands in the bed', async () => {
    server.use(
      http.get(`${BASE}/locations/:key/plantings`, () => HttpResponse.json([STANDING[3]])),
      http.get('/api/v1/species/:key', ({ params }) => HttpResponse.json(species(String(params.key), 'Basil'))),
    );
    renderTab();
    expect(await screen.findByTestId('planting-planned-s9')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-clear-button')).toBeNull();
  });

  it('the open dialog has no accessibility violations', async () => {
    useClearBackend();
    const user = userEvent.setup();
    renderTab();
    const dialog = await openDialog(user);
    await expectNoA11yViolations(dialog);
  });
});
