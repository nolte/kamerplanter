import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OverwinteringListPage from '@/pages/ueberwinterung/OverwinteringListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const listUrls = [
  '/api/v1/overwintering-profiles',
  '/api/v1/t/:tenant/overwintering-profiles',
];

function useProfiles(rows: Record<string, unknown>[]) {
  server.use(...listUrls.map((u) => http.get(u, () => HttpResponse.json(rows))));
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

describe('OverwinteringListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
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
});
