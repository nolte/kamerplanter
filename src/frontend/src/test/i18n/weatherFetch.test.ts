import { describe, it, expect } from 'vitest';
import { deFull as de, enFull as en } from '../i18nTestResources';

/**
 * F-14 (#2934) — the weather fetch strings of the installation's weather card.
 *
 * acceptance-4: label and helper of the timeout field make clear, in DE and EN,
 * that it limits one request and does not set how often data is fetched. The
 * rest pins DE/EN parity of the new `fetchStatus` / `fetchNow` blocks, so a key
 * added in one language only is caught here rather than rendered as a raw key.
 */

function at(locale: unknown, path: string[]): unknown {
  return path.reduce<unknown>((node, key) => (node as Record<string, unknown> | undefined)?.[key], locale);
}

function keysOf(value: unknown): string[] {
  return Object.keys((value as Record<string, unknown>) ?? {}).sort();
}

const BASE = ['pages', 'weatherProviders'];

describe('weather fetch i18n (F-14)', () => {
  it('acceptance-4: DE labels the timeout per request and points to the fetch interval', () => {
    expect(at(de, [...BASE, 'fetchTimeout'])).toMatch(/pro Anfrage/);
    const helper = at(de, [...BASE, 'fetchTimeoutHelper']) as string;
    expect(helper).toMatch(/höchstens/);
    expect(helper).toMatch(/Abrufintervall/);
    expect(helper).toMatch(/nicht dieses Feld/);
  });

  it('acceptance-4: EN labels the timeout per request and points to the fetch interval', () => {
    expect(at(en, [...BASE, 'fetchTimeout'])).toMatch(/per request/);
    const helper = at(en, [...BASE, 'fetchTimeoutHelper']) as string;
    expect(helper).toMatch(/at most/);
    expect(helper).toMatch(/fetch interval/);
    expect(helper).toMatch(/not by this field/);
  });

  it('names the interval in hours with its lower bound of 6 in both languages', () => {
    expect(at(de, [...BASE, 'fetchIntervalHelper'])).toMatch(/Stunden.*6/);
    expect(at(en, [...BASE, 'fetchIntervalHelper'])).toMatch(/Hours.*6/);
  });

  it.each(['fetchStatus', 'fetchNow'])('carries the same "%s" keys in DE and EN, none empty', (block) => {
    const path = [...BASE, block];
    const deKeys = keysOf(at(de, path));
    expect(deKeys.length).toBeGreaterThan(0);
    expect(deKeys).toEqual(keysOf(at(en, path)));
    for (const key of deKeys) {
      expect(String(at(de, [...path, key])).trim()).not.toBe('');
      expect(String(at(en, [...path, key])).trim()).not.toBe('');
    }
  });

  it('uses the informal "du" in the German refusal texts', () => {
    expect(at(de, [...BASE, 'fetchNow', 'cooldown'])).toMatch(/\bdu\b/);
    expect(JSON.stringify(at(de, [...BASE, 'fetchNow']))).not.toMatch(/\bSie\b/);
  });
});
