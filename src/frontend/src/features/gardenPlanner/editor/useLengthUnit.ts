import { useCallback, useMemo, useState } from 'react';
import { isLengthUnit, type LengthUnit } from '../model/units';

/** User-level display choice, like `module_visibility` (GP-FR-004): never changes stored values. */
const STORAGE_KEY = 'kp_garden_plan_length_unit';

function read(): LengthUnit {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return isLengthUnit(stored) ? stored : 'm';
  } catch {
    return 'm';
  }
}

export function useLengthUnit(): readonly [LengthUnit, (unit: LengthUnit) => void] {
  const [unit, setUnitState] = useState<LengthUnit>(read);
  const setUnit = useCallback((next: LengthUnit) => {
    setUnitState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* private mode or blocked storage: the choice lasts for this visit */
    }
  }, []);
  return useMemo(() => [unit, setUnit] as const, [unit, setUnit]);
}
