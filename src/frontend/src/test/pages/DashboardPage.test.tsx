import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import DashboardPage from '@/pages/DashboardPage';
import { renderWithProviders } from '../helpers';

describe('DashboardPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeTruthy();
    });
  });

  it('renders welcome message', async () => {
    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/willkommen/i)).toBeTruthy();
    });
  });

  it('renders quick action cards', async () => {
    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('Botanische Familien')).toBeTruthy();
      expect(screen.getByText('Arten')).toBeTruthy();
      expect(screen.getByText('Standorte')).toBeTruthy();
      expect(screen.getByText('Substrate')).toBeTruthy();
      expect(screen.getByText('Pflanzeninstanzen')).toBeTruthy();
      expect(screen.getByText('Berechnungen')).toBeTruthy();
    });
  });
});
