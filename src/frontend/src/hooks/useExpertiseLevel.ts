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
  const loading = useAppSelector((state) => state.userPreferences.loading);
  const rawLevel = preferences?.experience_level;
  const level = rawLevel ?? 'beginner';
  const levelKnown = rawLevel != null && !loading;

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
      // Never hide navigation when level is unknown (not yet loaded or missing)
      isNavVisible: (minLevel: ExperienceLevel) =>
        !levelKnown || LEVEL_ORDER[level] >= LEVEL_ORDER[minLevel],
    }),
    [level, levelKnown, showAllOverride, toggleShowAll],
  );
}
