import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { setActiveTenantSlug } from '@/api/client';

// The detail page reads its run key from the route via useParams. Provide a
// stable key without depending on a matched route path.
const RUN_KEY = 'run-1';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: RUN_KEY }),
  };
});

// Stub the heavy tab/dialog children: none are relevant to the run-batch
// "complete harvest" header action, and they pull redux/API state the shared
// test store does not preload. The header + the shared ConfirmDialog stay real.
vi.mock('@/pages/durchlaeufe/PlantingRunDetailsTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/PlantingRunPlantsTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/PlantingRunNutrientWateringTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/ActivityPlanTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/RunPhaseEditor', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/PhaseKamiTimeline', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/BatchPhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/PlantingRunEditDialog', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/AdoptPlantsDialog', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/WateringConfirmDialog', () => ({ default: () => null }));

import PlantingRunDetailPage from '@/pages/durchlaeufe/PlantingRunDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const SCOPED = '/api/v1/t/:tenant';

interface RunOptions {
  status?: string;
  activePlants?: number;
}

/** Seed the run detail-page load path plus a POST capture for run harvest. */
function seedRun({ status = 'active', activePlants = 2 }: RunOptions = {}) {
  const completeCalls: Array<{ body: unknown }> = [];
  const plants = Array.from({ length: activePlants }, (_, i) => ({
    key: `p-${i}`,
    instance_id: `RUN-${i}`,
    species_key: 'sp-1',
    plant_name: null,
    current_phase: 'flowering',
    planted_on: '2026-01-01',
    removed_on: null,
    detached_at: null,
  }));

  server.use(
    http.get(`${SCOPED}/planting-runs/:key`, () =>
      HttpResponse.json({
        key: RUN_KEY,
        name: 'Tomato Run',
        run_type: 'batch',
        status,
        location_key: null,
        planned_quantity: activePlants,
        actual_quantity: activePlants,
        started_at: '2026-01-01T00:00:00Z',
        phase_summary: null,
      }),
    ),
    http.get(`${SCOPED}/planting-runs/:key/entries`, () => HttpResponse.json([])),
    http.get(`${SCOPED}/planting-runs/:key/plants`, () => HttpResponse.json(plants)),
    http.get(`${SCOPED}/planting-runs/:key/nutrient-plan`, () =>
      HttpResponse.json({ plan: null }),
    ),
    http.get(`${SCOPED}/planting-runs/:key/phase-timeline`, () => HttpResponse.json([])),
    http.get(`${SCOPED}/planting-runs/:key/watering-schedule`, () =>
      HttpResponse.json(null),
    ),
    http.get(`${SCOPED}/sites`, () => HttpResponse.json([])),
    http.post(`${SCOPED}/harvest/runs/:key/complete`, async ({ request }) => {
      completeCalls.push({ body: await request.json() });
      return HttpResponse.json({
        run_key: RUN_KEY,
        completed_count: activePlants,
        completed_keys: plants.map((p) => p.key),
      });
    }),
  );
  return { completeCalls };
}

describe('PlantingRunDetailPage — run-batch complete harvest (REQ-007/013)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  const QUERY_TIMEOUT = { timeout: 5000 } as const;

  it('shows the complete-harvest action for an active run and posts on confirm', async () => {
    const { completeCalls } = seedRun({ status: 'active', activePlants: 2 });
    const user = userEvent.setup();

    renderWithProviders(<PlantingRunDetailPage />);

    const button = await screen.findByTestId('complete-harvest-button', {}, QUERY_TIMEOUT);
    await user.click(button);

    const dialog = await screen.findByTestId('confirm-dialog', {}, QUERY_TIMEOUT);
    // Confirm text carries the active-plant count.
    expect(within(dialog).getByText(/2/)).toBeTruthy();

    await user.click(within(dialog).getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(completeCalls.length).toBe(1), QUERY_TIMEOUT);
    // Empty body (no explicit back-date) → terminate as of today.
    expect(completeCalls[0].body).toEqual({});
  });

  it('hides the complete-harvest action for a planned run', async () => {
    seedRun({ status: 'planned', activePlants: 3 });

    renderWithProviders(<PlantingRunDetailPage />);

    // The create-plants button is the planned-state marker; wait for it first.
    await screen.findByTestId('create-plants-button', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('complete-harvest-button')).toBeNull();
  });
});
