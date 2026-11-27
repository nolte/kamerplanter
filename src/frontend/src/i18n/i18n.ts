import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import deCore from './locales/de/core.json';
import { configureZodErrorMap } from '@/validation/zodErrorMap';

/**
 * #612 — lazy-loaded translations (UI-NFR-003 R-013/R-015).
 *
 * The translation payload is the dominant cost of the initial JS bundle. To keep
 * it out of the entry chunk we split each locale into:
 *   - `core`    — shell/nav/common/errors and other small namespaces that the
 *                 app shell needs immediately. Only the German core (the
 *                 fallback locale) is statically imported and ships in the
 *                 initial bundle, so a key always resolves synchronously. The
 *                 core of every other locale (~15 KB gzip) is loaded with that
 *                 locale's feature bundles (#3023) — awaited before mount, like them.
 *                 Keys only a page or a lazy dialog reads (dashboard, settings tabs,
 *                 print, diagnosis, AI, …) live in `pages.json` instead (#3018).
 *   - features  — `pages`, `enums`, `glossary` — the bulk of the payload. These
 *                 are dynamically imported per locale (separate chunks, excluded
 *                 from the initial JS budget) and awaited before the app mounts
 *                 so no untranslated content is ever painted (no FOUC).
 *
 * All namespaces are merged into the single `translation` namespace via
 * {@link i18n.addResourceBundle}, so every consumer keeps using the existing
 * dotted keys unchanged (`t('pages.<section>.<key>')`, `t('enums.<name>...')`).
 */

export const SUPPORTED_LOCALES = ['de', 'en'] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      de: { translation: deCore },
    },
    fallbackLng: 'de',
    supportedLngs: [...SUPPORTED_LOCALES],
    load: 'languageOnly',
    // Resources are provided synchronously (core inline, features awaited before
    // mount), so initialise synchronously — the instance is ready on first render.
    initAsync: false,
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'kamerplanter-lang',
    },
    react: {
      // We gate the first render on the feature bundles ourselves (see initI18n),
      // so react-i18next must not suspend on missing namespaces.
      useSuspense: false,
    },
  });

// #1016 — route every zod built-in constraint message through i18next so a bare
// constraint can never render an English default in the German UI. Registered
// here (rather than in main.tsx) so the map is active in the test environment
// too, which imports `@/i18n` but not `main.tsx`.
configureZodErrorMap();

type FeatureBundle = { default: Record<string, unknown> };

/**
 * Dynamic-import loaders for the heavy feature namespaces, per locale. Each
 * `import()` becomes its own chunk that Vite excludes from the initial payload.
 */
const featureLoaders: Record<SupportedLocale, Array<() => Promise<FeatureBundle>>> = {
  de: [
    () => import('./locales/de/pages.json'),
    () => import('./locales/de/enums.json'),
    () => import('./locales/de/glossary.json'),
  ],
  en: [
    // #3023 — the English core is not in the initial bundle; it arrives with the feature namespaces.
    () => import('./locales/en/core.json'),
    () => import('./locales/en/pages.json'),
    () => import('./locales/en/enums.json'),
    () => import('./locales/en/glossary.json'),
  ],
};

const loadedFeatureLocales = new Set<SupportedLocale>();

/** Narrow an arbitrary i18next language tag (e.g. `de-DE`) to a supported locale. */
function toSupportedLocale(lng: string | undefined): SupportedLocale {
  const base = (lng ?? 'de').split('-')[0];
  return (SUPPORTED_LOCALES as readonly string[]).includes(base)
    ? (base as SupportedLocale)
    : 'de';
}

/**
 * Load and register the feature namespaces (`pages`, `enums`, `glossary`) for a
 * locale. Idempotent: a locale is fetched at most once. On failure the locale is
 * un-marked so a later attempt (e.g. a retry or language switch) can try again.
 */
export async function loadFeatureNamespaces(locale: SupportedLocale): Promise<void> {
  if (loadedFeatureLocales.has(locale)) return;
  loadedFeatureLocales.add(locale);
  try {
    const bundles = await Promise.all(featureLoaders[locale].map((load) => load()));
    for (const bundle of bundles) {
      i18n.addResourceBundle(locale, 'translation', bundle.default, true, true);
    }
  } catch (error) {
    loadedFeatureLocales.delete(locale);
    throw error;
  }
  // i18next resolves the active language against the resources present: while the active locale's
  // core was still loading, `resolvedLanguage` fell back to German (it drives the API's
  // Accept-Language). Re-resolve now that the locale has strings of its own.
  if (toSupportedLocale(i18n.language) === locale && i18n.resolvedLanguage !== locale) {
    await i18n.changeLanguage(i18n.language);
  }
}

/**
 * Mark a locale's feature namespaces as already present, bypassing the dynamic
 * import. Used by the test setup, which registers the split bundles synchronously
 * so `t()` resolves every key without awaiting a code-split chunk.
 */
export function markFeatureLocaleLoaded(locale: SupportedLocale): void {
  loadedFeatureLocales.add(locale);
}

// Keep feature namespaces in sync with the active language: when the user
// switches locale, load that locale's bundles on demand. Fire-and-forget — the
// LanguageSelector preloads on menu open, so the switch itself stays instant.
i18n.on('languageChanged', (lng) => {
  syncDocumentLang(lng);
  void loadFeatureNamespaces(toSupportedLocale(lng)).catch((err: unknown) => {
    // The core strings are loaded; a missing feature chunk falls back until the next load.
    // console, not captureHandledError: this module loads before error tracking and must not import it.
    console.warn('[i18n] feature namespaces failed to load', err);
  });
});

/**
 * Mirror the active language onto `<html lang>` (language part only, e.g. `de`)
 * so screen readers pick the right pronunciation and the browser offers the
 * right hyphenation / translation behaviour (WCAG 3.1.1).
 */
function syncDocumentLang(lng: string | undefined): void {
  if (typeof document === 'undefined') return;
  document.documentElement.lang = toSupportedLocale(lng);
}

// The instance initialises synchronously (`initAsync: false`), so the detected
// language is already known here — set the initial `<html lang>` once. `language`,
// not `resolvedLanguage`: the latter is German until a non-German core is loaded.
syncDocumentLang(i18n.language);

/**
 * Load every feature namespace required for the first paint: the active locale
 * plus the German fallback. Awaited by `main.tsx` before the app mounts so the
 * initial render already has all translations — the graceful load boundary that
 * prevents a flash of untranslated content.
 */
export async function initI18n(): Promise<typeof i18n> {
  // The detected language, not `resolvedLanguage` — that one reads German until the active core is loaded (#3023).
  const active = toSupportedLocale(i18n.language);
  await loadFeatureNamespaces(active);
  if (active !== 'de') {
    // German is the fallback locale — load it too so any key missing from the
    // active locale still resolves instead of rendering the raw key.
    await loadFeatureNamespaces('de');
  }
  return i18n;
}

if (import.meta.hot) {
  // Live-reload the statically imported German core; the other locales are dynamic imports.
  import.meta.hot.accept('./locales/de/core.json', (deModule) => {
    if (deModule) i18n.addResourceBundle('de', 'translation', deModule.default, true, true);
  });
}

export default i18n;
