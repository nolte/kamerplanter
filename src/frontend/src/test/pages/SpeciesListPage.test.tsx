import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SpeciesListPage from '@/pages/stammdaten/SpeciesListPage';
import { renderWithProviders } from '../helpers';

describe('SpeciesListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Arten')).toBeTruthy();
    });
  });

  it('loads and displays species from API', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Solanum lycopersicum')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Art erstellen')).toBeTruthy();
    });
  });

  it('displays species common names', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Tomato')).toBeTruthy();
    });
  });
});
