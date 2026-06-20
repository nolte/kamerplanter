import { useMemo } from 'react';

import { useAppSelector } from '@/store/hooks';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import {
  findModuleByPath,
  moduleCatalog,
  type ModuleKey,
} from '@/config/moduleCatalog';

/**
 * REQ-042 — combine the REQ-021 experience-level default with the personal
 * per-module overrides. Return value is `useMemo`-stabilized (hook convention).
 */
export function useModuleVisibility() {
  const { isNavVisible } = useExpertiseLevel();
  const overrides = useAppSelector(
    (s) => s.userPreferences.preferences?.module_visibility ?? {},
  );

  return useMemo(() => {
    const isModuleVisible = (key: ModuleKey): boolean => {
      const def = moduleCatalog[key];
      if (def.core) return true;
      const ov = overrides[key];
      if (ov === 'disabled') return false;
      if (ov === 'enabled') return true;
      return isNavVisible(def.defaultLevel);
    };

    const isPathVisible = (path: string): boolean => {
      const owner = findModuleByPath(path);
      return owner ? isModuleVisible(owner.key) : true;
    };

    return { isModuleVisible, isPathVisible, findModuleByPath, overrides };
  }, [overrides, isNavVisible]);
}
