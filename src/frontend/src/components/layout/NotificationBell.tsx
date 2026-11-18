import { lazy, Suspense, useState, useEffect, useCallback, useRef, useMemo } from 'react';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { useTranslation } from 'react-i18next';
import { getUnreadCount } from '@/api/endpoints/notifications';

// #3023 (W-30) — the drawer is its own chunk, fetched on the first click on the bell instead of with the shell.
const NotificationDrawer = lazy(() => import('./NotificationDrawer'));

const POLL_INTERVAL_MS = 60_000;

function isDocumentHidden(): boolean {
  return typeof document !== 'undefined' && document.visibilityState === 'hidden';
}

export default function NotificationBell() {
  const { t } = useTranslation();
  const [unreadCount, setUnreadCount] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  // Mounted from the first open on and kept afterwards, so the drawer's close transition still plays.
  const [drawerMounted, setDrawerMounted] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchCount = useCallback(async () => {
    try {
      const result = await getUnreadCount();
      setUnreadCount(result.unread_count);
    } catch {
      // Silently ignore — bell just shows stale count
    }
  }, []);

  // #3023 (W-28) — poll only while the tab is visible: a background tab sends no requests, and the count is
  // refreshed at once when the tab comes back, so the badge is current the moment it can be seen again.
  useEffect(() => {
    const startPolling = () => {
      if (intervalRef.current === null) {
        intervalRef.current = setInterval(() => void fetchCount(), POLL_INTERVAL_MS);
      }
    };
    const stopPolling = () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    const handleVisibilityChange = () => {
      if (isDocumentHidden()) {
        stopPolling();
        return;
      }
      void fetchCount();
      startPolling();
    };

    if (!isDocumentHidden()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- async fetch, setState is inside callback
      void fetchCount();
      startPolling();
    }
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      stopPolling();
    };
  }, [fetchCount]);

  const handleDrawerClose = useCallback(() => {
    setDrawerOpen(false);
    // Refresh count after drawer closes (user may have read notifications)
    void fetchCount();
  }, [fetchCount]);

  const handleDrawerOpen = useCallback(() => {
    setDrawerMounted(true);
    setDrawerOpen(true);
  }, []);

  return useMemo(
    () => (
      <>
        <IconButton
          color="inherit"
          onClick={handleDrawerOpen}
          aria-label={t('pages.notifications.title')}
          data-testid="notification-bell"
          sx={{ ml: 0.5 }}
        >
          <Badge
            badgeContent={unreadCount}
            color="error"
            max={99}
            invisible={unreadCount === 0}
          >
            <NotificationsIcon />
          </Badge>
        </IconButton>
        {drawerMounted && (
          <Suspense fallback={null}>
            <NotificationDrawer
              open={drawerOpen}
              onClose={handleDrawerClose}
              onCountChange={setUnreadCount}
            />
          </Suspense>
        )}
      </>
    ),
    [drawerMounted, drawerOpen, handleDrawerClose, handleDrawerOpen, t, unreadCount],
  );
}
