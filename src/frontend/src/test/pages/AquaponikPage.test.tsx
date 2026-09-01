import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import AquaponikPage from '@/pages/aquaponik/AquaponikPage';
import RequireRole from '@/auth/RequireRole';
import { createStoreWithTenantRole, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const T = '/api/v1/t/:tenant/aquaponics';

function field(scope: HTMLElement, name: string): HTMLInputElement {
  const input = within(scope)
    .getByTestId(`form-field-${name}`)
    .querySelector('input');
  if (!input) throw new Error(`input for ${name} not found`);
  return input as HTMLInputElement;
}

const SYSTEM = {
  key: 'sys1',
  name: 'Tilapia-Salat DWC',
  system_type: 'dwc',
  total_volume_liters: 640,
  grow_area_m2: 4,
  cycling_status: 'cycling',
  has_clarifier: false,
  has_mineralization: false,
  has_vermicompost: false,
  daily_feed_target_g: 67.5,
  outdoor: false,
  backup_power: false,
  ph_target_min: 6.8,
  ph_target_max: 7.2,
};

function mockSystems(systems: unknown[]) {
  server.use(http.get(`${T}/systems`, () => HttpResponse.json(systems)));
}

function mockDetail(options: {
  cyclingProgress?: number;
  waterQuality?: unknown[];
  stocks?: unknown[];
} = {}) {
  server.use(
    http.get(`${T}/systems/:key/cycling-progress`, () =>
      HttpResponse.json({
        status: 'cycling',
        progress_percent: options.cyclingProgress ?? 57,
        stable_days: 4,
        days_required: 7,
        estimated_completion: null,
        phase_description_de: 'Biofilter fährt ein.',
        phase_description_en: 'Biofilter cycling.',
      }),
    ),
    http.get(`${T}/systems/:key/water-quality-status`, () =>
      HttpResponse.json(options.waterQuality ?? []),
    ),
    http.get(`${T}/systems/:key/fish-stocks`, () =>
      HttpResponse.json(options.stocks ?? []),
    ),
  );
}

describe('AquaponikPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockSystems([]);
    mockDetail();
  });

  it('renders the page title, intro and create button', async () => {
    renderWithProviders(<AquaponikPage />);
    await waitFor(() =>
      expect(screen.getByTestId('create-system-button')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('page-title')).toHaveTextContent('Aquaponik');
    expect(screen.getByText(/Stickstoffkreislauf/)).toBeInTheDocument();
  });

  it('shows the empty state when there are no systems', async () => {
    renderWithProviders(<AquaponikPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/Noch kein Aquaponik-System angelegt/),
      ).toBeInTheDocument(),
    );
  });

  it('lists systems and renders the detail panel with cycling progress', async () => {
    mockSystems([SYSTEM]);
    mockDetail({
      cyclingProgress: 57,
      stocks: [
        {
          key: 'stock1',
          system_key: 'sys1',
          name: 'Tilapia März',
          species_key: 'tilapia_nile',
          count: 15,
          initial_count: 15,
          avg_weight_g: 150,
          total_biomass_kg: 2.25,
          stocking_date: '2026-03-01',
          mortality_count: 0,
        },
      ],
    });
    renderWithProviders(<AquaponikPage />);

    await waitFor(() =>
      expect(screen.getByTestId('system-card-sys1')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('system-detail')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText(/Biofilter fährt ein/)).toBeInTheDocument(),
    );
    expect(screen.getByTestId('stock-stock1')).toHaveTextContent('Tilapia März');
  });

  it('surfaces a critical water-quality alert', async () => {
    mockSystems([SYSTEM]);
    mockDetail({
      waterQuality: [
        {
          parameter: 'free_ammonia',
          value: 0.065,
          limit: 0.02,
          severity: 'critical',
          message_de: 'Freies Ammoniak 0.065 mg/L kritisch.',
          message_en: 'Free ammonia critical.',
        },
      ],
    });
    renderWithProviders(<AquaponikPage />);
    await waitFor(() =>
      expect(screen.getByTestId('critical-alert')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('critical-alert')).toHaveTextContent(
      'Freies Ammoniak',
    );
  });

  it('creates a system through the dialog', async () => {
    const user = userEvent.setup();
    const created = vi.fn();
    server.use(
      http.post(`${T}/systems`, async ({ request }) => {
        created(await request.json());
        return HttpResponse.json({ ...SYSTEM, key: 'new1', cycling_status: 'new' }, { status: 201 });
      }),
    );
    renderWithProviders(<AquaponikPage />);
    await waitFor(() =>
      expect(screen.getByTestId('create-system-button')).toBeInTheDocument(),
    );

    await user.click(screen.getByTestId('create-system-button'));
    const dialog = await screen.findByRole('dialog');

    await user.type(field(dialog, 'name'), 'Mein System');
    await user.clear(field(dialog, 'total_volume_liters'));
    await user.type(field(dialog, 'total_volume_liters'), '640');
    await user.clear(field(dialog, 'grow_area_m2'));
    await user.type(field(dialog, 'grow_area_m2'), '4');

    // dwc requires a biofilter — select MBBR.
    const biofilter = within(dialog).getByTestId('form-field-biofilter_type');
    await user.click(within(biofilter).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /MBBR/ }));

    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created).toHaveBeenCalled());
    expect(created.mock.calls[0][0]).toMatchObject({
      name: 'Mein System',
      system_type: 'dwc',
      biofilter_type: 'mbbr',
    });
  });

  it('blocks system creation when biofilter is missing for DWC', async () => {
    const user = userEvent.setup();
    const posted = vi.fn();
    server.use(
      http.post(`${T}/systems`, () => {
        posted();
        return HttpResponse.json({}, { status: 201 });
      }),
    );
    renderWithProviders(<AquaponikPage />);
    await user.click(await screen.findByTestId('create-system-button'));
    const dialog = await screen.findByRole('dialog');
    await user.type(field(dialog, 'name'), 'Ohne Biofilter');
    await user.clear(field(dialog, 'total_volume_liters'));
    await user.type(field(dialog, 'total_volume_liters'), '100');
    await user.clear(field(dialog, 'grow_area_m2'));
    await user.type(field(dialog, 'grow_area_m2'), '2');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(posted).not.toHaveBeenCalled());
  });

  it('records a water test through the dialog', async () => {
    const user = userEvent.setup();
    mockSystems([SYSTEM]);
    mockDetail();
    const recorded = vi.fn();
    server.use(
      http.post(`${T}/systems/:key/water-tests`, async ({ request }) => {
        recorded(await request.json());
        return HttpResponse.json({ key: 'wt1' }, { status: 201 });
      }),
    );
    renderWithProviders(<AquaponikPage />);

    await waitFor(() =>
      expect(screen.getByTestId('record-water-test-button')).toBeInTheDocument(),
    );
    await user.click(screen.getByTestId('record-water-test-button'));
    const dialog = await screen.findByRole('dialog');

    await user.clear(field(dialog, 'ammonia_tan_mgl'));
    await user.type(field(dialog, 'ammonia_tan_mgl'), '1.5');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(recorded).toHaveBeenCalled());
    expect(recorded.mock.calls[0][0]).toMatchObject({ ammonia_tan_mgl: 1.5 });
  });

  it('hides the water-test action from a viewer under the route guard (#1261)', async () => {
    // The route's *second* write affordance. `POST …/water-tests` carries
    // `require_tenant_role(grower)` just like the header action, but it lives
    // inside the detail card where PageTitle cannot reach it — so the page reads
    // the restriction itself. Without this case the guard would look applied
    // while the doomed button stayed on screen.
    mockSystems([SYSTEM]);
    mockDetail();
    renderWithProviders(
      <RequireRole min="grower">
        <AquaponikPage />
      </RequireRole>,
      { store: createStoreWithTenantRole('viewer') },
    );

    // The read half must survive: the system is selected and its detail rendered.
    // (The name appears twice — in the selector and as the detail heading — so
    // assert on the detail body instead of on an ambiguous text match.)
    await waitFor(() =>
      expect(screen.getAllByText('Tilapia-Salat DWC').length).toBeGreaterThan(0),
    );
    expect(screen.getByTestId('system-detail')).toBeInTheDocument();
    expect(screen.getByTestId('role-restriction-notice')).toBeInTheDocument();
    expect(screen.queryByTestId('record-water-test-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('create-system-button')).not.toBeInTheDocument();
  });

  it('keeps the water-test action for a grower under the same guard', async () => {
    // The negative control for the case above, same page, same fixtures, only
    // the role differs — so a fixture that never renders the button cannot pass
    // for a working guard.
    mockSystems([SYSTEM]);
    mockDetail();
    renderWithProviders(
      <RequireRole min="grower">
        <AquaponikPage />
      </RequireRole>,
      { store: createStoreWithTenantRole('grower') },
    );

    await waitFor(() =>
      expect(screen.getByTestId('record-water-test-button')).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('role-restriction-notice')).not.toBeInTheDocument();
  });
});
