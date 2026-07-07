import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { renderWithProviders } from '@/test/helpers';

/**
 * NotificationSettingsTab — coverage for the schedule/batching/escalation
 * sections, the Home-Assistant and Apprise channel config, the test-send
 * outcomes, and the save success/failure paths. Complements the email- and
 * PWA-focused suites (NotificationSettingsEmail / NotificationSettingsPwa).
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

// home_assistant deliberately absent from channels → exercises the
// getChannelPref default branch and the toggle-on config-creation path.
const BASE_PREFS = {
  key: 'p1',
  user_key: 'u1',
  channels: {
    email: { enabled: true, priority: 0, config: { email: 'a@b.de', digest: false } },
    apprise: { enabled: true, priority: 0, config: { urls: ['tgram://a/b'] } },
  },
  quiet_hours: { enabled: true, start: '22:00', end: '07:00', timezone: 'Europe/Berlin' },
  batching: { enabled: true, window_minutes: 30, max_batch_size: 10 },
  escalation: { watering_enabled: true, escalation_days: [2, 4, 7] },
  type_overrides: { some_type: {} },
  daily_summary: { enabled: true, time: '07:00', channel: 'email' },
  created_at: null,
  updated_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  i18n.changeLanguage('de');
  api.getPreferences.mockResolvedValue(structuredClone(BASE_PREFS));
  api.getChannelStatus.mockResolvedValue([
    { channel_key: 'email', healthy: true, supports_actions: false, supports_batching: true },
    { channel_key: 'apprise', healthy: false, supports_actions: false, supports_batching: false },
  ]);
  api.updatePreferences.mockImplementation((payload) => Promise.resolve(payload));
});

describe('NotificationSettingsTab — schedule / batching / escalation', () => {
  it('renders the loaded quiet-hours, batching, escalation and daily-summary sections', async () => {
    renderWithProviders(<NotificationSettingsTab />);

    // quiet hours enabled → start/end inputs shown
    expect(await screen.findByTestId('quiet-hours-start')).toBeInTheDocument();
    expect(screen.getByTestId('quiet-hours-end')).toBeInTheDocument();
    // batching enabled → window input shown
    expect(screen.getByTestId('batching-window')).toBeInTheDocument();
    // escalation enabled → escalation-day chips rendered (2, 4, 7)
    expect(screen.getByText(/\+2$/)).toBeInTheDocument();
    expect(screen.getByText(/\+7$/)).toBeInTheDocument();
    // daily summary enabled → time + channel select shown
    expect(screen.getByTestId('daily-summary-time')).toBeInTheDocument();
    expect(screen.getByTestId('daily-summary-channel')).toBeInTheDocument();
  });

  it('toggling the sections off hides their controls', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    await screen.findByTestId('quiet-hours-toggle');
    await user.click(screen.getByTestId('quiet-hours-toggle'));
    await user.click(screen.getByTestId('batching-toggle'));
    await user.click(screen.getByTestId('escalation-toggle'));
    await user.click(screen.getByTestId('daily-summary-toggle'));

    expect(screen.queryByTestId('quiet-hours-start')).not.toBeInTheDocument();
    expect(screen.queryByTestId('batching-window')).not.toBeInTheDocument();
    expect(screen.queryByTestId('daily-summary-time')).not.toBeInTheDocument();
  });

  it('clamps the batching window to the 1..120 range', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const window = (await screen.findByTestId('batching-window')).querySelector(
      'input',
    ) as HTMLInputElement;
    await user.clear(window);
    await user.type(window, '999');
    expect(window.value).toBe('120');
  });

  it('edits quiet-hours times and persists them on save', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const start = (await screen.findByTestId('quiet-hours-start')).querySelector(
      'input',
    ) as HTMLInputElement;
    await user.clear(start);
    await user.type(start, '23:30');

    await user.click(screen.getByTestId('notification-settings-save'));
    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    const payload = api.updatePreferences.mock.calls[0][0];
    expect(payload.quiet_hours.start).toBe('23:30');
    // type_overrides are passed straight through from the loaded prefs
    expect(payload.type_overrides).toEqual({ some_type: {} });
  });
});

describe('NotificationSettingsTab — Home Assistant channel', () => {
  it('enables HA, toggles its sub-options and writes the config on save', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    // home_assistant starts disabled (absent from prefs) → toggle it on.
    const haToggle = await screen.findByTestId('channel-toggle-home_assistant');
    await user.click(haToggle);

    // Sub-option switches appear.
    await user.click(
      screen.getByTestId('ha-persistent-notification-toggle'),
    );
    // Enabling TTS reveals the entity-id field.
    await user.click(screen.getByTestId('ha-tts-toggle'));
    const entity = (await screen.findByTestId('ha-tts-entity-id')).querySelector(
      'input',
    ) as HTMLInputElement;
    await user.type(entity, 'media_player.kitchen');

    await user.click(screen.getByTestId('notification-settings-save'));
    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    const haConfig = api.updatePreferences.mock.calls[0][0].channels.home_assistant;
    expect(haConfig.enabled).toBe(true);
    expect(haConfig.config.tts_enabled).toBe(true);
    expect(haConfig.config.tts_entity_id).toBe('media_player.kitchen');
  });
});

describe('NotificationSettingsTab — Apprise channel', () => {
  it('renders the loaded urls and writes the edited list on save', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    const urls = (await screen.findByTestId('apprise-urls')).querySelector(
      'textarea',
    ) as HTMLTextAreaElement;
    expect(urls.value).toBe('tgram://a/b');
    await user.clear(urls);
    await user.type(urls, 'slack://x/y/z');

    await user.click(screen.getByTestId('notification-settings-save'));
    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledTimes(1));
    const appriseConfig = api.updatePreferences.mock.calls[0][0].channels.apprise.config;
    expect(appriseConfig.urls).toEqual(['slack://x/y/z']);
  });
});

describe('NotificationSettingsTab — test send', () => {
  it('shows a success snackbar when the test succeeds', async () => {
    api.sendTest.mockResolvedValue({ success: true, error: null });
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    await user.click(await screen.findByTestId('test-send-email'));
    await waitFor(() => expect(api.sendTest).toHaveBeenCalledWith('email'));
    expect(
      await screen.findByText(i18n.t('pages.notifications.settings.testSuccess')),
    ).toBeInTheDocument();
  });

  it('shows a failure snackbar with the error detail when the test reports failure', async () => {
    api.sendTest.mockResolvedValue({ success: false, error: 'smtp down' });
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    await user.click(await screen.findByTestId('test-send-email'));
    await waitFor(() =>
      expect(screen.getByText(/smtp down/)).toBeInTheDocument(),
    );
  });

  it('shows an error snackbar when the test send throws', async () => {
    api.sendTest.mockRejectedValue(new Error('network boom'));
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    await user.click(await screen.findByTestId('test-send-email'));
    await waitFor(() =>
      expect(screen.getByText(/network boom/)).toBeInTheDocument(),
    );
  });
});

describe('NotificationSettingsTab — save failure', () => {
  it('surfaces the API error when saving fails', async () => {
    api.updatePreferences.mockRejectedValue(new Error('save failed'));
    const user = userEvent.setup();
    renderWithProviders(<NotificationSettingsTab />);

    await user.click(await screen.findByTestId('notification-settings-save'));
    await waitFor(() =>
      expect(screen.getByText(/save failed/)).toBeInTheDocument(),
    );
  });

  it('keeps defaults and stops loading when the initial load fails', async () => {
    api.getPreferences.mockRejectedValue(new Error('load failed'));
    api.getChannelStatus.mockRejectedValue(new Error('load failed'));
    renderWithProviders(<NotificationSettingsTab />);

    // The channels section still renders from the built-in defaults.
    expect(
      await screen.findByTestId('channel-toggle-home_assistant'),
    ).toBeInTheDocument();
  });
});
