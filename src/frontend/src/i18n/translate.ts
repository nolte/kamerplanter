/**
 * The translation function as a plain helper needs it: a key, optionally with interpolation
 * options, returning the translated string.
 *
 * Two call signatures instead of one with an optional `options` parameter: since i18next 27 the
 * non-strict `TFunction` takes its arguments as a union of tuples, and a single signature with an
 * optional second parameter fits none of those tuples on its own, so `useTranslation().t` was no
 * longer assignable to it. Each signature here matches one tuple, which keeps `t` assignable on
 * i18next 26 and 27, and a test double such as `(key, options?) => key` still satisfies both.
 */
export interface Translate {
  (key: string): string;
  (key: string, options: Record<string, unknown>): string;
}
