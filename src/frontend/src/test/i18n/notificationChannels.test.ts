import { describe, it, expect } from 'vitest';
import { deFull as de, enFull as en } from '../i18nTestResources';

/**
 * Guards consistency between the hardcoded CHANNEL_KEYS in NotificationSettingsTab
 * and the i18n label keys both locales must provide. CHANNEL_KEYS is re-declared
 * here intentionally: if a channel is added to the component, this list must be
 * updated too, which forces the matching DE/EN labels to exist.
 */
const CHANNEL_KEYS = ['home_assistant', 'email', 'pwa', 'apprise'] as const;

const CHANNEL_LABEL_KEYS: Record<(typeof CHANNEL_KEYS)[number], string> = {
  home_assistant: 'channelHomeAssistant',
  email: 'channelEmail',
  pwa: 'channelPwa',
  apprise: 'channelApprise',
};

// PWA-specific keys consumed by the NotificationSettingsTab pwa block.
const PWA_KEYS = [
  'pwaEnable',
  'pwaDisable',
  'pwaActive',
  'pwaEnabled',
  'pwaDisabled',
  'pwaHint',
  'pwaUnsupported',
  'pwaPermissionDenied',
];

function settings(locale: unknown): Record<string, string> {
  return (
    locale as {
      pages: { notifications: { settings: Record<string, string> } };
    }
  ).pages.notifications.settings;
}

describe('notification channel i18n consistency', () => {
  it.each(CHANNEL_KEYS)('has a non-empty DE + EN label for channel "%s"', (key) => {
    const labelKey = CHANNEL_LABEL_KEYS[key];
    expect(settings(de)[labelKey]?.length).toBeGreaterThan(0);
    expect(settings(en)[labelKey]?.length).toBeGreaterThan(0);
  });

  it.each(PWA_KEYS)('has a non-empty DE + EN string for pwa key "%s"', (key) => {
    expect(settings(de)[key]?.length).toBeGreaterThan(0);
    expect(settings(en)[key]?.length).toBeGreaterThan(0);
  });

  it('marks the pwa channel label as device-scoped in both locales', () => {
    expect(settings(de).channelPwa.toLowerCase()).toContain('gerät');
    expect(settings(en).channelPwa.toLowerCase()).toContain('device');
  });
});
