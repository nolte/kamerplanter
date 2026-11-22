import { describe, expect, it } from 'vitest';

/**
 * #3016 — a calendar day is made in one place, and the caller says which calendar it means.
 *
 * `new Date().toISOString().split('T')[0]` and `.slice(0, 10)` read like "today" but are the **UTC** day:
 * between 00:00 and 02:00 CEST they pre-filled `planted_on`, `purchase_date`, `mixed_on` and a run's start
 * with yesterday. Where UTC *is* meant (mirroring a server rule) the expression does not say so either.
 *
 * **The rule.** Production code turns an instant into a `YYYY-MM-DD` day only through
 * `@/utils/calendarDay` — `toLocalIsoDate` for a day the user enters, `toUtcIsoDate`/`utcDayOf` for the
 * server's clock. Cutting the date off `toISOString()` (`.split('T')[0]`, `.slice(0, 10)`,
 * `.substring(0, 10)`, `.substr(0, 10)`) is refused everywhere, the helper included (it formats from the
 * date fields). A full timestamp (`toISOString()` alone, or `.slice(0, 16)` for a `datetime-local` value)
 * is not a calendar day and is out of scope.
 *
 * The detector is exercised against fixtures in both directions at the end of this file.
 */

const SOURCES = import.meta.glob(['/src/**/*.ts', '/src/**/*.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function isProductionSource(path: string): boolean {
  return (
    !/\.(test|spec)\.tsx?$/.test(path) &&
    !path.endsWith('.d.ts') &&
    !path.startsWith('/src/test/') &&
    !path.includes('/__mocks__/')
  );
}

/** `toISOString()` followed (across whitespace/newlines) by a cut to the date part. */
const DATE_CUT =
  /\.toISOString\(\)\s*\.\s*(?:split\(\s*['"`]T['"`]\s*\)\s*\[\s*0\s*\]|(?:slice|substring|substr)\(\s*0\s*,\s*10\s*\))/g;

function dateCuts(source: string): string[] {
  return [...source.matchAll(DATE_CUT)].map((match) => {
    const line = source.slice(0, match.index).split('\n').length;
    return `${line}: ${match[0].replace(/\s+/g, ' ')}`;
  });
}

describe('calendar days come from @/utils/calendarDay (#3016)', () => {
  it('scans a realistic number of production sources (the glob is not empty)', () => {
    const production = Object.keys(SOURCES).filter(isProductionSource);
    expect(production.length).toBeGreaterThan(200);
    expect(production).toContain('/src/utils/calendarDay.ts');
  });

  it('no production source cuts a calendar day off toISOString()', () => {
    const offenders = Object.entries(SOURCES)
      .filter(([path]) => isProductionSource(path))
      .flatMap(([path, source]) => dateCuts(source).map((hit) => `${path}:${hit}`));
    expect(offenders).toEqual([]);
  });

  describe('detector', () => {
    it.each([
      "const d = new Date().toISOString().split('T')[0];",
      'const d = new Date().toISOString().split("T")[0];',
      'const d = now.toISOString().slice(0, 10);',
      'const d = now.toISOString().substring(0,10);',
      'const d = now.toISOString().substr(0, 10);',
      'const d = now\n  .toISOString()\n  .slice(0, 10);',
    ])('flags %j', (snippet) => {
      expect(dateCuts(snippet)).toHaveLength(1);
    });

    it.each([
      'const stamp = new Date().toISOString();',
      'const local = new Date().toISOString().slice(0, 16);',
      'const day = toLocalIsoDate();',
      "const due = value.slice(0, 10) < toUtcIsoDate();",
      "const [day] = value.split('T');",
    ])('leaves %j alone', (snippet) => {
      expect(dateCuts(snippet)).toEqual([]);
    });
  });
});
