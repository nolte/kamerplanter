import { useMemo } from 'react';
import { useAppSelector } from '@/store/hooks';

export function useSmartHomeEnabled(): { isSmartHomeEnabled: boolean } {
  const smartHomeEnabled = useAppSelector(
    (state) => state.userPreferences.preferences?.smart_home_enabled,
  );
  return useMemo(
    () => ({
      isSmartHomeEnabled: smartHomeEnabled ?? false,
    }),
    [smartHomeEnabled],
  );
}
