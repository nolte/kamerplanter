import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, createTestStore, authState } from '@/test/helpers';
import type { UserProfile } from '@/api/types';

/**
 * Email channel — NotificationSettingsTab (issue #1885).
 *
 * The channel mails the account's confirmed address only. The tab shows that
 * address read-only (no free-text recipient field), warns when it is not
 * confirmed, and never writes a recipient key back to the backend.
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
      config: { digest: false },
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

const ACCOUNT = {
  key: 'u1',
  email: 'owner@example.org',
  display_name: 'Owner',
  email_verified: true,
} as UserProfile;

const render = (user: UserProfile) => {
  const base = authState() as { auth: Record<string, unknown> };
  const store = createTestStore({ auth: { ...base.auth, user } });
  return renderWithProviders(<NotificationSettingsTab />, { store });
};

describe('NotificationSettingsTab — email recipient', () => {
  it('shows the confirmed account address read-only and offers no recipient field', async () => {
    render(ACCOUNT);

    expect(await screen.findByTestId('email-recipient-address')).toHaveTextContent('owner@example.org');
    expect(screen.getByTestId('email-recipient-helper')).toBeInTheDocument();
    expect(screen.queryByTestId('email-address')).not.toBeInTheDocument();
    expect(screen.queryByRole('textbox', { name: /e-mail|email/i })).not.toBeInTheDocument();
    expect(screen.queryByTestId('email-recipient-unverified')).not.toBeInTheDocument();
  });

  it('warns that nothing is mailed while the account address is unconfirmed', async () => {
    render({ ...ACCOUNT, email_verified: false });

    expect(await screen.findByTestId('email-recipient-unverified')).toBeInTheDocument();
    expect(screen.queryByTestId('email-recipient-helper')).not.toBeInTheDocument();
  });

  it('saves the digest flag without any recipient key', async () => {
    const user = userEvent.setup();
    render(ACCOUNT);

    await screen.findByTestId('email-recipient-address');
    await user.click(screen.getByTestId('notification-settings-save'));

    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    const emailConfig = api.updatePreferences.mock.calls[0][0].channels.email.config;
    expect(emailConfig.digest).toBe(false);
    expect(emailConfig).not.toHaveProperty('address');
    expect(emailConfig).not.toHaveProperty('digest_mode');
  });
});
