import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '@/hooks/useNotification';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

/**
 * UI-NFR-012 R-036/R-037 (#3025 N-39) — a snackbar when the connection drops and when it comes back.
 *
 * Only a *change* is announced: the state at mount is what the permanent indicator shows, and a page that opens
 * offline would otherwise greet the user with a toast for a state they did not just enter. Mounted by the
 * connectivity indicator, which each shell (MainLayout, KioskShell) renders exactly once, so a change is
 * announced once. A lazy chunk of its own: the indicator is part of the first paint, the snackbar machinery is
 * not (bundle budget, UI-NFR-003 R-013).
 *
 * Renders nothing.
 */
export interface ConnectivityNoticesProps {
  /**
   * Announce the state at mount as a change. Set when this chunk could only be fetched because the connection
   * came back: that reconnect happened before the component existed and would otherwise go unannounced.
   */
  announceCurrentState?: boolean;
}

export default function ConnectivityNotices({ announceCurrentState = false }: ConnectivityNoticesProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const online = useOnlineStatus();
  const previous = useRef(announceCurrentState ? !online : online);

  useEffect(() => {
    if (previous.current === online) return;
    previous.current = online;
    if (online) notification.info(t('common.pwa.backOnline'));
    else notification.warning(t('common.pwa.wentOffline'));
  }, [online, notification, t]);

  return null;
}
