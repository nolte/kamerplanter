import i18n, { markFeatureLocaleLoaded, type SupportedLocale } from '@/i18n/i18n';
import deCore from '@/i18n/locales/de/core.json';
import dePages from '@/i18n/locales/de/pages.json';
import deEnums from '@/i18n/locales/de/enums.json';
import deGlossary from '@/i18n/locales/de/glossary.json';
import enCore from '@/i18n/locales/en/core.json';
import enPages from '@/i18n/locales/en/pages.json';
import enEnums from '@/i18n/locales/en/enums.json';
import enGlossary from '@/i18n/locales/en/glossary.json';

/**
 * #612 — in the app the feature namespaces (`pages`, `enums`, `glossary`) are
 * code-split and dynamically imported on demand. Tests render synchronously and
 * assert on translated text, so they need every key resolvable up front. This
 * helper registers all feature bundles synchronously and marks the locales as
 * loaded, which also prevents the `languageChanged` listener from firing a
 * dynamic import (and an out-of-`act` re-render) when a test switches language.
 */
export function loadFeatureNamespacesForTests(): void {
  const bundles: Record<SupportedLocale, ReadonlyArray<Record<string, unknown>>> = {
    de: [dePages, deEnums, deGlossary],
    en: [enPages, enEnums, enGlossary],
  };
  for (const locale of ['de', 'en'] as const) {
    for (const bundle of bundles[locale]) {
      i18n.addResourceBundle(locale, 'translation', bundle, true, true);
    }
    markFeatureLocaleLoaded(locale);
  }
}

/** Fully merged translation objects (core + features) for DE/EN parity tests. */
export const deFull: Record<string, unknown> = {
  ...deCore,
  ...dePages,
  ...deEnums,
  ...deGlossary,
};

export const enFull: Record<string, unknown> = {
  ...enCore,
  ...enPages,
  ...enEnums,
  ...enGlossary,
};
