import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import authReducer, { clearAuth, fetchProfile } from '@/store/slices/authSlice';
import type { UserProfile } from '@/api/types';
import {
  ACCOUNT_SIGNAL_KEY,
  CONSENT_STORAGE_KEY,
  browserReportsPermitted,
  consentPrompt,
  decideOnDevice,
  hasPendingRevoke,
  readConsentSnapshot,
  resetConsentStoreForTests,
} from '@/observability/consent';
import {
  bindConsentToAuth,
  resetConsentAuthBridgeForTests,
} from '@/observability/consentAuthBridge';
import {
  RECHECK_INTERVAL_MS,
  decideAccountConsent,
  resetConsentSyncForTests,
} from '@/observability/consentSync';

/**
 * #3025 N-40 — the account reconciliation over the production path: the real
 * auth reducer, the bridge from `main.tsx`, the lazily loaded sync module, the
 * real API client and MSW as the server. The server keeps one record per
 * account; `signedIn` says whose token the requests carry.
 */
const DSN = 'https://key@tracker.example/1';

interface ServerRecord {
  granted: boolean;
  consent_version: string | null;
  revoked_at: string | null;
}

let records: Record<string, ServerRecord>;
let signedIn: string | null;
let calls: string[];
let purposeVersion: string;
let failGet: boolean;
let failDelete: boolean;
let failPost: boolean;
let holdGet: Promise<void> | null;
let postedVersions: (string | undefined)[];

function record(user: string): ServerRecord {
  return records[user] ?? { granted: false, consent_version: null, revoked_at: null };
}

function body(user: string, snapshot: ServerRecord = record(user)) {
  return {
    purpose: 'browser_error_reports',
    label: 'Send error reports from the browser',
    description: '…',
    legal_basis: 'Art. 6(1)(a) GDPR',
    required: false,
    granted: snapshot.granted,
    granted_at: snapshot.granted ? '2026-11-28T09:00:00Z' : null,
    revoked_at: snapshot.revoked_at,
    consent_version: snapshot.consent_version,
    purpose_version: purposeVersion,
  };
}

function installServer(): void {
  server.use(
    http.get('/api/v1/privacy/consents', async () => {
      calls.push(`GET ${signedIn}`);
      if (failGet) return new HttpResponse(null, { status: 503 });
      const user = signedIn!;
      // The answer is what the server held when the request arrived.
      const asOfRequest = { ...record(user) };
      if (holdGet) await holdGet;
      return HttpResponse.json([body(user, asOfRequest)]);
    }),
    http.post('/api/v1/privacy/consents', async ({ request }) => {
      calls.push(`POST ${signedIn}`);
      if (failPost) return new HttpResponse(null, { status: 503 });
      const sent = (await request.json()) as { purpose_version?: string };
      postedVersions.push(sent.purpose_version);
      // REQ-025 v1.42: like the real server, refuse a grant to another text and write nothing.
      if (sent.purpose_version !== purposeVersion) {
        return HttpResponse.json(
          {
            error_id: 'e1',
            error_code: 'CONSENT_TEXT_OUTDATED',
            message: 'The text changed.',
            details: [],
            path: '/api/v1/privacy/consents',
            method: 'POST',
          },
          { status: 409 },
        );
      }
      records[signedIn!] = { granted: true, consent_version: purposeVersion, revoked_at: null };
      return HttpResponse.json(body(signedIn!), { status: 201 });
    }),
    http.delete('/api/v1/privacy/consents/:purpose', () => {
      calls.push(`DELETE ${signedIn}`);
      if (failDelete) return new HttpResponse(null, { status: 503 });
      records[signedIn!] = {
        granted: false,
        consent_version: purposeVersion,
        revoked_at: '2026-11-28T10:00:00Z',
      };
      return HttpResponse.json(body(signedIn!));
    }),
  );
}

function profile(key: string): UserProfile {
  return {
    key,
    email: `${key}@example.com`,
    display_name: key,
    email_verified: true,
    is_active: true,
    avatar_url: null,
    locale: 'de',
    timezone: 'Europe/Berlin',
    last_login_at: null,
    created_at: null,
    is_platform_admin: false,
  };
}

function makeStore() {
  const store = configureStore({ reducer: { auth: authReducer } });
  const unbind = bindConsentToAuth(store);
  return { store, unbind };
}

type Store = ReturnType<typeof makeStore>['store'];

function signIn(store: Store, key: string): void {
  signedIn = key;
  store.dispatch(fetchProfile.fulfilled(profile(key), 'test', undefined));
}

function signOut(store: Store): void {
  signedIn = null;
  store.dispatch(clearAuth());
}

async function accountSettles(kind: string): Promise<void> {
  await vi.waitFor(() => expect(readConsentSnapshot().account.kind).toBe(kind));
}

function sends(): boolean {
  return browserReportsPermitted(readConsentSnapshot(), Date.now());
}

describe('account consent reconciliation (UI-NFR-013 v1.3 §5.4)', () => {
  let unbind: (() => void) | null = null;

  beforeEach(() => {
    resetConsentSyncForTests();
    resetConsentAuthBridgeForTests();
    resetConsentStoreForTests();
    window.localStorage.clear();
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
    records = {};
    signedIn = null;
    calls = [];
    purposeVersion = '1.0';
    failGet = false;
    failDelete = false;
    failPost = false;
    holdGet = null;
    postedVersions = [];
    installServer();
  });

  afterEach(() => {
    unbind?.();
    unbind = null;
    resetConsentSyncForTests();
    resetConsentAuthBridgeForTests();
    resetConsentStoreForTests();
    window.localStorage.clear();
    delete window.__RUNTIME_CONFIG__;
    vi.restoreAllMocks();
  });

  function boot(): Store {
    const made = makeStore();
    unbind = made.unbind;
    return made.store;
  }

  it('reports "sign-in unknown" until the auth bootstrap is done (CP-008)', () => {
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, browser_error_reports: true, version: '1.0' }),
    );
    const store = boot();
    expect(readConsentSnapshot().auth.kind).toBe('unknown');
    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();

    signOut(store);
    expect(readConsentSnapshot().auth.kind).toBe('signed_out');
    expect(sends()).toBe(true);
  });

  // The blocking finding of the earlier attempt (B-1): a browser grant must never become an account consent.
  it.each([
    [
      'a grant from before v1.3',
      { necessary: true, error_tracking: true, external_services: true },
    ],
    [
      'a grant made before signing in',
      { necessary: true, browser_error_reports: true, version: '1.0' },
    ],
  ])('a login with %s creates no account consent and asks the account', async (_label, stored) => {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(stored));
    const store = boot();

    signIn(store, 'user-a');
    await accountSettles('undecided');

    expect(calls).toEqual(['GET user-a']);
    expect(records['user-a']).toBeUndefined();
    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBe('account');
  });

  // Operator decision 2026-11-28 (UI-NFR-013 v1.5 CP-014): confirmed once per browser.
  it('an account grant from another device does not send from an undecided browser until it is confirmed', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    const store = boot();

    signIn(store, 'user-a');
    await accountSettles('granted');

    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBe('confirm');

    // "Ja, von diesem Gerät": the device decision only — no new account record.
    calls = [];
    decideOnDevice(true);
    expect(sends()).toBe(true);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();
    expect(calls).toEqual([]);
  });

  it('"not from this device" declines the device only; the account consent stays', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');
    calls = [];

    decideOnDevice(false);

    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();
    expect(calls).toEqual([]);
    expect(records['user-a']!.granted).toBe(true);

    // Resetting the device leads back to the question (N-6).
    decideOnDevice(null);
    expect(consentPrompt(readConsentSnapshot())).toBe('confirm');
  });

  // Operator decision 3: a signed-out decline holds for this device and revokes nothing.
  it('a decline on this device holds against an account grant and leaves the account alone', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, browser_error_reports: false, version: '1.0' }),
    );
    const store = boot();

    signIn(store, 'user-a');
    await accountSettles('granted');

    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();
    expect(calls).toEqual(['GET user-a']);
    expect(records['user-a']!.granted).toBe(true);
  });

  it('a grant to an older text of the purpose asks again (CP-004)', async () => {
    records['user-a'] = { granted: true, consent_version: '0.9', revoked_at: null };
    const store = boot();

    signIn(store, 'user-a');
    await accountSettles('undecided');

    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBe('account');
  });

  it('a server whose purpose text differs from this browser’s is "outdated": no report, no question (CP-013)', async () => {
    purposeVersion = '2.0';
    records['user-a'] = { granted: true, consent_version: '2.0', revoked_at: null };
    const store = boot();

    signIn(store, 'user-a');
    await accountSettles('outdated');

    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();
  });

  it('a failed read is no consent and no question; the network coming back reads again (CP-012)', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    failGet = true;
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, browser_error_reports: true, version: '1.0' }),
    );
    const store = boot();

    signIn(store, 'user-a');
    await accountSettles('failed');
    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();

    failGet = false;
    window.dispatchEvent(new Event('online'));
    await accountSettles('granted');
    expect(sends()).toBe(true);
  });

  it('the person’s own click grants for the current text', async () => {
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('undecided');

    await expect(decideAccountConsent(true)).resolves.toBe('confirmed');
    // CP-015: one click confirms the account and this browser.
    expect(readConsentSnapshot().device.browser_error_reports).toBe(true);

    expect(records['user-a']).toEqual({ granted: true, consent_version: '1.0', revoked_at: null });
    expect(sends()).toBe(true);
  });

  it('a grant sends the version shown; a newer text on the server writes nothing (F-2, CP-013)', async () => {
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('undecided');
    // The backend moved on to text 1.1 while this page still shows 1.0 (e.g. a cached bundle).
    purposeVersion = '1.1';

    await expect(decideAccountConsent(true)).resolves.toBe('outdated');

    expect(postedVersions).toEqual(['1.0']);
    expect(records['user-a']).toBeUndefined();
    expect(readConsentSnapshot().account.kind).toBe('outdated');
    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBeNull();
    // S-4 b: the device was not written either.
    expect(readConsentSnapshot().device.browser_error_reports).toBeNull();
    expect(window.localStorage.getItem(CONSENT_STORAGE_KEY)).toBeNull();
  });

  it('a failed grant changes nothing (CP-012)', async () => {
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('undecided');
    failPost = true;

    await expect(decideAccountConsent(true)).resolves.toBe('failed');

    expect(readConsentSnapshot().account.kind).toBe('undecided');
    expect(sends()).toBe(false);
    // S-4 b: no device grant from a failed account grant.
    expect(readConsentSnapshot().device.browser_error_reports).toBeNull();
  });

  // S-4 a: CP-015 — the account grant does not lift a decline of this device.
  it('a declined device stays declined when the account is granted in this browser', async () => {
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, browser_error_reports: false, version: '1.0' }),
    );
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('undecided');

    await expect(decideAccountConsent(true)).resolves.toBe('confirmed');

    expect(records['user-a']!.granted).toBe(true);
    expect(readConsentSnapshot().device.browser_error_reports).toBe(false);
    expect(sends()).toBe(false);
  });

  // CP-016 (v1.6): a device grant given signed in ends with the sign-out.
  describe('sign-out ends a signed-in device grant (CP-016)', () => {
    it('scenario A: A confirms, signs out — the next person on the sign-in page is asked, nothing is sent', async () => {
      records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
      const store = boot();
      signIn(store, 'user-a');
      await accountSettles('granted');
      decideOnDevice(true); // "Ja, von diesem Gerät"
      expect(sends()).toBe(true);
      expect(JSON.parse(window.localStorage.getItem(CONSENT_STORAGE_KEY)!).granted_signed_in).toBe(
        true,
      );

      signOut(store);

      expect(readConsentSnapshot().device.browser_error_reports).toBeNull();
      expect(sends()).toBe(false);
      expect(consentPrompt(readConsentSnapshot())).toBe('device');
    });

    it('scenario B: B signs in with an account grant — the confirmation is asked instead of sending', async () => {
      records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
      records['user-b'] = { granted: true, consent_version: '1.0', revoked_at: null };
      const store = boot();
      signIn(store, 'user-a');
      await accountSettles('granted');
      decideOnDevice(true);
      signOut(store);

      signIn(store, 'user-b');
      await accountSettles('granted');

      expect(sends()).toBe(false);
      expect(consentPrompt(readConsentSnapshot())).toBe('confirm');
    });

    it('a grant given signed out, and any decline, survive the sign-out', async () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ necessary: true, browser_error_reports: true, version: '1.0' }),
      );
      const store = boot();
      signOut(store);
      signIn(store, 'user-a');
      await accountSettles('undecided');
      signOut(store);
      expect(readConsentSnapshot().device.browser_error_reports).toBe(true);

      signIn(store, 'user-a');
      await accountSettles('undecided');
      decideOnDevice(false);
      signOut(store);
      expect(readConsentSnapshot().device.browser_error_reports).toBe(false);
    });

    it('a start without a session ends a signed-in grant left from before (expired session, closed tab)', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({
          necessary: true,
          browser_error_reports: true,
          version: '1.0',
          granted_signed_in: true,
        }),
      );
      const store = boot();
      signOut(store); // the bootstrap ends without a session

      expect(readConsentSnapshot().device.browser_error_reports).toBeNull();
      expect(sends()).toBe(false);
    });
  });

  it('a failed revoke stops at once, stays pending for that account across a switch, and is sent first (B-3)', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');
    failDelete = true;

    await expect(decideAccountConsent(false)).resolves.toBe('failed');
    expect(sends()).toBe(false);
    expect(hasPendingRevoke('user-a')).toBe(true);

    // Another person signs in here: A's pending revoke is neither sent with B's token nor lost.
    failDelete = false;
    calls = [];
    signOut(store);
    signIn(store, 'user-b');
    await accountSettles('undecided');
    expect(calls).toEqual(['GET user-b']);
    expect(hasPendingRevoke('user-a')).toBe(true);

    // A comes back: the revoke goes first, then the read.
    calls = [];
    signOut(store);
    signIn(store, 'user-a');
    await accountSettles('denied');
    expect(calls).toEqual(['DELETE user-a', 'GET user-a']);
    expect(hasPendingRevoke('user-a')).toBe(false);
    expect(records['user-a']!.granted).toBe(false);
    expect(sends()).toBe(false);
  });

  it('while a revoke is pending the browser does not send, whatever the server still says', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    failDelete = true;
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');
    await decideAccountConsent(false);

    // The next read fails to deliver the revoke and still finds the grant on the server.
    window.dispatchEvent(new Event('online'));
    await vi.waitFor(() => expect(calls.filter((c) => c.startsWith('DELETE'))).toHaveLength(2));

    expect(records['user-a']!.granted).toBe(true);
    expect(sends()).toBe(false);
  });

  it('a read requested before another tab’s revoke does not overwrite it (B-4)', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');

    // A re-read starts and the server answers "granted" as of that moment, but slowly…
    let release!: () => void;
    holdGet = new Promise<void>((resolve) => {
      release = resolve;
    });
    calls = [];
    window.dispatchEvent(new Event('online'));
    await vi.waitFor(() => expect(calls).toEqual(['GET user-a']));

    // …meanwhile the other tab revokes and signals it.
    records['user-a'] = {
      granted: false,
      consent_version: '1.0',
      revoked_at: '2026-11-28T10:00:00Z',
    };
    window.localStorage.setItem(ACCOUNT_SIGNAL_KEY, JSON.stringify({ revoked: true, nonce: 'x' }));
    window.dispatchEvent(
      new StorageEvent('storage', {
        key: ACCOUNT_SIGNAL_KEY,
        newValue: JSON.stringify({ revoked: true, nonce: 'x' }),
      }),
    );
    expect(readConsentSnapshot().account.kind).toBe('denied');
    expect(sends()).toBe(false);

    holdGet = null;
    release();

    // The stale "granted" is discarded and read again.
    await vi.waitFor(() => expect(calls).toEqual(['GET user-a', 'GET user-a']));
    await accountSettles('denied');
    expect(sends()).toBe(false);
  });

  it('signing out drops the account answer; the device decides again', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');
    decideOnDevice(true);
    expect(sends()).toBe(true);

    signOut(store);
    expect(readConsentSnapshot().account.kind).toBe('unknown');
    // CP-016: the grant was given signed in, so the sign-out ends it.
    expect(readConsentSnapshot().device.browser_error_reports).toBeNull();
    expect(sends()).toBe(false);
    expect(consentPrompt(readConsentSnapshot())).toBe('device');
  });

  it('a switch to another account never carries the previous account’s grant (CP-009)', async () => {
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    let release!: () => void;
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');

    holdGet = new Promise<void>((resolve) => {
      release = resolve;
    });
    signOut(store);
    signIn(store, 'user-b');

    // B's answer is still in flight: nothing counts for B yet.
    expect(readConsentSnapshot().account.kind).toBe('unknown');
    expect(sends()).toBe(false);
    holdGet = null;
    release();
    await accountSettles('undecided');
    expect(sends()).toBe(false);
  });

  it('a long-open visible tab re-reads every ten minutes, a hidden one does not (CP-011)', async () => {
    // Capture only the reconciliation's own timer; every other interval (the test
    // runner's polling) runs as usual.
    const intervals: [() => void, number | undefined][] = [];
    const realSetInterval = window.setInterval.bind(window);
    vi.spyOn(window, 'setInterval').mockImplementation(((
      fn: () => void,
      ms?: number,
      ...rest: unknown[]
    ) => {
      if (ms !== RECHECK_INTERVAL_MS) return realSetInterval(fn, ms, ...rest);
      intervals.push([fn, ms]);
      return realSetInterval(() => undefined, 1_000_000);
    }) as typeof window.setInterval);
    records['user-a'] = { granted: true, consent_version: '1.0', revoked_at: null };
    const store = boot();
    signIn(store, 'user-a');
    await accountSettles('granted');
    const tick = intervals.find(([, ms]) => ms === RECHECK_INTERVAL_MS)?.[0];
    expect(tick).toBeDefined();

    // Revoked on another device; this tab learns it on the next tick.
    records['user-a'] = {
      granted: false,
      consent_version: '1.0',
      revoked_at: '2026-11-28T10:00:00Z',
    };
    calls = [];
    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden');
    tick!();
    expect(calls).toEqual([]);

    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible');
    tick!();
    await accountSettles('denied');
    expect(sends()).toBe(false);
  });

  it('does not load or run the reconciliation without a DSN', async () => {
    delete window.__RUNTIME_CONFIG__;
    const store = boot();
    signIn(store, 'user-a');
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(calls).toEqual([]);
    expect(readConsentSnapshot().account.kind).toBe('unknown');
  });
});
