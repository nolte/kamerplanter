import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import Divider from '@mui/material/Divider';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import Tooltip from '@mui/material/Tooltip';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { loginLocal, clearError } from '@/store/slices/authSlice';
import { getOAuthProviders } from '@/api/endpoints/auth';
import { useAsyncOptions } from '@/hooks/useAsyncOptions';
import Form from '@/components/form/Form';

export default function LoginPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isLoading, error, isAuthenticated } = useAppSelector((s) => s.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  // AP-12 (FE-L3): load the optional OAuth providers with explicit error state
  // instead of a silent `.catch(() => {})`, so a failed load surfaces a hint
  // rather than looking identical to "no providers configured".
  const loadOAuthProviders = useCallback(() => getOAuthProviders(), []);
  const { options: oauthProviders, error: oauthError } = useAsyncOptions(loadOAuthProviders);

  useEffect(() => {
    dispatch(clearError());
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(loginLocal({ email, password, remember_me: rememberMe }));
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom align="center">
            {t('pages.auth.login')}
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Form onSubmit={handleSubmit}>
            <TextField
              label={t('pages.auth.email')}
              type="email"
              fullWidth
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              sx={{ mb: 2 }}
              autoComplete="email"
            />
            <TextField
              label={t('pages.auth.password')}
              type="password"
              fullWidth
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 1 }}
              autoComplete="current-password"
            />
            {/* `top`, not `right`: measured on the 393px mobile profile, the
                right-placed popper started at x=208 and is ~316px wide, so it
                ended at 524 — 131px past the screen. It is portalled, so it
                widened the *document* (`documentElement.scrollWidth` 524 while
                `body` stayed 393) and Chrome answered by widening the layout
                viewport, i.e. the whole page laid out for a screen no phone
                has. A vertical placement has the full width to shift within.

                `disableInteractive` pairs with that choice and is not cosmetic:
                the checkbox sits directly below the password field (REQ-023), so
                a popper above it covers that field — and MUI tooltips are
                interactive by default (`pointerEvents: 'auto'` while open), which
                would let the tooltip swallow a click meant for the input.

                Measured on the same 393px profile, with the tooltip open: the
                popper's box (276–333) *does* still overlap the password field's
                (285–325), and a click at that field's centre nevertheless lands
                on `INPUT.MuiInputBase-input`. The overlap is visual only, which
                is what `disableInteractive` buys — so do not "fix" the overlap
                by moving the popper somewhere it overflows again.

                `top-start` anchors it to the label's left edge instead of
                centring it over the form. (#1139) */}
            <Tooltip
              title={t('pages.auth.rememberMeTooltip')}
              placement="top-start"
              disableInteractive
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                }
                label={t('pages.auth.rememberMe')}
                sx={{ mb: 1 }}
              />
            </Tooltip>
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={isLoading || !email || !password}
              startIcon={
                isLoading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined
              }
              sx={{ mb: 2 }}
            >
              {t('pages.auth.loginButton')}
            </Button>
          </Form>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Link component={RouterLink} to="/register" variant="body2">
              {t('pages.auth.registerLink')}
            </Link>
            <Link component={RouterLink} to="/password-reset" variant="body2">
              {t('pages.auth.forgotPassword')}
            </Link>
          </Box>

          {oauthProviders.length > 0 && (
            <>
              <Divider sx={{ my: 2 }}>{t('pages.auth.or')}</Divider>
              {oauthProviders.map((p) => (
                <Button
                  key={p.slug}
                  variant="outlined"
                  fullWidth
                  sx={{ mb: 1 }}
                  onClick={() => {
                    window.location.href = `/api/v1/auth/oauth/${encodeURIComponent(p.slug)}`;
                  }}
                >
                  {t('pages.auth.loginWith', { provider: p.display_name })}
                </Button>
              ))}
            </>
          )}

          {oauthError && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {t('pages.auth.oauthProvidersLoadFailed')}
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
