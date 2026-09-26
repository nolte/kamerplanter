import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';
import { requestStepUpCode } from '@/api/endpoints/auth';
import type { StepUpAction } from '@/api/types';
import { getStepUpErrorMessage, isApiError, isStepUpReauthRequired } from '@/api/errors';

interface StepUpCodeFieldProps {
  value: string;
  onChange: (code: string) => void;
  /** The act the code is requested for; the code confirms this act only (review SEC-003). */
  stepUpAction: StepUpAction;
  /** What the act acts on (#1884); the code confirms this target only. */
  stepUpTarget?: string;
  disabled?: boolean;
  /** `<prefix>-code`, `<prefix>-send-code`, `<prefix>-code-sent`, `<prefix>-send-code-error`. */
  testIdPrefix: string;
  /** Called when sending answered 422 — the account has a password after all. */
  onAccountHasPassword?: () => void;
  /**
   * Called when sending answered 422 `STEP_UP_REAUTH_REQUIRED` — the account's
   * identity provider can prove a fresh sign-in, which it must use instead (#1815).
   */
  onReauthRequired?: () => void;
  /** Enter pressed in the code field. */
  onEnter?: () => void;
}

/**
 * The e-mailed one-time code of a step-up (#1815), for an account that has no
 * local password to confirm with.
 *
 * A button sends the code (`POST /users/me/step-up-code`) and, once sent, says
 * how long it stays valid and turns into "send again". A throttled request
 * (429 `STEP_UP_LOCKED`) reads as the translated lockout.
 */
export default function StepUpCodeField({
  value,
  onChange,
  stepUpAction,
  stepUpTarget,
  disabled = false,
  testIdPrefix,
  onAccountHasPassword,
  onReauthRequired,
  onEnter,
}: StepUpCodeFieldProps) {
  const { t } = useTranslation();
  const [sending, setSending] = useState(false);
  const [sentMinutes, setSentMinutes] = useState<number | null>(null);
  const [sendError, setSendError] = useState('');

  const handleSend = async () => {
    setSending(true);
    setSendError('');
    try {
      const sent = await requestStepUpCode(stepUpAction, stepUpTarget);
      setSentMinutes(Math.max(1, Math.ceil(sent.expires_in / 60)));
    } catch (err) {
      setSentMinutes(null);
      if (isStepUpReauthRequired(err)) {
        setSendError(getStepUpErrorMessage(err, t));
        onReauthRequired?.();
      } else if (isApiError(err) && err.statusCode === 422) {
        setSendError(t('pages.auth.stepUpCodeNotNeeded'));
        onAccountHasPassword?.();
      } else {
        setSendError(getStepUpErrorMessage(err, t));
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 2 }}>
      <Button
        variant="outlined"
        startIcon={<MarkEmailReadIcon />}
        onClick={handleSend}
        disabled={disabled}
        loading={sending}
        aria-busy={sending}
        sx={{ alignSelf: { xs: 'stretch', sm: 'flex-start' } }}
        data-testid={`${testIdPrefix}-send-code`}
      >
        {sentMinutes === null ? t('pages.auth.stepUpSendCode') : t('pages.auth.stepUpResendCode')}
      </Button>
      {sentMinutes !== null && (
        <Alert severity="info" role="status" data-testid={`${testIdPrefix}-code-sent`}>
          {t('pages.auth.stepUpCodeSent', { minutes: sentMinutes })}
        </Alert>
      )}
      {sendError && (
        <Alert severity="error" data-testid={`${testIdPrefix}-send-code-error`}>
          {sendError}
        </Alert>
      )}
      <TextField
        label={t('pages.auth.stepUpCodeLabel')}
        helperText={t('pages.auth.stepUpCodeHelper')}
        value={value}
        onChange={(e) => onChange(e.target.value.replace(/\s+/g, ''))}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onEnter?.();
        }}
        autoComplete="one-time-code"
        fullWidth
        required
        disabled={disabled}
        slotProps={{
          htmlInput: { inputMode: 'numeric', spellCheck: false, autoCapitalize: 'none' },
        }}
        data-testid={`${testIdPrefix}-code`}
      />
    </Box>
  );
}
