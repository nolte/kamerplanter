import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { normalizeStepUpReauthCallbackError } from '@/api/errors';
import type { StepUpAction } from '@/api/types';
import {
  clearStepUpResume,
  isStepUpAction,
  readStepUpResume,
  storePendingStepUpToken,
  storeStepUpReauthError,
} from '@/utils/stepUpReauth';

/** `hasResume`: a valid resume context was saved; without one a stale or forged record is dropped. */
type CallbackOutcome =
  | {
      kind: 'token';
      token: string;
      action: StepUpAction;
      target: string | null;
      returnPath: string;
      hasResume: boolean;
    }
  | { kind: 'error'; error: string; action: StepUpAction; returnPath: string; hasResume: boolean }
  | { kind: 'discard'; returnPath: string; hasResume: boolean };

/**
 * What the backend's redirect says, and where to go back to.
 *
 * Success carries `#step_up_token=…&action=…&client_nonce=…` in the **fragment**
 * (never sent to a server, never in a `Referer`); failure carries
 * `?error=…&action=…&client_nonce=…`. A result is kept only when this tab started
 * a fresh sign-in for the same act less than ten minutes ago and the client nonce
 * is the one it sent (SEC-005); anything else is discarded. The return path comes from
 * the resume context saved before the redirect and is validated there as an
 * app-relative path (open-redirect guard); without one the app root is used.
 */
function resolveOutcome(hash: string, search: string): CallbackOutcome {
  const fragment = new URLSearchParams(hash.replace(/^#/, ''));
  const query = new URLSearchParams(search);
  const resume = readStepUpResume();
  const returnPath = resume?.returnPath ?? '/';
  const hasResume = resume !== null;

  const token = fragment.get('step_up_token');
  if (token !== null) {
    const tokenAction = fragment.get('action');
    // SEC-005: kept only for a sign-in this tab started for this very act, less
    // than ten minutes ago. A crafted link lands in a tab without such a record
    // and is dropped silently — nothing stored, nothing shown.
    if (
      token &&
      !query.has('error') &&
      isStepUpAction(tokenAction) &&
      resume?.action === tokenAction &&
      fragment.get('client_nonce') === resume.nonce
    ) {
      // #1884 — the token is bound to the target this tab started the sign-in for.
      return {
        kind: 'token',
        token,
        action: tokenAction,
        target: resume.target,
        returnPath,
        hasResume,
      };
    }
    return { kind: 'discard', returnPath, hasResume };
  }
  const queryAction = query.get('action');
  const action = isStepUpAction(queryAction) ? queryAction : (resume?.action ?? null);
  // An error only concerns the act this tab started, with this tab's nonce.
  if (!resume || action !== resume.action || query.get('client_nonce') !== resume.nonce) {
    return { kind: 'discard', returnPath, hasResume };
  }
  return {
    kind: 'error',
    error: normalizeStepUpReauthCallbackError(query.get('error')),
    action,
    returnPath,
    hasResume,
  };
}

/**
 * Landing page of the fresh sign-in that confirms a step-up (#1815):
 * `/auth/step-up/callback`.
 *
 * Signs nobody in — the session is untouched. It removes the fragment (the
 * one-time token) and the query from the address bar at once, keeps the token
 * in sessionStorage for five minutes (`{token, action, target, expiresAt}`), or on
 * `?error=` leaves an error marker, and navigates back to the page that started
 * the sign-in. That page reopens its step-up dialog (`useStepUpResume`), which
 * sends the token or shows the translated error.
 */
export default function StepUpCallbackPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  // Parsed once, from the URL this page was opened with.
  const [outcome] = useState(() => resolveOutcome(location.hash, location.search));

  useEffect(() => {
    // The token must not stay in the address bar or the history entry.
    window.history.replaceState(window.history.state, '', window.location.pathname);
    if (outcome.kind === 'token') {
      storePendingStepUpToken(outcome.token, outcome.action, outcome.target);
    } else if (outcome.kind === 'error') {
      storeStepUpReauthError(outcome.error, outcome.action);
    }
    if (!outcome.hasResume) clearStepUpResume();
    navigate(outcome.returnPath, { replace: true });
  }, [outcome, navigate]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 2,
        minHeight: '60vh',
        px: 2,
      }}
      data-testid="step-up-callback-page"
    >
      <CircularProgress aria-hidden />
      <Typography role="status" color="text.secondary">
        {t('pages.auth.stepUpReauthReturning')}
      </Typography>
    </Box>
  );
}
