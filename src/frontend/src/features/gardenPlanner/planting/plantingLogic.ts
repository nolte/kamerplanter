/**
 * Pure rules of the planting dialog (REQ-053 WP 3.6): prefill order (GP-FR-061, F-11), the form to
 * layout fields, alternating rows of mixed cultures (GP-FR-070), the yellow ring of freely placed
 * positions (GP-FR-072), the container volume warning (W-016.5), run naming and the id prefix.
 *
 * The layout itself is `model/layout.ts` (the port of the Python reference, tested against the shared
 * vectors); nothing here recomputes a position.
 */
import type { Species } from '@/api/types';
import {
  MAX_SPACING_CM,
  MIN_SPACING_CM,
  SPACING_TOLERANCE_M,
  type EntryLayout,
  type LayoutStrategy,
  type RowDirection,
} from '../model/layout';
import type { Point } from '../model/types';
import type { PreviewEntry, RotationSeverity } from './plantingTypes';

/** Strategies that lay out counted plants in rows; only these alternate (GP-FR-070). */
export const ROW_STRATEGIES: readonly LayoutStrategy[] = ['grid', 'rows', 'triangular'];
export const LAYOUT_STRATEGIES: readonly LayoutStrategy[] = [
  'grid',
  'rows',
  'triangular',
  'zone',
  'free',
];
export const MAX_ENTRIES = 4;

/** A field that is empty or malformed has no value; the lower bound of a range ("60-80") is the value. */
export function parseLowerBound(value: string | number | null | undefined): number | null {
  if (typeof value === 'number') return Number.isFinite(value) && value > 0 ? value : null;
  if (typeof value !== 'string') return null;
  const match = /^\s*(\d+(?:[.,]\d+)?)/.exec(value);
  if (!match) return null;
  const parsed = Number(match[1].replace(',', '.'));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

// ── Prefill: Steckbrief → last used → empty with a hint ─────────────────────

export type PrefillSource = 'species' | 'lastUsed' | 'none';

export interface LastUsedSpacing {
  spacing_cm?: number;
  row_spacing_cm?: number;
  layout_strategy?: LayoutStrategy;
}

export interface Prefill {
  spacing: string;
  rowSpacing: string;
  spacingSource: PrefillSource;
  rowSpacingSource: PrefillSource;
  layout: LayoutStrategy | null;
}

function asText(value: number | null): string {
  return value === null ? '' : String(value);
}

/**
 * Where a spacing comes from, in the order of GP-FR-061: the Steckbrief (`spacing_cm`,
 * `row_spacing_cm`), else what this tenant used last for the species, else nothing - there is no
 * silent default (E-10); the dialog says that the field is empty.
 */
export function prefillFor(species: Species | null, lastUsed: LastUsedSpacing | null): Prefill {
  const fromSpecies = parseLowerBound(species?.spacing_cm);
  const rowFromSpecies = parseLowerBound(species?.row_spacing_cm);
  const fromLast = lastUsed?.spacing_cm ?? null;
  const rowFromLast = lastUsed?.row_spacing_cm ?? null;
  return {
    spacing: asText(fromSpecies ?? fromLast),
    rowSpacing: asText(rowFromSpecies ?? rowFromLast),
    spacingSource: fromSpecies !== null ? 'species' : fromLast !== null ? 'lastUsed' : 'none',
    rowSpacingSource: rowFromSpecies !== null ? 'species' : rowFromLast !== null ? 'lastUsed' : 'none',
    layout: lastUsed?.layout_strategy ?? null,
  };
}

// ── The entry form ──────────────────────────────────────────────────────────

export type CountMode = 'max' | 'number';

export interface EntryFormState {
  /** Local id (React key and the owner of free points); never sent. */
  id: string;
  speciesKey: string | null;
  cultivarKey: string | null;
  countMode: CountMode;
  count: string;
  layout: LayoutStrategy;
  spacing: string;
  rowSpacing: string;
  rowDirection: RowDirection;
  edgeAlong: string;
  edgeAcross: string;
  containerVolume: string;
  /** Freely placed positions (`layout = free`), bed frame, metres. */
  freePoints: Point[];
}

export function emptyEntry(id: string): EntryFormState {
  return {
    id,
    speciesKey: null,
    cultivarKey: null,
    countMode: 'max',
    count: '',
    layout: 'grid',
    spacing: '',
    rowSpacing: '',
    rowDirection: 'along_length',
    edgeAlong: '',
    edgeAcross: '',
    containerVolume: '',
    freePoints: [],
  };
}

function numberOrNull(text: string): number | null {
  const trimmed = text.trim().replace(',', '.');
  if (trimmed === '') return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

export type EntryErrorCode =
  | 'speciesRequired'
  | 'spacingRequired'
  | 'spacingRange'
  | 'rowSpacingRequired'
  | 'rowSpacingRange'
  | 'countRequired'
  | 'marginRange'
  | 'noPoints';

export interface EntryErrors {
  species?: EntryErrorCode;
  spacing?: EntryErrorCode;
  rowSpacing?: EntryErrorCode;
  count?: EntryErrorCode;
  edgeAlong?: EntryErrorCode;
  edgeAcross?: EntryErrorCode;
  points?: EntryErrorCode;
}

const MAX_MARGIN_CM = 200;
const MAX_COUNT = 2000;

export function validateEntry(form: EntryFormState): EntryErrors {
  const errors: EntryErrors = {};
  if (!form.speciesKey) errors.species = 'speciesRequired';
  const spacing = numberOrNull(form.spacing);
  if (spacing === null) errors.spacing = 'spacingRequired';
  else if (spacing < MIN_SPACING_CM || spacing > MAX_SPACING_CM) errors.spacing = 'spacingRange';
  if (form.layout === 'rows') {
    const rowSpacing = numberOrNull(form.rowSpacing);
    if (rowSpacing === null) errors.rowSpacing = 'rowSpacingRequired';
    else if (rowSpacing < MIN_SPACING_CM || rowSpacing > MAX_SPACING_CM) {
      errors.rowSpacing = 'rowSpacingRange';
    }
  }
  if (form.countMode === 'number') {
    const count = numberOrNull(form.count);
    if (count === null || !Number.isInteger(count) || count < 1 || count > MAX_COUNT) {
      errors.count = 'countRequired';
    }
  }
  for (const [field, text] of [
    ['edgeAlong', form.edgeAlong],
    ['edgeAcross', form.edgeAcross],
  ] as const) {
    const margin = numberOrNull(text);
    if (text.trim() !== '' && (margin === null || margin < 0 || margin > MAX_MARGIN_CM)) {
      errors[field] = 'marginRange';
    }
  }
  if (form.layout === 'free' && form.freePoints.length === 0) errors.points = 'noPoints';
  return errors;
}

export function hasErrors(errors: EntryErrors): boolean {
  return Object.keys(errors).length > 0;
}

/** The layout fields of an entry for the TS port; `null` while the spacing does not parse. */
export function toEntryLayout(
  form: EntryFormState,
  matureWidthCm: number | null,
  rowAssignment: number[] | null,
): EntryLayout | null {
  const spacing = numberOrNull(form.spacing);
  if (spacing === null || form.layout === 'free') return null;
  return {
    layout_strategy: form.layout,
    spacing_cm: spacing,
    row_spacing_cm: form.layout === 'rows' ? numberOrNull(form.rowSpacing) : null,
    row_direction: form.rowDirection,
    edge_margin_along_cm: numberOrNull(form.edgeAlong),
    edge_margin_across_cm: numberOrNull(form.edgeAcross),
    row_assignment: rowAssignment,
    mature_width_cm: matureWidthCm,
  };
}

/** The same fields as the server's preview request (`PlantingLayoutEntryRequest`). */
export function toPreviewEntry(layout: EntryLayout, maxCount: number | null): PreviewEntry {
  return {
    layout_strategy: layout.layout_strategy,
    spacing_cm: layout.spacing_cm,
    ...(layout.row_spacing_cm != null ? { row_spacing_cm: layout.row_spacing_cm } : {}),
    row_direction: layout.row_direction ?? 'along_length',
    ...(layout.edge_margin_along_cm != null
      ? { edge_margin_along_cm: layout.edge_margin_along_cm }
      : {}),
    ...(layout.edge_margin_across_cm != null
      ? { edge_margin_across_cm: layout.edge_margin_across_cm }
      : {}),
    ...(layout.row_assignment ? { row_assignment: layout.row_assignment } : {}),
    ...(layout.mature_width_cm != null ? { mature_width_cm: layout.mature_width_cm } : {}),
    ...(maxCount !== null ? { max_count: maxCount } : {}),
  };
}

/** The requested number of plants; `null` = as many as fit. */
export function requestedCount(form: EntryFormState): number | null {
  if (form.countMode === 'max') return null;
  const count = numberOrNull(form.count);
  return count !== null && Number.isInteger(count) && count >= 1 ? count : null;
}

// ── Alternating rows (GP-FR-070) ────────────────────────────────────────────

/**
 * Row indices (0-based, as `row_assignment` and the layout calculator count them) entry `index` of
 * `entryCount` takes when the rows alternate: entry 0 takes rows 0, n, 2n ..., entry 1 rows 1, n+1 ...
 * The sets of the entries are disjoint by construction, which the server demands.
 */
export function alternatingRows(rowCount: number, entryCount: number, index: number): number[] {
  const rows: number[] = [];
  for (let row = index; row < rowCount; row += entryCount) rows.push(row);
  return rows;
}

/** Whether the entries can share rows: two or more, all laid out in rows. */
export function canAlternate(forms: readonly EntryFormState[]): boolean {
  return forms.length >= 2 && forms.every((form) => ROW_STRATEGIES.includes(form.layout));
}

// ── Freely placed positions (GP-FR-072) ─────────────────────────────────────

/**
 * Indices of the points that stand closer than `spacingCm` to another one. A hint (the yellow ring),
 * never a blocker. The tolerance is the one the server's V-07 uses.
 */
export function tooClosePoints(points: readonly Point[], spacingCm: number): number[] {
  const limit = spacingCm / 100 - SPACING_TOLERANCE_M;
  const flagged = new Set<number>();
  for (let i = 0; i < points.length; i += 1) {
    for (let j = i + 1; j < points.length; j += 1) {
      if (Math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1]) < limit) {
        flagged.add(i);
        flagged.add(j);
      }
    }
  }
  return [...flagged].sort((a, b) => a - b);
}

// ── Container volume (W-016.5) ──────────────────────────────────────────────

export interface ContainerCheck {
  /** The pot is smaller than the species' recommendation. */
  volumeBelow: boolean;
  recommendedL: number | null;
}

/** W-016.5: warn when the pot volume the user names is below the Steckbrief recommendation. */
export function containerCheck(volumeText: string, species: Species | null): ContainerCheck {
  const recommendedL = parseLowerBound(species?.recommended_container_volume_l);
  const volume = numberOrNull(volumeText);
  return {
    volumeBelow: volume !== null && recommendedL !== null && volume < recommendedL,
    recommendedL,
  };
}

// ── Hints with a strength (D-09) ────────────────────────────────────────────

/** A hint of this strength needs a reason before the grower plants anyway ("Trotzdem pflanzen"). */
export function needsOverrideReason(severity: RotationSeverity): boolean {
  return severity === 'WARNING' || severity === 'CRITICAL';
}

const SEVERITY_RANK: Record<RotationSeverity, number> = { OK: 0, INFO: 1, WARNING: 2, CRITICAL: 3 };

export function worstSeverity(severities: readonly RotationSeverity[]): RotationSeverity {
  return severities.reduce<RotationSeverity>(
    (worst, next) => (SEVERITY_RANK[next] > SEVERITY_RANK[worst] ? next : worst),
    'OK',
  );
}

// ── Names ───────────────────────────────────────────────────────────────────

/** `^[A-Z]{2,5}$` for the plant ids of a run: the first letters of the species' name, diacritics folded. */
export function idPrefixOf(species: Species | null): string {
  const source = species?.common_names?.[0] || species?.scientific_name || '';
  const letters = source
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/ß/g, 'ss')
    .toUpperCase()
    .replace(/[^A-Z]/g, '');
  return letters.length >= 2 ? letters.slice(0, 3) : 'PLT';
}

const SLOT_PREFIX_LENGTH = 12;

/** `LOCATION` of a `LOCATION_NNN` slot id: the bed's name, upper-case letters and digits (GP-FR-064). */
export function slotIdPrefixOf(bedName: string, bedKey: string): string {
  const clean = (text: string) => text.toUpperCase().replace(/[^A-Z0-9]+/g, '');
  return clean(bedName).slice(0, SLOT_PREFIX_LENGTH) || clean(`L${bedKey}`).slice(0, SLOT_PREFIX_LENGTH) || 'BED';
}
