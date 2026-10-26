/**
 * Auto-save (REQ-053 GP-UX-004, SHOULD): saves two seconds after the last edit, when the user has switched it on.
 * The choice is a per-user option kept in localStorage - off by default, because an explicit save plus the
 * revision check is explainable and a silent save that meets a 409 is not (D-12). It pauses on its own while a
 * conflict stands or a refusal is shown (`selectAutoSaveReady`). Field mode has no dirty state and no save bar,
 * so it never mounts this.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  saveGardenPlan,
  selectAutoSaveReady,
  selectGardenPlanState,
} from '../state/gardenPlanSlice';

export const AUTO_SAVE_DELAY_MS = 2000;
export const AUTO_SAVE_STORAGE_KEY = 'kp_garden_plan_auto_save';

function read(): boolean {
  try {
    return window.localStorage.getItem(AUTO_SAVE_STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

export interface AutoSave {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
  /** Switched on, but held back by a conflict or a refused save. */
  paused: boolean;
}

export function useAutoSave(): AutoSave {
  const dispatch = useAppDispatch();
  const [enabled, setEnabledState] = useState<boolean>(read);
  const ready = useAppSelector(selectAutoSaveReady);
  // A new edit is a new `pending` list: the timer starts over, so the save follows two quiet seconds.
  const pending = useAppSelector((state) => selectGardenPlanState(state).pending);
  const { saveStatus } = useAppSelector(selectGardenPlanState);

  useEffect(() => {
    if (!enabled || !ready) return undefined;
    const timer = window.setTimeout(() => void dispatch(saveGardenPlan()), AUTO_SAVE_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [dispatch, enabled, pending, ready]);

  const setEnabled = useCallback((next: boolean) => {
    setEnabledState(next);
    try {
      window.localStorage.setItem(AUTO_SAVE_STORAGE_KEY, next ? '1' : '0');
    } catch {
      /* private mode or blocked storage: the choice lasts for this visit */
    }
  }, []);

  const paused = enabled && (saveStatus === 'conflict' || saveStatus === 'error');
  return useMemo(() => ({ enabled, setEnabled, paused }), [enabled, paused, setEnabled]);
}
