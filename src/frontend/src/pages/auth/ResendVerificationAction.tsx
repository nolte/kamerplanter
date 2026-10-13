import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { isRateLimited } from '@/api/client';
import { isApiError } from '@/api/errors';
import { resendVerification } from '@/api/endpoints/auth';

type ResendState = 'idle' | 'sending' | 'sent' | 'rateLimited' | 'failed';

interface ResendVerificationActionProps {
  /** The address the new link is asked for — the one the sign-in was refused for. */
  email: string;
}

function isTooManyRequests(error: unknown): boolean {
  return isRateLimited(error) || (isApiError(error) && error.statusCode === 429);
}

/**
 * "Send a new verification email" for an address whose sign-in was refused as
 * unverified (REQ-023, #2037).
 *
 * The answer it shows on success is the backend's own promise — a link is on
 * its way *if* the address still needs one — never "sent": the endpoint answers
 * every address alike and so does this component. The outcome is announced in a
 * polite live region, so a screen-reader user hears it without losing focus.
 */
export default function ResendVerificationAction({ email }: ResendVerificationActionProps) {
  const { t } = useTranslation();
  const [state, setState] = useState<ResendState>('idle');

  const handleResend = async () => {
    setState('sending');
    try {
      await resendVerification(email);
      setState('sent');
    } catch (error) {
      setState(isTooManyRequests(error) ? 'rateLimited' : 'failed');
    }
  };

  const message =
    state === 'sent'
      ? t('pages.auth.verificationResent')
      : state === 'rateLimited'
        ? t('pages.auth.verificationResendRateLimited')
        : state === 'failed'
          ? t('pages.auth.verificationResendFailed')
          : '';

  return (
    <Box sx={{ mt: 1 }}>
      <Button
        variant="outlined"
        size="small"
        onClick={handleResend}
        disabled={state === 'sending' || state === 'sent'}
        startIcon={state === 'sending' ? <CircularProgress size={16} color="inherit" aria-hidden /> : undefined}
        data-testid="resend-verification-button"
      >
        {t('pages.auth.resendVerification')}
      </Button>
      <Typography
        variant="body2"
        role="status"
        aria-live="polite"
        sx={{ mt: message ? 1 : 0 }}
        data-testid="resend-verification-status"
      >
        {message}
      </Typography>
    </Box>
  );
}
