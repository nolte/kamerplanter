import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import {
  CONSENT_STORAGE_KEY,
  INITIAL_CONSENT_STATE,
  hasConsent,
  readConsent,
  resetConsentStoreForTests,
  subscribeConsent,
  writeConsent,
  type ConsentState,
} from '@/observability/consent';
import { useConsent } from '@/hooks/useConsent';

const GRANTED: ConsentState = {
  necessary: true,
  error_tracking: true,
  external_services: false,
  timestamp: '2026-10-09T12:00:00Z',
  version: '1.0',
};

/**
 * #2159 — the consent store is the single source both the banner and the
 * error tracker read; a write here must reach every listener in this tab and
 * a write in another tab must reach them through the `storage` event.
 */
describe('consent store', () => {
  beforeEach(() => {
    resetConsentStoreForTests();
    window.localStorage.removeItem(CONSENT_STORAGE_KEY);
  });

  afterEach(() => {
    resetConsentStoreForTests();
    window.localStorage.removeItem(CONSENT_STORAGE_KEY);
    vi.restoreAllMocks();
  });

  it('reads an absent entry as undecided', () => {
    expect(readConsent()).toEqual(INITIAL_CONSENT_STATE);
    expect(hasConsent('error_tracking')).toBe(false);
  });

  it('reads a corrupt entry as undecided, never as consent', () => {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, '{not json');
    expect(readConsent().error_tracking).toBeNull();
  });

  it('accepts only real booleans as a decision', () => {
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ error_tracking: 'yes', external_services: 1, necessary: false }),
    );
    const state = readConsent();
    expect(state.error_tracking).toBeNull();
    expect(state.external_services).toBeNull();
    expect(state.necessary).toBe(true);
  });

  it('returns the same snapshot while the entry is unchanged', () => {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
    expect(readConsent()).toBe(readConsent());
  });

  it('persists a write and notifies listeners in this tab', () => {
    const listener = vi.fn();
    subscribeConsent(listener);

    writeConsent(GRANTED);

    expect(JSON.parse(window.localStorage.getItem(CONSENT_STORAGE_KEY)!)).toEqual(GRANTED);
    expect(listener).toHaveBeenCalledWith(GRANTED);
    expect(hasConsent('error_tracking')).toBe(true);
  });

  it('notifies listeners on a storage event for its key from another tab', () => {
    const listener = vi.fn();
    subscribeConsent(listener);

    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
    window.dispatchEvent(new StorageEvent('storage', { key: CONSENT_STORAGE_KEY }));

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0]![0]).toEqual(GRANTED);
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

  it('honours a decision in this page view when storage is unavailable', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('QuotaExceededError');
    });

    writeConsent(GRANTED);

    expect(hasConsent('error_tracking')).toBe(true);
  });

  describe('useConsent', () => {
    it('re-renders on a write and returns a stable object otherwise', () => {
      const { result, rerender } = renderHook(() => useConsent());
      const first = result.current;
      rerender();
      expect(result.current).toBe(first);
      expect(result.current.consent.error_tracking).toBeNull();

      act(() => result.current.setConsent(GRANTED));

      expect(result.current.consent).toEqual(GRANTED);
      expect(result.current).not.toBe(first);
    });

    it('follows a decision from another tab', () => {
      const { result } = renderHook(() => useConsent());

      act(() => {
        window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(GRANTED));
        window.dispatchEvent(new StorageEvent('storage', { key: CONSENT_STORAGE_KEY }));
      });

      expect(result.current.consent.error_tracking).toBe(true);
    });
  });
});
