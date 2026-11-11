import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse, delay } from 'msw';
import i18n from 'i18next';
import SiteDetailPage from '@/pages/standorte/SiteDetailPage';
import {
  renderWithProviders,
  createStoreWithModuleOverrides,
  createStoreWithSmartHome,
  createTestStore,
  smartHomeState,
  tenantState,
} from '../helpers';
import { server } from '../mocks/server';

// Issue #587: sensor UI is gated behind the smart-home toggle. Render with smart
// home enabled by default; the disabled (hidden) case has a dedicated test.
const renderPage = () =>
  renderWithProviders(<SiteDetailPage />, { store: createStoreWithSmartHome() });

// #1467: the destructive controls are lead-only, so the rank has to be namable.
const renderPageAs = (role: 'viewer' | 'grower' | 'lead') =>
  renderWithProviders(<SiteDetailPage />, {
    store: createTestStore({ ...smartHomeState(), ...tenantState(role) }),
  });

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'site-1' }), useNavigate: () => mockNavigate };
});

const sensor = {
  key: 'sensor-1',
  name: 'Temp Sensor',
  metric_type: 'temperature',
  ha_entity_id: 'sensor.temp',
  is_active: true,
  parent_type: 'site',
  parent_key: 'site-1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

function errorEnvelope(status: number) {
  return HttpResponse.json(
    {
      error_id: 'e1',
      error_code: 'INTERNAL_ERROR',
      message: 'boom',
      details: [],
      timestamp: '',
      path: '',
      method: '',
    },
    { status },
  );
}

// site-1 is seeded in the shared handlers (mockSites, type greenhouse, no GPS).
function useSiteSensors(sensors: unknown[] = []) {
  server.use(
    http.get('/api/v1/t/:tenant/sites/:key/sensors', () => HttpResponse.json(sensors)),
  );
}

// Override the seeded site fetch (used by the redux fetchSite thunk).
function useSite(overrides: Record<string, unknown> = {}) {
  server.use(
    http.get('/api/v1/t/:tenant/sites/:key', () =>
      HttpResponse.json({
        key: 'site-1',
        name: 'Main Greenhouse',
        type: 'greenhouse',
        gps_coordinates: null,
        climate_zone: '8b',
        total_area_m2: 50,
        timezone: 'UTC',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        ...overrides,
      }),
    ),
  );
}

function useDeleteResponse(status: number) {
  server.use(
    http.delete('/api/v1/t/:tenant/sites/:key', () =>
      status < 400 ? new HttpResponse(null, { status }) : errorEnvelope(status),
    ),
  );
}

describe('SiteDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('offers the garden plan as a sub-item of the site while the module is on (REQ-042 §4.3)', async () => {
    renderPage();
    const link = await screen.findByTestId('garden-plan-open-link');
    expect(link).toHaveAttribute('href', '/standorte/sites/site-1/plan');
  });

  it('hides the garden plan entry when the module is switched off', async () => {
    renderWithProviders(<SiteDetailPage />, {
      store: createStoreWithModuleOverrides('expert', { garden_planner: 'disabled' }),
    });
    await screen.findByTestId('site-detail-page');
    expect(screen.queryByTestId('garden-plan-open-link')).toBeNull();
  });

  it('renders the site detail page from the loaded site', async () => {
    useSiteSensors();
    renderPage();

    expect(await screen.findByTestId('site-detail-page')).toBeTruthy();
    expect(screen.getAllByText('Main Greenhouse').length).toBeGreaterThan(0);
    // greenhouse without GPS => weather source hint about the missing coordinates.
    expect(await screen.findByTestId('weather-source-gps-hint')).toBeTruthy();
  });

  it('shows the loading skeleton while the site is being fetched', async () => {
    useSite();
    server.use(
      http.get('/api/v1/t/:tenant/sites/:key', async () => {
        await delay(40);
        return HttpResponse.json({
          key: 'site-1',
          name: 'Main Greenhouse',
          type: 'greenhouse',
          gps_coordinates: null,
          climate_zone: '8b',
          total_area_m2: 50,
          timezone: 'UTC',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: null,
        });
      }),
    );
    useSiteSensors();
    renderPage();

    // Skeleton first, then the page.
    expect(screen.queryByTestId('site-detail-page')).toBeNull();
    expect(await screen.findByTestId('site-detail-page')).toBeTruthy();
  });

  it('renders the error state when the site fetch fails', async () => {
    server.use(http.get('/api/v1/t/:tenant/sites/:key', () => errorEnvelope(500)));
    renderPage();

    expect(await screen.findByTestId('error-display')).toBeTruthy();
    expect(screen.queryByTestId('site-detail-page')).toBeNull();
  });

  it('shows the weather type hint for a non-outdoor site', async () => {
    useSite({ type: 'indoor' });
    useSiteSensors();
    renderPage();

    await screen.findByTestId('site-detail-page');
    expect(await screen.findByTestId('site-weather-type-hint')).toBeTruthy();
  });

  it('renders the weather source section for an outdoor site with GPS', async () => {
    useSite({ type: 'outdoor', gps_coordinates: [52.5, 13.4] });
    useSiteSensors();
    server.use(
      http.get('/api/v1/t/:tenant/sites/:key/weather-sources', () => HttpResponse.json([])),
    );
    renderPage();

    await screen.findByTestId('site-detail-page');
    // The GPS hint must NOT appear when coordinates are present.
    await waitFor(() =>
      expect(screen.queryByTestId('weather-source-gps-hint')).toBeNull(),
    );
  });

  it('treats a balcony as weather-relevant: no disabled hint, positive balcony hint shown', async () => {
    useSite({ type: 'balcony', gps_coordinates: null });
    useSiteSensors();
    renderPage();

    await screen.findByTestId('site-detail-page');
    // Balcony must NOT be treated as a non-weather type.
    await waitFor(() =>
      expect(screen.queryByTestId('site-weather-type-hint')).toBeNull(),
    );
    // Instead it explains why GPS/weather is available for a balcony.
    expect(await screen.findByTestId('site-balcony-weather-hint')).toBeTruthy();
    // Without GPS yet, the weather source still needs coordinates first.
    expect(await screen.findByTestId('weather-source-gps-hint')).toBeTruthy();
  });

  it('renders the weather source section for a balcony site with GPS', async () => {
    useSite({ type: 'balcony', gps_coordinates: [48.1, 11.6] });
    useSiteSensors();
    server.use(
      http.get('/api/v1/t/:tenant/sites/:key/weather-sources', () => HttpResponse.json([])),
    );
    renderPage();

    await screen.findByTestId('site-detail-page');
    expect(await screen.findByTestId('weather-source-section')).toBeTruthy();
    await waitFor(() =>
      expect(screen.queryByTestId('weather-source-gps-hint')).toBeNull(),
    );
  });

  it('keeps a windowsill site indoor: weather type hint shown, no weather section', async () => {
    useSite({ type: 'windowsill', gps_coordinates: [48.1, 11.6] });
    useSiteSensors();
    renderPage();

    await screen.findByTestId('site-detail-page');
    expect(await screen.findByTestId('site-weather-type-hint')).toBeTruthy();
    // Even with GPS present, an indoor type never unlocks the weather section.
    await waitFor(() =>
      expect(screen.queryByTestId('weather-source-section')).toBeNull(),
    );
    expect(screen.queryByTestId('site-balcony-weather-hint')).toBeNull();
  });

  it('saves the edited site and notifies success', async () => {
    useSite();
    useSiteSensors();
    let putBody: Record<string, unknown> | null = null;
    server.use(
      http.put('/api/v1/t/:tenant/sites/:key', async ({ request }) => {
        putBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ key: 'site-1', ...putBody });
      }),
    );
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(putBody).not.toBeNull());
    expect(putBody!.name).toBe('Main Greenhouse');
    expect(putBody!.type).toBe('greenhouse');
  });

  describe('garden-planning thresholds (REQ-053 WP 8.24)', () => {
    function capturePut() {
      const bodies: Record<string, unknown>[] = [];
      server.use(
        http.put('/api/v1/t/:tenant/sites/:key', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          bodies.push(body);
          return HttpResponse.json({ key: 'site-1', ...body });
        }),
      );
      return bodies;
    }
    const input = (name: string) => {
      const element = document.querySelector<HTMLInputElement>(`input[name="${name}"]`);
      if (!element) throw new Error(`no input ${name}`);
      return element;
    };

    it('shows the values the site answered and keeps them (null) on an unchanged save', async () => {
      useSite({
        reach_thresholds: { both_sides_m: 1.4, one_side_m: 0.7 },
        sun_class_thresholds: {
          full_sun_min_hours: 6,
          partial_shade_min_hours: 3,
          shade_min_hours: 2,
          reference_month: 6,
          reference_day: 21,
        },
      });
      useSiteSensors();
      const bodies = capturePut();
      const user = userEvent.setup();
      renderPage();

      expect(await screen.findByTestId('site-thresholds-section')).toBeInTheDocument();
      await waitFor(() => expect(input('reach_thresholds.both_sides_m').value).toBe('1.4'));
      expect(input('sun_class_thresholds.reference_day').value).toBe('21');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(bodies).toHaveLength(1));
      expect(bodies[0].sun_class_thresholds).toBeNull();
      expect(bodies[0].reach_thresholds).toBeNull();
      expect(bodies[0].window_thresholds).toBeNull();
    });

    it('sends a changed reach threshold and leaves the sun classes alone', async () => {
      useSite();
      useSiteSensors();
      const bodies = capturePut();
      const user = userEvent.setup();
      renderPage();

      await screen.findByTestId('site-thresholds-section');
      await waitFor(() => expect(input('reach_thresholds.one_side_m').value).toBe('0.6'));
      await user.clear(input('reach_thresholds.one_side_m'));
      await user.type(input('reach_thresholds.one_side_m'), '0.8');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(bodies).toHaveLength(1));
      expect(bodies[0].reach_thresholds).toEqual({ both_sides_m: 1.2, one_side_m: 0.8, path_access_max_distance_m: 0.3 });
      expect(bodies[0].sun_class_thresholds).toBeNull();
    });

    it('sends a changed path distance and explains it next to the field (#2703)', async () => {
      useSite();
      useSiteSensors();
      const bodies = capturePut();
      const user = userEvent.setup();
      renderPage();

      await screen.findByTestId('site-thresholds-section');
      expect(screen.getByText(i18n.t('pages.sites.thresholds.pathDistanceHelper'))).toBeInTheDocument();
      await waitFor(() => expect(input('reach_thresholds.path_access_max_distance_m').value).toBe('0.3'));
      await user.clear(input('reach_thresholds.path_access_max_distance_m'));
      await user.type(input('reach_thresholds.path_access_max_distance_m'), '0.5');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(bodies).toHaveLength(1));
      expect(bodies[0].reach_thresholds).toEqual({ both_sides_m: 1.2, one_side_m: 0.6, path_access_max_distance_m: 0.5 });
    });

    it('sends a changed window radius and leaves the other thresholds alone (GP-FR-181, WP 10.7)', async () => {
      useSite();
      useSiteSensors();
      const bodies = capturePut();
      const user = userEvent.setup();
      renderPage();

      await screen.findByTestId('site-thresholds-section');
      expect(screen.getByText(i18n.t('pages.sites.thresholds.windowRadiusHelper'))).toBeInTheDocument();
      await waitFor(() => expect(input('window_thresholds.suggestion_radius_m').value).toBe('1.5'));
      await user.clear(input('window_thresholds.suggestion_radius_m'));
      await user.type(input('window_thresholds.suggestion_radius_m'), '2.5');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(bodies).toHaveLength(1));
      expect(bodies[0].window_thresholds).toEqual({ suggestion_radius_m: 2.5 });
      expect(bodies[0].reach_thresholds).toBeNull();
      expect(bodies[0].sun_class_thresholds).toBeNull();
    });

    it('refuses sun-class bounds that are not descending and sends nothing', async () => {
      useSite();
      useSiteSensors();
      const bodies = capturePut();
      const user = userEvent.setup();
      renderPage();

      await screen.findByTestId('site-thresholds-section');
      await waitFor(() => expect(input('sun_class_thresholds.partial_shade_min_hours').value).toBe('3'));
      await user.clear(input('sun_class_thresholds.partial_shade_min_hours'));
      await user.type(input('sun_class_thresholds.partial_shade_min_hours'), '7');
      await user.click(screen.getByTestId('form-submit-button'));

      expect(await screen.findByText(i18n.t('pages.sites.thresholds.partialBelowFull'))).toBeInTheDocument();
      expect(bodies).toHaveLength(0);
    });

    it('puts the default thresholds back with the reset button', async () => {
      useSite();
      useSiteSensors();
      const user = userEvent.setup();
      renderPage();

      await screen.findByTestId('site-thresholds-section');
      await waitFor(() => expect(input('reach_thresholds.both_sides_m').value).toBe('1.2'));
      await user.clear(input('reach_thresholds.one_side_m'));
      await user.type(input('reach_thresholds.one_side_m'), '0.9');
      await user.click(screen.getByTestId('site-thresholds-reset'));

      await waitFor(() => expect(input('reach_thresholds.one_side_m').value).toBe('0.6'));
    });

    it('is not offered while the garden planner module is switched off', async () => {
      renderWithProviders(<SiteDetailPage />, {
        store: createStoreWithModuleOverrides('expert', { garden_planner: 'disabled' }),
      });
      await screen.findByTestId('site-detail-page');
      expect(screen.queryByTestId('site-thresholds-section')).toBeNull();
    });
  });

  it('surfaces an API error when saving the site fails', async () => {
    useSite();
    useSiteSensors();
    server.use(http.put('/api/v1/t/:tenant/sites/:key', () => errorEnvelope(500)));
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('navigates back when cancelling the form', async () => {
    useSiteSensors();
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('renders the sensor table and opens the create dialog', async () => {
    useSiteSensors([sensor]);
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    expect(await screen.findByText('Temp Sensor')).toBeTruthy();

    await user.click(screen.getByTestId('add-sensor-button'));
    expect(await screen.findByRole('dialog')).toBeTruthy();
  });

  it('hides the sensor section when smart home is disabled (#587)', async () => {
    useSiteSensors([sensor]);
    // Default store → smart_home_enabled falsy → sensor surfaces hidden.
    renderWithProviders(<SiteDetailPage />);

    await screen.findByTestId('site-detail-page');
    expect(screen.queryByTestId('site-sensors-section')).toBeNull();
    expect(screen.queryByTestId('add-sensor-button')).toBeNull();
    expect(screen.queryByText('Temp Sensor')).toBeNull();
  });

  it('opens the sensor edit dialog from the row action', async () => {
    useSiteSensors([sensor]);
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    const sensorRow = (await screen.findByText('Temp Sensor')).closest('tr')!;
    await user.click(within(sensorRow).getByTestId('EditIcon').closest('button')!);
    expect(await screen.findByRole('dialog')).toBeTruthy();
  });

  it('renders the sensor list as mobile cards on a small screen', async () => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }));
    useSiteSensors([sensor]);
    renderPage();

    await screen.findByTestId('site-detail-page');
    expect(await screen.findAllByText('Temp Sensor')).toBeTruthy();
    vi.unstubAllGlobals();
  });

  it('deletes a sensor through its confirm dialog', async () => {
    useSiteSensors([sensor]);
    // Registered on `/tanks/sensors/{key}` until #1339 — a path no backend route
    // has ever served. The doubled boundary answered it anyway, so this test was
    // green while every real delete returned 404. The concrete pathname is
    // asserted, because a pattern handler also matches a call with the sensor
    // key in the parent position.
    let deleteCalled: string | null = null;
    server.use(
      http.delete('/api/v1/t/:tenant/sites/:siteKey/sensors/:key', ({ request }) => {
        deleteCalled = new URL(request.url).pathname;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    const sensorRow = (await screen.findByText('Temp Sensor')).closest('tr')!;
    await user.click(within(sensorRow).getByTestId('DeleteIcon').closest('button')!);

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));
    await waitFor(() =>
      expect(deleteCalled).toBe('/api/v1/t/test-tenant/sites/site-1/sensors/sensor-1'),
    );
  });

  it('surfaces an error when sensor deletion fails', async () => {
    useSiteSensors([sensor]);
    server.use(
      http.delete('/api/v1/t/:tenant/sites/:siteKey/sensors/:key', () => errorEnvelope(500)),
    );
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    const sensorRow = (await screen.findByText('Temp Sensor')).closest('tr')!;
    await user.click(within(sensorRow).getByTestId('DeleteIcon').closest('button')!);
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('offers neither destructive control to a grower, both to a lead (#1467)', async () => {
    useSiteSensors([sensor]);

    const { unmount } = renderPageAs('grower');
    await screen.findByTestId('site-detail-page');
    await screen.findByText('Temp Sensor');
    expect(screen.queryByTestId('site-delete-button')).toBeNull();
    expect(screen.queryByTestId('site-sensor-delete-button')).toBeNull();
    unmount();

    renderPageAs('lead');
    await screen.findByTestId('site-detail-page');
    await screen.findByText('Temp Sensor');
    expect(screen.getByTestId('site-delete-button')).toBeInTheDocument();
    expect(screen.getByTestId('site-sensor-delete-button')).toBeInTheDocument();
  });

  it('deletes the site through the confirm dialog and navigates to the list', async () => {
    useSiteSensors();
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/standorte/sites'),
    );
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('shows the pending state on the delete dialog while deleting', async () => {
    useSiteSensors();
    server.use(
      http.delete('/api/v1/t/:tenant/sites/:key', async () => {
        await delay(60);
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toBeDisabled(),
    );
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/standorte/sites'),
    );
  });

  it('surfaces an error and does not navigate when deletion fails', async () => {
    useSiteSensors();
    useDeleteResponse(500);
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
    expect(mockNavigate).not.toHaveBeenCalledWith('/standorte/sites');
  });

  it('cancels the delete confirmation without deleting', async () => {
    useSiteSensors();
    const user = userEvent.setup();
    renderPage();

    await screen.findByTestId('site-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
    expect(mockNavigate).not.toHaveBeenCalledWith('/standorte/sites');
  });
});
