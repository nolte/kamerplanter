import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import LoginIcon from '@mui/icons-material/Login';
import { startStepUpReauth } from '@/api/endpoints/auth';
import { getStepUpErrorMessage, isApiError, isStepUpPasswordRequired } from '@/api/errors';
import type { AuthProviderInfo, StepUpAction } from '@/api/types';
import { redirectTo } from '@/utils/browserNavigation';
import { clearStepUpResume, newStepUpClientNonce, saveStepUpResume } from '@/utils/stepUpReauth';

interface StepUpReauthButtonProps {
  /** The act the fresh sign-in confirms; the token is bound to it. */
  stepUpAction: StepUpAction;
  /** Linked providers that can re-authenticate; empty → one button, the backend picks. */
  providers: readonly AuthProviderInfo[];
  /**
   * The step-up surface's id — saved with the return path so the page can reopen
   * the right dialog, and the test-id prefix: `<surface>-reauth` (one provider or
   * none known), `<surface>-reauth-<providerKey>` (several), `<surface>-reauth-error`.
   */
  surface: string;
  disabled?: boolean;
  /** Called right before the request, e.g. to dismiss an earlier callback error. */
  onStart?: () => void;
  /**
   * Starting answered 422 `STEP_UP_REAUTH_UNAVAILABLE` (or an unspecific 422 of
   * an older backend): no linked provider can re-authenticate — the e-mailed code applies.
   */
  onUnavailable: () => void;
  /** Starting answered 422 `STEP_UP_PASSWORD_REQUIRED`: the account confirms with its password. */
  onPasswordRequired: () => void;
}

const PROVIDER_NAMES: Readonly<Record<string, string>> = {
  google: 'Google',
  oidc: 'SSO',
};

function providerLabel(provider: AuthProviderInfo, withEmail: boolean): string {
  const name = PROVIDER_NAMES[provider.provider] ?? provider.provider;
  return withEmail && provider.provider_email ? `${name} (${provider.provider_email})` : name;
}

/**
 * "Sign in again" — the step-up of an account without a local password whose
 * identity provider can prove a fresh sign-in (#1815).
 *
 * Asks the backend for the provider's authorization URL, saves where to come
 * back to (the current path with search and hash) together with the surface and
 * the act, then leaves the app for the provider. The provider returns via the
 * backend to `/auth/step-up/callback`, which stores the one-time token and
 * navigates back here.
 */
export default function StepUpReauthButton({
  stepUpAction,
  providers,
  surface,
  disabled = false,
  onStart,
  onUnavailable,
  onPasswordRequired,
}: StepUpReauthButtonProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const [startingKey, setStartingKey] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleStart = async (providerKey?: string) => {
    onStart?.();
    setStartingKey(providerKey ?? '');
    setError('');
    try {
      const nonce = newStepUpClientNonce();
      const { authorization_url: url } = await startStepUpReauth(stepUpAction, providerKey, nonce);
      saveStepUpResume({
        surface,
        action: stepUpAction,
        returnPath: `${location.pathname}${location.search}${location.hash}`,
        nonce,
      });
      redirectTo(url);
    } catch (err) {
      clearStepUpResume();
      setStartingKey(null);
      if (isStepUpPasswordRequired(err)) {
        onPasswordRequired();
      } else if (isApiError(err) && err.statusCode === 422) {
        onUnavailable();
      } else {
        setError(getStepUpErrorMessage(err, t));
      }
    }
  };

  const several = providers.length > 1;
  const buttons =
    providers.length === 0
      ? [{ key: undefined, label: t('pages.auth.stepUpReauthButton'), testId: `${surface}-reauth` }]
      : providers.map((p) => ({
          key: p.key,
          label: t('pages.auth.stepUpReauthButtonWith', { provider: providerLabel(p, several) }),
          testId: several ? `${surface}-reauth-${p.key}` : `${surface}-reauth`,
        }));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 2 }}>
      <Typography variant="body2" color="text.secondary">
        {t('pages.auth.stepUpReauthHint')}
      </Typography>
      {buttons.map((b) => (
        <Button
          key={b.key ?? 'default'}
          variant="outlined"
          startIcon={<LoginIcon />}
          onClick={() => handleStart(b.key)}
          disabled={disabled || startingKey !== null}
          loading={startingKey === (b.key ?? '')}
          aria-busy={startingKey === (b.key ?? '')}
          sx={{ alignSelf: { xs: 'stretch', sm: 'flex-start' }, minHeight: 44 }}
          data-testid={b.testId}
        >
          {b.label}
        </Button>
      ))}
      {error && (
        <Alert severity="error" data-testid={`${surface}-reauth-error`}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
