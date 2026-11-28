import { describe, it, expect } from 'vitest';
import {
  ACCOUNT_GRANT_MAX_AGE_MS,
  BROWSER_ERROR_REPORTS_VERSION,
  browserReportsPermitted,
  consentPrompt,
  type AccountConsent,
  type AuthStatus,
  type ConsentPrompt,
  type ConsentSnapshot,
} from '@/observability/consent';

/**
 * UI-NFR-013 v1.3 §5.4 — the case table, row by row, against the one pair of
 * functions the error tracker, the banner and the settings all call. A row
 * changed in the spec has to change here, and the reverse.
 */
const NOW = 1_800_000_000_000;

type Device = 'granted' | 'denied' | 'undecided';
type Account = 'granted' | 'denied' | 'none' | 'unread' | 'failed' | 'stale';

function snap(
  device: Device,
  auth: 'unknown' | 'signed_out' | 'signed_in',
  account: Account | '-',
  pendingRevoke = false,
): ConsentSnapshot {
  const authStatus: AuthStatus =
    auth === 'signed_in' ? { kind: 'signed_in', account: 'user-a' } : { kind: auth };
  const accountState: AccountConsent =
    account === 'granted'
      ? { kind: 'granted', confirmedAt: NOW - 1000 }
      : account === 'stale'
        ? { kind: 'granted', confirmedAt: NOW - ACCOUNT_GRANT_MAX_AGE_MS - 1 }
        : account === 'denied'
          ? { kind: 'denied' }
          : account === 'none'
            ? { kind: 'undecided' }
            : account === 'failed'
              ? { kind: 'failed' }
              : { kind: 'unknown' };
  return {
    device: {
      necessary: true,
      browser_error_reports: device === 'granted' ? true : device === 'denied' ? false : null,
      timestamp: null,
      version: BROWSER_ERROR_REPORTS_VERSION,
    },
    auth: authStatus,
    account: accountState,
    pendingRevoke,
  };
}

// [device, sign-in, account, pending revoke, sends?, banner]
const TABLE: [
  Device,
  'unknown' | 'signed_out' | 'signed_in',
  Account | '-',
  boolean,
  boolean,
  ConsentPrompt,
][] = [
  // CP-008: nothing before the auth bootstrap — not even with a device grant.
  ['granted', 'unknown', '-', false, false, null],
  ['denied', 'unknown', '-', false, false, null],
  ['undecided', 'unknown', '-', false, false, null],
  // Signed out: the device decides.
  ['granted', 'signed_out', '-', false, true, null],
  ['denied', 'signed_out', '-', false, false, null],
  ['undecided', 'signed_out', '-', false, false, 'device'],
  // Signed in with a device grant: the device grant is never the account's (CP-003).
  ['granted', 'signed_in', 'granted', false, true, null],
  ['granted', 'signed_in', 'denied', false, false, null],
  ['granted', 'signed_in', 'none', false, false, 'account'],
  // Signed in with a device decline: it holds against an account grant (CP-007), and is not asked again.
  ['denied', 'signed_in', 'granted', false, false, null],
  ['denied', 'signed_in', 'denied', false, false, null],
  ['denied', 'signed_in', 'none', false, false, null],
  // Signed in, device undecided: the account consent counts in every browser without a decline.
  ['undecided', 'signed_in', 'granted', false, true, null],
  ['undecided', 'signed_in', 'denied', false, false, null],
  ['undecided', 'signed_in', 'none', false, false, 'account'],
  // Not read yet / read failed: no report, no question (CP-012).
  ['granted', 'signed_in', 'unread', false, false, null],
  ['undecided', 'signed_in', 'unread', false, false, null],
  ['granted', 'signed_in', 'failed', false, false, null],
  ['undecided', 'signed_in', 'failed', false, false, null],
  // A confirmation older than 30 minutes no longer counts (CP-006, CP-011).
  ['undecided', 'signed_in', 'stale', false, false, null],
  // A pending revoke wins over everything the server still says (CP-009).
  ['undecided', 'signed_in', 'granted', true, false, null],
  ['granted', 'signed_in', 'none', true, false, null],
];

describe('UI-NFR-013 §5.4 — does this browser send reports?', () => {
  it.each(TABLE)(
    'device %s, %s, account %s, pending revoke %s → sends %s, banner %s',
    (device, auth, account, pending, sends, banner) => {
      const s = snap(device, auth, account, pending);
      expect(browserReportsPermitted(s, NOW)).toBe(sends);
      expect(consentPrompt(s)).toBe(banner);
    },
  );

  it('covers every combination of device × sign-in × account the table names', () => {
    const covered = new Set(TABLE.map(([d, a, acc]) => `${d}|${a}|${acc}`));
    for (const device of ['granted', 'denied', 'undecided'] as const) {
      expect(covered.has(`${device}|unknown|-`)).toBe(true);
      expect(covered.has(`${device}|signed_out|-`)).toBe(true);
      for (const account of ['granted', 'denied', 'none'] as const) {
        expect(covered.has(`${device}|signed_in|${account}`)).toBe(true);
      }
    }
  });
});
