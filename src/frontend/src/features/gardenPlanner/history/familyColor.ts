/**
 * A colour per botanical family for the planting timeline (REQ-053 GP-FR-103). The colour is an aid,
 * never the only carrier: every chip also names the family.
 *
 * Hues are assigned by position in the sorted set of families on the page, in golden-angle steps, so
 * the families of one bed are separated by construction - a hash of the key gave two common families
 * 2 degrees apart. The same set of families gives the same colours on every device; a new family
 * shifts the others, which is why the name always stays on the chip.
 */

const GOLDEN_ANGLE = 137.508;

/** A saturated mid-tone, chosen to stay visible on a light and on a dark surface. */
function colorAt(index: number): string {
  return `hsl(${Math.round((index * GOLDEN_ANGLE) % 360)} 55% 42%)`;
}

/** Family key -> CSS colour for every distinct key; the input order does not matter. */
export function familyColors(familyKeys: readonly string[]): Map<string, string> {
  const distinct = [...new Set(familyKeys)].sort((a, b) => a.localeCompare(b));
  return new Map(distinct.map((key, index) => [key, colorAt(index)]));
}

/** The hue of a colour from {@link familyColors}, for tests and for sorting. */
export function hueOf(color: string): number {
  const match = /^hsl\((\d+) /.exec(color);
  return match ? Number(match[1]) : Number.NaN;
}
