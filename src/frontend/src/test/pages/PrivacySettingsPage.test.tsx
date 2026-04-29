import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PrivacySettingsPage from '@/pages/auth/PrivacySettingsPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('PrivacySettingsPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/privacy/consents', () =>
        HttpResponse.json([
          {
            purpose: 'analytics',
            label: 'Analyse',
            description: 'Analytische Daten zur Produktverbesserung',
            legal_basis: 'consent',
            required: false,
            granted: false,
            granted_at: null,
            revoked_at: null,
          },
        ]),
      ),
    );
  });

  it('renders the page title and four privacy tabs', async () => {
    renderWithProviders(<PrivacySettingsPage />);
    await waitFor(() => {
      expect(screen.getByTestId('privacy-settings-page')).toBeTruthy();
    });
    expect(screen.getByTestId('privacy-tab-consents')).toBeTruthy();
    expect(screen.getByTestId('privacy-tab-export')).toBeTruthy();
    expect(screen.getByTestId('privacy-tab-erasure')).toBeTruthy();
    expect(screen.getByTestId('privacy-tab-restrict')).toBeTruthy();
  });
});
