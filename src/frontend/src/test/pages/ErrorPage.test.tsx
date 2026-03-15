import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import i18n from 'i18next';
import ErrorPage from '@/pages/ErrorPage';
import { renderWithProviders } from '../helpers';

describe('ErrorPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders default 500 status code', async () => {
    renderWithProviders(<ErrorPage />);
    await waitFor(() => {
      expect(screen.getByText('500')).toBeTruthy();
      expect(screen.getByTestId('error-page')).toBeTruthy();
    });
  });

  it('renders 404 with illustration', async () => {
    renderWithProviders(<ErrorPage statusCode={404} />);
    await waitFor(() => {
      expect(screen.getByText('404')).toBeTruthy();
      const img = document.querySelector('img[src*="error-404"]');
      expect(img).toBeTruthy();
    });
  });

  it('renders 403 with correct status code', async () => {
    renderWithProviders(<ErrorPage statusCode={403} />);
    await waitFor(() => {
      expect(screen.getByText('403')).toBeTruthy();
    });
  });

  it('renders back to dashboard button', async () => {
    renderWithProviders(<ErrorPage statusCode={500} />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /dashboard/i })).toBeTruthy();
    });
  });

  it('renders retry button when onRetry is provided', async () => {
    const onRetry = vi.fn();
    renderWithProviders(<ErrorPage statusCode={500} onRetry={onRetry} />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /erneut|retry/i })).toBeTruthy();
    });
  });

  it('calls onRetry when retry button is clicked', async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<ErrorPage statusCode={500} onRetry={onRetry} />);
    const retryButton = await screen.findByRole('button', { name: /erneut|retry/i });
    await user.click(retryButton);
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('does not render retry button without onRetry', async () => {
    renderWithProviders(<ErrorPage statusCode={404} />);
    await waitFor(() => {
      expect(screen.getByText('404')).toBeTruthy();
      expect(screen.queryByRole('button', { name: /erneut|retry/i })).toBeNull();
    });
  });

  it.each([400, 401, 403, 404, 408, 429, 500, 502, 503])(
    'renders status code %i',
    async (code) => {
      renderWithProviders(<ErrorPage statusCode={code} />);
      await waitFor(() => {
        expect(screen.getByText(String(code))).toBeTruthy();
        expect(screen.getByTestId('error-page')).toBeTruthy();
      });
    },
  );
});
