import { describe, it, expect } from 'vitest';
import { deFull as de, enFull as en } from '../i18nTestResources';

/**
 * F-12 (#2935) — DE/EN parity for the platform admin hub `/admin/platform`: the
 * sidebar entry, the page title and intro, and the back links of the admin pages
 * that now lead to it instead of to the settings page.
 */

type Tree = Record<string, unknown>;

function get(tree: Tree, path: string): unknown {
  return path.split('.').reduce<unknown>((node, key) => (node as Tree | undefined)?.[key], tree);
}

const KEYS = [
  'nav.platformAdmin',
  'pages.adminPlatform.title',
  'pages.adminPlatform.intro',
  'pages.adminPlatform.back',
  'pages.plans.back',
  'pages.tenantImports.back',
  'pages.admin.oidc.back',
] as const;

describe('platform admin hub i18n parity (F-12)', () => {
  it.each(KEYS)('has a non-empty, distinct DE + EN string for %s', (key) => {
    const deValue = get(de, key);
    const enValue = get(en, key);
    expect(typeof deValue === 'string' && deValue.length > 0).toBe(true);
    expect(typeof enValue === 'string' && enValue.length > 0).toBe(true);
    expect(deValue).not.toBe(enValue);
  });

  it.each(['pages.plans.back', 'pages.tenantImports.back', 'pages.admin.oidc.back'])(
    'names the hub, not the old settings location, in %s',
    (key) => {
      expect(get(de, key)).toBe(get(de, 'pages.adminPlatform.back'));
      expect(get(en, key)).toBe(get(en, 'pages.adminPlatform.back'));
    },
  );

  it('drops the label of the removed settings tab', () => {
    expect(get(de, 'pages.auth.tabPlatform')).toBeUndefined();
    expect(get(en, 'pages.auth.tabPlatform')).toBeUndefined();
  });
});
