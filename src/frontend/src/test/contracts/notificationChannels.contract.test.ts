import { describe, expect, it } from 'vitest';

import contract from '@/contracts/notification-channels.json';
import { CHANNEL_KEYS } from '@/pages/auth/NotificationSettingsTab';

/**
 * Consumer-driven contract: every channel the frontend renders (and sends as
 * `channel_key` to the backend) must be listed in the shared contract, which
 * the backend separately proves it can register
 * (src/backend/tests/contracts/test_notification_channels_contract.py).
 *
 * This is the guard for the bug that motivated it: the UI offered a `pwa`
 * channel the backend never registered, so "Test senden" failed with
 * `Channel 'pwa' not found`. Adding/removing a channel key now forces an update
 * to the shared contract, which in turn forces a matching backend channel.
 */
describe('notification channel contract (frontend ↔ backend)', () => {
  it('the rendered CHANNEL_KEYS exactly match the shared contract', () => {
    expect([...CHANNEL_KEYS].sort()).toEqual(
      [...contract.user_facing_channels].sort(),
    );
  });

  it('CHANNEL_KEYS has no duplicates', () => {
    expect(new Set(CHANNEL_KEYS).size).toBe(CHANNEL_KEYS.length);
  });
});
