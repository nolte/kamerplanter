import { useState } from 'react';
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
import CircularProgress from '@mui/material/CircularProgress';
import { useSnackbar } from 'notistack';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { registerLocal, clearError } from '@/store/slices/authSlice';

export default function RegisterPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { isLoading, error } = useAppSelector((s) => s.auth);

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(clearError());
    setLocalError('');

    if (password !== confirmPassword) {
      setLocalError(t('pages.auth.passwordMismatch'));
      return;
    }

    try {
      await dispatch(registerLocal({ email, password, display_name: displayName })).unwrap();
      enqueueSnackbar(t('pages.auth.registrationSuccess'), { variant: 'success' });
      navigate('/login');
    } catch {
      // Error handled by Redux
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom align="center">
            {t('pages.auth.register')}
          </Typography>

          {(error || localError) && (
            <Alert severity="error" sx={{ mb: 2 }}>{localError || error}</Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label={t('pages.auth.displayName')}
              fullWidth
              required
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              sx={{ mb: 2 }}
              autoComplete="name"
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
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={isLoading}
              sx={{ mb: 2 }}
            >
              {isLoading ? <CircularProgress size={24} /> : t('pages.auth.registerButton')}
            </Button>
          </Box>

          <Link component={RouterLink} to="/login" variant="body2">
            {t('pages.auth.loginLink')}
          </Link>
        </CardContent>
      </Card>
    </Box>
  );
}
