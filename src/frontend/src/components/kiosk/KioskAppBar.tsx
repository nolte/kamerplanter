import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HomeIcon from '@mui/icons-material/Home';
import LogoutIcon from '@mui/icons-material/Logout';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import LongPressButton from '@/components/kiosk/LongPressButton';
import { KIOSK_LONG_PRESS_MS } from '@/kiosk/longPress';
import { useKiosk } from '@/kiosk/KioskProvider';
import { KIOSK_START_PATH } from '@/kiosk/kioskStartPath';

interface KioskAppBarProps {
  /** Status indicators shown before the controls (connectivity, offline buffer). */
  indicators?: ReactNode;
}

/**
 * UI-NFR-019 — kiosk app bar. Carries the permanent "Kiosk" badge (R-003), a
 * large always-visible Home button (R-018), a large Back button in place of the
 * breadcrumbs on every page below the start page (R-017) and an exit control
 * that leaves the kiosk shell without a reload (R-004) once it was held for 2 s. There is no menu button:
 * kiosk mode has no hamburger and no sidebar (R-021).
 */
export default function KioskAppBar({ indicators }: KioskAppBarProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { disableKiosk } = useKiosk();
  const onStartPage = location.pathname === KIOSK_START_PATH;

  // `key === 'default'` is the first entry of this session: no in-app page to go back to, and
  // `navigate(-1)` would leave the app. Back then means the kiosk start.
  const handleBack = () => {
    if (location.key === 'default') navigate(KIOSK_START_PATH);
    else navigate(-1);
  };

  const handleExit = () => {
    disableKiosk();
    navigate('/dashboard');
  };

  return (
    <AppBar position="static" color="default" data-testid="kiosk-app-bar">
      {/* R-009 — 24px is the recommended (not just the 16px minimum) gap
          between kiosk touch targets, here between Home and Exit. */}
      <Toolbar sx={{ gap: 3, minHeight: { xs: 72, sm: 80 }, flexWrap: 'wrap', py: 1 }}>
        {!onStartPage && (
          <Button
            variant="contained"
            startIcon={<ArrowBackIcon />}
            onClick={handleBack}
            sx={{ minHeight: 64 }}
            data-testid="kiosk-back-button"
          >
            {t('common.back')}
          </Button>
        )}
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
        {indicators}
        <Button
          variant="outlined"
          startIcon={<HomeIcon />}
          onClick={() => navigate(KIOSK_START_PATH)}
          sx={{ minHeight: 64 }}
          data-testid="kiosk-home-button"
        >
          {t('pages.kiosk.home')}
        </Button>
        {/* Operator decision 2026-11-27 — leaving the kiosk is held for 2 s, so a visitor's tap
            (or a wet finger) does not drop the tablet into the full app. Keyboard and assistive
            activation leave directly, as with every LongPressButton. */}
        <LongPressButton
          variant="outlined"
          color="inherit"
          startIcon={<LogoutIcon />}
          onConfirm={handleExit}
          hint={t('pages.kiosk.exitHoldHint', { seconds: KIOSK_LONG_PRESS_MS / 1000 })}
          data-testid="kiosk-exit-button"
        >
          {t('pages.kiosk.exit')}
        </LongPressButton>
      </Toolbar>
    </AppBar>
  );
}
