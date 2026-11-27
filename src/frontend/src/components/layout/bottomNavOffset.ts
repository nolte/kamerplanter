/** Height of the phone's bottom navigation without the safe-area inset (MUI's own BottomNavigation height). */
export const BOTTOM_NAV_HEIGHT = 56;

/**
 * The space the bottom navigation takes from the bottom edge of the viewport, as a CSS custom property
 * (UI-NFR-005 R-031, #3018). `MobileBottomNav` sets it on `:root` only while the bar is mounted, so everything
 * that has to clear the bar — the page's bottom padding, a pinned form action row, snackbars, the consent
 * banner — reads one value and keeps its old position without the bar. A module of its own so those readers
 * do not import the bar.
 */
export const BOTTOM_NAV_OFFSET = '--kp-bottom-nav-offset';

/**
 * The offset in pixels as the browser resolves it right now (bar height plus safe-area inset), 0 without the
 * bar. For a layout that sizes itself in script against `window.innerHeight` — CSS can use the property
 * directly. Resolved through a probe element because a custom property's computed value stays the unresolved
 * `calc(… env(…))` text.
 */
export function bottomNavOffsetPx(): number {
  if (typeof document === 'undefined' || !document.body) return 0;
  const probe = document.createElement('div');
  probe.style.cssText = `position:fixed;visibility:hidden;pointer-events:none;height:var(${BOTTOM_NAV_OFFSET}, 0px)`;
  document.body.appendChild(probe);
  const height = probe.getBoundingClientRect().height;
  probe.remove();
  return Number.isFinite(height) && height > 0 ? height : 0;
}
