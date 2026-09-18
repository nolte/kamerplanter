import { describe, it, expect } from 'vitest';
import { apiLanguage } from '@/i18n/apiLanguage';

/**
 * The helper that replaced a copied ternary (review SCR-014). It is tiny, and
 * the reason it is tested is the regional-locale case: `en-GB` is the one every
 * hand-written copy would have to remember, and the one a naive `=== 'en'`
 * silently answers `de` for.
 */
describe('apiLanguage', () => {
  it('maps every English locale to en', () => {
    expect(apiLanguage('en')).toBe('en');
    expect(apiLanguage('en-GB')).toBe('en');
    expect(apiLanguage('en-US')).toBe('en');
  });

  it('maps everything else to the de default', () => {
    expect(apiLanguage('de')).toBe('de');
    expect(apiLanguage('de-AT')).toBe('de');
    expect(apiLanguage('fr')).toBe('de');
    expect(apiLanguage('')).toBe('de');
  });
});
