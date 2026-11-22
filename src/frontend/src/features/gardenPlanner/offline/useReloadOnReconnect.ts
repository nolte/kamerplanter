/**
 * Read from the server again once the connection is back (REQ-053 WP 9.2, R-012; #2789 review C2-C4):
 * every view that shows a cached state or an offline miss calls this with `active` = "what I show is
 * not the server's answer". The reload is kept in a ref, so a caller's unmemoised function cannot turn
 * this into a loop; it fires when `online` or `active` turns true.
 */
import { useEffect, useRef } from 'react';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

export function useReloadOnReconnect(active: boolean, reload: () => void): void {
  const online = useOnlineStatus();
  const reloadRef = useRef(reload);
  useEffect(() => {
    reloadRef.current = reload;
  });
  useEffect(() => {
    if (online && active) reloadRef.current();
  }, [online, active]);
}
