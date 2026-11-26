import { normalizeNameLanguage } from '@/utils/plantDisplay';

/**
 * #3025 M14 (audit A-16) — the one way to pick the text of a record that stores it per
 * language: `name` + `name_de` of a task or activity, `display_name` + `display_name_de`
 * of a phase, `name_de` + `name_en` of a substrate, `description` + `description_de`, …
 *
 * The rule, the same everywhere:
 *   1. the text of the UI language,
 *   2. the text of the other language (a German name is better than a machine name in the
 *      English UI, and vice versa),
 *   3. `fallback` (machine name, brand, …), then ''.
 * Blank strings count as missing. `language` is the UI language (`i18n.language`); it is
 * normalized, so `de-DE` is German, and anything that is not English reads as German, the
 * app's default.
 *
 * Species and IPM catalogue names have their own language map and rule:
 * `getLocalizedCommonName` / `getLocalizedCatalogName` in `utils/plantDisplay.ts`.
 * Guarded by `src/test/guards/localeFormattingHasOneHome.test.ts`.
 */
export interface LocalizedVariants {
  de?: string | null;
  en?: string | null;
}

function nonBlank(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function localizedText(
  language: string | null | undefined,
  variants: LocalizedVariants,
  fallback?: string | null,
): string {
  const english = normalizeNameLanguage(language) === 'en';
  const own = english ? variants.en : variants.de;
  const other = english ? variants.de : variants.en;
  return nonBlank(own) ?? nonBlank(other) ?? nonBlank(fallback) ?? '';
}
