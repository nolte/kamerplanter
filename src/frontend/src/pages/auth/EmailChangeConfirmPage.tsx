import { useState } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import { confirmEmailChange } from '@/api/endpoints/privacy';
import { isApiError } from '@/api/errors';
import { useAppDispatch } from '@/store/hooks';
import { clearAuth } from '@/store/slices/authSlice';

type ConfirmStatus = 'idle' | 'pending' | 'success' | 'invalid' | 'error';

const CONFIRM_STEPS = [
  'pages.emailChange.confirmStepAddress',
  'pages.emailChange.confirmStepSignOut',
] as const;

/**
 * Landing of the verification link mailed to the new address (REQ-025 Art. 16, #1848).
 *
 * Nothing is sent on page load: mail scanners prefetch links, and a prefetch at
 * the *new* address must not confirm the change. Otherwise someone could request
 * a change of their own account to a stranger's address and let the stranger's
 * scanner move the account onto it — squatting that address. The page says what
 * the confirmation does and posts only on an explicit click.
 *
 * Public, and deliberately *not* behind `PublicOnlyRoute`: the person who
 * requested the change usually still has a session in this browser and would
 * otherwise be bounced to the dashboard with the change left unconfirmed.
 *
 * The confirmation signs out every session of the account server-side, so the
 * in-memory session is cleared too; the login link then leads to a sign-in with
 * the new address instead of back into a dead session.
 */
export default function EmailChangeConfirmPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<ConfirmStatus>(() => (token ? 'idle' : 'invalid'));

  const handleConfirm = async () => {
    if (!token || status === 'pending') return;
    setStatus('pending');
    try {
      await confirmEmailChange(token);
      dispatch(clearAuth());
      setStatus('success');
    } catch (err) {
      setStatus(isApiError(err) && err.statusCode === 401 ? 'invalid' : 'error');
    }
  };

  const showExplanation = status === 'idle' || status === 'pending' || status === 'error';

  return (
    <Box
      data-testid="email-change-confirm-page"
      sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', px: 2 }}
    >
      <Card sx={{ width: '100%', maxWidth: 520 }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Typography variant="h5" component="h1" gutterBottom sx={{ textAlign: 'center' }}>
            {t('pages.emailChange.confirmTitle')}
          </Typography>

          {showExplanation && (
            <>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {t('pages.emailChange.confirmIntro')}
              </Typography>
              <Typography variant="subtitle2" component="h2">
                {t('pages.emailChange.confirmWhatHappens')}
              </Typography>
              <List dense sx={{ listStyleType: 'disc', pl: 3, mb: 2 }}>
                {CONFIRM_STEPS.map((key) => (
                  <ListItem key={key} sx={{ display: 'list-item', px: 0 }}>
                    <ListItemText primary={t(key)} />
                  </ListItem>
                ))}
              </List>
              {status === 'error' && (
                <Alert severity="error" sx={{ mb: 2 }} data-testid="email-change-confirm-error">
                  {t('pages.emailChange.confirmFailed')}
                </Alert>
              )}
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  onClick={handleConfirm}
                  loading={status === 'pending'}
                  aria-busy={status === 'pending'}
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                  data-testid="email-change-confirm-btn"
                >
                  {t('pages.emailChange.confirmButton')}
                </Button>
              </Box>
            </>
          )}

          {status === 'success' && (
            <>
              <Alert severity="success" sx={{ mb: 2 }} data-testid="email-change-confirm-success">
                {t('pages.emailChange.confirmSuccess')}
              </Alert>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {t('pages.emailChange.confirmSignedOut')}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button component={RouterLink} to="/login" variant="contained" data-testid="email-change-login-btn">
                  {t('pages.auth.loginButton')}
                </Button>
              </Box>
            </>
          )}

          {status === 'invalid' && (
            <>
              <Alert severity="error" sx={{ mb: 2 }} data-testid="email-change-confirm-error">
                {t('pages.emailChange.confirmInvalid')}
              </Alert>
              {/* Keep a way out of the dead end. */}
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button component={RouterLink} to="/login" variant="outlined" data-testid="email-change-login-btn">
                  {t('pages.auth.loginButton')}
                </Button>
              </Box>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
