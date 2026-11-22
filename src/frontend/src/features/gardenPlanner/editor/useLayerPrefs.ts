import { useCallback, useMemo, useRef, useState } from 'react';
import { DEFAULT_LAYER_PREFS, LAYERS, type LayerId, type LayerPrefs } from './layers';

/**
 * The layer switches of the plan (REQ-053 GP-FR-031): a per-user view choice kept in `localStorage`,
 * like the length unit. The layers come from the registry in `layers.ts`; a stored choice that lacks a layer
 * (written before the layer existed) keeps that layer's default. Every storage access is guarded - a blocked
 * or full storage means the choice lasts for this visit only.
 */
const STORAGE_KEY = 'kp_garden_plan_layers';

export type { LayerPrefs };

function read(): LayerPrefs {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === null) return DEFAULT_LAYER_PREFS;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== 'object' || parsed === null) return DEFAULT_LAYER_PREFS;
    const stored = parsed as Record<string, unknown>;
    const next = { ...DEFAULT_LAYER_PREFS };
    for (const { id } of LAYERS) {
      const value = stored[id];
      if (typeof value === 'boolean') next[id] = value;
    }
    return next;
  } catch {
    return DEFAULT_LAYER_PREFS;
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
  setLayer: (layer: LayerId, visible: boolean) => void;
} {
  const [prefs, setPrefs] = useState<LayerPrefs>(read);
  const latest = useRef(prefs);
  const setLayer = useCallback((layer: LayerId, visible: boolean) => {
    const next = { ...latest.current, [layer]: visible };
    latest.current = next;
    setPrefs(next);
    write(next);
  }, []);
  return useMemo(() => ({ prefs, setLayer }), [prefs, setLayer]);
}
