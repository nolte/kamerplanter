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

/**
 * The kiosk bar's height below and from `sm` (R-009: 72 px touch row, 80 px with the wider gap). One value for the
 * bar's toolbar and for the root's `scroll-padding-top` in `KioskShell`, so the two cannot drift.
 */
export const KIOSK_APP_BAR_MIN_HEIGHT = { xs: 72, sm: 80 } as const;

/** Below `sm` a control shows its icon only; the label text is its accessible name. */
const wideOnlySx = { display: { xs: 'none', sm: 'inline' } } as const;
const compactButtonSx = {
  minHeight: 64,
  minWidth: 64,
  '& .MuiButton-startIcon': { mr: { xs: 0, sm: 1 }, ml: { xs: 0, sm: -0.5 } },
} as const;

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
    // R-018 — Home (and Back, R-017) must be visible at all times: the bar stays at the top while
    // a long page scrolls under it.
    <AppBar position="sticky" color="default" sx={{ top: 0 }} data-testid="kiosk-app-bar">
      {/* One row down to 390 px: below `sm` the controls show their icon only (their names stay
          as accessible names) and the brand text steps back. R-009 — 16 px between touch targets
          there, 24 px (the recommended gap) from `sm`. The badge is not interactive and sits
          closer to Back. */}
      <Toolbar
        sx={{
          gap: { xs: 2, sm: 3 },
          minHeight: KIOSK_APP_BAR_MIN_HEIGHT,
          flexWrap: 'nowrap',
          px: { xs: 1, sm: 2 },
          py: 1,
        }}
      >
        {!onStartPage && (
          <Button
            variant="contained"
            startIcon={<ArrowBackIcon />}
            onClick={handleBack}
            aria-label={t('common.back')}
            sx={compactButtonSx}
            data-testid="kiosk-back-button"
          >
            <Box component="span" sx={wideOnlySx}>
              {t('common.back')}
            </Box>
          </Button>
        )}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 1 }}>
          <LocalFloristIcon aria-hidden="true" sx={{ fontSize: 36 }} />
          <Typography variant="h5" component="span" sx={{ fontWeight: 700 }}>
            Kamerplanter
          </Typography>
        </Box>
        <Chip
          label={t('pages.kiosk.badge')}
          color="primary"
          sx={{ fontWeight: 700, fontSize: '1rem', height: 40, px: { xs: 0, sm: 1 }, ml: onStartPage ? 0 : { xs: -1, sm: 0 } }}
          data-testid="kiosk-badge"
        />
        <Box sx={{ flexGrow: 1 }} />
        {indicators}
        <Button
          variant="outlined"
          startIcon={<HomeIcon />}
          onClick={() => navigate(KIOSK_START_PATH)}
          aria-label={t('pages.kiosk.home')}
          sx={compactButtonSx}
          data-testid="kiosk-home-button"
        >
          <Box component="span" sx={wideOnlySx}>
            {t('pages.kiosk.home')}
          </Box>
        </Button>
        {/* Operator decision 2026-11-27 — leaving the kiosk is held for 2 s, so a visitor's tap
            (or a wet finger) does not drop the tablet into the full app. Keyboard and assistive
            activation leave directly, as with every LongPressButton. The hint shows on a tap
            (compact bar) and is always part of the button's description. */}
        <LongPressButton
          variant="outlined"
          color="inherit"
          startIcon={<LogoutIcon />}
          onConfirm={handleExit}
          aria-label={t('pages.kiosk.exit')}
          hint={t('pages.kiosk.exitHoldHint', { seconds: KIOSK_LONG_PRESS_MS / 1000 })}
          compactHint
          data-testid="kiosk-exit-button"
        >
          <Box component="span" sx={wideOnlySx}>
            {t('pages.kiosk.exit')}
          </Box>
        </LongPressButton>
      </Toolbar>
    </AppBar>
  );
}
