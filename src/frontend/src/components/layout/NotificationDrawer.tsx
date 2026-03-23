import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import Chip from '@mui/material/Chip';
import CloseIcon from '@mui/icons-material/Close';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import InboxIcon from '@mui/icons-material/Inbox';
import {
  getNotifications,
  markRead,
  markAllRead,
} from '@/api/endpoints/notifications';
import type { NotificationResponse, NotificationUrgency } from '@/api/types';

const DRAWER_WIDTH = 400;
const PAGE_SIZE = 20;

function urgencyColor(urgency: NotificationUrgency): string {
  switch (urgency) {
    case 'critical':
      return 'error.main';
    case 'high':
      return 'warning.main';
    case 'normal':
      return 'info.main';
    case 'low':
    default:
      return 'grey.400';
  }
}

function formatRelativeTime(dateStr: string | null, t: (key: string) => string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);

  if (diffMinutes < 1) return t('pages.notifications.justNow');
  if (diffMinutes < 60)
    return t('pages.notifications.minutesAgo').replace('{{count}}', String(diffMinutes));
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24)
    return t('pages.notifications.hoursAgo').replace('{{count}}', String(diffHours));
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7)
    return t('pages.notifications.daysAgo').replace('{{count}}', String(diffDays));
  return date.toLocaleDateString();
}

interface NotificationDrawerProps {
  open: boolean;
  onClose: () => void;
  onCountChange: (count: number) => void;
}

export default function NotificationDrawer({
  open,
  onClose,
  onCountChange,
}: NotificationDrawerProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [markingAllRead, setMarkingAllRead] = useState(false);

  const loadNotifications = useCallback(
    async (currentOffset: number, append: boolean) => {
      setLoading(true);
      try {
        const result = await getNotifications({
          limit: PAGE_SIZE,
          offset: currentOffset,
        });
        if (append) {
          setNotifications((prev) => [...prev, ...result.items]);
        } else {
          setNotifications(result.items);
        }
        setHasMore(result.items.length === PAGE_SIZE);
        onCountChange(result.unread_count);
      } catch {
        // Silently ignore
      } finally {
        setLoading(false);
      }
    },
    [onCountChange],
  );

  useEffect(() => {
    if (open) {
      setOffset(0);
      setHasMore(true);
      void loadNotifications(0, false);
    }
  }, [open, loadNotifications]);

  const handleLoadMore = () => {
    const newOffset = offset + PAGE_SIZE;
    setOffset(newOffset);
    void loadNotifications(newOffset, true);
  };

  const handleMarkRead = async (notification: NotificationResponse) => {
    if (notification.read_at) return;
    try {
      const updated = await markRead(notification.key);
      setNotifications((prev) =>
        prev.map((n) => (n.key === notification.key ? updated : n)),
      );
      // Decrement is handled by re-fetching count on next load
      // The parent will get the accurate count when the drawer is re-opened
    } catch {
      // Silently ignore
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAllRead(true);
    try {
      await markAllRead();
      setNotifications((prev) =>
        prev.map((n) => ({
          ...n,
          read_at: n.read_at ?? new Date().toISOString(),
        })),
      );
      onCountChange(0);
    } catch {
      // Silently ignore
    } finally {
      setMarkingAllRead(false);
    }
  };

  const handleNotificationClick = (notification: NotificationResponse) => {
    void handleMarkRead(notification);
    const actionUrl = notification.data?.action_url as string | undefined;
    if (actionUrl) {
      navigate(actionUrl);
      onClose();
    }
  };

  const unreadExist = notifications.some((n) => !n.read_at);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{
        paper: {
          sx: {
            width: { xs: '100%', sm: DRAWER_WIDTH },
            maxWidth: '100vw',
          },
          role: 'region',
          'aria-label': t('pages.notifications.title'),
        } as Record<string, unknown>,
      }}
      data-testid="notification-drawer"
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2,
          py: 1.5,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" component="h2">
          {t('pages.notifications.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {unreadExist && (
            <Button
              size="small"
              startIcon={
                markingAllRead ? (
                  <CircularProgress size={14} />
                ) : (
                  <DoneAllIcon />
                )
              }
              onClick={handleMarkAllRead}
              disabled={markingAllRead}
              data-testid="mark-all-read-btn"
            >
              {t('pages.notifications.markAllRead')}
            </Button>
          )}
          <IconButton
            onClick={onClose}
            size="small"
            aria-label={t('common.close')}
            data-testid="notification-drawer-close"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Notification List */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          px: 1,
          py: 1,
        }}
        role="list"
        aria-label={t('pages.notifications.title')}
      >
        {notifications.length === 0 && !loading && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 8,
              color: 'text.secondary',
            }}
          >
            <InboxIcon sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
            <Typography variant="body2">
              {t('pages.notifications.empty')}
            </Typography>
          </Box>
        )}

        {notifications.map((notification) => (
          <Card
            key={notification.key}
            variant="outlined"
            role="listitem"
            sx={{
              mb: 1,
              borderLeft: 4,
              borderLeftColor: urgencyColor(notification.urgency),
              opacity: notification.read_at ? 0.7 : 1,
              bgcolor: notification.read_at
                ? 'transparent'
                : 'action.hover',
            }}
            data-testid={`notification-card-${notification.key}`}
          >
            <CardActionArea
              onClick={() => handleNotificationClick(notification)}
              data-testid={`notification-action-${notification.key}`}
            >
              <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    mb: 0.5,
                  }}
                >
                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: notification.read_at ? 'normal' : 'bold',
                      flex: 1,
                      mr: 1,
                    }}
                  >
                    {notification.title}
                  </Typography>
                  {notification.urgency !== 'normal' &&
                    notification.urgency !== 'low' && (
                      <Chip
                        size="small"
                        label={notification.urgency}
                        color={
                          notification.urgency === 'critical'
                            ? 'error'
                            : 'warning'
                        }
                        sx={{ height: 20, fontSize: '0.6875rem' }}
                      />
                    )}
                </Box>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mb: 0.5,
                    whiteSpace: 'pre-line',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {notification.body}
                </Typography>
                <Typography variant="caption" color="text.disabled">
                  {formatRelativeTime(notification.created_at, t)}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}

        {/* Load more / Loading indicator */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        {!loading && hasMore && notifications.length > 0 && (
          <>
            <Divider sx={{ my: 1 }} />
            <Button
              fullWidth
              size="small"
              onClick={handleLoadMore}
              data-testid="notification-load-more"
            >
              {t('pages.notifications.loadMore')}
            </Button>
          </>
        )}
      </Box>
    </Drawer>
  );
}
