/**
 * The lazily loaded parts of the kiosk surface, in one place (#3025 M16 review S1).
 *
 * They are code-split so a non-kiosk session never downloads them — but the service worker only
 * precaches the app shell, and a lazy chunk reaches its runtime cache on first use. A kiosk tablet
 * that drops offline before its first destructive dialog would then get a rejected `import()`.
 * The kiosk shell therefore loads all of them as soon as it mounts ({@link preloadKioskChunks}):
 * the module registry keeps them for the session, the worker's `/assets/` cache for the next start.
 */

export const loadLongPressButton = () => import('@/components/kiosk/LongPressButton');
export const loadKioskQuickSelect = () => import('@/components/kiosk/KioskQuickSelect');
export const loadKioskLayout = () => import('@/layouts/KioskLayout');
export const loadKioskStartPage = () => import('@/pages/kiosk/KioskStartPage');

/** Fetch every kiosk chunk now; a failure (already offline) is left to the components' fallbacks. */
export function preloadKioskChunks(): Promise<unknown> {
  return Promise.allSettled([
    loadLongPressButton(),
    loadKioskQuickSelect(),
    loadKioskLayout(),
    loadKioskStartPage(),
  ]);
}
