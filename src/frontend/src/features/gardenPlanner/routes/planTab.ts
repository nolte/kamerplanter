/**
 * Which tab of the planning mode is open (REQ-053 §17.3, GP-UX-064): `?tab=plan|list|beds`, next to `?mode=`.
 * A missing or unknown value is the plan; field mode ignores the parameter. Pure.
 */
export const PLAN_TABS = ['plan', 'list', 'beds'] as const;

export type PlanTab = (typeof PLAN_TABS)[number];

/** The query parameter that carries the tab. */
export const PLAN_TAB_PARAM = 'tab';

export function resolvePlanTab(param: string | null): PlanTab {
  return (PLAN_TABS as readonly string[]).includes(param ?? '') ? (param as PlanTab) : 'plan';
}

/** The same query with `tab` set, every other parameter (`mode`, ...) kept. */
export function planTabSearch(search: URLSearchParams, tab: PlanTab): URLSearchParams {
  const next = new URLSearchParams(search);
  next.set(PLAN_TAB_PARAM, tab);
  return next;
}

interface LocationLike {
  pathname: string;
  search: string;
  hash: string;
}

function withoutTab(search: string): string {
  const params = new URLSearchParams(search);
  params.delete(PLAN_TAB_PARAM);
  params.sort();
  return params.toString();
}

/**
 * Whether a navigation only switches the tab (GP-UX-065): same path, same hash, the same query apart from `tab`.
 * Such a move keeps the editor mounted, so the unsaved-changes guard lets it through; anything else (another
 * route, `mode=field`) still asks.
 */
export function isTabOnlyChange(current: LocationLike, next: LocationLike): boolean {
  return (
    current.pathname === next.pathname &&
    current.hash === next.hash &&
    withoutTab(current.search) === withoutTab(next.search)
  );
}
