import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import KioskShell from '@/layouts/KioskShell';
import { useKiosk } from '@/kiosk/KioskProvider';

/**
 * UI-NFR-019 — the `/kiosk` route (R-001). Visiting it turns kiosk mode on (URL entry point, no
 * reload) and renders the start page into the {@link KioskShell}. The pages a tile leads to are
 * NOT children of this route: they stay at their own URLs under `MainLayout`, which renders them
 * into the same shell while kiosk mode is on (#3025 N-37) — one shell, one timeout, one source of
 * truth (`isKiosk` in the KioskProvider).
 */
export default function KioskLayout() {
  const { isKiosk, enableKiosk } = useKiosk();

  // R-001 — reaching the kiosk route by URL turns the mode on (no reload).
  useEffect(() => {
    if (!isKiosk) enableKiosk();
  }, [isKiosk, enableKiosk]);

  return (
    <KioskShell>
      <Outlet />
    </KioskShell>
  );
}
