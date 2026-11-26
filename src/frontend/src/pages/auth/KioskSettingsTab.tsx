import { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import TabletMacIcon from '@mui/icons-material/TabletMac';
import LogoutIcon from '@mui/icons-material/Logout';
import { useKiosk } from '@/kiosk/KioskProvider';
import { KIOSK_LONG_PRESS_MS } from '@/kiosk/longPress';
import { GRID_2COL } from './settings/settingsLayout';

// Only a kiosk session holds the switch-off; the hold button is a kiosk chunk.
const LongPressButton = lazy(() => import('@/components/kiosk/LongPressButton'));

/**
 * UI-NFR-019 §2.1 — Settings entry point for the kiosk mode (R-001) and the
 * standalone high-contrast theme (R-045). Toggling kiosk on offers a direct
 * jump into the kiosk shell; the switch itself changes the mode without a
 * reload (R-004).
 */
export default function KioskSettingsTab() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isKiosk, highContrast, toggleKiosk, disableKiosk, setHighContrast } = useKiosk();

  return (
    <Box
      sx={GRID_2COL}
      data-testid="kiosk-settings-tab"
    >
      <Card variant="outlined">
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <TabletMacIcon color="primary" />
            <Typography variant="h6">{t('pages.kiosk.settings.title')}</Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.kiosk.settings.description')}
          </Typography>
          {isKiosk ? (
            // Operator decision 2026-11-27 — inside the kiosk shell this page is reachable by a
            // visitor, so switching the mode OFF is held like the app bar's exit. Turning it on
            // stays the operator's plain switch below.
            <Suspense fallback={null}>
              <LongPressButton
                variant="outlined"
                color="primary"
                startIcon={<LogoutIcon />}
                onConfirm={disableKiosk}
                hint={t('pages.kiosk.exitHoldHint', { seconds: KIOSK_LONG_PRESS_MS / 1000 })}
                data-testid="kiosk-mode-exit"
              >
                {t('pages.kiosk.settings.turnOff')}
              </LongPressButton>
            </Suspense>
          ) : (
            <FormControlLabel
              control={
                <Switch
                  checked={false}
                  onChange={() => toggleKiosk()}
                  data-testid="kiosk-mode-toggle"
                />
              }
              label={t('pages.kiosk.settings.toggle')}
            />
          )}
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              onClick={() => navigate('/kiosk')}
              data-testid="kiosk-open-button"
            >
              {t('pages.kiosk.settings.open')}
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>
            {t('pages.kiosk.settings.highContrastTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.kiosk.settings.highContrastDescription')}
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={highContrast}
                onChange={(e) => setHighContrast(e.target.checked)}
                data-testid="high-contrast-toggle"
              />
            }
            label={t('pages.kiosk.settings.highContrastToggle')}
          />
          {isKiosk && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {t('pages.kiosk.settings.highContrastKioskHint')}
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
