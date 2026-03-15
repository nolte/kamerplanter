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

  it('renders error page with illustration', async () => {
    renderWithProviders(<NotFoundPage />);
    await waitFor(() => {
      expect(screen.getByTestId('error-page')).toBeTruthy();
      const img = screen.getByRole('img');
      expect(img.getAttribute('src')).toContain('error-404');
    });
  });

  it('renders back to home button', async () => {
    renderWithProviders(<NotFoundPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /dashboard/i })).toBeTruthy();
    });
  });
});
