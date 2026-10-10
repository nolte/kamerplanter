import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import CircularProgress from '@mui/material/CircularProgress';
import { useSnackbar } from 'notistack';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { registerLocal, clearError, REGISTRATION_NOT_ALLOWED } from '@/store/slices/authSlice';
import { useRegistrationMode } from '@/hooks/useRegistrationMode';
import Form from '@/components/form/Form';

export default function RegisterPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const { isLoading, error } = useAppSelector((s) => s.auth);
  // #2132 — which registration the instance offers. Only a hint: the backend
  // enforces the mode whatever this page shows.
  const registration = useRegistrationMode();

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  // The token of an e-mail invitation, prefilled from `/register?invitation=…`.
  const [invitationToken, setInvitationToken] = useState(() => params.get('invitation') ?? '');

  // #2162 review W1 — the token is read into the form once; it does not stay in the address bar
  // (history, screenshots, a shared screen). The form state keeps it.
  useEffect(() => {
    if (!params.has('invitation')) return;
    const rest = new URLSearchParams(params);
    rest.delete('invitation');
    const search = rest.toString();
    navigate({ pathname: location.pathname, search: search ? `?${search}` : '' }, { replace: true });
  }, [params, navigate, location.pathname]);
  const [localError, setLocalError] = useState('');
  // A refusal of the registration mode is shown in the user's language rather
  // than as the backend's English sentence.
  const [refused, setRefused] = useState(false);

  const inviteOnly = registration.mode === 'invite_only';
  const showInvitationField = inviteOnly || registration.domainRestricted || invitationToken !== '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(clearError());
    setLocalError('');
    setRefused(false);

    if (password !== confirmPassword) {
      setLocalError(t('pages.auth.passwordMismatch'));
      return;
    }

    const token = invitationToken.trim();
    try {
      await dispatch(
        registerLocal({
          email,
          password,
          display_name: displayName,
          ...(token ? { invitation_token: token } : {}),
        }),
      ).unwrap();
      enqueueSnackbar(t('pages.auth.registrationSuccess'), { variant: 'success' });
      navigate('/login');
    } catch (rejection) {
      // Every other refusal is shown from the store's `error`, as before.
      if ((rejection as { code?: string } | null)?.code === REGISTRATION_NOT_ALLOWED) {
        setRefused(true);
      }
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', px: 2 }}>
      <Card sx={{ width: '100%', maxWidth: 420 }} data-testid="register-page">
        <CardContent sx={{ p: { xs: 2, sm: 4 } }}>
          <Typography variant="h5" gutterBottom align="center">
            {t('pages.auth.register')}
          </Typography>

          {registration.mode === 'closed' && (
            <>
              <Alert severity="info" sx={{ mb: 2 }} data-testid="registration-closed">
                {t('pages.auth.registrationClosed')}
              </Alert>
              <Link component={RouterLink} to="/login" variant="body2" data-testid="register-login-link">
                {t('pages.auth.loginLink')}
              </Link>
            </>
          )}

          {/* The form shows while the mode is still loading: an instance that is
              open (the default) never sees it flash away, and the backend decides
              whatever this page shows. */}
          {registration.mode !== 'closed' && (
            <>
              {inviteOnly && (
                <Alert severity="info" sx={{ mb: 2 }} data-testid="registration-invite-only">
                  {t('pages.auth.registrationInviteOnly')}
                </Alert>
              )}
              {!inviteOnly && registration.domainRestricted && (
                <Alert severity="info" sx={{ mb: 2 }} data-testid="registration-domain-restricted">
                  {t('pages.auth.registrationDomainRestricted')}
                </Alert>
              )}

              {refused ? (
                <Alert severity="error" sx={{ mb: 2 }} data-testid="registration-refused">
                  {t('pages.auth.registrationRefused')}
                </Alert>
              ) : (
                (error || localError) && (
                  <Alert severity="error" sx={{ mb: 2 }}>{localError || error}</Alert>
                )
              )}

              <Form onSubmit={handleSubmit}>
                <TextField
                  label={t('pages.auth.displayName')}
                  fullWidth
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  sx={{ mb: 2 }}
                  autoComplete="name"
                  data-testid="form-field-display-name"
                />
                <TextField
                  label={t('pages.auth.email')}
                  type="email"
                  fullWidth
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  sx={{ mb: 2 }}
                  autoComplete="email"
                  data-testid="form-field-email"
                />
                <TextField
                  label={t('pages.auth.password')}
                  type="password"
                  fullWidth
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  sx={{ mb: 2 }}
                  helperText={t('pages.auth.passwordHelp')}
                  autoComplete="new-password"
                  data-testid="form-field-password"
                />
                <TextField
                  label={t('pages.auth.confirmPassword')}
                  type="password"
                  fullWidth
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  sx={{ mb: 2 }}
                  autoComplete="new-password"
                  data-testid="form-field-confirm-password"
                />
                {showInvitationField && (
                  <TextField
                    label={t('pages.auth.invitationCode')}
                    fullWidth
                    required={inviteOnly}
                    value={invitationToken}
                    onChange={(e) => setInvitationToken(e.target.value)}
                    sx={{ mb: 2 }}
                    helperText={t('pages.auth.invitationCodeHelp')}
                    autoComplete="off"
                    slotProps={{ htmlInput: { maxLength: 512, spellCheck: false, autoCapitalize: 'none' } }}
                    data-testid="form-field-invitation-token"
                  />
                )}
                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  disabled={
                    isLoading ||
                    !displayName ||
                    !email ||
                    !password ||
                    !confirmPassword ||
                    (inviteOnly && !invitationToken.trim())
                  }
                  sx={{ mb: 2, minHeight: 44 }}
                  data-testid="register-submit"
                >
                  {isLoading ? <CircularProgress size={24} /> : t('pages.auth.registerButton')}
                </Button>
              </Form>

              <Link component={RouterLink} to="/login" variant="body2" data-testid="register-login-link">
                {t('pages.auth.loginLink')}
              </Link>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
