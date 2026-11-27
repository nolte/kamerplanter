import { lazy, Suspense, useEffect, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';
import type { Theme } from '@mui/material/styles';
import KioskAppBar, { KIOSK_APP_BAR_MIN_HEIGHT } from '@/components/kiosk/KioskAppBar';
import KioskTimeoutOverlay from '@/components/kiosk/KioskTimeoutOverlay';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import RouteAnnouncer from '@/components/layout/RouteAnnouncer';
import SkipLink from '@/components/layout/SkipLink';
import { preloadKioskChunks } from '@/kiosk/kioskChunks';
import { runKioskReset, useHasUnsavedInput } from '@/kiosk/kioskSession';
import { KIOSK_START_PATH } from '@/kiosk/kioskStartPath';
import { useAppSelector } from '@/store/hooks';
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
 * - the inactivity timeout and its warning, returning to the kiosk start even past an
 *   unsaved-changes prompt, after saying that unsaved input will be discarded (R-033..R-038);
 * - the preload of every kiosk chunk, so the kiosk keeps working offline (review S1);
 * - the 300 ms double-tap debounce for every click below it (R-029);
 * - skip link and route announcement, as in the standard shell (W-09, #3017 W-02).
 */
interface KioskShellProps {
  children: ReactNode;
  /**
   * Move the focus into `main` on mount when it was lost to the body — the shell replaces the
   * standard one when kiosk mode is switched on, which unmounts the focused switch.
   */
  takeFocus?: boolean;
}

/**
 * The sticky kiosk bar's height as the root's `scroll-padding-top` (WCAG 2.2 SC 2.4.11): what the browser scrolls
 * into view in the kiosk shell — a settings heading, a control reached with Shift+Tab — comes to rest below the bar.
 * The standard shell sets the same for its app bar in `MainLayout`; the kiosk bar is higher and has its own value.
 */
const kioskBarClearance = (theme: Theme) => ({
  ':root': {
    scrollPaddingTop: KIOSK_APP_BAR_MIN_HEIGHT.xs,
    [theme.breakpoints.up('sm')]: { scrollPaddingTop: KIOSK_APP_BAR_MIN_HEIGHT.sm },
  },
});

export default function KioskShell({ children, takeFocus = false }: KioskShellProps) {
  const navigate = useNavigate();
  const tapDebounce = useTapDebounce();
  const hasUnsavedInput = useHasUnsavedInput();
  // An identification or pest-detection upload the user is waiting for keeps the session alive.
  const uploading = useAppSelector(
    (s) => Boolean(s.identification?.identifying) || Boolean(s.pestDetection?.detecting),
  );
  const { showWarning, remainingSeconds, dismissWarning } = useKioskTimeout({
    enabled: true,
    paused: uploading,
    // R-035 — the return to the start page is not stoppable by an unsaved-changes prompt; the
    // overlay said beforehand that unsaved input will be discarded (R-038).
    onReset: () => runKioskReset(() => navigate(KIOSK_START_PATH)),
  });

  // #3025 M16 review S1 — every kiosk chunk now, while the tablet is online: the hold button of a
  // destructive dialog, the quick-select tiles, and the start page the timeout returns to.
  useEffect(() => {
    void preloadKioskChunks();
  }, []);

  useEffect(() => {
    if (!takeFocus) return;
    const active = document.activeElement;
    if (active === null || active === document.body) document.getElementById(MAIN_ID)?.focus();
  }, [takeFocus]);

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
      <GlobalStyles styles={kioskBarClearance} />
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
        unsavedInput={hasUnsavedInput}
      />
    </Box>
  );
}
