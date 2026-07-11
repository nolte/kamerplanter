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
import { useKiosk } from '@/kiosk/KioskProvider';

/**
 * UI-NFR-019 §2.1 — Settings entry point for the kiosk mode (R-001) and the
 * standalone high-contrast theme (R-045). Toggling kiosk on offers a direct
 * jump into the kiosk shell; the switch itself changes the mode without a
 * reload (R-004).
 */
export default function KioskSettingsTab() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isKiosk, highContrast, toggleKiosk, setHighContrast } = useKiosk();

  return (
    <Box
      sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}
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
          <FormControlLabel
            control={
              <Switch
                checked={isKiosk}
                onChange={() => toggleKiosk()}
                data-testid="kiosk-mode-toggle"
              />
            }
            label={t('pages.kiosk.settings.toggle')}
          />
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
