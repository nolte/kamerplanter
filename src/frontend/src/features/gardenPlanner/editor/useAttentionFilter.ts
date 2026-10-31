import { useCallback, useMemo, useState } from 'react';

/**
 * The filter "only plants that need attention" of the plant-state layer (REQ-053 GP-UX-061, #2488): a per-user view
 * choice kept in `localStorage` like the layer switches (`useLayerPrefs`). Every storage access is guarded - a blocked
 * or full storage means the choice lasts for this visit only.
 */
const STORAGE_KEY = 'kp_garden_plan_attention_filter';

function read(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

export function useAttentionFilter(): readonly [boolean, (active: boolean) => void] {
  const [active, setActiveState] = useState<boolean>(read);
  const setActive = useCallback((next: boolean) => {
    setActiveState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, String(next));
    } catch {
      /* private mode or blocked storage: the choice lasts for this visit */
    }
  }, []);
  return useMemo(() => [active, setActive] as const, [active, setActive]);
}
