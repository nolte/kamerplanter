import { describe, it, expect } from 'vitest';
import { deFull as de, enFull as en } from '../i18nTestResources';

/**
 * #2182 review SCR-005 — the invitation strings of the garden settings are complete in both
 * locales, and the plural-only hint has no dead base key.
 *
 * `invitationLinkHint` is only ever looked up with `count` (the link's `max_uses`), so i18next
 * resolves `_one` / `_other` and never the bare key; a bare key next to them is text no screen
 * shows that a translator still keeps in step. The whole `pages.tenants` subtree is compared DE
 * against EN, so a key added to one locale only fails here rather than showing a raw key.
 */

type Tree = Record<string, unknown>;

function tenants(locale: Tree): Tree {
  return (locale as { pages: { tenants: Tree } }).pages.tenants;
}

function enumGroup(locale: Tree, name: string): Record<string, string> {
  return (locale as { enums: Record<string, Record<string, string>> }).enums[name];
}

/** Every leaf path of *tree*, dotted. */
function leaves(tree: Tree, prefix = ''): string[] {
  return Object.entries(tree).flatMap(([key, value]) =>
    value !== null && typeof value === 'object'
      ? leaves(value as Tree, `${prefix}${key}.`)
      : [`${prefix}${key}`],
  );
}

const INVITATION_KEYS = [
  'invitationLinkHint_one',
  'invitationLinkHint_other',
  'linkMaxUses',
  'linkMaxUsesHelper',
  'invitationUses',
  'invitationUsesValue',
  'invitationUsesSubtitle',
  'invitationAcceptLink',
  'revokeInvitation',
] as const;

describe('tenant invitation i18n (#2182)', () => {
  it('has the same pages.tenants keys in DE and EN', () => {
    expect(leaves(tenants(de)).sort()).toEqual(leaves(tenants(en)).sort());
  });

  it.each(INVITATION_KEYS)('has a non-empty DE + EN string for pages.tenants.%s', (key) => {
    expect(String(tenants(de)[key] ?? '').length).toBeGreaterThan(0);
    expect(String(tenants(en)[key] ?? '').length).toBeGreaterThan(0);
  });

  it('keeps no bare invitationLinkHint next to its plural forms', () => {
    expect(tenants(de)).not.toHaveProperty('invitationLinkHint');
    expect(tenants(en)).not.toHaveProperty('invitationLinkHint');
  });

  it.each(['invitationUsesValue', 'invitationUsesSubtitle'])(
    'interpolates used and max in pages.tenants.%s',
    (key) => {
      for (const locale of [de, en]) {
        expect(tenants(locale)[key]).toContain('{{used}}');
        expect(tenants(locale)[key]).toContain('{{max}}');
      }
    },
  );

  it.each(['email', 'link'])('labels the invitation type %s in DE and EN', (type) => {
    expect(enumGroup(de, 'invitationType')[type]?.length).toBeGreaterThan(0);
    expect(enumGroup(en, 'invitationType')[type]?.length).toBeGreaterThan(0);
  });
});
