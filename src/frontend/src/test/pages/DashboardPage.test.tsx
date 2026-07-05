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
    // quick_actions is a default beginner widget; its tiles are lazy-loaded, so
    // give findByText headroom over its 1s default — under coverage
    // instrumentation on a loaded CI runner the Suspense chunk can take longer
    // than 1s to resolve, which otherwise flakes this assertion.
    expect(await screen.findByText('Standorte', undefined, { timeout: 5000 })).toBeTruthy();
    expect(await screen.findByText('Pflanzeninstanzen', undefined, { timeout: 5000 })).toBeTruthy();
  });
});
