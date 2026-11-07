import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import UpdateBanner from '@/components/common/UpdateBanner';
import { markUpdateAvailable } from '@/lib/serviceWorkerRegistration';
import { renderWithProviders } from '../helpers';

/**
 * R-014 across tabs (REQ-053 WP 9.1, #2786 review finding 7): when ANOTHER tab confirmed the update,
 * this tab's banner closes and the page reloads onto the new build on the controller change — and a
 * click on a banner whose worker no longer waits reloads instead of doing nothing.
 *
 * Its own file: the armed reload is module state, armed once per page like in the browser.
 */

let controllerChange: (() => void) | undefined;
let reload: ReturnType<typeof vi.fn>;
let originalLocation: Location;

beforeEach(async () => {
  await i18n.changeLanguage('de');
  controllerChange = undefined;
  reload = vi.fn();
  originalLocation = window.location;
  Object.defineProperty(window, 'location', { configurable: true, value: { ...originalLocation, reload } });
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: {
      addEventListener: (type: string, listener: () => void) => {
        if (type === 'controllerchange') controllerChange = listener;
      },
    },
  });
});

afterEach(() => {
  Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
  delete (navigator as unknown as Record<string, unknown>).serviceWorker;
});

describe('UpdateBanner in a second tab', () => {
  it('closes and reloads when another tab activated the update', async () => {
    const registration = { waiting: { postMessage: vi.fn() } } as unknown as ServiceWorkerRegistration;
    renderWithProviders(<UpdateBanner />);
    act(() => markUpdateAvailable(registration));
    expect(await screen.findByText('Neue Version verfügbar')).toBeInTheDocument();

    expect(controllerChange).toBeDefined();
    act(() => controllerChange?.());
    await waitFor(() => expect(screen.queryByText('Neue Version verfügbar')).toBeNull());
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('reloads on the click when the worker no longer waits', async () => {
    const registration = { waiting: null } as unknown as ServiceWorkerRegistration;
    renderWithProviders(<UpdateBanner />);
    act(() => markUpdateAvailable(registration));
    await userEvent.click(await screen.findByTestId('pwa-update-now'));
    expect(reload).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByText('Neue Version verfügbar')).toBeNull());
  });
});
