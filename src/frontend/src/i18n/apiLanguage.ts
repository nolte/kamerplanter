/**
 * The two-letter language the backend accepts, derived from the i18n locale.
 *
 * `i18n.language` can be `de`, `en`, `en-GB`, `de-AT`… the API's `language`
 * query parameter is a `Literal['de', 'en']`. The expression
 * `i18n.language.startsWith('en') ? 'en' : 'de'` was copied into a dozen call
 * sites; one helper is one place to change when a third language arrives, and
 * one place to get the default wrong instead of thirteen.
 */
export function apiLanguage(locale: string): 'de' | 'en' {
  return locale.startsWith('en') ? 'en' : 'de';
}
