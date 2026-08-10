import { describe, it, expect } from 'vitest';
import { deFull as de, enFull as en } from '../i18nTestResources';

/**
 * #1091 A-7 — DE/EN parity for the read-only explanation that replaces the
 * species/cultivar create call to action when the active tenant's role may not
 * create (SEC-005/#1113).
 *
 * The string is the *only* thing a read-only member is left with once the button
 * is hidden, so a missing locale would silently turn the empty state back into a
 * bare "no data" for that language — the failure would look like nothing at all.
 */

function pages(locale: unknown): Record<string, Record<string, string>> {
  return (locale as { pages: Record<string, Record<string, string>> }).pages;
}

describe('catalogue create-denied i18n parity', () => {
  it.each(['species', 'cultivars'] as const)(
    'has a non-empty DE + EN string for pages.%s.createDenied',
    (section) => {
      expect(pages(de)[section]?.createDenied?.length).toBeGreaterThan(0);
      expect(pages(en)[section]?.createDenied?.length).toBeGreaterThan(0);
    },
  );

  it.each(['species', 'cultivars'] as const)(
    'keeps the DE and EN wording distinct for pages.%s.createDenied',
    (section) => {
      // Copying the German sentence into the English bundle would satisfy a plain
      // presence check; it must not satisfy this one.
      expect(pages(de)[section].createDenied).not.toBe(pages(en)[section].createDenied);
    },
  );
});
