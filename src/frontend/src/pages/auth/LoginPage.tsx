import { useState, useEffect } from 'react';
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
import CircularProgress from '@mui/material/CircularProgress';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { loginLocal, clearError } from '@/store/slices/authSlice';
import { getOAuthProviders } from '@/api/endpoints/auth';
import type { OAuthProviderListItem } from '@/api/types';

export default function LoginPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isLoading, error, isAuthenticated } = useAppSelector((s) => s.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [oauthProviders, setOauthProviders] = useState<OAuthProviderListItem[]>([]);

  useEffect(() => {
    dispatch(clearError());
    getOAuthProviders().then(setOauthProviders).catch(() => {});
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(loginLocal({ email, password }));
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom align="center">
            {t('pages.auth.login')}
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit}>
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
              sx={{ mb: 2 }}
              autoComplete="current-password"
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={isLoading}
              sx={{ mb: 2 }}
            >
              {isLoading ? <CircularProgress size={24} /> : t('pages.auth.loginButton')}
            </Button>
          </Box>

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
                  disabled
                >
                  {t('pages.auth.loginWith', { provider: p.display_name })}
                </Button>
              ))}
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
