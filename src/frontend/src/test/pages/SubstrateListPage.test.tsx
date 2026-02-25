import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SubstrateListPage from '@/pages/standorte/SubstrateListPage';
import { renderWithProviders } from '../helpers';

describe('SubstrateListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<SubstrateListPage />);
    await waitFor(() => {
      expect(screen.getByText('Substrate')).toBeTruthy();
    });
  });

  it('shows empty state when no substrates', async () => {
    renderWithProviders(<SubstrateListPage />);
    await waitFor(() => {
      expect(screen.getByText(/keine daten/i)).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<SubstrateListPage />);
    await waitFor(() => {
      expect(screen.getByText('Substrat erstellen')).toBeTruthy();
    });
  });
});
