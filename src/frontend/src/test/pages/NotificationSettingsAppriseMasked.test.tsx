import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { renderWithProviders } from '@/test/helpers';

/**
 * #2113 — Apprise URLs carry access tokens and are stored encrypted. The
 * preferences API answers with masked placeholders (`tgram://****#1`); the tab
 * shows them as they come, explains them, and sends a kept placeholder back
 * verbatim so the backend keeps the stored URL it stands for.
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

const MASKED_PREFS = {
  key: 'p1',
  user_key: 'u1',
  channels: {
    apprise: {
      enabled: true,
      priority: 0,
      config: { urls: ['tgram://****#1', 'gotifys://****#2'] },
    },
  },
  quiet_hours: { enabled: false, start: '22:00', end: '07:00', timezone: 'Europe/Berlin' },
  batching: { enabled: false, window_minutes: 30, max_batch_size: 10 },
  escalation: { watering_enabled: false, escalation_days: [2, 4, 7] },
  type_overrides: {},
  daily_summary: { enabled: false, time: '07:00', channel: 'home_assistant' },
  created_at: null,
  updated_at: null,
};

async function appriseTextarea(): Promise<HTMLTextAreaElement> {
  return (await screen.findByTestId('apprise-urls')).querySelector(
    'textarea',
  ) as HTMLTextAreaElement;
}

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  vi.clearAllMocks();
  api.getPreferences.mockResolvedValue(structuredClone(MASKED_PREFS));
  api.getChannelStatus.mockResolvedValue([
    { channel_key: 'apprise', healthy: true, supports_actions: false, supports_batching: false },
  ]);
  api.updatePreferences.mockImplementation((payload) => Promise.resolve(payload));
});

describe('NotificationSettingsTab — masked Apprise URLs (#2113)', () => {
  it('shows the masked placeholders and explains them (de)', async () => {
    await i18n.changeLanguage('de');
    renderWithProviders(<NotificationSettingsTab />);

    expect((await appriseTextarea()).value).toBe('tgram://****#1\ngotifys://****#2');
    const helper = screen.getByTestId('apprise-urls-helper');
    expect(helper).toHaveTextContent('maskiert');
    expect((await appriseTextarea()).getAttribute('aria-describedby')).toBe(
      'apprise-urls-helper',
    );
  });

  it('explains the placeholders in English too', async () => {
    await i18n.changeLanguage('en');
    renderWithProviders(<NotificationSettingsTab />);

    expect(await screen.findByTestId('apprise-urls-helper')).toHaveTextContent(
      'shown masked',
    );
  });

  it('sends kept placeholders back verbatim and a new line beside them', async () => {
    await i18n.changeLanguage('de');
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const textarea = await appriseTextarea();
    await user.clear(textarea);
    await user.type(textarea, 'gotifys://****#2{enter}ntfys://ntfy.example.org/topic');
    await user.click(screen.getByTestId('notification-settings-save'));

    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    expect(api.updatePreferences.mock.calls[0][0].channels.apprise.config.urls).toEqual([
      'gotifys://****#2',
      'ntfys://ntfy.example.org/topic',
    ]);
  });

  it('an unchanged save keeps every placeholder', async () => {
    await i18n.changeLanguage('de');
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    await appriseTextarea();
    await user.click(screen.getByTestId('notification-settings-save'));

    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    expect(api.updatePreferences.mock.calls[0][0].channels.apprise.config.urls).toEqual([
      'tgram://****#1',
      'gotifys://****#2',
    ]);
  });

  it('shows the masked answer after a save, not the URL just typed', async () => {
    await i18n.changeLanguage('de');
    api.updatePreferences.mockImplementation((payload) =>
      Promise.resolve({
        ...structuredClone(MASKED_PREFS),
        ...payload,
        channels: {
          apprise: { enabled: true, priority: 0, config: { urls: ['tgram://****#1', 'ntfys://****#2'] } },
        },
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const textarea = await appriseTextarea();
    await user.clear(textarea);
    await user.type(textarea, 'tgram://****#1{enter}ntfys://ntfy.example.org/topic');
    await user.click(screen.getByTestId('notification-settings-save'));

    await waitFor(() =>
      expect(textarea.value).toBe('tgram://****#1\nntfys://****#2'),
    );
    expect(textarea.value).not.toContain('ntfy.example.org');
  });
});
