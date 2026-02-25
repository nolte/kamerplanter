import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SiteListPage from '@/pages/standorte/SiteListPage';
import { renderWithProviders } from '../helpers';

describe('SiteListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('Standorte')).toBeTruthy();
    });
  });

  it('loads and displays sites from API', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('Main Greenhouse')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('Standort erstellen')).toBeTruthy();
    });
  });

  it('displays area with unit', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('50 m²')).toBeTruthy();
    });
  });
});
