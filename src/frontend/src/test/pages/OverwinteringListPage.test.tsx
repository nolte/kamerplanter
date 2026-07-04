import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OverwinteringListPage from '@/pages/ueberwinterung/OverwinteringListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const listUrls = [
  '/api/v1/overwintering-profiles',
  '/api/v1/t/:tenant/overwintering-profiles',
];

const deleteUrls = [
  '/api/v1/overwintering-profiles/:key',
  '/api/v1/t/:tenant/overwintering-profiles/:key',
];

function useProfiles(rows: Record<string, unknown>[]) {
  server.use(...listUrls.map((u) => http.get(u, () => HttpResponse.json(rows))));
}

function useDeleteResponse(status: number) {
  server.use(
    ...deleteUrls.map((u) =>
      http.delete(u, () => new HttpResponse(null, { status })),
    ),
  );
}

function enableMobileViewport() {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
    } as unknown as MediaQueryList),
  );
}

const profile = {
  key: 'ow-1',
  plant_key: 'plant-1',
  planting_run_key: null,
  hardiness_zone_min: '7a',
  hardiness_rating: 'frost_free',
  winter_action: 'move_indoors',
  winter_action_month: 10,
  spring_action: 'move_outdoors',
  spring_action_month: 5,
  winter_quarter_key: null,
  winter_quarter_temp_min: 5,
  winter_quarter_temp_max: 12,
  winter_quarter_light: 'bright',
  winter_watering: 'minimal',
  storage_medium: null,
  storage_check_interval_days: null,
  tuber_status: null,
  notes: null,
  auto_generated: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

const runProfile = {
  ...profile,
  key: 'ow-2',
  plant_key: null,
  planting_run_key: 'run-77',
  hardiness_rating: 'needs_protection',
  winter_action: 'mulch',
  winter_action_month: 11,
  spring_action: null,
  spring_action_month: null,
  storage_medium: null,
  auto_generated: true,
};

const unlinkedProfile = {
  ...profile,
  key: 'ow-3',
  plant_key: null,
  planting_run_key: null,
  hardiness_rating: 'hardy',
  winter_action: 'none',
  winter_action_month: 12,
  auto_generated: false,
};

describe('OverwinteringListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the page title', async () => {
    useProfiles([]);
    renderWithProviders(<OverwinteringListPage />);
    await waitFor(() => {
      expect(screen.getByText(i18n.t('pages.overwintering.title'))).toBeTruthy();
    });
  });

  it('loads a profile and shows its hardiness chip and subject name', async () => {
    useProfiles([profile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-1')).toBeTruthy();
    });
    // plant-1 resolves to the mocked plant name "Big Red (TOM-001)"
    expect(screen.getByText(/Big Red/)).toBeTruthy();
    expect(
      screen.getByText(i18n.t('enums.hardinessRating.frost_free')),
    ).toBeTruthy();
  });

  it('shows the empty state with a create action', async () => {
    useProfiles([]);
    renderWithProviders(<OverwinteringListPage />);
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeTruthy();
    });
  });

  it('opens the create dialog when the create button is clicked', async () => {
    useProfiles([]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    const createButton = await screen.findByTestId('create-button');
    await user.click(createButton);

    expect(await screen.findByTestId('overwintering-dialog')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('renders the auto-generated chip and the planting-run subject fallback', async () => {
    useProfiles([runProfile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-2')).toBeTruthy();
    });
    // No plant_key → subjectLabel falls back to the planting_run_key.
    expect(screen.getAllByText('run-77').length).toBeGreaterThan(0);
    // auto_generated → the "Auto" chip is rendered.
    expect(
      screen.getAllByText(i18n.t('pages.overwintering.auto')).length,
    ).toBeGreaterThan(0);
  });

  it('renders an em dash when the profile has neither a plant nor a planting run', async () => {
    useProfiles([unlinkedProfile]);
    renderWithProviders(<OverwinteringListPage />);

    await waitFor(() => {
      expect(screen.getByTestId('hardiness-chip-ow-3')).toBeTruthy();
    });
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('opens the edit dialog when a row is clicked', async () => {
    useProfiles([profile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByText(/Big Red/));

    expect(await screen.findByTestId('overwintering-dialog')).toBeTruthy();
    expect(
      screen.getByText(i18n.t('pages.overwintering.edit')),
    ).toBeTruthy();
  });

  it('deletes a profile through the confirm dialog', async () => {
    useProfiles([profile]);
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('delete-ow-1'));

    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('surfaces an error when the delete request fails', async () => {
    useProfiles([profile]);
    useDeleteResponse(500);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('delete-ow-1'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    // Failure still closes the confirm dialog (finally clears deleteTarget)
    // and reports the error via a notification.
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('cancels the delete confirmation without calling the API', async () => {
    useProfiles([profile]);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    await user.click(await screen.findByTestId('delete-ow-1'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('renders mobile cards and deletes via the mobile action', async () => {
    enableMobileViewport();
    useProfiles([runProfile]);
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<OverwinteringListPage />);

    // Mobile card layout renders the auto chip and the mobile delete button.
    const mobileDelete = await screen.findByTestId('delete-mobile-ow-2');
    expect(
      screen.getAllByText(i18n.t('pages.overwintering.auto')).length,
    ).toBeGreaterThan(0);

    await user.click(mobileDelete);
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });
});
