/**
 * Reconciliation of the account consent `browser_error_reports` with the REQ-025
 * ConsentEngine (UI-NFR-013 v1.3 CP-001, CP-003, CP-009…CP-012).
 *
 * Its own chunk: loaded by `consentAuthBridge.ts` on the first sign-in of a page
 * view (and imported by the banner and the privacy settings, both lazy). Nothing
 * here ever sends a device decision to the server — a login only *reads* the
 * account (CP-003); the account changes only through `decideAccountConsent`,
 * which the banner and the settings call on a click of the signed-in person.
 */

import { grantConsent, listConsents, revokeConsent } from '@/api/endpoints/privacy';
import { isApiError } from '@/api/errors';
import type { ConsentRecord } from '@/api/types';
import {
  BROWSER_ERROR_REPORTS,
  BROWSER_ERROR_REPORTS_VERSION,
  accountEpoch,
  decideOnDevice,
  hasPendingRevoke,
  readConsentSnapshot,
  recordAccountDecision,
  setAccountConsent,
  setAccountResyncHandler,
  setPendingRevoke,
  signalAccountChange,
  subscribeConsent,
  type AccountConsent,
} from '@/observability/consent';

/** Re-read while visible, this often (CP-011). */
export const RECHECK_INTERVAL_MS = 10 * 60_000;

/** A tab becoming visible again re-reads at most this often (CP-011). */
export const VISIBLE_RECHECK_MIN_MS = 60_000;

/** Result of a decision of the signed-in person; `outdated` = the text changed, reload (CP-013). */
export type AccountWriteResult = 'confirmed' | 'failed' | 'outdated';

/** The backend's code for a grant to a text version that is not the current one (REQ-025 v1.42). */
export const CONSENT_TEXT_OUTDATED = 'CONSENT_TEXT_OUTDATED';

/**
 * The account consent from a `GET /privacy/consents` answer.
 *
 * A grant counts only for the text this browser shows: the record's version, the
 * purpose's current version and {@link BROWSER_ERROR_REPORTS_VERSION} must all
 * agree. A server whose purpose version differs from ours (frontend and backend
 * out of step) cannot have a decision recorded against the text we show, so the
 * state is `failed` rather than a question about a text the server does not know.
 */
export function accountConsentFrom(records: readonly ConsentRecord[], now: number): AccountConsent {
  const record = records.find((r) => r.purpose === BROWSER_ERROR_REPORTS);
  if (!record) return { kind: 'failed' };
  // CP-013: the server holds another text than this page shows (e.g. a cached bundle) — reload.
  if (record.purpose_version !== BROWSER_ERROR_REPORTS_VERSION) return { kind: 'outdated' };
  if (record.granted) {
    return record.consent_version === record.purpose_version
      ? { kind: 'granted', confirmedAt: now }
      : // A grant to an older text: ask again (CP-004).
        { kind: 'undecided' };
  }
  // A revoke stays a revoke whatever text it was given to; no record is "no answer yet".
  return record.revoked_at !== null || record.consent_version !== null
    ? { kind: 'denied' }
    : { kind: 'undecided' };
}

let running: Promise<void> | null = null;
let again = false;

async function reconcileOnce(): Promise<void> {
  const { auth } = readConsentSnapshot();
  if (auth.kind !== 'signed_in') return;
  const account = auth.account;
  const startedIn = accountEpoch();

  // CP-009: a revoke that never reached the server goes first; while it is
  // pending the browser does not send for this account, whatever the server says.
  if (hasPendingRevoke(account)) {
    try {
      await revokeConsent(BROWSER_ERROR_REPORTS);
      setPendingRevoke(account, false);
    } catch {
      setAccountConsent(account, { kind: 'failed' }, startedIn);
      return;
    }
  }

  let records: ConsentRecord[];
  try {
    records = await listConsents();
  } catch {
    // CP-012: a failed read is "no valid consent", never consent.
    setAccountConsent(account, { kind: 'failed' }, startedIn);
    return;
  }
  // CP-010: an answer requested before a newer decision (here or in another
  // tab) or a change of person is discarded and read again.
  if (!setAccountConsent(account, accountConsentFrom(records, Date.now()), startedIn)) {
    const { auth: now } = readConsentSnapshot();
    if (now.kind === 'signed_in') again = true;
  }
}

/**
 * Read the account consent of the signed-in person. Concurrent calls share one
 * run; a call during a run schedules exactly one more, so the last trigger
 * always gets a fresh read.
 */
export function reconcileAccountConsent(): Promise<void> {
  if (running) {
    again = true;
    return running;
  }
  const run = (async () => {
    do {
      again = false;
      await reconcileOnce();
    } while (again);
  })().finally(() => {
    running = null;
  });
  running = run;
  return run;
}

/**
 * Record the signed-in person's decision on their account (banner in the
 * account form, the switch in the privacy settings).
 *
 * - **Revoke:** stops this browser at once and marks the revoke pending before
 *   the request; a failed `DELETE` keeps it pending (sent first on the next
 *   reconcile of this account, also after another person signed in here
 *   meanwhile) — CW-003, CP-009, CP-012.
 * - **Grant:** changes nothing locally until the server confirmed it for the
 *   current text; a failure leaves the state as it was. A pending revoke is
 *   cleared only by a confirmed grant.
 */
export async function decideAccountConsent(granted: boolean): Promise<AccountWriteResult> {
  const { auth } = readConsentSnapshot();
  if (auth.kind !== 'signed_in') return 'failed';
  const account = auth.account;

  if (!granted) {
    setPendingRevoke(account, true);
    recordAccountDecision(account, { kind: 'denied' });
    signalAccountChange(true);
    try {
      await revokeConsent(BROWSER_ERROR_REPORTS);
    } catch {
      return 'failed';
    }
    setPendingRevoke(account, false);
    recordAccountDecision(account, { kind: 'denied' });
    return 'confirmed';
  }

  let record: ConsentRecord;
  try {
    // CP-013: the grant names the text version this page showed; the server refuses another.
    record = await grantConsent(BROWSER_ERROR_REPORTS, BROWSER_ERROR_REPORTS_VERSION);
  } catch (error) {
    if (isApiError(error) && error.errorCode === CONSENT_TEXT_OUTDATED) {
      recordAccountDecision(account, { kind: 'outdated' });
      return 'outdated';
    }
    return 'failed';
  }
  const next = accountConsentFrom([record], Date.now());
  if (next.kind !== 'granted') return 'failed';
  setPendingRevoke(account, false);
  if (!recordAccountDecision(account, next)) return 'failed';
  // CP-015: granting the account in this browser confirms this browser — one click, not two
  // questions. A decline of this device stays: lifting it is the device switch's job (CP-007).
  if (readConsentSnapshot().device.browser_error_reports !== false) decideOnDevice(true);
  signalAccountChange(false);
  return 'confirmed';
}

/** Removes what `startAccountSync` installed; `null` while not started. */
let teardown: (() => void) | null = null;

/**
 * Keep the account consent current for the rest of the page view (idempotent):
 * on every change of the signed-in person, on a signal from another tab, when
 * the tab becomes visible (at most once a minute), when the network comes back,
 * and every ten minutes while visible (CP-009…CP-011).
 */
export function startAccountSync(): void {
  if (teardown) return;

  let lastAccount: string | null = null;
  let lastRead = 0;
  const run = () => {
    lastRead = Date.now();
    void reconcileAccountConsent();
  };

  setAccountResyncHandler(run);
  const unsubscribe = subscribeConsent((snapshot) => {
    const current = snapshot.auth.kind === 'signed_in' ? snapshot.auth.account : null;
    if (current === lastAccount) return;
    lastAccount = current;
    if (current !== null) run();
  });

  const onVisible = () => {
    if (document.visibilityState !== 'visible') return;
    if (Date.now() - lastRead < VISIBLE_RECHECK_MIN_MS) return;
    run();
  };
  document.addEventListener('visibilitychange', onVisible);
  window.addEventListener('online', run);
  const interval = window.setInterval(() => {
    if (document.visibilityState === 'visible') run();
  }, RECHECK_INTERVAL_MS);
  teardown = () => {
    unsubscribe();
    setAccountResyncHandler(null);
    document.removeEventListener('visibilitychange', onVisible);
    window.removeEventListener('online', run);
    window.clearInterval(interval);
  };

  const { auth } = readConsentSnapshot();
  if (auth.kind === 'signed_in') {
    lastAccount = auth.account;
    run();
  }
}

/** Test seam: remove every listener and timer and forget any run in flight. */
export function resetConsentSyncForTests(): void {
  teardown?.();
  teardown = null;
  running = null;
  again = false;
}
