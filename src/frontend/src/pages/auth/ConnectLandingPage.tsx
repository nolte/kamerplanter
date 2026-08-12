import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import PhoneAndroidIcon from '@mui/icons-material/PhoneAndroid';

/**
 * Browser landing for the light-mode instance-discovery deep link (#1118 P13).
 *
 * The light-mode "Connect app" QR now encodes the plain URL
 * `https://<instance>/connect?v=1` so a phone's system camera recognizes it as a
 * link. When the future Kamerplanter Android app is installed it catches that URL
 * through a wildcard-host `intent-filter` and never reaches the web; but the same
 * URL must not 404 for everyone without the app. This page is that graceful
 * fallback: it explains that the link opens the Kamerplanter app, and lets a
 * visitor continue in the browser instead.
 *
 * It is a standalone, credential-free page mounted **outside** the auth guard and
 * outside the light/full mode gating, so a fresh system-camera visitor reaches it
 * in either deployment mode without being bounced to a login they may not have.
 * It reads nothing from and writes nothing to account state.
 */
export default function ConnectLandingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleContinue = useCallback(() => {
    // "/" resolves per mode: the light-mode dashboard, or the full-mode login for
    // a visitor without a session. Either is a sensible browser destination.
    navigate('/', { replace: true });
  }, [navigate]);

  return (
    <Box
      data-testid="connect-landing-page"
      sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', p: 2 }}
    >
      <Card sx={{ width: '100%', maxWidth: 460 }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <PhoneAndroidIcon color="primary" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            {t('pages.auth.connectLanding.title')}
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.auth.connectLanding.intro')}
          </Typography>
          <Alert severity="info" icon={false} sx={{ textAlign: 'left', mb: 3 }}>
            <Typography variant="body2">{t('pages.auth.connectLanding.appHint')}</Typography>
          </Alert>
          <Button
            variant="contained"
            onClick={handleContinue}
            data-testid="connect-landing-continue"
            fullWidth
            // UI-NFR-001 R-011 — 48px minimum touch target on mobile.
            sx={{ minHeight: 48 }}
          >
            {t('pages.auth.connectLanding.continueInBrowser')}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
