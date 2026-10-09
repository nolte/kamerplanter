/**
 * Browser-side consent state (UI-NFR-013 §3.3 CP-002, §3.5 CI-001/CI-003).
 *
 * The single reader and writer of the `kamerplanter:consent:v1` localStorage
 * entry. It is deliberately React-free: the error-tracking module has to gate
 * `Sentry.init` on it before the app mounts and react to a later decision
 * without a component in between. The React binding is `useConsent` in
 * `src/hooks/useConsent.ts`.
 *
 * Listeners fire on a write in this tab and on the `storage` event another tab
 * raises for the same key, so a revoke in one tab stops tracking in all of them.
 *
 * The server-side sync with the REQ-025 ConsentEngine (`POST/DELETE
 * /api/v1/privacy/consents`, CP-001/CP-003/CW-005) is a documented follow-up;
 * until it lands, this browser's own decision is the only one the frontend reads.
 */

export const CONSENT_STORAGE_KEY = 'kamerplanter:consent:v1';

/** Version of the consent texts the decision refers to (CP-004). */
export const CONSENT_VERSION = '1.0';

export interface ConsentState {
  necessary: true;
  /** `null` = not decided yet; only `true` permits error tracking. */
  error_tracking: boolean | null;
  external_services: boolean | null;
  timestamp: string | null;
  version: string;
}

export type OptionalConsentCategory = 'error_tracking' | 'external_services';

export const INITIAL_CONSENT_STATE: ConsentState = Object.freeze({
  necessary: true,
  error_tracking: null,
  external_services: null,
  timestamp: null,
  version: CONSENT_VERSION,
}) as ConsentState;

type Listener = (state: ConsentState) => void;

const listeners = new Set<Listener>();

/**
 * Snapshot cache keyed by the raw stored string, so repeated reads of an
 * unchanged entry return the same object — `useSyncExternalStore` requires a
 * stable snapshot or it re-renders forever.
 */
let cachedRaw: string | null = null;
let cachedState: ConsentState = INITIAL_CONSENT_STATE;

function readRaw(): string | null {
  try {
    return window.localStorage.getItem(CONSENT_STORAGE_KEY);
  } catch {
    // localStorage unavailable (private mode, blocked storage): undecided.
    return null;
  }
}

/** Accept only the three values the contract knows; anything else is undecided. */
function decision(value: unknown): boolean | null {
  return value === true || value === false ? value : null;
}

function parse(raw: string | null): ConsentState {
  if (!raw) return INITIAL_CONSENT_STATE;
  try {
    const parsed = JSON.parse(raw) as Partial<ConsentState> | null;
    if (!parsed || typeof parsed !== 'object') return INITIAL_CONSENT_STATE;
    return {
      necessary: true,
      error_tracking: decision(parsed.error_tracking),
      external_services: decision(parsed.external_services),
      timestamp: typeof parsed.timestamp === 'string' ? parsed.timestamp : null,
      version: typeof parsed.version === 'string' ? parsed.version : CONSENT_VERSION,
    };
  } catch {
    // A corrupt entry must read as "not decided", never as consent.
    return INITIAL_CONSENT_STATE;
  }
}

/** The current consent state; the same object while the stored entry is unchanged. */
export function readConsent(): ConsentState {
  const raw = readRaw();
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    cachedState = parse(raw);
  }
  return cachedState;
}

/** Whether the user has explicitly granted the given optional category. */
export function hasConsent(category: OptionalConsentCategory): boolean {
  return readConsent()[category] === true;
}

function notify(): void {
  const state = readConsent();
  for (const listener of [...listeners]) {
    try {
      listener(state);
    } catch (error) {
      // One faulty listener must not keep the others from learning of a revoke.
      console.warn('[consent] listener failed', error);
    }
  }
}

/** Persist a decision and notify every listener in this tab. */
export function writeConsent(state: ConsentState): void {
  try {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify({ ...state, necessary: true }));
  } catch {
    /* localStorage unavailable — the decision still applies to this page view */
  }
  // Seed the cache from the written state so a tab without working storage
  // still honours the decision it just made.
  cachedRaw = readRaw();
  cachedState = cachedRaw === null ? { ...state, necessary: true } : parse(cachedRaw);
  notify();
}

function onStorage(event: StorageEvent): void {
  // `key === null` is `localStorage.clear()` in another tab: the decision is gone.
  if (event.key !== null && event.key !== CONSENT_STORAGE_KEY) return;
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

/** Test seam: drop every listener and the snapshot cache. */
export function resetConsentStoreForTests(): void {
  listeners.clear();
  window.removeEventListener('storage', onStorage);
  cachedRaw = null;
  cachedState = INITIAL_CONSENT_STATE;
}
