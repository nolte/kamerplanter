import { useEffect, useState } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import { verifyEmail } from '@/api/endpoints/auth';

export default function EmailVerificationPage() {
  const { t } = useTranslation();
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(() => token ? 'loading' : 'error');
  const [error, setError] = useState(() => token ? '' : t('pages.auth.invalidToken'));

  useEffect(() => {
    if (!token) return;

    verifyEmail(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setStatus('error');
        setError(err?.message || t('pages.auth.verificationFailed'));
      });
  }, [token, t]);

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            {t('pages.auth.emailVerification')}
          </Typography>

          {status === 'loading' && <CircularProgress sx={{ my: 3 }} />}
          {status === 'success' && (
            <>
              <Alert severity="success" sx={{ mb: 2 }}>
                {t('pages.auth.verificationSuccess')}
              </Alert>
              <Button component={RouterLink} to="/login" variant="contained">
                {t('pages.auth.loginButton')}
              </Button>
            </>
          )}
          {status === 'error' && (
            <Alert severity="error">{error}</Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
