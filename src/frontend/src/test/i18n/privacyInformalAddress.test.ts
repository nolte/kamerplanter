import { describe, it, expect } from 'vitest';
import dePages from '@/i18n/locales/de/pages.json';

/**
 * #1845 — the privacy page addresses the user with "du", like the rest of the
 * UI conventions and DOCS.md. It mixed the formal "Sie" (the export, consent,
 * erasure and restriction texts) with the informal erasure dialog.
 *
 * The rule is held for `pages.privacy.*` only: the rest of the German locale
 * still carries formal texts (tracked separately), and a sentence-initial
 * "Sie" can also be the third-person plural ("Sie sehen im Winter schlafend
 * aus" about plants) — which is why this is a list of formal forms, not a
 * search for the bare word elsewhere.
 *
 * Spelling this does not see: a formal imperative without a pronoun ("Bitte
 * bestätigen" is neutral German and allowed) and a formal verb form in a
 * sentence whose pronoun lives in another key.
 */
const FORMAL = /\b(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)\b/;

function strings(node: unknown, path: string): Array<[string, string]> {
  if (typeof node === 'string') return [[path, node]];
  if (node && typeof node === 'object') {
    return Object.entries(node as Record<string, unknown>).flatMap(([key, value]) =>
      strings(value, `${path}.${key}`),
    );
  }
  return [];
}

describe('privacy page (DE) — informal address', () => {
  const privacy = (dePages as { pages: { privacy: unknown } }).pages.privacy;
  const all = strings(privacy, 'pages.privacy');

  it('reads every string of the page', () => {
    expect(all.length).toBeGreaterThan(20);
  });

  it('uses du, never the formal Sie/Ihr', () => {
    const formal = all.filter(([, text]) => FORMAL.test(text)).map(([key, text]) => `${key}: ${text}`);
    expect(formal).toEqual([]);
  });

  it('the detector sees each formal form and passes the informal one', () => {
    for (const text of ['Sie haben', 'über Sie', 'Ihren Status', 'Ihr Konto', 'wenden Sie sich', 'Ihnen']) {
      expect(FORMAL.test(text)).toBe(true);
    }
    for (const text of ['Du hast', 'dein Konto', 'wende dich', 'Bitte bestätigen']) {
      expect(FORMAL.test(text)).toBe(false);
    }
  });
});
