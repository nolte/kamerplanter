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

/** The server answers at most 200 plants per page (the shared pagination bound). */
export const PLANT_STATES_PAGE_SIZE = 200;
/** A bed holds at most 2 000 slots (GP-NFR-017): the page loop stops there even if a server never answers short. */
const MAX_PAGES = 10;

/** All standing plants of the bed: pages of 200 until one comes back shorter. */
export async function listPlantStates(bedKey: string, signal?: AbortSignal): Promise<PlantStateWire[]> {
  const all: PlantStateWire[] = [];
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const { data } = await tenantClient.get<PlantStateWire[]>(`/locations/${bedKey}/plant-states`, {
      params: { offset: page * PLANT_STATES_PAGE_SIZE, limit: PLANT_STATES_PAGE_SIZE },
      signal,
    });
    all.push(...data);
    if (data.length < PLANT_STATES_PAGE_SIZE) break;
  }
  return all;
}
