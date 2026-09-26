import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { listProviders } from '@/api/endpoints/auth';
import { getStepUpErrorMessage, getStepUpReauthCallbackErrorMessage, isStepUpRejection } from '@/api/errors';
import type { AuthProviderInfo, StepUpAction } from '@/api/types';
import { useStepUpFactors } from '@/hooks/useStepUpFactors';
import { usePendingStepUpReauth } from '@/hooks/useStepUpReauth';
import StepUpCodeField from './StepUpCodeField';
import StepUpReauthButton from './StepUpReauthButton';

/** What the requester typed to prove the irreversible action is intended. */
export interface StepUpConfirmation {
  /** The echo, trimmed — a slug or an e-mail address. */
  echo: string;
  /** The requester's current password; absent for a known federated-only account. */
  password?: string;
  /** The e-mailed one-time code (#1815); present only when the dialog asked for it. */
  code?: string;
  /** The one-time token of a fresh sign-in at the identity provider (#1815); taken from sessionStorage. */
  token?: string;
}

type StepUpTestIdSlot = 'dialog' | 'echo' | 'password' | 'error' | 'cancel' | 'confirm';

interface StepUpConfirmDialogProps {
  open: boolean;
  title: string;
  description: ReactNode;
  echoLabel: string;
  echoHelper: string;
  /** The value the echo must match before the confirm button enables. */
  expectedEcho: string;
  /**
   * `exact` for slugs, `caseInsensitive` for e-mail addresses — the backend
   * compares the same way (`echo_matches` in `step_up_service.py`).
   */
  echoMatch?: 'exact' | 'caseInsensitive';
  echoInputType?: 'text' | 'email';
  /** Defaults to the generic "your current password" wording. */
  passwordLabel?: string;
  /** Defaults to the generic helper; override when the password is not the obvious one (admin acting on another account). */
  passwordHelper?: string;
  /** Shown when Enter is pressed on an empty password field instead of silently doing nothing. */
  passwordRequiredMessage?: string;
  confirmLabel: string;
  /** The act this dialog confirms; an e-mailed code is requested for this act only (review SEC-003). */
  stepUpAction: StepUpAction;
  /**
   * `<prefix>-dialog`, `<prefix>-echo`, `<prefix>-password`, `<prefix>-error`, `<prefix>-cancel`,
   * `<prefix>-confirm`, for the e-mailed code `<prefix>-code`, `<prefix>-send-code`, and for the
   * fresh sign-in `<prefix>-reauth` (or `<prefix>-reauth-<providerKey>`) and `<prefix>-reauth-done`.
   * The prefix is also the surface id saved before the redirect to the identity provider — the
   * page that owns the dialog reopens it via `useStepUpResume(<prefix>)`.
   */
  testIdPrefix: string;
  /** Per-slot overrides for surfaces whose test ids predate this component. */
  testIds?: Partial<Record<StepUpTestIdSlot, string>>;
  /** Runs the action with the step-up; a rejection is shown inside the dialog. */
  onConfirm: (confirmation: StepUpConfirmation) => Promise<void>;
  onCancel: () => void;
}

/**
 * Confirms an irreversible action with a step-up (#1791, #1813, #1814, #1816).
 *
 * The backend refuses the action unless the body echoes a value naming the
 * target — a tenant slug, an account's e-mail — (422) and, for a requester with
 * a local password, carries the current password (401). Too many failed
 * confirmations answer 429 `STEP_UP_LOCKED`, shown as a translated lockout with
 * its minutes.
 *
 * The password field **fails closed**: it is shown unless the provider list
 * positively says the requester is federated-only — a failed or pending load
 * must not hide it, or a local account would meet a 401 it has no field to
 * answer (the #394 dead end). An **empty** list counts as unknown too: seeded
 * accounts carry a password hash without a `local` provider row (#1791 review
 * SEC-003). And once the server answered 401, the field stays, whatever the
 * list said — the backend decides on the stored hash, not on the list. A
 * password sent for a federated account is ignored by the backend.
 *
 * An account without a local password confirms with a one-time code sent by
 * e-mail instead (#1815): the code field and its "send" button appear when the
 * provider list positively says federated-only, or when the server answered
 * 401 `STEP_UP_CODE_REQUIRED`. The rule itself lives in `useStepUpFactors`,
 * shared with the password form.
 *
 * An account whose identity provider can prove a fresh sign-in (Google, a
 * generic OIDC provider — not GitHub or Apple) confirms by **signing in again**
 * there (#1815): the "sign in again" button leaves the app for the provider and
 * `/auth/step-up/callback` brings a one-time token back into sessionStorage.
 * While a token for this dialog's act is pending, the dialog says "signed in
 * again — confirm now" and sends it as `token`; it is taken out of storage when
 * sent successfully or refused as a step-up (401/429) — another refusal, e.g. a
 * mistyped echo (422), keeps it for the next try. A callback error (failed, stale,
 * cancelled) is shown when the dialog opens.
 *
 * On a rejection the dialog stays open, shows the error inside itself and
 * clears the password and the code so a wrong one is not resent by accident.
 */
export default function StepUpConfirmDialog({
  open,
  title,
  description,
  echoLabel,
  echoHelper,
  expectedEcho,
  echoMatch = 'exact',
  echoInputType = 'text',
  passwordLabel,
  passwordHelper,
  passwordRequiredMessage,
  confirmLabel,
  stepUpAction,
  testIdPrefix,
  testIds,
  onConfirm,
  onCancel,
}: StepUpConfirmDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [echo, setEcho] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  // `null` = unknown (loading or failed) → fail closed.
  const [providers, setProviders] = useState<AuthProviderInfo[] | null>(null);
  const factors = useStepUpFactors(providers);
  const reauth = usePendingStepUpReauth(stepUpAction, open);
  const reauthed = reauth.hasToken;
  const requiresPassword = factors.showPassword && !reauthed;
  const requiresCode = factors.showCode && !reauthed;
  const offersReauth = factors.showReauth && !reauthed;
  const callbackErrorMessage = reauth.callbackError
    ? getStepUpReauthCallbackErrorMessage(reauth.callbackError, t)
    : '';
  const shownError = error || callbackErrorMessage;

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    listProviders()
      .then((list) => {
        if (!cancelled) setProviders(list);
      })
      .catch(() => {
        if (!cancelled) setProviders(null);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const id = (slot: StepUpTestIdSlot) => testIds?.[slot] ?? `${testIdPrefix}-${slot}`;
  const titleId = `${testIdPrefix}-dialog-title`;
  const descriptionId = `${testIdPrefix}-dialog-description`;

  const trimmedEcho = echo.trim();
  const expected = expectedEcho.trim();
  const echoMatches =
    expected.length > 0 &&
    (echoMatch === 'caseInsensitive'
      ? trimmedEcho.toLowerCase() === expected.toLowerCase()
      : trimmedEcho === expected);
  const canConfirm = echoMatches && factors.isSatisfied(password, code, reauthed) && !pending;

  const reset = () => {
    setEcho('');
    setPassword('');
    setCode('');
    setError('');
  };

  const handleCancel = () => {
    if (pending) return;
    reset();
    if (reauth.callbackError) reauth.dismissError();
    onCancel();
  };

  const handleConfirm = async () => {
    if (!canConfirm) return;
    setPending(true);
    setError('');
    if (reauth.callbackError) reauth.dismissError();
    try {
      const confirmation: StepUpConfirmation = { echo: trimmedEcho };
      if (reauthed) {
        // Left in storage until the outcome is known: spent on success or when
        // the step-up itself is refused, kept for a refusal of anything else.
        const token = reauth.peekToken();
        if (token) confirmation.token = token;
      } else {
        if (requiresPassword && (!requiresCode || password.length > 0)) confirmation.password = password;
        if (requiresCode && code.length > 0) confirmation.code = code;
      }
      await onConfirm(confirmation);
      if (confirmation.token) reauth.consumeToken();
      reset();
    } catch (err) {
      if (reauthed && isStepUpRejection(err)) reauth.consumeToken();
      // Stay open so the requester can correct the echo, the password or the code.
      setError(getStepUpErrorMessage(err, t));
      setPassword('');
      setCode('');
      factors.noteRejection(err);
    } finally {
      setPending(false);
    }
  };

  const handlePasswordEnter = () => {
    if (pending) return;
    if (password.length === 0 && passwordRequiredMessage) {
      setError(passwordRequiredMessage);
      return;
    }
    handleConfirm();
  };

  return (
    <Dialog
      open={open}
      onClose={pending ? undefined : handleCancel}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      role="alertdialog"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      data-testid={id('dialog')}
    >
      <DialogTitle id={titleId}>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText id={descriptionId} sx={{ whiteSpace: 'pre-line' }}>
          {description}
        </DialogContentText>
        <TextField
          type={echoInputType}
          label={echoLabel}
          helperText={echoHelper}
          value={echo}
          onChange={(e) => setEcho(e.target.value)}
          autoComplete="off"
          fullWidth
          required
          autoFocus
          disabled={pending}
          error={echo.length > 0 && !echoMatches}
          sx={{ mt: 2 }}
          slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
          data-testid={id('echo')}
        />
        {requiresPassword && (
          <TextField
            type="password"
            label={passwordLabel ?? t('pages.auth.stepUpPasswordLabel')}
            helperText={passwordHelper ?? t('pages.auth.stepUpPasswordHelper')}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handlePasswordEnter();
            }}
            autoComplete="current-password"
            fullWidth
            required
            disabled={pending}
            sx={{ mt: 2 }}
            data-testid={id('password')}
          />
        )}
        {reauthed && (
          <Alert severity="success" sx={{ mt: 2 }} data-testid={`${testIdPrefix}-reauth-done`}>
            {t('pages.auth.stepUpReauthDone')}
          </Alert>
        )}
        {offersReauth && (
          <StepUpReauthButton
            stepUpAction={stepUpAction}
            providers={factors.reauthProviders}
            surface={testIdPrefix}
            disabled={pending}
            onStart={() => {
              setError('');
              if (reauth.callbackError) reauth.dismissError();
            }}
            onUnavailable={() => {
              setError(t('pages.auth.stepUpReauthUnavailable'));
              factors.noteReauthUnavailable();
            }}
            onPasswordRequired={() => {
              setError(t('pages.auth.stepUpCodeNotNeeded'));
              factors.noteAccountHasPassword();
            }}
          />
        )}
        {requiresCode && (
          <StepUpCodeField
            value={code}
            onChange={setCode}
            stepUpAction={stepUpAction}
            disabled={pending}
            testIdPrefix={testIdPrefix}
            onAccountHasPassword={factors.noteAccountHasPassword}
            onReauthRequired={() => {
              setError(t('pages.auth.stepUpReauthRequired'));
              factors.noteReauthRequired();
            }}
            onEnter={() => {
              if (!pending) handleConfirm();
            }}
          />
        )}
        {shownError && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid={id('error')}>
            {shownError}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} disabled={pending} data-testid={id('cancel')}>
          {t('common.cancel')}
        </Button>
        <Button
          onClick={handleConfirm}
          color="error"
          variant="contained"
          disabled={!canConfirm}
          loading={pending}
          aria-busy={pending}
          data-testid={id('confirm')}
        >
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
