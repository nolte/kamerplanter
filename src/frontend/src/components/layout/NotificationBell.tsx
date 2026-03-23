import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { useTranslation } from 'react-i18next';
import { getUnreadCount } from '@/api/endpoints/notifications';
import NotificationDrawer from './NotificationDrawer';

const POLL_INTERVAL_MS = 60_000;

export default function NotificationBell() {
  const { t } = useTranslation();
  const [unreadCount, setUnreadCount] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchCount = useCallback(async () => {
    try {
      const result = await getUnreadCount();
      setUnreadCount(result.unread_count);
    } catch {
      // Silently ignore — bell just shows stale count
    }
  }, []);

  useEffect(() => {
    void fetchCount();
    intervalRef.current = setInterval(() => void fetchCount(), POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchCount]);

  const handleDrawerClose = useCallback(() => {
    setDrawerOpen(false);
    // Refresh count after drawer closes (user may have read notifications)
    void fetchCount();
  }, [fetchCount]);

  const handleDrawerOpen = useCallback(() => {
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
        <NotificationDrawer
          open={drawerOpen}
          onClose={handleDrawerClose}
          onCountChange={setUnreadCount}
        />
      </>
    ),
    [drawerOpen, handleDrawerClose, handleDrawerOpen, t, unreadCount],
  );
}
