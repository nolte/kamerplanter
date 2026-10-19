/**
 * What field mode remembers per device (REQ-053 GP-UX-030): the tenant and site last used, the tab, and
 * the map viewport per site. `localStorage` only - no account preference, no server round trip.
 *
 * The record names the account it belongs to: on a shared device the next person starts fresh instead
 * of inheriting the previous person's site and view (MT-020 pattern). It holds keys and numbers only;
 * the user's own position (GP-UX-026) is never written here.
 */
import type { Point } from '../model/types';

export type FieldTab = 'list' | 'map';

export interface FieldViewport {
  pxPerM: number;
  originM: Point;
}

export interface FieldPrefs {
  userKey: string;
  tenantSlug: string;
  siteKey: string;
  tab: FieldTab;
  /** Map viewport per site key; bounded to {@link MAX_VIEWPORTS} sites. */
  viewports: Record<string, FieldViewport>;
}

export const FIELD_PREFS_KEY = 'kp-garden-field-mode';
/** A device rarely serves more sites; older views are dropped first. */
export const MAX_VIEWPORTS = 20;

function finite(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function readViewport(value: unknown): FieldViewport | null {
  if (!value || typeof value !== 'object') return null;
  const { pxPerM, originM } = value as { pxPerM?: unknown; originM?: unknown };
  if (!finite(pxPerM) || pxPerM <= 0) return null;
  if (!Array.isArray(originM) || originM.length !== 2 || !finite(originM[0]) || !finite(originM[1])) return null;
  return { pxPerM, originM: [originM[0], originM[1]] };
}

/** The stored record, or `null` when there is none, it is unreadable or it belongs to another account. */
export function readFieldPrefs(userKey: string | null): FieldPrefs | null {
  if (!userKey) return null;
  try {
    const raw = localStorage.getItem(FIELD_PREFS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<FieldPrefs> | null;
    if (!parsed || typeof parsed !== 'object' || parsed.userKey !== userKey) return null;
    if (typeof parsed.tenantSlug !== 'string' || typeof parsed.siteKey !== 'string') return null;
    const viewports: Record<string, FieldViewport> = {};
    for (const [site, value] of Object.entries(parsed.viewports ?? {})) {
      const viewport = readViewport(value);
      if (viewport) viewports[site] = viewport;
    }
    return {
      userKey,
      tenantSlug: parsed.tenantSlug,
      siteKey: parsed.siteKey,
      tab: parsed.tab === 'map' ? 'map' : 'list',
      viewports,
    };
  } catch {
    return null;
  }
}

function store(prefs: FieldPrefs): void {
  try {
    localStorage.setItem(FIELD_PREFS_KEY, JSON.stringify(prefs));
  } catch {
    // Storage unavailable (private mode, quota): field mode works without the memory.
  }
}

/** The record for `context`; another account's or another tenant's record starts empty. */
function baseFor(context: { userKey: string; tenantSlug: string; siteKey: string }): FieldPrefs {
  const current = readFieldPrefs(context.userKey);
  const sameTenant = current !== null && current.tenantSlug === context.tenantSlug;
  return {
    userKey: context.userKey,
    tenantSlug: context.tenantSlug,
    siteKey: context.siteKey,
    tab: sameTenant && current.siteKey === context.siteKey ? current.tab : 'list',
    viewports: sameTenant ? current.viewports : {},
  };
}

/** Remember the site (and the tab) the user works in. */
export function rememberFieldSite(context: {
  userKey: string;
  tenantSlug: string;
  siteKey: string;
  tab?: FieldTab;
}): void {
  const next = baseFor(context);
  store({ ...next, tab: context.tab ?? next.tab });
}

/** Remember the map viewport of a site; the oldest entries fall out past {@link MAX_VIEWPORTS}. */
export function rememberFieldViewport(
  context: { userKey: string; tenantSlug: string; siteKey: string },
  viewport: FieldViewport,
): void {
  const next = baseFor(context);
  const others = Object.entries(next.viewports).filter(([site]) => site !== context.siteKey);
  const kept = others.slice(Math.max(0, others.length - (MAX_VIEWPORTS - 1)));
  store({
    ...next,
    viewports: { ...Object.fromEntries(kept), [context.siteKey]: viewport },
  });
}
