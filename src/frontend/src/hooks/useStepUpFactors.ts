import { useCallback, useMemo, useState } from 'react';
import type { AuthProviderInfo } from '@/api/types';
import { isApiError, isStepUpCodeRequired, isStepUpReauthRequired } from '@/api/errors';
import { hasLocalPasswordFromProviders } from '@/utils/stepUp';
import { reauthCapableProviders } from '@/utils/stepUpReauth';

export interface StepUpFactors {
  /** `true`/`false` when the provider list proves it, `null` when unknown. */
  hasLocalPassword: boolean | null;
  /** Show (and ask for) the current password. */
  showPassword: boolean;
  /** Show the e-mailed one-time code (and the button that sends it). */
  showCode: boolean;
  /** Show the "sign in again" button — a fresh sign-in at the identity provider (#1815). */
  showReauth: boolean;
  /**
   * The linked providers a fresh sign-in can be started with, one button each.
   * Empty when the list is unknown — then one button without a provider, and the
   * backend picks the first capable link.
   */
  reauthProviders: readonly AuthProviderInfo[];
  /**
   * Whether what was supplied is enough to submit the step-up. `reauthed` is
   * `true` while a token of a fresh sign-in for the act is pending — that alone
   * is the factor.
   */
  isSatisfied: (password: string, code: string, reauthed?: boolean) => boolean;
  /** Feed every rejected step-up here; a 401 adjusts which factor is shown. */
  noteRejection: (error: unknown) => void;
  /** The server said the account has a password (sending a code answered 422). */
  noteAccountHasPassword: () => void;
  /** The server said the account confirms with a fresh sign-in (sending a code answered 422 `STEP_UP_REAUTH_REQUIRED`). */
  noteReauthRequired: () => void;
  /** Starting the fresh sign-in answered 422: no linked provider can — the e-mailed code applies. */
  noteReauthUnavailable: () => void;
  /** Forget what the server said, e.g. after a password was set successfully. */
  reset: () => void;
}

type ServerVerdict = 'password' | 'code' | 'reauth' | null;

/**
 * Which step-up factor a surface asks for: the current password, a fresh
 * sign-in at the identity provider, the e-mailed one-time code (#1815), or —
 * while unsure — the password beside one of the others.
 *
 * The one implementation of the **fail-closed** rule shared by
 * `StepUpConfirmDialog` and the password form (#1842):
 *
 * - The password field is shown unless a non-empty provider list positively
 *   lacks `local` ({@link hasLocalPasswordFromProviders}). Unknown — loading,
 *   failed, empty — shows it, or a local account meets a 401 it has no field to
 *   answer (the #394 dead end).
 * - After a 401 the password field stays, whatever the list said: the backend
 *   decides on the stored hash, not on the list.
 * - A federated-only list offers the **fresh sign-in** when any linked provider
 *   can prove one (not GitHub, not Apple); only a list of GitHub/Apple links
 *   offers the **e-mailed code**.
 * - The server's word beats the list: 401 `STEP_UP_REAUTH_REQUIRED` (or 422 of
 *   the same code when a code was requested) means the fresh sign-in only;
 *   401 `STEP_UP_CODE_REQUIRED` — or 422 when starting the fresh sign-in, i.e.
 *   no provider can — means the code only; 422 when sending a code means the
 *   password only.
 */
export function useStepUpFactors(providers: readonly AuthProviderInfo[] | null): StepUpFactors {
  const [serverVerdict, setServerVerdict] = useState<ServerVerdict>(null);
  const [rejectedWith401, setRejectedWith401] = useState(false);

  const hasLocalPassword = hasLocalPasswordFromProviders(providers);
  const reauthProviders = useMemo(() => reauthCapableProviders(providers), [providers]);
  const hasReauthProvider = reauthProviders.length > 0;

  const noteRejection = useCallback((error: unknown) => {
    if (isStepUpReauthRequired(error)) {
      setServerVerdict('reauth');
    } else if (isStepUpCodeRequired(error)) {
      setServerVerdict('code');
    } else if (isApiError(error) && error.statusCode === 401) {
      setRejectedWith401(true);
    }
  }, []);

  const noteAccountHasPassword = useCallback(() => setServerVerdict('password'), []);
  const noteReauthRequired = useCallback(() => setServerVerdict('reauth'), []);
  const noteReauthUnavailable = useCallback(() => setServerVerdict('code'), []);

  const reset = useCallback(() => {
    setServerVerdict(null);
    setRejectedWith401(false);
  }, []);

  return useMemo(() => {
    let showPassword: boolean;
    let showCode: boolean;
    let showReauth: boolean;
    if (serverVerdict === 'code') {
      showPassword = false;
      showCode = true;
      showReauth = false;
    } else if (serverVerdict === 'reauth') {
      showPassword = false;
      showCode = false;
      showReauth = true;
    } else if (serverVerdict === 'password') {
      showPassword = true;
      showCode = false;
      showReauth = false;
    } else {
      const federatedOnly = hasLocalPassword === false;
      showPassword = !federatedOnly || rejectedWith401;
      showReauth = federatedOnly && hasReauthProvider;
      showCode = federatedOnly && !hasReauthProvider;
    }
    const isSatisfied = (password: string, code: string, reauthed = false) => {
      if (reauthed) return true;
      if (!showPassword && !showCode) return !showReauth;
      return (showPassword && password.length > 0) || (showCode && code.length > 0);
    };
    return {
      hasLocalPassword,
      showPassword,
      showCode,
      showReauth,
      reauthProviders,
      isSatisfied,
      noteRejection,
      noteAccountHasPassword,
      noteReauthRequired,
      noteReauthUnavailable,
      reset,
    };
  }, [
    hasLocalPassword,
    hasReauthProvider,
    reauthProviders,
    serverVerdict,
    rejectedWith401,
    noteRejection,
    noteAccountHasPassword,
    noteReauthRequired,
    noteReauthUnavailable,
    reset,
  ]);
}
