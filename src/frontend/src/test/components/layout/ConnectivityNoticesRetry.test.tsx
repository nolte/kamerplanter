import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, screen } from '@testing-library/react';
import i18n from 'i18next';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import { renderWithProviders } from '../../helpers';

/**
 * #3025 N-39 (review 2) — the notices chunk is a dynamic import outside the app-shell precache. An app started
 * offline cannot fetch it; `React.lazy` would memoise that failure for the session and no R-036/R-037 snackbar
 * — "online again" included — would ever show before a reload. The indicator fetches the chunk again on the
 * `online` event, and the chunk that arrives with the reconnect announces it.
 */
function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
}

describe('ConnectivityIndicator — notices chunk retried on reconnect', () => {
  afterEach(() => setOnline(true));

  it('fetches the chunk again when the connection returns and announces that return', async () => {
    await i18n.changeLanguage('de');
    setOnline(false);
    const load = vi
      .fn<() => Promise<typeof import('@/components/layout/ConnectivityNotices')>>()
      .mockRejectedValueOnce(new Error('Failed to fetch dynamically imported module'))
      .mockImplementation(() => import('@/components/layout/ConnectivityNotices'));

    renderWithProviders(<ConnectivityIndicator loadNotices={load} />);
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(load).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('connectivity-indicator')).toBeInTheDocument();

    await act(async () => {
      setOnline(true);
      window.dispatchEvent(new Event('online'));
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    expect(load).toHaveBeenCalledTimes(2);
    expect(await screen.findByText(/^Online – Synchronisation startet/)).toBeInTheDocument();
  });
});
