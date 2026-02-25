import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import PlantInstanceListPage from '@/pages/pflanzen/PlantInstanceListPage';
import { renderWithProviders } from '../helpers';

describe('PlantInstanceListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Pflanzeninstanzen')).toBeTruthy();
    });
  });

  it('loads and displays plants from API', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Big Red')).toBeTruthy();
    });
  });

  it('shows instance ID', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('TOM-001')).toBeTruthy();
    });
  });

  it('shows current phase as chip', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('vegetative')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Pflanze erstellen')).toBeTruthy();
    });
  });
});
