import { useMemo, useRef, useCallback } from 'react';

import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { saveDashboardLayout } from '@/store/slices/userPreferencesSlice';
import {
  dashboardWidgetCatalog,
  resolveDefaultLayout,
  migrateLayout,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';
import type { DashboardLayout, DashboardWidgetCatalogEntry } from '@/api/types';

const DEBOUNCE_MS = 500;

/**
 * REQ-045 — effective dashboard layout + availability resolution.
 *
 * Combines the stored per-user layout (or the experience-level default when
 * none is stored) with the server-authoritative widget catalog (REQ-042/024/027
 * gating) and the client-side module visibility. Returns a `useMemo`-stabilized
 * object (hook convention).
 */
export function useDashboardLayout() {
  const dispatch = useAppDispatch();
  const { level } = useExpertiseLevel();
  const { isModuleVisible } = useModuleVisibility();
  const stored = useAppSelector((s) => s.userPreferences.preferences?.dashboard_layout ?? null);
  const catalog = useAppSelector((s) => s.dashboard.catalog);
  const catalogLoaded = useAppSelector((s) => s.dashboard.catalogLoaded);

  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const persist = useCallback(
    (layout: DashboardLayout | null, options?: { debounce?: boolean }) => {
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
      }
      if (options?.debounce) {
        timer.current = setTimeout(() => {
          void dispatch(saveDashboardLayout(layout));
          timer.current = null;
        }, DEBOUNCE_MS);
        return;
      }
      void dispatch(saveDashboardLayout(layout));
    },
    [dispatch],
  );

  const reset = useCallback(() => persist(null), [persist]);

  return useMemo(() => {
    const catalogByKey = new Map<string, DashboardWidgetCatalogEntry>(catalog.map((e) => [e.widget_key, e]));
    const availableKeys = new Set(
      catalog.filter((e) => e.available).map((e) => e.widget_key),
    );

    const isCustomized = stored != null;
    const layout: DashboardLayout =
      migrateLayout(stored) ?? resolveDefaultLayout(level, catalogLoaded ? availableKeys : undefined);

    /** A widget renders only when the server marks it available AND its module
     *  is currently visible (REQ-042). Before the catalog loads we stay
     *  optimistic (O-001 parallel load) so rendering is not blocked. */
    const isWidgetRenderable = (widgetKey: string): boolean => {
      const entry = catalogByKey.get(widgetKey);
      if (entry && !entry.available) return false;
      const def = dashboardWidgetCatalog[widgetKey as WidgetKey];
      if (def?.requiredModule && !isModuleVisible(def.requiredModule)) return false;
      return true;
    };

    const activeWidgets = layout.widgets.filter((w) => isWidgetRenderable(w.widget_key));

    return {
      layout,
      isCustomized,
      catalog,
      catalogByKey,
      catalogLoaded,
      availableKeys,
      isWidgetRenderable,
      activeWidgets,
      persist,
      reset,
    };
  }, [stored, catalog, catalogLoaded, level, isModuleVisible, persist, reset]);
}
