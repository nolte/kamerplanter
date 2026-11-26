import { lazy, Suspense, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import KioskAppBar from '@/components/kiosk/KioskAppBar';
import KioskTimeoutOverlay from '@/components/kiosk/KioskTimeoutOverlay';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import RouteAnnouncer from '@/components/layout/RouteAnnouncer';
import SkipLink from '@/components/layout/SkipLink';
import { KIOSK_START_PATH } from '@/kiosk/kioskStartPath';
import { useKioskTimeout } from '@/kiosk/useKioskTimeout';
import { useTapDebounce } from '@/kiosk/useTapDebounce';

// REQ-053 WP 9.4 — unsent offline entries and their sync; the same host the standard shell mounts.
const OfflineSyncHost = lazy(() => import('@/features/gardenPlanner/offline/OfflineSyncHost'));

const MAIN_ID = 'main-content';

/**
 * UI-NFR-019 — the kiosk shell: everything a page shows around its content while kiosk mode is on.
 *
 * It is the ONE place the kiosk rules of the frame live, so they hold on every page a kiosk
 * session reaches — the `/kiosk` start page (`KioskLayout`) and every page a tile or a
 * link leads to (`MainLayout` renders its routes into this shell instead of its own while
 * `isKiosk` is set; #3025 N-37):
 *
 * - kiosk app bar with badge, Home, Back and Exit — no menu button, no sidebar, no breadcrumbs
 *   (R-003, R-017, R-018, R-021);
 * - the inactivity timeout and its warning, returning to the kiosk start (R-033..R-036);
 * - the 300 ms double-tap debounce for every click below it (R-029);
 * - skip link and route announcement, as in the standard shell (W-09, #3017 W-02).
 */
export default function KioskShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const tapDebounce = useTapDebounce();
  const { showWarning, remainingSeconds, dismissWarning } = useKioskTimeout({
    enabled: true,
    onReset: () => navigate(KIOSK_START_PATH),
  });

  return (
    <Box
      {...tapDebounce}
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
      data-testid="kiosk-shell"
    >
      <SkipLink targetId={MAIN_ID} />
      <KioskAppBar
        indicators={
          <>
            <Suspense fallback={null}>
              <OfflineSyncHost />
            </Suspense>
            <ConnectivityIndicator />
          </>
        }
      />
      <RouteAnnouncer mainId={MAIN_ID} />
      <Box
        component="main"
        id={MAIN_ID}
        tabIndex={-1}
        sx={{ flexGrow: 1, minWidth: 0, p: { xs: 2, sm: 3 }, '&:focus': { outline: 'none' } }}
      >
        {children}
      </Box>
      <KioskTimeoutOverlay
        open={showWarning}
        remainingSeconds={remainingSeconds}
        onContinue={dismissWarning}
      />
    </Box>
  );
}
