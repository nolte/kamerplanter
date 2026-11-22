import { tenantClient } from '@/api/client';

/**
 * `GET /locations/{key}/companion-edges` (REQ-053 GP-FR-134, WP 8.15): every neighbouring pair of occupied slots of
 * one bed, judged with the planting dialog's rule (incompatible wins, else compatible with its score, else unknown).
 * One request per bed, never per hover; the server answers at most 500 pairs, strongest status first.
 */

export type CompanionStatus = 'compatible' | 'incompatible' | 'unknown';

export interface CompanionEndpointWire {
  slot_key: string;
  /** The slot's anchor in plan metres; `null` when the slot or its bed has no geometry (no line can be drawn). */
  position: { x: number; y: number } | null;
  species_keys: string[];
  /** `true` when the slot holds more than 8 species and only the first ones were judged. */
  species_truncated?: boolean;
}


export interface CompanionEdgeWire {
  slot_a: CompanionEndpointWire;
  slot_b: CompanionEndpointWire;
  status: CompanionStatus;
  reason_code: 'companion.compatible' | 'companion.incompatible' | 'companion.unknown';
  /** The curated reason of the deciding incompatibility, as stored in the companion data. */
  reason: string | null;
  /** The compatibility score of the deciding pair; `null` for any status but `compatible`. */
  score: number | null;
  deciding: {
    species_a_key: string;
    species_a_name: string | null;
    species_b_key: string;
    species_b_name: string | null;
  } | null;
  distance_cm: number | null;
}

export interface CompanionEdgesWire {
  location_key: string;
  edges: CompanionEdgeWire[];
  total: number;
  /** `true` when the bed has more pairs than the answer lists. */
  truncated: boolean;
}

export async function getCompanionEdges(bedKey: string, signal?: AbortSignal): Promise<CompanionEdgesWire> {
  const { data } = await tenantClient.get<CompanionEdgesWire>(`/locations/${bedKey}/companion-edges`, { signal });
  return data;
}

/** One pair as the text list of the legend shows it. */
export interface CompanionPairItem {
  id: string;
  edge: CompanionEdgeWire;
}
