/**
 * Which mode the garden plan page opens in (REQ-053 GP-UX-020): `?mode=field` and `?mode=plan` decide;
 * without the parameter, field mode is the default on xs (< 600 px) and planning mode elsewhere. Pure.
 */
export type PlanMode = 'field' | 'plan';

export function resolvePlanMode(param: string | null, narrow: boolean): PlanMode {
  if (param === 'field') return 'field';
  if (param === 'plan') return 'plan';
  return narrow ? 'field' : 'plan';
}

/** The same page in `mode`, keeping every other query parameter. */
export function planModeHref(pathname: string, search: URLSearchParams, mode: PlanMode): string {
  const next = new URLSearchParams(search);
  next.set('mode', mode);
  return `${pathname}?${next.toString()}`;
}
