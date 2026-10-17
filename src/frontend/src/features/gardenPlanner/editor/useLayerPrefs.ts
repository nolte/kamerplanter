import { useCallback, useMemo, useRef, useState } from 'react';

/**
 * The layer switches of the plan (REQ-053 GP-FR-031): a per-user view choice kept in `localStorage`,
 * like the length unit. Only the grid has a switch in the MVP editor; plants and labels join with
 * the renderer layers. Every storage access is guarded - a blocked or full storage means the choice
 * lasts for this visit only.
 */
const STORAGE_KEY = 'kp_garden_plan_layers';

export interface LayerPrefs {
  grid: boolean;
}

const DEFAULTS: LayerPrefs = { grid: true };

function read(): LayerPrefs {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === null) return DEFAULTS;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== 'object' || parsed === null) return DEFAULTS;
    const grid = (parsed as { grid?: unknown }).grid;
    return { grid: typeof grid === 'boolean' ? grid : DEFAULTS.grid };
  } catch {
    return DEFAULTS;
  }
}

function write(prefs: LayerPrefs): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    /* private mode or blocked storage: the choice lasts for this visit */
  }
}

export function useLayerPrefs(): {
  prefs: LayerPrefs;
  setLayer: (layer: keyof LayerPrefs, visible: boolean) => void;
} {
  const [prefs, setPrefs] = useState<LayerPrefs>(read);
  const latest = useRef(prefs);
  const setLayer = useCallback((layer: keyof LayerPrefs, visible: boolean) => {
    const next = { ...latest.current, [layer]: visible };
    latest.current = next;
    setPrefs(next);
    write(next);
  }, []);
  return useMemo(() => ({ prefs, setLayer }), [prefs, setLayer]);
}
