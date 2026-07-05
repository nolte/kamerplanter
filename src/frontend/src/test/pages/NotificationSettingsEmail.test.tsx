import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';

/**
 * Email channel config keys — NotificationSettingsTab (issue #367 item #4).
 *
 * The email address field and digest select used to write `config.address` and
 * `config.digest_mode`, while the backend reads `config.email` and
 * `config.digest` — so the settings never reached the backend. This test locks
 * in the canonical keys through the actual save flow.
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
    email: {
      enabled: true,
      priority: 0,
      config: { email: 'old@example.com', digest: false },
    },
  },
  quiet_hours: { enabled: false, start: '22:00', end: '07:00', timezone: 'Europe/Berlin' },
  batching: { enabled: false, window_minutes: 30, max_batch_size: 10 },
  escalation: { watering_enabled: false, escalation_days: [2, 4, 7] },
  type_overrides: {},
  daily_summary: { enabled: false, time: '07:00', channel: 'email' },
  created_at: null,
  updated_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  api.getPreferences.mockResolvedValue(BASE_PREFS);
  api.getChannelStatus.mockResolvedValue([
    { channel_key: 'email', healthy: true, supports_actions: false, supports_batching: true },
  ]);
  api.updatePreferences.mockImplementation((payload) => Promise.resolve(payload));
});

describe('NotificationSettingsTab — email channel config keys', () => {
  it('reads the existing address from config.email', async () => {
    renderWithProviders(<NotificationSettingsTab />);
    const input = (await screen.findByTestId('email-address')).querySelector('input');
    expect(input).not.toBeNull();
    expect((input as HTMLInputElement).value).toBe('old@example.com');
  });

  it('writes the address to config.email and digest to config.digest on save', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const input = (await screen.findByTestId('email-address')).querySelector(
      'input',
    ) as HTMLInputElement;
    await user.clear(input);
    await user.type(input, 'new@example.com');

    await user.click(screen.getByTestId('notification-settings-save'));

    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    const payload = api.updatePreferences.mock.calls[0][0];
    const emailConfig = payload.channels.email.config;
    expect(emailConfig.email).toBe('new@example.com');
    // The legacy keys must never be written again.
    expect(emailConfig).not.toHaveProperty('address');
    expect(emailConfig).not.toHaveProperty('digest_mode');
    // digest is a boolean the backend checks with `== true`.
    expect(typeof emailConfig.digest).toBe('boolean');
  });
});
