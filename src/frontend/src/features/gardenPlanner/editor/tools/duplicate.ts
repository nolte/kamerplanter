/**
 * Duplicate with offset (REQ-053 GP-FR-025): copies geometry and base fields of the selected
 * locations and garden objects - and everything inside a selected area - to the first free position: shifted by the
 * selection's own extent plus one grid step, so the copy lies next to the original instead of on it (operator
 * decision of 2026-11-14 on #2759, question 14). "Free" is the live validation's verdict, V-05 (`bed.overlap`)
 * included, so a copy never lands where the save would refuse it. Plants and tasks are never copied. Slots cannot be: the closed plan operation list has no
 * `create_slot`, so a copied bed starts without positions (the panel offers to lay them out).
 * Every copy gets a fresh temp key; one duplicate is one `PlanOperation` batch = one undo step.
 * `multiDuplicate` makes several copies in a row with a naming scheme (SHOULD, F-10) the same way.
 */
import { boundingBox, roundLength } from '../../model/geometry';
import { locationSubtree, newTempKey, type PlanModel } from '../../model/planModel';
import {
  MAX_BATCH_OPERATIONS,
  MAX_PLAN_OBJECTS_PER_SITE,
  type CreateGardenObjectData,
  type CreateLocationData,
  type GardenObject,
  type PlanLocation,
  type PlanOperation,
  type Point,
} from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { translateGeometry } from './geometryEdit';
import { objectsIn, selectionRoots } from './hierarchy';
import { ERROR_BED_OVERLAP, ERROR_OUTSIDE_PARENT, violationOfNew } from './validation';

/**
 * Offset directions tried in turn (the plan frame's y points up): right first, then down, left, up, then the
 * diagonals. Each one shifts by the selection's extent plus a grid step along its axes.
 */
const DIRECTIONS: readonly Point[] = [
  [1, 0],
  [0, -1],
  [-1, 0],
  [0, 1],
  [1, -1],
  [1, 1],
  [-1, -1],
  [-1, 1],
];

/**
 * How many positions one direction tries, one extent-plus-step further each time, while a copy still fits into its
 * parent somewhere: a row of 20 beds is skipped before the duplicate gives up and says why.
 */
export const MAX_DUPLICATE_RINGS = 20;

export interface DuplicateResult {
  ops: PlanOperation[];
  /** The copies of the selection roots, to select afterwards. */
  selection: SelectionRef[];
}

export type DuplicateOutcome =
  | { ok: true; value: DuplicateResult }
  | { ok: false; code: 'nothing' | 'geometry.outside_parent' | 'geometry.invalid' | 'bed.overlap' };

function locationData(
  location: PlanLocation,
  geometry: NonNullable<PlanLocation['geometry']>,
  parent: string | null,
  copyName: string,
): CreateLocationData {
  const data: CreateLocationData = {
    name: copyName,
    location_type_key: location.location_type_key,
    geometry,
    sun_exposure: location.sun_exposure,
    z_order: location.z_order,
  };
  if (parent) data.parent_location_key = parent;
  if (location.height_m != null) data.height_m = location.height_m;
  if (location.description != null) data.description = location.description;
  if (location.notes != null) data.notes = location.notes;
  return data;
}

function objectData(
  garden: GardenObject,
  geometry: GardenObject['geometry'],
  parent: string | null,
): CreateGardenObjectData {
  const data: CreateGardenObjectData = {
    object_type: garden.object_type,
    label: garden.label,
    geometry,
    props: garden.props as unknown as Record<string, unknown>,
    off_site: garden.off_site,
    z_order: garden.z_order,
  };
  if (parent) data.parent_location_key = parent;
  if (garden.notes != null) data.notes = garden.notes;
  return data;
}

interface Copyable {
  roots: ReturnType<typeof selectionRoots>;
  /** Locations of the roots and everything below them. */
  locationKeys: Set<string>;
  /** Root locations in breadth-first order, parents first. */
  orderedLocations: string[];
  /** Garden objects to copy: the roots first, then the ones inside a copied area. */
  objectKeys: string[];
  rootObjectKeys: string[];
}

function copyableOf(plan: PlanModel, selection: readonly SelectionRef[]): Copyable | null {
  const roots = selectionRoots(plan, selection).filter((ref) => {
    const source =
      ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key];
    return source?.geometry != null;
  });
  if (roots.length === 0) return null;
  const locationKeys = new Set(
    roots.filter((r) => r.entity === 'location').flatMap((r) => locationSubtree(plan, r.key)),
  );
  const insideObjects = objectsIn(plan, locationKeys);
  const rootObjectKeys = roots.filter((r) => r.entity === 'garden_object').map((r) => r.key);
  return {
    roots,
    locationKeys,
    // Parents first: `locationSubtree` is breadth-first per root.
    orderedLocations: roots
      .filter((r) => r.entity === 'location')
      .flatMap((r) => locationSubtree(plan, r.key)),
    objectKeys: [...rootObjectKeys, ...insideObjects.filter((k) => !rootObjectKeys.includes(k))],
    rootObjectKeys,
  };
}

/** One copy of the selection shifted by `delta`: its operations, the copies of the roots and the first rule it breaks. */
function copyAt(
  plan: PlanModel,
  source: Copyable,
  delta: Point,
  rootName: (name: string) => string,
): DuplicateResult & { violation: string | null } {
  // Keys of the copies, so children point at their copied parent.
  const copyOf = new Map<string, string>();
  for (const key of source.locationKeys) copyOf.set(key, newTempKey());
  const ops: PlanOperation[] = [];
  let violation: string | null = null;
  const rootCopies: SelectionRef[] = [];
  for (const key of source.orderedLocations) {
    const location = plan.locations[key];
    if (!location.geometry) continue;
    const geometry = translateGeometry(location.geometry, delta);
    const isRoot = source.roots.some((r) => r.entity === 'location' && r.key === key);
    const parent = isRoot
      ? (location.parent_location_key ?? null)
      : (copyOf.get(location.parent_location_key ?? '') ?? null);
    const tempKey = copyOf.get(key)!;
    ops.push({
      op: 'create_location',
      temp_key: tempKey,
      data: locationData(
        location,
        geometry,
        parent,
        isRoot ? rootName(location.name) : location.name,
      ),
    });
    if (isRoot) {
      // A root copy shares the parent of its original; its subtree moves rigidly with it. V-05 with its type (#2759).
      violation ??= violationOfNew(plan, geometry, parent, location.location_type_key);
      rootCopies.push({ entity: 'location', key: tempKey });
    }
  }
  for (const key of source.objectKeys) {
    const garden = plan.gardenObjects[key];
    const isRoot = source.rootObjectKeys.includes(key);
    const geometry = translateGeometry(garden.geometry, delta);
    const parent = isRoot
      ? (garden.parent_location_key ?? null)
      : (copyOf.get(garden.parent_location_key ?? '') ?? null);
    const tempKey = newTempKey();
    ops.push({
      op: 'create_garden_object',
      temp_key: tempKey,
      data: objectData(garden, geometry, parent),
    });
    if (isRoot) {
      if (!garden.off_site) violation ??= violationOfNew(plan, geometry, parent);
      rootCopies.push({ entity: 'garden_object', key: tempKey });
    }
  }
  return { ops, selection: rootCopies, violation };
}

/**
 * The operations that duplicate `selection` at the first free position (GP-FR-025, #2759): shifted by the
 * selection's own extent plus `stepM` metres along each direction in turn, then one extent-plus-step further, until
 * the copies pass the live validation (V-01..V-03 and V-05, GP-UX-053). The search stops when every direction leaves
 * the parent; the refusal names the reason that blocked a position inside it (`bed.overlap`) before the containment.
 * `copyName(name)` builds the name of a copied bed ("Beet 1 (Kopie)"); i18n stays with the caller.
 */
export function duplicateSelection(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  stepM: number,
  copyName: (name: string) => string,
): DuplicateOutcome {
  const source = copyableOf(plan, selection);
  if (source === null) return { ok: false, code: 'nothing' };
  const [x0, y0, x1, y1] = rootsExtent(plan, source);
  const pitch: Point = [x1 - x0 + stepM, y1 - y0 + stepM];
  let sawOutside = false;
  let sawOverlap = false;
  for (let ring = 1; ring <= MAX_DUPLICATE_RINGS; ring += 1) {
    let roomInside = false;
    for (const [dx, dy] of DIRECTIONS) {
      const delta: Point = [roundLength(dx * ring * pitch[0]), roundLength(dy * ring * pitch[1])];
      const copy = copyAt(plan, source, delta, copyName);
      if (copy.violation === null)
        return { ok: true, value: { ops: copy.ops, selection: copy.selection } };
      if (copy.violation === ERROR_OUTSIDE_PARENT) sawOutside = true;
      else roomInside = true;
      sawOverlap ||= copy.violation === ERROR_BED_OVERLAP;
    }
    // Every direction already leaves the parent: one step further out only leaves it further.
    if (!roomInside) break;
  }
  if (sawOverlap) return { ok: false, code: 'bed.overlap' };
  return { ok: false, code: sawOutside ? 'geometry.outside_parent' : 'geometry.invalid' };
}

// ── Duplicate several times (GP-FR-025, SHOULD, F-10) ────────────────────────

export type MultiDirection = 'right' | 'left' | 'up' | 'down';

/** The most copies one run makes: a community garden of 30 plots, with room (GP-NFR-017 caps a site at 500). */
export const MAX_MULTI_COPIES = 100;

export interface MultiDuplicateOptions {
  /** Number of copies, 1..{@link MAX_MULTI_COPIES}. */
  count: number;
  direction: MultiDirection;
  /** Gap between one copy and the next, edge to edge, in metres (>= 0). */
  spacingM: number;
  /** Naming scheme of the copied beds; `{n}` is replaced by the number ("Parzelle {n}"). */
  scheme: string;
  /** The number `{n}` starts at. */
  startNumber: number;
  /** Operations already waiting for the next save: they share its limit of one batch. */
  pendingCount?: number;
}

export type MultiDuplicateOutcome =
  | { ok: true; value: DuplicateResult & { copies: number } }
  | {
      ok: false;
      code:
        | 'nothing'
        | 'multi.invalid'
        | 'plan.quota_exceeded'
        | 'multi.too_many'
        | 'geometry.outside_parent'
        | 'geometry.invalid'
        | 'bed.overlap';
      /** Number of the first copy that breaks a rule (1-based), when the code is a geometry one. */
      failedCopy?: number;
      /** The name that copy's first bed would have carried ("Parzelle 13"); absent when it holds no bed. */
      failedName?: string;
    };

/** A refusal as the dialog shows it: the code of a `notice.*` text and, for a geometry rule, the first copy that breaks it. */
export interface MultiRefusal {
  code: string;
  failedCopy?: number;
  /** The name of the first bed of that copy, so the dialog names it as the plan would ("Parzelle 13"). */
  failedName?: string;
}

/** The name of a copied bed: the scheme with `{n}` replaced (a scheme without `{n}` gets the number appended). */
export function multiCopyName(scheme: string, n: number): string {
  const text = scheme.trim();
  return text.includes('{n}') ? text.split('{n}').join(String(n)) : `${text} ${n}`.trim();
}

/** The union of the boxes of the roots, in the plan frame. */
function rootsExtent(plan: PlanModel, source: Copyable): [number, number, number, number] {
  const boxes = source.roots.map((ref) => {
    const entity =
      ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key];
    return entity.bbox ?? boundingBox(entity.geometry!);
  });
  return [
    Math.min(...boxes.map((b) => b[0])),
    Math.min(...boxes.map((b) => b[1])),
    Math.max(...boxes.map((b) => b[2])),
    Math.max(...boxes.map((b) => b[3])),
  ];
}

/**
 * `count` copies of the selection in a row (GP-FR-025): each one `spacingM` apart from the last one, named by the
 * scheme. All copies are ONE list of operations = one undo step (GP-FR-155). The quota of the site (GP-NFR-017) and
 * the size of one batch are checked before anything is built; every copy goes through the live validation, and
 * the first one that does not fit refuses the whole run - nothing is half done. Slots are not copied (the closed
 * operation list has no `create_slot`), plants and tasks never.
 */
export function multiDuplicate(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  options: MultiDuplicateOptions,
): MultiDuplicateOutcome {
  const source = copyableOf(plan, selection);
  if (source === null) return { ok: false, code: 'nothing' };
  const { count, spacingM } = options;
  if (
    !Number.isInteger(count) ||
    count < 1 ||
    count > MAX_MULTI_COPIES ||
    !Number.isFinite(spacingM) ||
    spacingM < 0 ||
    !Number.isInteger(options.startNumber)
  ) {
    return { ok: false, code: 'multi.invalid' };
  }
  const perCopy = source.orderedLocations.length + source.objectKeys.length;
  const existing = Object.keys(plan.locations).length + Object.keys(plan.gardenObjects).length;
  if (existing + perCopy * count > MAX_PLAN_OBJECTS_PER_SITE) {
    return { ok: false, code: 'plan.quota_exceeded' };
  }
  if ((options.pendingCount ?? 0) + perCopy * count > MAX_BATCH_OPERATIONS) {
    return { ok: false, code: 'multi.too_many' };
  }
  const [x0, y0, x1, y1] = rootsExtent(plan, source);
  const horizontal = options.direction === 'right' || options.direction === 'left';
  const sign = options.direction === 'right' || options.direction === 'up' ? 1 : -1;
  const pitch = (horizontal ? x1 - x0 : y1 - y0) + spacingM;
  const ops: PlanOperation[] = [];
  const rootCopies: SelectionRef[] = [];
  let number = options.startNumber;
  for (let k = 1; k <= count; k += 1) {
    const shift = roundLength(sign * k * pitch);
    let firstName: string | undefined;
    const copy = copyAt(plan, source, horizontal ? [shift, 0] : [0, shift], (name) => {
      const given = options.scheme.trim() === '' ? name : multiCopyName(options.scheme, number++);
      firstName ??= given;
      return given;
    });
    if (copy.violation !== null) {
      return {
        ok: false,
        code:
          copy.violation === ERROR_OUTSIDE_PARENT || copy.violation === ERROR_BED_OVERLAP
            ? copy.violation
            : 'geometry.invalid',
        failedCopy: k,
        ...(firstName === undefined ? {} : { failedName: firstName }),
      };
    }
    ops.push(...copy.ops);
    rootCopies.push(...copy.selection);
  }
  return { ok: true, value: { ops, selection: rootCopies, copies: count } };
}
