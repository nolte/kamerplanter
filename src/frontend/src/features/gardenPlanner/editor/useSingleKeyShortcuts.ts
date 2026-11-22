/**
 * The "single-key shortcuts" setting (REQ-053 GP-UX-045, WCAG 2.1.4): printable one-key shortcuts
 * (`?`, later `G`, `R`, `+`, `-`) fire only while the plan has the focus, and can be switched off
 * here. On by default. Kept in localStorage - a per-device convenience, never required to render.
 */
import { useCallback, useMemo, useState } from 'react';

const STORAGE_KEY = 'kamerplanter.gardenPlan.singleKeyShortcuts';

function read(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) !== 'off';
  } catch {
    return true;
  }
}

export interface SingleKeyShortcuts {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
}

export function useSingleKeyShortcuts(): SingleKeyShortcuts {
  const [enabled, setState] = useState<boolean>(read);
  const setEnabled = useCallback((next: boolean) => {
    setState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next ? 'on' : 'off');
    } catch {
      // storage blocked: the choice holds for this visit
    }
  }, []);
  return useMemo(() => ({ enabled, setEnabled }), [enabled, setEnabled]);
}
