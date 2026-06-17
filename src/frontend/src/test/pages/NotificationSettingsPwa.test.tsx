import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';

/**
 * Frontend Web Push (PWA) channel — NotificationSettingsTab.
 *
 * The notifications endpoints module is mocked so the test asserts the UI flow
 * (enable → permission → subscribe → backend register, and the deactivate path)
 * without a real network or a real push service. The browser Push APIs
 * (serviceWorker / PushManager / Notification) are faked on the globals so the
 * real usePwaPush hook executes end-to-end.
 */

const api = vi.hoisted(() => ({
  getPreferences: vi.fn(),
  getChannelStatus: vi.fn(),
  updatePreferences: vi.fn(),
  sendTest: vi.fn(),
  getPwaVapidPublicKey: vi.fn(),
  subscribePwa: vi.fn(),
  unsubscribePwa: vi.fn(),
}));

vi.mock('@/api/endpoints/notifications', () => api);

import NotificationSettingsTab from '@/pages/auth/NotificationSettingsTab';

const BASE_PREFS = {
  key: 'p1',
  user_key: 'u1',
  channels: {
    pwa: { enabled: true, priority: 0, config: {} },
  },
  quiet_hours: { enabled: false, start: '22:00', end: '07:00', timezone: 'Europe/Berlin' },
  batching: { enabled: false, window_minutes: 30, max_batch_size: 10 },
  escalation: { watering_enabled: false, escalation_days: [2, 4, 7] },
  type_overrides: {},
  daily_summary: { enabled: false, time: '07:00', channel: 'pwa' },
  created_at: null,
  updated_at: null,
};

interface FakeSubscription {
  endpoint: string;
  unsubscribe: ReturnType<typeof vi.fn>;
  toJSON: () => PushSubscriptionJSON;
}

let currentSubscription: FakeSubscription | null;
let subscribeMock: ReturnType<typeof vi.fn>;
let permissionResult: NotificationPermission;

function makeSubscription(): FakeSubscription {
  return {
    endpoint: 'https://push.example/endpoint-1',
    unsubscribe: vi.fn().mockResolvedValue(true),
    toJSON: () => ({
      endpoint: 'https://push.example/endpoint-1',
      keys: { p256dh: 'P256', auth: 'AUTH' },
    }),
  };
}

function installPushApis(supported: boolean) {
  if (!supported) {
    // Remove PushManager to simulate an unsupported browser.
    delete (window as unknown as Record<string, unknown>).PushManager;
    return;
  }

  subscribeMock = vi.fn().mockImplementation(async () => {
    currentSubscription = makeSubscription();
    return currentSubscription;
  });

  const registration = {
    pushManager: {
      getSubscription: vi.fn().mockImplementation(async () => currentSubscription),
      subscribe: subscribeMock,
    },
  };

  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: {
      ready: Promise.resolve(registration),
      register: vi.fn().mockResolvedValue(registration),
    },
  });

  (window as unknown as Record<string, unknown>).PushManager = function PushManager() {};

  Object.defineProperty(window, 'Notification', {
    configurable: true,
    writable: true,
    value: Object.assign(
      function Notification() {},
      {
        permission: 'default' as NotificationPermission,
        requestPermission: vi.fn().mockImplementation(async () => permissionResult),
      },
    ),
  });

  // jsdom provides window.atob already; the VAPID key ('QUJD' = 'ABC') decodes
  // fine through it, so no shim is needed.
}

beforeEach(() => {
  vi.clearAllMocks();
  currentSubscription = null;
  permissionResult = 'granted';
  api.getPreferences.mockResolvedValue(BASE_PREFS);
  api.getChannelStatus.mockResolvedValue([
    { channel_key: 'pwa', healthy: true, supports_actions: true, supports_batching: false },
  ]);
  api.getPwaVapidPublicKey.mockResolvedValue({ vapid_public_key: 'QUJD' });
  api.subscribePwa.mockResolvedValue({ endpoint: 'https://push.example/endpoint-1' });
  api.unsubscribePwa.mockResolvedValue(undefined);
});

afterEach(() => {
  delete (window as unknown as Record<string, unknown>).PushManager;
});

describe('NotificationSettingsTab — Web Push (PWA) channel', () => {
  it('enables push: requests permission, subscribes and registers with the backend', async () => {
    installPushApis(true);
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const enableButton = await screen.findByTestId('pwa-enable');
    await user.click(enableButton);

    await waitFor(() => {
      expect(api.getPwaVapidPublicKey).toHaveBeenCalledTimes(1);
    });
    expect(subscribeMock).toHaveBeenCalledWith(
      expect.objectContaining({ userVisibleOnly: true }),
    );
    expect(api.subscribePwa).toHaveBeenCalledWith({
      endpoint: 'https://push.example/endpoint-1',
      keys: { p256dh: 'P256', auth: 'AUTH' },
    });

    // Reflects the active state afterwards.
    expect(await screen.findByTestId('pwa-disable')).toBeInTheDocument();
  });

  it('does not subscribe when permission is denied', async () => {
    permissionResult = 'denied';
    installPushApis(true);
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const enableButton = await screen.findByTestId('pwa-enable');
    await user.click(enableButton);

    await waitFor(() => {
      expect(
        screen.getByText(/blocked|blockiert/i),
      ).toBeInTheDocument();
    });
    expect(api.subscribePwa).not.toHaveBeenCalled();
  });

  it('deactivates an active subscription via the backend', async () => {
    installPushApis(true);
    currentSubscription = makeSubscription();
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const disableButton = await screen.findByTestId('pwa-disable');
    await user.click(disableButton);

    await waitFor(() => {
      expect(api.unsubscribePwa).toHaveBeenCalledWith(
        'https://push.example/endpoint-1',
      );
    });
    expect(await screen.findByTestId('pwa-enable')).toBeInTheDocument();
  });

  it('shows an unsupported hint when PushManager is missing', async () => {
    installPushApis(false);
    renderWithProviders(<NotificationSettingsTab />);

    expect(
      await screen.findByText(/does not support|unterstuetzt keine/i),
    ).toBeInTheDocument();
    expect(screen.queryByTestId('pwa-enable')).not.toBeInTheDocument();
  });
});
