/**
 * The underlay dialog under failure (REQ-053 GP-FR-033, #2545): a dialog chunk that cannot load - typically gone
 * after a deploy - or a dialog that fails to render says so in place and leaves the plan usable, with the reload
 * that fixes it instead of a retry that would fail the same way.
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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

const failure = vi.hoisted(() => ({ mode: 'none' as 'none' | 'chunk' | 'render' }));

// The real dialog module unless a test makes it fail. The failure sits in the export, not in the module
// evaluation: `lazy()` reads `default` on every render, so this fails the dialog whatever ran before.
vi.mock('@/features/gardenPlanner/underlay/UnderlayDialog', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/gardenPlanner/underlay/UnderlayDialog')>();
  const Broken = () => {
    throw new Error('the underlay dialog failed to render');
  };
  return {
    get default() {
      if (failure.mode === 'chunk') throw new TypeError('Failed to fetch dynamically imported module');
      return failure.mode === 'render' ? Broken : actual.default;
    },
  };
});

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';

function usePlan() {
  server.use(
    http.get(PLAN_URL, () =>
      HttpResponse.json(planResponse({ locations: [bed('loc_a', 2, 2, { name: 'North bed' })], garden_objects: [] })),
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

beforeEach(() => {
  window.localStorage.clear();
  // React reports the caught error on the console; the boundary turning it into the fallback is what is tested.
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  failure.mode = 'none';
  window.localStorage.clear();
});

describe('an underlay dialog that cannot be shown', () => {
  // Runs first on purpose: the dialog module is loaded (and its `lazy()` resolved) before the failure tests.
  it('opens the real dialog while the chunk is there', async () => {
    usePlan();
    renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-underlay-open'));
    expect(await screen.findByTestId('garden-plan-underlay-dialog')).toBeInTheDocument();
  });

  it.each(['chunk', 'render'] as const)(
    'keeps the plan, says what happened and offers a reload (%s failure)',
    async (mode) => {
      failure.mode = mode;
      usePlan();
      const reload = vi.fn();
      vi.spyOn(window, 'location', 'get').mockReturnValue({ ...window.location, reload });
      renderRoute();
      fireEvent.click(await screen.findByTestId('garden-plan-underlay-open'));

      const fallback = await screen.findByTestId('garden-plan-underlay-error');
      expect(fallback).toHaveTextContent('The underlay dialog could not be opened');
      expect(fallback).toHaveTextContent('Save your plan, then reload the page');
      expect(screen.getByTestId('garden-plan-canvas')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Retry' })).toBeNull();
      fireEvent.click(screen.getByRole('button', { name: 'Reload page' }));
      expect(reload).toHaveBeenCalled();
    },
  );
});

describe('after the failure tests', () => {
  it('window.location is the real one again', () => {
    expect(vi.isMockFunction(window.location.reload)).toBe(false);
  });
});
