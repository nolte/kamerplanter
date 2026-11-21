/**
 * #3037 SCR-008 / SCR-010 / SCR-011 — the section banner of `PlantingRunDetailPage`.
 *
 * - A run without a plan (`{ plan: null }`) is the empty case: no banner, and
 *   "no plan assigned" with its assign call to action.
 * - A 500 from the plan read raises the banner instead, without that call to
 *   action; the retry then shows the plan.
 * - A failure in the second leg of the watering load (plan entries) is one
 *   cause with one message: the banner, no toast.
 * - A failed location read on a sibling switch does not keep the previous
 *   run's site.
 */
import type { ReactElement } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { setActiveTenantSlug } from '@/api/client';
import { ThemeContextProvider } from '@/theme';
import { createStoreWithSmartHome } from '../helpers';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';

// The edit dialog is replaced by a probe that prints the site it would preselect.
vi.mock('@/pages/durchlaeufe/PlantingRunEditDialog', () => ({
  default: ({ initialSiteKey }: { initialSiteKey: string | null }) => (
    <div data-testid="edit-dialog-initial-site">{initialSiteKey ?? 'none'}</div>
  ),
}));
vi.mock('@/pages/durchlaeufe/PlantingRunDetailsTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/PlantingRunPlantsTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/ActivityPlanTab', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/RunPhaseEditor', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/PhaseKamiTimeline', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/BatchPhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/AdoptPlantsDialog', () => ({ default: () => null }));
vi.mock('@/pages/durchlaeufe/WateringConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));

import PlantingRunDetailPage from '@/pages/durchlaeufe/PlantingRunDetailPage';

const T = '/api/v1/t/:tenant';
const ERROR_BODY = { error_id: 'e', error_code: 'X', message: 'boom', details: [] };
const PLAN = { key: 'np-1', name: 'Tomato Plan' };

function runFor(key: string, locationKey: string | null = null): Record<string, unknown> {
  return {
    key,
    name: `Run ${key.toUpperCase()}`,
    run_type: 'monoculture',
    status: 'active',
    planned_quantity: 3,
    actual_quantity: 0,
    current_phase_key: null,
    current_phase_started_at: null,
    lifecycle_config_key: null,
    location_key: locationKey,
    substrate_batch_key: null,
    planned_start_date: null,
    started_at: null,
    completed_at: null,
    source_plant_key: null,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

/** Serves the run's reads; `planResponder` replaces the plan leg. */
function seedRun(planResponder: () => Response = () => HttpResponse.json({ plan: null })) {
  const calls = { plan: 0 };
  server.use(
    http.get(`${T}/planting-runs/:key`, ({ params }) => HttpResponse.json(runFor(String(params.key)))),
    http.get(`${T}/planting-runs/:key/entries`, () => HttpResponse.json([])),
    http.get(`${T}/planting-runs/:key/plants`, () => HttpResponse.json([])),
    http.get(`${T}/planting-runs/:key/nutrient-plan`, () => {
      calls.plan += 1;
      return planResponder();
    }),
    http.get(`${T}/planting-runs/:key/watering-schedule`, () => HttpResponse.json(null)),
    http.get(`${T}/planting-runs/:key/phase-timeline`, () => HttpResponse.json([])),
    http.get(`${T}/planting-runs/:key/active-channels`, () => HttpResponse.json([])),
    http.get('*/nutrient-plans/:key/entries', () => HttpResponse.json([])),
    http.get('*/fertilizers', () => HttpResponse.json([])),
    http.get(`${T}/sites`, () => HttpResponse.json([])),
  );
  return calls;
}

function renderAt(ui: ReactElement, path: string) {
  const router = createMemoryRouter([{ path: '/detail/:key', element: ui }], {
    initialEntries: [path],
  });
  render(
    <Provider store={createStoreWithSmartHome()}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return router;
}

async function openNutrientTab(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByTestId('nutrient-plan-tab', {}, { timeout: WAIT_BUDGET }));
  await screen.findByTestId('nutrient-watering-tab', {}, { timeout: WAIT_BUDGET });
}

describe('PlantingRunDetailPage — section load banner (#3037)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(async () => {
    cleanup();
    await i18n.changeLanguage('en');
  });

  it('shows "no plan assigned" and no banner for a run without a plan', async () => {
    const calls = seedRun();
    const user = userEvent.setup();
    renderAt(<PlantingRunDetailPage />, '/detail/a');

    await openNutrientTab(user);
    expect(await screen.findByTestId('run-no-plan-assigned', {}, { timeout: WAIT_BUDGET })).toBeInTheDocument();
    expect(calls.plan).toBeGreaterThan(0);
    expect(screen.queryByTestId('run-section-load-error')).toBeNull();
  });

  it('flags a failed plan read without the assign call to action, and shows the plan after the retry', async () => {
    let failPlan = true;
    seedRun(() =>
      failPlan ? HttpResponse.json(ERROR_BODY, { status: 500 }) : HttpResponse.json({ plan: PLAN }),
    );
    const user = userEvent.setup();
    renderAt(<PlantingRunDetailPage />, '/detail/a');

    await openNutrientTab(user);
    await screen.findByTestId('run-section-load-error', {}, { timeout: WAIT_BUDGET });
    expect(screen.queryByTestId('run-no-plan-assigned')).toBeNull();
    expect(screen.queryByText(i18n.t('pages.nutrientPlans.noPlanAssigned'))).toBeNull();

    failPlan = false;
    await user.click(screen.getByTestId('run-section-load-error-retry'));

    expect(await screen.findByText('Tomato Plan', {}, { timeout: WAIT_BUDGET })).toBeInTheDocument();
    expect(screen.queryByTestId('run-section-load-error')).toBeNull();
  });

  it('announces a failed second watering leg by the banner only, not by a toast', async () => {
    seedRun(() => HttpResponse.json({ plan: PLAN }));
    server.use(http.get('*/nutrient-plans/:key/entries', () => HttpResponse.json(ERROR_BODY, { status: 500 })));
    const user = userEvent.setup();
    renderAt(<PlantingRunDetailPage />, '/detail/a');

    await openNutrientTab(user);
    await screen.findByTestId('run-section-load-error', {}, { timeout: WAIT_BUDGET });
    // The toast is notistack's snackbar; useApiError words a 500 as errors.server.
    expect(screen.queryByText(i18n.t('errors.server'))).toBeNull();
  });

  it("drops the previous run's site when the next run's location read fails", async () => {
    seedRun();
    server.use(
      http.get(`${T}/planting-runs/:key`, ({ params }) => {
        const key = String(params.key);
        return HttpResponse.json(runFor(key, `loc-${key}`));
      }),
      http.get(`${T}/locations/:key`, ({ params }) =>
        params.key === 'loc-a'
          ? HttpResponse.json({ key: 'loc-a', name: 'Tent A', site_key: 'site-a', tank_key: null })
          : HttpResponse.json(ERROR_BODY, { status: 500 }),
      ),
      http.get(`${T}/tanks`, () => HttpResponse.json([])),
    );
    const router = renderAt(<PlantingRunDetailPage />, '/detail/a');

    await waitFor(
      () => expect(screen.getByTestId('edit-dialog-initial-site').textContent).toBe('site-a'),
      { timeout: WAIT_BUDGET },
    );

    await act(async () => {
      await router.navigate('/detail/b');
    });
    await screen.findByTestId('run-section-load-error', {}, { timeout: WAIT_BUDGET });
    expect(screen.getByTestId('edit-dialog-initial-site').textContent).toBe('none');
  });
});
