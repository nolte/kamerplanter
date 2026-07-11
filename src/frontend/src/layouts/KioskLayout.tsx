import { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import KioskAppBar from '@/components/kiosk/KioskAppBar';
import KioskTimeoutOverlay from '@/components/kiosk/KioskTimeoutOverlay';
import { useKiosk } from '@/kiosk/KioskProvider';
import { useKioskTimeout } from '@/kiosk/useKioskTimeout';

/**
 * UI-NFR-019 — kiosk shell layout (R-001). No sidebar, no breadcrumbs — just the
 * kiosk app bar plus the routed content. Visiting ``/kiosk`` directly activates
 * kiosk mode (URL entry point) and arms the inactivity timeout (§2.6).
 */
export default function KioskLayout() {
  const navigate = useNavigate();
  const { isKiosk, enableKiosk } = useKiosk();

  // R-001 — reaching the kiosk route by URL turns the mode on (no reload).
  useEffect(() => {
    if (!isKiosk) enableKiosk();
  }, [isKiosk, enableKiosk]);

  const { showWarning, remainingSeconds, dismissWarning } = useKioskTimeout({
    enabled: isKiosk,
    onReset: () => navigate('/kiosk'),
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      <KioskAppBar />
      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, sm: 3 } }}>
        <Outlet />
      </Box>
      <KioskTimeoutOverlay
        open={showWarning}
        remainingSeconds={remainingSeconds}
        onContinue={dismissWarning}
      />
    </Box>
  );
}
