/**
 * Browser-side consent state for browser error reports (UI-NFR-013 v1.3 §3.3, §5.4).
 *
 * The single place that decides whether this browser may send error reports.
 * Four inputs, one snapshot, one decision function:
 *
 * - the **device** decision — `kamerplanter:consent:v1` in localStorage, made by a
 *   click while signed out (CP-002) or reset in the privacy settings;
 * - the **sign-in** state — reported from the Redux auth slice by
 *   `consentAuthBridge.ts` in the initial chunk; `unknown` until the auth
 *   bootstrap has finished (CP-008);
 * - the **account** consent `browser_error_reports` — read from and written to
 *   the REQ-025 ConsentEngine by `consentSync.ts`, held in memory for this page
 *   view and only for the account it was read for (CP-006);
 * - a **pending revoke** of that account that has not reached the server yet
 *   (CP-009), kept per account under a device-local hash of the account key.
 *
 * Deliberately React-free: the error tracker has to gate `Sentry.init` before
 * the app mounts. The React binding is `useConsent` in `src/hooks/useConsent.ts`.
 *
 * A device grant never stands in for an account consent (operator decision
 * 2026-11-27): it may come from another person at this device and was given to a
 * text without an account. A device decline holds for everyone signed in here.
 */

export const CONSENT_STORAGE_KEY = 'kamerplanter:consent:v1';
const PENDING_REVOKE_PREFIX = 'kamerplanter:consent:pending-revoke:';
export const ACCOUNT_SIGNAL_KEY = 'kamerplanter:consent:account-signal';

/** The consent purpose of the REQ-025 ConsentEngine that switches browser error reports. */
export const BROWSER_ERROR_REPORTS = 'browser_error_reports';

/**
 * Version of the purpose text the banner shows (CP-004). Must equal the
 * backend's `ConsentPurpose.version` of `browser_error_reports`
 * (`src/backend/app/domain/engines/consent_engine.py`); the guard
 * `test_consent_purposes_are_read.py` compares the two. A device grant to an
 * older version reads as undecided; the server's version is checked in
 * `consentSync.ts`.
 */
export const BROWSER_ERROR_REPORTS_VERSION = '1.0';

/** An account grant older than this no longer counts until it is read again (CP-006, CP-011). */
export const ACCOUNT_GRANT_MAX_AGE_MS = 30 * 60_000;

/** The device decision as stored in localStorage. */
export interface ConsentState {
  necessary: true;
  /** `null` = not decided on this device. */
  browser_error_reports: boolean | null;
  timestamp: string | null;
  version: string;
  /**
   * The grant was given while signed in (confirmation, account grant, device
   * switch). It ends with the sign-out (UI-NFR-013 v1.6 CP-016); absent = given
   * signed out, which the device form's text says holds for this browser.
   */
  granted_signed_in?: true;
}

export const INITIAL_CONSENT_STATE: ConsentState = Object.freeze({
  necessary: true,
  browser_error_reports: null,
  timestamp: null,
  version: BROWSER_ERROR_REPORTS_VERSION,
}) as ConsentState;

/** Who is signed in. `unknown` until the auth bootstrap has completed. */
export type AuthStatus =
  | { readonly kind: 'unknown' }
  | { readonly kind: 'signed_out' }
  | { readonly kind: 'signed_in'; readonly account: string };

/** The account consent as known to this page view, for the account currently signed in. */
export type AccountConsent =
  | { readonly kind: 'unknown' }
  | { readonly kind: 'failed' }
  /** The server holds a different text version than this page shows (CP-013): reload. */
  | { readonly kind: 'outdated' }
  | { readonly kind: 'undecided' }
  | { readonly kind: 'denied' }
  | { readonly kind: 'granted'; readonly confirmedAt: number };

export interface ConsentSnapshot {
  readonly device: ConsentState;
  readonly auth: AuthStatus;
  readonly account: AccountConsent;
  /** A revoke of the signed-in account that has not reached the server yet. */
  readonly pendingRevoke: boolean;
}

/**
 * Which form of the banner to show, if any: `device` (signed out), `account` (no
 * account decision) or `confirm` (the account granted, this browser has not
 * decided — UI-NFR-013 v1.5 CP-014).
 */
export type ConsentPrompt = 'device' | 'account' | 'confirm' | null;

const UNKNOWN_AUTH: AuthStatus = Object.freeze({ kind: 'unknown' });
const SIGNED_OUT: AuthStatus = Object.freeze({ kind: 'signed_out' });
const UNKNOWN_ACCOUNT: AccountConsent = Object.freeze({ kind: 'unknown' });

/**
 * Whether this browser may send error reports now — the case table of
 * UI-NFR-013 §5.4. Light mode and a missing DSN are checked by the caller
 * (`trackingPermitted` in `errorTracking.ts`).
 */
export function browserReportsPermitted(snapshot: ConsentSnapshot, now: number): boolean {
  const device = snapshot.device.browser_error_reports;
  // CP-007: a decline on this device holds for everyone, whatever any account says.
  if (device === false) return false;
  const { auth, account } = snapshot;
  if (auth.kind === 'unknown') return false; // CP-008
  if (auth.kind === 'signed_out') return device === true;
  // Signed in: the person's own account consent AND this device's own grant
  // (CP-003, CP-006; operator decision 2026-11-28, v1.5 — confirmed once per browser).
  if (snapshot.pendingRevoke) return false; // CP-009
  if (device !== true) return false; // CP-014
  return account.kind === 'granted' && now - account.confirmedAt <= ACCOUNT_GRANT_MAX_AGE_MS;
}

/** {@link browserReportsPermitted} at this moment — for a status line that shows the decision. */
export function browserReportsPermittedNow(snapshot: ConsentSnapshot): boolean {
  return browserReportsPermitted(snapshot, Date.now());
}

/** Which banner to show (UI-NFR-013 §5.4): never before the sign-in state is known. */
export function consentPrompt(snapshot: ConsentSnapshot): ConsentPrompt {
  const device = snapshot.device.browser_error_reports;
  if (device === false) return null; // a decline is not asked again
  const { auth } = snapshot;
  if (auth.kind === 'unknown') return null;
  if (auth.kind === 'signed_out') return device === null ? 'device' : null;
  if (snapshot.pendingRevoke) return null;
  if (snapshot.account.kind === 'undecided') return 'account';
  // CP-014: the account granted, this browser has not decided — confirm it once.
  return snapshot.account.kind === 'granted' && device === null ? 'confirm' : null;
}

// ── Device decision ───────────────────────────────────────────────

type Listener = (snapshot: ConsentSnapshot) => void;

const listeners = new Set<Listener>();

/**
 * Snapshot cache keyed by the raw stored string, so repeated reads of an
 * unchanged entry return the same object — `useSyncExternalStore` requires a
 * stable snapshot or it re-renders forever.
 */
let cachedRaw: string | null = null;
let cachedState: ConsentState = INITIAL_CONSENT_STATE;

/**
 * The device decision this page made but could not persist (quota exceeded,
 * storage blocked). It wins over whatever storage still holds until the next
 * successful write here or a newer decision from another tab: a revoke stays a
 * revoke, and an actively given grant lasts until reload.
 */
let unpersisted: ConsentState | null = null;

function storageGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    // localStorage unavailable (private mode, blocked storage).
    return null;
  }
}

function parse(raw: string | null): ConsentState {
  if (!raw) return INITIAL_CONSENT_STATE;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown> | null;
    if (!parsed || typeof parsed !== 'object') return INITIAL_CONSENT_STATE;
    const version = typeof parsed.version === 'string' ? parsed.version : null;
    const value = parsed.browser_error_reports;
    let decision: boolean | null = null;
    if (value === false) {
      // A decline holds whatever text it was given to (CP-004).
      decision = false;
    } else if (value === true) {
      // A grant counts for the current text only; an older one asks again.
      decision = version === BROWSER_ERROR_REPORTS_VERSION ? true : null;
    } else if (parsed.error_tracking === false) {
      // CP-005: the decline of the pre-v1.3 entry stays a decline; its grant asks again.
      decision = false;
    }
    return {
      necessary: true,
      browser_error_reports: decision,
      timestamp: typeof parsed.timestamp === 'string' ? parsed.timestamp : null,
      version: version ?? BROWSER_ERROR_REPORTS_VERSION,
      ...(decision === true && parsed.granted_signed_in === true
        ? { granted_signed_in: true }
        : {}),
    };
  } catch {
    // A corrupt entry must read as "not decided", never as consent.
    return INITIAL_CONSENT_STATE;
  }
}

/** The device decision; the same object while the stored entry is unchanged. */
export function readConsent(): ConsentState {
  if (unpersisted) return unpersisted;
  const raw = storageGet(CONSENT_STORAGE_KEY);
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    cachedState = parse(raw);
  }
  return cachedState;
}

/** Persist a device decision and notify every listener in this tab. */
export function writeConsent(state: ConsentState): void {
  const next: ConsentState = {
    necessary: true,
    browser_error_reports: state.browser_error_reports,
    timestamp: state.timestamp,
    version: BROWSER_ERROR_REPORTS_VERSION,
    ...(state.browser_error_reports === true && state.granted_signed_in
      ? { granted_signed_in: true }
      : {}),
  };
  try {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(next));
    unpersisted = null;
  } catch {
    // Storage refused the write but may still return the *previous* decision
    // (quota exceeded): never let that older value stand in for this one.
    unpersisted = next;
  }
  notify();
}

/** Record a device decision made now (banner while signed out, settings reset). */
export function decideOnDevice(decision: boolean | null): void {
  writeConsent({
    ...INITIAL_CONSENT_STATE,
    browser_error_reports: decision,
    timestamp: decision === null ? null : new Date().toISOString(),
    // CP-016: remember that the grant was given signed in, so the sign-out ends it.
    ...(decision === true && auth.kind === 'signed_in' ? { granted_signed_in: true } : {}),
  });
}

/** The next banner that appears takes the focus (after the public reset link, N-d). */
let bannerFocusRequested = false;

/** Ask the consent banner to move focus to its heading when it appears next. */
export function requestConsentBannerFocus(): void {
  bannerFocusRequested = true;
}

/** Consume a pending focus request (the banner calls this once it is on screen). */
export function takeConsentBannerFocusRequest(): boolean {
  const requested = bannerFocusRequested;
  bannerFocusRequested = false;
  return requested;
}

/**
 * CP-016: once this tab knows nobody is signed in — sign-out, expired session, a
 * start without session — a device grant given while signed in is reset to
 * undecided. A device grant given signed out and every decline stay.
 */
function endSignedInDeviceGrant(): void {
  const device = readConsent();
  if (device.browser_error_reports === true && device.granted_signed_in) decideOnDevice(null);
}

// ── Sign-in state and account consent ─────────────────────────────

let auth: AuthStatus = UNKNOWN_AUTH;
let account: AccountConsent = UNKNOWN_ACCOUNT;

/**
 * Bumped by every change that makes an account answer in flight stale: a
 * sign-in change, a decision in this tab, a decision signalled by another tab.
 * `consentSync.ts` captures it before a request and discards the answer when it
 * moved meanwhile (CP-010).
 */
let epoch = 0;

/** Called when another tab signals an account decision; set by `consentSync.ts`. */
let resyncHandler: (() => void) | null = null;

/** Report the sign-in state. Cheap when nothing changed — it runs on every store dispatch. */
export function setAuthStatus(next: AuthStatus): void {
  const same =
    next.kind === auth.kind &&
    (next.kind !== 'signed_in' || (auth.kind === 'signed_in' && auth.account === next.account));
  if (same) return;
  auth = next.kind === 'signed_out' ? SIGNED_OUT : next.kind === 'unknown' ? UNKNOWN_AUTH : next;
  // CP-009: what was read for the previous person never counts for the next one.
  account = UNKNOWN_ACCOUNT;
  epoch += 1;
  if (auth.kind === 'signed_out') endSignedInDeviceGrant();
  notify();
}

/** The current epoch (see {@link epoch}). */
export function accountEpoch(): number {
  return epoch;
}

function isSignedInAs(accountKey: string): boolean {
  return auth.kind === 'signed_in' && auth.account === accountKey;
}

/**
 * Store an answer the server gave for `accountKey`, unless it is stale: the
 * person changed, or a newer decision happened since the request started.
 *
 * @returns whether the answer was applied.
 */
export function setAccountConsent(
  accountKey: string,
  next: AccountConsent,
  startedIn: number,
): boolean {
  if (!isSignedInAs(accountKey) || startedIn !== epoch) return false;
  account = next;
  notify();
  return true;
}

/**
 * Record a decision this tab just made or confirmed for `accountKey`. Makes
 * every answer still in flight stale.
 *
 * @returns whether `accountKey` is still the signed-in account.
 */
export function recordAccountDecision(accountKey: string, next: AccountConsent): boolean {
  if (!isSignedInAs(accountKey)) return false;
  epoch += 1;
  account = next;
  notify();
  return true;
}

/** Register the function that re-reads the account consent (one, set by `consentSync.ts`). */
export function setAccountResyncHandler(handler: (() => void) | null): void {
  resyncHandler = handler;
}

/** Tell the other tabs that this tab changed the account consent (CP-010). */
export function signalAccountChange(revoked: boolean): void {
  try {
    window.localStorage.setItem(
      ACCOUNT_SIGNAL_KEY,
      JSON.stringify({ revoked, nonce: `${Date.now()}-${Math.random()}` }),
    );
  } catch (error) {
    // The other tabs still re-read on their own triggers (CP-011).
    console.warn('[consent] could not signal the other tabs', error);
  }
}

// ── Pending revokes ───────────────────────────────────────────────

/**
 * A device-local, non-cryptographic 53-bit hash of the account key (cyrb53).
 * The entry has to outlive a sign-out (CP-009), so it must not carry the key
 * itself (07 PRIV-512); a collision would need two accounts on one device with
 * the same 53-bit hash.
 */
function accountHash(accountKey: string): string {
  let h1 = 0xdeadbeef;
  let h2 = 0x41c6ce57;
  for (let i = 0; i < accountKey.length; i += 1) {
    const ch = accountKey.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
}

/** Pending revokes this page could not persist; they hold until reload. */
const unpersistedRevokes = new Set<string>();

function pendingKey(accountKey: string): string {
  return `${PENDING_REVOKE_PREFIX}${accountHash(accountKey)}`;
}

/** Whether a revoke of `accountKey` is waiting to be sent. */
export function hasPendingRevoke(accountKey: string): boolean {
  const key = pendingKey(accountKey);
  return unpersistedRevokes.has(key) || storageGet(key) !== null;
}

/** Mark or clear a pending revoke of `accountKey`, and notify. */
export function setPendingRevoke(accountKey: string, pending: boolean): void {
  const key = pendingKey(accountKey);
  try {
    if (pending) window.localStorage.setItem(key, '1');
    else window.localStorage.removeItem(key);
    unpersistedRevokes.delete(key);
  } catch {
    if (pending) unpersistedRevokes.add(key);
    else unpersistedRevokes.delete(key);
  }
  notify();
}

// ── Snapshot and subscription ─────────────────────────────────────

let snapshot: ConsentSnapshot | null = null;

/** The current snapshot; the same object while nothing changed. */
export function readConsentSnapshot(): ConsentSnapshot {
  const device = readConsent();
  const pendingRevoke = auth.kind === 'signed_in' ? hasPendingRevoke(auth.account) : false;
  if (
    !snapshot ||
    snapshot.device !== device ||
    snapshot.auth !== auth ||
    snapshot.account !== account ||
    snapshot.pendingRevoke !== pendingRevoke
  ) {
    snapshot = { device, auth, account, pendingRevoke };
  }
  return snapshot;
}

function notify(): void {
  const current = readConsentSnapshot();
  for (const listener of [...listeners]) {
    try {
      listener(current);
    } catch (error) {
      // One faulty listener must not keep the others from learning of a revoke.
      console.warn('[consent] listener failed', error);
    }
  }
}

function onAccountSignal(raw: string | null): void {
  let revoked = false;
  try {
    revoked = raw !== null && (JSON.parse(raw) as { revoked?: unknown }).revoked === true;
  } catch (error) {
    // An unreadable signal still means "re-read".
    console.warn('[consent] unreadable account signal', error);
  }
  epoch += 1;
  // A revoke elsewhere stops this tab at once; the re-read below confirms it.
  if (revoked && auth.kind === 'signed_in') account = { kind: 'denied' };
  resyncHandler?.();
}

function onStorage(event: StorageEvent): void {
  if (event.key === null) {
    // `localStorage.clear()` in another tab: every decision stored here is gone.
    unpersisted = null;
    notify();
    return;
  }
  if (event.key === CONSENT_STORAGE_KEY) {
    // Another tab persisted a newer decision; it supersedes our unsaved one.
    unpersisted = null;
  } else if (event.key === ACCOUNT_SIGNAL_KEY) {
    onAccountSignal(event.newValue);
  } else if (!event.key.startsWith(PENDING_REVOKE_PREFIX)) {
    return;
  }
  notify();
}

/**
 * Register a listener for consent changes (this tab and other tabs).
 *
 * @returns the unsubscribe function.
 */
export function subscribeConsent(listener: Listener): () => void {
  if (listeners.size === 0) window.addEventListener('storage', onStorage);
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) window.removeEventListener('storage', onStorage);
  };
}

/** Test seam: drop every listener, the caches and the in-memory state. */
export function resetConsentStoreForTests(): void {
  listeners.clear();
  window.removeEventListener('storage', onStorage);
  cachedRaw = null;
  cachedState = INITIAL_CONSENT_STATE;
  unpersisted = null;
  unpersistedRevokes.clear();
  auth = UNKNOWN_AUTH;
  account = UNKNOWN_ACCOUNT;
  epoch += 1;
  resyncHandler = null;
  snapshot = null;
  bannerFocusRequested = false;
}
