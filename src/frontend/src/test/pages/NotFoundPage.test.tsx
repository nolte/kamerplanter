import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import NotFoundPage from '@/pages/NotFoundPage';
import { renderWithProviders } from '../helpers';

describe('NotFoundPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders 404 text', async () => {
    renderWithProviders(<NotFoundPage />);
    await waitFor(() => {
      expect(screen.getByText('404')).toBeTruthy();
    });
  });

  it('renders not found message', async () => {
    renderWithProviders(<NotFoundPage />);
    await waitFor(() => {
      expect(screen.getByText(/nicht gefunden|not found/i)).toBeTruthy();
    });
  });

  it('renders back to home button', async () => {
    renderWithProviders(<NotFoundPage />);
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeTruthy();
    });
  });
});
