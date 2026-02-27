import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import { requestPasswordReset } from '@/api/endpoints/auth';

export default function PasswordResetRequestPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await requestPasswordReset(email);
      setSent(true);
    } catch {
      // Always show success to prevent email enumeration
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom align="center">
            {t('pages.auth.resetPassword')}
          </Typography>

          {sent ? (
            <>
              <Alert severity="success" sx={{ mb: 2 }}>
                {t('pages.auth.resetEmailSent')}
              </Alert>
              <Link component={RouterLink} to="/login" variant="body2">
                {t('pages.auth.backToLogin')}
              </Link>
            </>
          ) : (
            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                label={t('pages.auth.email')}
                type="email"
                fullWidth
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                type="submit"
                variant="contained"
                fullWidth
                disabled={loading}
                sx={{ mb: 2 }}
              >
                {t('pages.auth.sendResetLink')}
              </Button>
              <Link component={RouterLink} to="/login" variant="body2">
                {t('pages.auth.backToLogin')}
              </Link>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
