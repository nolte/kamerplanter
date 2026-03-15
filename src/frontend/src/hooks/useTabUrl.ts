import { useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

/**
 * Syncs MUI Tabs index with URL hash fragment for deep-linkable tabs.
 *
 * Usage:
 *   const [tab, setTab] = useTabUrl(['details', 'stock', 'edit']);
 *   <Tabs value={tab} onChange={(_, v) => setTab(v)}>
 *
 * URL example: /duengung/fertilizers/123#stock → tab index 1
 * Unknown or missing hash → falls back to index 0.
 */
export function useTabUrl(tabs: readonly string[]): [number, (index: number) => void] {
  const location = useLocation();
  const navigate = useNavigate();

  // Stabilize tabs reference by join key
  const tabsKey = tabs.join('\0');
  const stableTabs = useMemo(() => tabs, [tabsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const currentIndex = useMemo(() => {
    const hash = location.hash.replace('#', '');
    if (!hash) return 0;
    const idx = stableTabs.indexOf(hash);
    return idx >= 0 ? idx : 0;
  }, [location.hash, stableTabs]);

  const setTab = useCallback(
    (index: number) => {
      const slug = stableTabs[index];
      if (slug != null) {
        navigate({ hash: index === 0 ? '' : slug }, { replace: true });
      }
    },
    [stableTabs, navigate],
  );

  return [currentIndex, setTab];
}
