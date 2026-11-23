import { useMemo } from 'react';
import { isLightMode } from '@/config/mode';
import { useSmartHomeEnabled } from '@/hooks/useSmartHomeEnabled';
import { usePlatformAdmin } from '@/hooks/usePlatformAdmin';
import { useAppSelector } from '@/store/hooks';
import type { SettingsGates } from '@/config/settingsGroups';

export interface SettingsGatesState {
  gates: SettingsGates;
  /**
   * Full mode only: the profile that carries `is_platform_admin` has not arrived
   * yet. Until then "not an operator" is not an answer — a platform admin's deep
   * link into the Installation group must not be sent elsewhere because the
   * profile was a few milliseconds late.
   */
  isProfilePending: boolean;
}

/** The inputs of the settings page's visibility gates, read once for the shell and every group. */
export function useSettingsGates(): SettingsGatesState {
  const { isSmartHomeEnabled } = useSmartHomeEnabled();
  const isPlatformAdminUser = usePlatformAdmin();
  const hasUser = useAppSelector((s) => s.auth.user !== null);
  // Installation-wide configuration (storage, weather providers, the Home
  // Assistant connection, the Pl@ntNet key, recognition). In light mode
  // (REQ-027) the sole anonymous user is the operator, which is also how
  // `require_platform_admin` decides server-side (#1385).
  const canManageInstanceSettings = isLightMode || isPlatformAdminUser;
  const isProfilePending = !isLightMode && !hasUser;

  return useMemo(
    () => ({
      gates: {
        lightMode: isLightMode,
        smartHomeEnabled: isSmartHomeEnabled,
        canManageInstanceSettings,
      },
      isProfilePending,
    }),
    [isSmartHomeEnabled, canManageInstanceSettings, isProfilePending],
  );
}
