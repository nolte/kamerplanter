import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import HomeIcon from '@mui/icons-material/Home';
import LogoutIcon from '@mui/icons-material/Logout';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import { useKiosk } from '@/kiosk/KioskProvider';

/**
 * UI-NFR-019 — kiosk app bar. Carries the permanent "Kiosk" badge (R-003), a
 * large always-visible Home button (R-018) and an exit control that leaves the
 * kiosk shell without a reload (R-004).
 */
export default function KioskAppBar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { disableKiosk } = useKiosk();

  const handleExit = () => {
    disableKiosk();
    navigate('/dashboard');
  };

  return (
    <AppBar position="static" color="default" data-testid="kiosk-app-bar">
      {/* R-009 — 24px is the recommended (not just the 16px minimum) gap
          between kiosk touch targets, here between Home and Exit. */}
      <Toolbar sx={{ gap: 3, minHeight: { xs: 72, sm: 80 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LocalFloristIcon aria-hidden="true" sx={{ fontSize: 36 }} />
          <Typography variant="h5" component="span" sx={{ fontWeight: 700 }}>
            Kamerplanter
          </Typography>
        </Box>
        <Chip
          label={t('pages.kiosk.badge')}
          color="primary"
          sx={{ fontWeight: 700, fontSize: '1rem', height: 40, px: 1 }}
          data-testid="kiosk-badge"
        />
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="outlined"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/kiosk')}
          sx={{ minHeight: 64 }}
          data-testid="kiosk-home-button"
        >
          {t('pages.kiosk.home')}
        </Button>
        <Button
          variant="text"
          startIcon={<LogoutIcon />}
          onClick={handleExit}
          sx={{ minHeight: 64 }}
          data-testid="kiosk-exit-button"
        >
          {t('pages.kiosk.exit')}
        </Button>
      </Toolbar>
    </AppBar>
  );
}
