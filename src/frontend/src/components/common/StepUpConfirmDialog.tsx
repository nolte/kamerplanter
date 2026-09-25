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
import { getStepUpErrorMessage, isApiError } from '@/api/errors';

/** What the requester typed to prove the irreversible action is intended. */
export interface StepUpConfirmation {
  /** The echo, trimmed — a slug or an e-mail address. */
  echo: string;
  /** The requester's current password; absent for a known federated-only account. */
  password?: string;
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
  /** `<prefix>-dialog`, `<prefix>-echo`, `<prefix>-password`, `<prefix>-error`, `<prefix>-cancel`, `<prefix>-confirm`. */
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
 * On a rejection the dialog stays open, shows the error inside itself and
 * clears the password so a wrong one is not resent by accident.
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
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  // Tri-state: `null` = unknown (loading or failed) → fail closed.
  const [hasLocalPassword, setHasLocalPassword] = useState<boolean | null>(null);
  const [serverAskedForPassword, setServerAskedForPassword] = useState(false);
  const requiresPassword = hasLocalPassword !== false || serverAskedForPassword;

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    listProviders()
      .then((list) => {
        if (cancelled) return;
        // Only a non-empty list without `local` is positive proof of a
        // federated-only account; an empty one stays unknown (fail closed).
        setHasLocalPassword(list.length === 0 ? null : list.some((p) => p.provider === 'local'));
      })
      .catch(() => {
        if (!cancelled) setHasLocalPassword(null);
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
  const canConfirm = echoMatches && (!requiresPassword || password.length > 0) && !pending;

  const reset = () => {
    setEcho('');
    setPassword('');
    setError('');
  };

  const handleCancel = () => {
    if (pending) return;
    reset();
    onCancel();
  };

  const handleConfirm = async () => {
    if (!canConfirm) return;
    setPending(true);
    setError('');
    try {
      await onConfirm(requiresPassword ? { echo: trimmedEcho, password } : { echo: trimmedEcho });
      reset();
    } catch (err) {
      // Stay open so the requester can correct the echo or the password.
      setError(getStepUpErrorMessage(err, t));
      setPassword('');
      if (isApiError(err) && err.statusCode === 401) setServerAskedForPassword(true);
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
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid={id('error')}>
            {error}
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
