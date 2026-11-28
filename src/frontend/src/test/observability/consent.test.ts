import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import {
  ACCOUNT_SIGNAL_KEY,
  BROWSER_ERROR_REPORTS_VERSION,
  CONSENT_STORAGE_KEY,
  INITIAL_CONSENT_STATE,
  accountEpoch,
  hasPendingRevoke,
  readConsent,
  readConsentSnapshot,
  recordAccountDecision,
  resetConsentStoreForTests,
  setAccountConsent,
  setAccountResyncHandler,
  setAuthStatus,
  setPendingRevoke,
  subscribeConsent,
  writeConsent,
  type ConsentState,
} from '@/observability/consent';
import { useConsent } from '@/hooks/useConsent';

const GRANTED: ConsentState = {
  necessary: true,
  browser_error_reports: true,
  timestamp: '2026-11-28T12:00:00Z',
  version: BROWSER_ERROR_REPORTS_VERSION,
};
const DECLINED: ConsentState = { ...GRANTED, browser_error_reports: false };

function deviceDecision(): boolean | null {
  return readConsent().browser_error_reports;
}

/**
 * #2159/#3025 — the consent store is the single source the banner, the settings
 * and the error tracker read; a write here must reach every listener in this
 * tab and a write in another tab must reach them through the `storage` event.
 */
describe('consent store', () => {
  beforeEach(() => {
    resetConsentStoreForTests();
    window.localStorage.clear();
  });

  afterEach(() => {
    resetConsentStoreForTests();
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  describe('device decision', () => {
    it('reads an absent entry as undecided', () => {
      expect(readConsent()).toEqual(INITIAL_CONSENT_STATE);
    });

    it('reads a corrupt entry as undecided, never as consent', () => {
      window.localStorage.setItem(CONSENT_STORAGE_KEY, '{not json');
      expect(deviceDecision()).toBeNull();
    });

    it('accepts only real booleans as a decision', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ browser_error_reports: 'yes', necessary: false }),
      );
      expect(deviceDecision()).toBeNull();
      expect(readConsent().necessary).toBe(true);
    });

    // CP-005 (operator decision 2026-11-27): an old browser grant is not carried over; the app asks once anew.
    it('reads a grant stored before v1.3 (`error_tracking: true`) as undecided', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({
          necessary: true,
          error_tracking: true,
          external_services: true,
          version: '1.0',
        }),
      );
      expect(deviceDecision()).toBeNull();
    });

    it('keeps a decline stored before v1.3 (`error_tracking: false`) a decline', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ necessary: true, error_tracking: false, external_services: false }),
      );
      expect(deviceDecision()).toBe(false);
    });

    it('reads a grant to an older text version as undecided, a decline as a decline (CP-004)', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ ...GRANTED, version: '0.9' }),
      );
      expect(deviceDecision()).toBeNull();
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ ...DECLINED, version: '0.9' }),
      );
      expect(deviceDecision()).toBe(false);
    });

    it('writes the current shape and drops the retired categories (CK-003)', () => {
      writeConsent(GRANTED);
      expect(JSON.parse(window.localStorage.getItem(CONSENT_STORAGE_KEY)!)).toEqual(GRANTED);
    });

    it('returns the same snapshot while the entry is unchanged', () => {
      window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
      expect(readConsent()).toBe(readConsent());
      expect(readConsentSnapshot()).toBe(readConsentSnapshot());
    });

    it('persists a write and notifies listeners in this tab', () => {
      const listener = vi.fn();
      subscribeConsent(listener);

      writeConsent(GRANTED);

      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener.mock.calls[0]![0].device).toEqual(GRANTED);
    });

    it('notifies listeners on a storage event for its key from another tab', () => {
      const listener = vi.fn();
      subscribeConsent(listener);

      window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
      window.dispatchEvent(new StorageEvent('storage', { key: CONSENT_STORAGE_KEY }));

      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener.mock.calls[0]![0].device).toEqual(GRANTED);
    });

    it('treats localStorage.clear() in another tab as a change', () => {
      const listener = vi.fn();
      subscribeConsent(listener);
      window.dispatchEvent(new StorageEvent('storage', { key: null }));
      expect(listener).toHaveBeenCalledTimes(1);
    });

    it('ignores storage events for other keys', () => {
      const listener = vi.fn();
      subscribeConsent(listener);
      window.dispatchEvent(new StorageEvent('storage', { key: 'i18nextLng' }));
      expect(listener).not.toHaveBeenCalled();
    });

    it('stops notifying after unsubscribe', () => {
      const listener = vi.fn();
      const unsubscribe = subscribeConsent(listener);
      unsubscribe();

      writeConsent(GRANTED);
      window.dispatchEvent(new StorageEvent('storage', { key: CONSENT_STORAGE_KEY }));

      expect(listener).not.toHaveBeenCalled();
    });

    it('keeps notifying the others when one listener throws', () => {
      vi.spyOn(console, 'warn').mockImplementation(() => undefined);
      const later = vi.fn();
      subscribeConsent(() => {
        throw new Error('faulty');
      });
      subscribeConsent(later);

      writeConsent(GRANTED);

      expect(later).toHaveBeenCalledTimes(1);
    });
  });

  describe('when localStorage refuses the write', () => {
    function refuseWrites(): void {
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new DOMException('quota', 'QuotaExceededError');
      });
    }

    it('a revoke wins over the old grant still readable in storage', () => {
      window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
      expect(deviceDecision()).toBe(true);
      refuseWrites();

      writeConsent(DECLINED);

      expect(deviceDecision()).toBe(false);
    });

    it('an actively given first grant holds for this page view only', () => {
      refuseWrites();
      writeConsent(GRANTED);
      expect(deviceDecision()).toBe(true);
      expect(window.localStorage.getItem(CONSENT_STORAGE_KEY)).toBeNull();
    });

    it('yields to a newer decision written by another tab', () => {
      subscribeConsent(() => undefined);
      window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
      refuseWrites();
      writeConsent(DECLINED);
      vi.restoreAllMocks();

      window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
      window.dispatchEvent(new StorageEvent('storage', { key: CONSENT_STORAGE_KEY }));

      expect(deviceDecision()).toBe(true);
    });

    it('a pending revoke that cannot be stored holds in memory', () => {
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
      refuseWrites();
      setPendingRevoke('user-a', true);
      expect(hasPendingRevoke('user-a')).toBe(true);
      expect(readConsentSnapshot().pendingRevoke).toBe(true);
    });
  });

  describe('sign-in state and account consent', () => {
    it('starts with the sign-in state unknown and the account unknown (CP-008)', () => {
      const snap = readConsentSnapshot();
      expect(snap.auth.kind).toBe('unknown');
      expect(snap.account.kind).toBe('unknown');
    });

    it('drops the account answer and moves the epoch when the person changes (CP-009)', () => {
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
      expect(setAccountConsent('user-a', { kind: 'granted', confirmedAt: 1 }, accountEpoch())).toBe(
        true,
      );
      const before = accountEpoch();

      setAuthStatus({ kind: 'signed_in', account: 'user-b' });

      expect(readConsentSnapshot().account.kind).toBe('unknown');
      expect(accountEpoch()).toBeGreaterThan(before);
      // An answer for A arriving now is not applied to B.
      expect(setAccountConsent('user-a', { kind: 'granted', confirmedAt: 2 }, accountEpoch())).toBe(
        false,
      );
    });

    it('ignores an unchanged sign-in report (it runs on every store dispatch)', () => {
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
      const listener = vi.fn();
      subscribeConsent(listener);
      const epoch = accountEpoch();

      setAuthStatus({ kind: 'signed_in', account: 'user-a' });

      expect(listener).not.toHaveBeenCalled();
      expect(accountEpoch()).toBe(epoch);
    });

    it('discards an answer requested before a newer decision (CP-010)', () => {
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
      const requestedIn = accountEpoch();
      recordAccountDecision('user-a', { kind: 'denied' });

      expect(setAccountConsent('user-a', { kind: 'granted', confirmedAt: 1 }, requestedIn)).toBe(
        false,
      );
      expect(readConsentSnapshot().account.kind).toBe('denied');
    });

    it('stops at once on a revoke signal from another tab and asks for a re-read', () => {
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
      recordAccountDecision('user-a', { kind: 'granted', confirmedAt: Date.now() });
      const resync = vi.fn();
      setAccountResyncHandler(resync);
      subscribeConsent(() => undefined);
      const requestedIn = accountEpoch();

      window.dispatchEvent(
        new StorageEvent('storage', {
          key: ACCOUNT_SIGNAL_KEY,
          newValue: JSON.stringify({ revoked: true }),
        }),
      );

      expect(readConsentSnapshot().account.kind).toBe('denied');
      expect(resync).toHaveBeenCalledTimes(1);
      expect(accountEpoch()).toBeGreaterThan(requestedIn);
    });

    it('keeps a pending revoke per account under a hash, not the account key', () => {
      setPendingRevoke('user-a-key-123', true);
      expect(hasPendingRevoke('user-a-key-123')).toBe(true);
      expect(hasPendingRevoke('user-b')).toBe(false);
      const keys = Object.keys(window.localStorage);
      expect(keys.some((k) => k.startsWith('kamerplanter:consent:pending-revoke:'))).toBe(true);
      expect(keys.some((k) => k.includes('user-a-key-123'))).toBe(false);

      setPendingRevoke('user-a-key-123', false);
      expect(hasPendingRevoke('user-a-key-123')).toBe(false);
    });
  });

  describe('useConsent', () => {
    it('re-renders on a write and returns a stable object otherwise', () => {
      const { result, rerender } = renderHook(() => useConsent());
      const first = result.current;
      rerender();
      expect(result.current).toBe(first);
      expect(result.current.snapshot.device.browser_error_reports).toBeNull();

      act(() => writeConsent(GRANTED));

      expect(result.current.snapshot.device).toEqual(GRANTED);
      expect(result.current).not.toBe(first);
    });

    it('follows a decision from another tab', () => {
      const { result } = renderHook(() => useConsent());

      act(() => {
        window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
        window.dispatchEvent(new StorageEvent('storage', { key: CONSENT_STORAGE_KEY }));
      });

      expect(result.current.snapshot.device.browser_error_reports).toBe(true);
    });
  });
});
