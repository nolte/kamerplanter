import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import deCore from './locales/de/core.json';
import enCore from './locales/en/core.json';

/**
 * #612 — lazy-loaded translations (UI-NFR-003 R-013/R-015).
 *
 * The translation payload is the dominant cost of the initial JS bundle. To keep
 * it out of the entry chunk we split each locale into:
 *   - `core`    — shell/nav/common/errors and other small namespaces that the
 *                 app shell needs immediately. Statically imported for both
 *                 locales (tiny, ~8 KB gzip each) so they ship in the initial
 *                 bundle and are always synchronously available.
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
      en: { translation: enCore },
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
  void loadFeatureNamespaces(toSupportedLocale(lng)).catch(() => undefined);
});

/**
 * Load every feature namespace required for the first paint: the active locale
 * plus the German fallback. Awaited by `main.tsx` before the app mounts so the
 * initial render already has all translations — the graceful load boundary that
 * prevents a flash of untranslated content.
 */
export async function initI18n(): Promise<typeof i18n> {
  const active = toSupportedLocale(i18n.resolvedLanguage ?? i18n.language);
  await loadFeatureNamespaces(active);
  if (active !== 'de') {
    // German is the fallback locale — load it too so any key missing from the
    // active locale still resolves instead of rendering the raw key.
    await loadFeatureNamespaces('de');
  }
  return i18n;
}

if (import.meta.hot) {
  // Live-reload the split translation files during development.
  import.meta.hot.accept(
    ['./locales/de/core.json', './locales/en/core.json'],
    ([deModule, enModule]) => {
      if (deModule) i18n.addResourceBundle('de', 'translation', deModule.default, true, true);
      if (enModule) i18n.addResourceBundle('en', 'translation', enModule.default, true, true);
    },
  );
}

export default i18n;
