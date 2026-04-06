import { useMemo, useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { toggleShowAllFields } from '@/store/slices/uiSlice';
import type { ExperienceLevel } from '@/api/types';

const LEVEL_ORDER: Record<ExperienceLevel, number> = {
  beginner: 0,
  intermediate: 1,
  expert: 2,
};

export function useExpertiseLevel() {
  const dispatch = useAppDispatch();
  const preferences = useAppSelector((state) => state.userPreferences.preferences);
  const showAllOverride = useAppSelector((state) => state.ui.showAllFieldsOverride);
  const level = preferences?.experience_level ?? 'beginner';

  const toggleShowAll = useCallback(() => {
    dispatch(toggleShowAllFields());
  }, [dispatch]);

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
