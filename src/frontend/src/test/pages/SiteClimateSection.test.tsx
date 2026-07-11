import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '@/test/helpers';
import SiteClimateSection from '@/pages/standorte/SiteClimateSection';

/**
 * REQ-041 — "Klima am Standort" section: renders the NASA POWER climate normals,
 * the CC-BY attribution (licence gate) and the reanalysis provenance badge, with
 * a graceful empty state and a retry on error.
 */

vi.mock('@/api/endpoints/weatherSources', () => ({
  getSiteClimateNormals: vi.fn(),
}));

import { getSiteClimateNormals } from '@/api/endpoints/weatherSources';
import type { ClimateNormal, SiteClimateResponse } from '@/api/types';

const mockGet = vi.mocked(getSiteClimateNormals);

const normal: ClimateNormal = {
  source: 'nasa-power',
  attribution: 'Klima- und Strahlungsdaten: NASA POWER (power.larc.nasa.gov)',
  period_start_year: 2001,
  period_end_year: 2020,
  monthly_temp_min_c: [-3, -1, 2, 5, 9, 12, 14, 13.5, 10, 6, 1, -2],
  monthly_temp_max_c: [],
  monthly_temp_avg_c: [0, 1, 5, 9, 14, 17, 19, 18.5, 14, 9, 4, 1],
  monthly_precip_mm: [40, 35, 45, 40, 55, 60, 65, 60, 50, 45, 48, 50],
  monthly_solar_mj_m2: [3, 5, 9, 14, 18, 20, 19, 16, 12, 7, 4, 2.5],
  coldest_month_min_c: -3,
  annual_temp_avg_c: 10.5,
  annual_precip_mm: 593,
  fetched_at: '2026-07-01T04:00:00Z',
};

function response(overrides: Partial<SiteClimateResponse> = {}): SiteClimateResponse {
  return { site_key: 'site-1', normals: [normal], ...overrides };
}

describe('SiteClimateSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the climate normals with the CC-BY attribution and provenance badge', async () => {
    mockGet.mockResolvedValue(response());

    renderWithProviders(<SiteClimateSection siteKey="site-1" />);

    // Licence gate — the NASA POWER attribution is visible in the UI.
    expect(await screen.findByTestId('climate-attribution')).toHaveTextContent('NASA POWER');
    // Provenance badge labels the source and the reanalysis kind (EN test locale).
    expect(screen.getByText('NASA POWER')).toBeInTheDocument();
    expect(screen.getByText('Reanalysis')).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('site-1');
  });

  it('shows the empty state when no normals are populated yet', async () => {
    mockGet.mockResolvedValue(response({ normals: [] }));

    renderWithProviders(<SiteClimateSection siteKey="site-1" />);

    await waitFor(() => {
      expect(screen.queryByTestId('climate-attribution')).not.toBeInTheDocument();
    });
    // The section title is always present (EN test locale).
    expect(screen.getByText('Climate at this site')).toBeInTheDocument();
  });

  it('offers a retry on load error', async () => {
    mockGet.mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce(response());

    renderWithProviders(<SiteClimateSection siteKey="site-1" />);

    const retry = await screen.findByRole('button', { name: 'Retry' });
    retry.click();

    expect(await screen.findByTestId('climate-attribution')).toBeInTheDocument();
  });
});
