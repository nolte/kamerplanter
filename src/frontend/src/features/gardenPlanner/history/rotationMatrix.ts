/**
 * Pure helpers of the rotation matrix (REQ-053 GP-FR-135): how a family is marked and how the pages of the
 * matrix merge. Colour alone must not carry the family (greyscale print, colour-blind users, GP-UX): every
 * family gets a short code and a fill pattern next to its colour, assigned by position in the sorted set of
 * the families on the page.
 */
import { colorAt } from './familyColor';
import type { RotationMatrix, RotationMatrixBed } from './historyTypes';

/** Fill patterns, light-on-dark independent: each is a CSS `background-image` over the family colour. */
export const FAMILY_PATTERNS: readonly string[] = [
  'none',
  'repeating-linear-gradient(45deg, rgba(255,255,255,0.55) 0 2px, transparent 2px 6px)',
  'radial-gradient(rgba(255,255,255,0.7) 1.5px, transparent 1.6px)',
  'repeating-linear-gradient(0deg, rgba(255,255,255,0.55) 0 2px, transparent 2px 6px)',
  'repeating-linear-gradient(135deg, rgba(255,255,255,0.55) 0 2px, transparent 2px 6px)',
  'repeating-linear-gradient(90deg, rgba(255,255,255,0.55) 0 2px, transparent 2px 6px)',
  'repeating-linear-gradient(45deg, rgba(255,255,255,0.55) 0 2px, transparent 2px 6px), repeating-linear-gradient(135deg, rgba(255,255,255,0.55) 0 2px, transparent 2px 6px)',
  'radial-gradient(rgba(0,0,0,0.45) 1.5px, transparent 1.6px)',
];

export interface FamilyMark {
  familyKey: string;
  /** The family's name; never its key. Falls back to the key only when no name exists. */
  name: string;
  /** Two or three letters, unique among the families of the matrix. */
  code: string;
  color: string;
  /** Index into {@link FAMILY_PATTERNS}. */
  pattern: number;
}

/** The letters of a family name without spaces and punctuation, upper-cased in the first position. */
function letters(name: string): string {
  const clean = name.replace(/[^\p{L}]/gu, '');
  return clean.length > 0 ? clean[0].toUpperCase() + clean.slice(1).toLowerCase() : '?';
}

/** The shortest prefix (from 2 letters) of each name that no other name shares; equal names get a number. */
function uniqueCodes(names: readonly string[]): string[] {
  const words = names.map(letters);
  const used = new Set<string>();
  return words.map((word) => {
    let length = 2;
    let code = word.slice(0, length);
    while (used.has(code) && length < word.length) {
      length += 1;
      code = word.slice(0, length);
    }
    let suffix = 2;
    const base = code;
    while (used.has(code)) {
      code = `${base}${suffix}`;
      suffix += 1;
    }
    used.add(code);
    return code;
  });
}

/**
 * A mark per distinct family of the beds. `known` is the order the page has already shown: those families keep
 * their position (and with it colour, pattern and code) when a further page brings new families, which come after
 * them in sorted order. The same sequence of pages gives the same marks on every device; the legend always names
 * the families.
 */
export function familyMarks(beds: readonly RotationMatrixBed[], known: readonly string[] = []): Map<string, FamilyMark> {
  const names = new Map<string, string>();
  for (const bed of beds) {
    for (const cell of bed.cells) {
      for (const planting of cell.plantings) {
        if (planting.family_key && !names.has(planting.family_key)) {
          names.set(planting.family_key, planting.family_name ?? planting.family_key);
        }
      }
    }
  }
  const shown = known.filter((key) => names.has(key));
  const fresh = [...names.keys()].filter((key) => !shown.includes(key)).sort((a, b) => a.localeCompare(b));
  const keys = [...shown, ...fresh];
  const codes = uniqueCodes(keys.map((key) => names.get(key) ?? key));
  return new Map(
    keys.map((key, index) => [
      key,
      {
        familyKey: key,
        name: names.get(key) ?? key,
        code: codes[index],
        color: colorAt(index),
        pattern: index % FAMILY_PATTERNS.length,
      },
    ]),
  );
}

/**
 * Append the next page of beds to the matrix. The columns, the look-back and the totals of the first page stay
 * (a later page must have been asked with the first page's `years`); a bed already listed is not repeated.
 */
export function mergeMatrixPage(current: RotationMatrix | null, next: RotationMatrix): RotationMatrix {
  if (current === null) return next;
  const seen = new Set(current.beds.map((bed) => bed.location_key));
  return {
    ...current,
    total: next.total,
    truncated: next.truncated,
    offset: next.offset,
    beds: [...current.beds, ...next.beds.filter((bed) => !seen.has(bed.location_key))],
  };
}

/** Whether another page can be asked: fewer beds are loaded than the matrix reads. */
export function hasMoreBeds(matrix: RotationMatrix): boolean {
  return matrix.beds.length < matrix.total;
}
