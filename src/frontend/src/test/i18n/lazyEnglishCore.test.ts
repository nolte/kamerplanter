import { afterEach, describe, expect, it, vi } from 'vitest';
import enCore from '@/i18n/locales/en/core.json';

/**
 * #3023 — the English core translations are not in the initial bundle any more; `initI18n` loads them before the
 * app mounts. For an English user that must still end with English strings, `resolvedLanguage === 'en'` (it drives
 * the API's Accept-Language, `api/client.ts`) and `<html lang="en">` — not with the German fallback that
 * i18next resolves to while the English core is still missing.
 *
 * Re-imports the i18n module fresh, as the app's first load does; the shared test setup registers every bundle
 * synchronously and would hide exactly this path.
 */
describe('i18n start-up with the English core code-split (#3023)', () => {
  afterEach(() => {
    window.localStorage.removeItem('kamerplanter-lang');
  });

  it('starts without the English core, loads it in initI18n and resolves to English', async () => {
    window.localStorage.setItem('kamerplanter-lang', 'en');
    vi.resetModules();
    const { default: i18n, initI18n } = await import('@/i18n/i18n');

    expect(i18n.language).toBe('en');
    expect(i18n.hasResourceBundle('en', 'translation')).toBe(false);

    await initI18n();

    expect(i18n.hasResourceBundle('en', 'translation')).toBe(true);
    expect(i18n.resolvedLanguage).toBe('en');
    expect(document.documentElement.lang).toBe('en');
    expect(i18n.t('common.retry')).toBe(enCore.common.retry);
    expect(i18n.t('common.retry')).not.toBe('');
  });
});
