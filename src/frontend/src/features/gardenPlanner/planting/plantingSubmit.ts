/**
 * What the dialog sends (REQ-053 §11.1 steps 5-6): the planned runs of all species in **one** request
 * (`POST /planting-runs/mixed-culture`, #2463). The server lays the entries out on the bed, reserves the
 * slots (GP-FR-064/065), keeps the points of a `free` entry as reserved positions and writes it all in one
 * transaction - so a refusal leaves nothing behind and the dialog has nothing to take back.
 * "Already planted" is the field-mode shortcut `quick-planting` (GP-API-017).
 */
import type { MixedCultureCreate, MixedCultureRunCreate, PlantingRunEntryCreate, Species } from '@/api/types';
import { getActiveTenantSlug } from '@/api/client';
import { createMixedRuns, quickPlant } from './plantingApi';
import { idPrefixOf, type EntryFormState } from './plantingLogic';
import type { QuickPlantingBody, QuickPlantingResponse } from './plantingTypes';
import type { EntryPreview } from './useEntryPreviews';

function numberOrNull(text: string): number | null {
  const parsed = Number(text.trim().replace(',', '.'));
  return text.trim() !== '' && Number.isFinite(parsed) ? parsed : null;
}

/** One planned entry of the run. `quantity` is what the preview shows - what fits, or what was asked for. */
export function entryPayload(
  form: EntryFormState,
  species: Species,
  preview: EntryPreview,
  rowAssignment: number[] | null,
): PlantingRunEntryCreate {
  const free = form.layout === 'free';
  const quantity = free ? form.freePoints.length : Math.max(preview.count, 1);
  const rowSpacing = form.layout === 'rows' ? numberOrNull(form.rowSpacing) : null;
  const along = numberOrNull(form.edgeAlong);
  const across = numberOrNull(form.edgeAcross);
  return {
    species_key: species.key,
    cultivar_key: form.cultivarKey,
    quantity,
    id_prefix: idPrefixOf(species),
    spacing_cm: numberOrNull(form.spacing),
    layout_strategy: form.layout,
    ...(rowSpacing !== null ? { row_spacing_cm: rowSpacing } : {}),
    ...(form.layout !== 'zone' && form.layout !== 'free' ? { row_direction: form.rowDirection } : {}),
    ...(along !== null ? { edge_margin_along_cm: along } : {}),
    ...(across !== null ? { edge_margin_across_cm: across } : {}),
    ...(rowAssignment ? { row_assignment: rowAssignment } : {}),
  };
}

export interface RunInput {
  bedKey: string;
  bedName: string;
  forms: readonly EntryFormState[];
  species: readonly Species[];
  previews: Record<string, EntryPreview>;
  rowAssignments: Record<string, number[] | null>;
  /** `yyyy-mm-dd`: the day the plants go in. */
  plantedFrom: string;
  /** The reason of "Trotzdem pflanzen"; `null` when no hint was overridden. */
  overrideReason: string | null;
}

function speciesOf(input: RunInput, form: EntryFormState): Species {
  const species = input.species.find((candidate) => candidate.key === form.speciesKey);
  if (!species) throw new Error('The entry has no species.');
  return species;
}

/** `Tomato - Raised bed 3`: what the run list shows. */
export function runName(species: Species, bedName: string): string {
  return `${species.common_names?.[0] || species.scientific_name} – ${bedName}`.slice(0, 200);
}

/**
 * One run per species: a mixed culture is separate runs per species (REQ-013 §2 - the phases, nutrient
 * plans and care differ), and a monoculture run holds exactly one entry. The alternating rows tie the runs
 * together on the bed: their `row_assignment`s are disjoint.
 */
export function runItem(input: RunInput, form: EntryFormState): MixedCultureRunCreate {
  const species = speciesOf(input, form);
  const volume = numberOrNull(form.containerVolume);
  return {
    name: runName(species, input.bedName),
    entry: entryPayload(form, species, input.previews[form.id], input.rowAssignments[form.id] ?? null),
    ...(form.layout === 'free' && form.freePoints.length > 0 ? { free_points: form.freePoints } : {}),
    ...(form.layout === 'free' && volume !== null && volume > 0 ? { container_volume_l: volume } : {}),
  };
}

/** The whole request: every species of the dialog on the bed, with the one reason of "Trotzdem pflanzen". */
export function mixedCulturePayload(input: RunInput): MixedCultureCreate {
  return {
    location_key: input.bedKey,
    planned_start_date: input.plantedFrom,
    planned_from: input.plantedFrom,
    plan_role: 'main_crop',
    source: 'manual',
    ...(input.overrideReason ? { rotation_override_reason: input.overrideReason } : {}),
    runs: input.forms.map((form) => runItem(input, form)),
  };
}

export interface RunOutcome {
  runKeys: string[];
  plantCount: number;
}

/**
 * Create the planned runs of all entries in one request. The server writes the runs, their layouts and the
 * freely set points in one transaction, so there is no step to fail half way: a refusal creates nothing and
 * nothing has to be taken back (which would need the lead role).
 */
export async function submitRuns(input: RunInput): Promise<RunOutcome> {
  const { runs } = await createMixedRuns(mixedCulturePayload(input));
  const plantCount = input.forms.reduce(
    (sum, form) => sum + (form.layout === 'free' ? form.freePoints.length : (input.previews[form.id]?.count ?? 0)),
    0,
  );
  return { runKeys: runs.map((run) => run.key), plantCount };
}

export function quickBody(
  form: EntryFormState,
  species: Species,
  preview: EntryPreview,
  plantedOn: string,
  overrideReason: string | null,
): QuickPlantingBody {
  const rowSpacing = form.layout === 'rows' ? numberOrNull(form.rowSpacing) : null;
  return {
    species_key: species.key,
    cultivar_key: form.cultivarKey,
    quantity: Math.max(preview.count, 1),
    planted_on: plantedOn,
    id_prefix: idPrefixOf(species),
    spacing_cm: numberOrNull(form.spacing),
    layout_strategy: form.layout as Exclude<EntryFormState['layout'], 'zone' | 'free'>,
    row_direction: form.rowDirection,
    ...(rowSpacing !== null ? { row_spacing_cm: rowSpacing } : {}),
    ...(overrideReason ? { rotation_override_reason: overrideReason } : {}),
  };
}

export function submitQuick(
  bedKey: string,
  body: QuickPlantingBody,
): Promise<QuickPlantingResponse> {
  return quickPlant(bedKey, body);
}

// ── What this tenant used last (F-11) ───────────────────────────────────────

const LAST_USED_KEY = 'kp.gardenPlanner.planting.lastUsed';

interface LastUsedMap {
  [speciesKey: string]: { spacing_cm?: number; row_spacing_cm?: number; layout_strategy?: EntryFormState['layout'] };
}

function storageKey(): string {
  return `${LAST_USED_KEY}.${getActiveTenantSlug() ?? 'default'}`;
}

/**
 * Per tenant and species, kept in this browser (a server-side store is an open question of the work
 * package). Storage can be absent or throw (private window): the dialog then simply has no "last used".
 */
export function readLastUsed(speciesKey: string): LastUsedMap[string] | null {
  try {
    const raw = localStorage.getItem(storageKey());
    if (!raw) return null;
    const map = JSON.parse(raw) as LastUsedMap;
    return map[speciesKey] ?? null;
  } catch {
    return null;
  }
}

export function writeLastUsed(forms: readonly EntryFormState[]): void {
  try {
    const raw = localStorage.getItem(storageKey());
    const map: LastUsedMap = raw ? (JSON.parse(raw) as LastUsedMap) : {};
    for (const form of forms) {
      if (!form.speciesKey) continue;
      const spacing = numberOrNull(form.spacing);
      const rowSpacing = form.layout === 'rows' ? numberOrNull(form.rowSpacing) : null;
      map[form.speciesKey] = {
        ...(spacing !== null ? { spacing_cm: spacing } : {}),
        ...(rowSpacing !== null ? { row_spacing_cm: rowSpacing } : {}),
        layout_strategy: form.layout,
      };
    }
    localStorage.setItem(storageKey(), JSON.stringify(map));
  } catch {
    // A convenience; losing it is not an error.
  }
}
