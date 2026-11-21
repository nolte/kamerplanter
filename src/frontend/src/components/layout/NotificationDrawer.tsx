import { useState, useEffect, useCallback, type MouseEvent as ReactMouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
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
import CardActions from '@mui/material/CardActions';
import Chip from '@mui/material/Chip';
import CloseIcon from '@mui/icons-material/Close';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import InboxIcon from '@mui/icons-material/Inbox';
import {
  getNotifications,
  markRead,
  markActed,
  markAllRead,
} from '@/api/endpoints/notifications';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { errorKey } from '@/api/errors';
import { useAbortableLoad } from '@/hooks/useAbortableLoad';
import { captureHandledError } from '@/observability/errorTracking';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { isCareConfirmAction } from '@/utils/careConfirmActions';
import { isLinkActivation, isPlainPrimaryClick } from '@/utils/isPlainPrimaryClick';
import { toSameOriginAppPath } from '@/utils/sameOriginPath';
import type { NotificationResponse, NotificationUrgency } from '@/api/types';

/**
 * A notification exposes a one-tap "Done" affordance when it carries an
 * actionable button and has not been acted on yet — REQ-030 §4.2 (Issue #742).
 * Clicking it drives the source-confirmation callback (`POST …/act`).
 *
 * `canEdit` withholds the affordance for the confirming actions, which persist a
 * `CareConfirmation` and a `WateringLog` and are refused to a viewer by the
 * backend (REQ-030 §4.2, #1441). Comfort, not the boundary: the server refuses
 * the same call with 403 whatever this returns, and `handleDone` rolls the
 * optimistic update back and surfaces that refusal. Every other action — read,
 * acted, snooze — stays open to every member, because that is per-user state.
 */
function actionableActionId(
  notification: NotificationResponse,
  canEdit: boolean,
): string | null {
  if (notification.acted_at) return null;
  const action = notification.actions?.[0];
  if (!action) return null;
  if (!canEdit && isCareConfirmAction(notification.notification_type, action.action_id)) {
    return null;
  }
  return action.action_id;
}

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
  const notify = useNotification();
  const { canEdit } = useTenantPermissions();

  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [markingAllRead, setMarkingAllRead] = useState(false);
  // A failed page load is shown as such, with a retry — never as "no notifications" (#3037).
  const [loadError, setLoadError] = useState<{ key: string; offset: number; append: boolean } | null>(null);
  // Keys currently awaiting the `POST …/act` round-trip — drives the per-button
  // loading state and guards against a second tap while one is in flight
  // (UI-NFR-008 R-016/R-017 double-submit protection).
  const [actingKeys, setActingKeys] = useState<Set<string>>(new Set());

  // Latest-wins (#3014): a reopen or a reset supersedes a pending page, so a stale
  // answer can neither put its error over a fresh list nor append into a reset one.
  const beginLoad = useAbortableLoad();
  const loadNotifications = useCallback(
    async (currentOffset: number, append: boolean) => {
      const ticket = beginLoad();
      setLoading(true);
      setLoadError(null);
      try {
        const result = await getNotifications({
          limit: PAGE_SIZE,
          offset: currentOffset,
        });
        if (!ticket.isCurrent()) return;
        if (append) {
          setNotifications((prev) => [...prev, ...result.items]);
        } else {
          setNotifications(result.items);
        }
        setHasMore(result.items.length === PAGE_SIZE);
        onCountChange(result.unread_count);
      } catch (err) {
        if (!ticket.isCurrent()) return;
        captureHandledError(err, { source: 'NotificationDrawer.load' });
        setLoadError({ key: errorKey(err, 'errors.loadFailed'), offset: currentOffset, append });
      } finally {
        if (ticket.isCurrent()) setLoading(false);
      }
    },
    [onCountChange, beginLoad],
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
    } catch (err) {
      // Marking as read is a side effect of opening the notification; the card
      // simply stays unread and the next open retries it. Reported, not shown.
      captureHandledError(err, { source: 'NotificationDrawer.markRead' });
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
    } catch (err) {
      captureHandledError(err, { source: 'NotificationDrawer.markAllRead' });
      notify.error(t('pages.notifications.markAllReadError'));
    } finally {
      setMarkingAllRead(false);
    }
  };

  const handleDone = async (
    notification: NotificationResponse,
    actionId: string,
  ) => {
    // A second tap while the round-trip is in flight is a no-op — the button
    // is already disabled via the `loading` prop, but this guards against
    // stray re-entrancy (e.g. Enter + click firing together).
    if (actingKeys.has(notification.key)) return;

    const wasUnread = !notification.read_at;
    const unreadCountBeforeAction = notifications.filter((n) => !n.read_at).length;
    const nowIso = new Date().toISOString();

    setActingKeys((prev) => new Set(prev).add(notification.key));
    // Optimistic update: mark acted + read immediately so the button disappears
    // and the badge drops without waiting for the round-trip.
    setNotifications((prev) =>
      prev.map((n) =>
        n.key === notification.key
          ? { ...n, acted_at: nowIso, read_at: n.read_at ?? nowIso }
          : n,
      ),
    );
    if (wasUnread) {
      onCountChange(Math.max(0, unreadCountBeforeAction - 1));
    }
    try {
      const updated = await markActed(notification.key, actionId);
      setNotifications((prev) =>
        prev.map((n) => (n.key === notification.key ? updated : n)),
      );
    } catch {
      // Roll back the optimistic update — including the unread badge, which
      // was decremented above — and surface the failure so the user knows the
      // "Done" tap did not actually confirm the source reminder.
      setNotifications((prev) =>
        prev.map((n) => (n.key === notification.key ? notification : n)),
      );
      if (wasUnread) {
        onCountChange(unreadCountBeforeAction);
      }
      notify.error(t('pages.notifications.markDoneError'));
    } finally {
      setActingKeys((prev) => {
        const next = new Set(prev);
        next.delete(notification.key);
        return next;
      });
    }
  };

  /**
   * Marks the notification read. With an action URL the card is a real link (#3047): the router follows
   * it, so this only closes the drawer — and only for a plain primary click; a Ctrl/Cmd/Shift/middle click
   * opens the target in a new tab and leaves this one where it is. A right click (`auxclick` with
   * `button === 2`) opens the context menu and is no activation: nothing is marked, nothing closes.
   */
  const handleNotificationClick = (
    notification: NotificationResponse,
    actionUrl: string | null,
    event: ReactMouseEvent<HTMLElement>,
  ) => {
    if (!isLinkActivation(event)) return;
    void handleMarkRead(notification);
    if (actionUrl && isPlainPrimaryClick(event)) onClose();
  };

  const handleRetryLoad = () => {
    if (!loadError) return;
    void loadNotifications(loadError.offset, loadError.append);
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
        {notifications.length === 0 && !loading && !loadError && (
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
            {(() => {
              // Only a same-origin app path becomes a link: the URL is server data that may derive from
              // user content (#3012).
              const actionUrl = toSameOriginAppPath(notification.data?.action_url as string | undefined);
              const content = (
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
                  <Typography variant="caption" color="text.secondary">
                    {formatRelativeTime(notification.created_at, t)}
                  </Typography>
                </CardContent>
              );
              const onClick = (e: ReactMouseEvent<HTMLElement>) => handleNotificationClick(notification, actionUrl, e);
              const testId = `notification-action-${notification.key}`;
              return actionUrl ? (
                <CardActionArea component={RouterLink} to={actionUrl} onClick={onClick} onAuxClick={onClick} data-testid={testId}>
                  {content}
                </CardActionArea>
              ) : (
                <CardActionArea onClick={onClick} data-testid={testId}>
                  {content}
                </CardActionArea>
              );
            })()}
            {(() => {
              const actionId = actionableActionId(notification, canEdit);
              if (!actionId) return null;
              return (
                <CardActions sx={{ pt: 0, px: 2, pb: 1.5, justifyContent: 'flex-end' }}>
                  <Button
                    size="small"
                    variant="outlined"
                    color="success"
                    startIcon={<CheckCircleOutlineIcon />}
                    onClick={() => void handleDone(notification, actionId)}
                    loading={actingKeys.has(notification.key)}
                    aria-busy={actingKeys.has(notification.key)}
                    data-testid={`notification-action-done-${notification.key}`}
                    // UI-NFR-001 R-011: 44px touch target — `size="small"` alone
                    // caps the rendered height at ~30px, well under the 48px
                    // mobile/tablet minimum.
                    sx={{ minHeight: 44 }}
                  >
                    {t('pages.notifications.markDone')}
                  </Button>
                </CardActions>
              );
            })()}
          </Card>
        ))}

        {/* Load more / Loading indicator */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        {!loading && loadError && (
          <ErrorDisplay error={loadError.key} onRetry={handleRetryLoad} />
        )}
        {!loading && !loadError && hasMore && notifications.length > 0 && (
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
