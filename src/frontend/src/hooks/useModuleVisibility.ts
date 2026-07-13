import { useMemo } from 'react';

import { useAppSelector } from '@/store/hooks';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useSmartHomeEnabled } from '@/hooks/useSmartHomeEnabled';
import {
  findModuleByPath,
  moduleCatalog,
  type ModuleKey,
} from '@/config/moduleCatalog';
import type { ModuleVisibilityState } from '@/api/types';

// Stable empty fallback so the selector does not hand back a fresh object every
// render (which would churn every downstream useMemo keyed on `overrides`).
const EMPTY_OVERRIDES: Record<string, ModuleVisibilityState> = {};

/**
 * REQ-042 — combine the REQ-021 experience-level default with the personal
 * per-module overrides. Issue #587 layers the `smart_home_enabled` gate on top:
 * a module flagged `requiresSmartHome` is force-hidden while smart home is off,
 * ahead of the override/level resolution. Return value is `useMemo`-stabilized
 * (hook convention).
 */
export function useModuleVisibility() {
  const { isNavVisible } = useExpertiseLevel();
  const { isSmartHomeEnabled } = useSmartHomeEnabled();
  const overrides = useAppSelector(
    (s) => s.userPreferences.preferences?.module_visibility ?? EMPTY_OVERRIDES,
  );

  return useMemo(() => {
    const isModuleVisible = (key: ModuleKey): boolean => {
      const def = moduleCatalog[key];
      // Smart-home gate (issue #587) wins over override + level so sensor/actuator
      // modules stay hidden until the user opts into smart-home features.
      if (def.requiresSmartHome && !isSmartHomeEnabled) return false;
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

    /** True when a path is blocked *specifically* by the smart-home gate (not by
     *  an override or the experience level) — lets ModuleGuard show a targeted
     *  reactivation hint pointing at the smart-home toggle. */
    const isSmartHomeGatedPath = (path: string): boolean => {
      const owner = findModuleByPath(path);
      return owner != null && !!owner.requiresSmartHome && !isSmartHomeEnabled;
    };

    return {
      isModuleVisible,
      isPathVisible,
      isSmartHomeGatedPath,
      findModuleByPath,
      overrides,
      isSmartHomeEnabled,
    };
  }, [overrides, isNavVisible, isSmartHomeEnabled]);
}
