import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import i18n from 'i18next';
import type { TenantRole } from '@/api/types';
import HardinessZoneDetectButton from '@/pages/standorte/HardinessZoneDetectButton';
import { ApiError } from '@/api/errors';
import { createTestStore, renderWithProviders } from '../helpers';

vi.mock('@/api/endpoints/sites', () => ({
  resolveSiteHardinessZone: vi.fn(),
}));
import { resolveSiteHardinessZone } from '@/api/endpoints/sites';

const mockResolve = vi.mocked(resolveSiteHardinessZone);

function storeWithRole(role: TenantRole) {
  return createTestStore({
    tenants: {
      activeTenant: { key: 't1', slug: 'garten', name: 'Garten', role },
      myTenants: [],
      loading: false,
      error: null,
    },
  });
}

function renderButton(
  { role = 'grower' as TenantRole, gpsPresent = true } = {},
  onResolved = vi.fn(),
) {
  renderWithProviders(
    <HardinessZoneDetectButton siteKey="site-1" gpsPresent={gpsPresent} onResolved={onResolved} />,
    { store: storeWithRole(role) },
  );
  return { onResolved };
}

describe('HardinessZoneDetectButton', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockResolve.mockReset();
  });
  afterEach(() => vi.clearAllMocks());

  it('is not rendered for a viewer (endpoint requires grower)', () => {
    renderButton({ role: 'viewer' });
    expect(screen.queryByTestId('hardiness-detect-button')).toBeNull();
  });

  it('is disabled with a hint when the saved site has no GPS', async () => {
    renderButton({ gpsPresent: false });
    const button = await screen.findByTestId('hardiness-detect-button');
    expect(button).toBeDisabled();
    expect(screen.getByText(/GPS-Koordinaten hinterlegen/i)).toBeTruthy();
  });

  it('resolves the zone and reloads the site on success', async () => {
    mockResolve.mockResolvedValue({
      site_key: 'site-1',
      hardiness_zone: '7a',
      hardiness_zone_source: 'derived_gps',
      hardiness_zone_resolved_at: '2026-07-23T00:00:00Z',
      mean_annual_minimum_c: -17,
      last_frost_date_avg: null,
      first_frost_date_avg: null,
      zone: null,
    });
    const { onResolved } = renderButton();

    await userEvent.click(await screen.findByTestId('hardiness-detect-button'));

    expect(mockResolve).toHaveBeenCalledWith('site-1');
    expect(await screen.findByText(/7a/)).toBeTruthy();
    expect(onResolved).toHaveBeenCalledOnce();
  });

  it('shows an info message and does not reload when no climate data (422)', async () => {
    mockResolve.mockRejectedValue(
      new ApiError({ error_code: 'VALIDATION_ERROR', message: 'no normals' } as never, 422),
    );
    const { onResolved } = renderButton();

    await userEvent.click(await screen.findByTestId('hardiness-detect-button'));

    expect(await screen.findByText(/keine Klimadaten abgerufen/i)).toBeTruthy();
    expect(onResolved).not.toHaveBeenCalled();
  });
});
