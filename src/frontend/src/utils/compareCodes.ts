/**
 * Order machine codes — keys, ids, enum values, ISO timestamps — by code unit, the same in
 * every UI language and browser (#3025 M14, audit A-21).
 *
 * `a.localeCompare(b)` ordered them by the browser's locale; for a code that is neither
 * stable nor meaningful (a family's colour index must not change with the language).
 * Human-readable text sorts with `compareText` from `utils/formatting.ts` instead.
 */
export function compareCodes(a: string, b: string): number {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}
