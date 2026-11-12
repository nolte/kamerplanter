import { describe, expect, it } from 'vitest';

/**
 * #2902 — a species name is shown in the UI language, never as "the first entry of
 * `common_names`".
 *
 * `common_names` is a flat, language-mixed list; species.yaml lists the English name
 * first for most species, so a reader that shows its first entry shows English in the
 * German UI. The one sanctioned reader is `getLocalizedCommonName` (and the helpers
 * built on it) in `src/utils/plantDisplay.ts`: UI language -> `de` -> scientific name,
 * and the first list entry only for a species without a language map.
 *
 * Writings of "the first entry" this guard sees:
 *
 *  1. index access — `common_names[0]`, `common_names?.[0]` (also
 *     `species_common_names[0]`)
 *  2. `.at(0)` — `common_names.at(0)`, `common_names?.at(0)`
 *  3. `.find(` on the list — "first name that is non-empty" is the same reader
 *  4. array destructuring — `const [first] = sp.common_names`
 *
 * Known blind spots, deliberately not covered (they need data-flow analysis, not a
 * line scan; nothing in the tree writes them today):
 *  - indirection through a variable — `const names = sp.common_names; names[0]`
 *  - `common_names.slice(0, 1)`, `common_names.filter(...)[0]`, `.shift()`
 *  - a name the SERVER already reduced to its first entry (`common_name` of the
 *    succession recommendation, the print service) — that is the backend's reader
 *    (#2902 slice C), the frontend only formats what it gets
 * Search/filter code (`[...common_names].join(' ')`, `.some(...)`) and the forms
 * (`name="common_names"`) read the whole list and are not display reads.
 */

const SOURCES = import.meta.glob(['/src/**/*.ts', '/src/**/*.tsx', '!/src/**/*.test.ts', '!/src/**/*.test.tsx', '!/src/test/**'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** File -> why a first-entry read there is not a display read. Keep it empty if possible. */
const ALLOWLIST: Record<string, string> = {};

const FIRST_ENTRY_READS: [string, RegExp][] = [
  ['index access', /common_names\s*(?:\?\.)?\s*\[\s*0\s*\]/],
  ['.at(0)', /common_names\s*\??\.\s*at\s*\(\s*0\s*\)/],
  ['.find(', /common_names\s*\??\.\s*find\s*\(/],
  ['destructuring', /(?:const|let|var)\s*\[\s*\w+[^\]]*\]\s*=\s*[\w.?]*common_names\b/],
];

/** Strip comments so the explanation of a fixed reader (like this file's header) is not reported. */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');
}

function firstEntryReads(source: string): string[] {
  const code = stripComments(source);
  return FIRST_ENTRY_READS.filter(([, pattern]) => pattern.test(code)).map(([name]) => name);
}

describe('species common names are shown in the UI language (#2902)', () => {
  it('scans the source tree (the glob is not empty)', () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(100);
    expect(Object.keys(SOURCES)).toContain('/src/utils/plantDisplay.ts');
  });

  it('has no first-entry display read of common_names outside the allowlist', () => {
    const offenders = Object.entries(SOURCES)
      .filter(([file]) => !(file in ALLOWLIST))
      .flatMap(([file, source]) => firstEntryReads(source).map((kind) => `${file}: ${kind}`));
    expect(offenders).toEqual([]);
  });

  it('keeps every allowlisted file real and still reading the first entry', () => {
    for (const file of Object.keys(ALLOWLIST)) {
      expect(SOURCES[file], file).toBeDefined();
      expect(firstEntryReads(SOURCES[file]), file).not.toEqual([]);
    }
  });

  describe('the scan sees every spelling it claims', () => {
    it.each([
      ['sp.common_names[0]'],
      ['sp.common_names?.[0]'],
      ['species?.common_names?.[0] || species?.scientific_name'],
      ['plant.species_common_names[0]'],
      ['s.common_names.at(0)'],
      ['s.common_names?.at(0)'],
      ["cn = option.common_names.find((n) => n.length > 0)"],
      ['const [first] = sp.common_names;'],
      ['const [first, ...rest] = species.common_names ?? [];'],
    ])('reports %s', (code) => {
      expect(firstEntryReads(code)).not.toEqual([]);
    });

    it.each([
      ["[species.scientific_name, ...(species.common_names ?? [])].join(' ')"],
      ["r.common_names.join(', ')"],
      ['names.some((n) => n.includes(q))'],
      ['name="common_names"'],
      ['// a reader used common_names[0] here before #2902'],
      ['/* common_names?.[0] */'],
    ])('does not report %s', (code) => {
      expect(firstEntryReads(code)).toEqual([]);
    });
  });
});
