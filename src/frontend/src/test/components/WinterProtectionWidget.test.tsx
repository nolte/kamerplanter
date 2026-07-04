import { screen, waitFor, within } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import WinterProtectionWidget from '@/components/dashboard/WinterProtectionWidget';
import type { WinterHardinessOverview } from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const overviewUrls = [
  '/api/v1/overwintering-profiles/hardiness-overview',
  '/api/v1/t/:tenant/overwintering-profiles/hardiness-overview',
];

function useOverview(body: WinterHardinessOverview) {
  server.use(...overviewUrls.map((u) => http.get(u, () => HttpResponse.json(body))));
}

describe('WinterProtectionWidget', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the traffic-light counts from the overview', async () => {
    useOverview({
      green: 5,
      yellow: 3,
      red: 2,
      total: 10,
      red_plants: [],
    });
    renderWithProviders(<WinterProtectionWidget />);

    await waitFor(() => {
      expect(screen.getByTestId('winter-count-green').textContent).toBe('5');
    });
    expect(screen.getByTestId('winter-count-yellow').textContent).toBe('3');
    expect(screen.getByTestId('winter-count-red').textContent).toBe('2');
  });

  it('lists the red (must-relocate) plants with their winter action', async () => {
    useOverview({
      green: 0,
      yellow: 0,
      red: 1,
      total: 1,
      red_plants: [
        {
          profile_key: 'ow-red-1',
          plant_key: 'Dahlie',
          planting_run_key: null,
          hardiness_rating: 'dig_and_store',
          winter_action: 'dig_store',
        },
      ],
    });
    renderWithProviders(<WinterProtectionWidget />);

    const row = await screen.findByTestId('winter-red-ow-red-1');
    expect(within(row).getByText('Dahlie')).toBeTruthy();
    expect(within(row).getByText(i18n.t('enums.winterAction.dig_store'))).toBeTruthy();
  });

  it('shows the empty state when there are no profiles', async () => {
    useOverview({ green: 0, yellow: 0, red: 0, total: 0, red_plants: [] });
    renderWithProviders(<WinterProtectionWidget />);

    await waitFor(() => {
      expect(screen.getByTestId('winter-protection-empty')).toBeTruthy();
    });
  });

  it('shows an error alert instead of the empty state when the overview fetch fails (F4)', async () => {
    server.use(
      ...overviewUrls.map((u) =>
        http.get(u, () => new HttpResponse(null, { status: 500 })),
      ),
    );
    renderWithProviders(<WinterProtectionWidget />);

    await waitFor(() => {
      expect(screen.getByTestId('winter-protection-error')).toBeTruthy();
    });
    expect(
      screen.getByText(i18n.t('pages.dashboard.winterProtection.error')),
    ).toBeTruthy();
    expect(screen.queryByTestId('winter-protection-empty')).toBeNull();
  });
});
