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
import CircularProgress from '@mui/material/CircularProgress';
import { isRateLimited } from '@/api/client';
import { isApiError } from '@/api/errors';
import { resendVerification } from '@/api/endpoints/auth';
import Form from '@/components/form/Form';

type Outcome = 'sent' | 'rateLimited' | 'failed' | null;

/**
 * Ask for a new verification link without signing in first (REQ-023, #2037).
 *
 * The landing for a link that has expired or was used up: `EmailVerificationPage`
 * points here from its error state. The confirmation never says whether a mail
 * went out — the backend answers every address alike, and so does this page.
 */
export default function ResendVerificationPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [outcome, setOutcome] = useState<Outcome>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setOutcome(null);
    try {
      await resendVerification(email);
      setOutcome('sent');
    } catch (error) {
      setOutcome(isRateLimited(error) || (isApiError(error) && error.statusCode === 429) ? 'rateLimited' : 'failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}
      data-testid="resend-verification-page"
    >
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" component="h1" gutterBottom align="center">
            {t('pages.auth.resendVerificationTitle')}
          </Typography>

          {outcome === 'sent' ? (
            <>
              <Alert severity="success" sx={{ mb: 2 }} data-testid="resend-verification-status">
                {t('pages.auth.verificationResent')}
              </Alert>
              <Link component={RouterLink} to="/login" variant="body2">
                {t('pages.auth.backToLogin')}
              </Link>
            </>
          ) : (
            <Form onSubmit={handleSubmit}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.auth.resendVerificationIntro')}
              </Typography>
              {outcome && (
                <Alert severity="error" sx={{ mb: 2 }} data-testid="resend-verification-status">
                  {outcome === 'rateLimited'
                    ? t('pages.auth.verificationResendRateLimited')
                    : t('pages.auth.verificationResendFailed')}
                </Alert>
              )}
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
              <Button
                type="submit"
                variant="contained"
                fullWidth
                disabled={loading || !email}
                startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined}
                sx={{ mb: 2 }}
                data-testid="resend-verification-submit"
              >
                {t('pages.auth.resendVerification')}
              </Button>
              <Link component={RouterLink} to="/login" variant="body2">
                {t('pages.auth.backToLogin')}
              </Link>
            </Form>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
