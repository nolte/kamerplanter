import { tenantClient } from '@/api/client';
import type { AttentionCode, Lifecycle } from '../model/plantState';

/**
 * `GET /locations/{key}/plant-states` (REQ-053 GP-API-054): the standing plants of a bed with the facts of
 * the info bubble and the inputs of the visual state. One request per bed, not per hover (GP-FR-191).
 */

export interface PlantStatePhase {
  key: string;
  name?: string | null;
  elapsed_d: number;
  typical_d?: number | null;
  fraction?: number | null;
  next_phase_eta?: string | null;
}

export interface PlantStateInputs {
  open_tasks: { category: string; due?: string | null }[];
  open_findings: number;
  frost_risk: boolean;
  harvest_batches: number;
  phase?: {
    key: string;
    started_on: string;
    typical_days?: number | null;
    allows_harvest: boolean;
    is_terminal: boolean;
  } | null;
}

/** One plant of the answer; only the fields of the plant info (no notes, no user names). */
export interface PlantStateWire {
  /** Absent on an older server: a plant. */
  kind?: 'plant';
  plant_key: string;
  slot_key?: string | null;
  slot_id?: string | null;
  instance_id: string;
  species_key: string;
  species_name?: string | null;
  scientific_name?: string | null;
  cultivar_name?: string | null;
  planted_on: string;
  lifecycle: Lifecycle;
  phase?: PlantStatePhase | null;
  last_care: { watering?: string | null; feeding?: string | null };
  next_task?: { name: string; category: string; due?: string | null } | null;
  attention: { reason: AttentionCode; count: number }[];
  finding_label?: string | null;
  harvest: { ready: boolean; ready_from?: string | null; harvested_total_g?: number | null };
  cover_photo_ref?: string | null;
  inputs: PlantStateInputs;
}

/**
 * A sown row or zone without plants yet (REQ-053 §11.3, W-015): no plant, `instance_id` is the slot's id and
 * `planted_on` the sowing day; no phase, care or reason that needs attention.
 */
export interface SownStateWire extends Omit<PlantStateWire, 'kind' | 'plant_key'> {
  kind: 'sown';
  plant_key: null;
}

/**
 * A zone thinned into a target stand instead of single plants (REQ-053 §11.3 "Zonen-Bestand", #2862): it stands
 * (lifecycle `active`), but no plant does. `planted_on` is the thinning day, `sown_on` the sowing day.
 */
export interface StandStateWire extends Omit<PlantStateWire, 'kind' | 'plant_key'> {
  kind: 'stand';
  plant_key: null;
  sown_on?: string | null;
}

/** One entry of the answer: a standing plant, a sown slot or a zone stand (the slot entries come first). */
export type PlantStateEntryWire = PlantStateWire | SownStateWire | StandStateWire;

/** Whether the entry is a standing plant (the field sheet and the plant actions take plants only). */
export function isPlantEntry(entry: PlantStateEntryWire): entry is PlantStateWire {
  return entry.kind !== 'sown' && entry.kind !== 'stand';
}

/** The key of an entry on the plan: the plant's, or for a sown slot or zone stand the slot's (a plantless slot). */
export function stateKeyOf(wire: Pick<PlantStateEntryWire, 'kind' | 'plant_key' | 'slot_key'>): string {
  return (wire.kind === 'sown' || wire.kind === 'stand' ? wire.slot_key : wire.plant_key) ?? '';
}

/** The server answers at most 200 plants per page (the shared pagination bound). */
export const PLANT_STATES_PAGE_SIZE = 200;
/** A bed holds at most 2 000 slots (GP-NFR-017): the page loop stops there even if a server never answers short. */
const MAX_PAGES = 10;

/** All entries of the bed (sown slots, then standing plants): pages of 200 until one comes back shorter. */
export async function listPlantStates(
  bedKey: string,
  signal?: AbortSignal,
  timeout?: number,
): Promise<PlantStateEntryWire[]> {
  const all: PlantStateEntryWire[] = [];
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const { data } = await tenantClient.get<PlantStateEntryWire[]>(`/locations/${bedKey}/plant-states`, {
      params: { offset: page * PLANT_STATES_PAGE_SIZE, limit: PLANT_STATES_PAGE_SIZE },
      signal,
      ...(timeout ? { timeout } : {}),
    });
    all.push(...data);
    if (data.length < PLANT_STATES_PAGE_SIZE) break;
  }
  return all;
}
