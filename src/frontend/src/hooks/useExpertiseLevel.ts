import { useMemo, useState, useCallback } from 'react';
import { useAppSelector } from '@/store/hooks';
import type { ExperienceLevel } from '@/api/types';

const LEVEL_ORDER: Record<ExperienceLevel, number> = {
  beginner: 0,
  intermediate: 1,
  expert: 2,
};

export function useExpertiseLevel() {
  const preferences = useAppSelector((state) => state.userPreferences.preferences);
  const level = preferences?.experience_level ?? 'beginner';
  const [showAllOverride, setShowAllOverride] = useState(false);

  const toggleShowAll = useCallback(() => {
    setShowAllOverride((prev) => !prev);
  }, []);

  return useMemo(
    () => ({
      level,
      showAllOverride,
      toggleShowAll,
      isFieldVisible: (minLevel: ExperienceLevel) =>
        showAllOverride || LEVEL_ORDER[level] >= LEVEL_ORDER[minLevel],
      isNavVisible: (minLevel: ExperienceLevel) =>
        LEVEL_ORDER[level] >= LEVEL_ORDER[minLevel],
    }),
    [level, showAllOverride, toggleShowAll],
  );
}
