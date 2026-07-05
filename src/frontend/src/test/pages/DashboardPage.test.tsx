import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import DashboardPage from '@/pages/DashboardPage';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';

describe('DashboardPage (REQ-045)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<DashboardPage />, { store: createStoreWithExpertise('beginner') });
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeTruthy();
    });
  });

  it('offers the edit toggle and the manage-widgets deep link', async () => {
    renderWithProviders(<DashboardPage />, { store: createStoreWithExpertise('beginner') });
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-edit-toggle')).toBeTruthy();
      expect(screen.getByTestId('dashboard-manage-link')).toBeTruthy();
    });
  });

  it('renders the quick-actions widget from the default beginner layout', async () => {
    // Default store → experience level unknown → all module paths visible.
    renderWithProviders(<DashboardPage />);
    // quick_actions is a default beginner widget; its tiles are lazy-loaded.
    expect(await screen.findByText('Standorte')).toBeTruthy();
    expect(await screen.findByText('Pflanzeninstanzen')).toBeTruthy();
  });
});
