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
import { revertEmailChange } from '@/api/endpoints/privacy';
import { isApiError } from '@/api/errors';
import { useAppDispatch } from '@/store/hooks';
import { clearAuth } from '@/store/slices/authSlice';

type RevertStatus = 'idle' | 'pending' | 'success' | 'invalid' | 'conflict' | 'error';

const REVERT_STEPS = [
  'pages.emailChange.revertStepRestore',
  'pages.emailChange.revertStepSignOut',
  'pages.emailChange.revertStepResetLinks',
] as const;

/**
 * Landing of the "undo" link in the notice mailed to the previous address after a
 * confirmed e-mail change (REQ-025 Art. 16, #1848).
 *
 * Nothing is sent on page load: mail scanners and link previews prefetch URLs,
 * and a prefetch must not spend the one-time token or sign anybody out. The page
 * explains what the revert does and posts only on an explicit click.
 *
 * Public and not behind `PublicOnlyRoute` — whoever still holds a session here
 * (possibly the person who took the account over) must not be bounced away from
 * it. A successful revert signs out every session server-side, so the in-memory
 * one is cleared too.
 */
export default function EmailChangeRevertPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<RevertStatus>(() => (token ? 'idle' : 'invalid'));

  const handleRevert = async () => {
    if (!token || status === 'pending') return;
    setStatus('pending');
    try {
      await revertEmailChange(token);
      dispatch(clearAuth());
      setStatus('success');
    } catch (err) {
      if (isApiError(err) && err.statusCode === 401) setStatus('invalid');
      else if (isApiError(err) && err.statusCode === 422) setStatus('conflict');
      else setStatus('error');
    }
  };

  const showExplanation = status === 'idle' || status === 'pending' || status === 'error';

  return (
    <Box
      data-testid="email-change-revert-page"
      sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', px: 2 }}
    >
      <Card sx={{ width: '100%', maxWidth: 520 }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Typography variant="h5" component="h1" gutterBottom sx={{ textAlign: 'center' }}>
            {t('pages.emailChange.revertTitle')}
          </Typography>

          {showExplanation && (
            <>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {t('pages.emailChange.revertIntro')}
              </Typography>
              <Typography variant="subtitle2" component="h2">
                {t('pages.emailChange.revertWhatHappens')}
              </Typography>
              <List dense sx={{ listStyleType: 'disc', pl: 3, mb: 2 }}>
                {REVERT_STEPS.map((key) => (
                  <ListItem key={key} sx={{ display: 'list-item', px: 0 }}>
                    <ListItemText primary={t(key)} />
                  </ListItem>
                ))}
              </List>
              {status === 'error' && (
                <Alert severity="error" sx={{ mb: 2 }} data-testid="email-change-revert-error">
                  {t('pages.emailChange.revertFailed')}
                </Alert>
              )}
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  color="warning"
                  onClick={handleRevert}
                  loading={status === 'pending'}
                  aria-busy={status === 'pending'}
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                  data-testid="email-change-revert-btn"
                >
                  {t('pages.emailChange.revertButton')}
                </Button>
              </Box>
            </>
          )}

          {status === 'success' && (
            <>
              <Alert severity="success" sx={{ mb: 2 }} data-testid="email-change-revert-success">
                {t('pages.emailChange.revertSuccess')}
              </Alert>
              <Alert severity="warning" sx={{ mb: 3 }}>
                {t('pages.emailChange.revertResetAdvice')}
              </Alert>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                <Button
                  component={RouterLink}
                  to="/password-reset"
                  variant="contained"
                  data-testid="email-change-revert-reset-btn"
                >
                  {t('pages.emailChange.resetPasswordButton')}
                </Button>
                <Button component={RouterLink} to="/login" variant="outlined" data-testid="email-change-login-btn">
                  {t('pages.auth.loginButton')}
                </Button>
              </Box>
            </>
          )}

          {(status === 'invalid' || status === 'conflict') && (
            <>
              <Alert severity="error" sx={{ mb: 2 }} data-testid="email-change-revert-error">
                {status === 'invalid'
                  ? t('pages.emailChange.revertInvalid')
                  : t('pages.emailChange.revertConflict')}
              </Alert>
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
