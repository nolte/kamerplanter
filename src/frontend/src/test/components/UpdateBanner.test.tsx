import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import UpdateBanner from '@/components/common/UpdateBanner';
import { markUpdateAvailable } from '@/lib/serviceWorkerRegistration';
import { renderWithProviders } from '../helpers';

/** UI-NFR-012 R-014 (REQ-053 WP 9.1) — a waiting service worker is activated only on the user's go. */

function waitingRegistration() {
  const postMessage = vi.fn();
  return { registration: { waiting: { postMessage } } as unknown as ServiceWorkerRegistration, postMessage };
}

describe('UpdateBanner', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    Object.defineProperty(navigator, 'serviceWorker', {
      configurable: true,
      value: { addEventListener: vi.fn() },
    });
  });

  afterEach(() => {
    act(() => markUpdateAvailable(null));
    delete (navigator as unknown as Record<string, unknown>).serviceWorker;
  });

  it('renders nothing while no update waits', () => {
    renderWithProviders(<UpdateBanner />);
    expect(screen.queryByText('Neue Version verfügbar')).toBeNull();
  });

  it('offers the update and activates the waiting worker on "Jetzt aktualisieren"', async () => {
    const { registration, postMessage } = waitingRegistration();
    renderWithProviders(<UpdateBanner />);
    act(() => markUpdateAvailable(registration));

    expect(await screen.findByText('Neue Version verfügbar')).toBeInTheDocument();
    await userEvent.click(screen.getByTestId('pwa-update-now'));
    expect(postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' });
    // The reload is armed for the moment the new worker takes control.
    expect(navigator.serviceWorker.addEventListener).toHaveBeenCalledWith(
      'controllerchange',
      expect.any(Function),
      { once: true },
    );
  });

  it('hides on "Später" without activating anything', async () => {
    const { registration, postMessage } = waitingRegistration();
    renderWithProviders(<UpdateBanner />);
    act(() => markUpdateAvailable(registration));

    await userEvent.click(await screen.findByRole('button', { name: 'Später' }));
    await waitFor(() => expect(screen.queryByText('Neue Version verfügbar')).toBeNull());
    expect(postMessage).not.toHaveBeenCalled();
  });
});
