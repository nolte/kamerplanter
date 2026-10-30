/**
 * The irrigation layers over time and under failure (REQ-053 WP 7.6 / 7.7, #2534): the "days since" classes move on
 * at midnight UTC without a reload, and a zone panel chunk that cannot load leaves the plan usable and offers the
 * reload that fixes it.
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';

const chunk = vi.hoisted(() => ({ fail: false }));

// The real panel module unless a test makes its chunk fail, as a deploy that removed the old chunk does. The
// failure sits in the export, not in the module evaluation: the module and the resolved `lazy()` are cached for
// the whole file, so a failure decided at evaluation would depend on whether an earlier test loaded the panel.
// `lazy()` reads `default` on every render, so this fails the panel whatever ran before.
vi.mock('@/features/gardenPlanner/zones/ZonePanel', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/gardenPlanner/zones/ZonePanel')>();
  return {
    get default() {
      if (chunk.fail) throw new TypeError('Failed to fetch dynamically imported module');
      return actual.default;
    },
  };
});

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';

function usePlan(lastWateredAt: string) {
  server.use(
    http.get(PLAN_URL, () =>
      HttpResponse.json(
        planResponse({
          locations: [bed('loc_a', 2, 2, { name: 'North bed', irrigation_zone_key: 'z1', last_watered_at: lastWateredAt })],
          garden_objects: [],
          zones: [{ key: 'z1', name: 'Drip line', irrigation_type: 'drip', color: '#2E7D32', location_keys: ['loc_a'] }],
        }),
      ),
    ),
    http.get('/api/v1/t/:tenant/sites/:key/irrigation-zones', () => HttpResponse.json([])),
  );
}

function renderRoute() {
  const store = configureStore({ reducer: rootReducer });
  const router = createMemoryRouter([{ path: 'standorte/sites/:key/plan', element: <GardenPlanRoute /> }], {
    initialEntries: ['/standorte/sites/site_1/plan?mode=plan'],
  });
  return render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
}

beforeEach(() => window.localStorage.clear());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
  chunk.fail = false;
  window.localStorage.clear();
});

describe('the last-watered layer over midnight', () => {
  it('moves a bed into the next class once the UTC day changes, without a reload', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true, toFake: ['Date', 'setInterval', 'clearInterval'] });
    vi.setSystemTime(new Date('2026-10-30T23:59:30Z'));
    usePlan('2026-10-27T10:00:00Z');
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-lastWatered'));
    const cls = () => container.querySelector('[data-watered-bed="loc_a"]')?.getAttribute('data-watered-class');
    // 27th to 30th: three days since.
    expect(cls()).toBe('d2_3');
    await act(async () => {
      vi.advanceTimersByTime(60_000);
    });
    // Past midnight UTC it is the 31st: four days since.
    await waitFor(() => expect(cls()).toBe('d4_7'));
  });
});

describe('a zone panel chunk that cannot load', () => {
  // Runs first on purpose: the panel module is loaded (and its `lazy()` resolved) before the failure test.
  it('loads the real panel while the chunk is there', async () => {
    usePlan(new Date().toISOString());
    renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-zones-open'));
    expect(await screen.findByTestId('garden-plan-zone-panel')).toBeInTheDocument();
  });

  it('keeps the plan, says what happened and offers a reload instead of a retry that fails again', async () => {
    chunk.fail = true;
    usePlan(new Date().toISOString());
    const reload = vi.fn();
    vi.spyOn(window, 'location', 'get').mockReturnValue({ ...window.location, reload });
    renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-zones-open'));
    const fallback = await screen.findByTestId('garden-plan-zone-panel-error');
    expect(fallback).toHaveTextContent('The zones area could not be loaded');
    expect(fallback).toHaveTextContent('Save your plan, then reload the page');
    expect(screen.getByTestId('garden-plan-canvas')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Reload page' }));
    expect(reload).toHaveBeenCalled();
  });
});

describe('after the chunk test', () => {
  it('window.location is the real one again', () => {
    expect(vi.isMockFunction(window.location.reload)).toBe(false);
  });
});
